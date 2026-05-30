import backtrader as bt


class BuySellStrategy(bt.Strategy):
    """Simple golden-cross strategy: buy on fast MA crossing above slow MA, sell on opposite."""

    params = (
        ('fast_period', 5),
        ('slow_period', 20),
        ('print_log', False),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(self.data.close, period=self.p.fast_period)
        self.slow_ma = bt.indicators.SMA(self.data.close, period=self.p.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()
