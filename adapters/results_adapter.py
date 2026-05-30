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
            raw_dd = drawdown.get('max', {}).get('drawdown', None)
            # Normalize to ratio: analyzer returns e.g. -15.0 for -15%
            metrics['max_drawdown'] = raw_dd / 100.0 if raw_dd is not None else None
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
    
    def get_equity_curve(self, initial_cash: float = 100000.0) -> pd.DataFrame:
        """
        Extract equity curve from TimeReturn analyzer.

        Args:
            initial_cash: Starting cash amount for dollar-denominated equity

        Returns:
            DataFrame with datetime index and 'equity' column in dollar values
        """
        try:
            timereturn = self.strategy.analyzers.timereturn.get_analysis()

            dates = []
            values = []
            cumulative = initial_cash

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
        Compute drawdown curve from equity curve.

        Returns:
            DataFrame with datetime index and 'drawdown' column (negative values)
        """
        try:
            equity_df = self.get_equity_curve()
            if equity_df.empty:
                return pd.DataFrame(columns=['drawdown'])

            running_max = equity_df['equity'].cummax()
            drawdown = (equity_df['equity'] - running_max) / running_max

            result = pd.DataFrame({'drawdown': drawdown}, index=equity_df.index)
            result.index.name = 'date'
            return result
        except Exception:
            return pd.DataFrame(columns=['drawdown'])
    
    def get_trade_log(self) -> pd.DataFrame:
        """
        Extract detailed trade records from Transactions analyzer.

        Returns:
            DataFrame with trade details (date, amount, price, value)
        """
        try:
            transactions = self.strategy.analyzers.transactions.get_analysis()

            rows = []
            # Transactions analyzer returns: OrderedDict({datetime: [[amount, price, ...], ...]})
            if isinstance(transactions, dict):
                for date, trans_list in transactions.items():
                    for trans in trans_list:
                        # Each trans is a list: [amount, price, size, '', value]
                        if not isinstance(trans, (list, tuple)):
                            continue
                        amount = trans[0] if len(trans) > 0 else 0
                        price = trans[1] if len(trans) > 1 else 0
                        value = trans[4] if len(trans) > 4 else (trans[2] if len(trans) > 2 else 0)
                        rows.append({
                            'date': date,
                            'amount': amount,
                            'price': price,
                            'value': value,
                        })

            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame(columns=['date', 'amount', 'price', 'value'])
    
    def get_ohlcv_data(self) -> pd.DataFrame:
        """
        Extract OHLCV price data from strategy data feeds.

        After ``cerebro.run()``, the feed cursor is on the last bar: index ``0``
        is the latest bar, ``-1`` the previous, etc. Positive indices are not
        valid for walking history.

        Returns:
            DataFrame with datetime index and open, high, low, close, volume
        """
        try:
            data = self.strategy.data
            n = len(data)
            if n == 0:
                return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])

            dates = []
            opens, highs, lows, closes, volumes = [], [], [], [], []
            for ago in range(-(n - 1), 1):
                dates.append(data.datetime.date(ago))
                opens.append(float(data.open[ago]))
                highs.append(float(data.high[ago]))
                lows.append(float(data.low[ago]))
                closes.append(float(data.close[ago]))
                volumes.append(float(data.volume[ago]))

            df = pd.DataFrame(
                {
                    'open': opens,
                    'high': highs,
                    'low': lows,
                    'close': closes,
                    'volume': volumes,
                },
                index=dates,
            )
            df.index.name = 'date'
            return df
        except Exception:
            return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
    
    def get_trade_signals(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract buy/sell markers for the price chart (from Transactions analyzer).

        Returns:
            {'buys': [{'date', 'price'}, ...], 'sells': [...]}
        """
        buys: List[Dict[str, Any]] = []
        sells: List[Dict[str, Any]] = []
        try:
            transactions = self.strategy.analyzers.transactions.get_analysis()
            for _data_key, data_trans in transactions.items():
                for date, trans_list in data_trans.items():
                    for trans in trans_list:
                        amount = trans.get(0, 0)
                        price = float(trans.get(1, 0) or 0)
                        row = {'date': date, 'price': price}
                        if amount > 0:
                            buys.append(row)
                        elif amount < 0:
                            sells.append(row)
        except Exception:
            pass
        return {'buys': buys, 'sells': sells}
