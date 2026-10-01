"""Timeframe definitions shared by the whole trading system.

Naming note: the strategy text uses ``1M`` for *monthly* and ``1m`` for *one
minute*.  The enum uses unambiguous names (``MN_1`` vs ``MIN_1``) and
``Timeframe.parse`` accepts the trader's shorthand case-sensitively.
"""
from __future__ import annotations

from enum import Enum
from functools import total_ordering
from typing import List, Optional

import pandas as pd

SESSION_CLOSE_HOUR = 17   # the forex trading day ends at 17:00 New York; sessions, 4H, daily, weekly and monthly candles start there


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
        return pd.Timedelta(self.minutes, unit="min")

    def floor(self, ts: pd.Timestamp) -> pd.Timestamp:
        """Open time of the candle that contains ``ts``."""
        ts = pd.Timestamp(ts)
        if self is Timeframe.MN_1:
            return ts.normalize().replace(day=1)
        if self is Timeframe.W_1:
            return ts.normalize() - pd.Timedelta(ts.weekday(), unit="D")
        if self is Timeframe.D_1:
            return ts.normalize()
        return ts.floor(f"{self.minutes}min")

    def close_time(self, open_time: pd.Timestamp, session_tz: Optional[str] = "America/New_York") -> pd.Timestamp:
        """Timestamp at which the candle opened at ``open_time`` is fully closed.

        Monthly candles may be stamped on the previous evening (a New York close
        feed stamps March as 28 February 21:00); the close is then the next
        month's boundary with the same offset (31 March 21:00), never
        ``open + 1 month`` (28 March 21:00), which would show three days of the
        month before they happened.
        """
        open_time = pd.Timestamp(open_time)
        if self is Timeframe.MN_1:
            logical = (open_time + pd.Timedelta(hours=12)).normalize().replace(day=1)
            nxt = logical + pd.DateOffset(months=1)
            offset = logical - open_time
            if offset == pd.Timedelta(0) or not session_tz:
                return nxt - offset
            # an evening stamp is a session-close feed: the month ends at the session close (17:00 New York)
            # on its last day, which follows that zone's daylight saving, not the stamp's own offset
            close_local = nxt - pd.Timedelta(hours=24 - SESSION_CLOSE_HOUR)
            return close_local.tz_localize(session_tz).tz_convert("UTC").tz_localize(None)
        return open_time + self.delta()

    def close_times(self, open_times, session_tz: Optional[str] = "America/New_York") -> pd.Series:
        """Vectorised :meth:`close_time` for a series of candle open times."""
        opens = pd.Series(pd.to_datetime(open_times)).reset_index(drop=True)
        if self is Timeframe.MN_1:
            return pd.Series([self.close_time(t, session_tz) for t in opens], dtype="datetime64[ns]")
        return opens + self.delta()

    def future_timestamps(self, last_open: pd.Timestamp, n: int, skip_weekends: bool = True) -> pd.Series:
        """``n`` candle open times following ``last_open`` (used for Kronos ``y_timestamp``)."""
        last_open = pd.Timestamp(last_open)
        if self is Timeframe.MN_1:
            idx = pd.date_range(last_open + pd.DateOffset(months=1), periods=n, freq="MS")
            return pd.Series(idx)
        if self is Timeframe.W_1:
            week = pd.Timedelta(7, unit="D")
            idx = pd.date_range(last_open + week, periods=n, freq=week)
            return pd.Series(idx)
        step = pd.Timedelta(self.minutes, unit="min")
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
