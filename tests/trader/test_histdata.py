"""HistData files: period plan, CSV parsing with the EST clock, zip handling, cache building (no network)."""
import io
import zipfile

import pandas as pd

from kronos_trader.core import Timeframe as T
from kronos_trader.data.histdata import build_cache, parse_csv, period_url, periods, unzip_csv
from kronos_trader.data.tv_cache import load_all

CSV = "20250801 000000;1.141820;1.141840;1.141740;1.141830;0\n20250801 000100;1.141830;1.141900;1.141800;1.141850;0\n"


def test_periods_and_urls():
    plan = periods(2023, 2026, 9, this_year=2026)
    assert plan[:3] == [(2023, None), (2024, None), (2025, None)] and plan[3] == (2026, 1) and plan[-1] == (2026, 9) and len(plan) == 12
    assert period_url("EURUSD", 2024) == "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd/2024"
    assert period_url("XAUUSD", 2026, 9).endswith("/xauusd/2026/9")


def test_parse_csv_converts_the_clock_to_utc():
    """HistData's stamps plus 5 h are London time: in British summer time 00:00 is 04:00 UTC (a fixed +5 h put every
    summer candle an hour late: the 08:30 New York payrolls spike showed at 13:30 UTC instead of 12:30)."""
    df = parse_csv(CSV)
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"] and len(df) == 2
    assert str(df["timestamp"].iloc[0]) == "2025-08-01 04:00:00"
    assert df["close"].iloc[1] == 1.14185
    nfp = parse_csv("20250703 083000;1.1;1.1;1.1;1.1;0\n20250110 083000;1.0;1.0;1.0;1.0;0\n"     # payrolls, summer / winter
                    "20241101 073000;1.0;1.0;1.0;1.0;0\n")                                      # US summer, UK winter
    assert [str(t) for t in nfp.timestamp] == ["2025-07-03 12:30:00", "2025-01-10 13:30:00", "2024-11-01 12:30:00"]


def test_unzip_and_build_cache(tmp_path):
    buf = io.BytesIO()
    minutes = "\n".join(f"20250801 {h:02d}{m:02d}00;1.1;1.1005;1.0995;1.1002;0" for h in range(24) for m in range(60))
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("DAT_ASCII_EURUSD_M1_202508.csv", minutes)
        z.writestr("DAT_ASCII_EURUSD_M1_202508.txt", "readme")
    assert unzip_csv(buf.getvalue()).startswith("20250801 000000")
    raw = tmp_path / "raw" / "EURUSD"
    raw.mkdir(parents=True)
    (raw / "202508.zip").write_bytes(buf.getvalue())
    written = build_cache("EURUSD", "EURUSD", tmp_path / "raw", tmp_path / "cache", timeframes=(T.MIN_5, T.H_4))
    assert written["5m"] == 288
    views = load_all(tmp_path / "cache", "EURUSD")
    assert {ts.hour for ts in views[T.H_4].timestamps} <= {21, 1, 5, 9, 13, 17}
