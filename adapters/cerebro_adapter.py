import backtrader as bt
from typing import Optional, Dict, Any, List
from datetime import datetime


class CerebroAdapter:
    """
    Adapter for Cerebro engine that encapsulates backtest execution
    with standard analyzers and result extraction.
    """
    
    def __init__(self, initial_cash: float = 100000.0):
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self._results = None
        self._data_feeds: List = []
        self._strategy = None
    
    def add_strategy(self, strategy_class, **kwargs):
        self._strategy = strategy_class
        self.cerebro.addstrategy(strategy_class, **kwargs)
        return self
    
    def add_data(self, data_feed):
        self._data_feeds.append(data_feed)
        self.cerebro.adddata(data_feed)
        return self
    
    def set_commission(self, commission: float = 0.001):
        self.cerebro.broker.setcommission(commission=commission)
        return self
    
    def add_standard_analyzers(self):
        """Add standard analyzers for KPI and visualization"""
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Days, _name='timereturn')
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
        self.cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='positionsvalue')
        return self
    
    def run(self) -> List:
        """Execute backtest and return results"""
        self._results = self.cerebro.run()
        return self._results
    
    def get_strategy(self):
        """Get the first strategy instance"""
        if self._results and len(self._results) > 0:
            return self._results[0]
        return None
    
    def get_initial_cash(self) -> float:
        return self.cerebro.broker.getcash()
