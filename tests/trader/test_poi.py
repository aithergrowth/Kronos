import pandas as pd

from kronos_trader.core import Bias, CandleSeries, POIStatus, Timeframe
from kronos_trader.strategy import analyze_structure, current_visit, map_pois


def test_poi_is_x_to_balance(scenario):
    pois = map_pois(analyze_structure(scenario), current_price=105.0)
    assert len(pois) == 1
    poi = pois[0]
    assert poi.direction is Bias.BULLISH and (poi.low, poi.high) == (99.0, 102.0)   # sweep wick -> bottom of the gap
    assert poi.protection_level == 99.0 and poi.protector_extreme == 100.6           # P = candle 12
    assert poi.gap is not None and poi.gap.index == 13 and poi.balance is not None
    assert poi.created_at == pd.Timestamp("2024-01-01 13:00")
    assert poi.status is POIStatus.FRESH


def test_poi_far_edge_options(scenario):
    from kronos_trader.config import StructureParams
    st = analyze_structure(scenario)
    top = map_pois(st, StructureParams(poi_far_edge="gap_top"), current_price=105.0)[0]
    assert (top.low, top.high) == (99.0, 105.0)
    prot = map_pois(st, StructureParams(poi_far_edge="protector"), current_price=105.0)[0]
    assert (prot.low, prot.high) == (99.0, 106.0)
    none = map_pois(st, StructureParams(max_bars_sweep_to_balance=1), current_price=105.0)
    assert none == []


def test_poi_status_active_tested_invalidated(scenario, scenario_rows):
    st = analyze_structure(scenario)
    assert map_pois(st, current_price=101.0)[0].status is POIStatus.ACTIVE
    rows = list(scenario_rows) + [(111.5, 112, 101.5, 108)]          # dips into the zone and leaves
    st2 = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1))
    poi = map_pois(st2, current_price=108.0)[0]
    assert poi.status is POIStatus.TESTED and poi.first_touch_index == 16
    rows.append((108, 108.5, 98, 98.5))                                # closes below the protecting low
    st3 = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1))
    assert map_pois(st3, current_price=98.5)[0].status is POIStatus.INVALIDATED


def test_current_visit_counts_returns(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    ltf = CandleSeries.from_records([
        (110, 111, 109, 110),          # 14:00 not touching
        (110, 110.5, 101.5, 102.5),    # 14:15 touches -> visit 1
        (102.5, 104, 102, 103.8),      # inside
        (103.8, 107, 103.5, 106.8),    # closes > 102 + 1.5*3 -> left
        (106.8, 107, 101, 101.5),      # touches again -> visit 2
    ], Timeframe.MIN_15, start="2024-01-01 14:00")
    start, visits, invalid = current_visit(poi, ltf, 1.5)
    assert (start, visits, invalid) == (4, 2, False)
    assert ltf.timestamps.iloc[start] == pd.Timestamp("2024-01-01 15:00")
    gone = CandleSeries.from_records([(110, 111, 109, 110), (110, 110.5, 101.5, 102.5), (102.5, 104, 102, 103.8),
                                      (103.8, 107, 103.5, 106.8)], Timeframe.MIN_15, start="2024-01-01 14:00")
    assert current_visit(poi, gone, 1.5)[0] is None
