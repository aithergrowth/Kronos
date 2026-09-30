import pandas as pd
import pytest

from kronos_trader.config import RiskParams, Settings
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
    nearest = find_take_profit(Direction.LONG, 1.1000, st, T.H_1, RiskParams(tp_policy="nearest"))
    assert nearest[0] == 1.1150 and "balance" in nearest[1]
    liq = find_take_profit(Direction.LONG, 1.1000, st, T.H_1, RiskParams(tp_policy="liquidity_first"))
    assert liq[0] == 1.1200 and "liquidity" in liq[1]
    assert find_take_profit(Direction.SHORT, 1.1000, st, T.H_1, RiskParams()) is None


def test_build_setup_enforces_min_rr(scenario):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-01 16:15"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    good = {T.H_1: StubStructure(bsl=[1.1200])}
    setup, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, good, RiskParams(), 100_000)
    assert setup is not None and reasons == []
    assert setup.stop == 1.0949 and setup.take_profit == 1.1200
    assert setup.rr == pytest.approx(0.02 / 0.0052)
    assert setup.lots == 1.92 and setup.breakeven_r == 4.0
    bad = {T.H_1: StubStructure(bsl=[1.1100])}
    setup, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, bad, RiskParams(), 100_000)
    assert setup is None and "R:R" in reasons[0]
    none, reasons = build_setup("EURUSD", EURUSD, Direction.LONG, poi, conf, 1.1000, {T.H_1: StubStructure()}, RiskParams(), 100_000)
    assert none is None and "target" in reasons[0]
