"""Live loop: approve / skip / expire flow, execution through the paper broker, close reports, composite fetch."""
from unittest.mock import Mock

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import (Analysis, Bias, BiasDecision, Candle, CandleSeries, Confirmation, ConfirmationType, Direction,
                                Signal, SignalStatus, Timeframe, TradeMode, TradeSetup)
from kronos_trader.data import save_series
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner, build_fetch, short_id_for
from kronos_trader.notify import TelegramNotifier
from kronos_trader.strategy import analyze_structure, map_pois

T = Timeframe
NOW = pd.Timestamp("2026-10-01 09:00")


class FakeEngine:
    """Returns a fixed valid signal on the first call, then no signal."""

    def __init__(self, setup, pois=(), price=1.1000, signal_on_first_call=True):
        self.setup = setup
        self.pois = list(pois)
        self.price = price
        self.signal_on_first_call = signal_on_first_call
        self.calls = 0

    def analyze(self, symbol, views, equity=None, now=None, max_confirmation_age=0, compute_forecasts=False):
        self.calls += 1
        decision = BiasDecision(Bias.BULLISH, TradeMode.FULL, (T.MN_1, T.W_1, T.D_1), (), (T.H_4, T.H_1), (T.MN_1, T.W_1, T.D_1), "test")
        signal = Signal(now, SignalStatus.VALID, self.setup, None, []) if self.calls == 1 and self.signal_on_first_call else None
        return Analysis(symbol, now, self.price, {}, decision, self.pois, signal)


@pytest.fixture
def setup(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2026-10-01 08:45"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    return TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, 1.1200, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H liquidity")


