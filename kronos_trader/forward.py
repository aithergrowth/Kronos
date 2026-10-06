"""The forward record: what the bot planned (the journal) against what the broker booked (the MT5 deal history).

``reconcile`` gives one row per position the account traded: the setup the engine planned, the fill and the exit(s)
the broker booked, the slippage against the plan in price and in R, commission, swap and fee, the R before and after
costs, and the code and settings the window ran (its last ``start`` row before the fill). Positions without a fill in
the journal are the account's other trades (by hand, another program): the funding limits count them too, so they are
listed, never mixed into the bot's numbers.

``funding_status`` reads the account against a prop-firm product's limits: what is left of the day's loss allowance
and of the total, the open risk to every stop (manual positions included) and the margin in use.

The functions take plain frames and dicts, so they are tested without a terminal; ``deals_from_mt5`` and
``account_from_mt5`` are the only parts that talk to MetaTrader 5, and they only read.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

DEAL_COLUMNS = ["ticket", "order", "position_id", "symbol", "type", "entry", "reason", "time", "price", "volume",
                "profit", "commission", "swap", "fee", "magic", "comment"]
BUY, SELL = 0, 1                                     # DEAL_TYPE_BUY / DEAL_TYPE_SELL (balance operations are 2 and up)
ENTRY_IN, ENTRY_OUT, ENTRY_INOUT, ENTRY_OUT_BY = 0, 1, 2, 3
REASONS = {0: "client", 1: "mobile", 2: "web", 3: "expert", 4: "stop", 5: "take_profit", 6: "stop_out", 7: "rollover",
           8: "variation_margin", 9: "split"}


@dataclass(frozen=True)
class Product:
    """A funding product's loss limits, in % of the initial balance. ``total_basis`` "initial": the floor is the initial
    balance less ``total_pct``; "eod_high": the highest balance at a day's start less ``total_pct`` (trailing)."""
    name: str
    daily_pct: float
    total_pct: float
    total_basis: str = "initial"
    day_timezone: str = "Europe/Prague"            # FTMO's day starts at midnight CE(S)T


PRODUCTS: Dict[str, Product] = {
    "ftmo_2step": Product("FTMO 2-Step", daily_pct=5.0, total_pct=10.0, total_basis="initial"),
    "ftmo_1step": Product("FTMO 1-Step", daily_pct=3.0, total_pct=10.0, total_basis="eod_high"),
}


# ------------------------------------------------------------------ reading the terminal (read only)

def deals_from_mt5(broker, since: pd.Timestamp, until: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """The account's deals from ``since`` (naive UTC) on, every magic number, as a frame with ``DEAL_COLUMNS`` (UTC)."""
    mt5 = broker.mt5
    start = pd.Timestamp(since) + broker.server_offset() - pd.Timedelta(days=1)       # server time, a day early
    end = (pd.Timestamp(until) if until is not None else pd.Timestamp.now()) + pd.Timedelta(days=2)
    raw = mt5.history_deals_get(start.to_pydatetime(), end.to_pydatetime())
    if raw is None:
        raise RuntimeError(f"MT5 did not return the deal history: {mt5.last_error()}")
    rows = []
    for d in raw:
        name = str(getattr(d, "symbol", "") or "")
        rows.append({"ticket": int(d.ticket), "order": int(getattr(d, "order", 0) or 0),
                     "position_id": int(getattr(d, "position_id", 0) or 0), "symbol": broker.our_symbol(name) if name else "",
                     "type": int(d.type), "entry": int(getattr(d, "entry", 0) or 0), "reason": int(getattr(d, "reason", -1)),
                     "time": broker.to_utc(d.time), "price": float(d.price), "volume": float(d.volume),
                     "profit": float(d.profit), "commission": float(getattr(d, "commission", 0.0) or 0.0),
                     "swap": float(getattr(d, "swap", 0.0) or 0.0), "fee": float(getattr(d, "fee", 0.0) or 0.0),
                     "magic": int(getattr(d, "magic", 0) or 0), "comment": str(getattr(d, "comment", "") or "")})
    frame = pd.DataFrame(rows, columns=DEAL_COLUMNS)
    if len(frame):
        frame = frame[(frame["time"] >= pd.Timestamp(since)) | (frame["type"] > SELL)]
    return frame.reset_index(drop=True)


def account_from_mt5(broker) -> Dict[str, Any]:
    """Balance, equity, margin and every open position (all magic numbers) with its loss at the stop."""
    mt5 = broker.mt5
    info = mt5.account_info()
    if info is None:
        raise RuntimeError(f"MT5 did not return the account: {mt5.last_error()}")
    raw = mt5.positions_get()
    if raw is None:
        raise RuntimeError(f"MT5 did not list the open positions: {mt5.last_error()}")
    from .core.types import Direction
    positions = []
    for p in raw:
        symbol = broker.our_symbol(str(p.symbol))
        direction = Direction.LONG if p.type == mt5.POSITION_TYPE_BUY else Direction.SHORT
        sl = float(p.sl or 0.0)
        loss = None
        if sl:
            try:
                loss = -float(broker.pnl_for(symbol, direction, float(p.price_open), sl, float(p.volume)))
            except Exception:
                loss = None
        positions.append({"position_id": int(p.ticket), "symbol": symbol, "direction": direction.name, "volume": float(p.volume),
                          "price_open": float(p.price_open), "sl": sl, "tp": float(p.tp or 0.0), "profit": float(p.profit),
                          "swap": float(getattr(p, "swap", 0.0) or 0.0), "magic": int(p.magic), "loss_at_stop": loss,
                          "source": "bot" if int(p.magic) == int(getattr(broker, "magic", -1)) else "other",
                          "opened": broker.to_utc(p.time)})
    return {"balance": float(info.balance), "equity": float(info.equity), "margin": float(getattr(info, "margin", 0.0) or 0.0),
            "margin_free": float(getattr(info, "margin_free", 0.0) or 0.0), "currency": str(getattr(info, "currency", "") or ""),
            "login": getattr(info, "login", None), "server": str(getattr(info, "server", "") or ""), "positions": positions}


# ------------------------------------------------------------------ the journal

def read_journal(path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"id": str})
    frame["time"] = pd.to_datetime(frame["time"], errors="coerce")
    for col in ("entry", "stop", "take_profit", "rr", "lots", "risk", "price", "pnl", "r"):
        if col in frame:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame


