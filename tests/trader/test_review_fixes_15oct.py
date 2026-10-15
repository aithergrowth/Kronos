"""The confirmed findings of the 15 October stack review (scratchpad review/), each fixed and pinned here: a lost reply
never sends a limit twice, an unpriced position refuses new entries, accrued swaps count in the worst case, break-even
never reads the cached or pre-fill candles, a stop that shrank before the order is sized on the minimum, a refused close backs
off, the day report reads a flat account, and no window ever logs a terminal in to another account."""
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.config import PropFirmParams, Settings
from kronos_trader.core import CandleSeries, Direction, Timeframe as T
from kronos_trader.execution import PaperBroker, RiskGuard
from kronos_trader.execution.base import LimitOrder, Position
from kronos_trader.execution.mt5 import MT5Broker
from kronos_trader.live import FeedReport, LiveRunner
from kronos_trader.notify import TelegramNotifier
from tests.trader.test_live import FakeEngine, _runner, setup  # noqa: F401  (the setup fixture lives there)
from tests.trader.test_mt5 import NOW, LimitMT5


# ---------------------------------------------------------------- 1. a lost reply never sends the limit twice
class LostReply(LimitMT5):
    """The first pending order reaches the server (``placed``) or not, and its reply never reaches Python (None)."""

    def __init__(self, placed=True, **kw):
        super().__init__(**kw)
        self.placed, self.lost = placed, 1

    def order_send(self, request):
        if request["action"] == self.TRADE_ACTION_PENDING and self.lost:
            self.lost -= 1
            if self.placed:
                super().order_send(request)
            else:
                self.requests.append(request)
            return None
        return super().order_send(request)

    def last_error(self):
        return (-10005, "IPC timeout")


def _place(api):
    broker = MT5Broker(Settings(), api=api, clock=lambda: NOW)
    order = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    return broker, order


def test_a_lost_reply_is_looked_up_and_never_sent_again():
    api = LostReply(expiration_mode=1 | 4)              # GTC and a specified expiry: the timed request goes first
    broker, order = _place(api)
    pending = [r for r in api.requests if r["action"] == api.TRADE_ACTION_PENDING]
    assert len(pending) == 1 and len(api.orders) == 1                 # before the fix: two requests, two resting orders
    assert order.id == str(api.orders[0].ticket)
    assert [o.id for o in broker.limit_orders()] == [order.id] and RiskGuard.open_risk(broker) == pytest.approx(344.0)


def test_a_lost_reply_with_nothing_resting_raises_and_sends_nothing_more():
    api = LostReply(placed=False, expiration_mode=1 | 4)
    with pytest.raises(RuntimeError, match="not sent again"):
        _place(api)
    assert len([r for r in api.requests if r["action"] == api.TRADE_ACTION_PENDING]) == 1 and api.orders == []


class LateList(LostReply):
    """The terminal lists the order only after ``lag`` listings (fixcheck mt5_semantics, case B)."""

    def __init__(self, lag=3, **kw):
        super().__init__(**kw)
        self.lag = lag

    def orders_get(self, symbol=None):
        if self.lag:
            self.lag -= 1
            return []
        return super().orders_get(symbol)


class FilledAtOnce(LostReply):
    """The lost reply's limit fills before the lookup: a position carrying the order's ticket (case D)."""

    def order_send(self, request):
        result = super().order_send(request)
        if request["action"] == self.TRADE_ACTION_PENDING and result is None and self.orders:
            self.fill(self.orders[-1].ticket)
        return result


class Unsent(LostReply):
    """No reply and nothing on the server; the lookup's own calls succeed and overwrite last_error (case I)."""

    def __init__(self, **kw):
        super().__init__(placed=False, **kw)
        self.err = (1, "Success")

    def order_send(self, request):
        result = super().order_send(request)
        if result is None:
            self.err = (-10005, "IPC timeout")
        return result

    def orders_get(self, symbol=None):
        self.err = (1, "Success")
        return super().orders_get(symbol)

    def last_error(self):
        return self.err


def test_the_lookup_waits_for_a_late_listing_and_adopts_an_instant_fill(monkeypatch):
    monkeypatch.setattr(MT5Broker, "retry_seconds", 0.0)
    api = LateList(expiration_mode=1 | 4)
    broker, order = _place(api)
    assert order.id == str(api.orders[0].ticket) and len([r for r in api.requests if r["action"] == api.TRADE_ACTION_PENDING]) == 1
    api = FilledAtOnce(expiration_mode=1 | 4)
    broker, order = _place(api)
    assert broker.limit_state(order.id)[0] == "filled" and api.orders == [] and len(api.positions) == 1


