"""prop_firm.lock_at_target (16 October, option B, Max: "Oké dan doen we B"): once the phase has its trading days (the
trade's own day counted) a trade takes profit where its close brings the closed balance to the target plus the buffer,
after its costs, when that is nearer than its own target; at the order and every scan; off by default."""
import math
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Candle, CandleSeries, Direction, Timeframe as T
from kronos_trader.execution import PaperBroker
from kronos_trader.execution.mt5 import MT5Broker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from kronos_trader.strategy.risk import target_lock_price
from tests.trader.test_live import FakeEngine, NOW, setup  # noqa: F401  (the setup fixture lives there)
from tests.trader.test_mt5 import LimitMT5, server_seconds

ROOT = Path(__file__).resolve().parents[2]
TODAY = pd.Timestamp(NOW).tz_localize("UTC").tz_convert("Europe/Prague").date()


def _earlier(n: int):
    return [TODAY - pd.Timedelta(days=k) for k in range(1, n + 1)]


def _settings(tmp_path, lock=True, target=10.0, stop=False) -> Settings:
    s = Settings()
    s.account_size = 10_000.0
    s.risk.risk_pct, s.risk.target_pct = 1.5, target
    s.prop_firm.lock_at_target, s.prop_firm.stop_at_target = lock, stop
    s.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    return s


def _paper(setup, tmp_path, balance, days, dates="earlier", broker=None, **kw):
    """A paper window of a 10k account at ``balance`` with ``days`` trading days logged; ``dates`` the dates the account
    lists ("earlier": ``days`` days before today; None: the broker cannot list them)."""
    s = _settings(tmp_path, **kw)
    if broker is None:
        broker = PaperBroker(s)
        broker.set_price("EURUSD", 1.1)
    broker._balance = balance
    broker.trading_days = lambda tz="Europe/Prague": days
    listed = _earlier(days) if dates == "earlier" else dates
    broker.trading_dates = lambda tz="Europe/Prague": None if listed is None else set(listed)
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(s, "EURUSD", lambda: {}, broker=broker, notifier=notifier,
                        engine=FakeEngine(setup, signal_on_first_call=False), dry_run=False, require_approval=False,
                        clock=lambda: NOW)
    return runner, broker, notifier


def _hold(broker, direction=Direction.LONG, lots=0.3, entry=1.1, tp=None):
    """A position of the window: 0.3 lots from 1.1000, stop 51 pips away, its own target 200 pips away."""
    stop = entry - direction.sign * 0.0051
    tp = entry + direction.sign * 0.02 if tp is None else tp
    return broker.place_market_order("EURUSD", direction, lots, stop, tp, 153.0, 0.0051, 4.0, price=entry,
                                     ts=NOW - pd.Timedelta(hours=1), price_is_fill=True)


def _scan(runner, minutes=0):
    runner._scan_id += 1                                 # what step() does: the account read again
    runner.manage_target_lock(NOW + pd.Timedelta(minutes=minutes))


def _rows(runner, event):
    path = Path(runner.settings.live.journal_path)
    rows = pd.read_csv(path, dtype={"id": str}) if path.exists() else pd.DataFrame(columns=["event"])
    return rows[rows["event"] == event]


# ------------------------------------------------------------------ off

def test_off_by_default_and_without_a_target(capsys):
    assert Settings().prop_firm.lock_at_target is False and Settings().prop_firm.lock_buffer_pct == 0.05
    from kronos_trader.cli import live_settings
    base = dict(config=str(ROOT / "config" / "dorus_live.yaml"), symbol="EURUSD", lock_at_target=True)
    s, _ = live_settings(SimpleNamespace(**base, target_pct=None))
    assert s.prop_firm.lock_at_target is False and "--lock-at-target needs the phase's target" in capsys.readouterr().out
    s, _ = live_settings(SimpleNamespace(**base, target_pct=5.0))
    assert s.prop_firm.lock_at_target is True
    s, _ = live_settings(SimpleNamespace(config=base["config"], symbol="EURUSD", target_pct=10.0))
    assert s.prop_firm.lock_at_target is False                                  # no flag: off


