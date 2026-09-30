"""CSV cache of candles, one file per symbol and timeframe.

Layout: ``<dir>/<SYMBOL>_<TF>.csv`` with columns
``timestamp,open,high,low,close,volume`` (timestamp = candle open, UTC).
Exchange prefixes are kept but the colon becomes an underscore
(``OANDA_EURUSD_4H.csv``).  Saving merges with what is already cached, so
repeated pulls from TradingView extend the history instead of replacing it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..core.candles import COLUMNS, CandleSeries
from ..core.timeframe import Timeframe


def _slug(symbol: str) -> str:
    return symbol.replace(":", "_").replace("/", "_").upper()


def cache_path(directory: "str | Path", symbol: str, timeframe: Timeframe) -> Path:
    return Path(directory) / f"{_slug(symbol)}_{Timeframe.parse(timeframe).label}.csv"


def save_series(series: CandleSeries, directory: "str | Path", symbol: Optional[str] = None, merge: bool = True) -> Path:
    symbol = symbol or series.symbol
    if not symbol:
        raise ValueError("a symbol is required to cache a series")
    path = cache_path(directory, symbol, series.timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = series.df[COLUMNS]
    if merge and path.exists():
        old = pd.read_csv(path, parse_dates=["timestamp"])
        frame = pd.concat([old, frame]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    frame.to_csv(path, index=False)
    return path


def save_payload(payload: Any, timeframe: Timeframe, directory: "str | Path", symbol: Optional[str] = None) -> Path:
    """Persist the raw ``mcp-tv-get-ohlcv`` payload (dict / list / JSON text)."""
    from .tradingview_mcp import parse_ohlcv_payload
    series = parse_ohlcv_payload(payload, timeframe, symbol)
    return save_series(series, directory, symbol or series.symbol)


def load_series(directory: "str | Path", symbol: str, timeframe: Timeframe) -> Optional[CandleSeries]:
    path = cache_path(directory, symbol, timeframe)
    if not path.exists():
        return None
    frame = pd.read_csv(path, parse_dates=["timestamp"])
    return CandleSeries(frame, timeframe, symbol)


def load_all(directory: "str | Path", symbol: str) -> Dict[Timeframe, CandleSeries]:
    out: Dict[Timeframe, CandleSeries] = {}
    for tf in Timeframe:
        series = load_series(directory, symbol, tf)
        if series is not None and len(series):
            out[tf] = series
    return out
