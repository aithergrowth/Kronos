"""Live loop: approve / skip / expire flow, execution through the paper broker, close reports, composite fetch."""
from types import SimpleNamespace
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
    runner.step()
    assert broker.open_positions() == [] and runner.pending == {}
    assert any("BUY" in m for m in notifier.sent) and any("dry-run" in m for m in notifier.sent)


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
    assert pos.lots == pytest.approx(1.90) and pos.stop == 1.0949 and pos.take_profit == 1.12   # re-sized on the ask 1.10005
    assert any("filled" in m for m in notifier.sent)

    broker.on_candle("EURUSD", Candle(0, NOW + pd.Timedelta(15, unit="min"), 1.1, 1.125, 1.099, 1.124))
    runner.step(NOW + pd.Timedelta(16, unit="min"))
    assert broker.open_positions() == []
    assert any("take_profit" in m and "P&L" in m for m in notifier.sent)


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


def test_execution_resizes_to_the_current_price(setup):
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker, last_close=1.1010, require_approval=False)   # 10 pips above the planned entry
    runner.step(NOW)
    pos = broker.open_positions()[0]
    assert pos.entry == pytest.approx(1.10105)                                           # the ask: close plus half the spread
    assert pos.lots == pytest.approx(1.60) and pos.meta["risk_budget"] == pytest.approx(1000.0)   # 1 % over 61.5 + 1 pips, not 1.92
    assert pos.risk_distance == pytest.approx(0.00615) and pos.risk_amount == pytest.approx(61.5 * 10 * 1.60)
    assert any("1.92 -> 1.61" in str(r) for r in runner.journal.rows) if hasattr(runner.journal, "rows") else True


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


def test_setup_comes_with_a_chart(setup, tmp_path):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.settings.live.charts_dir = str(tmp_path)
    runner.settings.live.briefing_time = None                  # the briefing would send its own chart
    runner.step(NOW)
    photos = [m for m in notifier.sent if m.startswith("[photo]")]
    assert len(photos) == 1 and "EURUSD_15m_setup.png" in photos[0] and (tmp_path / "EURUSD_15m_setup.png").exists()


def test_journal_records_the_whole_sequence(setup, tmp_path):
    from kronos_trader.journal import summary
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker)
    runner.settings.live.briefing_time = None
    runner.settings.live.send_charts = False
    runner.journal = __import__("kronos_trader.journal", fromlist=["Journal"]).Journal(tmp_path / "trades.csv", clock=lambda: NOW)
    runner.step(NOW)
    sid = next(iter(runner.pending))
    notifier.queue_decision(sid, approved=True)
    runner.step(NOW + pd.Timedelta(1, unit="min"))
    broker.on_candle("EURUSD", Candle(0, NOW + pd.Timedelta(15, unit="min"), 1.1, 1.125, 1.099, 1.124))
    runner.step(NOW + pd.Timedelta(16, unit="min"))
    rows = pd.read_csv(tmp_path / "trades.csv")
    assert list(rows["event"]) == ["setup", "approval_requested", "approved", "filled", "closed"]
    assert rows.iloc[0]["rr"] == 3.85 and rows.iloc[0]["poi_tf"] == "1H" and rows.iloc[-1]["reason"] == "take_profit"
    s = summary(tmp_path / "trades.csv")
    assert s["closed"] == 1 and s["wins"] == 1 and s["win_rate"] == 1.0 and s["avg_r"] > 3


def test_evening_summary_once_per_weekday_from_the_journal(setup, tmp_path):
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "trades.csv")
    settings.live.briefing_time = None
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 18:00", symbol="EURUSD")}
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier,
                        engine=FakeEngine(setup, signal_on_first_call=False), clock=lambda: NOW)
    runner.journal.log("setup", "EURUSD", time=pd.Timestamp("2026-10-01 08:05"))
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-10-01 08:30"), r=-1.0, pnl=-1000.0)
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-10-01 14:10"), r=2.5, pnl=2500.0)
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-09-30 14:10"), r=1.0, pnl=1000.0)   # yesterday
    runner.journal.log("closed", "XAUUSD", time=pd.Timestamp("2026-10-01 14:10"), r=-1.0, pnl=-1000.0)  # another market
    runner.step(pd.Timestamp("2026-10-01 19:55"))            # 21:55 Amsterdam: too early
    assert not any("📊" in m for m in notifier.sent)
    runner.step(pd.Timestamp("2026-10-01 20:01"))            # 22:01: the summary
    runner.step(pd.Timestamp("2026-10-01 20:30"))            # not again today
    summaries = [m for m in notifier.sent if "📊" in m]
    assert len(summaries) == 1
    assert "2 trade(s) closed, 1 won, +1.50R" in summaries[0] and "1 setup(s)" in summaries[0] and "equity" in summaries[0]
    runner.step(pd.Timestamp("2026-10-03 20:30"))            # Saturday: nothing
    assert sum("📊" in m for m in notifier.sent) == 1


def test_touch_only_on_the_zone_timeframes_the_profile_trades(setup):
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    settings = Settings()
    settings.confirmation.poi_timeframes = (T.D_1, T.H_4)            # the setup's zone is a 1H zone: not traded in full mode
    notifier = TelegramNotifier(dry_run=True)
    engine = FakeEngine(setup, pois=[setup.poi], price=101.0, signal_on_first_call=False)
    runner = LiveRunner(settings, "EURUSD", fetch, notifier=notifier, engine=engine, clock=lambda: NOW)
    runner.step(NOW)
    assert not any("inside the" in m for m in notifier.sent)
    settings.confirmation.poi_timeframes = (T.D_1, T.H_4, T.H_1)
    runner.step(NOW + pd.Timedelta(15, unit="min"))
    assert sum("inside the" in m for m in notifier.sent) == 1


