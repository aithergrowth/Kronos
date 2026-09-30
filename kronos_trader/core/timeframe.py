"""Timeframe definitions shared by the whole trading system.

Naming note: the strategy text uses ``1M`` for *monthly* and ``1m`` for *one
minute*.  The enum uses unambiguous names (``MN_1`` vs ``MIN_1``) and
``Timeframe.parse`` accepts the trader's shorthand case-sensitively.
"""
from __future__ import annotations

from enum import Enum
from functools import total_ordering
from typing import List

import pandas as pd


@total_ordering
class Timeframe(Enum):
    MIN_1 = ("1m", 1, "1min")
    MIN_5 = ("5m", 5, "5min")
    MIN_15 = ("15m", 15, "15min")
    MIN_30 = ("30m", 30, "30min")
    H_1 = ("1H", 60, "1h")
    H_4 = ("4H", 240, "4h")
    D_1 = ("1D", 1440, "1D")
    W_1 = ("1W", 10080, "W-MON")
    MN_1 = ("1M", 43200, "MS")

    def __init__(self, label: str, minutes: int, pandas_rule: str):
        self.label = label
        self.minutes = minutes
        self.pandas_rule = pandas_rule

    # ------------------------------------------------------------------ ordering
    def __lt__(self, other: "Timeframe") -> bool:
        if not isinstance(other, Timeframe):
            return NotImplemented
        return self.minutes < other.minutes

    def __hash__(self) -> int:  # Enum defines __eq__; keep hashability explicit
        return hash(self.name)

    def __str__(self) -> str:
        return self.label

    # ------------------------------------------------------------------ parsing
    @classmethod
    def parse(cls, text: "str | Timeframe") -> "Timeframe":
        if isinstance(text, Timeframe):
            return text
        raw = str(text).strip()
        if raw in _CASE_SENSITIVE_ALIASES:
            return _CASE_SENSITIVE_ALIASES[raw]
        key = raw.lower()
        if key in _ALIASES:
            return _ALIASES[key]
        raise ValueError(f"Unknown timeframe {text!r}. Known: {sorted(_ALIASES)}")

    # ------------------------------------------------------------------ time math
    @property
    def is_intraday(self) -> bool:
        return self.minutes < Timeframe.D_1.minutes

    def delta(self):
        """Length of one candle as a pandas offset (calendar-month aware)."""
        if self is Timeframe.MN_1:
            return pd.DateOffset(months=1)
        return pd.Timedelta(minutes=self.minutes)

    def floor(self, ts: pd.Timestamp) -> pd.Timestamp:
        """Open time of the candle that contains ``ts``."""
        ts = pd.Timestamp(ts)
        if self is Timeframe.MN_1:
            return ts.normalize().replace(day=1)
        if self is Timeframe.W_1:
            return ts.normalize() - pd.Timedelta(days=ts.weekday())
        if self is Timeframe.D_1:
            return ts.normalize()
        return ts.floor(f"{self.minutes}min")

    def close_time(self, open_time: pd.Timestamp) -> pd.Timestamp:
        """Timestamp at which the candle opened at ``open_time`` is fully closed."""
        return pd.Timestamp(open_time) + self.delta()

    def future_timestamps(self, last_open: pd.Timestamp, n: int, skip_weekends: bool = True) -> pd.Series:
        """``n`` candle open times following ``last_open`` (used for Kronos ``y_timestamp``)."""
        last_open = pd.Timestamp(last_open)
        if self is Timeframe.MN_1:
            idx = pd.date_range(last_open + pd.DateOffset(months=1), periods=n, freq="MS")
            return pd.Series(idx)
        if self is Timeframe.W_1:
            idx = pd.date_range(last_open + pd.Timedelta(days=7), periods=n, freq="7D")
            return pd.Series(idx)
        step = pd.Timedelta(minutes=self.minutes)
        out = []
        t = last_open
        while len(out) < n:
            t = t + step
            if skip_weekends and t.weekday() >= 5:   # markets that close at the weekend
                continue
            out.append(t)
        return pd.Series(pd.DatetimeIndex(out))


_ALIASES = {
    "1min": Timeframe.MIN_1, "m1": Timeframe.MIN_1, "min1": Timeframe.MIN_1,
    "5m": Timeframe.MIN_5, "5min": Timeframe.MIN_5, "m5": Timeframe.MIN_5,
    "15m": Timeframe.MIN_15, "15min": Timeframe.MIN_15, "m15": Timeframe.MIN_15,
    "30m": Timeframe.MIN_30, "30min": Timeframe.MIN_30, "m30": Timeframe.MIN_30,
    "1h": Timeframe.H_1, "h1": Timeframe.H_1, "60m": Timeframe.H_1, "60min": Timeframe.H_1, "60": Timeframe.H_1,
    "4h": Timeframe.H_4, "h4": Timeframe.H_4, "240m": Timeframe.H_4, "240": Timeframe.H_4,
    "1d": Timeframe.D_1, "d": Timeframe.D_1, "d1": Timeframe.D_1, "daily": Timeframe.D_1,
    "1w": Timeframe.W_1, "w": Timeframe.W_1, "w1": Timeframe.W_1, "weekly": Timeframe.W_1,
    "1mo": Timeframe.MN_1, "mn": Timeframe.MN_1, "mn1": Timeframe.MN_1, "1mn": Timeframe.MN_1,
    "monthly": Timeframe.MN_1, "month": Timeframe.MN_1, "mo": Timeframe.MN_1,
}
# "1m" (minute) versus "1M" (month) can only be told apart by case.
_CASE_SENSITIVE_ALIASES = {
    "1m": Timeframe.MIN_1, "m": Timeframe.MIN_1,
    "1M": Timeframe.MN_1, "M": Timeframe.MN_1,
}

#: The five timeframes that vote on the bias (rule: minimum 3/5 must match).
BIAS_TIMEFRAMES: List[Timeframe] = [Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1, Timeframe.H_4, Timeframe.H_1]
#: Timeframes on which POIs are mapped (rule: map POIs on 1M, 1W, 1D, 4H, 1H).
POI_TIMEFRAMES: List[Timeframe] = list(BIAS_TIMEFRAMES)
