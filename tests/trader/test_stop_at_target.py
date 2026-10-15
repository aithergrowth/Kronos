"""prop_firm.stop_at_target (15 October, the pre-mortem's second risk): at the phase's target no new trade once the
minimum trading days are logged, the finish stake while they are not; off by default."""
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Direction
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from tests.trader.test_live import FakeEngine, NOW, setup  # noqa: F401  (the setup fixture lives there)


def _runner(setup, tmp_path, balance, days, stop=True, target=10.0):
    s = Settings()
    s.account_size = 10_000.0
    s.risk.risk_pct, s.risk.target_pct = 1.5, target
    s.prop_firm.stop_at_target = stop
    s.live.journal_path = str(tmp_path / "trades.csv")
    broker = PaperBroker(s)
    broker.set_price("EURUSD", 1.1)
    broker._balance = balance
    broker.trading_days = lambda tz="Europe/Prague": days
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(s, "EURUSD", lambda: {}, broker=broker, notifier=notifier,
                        engine=FakeEngine(setup, signal_on_first_call=False), dry_run=False, clock=lambda: NOW)
    return runner, notifier


def test_off_by_default_and_under_the_target(setup, tmp_path):
    assert Settings().prop_firm.stop_at_target is False
    runner, _ = _runner(setup, tmp_path, 11_500.0, 6, stop=False)
    assert runner.target_state() is None and runner.stake_params(setup).risk_pct == pytest.approx(1.5)
    runner, _ = _runner(setup, tmp_path, 10_900.0, 6)                              # +9 %: not yet
    assert runner.target_state() is None
    runner, _ = _runner(setup, tmp_path, 11_500.0, 6, target=0.0)                  # no target known: off
    assert runner.target_state() is None


def test_at_the_target_with_the_days_done_no_new_trade(setup, tmp_path):
    runner, _ = _runner(setup, tmp_path, 11_020.0, 4)
    assert runner.target_state() == ("done", 4, 11_020.0)
    ok, reason = runner._can_open(setup, NOW)
    assert not ok and "target +10 % stands with 4 trading day(s)" in reason


def test_at_the_target_with_days_missing_the_finish_stake(setup, tmp_path):
    runner, _ = _runner(setup, tmp_path, 11_020.0, 2)
    assert runner.target_state()[0] == "finish"
    assert runner.stake_params(setup).risk_pct == pytest.approx(0.1)
    assert runner.planned_risk(setup) == pytest.approx(11_020.0 * 0.001)
    assert "the phase's target stands, 2 of 4 trading days" in runner.stake_note(runner.stake_params(setup))
    runner, _ = _runner(setup, tmp_path, 11_020.0, None)                           # unknown days count as missing
    assert runner.target_state()[0] == "finish"


def test_the_notice_goes_out_once_a_day_for_the_account(setup, tmp_path):
    a, na = _runner(setup, tmp_path, 11_020.0, 5)
    b, nb = _runner(setup, tmp_path, 11_020.0, 5)                                   # a second window of the same account
    a.announce_target(NOW)
    a.announce_target(NOW + pd.Timedelta(minutes=5))
    b.announce_target(NOW + pd.Timedelta(minutes=6))
    sent = [m for m in na.sent + nb.sent if m.startswith("🏁")]
    assert len(sent) == 1 and "volgende fase" in sent[0]
    a.announce_target(NOW + pd.Timedelta(days=1))                                   # the next day: again
    assert sum(m.startswith("🏁") for m in na.sent) == 2


