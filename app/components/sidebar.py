import streamlit as st
from typing import Dict, Any, Tuple, List

from adapters.strategy_adapter import StrategyAdapter


COMPLEXITY_BADGES = {
    'simple': '',
    'moderate': ' ⚠',
    'complex': ' 🔴',
}


def _dispatch_widget(cfg: Dict[str, Any]) -> Any:
    """Render a single Streamlit widget based on config."""
    widget_type = cfg['widget_type']
    key = cfg['key']
    label = cfg['label']
    default = cfg.get('default')
    kwargs = cfg.get('widget_kwargs', {})
    doc = cfg.get('doc', '')

    help_text = doc if doc else None

    if widget_type == 'number_input':
        if isinstance(default, bool):
            return st.checkbox(label, value=default, key=key, help=help_text)

        optional = cfg.get('optional', False)

        if optional and default is None:
            return st.number_input(label, value=None, step=1,
                                   key=key, help=help_text)

        if isinstance(default, int):
            min_v = kwargs.get('min_value', None)
            max_v = kwargs.get('max_value', None)
            step_v = kwargs.get('step', 1)
            d = default
            if min_v is not None and d < min_v:
                d = min_v
            if max_v is not None and d > max_v:
                d = max_v
            return st.number_input(label, value=d, step=step_v,
                                   min_value=min_v, max_value=max_v,
                                   key=key, help=help_text)
        else:
            step_v = float(kwargs.get('step', 1))
            val = default if default is not None else 0.0
            fmt = kwargs.get('format', None)
            return st.number_input(label, value=float(val),
                                   step=step_v, format=fmt,
                                   key=key, help=help_text)

    elif widget_type == 'checkbox':
        return st.checkbox(label, value=bool(default), key=key, help=help_text)

    elif widget_type == 'text_input':
        return st.text_input(label, value=str(default) if default else '', key=key, help=help_text)

    elif widget_type == 'selectbox':
        options = kwargs.get('options', [])
        idx = 0
        if default in options:
            idx = options.index(default)
        return st.selectbox(label, options, index=idx, key=key, help=help_text)

    elif widget_type == 'date_input':
        from datetime import date
        d = default if isinstance(default, date) else date.today()
        return st.date_input(label, value=d, key=key, help=help_text)

    return None


