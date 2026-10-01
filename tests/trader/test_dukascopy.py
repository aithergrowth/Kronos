"""Dukascopy day files: decoding, session-anchored resampling, cache building (no network)."""
import datetime as dt
import lzma
import struct

import pandas as pd

from kronos_trader.core import Timeframe as T
from kronos_trader.data.dukascopy import RECORD, anchored_resample, build_cache, day_url, decode_day, scale_for
from kronos_trader.data.tv_cache import load_all


def _day_file(day_minutes=1440, base=1.1000, scale=1e5):
    records = []
    for m in range(day_minutes):
        o = base + m * 0.00001
        records.append(RECORD.pack(m * 60, int(round(o * scale)), int(round((o + 0.00002) * scale)),
                                   int(round((o - 0.00005) * scale)), int(round((o + 0.00005) * scale)), 12.5))
    return lzma.compress(b"".join(records))


def test_url_and_scale():
    assert day_url("EURUSD", dt.date(2025, 9, 1)) == "https://datafeed.dukascopy.com/datafeed/EURUSD/2025/08/01/BID_candles_min_1.bi5"
    assert scale_for("EURUSD") == 1e5 and scale_for("XAUUSD") == 1e3 and scale_for("usdjpy") == 1e3


def test_decode_day():
    df = decode_day(_day_file(3), dt.date(2025, 9, 1), 1e5)
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"] and len(df) == 3
    assert str(df["timestamp"].iloc[1]) == "2025-09-01 00:01:00"
    assert abs(df["open"].iloc[0] - 1.1) < 1e-9 and abs(df["close"].iloc[0] - 1.10002) < 1e-9
    assert df["high"].iloc[0] >= df["low"].iloc[0] and df["volume"].iloc[0] == 12.5
    assert len(decode_day(b"", dt.date(2025, 9, 1), 1e5)) == 0


def test_build_cache_anchors_the_session(tmp_path):
    raw = tmp_path / "raw" / "EURUSD"
    raw.mkdir(parents=True)
    for day in (dt.date(2025, 9, 1), dt.date(2025, 9, 2)):
        (raw / f"{day.isoformat()}.bi5").write_bytes(_day_file())
    (raw / "2025-09-06.bi5").write_bytes(b"")                                   # an empty (holiday) file
    written = build_cache("EURUSD", "EURUSD", tmp_path / "raw", tmp_path / "cache", session_offset_hours=3.0)
    assert written["5m"] == 576 and written["4H"] >= 12
    views = load_all(tmp_path / "cache", "EURUSD")
    assert {tf.label for tf in views} >= {"5m", "15m", "1H", "4H", "1D", "1W", "1M"}
    h4 = views[T.H_4]
    assert {ts.hour for ts in h4.timestamps} <= {21, 1, 5, 9, 13, 17}        # 4H bins start at the 21:00 UTC session open
    assert views[T.D_1].timestamps.iloc[0].hour == 21
