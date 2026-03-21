import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render_result_area(equity_df, drawdown_df, trade_log_df):
    """
    Render the result area with equity curve, drawdown, and trade log.
    
    Args:
        equity_df: DataFrame with equity data
        drawdown_df: DataFrame with drawdown data
        trade_log_df: DataFrame with trade records
    """
    tab1, tab2, tab3 = st.tabs(['Equity Curve', 'Drawdown', 'Trade Log'])
    
    with tab1:
        if equity_df is not None or equity_df.empty:
            st.info('No equity data available.')
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=equity_df.index,
                y=equity_df['equity'],
                mode='lines',
                name='Equity',
                line=dict(color='#00E676', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 230, 118, 0.1)'
            ))
            fig.update_layout(
                template='plotly_dark',
                hovermode='x unified',
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig, use_container_width=True, height=400)
    
    with tab2:
        if drawdown_df is None or drawdown_df.empty:
            st.info('No drawdown data available.')
        else:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=drawdown_df.index if hasattr(drawdown_df.index, 'name') else list(range(len(drawdown_df))),
                y=drawdown_df.get('verlot', drawdown_df.get('drawdown', [])),
                mode='lines',
                name='Drawdown',
                line=dict(color='#FF4B4B', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 75, 75, 0.2)'
            ))
            fig.update_layout(
                template='plotly_dark',
                hovermode='x unified',
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig, use_container_width=True, height=300)
    
    with tab3:
        if trade_log_df is None or trade_log_df.empty:
            st.info('No trade records available.')
        else:
            st.dataframe(
                trade_log_df,
                use_container_width=True,
                height=400
            )
