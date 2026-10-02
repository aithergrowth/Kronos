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
    touch_ts=None,
    pip_size: float = 0.0,
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
    if params.tp_policy == "previous_extreme":
        prev = previous_extreme_target(direction, entry, structures, poi_tf, params, touch_ts, pip_size)
        if prev is not None:
            return prev
    liquidity, balance = target_candidates(direction, entry, structures, poi_tf, params, confirmation_tf, params.tp_floor_tf)

    def nearest(cands) -> Optional[Tuple[float, str]]:
        if not cands:
            return None
        best = min(cands, key=lambda c: abs(c[0] - entry))
        return best[0], best[1]

    if params.tp_policy == "liquidity":
        own_tf = [c for c in liquidity if c[2] is poi_tf]
        return nearest(own_tf) or nearest(liquidity)
    if params.tp_policy in ("liquidity_nearest", "previous_extreme"):
        return nearest(liquidity)
    if params.tp_policy == "liquidity_first":
        return nearest(liquidity) or nearest(balance)
    if params.tp_policy == "balance_first":
        return nearest(balance) or nearest(liquidity)
    return nearest(liquidity + balance)


def target_candidates(
    direction: Direction,
    entry: float,
    structures: Dict[Timeframe, StructureAnalysis],
    poi_tf: Timeframe,
    params: RiskParams,
    confirmation_tf: Optional[Timeframe],
    floor_tf: Optional[Timeframe],
) -> Tuple[List[Tuple[float, str, Timeframe]], List[Tuple[float, str]]]:
    """Resting opposite liquidity and unmitigated balance blocks beyond ``entry``: ``(liquidity, balance)``.

    With ``liquidity_nearest`` the timeframes considered are those above the confirmation timeframe and at or
    above ``floor_tf`` (None = every timeframe above the confirmation timeframe); otherwise the POI timeframe and up.
    """
    liquidity: List[Tuple[float, str, Timeframe]] = []
    balance: List[Tuple[float, str]] = []
    nearest_policy = params.tp_policy in ("liquidity_nearest", "previous_extreme") and confirmation_tf is not None
    for tf, st in structures.items():
        if nearest_policy:
            if tf <= confirmation_tf or (floor_tf is not None and tf < floor_tf):
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
    return liquidity, balance


def previous_extreme_target(
    direction: Direction,
    entry: float,
    structures: Dict[Timeframe, StructureAnalysis],
    poi_tf: Timeframe,
    params: RiskParams,
    touch_ts,
    pip_size: float = 0.0,
) -> Optional[Tuple[float, str]]:
    """The previous significant low (short) or high (long) of the move: the extreme of the last ``tp_lookback_candles``
    candles on the zone's timeframe before the touch, ``tp_buffer_pips`` before it; None when it does not lie beyond entry."""
    st = structures.get(poi_tf)
    if st is None or touch_ts is None or params.tp_lookback_candles <= 0:
        return None
    series = st.series
    idx = series.index_at_or_after(touch_ts)
    lo = max(0, idx - int(params.tp_lookback_candles))
    if idx - lo < 1:
        return None
    buffer = params.tp_buffer_pips * pip_size
    if direction is Direction.LONG:
        level = float(series.high[lo:idx].max()) - buffer
        if level <= entry:
            return None
        return level, f"{poi_tf.label} previous high {level:.5f} ({idx - lo} candles before the touch)"
    level = float(series.low[lo:idx].min()) + buffer
    if level >= entry:
        return None
    return level, f"{poi_tf.label} previous low {level:.5f} ({idx - lo} candles before the touch)"


def nearer_liquidity_target(
    direction: Direction,
    entry: float,
    structures: Dict[Timeframe, StructureAnalysis],
    poi_tf: Timeframe,
    params: RiskParams,
    confirmation_tf: Optional[Timeframe],
    rr_distance: float,
) -> Optional[Tuple[float, str]]:
    """The nearest resting liquidity on any timeframe above the confirmation timeframe whose R:R lies between
    ``min_rr`` and ``tp_max_rr`` (the floor timeframe ignored); None when no level fits."""
    if rr_distance <= 0:
        return None
    liquidity, _ = target_candidates(direction, entry, structures, poi_tf, params, confirmation_tf, None)
    fitting = [(price, source) for price, source, _tf in sorted(liquidity, key=lambda c: abs(c[0] - entry))
               if params.min_rr <= abs(price - entry) / rr_distance <= params.tp_max_rr]
    if not fitting:
        return None
    return fitting[-1] if params.tp_cap_choice == "farthest" else fitting[0]


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


def reconcile_risk(position, broker, budget: float) -> None:
    """Measure the position's risk on its actual fill: ``risk_distance`` becomes entry-to-stop and
    ``risk_amount`` the cash lost at the stop, so R and break-even use what is really at stake.
    The sizing budget and the planned numbers stay in ``meta`` for the record."""
    position.meta.setdefault("risk_budget", float(budget))
    position.meta.setdefault("risk_distance_sized", float(position.risk_distance))
    position.risk_distance = abs(float(position.entry) - float(position.stop))
    position.risk_amount = abs(broker.pnl_for(position.symbol, position.direction, position.entry, position.stop, position.lots))
    position.meta["rr_at_fill"] = (abs(float(position.take_profit) - float(position.entry)) / position.risk_distance
                                   if position.risk_distance > 0 else 0.0)


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
    touch_ts=None,
) -> Tuple[Optional[TradeSetup], List[str]]:
    """Apply the SL / TP / R:R / sizing rules; returns ``(setup, rejection_reasons)``.

    ``protection_level`` is the extreme of the protected zone (P) the stop sits
    behind when ``stop_basis == "protector"`` ("SL ALTIJD op minimale 1H P");
    it defaults to the POI's own protector.  With ``stop_basis == "confirmation"``
    the lower-timeframe invalidation swing is used instead.
    """
    reasons: List[str] = []
    if params.max_entry_depth > 0 and poi.height > 0:
        depth = (poi.high - entry) / poi.height if direction is Direction.LONG else (entry - poi.low) / poi.height
        if depth > params.max_entry_depth:
            reasons.append(f"entry {entry} lies {depth:.0%} of the zone's height inside it (max {params.max_entry_depth:.0%}): "
                           f"no room for the stop")
            return None, reasons
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

    target = find_take_profit(direction, entry, structures, poi.timeframe, params, confirmation_tf=confirmation.timeframe,
                              touch_ts=touch_ts, pip_size=spec.pip_size)
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
    if params.tp_max_rr > 0 and rr > params.tp_max_rr:
        nearer = nearer_liquidity_target(direction, entry, structures, poi.timeframe, params, confirmation.timeframe, rr_distance)
        if nearer is not None:
            far_source, far_rr = tp_source, rr
            tp_price, tp_source = spec.round_price(nearer[0]), f"{nearer[1]} [nearer than {far_source} at 1:{far_rr:.1f}; R:R cap {params.tp_max_rr:.1f}]"
            reward_distance = abs(tp_price - entry)
            rr = reward_distance / rr_distance
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
