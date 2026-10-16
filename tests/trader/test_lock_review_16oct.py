"""The review of the lock at the phase's target (16 October, option B): one test per finding that was fixed. The lock aims
the trade that lifts the closed balance over the target and does nothing once the target stands; it counts the fill's
round turn and the other open positions' closing costs; a market order carries it only clear of the price."""
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.core import CandleSeries, Direction, Timeframe as T
from kronos_trader.core.types import TradeSetup
from kronos_trader.execution.mt5 import MT5Broker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from tests.trader.test_live import FakeEngine, NOW, setup  # noqa: F401  (the setup fixture lives there)
from tests.trader.test_lock_at_target import (TODAY, AccountMT5, _earlier, _hold, _mt5, _paper, _rows, _scan,
                                              _settings)


class BookingMT5(AccountMT5):
    """The account books each deal's commission (forex 1.50 a lot a side, crypto 0.0325 % of the notional a side) and a
    close's profit and swap into its balance; ``drift`` ticks move the quote while a market order travels, and a buy whose
    take-profit is not above the bid then is refused with 10016 Invalid stops."""
    FX_SIDE, CRYPTO_SIDE_PCT = 1.5, 0.0325

    def __init__(self, balance, drift=0):
        super().__init__(balance)
        self.drift = drift

    def side_commission(self, name, volume, price):
        if name == "BTCUSD":
            return -self.CRYPTO_SIDE_PCT / 100.0 * volume * price * self.CONTRACT[name]
        return -self.FX_SIDE * volume if name == "EURUSD" else 0.0

    def order_calc_margin(self, kind, name, lots, price):
        return lots * price * self.CONTRACT[name] / (2.0 if name == "BTCUSD" else 100.0)

    def order_send(self, request):
        if request["action"] == self.TRADE_ACTION_DEAL and not request.get("position"):
            name, tick = request["symbol"], self.TICK[request["symbol"]]
            bid, ask = self.quotes[name]
            self.quotes[name] = bid, ask = bid + self.drift * tick, ask + self.drift * tick
            buy = request["type"] == self.ORDER_TYPE_BUY
            if request["tp"] and ((buy and request["tp"] <= bid) or (not buy and request["tp"] >= ask)):
                self.requests.append(request)
                return SimpleNamespace(retcode=10016, order=0, deal=0, price=0.0, comment="Invalid stops")
            price = ask if buy else bid
            commission = self.side_commission(name, float(request["volume"]), price)
            pid = self.hold(name, Direction.LONG if buy else Direction.SHORT, request["volume"], price, request["sl"],
                            request["tp"], request["magic"], commission=commission)
            self.balance += commission
            self.requests.append(request)
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=int(pid), deal=int(pid) + 10_000, price=price,
                                   comment="")
        return super().order_send(request)

    def fill(self, ticket, price=None):
        super().fill(ticket, price)
        d, p = self.deals[-1], next(x for x in self.positions if x.ticket == ticket)
        d.commission = self.side_commission(p.symbol, float(p.volume), d.price)
        d.fee, d.type, d.volume, d.symbol, d.magic, p.swap = 0.0, p.type, p.volume, p.symbol, p.magic, 0.0
        self.balance += d.commission

    def close_at(self, ticket, price):
        """The server closes the position at ``price`` (its take-profit or its stop): profit, swap and the exit's commission."""
        p = next(x for x in self.positions if x.ticket == ticket)
        self.positions.remove(p)
        kind = self.ORDER_TYPE_BUY if p.type == self.POSITION_TYPE_BUY else self.ORDER_TYPE_SELL
        profit = self.order_calc_profit(kind, p.symbol, p.volume, p.price_open, price)
        commission = self.side_commission(p.symbol, float(p.volume), price)
        self.balance += profit + commission + float(getattr(p, "swap", 0.0) or 0.0)
        self._ticket += 1
        self.deals.append(SimpleNamespace(ticket=self._ticket, position_id=ticket, entry=self.DEAL_ENTRY_OUT,
                                          reason=self.DEAL_REASON_TP, price=price, profit=profit, commission=commission,
                                          swap=float(getattr(p, "swap", 0.0) or 0.0), fee=0.0, time=0, type=1 - p.type,
                                          volume=p.volume, symbol=p.symbol, magic=p.magic))


