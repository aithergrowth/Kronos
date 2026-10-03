import pandas as pd
import pytest

from kronos_trader.config import RiskParams, Settings, SymbolSpec
from kronos_trader.core import Bias, Confirmation, ConfirmationType, Direction, LiquiditySide, LiquidityLevel, SwingKind, SwingPoint, Timeframe
from kronos_trader.core.types import BalanceBlock
from kronos_trader.strategy import analyze_structure, build_setup, compute_stop, find_take_profit, map_pois, size_position

T = Timeframe
EURUSD = Settings().symbol("EURUSD")


class StubStructure:
    def __init__(self, bsl=(), ssl=(), bear_blocks=(), bull_blocks=()):
        self._bsl, self._ssl = bsl, ssl
        self._bear = bear_blocks
        self._bull = bull_blocks

    def _level(self, price, side):
        sw = SwingPoint(0, pd.Timestamp("2024-01-01"), price, SwingKind.HIGH if side is LiquiditySide.BUY_SIDE else SwingKind.LOW)
        return LiquidityLevel(price, side, sw)

    def resting_liquidity_above(self, price):
        return [self._level(p, LiquiditySide.BUY_SIDE) for p in sorted(self._bsl) if p > price]

    def resting_liquidity_below(self, price):
        return [self._level(p, LiquiditySide.SELL_SIDE) for p in sorted(self._ssl, reverse=True) if p < price]

    def unmitigated_blocks(self, direction):
        src = self._bear if direction is Bias.BEARISH else self._bull
        return [BalanceBlock(direction, lo, hi, 0, pd.Timestamp("2024-01-01"), 0) for lo, hi in src]


def test_stop_is_one_pip_behind_invalidation():
    params = RiskParams(sl_offset_pips=1.0)
    assert compute_stop(Direction.LONG, 1.1000, EURUSD, params) == 1.0999
    assert compute_stop(Direction.SHORT, 1.1000, EURUSD, params) == 1.1001


def test_lot_size_uses_one_percent_and_spread_buffer():
    lots, risk_amount, risk_distance, stop_pips = size_position(100_000, 1.1000, 1.0950, EURUSD, RiskParams())
    assert risk_amount == 1000.0
    assert stop_pips == pytest.approx(51.0)          # 50 pips + 1 pip buffer
    assert risk_distance == pytest.approx(0.0051)
    assert lots == 1.96                              # 1000 / (51 * 10) floored to 0.01


def test_lot_size_below_minimum_is_zero():
    lots, *_ = size_position(100, 1.1000, 1.0950, EURUSD, RiskParams())
    assert lots == 0.0


def test_take_profit_policies():
    st = {T.H_1: StubStructure(bsl=[1.1200, 1.1300], bear_blocks=[(1.1150, 1.1170)]),
          T.MIN_15: StubStructure(bsl=[1.1050])}   # below the POI timeframe -> ignored
    default = find_take_profit(Direction.LONG, 1.1000, st, T.H_1, RiskParams())    # "TP altijd op liquiditeit"
    assert default[0] == 1.1200 and "liquidity" in default[1]
    nearest = find_take_profit(Direction.LONG, 1.1000, st, T.H_1, RiskParams(tp_policy="nearest"))
    assert nearest[0] == 1.1150 and "order block" in nearest[1]
    liq = find_take_profit(Direction.LONG, 1.1000, st, T.H_1, RiskParams(tp_policy="liquidity_first"))
    assert liq[0] == 1.1200 and "liquidity" in liq[1]
    assert find_take_profit(Direction.SHORT, 1.1000, st, T.H_1, RiskParams()) is None
    higher = {T.H_1: StubStructure(), T.H_4: StubStructure(bsl=[1.1300])}
    assert find_take_profit(Direction.LONG, 1.1000, higher, T.H_1, RiskParams())[0] == 1.1300   # falls back to a higher timeframe


def test_build_setup_enforces_min_rr(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    params = RiskParams(stop_basis="confirmation")
    good = {T.H_1: StubStructure(bsl=[1.1200])}
    setup, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, good, params, 100_000)
    assert setup is not None and reasons == []
    assert setup.stop == 1.0949 and setup.take_profit == 1.1200
    assert setup.rr == pytest.approx(0.02 / 0.0052)
    assert setup.lots == 1.92 and setup.breakeven_r == 4.0
    bad = {T.H_1: StubStructure(bsl=[1.1100])}
    setup, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, bad, params, 100_000)
    assert setup is None and "R:R" in reasons[0]
    none, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, {T.H_1: StubStructure()}, params, 100_000)
    assert none is None and "target" in reasons[0]


