"""The fourth fix check of 15 October (scratchpad fixcheck4/), each finding fixed and pinned here: a terminal re-attached
inside one check holds the entry a scan, a window's own resting limit survives a terminal that lists nothing yet, a limit
fill under another ticket is no "found" position, the account a window took on is said also after a down scan, a demo
terminal that logs in late is waited for, and a stale saved ForexFactory week never re-blocks a week read fresh."""
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Direction, Timeframe as T
from kronos_trader.execution.mt5 import MT5Broker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from tests.trader.test_live import FakeEngine, _runner, setup  # noqa: F401  (the setup fixture lives there)
from tests.trader.test_mt5 import NOW, LimitMT5, server_seconds


class Restarted(LimitMT5):
    """``broken``: the terminal process restarted (account_info None) until initialize() attaches again; ``hidden``: the
    re-attached terminal has not received the account's positions and orders yet."""

    def __init__(self):
        super().__init__()
        self.broken = self.hidden = False
        self.inits = 0

    def initialize(self, **kw):
        self.inits += 1
        if self.broken:
            self.broken, self.hidden = False, True
        return super().initialize(**kw)

    def account_info(self):
        return None if self.broken else super().account_info()

    def positions_get(self, symbol=None):
        return [] if self.hidden else super().positions_get(symbol)

    def orders_get(self, symbol=None):
        return [] if self.hidden else super().orders_get(symbol)


class From(FakeEngine):
    """No signal before the k-th analysis, the same valid setup from it on."""

    def __init__(self, setup, k):
        super().__init__(setup)
        self.k, self.n = k, 0

    def analyze(self, *a, **kw):
        self.n += 1
        self.calls = 0 if self.n >= self.k else 1
        return super().analyze(*a, **kw)


def _window(api, tmp_path, engine, limit=False):
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    if limit:
        settings.risk.limit_entry_fraction, settings.risk.limit_entry_minutes = 0.25, 240
    broker = MT5Broker(settings, api=api, clock=lambda: NOW)
    broker.retry_seconds = 0.0
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=engine, dry_run=False,
                        require_approval=False, clock=lambda: NOW)
    return runner, broker, notifier


def _held_position(api):
    api.positions.append(NS(ticket=901, identifier=901, symbol="EURUSD", type=0, volume=0.2, price_open=1.1, sl=1.095,
                            tp=1.11, time=server_seconds(NOW - pd.Timedelta(hours=3)), magic=20260930,
                            comment="1HPOI BS", profit=0.0, swap=0.0))


# ---------------------------------------------------------------- 1. a re-attach inside one check holds the entry
def test_a_terminal_reattached_inside_one_check_holds_the_entry_a_scan(setup, tmp_path):
    """entries_and_limits [0], critical (pre-existing): a terminal restart that connection_ok re-attaches within the same
    call never showed the link down, so the wait was not re-armed and an empty first listing let a second position in."""
    api = Restarted()
    _held_position(api)
    runner, broker, notifier = _window(api, tmp_path, From(setup, 4))
    runner._listings = 0                                # as run_forever starts it
    for i in range(1, 6):
        api.broken = api.broken or i == 4               # the terminal restarted between scans 3 and 4
        if i == 5:
            api.hidden = False                          # its positions are in at the next scan
        assert runner.connection_ok()                   # re-attached inside the check at scan 4: never seen down
        runner.step()
    assert api.inits == 2 and broker.attaches == 1
    assert [p.ticket for p in api.positions] == [901]   # no second position
    assert not [m for m in notifier.sent if m.startswith("💸")]
    assert [m for m in notifier.sent if m.startswith("⛔") and "open trade(s)" in m]


# ---------------------------------------------------------------- 2. the window's own limit survives an unsynced terminal
def test_a_resting_limit_is_neither_gone_nor_cancelled_while_a_restarted_terminal_lists_nothing(setup, tmp_path):
    """entries_and_limits [1], major: the first scan after a restart read the window's own limit as "gone" (no order, no
    position, no history) and the next scan cancelled it as a stray; the trade was lost."""
    api = Restarted()
    runner, broker, notifier = _window(api, tmp_path, FakeEngine(setup), limit=True)
    runner.step(NOW)                                    # a scan run by hand: the limit is placed
    assert len(api.orders) == 1 and len(runner.limits) == 1
    oid = next(iter(runner.limits))
    runner._listings = 2                                # running, synced
    api.broken = True                                   # the terminal restarts; it lists nothing at the first scan
    assert runner.connection_ok()
    runner.step(NOW)
    api.hidden = False
    assert runner.connection_ok()
    runner.step(NOW)
    assert [str(o.ticket) for o in api.orders] == [oid] and oid in runner.limits
    assert not [m for m in notifier.sent if m.startswith("⌛") or m.startswith("🚫")]


