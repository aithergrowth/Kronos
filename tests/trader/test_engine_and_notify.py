import pandas as pd
import pytest

from kronos_trader.backtest import Backtester, summarize
from kronos_trader.config import Settings, SymbolSpec
from kronos_trader.core import BIAS_TIMEFRAMES, Bias, CandleSeries, Direction, Timeframe
from kronos_trader.data import MultiTimeframeData
from kronos_trader.notify import TelegramNotifier, format_analysis, format_setup
from kronos_trader.strategy import StrategyEngine

from conftest import HK_CSV

T = Timeframe


@pytest.fixture(scope="module")
def hk_data():
    base = CandleSeries.from_csv(HK_CSV, T.MIN_5, symbol="09988")
    return MultiTimeframeData.from_base(base, [T.MIN_15, T.H_1, T.H_4, T.D_1, T.W_1, T.MN_1])


def _settings():
    s = Settings()
    s.symbols["09988"] = SymbolSpec("09988", 0.01, 1.0, price_decimals=2, typical_spread_pips=2.0)
    s.kronos.mode = "off"
    s.session.enabled = False     # Hong Kong stock hours, not the Amsterdam forex windows
    return s


def test_session_windows():
    from kronos_trader.config import SessionParams
    from kronos_trader.strategy.engine import in_session
    params = SessionParams()                                                              # Max's 09:00-17:00
    assert in_session(pd.Timestamp("2026-10-01 07:30"), params) == (True, "Thu 09:30")     # CEST = UTC+2
    assert in_session(pd.Timestamp("2026-10-01 09:30"), params)[0] is True                 # 11:30 Amsterdam
    assert in_session(pd.Timestamp("2026-10-01 06:59"), params)[0] is False                # 08:59: before the open
    split = SessionParams(windows=(("09:00", "11:00"), ("13:00", "17:00")))               # A's split windows
    assert in_session(pd.Timestamp("2026-10-01 09:30"), split)[0] is False                 # 11:30: between A's windows
    assert in_session(pd.Timestamp("2026-10-01 14:59"), params)[0] is True                 # 16:59
    assert in_session(pd.Timestamp("2026-10-01 15:00"), params)[0] is False                # 17:00 is rejected (A 02:30:56)
    assert in_session(pd.Timestamp("2026-10-03 08:00"), params)[0] is False                # Saturday
    assert in_session(pd.Timestamp("2026-12-01 08:30"), params) == (True, "Tue 09:30")     # CET = UTC+1


def test_engine_analysis_on_real_data(hk_data):
    engine = StrategyEngine(_settings())
    now = pd.Timestamp("2024-06-03 10:00")
    analysis = engine.analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    assert set(analysis.biases) == set(BIAS_TIMEFRAMES)
    assert analysis.timestamp == now
    assert all(p.high > p.low for p in analysis.pois)
    assert analysis.decision.reason
    text = format_analysis(analysis, _settings().symbol("09988"))
    assert "09988" in text and "Bias:" in text
    d = analysis.to_dict()
    assert d["symbol"] == "09988" and isinstance(d["pois"], list)


def test_backtest_two_weeks_is_consistent(hk_data):
    s = _settings()
    s.confirmation.allow_first_candle = True   # more signals for the consistency checks
    result = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert result.steps > 100
    for t in result.trades:
        assert t.meta["planned_rr"] >= 3.0
        if t.direction is Direction.LONG:
            assert t.initial_stop < t.entry < t.take_profit
        else:
            assert t.take_profit < t.entry < t.initial_stop
        if t.reason == "breakeven":
            assert t.stop == pytest.approx(t.entry)
        assert t.reason in {"stop", "take_profit", "breakeven", "end_of_data"}
        assert t.lots > 0
        # the ledger says which P the stop sits behind and when the confirmation candle closed
        assert t.meta["stop_tf"] and t.meta["stop_basis"] and t.meta["stop_p"] is not None
        spec = s.symbol("09988")
        if t.direction is Direction.LONG:            # the stop sits behind the recorded P, within the offset and the spread
            assert t.initial_stop <= t.meta["stop_p"] + 1e-9
        else:
            assert t.initial_stop >= t.meta["stop_p"] - 1e-9
        assert abs(t.meta["stop_p"] - t.initial_stop) <= (s.risk.sl_offset_pips + spec.typical_spread_pips + 1) * spec.pip_size
        assert pd.Timestamp(t.meta["confirmed_close_at"]) > pd.Timestamp(t.meta["confirmed_at"])
        assert pd.Timestamp(t.meta["confirmed_close_at"]) <= t.opened_at
    frame = result.trades_frame()
    if len(frame):
        assert {"stop_p", "stop_tf", "stop_p_open", "stop_p_close", "stop_basis", "confirmed_close_at"} <= set(frame.columns)
    stats = summarize(result)
    assert stats["trades"] == len(result.trades)
    assert result.rejected_by_guard <= result.signals


