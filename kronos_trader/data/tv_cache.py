"""CSV cache of candles, one file per symbol and timeframe.

Layout: ``<dir>/<SYMBOL>_<TF>.csv`` with columns
``timestamp,open,high,low,close,volume`` (timestamp = candle open, UTC).
Exchange prefixes are kept but the colon becomes an underscore
(``OANDA_EURUSD_4H.csv``).  Saving merges with what is already cached, so
repeated pulls from TradingView extend the history instead of replacing it.

File names use case-safe timeframe labels (``1min`` … ``1MO``) because Windows
and macOS file systems ignore letter case: ``1m`` (minute) and ``1M`` (month)
would be the same file there.  Loading also checks that the candle spacing
matches the timeframe, so a mislabelled file is rejected instead of silently
feeding the engine the wrong candles.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..core.candles import COLUMNS, CandleSeries
from ..core.timeframe import Timeframe

#: timeframe label used in file names (unambiguous on case-insensitive file systems)
FILE_LABELS: Dict[Timeframe, str] = {
    Timeframe.MIN_1: "1min", Timeframe.MIN_5: "5min", Timeframe.MIN_15: "15min", Timeframe.MIN_30: "30min",
    Timeframe.H_1: "1H", Timeframe.H_4: "4H", Timeframe.D_1: "1D", Timeframe.W_1: "1W", Timeframe.MN_1: "1MO",
}
#: older file names that are still safe to read (the 1m / 1M pair is deliberately excluded)
_LEGACY_LABELS: Dict[Timeframe, str] = {Timeframe.MIN_5: "5m", Timeframe.MIN_15: "15m", Timeframe.MIN_30: "30m"}


def _slug(symbol: str) -> str:
    return symbol.replace(":", "_").replace("/", "_").upper()


def cache_path(directory: "str | Path", symbol: str, timeframe: Timeframe) -> Path:
    return Path(directory) / f"{_slug(symbol)}_{FILE_LABELS[Timeframe.parse(timeframe)]}.csv"


def spacing_matches(series: CandleSeries, low: float = 0.9, high: float = 3.0) -> bool:
    """Check median cadence without requiring a continuous market session.

    The lower tolerance admits short calendar months and DST shifts, but not
    half-timeframe data. With only one interval, reject excessive density but
    do not mistake a weekend/session gap for an incorrect timeframe.
    """
    if len(series) < 2:
        return True
    median_minutes = float(series.timestamps.diff().median().total_seconds()) / 60.0
    ratio = median_minutes / series.timeframe.minutes
    return ratio >= low and (len(series) < 3 or ratio <= high)


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
    """Load one cached series; raises ``ValueError`` when the file's candle spacing does not fit ``timeframe``."""
    timeframe = Timeframe.parse(timeframe)
    path = cache_path(directory, symbol, timeframe)
    if not path.exists():
        legacy = _LEGACY_LABELS.get(timeframe)
        if legacy is None:
            return None
        path = Path(directory) / f"{_slug(symbol)}_{legacy}.csv"
        if not path.exists():
            return None
    frame = pd.read_csv(path, parse_dates=["timestamp"])
    series = CandleSeries(frame, timeframe, symbol)
    if not spacing_matches(series):
        median = series.timestamps.diff().median()
        raise ValueError(f"{path} does not contain {timeframe.label} candles (median spacing {median}); check the file name")
    return series


def load_all(directory: "str | Path", symbol: str) -> Dict[Timeframe, CandleSeries]:
    out: Dict[Timeframe, CandleSeries] = {}
    for tf in Timeframe:
        try:
            series = load_series(directory, symbol, tf)
        except ValueError as exc:
            print(f"[warn] {exc}")
            continue
        if series is not None and len(series):
            out[tf] = series
    return out
