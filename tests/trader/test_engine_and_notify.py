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