def test_stop_behind_the_protected_zone(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]          # P = candle 12, low 100.6
    conf = Confirmation(ConfirmationType.BS, T.MIN_15, 7, pd.Timestamp("2024-01-01 15:45"), Bias.BULLISH, 102.5, 100.0, 102.8)
    spec = SymbolSpec("TEST", 0.01, 1.0, price_decimals=2)
    targets = {T.H_1: StubStructure(bsl=[112.0])}
    setup, reasons = build_setup("TEST", spec, Direction.LONG, poi, conf, 102.8, targets, RiskParams(), 100_000)
    assert setup is not None, reasons
    assert setup.stop == pytest.approx(100.59)                                   # 100.6 minus one pip
    assert "protected zone" in setup.notes[0]
    explicit, _ = build_setup("TEST", spec, Direction.LONG, poi, conf, 102.8, targets, RiskParams(), 100_000, protection_level=101.0)
    assert explicit.stop == pytest.approx(100.99)                                # a 1H P handed in by the engine wins


TEST = SymbolSpec("TEST", 0.01, 1.0, price_decimals=2, typical_spread_pips=2.0)   # the scenario trades around 100


def test_max_entry_depth_rejects_an_entry_deep_in_the_zone(scenario):
    """An entry deeper than ``max_entry_depth`` of the zone's height (from the edge price enters by) is refused: the P is a
    few pips away and the stop has no room.  Off by default; an entry outside the zone counts as depth 0."""
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]          # bullish 100.6-110.0
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 104.0, 100.0, 102.0)
    good = {T.H_1: StubStructure(bsl=[115.0])}
    deep = round(poi.low + 0.2 * poi.height, 2)       # 80 % of the way in (a bullish zone is entered from its high)
    shallow = round(poi.high - 0.2 * poi.height, 2)   # 20 % in
    default, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, deep, good, RiskParams(stop_basis="confirmation", min_rr=0.5), 100_000)
    assert default is not None
    params = RiskParams(stop_basis="confirmation", min_rr=0.5, max_entry_depth=0.5)
    refused, reasons = build_setup("TEST", TEST, Direction.LONG, poi, conf, deep, good, params, 100_000)
    assert refused is None and "80%" in reasons[0] and "no room for the stop" in reasons[0]
    ok, reasons = build_setup("TEST", TEST, Direction.LONG, poi, conf, shallow, good, params, 100_000)
    assert ok is not None and reasons == []
    outside, reasons = build_setup("TEST", TEST, Direction.LONG, poi, conf, poi.high + 0.5, {T.H_1: StubStructure(bsl=[125.0])}, params, 100_000)
    assert outside is not None and reasons == []


def test_tp_max_rr_takes_a_nearer_liquidity_when_the_floor_target_is_too_far(scenario):
    """With ``tp_max_rr`` a liquidity level above the confirmation timeframe whose R:R lies between ``min_rr`` and the cap
    replaces a floor target beyond the cap: the nearest such level by default, the farthest with ``tp_cap_choice``;
    when nothing fits, the far target stays."""
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_1, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 108.5, 107.0, 108.0)
    st = {T.H_1: StubStructure(bsl=[115.0]), T.MIN_15: StubStructure(bsl=[108.3, 109.5]), T.MIN_5: StubStructure(bsl=[109.0])}
    base = RiskParams(stop_basis="confirmation", tp_policy="liquidity_nearest", tp_floor_tf=T.H_1, min_rr=0.5)
    far, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, base, 100_000)
    assert far is not None and far.take_profit == 115.0 and far.rr > 2            # the 1H floor target, 7.0 on a 1.03 risk
    capped = RiskParams(stop_basis="confirmation", tp_policy="liquidity_nearest", tp_floor_tf=T.H_1, min_rr=0.5, tp_max_rr=2.0)
    near, reasons = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, capped, 100_000)
    assert near is not None and reasons == []
    assert near.take_profit == 109.0                       # the 5m level: nearest with R:R >= 0.5 (the 15m 108.3 gives 0.29)
    assert 0.5 <= near.rr <= 2.0 and "R:R cap 2.0" in near.tp_source and "nearer than 1H buy-side liquidity 115.00000" in near.tp_source
    farthest = RiskParams(stop_basis="confirmation", tp_policy="liquidity_nearest", tp_floor_tf=T.H_1, min_rr=0.5, tp_max_rr=2.0, tp_cap_choice="farthest")
    full, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, farthest, 100_000)
    assert full is not None and full.take_profit == 109.5    # the 15m level: farthest within the cap (1.46R)
    nothing_fits = {T.H_1: StubStructure(bsl=[115.0]), T.MIN_15: StubStructure(bsl=[108.3])}
    kept, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, nothing_fits, capped, 100_000)
    assert kept is not None and kept.take_profit == 115.0   # no nearer level with R:R >= min: the far target stays


