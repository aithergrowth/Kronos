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
import math
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis, Bias, ForecastSummary, TradeSetup
from .data.tv_cache import load_all
from .execution.base import Broker, Position
from .execution.risk_guard import RiskGuard
from .notify.telegram import TelegramNotifier
from .strategy.engine import StrategyEngine
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
    ):
        self.settings = settings
        self.symbol = symbol.upper()
        self.spec = settings.symbol(self.symbol)
        self.fetch = fetch
        self.broker = broker
        self.notifier = notifier or TelegramNotifier(params=settings.telegram, dry_run=True)
        self.engine = engine or StrategyEngine(settings)
        self.guard = guard or RiskGuard(settings.prop_firm, settings.account_size)
        self.dry_run = dry_run
        self.require_approval = settings.live.require_approval if require_approval is None else require_approval
        self.approval_timeout_minutes = approval_timeout_minutes if approval_timeout_minutes is not None else settings.live.approval_timeout_minutes
        self.notify_every_scan = settings.live.notify_every_scan if notify_every_scan is None else notify_every_scan
        self.clock = clock or utc_now
        self.seen: set = set()
        self.pending: Dict[str, PendingSetup] = {}
        self.known_positions: Dict[str, Position] = {}
        self.unconfirmed: Dict[str, Position] = {}       # submitted orders whose fill is not confirmed yet
        self._attention_reports: Dict[str, tuple] = {}   # alert once per observed exposure/status change
        self.last_analysis: Optional[Analysis] = None
        self.stale: Dict[Timeframe, pd.Timedelta] = {}   # timeframe -> age of its last closed candle
        self._fed_until: Optional[pd.Timestamp] = None   # last candle handed to a simulated broker
        self._feed_line: Optional[str] = None
        self._news_refreshed: Optional[pd.Timestamp] = None
        self._briefed_on: Optional[object] = None          # local date of the last morning briefing
        self._views: Dict[Timeframe, CandleSeries] = {}
        self._touched: set = set()                          # POI keys already announced as entered

    # ------------------------------------------------------------ one tick
    def step(self, now: Optional[pd.Timestamp] = None) -> Analysis:
        now = pd.Timestamp(now) if now is not None else self.clock()
        views = self.fetch()
        self._views = {tf: series.closed_as_of(now) for tf, series in views.items()}
        if not self.dry_run:
            self.advance_paper(views, now)
        self.stale = self.stale_timeframes(views, now)
        self.report_feed(views)
        self.refresh_news(now)
        equity = self.broker.equity() if self.broker is not None else self.settings.account_size
        # Skip the broad per-scan forecast batch. Candidate-level filter/advisory
        # forecasts still run inside StrategyEngine.analyze. Charts forecast on demand.
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=False)
        self.last_analysis = analysis
        if not self.dry_run:
            self.manage_positions(views)
            self.process_decisions(now)
            self.report_closes()
        self.morning_briefing(analysis, now)
        self.announce_poi_touch(analysis)
        if analysis.has_valid_signal:
            self.handle_signal(analysis, now)
        elif self.notify_every_scan:
            self.notifier.send_analysis(analysis, self.spec)
        return analysis

    # ------------------------------------------------------------ configured notifications
    def morning_briefing(self, analysis: Analysis, now: pd.Timestamp) -> None:
        """Once per weekday at ``live.briefing_time`` local time: the bias, the decision and the POI map for the day."""
        at = self.settings.live.briefing_time
        if not at:
            return
        stamp = pd.Timestamp(now)
        local = (stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp).tz_convert(self.settings.session.timezone)
        hour, minute = (int(x) for x in at.split(":"))
        if local.weekday() > 4 or (local.hour, local.minute) < (hour, minute) or self._briefed_on == local.date():
            return
        self.notifier.send(f"☀️ {self.symbol} morning analysis ({local:%a %H:%M} {self.settings.session.timezone})")
        self.notifier.send_analysis(analysis, self.spec)
        self.send_chart(analysis, "briefing")
        self._briefed_on = local.date()  # failed delivery must remain retryable

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
            if not len(series):
                return
            if forecast is None and self.settings.kronos.mode != "off" and getattr(self.engine, "forecaster", None) is not None:
                forecast = self.engine._forecast(series, [])
            bias = "  ".join(f"{t.label} {b.bias.name.lower()}" for t, b in sorted(analysis.biases.items())) if analysis.biases else ""
            zones = [p for p in analysis.pois if p.direction is analysis.decision.direction] or list(analysis.pois)
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

    def announce_poi_touch(self, analysis: Analysis) -> None:
        """Say once when price enters a POI that the bias allows, so the trader can watch the confirmation form."""
        if not self.settings.live.notify_poi_touch or not analysis.decision.tradable:
            return
        d = self.spec.price_decimals
        for poi in analysis.pois:
            if poi.direction is not analysis.decision.direction or not poi.contains(analysis.price):
                continue
            if poi.key in self._touched:
                continue
            arrow = "▲" if poi.direction is Bias.BULLISH else "▼"
            self.notifier.send(f"👀 {self.symbol} is inside the {poi.timeframe.label} {arrow} POI {poi.low:.{d}f}-{poi.high:.{d}f} "
                               f"({analysis.decision.reason}); waiting for a confirmation")
            self._touched.add(poi.key)  # failed delivery must remain retryable
            self.send_chart(analysis, "touch", timeframe=poi.timeframe)

    def run_forever(self, poll_seconds: Optional[int] = None) -> None:
        poll = poll_seconds or self.settings.live.poll_seconds
        while True:
            try:
                self.step()
            except Exception as exc:  # keep the loop alive and say what broke
                try:
                    self.notifier.send(f"⚠️ {self.symbol}: live loop error: {exc}")
                except Exception:
                    # The transport may be the original failure; it must not terminate polling.
                    print(f"[live] {self.symbol}: {type(exc).__name__}; notification unavailable, retrying next poll")
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
        try:
            from .data.calendar import fetch_forexfactory
            for week in ("thisweek", "nextweek"):
                calendar.add(fetch_forexfactory(week))
        except Exception as exc:
            print(f"[live] {self.symbol}: news calendar refresh failed ({exc}); using the events already loaded")

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
        if self.stale and self.settings.live.require_fresh_data:
            self.seen.add(key)
            self.notifier.send(f"⏸ {self.symbol}: setup ignored, the data is stale ({self.stale_text()}); refresh the feed")
            return
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
            self.seen.add(key)  # failed Telegram delivery must remain retryable
            if self.broker is not None:
                self.notifier.send(f"{self.symbol}: dry-run, order not sent")
            return
        self.seen.add(key)
        ok, reason = self.guard.can_open(self.broker, now, self.symbol)
        if not ok:
            self.notifier.send_setup(setup, forecast, self.spec)
            self.notifier.send(f"⛔ {self.symbol}: setup NOT executable - {reason}")
            return
        if self.require_approval:
            timeout = self.approval_timeout_minutes or max(5, setup.confirmation.timeframe.minutes)
            pending = PendingSetup(short_id_for(key), key, setup, forecast, now, now + pd.Timedelta(int(timeout), unit="min"))
            self.pending[pending.short_id] = pending
            self.notifier.send_approval_request(setup, pending.short_id, forecast, self.spec, pending.expires_at)
            self.send_chart(analysis, "setup", setup=setup, forecast=forecast)
            return
        self.execute(setup, forecast, now)

    def execute(self, setup: TradeSetup, forecast: Optional[ForecastSummary], now: pd.Timestamp) -> Optional[Position]:
        if self.dry_run or self.broker is None:
            self.notifier.send(f"{self.symbol}: notification-only mode, order not sent")
            return None
        if self.stale and self.settings.live.require_fresh_data:
            self.notifier.send(f"⛔ {self.symbol}: not executed - the data is stale ({self.stale_text()}); refresh the feed")
            return None
        calendar = getattr(self.engine, "calendar", None)
        if calendar is not None and self.settings.news.enabled:
            event = calendar.blackout(self.symbol, now)
            if event is not None:
                self.notifier.send(f"⛔ {self.symbol}: not executed - news blackout: {event.title} ({event.currency}) "
                                   f"at {event.time:%H:%M} UTC")
                return None
        ok, reason = self.guard.can_open(self.broker, now, self.symbol)
        if not ok:
            self.notifier.send(f"⛔ {self.symbol}: not executed - {reason}")
            return None
        try:
            price = float(self.broker.current_price(self.symbol))
            if not math.isfinite(price) or price <= 0:
                raise ValueError("current price must be finite and positive")
        except Exception as exc:
            self.notifier.send(f"⛔ {self.symbol}: not executed - no current price ({exc})")
            return None
        risk_now = abs(price - setup.stop) + self.settings.risk.spread_buffer_pips * self.spec.pip_size
        reward_now = abs(setup.take_profit - price)
        rr_now = reward_now / risk_now if risk_now > 0 else 0.0
        wrong_side = (setup.direction.sign > 0 and price <= setup.stop) or (setup.direction.sign < 0 and price >= setup.stop)
        if wrong_side or rr_now < self.settings.risk.min_rr:
            self.notifier.send(f"⛔ {self.symbol}: not executed - price moved to {price:.{self.spec.price_decimals}f}, "
                               f"R:R now 1:{rr_now:.1f} (min {self.settings.risk.min_rr:.0f})")
            return None
        try:
            pos = self.broker.place_market_order(
                self.symbol, setup.direction, setup.lots, setup.stop, setup.take_profit, setup.risk_amount,
                setup.risk_distance, setup.breakeven_r,
                meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value}",
                      "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value},
                price=price, ts=now,
            )
        except Exception as exc:
            self.notifier.send(f"⛔ {self.symbol}: order failed - {exc}")
            return None
        self.guard.record_trade(now)
        self.known_positions[pos.id] = pos
        side = "BUY" if pos.direction.sign > 0 else "SELL"
        d = self.spec.price_decimals
        if getattr(pos, "status", "filled") == "attention":
            self.report_execution_attention(pos)
        elif getattr(pos, "status", "filled") == "filled":
            self.notifier.send(f"💸 {self.symbol} {side} filled {pos.lots:.2f} lots @ {pos.entry:.{d}f}  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  risk {pos.risk_amount:,.0f}  (id {pos.id})")
        else:
            self.unconfirmed[pos.id] = pos
            self.notifier.send(f"📨 {self.symbol} {side} {pos.lots:.2f} lots submitted, fill not confirmed yet  "
                               f"SL {pos.stop:.{d}f}  TP {pos.take_profit:.{d}f}  (id {pos.id})")
        return pos

    # ------------------------------------------------------------ approvals
    def process_decisions(self, now: pd.Timestamp) -> None:
        for decision in self.notifier.poll_decisions():
            pending = self.pending.pop(decision.short_id, None)
            if pending is None:
                self.notifier.send(f"{self.symbol}: no pending setup with id {decision.short_id} (expired or already handled)")
                continue
            if not decision.approved:
                self.notifier.send(f"❌ {self.symbol}: setup {pending.short_id} skipped")
                continue
            if now >= pending.expires_at:
                self.notifier.send(f"⌛ {self.symbol}: setup {pending.short_id} approved too late "
                                   f"(expired {pending.expires_at:%H:%M} UTC), not executed")
                continue
            self.notifier.send(f"✅ {self.symbol}: setup {pending.short_id} approved, checking execution conditions")
            self.execute(pending.setup, pending.forecast, now)
        for short_id, pending in list(self.pending.items()):
            if now >= pending.expires_at:
                self.pending.pop(short_id)
                self.notifier.send(f"⌛ {self.symbol}: setup {short_id} expired without approval")

    # ------------------------------------------------------------ positions
    def report_execution_attention(self, pos: Position) -> None:
        """Keep uncertain exposure visible without claiming a protected/full fill."""
        self.known_positions[pos.id] = pos
        self.unconfirmed.pop(pos.id, None)
        reason = pos.meta.get("attention_reason", "broker exposure needs reconciliation")
        unknown = pos.meta.get("exposure_unverified", False)
        observed = (pos.meta.get("filled_units"), pos.meta.get("parent_status"), pos.lots, unknown, reason)
        if self._attention_reports.get(pos.id) == observed:
            return
        quantity = "exposure quantity unverified" if unknown else f"observed {pos.lots:.2f} lots"
        self.notifier.send(f"⚠️ {pos.symbol}: execution needs attention, {quantity}; "
                           f"protection unverified, new entries halted. Check broker positions and orders. "
                           f"{reason} (id {pos.id})")
        self._attention_reports[pos.id] = observed

    def manage_positions(self, views: Dict[Timeframe, CandleSeries]) -> None:
        """Confirm pending fills and move stops to break-even per the exit rules (no partials)."""
        if self.dry_run or self.broker is None or not views:
            return
        open_by_id = {p.id: p for p in self.broker.open_positions(self.symbol)}
        for pos in open_by_id.values():
            if getattr(pos, "status", "filled") == "attention":
                self.report_execution_attention(pos)
        d = self.spec.price_decimals
        for pid in list(self.unconfirmed):
            current = open_by_id.get(pid)
            if current is None:
                self.unconfirmed.pop(pid)
                self.known_positions.pop(pid, None)
                self.notifier.send(f"❌ {self.symbol}: order {pid} did not fill (cancelled or rejected)")
            elif getattr(current, "status", "filled") == "filled":
                self.unconfirmed.pop(pid)
                self.notifier.send(f"💸 {self.symbol}: fill confirmed @ {current.entry:.{d}f}  (id {pid})")
        lowest = views[min(views)]
        if len(lowest) == 0:
            return
        last = lowest.last
        for pos in open_by_id.values():
            self.known_positions.setdefault(pos.id, pos)
            if pos.breakeven_done or getattr(pos, "status", "filled") != "filled":
                continue
            extreme = last.high if pos.direction.sign > 0 else last.low
            if breakeven_reached(pos.direction, pos.entry, pos.risk_distance, extreme, pos.breakeven_r):
                self.broker.modify_stop(pos.id, pos.entry)
                pos.breakeven_done = True
                self.notifier.send(f"🔒 {self.symbol}: stop moved to break-even on {pos.id} ({pos.breakeven_r:.0f}R reached)")

    def report_closes(self) -> None:
        if self.broker is None:
            return
        for trade in self.broker.recent_closes():
            self.known_positions.pop(trade.id, None)
            icon = "🎯" if trade.reason == "take_profit" else "🛑" if trade.reason == "stop" else "➖"
            self.notifier.send(f"{icon} {self.symbol} closed ({trade.reason}) @ {trade.exit:.{self.spec.price_decimals}f}  "
                               f"P&L {trade.pnl:+,.0f}  ({trade.r:+.2f}R)  id {trade.id}")
