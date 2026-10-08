"""The forward record: journal plans against the broker's deals, the funding limits, the report."""
import pandas as pd
import pytest

from kronos_trader.forward import PRODUCTS, funding_status, reconcile, summary, unmatched_fills, write_report

T0 = pd.Timestamp("2026-10-07 08:05")


def _journal(rows):
    cols = ["time", "symbol", "event", "id", "direction", "poi_tf", "confirmation", "entry", "stop", "take_profit", "rr",
            "lots", "risk", "price", "pnl", "r", "reason", "note"]
    frame = pd.DataFrame([{c: r.get(c) for c in cols} for r in rows])
    frame["time"] = pd.to_datetime(frame["time"])
    frame["id"] = frame["id"].astype(str)
    return frame


def _deal(ticket, pid, typ, entry, reason, time, price, volume, profit=0.0, commission=0.0, swap=0.0, magic=20260930,
          symbol="EURUSD"):
    return {"ticket": ticket, "order": ticket, "position_id": pid, "symbol": symbol, "type": typ, "entry": entry,
            "reason": reason, "time": pd.Timestamp(time), "price": price, "volume": volume, "profit": profit,
            "commission": commission, "swap": swap, "fee": 0.0, "magic": magic, "comment": ""}


@pytest.fixture
def record():
    journal = _journal([
        {"time": "2026-10-07 06:00", "symbol": "EURUSD", "event": "start", "note": "code abc123def456 source 111 settings 222"},
        {"time": T0, "symbol": "EURUSD", "event": "setup", "id": "a1b2c3", "direction": "LONG", "entry": 1.10000,
         "stop": 1.09900, "take_profit": 1.10200, "rr": 2.0, "lots": 2.0, "risk": 200.0},
        {"time": T0, "symbol": "EURUSD", "event": "filled", "id": "9001", "direction": "LONG", "entry": 1.10002,
         "stop": 1.09900, "take_profit": 1.10200, "lots": 2.0, "risk": 204.0, "note": "setup a1b2c3"},
        {"time": "2026-10-07 11:00", "symbol": "EURUSD", "event": "closed", "id": "9001", "r": 1.96, "pnl": 396.0},
        {"time": T0, "symbol": "EURUSD", "event": "filled", "id": "9555", "note": "setup zzz"},      # not in the history
    ])
    deals = pd.DataFrame([
        _deal(1, 9001, 0, 0, 3, "2026-10-07 08:05:20", 1.10002, 2.0, commission=-6.0),
        _deal(2, 9001, 1, 1, 5, "2026-10-07 10:59", 1.10199, 2.0, profit=394.0, commission=-6.0),
        _deal(3, 7777, 1, 0, 0, "2026-10-07 09:00", 2650.0, 0.1, magic=0, symbol="XAUUSD"),          # Max by hand
        _deal(4, 7777, 0, 1, 4, "2026-10-07 09:30", 2655.0, 0.1, profit=-50.0, magic=0, symbol="XAUUSD"),
        _deal(5, 0, 2, 0, 0, "2026-10-06 00:00", 0.0, 0.0, profit=10000.0, magic=0, symbol=""),       # the deposit
    ])
    return journal, deals


def test_reconcile_matches_plan_fill_exit_costs_and_code(record):
    journal, deals = record
    rec = reconcile(journal, deals, magic=20260930)
    bot = rec[rec.position_id == "9001"].iloc[0]
    assert bot.source == "bot" and bot.status == "closed" and bot.setup_id == "a1b2c3" and bot.exit_reason == "take_profit"
    assert bot.entry_slip == pytest.approx(0.00002) and bot.entry_slip_r == pytest.approx(0.02)       # 0.2 pip of a 10-pip plan
    assert bot.exit_slip == pytest.approx(0.00001) and bot.exit_slip_r == pytest.approx(0.01)         # the target left 0.1 pip short
    assert bot.net == pytest.approx(382.0) and bot.r_gross == pytest.approx(394 / 204) and bot.r_net == pytest.approx(382 / 204)
    assert bot.cost_r == pytest.approx(-12 / 204) and bot.journal_r == pytest.approx(1.96)
    assert bot.code.startswith("code abc123def456")
    manual = rec[rec.position_id == "7777"].iloc[0]
    assert manual.source == "other" and manual.direction == "SHORT" and manual.exit_reason == "stop" and pd.isna(manual.r_net)
    assert list(unmatched_fills(journal, rec).id) == ["9555"]
    s = summary(rec)
    bot_all = s[(s.source == "bot") & (s.market == "all")].iloc[0]
    assert bot_all.closed == 1 and bot_all.r_net == pytest.approx(round(382 / 204, 2))
    assert s[(s.source == "other") & (s.market == "all")].iloc[0].net == pytest.approx(-50.0)


