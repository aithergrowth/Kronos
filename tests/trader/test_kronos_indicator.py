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
        self.timestamps = []

    def predict(self, df, x_timestamp, y_timestamp, pred_len, **kwargs):
        self.calls.append((len(df), list(df.columns), len(y_timestamp), pred_len, kwargs))
        self.timestamps.append((x_timestamp.copy(), y_timestamp.copy()))
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


@pytest.mark.parametrize("symbol,timeframe,start,n,first_prediction", [
    ("BTCUSD", Timeframe.H_1, "2024-01-04", 48, "2024-01-06 00:00"),
    ("BTCUSDT", Timeframe.H_1, "2024-01-04", 48, "2024-01-06 00:00"),
    ("BTCUSD", Timeframe.D_1, "2023-12-02", 35, "2024-01-06 00:00"),
    ("EURUSD", Timeframe.H_1, "2024-01-04", 48, "2024-01-08 00:00"),
])
def test_forecast_calendar_keeps_configured_weekend_candles(symbol, timeframe, start, n, first_prediction):
    series = CandleSeries.from_records([(100, 101, 99, 100)] * n, timeframe, start=start, symbol=symbol)
    fake = FakePredictor(0.01)
    fc = KronosForecaster(KronosParams(horizon=3, n_paths=1), predictor=fake)
    fc.forecast(series)
    assert fake.timestamps[0][1].iloc[0] == pd.Timestamp(first_prediction)


def test_forecast_calendar_preserves_default_tradingview_cache_weekends(tmp_path):
    from kronos_trader.config import Settings
    from kronos_trader.data.tv_cache import load_series, save_series
    settings = Settings()
    feed_symbol = settings.symbol("BTCUSD").tradingview_symbol
    assert feed_symbol == "BINANCE:BTCUSDT"
    series = CandleSeries.from_records([(100, 101, 99, 100)] * 48, Timeframe.H_1,
                                       start="2024-01-04", symbol=feed_symbol)
    save_series(series, tmp_path)
    cached = load_series(tmp_path, feed_symbol, Timeframe.H_1)
    assert cached.symbol == feed_symbol
    fake = FakePredictor(0.01)
    KronosForecaster(settings.kronos, predictor=fake).forecast(cached, horizon=3, n_paths=1)
    assert fake.timestamps[0][1].iloc[0] == pd.Timestamp("2024-01-06 00:00")


def test_forecast_calendar_uses_explicit_symbol_alias_configuration():
    params = KronosParams(horizon=3, n_paths=1, weekend_symbols=("BTCUSD.r",))
    fake = FakePredictor(0.01)
    fc = KronosForecaster(params, predictor=fake)
    for symbol, first in [("BTCUSD.r", "2024-01-06"), ("BTCUSD", "2024-01-08")]:
        series = CandleSeries.from_records([(100, 101, 99, 100)] * 48, Timeframe.H_1,
                                           start="2024-01-04", symbol=symbol)
        fc.forecast(series)
        assert fake.timestamps[-1][1].iloc[0] == pd.Timestamp(first)


def test_engine_forecast_receives_only_candles_closed_at_analysis_time():
    from kronos_trader.config import Settings
    from kronos_trader.strategy import StrategyEngine
    settings = Settings()
    settings.kronos.mode = "advisory"
    settings.kronos.forecast_timeframes = (Timeframe.H_1,)
    settings.kronos.n_paths = 1
    fake = FakePredictor(0.01)
    fc = KronosForecaster(settings.kronos, predictor=fake)
    now = pd.Timestamp("2024-01-03 12:00")
    StrategyEngine(settings, fc).analyze("EURUSD", {Timeframe.H_1: _series(100)},
                                          now=now, compute_forecasts=True)
    x_ts, y_ts = fake.timestamps[0]
    assert len(x_ts) == 60
    assert x_ts.iloc[-1] == now - pd.Timedelta(hours=1)
    assert y_ts.iloc[0] == now