def _setup_id(note: Any) -> Optional[str]:
    m = re.search(r"setup (\w+)", str(note or ""))
    return m.group(1) if m else None


# ------------------------------------------------------------------ the reconciliation

def _vwap(rows: pd.DataFrame) -> float:
    v = rows["volume"].sum()
    return float((rows["price"] * rows["volume"]).sum() / v) if v > 0 else float("nan")


def reconcile(journal: pd.DataFrame, deals: pd.DataFrame, magic: Optional[int] = None) -> pd.DataFrame:
    """One row per position in ``deals`` (trade deals only), matched to the journal's ``filled`` row with that position
    id; its ``setup`` row (the id in the fill's note) gives the plan, the last ``start`` row of the symbol before the
    fill the code. ``source`` is "bot" for a journal match or the bot's magic number, else "other"."""
    trades = deals[deals["type"].isin([BUY, SELL]) & (deals["position_id"] > 0)] if len(deals) else deals
    fills = journal[journal["event"].isin(["filled", "submitted"])] if len(journal) else journal
    fills = fills.drop_duplicates("id", keep="first").set_index("id") if len(fills) else fills
    setups = journal[journal["event"] == "setup"].drop_duplicates("id", keep="last").set_index("id") if len(journal) else journal
    starts = journal[journal["event"] == "start"].sort_values("time") if len(journal) else journal
    closes = journal[journal["event"] == "closed"].drop_duplicates("id", keep="last").set_index("id") if len(journal) else journal
    moved = journal[journal["event"] == "breakeven"].drop_duplicates("id", keep="last").set_index("id") if len(journal) else journal
    rows: List[Dict[str, Any]] = []
    for pid, group in trades.groupby("position_id", sort=False):
        group = group.sort_values("time")
        ins = group[group["entry"].isin([ENTRY_IN, ENTRY_INOUT])]
        outs = group[group["entry"].isin([ENTRY_OUT, ENTRY_OUT_BY, ENTRY_INOUT])]
        if not len(ins):
            continue                                   # opened before the window read: no entry deal to judge
        sign = 1.0 if int(ins.iloc[0]["type"]) == BUY else -1.0
        key = str(pid)
        fill = fills.loc[key] if len(fills) and key in fills.index else None
        sid = _setup_id(fill["note"]) if fill is not None else None
        plan = setups.loc[sid] if sid is not None and len(setups) and sid in setups.index else None
        source = "bot" if fill is not None or (magic is not None and int(group["magic"].iloc[0]) == int(magic)) else "other"
        entry_price, volume = _vwap(ins), float(ins["volume"].sum())
        closed = len(outs) and outs["volume"].sum() >= volume - 1e-9
        exit_price = _vwap(outs) if len(outs) else float("nan")
        last_out = outs.iloc[-1] if len(outs) else None
        profit = float(group["profit"].sum())
        costs = float(group[["commission", "swap", "fee"]].sum().sum())
        risk = float(fill["risk"]) if fill is not None and pd.notna(fill.get("risk")) else float("nan")
        p_entry = float(plan["entry"]) if plan is not None else float("nan")
        p_stop = float(plan["stop"]) if plan is not None else (float(fill["stop"]) if fill is not None else float("nan"))
        p_tp = float(plan["take_profit"]) if plan is not None else (float(fill["take_profit"]) if fill is not None else float("nan"))
        p_dist = abs(p_entry - p_stop) if plan is not None else float("nan")
        reason = REASONS.get(int(last_out["reason"]), str(int(last_out["reason"]))) if last_out is not None else ""
        if reason == "stop" and len(moved) and key in moved.index and pd.notna(moved.loc[key].get("stop")):
            exit_ref = float(moved.loc[key]["stop"])     # the stop had moved to break-even: that is the level it left at
        else:
            exit_ref = p_stop if reason == "stop" else p_tp if reason == "take_profit" else float("nan")
        code = ""
        symbol = str(group["symbol"].iloc[0])
        if len(starts):
            before = starts[(starts["symbol"].astype(str).str.upper() == symbol.upper()) & (starts["time"] <= ins.iloc[0]["time"])]
            code = str(before.iloc[-1]["note"]) if len(before) else ""
        rows.append({
            "position_id": key, "symbol": symbol, "direction": "LONG" if sign > 0 else "SHORT", "source": source,
            "status": "closed" if closed else "open", "setup_id": sid or "", "planned_entry": p_entry, "planned_stop": p_stop,
            "planned_take_profit": p_tp, "planned_rr": float(plan["rr"]) if plan is not None else float("nan"),
            "fill_time": ins.iloc[0]["time"], "fill_price": entry_price, "lots": volume,
            "exit_time": last_out["time"] if last_out is not None else pd.NaT, "exit_price": exit_price, "exit_reason": reason,
            # slippage against the plan, positive = against us: the entry from the confirmation close, the exit from the level
            "entry_slip": sign * (entry_price - p_entry), "entry_slip_r": sign * (entry_price - p_entry) / p_dist if p_dist else float("nan"),
            "exit_slip": sign * (exit_ref - exit_price) if closed else float("nan"),
            "exit_slip_r": sign * (exit_ref - exit_price) / p_dist if closed and p_dist else float("nan"),
            "profit": profit, "commission": float(group["commission"].sum()), "swap": float(group["swap"].sum()),
            "fee": float(group["fee"].sum()), "net": profit + costs, "risk": risk,
            "r_gross": profit / risk if risk and risk == risk else float("nan"),
            "r_net": (profit + costs) / risk if risk and risk == risk else float("nan"),
            "cost_r": costs / risk if risk and risk == risk else float("nan"),
            "journal_r": float(closes.loc[key]["r"]) if len(closes) and key in closes.index else float("nan"),
            "code": code,
        })
    return pd.DataFrame(rows)


