"""structure.session_liquidity: yesterday's high/low and the Asia range as the liquidity a displacement takes (X)."""
from dataclasses import replace

import numpy as np
import pandas as pd

from kronos_trader.config import StructureParams
from kronos_trader.core import Bias, CandleSeries, Timeframe
from kronos_trader.strategy import analyze_structure, map_pois
from kronos_trader.strategy.poi import session_levels

T = Timeframe


def _two_days() -> CandleSeries:
    """1 June (Amsterdam) ranging up to a high of 101.0; 2 June: an Asia range of 99.6-100.5, then at 08:00 a quiet
    candle and a displacement (P, low 100.3) that closes through yesterday's high, leaving a bullish gap (100.4 -> 100.9)."""
    day1 = [(100.2, 100.6, 99.9, 100.4), (100.4, 100.7, 100.1, 100.3), (100.3, 100.8, 100.0, 100.5)] * 7 \
        + [(100.5, 101.0, 100.3, 100.6), (100.6, 100.8, 100.2, 100.4), (100.4, 100.7, 100.1, 100.3)]
    asia = [(100.3, 100.5, 99.8, 100.0), (100.0, 100.3, 99.6, 100.1)] * 4
    move = [(100.1, 100.4, 100.0, 100.3), (100.3, 101.6, 100.3, 101.5), (101.5, 101.9, 100.9, 101.8),
            (101.8, 102.0, 101.6, 101.7), (101.7, 101.9, 101.5, 101.8), (101.8, 102.1, 101.6, 102.0)]
    return CandleSeries.from_records(day1 + asia + move, T.H_1, start="2026-05-31 22:00", symbol="TEST")


def test_session_levels_know_yesterday_and_the_asia_range_only_once_it_is_over():
    series = _two_days()
    lv = session_levels(series, "Europe/Amsterdam", 8)
    first_day2 = 24                                            # 2026-06-01 22:00 UTC = 2 June 00:00 Amsterdam
    assert np.isnan(lv["pdh"][0]) and lv["pdh"][first_day2] == 101.0 and lv["pdl"][first_day2] == 99.9
    assert np.isnan(lv["ah"][first_day2]) and np.isnan(lv["ah"][first_day2 + 7])    # before 08:00 the range is still forming
    assert lv["ah"][first_day2 + 8] == 100.5 and lv["al"][first_day2 + 8] == 99.6


def test_a_displacement_through_yesterdays_high_maps_a_zone_only_with_session_liquidity():
    series = _two_days()
    st = analyze_structure(series, StructureParams())
    st = replace(st, breaks=[])                                 # no swing broke: only the session level can be X
    assert not [p for p in map_pois(st, StructureParams()) if p.direction is Bias.BULLISH]
    zones = [p for p in map_pois(st, StructureParams(session_liquidity=True)) if p.direction is Bias.BULLISH]
    assert len(zones) == 1
    z = zones[0]
    assert z.liquidity_level == 101.0 and z.liquidity_break is None
    assert z.low == 100.3 and z.high == 101.0                   # from P (the candle that made the gap) to X
    assert z.created_at == pd.Timestamp("2026-06-02 08:00")    # the gap's third candle, after the close through X
