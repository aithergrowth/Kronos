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

    def __init__(self, setup):
        self.setup = setup
        self.calls = 0

    def analyze(self, symbol, views, equity=None, now=None, max_confirmation_age=0, compute_forecasts=False):
        self.calls += 1
        decision = BiasDecision(Bias.BULLISH, TradeMode.FULL, (T.MN_1, T.W_1, T.D_1), (), (T.H_4, T.H_1), (T.MN_1, T.W_1, T.D_1), "test")
        signal = Signal(now, SignalStatus.VALID, self.setup, None, []) if self.calls == 1 else None
        return Analysis(symbol, now, 1.1000, {}, decision, [], signal)


@pytest.fixture
def setup(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2026-10-01 08:45"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    return TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, 1.1200, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H liquidity")


def _runner(setup, broker, **kw):
    notifier = TelegramNotifier(dry_run=True)
    fetch = lambda: {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
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
    assert pos.lots == 1.92 and pos.stop == 1.0949 and pos.take_profit == 1.12
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
    broker.set_price("EURUSD", 1.1150)                     # price ran away: R:R now far below 1:3
    runner, notifier = _runner(setup, broker, require_approval=False)
    runner.step(NOW)
    assert broker.open_positions() == [] and any("R:R now" in m for m in notifier.sent)

    broker2 = PaperBroker(Settings())
    broker2.set_price("EURUSD", 1.1)
    broker2.place_market_order("EURUSD", Direction.SHORT, 0.1, 1.11, 1.09, 100.0, 0.0101, 4.0, price=1.1, ts=NOW)
    runner2, notifier2 = _runner(setup, broker2, require_approval=False)
    runner2.step(NOW)
    assert len(broker2.open_positions()) == 1 and any("NOT executable" in m for m in notifier2.sent)


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
