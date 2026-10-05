"""Prop-firm risk guard.

Rules enforced before any order is sent:

* max 1 open trade per funded account (rule),
* daily loss limit and maximum drawdown with a safety margin below the
  typical 5 % / 10 % prop-firm limits,
* an optional monthly loss limit on the month's closed trades,
* optional minimum spacing between trades and news blackout windows.
"""
from __future__ import annotations

from typing import Callable, List, Optional, Tuple

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
        self.month: Optional[pd.Period] = None
        self.month_start_balance = float(account_size)
        # the broker's closed P&L since a UTC time, when it can tell: a guard that starts mid-day or mid-month (a restart)
        # takes its baselines from it instead of from the balance it first sees
        self.realized_since: Optional[Callable[[pd.Timestamp], Optional[float]]] = None
        self.last_balance = float(account_size)
        self.last_trade_ts: Optional[pd.Timestamp] = None
        self.blackout_windows: List[Tuple[pd.Timestamp, pd.Timestamp, str]] = []
        self.halted_reason: Optional[str] = None
        self.first_breach: Optional[Tuple[pd.Timestamp, str]] = None   # the first published rule hit, kept even if equity recovers

    def rules(self) -> dict:
        p = self.params
        return {"account_size": self.account_size, "day_timezone": p.day_timezone,
                "recorded_against": {"daily_loss_pct_of_initial": p.record_daily_loss_pct, "max_loss_pct_of_initial_static": p.record_max_loss_pct},
                "halting_limits": {"daily_loss_pct": p.daily_loss_limit_pct, "monthly_loss_pct": p.monthly_loss_limit_pct,
                                   "max_drawdown_pct": p.max_drawdown_pct, "drawdown_basis": p.drawdown_basis,
                                   "max_open_trades": p.max_open_trades, "max_open_per_symbol": p.max_open_per_symbol}}

    def _day_of(self, ts: pd.Timestamp) -> pd.Timestamp:
        ts = pd.Timestamp(ts)
        tz = self.params.day_timezone
        if not tz:
            return ts.normalize()
        local = (ts.tz_localize("UTC") if ts.tzinfo is None else ts).tz_convert(tz)
        return local.normalize().tz_localize(None)

    def _utc_start(self, local_start: pd.Timestamp) -> pd.Timestamp:
        """A local (firm time zone) midnight as naive UTC."""
        tz = self.params.day_timezone
        if not tz:
            return pd.Timestamp(local_start)
        return pd.Timestamp(local_start).tz_localize(tz).tz_convert("UTC").tz_localize(None)

    def _baseline(self, local_start: pd.Timestamp) -> float:
        """The balance at ``local_start``: the current balance less what closed since, when the broker can say."""
        if self.realized_since is not None:
            try:
                done = self.realized_since(self._utc_start(local_start))
                if done is not None:
                    return self.last_balance - float(done)
            except Exception:
                pass
        return self.last_balance

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
            first = self.day is None
            self.day = day
            self.day_start_balance = self._baseline(day) if first else self.last_balance
        month = day.to_period("M")
        if self.month is None or month != self.month:
            first = self.month is None
            self.month = month
            self.month_start_balance = self._baseline(month.to_timestamp()) if first else self.last_balance
        self.peak_equity = max(self.peak_equity, equity)
        if self.first_breach is None:
            p = self.params
            daily = self.daily_loss_pct(equity)
            static_loss = (self.account_size - equity) / self.account_size * 100.0
            if daily >= p.record_daily_loss_pct:
                self.first_breach = (ts, f"daily loss {daily:.2f}% >= {p.record_daily_loss_pct}% (baseline {self.day_start_balance:,.0f})")
            elif static_loss >= p.record_max_loss_pct:
                self.first_breach = (ts, f"loss {static_loss:.2f}% of the initial balance >= {p.record_max_loss_pct}%")

    @property
    def day_start_equity(self) -> float:
        """Backwards-compatible name: the day's baseline is the balance when the day started."""
        return self.day_start_balance

    def monthly_loss_pct(self, balance: Optional[float] = None) -> float:
        """The month's closed loss as a share of the account (positive = a loss)."""
        b = self.last_balance if balance is None else float(balance)
        return (self.month_start_balance - b) / self.account_size * 100.0

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
        balance = getattr(broker, "balance", None)
        self.update(ts, equity, balance() if callable(balance) else None)
        p = self.params
        if len(broker.open_positions()) >= p.max_open_trades:
            return False, f"max {p.max_open_trades} open trade(s) per account"
        if symbol and len(broker.open_positions(symbol)) >= max(1, p.max_open_per_symbol):
            return False, f"max {max(1, p.max_open_per_symbol)} open trade(s) in {symbol}"
        if self.daily_loss_pct(equity) >= p.daily_loss_limit_pct:
            return False, f"daily loss {self.daily_loss_pct(equity):.2f}% reached the {p.daily_loss_limit_pct}% limit"
        if p.monthly_loss_limit_pct and self.monthly_loss_pct() >= p.monthly_loss_limit_pct:
            return False, f"monthly loss {self.monthly_loss_pct():.2f}% reached the {p.monthly_loss_limit_pct}% limit (trading resumes next month)"
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
