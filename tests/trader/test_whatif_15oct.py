"""The "Trade als" line of the morning check (15 October, Max: "maar ondertussen zegt die geen trade"): the engine's own
bias code asked what would have to close where for the decision to allow a trade."""
import pandas as pd

from kronos_trader.config import Settings
from kronos_trader.core import Bias, CandleSeries, Timeframe as T
from kronos_trader.core.types import Analysis, BiasDecision, TimeframeBias, TradeMode
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from kronos_trader.strategy import analyze_structure, combine_biases, timeframe_bias
from kronos_trader.strategy.whatif import Turn, turn_text, turning_closes
from tests.trader.conftest import SWEEP_BREAK_ROWS
from tests.trader.test_live import FakeEngine, setup  # noqa: F401  (the setup fixture lives there)

# the conftest's bullish hour (a sweep of 100, a break through 110, a gap with its P at 105), three quiet hours on top,
# and a forming candle; the hour reads bullish while the month, week and day read bearish
ROWS = list(SWEEP_BREAK_ROWS) + [(112.5, 112.9, 111.8, 112.2), (112.2, 112.7, 111.6, 112.0), (112.0, 112.6, 111.5, 112.1)]
FORMING = (112.1, 112.4, 111.9, 112.2)
START = "2026-09-30 11:00"
NOW = pd.Timestamp("2026-10-01 06:45")            # 08:45 Amsterdam: the hour that opened at 06:00 is forming


def _hourly(extra=()):
    return CandleSeries.from_records(ROWS + [FORMING] + list(extra), T.H_1, start=START, symbol="EURUSD")


def _settings():
    s = Settings()
    s.session.windows = (("09:00", "11:00"), ("13:00", "17:00"))
    s.bias.required_aligned = (T.H_1,)
    return s


BIASES = {T.MN_1: Bias.BEARISH, T.W_1: Bias.BEARISH, T.D_1: Bias.BEARISH, T.H_4: Bias.NEUTRAL, T.H_1: Bias.BULLISH}


def _closed_with(series, close, wick=None):
    """The forming candle closed at ``close`` (its wick through ``wick`` when given), as the engine would then read it."""
    closed = series.closed_as_of(NOW)
    o, h, l, _ = FORMING
    row = pd.DataFrame([[closed.last_timestamp + pd.Timedelta(hours=1), o, max(h, close, wick or close),
                         min(l, close), close, 0.0]], columns=["timestamp", "open", "high", "low", "close", "volume"])
    return CandleSeries(pd.concat([closed.df, row], ignore_index=True), T.H_1, "EURUSD", validate=False)


def test_the_hour_turns_on_a_sweep_of_its_high_and_a_close_under_its_p():
    s = _settings()
    assert timeframe_bias(analyze_structure(_hourly().closed_as_of(NOW), s.structure), s.bias).bias is Bias.BULLISH
    assert not combine_biases(BIASES, s.bias).tradable
    turn = turning_closes({T.H_1: _hourly()}, BIASES, s, NOW, 112.2)[Bias.BEARISH]
    assert isinstance(turn, Turn) and turn.timeframes == (T.H_1,) and turn.direction is Bias.BEARISH
    assert turn.sweep is not None and 113.0 <= turn.sweep < 113.1            # the swing high of candle 15
    assert turn.close < 105.0 + 0.05                                         # the close through the gap's P
    # the engine itself agrees: that candle turns the hour and the decision allows a short ...
    hour = timeframe_bias(analyze_structure(_closed_with(_hourly(), turn.close, turn.sweep * 1.000001), s.structure), s.bias)
    assert hour.bias is Bias.BEARISH and combine_biases({**BIASES, T.H_1: hour.bias}, s.bias).direction is Bias.BEARISH
    # ... and a close a little nearer to the price does not
    nearer = turn.close + 0.1
    hour = timeframe_bias(analyze_structure(_closed_with(_hourly(), nearer, turn.sweep * 1.000001), s.structure), s.bias)
    assert hour.bias is not Bias.BEARISH
    text = turn_text(turn, lambda p: f"{p:.2f}", "1H supply 110.00–113.00 (prijs erin)")
    assert text.startswith("de 1H veegt 113.0") and "sluit onder 10" in text and text.endswith("→ short uit de 1H supply 110.00–113.00 (prijs erin)")


def test_a_weekly_veto_is_named_instead_of_a_level():
    s = _settings()
    s.bias.no_trade_against = (T.W_1,)
    biases = {**BIASES, T.W_1: Bias.BULLISH}
    result = turning_closes({T.H_1: _hourly()}, biases, s, NOW, 112.2, directions=(Bias.BEARISH,), full=(Bias.BEARISH,))
    assert isinstance(result[Bias.BEARISH], BiasDecision) and "1W against" in result[Bias.BEARISH].reason


def test_the_answer_reads_no_candle_after_the_forming_one_and_a_spent_budget_answers_nothing():
    s = _settings()
    plain = turning_closes({T.H_1: _hourly()}, BIASES, s, NOW, 112.2)
    later = turning_closes({T.H_1: _hourly(extra=[(112.2, 130.0, 90.0, 95.0)])}, BIASES, s, NOW, 112.2)
    assert plain[Bias.BEARISH] == later[Bias.BEARISH]
    assert turning_closes({T.H_1: _hourly()}, BIASES, s, NOW, 112.2, budget_s=0.0) == {}


class NoTradeEngine(FakeEngine):
    """A decision that refuses: the month, week and day bearish, the hour bullish."""

    def analyze(self, symbol, views, equity=None, now=None, max_confirmation_age=0, compute_forecasts=False):
        decision = combine_biases(BIASES, _settings().bias)
        tbs = {tf: TimeframeBias(tf, b, b, b, []) for tf, b in BIASES.items()}
        return Analysis(symbol, now, self.price, tbs, decision, self.pois, None, rejections=[])


def test_the_morning_check_says_what_would_turn_it_and_survives_a_failure(setup, monkeypatch):
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 112.2)
    views = {T.H_1: _hourly()}
    sent = TelegramNotifier(dry_run=True)
    runner = LiveRunner(_settings(), "EURUSD", lambda: views, broker=broker, notifier=sent,
                        engine=NoTradeEngine(setup, price=112.2, signal_on_first_call=False), clock=lambda: NOW)
    runner.step(NOW)
    morning = [m for m in sent.sent if m.startswith("☀️")]
    assert len(morning) == 1 and "❌ geen short: wacht tot de 1H meedraait" in morning[0]
    assert "🎯 Trade als: de 1H veegt 113.0" in morning[0] and "→ short" in morning[0]

    import kronos_trader.strategy.whatif as whatif

    def boom(*args, **kwargs):
        raise RuntimeError("a bug in the what-if")
    monkeypatch.setattr(whatif, "turning_closes", boom)
    sent2 = TelegramNotifier(dry_run=True)
    runner2 = LiveRunner(_settings(), "EURUSD", lambda: views, broker=broker, notifier=sent2,
                         engine=NoTradeEngine(setup, price=112.2, signal_on_first_call=False), clock=lambda: NOW)
    runner2.step(NOW)
    morning = [m for m in sent2.sent if m.startswith("☀️")]
    assert len(morning) == 1 and "🕘 Vensters" in morning[0] and "Trade als" not in morning[0]
