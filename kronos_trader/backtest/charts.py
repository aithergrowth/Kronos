"""Chart images for backtest trades.

Re-runs the engine at each trade's open time (the same closed candles the
backtester saw) and draws the confirmation timeframe with the zone, the
X/B/P marks and the entry, stop and target, so a trade list can be checked
by eye without replaying every setup.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd

from ..config import Settings
from ..core.timeframe import Timeframe
from ..data.resample import MultiTimeframeData
from ..notify.chart import chart_label
from ..strategy.engine import StrategyEngine


def pick_rows(trades: pd.DataFrame, max_charts: int) -> pd.DataFrame:
    """At most ``max_charts`` trades, spread evenly over the list (all of them when it is short)."""
    if max_charts <= 0 or len(trades) <= max_charts:
        return trades
    step = len(trades) / max_charts
    idx = sorted({int(i * step) for i in range(max_charts)})
    return trades.iloc[idx]


def render_trade_charts(
    settings: Settings,
    data: MultiTimeframeData,
    symbol: str,
    trades: pd.DataFrame,
    out_dir,
    engine: Optional[StrategyEngine] = None,
    max_charts: int = 20,
    lookback: int = 120,
    max_zones: int = 3,
    blind: bool = False,
) -> List[Path]:
    from ..notify.chart import render_chart

    engine = engine or StrategyEngine(settings)
    symbol = symbol.upper()
    spec = settings.symbols.get(symbol)
    decimals = spec.price_decimals if spec else 5
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: List[Path] = []
    for seq, (_, row) in enumerate(pick_rows(trades.reset_index(drop=True), max_charts).iterrows(), start=1):
        now = pd.Timestamp(row["opened_at"])
        views = data.as_of(now, lookback=settings.structure.lookback)
        analysis = engine.analyze(symbol, views, equity=settings.account_size, now=now)
        regenerated = analysis.signal.setup if analysis.has_valid_signal else None
        drawn, flags = ledger_setup(row, regenerated, symbol)
        tf = drawn.confirmation.timeframe if drawn.confirmation is not None else Timeframe.parse(str(row.get("confirmation_tf") or "15m"))
        if tf not in views:
            tf = min(views)
        zones = [p for p in analysis.pois if p.direction is analysis.decision.direction] or list(analysis.pois)
        bias = "  ".join(f"{t.label} {b.bias.name.lower()}" for t, b in sorted(analysis.biases.items())) if analysis.biases else ""
        result = f"{float(row['r']):+.2f}R ({row['reason']})" if pd.notna(row.get("r")) else "open"
        title = f"{symbol} {tf.label}  trade {row.get('id', '')} {row['direction']}  R:R 1:{drawn.rr:.1f}"
        title += "  outcome hidden" if blind else f"  result {result}"
        if flags:
            title += "  [" + "; ".join(flags) + "]"
        boxes = []
        if "ledger zone drawn dashed" in " ".join(flags) and pd.notna(row.get("poi_low")):
            boxes.append((float(row["poi_low"]), float(row["poi_high"]), f"{row.get('poi_tf', '')} zone of the trade"))
        lines = stop_p_lines(row)
        name = f"{symbol}_{seq:03d}_{now:%Y%m%d_%H%M}_{chart_label(tf)}.png"
        paths.append(render_chart(views[tf], out / name, pois=zones, setup=drawn, title=title,
                                  subtitle=f"{bias}  |  {analysis.decision.reason}", lookback=lookback, price_decimals=decimals,
                                  max_zones=max_zones, extra_boxes=boxes, extra_lines=lines))
    return paths


def stop_p_lines(row) -> List[tuple]:
    """The P the stop sits behind, as a separate line when the ledger says it is not the zone's own P."""
    if not ("stop_p" in row and pd.notna(row.get("stop_p")) and pd.notna(row.get("stop_tf"))):
        return []
    stop_p = float(row["stop_p"])
    zone_p = float(row["poi_p"]) if "poi_p" in row and pd.notna(row.get("poi_p")) else None
    if zone_p is not None and abs(stop_p - zone_p) <= 1e-9:
        return []
    opened = pd.Timestamp(row["stop_p_open"]) if "stop_p_open" in row and pd.notna(row.get("stop_p_open")) else None
    label = f"stop P on {row['stop_tf']}" + (f", candle {opened:%d %b %H:%M}" if opened is not None else "")
    return [(stop_p, label, opened)]