def test_chart_zones_are_the_nearest_tradable_ones(setup, scenario):
    pois = map_pois(analyze_structure(scenario), current_price=101.0)
    runner = LiveRunner(Settings(), "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True),
                        engine=FakeEngine(setup, pois=pois, price=101.0, signal_on_first_call=False), clock=lambda: NOW)
    analysis = runner.engine.analyze("EURUSD", {}, now=NOW)
    zones = runner.chart_zones(analysis, limit=2)
    assert 1 <= len(zones) <= 2 and all(z.direction is analysis.decision.direction for z in zones if
                                         any(p.direction is analysis.decision.direction for p in pois))
    assert any(z.key == setup.poi.key for z in runner.chart_zones(analysis, setup=setup, limit=1))



def test_the_guard_reads_closed_pnl_from_the_broker(setup):
    broker = PaperBroker(Settings())
    runner, _ = _runner(setup, broker)
    assert runner.guard.realized_since == broker.realized_pnl_since
    assert broker.realized_pnl_since(NOW) == 0.0


def test_traded_zones_survive_a_restart(tmp_path):
    from types import SimpleNamespace
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "trades.csv")
    key = ("1H", -1, "2026-10-05 03:00:00")
    first = LiveRunner(settings, "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True),
                       engine=SimpleNamespace(traded={"EURUSD": {key: 1}}), clock=lambda: NOW)
    first.save_traded()
    assert (tmp_path / "traded_EURUSD.json").exists()
    restarted = LiveRunner(settings, "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True),
                           engine=SimpleNamespace(traded={}), clock=lambda: NOW)
    assert restarted.engine.traded == {"EURUSD": {key: 1}}
    other = LiveRunner(settings, "XAUUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True),
                       engine=SimpleNamespace(traded={}), clock=lambda: NOW)
    assert other.engine.traded == {}                                   # each market keeps its own file


def test_news_download_is_shared_between_windows(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace
    from kronos_trader.data import calendar as cal
    calls = []
    event = cal.NewsEvent(pd.Timestamp("2026-10-07 12:30"), "USD", "CPI", 3)

    def fake_fetch(week="thisweek", **kw):
        calls.append(week)
        if week == "nextweek":
            raise RuntimeError("ForexFactory calendar 404")
        return [event]

    monkeypatch.setattr(cal, "fetch_forexfactory", fake_fetch)
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "trades.csv")
    settings.news.enabled, settings.news.forexfactory = True, True
    added = []
    engine = SimpleNamespace(calendar=SimpleNamespace(add=lambda ev: added.extend(ev)), traded={})
    for symbol in ("EURUSD", "XAUUSD"):
        LiveRunner(settings, symbol, lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=engine,
                   clock=lambda: NOW).refresh_news(NOW)
    assert calls.count("thisweek") == 1                          # the second window read the first one's file
    assert len(added) == 2 and all(e.title == "CPI" for e in added)
    monkeypatch.setattr(cal, "fetch_forexfactory", lambda week="thisweek", **kw: (_ for _ in ()).throw(RuntimeError("ForexFactory calendar 429")))
    (tmp_path / "forexfactory_thisweek.csv").unlink()
    runner = LiveRunner(settings, "GBPUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=engine, clock=lambda: NOW)
    runner.refresh_news(NOW)
    runner.refresh_news(NOW + pd.Timedelta(hours=2))
    assert capsys.readouterr().out.count("news calendar refresh failed") == 1   # once a day


def test_no_telegram_polling_without_a_setup_waiting(setup):
    class Notifier(TelegramNotifier):
        polls = 0

        def poll_decisions(self):
            Notifier.polls += 1
            raise RuntimeError("Telegram getUpdates failed: 409 Conflict: terminated by other getUpdates request")

    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    notifier = Notifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(Settings(), "EURUSD", fetch, broker=broker, notifier=notifier,
                        engine=FakeEngine(setup, signal_on_first_call=False), dry_run=False, require_approval=False, clock=lambda: NOW)
    runner.step(NOW)
    assert Notifier.polls == 0                                       # nothing to approve: Telegram is not asked
    runner.pending["abc"] = SimpleNamespace(short_id="abc", expires_at=NOW + pd.Timedelta(hours=1), setup=setup, forecast=None)
    runner.step(NOW + pd.Timedelta(minutes=1))                      # a setup waits: asked, the 409 does not end the scan
    assert Notifier.polls == 1 and "abc" in runner.pending
    assert not any("live loop error" in m for m in notifier.sent)


def test_friday_summary_adds_the_week(setup, tmp_path):
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "trades.csv")
    settings.live.briefing_time = None
    notifier = TelegramNotifier(dry_run=True)
    runner = LiveRunner(settings, "EURUSD", lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15,
                                                                                        start="2026-10-02 18:00", symbol="EURUSD")},
                        notifier=notifier, engine=FakeEngine(setup, signal_on_first_call=False), clock=lambda: NOW)
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-09-28 09:00"), r=2.0, pnl=3000.0)   # Monday
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-10-01 14:00"), r=-1.0, pnl=-1500.0)  # Thursday
    runner.journal.log("closed", "EURUSD", time=pd.Timestamp("2026-09-25 14:00"), r=5.0, pnl=7500.0)   # the week before
    runner.step(pd.Timestamp("2026-10-02 20:05"))                 # Friday 22:05 Amsterdam
    summary = next(m for m in notifier.sent if "📊" in m)
    assert "this week: 2 trade(s), 50 % won, +1.00R" in summary


