"""Paper broker: fills and stop/target checks on bid and ask built from the candles
(``quote_basis="mid"``: candle +/- half the spread; ``"bid"``: the candles are bid
quotes, as HistData's are, so ask = bid + spread), checks SL/TP on every closed
candle, fills a stop at the open when a candle gaps through it, moves the stop to
break-even per the exit rules and never takes partials."""
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
        bid_off, ask_off = self._offsets(symbol)
        fill = mid + (ask_off if direction is Direction.LONG else bid_off)
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
        bid_off, ask_off = self._offsets(symbol)
        closed: List[ClosedTrade] = []
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
        self._last_price[symbol] = float(candle.close)
        self.equity_curve.append((close_ts, self.equity()))
        return closed
