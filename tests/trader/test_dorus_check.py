"""The Dorus check per trade: the verdict parser, the request, and the live runner's advice after an entry."""
import csv
import json

import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import CandleSeries, Timeframe
from kronos_trader.execution import PaperBroker
from kronos_trader.live import LiveRunner
from kronos_trader.notify import TelegramNotifier
from kronos_trader.notify.dorus_check import DorusCheck, parse_verdict

from test_live import NOW, FakeEngine, setup  # noqa: F401  (the fixture)

T = Timeframe


def test_parse_verdict_reads_the_json_and_falls_back_to_let_op():
    v = parse_verdict('{"verdict": "niet", "reason": "De zone is een week oud."}')
    assert (v.verdict, v.icon, v.reason) == ("niet", "❌", "De zone is een week oud.")
    assert parse_verdict('Mijn oordeel:\n{"verdict": "eens", "reason": "Verse demand na een sweep."}').verdict == "eens"
    odd = parse_verdict("geen idee")
    assert odd.verdict == "let op" and odd.icon == "⚠️" and "geen idee" in odd.reason
    assert parse_verdict('{"verdict": "misschien"}').verdict == "let op"


def test_the_check_is_off_without_a_key_or_a_model_and_sends_charts_and_context():
    assert not DorusCheck(api_key="", model="m", rubric="").available
    assert not DorusCheck(api_key="k", model="", rubric="").available
    sent = []
    check = DorusCheck(api_key="k", model="the-model", rubric="RUBRIC",
                       post=lambda body: sent.append(body) or {"content": [{"type": "text", "text": '{"verdict": "eens", "reason": "ok"}'}]})
    verdict = check.review("the setup", [("EURUSD 1H chart", b"\x89PNG")])
    assert verdict.verdict == "eens"
    body = sent[0]
    assert body["model"] == "the-model" and "RUBRIC" in body["system"]
    kinds = [c["type"] for c in body["messages"][0]["content"]]
    assert kinds == ["text", "image", "text"] and "the setup" in body["messages"][0]["content"][-1]["text"]


def _advisory_runner(setup, tmp_path, monkeypatch, answer):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("DORUS_CHECK_MODEL", "test-model")
    settings = Settings()
    settings.live.dorus_check = "advisory"
    settings.live.journal_path = str(tmp_path / "journal" / "trades.csv")
    settings.live.charts_dir = str(tmp_path / "charts")
    settings.live.briefing_time = None
    broker = PaperBroker(settings)
    broker.set_price("EURUSD", 1.1)
    notifier = TelegramNotifier(dry_run=True)
    rows = [(1.1, 1.101, 1.099, 1.1)] * 3
    fetch = lambda: {T.MIN_15: CandleSeries.from_records(rows, T.MIN_15, start="2026-10-01 08:15", symbol="EURUSD")}
    runner = LiveRunner(settings, "EURUSD", fetch, broker=broker, notifier=notifier, engine=FakeEngine(setup),
                        dry_run=False, require_approval=False, clock=lambda: NOW)
    assert runner.dorus is not None
    runner.dorus._post = answer
    runner.dorus_wait = True
    return runner, notifier, broker


def test_after_an_entry_the_verdict_goes_to_telegram_and_the_log(setup, tmp_path, monkeypatch):
    seen = []

    def answer(body):
        seen.append(body)
        return {"content": [{"type": "text", "text": json.dumps({"verdict": "niet", "reason": "Run through, <niet> getest."})}]}

    runner, notifier, broker = _advisory_runner(setup, tmp_path, monkeypatch, answer)
    runner.step(NOW)
    assert len(broker.open_positions()) == 1                         # the trade stands: the check is advice only
    line = next(m for m in notifier.sent if m.startswith("🧭 Dorus-check"))
    assert line == "🧭 Dorus-check EURUSD long: ❌ niet - Run through, &lt;niet&gt; getest."
    context = seen[0]["messages"][0]["content"][-1]["text"]
    assert "The bot went LONG at 1.10000" in context and "Confirmation: BOS on the 15m" in context
    assert any(c["type"] == "image" for c in seen[0]["messages"][0]["content"])     # the 15m chart went along
    with open(tmp_path / "journal" / "dorus_checks.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["symbol"] == "EURUSD" and rows[0]["verdict"] == "niet" and rows[0]["direction"] == "LONG"


def test_a_failing_check_changes_nothing(setup, tmp_path, monkeypatch):
    def answer(body):
        raise OSError("no network")

    runner, notifier, broker = _advisory_runner(setup, tmp_path, monkeypatch, answer)
    runner.step(NOW)
    assert len(broker.open_positions()) == 1
    assert not any(m.startswith("🧭") for m in notifier.sent)
    assert not (tmp_path / "journal" / "dorus_checks.csv").exists()


def test_without_the_environment_the_check_stays_off(setup, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DORUS_CHECK_MODEL", raising=False)
    settings = Settings()
    settings.live.dorus_check = "advisory"
    runner = LiveRunner(settings, "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=FakeEngine(setup))
    assert runner.dorus is None
    assert LiveRunner(Settings(), "EURUSD", lambda: {}, notifier=TelegramNotifier(dry_run=True), engine=FakeEngine(setup)).dorus is None