def test_a_stop_after_break_even_is_measured_from_the_moved_stop(record):
    journal, deals = record
    journal = _journal(journal.to_dict("records") + [{"time": "2026-10-07 09:00", "symbol": "EURUSD", "event": "breakeven",
                                                      "id": "9001", "stop": 1.10002}])
    deals = deals.copy()
    deals.loc[deals.ticket == 2, ["reason", "price", "profit"]] = [4, 1.10001, -4.0]
    bot = reconcile(journal, deals, magic=20260930).set_index("position_id").loc["9001"]
    assert bot.exit_reason == "stop" and bot.exit_slip == pytest.approx(0.00001)       # 0.1 pip under the moved stop, not +1R


def test_funding_status_ftmo_two_step_counts_the_day_and_every_stop():
    deals = pd.DataFrame([_deal(1, 11, 0, 1, 4, "2026-10-07 07:30", 1.1, 1.0, profit=-300.0)])     # 09:30 Prague: today
    account = {"balance": 9700.0, "equity": 9650.0, "margin": 300.0, "margin_free": 9350.0, "positions": [
        {"position_id": 12, "symbol": "XAUUSD", "sl": 2600.0, "loss_at_stop": 200.0, "profit": -50.0, "source": "bot"},
        {"position_id": 13, "symbol": "EURUSD", "sl": 1.09, "loss_at_stop": 100.0, "profit": 0.0, "source": "other"}]}
    st = funding_status(account, deals, PRODUCTS["ftmo_2step"], 10_000.0, pd.Timestamp("2026-10-07 12:00"))
    assert st["day_start_balance"] == pytest.approx(10_000.0) and st["daily_floor"] == pytest.approx(9_500.0)
    assert st["total_floor"] == pytest.approx(9_000.0) and st["left_today"] == pytest.approx(150.0)
    assert st["open_risk"] == pytest.approx(300.0) and st["manual_positions"] == 1
    assert st["worst_case_equity"] == pytest.approx(9_400.0) and st["worst_case_breaks"] is True
    one = funding_status(account, deals, PRODUCTS["ftmo_1step"], 10_000.0, pd.Timestamp("2026-10-07 12:00"), eod_balances=[10_400.0])
    assert one["daily_floor"] == pytest.approx(9_700.0) and one["total_floor"] == pytest.approx(9_400.0)   # 3 %; 10 % under the high
    no_stop = dict(account, positions=account["positions"] + [{"position_id": 14, "symbol": "NAS100", "sl": 0.0, "loss_at_stop": None, "profit": 0.0}])
    st2 = funding_status(no_stop, deals, PRODUCTS["ftmo_2step"], 10_000.0, pd.Timestamp("2026-10-07 12:00"))
    assert st2["positions_without_stop"] == [14] and st2["worst_case_equity"] is None


def test_write_report_makes_the_csv_and_the_page(record, tmp_path):
    journal, deals = record
    rec = reconcile(journal, deals, magic=20260930)
    page = write_report(tmp_path / "rep", rec, summary(rec), None, unmatched_fills(journal, rec))
    text = page.read_text(encoding="utf-8")
    assert (tmp_path / "rep" / "forward_trades.csv").exists() and "9001" in text and "Journal fills not in the deal history" in text


