"""Prop-firm risk guard.

Rules enforced before any order is sent:

* max 1 open trade per funded account (rule),
* daily loss limit and maximum drawdown with a safety margin below the
  typical 5 % / 10 % prop-firm limits,
* optional minimum spacing between trades and news blackout windows.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import pandas as pd

from ..config import PropFirmParams
from .base import Broker


class RiskGuard:
    def __init__(self, params: Optional[PropFirmParams] = None, account_size: float = 100_000.0):
        self.params = params or PropFirmParams()
        self.account_size = float(account_size)
        self.peak_equity = float(account_size)
        self.day: Optional[pd.Timestamp] = None
        self.day_start_equity = float(account_size)
        self.last_trade_ts: Optional[pd.Timestamp] = None
        self.blackout_windows: List[Tuple[pd.Timestamp, pd.Timestamp, str]] = []
        self.halted_reason: Optional[str] = None

    def update(self, ts: pd.Timestamp, equity: float) -> None:
        ts = pd.Timestamp(ts)
        day = ts.normalize()
        if self.day is None or day != self.day:
            self.day = day
            self.day_start_equity = equity
        self.peak_equity = max(self.peak_equity, equity)

    def daily_loss_pct(self, equity: float) -> float:
        return (self.day_start_equity - equity) / self.account_size * 100.0

    def drawdown_pct(self, equity: float) -> float:
        return (self.peak_equity - equity) / self.account_size * 100.0

    def in_blackout(self, ts: pd.Timestamp) -> Optional[str]:
        ts = pd.Timestamp(ts)
        for start, end, label in self.blackout_windows:
            if start <= ts <= end:
                return label
        return None

    def can_open(self, broker: Broker, ts: pd.Timestamp, symbol: Optional[str] = None) -> Tuple[bool, str]:
        ts = pd.Timestamp(ts)
        equity = broker.equity()
        self.update(ts, equity)
        p = self.params
        positions = broker.open_positions()  # reconciliation can discover an execution halt
        execution_halt = getattr(broker, "execution_halt_reason", None)
        if execution_halt:
            return False, f"broker execution halted: {execution_halt}"
        if len(positions) >= p.max_open_trades:
            return False, f"max {p.max_open_trades} open trade(s) per account"
        if self.daily_loss_pct(equity) >= p.daily_loss_limit_pct:
            return False, f"daily loss {self.daily_loss_pct(equity):.2f}% reached the {p.daily_loss_limit_pct}% limit"
        if self.drawdown_pct(equity) >= p.max_drawdown_pct:
            self.halted_reason = f"drawdown {self.drawdown_pct(equity):.2f}% reached the {p.max_drawdown_pct}% limit"
            return False, self.halted_reason
        if self.last_trade_ts is not None and p.min_minutes_between_trades:
            gap = (ts - self.last_trade_ts).total_seconds() / 60.0
            if gap < p.min_minutes_between_trades:
                return False, f"only {gap:.0f} min since the last trade (min {p.min_minutes_between_trades})"
        label = self.in_blackout(ts)
        if label:
            return False, f"news blackout: {label}"
        return True, "ok"

    def record_trade(self, ts: pd.Timestamp) -> None:
        self.last_trade_ts = pd.Timestamp(ts)
