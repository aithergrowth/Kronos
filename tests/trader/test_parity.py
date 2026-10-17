"""The weekly parity check: setup ids shared by the backtest and the journal, the journal's links (limit -> fill -> close),
the verdicts and their explanations, and a whole run on saved candles and on a terminal stand-in."""
from types import SimpleNamespace

import pandas as pd
import pytest

from kronos_trader import cli
from kronos_trader.backtest import Backtester
from kronos_trader.backtest.provenance import settings_fingerprint
from kronos_trader.config import Settings, SymbolSpec
from kronos_trader.core import CandleSeries, Timeframe
from kronos_trader.data import MultiTimeframeData
from kronos_trader.data.tv_cache import save_series
from kronos_trader.forward import read_journal
from kronos_trader.journal import Journal, setup_id
from kronos_trader.live import LiveRunner, short_id_for
from kronos_trader.parity import (backtest_week, command_argv, compare, live_side, run_parity, settings_diff, summary_lines,
                                  telegram_text, warm_start, week_window, window_settings, LiveSignal)

from conftest import HK_CSV, REPO_ROOT

T = Timeframe
WEEK = (pd.Timestamp("2024-01-08"), pd.Timestamp("2024-01-15"))     # three trades (a stop, a break-even, a target that
NOW = pd.Timestamp("2024-01-20")                                       # closes the week after) and many refusals


@pytest.fixture(scope="module")
def hk_data():
    base = CandleSeries.from_csv(HK_CSV, T.MIN_5, symbol="09988")
    return MultiTimeframeData.from_base(base, [T.MIN_15, T.H_1, T.H_4, T.D_1, T.W_1, T.MN_1])


def _hk_settings():
    s = Settings()
    s.symbols["09988"] = SymbolSpec("09988", 0.01, 1.0, price_decimals=2, typical_spread_pips=2.0)
    s.kronos.mode = "off"
    s.session.enabled = False          # Hong Kong stock hours, not the Amsterdam windows
    s.news.enabled = False
    s.confirmation.allow_first_candle = True
    return s


PROFILE = """
symbols:
  "09988": {pip_size: 0.01, pip_value_per_lot: 1.0, price_decimals: 2, typical_spread_pips: 2.0}
kronos: {mode: "off"}
session: {enabled: false}
news: {enabled: false}
confirmation: {allow_first_candle: true}
"""


def test_the_backtests_setup_id_is_the_live_windows():
    for key in [(("1H", "bearish", "2026-10-07 09:00:00"), "2026-10-08 10:00:00"), (("4H", "bullish", "x"), "y")]:
        assert setup_id(key) == short_id_for(key)
        assert len(setup_id(key)) == 8


def test_week_window():
    wed = pd.Timestamp("2026-10-14 15:00")
    assert week_window("auto", wed) == (pd.Timestamp("2026-10-12"), wed)                       # the week so far
    mon = pd.Timestamp("2026-10-12 09:00")
    assert week_window("auto", mon) == (pd.Timestamp("2026-10-05"), pd.Timestamp("2026-10-12"))   # Monday: the week before
    assert week_window("last", wed) == (pd.Timestamp("2026-10-05"), pd.Timestamp("2026-10-12"))
    assert week_window("2026-10-07", pd.Timestamp("2026-10-20")) == (pd.Timestamp("2026-10-05"), pd.Timestamp("2026-10-12"))
    sun = pd.Timestamp("2026-10-11 20:00")
    assert week_window("auto", sun) == (pd.Timestamp("2026-10-05"), sun)                       # BTC's weekend counts


