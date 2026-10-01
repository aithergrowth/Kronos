"""High-impact news calendar and the entry blackout around it.

Dorus discusses avoiding an entry immediately before news and retaining a
plan-compliant open trade (source G, 11:08-11:24). The configurable blackout
here rejects new signals before and after relevant high-impact events. Its
30-minute default windows are implementation choices, not stated durations
from that source. Events come from a CSV
(``data/calendar/high_impact.csv``, filled from the TradingView economic
calendar for backtests) and, on the laptop, from the free ForexFactory weekly
feed, which needs no key.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import pandas as pd

from ..config import SymbolSpec

FOREXFACTORY_URL = "https://nfs.faireconomy.media/ff_calendar_{week}.json"
IMPACT = {"high": 1, "medium": 0, "low": -1, "holiday": -1}
NON_CURRENCIES = {"XAU", "XAG", "BTC", "ETH", "NAS", "US3", "SPX", "US1", "GER", "UK1"}


@dataclass(frozen=True)
class NewsEvent:
    time: pd.Timestamp          # naive UTC
    currency: str
    title: str
    importance: int = 1         # 1 high, 0 medium, -1 low

    def as_row(self) -> Dict[str, Any]:
        return {"time": self.time.strftime("%Y-%m-%d %H:%M"), "currency": self.currency, "importance": self.importance,
                "title": self.title}


def _utc(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_convert("UTC").tz_localize(None) if ts.tzinfo is not None else ts


def currencies_of(symbol: str, spec: Optional[SymbolSpec] = None) -> Set[str]:
    """Currencies whose news matter for ``symbol``: EURUSD -> EUR, USD; gold, indices and crypto -> USD."""
    symbol = symbol.upper()
    out: Set[str] = set()
    if len(symbol) == 6 and symbol.isalpha():
        for part in (symbol[:3], symbol[3:]):
            out.add("USD" if part in NON_CURRENCIES else part)
    else:
        out.add("USD")
    return out


def from_tradingview(payload: Any) -> List[NewsEvent]:
    """Events from the ``mcp-tv-get-economic-calendar`` result (list or ``{"result": [...]}``)."""
    rows = payload.get("result", payload) if isinstance(payload, dict) else payload
    out: List[NewsEvent] = []
    for r in rows or []:
        if not r.get("date") or not r.get("currency"):
            continue
        out.append(NewsEvent(_utc(r["date"]), str(r["currency"]).upper(), str(r.get("title") or r.get("indicator") or ""),
                             int(r.get("importance", 0) or 0)))
    return out


def from_forexfactory(payload: Any) -> List[NewsEvent]:
    """Events from the ForexFactory weekly JSON (``title, country, date, impact``)."""
    out: List[NewsEvent] = []
    for r in payload or []:
        if not r.get("date") or not r.get("country"):
            continue
        out.append(NewsEvent(_utc(r["date"]), str(r["country"]).upper(), str(r.get("title", "")),
                             IMPACT.get(str(r.get("impact", "")).lower(), -1)))
    return out


def fetch_forexfactory(week: str = "thisweek", session=None, timeout: float = 15.0) -> List[NewsEvent]:
    if session is None:
        import requests
        session = requests.Session()
    r = session.get(FOREXFACTORY_URL.format(week=week), timeout=timeout, headers={"User-Agent": "kronos_trader"})
    if r.status_code != 200:
        raise RuntimeError(f"ForexFactory calendar {r.status_code}")
    return from_forexfactory(r.json())


def save_events(events: Iterable[NewsEvent], path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted({e.as_row()["time"] + e.currency + e.title: e for e in events}.values(), key=lambda e: (e.time, e.currency))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time", "currency", "importance", "title"])
        w.writeheader()
        for e in rows:
            w.writerow(e.as_row())
    return path


def load_events(path) -> List[NewsEvent]:
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return [NewsEvent(pd.Timestamp(r["time"]), r["currency"].upper(), r["title"], int(r["importance"] or 0))
                for r in csv.DictReader(f)]


class NewsCalendar:
    """Answers "is ``ts`` inside the blackout of a high-impact event for ``symbol``?"."""

    def __init__(self, events: Iterable[NewsEvent] = (), before_minutes: int = 30, after_minutes: int = 30,
                 min_importance: int = 1):
        self.before = pd.Timedelta(int(before_minutes), unit="min")
        self.after = pd.Timedelta(int(after_minutes), unit="min")
        self.min_importance = min_importance
        self.events: List[NewsEvent] = []
        self.add(events)

    def add(self, events: Iterable[NewsEvent]) -> None:
        known = {(e.time, e.currency, e.title) for e in self.events}
        for e in events:
            if e.importance >= self.min_importance and (e.time, e.currency, e.title) not in known:
                self.events.append(e)
                known.add((e.time, e.currency, e.title))
        self.events.sort(key=lambda e: e.time)

    def blackout(self, symbol: str, ts, spec: Optional[SymbolSpec] = None) -> Optional[NewsEvent]:
        ts = pd.Timestamp(ts)
        wanted = currencies_of(symbol, spec)
        for e in self.events:
            if e.currency in wanted and e.time - self.before <= ts <= e.time + self.after:
                return e
        return None

    def upcoming(self, symbol: str, ts, within_minutes: int = 240) -> List[NewsEvent]:
        ts = pd.Timestamp(ts)
        wanted = currencies_of(symbol)
        return [e for e in self.events if e.currency in wanted and ts <= e.time <= ts + pd.Timedelta(within_minutes, unit="min")]