def test_the_switch_off_changes_nothing(setup, tmp_path):
    """Off (or without a target), with the phase's days logged and the balance just under the target: the order carries the
    setup's own target, a scan sends nothing to the broker and writes nothing."""
    for kw in ({"lock": False}, {"lock": True, "target": 0.0}):
        runner, broker, notifier = _paper(setup, tmp_path / str(len(kw)), 10_990.0, 6, **kw)
        calls = []
        broker.modify_take_profit = lambda *a: calls.append(a)
        broker.modify_limit_take_profit = lambda *a: calls.append(a)
        broker.balance = lambda: calls.append("balance") or 10_990.0
        pos = runner.execute(setup, None, NOW)
        assert pos.take_profit == setup.take_profit == 1.12
        calls.clear()
        _scan(runner)
        assert calls == [] and runner.target_lock_state() is None and runner.own_targets == {}
        assert not any("🔐" in m for m in notifier.sent) and _rows(runner, "target_lock").empty
        assert not (Path(runner.settings.live.journal_path).parent / "target_lock_EURUSD.json").exists()


# ------------------------------------------------------------------ the price

def test_the_price_rounds_away_from_the_entry_and_never_reaches_past_the_own_target():
    assert target_lock_price(Direction.LONG, 1.1, 1.106, 600.0, 250.0, 0.00001) == 1.1025
    assert target_lock_price(Direction.SHORT, 1.1, 1.094, 600.0, 250.0, 0.00001) == 1.0975
    assert target_lock_price(Direction.LONG, 4000.37, 4030.0, 1000.0, 333.3, 0.01) == 4010.25   # 4010.2458: up, never down
    assert target_lock_price(Direction.SHORT, 4000.37, 3970.0, 1000.0, 333.3, 0.01) == 3990.24  # 3990.2477: down
    assert target_lock_price(Direction.LONG, 1.1, 1.106, 600.0, 0.0, 0.00001) == 1.10001       # at least a tick: never
    assert target_lock_price(Direction.SHORT, 1.1, 1.094, 600.0, 0.0, 0.00001) == 1.09999      # at the entry or behind it
    assert target_lock_price(Direction.LONG, 1.1, 1.106, 600.0, 600.0, 0.00001) is None        # the own target as near
    assert target_lock_price(Direction.LONG, 1.1, 1.106, 600.0, 700.0, 0.00001) is None        # or nearer
    assert target_lock_price(Direction.LONG, 1.1, 1.10001, 600.0, 599.0, 0.00001) is None      # rounds onto it


