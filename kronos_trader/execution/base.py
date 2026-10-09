"""Broker abstraction shared by the paper broker, MetaTrader 5 and the backtester."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Direction


@dataclass
class Position:
    id: str
    symbol: str
    direction: Direction
    lots: float
    entry: float
    stop: float
    take_profit: float
    opened_at: pd.Timestamp
    risk_amount: float
    risk_distance: float
    breakeven_r: float
    initial_stop: float
    breakeven_done: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    status: str = "filled"             # "filled" (confirmed) | "pending" (submitted, fill not confirmed yet)

    def r_at(self, price: float) -> float:
        if self.risk_distance <= 0:
            return 0.0
        return self.direction.sign * (price - self.entry) / self.risk_distance

    @property
    def planned_rr(self) -> float:
        return abs(self.take_profit - self.entry) / self.risk_distance if self.risk_distance else 0.0


@dataclass
class ClosedTrade:
    id: str
    symbol: str
    direction: Direction
    lots: float
    entry: float
    exit: float
    stop: float
    take_profit: float
    opened_at: pd.Timestamp
    closed_at: pd.Timestamp
    reason: str
    pnl: float
    r: float
    risk_amount: float
    initial_stop: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LimitOrder:
    """A resting limit entry (risk.limit_entry_fraction): it becomes a Position when price reaches ``price``; the live runner
    cancels it at ``expires_at`` or when the target trades first."""
    id: str
    symbol: str
    direction: Direction
    lots: float
    price: float
    stop: float
    take_profit: float
    risk_amount: float
    risk_distance: float
    breakeven_r: float
    placed_at: pd.Timestamp
    expires_at: pd.Timestamp
    meta: Dict[str, Any] = field(default_factory=dict)


class Broker(ABC):
    @abstractmethod
    def equity(self) -> float: ...

    @abstractmethod
    def balance(self) -> float: ...

    @abstractmethod
    def open_positions(self, symbol: Optional[str] = None) -> List[Position]: ...

    @abstractmethod
    def place_market_order(self, symbol: str, direction: Direction, lots: float, stop: float, take_profit: float,
                           risk_amount: float, risk_distance: float, breakeven_r: float,
                           meta: Optional[Dict[str, Any]] = None, price: Optional[float] = None,
                           ts: Optional[pd.Timestamp] = None, price_is_fill: bool = False) -> Position: ...

    # limit entries (brokers without them refuse; the live runner only places one when risk.limit_entry_fraction > 0)
    def place_limit_order(self, symbol: str, direction: Direction, lots: float, price: float, stop: float, take_profit: float,
                          risk_amount: float, risk_distance: float, breakeven_r: float, expires_at: pd.Timestamp,
                          meta: Optional[Dict[str, Any]] = None, ts: Optional[pd.Timestamp] = None) -> "LimitOrder":
        raise NotImplementedError(f"{type(self).__name__} places no limit orders")

    def limit_orders(self, symbol: Optional[str] = None) -> List["LimitOrder"]:
        return []

    def cancel_limit(self, order_id: str) -> None:
        raise NotImplementedError(f"{type(self).__name__} places no limit orders")

    def limit_state(self, order_id: str):
        """``("pending" | "filled" | "gone", Position or None)``: still resting, filled (the position, None when it closed
        already), or no longer on the server (cancelled or expired there)."""
        return "gone", None

    def fill_price(self, symbol: str, direction: Direction, base: Optional[float] = None) -> float:
        """The executable price for a market order now: the ask for a long, the bid for a short.

        Brokers with a quote override this; the default is the current (mid) price, so sizing on it
        understates the spread by half.
        """
        return float(base if base is not None else self.current_price(symbol))

    @abstractmethod
    def modify_stop(self, position_id: str, stop: float) -> None: ...

    @abstractmethod
    def close_position(self, position_id: str, reason: str = "manual", price: Optional[float] = None,
                       ts: Optional[pd.Timestamp] = None) -> ClosedTrade: ...

    @abstractmethod
    def current_price(self, symbol: str) -> float: ...

    # optional capabilities -------------------------------------------------
    def recent_closes(self) -> List[ClosedTrade]:
        """Trades closed since the last call (stop / target hits at the broker)."""
        return []

    def idle(self, seconds: float) -> None:
        """Wait between polls; brokers with an event loop override this so it keeps running."""
        time.sleep(seconds)

    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        raise NotImplementedError(f"{type(self).__name__} does not provide candles")
