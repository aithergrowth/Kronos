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
    assert broker.on_candle("EURUSD", _candle(1.1000, 1.1210, 1.1010, 1.1205)) == []   # reaches 4R, stays above the entry
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


def test_backtest_commission_comes_off_pnl_and_r():
    """``commission_per_lot`` (forex, a lot round turn) and ``commission_pct`` (crypto, of the notional) come off the
    closed trade's P&L and R; none by default."""
    s = Settings()
    s.symbol("EURUSD").commission_per_lot = 3.0
    broker = PaperBroker(s, use_spread=False)
    t0 = pd.Timestamp("2026-10-01 09:00")
    broker.place_market_order("EURUSD", Direction.LONG, 2.0, 1.0900, 1.1200, 200.0, 0.01, 4.0, price=1.1000, ts=t0)
    trade = broker.close_position(broker.open_positions()[0].id, "manual", 1.1010, t0)
    assert trade.pnl == pytest.approx(10 * 10 * 2 - 6.0) and trade.r == pytest.approx(0.1 - 6.0 / 200.0)
    s2 = Settings()
    s2.symbol("BTCUSD").commission_pct = 0.065
    btc = PaperBroker(s2, use_spread=False)
    btc.place_market_order("BTCUSD", Direction.SHORT, 0.5, 100_500.0, 99_000.0, 250.0, 500.0, 4.0, price=100_000.0, ts=t0)
    trade = btc.close_position(btc.open_positions()[0].id, "manual", 99_500.0, t0)
    assert trade.pnl == pytest.approx(250.0 - 0.00065 * 100_000.0 * 0.5)                  # 32.5 of commission
    plain = PaperBroker(Settings(), use_spread=False)
    plain.place_market_order("EURUSD", Direction.LONG, 2.0, 1.0900, 1.1200, 200.0, 0.01, 4.0, price=1.1000, ts=t0)
    assert plain.close_position(plain.open_positions()[0].id, "manual", 1.1010, t0).pnl == pytest.approx(200.0)


def test_a_candle_that_reaches_break_even_and_trades_back_closes_at_break_even():
    """The trigger candle also traded back through the entry: the order inside the candle is unknown, so the backtest
    takes the break-even stop instead of keeping the trade for a later target."""
    s = Settings()
    broker = PaperBroker(s, use_spread=False)
    t0 = pd.Timestamp("2026-10-01 09:00")
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.1100, 100.0, 0.0010, 4.0, price=1.1000, ts=t0)
    closed = broker.on_candle("EURUSD", Candle(0, t0, 1.1000, 1.1045, 1.0995, 1.1001))   # +4.5R high, back under the entry
    assert len(closed) == 1 and closed[0].reason == "breakeven" and closed[0].r == pytest.approx(0.0)
    broker.place_market_order("EURUSD", Direction.LONG, 1.0, 1.0990, 1.1100, 100.0, 0.0010, 4.0, price=1.1000, ts=t0)
    assert broker.on_candle("EURUSD", Candle(0, t0, 1.1000, 1.1045, 1.1002, 1.1040)) == []    # stays above: kept at BE
    assert broker.open_positions()[0].breakeven_done


def test_day_close_cutoff_is_the_next_clock_in_the_session_timezone():
    """``exits.day_close``: a position closes at the first "HH:MM" (session timezone) at or after it opened."""
    from kronos_trader.strategy.exits import day_close_cutoff_after
    # 8 October 2026, Amsterdam = UTC+2: a trade opened 14:00 UTC (16:00 local) closes at 22:50 local = 20:50 UTC
    assert day_close_cutoff_after(pd.Timestamp("2026-10-08 14:00"), "22:50") == pd.Timestamp("2026-10-08 20:50")
    # opened after the cutoff (21:30 UTC = 23:30 local): the next day's 22:50
    assert day_close_cutoff_after(pd.Timestamp("2026-10-08 21:30"), "22:50") == pd.Timestamp("2026-10-09 20:50")
    # exactly at the cutoff: closes now
    assert day_close_cutoff_after(pd.Timestamp("2026-10-08 20:50"), "22:50") == pd.Timestamp("2026-10-08 20:50")
    # in winter (UTC+1) the same clock is 21:50 UTC
    assert day_close_cutoff_after(pd.Timestamp("2026-12-01 10:00"), "22:50") == pd.Timestamp("2026-12-01 21:50")


def test_the_paper_broker_closes_a_position_before_the_daily_break():
    from kronos_trader.config import Settings
    from kronos_trader.core import Direction
    from kronos_trader.execution import PaperBroker
    settings = Settings(); settings.exits.day_close = "22:50"
    broker = PaperBroker(settings)
    broker.set_price("NAS100", 20000.0)
    pos = broker.place_market_order("NAS100", Direction.LONG, 1.0, 19900.0, 20300.0, 100.0, 100.0, 4.0, meta={},
                                    price=20000.0, ts=pd.Timestamp("2026-10-08 14:00"), price_is_fill=True)
    from kronos_trader.core import CandleSeries
    quiet = CandleSeries.from_records([(20010.0, 20020.0, 20000.0, 20015.0)], T.MIN_5, start="2026-10-08 20:40", symbol="NAS100")
    assert broker.on_candle("NAS100", quiet[0]) == []                                   # opens 22:40 local: still open
    late = CandleSeries.from_records([(20015.0, 20025.0, 20005.0, 20020.0)], T.MIN_5, start="2026-10-08 20:50", symbol="NAS100")
    closed = broker.on_candle("NAS100", late[0])                                         # opens 22:50 local (the cutoff): closed at its close
    assert len(closed) == 1 and closed[0].reason == "day_close" and broker.open_positions() == []