class AccountMT5(LimitMT5):
    """An FTMO 10k account on the four markets: each symbol's contract and tick, its own quote, the server's profit maths,
    a stops level, and the lock's requests (TRADE_ACTION_SLTP on a position, TRADE_ACTION_MODIFY on a resting limit)."""
    TRADE_ACTION_MODIFY = 7
    CONTRACT = {"EURUSD": 100_000.0, "XAUUSD": 100.0, "US100.cash": 1.0, "BTCUSD": 1.0}
    TICK = {"EURUSD": 0.00001, "XAUUSD": 0.01, "US100.cash": 0.01, "BTCUSD": 0.01}
    known = tuple(CONTRACT)

    def __init__(self, balance=10_000.0, stops_level=0):
        super().__init__()
        self.balance, self.stops_level = balance, stops_level
        self.quotes = {"EURUSD": (1.1001, 1.10011), "XAUUSD": (4000.2, 4000.5), "US100.cash": (25001.0, 25002.5),
                       "BTCUSD": (110010.0, 110025.0)}

    def account_info(self):
        return SimpleNamespace(login=1, server="FTMO-Demo", currency="USD", balance=self.balance, equity=self.balance,
                               leverage=100, trade_mode=0, margin_free=self.balance)

    def symbol_info(self, name):
        if name not in self.CONTRACT:
            return None
        return SimpleNamespace(description=name, digits=round(-math.log10(self.TICK[name])), point=self.TICK[name],
                               trade_tick_size=self.TICK[name], trade_contract_size=self.CONTRACT[name],
                               trade_stops_level=self.stops_level, trade_freeze_level=0, volume_min=0.01, volume_step=0.01,
                               volume_max=100.0, trade_mode=4, currency_profit="USD", spread=10, expiration_mode=0)

    def symbol_info_tick(self, name):
        bid, ask = self.quotes[name]
        return SimpleNamespace(bid=bid, ask=ask, time=server_seconds(NOW))

    def order_calc_profit(self, kind, name, lots, open_price, close_price):
        return (1 if kind == self.ORDER_TYPE_BUY else -1) * (close_price - open_price) * lots * self.CONTRACT[name]

    def order_send(self, request):
        if request["action"] == self.TRADE_ACTION_MODIFY:
            self.requests.append(request)
            order = next(o for o in self.orders if o.ticket == request["order"])
            order.tp = request["tp"]
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=order.ticket, deal=0, price=0.0, comment="")
        return super().order_send(request)

    def hold(self, name, direction, lots, entry, sl, tp, magic, commission=0.0, swap=0.0, when=NOW):
        """A position of the bot on the server, with its entry deal (and that deal's commission)."""
        self._ticket += 1
        t = self._ticket
        side = self.POSITION_TYPE_BUY if direction is Direction.LONG else self.POSITION_TYPE_SELL
        self.positions.append(SimpleNamespace(ticket=t, identifier=t, symbol=name, type=side, volume=lots, price_open=entry,
                                              sl=sl, tp=tp, time=server_seconds(when), magic=magic, comment="1HPOI BS",
                                              profit=0.0, swap=swap))
        self.deals.append(SimpleNamespace(ticket=t + 10_000, position_id=t, entry=self.DEAL_ENTRY_IN, reason=0, price=entry,
                                          profit=0.0, commission=commission, swap=0.0, fee=0.0, time=server_seconds(when),
                                          type=side, volume=lots, symbol=name, magic=magic, comment=""))
        return str(t)

    def days(self, dates):
        """Entry deals of other trades on these Prague days (the account's trading days)."""
        for d in dates:
            when = pd.Timestamp(d) + pd.Timedelta(hours=8)                   # 10:00 in Prague
            self.deals.append(SimpleNamespace(ticket=len(self.deals) + 90_000, position_id=1, entry=self.DEAL_ENTRY_IN,
                                              reason=0, price=1.0, profit=0.0, commission=0.0, swap=0.0, fee=0.0,
                                              time=server_seconds(when), type=0, volume=0.01, symbol="EURUSD", magic=0))


def _mt5(tmp_path, symbol, balance, target=10.0, stops_level=0):
    s = _settings(tmp_path, target=target)
    s.symbols["NAS100"].mt5_symbol = "US100.cash"
    api = AccountMT5(balance, stops_level)
    broker = MT5Broker(s, api=api, clock=lambda: NOW)
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(s, symbol, lambda: {}, broker=broker, notifier=notifier, engine=FakeEngine(None, signal_on_first_call=False),
                        dry_run=False, clock=lambda: NOW)
    return runner, api, notifier


# market, server name, lots, entry, own target distance, entry commission, swap, long price, short price
MARKETS = [("EURUSD", "EURUSD", 2.0, 1.1, 0.006, -3.0, -1.2, 1.10105, 1.09895),           # 205 + 3.00 + 1.20
           ("XAUUSD", "XAUUSD", 0.5, 4000.0, 30.0, -0.75, 0.0, 4004.12, 3995.88),         # 205 + 0.75
           ("NAS100", "US100.cash", 3.0, 25000.0, 300.0, 0.0, -2.5, 25069.17, 24930.83),  # 205 + 2.50, the 0.01 grid
           ("BTCUSD", "BTCUSD", 0.1, 110000.0, 3000.0, -3.575, 0.0, 112085.75, 107914.25)]   # 205 + 0.0325 % a side


