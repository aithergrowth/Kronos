"""Candle (OHLCV) containers.

``CandleSeries`` is a thin, validated wrapper around a pandas DataFrame with the
columns ``timestamp, open, high, low, close, volume``.  ``timestamp`` is the
candle **open** time, timezone-naive UTC, strictly increasing.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import pandas as pd
from pandas.api.types import is_numeric_dtype

from .timeframe import Timeframe

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

_TIME_ALIASES = ["timestamp", "timestamps", "time", "datetime", "date", "<date>", "gmt time", "local time"]
_PRICE_ALIASES = {
    "open": ["open", "<open>", "o"],
    "high": ["high", "<high>", "h"],
    "low": ["low", "<low>", "l"],
    "close": ["close", "<close>", "c", "adj close"],
    "volume": ["volume", "<vol>", "<tickvol>", "vol", "tick volume", "tickvol", "v"],
}


@dataclass(frozen=True)
class Candle:
    index: int
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def is_bullish(self) -> bool:
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        return self.close < self.open

    @property
    def body_high(self) -> float:
        return max(self.open, self.close)

    @property
    def body_low(self) -> float:
        return min(self.open, self.close)

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)


class CandleSeries:
    """Validated OHLCV series for one symbol and one timeframe."""

    def __init__(self, df: pd.DataFrame, timeframe: Timeframe, symbol: Optional[str] = None, validate: bool = True):
        self.timeframe = Timeframe.parse(timeframe)
        self.symbol = symbol
        frame = df.copy()
        if validate:
            frame = _normalise_frame(frame)
        self.df = frame
        # numpy views for fast rule evaluation
        self.open = frame["open"].to_numpy(dtype=float)
        self.high = frame["high"].to_numpy(dtype=float)
        self.low = frame["low"].to_numpy(dtype=float)
        self.close = frame["close"].to_numpy(dtype=float)
        self.volume = frame["volume"].to_numpy(dtype=float)
        self.timestamps = frame["timestamp"]

    # ------------------------------------------------------------ constructors
    @classmethod
    def from_records(
        cls,
        ohlc: Sequence[Sequence[float]],
        timeframe: Timeframe,
        start: "str | pd.Timestamp" = "2024-01-01",
        symbol: Optional[str] = None,
        timestamps: Optional[Iterable] = None,
    ) -> "CandleSeries":
        """Build a series from ``(open, high, low, close[, volume])`` rows.

        Timestamps are generated at the timeframe spacing from ``start`` unless
        given explicitly.  Handy for tests and for hand-drawn scenarios.
        """
        timeframe = Timeframe.parse(timeframe)
        rows = [list(r) for r in ohlc]
        for r in rows:
            if len(r) == 4:
                r.append(0.0)
        if timestamps is None:
            step = timeframe.delta()
            ts = [pd.Timestamp(start)]
            for _ in range(len(rows) - 1):
                ts.append(ts[-1] + step)
        else:
            ts = [pd.Timestamp(t) for t in timestamps]
        frame = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
        frame.insert(0, "timestamp", ts)
        return cls(frame, timeframe, symbol)

    @classmethod
    def from_csv(cls, path: "str | Path", timeframe: Timeframe, symbol: Optional[str] = None, tz: Optional[str] = None) -> "CandleSeries":
        """Load a CSV exported from MetaTrader, TradingView, Dukascopy or Kronos.

        Column names are matched case-insensitively.  MetaTrader exports with
        separate ``<DATE>``/``<TIME>`` columns are merged.  Numeric ``time``
        columns are treated as unix seconds (or milliseconds when large).
        """
        raw = pd.read_csv(path, sep=None, engine="python", encoding="utf-8-sig")
        frame = _coerce_columns(raw)
        if tz is not None:
            ts = pd.to_datetime(frame["timestamp"])
            if ts.dt.tz is None:
                ts = ts.dt.tz_localize(tz)
            frame["timestamp"] = ts.dt.tz_convert("UTC").dt.tz_localize(None)
        return cls(frame, timeframe, symbol or _symbol_from_path(path))

    # ------------------------------------------------------------ container API
    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, i: int) -> Candle:
        if i < 0:
            i += len(self)
        return Candle(
            index=i,
            timestamp=self.timestamps.iloc[i],
            open=float(self.open[i]),
            high=float(self.high[i]),
            low=float(self.low[i]),
            close=float(self.close[i]),
            volume=float(self.volume[i]),
        )

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    @property
    def last(self) -> Candle:
        return self[len(self) - 1]

    @property
    def last_timestamp(self) -> pd.Timestamp:
        return self.timestamps.iloc[-1]

    @property
    def last_close_time(self) -> pd.Timestamp:
        return self.timeframe.close_time(self.last_timestamp)

    def tail(self, n: int) -> "CandleSeries":
        if n >= len(self):
            return self
        return CandleSeries(self.df.iloc[-n:].reset_index(drop=True), self.timeframe, self.symbol, validate=False)

    def head(self, n: int) -> "CandleSeries":
        return CandleSeries(self.df.iloc[:n].reset_index(drop=True), self.timeframe, self.symbol, validate=False)

    def until(self, ts: pd.Timestamp) -> "CandleSeries":
        """Candles whose *open* time is <= ``ts``."""
        ts = pd.Timestamp(ts)
        mask = self.timestamps <= ts
        return CandleSeries(self.df.loc[mask].reset_index(drop=True), self.timeframe, self.symbol, validate=False)

    def closed_as_of(self, ts: pd.Timestamp) -> "CandleSeries":
        """Only candles that are fully closed at ``ts`` (no look-ahead into a forming candle)."""
        ts = pd.Timestamp(ts)
        if len(self) == 0:
            return self
        # Compare forward close times, as MultiTimeframeData.as_of does.
        # Calendar-month subtraction is not the inverse of addition at month
        # ends (Jan 31 + one month can close on Feb 28).
        close_times = self.timestamps + self.timeframe.delta()
        n = int(close_times.searchsorted(ts, side="right"))
        if n >= len(self):
            return self
        return CandleSeries(self.df.iloc[:n].reset_index(drop=True), self.timeframe, self.symbol, validate=False)

    def index_at_or_after(self, ts: pd.Timestamp) -> int:
        """Index of the first candle opening at or after ``ts`` (``len`` if none)."""
        return int(self.timestamps.searchsorted(pd.Timestamp(ts), side="left"))

    def to_kronos_inputs(self) -> Tuple[pd.DataFrame, pd.Series]:
        """``(x_df, x_timestamp)`` in the layout ``KronosPredictor.predict`` expects."""
        x = self.df[["open", "high", "low", "close", "volume"]].reset_index(drop=True).copy()
        x["amount"] = x["volume"] * x[["open", "high", "low", "close"]].mean(axis=1)
        return x, self.df["timestamp"].reset_index(drop=True)

    def __repr__(self) -> str:
        if len(self) == 0:
            return f"CandleSeries({self.symbol} {self.timeframe.label}, empty)"
        return (
            f"CandleSeries({self.symbol} {self.timeframe.label}, n={len(self)}, "
            f"{self.timestamps.iloc[0]} -> {self.timestamps.iloc[-1]})"
        )


# ---------------------------------------------------------------------- helpers

def _symbol_from_path(path) -> Optional[str]:
    stem = Path(path).stem
    return stem.split("_")[0].split("-")[0].upper() if stem else None


def _coerce_columns(raw: pd.DataFrame) -> pd.DataFrame:
    cols = {c: str(c).strip().lstrip("﻿").lower() for c in raw.columns}
    lower = {v: k for k, v in cols.items()}

    frame = pd.DataFrame()
    # timestamp ---------------------------------------------------------
    if "<date>" in lower and "<time>" in lower:
        frame["timestamp"] = pd.to_datetime(raw[lower["<date>"]].astype(str) + " " + raw[lower["<time>"]].astype(str))
    elif "date" in lower and "time" in lower and not is_numeric_dtype(raw[lower["time"]]):
        frame["timestamp"] = pd.to_datetime(raw[lower["date"]].astype(str) + " " + raw[lower["time"]].astype(str))
    else:
        tcol = next((lower[a] for a in _TIME_ALIASES if a in lower), None)
        if tcol is None:
            raise ValueError(f"No timestamp column found in {list(raw.columns)}")
        col = raw[tcol]
        if is_numeric_dtype(col):
            unit = "ms" if col.max() > 1e12 else "s"
            frame["timestamp"] = pd.to_datetime(col, unit=unit)
        else:
            frame["timestamp"] = pd.to_datetime(col)
    # prices ------------------------------------------------------------
    for target, aliases in _PRICE_ALIASES.items():
        src = next((lower[a] for a in aliases if a in lower), None)
        if src is None:
            if target == "volume":
                frame["volume"] = 0.0
                continue
            raise ValueError(f"Missing column for {target!r} in {list(raw.columns)}")
        frame[target] = pd.to_numeric(raw[src], errors="coerce")
    return frame


def _normalise_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in COLUMNS if c not in frame.columns and c != "volume"]
    if missing:
        raise ValueError(f"CandleSeries is missing columns {missing}")
    if "volume" not in frame.columns:
        frame["volume"] = 0.0
    frame = frame[COLUMNS].copy()
    ts = pd.to_datetime(frame["timestamp"])
    if getattr(ts.dt, "tz", None) is not None:
        ts = ts.dt.tz_convert("UTC").dt.tz_localize(None)
    frame["timestamp"] = ts
    for c in ["open", "high", "low", "close", "volume"]:
        frame[c] = pd.to_numeric(frame[c], errors="coerce").astype(float)
    frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"])
    frame["volume"] = frame["volume"].fillna(0.0)
    frame = frame.sort_values("timestamp").drop_duplicates("timestamp", keep="last").reset_index(drop=True)
    bad = (frame["high"] < frame[["open", "close"]].max(axis=1)) | (frame["low"] > frame[["open", "close"]].min(axis=1))
    if bad.any():
        # repair rather than fail: exported data occasionally has a high below the close
        frame.loc[bad, "high"] = frame.loc[bad, ["high", "open", "close"]].max(axis=1)
        frame.loc[bad, "low"] = frame.loc[bad, ["low", "open", "close"]].min(axis=1)
    return frame