def test_a_window_is_rebuilt_from_the_command_in_its_start_record(tmp_path):
    profile = (REPO_ROOT / "config" / "dorus_live_nas100.yaml").as_posix()
    command = (f"C:\\Users\\max\\Kronos\\kronos_trader\\__main__.py --config {profile} live --symbol NAS100 --broker mt5 "
               f"--execute --no-approval --account-size 10000 --journal journal_ftmo/trades.csv --tag FTMO "
               f"--mt5-symbol US100.cash --product ftmo_2step")
    argv = command_argv(command)
    assert argv[:2] == ["--config", profile]
    settings, symbol, source = window_settings(command, [])
    assert symbol == "NAS100" and source == "the window's start record"
    assert settings.account_size == 10000 and settings.symbol("NAS100").mt5_symbol == "US100.cash"
    assert settings.live.journal_path == "journal_ftmo/trades.csv"
    # exactly what the window built: the same function on the same command, the same fingerprint
    same, _sym = cli.live_settings(cli.build_parser().parse_args(argv))
    assert settings_fingerprint(settings)[1] == settings_fingerprint(same)[1]
    # a command that no longer parses falls back to the profile
    fallback = ["--config", profile, "live", "--symbol", "NAS100", "--account-size", "25000"]
    settings2, _s, source2 = window_settings("x --config", fallback)
    assert settings2.account_size == 25000 and source2.startswith("the profile")
    with pytest.raises(RuntimeError):
        window_settings(None, [])


def test_the_window_and_its_engine_leave_the_settings_fingerprint_alone(tmp_path):
    """cmd_live records the fingerprint after the runner and the engine are built: building them must not change it."""
    profile = (REPO_ROOT / "config" / "dorus_live.yaml").as_posix()
    args = cli.build_parser().parse_args(["--config", profile, "live", "--symbol", "EURUSD", "--journal", str(tmp_path / "t.csv")])
    settings, symbol = cli.live_settings(args)
    before = settings_fingerprint(settings)[1]
    LiveRunner(settings, symbol, fetch=lambda: {}, engine=cli._engine(settings))
    assert settings_fingerprint(settings)[1] == before


def test_settings_diff_names_the_changed_keys():
    a = {"risk": {"risk_pct": 1.5, "min_rr": 1.0}, "symbols": {"EURUSD": {"pip_size": 0.0001}}}
    b = {"risk": {"risk_pct": 1.25, "min_rr": 1.0}, "symbols": {"EURUSD": {"pip_size": 0.0001}}, "extra": {"x": 1}}
    diff = settings_diff(a, b)
    assert any(d.startswith("risk.risk_pct: window 1.5, here 1.25") for d in diff)
    assert any(d.startswith("extra.x") for d in diff) and not any("min_rr" in d for d in diff)


def test_new_settings_at_their_defaults_are_not_a_different_profile():
    from kronos_trader.parity import settings_new_keys_only
    window = {"risk": {"risk_pct": 1.5, "min_rr": 1.0}}
    assert settings_new_keys_only(window, {"risk": {"risk_pct": 1.5, "min_rr": 1.0, "tp_buffer_fraction": 0.0}}) == 1
    assert settings_new_keys_only(window, {"risk": {"risk_pct": 1.25, "min_rr": 1.0, "tp_buffer_fraction": 0.0}}) == 0   # a value changed
    assert settings_new_keys_only(window, {"risk": {"risk_pct": 1.5}}) == 0                                               # a key gone
    assert settings_new_keys_only(window, window) == 0


def _journal(tmp_path):
    j = Journal(tmp_path / "trades.csv")
    t = pd.Timestamp("2026-10-06 08:00")
    fields = dict(direction="SHORT", poi_tf="1H", confirmation="BS", entry=1.1662, stop=1.1675, take_profit=1.1630, rr=2.5)
    j.log("setup", "EURUSD", time=pd.Timestamp("2026-10-02 08:00"), id="00000000", **fields)      # before the week
    j.log("setup", "EURUSD", time=t, id="aaaaaaaa", **fields)
    j.log("limit_placed", "EURUSD", time=t, id="L1", entry=1.1665, note="setup aaaaaaaa; limit 0.25; valid until 12:00 UTC")
    # the close carries its deal's time, before the scan that journaled the fill
    j.log("closed", "EURUSD", time=t + pd.Timedelta(minutes=9), id="P1", entry=1.1665, price=1.1630, r=2.69, reason="take_profit")
    j.log("filled", "EURUSD", time=t + pd.Timedelta(minutes=10), id="P1", entry=1.1665, note="setup aaaaaaaa; limit L1")
    j.log("setup", "EURUSD", time=t + pd.Timedelta(hours=1), id="bbbbbbbb", **fields)
    j.log("not_executed", "EURUSD", time=t + pd.Timedelta(hours=1), id="bbbbbbbb", reason="spread 41% of the stop distance (max 30%)")
    j.log("setup", "EURUSD", time=t + pd.Timedelta(hours=2), id="cccccccc", **fields)
    j.log("limit_placed", "EURUSD", time=t + pd.Timedelta(hours=2), id="L2", entry=1.1666, note="setup cccccccc; limit 0.25; valid until")
    j.log("limit_cancelled", "EURUSD", time=t + pd.Timedelta(hours=6), id="L2", reason="expired")
    j.log("stale", "EURUSD", time=t + pd.Timedelta(hours=3), id="dddddddd", note="5m 2 h old", **fields)
    j.log("setup", "EURUSD", time=t + pd.Timedelta(hours=4), id="eeeeeeee", **fields)
    j.log("setup", "XAUUSD", time=t, id="ffffffff", **fields)                                       # another market
    return read_journal(j.path)


