"""8 October review: the live path fails closed where it used to fail open."""
import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Timeframe
from kronos_trader.execution import PaperBroker
from kronos_trader.live import AccountLock, LiveRunner
from kronos_trader.notify import TelegramNotifier

from test_live import NOW, FakeEngine, setup  # noqa: F401  (the fixture)

T = Timeframe


def _runner(setup, tmp_path):
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    settings.live.charts_dir = str(tmp_path / "charts")
    settings.live.briefing_time = None
    broker = PaperBroker(settings)
    broker.set_price("EURUSD", 1.1)
    notifier = TelegramNotifier(dry_run=True)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    return runner, notifier, broker


def test_an_unknown_planned_risk_refuses_the_entry_instead_of_counting_it_as_zero(setup, tmp_path):
    """``planned_risk`` used to return 0.0 when the terminal did not answer, so the guard's worst case ran without the new
    trade's risk while the order a moment later went through."""
    runner, notifier, broker = _runner(setup, tmp_path)
    assert runner.planned_risk(setup) > 0

    def broken():
        raise RuntimeError("IPC timeout")

    runner.broker.balance = broken
    assert runner.planned_risk(setup) is None
    runner.step(NOW)
    assert broker.open_positions() == []
    assert any(LiveRunner.NO_PLANNED_RISK in m for m in notifier.sent)


def test_the_account_lock_counts_a_file_stale_after_five_minutes(tmp_path):
    """A slow terminal's own entry (a dozen calls and a wait for the position) could outlive the old 60 s, after which
    a second window broke the lock and both passed the account's checks."""
    lock = AccountLock(tmp_path / "account.lock")
    assert lock.stale == 300.0
    with lock:
        assert lock.held
        other = AccountLock(tmp_path / "account.lock", timeout=0.2)
        with other:
            assert not other.held                        # held by the first: the second defers


def test_telegram_errors_never_carry_the_bot_token(monkeypatch):
    notifier = TelegramNotifier(token="123456:SECRET-TOKEN", chat_id="1")
    assert notifier.configured

    class Boom(Exception):
        pass

    def post(url, **kwargs):
        raise Boom(f"cannot reach {url}")

    import requests
    monkeypatch.setattr(requests, "post", post)
    with pytest.raises(RuntimeError) as err:
        notifier._call("getMe", {})
    assert "SECRET-TOKEN" not in str(err.value) and "<token>" in str(err.value)
    assert notifier.send("hallo") is False               # swallowed, as before


def test_a_position_without_a_stop_is_said_at_once_and_blocks_new_entries(setup, tmp_path):
    """The guard counts a stopless position as no risk (it cannot price its loss); the window now says so on Telegram
    the moment it sees one and refuses every new entry until the position has a stop."""
    from kronos_trader.core import Direction
    from kronos_trader.execution.base import Position
    runner, notifier, broker = _runner(setup, tmp_path)
    naked = Position(id="777", symbol="EURUSD", direction=Direction.LONG, lots=0.1, entry=1.1, stop=0.0, take_profit=1.12,
                     opened_at=NOW - pd.Timedelta(hours=1), risk_amount=0.0, risk_distance=0.0, breakeven_r=4.0, initial_stop=0.0)
    broker.open_positions = lambda symbol=None: [naked]
    runner.step(NOW)
    alarms = [m for m in notifier.sent if "NO STOP" in m]
    assert len(alarms) == 1 and "777" in alarms[0]
    assert any("without a stop on the server: no new trade" in m for m in notifier.sent)
    runner.step(NOW + pd.Timedelta(minutes=5))
    assert len([m for m in notifier.sent if "NO STOP" in m]) == 1          # said once per position
