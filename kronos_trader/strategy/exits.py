"""Exit rules: break-even after 4R (intraday/scalp) or 2R (swing); no partials; let SL/TP run."""
from __future__ import annotations

from typing import Optional

import pandas as pd

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


WEEK_OPEN_NY = "17:00"          # FX, metals and the index CFDs reopen Sunday 17:00 New York


def _ny_clock(text: str):
    hh, mm = (int(x) for x in str(text).split(":"))
    return pd.Timedelta(hours=hh, minutes=mm)


def weekend_cutoff_after(ts, at: str) -> pd.Timestamp:
    """The first Friday ``at`` (New York time, "HH:MM") after ``ts`` (naive UTC), as naive UTC: when a position opened at
    ``ts`` has to be closed on an account that may not hold over the weekend (prop_firm.weekend_close)."""
    ny = pd.Timestamp(ts).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    cut = ny.normalize() + pd.Timedelta(days=(4 - ny.weekday()) % 7) + _ny_clock(at)
    if cut <= ny:
        cut += pd.Timedelta(days=7)
    return cut.tz_localize("America/New_York").tz_convert("UTC").tz_localize(None)


def in_weekend_close(ts, at: str) -> bool:
    """True from Friday ``at`` New York until the market reopens Sunday 17:00 New York: no new position then."""
    ny = pd.Timestamp(ts).tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    clock = ny - ny.normalize()
    return ((ny.weekday() == 4 and clock >= _ny_clock(at)) or ny.weekday() == 5
            or (ny.weekday() == 6 and clock < _ny_clock(WEEK_OPEN_NY)))


def day_close_cutoff_after(ts, at: str, tz: str = "Europe/Amsterdam") -> pd.Timestamp:
    """The first ``at`` ("HH:MM", ``tz`` clock) at or after ``ts`` (naive UTC), as naive UTC: when a position opened at ``ts``
    is closed before the daily break (exits.day_close)."""
    local = pd.Timestamp(ts).tz_localize("UTC").tz_convert(tz).tz_localize(None)
    hh, mm = (int(x) for x in str(at).split(":"))
    cut = local.normalize() + pd.Timedelta(hours=hh, minutes=mm)
    if cut < local:
        cut += pd.Timedelta(days=1)
    return cut.tz_localize(tz).tz_convert("UTC").tz_localize(None)