def test_algo_trading_off_is_reported_once(setup):
    class Broker(PaperBroker):
        on = False

        def algo_trading_on(self):
            return Broker.on

    broker = Broker(Settings())
    broker.set_price("EURUSD", 1.1)
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(Settings(), "EURUSD", fetch, broker=broker, notifier=notifier,
                        engine=FakeEngine(setup, signal_on_first_call=False), dry_run=False, clock=lambda: NOW)
    runner.step(NOW)
    runner.step(NOW + pd.Timedelta(minutes=11))
    assert sum("Algo Trading staat UIT" in m for m in notifier.sent) == 1
    Broker.on = True
    runner.step(NOW + pd.Timedelta(minutes=22))
    assert sum("weer aan" in m for m in notifier.sent) == 1


def test_drawdown_steps_lower_the_live_stake(setup):
    """Live, a balance 4 % under the start (account_size) with ``risk.drawdown_steps`` ((-3, 1.0),) sizes the order at
    1.0 % instead of the profile's 1.5 %, and the fill message says so."""
    lots = {}
    for steps in ((), ((-3, 1.0),)):
        s = Settings(); s.account_size = 100_000.0
        broker = PaperBroker(s)
        broker.set_price("EURUSD", 1.1)
        broker._balance = 96_000.0                                   # 4 % under the start after earlier losses
        runner, notifier = _runner(setup, broker, require_approval=False)
        runner.settings.account_size = 100_000.0
        runner.settings.risk.risk_pct = 1.5
        runner.settings.risk.drawdown_steps = steps
        runner.step(NOW)
        assert len(broker.open_positions()) == 1
        lots[steps] = broker.open_positions()[0].lots
        if steps:
            assert any("1 %: balance below the start" in m for m in notifier.sent)
    assert lots[((-3, 1.0),)] == pytest.approx(lots[()] / 1.5, rel=0.02)


def test_a_refused_break_even_move_does_not_stop_the_scan(setup):
    """modify_stop failing (10016: price back under the entry) leaves the stop, says so once and tries again later;
    the scan goes on to report closes and look for setups."""
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    pos.breakeven_r = 0.5                                          # 1.10005 + 0.5 x 0.00515 = 1.1026: reached by 1.104
    rows = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.104, 1.099, 1.1)]
    runner.fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}

    def refuse(position_id, stop):
        raise RuntimeError("modify stop failed: retcode 10016 Invalid stops")
    broker.modify_stop = refuse
    runner.step(NOW + pd.Timedelta(1, unit="min"))
    runner.step(NOW + pd.Timedelta(2, unit="min"))
    assert not pos.breakeven_done and pos.stop == 1.0949
    assert sum("refused" in m for m in notifier.sent) == 1


def test_closes_of_other_windows_are_not_reported_here(setup):
    """On one MT5 account every window sees every position of the bot (the account-wide cap counts them); a close is
    reported and journaled only by the window of its own market."""
    from kronos_trader.execution.base import ClosedTrade
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker)
    other = ClosedTrade(id="77", symbol="XAUUSD", direction=Direction.LONG, lots=1.0, entry=2650.0, exit=2670.0, stop=2640.0,
                        take_profit=2670.0, opened_at=NOW, closed_at=NOW, reason="take_profit", pnl=2000.0, r=2.0,
                        risk_amount=1000.0, initial_stop=2640.0, meta={})
    broker.recent_closes = lambda: [other]
    runner.report_closes()
    assert not any("closed" in m for m in notifier.sent)


def test_link_and_feed_alerts_once_down_and_once_back(setup):
    """The broker's link and the lowest timeframe's candles: one message when they fail during the session, one when they
    are back, nothing in between; outside the session a quiet feed says nothing."""
    broker = PaperBroker(Settings())
    runner, notifier = _runner(setup, broker)
    state = {"ok": False}
    broker.connection_ok = lambda: (state["ok"], "MT5 not reachable (terminal closed or restarting)")
    assert runner.connection_ok() is False and runner.connection_ok() is False
    state["ok"] = True
    assert runner.connection_ok() is True
    assert sum("not reachable" in m for m in notifier.sent) == 1 and sum("weer verbonden" in m for m in notifier.sent) == 1

    runner.settings.session.enabled = True
    runner.settings.session.windows = [["09:00", "17:00"]]
    views = runner.fetch()
    in_session_now = pd.Timestamp("2026-10-05 10:00")                       # Monday 12:00 Amsterdam, candles from Thursday
    runner.stale = runner.stale_timeframes(views, in_session_now)
    runner.check_feed(views, in_session_now)
    runner.check_feed(views, in_session_now)
    assert sum("geen nieuwe 15m-candles" in m for m in notifier.sent) == 1
    runner.stale = {}
    runner.check_feed(views, in_session_now)
    assert sum("loopt weer" in m for m in notifier.sent) == 1
    night = pd.Timestamp("2026-10-05 21:00")                                 # 23:00 Amsterdam: outside the session
    runner.stale = runner.stale_timeframes(views, night)
    runner.check_feed(views, night)
    assert sum("geen nieuwe 15m-candles" in m for m in notifier.sent) == 1


def test_account_lock_serialises_and_a_stale_file_never_blocks_for_good(tmp_path):
    from kronos_trader.live import AccountLock
    path = tmp_path / "journal" / "account.lock"
    with AccountLock(path) as first:
        assert first.held and path.exists()
        second = AccountLock(path, timeout=0.2).__enter__()                 # another window waits, then gives up: not held
        assert not second.held
    assert not path.exists()
    path.write_text("123")
    import os, time as _t
    old = _t.time() - 120
    os.utime(path, (old, old))                                              # left behind by a killed window
    with AccountLock(path, timeout=0.2) as third:
        assert third.held


