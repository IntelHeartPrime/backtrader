from typing import Dict, Any
import pandas as pd


class MetricsPresenter:
    """
    Format backtest metrics for KPI card display.
    Handles null values and percentage formatting.
    """
    
    @staticmethod
    def format_metrics(metrics: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Convert raw analyzer output to display-ready KPI data.
        
        Args:
            metrics: Raw metrics from ResultsAdapter
            
        Returns:
            Dict with KPI card configs: {'metric_name': {'value': val, 'format': str, 'unit': str}}
        """
        return {
            'sharpe': {
                'value': metrics.get('sharpe'),
                'format': '.2f',
                'unit': '',
                'label': 'Sharpe Ratio'
            },
            'total_return': {
                'value': metrics.get('total_return'),
                'format': '.2%',
                'unit': '',
                'label': 'Total Return'
            },
            'annual_return': {
                'value': metrics.get('annual_return'),
                'format': '.2%',
                'unit': '',
                'label': 'Annual Return'
            },
            'max_drawdown': {
                'value': metrics.get('max_drawdown'),
                'format': '.2%',
                'unit': '',
                'label': 'Max Drawdown'
            },
            'total_trades': {
                'value': metrics.get('total_trades'),
                'format': 'd',
                'unit': '',
                'label': 'Total Trades'
            },
            'win_rate': {
                'value': metrics.get('win_rate'),
                'format': '.1f',
                'unit': '%',
                'label': 'Win Rate'
            }
        }
    
    @staticmethod
    def format_value(value: Any, format_str: str, unit: str = '') -> str:
        """
        Format a single metric value.
        
        Args:
            value: Metric value
            format_str: Format string (e.g., '.2f', '.2%', 'd')
            unit: Unit suffix
            
        Returns:
            Formatted string
        """
        if value is None:
            return 'N/A'
        
        if '%' in format_str:
            return f'{value:{format_str}}{unit}'
        elif format_str == 'd':
            return f'{int(value):d}{unit}'
        else:
            return f'{value:{format_str}}{unit}'
