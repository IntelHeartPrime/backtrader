#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader with Tushare Data Source Example

This example demonstrates how to:
1. Fetch stock data from Tushare API
2. Load it into backtrader using TushareData
3. Run a simple moving average crossover strategy
4. Automatically launch Streamlit visualization

Requirements:
    pip install tushare backtrader[plotting]
    pip install streamlit plotly
    # or: pip install -r requirements.txt

Configuration:
    Create .env file from .env.example and fill in your Tushare API token
    Or set TUSHARE_TOKEN environment variable
"""

import backtrader as bt
import importlib.util
import sys
import os
import socket
import subprocess
import time
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tushare_fetcher import get_tushare_data


def _wait_local_port(port, process, timeout=45, host='127.0.0.1'):
    """Wait until something accepts TCP connections on host:port or process exits."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        finally:
            sock.close()
        time.sleep(0.25)
    return False


class SmaCrossStrategy(bt.Strategy):
    """
    Simple moving average crossover strategy

    Buy when close price crosses above SMA
    Sell when close price crosses below SMA
    """

    params = (
        ('sma_period', 20),
        ('print_log', True),
    )

    def __init__(self):
        self.sma = bt.indicators.SMA(self.data.close, period=self.p.sma_period)
        self.close = self.data.close

    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.data.datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                          f'Cost: {order.executed.value:.2f}, '
                          f'Comm: {order.executed.comm:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                          f'Cost: {order.executed.value:.2f}, '
                          f'Comm: {order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'TRADE CLOSED, PnL: {trade.pnl:.2f}, PnL Net: {trade.pnlcomm:.2f}')

    def next(self):
        if not self.position:
            if self.close[0] > self.sma[0]:
                self.buy()
        else:
            if self.close[0] < self.sma[0]:
                self.sell()


def run_example():
    # Tushare daily API requires YYYYMMDD (see https://tushare.pro/document/2?doc_id=27)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stock_code = '000001.SZ'
    start_date = '20250101'
    end_date = '20251231'

    print(f'Fetching data for {stock_code} from {start_date} to {end_date}...')
    print()

    try:
        df = get_tushare_data(
            ts_code=stock_code,
            start_date=start_date,
            end_date=end_date
        )
        print(f'Fetched {len(df)} bars of data')
        print(df.head())
        print()
    except Exception as e:
        print(f'Error fetching data: {e}')
        print()
        print('Please ensure you have set your Tushare API token:')
        print('  Option 1: Set TUSHARE_TOKEN environment variable')
        print('  Option 2: Create .env file from .env.example and fill in your token')
        return

    cerebro = bt.Cerebro()

    cerebro.addstrategy(SmaCrossStrategy, sma_period=20, print_log=True)

    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.TimeReturn, timeframe=bt.TimeFrame.Days, _name='timereturn')
    cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
    cerebro.addanalyzer(bt.analyzers.PositionsValue, _name='positionsvalue')

    print('Starting backtest...')
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')
    print()

    results = cerebro.run()

    strat = results[0]

    final_value = cerebro.broker.getvalue()
    print()
    print(f'Final Portfolio Value: {final_value:.2f}')
    print(f'Total Return: {(final_value - 100000.0) / 100000.0 * 100:.2f}%')

    sharpe = strat.analyzers.sharpe.get_analysis()
    sharpe_ratio = sharpe.get('sharperatio')
    print(f'Sharpe Ratio: {sharpe_ratio:.2f}' if sharpe_ratio is not None else 'Sharpe Ratio: N/A')

    drawdown = strat.analyzers.drawdown.get_analysis()
    print(f'Max Drawdown: {drawdown.max.drawdown:.2f}%')

    returns = strat.analyzers.returns.get_analysis()
    avg_return = returns.get('rnorm100')
    print(f'Average Return: {avg_return:.2f}%' if avg_return is not None else 'Average Return: N/A')

    print()
    print('=' * 60)
    print('✅ Backtest completed!')
    print('🚀 Launching Streamlit visualization...')
    print('=' * 60)
    print()

    if importlib.util.find_spec('streamlit') is None:
        print('❌ 当前 Python 环境未安装 streamlit（与子进程使用的是同一解释器）。')
        print(f'   解释器: {sys.executable}')
        print('   请执行: python -m pip install streamlit plotly')
        print('   或安装项目依赖: python -m pip install -r requirements.txt')
        rel_main = os.path.join('app', 'main.py')
        print(f'   安装后也可手动: streamlit run {rel_main}')
        return

    streamlit_app = os.path.join(project_root, 'app', 'main.py')
    streamlit_url = 'http://localhost:8501'
    try:
        proc = subprocess.Popen(
            [sys.executable, '-m', 'streamlit', 'run', streamlit_app],
            cwd=project_root,
        )
    except Exception as e:
        print(f'❌ Error launching visualization: {e}')
        print('💡 Install: pip install streamlit plotly')
        print(
            f'💡 Or from project root: streamlit run {os.path.join("app", "main.py")}'
        )
        return

    print('Waiting for Streamlit to listen on port 8501...')
    if not _wait_local_port(8501, proc):
        if proc.poll() is not None:
            print(
                '❌ Streamlit exited early (see traceback above). '
                'Common causes: missing deps or import errors in app/main.py.'
            )
            print(
                '   If you see "No module named streamlit", run:\n'
                f'   {sys.executable} -m pip install streamlit plotly'
            )
        else:
            print('❌ Timed out waiting for port 8501.')
        rel_main = os.path.join('app', 'main.py')
        print(f'💡 From project root: streamlit run {rel_main}')
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return

    try:
        webbrowser.open(streamlit_url)
        print(f'✅ Opened {streamlit_url} in your browser')
    except OSError:
        print(f'📋 Open {streamlit_url} in your browser manually')

    print('💡 Press Ctrl+C here to stop the Streamlit server')
    print()
    try:
        proc.wait()
    except KeyboardInterrupt:
        print('\n🛑 Stopping Streamlit...')
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == '__main__':
    run_example()
