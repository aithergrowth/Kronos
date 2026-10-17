"""A local, read-only page of what the live windows are doing: ``python -m kronos_trader dashboard``.

The windows write everything the page shows next to the journal (``journal_ftmo/``): the journal rows, a heartbeat per
market after every scan, a start record per window (``starts/``), the resting limits (``limits_<symbol>.json``), the
guard's day files, the watchdog's day-report marker and the weekly parity reports; the chart images sit in ``charts/``.
The page reads those files and nothing else: no terminal, no Telegram, no network, so it can run while the windows
trade and never changes what they do. One HTML file with its style inside, reloaded by the browser every minute;
``--serve`` hands out the dashboard folder on 127.0.0.1 only. Nothing secret is on the page: a start record's settings
and command stay in the file (they name the environment variables of the secrets), a heartbeat is a time, a state and
a detail, and no environment variable is read.
"""
from __future__ import annotations

import html
import json
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .forward import PRODUCTS
from .journal import FIELDS, journal_times
from .watchdog import read_heartbeats

MARKET_ORDER = ("EURUSD", "XAUUSD", "NAS100", "BTCUSD")     # the FTMO windows in the start script's order; others follow
STALE_MINUTES = 5.0                                           # the watchdog's --max-age: a heartbeat older than this is red
NUMERIC = ("entry", "stop", "take_profit", "rr", "lots", "risk", "price", "pnl", "r")
POSITION_OVER = ("closed", "did_not_fill", "expired")         # a fill followed by one of these (same id) is no longer open
LIMIT_OVER = ("limit_cancelled", "limit_gone", "expired", "did_not_fill")
STYLE = ("body{font-family:Segoe UI,sans-serif;margin:16px;color:#222;background:#fafafa}h1{font-size:20px;margin:0 0 4px}"
         "h2{font-size:15px;margin:22px 0 6px;border-bottom:1px solid #ddd}section{margin-bottom:8px}table{border-collapse:collapse;"
         "font-size:12px}td,th{border:1px solid #ccc;padding:2px 6px;text-align:left;vertical-align:top}th{background:#eee}"
         "td.n{text-align:right;font-variant-numeric:tabular-nums}.cards{display:flex;flex-wrap:wrap;gap:8px}.card{border:1px solid "
         "#bbb;border-radius:6px;padding:6px 10px;min-width:180px;background:#eef7ee}.card.red{background:#fde8e8;border-color:#c33}"
         ".card b{font-size:14px}.muted{color:#777}.warn{color:#b00;font-weight:bold}.pill{display:inline-block;border:1px solid "
         "#ccc;border-radius:10px;padding:1px 8px;margin:2px 4px 2px 0;font-size:12px;background:#fff}code{font-family:Consolas,"
         "monospace}pre{font-size:12px;background:#fff;border:1px solid #ddd;padding:6px;white-space:pre-wrap}figure{display:inline-"
         "block;margin:4px 8px 4px 0;text-align:center}figure img{max-width:460px;border:1px solid #ccc}figcaption{font-size:11px}"
         "footer{margin-top:24px;font-size:11px;color:#777}")
e = html.escape


