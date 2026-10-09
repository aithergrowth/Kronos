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


def test_news_blackout_windows():
    events = [{"date": "2026-10-02T12:30:00.000Z", "currency": "USD", "title": "Non Farm Payrolls"}]
    (start, end, label), = news_blackout_windows(events, 30, 30)
    assert start == pd.Timestamp("2026-10-02 12:00") and end == pd.Timestamp("2026-10-02 13:00") and "USD" in label


def test_yaml_off_is_read_as_the_string_off(tmp_path):
    from kronos_trader.config import Settings
    path = tmp_path / "c.yaml"
    path.write_text("kronos:\n  mode: off\nrisk:\n  min_rr: 1.5\n", encoding="utf-8")
    s = Settings.load(path)
    assert s.kronos.mode == "off" and s.risk.min_rr == 1.5


def test_a_missing_config_file_is_an_error(tmp_path):
    """A typo in --config, or a profile renamed by an update, stops the start instead of trading the built-in defaults."""
    from kronos_trader.config import Settings
    with pytest.raises(FileNotFoundError, match="config file not found"):
        Settings.load(tmp_path / "dorus_live_typo.yaml")
    assert Settings.load(None).risk.risk_pct > 0                       # no path given: the defaults, as before
