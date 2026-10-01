"""Resampling and multi-timeframe views without look-ahead."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import BIAS_TIMEFRAMES, Timeframe

AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}


def resample(series: CandleSeries, target: Timeframe, session_offset_hours: float = 0.0) -> CandleSeries:
    """Aggregate ``series`` into ``target`` candles.

    Intraday bins are anchored at midnight UTC.  ``session_offset_hours`` shifts
    the daily/weekly/monthly boundary (e.g. ``2`` when the broker's day starts
    at 22:00 UTC) so resampled higher-timeframe candles match the platform.
    """
    target = Timeframe.parse(target)
    if target is series.timeframe:
        return series
    if target < series.timeframe:
        raise ValueError(f"cannot resample {series.timeframe.label} into the smaller {target.label}")
    df = series.df.set_index("timestamp")
    if target.is_intraday:
        out = df.resample(target.pandas_rule, closed="left", label="left", origin="start_day").agg(AGG)
    else:
        shift = pd.Timedelta(float(session_offset_hours), unit="h")
        shifted = df.copy()
        shifted.index = shifted.index + shift
        out = shifted.resample(target.pandas_rule, closed="left", label="left").agg(AGG)
        out.index = out.index - shift
    out = out.dropna(subset=["open"]).reset_index()
    return CandleSeries(out, target, series.symbol, validate=False)


class MultiTimeframeData:
    """A bundle of candle series for one symbol, queryable as of any moment."""

    def __init__(self, series: Dict[Timeframe, CandleSeries]):
        if not series:
            raise ValueError("no series given")
        self.series: Dict[Timeframe, CandleSeries] = {Timeframe.parse(tf): s for tf, s in series.items()}
        self._close_times: Dict[Timeframe, np.ndarray] = {}
        for tf, s in self.series.items():
            self._close_times[tf] = pd.DatetimeIndex(tf.close_times(s.timestamps)).to_numpy()

    # ------------------------------------------------------------ constructors
    @classmethod
    def from_base(
        cls,
        base: CandleSeries,
        timeframes: Optional[Iterable[Timeframe]] = None,
        extra: Optional[Dict[Timeframe, CandleSeries]] = None,
        session_offset_hours: float = 0.0,
    ) -> "MultiTimeframeData":
        """Build every requested timeframe from ``base`` by resampling; ``extra`` series win."""
        wanted = [Timeframe.parse(tf) for tf in (timeframes or BIAS_TIMEFRAMES)]
        out: Dict[Timeframe, CandleSeries] = {base.timeframe: base}
        for tf in wanted:
            if tf < base.timeframe:
                continue
            if tf not in out:
                out[tf] = resample(base, tf, session_offset_hours)
        for tf, s in (extra or {}).items():
            out[Timeframe.parse(tf)] = s
        return cls(out)

    @classmethod
    def from_directory(cls, directory: "str | Path", symbol: str) -> "MultiTimeframeData":
        from .tv_cache import load_all  # local import to avoid a cycle
        found = load_all(directory, symbol)
        if not found:
            raise FileNotFoundError(f"no cached candles for {symbol} in {directory}")
        return cls(found)

    # ------------------------------------------------------------ access
    @property
    def symbol(self) -> Optional[str]:
        return next(iter(self.series.values())).symbol

    @property
    def timeframes(self) -> List[Timeframe]:
        return sorted(self.series)

    @property
    def lowest(self) -> CandleSeries:
        return self.series[min(self.series)]

    def __getitem__(self, tf: Timeframe) -> CandleSeries:
        return self.series[Timeframe.parse(tf)]

    def as_of(self, ts: pd.Timestamp, lookback: Optional[int] = None) -> Dict[Timeframe, CandleSeries]:
        """Closed candles of every timeframe at ``ts`` (optionally only the last ``lookback``)."""
        stamp = np.datetime64(pd.Timestamp(ts))
        views: Dict[Timeframe, CandleSeries] = {}
        for tf, s in self.series.items():
            n_closed = int(np.searchsorted(self._close_times[tf], stamp, side="right"))
            if n_closed == 0:
                continue
            start = 0 if lookback is None else max(0, n_closed - lookback)
            frame = s.df.iloc[start:n_closed]
            if start:
                frame = frame.reset_index(drop=True)
            views[tf] = CandleSeries(frame, tf, s.symbol, validate=False)
        return views

    def describe(self) -> str:
        return "\n".join(f"  {tf.label:>3}: {s}" for tf, s in sorted(self.series.items()))