@pytest.mark.parametrize("market", MARKETS, ids=[m[0] for m in MARKETS])
@pytest.mark.parametrize("direction", [Direction.LONG, Direction.SHORT], ids=["long", "short"])
def test_the_lock_price_on_each_markets_contract(tmp_path, market, direction):
    """Balance 10,800 of 10,000, target +10 %, buffer 0.05 %: the close must bring 205 plus the exit's commission (the
    entry deal's again) and the accrued swap. The take-profit lands on the price that nets that, rounded away from the
    entry onto the server's tick; the stop goes along unchanged."""
    symbol, name, lots, entry, distance, commission, swap, long_price, short_price = market
    runner, api, notifier = _mt5(tmp_path, symbol, 10_800.0)
    api.days(_earlier(3))
    sign = direction.sign
    stop, own = entry - sign * distance / 3, entry + sign * distance
    pid = api.hold(name, direction, lots, entry, stop, own, runner.broker.magic, commission=commission, swap=swap)
    if direction is Direction.SHORT:                                           # a short is in profit a little too
        bid, ask = api.quotes[name]
        api.quotes[name] = (2 * entry - ask, 2 * entry - bid)
    _scan(runner)
    want = long_price if direction is Direction.LONG else short_price
    p = next(x for x in api.positions if str(x.ticket) == pid)
    assert p.tp == pytest.approx(want, abs=1e-9) and p.sl == stop
    req = api.requests[-1]
    assert (req["action"], req["position"], req["sl"], req["tp"]) == (api.TRADE_ACTION_SLTP, int(pid), stop, p.tp)
    costs = abs(commission) + max(0.0, -swap)
    gain = lambda price: sign * (price - entry) * lots * api.CONTRACT[name]
    tick = api.TICK[name]
    assert gain(want) - costs >= 205.0 - 1e-6 > gain(want - sign * tick) - costs      # the nearest tick that reaches the goal
    assert runner.own_targets[pid]["take_profit"] == own
    assert sum("🔐" in m for m in notifier.sent) == 1


# ------------------------------------------------------------------ the days, the own target, the balance

def test_the_order_carries_the_lock_and_the_setup_keeps_its_own_target(setup, tmp_path):
    """Balance 10,900 with four days logged: the market order goes out with the price that nets the 105 left (0.31 lots
    from the ask 1.10005), after the R:R check on the setup's own target (1:3.8 there; the lock's would be 1:0.7)."""
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 4)
    pos = runner.execute(setup, None, NOW)
    assert pos.lots == pytest.approx(0.31) and pos.entry == pytest.approx(1.10005)
    assert pos.take_profit == pytest.approx(1.10344) and setup.take_profit == 1.12
    assert runner.own_targets[pos.id] == {"take_profit": 1.12, "set": pos.take_profit, "told": True}
    fill = [m for m in notifier.sent if m.startswith("💸")]
    assert len(fill) == 1 and "TP 1.10344" in fill[0] and "Doel-lock" in fill[0] and "eigen doel 1.12000" in fill[0]
    rows = pd.read_csv(runner.settings.live.journal_path)
    assert rows[rows.event == "setup"].empty or (rows[rows.event == "setup"].take_profit == 1.12).all()
    assert "target lock: TP 1.12000 -> 1.10344" in rows[rows.event == "filled"].iloc[0].note
    assert float(rows[rows.event == "target_lock"].iloc[0].take_profit) == pytest.approx(1.10344)
    sent = len(notifier.sent)
    _scan(runner)                                                              # the next scan agrees: nothing sent
    assert broker.open_positions()[0].take_profit == pytest.approx(1.10344) and notifier.sent[sent:] == []


