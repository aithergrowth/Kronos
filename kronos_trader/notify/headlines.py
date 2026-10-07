"""The latest news titles of a market from the TradingView MCP (``TRADINGVIEW_MCP_TOKEN``) for the Telegram messages:
context for the trader, never an input to a trade (no history of headlines exists to test one on). Cached per symbol;
a missing token, a failed call or an odd payload gives no lines and never an error."""
from __future__ import annotations

import html
import os
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd


def _default_client():
    token = os.environ.get("TRADINGVIEW_MCP_TOKEN")
    if not token:
        return None
    from ..data.tradingview_mcp import TradingViewMCPClient
    return TradingViewMCPClient(access_token=token, timeout=10.0)


class Headlines:
    """``lines(symbol, now)``: up to ``max_items`` titles of the last ``max_age_hours``, newest first, as
    "HH:MM provider: title" in ``tz``; the symbol's news is read at most once per ``ttl_minutes`` (a failed read too)."""

    def __init__(self, max_items: int = 3, max_age_hours: float = 24.0, ttl_minutes: float = 15.0,
                 client_factory: Optional[Callable[[], object]] = None, tz: str = "Europe/Amsterdam"):
        self.max_items = int(max_items)
        self.max_age = pd.Timedelta(hours=float(max_age_hours))
        self.ttl = pd.Timedelta(minutes=float(ttl_minutes))
        self.client_factory = client_factory or _default_client
        self.tz = tz
        self._client = None
        self._cache: Dict[str, Tuple[pd.Timestamp, List[dict]]] = {}

    def lines(self, symbol: str, now) -> List[str]:
        now = pd.Timestamp(now)
        if self.max_items <= 0:
            return []
        try:
            cached = self._cache.get(symbol)
            if cached is None or now - cached[0] >= self.ttl:
                self._cache[symbol] = (now, [])          # a failed read waits its turn as well
                if self._client is None:
                    self._client = self.client_factory()
                if self._client is None:
                    return []
                self._cache[symbol] = (now, list(self._client.get_news(symbol, limit=20) or []))
            items = self._cache[symbol][1]
        except Exception as exc:
            print(f"[live] headlines for {symbol} not read ({type(exc).__name__}: {exc})")
            return []
        out: List[str] = []
        for h in sorted((h for h in items if isinstance(h, dict)), key=lambda h: h.get("published") or 0, reverse=True):
            if not h.get("published") or not h.get("title"):
                continue
            ts = pd.Timestamp(int(h["published"]), unit="s")
            if now - ts > self.max_age:
                continue
            provider = h.get("provider")
            name = provider.get("name", "") if isinstance(provider, dict) else str(provider or "")
            local = ts.tz_localize("UTC").tz_convert(self.tz)
            out.append(f"{local:%H:%M} {html.escape(name)}: {html.escape(str(h['title'])[:120])}".replace(" : ", ": "))
            if len(out) >= self.max_items:
                break
        return out