def test_previous_extreme_target_is_the_lowest_low_before_the_touch(scenario):
    """``tp_policy previous_extreme``: the target is the extreme of the last ``tp_lookback_candles`` candles on the zone's
    timeframe before the touch, a buffer before it; when nothing lies beyond entry it falls back to the nearest liquidity."""
    from kronos_trader.strategy.risk import previous_extreme_target
    st = analyze_structure(scenario)
    poi = map_pois(st, current_price=101.0)[0]                      # bullish 100.6-110.0 on the 1H
    series = st.series
    touch = series.ts_list[-1]
    idx = series.index_at_or_after(touch)
    params = RiskParams(tp_policy="previous_extreme", tp_lookback_candles=5, tp_buffer_pips=2.0)
    expected_high = float(series.high[idx - 5:idx].max()) - 0.02   # 2 pips of 0.01 before the high
    level = previous_extreme_target(Direction.LONG, expected_high - 1.0, {T.H_1: st}, T.H_1, params, touch, pip_size=0.01)
    assert level is not None and level[0] == pytest.approx(expected_high) and "previous high" in level[1] and "5 candles" in level[1]
    assert previous_extreme_target(Direction.LONG, expected_high + 1.0, {T.H_1: st}, T.H_1, params, touch, pip_size=0.01) is None
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 104.0, 100.0, 102.0)
    structures = {T.H_1: st, T.H_4: StubStructure(bsl=[expected_high + 50.0])}
    setup, reasons = build_setup("TEST", TEST, Direction.LONG, poi, conf, expected_high - 1.0, structures,
                                 RiskParams(tp_policy="previous_extreme", tp_lookback_candles=5, tp_buffer_pips=2.0, stop_basis="confirmation", min_rr=0.05),
                                 100_000, touch_ts=touch)
    assert setup is not None and setup.take_profit == pytest.approx(expected_high, abs=0.01) and "previous high" in setup.tp_source
    fallback, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, expected_high + 1.0, structures,
                              RiskParams(tp_policy="previous_extreme", tp_lookback_candles=5, stop_basis="confirmation", min_rr=0.05), 100_000, touch_ts=touch)
    assert fallback is not None and fallback.take_profit == pytest.approx(expected_high + 50.0)   # nothing beyond entry: the nearest liquidity


def test_min_stop_pips_moves_a_tight_stop_out(scenario):
    """A stop nearer than ``min_stop_pips`` is moved out to that distance; a wider one is left alone."""
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_5, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 108.5, 107.95, 108.0)
    st = {T.H_1: StubStructure(bsl=[112.0])}
    tight, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, RiskParams(stop_basis="confirmation", min_rr=0.5), 100_000)
    assert tight is not None and tight.stop == pytest.approx(107.94)                 # 6 pips of 0.01: the swing minus the 1-pip offset
    wide, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, RiskParams(stop_basis="confirmation", min_rr=0.5, min_stop_pips=10), 100_000)
    assert wide is not None and wide.stop == pytest.approx(107.90) and "moved out" in wide.notes[0]
    assert wide.rr == pytest.approx((112.0 - 108.0) / (0.10 + 0.01))
    same, _ = build_setup("TEST", TEST, Direction.LONG, poi, conf, 108.0, st, RiskParams(stop_basis="confirmation", min_rr=0.5, min_stop_pips=3), 100_000)
    assert same is not None and same.stop == pytest.approx(107.94)


def test_impulse_origin_target_is_the_extreme_before_the_zone_formed(scenario):
    """``tp_policy impulse_origin``: the target is the extreme of the candles before the zone's first candle (the low or
    high the creating move started from); nothing beyond entry falls back to the nearest liquidity."""
    from kronos_trader.strategy.risk import impulse_origin_target
    st = analyze_structure(scenario)
    poi = map_pois(st, current_price=101.0)[0]
    series = st.series
    end = (poi.gap.protector_index + 1) if poi.gap is not None else series.index_at_or_after(poi.created_at)
    params = RiskParams(tp_policy="impulse_origin", tp_origin_candles=3, tp_buffer_pips=1.0)
    expected = float(series.high[max(0, end - 4):end].max()) - 0.01
    level = impulse_origin_target(Direction.LONG, expected - 1.0, {T.H_1: st}, poi, params, pip_size=0.01)
    assert level is not None and level[0] == pytest.approx(expected) and "origin high" in level[1]
    assert impulse_origin_target(Direction.LONG, expected + 1.0, {T.H_1: st}, poi, params, pip_size=0.01) is None
