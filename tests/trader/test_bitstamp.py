"""Bitstamp feed: pair names, paging, weekly/monthly candles from daily ones, the shared daily fetch, errors, CLI."""
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.cli import _feed
from kronos_trader.config import Settings
from kronos_trader.core import Timeframe as T
from kronos_trader.data.bitstamp import BitstampFeed, pair_for

NOW = int(pd.Timestamp("2026-10-05 08:00").timestamp())     # a Monday, UTC


class FakeBitstamp:
    """Serves ``limit`` candles of ``step`` seconds ending at ``end`` (default: the current candle at NOW)."""

    def __init__(self, status=200):
        self.status, self.calls = status, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {})))
        if url.endswith("/ticker/btcusd/"):
            return SimpleNamespace(status_code=self.status, json=lambda: {"last": "86236.71"}, text="oops")
        step, limit = int(params["step"]), int(params["limit"])
        last = (int(params.get("end", NOW)) // step) * step
        rows = []
        for k in range(limit - 1, -1, -1):
            ts = last - k * step
            base = 80_000 + (ts // step) % 97          # a deterministic wiggle
            rows.append({"timestamp": str(ts), "open": f"{base:.2f}", "high": f"{base + 5:.2f}",
                         "low": f"{base - 5:.2f}", "close": f"{base + 1:.2f}", "volume": "1.5"})
        return SimpleNamespace(status_code=self.status, json=lambda: {"data": {"pair": "BTC/USD", "ohlc": rows}}, text="oops")


def test_pair_names():
    assert pair_for("BTCUSD") == "btcusd" and pair_for("ethusd") == "ethusd" and pair_for("SOLUSD") == "solusd"


def test_intraday_candles_in_one_request():
    session = FakeBitstamp()
    series = BitstampFeed(session=session).get_candles("BTCUSD", T.MIN_5, 300)
    url, params = session.calls[-1]
    assert url == "https://www.bitstamp.net/api/v2/ohlc/btcusd/" and params == {"step": 300, "limit": 300}
    assert len(series) == 300 and series.symbol == "BTCUSD"
    assert series.timestamps.iloc[-1] == pd.Timestamp("2026-10-05 08:00")      # naive UTC bar open, forming bar kept
    assert (series.timestamps.diff().dropna() == pd.Timedelta(minutes=5)).all()


def test_daily_pages_back_a_thousand_at_a_time():
    session = FakeBitstamp()
    series = BitstampFeed(session=session, min_daily_days=0).get_candles("BTCUSD", T.D_1, 2500)
    assert [c[1]["limit"] for c in session.calls] == [1000, 1000, 500]
    ends = [c[1].get("end") for c in session.calls]
    assert ends[0] is None and ends[1] > ends[2]
    assert len(series) == 2500 and series.timestamps.is_monotonic_increasing and series.timestamps.is_unique


def test_weekly_and_monthly_from_daily_share_one_fetch():
    session = FakeBitstamp()
    feed = BitstampFeed(session=session, min_daily_days=2300, clock=lambda: 0.0)
    daily = feed.get_candles("BTCUSD", T.D_1, 300)
    weekly = feed.get_candles("BTCUSD", T.W_1, 120)
    monthly = feed.get_candles("BTCUSD", T.MN_1, 72)
    assert len(session.calls) == 3                          # 2,300 days in pages of 1,000 for all three views
    assert len(daily) == 300 and len(weekly) == 120 and len(monthly) == 72
    assert (weekly.timestamps.dt.dayofweek == 0).all() and (weekly.timestamps.dt.hour == 0).all()
    assert (monthly.timestamps.dt.day == 1).all()
    d = daily.df.set_index("timestamp") if "timestamp" in daily.df.columns else daily.df
    week = weekly.timestamps.iloc[-2]                        # last complete week
    days = d.loc[week:week + pd.Timedelta(days=6)]
    row = weekly.df.iloc[-2]
    assert row["high"] == pytest.approx(days["high"].max()) and row["low"] == pytest.approx(days["low"].min())
    assert row["open"] == pytest.approx(days["open"].iloc[0]) and row["close"] == pytest.approx(days["close"].iloc[-1])


def test_errors_and_ticker():
    with pytest.raises(RuntimeError, match="Bitstamp 500"):
        BitstampFeed(session=FakeBitstamp(status=500)).get_candles("BTCUSD", T.H_1, 10)
    assert BitstampFeed(session=FakeBitstamp()).current_price("BTCUSD") == pytest.approx(86236.71)


def test_cli_builds_the_feed():
    args = SimpleNamespace(feed="bitstamp", broker="paper")
    kind, feed = _feed(args, Settings(), broker=None)
    assert kind == "bitstamp" and isinstance(feed, BitstampFeed)
    assert Settings().symbol("ETHUSD").pip_size == pytest.approx(0.1)
