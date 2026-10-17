"""The local dashboard: one page from the journal folder and the charts folder, never a crash on what is missing."""
import csv
import json
import os

import pandas as pd

from kronos_trader.dashboard import build_dashboard, open_positions, resting_limits, load_journal
from kronos_trader.journal import FIELDS

NOW = pd.Timestamp("2026-10-14 10:00")          # a Wednesday, 12:00 in Prague


def _journal(folder, rows):
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def _beat(folder, symbol, minutes_ago=1, state="ok", detail=""):
    doc = {"symbol": symbol, "pid": 4242, "time": str(NOW - pd.Timedelta(minutes=minutes_ago)), "state": state, "detail": detail,
           "last_scan_ok": str(NOW - pd.Timedelta(minutes=minutes_ago)), "last_candle": "2026-10-14 09:45:00"}
    (folder / f"heartbeat_{symbol}.json").write_text(json.dumps(doc), encoding="utf-8")


def _start(folder, symbol, commit, dirty=False, when="20261014_060000"):
    (folder / "starts").mkdir(exist_ok=True)
    doc = {"symbol": symbol, "started_utc": "2026-10-14 06:00:00", "command": "python -m kronos_trader live",
           "code": {"commit": commit, "dirty": dirty}, "settings": {"telegram": {"token": "env:TELEGRAM_BOT_TOKEN"}}}
    (folder / "starts" / f"{symbol}_{when}.json").write_text(json.dumps(doc), encoding="utf-8")


def _fake_folder(tmp_path):
    folder, charts = tmp_path / "journal_ftmo", tmp_path / "charts"
    _journal(folder, [
        {"time": "2026-10-14 06:00:00", "symbol": "EURUSD", "event": "start", "note": "code abc123def456 source 111 settings 222"},
        {"time": "2026-10-14 06:00:05", "symbol": "XAUUSD", "event": "start", "note": "code abc123def456 source 111 settings 222"},
        {"time": "2026-10-14 07:00:00.123456", "symbol": "EURUSD", "event": "briefing", "price": "1.1", "note": "no setup: bias unclear"},
        {"time": "2026-10-14 08:05:00", "symbol": "EURUSD", "event": "setup", "id": "a1b2c3d4", "direction": "LONG", "entry": "1.1",
         "stop": "1.099", "take_profit": "1.102", "rr": "2", "lots": "2", "risk": "200"},
        {"time": "2026-10-14 08:05:01", "symbol": "EURUSD", "event": "filled", "id": "9001", "direction": "LONG", "entry": "1.10002",
         "stop": "1.099", "take_profit": "1.102", "lots": "2", "risk": "204", "note": "setup a1b2c3d4"},
        {"time": "2026-10-14 09:00:00", "symbol": "EURUSD", "event": "closed", "id": "9001", "direction": "LONG", "entry": "1.10002",
         "price": "1.10199", "pnl": "396", "r": "1.96", "reason": "take_profit", "lots": "2"},
        {"time": "2026-10-14 09:10:00", "symbol": "XAUUSD", "event": "filled", "id": "9002", "direction": "SHORT", "entry": "2650",
         "stop": "2660", "take_profit": "2630", "lots": "0.1", "risk": "100", "note": "setup ffff0000"},
        {"time": "2026-10-14 09:20:00", "symbol": "NAS100", "event": "limit_placed", "id": "7001", "direction": "LONG", "entry": "20000",
         "stop": "19950", "take_profit": "20100", "lots": "0.5", "risk": "100", "note": "setup 12345678; limit 0.5; valid until 11:00 UTC"},
        {"time": "2026-10-13 15:00:00", "symbol": "XAUUSD", "event": "closed", "id": "8000", "pnl": "-100", "r": "-1", "reason": "stop"},
        {"time": "bad time", "symbol": "EURUSD", "event": "closed", "id": "x", "pnl": "oops", "r": "oops"},
    ])
    _beat(folder, "EURUSD", minutes_ago=1)
    _beat(folder, "XAUUSD", minutes_ago=12)                                 # stopped
    _beat(folder, "NAS100", minutes_ago=1, state="link down", detail="terminal closed")
    _start(folder, "EURUSD", "abc123def456789")
    _start(folder, "XAUUSD", "abc123def456789", when="20261013_060000")    # older record of the same window
    _start(folder, "XAUUSD", "abc123def456789", dirty=True)
    (folder / "guard_day_start.json").write_text(json.dumps({"account_size": 10000.0, "day": "2026-10-14", "balance": 10050.0}))
    (folder / "guard_day_high.json").write_text(json.dumps({"account_size": 10000.0, "day_high": 10050.0}))
    (folder / "day_report.json").write_text(json.dumps({"date": "2026-10-13"}))
    (folder / "parity").mkdir()
    (folder / "parity" / "parity_2026-10-06.md").write_text("# Parity 2026-10-06\n\nold week\n", encoding="utf-8")
    (folder / "parity" / "parity_2026-10-13.md").write_text("# Parity 2026-10-13\n\n" + "\n".join(f"line {i}" for i in range(40)), encoding="utf-8")
    charts.mkdir()
    for k, name in enumerate(("EURUSD_4H_poi_touch.png", "XAUUSD_1H_briefing.png", "EURUSD_15m_setup.png", "EURUSD_1H_briefing.png")):
        (charts / name).write_bytes(b"\x89PNG not really")
        os.utime(charts / name, (NOW.timestamp() + 60 * k, NOW.timestamp() + 60 * k))   # oldest first: the 4H one is dropped
    return folder, charts


