"""scripts/morning_review.py: TradingView payloads into the cache the engine reads."""
import importlib.util
import json
from pathlib import Path

import pandas as pd

from kronos_trader.core.candles import CandleSeries
from kronos_trader.core.timeframe import Timeframe

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("morning_review", ROOT / "scripts" / "morning_review.py")
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def _daily(start: str, days: int) -> CandleSeries:
    """TradingView-style daily candles: each stamped at its session's open, 21:00 UTC the evening before."""
    opens = [pd.Timestamp(start) + pd.Timedelta(days=i) for i in range(days)]
    opens = [t for t in opens if (t + pd.Timedelta(hours=7)).weekday() < 5]           # trading dates Monday-Friday
    n = len(opens)
    df = pd.DataFrame({"timestamp": opens, "open": [1.0 + i for i in range(n)], "high": [1.5 + i for i in range(n)],
                       "low": [0.5 + i for i in range(n)], "close": [1.2 + i for i in range(n)], "volume": [10.0] * n})
    return CandleSeries(df, Timeframe.D_1, "EURUSD")


def test_weeks_and_months_hold_the_sessions_of_their_trading_dates():
    daily = _daily("2026-08-30 21:00", 40)            # sessions of Monday 31 August to Friday 9 October
    now = pd.Timestamp("2026-10-08 06:40")
    weeks = mr.from_sessions(daily, Timeframe.W_1, now).df
    first = weeks.iloc[0]
    assert first["timestamp"] == pd.Timestamp("2026-08-30 21:00")                    # the Sunday-evening open
    assert first["open"] == 1.0 and first["close"] == 5.2 and first["high"] == 5.5    # five sessions, Mon-Fri
    assert weeks["timestamp"].iloc[-1] == pd.Timestamp("2026-09-27 21:00")           # the running week is left out
    months = mr.from_sessions(daily, Timeframe.MN_1, now).df
    assert list(months["timestamp"]) == [pd.Timestamp("2026-08-30 21:00"),            # August: its one session
                                         pd.Timestamp("2026-08-31 21:00")]            # September; October still runs


def test_build_reads_market_and_timeframe_from_the_payload_and_drops_the_forming_candle(tmp_path, monkeypatch):
    now = pd.Timestamp.now(tz="UTC").tz_localize(None).floor("h")
    stamps = [int((now - pd.Timedelta(hours=k)).timestamp()) for k in (3, 2, 1, 0)]  # the last one still forming
    payload = {"symbol": "OANDA:EURUSD", "interval": "1h",
               "bars": {"t": stamps, "o": [1.1] * 4, "h": [1.2] * 4, "l": [1.0] * 4, "c": [1.15] * 4, "v": [1] * 4}}
    f = tmp_path / "payload.txt"
    f.write_text(json.dumps(payload))

    class Args:
        dir = str(tmp_path / "review")
        payloads = [str(f)]
        no_btc = True

    mr.cmd_build(Args())
    out = pd.read_csv(tmp_path / "review" / "cache" / "EURUSD_1H.csv", parse_dates=["timestamp"])
    assert len(out) == 3 and out["timestamp"].iloc[-1] == now - pd.Timedelta(hours=1)
