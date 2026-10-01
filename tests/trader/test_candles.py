import pandas as pd

from kronos_trader.core import CandleSeries, Timeframe


def test_from_records_and_candle_properties():
    s = CandleSeries.from_records([(1, 2, 0.5, 1.5), (1.5, 2.5, 1, 1.2)], Timeframe.H_1, symbol="EURUSD")
    assert len(s) == 2
    assert s.timestamps.iloc[1] == pd.Timestamp("2024-01-01 01:00")
    c = s[0]
    assert c.is_bullish and c.body_high == 1.5 and c.body_low == 1 and c.range == 1.5
    assert s[-1].is_bearish
    assert s.last_close_time == pd.Timestamp("2024-01-01 02:00")


def test_closed_as_of_excludes_forming_candle():
    s = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 5, Timeframe.H_4, start="2024-01-01")
    assert len(s.closed_as_of(pd.Timestamp("2024-01-01 03:59"))) == 0
    assert len(s.closed_as_of(pd.Timestamp("2024-01-01 04:00"))) == 1
    assert len(s.closed_as_of(pd.Timestamp("2024-01-01 15:00"))) == 3
    assert len(s.closed_as_of(pd.Timestamp("2025-01-01"))) == 5
    m = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 3, Timeframe.MN_1, start="2024-01-01")
    assert len(m.closed_as_of(pd.Timestamp("2024-02-01"))) == 1
    assert len(m.closed_as_of(pd.Timestamp("2024-03-15"))) == 2


def test_from_csv_handles_bom_and_metatrader_columns(tmp_path):
    p = tmp_path / "EURUSD_M1.csv"
    p.write_text("﻿<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\n"
                 "2024.01.02\t00:00:00\t1.1\t1.2\t1.0\t1.15\t10\n"
                 "2024.01.02\t00:01:00\t1.15\t1.16\t1.14\t1.14\t12\n", encoding="utf-8")
    s = CandleSeries.from_csv(p, Timeframe.MIN_1)
    assert s.symbol == "EURUSD"
    assert len(s) == 2 and s.timestamps.iloc[0] == pd.Timestamp("2024-01-02 00:00")
    assert s.volume.tolist() == [10.0, 12.0]


def test_from_csv_unix_seconds_and_repairs_bad_high(tmp_path):
    p = tmp_path / "bars.csv"
    p.write_text("time,open,high,low,close,Volume\n1704153600,1.1,1.05,1.0,1.15,5\n1704157200,1.15,1.2,1.1,1.12,6\n")
    s = CandleSeries.from_csv(p, Timeframe.H_1, symbol="X")
    assert s.timestamps.iloc[0] == pd.Timestamp("2024-01-02 00:00")
    assert s.high[0] == 1.15  # repaired: high may not be below the close


def test_to_kronos_inputs_adds_amount():
    s = CandleSeries.from_records([(1, 2, 0.5, 1.5, 100)], Timeframe.H_1)
    x, ts = s.to_kronos_inputs()
    assert list(x.columns) == ["open", "high", "low", "close", "volume", "amount"]
    assert x["amount"].iloc[0] == 100 * (1 + 2 + 0.5 + 1.5) / 4
    assert len(ts) == 1


def test_monthly_candle_is_not_visible_before_the_month_ends():
    import pandas as pd
    from kronos_trader.core import CandleSeries, Timeframe
    from kronos_trader.data.resample import MultiTimeframeData
    rows = [(1.0, 1.1, 0.9, 1.05), (1.05, 1.3, 1.0, 1.2)]
    monthly = CandleSeries.from_records(rows, Timeframe.MN_1, start="2023-01-31 22:00", symbol="EURUSD")
    monthly.df.loc[1, "timestamp"] = pd.Timestamp("2023-02-28 21:00")   # March, stamped the evening before
    assert len(monthly.closed_as_of(pd.Timestamp("2023-03-28 21:00"))) == 1     # the old rule showed it here
    assert len(monthly.closed_as_of(pd.Timestamp("2023-03-31 20:59"))) == 1
    assert len(monthly.closed_as_of(pd.Timestamp("2023-03-31 21:00"))) == 2
    data = MultiTimeframeData({Timeframe.MN_1: monthly})
    assert len(data.as_of(pd.Timestamp("2023-03-30"))[Timeframe.MN_1]) == 1
    assert len(data.as_of(pd.Timestamp("2023-04-01"))[Timeframe.MN_1]) == 2


def test_csv_columns_with_pandas_string_dtype_are_coerced():
    import pandas as pd
    from kronos_trader.core.candles import _coerce_columns
    raw = pd.DataFrame({"timestamp": pd.array(["2024-01-02 10:00", "2024-01-02 10:05"], dtype=pd.StringDtype()),
                        "open": [1.0, 1.1], "high": [1.2, 1.3], "low": [0.9, 1.0], "close": [1.1, 1.2]})
    frame = _coerce_columns(raw)
    assert list(frame["timestamp"]) == [pd.Timestamp("2024-01-02 10:00"), pd.Timestamp("2024-01-02 10:05")]
    raw2 = pd.DataFrame({"Date": pd.array(["2024.01.02", "2024.01.02"], dtype=pd.StringDtype()),
                         "Time": pd.array(["10:00", "10:05"], dtype=pd.StringDtype()),
                         "Open": [1.0, 1.1], "High": [1.2, 1.3], "Low": [0.9, 1.0], "Close": [1.1, 1.2]})
    assert len(_coerce_columns(raw2)) == 2
