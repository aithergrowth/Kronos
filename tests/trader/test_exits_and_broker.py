import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Candle, Direction, Timeframe
from kronos_trader.execution import PaperBroker, RiskGuard
from kronos_trader.strategy import breakeven_reached, breakeven_trigger_r, r_multiple

T = Timeframe


def test_breakeven_rules():
    assert breakeven_trigger_r(T.MN_1) == 2.0 and breakeven_trigger_r(T.W_1) == 2.0
    for tf in (T.D_1, T.H_4, T.H_1):
        assert breakeven_trigger_r(tf) == 4.0
    assert r_multiple(Direction.LONG, 1.10, 0.005, 1.12) == pytest.approx(4.0)
    assert r_multiple(Direction.SHORT, 1.10, 0.005, 1.12) == pytest.approx(-4.0)
    assert breakeven_reached(Direction.LONG, 1.10, 0.005, 1.1201, 4.0)
    assert not breakeven_reached(Direction.LONG, 1.10, 0.005, 1.1199, 4.0)


def _candle(o, h, l, c, ts="2024-01-02 10:00"):
    return Candle(0, pd.Timestamp(ts), o, h, l, c)


def _long(broker):
    return broker.place_market_order("EURUSD", Direction.LONG, 1.96, 1.0950, 1.1200, 1000.0, 0.0051, 4.0,
                                     price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))


def test_paper_broker_fills_with_spread_and_hits_take_profit():
    broker = PaperBroker(Settings())
    pos = _long(broker)
    assert pos.entry == pytest.approx(1.10005)  # 1 pip spread -> half a pip worse
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.1250, 1.0990, 1.1240))
    assert len(closed) == 1 and closed[0].reason == "take_profit"
    assert closed[0].pnl == pytest.approx((1.1200 - 1.10005) / 0.0001 * 10 * 1.96)
    assert broker.balance() == pytest.approx(100_000 + closed[0].pnl)


def test_paper_broker_stop_wins_when_both_hit():
    broker = PaperBroker(Settings())
    _long(broker)
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.1300, 1.0900, 1.1000))
    assert closed[0].reason == "stop" and closed[0].exit == 1.0950 and closed[0].r == pytest.approx(-1.0, abs=0.02)


def test_paper_broker_moves_to_breakeven_after_4r():
    broker = PaperBroker(Settings())
    pos = broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0950, 1.1300, 1000.0, 0.0051, 4.0,
                                    price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))
    assert broker.on_candle("EURUSD", _candle(1.1000, 1.1210, 1.0999, 1.1205)) == []
    assert pos.breakeven_done and pos.stop == pytest.approx(pos.entry)
    closed = broker.on_candle("EURUSD", _candle(1.1205, 1.1210, 1.0999, 1.1000, "2024-01-02 11:00"))
    assert closed[0].reason == "breakeven" and closed[0].pnl == pytest.approx(0.0)


def test_risk_guard_limits():
    settings = Settings()
    broker = PaperBroker(settings)
    guard = RiskGuard(settings.prop_firm, settings.account_size)
    ts = pd.Timestamp("2024-01-02 09:00")
    assert guard.can_open(broker, ts)[0]
    _long(broker)
    ok, reason = guard.can_open(broker, ts)
    assert not ok and "open trade" in reason
    broker.close_position(broker.open_positions()[0].id, "manual", 1.1000, ts)
    broker._balance = 95_500.0
    ok, reason = guard.can_open(broker, ts)
    assert not ok and "daily loss" in reason
    broker._balance = 91_500.0
    ok, reason = guard.can_open(broker, ts + pd.Timedelta(1, unit="D"))
    assert not ok and "drawdown" in reason


def test_bid_quote_basis_fills_longs_at_the_full_spread_and_checks_stops_on_the_bid():
    broker = PaperBroker(Settings(), quote_basis="bid")
    pos = _long(broker)
    assert pos.entry == pytest.approx(1.1001)          # ask = bid + the full 1-pip spread
    # bid low 1.09505 is above the stop: with the candles as bid quotes nothing is subtracted, so no stop
    assert broker.on_candle("EURUSD", _candle(1.1000, 1.1010, 1.09505, 1.1005)) == []
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.1010, 1.0950, 1.1005))
    assert len(closed) == 1 and closed[0].reason == "stop" and closed[0].exit == pytest.approx(1.0950)
    with pytest.raises(ValueError):
        PaperBroker(Settings(), quote_basis="ask")