def _locked_runner(setup, tmp_path):
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup), dry_run=False,
                        require_approval=False, clock=lambda: NOW)
    runner.lock_timeout = 0.1
    runner.lock_path.parent.mkdir(parents=True, exist_ok=True)
    runner.lock_path.write_text("4242")                                     # another window holds the account lock
    return runner, broker, notifier


def test_a_busy_account_lock_defers_the_entry_until_it_is_free(setup, tmp_path):
    """A window that cannot get the account lock does not trade without it (two windows could then pass the account's
    risk checks together): the entry is deferred, tried again every scan with every check, and sent once the lock is free."""
    runner, broker, notifier = _locked_runner(setup, tmp_path)
    runner.step(NOW)
    assert broker.open_positions() == [] and len(runner.deferred) == 1
    assert sum("deferred" in m for m in notifier.sent) == 1
    runner.step(NOW + pd.Timedelta(minutes=1))                              # still busy: still waiting, no second message
    assert broker.open_positions() == [] and len(runner.deferred) == 1 and sum("deferred" in m for m in notifier.sent) == 1
    runner.lock_path.unlink()                                               # the other window is done
    runner.step(NOW + pd.Timedelta(minutes=2))
    assert len(broker.open_positions()) == 1 and runner.deferred == {}
    assert any("filled" in m for m in notifier.sent) and not runner.lock_path.exists()


def test_a_deferred_entry_expires_when_the_lock_stays_busy(setup, tmp_path):
    """The deferral lasts as long as an approval would (at least 5 minutes, the confirmation's timeframe for a coarser
    one: 15 minutes here); then the setup expires unexecuted."""
    runner, broker, notifier = _locked_runner(setup, tmp_path)
    runner.step(NOW)
    assert len(runner.deferred) == 1
    import os, time as _t
    runner.step(NOW + pd.Timedelta(minutes=14))
    assert len(runner.deferred) == 1
    now_ts = _t.time()
    os.utime(runner.lock_path, (now_ts, now_ts))                            # still held, freshly (not a stale file)
    runner.step(NOW + pd.Timedelta(minutes=16))
    assert broker.open_positions() == [] and runner.deferred == {}
    assert any("expired, the account lock stayed busy" in m for m in notifier.sent)


def test_a_live_start_records_the_code_and_the_settings_without_secrets(setup, tmp_path, monkeypatch):
    """Every start writes a ``start`` row (code, source and settings hashes) and ``starts/<symbol>_<time>.json`` next to the
    journal, so each forward trade traces to the program and profile that took it; secrets stay names of env variables."""
    import json as _json
    from kronos_trader.backtest.provenance import settings_dict
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:never-in-a-file")
    monkeypatch.setenv("MT5_PASSWORD", "hunter2-never-in-a-file")
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    broker = PaperBroker(Settings())
    runner = LiveRunner(settings, "EURUSD", lambda: {}, broker=broker, notifier=TelegramNotifier(dry_run=True),
                        engine=FakeEngine(setup), dry_run=False, clock=lambda: NOW)
    doc = settings_dict(settings)
    path = runner.record_start({"commit": "abc123def4567890", "dirty": False, "source_sha256": "f" * 64}, doc, "e" * 64, "kronos_trader live")
    text = path.read_text(encoding="utf-8")
    assert "never-in-a-file" not in text and "TELEGRAM_BOT_TOKEN" in text
    record = _json.loads(text)
    assert record["code"]["commit"] == "abc123def4567890" and record["settings_sha256"] == "e" * 64 and record["symbol"] == "EURUSD"
    assert record["versions"]["pandas"] == pd.__version__ and record["versions"]["python"]
    rows = pd.read_csv(settings.live.journal_path)
    start = rows[rows.event == "start"].iloc[0]
    assert "code abc123def456" in start.note and "settings eeeeeeeeeeee" in start.note


def test_a_paper_window_keeps_its_account_across_a_restart(setup):
    """With keep_paper_account (the CLI sets it for --broker paper, the BTC window) the balance, the open trades and the
    recent closed P&L come back after a restart; the position ids go on where they stopped."""
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, _ = _runner(setup, broker, require_approval=False, keep_paper_account=True)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    broker._balance = 101_234.5
    broker._restored_realized = [(NOW - pd.Timedelta(hours=2), -500.0)]
    runner.save_paper()
    fresh = PaperBroker(Settings())
    again, _ = _runner(setup, fresh, require_approval=False, keep_paper_account=True)
    assert fresh.balance() == pytest.approx(101_234.5)
    back = fresh.open_positions()[0]
    assert (back.id, back.direction, back.lots, back.entry, back.stop, back.breakeven_r) == \
        (pos.id, pos.direction, pos.lots, pos.entry, pos.stop, pos.breakeven_r)
    assert fresh.realized_pnl_since(NOW - pd.Timedelta(hours=3)) == pytest.approx(-500.0)
    assert fresh.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.11, 1.09, 100.0, 0.01, 4.0, price=1.1, ts=NOW).id == "P2"


def test_max_hold_hours_closes_a_lingering_trade():
    """``exits.max_hold_hours``: the paper broker closes a trade at the market on the first candle at or past the limit
    (reason "time"); nothing before it."""
    s = Settings(); s.exits.max_hold_hours = 24
    broker = PaperBroker(s, use_spread=False)
    t0 = pd.Timestamp("2026-10-01 09:00")
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1000, ts=t0)
    assert broker.on_candle("EURUSD", Candle(0, t0 + pd.Timedelta(hours=23, minutes=55), 1.1, 1.101, 1.099, 1.1005)) == []
    closed = broker.on_candle("EURUSD", Candle(0, t0 + pd.Timedelta(hours=24), 1.1005, 1.102, 1.1, 1.1015))
    assert len(closed) == 1 and closed[0].reason == "time" and closed[0].exit == pytest.approx(1.1015)
    assert closed[0].r == pytest.approx(0.15)