def test_the_page_shows_the_windows_the_trades_and_the_guard(tmp_path):
    folder, charts = _fake_folder(tmp_path)
    out = tmp_path / "journal_ftmo" / "dashboard" / "index.html"
    page = build_dashboard(folder / "trades.csv", charts, out, product="ftmo_2step", account_size=10000, now=NOW).read_text(encoding="utf-8")
    for market in ("EURUSD", "XAUUSD", "NAS100"):
        assert market in page
    assert "account <b>10,000</b>" in page and "FTMO 2-Step" in page and "abc123def456" in page
    assert "local changes" in page                                            # XAUUSD's newest start record is dirty
    assert "different code" not in page                                       # same commit everywhere
    assert "STALE" in page and "terminal closed" in page                      # XAUUSD silent, NAS100 link down
    assert page.count("card red") == 2 and "card'><b>EURUSD" in page
    assert "9002" in page and "no open position" not in page                  # XAUUSD still open, EURUSD closed
    assert "7001" in page and "valid until 11:00" in page                     # the resting limit
    assert "+1.96R" in page and "+396" in page                                # today's total
    assert "+0.96R" in page and "+296" in page                                # the week includes Tuesday's -1R
    assert "day floor 9,550.00" in page and "total floor 9,000.00" in page and "2026-10-13" in page
    assert "no setup: bias unclear" in page                                   # the briefing's decision
    assert "limit placed" in page and "take profit" in page                   # plain words in the events table
    assert "charts/EURUSD_1H_briefing.png" in page and "parity_2026-10-13.md" in page and "line 27" in page and "line 35" not in page
    assert (out.parent / "charts" / "EURUSD_1H_briefing.png").exists()
    assert "TELEGRAM_BOT_TOKEN" not in page and "kronos_trader live" not in page   # settings and command stay in the file
    assert 'http-equiv=refresh' in page and "written 2026-10-14 10:00:00 UTC" in page
    assert "oops" not in page                                                 # the damaged row is dropped
    copies = sorted(p.name for p in (out.parent / "charts").glob("*.png"))
    assert copies == ["EURUSD_15m_setup.png", "EURUSD_1H_briefing.png", "XAUUSD_1H_briefing.png"]   # two per market at most
    assert page.index("EURUSD_1H_briefing") < page.index("EURUSD_15m_setup")  # newest first
    (charts / "XAUUSD_1H_briefing.png").unlink()
    build_dashboard(folder / "trades.csv", charts, out, account_size=10000, now=NOW)
    assert not (out.parent / "charts" / "XAUUSD_1H_briefing.png").exists()    # the copy of a chart that is gone goes too


def test_the_journal_s_open_positions_and_resting_limits(tmp_path):
    folder, _ = _fake_folder(tmp_path)
    journal = load_journal(folder / "trades.csv")
    assert list(open_positions(journal)["id"]) == ["9002"]
    assert list(resting_limits(journal)["id"]) == ["7001"]
    with open(folder / "trades.csv", "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writerow({"time": "2026-10-14 09:30:00", "symbol": "NAS100", "event": "filled", "id": "9003", "note": "setup 12345678; limit 7001"})
        w.writerow({"time": "2026-10-14 09:40:00", "symbol": "XAUUSD", "event": "closed", "id": "9002", "pnl": "-50", "r": "-0.5"})
    journal = load_journal(folder / "trades.csv")
    assert list(open_positions(journal)["id"]) == ["9003"]                   # the filled limit is a position now
    assert len(resting_limits(journal)) == 0


def test_an_empty_folder_and_a_missing_one_render_without_error(tmp_path):
    out = tmp_path / "dash" / "index.html"
    page = build_dashboard(tmp_path / "nowhere" / "trades.csv", tmp_path / "nocharts", out, now=NOW).read_text(encoding="utf-8")
    assert "no data yet" in page and "no start records yet" in page and "no parity report yet" in page and "no guard files yet" in page
    (tmp_path / "journal").mkdir()
    (tmp_path / "journal" / "trades.csv").write_text("not,a,journal\n1,2\n", encoding="utf-8")
    (tmp_path / "journal" / "heartbeat_EURUSD.json").write_text("{broken", encoding="utf-8")
    page = build_dashboard(tmp_path / "journal" / "trades.csv", tmp_path / "nocharts", out, now=NOW).read_text(encoding="utf-8")
    assert "<footer>" in page and "could not render" not in page


def test_the_cli_registers_the_command():
    from kronos_trader.cli import build_parser
    args = build_parser().parse_args(["dashboard", "--journal", "j/trades.csv", "--every", "60", "--serve", "8765", "--account-size", "10000"])
    assert args.func.__name__ == "cmd_dashboard" and args.serve == 8765 and args.every == 60.0 and args.product == "ftmo_2step"
