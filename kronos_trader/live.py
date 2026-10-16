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
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis, Bias, Direction, ForecastSummary, POIStatus, TradeMode, TradeSetup
from .data.tv_cache import load_all
from .execution.base import Broker, Position
from .execution.risk_guard import RiskGuard
from .journal import Journal, journal_times
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
    a killed window) is removed, so a stuck file costs at most five minutes of deferral, never the trading itself (8
    October: at 60 s a slow terminal's own entry, a dozen calls and a 2 s wait for the position, could outlive the lock
    and let a second window past the account's checks)."""

    def __init__(self, path: Optional[Path], timeout: float = 10.0, stale: float = 300.0):
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
            except OSError:                 # gone already, or held by a virus scanner / OneDrive (WinError 32): stale in five minutes
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
        from .notify.headlines import Headlines
        self.headlines = Headlines(settings.live.news_headlines, settings.live.news_headlines_hours) \
            if settings.live.news_headlines else None
        self.dorus = None                                   # the Dorus check after an entry (live.dorus_check: advisory)
        self.dorus_wait = False                             # tests: run the check in the loop instead of beside it
        if str(settings.live.dorus_check).lower() == "advisory":
            from .notify.dorus_check import DorusCheck
            check = DorusCheck(timeout=settings.live.dorus_check_timeout)
            if check.available:
                self.dorus = check
            else:
                print(f"[live] {symbol}: Dorus check off (ANTHROPIC_API_KEY or DORUS_CHECK_MODEL not set)")
        self.seen: set = set()
        self.pending: Dict[str, PendingSetup] = {}
        self.deferred: Dict[str, PendingSetup] = {}      # entries the account lock held up: retried every scan until expiry
        self._last_scan_ok: Optional[pd.Timestamp] = None   # for the heartbeat: the last scan that ran through
        self.limits: Dict[str, Dict[str, Any]] = {}      # resting limit entries: order id -> what is needed to watch them
        self._limits_checked = False                     # every scan cancels resting limits this window has no record of
        self._stray_warned: set = set()                  # unrecorded limits whose cancel failed, said once on Telegram
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
        self._started_at: pd.Timestamp = self.clock()       # positions opened before this window started are restored ones
        # position listings since run_forever started or the link came back (None: not counted, a scan run by hand). The
        # first listing after a terminal (re)start can come before the account's positions are in: read as empty it let a
        # second position through the per-market cap, and the guard counted no open risk (fixcheck3). An entry waits for
        # a second listing
        self._listings: Optional[int] = None
        self._account_start = getattr(broker, "account_login", None)   # the account the window connected on (none: the
        self._account_told = False                                        # terminal showed none; the first one is said)
        self.link_quiet_minutes: float = 5.0                # a shorter outage stays off Telegram: FTMO's server restarts
                                                            # every night at 23:00 Amsterdam for about a minute
        self._feed_down: bool = False                       # the lowest timeframe went quiet during the session
        self.journal: Optional[Journal] = Journal(settings.live.journal_path, clock=self.clock) if settings.live.journal_path else None
        # the zones traded per visit survive a restart: without them a restart right after a stop-out could re-enter the same
        # visit, which one_trade_per_visit forbids (re-entries after a stop-out won 9 % in R6)
        self.traded_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"traded_{self.symbol}.json"
                                            if settings.live.journal_path else None)
        # the setups this market handled survive a restart too: a restart while a setup's confirmation candle is still the newest
        # would signal it again, and with two places in a market (EURUSD since 13 October, which also re-enters a zone in the
        # same visit) the same setup could be taken twice (the laptop's code review, 13 October)
        self.seen_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"seen_{self.symbol}.json"
                                          if settings.live.journal_path else None)
        self.seen_ids: Dict[str, str] = {}               # setup id -> when this window handled it
        # the zones' visit memory (when each visit began, how many there were) survives a restart too: a fresh window sees
        # only its first candles and would date a visit's first touch to the first candle it has, which moves the 24 h
        # touch-age and visit-age gates away from the backtest's (the engine review of 14 October)
        self.visits_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"visits_{self.symbol}.json"
                                            if settings.live.journal_path else None)
        # the day's start balance, shared by the account's windows: a window that starts mid-day takes it from the terminal's
        # trade history, which may not be complete yet (a terminal just started); the file keeps the highest one of the day
        self.day_start_path: Optional[Path] = (Path(settings.live.journal_path).parent / "guard_day_start.json"
                                               if settings.live.journal_path else None)
        self._saved_day_start: Optional[Tuple[str, float]] = None
        self.lock_path: Optional[Path] = Path(settings.live.journal_path).parent / "account.lock" if settings.live.journal_path else None
        self.lock_timeout: float = 10.0                  # seconds a window waits for the account lock before it defers the entry
        # a paper account (BTC on Bitstamp prices) keeps its balance and open trades across a restart
        self.paper_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"paper_{self.symbol}.json"
                                           if keep_paper_account and settings.live.journal_path
                                           and callable(getattr(broker, "restore", None)) else None)
        # the lock at the phase's target (prop_firm.lock_at_target) moves a trade's take-profit: its own target, the last level
        # the lock sent and whether Telegram heard of it are kept per position next to the journal, so a restart moves a lock
        # back toward the trade's own target, never toward a lock price taken for its own
        self.own_targets_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"target_lock_{self.symbol}.json"
                                                 if settings.live.journal_path else None)
        self.own_targets: Dict[str, Dict[str, Any]] = {}
        self._lock_cache: Optional[Tuple[int, Any]] = None  # the lock's account state, read once a scan
        self._lock_retry: Dict[str, Tuple[int, pd.Timestamp]] = {}   # id -> (refusals, next try) of a refused move or close
        self.load_paper()
        self.load_traded()
        self.load_limits()
        self.load_seen()
        self.load_visits()
        self.load_own_targets()
        self._briefed_on: Optional[object] = None          # local date of the last morning briefing
        self._summarized_on: Optional[object] = None       # local date of the last evening summary
        self._loop_error: Optional[Tuple[str, float, int]] = None   # (text, time sent, repeats since): one message per error
        self._views: Dict[Timeframe, CandleSeries] = {}
        self._touched: set = set()                          # POI keys already announced as entered
        self._near_missed: Dict[Tuple[str, str], pd.Timestamp] = {}   # (zone key, reason) -> when the near miss was said
        self._approached: Dict[str, object] = {}            # zone key -> local date of its approach notice
        self._midday_on: Optional[object] = None            # local date of the last midday check
        self._last_briefing_at: Optional[pd.Timestamp] = None
        self._target_told: Optional[str] = None             # the day and state of the last target notice of this window
        self._scan_id = 0                                   # one target state per scan (target_state's cache key)
        self._target_cache: Optional[Tuple[int, Any]] = None
        self._days_known: Optional[int] = None              # the highest trading-day count read (days never go down)

    # ------------------------------------------------------------ one tick
    def step(self, now: Optional[pd.Timestamp] = None) -> Analysis:
        now = pd.Timestamp(now) if now is not None else self.clock()
        self._scan_id += 1
        views = self.fetch()
        self._views = views
        self.advance_paper(views, now)
        self.stale = self.stale_timeframes(views, now)
        self.report_feed(views)
        self.check_feed(views, now)
        self.check_algo_trading(now)
        self.refresh_news(now)
        unread: Optional[Exception] = None
        try:
            equity = self.broker.equity() if self.broker is not None else self.settings.account_size
        except Exception as exc:         # the terminal did not give the account this once (15 October stack review, A15)
            equity, unread = None, exc
        if self.broker is not None and equity is not None:
            try:
                self.guard.update(now, equity, self.broker.balance())
                self.sync_day_start()
                self.save_day_high()
            except Exception as exc:     # a feed hiccup must not stop the loop; the guard re-checks before any order
                print(f"[live] {self.symbol}: guard update failed ({exc})")
        # exits first and on their own: a failing analysis (an engine error on one day's data), or an account the terminal
        # did not give this once, must not keep a trade past its time limit, its weekend close or its break-even
        exits_failed = False
        try:
            self.manage_positions(views)
            self.manage_limits(now)
            self.report_closes()
        except Exception as exc:
            exits_failed = True
            self.report_loop_error(exc)
        try:                             # on its own as well: a failing target lock never holds up the exits or an entry
            self.manage_target_lock(now)
        except Exception as exc:
            self.report_loop_error(exc)
        if unread is not None:
            raise RuntimeError(f"the account could not be read ({unread!r}); "
                               f"{'the exits failed as well (see the error before)' if exits_failed else 'the exits were handled'}, "
                               f"no entry this scan")
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=False)
        self.last_analysis = analysis
        self.save_visits(now)
        self.process_decisions(now)
        if self.deferred and self.broker is not None and not self.dry_run and not self._entries_held():
            self.retry_deferred(now)
        self.report_closes()
        # the notices, each on its own: a bug in one of them must never reach the setup below (the pre-mortem of 14 October:
        # a notice that raised would have skipped handle_signal while the window looked alive)
        for name, notice in (("morning briefing", lambda: self.morning_briefing(analysis, now)),
                             ("evening summary", lambda: self.evening_summary(now)),
                             ("zone touch", lambda: self.announce_poi_touch(analysis, now)),
                             ("midday check", lambda: self.midday_check(analysis, now)),
                             ("near misses", lambda: self.announce_near_misses(analysis, now)),
                             ("approach", lambda: self.announce_approach(analysis, now)),
                             ("target", lambda: self.announce_target(now))):
            try:
                notice()
            except Exception as exc:
                print(f"[live] {self.symbol}: the {name} notice failed ({exc})")
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
        if self._briefing_due(now, self.settings.live.briefing_time, "_briefed_on"):
            self._send_briefing(analysis, now, "ochtendcheck")

    def midday_check(self, analysis: Analysis, now: pd.Timestamp) -> None:
        """The same once more at ``live.midday_time``, before the afternoon window (14 October, Max: "ik wil alles zien")."""
        if self._briefing_due(now, getattr(self.settings.live, "midday_time", None), "_midday_on"):
            last = self._last_briefing_at
            if last is not None and pd.Timestamp(now) - last < pd.Timedelta(hours=1):
                return                                      # a window started after 12:55: the morning check just went out
            self._send_briefing(analysis, now, "middagcheck")

    def _briefing_due(self, now: pd.Timestamp, at: Optional[str], flag: str) -> bool:
        """True once per weekday from ``at`` (local time) on; ``flag`` is the attribute that remembers the day it was sent."""
        if not at:
            return False
        local = now.tz_localize("UTC").tz_convert(self.settings.session.timezone)
        hour, minute = (int(x) for x in at.split(":"))
        if local.weekday() > 4 or (local.hour, local.minute) < (hour, minute) or getattr(self, flag) == local.date():
            return False
        setattr(self, flag, local.date())
        return True

    def _send_briefing(self, analysis: Analysis, now: pd.Timestamp, kind: str) -> None:
        local = now.tz_localize("UTC").tz_convert(self.settings.session.timezone)
        self._last_briefing_at = pd.Timestamp(now)
        self.note("briefing", now, price=float(analysis.price),
                  note=analysis.decision.reason if kind == "ochtendcheck" else f"{kind}: {analysis.decision.reason}")
        # 14 October (Max: "de telegram berichten duidelijker"): one message a market in Dutch, the decision in words and only
        # the zones the bot can still trade, the extra lines, then the 1H chart; the old three messages if the new one fails
        try:
            from .notify.formatting import WEEKDAYS, format_briefing
            zones = self.chart_zones(analysis)
            text = format_briefing(analysis, self.spec, zones, f"{WEEKDAYS[local.weekday()]} {local:%H:%M}",
                                   kind=kind, extra=self.briefing_extras(analysis, now, zones))
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing text failed ({exc}); the plain analysis instead")
            text = None
        if text is not None:
            self.notifier.send(text)
        else:
            self.notifier.send(f"☀️ {self.symbol} {kind} ({local:%a %H:%M} {self.settings.session.timezone})")
            self.notifier.send_analysis(analysis, self.spec)
        self.send_chart(analysis, "briefing" if kind == "ochtendcheck" else kind, timeframe=Timeframe.H_1)

    def closed_daily(self, now: pd.Timestamp) -> Optional[CandleSeries]:
        """The daily candles closed by ``now``: the feeds hand over the forming day as well, the engine drops it
        (``closed_as_of``) and so does every line that reads the days."""
        daily = self._views.get(Timeframe.D_1)
        if daily is None:
            return None
        try:
            return daily.closed_as_of(pd.Timestamp(now))
        except Exception:
            return daily

    def briefing_extras(self, analysis: Analysis, now: pd.Timestamp, zones: Optional[list] = None) -> List[str]:
        """The lines under a briefing (14 October, Max: "alles wat je kan zien"): the regime, today's news with its blackouts,
        the stake after the drawdown ladder, the room to the limits, the entry windows and what has to happen for a trade.
        Every line on its own; a line that cannot be made is left out, never an error."""
        lines: List[str] = []
        tz = self.settings.session.timezone
        local = pd.Timestamp(now).tz_localize("UTC").tz_convert(tz)
        try:        # the regime: the 20-day efficiency ratio (trend or range) and the day range against the last year
            daily = self.closed_daily(now)
            if daily is not None and len(daily) >= 40:
                closes = pd.Series(daily.close[-21:], dtype=float)
                moved = float(closes.diff().abs().sum())
                er = abs(float(closes.iloc[-1] - closes.iloc[0])) / moved if moved > 0 else 0.0
                ranges = pd.Series(daily.high - daily.low, dtype=float).rolling(14).mean().dropna().tail(250)
                pct = float((ranges <= ranges.iloc[-1]).mean() * 100) if len(ranges) else float("nan")
                regime = "trending" if er >= 0.35 else "range"
                lines.append(f"📈 Regime: {regime} (ER20 {er:.2f}) · dagbereik op het {pct:.0f}e percentiel van het jaar")
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing regime line failed ({exc})")
        try:        # the high-impact news still to come today, with the blackout each one brings
            calendar = getattr(self.engine, "calendar", None)
            if not self.settings.news.enabled:
                lines.append("📰 Het nieuwsfilter staat uit in dit profiel")
            elif calendar is not None:
                end_of_day = (local.normalize() + pd.Timedelta(days=1)).tz_convert("UTC").tz_localize(None)
                minutes = max(int((end_of_day - pd.Timestamp(now)).total_seconds() // 60), 1)
                events = calendar.upcoming(self.symbol, now, within_minutes=minutes)
                if events:
                    n = self.settings.news
                    bits = []
                    for e in events[:4]:
                        t = pd.Timestamp(e.time).tz_localize("UTC").tz_convert(tz)
                        bits.append(f"{t:%H:%M} {e.title} ({e.currency}), blackout "
                                    f"{t - pd.Timedelta(minutes=n.before_minutes):%H:%M}–{t + pd.Timedelta(minutes=n.after_minutes):%H:%M}")
                    lines.append("📰 Nieuws vandaag: " + "; ".join(bits))
                else:
                    lines.append("📰 Geen high-impact nieuws meer vandaag")
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing news line failed ({exc})")
        try:        # the stake today and the room to the limits
            if self.broker is not None:
                from .strategy.risk import stepped_risk
                balance, equity = float(self.broker.balance()), float(self.broker.equity())
                base = self.settings.risk
                stepped = stepped_risk(base, balance, self.settings.account_size)
                pct = stepped.risk_pct * float(getattr(base, "stake_multiplier", 1.0) or 1.0)
                if abs(stepped.risk_pct - base.risk_pct) < 1e-9:
                    ladder = ""
                elif balance >= self.settings.account_size:          # stepped_risk also halves the stake near the phase's target
                    ladder = " (dicht bij het doel: halve inzet)"
                else:
                    ladder = f" (ladder: balans {100 * (balance / self.settings.account_size - 1):+.1f}% t.o.v. de start)"
                multipliers = ", ".join(f"{getattr(k, 'label', k)}-zone ×{v:g}" for k, v in (getattr(base, "zone_risk_multiplier", {}) or {}).items())
                target = self.target_state()
                if target is not None and target[0] == "done":
                    lines.append(f"🏁 Doel +{float(base.target_pct):g}% staat, {target[1]} handelsdagen: geen nieuwe trades; "
                                 f"vraag de volgende fase aan zodra alles dicht is")
                elif target is not None:
                    pct = float(self.settings.prop_firm.finish_risk_pct)
                    have = "?" if target[1] is None else target[1]
                    lines.append(f"🏁 Doel +{float(base.target_pct):g}% staat, {have} van {self.settings.prop_firm.min_trading_days} "
                                 f"handelsdagen: inzet {pct:g}% = {equity * pct / 100:,.0f} tot de dagen er zijn")
                else:
                    lines.append(f"💰 Inzet: {pct:g}% = {equity * pct / 100:,.0f}{ladder}" + (f" · {multipliers}" if multipliers else ""))
                lock = self.target_lock_state()
                if lock is not None:            # the lock at the phase's target (16 October): what it does today
                    days = "?" if lock["days"] is None else lock["days"]
                    need = self.settings.prop_firm.min_trading_days
                    lines.append(f"🔐 Doel-lock aan ({days} van {need} handelsdagen): " + (
                        f"vanaf de {need}e handelsdag (de dag van de trade telt mee) neemt een trade winst waar de gesloten "
                        f"balans +{float(base.target_pct):g}% haalt, als dat dichter ligt dan zijn eigen doel; nog "
                        f"{lock['goal'] - lock['balance']:,.0f} te gaan" if lock["balance"] < lock["target"] else
                        f"het doel staat: de lock doet niets meer, open trades houden hun eigen doel"))
                g = self.guard
                day_room = g.params.daily_loss_limit_pct - g.daily_loss_pct(equity)
                total_room = g.params.max_drawdown_pct - g.drawdown_pct(equity)
                lines.append(f"🛡 Ruimte: vandaag nog {day_room:.1f}% (grens {g.params.daily_loss_limit_pct:g}%), totaal nog "
                             f"{total_room:.1f}% (grens {g.params.max_drawdown_pct:g}%) · balans {balance:,.0f}, equity {equity:,.0f}")
                room = g.worst_case_room(self.broker) if self.broker is not None else None
                if room is not None:            # the guard also refuses on the equity: never more room than that line shows
                    room = (min(room[0], day_room), min(room[1], total_room))
                if room is not None and abs(room[0] - day_room) >= 0.05:       # open stops or swaps: what the guard decides on
                    lines.append(f"🛡 Na alle open stops: vandaag nog {room[0]:.1f}%, totaal nog {room[1]:.1f}% "
                                 f"(daarop beslist de bewaker over een nieuwe trade)")
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing stake line failed ({exc})")
        try:        # the windows and what a trade needs
            s = self.settings.session
            if s.enabled:
                lines.append("🕘 Vensters: " + " en ".join(f"{a}–{b}" for a, b in s.windows) + f" ({tz})")
            if analysis.decision.tradable:
                zones = [p for p in (self.chart_zones(analysis) if zones is None else zones) if p.direction is analysis.decision.direction]
                if zones:
                    from .notify.formatting import zone_line
                    from .strategy.confirmation import allowed_confirmation_timeframes
                    p = zones[0]
                    tfs = "/".join(tf.label for tf in allowed_confirmation_timeframes(p.timeframe, self.settings.confirmation)) or "lagere timeframe"
                    price = float(analysis.price)
                    where = "de prijs zit erin: " if p.contains(price) else \
                        f"de prijs naar de {p.timeframe.label}-zone ({zone_line(p, price, self.spec).split(' · ')[-1]}), dan "
                    lines.append(f"🎯 Voor een trade: {where}een balance shift op de {tfs} binnen een venster")
                else:
                    lines.append("🎯 Voor een trade: eerst een verse zone in de richting van de bias")
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing plan line failed ({exc})")
        try:        # no trade allowed: what would have to close where (15 October, Max: "maar ondertussen zegt die geen trade")
            if not analysis.decision.tradable:
                lines += self.turn_lines(analysis, now, zones)
        except Exception as exc:
            print(f"[live] {self.symbol}: briefing turn line failed ({exc})")
        return lines

    def turn_lines(self, analysis: Analysis, now: pd.Timestamp, zones: Optional[list] = None) -> List[str]:
        """What the next hour's close would have to be before the bias allows a trade: the engine's own bias code asked
        with the forming candles closed at trial prices (strategy/whatif.py), the side the higher timeframes lean to
        first, with the zone it would trade from. Nothing when the search was cut short; a line that no close near the
        price turns it only when the search was complete (15 October fix check)."""
        from .core.types import Bias
        from .notify.formatting import _price, zone_kind, zone_line
        from .strategy.whatif import Turn, turn_text, turning_closes
        if not self._views or analysis.decision.tradable:
            return []
        reason = analysis.decision.reason or ""
        lean = Bias.BEARISH if reason.startswith("bearish") else Bias.BULLISH if reason.startswith("bullish") else None
        directions = (lean, lean.opposite) if lean is not None else (Bias.BEARISH, Bias.BULLISH)
        price = float(analysis.price)
        result = turning_closes(self._views, {tf: b.bias for tf, b in analysis.biases.items()}, self.settings,
                                pd.Timestamp(now), price, directions=directions)
        at = getattr(result, "at", None)
        when = ""
        if at is not None:
            when = f"{pd.Timestamp(at).tz_localize('UTC').tz_convert(self.settings.session.timezone):%H:%M}"
        zones = self.chart_zones(analysis) if zones is None else zones
        lines: List[str] = []
        for direction in directions:
            r = result.get(direction)
            if isinstance(r, Turn):
                near = [p for p in zones if p.direction is direction]
                zone = None
                if near:
                    p = min(near, key=lambda z: 0.0 if z.contains(price) else min(abs(price - z.low), abs(price - z.high)))
                    where = zone_line(p, price, self.spec).split(" · ")[-1]
                    zone = f"{p.timeframe.label} {zone_kind(p)} {_price(p.low, self.spec)}–{_price(p.high, self.spec)} ({where})"
                lines.append(f"🎯 Trade als{' om ' + when if when else ''}: " + turn_text(r, lambda x: _price(x, self.spec), zone))
        if not lines and getattr(result, "complete", False) and when:
            lines.append(f"🎯 Bij de sluiting van {when} laat geen koers binnen drie gemiddelde candles van de prijs een "
                         f"trade toe")
        return lines

    def announce_near_misses(self, analysis: Analysis, now: Optional[pd.Timestamp] = None) -> None:
        """A zone in play (price in it, or entered earlier) and the engine refused the trade for a reason worth knowing: the
        R:R, the stop, the depth, a second visit... Said once per zone and reason per four hours, inside the entry windows
        (14 October, Max: "alles zien wat de bot doet")."""
        if not getattr(self.settings.live, "notify_near_miss", False) or not analysis.decision.tradable or not analysis.rejections:
            return
        now = pd.Timestamp(now) if now is not None else self.clock()
        session = self.settings.session
        if session.enabled and not in_session(now, session)[0]:
            return
        from .notify.formatting import classify_near_miss, format_near_miss
        allowed = self.tradable_timeframes(analysis)
        price = float(analysis.price)
        for key, when in list(self._near_missed.items()):   # the throttle's memory stays a day long
            if now - when > pd.Timedelta(days=1):
                del self._near_missed[key]
        for poi in analysis.pois:
            if poi.timeframe not in allowed or poi.direction is not analysis.decision.direction:
                continue
            if not (poi.contains(price) or poi.key in self._touched):
                continue
            prefix = poi.describe() + ":"
            for reason in analysis.rejections:
                if not (reason.startswith(prefix) or reason.startswith("reversal: " + prefix)):
                    continue
                found = classify_near_miss(reason.split(prefix, 1)[1].strip())
                if found is None:
                    continue
                rule, text = found
                key = (poi.key, rule)
                last = self._near_missed.get(key)
                if last is not None and now - last < pd.Timedelta(hours=4):
                    continue
                self._near_missed[key] = now
                d = self.spec.price_decimals
                self.note("near_miss", now, poi_tf=poi.timeframe.label, direction=poi.direction.name, price=price, reason=text,
                          note=f"{poi.low:.{d}f}-{poi.high:.{d}f}")
                try:
                    self.notifier.send(format_near_miss(self.symbol, poi, text, self.spec))
                except Exception as exc:
                    print(f"[live] {self.symbol}: near-miss message failed ({exc})")

    def announce_approach(self, analysis: Analysis, now: Optional[pd.Timestamp] = None) -> None:
        """Price comes within ``live.approach_atr`` ATR14 of the 1H of a zone the bias allows and the profile trades: a
        heads-up once per zone per day, inside the entry windows (14 October)."""
        if not getattr(self.settings.live, "notify_approach", False) or not analysis.decision.tradable:
            return
        now = pd.Timestamp(now) if now is not None else self.clock()
        session = self.settings.session
        if session.enabled and not in_session(now, session)[0]:
            return
        hourly = self._views.get(Timeframe.H_1)
        if hourly is None:
            return
        from .strategy.risk import atr
        ref = atr(hourly)
        reach = float(getattr(self.settings.live, "approach_atr", 0.0) or 0.0) * (ref or 0.0)
        if reach <= 0:
            return
        today = now.tz_localize("UTC").tz_convert(session.timezone).date()
        for key, day in list(self._approached.items()):     # yesterday's notices are forgotten
            if day != today:
                del self._approached[key]
        price = float(analysis.price)
        from .notify.formatting import format_approach
        from .strategy.confirmation import allowed_confirmation_timeframes
        for poi in self.chart_zones(analysis):
            if poi.direction is not analysis.decision.direction or poi.contains(price):
                continue
            distance = poi.low - price if poi.low > price else price - poi.high
            if distance > reach or self._approached.get(poi.key) == today:
                continue
            self._approached[poi.key] = today
            d = self.spec.price_decimals
            self.note("approach", now, poi_tf=poi.timeframe.label, direction=poi.direction.name, price=price,
                      note=f"{poi.low:.{d}f}-{poi.high:.{d}f}")
            try:
                self.notifier.send(format_approach(self.symbol, poi, price, self.spec,
                                                   allowed_confirmation_timeframes(poi.timeframe, self.settings.confirmation)))
            except Exception as exc:
                print(f"[live] {self.symbol}: approach message failed ({exc})")

    def chart_context(self, series: CandleSeries, now: Optional[pd.Timestamp] = None) -> Tuple[list, list]:
        """For the charts without a setup: the previous day's high and low (the liquidity above and below the day; the last
        CLOSED day, the feeds hand over the forming one too) as lines, and the entry windows as index spans of the drawn
        candles to shade."""
        lines, spans = [], []
        try:
            daily = self.closed_daily(now if now is not None else self.clock())
            if daily is not None and len(daily) >= 1 and series.timeframe < Timeframe.D_1:
                d = self.spec.price_decimals
                lines = [(float(daily.high[-1]), f"vorige dag high {float(daily.high[-1]):.{d}f}", None),
                         (float(daily.low[-1]), f"vorige dag low {float(daily.low[-1]):.{d}f}", None)]
            session = self.settings.session
            if session.enabled and series.timeframe < Timeframe.D_1:
                view = series.tail(self.settings.live.chart_lookback)
                inside = [in_session(pd.Timestamp(t), session)[0] for t in view.timestamps] + [False]
                start = None
                for i, flag in enumerate(inside):
                    if flag and start is None:
                        start = i
                    elif not flag and start is not None:
                        spans.append((start, i))
                        start = None
        except Exception as exc:
            print(f"[live] {self.symbol}: chart context failed ({exc})")
        return lines, spans

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

    def load_visits(self) -> None:
        """The zones' visit states from the file the last run left (none when there is no file): the tracker goes on
        folding candles after each state's last candle, as it does inside one run."""
        visits = getattr(self.engine, "visits", None)
        if self.visits_path is None or visits is None or not self.visits_path.exists():
            return
        try:
            from .strategy.poi import VisitState, VisitTracker
            rows = json.loads(self.visits_path.read_text(encoding="utf-8"))
            tracker = visits.setdefault(self.symbol, VisitTracker())
            for row in rows:
                key = (str(row["key"][0]), int(row["key"][1]), str(row["key"][2]))
                state = VisitState(last_ts=pd.Timestamp(row["last_ts"]) if row.get("last_ts") else None,
                                   inside=bool(row.get("inside")), visits=int(row.get("visits") or 0),
                                   visit_start_ts=pd.Timestamp(row["visit_start_ts"]) if row.get("visit_start_ts") else None,
                                   invalid=bool(row.get("invalid")))
                if row.get("first_touch_ts") and hasattr(state, "first_touch_ts"):
                    state.first_touch_ts = pd.Timestamp(row["first_touch_ts"])
                tracker.states[key] = state
        except Exception as exc:     # a damaged file must not stop the loop: the memory starts afresh, as before
            print(f"[live] {self.symbol}: could not read {self.visits_path} ({exc})")

    def save_visits(self, now: Optional[pd.Timestamp] = None) -> None:
        """Write the visit states that saw a candle in the last 14 days (older zones are past every age gate)."""
        visits = getattr(self.engine, "visits", None)
        tracker = visits.get(self.symbol) if isinstance(visits, dict) else None
        if self.visits_path is None or tracker is None:
            return
        cutoff = (pd.Timestamp(now) if now is not None else self.clock()) - pd.Timedelta(days=14)
        rows = []
        for key, st in tracker.states.items():
            if st.last_ts is None or pd.Timestamp(st.last_ts) < cutoff:
                continue
            rows.append({"key": [key[0], int(key[1]), key[2]], "last_ts": str(st.last_ts), "inside": bool(st.inside),
                         "visits": int(st.visits), "visit_start_ts": str(st.visit_start_ts) if st.visit_start_ts is not None else None,
                         "invalid": bool(st.invalid),
                         "first_touch_ts": str(getattr(st, "first_touch_ts", None)) if getattr(st, "first_touch_ts", None) is not None else None})
        try:
            self.visits_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.visits_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(rows), encoding="utf-8")
            os.replace(tmp, self.visits_path)
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.visits_path} ({exc})")

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

    def load_seen(self) -> None:
        """The setups this market handled (setup id -> when), from the file the last run left (none when there is no file)."""
        if self.seen_path is None or not self.seen_path.exists():
            return
        try:
            doc = json.loads(self.seen_path.read_text(encoding="utf-8"))
            self.seen_ids = {str(k): str(v) for k, v in dict(doc).items()}
        except Exception as exc:     # a damaged file must not stop the loop
            print(f"[live] {self.symbol}: could not read {self.seen_path} ({exc})")

    def save_seen(self, now: pd.Timestamp) -> None:
        """Write the handled setups of the last week (older ones can no longer signal: their confirmation candle is long past)."""
        if self.seen_path is None:
            return
        cutoff = pd.Timestamp(now) - pd.Timedelta(days=7)
        kept = {}
        for sid, when in self.seen_ids.items():
            try:
                if pd.Timestamp(when) < cutoff:
                    continue
            except Exception:
                pass
            kept[sid] = when
        self.seen_ids = kept
        try:
            self.seen_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.seen_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(kept), encoding="utf-8")
            os.replace(tmp, self.seen_path)
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.seen_path} ({exc})")

    def sync_day_start(self) -> None:
        """Keep the guard's day start balance at the highest one any window of the account saw today. A window that (re)starts
        mid-day takes it from the terminal's trade history; a history that is not complete yet would read the morning's losses
        as zero and leave the day its whole limit again. The highest baseline is the strictest, and the right one when the
        history was complete."""
        g = self.guard
        if self.day_start_path is None or g.day is None or not g.day_known:
            return
        day = str(pd.Timestamp(g.day).date())
        on_file = 0.0
        try:
            if self.day_start_path.exists():
                doc = json.loads(self.day_start_path.read_text(encoding="utf-8"))
                if doc.get("day") == day and float(doc.get("account_size", -1)) == float(self.settings.account_size):
                    on_file = float(doc.get("balance", 0.0))
        except OSError as exc:       # another window replacing it this instant: never overwrite it blind, try next scan
            print(f"[live] {self.symbol}: could not read {self.day_start_path} ({exc})")
            return
        except Exception as exc:     # a damaged file: written anew below
            print(f"[live] {self.symbol}: could not read {self.day_start_path} ({exc})")
        if on_file > g.day_start_balance:
            g.day_start_balance = on_file
            g.day_high = max(g.day_high, on_file)
        if on_file >= g.day_start_balance or self._saved_day_start == (day, g.day_start_balance):
            return
        try:
            self.day_start_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.day_start_path.with_name(f"{self.day_start_path.stem}_{self.symbol}.tmp")
            tmp.write_text(json.dumps({"account_size": float(self.settings.account_size), "day": day,
                                       "balance": float(g.day_start_balance)}), encoding="utf-8")
            os.replace(tmp, self.day_start_path)
            self._saved_day_start = (day, g.day_start_balance)
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.day_start_path} ({exc})")

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
        closed = setups = touches = misses = 0
        wins, total_r, total_pnl = 0, 0.0, 0.0
        week_line = ""
        if self.journal is not None and self.journal.path.exists():
            try:
                rows = pd.read_csv(self.journal.path)
                rows["time"] = journal_times(rows["time"])
                rows = rows[rows["symbol"] == self.symbol]
                dates = rows["time"].dt.tz_localize("UTC").dt.tz_convert(tz).dt.date
                day = dates == local.date()
                done = rows[day & (rows["event"] == "closed")]
                closed, wins = len(done), int((done["r"] > 0).sum())
                total_r, total_pnl = float(done["r"].sum()), float(done["pnl"].sum())
                setups = int((day & (rows["event"] == "setup")).sum())
                touches = int((day & (rows["event"] == "poi_touch")).sum())
                misses = int((day & (rows["event"] == "near_miss")).sum())
                if local.weekday() == 4:          # Friday: the week as well (Monday to today)
                    monday = (local - pd.Timedelta(days=4)).date()
                    week = rows[(dates >= monday) & (dates <= local.date()) & (rows["event"] == "closed")]
                    wr = f", {100 * (week['r'] > 0).mean():.0f} % won" if len(week) else ""
                    week_line = (f"\n📅 {self.symbol} this week: {len(week)} trade(s){wr}, {float(week['r'].sum()):+.2f}R, "
                                 f"P&L {float(week['pnl'].sum()):+,.0f}")
            except Exception as exc:     # a summary must never stop the loop
                print(f"[live] {self.symbol}: evening summary could not read the journal ({exc})")
        line = (f"📊 {self.symbol} {local:%a %d %b}: {closed} trade(s) closed, {wins} won, {total_r:+.2f}R, "
                f"P&L {total_pnl:+,.0f}; {setups} setup(s), {touches} zone(s) geraakt, {misses} bijna-trade(s)")
        if self.broker is not None:
            try:
                open_now = self.broker.open_positions(self.symbol)
                line += f"; equity {self.broker.equity():,.0f}; open: {len(open_now) or 'none'}"
            except Exception as exc:
                print(f"[live] {self.symbol}: evening summary could not read the broker ({exc})")
        self.notifier.send(line + week_line)

    def send_chart(self, analysis: Analysis, kind: str, timeframe: Optional[Timeframe] = None,
                   setup: Optional[TradeSetup] = None, forecast: Optional[ForecastSummary] = None,
                   limit_price: Optional[float] = None) -> None:
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
            from .notify.formatting import bias_line, plain_decision
            zones = self.chart_zones(analysis, setup)
            label = {"briefing": "ochtendcheck", "touch": "in de zone", "setup": "setup"}.get(kind, kind)
            extra_lines, spans = self.chart_context(series, analysis.timestamp) if setup is None else ([], [])
            title = f"{self.symbol} · {tf.label} · {label}"
            if setup is not None:
                title += f" · R:R 1:{setup.rr:.1f} · {setup.lots:.2f} lots · risico {setup.risk_amount:,.0f}"
            decision = plain_decision(analysis.decision, emoji=False)
            subtitle = f"{bias_line(analysis)}   |   {decision}" if analysis.biases else decision
            path = render_chart(series, f"{self.settings.live.charts_dir}/{self.symbol}_{tf.label}_{kind}.png",
                                pois=zones, setup=setup, forecast=forecast, title=title,
                                subtitle=subtitle, lookback=self.settings.live.chart_lookback,
                                price_decimals=self.spec.price_decimals, last_price=float(analysis.price),
                                limit_price=limit_price, extra_lines=extra_lines, shade_spans=spans)
            self.notifier.send_photo(path, f"{self.symbol} {tf.label} {label}")
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
        """The zones worth drawing and naming: on the timeframes the profile trades, not invalidated, not spent (the engine
        would refuse them for their age: 14 October, Max: "oudere POI's weghalen"), in the bias direction when the bias
        allows one, the ``limit`` nearest to price (and the setup's own zone). A chart with every zone of every timeframe,
        a monthly zone of 800 pips among them, hides the one that matters."""
        c = self.settings.confirmation
        if analysis.decision.tradable:
            allowed = set(self.tradable_timeframes(analysis))
        else:
            allowed = set(c.poi_timeframes) | set(getattr(c, "scalp_poi_timeframes", ()) or ())
        zones = [p for p in analysis.pois if p.status is not POIStatus.INVALIDATED and (not allowed or p.timeframe in allowed)]
        zones = [p for p in zones if not self.spent_zone(p, analysis.timestamp)]
        if analysis.decision.tradable:
            zones = [p for p in zones if p.direction is analysis.decision.direction]
        unique, seen = [], set()                      # a 4H and a 1H zone on the same candles: the larger one names it
        for p in sorted(zones, key=lambda z: z.timeframe, reverse=True):
            same = (round(p.low, 8), round(p.high, 8), p.direction)
            if same not in seen:
                seen.add(same)
                unique.append(p)
        zones = unique
        price = float(analysis.price)
        zones = sorted(zones, key=lambda p: 0.0 if p.contains(price) else min(abs(price - p.low), abs(price - p.high)))[:limit]
        if setup is not None and all(p.key != setup.poi.key for p in zones):
            zones.append(setup.poi)
        return zones

    def announce_poi_touch(self, analysis: Analysis, now: Optional[pd.Timestamp] = None) -> None:
        """Say once when price enters a POI that the bias allows, so the trader can watch the confirmation form.
        Only zones on the timeframes the profile trades: a touch of a monthly zone on a 1D/4H/1H profile is not a setup.
        Only inside the entry windows: outside them no entry can follow (7 October: six BTC touches between 03:30 and
        04:06 read as trades about to happen); a zone price is still in when a window opens is said then."""
        if not self.settings.live.notify_poi_touch or not analysis.decision.tradable:
            return
        session = self.settings.session
        if session.enabled and not in_session(pd.Timestamp(now) if now is not None else self.clock(), session)[0]:
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
            if self.spent_zone(poi, now):
                continue
            self._touched.add(poi.key)
            self.note("poi_touch", analysis.timestamp, poi_tf=poi.timeframe.label, direction=poi.direction.name,
                      price=float(analysis.price), note=f"{poi.low:.{d}f}-{poi.high:.{d}f}")
            news = self.news_lines(now)
            try:
                from .notify.formatting import format_touch
                from .strategy.confirmation import allowed_confirmation_timeframes
                text = format_touch(analysis, poi, self.spec, allowed_confirmation_timeframes(poi.timeframe, self.settings.confirmation))
            except Exception:
                arrow = "▲" if poi.direction is Bias.BULLISH else "▼"
                text = (f"👀 {self.symbol} zit in de {poi.timeframe.label} {arrow} zone {poi.low:.{d}f}-{poi.high:.{d}f}; "
                        f"wacht op een balance shift")
            self.notifier.send(text + "".join(f"\n📰 {line}" for line in news))
            self.send_chart(analysis, "touch", timeframe=poi.timeframe)

    def spent_zone(self, poi, now: Optional[pd.Timestamp] = None) -> bool:
        """True when the engine will not trade ``poi`` for its age: older than the profile's zone age limit, or visited
        more than confirmation.max_touch_age_hours after it formed (the visit's start as the engine's visit tracker has
        it, else ``now``). Such a zone gets no touch notice: "waiting for a confirmation" would wait for nothing (8
        October: a BTC 1D zone of 22 September, visited 328 hours later)."""
        from .strategy.engine import touch_age_hours, zone_age_candles
        c = self.settings.confirmation
        now = pd.Timestamp(now) if now is not None else self.clock()
        created = getattr(poi, "created_at", None)
        if created is None:
            return False
        max_age = c.max_zone_age_by_tf.get(poi.timeframe, c.max_zone_age_candles)
        if max_age > 0 and zone_age_candles(now, created, poi.timeframe) > max_age:
            return True
        if c.max_touch_age_hours > 0:
            state = getattr(getattr(self.engine, "visits", {}).get(self.symbol), "states", {}).get(getattr(poi, "key", None))
            start = getattr(state, "visit_start_ts", None) or now
            # the engine's clock: a zone forms when its candle closes (the review of 14 October: counted from the open, a
            # 1H zone touched 23.5 h after forming got no notice and no place on the chart while the engine traded it)
            if touch_age_hours(created, poi.timeframe, start) > c.max_touch_age_hours:
                return True
        return False

    def run_forever(self, poll_seconds: Optional[int] = None) -> None:
        poll = poll_seconds or self.settings.live.poll_seconds
        self._listings = 0
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
        # one throttle per error text (fixcheck2 loop_changes s06 b: two errors alternating in one scan, the exits' and
        # the unread account's, reset a single remembered text every call and sent two messages a minute)
        seen = getattr(self, "_loop_errors", None)
        if seen is None:
            seen = self._loop_errors = {}
        last = seen.get(text)
        if last is not None and now - last[0] < 1800:
            last[1] += 1
            self._loop_error = (text, last[0], last[1])
            return
        again = f" (also {last[1]}x since the last message)" if last is not None and last[1] else ""
        for old in [k for k, v in seen.items() if now - v[0] > 86400]:
            seen.pop(old)
        seen[text] = [now, 0]
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
        fresh: List[Tuple[pd.Timestamp, pd.Timestamp]] = []    # the spans of the weeks read fresh in this refresh
        for week in ("thisweek", "nextweek"):          # next week's file is often missing (404) until late in the week
            cache = cache_dir / f"forexfactory_{week}.csv" if cache_dir is not None else None
            try:
                if cache is not None and cache.exists() and time.time() - cache.stat().st_mtime < max_age.total_seconds():
                    events = load_events(cache)
                    calendar.add(events)
                    if events:
                        fresh.append((min(e.time for e in events), max(e.time for e in events)))
                    continue
                events = fetch_forexfactory(week)
                calendar.add(events)
                if events:
                    fresh.append((min(e.time for e in events), max(e.time for e in events)))
            except Exception as exc:
                failed.append(f"{week}: {exc}")
                if cache is not None and cache.exists():  # an older saved week still blocks its releases (stack review B1:
                    try:                                  # a restart during an outage used to ignore it); past ones block nothing.
                        # never inside a week read fresh: last week's "nextweek" file is this week as it was listed then,
                        # and an event moved or dropped since would block its old slot all week (fixcheck4)
                        calendar.add([e for e in load_events(cache) if not any(lo <= e.time <= hi for lo, hi in fresh)])
                    except Exception:
                        pass
                continue
            if cache is not None:
                try:                                      # a file another window holds open is no failed refresh
                    save_events(events, cache)
                except Exception as exc:
                    print(f"[live] {self.symbol}: the ForexFactory week was read but not saved ({exc})")
        if len(failed) == 2 and self._news_warned != now.date():
            self._news_warned = now.date()            # once a day is enough: the loaded calendar covers the gap
            last = max((e.time for e in getattr(calendar, "events", []) or []), default=None)
            print(f"[live] {self.symbol}: news calendar refresh failed ({'; '.join(failed)}); using the events already "
                  f"loaded (data/calendar/high_impact.csv and the saved ForexFactory weeks"
                  f"{f', to {last:%Y-%m-%d}' if last is not None else ''})")

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
        attaches = getattr(self.broker, "attaches", None)
        try:
            ok, reason = check()
        except Exception as exc:
            ok, reason = False, str(exc)
        now = self.clock()
        taken = getattr(self.broker, "account_login", None)
        if ok and not self._account_start and taken and not self._account_told:
            self._account_told = True                     # connected while the terminal showed no account: say which one,
            self.notifier.send(f"ℹ️ {self.symbol}: MT5 toont nu account {taken}; dit venster handelt vanaf nu op dat account.")
        if self._listings is not None and attaches is not None and getattr(self.broker, "attaches", None) != attaches:
            self._listings = 0                            # re-attached (a restarted terminal), also inside one check that
                                                          # said ok and never showed the link down (fixcheck4)
        if not ok:
            if self._link_down is None:
                self._link_down_since = now
                print(f"[live] {self.symbol}: {reason}; waiting, trying again every scan")
            self._link_down = reason                      # the heartbeat (and the watchdog) say the current reason
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
            if self._listings is not None:
                self._listings = 0                        # a restarted terminal: its positions are listed twice again
        return ok

    def _entries_held(self) -> bool:
        """No entry until the positions were listed twice since run_forever started or the link came back (``_listings``)."""
        return self._listings is not None and self._listings < 2 and self.broker is not None

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
        sid = short_id_for(key)
        if key in self.seen or sid in self.seen_ids:
            return
        if self._entries_held():
            # not marked seen: the next scan, with a second listing of the positions, acts on it
            print(f"[live] {self.symbol}: setup {sid} waits a scan: positions listed {self._listings}x since the start or "
                  f"the reconnect")
            return
        self.seen.add(key)
        self.seen_ids[sid] = str(now)
        self.save_seen(now)
        sf = self.journal.setup_fields(setup) if self.journal is not None else {}
        if self.stale and self.settings.live.require_fresh_data:
            self.note("stale", now, id=sid, note=self.stale_text(), **sf)
            self.notifier.send(f"⏸ {self.symbol}: setup ignored, the data is stale ({self.stale_text()}); refresh the feed")
            return
        target = self.target_state() if (self.broker is not None and not self.dry_run) else None
        if target is not None and target[0] == "done":
            self.note("not_executed", now, id=sid, reason="the phase's target stands with the trading days done", **sf)
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
        ok, reason = self._can_open(setup, now)
        if not ok:
            # journaled too (15 October stack review, A10): the weekly parity check and the evening prompt read the refusal
            self.note("not_executed", now, id=sid, reason=reason, **sf)
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
        limits_before = set(self.limits)
        position = self.execute(setup, forecast, now)
        news = self.news_lines(now)
        if news:
            self.notifier.send(f"📰 {self.symbol}, the latest news (TradingView):" + "".join(f"\n• {line}" for line in news))
        placed = [self.limits[k] for k in self.limits if k not in limits_before]
        if position is not None or placed:
            # the chart of what was sent (14 October: without the approval step no setup chart went out at all)
            self.send_chart(analysis, "setup", setup=setup, forecast=forecast, limit_price=placed[0]["price"] if placed else None)
            self.dorus_review(analysis, setup, now, sid, limit_price=placed[0]["price"] if placed else None)

    def dorus_context(self, analysis: Analysis, setup: TradeSetup, now: pd.Timestamp, limit_price: Optional[float] = None) -> str:
        """The setup in words for the Dorus check: the trade, the zone and its age, the confirmation, the bias per
        timeframe, how far the entry lies from the zone and how the last day moved, in average 1H ranges."""
        d = self.spec.price_decimals
        poi, conf = setup.poi, setup.confirmation
        side = "demand" if poi.direction is Bias.BULLISH else "supply"
        local = pd.Timestamp(now).tz_localize("UTC").tz_convert(self.settings.session.timezone)
        lines = [f"Market {self.symbol}, {pd.Timestamp(now):%Y-%m-%d %H:%M} UTC ({local:%a %H:%M} Amsterdam).",
                 f"The bot went {setup.direction.name} at {setup.entry:.{d}f}"
                 + (f" (a limit order at {limit_price:.{d}f})" if limit_price is not None else "")
                 + f", stop {setup.stop:.{d}f}, target {setup.take_profit:.{d}f} ({setup.tp_source}), R:R {setup.rr:.1f}."]
        waited = ""
        if setup.touched_at is not None and poi.created_at is not None:
            waited = f", touched {setup.touched_at:%m-%d %H:%M} ({(setup.touched_at - poi.created_at) / pd.Timedelta(hours=1):.0f} h after it formed)"
        x = f", X {poi.liquidity_level:.{d}f}" if poi.liquidity_level is not None else ""
        lines.append(f"Zone: {poi.timeframe.label} {side} {poi.low:.{d}f}-{poi.high:.{d}f}{x}, formed {poi.created_at:%m-%d %H:%M}"
                     f"{waited}, visit {setup.visit_number or 1}.")
        kind = getattr(getattr(conf, "type", None), "value", "")
        lines.append(f"Confirmation: {kind} on the {conf.timeframe.label} at {pd.Timestamp(conf.timestamp):%m-%d %H:%M} UTC.")
        lines.append(f"Bias: {analysis.decision.direction.name.lower()} {analysis.decision.mode.value} ({analysis.decision.reason}); "
                     + "; ".join(f"{tf.label} {b.bias.name.lower()} (liquidity {b.liquidity_view.name.lower()}, balance "
                                 f"{b.balance_view.name.lower()})" for tf, b in sorted(analysis.biases.items(), reverse=True)))
        hourly = self._views.get(Timeframe.H_1)
        if hourly is not None and len(hourly.df) >= 24:
            h = hourly.df.tail(24)
            rng = float((h["high"] - h["low"]).mean()) or 1.0
            move = (float(h["close"].iloc[-1]) - float(h["open"].iloc[0])) * setup.direction.sign / rng
            outside = max(0.0, poi.low - setup.entry, setup.entry - poi.high) / rng
            lines.append(f"Last 24 1H candles: {move:+.1f} average 1H ranges in the trade's direction. Entry {outside:.1f} "
                         f"average 1H ranges outside the zone.")
        return "\n".join(lines)

    def dorus_review(self, analysis: Analysis, setup: TradeSetup, now: pd.Timestamp, sid: str,
                     limit_price: Optional[float] = None) -> None:
        """The Dorus check after an entry (live.dorus_check): the charts are drawn here, the API call and the Telegram line
        run beside the loop, which never waits for them. Advice only, and never fatal."""
        if self.dorus is None:
            return
        try:
            context = self.dorus_context(analysis, setup, now, limit_price)
            images = []
            from .notify.chart import render_chart
            zones = self.chart_zones(analysis, setup)
            for tf in dict.fromkeys((Timeframe.H_4, Timeframe.H_1, setup.confirmation.timeframe)):
                if tf not in self._views:
                    continue
                path = render_chart(self._views[tf], f"{self.settings.live.charts_dir}/{self.symbol}_{tf.label}_dorus.png",
                                    pois=zones, setup=setup, title=f"{self.symbol} {tf.label}", lookback=self.settings.live.chart_lookback,
                                    price_decimals=self.spec.price_decimals)
                images.append((f"{self.symbol} {tf.label} chart", Path(path).read_bytes()))
        except Exception as exc:
            print(f"[live] {self.symbol}: Dorus check could not be prepared ({exc})")
            return
        row = {"time": str(now), "symbol": self.symbol, "id": sid, "direction": setup.direction.name,
               "zone_tf": setup.poi.timeframe.label, "entry": limit_price if limit_price is not None else setup.entry,
               "stop": setup.stop, "target": setup.take_profit, "rr": round(setup.rr, 2)}
        check, notifier, journal_path = self.dorus, self.notifier, self.settings.live.journal_path

        def work() -> None:
            import html
            from .notify.dorus_check import log_verdict
            try:
                verdict = check.review(context, images)
            except Exception as exc:
                print(f"[live] {self.symbol}: Dorus check failed ({exc})")
                return
            notifier.send(f"🧭 Dorus-check {self.symbol} {setup.direction.name.lower()}: {verdict.icon} {verdict.verdict} - "
                          f"{html.escape(verdict.reason)}")
            if journal_path:
                try:
                    log_verdict(Path(journal_path).parent / "dorus_checks.csv", {**row, "verdict": verdict.verdict, "reason": verdict.reason})
                except Exception as exc:
                    print(f"[live] {self.symbol}: Dorus check not logged ({exc})")

        if self.dorus_wait:
            work()
        else:
            import threading
            threading.Thread(target=work, daemon=True, name=f"dorus-{self.symbol}").start()

    def news_lines(self, now: Optional[pd.Timestamp] = None) -> List[str]:
        """The latest TradingView headlines of this market (live.news_headlines): context for the trader, never an input
        to a trade; none without TRADINGVIEW_MCP_TOKEN, when off, or when the read fails."""
        if self.headlines is None:
            return []
        return self.headlines.lines(self.spec.tradingview_symbol or self.symbol, now if now is not None else self.clock())

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

    def target_state(self) -> Optional[Tuple[str, Optional[int], float]]:
        """With prop_firm.stop_at_target and risk.target_pct: ``("done", days, balance)`` once the closed balance stands at
        the phase's target and min_trading_days are logged, ``("finish", days, balance)`` while days are missing (None =
        unknown, counted as missing); None when off, without a target, under it, or when the balance cannot be read."""
        p, r = self.settings.prop_firm, self.settings.risk
        if not getattr(p, "stop_at_target", False) or not r.target_pct or self.broker is None:
            return None
        if self._target_cache is not None and self._target_cache[0] == self._scan_id:
            return self._target_cache[1]                  # one answer per scan: the guard and the order see the same state
        try:
            balance = float(self.broker.balance())
        except Exception:
            return None                                   # not cached: the next call asks again
        result = None
        if balance >= self.settings.account_size * (1.0 + float(r.target_pct) / 100.0):
            counter = getattr(self.broker, "trading_days", None)
            days = None
            if callable(counter):
                try:
                    days = counter(p.day_timezone)
                    days = int(days) if days is not None else None
                except Exception:
                    days = None
            if days is not None:
                self._days_known = max(days, self._days_known or 0)
            days = self._days_known                       # a terminal that does not answer keeps the last count
            state = "done" if days is not None and days >= int(p.min_trading_days) else "finish"
            result = (state, days, balance)
        self._target_cache = (self._scan_id, result)
        return result

    def stake_params(self, setup: Optional[TradeSetup] = None):
        """The risk parameters of the next trade: the profile's risk lowered by risk.drawdown_steps, the setup's multipliers,
        and the finish stake (prop_firm.finish_risk_pct) while the phase's target stands and trading days are missing."""
        from .strategy.risk import confirmation_label, setup_risk, stepped_risk
        params = stepped_risk(self.settings.risk, self.broker.balance(), self.settings.account_size)
        params = setup_risk(params, setup.poi.timeframe if setup is not None else None,
                            setup.bias_combo if setup is not None else None,
                            confirmation_label(setup.confirmation) if setup is not None else None,
                            getattr(setup, "neutral_timeframes", ()) if setup is not None else (),
                            getattr(setup, "aligned_count", 0) if setup is not None else 0,
                            rr=getattr(setup, "rr", 0.0) if setup is not None else 0.0)
        target = self.target_state()
        if target is not None and target[0] == "finish":
            params = replace(params, risk_pct=float(self.settings.prop_firm.finish_risk_pct))
        return params

    def planned_risk(self, setup: Optional[TradeSetup] = None) -> Optional[float]:
        """What the next trade risks at its stop (account currency): the profile's risk, lowered by risk.drawdown_steps, times
        the profile's stake and the setup's zone multiplier (setup B). ``None`` when the terminal did not answer: the
        guard's worst case then cannot be known, and the caller refuses the entry (8 October: a 0 here let a trade
        past the day's limit)."""
        try:
            return float(self.broker.equity()) * self.stake_params(setup).risk_pct / 100.0
        except Exception:
            return None

    def announce_target(self, now: pd.Timestamp) -> None:
        """Once a day for the account (the windows share a file next to the journal): the phase's target stands, and what
        the windows do about it (prop_firm.stop_at_target)."""
        target = self.target_state()
        if target is None:
            return
        state, days, balance = target
        p, goal = self.settings.prop_firm, float(self.settings.risk.target_pct)
        day = pd.Timestamp(now).tz_localize("UTC").tz_convert(p.day_timezone).date()
        key = f"{day}:{state}"
        if self._target_told == key:
            return
        self._target_told = key
        path = Path(self.settings.live.journal_path).parent / "target_notice.json" if self.settings.live.journal_path else None
        if path is not None:
            try:
                with AccountLock(self.lock_path, timeout=3.0):    # read and write as one step: one message for the account
                    if path.exists() and json.loads(path.read_text(encoding="utf-8")).get("key") == key:
                        return                                # another window of the account said it today
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps({"key": key, "by": self.symbol}), encoding="utf-8")
            except Exception as exc:
                print(f"[live] {self.symbol}: target notice file ({exc})")
        self.note("target", now, note=f"{state}: balance {balance:,.2f}, {days if days is not None else '?'} trading day(s)")
        if state == "done":
            self.notifier.send(f"🏁 Doel +{goal:g}% bereikt: balans {balance:,.0f}, {days} handelsdagen. De bot opent niets nieuws "
                               f"meer; open posities lopen af. Zodra alles dicht is: vraag in het FTMO-dashboard de volgende fase aan.")
        else:
            have = "?" if days is None else str(days)
            self.notifier.send(f"🏁 Doel +{goal:g}% bereikt: balans {balance:,.0f}, {have} van {p.min_trading_days} handelsdagen. "
                               f"Nieuwe trades op {p.finish_risk_pct:g}% tot de {p.min_trading_days} dagen er zijn.")

    NO_PLANNED_RISK = "the trade's risk could not be computed (the terminal did not answer); not executed (this setup is not retried)"

    def _can_open(self, setup: TradeSetup, now: pd.Timestamp) -> Tuple[bool, str]:
        """The guard's answer for ``setup``, a refusal when its risk is unknown or a position of the account has no stop
        (the guard would count that position as no risk), or when the phase's target stands with the trading days done."""
        target = self.target_state()
        if target is not None and target[0] == "done":
            return False, (f"the phase's target +{float(self.settings.risk.target_pct):g} % stands with {target[1]} trading day(s): "
                           f"no new trade; the open ones run, then request the next phase")
        risk = self.planned_risk(setup)
        if risk is None:
            return False, self.NO_PLANNED_RISK
        try:
            stopless = [p.id for p in self.broker.open_positions() if getattr(p, "status", "filled") == "filled" and not p.stop]
        except Exception:
            stopless = []
        if stopless:
            return False, f"position(s) {', '.join(stopless)} without a stop on the server: no new trade until every position has one"
        # as the backtest: no new setup in this market while one of its limit entries rests, whatever the per-market slots
        # (with prop_firm.max_open_per_symbol 2 a second position comes from a filled trade, never from a second limit)
        working = getattr(self.broker, "limit_orders", None)
        if callable(working):
            try:
                resting = working(self.symbol)
            except Exception as exc:
                return False, f"the resting limit entries could not be read ({exc})"
            if resting:
                return False, f"a limit entry is working in {self.symbol} ({resting[0].id})"
        return self.guard.can_open(self.broker, now, self.symbol, new_risk=risk)

    def stake_note(self, risk_params) -> str:
        """Why a trade risks other than the profile's risk_pct, for the fill message: the balance under the start (drawdown
        steps), near the phase's target (target protection), the zone's or the profile's multiplier."""
        from .strategy.risk import stepped_risk
        base = self.settings.risk
        if abs(risk_params.risk_pct - base.risk_pct) < 1e-12:
            return ""
        target = self.target_state()
        if target is not None and target[0] == "finish":
            days = "?" if target[1] is None else target[1]
            return (f" ({risk_params.risk_pct:g} % on this trade: the phase's target stands, {days} of "
                    f"{self.settings.prop_firm.min_trading_days} trading days)")
        parts = []
        try:
            balance = float(self.broker.balance())
            stepped = stepped_risk(base, balance, self.settings.account_size).risk_pct
        except Exception:
            balance, stepped = None, base.risk_pct
        if stepped < base.risk_pct:
            parts.append("near the target" if balance is not None and balance >= self.settings.account_size else "balance below the start")
        if stepped > 0 and abs(risk_params.risk_pct / stepped - 1.0) > 1e-9:
            parts.append(f"x{risk_params.risk_pct / stepped:g} for its zone, its bias combination, its confirmation, a 50/50 timeframe, "
                         f"a far target or the profile's stake")
        return f" ({risk_params.risk_pct:g} % on this trade: {', '.join(parts) or 'adjusted'})"

    def _open_locked(self, setup: TradeSetup, now: pd.Timestamp):
        """The checks and the order, inside the account lock: the message to send on a refusal, else
        ``(position, setup id, risk amount, risk params, resize note, margin note)``."""
        sid = short_id_for((setup.poi.key, str(setup.confirmation.timestamp)))
        ok, reason = self._can_open(setup, now)
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
        from .strategy.risk import confirmation_label, resize_at, setup_risk, stepped_risk
        wrong_side = (setup.direction.sign > 0 and price <= setup.stop) or (setup.direction.sign < 0 and price >= setup.stop)
        risk_params = self.stake_params(setup)
        equity = self.broker.equity()
        lots, risk_amount, risk_distance, rr_now, _ = resize_at(price, setup.stop, setup.take_profit, equity,
                                                                self.spec, risk_params)
        if wrong_side or rr_now < self.settings.risk.min_rr:
            self.note("not_executed", now, id=sid, price=float(price), rr=float(rr_now), reason="price moved, R:R below minimum")
            return (f"⛔ {self.symbol}: not executed - price moved to {price:.{self.spec.price_decimals}f}, "
                    f"R:R now 1:{rr_now:.1f} (min {self.settings.risk.min_rr:.0f})")
        planned_lots = lots
        floor = self._min_stop_pips()
        if abs(price - setup.stop) >= 0.5 * floor * self.spec.pip_size:
            floor = 0.0                                  # frozen sizing: only a stop under half the minimum (the stated fix)
        floored, floor_note = self._floored_lots(price, setup.stop, lots, equity, risk_params, floor)
        if floor_note:
            risk_amount *= floored / lots
            lots = floored
        if lots <= 0:
            why = ("the minimum stop's lots are under the minimum lot" if floor_note else
                   "stop too wide for the minimum lot")
            self.note("not_executed", now, id=sid, price=float(price), reason=why if floor_note else f"{why} at this price")
            return f"⛔ {self.symbol}: not executed - {why} at {price:.{self.spec.price_decimals}f}"
        frac = float(getattr(self.settings.risk, "limit_entry_fraction", 0.0) or 0.0)
        at_level = str(getattr(self.settings.risk, "limit_entry_at", "") or "")
        if frac > 0 or at_level == "break_level":        # the same checks at the market price first, as the backtest makes them
            return self._place_limit(setup, now, sid, price, frac, risk_params, at_level)
        resized = f"; lots {setup.lots:.2f} -> {lots:.2f} at {price:.{self.spec.price_decimals}f}" if abs(lots - setup.lots) > 1e-9 else ""
        if floor_note:
            resized += f"; {floor_note}"
        if risk_params.risk_pct != self.settings.risk.risk_pct:
            finishing = self.target_state()
            resized += (f"; risk {risk_params.risk_pct:g} % (the phase's target stands: the finish stake)"
                        if finishing is not None and finishing[0] == "finish" else
                        f"; risk {risk_params.risk_pct:g} % (drawdown steps, stake or zone multiplier)")
        margin_note = f" ({floor_note})" if floor_note else ""
        room = self.margin_room(setup.direction, price)
        if room is not None and lots > room[0] + 1e-9:
            fit = round(math.floor(room[0] / self.spec.lot_step + 1e-9) * self.spec.lot_step, 4)
            if fit < self.spec.min_lot:
                self.note("not_executed", now, id=sid, price=float(price), reason=f"margin: {room[1]:,.0f} available, "
                          f"{lots:.2f} lots wanted, {room[0]:.3f} fit")
                return (f"⛔ {self.symbol}: not executed - not enough margin for the minimum lot "
                        f"({room[1]:,.0f} available, {self.spec.min_lot:g} lots needed)")
            margin_note += f" (margin: lots cut from {lots:.2f}, risk {100 * fit / planned_lots:.0f} % of planned)"
            resized += f"; lots {lots:.2f} -> {fit:.2f}: margin ({room[1]:,.0f} available)"
            risk_amount *= fit / lots
            lots = fit
        # the lock at the phase's target: a nearer take-profit on the order, after the R:R checks above, which stay on the
        # setup's own target (setup.take_profit is never changed: the journal's plan, a retry and the min R:R read it)
        meta = {"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value}",
                "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value}
        take_profit = setup.take_profit
        try:
            lock = self._order_lock(setup.direction, price, lots, setup.take_profit, now)
        except Exception as exc:                         # the order goes out with its own target; the next scan tries again
            print(f"[live] {self.symbol}: target lock for the order failed ({exc}); its own target goes out")
            lock = None
        if lock is not None:
            take_profit = lock[0]
            meta.update({"own_take_profit": float(setup.take_profit), "lock_need": float(lock[1]), "lock_days": int(lock[2])})
            resized += f"; target lock: TP {setup.take_profit:.{self._lock_decimals()}f} -> {take_profit:.{self._lock_decimals()}f}"
        try:
            pos = self.broker.place_market_order(
                self.symbol, setup.direction, lots, setup.stop, take_profit, risk_amount,
                risk_distance, setup.breakeven_r, meta=meta,
                price=price, ts=self.fill_stamp(now), price_is_fill=True,
            )
        except Exception as exc:
            self.note("not_executed", now, id=sid, reason=f"order failed: {exc}")
            return f"⛔ {self.symbol}: order failed - {exc}"
        return pos, sid, risk_amount, risk_params, resized, margin_note

    def _min_stop_pips(self) -> float:
        return float(getattr(self.settings.risk, "min_stop_pips", 0.0) or 0.0)

    def _floored_lots(self, price: float, stop: float, lots: float, equity: float, risk_params, floor_pips: float):
        """``(lots, note)``: the lots, at most those of a stop ``floor_pips`` away, and a note when that cut them. The
        engine keeps every stop at least ``risk.min_stop_pips`` from the confirmation close, but the order goes out up to a
        minute later at the tick and was sized on the distance left: a price that ran almost to the stop gave a 0.8-pip
        stop at twice the lots, a stop the research never took (15 October stack review, A7). The stop stays where it is
        and the trade is taken, as the backtest takes it; only its size is held to the research's smallest stop, so the
        money at the stop comes out under the budget, never over it."""
        pip = self.spec.pip_size
        distance = abs(float(price) - float(stop))
        if floor_pips <= 0 or lots <= 0 or pip <= 0 or distance >= floor_pips * pip - 1e-12:
            return lots, ""
        from .strategy.risk import size_position
        far = float(price) - floor_pips * pip if float(stop) < float(price) else float(price) + floor_pips * pip
        floored = size_position(equity, float(price), far, self.spec, risk_params)[0]
        if floored >= lots - 1e-9:
            return lots, ""
        return floored, (f"lots {lots:.2f} -> {floored:.2f}: the stop is {distance / pip:.1f} pips away, sized on the "
                         f"{floor_pips:g}-pip minimum")

    # ------------------------------------------------------------ limit entries (risk.limit_entry_fraction)
    def _place_limit(self, setup: TradeSetup, now: pd.Timestamp, sid: str, price: float, frac: float, risk_params, at_level: str = ""):
        """Inside the account lock: a limit ``frac`` of the way from the executable price back toward the stop, or on the
        balance level the shift closed through (``at_level`` break_level), sized on the smaller stop, the margin checked;
        returns ("limit", order, sid) or the refusal to send."""
        from .strategy.risk import limit_entry_price, resize_at
        d = self.spec.price_decimals
        raw, mode = limit_entry_price(setup, price, frac, at_level)
        limit = self.spec.round_price(raw)
        self._limit_mode = mode
        self._limit_note = ""
        self._limit_locked = False
        equity = self.broker.equity()
        lots, risk_amount, risk_distance, rr, _ = resize_at(limit, setup.stop, setup.take_profit, equity,
                                                            self.spec, risk_params)
        if rr < self.settings.risk.min_rr:
            self.note("not_executed", now, id=sid, price=float(limit), rr=float(rr), reason="limit: R:R below minimum")
            return f"⛔ {self.symbol}: not executed - R:R at the limit {limit:.{d}f} is 1:{rr:.1f} (min {self.settings.risk.min_rr:g})"
        # the research's smallest limit stop: the fraction's share of the minimum (on the balance level: no floor known)
        share = 0.0 if mode == "limit break_level" else 1.0 - (frac if frac > 0 else 0.25)
        floor = share * self._min_stop_pips()
        if abs(limit - setup.stop) >= 0.5 * self._min_stop_pips() * self.spec.pip_size:
            floor = 0.0                                  # frozen sizing: only a stop under half the minimum (the stated fix)
        floored, floor_note = self._floored_lots(limit, setup.stop, lots, equity, risk_params, floor)
        if floor_note:
            risk_amount *= floored / lots
            lots = floored
            self._limit_note = floor_note
        if lots <= 0:
            why = ("the minimum stop's lots are under the minimum lot" if floor_note else
                   "stop too wide for the minimum lot")
            self.note("not_executed", now, id=sid, price=float(limit), reason=f"limit: {why}")
            return f"⛔ {self.symbol}: not executed - {why} at the limit {limit:.{d}f}"
        room = self.margin_room(setup.direction, limit)
        if room is not None and lots > room[0] + 1e-9:
            fit = round(math.floor(room[0] / self.spec.lot_step + 1e-9) * self.spec.lot_step, 4)
            if fit < self.spec.min_lot:
                self.note("not_executed", now, id=sid, price=float(limit), reason=f"limit: margin {room[1]:,.0f} available")
                return f"⛔ {self.symbol}: not executed - not enough margin for the minimum lot ({room[1]:,.0f} available)"
            self._limit_note = "; ".join(x for x in (self._limit_note, f"lots {lots:.2f} -> {fit:.2f}: margin "
                                                     f"({room[1]:,.0f} available)") if x)
            risk_amount *= fit / lots
            lots = fit
        expires = pd.Timestamp(now) + pd.Timedelta(minutes=int(self.settings.risk.limit_entry_minutes))
        take_profit = setup.take_profit                  # the lock at the phase's target, after the R:R check on the own target
        try:
            lock = self._order_lock(setup.direction, limit, lots, setup.take_profit, now, reference=limit)
        except Exception as exc:
            print(f"[live] {self.symbol}: target lock for the limit failed ({exc}); its own target goes out")
            lock = None
        self._limit_locked = lock is not None
        if lock is not None:
            take_profit = lock[0]
            self._limit_note = "; ".join(x for x in (self._limit_note, f"target lock: TP {setup.take_profit:.{d}f} -> "
                                                     f"{take_profit:.{self._lock_decimals()}f}") if x)
        try:
            order = self.broker.place_limit_order(
                self.symbol, setup.direction, lots, limit, setup.stop, take_profit, risk_amount, risk_distance,
                setup.breakeven_r, expires, ts=self.fill_stamp(now),
                meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value} L",
                      "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value})
        except Exception as exc:
            self.note("not_executed", now, id=sid, reason=f"limit order failed: {exc}")
            if "not sent again" in str(exc):             # a lost reply: the order may still reach the server and fill
                mark_traded = getattr(self.engine, "mark_traded", None)
                if mark_traded is not None:
                    mark_traded(self.symbol, setup.poi.key, getattr(setup, "visit_number", None))
                    self.save_traded()
            return f"⛔ {self.symbol}: limit order failed - {exc}"
        return "limit", order, sid

    def _limit_placed(self, setup: TradeSetup, order, sid: str, now: pd.Timestamp) -> None:
        self.guard.record_trade(now)
        mark_traded = getattr(self.engine, "mark_traded", None)
        if mark_traded is not None:                      # the zone's visit is used, filled or not (as the backtest counts it)
            mark_traded(self.symbol, setup.poi.key, getattr(setup, "visit_number", None))
            self.save_traded()
        # "take_profit" stays the setup's own target (the "target traded first" cancel reads it, as the backtest's); a nearer
        # one the lock at the phase's target put on the order is "lock_tp"
        locked = bool(getattr(self, "_limit_locked", False))
        self.limits[order.id] = {"sid": sid, "direction": order.direction.name, "price": float(order.price),
                                 "stop": float(order.stop), "lots": float(order.lots),
                                 "take_profit": float(setup.take_profit if locked else order.take_profit),
                                 "risk_amount": float(order.risk_amount), "placed_at": pd.Timestamp(now),
                                 "expires_at": pd.Timestamp(order.expires_at)}
        if locked:
            self.limits[order.id].update({"lock_tp": float(order.take_profit), "lock_told": True})
        self.save_limits()
        d = self.spec.price_decimals
        side = "BUY" if order.direction is Direction.LONG else "SELL"
        mode = getattr(self, "_limit_mode", "") or f"limit {float(self.settings.risk.limit_entry_fraction):g}"
        where = "on the balance level the shift closed through" if mode == "limit break_level" else \
            f"{float(mode.split()[1]) if len(mode.split()) > 1 else 0:.0%} back toward the stop"
        floor_note = getattr(self, "_limit_note", "")
        self.note("limit_placed", now, id=order.id, direction=order.direction.name, entry=float(order.price), stop=float(order.stop),
                  take_profit=float(order.take_profit), lots=float(order.lots), risk=float(order.risk_amount),
                  note=f"setup {sid}; {mode}; valid until {order.expires_at:%H:%M} UTC" + (f"; {floor_note}" if floor_note else ""))
        dt = self._lock_decimals() if locked else d
        self.notifier.send(f"📌 {self.symbol} {side} LIMIT {order.lots:.2f} lots @ {order.price:.{d}f} ({where})  SL {order.stop:.{d}f}  "
                           f"TP {order.take_profit:.{dt}f}  risk {order.risk_amount:,.0f}  valid until {order.expires_at:%H:%M} UTC (id {order.id})"
                           + (f"\n({floor_note})" if floor_note else "")
                           + (f"\n🔐 Doel-lock: TP op de prijs waar de gesloten balans +{float(self.settings.risk.target_pct):g}% "
                              f"haalt (eigen doel {float(setup.take_profit):.{d}f}); de stop blijft" if locked else ""))

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
            tmp = self.limits_path.with_suffix(".tmp")       # a window killed mid-write must not lose its limits' records
            tmp.write_text(json.dumps(rows), encoding="utf-8")
            os.replace(tmp, self.limits_path)
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
        cancelled; one the server dropped is reported. A resting limit of this market the window has no record of is
        cancelled, at every scan (15 October stack review, A12): one left from before a restart without its file, or one
        that reached the server while its reply was lost (the setup was then reported as failed and never counted)."""
        if self.broker is None or self.dry_run:
            return
        # a terminal that has just (re)started may list no orders yet: no stray sweep and no "gone" until the positions were
        # listed twice (fixcheck4: its own resting limit read "gone" and the next scan cancelled it as a stray)
        held = self._entries_held()
        try:
            for order in ([] if held else self.broker.limit_orders(self.symbol)):
                if order.id in self.limits:
                    continue
                when = "at the start" if not self._limits_checked else "now"
                retry = getattr(self, "_stray_retry", {}).get(order.id)
                if retry is not None and now < retry[1]:
                    continue                    # a refused cancel backs off as a refused close does (fixcheck2 s04 a)
                try:
                    self.broker.cancel_limit(order.id)
                except Exception as exc:
                    tries = (retry[0] if retry is not None else 0) + 1
                    self.__dict__.setdefault("_stray_retry", {})[order.id] = (
                        tries, now + pd.Timedelta(minutes=15 if tries >= 3 else 1))
                    print(f"[live] {self.symbol}: cancel of the unrecorded limit {order.id} failed ({exc}); trying again later")
                    if order.id not in self._stray_warned:
                        self._stray_warned.add(order.id)
                        self.notifier.send(f"⚠️ {self.symbol}: limit {order.id} is not this window's and could not be "
                                           f"cancelled ({exc}); trying again (every 15 min after three tries), look at MT5's Trade tab")
                    continue
                self.note("limit_cancelled", now, id=order.id, reason=f"no record of it ({when})")
                self.notifier.send(f"🚫 {self.symbol}: limit {order.id} cancelled {when} - this window has no record of it")
            if not held:
                self._limits_checked = True
        except Exception as exc:
            print(f"[live] {self.symbol}: could not check the resting limit orders ({exc})")
        changed = False
        target = self.target_state() if self.limits else None
        finish_cap = None
        if target is not None:          # a limit placed before the target stands carries the full stake: only finish-sized ones stay
            try:
                finish_cap = float(self.broker.equity()) * float(self.settings.prop_firm.finish_risk_pct) / 100.0 * 1.05
            except Exception:   # the equity unread (since A15 this runs in such a scan): the balance target_state just read
                finish_cap = float(target[2]) * float(self.settings.prop_firm.finish_risk_pct) / 100.0 * 1.05
        for oid, info in list(self.limits.items()):
            try:
                state, pos = self.broker.limit_state(oid)
            except Exception as exc:
                print(f"[live] {self.symbol}: limit {oid} state unknown ({exc}); asking again next scan")
                continue
            if state == "pending":
                reason = "expired" if now >= info["expires_at"] else "the target traded first" if self._target_traded(info) else None
                if reason is None and target is not None and (target[0] == "done" or float(info.get("risk_amount", 0.0)) > finish_cap):
                    reason = "the phase's target stands"
                if reason is None:
                    continue
                try:
                    self.broker.cancel_limit(oid)
                except Exception as exc:
                    print(f"[live] {self.symbol}: cancel of limit {oid} failed ({exc}); trying again next scan")
                    continue
                info["cancel_reason"] = reason                      # a later "gone" is this cancel (fixcheck2 s07 a)
                try:
                    state, pos = self.broker.limit_state(oid)       # it may have filled while it was being cancelled
                except Exception as exc:
                    print(f"[live] {self.symbol}: limit {oid} cancelled ({reason}), its state unknown ({exc}); asking again next scan")
                    changed = True
                    continue
                if state != "filled":
                    self.limits.pop(oid); changed = True
                    self.note("limit_cancelled", now, id=oid, reason=reason)
                    self.notifier.send(f"🚫 {self.symbol}: limit {oid} cancelled - {reason}")
                    continue
            if state == "filled":
                self.limits.pop(oid); changed = True
                self._limit_filled(oid, info, pos, now)
            elif state == "gone" and held:
                continue                                  # not listed by a terminal that may not be synced: ask again
            elif state == "gone" and info.get("cancel_reason"):
                self.limits.pop(oid); changed = True
                self.note("limit_cancelled", now, id=oid, reason=info["cancel_reason"])
                self.notifier.send(f"🚫 {self.symbol}: limit {oid} cancelled - {info['cancel_reason']}")
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
        locked = info.get("lock_tp") is not None         # the lock's take-profit came with the fill: its own target goes along
        if locked or info.get("lock_told"):
            self.own_targets[pos.id] = {"take_profit": float(info["take_profit"]), "set": float(pos.take_profit) if locked else None,
                                        "told": bool(info.get("lock_told"))}
            self.save_own_targets()
        if locked:
            self.note("target_lock", now, id=pos.id, direction=pos.direction.name, entry=float(pos.entry),
                      take_profit=float(pos.take_profit), lots=float(pos.lots),
                      note=f"locked at the limit {oid}: own target {float(info['take_profit']):.{self._lock_decimals()}f}")
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
        locked = self._lock_at_order(pos, now)
        if filled:
            stepped = self.stake_note(risk_params)
            self.notifier.send(f"💸 {self.symbol} {side} filled {pos.lots:.2f} lots @ {pos.entry:.{d}f}  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  risk {pos.risk_amount:,.0f}{stepped}{margin_note}  "
                               f"(id {pos.id}){locked}")
        else:
            self.unconfirmed[pos.id] = pos
            self.notifier.send(f"📨 {self.symbol} {side} {pos.lots:.2f} lots submitted, fill not confirmed yet  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  (id {pos.id}){locked}")
        return pos

    def _lock_at_order(self, pos: Position, now: pd.Timestamp) -> str:
        """A market order that went out with the lock's take-profit: the trade's own target recorded (a restart moves the lock
        back toward it, never past it), a journal row, and the line for the fill message ("" without a lock)."""
        own = pos.meta.get("own_take_profit")
        if own is None:
            return ""
        self.own_targets[pos.id] = {"take_profit": float(own), "set": float(pos.take_profit), "told": True}
        self.save_own_targets()
        d = self._lock_decimals()
        self.note("target_lock", now, id=pos.id, direction=pos.direction.name, entry=float(pos.entry),
                  take_profit=float(pos.take_profit), lots=float(pos.lots),
                  note=f"locked at the order: own target {float(own):.{d}f}; needs {float(pos.meta.get('lock_need', 0.0)):,.2f} "
                       f"with costs; {pos.meta.get('lock_days', '?')} trading day(s)")
        return (f"\n🔐 Doel-lock: TP op de prijs waar de gesloten balans +{float(self.settings.risk.target_pct):g}% haalt "
                f"(eigen doel {float(own):.{d}f}); de stop blijft")

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
        if self._listings is not None:
            self._listings += 1
        hold = self.settings.exits.max_hold_hours
        ts_hours = float(getattr(self.settings.exits, "time_stop_hours", 0.0) or 0.0)
        ts_r = float(getattr(self.settings.exits, "time_stop_r", -0.5))
        weekend = self.settings.prop_firm.weekend_close
        day_close = getattr(self.settings.exits, "day_close", "")
        if (hold or ts_hours or weekend or day_close) and not callable(getattr(self.broker, "on_candle", None)):
            from .strategy.exits import day_close_cutoff_after, weekend_cutoff_after
            now = self.clock()
            shut = self._exit_series(views) is None      # no fresh bars from the terminal: the market is shut (or the feed down)
            for pid, pos in list(open_by_id.items()):
                if getattr(pos, "status", "filled") != "filled" or pos.opened_at is None:
                    continue
                if hold and now - pd.Timestamp(pos.opened_at) >= pd.Timedelta(hours=float(hold)):
                    reason, why = "time", f"after {hold:g} h"
                elif ts_hours and now - pd.Timestamp(pos.opened_at) >= pd.Timedelta(hours=float(ts_hours)) and self._r_now(pos) is not None \
                        and self._r_now(pos) <= float(ts_r):
                    reason, why = "time_stop", f"at {self._r_now(pos):+.2f}R after {ts_hours:g} h (time stop under {ts_r:+g}R)"
                elif day_close and now >= day_close_cutoff_after(pos.opened_at, day_close, self.settings.session.timezone):
                    reason, why = "day_close", f"before the daily break ({day_close} {self.settings.session.timezone})"
                elif weekend and now >= weekend_cutoff_after(pos.opened_at, weekend):
                    reason, why = "weekend", f"before the weekend (Friday {weekend} New York)"
                else:
                    continue
                retry_at = pos.meta.get(f"{reason}_exit_retry_at")
                # backs off only while the market is shut AND the server said so (10018): a feed that failed while the
                # market trades reads as shut too, and a funded Friday close refused for 3 minutes then waited 15
                # (fixcheck2 loop_changes s11 D)
                if shut and pos.meta.get(f"{reason}_exit_closed") and retry_at is not None and now < retry_at:
                    continue
                try:
                    self.broker.close_position(pid, reason, ts=now)
                    open_by_id.pop(pid)
                    self.note(f"{reason}_exit", now, id=pid, note=why)
                except Exception as exc:
                    # three quick tries, then every 15 minutes: a market that is closed (NAS100's 48 h exit falling on a
                    # Saturday) refused about 2,000 closes a weekend at one a scan, and FTMO counts server requests
                    # ("hyperactivity", 15 October stack review)
                    tries = int(pos.meta.get(f"{reason}_exit_tries", 0)) + 1
                    pos.meta[f"{reason}_exit_tries"] = tries
                    closed = "retcode 10018" in str(exc)          # TRADE_RETCODE_MARKET_CLOSED
                    pos.meta[f"{reason}_exit_closed"] = closed
                    pos.meta[f"{reason}_exit_retry_at"] = now + pd.Timedelta(minutes=15 if shut and closed and tries >= 3 else 1)
                    if not pos.meta.get(f"{reason}_exit_failed_sent"):
                        pos.meta[f"{reason}_exit_failed_sent"] = True
                        self.notifier.send(f"⚠️ {self.symbol}: closing {pid} {why} failed ({exc}); trying again every scan "
                                           f"while the market trades, every 15 min while it is shut")
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
        lowest = self._exit_series(views)
        last = lowest.last if lowest is not None else None
        listed_before, self._positions_listed = getattr(self, "_positions_listed", False), True
        for pos in open_by_id.values():
            # one opened before this window started is a restored one, even when the first listing missed it (fixcheck3)
            opened_since_start = pos.opened_at is not None and pd.Timestamp(pos.opened_at) >= self._started_at
            if (pos.id not in self.known_positions and pos.id not in self.limits and listed_before   # a recorded limit's
                    and str(pos.meta.get("limit_id", "")) not in self.limits                     # fill (by its order) is
                    and pos.meta.get("restored") and opened_since_start):                        # manage_limits'
                # its risk and target as a fill row has them: the forward record counts its R (fixcheck3)
                self.note("found", self.clock(), id=pos.id, direction=pos.direction.name, entry=float(pos.entry),
                          stop=float(pos.stop), take_profit=float(pos.take_profit), lots=float(pos.lots),
                          risk=float(pos.risk_amount), note="on the server without this window's record")
                self.notifier.send(f"⚠️ {self.symbol}: position {pos.id} ({pos.direction.name} {pos.lots:.2f} lots @ "
                                   f"{pos.entry:.{d}f}) is on the server without this window's record (a lost order "
                                   f"reply?); its exits are managed from now on")
            self.known_positions.setdefault(pos.id, pos)
            if getattr(pos, "status", "filled") != "filled":
                continue
            if not pos.stop and not pos.meta.get("no_stop_sent"):    # 8 October: the guard counts such a position as no
                pos.meta["no_stop_sent"] = True                        # risk; say so at once, not only in the 22:05 report
                self.note("no_stop", id=pos.id)
                self.notifier.send(f"🚨 {self.symbol}: position {pos.id} has NO STOP on the server; no new trade until it has "
                                   f"one (set it in the terminal)")
            if pos.breakeven_done:
                continue
            if pos.breakeven_r <= 0 or pos.risk_distance <= 0:
                continue                                   # no trigger or no risk known: never move a stop on a guess
            if last is None:
                continue                                   # no fresh bars from the terminal in this scan: the check waits
            retry_at = pos.meta.get("breakeven_retry_at")
            if retry_at is not None and last.timestamp < retry_at:
                continue
            # every candle since the last look (or the fill), not only the newest: a touch of the trigger in the last
            # seconds of a candle between two polls, or while the window was down, counts as in the backtest. Never a
            # candle that opened before the fill, and never candles older than the last look (15 October stack review: a
            # scan on the cached candles of 1 October set the checkpoint back, and the next scan read 41 hours of candles
            # from before the fill and moved the stop on a high it never saw)
            checked = pos.meta.get("be_checked_until")
            opened = pd.Timestamp(pos.opened_at) if pos.opened_at is not None else None
            if opened is not None and not pos.meta.get("limit_id") and not str(pos.meta.get("comment", "")).endswith(" L"):
                start = opened.floor(f"{lowest.timeframe.minutes}min")
                if opened - start <= pd.Timedelta(seconds=90):     # a market fill at the scan after a close: its own candle
                    opened = start                                 # counts, as in the backtest (entry at that candle's open)
            since = checked or opened
            if since is not None and opened is not None:
                since = max(pd.Timestamp(since), opened)
            k0 = len(lowest) - 1
            if since is not None:
                k0 = lowest.index_at_or_after(pd.Timestamp(since))
                if k0 >= len(lowest):
                    continue                               # no candle since the last look (or since the fill) yet
            extreme = float(lowest.high[k0:].max()) if pos.direction.sign > 0 else float(lowest.low[k0:].min())
            # the newest candle may still be forming: again next scan; the checkpoint only moves forward
            pos.meta["be_checked_until"] = last.timestamp if checked is None else max(pd.Timestamp(checked), last.timestamp)
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

    def _exit_series(self, views: Dict[Timeframe, CandleSeries]) -> Optional[CandleSeries]:
        """The candles the break-even check reads: the lowest timeframe whose bars came from the terminal (or the feed) in
        this scan and are not stale. Never the TradingView cache: when MT5's 5m and 15m bars failed, the check read the
        cache's 15m candles of 1 October and moved stops to break-even on prices long gone (15 October stack review). None
        when no such timeframe exists: the check waits for the next scan."""
        report = getattr(self.fetch, "report", None)
        sources = dict(getattr(report, "sources", None) or {})
        live = [tf for tf, series in views.items() if len(series) and sources.get(tf, "broker") != "cache"]
        if not live:
            return None
        tf = min(live)
        if tf in (self.stale or {}):
            return None
        return views[tf]

    def _r_now(self, pos) -> Optional[float]:
        """The position's R at the price it would close at now (the bid for a long, the ask for a short); None without a price."""
        try:
            price = self.broker.fill_price(self.symbol, Direction.SHORT if pos.direction is Direction.LONG else Direction.LONG)
        except Exception:
            return None
        return float(pos.r_at(float(price))) if pos.risk_distance > 0 else None

    # ------------------------------------------------------------ the lock at the phase's target (prop_firm.lock_at_target)
    def target_lock_state(self, fresh: bool = False) -> Optional[Dict[str, Any]]:
        """With prop_firm.lock_at_target and risk.target_pct: the closed ``balance``, the phase's ``target`` balance and the
        ``goal`` the lock aims at (the target plus prop_firm.lock_buffer_pct of the account), the trading ``days`` (the
        highest count read, as target_state keeps it; None = unknown) and their ``dates`` (None when the broker cannot list
        them), on prop_firm.day_timezone's calendar. Read once a scan; ``fresh`` reads the balance again (an order inside
        the account lock: another window may just have closed a trade). None when off or the balance cannot be read."""
        p, r = self.settings.prop_firm, self.settings.risk
        if not getattr(p, "lock_at_target", False) or not r.target_pct or self.broker is None:
            return None
        cached = self._lock_cache[1] if self._lock_cache is not None and self._lock_cache[0] == self._scan_id else None
        if cached is not None and not fresh:
            return cached
        try:
            balance = float(self.broker.balance())
        except Exception:
            return None
        if cached is None:
            count, dates = None, None
            try:
                lister = getattr(self.broker, "trading_dates", None)
                dates = lister(p.day_timezone) if callable(lister) else None
            except Exception:
                dates = None
            try:                                         # one read of the deal history where the broker lists the dates
                counter = getattr(self.broker, "trading_days", None)
                count = len(dates) if dates is not None else counter(p.day_timezone) if callable(counter) else None
                count = int(count) if count is not None else None
            except Exception:
                count = None
            if count is not None:
                self._days_known = max(count, self._days_known or 0)
            size = float(self.settings.account_size)
            target = size * (1.0 + float(r.target_pct) / 100.0)
            cached = {"target": target, "goal": target + size * float(p.lock_buffer_pct) / 100.0, "days": self._days_known,
                      "dates": set(dates) if dates is not None else None}
        state = {**cached, "balance": balance}
        self._lock_cache = (self._scan_id, state)
        return state

    def _prague_day(self, ts) -> Any:
        """The date of a naive UTC time on the firm's calendar (prop_firm.day_timezone); None without a time."""
        if ts is None or pd.isna(ts):
            return None
        return pd.Timestamp(ts).tz_localize("UTC").tz_convert(self.settings.prop_firm.day_timezone).date()

    def _lock_rules(self) -> Tuple[float, float, float]:
        """``(tick, stops distance, freeze distance)`` of this market: the server's, else the profile's price grid; read once
        a scan."""
        cached = getattr(self, "_rules_cache", None)
        if cached is not None and cached[0] == self._scan_id:
            return cached[1]
        rules = None
        fn = getattr(self.broker, "price_rules", None)
        if callable(fn):
            try:
                rules = fn(self.symbol)
            except Exception:
                rules = None
        if not rules or not rules[0] or float(rules[0]) <= 0:
            out = (10.0 ** -self.spec.price_decimals, 0.0, 0.0)
        else:
            out = (float(rules[0]), float(rules[1] or 0.0), float(rules[2] or 0.0))
        self._rules_cache = (self._scan_id, out)
        return out

    def _cost_model(self, entry: float, lots: float) -> float:
        """The profile's round-turn commission of ``lots`` at ``entry`` (SymbolSpec.commission_per_lot and commission_pct, none
        on the live profiles): what an order's lock counts until the fill's own commission can be read."""
        spec = self.spec
        cost = float(spec.commission_per_lot) * lots
        if spec.commission_pct:
            cost += float(spec.commission_pct) / 100.0 * abs(entry) / spec.pip_size * spec.pip_value_per_lot * lots
        return cost

    def _closing_costs(self, pos: Position) -> float:
        """What closing ``pos`` still costs: the broker's figure (MT5: the entry deal's commission again and a negative swap;
        paper: the round turn it books at the close), else the profile's commission."""
        fn = getattr(self.broker, "closing_costs", None)
        costs = None
        if callable(fn):
            try:
                costs = fn(pos)
            except Exception:
                costs = None
        return max(0.0, float(costs)) if costs is not None else self._cost_model(float(pos.entry), float(pos.lots))

    def lock_take_profit(self, direction: Direction, entry: float, lots: float, own_tp: float, costs: float, own_day,
                         state: Dict[str, Any]) -> Tuple[Optional[float], float, Optional[int]]:
        """``(price, need, days)`` for a trade of ``lots`` from ``entry`` whose own target is ``own_tp``: ``need`` is what its
        close must bring for the closed balance to reach the lock's goal, after ``costs``; ``days`` the phase's trading
        days with ``own_day`` counted (None: unknown); ``price`` the take-profit that nets ``need`` while the closed balance
        is under the phase's target, the days are logged and it lies nearer than the own target (None: the trade keeps its
        own target). Once the target stands the lock does nothing, as Max approved it (16 October): the trade that lifts
        the balance over the target aims at it, a trade opened or still open after that runs to its own exits (a trade
        closed at break-even only to log a day is what he turned down)."""
        need = max(0.0, float(state["goal"]) - float(state["balance"])) + max(0.0, float(costs))
        days = state.get("days")
        dates = state.get("dates")
        if days is not None and own_day is not None and dates is not None and own_day not in dates:
            days += 1                                    # the trade's own day is not in the account's history yet
        if (float(state["balance"]) >= float(state["target"]) or days is None
                or days < int(self.settings.prop_firm.min_trading_days) or not own_tp or lots <= 0):
            return None, need, days
        pnl_for = getattr(self.broker, "pnl_for", None)
        if callable(pnl_for):
            gain = float(pnl_for(self.symbol, direction, float(entry), float(own_tp), float(lots)))
        else:
            gain = direction.sign * (float(own_tp) - float(entry)) / self.spec.pip_size * self.spec.pip_value_per_lot * lots
        from .strategy.risk import target_lock_price
        return target_lock_price(direction, float(entry), float(own_tp), gain, need, self._lock_rules()[0]), need, days

    def _order_lock(self, direction: Direction, entry: float, lots: float, own_tp: float, now: pd.Timestamp,
                    reference: Optional[float] = None) -> Optional[Tuple[float, float, int]]:
        """``(price, need, days)`` of the lock for an order about to go out (inside the account lock, the balance read again;
        the trade's own day is today), or None to send its own target: also when the price lies inside the server's stops
        level from ``reference`` (the order's price for a limit; for a market order the price it would close at, which the
        server checks a take-profit against), where the order would be refused: the first scan after the fill sets it."""
        state = self.target_lock_state(fresh=True)
        if state is None:
            return None
        price, need, days = self.lock_take_profit(direction, entry, lots, own_tp, self._cost_model(entry, lots),
                                                  self._prague_day(now), state)
        if price is None:
            return None
        if reference is None:
            try:
                reference = float(self.broker.fill_price(self.symbol, Direction.SHORT if direction is Direction.LONG else Direction.LONG))
            except Exception:
                reference = float(entry)
        tick, stops, _freeze = self._lock_rules()
        if direction.sign * (price - reference) < max(stops, tick) - 1e-12:
            return None
        return price, need, days

    def manage_target_lock(self, now: pd.Timestamp) -> None:
        """Every scan with prop_firm.lock_at_target: each filled position of this market (with a stop and a target) and each
        of its resting limits gets the take-profit the lock wants, its own target or the lock's price (``lock_take_profit``),
        sent to the server when it differs by a tick or more; a position whose lock price has already traded is closed at
        the market. A balance that moved since the last scan (another trade closed, a limit filled later) moves the level
        with it, and a restarted window treats the positions it finds the same way."""
        if self.broker is None or self.dry_run:
            return
        state = self.target_lock_state()
        if state is None:
            return
        listed = self.broker.open_positions(self.symbol)
        changed = False
        for pos in listed:
            if getattr(pos, "status", "filled") == "filled" and pos.stop and pos.take_profit:
                changed = self._lock_position(pos, state, now) or changed
        limits_changed = False
        for oid, info in list(self.limits.items()):
            limits_changed = self._lock_limit(oid, info, state, now) or limits_changed
        if limits_changed:
            self.save_limits()
        gone = set(self.own_targets) - {p.id for p in listed} - set(self.limits) - set(self.known_positions) - set(self.unconfirmed)
        if gone and not self._entries_held():           # closed: their records go (never on a terminal's first listings)
            for key in gone:
                self.own_targets.pop(key, None)
            changed = True
        if changed:
            self.save_own_targets()

    def _own_record(self, pos: Position) -> Tuple[Dict[str, Any], bool]:
        """``(record, changed)``: the position's own target, the last take-profit the lock sent and whether Telegram heard of
        the lock. Made from the server's take-profit the first time (a trade the lock never moved carries its own); a
        take-profit moved by hand since the lock's last move (neither the own target nor the lock's) is the trade's own
        target from then on."""
        tick = self._lock_rules()[0]
        server = float(pos.take_profit)
        rec = self.own_targets.get(pos.id)
        if rec is None:
            own = pos.meta.get("own_take_profit")
            rec = self.own_targets[pos.id] = {"take_profit": float(own) if own else server, "set": None, "told": False}
            return rec, True
        sent = rec.get("set")
        if abs(server - float(rec["take_profit"])) < 0.5 * tick or (sent is not None and abs(server - float(sent)) < 0.5 * tick):
            return rec, False
        rec["take_profit"], rec["set"] = server, None
        return rec, True

    def _lock_position(self, pos: Position, state: Dict[str, Any], now: pd.Timestamp) -> bool:
        """One position: its take-profit as the lock wants it, or a close at the market when the lock's price has traded.
        True when its record changed."""
        rec, changed = self._own_record(pos)
        retry = self._lock_retry.get(pos.id)
        if retry is not None and now < retry[1]:
            return changed
        own = float(rec["take_profit"])
        price, need, days = self.lock_take_profit(pos.direction, float(pos.entry), float(pos.lots), own,
                                                  self._closing_costs(pos), self._prague_day(pos.opened_at), state)
        if days is None and float(state["balance"]) < float(state["target"]):
            return changed                               # the day count unknown: the take-profit on the server stays
        tick, stops, _freeze = self._lock_rules()
        want = own
        if price is not None:
            close_at = self._close_price(pos)
            if close_at is not None and pos.direction.sign * (close_at - price) >= 0:
                return self._lock_close(pos, price, close_at, need, days, state, now) or changed
            if close_at is not None and pos.direction.sign * (price - close_at) < stops:
                return changed                           # inside the stops level: not settable; a later scan closes it
            want = price
        if abs(want - float(pos.take_profit)) < 0.5 * tick:
            return changed
        try:
            self.broker.modify_take_profit(pos.id, want)
        except KeyError:
            return changed                               # closed meanwhile: its close is reported
        except Exception as exc:
            self._lock_refused(pos.id, f"take-profit of {pos.id} to {want:.{self._lock_decimals()}f}", exc, now)
            return changed
        self._lock_retry.pop(pos.id, None)
        rec["set"] = want if price is not None else None
        self._lock_moved(pos.id, pos.direction, float(pos.entry), float(pos.lots), own, want, price is not None, need, days,
                         state, rec, "told", now)
        return True

    def _lock_limit(self, oid: str, info: Dict[str, Any], state: Dict[str, Any], now: pd.Timestamp) -> bool:
        """One resting limit: the lock's take-profit from its price and lots (its own day is today: a limit rests a few hours
        inside the session), moved on the server; its own target stays in its record, so the "target traded first" cancel
        keeps reading it as the backtest does. True when its record changed."""
        retry = self._lock_retry.get(oid)
        if retry is not None and now < retry[1]:
            return False
        direction = Direction[str(info["direction"])]
        entry, lots, own = float(info["price"]), float(info["lots"]), float(info["take_profit"])
        current = float(info.get("lock_tp") or own)
        price, need, days = self.lock_take_profit(direction, entry, lots, own, self._cost_model(entry, lots),
                                                  self._prague_day(now), state)
        if days is None and float(state["balance"]) < float(state["target"]):
            return False
        tick, stops, _freeze = self._lock_rules()
        want = price if price is not None and direction.sign * (price - entry) >= max(stops, tick) - 1e-12 else own
        if abs(want - current) < 0.5 * tick:
            return False
        try:
            self.broker.modify_limit_take_profit(oid, want)
        except KeyError:
            return False                                 # filled or gone meanwhile: manage_limits takes it next scan
        except Exception as exc:
            self._lock_refused(oid, f"take-profit of limit {oid} to {want:.{self._lock_decimals()}f}", exc, now)
            return False
        self._lock_retry.pop(oid, None)
        locked = abs(want - own) >= 0.5 * tick
        info["lock_tp"] = want if locked else None
        self._lock_moved(oid, direction, entry, lots, own, want, locked, need, days, state, info, "lock_told", now)
        return True

    def _close_price(self, pos: Position) -> Optional[float]:
        """The price ``pos`` would close at now (the bid for a long, the ask for a short); None without a quote."""
        try:
            return float(self.broker.fill_price(self.symbol, Direction.SHORT if pos.direction is Direction.LONG else Direction.LONG))
        except Exception:
            return None

    def _lock_decimals(self) -> int:
        from .strategy.risk import tick_decimals
        return max(int(self.spec.price_decimals), tick_decimals(self._lock_rules()[0]))

    def _lock_close(self, pos: Position, price: float, close_at: float, need: float, days: int, state: Dict[str, Any],
                    now: pd.Timestamp) -> bool:
        """The lock's price has traded already (between two scans, or before the take-profit could be set): the position
        closes at the market. True when it closed."""
        try:
            self.broker.close_position(pos.id, "target_lock", ts=now)
        except KeyError:
            return False
        except Exception as exc:
            self._lock_refused(pos.id, f"close of {pos.id} at the market", exc, now)
            return False
        self._lock_retry.pop(pos.id, None)
        self.own_targets.pop(pos.id, None)
        d = self._lock_decimals()
        self.note("target_lock_exit", now, id=pos.id, direction=pos.direction.name, entry=float(pos.entry), take_profit=float(price),
                  price=float(close_at), lots=float(pos.lots),
                  note=f"the lock's price had traded; needs {need:,.2f} for the goal {state['goal']:,.2f} (balance "
                       f"{state['balance']:,.2f}); {days} trading day(s)")
        self.notifier.send(f"🔐 {self.symbol}: {pos.id} gesloten met de doel-lock rond {close_at:.{d}f}: de prijs stond al voorbij "
                           f"{price:.{d}f}, waar de gesloten balans +{float(self.settings.risk.target_pct):g}% haalt")
        return True

    def _lock_refused(self, key: str, what: str, exc: Exception, now: pd.Timestamp) -> None:
        """A move or close the server refused (a freeze level, a market that is shut): three quick tries, then every 15
        minutes, one message (FTMO counts server requests)."""
        tries = self._lock_retry.get(key, (0, now))[0] + 1
        self._lock_retry[key] = (tries, pd.Timestamp(now) + pd.Timedelta(minutes=15 if tries >= 3 else 1))
        print(f"[live] {self.symbol}: target lock: {what} refused ({exc}); try {tries}")
        if tries == 1:
            self.note("target_lock_failed", now, id=key, reason=str(exc))
            self.notifier.send(f"⚠️ {self.symbol}: doel-lock: {what} geweigerd ({exc}); de bot probeert het opnieuw, na drie "
                               f"pogingen elke 15 min")

    def _lock_moved(self, key: str, direction: Direction, entry: float, lots: float, own: float, tp: float, locked: bool,
                    need: float, days: int, state: Dict[str, Any], rec: Dict[str, Any], told: str, now: pd.Timestamp) -> None:
        """A take-profit the lock moved: a journal row every time, Telegram once a trade (``rec[told]``)."""
        d = self._lock_decimals()
        target = float(self.settings.risk.target_pct)
        days_text = "?" if days is None else days
        self.note("target_lock", now, id=key, direction=direction.name, entry=float(entry), take_profit=float(tp), lots=float(lots),
                  note=(f"{'locked' if locked else 'own target again'}: own target {own:.{d}f}; needs {need:,.2f} with costs for "
                        f"the goal {state['goal']:,.2f} (balance {state['balance']:,.2f}); {days_text} trading day(s)"))
        print(f"[live] {self.symbol}: target lock: {key} take-profit {tp:.{d}f} ({'locked' if locked else 'its own'}; own {own:.{d}f})")
        if not locked or rec.get(told):
            return
        rec[told] = True
        self.notifier.send(f"🔐 {self.symbol}: doel-lock op {key}: TP van {own:.{d}f} naar {tp:.{d}f}, de prijs waar de gesloten "
                           f"balans +{target:g}% haalt (na kosten, {state['goal'] - state['target']:,.0f} marge); {days} "
                           f"handelsdagen. Nooit verder dan zijn eigen doel; de stop blijft")

    def load_own_targets(self) -> None:
        if self.own_targets_path is None or not self.own_targets_path.exists():
            return
        try:
            doc = json.loads(self.own_targets_path.read_text(encoding="utf-8"))
            self.own_targets = {str(k): {"take_profit": float(v["take_profit"]),
                                         "set": float(v["set"]) if v.get("set") is not None else None,
                                         "told": bool(v.get("told"))} for k, v in dict(doc).items()}
        except Exception as exc:     # a damaged file: the positions' take-profits on the server count as their own
            print(f"[live] {self.symbol}: could not read {self.own_targets_path} ({exc})")

    def save_own_targets(self) -> None:
        if self.own_targets_path is None:
            return
        try:
            self.own_targets_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.own_targets_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.own_targets), encoding="utf-8")
            os.replace(tmp, self.own_targets_path)
        except Exception as exc:
            print(f"[live] {self.symbol}: could not write {self.own_targets_path} ({exc})")

    def report_closes(self) -> None:
        if self.broker is None:
            return
        for trade in self.broker.recent_closes():
            if str(trade.symbol).upper() != self.symbol:
                continue                                   # another window's trade on the same account: its window reports it
            self.known_positions.pop(trade.id, None)
            if self.own_targets.pop(trade.id, None) is not None:
                self.save_own_targets()
            self.note("closed", trade.closed_at, id=trade.id, direction=trade.direction.name, entry=float(trade.entry),
                      price=float(trade.exit), pnl=float(trade.pnl), r=float(trade.r), reason=trade.reason, lots=float(trade.lots))
            icon = "🎯" if trade.reason == "take_profit" else "🛑" if trade.reason == "stop" else "➖"
            self.notifier.send(f"{icon} {self.symbol} closed ({trade.reason}) @ {trade.exit:.{self.spec.price_decimals}f}  "
                               f"P&L {trade.pnl:+,.0f}  ({trade.r:+.2f}R)  id {trade.id}")
