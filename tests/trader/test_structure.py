from kronos_trader.config import StructureParams
from kronos_trader.core import Bias, BreakKind, CandleSeries, LiquiditySide, SwingKind, Timeframe
from kronos_trader.strategy import analyze_structure, find_swings


def test_swings_are_fractals(scenario):
    swings = find_swings(scenario, 2, 2)
    assert [(s.index, s.kind, s.price) for s in swings] == [
        (2, SwingKind.LOW, 100.0), (6, SwingKind.HIGH, 110.0), (10, SwingKind.LOW, 99.0)]


def test_sweep_requires_wick_pierce_with_body_inside(scenario):
    st = analyze_structure(scenario)
    assert len(st.sweeps) == 1
    sweep = st.sweeps[0]
    assert sweep.index == 10 and sweep.level.side is LiquiditySide.SELL_SIDE
    assert sweep.level.price == 100.0 and sweep.extreme == 99.0
    assert sweep.implied_bias is Bias.BULLISH
    assert sweep.level.is_swept and not sweep.level.is_broken


def test_close_through_level_is_a_break_not_a_sweep(scenario_rows):
    rows = list(scenario_rows)
    rows[10] = (102.5, 103, 99, 99.5)  # body closes below the 100 low
    st = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1))
    assert not any(s.index == 10 for s in st.sweeps)
    brk = next(b for b in st.breaks if b.index == 10)
    assert brk.direction is Bias.BEARISH and brk.broken_level == 100.0


def test_break_needs_body_close_and_full_body_option(scenario_rows):
    st = analyze_structure(CandleSeries.from_records(scenario_rows, Timeframe.H_1))
    brk = st.breaks[0]
    assert brk.index == 13 and brk.direction is Bias.BULLISH and brk.kind is BreakKind.BOS
    assert brk.broken_level == 110.0
    assert brk.origin_index == 10 and brk.origin_price == 99.0   # invalidation swing = the sweep low

    rows = list(scenario_rows)
    rows[13] = (109.5, 111, 105, 110.8)  # opens below 110, closes above: not a *full body* close
    strict = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1), StructureParams(full_body_break=True))
    assert strict.breaks[0].index == 14
    loose = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1), StructureParams(full_body_break=False))
    assert loose.breaks[0].index == 13


def test_balance_block_is_last_opposing_candle(scenario):
    st = analyze_structure(scenario)
    block = st.block_for_break(st.breaks[0])
    assert block.index == 11 and block.direction is Bias.BULLISH
    assert (block.low, block.high) == (100.5, 102.0)
    assert not block.is_mitigated and not block.is_violated


def test_block_mitigation_and_bms_classification(scenario_rows):
    rows = list(scenario_rows) + [
        (112.5, 113, 105, 106),   # 16
        (106, 107, 100, 101),     # 17 trades into the block 100.5-102 -> mitigated
        (101, 102, 97, 98),       # 18 closes below the 99 swing low -> bearish BMS
    ]
    st = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1))
    block = st.block_for_break(st.breaks[0])
    assert block.mitigated_index == 17
    last = st.breaks[-1]
    assert last.index == 18 and last.direction is Bias.BEARISH and last.kind is BreakKind.BMS


def test_balance_level_is_the_gap_and_p_is_the_candle_that_made_it(scenario):
    st = analyze_structure(scenario)
    gaps = st.gaps_in(Bias.BULLISH)
    gap = next(g for g in gaps if g.index == 13)
    assert (gap.low, gap.high) == (102.0, 105.0)                                    # candle 11 high -> candle 13 low
    assert gap.protector_index == 12 and (gap.protector_low, gap.protector_high) == (100.6, 106.0)
    assert gap.origin_index == 11 and gap.protection_level == 100.6
    assert not gap.is_mitigated and not gap.is_violated
    assert st.last_gap.index == 14                                                  # the impulse leaves a second gap: 106 -> 110
    small = next(g for g in gaps if g.index == 5)                                   # 103 -> 104 in the first rally
    assert small.mitigated_index == 8 and small.violated_index == 10                 # filled on the way down, P broken by the sweep candle


def test_equal_highs_stack_on_one_level():
    rows = [(10, 11, 9, 10), (10, 12, 9.5, 11), (11, 13, 10.5, 12), (12, 12.5, 11, 11.5), (11.5, 12, 10.5, 11),
            (11, 12, 10.5, 11.5), (11.5, 13, 11, 12.5), (12.5, 12.8, 11.8, 12), (12, 12.5, 11, 11.2),
            (11.2, 11.5, 10, 10.5), (10.5, 11, 9.8, 10)]
    st = analyze_structure(CandleSeries.from_records(rows, Timeframe.H_1), StructureParams(equal_level_tolerance_pct=0.001))
    highs = [l for l in st.levels if l.side is LiquiditySide.BUY_SIDE]
    assert len(highs) == 1 and highs[0].touches == 2 and highs[0].price == 13.0
