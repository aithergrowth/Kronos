"""The third fix check of 15 October (scratchpad fixcheck3/), each finding fixed and pinned here: an entry waits for a
second listing of the positions after a (re)start, a restored position never raises the "found" alarm, a fill the history
shows before its position is not "closed again", a found position counts its R, the day report reads a loaded history
without a trade in its range, a window says in a line why the terminal is refused, and which account it took on."""
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from kronos_trader import cli
from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Direction, Timeframe as T
from kronos_trader.execution.mt5 import MT5Broker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from tests.trader.test_live import FakeEngine, _runner, setup  # noqa: F401  (the setup fixture lives there)
from tests.trader.test_mt5 import NOW, LimitMT5, server_seconds


class Syncing(LimitMT5):
    """``hidden``: positions_get lists nothing (the terminal has not received the account's positions yet);
    ``fill_later``: a filled order's position is listed only after that many positions_get calls (its history says FILLED)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.hidden, self.waiting = False, []

    def positions_get(self, symbol=None):
        for item in list(self.waiting):
            item[0] -= 1
            if item[0] <= 0:
                self.waiting.remove(item)
                self.positions.append(item[1])
        return [] if self.hidden else super().positions_get(symbol)

    def fill_later(self, ticket, lag):
        self.fill(ticket)
        p = self.positions.pop()
        self.waiting.append([lag, p])


class EveryScan(FakeEngine):
    """The same valid signal at every scan (its confirmation candle is still the newest)."""

    def analyze(self, *args, **kwargs):
        self.calls = 0
        return super().analyze(*args, **kwargs)


def _window(api, journal, engine=None):
    settings = Settings()
    settings.live.journal_path = str(journal / "trades.csv")
    broker = MT5Broker(settings, api=api, clock=lambda: NOW)
    broker.retry_seconds = 0.0
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier,
                        engine=engine or FakeEngine(None, signal_on_first_call=False),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    return runner, notifier


def _held(api, hours=3):
    """A position of this program, opened ``hours`` before the window started (a restart finds it on the server)."""
    api.positions.append(NS(ticket=901, identifier=901, symbol="EURUSD", type=0, volume=0.2, price_open=1.1, sl=1.095,
                            tp=1.11, time=server_seconds(NOW - pd.Timedelta(hours=hours)), magic=20260930,
                            comment="1HPOI BS", profit=0.0, swap=0.0))


# ---------------------------------------------------------------- 1. an entry waits for a second listing
def test_an_entry_after_a_start_waits_for_a_second_listing_of_the_positions(setup, tmp_path):
    """live_changes [0]: a terminal that is not synced yet lists no positions; read so, a second position went through the
    per-market cap and the guard counted no open risk. The setup waits a scan (not marked seen) and the cap then holds."""
    api = Syncing()
    _held(api)
    runner, notifier = _window(api, tmp_path / "journal", engine=EveryScan(setup))
    runner._listings = 0                                # as run_forever starts it
    api.hidden = True                                   # the restarted window's first scan: no positions yet
    runner.step(NOW)
    assert [p.ticket for p in api.positions] == [901] and runner.seen == set()
    assert not [m for m in notifier.sent if m.startswith("💸")]
    api.hidden = False
    runner.step(NOW)
    assert [p.ticket for p in api.positions] == [901]   # the cap held: no second trade
    assert [m for m in notifier.sent if m.startswith("⛔") and "max 1 open trade(s)" in m] and len(runner.seen) == 1


def test_a_reconnect_counts_the_listings_again_and_a_scan_by_hand_is_not_held(setup):
    from kronos_trader.execution import PaperBroker
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner._listings = 2
    states = iter([(False, "MT5 not reachable (terminal closed or restarting)"), (True, "ok")])
    broker.connection_ok = lambda: next(states)
    runner.connection_ok()
    runner.connection_ok()
    assert runner._listings == 0                        # the link came back: a restarted terminal is listed twice again
    runner._listings = None                             # a scan run by hand (no run_forever): acted on at once, as before
    runner.step(NOW)
    assert len(broker.open_positions()) == 1


# ---------------------------------------------------------------- 2. the "found" alarm
def test_a_restart_whose_first_listing_is_empty_says_nothing_about_its_own_positions(tmp_path):
    """live_changes [1]: a position opened before the window started is a restored one, even when the first listing
    missed it; only one opened since the start (a lost order reply) is "found"."""
    api = Syncing()
    _held(api)
    runner, notifier = _window(api, tmp_path / "journal")
    api.hidden = True
    runner.manage_positions(runner.fetch())
    api.hidden = False
    runner.manage_positions(runner.fetch())
    assert not [m for m in notifier.sent if "without this window's record" in m]
    assert "901" in runner.known_positions


def test_a_found_position_carries_its_risk_and_counts_its_r(setup, tmp_path):
    """live_changes [3]: the found row has the risk and target a fill row has, and the forward record counts its R."""
    from kronos_trader.forward import DEAL_COLUMNS, reconcile, read_journal
    from tests.trader.test_live import _limit_runner
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    runner.step(NOW)
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 500.0, 0.0051, 4.0, price=1.1, ts=NOW)
    pos.meta["restored"] = True                         # a lost reply's order that landed and filled
    views = runner.fetch()
    runner.manage_positions(views)
    runner.manage_positions(views)
    journal = read_journal(tmp_path / "journal" / "trades.csv")
    found = journal[journal["event"] == "found"].iloc[0]
    assert found["risk"] == pytest.approx(500.0) and found["take_profit"] == pytest.approx(1.12)
    journal.loc[journal["event"] == "found", "id"] = "801"     # MT5's position id (the paper broker's is "P2")
    deals = pd.DataFrame([[1, 1, 801, "EURUSD", 0, 0, 0, NOW, 1.1, 1.0, 0.0, 0.0, 0.0, 0.0, 0, ""],
                          [2, 2, 801, "EURUSD", 1, 1, 4, NOW + pd.Timedelta(hours=1), 1.0949, 1.0, -500.0,
                           0.0, 0.0, 0.0, 0, ""]], columns=DEAL_COLUMNS)
    rec = reconcile(journal, deals)
    assert rec.iloc[0]["source"] == "bot" and rec.iloc[0]["r_gross"] == pytest.approx(-1.0)


# ---------------------------------------------------------------- 3. a fill the history shows before its position
def test_a_fill_the_history_shows_before_its_position_is_not_closed_again(tmp_path):
    """live_changes [2]: the terminal does not update at once; FILLED in the history with no listed position was read as
    "filled and closed again", and after a restart the next scan raised a false "found" alarm."""
    api = Syncing()
    api.orders.append(NS(ticket=501, symbol="EURUSD", type=2, volume_initial=0.24, volume_current=0.24, price_open=1.09808,
                         sl=1.092, tp=1.12, magic=20260930, comment="1HPOI BS L", time_setup=server_seconds(NOW)))
    runner, notifier = _window(api, tmp_path / "journal")   # a restarted window: the limit is in its file, not in the broker
    runner.limits["501"] = {"sid": "abc", "direction": "LONG", "price": 1.09808, "stop": 1.092, "take_profit": 1.12,
                            "lots": 0.24, "risk_amount": 146.0, "placed_at": NOW, "expires_at": NOW + pd.Timedelta(hours=4)}
    runner.manage_positions(runner.fetch())
    runner.manage_limits(NOW)
    api.fill_later(501, lag=3)                          # the history says FILLED, the position is listed a moment later
    runner.manage_limits(NOW)
    assert "501" in runner.limits                       # no answer yet: asked again next scan
    runner.manage_positions(runner.fetch())
    runner.manage_limits(NOW)
    assert not [m for m in notifier.sent if "closed again" in m]
    assert not [m for m in notifier.sent if "without this window's record" in m]
    assert [m for m in notifier.sent if "filled (limit)" in m]


def test_a_fill_whose_position_stays_unlisted_is_read_as_before_after_two_minutes():
    """A bound on the wait: a history that says FILLED while no position is listed and no deal closed it, for 2 minutes,
    is read as "filled and closed again" as before (the limit never blocks its market for good)."""
    clock = {"now": NOW}
    api = LimitMT5()
    broker = MT5Broker(Settings(), api=api, clock=lambda: clock["now"])
    order = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    api.fill(int(order.id))
    api.positions.clear()                               # never listed
    with pytest.raises(RuntimeError, match="not listed yet"):
        broker.limit_state(order.id)
    clock["now"] = NOW + pd.Timedelta(minutes=2)
    assert broker.limit_state(order.id)[0] == "filled"


def test_a_limit_that_filled_and_closed_between_two_scans_still_reads_closed_again():
    broker = MT5Broker(Settings(), api=LimitMT5(), clock=lambda: NOW)
    order = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    api = broker.mt5
    api.fill(int(order.id))
    api.server_closes(int(order.id), "sl")              # stopped out before the next scan
    assert broker.limit_state(order.id) == ("filled", None)


# ---------------------------------------------------------------- 4. the day report
class History(LimitMT5):
    """A loaded deal history (typed deals, the server's range filter); None and (-4, Not found) when nothing matches."""

    def __init__(self, balance, deals, unloaded=False):
        super().__init__()
        self.balance, self.typed, self.unloaded, self.asked = balance, list(deals), unloaded, 0

    def last_error(self):
        return (-4, "Terminal: Not found")

    def account_info(self):
        info = super().account_info()
        info.balance, info.equity = self.balance, self.balance
        return info

    def positions_get(self, symbol=None):
        return None

    def history_deals_get(self, *args, position=None, ticket=None):
        self.asked += 1
        if self.unloaded:
            return None
        lo, hi = (int(pd.Timestamp(x).timestamp()) for x in args)
        found = [d for d in self.typed if lo <= d.time <= hi]
        return tuple(found) if found else None


def _deal(n, when, typ, profit, entry=0, pid=0):
    return NS(ticket=n, order=n, position_id=pid, symbol="EURUSD" if typ <= 1 else "", type=typ, entry=entry, reason=0,
              time=server_seconds(when), price=1.1 if typ <= 1 else 0.0, volume=1.0 if typ <= 1 else 0.0, profit=profit,
              commission=0.0, swap=0.0, fee=0.0, magic=0, comment="")


def _record(term, settings, tmp_path, since):
    return cli._forward_record(settings, tmp_path / "trades.csv", since, "ftmo_2step",
                               connect=lambda: MT5Broker(settings, api=term, clock=lambda: NOW), now=NOW)


def test_trades_older_than_the_range_read_as_a_day_without_a_trade(monkeypatch, tmp_path):
    """connect_and_report [2]: a loaded history without a trade in the read's range (a new journal, --since) was refused
    as "not loaded" every day until a trade landed in the range."""
    monkeypatch.setattr(cli, "_pause", lambda s: None)
    settings = Settings()
    size = float(settings.account_size)
    deals = [_deal(1, NOW - pd.Timedelta(days=6), 2, size),                         # the deposit
             _deal(2, NOW - pd.Timedelta(days=3, hours=2), 0, 0.0, 0, 801),          # a trade three days ago: -300
             _deal(3, NOW - pd.Timedelta(days=3), 1, -300.0, 1, 801)]
    record = _record(History(size - 300.0, deals), settings, tmp_path, NOW - pd.Timedelta(days=1))
    assert record["status"]["left_today"] == pytest.approx(0.05 * size)               # nothing closed today


def test_a_balance_operation_without_a_trade_is_read(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_pause", lambda s: None)
    settings = Settings()
    size = float(settings.account_size)
    deals = [_deal(1, NOW - pd.Timedelta(days=1), 2, size), _deal(2, NOW - pd.Timedelta(hours=3), 2, 50.0)]
    record = _record(History(size + 50.0, deals), settings, tmp_path, NOW - pd.Timedelta(days=1))
    assert record["account"]["balance"] == pytest.approx(size + 50.0)


def test_a_history_that_lists_nothing_still_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_pause", lambda s: None)
    settings = Settings()
    term = History(float(settings.account_size) - 300.0, [], unloaded=True)
    with pytest.raises(RuntimeError, match="deal history is not loaded"):
        _record(term, settings, tmp_path, NOW - pd.Timedelta(days=2))
    assert term.asked == 2


# ---------------------------------------------------------------- 5. what a window says about the terminal's account
def test_a_window_that_connected_without_an_account_says_once_which_one_it_trades(setup):
    """connect_and_report [1]: the first account the terminal shows is taken on; the window says which (once), and a
    refusal of another one later says how it was taken on and the two ways out."""
    from tests.trader.test_review_fixes_15oct import Starting
    late = Starting(on=0)
    broker = MT5Broker(Settings(), api=late, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    broker.connect()
    runner, notifier = _runner(setup, broker)
    late.on = 55556666
    assert runner.connection_ok() and runner.connection_ok()
    said = [m for m in notifier.sent if "55556666" in m]
    assert len(said) == 1 and "dit venster handelt vanaf nu op dat account" in said[0]


def test_a_timed_out_limit_order_says_the_server_s_answer_not_the_send_s_success(monkeypatch):
    """live_changes [7]: a 10012 reply ended in "((1, 'Success'))", the send's own error that only a lost reply has."""
    monkeypatch.setattr(MT5Broker, "retry_seconds", 0.0)

    class TimedOut(LimitMT5):
        def order_send(self, request):
            if request["action"] == self.TRADE_ACTION_PENDING:
                self.requests.append(request)
                return NS(retcode=10012, order=0, deal=0, price=0.0, comment="Request timeout")
            return super().order_send(request)

        def last_error(self):
            return (1, "Success")
    broker = MT5Broker(Settings(), api=TimedOut(), clock=lambda: NOW)
    with pytest.raises(RuntimeError) as err:
        broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                 NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    assert "timed out on the server (retcode 10012 Request timeout) and not found" in str(err.value)
    assert "Success" not in str(err.value)
