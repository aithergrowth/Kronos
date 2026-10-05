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


def test_worst_case_of_open_trades_and_the_new_one_stays_inside_the_limits():
    """Before a new trade the guard adds what every open trade loses at its stop and the new trade's risk to the closed
    loss: a day already 1.5 % down with one 1.5 % trade open refuses a third 1.5 % (4.5 % >= 4 %), a stop at the entry
    risks nothing, and the static floor is checked the same way."""
    p = PropFirmParams(daily_loss_limit_pct=4.0, max_drawdown_pct=8.0, drawdown_basis="initial", max_open_trades=3)
    guard = RiskGuard(p, 100_000)
    broker = PaperBroker(Settings(), use_spread=False)
    ts = pd.Timestamp("2024-01-03 10:00")
    guard.update(ts, 100_000, 100_000)
    broker._balance = 98_500.0                                     # a 1.5 % loss closed today
    guard.update(ts, 98_500, 98_500)
    assert guard.can_open(broker, ts, "EURUSD", new_risk=1_500.0) == (True, "ok")             # 1.5 + 1.5 = 3 %
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0850, 1.1300, 1500.0, 0.015, 4.0, price=1.1000, ts=ts)
    assert RiskGuard.open_risk(broker) == pytest.approx(1_500.0)
    ok, reason = guard.can_open(broker, ts, "XAUUSD", new_risk=1_500.0)                       # 1.5 + 1.5 + 1.5 = 4.5 %
    assert not ok and "daily loss would reach 4.50%" in reason
    assert guard.can_open(broker, ts, "XAUUSD", new_risk=900.0) == (True, "ok")                # a smaller stake fits
    pos = broker.open_positions("EURUSD")[0]
    broker.modify_stop(pos.id, pos.entry)                                                      # at break-even: no risk
    assert RiskGuard.open_risk(broker) == 0.0
    assert guard.can_open(broker, ts, "XAUUSD", new_risk=1_500.0) == (True, "ok")
    floor = RiskGuard(PropFirmParams(daily_loss_limit_pct=50.0, max_drawdown_pct=8.0, drawdown_basis="initial"), 100_000)
    low = Account(93_000)
    ok, reason = floor.can_open(low, ts, "EURUSD", new_risk=1_000.0)                           # 7 + 1 = 8 % from the start
    assert not ok and "drawdown would reach 8.00%" in reason


def test_a_day_change_takes_the_balance_at_midnight_not_at_the_first_look():
    """The laptop slept through a stop hit after midnight: with the broker's closed P&L the new day's baseline is the
    balance at midnight (Prague), so that loss counts against the new day."""
    guard = RiskGuard(PropFirmParams(daily_loss_limit_pct=4.0), 100_000)
    guard.update(pd.Timestamp("2024-01-02 20:00"), 100_000, 100_000)
    guard.realized_since = lambda since: -1_500.0 if since <= pd.Timestamp("2024-01-03 05:00") else 0.0
    guard.update(pd.Timestamp("2024-01-03 06:00"), 98_500, 98_500)     # first look of the day, after the night's stop-out
    assert guard.day_start_balance == pytest.approx(100_000) and guard.daily_loss_pct(98_500) == pytest.approx(1.5)


def test_weekend_close_blocks_new_trades_until_the_sunday_open():
    """``prop_firm.weekend_close`` (FTMO Account, Standard type: flat before the weekend): no new trade from Friday 16:45
    New York until the market reopens Sunday 17:00 New York, in summer and winter time."""
    from kronos_trader.strategy.exits import weekend_cutoff_after
    guard = RiskGuard(PropFirmParams(weekend_close="16:45", max_open_trades=2), 100_000)
    broker = PaperBroker(Settings(), use_spread=False)
    for ts, allowed in (("2026-10-02 12:00", True), ("2026-10-02 20:44", True), ("2026-10-02 20:46", False),
                        ("2026-10-03 12:00", False), ("2026-10-04 20:59", False), ("2026-10-04 21:01", True),
                        ("2026-11-06 21:00", True), ("2026-11-06 21:46", False)):        # 6 November: New York on EST
        ok, reason = guard.can_open(broker, pd.Timestamp(ts))
        assert ok is allowed, ts
        assert allowed or "weekend" in reason
    assert weekend_cutoff_after(pd.Timestamp("2026-03-07 12:00"), "16:45") == pd.Timestamp("2026-03-13 20:45")   # past the switch
    assert weekend_cutoff_after(pd.Timestamp("2026-10-09 20:45"), "16:45") == pd.Timestamp("2026-10-16 20:45")
    assert RiskGuard(PropFirmParams(), 100_000).can_open(broker, pd.Timestamp("2026-10-03 12:00"))[0]           # off by default
