"""OANDA feed: instrument names, request parameters, candle parsing, errors."""
import dataclasses
from types import SimpleNamespace

import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Timeframe as T
from kronos_trader.data.oanda import OandaFeed, instrument_for

PAYLOAD = {"instrument": "EUR_USD", "granularity": "M15", "candles": [
    {"complete": True, "volume": 120, "time": "2026-10-01T08:30:00.000000000Z",
     "mid": {"o": "1.17000", "h": "1.17100", "l": "1.16950", "c": "1.17050"}},
    {"complete": False, "volume": 8, "time": "2026-10-01T08:45:00.000000000Z",
     "mid": {"o": "1.17050", "h": "1.17080", "l": "1.17020", "c": "1.17060"}},
]}


class FakeSession:
    def __init__(self, status=200, payload=PAYLOAD):
        self.status, self.payload, self.calls = status, payload, []

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append((url, headers, params))
        return SimpleNamespace(status_code=self.status, json=lambda: self.payload, text="oops")


def test_instrument_names():
    assert instrument_for("EURUSD") == "EUR_USD" and instrument_for("XAUUSD") == "XAU_USD"
    assert instrument_for("NAS100") == "NAS100_USD" and instrument_for("usdjpy") == "USD_JPY"
    spec = dataclasses.replace(Settings().symbol("EURUSD"), oanda_instrument="EUR_USD_X")
    assert instrument_for("EURUSD", spec) == "EUR_USD_X"


def test_candles_request_and_parsing():
    session = FakeSession()
    feed = OandaFeed(token="abc", environment="practice", session=session)
    series = feed.get_candles("EURUSD", T.MIN_15, 300)
    url, headers, params = session.calls[-1]
    assert url == "https://api-fxpractice.oanda.com/v3/instruments/EUR_USD/candles"
    assert headers["Authorization"] == "Bearer abc"
    assert params["granularity"] == "M15" and params["count"] == 300
    assert params["dailyAlignment"] == 17 and params["weeklyAlignment"] == "Monday"
    assert len(series) == 2 and series.symbol == "EURUSD" and str(series.timestamps.iloc[0]) == "2026-10-01 08:30:00"
    assert series.last.close == pytest.approx(1.1706)
    assert feed.current_price("EURUSD") == pytest.approx(1.1706)


def test_http_errors_and_missing_token(monkeypatch):
    with pytest.raises(RuntimeError, match="OANDA 401"):
        OandaFeed(token="abc", session=FakeSession(status=401)).get_candles("EURUSD", T.H_1, 10)
    monkeypatch.delenv("OANDA_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="OANDA_TOKEN"):
        OandaFeed(token="", session=FakeSession())
