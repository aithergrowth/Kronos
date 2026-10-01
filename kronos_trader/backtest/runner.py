"""Event-driven backtester.

Walks the ``step_tf`` candles one closed candle at a time.  At every step the
paper broker first processes the candle (stops, targets, break-even), then the
engine sees exactly the candles that were closed at that moment on every
timeframe, so nothing in the analysis can peek into the future.
"""
from __future__ import annotations

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
from ..strategy.risk import resize_at


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
                "tp_source": t.meta.get("tp_source"), "touched_at": t.meta.get("touched_at"), "confirmed_at": t.meta.get("confirmed_at"),
                "entry_planned": t.meta.get("entry_planned"), "rr_at_fill": t.meta.get("rr_at_fill"), "lots_planned": t.meta.get("lots_planned"),
                "poi_low": (t.meta.get("poi") or (None, None))[0],
                "poi_high": (t.meta.get("poi") or (None, None))[1], "kronos": t.meta.get("kronos"),
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
        quote_basis: str = "mid",
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
        self.quote_basis = quote_basis

    def run(self) -> BacktestResult:
        t0 = time.time()
        s = self.settings
        broker = PaperBroker(s, use_spread=self.use_spread, quote_basis=self.quote_basis)
        spec = s.symbol(self.symbol)
        guard = RiskGuard(s.prop_firm, s.account_size)
        step = self.data[self.step_tf]
        seen: Set[Tuple] = set()
        signals = rejected = steps = 0
        guard_reasons: Dict[str, int] = {}
        rejection_reasons: Dict[str, int] = {}
        first_ts = last_ts = None
        last_candle = None

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
            last_candle = candle
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
                # market order at the price of this moment (the close of the candle that just closed), with the
                # same re-check the live runner makes: the confirmation close may be older than ``now`` when a
                # session or news gate held the signal back
                price_now = float(candle.close)
                wrong_side = (setup.direction.sign > 0 and price_now <= setup.stop) or (setup.direction.sign < 0 and price_now >= setup.stop)
                lots_now, risk_amount_now, risk_distance_now, rr_now, _ = resize_at(
                    price_now, setup.stop, setup.take_profit, broker.equity(), spec, s.risk)
                if wrong_side or rr_now < s.risk.min_rr or lots_now <= 0:
                    rejected += 1
                    reason = ("price moved: wrong side of the stop" if wrong_side else
                              "price moved: R:R below minimum" if rr_now < s.risk.min_rr else
                              "price moved: stop too wide for the minimum lot")
                    guard_reasons[reason] = guard_reasons.get(reason, 0) + 1
                    continue
                fc = analysis.signal.forecast
                broker.place_market_order(
                    self.symbol, setup.direction, lots_now, setup.stop, setup.take_profit, risk_amount_now,
                    risk_distance_now, setup.breakeven_r,
                    meta={
                        "poi_tf": setup.poi.timeframe.label, "poi": (setup.poi.low, setup.poi.high),
                        "confirmation": setup.confirmation.type.value, "confirmation_tf": setup.confirmation.timeframe.label,
                        "confirmed_at": setup.confirmation.timestamp, "touched_at": setup.touched_at, "entry_planned": setup.entry,
                        "planned_rr": round(setup.rr, 2), "rr_at_fill": round(rr_now, 2), "lots_planned": setup.lots,
                        "tp_source": setup.tp_source,
                        "kronos": None if fc is None else f"{fc.direction} {fc.confidence:.0%}",
                    },
                    price=price_now, ts=now,
                )
                guard.record_trade(now)
            if self.progress and i % report_every == 0:
                print(f"  {i}/{n} {ts} equity={broker.equity():,.0f} trades={len(broker.closed)}", flush=True)

        # flatten at the end so every trade has an outcome (at the last candle this run processed)
        if broker.open_positions() and last_candle is not None:
            for pos in list(broker.open_positions()):
                broker.close_position(pos.id, "end_of_data", float(last_candle.close), self.step_tf.close_time(last_candle.timestamp), market=True)

        return BacktestResult(
            symbol=self.symbol, step_tf=self.step_tf, start=first_ts, end=last_ts,
            initial_equity=broker.initial_balance, final_equity=broker.balance(), trades=list(broker.closed),
            equity_curve=list(broker.equity_curve), steps=steps, signals=signals, rejected_by_guard=rejected,
            guard_reasons=guard_reasons, rejection_reasons=rejection_reasons, runtime_seconds=time.time() - t0,
        )
