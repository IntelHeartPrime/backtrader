import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

from app.components.kpi_cards import render_kpi_cards
from presenters.metrics_presenter import MetricsPresenter


def render_batch_results(batch_results: List[Dict[str, Any]]):
    """
    Render batch backtest results with equity curve comparison.
    
    Args:
        batch_results: List of backtest result dictionaries
    """
    if not batch_results:
        st.info('No batch results to display')
        return
    
    st.subheader('📊 Batch Backtest Results')
    
    tabs = st.tabs(['Equity Comparison', 'Metrics Table', 'Performance Rankings'])
    
    with tabs[0]:
        st.markdown('### Equity Curve Comparison')
        
        fig = go.Figure()
        
        colors = ['#00E676', '#00BFFF', '#FFA500', '#FF4B4B', '#E0E7FF', '#7C4DFF']
        
        for i, result in enumerate(batch_results):
            if 'equity' in result and not result['equity'].empty:
                fig.add_trace(go.Scatter(
                    x=result['equity'].index,
                    y=result['equity']['equity'],
                    mode='lines',
                    name=result.get('label', f'Strategy {i+1}'),
                    line=dict(color=colors[i % len(colors)], width=2),
                ))
        
        fig.update_layout(
            template='plotly_dark',
            hovermode='x unified',
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            xaxis_title='Date',
            yaxis_title='Equity',
        )
        
        st.plotly_chart(fig, use_container_width=True, height=500)
    
    with tabs[1]:
        st.markdown('### Metrics Comparison Table')

        metrics_data = []
        for result in batch_results:
            if 'metrics' in result:
                label = result.get('label', 'Unknown')
                metrics = result['metrics']
                configs = MetricsPresenter.format_metrics(metrics)

                row = {'Strategy': label}
                for key, cfg in configs.items():
                    row[cfg['label']] = MetricsPresenter.format_value(
                        cfg['value'], cfg['format'], cfg['unit']
                    )
                metrics_data.append(row)

        if metrics_data:
            df = pd.DataFrame(metrics_data)
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )
        else:
            st.info('No metrics data available')
    
    with tabs[2]:
        st.markdown('### Performance Rankings')
        
        rankings = []
        for result in batch_results:
            if 'metrics' in result:
                label = result.get('label', 'Unknown')
                metrics = result['metrics']
                
                sharpe = metrics.get('sharpe', 0) or 0
                total_return = metrics.get('total_return', 0) or 0
                
                rankings.append({
                    'Rank': len(rankings) + 1,
                    'Strategy': label,
                    'Sharpe Score': sharpe,
                    'Total Return (%)': total_return * 100,
                })
        
        if rankings:
            df = pd.DataFrame(rankings)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('#### By Sharpe Ratio')
                sharpe_sorted = df.sort_values('Sharpe Score', ascending=False)
                st.dataframe(
                    sharpe_sorted,
                    use_container_width=True,
                    height=300
                )
            
            with col2:
                st.markdown('#### By Total Return')
                return_sorted = df.sort_values('Total Return (%)', ascending=False)
                st.dataframe(
                    return_sorted,
                    use_container_width=True,
                    height=300
                )
            
            with col3:
                st.markdown('#### Summary Stats')
                st.metric('Total Backtests', len(rankings))
                st.metric('Best Sharpe', f"{df['Sharpe Score'].max():.2f}")
                st.metric('Best Return', f"{df['Total Return (%)'].max():.2f}%")
        else:
            st.info('No ranking data available')


def render_single_results(results: Dict[str, Any]):
    """
    Render single backtest results.
    
    Args:
        results: Backtest result dictionary
    """
    st.markdown('### 📊 Performance Metrics')
    render_kpi_cards(results.get('metrics', {}))
    
    st.markdown('---')
    
    col_chart, col_results = st.columns([2, 1])
    
    with col_chart:
        from app.components.main_chart import render_main_chart
        render_main_chart(
            equity_df=results.get('equity'),
            buy_signals=results.get('signals', {}).get('buys', []),
            sell_signals=results.get('signals', {}).get('sells', [])
        )
    
    with col_results:
        from app.components.result_area import render_result_area
        render_result_area(
            equity_df=results.get('equity'),
            drawdown_df=results.get('drawdown'),
            trade_log_df=results.get('trade_log')
        )