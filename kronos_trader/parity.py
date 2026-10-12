"""The weekly parity check: did the live windows do what the backtest does on the same candles?

Each market's window is rebuilt from its start record (``starts/<symbol>_<time>.json`` next to the journal: the command it
ran and the settings it resolved, through ``cli.live_settings`` as the window built them), its candles come from the MT5
terminal the window trades on, and the backtester walks the week (after a warm-up) with the window's settings and its
news calendar. A setup has the same id on both sides (``journal.setup_id``: the zone's key and the confirmation candle),
so the two lists line up one to one:

    match            both saw the setup and did the same with it (a trade with the same exit, a limit that did not fill,
                     a refusal)
    outcome differs  both saw it, the result differs (a stop live and the target in the backtest, refused on one side)
    backtest only    the backtest signalled, the window did not (it was down, or saw other candles or other state)
    live only        the window signalled, the backtest did not

The report (markdown and CSV in ``parity/`` next to the journal) gives each difference the explanation the files hold: the
window was down (its next journal row is a restart), it ran other settings, a live-only rule (the spread cap, the
account's other markets in the guard: the backtest runs one market at a time). The candles it used stay beside the report,
so a later look reruns the week on exactly them (``--data-dir``). It only reads: no order, no change to a window's files.
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from .core.timeframe import Timeframe

#: the FTMO windows' profiles (scripts/start_ftmo.bat), used for a market without a start record next to the journal
LIVE_PROFILES: Dict[str, str] = {"EURUSD": "config/dorus_live.yaml", "XAUUSD": "config/dorus_live_gold.yaml",
                                 "NAS100": "config/dorus_live_nas100.yaml", "BTCUSD": "config/dorus_live_btc.yaml"}
#: candles taken from the terminal per timeframe: the engine's lookback (5m/15m 400, 1H/4H 300, 1D 250, 1W 104, 1MO 60)
#: and two to three weeks on top; 5000 stays inside a terminal whose "Max bars in chart" is 5000
EXPORT_COUNTS: Dict[Timeframe, int] = {Timeframe.MIN_5: 5000, Timeframe.MIN_15: 3000, Timeframe.H_1: 2000,
                                       Timeframe.H_4: 1000, Timeframe.D_1: 600, Timeframe.W_1: 200, Timeframe.MN_1: 100}
#: what ``MT5Broker.align_spec`` writes into a window's contract at its start (the server's numbers): taken from the start
#: record, so the backtest sizes as the window did and the settings compare equal
SERVER_SPEC_FIELDS = ("pip_value_per_lot", "min_lot", "lot_step", "max_lot")
LOCAL_TZ = "Europe/Amsterdam"
SETUP_RE = re.compile(r"\bsetup ([0-9a-f]{8})\b")
VERDICTS = ("match", "outcome differs", "backtest only", "live only")


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def local(ts, fmt: str = "%a %d %b %H:%M") -> str:
    """A naive UTC time as Amsterdam time (the report's clock: the one Max trades by)."""
    if ts is None or pd.isna(ts):
        return ""
    return pd.Timestamp(ts).tz_localize("UTC").tz_convert(LOCAL_TZ).strftime(fmt)


def week_window(week: str = "auto", now: Optional[pd.Timestamp] = None) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """The week to check, Monday 00:00 UTC to the next Monday (naive UTC), its end no later than ``now``. ``auto``: the week
    so far, on a Monday the week before; ``this``; ``last``; or a date (YYYY-MM-DD) inside the week."""
    now = pd.Timestamp(now) if now is not None else utc_now()
    w = (week or "auto").strip().lower()
    if w == "auto":
        w = "last" if now.dayofweek == 0 else "this"
    if w in ("this", "last"):
        day = now.normalize() - pd.Timedelta(days=7 if w == "last" else 0)
    else:
        day = pd.Timestamp(week).normalize()
    monday = day - pd.Timedelta(days=int(day.dayofweek))
    return monday, min(monday + pd.Timedelta(days=7), now)


# ------------------------------------------------------------------ the windows' settings

@dataclass
class StartRecord:
    """One window start (``LiveRunner.record_start``): the command it ran and the settings it resolved."""
    symbol: str
    started: pd.Timestamp
    command: str
    commit: str
    dirty: bool
    settings_sha: str
    settings: Dict[str, Any]
    path: Optional[Path] = None


def start_records(journal_dir, symbol: Optional[str] = None) -> List[StartRecord]:
    """The windows' start records next to the journal (``starts/<symbol>_<time>.json``), oldest first."""
    folder = Path(journal_dir) / "starts"
    out: List[StartRecord] = []
    if not folder.exists():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            started = pd.Timestamp(doc.get("started_utc"))
        except Exception:
            continue
        sym = str(doc.get("symbol") or "").upper()
        if not sym or pd.isna(started) or (symbol and sym != symbol.upper()):
            continue
        code = doc.get("code") or {}
        out.append(StartRecord(sym, started, str(doc.get("command") or ""), str(code.get("commit") or ""),
                               bool(code.get("dirty")), str(doc.get("settings_sha256") or ""), doc.get("settings") or {}, path))
    return sorted(out, key=lambda r: r.started)


def record_in_effect(records: Sequence[StartRecord], end: pd.Timestamp) -> Optional[StartRecord]:
    """The start whose settings ran at ``end``: the last one at or before it, else the first one after."""
    before = [r for r in records if r.started <= end]
    return before[-1] if before else (records[0] if records else None)


def command_argv(command: str) -> List[str]:
    """The arguments of a recorded command line (``" ".join(sys.argv)``) without the program's path: from the first option
    or the ``live`` command on."""
    tokens = str(command or "").split()
    for i, tok in enumerate(tokens):
        if tok.startswith("--") or tok == "live":
            return tokens[i:]
    return []


def fallback_argv(symbol: str, profile: str, account_size: Optional[float] = None, product: Optional[str] = None,
                  mt5_name: Optional[str] = None, journal=None) -> List[str]:
    """A window's command as scripts/start_ftmo.bat builds it, for a market without a start record."""
    argv = ["--config", profile, "live", "--symbol", symbol, "--broker", "mt5"]
    if account_size:
        argv += ["--account-size", f"{float(account_size):g}"]
    if product:
        argv += ["--product", product]
    if mt5_name:
        argv += ["--mt5-symbol", mt5_name]
    if journal:
        argv += ["--journal", str(journal)]
    return argv


def window_settings(command: Optional[str], fallback: Sequence[str]) -> Tuple[Any, str, str]:
    """The settings a window ran with, rebuilt as it built them (``cli.live_settings``): from the command of its start
    record, else from ``fallback``. Returns (settings, symbol, where they came from)."""
    from . import cli
    parser = cli.build_parser()
    problems: List[str] = []
    for argv, source in ((command_argv(command or ""), "the window's start record"), (list(fallback), "the profile")):
        if not argv:
            continue
        try:
            args, _unknown = parser.parse_known_args(argv)
            if getattr(args, "command", None) != "live":
                problems.append(f"{source}: not a live command")
                continue
            settings, symbol = cli.live_settings(args)
            if problems:
                source += f" ({'; '.join(problems)})"
            return settings, symbol, source
        except SystemExit as exc:                  # argparse on an older command line, a profile that is gone
            problems.append(f"{source}: {exc}")
    raise RuntimeError("the window's settings could not be rebuilt: " + ("; ".join(problems) or "no command"))


def _flatten(doc: Any, prefix: str = "") -> Dict[str, Any]:
    if isinstance(doc, dict):
        out: Dict[str, Any] = {}
        for k, v in doc.items():
            out.update(_flatten(v, f"{prefix}{k}."))
        return out
    return {prefix[:-1]: doc}


def settings_diff(live_doc: Dict[str, Any], ours: Dict[str, Any], limit: int = 12) -> List[str]:
    """The settings that differ between a window's start record and this check (keys as section.name)."""
    a = _flatten(json.loads(json.dumps(live_doc, default=str)))
    b = _flatten(json.loads(json.dumps(ours, default=str)))
    out = [f"{key}: window {a.get(key, '(absent)')!r}, here {b.get(key, '(absent)')!r}"
           for key in sorted(set(a) | set(b)) if a.get(key, "(absent)") != b.get(key, "(absent)")]
    return out[:limit] + ([f"... and {len(out) - limit} more"] if len(out) > limit else [])


# ------------------------------------------------------------------ candles and news

def export_candles(broker, symbol: str, directory, now: pd.Timestamp, counts: Optional[Dict[Timeframe, int]] = None,
                   failures: Optional[Dict[Timeframe, str]] = None) -> Dict[Timeframe, Any]:
    """The terminal's closed candles of ``symbol`` per timeframe (the forming one left out), saved as ``<SYMBOL>_<TF>.csv``
    in ``directory`` (a later look reruns the week on exactly these with ``--data-dir``). A timeframe the terminal does
    not give goes into ``failures`` (the window went without it too); without the lowest one nothing can run."""
    from .data.tv_cache import save_series
    counts = counts or EXPORT_COUNTS
    out: Dict[Timeframe, Any] = {}
    for tf, count in counts.items():
        try:
            series = broker.get_candles(symbol, tf, count).closed_as_of(now)
        except Exception as exc:
            if tf == min(counts):
                raise
            if failures is not None:
                failures[tf] = str(exc)
            continue
        if len(series):
            save_series(series, directory, symbol, merge=False)
            out[tf] = series
    return out


def update_news_archive(journal_dir, archive) -> int:
    """Keep the ForexFactory weeks the windows saved next to the journal (``forexfactory_thisweek.csv``, ``..nextweek``):
    they are overwritten every week, so a check of last week on a Monday still finds them here. Returns the events kept."""
    from .data.calendar import load_events, save_events
    events = load_events(archive)
    fresh = [e for week in ("thisweek", "nextweek") for e in load_events(Path(journal_dir) / f"forexfactory_{week}.csv")]
    if fresh:
        save_events(events + fresh, archive)
        events = load_events(archive)
    return len(events)


def news_calendar(settings, journal_dir, archive=None) -> Tuple[Any, List[str]]:
    """The window's news calendar: the profile's CSV and the ForexFactory weeks it read (next to the journal, and the
    archive this check keeps of them). Returns (calendar or None, the sources with their event counts)."""
    n = settings.news
    if not n.enabled:
        return None, ["the profile's news blackout is off"]
    from .data.calendar import NewsCalendar, load_events
    calendar = NewsCalendar(load_events(n.calendar_csv), n.before_minutes, n.after_minutes, n.min_importance)
    sources = [f"{n.calendar_csv} ({len(calendar.events)})"]
    if n.forexfactory and journal_dir is not None:
        paths = [Path(journal_dir) / f"forexfactory_{w}.csv" for w in ("thisweek", "nextweek")] + ([Path(archive)] if archive else [])
        for path in paths:
            events = load_events(path)
            if events:
                calendar.add(events)
                sources.append(f"{path.name} ({len(events)})")
    return calendar, sources


# ------------------------------------------------------------------ the live side

@dataclass
class LiveSignal:
    """A setup the window journaled and what became of it."""
    sid: str
    time: pd.Timestamp
    direction: str
    poi_tf: str
    confirmation: str
    entry: float
    stop: float
    take_profit: float
    rr: float
    kind: str = "no action"            # trade | limit unfilled | limit resting | refused | no trade | no action
    outcome: str = "setup only (no order and no refusal in the journal)"
    limit: Optional[float] = None
    fill: Optional[float] = None
    position: str = ""
    exit_reason: str = ""
    r: Optional[float] = None


def _text(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)


def _num(value) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if pd.isna(f) else f


def live_side(journal: pd.DataFrame, symbol: str, start: pd.Timestamp, end: pd.Timestamp) -> Dict[str, LiveSignal]:
    """Every setup the window journaled in [start, end) (``setup`` and ``stale`` rows) with its fate: the refusal, the limit
    (linked by the order id the ``limit_placed`` note names), the fill and the close (linked by the position id the fill's
    note names)."""
    if journal is None or not len(journal):
        return {}
    rows = journal[journal["symbol"].astype(str).str.upper() == symbol.upper()].sort_values("time", kind="stable")
    rows = rows[rows["time"] >= start]
    out: Dict[str, LiveSignal] = {}
    for _, r in rows[rows["event"].isin(["setup", "stale"]) & (rows["time"] < end)].iterrows():
        sid = _text(r["id"])
        if not sid or sid in out:
            continue                                   # a restart may journal a setup again: its first sighting counts
        out[sid] = LiveSignal(sid, r["time"], _text(r.get("direction")), _text(r.get("poi_tf")), _text(r.get("confirmation")),
                              _num(r.get("entry")), _num(r.get("stop")), _num(r.get("take_profit")), _num(r.get("rr")))
        if r["event"] == "stale":
            out[sid].kind, out[sid].outcome = "no trade", "ignored: stale data" + (f" ({_text(r.get('note'))})" if _text(r.get("note")) else "")
    # the links first, over every row: a close is journaled at its deal's time, which can come before the scan that
    # journaled the fill (a trade that filled and closed between two scans)
    orders: Dict[str, str] = {}                        # limit order id -> setup id
    positions: Dict[str, str] = {}                     # position id -> setup id
    for _, r in rows.iterrows():
        m = SETUP_RE.search(_text(r.get("note")))
        if m and r["event"] == "limit_placed":
            orders[_text(r["id"])] = m.group(1)
        elif m and r["event"] in ("filled", "submitted"):
            positions[_text(r["id"])] = m.group(1)
    for _, r in rows.iterrows():
        ev, rid = r["event"], _text(r["id"])
        if ev in ("not_executed", "deferred", "expired", "skipped"):
            sig = out.get(rid)
        elif ev in ("limit_placed", "limit_cancelled", "limit_gone"):
            sig = out.get(orders.get(rid, ""))
        elif ev in ("filled", "submitted", "did_not_fill", "closed"):
            sig = out.get(positions.get(rid, ""))
        else:
            sig = None
        if sig is None or sig.kind == "no trade":
            continue
        reason, note = _text(r.get("reason")), _text(r.get("note"))
        if ev == "not_executed":
            sig.kind, sig.outcome = "refused", f"refused: {reason}"
        elif ev == "deferred" and sig.kind == "no action":
            sig.kind, sig.outcome = "refused", "deferred: the account lock was busy"
        elif ev == "expired":
            sig.kind, sig.outcome = "refused", f"expired ({note or reason})"
        elif ev == "skipped":
            sig.kind, sig.outcome = "refused", "skipped at the approval"
        elif ev == "limit_placed":
            sig.limit = _num(r.get("entry"))
            if sig.kind != "trade":
                sig.kind, sig.outcome = "limit resting", f"limit @ {_fmt(sig.limit)} still resting"
        elif ev == "limit_cancelled" and sig.kind != "trade":
            sig.kind, sig.outcome = "limit unfilled", f"limit @ {_fmt(sig.limit)} cancelled: {reason}"
        elif ev == "limit_gone" and sig.kind != "trade":
            sig.kind, sig.outcome = "limit unfilled", f"limit @ {_fmt(sig.limit)} gone from the server, not filled"
        elif ev in ("filled", "submitted"):
            sig.kind, sig.fill, sig.position = "trade", _num(r.get("entry")), rid
        elif ev == "did_not_fill" and not sig.exit_reason:
            sig.kind, sig.outcome = "refused", "the order did not fill"
        elif ev == "closed":
            sig.kind, sig.exit_reason, sig.r = "trade", reason, _num(r.get("r"))
            if sig.fill is None:
                sig.fill = _num(r.get("entry"))
    for sig in out.values():
        if sig.kind == "trade":
            how = f"{'limit ' if sig.limit is not None else ''}filled @ {_fmt(sig.fill)}"
            sig.outcome = f"{how}, {_exit_kind(sig.exit_reason, sig.r)} {_r(sig.r)}" if sig.exit_reason else f"{how}, open"
    return out


# ------------------------------------------------------------------ the backtest side

def warm_start(data, settings, wanted: pd.Timestamp) -> pd.Timestamp:
    """The backtest's first step: ``wanted``, or later where an intraday timeframe up to 1H holds too few candles before it
    to fill the engine's lookback (the export's 5000 5m candles reach back about three weeks; the window's views were
    full). The higher timeframes' exports reach years back: a shortage there is the server's history, the window's too."""
    s = settings.structure
    first = pd.Timestamp(wanted)
    for tf, series in data.series.items():
        need = int(s.lookback_by_timeframe.get(tf, s.lookback))
        if tf <= Timeframe.H_1 and len(series) >= need:
            first = max(first, tf.close_time(series.timestamps.iloc[need - 1]))
    return first


def backtest_week(settings, data, symbol: str, start: pd.Timestamp, end: pd.Timestamp, run_start: pd.Timestamp,
                  run_end: pd.Timestamp, calendar=None):
    """The backtester from ``run_start`` (the warm-up) to ``run_end`` on the window's settings, its candles taken as bid
    quotes (MT5 bars are bids): the result, the signals in [start, end) by setup id and their trades by setup id."""
    from .backtest.runner import Backtester
    from .cli import _forecaster
    from .strategy.engine import StrategyEngine
    engine = StrategyEngine(settings, _forecaster(settings), calendar=calendar)
    result = Backtester(settings, data, symbol, engine=engine, start=run_start, end=run_end, quote_basis="bid").run()
    signals = {s["sid"]: s for s in result.signal_log if start <= pd.Timestamp(s["at"]) < end}
    trades = {t.meta.get("sid"): t for t in result.trades if t.meta.get("sid") in signals}
    return result, signals, trades


def _bt_kind(log: Dict[str, Any], trade) -> Tuple[str, str]:
    o = str(log.get("outcome") or "")
    limit = log.get("limit")
    if trade is not None:
        how = f"{'limit ' if o == 'limit filled' else ''}filled @ {_fmt(trade.entry)}"
        if trade.reason == "end_of_data":
            return "trade", f"{how}, open"
        return "trade", f"{how}, {_exit_kind(trade.reason, trade.r)} {_r(trade.r)}"
    if o == "limit placed":
        return "limit resting", f"limit @ {_fmt(limit)} still resting"
    if o in ("limit: expired unfilled", "limit: the target traded first"):
        return "limit unfilled", f"limit @ {_fmt(limit)} {o[len('limit: '):]}"
    if o:
        return "refused", o
    return "no action", "no order"


# ------------------------------------------------------------------ the comparison

@dataclass
class ParityRow:
    symbol: str
    sid: str
    time: pd.Timestamp                 # the backtest's signal time, else the window's
    direction: str
    poi_tf: str
    confirmation: str
    verdict: str
    live: str = ""
    backtest: str = ""
    note: str = ""
    live_time: Optional[pd.Timestamp] = None
    bt_time: Optional[pd.Timestamp] = None
    live_r: Optional[float] = None
    bt_r: Optional[float] = None

    def as_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "sid": self.sid, "time_utc": self.time, "time_local": local(self.time),
                "direction": self.direction, "poi_tf": self.poi_tf, "confirmation": self.confirmation,
                "verdict": self.verdict, "live": self.live, "backtest": self.backtest, "note": self.note,
                "live_time_utc": self.live_time, "backtest_time_utc": self.bt_time, "live_r": self.live_r,
                "backtest_r": self.bt_r}


