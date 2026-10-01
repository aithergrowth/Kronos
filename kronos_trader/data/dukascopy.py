"""Dukascopy historical candles: free per-day 1-minute BID files, no account needed.

``https://datafeed.dukascopy.com/datafeed/{INSTRUMENT}/{YYYY}/{MM}/{DD}/BID_candles_min_1.bi5``
with a zero-based month.  Each file is an LZMA stream of 24-byte big-endian
records: seconds since 00:00 UTC, open, close, low, high (integers scaled by
the instrument's decimals) and volume (float32).  The feed rate-limits, so
``fetch_days`` goes one day at a time with a pause and backs off on 429.
Raw files are kept under ``raw/<INSTRUMENT>/<date>.bi5`` so a second run only
fetches what is missing.  ``build_cache`` turns them into the cache layout the
engine reads (``<SYMBOL>_5min.csv`` ... ``<SYMBOL>_1MO.csv``), with 4H, daily,
weekly and monthly candles anchored to the New York close like the TradingView
OANDA bars (``session_offset_hours=3`` means the day starts at 21:00 UTC).
"""
from __future__ import annotations

import datetime as dt
import lzma
import struct
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from .resample import resample
from .tv_cache import save_series

URL = "https://datafeed.dukascopy.com/datafeed/{inst}/{y:04d}/{m0:02d}/{d:02d}/BID_candles_min_1.bi5"
RECORD = struct.Struct(">iiiiif")
SCALE: Dict[str, float] = {"XAUUSD": 1e3, "XAGUSD": 1e3, "USDJPY": 1e3, "EURJPY": 1e3, "GBPJPY": 1e3, "AUDJPY": 1e3,
                           "CHFJPY": 1e3, "CADJPY": 1e3, "NZDJPY": 1e3, "BTCUSD": 1e1, "ETHUSD": 1e1}
CACHE_TIMEFRAMES = (Timeframe.MIN_5, Timeframe.MIN_15, Timeframe.MIN_30, Timeframe.H_1, Timeframe.H_4,
                    Timeframe.D_1, Timeframe.W_1, Timeframe.MN_1)


def scale_for(instrument: str) -> float:
    return SCALE.get(instrument.upper(), 1e5)


def day_url(instrument: str, day: dt.date) -> str:
    return URL.format(inst=instrument.upper(), y=day.year, m0=day.month - 1, d=day.day)


def decode_day(raw: bytes, day: dt.date, scale: float) -> pd.DataFrame:
    """Decode one day file into timestamp/open/high/low/close/volume rows (UTC, naive)."""
    cols = ["timestamp", "open", "high", "low", "close", "volume"]
    if not raw:
        return pd.DataFrame(columns=cols)
    data = lzma.decompress(raw)
    n = len(data) // RECORD.size
    if n == 0:
        return pd.DataFrame(columns=cols)
    arr = np.array([RECORD.unpack_from(data, i * RECORD.size) for i in range(n)], dtype=float)
    base = pd.Timestamp(day)
    df = pd.DataFrame({
        "timestamp": base + pd.to_timedelta(arr[:, 0], unit="s"),
        "open": arr[:, 1] / scale, "high": arr[:, 4] / scale, "low": arr[:, 3] / scale, "close": arr[:, 2] / scale,
        "volume": arr[:, 5],
    })
    df = df[(df["open"] > 0) & (df["high"] >= df["low"])]
    return df[cols].reset_index(drop=True)


def fetch_days(instrument: str, start: dt.date, end: dt.date, raw_dir, pause: float = 0.4, session=None,
               progress: Optional[Callable[[str], None]] = None) -> Dict[str, int]:
    """Fetch the day files from ``start`` to ``end`` into ``raw_dir/<INSTRUMENT>``; skips Saturdays and files present."""
    if session is None:
        import requests
        session = requests.Session()
        session.headers["User-Agent"] = "kronos_trader/0.1"
    out = Path(raw_dir) / instrument.upper()
    out.mkdir(parents=True, exist_ok=True)
    counts = {"fetched": 0, "empty": 0, "skipped": 0, "failed": 0}
    day = start
    while day <= end:
        target = out / f"{day.isoformat()}.bi5"
        if day.weekday() == 5 or target.exists():
            counts["skipped"] += 1
            day += dt.timedelta(days=1)
            continue
        for attempt in range(6):
            try:
                r = session.get(day_url(instrument, day), timeout=40)
            except Exception:
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                target.write_bytes(r.content)
                counts["fetched"] += 1
                break
            if r.status_code == 404:
                target.write_bytes(b"")
                counts["empty"] += 1
                break
            time.sleep(5 * (2 ** attempt))                      # 429 / 5xx: back off
        else:
            counts["failed"] += 1
            if progress:
                progress(f"{instrument} {day}: failed")
        if progress and (counts["fetched"] + counts["empty"]) % 100 == 0:
            progress(f"{instrument} {day}: {counts}")
        time.sleep(pause)
        day += dt.timedelta(days=1)
    return counts


