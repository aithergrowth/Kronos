from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.backtest.runner import Backtester
from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Direction, Timeframe
from kronos_trader.data import MultiTimeframeData


class OnceEngine:
    """One deterministic signal isolates runner boundaries from strategy selection."""

    def __init__(self, direction):
        self.direction = direction
        self.calls = 0

    def analyze(self, symbol, views, equity, now):
        self.calls += 1
        if self.calls > 1:
            return SimpleNamespace(rejections=[], has_valid_signal=False)
        stop, target = (1.0, 2.0) if self.direction is Direction.LONG else (1.2, 0.5)
        setup = SimpleNamespace(
            poi=SimpleNamespace(key=("test",), timeframe=Timeframe.H_1, low=1.0, high=1.11),
            confirmation=SimpleNamespace(timestamp=pd.Timestamp("2026-01-02 09:00"),
                                         type=SimpleNamespace(value="test"), timeframe=Timeframe.H_1),
            direction=self.direction, lots=0.1, stop=stop, take_profit=target,
            risk_amount=1000.0, risk_distance=abs(1.1 - stop), breakeven_r=4.0,
            rr=3.0, tp_source="test", entry=1.1,
        )
        return SimpleNamespace(rejections=[], has_valid_signal=True,
                               signal=SimpleNamespace(setup=setup, forecast=None))


@pytest.mark.parametrize("direction", [Direction.LONG, Direction.SHORT])
def test_end_bounded_run_matches_physically_truncated_data(direction):
    # The future candle is deliberately far from the last in-range mark.
    candles = CandleSeries.from_records(
        [(1.1, 1.101, 1.099, 1.1), (1.1, 1.102, 1.1, 1.101), (1.101, 1.31, 1.10, 1.3)],
        Timeframe.H_1, start="2026-01-02 09:00", symbol="EURUSD",
    )

    def run(series, end=None):
        return Backtester(Settings(), MultiTimeframeData({Timeframe.H_1: series}), "EURUSD",
                          engine=OnceEngine(direction), end=end, use_spread=False).run()

    bounded = run(candles, end=pd.Timestamp("2026-01-02 10:00"))
    truncated = run(candles.head(2))

    assert bounded.steps == truncated.steps == 2
    pd.testing.assert_frame_equal(bounded.trades_frame(), truncated.trades_frame())
    assert bounded.final_equity == pytest.approx(truncated.final_equity)
    assert bounded.trades[0].exit == pytest.approx(1.101)
    assert bounded.trades[0].closed_at == pd.Timestamp("2026-01-02 11:00")
    assert bounded.trades[0].reason == "end_of_data"
