import backtrader as bt
from typing import Dict, Any, Optional, Union, Callable
from datetime import datetime
import pandas as pd
import os

from utils.logger import get_logger

log = get_logger()


class DataAdapter:
    """
    Factory for creating backtrader data feeds from UI input.
    Supports multiple data sources: CSV, Yahoo, Pandas.
    """
    
    @staticmethod
    def create_csv_data(
        filepath: str,
        datetime_format: Union[str, Callable[[str], datetime]] = '%Y-%m-%d',
        open_col: int = 1,
        high_col: int = 2,
        low_col: int = 3,
        close_col: int = 4,
        volume_col: int = 5,
        openinterest_col: int = -1,
        fromdate: Optional[datetime] = None,
        todate: Optional[datetime] = None
    ) -> bt.feeds.GenericCSVData:
        """
        Create data feed from CSV file.

        Column indices follow GenericCSVData: datetime defaults to column 0;
        OHLCV default to columns 1–5 (column 0 is the date/time field).

        Args:
            filepath: Path to CSV file
            datetime_format: strptime format, or a callable (str -> datetime)
            open_col/high_col/low_col/close_col/volume_col: Column indices
            openinterest_col: Open interest column, or -1 if absent
            fromdate: Start date filter
            todate: End date filter
        """
        data = bt.feeds.GenericCSVData(
            dataname=filepath,
            dtformat=datetime_format,
            datetime=0,
            open=open_col,
            high=high_col,
            low=low_col,
            close=close_col,
            volume=volume_col,
            openinterest=openinterest_col,
            fromdate=fromdate,
            todate=todate
        )
        return data
    
    @staticmethod
    def create_yahoo_data(
        ticker: str,
        fromdate: Optional[datetime] = None,
        todate: Optional[datetime] = None
    ) -> bt.feeds.YahooFinanceData:
        """
        Create data feed from Yahoo Finance.
        
        Args:
            ticker: Stock symbol (e.g., 'AAPL')
            fromdate: Start date
            todate: End date
        """
        data = bt.feeds.YahooFinanceData(
            dataname=ticker,
            fromdate=fromdate,
            todate=todate
        )
        return data
    
    @staticmethod
    def create_pandas_data(
        dataframe: pd.DataFrame,
        datetime_col: Optional[str] = 'date',
        fromdate: Optional[datetime] = None,
        todate: Optional[datetime] = None
    ) -> bt.feeds.PandasData:
        """
        Create data feed from Pandas DataFrame.
        
        Args:
            dataframe: DataFrame with OHLCV data
            datetime_col: Name of datetime column
            fromdate: Start date filter
            todate: End date filter
        """
        data = bt.feeds.PandasData(
            dataname=dataframe,
            datetime=datetime_col,
            fromdate=fromdate,
            todate=todate
        )
        return data
    
    @staticmethod
    def get_sample_data_path() -> Optional[str]:
        """
        Return path to sample data file if available.
        """
        import os
        sample_path = os.path.join(
            os.path.dirname(__file__),
            '../datas/ticksample.csv'
        )
        if os.path.exists(sample_path):
            return sample_path
        return None

    @staticmethod
    def _parse_iso_datetime(dt_str: str) -> datetime:
        """Parse ISO-8601 datetime strings like '2015-09-23T20:57:42.146'."""
        return datetime.strptime(dt_str[:19], '%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def create_from_params(data_params: Dict[str, Any]):
        """
        Create a data feed from the sidebar data_params dict.

        Supported sources: 'Sample Data', 'CSV File', 'Yahoo Finance', 'Tushare'
        """
        source = data_params.get('source', 'Sample Data')
        log.info(f'DataAdapter: creating feed from source={source}')

        fromdate = data_params.get('fromdate')
        todate = data_params.get('todate')
        # Convert date objects to datetime
        if fromdate is not None and not isinstance(fromdate, datetime):
            fromdate = datetime.combine(fromdate, datetime.min.time())
        if todate is not None and not isinstance(todate, datetime):
            todate = datetime.combine(todate, datetime.min.time())

        log.debug(f'Date filter: fromdate={fromdate}, todate={todate}')

        if source == 'Sample Data':
            path = DataAdapter.get_sample_data_path()
            if path is None:
                log.error('Sample data file not found')
                raise FileNotFoundError('Sample data file not found')
            log.info(f'Loading sample CSV: {path}')
            data = DataAdapter.create_csv_data(
                path, datetime_format=DataAdapter._parse_iso_datetime,
                fromdate=fromdate, todate=todate
            )
            log.info(f'Sample CSV data feed created OK')
            return data

        elif source == 'CSV File':
            csv_path = data_params.get('csv_path', '')
            if not csv_path or not os.path.exists(csv_path):
                log.error(f'CSV file not found: {csv_path}')
                raise FileNotFoundError(f'CSV file not found: {csv_path}')
            log.info(f'Loading CSV: {csv_path}')
            data = DataAdapter.create_csv_data(
                csv_path, fromdate=fromdate, todate=todate
            )
            log.info(f'CSV data feed created OK')
            return data

        elif source == 'Yahoo Finance':
            try:
                import yfinance as yf
                log.debug(f'yfinance version: {yf.__version__}')
            except ImportError:
                log.error('yfinance not installed')
                raise ImportError(
                    'yfinance not installed. Run: pip install yfinance'
                )
            ticker = data_params.get('ticker', 'AAPL')
            start = fromdate.strftime('%Y-%m-%d') if fromdate else '2020-01-01'
            end = todate.strftime('%Y-%m-%d') if todate else '2025-12-31'
            log.info(f'Yahoo Finance: ticker={ticker}, range={start}~{end}')
            try:
                df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
            except Exception as e:
                log.error(f'Yahoo Finance download failed: {e}')
                raise ConnectionError(
                    f'Failed to fetch data for {ticker}. '
                    'Check your network connection or try Tushare instead.'
                )
            if df is None or df.empty:
                log.error(f'Yahoo Finance returned empty data for {ticker}')
                raise ValueError(f'No data returned for {ticker}')
            log.info(f'Yahoo Finance returned {len(df)} rows, columns={list(df.columns)}')
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower() for c in df.columns]
                log.debug(f'Flattened multi-index columns: {list(df.columns)}')
            else:
                df.columns = [c.lower() for c in df.columns]
            if 'date' not in df.columns:
                df = df.reset_index()
                log.debug('Reset index to expose date column')
            data = DataAdapter.create_pandas_data(df)
            log.info(f'Yahoo Finance data feed created OK: {len(df)} bars')
            return data

        elif source == 'Tushare':
            from tushare_fetcher import get_tushare_data
            ts_code = data_params.get('ts_code', '000001.SZ')
            start_date = data_params.get('start_date', '20250101')
            end_date = data_params.get('end_date', '20251231')
            log.info(f'Tushare: ts_code={ts_code}, range={start_date}~{end_date}')
            df = get_tushare_data(ts_code=ts_code, start_date=start_date, end_date=end_date)
            # Tushare data has date as the index, not a column
            data = DataAdapter.create_pandas_data(
                df, datetime_col=None, fromdate=fromdate, todate=todate
            )
            log.info(f'Tushare data feed created OK: {len(df)} bars, datetime from index')
            return data

        else:
            log.error(f'Unknown data source: {source}')
            raise ValueError(f'Unknown data source: {source}')

    @staticmethod
    def create_multi_tushare_data(
        ts_codes,
        start_date='20200101',
        end_date='20251231',
        fromdate=None,
        todate=None
    ):
        """
        Create multiple backtrader data feeds from Tushare for a list of stocks.

        Args:
            ts_codes: List of Tushare stock codes (e.g. ['601398.SH', '600036.SH'])
            start_date: Start date in 'YYYYMMDD' format
            end_date: End date in 'YYYYMMDD' format
            fromdate: Optional datetime filter start
            todate: Optional datetime filter end

        Returns:
            List of bt.feeds.PandasData ready to add to cerebro
        """
        from tushare_fetcher import get_tushare_multiple_stocks
        import pandas as pd

        log.info(f'DataAdapter: fetching {len(ts_codes)} stocks from Tushare, '
                 f'range={start_date}~{end_date}')
        stock_dfs = get_tushare_multiple_stocks(ts_codes, start_date, end_date)

        feeds = []
        for code in ts_codes:
            df = stock_dfs.get(code)
            if df is None or df.empty:
                log.warning(f'No data for {code}, skipping')
                continue

            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                log.warning(f'{code}: index is not DatetimeIndex, skipping')
                continue

            feed = bt.feeds.PandasData(
                dataname=df,
                datetime=None,  # index is datetime
                open=0, high=1, low=2, close=3, volume=4,
                fromdate=fromdate,
                todate=todate,
                name=code,
            )
            feeds.append(feed)
            log.debug(f'{code}: {len(df)} bars, '
                      f'{df.index[0].strftime("%Y-%m-%d")}~{df.index[-1].strftime("%Y-%m-%d")}')

        log.info(f'Created {len(feeds)} multi-stock data feeds from Tushare')
        return feeds
