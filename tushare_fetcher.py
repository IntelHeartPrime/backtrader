#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Tushare Data Fetcher for Backtrader
#
# Fetches stock data from Tushare API and formats it for backtrader usage
#
###############################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import pandas as pd

from utils.logger import get_logger

log = get_logger()


def _get_tushare_token(token=None):
    """
    Get Tushare API token from multiple sources

    Priority:
        1. Explicit token parameter
        2. Environment variable TUSHARE_TOKEN
        3. .env file (if python-dotenv is installed)

    Returns:
        str: API token

    Raises:
        ValueError: If no token is found
    """
    if token is not None:
        return token

    env_token = os.getenv('TUSHARE_TOKEN')
    if env_token:
        return env_token

    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
            env_token = os.getenv('TUSHARE_TOKEN')
            if env_token:
                return env_token
    except ImportError:
        pass

    raise ValueError(
        "Tushare API token not found. "
        "Please provide it via: "
        "1. token parameter, "
        "2. TUSHARE_TOKEN environment variable, or "
        "3. .env file (copy .env.example to .env and fill in your token)"
    )


def get_tushare_data(ts_code, start_date, end_date, token=None, adj=None):
    """
    Fetch historical daily stock data from Tushare API

    Parameters:
    -----------
    ts_code : str
        Stock code in Tushare format (e.g., '000001.SZ' for Shenzhen,
        '600000.SH' for Shanghai)

    start_date : str
        Start date in 'YYYYMMDD' format (e.g., '20240101')

    end_date : str
        End date in 'YYYYMMDD' format (e.g., '20241231')

    token : str, optional
        Your Tushare API token. If not provided, will be read from:
        - TUSHARE_TOKEN environment variable
        - .env file (if python-dotenv is installed)

    adj : str, optional
        Price adjustment type: None (unadjusted), 'qfq' (forward adjusted),
        'hfq' (backward adjusted). Default: None

    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns: datetime (index), open, high, low, close, volume

    Raises:
    -------
    ImportError
        If tushare package is not installed

    ValueError
        If no data is returned or invalid parameters
    """
    try:
        import tushare as ts
        log.debug(f'Imported tushare OK')
    except ImportError:
        log.error('tushare package not installed')
        raise ImportError(
            "tushare package is required. Install it with: pip install tushare"
        )

    # Get token from parameter, env var, or .env file
    token = _get_tushare_token(token)
    log.info(f'Tushare token loaded (len={len(token)})')

    # Initialize Tushare API
    pro = ts.pro_api(token)
    log.info(f'Tushare API initialized')

    # Fetch daily data
    log.info(f'Fetching Tushare daily: ts_code={ts_code}, start={start_date}, end={end_date}')
    df = pro.daily(
        ts_code=ts_code,
        start_date=start_date,
        end_date=end_date
    )
    log.info(f'Tushare API returned {len(df)} rows, columns={list(df.columns)}')

    # Check if data is empty
    if df.empty:
        raise ValueError(
            f"No data returned for ts_code={ts_code}, "
            f"start_date={start_date}, end_date={end_date}"
        )

    # Apply price adjustment if requested
    if adj is not None:
        if adj == 'qfq':
            df_adj = pro.adj_factor(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if not df_adj.empty:
                df = df.merge(df_adj[['trade_date', 'adj_factor']],
                            on='trade_date', how='left')
                df['open'] = df['open'] * df['adj_factor']
                df['high'] = df['high'] * df['adj_factor']
                df['low'] = df['low'] * df['adj_factor']
                df['close'] = df['close'] * df['adj_factor']
        elif adj == 'hfq':
            # Backward adjustment not fully supported
            raise ValueError("Backward adjustment (hfq) is not yet implemented")

    # Convert trade_date to datetime and set as index
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df.set_index('trade_date', inplace=True)
    log.debug(f'Date range: {df.index.min()} ~ {df.index.max()}')

    # Sort by date (ascending)
    df.sort_index(inplace=True)

    # Rename 'vol' to 'volume' for consistency
    # Note: tushare returns volume in 'lots' (手), convert to shares
    if 'vol' in df.columns:
        df.rename(columns={'vol': 'volume'}, inplace=True)
        df['volume'] = df['volume'] * 100  # 1 lot = 100 shares
        log.debug(f'Volume converted: lots -> shares (x100)')

    # Select and order columns for backtrader
    columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
    df = df[columns_to_keep]

    # Drop rows with missing values
    before = len(df)
    df.dropna(inplace=True)
    if len(df) < before:
        log.warning(f'Dropped {before - len(df)} rows with NaN values')

    log.info(f'Tushare data ready: {len(df)} rows, '
             f'open range [{df["open"].min():.2f}~{df["open"].max():.2f}], '
             f'close range [{df["close"].min():.2f}~{df["close"].max():.2f}]')

    return df


def get_tushare_multiple_stocks(ts_codes, start_date, end_date, token=None, adj=None):
    """
    Fetch data for multiple stocks from Tushare API.

    Queries stocks in batches to avoid hitting Tushare's per-request row limit
    (~6000 rows). Each batch of 3 stocks × ~1450 trading days ≈ 4350 rows fits
    safely within the limit.

    Parameters:
    -----------
    ts_codes : list of str
        List of stock codes (e.g., ['000001.SZ', '600000.SH'])

    start_date : str
        Start date in 'YYYYMMDD' format

    end_date : str
        End date in 'YYYYMMDD' format

    token : str, optional
        Your Tushare API token.

    adj : str, optional
        Price adjustment type

    Returns: dict of pandas.DataFrame
        Dictionary mapping ts_code to DataFrame
    """
    try:
        import tushare as ts
    except ImportError:
        raise ImportError(
            "tushare package is required. Install it with: pip install tushare"
        )

    token = _get_tushare_token(token)
    pro = ts.pro_api(token)

    result = {}
    BATCH_SIZE = 3

    for i in range(0, len(ts_codes), BATCH_SIZE):
        batch = ts_codes[i:i + BATCH_SIZE]
        code_str = ','.join(batch)
        log.info(f'Fetching batch {i//BATCH_SIZE + 1}: {len(batch)} stocks '
                 f'({batch[0]}...{batch[-1]})')

        try:
            df = pro.daily(
                ts_code=code_str,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            log.warning(f'Batch query failed: {e}, falling back to single-stock')
            # Fall back to single-stock queries for this batch
            for code in batch:
                try:
                    df_single = pro.daily(
                        ts_code=code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    _process_stock_df(code, df_single, result)
                except Exception:
                    continue
            continue

        if df.empty:
            log.warning(f'Batch returned empty, falling back to single-stock')
            for code in batch:
                try:
                    df_single = pro.daily(
                        ts_code=code,
                        start_date=start_date,
                        end_date=end_date
                    )
                    _process_stock_df(code, df_single, result)
                except Exception:
                    continue
            continue

        for code in batch:
            _process_stock_df(code, df, result)

    return result


def _process_stock_df(code, df, result):
    """Process a Tushare daily DataFrame for a single stock into result dict."""
    if df is None or df.empty:
        return
    df_code = df[df['ts_code'] == code].copy()
    if df_code.empty:
        return

    df_code['trade_date'] = pd.to_datetime(df_code['trade_date'])
    df_code.set_index('trade_date', inplace=True)
    df_code.sort_index(inplace=True)

    if 'vol' in df_code.columns:
        df_code.rename(columns={'vol': 'volume'}, inplace=True)
        df_code['volume'] = df_code['volume'] * 100

    columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
    df_code = df_code[columns_to_keep]
    df_code.dropna(inplace=True)

    if not df_code.empty:
        result[code] = df_code
