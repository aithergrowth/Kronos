"""IBKR adapter logic against a fake ib_async: contracts, bracket orders, break-even, reconciliation, bars."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Direction, Timeframe
from kronos_trader.execution.ibkr import IBKRBroker, build_contract, duration_for, symbol_of

T = Timeframe


class _Contract(SimpleNamespace):
    pass


class FakeApi:
    @staticmethod
    def Forex(pair="", exchange="IDEALPRO", symbol="", currency=""):
        return _Contract(secType="CASH", symbol=pair[:3], currency=pair[3:], exchange=exchange)

    @staticmethod
    def CFD(symbol="", exchange="", currency=""):
        return _Contract(secType="CFD", symbol=symbol, exchange=exchange, currency=currency)

    @staticmethod
    def Stock(symbol="", exchange="", currency=""):
        return _Contract(secType="STK", symbol=symbol, exchange=exchange, currency=currency)

    @staticmethod
    def Crypto(symbol="", exchange="", currency=""):
        return _Contract(secType="CRYPTO", symbol=symbol, exchange=exchange, currency=currency)

    class _Order(SimpleNamespace):
        def __init__(self, **attrs):
            base = dict(orderId=0, parentId=0, transmit=True, tif="DAY")
            base.update(attrs)
            super().__init__(**base)

    class MarketOrder(_Order):
        def __init__(self, action, totalQuantity, **kw):
            super().__init__(action=action, totalQuantity=totalQuantity, orderType="MKT", **kw)

    class LimitOrder(_Order):
        def __init__(self, action, totalQuantity, lmtPrice, **kw):
            super().__init__(action=action, totalQuantity=totalQuantity, orderType="LMT", lmtPrice=lmtPrice, **kw)

    class StopOrder(_Order):
        def __init__(self, action, totalQuantity, stopPrice, **kw):
            super().__init__(action=action, totalQuantity=totalQuantity, orderType="STP", auxPrice=stopPrice, **kw)


class FakeIB:
    def __init__(self, price=1.1000):
        self.connected = False
        self.price = price
        self.trades = []
        self._next_id = 100
        self.held = {}          # symbol -> signed units
        self.hist_calls = []
        self.bars = []

    def isConnected(self):
        return self.connected

    def connect(self, host, port, clientId, account="", timeout=4):
        self.connected = True
        self.connect_args = (host, port, clientId)

    def disconnect(self):
        self.connected = False

    def qualifyContracts(self, c):
        return [c]

    def sleep(self, s):
        self.slept = getattr(self, "slept", 0) + s

    def placeOrder(self, contract, order):
        existing = next((t for t in self.trades if t.order is order), None)
        if existing is not None:      # a modification
            existing.modified = True
            return existing
        if order.orderId == 0:
            order.orderId = self._next_id
            self._next_id += 1
        status = "Submitted"
        fill = 0.0
        if order.orderType == "MKT":
            status, fill = "Filled", self.price
            sym = symbol_of(contract)
            sign = 1 if order.action == "BUY" else -1
            self.held[sym] = self.held.get(sym, 0.0) + sign * order.totalQuantity
        trade = SimpleNamespace(order=order, contract=contract, orderStatus=SimpleNamespace(status=status, avgFillPrice=fill), modified=False)
        self.trades.append(trade)
        return trade

    def cancelOrder(self, order):
        for t in self.trades:
            if t.order is order:
                t.orderStatus.status = "Cancelled"

    def positions(self):
        return [SimpleNamespace(account="DU1", contract=_Contract(secType="CASH", symbol=s[:3], currency=s[3:]), position=q, avgCost=self.price)
                for s, q in self.held.items() if abs(q) > 0]

    def accountValues(self):
        return [SimpleNamespace(tag="NetLiquidation", value="100000", currency="USD"),
                SimpleNamespace(tag="UnrealizedPnL", value="250", currency="USD")]

    def reqTickers(self, contract):
        return [SimpleNamespace(bid=self.price - 0.00005, ask=self.price + 0.00005, last=None, close=None)]

    def reqHistoricalData(self, contract, endDateTime, durationStr, barSizeSetting, whatToShow, useRTH, formatDate=1):
        self.hist_calls.append((durationStr, barSizeSetting, whatToShow, useRTH))
        return self.bars


@pytest.fixture
def broker():
    ib = FakeIB()
    b = IBKRBroker(Settings(), ib=ib, api=FakeApi, connect=True)
    return b


def test_connect_uses_env_defaults(broker):
    assert broker.ib.connected and broker.ib.connect_args == ("127.0.0.1", 7497, 17)


def test_contracts_and_quantities(broker):
    s = Settings()
    fx = build_contract(FakeApi, "EURUSD", s.symbol("EURUSD"))
    assert fx.secType == "CASH" and fx.symbol == "EUR" and fx.currency == "USD" and symbol_of(fx) == "EURUSD"
    gold = build_contract(FakeApi, "XAUUSD", s.symbol("XAUUSD"))
    assert gold.secType == "CFD" and gold.symbol == "XAUUSD"
    nas = build_contract(FakeApi, "NAS100", s.symbol("NAS100"))
    assert nas.symbol == "IBUST100"
    assert broker.quantity("EURUSD", 1.96) == 196000.0
    assert broker.quantity("XAUUSD", 0.5) == 50.0
    assert broker.quantity("NAS100", 1.0) == 1.0


def test_duration_strings():
    assert duration_for(T.MIN_1, 500) == "30000 S"
    assert duration_for(T.MIN_5, 500) == "2 D"
    assert duration_for(T.H_4, 400) == "67 D"
    assert duration_for(T.D_1, 250) == "250 D"
    assert duration_for(T.D_1, 500) == "2 Y"
    assert duration_for(T.W_1, 300) == "6 Y"
    assert duration_for(T.MN_1, 100) == "9 Y"


def test_bracket_order_and_tracking(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.96, 1.0950, 1.1200, 1000.0, 0.0051, 4.0,
                                    meta={"comment": "test"}, ts=pd.Timestamp("2026-10-01 09:00"))
    orders = [t.order for t in broker.ib.trades]
    assert [o.orderType for o in orders] == ["MKT", "LMT", "STP"]
    parent, tp, stop = orders
    assert parent.action == "BUY" and parent.totalQuantity == 196000.0 and parent.transmit is False
    assert tp.action == "SELL" and tp.lmtPrice == 1.12 and tp.parentId == parent.orderId and tp.transmit is False
    assert stop.action == "SELL" and stop.auxPrice == 1.095 and stop.parentId == parent.orderId and stop.transmit is True
    assert pos.id == str(parent.orderId) and pos.entry == 1.1 and pos.lots == 1.96
    assert broker.open_positions("EURUSD")[0].id == pos.id
    assert broker.equity() == 100000.0 and broker.balance() == 99750.0
    assert broker.current_price("EURUSD") == pytest.approx(1.1)


def test_breakeven_modifies_stop_child(broker):
    pos = broker.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.1050, 1.0800, 1000.0, 0.0051, 4.0)
    broker.modify_stop(pos.id, pos.entry)
    stop_trade = broker.ib.trades[2]
    assert stop_trade.order.auxPrice == pos.entry and stop_trade.modified
    assert broker.open_positions()[0].stop == pos.entry


def test_reconcile_reports_stop_fill(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 2.0, 1.0950, 1.1200, 1000.0, 0.0051, 4.0)
    assert broker.recent_closes() == []
    # the stop fills at the broker: position disappears, stop child is Filled
    broker.ib.held["EURUSD"] = 0.0
    broker.ib.trades[2].orderStatus.status = "Filled"
    broker.ib.trades[2].orderStatus.avgFillPrice = 1.0949
    closes = broker.recent_closes()
    assert len(closes) == 1 and closes[0].reason == "stop" and closes[0].exit == 1.0949
    assert closes[0].pnl == pytest.approx((1.0949 - 1.1) / 0.0001 * 10 * 2.0)
    assert broker.open_positions() == [] and broker.recent_closes() == []


def test_get_candles_parses_bars(broker):
    broker.ib.bars = [
        SimpleNamespace(date=datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc), open=1.1, high=1.11, low=1.09, close=1.105, volume=-1),
        SimpleNamespace(date=datetime(2026, 10, 1, 9, 15, tzinfo=timezone.utc), open=1.105, high=1.12, low=1.10, close=1.115, volume=12),
    ]
    s = broker.get_candles("EURUSD", T.MIN_15, 500)
    assert len(s) == 2 and s.timeframe is T.MIN_15 and s.symbol == "EURUSD"
    assert s.timestamps.iloc[0] == pd.Timestamp("2026-10-01 09:00") and s.timestamps.dt.tz is None
    assert s.volume.tolist() == [0.0, 12.0]
    assert broker.ib.hist_calls[0] == ("6 D", "15 mins", "MIDPOINT", False)


def test_idle_runs_the_ib_event_loop(broker):
    broker.idle(2)
    assert broker.ib.slept == 2
