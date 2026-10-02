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
