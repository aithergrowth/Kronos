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
