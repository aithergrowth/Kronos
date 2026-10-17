import pandas as pd

from kronos_trader.config import ConfirmationParams
from kronos_trader.core import CandleSeries, ConfirmationType, Timeframe
from kronos_trader.strategy import allowed_confirmation_timeframes, analyze_structure, find_confirmation, map_pois

T = Timeframe

LTF_ROWS = [
    (104, 104.5, 103.5, 104.2),    # 0
    (104.2, 105, 104, 104.8),      # 1
    (104.8, 105.8, 104.5, 105.2),  # 2 swing high 105.8
    (105.2, 105.5, 103.5, 104),    # 3
    (104, 104.5, 102.5, 103),      # 4 candle 1 of the bearish balance level (low 102.5)
    (103, 103.5, 101, 101.5),      # 5 touches the 99-102 zone; P of the bearish gap
    (101.5, 102, 100, 100.5),      # 6 candle 3: bearish gap 102-102.5; swing low 100 (invalidation)
    (100.5, 103, 100.2, 102.8),    # 7 first bullish candle; closes above 102.5 -> balance shift
    (102.8, 104.5, 102.5, 104.2),  # 8
    (104.2, 106.2, 104, 106.0),    # 9 body close above 105.8 -> BOS
]
BREAKS_ONLY = ConfirmationParams(allow_balance_shift=False, allow_first_candle=False)


def test_minimum_confirmation_timeframes_follow_the_table():
    assert allowed_confirmation_timeframes(T.MN_1) == [T.H_4, T.D_1, T.W_1]
    assert allowed_confirmation_timeframes(T.W_1) == [T.H_1, T.H_4, T.D_1]
    assert allowed_confirmation_timeframes(T.D_1) == [T.MIN_15, T.MIN_30, T.H_1, T.H_4]
    assert allowed_confirmation_timeframes(T.H_4) == [T.MIN_5, T.MIN_15, T.MIN_30, T.H_1]
    assert allowed_confirmation_timeframes(T.H_1) == [T.MIN_1, T.MIN_5, T.MIN_15, T.MIN_30]
    exact = ConfirmationParams(confirmation_tf_mode="exact")
    assert allowed_confirmation_timeframes(T.H_4, exact) == [T.MIN_5] and allowed_confirmation_timeframes(T.H_1, exact) == [T.MIN_1]


def _poi(scenario):
    # the lower-timeframe rows below are drawn around the legacy 99-102 zone
    from kronos_trader.config import StructureParams
    return map_pois(analyze_structure(scenario), StructureParams(poi_mode="sweep_to_gap"), current_price=101.0)[0]


def _ltf(rows=LTF_ROWS):
    return CandleSeries.from_records(rows, T.MIN_15, start="2024-01-01 14:00")


def test_balance_shift_is_the_first_confirmation(scenario):
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    conf = find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False), max_age=9)
    assert conf is not None and conf.type is ConfirmationType.BS
    assert conf.index == 7 and conf.break_level == 102.5 and conf.invalidation_price == 100.0 and conf.close == 102.8


def test_a_balance_shift_can_wait_for_the_structure_break(scenario):
    """``bs_requires_structure``: the shift at candle 7 broke no swing yet; the close above the 105.8 high at candle 9 breaks
    the structure, so the entry moves there (shift level and the low since the touch kept); without a break in reach, none."""
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    only_bs = dict(allow_first_candle=False, allow_bms=False, accept_bos=False)          # the profiles' set: the shift alone
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs), max_age=9).index == 7
    conf = find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs, bs_requires_structure=True), max_age=9)
    assert conf is not None and conf.type is ConfirmationType.BS and conf.index == 9
    assert conf.break_level == 102.5 and conf.invalidation_price == 100.0 and conf.close == 106.0
    short = ConfirmationParams(**only_bs, bs_requires_structure=True, bs_structure_window=1)
    assert find_confirmation(ltf, poi, touch, short, max_age=9) is None
    assert find_confirmation(_ltf(LTF_ROWS[:9]), poi, touch, ConfirmationParams(**only_bs, bs_requires_structure=True),
                             max_age=9) is None


