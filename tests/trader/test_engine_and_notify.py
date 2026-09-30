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
    params = SessionParams()
    assert in_session(pd.Timestamp("2026-10-01 07:30"), params) == (True, "Thu 09:30")     # CEST = UTC+2
    assert in_session(pd.Timestamp("2026-10-01 09:30"), params)[0] is False                # 11:30 Amsterdam: between windows
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
