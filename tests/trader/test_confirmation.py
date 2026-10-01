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
