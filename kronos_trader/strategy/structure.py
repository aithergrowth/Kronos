"""Market-structure detection: swings, liquidity, sweeps, breaks and balance blocks.

This module turns raw candles into the vocabulary the Dorus Wanders rules use:

* **Swing points** - fractal highs/lows (``swing_left`` bars lower on the left,
  ``swing_right`` bars not higher on the right).  A swing is only *known*
  ``swing_right`` candles after it prints, so nothing here looks ahead.
* **Liquidity levels** - every swing high carries buy-side liquidity (BSL),
  every swing low sell-side liquidity (SSL).  Equal highs/lows within a small
  tolerance stack onto one level (``touches``).
* **Sweep** - a *wick* pierces the level while the body closes back inside the
  range (rule: "High-Timeframe Sweep: wick pierce only").
* **Structure break** (BOS / BMS) - a candle *body closes* through the level
  (rule: "wicks do NOT count").  BOS continues the previous break direction,
  BMS reverses it.
* **Balance block** - the last opposing candle before the impulse that broke
  structure (order block); tracked as mitigated / violated afterwards.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from ..config import StructureParams
from ..core.candles import CandleSeries
from ..core.types import (
    BalanceBlock,
    Bias,
    BreakKind,
    LiquidityLevel,
    LiquiditySide,
    StructureBreak,
    Sweep,
    SwingKind,
    SwingPoint,
)


def find_swings(series: CandleSeries, left: int = 2, right: int = 2) -> List[SwingPoint]:
    """Fractal swing highs and lows, in candle order (vectorised)."""
    highs, lows = series.high, series.low
    n = len(series)
    if n < left + right + 1:
        return []
    idx = np.arange(left, n - right)
    lh = sliding_window_view(highs, left)[idx - left].max(axis=1)      # highs[i-left:i]
    rh = sliding_window_view(highs, right)[idx + 1].max(axis=1)        # highs[i+1:i+1+right]
    ll = sliding_window_view(lows, left)[idx - left].min(axis=1)
    rl = sliding_window_view(lows, right)[idx + 1].min(axis=1)
    is_high = (highs[idx] > lh) & (highs[idx] >= rh)
    is_low = (lows[idx] < ll) & (lows[idx] <= rl)
    swings: List[SwingPoint] = []
    for i in idx[is_high | is_low]:
        i = int(i)
        ts = series.timestamps.iloc[i]
        if is_high[i - left]:
            swings.append(SwingPoint(i, ts, float(highs[i]), SwingKind.HIGH))
        if is_low[i - left]:
            swings.append(SwingPoint(i, ts, float(lows[i]), SwingKind.LOW))
    return swings


@dataclass
class StructureAnalysis:
    series: CandleSeries
    params: StructureParams
    swings: List[SwingPoint] = field(default_factory=list)
    levels: List[LiquidityLevel] = field(default_factory=list)
    sweeps: List[Sweep] = field(default_factory=list)
    breaks: List[StructureBreak] = field(default_factory=list)
    blocks: List[BalanceBlock] = field(default_factory=list)
    _block_by_break: Dict[int, BalanceBlock] = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------- shortcuts
    @property
    def n(self) -> int:
        return len(self.series)

    @property
    def last_sweep(self) -> Optional[Sweep]:
        return self.sweeps[-1] if self.sweeps else None

    @property
    def last_break(self) -> Optional[StructureBreak]:
        return self.breaks[-1] if self.breaks else None

    def block_for_break(self, brk: StructureBreak) -> Optional[BalanceBlock]:
        return self._block_by_break.get(brk.index)

    def resting_liquidity(self, side: LiquiditySide) -> List[LiquidityLevel]:
        return [lvl for lvl in self.levels if lvl.side is side and lvl.is_resting]

    def resting_liquidity_above(self, price: float) -> List[LiquidityLevel]:
        lv = [l for l in self.resting_liquidity(LiquiditySide.BUY_SIDE) if l.price > price]
        return sorted(lv, key=lambda l: l.price)

    def resting_liquidity_below(self, price: float) -> List[LiquidityLevel]:
        lv = [l for l in self.resting_liquidity(LiquiditySide.SELL_SIDE) if l.price < price]
        return sorted(lv, key=lambda l: -l.price)

    def unmitigated_blocks(self, direction: Bias) -> List[BalanceBlock]:
        return [b for b in self.blocks if b.direction is direction and not b.is_mitigated and not b.is_violated]

    def events_in_order(self):
        """Sweeps and breaks merged by candle index (sweeps first on ties)."""
        items = [(s.index, 0, s) for s in self.sweeps] + [(b.index, 1, b) for b in self.breaks]
        return [it[2] for it in sorted(items, key=lambda it: (it[0], it[1]))]

    def summary(self) -> str:
        parts = [f"{self.series.symbol or ''} {self.series.timeframe.label}: {self.n} candles, "
                 f"{len(self.swings)} swings, {len(self.sweeps)} sweeps, {len(self.breaks)} breaks, {len(self.blocks)} blocks"]
        if self.last_sweep:
            s = self.last_sweep
            parts.append(f"last sweep: {s.level.side.value} @ {s.level.price:.5f} on {s.timestamp} -> {s.implied_bias}")
        if self.last_break:
            b = self.last_break
            parts.append(f"last break: {b.kind.value} {b.direction} through {b.broken_level:.5f} on {b.timestamp}")
        return "; ".join(parts)


def analyze_structure(series: CandleSeries, params: Optional[StructureParams] = None) -> StructureAnalysis:
    """Single forward pass over ``series`` producing all structure events without look-ahead."""
    params = params or StructureParams()
    n = len(series)
    analysis = StructureAnalysis(series=series, params=params)
    if n < params.swing_left + params.swing_right + 2:
        return analysis

    opens, highs, lows, closes = series.open, series.high, series.low, series.close
    ts = series.timestamps
    swings = find_swings(series, params.swing_left, params.swing_right)
    analysis.swings = swings

    confirm_at: Dict[int, List[SwingPoint]] = {}
    for sw in swings:
        confirm_at.setdefault(sw.index + params.swing_right, []).append(sw)

    active_high: List[LiquidityLevel] = []
    active_low: List[LiquidityLevel] = []
    swing_lows_seen: List[SwingPoint] = []   # confirmed swing lows, for origin lookup
    swing_highs_seen: List[SwingPoint] = []
    trend: Optional[Bias] = None
    tol = params.equal_level_tolerance_pct

    for j in range(n):
        # 1) swings confirmed at this candle become liquidity levels -------------
        for sw in confirm_at.get(j, []):
            if sw.kind is SwingKind.HIGH:
                swing_highs_seen.append(sw)
                _register_level(analysis, active_high, sw, LiquiditySide.BUY_SIDE, tol)
            else:
                swing_lows_seen.append(sw)
                _register_level(analysis, active_low, sw, LiquiditySide.SELL_SIDE, tol)

        o, h, l, c = opens[j], highs[j], lows[j], closes[j]
        body_hi, body_lo = max(o, c), min(o, c)

        # 2) buy-side liquidity: swept or broken? ---------------------------------
        broken_highs: List[LiquidityLevel] = []
        for lvl in list(active_high):
            if h <= lvl.price:
                continue
            closes_beyond = c > lvl.price and (not params.full_body_break or o > lvl.price)
            if closes_beyond:
                lvl.broken_index = j
                broken_highs.append(lvl)
                active_high.remove(lvl)
            elif not lvl.is_swept and body_hi <= lvl.price:
                lvl.swept_index = j
                analysis.sweeps.append(Sweep(level=lvl, index=j, timestamp=ts.iloc[j], extreme=float(h), close=float(c)))
        if broken_highs:
            lvl = max(broken_highs, key=lambda x: x.swing.index)   # the most recent structure
            trend = _record_break(analysis, j, Bias.BULLISH, lvl, swing_lows_seen, trend, params)

        # 3) sell-side liquidity ------------------------------------------------
        broken_lows: List[LiquidityLevel] = []
        for lvl in list(active_low):
            if l >= lvl.price:
                continue
            closes_beyond = c < lvl.price and (not params.full_body_break or o < lvl.price)
            if closes_beyond:
                lvl.broken_index = j
                broken_lows.append(lvl)
                active_low.remove(lvl)
            elif not lvl.is_swept and body_lo >= lvl.price:
                lvl.swept_index = j
                analysis.sweeps.append(Sweep(level=lvl, index=j, timestamp=ts.iloc[j], extreme=float(l), close=float(c)))
        if broken_lows:
            lvl = max(broken_lows, key=lambda x: x.swing.index)
            trend = _record_break(analysis, j, Bias.BEARISH, lvl, swing_highs_seen, trend, params)

    _update_block_states(analysis)
    return analysis


# --------------------------------------------------------------------------- internals

def _register_level(analysis: StructureAnalysis, active: List[LiquidityLevel], sw: SwingPoint, side: LiquiditySide, tol: float) -> None:
    for lvl in active:
        if lvl.is_swept:
            continue
        if abs(lvl.price - sw.price) <= tol * sw.price:
            lvl.touches += 1
            lvl.price = max(lvl.price, sw.price) if side is LiquiditySide.BUY_SIDE else min(lvl.price, sw.price)
            return
    lvl = LiquidityLevel(price=sw.price, side=side, swing=sw)
    active.append(lvl)
    analysis.levels.append(lvl)


def _record_break(
    analysis: StructureAnalysis,
    j: int,
    direction: Bias,
    lvl: LiquidityLevel,
    opposite_swings: List[SwingPoint],
    trend: Optional[Bias],
    params: StructureParams,
) -> Bias:
    series = analysis.series
    s = lvl.swing.index
    # origin: the invalidation extreme of the leg that produced the break --------
    start = s + 1
    recent = [sw for sw in opposite_swings if s < sw.index < j]
    if recent:
        start = max(start, recent[-1].index)
    if direction is Bias.BULLISH:
        window = series.low[start:j + 1]
        origin_index = start + int(np.argmin(window))
        origin_price = float(series.low[origin_index])
    else:
        window = series.high[start:j + 1]
        origin_index = start + int(np.argmax(window))
        origin_price = float(series.high[origin_index])

    kind = BreakKind.BOS if trend is None or trend is direction else BreakKind.BMS
    brk = StructureBreak(
        index=j,
        timestamp=series.timestamps.iloc[j],
        direction=direction,
        kind=kind,
        broken_level=float(lvl.price),
        broken_swing=lvl.swing,
        origin_index=origin_index,
        origin_price=origin_price,
        close=float(series.close[j]),
    )
    analysis.breaks.append(brk)

    # balance block: last opposing candle inside the leg -------------------------
    block_idx = origin_index
    for k in range(j - 1, origin_index - 1, -1):
        if direction is Bias.BULLISH and series.close[k] < series.open[k]:
            block_idx = k
            break
        if direction is Bias.BEARISH and series.close[k] > series.open[k]:
            block_idx = k
            break
    if params.block_body_only:
        lo = float(min(series.open[block_idx], series.close[block_idx]))
        hi = float(max(series.open[block_idx], series.close[block_idx]))
    else:
        lo, hi = float(series.low[block_idx]), float(series.high[block_idx])
    block = BalanceBlock(direction=direction, low=lo, high=hi, index=block_idx,
                         timestamp=series.timestamps.iloc[block_idx], break_index=j)
    analysis.blocks.append(block)
    analysis._block_by_break[j] = block
    return direction


def _update_block_states(analysis: StructureAnalysis) -> None:
    series = analysis.series
    n = len(series)
    for block in analysis.blocks:
        start = block.break_index + 1
        if start >= n:
            continue
        if block.direction is Bias.BULLISH:
            touched = np.flatnonzero(series.low[start:] <= block.high)
            violated = np.flatnonzero(series.close[start:] < block.low)
        else:
            touched = np.flatnonzero(series.high[start:] >= block.low)
            violated = np.flatnonzero(series.close[start:] > block.high)
        if touched.size:
            block.mitigated_index = start + int(touched[0])
        if violated.size:
            block.violated_index = start + int(violated[0])
