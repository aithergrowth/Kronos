"""Live loop: fetch candles -> analyse -> Telegram -> (approve) -> execute -> report.

Candles come from a live source (the broker, or a dedicated feed such as OANDA)
with the TradingView CSV cache as fallback; the cache alone is enough for a
dry run but is only as fresh as its last import.  Analysis runs on closed
candles only.  When the freshest candle of a timeframe closed more than
``live.max_data_age_bars`` candles ago the loop still analyses and manages
positions but opens no new setups (``live.require_fresh_data``).

Execution is human-in-the-loop by default: a valid setup is sent to Telegram
with Approve / Skip buttons and the order is only placed after a tap, as long
as the request has not expired and the risk guard still allows it.  An order
is reported as filled only when the broker confirmed the fill; a submitted but
unconfirmed order is reported as such and confirmed (or dropped) on a later
poll.  Fills, break-even moves and closes (stop / target / break-even) are
reported with P&L.  ``dry_run=True`` never sends an order.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis, Bias, Direction, ForecastSummary, TradeMode, TradeSetup
from .data.tv_cache import load_all
from .execution.base import Broker, Position
from .execution.risk_guard import RiskGuard
from .journal import Journal
from .notify.telegram import TelegramNotifier
from .strategy.engine import StrategyEngine, in_session
from .strategy.exits import breakeven_reached


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


def short_id_for(key) -> str:
    return hashlib.sha1(str(key).encode("utf-8")).hexdigest()[:8]


def _age_text(age: pd.Timedelta) -> str:
    minutes = int(age.total_seconds() // 60)
    if minutes < 90:
        return f"{minutes}m"
    if minutes < 48 * 60:
        return f"{minutes // 60}h"
    return f"{minutes // (24 * 60)}d"


@dataclass
class PendingSetup:
    short_id: str
    key: Tuple
    setup: TradeSetup
    forecast: Optional[ForecastSummary]
    created_at: pd.Timestamp
    expires_at: pd.Timestamp


@dataclass
class FeedReport:
    """Where each timeframe of the last fetch came from, and what failed."""
    sources: Dict[Timeframe, str] = field(default_factory=dict)       # "feed" | "broker" | "cache"
    failures: Dict[Timeframe, str] = field(default_factory=dict)
    skipped: List[Timeframe] = field(default_factory=list)            # failed and nothing cached

    def describe(self) -> str:
        by_source: Dict[str, List[str]] = {}
        for tf in sorted(self.sources):
            by_source.setdefault(self.sources[tf], []).append(tf.label)
        parts = [f"{', '.join(tfs)} {src}" for src, tfs in by_source.items()]
        if self.skipped:
            parts.append("missing " + ", ".join(tf.label for tf in sorted(self.skipped)))
        return "; ".join(parts) or "no data"


def build_fetch(
    settings: Settings,
    symbol: str,
    cache_dir: Optional[str] = None,
    broker: Optional[Broker] = None,
    broker_timeframes: Optional[Iterable[Timeframe]] = None,
    bar_counts: Optional[Dict[Timeframe, int]] = None,
    feed=None,
    retry_after_seconds: Optional[int] = None,
) -> Callable[[], Dict[Timeframe, CandleSeries]]:
    """Compose a ``fetch`` for ``LiveRunner``: live bars (``feed`` or ``broker``) over the cached TradingView bars.

    When the live source fails for a timeframe the cached candles are kept (or
    the timeframe is skipped when nothing is cached); when it fails for every
    timeframe it is left alone for ``retry_after_seconds`` so a broker without
    market data permissions is not hammered every poll.  The outcome of the
    last call is on ``fetch.report`` (a ``FeedReport``).
    """
    symbol = symbol.upper()
    spec = settings.symbols.get(symbol)
    tv_symbol = spec.tradingview_symbol if spec and spec.tradingview_symbol else symbol
    tfs = [Timeframe.parse(tf) for tf in (broker_timeframes if broker_timeframes is not None else settings.live.broker_timeframes)]
    counts = dict(settings.live.broker_bar_counts)
    counts.update(bar_counts or {})
    source = feed if feed is not None else broker
    source_name = "feed" if feed is not None else "broker"
    retry_after = settings.live.feed_retry_seconds if retry_after_seconds is None else retry_after_seconds
    state = {"down_until": None}

    def fetch() -> Dict[Timeframe, CandleSeries]:
        report = FeedReport()
        views: Dict[Timeframe, CandleSeries] = {}
        if cache_dir:
            cached = load_all(cache_dir, tv_symbol) or load_all(cache_dir, symbol)
            views.update(cached)
            report.sources.update({tf: "cache" for tf in cached})
        live_allowed = state["down_until"] is None or time.monotonic() >= state["down_until"]
        if source is not None and tfs and live_allowed:
            for tf in tfs:
                try:
                    views[tf] = source.get_candles(symbol, tf, counts.get(tf, 500))
                    report.sources[tf] = source_name
                except Exception as exc:
                    report.failures[tf] = str(exc)
                    if tf not in views:
                        report.skipped.append(tf)
            if len(report.failures) == len(tfs):
                state["down_until"] = time.monotonic() + retry_after
                first = next(iter(report.failures.values()))
                print(f"[live] {symbol}: no live bars for any timeframe ({first}); using the cache, next try in {retry_after // 60} min")
            else:
                state["down_until"] = None
                for tf, err in report.failures.items():
                    what = "using the cached candles" if tf in views else "timeframe skipped"
                    print(f"[live] {symbol} {tf.label}: live bars failed ({err}); {what}")
        if not views:
            raise RuntimeError(f"no candles for {symbol}: cache {cache_dir!r} empty and no live feed")
        fetch.report = report
        return views

    fetch.report = FeedReport()
    return fetch


class AccountLock:
    """A lock file next to the journal, shared by the windows of one account. It waits up to ``timeout`` seconds; when it
    could not take the lock, ``held`` stays False and the caller defers the entry (``LiveRunner.execute``): trading on
    without it would let two windows pass the account's risk checks at once. A file older than ``stale`` seconds (left by
    a killed window) is removed, so a stuck file costs at most a minute of deferral, never the trading itself."""

    def __init__(self, path: Optional[Path], timeout: float = 10.0, stale: float = 60.0):
        self.path, self.timeout, self.stale, self.held = path, timeout, stale, False

    def __enter__(self) -> "AccountLock":
        if self.path is None:
            return self
        deadline = time.time() + self.timeout
        while True:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > self.stale:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                except OSError:             # being deleted by its holder (Windows: delete pending), or a scanner has it
                    pass
                if time.time() >= deadline:
                    return self
                time.sleep(0.05)
            except OSError:                 # Windows: PermissionError while the holder deletes the file; try until the deadline
                if time.time() >= deadline:
                    return self
                time.sleep(0.05)

    def __exit__(self, *exc) -> bool:
        if self.held:
            try:
                self.path.unlink()
            except OSError:                 # gone already, or held by a virus scanner / OneDrive (WinError 32): stale in 60 s
                pass
            self.held = False
        return False


WINDOW_TAKEN = 3                            # the exit code of a window whose market runs already: the start scripts close it


def pid_alive(pid: int) -> bool:
    """Whether process ``pid`` runs. Windows asks the process table: ``os.kill(pid, 0)`` would end the process there."""
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.OpenProcess.argtypes = (ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong)
        kernel32.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong))
        kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
        handle = kernel32.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:                 # runs, under another user
        return True
    except OSError:
        return False
    return True


class WindowLock:
    """One window per market and journal folder: ``window_<name>.lock`` next to the journal, locked by the operating
    system while the window runs and let go however it ends (closed, crashed, killed), so it is never left behind. A
    second window for the market finds it taken and stops at the start: start_ftmo.bat run again, or a market started by
    hand beside the script's, would otherwise run it twice, sharing the limit file and the heartbeat and sending every
    message twice. A window on code from before the lock (6 October) holds no lock; its heartbeat, written in the last
    ``fresh_minutes`` by a process that still runs, counts as taken too."""

    LOCK_AT = 4096                          # Windows locks this byte, past the pid at the start, so the pid stays readable

    def __init__(self, folder, name: str, fresh_minutes: float = 10.0,
                 clock: Optional[Callable[[], pd.Timestamp]] = None):
        self.path = Path(folder) / f"window_{name}.lock"
        self.heartbeat = Path(folder) / f"heartbeat_{name}.json"
        self.fresh_minutes, self.clock = fresh_minutes, clock or utc_now
        self.fd: Optional[int] = None

    def acquire(self) -> Optional[str]:
        """Take the market: None when this window may run it, else which process runs it already."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path), os.O_RDWR | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
        try:
            if os.name == "nt":
                import msvcrt
                os.lseek(fd, self.LOCK_AT, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return f"process {self._pid_in_file() or '?'}"
        older = self._older_window()
        if older:
            os.close(fd)
            return older
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, f"{os.getpid():<12}".encode())
        self.fd = fd
        return None

    def release(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _pid_in_file(self) -> Optional[int]:
        try:
            return int(self.path.read_bytes()[:12].strip() or 0) or None
        except (OSError, ValueError):
            return None

    def _older_window(self) -> Optional[str]:
        try:
            beat = json.loads(self.heartbeat.read_text(encoding="utf-8"))
            pid, seen = int(beat.get("pid") or 0), pd.Timestamp(beat["time"])
        except Exception:                   # no heartbeat yet, or one being replaced: nothing to go on
            return None
        if pid == os.getpid() or self.clock() - seen > pd.Timedelta(minutes=self.fresh_minutes) or not pid_alive(pid):
            return None
        return f"process {pid}, last scan {seen:%H:%M} UTC"


class LiveRunner:
    def __init__(
        self,
        settings: Settings,
        symbol: str,
        fetch: Callable[[], Dict[Timeframe, CandleSeries]],
        broker: Optional[Broker] = None,
        notifier: Optional[TelegramNotifier] = None,
        engine: Optional[StrategyEngine] = None,
        guard: Optional[RiskGuard] = None,
        dry_run: bool = True,
        require_approval: Optional[bool] = None,
        approval_timeout_minutes: Optional[int] = None,
        notify_every_scan: Optional[bool] = None,
        clock: Optional[Callable[[], pd.Timestamp]] = None,
        keep_paper_account: bool = False,
    ):
        self.settings = settings
        self.symbol = symbol.upper()
        self.spec = settings.symbol(self.symbol)
        self.fetch = fetch
        self.broker = broker
        self.notifier = notifier or TelegramNotifier(params=settings.telegram, dry_run=True)
        self.engine = engine or StrategyEngine(settings)
        self.guard = guard or RiskGuard(settings.prop_firm, settings.account_size)
        if broker is not None and callable(getattr(broker, "realized_pnl_since", None)) and self.guard.realized_since is None:
            self.guard.realized_since = broker.realized_pnl_since     # a restart keeps the day's and the month's losses
        # the highest day-start balance (drawdown_basis day_high, the FTMO 1-step's trailing limit) survives a restart and is
        # shared by the account's windows: a file next to the journal, the highest value wins
        self.day_high_path: Optional[Path] = (Path(settings.live.journal_path).parent / "guard_day_high.json"
                                              if settings.live.journal_path else None)
        self._saved_day_high = self.load_day_high()
        self.limits_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"limits_{self.symbol}.json"
                                            if settings.live.journal_path else None)
        self.dry_run = dry_run
        self.require_approval = settings.live.require_approval if require_approval is None else require_approval
        self.approval_timeout_minutes = approval_timeout_minutes if approval_timeout_minutes is not None else settings.live.approval_timeout_minutes
        self.notify_every_scan = settings.live.notify_every_scan if notify_every_scan is None else notify_every_scan
        self.clock = clock or utc_now
        self.seen: set = set()
        self.pending: Dict[str, PendingSetup] = {}
        self.deferred: Dict[str, PendingSetup] = {}      # entries the account lock held up: retried every scan until expiry
        self._last_scan_ok: Optional[pd.Timestamp] = None   # for the heartbeat: the last scan that ran through
        self.limits: Dict[str, Dict[str, Any]] = {}      # resting limit entries: order id -> what is needed to watch them
        self._limits_checked = False                     # the first scan cancels resting limits this window has no record of
        self.known_positions: Dict[str, Position] = {}
        self.unconfirmed: Dict[str, Position] = {}       # submitted orders whose fill is not confirmed yet
        self.last_analysis: Optional[Analysis] = None
        self.stale: Dict[Timeframe, pd.Timedelta] = {}   # timeframe -> age of its last closed candle
        self._fed_until: Optional[pd.Timestamp] = None   # last candle handed to a simulated broker
        self._feed_line: Optional[str] = None
        self._news_refreshed: Optional[pd.Timestamp] = None
        self._news_warned: Optional[object] = None          # local date of the last calendar warning
        self._poll_warned: Optional[pd.Timestamp] = None    # last time a failed Telegram poll was printed
        self._algo_checked: Optional[pd.Timestamp] = None   # last look at the terminal's Algo Trading button
        self._algo_on: Optional[bool] = None
        self._link_down: Optional[str] = None               # why the broker link is down, while it is
        self._link_down_since: Optional[pd.Timestamp] = None
        self._link_told = False                             # the down message went out (so the back message goes too)
        self.link_quiet_minutes: float = 5.0                # a shorter outage stays off Telegram: FTMO's server restarts
                                                            # every night at 23:00 Amsterdam for about a minute
        self._feed_down: bool = False                       # the lowest timeframe went quiet during the session
        self.journal: Optional[Journal] = Journal(settings.live.journal_path, clock=self.clock) if settings.live.journal_path else None
        # the zones traded per visit survive a restart: without them a restart right after a stop-out could re-enter the same
        # visit, which one_trade_per_visit forbids (re-entries after a stop-out won 9 % in R6)
        self.traded_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"traded_{self.symbol}.json"
                                            if settings.live.journal_path else None)
        self.lock_path: Optional[Path] = Path(settings.live.journal_path).parent / "account.lock" if settings.live.journal_path else None
        self.lock_timeout: float = 10.0                  # seconds a window waits for the account lock before it defers the entry
        # a paper account (BTC on Bitstamp prices) keeps its balance and open trades across a restart
        self.paper_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"paper_{self.symbol}.json"
                                           if keep_paper_account and settings.live.journal_path
                                           and callable(getattr(broker, "restore", None)) else None)
        self.load_paper()
        self.load_traded()
        self.load_limits()
        self._briefed_on: Optional[object] = None          # local date of the last morning briefing
        self._summarized_on: Optional[object] = None       # local date of the last evening summary
        self._loop_error: Optional[Tuple[str, float, int]] = None   # (text, time sent, repeats since): one message per error
        self._views: Dict[Timeframe, CandleSeries] = {}
        self._touched: set = set()                          # POI keys already announced as entered

    # ------------------------------------------------------------ one tick
    def step(self, now: Optional[pd.Timestamp] = None) -> Analysis:
        now = pd.Timestamp(now) if now is not None else self.clock()
        views = self.fetch()
        self._views = views
        self.advance_paper(views, now)
        self.stale = self.stale_timeframes(views, now)
        self.report_feed(views)
        self.check_feed(views, now)
        self.check_algo_trading(now)
        self.refresh_news(now)
        equity = self.broker.equity() if self.broker is not None else self.settings.account_size
        if self.broker is not None:
            try:
                self.guard.update(now, equity, self.broker.balance())
                self.save_day_high()
            except Exception as exc:     # a feed hiccup must not stop the loop; the guard re-checks before any order
                print(f"[live] {self.symbol}: guard update failed ({exc})")
        # exits first and on their own: a failing analysis (an engine error on one day's data) must not keep a trade past
        # its time limit, its weekend close or its break-even
        try:
            self.manage_positions(views)
            self.manage_limits(now)
            self.report_closes()
        except Exception as exc:
            self.report_loop_error(exc)
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=False)
        self.last_analysis = analysis
        self.process_decisions(now)
        if self.deferred and self.broker is not None and not self.dry_run:
            self.retry_deferred(now)
        self.report_closes()
        self.morning_briefing(analysis, now)
        self.evening_summary(now)
        self.announce_poi_touch(analysis)
        if analysis.has_valid_signal:
            self.handle_signal(analysis, now)
        elif self.notify_every_scan:
            self.notifier.send_analysis(analysis, self.spec)
        self.save_paper()
        return analysis

    def record_start(self, code: Dict, settings_doc: Dict, settings_sha: str, command: str) -> Optional[Path]:
        """What this window runs, recorded at its start: a ``start`` row in the journal (code revision, source hash, settings
        hash) and, next to the journal, ``starts/<symbol>_<time>.json`` with the resolved settings (secrets appear as the
        names of their environment variables only) and the command. Every forward trade can then be traced to the program
        and the profile that took it. Never stops the start."""
        now = self.clock()
        commit = code.get("commit") or "?"
        self.note("start", now, note=f"code {commit[:12]}{' + local changes' if code.get('dirty') else ''} source "
                                     f"{str(code.get('source_sha256') or '')[:12]} settings {settings_sha[:12]}")
        if not self.settings.live.journal_path:
            return None
        try:
            path = Path(self.settings.live.journal_path).parent / "starts" / f"{self.symbol}_{pd.Timestamp(now):%Y%m%d_%H%M%S}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            from .backtest.provenance import package_versions
            doc = {"symbol": self.symbol, "started_utc": str(now), "command": command,
                   "code": {k: code.get(k) for k in ("commit", "dirty", "local_changes", "source_sha256")},
                   "versions": package_versions(), "settings_sha256": settings_sha, "settings": settings_doc}
            path.write_text(json.dumps(doc, indent=1, default=str), encoding="utf-8")
            return path
        except Exception as exc:
            print(f"[live] {self.symbol}: start record not written ({exc})")
            return None

    def note(self, event: str, now: Optional[pd.Timestamp] = None, **fields) -> None:
        if self.journal is not None:
            try:
                self.journal.log(event, self.symbol, time=now, **fields)
            except Exception as exc:
                print(f"[live] journal failed ({exc})")

    # ------------------------------------------------------------ Dorus's routine
    def morning_briefing(self, analysis: Analysis, now: pd.Timestamp) -> None:
        """Once per weekday at ``live.briefing_time`` local time: the bias, the decision and the POI map for the day."""
        at = self.settings.live.briefing_time
        if not at:
            return
        local = now.tz_localize("UTC").tz_convert(self.settings.session.timezone)
        hour, minute = (int(x) for x in at.split(":"))
        if local.weekday() > 4 or (local.hour, local.minute) < (hour, minute) or self._briefed_on == local.date():
            return
        self._briefed_on = local.date()
        self.note("briefing", now, price=float(analysis.price), note=analysis.decision.reason)
        self.notifier.send(f"☀️ {self.symbol} morning analysis ({local:%a %H:%M} {self.settings.session.timezone})")
        self.notifier.send_analysis(analysis, self.spec)
        self.send_chart(analysis, "briefing")

    def check_algo_trading(self, now: pd.Timestamp) -> None:
        """Every ten minutes with real orders on: is the terminal's Algo Trading button on?  When it is off MT5 refuses every
        order (retcode 10027, "AutoTrading disabled by client"); say so once when it goes off and once when it is back."""
        if self.dry_run or self.broker is None or not callable(getattr(self.broker, "algo_trading_on", None)):
            return
        if self._algo_checked is not None and now - self._algo_checked < pd.Timedelta(minutes=10):
            return
        self._algo_checked = now
        try:
            on = bool(self.broker.algo_trading_on())
        except Exception:
            return
        if on == self._algo_on:
            return
        if not on:
            self.notifier.send(f"⚠️ {self.symbol}: Algo Trading staat UIT in MT5 - orders worden geweigerd. "
                               f"Zet de knop Algo Trading bovenin MT5 aan (groen).")
        elif self._algo_on is False:
            self.notifier.send(f"✅ {self.symbol}: Algo Trading staat weer aan in MT5.")
        self._algo_on = on

    def load_paper(self) -> None:
        if self.paper_path is None or not self.paper_path.exists():
            return
        try:
            saved = json.loads(self.paper_path.read_text(encoding="utf-8"))
            self.broker.restore(saved.get("broker", saved))
            if saved.get("fed_until"):                 # the candles it already saw are not fed again after a restart
                self._fed_until = pd.Timestamp(saved["fed_until"])
            n = len(self.broker.open_positions())
            print(f"[live] {self.symbol}: paper account restored: balance {self.broker.balance():,.2f}, {n} open trade(s)")
        except Exception as exc:
            print(f"[live] {self.symbol}: paper account not restored ({exc}); starting fresh")

    def save_paper(self) -> None:
        if self.paper_path is None:
            return
        try:
            self.paper_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.paper_path.with_suffix(".tmp")
            state = {"broker": self.broker.state(), "fed_until": str(self._fed_until) if self._fed_until is not None else None}
            tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
            os.replace(tmp, self.paper_path)
        except Exception as exc:
            print(f"[live] {self.symbol}: paper account not saved ({exc})")

    def load_traded(self) -> None:
        """Zones this market traded per visit, from the file the last run left (none when there is no file)."""
        traded = getattr(self.engine, "traded", None)
        if self.traded_path is None or traded is None or not self.traded_path.exists():
            return
        try:
            rows = json.loads(self.traded_path.read_text(encoding="utf-8"))
            mine = traded.setdefault(self.symbol, {})
            for tf, direction, created, visit in rows:
                mine[(str(tf), int(direction), str(created))] = int(visit)
        except Exception as exc:     # a damaged file must not stop the loop
            print(f"[live] {self.symbol}: could not read {self.traded_path} ({exc})")

    def load_day_high(self) -> float:
        """The highest day-start balance on record for this account size (0 when none); raises the guard's to it."""
        if self.day_high_path is None or not self.day_high_path.exists():
            return 0.0
        try:
            doc = json.loads(self.day_high_path.read_text(encoding="utf-8"))
            if float(doc.get("account_size", -1)) != float(self.settings.account_size):
                return 0.0                               # another account size: a new challenge, not this one's record
            value = float(doc["day_high"])
            self.guard.day_high = max(self.guard.day_high, value)
            return value
        except Exception as exc:
            print(f"[live] {self.symbol}: could not read {self.day_high_path} ({exc})")
            return 0.0

    def save_day_high(self) -> None:
        """Write the guard's highest day-start balance when it rose (another window may have written a higher one: kept)."""
        if self.day_high_path is None or self.guard.day_high <= self._saved_day_high:
            return
        try:
            on_file = self.load_day_high()
            value = max(self.guard.day_high, on_file)
            self.day_high_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.day_high_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"account_size": float(self.settings.account_size), "day_high": value}), encoding="utf-8")
            os.replace(tmp, self.day_high_path)
            self._saved_day_high = value
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.day_high_path} ({exc})")

    def save_traded(self) -> None:
        traded = getattr(self.engine, "traded", None)
        if self.traded_path is None or traded is None:
            return
        try:
            rows = [[k[0], int(k[1]), k[2], int(v)] for k, v in traded.get(self.symbol, {}).items()]
            self.traded_path.parent.mkdir(parents=True, exist_ok=True)
            self.traded_path.write_text(json.dumps(rows), encoding="utf-8")
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.traded_path} ({exc})")

    def evening_summary(self, now: pd.Timestamp) -> None:
        """Once per weekday at ``live.summary_time`` local time: the day's closed trades of this market from the journal,
        their R and P&L, the setups seen, the equity and what is still open."""
        at = self.settings.live.summary_time
        if not at:
            return
        tz = self.settings.session.timezone
        local = now.tz_localize("UTC").tz_convert(tz)
        hour, minute = (int(x) for x in at.split(":"))
        if local.weekday() > 4 or (local.hour, local.minute) < (hour, minute) or self._summarized_on == local.date():
            return
        self._summarized_on = local.date()
        closed = setups = 0
        wins, total_r, total_pnl = 0, 0.0, 0.0
        week_line = ""
        if self.journal is not None and self.journal.path.exists():
            try:
                rows = pd.read_csv(self.journal.path, parse_dates=["time"])
                rows = rows[rows["symbol"] == self.symbol]
                dates = rows["time"].dt.tz_localize("UTC").dt.tz_convert(tz).dt.date
                day = dates == local.date()
                done = rows[day & (rows["event"] == "closed")]
                closed, wins = len(done), int((done["r"] > 0).sum())
                total_r, total_pnl = float(done["r"].sum()), float(done["pnl"].sum())
                setups = int((day & (rows["event"] == "setup")).sum())
                if local.weekday() == 4:          # Friday: the week as well (Monday to today)
                    monday = (local - pd.Timedelta(days=4)).date()
                    week = rows[(dates >= monday) & (dates <= local.date()) & (rows["event"] == "closed")]
                    wr = f", {100 * (week['r'] > 0).mean():.0f} % won" if len(week) else ""
                    week_line = (f"\n📅 {self.symbol} this week: {len(week)} trade(s){wr}, {float(week['r'].sum()):+.2f}R, "
                                 f"P&L {float(week['pnl'].sum()):+,.0f}")
            except Exception as exc:     # a summary must never stop the loop
                print(f"[live] {self.symbol}: evening summary could not read the journal ({exc})")
        line = (f"📊 {self.symbol} {local:%a %d %b}: {closed} trade(s) closed, {wins} won, {total_r:+.2f}R, "
                f"P&L {total_pnl:+,.0f}; {setups} setup(s)")
        if self.broker is not None:
            try:
                open_now = self.broker.open_positions(self.symbol)
                line += f"; equity {self.broker.equity():,.0f}; open: {len(open_now) or 'none'}"
            except Exception as exc:
                print(f"[live] {self.symbol}: evening summary could not read the broker ({exc})")
        self.notifier.send(line + week_line)

    def send_chart(self, analysis: Analysis, kind: str, timeframe: Optional[Timeframe] = None,
                   setup: Optional[TradeSetup] = None, forecast: Optional[ForecastSummary] = None) -> None:
        """Chart image to Telegram (candles, zones, setup, Kronos fan) and the MT5 overlay file; never fatal."""
        if not self.settings.live.send_charts or not self._views:
            return
        try:
            from .notify.chart import render_chart
            tf = timeframe or (setup.confirmation.timeframe if setup is not None else None)
            if tf is None or tf not in self._views:
                tf = next((t for t in (Timeframe.H_4, Timeframe.H_1, Timeframe.MIN_15) if t in self._views), min(self._views))
            series = self._views[tf]
            if forecast is None and self.settings.kronos.mode != "off" and getattr(self.engine, "forecaster", None) is not None:
                forecast = self.engine._forecast(series, [])
            bias = "  ".join(f"{t.label} {b.bias.name.lower()}" for t, b in sorted(analysis.biases.items())) if analysis.biases else ""
            zones = self.chart_zones(analysis, setup)
            title = f"{self.symbol} {tf.label}  {kind}"
            if setup is not None:
                title += f"  R:R 1:{setup.rr:.1f}  {setup.lots:.2f} lots  risk {setup.risk_amount:,.0f}"
            path = render_chart(series, f"{self.settings.live.charts_dir}/{self.symbol}_{tf.label}_{kind}.png",
                                pois=zones, setup=setup, forecast=forecast, title=title,
                                subtitle=f"{bias}  |  {analysis.decision.reason}", lookback=self.settings.live.chart_lookback,
                                price_decimals=self.spec.price_decimals)
            self.notifier.send_photo(path, f"{self.symbol} {tf.label} {kind}")
            if forecast is not None and self.settings.live.mt5_overlay and hasattr(self.broker, "server_offset"):
                from .notify.mt5_overlay import write_forecast_file
                write_forecast_file(self.symbol, forecast, series.timestamps.iloc[-1], tf, self.broker.server_offset(self.symbol),
                                    mt5_symbol=self.broker.mt5_symbol(self.symbol))
        except Exception as exc:
            print(f"[live] {self.symbol}: chart failed ({exc})")

    def tradable_timeframes(self, analysis: Analysis) -> Tuple[Timeframe, ...]:
        """The zone timeframes the engine trades in this decision's mode (``poi_timeframes`` in full mode,
        ``scalp_poi_timeframes`` in scalp mode)."""
        c = self.settings.confirmation
        return tuple(c.poi_timeframes) if analysis.decision.mode is TradeMode.FULL else tuple(c.scalp_poi_timeframes)

    def chart_zones(self, analysis: Analysis, setup: Optional[TradeSetup] = None, limit: int = 4) -> list:
        """The zones worth drawing: the bias direction, the timeframes the profile trades, the ``limit`` nearest to price
        (and the setup's own zone).  A chart with every zone of every timeframe hides the one that matters."""
        zones = [p for p in analysis.pois if p.direction is analysis.decision.direction] or list(analysis.pois)
        if analysis.decision.tradable:
            allowed = self.tradable_timeframes(analysis)
            zones = [p for p in zones if p.timeframe in allowed] or zones
        price = float(analysis.price)
        zones = sorted(zones, key=lambda p: 0.0 if p.contains(price) else min(abs(price - p.low), abs(price - p.high)))[:limit]
        if setup is not None and all(p.key != setup.poi.key for p in zones):
            zones.append(setup.poi)
        return zones

    def announce_poi_touch(self, analysis: Analysis) -> None:
        """Say once when price enters a POI that the bias allows, so the trader can watch the confirmation form.
        Only zones on the timeframes the profile trades: a touch of a monthly zone on a 1D/4H/1H profile is not a setup."""
        if not self.settings.live.notify_poi_touch or not analysis.decision.tradable:
            return
        d = self.spec.price_decimals
        allowed = self.tradable_timeframes(analysis)
        for poi in analysis.pois:
            if poi.direction is not analysis.decision.direction or not poi.contains(analysis.price):
                continue
            if poi.timeframe not in allowed:
                continue
            if poi.key in self._touched:
                continue
            self._touched.add(poi.key)
            self.note("poi_touch", analysis.timestamp, poi_tf=poi.timeframe.label, direction=poi.direction.name,
                      price=float(analysis.price), note=f"{poi.low:.{d}f}-{poi.high:.{d}f}")
            arrow = "▲" if poi.direction is Bias.BULLISH else "▼"
            self.notifier.send(f"👀 {self.symbol} is inside the {poi.timeframe.label} {arrow} POI {poi.low:.{d}f}-{poi.high:.{d}f} "
                               f"({analysis.decision.reason}); waiting for a confirmation")
            self.send_chart(analysis, "touch", timeframe=poi.timeframe)

    def run_forever(self, poll_seconds: Optional[int] = None) -> None:
        poll = poll_seconds or self.settings.live.poll_seconds
        while True:
            state, detail = "ok", ""
            try:
                if self.connection_ok():
                    self.step()
                    self._last_scan_ok = self.clock()
                else:
                    state, detail = "link down", str(self._link_down or "")
            except Exception as exc:  # keep the loop alive and say what broke
                state, detail = "error", f"{type(exc).__name__}: {exc}"
                self.report_loop_error(exc)
            self.write_heartbeat(state, detail)
            try:
                if self.broker is not None:
                    self.broker.idle(poll)
                else:
                    time.sleep(poll)
            except Exception as exc:  # an event-loop broker (IBKR) can raise while waiting: wait plainly this once
                self.report_loop_error(exc)
                time.sleep(poll)

    def write_heartbeat(self, state: str = "ok", detail: str = "") -> Optional[Path]:
        """``heartbeat_<symbol>.json`` next to the journal after every scan, for ``watchdog``: the time, the state (ok, link
        down, error), the last good scan, the newest candle and how far the news calendar reaches. Never stops the loop."""
        if not self.settings.live.journal_path:
            return None
        try:
            now = self.clock()
            last_candle = None
            if self._views:
                lowest = self._views[min(self._views)]
                if len(lowest):
                    last_candle = str(min(self._views).close_time(lowest.timestamps.iloc[-1]))
            calendar = getattr(self.engine, "calendar", None)
            events = getattr(calendar, "events", None) or []
            news = self.settings.news
            doc = {"symbol": self.symbol, "pid": os.getpid(), "time": str(now), "state": state, "detail": detail[:300],
                   "last_scan_ok": str(self._last_scan_ok) if self._last_scan_ok is not None else None,
                   "last_candle": last_candle, "stale": self.stale_text(),
                   "calendar_until": str(max(e.time for e in events)) if events else None,
                   "news": bool(news.enabled), "tag": getattr(self.notifier, "prefix", "").strip()}
            path = Path(self.settings.live.journal_path).parent / f"heartbeat_{self.symbol}.json"
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc), encoding="utf-8")
            os.replace(tmp, path)
            return path
        except Exception as exc:
            print(f"[live] {self.symbol}: heartbeat not written ({exc})")
            return None

    def report_loop_error(self, exc: Exception) -> None:
        """A scan error: the traceback on the console, a Telegram message for a new error, and the same error again at most
        every 30 minutes with how often it came back (a call failing every scan sent a message a minute)."""
        import traceback
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        text, now = f"{type(exc).__name__}: {exc}", time.time()
        last = self._loop_error
        if last is not None and last[0] == text and now - last[1] < 1800:
            self._loop_error = (text, last[1], last[2] + 1)
            return
        again = f" (also {last[2]}x since the last message)" if last is not None and last[0] == text and last[2] else ""
        self._loop_error = (text, now, 0)
        self.notifier.send(f"⚠️ {self.symbol}: live loop error: {exc}{again}")

    # ------------------------------------------------------------ data
    def refresh_news(self, now: pd.Timestamp) -> None:
        """Pull this and next week's high-impact events from ForexFactory into the engine's calendar, hourly."""
        n = self.settings.news
        calendar = getattr(self.engine, "calendar", None)
        if calendar is None or not n.enabled or not n.forexfactory:
            return
        if self._news_refreshed is not None and now - self._news_refreshed < pd.Timedelta(int(n.refresh_minutes), unit="min"):
            return
        self._news_refreshed = now
        from .data.calendar import fetch_forexfactory, load_events, save_events
        # one download an hour for all windows: the first window to need it saves the week next to the journal and the
        # others read that file (five windows asking every hour drew ForexFactory's 429 "too many requests")
        cache_dir = Path(self.settings.live.journal_path).parent if self.settings.live.journal_path else None
        max_age = pd.Timedelta(int(n.refresh_minutes), unit="min")
        failed = []
        for week in ("thisweek", "nextweek"):          # next week's file is often missing (404) until late in the week
            cache = cache_dir / f"forexfactory_{week}.csv" if cache_dir is not None else None
            try:
                if cache is not None and cache.exists() and time.time() - cache.stat().st_mtime < max_age.total_seconds():
                    calendar.add(load_events(cache))
                    continue
                events = fetch_forexfactory(week)
                calendar.add(events)
                if cache is not None:
                    save_events(events, cache)
            except Exception as exc:
                failed.append(f"{week}: {exc}")
        if len(failed) == 2 and self._news_warned != now.date():
            self._news_warned = now.date()            # once a day is enough: the loaded calendar covers the gap
            print(f"[live] {self.symbol}: news calendar refresh failed ({'; '.join(failed)}); using the events already "
                  f"loaded (data/calendar/high_impact.csv, extended from the TradingView calendar when it runs out)")

    def stale_timeframes(self, views: Dict[Timeframe, CandleSeries], now: pd.Timestamp) -> Dict[Timeframe, pd.Timedelta]:
        """Timeframes whose newest candle closed more than ``live.max_data_age_bars`` candles before ``now``."""
        out: Dict[Timeframe, pd.Timedelta] = {}
        for tf, series in views.items():
            if len(series) == 0:
                continue
            last_close = tf.close_time(series.timestamps.iloc[-1])
            deadline = last_close
            for _ in range(max(1, int(self.settings.live.max_data_age_bars))):
                deadline = deadline + tf.delta()
            if now > deadline:
                out[tf] = now - last_close
        return out

    def check_feed(self, views: Dict[Timeframe, CandleSeries], now: pd.Timestamp, quiet_minutes: int = 20) -> None:
        """Say once when the lowest timeframe has had no new candle for ``quiet_minutes`` during the entry session (the
        bot cannot trade on it: a lost connection, a symbol the server lacks, cached bars), and once when it is back.
        Outside the session nothing is said (weekends, the daily break of gold and indices)."""
        if not views:
            return
        lowest = min(views)
        age = self.stale.get(lowest)
        session = self.settings.session
        open_now = in_session(now, session)[0] if session.enabled else True
        quiet = age is not None and age >= pd.Timedelta(minutes=quiet_minutes) and open_now
        if quiet and not self._feed_down:
            self._feed_down = True
            self.notifier.send(f"⚠️ {self.symbol}: geen nieuwe {lowest.label}-candles sinds {_age_text(age)} tijdens de "
                               f"handelstijden - zo kan de bot niet handelen. Controleer MT5 (verbinding, symbool).")
        elif self._feed_down and age is None:
            self._feed_down = False
            self.notifier.send(f"✅ {self.symbol}: de koersdata loopt weer.")

    def connection_ok(self) -> bool:
        """The broker's link (MT5: re-initialised after a terminal restart); while down the scan is skipped. One message
        once it has been down ``link_quiet_minutes`` and one when it is back; a shorter outage only on the console (6
        October: FTMO's nightly server restart sent a down and a back message for every market at 23:01 and 23:02)."""
        check = getattr(self.broker, "connection_ok", None)
        if not callable(check):
            return True
        try:
            ok, reason = check()
        except Exception as exc:
            ok, reason = False, str(exc)
        now = self.clock()
        if not ok:
            if self._link_down is None:
                self._link_down, self._link_down_since = reason, now
                print(f"[live] {self.symbol}: {reason}; waiting, trying again every scan")
            minutes = (now - self._link_down_since) / pd.Timedelta(minutes=1)
            if not self._link_told and minutes >= self.link_quiet_minutes:
                self._link_told = True
                self.notifier.send(f"⚠️ {self.symbol}: {reason}, al {minutes:.0f} min - de bot wacht en probeert het elke "
                                   f"minuut opnieuw.")
        elif self._link_down is not None:
            minutes = (now - self._link_down_since) / pd.Timedelta(minutes=1)
            if self._link_told:
                self.notifier.send(f"✅ {self.symbol}: weer verbonden met MT5.")
            else:
                print(f"[live] {self.symbol}: connected again after {minutes:.0f} min")
            self._link_down, self._link_down_since, self._link_told = None, None, False
        return ok

    def stale_text(self) -> str:
        return ", ".join(f"{tf.label} {_age_text(age)} old" for tf, age in sorted(self.stale.items()))

    def report_feed(self, views: Dict[Timeframe, CandleSeries]) -> None:
        report = getattr(self.fetch, "report", None)
        line = report.describe() if isinstance(report, FeedReport) and report.sources else ", ".join(tf.label for tf in sorted(views))
        if self.stale:
            line += " | stale: " + self.stale_text()
        if line != self._feed_line:
            self._feed_line = line
            print(f"[live] {self.symbol} data: {line}")

    def advance_paper(self, views: Dict[Timeframe, CandleSeries], now: pd.Timestamp) -> None:
        """Hand every newly closed candle of the lowest timeframe to a simulated broker, exactly once."""
        on_candle = getattr(self.broker, "on_candle", None)
        if on_candle is None or not views:
            return
        lowest = views[min(views)].closed_as_of(now)
        if len(lowest) == 0:
            return
        start = 0
        if self._fed_until is not None:
            start = lowest.index_at_or_after(self._fed_until)
            if start < len(lowest) and lowest.timestamps.iloc[start] == self._fed_until:
                start += 1
        for k in range(start, len(lowest)):
            on_candle(self.symbol, lowest[k])
        self._fed_until = lowest.timestamps.iloc[-1]      # on_candle also records the last close as the price

    # ------------------------------------------------------------ signals
    def handle_signal(self, analysis: Analysis, now: pd.Timestamp) -> None:
        setup = analysis.signal.setup
        forecast = analysis.signal.forecast
        key = (setup.poi.key, str(setup.confirmation.timestamp))
        if key in self.seen:
            return
        self.seen.add(key)
        sid = short_id_for(key)
        sf = self.journal.setup_fields(setup) if self.journal is not None else {}
        if self.stale and self.settings.live.require_fresh_data:
            self.note("stale", now, id=sid, note=self.stale_text(), **sf)
            self.notifier.send(f"⏸ {self.symbol}: setup ignored, the data is stale ({self.stale_text()}); refresh the feed")
            return
        self.note("setup", now, id=sid, reason=setup.tp_source, **sf)
        calendar = getattr(self.engine, "calendar", None)
        if calendar is not None:
            soon = calendar.upcoming(self.symbol, now, within_minutes=240)
            if soon:
                e = soon[0]
                minutes = int((e.time - now).total_seconds() // 60)
                self.notifier.send(f"📰 {self.symbol}: next high-impact news {e.title} ({e.currency}) in {minutes} min")
        if self.broker is None or self.dry_run:
            self.notifier.send_setup(setup, forecast, self.spec)
            self.send_chart(analysis, "setup", setup=setup, forecast=forecast)
            if self.broker is not None:
                self.notifier.send(f"{self.symbol}: dry-run, order not sent")
            return
        ok, reason = self.guard.can_open(self.broker, now, self.symbol, new_risk=self.planned_risk(setup))
        if not ok:
            self.notifier.send_setup(setup, forecast, self.spec)
            self.notifier.send(f"⛔ {self.symbol}: setup NOT executable - {reason}")
            return
        if self.require_approval:
            timeout = self.approval_timeout_minutes or max(5, setup.confirmation.timeframe.minutes)
            pending = PendingSetup(short_id_for(key), key, setup, forecast, now, now + pd.Timedelta(int(timeout), unit="min"))
            self.pending[pending.short_id] = pending
            self.note("approval_requested", now, id=pending.short_id, note=f"expires {pending.expires_at:%H:%M} UTC")
            self.notifier.send_approval_request(setup, pending.short_id, forecast, self.spec, pending.expires_at)
            self.send_chart(analysis, "setup", setup=setup, forecast=forecast)
            return
        self.execute(setup, forecast, now)

    def fill_stamp(self, now: pd.Timestamp) -> pd.Timestamp:
        """The fill time a simulated broker records: the start of the lowest timeframe's candle the fill falls in, so the
        paper broker checks that candle's stop and target too (stamped at the poll time it skipped the whole candle)."""
        if callable(getattr(self.broker, "on_candle", None)) and self._views:
            return pd.Timestamp(now).floor(f"{min(self._views).minutes}min")
        return now

    def margin_room(self, direction, price: float) -> Optional[Tuple[float, float]]:
        """``(most lots, margin available)`` for a new position at ``price``, or None when the broker cannot tell (paper,
        a server without order_calc_margin). One position may tie up prop_firm.max_margin_pct of equity and at most 90 %
        of the free margin: at 1.5 % risk a BTC trade needs about 2.5x its account in exposure, which a 10k FTMO account
        (crypto at about 1:2) refuses as "No money"; cut to fit, it trades smaller instead of not at all."""
        pct = self.settings.prop_firm.max_margin_pct
        per_lot_fn, free_fn = getattr(self.broker, "margin_per_lot", None), getattr(self.broker, "free_margin", None)
        if not pct or per_lot_fn is None:
            return None
        try:
            per_lot = per_lot_fn(self.symbol, direction, float(price))
            free = free_fn() if free_fn is not None else None
            room = float(self.broker.equity()) * pct / 100.0
        except Exception:
            return None
        if not per_lot or per_lot <= 0:
            return None
        if free is not None:
            room = min(room, 0.9 * float(free))
        room = max(0.0, room)
        return room / per_lot, room

    def planned_risk(self, setup: Optional[TradeSetup] = None) -> float:
        """What the next trade risks at its stop (account currency): the profile's risk, lowered by risk.drawdown_steps, times
        the profile's stake and the setup's zone multiplier (setup B)."""
        from .strategy.risk import setup_risk, stepped_risk
        try:
            params = stepped_risk(self.settings.risk, self.broker.balance(), self.settings.account_size)
            params = setup_risk(params, setup.poi.timeframe if setup is not None else None)
            return float(self.broker.equity()) * params.risk_pct / 100.0
        except Exception:
            return 0.0

    def stake_note(self, risk_params) -> str:
        """Why a trade risks other than the profile's risk_pct, for the fill message: the balance under the start (drawdown
        steps), near the phase's target (target protection), the zone's or the profile's multiplier."""
        from .strategy.risk import stepped_risk
        base = self.settings.risk
        if abs(risk_params.risk_pct - base.risk_pct) < 1e-12:
            return ""
        parts = []
        try:
            balance = float(self.broker.balance())
            stepped = stepped_risk(base, balance, self.settings.account_size).risk_pct
        except Exception:
            balance, stepped = None, base.risk_pct
        if stepped < base.risk_pct:
            parts.append("near the target" if balance is not None and balance >= self.settings.account_size else "balance below the start")
        if stepped > 0 and abs(risk_params.risk_pct / stepped - 1.0) > 1e-9:
            parts.append(f"x{risk_params.risk_pct / stepped:g} for its zone or the profile's stake")
        return f" ({risk_params.risk_pct:g} % on this trade: {', '.join(parts) or 'adjusted'})"

    def _open_locked(self, setup: TradeSetup, now: pd.Timestamp):
        """The checks and the order, inside the account lock: the message to send on a refusal, else
        ``(position, setup id, risk amount, risk params, resize note, margin note)``."""
        sid = short_id_for((setup.poi.key, str(setup.confirmation.timestamp)))
        ok, reason = self.guard.can_open(self.broker, now, self.symbol, new_risk=self.planned_risk(setup))
        if not ok:
            self.note("not_executed", now, id=sid, reason=reason)
            return f"⛔ {self.symbol}: not executed - {reason}"
        try:
            price = self.broker.fill_price(self.symbol, setup.direction)       # the ask for a buy, the bid for a sell
        except Exception as exc:
            self.note("not_executed", now, id=sid, reason=f"no current price: {exc}")
            return f"⛔ {self.symbol}: not executed - no current price ({exc})"
        cap = self.settings.risk.max_spread_stop_fraction
        if cap > 0 and abs(price - setup.stop) > 0:
            try:
                spread = abs(self.broker.fill_price(self.symbol, Direction.LONG) - self.broker.fill_price(self.symbol, Direction.SHORT))
            except Exception:
                spread = None
            if spread is not None and spread > cap * abs(price - setup.stop):
                share = spread / abs(price - setup.stop)
                self.note("not_executed", now, id=sid, price=float(price), spread=float(spread),
                          reason=f"spread {share:.0%} of the stop distance (max {cap:.0%})")
                return (f"⛔ {self.symbol}: not executed - spread {spread:.{self.spec.price_decimals}f} is {share:.0%} of the "
                        f"stop distance (max {cap:.0%})")
        from .strategy.risk import resize_at, setup_risk, stepped_risk
        wrong_side = (setup.direction.sign > 0 and price <= setup.stop) or (setup.direction.sign < 0 and price >= setup.stop)
        risk_params = setup_risk(stepped_risk(self.settings.risk, self.broker.balance(), self.settings.account_size),
                                 setup.poi.timeframe)
        lots, risk_amount, risk_distance, rr_now, _ = resize_at(price, setup.stop, setup.take_profit, self.broker.equity(),
                                                                self.spec, risk_params)
        if wrong_side or rr_now < self.settings.risk.min_rr:
            self.note("not_executed", now, id=sid, price=float(price), rr=float(rr_now), reason="price moved, R:R below minimum")
            return (f"⛔ {self.symbol}: not executed - price moved to {price:.{self.spec.price_decimals}f}, "
                    f"R:R now 1:{rr_now:.1f} (min {self.settings.risk.min_rr:.0f})")
        if lots <= 0:
            self.note("not_executed", now, id=sid, price=float(price), reason="stop too wide for the minimum lot at this price")
            return f"⛔ {self.symbol}: not executed - stop too wide for the minimum lot at {price:.{self.spec.price_decimals}f}"
        frac = float(getattr(self.settings.risk, "limit_entry_fraction", 0.0) or 0.0)
        if frac > 0:                                     # the same checks at the market price first, as the backtest makes them
            return self._place_limit(setup, now, sid, price, frac, risk_params)
        resized = f"; lots {setup.lots:.2f} -> {lots:.2f} at {price:.{self.spec.price_decimals}f}" if abs(lots - setup.lots) > 1e-9 else ""
        if risk_params.risk_pct != self.settings.risk.risk_pct:
            resized += f"; risk {risk_params.risk_pct:g} % (drawdown steps, stake or zone multiplier)"
        margin_note = ""
        room = self.margin_room(setup.direction, price)
        if room is not None and lots > room[0] + 1e-9:
            fit = round(math.floor(room[0] / self.spec.lot_step + 1e-9) * self.spec.lot_step, 4)
            if fit < self.spec.min_lot:
                self.note("not_executed", now, id=sid, price=float(price), reason=f"margin: {room[1]:,.0f} available, "
                          f"{lots:.2f} lots wanted, {room[0]:.3f} fit")
                return (f"⛔ {self.symbol}: not executed - not enough margin for the minimum lot "
                        f"({room[1]:,.0f} available, {self.spec.min_lot:g} lots needed)")
            margin_note = f" (margin: lots cut from {lots:.2f}, risk {100 * fit / lots:.0f} % of planned)"
            resized += f"; lots {lots:.2f} -> {fit:.2f}: margin ({room[1]:,.0f} available)"
            risk_amount *= fit / lots
            lots = fit
        try:
            pos = self.broker.place_market_order(
                self.symbol, setup.direction, lots, setup.stop, setup.take_profit, risk_amount,
                risk_distance, setup.breakeven_r,
                meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value}",
                      "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value},
                price=price, ts=self.fill_stamp(now), price_is_fill=True,
            )
        except Exception as exc:
            self.note("not_executed", now, id=sid, reason=f"order failed: {exc}")
            return f"⛔ {self.symbol}: order failed - {exc}"
        return pos, sid, risk_amount, risk_params, resized, margin_note

    # ------------------------------------------------------------ limit entries (risk.limit_entry_fraction)
    def _place_limit(self, setup: TradeSetup, now: pd.Timestamp, sid: str, price: float, frac: float, risk_params):
        """Inside the account lock: a limit ``frac`` of the way from the executable price back toward the stop, sized on the
        smaller stop, the margin checked; returns ("limit", order, sid) or the refusal to send."""
        from .strategy.risk import resize_at
        d = self.spec.price_decimals
        limit = self.spec.round_price(price - setup.direction.sign * frac * abs(price - setup.stop))
        lots, risk_amount, risk_distance, rr, _ = resize_at(limit, setup.stop, setup.take_profit, self.broker.equity(),
                                                            self.spec, risk_params)
        if rr < self.settings.risk.min_rr:
            self.note("not_executed", now, id=sid, price=float(limit), rr=float(rr), reason="limit: R:R below minimum")
            return f"⛔ {self.symbol}: not executed - R:R at the limit {limit:.{d}f} is 1:{rr:.1f} (min {self.settings.risk.min_rr:g})"
        if lots <= 0:
            self.note("not_executed", now, id=sid, price=float(limit), reason="limit: stop too wide for the minimum lot")
            return f"⛔ {self.symbol}: not executed - stop too wide for the minimum lot at the limit {limit:.{d}f}"
        room = self.margin_room(setup.direction, limit)
        if room is not None and lots > room[0] + 1e-9:
            fit = round(math.floor(room[0] / self.spec.lot_step + 1e-9) * self.spec.lot_step, 4)
            if fit < self.spec.min_lot:
                self.note("not_executed", now, id=sid, price=float(limit), reason=f"limit: margin {room[1]:,.0f} available")
                return f"⛔ {self.symbol}: not executed - not enough margin for the minimum lot ({room[1]:,.0f} available)"
            risk_amount *= fit / lots
            lots = fit
        expires = pd.Timestamp(now) + pd.Timedelta(minutes=int(self.settings.risk.limit_entry_minutes))
        try:
            order = self.broker.place_limit_order(
                self.symbol, setup.direction, lots, limit, setup.stop, setup.take_profit, risk_amount, risk_distance,
                setup.breakeven_r, expires, ts=self.fill_stamp(now),
                meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value} L",
                      "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value})
        except Exception as exc:
            self.note("not_executed", now, id=sid, reason=f"limit order failed: {exc}")
            return f"⛔ {self.symbol}: limit order failed - {exc}"
        return "limit", order, sid

    def _limit_placed(self, setup: TradeSetup, order, sid: str, now: pd.Timestamp) -> None:
        self.guard.record_trade(now)
        mark_traded = getattr(self.engine, "mark_traded", None)
        if mark_traded is not None:                      # the zone's visit is used, filled or not (as the backtest counts it)
            mark_traded(self.symbol, setup.poi.key, getattr(setup, "visit_number", None))
            self.save_traded()
        self.limits[order.id] = {"sid": sid, "direction": order.direction.name, "price": float(order.price),
                                 "stop": float(order.stop), "take_profit": float(order.take_profit), "lots": float(order.lots),
                                 "risk_amount": float(order.risk_amount), "placed_at": pd.Timestamp(now),
                                 "expires_at": pd.Timestamp(order.expires_at)}
        self.save_limits()
        d = self.spec.price_decimals
        side = "BUY" if order.direction is Direction.LONG else "SELL"
        frac = float(self.settings.risk.limit_entry_fraction)
        self.note("limit_placed", now, id=order.id, direction=order.direction.name, entry=float(order.price), stop=float(order.stop),
                  take_profit=float(order.take_profit), lots=float(order.lots), risk=float(order.risk_amount),
                  note=f"setup {sid}; valid until {order.expires_at:%H:%M} UTC")
        self.notifier.send(f"📌 {self.symbol} {side} LIMIT {order.lots:.2f} lots @ {order.price:.{d}f} ({frac:.0%} back toward the "
                           f"stop)  SL {order.stop:.{d}f}  TP {order.take_profit:.{d}f}  risk {order.risk_amount:,.0f}  valid until "
                           f"{order.expires_at:%H:%M} UTC (id {order.id})")

    def load_limits(self) -> None:
        if self.limits_path is None or not self.limits_path.exists():
            return
        try:
            for row in json.loads(self.limits_path.read_text(encoding="utf-8")):
                row = dict(row)
                row["placed_at"], row["expires_at"] = pd.Timestamp(row["placed_at"]), pd.Timestamp(row["expires_at"])
                self.limits[str(row.pop("id"))] = row
        except Exception as exc:
            print(f"[live] {self.symbol}: could not read {self.limits_path} ({exc})")

    def save_limits(self) -> None:
        if self.limits_path is None:
            return
        try:
            rows = [{"id": oid, **{k: (str(v) if isinstance(v, pd.Timestamp) else v) for k, v in info.items()}}
                    for oid, info in self.limits.items()]
            self.limits_path.parent.mkdir(parents=True, exist_ok=True)
            self.limits_path.write_text(json.dumps(rows), encoding="utf-8")
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.limits_path} ({exc})")

    def _target_traded(self, info: Dict) -> bool:
        """Did price reach the target since the limit was placed? The lowest timeframe's candles that close after the
        placement, the forming one included (its extreme has traded): the backtest's candles from the placement on."""
        if not self._views:
            return False
        tf = min(self._views)
        lowest = self._views[tf]
        k0 = lowest.index_after(pd.Timestamp(info["placed_at"]) - tf.delta())
        if k0 >= len(lowest):
            return False
        if info["direction"] == "LONG":
            return bool(float(lowest.high[k0:].max()) >= float(info["take_profit"]))
        return bool(float(lowest.low[k0:].min()) <= float(info["take_profit"]))

    def manage_limits(self, now: pd.Timestamp) -> None:
        """Every scan: a filled limit becomes a trade like a market fill; one past its time or whose target traded first is
        cancelled; one the server dropped is reported. At the first scan, a resting limit of this market the window has no
        record of (left from before a restart without its file) is cancelled."""
        if self.broker is None or self.dry_run:
            return
        if not self._limits_checked:
            self._limits_checked = True
            try:
                for order in self.broker.limit_orders(self.symbol):
                    if order.id not in self.limits:
                        self.broker.cancel_limit(order.id)
                        self.note("limit_cancelled", now, id=order.id, reason="no record of it at the start")
                        self.notifier.send(f"🚫 {self.symbol}: limit {order.id} cancelled at the start - this window has no record of it")
            except Exception as exc:
                print(f"[live] {self.symbol}: could not check the resting limit orders ({exc})")
        changed = False
        for oid, info in list(self.limits.items()):
            try:
                state, pos = self.broker.limit_state(oid)
            except Exception as exc:
                print(f"[live] {self.symbol}: limit {oid} state unknown ({exc}); asking again next scan")
                continue
            if state == "pending":
                reason = "expired" if now >= info["expires_at"] else "the target traded first" if self._target_traded(info) else None
                if reason is None:
                    continue
                try:
                    self.broker.cancel_limit(oid)
                    state, pos = self.broker.limit_state(oid)       # it may have filled while it was being cancelled
                except Exception as exc:
                    print(f"[live] {self.symbol}: cancel of limit {oid} failed ({exc}); trying again next scan")
                    continue
                if state != "filled":
                    self.limits.pop(oid); changed = True
                    self.note("limit_cancelled", now, id=oid, reason=reason)
                    self.notifier.send(f"🚫 {self.symbol}: limit {oid} cancelled - {reason}")
                    continue
            if state == "filled":
                self.limits.pop(oid); changed = True
                self._limit_filled(oid, info, pos, now)
            elif state == "gone":
                self.limits.pop(oid); changed = True
                self.note("limit_gone", now, id=oid, reason="no longer on the server, not filled")
                self.notifier.send(f"⌛ {self.symbol}: limit {oid} is no longer on the server (removed or expired there), not filled")
        if changed:
            self.save_limits()

    def _limit_filled(self, oid: str, info: Dict, pos: Optional[Position], now: pd.Timestamp) -> None:
        d = self.spec.price_decimals
        side = "BUY" if info["direction"] == "LONG" else "SELL"
        if pos is None:                                  # filled and closed again between two scans: its close follows
            self.note("filled", now, id=oid, direction=info["direction"], entry=float(info["price"]), stop=float(info["stop"]),
                      take_profit=float(info["take_profit"]), lots=float(info["lots"]), risk=float(info["risk_amount"]),
                      note=f"setup {info['sid']}; limit {oid}; closed again before this scan")
            self.notifier.send(f"💸 {self.symbol} {side} limit {oid} filled @ {info['price']:.{d}f} and closed again before this scan")
            return
        from .strategy.risk import reconcile_risk
        if getattr(pos, "status", "filled") == "filled" and hasattr(self.broker, "pnl_for"):
            reconcile_risk(pos, self.broker, float(info["risk_amount"]))
        self.known_positions[pos.id] = pos
        self.note("filled", now, id=pos.id, direction=pos.direction.name, entry=float(pos.entry), stop=float(pos.stop),
                  take_profit=float(pos.take_profit), lots=float(pos.lots), risk=float(pos.risk_amount),
                  note=f"setup {info['sid']}; limit {oid}")
        self.notifier.send(f"💸 {self.symbol} {side} filled (limit) {pos.lots:.2f} lots @ {pos.entry:.{d}f}  SL {pos.stop:.{d}f}  "
                           f"TP {pos.take_profit:.{d}f}  risk {pos.risk_amount:,.0f}  (id {pos.id})")

    def defer(self, setup: TradeSetup, forecast: Optional[ForecastSummary], now: pd.Timestamp) -> None:
        """The account lock stayed busy: keep the entry for the next scans, up to ``max(5, confirmation minutes)`` after the
        first try (the approval timeout's rule); one message when it is deferred and one if it expires."""
        key = (setup.poi.key, str(setup.confirmation.timestamp))
        sid = short_id_for(key)
        held = self.deferred.get(sid)
        if held is None:
            wait = max(5, setup.confirmation.timeframe.minutes)
            held = PendingSetup(sid, key, setup, forecast, now, now + pd.Timedelta(int(wait), unit="min"))
            self.deferred[sid] = held
            self.notifier.send(f"⏳ {self.symbol}: setup {sid} deferred - another window holds the account lock; "
                               f"trying again every scan until {held.expires_at:%H:%M} UTC")
        self.note("deferred", now, id=sid, reason="account lock busy", note=f"expires {held.expires_at:%H:%M} UTC")

    def retry_deferred(self, now: pd.Timestamp) -> None:
        for sid, held in list(self.deferred.items()):
            if now >= held.expires_at:
                self.deferred.pop(sid)
                self.note("expired", now, id=sid, note="deferred: the account lock stayed busy")
                self.notifier.send(f"⌛ {self.symbol}: setup {sid} expired, the account lock stayed busy until "
                                   f"{held.expires_at:%H:%M} UTC; not executed")
                continue
            self.execute(held.setup, held.forecast, now)

    def execute(self, setup: TradeSetup, forecast: Optional[ForecastSummary], now: pd.Timestamp) -> Optional[Position]:
        # the cap check and the order under one lock shared by the windows of the account: two markets signalling in
        # the same second could otherwise both take the last open slot. Telegram waits until the lock is released (a
        # slow send inside it held the other windows for 15 s). A window that cannot get the lock within 10 s does not
        # trade without it: the entry is deferred and tried again every scan, with every check, until it expires
        lock = AccountLock(self.lock_path, timeout=self.lock_timeout)
        with lock:
            opened = self._open_locked(setup, now) if lock.held or self.lock_path is None else None
        if opened is None:
            self.defer(setup, forecast, now)
            return None
        self.deferred.pop(short_id_for((setup.poi.key, str(setup.confirmation.timestamp))), None)
        if isinstance(opened, str):
            self.notifier.send(opened)
            return None
        if opened[0] == "limit":
            self._limit_placed(setup, opened[1], opened[2], now)
            return None
        pos, sid, risk_amount, risk_params, resized, margin_note = opened
        from .strategy.risk import reconcile_risk
        self.guard.record_trade(now)
        mark_traded = getattr(self.engine, "mark_traded", None)   # test doubles may lack it
        if mark_traded is not None:
            mark_traded(self.symbol, setup.poi.key, getattr(setup, "visit_number", None))
            self.save_traded()
        if getattr(pos, "status", "filled") == "filled" and hasattr(self.broker, "pnl_for"):
            reconcile_risk(pos, self.broker, risk_amount)
        self.known_positions[pos.id] = pos
        side = "BUY" if pos.direction.sign > 0 else "SELL"
        d = self.spec.price_decimals
        filled = getattr(pos, "status", "filled") == "filled"
        self.note("filled" if filled else "submitted", now, id=pos.id, direction=pos.direction.name, entry=float(pos.entry),
                  stop=float(pos.stop), take_profit=float(pos.take_profit), lots=float(pos.lots), risk=float(pos.risk_amount),
                  note=f"setup {sid}{resized}")
        if filled:
            stepped = self.stake_note(risk_params)
            self.notifier.send(f"💸 {self.symbol} {side} filled {pos.lots:.2f} lots @ {pos.entry:.{d}f}  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  risk {pos.risk_amount:,.0f}{stepped}{margin_note}  "
                               f"(id {pos.id})")
        else:
            self.unconfirmed[pos.id] = pos
            self.notifier.send(f"📨 {self.symbol} {side} {pos.lots:.2f} lots submitted, fill not confirmed yet  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  (id {pos.id})")
        return pos

    # ------------------------------------------------------------ approvals
    def process_decisions(self, now: pd.Timestamp) -> None:
        # Telegram serves one getUpdates poller per bot: five windows polling every minute drew "409 Conflict: terminated by
        # other getUpdates request", and the error ended the window's scan. Only a window with a setup waiting for an answer
        # asks (none ever does without the approve step), and a failed ask leaves the scan running.
        decisions = []
        if self.pending or getattr(self.notifier, "_queued", None):
            try:
                decisions = self.notifier.poll_decisions()
            except Exception as exc:
                if self._poll_warned is None or now - self._poll_warned >= pd.Timedelta(hours=1):
                    self._poll_warned = now
                    print(f"[live] {self.symbol}: Telegram answers not read ({exc}); retrying next scan")
        for decision in decisions:
            pending = self.pending.pop(decision.short_id, None)
            if pending is None:
                self.notifier.send(f"{self.symbol}: no pending setup with id {decision.short_id} (expired or already handled)")
                continue
            if not decision.approved:
                self.note("skipped", now, id=pending.short_id)
                self.notifier.send(f"❌ {self.symbol}: setup {pending.short_id} skipped")
                continue
            if now >= pending.expires_at:
                self.note("approved_late", now, id=pending.short_id)
                self.notifier.send(f"⌛ {self.symbol}: setup {pending.short_id} approved too late "
                                   f"(expired {pending.expires_at:%H:%M} UTC), not executed")
                continue
            self.note("approved", now, id=pending.short_id)
            self.notifier.send(f"✅ {self.symbol}: setup {pending.short_id} approved, sending order")
            self.execute(pending.setup, pending.forecast, now)
        for short_id, pending in list(self.pending.items()):
            if now >= pending.expires_at:
                self.pending.pop(short_id)
                self.note("expired", now, id=short_id)
                self.notifier.send(f"⌛ {self.symbol}: setup {short_id} expired without approval")

    # ------------------------------------------------------------ positions
    def manage_positions(self, views: Dict[Timeframe, CandleSeries]) -> None:
        """Confirm pending fills, close trades past ``exits.max_hold_hours`` and move stops to break-even per the exit
        rules (no partials). A simulated broker applies the time limit itself, candle by candle."""
        if self.broker is None or not views:
            return
        open_by_id = {p.id: p for p in self.broker.open_positions(self.symbol)}
        hold = self.settings.exits.max_hold_hours
        weekend = self.settings.prop_firm.weekend_close
        if (hold or weekend) and not callable(getattr(self.broker, "on_candle", None)):
            from .strategy.exits import weekend_cutoff_after
            now = self.clock()
            for pid, pos in list(open_by_id.items()):
                if getattr(pos, "status", "filled") != "filled" or pos.opened_at is None:
                    continue
                if hold and now - pd.Timestamp(pos.opened_at) >= pd.Timedelta(hours=float(hold)):
                    reason, why = "time", f"after {hold:g} h"
                elif weekend and now >= weekend_cutoff_after(pos.opened_at, weekend):
                    reason, why = "weekend", f"before the weekend (Friday {weekend} New York)"
                else:
                    continue
                try:
                    self.broker.close_position(pid, reason, ts=now)
                    open_by_id.pop(pid)
                    self.note(f"{reason}_exit", now, id=pid, note=why)
                except Exception as exc:
                    if not pos.meta.get(f"{reason}_exit_failed_sent"):
                        pos.meta[f"{reason}_exit_failed_sent"] = True
                        self.notifier.send(f"⚠️ {self.symbol}: closing {pid} {why} failed ({exc}); trying every scan")
        d = self.spec.price_decimals
        for pid in list(self.unconfirmed):
            current = open_by_id.get(pid)
            if current is None:
                self.unconfirmed.pop(pid)
                self.known_positions.pop(pid, None)
                self.note("did_not_fill", id=pid)
                self.notifier.send(f"❌ {self.symbol}: order {pid} did not fill (cancelled or rejected)")
            elif getattr(current, "status", "filled") == "filled":
                self.unconfirmed.pop(pid)
                self.note("fill_confirmed", id=pid, entry=float(current.entry))
                self.notifier.send(f"💸 {self.symbol}: fill confirmed @ {current.entry:.{d}f}  (id {pid})")
        lowest = views[min(views)]
        if len(lowest) == 0:
            return
        last = lowest.last
        for pos in open_by_id.values():
            self.known_positions.setdefault(pos.id, pos)
            if pos.breakeven_done or getattr(pos, "status", "filled") != "filled":
                continue
            if pos.breakeven_r <= 0 or pos.risk_distance <= 0:
                continue                                   # no trigger or no risk known: never move a stop on a guess
            retry_at = pos.meta.get("breakeven_retry_at")
            if retry_at is not None and last.timestamp < retry_at:
                continue
            # every candle since the last look (or the fill), not only the newest: a touch of the trigger in the last
            # seconds of a candle between two polls, or while the window was down, counts as in the backtest
            since = pos.meta.get("be_checked_until") or pos.opened_at
            k0 = len(lowest) - 1
            if since is not None:
                k0 = min(max(0, lowest.index_at_or_after(pd.Timestamp(since))), len(lowest) - 1)
            extreme = float(lowest.high[k0:].max()) if pos.direction.sign > 0 else float(lowest.low[k0:].min())
            pos.meta["be_checked_until"] = last.timestamp               # the newest candle may still be forming: again next scan
            # once the trigger was reached, a refused move is tried again every 15 minutes whatever price does since:
            # the trigger is history, the move is still owed
            if pos.meta.get("breakeven_pending") or breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme,
                                                                       pos.breakeven_r):
                try:
                    self.broker.modify_stop(pos.id, pos.entry)
                except Exception as exc:                   # e.g. 10016 when price is back under the entry: keep the
                    pos.meta["breakeven_pending"] = True   # stop, try again later
                    pos.meta["breakeven_retry_at"] = last.timestamp + pd.Timedelta(15, unit="min")
                    if not pos.meta.get("breakeven_failed_sent"):
                        pos.meta["breakeven_failed_sent"] = True
                        self.note("breakeven_failed", id=pos.id, reason=str(exc))
                        self.notifier.send(f"⚠️ {self.symbol}: stop to break-even on {pos.id} refused ({exc}); trying again "
                                           f"every 15 min, the original stop stays")
                    continue
                pos.meta.pop("breakeven_pending", None)
                pos.breakeven_done = True
                self.note("breakeven", id=pos.id, stop=float(pos.entry))
                self.notifier.send(f"🔒 {self.symbol}: stop moved to break-even on {pos.id} ({pos.breakeven_r:.0f}R reached)")

    def report_closes(self) -> None:
        if self.broker is None:
            return
        for trade in self.broker.recent_closes():
            if str(trade.symbol).upper() != self.symbol:
                continue                                   # another window's trade on the same account: its window reports it
            self.known_positions.pop(trade.id, None)
            self.note("closed", trade.closed_at, id=trade.id, direction=trade.direction.name, entry=float(trade.entry),
                      price=float(trade.exit), pnl=float(trade.pnl), r=float(trade.r), reason=trade.reason, lots=float(trade.lots))
            icon = "🎯" if trade.reason == "take_profit" else "🛑" if trade.reason == "stop" else "➖"
            self.notifier.send(f"{icon} {self.symbol} closed ({trade.reason}) @ {trade.exit:.{self.spec.price_decimals}f}  "
                               f"P&L {trade.pnl:+,.0f}  ({trade.r:+.2f}R)  id {trade.id}")
