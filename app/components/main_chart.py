import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def render_main_chart(equity_df: pd.DataFrame, buy_signals=None, sell_signals=None):
    """
    Render the main equity curve line chart with optional trade signal markers.

    Args:
        equity_df: DataFrame with 'equity' column and datetime index
        buy_signals: List of buy signal dicts with 'date' and 'price'
        sell_signals: List of sell signal dicts with 'date' and 'price'
    """
    st.subheader('Net Value Curve')

    if equity_df is None or equity_df.empty or 'equity' not in equity_df.columns:
        st.info('No data to display. Run a backtest first.')
        return

    eq_vals = equity_df['equity'].values
    eq_unique = len(set(round(v, 2) for v in eq_vals))

    if eq_unique <= 1:
        st.warning(
            'Net value is flat — this strategy did not generate any trades '
            'with the current data and settings. '
            'Try a different strategy, a larger date range, or check the '
            'strategy warnings in the sidebar.'
        )
        return

    pct_change = (eq_vals[-1] - eq_vals[0]) / eq_vals[0] * 100
    color = '#00E676' if pct_change >= 0 else '#FF4B4B'
    fill_rgba = 'rgba(0, 230, 118, 0.08)' if pct_change >= 0 else 'rgba(255, 75, 75, 0.08)'

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity_df.index,
        y=equity_df['equity'],
        mode='lines',
        name='Net Value',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=fill_rgba
    ))

    if buy_signals:
        buy_dates = [s['date'] for s in buy_signals]
        buy_prices = [s['price'] for s in buy_signals]
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy',
            marker=dict(symbol='triangle-up', size=12, color='#00E676',
                        line=dict(width=1, color='white'))
        ))

    if sell_signals:
        sell_dates = [s['date'] for s in sell_signals]
        sell_prices = [s['price'] for s in sell_signals]
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell',
            marker=dict(symbol='triangle-down', size=12, color='#FF4B4B',
                        line=dict(width=1, color='white'))
        ))

    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=10, b=0),
        height=500,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_title='Date',
        yaxis_title='Net Value',
    )

    st.plotly_chart(fig, use_container_width=True)
