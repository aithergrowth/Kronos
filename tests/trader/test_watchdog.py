"""Heartbeats from the live windows and the watchdog that reads them."""
import json
import pandas as pd
import pytest

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


def test_the_day_job_runs_once_a_day_after_its_time_and_once_after_a_restart(tmp_path):
    from kronos_trader.watchdog import DailyJob
    ran, clock = [], {"now": pd.Timestamp("2026-10-07 20:04")}                      # 22:04 in Amsterdam
    state = tmp_path / "day_report.json"
    job = DailyJob("22:05", "Europe/Amsterdam", ran.append, state_path=state, clock=lambda: clock["now"])
    assert job() is False and ran == []
    clock["now"] = pd.Timestamp("2026-10-07 20:05")
    assert job() is True and ran == [pd.Timestamp("2026-10-07 20:05")]
    clock["now"] = pd.Timestamp("2026-10-07 21:30")
    assert job() is False                                                             # once a day
    again = DailyJob("22:05", "Europe/Amsterdam", ran.append, state_path=state, clock=lambda: clock["now"])
    assert again() is False and len(ran) == 1                                         # a restart: not twice
    clock["now"] = pd.Timestamp("2026-10-08 06:00")                                   # the computer was off at 22:05
    assert again() is False
    clock["now"] = pd.Timestamp("2026-10-08 21:10")                                   # 23:10: late, but that day's
    assert again() is True and len(ran) == 2


def test_a_failing_day_job_tries_again_then_says_why(tmp_path):
    from kronos_trader.watchdog import DailyJob
    said, calls = [], []

    def job(now):
        calls.append(now)
        raise RuntimeError("MT5 initialize failed")

    job_ = DailyJob("22:05", "Europe/Amsterdam", job, clock=lambda: pd.Timestamp("2026-10-07 20:10"), tries=3, on_fail=said.append)
    assert job_() is False and job_() is False and said == []
    assert job_() is True and said == ["RuntimeError: MT5 initialize failed"] and len(calls) == 3
    assert job_() is False and len(calls) == 3                                        # given up for the day


def test_the_pinger_calls_at_most_every_period_and_survives_a_failed_call():
    from kronos_trader.watchdog import Pinger
    calls, clock = [], {"t": 0.0}

    def get(url):
        calls.append(url)
        if len(calls) == 2:
            raise OSError("no internet")

    ping = Pinger("https://hc-ping.com/abc", every_seconds=300, get=get, clock=lambda: clock["t"])
    assert ping() is True and calls == ["https://hc-ping.com/abc"]
    clock["t"] = 299.0
    assert ping() is False and len(calls) == 1
    clock["t"] = 300.0
    assert ping() is False and len(calls) == 2                                        # failed: printed, not raised
    clock["t"] = 610.0
    assert ping() is True and len(calls) == 3


def test_the_watchdog_command_wires_the_ping_and_the_day_report(tmp_path, monkeypatch):
    from kronos_trader import cli
    from kronos_trader.forward import PRODUCTS
    from kronos_trader.watchdog import DailyJob, Pinger
    seen = {}
    monkeypatch.setenv("WATCHDOG_PING_URL", "https://hc-ping.com/abc")
    monkeypatch.setattr("kronos_trader.watchdog.Watchdog.run_forever", lambda self, every, also=(): seen.update(also=also))
    sent = []
    monkeypatch.setattr(cli.TelegramNotifier, "send", lambda self, text, reply_markup=None: sent.append(self.prefix + text))
    journal = tmp_path / "journal_ftmo" / "trades.csv"
    assert cli.main(["watchdog", "--journal", str(journal), "--tag", "FTMO", "--report-at", "22:05", "--account-size", "10000",
                     "--target-pct", "10", "--mt5-names", "NAS100=US100.cash"]) == 0
    ping, day = seen["also"]
    assert isinstance(ping, Pinger) and ping.url == "https://hc-ping.com/abc" and ping.every == 300.0
    assert isinstance(day, DailyJob) and day.at == (22, 5) and day.state_path == journal.parent / "day_report.json"
    record = {"rec": pd.DataFrame(), "status": {"balance": 10_050.0, "equity": 10_050.0, "closed_today": 50.0, "open_risk": 0.0,
              "product": "FTMO 2-Step", "left_today": 550.0, "left_today_pct": 5.5, "left_total": 1_050.0, "left_total_pct": 10.5},
              "account": {"positions": []}, "now": NOW, "initial": 10_000.0, "product": PRODUCTS["ftmo_2step"]}

    class Broker:
        def __init__(self, settings, connect=True):
            seen["names"] = settings.symbols["NAS100"].mt5_symbol
        def connect(self):
            seen["connected"] = True

    monkeypatch.setattr("kronos_trader.execution.mt5.MT5Broker", Broker)
    monkeypatch.setattr(cli, "_forward_record", lambda *a, **k: dict(record, now=k["now"], broker=k["connect"]()))
    day.job(NOW)
    assert seen["connected"] and seen["names"] == "US100.cash"
    assert sent[0].startswith("[FTMO] 📒 Account Wed 07 Oct 12:00: balance 10,050.00 (+0.50 % since the start)")
    assert "target +10 %: 950.00 to go" in sent[0]
    with pytest.raises(SystemExit):
        cli.main(["watchdog", "--journal", str(tmp_path / "j2" / "trades.csv"), "--report-at", "22:05", "--product", "ftmo_3step"])