def ledger_setup(row, regenerated, symbol: str):
    """The setup to draw: entry, stop, target, side and confirmation time/type/timeframe always from the
    trade record.  The replayed zone is drawn with its X/B/P marks only when its identity matches the
    record (timeframe, formation time, bounds, X, gap and P within 5 % of the zone height); otherwise the
    record's own zone is drawn dashed and the title carries the differences.  Returns ``(setup_like, flags)``."""
    from dataclasses import replace
    from types import SimpleNamespace
    from ..core.types import Bias, Direction, POI
    direction = Direction.LONG if str(row["direction"]).upper().startswith("L") else Direction.SHORT
    entry, stop, tp = float(row["entry"]), float(row["stop"]), float(row["take_profit"])
    rr = abs(tp - entry) / abs(entry - stop) if entry != stop else 0.0
    flags: List[str] = []

    def has(key):
        return key in row and pd.notna(row.get(key))

    # the confirmation as recorded (the replay's is used only to fill in fields the record lacks)
    conf_tf = Timeframe.parse(str(row["confirmation_tf"])) if has("confirmation_tf") else (
        regenerated.confirmation.timeframe if regenerated is not None else Timeframe.MIN_15)
    conf_ts = pd.Timestamp(row["confirmed_at"]) if has("confirmed_at") else (
        regenerated.confirmation.timestamp if regenerated is not None else pd.Timestamp(row["opened_at"]))
    conf_type = str(row["confirmation"]) if has("confirmation") else (
        regenerated.confirmation.type.value if regenerated is not None else "entry")
    confirmation = SimpleNamespace(timestamp=conf_ts, timeframe=conf_tf, type=SimpleNamespace(value=conf_type))

    has_zone = has("poi_low") and has("poi_high")
    zone_matches = False
    if regenerated is not None:
        differences: List[str] = []
        if regenerated.direction is not direction:
            differences.append("side")
        if has("poi_tf") and regenerated.poi.timeframe.label != str(row["poi_tf"]):
            differences.append("zone timeframe")
        if has("poi_formed") and pd.Timestamp(row["poi_formed"]) != pd.Timestamp(regenerated.poi.created_at):
            differences.append("zone formation time")
        if has_zone:
            height = max(float(row["poi_high"]) - float(row["poi_low"]), 1e-9)
            tol = 0.05 * height
            if abs(regenerated.poi.low - float(row["poi_low"])) > tol or abs(regenerated.poi.high - float(row["poi_high"])) > tol:
                differences.append("zone bounds")
            for key, value in (("poi_x", regenerated.poi.liquidity_level), ("poi_p", regenerated.poi.protector_extreme)):
                if has(key) and value is not None and abs(float(row[key]) - float(value)) > tol:
                    differences.append({"poi_x": "X", "poi_p": "P"}[key])
            gap = regenerated.poi.gap if regenerated.poi.gap is not None else regenerated.poi.balance
            if has("poi_b_low") and has("poi_b_high") and gap is not None:
                if abs(gap.low - float(row["poi_b_low"])) > tol or abs(gap.high - float(row["poi_b_high"])) > tol:
                    differences.append("balance level")
        if has("confirmed_at") and pd.Timestamp(row["confirmed_at"]) != pd.Timestamp(regenerated.confirmation.timestamp):
            differences.append("confirmation time")
        if has("confirmation") and str(row["confirmation"]) != regenerated.confirmation.type.value:
            differences.append("confirmation type")
        if has("confirmation_tf") and str(row["confirmation_tf"]) != regenerated.confirmation.timeframe.label:
            differences.append("confirmation timeframe")
        if has("entry_planned") and abs(float(row["entry_planned"]) - regenerated.entry) > 0.001 * abs(regenerated.entry):
            differences.append("planned entry")
        zone_matches = not differences
        if differences:
            flags.append("REPLAY MISMATCH (" + ", ".join(differences) + ")" + ("; ledger zone drawn dashed" if has_zone else "; record context used"))
    else:
        flags.append("setup not reproduced by the replay" + ("; ledger zone drawn dashed" if has_zone else ""))
    if zone_matches:
        return replace(regenerated, entry=entry, stop=stop, take_profit=tp, rr=rr, direction=direction, confirmation=confirmation), flags
    poi = None
    if has_zone:
        when = row["poi_formed"] if has("poi_formed") else (row["touched_at"] if has("touched_at") else row["opened_at"])
        poi = POI(Timeframe.parse(str(row["poi_tf"])) if has("poi_tf") else Timeframe.H_1,
                  Bias.BULLISH if direction is Direction.LONG else Bias.BEARISH,
                  float(row["poi_low"]), float(row["poi_high"]), None, None, 0, pd.Timestamp(when))
    setup = SimpleNamespace(symbol=symbol, direction=direction, entry=entry, stop=stop, take_profit=tp, rr=rr,
                            poi=poi, confirmation=confirmation, lots=float(row.get("lots", 0) or 0), risk_amount=0.0)
    return setup, flags