def _fmt(x) -> str:
    return "?" if x is None else f"{float(x):.6g}"


def _r(r) -> str:
    return "" if r is None else f"{float(r):+.2f}R"


def _exit_kind(reason: str, r: Optional[float]) -> str:
    reason = str(reason or "")
    if reason in ("", "end_of_data"):
        return "open"
    if reason == "breakeven" or (reason == "stop" and r is not None and abs(float(r)) < 0.15):
        return "breakeven"
    return {"take_profit": "target"}.get(reason, reason)


def _live_refusal_hint(outcome: str) -> str:
    o = outcome.lower()
    if "spread" in o:
        return "the spread cap is a live-only rule"
    if "margin" in o:
        return "the account's margin is live only"
    if "lock" in o:
        return "the account lock (another window was trading) is live only"
    if "open" in o or "per market" in o or "trades" in o:
        return "the account's other markets count in the live guard; the backtest runs one market alone"
    if "price moved" in o:
        return "the live price at the scan differed from the candle's close"
    return ""


def _downtime_hint(rows_sym: pd.DataFrame, t: pd.Timestamp) -> str:
    """When the window's next journal row after ``t`` is a restart, it was probably not running at ``t``."""
    if rows_sym is None or not len(rows_sym):
        return "the window wrote nothing in the journal"
    after = rows_sym[rows_sym["time"] > t]
    before = rows_sym[rows_sym["time"] <= t]
    if not len(after):
        return f"the window wrote nothing after {local(before['time'].max()) if len(before) else 'it'}: probably not running"
    nxt = after.iloc[0]
    if nxt["event"] == "start":
        return f"probably down: the window's next journal row is its restart, {local(nxt['time'])}"
    if len(before) and before.iloc[-1]["event"] == "start" and t - before.iloc[-1]["time"] < pd.Timedelta(minutes=15):
        return f"the window had just started ({local(before.iloc[-1]['time'])})"
    return ""


