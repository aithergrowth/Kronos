from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.backtest.runner import Backtester
from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Direction, Timeframe
from kronos_trader.data import MultiTimeframeData


class StaleSignalEngine:
    def __init__(self, direction, entry, stop, target):
        self.setup = SimpleNamespace(
            poi=SimpleNamespace(key=("test",), timeframe=Timeframe.H_4, low=1.0, high=1.2),
            confirmation=SimpleNamespace(timestamp=pd.Timestamp("2026-01-02 10:00"),
                                         type=SimpleNamespace(value="first_candle"), timeframe=Timeframe.H_1),
            direction=direction, entry=entry, stop=stop, take_profit=target,
            lots=0.1, risk_amount=1000.0, risk_distance=abs(entry - stop),
            breakeven_r=4.0, rr=4.0, tp_source="test",
        )

    def analyze(self, symbol, views, equity, now):
        return SimpleNamespace(rejections=[], has_valid_signal=True,
                               signal=SimpleNamespace(setup=self.setup, forecast=None))


def run_signal(engine, current_price, settings=None, use_spread=True):
    candles = CandleSeries.from_records(
        [(current_price, current_price, current_price, current_price)],
        Timeframe.MIN_15, start="2026-01-02 11:00", symbol="EURUSD",
    )
    return Backtester(settings or Settings(), MultiTimeframeData({Timeframe.MIN_15: candles}), "EURUSD",
                      engine=engine, use_spread=use_spread).run()


@pytest.mark.parametrize("direction,old_entry,stop,target,fill", [
    (Direction.LONG, 1.15, 1.09, 1.16, 1.10005),
    (Direction.SHORT, 1.05, 1.11, 1.04, 1.09995),
])
def test_stale_confirmation_is_filled_and_sized_at_current_executable_price(direction, old_entry, stop, target, fill):
    engine = StaleSignalEngine(direction, old_entry, stop, target)
    result = run_signal(engine, current_price=1.1)
    trade, = result.trades

    assert trade.opened_at == pd.Timestamp("2026-01-02 11:15")
    assert trade.entry == pytest.approx(fill)
    assert trade.lots == 0.98  # 1% of 100k, 101.5 pips including the configured sizing buffer
    assert trade.risk_amount == 1000
    assert trade.meta["planned_rr"] == 5.91
    assert trade.meta["signal_entry"] == old_entry
    assert engine.setup.entry == old_entry  # the strategy signal itself is not rewritten
    assert engine.setup.lots == 0.1


@pytest.mark.parametrize("direction,current,stop,target,reason", [
    (Direction.LONG, 1.09, 1.09, 1.16, "stop already crossed"),
    (Direction.SHORT, 1.11, 1.11, 1.04, "stop already crossed"),
    (Direction.LONG, 1.16, 1.09, 1.16, "target already crossed"),
    (Direction.SHORT, 1.04, 1.11, 1.04, "target already crossed"),
    (Direction.LONG, 1.11, 1.09, 1.14, "R:R below minimum at current price"),
    (Direction.SHORT, 1.09, 1.11, 1.06, "R:R below minimum at current price"),
])
def test_repricing_rejects_crossed_levels_or_insufficient_rr(direction, current, stop, target, reason):
    result = run_signal(StaleSignalEngine(direction, 1.1, stop, target), current, use_spread=False)
    assert result.trades == []
    assert result.signals == 1
    assert result.rejection_reasons[f"execution - {reason}"] == 1


def test_spread_can_make_an_otherwise_valid_current_rr_untradeable():
    settings = Settings()
    settings.risk.spread_buffer_pips = 0
    # Midpoint R:R is exactly 3; the executable ask entry makes it smaller.
    engine = StaleSignalEngine(Direction.LONG, 1.125, 1.0, 1.5)
    with_spread = run_signal(engine, 1.125, settings)
    without_spread = run_signal(engine, 1.125, settings, use_spread=False)
    assert with_spread.trades == []
    assert with_spread.rejection_reasons["execution - R:R below minimum at current price"] == 1
    assert len(without_spread.trades) == 1


def test_repricing_rejects_size_below_broker_minimum():
    settings = Settings()
    settings.account_size = 100
    result = run_signal(StaleSignalEngine(Direction.LONG, 1.1, 0.5, 4.0), 1.1, settings)
    assert result.trades == []
    assert result.rejection_reasons["execution - position below minimum lot at current price"] == 1
