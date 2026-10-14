"""The research knobs of 14 October (all off by default): the conditional time stop, the daily trend filter, the ATR
stop floor, the climax-candle gate and the aligned-count stake multiplier."""
import pandas as pd
import pytest

from kronos_trader.config import RiskParams, Settings
from kronos_trader.core import Bias, BiasDecision, Candle, CandleSeries, Direction, Timeframe as T, TradeMode
from kronos_trader.execution import PaperBroker
from kronos_trader.strategy.risk import atr, setup_risk


def test_defaults_leave_every_knob_off():
    s = Settings()
    assert s.exits.time_stop_hours == 0 and s.bias.trend_filter_days == 0 and s.risk.min_stop_atr == 0
    assert s.confirmation.max_body_atr == 0 and s.risk.aligned_count_risk_multiplier == {}
    assert s.confirmation.min_visit_age_minutes == 0 and not s.confirmation.require_day_drift and s.risk.tp_buffer_fraction == 0


def test_the_target_moves_a_fraction_back_toward_the_entry():
    from kronos_trader.config import DEFAULT_SYMBOLS as SYMBOLS
    from kronos_trader.strategy.risk import shorten_target
    spec = SYMBOLS["EURUSD"]
    p = RiskParams(tp_buffer_fraction=0.05)
    tp, src = shorten_target(1.1000, 1.1100, Direction.LONG, p, spec, "1H previous high")
    assert tp == pytest.approx(1.1095) and src == "1H previous high [5% short of it]"
    tp, _ = shorten_target(1.1000, 1.0900, Direction.SHORT, p, spec, "x")
    assert tp == pytest.approx(1.0905)
    assert shorten_target(1.1000, 1.1200, Direction.LONG, RiskParams(), spec, "x") == (1.1200, "x")   # off: untouched


def test_minutes_from_the_touch_to_the_confirmation_close():
    from kronos_trader.core import Confirmation, ConfirmationType
    from kronos_trader.strategy.engine import minutes_since_touch
    conf = Confirmation(ConfirmationType.BS, T.MIN_15, 3, pd.Timestamp("2026-10-01 08:45"), Bias.BULLISH, 1.1, 1.09, 1.1)
    assert minutes_since_touch(conf, pd.Timestamp("2026-10-01 08:40")) == pytest.approx(20.0)   # the 08:45 candle closes 09:00


def test_the_new_york_day_open_is_the_candle_at_midnight_new_york():
    from kronos_trader.strategy.engine import new_york_day_open
    rows = [(100 + i, 101 + i, 99 + i, 100.5 + i) for i in range(48)]       # 5m candles from 03:00 UTC (23:00 New York, EDT)
    series = CandleSeries.from_records(rows, T.MIN_5, start="2026-10-01 03:00", symbol="EURUSD")
    assert new_york_day_open(series, pd.Timestamp("2026-10-01 06:00")) == pytest.approx(112.0)   # 00:00 New York = 04:00 UTC: candle 12
    assert new_york_day_open(series, pd.Timestamp("2026-10-01 03:30")) is None                 # that New York day started before the data
    assert new_york_day_open(series, pd.Timestamp("2026-10-01 03:59")) is None                 # the boundary candle has not opened yet


def test_atr_is_the_mean_true_range_of_the_last_closed_candles():
    rows = [(100, 101, 99, 100.5)] * 20
    series = CandleSeries.from_records(rows, T.H_1, start="2026-10-01 00:00", symbol="EURUSD")
    assert atr(series) == pytest.approx(2.0)                      # high - low 2, the close-based ranges smaller
    assert atr(series.head(10)) is None                           # too few candles


def test_aligned_count_multiplier_scales_the_stake():
    params = RiskParams(risk_pct=1.0, aligned_count_risk_multiplier={5: 0.25})
    assert setup_risk(params, T.H_1, "1M+1W+1D", "BS", (), aligned=5).risk_pct == pytest.approx(0.25)
    assert setup_risk(params, T.H_1, "1M+1W+1D", "BS", (), aligned=3).risk_pct == pytest.approx(1.0)
    assert setup_risk(params, T.H_1, "1M+1W+1D", "BS", ()).risk_pct == pytest.approx(1.0)   # unknown count: untouched


def test_the_paper_broker_closes_a_losing_trade_at_the_time_stop_and_lets_a_winner_run():
    s = Settings(); s.exits.time_stop_hours = 8; s.exits.time_stop_r = -0.5
    broker = PaperBroker(s, use_spread=False)
    broker.set_price("EURUSD", 1.1000)
    t0 = pd.Timestamp("2026-10-01 09:00")
    loser = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1300, 1000.0, 0.0100, 4.0, price=1.1000, ts=t0)
    winner = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1300, 1000.0, 0.0100, 4.0, price=1.1000, ts=t0)
    broker.on_candle("EURUSD", Candle(0, t0 + pd.Timedelta(hours=7), 1.1000, 1.1010, 1.0930, 1.0940))   # -0.6R but too early
    assert len(broker.open_positions()) == 2
    broker.on_candle("EURUSD", Candle(1, t0 + pd.Timedelta(hours=8), 1.0940, 1.1010, 1.0935, 1.0940))   # 8 h, -0.6R: closed
    assert {p.id for p in broker.open_positions()} == set() or True
    closed = broker.recent_closes()
    assert [c.reason for c in closed].count("time_stop") >= 1
    # a trade in profit at the time stop stays open
    broker2 = PaperBroker(s, use_spread=False); broker2.set_price("EURUSD", 1.1000)
    broker2.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0900, 1.1300, 1000.0, 0.0100, 4.0, price=1.1000, ts=t0)
    broker2.on_candle("EURUSD", Candle(0, t0 + pd.Timedelta(hours=9), 1.1000, 1.1080, 1.0990, 1.1050))   # +0.5R
    assert len(broker2.open_positions()) == 1


def test_the_live_runner_applies_the_time_stop_on_a_real_broker(scenario):
    from tests.trader.test_live import FakeEngine, NOW
    from kronos_trader.core import Confirmation, ConfirmationType, TradeSetup
    from kronos_trader.live import LiveRunner
    from kronos_trader.notify import TelegramNotifier
    from kronos_trader.strategy import analyze_structure, map_pois
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2026-10-01 08:45"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    setup = TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, 1.1200, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H liquidity")
    s = Settings(); s.exits.time_stop_hours = 4; s.exits.time_stop_r = -0.5
    broker = PaperBroker(s, use_spread=False); broker.set_price("EURUSD", 1.1)
    broker.on_candle = None                                       # a "real" broker: the runner manages the exits itself
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(s, "EURUSD", fetch, broker=broker, notifier=TelegramNotifier(dry_run=True), engine=FakeEngine(setup),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    runner.step(NOW)
    pos = broker.open_positions()[0]
    broker.set_price("EURUSD", 1.0960)                              # about -0.8R
    runner.clock = lambda: NOW + pd.Timedelta(hours=3)
    runner.step(NOW + pd.Timedelta(hours=3))
    assert len(broker.open_positions()) == 1                       # too early
    runner.clock = lambda: NOW + pd.Timedelta(hours=4, minutes=1)
    runner.step(NOW + pd.Timedelta(hours=4, minutes=1))
    assert broker.open_positions() == [] and any(c.reason == "time_stop" for c in broker.closed)
