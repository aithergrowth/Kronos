"""TradingView headlines under the Telegram messages: context, cached, and never an error."""
import pandas as pd

from kronos_trader.notify.headlines import Headlines

NOW = pd.Timestamp("2026-10-07 14:30")                       # 16:30 in Amsterdam


def _item(minutes_ago, title, provider="Reuters"):
    return {"published": int((NOW - pd.Timedelta(minutes=minutes_ago)).timestamp()), "title": title,
            "provider": {"name": provider}}


class FakeClient:
    def __init__(self, items=None, fail=False):
        self.items, self.fail, self.calls = items or [], fail, []

    def get_news(self, symbol, limit=25):
        self.calls.append(symbol)
        if self.fail:
            raise OSError("no internet")
        return self.items


def test_the_newest_titles_of_the_day_in_local_time_escaped():
    client = FakeClient([_item(10, "Gold slides as dollar & yields rise"), _item(60 * 30, "Old news"),
                         _item(5, "Gold <b>slips</b> ahead of Fed minutes", "Dow Jones"), _item(20, "Third"), _item(30, "Fourth")])
    h = Headlines(max_items=3, client_factory=lambda: client)
    lines = h.lines("OANDA:XAUUSD", NOW)
    assert lines == ["16:25 Dow Jones: Gold &lt;b&gt;slips&lt;/b&gt; ahead of Fed minutes",
                     "16:20 Reuters: Gold slides as dollar &amp; yields rise", "16:10 Reuters: Third"]
    assert h.lines("OANDA:XAUUSD", NOW + pd.Timedelta(minutes=10)) == lines and client.calls == ["OANDA:XAUUSD"]   # cached
    h.lines("OANDA:XAUUSD", NOW + pd.Timedelta(minutes=16))
    assert len(client.calls) == 2                                                      # read again after the ttl


def test_no_token_a_failed_read_or_zero_items_give_no_lines():
    assert Headlines(client_factory=lambda: None).lines("OANDA:EURUSD", NOW) == []
    failing = FakeClient(fail=True)
    h = Headlines(client_factory=lambda: failing)
    assert h.lines("OANDA:EURUSD", NOW) == [] and h.lines("OANDA:EURUSD", NOW + pd.Timedelta(minutes=5)) == []
    assert len(failing.calls) == 1                                                     # a failed read waits its turn too
    assert Headlines(max_items=0, client_factory=lambda: FakeClient([_item(1, "x")])).lines("OANDA:EURUSD", NOW) == []
    assert Headlines(client_factory=lambda: FakeClient([{"title": None}, "junk", {"published": None}])).lines("X", NOW) == []

