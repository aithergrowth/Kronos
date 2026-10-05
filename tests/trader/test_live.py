"""Live loop: approve / skip / expire flow, execution through the paper broker, close reports, composite fetch."""
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
