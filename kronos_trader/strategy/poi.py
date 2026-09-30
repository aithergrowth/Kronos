"""POI mapping - "X to b/P" (K1 03:54).

A POI forms when liquidity is swept (X, the wick that took the level) and a
balance level (b, the gap) is created in the implied direction shortly after by
a protector candle (P).  The zone runs from the sweep wick to the balance level;
which edge of the gap ends the zone is a setting (``poi_far_edge``).  Mapped on
1M, 1W, 1D, 4H, 1H, both sides.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from ..config import StructureParams
from ..core.candles import CandleSeries
from ..core.types import Bias, Gap, POI, POIStatus
from .structure import StructureAnalysis


def _far_edge(gap: Gap, direction: Bias, mode: str) -> float:
    if mode == "gap_top":
        return gap.high if direction is Bias.BULLISH else gap.low
    if mode == "protector":
        return gap.protector_high if direction is Bias.BULLISH else gap.protector_low
    return gap.low if direction is Bias.BULLISH else gap.high     # gap_bottom: where the balance level begins


def map_pois(st: StructureAnalysis, params: Optional[StructureParams] = None, current_price: Optional[float] = None) -> List[POI]:
    params = params or st.params
    pois: List[POI] = []
    for sweep in st.sweeps:
        want = sweep.implied_bias
        # an opposite structure break before the balance forms means the sweep did not lead anywhere
        opposite_break = next((b.index for b in st.breaks if b.index > sweep.index and b.direction is not want), None)
        gap = next((g for g in st.gaps_in(want)
                    if g.index > sweep.index and g.index - sweep.index <= params.max_bars_sweep_to_balance
                    and (opposite_break is None or g.index < opposite_break)), None)
        if gap is None:
            continue
        brk = next((b for b in st.breaks if b.index > sweep.index and b.direction is want
                    and (opposite_break is None or b.index < opposite_break)), None)
        if params.poi_requires_break and brk is None:
            continue
        far = _far_edge(gap, want, params.poi_far_edge)
        if want is Bias.BULLISH:
            low, high = sweep.extreme, far
        else:
            low, high = far, sweep.extreme
        if high <= low:
            continue
        pois.append(POI(
            timeframe=st.series.timeframe,
            direction=want,
            low=float(low),
            high=float(high),
            sweep=sweep,
            balance=st.block_for_break(brk) if brk is not None else None,
            created_index=gap.index,
            created_at=gap.timestamp,
            gap=gap,
        ))
    # twin sweeps (equal lows swept one after the other) can produce identical zones: keep the first
    unique: List[POI] = []
    seen = set()
    for poi in pois:
        key = (poi.direction, round(poi.low, 8), round(poi.high, 8), poi.created_index)
        if key in seen:
            continue
        seen.add(key)
        unique.append(poi)
    for poi in unique:
        update_poi_status(poi, st.series, current_price)
    return unique


def update_poi_status(poi: POI, series: CandleSeries, current_price: Optional[float] = None) -> POI:
    """Status as of the end of ``series`` (closed candles) and ``current_price``."""
    n = len(series)
    start = poi.created_index + 1
    price = float(current_price) if current_price is not None else float(series.close[-1])
    poi.first_touch_index = None
    if start < n:
        if poi.direction is Bias.BULLISH:
            invalid = np.flatnonzero(series.close[start:] < poi.low)
            touched = np.flatnonzero(series.low[start:] <= poi.high)
        else:
            invalid = np.flatnonzero(series.close[start:] > poi.high)
            touched = np.flatnonzero(series.high[start:] >= poi.low)
        if touched.size:
            poi.first_touch_index = start + int(touched[0])
        if invalid.size:
            poi.status = POIStatus.INVALIDATED
            return poi
    if poi.direction is Bias.BULLISH and price < poi.low or poi.direction is Bias.BEARISH and price > poi.high:
        # price is beyond the protection line intrabar; a close there would invalidate
        poi.status = POIStatus.TESTED if poi.first_touch_index is not None else POIStatus.FRESH
        return poi
    if poi.contains(price):
        poi.status = POIStatus.ACTIVE
    elif poi.first_touch_index is not None:
        poi.status = POIStatus.TESTED
    else:
        poi.status = POIStatus.FRESH
    return poi


def current_visit(poi: POI, ltf: CandleSeries, max_extension_zones: float) -> Tuple[Optional[int], int, bool]:
    """Track visits of price into the POI on a lower timeframe.

    Returns ``(start_index_of_current_visit, visit_number, invalidated)``.
    A visit starts when a candle trades into the zone and ends when a candle
    closes more than ``max_extension_zones`` zone-heights beyond it.  The
    current visit is the last one that has not ended.  ``start_index`` is
    ``None`` when price is not visiting the zone right now.
    """
    n = len(ltf)
    start = ltf.index_at_or_after(poi.created_at)
    # the POI-timeframe candle that created the zone closes after created_at; skip it
    start = max(start, ltf.index_at_or_after(poi.timeframe.close_time(poi.created_at)))
    ext = poi.height * max_extension_zones
    inside = False
    visit_start: Optional[int] = None
    visits = 0
    for k in range(start, n):
        hi, lo, close = ltf.high[k], ltf.low[k], ltf.close[k]
        if poi.direction is Bias.BULLISH:
            touches = lo <= poi.high
            left = close > poi.high + ext
            invalid = close < poi.low
        else:
            touches = hi >= poi.low
            left = close < poi.low - ext
            invalid = close > poi.high
        if invalid and poi.timeframe <= ltf.timeframe:
            return None, visits, True
        if not inside and touches:
            inside = True
            visits += 1
            visit_start = k
        elif inside and left:
            inside = False
            visit_start = None
    return visit_start, visits, False