def test_format_setup_and_dry_run_notifier(scenario):
    from kronos_trader.core import Confirmation, ConfirmationType, TradeSetup
    from kronos_trader.strategy import analyze_structure, map_pois
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 105.8, 100.0, 106.0)
    setup = TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, 1.1200, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H buy-side liquidity")
    text = format_setup(setup, None, Settings().symbol("EURUSD"))
    assert "BUY" in text and "1.10000" in text and "1.09490" in text and f"1:{3.85:.1f}" in text
    notifier = TelegramNotifier(dry_run=True)
    assert notifier.send_setup(setup) is False and notifier.sent and "BUY" in notifier.sent[0]


def test_news_blackout_blocks_new_entries(hk_data):
    """A high-impact event of the symbol's currency inside the window stops new entries (open trades run on)."""
    from kronos_trader.data.calendar import NewsCalendar, NewsEvent
    gated = _settings()
    gated.session.enabled = True
    # find a moment where the bias allows a trade, so the entry gates are reached (session says no at 20:00 Amsterdam)
    reached = None
    for day in pd.date_range("2024-06-03", "2024-06-28", freq="B"):
        now = day + pd.Timedelta(18, unit="h")
        a = StrategyEngine(gated).analyze("09988", hk_data.as_of(now, lookback=400), now=now)
        if any("outside the entry windows" in r for r in a.rejections):
            reached = now
            break
    assert reached is not None
    calendar = NewsCalendar([NewsEvent(reached + pd.Timedelta(10, unit="min"), "USD", "Non Farm Payrolls", 1)])
    engine = StrategyEngine(_settings(), calendar=calendar)        # sessions off, calendar on
    a = engine.analyze("09988", hk_data.as_of(reached, lookback=400), now=reached)
    assert any("news blackout: Non Farm Payrolls (USD)" in r for r in a.rejections) and not a.has_valid_signal
    quiet = StrategyEngine(_settings(), calendar=NewsCalendar([]))
    a2 = quiet.analyze("09988", hk_data.as_of(reached, lookback=400), now=reached)
    assert not any("news blackout" in r for r in a2.rejections)


def test_assume_direction_walks_past_a_refusing_gate_without_making_a_signal(hk_data):
    """Diagnostic mode: the refusal is recorded, the later gates still report, nothing becomes a signal."""
    from kronos_trader.core import Direction
    from kronos_trader.strategy.engine import StrategyEngine
    s = _settings()
    s.session.enabled = True
    s.session.windows = [["03:00", "03:05"]]              # a window the moment is outside of: the session gate refuses
    engine = StrategyEngine(s)
    now = pd.Timestamp("2024-06-03 10:00")
    plain = engine.analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    assert not plain.has_valid_signal and getattr(plain, "diagnostic_setup", None) is None
    diag = StrategyEngine(s).analyze("09988", hk_data.as_of(now, lookback=400), now=now, assume_direction=Direction.SHORT)
    assert not diag.has_valid_signal
    assert any(r.startswith("outside the entry windows") for r in diag.rejections)
    later = [r for r in diag.rejections if r.startswith("outside") is False and r != plain.rejections[0]]
    assert later, "the walk-through must report the gates after the refusing one"
    assert all("not a signal" in r or "diagnostic" in r or "POI" in r or "visit" in r or "confirmation" in r or "fewer" in r or "zones" in r
               for r in later)