def _runner(setup, broker, last_close=1.1, **kw):
    notifier = TelegramNotifier(dry_run=True)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, max(1.101, last_close), min(1.099, last_close), last_close)]
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(Settings(), "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: NOW, **kw)
    return runner, notifier


def test_dry_run_only_notifies(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.dry_run = True
    runner.settings.prop_firm.max_open_trades = 5
    runner.step()
    assert broker.open_positions() == [] and runner.pending == {}
    assert any("BUY" in m for m in notifier.sent) and any("dry-run" in m for m in notifier.sent)


def test_dry_run_does_not_manage_existing_stops_or_execute_directly(setup, monkeypatch):
    broker = PaperBroker(Settings())
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.25, 1.095, 1.12, 250, 0.0051, 0,
                                    price=1.1, ts=NOW)
    runner, notifier = _runner(setup, broker)
    runner.dry_run = True
    modify = Mock(wraps=broker.modify_stop)
    submit = Mock(wraps=broker.place_market_order)
    monkeypatch.setattr(broker, "modify_stop", modify)
    monkeypatch.setattr(broker, "place_market_order", submit)
    runner.manage_positions(runner.fetch())
    runner.execute(setup, None, NOW)
    modify.assert_not_called()
    submit.assert_not_called()
    assert pos.stop == 1.095 and not pos.breakeven_done


def test_notification_only_scan_does_not_poll_approval_commands(setup, monkeypatch):
    runner, notifier = _runner(setup, PaperBroker(Settings()))
    runner.dry_run = True
    poll = Mock(return_value=[])
    monkeypatch.setattr(notifier, "poll_decisions", poll)
    runner.step(NOW)
    poll.assert_not_called()


def test_notification_only_setup_retries_failure_and_deduplicates_success(setup, monkeypatch):
    runner, notifier = _runner(setup, None)
    runner.dry_run = True
    analysis = runner.engine.analyze("EURUSD", runner.fetch(), now=NOW)
    send = Mock(side_effect=[RuntimeError("temporary Telegram failure"), True])
    monkeypatch.setattr(notifier, "send_setup", send)
    with pytest.raises(RuntimeError, match="Telegram failure"):
        runner.handle_signal(analysis, NOW)
    runner.handle_signal(analysis, NOW)
    runner.handle_signal(analysis, NOW)
    assert send.call_count == 2 and len(runner.seen) == 1


def test_notification_outage_does_not_stop_the_monitor_loop(setup, monkeypatch):
    runner, notifier = _runner(setup, None)
    runner.dry_run = True
    step = Mock(side_effect=[RuntimeError("temporary feed failure"), KeyboardInterrupt()])
    monkeypatch.setattr(runner, "step", step)
    monkeypatch.setattr(notifier, "send", Mock(side_effect=RuntimeError("notification transport unavailable")))
    monkeypatch.setattr("kronos_trader.live.time.sleep", Mock())
    with pytest.raises(KeyboardInterrupt):
        runner.run_forever(poll_seconds=1)
    assert step.call_count == 2


def test_approval_then_execution_and_close_report(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.step(NOW)
    assert len(runner.pending) == 1 and broker.open_positions() == []
    sid = next(iter(runner.pending))
    assert sid == short_id_for((setup.poi.key, str(setup.confirmation.timestamp)))
    assert any("APPROVAL NEEDED" in m and sid in m for m in notifier.sent)

    notifier.queue_decision(sid, approved=True)
    runner.step(NOW + pd.Timedelta(1, unit="min"))
    assert runner.pending == {} and len(broker.open_positions()) == 1
    pos = broker.open_positions()[0]
    assert pos.lots == 1.92 and pos.stop == 1.0949 and pos.take_profit == 1.12
    assert any("filled" in m for m in notifier.sent)

    broker.on_candle("EURUSD", Candle(0, NOW + pd.Timedelta(15, unit="min"), 1.1, 1.125, 1.099, 1.124))
    runner.step(NOW + pd.Timedelta(16, unit="min"))
    assert broker.open_positions() == []
    assert any("take_profit" in m and "P&L" in m for m in notifier.sent)


@pytest.mark.parametrize("news_enabled", [True, False])
def test_approval_rechecks_news_at_execution_time(setup, monkeypatch, news_enabled):
    from kronos_trader.data.calendar import NewsCalendar, NewsEvent

    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.settings.news.enabled = news_enabled
    runner.settings.news.forexfactory = False  # exercise only the loaded calendar; no network
    event = NewsEvent(NOW + pd.Timedelta(31, unit="min"), "USD", "Test release")
    calendar = NewsCalendar([event], before_minutes=30, after_minutes=30)
    runner.engine.calendar = calendar
    assert calendar.blackout("EURUSD", NOW) is None
    runner.step(NOW)
    sid = next(iter(runner.pending))

    approval_time = NOW + pd.Timedelta(2, unit="min")
    assert approval_time < runner.pending[sid].expires_at
    assert calendar.blackout("EURUSD", approval_time) is event
    submit = Mock(wraps=broker.place_market_order)
    monkeypatch.setattr(broker, "place_market_order", submit)
    notifier.queue_decision(sid, approved=True)
    runner.step(approval_time)

    assert runner.pending == {}
    if news_enabled:
        submit.assert_not_called()
        assert broker.open_positions() == []
        assert any("not executed - news blackout: Test release (USD)" in m for m in notifier.sent)
    else:
        submit.assert_called_once()
        assert len(broker.open_positions()) == 1


def test_skip_and_expiry(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.step(NOW)
    sid = next(iter(runner.pending))
    notifier.queue_decision(sid, approved=False)
    runner.step(NOW + pd.Timedelta(1, unit="min"))
    assert runner.pending == {} and broker.open_positions() == [] and any("skipped" in m for m in notifier.sent)

    runner2, notifier2 = _runner(setup, PaperBroker(Settings()))
    runner2.broker.set_price("EURUSD", 1.1)
    runner2.step(NOW)
    runner2.step(NOW + pd.Timedelta(20, unit="min"))      # 15m confirmation -> 15 minute approval window
    assert runner2.pending == {} and any("expired" in m for m in notifier2.sent)


def test_execution_rechecks_rr_and_guard(setup):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker, last_close=1.1150, require_approval=False)   # price ran away: R:R now far below 1:3
    runner.step(NOW)
    assert broker.open_positions() == [] and any("R:R now" in m for m in notifier.sent)

    broker2 = PaperBroker(Settings())
    broker2.set_price("EURUSD", 1.1)
    broker2.place_market_order("EURUSD", Direction.SHORT, 0.1, 1.11, 1.09, 100.0, 0.0101, 4.0, price=1.1, ts=NOW)
    runner2, notifier2 = _runner(setup, broker2, require_approval=False)
    runner2.step(NOW)
    assert len(broker2.open_positions()) == 1 and any("NOT executable" in m for m in notifier2.sent)


@pytest.mark.parametrize("initially_pending", [False, True])
@pytest.mark.parametrize("unknown_quantity", [False, True])
def test_partial_fill_attention_is_reported_and_not_managed_as_confirmed(setup, monkeypatch, initially_pending, unknown_quantity):
    class AttentionBroker(PaperBroker):
        execution_halt_reason = None

        def place_market_order(self, *args, **kwargs):
            pos = super().place_market_order(*args, **kwargs)
            pos.status = "pending" if initially_pending else "attention"
            if not initially_pending:
                mark_attention(pos)
            return pos

    def mark_attention(pos):
        pos.status = "attention"
        pos.lots = 0.0 if unknown_quantity else 0.25
        pos.meta.update(filled_units=0 if unknown_quantity else 25000, requested_units=100000, parent_status="Cancelled",
                        attention_reason="partial fill requires reconciliation", protection_verified=False,
                        exposure_unverified=unknown_quantity)
        broker.execution_halt_reason = pos.meta["attention_reason"]

    broker = AttentionBroker(Settings())
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    if initially_pending:
        assert pos.id in runner.unconfirmed
        mark_attention(pos)
    modify = Mock(wraps=broker.modify_stop)
    monkeypatch.setattr(broker, "modify_stop", modify)
    views = {T.MIN_15: CandleSeries.from_records([(1.1, 1.2, 1.09, 1.1)], T.MIN_15,
                                               start="2026-10-01 09:00", symbol="EURUSD")}
    runner.manage_positions(views)
    runner.manage_positions(views)
    messages = [m for m in notifier.sent if "protection unverified" in m]
    assert len(messages) == 1 and "entries halted" in messages[0]
    if unknown_quantity:
        assert "exposure quantity unverified" in messages[0] and "0.00 lots" not in messages[0]
    else:
        assert "0.25" in messages[0]
    assert pos.id in runner.known_positions and pos.id not in runner.unconfirmed
    assert not any("did not fill" in m or "fill confirmed" in m for m in notifier.sent)
    modify.assert_not_called()
    assert not pos.breakeven_done

    pos.lots = 0.5
    pos.meta["filled_units"] = 50000
    runner.manage_positions(views)
    assert len([m for m in notifier.sent if "protection unverified" in m]) == 2


def test_attention_alert_retries_after_notifier_failure(setup, monkeypatch):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker)
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.25, 1.095, 1.12, 250, 0.0051, 4,
                                    price=1.1, ts=NOW)
    pos.status = "attention"
    pos.meta.update(attention_reason="partial fill requires reconciliation", filled_units=25000)
    send = Mock(side_effect=[RuntimeError("temporary notification failure"), None])
    monkeypatch.setattr(notifier, "send", send)
    with pytest.raises(RuntimeError, match="notification failure"):
        runner.report_execution_attention(pos)
    runner.report_execution_attention(pos)
    assert send.call_count == 2
    assert pos.id in runner.known_positions