def test_a_balance_shift_can_require_liquidity_taken_first(scenario):
    """``bs_requires_sweep``: the shift counts only after the entry timeframe swept sell-side liquidity (for a long) since the
    touch; a sweep after the shift, or none, leaves no confirmation."""
    from types import SimpleNamespace
    from kronos_trader.core import Bias
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    st = analyze_structure(ltf)
    only_bs = dict(allow_first_candle=False, allow_bms=False, accept_bos=False, bs_requires_sweep=True)
    st.sweeps = []
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs), max_age=9, structure=st) is None
    st.sweeps = [SimpleNamespace(index=6, implied_bias=Bias.BULLISH)]            # swept at candle 6, shift at 7
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs), max_age=9, structure=st).index == 7
    st.sweeps = [SimpleNamespace(index=8, implied_bias=Bias.BULLISH)]            # after the shift: too late
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs), max_age=9, structure=st) is None
    st.sweeps = [SimpleNamespace(index=6, implied_bias=Bias.BEARISH)]            # buy-side taken: the wrong side
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(**only_bs), max_age=9, structure=st) is None


def test_balance_shift_protector_threshold(scenario):
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    conf = find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False, bs_threshold="protector"), max_age=9)
    assert conf.type is ConfirmationType.BS and conf.index == 8          # first close above candle 5's high (103.5)
    assert conf.break_level == 103.5 and conf.close == 104.2


def test_structure_break_confirmation_with_body_close(scenario):
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    conf = find_confirmation(ltf, poi, touch, BREAKS_ONLY)
    assert conf is not None and conf.type is ConfirmationType.BOS
    assert conf.index == 9 and conf.break_level == 105.8 and conf.invalidation_price == 100.0 and conf.close == 106.0


def test_stale_confirmation_is_ignored_unless_max_age_allows(scenario):
    poi = _poi(scenario)
    ltf = _ltf(LTF_ROWS + [(106, 106.5, 105.5, 106.2)])
    touch = ltf.timestamps.iloc[5]
    assert find_confirmation(ltf, poi, touch, BREAKS_ONLY, max_age=0) is None
    assert find_confirmation(ltf, poi, touch, BREAKS_ONLY, max_age=1).index == 9


def test_first_candle_and_priority(scenario):
    poi = _poi(scenario)
    ltf = _ltf(LTF_ROWS[:8])
    touch = ltf.timestamps.iloc[5]
    assert find_confirmation(ltf, poi, touch, BREAKS_ONLY) is None
    first = find_confirmation(ltf, poi, touch, ConfirmationParams(allow_balance_shift=False, allow_first_candle=True))
    assert first.type is ConfirmationType.FIRST_CANDLE and first.index == 7 and first.invalidation_price == 100.0
    both = find_confirmation(ltf, poi, touch, ConfirmationParams())   # BS and first candle on the same candle: BS wins
    assert both.type is ConfirmationType.BS and both.index == 7


def test_confirmation_too_far_from_zone_is_rejected(scenario):
    poi = _poi(scenario)
    ltf = _ltf()
    touch = ltf.timestamps.iloc[5]
    strict = ConfirmationParams(allow_balance_shift=False, allow_first_candle=False, max_extension_zones=1.0)
    assert find_confirmation(ltf, poi, touch, strict) is None          # the BOS closes at 106 > 102 + 1.0 * 3
    loose = ConfirmationParams(allow_first_candle=False, max_extension_zones=1.0)
    assert find_confirmation(ltf, poi, touch, loose, max_age=9).type is ConfirmationType.BS   # the BS closes at 102.8