def _tp(api, ticket) -> float:
    """The take-profit the server holds on position ``ticket``."""
    return next(float(x.tp) for x in api.positions if str(x.ticket) == str(ticket))


def _ftmo(tmp_path, api, symbol="EURUSD", stop=True, lock=True):
    """A window of Max's FTMO set (TARGET=10, STOP_AT_TARGET=1, LOCK_AT_TARGET=1, RISK=1.75) on ``api``: EURUSD with its
    limit 25 % back toward the stop, BTCUSD at a quarter of RISK with market orders."""
    s = _settings(tmp_path, lock=lock, stop=stop)
    s.risk.risk_pct = 1.75
    if symbol == "EURUSD":
        s.risk.limit_entry_fraction, s.risk.limit_entry_minutes = 0.25, 240
    if symbol == "BTCUSD":
        s.risk.stake_multiplier, s.risk.min_rr = 0.25, 0.5
    runner = LiveRunner(s, symbol, lambda: {}, broker=MT5Broker(s, api=api, clock=lambda: NOW),
                        notifier=TelegramNotifier(dry_run=True), engine=FakeEngine(None, signal_on_first_call=False),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    return runner


def _eurusd(setup, stop_pips=10):
    """A 1H EURUSD long at the ask 1.10011, its stop ``stop_pips`` under it, its own target 60 pips over it."""
    stop = round(1.10011 - stop_pips * 0.0001, 5)
    return TradeSetup("EURUSD", Direction.LONG, setup.poi, setup.confirmation, 1.10011, stop, 1.10611, stop_pips * 1e-4, 0.006,
                      6.0, 1.9, 190.0, 4.0, "1H liquidity")


def _trading(runner):
    """This scan's candles show the market trading (the lowest timeframe's bars came from the broker and are fresh)."""
    runner._views = {T.MIN_5: CandleSeries.from_records([(1.1, 1.1, 1.1, 1.1)], T.MIN_5, start=str(NOW), symbol=runner.symbol)}


# ------------------------------------------------------------------ the lock does nothing once the target stands

def test_the_fourth_days_finish_trade_goes_out_with_its_own_target_and_fills(setup, tmp_path):
    """The review's scenario: the target stands (11,050) with three days logged; the fourth day's setup takes the finish
    stake. It went out with its take-profit one tick past the ask, and a quote that moved two ticks while it travelled
    made the server refuse it (10016): no position, no fourth day. Now it carries its own target and fills."""
    api = BookingMT5(11_050.0, drift=2)
    api.days(_earlier(3))
    api.quotes["EURUSD"] = (1.10000, 1.10001)
    runner = _ftmo(tmp_path, api)
    runner.settings.risk.limit_entry_fraction = 0.0                            # a market order, as gold and BTC send
    runner._scan_id += 1
    pos = runner.execute(setup, None, NOW)
    assert pos is not None and pos.take_profit == 1.12 and pos.lots == pytest.approx(0.02)
    assert len(api.positions) == 1 and _rows(runner, "not_executed").empty


def test_the_lock_without_stop_at_target_leaves_a_full_trade_its_own_target(setup, tmp_path):
    """--lock-at-target without --stop-at-target: once the target stands the windows trade on at the full stake, and such
    a trade used to get a take-profit one tick past its entry (break-even "after costs") with its full stop. The lock does
    nothing once the target stands, so the trade keeps its own target, as without the lock."""
    runner, broker, _ = _paper(setup, tmp_path, 11_050.0, 4, stop=False)
    pos = runner.execute(setup, None, NOW)
    assert pos.risk_amount > 150.0 and pos.take_profit == 1.12
    _scan(runner)
    assert broker.open_positions()[0].take_profit == 1.12


# ------------------------------------------------------------------ a market order carries the lock only clear of the price

def test_a_lock_near_the_price_is_set_by_the_first_scan_not_on_the_market_order(setup, tmp_path):
    """9 to go on 0.32 lots puts the lock 0.4 pips over the bid, inside a tenth of the 51-pip stop: a quote that moves
    while the order travels could void the entry, so the order carries its own target and the first scan sets the lock."""
    runner, broker, _ = _paper(setup, tmp_path, 10_996.0, 4)
    pos = runner.execute(setup, None, NOW)
    assert pos.take_profit == 1.12 and pos.id not in runner.own_targets
    _scan(runner)
    tp = broker.open_positions()[0].take_profit
    assert tp < 1.11 and broker.pnl_for("EURUSD", Direction.LONG, pos.entry, tp, pos.lots) >= 9.0 - 1e-6


def test_an_order_refused_for_its_locked_take_profit_goes_out_again_with_its_own_target(setup, tmp_path):
    """The quote runs 16 pips while the order travels, past the lock's level: the server refuses it (10016) and the window
    sends it once more with its own target; the first scan after the fill sets the lock from the new entry."""
    api = BookingMT5(10_950.0, drift=160)
    api.days(_earlier(4))
    api.quotes["EURUSD"] = (1.10000, 1.10001)
    runner = _ftmo(tmp_path, api)
    runner.settings.risk.limit_entry_fraction = 0.0
    runner._scan_id += 1
    pos = runner.execute(setup, None, NOW)
    deals = [r for r in api.requests if r.get("action") == api.TRADE_ACTION_DEAL]
    assert len(deals) == 2 and deals[0]["tp"] < 1.12 and deals[1]["tp"] == 1.12
    assert pos is not None and pos.take_profit == 1.12 and _rows(runner, "not_executed").empty
    assert "target lock refused at the order" in _rows(runner, "filled").iloc[0].note
    _scan(runner)
    assert _tp(api, pos.id) < 1.12 and runner.own_targets[pos.id]["take_profit"] == 1.12


# ------------------------------------------------------------------ the costs

def test_a_locked_limit_that_runs_to_its_level_before_the_next_scan_reaches_the_target(setup, tmp_path):
    """10 under the target with the fourth day: the limit's lock counted no commission, and a fill that ran to it before
    the next scan closed at 10,999.04 after the round turn the server books (6.78 on 2.26 lots). Now the order counts
    FTMO's documented round turn until the account has closed a EURUSD trade, and then what that one paid."""
    api = BookingMT5(10_990.0)
    api.days(_earlier(3))
    runner = _ftmo(tmp_path, api)
    runner.execute(_eurusd(setup), None, NOW)
    oid, info = next(iter(runner.limits.items()))
    assert info["lock_tp"] < info["take_profit"]
    api.fill(int(oid))
    api.close_at(int(oid), _tp(api, oid))
    assert api.balance >= 11_005.0                                             # FTMO's 5.00 a lot over-counts the 3.00 here

    api2 = BookingMT5(10_990.0)                                                # a EURUSD trade closed on the account before
    api2.days(_earlier(3))
    first = api2.hold("EURUSD", Direction.LONG, 1.0, 1.1, 1.098, 1.106, 7, commission=-1.5, when=NOW - pd.Timedelta(days=1))
    api2.close_at(int(first), 1.1)
    api2.balance = 10_990.0
    runner2 = _ftmo(tmp_path / "b", api2)
    runner2.execute(_eurusd(setup), None, NOW)
    oid2 = next(iter(runner2.limits))
    api2.fill(int(oid2))
    api2.close_at(int(oid2), _tp(api2, oid2))
    assert 11_005.0 - 1e-6 <= api2.balance < 11_006.0                          # its 3.00 a lot: the goal, to the tick


def test_a_btc_order_counts_its_round_turn(setup, tmp_path):
    """BTCUSD at a quarter of RISK, the margin cap holding it at 0.08 lots: the round turn on 8,800 of notional (5.72) is
    over the 5 of buffer; counted at the order, the take-profit closes at the goal."""
    api = BookingMT5(10_990.0)
    api.days(_earlier(3))
    runner = _ftmo(tmp_path, api, symbol="BTCUSD")
    btc = TradeSetup("BTCUSD", Direction.LONG, setup.poi, setup.confirmation, 110_025.0, 109_525.0, 112_025.0, 500.0, 2000.0,
                     4.0, 0.1, 48.0, 4.0, "1H liquidity")
    pos = runner.execute(btc, None, NOW)
    assert pos.meta.get("own_take_profit") == 112_025.0 and pos.lots == pytest.approx(0.08)
    api.close_at(int(pos.id), _tp(api, pos.id))
    assert api.balance >= 11_004.9                                             # the exit's 0.0325 % is on its higher price


def test_a_lock_counts_the_other_open_positions_closing_costs(tmp_path):
    """Two windows of one account. EURUSD A's lock counts gold B's exit commission and its 12 of swap: once A closes at its
    lock the target stands, B keeps its own target, and B leaving at its break-even stop leaves the balance over it."""
    api = BookingMT5(10_800.0)
    api.days(_earlier(4))
    eur, gold = _ftmo(tmp_path / "eur", api), _ftmo(tmp_path / "gold", api, symbol="XAUUSD")
    a = api.hold("EURUSD", Direction.LONG, 2.0, 1.1, 1.098, 1.106, eur.broker.magic, commission=-3.0)
    b = api.hold("XAUUSD", Direction.LONG, 0.5, 4000.0, 4000.0, 4030.0, eur.broker.magic, commission=0.0, swap=-12.0)
    api.quotes["EURUSD"], api.quotes["XAUUSD"] = (1.1001, 1.10011), (3999.5, 3999.8)
    _scan(eur)
    _scan(gold)
    api.close_at(int(a), _tp(api, a))
    assert api.balance >= 11_005.0 + 12.0 - 1e-6
    _scan(gold, 1)
    assert _tp(api, b) == 4030.0                                              # the target stands: its own target again
    api.close_at(int(b), 4000.0)
    assert api.balance >= 11_005.0 - 1e-6


# ------------------------------------------------------------------ the server's answers

@pytest.mark.parametrize("reply", ["timeout", "none"])
def test_a_move_whose_reply_was_lost_stays_the_locks_level(tmp_path, reply):
    """The server takes the move but its answer is lost (10012, or no reply): the next scan finds the lock's level on the
    server and keeps it as the lock's, not as a target moved by hand; a loss elsewhere then moves it back out to the
    trade's own target. No refusal message: the scan sees what the server did."""
    runner, api, notifier = _mt5(tmp_path, "EURUSD", 10_800.0)
    api.days(_earlier(4))
    pid = api.hold("EURUSD", Direction.LONG, 2.0, 1.1, 1.098, 1.1015, runner.broker.magic, commission=-3.0)
    send, lost = api.order_send, [True]

    def answer_lost(request):
        result = send(request)                                                 # the server applies it...
        if request["action"] == api.TRADE_ACTION_SLTP and lost:
            lost.clear()                                                       # ...and its answer is lost, once
            return None if reply == "none" else SimpleNamespace(retcode=10012, order=0, deal=0, price=0.0, comment="Timeout")
        return result
    api.order_send = answer_lost
    _scan(runner)
    assert _tp(api, pid) == pytest.approx(1.10104) and runner.own_targets[pid].get("tried") == pytest.approx(1.10104)
    _scan(runner, 2)
    assert runner.own_targets[pid]["take_profit"] == 1.1015 and runner.own_targets[pid]["set"] == pytest.approx(1.10104)
    api.balance = 10_581.0                                                     # another market's 4H trade lost 2.19 %
    _scan(runner, 3)
    assert _tp(api, pid) == pytest.approx(1.1015)
    assert not any("geweigerd" in m for m in notifier.sent)


def test_a_shut_market_is_tried_again_when_it_trades_and_a_traded_level_closes_meanwhile(tmp_path):
    """The rollover books a swap in gold's daily break: the move it calls for is refused (10018), quietly, and tried again
    at the first scan whose candles show gold trading, not 15 minutes later. And while a refused move waits, a lock price
    that has traded closes the position at the market."""
    api = BookingMT5(10_977.46)
    api.days(_earlier(15))
    api.quotes["XAUUSD"] = (3340.265, 3340.465)
    runner = _ftmo(tmp_path, api, symbol="XAUUSD")
    pid = api.hold("XAUUSD", Direction.LONG, 0.18, 3340.465, 3327.28, 3366.42, runner.broker.magic)
    _scan(runner)
    assert _tp(api, pid) == pytest.approx(3342.00)
    send, shut = api.order_send, [True]

    def market(request):
        if shut[0]:
            return SimpleNamespace(retcode=10018, order=0, deal=0, price=0.0, comment="Market closed")
        return send(request)
    api.order_send = market
    next(x for x in api.positions if str(x.ticket) == pid).swap = -10.0
    for minute in (1, 2, 3):
        _scan(runner, minute)
    assert _tp(api, pid) == pytest.approx(3342.00) and not any("geweigerd" in m for m in runner.notifier.sent)
    shut[0] = False
    _scan(runner, 4)                                                           # still no fresh candles: it waits
    assert _tp(api, pid) == pytest.approx(3342.00)
    _trading(runner)
    _scan(runner, 5)                                                           # gold trades again: at once
    assert _tp(api, pid) == pytest.approx(3342.56)

    runner._lock_retry[pid] = {"tries": 3, "at": NOW + pd.Timedelta(minutes=30), "shut": False, "told": True}
    api.quotes["XAUUSD"] = (3343.0, 3343.2)                                    # past the level during a refused move's wait
    _scan(runner, 6)
    assert api.positions == [] and _rows(runner, "target_lock_exit").iloc[0].id == pid


# ------------------------------------------------------------------ the days, the switch, the lots, the records

def test_a_short_history_read_does_not_count_the_trades_own_day_twice(setup, tmp_path):
    """Three trading days, today's among them, and a position opened today. A terminal that has just restarted lists no
    deals yet: the day count stays three and today is not counted again on top, so no lock on the third day."""
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 3, dates=_earlier(2) + [TODAY])
    pos = _hold(broker)
    _scan(runner)
    broker.trading_dates = lambda tz="Europe/Prague": set()
    _scan(runner, 1)
    assert pos.take_profit == 1.12 and not any("🔐" in m for m in notifier.sent)
    broker.trading_dates = lambda tz="Europe/Prague": set(_earlier(3) + [TODAY])   # the next day's trade elsewhere
    _scan(runner, 2)
    assert pos.take_profit == pytest.approx(1.1035)


