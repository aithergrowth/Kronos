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


def test_a_stop_still_over_half_the_minimum_is_sized_as_before(setup):
    """The final fix check (N3): the lots floor acts only where the stated fix acted, a stop under half of
    risk.min_stop_pips at the order price. An ordinary slip toward a stop at the minimum keeps the lots of the running
    code (the profiles' sizing is frozen during the challenge; the full floor is Max's decision)."""
    from kronos_trader.strategy.risk import size_position
    runner, broker, notifier = _shrunk(setup, 1.0955)                   # market: 6 pips left of the 8-pip minimum
    pos = broker.open_positions()[0]
    assert pos.lots == pytest.approx(size_position(broker.equity(), 1.0955, 1.0949, runner.spec, runner.stake_params(setup))[0])
    assert not any("minimum" in m for m in notifier.sent)
    runner, broker, notifier = _shrunk(setup, 1.0955, frac=0.25)        # limit: 4.5 pips at the limit, over half of 8
    order = broker.limit_orders("EURUSD")[0]
    assert order.lots == pytest.approx(size_position(broker.equity(), order.price, 1.0949, runner.spec,
                                                     runner.stake_params(setup))[0])
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


def test_the_day_report_fails_when_the_balance_moved_and_no_trade_is_listed(monkeypatch, tmp_path):
    """fixcheck guard_arith: a deal history not loaded yet also answers "not found"; read as empty it gave the day's start
    without the day's loss (500 left today instead of 200). Money moved and no trade listed: asked again, then an error."""
    from kronos_trader import cli

    class Unloaded(LimitMT5):
        def __init__(self, balance):
            super().__init__()
            self.balance, self.asked = balance, 0

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
            return None
    monkeypatch.setattr(cli, "_pause", lambda s: None)
    settings = Settings()
    moved = Unloaded(settings.account_size - 300.0)
    with pytest.raises(RuntimeError, match="deal history is not loaded"):
        cli._forward_record(settings, tmp_path / "trades.csv", NOW - pd.Timedelta(days=2), "ftmo_2step",
                            connect=lambda: MT5Broker(settings, api=moved, clock=lambda: NOW), now=NOW)
    assert moved.asked == 2
    flat = Unloaded(settings.account_size)                             # a phase without a trade yet: read as it is
    record = cli._forward_record(settings, tmp_path / "trades.csv", NOW - pd.Timedelta(days=2), "ftmo_2step",
                                 connect=lambda: MT5Broker(settings, api=flat, clock=lambda: NOW), now=NOW)
    assert len(record["deals"]) == 0 and flat.asked == 1


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


