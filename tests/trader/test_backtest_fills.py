"""Backtester execution: market fills at the current price with the live re-check, bounded flattening."""
import pandas as pd
import pytest

from kronos_trader.backtest.runner import Backtester
from kronos_trader.config import Settings
from kronos_trader.core import (Analysis, Bias, BiasDecision, CandleSeries, Confirmation, ConfirmationType, Direction, Signal,
                                SignalStatus, Timeframe, TradeMode, TradeSetup)
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy import analyze_structure, map_pois

T = Timeframe


class StaleEngine:
    """Signals once, with a setup whose confirmation close (1.1000) is older than the current candle."""

    def __init__(self, setup):
        self.setup = setup
        self.calls = 0

    def analyze(self, symbol, views, equity=None, now=None, max_confirmation_age=0, compute_forecasts=False):
        self.calls += 1
        decision = BiasDecision(Bias.BULLISH, TradeMode.FULL, (T.MN_1, T.W_1, T.D_1), (), (T.H_4, T.H_1), (T.MN_1, T.W_1, T.D_1), "test")
        signal = Signal(now, SignalStatus.VALID, self.setup, None, []) if self.calls == 1 else None
        return Analysis(symbol, now, 1.11, {}, decision, [], signal)


def _setup(scenario, take_profit):
    poi = map_pois(analyze_structure(scenario), current_price=101.0)[0]
    conf = Confirmation(ConfirmationType.BOS, T.MIN_15, 9, pd.Timestamp("2024-01-02 08:45"), Bias.BULLISH, 1.1050, 1.0950, 1.1000)
    return TradeSetup("EURUSD", Direction.LONG, poi, conf, 1.1000, 1.0949, take_profit, 0.0052, 0.02, 3.85, 1.92, 1000.0, 4.0, "1H liquidity")


