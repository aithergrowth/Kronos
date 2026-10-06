import pandas as pd

from kronos_trader.config import StructureParams
from kronos_trader.core import Bias, CandleSeries, POIStatus, Timeframe
from kronos_trader.strategy import analyze_structure, current_visit, map_pois

LEGACY = StructureParams(poi_mode="sweep_to_gap")


def test_poi_runs_from_liquidity_to_protection(scenario):
    pois = map_pois(analyze_structure(scenario), current_price=105.0)
    assert len(pois) == 1                                   # two gaps in one impulse -> one zone (deepest P)
    poi = pois[0]
    assert poi.direction is Bias.BULLISH
    assert (poi.low, poi.high) == (100.6, 110.0)            # P low (candle 12) -> the 110 high the impulse took
    assert poi.liquidity_level == 110.0 and poi.liquidity_break.index == 13
    assert poi.gap.index == 13 and poi.protector_extreme == 100.6
    assert poi.sweep is not None and poi.sweep.index == 10  # the sweep that preceded the displacement
    assert poi.created_at == pd.Timestamp("2024-01-01 13:00")
    assert poi.status is POIStatus.ACTIVE
    assert map_pois(analyze_structure(scenario), current_price=112.5)[0].status is POIStatus.TESTED   # candle 14 touched 110


def test_poi_invalidates_below_p(scenario_rows):
    rows = list(scenario_rows) + [(111.5, 112, 101, 108), (108, 108.5, 100, 100.3)]   # closes below P low 100.6
    poi = map_pois(analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1)), current_price=100.3)[0]
    assert poi.status is POIStatus.INVALIDATED


def test_legacy_sweep_to_gap_zone(scenario):
    pois = map_pois(analyze_structure(scenario), LEGACY, current_price=105.0)
    assert len(pois) == 1
    poi = pois[0]
    assert (poi.low, poi.high) == (99.0, 102.0)             # sweep wick -> bottom of the gap
    assert poi.protection_level == 99.0 and poi.protector_extreme == 100.6
    assert poi.status is POIStatus.FRESH
    top = map_pois(analyze_structure(scenario), StructureParams(poi_mode="sweep_to_gap", poi_far_edge="gap_top"), current_price=105.0)[0]
    assert (top.low, top.high) == (99.0, 105.0)
    none = map_pois(analyze_structure(scenario), StructureParams(poi_mode="sweep_to_gap", max_bars_sweep_to_balance=1), current_price=105.0)
    assert none == []


def test_legacy_status_active_tested_invalidated(scenario, scenario_rows):
    st = analyze_structure(scenario)
    assert map_pois(st, LEGACY, current_price=101.0)[0].status is POIStatus.ACTIVE
    rows = list(scenario_rows) + [(111.5, 112, 101.5, 108)]          # dips into the zone and leaves
    poi = map_pois(analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1)), LEGACY, current_price=108.0)[0]
    assert poi.status is POIStatus.TESTED and poi.first_touch_index == 16
    rows.append((108, 108.5, 98, 98.5))                                # closes below the protecting low
    assert map_pois(analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1)), LEGACY, current_price=98.5)[0].status is POIStatus.INVALIDATED


def test_current_visit_counts_returns(scenario):
    poi = map_pois(analyze_structure(scenario), LEGACY, current_price=101.0)[0]
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


def test_visit_tracker_remembers_a_first_visit_outside_the_window():
    """A zone touched before the analysis window: the stateless scan calls the return 'visit 1', the tracker 'visit 2'."""
    import pandas as pd
    from kronos_trader.core import Bias, CandleSeries, POI, Timeframe
    from kronos_trader.strategy import VisitTracker, current_visit
    rows = []
    for i in range(403):
        if i in (1, 2):
            rows.append((112.0, 113.0, 105.0, 108.0))      # first visit: trades into the zone 100-110
        elif i == 3:
            rows.append((112.0, 130.0, 111.0, 128.0))      # leaves: close beyond 1.5 zone heights (125), no touch
        elif i == 402:
            rows.append((126.0, 126.0, 109.5, 109.5))      # the return
        else:
            rows.append((126.0, 127.0, 125.5, 126.0))
    series = CandleSeries.from_records(rows, Timeframe.MIN_5, start="2024-01-01 00:00", symbol="EURUSD")
    poi = POI(Timeframe.H_4, Bias.BULLISH, 100.0, 110.0, None, None, 0, pd.Timestamp("2023-12-31 20:00"))
    full = current_visit(poi, series, 1.5)
    assert full[1] == 2 and full[0] == 402
    window = series.tail(400)
    assert current_visit(poi, window, 1.5)[1] == 1                      # the stateless scan forgets visit 1
    tracker = VisitTracker()
    for end in range(5, 404):
        touch, visits, invalid = tracker.observe(poi, series.tail(400) if end == 403 else CandleSeries(series.df.iloc[max(0, end - 400):end].reset_index(drop=True), Timeframe.MIN_5, "EURUSD", validate=False), 1.5)
    assert visits == 2 and touch == series.timestamps.iloc[402] and not invalid
    # stateless and stateful agree when the whole history is visible
    fresh = VisitTracker()
    assert fresh.observe(poi, series, 1.5)[1:] == (2, False)


def test_a_gap_without_liquidity_taken_is_a_zone_only_when_asked():
    """``structure.poi_gap_zones``: a gap whose displacement closed through no high (no X) maps a zone from its P to the
    gap's far edge (his "price gap" trades). Off by default: no liquidity taken, no zone."""
    rows = [
        (104, 105, 103, 104.5),
        (104.5, 105.5, 104, 105),
        (105, 106, 104.5, 105.5),      # 2: swing high 106, never closed through
        (105.5, 105.6, 102, 102.5),
        (102.5, 103, 100, 100.5),
        (100.5, 101, 99, 100),
        (100, 100.8, 99.5, 100.5),
        (100.5, 104, 100.4, 103.8),    # 7: the displacement (P)
        (103.8, 105, 102.5, 104.6),    # 8: low 102.5 above candle 6's high 100.8 -> bullish gap 100.8-102.5
    ]
    st = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1))
    gap = [g for g in st.gaps if g.direction is Bias.BULLISH][-1]
    assert (gap.low, gap.high, gap.index) == (100.8, 102.5, 8)
    assert not [b for b in st.breaks if b.direction is Bias.BULLISH]
    assert not [p for p in map_pois(st) if p.direction is Bias.BULLISH]
    zones = [p for p in map_pois(st, StructureParams(poi_gap_zones=True)) if p.direction is Bias.BULLISH]
    assert len(zones) == 1
    zone = zones[0]
    assert (zone.low, zone.high) == (100.4, 102.5) and zone.liquidity_break is None and zone.liquidity_level == 102.5
    assert zone.created_index == 8 and zone.protector_extreme == 100.4