def _restart_note(rows_sym: Optional[pd.DataFrame], t: pd.Timestamp, hours: float = 48.0) -> str:
    """The window's last (re)start within ``hours`` before ``t``: its zone and visit memory starts there, the backtest's
    at its warm-up."""
    if rows_sym is None or not len(rows_sym):
        return ""
    starts = rows_sym[(rows_sym["event"] == "start") & (rows_sym["time"] <= t) & (rows_sym["time"] > t - pd.Timedelta(hours=hours))]
    if not len(starts):
        return ""
    return f"the window (re)started {local(starts['time'].iloc[-1])}: its zone and visit memory starts there"


def _twin(t: pd.Timestamp, direction: str, poi_tf: str, others: Dict[str, Any], minutes: int, label: str) -> str:
    """A signal of the other side on the same side and zone timeframe within ``minutes``: the same idea on another zone
    or confirmation candle."""
    best = None
    for sid, o in others.items():
        ot = pd.Timestamp(o["at"] if isinstance(o, dict) else o.time)
        od = o["direction"] if isinstance(o, dict) else o.direction
        otf = o["poi_tf"] if isinstance(o, dict) else o.poi_tf
        if od == direction and otf == poi_tf and abs(ot - t) <= pd.Timedelta(minutes=minutes):
            if best is None or abs(ot - t) < abs(best[1] - t):
                best = (sid, ot)
    if best is None:
        return ""
    return f"{label} {best[0]} at {local(best[1], '%H:%M')}: same side and zone timeframe, another zone or confirmation candle"