def _read_json(path) -> Optional[dict]:
    """A JSON file as a dict, or None when it is missing, being replaced this instant or damaged."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else {"rows": doc}
    except Exception:
        return None


def load_journal(path) -> pd.DataFrame:
    """The journal with its times and numbers parsed. A missing or unreadable file gives an empty frame with the journal's
    columns, a damaged row is dropped: the page is rendered from what can be read, it never stops on a bad line."""
    empty = pd.DataFrame(columns=FIELDS)
    try:
        if not Path(path).exists():
            return empty
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, on_bad_lines="skip", encoding="utf-8")
    except Exception:
        return empty
    for col in FIELDS:
        if col not in frame:
            frame[col] = ""
    frame["time"] = journal_times(frame["time"])
    for col in NUMERIC:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame[frame["time"].notna()].sort_values("time", kind="stable").reset_index(drop=True)


def _fmt(value) -> str:
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        return f"{value:%a %d %b %H:%M}"
    if isinstance(value, float):
        return f"{value:,.2f}" if abs(value) >= 1000 else f"{value:.6g}"
    return e(str(value).replace("_", " ")) if value != "" else ""


def _table(frame: pd.DataFrame, columns: Sequence[Tuple[str, str]], empty: str = "no data yet") -> str:
    """Rows of ``frame`` as an HTML table, ``columns`` = (column, heading); numbers right-aligned, text escaped."""
    if frame is None or not len(frame):
        return f"<p class=muted>{e(empty)}</p>"
    head = "".join(f"<th>{e(h)}</th>" for _, h in columns)
    rows = []
    for _, row in frame.iterrows():
        cells = "".join(f"<td{' class=n' if isinstance(row.get(c), float) else ''}>{_fmt(row.get(c))}</td>" for c, _ in columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table><tr>{head}</tr>{''.join(rows)}</table>"


def _starts(folder: Path) -> Dict[str, dict]:
    """The newest start record per market: the code it runs and when it started. ``starts/<symbol>_<time>.json`` carries
    the time in its name, so the last name per market sorts newest. The settings and the command stay in the file."""
    out: Dict[str, dict] = {}
    for path in sorted(folder.glob("starts/*.json")):
        doc = _read_json(path)
        if doc and doc.get("symbol"):
            code = doc.get("code") or {}
            out[str(doc["symbol"])] = {"commit": str(code.get("commit") or "?"), "dirty": bool(code.get("dirty")),
                                       "started": str(doc.get("started_utc") or "")[:16]}
    return out


def _markets(journal: pd.DataFrame, beats: Dict[str, dict], starts: Dict[str, dict]) -> List[str]:
    found = set(journal["symbol"].astype(str)) | set(beats) | set(starts)
    found.discard("")
    return [m for m in MARKET_ORDER if m in found] + sorted(m for m in found if m not in MARKET_ORDER)


def _header(product: str, account_size: Optional[float], starts: Dict[str, dict], markets: List[str]) -> str:
    """Account, product and the code each window runs; a warning when the windows differ or one has local changes
    (a trade can then not be traced to one program, and the parity check compares against the wrong backtest)."""
    name, size = (PRODUCTS[product].name if product in PRODUCTS else product), (f"{account_size:,.0f}" if account_size else "?")
    pills = [f"<span class=pill>{e(m)} <code>{e(starts[m]['commit'][:12])}</code>{' + local changes' if starts[m]['dirty'] else ''}"
             f" <span class=muted>since {e(starts[m]['started'])} UTC</span></span>" for m in markets if m in starts]
    warnings = []
    if len({starts[m]["commit"] for m in markets if m in starts}) > 1:
        warnings.append("the windows run different code: restart them on one commit")
    if any(starts[m]["dirty"] for m in markets if m in starts):
        warnings.append("a window runs with local changes (not committed)")
    body = (f"<p>account <b>{size}</b> &middot; {e(name)} &middot; code per window: {''.join(pills) or '<span class=muted>no start records yet</span>'}</p>"
            + "".join(f"<p class=warn>&#9888; {e(w)}</p>" for w in warnings))
    return f"<header><h1>Kronos live</h1>{body}</header>"


def _status(beats: Dict[str, dict], markets: List[str], now: pd.Timestamp) -> str:
    """One card per market from its heartbeat: how long ago it scanned, its state and detail. Red when the heartbeat is
    older than the watchdog's limit or the last scan did not run through."""
    cards = []
    for m in markets:
        b = beats.get(m)
        seen = pd.Timestamp(b["time"]) if b and b.get("time") else None
        if b is None or seen is None:
            cards.append(f"<div class='card red'><b>{e(m)}</b><br>no heartbeat yet</div>")
            continue
        age = max(0.0, (now - seen).total_seconds() / 60.0)
        state = str(b.get("state") or "?")
        red = age > STALE_MINUTES or state != "ok"
        lines = [f"last scan {age:.0f} min ago" + (" (STALE: no scan for more than 5 minutes)" if age > STALE_MINUTES else ""),
                 f"state: {state}" + (f" - {b.get('detail')}" if b.get("detail") else ""),
                 f"last candle {str(b.get('last_candle') or '')[:16]}" if b.get("last_candle") else "", str(b.get("stale") or "")]
        cards.append(f"<div class='card{' red' if red else ''}'><b>{e(m)}</b><br>" + "<br>".join(e(x) for x in lines if x) + "</div>")
    return f"<div class=cards>{''.join(cards)}</div>" if cards else "<p class=muted>no data yet</p>"


