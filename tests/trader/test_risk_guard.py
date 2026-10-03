"""Prop-firm guard: the daily-loss baseline is the balance at the start of the day, in the firm's time zone."""
import pandas as pd
import pytest

from kronos_trader.config import PropFirmParams, Settings
from kronos_trader.core import Direction
from kronos_trader.execution import PaperBroker, RiskGuard


def test_overnight_loss_counts_against_the_new_day():
    guard = RiskGuard(PropFirmParams(daily_loss_limit_pct=4.0, max_open_trades=2), 100_000)
    guard.update(pd.Timestamp("2024-01-02 20:00"), 100_000, 100_000)
    guard.update(pd.Timestamp("2024-01-03 07:00"), 94_000, 100_000)     # open position fell overnight, nothing closed
    assert guard.daily_loss_pct(94_000) == pytest.approx(6.0)
    assert guard.first_breach is not None and "daily loss" in guard.first_breach[1]
    broker = PaperBroker(Settings(), use_spread=False)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0000, 1.2000, 1000.0, 0.01, 4.0, price=1.1000, ts=pd.Timestamp("2024-01-02 20:00"))
    broker.set_price("EURUSD", 1.0400)                                    # 600 pips against 1 lot: equity 94,000
    assert broker.equity() == pytest.approx(94_000)
    ok, reason = guard.can_open(broker, pd.Timestamp("2024-01-03 07:05"))
    assert not ok and "daily loss" in reason


def test_day_boundary_follows_the_firm_time_zone():
    guard = RiskGuard(PropFirmParams(), 100_000)
    guard.update(pd.Timestamp("2024-01-02 22:30"), 100_000, 100_000)      # 23:30 Prague, still 2 January
    guard.update(pd.Timestamp("2024-01-02 22:45"), 98_000, 98_000)
    assert guard.day == pd.Timestamp("2024-01-02") and guard.day_start_balance == 100_000
    guard.update(pd.Timestamp("2024-01-02 23:30"), 98_000, 98_000)        # 00:30 Prague: 3 January starts from 98,000
    assert guard.day == pd.Timestamp("2024-01-03") and guard.day_start_balance == 98_000
    assert guard.daily_loss_pct(98_000) == 0.0


def test_drawdown_basis_initial_is_a_static_floor():
    guard = RiskGuard(PropFirmParams(drawdown_basis="initial", max_drawdown_pct=10.0), 100_000)
    guard.update(pd.Timestamp("2024-01-02 10:00"), 120_000, 120_000)
    assert guard.drawdown_pct(109_000) == pytest.approx(-9.0)        # above the start: no drawdown against the floor
    peak = RiskGuard(PropFirmParams(drawdown_basis="peak", max_drawdown_pct=10.0), 100_000)
    peak.update(pd.Timestamp("2024-01-02 10:00"), 120_000, 120_000)
    assert peak.drawdown_pct(109_000) == pytest.approx(11.0)