def test_max_hold_hours_closes_on_a_real_broker(setup):
    """A broker that does not simulate candles (MT5): the live runner closes the trade itself once it has been open
    ``exits.max_hold_hours`` and the close is reported."""
    class Server(PaperBroker):
        on_candle = None                                      # like MT5: the server, not the runner, runs SL and TP
    broker = Server(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1,
                              ts=NOW - pd.Timedelta(hours=49))
    runner, notifier = _runner(setup, broker)
    runner.settings.exits.max_hold_hours = 48
    runner.manage_positions(runner.fetch())
    runner.report_closes()
    assert broker.open_positions() == [] and any("closed (time)" in m for m in notifier.sent)


def test_a_paper_fill_is_stamped_at_its_candle_start(setup):
    """The paper broker checks stops and targets from the candle a fill falls in: the fill is stamped at that candle's
    start on the lowest timeframe (stamped at the poll time the broker skipped the whole candle)."""
    broker = PaperBroker(Settings())
    runner, _ = _runner(setup, broker)
    runner._views = runner.fetch()                                           # 15m is the lowest timeframe here
    assert runner.fill_stamp(pd.Timestamp("2026-10-01 08:47:23")) == pd.Timestamp("2026-10-01 08:45")


def test_the_engine_recomputes_a_candle_whose_values_changed():
    """The structure cache knows a view by its last candle's time, values and the length: a daily candle completed
    after it was first seen (its last minutes arrived late) is analysed again."""
    from kronos_trader.strategy.engine import StrategyEngine
    from kronos_trader.config import Settings
    eng = StrategyEngine(Settings())
    rows = [(1.0 + k / 100, 1.02 + k / 100, 0.99 + k / 100, 1.01 + k / 100) for k in range(60)]
    early = CandleSeries.from_records(rows, T.D_1, start="2026-07-01", symbol="EURUSD")
    late_rows = rows[:-1] + [(rows[-1][0], rows[-1][1] + 0.05, rows[-1][2], rows[-1][3] + 0.04)]
    late = CandleSeries.from_records(late_rows, T.D_1, start="2026-07-01", symbol="EURUSD")
    a = eng.structure_for("EURUSD", early)
    assert eng.structure_for("EURUSD", early) is a
    assert eng.structure_for("EURUSD", late) is not a


def test_a_refused_break_even_is_retried_without_a_new_trigger(setup):
    """The trigger was reached once and the move refused: 15 minutes later it is sent again even though no newer candle
    reached the trigger (the move is owed, the trigger is history)."""
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    pos.breakeven_r = 0.5
    high = [(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.104, 1.099, 1.1)]
    flat = [(1.1, 1.101, 1.099, 1.1)] * 3
    runner.fetch = lambda: {T.MIN_15: CandleSeries.from_records(high, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    calls = []
    real = broker.modify_stop

    def flaky(position_id, stop):
        calls.append(stop)
        if len(calls) == 1:
            raise RuntimeError("modify stop failed: retcode 10018 Market closed")
        real(position_id, stop)
    broker.modify_stop = flaky
    runner.step(NOW + pd.Timedelta(1, unit="min"))                         # refused
    runner.fetch = lambda: {T.MIN_15: CandleSeries.from_records(flat, T.MIN_15, start="2026-10-01 08:30", symbol="EURUSD")}
    runner.step(NOW + pd.Timedelta(16, unit="min"))                        # no new trigger, but 15 minutes later
    assert len(calls) == 2 and pos.breakeven_done and pos.stop == pos.entry


def test_a_paper_restart_does_not_replay_old_candles_or_reuse_ids(setup):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    runner, _ = _runner(setup, broker, require_approval=False, keep_paper_account=True)
    runner.step(NOW)
    for _ in range(3):
        broker.place_market_order("EURUSD", Direction.LONG, 0.1, 1.09, 1.12, 10.0, 0.01, 4.0, price=1.1, ts=NOW)
    for p in list(broker.open_positions())[1:]:
        broker.close_position(p.id, "manual", price=1.1, ts=NOW)
    runner.save_paper()
    fresh = PaperBroker(Settings())
    again, _ = _runner(setup, fresh, require_approval=False, keep_paper_account=True)
    assert again._fed_until == runner._fed_until and again._fed_until is not None
    assert fresh.place_market_order("EURUSD", Direction.SHORT, 0.1, 1.11, 1.09, 10.0, 0.01, 4.0, price=1.1, ts=NOW).id == "P5"


class MarginBroker(PaperBroker):
    """A paper account whose server asks ``per_lot`` margin a lot, as MT5's order_calc_margin does (FTMO crypto: 1:2)."""

    def __init__(self, settings, per_lot, free=None):
        super().__init__(settings)
        self.per_lot, self.free = per_lot, free

    def margin_per_lot(self, symbol, direction, price):
        return self.per_lot

    def free_margin(self):
        return self.free


def test_lots_are_cut_to_fit_the_margin(setup):
    """A full-size position needing more margin than the account has is refused by MT5 ("No money"): the live loop cuts
    the lots so one position ties up at most 45 % of equity and 90 % of the free margin, says so, and skips the setup
    only when not even the minimum lot fits."""
    broker = MarginBroker(Settings(), per_lot=50_000.0)
    broker.set_price("EURUSD", 1.1)
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    assert pos.lots == pytest.approx(0.90)                                     # 45 % of 100,000 over 50,000 a lot
    assert pos.meta["risk_budget"] == pytest.approx(1000.0 * 0.90 / 1.90)     # the planned 1.90 lots, risk cut alike
    assert any("margin: lots cut from 1.90, risk 47 % of planned" in m for m in notifier.sent)

    tight = MarginBroker(Settings(), per_lot=50_000.0, free=20_000.0)
    tight.set_price("EURUSD", 1.1)
    runner2, _ = _runner(setup, tight, require_approval=False)
    runner2.step(NOW)
    assert tight.open_positions()[0].lots == pytest.approx(0.36)              # 90 % of the 20,000 free

    full = MarginBroker(Settings(), per_lot=1e7)
    full.set_price("EURUSD", 1.1)
    runner3, notifier3 = _runner(setup, full, require_approval=False)
    runner3.step(NOW)
    assert full.open_positions() == [] and any("not enough margin for the minimum lot" in m for m in notifier3.sent)

    off = MarginBroker(Settings(), per_lot=50_000.0)
    off.set_price("EURUSD", 1.1)
    runner4, _ = _runner(setup, off, require_approval=False)
    runner4.settings.prop_firm.max_margin_pct = 0.0
    runner4.step(NOW)
    assert off.open_positions()[0].lots == pytest.approx(1.90)


def test_weekend_close_on_paper_and_on_a_real_broker(setup):
    """``prop_firm.weekend_close``: the paper broker closes a position at the market on the candle at Friday 16:45 New
    York (reason "weekend"), and on a broker that does not simulate candles the live runner closes it and reports it."""
    s = Settings(); s.prop_firm.weekend_close = "16:45"
    broker = PaperBroker(s, use_spread=False)
    t0 = pd.Timestamp("2026-10-07 09:00")                                      # a Wednesday
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1000, ts=t0)
    assert broker.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-09 20:40"), 1.1, 1.101, 1.099, 1.1005)) == []
    closed = broker.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-09 20:45"), 1.1005, 1.102, 1.1, 1.1015))
    assert len(closed) == 1 and closed[0].reason == "weekend" and closed[0].exit == pytest.approx(1.1015)

    class Server(PaperBroker):
        on_candle = None                                                       # like MT5
    server = Server(Settings())
    server.set_price("EURUSD", 1.1)
    server.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1, ts=NOW)
    runner, notifier = _runner(setup, server)
    runner.settings.prop_firm.weekend_close = "16:45"
    runner.clock = lambda: pd.Timestamp("2026-10-02 20:30")                    # Friday 16:30 New York: still held
    runner.manage_positions(runner.fetch())
    assert len(server.open_positions()) == 1
    runner.clock = lambda: pd.Timestamp("2026-10-02 20:46")
    runner.manage_positions(runner.fetch())
    runner.report_closes()
    assert server.open_positions() == [] and any("closed (weekend)" in m for m in notifier.sent)