def open_positions(journal: pd.DataFrame) -> pd.DataFrame:
    """The fills the journal has not seen the end of: the latest ``filled`` per id without a closed, did_not_fill or expired
    of the same id (the id its window gave the position; the terminal is not asked)."""
    over = set(journal.loc[journal["event"].isin(POSITION_OVER), "id"].astype(str))
    fills = journal[journal["event"] == "filled"].drop_duplicates("id", keep="last")
    return fills[~fills["id"].astype(str).isin(over)]


def resting_limits(journal: pd.DataFrame) -> pd.DataFrame:
    """The placed limits still waiting: the latest ``limit_placed`` per id without a later cancel, gone, expiry, or a fill
    whose note names it (a filled limit becomes a position under the position's id)."""
    over = set(journal.loc[journal["event"].isin(LIMIT_OVER), "id"].astype(str))
    for note in journal.loc[journal["event"] == "filled", "note"].astype(str):
        if "limit " in note:
            over.add(note.split("limit ", 1)[1].split(";")[0].strip())
    placed = journal[journal["event"] == "limit_placed"].drop_duplicates("id", keep="last")
    return placed[~placed["id"].astype(str).isin(over)]


def _since(now: pd.Timestamp, tz: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """The start of today and of this week (Monday) in the product's day timezone, as naive UTC like the journal."""
    local = now.tz_localize("UTC").tz_convert(tz).normalize()
    return (local.tz_convert("UTC").tz_localize(None),
            (local - pd.Timedelta(days=local.weekday())).tz_convert("UTC").tz_localize(None))


def closed_trades(journal: pd.DataFrame, since: pd.Timestamp) -> pd.DataFrame:
    """The closes from ``since`` on, oldest first, with the running R and P&L down the list."""
    closed = journal[(journal["event"] == "closed") & (journal["time"] >= since)].copy()
    closed["total_r"], closed["total_pnl"] = closed["r"].fillna(0.0).cumsum(), closed["pnl"].fillna(0.0).cumsum()
    return closed


def _closed_section(journal: pd.DataFrame, now: pd.Timestamp, tz: str) -> str:
    day, week = _since(now, tz)
    cols = [("time", "closed (UTC)"), ("symbol", "market"), ("id", "id"), ("direction", "side"), ("reason", "reason"),
            ("entry", "entry"), ("price", "exit"), ("lots", "lots"), ("r", "R"), ("pnl", "P&L"), ("total_r", "running R"),
            ("total_pnl", "running P&L")]
    parts = []
    for title, frame in (("Today", closed_trades(journal, day)), ("This week", closed_trades(journal, week))):
        total = (f" &middot; {len(frame)} closed, <b>{frame['r'].fillna(0).sum():+.2f}R</b>, P&amp;L <b>{frame['pnl'].fillna(0).sum():+,.0f}</b>"
                 if len(frame) else "")
        parts.append(f"<h3>{title} <span class=muted>({e(tz)} day)</span>{total}</h3>" + _table(frame, cols, "no closed trades yet"))
    return "".join(parts)


def _guard(folder: Path, product: str, account_size: Optional[float], journal: pd.DataFrame, now: pd.Timestamp, tz: str) -> str:
    """The room under the product's floors as the guard files and the journal know it: the day's start balance the windows
    agreed on, the day floor (that balance less the daily % of the initial balance), the total floor, and the estimate of
    the room left from today's closes in the journal. The terminal's equity decides; this is the journal's view."""
    day_start, day_high, report = (_read_json(folder / n) for n in ("guard_day_start.json", "guard_day_high.json", "day_report.json"))
    if not any((day_start, day_high, report)):
        return "<p class=muted>no guard files yet</p>"
    prod = PRODUCTS.get(product)
    initial = float(account_size or (day_start or {}).get("account_size") or (day_high or {}).get("account_size") or 0.0)
    lines = []
    if day_start and prod and initial:
        balance = float(day_start.get("balance", 0.0))
        pnl_today = float(closed_trades(journal, _since(now, tz)[0])["pnl"].fillna(0).sum())
        floor = balance - prod.daily_pct / 100.0 * initial
        lines.append(f"day {e(str(day_start.get('day')))}: start balance {balance:,.2f}, day floor {floor:,.2f} "
                     f"(-{prod.daily_pct:g} % of {initial:,.0f}); closed today in the journal {pnl_today:+,.2f}, so about "
                     f"<b>{balance + pnl_today - floor:,.2f}</b> left today before open risk")
    if prod and initial:
        high = float((day_high or {}).get("day_high") or initial)
        total_floor = (max(initial, high) if prod.total_basis == "eod_high" else initial) - prod.total_pct / 100.0 * initial
        lines.append(f"total floor {total_floor:,.2f} (-{prod.total_pct:g} % of {initial:,.0f}"
                     + (f", from the highest day start {high:,.2f}" if prod.total_basis == "eod_high" else "") + ")")
    if report and report.get("date"):
        lines.append(f"the watchdog's day report last went out on {e(str(report['date']))}")
    return "".join(f"<p>{line}</p>" for line in lines) or "<p class=muted>no guard files yet</p>"


def _briefings(journal: pd.DataFrame, markets: List[str]) -> str:
    rows = journal[journal["event"] == "briefing"].drop_duplicates("symbol", keep="last").set_index("symbol")
    items = [f"<tr><td>{e(m)}</td><td>{_fmt(rows.loc[m, 'time'])}</td><td class=n>{_fmt(rows.loc[m, 'price'])}</td>"
             f"<td>{e(str(rows.loc[m, 'note']))}</td></tr>" if m in rows.index else
             f"<tr><td>{e(m)}</td><td colspan=3 class=muted>no briefing yet</td></tr>" for m in markets]
    return (f"<table><tr><th>market</th><th>when (UTC)</th><th>price</th><th>decision</th></tr>{''.join(items)}</table>"
            if items else "<p class=muted>no data yet</p>")


def _charts(charts_dir: Path, out_dir: Path, markets: List[str]) -> str:
    """The newest two chart images per market, copied into ``<out>/charts/`` so the page finds them by the same relative
    path from the file and over --serve (the server hands out the dashboard folder only); older copies are removed."""
    keep: Dict[str, Path] = {}
    for m in markets:
        files = sorted(charts_dir.glob(f"{m}_*.png"), key=lambda p: (p.stat().st_mtime, p.name), reverse=True)[:2]
        keep.update({p.name: p for p in files})
    if not keep:
        return "<p class=muted>no chart images yet</p>"
    folder = out_dir / "charts"
    folder.mkdir(parents=True, exist_ok=True)
    for name, src in keep.items():
        dst = folder / name
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)                   # a chart being drawn this instant is copied again next build
    for old in folder.glob("*.png"):
        if old.name not in keep:
            old.unlink(missing_ok=True)
    figures = [f"<figure><img src='charts/{e(n)}' alt='{e(n)}'><figcaption>{e(n[:-4].replace('_', ' '))} &middot; "
               f"{pd.Timestamp(keep[n].stat().st_mtime, unit='s'):%a %H:%M} UTC</figcaption></figure>"
               for n in sorted(keep, key=lambda n: (keep[n].stat().st_mtime, n), reverse=True)]
    return "".join(figures)


