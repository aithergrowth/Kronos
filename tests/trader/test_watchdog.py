"""Heartbeats from the live windows and the watchdog that reads them."""
import json
import pandas as pd

from kronos_trader.watchdog import Watchdog, problems, read_heartbeats

NOW = pd.Timestamp("2026-10-07 10:00")          # a Wednesday


def _beat(folder, symbol, **kw):
    doc = {"symbol": symbol, "time": str(NOW - pd.Timedelta(minutes=1)), "state": "ok", "detail": "",
           "last_scan_ok": str(NOW - pd.Timedelta(minutes=1)), "calendar_until": str(NOW + pd.Timedelta(days=2)), "news": True}
    doc.update(kw)
    (folder / f"heartbeat_{symbol}.json").write_text(json.dumps(doc), encoding="utf-8")


def test_problems_name_a_silent_window_a_failing_one_and_an_empty_calendar(tmp_path):
    _beat(tmp_path, "EURUSD")
    _beat(tmp_path, "XAUUSD", time=str(NOW - pd.Timedelta(minutes=12)))                               # stopped
    _beat(tmp_path, "NAS100", state="link down", detail="terminal closed", last_scan_ok=str(NOW - pd.Timedelta(minutes=20)))
    _beat(tmp_path, "BTCUSD", calendar_until=str(NOW - pd.Timedelta(hours=3)))
    (tmp_path / "heartbeat_BROKEN.json").write_text("{not json", encoding="utf-8")
    found = problems(read_heartbeats(tmp_path), NOW)
    assert set(found) == {("XAUUSD", "silent"), ("NAS100", "down"), ("BTCUSD", "calendar")}
    assert "no scan since" in found[("XAUUSD", "silent")] and "terminal closed" in found[("NAS100", "down")]
    friday = NOW + pd.Timedelta(days=2)                                                              # an empty week end is normal
    _beat(tmp_path, "BTCUSD", time=str(friday), last_scan_ok=str(friday), calendar_until=str(friday - pd.Timedelta(hours=3)))
    assert ("BTCUSD", "calendar") not in problems(read_heartbeats(tmp_path), friday)


def test_the_watchdog_says_it_once_and_says_when_it_is_over(tmp_path):
    sent, clock = [], {"now": NOW - pd.Timedelta(minutes=30)}
    dog = Watchdog(tmp_path, sent.append, clock=lambda: clock["now"])
    clock["now"] = NOW
    _beat(tmp_path, "EURUSD", time=str(NOW - pd.Timedelta(minutes=9)))
    assert len(dog.check()) == 1 and "EURUSD" in sent[0]
    assert dog.check() == []                                                                          # not again
    _beat(tmp_path, "EURUSD")
    assert dog.check() == ["✅ EURUSD: scanning again."]


def test_a_live_window_writes_its_heartbeat_after_every_scan(tmp_path):
    from kronos_trader.config import Settings
    from kronos_trader.core import CandleSeries, Timeframe
    from kronos_trader.execution import PaperBroker
    from kronos_trader.live import LiveRunner
    from kronos_trader.notify import TelegramNotifier
    settings = Settings()
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    series = CandleSeries.from_records([(1.1, 1.101, 1.099, 1.1)] * 3, Timeframe.MIN_15, start="2026-10-07 09:00", symbol="EURUSD")
    runner = LiveRunner(settings, "EURUSD", lambda: {Timeframe.MIN_15: series}, broker=PaperBroker(Settings()),
                        notifier=TelegramNotifier(dry_run=True), clock=lambda: NOW)
    runner._views = {Timeframe.MIN_15: series}
    runner._last_scan_ok = NOW
    path = runner.write_heartbeat("link down", "terminal closed")
    beat = json.loads(path.read_text(encoding="utf-8"))
    assert beat["symbol"] == "EURUSD" and beat["state"] == "link down" and beat["detail"] == "terminal closed"
    assert beat["last_candle"] == "2026-10-07 09:45:00" and beat["last_scan_ok"] == str(NOW)
    assert read_heartbeats(tmp_path / "journal")["EURUSD"]["time"] == str(NOW)


def test_a_market_whose_window_never_started_is_named_after_the_start_minutes(tmp_path):
    sent, clock = [], {"now": NOW}
    dog = Watchdog(tmp_path, sent.append, clock=lambda: clock["now"], expect=["EURUSD", "NAS100"])
    _beat(tmp_path, "EURUSD", time=str(NOW - pd.Timedelta(hours=20)), last_scan_ok=str(NOW - pd.Timedelta(hours=20)),
          state="error")                                                     # yesterday's: its window is still starting
    assert dog.check() == []
    clock["now"] = NOW + pd.Timedelta(minutes=2)
    _beat(tmp_path, "EURUSD", time=str(clock["now"]), last_scan_ok=str(clock["now"]))
    assert dog.check() == []                                                  # NAS100: the windows may still be starting
    clock["now"] = NOW + pd.Timedelta(minutes=6)
    _beat(tmp_path, "EURUSD", time=str(clock["now"]), last_scan_ok=str(clock["now"]))
    sent_now = dog.check()
    assert len(sent_now) == 1 and sent_now[0].startswith("🚨 NAS100: no window has scanned it since the watchdog started")
    assert "start_ftmo.bat" in sent_now[0]
    assert dog.check() == []
    _beat(tmp_path, "NAS100", time=str(clock["now"]), last_scan_ok=str(clock["now"]))
    assert dog.check() == ["✅ NAS100: its window runs and scans."]


def test_a_single_look_names_a_missing_market_at_once(tmp_path):
    _beat(tmp_path, "EURUSD")
    found = problems(read_heartbeats(tmp_path), NOW, expect=["EURUSD", "BTCUSD"], started=None)
    assert set(found) == {("BTCUSD", "missing")} and "watchdog started" not in found[("BTCUSD", "missing")]
