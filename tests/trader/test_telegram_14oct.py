"""The Telegram upgrade of 14 October (Max: "ik wil alles zien wat de bot ziet"): near misses, approach notices, the
briefing extras and the midday check, the chart context (previous day, shaded windows)."""
import pandas as pd

from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Timeframe as T
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from kronos_trader.notify.formatting import plain_near_miss
from tests.trader.test_live import FakeEngine, NOW, setup  # noqa: F401  (the setup fixture lives there)

T0 = pd.Timestamp("2026-10-01 08:00")          # 10:00 Amsterdam: inside the morning window


def _views(hourly=False, daily=False):
    views = {T.MIN_15: CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, T.MIN_15, start="2026-10-01 07:15", symbol="EURUSD")}
    if hourly:                                            # a range of 1.0 a candle: ATR14 is 1.0
        views[T.H_1] = CandleSeries.from_records([(100.0, 100.6, 99.6, 100.2)] * 30, T.H_1, start="2026-09-30 02:00", symbol="EURUSD")
    if daily:
        views[T.D_1] = CandleSeries.from_records([(100, 102, 98, 101)] * 3, T.D_1, start="2026-09-28", symbol="EURUSD")
    return views


def _settings():
    s = Settings()
    s.session.windows = (("09:00", "11:00"), ("13:00", "17:00"))
    return s


def test_plain_near_miss_speaks_dutch_and_stays_silent_while_waiting():
    assert plain_near_miss("R:R 0.70 below minimum 1.0 (target 1H previous high 1.10500)") == \
        "shift gezien, maar R:R 1:0.7 onder het minimum 1:1.0 (doel: 1H previous high 1.10500)"
    assert plain_near_miss("visit #2 - only the first return is traded").startswith("geen trade: dit is bezoek #2")
    assert plain_near_miss("entry 1.1 lies 70% of the zone's height inside it (max 50%): no room for the stop").startswith("shift gezien, maar de instap ligt te diep")
    assert plain_near_miss("touched at 2026-10-01 08:00, waiting for confirmation on 5m") is None
    assert plain_near_miss("touched 30 h after it formed (max 24 h): a spent zone") is None
    assert plain_near_miss("zone 95 1H candles old (max 72)") is None                       # the engine's business, not news
    assert plain_near_miss("entry 1.1 lies 70% of the zone's height inside it (max 50%): no room for the stop; "
                           "R:R 0.70 below minimum 1.0 (target x)") == \
        "shift gezien, maar de instap ligt te diep in de zone (70% van de hoogte, max 50%); R:R 1:0.7 onder het minimum 1:1.0 (doel: x)"


def test_a_refused_shift_in_a_zone_in_play_is_said_once_per_four_hours(setup):
    notifier = TelegramNotifier(dry_run=True)
    engine = FakeEngine(setup, pois=[setup.poi], price=101.0, signal_on_first_call=False)      # price inside the zone
    engine.rejections = [f"{setup.poi.describe()}: R:R 0.70 below minimum 1.0 (target 1H previous high 1.10500)"]
    views = _views()
    runner = LiveRunner(_settings(), "EURUSD", lambda: views, notifier=notifier, engine=engine, clock=lambda: NOW)
    runner.step(T0)
    engine.rejections = [f"{setup.poi.describe()}: R:R 0.68 below minimum 1.0 (target 1H previous high 1.10400)"]   # a new number
    runner.step(T0 + pd.Timedelta(minutes=5))
    misses = [m for m in notifier.sent if "shift gezien" in m]
    assert len(misses) == 1 and "R:R 1:0.7" in misses[0] and "shift gezien" in misses[0] and "1H demand" in misses[0]
    runner.step(T0 + pd.Timedelta(hours=5))                                                    # 15:00: four hours on, said again
    assert len([m for m in notifier.sent if "shift gezien" in m]) == 2
    engine.rejections = [f"{setup.poi.describe()}: touched at 08:00, waiting for confirmation on 5m"]
    runner.step(T0 + pd.Timedelta(hours=5, minutes=5))
    assert len([m for m in notifier.sent if "shift gezien" in m]) == 2                          # waiting is no near miss
    engine.rejections = [f"{setup.poi.describe()}: R:R 0.70 below minimum 1.0 (target 1H previous high 1.10500)"]
    runner.step(pd.Timestamp("2026-10-01 20:00"))                                              # 22:00: outside the windows
    assert len([m for m in notifier.sent if "shift gezien" in m]) == 2


