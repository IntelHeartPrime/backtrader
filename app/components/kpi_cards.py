import streamlit as st
import pandas as pd
from typing import Dict, Any


def _format_metric_value(value: Any, fmt: str) -> str:
    """Format a scalar for display; missing values -> 'N/A'."""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        if pd.isna(value):
            return 'N/A'
    except TypeError:
        pass
    try:
        if fmt == 'd':
            return f'{int(value):d}'
        return f'{value:{fmt}}'
    except (TypeError, ValueError):
        return 'N/A'


def render_kpi_cards(metrics: Dict[str, Any]):
    """
    Render KPI cards in a horizontal layout.

    Args:
        metrics: Flat dict from ResultsAdapter.get_metrics()
    """
    st.subheader('Performance Metrics')

    cols = st.columns(3)

    card_configs = [
        ('Total Return', metrics.get('total_return'), '.2%'),
        ('Sharpe Ratio', metrics.get('sharpe'), '.2f'),
        ('Max Drawdown', metrics.get('max_drawdown'), '.2%'),
        ('Annual Return', metrics.get('annual_return'), '.2%'),
        ('Total Trades', metrics.get('total_trades'), 'd'),
        ('Win Rate', metrics.get('win_rate'), '.1f'),
    ]

    for i, (label, value, fmt) in enumerate(card_configs):
        with cols[i % 3]:
            formatted_value = _format_metric_value(value, fmt)
            if formatted_value == 'N/A':
                st.metric(label, 'N/A', delta=None)
            elif fmt.endswith('%'):
                # .2% 等已在字符串中带 %
                st.metric(label, formatted_value, delta=None)
            elif label == 'Win Rate':
                st.metric(label, f'{formatted_value}%', delta=None)
            else:
                st.metric(label, formatted_value, delta=None)