def test_credentials_only_log_a_terminal_in_again_to_the_account_it_shows(monkeypatch):
    _env(monkeypatch)
    again = Terminal(on=11112222, connected=False)             # on MT5_LOGIN without its server: the same account
    broker = MT5Broker(Settings(), api=again, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    broker.connect()
    assert again.calls[-1]["login"] == 11112222 and broker.account_login == 11112222
    blind = Terminal(on=0)                                     # no account to read: refused, never logged in blind
    broker = MT5Broker(Settings(), api=blind, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    with pytest.raises(RuntimeError, match="shows no account after a minute"):
        broker.connect()
    assert all("login" not in c for c in blind.calls)
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


# ---------------------------------------------------------------- 10. the second fix check (fixcheck2): the residuals
class Starting(FakeMT5):
    """A terminal on account ``on``. ``busy``: the next N initialize calls answer IPC timeout. ``logs_in_after``: it is
    starting and reaches its account only after that many seconds of the broker's own pauses. ``refuses``: initialize
    without credentials answers -6 (authorization failed)."""

    def __init__(self, on, busy=0, logs_in_after=0.0, refuses=False):
        super().__init__()
        self.on, self.busy, self.after, self.refuses = on, busy, logs_in_after, refuses
        self.waited, self.calls, self.err = 0.0, [], (1, "Success")

    def initialize(self, **kwargs):
        self.calls.append(dict(kwargs))
        if self.busy:
            self.busy -= 1
            self.err = (-10005, "IPC timeout")
            return False
        if "login" in kwargs:
            self.on, self.after, self.refuses = kwargs["login"], 0.0, False   # logs it in: a switch when on another
        elif self.refuses:
            self.err = (-6, "Terminal: Authorization failed")
            return False
        self.err = (1, "Success")
        return True

    def last_error(self):
        return self.err

    def account_info(self):
        if self.waited < self.after or self.refuses:
            return None
        return SimpleNamespace(login=self.on, server="X", currency="USD", balance=10000.0, equity=10000.0, leverage=100,
                               trade_mode=0)

    def terminal_info(self):
        return SimpleNamespace(connected=self.waited >= self.after, trade_allowed=True)


def _broker_on(terminal, monkeypatch):
    _env(monkeypatch)                                          # the demo login still set, MT5_PATH on the FTMO terminal
    broker = MT5Broker(Settings(), api=terminal, clock=lambda: NOW, connect=False)

    def pause(seconds):
        terminal.waited += seconds
    broker._sleep = pause
    return broker


def test_a_terminal_that_did_not_answer_or_is_still_starting_never_gets_the_credentials(monkeypatch):
    busy = Starting(on=55556666, busy=1)                       # one IPC timeout, then it answers with its own account
    with pytest.raises(RuntimeError, match="not switching"):
        _broker_on(busy, monkeypatch).connect()
    assert busy.on == 55556666 and all("login" not in c for c in busy.calls)
    slow = Starting(on=55556666, logs_in_after=20.0)           # a cold start: its own account after 20 s
    with pytest.raises(RuntimeError, match="not switching"):
        _broker_on(slow, monkeypatch).connect()
    assert slow.on == 55556666 and all("login" not in c for c in slow.calls)
    slower = Starting(on=55556666, logs_in_after=75.0)        # slower than the minute: refused, not switched
    with pytest.raises(RuntimeError, match="shows no account after a minute"):
        _broker_on(slower, monkeypatch).connect()
    assert slower.on == 55556666 and all("login" not in c for c in slower.calls)
    refused = Starting(on=0, refuses=True)                     # "authorization failed": refused with what to do
    with pytest.raises(RuntimeError, match="Authorization failed.*log it in by hand"):
        _broker_on(refused, monkeypatch).connect()
    assert all("login" not in c for c in refused.calls)


def test_a_refused_reconnect_says_so_and_a_window_without_an_account_adopts_the_first_one(monkeypatch):
    terminal = Starting(on=11112222)
    broker = _broker_on(terminal, monkeypatch)
    broker.connect()
    terminal.on, real, first = 55556666, terminal.account_info, [True]

    def info():                                                # the link dropped once; the terminal is back elsewhere
        if first:
            first.clear()
            return None
        return real()
    terminal.account_info = info
    ok, reason = broker.connection_ok()
    assert not ok and reason.startswith("the MT5 terminal") and "not switching" in reason
    late = Starting(on=0)                                      # connected while the terminal had no account yet ...
    for key in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"):
        monkeypatch.delenv(key, raising=False)
    broker = MT5Broker(Settings(), api=late, clock=lambda: NOW, connect=False)
    broker._sleep = lambda s: None
    broker.connect()
    assert not broker.account_login                           # no account at connect: no check yet
    late.on = 55556666                                         # ... its account shows: from now on it is this window's
    assert broker.connection_ok() == (True, "ok") and broker.account_login == 55556666
    late.on = 11112222
    ok, reason = broker.connection_ok()
    assert not ok and "this window trades 55556666" in reason


def test_the_heartbeat_names_the_current_reason_of_an_outage(setup):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker)
    reasons = iter([(False, "MT5 not reachable (terminal closed or restarting)"),
                    (False, "MT5 is logged in to account 11112222, this window trades 55556666: not trading")])
    broker.connection_ok = lambda: next(reasons)
    runner.connection_ok()
    runner.connection_ok()
    assert "logged in to account 11112222" in runner._link_down


def test_a_lost_limit_reply_uses_the_visit_and_an_unknown_fill_is_said_once(setup, tmp_path):
    from tests.trader.test_live import _limit_runner
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    marked = []
    runner.engine.mark_traded = lambda *a: marked.append(a)

    def lost(*args, **kwargs):
        raise RuntimeError("EURUSD limit order: no answer from the terminal ((-10005, 'IPC timeout')) and not found on "
                           "the server within 2 s; not sent again - it may still appear there")
    broker.place_limit_order = lost
    runner.step(NOW)
    assert len(marked) == 1 and runner.limits == {}             # the visit counts as used, as a placed limit does
    # the order reached the server after all and filled: a position this window has no record of
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 500.0, 0.0051, 4.0, price=1.1, ts=NOW)
    pos.meta["restored"] = True
    views = runner.fetch()
    runner.manage_positions(views)
    runner.manage_positions(views)
    found = [m for m in notifier.sent if "without this window's record" in m]
    assert len(found) == 1 and pos.id in found[0]
    rows = pd.read_csv(tmp_path / "journal" / "trades.csv")
    assert (rows["event"] == "found").sum() == 1


