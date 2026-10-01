"""Provenance bundle, ledger-drawn charts, and the as-of gap threshold."""
import json

import numpy as np
import pandas as pd
import pytest

from kronos_trader.backtest.charts import ledger_setup
from kronos_trader.backtest.provenance import write_provenance
from kronos_trader.config import Settings, StructureParams
from kronos_trader.core import Bias, CandleSeries, Direction, Timeframe
from kronos_trader.strategy import analyze_structure


def test_provenance_records_code_settings_data_and_calendar(tmp_path):
    s = Settings()
    (tmp_path / "EURUSD_15min.csv").write_text("timestamp,open,high,low,close,volume\n2024-01-02 10:00,1,1,1,1,0\n", encoding="utf-8")
    path = write_provenance(tmp_path / "run.provenance.json", settings=s, symbol="EURUSD", data_dir=tmp_path, quote_basis="bid",
                            command="python -m kronos_trader backtest --symbol EURUSD")
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["symbol"] == "EURUSD" and doc["costs"]["quote_basis"] == "bid" and "commit" in doc["code"]
    assert doc["settings"]["risk"]["min_rr"] == s.risk.min_rr and doc["versions"]["pandas"]
    assert doc["data"]["EURUSD_15min.csv"]["rows"] == 1 and len(doc["data"]["EURUSD_15min.csv"]["sha256"]) == 64
    assert doc["calendar"]["present"] in (True, False)
    assert doc["settings"]["telegram"]["bot_token_env"] == "TELEGRAM_BOT_TOKEN"   # the env var's name, never its value

    def keys(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield k
                yield from keys(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from keys(v)
    assert not {k for k in keys(doc["settings"]) if k in ("bot_token", "password", "token", "api_key", "secret")}


def _row(**over):
    base = dict(id="P1", direction="LONG", opened_at="2024-01-02 10:00", entry=1.1101, stop=1.0949, take_profit=1.1300,
                r=-0.99, reason="stop", poi_tf="1H", confirmation="BMS", confirmation_tf="15m", poi_low=1.0950, poi_high=1.1050,
                entry_planned=1.1000, confirmed_at="2024-01-02 09:45", touched_at="2024-01-02 09:00", poi_formed="2024-01-02 03:00", lots=0.5)
    base.update(over)
    return pd.Series(base)


class _Poi:
    def __init__(self, low, high):
        self.low, self.high, self.direction = low, high, Bias.BULLISH
        self.key = ("1H", 1, "x")


class _Regenerated:
    def __init__(self, low, high, entry=1.1000):
        from types import SimpleNamespace
        self.poi = _Poi(low, high)
        self.direction, self.entry, self.stop, self.take_profit, self.rr = Direction.LONG, entry, 1.0949, 1.1300, 3.0
        self.confirmation = SimpleNamespace(timestamp=pd.Timestamp("2024-01-02 09:45"), timeframe=Timeframe.MIN_15,
                                            type=SimpleNamespace(value="BMS"))

    def __dataclass_fields__(self):   # pragma: no cover - placeholder so dataclasses.replace is not used on it
        return {}


def test_ledger_setup_draws_the_recorded_levels_and_flags_mismatches():
    drawn, flags = ledger_setup(_row(), None, "EURUSD")
    assert drawn.entry == 1.1101 and drawn.stop == 1.0949 and drawn.take_profit == 1.1300 and drawn.direction is Direction.LONG
    assert drawn.poi.low == 1.0950 and drawn.poi.high == 1.1050 and drawn.confirmation.timeframe is Timeframe.MIN_15
    assert flags and "not reproduced" in flags[0] and "dashed" in flags[0]
    drawn2, flags2 = ledger_setup(_row(poi_low=1.0950, poi_high=1.1050), None, "EURUSD")
    assert drawn2.rr == pytest.approx((1.1300 - 1.1101) / (1.1101 - 1.0949))


def test_gap_threshold_is_as_of_so_later_candles_do_not_reclassify_old_gaps():
    rows = [(1.0, 1.01, 0.99, 1.0)] * 4 + [(1.0, 1.02, 1.0, 1.02), (1.03, 1.05, 1.03, 1.05), (1.06, 1.08, 1.06, 1.08)]   # a gap at index 6
    rows += [(1.08, 1.085, 1.075, 1.08)] * 10
    base = CandleSeries.from_records(rows, Timeframe.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    before = {g.index for g in analyze_structure(base, StructureParams()).gaps}
    assert 6 in before
    wide = rows + [(1.08, 1.30, 0.90, 1.10)] * 30            # later, much wider candles raise the median range
    longer = CandleSeries.from_records(wide, Timeframe.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    after = {g.index for g in analyze_structure(longer, StructureParams()).gaps}
    assert before <= after                                   # old gaps keep their classification