def _render_dynamic_params(params_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Render UI controls for strategy params and return user values."""
    configs = StrategyAdapter.generate_widget_configs(params_meta)
    user_values = {}
    for cfg in configs:
        value = _dispatch_widget(cfg)
        if value is not None:
            user_values[cfg['key']] = value
    return user_values


def _render_batch_grid(params_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Render batch grid search configuration for numeric params.

    Shows a multiselect of numeric params, then start/end/step for each selected.
    """
    st.markdown('**Parameter Grid Search**')
    enable_batch = st.checkbox('Enable Grid Search', False, key='enable_batch')

    if not enable_batch:
        return {'enabled': False}

    numeric_params = {
        name: meta for name, meta in params_meta.items()
        if meta['type'] in (int, float) and not name.startswith('_')
    }

    if not numeric_params:
        st.info('This strategy has no numeric parameters for grid search.')
        return {'enabled': False}

    param_names = list(numeric_params.keys())
    selected_params = st.multiselect(
        'Select parameters for grid search',
        param_names,
        default=param_names[:min(2, len(param_names))],
        key='batch_params_select'
    )

    if not selected_params:
        return {'enabled': False}

    param_grid = {}
    for pname in selected_params:
        meta = numeric_params[pname]
        default_val = meta['default']
        is_int = meta['type'] == int
        step_default = 1 if is_int else 0.01

        st.markdown(f'**{pname}**')
        c1, c2, c3 = st.columns(3)
        with c1:
            start = st.number_input(
                f'{pname} start',
                value=max(1, default_val // 2) if isinstance(default_val, (int, float)) and default_val else 1,
                step=step_default, key=f'batch_{pname}_start'
            )
        with c2:
            end = st.number_input(
                f'{pname} end',
                value=max(start + step_default, default_val * 2 if isinstance(default_val, (int, float)) and default_val else start + 5),
                step=step_default, key=f'batch_{pname}_end'
            )
        with c3:
            step_val = st.number_input(
                f'{pname} step',
                value=step_default,
                step=step_default, key=f'batch_{pname}_step'
            )

        if is_int:
            start_v = int(start)
            end_v = int(end) + 1
            step_v = max(1, int(step_val))
        else:
            start_v = float(start)
            end_v = float(end) + step_val
            step_v = max(0.0001, float(step_val))

        vals = []
        v = start_v
        while v <= end_v:
            vals.append(v if is_int else round(v, 6))
            v += step_v
        if vals:
            param_grid[pname] = vals

    return {
        'enabled': True,
        'param_grid': param_grid,
    }


def render_sidebar(catalog: Dict[str, Any] = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Render dynamic sidebar with strategy discovery integration.

    Args:
        catalog: Dict of StrategyCatalogEntry from StrategyAutoDiscovery.discover()

    Returns:
        Tuple of (strategy_params, data_params, backtest_params, batch_params)
    """
    if catalog is None:
        catalog = {}

    with st.sidebar:
        st.header('📊 Backtest Configuration')

        st.markdown('### Quick Actions')
        col1, col2 = st.columns(2)
        with col1:
            if st.button('▶ Run Single', type='primary', use_container_width=True, key='sb_run'):
                st.session_state.run_backtest = True
                st.session_state.run_mode = 'single'
        with col2:
            if st.button('▶ Run Batch', type='secondary', use_container_width=True, key='sb_batch'):
                st.session_state.run_batch = True
                st.session_state.run_mode = 'batch'

        if st.button('🔄 Reset All', use_container_width=True, key='sb_reset'):
            st.session_state.clear()
            st.rerun()

        st.markdown('---')

        # --- Strategy Selection ---
        with st.expander('Strategy Settings', expanded=True):
            categories = sorted(set(e.category for e in catalog.values()))
            if not categories:
                st.warning('No strategies discovered.')
                strategy_params = {}
                selected_entry = None
            else:
                if 'selected_category' not in st.session_state:
                    st.session_state.selected_category = categories[0]
                selected_category = st.radio(
                    'Category',
                    categories,
                    horizontal=True,
                    key='selected_category'
                )

                filtered = [
                    e for e in catalog.values()
                    if e.category == selected_category
                ]
                filtered.sort(key=lambda e: (e.complexity != 'simple', e.class_name))

                strategy_labels = []
                for e in filtered:
                    badge = COMPLEXITY_BADGES.get(e.complexity, '')
                    strategy_labels.append(f'{e.class_name}{badge}')

                default_idx = 0
                selected_label = st.selectbox(
                    'Strategy',
                    strategy_labels,
                    index=default_idx,
                    key='selected_strategy_label'
                )

                clean_label = selected_label.rstrip(' ⚠🔴')
                selected_entry = next(
                    (e for e in filtered if e.class_name == clean_label), None
                )

                if selected_entry:
                    with st.expander('Strategy Info', expanded=False):
                        if selected_entry.docstring:
                            st.caption(selected_entry.docstring)
                        st.caption(f'Source: `{selected_entry.file_path}`')
                        for w in selected_entry.warnings:
                            st.warning(w)

            if selected_entry:
                if getattr(selected_entry.cls, '_needs_multi_data', False):
                    st.info('📊 Multi-stock strategy — data will be auto-fetched from Tushare for all bank stocks.')
                st.markdown('---')
                st.markdown('### Parameters')
                custom_params = _render_dynamic_params(selected_entry.params_meta)
                strategy_params = {
                    'strategy_key': selected_entry.key,
                    'class_name': selected_entry.class_name,
                    'category': selected_entry.category,
                    **custom_params,
                }
            else:
                strategy_params = {}

        # --- Data Source ---
        with st.expander('Data Source', expanded=False):
            data_source = st.selectbox(
                'Data Source',
                ['Sample Data', 'CSV File', 'Yahoo Finance', 'Tushare'],
                index=0,
                key='data_source',
            )

            data_params = {'source': data_source}

            # Common date range for all data sources
            from datetime import date
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                fromdate = st.date_input('Start Date', value=date(2020, 1, 1), key='fromdate')
                data_params['fromdate'] = fromdate
            with col_d2:
                todate = st.date_input('End Date', value=date(2025, 12, 31), key='todate')
                data_params['todate'] = todate

            if data_source == 'CSV File':
                csv_path = st.text_input('CSV Path', '', key='csv_path')
                data_params['csv_path'] = csv_path
            elif data_source == 'Yahoo Finance':
                ticker = st.text_input('Ticker', 'AAPL', key='ticker')
                data_params['ticker'] = ticker
            elif data_source == 'Tushare':
                ts_code = st.text_input('Stock Code', '000001.SZ', key='ts_code')
                data_params['ts_code'] = ts_code
                # Override with Tushare-format dates
                data_params['start_date'] = fromdate.strftime('%Y%m%d')
                data_params['end_date'] = todate.strftime('%Y%m%d')

        # --- Backtest Settings ---
        with st.expander('Backtest Settings', expanded=False):
            initial_cash = st.number_input(
                'Initial Cash ($)',
                1000.0,
                1000000.0,
                100000.0,
                1000.0,
                key='initial_cash',
            )
            commission = st.number_input(
                'Commission (%)',
                0.0,
                1.0,
                0.1,
                0.01,
                key='commission_pct',
            )
            position_pct = st.slider(
                'Position Size (% of cash)',
                10, 100, 95, 5,
                key='position_pct',
                help='Percentage of available cash used per trade. 95% = almost all-in.'
            )

            backtest_params = {
                'initial_cash': initial_cash,
                'commission': commission / 100.0,
                'position_pct': position_pct,
            }

        # --- Batch Backtest ---
        with st.expander('📊 Batch Backtest', expanded=False):
            if selected_entry and selected_entry.params_meta:
                batch_params = _render_batch_grid(selected_entry.params_meta)
                if selected_entry:
                    batch_params['strategy_key'] = selected_entry.key
            else:
                batch_params = {'enabled': False}

        # --- Log Viewer ---
        with st.expander('📋 Data Pipeline Logs', expanded=False):
            from utils.logger import get_logger
            lg = get_logger()
            if st.button('Clear Logs', key='clear_logs'):
                lg.clear()
            logs = lg.recent
            if logs:
                st.code(logs, language='text')
            else:
                st.caption('No logs yet. Run a backtest to see data pipeline logs.')

    return strategy_params, data_params, backtest_params, batch_params