def test_the_lookup_never_adopts_a_position_with_other_exits(monkeypatch):
    monkeypatch.setattr(MT5Broker, "retry_seconds", 0.0)

    class Lookalike(LostReply):
        """The lost order never reached the server; an earlier position of the same size and comment, with other
        exits, is open and untracked (a restart)."""

        def __init__(self, **kw):
            super().__init__(placed=False, **kw)
            self.positions.append(SimpleNamespace(ticket=900, identifier=900, symbol="EURUSD", type=self.POSITION_TYPE_BUY,
                                                  volume=1.0, price_open=1.0995, sl=1.0900, tp=1.1300, time=0,
                                                  magic=20260930, comment="4HPOI balance_shift L", profit=0.0, swap=0.0))
    with pytest.raises(RuntimeError, match="not sent again"):
        _place(Lookalike(expiration_mode=1 | 4))


def test_a_floored_order_cut_by_the_margin_states_the_share_of_the_planned_lots(setup):
    settings = Settings()
    settings.risk.min_stop_pips = 8.0
    settings.live.journal_path = "journal_floor_margin/trades.csv"
    broker = PaperBroker(settings, use_spread=False)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.1, 1.0951, 1.0951)]          # 2 pips left: 33.33 -> 11.11 lots
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: NOW, require_approval=False)
    runner.margin_room = lambda direction, price: (1.0, 500.0)                      # 1 lot fits
    runner.step(NOW)
    fill = [m for m in notifier.sent if "filled" in m][0]
    assert broker.open_positions()[0].lots == pytest.approx(1.0)
    assert "lots 33.33 -> 11.11" in fill and "(margin: lots cut from 11.11, risk 3 % of planned)" in fill


# ---------------------------------------------------------------- 11. the news calendar reaches the end of the year
def test_the_seeded_calendar_blacks_out_the_releases_after_13_november():
    """Stack review B1: the file ended on 13 November, after which only ForexFactory's "High" rows blocked entries (none
    at all with ForexFactory down). The rows to 31 December are checked against the publishers (BLS, Census, BEA, the
    Fed, the ECB, Eurostat, Destatis, INSEE)."""
    from pathlib import Path
    from kronos_trader.data.calendar import NewsCalendar, load_events
    events = load_events(Path(__file__).resolve().parents[2] / "data" / "calendar" / "high_impact.csv")
    cal = NewsCalendar(events)
    assert max(e.time for e in events) >= pd.Timestamp("2026-12-30")
    for ts, title in (("2026-11-17 13:20", "Retail Sales MoM"), ("2026-12-04 13:20", "Non Farm Payrolls"),
                      ("2026-12-09 19:10", "Fed Interest Rate Decision"), ("2026-12-10 13:45", "Core Inflation Rate MoM")):
        hit = cal.blackout("EURUSD", pd.Timestamp(ts))
        assert hit is not None and hit.currency == "USD", ts
    assert cal.blackout("EURUSD", pd.Timestamp("2026-12-17 13:00")).title in ("Deposit Facility Rate", "ECB Interest Rate Decision")
    assert cal.blackout("EURUSD", pd.Timestamp("2026-11-17 12:00")) is None