def test_live_side_follows_each_setup_to_its_end(tmp_path):
    live = live_side(_journal(tmp_path), "EURUSD", pd.Timestamp("2026-10-05"), pd.Timestamp("2026-10-12"))
    assert set(live) == {"aaaaaaaa", "bbbbbbbb", "cccccccc", "dddddddd", "eeeeeeee"}
    a = live["aaaaaaaa"]
    assert (a.kind, a.limit, a.fill, a.exit_reason, a.r) == ("trade", 1.1665, 1.1665, "take_profit", 2.69)
    assert a.outcome == "limit filled @ 1.1665, target +2.69R"
    assert live["bbbbbbbb"].kind == "refused" and "spread" in live["bbbbbbbb"].outcome
    assert live["cccccccc"].kind == "limit unfilled" and live["cccccccc"].outcome.endswith("cancelled: expired")
    assert live["dddddddd"].kind == "no trade" and "stale" in live["dddddddd"].outcome
    assert live["eeeeeeee"].kind == "no action"


def _log(sid, at, outcome, direction="SHORT", poi_tf="1H", limit=None):
    out = {"sid": sid, "at": pd.Timestamp(at), "direction": direction, "poi_tf": poi_tf, "confirmation": "BS",
           "entry": 1.1662, "stop": 1.1675, "take_profit": 1.1630, "rr": 2.5, "bias_combo": "", "outcome": outcome}
    if limit is not None:
        out["limit"] = limit
    return out


def _live(sid, at, kind, outcome, direction="SHORT", exit_reason="", r=None, fill=None):
    return LiveSignal(sid, pd.Timestamp(at), direction, "1H", "BS", 1.1662, 1.1675, 1.1630, 2.5, kind=kind, outcome=outcome,
                      fill=fill, exit_reason=exit_reason, r=r)


def test_compare_gives_each_setup_a_verdict_and_a_reason():
    trade = lambda reason, r: SimpleNamespace(reason=reason, r=r, entry=1.1662)
    live = {"a1": _live("a1", "2026-10-06 08:00:40", "trade", "filled, target", exit_reason="take_profit", r=2.4, fill=1.1662),
            "b2": _live("b2", "2026-10-06 09:00:40", "trade", "filled, stop", exit_reason="stop", r=-1.0, fill=1.1662),
            "c3": _live("c3", "2026-10-06 10:00:40", "refused", "refused: spread 41% of the stop distance (max 30%)"),
            "e5": _live("e5", "2026-10-07 12:20:00", "refused", "refused: spread 41%")}
    signals = {"a1": _log("a1", "2026-10-06 08:00", "market"), "b2": _log("b2", "2026-10-06 09:00", "market"),
               "c3": _log("c3", "2026-10-06 10:00", "market"), "d4": _log("d4", "2026-10-07 09:00", "market"),
               "f6": _log("f6", "2026-10-07 12:05", "limit: expired unfilled", limit=1.1666)}
    trades = {"a1": trade("take_profit", 2.4), "b2": trade("take_profit", 2.4), "c3": trade("stop", -1.0), "d4": trade("stop", -1.0)}
    rows_sym = pd.DataFrame({"time": pd.to_datetime(["2026-10-06 08:00:40", "2026-10-07 08:00:00", "2026-10-07 15:00:00"]),
                             "event": ["setup", "briefing", "start"]})
    rows = {r.sid: r for r in compare("EURUSD", live, signals, trades, rows_sym)}
    assert rows["a1"].verdict == "match" and rows["a1"].live_r == 2.4 and rows["a1"].bt_r == 2.4
    assert rows["b2"].verdict == "outcome differs"
    assert rows["c3"].verdict == "outcome differs" and "spread cap is a live-only rule" in rows["c3"].note
    assert rows["d4"].verdict == "backtest only" and "probably down" in rows["d4"].note        # next row: the restart
    assert rows["e5"].verdict == "live only" and "the backtest signalled f6" in rows["e5"].note  # its near twin
    assert rows["f6"].verdict == "backtest only" and "the window signalled e5" in rows["f6"].note
    assert [r.sid for r in compare("EURUSD", live, signals, trades, rows_sym)] == ["a1", "b2", "c3", "d4", "f6", "e5"]


