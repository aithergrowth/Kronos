"""Paper broker: fills at mid +/- half spread, checks SL/TP on every closed candle,
moves the stop to break-even per the exit rules and never takes partials."""
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

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        unrealized = 0.0
        for pos in self.positions.values():
            price = self._last_price.get(pos.symbol)
            if price is not None:
                unrealized += self.pnl_for(pos.symbol, pos.direction, pos.entry, price, pos.lots)
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
        fill = mid + direction.sign * self._half_spread(symbol)
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
        pos = self.positions.pop(position_id)
        exit_price = float(price if price is not None else self.current_price(pos.symbol))
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
        """Process a just-closed candle: stops first (conservative), then targets, then break-even."""
        symbol = symbol.upper()
        half = self._half_spread(symbol)
        closed: List[ClosedTrade] = []
        close_ts = candle.timestamp
        for pos in list(self.open_positions(symbol)):
            if pos.opened_at is not None and pd.Timestamp(candle.timestamp) < pos.opened_at:
                continue
            if pos.direction is Direction.LONG:
                bid_low, bid_high = candle.low - half, candle.high - half
                hit_stop = bid_low <= pos.stop
                hit_tp = bid_high >= pos.take_profit
                extreme = bid_high
            else:
                ask_high, ask_low = candle.high + half, candle.low + half
                hit_stop = ask_high >= pos.stop
                hit_tp = ask_low <= pos.take_profit
                extreme = ask_low
            if hit_stop:
                reason = "breakeven" if pos.breakeven_done else "stop"
                closed.append(self.close_position(pos.id, reason, pos.stop, close_ts))
                continue
            if hit_tp:
                closed.append(self.close_position(pos.id, "take_profit", pos.take_profit, close_ts))
                continue
            if not pos.breakeven_done and breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme, pos.breakeven_r):
                offset = self.settings.exits.breakeven_offset_pips * self._spec(symbol).pip_size
                pos.stop = pos.entry + pos.direction.sign * offset
                pos.breakeven_done = True
        self._last_price[symbol] = float(candle.close)
        self.equity_curve.append((close_ts, self.equity()))
        return closed
