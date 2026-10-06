"""Paper broker: fills and stop/target checks on bid and ask built from the candles
(``quote_basis="mid"``: candle +/- half the spread; ``"bid"``: the candles are bid
quotes, as HistData's are, so ask = bid + spread), checks SL/TP on every closed
candle, fills a stop at the open when a candle gaps through it, moves the stop to
break-even per the exit rules and never takes partials."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..config import Settings
from ..core.candles import Candle
from ..core.types import Direction
from ..strategy.exits import breakeven_reached, weekend_cutoff_after
from .base import Broker, ClosedTrade, LimitOrder, Position


class PaperBroker(Broker):
    def __init__(self, settings: Optional[Settings] = None, equity: Optional[float] = None,
                 spread_pips: Optional[Dict[str, float]] = None, use_spread: bool = True, quote_basis: str = "mid"):
        if quote_basis not in ("mid", "bid"):
            raise ValueError(f"quote_basis must be 'mid' or 'bid', not {quote_basis!r}")
        self.quote_basis = quote_basis
        self.settings = settings or Settings()
        self._balance = float(equity if equity is not None else self.settings.account_size)
        self.initial_balance = self._balance
        self.spread_pips = dict(spread_pips or {})
        self.use_spread = use_spread
        self.positions: Dict[str, Position] = {}
        self.closed: List[ClosedTrade] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self._last_price: Dict[str, float] = {}
        self._last_id = 0
        self._close_cursor = 0
        self._restored_realized: List[Tuple[pd.Timestamp, float]] = []   # closes before a restart (day/month baselines)
        self.limits: Dict[str, LimitOrder] = {}          # resting limit entries
        self._limit_fills: Dict[str, Optional[Position]] = {}   # limit id -> its position (None once it closed again)

    def recent_closes(self) -> List[ClosedTrade]:
        out = self.closed[self._close_cursor:]
        self._close_cursor = len(self.closed)
        return out

    # ------------------------------------------------------------ helpers
    def _spec(self, symbol: str):
        return self.settings.symbol(symbol)

    def _half_spread(self, symbol: str) -> float:
        if not self.use_spread:
            return 0.0
        spec = self._spec(symbol)
        pips = self.spread_pips.get(symbol.upper(), spec.typical_spread_pips)
        return pips * spec.pip_size / 2.0

    def _offsets(self, symbol: str) -> Tuple[float, float]:
        """``(bid - candle, ask - candle)`` for the configured quote basis."""
        half = self._half_spread(symbol)
        if self.quote_basis == "bid":
            return 0.0, 2.0 * half
        return -half, half

    def _market_exit(self, symbol: str, direction: Direction, base: float) -> float:
        """The price a position closes at from candle price ``base``: the bid for a long, the ask for a short."""
        bid_off, ask_off = self._offsets(symbol)
        return float(base) + (bid_off if direction is Direction.LONG else ask_off)

    def pnl_for(self, symbol: str, direction: Direction, entry: float, exit_price: float, lots: float) -> float:
        spec = self._spec(symbol)
        pips = direction.sign * (exit_price - entry) / spec.pip_size
        return pips * spec.pip_value_per_lot * lots

    def commission(self, symbol: str, entry: float, lots: float) -> float:
        """The round-turn commission of ``lots`` (account currency) from the symbol's ``commission_per_lot`` and
        ``commission_pct`` of the notional; 0 unless a backtest sets them (``--costs``)."""
        spec = self._spec(symbol)
        cost = spec.commission_per_lot * lots
        if spec.commission_pct:
            cost += spec.commission_pct / 100.0 * abs(entry) / spec.pip_size * spec.pip_value_per_lot * lots
        return cost

    def set_price(self, symbol: str, price: float) -> None:
        self._last_price[symbol.upper()] = float(price)

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        unrealized = 0.0
        for pos in self.positions.values():
            price = self._last_price.get(pos.symbol)
            if price is not None:
                unrealized += self.pnl_for(pos.symbol, pos.direction, pos.entry, self._market_exit(pos.symbol, pos.direction, price), pos.lots)
        return self._balance + unrealized

    def balance(self) -> float:
        return self._balance

    def realized_pnl_since(self, since: pd.Timestamp) -> float:
        """Closed P&L since ``since`` (naive UTC), the closes from before a restart included."""
        since = pd.Timestamp(since)
        now = sum(t.pnl for t in self.closed if t.closed_at is not None and t.closed_at >= since)
        return float(now + sum(p for at, p in self._restored_realized if at >= since))

    # ------------------------------------------------------------ restart memory
    def state(self) -> Dict[str, Any]:
        """Balance, open positions and the last 500 closes' P&L as plain JSON values, so a live paper window (BTC on
        Bitstamp prices) keeps its account, and its day and month baselines, across a restart."""
        realized = [(str(at), p) for at, p in self._restored_realized]
        realized += [(str(t.closed_at), float(t.pnl)) for t in self.closed if t.closed_at is not None]
        realized = realized[-500:]
        positions = []
        for p in self.positions.values():
            positions.append({"id": p.id, "symbol": p.symbol, "direction": p.direction.name, "lots": p.lots, "entry": p.entry,
                              "stop": p.stop, "take_profit": p.take_profit, "opened_at": str(p.opened_at),
                              "risk_amount": p.risk_amount, "risk_distance": p.risk_distance, "breakeven_r": p.breakeven_r,
                              "initial_stop": p.initial_stop, "breakeven_done": p.breakeven_done, "status": p.status,
                              "meta": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in p.meta.items()}})
        limits = [{"id": o.id, "symbol": o.symbol, "direction": o.direction.name, "lots": o.lots, "price": o.price, "stop": o.stop,
                   "take_profit": o.take_profit, "risk_amount": o.risk_amount, "risk_distance": o.risk_distance,
                   "breakeven_r": o.breakeven_r, "placed_at": str(o.placed_at), "expires_at": str(o.expires_at),
                   "meta": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in o.meta.items()}}
                  for o in self.limits.values()]
        return {"balance": self._balance, "initial_balance": self.initial_balance, "next_id": self._last_id + 1,
                "positions": positions, "realized": realized, "limits": limits}

    def restore(self, state: Dict[str, Any]) -> None:
        self._balance = float(state.get("balance", self._balance))
        self.initial_balance = float(state.get("initial_balance", self.initial_balance))
        self.positions = {}
        for d in state.get("positions", []):
            pos = Position(id=str(d["id"]), symbol=str(d["symbol"]), direction=Direction[d["direction"]], lots=float(d["lots"]),
                           entry=float(d["entry"]), stop=float(d["stop"]), take_profit=float(d["take_profit"]),
                           opened_at=pd.Timestamp(d["opened_at"]), risk_amount=float(d["risk_amount"]),
                           risk_distance=float(d["risk_distance"]), breakeven_r=float(d["breakeven_r"]),
                           initial_stop=float(d["initial_stop"]), breakeven_done=bool(d.get("breakeven_done", False)),
                           meta=dict(d.get("meta") or {}), status=str(d.get("status", "filled")))
            self.positions[pos.id] = pos
        self.limits = {}
        for d in state.get("limits", []):
            order = LimitOrder(id=str(d["id"]), symbol=str(d["symbol"]), direction=Direction[d["direction"]], lots=float(d["lots"]),
                               price=float(d["price"]), stop=float(d["stop"]), take_profit=float(d["take_profit"]),
                               risk_amount=float(d["risk_amount"]), risk_distance=float(d["risk_distance"]),
                               breakeven_r=float(d["breakeven_r"]), placed_at=pd.Timestamp(d["placed_at"]),
                               expires_at=pd.Timestamp(d["expires_at"]), meta=dict(d.get("meta") or {}))
            self.limits[order.id] = order
        self._last_id = int(state.get("next_id", 1)) - 1
        self._restored_realized = [(pd.Timestamp(at), float(p)) for at, p in state.get("realized", [])]

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        if symbol is None:
            return list(self.positions.values())
        return [p for p in self.positions.values() if p.symbol == symbol.upper()]

    def current_price(self, symbol: str) -> float:
        return self._last_price[symbol.upper()]

    def fill_price(self, symbol: str, direction: Direction, base: Optional[float] = None) -> float:
        symbol = symbol.upper()
        base = float(base if base is not None else self.current_price(symbol))
        bid_off, ask_off = self._offsets(symbol)
        return base + (ask_off if direction is Direction.LONG else bid_off)

    def place_market_order(self, symbol, direction, lots, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                           meta=None, price=None, ts=None, price_is_fill=False) -> Position:
        """``price`` is a candle/mid price unless ``price_is_fill`` says it already is the executable quote."""
        symbol = symbol.upper()
        base = float(price if price is not None else self.current_price(symbol))
        fill = base if price_is_fill else self.fill_price(symbol, direction, base)
        bid_off, ask_off = self._offsets(symbol)
        mid = fill - (ask_off if direction is Direction.LONG else bid_off)
        pos = Position(
            id=f"P{self._next_id()}", symbol=symbol, direction=direction, lots=float(lots), entry=fill,
            stop=float(stop), take_profit=float(take_profit), opened_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.now("UTC").tz_localize(None),
            risk_amount=float(risk_amount), risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
            initial_stop=float(stop), meta=dict(meta or {}),
        )
        self.positions[pos.id] = pos
        self._last_price[symbol] = mid
        return pos

    # ------------------------------------------------------------ limit entries
    def place_limit_order(self, symbol, direction, lots, price, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                          expires_at, meta=None, ts=None) -> LimitOrder:
        order = LimitOrder(id=f"L{self._next_id()}", symbol=symbol.upper(), direction=direction, lots=float(lots),
                           price=float(price), stop=float(stop), take_profit=float(take_profit), risk_amount=float(risk_amount),
                           risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
                           placed_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.now("UTC").tz_localize(None),
                           expires_at=pd.Timestamp(expires_at), meta=dict(meta or {}))
        self.limits[order.id] = order
        return order

    def limit_orders(self, symbol: Optional[str] = None) -> List[LimitOrder]:
        return [o for o in self.limits.values() if symbol is None or o.symbol == symbol.upper()]

    def cancel_limit(self, order_id: str) -> None:
        self.limits.pop(str(order_id), None)

    def limit_state(self, order_id: str):
        order_id = str(order_id)
        if order_id in self.limits:
            return "pending", None
        if order_id in self._limit_fills:
            pos = self._limit_fills[order_id]
            return "filled", (pos if pos is not None and pos.id in self.positions else None)
        return "gone", None

    def _work_limits(self, symbol: str, candle: Candle, bid_off: float, ask_off: float) -> List[ClosedTrade]:
        """Limit entries of ``symbol`` that this candle reaches become positions at their price (the ask for a buy, the bid
        for a sell); a stop in the fill's own candle closes it there. Expiry and the target trading first are the live
        runner's (it cancels the order)."""
        closed: List[ClosedTrade] = []
        for order in [o for o in self.limits.values() if o.symbol == symbol]:
            if pd.Timestamp(candle.timestamp) < order.placed_at:
                continue                                 # placed_at: the start of the candle it was placed in (fill_stamp)
            long = order.direction is Direction.LONG
            filled = (candle.low + ask_off <= order.price) if long else (candle.high + bid_off >= order.price)
            if not filled:
                continue
            self.limits.pop(order.id)
            pos = Position(id=f"P{self._next_id()}", symbol=symbol, direction=order.direction, lots=order.lots, entry=order.price,
                           stop=order.stop, take_profit=order.take_profit,
                           opened_at=pd.Timestamp(candle.timestamp) + pd.Timedelta(microseconds=1),   # checked from the next candle
                           risk_amount=order.risk_amount, risk_distance=order.risk_distance, breakeven_r=order.breakeven_r,
                           initial_stop=order.stop, meta={**order.meta, "limit_id": order.id})
            from ..strategy.risk import reconcile_risk
            reconcile_risk(pos, self, order.risk_amount)  # the risk on the fill, as the backtest measures a limit fill
            self.positions[pos.id] = pos
            self._limit_fills[order.id] = pos
            stopped = (candle.low + bid_off <= order.stop) if long else (candle.high + ask_off >= order.stop)
            if stopped:                                  # the fill's own candle traded through the stop too: taken as hit
                closed.append(self.close_position(pos.id, "stop", order.stop, candle.timestamp))
        return closed

    def _next_id(self) -> int:
        self._last_id += 1
        return self._last_id

    def modify_stop(self, position_id: str, stop: float) -> None:
        self.positions[position_id].stop = float(stop)

    def close_position(self, position_id, reason="manual", price=None, ts=None, market=False) -> ClosedTrade:
        """Close at ``price`` (a stop or target level, already a bid/ask level) or, with ``market=True`` or no
        price, at the bid/ask built from that candle price for the position's side."""
        pos = self.positions.pop(position_id)
        if price is None:
            exit_price = self._market_exit(pos.symbol, pos.direction, self.current_price(pos.symbol))
        elif market:
            exit_price = self._market_exit(pos.symbol, pos.direction, price)
        else:
            exit_price = float(price)
        pnl = self.pnl_for(pos.symbol, pos.direction, pos.entry, exit_price, pos.lots)
        r = pos.r_at(exit_price)
        cost = self.commission(pos.symbol, pos.entry, pos.lots)
        if cost:
            pnl -= cost
            r -= cost / pos.risk_amount if pos.risk_amount > 0 else 0.0
        self._balance += pnl
        trade = ClosedTrade(
            id=pos.id, symbol=pos.symbol, direction=pos.direction, lots=pos.lots, entry=pos.entry, exit=exit_price,
            stop=pos.stop, take_profit=pos.take_profit, opened_at=pos.opened_at,
            closed_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.now("UTC").tz_localize(None), reason=reason, pnl=pnl, r=r,
            risk_amount=pos.risk_amount, initial_stop=pos.initial_stop, meta=dict(pos.meta),
        )
        self.closed.append(trade)
        return trade

    # ------------------------------------------------------------ simulation
    def on_candle(self, symbol: str, candle: Candle) -> List[ClosedTrade]:
        """Process a just-closed candle: stops first (conservative), then targets, then break-even."""
        symbol = symbol.upper()
        bid_off, ask_off = self._offsets(symbol)
        closed: List[ClosedTrade] = self._work_limits(symbol, candle, bid_off, ask_off) if self.limits else []
        close_ts = candle.timestamp
        for pos in list(self.open_positions(symbol)):
            if pos.opened_at is not None and pd.Timestamp(candle.timestamp) < pos.opened_at:
                continue
            if pos.direction is Direction.LONG:
                bid_low, bid_high, bid_open = candle.low + bid_off, candle.high + bid_off, candle.open + bid_off
                hit_stop = bid_low <= pos.stop
                hit_tp = bid_high >= pos.take_profit
                extreme = bid_high
                stop_fill = min(pos.stop, bid_open)      # a candle gapping through the stop fills at its open
            else:
                ask_high, ask_low, ask_open = candle.high + ask_off, candle.low + ask_off, candle.open + ask_off
                hit_stop = ask_high >= pos.stop
                hit_tp = ask_low <= pos.take_profit
                extreme = ask_low
                stop_fill = max(pos.stop, ask_open)
            if hit_stop:
                reason = "breakeven" if pos.breakeven_done else "stop"
                closed.append(self.close_position(pos.id, reason, stop_fill, close_ts))
                continue
            if hit_tp:
                closed.append(self.close_position(pos.id, "take_profit", pos.take_profit, close_ts))
                continue
            if not pos.breakeven_done and breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme, pos.breakeven_r):
                offset = self.settings.exits.breakeven_offset_pips * self._spec(symbol).pip_size
                pos.stop = pos.entry + pos.direction.sign * offset
                pos.breakeven_done = True
                # the candle that reached the trigger also traded back through the new stop: which came first is unknown,
                # so the backtest takes the stop (keeping the trade open booked a later target that was not certain)
                back = (bid_low <= pos.stop) if pos.direction is Direction.LONG else (ask_high >= pos.stop)
                if back:
                    closed.append(self.close_position(pos.id, "breakeven", pos.stop, close_ts))
                    continue
            hold = self.settings.exits.max_hold_hours
            if hold and pos.opened_at is not None and pd.Timestamp(close_ts) - pos.opened_at >= pd.Timedelta(hours=float(hold)):
                closed.append(self.close_position(pos.id, "time", float(candle.close), close_ts, market=True))
                continue
            weekend = self.settings.prop_firm.weekend_close
            if weekend and pos.opened_at is not None and pd.Timestamp(close_ts) >= weekend_cutoff_after(pos.opened_at, weekend):
                closed.append(self.close_position(pos.id, "weekend", float(candle.close), close_ts, market=True))
        self._last_price[symbol] = float(candle.close)
        self.equity_curve.append((close_ts, self.equity()))
        return closed