def _parity(folder: Path) -> str:
    """The first 30 lines of the newest parity report (``parity/parity_<Monday>.md``: the name sorts by week)."""
    reports = sorted(folder.glob("parity/parity_*.md"))
    if not reports:
        return "<p class=muted>no parity report yet</p>"
    lines = reports[-1].read_text(encoding="utf-8", errors="replace").splitlines()[:30]
    return f"<p class=muted>{e(reports[-1].name)}</p><pre>{e(chr(10).join(lines))}</pre>"


def build_dashboard(journal_path, charts_dir, out_path, product: str = "ftmo_2step", account_size: Optional[float] = None,
                    now: Optional[pd.Timestamp] = None) -> Path:
    """Render the page to ``out_path`` from the journal folder and the charts folder and return its path. Every section
    is rendered on its own: a file that cannot be read shows "no data yet" or the error in its place, the rest of the
    page still appears, and the function never raises (the loop that calls it every minute must go on)."""
    now = now if now is not None else pd.Timestamp.now("UTC").tz_localize(None)
    journal_path, charts_dir, out_path = Path(journal_path), Path(charts_dir), Path(out_path)
    folder, tz = journal_path.parent, PRODUCTS[product].day_timezone if product in PRODUCTS else "UTC"
    journal, beats, starts = load_journal(journal_path), read_heartbeats(folder), _starts(folder)
    markets = _markets(journal, beats, starts)
    position_cols = [("time", "filled (UTC)"), ("symbol", "market"), ("id", "id"), ("direction", "side"), ("entry", "entry"),
                     ("stop", "stop"), ("take_profit", "target"), ("lots", "lots"), ("risk", "risk"), ("note", "note")]
    event_cols = [("time", "time (UTC)"), ("symbol", "market"), ("event", "event"), ("id", "id"), ("direction", "side"),
                  ("entry", "entry"), ("stop", "stop"), ("take_profit", "target"), ("price", "price"), ("lots", "lots"),
                  ("r", "R"), ("pnl", "P&L"), ("reason", "reason"), ("note", "note")]
    sections: List[Tuple[str, Callable[[], str]]] = [
        ("Windows (one per market)", lambda: _status(beats, markets, now)),
        ("Open positions (as the journal knows them)", lambda: _table(open_positions(journal), position_cols, "no open position")),
        ("Resting limits", lambda: _table(resting_limits(journal), position_cols, "no resting limit")),
        ("Closed trades", lambda: _closed_section(journal, now, tz)),
        ("Guard room", lambda: _guard(folder, product, account_size, journal, now, tz)),
        ("Last briefing per market", lambda: _briefings(journal, markets)),
        ("Last events (newest first)", lambda: _table(journal.tail(60).iloc[::-1], event_cols)),
        ("Latest charts", lambda: _charts(charts_dir, out_path.parent, markets)),
        ("Parity (latest weekly check)", lambda: _parity(folder))]
    parts = []
    for title, render in sections:
        try:
            body = render()
        except Exception as exc:              # one bad file must not take the whole page down
            body = f"<p class=warn>could not render ({e(type(exc).__name__)}: {e(str(exc))})</p>"
        parts.append(f"<section><h2>{e(title)}</h2>{body}</section>")
    head = _header(product, account_size, starts, markets)      # formats the coerced start records only: nothing to catch
    page = (f"<!doctype html><html lang=en><head><meta charset=utf-8><meta http-equiv=refresh content=60>"
            f"<title>Kronos live - {e(product)}</title><style>{STYLE}</style></head><body>{head}{''.join(parts)}"
            f"<footer>written {now:%Y-%m-%d %H:%M:%S} UTC from {e(str(journal_path))} by python -m kronos_trader dashboard; "
            f"the browser reloads it every minute</footer></body></html>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out_path)                 # the browser never reads a half-written page
    return out_path


def serve(folder, port: int) -> str:
    """Hand out ``folder`` on http://127.0.0.1:<port>/ from a daemon thread, quietly and without caching; the address is
    the laptop's own, so nothing else on the network can reach it. Returns the URL."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, *args: Any) -> None:
            pass

        def end_headers(self) -> None:
            self.send_header("Cache-Control", "no-cache")
            super().end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", int(port)), partial(Handler, directory=str(folder)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{int(port)}/"


def run(args) -> int:
    """The ``dashboard`` command: build once; with --every build again every so many seconds; with --serve also hand the
    folder out on the laptop's own address (then it keeps building every minute even without --every)."""
    out = Path(args.out)
    every = float(args.every or 0) or (60.0 if args.serve else 0.0)

    def build() -> None:
        build_dashboard(args.journal, args.charts, out, product=args.product, account_size=args.account_size)
        print(f"[dashboard] {pd.Timestamp.now('UTC'):%H:%M:%S} UTC written {out}")

    build()
    if args.serve:
        print(f"dashboard: {serve(out.parent, args.serve)} (this computer only; Ctrl+C stops it)")
    while every > 0:
        time.sleep(every)
        try:
            build()
        except Exception as exc:              # build_dashboard does not raise, but a full disk might: say so, go on
            print(f"[dashboard] {type(exc).__name__}: {exc}")
    return 0