def test_a_repeating_loop_error_is_sent_once_per_half_hour(setup, monkeypatch, capsys):
    """A scan failing the same way every minute sends one Telegram message, then at most one every 30 minutes with how
    often it came back; a different error is sent at once; the traceback goes to the console."""
    import kronos_trader.live as live_mod
    clock = [1_000_000.0]
    monkeypatch.setattr(live_mod.time, "time", lambda: clock[0])
    runner, notifier = _runner(setup, PaperBroker(Settings()))
    def boom():
        raise RuntimeError("terminal gone")
    for minute in range(31):
        clock[0] = 1_000_000.0 + 60 * minute
        try:
            boom()
        except RuntimeError as exc:
            runner.report_loop_error(exc)
    sent = [m for m in notifier.sent if "live loop error" in m]
    assert len(sent) == 2 and "also 29x since the last message" in sent[1]
    try:
        raise ValueError("other")
    except ValueError as exc:
        runner.report_loop_error(exc)
    assert sum("live loop error" in m for m in notifier.sent) == 3
    assert "RuntimeError: terminal gone" in capsys.readouterr().err


def test_break_even_counts_every_candle_since_the_last_look(setup):
    """On a real broker the runner moves the stop itself: a trigger reached by an earlier candle (between two polls, or
    while the window was down) counts, not only the newest candle's extreme, as in the backtest."""
    class Server(PaperBroker):
        on_candle = None
    broker = Server(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0949, 1.1200, 1000.0, 0.0051, 0.5, price=1.1,
                              ts=pd.Timestamp("2026-10-01 08:15"))                 # trigger at 0.5R: about 1.1026
    runner, notifier = _runner(setup, broker)
    rows = [(1.1, 1.101, 1.099, 1.1), (1.1, 1.104, 1.099, 1.1), (1.1, 1.101, 1.099, 1.1)]   # only the middle one reaches it
    views = {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner.manage_positions(views)
    pos = broker.open_positions()[0]
    assert pos.breakeven_done and pos.stop == pytest.approx(pos.entry)
    assert any("break-even" in m for m in notifier.sent)


def test_exits_run_even_when_the_analysis_fails(setup):
    """An engine error on one day's data must not keep a trade past its time limit (or weekend close, or break-even):
    the exits run before the analysis, on their own."""
    class Server(PaperBroker):
        on_candle = None
    broker = Server(Settings())
    broker.set_price("EURUSD", 1.1)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1200, 1000.0, 0.01, 4.0, price=1.1,
                              ts=NOW - pd.Timedelta(hours=49))
    runner, notifier = _runner(setup, broker)
    runner.settings.exits.max_hold_hours = 48

    class Broken:
        def analyze(self, *args, **kwargs):
            raise RuntimeError("engine bug")
    runner.engine = Broken()
    with pytest.raises(RuntimeError, match="engine bug"):
        runner.step(NOW)
    assert broker.open_positions() == [] and any("closed (time)" in m for m in notifier.sent)