def test_not_before_the_fourth_trading_day_with_the_trades_own_day_counted(setup, tmp_path):
    runner, *_ = _paper(setup, tmp_path / "a", 10_900.0, 3, dates=_earlier(2) + [TODAY])
    assert runner.execute(setup, None, NOW).take_profit == 1.12                # today traded already: still three days
    runner, *_ = _paper(setup, tmp_path / "b", 10_900.0, 3)
    assert runner.execute(setup, None, NOW).take_profit == pytest.approx(1.10344)   # today is the fourth
    runner, broker, _ = _paper(setup, tmp_path / "c", 10_900.0, 3, dates=None)
    pos = runner.execute(setup, None, NOW)                                     # the dates unknown: today is not assumed new
    assert pos.take_profit == 1.12
    _scan(runner)
    assert broker.open_positions()[0].take_profit == 1.12
    broker.trading_days = lambda tz="Europe/Prague": 4                         # the history shows the fourth day
    _scan(runner)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.10344)


def test_the_closed_balance_moving_between_scans_moves_the_lock_never_past_the_own_target(setup, tmp_path):
    """0.3 lots from 1.1000, its own target 1.1200 (600). Under the target by 1,005 the own target is nearer; by 505 the
    lock sits at 1.11684; another market's win leaves 105: 1.10350; a loss elsewhere then leaves 705: back to 1.12."""
    runner, broker, notifier = _paper(setup, tmp_path, 10_000.0, 5)
    pid = _hold(broker).id
    seen = []
    for balance in (10_000.0, 10_500.0, 10_900.0, 10_300.0):
        broker._balance = balance
        _scan(runner, len(seen))
        seen.append(broker.open_positions()[0].take_profit)
    assert seen == [1.12, pytest.approx(1.11684), pytest.approx(1.1035), 1.12]
    rows = _rows(runner, "target_lock")
    assert list(rows.id) == [pid] * 3 and rows.iloc[-1].note.startswith("own target again")
    assert sum("🔐" in m for m in notifier.sent) == 1                          # said once a trade
    assert broker.open_positions()[0].stop == pytest.approx(1.0949)            # the stop never moves


def test_phase_two_aims_at_its_5_pct(setup, tmp_path):
    runner, broker, _ = _paper(setup, tmp_path, 10_400.0, 4, target=5.0)
    _hold(broker)
    _scan(runner)
    assert runner.target_lock_state()["goal"] == pytest.approx(10_505.0)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.1035)      # 105 to go, as at 10,900 in phase 1


def test_a_limit_filling_after_the_balance_changed(setup, tmp_path):
    """The limit rests with the lock's price for the balance when it was placed; a trade elsewhere closes at a loss while it
    rests and the scan moves the order's take-profit; it fills later and the position carries the level for the balance
    at its fill. The limit's own target stays in its record: price trading through the lock level before the fill does
    not cancel it, only the own target does (as the backtest's)."""
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 4)
    runner.settings.risk.limit_entry_fraction, runner.settings.risk.limit_entry_minutes = 0.25, 240
    runner.execute(setup, None, NOW)
    order = broker.limit_orders()[0]
    info = runner.limits[order.id]
    assert order.price == pytest.approx(1.09876) and order.lots == pytest.approx(0.41)          # 105 over 0.41 lots
    assert order.take_profit == pytest.approx(1.10133) and info["take_profit"] == 1.12 and info["lock_tp"] == pytest.approx(1.10133)
    assert any(m.startswith("📌") and "Doel-lock" in m for m in notifier.sent)
    broker._balance = 10_800.0                                                 # another market's trade lost 100
    _scan(runner, 5)
    assert order.take_profit == pytest.approx(1.10376) and info["lock_tp"] == pytest.approx(1.10376)   # 205 to go
    runner._views = {T.MIN_15: CandleSeries.from_records([(1.0995, 1.1051, 1.0990, 1.105)], T.MIN_15, start=str(NOW),
                                                         symbol="EURUSD")}
    assert not runner._target_traded(info)                                     # through the lock's level, not its own target
    runner._views = {T.MIN_15: CandleSeries.from_records([(1.0995, 1.1205, 1.0990, 1.12)], T.MIN_15, start=str(NOW),
                                                         symbol="EURUSD")}
    assert runner._target_traded(info)
    broker.on_candle("EURUSD", Candle(0, NOW + pd.Timedelta(minutes=15), 1.0995, 1.0996, 1.0986, 1.0990))   # it fills
    runner.manage_limits(NOW + pd.Timedelta(minutes=31))
    pos = broker.open_positions()[0]
    assert pos.take_profit == pytest.approx(1.10376) and runner.own_targets[pos.id]["take_profit"] == 1.12
    sent = len(notifier.sent)
    broker._balance = 10_900.0                                                 # a win elsewhere after the fill
    _scan(runner, 32)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.10133)
    assert not any("🔐" in m for m in notifier.sent[sent:])                    # the 📌 message said it already