def load_minutes(instrument: str, raw_dir, symbol: Optional[str] = None) -> CandleSeries:
    """All decoded day files of ``instrument`` as one 1-minute series."""
    folder = Path(raw_dir) / instrument.upper()
    scale = scale_for(instrument)
    frames = []
    for f in sorted(folder.glob("*.bi5")):
        try:
            day = dt.date.fromisoformat(f.stem)
        except ValueError:
            continue
        df = decode_day(f.read_bytes(), day, scale)
        if len(df):
            frames.append(df)
    if not frames:
        raise RuntimeError(f"no decoded candles for {instrument} under {folder}")
    df = pd.concat(frames, ignore_index=True).drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return CandleSeries(df, Timeframe.MIN_1, (symbol or instrument).upper())


SESSION_CLOSE_HOUR = 17   # the trading day ends at 17:00 New York; 4H, daily, weekly and monthly bins start there


def anchored_resample(minutes: CandleSeries, target: Timeframe, session_offset_hours: float = 0.0,
                      session_tz: Optional[str] = "America/New_York") -> CandleSeries:
    """Resample with the 4H and higher bins anchored to the session boundary.

    With ``session_tz`` the boundary is 17:00 local time in that zone and follows
    its daylight-saving changes (21:00 UTC in summer, 22:00 UTC in winter for New
    York), which is what MetaTrader and TradingView "New York close" candles do.
    Without it the boundary is a fixed ``session_offset_hours`` before midnight UTC.
    Intraday targets below 4H are unaffected either way (their bins repeat every hour).
    """
    if target < Timeframe.H_4:
        return resample(minutes, target)
    if session_tz:
        shift = pd.Timedelta(24 - SESSION_CLOSE_HOUR, unit="h")      # 17:00 local -> midnight of the "session day"
        utc = pd.DatetimeIndex(minutes.df["timestamp"]).tz_localize("UTC")
        local = utc.tz_convert(session_tz).tz_localize(None) + shift
        shifted = CandleSeries(minutes.df.assign(timestamp=local), minutes.timeframe, minutes.symbol, validate=False)
        out = resample(shifted, target)
        back = (pd.DatetimeIndex(out.df["timestamp"]) - shift).tz_localize(session_tz, ambiguous="NaT", nonexistent="shift_forward")
        stamps = back.tz_convert("UTC").tz_localize(None)
        return CandleSeries(out.df.assign(timestamp=stamps), target, minutes.symbol, validate=False)
    if target is Timeframe.H_4 and session_offset_hours:
        shift = pd.Timedelta(session_offset_hours, unit="h")
        shifted = CandleSeries(minutes.df.assign(timestamp=minutes.df["timestamp"] + shift), minutes.timeframe, minutes.symbol, validate=False)
        out = resample(shifted, target)
        return CandleSeries(out.df.assign(timestamp=out.df["timestamp"] - shift), target, minutes.symbol, validate=False)
    return resample(minutes, target, session_offset_hours=session_offset_hours)


def build_cache(symbol: str, instrument: str, raw_dir, out_dir, session_offset_hours: float = 3.0,
                timeframes: Iterable[Timeframe] = CACHE_TIMEFRAMES, keep_minutes: bool = False,
                session_tz: Optional[str] = "America/New_York") -> Dict[str, int]:
    """Decode the raw day files and write every timeframe the engine needs into ``out_dir``."""
    minutes = load_minutes(instrument, raw_dir, symbol)
    written = {}
    if keep_minutes:
        save_series(minutes, out_dir, symbol, merge=False)
        written["1m"] = len(minutes)
    for tf in timeframes:
        series = anchored_resample(minutes, tf, session_offset_hours, session_tz=session_tz)
        save_series(series, out_dir, symbol, merge=False)
        written[tf.label] = len(series)
    return written