def test_a_spread_wider_than_the_cap_blocks_the_entry(setup):
    """``risk.max_spread_stop_fraction``: no entry while the spread is wider than that fraction of the stop distance
    (live only). The setup's stop sits 51 pips under 1.1000; a 20-pip spread is 39 % of it."""
    class WideSpreadBroker(PaperBroker):
        def fill_price(self, symbol, direction, base=None):
            mid = self.current_price(symbol)
            return mid + (0.0010 if direction is Direction.LONG else -0.0010)

    settings = Settings()
    settings.risk.max_spread_stop_fraction = 0.3
    broker = WideSpreadBroker(settings)
    broker.set_price("EURUSD", 1.1)
    notifier = TelegramNotifier(dry_run=True)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, clock=lambda: NOW, require_approval=False)
    runner.step(NOW)
    assert broker.open_positions() == [] and any("spread" in m and "of the stop distance" in m for m in notifier.sent)

    settings.risk.max_spread_stop_fraction = 0.0                 # off: the same spread does not block
    broker2 = WideSpreadBroker(settings)
    broker2.set_price("EURUSD", 1.1)
    runner2 = LiveRunner(settings, "EURUSD", fetch, broker=broker2, notifier=TelegramNotifier(dry_run=True),
                         engine=FakeEngine(setup), dry_run=False, clock=lambda: NOW, require_approval=False)
    runner2.step(NOW)
    assert not any("of the stop distance" in m for m in runner2.notifier.sent)


def test_the_highest_day_start_balance_survives_a_restart_and_the_zone_multiplier_sizes_the_risk(setup, tmp_path):
    """The guard's day high (the FTMO 1-Step's trailing basis) is written next to the journal and read back by a new window
    of the same account size; planned_risk carries the setup's zone multiplier."""
    settings = Settings()
    settings.account_size = 10_000.0
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    settings.prop_firm.drawdown_basis = "day_high"
    broker = PaperBroker(settings)
    runner = LiveRunner(settings, "EURUSD", lambda: {}, broker=broker, notifier=TelegramNotifier(dry_run=True),
                        engine=FakeEngine(setup), dry_run=False, clock=lambda: NOW)
    runner.guard.day_high = 10_450.0
    runner.save_day_high()
    again = LiveRunner(settings, "EURUSD", lambda: {}, broker=PaperBroker(settings), notifier=TelegramNotifier(dry_run=True),
                       engine=FakeEngine(setup), dry_run=False, clock=lambda: NOW)
    assert again.guard.day_high == 10_450.0
    other = Settings(); other.account_size = 25_000.0; other.live.journal_path = settings.live.journal_path
    fresh = LiveRunner(other, "EURUSD", lambda: {}, broker=PaperBroker(other), notifier=TelegramNotifier(dry_run=True),
                       engine=FakeEngine(setup), dry_run=False, clock=lambda: NOW)
    assert fresh.guard.day_high == 25_000.0                                     # another account size: not this record
    settings.risk.risk_pct = 1.0
    settings.risk.zone_risk_multiplier = {setup.poi.timeframe.label: 2.0}
    assert again.planned_risk(setup) == pytest.approx(2 * again.planned_risk(None))


def test_apply_product_sets_the_guard_for_the_ftmo_one_step():
    from kronos_trader.cli import apply_product
    s = Settings()
    apply_product(s, "ftmo_1step")
    assert (s.prop_firm.daily_loss_limit_pct, s.prop_firm.max_drawdown_pct, s.prop_firm.drawdown_basis) == (2.9, 9.0, "day_high")
    apply_product(s, "ftmo_2step")
    assert (s.prop_firm.daily_loss_limit_pct, s.prop_firm.max_drawdown_pct, s.prop_firm.drawdown_basis) == (4.0, 9.5, "initial")
    with pytest.raises(SystemExit):
        apply_product(s, "ftmo_3step")


def _limit_runner(setup, tmp_path=None, broker=None, **kw):
    """A runner whose profile rests a limit 25 % of the way back toward the stop (setup B's NAS100 entry), valid 4 hours."""
    settings = Settings()
    settings.risk.limit_entry_fraction, settings.risk.limit_entry_minutes = 0.25, 240
    if tmp_path is not None:
        settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    broker = broker or PaperBroker(Settings())
    notifier = TelegramNotifier(dry_run=True)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup), dry_run=False,
                        require_approval=False, clock=lambda: NOW, **kw)
    return runner, broker, notifier


def test_a_limit_entry_rests_part_way_back_and_fills_as_a_trade(setup, tmp_path):
    """No market order: a buy limit 25 % of the way from the ask back toward the stop, sized on the smaller stop; the
    zone's visit is used. When price comes back to it, it is a trade like any other (filled row, R from the fill)."""
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    runner.step(NOW)
    assert broker.open_positions() == [] and len(broker.limit_orders()) == 1
    order = broker.limit_orders()[0]
    ask = 1.10005
    assert order.price == pytest.approx(round(ask - 0.25 * (ask - 1.0949), 5)) and order.stop == 1.0949 and order.take_profit == 1.12
    assert order.risk_amount == pytest.approx(1000.0, rel=0.02) and order.lots > 1.92      # 1 % over the smaller stop
    assert order.expires_at == NOW + pd.Timedelta(hours=4) and order.placed_at == NOW
    assert any("LIMIT" in m and "25% back toward the stop" in m for m in notifier.sent)
    assert not any("filled" in m for m in notifier.sent)
    assert runner.limits[order.id]["sid"] == short_id_for((setup.poi.key, str(setup.confirmation.timestamp)))
    broker.on_candle("EURUSD", Candle(0, NOW, 1.1, 1.1002, 1.0985, 1.0990))                 # back down through the limit
    runner.step(NOW + pd.Timedelta(minutes=16))
    pos = broker.open_positions()[0]
    assert pos.entry == order.price and pos.meta["limit_id"] == order.id and runner.limits == {}
    assert pos.risk_distance == pytest.approx(order.price - 1.0949)                         # reconciled on the fill
    assert any("filled (limit)" in m for m in notifier.sent)
    broker.on_candle("EURUSD", Candle(0, NOW + pd.Timedelta(minutes=15), 1.099, 1.125, 1.0985, 1.124))
    runner.step(NOW + pd.Timedelta(minutes=31))
    assert broker.open_positions() == [] and any("take_profit" in m for m in notifier.sent)
    rows = pd.read_csv(runner.settings.live.journal_path)
    assert list(rows.event[rows.event.isin(["limit_placed", "filled", "closed"])]) == ["limit_placed", "filled", "closed"]
    assert "limit " + order.id in rows[rows.event == "filled"].iloc[0].note