def test_short_stop_on_bid_basis_uses_the_ask():
    broker = PaperBroker(Settings(), quote_basis="bid")
    pos = broker.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.1050, 1.0900, 1000.0, 0.0051, 4.0,
                                    price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))
    assert pos.entry == pytest.approx(1.1000)          # sold on the bid itself
    assert broker.on_candle("EURUSD", _candle(1.1000, 1.10485, 1.0990, 1.1000)) == []      # ask high 1.10495 < stop
    closed = broker.on_candle("EURUSD", _candle(1.1000, 1.10495, 1.0990, 1.1000))          # ask high 1.10505 >= stop
    assert len(closed) == 1 and closed[0].reason == "stop"


def test_stop_fills_at_the_open_when_a_candle_gaps_through_it():
    broker = PaperBroker(Settings(), use_spread=False)
    _long(broker)                                                     # stop 1.0950
    closed = broker.on_candle("EURUSD", _candle(1.0900, 1.0920, 1.0880, 1.0910, ts="2024-01-07 22:00"))
    assert len(closed) == 1 and closed[0].reason == "stop" and closed[0].exit == pytest.approx(1.0900)
    assert closed[0].r < -1.0


def test_shorts_are_valued_and_market_closed_on_the_ask():
    broker = PaperBroker(Settings(), quote_basis="bid")
    broker.place_market_order("EURUSD", Direction.SHORT, 1.0, 1.1050, 1.0900, 1000.0, 0.0051, 4.0,
                              price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))
    broker.on_candle("EURUSD", _candle(1.1000, 1.1005, 1.0940, 1.0950))
    assert broker.equity() == pytest.approx(100_000 + (1.1000 - 1.0951) / 0.0001 * 10)      # closed on the ask: 49 pips, not 50
    closed = broker.close_position(broker.open_positions()[0].id, "end_of_data", 1.0950, market=True)
    assert closed.exit == pytest.approx(1.0951)
    long_broker = PaperBroker(Settings(), quote_basis="bid")
    long_broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0950, 1.1200, 1000.0, 0.0051, 4.0,
                                   price=1.1000, ts=pd.Timestamp("2024-01-02 09:00"))
    long_broker.on_candle("EURUSD", _candle(1.1000, 1.1060, 1.0990, 1.1050))
    assert long_broker.equity() == pytest.approx(100_000 + (1.1050 - 1.1001) / 0.0001 * 10)   # long closes on the bid itself



def _partial_settings(k=1.0, fraction=1 / 3):
    s = Settings()
    s.exits.partial_at_r, s.exits.partial_fraction = k, fraction
    return s


def test_partial_at_1r_then_break_even():
    from kronos_trader.core import Candle
    broker = PaperBroker(_partial_settings(), use_spread=False)
    pos = broker.place_market_order("EURUSD", Direction.LONG, 3.0, 1.0990, 1.1030, 300.0, 0.0010, 4.0, price=1.1000,
                                    ts=pd.Timestamp("2026-10-01 09:00"))
    broker.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-01 09:05"), 1.1000, 1.1012, 1.0998, 1.1008))   # +1R reached
    assert pos.partial_done and pos.lots == pytest.approx(2.0) and pos.stop == pytest.approx(1.1000)
    closed = broker.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-01 09:10"), 1.1008, 1.1009, 1.0995, 1.0996))
    assert closed[0].reason == "breakeven" and closed[0].r == pytest.approx(1 / 3) and closed[0].lots == pytest.approx(3.0)
    assert closed[0].pnl == pytest.approx(100.0) and broker.balance() == pytest.approx(100_000 + 100.0)


def test_partial_then_target_and_no_partial_when_the_target_comes_first():
    from kronos_trader.core import Candle
    broker = PaperBroker(_partial_settings(), use_spread=False)
    broker.place_market_order("EURUSD", Direction.SHORT, 3.0, 1.1010, 1.0970, 300.0, 0.0010, 4.0, price=1.1000,
                              ts=pd.Timestamp("2026-10-01 09:00"))
    closed = broker.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-01 09:05"), 1.1000, 1.1002, 1.0965, 1.0968))
    assert closed[0].reason == "take_profit" and closed[0].r == pytest.approx(1 / 3 + 2 / 3 * 3)
    near = PaperBroker(_partial_settings(k=1.0), use_spread=False)
    p2 = near.place_market_order("EURUSD", Direction.LONG, 3.0, 1.0990, 1.1008, 300.0, 0.0010, 4.0, price=1.1000,
                                 ts=pd.Timestamp("2026-10-01 09:00"))                  # target at 0.8R: no partial
    closed = near.on_candle("EURUSD", Candle(0, pd.Timestamp("2026-10-01 09:05"), 1.1000, 1.1012, 1.0998, 1.1008))
    assert closed[0].reason == "take_profit" and closed[0].r == pytest.approx(0.8) and not p2.partial_done