def test_a_restart_keeps_each_trades_own_target(setup, tmp_path):
    runner, broker, _ = _paper(setup, tmp_path, 10_900.0, 4)
    pid = _hold(broker).id
    _scan(runner)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.1035)
    again, _, notifier = _paper(setup, tmp_path, 10_300.0, 4, broker=broker)   # restarted after a loss elsewhere
    assert again.own_targets[pid] == {"take_profit": 1.12, "set": pytest.approx(1.1035), "told": True}
    _scan(again)
    assert broker.open_positions()[0].take_profit == 1.12                       # its own target, not the lock's 1.1035
    broker._balance = 10_900.0
    _scan(again, 1)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.1035) and not any("🔐" in m for m in notifier.sent)
    (tmp_path / "journal" / "target_lock_EURUSD.json").unlink()               # without the record: the server's level is its own
    third, *_ = _paper(setup, tmp_path, 10_300.0, 4, broker=broker)
    _scan(third)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.1035)


def test_a_target_set_by_hand_becomes_the_trades_own(setup, tmp_path):
    runner, broker, _ = _paper(setup, tmp_path, 10_500.0, 4)
    pos = _hold(broker)
    _scan(runner)
    assert pos.take_profit == pytest.approx(1.11684)
    pos.take_profit = 1.1100                                                   # Max moves it in MT5
    _scan(runner, 1)
    assert pos.take_profit == 1.11 and runner.own_targets[pos.id]["take_profit"] == 1.11


# ------------------------------------------------------------------ at the target, the market, the server

def test_with_stop_at_target_the_target_standing_closes_the_rest_at_break_even_after_costs(setup, tmp_path):
    """The phase's target stands with its days: no new trade (stop_at_target), and an open position's take-profit goes to
    break-even after its costs (a tick past the entry here, no commission), never to the loss side; once its price
    trades there it is closed at the market so the account is flat."""
    runner, broker, notifier = _paper(setup, tmp_path, 11_050.0, 4, stop=True)
    pos = _hold(broker)
    ok, reason = runner._can_open(setup, NOW)
    assert not ok and "target +10 % stands" in reason
    _scan(runner)
    assert pos.take_profit == pytest.approx(1.10001) and pos.stop == pytest.approx(1.0949)
    assert any("het doel +10% staat" in m for m in notifier.sent)
    short = _hold(broker, Direction.SHORT)                                     # never on the loss side for a short either
    _scan(runner, 1)
    assert short.take_profit == pytest.approx(1.09999)
    broker.set_price("EURUSD", 1.1002)                                         # the long's bid 1.10015: past its level
    _scan(runner, 2)
    assert pos.id not in {p.id for p in broker.open_positions()}
    assert _rows(runner, "target_lock_exit").iloc[0].id == pos.id
    runner.report_closes()
    assert any(f"closed (target_lock)" in m for m in notifier.sent) and pos.id not in runner.own_targets


