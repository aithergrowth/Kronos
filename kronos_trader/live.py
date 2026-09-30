"""Live loop: fetch candles -> analyse -> Telegram -> (approve) -> execute -> report.

Data comes from two places: higher timeframes from the TradingView CSV cache
(refreshed by Claude through the MCP, or by ``import-tv``) and the low
timeframes straight from the broker, which is the only real-time feed.

Execution is human-in-the-loop by default: a valid setup is sent to Telegram
with Approve / Skip buttons and the order is only placed after a tap, as long
as the request has not expired and the risk guard still allows it.  Fills,
break-even moves and closes (stop / target / break-even) are reported with
P&L.  ``dry_run=True`` never sends an order.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Tuple

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Analysis, ForecastSummary, TradeSetup
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


@dataclass
class PendingSetup:
    short_id: str
    key: Tuple
    setup: TradeSetup
    forecast: Optional[ForecastSummary]
    created_at: pd.Timestamp
    expires_at: pd.Timestamp


def build_fetch(
    settings: Settings,
    symbol: str,
    cache_dir: Optional[str] = None,
    broker: Optional[Broker] = None,
    broker_timeframes: Optional[Iterable[Timeframe]] = None,
    bar_counts: Optional[Dict[Timeframe, int]] = None,
) -> Callable[[], Dict[Timeframe, CandleSeries]]:
    """Compose a ``fetch`` for ``LiveRunner``: cached TradingView bars + live broker bars."""
    symbol = symbol.upper()
    spec = settings.symbols.get(symbol)
    tv_symbol = spec.tradingview_symbol if spec and spec.tradingview_symbol else symbol
    tfs = [Timeframe.parse(tf) for tf in (broker_timeframes if broker_timeframes is not None else settings.live.broker_timeframes)]
    counts = dict(settings.live.broker_bar_counts)
    counts.update(bar_counts or {})

    def fetch() -> Dict[Timeframe, CandleSeries]:
        views: Dict[Timeframe, CandleSeries] = {}
        if cache_dir:
            views.update(load_all(cache_dir, tv_symbol) or load_all(cache_dir, symbol))
        if broker is not None:
            for tf in tfs:
                views[tf] = broker.get_candles(symbol, tf, counts.get(tf, 500))
        if not views:
            raise RuntimeError(f"no candles for {symbol}: cache {cache_dir!r} empty and no broker feed")
        return views

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
        self.last_analysis: Optional[Analysis] = None

    # ------------------------------------------------------------ one tick
    def step(self, now: Optional[pd.Timestamp] = None) -> Analysis:
        now = pd.Timestamp(now) if now is not None else self.clock()
        views = self.fetch()
        equity = self.broker.equity() if self.broker is not None else self.settings.account_size
        analysis = self.engine.analyze(self.symbol, views, equity=equity, now=now, compute_forecasts=True)
        self.last_analysis = analysis
        self.manage_positions(views)
        self.process_decisions(now)
        self.report_closes()
        if analysis.has_valid_signal:
            self.handle_signal(analysis, now)
        elif self.notify_every_scan:
            self.notifier.send_analysis(analysis, self.spec)
        return analysis

    def run_forever(self, poll_seconds: Optional[int] = None) -> None:
        poll = poll_seconds or self.settings.live.poll_seconds
        while True:
            try:
                self.step()
            except Exception as exc:  # keep the loop alive and say what broke
                self.notifier.send(f"⚠️ {self.symbol}: live loop error: {exc}")
            time.sleep(poll)

    # ------------------------------------------------------------ signals
    def handle_signal(self, analysis: Analysis, now: pd.Timestamp) -> None:
        setup = analysis.signal.setup
        forecast = analysis.signal.forecast
        key = (setup.poi.key, str(setup.confirmation.timestamp))
        if key in self.seen:
            return
        self.seen.add(key)
        if self.broker is None or self.dry_run:
            self.notifier.send_setup(setup, forecast, self.spec)
            if self.broker is not None:
                self.notifier.send(f"{self.symbol}: dry-run, order not sent")
            return
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
            return
        self.execute(setup, forecast, now)

    def execute(self, setup: TradeSetup, forecast: Optional[ForecastSummary], now: pd.Timestamp) -> Optional[Position]:
        ok, reason = self.guard.can_open(self.broker, now, self.symbol)
        if not ok:
            self.notifier.send(f"⛔ {self.symbol}: not executed - {reason}")
            return None
        try:
            price = self.broker.current_price(self.symbol)
        except Exception:
            price = setup.entry
        risk_now = abs(price - setup.stop) + self.settings.risk.spread_buffer_pips * self.spec.pip_size
        reward_now = abs(setup.take_profit - price)
        rr_now = reward_now / risk_now if risk_now > 0 else 0.0
        wrong_side = (setup.direction.sign > 0 and price <= setup.stop) or (setup.direction.sign < 0 and price >= setup.stop)
        if wrong_side or rr_now < self.settings.risk.min_rr:
            self.notifier.send(f"⛔ {self.symbol}: not executed - price moved to {price:.{self.spec.price_decimals}f}, "
                               f"R:R now 1:{rr_now:.1f} (min {self.settings.risk.min_rr:.0f})")
            return None
        pos = self.broker.place_market_order(
            self.symbol, setup.direction, setup.lots, setup.stop, setup.take_profit, setup.risk_amount,
            setup.risk_distance, setup.breakeven_r,
            meta={"comment": f"{setup.poi.timeframe.label}POI {setup.confirmation.type.value}",
                  "poi_tf": setup.poi.timeframe.label, "confirmation": setup.confirmation.type.value},
            price=price, ts=now,
        )
        self.guard.record_trade(now)
        self.known_positions[pos.id] = pos
        side = "BUY" if pos.direction.sign > 0 else "SELL"
        self.notifier.send(f"💸 {self.symbol} {side} filled {pos.lots:.2f} lots @ {pos.entry:.{self.spec.price_decimals}f}  "
                           f"SL {pos.stop:.{self.spec.price_decimals}f}  TP {pos.take_profit:.{self.spec.price_decimals}f}  "
                           f"risk {pos.risk_amount:,.0f}  (id {pos.id})")
        return pos

    # ------------------------------------------------------------ approvals
    def process_decisions(self, now: pd.Timestamp) -> None:
        for decision in self.notifier.poll_decisions():
            pending = self.pending.pop(decision.short_id, None)
            if pending is None:
                self.notifier.send(f"{self.symbol}: no pending setup with id {decision.short_id} (expired or already handled)")
                continue
            if decision.approved:
                self.notifier.send(f"✅ {self.symbol}: setup {pending.short_id} approved, sending order")
                self.execute(pending.setup, pending.forecast, now)
            else:
                self.notifier.send(f"❌ {self.symbol}: setup {pending.short_id} skipped")
        for short_id, pending in list(self.pending.items()):
            if now >= pending.expires_at:
                self.pending.pop(short_id)
                self.notifier.send(f"⌛ {self.symbol}: setup {short_id} expired without approval")

    # ------------------------------------------------------------ positions
    def manage_positions(self, views: Dict[Timeframe, CandleSeries]) -> None:
        """Move stops to break-even per the exit rules (no partials, let SL/TP run)."""
        if self.broker is None or not views:
            return
        lowest = views[min(views)]
        if len(lowest) == 0:
            return
        last = lowest.last
        for pos in self.broker.open_positions(self.symbol):
            self.known_positions.setdefault(pos.id, pos)
            if pos.breakeven_done:
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
