"""The confirmed findings of the 15 October stack review (scratchpad review/), each fixed and pinned here: a lost reply
never sends a limit twice, an unpriced position refuses new entries, accrued swaps count in the worst case, break-even
never reads the cached or pre-fill candles, a stop under half the minimum at the fill is refused, a refused close backs
off, and the day report reads a flat account."""
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


# ---------------------------------------------------------------- 5. a stop under half the minimum at the fill
def test_a_stop_that_shrank_under_half_the_minimum_before_the_fill_is_refused(setup):
    settings = Settings()
    settings.risk.min_stop_pips = 8.0
    broker = PaperBroker(settings, use_spread=False)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.1, 1.0950, 1.0951)]                # price ran almost to the stop
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: NOW, require_approval=False)
    runner.step(NOW)
    assert broker.open_positions() == []
    assert any("under half the 8-pip minimum" in m for m in notifier.sent)


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
        runner.manage_positions(views)
    assert Closed.tries == 4                                           # minutes 0, 1, 2 and 17 (before: 30, one a scan)
    assert sum("closing" in m and "failed" in m for m in notifier.sent) == 1


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
