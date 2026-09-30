"""Bias rules.

Per timeframe (rule: "liquidity + balance align -> bullish or bearish; conflicting -> 50/50"):

* **liquidity view** - what the most recent liquidity event implies.  A sweep
  of sell-side liquidity (wick below a low, close back inside) implies price
  now targets the other side -> bullish; a body close *through* a level is a
  break in that direction.
* **balance view** - the direction of the most recent structure break, as long
  as the balance block it created has not been closed through (violated).

Across timeframes (rule: "minimum 3/5 must match", valid combos
``1M+1W+1D``, ``1W+1D+4H``, ``1M+1D+1H``; ``1D+4H+1H`` = scalp only; anything
else = no trade).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..config import BiasParams, StructureParams
from ..core.candles import CandleSeries
from ..core.timeframe import BIAS_TIMEFRAMES, Timeframe
from ..core.types import Bias, BiasDecision, TimeframeBias, TradeMode
from .structure import StructureAnalysis, Sweep, StructureBreak, analyze_structure


def timeframe_bias(
    structure: "StructureAnalysis | CandleSeries",
    params: Optional[BiasParams] = None,
    structure_params: Optional[StructureParams] = None,
) -> TimeframeBias:
    """Liquidity view + balance view -> bias for one timeframe."""
    params = params or BiasParams()
    st = structure if isinstance(structure, StructureAnalysis) else analyze_structure(structure, structure_params)
    n = st.n
    notes: List[str] = []

    # liquidity view -----------------------------------------------------------
    liquidity = Bias.NEUTRAL
    events = st.events_in_order()
    if events:
        last = events[-1]
        age = n - 1 - last.index
        if age <= params.liquidity_lookback:
            if isinstance(last, Sweep):
                liquidity = last.implied_bias
                notes.append(f"liquidity: {last.level.side.value} swept @ {last.level.price:.5f} ({age} candles ago) -> {liquidity}")
            else:
                liquidity = last.direction
                notes.append(f"liquidity: {last.kind.value} closed through {last.broken_level:.5f} ({age} candles ago) -> {liquidity}")
        else:
            notes.append(f"liquidity: last event {age} candles ago is older than lookback {params.liquidity_lookback} -> 50/50")
    else:
        notes.append("liquidity: no sweep or break found -> 50/50")

    # balance view -------------------------------------------------------------
    balance = Bias.NEUTRAL
    brk: Optional[StructureBreak] = st.last_break
    if brk is not None:
        block = st.block_for_break(brk)
        if block is not None and block.is_violated:
            notes.append(f"balance: {brk.direction} block {block.low:.5f}-{block.high:.5f} violated at candle {block.violated_index} -> 50/50")
        else:
            balance = brk.direction
            where = "unmitigated" if block is not None and not block.is_mitigated else "mitigated"
            notes.append(f"balance: last {brk.kind.value} {brk.direction}, block {block.low:.5f}-{block.high:.5f} ({where}) -> {balance}")
    else:
        notes.append("balance: no structure break found -> 50/50")

    if liquidity is balance and liquidity is not Bias.NEUTRAL:
        bias = liquidity
        notes.append(f"aligned -> {bias}")
    else:
        bias = Bias.NEUTRAL
        notes.append("conflicting / incomplete -> 50/50")
    return TimeframeBias(timeframe=st.series.timeframe, bias=bias, liquidity_view=liquidity, balance_view=balance, notes=notes)


def combine_biases(biases: Dict[Timeframe, Bias], params: Optional[BiasParams] = None) -> BiasDecision:
    """Apply the 3/5 rule and the valid-combination table."""
    params = params or BiasParams()
    voting = [tf for tf in BIAS_TIMEFRAMES if tf in biases]
    neutral = tuple(tf for tf in voting if biases[tf] is Bias.NEUTRAL)
    best: Optional[BiasDecision] = None

    for direction in (Bias.BULLISH, Bias.BEARISH):
        aligned = tuple(tf for tf in voting if biases[tf] is direction)
        conflicting = tuple(tf for tf in voting if biases[tf] is direction.opposite)
        if len(aligned) < params.min_matching_timeframes:
            continue
        aligned_set = set(aligned)
        for combo in params.full_combos:
            if set(combo) <= aligned_set:
                return BiasDecision(direction, TradeMode.FULL, aligned, conflicting, neutral, tuple(combo),
                                    f"{direction}: {'+'.join(tf.label for tf in combo)} aligned -> full trade allowed")
        if set(params.scalp_combo) <= aligned_set:
            return BiasDecision(direction, TradeMode.SCALP, aligned, conflicting, neutral, tuple(params.scalp_combo),
                                f"{direction}: 1D+4H+1H aligned -> scalp only")
        best = BiasDecision(direction, TradeMode.NONE, aligned, conflicting, neutral, None,
                            f"{direction}: {'+'.join(tf.label for tf in aligned)} aligned but not a valid combination -> no trade")

    if best is not None:
        return best
    aligned_bull = tuple(tf for tf in voting if biases[tf] is Bias.BULLISH)
    aligned_bear = tuple(tf for tf in voting if biases[tf] is Bias.BEARISH)
    detail = ", ".join(f"{tf.label}={biases[tf]}" for tf in voting)
    return BiasDecision(Bias.NEUTRAL, TradeMode.NONE, (), (), neutral, None,
                        f"fewer than {params.min_matching_timeframes} timeframes agree ({detail}) -> no trade")
