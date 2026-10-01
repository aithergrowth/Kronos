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
        title = f"{symbol} {tf.label}  trade {row.get('id', '')} {row['direction']}  R:R 1:{drawn.rr:.1f}  result {result}"
        if flags:
            title += "  [" + "; ".join(flags) + "]"
        boxes = []
        if "ledger zone drawn dashed" in " ".join(flags):
            boxes.append((float(row["poi_low"]), float(row["poi_high"]), f"{row.get('poi_tf', '')} zone of the trade"))
        name = f"{symbol}_{seq:03d}_{now:%Y%m%d_%H%M}_{tf.label}.png"
        paths.append(render_chart(views[tf], out / name, pois=zones, setup=drawn, title=title,
                                  subtitle=f"{bias}  |  {analysis.decision.reason}", lookback=lookback, price_decimals=decimals,
                                  max_zones=max_zones, extra_boxes=boxes))
    return paths


def ledger_setup(row, regenerated, symbol: str):
    """The setup to draw: entry, stop, target and side always from the trade record; the zone and the
    confirmation from the replayed analysis when they match the record, else flagged and the record's
    own zone drawn dashed.  Returns ``(setup_like, flags)``."""
    from dataclasses import replace
    from types import SimpleNamespace
    from ..core.types import Bias, Direction, POI
    direction = Direction.LONG if str(row["direction"]).upper().startswith("L") else Direction.SHORT
    entry, stop, tp = float(row["entry"]), float(row["stop"]), float(row["take_profit"])
    rr = abs(tp - entry) / abs(entry - stop) if entry != stop else 0.0
    flags: List[str] = []
    has_zone = pd.notna(row.get("poi_low")) and pd.notna(row.get("poi_high"))
    if regenerated is not None:
        zone_ok = True
        if has_zone:
            height = max(float(row["poi_high"]) - float(row["poi_low"]), 1e-9)
            zone_ok = (abs(regenerated.poi.low - float(row["poi_low"])) <= 0.05 * height
                       and abs(regenerated.poi.high - float(row["poi_high"])) <= 0.05 * height)
        side_ok = regenerated.direction is direction
        planned = row.get("entry_planned")
        conf_ok = pd.isna(planned) if planned is not None else True
        if planned is not None and pd.notna(planned):
            conf_ok = abs(float(planned) - regenerated.entry) <= 1e-9 or abs(float(planned) - regenerated.entry) <= 0.001 * abs(regenerated.entry)
        if zone_ok and side_ok:
            if not conf_ok:
                flags.append("replayed confirmation differs from the record")
            return replace(regenerated, entry=entry, stop=stop, take_profit=tp, rr=rr, direction=direction), flags
        flags.append("REPLAY MISMATCH: replayed zone differs, ledger zone drawn dashed" if has_zone else "REPLAY MISMATCH: replayed zone differs")
    else:
        flags.append("setup not reproduced by the replay" + ("; ledger zone drawn dashed" if has_zone else ""))
    poi = None
    if has_zone:
        when = row.get("poi_formed") if pd.notna(row.get("poi_formed", None)) else row.get("touched_at", row["opened_at"])
        poi = POI(Timeframe.parse(str(row.get("poi_tf") or "1H")), Bias.BULLISH if direction is Direction.LONG else Bias.BEARISH,
                  float(row["poi_low"]), float(row["poi_high"]), None, None, 0, pd.Timestamp(when))
    conf_tf = Timeframe.parse(str(row.get("confirmation_tf") or "15m"))
    conf_ts = row.get("confirmed_at") if pd.notna(row.get("confirmed_at", None)) else row["opened_at"]
    confirmation = SimpleNamespace(timestamp=pd.Timestamp(conf_ts), timeframe=conf_tf,
                                   type=SimpleNamespace(value=str(row.get("confirmation") or "entry")))
    setup = SimpleNamespace(symbol=symbol, direction=direction, entry=entry, stop=stop, take_profit=tp, rr=rr,
                            poi=poi, confirmation=confirmation, lots=float(row.get("lots", 0) or 0), risk_amount=0.0)
    return setup, flags
