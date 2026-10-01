import json

import pandas as pd
import pytest

from kronos_trader.core import CandleSeries, Timeframe
from kronos_trader.data import MultiTimeframeData, cache_path, load_all, load_series, parse_ohlcv_payload, resample, save_payload, save_series
from kronos_trader.data.tradingview_mcp import news_blackout_windows

T = Timeframe

SAMPLE_PAYLOAD = {
    "symbol": "FX:EURUSD", "interval": "1D", "count": 3,
    "bars": [
        {"c": 1.13801, "h": 1.13992, "l": 1.13591, "o": 1.13826, "t": 1790197200, "v": 410816},
        {"c": 1.13902, "h": 1.14109, "l": 1.13682, "o": 1.13801, "t": 1790283600, "v": 181249},
        {"c": 1.13708, "h": 1.13913, "l": 1.13531, "o": 1.13767, "t": 1790542800, "v": 179747},
    ],
    "notice": "bars are delayed 15+ minutes",
}


def test_resample_anchors():
    hourly = CandleSeries.from_records([(1, 2, 0.5, 1.5, 1)] * 24 * 14, T.H_1, start="2024-01-01", symbol="X")  # Mon .. Sun
    weekly = resample(hourly, T.W_1)
    assert weekly.timestamps.tolist() == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-08")]
    assert weekly.volume.tolist() == [168.0, 168.0]
    assert resample(hourly, T.MN_1).timestamps.tolist() == [pd.Timestamp("2024-01-01")]
    four = resample(hourly, T.H_4)
    assert four.timestamps.iloc[1] == pd.Timestamp("2024-01-01 04:00") and len(four) == 84
    shifted = resample(hourly, T.D_1, session_offset_hours=2)
    assert shifted.timestamps.iloc[0] == pd.Timestamp("2023-12-31 22:00")


def test_multi_timeframe_as_of_has_no_lookahead():
    base = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 24 * 3, T.H_1, start="2024-01-01", symbol="X")
    data = MultiTimeframeData.from_base(base, [T.H_4, T.D_1])
    views = data.as_of(pd.Timestamp("2024-01-01 05:30"))
    assert views[T.H_1].last_timestamp == pd.Timestamp("2024-01-01 04:00")
    assert views[T.H_4].last_timestamp == pd.Timestamp("2024-01-01 00:00")
    assert T.D_1 not in views
    views = data.as_of(pd.Timestamp("2024-01-02 00:00"), lookback=5)
    assert len(views[T.H_1]) == 5 and views[T.D_1].last_timestamp == pd.Timestamp("2024-01-01")


@pytest.mark.parametrize("offset", [2, -5.5])
def test_shifted_monthly_resample_rejects_unrepresentable_close_boundaries(offset):
    # With +2, March was labeled Feb 28 22:00 and falsely considered closed
    # on Mar 28, exposing this final Mar 31 high before it occurred.
    rows = [(1, 2, 0.5, 1.5)] * (31 * 24)
    rows[-1] = (1, 99, 0.5, 1.5)
    hourly = CandleSeries.from_records(rows, T.H_1, start="2026-02-28 22:00", symbol="X")
    assert hourly.last_timestamp == pd.Timestamp("2026-03-31 21:00")
    with pytest.raises(ValueError, match="Use native higher-timeframe candles"):
        resample(hourly, T.MN_1, session_offset_hours=offset)


def test_unshifted_monthly_resample_waits_for_calendar_month_end():
    hourly = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * (31 * 24), T.H_1,
                                      start="2026-03-01", symbol="X")
    monthly = resample(hourly, T.MN_1)
    data = MultiTimeframeData({T.MN_1: monthly})
    assert monthly.last_timestamp == pd.Timestamp("2026-03-01")
    assert T.MN_1 not in data.as_of(pd.Timestamp("2026-03-31 23:59"))
    assert len(data.as_of(pd.Timestamp("2026-04-01"))[T.MN_1]) == 1


def test_native_monthly_override_avoids_shifted_resampling():
    hourly = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 48, T.H_1,
                                      start="2026-03-01", symbol="X")
    native = CandleSeries.from_records([(1, 3, 0.5, 2)], T.MN_1, start="2026-02-01", symbol="X")
    assert resample(native, T.MN_1, session_offset_hours=2) is native
    data = MultiTimeframeData.from_base(hourly, [T.D_1, T.MN_1], extra={T.MN_1: native},
                                        session_offset_hours=2)
    assert data[T.MN_1] is native
    assert data[T.D_1].timestamps.iloc[0] == pd.Timestamp("2026-02-28 22:00")


