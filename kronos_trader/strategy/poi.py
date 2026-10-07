"""POI mapping - "X to b/P" (K1 03:54).

Default mode ``liquidity_to_protection`` (trading-plan video D 12:21-12:54 and
FVG video F 03:00-03:36): the buying / selling area runs from the liquidity the
displacement took (X, "begint ten alle tijden bij het punt van liquiditeit")
through the balance level (b, the gap) to the protector candle (P) that created
it; price may react just inside the area, midway, after filling the gap or
deeper at P, and interest ends below P ("wanneer die onder de P komt").

Legacy mode ``sweep_to_gap`` keeps the earlier reading: sweep wick to the gap.
Mapped on 1M, 1W, 1D, 4H, 1H, both sides.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

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


def _map_liquidity_to_protection(st: StructureAnalysis, params: StructureParams) -> List[POI]:
    ts_list = st.series.ts_list
    by_break: Dict[object, POI] = {}
    for gap in st.gaps:
        d = gap.direction
        brk = next((b for b in st.breaks if b.direction is d
                    and gap.protector_index <= b.index <= gap.index + params.poi_break_window), None)
        if brk is None:
            if not params.poi_gap_zones:
                continue                               # no liquidity taken by this displacement: no X, no POI
            x, key, created = (gap.high if d is Bias.BULLISH else gap.low), ("gap", gap.index), gap.index   # the price gap alone
        else:
            x, key, created = brk.broken_level, brk.index, max(gap.index, brk.index)
        if d is Bias.BULLISH:
            low, high = gap.protector_low, max(x, gap.high)
            if params.poi_extent == "gap":
                high = gap.high
            elif params.poi_extent == "protector":
                high = min(high, gap.protector_high)   # P's range, never past X
        else:
            low, high = min(x, gap.low), gap.protector_high
            if params.poi_extent == "gap":
                low = gap.low
            elif params.poi_extent == "protector":
                low = max(low, gap.protector_low)
        if high <= low:
            continue
        if key in by_break:                            # several gaps in one impulse: keep the first (deepest P)
            continue
        sweep = next((s for s in reversed(st.sweeps) if s.implied_bias is d and s.index < gap.protector_index
                      and gap.protector_index - s.index <= params.max_bars_sweep_to_balance), None)
        by_break[key] = POI(
            timeframe=st.series.timeframe, direction=d, low=float(low), high=float(high), sweep=sweep,
            balance=st.block_for_break(brk) if brk is not None else None, created_index=created, created_at=ts_list[created],
            gap=gap, liquidity_level=float(x), liquidity_break=brk,
        )
    return sorted(by_break.values(), key=lambda p: p.created_index)


def _map_sweep_to_gap(st: StructureAnalysis, params: StructureParams) -> List[POI]:
    pois: List[POI] = []
    for sweep in st.sweeps:
        want = sweep.implied_bias
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
        low, high = (sweep.extreme, far) if want is Bias.BULLISH else (far, sweep.extreme)
        if high <= low:
            continue
        pois.append(POI(
            timeframe=st.series.timeframe, direction=want, low=float(low), high=float(high), sweep=sweep,
            balance=st.block_for_break(brk) if brk is not None else None, created_index=gap.index,
            created_at=gap.timestamp, gap=gap, liquidity_level=float(sweep.extreme), liquidity_break=brk,
        ))
    return pois


def map_pois(st: StructureAnalysis, params: Optional[StructureParams] = None, current_price: Optional[float] = None) -> List[POI]:
    params = params or st.params
    pois = _map_sweep_to_gap(st, params) if params.poi_mode == "sweep_to_gap" else _map_liquidity_to_protection(st, params)
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


def poi_scan(poi: POI, series: CandleSeries) -> Tuple[bool, Optional[int]]:
    """``(invalidated, first touch index)`` from the closed candles of ``series`` after the zone formed."""
    start = poi.created_index + 1
    if start >= len(series):
        return False, None
    if poi.direction is Bias.BULLISH:
        invalid = np.flatnonzero(series.close[start:] < poi.low)
        touched = np.flatnonzero(series.low[start:] <= poi.high)
    else:
        invalid = np.flatnonzero(series.close[start:] > poi.high)
        touched = np.flatnonzero(series.high[start:] >= poi.low)
    return bool(invalid.size), (start + int(touched[0]) if touched.size else None)


def update_poi_status(poi: POI, series: CandleSeries, current_price: Optional[float] = None,
                      scan: Optional[Tuple[bool, Optional[int]]] = None) -> POI:
    """Status as of the end of ``series`` (closed candles) and ``current_price``.

    Invalidation = a close beyond the protection line (below P for a bullish zone).  ``scan`` is
    ``poi_scan(poi, series)`` when the caller kept it (the candles did not change since)."""
    price = float(current_price) if current_price is not None else float(series.close[-1])
    invalidated, poi.first_touch_index = scan if scan is not None else poi_scan(poi, series)
    if invalidated:
        poi.status = POIStatus.INVALIDATED
        return poi
    if poi.direction is Bias.BULLISH and price < poi.low or poi.direction is Bias.BEARISH and price > poi.high:
        poi.status = POIStatus.TESTED if poi.first_touch_index is not None else POIStatus.FRESH
        return poi
    if poi.contains(price):
        poi.status = POIStatus.ACTIVE
    elif poi.first_touch_index is not None:
        poi.status = POIStatus.TESTED
    else:
        poi.status = POIStatus.FRESH
    return poi


@dataclass
class VisitState:
    """Where price stands with one zone on the lowest timeframe, carried from candle to candle."""
    last_ts: Optional[pd.Timestamp] = None      # last candle folded in
    inside: bool = False
    visits: int = 0
    visit_start_ts: Optional[pd.Timestamp] = None
    invalid: bool = False

    def step(self, poi: POI, hi: float, lo: float, close: float, ts, ext: float, check_invalid: bool) -> None:
        if poi.direction is Bias.BULLISH:
            touches, left, invalid = lo <= poi.high, close > poi.high + ext, close < poi.low
        else:
            touches, left, invalid = hi >= poi.low, close < poi.low - ext, close > poi.high
        self.last_ts = ts
        if invalid and check_invalid:
            self.invalid = True
            self.inside, self.visit_start_ts = False, None
            return
        if not self.inside and touches:
            self.inside, self.visits, self.visit_start_ts = True, self.visits + 1, ts
        elif self.inside and left:
            self.inside, self.visit_start_ts = False, None


def _visit_scan_start(poi: POI, ltf: CandleSeries) -> int:
    start = ltf.index_at_or_after(poi.created_at)
    return max(start, ltf.index_at_or_after(poi.timeframe.close_time(poi.created_at)))


def current_visit(poi: POI, ltf: CandleSeries, max_extension_zones: float) -> Tuple[Optional[int], int, bool]:
    """Track visits of price into the POI on a lower timeframe, over the candles given.

    Returns ``(start_index_of_current_visit, visit_number, invalidated)``.
    A visit starts when a candle trades into the zone and ends when a candle
    closes more than ``max_extension_zones`` zone-heights beyond it.  The
    current visit is the last one that has not ended.  ``start_index`` is
    ``None`` when price is not visiting the zone right now.  Stateless: it only
    sees the candles passed in; :class:`VisitTracker` remembers earlier ones.
    """
    n = len(ltf)
    ext = poi.height * max_extension_zones
    check_invalid = poi.timeframe <= ltf.timeframe
    state = VisitState()
    start_index: Optional[int] = None
    for k in range(_visit_scan_start(poi, ltf), n):
        state.step(poi, ltf.high[k], ltf.low[k], ltf.close[k], ltf.ts_list[k], ext, check_invalid)
        if state.invalid:
            return None, state.visits, True
        start_index = k if state.visit_start_ts is not None and state.visit_start_ts == ltf.ts_list[k] else start_index
        if state.visit_start_ts is None:
            start_index = None
    return start_index, state.visits, False


class VisitTracker:
    """Visit history per zone that survives the analysis window.

    The engine only analyses the last few hundred lowest-timeframe candles, so a
    stateless scan forgets a first visit that happened before that window and
    would trade a later return as "the first".  This keeps a :class:`VisitState`
    per zone and folds in only the candles it has not seen yet.
    """

    def __init__(self, max_zones: int = 5000):
        self.states: Dict[Tuple[str, int, str], VisitState] = {}
        self.max_zones = max_zones

    def observe(self, poi: POI, ltf: CandleSeries, max_extension_zones: float) -> Tuple[Optional[pd.Timestamp], int, bool]:
        """Fold the new candles of ``ltf`` into the zone's state; returns ``(touch_ts, visit_number, invalidated)``."""
        state = self.states.get(poi.key)
        if state is None:
            state = VisitState()
            self.states[poi.key] = state
            if len(self.states) > self.max_zones:
                for key in sorted(self.states, key=lambda k: (self.states[k].last_ts or pd.Timestamp.min))[: self.max_zones // 5]:
                    del self.states[key]
        n = len(ltf)
        if n == 0:
            return state.visit_start_ts, state.visits, state.invalid
        ext = poi.height * max_extension_zones
        check_invalid = poi.timeframe <= ltf.timeframe
        if state.last_ts is None:
            start = _visit_scan_start(poi, ltf)
        else:
            start = ltf.index_after(state.last_ts)
        high, low, close, ts_list = ltf.high, ltf.low, ltf.close, ltf.ts_list
        for k in range(start, n):
            state.step(poi, high[k], low[k], close[k], ts_list[k], ext, check_invalid)
            if state.invalid:
                break
        return state.visit_start_ts, state.visits, state.invalid
