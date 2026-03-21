import streamlit as st
import pandas as pd
from typing import Dict, Any


def render_kpi_cards(metrics: Dict[str, Any]):
    """
    Render KPI cards in a horizontal layout.
    
    Args:
        metrics: Dict with metric names as keys and values as dicts
    """
    st.subheader('Performance Metrics')
    
    cols = st.columns(3)
    
    card_configs = [
        ('Total Return', metrics.get('total_return', 'N/A'), '.2%'),
        ('Sharpe Ratio', metrics.get('sharpe', 'N/A'), '.2f'),
        ('Max Drawdown', metrics.get('max_drawdown', 'N/A'), '.2%'),
        ('Annual Return', metrics.get('annual_return', 'N/A'), '.2%'),
        ('Total Trades', metrics.get('total_trades', 'N/A'), 'd'),
        ('Win Rate', metrics.get('win_rate', 'N/A'), '.1f')
    ]
    
    for i, (label, value, fmt) in enumerate(card_configs):
        with cols[i % 3]:
            formatted_value = value if value == 'N/A' else f'{value:{fmt}}'
            if 'Return' in label or 'Drawdown' in label or 'Rate' in label:
                st.metric(label, f'{formatted_value}%', delta=None)
            else:
                st.metric(label, formatted_value, delta=None)
