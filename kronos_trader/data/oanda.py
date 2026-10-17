"""OANDA v20 candles as a live feed (practice or live account token).

A free OANDA practice account serves real-time mid candles for forex, metals
and index CFDs, which makes it the simplest feed for a laptop whose broker has
no market data permissions.  Only candles come from here; orders still go to
the configured broker.  Daily candles are aligned to 17:00 New York and weekly
candles start on Monday, the same convention as the TradingView OANDA bars in
the cache.  Set ``OANDA_TOKEN`` (and ``OANDA_ENV=practice|live``).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import pandas as pd

from ..config import Settings, SymbolSpec
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe

GRANULARITY: Dict[Timeframe, str] = {
    Timeframe.MIN_1: "M1", Timeframe.MIN_5: "M5", Timeframe.MIN_15: "M15", Timeframe.MIN_30: "M30",
    Timeframe.H_1: "H1", Timeframe.H_4: "H4", Timeframe.D_1: "D", Timeframe.W_1: "W", Timeframe.MN_1: "M",
}
HOSTS = {"practice": "https://api-fxpractice.oanda.com", "live": "https://api-fxtrade.oanda.com"}
INSTRUMENTS = {"XAUUSD": "XAU_USD", "XAGUSD": "XAG_USD", "NAS100": "NAS100_USD", "US30": "US30_USD",
               "SPX500": "SPX500_USD", "BTCUSD": "BTC_USD"}


def instrument_for(symbol: str, spec: Optional[SymbolSpec] = None) -> str:
    """OANDA instrument name: the spec's ``oanda_instrument``, a known alias, or ``EUR_USD`` style."""
    if spec is not None and spec.oanda_instrument:
        return spec.oanda_instrument
    symbol = symbol.upper()
    if symbol in INSTRUMENTS:
        return INSTRUMENTS[symbol]
    if len(symbol) == 6 and symbol.isalpha():
        return f"{symbol[:3]}_{symbol[3:]}"
    return symbol


def parse_candles(payload: Dict[str, Any], timeframe: Timeframe, symbol: str) -> CandleSeries:
    """Turn an OANDA ``/candles`` response (mid prices) into a ``CandleSeries`` with naive UTC open times."""
    rows = []
    for c in payload.get("candles", []):
        px = c.get("mid") or c.get("bid") or c.get("ask")
        if not px:
            continue
        rows.append({"timestamp": c["time"], "open": float(px["o"]), "high": float(px["h"]),
                     "low": float(px["l"]), "close": float(px["c"]), "volume": float(c.get("volume", 0) or 0)})
    if not rows:
        raise RuntimeError(f"OANDA returned no candles for {symbol} {timeframe.label}")
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_localize(None)
    return CandleSeries(df, timeframe, symbol.upper())


class OandaFeed:
    """Candle feed over the OANDA v20 REST API (``get_candles`` like a broker, plus ``current_price``)."""

    def __init__(self, token: Optional[str] = None, environment: Optional[str] = None,
                 settings: Optional[Settings] = None, session=None, timeout: float = 15.0):
        self.settings = settings or Settings()
        self.token = token or os.environ.get("OANDA_TOKEN", "")
        self.environment = environment or os.environ.get("OANDA_ENV", "practice")
        if not self.token:
            raise RuntimeError("set OANDA_TOKEN (an OANDA practice API token) to use the OANDA feed")
        self.base = HOSTS.get(self.environment, self.environment.rstrip("/"))
        self.session = session          # anything with .get(url, headers=, params=, timeout=) -> .status_code / .json()
        self.timeout = timeout

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if self.session is None:
            import requests
            self.session = requests.Session()
        r = self.session.get(self.base + path, params=params, timeout=self.timeout,
                             headers={"Authorization": f"Bearer {self.token}", "Accept-Datetime-Format": "RFC3339"})
        if r.status_code != 200:
            raise RuntimeError(f"OANDA {r.status_code} for {path}: {str(r.text)[:200]}")
        return r.json()

    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        timeframe = Timeframe.parse(timeframe)
        instrument = instrument_for(symbol, self.settings.symbols.get(symbol.upper()))
        params = {"granularity": GRANULARITY[timeframe], "count": int(min(max(count, 1), 5000)), "price": "M",
                  "alignmentTimezone": "America/New_York", "dailyAlignment": 17, "weeklyAlignment": "Monday"}
        return parse_candles(self._get(f"/v3/instruments/{instrument}/candles", params), timeframe, symbol)

    def current_price(self, symbol: str) -> float:
        """Mid close of the latest 1-minute candle (forming candle included)."""
        return float(self.get_candles(symbol, Timeframe.MIN_1, 2).last.close)