@pytest.mark.parametrize("mode,result,confidence,expected_status", [
    ("off", "error", .9, "valid"),
    ("advisory", "error", .9, "valid"),
    ("advisory", "opposing", .9, "valid"),
    ("filter", "error", .9, "rejected"),
    ("filter", "absent", .9, "rejected"),
    ("filter", "opposing", .9, "rejected"),
    ("filter", "opposing", .5, "valid"),
])
def test_engine_forecast_filter_requires_available_forecast(monkeypatch, mode, result, confidence, expected_status):
    """Isolate forecast routing after a valid setup; no broker, notifier or real model."""
    from kronos_trader.config import Settings
    from kronos_trader.core.types import (BiasDecision, Confirmation, ConfirmationType, Direction,
                                          ForecastSummary, POI, POIStatus, TradeMode, TradeSetup)
    from kronos_trader.strategy import StrategyEngine
    import kronos_trader.strategy.engine as engine_module

    settings = Settings()
    settings.session.enabled = False
    settings.kronos.mode = mode
    decision = BiasDecision(Bias.BULLISH, TradeMode.FULL, (), (), (), (), "synthetic forecast routing")
    poi = POI(Timeframe.H_1, Bias.BULLISH, 98., 102., None, None, 0,
              pd.Timestamp("2024-01-01"), status=POIStatus.ACTIVE)
    conf = Confirmation(ConfirmationType.BS, Timeframe.MIN_15, 99, pd.Timestamp("2024-01-02 00:45"),
                        Bias.BULLISH, 99., 98., 100.)
    setup = TradeSetup("EURUSD", Direction.LONG, poi, conf, 100., 98., 106., 2., 6., 3.,
                       1., 1000., 4., "synthetic")

    class Forecaster:
        calls = 0

        def forecast(self, series):
            self.calls += 1
            if result == "error":
                raise RuntimeError("synthetic model unavailable")
            return ForecastSummary(Timeframe.MIN_15, 12, Bias.BEARISH, confidence, 100., 98.,
                                   101., 97., -2., 5, "fake")

    forecaster = None if result == "absent" else Forecaster()
    monkeypatch.setattr(engine_module, "combine_biases", lambda *args: decision)
    monkeypatch.setattr(engine_module, "map_pois", lambda st, *args: [poi] if st.series.timeframe is Timeframe.H_1 else [])
    monkeypatch.setattr(engine_module, "current_visit", lambda *args: (0, 1, False))
    monkeypatch.setattr(engine_module, "find_confirmation", lambda *args, **kwargs: conf)
    monkeypatch.setattr(engine_module, "build_setup", lambda *args, **kwargs: (setup, []))
    views = {Timeframe.H_1: _series(), Timeframe.MIN_15: CandleSeries.from_records(
        [(100, 101, 99, 100)] * 100, Timeframe.MIN_15, start="2024-01-01", symbol="EURUSD")}
    analysis = StrategyEngine(settings, forecaster).analyze("EURUSD", views, now=pd.Timestamp("2024-01-06"))
    assert analysis.signal.status.value == expected_status
    if forecaster is not None:
        assert forecaster.calls == (0 if mode == "off" else 1)
    if result in ("error", "absent"):
        assert analysis.signal.forecast is None
    if mode == "advisory" and result == "error":
        assert any("forecast failed" in note for note in setup.notes)
    if mode == "filter" and result in ("error", "absent"):
        assert not analysis.has_valid_signal
        assert any("unavailable" in reason for reason in analysis.rejections)


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


def test_forecast_paths_keep_requested_calendar_when_predictor_returns_range_index():
    class RangeIndexPredictor(FakePredictor):
        def predict(self, *args, **kwargs):
            return super().predict(*args, **kwargs).reset_index(drop=True)

    series = CandleSeries.from_records([(100, 101, 99, 100)] * 48, Timeframe.H_1,
                                       start="2024-01-04", symbol="BTCUSD")
    summary = KronosForecaster(KronosParams(horizon=3, n_paths=1),
                              predictor=RangeIndexPredictor(0.01)).forecast(series)
    assert list(summary.paths_ohlc[0].index) == list(pd.date_range("2024-01-06", periods=3, freq="h"))
