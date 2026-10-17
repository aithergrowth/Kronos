"""Bitstamp public candles as a live feed for crypto (no account, no key).

On Monday 5 October 2026 the MetaQuotes demo server's BTCUSD still stood at Friday's close (84,316 at 06:58 UTC
against 86,229 on the spot market), so a crypto profile on that demo had no live price at all.  Bitstamp's public
OHLC endpoint serves BTC/USD and ETH/USD around the clock, and the BTC profile's backtests ran on candles from the
same endpoint.  Weekly and monthly candles are built from the daily ones the way that backtest cache was: weeks
from Monday 00:00 UTC, months from the 1st.

Pair the feed with ``--broker paper`` (simulated fills on these candles).  Orders to a broker whose own price
differs from Bitstamp's would put the stop and the target on the wrong levels.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe

API = "https://www.bitstamp.net/api/v2"
STEPS: Dict[Timeframe, int] = {
    Timeframe.MIN_1: 60, Timeframe.MIN_5: 300, Timeframe.MIN_15: 900, Timeframe.MIN_30: 1800,
    Timeframe.H_1: 3600, Timeframe.H_4: 14400, Timeframe.D_1: 86400,
}
MAX_LIMIT = 1000                         # Bitstamp returns at most 1,000 candles per request
PAIRS = {"BTCUSD": "btcusd", "ETHUSD": "ethusd"}
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def pair_for(symbol: str) -> str:
    """Bitstamp's pair name: ``btcusd`` for BTCUSD, and the lower-cased symbol otherwise."""
    return PAIRS.get(symbol.upper(), symbol.lower())


def to_frame(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """Bitstamp OHLC rows -> timestamp (naive UTC bar open), open, high, low, close, volume; sorted, unique."""
    if not rows:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = df[col].astype(float)
    return (df[["timestamp", "open", "high", "low", "close", "volume"]]
            .drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True))


def from_daily(daily: pd.DataFrame, timeframe: Timeframe) -> pd.DataFrame:
    """Weekly (from Monday 00:00 UTC) or monthly (from the 1st) candles out of daily ones."""
    rule = "W-MON" if timeframe is Timeframe.W_1 else "MS"
    kwargs = {"label": "left", "closed": "left"} if timeframe is Timeframe.W_1 else {}
    out = daily.set_index("timestamp").resample(rule, **kwargs).agg(AGG).dropna()
    return out.reset_index()


class BitstampFeed:
    """Candle feed over Bitstamp's public REST API (``get_candles`` like a broker, plus ``current_price``)."""

    def __init__(self, session=None, timeout: float = 15.0, daily_ttl_seconds: float = 600.0,
                 min_daily_days: int = 2300, clock: Callable[[], float] = time.monotonic):
        self.session = session          # anything with .get(url, params=, timeout=) -> .status_code / .json() / .text
        self.timeout = timeout
        self.daily_ttl_seconds = daily_ttl_seconds
        self.min_daily_days = min_daily_days    # one daily fetch covers the 1D, 1W (120) and 1M (72) views of a scan
        self.clock = clock
        self._daily: Dict[str, Tuple[float, int, pd.DataFrame]] = {}   # pair -> (fetched at, days, candles)

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.session is None:
            import requests
            self.session = requests.Session()
        r = self.session.get(API + path, params=params, timeout=self.timeout)
        if r.status_code != 200:
            raise RuntimeError(f"Bitstamp {r.status_code} for {path}: {str(r.text)[:200]}")
        return r.json()

    def _ohlc(self, pair: str, step: int, count: int) -> pd.DataFrame:
        """The latest ``count`` candles of ``step`` seconds (the forming one included), paging back 1,000 at a time."""
        frames: List[pd.DataFrame] = []
        end: Optional[int] = None
        remaining = max(int(count), 1)
        while remaining > 0:
            params: Dict[str, Any] = {"step": step, "limit": min(remaining, MAX_LIMIT)}
            if end is not None:
                params["end"] = end
            rows = self._get(f"/ohlc/{pair}/", params).get("data", {}).get("ohlc", [])
            df = to_frame(rows)
            if df.empty:
                break
            frames.append(df)
            remaining -= len(df)
            first = int(df["timestamp"].iloc[0].timestamp())
            if end is not None and first >= end:
                break
            end = first - step
        if not frames:
            raise RuntimeError(f"Bitstamp returned no candles for {pair} at {step} s")
        out = pd.concat(frames).drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
        return out.tail(int(count)).reset_index(drop=True)

    def _daily_candles(self, pair: str, days: int) -> pd.DataFrame:
        """Daily candles, fetched once per ``daily_ttl_seconds`` for the daily, weekly and monthly views together."""
        cached = self._daily.get(pair)
        now = self.clock()
        if cached is not None and cached[1] >= days and now - cached[0] < self.daily_ttl_seconds:
            return cached[2].tail(days).reset_index(drop=True)
        fetch_days = max(int(days), int(self.min_daily_days))
        df = self._ohlc(pair, STEPS[Timeframe.D_1], fetch_days)
        self._daily[pair] = (now, fetch_days, df)
        return df.tail(days).reset_index(drop=True)

    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        timeframe = Timeframe.parse(timeframe)
        pair = pair_for(symbol)
        if timeframe in (Timeframe.W_1, Timeframe.MN_1):
            per = 7 if timeframe is Timeframe.W_1 else 31
            df = from_daily(self._daily_candles(pair, (int(count) + 1) * per), timeframe).tail(int(count))
        elif timeframe is Timeframe.D_1:
            df = self._daily_candles(pair, int(count))
        elif timeframe in STEPS:
            df = self._ohlc(pair, STEPS[timeframe], int(count))
        else:
            raise ValueError(f"Bitstamp has no {timeframe.label} candles")
        if df.empty:
            raise RuntimeError(f"Bitstamp returned no {timeframe.label} candles for {symbol}")
        return CandleSeries(df.reset_index(drop=True), timeframe, symbol.upper())

    def current_price(self, symbol: str) -> float:
        """The last traded price from the ticker."""
        return float(self._get(f"/ticker/{pair_for(symbol)}/", {})["last"])