def test_the_paper_broker_counts_days_with_a_trade_opened(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    for ts in ("2026-10-13 21:30", "2026-10-13 22:30", "2026-10-15 09:00"):      # 22:30 UTC is the 14th in Prague
        broker.place_market_order("EURUSD", Direction.LONG, 0.1, 1.09, 1.12, 100.0, 0.01, 4.0, price=1.1, ts=pd.Timestamp(ts))
    assert broker.trading_days("Europe/Prague") == 3


def test_mt5_counts_entry_deals_on_the_prague_calendar():
    from kronos_trader.execution.mt5 import MT5Broker
    from tests.trader.test_mt5 import FakeMT5, server_seconds
    api = FakeMT5()
    mk = lambda t, entry, typ=0: SimpleNamespace(ticket=1, position_id=1, time=server_seconds(pd.Timestamp(t)), entry=entry, type=typ,
                                                 reason=0, price=1.1, profit=0.0, commission=0.0, swap=0.0, fee=0.0, volume=0.1,
                                                 symbol="EURUSD", magic=0, comment="")
    api.deals = [mk("2026-10-13 10:00", api.DEAL_ENTRY_IN), mk("2026-10-13 15:00", api.DEAL_ENTRY_OUT),
                 mk("2026-10-14 08:00", api.DEAL_ENTRY_IN), mk("2026-10-14 09:00", api.DEAL_ENTRY_IN, typ=2)]   # type 2: a balance deal
    b = MT5Broker(Settings(), api=api, clock=lambda: NOW)
    assert b.trading_days("Europe/Prague") == 2


def test_the_flag_needs_a_target_and_stays_off_without_one(capsys):
    from kronos_trader.cli import live_settings
    from pathlib import Path
    profile = str(Path(__file__).resolve().parents[2] / "config" / "dorus_live.yaml")
    base = dict(config=profile, symbol="EURUSD", stop_at_target=True)
    s, _ = live_settings(SimpleNamespace(**base, target_pct=None))
    assert s.prop_firm.stop_at_target is False and "stays off" in capsys.readouterr().out
    s, _ = live_settings(SimpleNamespace(**base, target_pct=10.0))
    assert s.prop_firm.stop_at_target is True and s.risk.target_pct == 10.0


def test_a_resting_full_stake_limit_is_cancelled_once_the_target_stands(setup, tmp_path):
    runner, notifier = _runner(setup, tmp_path, 11_020.0, 2)                       # finish: limits over the finish stake go
    broker = runner.broker
    big = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0949, 1.1200, 150.0, 0.0041, 4.0,
                                   expires_at=NOW + pd.Timedelta(hours=4))
    small = broker.place_limit_order("EURUSD", Direction.LONG, 0.02, 1.0990, 1.0949, 1.1200, 10.0, 0.0041, 4.0,
                                     expires_at=NOW + pd.Timedelta(hours=4))
    runner._limits_checked = True
    for o in (big, small):
        runner.limits[o.id] = {"sid": "x", "direction": "LONG", "price": o.price, "stop": o.stop, "take_profit": o.take_profit,
                               "lots": o.lots, "risk_amount": o.risk_amount, "placed_at": NOW,
                               "expires_at": NOW + pd.Timedelta(hours=4)}
    runner.manage_limits(NOW)
    assert big.id not in runner.limits and small.id in runner.limits
    assert any("cancelled - the phase's target stands" in m for m in notifier.sent)


def test_a_terminal_that_stops_answering_keeps_the_last_day_count(setup, tmp_path):
    runner, _ = _runner(setup, tmp_path, 11_020.0, 5)
    assert runner.target_state()[0] == "done"
    runner.broker.trading_days = lambda tz="Europe/Prague": None
    runner._scan_id += 1                                                            # the next scan asks again
    assert runner.target_state() == ("done", 5, 11_020.0)


def test_once_done_a_new_setup_is_journaled_not_announced(setup, tmp_path):
    runner, notifier = _runner(setup, tmp_path, 11_020.0, 5)
    runner.engine = FakeEngine(setup)                                               # a signal on the first scan
    runner.require_approval = False
    runner.step(NOW)
    assert runner.broker.open_positions() == []
    assert not any("BUY" in m or "not executed" in m for m in notifier.sent)
    rows = pd.read_csv(tmp_path / "trades.csv")
    assert (rows["event"] == "not_executed").sum() == 1 and "target stands" in rows.loc[rows["event"] == "not_executed", "reason"].iloc[0]
