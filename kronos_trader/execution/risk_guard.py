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
        self.day_start_balance = float(account_size)
        self.last_balance = float(account_size)
        self.last_trade_ts: Optional[pd.Timestamp] = None
        self.blackout_windows: List[Tuple[pd.Timestamp, pd.Timestamp, str]] = []
        self.halted_reason: Optional[str] = None
        self.first_breach: Optional[Tuple[pd.Timestamp, str]] = None   # the first rule hit, kept even if equity recovers

    def _day_of(self, ts: pd.Timestamp) -> pd.Timestamp:
        ts = pd.Timestamp(ts)
        tz = self.params.day_timezone
        if not tz:
            return ts.normalize()
        local = (ts.tz_localize("UTC") if ts.tzinfo is None else ts).tz_convert(tz)
        return local.normalize().tz_localize(None)

    def update(self, ts: pd.Timestamp, equity: float, balance: Optional[float] = None) -> None:
        """Feed every observation (each closed candle in a backtest, each loop in live), not only signals.

        The daily-loss baseline is the account balance when the day starts (FTMO: midnight CE(S)T), so a
        loss carried overnight in an open position counts against the day that closes it.
        """
        ts = pd.Timestamp(ts)
        day = self._day_of(ts)
        if balance is not None:
            self.last_balance = float(balance)
        if self.day is None or day != self.day:
            self.day = day
            self.day_start_balance = self.last_balance
        self.peak_equity = max(self.peak_equity, equity)
        if self.first_breach is None:
            p = self.params
            if self.daily_loss_pct(equity) >= p.daily_loss_limit_pct:
                self.first_breach = (ts, f"daily loss {self.daily_loss_pct(equity):.2f}% >= {p.daily_loss_limit_pct}%")
            elif self.drawdown_pct(equity) >= p.max_drawdown_pct:
                self.first_breach = (ts, f"drawdown {self.drawdown_pct(equity):.2f}% >= {p.max_drawdown_pct}%")

    def daily_loss_pct(self, equity: float) -> float:
        return (self.day_start_balance - equity) / self.account_size * 100.0

    def drawdown_pct(self, equity: float) -> float:
        base = self.peak_equity if self.params.drawdown_basis == "peak" else self.account_size
        return (base - equity) / self.account_size * 100.0

    def in_blackout(self, ts: pd.Timestamp) -> Optional[str]:
        ts = pd.Timestamp(ts)
        for start, end, label in self.blackout_windows:
            if start <= ts <= end:
                return label
        return None

    def can_open(self, broker: Broker, ts: pd.Timestamp, symbol: Optional[str] = None) -> Tuple[bool, str]:
        ts = pd.Timestamp(ts)
        equity = broker.equity()
        self.update(ts, equity, broker.balance())
        p = self.params
        if len(broker.open_positions()) >= p.max_open_trades:
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
