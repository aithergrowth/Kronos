import pandas as pd
import pytest

from kronos_trader.core import BIAS_TIMEFRAMES, Timeframe


def test_parse_is_case_sensitive_for_minute_vs_month():
    assert Timeframe.parse("1m") is Timeframe.MIN_1
    assert Timeframe.parse("1M") is Timeframe.MN_1
    assert Timeframe.parse("4h") is Timeframe.H_4
    assert Timeframe.parse("4H") is Timeframe.H_4
    assert Timeframe.parse("1D") is Timeframe.D_1
    assert Timeframe.parse("1w") is Timeframe.W_1
    assert Timeframe.parse("monthly") is Timeframe.MN_1
    assert Timeframe.parse(Timeframe.H_1) is Timeframe.H_1
    with pytest.raises(ValueError):
        Timeframe.parse("3h")


def test_ordering_and_bias_timeframes():
    assert Timeframe.MIN_1 < Timeframe.MIN_5 < Timeframe.MIN_15 < Timeframe.H_1 < Timeframe.H_4 < Timeframe.D_1 < Timeframe.W_1 < Timeframe.MN_1
    assert [tf.label for tf in BIAS_TIMEFRAMES] == ["1M", "1W", "1D", "4H", "1H"]
    assert max(BIAS_TIMEFRAMES) is Timeframe.MN_1


def test_floor_and_close_time():
    ts = pd.Timestamp("2024-03-13 10:37")  # a Wednesday
    assert Timeframe.MIN_15.floor(ts) == pd.Timestamp("2024-03-13 10:30")
    assert Timeframe.H_4.floor(ts) == pd.Timestamp("2024-03-13 08:00")
    assert Timeframe.D_1.floor(ts) == pd.Timestamp("2024-03-13")
    assert Timeframe.W_1.floor(ts) == pd.Timestamp("2024-03-11")
    assert Timeframe.MN_1.floor(ts) == pd.Timestamp("2024-03-01")
    assert Timeframe.H_4.close_time(pd.Timestamp("2024-03-13 08:00")) == pd.Timestamp("2024-03-13 12:00")
    assert Timeframe.MN_1.close_time(pd.Timestamp("2024-01-01")) == pd.Timestamp("2024-02-01")


def test_future_timestamps_skip_weekends():
    fri = pd.Timestamp("2024-03-15")  # Friday
    daily = Timeframe.D_1.future_timestamps(fri, 3).tolist()
    assert daily == [pd.Timestamp("2024-03-18"), pd.Timestamp("2024-03-19"), pd.Timestamp("2024-03-20")]
    hourly = Timeframe.H_1.future_timestamps(pd.Timestamp("2024-03-15 22:00"), 3).tolist()
    assert hourly == [pd.Timestamp("2024-03-15 23:00"), pd.Timestamp("2024-03-18 00:00"), pd.Timestamp("2024-03-18 01:00")]
    monthly = Timeframe.MN_1.future_timestamps(pd.Timestamp("2024-03-01"), 2).tolist()
    assert monthly == [pd.Timestamp("2024-04-01"), pd.Timestamp("2024-05-01")]


def test_monthly_close_time_keeps_the_feed_stamp_offset():
    # a New York close feed stamps March as 28 February 21:00: the candle closes 31 March 21:00, not 28 March
    assert Timeframe.MN_1.close_time(pd.Timestamp("2023-02-28 21:00")) == pd.Timestamp("2023-03-31 21:00")
    assert Timeframe.MN_1.close_time(pd.Timestamp("2023-04-30 21:00")) == pd.Timestamp("2023-05-31 21:00")
    # a feed stamping the first of the month at midnight closes on the next first
    assert Timeframe.MN_1.close_time(pd.Timestamp("2007-06-01 00:00")) == pd.Timestamp("2007-07-01 00:00")
    assert Timeframe.MN_1.close_time(pd.Timestamp("2024-02-01 00:00")) == pd.Timestamp("2024-03-01 00:00")
    closes = Timeframe.MN_1.close_times(pd.Series(pd.to_datetime(["2023-02-28 21:00", "2023-03-31 21:00"])))
    assert list(closes) == [pd.Timestamp("2023-03-31 21:00"), pd.Timestamp("2023-04-30 21:00")]
    assert Timeframe.H_4.close_time(pd.Timestamp("2024-01-10 22:00")) == pd.Timestamp("2024-01-11 02:00")


def test_monthly_close_follows_new_york_daylight_saving():
    # November 2023 opens 31 October 21:00 UTC (summer) and closes 30 November 17:00 New York = 22:00 UTC (winter)
    assert Timeframe.MN_1.close_time(pd.Timestamp("2023-10-31 21:00")) == pd.Timestamp("2023-11-30 22:00")
    # March 2024 opens 29 February 22:00 UTC (winter) and closes 31 March 21:00 UTC (summer)
    assert Timeframe.MN_1.close_time(pd.Timestamp("2024-02-29 22:00")) == pd.Timestamp("2024-03-31 21:00")
    # without a session calendar the stamp offset is kept
    assert Timeframe.MN_1.close_time(pd.Timestamp("2023-10-31 21:00"), session_tz=None) == pd.Timestamp("2023-11-30 21:00")


def test_monthly_close_times_are_unit_independent():
    # pandas 3 stores parsed timestamps in microseconds; the cached vector rule must not read them as nanoseconds
    opens_ns = pd.Series(pd.to_datetime(["2023-10-31 21:00", "2024-02-29 22:00"]).astype("datetime64[ns]"))
    opens_us = opens_ns.astype("datetime64[us]")
    want = [pd.Timestamp("2023-11-30 22:00"), pd.Timestamp("2024-03-31 21:00")]
    assert list(Timeframe.MN_1.close_times(opens_ns)) == want
    assert list(Timeframe.MN_1.close_times(opens_us)) == want
    assert list(Timeframe.MN_1.close_times(opens_us, session_tz=None)) == [pd.Timestamp("2023-11-30 21:00"), pd.Timestamp("2024-03-31 22:00")]
