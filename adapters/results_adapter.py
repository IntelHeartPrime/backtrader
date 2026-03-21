import backtrader as bt
from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd


class ResultsAdapter:
    """
    Extract backtest results from strategy instance for visualization.
    Converts analyzer outputs to presentation-friendly formats.
    """
    
    def __init__(self, strategy: bt.Strategy):
        self.strategy = strategy
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Extract key performance metrics for KPI cards.
        
        Returns:
            Dict with sharpe, max_drawdown, total_return, etc.
        """
        metrics = {
            'sharpe': None,
            'total_return': None,
            'max_drawdown': None,
            'total_trades': None,
            'win_rate': None
        }
        
        try:
            sharpe = self.strategy.analyzers.sharpe.get_analysis()
            metrics['sharpe'] = sharpe.get('sharperatio', None)
        except:
            pass
        
        try:
            drawdown = self.strategy.analyzers.drawdown.get_analysis()
            metrics['max_drawdown'] = drawdown.get('max', {}).get('drawdown', None)
        except:
            pass
        
        try:
            returns = self.strategy.analyzers.returns.get_analysis()
            metrics['total_return'] = returns.get('rtot', None)
            metrics['annual_return'] = returns.get('rnorm', None)
        except:
            pass
        
        try:
            trades = self.strategy.analyzers.tradeanalyzer.get_analysis()
            metrics['total_trades'] = trades.get('total', {}).get('total', None)
            
            won = trades.get('won', {}).get('total', 0)
            total = trades.get('total', {}).get('total', 0)
            metrics['win_rate'] = (won / total * 100) if total > 0 else None
        except:
            pass
        
        return metrics
    
    def get_equity_curve(self) -> pd.DataFrame:
        """
        Extract equity curve from TimeReturn analyzer.
        
        Returns:
            DataFrame with datetime index and cumulative returns
        """
        try:
            timereturn = self.strategy.analyzers.timereturn.get_analysis()
            
            dates = []
            values = []
            cumulative = 1.0
            
            for date, ret in sorted(timereturn.items()):
                cumulative *= (1 + ret)
                dates.append(date)
                values.append(cumulative)
            
            df = pd.DataFrame({'equity': values}, index=dates)
            df.index.name = 'date'
            return df
        except:
            return pd.DataFrame(columns=['equity'])
    
    def get_drawdown_curve(self) -> pd.DataFrame:
        """
        Extract drawdown over time.
        
        Returns:
            DataFrame with drawdown percentages
        """
        try:
            drawdown = self.strategy.analyzers.drawdown.get_analysis()
            return pd.DataFrame([drawdown])
        except:
            return pd.DataFrame()
    
    def get_trade_log(self) -> pd.DataFrame:
        """
        Extract detailed trade records from Transactions analyzer.
        
        Returns:
            DataFrame with trade details (date, direction, price, value)
        """
        try:
            transactions = self.strategy.analyzers.transactions.get_analysis()
            
            rows = []
            for data_key, data_trans in transactions.items():
                for date, trans_list in data_trans.items():
                    for trans in trans_list:
                        rows.append({
                            'date': date,
                            'data': data_key,
                            'amount': trans.get(0, 0),
                            'price': trans.get(1, 0),
                            'value': trans.get(2, 0)
                        })
            
            return pd.DataFrame(rows)
        except:
            return pd.DataFrame(columns=['date', 'data', 'amount', 'price', 'value'])
    
    def get_ohlcv_data(self) -> pd.DataFrame:
        """
        Extract OHLCV price data from strategy data feeds.
        
        Returns:
            DataFrame with datetime, open, high, low, close, volume
        """
        try:
            data = self.strategy.data
            dates = []
            opens, highs, lows, closes, volumes = [], [], [], []
            
            for i in range(len(data)):
                dates.append(data.datetime.date(i))
                opens.append(data.open[i])
                highs.append(data.high[i])
                lows.append(data.low[i])
                closes.append(data.close[i])
                volumes.append(data.volume[i])
            
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            }, index=dates)
            df.index.name = 'date'
            return df
        except:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def get_trade_signals(self) -> List[Dict[str, Any]]:
        """
        Extract buy/sell signals for plotting markers.
        
        Returns:
            List of {'date': datetime, 'type': 'buy'|'sell', 'price': float}
        """
        signals = []
        
        try:
            trades = self.strategy.analyzers.tradeanalyzer.get_analysis()
        except:
            return signals
        
        return signals