def test_build_fetch_combines_cache_and_broker(tmp_path):
    settings = Settings()
    daily = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 5, T.D_1, start="2026-09-20", symbol="OANDA:EURUSD")
    save_series(daily, tmp_path)

    class FeedBroker(PaperBroker):
        def get_candles(self, symbol, timeframe, count=500):
            return CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 3, timeframe, start="2026-10-01", symbol=symbol)

    fetch = build_fetch(settings, "EURUSD", cache_dir=tmp_path, broker=FeedBroker(settings), broker_timeframes=[T.MIN_15, T.H_1])
    views = fetch()
    assert set(views) == {T.D_1, T.MIN_15, T.H_1}
    assert len(views[T.D_1]) == 5 and views[T.MIN_15].symbol == "EURUSD"
    with pytest.raises(RuntimeError):
        build_fetch(settings, "GBPUSD", cache_dir=tmp_path, broker=None, broker_timeframes=[])()


def test_build_fetch_falls_back_to_cache_when_broker_fails(tmp_path):
    settings = Settings()
    assert T.MN_1 in settings.live.broker_timeframes          # the broker feeds every timeframe by default
    for tf, lookback in settings.structure.lookback_by_timeframe.items():
        assert settings.live.broker_bar_counts[tf] >= lookback
    daily = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 5, T.D_1, start="2026-09-20", symbol="OANDA:EURUSD")
    save_series(daily, tmp_path)

    class FlakyBroker(PaperBroker):
        def get_candles(self, symbol, timeframe, count=500):
            if timeframe is T.D_1:
                raise RuntimeError("IBKR returned no bars")
            return CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 3, timeframe, start="2026-10-01", symbol=symbol)

    fetch = build_fetch(settings, "EURUSD", cache_dir=tmp_path, broker=FlakyBroker(settings), broker_timeframes=[T.H_1, T.D_1])
    views = fetch()
    assert len(views[T.D_1]) == 5 and len(views[T.H_1]) == 3      # cached daily candles, live hourly ones
    with pytest.raises(RuntimeError):                               # nothing cached to fall back on
        build_fetch(settings, "EURUSD", cache_dir=None, broker=FlakyBroker(settings), broker_timeframes=[T.D_1])()