def _levels_note(live: LiveSignal, log: Dict[str, Any]) -> str:
    risk = abs(float(log["entry"]) - float(log["stop"])) or 1e-12
    parts = []
    for name, a, b in (("entry", live.entry, log["entry"]), ("stop", live.stop, log["stop"]), ("target", live.take_profit, log["take_profit"])):
        if a is not None and abs(float(a) - float(b)) / risk > 0.02:
            parts.append(f"{name} {float(a) - float(b):+.6g} ({(float(a) - float(b)) / risk:+.2f}R)")
    return ("plan differs: " + ", ".join(parts)) if parts else ""


def _fill_note(live: LiveSignal, log: Dict[str, Any], trade) -> str:
    if live.fill is None or trade is None:
        return ""
    risk = abs(float(log["entry"]) - float(log["stop"])) or 1e-12
    sign = 1.0 if str(log["direction"]).upper() == "LONG" else -1.0
    slip = sign * (float(live.fill) - float(trade.entry)) / risk
    return f"live filled {abs(slip):.2f}R {'worse' if slip > 0 else 'better'} than the backtest" if abs(slip) >= 0.05 else ""


def compare(symbol: str, live: Dict[str, LiveSignal], signals: Dict[str, Dict[str, Any]], trades: Dict[str, Any],
            rows_sym: Optional[pd.DataFrame] = None, near_minutes: int = 60) -> List[ParityRow]:
    """One row per setup id seen on either side, in time order, with the verdict and what explains a difference."""
    out: List[ParityRow] = []
    for sid in set(live) | set(signals):
        L, B, T = live.get(sid), signals.get(sid), trades.get(sid)
        if L is not None and B is not None:
            bk, bt_text = _bt_kind(B, T)
            notes = [n for n in (_levels_note(L, B), _fill_note(L, B, T)) if n]
            if L.kind == bk == "trade":
                lx = _exit_kind(L.exit_reason, L.r)
                bx = _exit_kind(T.reason, T.r) if T is not None else "open"
                verdict = "match" if lx == bx else "outcome differs"
                if verdict != "match" and "open" in (lx, bx):
                    notes.append("one side still holds the trade")
            elif L.kind == bk:
                verdict = "match"
            else:
                verdict = "outcome differs"
                hint = _live_refusal_hint(L.outcome) if L.kind == "refused" else ""
                if hint:
                    notes.append(hint)
                if bk == "refused" and "a limit entry is working" in bt_text:
                    notes.append("the backtest holds one limit at a time")
            if verdict != "match":
                notes.append(_restart_note(rows_sym, L.time))
            out.append(ParityRow(symbol, sid, pd.Timestamp(B["at"]), B["direction"], B["poi_tf"], B["confirmation"], verdict,
                                 L.outcome, bt_text, "; ".join(n for n in notes if n), L.time, pd.Timestamp(B["at"]), L.r,
                                 None if T is None or T.reason == "end_of_data" else float(T.r)))
        elif B is not None:
            t = pd.Timestamp(B["at"])
            _bk, bt_text = _bt_kind(B, T)
            down = _downtime_hint(rows_sym, t)
            notes = [n for n in (down, _twin(t, B["direction"], B["poi_tf"], live, near_minutes, "the window signalled"),
                                 "" if down else _restart_note(rows_sym, t)) if n]
            out.append(ParityRow(symbol, sid, t, B["direction"], B["poi_tf"], B["confirmation"], "backtest only", "",
                                 bt_text, "; ".join(notes), None, t, None,
                                 None if T is None or T.reason == "end_of_data" else float(T.r)))
        else:
            twin = _twin(L.time, L.direction, L.poi_tf, signals, near_minutes, "the backtest signalled")
            notes = [twin or "the backtest saw no such setup (other candles, or other zone or visit state)",
                     _restart_note(rows_sym, L.time)]
            out.append(ParityRow(symbol, sid, L.time, L.direction, L.poi_tf, L.confirmation, "live only", L.outcome, "",
                                 "; ".join(n for n in notes if n), L.time, None, L.r, None))
    return sorted(out, key=lambda r: (r.time, r.sid))