def test_the_signal_log_holds_every_signal_and_what_became_of_it(hk_data):
    s = _hk_settings()
    s.risk.limit_entry_fraction = 0.25                 # limit entries: placed, filled, expired
    result = Backtester(s, hk_data, "09988", step_tf=T.MIN_15, start="2024-05-20", end="2024-06-07").run()
    assert len(result.signal_log) == result.signals > 0
    ids = [entry["sid"] for entry in result.signal_log]
    assert len(set(ids)) == len(ids) and all(len(i) == 8 for i in ids)
    assert all(entry["outcome"] for entry in result.signal_log)
    by_id = {entry["sid"]: entry for entry in result.signal_log}
    assert result.trades
    for t in result.trades:
        assert by_id[t.meta["sid"]]["outcome"] == "limit filled"
    placed = [e for e in result.signal_log if e["outcome"].startswith("limit")]
    assert placed and all("limit" in e for e in placed)


def _save(data, folder, until):
    for tf, series in data.series.items():
        save_series(series.closed_as_of(until), folder, "09988", merge=False)


def _write_journal_from_backtest(tmp_path, data, journal_path, drop_first=False):
    """A window's journal as the live runner writes it, from the backtest of the same candles: start record, setups,
    fills, closes and refusals."""
    profile = tmp_path / "hk.yaml"
    profile.write_text(PROFILE, encoding="utf-8")
    argv = ["--config", str(profile), "live", "--symbol", "09988", "--journal", str(journal_path)]
    settings, symbol = cli.live_settings(cli.build_parser().parse_args(argv))
    runner = LiveRunner(settings, symbol, fetch=lambda: {}, clock=lambda: pd.Timestamp("2024-01-07 20:00"))
    resolved, sha = settings_fingerprint(settings)
    runner.record_start({"commit": "abc1234", "dirty": False, "source_sha256": "f" * 64}, resolved, sha,
                        "C:\\K\\kronos_trader\\__main__.py " + " ".join(argv))
    run_start = warm_start(data, settings, WEEK[0] - pd.Timedelta(days=7))
    _result, signals, trades = backtest_week(settings, data, "09988", WEEK[0], WEEK[1], run_start, NOW)
    j = Journal(journal_path)
    for n, (sid, log) in enumerate(sorted(signals.items(), key=lambda kv: kv[1]["at"])):
        if drop_first and n == 0:
            continue
        t = pd.Timestamp(log["at"]) + pd.Timedelta(seconds=40)
        j.log("setup", "09988", time=t, id=sid, direction=log["direction"], poi_tf=log["poi_tf"], confirmation=log["confirmation"],
              entry=log["entry"], stop=log["stop"], take_profit=log["take_profit"], rr=log["rr"])
        tr = trades.get(sid)
        if tr is None:
            j.log("not_executed", "09988", time=t, id=sid, reason=log["outcome"])
            continue
        j.log("filled", "09988", time=t, id=f"P{n}", direction=log["direction"], entry=tr.entry, note=f"setup {sid}")
        if tr.reason != "end_of_data":
            j.log("closed", "09988", time=tr.closed_at, id=f"P{n}", price=tr.exit, r=float(tr.r), reason=tr.reason)
    return signals


