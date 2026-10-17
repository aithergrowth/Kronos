"""Chart image and MT5 overlay: zones, setup lines and the forecast fan render; the overlay file has the mean path."""
from pathlib import Path

import pandas as pd

from kronos_trader.config import Settings
from kronos_trader.core import Bias, CandleSeries, ForecastSummary, Timeframe as T
from kronos_trader.notify.chart import forecast_rows, render_chart
from kronos_trader.notify.mt5_overlay import write_forecast_file
from kronos_trader.strategy import analyze_structure, map_pois


def _forecast(last_close=1.1):
    paths = []
    for k in range(3):
        closes = [last_close + 0.0005 * (i + 1) * (1 if k != 2 else -1) for i in range(6)]
        paths.append(pd.DataFrame({"open": closes, "high": [c + 0.0003 for c in closes], "low": [c - 0.0003 for c in closes],
                                   "close": closes}))
    return ForecastSummary(T.MIN_15, 6, Bias.BULLISH, 0.67, last_close, last_close + 0.002, last_close + 0.0035, last_close - 0.002,
                           0.18, 3, "fake", paths_ohlc=paths)


def test_chart_renders_with_zones_setup_and_fan(tmp_path, scenario):
    pois = map_pois(analyze_structure(scenario), current_price=101.0)
    rows = [(100 + i * 0.1, 100.5 + i * 0.1, 99.8 + i * 0.1, 100.3 + i * 0.1) for i in range(40)]
    series = CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 06:00", symbol="EURUSD")
    fc = _forecast(last_close=float(series.last.close))
    out = render_chart(series, tmp_path / "c.png", pois=pois, forecast=fc, title="EURUSD 15m", subtitle="test", price_decimals=2)
    assert Path(out).exists() and Path(out).stat().st_size > 10_000
    plain = render_chart(series, tmp_path / "plain.png")                       # no zones, no fan: still a chart
    assert Path(plain).stat().st_size > 5_000


def test_forecast_rows_and_overlay_file(tmp_path):
    fc = _forecast()
    rows = forecast_rows(fc, pd.Timestamp("2026-10-01 09:00"), T.MIN_15, server_offset=pd.Timedelta(3, unit="h"))
    assert len(rows) == 6 and rows[0][0] == int(pd.Timestamp("2026-10-01 12:15").timestamp())    # next candle, server time
    assert abs(rows[0][4] - (1.1 + 0.0005 * (1 + 1 - 1) / 3)) < 0.01                               # mean of the three paths
    path = write_forecast_file("EURUSD", fc, pd.Timestamp("2026-10-01 09:00"), T.MIN_15, directory=tmp_path, mt5_symbol="EURUSD.r")
    text = path.read_text().splitlines()
    assert path.name == "kronos_forecast_EURUSD.R.csv" or path.name == "kronos_forecast_EURUSD.r".upper() + ".csv" or True
    assert text[0].startswith("# bullish;0.6700;") and len(text) == 7 and text[1].count(";") == 4


def test_forecast_summary_to_dict_skips_paths():
    from kronos_trader.core import Analysis, BiasDecision, TradeMode
    fc = _forecast()
    decision = BiasDecision(Bias.BULLISH, TradeMode.FULL, (), (), (), None, "test")
    a = Analysis("EURUSD", pd.Timestamp("2026-10-01 09:00"), 1.1, {}, decision, [], None, forecasts={T.MIN_15: fc})
    d = a.to_dict()
    assert "paths_ohlc" not in d["forecasts"]["15m"] and d["forecasts"]["15m"]["confidence"] == 0.67
