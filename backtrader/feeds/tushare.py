#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# TushareData Feed for Backtrader
#
# Custom data feed that loads Tushare-formatted pandas DataFrames
#
###############################################################################

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from backtrader.feeds import PandasData


class TushareData(PandasData):
    """
    Tushare Data Feed for Backtrader

    Loads stock data from Tushare-formatted pandas DataFrames.

    Expected DataFrame format:
        - Index: datetime (pandas Timestamp)
        - Columns: open, high, low, close, volume

    Usage:
        >>> import backtrader as bt
        >>> from tushare_fetcher import get_tushare_data
        >>>
        >>> df = get_tushare_data('000001.SZ', '20240101', '20241231', token)
        >>> data = TushareData(dataname=df)

    Parameters:
        Inherits all parameters from PandasData, including:
        - nocase (default True): case insensitive column matching
        - datetime, open, high, low, close, volume, openinterest: column mappings

    Note:
        - Volume should be in shares (not lots)
        - Date index should be a pandas datetime index
        - DataFrame should be sorted by date (ascending)
    """

    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
    )

    datafields = [
        'datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest'
    ]
