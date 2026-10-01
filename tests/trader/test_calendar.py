"""News calendar: currency mapping, blackout window, CSV round trip, feed parsers."""
from types import SimpleNamespace

import pandas as pd

from kronos_trader.data.calendar import (NewsCalendar, NewsEvent, currencies_of, fetch_forexfactory, from_forexfactory,
                                         from_tradingview, load_events, save_events)


def test_currencies_of_symbol():
    assert currencies_of("EURUSD") == {"EUR", "USD"} and currencies_of("usdjpy") == {"USD", "JPY"}
    assert currencies_of("XAUUSD") == {"USD"} and currencies_of("NAS100") == {"USD"} and currencies_of("BTCUSD") == {"USD"}


def test_blackout_window_and_importance():
    events = [NewsEvent(pd.Timestamp("2026-07-30 12:30"), "USD", "GDP Growth Rate QoQ Adv", 1),
              NewsEvent(pd.Timestamp("2026-07-30 11:00"), "GBP", "BoE Interest Rate Decision", 1),
              NewsEvent(pd.Timestamp("2026-07-30 13:00"), "USD", "Medium thing", 0)]
    cal = NewsCalendar(events, before_minutes=30, after_minutes=30, min_importance=1)
    assert cal.blackout("USDJPY", "2026-07-30 12:00").title.startswith("GDP")      # 30 minutes before the release
    assert cal.blackout("USDJPY", "2026-07-30 13:00").title.startswith("GDP")      # 30 minutes after
    assert cal.blackout("USDJPY", "2026-07-30 11:15") is None                      # BoE is not a USDJPY currency
    assert cal.blackout("GBPUSD", "2026-07-30 11:15").currency == "GBP"
    assert cal.blackout("USDJPY", "2026-07-30 13:20") is None                      # the medium event is ignored
    assert [e.title for e in cal.upcoming("EURUSD", "2026-07-30 10:00", within_minutes=180)] == ["GDP Growth Rate QoQ Adv"]


def test_csv_round_trip_and_dedupe(tmp_path):
    events = [NewsEvent(pd.Timestamp("2026-09-11 12:30"), "USD", "Inflation Rate YoY", 1)] * 2
    path = save_events(events, tmp_path / "cal.csv")
    loaded = load_events(path)
    assert len(loaded) == 1 and loaded[0] == events[0]
    assert load_events(tmp_path / "missing.csv") == []


def test_feed_parsers():
    tv = {"result": [{"date": "2026-09-16T18:00:00.000Z", "currency": "USD", "title": "Fed Interest Rate Decision", "importance": 1},
                     {"date": None, "currency": "USD", "title": "skipped"}]}
    ev = from_tradingview(tv)
    assert len(ev) == 1 and str(ev[0].time) == "2026-09-16 18:00:00" and ev[0].importance == 1
    ff = [{"title": "Non-Farm Employment Change", "country": "USD", "date": "2026-10-02T08:30:00-04:00", "impact": "High"},
          {"title": "Bank Holiday", "country": "JPY", "date": "2026-10-02T00:00:00-04:00", "impact": "Holiday"}]
    ev = from_forexfactory(ff)
    assert str(ev[0].time) == "2026-10-02 12:30:00" and ev[0].importance == 1 and ev[1].importance == -1

    class Session:
        def get(self, url, timeout=None, headers=None):
            assert url.endswith("ff_calendar_thisweek.json")
            return SimpleNamespace(status_code=200, json=lambda: ff)

    assert len(fetch_forexfactory(session=Session())) == 2
