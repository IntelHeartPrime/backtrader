import backtrader as bt
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd


class DataAdapter:
    """
    Factory for creating backtrader data feeds from UI input.
    Supports multiple data sources: CSV, Yahoo, Pandas.
    """
    
    @staticmethod
    def create_csv_data(
        filepath: str,
        datetime_format: str = '%Y-%m-%d',
        open_col: int = 0,
        high_col: int = 1,
        low_col: int = 2,
        close_col: int = 3,
        volume_col: int = 4,
        fromdate: Optional[datetime] = None,
        todate: Optional[datetime] = None
    ) -> bt.feeds.GenericCSVData:
        """
        Create data feed from CSV file.
        
        Args:
            filepath: Path to CSV file
            datetime_format: Date format string
            open_col/high_col/low_col/close_col/volume_col: Column indices
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
        datetime_col: str = 'date',
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