def test_deals_and_account_are_read_from_the_terminal_only(monkeypatch):
    """deals_from_mt5 / account_from_mt5 read the history, the account and every position (all magic numbers), in UTC."""
    from types import SimpleNamespace as NS
    from kronos_trader.forward import account_from_mt5, deals_from_mt5
    off = pd.Timedelta(hours=3)
    sec = lambda ts: int((pd.Timestamp(ts) + off).timestamp())

    class Api:
        POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
        def history_deals_get(self, a, b):
            self.window = (a, b)
            return [NS(ticket=1, order=1, position_id=9001, symbol="US100.cash", type=0, entry=0, reason=3, time=sec("2026-10-07 13:40"),
                       price=25000.0, volume=0.5, profit=0.0, commission=0.0, swap=0.0, fee=0.0, magic=20260930, comment="1HPOI BS"),
                    NS(ticket=2, order=0, position_id=0, symbol="", type=2, entry=0, reason=0, time=sec("2026-09-30 00:00"),
                       price=0.0, volume=0.0, profit=10000.0, commission=0.0, swap=0.0, fee=0.0, magic=0, comment="deposit")]
        def account_info(self):
            return NS(balance=10000.0, equity=9990.0, margin=250.0, margin_free=9740.0, currency="USD", login=1, server="FTMO-Demo")
        def positions_get(self):
            return [NS(ticket=9001, symbol="US100.cash", type=0, volume=0.5, price_open=25000.0, sl=24900.0, tp=25200.0, profit=-10.0,
                       swap=0.0, magic=20260930, time=sec("2026-10-07 13:40")),
                    NS(ticket=7777, symbol="XAUUSD", type=1, volume=0.1, price_open=2650.0, sl=0.0, tp=0.0, profit=0.0, swap=0.0,
                       magic=0, time=sec("2026-10-07 14:00"))]
        def last_error(self):
            return (0, "ok")

    class Broker:
        mt5, magic = Api(), 20260930
        def server_offset(self): return off
        def to_utc(self, s): return pd.Timestamp(s, unit="s") - off
        def our_symbol(self, name): return {"US100.cash": "NAS100"}.get(name, name)
        def pnl_for(self, symbol, direction, entry, exit_price, lots): return (exit_price - entry) * lots * direction.sign

    deals = deals_from_mt5(Broker(), pd.Timestamp("2026-10-07"))
    assert list(deals.symbol) == ["NAS100", ""] and deals.iloc[0].time == pd.Timestamp("2026-10-07 13:40")
    acc = account_from_mt5(Broker())
    bot, manual = acc["positions"]
    assert bot["symbol"] == "NAS100" and bot["loss_at_stop"] == pytest.approx(50.0) and bot["source"] == "bot"
    assert manual["source"] == "other" and manual["loss_at_stop"] is None and acc["equity"] == 9990.0


def test_the_day_message_names_the_day_the_open_risk_the_floors_and_the_target(record):
    from kronos_trader.forward import day_message
    journal, deals = record
    rec = reconcile(journal, deals, magic=20260930)
    positions = [{"position_id": 9100, "symbol": "BTCUSD", "direction": "LONG", "profit": 12.5, "source": "bot", "sl": 60000.0,
                  "loss_at_stop": 125.0}]
    account = {"balance": 10_332.0, "equity": 10_344.5, "positions": positions}
    evening = pd.Timestamp("2026-10-07 20:05")                                                   # 22:05 in Prague
    status = funding_status(account, deals, PRODUCTS["ftmo_2step"], 10_000.0, evening)
    text = day_message(rec, status, positions, evening, 10_000.0, target_pct=10.0)
    lines = text.splitlines()
    assert lines[0] == "📒 Account Wed 07 Oct 22:05: balance 10,332.00 (+3.32 % since the start), equity 10,344.50"
    assert lines[1] == "Today: 2 closed, 1 won, +1.87R after costs, net +332.00 (costs -12.00)"
    assert lines[2] == "• XAUUSD SHORT not the bot's (stop, -50.00)"                               # by hand: no R, first out
    assert lines[3] == "• EURUSD LONG +1.87R (take_profit, +382.00, entry +0.02R off the plan)"
    assert lines[4] == "Open: BTCUSD LONG +12.50; risk to the stops 125.00 (1.25 %)"
    assert lines[5] == "FTMO 2-Step: 844.50 left today (8.45 %), 1,344.50 to the total floor (13.44 %)"
    assert lines[6] == "target +10 %: 668.00 to go; 1 trading day(s)"
    assert lines[7] == "Since the start: 1 trade(s), 100 % won, +1.87R after costs, net +382.00"
    next_day = pd.Timestamp("2026-10-08 20:05")
    quiet = day_message(rec, funding_status(dict(account, positions=[]), deals, PRODUCTS["ftmo_2step"], 10_000.0, next_day), [],
                        next_day, 10_000.0)
    assert "Today: no trade closed (day result +0.00)" in quiet and "Open: nothing" in quiet and "target" not in quiet
    empty = day_message(pd.DataFrame(), status, [], evening, 10_000.0)
    assert "Today: no trade closed" in empty and "0 trading day(s)" in empty and "Since the start" not in empty


