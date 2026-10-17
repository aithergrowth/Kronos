"""Option B's stakes (16 October, Max: "Oké dan doen we B"): a 4H zone at 1.25 times RISK on EURUSD, gold and NAS100, BTC
at a quarter, so a RISK of 1.75 or 2.25 keeps every single trade under the guard's 4 % day of the FTMO 2-Step."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader.cli import live_settings
from kronos_trader.core import Direction, Timeframe
from kronos_trader.execution import PaperBroker
from kronos_trader.execution.risk_guard import RiskGuard
from kronos_trader.strategy.risk import setup_risk, stepped_risk

CONFIG = Path(__file__).resolve().parents[2] / "config"
PROFILES = {"EURUSD": "dorus_live.yaml", "XAUUSD": "dorus_live_gold.yaml", "NAS100": "dorus_live_nas100.yaml",
            "BTCUSD": "dorus_live_btc.yaml"}
NOW = pd.Timestamp("2026-10-19 09:00")                  # a Monday morning: a fresh day, nothing closed yet


def _ftmo(symbol: str, risk: float):
    """The FTMO window's settings as start_ftmo.bat builds them: the profile, --risk-pct, --product ftmo_2step, 10k."""
    args = SimpleNamespace(config=str(CONFIG / PROFILES[symbol]), symbol=symbol, risk_pct=risk, product="ftmo_2step",
                           account_size=10_000.0, target_pct=10.0)
    return live_settings(args)[0]


def _stake(risk_params, zone=Timeframe.H_1, balance=10_000.0) -> float:
    return setup_risk(stepped_risk(risk_params, balance, 10_000.0), zone).risk_pct


def test_the_profiles_carry_option_b():
    for symbol in ("EURUSD", "XAUUSD", "NAS100"):
        risk = _ftmo(symbol, 1.75).risk
        assert risk.zone_risk_multiplier == {"4H": 1.25} and risk.stake_multiplier == 1.0
    btc = _ftmo("BTCUSD", 1.75).risk
    assert btc.stake_multiplier == 0.25 and not btc.zone_risk_multiplier


@pytest.mark.parametrize("risk, four_h, one_h, btc", [(1.75, 2.1875, 1.75, 0.4375), (2.25, 2.8125, 2.25, 0.5625)])
def test_a_trade_risks_risk_times_the_multipliers(risk, four_h, one_h, btc):
    for symbol in ("EURUSD", "XAUUSD", "NAS100"):
        r = _ftmo(symbol, risk).risk
        assert _stake(r, Timeframe.H_4) == pytest.approx(four_h) and _stake(r, Timeframe.H_1) == pytest.approx(one_h)
        assert _stake(r, Timeframe.H_4, balance=9_650.0) == pytest.approx(1.25)   # the ladder does not scale with RISK
    assert _stake(_ftmo("BTCUSD", risk).risk, Timeframe.H_4) == pytest.approx(btc)


def _account(settings):
    broker = PaperBroker(settings)
    for symbol, price in (("EURUSD", 1.1), ("XAUUSD", 4000.0), ("NAS100", 25_000.0), ("BTCUSD", 110_000.0)):
        broker.set_price(symbol, price)
    return broker, RiskGuard(settings.prop_firm, settings.account_size)


def _hold(broker, symbol: str, money: float) -> None:
    """An open position that loses ``money`` at its stop."""
    spec = broker.settings.symbol(symbol)
    price, distance = broker.current_price(symbol), 100 * spec.pip_size
    broker.place_market_order(symbol, Direction.LONG, money / (100 * spec.pip_value_per_lot), price - distance,
                              price + 3 * distance, money, distance, 4.0, price=price, ts=NOW - pd.Timedelta(hours=1),
                              price_is_fill=True)


def test_a_4h_trade_at_risk_2_25_fits_the_4_pct_day():
    s = _ftmo("XAUUSD", 2.25)
    assert s.prop_firm.daily_loss_limit_pct == 4.0 and s.prop_firm.max_drawdown_pct == 9.5
    broker, guard = _account(s)
    ok, why = guard.can_open(broker, NOW, "XAUUSD", new_risk=100.0 * _stake(s.risk, Timeframe.H_4))
    assert ok, why
    old = replace(s.risk, zone_risk_multiplier={"4H": 2.0})   # the old x2: a 4.5 % trade, refused (the profiles go first)
    ok, why = guard.can_open(broker, NOW, "XAUUSD", new_risk=100.0 * _stake(old, Timeframe.H_4))
    assert not ok and "4.50%" in why


def test_two_positions_open_at_risk_2_25():
    s = _ftmo("XAUUSD", 2.25)
    broker, guard = _account(s)
    _hold(broker, "XAUUSD", 281.25)                           # a 4H gold trade open
    ok, why = guard.can_open(broker, NOW, "NAS100", new_risk=225.0)          # and a full 1H trade: 5.06 %
    assert not ok and "5.06%" in why
    ok, why = guard.can_open(broker, NOW, "BTCUSD", new_risk=56.25)          # and a BTC trade: 3.38 %
    assert ok, why
    broker, guard = _account(s)
    _hold(broker, "EURUSD", 225.0)                            # two full 1H trades make 4.5 %: never together at 2.25
    ok, why = guard.can_open(broker, NOW, "XAUUSD", new_risk=225.0)
    assert not ok and "4.50%" in why


def test_two_positions_open_at_risk_1_75():
    s = _ftmo("EURUSD", 1.75)
    broker, guard = _account(s)
    _hold(broker, "XAUUSD", 218.75)                           # a 4H gold trade and a full 1H EURUSD trade: 3.94 %
    ok, why = guard.can_open(broker, NOW, "EURUSD", new_risk=175.0)
    assert ok, why
    _hold(broker, "EURUSD", 175.0)
    ok, why = guard.can_open(broker, NOW, "NAS100", new_risk=175.0)           # a third never: two open on the account
    assert not ok and "max 2 open" in why