# ------------------------------------------------------------------ the run

@dataclass
class MarketParity:
    symbol: str
    settings_note: str = ""
    settings_diff: List[str] = field(default_factory=list)
    source: str = ""
    starts: List[str] = field(default_factory=list)
    news: str = ""
    candles: str = ""
    backtest: str = ""
    notes: List[str] = field(default_factory=list)
    rows: List[ParityRow] = field(default_factory=list)
    error: str = ""

    def count(self, verdict: str) -> int:
        return sum(1 for r in self.rows if r.verdict == verdict)

    @property
    def live_signals(self) -> int:
        return sum(1 for r in self.rows if r.live_time is not None)

    @property
    def bt_signals(self) -> int:
        return sum(1 for r in self.rows if r.bt_time is not None)

    @property
    def live_r(self) -> float:
        return float(sum(r.live_r for r in self.rows if r.live_r is not None))

    @property
    def bt_r(self) -> float:
        return float(sum(r.bt_r for r in self.rows if r.bt_r is not None))


@dataclass
class ParityReport:
    start: pd.Timestamp
    end: pd.Timestamp
    run_at: pd.Timestamp
    journal: str
    code: str = ""
    markets: List[MarketParity] = field(default_factory=list)
    markdown_path: Optional[Path] = None
    csv_path: Optional[Path] = None
    candles_dir: Optional[Path] = None

    @property
    def rows(self) -> List[ParityRow]:
        return [r for m in self.markets for r in m.rows]

    @property
    def matched(self) -> int:
        return sum(1 for r in self.rows if r.verdict == "match")

    @property
    def markets_checked(self) -> int:
        return sum(1 for m in self.markets if not m.error)


def _markets_arg(markets) -> Dict[str, Optional[str]]:
    """``EURUSD,XAUUSD=config/x.yaml`` (or a list of such) -> {symbol: profile or None}."""
    items = markets.split(",") if isinstance(markets, str) else list(markets or [])
    out: Dict[str, Optional[str]] = {}
    for item in items:
        item = str(item).strip()
        if not item:
            continue
        sym, _, profile = item.partition("=")
        out[sym.strip().upper()] = profile.strip() or None
    return out


