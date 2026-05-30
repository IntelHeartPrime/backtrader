import streamlit as st
import sys
import os
import itertools
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtrader as bt
from adapters.cerebro_adapter import CerebroAdapter
from adapters.data_adapter import DataAdapter
from adapters.results_adapter import ResultsAdapter
from adapters.strategy_adapter import StrategyAutoDiscovery


@st.cache_resource
def get_strategy_catalog():
    """Discover all strategies. Cached across Streamlit reruns."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return StrategyAutoDiscovery.discover(project_root)


def run_single_backtest(strategy_params, data_params, backtest_params) -> Dict[str, Any]:
    """
    Run a single backtest.

    Args:
        strategy_params: User-configured strategy params (includes 'strategy_key')
        data_params: Data source configuration
        backtest_params: Backtest settings (initial_cash, commission)

    Returns:
        Results dictionary
    """
    try:
        adapter = CerebroAdapter(initial_cash=backtest_params['initial_cash'])
        adapter.set_commission(backtest_params['commission'])
        adapter.add_standard_analyzers()

        strategy_key = strategy_params.pop('strategy_key', None)
        class_name = strategy_params.pop('class_name', None)
        strategy_params.pop('category', None)  # metadata, not a strategy param
        catalog = get_strategy_catalog()
        entry = catalog.get(strategy_key) if strategy_key else None

        if entry is None:
            st.error(f'Strategy not found: {class_name or strategy_key}')
            return None

        # Check if strategy needs multiple data feeds
        needs_multi = getattr(entry.cls, '_needs_multi_data', False)

        if not needs_multi:
            adapter.set_sizer(backtest_params.get('position_pct', 95))

        if needs_multi:
            # Multi-data mode: fetch all bank stocks
            bank_stocks = strategy_params.get('bank_stocks', '')
            if isinstance(bank_stocks, str):
                bank_stocks = [s.strip() for s in bank_stocks.split(',') if s.strip()]
            if not bank_stocks:
                from examples.high_div_bank_strategy_001 import _fetch_bank_stocks
                bank_stocks = _fetch_bank_stocks()

            if not bank_stocks:
                st.error('No bank stocks available for multi-data strategy')
                return None

            start = data_params.get('start_date', '20200101')
            end = data_params.get('end_date', '20251231')
            fromdate = data_params.get('fromdate')
            todate = data_params.get('todate')

            st.info(f'Loading {len(bank_stocks)} bank stocks: {", ".join(bank_stocks[:8])}...')
            data_feeds = DataAdapter.create_multi_tushare_data(
                bank_stocks, start_date=start, end_date=end,
                fromdate=fromdate, todate=todate
            )
            if not data_feeds:
                st.error('Failed to fetch data for any bank stock')
                return None

            for feed in data_feeds:
                adapter.add_data(feed)
            strategy_params['bank_stocks'] = bank_stocks
        else:
            data = DataAdapter.create_from_params(data_params)
            adapter.add_data(data)

        adapter.add_strategy(entry.cls, **strategy_params)

        results = adapter.run()
        strategy = adapter.get_strategy()

        if strategy is None:
            return None

        results_adapter = ResultsAdapter(strategy)

        return {
            'metrics': results_adapter.get_metrics(),
            'equity': results_adapter.get_equity_curve(backtest_params['initial_cash']),
            'drawdown': results_adapter.get_drawdown_curve(),
            'trade_log': results_adapter.get_trade_log(),
            'ohlcv': results_adapter.get_ohlcv_data(),
            'signals': results_adapter.get_trade_signals()
        }
    except Exception as e:
        st.error(f'Backtest failed: {str(e)}')
        return None


def run_batch_backtest(data_params, backtest_params, batch_params) -> List[Dict[str, Any]]:
    """
    Run batch backtests with generic parameter grid search.

    Args:
        data_params: Data source configuration
        backtest_params: Backtest settings (initial_cash, commission)
        batch_params: Batch parameters including 'param_grid' and 'strategy_key'

    Returns:
        List of backtest result dictionaries
    """
    if not batch_params.get('enabled', False):
        return []

    param_grid = batch_params.get('param_grid', {})
    if not param_grid:
        st.warning('No parameter grid defined for batch search')
        return []

    strategy_key = batch_params.get('strategy_key')
    catalog = get_strategy_catalog()
    entry = catalog.get(strategy_key) if strategy_key else None
    if entry is None:
        st.error('Strategy not found for batch')
        return []

    # Build Cartesian product of param ranges
    param_names = list(param_grid.keys())
    param_ranges = [param_grid[name] for name in param_names]
    combos = list(itertools.product(*param_ranges))

    results = []
    total_backtests = len(combos)
    progress_bar = st.progress(0, text=f'Running Batch Backtests (0/{total_backtests})')

    # Pre-load data once — handle multi-data strategies
    needs_multi = getattr(entry.cls, '_needs_multi_data', False)
    if needs_multi:
        from examples.high_div_bank_strategy_001 import _fetch_bank_stocks
        # Use strategy default bank_stocks or auto-discover
        bank_stocks_param = getattr(entry.cls.params, 'bank_stocks', '')
        if isinstance(bank_stocks_param, str) and bank_stocks_param:
            bank_stocks = [s.strip() for s in bank_stocks_param.split(',') if s.strip()]
        elif isinstance(bank_stocks_param, list) and bank_stocks_param:
            bank_stocks = list(bank_stocks_param)
        else:
            bank_stocks = []
        if not bank_stocks:
            bank_stocks = _fetch_bank_stocks()
        if not bank_stocks:
            st.error('No bank stocks available for multi-data strategy')
            return []
        start = data_params.get('start_date', '20200101')
        end = data_params.get('end_date', '20251231')
        fromdate = data_params.get('fromdate')
        todate = data_params.get('todate')
        data_feeds = DataAdapter.create_multi_tushare_data(
            bank_stocks, start_date=start, end_date=end,
            fromdate=fromdate, todate=todate
        )
    else:
        data_feeds = [DataAdapter.create_from_params(data_params)]

    for idx, combo in enumerate(combos):
        strategy_kwargs = dict(zip(param_names, combo))
        label = ' - '.join(f'{name}={val}' for name, val in strategy_kwargs.items())

        try:
            adapter = CerebroAdapter(initial_cash=backtest_params['initial_cash'])
            adapter.set_commission(backtest_params['commission'])
            if not needs_multi:
                adapter.set_sizer(backtest_params.get('position_pct', 95))
            adapter.add_standard_analyzers()
            for feed in data_feeds:
                adapter.add_data(feed)

            adapter.add_strategy(entry.cls, **strategy_kwargs)

            bt_strategies = adapter.run()
            strategy = bt_strategies[0]

            if strategy is not None:
                results_adapter = ResultsAdapter(strategy)
                result = {
                    'label': label,
                    'metrics': results_adapter.get_metrics(),
                    'equity': results_adapter.get_equity_curve(),
                    'drawdown': results_adapter.get_drawdown_curve(),
                    'trade_log': results_adapter.get_trade_log(),
                    'ohlcv': results_adapter.get_ohlcv_data(),
                    'signals': results_adapter.get_trade_signals(),
                    'params': strategy_kwargs,
                }
                results.append(result)

            progress_bar.progress(
                len(results) / total_backtests,
                text=f'Running Batch Backtests ({len(results)}/{total_backtests})'
            )

        except Exception as e:
            st.error(f'Error in {label}: {str(e)}')

    progress_bar.empty()
    return results


def main():
    st.set_page_config(
        page_title='Backtrader Visualization',
        page_icon='📈',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    st.title('📈 Backtrader Interactive Workbench')
    st.markdown('---')

    st.header('Quantitative Trading Backtest Visualization')
    st.caption('Streamlit + Plotly + Backtrader | Non-intrusive visualization layer')
    st.markdown('---')

    catalog = get_strategy_catalog()

    from app.components.sidebar import render_sidebar
    strategy_params, data_params, backtest_params, batch_params = render_sidebar(catalog)

    if 'run_batch' in st.session_state and st.session_state.run_batch:
        st.session_state.batch_results = []

        with st.spinner('Running batch backtests...'):
            results = run_batch_backtest(data_params, backtest_params, batch_params)

            if results:
                st.session_state.batch_results = results
                st.success(f'Completed {len(results)} backtests!')

            st.session_state.run_batch = False

    elif 'run_backtest' in st.session_state and st.session_state.run_backtest:
        with st.spinner('Running single backtest...'):
            result = run_single_backtest(strategy_params, data_params, backtest_params)

            if result:
                st.session_state.single_result = result
                st.success('Backtest completed!')

            st.session_state.run_backtest = False

    if 'batch_results' in st.session_state and st.session_state.batch_results:
        from app.components.batch_results import render_batch_results
        render_batch_results(st.session_state.batch_results)
    elif 'single_result' in st.session_state:
        from app.components.batch_results import render_single_results
        render_single_results(st.session_state.single_result)
    else:
        st.info('👈 Configure backtest parameters in sidebar and click Run')


if __name__ == '__main__':
    main()
