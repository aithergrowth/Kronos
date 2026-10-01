"""Kronos as an indicator.

Wraps ``KronosPredictor`` from this repository so the strategy can ask
"where does the foundation model think the next N candles go?" and get back a
direction, a confidence and an expected range.  The model is loaded lazily,
runs on CPU when no GPU is present and can be swapped for any object with a
compatible ``predict`` method (used by the tests).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

from ..config import KronosParams
from ..core.candles import CandleSeries
from ..core.types import Bias, ForecastSummary

REPO_ROOT = Path(__file__).resolve().parents[2]


def _import_kronos():
    try:
        from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: WPS433
    except ModuleNotFoundError:
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from model import Kronos, KronosPredictor, KronosTokenizer  # noqa: WPS433
    return Kronos, KronosPredictor, KronosTokenizer


class KronosForecaster:
    def __init__(self, params: Optional[KronosParams] = None, predictor=None):
        self.params = params or KronosParams()
        self._predictor = predictor
        self.last_paths: List[pd.DataFrame] = []

    # ------------------------------------------------------------------ model
    @property
    def predictor(self):
        if self._predictor is None:
            self._predictor = self.load_predictor(self.params)
        return self._predictor

    @staticmethod
    def load_predictor(params: KronosParams):
        Kronos, KronosPredictor, KronosTokenizer = _import_kronos()
        tokenizer = KronosTokenizer.from_pretrained(params.tokenizer)
        model = Kronos.from_pretrained(params.model)
        tokenizer.eval()
        model.eval()
        return KronosPredictor(model, tokenizer, device=params.device, max_context=params.max_context)

    @property
    def is_loaded(self) -> bool:
        return self._predictor is not None

    # ------------------------------------------------------------------ forecast
    def forecast(self, series: CandleSeries, horizon: Optional[int] = None, n_paths: Optional[int] = None) -> ForecastSummary:
        p = self.params
        horizon = horizon or p.horizon
        n_paths = n_paths or p.n_paths
        context = series.tail(min(p.lookback, p.max_context))
        if len(context) < 32:
            raise ValueError(f"need at least 32 candles for a Kronos forecast, got {len(context)}")
        x_df, x_ts = context.to_kronos_inputs()
        # Explicit instrument configuration: broker/feed aliases must be listed;
        # do not infer exchange hours or holidays from arbitrary symbol names.
        weekend_symbols = {symbol.upper() for symbol in p.weekend_symbols}
        skip_weekends = (series.symbol or "").upper() not in weekend_symbols
        y_ts = series.timeframe.future_timestamps(context.last_timestamp, horizon, skip_weekends=skip_weekends)
        last_close = float(context.last.close)

        paths: List[pd.DataFrame] = []
        for _ in range(n_paths):
            pred = self.predictor.predict(
                df=x_df,
                x_timestamp=x_ts,
                y_timestamp=y_ts,
                pred_len=horizon,
                T=p.temperature,
                top_k=p.top_k,
                top_p=p.top_p,
                sample_count=1,
                verbose=False,
            )
            paths.append(pred)
        self.last_paths = paths

        final_closes = np.array([float(path["close"].iloc[-1]) for path in paths])
        expected_close = float(final_closes.mean())
        expected_high = float(np.mean([float(path["high"].max()) for path in paths]))
        expected_low = float(np.mean([float(path["low"].min()) for path in paths]))
        pct_change = (expected_close - last_close) / last_close * 100.0
        bull_share = float(np.mean(final_closes > last_close))

        if abs(pct_change) < p.neutral_band_pct:
            direction = Bias.NEUTRAL
            confidence = 1.0 - abs(bull_share - 0.5) * 2.0
        elif pct_change > 0:
            direction = Bias.BULLISH
            confidence = bull_share
        else:
            direction = Bias.BEARISH
            confidence = 1.0 - bull_share

        return ForecastSummary(
            timeframe=series.timeframe,
            horizon=horizon,
            direction=direction,
            confidence=confidence,
            last_close=last_close,
            expected_close=expected_close,
            expected_high=expected_high,
            expected_low=expected_low,
            pct_change=pct_change,
            paths=n_paths,
            model=p.model,
        )

    def mean_path(self) -> Optional[pd.DataFrame]:
        """Average of the last sampled paths (OHLC), for plotting / Telegram."""
        if not self.last_paths:
            return None
        stacked = np.stack([path[["open", "high", "low", "close"]].to_numpy() for path in self.last_paths])
        return pd.DataFrame(stacked.mean(axis=0), columns=["open", "high", "low", "close"], index=self.last_paths[0].index)
