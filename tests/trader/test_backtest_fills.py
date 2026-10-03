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
