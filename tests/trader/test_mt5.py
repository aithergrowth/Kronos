"""MT5 adapter against a fake MetaTrader5 module: server time, candles, orders, break-even, closes."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Direction, Timeframe as T
from kronos_trader.execution.mt5 import MT5Broker

NOW = pd.Timestamp("2026-10-01 09:00")          # UTC
OFFSET_H = 3                                     # the broker server runs on UTC+3


def server_seconds(ts: pd.Timestamp) -> int:
    return int((ts + pd.Timedelta(OFFSET_H, unit="h")).timestamp())


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
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=server_seconds(NOW))

    def copy_rates_from_pos(self, name, tf, start, count):
        rows = [(server_seconds(NOW - pd.Timedelta(15 * (count - 1 - i), unit="min")), 1.1, 1.101, 1.099, 1.1005, 12, 1, 0)
                for i in range(count)]
        return np.array(rows, dtype=[("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                                     ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])

    def _deal(self, position_id, entry, reason, price, profit, when):
        self._ticket += 1
        d = SimpleNamespace(ticket=self._ticket, position_id=position_id, entry=entry, reason=reason, price=price,
                            profit=profit, commission=-0.5, swap=0.0, time=server_seconds(when))
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
                                              time=server_seconds(NOW), magic=request["magic"], comment=request["comment"],
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


def test_server_time_is_converted_to_utc(broker):
    assert broker.server_offset("EURUSD") == pd.Timedelta(3, unit="h")
    s = broker.get_candles("EURUSD", T.MIN_15, 4)
    assert len(s) == 4 and s.symbol == "EURUSD" and str(s.timestamps.iloc[-1]) == "2026-10-01 09:00:00"
    assert s.last.close == pytest.approx(1.1005)


def test_pinned_offset(monkeypatch):
    monkeypatch.setenv("MT5_SERVER_OFFSET_HOURS", "2")
    b = MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)
    assert b.server_offset() == pd.Timedelta(2, unit="h")


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
