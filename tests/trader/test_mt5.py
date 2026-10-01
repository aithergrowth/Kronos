"""MT5 adapter against a fake MetaTrader5 module: UTC timestamps, candles, orders, break-even, closes."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Direction, Timeframe as T
from kronos_trader.execution.mt5 import MT5Broker

NOW = pd.Timestamp("2026-10-01 09:00")          # UTC


def utc_seconds(ts: pd.Timestamp) -> int:
    ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")
    return int(ts.timestamp())


class FakeMT5:
    TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_M30, TIMEFRAME_H1, TIMEFRAME_H4 = 1, 5, 15, 30, 16385, 16388
    TIMEFRAME_D1, TIMEFRAME_W1, TIMEFRAME_MN1 = 16408, 32769, 49153
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
    ORDER_TIME_GTC, ORDER_FILLING_FOK, ORDER_FILLING_IOC = 0, 0, 1
    TRADE_RETCODE_DONE, TRADE_RETCODE_PLACED = 10009, 10008
    DEAL_ENTRY_IN, DEAL_ENTRY_OUT = 0, 1
    DEAL_REASON_CLIENT, DEAL_REASON_SL, DEAL_REASON_TP = 0, 4, 5

    def __init__(self, bid=1.1000, ask=1.1001):
        self.bid, self.ask = bid, ask
        self.init_kwargs = None
        self.positions = []
        self.deals = []
        self.requests = []
        self._ticket = 500
        self.accept = True
        self.tick_time = utc_seconds(NOW)

    def initialize(self, **kwargs):
        self.init_kwargs = kwargs
        return True

    def login(self, login, password=None, server=None, timeout=None):
        self.login_args = (login, password, server)
        return True

    def shutdown(self):
        self.init_kwargs = None

    def last_error(self):
        return (0, "ok")

    def version(self):
        return (500, 4000, "01 Jan 2026")

    def account_info(self):
        return SimpleNamespace(login=62724281, server="MetaQuotes-Demo", currency="EUR", balance=50000.0,
                               equity=50010.0, leverage=100, trade_mode=0)

    def terminal_info(self):
        return SimpleNamespace(connected=True, trade_allowed=True)

    def symbol_select(self, name, enable=True):
        return True

    def symbol_info_tick(self, name):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=self.tick_time)

    def copy_rates_from_pos(self, name, tf, start, count):
        rows = [(utc_seconds(NOW - pd.Timedelta(15 * (count - 1 - i), unit="min")), 1.1, 1.101, 1.099, 1.1005, 12, 1, 0)
                for i in range(count)]
        return np.array(rows, dtype=[("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                                     ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])

    def _deal(self, position_id, entry, reason, price, profit, when):
        self._ticket += 1
        d = SimpleNamespace(ticket=self._ticket, position_id=position_id, entry=entry, reason=reason, price=price,
                            profit=profit, commission=-0.5, swap=0.0, time=utc_seconds(when))
        self.deals.append(d)
        return d

    def order_send(self, request):
        self.requests.append(request)
        if not self.accept:
            return SimpleNamespace(retcode=10013, order=0, deal=0, price=0.0, comment="Invalid request")
        if request["action"] == self.TRADE_ACTION_SLTP:
            for p in self.positions:
                if p.ticket == request["position"]:
                    p.sl, p.tp = request["sl"], request["tp"]
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=0, deal=0, price=0.0, comment="")
        price = self.ask if request["type"] == self.ORDER_TYPE_BUY else self.bid
        if request.get("position"):                                                     # closing deal
            pos = next(p for p in self.positions if p.ticket == request["position"])
            self.positions.remove(pos)
            d = self._deal(pos.ticket, self.DEAL_ENTRY_OUT, self.DEAL_REASON_CLIENT, price, 15.0, NOW)
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=d.ticket, deal=d.ticket, price=price, comment="")
        self._ticket += 1
        ticket = self._ticket
        self.positions.append(SimpleNamespace(ticket=ticket, symbol=request["symbol"], type=request["type"],
                                              volume=request["volume"], price_open=price, sl=request["sl"], tp=request["tp"],
                                              time=utc_seconds(NOW), magic=request["magic"], comment=request["comment"],
                                              profit=0.0))
        d = self._deal(ticket, self.DEAL_ENTRY_IN, self.DEAL_REASON_CLIENT, price, 0.0, NOW)
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=ticket, deal=d.ticket, price=price, comment="")

    def positions_get(self, symbol=None):
        return [p for p in self.positions if symbol is None or p.symbol == symbol]

    def history_deals_get(self, *args, position=None, ticket=None):
        if ticket is not None:
            return [d for d in self.deals if d.ticket == ticket]
        if position is not None:
            return [d for d in self.deals if d.position_id == position]
        return list(self.deals)

    def server_closes(self, ticket, how="sl"):
        """The server closes a position at its stop or target an hour later."""
        pos = next(p for p in self.positions if p.ticket == ticket)
        self.positions.remove(pos)
        reason = self.DEAL_REASON_SL if how == "sl" else self.DEAL_REASON_TP
        self._deal(ticket, self.DEAL_ENTRY_OUT, reason, pos.sl if how == "sl" else pos.tp,
                   -100.0 if how == "sl" else 300.0, NOW + pd.Timedelta(1, unit="h"))


@pytest.fixture
def broker(monkeypatch):
    for key in ("MT5_PATH", "MT5_SERVER_OFFSET_HOURS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MT5_LOGIN", "62724281")
    monkeypatch.setenv("MT5_PASSWORD", "pw")
    monkeypatch.setenv("MT5_SERVER", "MetaQuotes-Demo")
    return MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)


def test_initialize_uses_the_environment(broker):
    assert broker.mt5.init_kwargs == {} and broker.mt5.login_args == (62724281, "pw", "MetaQuotes-Demo")
    d = broker.diagnostics()
    assert d["server"] == "MetaQuotes-Demo" and d["currency"] == "EUR" and d["connected"] and d["equity"] == 50010.0


def test_connection_falls_back_to_first_available_terminal(broker, monkeypatch):
    paths = [r"C:\First\terminal64.exe", r"C:\Second\terminal64.exe", r"C:\Third\terminal64.exe"]
    monkeypatch.setattr("kronos_trader.execution.mt5.terminal_candidates", lambda: paths)
    calls = []

    def initialize(**kwargs):
        calls.append(kwargs)
        return kwargs.get("path") == paths[1]

    monkeypatch.setattr(broker.mt5, "initialize", initialize)
    broker.connect()

    assert calls == [{}, {"path": paths[0]}, {"path": paths[1]}]
    assert broker.terminal_path == paths[1]
    assert broker.mt5.login_args == (62724281, "pw", "MetaQuotes-Demo")
    assert broker.mt5.requests == []


def test_explicit_terminal_failure_does_not_switch_terminals(broker, monkeypatch):
    path = r"C:\Chosen\terminal64.exe"
    monkeypatch.setenv("MT5_PATH", path)
    calls = []

    def initialize(**kwargs):
        calls.append(kwargs)
        return False

    def unexpected_call(*args, **kwargs):
        raise AssertionError("an explicit terminal failure must not discover or log into another terminal")

    monkeypatch.setattr(broker.mt5, "initialize", initialize)
    monkeypatch.setattr(broker.mt5, "login", unexpected_call)
    monkeypatch.setattr("kronos_trader.execution.mt5.terminal_candidates", unexpected_call)
    with pytest.raises(RuntimeError, match="MT5 initialize failed"):
        broker.connect()

    assert calls == [{"path": path}]
    assert broker.mt5.requests == []


def test_explicit_login_failure_is_not_silently_accepted(broker, monkeypatch):
    monkeypatch.setattr(broker.mt5, "login", lambda *args, **kwargs: False)

    with pytest.raises(RuntimeError, match="MT5 login failed"):
        broker.connect()

    assert broker.mt5.requests == []


def test_mt5_utc_timestamps_are_preserved_by_default(broker):
    assert broker.server_offset("EURUSD") == pd.Timedelta(0)
    s = broker.get_candles("EURUSD", T.MIN_15, 4)
    assert len(s) == 4 and s.symbol == "EURUSD" and str(s.timestamps.iloc[-1]) == "2026-10-01 09:00:00"
    assert s.timestamps.dt.tz is None and broker.to_utc(utc_seconds(NOW)) == NOW
    assert s.last.close == pytest.approx(1.1005)


def test_pinned_offset(monkeypatch):
    monkeypatch.setenv("MT5_SERVER_OFFSET_HOURS", "2")
    b = MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)
    assert b.server_offset() == pd.Timedelta(2, unit="h")
    # An explicitly configured compatibility correction, never inferred from a tick.
    assert b.to_utc(utc_seconds(NOW + pd.Timedelta(2, unit="h"))) == NOW


@pytest.mark.parametrize("age", [pd.Timedelta(2, unit="h"), pd.Timedelta(3, unit="d")], ids=["two_hours", "weekend"])
@pytest.mark.parametrize("clock_time", [NOW, NOW.tz_localize("UTC")], ids=["naive_utc_clock", "aware_utc_clock"])
def test_stale_tick_cannot_retime_utc_candles(broker, age, clock_time):
    broker.mt5.tick_time = utc_seconds(NOW - age)
    broker.clock = lambda: clock_time
    raw = broker.mt5.copy_rates_from_pos("EURUSD", FakeMT5.TIMEFRAME_M15, 0, 4)
    expected = pd.to_datetime(raw["time"], unit="s", utc=True).tz_localize(None).tolist()

    series = broker.get_candles("EURUSD", T.MIN_15, 4)

    assert series.timestamps.tolist() == expected
    assert broker.server_offset() == pd.Timedelta(0)
    assert broker.to_utc(utc_seconds(NOW - age)) == NOW - age
    assert broker.mt5.requests == []


@pytest.mark.parametrize("timeframe,api_timeframe,opens", [
    (T.H_4, FakeMT5.TIMEFRAME_H4, ["2026-09-30 21:00", "2026-10-01 01:00", "2026-10-01 05:00"]),
    (T.D_1, FakeMT5.TIMEFRAME_D1, ["2026-09-28 21:00", "2026-09-29 21:00", "2026-09-30 21:00"]),
], ids=["native_4h", "native_daily"])
def test_native_bar_open_times_are_not_reanchored(broker, monkeypatch, timeframe, api_timeframe, opens):
    broker.mt5.tick_time = utc_seconds(NOW - pd.Timedelta(2, unit="h"))
    expected = [pd.Timestamp(value) for value in opens]
    raw = broker.mt5.copy_rates_from_pos("EURUSD", api_timeframe, 0, 3)
    raw["time"] = [utc_seconds(value) for value in expected]
    calls = []

    def native_rates(symbol, tf, start, count):
        calls.append((symbol, tf, start, count))
        return raw.copy()

    monkeypatch.setattr(broker.mt5, "copy_rates_from_pos", native_rates)
    series = broker.get_candles("EURUSD", timeframe, 3)

    assert calls == [("EURUSD", api_timeframe, 0, 3)]
    assert series.timestamps.tolist() == expected and series.timeframe is timeframe
    assert series.timestamps.dt.tz is None


def test_candle_timestamp_conversion_does_not_need_a_tick(broker, monkeypatch):
    def unavailable_tick(symbol):
        raise AssertionError("historical timestamp parsing must not query a tick")

    monkeypatch.setattr(broker.mt5, "symbol_info_tick", unavailable_tick)
    series = broker.get_candles("EURUSD", T.MIN_15, 4)
    assert series.last_timestamp == NOW and broker.server_offset() == pd.Timedelta(0)


def test_market_order_tracking_breakeven_and_close(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0,
                                    meta={"comment": "test"}, ts=NOW)
    req = broker.mt5.requests[-1]
    assert req["symbol"] == "EURUSD" and req["volume"] == 0.5 and req["sl"] == 1.0950 and req["tp"] == 1.12
    assert req["magic"] == broker.magic and req["type_filling"] == FakeMT5.ORDER_FILLING_IOC
    assert pos.status == "filled" and pos.entry == pytest.approx(1.1001) and pos.opened_at == NOW
    assert broker.open_positions("EURUSD") == [pos] and broker.open_positions()[0] is pos     # same object every poll
    assert not pos.breakeven_done
    broker.modify_stop(pos.id, 1.1001)
    assert broker.open_positions("EURUSD")[0].stop == 1.1001 and pos.breakeven_done
    trade = broker.close_position(pos.id, "manual", ts=NOW)
    assert trade.reason == "manual" and trade.pnl == pytest.approx(14.5) and broker.open_positions() == []


def test_stop_and_target_hits_are_reported(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0, ts=NOW)
    broker.mt5.server_closes(int(pos.id), "sl")
    closes = broker.recent_closes()
    assert len(closes) == 1 and closes[0].reason == "stop" and closes[0].exit == 1.0950
    assert closes[0].pnl == pytest.approx(-100.5) and closes[0].r == pytest.approx(-1.0)
    assert str(closes[0].closed_at) == "2026-10-01 10:00:00"
    assert broker.recent_closes() == []
    pos2 = broker.place_market_order("EURUSD", Direction.SHORT, 0.5, 1.1050, 1.0800, 500.0, 0.0050, 4.0, ts=NOW)
    broker.mt5.server_closes(int(pos2.id), "tp")
    assert broker.recent_closes()[0].reason == "take_profit"


def test_rejected_order_raises(broker):
    broker.mt5.accept = False
    with pytest.raises(RuntimeError, match="not accepted"):
        broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0)
    assert broker.open_positions() == []