def test_parse_tradingview_payload():
    s = parse_ohlcv_payload(SAMPLE_PAYLOAD, T.D_1)
    assert s.symbol == "FX:EURUSD" and len(s) == 3
    assert s.timestamps.iloc[0] == pd.Timestamp(1790197200, unit="s")
    assert s.close.tolist() == [1.13801, 1.13902, 1.13708]
    again = parse_ohlcv_payload(json.dumps(SAMPLE_PAYLOAD), T.D_1, symbol="OANDA:EURUSD")
    assert again.symbol == "OANDA:EURUSD"


def test_cache_roundtrip_merges(tmp_path):
    path = save_payload(SAMPLE_PAYLOAD, T.D_1, tmp_path)
    assert path.name == "FX_EURUSD_1D.csv"
    more = parse_ohlcv_payload({"bars": SAMPLE_PAYLOAD["bars"][1:] + [{"t": 1790629200, "o": 1.137, "h": 1.138, "l": 1.131, "c": 1.134, "v": 1}]}, T.D_1, "FX:EURUSD")
    save_series(more, tmp_path)
    loaded = load_series(tmp_path, "FX:EURUSD", T.D_1)
    assert len(loaded) == 4
    assert list(load_all(tmp_path, "FX:EURUSD")) == [T.D_1]


def test_cache_names_are_case_safe_and_spacing_is_checked(tmp_path):
    names = {cache_path(tmp_path, "X", tf).name.lower() for tf in T}
    assert len(names) == len(list(T))   # no two timeframes may share a file name on a case-insensitive file system
    monthly = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 6, T.MN_1, start="2024-01-01", symbol="X")
    save_series(monthly, tmp_path)
    assert cache_path(tmp_path, "X", T.MN_1).name == "X_1MO.csv"
    # a monthly file served under the 1-minute name (what Windows did with 1M / 1m) must be rejected, not used
    (tmp_path / "X_1min.csv").write_bytes(cache_path(tmp_path, "X", T.MN_1).read_bytes())
    with pytest.raises(ValueError):
        load_series(tmp_path, "X", T.MIN_1)
    assert set(load_all(tmp_path, "X")) == {T.MN_1}


@pytest.mark.parametrize("count", [2, 4])
def test_cache_rejects_half_hour_candles_labeled_hourly(tmp_path, count):
    mislabeled = CandleSeries.from_records(
        [(1, 2, 0.5, 1.5)] * count, T.H_1, symbol="X",
        timestamps=pd.date_range("2026-01-02 09:00", periods=count, freq="30min"),
    )
    save_series(mislabeled, tmp_path)
    with pytest.raises(ValueError, match="does not contain 1H candles"):
        load_series(tmp_path, "X", T.H_1)


@pytest.mark.parametrize("timeframe,timestamps", [
    (T.H_1, ["2026-01-02 20:00", "2026-01-02 21:00", "2026-01-02 22:00",
             "2026-01-05 00:00", "2026-01-05 01:00", "2026-01-05 02:00"]),
    (T.H_1, ["2026-01-02 22:00", "2026-01-05 00:00"]),
    (T.D_1, ["2026-03-06 22:00", "2026-03-09 21:00", "2026-03-10 21:00", "2026-03-11 21:00"]),
    (T.W_1, ["2026-03-01 22:00", "2026-03-08 21:00", "2026-03-15 21:00"]),
    (T.MN_1, ["2026-01-31 22:00", "2026-02-28 22:00", "2026-03-31 21:00", "2026-04-30 21:00"]),
    (T.MN_1, ["2026-01-01 00:00", "2026-02-01 00:00", "2026-03-01 00:00"]),
])
def test_cache_preserves_calendar_anchors_and_normal_session_gaps(tmp_path, timeframe, timestamps):
    series = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * len(timestamps), timeframe,
                                      symbol="X", timestamps=timestamps)
    save_series(series, tmp_path)
    loaded = load_series(tmp_path, "X", timeframe)
    pd.testing.assert_frame_equal(loaded.df, series.df)


def test_news_blackout_windows():
    events = [{"date": "2026-10-02T12:30:00.000Z", "currency": "USD", "title": "Non Farm Payrolls"}]
    (start, end, label), = news_blackout_windows(events, 30, 30)
    assert start == pd.Timestamp("2026-10-02 12:00") and end == pd.Timestamp("2026-10-02 13:00") and "USD" in label