def test_price_near_a_zone_gets_one_approach_notice_a_day(setup):
    notifier = TelegramNotifier(dry_run=True)
    poi = setup.poi
    engine = FakeEngine(setup, pois=[poi], price=poi.high + 0.3, signal_on_first_call=False)   # 0.3 above a zone, ATR14 1.0
    views = _views(hourly=True)
    runner = LiveRunner(_settings(), "EURUSD", lambda: views, notifier=notifier, engine=engine, clock=lambda: NOW)
    runner.step(T0)
    runner.step(T0 + pd.Timedelta(minutes=5))
    near = [m for m in notifier.sent if m.startswith("🔎")]
    assert len(near) == 1 and "nadert de" in near[0] and "1H demand" in near[0] and "balance shift" in near[0]
    engine.price = poi.high + 3.0                                                               # far away: nothing
    runner.step(T0 + pd.Timedelta(minutes=10))
    assert len([m for m in notifier.sent if m.startswith("🔎")]) == 1
    engine.price = poi.high + 0.3
    runner.step(pd.Timestamp("2026-10-02 08:00"))                                              # the next day: again
    assert len([m for m in notifier.sent if m.startswith("🔎")]) == 2


def test_the_briefing_carries_the_stake_the_room_and_what_a_trade_needs_and_the_midday_check_comes_once(setup):
    notifier = TelegramNotifier(dry_run=True)
    broker = PaperBroker(Settings())
    broker.set_price("EURUSD", 1.1)
    engine = FakeEngine(setup, pois=[setup.poi], price=setup.poi.high + 0.3, signal_on_first_call=False)
    views = _views(hourly=True)
    runner = LiveRunner(_settings(), "EURUSD", lambda: views, broker=broker, notifier=notifier, engine=engine, clock=lambda: NOW)
    runner.step(pd.Timestamp("2026-10-01 06:45"))                                              # 08:45: the morning check
    morning = [m for m in notifier.sent if m.startswith("☀️")]
    assert len(morning) == 1
    assert "💰 Inzet: 1% = 1,000" in morning[0] and "🛡 Ruimte: vandaag nog" in morning[0]
    assert "🕘 Vensters: 09:00–11:00 en 13:00–17:00" in morning[0]
    assert "🎯 Voor een trade: de prijs naar de 1H-zone" in morning[0] and "balance shift op de" in morning[0]
    runner.step(pd.Timestamp("2026-10-01 10:50"))                                              # 12:50: not yet
    assert not any(m.startswith("🕐") for m in notifier.sent)
    runner.step(pd.Timestamp("2026-10-01 10:56"))                                              # 12:56: the midday check
    runner.step(pd.Timestamp("2026-10-01 11:30"))
    midday = [m for m in notifier.sent if m.startswith("🕐")]
    assert len(midday) == 1 and "middagcheck" in midday[0] and "💰 Inzet" in midday[0]
    # a window started after 12:55 sends the morning check and not the midday one on top of it
    late = TelegramNotifier(dry_run=True)
    runner2 = LiveRunner(_settings(), "EURUSD", lambda: views, broker=broker, notifier=late, engine=engine, clock=lambda: NOW)
    runner2.step(pd.Timestamp("2026-10-01 12:10"))                                             # 14:10 Amsterdam
    assert sum(m.startswith("☀️") for m in late.sent) == 1 and not any(m.startswith("🕐") for m in late.sent)


def test_chart_context_gives_the_previous_closed_day_and_the_window_spans(setup):
    views = _views(hourly=True, daily=True)
    rows = [(100, 102, 98, 101), (100, 102, 98, 101), (101, 109, 100, 105)]                 # the last day is still forming at T0
    views[T.D_1] = CandleSeries.from_records(rows, T.D_1, start="2026-09-29", symbol="EURUSD")
    runner = LiveRunner(_settings(), "EURUSD", lambda: views, notifier=TelegramNotifier(dry_run=True),
                        engine=FakeEngine(setup, signal_on_first_call=False), clock=lambda: NOW)
    runner.step(T0)
    lines, spans = runner.chart_context(views[T.H_1], T0)
    assert [round(v, 1) for v, _, _ in lines] == [102.0, 98.0] and "vorige dag high" in lines[0][1]
    assert spans and all(0 <= a < b <= 30 for a, b in spans)
    assert runner.chart_context(views[T.D_1]) == ([], [])                                      # a daily chart: no context


def test_the_chart_draws_shaded_windows_and_context_lines(tmp_path):
    from kronos_trader.notify.chart import render_chart
    rows = [(1.1 + i * 1e-4, 1.1015 + i * 1e-4, 1.0995 + i * 1e-4, 1.1005 + i * 1e-4) for i in range(40)]
    series = CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 06:00", symbol="EURUSD")
    out = render_chart(series, tmp_path / "c.png", extra_lines=[(1.1030, "vorige dag high 1.10300", None)],
                       shade_spans=[(4, 12), (20, 30)], title="EURUSD · 15m · ochtendcheck")
    assert out.exists() and out.stat().st_size > 10_000