def test_with_stop_at_target_the_finish_stake_trade_on_the_fourth_day(setup, tmp_path):
    """At the target with three days, the next setup takes the finish stake (0.1 %); its own day is the fourth, so it goes
    out with its take-profit at break-even after costs: once it closes the account is flat and the phase passes."""
    runner, broker, _ = _paper(setup, tmp_path, 11_050.0, 3, stop=True)
    pos = runner.execute(setup, None, NOW)
    assert pos.lots == pytest.approx(0.02) and pos.take_profit == pytest.approx(1.10006)
    runner, broker, _ = _paper(setup, tmp_path / "b", 11_050.0, 2, stop=True)  # two days: the fifth is far, no lock
    assert runner.execute(setup, None, NOW).take_profit == 1.12


def test_a_lock_price_traded_already_closes_at_the_market(setup, tmp_path):
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 4)
    pos = _hold(broker)
    broker.set_price("EURUSD", 1.1040)                                         # bid 1.10395, past 1.1035
    _scan(runner)
    assert broker.open_positions() == [] and broker.closed[-1].reason == "target_lock"
    assert broker.closed[-1].pnl >= 105.0
    assert any(m.startswith("🔐") and "gesloten met de doel-lock" in m for m in notifier.sent)


def test_a_refused_move_backs_off_with_one_message(setup, tmp_path):
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 4)
    pos = _hold(broker)
    tries = []

    def frozen(pid, tp):
        tries.append(tp)
        raise RuntimeError("modify take-profit failed: retcode 10029 Frozen")
    broker.modify_take_profit = frozen
    for minute in (0, 0.5, 1, 2, 3, 10, 18):
        _scan(runner, minute)
    assert len(tries) == 4 and pos.take_profit == 1.12                         # 0, 1, 2 and 18 min (15 after the third)
    assert sum("doel-lock" in m and "geweigerd" in m for m in notifier.sent) == 1
    assert len(_rows(runner, "target_lock_failed")) == 1


def test_the_servers_stops_level(tmp_path):
    """A level the server would refuse (inside its stops distance from the price) is not sent: an order goes out with its own
    target and a position keeps its take-profit until the level can be set or has traded."""
    runner, api, _ = _mt5(tmp_path, "EURUSD", 10_800.0, stops_level=100)       # 0.00100 from the price
    api.days(_earlier(4))
    pid = api.hold("EURUSD", Direction.LONG, 2.0, 1.1, 1.098, 1.106, runner.broker.magic, commission=-3.0, swap=-1.2)
    api.quotes["EURUSD"] = (1.1001, 1.10011)                                   # 1.10105 is 0.00095 away
    _scan(runner)
    assert api.positions[-1].tp == 1.106 and not any(r.get("action") == api.TRADE_ACTION_SLTP for r in api.requests)
    api.quotes["EURUSD"] = (1.10000, 1.10001)                                  # 0.00105 away: allowed
    _scan(runner, 1)
    assert api.positions[-1].tp == pytest.approx(1.10105)
    api.stops_level, runner._scan_id = 110, runner._scan_id + 1               # an order: 1.10104 is 0.00104 from the bid
    assert runner._order_lock(Direction.LONG, 1.10001, 2.0, 1.106, NOW) is None
    api.stops_level, runner._scan_id = 0, runner._scan_id + 1
    assert runner._order_lock(Direction.LONG, 1.10001, 2.0, 1.106, NOW)[0] == pytest.approx(1.10104)