def test_switched_off_a_lock_goes_back_to_the_trades_own_target(setup, tmp_path):
    """Locked, then the window restarts with the switch deleted (and a loss elsewhere): the take-profit the lock left goes
    back to the trade's own target once, a resting limit's too, and the records go. One moved by hand since stays."""
    runner, broker, _ = _paper(setup, tmp_path, 10_900.0, 4)
    pos, other = _hold(broker), _hold(broker, lots=0.2)
    runner.limits["L1"] = {"sid": "x", "direction": "LONG", "price": 1.098, "stop": 1.093, "take_profit": 1.12, "lots": 0.3,
                           "risk_amount": 150.0, "placed_at": NOW, "expires_at": NOW + pd.Timedelta(hours=4)}
    broker.limits["L1"] = SimpleNamespace(take_profit=1.12)
    _scan(runner)
    assert pos.take_profit < 1.12 and other.take_profit < 1.12 and runner.limits["L1"]["lock_tp"] is not None
    runner.save_limits()
    other.take_profit = 1.115                                                  # Max moves this one in MT5
    off, _, notifier = _paper(setup, tmp_path, 10_300.0, 4, broker=broker, lock=False)
    _scan(off)
    assert pos.take_profit == 1.12 and other.take_profit == 1.115
    assert off.own_targets == {} and off.limits["L1"]["lock_tp"] is None and broker.limits["L1"].take_profit == 1.12
    assert sum("doel-lock uit" in m for m in notifier.sent) == 1
    calls = []
    broker.modify_take_profit = lambda *a: calls.append(a)
    _scan(off, 1)
    assert calls == []                                                          # once


