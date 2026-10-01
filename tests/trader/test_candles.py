import pandas as pd
import pytest

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


@pytest.mark.parametrize("opened,closed", [
    ("2026-01-31 22:00", "2026-02-28 22:00"),
    ("2024-01-31 22:00", "2024-02-29 22:00"),
    ("2026-03-31 21:00", "2026-04-30 21:00"),
    ("2026-01-01 00:00", "2026-02-01 00:00"),
])
def test_monthly_closed_as_of_uses_forward_calendar_close(opened, closed):
    from kronos_trader.data import MultiTimeframeData

    series = CandleSeries.from_records([(1, 2, 0.5, 1.5)], Timeframe.MN_1,
                                      timestamps=[pd.Timestamp(opened)])
    boundary = pd.Timestamp(closed)
    assert series.last_close_time == boundary
    assert len(series.closed_as_of(boundary - pd.Timedelta(1, unit="ns"))) == 0
    assert len(series.closed_as_of(boundary)) == 1
    bundled = MultiTimeframeData({Timeframe.MN_1: series}).as_of(boundary)[Timeframe.MN_1]
    pd.testing.assert_frame_equal(series.closed_as_of(boundary).df, bundled.df)


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


@pytest.mark.parametrize("time_header,time_rows,string_columns", [
    ("timestamp", ["2024-01-02 00:00:00", "2024-01-02 01:00:00"], ["timestamp"]),
    ("date,time", ["2024-01-02,00:00:00", "2024-01-02,01:00:00"], ["date", "time"]),
], ids=["timestamp_string_dtype", "separate_date_time_string_dtype"])
def test_from_csv_accepts_string_extension_timestamps(tmp_path, monkeypatch, time_header, time_rows, string_columns):
    path = tmp_path / "EURUSD_H1.csv"
    path.write_text(f"{time_header},open,high,low,close,volume\n"
                    f"{time_rows[0]},1.1,1.2,1.0,1.15,5\n"
                    f"{time_rows[1]},1.15,1.2,1.1,1.12,6\n", encoding="utf-8")
    read_csv = pd.read_csv

    def read_with_extension_strings(*args, **kwargs):
        # Explicit dtype reproduces pandas 3's inferred string columns on pandas 2 too.
        frame = read_csv(*args, **kwargs, dtype={column: "string" for column in string_columns})
        assert all(isinstance(frame[column].dtype, pd.StringDtype) for column in string_columns)
        return frame

    monkeypatch.setattr(pd, "read_csv", read_with_extension_strings)
    series = CandleSeries.from_csv(path, Timeframe.H_1)

    assert series.timestamps.tolist() == [pd.Timestamp("2024-01-02 00:00"), pd.Timestamp("2024-01-02 01:00")]
    assert series.timestamps.dt.tz is None
    assert series.close.tolist() == [1.15, 1.12]
    assert series.volume.tolist() == [5.0, 6.0]


def test_to_kronos_inputs_adds_amount():
    s = CandleSeries.from_records([(1, 2, 0.5, 1.5, 100)], Timeframe.H_1)
    x, ts = s.to_kronos_inputs()
    assert list(x.columns) == ["open", "high", "low", "close", "volume", "amount"]
    assert x["amount"].iloc[0] == 100 * (1 + 2 + 0.5 + 1.5) / 4
    assert len(ts) == 1