def test_a_failed_forexfactory_read_falls_back_on_the_saved_week_whatever_its_age(tmp_path, monkeypatch):
    import os
    from types import SimpleNamespace
    from kronos_trader.data import calendar as cal
    saved = cal.NewsEvent(pd.Timestamp("2026-11-20 13:30"), "USD", "Retail Sales MoM", 1)
    cal.save_events([saved], tmp_path / "forexfactory_nextweek.csv")
    os.utime(tmp_path / "forexfactory_nextweek.csv", (0, 0))                   # four days old: too old to count as fresh
    monkeypatch.setattr(cal, "fetch_forexfactory",
                        lambda week="thisweek", **kw: (_ for _ in ()).throw(RuntimeError("ForexFactory calendar 429")))
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "trades.csv")
    settings.news.enabled, settings.news.forexfactory = True, True
    added = []
    engine = SimpleNamespace(calendar=SimpleNamespace(add=lambda ev: added.extend(ev)), traded={})
    LiveRunner(settings, "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=engine,
               clock=lambda: NOW).refresh_news(NOW)
    assert [e.title for e in added] == ["Retail Sales MoM"]


# ---------------------------------------------------------------- 12. the loop changes' check (fixcheck2 loop_changes)
def test_a_feed_outage_while_the_market_trades_does_not_slow_a_refused_exit(setup):
    """No fresh bars (the feed failed) reads as 'shut', but only the server's 10018 is a closed market: a close refused
    with 10021 (no quotes) is tried every scan, so a funded Friday close is not pushed past the close."""
    class Refusing(Server):
        tries = 0

        def close_position(self, *args, **kwargs):
            Refusing.tries += 1
            if Refusing.tries <= 3:
                raise RuntimeError("close failed: retcode 10021 No quotes")
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
        runner.stale = {T.MIN_15: pd.Timedelta(hours=1)}               # the feed is down: no fresh bars
        runner.manage_positions(views)
    assert Refusing.tries == 4 and broker.open_positions() == []


def test_a_stray_limit_whose_cancel_is_refused_backs_off(setup, tmp_path):
    from tests.trader.test_live import _limit_runner
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    runner.engine.calls = 1                                             # no signal: only the sweep runs
    stray = broker.place_limit_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.0900, 1.1100, 250.0, 0.005, 4.0,
                                     NOW + pd.Timedelta(hours=1), ts=NOW)
    asked = []

    def refused(order_id):
        asked.append(order_id)
        raise RuntimeError("retcode 10018 Market closed")
    broker.cancel_limit = refused
    for minute in range(30):
        runner.manage_limits(NOW + pd.Timedelta(minutes=minute))
    assert len(asked) == 4                                              # minutes 0, 1, 2 and 17 (not 30 requests)
    assert len([m for m in notifier.sent if f"limit {stray.id} is not this window's" in m]) == 1


def test_the_room_after_the_stops_never_shows_more_than_the_equity_room_nor_with_a_stopless_position(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    pos = broker.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.11, 1.09, 1000.0, 0.0101, 4.0, price=1.1, ts=NOW)
    pos.stop = 0.0                                                      # a position without a stop: no room to show
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    morning = [m for m in notifier.sent if m.startswith("☀️")]
    assert len(morning) == 1 and "Na alle open stops" not in morning[0]


def test_a_restored_limit_fill_is_known_as_one_from_the_order_history():
    """After a restart a limit fill is told from a market fill by the order that opened it, not only by its comment
    (a server may cut the comment): break-even then never reads its own candle from before the fill."""
    api = LimitMT5()
    broker = MT5Broker(Settings(), api=api, clock=lambda: NOW)
    order = broker.place_limit_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.0950, 1.1200, 344.0, 0.0041, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "4HPOI balance_shift L"}, ts=NOW)
    api.fill(int(order.id))
    api.positions[-1].comment = "4HPOI"                                 # the server kept only part of it
    restarted = MT5Broker(Settings(), api=api, clock=lambda: NOW)
    pos = restarted.open_positions("EURUSD")[0]
    assert pos.meta.get("restored") and pos.meta.get("limit_id") == order.id