def unmatched_fills(journal: pd.DataFrame, rec: pd.DataFrame) -> pd.DataFrame:
    """Fills the journal recorded that the deal history does not show (outside the range read, or never booked)."""
    fills = journal[journal["event"] == "filled"] if len(journal) else journal
    seen = set(rec["position_id"]) if len(rec) else set()
    return fills[~fills["id"].astype(str).isin(seen)] if len(fills) else fills


def summary(rec: pd.DataFrame) -> pd.DataFrame:
    """Per source and market (and all): closed trades, win rate, R after costs, slippage and costs in R, net money."""
    if not len(rec):
        return pd.DataFrame()
    closed = rec[rec["status"] == "closed"]
    out = []
    groups = [((s, "all"), g) for s, g in closed.groupby("source")] + [((s, m), g) for (s, m), g in closed.groupby(["source", "symbol"])]
    for (source, symbol), g in groups:
        won = g[g["net"] > 0]
        out.append({"source": source, "market": symbol, "closed": len(g), "won": len(won),
                    "win_rate": round(len(won) / len(g), 3) if len(g) else float("nan"),
                    "r_net": round(float(g["r_net"].sum()), 2), "r_gross": round(float(g["r_gross"].sum()), 2),
                    "avg_entry_slip_r": round(float(g["entry_slip_r"].mean()), 3) if g["entry_slip_r"].notna().any() else float("nan"),
                    "avg_exit_slip_r": round(float(g["exit_slip_r"].mean()), 3) if g["exit_slip_r"].notna().any() else float("nan"),
                    "costs_r": round(float(g["cost_r"].sum()), 2), "net": round(float(g["net"].sum()), 2)})
    out.append({"source": "open", "market": "all", "closed": int((rec["status"] == "open").sum())})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ the funding limits