class RaisingPriceBroker(PaperBroker):
    def current_price(self, symbol):
        raise RuntimeError("no quote")


def test_late_approval_is_not_executed(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.step(NOW)
    sid = next(iter(runner.pending))
    notifier.queue_decision(sid, approved=True)
    runner.step(NOW + pd.Timedelta(16, unit="min"))         # the 15-minute approval window has passed
    assert broker.open_positions() == [] and runner.pending == {}
    assert any("approved too late" in m for m in notifier.sent)


def test_no_current_price_means_no_order(setup):
    runner, notifier = _runner(setup, RaisingPriceBroker(Settings()), require_approval=False)
    runner.step(NOW)
    assert runner.broker.open_positions() == [] and any("no current price" in m for m in notifier.sent)


@pytest.mark.parametrize("price", [float("inf"), float("-inf"), float("nan"), None, "not-a-price", 0.0, -1.0],
                         ids=["positive_infinity", "negative_infinity", "nan", "none", "non_numeric", "zero", "negative"])
def test_invalid_executable_quote_blocks_order(setup, monkeypatch, price):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker, require_approval=False)
    submit = Mock(wraps=broker.place_market_order)
    monkeypatch.setattr(broker, "place_market_order", submit)
    monkeypatch.setattr(broker, "current_price", lambda symbol: price)

    runner.step(NOW)

    submit.assert_not_called()
    assert broker.open_positions() == [] and runner.known_positions == {}
    assert any("no current price" in m for m in notifier.sent)
    assert not any("filled" in m or "submitted" in m for m in notifier.sent)