def test_forward_report_sends_the_day_message_with_telegram(record, tmp_path, monkeypatch):
    from kronos_trader import cli
    journal, deals = record
    rec = reconcile(journal, deals, magic=20260930)
    evening = pd.Timestamp("2026-10-07 20:05")
    account = {"balance": 10_332.0, "equity": 10_332.0, "positions": [], "server": "FTMO-Demo", "login": 1}
    status = funding_status(account, deals, PRODUCTS["ftmo_2step"], 10_000.0, evening)
    got = {}

    def fake_record(settings, journal_path, since, product, account_size, **kw):
        got.update(journal=journal_path, product=product, size=account_size)
        return {"journal": journal, "since": pd.Timestamp("2026-10-06"), "deals": deals, "account": account, "rec": rec,
                "summary": summary(rec), "status": status, "initial": 10_000.0, "product": PRODUCTS[product], "now": evening}

    sent = []
    monkeypatch.setattr(cli, "_forward_record", fake_record)
    monkeypatch.setattr(cli.TelegramNotifier, "send", lambda self, text, reply_markup=None: sent.append(self.prefix + text))
    assert cli.main(["forward-report", "--journal", "journal_ftmo/trades.csv", "--account-size", "10000", "--out-dir",
                     str(tmp_path / "rep"), "--telegram", "--tag", "FTMO", "--target-pct", "10"]) == 0
    assert got == {"journal": "journal_ftmo/trades.csv", "product": "ftmo_2step", "size": 10_000.0}
    assert len(sent) == 1 and sent[0].startswith("[FTMO] 📒 Account Wed 07 Oct 22:05") and "668.00 to go" in sent[0]
    assert (tmp_path / "rep" / "forward_report.html").exists()
    sent.clear()
    assert cli.main(["forward-report", "--journal", "journal_ftmo/trades.csv", "--out-dir", str(tmp_path / "rep")]) == 0
    assert sent == []                                                                   # without --telegram: the files only


def test_the_edge_line_reads_the_last_trades_and_warns_when_they_run_cold():
    """The 22:05 report's edge meter: the R after costs of the last 20 and 30 bot trades; a warning under 0R / -5R."""
    from kronos_trader.forward import edge_line
    import numpy as np
    stamps = pd.date_range("2026-10-01", periods=30, freq="h")
    rec = pd.DataFrame({"exit_time": stamps, "r_net": [2.0, -1.0] * 15, "source": "bot"})
    assert edge_line(rec.head(19)) == ""                                       # too few to read
    line = edge_line(rec)
    assert line.startswith("Edge: last 20 trades +10.0R, last 30 +15.0R")
    cold = rec.copy(); cold.loc[cold.index[-20:], "r_net"] = -1.0
    assert edge_line(cold).startswith("⚠️ Edge: last 20 trades -20.0R")
    assert edge_line(pd.DataFrame({"exit_time": stamps[:25], "r_net": [np.nan] * 25, "source": "bot"})) == ""   # nothing after costs yet
