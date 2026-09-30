"""Live loop: fetch candles -> analyse -> notify -> (optionally) execute.

The runner is data-source agnostic.  ``fetch`` returns ``{Timeframe: CandleSeries}``
for the symbol - from the TradingView CSV cache, the MetaTrader terminal or the
direct MCP client.  With ``dry_run=True`` nothing is sent to a broker; signals
only go to Telegram / stdout.
"""
from __future__ import annotations

import time
from typing import Callable, Dict, Optional

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis
from .execution.base import Broker
from .execution.risk_guard import RiskGuard
from .notify.telegram import TelegramNotifier
from .strategy.engine import StrategyEngine
from .strategy.exits import breakeven_reached


class LiveRunner:
    def __init__(
        self,
        settings: Settings,
        symbol: str,
        fetch: Callable[[], Dict[Timeframe, CandleSeries]],
        broker: Optional[Broker] = None,
        notifier: Optional[TelegramNotifier] = None,
        engine: Optional[StrategyEngine] = None,
        guard: Optional[RiskGuard] = None,
        dry_run: bool = True,
        notify_every_scan: bool = False,
    ):
        self.settings = settings
        self.symbol = symbol.upper()
        self.fetch = fetch
        self.broker = broker
        self.notifier = notifier or TelegramNotifier(params=settings.telegram, dry_run=True)
        self.engine = engine or StrategyEngine(settings)
        self.guard = guard or RiskGuard(settings.prop_firm, settings.account_size)
        self.dry_run = dry_run
        self.notify_every_scan = notify_every_scan
        self.seen: set = set()
        self.last_analysis: Optional[Analysis] = None

    def manage_positions(self, views: Dict[Timeframe, CandleSeries]) -> None:
        """Move stops to break-even per the exit rules (no partials, let SL/TP run)."""
        if self.broker is None or not views:
            return
        lowest = views[min(views)]
        last = lowest.last
        for pos in self.broker.open_positions(self.symbol):
            if pos.breakeven_done:
                continue
            extreme = last.high if pos.direction.sign > 0 else last.low
            if breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme, pos.breakeven_r):
                self.broker.modify_stop(pos.id, pos.entry)
                pos.breakeven_done = True
                self.notifier.send(f"{self.symbol}: stop moved to break-even on {pos.id} ({pos.breakeven_r:.0f}R reached)")

    def step(self, now: Optional[pd.Timestamp] = None) -> Analysis:
        views = self.fetch()
        spec = self.settings.symbol(self.symbol)
        equity = self.broker.equity() if self.broker is not None else self.settings.account_size
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=True)
        self.last_analysis = analysis
        self.manage_positions(views)
        if analysis.has_valid_signal:
            setup = analysis.signal.setup
            key = (setup.poi.key, str(setup.confirmation.timestamp))
            if key not in self.seen:
                self.seen.add(key)
                self.notifier.send_setup(setup, analysis.signal.forecast, spec)
                if self.broker is not None:
                    ok, reason = self.guard.can_open(self.broker, analysis.timestamp, self.symbol)
                    if not ok:
                        self.notifier.send(f"{self.symbol}: setup NOT executed - {reason}")
                    elif self.dry_run:
                        self.notifier.send(f"{self.symbol}: dry-run, order not sent")
                    else:
                        pos = self.broker.place_market_order(
                            self.symbol, setup.direction, setup.lots, setup.stop, setup.take_profit, setup.risk_amount,
                            setup.risk_distance, setup.breakeven_r,
                            meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value}"},
                            price=setup.entry, ts=analysis.timestamp)
                        self.guard.record_trade(analysis.timestamp)
                        self.notifier.send(f"{self.symbol}: order filled {pos.id} @ {pos.entry}")
        elif self.notify_every_scan:
            self.notifier.send_analysis(analysis, spec)
        return analysis

    def run_forever(self, poll_seconds: int = 60) -> None:
        while True:
            try:
                self.step()
            except Exception as exc:  # keep the loop alive, report the problem
                self.notifier.send(f"{self.symbol}: live loop error: {exc}")
            time.sleep(poll_seconds)