def test_stop_protection_poi_keeps_the_stop_on_the_zones_own_p(hk_data):
    s = _settings()
    s.confirmation.allow_first_candle = True
    s.risk.stop_protection = "poi"
    result = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert result.trades, "the fixture produces trades"
    for t in result.trades:
        assert t.meta["stop_basis"].startswith("P of the POI itself")
        assert t.meta["stop_tf"] == t.meta["poi_tf"]
        assert abs(t.meta["stop_p"] - t.meta["poi_p"]) < 1e-9


def test_entry_outside_zone_keeps_a_just_left_zone_while_its_visit_is_open(hk_data):
    """With the option on, a zone price has just left (status tested, visit still open) is still examined; the visit gate,
    not the status, decides.  The default keeps the old behaviour."""
    from kronos_trader.core import POIStatus
    from kronos_trader.strategy.engine import StrategyEngine
    s = _settings(); s.confirmation.allow_first_candle = True
    now = pd.Timestamp("2024-06-03 10:00")
    base = StrategyEngine(s).analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    s2 = _settings(); s2.confirmation.allow_first_candle = True; s2.confirmation.entry_outside_zone = True
    wide = StrategyEngine(s2).analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    tested_same_side = [p for p in wide.pois if p.status is POIStatus.TESTED and p.direction is wide.decision.direction]
    mentioned = lambda a: {r.split(":")[0] for r in a.rejections if "POI" in r and ":" in r}
    assert mentioned(base) <= mentioned(wide)                      # the wider filter never drops a zone the narrow one examined
    if tested_same_side and wide.decision.tradable:
        assert len(mentioned(wide)) >= len(mentioned(base))