def test_the_failure_text_carries_the_sends_own_error(monkeypatch):
    monkeypatch.setattr(MT5Broker, "retry_seconds", 0.0)
    with pytest.raises(RuntimeError, match="IPC timeout.*not sent again"):
        _place(Unsent(expiration_mode=1 | 4))


def test_a_refused_expiry_still_falls_back_to_good_till_cancelled():
    api = LimitMT5(expiration_mode=1 | 4, refuse_expiry=True)
    broker, order = _place(api)
    assert [r["type_time"] for r in api.requests] == [api.ORDER_TIME_SPECIFIED, api.ORDER_TIME_GTC]
    assert order.id == str(api.orders[0].ticket) and len(api.orders) == 1


# ---------------------------------------------------------------- 2 and 3. the guard: unpriced risk, accrued swaps
class Book:
    """An account the guard reads: positions and limits; ``US100.cash`` cannot be priced (another window's NAS100)."""

    def __init__(self, positions=(), limits=(), balance=10_000.0):
        self.positions, self.limits, self.bal = list(positions), list(limits), balance

    def equity(self):
        return self.bal

    def balance(self):
        return self.bal

    def open_positions(self, symbol=None):
        return [p for p in self.positions if symbol is None or p.symbol == symbol]

    def limit_orders(self, symbol=None):
        return [o for o in self.limits if symbol is None or o.symbol == symbol]

    def pnl_for(self, symbol, direction, entry, exit, lots):
        if symbol == "US100.cash":
            raise KeyError(symbol)
        return direction.sign * (exit - entry) * lots * 100_000


def _position(symbol="EURUSD", stop=1.0950, risk=0.0, swap=0.0, lots=1.0):
    return Position(id="7", symbol=symbol, direction=Direction.LONG, lots=lots, entry=1.1000, stop=stop, take_profit=1.12,
                    opened_at=NOW, risk_amount=risk, risk_distance=0.005, breakeven_r=4.0, initial_stop=stop,
                    meta={"swap": swap})


def _guard():
    guard = RiskGuard(PropFirmParams(daily_loss_limit_pct=4.0, max_drawdown_pct=9.5, max_open_trades=3), 10_000)
    guard.update(NOW, 10_000, 10_000)
    return guard


def test_a_position_or_limit_the_window_cannot_price_refuses_a_new_entry():
    ok, reason = _guard().can_open(Book([_position(symbol="US100.cash", risk=0.0)]), NOW, new_risk=150)
    assert not ok and "could not be computed" in reason and "US100.cash 7" in reason      # before: open risk 0, admitted
    ok, _ = _guard().can_open(Book([_position(symbol="US100.cash", risk=294.0)]), NOW, new_risk=50)
    assert ok                                                          # the recorded risk prices it: no refusal
    limit = LimitOrder(id="9", symbol="US100.cash", direction=Direction.LONG, lots=1.0, price=25000.0, stop=24950.0,
                       take_profit=25200.0, risk_amount=0.0, risk_distance=50.0, breakeven_r=4.0, placed_at=NOW,
                       expires_at=NOW + pd.Timedelta(hours=4))
    ok, reason = _guard().can_open(Book(limits=[limit]), NOW, new_risk=50)
    assert not ok and "US100.cash limit 9" in reason


def test_accrued_swaps_count_in_the_worst_case():
    book = Book([_position(stop=1.0950, swap=0.0, lots=0.5)])          # 250 at the stop
    ok, _ = _guard().can_open(book, NOW, new_risk=140)                 # 250 + 140 = 3.9 % of the day: admitted
    assert ok
    swapped = Book([_position(stop=1.0950, swap=-166.0, lots=0.5)])    # a NAS100-like weekend of financing on top: 5.6 %
    ok, reason = _guard().can_open(swapped, NOW, new_risk=140)
    assert not ok and "daily loss would reach 5.56%" in reason
    credited = Book([_position(stop=1.0950, swap=+40.0, lots=0.5)])    # a credit never buys room
    ok, _ = _guard().can_open(credited, NOW, new_risk=155)
    assert not ok