def test_entry_after_shift_waits_for_the_first_candle_in_the_direction():
    """A bullish shift whose candle closes bearish: the entry is the next bullish candle, at its close."""
    import pandas as pd
    from kronos_trader.config import ConfirmationParams
    from kronos_trader.core import Bias, CandleSeries, Confirmation, ConfirmationType, Timeframe
    from kronos_trader.strategy.confirmation import _entry_candle
    rows = [(1.0, 1.05, 0.99, 1.04), (1.04, 1.06, 1.02, 1.03), (1.03, 1.07, 1.03, 1.065), (1.065, 1.08, 1.06, 1.07)]
    ltf = CandleSeries.from_records(rows, Timeframe.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    shift = Confirmation(ConfirmationType.BS, Timeframe.MIN_15, 1, ltf.timestamps.iloc[1], Bias.BULLISH, 1.02, 0.99, 1.03)   # closes bearish
    entry = _entry_candle(shift, ltf, True, 3)
    assert entry is not None and entry.index == 2 and entry.close == 1.065 and entry.type is ConfirmationType.BS
    same = Confirmation(ConfirmationType.BS, Timeframe.MIN_15, 0, ltf.timestamps.iloc[0], Bias.BULLISH, 1.02, 0.99, 1.04)   # closes bullish itself
    assert _entry_candle(same, ltf, True, 3) is same
    pending = _entry_candle(shift, CandleSeries(ltf.df.iloc[:2].reset_index(drop=True), Timeframe.MIN_15, "EURUSD", validate=False), True, 3)
    assert pending is None                                   # no bullish candle has closed yet
    assert ConfirmationParams().entry_after_shift is False


def test_balance_shift_clears_the_most_recent_opposing_gap_at_that_moment():
    """A bearish gap left inside the zone during the visit is the level to clear, not the older gap higher up
    ("de eerste beste balance shift ... de volgende shift, die zit hier", A 01:20:33)."""
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, Gap, POI
    from kronos_trader.strategy.structure import StructureAnalysis
    closes = [1.0300, 1.0290, 1.0250, 1.0200, 1.0150, 1.0090, 1.0070, 1.0050, 1.0040, 1.0030, 1.0060, 1.0075, 1.0085, 1.0090, 1.0095]
    series = CandleSeries.from_records([(c, c + 0.0005, c - 0.0005, c) for c in closes], T.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    poi = POI(T.H_1, Bias.BULLISH, 1.0000, 1.0100, None, None, 0, pd.Timestamp("2024-01-02 08:00"))
    st = StructureAnalysis(series, StructureParams())
    older = Gap(Bias.BEARISH, 1.0160, 1.0240, 3, series.timestamps.iloc[3], 2, 1.0200, 1.0300, 1)      # drove price into the zone
    newer = Gap(Bias.BEARISH, 1.0045, 1.0065, 8, series.timestamps.iloc[8], 7, 1.0045, 1.0075, 6)      # left inside the zone, later
    st.gaps = [older, newer]
    params = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    conf = find_confirmation(series, poi, series.timestamps.iloc[5], params, max_age=100, structure=st)
    assert conf is not None and conf.type is ConfirmationType.BS
    assert conf.index == 11 and conf.break_level == 1.0065 and conf.close == 1.0075   # first close above the newer gap, far below the older one
    st.gaps = [older]                                                                  # without the newer gap the older one is still the level
    assert find_confirmation(series, poi, series.timestamps.iloc[5], params, max_age=100, structure=st) is None


def test_confirmation_age_allows_finer_candles_inside_the_step():
    from kronos_trader.strategy.engine import confirmation_age
    assert confirmation_age(0, None, T.MIN_1) == 0
    assert confirmation_age(0, 5, T.MIN_1) == 4          # a 1m shift up to four minutes before the 5m step is still new
    assert confirmation_age(0, 5, T.MIN_5) == 0
    assert confirmation_age(0, 5, T.MIN_15) == 0
    assert confirmation_age(2, 5, T.MIN_15) == 2
    assert confirmation_age(0, 15, T.MIN_5) == 2


def test_bms_can_be_switched_off_while_the_balance_shift_stays():
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, BreakKind, POI, StructureBreak, SwingPoint
    from kronos_trader.strategy.structure import StructureAnalysis
    closes = [1.0300, 1.0250, 1.0200, 1.0150, 1.0090, 1.0070, 1.0050, 1.0080, 1.0120, 1.0140]
    series = CandleSeries.from_records([(c, c + 0.0005, c - 0.0005, c) for c in closes], T.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    poi = POI(T.H_1, Bias.BULLISH, 1.0000, 1.0100, None, None, 0, pd.Timestamp("2024-01-02 08:00"))
    st = StructureAnalysis(series, StructureParams())
    swing = SwingPoint(index=3, price=1.0155, kind="high", timestamp=series.timestamps.iloc[3]) if "kind" in SwingPoint.__dataclass_fields__ else None
    brk = StructureBreak(8, series.timestamps.iloc[8], Bias.BULLISH, BreakKind.BMS, 1.0105, swing, 6, 1.0045, 1.0120)
    st.breaks = [brk]
    touch = series.timestamps.iloc[4]
    on = find_confirmation(series, poi, touch, ConfirmationParams(allow_first_candle=False, allow_balance_shift=False), max_age=100, structure=st)
    assert on is not None and on.type is ConfirmationType.BMS and on.index == 8
    off = find_confirmation(series, poi, touch, ConfirmationParams(allow_first_candle=False, allow_balance_shift=False, allow_bms=False), max_age=100, structure=st)
    assert off is None


def test_an_old_crossing_far_from_the_zone_does_not_end_the_balance_shift_search():
    """A close beyond an older opposing gap while price was still far above the zone is not the shift; the search goes on
    and the first close beyond the gap that is current near the zone is (his EURUSD short of 11 Nov 2025: the 5m shift
    at 15:05 UTC below the 14:25 gap, after dozens of earlier crossings on the way down)."""
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, Gap, POI
    from kronos_trader.strategy.structure import StructureAnalysis
    closes = [1.0400, 1.0390, 1.0380, 1.0350, 1.0340, 1.0330, 1.0200, 1.0150, 1.0120, 1.0110, 1.0115, 1.0105, 1.0090, 1.0070, 1.0060]
    series = CandleSeries.from_records([(c, c + 0.0005, c - 0.0005, c) for c in closes], T.MIN_5, start="2024-01-02 09:00", symbol="EURUSD")
    poi = POI(T.H_4, Bias.BEARISH, 1.0100, 1.0140, None, None, 0, pd.Timestamp("2024-01-01 09:00"))     # bearish zone 1.0100-1.0140
    st = StructureAnalysis(series, StructureParams())
    old = Gap(Bias.BULLISH, 1.0385, 1.0395, 2, series.timestamps.iloc[2], 1, 1.0380, 1.0392, 0)      # far above the zone, crossed at index 3
    near = Gap(Bias.BULLISH, 1.0112, 1.0118, 10, series.timestamps.iloc[10], 9, 1.0105, 1.0120, 8)   # formed inside the zone during the visit
    st.gaps = [old, near]
    params = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    conf = find_confirmation(series, poi, series.timestamps.iloc[7], params, max_age=100, structure=st)
    assert conf is not None and conf.type is ConfirmationType.BS
    assert conf.index == 11 and conf.break_level == 1.0112 and conf.close == 1.0105
    assert conf.invalidation_price == 1.0120 + 0.0005        # the high since price re-entered the zone (index 8), the sweep extreme of the last approach


def test_confirmation_search_starts_at_the_latest_re_entry_into_the_zone():
    """Price touched the zone, left it for a while and came back: the shift (and the sweep extreme for the stop) belong to the
    last approach, so an opposing gap and a crossing from the first approach are ignored."""
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, Gap, POI
    from kronos_trader.strategy.confirmation import latest_entry_index
    from kronos_trader.strategy.structure import StructureAnalysis
    poi = POI(T.H_4, Bias.BEARISH, 1.0100, 1.0140, None, None, 0, pd.Timestamp("2024-01-01 09:00"))
    closes = [1.0120, 1.0110, 1.0060, 1.0050, 1.0040, 1.0045, 1.0050, 1.0130, 1.0138, 1.0135, 1.0128, 1.0115, 1.0110]
    #        touch   in     out    out    out    out    out    back   high   .      shift  .      .
    series = CandleSeries.from_records([(c, c + 0.0004, c - 0.0004, c) for c in closes], T.MIN_5, start="2024-01-02 09:00", symbol="EURUSD")
    assert latest_entry_index(series, poi, 0) == 7
    st = StructureAnalysis(series, StructureParams())
    first_approach = Gap(Bias.BULLISH, 1.0112, 1.0116, 1, series.timestamps.iloc[1], 0, 1.0105, 1.0124, 0)   # crossed at index 2 while leaving
    last_approach = Gap(Bias.BULLISH, 1.0129, 1.0133, 9, series.timestamps.iloc[9], 8, 1.0120, 1.0154, 7)   # left by the second approach
    st.gaps = [first_approach, last_approach]
    params = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    conf = find_confirmation(series, poi, series.timestamps.iloc[0], params, max_age=100, structure=st)
    assert conf is not None and conf.type is ConfirmationType.BS and conf.index == 10 and conf.break_level == 1.0129
    assert conf.invalidation_price == 1.0138 + 0.0004          # the high since the re-entry, not since the first touch
    off = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False, search_from_reentry=False)
    old = find_confirmation(series, poi, series.timestamps.iloc[0], off, max_age=100, structure=st)
    assert old is not None and old.index == 2                  # the old search took the crossing of the first approach


def test_a_later_shift_over_a_newer_gap_counts_when_the_first_one_was_not_actionable():
    """Two opposing gaps during one visit, the first crossed long ago (say outside the session): the crossing of the newer gap is
    the fresh confirmation now (his 18 Mar 2024 and 9 Dec 2025 trades: price sat in the zone for hours before the shift he took)."""
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, Gap, POI
    from kronos_trader.strategy.structure import StructureAnalysis
    closes = [1.0130, 1.0125, 1.0118, 1.0108, 1.0112, 1.0120, 1.0126, 1.0130, 1.0128, 1.0124, 1.0127, 1.0122, 1.0109]
    series = CandleSeries.from_records([(c, c + 0.0003, c - 0.0003, c) for c in closes], T.MIN_5, start="2024-01-02 09:00", symbol="EURUSD")
    poi = POI(T.H_4, Bias.BEARISH, 1.0100, 1.0140, None, None, 0, pd.Timestamp("2024-01-01 09:00"))
    st = StructureAnalysis(series, StructureParams())
    first = Gap(Bias.BULLISH, 1.0112, 1.0116, 2, series.timestamps.iloc[2], 1, 1.0105, 1.0124, 0)     # crossed at index 3 (close 1.0108)
    second = Gap(Bias.BULLISH, 1.0117, 1.0121, 9, series.timestamps.iloc[9], 8, 1.0110, 1.0131, 7)    # crossed at index 12 (close 1.0109)
    st.gaps = [first, second]
    params = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    now_fresh = find_confirmation(series, poi, series.timestamps.iloc[0], params, max_age=0, structure=st)
    assert now_fresh is not None and now_fresh.index == 12 and now_fresh.break_level == 1.0117
    earliest = find_confirmation(series, poi, series.timestamps.iloc[0], params, max_age=100, structure=st)
    assert earliest is not None and earliest.index == 3                                       # with no age limit the first one still comes first


def test_the_candle_that_holds_the_touch_gives_the_sweep_extreme_for_the_stop():
    """A touch seen on the 5m at 09:05 lies inside the 15m candle of 09:00: that candle's high is the sweep the stop
    goes behind (8 October: the search began at the next 15m candle, and the stop sat inside the sweep)."""
    from kronos_trader.config import StructureParams
    from kronos_trader.core.types import Bias, Gap, POI
    from kronos_trader.strategy.structure import StructureAnalysis
    poi = POI(T.H_4, Bias.BEARISH, 1.0100, 1.0140, None, None, 0, pd.Timestamp("2024-01-01 09:00"))
    rows = [(1.0120, 1.0150, 1.0115, 1.0125),      # 09:00: the touch (seen on the 5m at 09:05), the sweep high 1.0150
            (1.0125, 1.0135, 1.0118, 1.0130),      # 09:15
            (1.0130, 1.0138, 1.0110, 1.0112)]      # 09:30: closes under the bullish gap -> the balance shift
    series = CandleSeries.from_records(rows, T.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    st = StructureAnalysis(series, StructureParams())
    st.gaps = [Gap(Bias.BULLISH, 1.0122, 1.0126, 1, series.timestamps.iloc[1], 0, 1.0115, 1.0150, 0)]
    params = ConfirmationParams(allow_first_candle=False, allow_bms=False, accept_bos=False)
    conf = find_confirmation(series, poi, pd.Timestamp("2024-01-02 09:05"), params, max_age=100, structure=st)
    assert conf is not None and conf.type is ConfirmationType.BS and conf.index == 2
    assert conf.invalidation_price == 1.0150                 # not 1.0138, the high of the candles after the touch
    aligned = find_confirmation(series, poi, pd.Timestamp("2024-01-02 09:00"), params, max_age=100, structure=st)
    assert aligned is not None and aligned.invalidation_price == 1.0150