# ---------------------------------------------------------------- 3. a limit fill under another ticket
def test_a_limit_fill_with_another_position_ticket_is_no_found_position(setup, tmp_path):
    """entries_and_limits [3]: the server can give the position another ticket than its order (the identifier stays);
    manage_positions saw it before manage_limits and raised the "found" alarm on the window's own fill."""
    api = LimitMT5()
    runner, broker, notifier = _window(api, tmp_path, FakeEngine(setup), limit=True)
    runner.step(NOW)
    oid = next(iter(runner.limits))
    api.fill(int(oid))
    api.positions[-1].ticket = 9001                     # identifier stays the order's ticket
    runner.step(NOW)
    runner.step(NOW)
    assert not [m for m in notifier.sent if "without this window's record" in m]
    assert [m for m in notifier.sent if "filled (limit)" in m]


# ---------------------------------------------------------------- 4. the account taken on, said after a down scan too
def test_the_account_taken_on_in_a_down_scan_is_said_at_the_next_good_one(setup):
    """connect [3]: the account was taken on in a check that reported the trade server down; the message waited for an
    ok check in the same call, and was lost."""
    from tests.trader.test_review_fixes_15oct import Starting

    class Offline(Starting):
        offline = False

        def terminal_info(self):
            return NS(connected=not self.offline, trade_allowed=True)
    late = Offline(on=0)
    broker = MT5Broker(Settings(), api=late, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    broker.connect()
    runner, notifier = _runner(setup, broker)
    late.on, late.offline = 55556666, True              # its account shows while the trade server is away
    assert not runner.connection_ok()
    late.offline = False
    assert runner.connection_ok() and runner.connection_ok()
    said = [m for m in notifier.sent if "55556666" in m]
    assert len(said) == 1 and "dit venster handelt vanaf nu op dat account" in said[0]


# ---------------------------------------------------------------- 5. a demo terminal that logs in late is waited for
def test_a_demo_terminal_that_logs_in_after_a_minute_is_waited_for(monkeypatch):
    """connect [2]: a cold-started terminal that reached MT5_LOGIN after 75 s ended the demo window at its start."""
    from tests.trader.test_review_fixes_15oct import Starting, _broker_on
    slow = Starting(on=11112222, logs_in_after=75.0)    # MT5_LOGIN is 11112222 (_env)
    broker = _broker_on(slow, monkeypatch)
    broker.connect()
    assert broker.account_login == 11112222 and all("login" not in c for c in slow.calls)


# ---------------------------------------------------------------- 6. a stale saved ForexFactory week
def test_a_stale_saved_week_never_reblocks_a_week_read_fresh(setup, tmp_path, monkeypatch):
    """calendar_news [1]: next week's feed is missing most of the week; its saved file (this week as listed last week)
    was added every hour, so a release moved since kept blocking its old slot."""
    from kronos_trader.data import calendar as cal
    from kronos_trader.data.calendar import NewsCalendar, NewsEvent, save_events
    from kronos_trader.execution import PaperBroker
    this_week = [NewsEvent(pd.Timestamp("2026-10-12 12:30"), "USD", "CPI m/m"),
                 NewsEvent(pd.Timestamp("2026-10-16 12:30"), "USD", "Retail Sales m/m")]
    moved = NewsEvent(pd.Timestamp("2026-10-14 12:30"), "USD", "PPI m/m")          # since moved: not in the fresh week
    later = NewsEvent(pd.Timestamp("2026-10-21 12:30"), "USD", "Existing Home Sales")

    def fetch(week, *a, **kw):
        if week == "thisweek":
            return list(this_week)
        raise RuntimeError("404 Not Found")
    monkeypatch.setattr(cal, "fetch_forexfactory", fetch)
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker, journal=str(tmp_path / "j" / "trades.csv"))
    runner.engine.calendar = NewsCalendar()
    saved = save_events([moved, later], tmp_path / "j" / "forexfactory_nextweek.csv")
    old = saved.stat().st_mtime - 3 * 86400            # saved last week, when ForexFactory still listed the old slot
    import os
    os.utime(saved, (old, old))
    runner.refresh_news(NOW)
    titles = [e.title for e in runner.engine.calendar.events]
    assert "PPI m/m" not in titles                      # inside the week read fresh: stale
    assert "Existing Home Sales" in titles and "CPI m/m" in titles
