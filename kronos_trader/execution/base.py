"""Broker abstraction shared by the paper broker, MetaTrader 5 and the backtester."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

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
                           ts: Optional[pd.Timestamp] = None) -> Position: ...

    @abstractmethod
    def modify_stop(self, position_id: str, stop: float) -> None: ...

    @abstractmethod
    def close_position(self, position_id: str, reason: str = "manual", price: Optional[float] = None,
                       ts: Optional[pd.Timestamp] = None) -> ClosedTrade: ...

    @abstractmethod
    def current_price(self, symbol: str) -> float: ...
