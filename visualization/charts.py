import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any


class ChartBuilder:
    """
    Build Plotly charts for backtrader visualization.
    Creates candlestick, indicator, and signal charts.
    """
    
    @staticmethod
    def create_candlestick_chart(
        df: pd.DataFrame,
        buy_signals: List[Dict[str, Any]] = None,
        sell_signals: List[Dict[str, Any]] = None,
        show_volume: bool = True
    ) -> go.Figure:
        """
        Create candlestick chart with optional buy/sell markers.
        
        Args:
            df: DataFrame with open, high, low, close, volume
            buy_signals: List of {'date': datetime, 'price': float}
            sell_signals: List of {'date': datetime, 'price': float}
            show_volume: Whether to show volume subplot
            
        Returns:
            Plotly Figure with candlestick and optional volume
        """
        if df.empty:
            return go.Figure()
        
        if show_volume:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                 vertical_spacing=0.03, row_heights=[0.7, 0.3])
        else:
            fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#00E676',
            increasing_fillcolor='rgba(0, 230, 118, 0.3)',
            decreasing_line_color='#FF4B4B',
            decreasing_fillcolor='rgba(255, 75, 75, 0.3)'
        ), row=1, col=1)
        
        if buy_signals:
            buy_dates = [s['date'] for s in buy_signals]
            buy_prices = [s['price'] for s in buy_signals]
            fig.add_trace(go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='Buy',
                marker=dict(symbol='triangle-up', size=12, color='#00E676', line=dict(width=2, color='white'))
            ), row=1, col=1)
        
        if sell_signals:
            sell_dates = [s['date'] for s in sell_signals]
            sell_prices = [s['price'] for s in sell_signals]
            fig.add_trace(go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='Sell',
                marker=dict(symbol='triangle-down', size=12, color='#FF4B4B', line=dict(width=2, color='white'))
            ), row=1, col=1)
        
        if show_volume:
            colors = ['#00E676' if df['close'][i] >= df['open'][i] else '#FF4B4B' 
                      for i in range(len(df))]
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ), row=2, col=1)
        
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        fig.update_yaxes(title_text='Price', row=1, col=1)
        if show_volume:
            fig.update_yaxes(title_text='Volume', row=2, col=1)
        
        return fig
    
    @staticmethod
    def create_line_chart(
        df: pd.DataFrame,
        y_columns: List[str],
        title: str = 'Line Chart',
        colors: List[str] = None
    ) -> go.Figure:
        """
        Create multi-line chart.
        
        Args:
            df: DataFrame with datetime index
            y_columns: List of column names to plot
            title: Chart title
            colors: Optional list of colors for each line
            
        Returns:
            Plotly Figure
        """
        if df.empty:
            return go.Figure()
        
        if colors is None:
            colors = ['#00E676', '#FF4B4B', '#FFA500', '#00BFFF']
        
        fig = go.Figure()
        
        for i, col in enumerate(y_columns):
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode='lines',
                    name=col,
                    line=dict(color=colors[i % len(colors)], width=2)
                ))
        
        fig.update_layout(
            title=title,
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )
        
        return fig