def _data(closes):
    rows = [(c, c + 0.0005, c - 0.0005, c) for c in closes]
    series = CandleSeries.from_records(rows, T.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    return MultiTimeframeData({T.MIN_15: series})


def test_fill_is_at_the_current_price_not_the_stale_confirmation_close(scenario):
    s = Settings()
    bt = Backtester(s, _data([1.1100, 1.1150, 1.1120]), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(_setup(scenario, 1.1700)))
    result = bt.run()
    assert len(result.trades) == 1
    trade = result.trades[0]
    assert trade.entry == pytest.approx(1.1100 + 0.00005)       # the candle that just closed, plus half the spread
    assert trade.meta["entry_planned"] == pytest.approx(1.1000)
    assert trade.meta["rr_at_fill"] == pytest.approx((1.17 - 1.11005) / (1.11005 - 1.0949), rel=1e-4)   # on the real fill
    # sized on the executable entry (the ask 1.11005): 1 % of 100,000 over 151.5 + 1 pips -> 0.65 lots, not 1.92
    assert trade.lots == pytest.approx(0.65) and trade.meta["lots_planned"] == pytest.approx(1.92)
    assert trade.meta["risk_budget"] == pytest.approx(1000.0)
    assert trade.risk_amount == pytest.approx(151.5 * 10 * 0.65)              # the cash actually lost at the stop
    assert trade.pnl == pytest.approx(trade.r * trade.risk_amount, rel=1e-6)   # R measured on that risk


def test_signal_is_skipped_when_the_move_leaves_too_little_reward(scenario):
    s = Settings()
    bt = Backtester(s, _data([1.1100, 1.1150, 1.1120]), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(_setup(scenario, 1.1200)))
    result = bt.run()
    assert result.trades == [] and result.rejected_by_guard == 1
    assert "price moved: R:R below minimum" in result.guard_reasons


def test_bounded_run_flattens_at_its_own_last_candle(scenario):
    s = Settings()
    bt = Backtester(s, _data([1.1100, 1.1150, 1.1120, 1.2000]), "EURUSD", step_tf=T.MIN_15,
                    engine=StaleEngine(_setup(scenario, 1.1700)), end="2024-01-02 09:30")
    result = bt.run()
    assert len(result.trades) == 1 and result.trades[0].reason == "end_of_data"
    assert result.trades[0].exit == pytest.approx(1.1120 - 0.00005)   # its own last close on the bid, not the 1.2000 after --end


def test_stop_too_wide_at_the_moved_price_is_skipped(scenario):
    s = Settings()
    s.account_size = 1_000.0                          # 1 % = 10: at 152 pips that is under the 0.01-lot minimum
    bt = Backtester(s, _data([1.1100, 1.1150, 1.1120]), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(_setup(scenario, 1.1700)))
    result = bt.run()
    assert result.trades == [] and "price moved: stop too wide for the minimum lot" in result.guard_reasons


def test_gold_is_sized_and_judged_on_the_ask(scenario):
    """Astra's probe: bid 2500.00, ask 2500.20, stop 2499.00, target 2501.66 passes 1.5 on the bid, not on the ask."""
    from kronos_trader.config import RiskParams
    from kronos_trader.execution import PaperBroker
    from kronos_trader.strategy.risk import resize_at
    s = Settings()
    broker = PaperBroker(s, quote_basis="bid")
    spec = s.symbol("XAUUSD")
    fill = broker.fill_price("XAUUSD", Direction.LONG, 2500.0)
    assert fill == pytest.approx(2500.2)
    params = RiskParams(min_rr=1.5, sl_offset_pips=0.0)
    _, _, _, rr_bid, _ = resize_at(2500.0, 2499.0, 2501.66, 100_000, spec, params)
    lots, budget, _, rr_ask, _ = resize_at(fill, 2499.0, 2501.66, 100_000, spec, params)
    assert rr_bid > 1.5 > rr_ask                                       # the old sizing let it through
    cash_at_stop = abs(broker.pnl_for("XAUUSD", Direction.LONG, fill, 2499.0, lots))
    assert cash_at_stop <= budget                                      # never more than the 1 % budget


def _bars(rows):
    """(open, high, low, close) 15m candles from 09:00."""
    series = CandleSeries.from_records(rows, T.MIN_15, start="2024-01-02 09:00", symbol="EURUSD")
    return MultiTimeframeData({T.MIN_15: series})


def _limit_settings(fraction=0.25, minutes=60):
    s = Settings()
    s.risk.limit_entry_fraction, s.risk.limit_entry_minutes = fraction, minutes
    return s


def test_a_limit_entry_fills_part_way_back_toward_the_stop_and_sizes_on_the_smaller_stop(scenario):
    """risk.limit_entry_fraction 0.25: after the signal at the 1.1000 candle a buy limit rests a quarter of the way back
    to the stop; it fills when the ask reaches it, the size follows the smaller stop, the target stays."""
    setup = _setup(scenario, 1.1300)
    rows = [(1.1000, 1.1005, 1.0995, 1.1000), (1.0990, 1.0992, 1.0960, 1.0970), (1.0970, 1.1310, 1.0965, 1.1300)]
    result = Backtester(_limit_settings(), _bars(rows), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(setup)).run()
    assert len(result.trades) == 1
    t = result.trades[0]
    signal_ask = 1.1000 + 0.00005
    limit = round(signal_ask - 0.25 * (signal_ask - 1.0949), 5)
    assert t.entry == pytest.approx(limit) and t.reason == "take_profit" and t.meta["entry_mode"] == "limit 0.25"
    assert t.r == pytest.approx((1.1300 - limit) / (limit - 1.0949), rel=1e-3)        # R on the smaller stop
    assert t.r > (1.1300 - signal_ask) / (signal_ask - 1.0949)                          # more than the market entry's R


def test_a_limit_entry_is_missed_when_the_target_trades_first_or_it_expires(scenario):
    setup = _setup(scenario, 1.1200)                                                    # R:R 3.9 at the signal, over the 3.0 floor
    first = [(1.1000, 1.1005, 1.0995, 1.1000), (1.1000, 1.1210, 1.0999, 1.1200), (1.1200, 1.1205, 1.0900, 1.0950)]
    r1 = Backtester(_limit_settings(), _bars(first), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(setup)).run()
    assert r1.trades == [] and r1.guard_reasons.get("limit entry: the target traded first") == 1
    quiet = [(1.1000, 1.1005, 1.0995, 1.1000)] + [(1.1000, 1.1004, 1.0996, 1.1000)] * 6
    r2 = Backtester(_limit_settings(minutes=30), _bars(quiet), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(setup)).run()
    assert r2.trades == [] and r2.guard_reasons.get("limit entry: expired unfilled") == 1


def test_a_limit_fill_whose_candle_also_reaches_the_stop_is_a_loss(scenario):
    setup = _setup(scenario, 1.1300)
    rows = [(1.1000, 1.1005, 1.0995, 1.1000), (1.0990, 1.0992, 1.0940, 1.0945), (1.0945, 1.1310, 1.0940, 1.1300)]
    result = Backtester(_limit_settings(), _bars(rows), "EURUSD", step_tf=T.MIN_15, engine=StaleEngine(setup)).run()
    assert len(result.trades) == 1 and result.trades[0].reason == "stop" and result.trades[0].r == pytest.approx(-1.0, abs=0.02)
