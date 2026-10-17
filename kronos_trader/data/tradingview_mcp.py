"""TradingView data via the official TradingView MCP server.

Two ways to get TradingView data into the system:

1. **Claude Code as the bridge** (works today).  Claude Code with the
   TradingView MCP connected calls ``mcp-tv-get-ohlcv`` and writes the bars
   into the CSV cache (``kronos_trader.data.tv_cache``); the engine reads the
   cache.  No tokens live in this repository.
2. **Direct client** (``TradingViewMCPClient``).  A minimal MCP
   "streamable HTTP" client that talks JSON-RPC to
   ``https://mcp.tradingview.com/mcp`` with an OAuth bearer token
   (``TRADINGVIEW_MCP_TOKEN``).  The tool names and payload shapes below were
   taken from the live server; ``discover_tools`` re-checks them at runtime.

Payload of ``mcp-tv-get-ohlcv``::

    {"symbol": "OANDA:EURUSD", "interval": "1D", "count": 5,
     "bars": [{"t": 1790197200, "o": 1.13826, "h": 1.13992, "l": 1.13591, "c": 1.13801, "v": 410816}, ...],
     "summary": {...}, "notice": "bars are delayed 15+ minutes ..."}
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe

#: interval strings accepted by ``mcp-tv-get-ohlcv``
TV_INTERVALS: Dict[Timeframe, str] = {
    Timeframe.MIN_1: "1m",
    Timeframe.MIN_5: "5m",
    Timeframe.MIN_15: "15m",
    Timeframe.MIN_30: "30m",
    Timeframe.H_1: "1h",
    Timeframe.H_4: "4h",
    Timeframe.D_1: "1D",
    Timeframe.W_1: "1W",
    Timeframe.MN_1: "1mo",
}

#: tool names on the official server (verified 2026-09-30)
TOOL_NAMES = {
    "ohlcv": "mcp-tv-get-ohlcv",
    "news": "mcp-tv-get-news",
    "news_story": "mcp-tv-get-news-story",
    "symbol_data": "mcp-tv-get-symbol-data",
    "search": "mcp-tv-search-symbols",
    "calendar": "mcp-tv-get-economic-calendar",
    "technicals": "mcp-tv-get-technicals-rating",
}

MAX_BARS_PER_REQUEST = 5000


def parse_ohlcv_payload(payload: Any, timeframe: Timeframe, symbol: Optional[str] = None) -> CandleSeries:
    """Turn the tool payload (dict, list of bars or JSON text) into a ``CandleSeries``."""
    if isinstance(payload, str):
        payload = json.loads(payload)
    if isinstance(payload, dict):
        bars = payload.get("bars")
        symbol = symbol or payload.get("symbol")
        if bars is None:
            raise ValueError("payload has no 'bars' (was summary=true used?)")
    else:
        bars = payload
    if not bars:
        raise ValueError("payload contains no bars")
    df = pd.DataFrame(bars)
    rename = {"t": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    if "timestamp" not in df.columns:
        raise ValueError(f"bars have no 't' field: {list(df.columns)}")
    if pd.api.types.is_numeric_dtype(df["timestamp"]):
        unit = "ms" if df["timestamp"].max() > 1e12 else "s"
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit=unit)
    if "volume" not in df.columns:
        df["volume"] = 0.0
    return CandleSeries(df[["timestamp", "open", "high", "low", "close", "volume"]], timeframe, symbol)


class TradingViewMCPClient:
    """Minimal MCP client for the official TradingView server (streamable HTTP transport)."""

    def __init__(self, url: str = "https://mcp.tradingview.com/mcp", access_token: Optional[str] = None,
                 timeout: float = 30.0, session=None):
        import requests  # optional dependency for the direct client only
        self.url = url
        self.token = access_token
        self.timeout = timeout
        self.http = session or requests.Session()
        self.session_id: Optional[str] = None
        self.tools: List[Dict[str, Any]] = []
        self._initialized = False

    # ------------------------------------------------------------ transport
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        return headers

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None, notification: bool = False) -> Any:
        body: Dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notification:
            body["id"] = str(uuid.uuid4())
        resp = self.http.post(self.url, headers=self._headers(), json=body, timeout=self.timeout)
        sid = resp.headers.get("Mcp-Session-Id")
        if sid:
            self.session_id = sid
        if resp.status_code == 401:
            raise PermissionError("TradingView MCP rejected the token (401). Sign in via OAuth and set TRADINGVIEW_MCP_TOKEN.")
        resp.raise_for_status()
        if notification or not resp.content:
            return None
        message = self._parse_body(resp)
        if "error" in message:
            raise RuntimeError(f"MCP error for {method}: {message['error']}")
        return message.get("result")

    @staticmethod
    def _parse_body(resp) -> Dict[str, Any]:
        ctype = resp.headers.get("Content-Type", "")
        if "text/event-stream" in ctype:
            last: Optional[Dict[str, Any]] = None
            for line in resp.text.splitlines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        try:
                            last = json.loads(data)
                        except json.JSONDecodeError:
                            continue
            if last is None:
                raise RuntimeError("empty event stream from MCP server")
            return last
        return resp.json()

    def initialize(self) -> None:
        if self._initialized:
            return
        self._rpc("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "kronos_trader", "version": "0.1.0"},
        })
        self._rpc("notifications/initialized", notification=True)
        self._initialized = True

    # ------------------------------------------------------------ tools
    def discover_tools(self) -> List[Dict[str, Any]]:
        self.initialize()
        result = self._rpc("tools/list") or {}
        self.tools = result.get("tools", [])
        names = {t["name"] for t in self.tools}
        for key, wanted in TOOL_NAMES.items():
            if wanted not in names:
                match = next((n for n in names if wanted.replace("mcp-tv-", "") in n), None)
                if match:
                    TOOL_NAMES[key] = match
        return self.tools

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        self.initialize()
        result = self._rpc("tools/call", {"name": name, "arguments": arguments}) or {}
        if result.get("isError"):
            raise RuntimeError(f"tool {name} failed: {result}")
        if "structuredContent" in result:
            return result["structuredContent"]
        for item in result.get("content", []):
            if item.get("type") == "text":
                text = item.get("text", "")
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return result

    # ------------------------------------------------------------ data
    def get_ohlcv(self, symbol: str, timeframe: Timeframe, count: int = 300) -> CandleSeries:
        timeframe = Timeframe.parse(timeframe)
        payload = self.call_tool(TOOL_NAMES["ohlcv"], {
            "symbol": symbol, "interval": TV_INTERVALS[timeframe], "count": min(int(count), MAX_BARS_PER_REQUEST)})
        return parse_ohlcv_payload(payload, timeframe, symbol)

    def get_multi(self, symbol: str, timeframes: List[Timeframe], counts: Optional[Dict[Timeframe, int]] = None) -> Dict[Timeframe, CandleSeries]:
        out: Dict[Timeframe, CandleSeries] = {}
        for tf in timeframes:
            tf = Timeframe.parse(tf)
            out[tf] = self.get_ohlcv(symbol, tf, (counts or {}).get(tf, 300))
        return out

    def get_news(self, symbol: str, limit: int = 25, offset: int = 0, lang: str = "en") -> List[Dict[str, Any]]:
        payload = self.call_tool(TOOL_NAMES["news"], {"symbol": symbol, "limit": limit, "offset": offset, "lang": lang})
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        return data.get("headlines", []) if isinstance(data, dict) else data

    def get_news_story(self, story_id: str) -> Dict[str, Any]:
        return self.call_tool(TOOL_NAMES["news_story"], {"id": story_id})

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        payload = self.call_tool(TOOL_NAMES["symbol_data"], {
            "symbol": symbol,
            "columns": ["name", "description", "close", "change", "update_mode", "bid", "ask", "high", "low", "open", "pricescale", "minmov"],
        })
        return payload.get("data", payload) if isinstance(payload, dict) else payload

    def get_economic_calendar(self, currencies: str = "USD,EUR", date_from: Optional[str] = None,
                              date_to: Optional[str] = None, min_importance: int = 1) -> List[Dict[str, Any]]:
        args: Dict[str, Any] = {"currencies": currencies, "min_importance": min_importance}
        if date_from:
            args["date_from"] = date_from
        if date_to:
            args["date_to"] = date_to
        payload = self.call_tool(TOOL_NAMES["calendar"], args)
        return payload.get("result", payload) if isinstance(payload, dict) else payload

    def search_symbols(self, query: str, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        args: Dict[str, Any] = {"query": query}
        if type_filter:
            args["type_filter"] = type_filter
        payload = self.call_tool(TOOL_NAMES["search"], args)
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        return data.get("symbols", []) if isinstance(data, dict) else data


def news_blackout_windows(events: List[Dict[str, Any]], minutes_before: int, minutes_after: int) -> List[tuple]:
    """``(start, end)`` UTC windows around high-impact calendar events."""
    windows = []
    for ev in events:
        when = ev.get("date")
        if not when:
            continue
        ts = pd.Timestamp(when)
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC").tz_localize(None)
        windows.append((ts - pd.Timedelta(int(minutes_before), unit="min"), ts + pd.Timedelta(int(minutes_after), unit="min"),
                        f"{ev.get('currency', '')} {ev.get('title', ev.get('indicator', ''))}"))
    return windows