def test_a_position_partly_closed_by_hand_is_locked_on_what_is_left(tmp_path):
    """Max closes half of a 2-lot position in MT5: the window reads the server's volume, so the lock prices the 455 still
    needed on the 1 lot left (and its exit commission on that lot), not on 2."""
    runner, api, _ = _mt5(tmp_path, "EURUSD", 10_500.0)
    api.days(_earlier(4))
    pid = api.hold("EURUSD", Direction.LONG, 2.0, 1.1, 1.098, 1.106, runner.broker.magic, commission=-3.0)
    _scan(runner)
    p = next(x for x in api.positions if str(x.ticket) == pid)
    p.volume = 1.0
    api.balance += 50.0
    _scan(runner, 1)
    assert runner.broker.open_positions("EURUSD")[0].lots == 1.0
    assert api.order_calc_profit(api.ORDER_TYPE_BUY, "EURUSD", 1.0, 1.1, _tp(api, pid)) - 1.5 >= 455.0 - 1e-6


def test_a_locked_limit_filled_and_closed_before_the_scan_keeps_its_lock_in_the_records(setup, tmp_path):
    """A limit resting with the lock's take-profit fills and reaches it before the next scan: the journal says the lock
    (a target_lock row, the fill's take-profit the lock's), so the forward record measures no exit slippage and the
    parity check names the lock."""
    from kronos_trader.forward import reconcile
    from kronos_trader.live import short_id_for
    from kronos_trader.parity import live_side
    api = BookingMT5(10_800.0)
    api.days(_earlier(3))
    runner = _ftmo(tmp_path, api)
    st = _eurusd(setup)
    sid = short_id_for((st.poi.key, str(st.confirmation.timestamp)))
    runner.note("setup", NOW, id=sid, direction="LONG", entry=st.entry, stop=st.stop, take_profit=st.take_profit, rr=st.rr)
    runner.execute(st, None, NOW)
    oid, info = next(iter(runner.limits.items()))
    lock_tp = float(info["lock_tp"])
    api.fill(int(oid))
    api.close_at(int(oid), lock_tp)
    runner._scan_id += 1
    runner.manage_limits(NOW + pd.Timedelta(minutes=31))
    runner.report_closes()
    journal = pd.read_csv(runner.settings.live.journal_path, dtype={"id": str})
    journal["time"] = pd.to_datetime(journal["time"])
    assert float(journal[journal.event == "target_lock"].iloc[-1].take_profit) == pytest.approx(lock_tp)
    assert float(journal[journal.event == "filled"].iloc[0].take_profit) == pytest.approx(lock_tp)
    deals = pd.DataFrame([{"time": NOW + pd.Timedelta(minutes=30 + k), "position_id": int(d.position_id), "type": int(d.type),
                           "entry": int(d.entry), "price": float(d.price), "volume": float(d.volume), "profit": float(d.profit),
                           "commission": float(d.commission), "swap": 0.0, "fee": 0.0, "reason": int(d.reason),
                           "symbol": "EURUSD", "magic": runner.broker.magic}
                          for k, d in enumerate(api.deals) if getattr(d, "magic", 0) == runner.broker.magic])
    row = reconcile(journal, deals).iloc[0]
    assert row.exit_reason == "take_profit" and row.exit_slip == pytest.approx(0.0, abs=1e-9)
    assert live_side(journal, "EURUSD", NOW - pd.Timedelta(days=1), NOW + pd.Timedelta(days=1))[sid].locked


def test_a_close_at_the_lock_is_read_by_the_rest_of_the_scan(setup, tmp_path):
    """A limit record made the scan read the target state (under the target) before the lock closed a position at its
    traded level and carried the balance over it: the rest of the scan reads it again, so the stop at the target refuses
    a new setup in the same scan."""
    runner, broker, _ = _paper(setup, tmp_path, 10_900.0, 4, stop=True)
    _hold(broker)
    runner.limits["L1"] = {"sid": "x", "direction": "LONG", "price": 1.09, "stop": 1.08, "take_profit": 1.2, "lots": 0.1,
                           "risk_amount": 100.0, "placed_at": NOW, "expires_at": NOW + pd.Timedelta(hours=4)}
    broker.limit_state = lambda oid: ("filled", None)
    broker.set_price("EURUSD", 1.1040)
    runner._scan_id += 1
    runner.manage_limits(NOW)
    runner.manage_target_lock(NOW)
    assert broker.balance() >= 11_005.0 and broker.open_positions() == []
    ok, why = runner._can_open(setup, NOW)
    assert not ok and "target +10 % stands" in why

