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
    (104, 104.5, 102.5, 103),      # 4
    (103, 103.5, 101, 101.5),      # 5 touches the 99-102 zone
    (101.5, 102, 100, 100.5),      # 6 swing low 100 (invalidation)
    (100.5, 103, 100.2, 102.8),    # 7 first bullish candle
    (102.8, 104.5, 102.5, 104.2),  # 8
    (104.2, 106.2, 104, 106.0),    # 9 body close above 105.8 -> BOS
]


def test_minimum_confirmation_timeframes_follow_the_table():
    assert allowed_confirmation_timeframes(T.MN_1) == [T.H_4, T.D_1, T.W_1]
    assert allowed_confirmation_timeframes(T.W_1) == [T.H_1, T.H_4, T.D_1]
    assert allowed_confirmation_timeframes(T.D_1) == [T.MIN_15, T.MIN_30, T.H_1, T.H_4]
    assert allowed_confirmation_timeframes(T.H_4) == [T.MIN_5, T.MIN_15, T.MIN_30, T.H_1]
    assert allowed_confirmation_timeframes(T.H_1) == [T.MIN_1, T.MIN_5, T.MIN_15, T.MIN_30]


def _poi(scenario):
    return map_pois(analyze_structure(scenario), current_price=101.0)[0]


def test_bos_confirmation_with_body_close(scenario):
    poi = _poi(scenario)
    ltf = CandleSeries.from_records(LTF_ROWS, T.MIN_15, start="2024-01-01 14:00")
    touch = ltf.timestamps.iloc[5]
    conf = find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False))
    assert conf is not None and conf.type is ConfirmationType.BOS
    assert conf.index == 9 and conf.break_level == 105.8 and conf.invalidation_price == 100.0 and conf.close == 106.0


def test_stale_confirmation_is_ignored_unless_max_age_allows(scenario):
    poi = _poi(scenario)
    ltf = CandleSeries.from_records(LTF_ROWS + [(106, 106.5, 105.5, 106.2)], T.MIN_15, start="2024-01-01 14:00")
    touch = ltf.timestamps.iloc[5]
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False), max_age=0) is None
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False), max_age=1).index == 9


def test_first_candle_confirmation_when_enabled(scenario):
    poi = _poi(scenario)
    ltf = CandleSeries.from_records(LTF_ROWS[:8], T.MIN_15, start="2024-01-01 14:00")
    touch = ltf.timestamps.iloc[5]
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False)) is None
    conf = find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=True))
    assert conf.type is ConfirmationType.FIRST_CANDLE and conf.index == 7 and conf.invalidation_price == 100.0


def test_confirmation_too_far_from_zone_is_rejected(scenario):
    poi = _poi(scenario)
    ltf = CandleSeries.from_records(LTF_ROWS, T.MIN_15, start="2024-01-01 14:00")
    touch = ltf.timestamps.iloc[5]
    assert find_confirmation(ltf, poi, touch, ConfirmationParams(allow_first_candle=False, max_extension_zones=1.0)) is None