def _names_arg(text: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for pair in str(text or "").split(","):
        if "=" in pair:
            sym, name = (x.strip() for x in pair.split("=", 1))
            out[sym.upper()] = name
    return out


def default_markets(journal: pd.DataFrame, records: Sequence[StartRecord]) -> List[str]:
    """The journal's markets that have a start record or a known profile, the live windows' order first."""
    seen = set(journal["symbol"].dropna().astype(str).str.upper()) if journal is not None and len(journal) else set()
    known = set(LIVE_PROFILES) | {r.symbol for r in records}
    found = seen & known
    return [s for s in LIVE_PROFILES if s in found] + sorted(found - set(LIVE_PROFILES))


def run_parity(journal_path, week: str = "auto", start=None, end=None, markets=None, data_dir=None, out_dir=None,
               warmup_days: float = 7.0, account_size: Optional[float] = None, product: Optional[str] = None,
               mt5_names: Optional[str] = None, connect: Optional[Callable] = None, now: Optional[pd.Timestamp] = None,
               near_minutes: int = 60, log: Callable[[str], None] = print) -> ParityReport:
    """The week's journal against a backtest of the same week, per market; writes the report next to the journal.

    ``data_dir``: read ``<SYMBOL>_<TF>.csv`` candles there instead of the terminal; ``connect``: makes the connected broker
    from a ``Settings`` holding every market's contract (default: ``MT5Broker``, attached to the running terminal)."""
    from .backtest.provenance import code_snapshot, settings_fingerprint
    from .config import Settings
    from .data.calendar import currencies_of
    from .data.resample import MultiTimeframeData
    from .data.tv_cache import load_all
    from .forward import read_journal

    now = pd.Timestamp(now) if now is not None else utc_now()
    journal_path = Path(journal_path)
    journal_dir = journal_path.parent
    journal = read_journal(journal_path) if journal_path.exists() else pd.DataFrame(columns=["time", "symbol", "event", "id", "note"])
    if start is not None:
        w_start, w_end = pd.Timestamp(start), min(pd.Timestamp(end) if end is not None else now, now)
    else:
        w_start, w_end = week_window(week, now)
    records = start_records(journal_dir)
    wanted = _markets_arg(markets) if markets else {s: None for s in default_markets(journal, records)}
    names = _names_arg(mt5_names)
    try:
        code = code_snapshot()
        code_text = f"{str(code.get('commit') or '?')[:7]}{' + local changes' if code.get('dirty') else ''}"
    except Exception:
        code_text = "?"
    out_dir = Path(out_dir) if out_dir else journal_dir / "parity"
    label = f"{w_start:%Y-%m-%d}"
    report = ParityReport(w_start, w_end, now, str(journal_path), code_text)
    log(f"parity: {journal_path}, {w_start:%Y-%m-%d %H:%M} to {w_end:%Y-%m-%d %H:%M} UTC, markets {', '.join(wanted) or 'none'}")

    # 1. each window's settings, from its start record (the server's contract numbers included)
    plans: List[Dict[str, Any]] = []
    for sym, profile in wanted.items():
        mp = MarketParity(sym)
        report.markets.append(mp)
        recs = [r for r in records if r.symbol == sym]
        rec = record_in_effect(recs, w_end)
        mp.starts = [f"{local(r.started)} (code {r.commit[:7] or '?'}{' + local changes' if r.dirty else ''}, settings "
                     f"{r.settings_sha[:12] or '?'})" for r in recs if w_start <= r.started < w_end]
        use_rec = rec if not profile else None
        profile = profile or LIVE_PROFILES.get(sym)
        if use_rec is None and not profile:
            mp.error = f"no start record of its window next to the journal and no known profile (--markets {sym}=<profile>)"
            log(f"  {sym}: {mp.error}")
            continue
        fallback = fallback_argv(sym, profile, account_size, product, names.get(sym), journal_path) if profile else []
        try:
            settings, _sym, source = window_settings(use_rec.command if use_rec is not None else None, fallback)
        except RuntimeError as exc:
            mp.error = str(exc)
            log(f"  {sym}: {exc}")
            continue
        spec = settings.symbol(sym)
        recorded = ((use_rec.settings.get("symbols") or {}).get(sym) or {}) if use_rec is not None else {}
        for key in SERVER_SPEC_FIELDS:
            if recorded.get(key) is not None:
                setattr(spec, key, float(recorded[key]))
        if source.startswith("the window's start record"):
            mp.source = f"the window's start record of {local(use_rec.started)}" + source[len("the window's start record"):]
        else:
            mp.source, use_rec = profile + source[len("the profile"):], None
        plans.append({"mp": mp, "settings": settings, "rec": use_rec, "data": None})

    # 2. the candles: the terminal's own, or saved ones
    candles_dir = out_dir / f"candles_{label}"
    if plans and data_dir is None:
        holder = Settings()
        holder.mt5 = plans[0]["settings"].mt5             # the windows' terminal settings (MT5_PATH and the rest)
        for p in plans:
            holder.symbols[p["mp"].symbol] = p["settings"].symbol(p["mp"].symbol)     # the same objects: aligned in place
        if connect is None:
            from .execution.mt5 import MT5Broker
            connect = MT5Broker
        broker = connect(holder)
        try:
            for p in plans:
                sym = p["mp"].symbol
                try:
                    if p["rec"] is None and callable(getattr(broker, "align_spec", None)):
                        broker.align_spec(sym)                 # no start record: the server's contract, as a window reads it
                    failed: Dict[Timeframe, str] = {}
                    p["data"] = export_candles(broker, sym, candles_dir, now, failures=failed)
                    p["mp"].notes += [f"no {tf.label} candles from the terminal ({err})" for tf, err in failed.items()]
                except Exception as exc:
                    p["mp"].error = f"no candles from the terminal: {exc}"
                    log(f"  {sym}: {p['mp'].error}")
        finally:
            try:
                broker.disconnect()
            except Exception:
                pass
        report.candles_dir = candles_dir
    else:
        for p in plans:
            sym = p["mp"].symbol
            alt = p["settings"].symbol(sym).tradingview_symbol
            found = load_all(data_dir, sym) or (load_all(data_dir, alt) if alt else {})     # the cache's OANDA_EURUSD too
            if found:
                p["data"] = found
            else:
                p["mp"].error = f"no candles for {p['mp'].symbol} in {data_dir}"

    # 3. per market: the settings against the window's, the news, the backtest, the comparison
    archive = out_dir / "news_seen.csv"
    try:
        update_news_archive(journal_dir, archive)
    except Exception as exc:                            # the archive is a convenience, never a reason to stop
        log(f"  news archive not updated ({exc})")
    for p in plans:
        mp, settings, rec = p["mp"], p["settings"], p["rec"]
        if mp.error or not p["data"]:
            continue
        sym = mp.symbol
        resolved, sha = settings_fingerprint(settings)
        if rec is not None and rec.settings_sha and sha == rec.settings_sha:
            mp.settings_note = f"identical to the window's (settings {sha[:12]})"
        elif rec is not None:
            mp.settings_note = f"NOT identical to the window's (window {rec.settings_sha[:12] or '?'}, this check {sha[:12]})"
            mp.settings_diff = settings_diff(rec.settings, resolved)
        else:
            mp.settings_note = f"the profile's (settings {sha[:12]}): the window left no start record next to the journal"
        if rec is not None and any(r.settings_sha and r.settings_sha != rec.settings_sha for r in records
                                   if r.symbol == sym and w_start <= r.started < w_end):
            mp.notes.append("the window ran other settings for part of the week (see its starts): differences before the "
                            "last restart can come from that")
        calendar, sources = news_calendar(settings, journal_dir, archive)
        if calendar is not None:
            wanted_ccy = currencies_of(sym)
            n_week = sum(1 for e in calendar.events if w_start <= e.time < w_end and e.currency in wanted_ccy)
            mp.news = f"{n_week} high-impact events for {', '.join(sorted(wanted_ccy))} in the week ({', '.join(sources)})"
            if n_week == 0:
                mp.notes.append("no news events in the week: the backtest applied no news blackout (the windows read the "
                                "ForexFactory week live; it may be missing here)")
        else:
            mp.news = sources[0]
        data = MultiTimeframeData(p["data"])
        lowest = data.lowest
        data_end = min(lowest.timeframe.close_time(lowest.timestamps.iloc[-1]), now)
        m_end = min(w_end, data_end)
        run_start = warm_start(data, settings, w_start - pd.Timedelta(days=float(warmup_days)))
        mp.candles = ", ".join(f"{tf.label} {len(s)} from {s.timestamps.iloc[0]:%d %b %Y}" for tf, s in sorted(data.series.items()))
        if run_start > w_start - pd.Timedelta(days=1):
            mp.notes.append(f"short warm-up: the backtest starts {local(run_start)}; zone and visit memory before it is missing")
        if m_end < w_end:
            mp.notes.append(f"the candles end {local(data_end)}: the comparison stops there")
        log(f"  {sym}: backtest {run_start:%Y-%m-%d %H:%M} to {data_end:%Y-%m-%d %H:%M} UTC ...")
        try:
            result, signals, trades = backtest_week(settings, data, sym, w_start, m_end, run_start, data_end, calendar)
        except Exception as exc:
            mp.error = f"backtest failed: {exc}"
            log(f"  {sym}: {mp.error}")
            continue
        mp.backtest = (f"{local(run_start)} to {local(data_end)}: {result.steps} steps, {_n(result.signals, 'signal')} "
                       f"({len(signals)} in the week), {_n(len(result.trades), 'trade')}")
        live = live_side(journal, sym, w_start, m_end)
        rows_sym = journal[journal["symbol"].astype(str).str.upper() == sym].sort_values("time", kind="stable") if len(journal) else journal
        mp.rows = compare(sym, live, signals, trades, rows_sym, near_minutes)
        log(f"  {sym}: {len(live)} live, {len(signals)} backtest signals; " +
            ", ".join(f"{mp.count(v)} {v}" for v in VERDICTS if mp.count(v)) if mp.rows else f"  {sym}: no signals on either side")
    report.markdown_path, report.csv_path = write_report(report, out_dir, label)
    return report


# ------------------------------------------------------------------ the report

def _sentence(text: str) -> str:
    text = str(text).strip()
    return (text[:1].upper() + text[1:] + ("" if text.endswith(".") else ".")) if text else ""


def _n(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def _md(text: Any) -> str:
    return str(text if text is not None else "").replace("|", "/").replace("\n", " ")


def write_report(report: ParityReport, out_dir, label: str) -> Tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path, csv_path = out_dir / f"parity_{label}.md", out_dir / f"parity_{label}.csv"
    pd.DataFrame([r.as_dict() for r in report.rows], columns=list(ParityRow("", "", pd.Timestamp(0), "", "", "", "").as_dict())
                 ).to_csv(csv_path, index=False)
    md_path.write_text(markdown(report), encoding="utf-8")
    return md_path, csv_path


def headline(report: ParityReport) -> str:
    rows = report.rows
    if not rows:
        return "no signals in the week, live or in the backtest"
    return f"{report.matched} of {len(rows)} signals match ({report.matched / len(rows):.0%})"


def markdown(report: ParityReport) -> str:
    lines = [f"# Parity check, week of {report.start:%d %b %Y}", "",
             f"The live journal `{report.journal}` against a backtest of the same week on the terminal's candles, each "
             f"market with its window's own settings. Times are Amsterdam time.", "",
             f"- Window: {local(report.start)} to {local(report.end)}",
             f"- Run: {local(report.run_at)}, code {report.code}", ""]
    rows = report.rows
    lines += [f"**{headline(report)}.**" + (f" R of the week's signals: live {sum(m.live_r for m in report.markets):+.2f}, "
                                            f"backtest {sum(m.bt_r for m in report.markets):+.2f} (closed trades)." if rows else ""), "",
              "| Market | Live signals | Backtest signals | Match | Outcome differs | Backtest only | Live only | R live | R backtest |",
              "|---|---|---|---|---|---|---|---|---|"]
    for m in report.markets:
        if m.error:
            lines.append(f"| {m.symbol} | not checked: {_md(m.error)} |  |  |  |  |  |  |  |")
            continue
        lines.append(f"| {m.symbol} | {m.live_signals} | {m.bt_signals} | {m.count('match')} | {m.count('outcome differs')} | "
                     f"{m.count('backtest only')} | {m.count('live only')} | {m.live_r:+.2f} | {m.bt_r:+.2f} |")
    diffs = [r for r in rows if r.verdict != "match"]
    if diffs:
        lines += ["", "## What differs", ""]
        for r in diffs:
            lines.append(f"- {r.symbol} {local(r.time)} {r.direction} {r.poi_tf} ({r.sid}): **{r.verdict}**. "
                         f"Live: {r.live or 'no signal'}. Backtest: {r.backtest or 'no signal'}." + (f" {_sentence(r.note)}" if r.note else ""))
    for m in report.markets:
        lines += ["", f"## {m.symbol}", ""]
        if m.error:
            lines += [f"Not checked: {m.error}"]
            continue
        lines += [f"- Settings: {m.settings_note}; from {m.source}"]
        lines += [f"  - {d}" for d in m.settings_diff]
        lines += [f"- Window starts in the week: {', '.join(m.starts) if m.starts else 'none (it ran from before the week)'}",
                  f"- Backtest: {m.backtest}", f"- Candles: {m.candles}", f"- News: {m.news}"]
        lines += [f"- Note: {n}" for n in m.notes]
        if not m.rows:
            lines += ["", "No signals on either side."]
            continue
        lines += ["", "| Time | Id | Side | Zone | Confirmation | Live | Backtest | Verdict | Note |", "|---|---|---|---|---|---|---|---|---|"]
        for r in m.rows:
            when = local(r.time)
            if r.live_time is not None and r.bt_time is not None and abs(r.live_time - r.bt_time) >= pd.Timedelta(minutes=2):
                when += f" (live {local(r.live_time, '%H:%M')})"
            lines.append(f"| {when} | {r.sid} | {r.direction} | {r.poi_tf} | {_md(r.confirmation)} | {_md(r.live) or '-'} | "
                         f"{_md(r.backtest) or '-'} | {r.verdict} | {_md(r.note)} |")
    rerun = (f"python -m kronos_trader parity --journal {report.journal} --week {report.start:%Y-%m-%d} --data-dir "
             f"{report.candles_dir.as_posix()}") if report.candles_dir is not None else ""
    lines += ["", "## How to read this", "",
              "- **match**: both sides saw the setup (same id: the same zone and confirmation candle) and did the same with "
              "it: a trade with the same exit, a limit that did not fill, a refusal.",
              "- **outcome differs**: both saw it, the result differs. A live refusal by the spread cap, the margin or the "
              "account's other markets is a live-only rule; another exit is a fill or price difference worth a look.",
              "- **backtest only**: the backtest signalled and the window did not. Most often the window was not running "
              "(its next journal row is a restart); otherwise its candles or its zone memory differed: worth a look.",
              "- **live only**: the window signalled and the backtest did not: the window saw other candles (a gap or a "
              "late bar) or other state. Worth a look.",
              "- R is price R without costs on both sides (the journal's close and the backtest's), the backtest starting "
              "flat each week at the account size: R compares, money does not."]
    if rerun:
        lines += ["", f"Rerun this week on the same candles: `{rerun}`"]
    return "\n".join(lines) + "\n"


def summary_lines(report: ParityReport) -> List[str]:
    """The console summary (ASCII: a Windows console reading a pipe may not take other characters)."""
    out = [f"parity {report.start:%Y-%m-%d} to {report.end:%Y-%m-%d %H:%M} UTC: {headline(report)}"]
    for m in report.markets:
        if m.error:
            out.append(f"  {m.symbol}: not checked ({m.error})")
        else:
            out.append(f"  {m.symbol}: live {m.live_signals}, backtest {m.bt_signals}, " +
                       ", ".join(f"{m.count(v)} {v}" for v in VERDICTS) + f"; R live {m.live_r:+.2f}, backtest {m.bt_r:+.2f}")
    for r in report.rows:
        if r.verdict != "match":
            out.append(f"  - {r.symbol} {local(r.time)} {r.direction} {r.poi_tf} {r.sid}: {r.verdict}"
                       f" (live: {r.live or 'none'}; backtest: {r.backtest or 'none'})" + (f" - {r.note}" if r.note else ""))
    return [line.encode("ascii", "replace").decode("ascii") for line in out]


def telegram_text(report: ParityReport, limit: int = 6) -> str:
    """The week in a few lines for Telegram (HTML): the headline, R on both sides, the differences, the report's path."""
    e = html.escape
    lines = [f"🔁 <b>Parity week of {report.start:%d %b}</b>: {e(headline(report))}"]
    if report.rows:
        lines.append(f"R live {sum(m.live_r for m in report.markets):+.2f} · backtest {sum(m.bt_r for m in report.markets):+.2f}")
    diffs = [r for r in report.rows if r.verdict != "match"]
    for r in diffs[:limit]:
        what = {"backtest only": f"backtest only ({r.backtest})", "live only": f"live only ({r.live})"}.get(
            r.verdict, f"live {r.live}; backtest {r.backtest}")
        note = r.note.split("; ")[0] if r.note else ""
        lines.append(f"• {e(r.symbol)} {e(local(r.time, '%a %H:%M'))} {e(r.direction)} {e(r.poi_tf)}: {e(what)}"
                     + (f" - {e(note)}" if note else ""))
    if len(diffs) > limit:
        lines.append(f"… and {len(diffs) - limit} more")
    for m in report.markets:
        if m.error:
            lines.append(f"⚠️ {e(m.symbol)} not checked: {e(m.error)}")
    if report.markdown_path is not None:
        lines.append(f"Report: {e(str(report.markdown_path))}")
    return "\n".join(lines)
