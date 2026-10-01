"""Target selection: the POI-timeframe policy against the nearest-substantial-liquidity policy."""
from types import SimpleNamespace

from kronos_trader.config import RiskParams
from kronos_trader.core.timeframe import Timeframe
from kronos_trader.core.types import Direction
from kronos_trader.strategy.risk import find_take_profit


class FakeStructure:
    def __init__(self, above=(), below=()):
        self._above, self._below = above, below

    def resting_liquidity_above(self, price):
        return [SimpleNamespace(price=p, touches=1) for p in sorted(self._above) if p > price]

    def resting_liquidity_below(self, price):
        return [SimpleNamespace(price=p, touches=1) for p in sorted(self._below, reverse=True) if p < price]

    def unmitigated_blocks(self, direction):
        return []


STRUCTURES = {
    Timeframe.MIN_5: FakeStructure(above=[1.1010]),
    Timeframe.MIN_15: FakeStructure(above=[1.1030]),
    Timeframe.H_1: FakeStructure(above=[1.1080]),
    Timeframe.H_4: FakeStructure(above=[1.1200]),
    Timeframe.MN_1: FakeStructure(above=[1.1900]),
}


def test_poi_timeframe_policy_targets_the_zones_own_liquidity():
    params = RiskParams(tp_policy="liquidity")
    price, source = find_take_profit(Direction.LONG, 1.1000, STRUCTURES, Timeframe.MN_1, params, confirmation_tf=Timeframe.H_4)
    assert price == 1.1900 and source.startswith("1M")


def test_nearest_policy_takes_the_next_level_above_the_confirmation_timeframe():
    params = RiskParams(tp_policy="liquidity_nearest")
    price, source = find_take_profit(Direction.LONG, 1.1000, STRUCTURES, Timeframe.MN_1, params, confirmation_tf=Timeframe.MIN_5)
    assert price == 1.1030 and source.startswith("15m")      # the 5m swing itself is skipped as local liquidity


def test_nearest_policy_without_confirmation_falls_back_to_poi_timeframe_and_up():
    params = RiskParams(tp_policy="liquidity_nearest")
    price, source = find_take_profit(Direction.LONG, 1.1000, STRUCTURES, Timeframe.H_4, params)
    assert price == 1.1200 and source.startswith("4H")


def test_nearest_policy_short_side():
    structures = {Timeframe.MIN_15: FakeStructure(below=[1.0990]), Timeframe.H_1: FakeStructure(below=[1.0950]),
                  Timeframe.H_4: FakeStructure(below=[1.0800])}
    params = RiskParams(tp_policy="liquidity_nearest")
    price, source = find_take_profit(Direction.SHORT, 1.1000, structures, Timeframe.H_4, params, confirmation_tf=Timeframe.MIN_15)
    assert price == 1.0950 and source.startswith("1H")
