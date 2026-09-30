"""Exit rules: break-even after 4R (intraday/scalp) or 2R (swing); no partials; let SL/TP run."""
from __future__ import annotations

from typing import Optional

from ..config import ExitParams
from ..core.timeframe import Timeframe
from ..core.types import Direction

SWING_POI_TIMEFRAMES = (Timeframe.MN_1, Timeframe.W_1)


def breakeven_trigger_r(poi_tf: Timeframe, params: Optional[ExitParams] = None) -> float:
    params = params or ExitParams()
    return params.breakeven_r_swing if poi_tf in SWING_POI_TIMEFRAMES else params.breakeven_r_intraday


def r_multiple(direction: Direction, entry: float, risk_distance: float, price: float) -> float:
    if risk_distance <= 0:
        return 0.0
    return direction.sign * (price - entry) / risk_distance


def breakeven_reached(direction: Direction, entry: float, risk_distance: float, extreme_price: float, trigger_r: float) -> bool:
    return r_multiple(direction, entry, risk_distance, extreme_price) >= trigger_r
