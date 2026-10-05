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
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis, Bias, ForecastSummary, TradeMode, TradeSetup
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
    """A lock file next to the journal, shared by the windows of one account. It waits up to ``timeout`` seconds and then
    goes on without the lock, so a stuck file never stops trading; a file older than ``stale`` seconds is removed."""

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
                if time.time() >= deadline:
                    return self
                time.sleep(0.05)
            except OSError:
                return self

    def __exit__(self, *exc) -> bool:
        if self.held:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.held = False
        return False


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
        self.dry_run = dry_run
        self.require_approval = settings.live.require_approval if require_approval is None else require_approval
        self.approval_timeout_minutes = approval_timeout_minutes if approval_timeout_minutes is not None else settings.live.approval_timeout_minutes
        self.notify_every_scan = settings.live.notify_every_scan if notify_every_scan is None else notify_every_scan
        self.clock = clock or utc_now
        self.seen: set = set()
        self.pending: Dict[str, PendingSetup] = {}
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
        self._feed_down: bool = False                       # the lowest timeframe went quiet during the session
        self.journal: Optional[Journal] = Journal(settings.live.journal_path, clock=self.clock) if settings.live.journal_path else None
        # the zones traded per visit survive a restart: without them a restart right after a stop-out could re-enter the same
        # visit, which one_trade_per_visit forbids (re-entries after a stop-out won 9 % in R6)
        self.traded_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"traded_{self.symbol}.json"
                                            if settings.live.journal_path else None)
        self.lock_path: Optional[Path] = Path(settings.live.journal_path).parent / "account.lock" if settings.live.journal_path else None
        # a paper account (BTC on Bitstamp prices) keeps its balance and open trades across a restart
        self.paper_path: Optional[Path] = (Path(settings.live.journal_path).parent / f"paper_{self.symbol}.json"
                                           if keep_paper_account and settings.live.journal_path
                                           and callable(getattr(broker, "restore", None)) else None)
        self.load_paper()
        self.load_traded()
        self._briefed_on: Optional[object] = None          # local date of the last morning briefing
        self._summarized_on: Optional[object] = None       # local date of the last evening summary
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
            except Exception as exc:     # a feed hiccup must not stop the loop; the guard re-checks before any order
                print(f"[live] {self.symbol}: guard update failed ({exc})")
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=False)
        self.last_analysis = analysis
        self.manage_positions(views)
        self.process_decisions(now)
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
            try:
                if self.connection_ok():
                    self.step()
            except Exception as exc:  # keep the loop alive and say what broke
                self.notifier.send(f"⚠️ {self.symbol}: live loop error: {exc}")
            if self.broker is not None:
                self.broker.idle(poll)
            else:
                time.sleep(poll)

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
        """The broker's link (MT5: re-initialised after a terminal restart): one message when it goes down and one when it
        is back; while down the scan is skipped."""
        check = getattr(self.broker, "connection_ok", None)
        if not callable(check):
            return True
        try:
            ok, reason = check()
        except Exception as exc:
            ok, reason = False, str(exc)
        if not ok and self._link_down is None:
            self._link_down = reason
            self.notifier.send(f"⚠️ {self.symbol}: {reason} - de bot wacht en probeert het elke minuut opnieuw.")
        elif ok and self._link_down is not None:
            self._link_down = None
            self.notifier.send(f"✅ {self.symbol}: weer verbonden met MT5.")
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
        ok, reason = self.guard.can_open(self.broker, now, self.symbol, new_risk=self.planned_risk())
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

    def planned_risk(self) -> float:
        """What the next trade risks at its stop (account currency): the profile's risk, lowered by risk.drawdown_steps."""
        from .strategy.risk import stepped_risk
        try:
            params = stepped_risk(self.settings.risk, self.broker.balance(), self.settings.account_size)
            return float(self.broker.equity()) * params.risk_pct / 100.0
        except Exception:
            return 0.0

    def execute(self, setup: TradeSetup, forecast: Optional[ForecastSummary], now: pd.Timestamp) -> Optional[Position]:
        # the cap check and the order under one lock shared by the windows of the account: two markets signalling in
        # the same second could otherwise both take the last open slot
        with AccountLock(self.lock_path):
            sid = short_id_for((setup.poi.key, str(setup.confirmation.timestamp)))
            ok, reason = self.guard.can_open(self.broker, now, self.symbol, new_risk=self.planned_risk())
            if not ok:
                self.note("not_executed", now, id=sid, reason=reason)
                self.notifier.send(f"⛔ {self.symbol}: not executed - {reason}")
                return None
            try:
                price = self.broker.fill_price(self.symbol, setup.direction)       # the ask for a buy, the bid for a sell
            except Exception as exc:
                self.note("not_executed", now, id=sid, reason=f"no current price: {exc}")
                self.notifier.send(f"⛔ {self.symbol}: not executed - no current price ({exc})")
                return None
            from .strategy.risk import reconcile_risk, resize_at, stepped_risk
            wrong_side = (setup.direction.sign > 0 and price <= setup.stop) or (setup.direction.sign < 0 and price >= setup.stop)
            risk_params = stepped_risk(self.settings.risk, self.broker.balance(), self.settings.account_size)
            lots, risk_amount, risk_distance, rr_now, _ = resize_at(price, setup.stop, setup.take_profit, self.broker.equity(),
                                                                    self.spec, risk_params)
            if wrong_side or rr_now < self.settings.risk.min_rr:
                self.note("not_executed", now, id=sid, price=float(price), rr=float(rr_now), reason="price moved, R:R below minimum")
                self.notifier.send(f"⛔ {self.symbol}: not executed - price moved to {price:.{self.spec.price_decimals}f}, "
                                   f"R:R now 1:{rr_now:.1f} (min {self.settings.risk.min_rr:.0f})")
                return None
            if lots <= 0:
                self.note("not_executed", now, id=sid, price=float(price), reason="stop too wide for the minimum lot at this price")
                self.notifier.send(f"⛔ {self.symbol}: not executed - stop too wide for the minimum lot at {price:.{self.spec.price_decimals}f}")
                return None
            resized = f"; lots {setup.lots:.2f} -> {lots:.2f} at {price:.{self.spec.price_decimals}f}" if abs(lots - setup.lots) > 1e-9 else ""
            if risk_params.risk_pct != self.settings.risk.risk_pct:
                resized += f"; risk {risk_params.risk_pct:g} % (balance below the start, risk.drawdown_steps)"
            margin_note = ""
            room = self.margin_room(setup.direction, price)
            if room is not None and lots > room[0] + 1e-9:
                fit = round(math.floor(room[0] / self.spec.lot_step + 1e-9) * self.spec.lot_step, 4)
                if fit < self.spec.min_lot:
                    self.note("not_executed", now, id=sid, price=float(price), reason=f"margin: {room[1]:,.0f} available, "
                              f"{lots:.2f} lots wanted, {room[0]:.3f} fit")
                    self.notifier.send(f"⛔ {self.symbol}: not executed - not enough margin for the minimum lot "
                                       f"({room[1]:,.0f} available, {self.spec.min_lot:g} lots needed)")
                    return None
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
                self.notifier.send(f"⛔ {self.symbol}: order failed - {exc}")
                return None
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
            stepped = f" ({risk_params.risk_pct:g} %: balance below the start)" if risk_params.risk_pct != self.settings.risk.risk_pct else ""
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
        if hold and not callable(getattr(self.broker, "on_candle", None)):
            now = self.clock()
            for pid, pos in list(open_by_id.items()):
                if getattr(pos, "status", "filled") != "filled" or pos.opened_at is None:
                    continue
                if now - pd.Timestamp(pos.opened_at) < pd.Timedelta(hours=float(hold)):
                    continue
                try:
                    self.broker.close_position(pid, "time", ts=now)
                    open_by_id.pop(pid)
                    self.note("time_exit", now, id=pid, note=f"open {hold:g} h")
                except Exception as exc:
                    if not pos.meta.get("time_exit_failed_sent"):
                        pos.meta["time_exit_failed_sent"] = True
                        self.notifier.send(f"⚠️ {self.symbol}: closing {pid} after {hold:g} h failed ({exc}); trying every scan")
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
            extreme = last.high if pos.direction.sign > 0 else last.low
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
