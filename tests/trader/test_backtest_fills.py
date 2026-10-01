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
    assert trade.meta["rr_at_fill"] == pytest.approx(round(0.06 / 0.0152, 2))
    # sized on the executable entry: 1 % of 100,000 over 152 pips -> 0.65 lots, not the 1.92 planned at 1.1000
    assert trade.lots == pytest.approx(0.65) and trade.meta["lots_planned"] == pytest.approx(1.92)
    assert trade.risk_amount == pytest.approx(1000.0)
    assert abs(trade.pnl) == pytest.approx(abs(trade.r) * 1000.0, rel=0.05)      # R is measured on the real risk


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
