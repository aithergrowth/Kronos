"""Event-driven backtester.

Walks the ``step_tf`` candles one closed candle at a time.  At every step the
paper broker first processes the candle (stops, targets, break-even), then the
engine sees exactly the candles that were closed at that moment on every
timeframe, so nothing in the analysis can peek into the future.
"""
from __future__ import annotations

import re
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
from ..strategy.risk import reconcile_risk, resize_at, stepped_risk


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
    zones_by_reason: Dict[str, int] = field(default_factory=dict)      # distinct zones (not bars) behind each rejection bucket
    first_breach: Optional[Tuple[pd.Timestamp, str]] = None             # first published prop-firm rule hit on bar-close equity
    guard_rules: Dict[str, object] = field(default_factory=dict)
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
                "confirmed_close_at": t.meta.get("confirmed_close_at"),
                "bias_mode": t.meta.get("bias_mode"), "bias_combo": t.meta.get("bias_combo"), "bias_aligned": t.meta.get("bias_aligned"),
                "bias_by_tf": t.meta.get("bias_by_tf"),
                "entry_planned": t.meta.get("entry_planned"), "rr_at_fill": t.meta.get("rr_at_fill"), "lots_planned": t.meta.get("lots_planned"),
                "poi_x": t.meta.get("poi_x"), "poi_b_low": (t.meta.get("poi_b") or (None, None))[0],
                "poi_b_high": (t.meta.get("poi_b") or (None, None))[1], "poi_p": t.meta.get("poi_p"),
                "stop_p": t.meta.get("stop_p"), "stop_tf": t.meta.get("stop_tf"), "stop_p_open": t.meta.get("stop_p_open"),
                "stop_p_close": t.meta.get("stop_p_close"), "stop_basis": t.meta.get("stop_basis"),
                "poi_formed": t.meta.get("poi_formed"), "visit": t.meta.get("visit"),
                "risk_amount": t.risk_amount, "risk_budget": t.meta.get("risk_budget"),
                "poi_low": (t.meta.get("poi") or (None, None))[0],
                "poi_high": (t.meta.get("poi") or (None, None))[1], "kronos": t.meta.get("kronos"),
            })
        return pd.DataFrame(rows)


def visits_of(setup) -> Optional[int]:
    return getattr(setup, "visit_number", None)


def _close_of(confirmation) -> Optional[pd.Timestamp]:
    try:
        return confirmation.timeframe.close_time(pd.Timestamp(confirmation.timestamp))
    except Exception:
        return None


ZONE_RE = re.compile(r"^(\S+ \S+ POI [\d.]+-[\d.]+) \(\w+, formed ([^)]+)\)")


