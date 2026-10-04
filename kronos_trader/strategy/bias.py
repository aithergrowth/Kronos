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

    # balance view: the last balance level (gap) and its protector ------------------
    balance = Bias.NEUTRAL
    gap = st.last_gap
    if params.balance_view == "last_tested":
        tested = [g for g in st.gaps if g.is_mitigated]
        gap = tested[-1] if tested else None
        if gap is None:
            notes.append("balance: no balance level tested yet")
    if gap is not None:
        if gap.is_violated:
            if params.balance_violation == "flip":
                balance = gap.direction.opposite
                notes.append(f"balance: {gap.direction} P {gap.protector_low:.5f}-{gap.protector_high:.5f} broken at candle "
                             f"{gap.violated_index} -> continuation {balance}")
            else:
                notes.append(f"balance: {gap.direction} P broken at candle {gap.violated_index} -> 50/50")
        else:
            balance = gap.direction
            where = "unmitigated" if not gap.is_mitigated else "mitigated"
            notes.append(f"balance: last balance level {gap.direction} gap {gap.low:.5f}-{gap.high:.5f} ({where}) -> {balance}")
    else:
        brk: Optional[StructureBreak] = st.last_break
        if brk is not None:
            balance = brk.direction
            notes.append(f"balance: no gap found; last {brk.kind.value} {brk.direction} -> {balance}")
        else:
            notes.append("balance: no balance level found -> 50/50")

    if liquidity is balance and liquidity is not Bias.NEUTRAL:
        bias = liquidity
        notes.append(f"aligned -> {bias}")
    elif (params.conflict_rule == "recent" and liquidity is not Bias.NEUTRAL and balance is not Bias.NEUTRAL
          and events and gap is not None):
        event_index = events[-1].index
        gap_index = gap.mitigated_index if (params.balance_view == "last_tested" and gap.mitigated_index is not None) else gap.index
        bias = liquidity if event_index > gap_index else balance
        notes.append(f"conflicting: the {'liquidity event' if bias is liquidity else 'balance level'} is the more recent "
                     f"(candle {max(event_index, gap_index)} vs {min(event_index, gap_index)}) -> {bias}")
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
        if params.required_aligned and not set(params.required_aligned) <= aligned_set:
            missing = "+".join(tf.label for tf in params.required_aligned if tf not in aligned_set)
            return BiasDecision(Bias.NEUTRAL, TradeMode.NONE, aligned, conflicting, neutral, None,
                                f"{direction}: {missing} not aligned (required) -> no trade")
        for combo in params.active_full_combos:
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