def test_queued_approval_rechecks_data_freshness_before_expiry(setup, monkeypatch):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker)
    runner.fetch = lambda: {T.MIN_5: CandleSeries.from_records(
        [(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_5, start="2026-10-01 08:45", symbol="EURUSD")}
    submit = Mock(wraps=broker.place_market_order)
    monkeypatch.setattr(broker, "place_market_order", submit)
    assert runner.settings.live.require_fresh_data and runner.settings.live.max_data_age_bars == 2
    runner.step(NOW)
    assert not runner.stale and len(runner.pending) == 1
    sid = next(iter(runner.pending))
    approved_at = NOW + pd.Timedelta(11, unit="min")
    assert approved_at < runner.pending[sid].expires_at

    notifier.queue_decision(sid, approved=True)
    runner.step(approved_at)

    assert T.MIN_5 in runner.stale and runner.pending == {}
    submit.assert_not_called()
    assert broker.open_positions() == [] and runner.known_positions == {}
    assert any("not executed" in m and "stale" in m for m in notifier.sent)


def test_order_failure_is_reported_not_raised(setup):
    class RejectingBroker(PaperBroker):
        def place_market_order(self, *args, **kwargs):
            raise RuntimeError("not accepted by TWS")

    broker = RejectingBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    assert broker.open_positions() == [] and any("order failed" in m and "not accepted" in m for m in notifier.sent)


def test_paper_broker_is_advanced_by_the_loop(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    candles = [(1.1, 1.101, 1.099, 1.1)] * 3
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(candles, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(Settings(), "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    runner.step(NOW)
    assert len(broker.open_positions()) == 1
    candles.append((1.1, 1.125, 1.099, 1.124))                # the 09:00 candle trades through the 1.12 target
    runner.step(NOW + pd.Timedelta(15, unit="min"))           # it is closed at 09:15 and fed to the paper broker
    assert broker.open_positions() == [] and sum("take_profit" in m for m in notifier.sent) == 1
    runner.step(NOW + pd.Timedelta(30, unit="min"))           # the same candles again: fed once, reported once
    assert sum("take_profit" in m for m in notifier.sent) == 1


def test_stale_data_blocks_new_setups(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW + pd.Timedelta(3, unit="h"))              # the 15m candles ended at 09:00, it is noon
    assert T.MIN_15 in runner.stale and broker.open_positions() == [] and runner.pending == {}
    assert any("stale" in m for m in notifier.sent)


def test_build_fetch_skips_missing_timeframes_and_backs_off(tmp_path):
    settings = Settings()
    daily = CandleSeries.from_records([(1, 2, 0.5, 1.5)] * 5, T.D_1, start="2026-09-20", symbol="OANDA:EURUSD")
    save_series(daily, tmp_path)
    calls = []

    class DownBroker(PaperBroker):
        def get_candles(self, symbol, timeframe, count=500):
            calls.append(timeframe)
            raise RuntimeError("No market data permissions")

    fetch = build_fetch(settings, "EURUSD", cache_dir=tmp_path, broker=DownBroker(settings),
                        broker_timeframes=[T.MIN_5, T.D_1], retry_after_seconds=600)
    views = fetch()
    assert set(views) == {T.D_1} and fetch.report.skipped == [T.MIN_5] and fetch.report.sources[T.D_1] == "cache"
    assert len(calls) == 2
    fetch()                                                   # the broker is left alone while it is down
    assert len(calls) == 2 and "cache" in fetch.report.describe()


def test_morning_briefing_once_per_weekday(setup):
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 06:00", symbol="EURUSD")}
    runner = LiveRunner(Settings(), "EURUSD", fetch, notifier=notifier, engine=FakeEngine(setup, signal_on_first_call=False),
                        clock=lambda: NOW)
    runner.step(pd.Timestamp("2026-10-01 06:30"))            # 08:30 Amsterdam: too early
    assert not any("morning analysis" in m for m in notifier.sent)
    runner.step(pd.Timestamp("2026-10-01 06:45"))            # 08:45: the briefing
    runner.step(pd.Timestamp("2026-10-01 07:00"))            # not again today
    assert sum("morning analysis" in m for m in notifier.sent) == 1
    runner.step(pd.Timestamp("2026-10-03 07:00"))            # Saturday: nothing
    runner.step(pd.Timestamp("2026-10-05 06:50"))            # Monday: again
    assert sum("morning analysis" in m for m in notifier.sent) == 2


def test_poi_touch_is_announced_once(setup):
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    engine = FakeEngine(setup, pois=[setup.poi], price=101.0, signal_on_first_call=False)   # price inside the bullish POI
    runner = LiveRunner(Settings(), "EURUSD", fetch, notifier=notifier, engine=engine, clock=lambda: NOW)
    runner.step(NOW)
    runner.step(NOW + pd.Timedelta(15, unit="min"))
    touches = [m for m in notifier.sent if "inside the" in m and "POI" in m]
    assert len(touches) == 1 and "waiting for a confirmation" in touches[0]


def test_morning_briefing_retries_failed_analysis_delivery(setup, monkeypatch):
    runner, notifier = _runner(setup, None)
    analysis = runner.engine.analyze("EURUSD", runner.fetch(), now=NOW)
    send_analysis = Mock(side_effect=[RuntimeError("temporary delivery failure"), None])
    monkeypatch.setattr(notifier, "send_analysis", send_analysis)

    with pytest.raises(RuntimeError, match="temporary delivery failure"):
        runner.morning_briefing(analysis, NOW)
    assert runner._briefed_on is None
    runner.morning_briefing(analysis, NOW)
    runner.morning_briefing(analysis, NOW)
    assert send_analysis.call_count == 2
    assert runner._briefed_on == NOW.date()


def test_poi_touch_retries_failed_delivery(setup, monkeypatch):
    runner, notifier = _runner(setup, None)
    engine = FakeEngine(setup, pois=[setup.poi], price=101.0, signal_on_first_call=False)
    analysis = engine.analyze("EURUSD", runner.fetch(), now=NOW)
    send = Mock(side_effect=[RuntimeError("temporary delivery failure"), None])
    monkeypatch.setattr(notifier, "send", send)

    with pytest.raises(RuntimeError, match="temporary delivery failure"):
        runner.announce_poi_touch(analysis)
    assert setup.poi.key not in runner._touched
    runner.announce_poi_touch(analysis)
    runner.announce_poi_touch(analysis)
    assert send.call_count == 2
    assert setup.poi.key in runner._touched
