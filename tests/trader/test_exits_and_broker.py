import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Candle, Direction, Timeframe
from kronos_trader.execution import PaperBroker, RiskGuard
from kronos_trader.strategy import breakeven_reached, breakeven_trigger_r, r_multiple

T = Timeframe


def test_breakeven_rules():
    assert breakeven_trigger_r(T.MN_1) == 2.0 and breakeven_trigger_r(T.W_1) == 2.0
    for tf in (T.D_1, T.H_4, T.H_1):
        assert breakeven_trigger_r(tf) == 4.0
    assert r_multiple(Direction.LONG, 1.10, 0.005, 1.12) == pytest.approx(4.0)
    assert r_multiple(Direction.SHORT, 1.10, 0.005, 1.12) == pytest.approx(-4.0)
    assert breakeven_reached(Direction.LONG, 1.10, 0.005, 1.1201, 4.0)
    assert not breakeven_reached(Direction.LONG, 1.10, 0.005, 1.1199, 4.0)


def _candle(o, h, l, c, ts="2024-01-02 10:00"):
    return Candle(0, pd.Timestamp(ts), o, h, l, c)


def _long(broker):
    return broker.place_market_order("EURUSD", Direction.LONG, 1.96, 1.0950, 1.1200, 1000.0, 0.0051, 4.0,
                                     price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))


def test_paper_broker_fills_with_spread_and_hits_take_profit():
    broker = PaperBroker(Settings())
    pos = _long(broker)
    assert pos.entry == pytest.approx(1.10005)  # 1 pip spread -> half a pip worse
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.1250, 1.0990, 1.1240))
    assert len(closed) == 1 and closed[0].reason == "take_profit"
    assert closed[0].pnl == pytest.approx((1.1200 - 1.10005) / 0.0001 * 10 * 1.96)
    assert broker.balance() == pytest.approx(100_000 + closed[0].pnl)


def test_paper_broker_stop_wins_when_both_hit():
    broker = PaperBroker(Settings())
    _long(broker)
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.1300, 1.0900, 1.1000))
    assert closed[0].reason == "stop" and closed[0].exit == 1.0950 and closed[0].r == pytest.approx(-1.0, abs=0.02)


def test_paper_broker_moves_to_breakeven_after_4r():
    broker = PaperBroker(Settings())
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0950, 1.1300, 1000.0, 0.0051, 4.0,
                                    price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))
    assert broker.on_candle("EURUSD", _candle(1.1000, 1.1210, 1.0999, 1.1205)) == []
    assert pos.breakeven_done and pos.stop == pytest.approx(pos.entry)
    closed = broker.on_candle("EURUSD", _candle(1.1205, 1.1210, 1.0999, 1.1000, "2024-01-02 11:00"))
    assert closed[0].reason == "breakeven" and closed[0].pnl == pytest.approx(0.0)


def test_risk_guard_limits():
    settings = Settings()
    broker = PaperBroker(settings)
    guard = RiskGuard(settings.prop_firm, settings.account_size)
    ts = pd.Timestamp("2024-01-02 09:00")
    assert guard.can_open(broker, ts)[0]
    _long(broker)
    ok, reason = guard.can_open(broker, ts)
    assert not ok and "open trade" in reason
    broker.close_position(broker.open_positions()[0].id, "manual", 1.1000, ts)
    broker._balance = 95_500.0
    ok, reason = guard.can_open(broker, ts)
    assert not ok and "daily loss" in reason
    broker._balance = 91_500.0
    ok, reason = guard.can_open(broker, ts + pd.Timedelta(1, unit="D"))
    assert not ok and "drawdown" in reason


@pytest.mark.parametrize("raised_during_reconcile", [False, True])
def test_broker_execution_halt_blocks_other_symbols_without_positions(monkeypatch, raised_during_reconcile):
    settings = Settings()
    settings.prop_firm.max_open_trades = 5
    broker = PaperBroker(settings)
    reason = "EURUSD partial fill requires reconciliation"
    broker.execution_halt_reason = None if raised_during_reconcile else reason

    def reconcile():
        broker.execution_halt_reason = reason
        return []

    if raised_during_reconcile:
        monkeypatch.setattr(broker, "open_positions", reconcile)
    guard = RiskGuard(settings.prop_firm, settings.account_size)
    ok, detail = guard.can_open(broker, pd.Timestamp("2026-10-01 09:00"), "USDJPY")
    assert not ok and reason in detail
