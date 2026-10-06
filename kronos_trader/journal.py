"""Forward-test journal: one CSV row per event the loop decides or observes.

The point of the forward test is a win rate and an R:R you can trust, so every
setup, approval, fill, break-even move and close lands in ``journal/trades.csv``
as it happens, and ``python -m kronos_trader journal`` reads the numbers back
from that file alone.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

FIELDS = ["time", "symbol", "event", "id", "direction", "poi_tf", "confirmation", "entry", "stop", "take_profit", "rr",
          "lots", "risk", "price", "pnl", "r", "reason", "note"]
EVENTS = ("briefing", "poi_touch", "setup", "approval_requested", "approved", "approved_late", "skipped", "expired",
          "not_executed", "filled", "submitted", "fill_confirmed", "did_not_fill", "breakeven", "closed", "stale", "deferred",
          "start")


class Journal:
    def __init__(self, path, clock=None):
        self.path = Path(path)
        self.clock = clock or (lambda: pd.Timestamp.now(tz="UTC").tz_localize(None))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=FIELDS).writeheader()

    def log(self, event: str, symbol: str, **fields: Any) -> None:
        row: Dict[str, Any] = {k: "" for k in FIELDS}
        row.update({"time": fields.pop("time", None) or self.clock(), "symbol": symbol, "event": event})
        for k, v in fields.items():
            if k in row and v is not None:
                row[k] = f"{v:.6g}" if isinstance(v, float) else v
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=FIELDS).writerow(row)

    def setup_fields(self, setup) -> Dict[str, Any]:
        return {"direction": setup.direction.name, "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value,
                "entry": float(setup.entry), "stop": float(setup.stop), "take_profit": float(setup.take_profit),
                "rr": float(setup.rr), "lots": float(setup.lots), "risk": float(setup.risk_amount)}


def summary(path) -> Dict[str, Any]:
    """Win rate, expectancy and R:R of the closed trades in a journal file."""
    path = Path(path)
    if not path.exists():
        return {"closed": 0}
    df = pd.read_csv(path)
    out: Dict[str, Any] = {"rows": len(df), "setups": int((df["event"] == "setup").sum()),
                           "approved": int((df["event"] == "approved").sum()), "skipped": int((df["event"] == "skipped").sum()),
                           "expired": int((df["event"] == "expired").sum()), "filled": int(df["event"].isin(["filled", "fill_confirmed"]).sum())}
    closed = df[df["event"] == "closed"].copy()
    closed["r"] = pd.to_numeric(closed["r"], errors="coerce")
    closed["pnl"] = pd.to_numeric(closed["pnl"], errors="coerce")
    out["closed"] = len(closed)
    if len(closed):
        wins = closed[closed["r"] > 0.05]; losses = closed[closed["r"] < -0.05]
        out.update({"wins": len(wins), "losses": len(losses), "break_even": len(closed) - len(wins) - len(losses),
                    "win_rate": len(wins) / max(1, len(wins) + len(losses)), "avg_r": float(closed["r"].mean()),
                    "sum_r": float(closed["r"].sum()), "avg_win_r": float(wins["r"].mean()) if len(wins) else 0.0,
                    "pnl": float(closed["pnl"].sum())})
        closed["month"] = pd.to_datetime(closed["time"]).dt.to_period("M").astype(str)
        out["by_month"] = {m: (len(g), round(float(g["r"].sum()), 2)) for m, g in closed.groupby("month")}
    return out


def format_summary(s: Dict[str, Any]) -> str:
    if not s.get("closed"):
        return f"journal: {s.get('setups', 0)} setups, {s.get('filled', 0)} fills, no closed trades yet"
    lines = [f"closed trades {s['closed']}  wins {s['wins']}  losses {s['losses']}  break-even {s['break_even']}  "
             f"win rate {s['win_rate']:.0%}",
             f"expectancy {s['avg_r']:+.2f}R per trade  average winner {s['avg_win_r']:+.1f}R  total {s['sum_r']:+.1f}R  P&L {s['pnl']:+,.0f}",
             f"setups {s['setups']}  approved {s['approved']}  skipped {s['skipped']}  expired {s['expired']}"]
    for m, (n, r) in s.get("by_month", {}).items():
        lines.append(f"  {m}: {n} closed, {r:+.1f}R")
    return "\n".join(lines)