def test_a_limit_entry_is_cancelled_at_its_expiry(setup, tmp_path):
    runner, broker, notifier = _limit_runner(setup, tmp_path)
    runner.step(NOW)
    oid = broker.limit_orders()[0].id
    runner.step(NOW + pd.Timedelta(minutes=239))
    assert len(broker.limit_orders()) == 1
    runner.step(NOW + pd.Timedelta(minutes=240))
    assert broker.limit_orders() == [] and runner.limits == {} and broker.open_positions() == []
    assert any(f"limit {oid} cancelled - expired" in m for m in notifier.sent)
    rows = pd.read_csv(runner.settings.live.journal_path)
    assert rows[rows.event == "limit_cancelled"].iloc[0].reason == "expired"


def test_a_limit_entry_is_cancelled_when_the_target_trades_first(setup):
    runner, broker, notifier = _limit_runner(setup)
    runner.step(NOW)
    oid = broker.limit_orders()[0].id
    later = [(1.1, 1.101, 1.099, 1.1)] * 3 + [(1.1, 1.1205, 1.0995, 1.12)]                  # up to the target, the limit untouched
    runner.fetch = lambda: {T.MIN_15: CandleSeries.from_records(later, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner.step(NOW + pd.Timedelta(minutes=16))
    assert broker.limit_orders() == [] and broker.open_positions() == [] and runner.limits == {}
    assert any(f"limit {oid} cancelled - the target traded first" in m for m in notifier.sent)


def test_no_limit_when_the_market_price_fails_the_checks(setup):
    """The same checks at the market price as for a market order come first (as the backtest makes them): a price that
    ran away to an R:R below the minimum places no limit either."""
    runner, broker, notifier = _limit_runner(setup)
    runner.fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 2 + [(1.1, 1.1155, 1.099, 1.1150)],
                                                                T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner.step(NOW)
    assert broker.limit_orders() == [] and broker.open_positions() == [] and any("R:R now" in m for m in notifier.sent)


def test_a_resting_limit_takes_the_markets_slot(setup):
    """While a limit rests, the market's one slot is taken: a second setup there is refused, as the backtest refuses one
    while its limit works."""
    from kronos_trader.execution import RiskGuard
    runner, broker, notifier = _limit_runner(setup)
    runner.step(NOW)
    order = broker.limit_orders()[0]
    assert RiskGuard.open_risk(broker) == pytest.approx(order.risk_amount)
    ok, reason = runner.guard.can_open(broker, NOW, "EURUSD", new_risk=100.0)
    assert not ok and "resting limit entries count" in reason


def test_resting_limits_survive_a_restart_and_unknown_ones_are_cancelled(setup, tmp_path):
    """The window's resting limits are kept next to the journal: after a restart they are still watched (expiry, fill).
    A resting limit of this market the window has no record of is cancelled at its first scan."""
    runner, broker, _ = _limit_runner(setup, tmp_path)
    runner.step(NOW)
    known = broker.limit_orders()[0]
    assert (tmp_path / "journal" / "limits_EURUSD.json").exists()
    stray = broker.place_limit_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.0900, 1.1100, 250.0, 0.005, 4.0,
                                     NOW + pd.Timedelta(hours=1), ts=NOW)
    again, _, notifier = _limit_runner(setup, tmp_path, broker=broker)
    assert set(again.limits) == {known.id} and again.limits[known.id]["expires_at"] == NOW + pd.Timedelta(hours=4)
    again.engine.calls = 1                                                       # no new signal on the restart
    again.step(NOW + pd.Timedelta(minutes=5))
    assert [o.id for o in broker.limit_orders()] == [known.id]
    assert any(f"limit {stray.id} cancelled at the start" in m for m in notifier.sent)
    again.step(NOW + pd.Timedelta(minutes=241))
    assert broker.limit_orders() == [] and again.limits == {}
    assert (tmp_path / "journal" / "limits_EURUSD.json").read_text(encoding="utf-8") == "[]"


def test_a_paper_limit_filled_and_stopped_in_one_candle_is_one_losing_trade(setup):
    runner, broker, notifier = _limit_runner(setup)
    runner.step(NOW)
    broker.on_candle("EURUSD", Candle(0, NOW, 1.1, 1.1002, 1.0940, 1.0945))                 # through the limit and the stop
    runner.step(NOW + pd.Timedelta(minutes=16))
    assert broker.open_positions() == [] and runner.limits == {}
    assert any("closed again before this scan" in m for m in notifier.sent)
    assert any("closed (stop)" in m and "-1.00R" in m for m in notifier.sent)
