import streamlit as st
import sys
import os

# Project root must be on path: adapters/, presenters/, package app/
_app_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_app_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import backtrader as bt
from adapters.cerebro_adapter import CerebroAdapter
from adapters.data_adapter import DataAdapter
from adapters.results_adapter import ResultsAdapter
from presenters.metrics_presenter import MetricsPresenter
from presenters.equity_presenter import EquityPresenter
from presenters.trade_log_presenter import TradeLogPresenter
from app.components.sidebar import render_sidebar
from app.components.main_chart import render_main_chart
from app.components.kpi_cards import render_kpi_cards
from app.components.result_area import render_result_area


def run_backtest(strategy_params, data_params, backtest_params):
    """
    Execute backtest with given parameters.
    
    Args:
        strategy_params: Strategy configuration
        data_params: Data source configuration
        backtest_params: Backtest settings (initial_cash, commission)
        
    Returns:
        Results dict with metrics, equity, drawdown, trade_log, ohlcv
    """
    try:
        adapter = CerebroAdapter(initial_cash=backtest_params['initial_cash'])
        adapter.set_commission(backtest_params['commission'])
        adapter.add_standard_analyzers()
        
        sample_path = DataAdapter.get_sample_data_path()
        if sample_path:
            data = DataAdapter.create_csv_data(sample_path)
            adapter.add_data(data)
        
        from examples.tushare_backtest import SmaCrossStrategy
        
        adapter.add_strategy(SmaCrossStrategy, **strategy_params)
        
        results = adapter.run()
        strategy = adapter.get_strategy()
        
        if strategy is None:
            return None
        
        results_adapter = ResultsAdapter(strategy)
        
        return {
            'metrics': results_adapter.get_metrics(),
            'equity': results_adapter.get_equity_curve(),
            'drawdown': results_adapter.get_drawdown_curve(),
            'trade_log': results_adapter.get_trade_log(),
            'ohlcv': results_adapter.get_ohlcv_data(),
            'signals': results_adapter.get_trade_signals()
        }
    except Exception as e:
        st.error(f'Backtest failed: {str(e)}')
        return None


def main():
    st.set_page_config(
        page_title='Backtrader Visualization',
        page_icon='📈',
        layout='wide',
        initial_sidebar_state='expanded'
    )
    
    st.title('📈 Backtrader Interactive Workbench')
    st.markdown('---')
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image('https://www.backtrader.com/static/backtrader_logo.png', width=100)
    with col2:
        st.header('Quantitative Trading Backtest Visualization')
        st.caption('Streamlit + Plotly + Backtrader | Non-intrusive visualization layer')
    
    strategy_params, data_params, backtest_params = render_sidebar()
    
    if 'run_backtest' in st.session_state and st.session_state.run_backtest:
        with st.spinner('Running backtest...'):
            results = run_backtest(strategy_params, data_params, backtest_params)
            
            if results:
                st.session_state.results = results
                st.success('✅ Backtest completed!')
            
            st.session_state.run_backtest = False
    
    if 'results' in st.session_state:
        results = st.session_state.results
        
        st.markdown('---')
        st.markdown('### 📊 Performance Metrics')
        render_kpi_cards(results['metrics'])
        
        st.markdown('---')
        
        col_chart, col_results = st.columns([2, 1])
        
        with col_chart:
            render_main_chart(
                ohlcv_df=results['ohlcv'],
                buy_signals=results['signals'].get('buys', []),
                sell_signals=results['signals'].get('sells', [])
            )
        
        with col_results:
            render_result_area(
                equity_df=results['equity'],
                drawdown_df=results['drawdown'],
                trade_log_df=results['trade_log']
            )
    else:
        st.info('👈 Configure backtest parameters in the sidebar and click "Run Backtest"')


if __name__ == '__main__':
    main()
