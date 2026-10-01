"""The decision-moment dossier writes a chart per timeframe, the bias notes, the gaps kept and dropped, and the rejections."""
import json

import pandas as pd

from kronos_trader.backtest.dossier import geometric_gaps, write_decision_dossier
from kronos_trader.config import Settings, StructureParams
from kronos_trader.core import CandleSeries, Timeframe
from kronos_trader.data.resample import MultiTimeframeData


def test_geometric_gaps_report_the_threshold_reason():
    rows = [(1.0, 1.01, 0.99, 1.0)] * 4 + [(1.0, 1.02, 1.0, 1.02), (1.03, 1.05, 1.03, 1.05), (1.06, 1.08, 1.06, 1.08)] + [(1.08, 1.085, 1.075, 1.08)] * 5
    series = CandleSeries.from_records(rows, Timeframe.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    gaps = geometric_gaps(series, StructureParams())
    assert gaps and all({"candle3", "direction", "width", "required", "kept", "reason"} <= set(g) for g in gaps)
    tight = geometric_gaps(series, StructureParams(min_gap_fraction=50.0))
    assert tight and not any(g["kept"] for g in tight) and "below" in tight[0]["reason"]


def test_dossier_writes_charts_notes_and_json(tmp_path, scenario):
    s = Settings()
    s.kronos.mode = "off"
    data = MultiTimeframeData.from_base(scenario, [Timeframe.H_1, Timeframe.H_4, Timeframe.D_1])      # the fixture is hourly
    out = write_decision_dossier(s, data, "EURUSD", scenario.last_timestamp, tmp_path / "d")
    readme = (out / "README.md").read_text(encoding="utf-8")
    doc = json.loads((out / "dossier.json").read_text(encoding="utf-8"))
    assert "## 1H" in readme and "Rejections at this moment" in readme
    assert (out / "1H.png").exists() and doc["timeframes"]["1H"]["candles"] > 0
    assert "gaps_geometric" in doc["timeframes"]["1H"] and "decision" in doc
