"""Interactive Brokers adapter (paper or live) built on ``ib_async``.

Use: run TWS or IB Gateway with API access enabled (paper TWS: port 7497,
paper Gateway: 4002), then::

    broker = IBKRBroker(settings)          # reads IBKR_HOST / IBKR_PORT / IBKR_CLIENT_ID / IBKR_ACCOUNT
    broker.get_candles("EURUSD", Timeframe.MIN_15, 500)
    broker.place_market_order(...)         # market entry + stop + target as a bracket

Every position the adapter opens is a bracket: a market parent, a stop child
and a limit (take-profit) child, OCA-linked by IBKR so one cancels the other.
Break-even is a modification of the stop child.  Positions are reconciled
against the account on every query, so a stop or target filled at the broker
shows up in ``recent_closes``.

Notes: forex on IBKR trades on IDEALPRO in base-currency units (1.0 lot =
``SymbolSpec.contract_size`` = 100,000); orders under roughly 25,000 units are
odd lots with worse fills.  Bars use MIDPOINT by default so structure matches
charts.  The last bar returned by IBKR is the forming one; the engine drops it
through ``closed_as_of``.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import IBKRParams, Settings, SymbolSpec
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Direction
from .base import Broker, ClosedTrade, Position

IB_BAR_SIZES = {
    Timeframe.MIN_1: "1 min", Timeframe.MIN_5: "5 mins", Timeframe.MIN_15: "15 mins", Timeframe.MIN_30: "30 mins",
    Timeframe.H_1: "1 hour", Timeframe.H_4: "4 hours", Timeframe.D_1: "1 day", Timeframe.W_1: "1 week",
    Timeframe.MN_1: "1 month",
}


def duration_for(timeframe: Timeframe, count: int) -> str:
    """IBKR ``durationStr`` long enough to cover ``count`` bars of ``timeframe``."""
    timeframe = Timeframe.parse(timeframe)
    if timeframe is Timeframe.MN_1:
        return f"{max(1, math.ceil(count / 12))} Y"
    if timeframe is Timeframe.W_1:
        return f"{max(1, math.ceil(count / 52))} Y"
    seconds = timeframe.minutes * 60 * count
    if seconds < 86_400:
        return f"{max(60, seconds)} S"
    days = math.ceil(seconds / 86_400)
    if days <= 365:
        return f"{days} D"
    return f"{math.ceil(days / 365)} Y"


def build_contract(api, symbol: str, spec: SymbolSpec):
    """Translate a SymbolSpec into an ib_async contract."""
    symbol = symbol.upper()
    kind = spec.ibkr_contract or ("forex" if len(symbol) == 6 and symbol.isalpha() else None)
    if kind is None:
        raise ValueError(f"no IBKR contract mapping for {symbol}; set symbols.{symbol}.ibkr_contract")
    parts = kind.split(":")
    head = parts[0].lower()
    if head == "forex":
        return api.Forex(symbol)
    if head == "cfd":
        return api.CFD(parts[1], exchange="SMART", currency=parts[2] if len(parts) > 2 else "USD")
    if head == "stock":
        return api.Stock(parts[1], parts[2] if len(parts) > 2 else "SMART", parts[3] if len(parts) > 3 else "USD")
    if head == "crypto":
        return api.Crypto(parts[1], parts[2] if len(parts) > 2 else "PAXOS", parts[3] if len(parts) > 3 else "USD")
    raise ValueError(f"unknown ibkr_contract kind {kind!r}")


def symbol_of(contract) -> str:
    if getattr(contract, "secType", "") == "CASH":
        return f"{contract.symbol}{contract.currency}".upper()
    return str(getattr(contract, "symbol", "")).upper()


class IBKRBroker(Broker):
    def __init__(self, settings: Optional[Settings] = None, params: Optional[IBKRParams] = None,
                 ib=None, api=None, connect: bool = True):
        self.settings = settings or Settings()
        self.params = params or self.settings.ibkr
        if api is None:
            try:
                import ib_async as api  # type: ignore
            except ImportError as exc:
                raise RuntimeError("pip install ib_async to use the IBKR adapter") from exc
        self.api = api
        self.ib = ib if ib is not None else api.IB()
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Dict[str, Any]] = {}
        self._contracts: Dict[str, Any] = {}
        self._closed: List[ClosedTrade] = []
        self._close_cursor = 0
        self._quotes_blocked = False
        if connect and not self.ib.isConnected():
            self.connect()

    # ------------------------------------------------------------ connection
    def connect(self) -> None:
        p = self.params
        self.ib.connect(p.host, p.port, clientId=p.client_id, account=p.account, timeout=10)

    def disconnect(self) -> None:
        self.ib.disconnect()

    def idle(self, seconds: float) -> None:
        self.ib.sleep(seconds)      # runs the ib_async event loop so order updates and fills keep arriving

    # ------------------------------------------------------------ helpers
    def spec(self, symbol: str) -> SymbolSpec:
        return self.settings.symbol(symbol)

    def contract(self, symbol: str):
        key = symbol.upper()
        if key not in self._contracts:
            c = build_contract(self.api, key, self.spec(key))
            try:
                self.ib.qualifyContracts(c)
            except Exception:
                pass
            self._contracts[key] = c
        return self._contracts[key]

    def quantity(self, symbol: str, lots: float) -> float:
        size = self.spec(symbol).contract_size
        qty = lots * size
        return float(int(round(qty))) if size >= 1000 else round(qty, 2)

    def pnl_for(self, symbol: str, direction: Direction, entry: float, exit_price: float, lots: float) -> float:
        spec = self.spec(symbol)
        pips = direction.sign * (exit_price - entry) / spec.pip_size
        return pips * spec.pip_value_per_lot * lots

    def _rows(self, tag: str) -> List[Any]:
        account = self.params.account
        return [v for v in self.ib.accountValues()
                if v.tag == tag and (not account or getattr(v, "account", account) == account)]

    def base_currency(self) -> str:
        """The account's base currency: IBKR reports NetLiquidation once, in that currency."""
        for v in self._rows("NetLiquidation"):
            currency = getattr(v, "currency", "")
            if currency and currency != "BASE":
                return currency
        return self.settings.account_currency

    def _account_value(self, tag: str, default: float = 0.0) -> float:
        """Base-currency value of an account tag (IBKR also reports per-currency rows)."""
        rows = self._rows(tag)
        for wanted in ("BASE", self.base_currency(), self.settings.account_currency, ""):
            for v in rows:
                if getattr(v, "currency", "") == wanted:
                    try:
                        return float(v.value)
                    except (TypeError, ValueError):
                        continue
        if len(rows) == 1:
            try:
                return float(rows[0].value)
            except (TypeError, ValueError):
                pass
        return default

    def diagnostics(self) -> Dict[str, Any]:
        """What the account looks like from the API, for ``ibkr-test``."""
        values = list(self.ib.accountValues())
        out: Dict[str, Any] = {"accounts": sorted({getattr(v, "account", "") for v in values} - {""}),
                               "base_currency": self.base_currency()}
        for tag in ("NetLiquidation", "TotalCashValue", "AvailableFunds", "BuyingPower", "UnrealizedPnL", "RealizedPnL"):
            out[tag] = {getattr(v, "currency", ""): v.value for v in values if v.tag == tag}
        return out

    def _wait(self, seconds: float) -> None:
        sleep = getattr(self.ib, "sleep", None)
        if sleep is not None and seconds > 0:
            sleep(seconds)

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        return self._account_value("NetLiquidation")

    def balance(self) -> float:
        return self.equity() - self._account_value("UnrealizedPnL")

    def current_price(self, symbol: str) -> float:
        """Mid price from an API quote, else the close of the last 1-minute midpoint bar.

        Paper accounts without a market data entitlement get error 10089 on quotes
        (``Requested market data requires additional subscription for API``) while
        historical midpoint bars still work; after the first failure the loop prices
        from history only.
        """
        price = None if self._quotes_blocked else self._quote(symbol)
        if price is None:
            if not self._quotes_blocked:
                self._quotes_blocked = True
                print(f"[ibkr] no API quote for {symbol} (market data entitlement); pricing from 1-minute midpoint bars")
            price = self._last_close(symbol)
        if price is None:
            raise RuntimeError(f"no price for {symbol}: no API quote and no historical bars")
        return price

    def _quote(self, symbol: str) -> Optional[float]:
        try:
            ticker = self.ib.reqTickers(self.contract(symbol))[0]
        except Exception:
            return None
        bid, ask = getattr(ticker, "bid", None), getattr(ticker, "ask", None)
        if bid and ask and bid == bid and ask == ask and bid > 0 and ask > 0:
            return float((bid + ask) / 2.0)
        for attr in ("last", "close", "midpoint"):
            value = getattr(ticker, attr, None)
            value = value() if callable(value) else value
            if value and value == value and value > 0:
                return float(value)
        return None

    def _last_close(self, symbol: str) -> Optional[float]:
        try:
            bars = self.ib.reqHistoricalData(
                self.contract(symbol), endDateTime="", durationStr="600 S", barSizeSetting="1 min",
                whatToShow=self.params.what_to_show, useRTH=False, formatDate=2,
            )
        except Exception:
            return None
        if not bars:
            return None
        close = float(bars[-1].close)
        return close if close > 0 else None

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        self._reconcile()
        return [p for p in self._positions.values() if symbol is None or p.symbol == symbol.upper()]

    def place_market_order(self, symbol, direction, lots, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                           meta=None, price=None, ts=None) -> Position:
        symbol = symbol.upper()
        contract = self.contract(symbol)
        qty = self.quantity(symbol, lots)
        action = "BUY" if direction is Direction.LONG else "SELL"
        reverse = "SELL" if direction is Direction.LONG else "BUY"

        parent = self.api.MarketOrder(action, qty, transmit=False, tif="GTC")
        parent_trade = self.ib.placeOrder(contract, parent)
        parent_id = parent_trade.order.orderId
        tp_order = self.api.LimitOrder(reverse, qty, float(take_profit), parentId=parent_id, transmit=False, tif="GTC")
        tp_trade = self.ib.placeOrder(contract, tp_order)
        stop_order = self.api.StopOrder(reverse, qty, float(stop), parentId=parent_id, transmit=True, tif="GTC")
        stop_trade = self.ib.placeOrder(contract, stop_order)
        self._wait(self.params.fill_wait_seconds)

        fill = float(getattr(parent_trade.orderStatus, "avgFillPrice", 0.0) or 0.0)
        if fill <= 0:
            fill = float(price) if price is not None else self.current_price(symbol)
        pos = Position(
            id=str(parent_id), symbol=symbol, direction=direction, lots=float(lots), entry=fill, stop=float(stop),
            take_profit=float(take_profit), opened_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.now(tz="UTC").tz_localize(None),
            risk_amount=float(risk_amount), risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
            initial_stop=float(stop), meta=dict(meta or {}),
        )
        self._positions[pos.id] = pos
        self._orders[pos.id] = {"parent": parent_trade, "stop": stop_trade, "tp": tp_trade, "contract": contract}
        return pos

    def modify_stop(self, position_id: str, stop: float) -> None:
        orders = self._orders.get(str(position_id))
        if orders is None:
            raise KeyError(f"position {position_id} not tracked by this adapter")
        stop_trade = orders["stop"]
        stop_trade.order.auxPrice = float(stop)
        stop_trade.order.transmit = True
        self.ib.placeOrder(orders["contract"], stop_trade.order)
        self._positions[str(position_id)].stop = float(stop)

    def close_position(self, position_id, reason="manual", price=None, ts=None) -> ClosedTrade:
        pid = str(position_id)
        pos = self._positions.get(pid)
        if pos is None:
            raise KeyError(f"position {position_id} not tracked by this adapter")
        orders = self._orders.get(pid, {})
        for key in ("stop", "tp"):
            trade = orders.get(key)
            if trade is not None:
                try:
                    self.ib.cancelOrder(trade.order)
                except Exception:
                    pass
        contract = orders.get("contract") or self.contract(pos.symbol)
        reverse = "SELL" if pos.direction is Direction.LONG else "BUY"
        trade = self.ib.placeOrder(contract, self.api.MarketOrder(reverse, self.quantity(pos.symbol, pos.lots), tif="GTC"))
        self._wait(self.params.fill_wait_seconds)
        exit_price = float(getattr(trade.orderStatus, "avgFillPrice", 0.0) or 0.0)
        if exit_price <= 0:
            exit_price = float(price) if price is not None else self.current_price(pos.symbol)
        return self._finish(pos, exit_price, reason, ts)

    def recent_closes(self) -> List[ClosedTrade]:
        self._reconcile()
        out = self._closed[self._close_cursor:]
        self._close_cursor = len(self._closed)
        return out

    # ------------------------------------------------------------ reconciliation
    def _reconcile(self) -> None:
        held: Dict[str, float] = {}
        for p in self.ib.positions():
            sym = symbol_of(p.contract)
            held[sym] = held.get(sym, 0.0) + float(p.position)
        for pid, pos in list(self._positions.items()):
            if abs(held.get(pos.symbol, 0.0)) > 1e-9:
                continue
            orders = self._orders.get(pid, {})
            exit_price, reason = None, "closed"
            for key, label in (("stop", "stop"), ("tp", "take_profit")):
                trade = orders.get(key)
                status = getattr(getattr(trade, "orderStatus", None), "status", "")
                if trade is not None and status == "Filled":
                    exit_price = float(trade.orderStatus.avgFillPrice or 0.0) or None
                    reason = "breakeven" if label == "stop" and pos.breakeven_done else label
                    break
            if exit_price is None:
                exit_price = pos.stop if reason == "stop" else pos.take_profit if reason == "take_profit" else pos.entry
            self._finish(pos, exit_price, reason, None)

    def _finish(self, pos: Position, exit_price: float, reason: str, ts) -> ClosedTrade:
        self._positions.pop(pos.id, None)
        self._orders.pop(pos.id, None)
        trade = ClosedTrade(
            id=pos.id, symbol=pos.symbol, direction=pos.direction, lots=pos.lots, entry=pos.entry, exit=float(exit_price),
            stop=pos.stop, take_profit=pos.take_profit, opened_at=pos.opened_at,
            closed_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.now(tz="UTC").tz_localize(None),
            reason=reason, pnl=self.pnl_for(pos.symbol, pos.direction, pos.entry, float(exit_price), pos.lots),
            r=pos.r_at(float(exit_price)), risk_amount=pos.risk_amount, initial_stop=pos.initial_stop, meta=dict(pos.meta),
        )
        self._closed.append(trade)
        return trade

    # ------------------------------------------------------------ data
    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        timeframe = Timeframe.parse(timeframe)
        bars = self.ib.reqHistoricalData(
            self.contract(symbol), endDateTime="", durationStr=duration_for(timeframe, count),
            barSizeSetting=IB_BAR_SIZES[timeframe], whatToShow=self.params.what_to_show, useRTH=False, formatDate=2,
        )
        rows = [{"timestamp": b.date, "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                 "volume": max(float(getattr(b, "volume", 0.0) or 0.0), 0.0)} for b in bars]
        if not rows:
            raise RuntimeError(f"IBKR returned no bars for {symbol} {timeframe.label}")
        df = pd.DataFrame(rows)
        ts = pd.to_datetime(df["timestamp"], utc=True)
        df["timestamp"] = ts.dt.tz_localize(None)
        return CandleSeries(df.tail(count), timeframe, symbol.upper())
