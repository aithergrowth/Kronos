"""HistData.com free 1-minute forex and gold history: one zip per month, or per year for past years.

The download is a form post: the page for a pair and period carries a token
(``tk``) and the hidden fields, ``get.php`` answers with a zip holding
``DAT_ASCII_<PAIR>_M1_<period>.csv`` (``YYYYMMDD HHMMSS;open;high;low;close;volume``).
The clock is documented as Eastern Standard Time without daylight saving, but it moves with Europe's: the stamps plus
5 hours are London time (``to_utc``). Measured on EURUSD, GBPUSD and gold 2024-2026: the payrolls spike (08:30 New
York) sat 60 minutes late in all 22 European-summer releases with a fixed +5 h, and on time in all 13 winter ones,
the weeks when only the US is on summer time included; the summer weeks opened Sunday 22:00 UTC, not 21:00.  Zips are kept
under ``raw/<PAIR>/<period>.zip`` so a second run fetches only what is new.
``build_cache`` writes the engine cache with 4H, daily, weekly and monthly
candles anchored to the New York close (``session_offset_hours=3``: 21:00 UTC).
"""
from __future__ import annotations

import io
import re
import time
import zipfile
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from .dukascopy import anchored_resample, CACHE_TIMEFRAMES
from .tv_cache import save_series

PAGE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{period}"
GET = "https://www.histdata.com/get.php"
EST_OFFSET = pd.Timedelta(5, unit="h")           # HistData's stamps plus this are London time (see the module notes)


def to_utc(stamps) -> pd.DatetimeIndex:
    """HistData stamps as naive UTC: plus 5 h is London local time (UTC+1 in British summer time). Until 5 October
    2026 a fixed +5 h left every European-summer candle an hour late: the sessions, the news blackouts and the 17:00
    New York anchors of the backtests sat an hour off what a live MT5 feed shows. The hour that does not exist when the
    clocks go forward, and the doubled one in autumn, fall on Sunday night with the market shut: dropped (NaT)."""
    local = pd.DatetimeIndex(pd.to_datetime(stamps)) + EST_OFFSET
    return local.tz_localize("Europe/London", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC").tz_localize(None)


def period_url(pair: str, year: int, month: Optional[int] = None) -> str:
    period = f"{year}/{month}" if month else f"{year}"
    return PAGE.format(pair=pair.lower(), period=period)


def parse_csv(text: str) -> pd.DataFrame:
    rows = []
    for line in text.splitlines():
        parts = line.strip().split(";")
        if len(parts) < 5 or len(parts[0]) < 15:
            continue
        rows.append((parts[0], float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]),
                     float(parts[5]) if len(parts) > 5 and parts[5] else 0.0))
    df = pd.DataFrame(rows, columns=["stamp", "open", "high", "low", "close", "volume"])
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = to_utc(pd.to_datetime(df["stamp"], format="%Y%m%d %H%M%S"))
    df = df.dropna(subset=["timestamp"])
    return df[["timestamp", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def unzip_csv(blob: bytes) -> str:
    z = zipfile.ZipFile(io.BytesIO(blob))
    name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    return z.read(name).decode("ascii", "ignore")


def download_period(pair: str, year: int, month: Optional[int] = None, session=None, timeout: float = 180.0) -> bytes:
    """The zip for one month (or one past year); raises on a missing period."""
    if session is None:
        import requests
        session = requests.Session()
        session.headers["User-Agent"] = "Mozilla/5.0 (kronos_trader)"
    url = period_url(pair, year, month)
    html = session.get(url, timeout=timeout).text
    fields = dict(re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', html))
    if "tk" not in fields:
        raise RuntimeError(f"HistData has no file for {pair} {year}/{month or 'year'}")
    post = {k: fields[k] for k in ("tk", "date", "datemonth", "platform", "timeframe", "fxpair") if k in fields}
    r = session.post(GET, data=post, headers={"Referer": url}, timeout=timeout)
    if r.status_code != 200 or not r.content[:2] == b"PK":
        raise RuntimeError(f"HistData download failed for {pair} {year}/{month or 'year'}: status {r.status_code}")
    return r.content


def periods(start_year: int, end_year: int, end_month: int, this_year: int) -> List[Tuple[int, Optional[int]]]:
    """Past years as whole-year files, the current year month by month up to ``end_month``."""
    out: List[Tuple[int, Optional[int]]] = []
    for y in range(start_year, end_year + 1):
        if y < this_year:
            out.append((y, None))
        else:
            for m in range(1, end_month + 1):
                out.append((y, m))
    return out


def fetch_history(pair: str, start_year: int, end_year: int, end_month: int, raw_dir, session=None, pause: float = 1.5,
                  progress: Optional[Callable[[str], None]] = None, this_year: Optional[int] = None) -> pd.DataFrame:
    this_year = this_year or pd.Timestamp.now(tz="UTC").year
    folder = Path(raw_dir) / pair.upper()
    folder.mkdir(parents=True, exist_ok=True)
    frames = []
    for year, month in periods(start_year, end_year, end_month, this_year):
        target = folder / (f"{year}{month:02d}.zip" if month else f"{year}.zip")
        if not target.exists() or target.stat().st_size == 0:
            try:
                target.write_bytes(download_period(pair, year, month, session=session))
            except Exception as exc:
                if progress:
                    progress(f"{pair} {year}/{month or 'year'}: {exc}")
                continue
            time.sleep(pause)
        if progress:
            progress(f"{pair} {year}/{month or 'year'}: ok")
        frames.append(parse_csv(unzip_csv(target.read_bytes())))
    if not frames:
        raise RuntimeError(f"no HistData files for {pair}")
    df = pd.concat(frames, ignore_index=True).drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return df


def build_cache(symbol: str, pair: str, raw_dir, out_dir, session_offset_hours: float = 3.0,
                timeframes: Iterable[Timeframe] = CACHE_TIMEFRAMES, minutes: Optional[pd.DataFrame] = None,
                session_tz: Optional[str] = "America/New_York") -> Dict[str, int]:
    if minutes is None:
        folder = Path(raw_dir) / pair.upper()
        frames = [parse_csv(unzip_csv(p.read_bytes())) for p in sorted(folder.glob("*.zip")) if p.stat().st_size]
        minutes = pd.concat(frames, ignore_index=True).drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    series = CandleSeries(minutes, Timeframe.MIN_1, symbol.upper())
    written = {}
    for tf in timeframes:
        out = anchored_resample(series, tf, session_offset_hours, session_tz=session_tz)
        save_series(out, out_dir, symbol, merge=False)
        written[tf.label] = len(out)
    return written