def funding_status(account: Dict[str, Any], deals: pd.DataFrame, product: Product, initial: float,
                   now: pd.Timestamp, eod_balances: Optional[List[float]] = None) -> Dict[str, Any]:
    """The account against ``product``: the day's start balance (balance less what closed since the day began in the
    product's timezone), the day's floor (that balance less ``daily_pct`` of the initial balance) and the total floor,
    what is left of each now (equity based), the open risk to every stop, manual positions included, and the worst case
    if every stop is hit. Positions without a stop make the worst case unbounded. The products' numbers follow FTMO's
    published terms as read in October 2026; check them against the account's own terms before relying on them."""
    tz = product.day_timezone
    local_now = pd.Timestamp(now).tz_localize("UTC").tz_convert(tz)
    day_start = local_now.normalize().tz_convert("UTC").tz_localize(None)
    trade = deals[deals["type"].isin([BUY, SELL])] if len(deals) else deals
    since_day = trade[trade["time"] >= day_start] if len(trade) else trade
    closed_today = float(since_day[["profit", "commission", "swap", "fee"]].sum().sum()) if len(since_day) else 0.0
    balance, equity = float(account["balance"]), float(account["equity"])
    day_start_balance = balance - closed_today
    daily_floor = day_start_balance - product.daily_pct / 100.0 * initial
    if product.total_basis == "eod_high":
        high = max([initial, day_start_balance] + list(eod_balances or []))
        total_floor = high - product.total_pct / 100.0 * initial
    else:
        total_floor = initial - product.total_pct / 100.0 * initial
    positions = account.get("positions", [])
    no_stop = [p for p in positions if not p.get("sl")]
    open_risk = float(sum(max(0.0, p["loss_at_stop"] or 0.0) for p in positions if p.get("loss_at_stop") is not None))
    worst = None if no_stop else equity - sum(float(p.get("profit", 0.0)) for p in positions) - open_risk
    floor = max(daily_floor, total_floor)
    return {"product": product.name, "day_start_utc": str(day_start), "balance": balance, "equity": equity,
            "day_start_balance": round(day_start_balance, 2), "closed_today": round(closed_today, 2),
            "daily_floor": round(daily_floor, 2), "total_floor": round(total_floor, 2),
            "left_today": round(equity - daily_floor, 2), "left_total": round(equity - total_floor, 2),
            "left_today_pct": round((equity - daily_floor) / initial * 100.0, 2),
            "left_total_pct": round((equity - total_floor) / initial * 100.0, 2),
            "open_positions": len(positions), "manual_positions": sum(1 for p in positions if p.get("source") == "other"),
            "open_risk": round(open_risk, 2), "positions_without_stop": [p["position_id"] for p in no_stop],
            "worst_case_equity": None if worst is None else round(worst, 2),
            "worst_case_breaks": None if worst is None else bool(worst <= floor),
            "margin": account.get("margin"), "margin_free": account.get("margin_free")}


# ------------------------------------------------------------------ the report

def write_report(out_dir, rec: pd.DataFrame, summ: pd.DataFrame, status: Optional[Dict[str, Any]],
                 unmatched: pd.DataFrame, account_positions: Optional[List[Dict[str, Any]]] = None,
                 title: str = "Kronos forward record") -> Path:
    """``forward_trades.csv`` and ``forward_report.html`` (status, summary, every trade, the account's other positions,
    journal fills the history does not show) in ``out_dir``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rec.to_csv(out / "forward_trades.csv", index=False)
    parts = [f"<h1>{html.escape(title)}</h1>", f"<p>written {pd.Timestamp.now('UTC'):%Y-%m-%d %H:%M} UTC</p>"]
    if status is not None:
        parts += ["<h2>Funding limits</h2>", pd.DataFrame([status]).T.rename(columns={0: "value"}).to_html()]
    parts += ["<h2>Summary</h2>", summ.to_html(index=False) if len(summ) else "<p>no closed trades yet</p>"]
    parts += ["<h2>Trades</h2>", rec.to_html(index=False, float_format=lambda v: f"{v:.5g}") if len(rec) else "<p>none</p>"]
    if account_positions:
        parts += ["<h2>Open positions on the account</h2>", pd.DataFrame(account_positions).to_html(index=False)]
    if len(unmatched):
        parts += ["<h2>Journal fills not in the deal history</h2>", unmatched.to_html(index=False)]
    page = ("<!doctype html><html><head><meta charset='utf-8'><title>Kronos forward record</title>"
            "<style>body{font-family:sans-serif;margin:16px}table{border-collapse:collapse;font-size:12px}"
            "td,th{border:1px solid #ccc;padding:2px 6px}</style></head><body>" + "".join(parts) + "</body></html>")
    path = out / "forward_report.html"
    path.write_text(page, encoding="utf-8")
    return path
