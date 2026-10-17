"""Astra's integration probes: visits are tracked before the entry gates, charts match identity, the first breach is exported."""
import copy
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from kronos_trader.backtest.charts import ledger_setup
from kronos_trader.backtest.runner import BacktestResult
from kronos_trader.config import PropFirmParams, Settings
from kronos_trader.core import (Bias, CandleSeries, Confirmation, ConfirmationType, Direction, POI, POIStatus, Timeframe,
                                TimeframeBias, TradeSetup)
from kronos_trader.execution import RiskGuard
from kronos_trader.strategy import current_visit
from kronos_trader.strategy.engine import StrategyEngine

T = Timeframe


def test_a_touch_during_a_closed_session_still_counts_as_a_visit():
    """First touch at 02:05 Amsterdam (outside the window); by the next touch it has left the 400-candle window."""
    s = Settings()
    s.session.enabled = True
    s.news.enabled = False
    poi = POI(T.H_1, Bias.BULLISH, 100.0, 110.0, None, None, 0, pd.Timestamp("2024-01-01 00:00"))
    rows = [(111.0, 112.0, 109.0, 109.5), (110.0, 131.0, 109.0, 130.0)] + [(130.0, 131.0, 129.0, 130.0)] * 400 + [(111.0, 112.0, 109.0, 109.5)]
    history = CandleSeries.from_records(rows, T.MIN_5, start="2024-01-01 01:00", symbol="EURUSD")
    assert current_visit(poi, history, 1.5)[1] == 2
    htf = {tf: CandleSeries.from_records([(105.0, 120.0, 95.0, 109.5)], tf, start=start, symbol="EURUSD")
           for tf, start in [(T.MN_1, "2023-11-01"), (T.W_1, "2023-12-18"), (T.D_1, "2023-12-31"), (T.H_4, "2023-12-31 20:00"), (T.H_1, "2024-01-01 00:00")]}
    eng = StrategyEngine(s)
    eng.structure_for = lambda symbol, view: SimpleNamespace(series=view)
    last = None
    with patch("kronos_trader.strategy.engine.timeframe_bias", lambda st, *a: TimeframeBias(st.series.timeframe, Bias.BULLISH, Bias.BULLISH, Bias.BULLISH)), \
         patch("kronos_trader.strategy.engine.map_pois", lambda st, *a: [poi] if st.series.timeframe is T.H_1 else []), \
         patch("kronos_trader.strategy.engine.find_confirmation", lambda *a, **k: None):
        for n in range(1, len(history) + 1):
            view = history.head(n)
            poi.status = POIStatus.ACTIVE if poi.contains(float(view.last.close)) else POIStatus.FRESH
            last = eng.analyze("EURUSD", {**htf, T.MIN_5: view}, now=view.last_close_time)
    state = eng.visits["EURUSD"].states[poi.key]
    assert state.visits == 2
    assert any("visit #2 - only the first return is traded" in r for r in last.rejections)


def test_chart_uses_the_recorded_confirmation_and_flags_a_different_zone_identity():
    conf = Confirmation(ConfirmationType.BMS, T.MIN_15, 0, pd.Timestamp("2024-01-02 11:45"), Bias.BULLISH, 1.105, 1.095, 1.1)
    zone = POI(T.H_1, Bias.BULLISH, 1.095, 1.105, None, None, 0, pd.Timestamp("2024-01-02 05:00"))
    setup = TradeSetup("EURUSD", Direction.LONG, zone, conf, 1.1, 1.0949, 1.13, 0.0051, 0.03, 5.88, 0.5, 255.0, 4.0, "synthetic")
    row = pd.Series(dict(direction="LONG", opened_at="2024-01-02 10:00", entry=1.1101, stop=1.0949, take_profit=1.13,
                         poi_tf="1H", poi_low=1.095, poi_high=1.105, poi_formed="2024-01-02 03:00",
                         confirmation="BMS", confirmation_tf="15m", confirmed_at="2024-01-02 09:45",
                         entry_planned=1.1, touched_at="2024-01-02 09:00", lots=0.5))
    drawn, flags = ledger_setup(row, setup, "EURUSD")
    assert drawn.entry == 1.1101 and drawn.confirmation.timestamp == pd.Timestamp("2024-01-02 09:45")
    assert drawn.poi.created_at == pd.Timestamp("2024-01-02 03:00")              # the record's zone, not the replay's
    assert flags and "REPLAY MISMATCH" in flags[0] and "zone formation time" in flags[0] and "confirmation time" in flags[0]
    # a replay that matches the record keeps its zone (with the X/B/P marks) and still draws the recorded confirmation
    same = pd.Series(dict(row, poi_formed="2024-01-02 05:00", confirmed_at="2024-01-02 11:45"))
    drawn2, flags2 = ledger_setup(same, setup, "EURUSD")
    assert flags2 == [] and drawn2.poi is zone and drawn2.confirmation.timestamp == pd.Timestamp("2024-01-02 11:45")


def test_first_breach_is_recorded_against_published_limits_and_exported():
    guard = RiskGuard(PropFirmParams(daily_loss_limit_pct=1000.0, max_drawdown_pct=1000.0), 100_000)   # research run: no halting
    guard.update(pd.Timestamp("2024-01-02 22:55"), 100_000, 100_000)
    guard.update(pd.Timestamp("2024-01-02 23:00"), 94_000, 100_000)
    assert guard.first_breach is not None and "daily loss 6.00% >= 5.0%" in guard.first_breach[1]
    guard.update(pd.Timestamp("2024-01-03 01:00"), 100_000, 100_000)
    assert guard.first_breach is not None                                     # kept after the recovery
    assert guard.rules()["recorded_against"] == {"daily_loss_pct_of_initial": 5.0, "max_loss_pct_of_initial_static": 10.0}
    assert "first_breach" in BacktestResult.__dataclass_fields__ and "guard_rules" in BacktestResult.__dataclass_fields__
