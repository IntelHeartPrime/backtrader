import streamlit as st
from typing import Dict, Any, Tuple


def render_sidebar() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """
    Render the left sidebar control panel.
    
    Returns:
        Tuple of (strategy_params, data_params, backtest_params)
    """
    st.sidebar.header('Backtest Configuration')
    
    with st.sidebar.expander('Strategy Settings', expanded=True):
        strategy_name = st.selectbox(
            'Strategy',
            ['SmaCrossStrategy', 'BuySellStrategy'],
            index=0
        )
        
        st.sidebar.markdown('---')
        
        if strategy_name == 'SmaCrossStrategy':
            sma_period = st.sidebar.slider('SMA Period', 5, 50, 20)
            print_log = st.sidebar.checkbox('Print Logs', False)
            strategy_params = {'sma_period': sma_period, 'print_log': print_log}
        else:
            strategy_params = {}
    
    with st.sidebar.expander('Data Source', expanded=True):
        data_source = st.sidebar.selectbox(
            'Data Source',
            ['Sample Data', 'CSV File', 'Yahoo Finance'],
            index=0
        )
        
        if data_source == 'CSV File':
            csv_path = st.sidebar.text_input('CSV Path', '')
        elif data_source == 'Yahoo Finance':
            ticker = st.sidebar.text_input('Ticker', 'AAPL')
        
        data_params = {'source': data_source}
    
    with st.sidebar.expander('Backtest Settings', expanded=True):
        initial_cash = st.sidebar.number_input(
            'Initial Cash ($)',
            1000.0,
            1000000.0,
            100000.0,
            1000.0
        )
        commission = st.sidebar.number_input(
            'Commission (%)',
            0.0,
            1.0,
            0.1,
            0.01
        )
        
        backtest_params = {
            'initial_cash': initial_cash,
            'commission': commission / 100.0
        }
    
    st.sidebar.markdown('---')
    
    if st.sidebar.button('Run Backtest', type='primary', use_container_width=True):
        st.session_state.run_backtest = True
    
    if st.sidebar.button('Reset', use_container_width=True):
        st.session_state.clear()
        st.rerun()
    
    return strategy_params, data_params, backtest_params
