import os

import pandas as pd
import pytest

from kronos_trader.config import KronosParams
from kronos_trader.core import Bias, CandleSeries, Timeframe
from kronos_trader.indicators import KronosForecaster


class FakePredictor:
    """Stands in for KronosPredictor: drifts the close by a fixed % per candle."""

    def __init__(self, drift: float):
        self.drift = drift
        self.calls = []

    def predict(self, df, x_timestamp, y_timestamp, pred_len, **kwargs):
        self.calls.append((len(df), list(df.columns), len(y_timestamp), pred_len, kwargs))
        last = float(df["close"].iloc[-1])
        closes = [last * (1 + self.drift) ** (i + 1) for i in range(pred_len)]
        return pd.DataFrame({"open": closes, "high": [c * 1.001 for c in closes], "low": [c * 0.999 for c in closes],
                             "close": closes, "volume": 0.0, "amount": 0.0}, index=y_timestamp)


def _series(n=100):
    return CandleSeries.from_records([(100, 101, 99, 100)] * n, Timeframe.H_1, start="2024-01-01", symbol="EURUSD")


@pytest.mark.parametrize("drift,expected", [(0.01, Bias.BULLISH), (-0.01, Bias.BEARISH), (0.0001, Bias.NEUTRAL)])
def test_forecast_direction_and_confidence(drift, expected):
    fake = FakePredictor(drift)
    fc = KronosForecaster(KronosParams(horizon=5, n_paths=3, neutral_band_pct=0.1), predictor=fake)
    summary = fc.forecast(_series())
    assert summary.direction is expected
    assert summary.paths == 3 and summary.horizon == 5
    assert summary.confidence == pytest.approx(1.0) or expected is Bias.NEUTRAL
    n, cols, ny, pred_len, kwargs = fake.calls[0]
    assert n == 100 and "amount" in cols and ny == 5 and pred_len == 5 and kwargs["sample_count"] == 1
    assert summary.expected_high > summary.expected_low
    assert fc.mean_path().shape == (5, 4)


def test_forecast_uses_at_most_max_context():
    fake = FakePredictor(0.01)
    fc = KronosForecaster(KronosParams(horizon=3, n_paths=1, lookback=400, max_context=64), predictor=fake)
    fc.forecast(_series(500))
    assert fake.calls[0][0] == 64


def test_forecast_needs_enough_history():
    fc = KronosForecaster(KronosParams(), predictor=FakePredictor(0.0))
    with pytest.raises(ValueError):
        fc.forecast(_series(10))


@pytest.mark.slow
def test_real_kronos_small_forecast():
    if not os.environ.get("KRONOS_TRADER_REAL_MODEL"):
        pytest.skip("set KRONOS_TRADER_REAL_MODEL=1 to download Kronos-small and run this")
    from pathlib import Path
    csv = Path(__file__).resolve().parents[1] / "data" / "regression_input.csv"
    series = CandleSeries.from_csv(csv, Timeframe.MIN_5, symbol="600977")
    fc = KronosForecaster(KronosParams(horizon=8, n_paths=2, device="cpu"))
    summary = fc.forecast(series)
    assert summary.direction in (Bias.BULLISH, Bias.BEARISH, Bias.NEUTRAL)
    assert summary.expected_low < summary.expected_high
