"""Decision-moment dossier: everything the engine saw at one instant, per timeframe.

For one symbol and one timestamp it writes a folder with a chart per timeframe (all zones of that
timeframe, X/B/P on the zones the engine would trade from), the bias per timeframe with its notes,
every geometric 3-candle gap with the reason it was or was not kept as a balance level, the swings,
sweeps and breaks, the mapped zones with status and visit number, the confirmation search result,
every rejection, and the setup if there was one.  Judge the reading first, look at the outcome later.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import Settings
from ..core.candles import CandleSeries
from ..core.timeframe import BIAS_TIMEFRAMES, POI_TIMEFRAMES, Timeframe
from ..core.types import Bias, POIStatus
from ..data.resample import MultiTimeframeData
from ..strategy.engine import StrategyEngine


def geometric_gaps(series: CandleSeries, params) -> List[dict]:
    """Every three-candle gap in the view with the threshold that applied when it formed and whether it passed."""
    highs, lows = series.high, series.low
    n = len(series)
    if n < 3:
        return []
    ranges = pd.Series(highs - lows, dtype=float)
    rolling = ranges.rolling(max(1, params.gap_median_window), min_periods=1).median().shift(1).bfill()
    min_gap_at = (params.min_gap_fraction * rolling).to_numpy(dtype=float)
    out = []
    ts = series.ts_list
    for j in range(2, n):
        if lows[j] > highs[j - 2]:
            width, direction, low, high = float(lows[j] - highs[j - 2]), "bullish", float(highs[j - 2]), float(lows[j])
        elif highs[j] < lows[j - 2]:
            width, direction, low, high = float(lows[j - 2] - highs[j]), "bearish", float(highs[j]), float(lows[j - 2])
        else:
            continue
        need = float(min_gap_at[j])
        out.append({"candle3": str(ts[j]), "direction": direction, "low": low, "high": high, "width": width,
                    "required": need, "kept": width >= need,
                    "reason": "" if width >= need else f"width {width:.5g} below {params.min_gap_fraction:.0%} of the median range before it ({need:.5g})"})
    return out


def warm_up(engine: StrategyEngine, data: MultiTimeframeData, symbol: str, at, days: float, step_tf: Optional[Timeframe] = None) -> int:
    """Replay the lowest timeframe from ``days`` before ``at`` so the engine's visit memory is not cold-started.
    Returns the number of steps replayed."""
    at = pd.Timestamp(at)
    step = data[step_tf] if step_tf is not None else data.lowest
    start = at - pd.Timedelta(days=float(days))
    i0 = int(step.timestamps.searchsorted(start))
    n = 0
    for i in range(i0, len(step)):
        ts = step.timestamps.iloc[i]
        now = step.timeframe.close_time(ts)
        if now >= at:
            break
        views = data.as_of(now, lookback=engine.settings.structure.lookback)
        if views:
            engine.analyze(symbol, views, now=now)
            n += 1
    return n


def write_decision_dossier(settings: Settings, data: MultiTimeframeData, symbol: str, at, out_dir,
                           engine: Optional[StrategyEngine] = None, lookback: int = 120, warmup_days: float = 0.0,
                           memory_label: Optional[str] = None) -> Path:
    from ..notify.chart import render_chart
    engine = engine or StrategyEngine(settings)
    symbol = symbol.upper()
    at = pd.Timestamp(at)
    warmed = warm_up(engine, data, symbol, at, warmup_days) if warmup_days else 0
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec = settings.symbols.get(symbol)
    decimals = spec.price_decimals if spec else 5
    views = data.as_of(at, lookback=settings.structure.lookback)
    analysis = engine.analyze(symbol, views, equity=settings.account_size, now=at)
    tracker = getattr(engine, "visits", {}).get(symbol)
    structure_for = getattr(engine, "structure_for", None)
    if structure_for is None:                       # a stub engine in tests: analyse the structure here
        from ..strategy.structure import analyze_structure
        structure_for = lambda sym, view: analyze_structure(view, settings.structure)
    doc: Dict[str, object] = {"symbol": symbol, "at": str(at), "price": analysis.price, "warmup_steps": warmed,
                              "visit_memory": memory_label or (f"warm-up replay of {warmed} steps before this moment" if warmed
                                                               else "cold start: visits counted from the analysis window only"),
                              "decision": {"direction": analysis.decision.direction.name, "mode": analysis.decision.mode.value,
                                           "reason": analysis.decision.reason},
                              "rejections": list(analysis.rejections), "timeframes": {}}
    lines = [f"# {symbol} at {at:%Y-%m-%d %H:%M} UTC", "",
             f"Price {analysis.price:.{decimals}f}. Decision: **{analysis.decision.direction.name.lower()}**, {analysis.decision.mode.value}: {analysis.decision.reason}", "",
             f"Visit memory: {doc['visit_memory']}.", ""]
    for tf in sorted(views):
        view = views[tf].tail(settings.structure.lookback_by_timeframe.get(tf, settings.structure.lookback))
        st = structure_for(symbol, view)
        tb = analysis.biases.get(tf)
        gaps = geometric_gaps(view, settings.structure)
        zones = [p for p in analysis.pois if p.timeframe is tf]
        zone_rows = []
        for p in zones:
            visit = None
            if tracker is not None and p.key in tracker.states:
                s = tracker.states[p.key]
                visit = {"visits": s.visits, "inside": s.inside, "touch": str(s.visit_start_ts) if s.visit_start_ts is not None else None}
            gap = p.gap if p.gap is not None else p.balance
            zone_rows.append({"direction": p.direction.name, "low": p.low, "high": p.high, "x": p.liquidity_level,
                              "b": (gap.low, gap.high) if gap is not None else None, "p": p.protector_extreme,
                              "formed": str(p.created_at), "status": p.status.value, "visit": visit})
        recent_swings = [{"time": str(s.timestamp), "price": float(s.price), "kind": s.kind.value} for s in st.swings[-12:]]
        sweeps = [{"time": str(s.timestamp), "level": float(s.level.price), "extreme": s.extreme, "implied": s.implied_bias.name} for s in st.sweeps[-6:]]
        breaks = [{"time": str(b.timestamp), "level": float(b.broken_level), "direction": b.direction.name, "kind": b.kind.value} for b in st.breaks[-6:]]
        doc["timeframes"][tf.label] = {
            "candles": len(view), "last": str(view.last_timestamp),
            "bias": None if tb is None else {"bias": tb.bias.name, "liquidity": tb.liquidity_view.name, "balance": tb.balance_view.name, "notes": tb.notes},
            "gaps_geometric": gaps, "gaps_kept": sum(1 for g in gaps if g["kept"]),
            "swings": recent_swings, "sweeps": sweeps, "breaks": breaks, "zones": zone_rows}
        live = [p for p in zones if p.status is not POIStatus.INVALIDATED]
        chart_zones = sorted(live, key=lambda p: abs((p.low + p.high) / 2 - analysis.price))[:4]
        title = f"{symbol} {tf.label}  {at:%Y-%m-%d %H:%M}"
        if tb is not None:
            title += f"  bias {tb.bias.name.lower()} (liquidity {tb.liquidity_view.name.lower()}, balance {tb.balance_view.name.lower()})"
        setup = analysis.signal.setup if analysis.has_valid_signal and analysis.signal.setup.confirmation.timeframe is tf else None
        png = render_chart(view, out / f"{tf.label}.png", pois=chart_zones, setup=setup, title=title,
                           subtitle="; ".join(tb.notes[:2]) if tb is not None else "", lookback=lookback, price_decimals=decimals, max_zones=4)
        lines += [f"## {tf.label}", "", f"![{tf.label}]({png.name})", ""]
        if tb is not None:
            lines += [f"Bias **{tb.bias.name.lower()}**: liquidity view {tb.liquidity_view.name.lower()}, balance view {tb.balance_view.name.lower()}.", ""]
            lines += [f"- {n}" for n in tb.notes] + [""]
        if zone_rows:
            lines += ["| Zone | Low | High | X | B | P | Formed | Status | Visits (a visit stays open until a close 1.5 zone heights beyond the zone) |", "|---|---|---|---|---|---|---|---|---|"]
            for z in zone_rows:
                b = "" if z["b"] is None else f"{z['b'][0]:.{decimals}f}-{z['b'][1]:.{decimals}f}"
                v = "" if z["visit"] is None else f"{z['visit']['visits']} ({'visit open' if z['visit']['inside'] else 'no visit'})"
                lines.append(f"| {z['direction'].lower()} | {z['low']:.{decimals}f} | {z['high']:.{decimals}f} | {'' if z['x'] is None else f'{z[chr(120)]:.{decimals}f}'} | {b} | {z['p']:.{decimals}f} | {z['formed'][:16]} | {z['status']} | {v} |")
            lines.append("")
        dropped = [g for g in gaps if not g["kept"]]
        lines += [f"Balance levels: {sum(1 for g in gaps if g['kept'])} kept of {len(gaps)} three-candle gaps in the window; "
                  f"{len(dropped)} dropped by the size threshold ({settings.structure.min_gap_fraction:.0%} of the median range before them)."]
        if dropped:
            lines += ["", "| Dropped gap (candle 3) | Side | Width | Required |", "|---|---|---|---|"]
            lines += [f"| {g['candle3'][:16]} | {g['direction']} | {g['width']:.{decimals}f} | {g['required']:.{decimals}f} |" for g in dropped[-8:]]
        lines.append("")
    lines += ["## Rejections at this moment", ""] + ([f"- {r}" for r in analysis.rejections] or ["- none"]) + [""]
    if analysis.has_valid_signal:
        s = analysis.signal.setup
        doc["setup"] = {"direction": s.direction.name, "poi_tf": s.poi.timeframe.label, "poi": (s.poi.low, s.poi.high),
                        "confirmation": s.confirmation.type.value, "confirmation_tf": s.confirmation.timeframe.label,
                        "confirmed_at": str(s.confirmation.timestamp), "entry": s.entry, "stop": s.stop, "take_profit": s.take_profit,
                        "rr": s.rr, "tp_source": s.tp_source, "touched_at": str(s.touched_at), "visit": s.visit_number}
        lines += ["## Setup", "", f"{s.direction.name} from the {s.poi.timeframe.label} zone {s.poi.low:.{decimals}f}-{s.poi.high:.{decimals}f}, "
                  f"{s.confirmation.type.value} on {s.confirmation.timeframe.label} at {s.confirmation.timestamp}, entry {s.entry:.{decimals}f}, "
                  f"stop {s.stop:.{decimals}f}, target {s.take_profit:.{decimals}f} ({s.tp_source}), R:R 1:{s.rr:.2f}, visit {s.visit_number}.", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "dossier.json").write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    return out
