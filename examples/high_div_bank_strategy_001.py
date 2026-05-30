import backtrader as bt
import pandas as pd


def _fetch_bank_stocks():
    """Fetch all listed bank stock codes from Tushare."""
    try:
        from tushare_fetcher import _get_tushare_token
        import tushare as ts
        pro = ts.pro_api(_get_tushare_token())
        df = pro.stock_basic(exchange='', list_status='L',
                             fields='ts_code,name,industry')
        banks = df[df['industry'] == '银行']
        return list(banks['ts_code'])
    except Exception:
        return []


def _fetch_annual_cash_div(ts_codes, year, pro):
    """
    Fetch total cash dividend per share for each stock in the target year.

    Tushare dividend endpoint does not support multi-code batch queries,
    so we query one stock at a time.

    Returns: dict {ts_code: total_cash_div_per_share}
    """
    if pro is None:
        return {}

    result = {}
    for code in ts_codes:
        try:
            df_div = pro.dividend(ts_code=code)
        except Exception:
            result[code] = 0.0
            continue

        if df_div.empty:
            result[code] = 0.0
            continue

        df_div = df_div.drop_duplicates()
        df_div['end_date'] = pd.to_datetime(df_div['end_date'])
        df_div = df_div[df_div['end_date'].dt.year == year]
        df_div = df_div[df_div['div_proc'] == '实施']

        if df_div.empty:
            result[code] = 0.0
            continue

        result[code] = float(df_div['cash_div'].sum())

    return result


class HighDivBankStrategy001(bt.Strategy):
    """
    高股息股息率银行股策略001

    每年四月第一个交易日，按上一年度股息率对银行股排名，
    选取股息率最高的前N只等权配置。
    """

    params = (
        ('num_stocks', 5),
        ('rebalance_month', 4),
        ('bank_stocks',
         '601398.SH,601939.SH,601288.SH,601988.SH,601328.SH,'
         '600036.SH,601166.SH,600000.SH,600016.SH,601998.SH,'
         '601818.SH,000001.SZ,600015.SH,601169.SH,601009.SH,002142.SZ'),
        ('print_log', True),
    )

    # Signal to strategy auto-discovery that multiple data feeds are required
    _needs_multi_data = True

    def __init__(self):
        self.rebalanced_year = None
        self._tushare_pro = None
        # Map: Tushare stock code -> backtrader data feed
        self._feed_map = {}

        bank_codes = self._get_bank_stocks()
        # Build mapping from stock code to data feed
        for code in bank_codes:
            for d in self.datas:
                name = d._name or ''
                if name and code in name:
                    self._feed_map[code] = d
                    break

        if not self._feed_map:
            self._feed_map['__single__'] = self.data

        self.log(f'Initialized with {len(self._feed_map)} data feed(s) mapped')

    def _get_pro(self):
        if self._tushare_pro is None:
            try:
                from tushare_fetcher import _get_tushare_token
                import tushare as ts
                self._tushare_pro = ts.pro_api(_get_tushare_token())
            except Exception:
                self._tushare_pro = False
        return self._tushare_pro if self._tushare_pro is not False else None

    def _get_bank_stocks(self):
        """Parse bank_stocks param. If empty string, auto-discover from Tushare."""
        if self.p.bank_stocks and isinstance(self.p.bank_stocks, str):
            return [s.strip() for s in self.p.bank_stocks.split(',') if s.strip()]
        if isinstance(self.p.bank_stocks, list):
            return list(self.p.bank_stocks)
        return _fetch_bank_stocks()

    def log(self, txt, dt=None):
        if self.p.print_log:
            dt = dt or self.data.datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            side = 'BUY' if order.isbuy() else 'SELL'
            dname = getattr(order.data, '_name', '?')
            self.log(f'{side} {dname}, Price={order.executed.price:.2f}, '
                     f'Size={order.executed.size}, '
                     f'Cost={order.executed.value:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            dname = getattr(order.data, '_name', '?')
            self.log(f'Order {dname} Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if trade.isclosed:
            dname = getattr(trade.data, '_name', '?')
            self.log(f'TRADE CLOSED {dname}, Gross PnL={trade.pnl:.2f}, '
                     f'Net PnL={trade.pnlcomm:.2f}')

    def next(self):
        dt = self.data.datetime.date(0)

        # Already rebalanced this year
        if self.rebalanced_year == dt.year:
            return

        # Only rebalance in the configured month
        if dt.month != self.p.rebalance_month:
            return

        self.rebalanced_year = dt.year
        pro = self._get_pro()
        if pro is None:
            self.log('Tushare API unavailable, skip rebalance')
            return

        codes = list(self._feed_map.keys())
        prev_year = dt.year - 1

        # Fetch cash dividend per share for previous year
        cash_div = _fetch_annual_cash_div(codes, prev_year, pro)

        if not cash_div:
            self.log(f'No dividend data for year {prev_year}')
            return

        # Compute dividend yield = total_cash_div / current_close_price
        # Sort by yield descending
        scored = []
        for code, feed in self._feed_map.items():
            div = cash_div.get(code, 0)
            if div <= 0:
                continue
            price = feed.close[0]
            if price <= 0:
                continue
            div_yield = div / price
            scored.append((code, div_yield))

        if not scored:
            self.log(f'No stocks with positive dividend yield for {prev_year}')
            return

        scored.sort(key=lambda x: x[1], reverse=True)
        num = min(self.p.num_stocks, len(scored))
        buy_codes = {c for c, _ in scored[:num]}

        self.log(f'=== Annual Rebalance ({prev_year} dividends) ===')
        self.log(f'Top {num} by dividend yield:')
        for code, yld in scored[:num]:
            self.log(f'  {code}: {yld*100:.2f}%')

        # Sell positions not in buy list
        for code, feed in self._feed_map.items():
            pos = self.getposition(feed)
            if pos.size > 0 and code not in buy_codes:
                self.log(f'CLOSE {code} (no longer top {self.p.num_stocks})')
                self.close(data=feed)

        # Buy / rebalance selected stocks at equal weight
        target_pct = 1.0 / num
        for code in buy_codes:
            feed = self._feed_map[code]
            self.log(f'TARGET {code}: {target_pct*100:.1f}%')
            self.order_target_percent(data=feed, target=target_pct)

        self.log(f'=== End Rebalance ===')