def test_one_trade_per_visit_blocks_a_second_entry_on_the_same_zone_and_visit(hk_data):
    """With ``one_trade_per_visit`` a zone that was traded during a visit gives no second signal in that visit (R6: re-entries
    after a stop-out on the same zone won 9 %).  The runner tells the engine which zone it traded; the default keeps re-entries."""
    s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
    s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
    base = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    s2 = _settings(); s2.confirmation.allow_first_candle = True; s2.confirmation.entry_outside_zone = True
    s2.prop_firm.max_drawdown_pct = 1000.0; s2.prop_firm.daily_loss_limit_pct = 1000.0
    s2.confirmation.one_trade_per_visit = True
    once = Backtester(s2, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    key = lambda t: (t.meta["poi_tf"], t.meta["poi"], str(t.meta["poi_formed"]), t.meta["visit"])
    assert len(once.trades) <= len(base.trades)
    assert len({key(t) for t in once.trades}) == len(once.trades), "no zone is traded twice in one visit"
    assert any(r.startswith("one trade per visit") or "one trade per visit" in r for r in once.rejection_reasons) or len(once.trades) == len(base.trades)


def test_poi_timeframes_limits_the_zones_traded_in_full_mode(hk_data):
    """``confirmation.poi_timeframes`` names the zone timeframes a full-mode bias may trade; the default keeps all five."""
    from kronos_trader.core.timeframe import Timeframe as T
    s = _settings(); s.confirmation.allow_first_candle = True
    s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
    base = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    s2 = _settings(); s2.confirmation.allow_first_candle = True
    s2.prop_firm.max_drawdown_pct = 1000.0; s2.prop_firm.daily_loss_limit_pct = 1000.0
    s2.confirmation.poi_timeframes = (T.H_1,)
    s2.confirmation.scalp_poi_timeframes = (T.H_1,)
    only_1h = Backtester(s2, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert only_1h.trades and all(t.meta["poi_tf"] == "1H" for t in only_1h.trades)
    assert any(t.meta["poi_tf"] != "1H" for t in base.trades)      # the default traded a higher-timeframe zone here


def test_max_zone_age_candles_refuses_stale_zones(hk_data):
    """``confirmation.max_zone_age_candles``: a zone older than that many candles of its own timeframe is not a candidate
    (loss anatomy, 4 October: zones under a day old won 43-48 % on three markets, older ones 12-33 %). Off by default."""
    s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
    s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
    base = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    s2 = _settings(); s2.confirmation.allow_first_candle = True; s2.confirmation.entry_outside_zone = True
    s2.prop_firm.max_drawdown_pct = 1000.0; s2.prop_firm.daily_loss_limit_pct = 1000.0
    s2.confirmation.max_zone_age_candles = 2
    fresh = Backtester(s2, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert len(fresh.trades) < len(base.trades)
    assert any("candles old" in r for r in fresh.rejection_reasons)
    for t in fresh.trades:
        tf = T.parse(t.meta["poi_tf"])
        assert (pd.Timestamp(t.opened_at) - pd.Timestamp(t.meta["poi_formed"])) / tf.delta() <= 2 + 1   # the scan step adds at most one candle


def test_max_touch_age_hours_refuses_a_zone_touched_long_after_it_formed(hk_data):
    """``confirmation.max_touch_age_hours``: a visit that began more than that many hours after the zone formed is not
    traded, whatever the zone's timeframe (7 October: zones touched after a day lost in every market). Off by default."""
    s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
    s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
    base = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    waited = [(pd.Timestamp(t.meta["touched_at"]) - pd.Timestamp(t.meta["poi_formed"])) / pd.Timedelta(hours=1) for t in base.trades]
    limit = min(waited) + 1.0                                # the freshest visit stays, the later ones go
    assert max(waited) > limit
    s.confirmation.max_touch_age_hours = limit
    fresh = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert any("after it formed" in r and "a spent zone" in r for r in fresh.rejection_reasons)
    assert fresh.trades and all((pd.Timestamp(t.meta["touched_at"]) - pd.Timestamp(t.meta["poi_formed"]))
                                / pd.Timedelta(hours=1) <= limit for t in fresh.trades)


def test_max_touch_age_by_tf_sets_the_limit_per_zone_timeframe(hk_data):
    """``confirmation.max_touch_age_by_tf`` in place of max_touch_age_hours for the zone timeframes it names (0 = no limit
    there): Max, 8 October, a week-old drawing is fine on the higher timeframes."""
    def run(**c):
        s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
        s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
        for key, value in c.items():
            setattr(s.confirmation, key, value)
        return Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    base = run()
    waited = {(t.meta["poi_tf"], round((pd.Timestamp(t.meta["touched_at"]) - pd.Timestamp(t.meta["poi_formed"]))
                                       / pd.Timedelta(hours=1), 1)) for t in base.trades}
    tf, hours = max(waited, key=lambda x: x[1])              # the latest-touched zone of the base run
    strict = run(max_touch_age_hours=0.5)
    assert all(t.meta["poi_tf"] != tf or (pd.Timestamp(t.meta["touched_at"]) - pd.Timestamp(t.meta["poi_formed"]))
               / pd.Timedelta(hours=1) <= 0.5 for t in strict.trades)
    freed = run(max_touch_age_hours=0.5, max_touch_age_by_tf={T.parse(tf): 0})
    assert any(t.meta["poi_tf"] == tf and (pd.Timestamp(t.meta["touched_at"]) - pd.Timestamp(t.meta["poi_formed"]))
               / pd.Timedelta(hours=1) > 0.5 for t in freed.trades)


def test_combo_risk_multiplier_stakes_the_trades_of_that_bias_combination(hk_data):
    """``risk.combo_risk_multiplier``: the trades the bias allowed through the named combination risk that multiple, the
    others the profile's stake; which trades are taken does not change."""
    def run(mult):
        s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
        s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
        s.risk.combo_risk_multiplier = mult
        return Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    base = run({})
    combos = [t.meta["bias_combo"] for t in base.trades]
    assert base.trades and all(combos)
    named = max(set(combos), key=combos.count)
    half = run({named: 0.5})
    assert [pd.Timestamp(t.opened_at) for t in half.trades] == [pd.Timestamp(t.opened_at) for t in base.trades]
    for b, h in zip(base.trades, half.trades):
        ratio = h.meta["risk_budget"] / b.meta["risk_budget"]
        assert ratio == pytest.approx(0.5 if b.meta["bias_combo"] == named else 1.0, rel=0.02)


def test_confirmation_risk_multiplier_stakes_the_trades_of_that_confirmation_type(hk_data):
    """``risk.confirmation_risk_multiplier``: the trades entered on the named confirmation type risk that multiple, the
    others the profile's stake; which trades are taken does not change."""
    def run(mult):
        s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
        s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
        s.risk.confirmation_risk_multiplier = mult
        return Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    base = run({})
    kinds = [t.meta["confirmation"] for t in base.trades]
    assert base.trades and all(kinds)
    named = max(set(kinds), key=kinds.count)
    half = run({named: 0.5})
    assert [pd.Timestamp(t.opened_at) for t in half.trades] == [pd.Timestamp(t.opened_at) for t in base.trades]
    for b, h in zip(base.trades, half.trades):
        ratio = h.meta["risk_budget"] / b.meta["risk_budget"]
        assert ratio == pytest.approx(0.5 if b.meta["confirmation"] == named else 1.0, rel=0.02)


def test_a_reversal_at_a_named_zone_timeframe_trades_against_the_bias(hk_data):
    """``confirmation.reversal_poi_timeframes`` (7 October, Max: the big zone's liquidity swept, then a balance shift): a
    visited zone of a named timeframe is also traded against the bias or without one, on its own shift timeframe
    (``reversal_confirmation_tf``), labelled REV so ``risk.combo_risk_multiplier`` sets its stake. Off by default."""
    def run(**rev):
        s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
        s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
        s.risk.combo_risk_multiplier = {"REV": 0.5}
        for key, value in rev.items():
            setattr(s.confirmation, key, value)
        return Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    base = run()
    assert base.trades and not any(t.meta["bias_combo"] == "REV" for t in base.trades)
    rev = run(reversal_poi_timeframes=(T.H_4, T.H_1), reversal_confirmation_tf={T.H_4: T.MIN_15, T.H_1: T.MIN_15})
    reversals = [t for t in rev.trades if t.meta["bias_combo"] == "REV"]
    assert reversals and all(t.meta["confirmation_tf"] == "15m" for t in reversals)
    normal = next(t for t in rev.trades if t.meta["bias_combo"] != "REV")
    for t in reversals:
        assert t.meta["risk_budget"] == pytest.approx(0.5 * normal.meta["risk_budget"], rel=0.05)


def test_max_zone_age_by_tf_limits_only_the_named_timeframes(hk_data):
    """``confirmation.max_zone_age_by_tf`` ({1H: 24} in YAML) limits the age of the zones of the timeframes it names; the zones
    of the other timeframes keep ``max_zone_age_candles`` (here off)."""
    from kronos_trader.config import Settings
    assert Settings.from_dict({"confirmation": {"max_zone_age_by_tf": {"1H": 24}}}).confirmation.max_zone_age_by_tf == {T.H_1: 24}
    s = _settings(); s.confirmation.allow_first_candle = True; s.confirmation.entry_outside_zone = True
    s.prop_firm.max_drawdown_pct = 1000.0; s.prop_firm.daily_loss_limit_pct = 1000.0
    s.confirmation.max_zone_age_by_tf = {T.H_1: 2}
    run = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert run.trades and any("1H" in r and "candles old (max 2)" in r for r in run.rejection_reasons)
    assert not any("candles old" in r and " 1H " not in f" {r}" for r in run.rejection_reasons)
    for t in run.trades:
        if t.meta["poi_tf"] == "1H":
            assert (pd.Timestamp(t.opened_at) - pd.Timestamp(t.meta["poi_formed"])) / T.H_1.delta() <= 2 + 1


def test_lower_zone_timeframes_are_mapped_only_when_the_profile_names_them(hk_data):
    """15m zones are mapped when ``confirmation.poi_timeframes`` (or ``scalp_poi_timeframes``) names the 15m; by default only
    the bias timeframes are. Before 5 October a 15m in the profile was silently ignored, so no 15m zone was ever traded."""
    from kronos_trader.core.timeframe import Timeframe as T
    now = pd.Timestamp("2024-06-03 10:00")
    views = hk_data.as_of(now, lookback=400)
    default = StrategyEngine(_settings()).analyze("09988", views, now=now)
    assert all(p.timeframe in (T.MN_1, T.W_1, T.D_1, T.H_4, T.H_1) for p in default.pois)
    s = _settings()
    s.confirmation.poi_timeframes = (T.D_1, T.H_4, T.H_1, T.MIN_15)
    s.confirmation.scalp_poi_timeframes = (T.H_4, T.H_1, T.MIN_15)
    s.confirmation.min_confirmation_tf = {**s.confirmation.min_confirmation_tf, T.MIN_15: T.MIN_5}
    lower = StrategyEngine(s).analyze("09988", views, now=now)
    assert any(p.timeframe is T.MIN_15 for p in lower.pois)


def test_mirror_bias_inverts_the_mirrored_timeframes(hk_data):
    """With ``bias.mirror_symbol`` set, the readings of ``mirror_timeframes`` come from the mirror market, inverted. Using
    the symbol's own candles as the mirror, the mirrored timeframes must read the opposite of the plain run and the
    others must be unchanged."""
    from kronos_trader.core import Bias
    from kronos_trader.core.timeframe import Timeframe as T
    from kronos_trader.strategy.engine import StrategyEngine
    now = pd.Timestamp("2024-06-03 10:00")
    plain = StrategyEngine(_settings()).analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    s = _settings(); s.bias.mirror_symbol = "09988"; s.bias.mirror_timeframes = (T.D_1,)
    engine = StrategyEngine(s); engine._mirror = hk_data; engine._mirror_tried = True
    mirrored = engine.analyze("09988", hk_data.as_of(now, lookback=400), now=now)
    assert mirrored.biases[T.D_1].bias is plain.biases[T.D_1].bias.opposite
    assert any("mirrored from 09988 (inverted)" in n for n in mirrored.biases[T.D_1].notes)
    for tf in plain.biases:
        if tf is not T.D_1:
            assert mirrored.biases[tf].bias is plain.biases[tf].bias
    assert Bias.NEUTRAL.opposite is Bias.NEUTRAL


# ---------------------------------------------------------------- telegram setup checks

def test_telegram_token_is_cleaned_and_checked():
    from kronos_trader.notify.telegram import TelegramNotifier, clean_token, masked

    assert clean_token(' "bot123456:ABCdef" ') == "123456:ABCdef"          # pasted with quotes and the URL prefix
    assert clean_token("botfather") == "botfather" and clean_token("") is None and clean_token(None) is None
    assert masked("123456:ABCdefGHIjkl") == "1234...kl (19 characters)"   # never the token itself
    n = TelegramNotifier(token=" bot123:abc ", chat_id=" 42 ")
    assert n.token == "123:abc" and n.chat_id == "42" and n.configured and not n.dry_run
    assert TelegramNotifier(token="", chat_id="").dry_run

    def fake(method, payload):
        if method == "getMe":
            return {"ok": True, "result": {"username": "dorustraderbot"}}
        if method == "getUpdates":
            return {"ok": True, "result": [{"message": {"chat": {"id": 777, "first_name": "Max", "last_name": "G"}}},
                                           {"message": {"chat": {"id": 777, "first_name": "Max"}}},
                                           {"edited_message": {"chat": {"id": -5, "title": "Kronos group"}}}]}
        return {"ok": True}

    n._call = fake
    assert n.check() == "dorustraderbot"
    assert n.chats_seen() == [{"id": 777, "name": "Max"}, {"id": -5, "name": "Kronos group"}]


def test_telegram_errors_carry_the_api_description(monkeypatch):
    from types import SimpleNamespace
    import requests
    from kronos_trader.notify.telegram import TelegramError, TelegramNotifier

    def post(url, json=None, timeout=None):
        assert "/bot123:abc/" in url
        return SimpleNamespace(status_code=404, text="nf", json=lambda: {"ok": False, "description": "Not Found"})

    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(TelegramError) as exc:
        TelegramNotifier(token="123:abc", chat_id="42").check()
    assert exc.value.status == 404 and exc.value.description == "Not Found" and exc.value.method == "getMe"


def test_adverse_move_counts_the_last_day_against_the_trade():
    from kronos_trader.core import Direction, Timeframe as TF
    from kronos_trader.strategy.engine import adverse_move_atr
    # 30 hourly candles falling 10 points each with a 10-point range: 24 candles x 10 = 240 down, ATR about 10-20
    rows = [(1000 - 10 * i, 1000 - 10 * i + 5, 1000 - 10 * i - 5, 1000 - 10 * (i + 1)) for i in range(30)]
    h1 = CandleSeries.from_records(rows, TF.H_1, start="2026-10-01 00:00", symbol="TEST")
    against_long = adverse_move_atr(h1, Direction.LONG)
    assert against_long is not None and against_long > 10                   # far against a long
    assert adverse_move_atr(h1, Direction.SHORT) == pytest.approx(-against_long)   # with a short
    short = CandleSeries.from_records(rows[:10], TF.H_1, start="2026-10-01 00:00", symbol="TEST")
    assert adverse_move_atr(short, Direction.LONG) is None                   # too little history


def test_volatility_percentile_ranks_the_last_day_against_sixty():
    from kronos_trader.core import Timeframe as TF
    from kronos_trader.strategy.engine import volatility_percentile
    quiet = [(100, 101, 99, 100)] * 200                     # 2-point ranges
    busy = [(100, 110, 90, 100)] * 6                        # 20-point ranges in the last day
    s = CandleSeries.from_records(quiet + busy, TF.H_4, start="2026-07-01 00:00", symbol="TEST")
    assert volatility_percentile(s) == pytest.approx(1.0)
    s2 = CandleSeries.from_records(busy * 20 + quiet, TF.H_4, start="2026-07-01 00:00", symbol="TEST")
    assert volatility_percentile(s2) < 0.7                   # a quiet day after busy weeks
    assert volatility_percentile(CandleSeries.from_records(quiet[:20], TF.H_4, start="2026-07-01", symbol="TEST")) is None


def test_telegram_send_never_raises():
    """A message is not worth a scan: no network, a timeout or a refusal is printed and dropped; an HTML refusal (an
    error text with a "<") goes again as plain text, a 429 waits its retry_after once."""
    from kronos_trader.notify.telegram import TelegramError, TelegramNotifier
    n = TelegramNotifier(token="123:abc", chat_id="42")
    calls = []

    def offline(method, payload):
        calls.append(payload)
        raise ConnectionError("no network")
    n._call = offline
    assert n.send("⚠️ EURUSD: live loop error") is False and len(calls) == 1

    calls.clear()

    def html_refused(method, payload):
        calls.append(payload)
        if "parse_mode" in payload:
            raise TelegramError(method, 400, "Bad Request: can't parse entities: unsupported start tag")
        return {"ok": True}
    n._call = html_refused
    assert n.send("order not accepted: <class 'RuntimeError'>") is True
    assert "parse_mode" in calls[0] and "parse_mode" not in calls[1]

    calls.clear()

    def busy_once(method, payload):
        calls.append(payload)
        if len(calls) == 1:
            raise TelegramError(method, 429, "Too Many Requests: retry after 0", retry_after=0)
        return {"ok": True}
    n._call = busy_once
    assert n.send("again") is True and len(calls) == 2

    def refused(method, payload):
        raise TelegramError(method, 403, "Forbidden: bot was blocked by the user")
    n._call = refused
    assert n.send("blocked") is False


def test_a_second_account_has_its_own_journal_and_a_tag():
    """``live --journal journal_ftmo/trades.csv --tag FTMO``: the FTMO windows keep their own journal (traded zones, lock,
    paper state) and every Telegram message says which account it is about."""
    from kronos_trader.cli import build_parser
    from kronos_trader.notify.telegram import TelegramNotifier
    args = build_parser().parse_args(["live", "--symbol", "EURUSD", "--broker", "mt5", "--journal", "journal_ftmo/trades.csv",
                                      "--tag", "FTMO", "--account-size", "10000"])
    assert args.journal == "journal_ftmo/trades.csv" and args.tag == "FTMO" and args.account_size == 10000
    n = TelegramNotifier(dry_run=True)
    n.prefix = "[FTMO] "
    n.send("EURUSD BUY filled")
    n.send_photo("charts/x.png", "EURUSD 1H touch")
    assert n.sent[0] == "[FTMO] EURUSD BUY filled" and n.sent[1].endswith("[FTMO] EURUSD 1H touch")


def test_telegram_test_reports_a_rejected_chat():
    """send() never raises, but the telegram-test check must: a wrong chat id comes back as TelegramError."""
    from kronos_trader.notify.telegram import TelegramError, TelegramNotifier
    n = TelegramNotifier(token="123:abc", chat_id="42")

    def rejected(method, payload):
        raise TelegramError(method, 400, "Bad Request: chat not found")
    n._call = rejected
    with pytest.raises(TelegramError, match="chat not found"):
        n.test()


def test_zone_age_counts_candles_of_the_zones_own_timeframe():
    """The age limit counts candles of the zone's timeframe; a monthly zone is aged in average months (the calendar
    offset of a month raised a TypeError in the diagnostic walk, which looks at every zone timeframe)."""
    import pandas as pd
    from kronos_trader.strategy.engine import zone_age_candles
    assert zone_age_candles(pd.Timestamp("2026-10-01 12:00"), pd.Timestamp("2026-10-01 00:00"), T.H_1) == 12
    assert 5.9 < zone_age_candles(pd.Timestamp("2026-10-01"), pd.Timestamp("2026-04-01"), T.MN_1) < 6.1
    assert zone_age_candles(pd.Timestamp("2026-10-15"), pd.Timestamp("2026-10-01"), T.W_1) == 2


def test_poi_in_poi_needs_a_higher_zone_of_the_same_side_that_overlaps():
    """``confirmation.poi_in_poi`` ("POI in een POI" on his trade-plan board): a zone counts only inside a zone of a higher
    timeframe in the same direction that is not invalidated."""
    import pandas as pd
    from kronos_trader.config import Settings
    from kronos_trader.core.types import POI, POIStatus
    from kronos_trader.strategy.engine import _parent_zone
    assert Settings.from_dict({"confirmation": {"poi_in_poi": True}}).confirmation.poi_in_poi is True

    def zone(tf, side, low, high, status=POIStatus.FRESH):
        return POI(tf, side, low, high, None, None, 0, pd.Timestamp("2026-10-01"), status=status)

    h1 = zone(T.H_1, Bias.BULLISH, 1.1600, 1.1620)
    assert _parent_zone(h1, [h1]) is None
    daily = zone(T.D_1, Bias.BULLISH, 1.1500, 1.1610)
    assert _parent_zone(h1, [h1, daily]) is daily
    assert _parent_zone(h1, [zone(T.D_1, Bias.BEARISH, 1.1500, 1.1610)]) is None                    # the other side
    assert _parent_zone(h1, [zone(T.D_1, Bias.BULLISH, 1.1630, 1.1700)]) is None                    # no overlap
    assert _parent_zone(h1, [zone(T.D_1, Bias.BULLISH, 1.1500, 1.1610, POIStatus.INVALIDATED)]) is None
    assert _parent_zone(daily, [daily, h1]) is None                                                 # a lower zone is no parent
