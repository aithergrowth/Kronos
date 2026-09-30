"""Lower-timeframe confirmation.

Written plan (K1 06:30-06:37): options are **BS** (balance shift), **BMS** and
the **first bullish/bearish candle**; the minimum confirmation timeframe per POI
is Monthly -> 4H, Weekly -> 1H, Daily -> 15m, 4H -> 5m, 1H -> 1m.

* **Balance shift**: after the touch, a candle body closes through the
  opposing balance level - the gap that drove price into the zone (A 01:29:29
  distinguishes it from a plain structural break by the opposing balance level).
* **BMS / BOS**: a body close through the lower-timeframe swing ("closure").
* **First candle**: the first candle in the POI direction that traded in the zone.

Candidates are ranked by time, then BS > BMS > BOS > first candle.
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
    bullish = poi.direction is Bias.BULLISH

    def within_zone_reach(close: float) -> bool:
        if bullish:
            return poi.low <= close <= poi.high + ext
        return poi.low - ext <= close <= poi.high

    candidates: List[Confirmation] = []

    # balance shift ----------------------------------------------------------------------
    if params.allow_balance_shift:
        opposing = [g for g in st.gaps_in(poi.direction.opposite)
                    if touch_index - params.opposing_gap_lookback <= g.index <= touch_index + 1]
        if opposing:
            gap = opposing[-1]
            level = gap.high if bullish else gap.low     # the far edge of the opposing balance level
            for k in range(max(touch_index, gap.index + 1), n):
                close = float(ltf.close[k])
                if (bullish and close > level) or (not bullish and close < level):
                    if within_zone_reach(close):
                        invalidation = float(ltf.low[touch_index:k + 1].min()) if bullish else float(ltf.high[touch_index:k + 1].max())
                        candidates.append(Confirmation(ConfirmationType.BS, ltf.timeframe, k, ltf.timestamps.iloc[k],
                                                       poi.direction, level, invalidation, close))
                    break

    # structure breaks --------------------------------------------------------------------
    for brk in st.breaks:
        if brk.index < touch_index or brk.direction is not poi.direction:
            continue
        if not within_zone_reach(brk.close):
            continue
        if brk.kind is BreakKind.BOS and not params.accept_bos:
            continue
        ctype = ConfirmationType.BOS if brk.kind is BreakKind.BOS else ConfirmationType.BMS
        candidates.append(Confirmation(ctype, ltf.timeframe, brk.index, brk.timestamp, brk.direction,
                                       brk.broken_level, brk.origin_price, brk.close))

    # first candle in the POI direction -----------------------------------------------------
    if params.allow_first_candle:
        for k in range(touch_index, n):
            c = ltf[k]
            if bullish and c.is_bullish and c.low <= poi.high and c.close >= poi.low:
                candidates.append(Confirmation(ConfirmationType.FIRST_CANDLE, ltf.timeframe, k, c.timestamp, poi.direction,
                                               poi.high, float(ltf.low[touch_index:k + 1].min()), c.close))
                break
            if not bullish and c.is_bearish and c.high >= poi.low and c.close <= poi.high:
                candidates.append(Confirmation(ConfirmationType.FIRST_CANDLE, ltf.timeframe, k, c.timestamp, poi.direction,
                                               poi.low, float(ltf.high[touch_index:k + 1].max()), c.close))
                break

    fresh = [c for c in candidates if n - 1 - c.index <= max_age]
    if not fresh:
        return None
    return min(fresh, key=lambda c: (c.index, c.type.priority))
