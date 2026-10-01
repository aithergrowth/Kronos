"""Paper broker with executable-side spread and conservative OHLC exit ordering.

Opening quotes are ordered before intrabar extremes. Otherwise unknown intrabar
paths favour an existing stop, or a reachable break-even return before a farther
target. These are simulation assumptions, not reconstructed tick sequences.
"""
from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from ..config import Settings
from ..core.candles import Candle
from ..core.types import Direction
from ..strategy.exits import breakeven_reached
from .base import Broker, ClosedTrade, Position


class PaperBroker(Broker):
    def __init__(self, settings: Optional[Settings] = None, equity: Optional[float] = None,
                 spread_pips: Optional[Dict[str, float]] = None, use_spread: bool = True):
        self.settings = settings or Settings()
        self._balance = float(equity if equity is not None else self.settings.account_size)
        self.initial_balance = self._balance
        self.spread_pips = dict(spread_pips or {})
        self.use_spread = use_spread
        self.positions: Dict[str, Position] = {}
        self.closed: List[ClosedTrade] = []
        self.equity_curve: List[Tuple[pd.Timestamp, float]] = []
        self._last_price: Dict[str, float] = {}
        self._ids = itertools.count(1)
        self._close_cursor = 0

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

    def pnl_for(self, symbol: str, direction: Direction, entry: float, exit_price: float, lots: float) -> float:
        spec = self._spec(symbol)
        pips = direction.sign * (exit_price - entry) / spec.pip_size
        return pips * spec.pip_value_per_lot * lots

    def set_price(self, symbol: str, price: float) -> None:
        self._last_price[symbol.upper()] = float(price)

    def market_fill_price(self, symbol: str, direction: Direction, price: Optional[float] = None) -> float:
        """Preview a market fill from a midpoint, using the order's buy/sell side."""
        mid = float(price if price is not None else self.current_price(symbol))
        return mid + direction.sign * self._half_spread(symbol)

    def _activate_breakeven(self, pos: Position) -> None:
        offset = self.settings.exits.breakeven_offset_pips * self._spec(pos.symbol).pip_size
        pos.stop = pos.entry + pos.direction.sign * offset
        pos.breakeven_done = True

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        unrealized = 0.0
        for pos in self.positions.values():
            price = self._last_price.get(pos.symbol)
            if price is not None:
                liquidation = self.market_fill_price(pos.symbol, Direction(-pos.direction.sign), price)
                unrealized += self.pnl_for(pos.symbol, pos.direction, pos.entry, liquidation, pos.lots)
        return self._balance + unrealized

    def balance(self) -> float:
        return self._balance

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        if symbol is None:
            return list(self.positions.values())
        return [p for p in self.positions.values() if p.symbol == symbol.upper()]

    def current_price(self, symbol: str) -> float:
        return self._last_price[symbol.upper()]

    def place_market_order(self, symbol, direction, lots, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                           meta=None, price=None, ts=None) -> Position:
        symbol = symbol.upper()
        mid = float(price if price is not None else self.current_price(symbol))
        fill = self.market_fill_price(symbol, direction, mid)
        pos = Position(
            id=f"P{next(self._ids)}", symbol=symbol, direction=direction, lots=float(lots), entry=fill,
            stop=float(stop), take_profit=float(take_profit), opened_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.utcnow(),
            risk_amount=float(risk_amount), risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
            initial_stop=float(stop), meta=dict(meta or {}),
        )
        self.positions[pos.id] = pos
        self._last_price[symbol] = mid
        return pos

    def modify_stop(self, position_id: str, stop: float) -> None:
        self.positions[position_id].stop = float(stop)

    def close_position(self, position_id, reason="manual", price=None, ts=None) -> ClosedTrade:
        """Market liquidation: an explicit ``price`` is a midpoint, not a bid/ask fill."""
        pos = self.positions[position_id]
        exit_price = self.market_fill_price(pos.symbol, Direction(-pos.direction.sign), price)
        return self._close_at_price(position_id, reason, exit_price, ts)

    def _close_at_price(self, position_id, reason, exit_price, ts=None) -> ClosedTrade:
        """Record an already executable SL/TP/gap price without adding spread twice."""
        pos = self.positions.pop(position_id)
        exit_price = float(exit_price)
        pnl = self.pnl_for(pos.symbol, pos.direction, pos.entry, exit_price, pos.lots)
        self._balance += pnl
        r = pos.r_at(exit_price)
        trade = ClosedTrade(
            id=pos.id, symbol=pos.symbol, direction=pos.direction, lots=pos.lots, entry=pos.entry, exit=exit_price,
            stop=pos.stop, take_profit=pos.take_profit, opened_at=pos.opened_at,
            closed_at=pd.Timestamp(ts) if ts is not None else pd.Timestamp.utcnow(), reason=reason, pnl=pnl, r=r,
            risk_amount=pos.risk_amount, initial_stop=pos.initial_stop, meta=dict(pos.meta),
        )
        self.closed.append(trade)
        return trade

    # ------------------------------------------------------------ simulation
    def on_candle(self, symbol: str, candle: Candle) -> List[ClosedTrade]:
        """Simulate exits from OHLC; ambiguous paths use the worse reachable exit.

        Stop gaps fill at the executable opening quote. A target marketable at
        the open fills at its limit (no assumed favourable price improvement).
        Then an existing stop takes priority over unknown intrabar ordering.
        A BE trigger followed by a possible return is treated as a BE exit,
        unless the target necessarily precedes the trigger. Exact hit times,
        liquidity, slippage beyond opening gaps, commission and swap are absent.
        """
        symbol = symbol.upper()
        half = self._half_spread(symbol)
        closed: List[ClosedTrade] = []
        close_ts = candle.timestamp
        for pos in list(self.open_positions(symbol)):
            if pos.opened_at is not None and pd.Timestamp(candle.timestamp) < pos.opened_at:
                continue
            sign = pos.direction.sign
            opening = candle.open - sign * half
            if pos.direction is Direction.LONG:
                adverse, extreme = candle.low - half, candle.high - half
            else:
                adverse, extreme = candle.high + half, candle.low + half
            if sign * (opening - pos.stop) <= 0:
                reason = "breakeven" if pos.breakeven_done else "stop"
                closed.append(self._close_at_price(pos.id, reason, opening, close_ts))
                continue
            if sign * (opening - pos.take_profit) >= 0:
                closed.append(self._close_at_price(pos.id, "take_profit", pos.take_profit, close_ts))
                continue
            if not pos.breakeven_done and breakeven_reached(pos.direction, pos.entry, pos.risk_distance, opening, pos.breakeven_r):
                self._activate_breakeven(pos)
                if sign * (opening - pos.stop) <= 0:
                    closed.append(self._close_at_price(pos.id, "breakeven", opening, close_ts))
                    continue
            if sign * (adverse - pos.stop) <= 0:
                reason = "breakeven" if pos.breakeven_done else "stop"
                closed.append(self._close_at_price(pos.id, reason, pos.stop, close_ts))
                continue
            hit_tp = sign * (extreme - pos.take_profit) >= 0
            target_precedes_be = sign * (pos.take_profit - pos.entry) <= pos.risk_distance * pos.breakeven_r
            if hit_tp and target_precedes_be:
                closed.append(self._close_at_price(pos.id, "take_profit", pos.take_profit, close_ts))
                continue
            if not pos.breakeven_done and breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme, pos.breakeven_r):
                self._activate_breakeven(pos)
                activation = pos.entry + sign * pos.risk_distance * pos.breakeven_r
                if sign * (activation - pos.stop) <= 0:
                    closed.append(self._close_at_price(pos.id, "breakeven", activation, close_ts))
                    continue
                if sign * (adverse - pos.stop) <= 0:
                    closed.append(self._close_at_price(pos.id, "breakeven", pos.stop, close_ts))
                    continue
            if hit_tp:
                closed.append(self._close_at_price(pos.id, "take_profit", pos.take_profit, close_ts))
        self._last_price[symbol] = float(candle.close)
        self.equity_curve.append((close_ts, self.equity()))
        return closed
