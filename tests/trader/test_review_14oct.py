"""The engine review of 14 October: the visit memory survives a restart, the zone clock of the notices matches the
engine's, the setup chart goes out after an executed entry, the chart marks the candle that holds the confirmation,
and the four research knobs (off by default) do what their comments say."""
import json

import pandas as pd
import pytest

from kronos_trader.config import ConfirmationParams, RiskParams, Settings, StructureParams
from kronos_trader.core import Bias, CandleSeries, Direction, Gap, POI, Timeframe as T
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from kronos_trader.strategy import VisitTracker, analyze_structure, map_pois
from kronos_trader.strategy.confirmation import find_confirmation
from kronos_trader.strategy.poi import VisitState
from kronos_trader.strategy.risk import compute_stop, impulse_origin_target
from kronos_trader.strategy.structure import StructureAnalysis

NOW = pd.Timestamp("2026-10-01 09:00")


def _window(settings, engine, clock=NOW):
    return LiveRunner(settings, "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=engine, clock=lambda: clock)


def test_visit_memory_survives_a_restart(tmp_path):
    """visits_<symbol>.json next to the journal: a new window starts with the old window's visit states (when each visit
    began, how many there were), so the 24 h touch-age and visit-age gates read the same clock as before the restart."""
    from types import SimpleNamespace
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    key = ("4H", 1, "2026-09-28 05:00:00")
    state = VisitState(last_ts=pd.Timestamp("2026-10-01 08:55"), inside=True, visits=2, visit_start_ts=pd.Timestamp("2026-09-30 10:05"),
                       invalid=False, first_touch_ts=pd.Timestamp("2026-09-28 12:05"))
    tracker = VisitTracker(); tracker.states[key] = state
    stale = VisitState(last_ts=pd.Timestamp("2026-09-01 08:55"), inside=False, visits=1)      # older than 14 days: left out
    tracker.states[("1H", -1, "2026-08-30 05:00:00")] = stale
    first = _window(settings, SimpleNamespace(visits={"EURUSD": tracker}, traded={}))
    first.save_visits(NOW)
    rows = json.loads((tmp_path / "journal" / "visits_EURUSD.json").read_text())
    assert [tuple(r["key"]) for r in rows] == [("4H", 1, "2026-09-28 05:00:00")]
    again = _window(settings, SimpleNamespace(visits={}, traded={}))
    back = again.engine.visits["EURUSD"].states[key]
    assert (back.visits, back.inside, back.visit_start_ts, back.last_ts, back.first_touch_ts) == \
        (2, True, pd.Timestamp("2026-09-30 10:05"), pd.Timestamp("2026-10-01 08:55"), pd.Timestamp("2026-09-28 12:05"))
    (tmp_path / "journal" / "visits_EURUSD.json").write_text("not json")                        # a damaged file: a fresh start
    assert _window(settings, SimpleNamespace(visits={}, traded={})).engine.visits == {}


def test_the_touch_notice_ages_a_zone_from_its_candles_close_like_the_engine(scenario):
    """A 1H zone whose visit began 23.5 h after it formed is traded by the engine (the clock runs from the zone candle's
    close); the notice and the chart must not call it spent (counted from the candle's open it read 24.5 h)."""
    from types import SimpleNamespace
    settings = Settings(); settings.confirmation.max_touch_age_hours = 24
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    tracker = VisitTracker()
    tracker.states[poi.key] = VisitState(last_ts=NOW, inside=True, visits=1,
                                         visit_start_ts=poi.timeframe.close_time(poi.created_at) + pd.Timedelta(hours=23.5))
    runner = _window(settings, SimpleNamespace(visits={"EURUSD": tracker}, traded={}))
    assert runner.spent_zone(poi, NOW) is False
    tracker.states[poi.key].visit_start_ts = poi.timeframe.close_time(poi.created_at) + pd.Timedelta(hours=24.5)
    assert runner.spent_zone(poi, NOW) is True


def test_the_setup_chart_goes_out_after_an_executed_entry(scenario, tmp_path):
    """Without the approval step the chart went only with a dry run; now it follows the fill (or the resting limit, with
    the limit's price on it)."""
    from kronos_trader.core import Confirmation, ConfirmationType, TradeSetup
    from tests.trader.test_live import FakeEngine
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2026-10-01 08:45"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    setup = TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, 1.1200, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H liquidity")
    settings = Settings()
    settings.live.charts_dir = str(tmp_path / "charts")
    broker = PaperBroker(settings); broker.set_price("EURUSD", 1.1)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup), dry_run=False,
                        require_approval=False, clock=lambda: NOW)
    runner.step(NOW)
    assert len(broker.open_positions()) == 1
    assert any(m.startswith("[photo]") and "setup" in m for m in notifier.sent)
    assert (tmp_path / "charts" / "EURUSD_15m_setup.png").exists()


def test_the_chart_marks_the_candle_that_holds_the_confirmation(tmp_path, scenario):
    """A 5m shift at 09:35 on a 1H chart belongs to the 09:00 candle, not to the 10:00 one."""
    from kronos_trader.core import Confirmation, ConfirmationType, TradeSetup
    from kronos_trader.notify import chart as chart_mod
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    rows = [(100 + i * 0.1, 100.5 + i * 0.1, 99.8 + i * 0.1, 100.3 + i * 0.1) for i in range(12)]
    series = CandleSeries.from_records(rows, T.H_1, start="2026-10-01 00:00", symbol="EURUSD")
    conf = Confirmation(ConfirmationType.BS, T.MIN_5, 9, pd.Timestamp("2026-10-01 09:35"), Bias.BULLISH, 100.9, 100.5, 100.95)
    setup = TradeSetup("EURUSD", Direction.LONG, poi, conf, 100.95, 100.5, 102.0, 0.45, 1.0, 2.3, 1.0, 100.0, 4.0, "test")
    marks = []
    real_plot = chart_mod.__dict__.get("_plot_hook")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.axes
    orig = matplotlib.axes.Axes.plot

    def spy(self, *a, **k):
        if k.get("marker") in ("^", "v"):
            marks.append(a[0][0])
        return orig(self, *a, **k)
    matplotlib.axes.Axes.plot = spy
    try:
        chart_mod.render_chart(series, tmp_path / "s.png", pois=[poi], setup=setup, price_decimals=2, limit_price=100.8)
    finally:
        matplotlib.axes.Axes.plot = orig
    assert marks == [9]                                                 # index of the 09:00 candle


