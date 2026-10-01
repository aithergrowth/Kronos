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
        setup = analysis.signal.setup if analysis.has_valid_signal else None
        tf = setup.confirmation.timeframe if setup is not None else Timeframe.parse(str(row.get("confirmation_tf") or "15m"))
        if tf not in views:
            tf = min(views)
        zones = [p for p in analysis.pois if p.direction is analysis.decision.direction] or list(analysis.pois)
        bias = "  ".join(f"{t.label} {b.bias.name.lower()}" for t, b in sorted(analysis.biases.items())) if analysis.biases else ""
        result = f"{float(row['r']):+.2f}R ({row['reason']})" if pd.notna(row.get("r")) else "open"
        rr = float(row["planned_rr"]) if pd.notna(row.get("planned_rr")) else (setup.rr if setup is not None else 0.0)
        title = f"{symbol} {tf.label}  trade {row.get('id', '')} {row['direction']}  R:R 1:{rr:.1f}  result {result}"
        if setup is None:
            title += "  (setup not reproduced: zones only)"
        name = f"{symbol}_{seq:03d}_{now:%Y%m%d_%H%M}_{tf.label}.png"
        paths.append(render_chart(views[tf], out / name, pois=zones, setup=setup, title=title,
                                  subtitle=f"{bias}  |  {analysis.decision.reason}", lookback=lookback, price_decimals=decimals,
                                  max_zones=max_zones))
    return paths
