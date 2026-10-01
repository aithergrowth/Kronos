"""Event-driven backtester.

Walks the ``step_tf`` candles one closed candle at a time.  At every step the
paper broker first processes the candle (stops, targets, break-even), then the
engine receives slices whose candle close timestamps are no later than that
step. Candle completeness and correct session anchoring remain the caller's
responsibility.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

from ..config import Settings
from ..core.timeframe import Timeframe
from ..data.resample import MultiTimeframeData
from ..execution.base import ClosedTrade
from ..execution.paper import PaperBroker
from ..execution.risk_guard import RiskGuard
from ..strategy.engine import StrategyEngine
from ..strategy.risk import size_position


@dataclass
class BacktestResult:
    symbol: str
    step_tf: Timeframe
    start: pd.Timestamp
    end: pd.Timestamp
    initial_equity: float
    final_equity: float
    trades: List[ClosedTrade]
    equity_curve: List[Tuple[pd.Timestamp, float]]
    steps: int = 0
    signals: int = 0
    rejected_by_guard: int = 0
    guard_reasons: Dict[str, int] = field(default_factory=dict)
    rejection_reasons: Dict[str, int] = field(default_factory=dict)
    runtime_seconds: float = 0.0

    def trades_frame(self) -> pd.DataFrame:
        rows = []
        for t in self.trades:
            rows.append({
                "id": t.id, "symbol": t.symbol, "direction": t.direction.name, "opened_at": t.opened_at, "closed_at": t.closed_at,
                "entry": t.entry, "exit": t.exit, "stop": t.initial_stop, "final_stop": t.stop, "take_profit": t.take_profit, "lots": t.lots,
                "pnl": t.pnl, "r": t.r, "reason": t.reason,
                "poi_tf": t.meta.get("poi_tf"), "confirmation": t.meta.get("confirmation"),
                "confirmation_tf": t.meta.get("confirmation_tf"), "planned_rr": t.meta.get("planned_rr"),
                "signal_entry": t.meta.get("signal_entry"), "signal_rr": t.meta.get("signal_rr"),
                "kronos": t.meta.get("kronos"),
            })
        return pd.DataFrame(rows)


def _bucket(reason: str) -> str:
    """Collapse a rejection message into a short category for the report."""
    if ": " in reason:
        head, tail = reason.split(": ", 1)
        if " POI " in head:
            tail = tail.split(" at ")[0] if tail.startswith("touched") else tail
            return "POI - " + tail[:70]
        if head in ("bullish", "bearish"):
            return f"{head} - {tail[:60]}"
    return reason[:70]


class Backtester:
    def __init__(
        self,
        settings: Settings,
        data: MultiTimeframeData,
        symbol: str,
        step_tf: Optional[Timeframe] = None,
        engine: Optional[StrategyEngine] = None,
        forecaster=None,
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
        use_spread: bool = True,
        progress: bool = False,
    ):
        self.settings = settings
        self.data = data
        self.symbol = symbol.upper()
        self.step_tf = Timeframe.parse(step_tf) if step_tf else min(data.series)
        self.engine = engine or StrategyEngine(settings, forecaster)
        self.start = pd.Timestamp(start) if start is not None else None
        self.end = pd.Timestamp(end) if end is not None else None
        self.use_spread = use_spread
        self.progress = progress

    def run(self) -> BacktestResult:
        t0 = time.time()
        s = self.settings
        broker = PaperBroker(s, use_spread=self.use_spread)
        guard = RiskGuard(s.prop_firm, s.account_size)
        step = self.data[self.step_tf]
        seen: Set[Tuple] = set()
        signals = rejected = steps = 0
        guard_reasons: Dict[str, int] = {}
        rejection_reasons: Dict[str, int] = {}
        first_ts = last_ts = None
        last_processed_candle = None

        n = len(step)
        report_every = max(1, n // 20)
        for i in range(n):
            candle = step[i]
            ts = candle.timestamp
            if self.start is not None and ts < self.start:
                continue
            if self.end is not None and ts > self.end:
                break
            first_ts = first_ts or ts
            last_ts = ts
            last_processed_candle = candle
            steps += 1
            broker.on_candle(self.symbol, candle)
            now = self.step_tf.close_time(ts)
            views = self.data.as_of(now, lookback=s.structure.lookback)
            analysis = self.engine.analyze(self.symbol, views, equity=broker.equity(), now=now)
            for r in analysis.rejections:
                key = _bucket(r)
                rejection_reasons[key] = rejection_reasons.get(key, 0) + 1
            if analysis.has_valid_signal:
                setup = analysis.signal.setup
                key = (setup.poi.key, str(setup.confirmation.timestamp))
                if key in seen:
                    continue
                seen.add(key)
                signals += 1
                ok, reason = guard.can_open(broker, now, self.symbol)
                if not ok:
                    rejected += 1
                    guard_reasons[reason] = guard_reasons.get(reason, 0) + 1
                    continue
                # A higher-timeframe confirmation can still be the latest one
                # after its close. It is a signal reference, not today's fill.
                entry = broker.market_fill_price(self.symbol, setup.direction, candle.close)
                spec = s.symbol(self.symbol)
                reason = None
                if not all(math.isfinite(x) for x in (entry, setup.stop, setup.take_profit)):
                    reason = "execution - non-finite entry, stop or target"
                elif setup.direction.sign * (entry - setup.stop) <= 0:
                    reason = "execution - stop already crossed"
                elif setup.direction.sign * (setup.take_profit - entry) <= 0:
                    reason = "execution - target already crossed"
                else:
                    lots, risk_amount, risk_distance, _ = size_position(
                        broker.equity(), entry, setup.stop, spec, s.risk)
                    rr_distance = risk_distance if s.risk.rr_includes_buffer else abs(entry - setup.stop)
                    rr = abs(setup.take_profit - entry) / rr_distance
                    if rr < s.risk.min_rr:
                        reason = "execution - R:R below minimum at current price"
                    elif lots <= 0:
                        reason = "execution - position below minimum lot at current price"
                if reason is not None:
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                    continue
                fc = analysis.signal.forecast
                broker.place_market_order(
                    self.symbol, setup.direction, lots, setup.stop, setup.take_profit, risk_amount,
                    risk_distance, setup.breakeven_r,
                    meta={
                        "poi_tf": setup.poi.timeframe.label, "poi": (setup.poi.low, setup.poi.high),
                        "confirmation": setup.confirmation.type.value, "confirmation_tf": setup.confirmation.timeframe.label,
                        "planned_rr": round(rr, 2), "signal_rr": round(setup.rr, 2),
                        "signal_entry": setup.entry, "tp_source": setup.tp_source,
                        "kronos": None if fc is None else f"{fc.direction} {fc.confidence:.0%}",
                    },
                    price=candle.close, ts=now,
                )
                guard.record_trade(now)
            if self.progress and i % report_every == 0:
                print(f"  {i}/{n} {ts} equity={broker.equity():,.0f} trades={len(broker.closed)}", flush=True)

        # flatten at the end so every trade has an outcome
        if broker.open_positions() and last_processed_candle is not None:
            # A bounded run must not mark positions using candles after ``end``.
            last_price = last_processed_candle.close
            for pos in list(broker.open_positions()):
                broker.close_position(pos.id, "end_of_data", last_price,
                                      self.step_tf.close_time(last_processed_candle.timestamp))

        return BacktestResult(
            symbol=self.symbol, step_tf=self.step_tf, start=first_ts, end=last_ts,
            initial_equity=broker.initial_balance, final_equity=broker.balance(), trades=list(broker.closed),
            equity_curve=list(broker.equity_curve), steps=steps, signals=signals, rejected_by_guard=rejected,
            guard_reasons=guard_reasons, rejection_reasons=rejection_reasons, runtime_seconds=time.time() - t0,
        )