def test_a_resting_limit_on_mt5_is_moved_with_its_price_stop_and_expiry(tmp_path):
    runner, api, _ = _mt5(tmp_path, "EURUSD", 10_800.0)
    api.days(_earlier(4))
    broker = runner.broker
    order = broker.place_limit_order("EURUSD", Direction.LONG, 2.0, 1.0990, 1.0950, 1.1100, 800.0, 0.004, 4.0,
                                     NOW + pd.Timedelta(hours=4), meta={"comment": "1HPOI BS L"}, ts=NOW)
    runner.limits[order.id] = {"sid": "abcd1234", "direction": "LONG", "price": 1.0990, "stop": 1.0950, "take_profit": 1.11,
                               "lots": 2.0, "risk_amount": 800.0, "placed_at": NOW, "expires_at": NOW + pd.Timedelta(hours=4)}
    _scan(runner)
    req = api.requests[-1]
    assert (req["action"], req["order"], req["price"], req["sl"]) == (7, int(order.id), 1.099, 1.095)
    assert req["tp"] == pytest.approx(1.10003) and req["type_time"] == api.ORDER_TIME_GTC     # 205 over 2 lots, no commission yet
    assert api.orders[0].tp == pytest.approx(1.10003) and runner.limits[order.id]["take_profit"] == 1.11


def test_mt5_reads_the_days_dates_and_costs(tmp_path):
    runner, api, _ = _mt5(tmp_path, "EURUSD", 10_800.0)
    api.days(_earlier(2))
    pid = api.hold("EURUSD", Direction.LONG, 2.0, 1.1, 1.098, 1.106, runner.broker.magic, commission=-3.0, swap=-1.2)
    broker = runner.broker
    assert broker.trading_dates("Europe/Prague") == set(_earlier(2)) | {TODAY} and broker.trading_days() == 3
    pos = broker.open_positions("EURUSD")[0]
    assert broker.closing_costs(pos) == pytest.approx(4.2)
    pos.meta["swap"] = 2.5                                                     # a swap paid to the account is not counted
    assert broker.closing_costs(pos) == pytest.approx(3.0)
    assert broker.price_rules("EURUSD") == (0.00001, 0.0, 0.0)
    broker.modify_take_profit(pid, 1.1033)
    assert api.requests[-1] == {"action": 6, "position": int(pid), "symbol": "EURUSD", "sl": 1.098, "tp": 1.1033,
                                "magic": broker.magic}
    with pytest.raises(KeyError):
        broker.modify_take_profit("999", 1.2)



def test_a_scan_sends_the_locked_order_and_a_failing_lock_never_stops_it(setup, tmp_path):
    runner, broker, notifier = _paper(setup, tmp_path, 10_900.0, 4)
    runner.engine = FakeEngine(setup)                                          # a signal on the first scan

    def broken(now):
        raise RuntimeError("a bug in the lock")
    runner.manage_target_lock = broken
    runner.step(NOW)
    assert broker.open_positions()[0].take_profit == pytest.approx(1.10344)
    assert any("a bug in the lock" in m for m in notifier.sent)


def test_the_morning_check_says_what_the_lock_does(setup, tmp_path):
    runner, *_ = _paper(setup, tmp_path, 10_900.0, 3)
    lines = runner.briefing_extras(runner.engine.analyze("EURUSD", {}, now=NOW), NOW)
    assert any(x.startswith("🔐 Doel-lock aan (3 van 4 handelsdagen)") and "nog 105 te gaan" in x for x in lines)
    runner, *_ = _paper(setup, tmp_path / "b", 11_050.0, 4, stop=True)
    lines = runner.briefing_extras(runner.engine.analyze("EURUSD", {}, now=NOW), NOW)
    assert any(x.startswith("🔐 Doel-lock aan (4 van 4") and "het doel staat" in x for x in lines)
    runner, *_ = _paper(setup, tmp_path / "c", 10_900.0, 3, lock=False)
    assert not any("Doel-lock" in x for x in runner.briefing_extras(runner.engine.analyze("EURUSD", {}, now=NOW), NOW))
