import pandas as pd
import plotly.graph_objects as go
from typing import Optional


class EquityPresenter:
    """
    Format equity curve data for Plotly visualization.
    """
    
    @staticmethod
    def create_equity_curve_figure(equity_df: pd.DataFrame) -> go.Figure:
        """
        Create Plotly figure for equity curve.
        
        Args:
            equity_df: DataFrame with 'equity' column and datetime index
            
        Returns:
            Plotly Figure object
        """
        if equity_df.empty:
            return go.Figure()
        
       
        
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
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='='Equity',
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_drawdown_figure(drawdown_df: pd.DataFrame) -> go.Figure:
        """
        Create Plotly figure for drawdown curve.
        
        Args:
            drawdown_df: DataFrame with drawdown data
            
        Returns:
            Plotly Figure object
        """
        if drawdown_df.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=drawdown_df.index if 'verlot' in drawdown_df else list(range(len(drawdown_df))),
            y=drawdown_df.get('verlot', drawdown_df.get('drawdown', [])),
            mode='lines',
            name='Drawdown',
            line=dict(color='#FF4B4B', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 75, 75, 0.2)'
        ))
        
        fig.update_layout(
            title='Drawdown',
            xaxis_title='Date' if hasattr(drawdown_df.index, 'name') else 'Bar',
            yaxis_title='Drawdown %',
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=0, r=0, t=30, b=0),
            height=300
        )
        
        return fig