def test_origin_window_without_p_falls_back_when_p_set_the_extreme(scenario):
    """risk.tp_origin_includes_p False: when the P candle itself is the 30-candle extreme, the window before it has no
    extreme beyond the entry, so the setup falls back to liquidity instead of a target a few pips past the zone."""
    st = analyze_structure(scenario)
    poi = map_pois(st, current_price=101.0)[0]
    series = st.series
    p = poi.gap.protector_index
    with_p = impulse_origin_target(Direction.LONG, 100.0, {T.H_1: st}, poi, RiskParams(tp_policy="impulse_origin", tp_origin_candles=3), pip_size=0.01)
    without = impulse_origin_target(Direction.LONG, 100.0, {T.H_1: st}, poi,
                                    RiskParams(tp_policy="impulse_origin", tp_origin_candles=3, tp_origin_includes_p=False), pip_size=0.01)
    assert with_p is not None and with_p[0] == pytest.approx(float(series.high[max(0, p - 3):p + 1].max()))
    assert without is not None and without[0] == pytest.approx(float(series.high[max(0, p - 4):p].max()))
    high_entry = float(series.high[max(0, p - 4):p].max()) + 0.5                 # beyond the window before P: no target
    assert impulse_origin_target(Direction.LONG, high_entry, {T.H_1: st}, poi,
                                 RiskParams(tp_policy="impulse_origin", tp_origin_candles=3, tp_origin_includes_p=False), pip_size=0.01) is None


def test_stop_window_can_include_the_sweep_before_the_re_entry():
    """confirmation.stop_window_includes_sweep: the candles wholly outside the zone right before the re-entry (the sweep of
    P) count for the stop, so it sits beyond that sweep instead of inside it."""
    poi = POI(T.H_4, Bias.BEARISH, 1.0100, 1.0140, None, None, 0, pd.Timestamp("2024-01-01 09:00"))
    closes = [1.0120, 1.0110, 1.0150, 1.0155, 1.0160, 1.0150, 1.0148, 1.0130, 1.0138, 1.0135, 1.0128, 1.0115, 1.0110]
    #        touch   in     above  above  sweep  above  above  back   high   .      shift  .      .
    recs = [(c, c + 0.0004, c - 0.0004, c) for c in closes]
    series = CandleSeries.from_records(recs, T.MIN_5, start="2024-01-02 09:00", symbol="EURUSD")
    st = StructureAnalysis(series, StructureParams())
    st.gaps = [Gap(Bias.BULLISH, 1.0129, 1.0133, 9, series.timestamps.iloc[9], 8, 1.0120, 1.0154, 7)]
    base = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    conf = find_confirmation(series, poi, series.timestamps.iloc[0], base, max_age=100, structure=st)
    assert conf is not None and conf.index == 10 and conf.invalidation_price == pytest.approx(1.0138 + 0.0004)   # since the re-entry at 7
    wide = find_confirmation(series, poi, series.timestamps.iloc[0],
                             ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False, stop_window_includes_sweep=True),
                             max_age=100, structure=st)
    assert wide is not None and wide.index == 10
    assert wide.invalidation_price == pytest.approx(1.0160 + 0.0004)                   # the sweep's high, before the re-entry


def test_first_touch_is_remembered_and_the_touch_rule_can_use_it():
    """VisitState keeps the first visit's first touch; with confirmation.touch_age_from_first_visit the 24 h rule counts
    from it, so a timely zone stays tradable on a later visit."""
    poi = POI(T.H_1, Bias.BULLISH, 100.0, 110.0, None, None, 0, pd.Timestamp("2024-01-01 08:00"))
    state = VisitState()
    ext = 15.0
    state.step(poi, 112.0, 105.0, 108.0, pd.Timestamp("2024-01-01 10:00"), ext, True)    # visit 1
    state.step(poi, 130.0, 111.0, 128.0, pd.Timestamp("2024-01-01 11:00"), ext, True)    # leaves
    state.step(poi, 126.0, 109.0, 109.5, pd.Timestamp("2024-01-02 20:00"), ext, True)    # visit 2, 35 h later
    assert state.visits == 2 and state.visit_start_ts == pd.Timestamp("2024-01-02 20:00")
    assert state.first_touch_ts == pd.Timestamp("2024-01-01 10:00")
    assert ConfirmationParams().touch_age_from_first_visit is False


def test_a_short_stop_can_carry_the_spread():
    spec = Settings().symbol("EURUSD")                                 # pip 0.0001, typical spread 1 pip
    base = compute_stop(Direction.SHORT, 1.1200, spec, RiskParams(sl_offset_pips=0.0))
    with_spread = compute_stop(Direction.SHORT, 1.1200, spec, RiskParams(sl_offset_pips=0.0, short_stop_spread=True))
    assert base == pytest.approx(1.1200) and with_spread == pytest.approx(1.1201)
    assert compute_stop(Direction.LONG, 1.1200, spec, RiskParams(sl_offset_pips=0.0, short_stop_spread=True)) == pytest.approx(1.1200)
