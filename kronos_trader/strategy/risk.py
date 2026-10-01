"""Entry, stop, target and position sizing rules.

* SL strictly behind the invalidation swing that created the confirmation break.
* TP at the opposite higher-timeframe external liquidity line or the next
  unmitigated higher-timeframe balance block.
* Minimum R:R 1:3.
* 1 % risk per trade, with a 1-pip protection buffer in the lot-size maths.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from ..config import RiskParams, SymbolSpec
from ..core.timeframe import Timeframe
from ..core.types import Bias, Confirmation, Direction, POI, TradeSetup
from .exits import breakeven_trigger_r
from .structure import StructureAnalysis


def compute_stop(direction: Direction, invalidation_price: float, spec: SymbolSpec, params: RiskParams) -> float:
    offset = params.sl_offset_pips * spec.pip_size
    stop = invalidation_price - offset if direction is Direction.LONG else invalidation_price + offset
    return spec.round_price(stop)


def find_take_profit(
    direction: Direction,
    entry: float,
    structures: Dict[Timeframe, StructureAnalysis],
    poi_tf: Timeframe,
    params: RiskParams,
    confirmation_tf: Optional[Timeframe] = None,
) -> Optional[Tuple[float, str]]:
    """Target beyond ``entry``.

    Default policy ``liquidity``: "ik zet ten alle tijden mijn take profit op
    liquiditeit" (A 01:50:40) - the nearest resting opposite liquidity on the POI
    timeframe, then on higher timeframes.  Policy ``liquidity_nearest``: the
    nearest resting opposite liquidity on any timeframe above the confirmation
    timeframe (the next substantial high/low rather than the zone's own far
    extreme; his accepted trades run 0.7R-2R, A 01:43:58-01:47:06).  Legacy
    policies also consider unmitigated order blocks.
    """
    liquidity: List[Tuple[float, str, Timeframe]] = []
    balance: List[Tuple[float, str]] = []
    nearest_policy = params.tp_policy == "liquidity_nearest" and confirmation_tf is not None
    for tf, st in structures.items():
        if nearest_policy:
            if tf <= confirmation_tf:
                continue
        elif tf < poi_tf:
            continue
        if direction is Direction.LONG:
            for lvl in st.resting_liquidity_above(entry):
                liquidity.append((lvl.price, f"{tf.label} buy-side liquidity {lvl.price:.5f} (x{lvl.touches})", tf))
            for blk in st.unmitigated_blocks(Bias.BEARISH):
                if blk.low > entry:
                    balance.append((blk.low, f"{tf.label} bearish order block {blk.low:.5f}-{blk.high:.5f}"))
        else:
            for lvl in st.resting_liquidity_below(entry):
                liquidity.append((lvl.price, f"{tf.label} sell-side liquidity {lvl.price:.5f} (x{lvl.touches})", tf))
            for blk in st.unmitigated_blocks(Bias.BULLISH):
                if blk.high < entry:
                    balance.append((blk.high, f"{tf.label} bullish order block {blk.low:.5f}-{blk.high:.5f}"))

    def nearest(cands) -> Optional[Tuple[float, str]]:
        if not cands:
            return None
        best = min(cands, key=lambda c: abs(c[0] - entry))
        return best[0], best[1]

    if params.tp_policy == "liquidity":
        own_tf = [c for c in liquidity if c[2] is poi_tf]
        return nearest(own_tf) or nearest(liquidity)
    if params.tp_policy == "liquidity_nearest":
        return nearest(liquidity)
    if params.tp_policy == "liquidity_first":
        return nearest(liquidity) or nearest(balance)
    if params.tp_policy == "balance_first":
        return nearest(balance) or nearest(liquidity)
    return nearest(liquidity + balance)


def resize_at(
    price: float,
    stop: float,
    take_profit: float,
    equity: float,
    spec: SymbolSpec,
    params: RiskParams,
) -> Tuple[float, float, float, float, float]:
    """Size and R:R of a setup executed at ``price`` instead of at its confirmation close.

    Returns ``(lots, risk_amount, risk_distance, rr, stop_pips)``; ``lots`` is 0 when
    the stop is too wide for the minimum lot at ``params.risk_pct`` of ``equity``.
    """
    lots, risk_amount, risk_distance, stop_pips = size_position(equity, price, stop, spec, params)
    rr_distance = risk_distance if params.rr_includes_buffer else abs(price - stop)
    rr = abs(take_profit - price) / rr_distance if rr_distance > 0 else 0.0
    return lots, risk_amount, risk_distance, rr, stop_pips


def size_position(
    equity: float,
    entry: float,
    stop: float,
    spec: SymbolSpec,
    params: RiskParams,
) -> Tuple[float, float, float, float]:
    """Return ``(lots, risk_amount, risk_distance, stop_pips)``.

    ``risk_distance`` includes the spread buffer so the money at risk when the
    stop is hit through a spread is still <= ``risk_pct`` of equity.
    """
    raw = abs(entry - stop)
    risk_distance = raw + params.spread_buffer_pips * spec.pip_size
    stop_pips = risk_distance / spec.pip_size
    risk_amount = equity * params.risk_pct / 100.0
    if stop_pips <= 0:
        return 0.0, risk_amount, risk_distance, stop_pips
    lots = risk_amount / (stop_pips * spec.pip_value_per_lot)
    lots = math.floor(lots / spec.lot_step + 1e-9) * spec.lot_step
    lots = min(lots, spec.max_lot)
    if lots < spec.min_lot:
        lots = 0.0
    return round(lots, 4), risk_amount, risk_distance, stop_pips


def build_setup(
    symbol: str,
    spec: SymbolSpec,
    direction: Direction,
    poi: POI,
    confirmation: Confirmation,
    entry: float,
    structures: Dict[Timeframe, StructureAnalysis],
    params: RiskParams,
    equity: float,
    breakeven_r: Optional[float] = None,
    protection_level: Optional[float] = None,
) -> Tuple[Optional[TradeSetup], List[str]]:
    """Apply the SL / TP / R:R / sizing rules; returns ``(setup, rejection_reasons)``.

    ``protection_level`` is the extreme of the protected zone (P) the stop sits
    behind when ``stop_basis == "protector"`` ("SL ALTIJD op minimale 1H P");
    it defaults to the POI's own protector.  With ``stop_basis == "confirmation"``
    the lower-timeframe invalidation swing is used instead.
    """
    reasons: List[str] = []
    if params.stop_basis == "protector":
        level = protection_level if protection_level is not None else poi.protector_extreme
        stop_note = "stop behind the protected zone (P)"
    else:
        level = confirmation.invalidation_price
        stop_note = "stop behind the confirmation swing"
    stop = compute_stop(direction, level, spec, params)
    if direction is Direction.LONG and stop >= entry or direction is Direction.SHORT and stop <= entry:
        reasons.append(f"stop {stop} ({stop_note}) is not behind entry {entry}")
        return None, reasons

    target = find_take_profit(direction, entry, structures, poi.timeframe, params, confirmation_tf=confirmation.timeframe)
    if target is None:
        reasons.append("no opposite liquidity or unmitigated balance block to target")
        return None, reasons
    tp_price, tp_source = spec.round_price(target[0]), target[1]

    lots, risk_amount, risk_distance, stop_pips = size_position(equity, entry, stop, spec, params)
    reward_distance = abs(tp_price - entry)
    rr_distance = risk_distance if params.rr_includes_buffer else abs(entry - stop)
    rr = reward_distance / rr_distance if rr_distance > 0 else 0.0
    if rr < params.min_rr:
        reasons.append(f"R:R {rr:.2f} below minimum {params.min_rr:.1f} (target {tp_source})")
        return None, reasons
    if lots <= 0:
        reasons.append(f"stop of {stop_pips:.1f} pips too wide for {spec.min_lot} lot minimum at {params.risk_pct}% risk")
        return None, reasons

    setup = TradeSetup(
        symbol=symbol,
        direction=direction,
        poi=poi,
        confirmation=confirmation,
        entry=entry,
        stop=stop,
        take_profit=tp_price,
        risk_distance=risk_distance,
        reward_distance=reward_distance,
        rr=rr,
        lots=lots,
        risk_amount=risk_amount,
        breakeven_r=breakeven_r if breakeven_r is not None else breakeven_trigger_r(poi.timeframe),
        tp_source=tp_source,
        notes=[f"{stop_note}; {stop_pips:.1f} pips incl. {params.spread_buffer_pips:.0f}-pip buffer"],
    )
    return setup, reasons