def test_a_journal_written_from_the_same_candles_matches_one_to_one(hk_data, tmp_path):
    candles = tmp_path / "candles"
    _save(hk_data, candles, NOW)
    journal_path = tmp_path / "journal_x" / "trades.csv"
    signals = _write_journal_from_backtest(tmp_path, hk_data, journal_path)
    assert signals, "the fixture week has signals"
    report = run_parity(journal_path, start=WEEK[0], end=WEEK[1], data_dir=candles, now=NOW, log=lambda s: None)
    (m,) = report.markets
    assert not m.error and m.settings_note.startswith("identical to the window's")
    assert [r.verdict for r in m.rows] == ["match"] * len(signals)
    assert report.matched == len(signals) and abs(m.live_r - m.bt_r) < 1e-6
    assert report.markdown_path.exists() and report.csv_path.exists()
    text = report.markdown_path.read_text(encoding="utf-8")
    assert f"{len(signals)} of {len(signals)} signals match" in text
    assert telegram_text(report).startswith("🔁 <b>Parity week of 08 Jan</b>")
    assert all(line.isascii() for line in summary_lines(report))


def test_a_missed_signal_shows_as_backtest_only(hk_data, tmp_path):
    candles = tmp_path / "candles"
    _save(hk_data, candles, NOW)
    journal_path = tmp_path / "journal_y" / "trades.csv"
    signals = _write_journal_from_backtest(tmp_path, hk_data, journal_path, drop_first=True)
    report = run_parity(journal_path, start=WEEK[0], end=WEEK[1], data_dir=candles, now=NOW, log=lambda s: None)
    verdicts = [r.verdict for r in report.rows]
    assert verdicts[0] == "backtest only" and verdicts[1:] == ["match"] * (len(signals) - 1)
    assert "backtest only" in telegram_text(report)


class _Terminal:
    """The MT5 terminal's stand-in: candles up to now, the forming one included (export_candles drops it)."""
    def __init__(self, data, now):
        self.data, self.now, self.asked, self.closed = data, now, [], False

    def get_candles(self, symbol, tf, count):
        self.asked.append((symbol, tf, count))
        series = self.data[tf]
        n = int((series.timestamps <= self.now).sum())
        return series._view(max(0, n - count), n)

    def disconnect(self):
        self.closed = True


def test_the_candles_come_from_the_terminal_and_stay_beside_the_report(hk_data, tmp_path):
    journal_path = tmp_path / "journal_z" / "trades.csv"
    _write_journal_from_backtest(tmp_path, hk_data, journal_path)
    terminal = _Terminal(hk_data, NOW)
    report = run_parity(journal_path, start=WEEK[0], end=WEEK[1], connect=lambda settings: terminal, now=NOW,
                        log=lambda s: None)
    assert terminal.closed and {tf for _s, tf, _n in terminal.asked} == set(hk_data.series)
    saved = report.candles_dir
    assert (saved / "09988_5min.csv").exists() and (saved / "09988_1MO.csv").exists()
    last = pd.read_csv(saved / "09988_5min.csv", parse_dates=["timestamp"])["timestamp"].max()
    assert last + pd.Timedelta(minutes=5) <= NOW                    # the forming candle stays out
    assert not report.markets[0].error and report.rows
    assert all(r.verdict == "match" for r in report.rows)
    assert "--data-dir" in report.markdown_path.read_text(encoding="utf-8")     # the rerun line


def test_the_parity_command_writes_the_report(hk_data, tmp_path, capsys):
    candles = tmp_path / "candles"
    _save(hk_data, candles, NOW)
    journal_path = tmp_path / "journal_c" / "trades.csv"
    _write_journal_from_backtest(tmp_path, hk_data, journal_path)
    code = cli.main(["parity", "--journal", str(journal_path), "--from", "2024-01-08", "--to", "2024-01-15",
                     "--data-dir", str(candles)])
    out = capsys.readouterr().out
    assert code == 0 and "signals match" in out and "report:" in out
    assert (journal_path.parent / "parity" / "parity_2024-01-08.md").exists()
