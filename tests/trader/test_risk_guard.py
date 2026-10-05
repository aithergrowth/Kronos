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


def test_two_open_trades_on_the_account_but_one_per_market():
    guard = RiskGuard(PropFirmParams(max_open_trades=2, max_open_per_symbol=1), 100_000)
    broker = PaperBroker(Settings(), use_spread=False)
    ts = pd.Timestamp("2024-01-03 10:00")
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1000, ts=ts)
    ok, reason = guard.can_open(broker, ts, "EURUSD")
    assert not ok and "in EURUSD" in reason                      # a second EURUSD trade waits
    assert guard.can_open(broker, ts, "XAUUSD") == (True, "ok")   # another market may open
    broker.place_market_order("XAUUSD", Direction.SHORT, 0.1, 2010.0, 1980.0, 1000.0, 10.0, 4.0, price=2000.0, ts=ts)
    ok, reason = guard.can_open(broker, ts, "BTCUSD")
    assert not ok and "per account" in reason                    # two open on the account: the third waits


class Account:
    """Balance-only account for the guard: no open trades, equity = balance."""

    def __init__(self, balance):
        self.bal = float(balance)

    def equity(self):
        return self.bal

    def balance(self):
        return self.bal

    def open_positions(self, symbol=None):
        return []


def test_monthly_loss_stop_waits_for_the_next_month():
    guard = RiskGuard(PropFirmParams(monthly_loss_limit_pct=4.5), 10_000)
    acct = Account(10_000)
    guard.update(pd.Timestamp("2026-10-01 08:00"), acct.equity(), acct.balance())
    acct.bal = 9_600                                                   # -4 % closed this month
    assert guard.can_open(acct, pd.Timestamp("2026-10-06 09:00"), "EURUSD") == (True, "ok")
    acct.bal = 9_540                                                   # -4.6 %
    ok, reason = guard.can_open(acct, pd.Timestamp("2026-10-07 09:00"), "EURUSD")
    assert not ok and "monthly loss" in reason and "next month" in reason
    assert guard.can_open(acct, pd.Timestamp("2026-11-02 09:00"), "EURUSD") == (True, "ok")


def test_a_restart_keeps_the_days_and_the_months_losses():
    guard = RiskGuard(PropFirmParams(monthly_loss_limit_pct=4.5), 10_000)
    asked = []

    def realized(since):
        asked.append(since)
        return -400.0 if since < pd.Timestamp("2026-10-05") else -150.0   # this month -400, today -150

    guard.realized_since = realized
    guard.update(pd.Timestamp("2026-10-07 10:00"), 9_600, 9_600)
    assert guard.day_start_balance == pytest.approx(9_750) and guard.month_start_balance == pytest.approx(10_000)
    assert guard.daily_loss_pct(9_600) == pytest.approx(1.5) and guard.monthly_loss_pct() == pytest.approx(4.0)
    assert pd.Timestamp("2026-10-06 22:00") in asked and pd.Timestamp("2026-09-30 22:00") in asked   # Prague midnights in UTC