def zone_identity(reason: str) -> Optional[str]:
    """The zone a rejection text is about (timeframe, side, bounds, formation time), status stripped."""
    m = ZONE_RE.match(reason)
    return f"{m.group(1)} formed {m.group(2)}" if m else None


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
        dossier_dir=None,
        dossier_limit: int = 200,
    ):
        self.settings = settings
        self.data = data
        self.symbol = symbol.upper()
        self.step_tf = Timeframe.parse(step_tf) if step_tf else min(data.series)
        # a finer timeframe than the step (1m candles under a 5m walk) may confirm inside the step: tell the engine the step
        self._engine_kwargs = {"step_minutes": self.step_tf.minutes} if any(tf < self.step_tf for tf in data.series) else {}
        self.engine = engine or StrategyEngine(settings, forecaster)
        self.start = pd.Timestamp(start) if start is not None else None
        self.end = pd.Timestamp(end) if end is not None else None
        self.use_spread = use_spread
        self.progress = progress
        self.quote_basis = quote_basis
        self.dossier_dir = dossier_dir            # write a decision dossier at every signal, with this run's own engine state
        self.dossier_limit = dossier_limit
        self._dossiers_written = 0

    def _write_dossier(self, now) -> None:
        """A decision dossier for this moment from the running engine (its visit memory included), never fatal."""
        if self.dossier_dir is None or self._dossiers_written >= self.dossier_limit:
            return
        try:
            from pathlib import Path
            from .dossier import write_decision_dossier
            out = Path(self.dossier_dir) / f"{pd.Timestamp(now):%Y-%m-%d_%H%M}"
            write_decision_dossier(self.settings, self.data, self.symbol, now, out, engine=self.engine,
                                   memory_label="the run's own engine (visits counted from each zone's formation)")
            self._dossiers_written += 1
        except Exception as exc:   # pragma: no cover - diagnostics must not stop a run
            print(f"  dossier at {now} failed: {exc}", flush=True)

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
        zones_by_reason: Dict[str, Set[str]] = {}
        first_ts = last_ts = None
        last_candle = None

        n = len(step)
        report_every = max(1, n // 20)
        first = step.index_at_or_after(self.start) if self.start is not None else 0     # the candles before the start are skipped
        for i in range(first, n):
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
            guard.update(now, broker.equity(), broker.balance())
            views = self.data.as_of(now, lookback=s.structure.lookback)
            analysis = self.engine.analyze(self.symbol, views, equity=broker.equity(), now=now, **self._engine_kwargs)
            for r in analysis.rejections:
                key = _bucket(r)
                rejection_reasons[key] = rejection_reasons.get(key, 0) + 1
                zone = zone_identity(r)
                if zone is not None:
                    zones_by_reason.setdefault(key, set()).add(zone)
            if analysis.has_valid_signal:
                setup = analysis.signal.setup
                key = (setup.poi.key, str(setup.confirmation.timestamp))
                if key in seen:
                    continue
                seen.add(key)
                signals += 1
                self._write_dossier(now)
                ok, reason = guard.can_open(broker, now, self.symbol)
                if not ok:
                    rejected += 1
                    guard_reasons[reason] = guard_reasons.get(reason, 0) + 1
                    continue
                # market order at the price of this moment (the close of the candle that just closed), with the
                # same re-check the live runner makes: the confirmation close may be older than ``now`` when a
                # session or news gate held the signal back
                price_now = broker.fill_price(self.symbol, setup.direction, float(candle.close))   # the ask / the bid
                wrong_side = (setup.direction.sign > 0 and price_now <= setup.stop) or (setup.direction.sign < 0 and price_now >= setup.stop)
                lots_now, risk_amount_now, risk_distance_now, rr_now, _ = resize_at(
                    price_now, setup.stop, setup.take_profit, broker.equity(), spec,
                    stepped_risk(s.risk, broker.balance(), s.account_size))
                if wrong_side or rr_now < s.risk.min_rr or lots_now <= 0:
                    rejected += 1
                    reason = ("price moved: wrong side of the stop" if wrong_side else
                              "price moved: R:R below minimum" if rr_now < s.risk.min_rr else
                              "price moved: stop too wide for the minimum lot")
                    guard_reasons[reason] = guard_reasons.get(reason, 0) + 1
                    continue
                fc = analysis.signal.forecast
                pos = broker.place_market_order(
                    self.symbol, setup.direction, lots_now, setup.stop, setup.take_profit, risk_amount_now,
                    risk_distance_now, setup.breakeven_r,
                    meta={
                        "poi_tf": setup.poi.timeframe.label, "poi": (setup.poi.low, setup.poi.high),
                        "poi_x": setup.poi.liquidity_level, "poi_p": setup.poi.protector_extreme,
                        "poi_b": ((setup.poi.gap.low, setup.poi.gap.high) if setup.poi.gap is not None else
                                  (setup.poi.balance.low, setup.poi.balance.high) if setup.poi.balance is not None else (None, None)),
                        "poi_formed": setup.poi.created_at, "visit": visits_of(setup),
                        "confirmation": setup.confirmation.type.value, "confirmation_tf": setup.confirmation.timeframe.label,
                        "confirmed_at": setup.confirmation.timestamp,           # the confirmation candle's open label
                        "confirmed_close_at": _close_of(setup.confirmation),    # when that candle closed = when it could be acted on
                        "touched_at": setup.touched_at, "entry_planned": setup.entry,
                        **(getattr(setup, "stop_detail", None) or {}),          # stop_p, stop_tf, stop_p_open, stop_p_close, stop_basis
                        "planned_rr": round(setup.rr, 2), "rr_at_fill": round(rr_now, 2), "lots_planned": setup.lots,
                        "tp_source": setup.tp_source,
                        "kronos": None if fc is None else f"{fc.direction} {fc.confidence:.0%}",
                        # the bias the trade was taken under: mode (full / scalp), the combo that matched, the reading per timeframe
                        "bias_mode": getattr(analysis.decision.mode, "value", str(analysis.decision.mode)),
                        "bias_combo": "+".join(tf.label for tf in (analysis.decision.matched_combo or ())),
                        "bias_aligned": "+".join(tf.label for tf in analysis.decision.aligned),
                        "bias_by_tf": " ".join(f"{tf.label}={b.bias}" for tf, b in analysis.biases.items()),
                    },
                    price=price_now, ts=now, price_is_fill=True,
                )
                reconcile_risk(pos, broker, risk_amount_now)
                guard.record_trade(now)
                mark_traded = getattr(self.engine, "mark_traded", None)   # test doubles may lack it
                if mark_traded is not None:
                    mark_traded(self.symbol, setup.poi.key, visits_of(setup))
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
            guard_reasons=guard_reasons, rejection_reasons=rejection_reasons,
            zones_by_reason={k: len(v) for k, v in zones_by_reason.items()}, first_breach=guard.first_breach,
            guard_rules=guard.rules(), runtime_seconds=time.time() - t0,
        )