# ---------------------------------------------------------------- 4. break-even: never the cache, never before the fill
class Server(PaperBroker):
    on_candle = None


def _be_runner(setup, rows, start, source):
    broker = Server(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 1000.0, 0.0051, 0.5, price=1.1,
                              ts=pd.Timestamp("2026-10-01 08:15"))                 # trigger at 0.5R: about 1.1026
    runner, notifier = _runner(setup, broker)
    views = {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start=start, symbol="EURUSD")}
    runner.fetch.report = FeedReport()
    runner.fetch.report.sources = {T.MIN_15: source}
    return runner, broker, notifier, views


def test_break_even_never_reads_the_cached_candles(setup):
    rows = [(1.1, 1.101, 1.099, 1.1), (1.1, 1.104, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1)]   # reaches the trigger
    runner, broker, notifier, views = _be_runner(setup, rows, "2026-10-01 08:15", "cache")
    runner.manage_positions(views)
    pos = broker.open_positions()[0]
    assert not pos.breakeven_done and pos.stop == pytest.approx(1.0949) and "be_checked_until" not in pos.meta
    runner.fetch.report.sources = {T.MIN_15: "broker"}                  # the same candles from the terminal: it moves
    runner.manage_positions(views)
    assert broker.open_positions()[0].breakeven_done


def test_break_even_never_reads_a_candle_from_before_the_fill_nor_an_old_checkpoint(setup):
    rows = [(1.1, 1.106, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1)]
    runner, broker, notifier, views = _be_runner(setup, rows, "2026-10-01 08:00", "broker")   # the high came at 08:00
    pos = broker.open_positions()[0]
    pos.meta["be_checked_until"] = pd.Timestamp("2026-10-01 05:45")    # a checkpoint set on the cache's 1 October
    runner.manage_positions(views)
    pos = broker.open_positions()[0]
    assert not pos.breakeven_done and pos.stop == pytest.approx(1.0949)
    assert pos.meta["be_checked_until"] == pd.Timestamp("2026-10-01 08:45")
    pos.meta["be_checked_until"] = pd.Timestamp("2026-10-01 09:30")    # a later look: the checkpoint never moves back
    runner.manage_positions(views)
    assert broker.open_positions()[0].meta["be_checked_until"] == pd.Timestamp("2026-10-01 09:30")


# ---------------------------------------------------------------- 5. a stop that shrank before the order: sized on the minimum
def _shrunk(setup, last, frac=0.0):
    settings = Settings()
    settings.risk.min_stop_pips = 8.0
    settings.risk.limit_entry_fraction = frac
    settings.live.journal_path = f"journal_floor_{frac}_{last}/trades.csv"
    broker = PaperBroker(settings, use_spread=False)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.1, min(1.099, last), last)]          # price ran toward the stop
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: NOW, require_approval=False)
    runner.step(NOW)
    return runner, broker, notifier


def test_a_stop_that_shrank_before_the_order_is_taken_on_the_lots_of_the_minimum(setup):
    from kronos_trader.strategy.risk import size_position
    runner, broker, notifier = _shrunk(setup, 1.0951)                   # 2 pips left to the stop at 1.0949
    pos = broker.open_positions()[0]
    floor = size_position(broker.equity(), 1.0951, 1.0951 - 0.0008, runner.spec, runner.stake_params(setup))[0]
    assert pos.stop == pytest.approx(1.0949) and pos.lots == pytest.approx(floor) and floor > 0
    assert any("sized on the 8-pip minimum" in m for m in notifier.sent)
    # the money at the stop stays under the budget (1,000), not the budget on a 2-pip stop (33.33 lots)
    budget = 100_000 * runner.stake_params(setup).risk_pct / 100
    assert 0 < -broker.pnl_for("EURUSD", Direction.LONG, pos.entry, pos.stop, pos.lots) < 0.3 * budget
    # a stop at or past the minimum is sized as before
    runner, broker, notifier = _shrunk(setup, 1.1)
    pos = broker.open_positions()[0]
    assert pos.lots == pytest.approx(size_position(broker.equity(), 1.1, 1.0949, runner.spec, runner.stake_params(setup))[0])
    assert not any("minimum" in m for m in notifier.sent)


