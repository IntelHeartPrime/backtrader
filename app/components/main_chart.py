import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import Optional


def render_main_chart(ohlcv_df: pd.DataFrame, buy_signals=None, sell_signals=None):
    """
    Render the main price chart with candlestick and trade signals.
    
    Args:
        ohlcv_df: DataFrame with OHLCV data
        buy_signals: List of buy signal dicts
        sell_signals: List of sell signal dicts
    """
    st.subheader('Price Chart')
    
    if ohlcv_df is None or ohlcv_df.empty:
        st.info('No data to display. Run a backtest first.')
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Candlestick(
        x=ohlcv_df.index,
        open=ohlcv_df['open'],
        high=ohlcv_df['high'],
        low=ohlcv_df['low'],
        close=ohlcv_df['close'],
        name='Price',
        increasing_line_color='#00E676',
        increasing_fillcolor='rgba(0, 230, 118, 0.3)',
        decreasing_line_color='#FF4B4B',
        decreasing_fillcolor='rgba(255, 75, 75, 0.3)'
    ))
    
    if buy_signals:
        buy_dates = [s['date'] for s in buy_signals]
        buy_prices = [s['price'] for s in buy_signals]
        fig.add_trace(go.Scatter(
            x=buy_dates,
            y=buy_prices,
            mode='markers',
            name='Buy',
            marker=dict(symbol='triangle-up', size=15, color='#00E676', line=dict(width=2, color='white'))
        ))
    
    if sell_signals:
        sell_dates = [s['date'] for s in sell_signals]
        sell_prices = [s['price'] for s in sell_signals]
        fig.add_trace(go.Scatter(
            x=sell_dates,
            y=sell_prices,
            mode='markers',
            name='Sell',
            marker=dict(symbol='triangle-down', size=15, color='#FF4B4B', line=dict(width=2, color='white'))
        ))
    
    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis_rangeslider_visible=True
    )
    
    st.plotly_chart(fig, use_container_width=True, height=600)
