"""Lower-timeframe confirmation.

Rule table: Monthly POI -> min. 4H, Weekly -> 1H, Daily -> 15m, 4H -> 5m, 1H -> 1m.
Confirmation = BOS, BMS (body close past the structural high/low - wicks do not
count) or, when enabled, the first bullish/bearish candle after the touch.
"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from ..config import ConfirmationParams, StructureParams
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Bias, BreakKind, Confirmation, ConfirmationType, POI
from .structure import analyze_structure


def allowed_confirmation_timeframes(poi_tf: Timeframe, params: Optional[ConfirmationParams] = None) -> List[Timeframe]:
    """Timeframes on which a confirmation for a ``poi_tf`` POI may be taken (smallest first)."""
    params = params or ConfirmationParams()
    min_tf = params.min_confirmation_tf[poi_tf]
    return sorted(tf for tf in Timeframe if min_tf <= tf < poi_tf)


def find_confirmation(
    ltf: CandleSeries,
    poi: POI,
    touch_ts: pd.Timestamp,
    params: Optional[ConfirmationParams] = None,
    structure_params: Optional[StructureParams] = None,
    max_age: int = 0,
    structure=None,
) -> Optional[Confirmation]:
    """Earliest still-actionable confirmation on ``ltf`` after price touched the POI at ``touch_ts``.

    ``max_age`` limits how many candles ago the confirmation may have closed
    (0 = it must be the last closed candle, so the signal is actionable now).
    ``structure`` may carry a precomputed ``StructureAnalysis`` of ``ltf``.
    """
    params = params or ConfirmationParams()
    structure_params = structure_params or StructureParams()
    n = len(ltf)
    if n == 0:
        return None
    touch_index = ltf.index_at_or_after(touch_ts)
    if touch_index >= n:
        return None
    ext = poi.height * params.max_extension_zones
    st = structure if structure is not None else analyze_structure(ltf, structure_params)

    candidates: List[Confirmation] = []
    for brk in st.breaks:
        if brk.index < touch_index or brk.direction is not poi.direction:
            continue
        if poi.direction is Bias.BULLISH and brk.close > poi.high + ext:
            continue
        if poi.direction is Bias.BEARISH and brk.close < poi.low - ext:
            continue
        ctype = ConfirmationType.BOS if brk.kind is BreakKind.BOS else ConfirmationType.BMS
        candidates.append(Confirmation(ctype, ltf.timeframe, brk.index, brk.timestamp, brk.direction,
                                       brk.broken_level, brk.origin_price, brk.close))

    if params.allow_first_candle:
        for k in range(touch_index, n):
            c = ltf[k]
            if poi.direction is Bias.BULLISH and c.is_bullish and c.low <= poi.high and c.close >= poi.low:
                candidates.append(Confirmation(ConfirmationType.FIRST_CANDLE, ltf.timeframe, k, c.timestamp, poi.direction,
                                               poi.high, float(ltf.low[touch_index:k + 1].min()), c.close))
                break
            if poi.direction is Bias.BEARISH and c.is_bearish and c.high >= poi.low and c.close <= poi.high:
                candidates.append(Confirmation(ConfirmationType.FIRST_CANDLE, ltf.timeframe, k, c.timestamp, poi.direction,
                                               poi.low, float(ltf.high[touch_index:k + 1].max()), c.close))
                break

    fresh = [c for c in candidates if n - 1 - c.index <= max_age]
    if not fresh:
        return None
    return min(fresh, key=lambda c: c.index)
