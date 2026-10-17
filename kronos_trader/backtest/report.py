"""Backtest statistics and a plain-text report."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

from .runner import BacktestResult


def max_drawdown(equity: List[float]) -> float:
    if not equity:
        return 0.0
    arr = np.asarray(equity, dtype=float)
    peaks = np.maximum.accumulate(arr)
    dd = (peaks - arr) / peaks
    return float(dd.max())


def summarize(result: BacktestResult) -> Dict[str, Any]:
    trades = result.trades
    rs = np.array([t.r for t in trades], dtype=float)
    pnls = np.array([t.pnl for t in trades], dtype=float)
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    summary: Dict[str, Any] = {
        "symbol": result.symbol,
        "period": f"{result.start} -> {result.end}",
        "steps": result.steps,
        "signals": result.signals,
        "rejected_by_guard": result.rejected_by_guard,
        "trades": len(trades),
        "wins": int((pnls > 0).sum()),
        "losses": int((pnls < 0).sum()),
        "breakeven": int((pnls == 0).sum()),
        "win_rate": float((pnls > 0).mean()) if len(pnls) else 0.0,
        "avg_r": float(rs.mean()) if len(rs) else 0.0,
        "total_r": float(rs.sum()) if len(rs) else 0.0,
        "best_r": float(rs.max()) if len(rs) else 0.0,
        "worst_r": float(rs.min()) if len(rs) else 0.0,
        "profit_factor": float(wins.sum() / -losses.sum()) if len(losses) and losses.sum() != 0 else (float("inf") if len(wins) else 0.0),
        "net_pnl": float(pnls.sum()),
        "return_pct": (result.final_equity / result.initial_equity - 1.0) * 100.0 if result.initial_equity else 0.0,
        "max_drawdown_pct": max_drawdown([e for _, e in result.equity_curve]) * 100.0,
        "runtime_seconds": result.runtime_seconds,
    }
    if trades:
        df = result.trades_frame()
        summary["by_poi_tf"] = df.groupby("poi_tf")["r"].agg(["count", "mean", "sum"]).round(2).to_dict("index")
        summary["by_confirmation"] = df.groupby("confirmation")["r"].agg(["count", "mean", "sum"]).round(2).to_dict("index")
        summary["by_exit"] = df.groupby("reason")["r"].agg(["count", "mean", "sum"]).round(2).to_dict("index")
    return summary


def format_report(result: BacktestResult) -> str:
    s = summarize(result)
    lines = [
        f"Backtest {s['symbol']}  {s['period']}  (step {result.step_tf.label}, {s['steps']} steps, {s['runtime_seconds']:.1f}s)",
        f"  signals {s['signals']}  guard-rejected {s['rejected_by_guard']}  trades {s['trades']}",
        f"  wins {s['wins']}  losses {s['losses']}  break-even {s['breakeven']}  win rate {s['win_rate']:.1%}",
        f"  avg R {s['avg_r']:+.2f}  total R {s['total_r']:+.1f}  best {s['best_r']:+.1f}  worst {s['worst_r']:+.1f}",
        f"  profit factor {s['profit_factor']:.2f}  net P&L {s['net_pnl']:+,.0f}  return {s['return_pct']:+.2f}%  max DD {s['max_drawdown_pct']:.2f}%",
    ]
    for key in ("by_poi_tf", "by_confirmation", "by_exit"):
        if key in s:
            lines.append(f"  {key}:")
            for k, v in s[key].items():
                lines.append(f"    {k}: n={int(v['count'])} avgR={v['mean']:+.2f} sumR={v['sum']:+.1f}")
    if result.first_breach:
        lines.append(f"  first guard breach: {result.first_breach[0]}  {result.first_breach[1]}")
    else:
        lines.append("  first guard breach: never (bar-close equity, published limits)")
    if result.guard_reasons:
        lines.append("  guard rejections:")
        for k, v in sorted(result.guard_reasons.items(), key=lambda kv: -kv[1]):
            lines.append(f"    {v:5d}  {k}")
    if result.rejection_reasons:
        lines.append("  engine rejections (top):")
        for k, v in sorted(result.rejection_reasons.items(), key=lambda kv: -kv[1])[:8]:
            lines.append(f"    {v:6d}  {k}")
    return "\n".join(lines)
