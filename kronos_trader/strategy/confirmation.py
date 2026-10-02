"""Lower-timeframe confirmation.

Written plan (K1 06:30-06:37): options are **BS** (balance shift), **BMS** and
the **first bullish/bearish candle**; the minimum confirmation timeframe per POI
is Monthly -> 4H, Weekly -> 1H, Daily -> 15m, 4H -> 5m, 1H -> 1m.

* **Balance shift**: after the touch, a candle body closes through the
  opposing balance level - the most recent gap in the opposing direction at
  that moment, whether it drove price into the zone or formed inside it during
  the visit ("de eerste beste balance shift ... de volgende shift, die zit hier",
  A 01:20:33-01:20:46; A 01:29:29 distinguishes it from a plain structural break
  by the opposing balance level).
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
    if getattr(params, "confirmation_tf_mode", "at_least") == "exact":
        return [min_tf]
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
    if getattr(params, "search_from_reentry", True):
        touch_index = latest_entry_index(ltf, poi, touch_index)
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
        opposing = [g for g in st.gaps_in(poi.direction.opposite) if g.index >= touch_index - params.opposing_gap_lookback]
        if opposing:
            def shift_level(gap):
                if params.bs_threshold == "protector":   # "above the candle that caused the gap" (A 01:07:49, 01:08:22)
                    return gap.protector_high if bullish else gap.protector_low
                return gap.high if bullish else gap.low   # beyond the opposing balance level itself (A 01:31:52, 02:25:46)
            latest = None
            pointer = 0
            crossed = set()            # a gap counts once: its first close beyond it; an old crossing far from the zone does not end the search
            start = max(touch_index, opposing[0].index + 1)
            for g in opposing:         # a gap already closed through before the search window was crossed back then, not now
                if g.index + 1 < start:
                    seg = ltf.close[g.index + 1:start]
                    lvl = shift_level(g)
                    if len(seg) and ((bullish and float(seg.max()) > lvl) or (not bullish and float(seg.min()) < lvl)):
                        crossed.add(g.index)
            for k in range(start, n):
                while pointer < len(opposing) and opposing[pointer].index < k:   # the opposing gap that is current at candle k
                    latest = opposing[pointer]
                    pointer += 1
                if latest.index in crossed:
                    continue
                level = shift_level(latest)
                close = float(ltf.close[k])
                if (bullish and close > level) or (not bullish and close < level):
                    crossed.add(latest.index)
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
        if brk.kind is not BreakKind.BOS and not params.allow_bms:
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

    if params.entry_after_shift:
        candidates = [_entry_candle(c, ltf, bullish, params.entry_after_shift_max_candles) for c in candidates]
        candidates = [c for c in candidates if c is not None]
    fresh = [c for c in candidates if n - 1 - c.index <= max_age]
    if not fresh:
        return None
    return min(fresh, key=lambda c: (c.index, c.type.priority))


def latest_entry_index(ltf: CandleSeries, poi: POI, touch_index: int) -> int:
    """Index of the candle on which price last came back into the zone after at least one candle wholly outside it,
    at or after ``touch_index``; ``touch_index`` itself when price never left the zone since the touch."""
    n = len(ltf)
    if touch_index >= n - 1:
        return touch_index
    lows, highs = ltf.low, ltf.high
    for k in range(n - 1, touch_index, -1):
        inside_k = lows[k] <= poi.high and highs[k] >= poi.low
        outside_prev = highs[k - 1] < poi.low or lows[k - 1] > poi.high
        if inside_k and outside_prev:
            return k
    return touch_index


def _entry_candle(conf: Confirmation, ltf: CandleSeries, bullish: bool, max_candles: int) -> Optional[Confirmation]:
    """The first candle closing in the trade direction at or after the shift; ``None`` while none has closed yet
    (the shift candle itself counts when it closes in the direction: "in dit geval zijn we hier er al", B 09:10)."""
    if conf.type is ConfirmationType.FIRST_CANDLE:
        return conf
    n = len(ltf)
    for j in range(conf.index, min(n, conf.index + 1 + max_candles)):
        c = ltf[j]
        if (bullish and c.is_bullish) or (not bullish and c.is_bearish):
            if j == conf.index:
                return conf
            return Confirmation(conf.type, conf.timeframe, j, c.timestamp, conf.direction, conf.break_level, conf.invalidation_price, c.close)
    return None