def test_a_limit_is_held_to_the_fractions_share_of_the_minimum(setup):
    from kronos_trader.strategy.risk import size_position
    runner, broker, notifier = _shrunk(setup, 1.0953, frac=0.25)        # the limit a pip toward the stop: 3 pips left
    order = broker.limit_orders("EURUSD")[0]
    limits = [m for m in notifier.sent if "LIMIT" in m]
    assert len(limits) == 1 and "sized on the 6-pip minimum" in limits[0]
    floor = size_position(broker.equity(), order.price, order.price - 0.0006, runner.spec, runner.stake_params(setup))[0]
    assert order.lots == pytest.approx(floor) and order.stop == pytest.approx(1.0949)


# ---------------------------------------------------------------- 6. a refused close backs off
def test_a_refused_time_exit_is_tried_three_times_then_every_quarter_hour(setup):
    class Closed(Server):
        tries = 0

        def close_position(self, *args, **kwargs):
            Closed.tries += 1
            raise RuntimeError("retcode 10018 Market closed")
    settings = Settings()
    settings.exits.max_hold_hours = 1.0
    broker = Closed(settings)
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 1000.0, 0.0051, 4.0, price=1.1,
                              ts=NOW - pd.Timedelta(hours=2))
    clock = {"now": NOW}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", lambda: {}, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: clock["now"], require_approval=False)
    views = {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    for minute in range(30):
        clock["now"] = NOW + pd.Timedelta(minutes=minute)
        runner.stale = {T.MIN_15: pd.Timedelta(hours=40)}               # the market is shut: no fresh candles
        runner.manage_positions(views)
    assert Closed.tries == 4                                           # minutes 0, 1, 2 and 17 (before: 30, one a scan)
    assert sum("closing" in m and "failed" in m for m in notifier.sent) == 1


def test_a_refused_time_exit_is_tried_every_scan_while_the_market_trades(setup):
    """fixcheck regress_normal: the back-off holds only while the market is shut; with fresh bars every scan tries again,
    so a funded Friday close refused for three minutes still goes out before US100.cash's close."""
    class Refusing(Server):
        tries = 0

        def close_position(self, *args, **kwargs):
            Refusing.tries += 1
            if Refusing.tries <= 3:
                raise RuntimeError("retcode 10021 no quotes")
            return super().close_position(*args, **kwargs)
    settings = Settings()
    settings.exits.max_hold_hours = 1.0
    broker = Refusing(settings)
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 1000.0, 0.0051, 4.0, price=1.1,
                              ts=NOW - pd.Timedelta(hours=2))
    clock = {"now": NOW}
    runner = LiveRunner(settings, "EURUSD", lambda: {}, broker=broker, notifier=TelegramNotifier(dry_run=True),
                        engine=FakeEngine(setup), dry_run=False, clock=lambda: clock["now"], require_approval=False)
    views = {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    for minute in range(6):
        clock["now"] = NOW + pd.Timedelta(minutes=minute)
        runner.stale = {}                                               # fresh bars: the market trades
        runner.manage_positions(views)
    assert Refusing.tries == 4 and broker.open_positions() == []      # minutes 0-2 refused, closed at minute 3


def test_break_even_reads_a_market_fills_own_candle(setup):
    """fixcheck regress_normal: a market fill made at the scan after a close counts its own candle, as the backtest does
    (its entry is that candle's open); a fill later in the candle does not."""
    rows = [(1.1, 1.104, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1)]   # the trigger in the first
    for filled, moved in (("2026-10-01 08:15:40", True), ("2026-10-01 08:20:00", False)):
        broker = Server(Settings())
        broker.set_price("EURUSD", 1.1)
        broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 1000.0, 0.0051, 0.5, price=1.1,
                                  ts=pd.Timestamp(filled))
        runner, notifier = _runner(setup, broker)
        views = {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
        runner.fetch.report = FeedReport()
        runner.fetch.report.sources = {T.MIN_15: "broker"}
        runner.manage_positions(views)
        assert broker.open_positions()[0].breakeven_done is moved, filled


# ---------------------------------------------------------------- 7. the day report on a flat account
def test_the_day_report_reads_a_flat_account_and_a_phase_without_deals():
    from kronos_trader.forward import account_from_mt5, deals_from_mt5

    class Build6244(LimitMT5):
        def last_error(self):
            return (-4, "Terminal: Not found")

        def positions_get(self, symbol=None):
            found = [p for p in self.positions if symbol is None or p.symbol == symbol]
            return tuple(found) if found else None

        def history_deals_get(self, *args, position=None, ticket=None):
            found = super().history_deals_get(*args, position=position, ticket=ticket)
            return tuple(found) if found else None
    broker = MT5Broker(Settings(), api=Build6244(), clock=lambda: NOW)
    account = account_from_mt5(broker)
    assert account["positions"] == [] and account["balance"] == pytest.approx(100_000.0)
    assert len(deals_from_mt5(broker, NOW - pd.Timedelta(days=2), NOW)) == 0

    class Broken(Build6244):
        def last_error(self):
            return (-10001, "IPC send failed")
    with pytest.raises(RuntimeError, match="did not"):
        account_from_mt5(MT5Broker(Settings(), api=Broken(), clock=lambda: NOW))


# ---------------------------------------------------------------- 8. a terminal is never switched to another account
from tests.trader.test_mt5 import FakeMT5  # noqa: E402


class Terminal(FakeMT5):
    """A terminal on account ``on`` (0: none yet, "authorization failed"), optionally without its trade server; every
    initialize call is kept, and one with credentials logs it in to that account."""

    def __init__(self, on, connected=True):
        super().__init__()
        self.on, self.connected, self.calls = on, connected, []

    def initialize(self, **kwargs):
        self.calls.append(dict(kwargs))
        if "login" in kwargs:
            self.on, self.connected = kwargs["login"], True
        return True

    def account_info(self):
        return None if not self.on else SimpleNamespace(login=self.on, server="X", currency="USD", balance=10000.0,
                                                        equity=10000.0, leverage=100, trade_mode=0)

    def terminal_info(self):
        return SimpleNamespace(connected=self.connected, trade_allowed=True)


def _env(monkeypatch, login="11112222"):
    monkeypatch.setenv("MT5_PATH", r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")
    monkeypatch.setenv("MT5_LOGIN", login)
    monkeypatch.setenv("MT5_PASSWORD", "pw")
    monkeypatch.setenv("MT5_SERVER", "MetaQuotes-Demo")


def test_a_terminal_on_another_account_is_refused_never_logged_in_to_ours(monkeypatch):
    _env(monkeypatch)                                          # the demo login left in the environment
    ftmo = Terminal(on=55556666)                               # the FTMO terminal, on the challenge account
    broker = MT5Broker(Settings(), api=ftmo, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    with pytest.raises(RuntimeError, match="logged in to account 55556666, MT5_LOGIN is 11112222: not switching"):
        broker.connect()
    assert ftmo.on == 55556666 and all("login" not in c and "password" not in c for c in ftmo.calls)


def test_credentials_log_in_only_a_terminal_without_an_account_or_its_server(monkeypatch):
    _env(monkeypatch)
    for terminal in (Terminal(on=0), Terminal(on=11112222, connected=False)):
        broker = MT5Broker(Settings(), api=terminal, clock=lambda: NOW, connect=False)
        broker._sleep = lambda s: None
        broker.connect()
        assert terminal.calls[-1]["login"] == 11112222 and broker.account_login == 11112222
    on_it = Terminal(on=11112222)                              # already there: attached, no credentials sent
    broker = MT5Broker(Settings(), api=on_it, clock=lambda: NOW, connect=False)
    broker.connect()
    assert [("login" in c) for c in on_it.calls] == [False]


def test_a_reconnect_never_switches_the_terminal_either(monkeypatch):
    _env(monkeypatch)
    terminal = Terminal(on=11112222)
    broker = MT5Broker(Settings(), api=terminal, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    broker.connect()
    terminal.on = 55556666                                     # someone logged the terminal in to another account
    real, first = terminal.account_info, [True]

    def info():                                                # ... and the link dropped once: the window re-initialises
        if first:
            first.clear()
            return None
        return real()
    terminal.account_info = info
    ok, reason = broker.connection_ok()
    assert not ok and "not switching" in reason and terminal.on == 55556666
    assert all("login" not in c for c in terminal.calls[1:])


# ---------------------------------------------------------------- 9. the smaller live-path fixes (A10, A12, A15, A17, A19, A28)
def test_a_guard_refusal_at_the_first_check_is_journaled(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.SHORT, 0.1, 1.11, 1.09, 100.0, 0.0101, 4.0, price=1.1, ts=NOW)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    rows = pd.read_csv(runner.settings.live.journal_path)
    assert (rows["event"] == "not_executed").sum() == 1 and any("NOT executable" in m for m in notifier.sent)


def test_a_stray_limit_that_appears_later_is_cancelled_at_the_next_scan(setup, tmp_path):
    from tests.trader.test_live import _limit_runner
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    runner.step(NOW)                                                    # this window's own limit
    known = broker.limit_orders()[0]
    stray = broker.place_limit_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.0900, 1.1100, 250.0, 0.005, 4.0,
                                     NOW + pd.Timedelta(hours=1), ts=NOW)   # e.g. one whose reply was lost
    runner.step(NOW + pd.Timedelta(minutes=1))
    assert [o.id for o in broker.limit_orders()] == [known.id]
    assert any(f"limit {stray.id} cancelled now" in m for m in notifier.sent)
    stuck = broker.place_limit_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.0900, 1.1100, 250.0, 0.005, 4.0,
                                     NOW + pd.Timedelta(hours=1), ts=NOW)

    def refused(order_id):
        raise RuntimeError("market closed")
    broker.cancel_limit = refused
    for minute in (2, 3, 4):
        runner.step(NOW + pd.Timedelta(minutes=minute))
    assert len([m for m in notifier.sent if f"limit {stuck.id} is not this window's" in m]) == 1


def test_an_account_the_terminal_did_not_give_still_runs_the_exits(setup):
    broker = Server(Settings())                                         # a terminal: no paper candles to advance
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    ran = []
    runner.manage_positions = lambda views: ran.append("exits")

    def unread():
        raise AttributeError("'NoneType' object has no attribute 'equity'")
    broker.equity = unread
    with pytest.raises(RuntimeError, match="the account could not be read.*the exits were handled"):
        runner.step(NOW)
    assert ran == ["exits"] and broker.open_positions() == []


def test_a_failed_positions_listing_leaves_a_limit_unknown_instead_of_closed_again():
    api = LimitMT5()
    broker = MT5Broker(Settings(), api=api, clock=lambda: NOW)
    order = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    api.fill(int(order.id))
    listed, error = api.positions_get, api.last_error
    api.positions_get = lambda symbol=None: None
    api.last_error = lambda: (-10001, "IPC send failed")
    with pytest.raises(RuntimeError, match="did not list the open positions"):
        broker.limit_state(order.id)
    api.positions_get, api.last_error = listed, error
    state, pos = broker.limit_state(order.id)
    assert state == "filled" and pos is not None


def test_a_close_confirmed_without_a_price_books_the_closing_deals_price():
    class NoPrice(FakeMT5):
        def order_send(self, request):
            result = super().order_send(request)
            if request.get("position"):
                result.price = 0.0
            return result
    broker = MT5Broker(Settings(), api=NoPrice(), clock=lambda: NOW)
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0950, 1.1200, 50.0, 0.005, 4.0, ts=NOW)
    closed = broker.close_position(pos.id, reason="time")
    assert closed.exit == pytest.approx(1.1000)                         # the bid the closing deal was made at


def test_a_failed_chart_leaves_no_figure_behind(tmp_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from kronos_trader.notify.chart import render_chart
    series = CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 30, T.MIN_15, start="2026-10-01 08:00", symbol="EURUSD")
    blocked = tmp_path / "a_file"
    blocked.write_text("not a folder", encoding="utf-8")
    for _ in range(3):
        with pytest.raises(Exception):
            render_chart(series, blocked / "charts" / "c.png")
    assert len(plt.get_fignums()) <= 1
    render_chart(series, tmp_path / "ok.png")
    assert plt.get_fignums() == []


def test_the_morning_room_line_adds_the_room_after_every_open_stop(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.11, 1.09, 1000.0, 0.0101, 4.0, price=1.1, ts=NOW)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    morning = [m for m in notifier.sent if m.startswith("☀️")]
    assert len(morning) == 1 and "🛡 Ruimte: vandaag nog 4.0%" in morning[0]
    assert "🛡 Na alle open stops: vandaag nog 3.0%, totaal nog 7.0%" in morning[0]     # 100 pips x 1 lot = 1 % of 100,000
    flat = PaperBroker(Settings())
    flat.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, flat, require_approval=False)
    runner.step(NOW)
    assert not any("Na alle open stops" in m for m in notifier.sent)
