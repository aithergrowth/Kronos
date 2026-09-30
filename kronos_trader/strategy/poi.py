"""POI mapping.

Rule: *POI = area between liquidity and balance level (protected zone)*; map on
1M, 1W, 1D, 4H, 1H; look at both sides.

A bullish POI forms when sell-side liquidity is swept (wick only) and price
then breaks structure upwards with a body close.  The zone runs from the sweep
wick (the liquidity line that protects it) to the top of the balance block of
that break.  Bearish POIs mirror this.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np

from ..config import StructureParams
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Bias, POI, POIStatus
from .structure import StructureAnalysis


def map_pois(st: StructureAnalysis, params: Optional[StructureParams] = None, current_price: Optional[float] = None) -> List[POI]:
    params = params or st.params
    pois: List[POI] = []
    for sweep in st.sweeps:
        want = sweep.implied_bias
        for brk in st.breaks:
            if brk.index <= sweep.index:
                continue
            if brk.index - sweep.index > params.max_bars_sweep_to_break:
                break
            if brk.direction is not want:
                break  # an opposite break first: the sweep did not lead to displacement
            block = st.block_for_break(brk)
            if block is None:
                break
            if want is Bias.BULLISH:
                low, high = sweep.extreme, block.high
            else:
                low, high = block.low, sweep.extreme
            if high <= low:
                break
            pois.append(POI(
                timeframe=st.series.timeframe,
                direction=want,
                low=float(low),
                high=float(high),
                sweep=sweep,
                balance=block,
                created_index=brk.index,
                created_at=brk.timestamp,
            ))
            break
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
