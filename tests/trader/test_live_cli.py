"""Read-only candle/notification wiring; every external boundary is a test double."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kronos_trader import cli, live
from kronos_trader.config import Settings


@pytest.mark.parametrize("execute", [False, True])
def test_mt5_feed_is_separate_from_execution_capability(monkeypatch, execute):
    settings = Settings()
    adapter = object()
    fetch = Mock()
    build = Mock(return_value=fetch)
    notifier = SimpleNamespace(configured=True)
    runner = Mock()
    runner_factory = Mock(return_value=runner)
    monkeypatch.setattr(cli, "_load_settings", lambda args: settings)
    monkeypatch.setattr(cli, "_broker", lambda args, settings: adapter)
    monkeypatch.setattr(cli, "_forecaster", lambda settings: None)
    monkeypatch.setattr(cli, "TelegramNotifier", lambda **kwargs: notifier)
    monkeypatch.setattr(live, "build_fetch", build)
    monkeypatch.setattr(live, "LiveRunner", runner_factory)
    args = SimpleNamespace(symbol="EURUSD", broker="mt5", feed="broker", data_dir=None,
                           execute=execute, no_approval=False, notify_every_scan=False, once=False, poll=60)
    assert cli.cmd_live(args) == 0
    assert build.call_args.kwargs["broker"] is adapter
    assert runner_factory.call_args.kwargs["broker"] is (adapter if execute else None)
    assert runner_factory.call_args.kwargs["dry_run"] is not execute
    assert runner_factory.call_args.kwargs["notifier"] is notifier
    runner.run_forever.assert_called_once_with(60)
