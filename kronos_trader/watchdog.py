"""A watchdog beside the live windows: it reads their heartbeats (``heartbeat_<symbol>.json`` next to the journal) and
says on Telegram what a window cannot say itself.

- a window without a heartbeat for ``max_age_minutes``: stopped, crashed, or the computer slept;
- a window whose MT5 link has been down, or whose scans have failed, for ``down_minutes``;
- a news calendar with no event ahead on a Monday to Thursday (this week's ForexFactory file always has some then;
  from Friday the next week's file is often not out yet, so an empty week end is normal).

One message when a problem starts and one when it is over. It runs on the same computer, so it cannot report that the
computer itself is off or asleep: that is visible in the morning briefing that does not come, and outside help (a
service the heartbeat pings) is the only cover for it.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd


def read_heartbeats(folder) -> Dict[str, dict]:
    beats: Dict[str, dict] = {}
    for path in sorted(Path(folder).glob("heartbeat_*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue                                   # being replaced at this moment: next round
        beats[str(doc.get("symbol") or path.stem.replace("heartbeat_", ""))] = doc
    return beats


def problems(beats: Dict[str, dict], now: pd.Timestamp, max_age_minutes: float = 5.0,
             down_minutes: float = 15.0) -> Dict[Tuple[str, str], str]:
    """The current problems as ``{(symbol, kind): message}``; kinds: silent, down, calendar."""
    out: Dict[Tuple[str, str], str] = {}
    for symbol, b in beats.items():
        seen = pd.Timestamp(b.get("time")) if b.get("time") else None
        if seen is None or now - seen > pd.Timedelta(minutes=max_age_minutes):
            since = f"{seen:%a %H:%M} UTC" if seen is not None else "the start"
            out[(symbol, "silent")] = (f"🚨 {symbol}: no scan since {since}: the window stopped, crashed or the computer "
                                       f"slept. Restart it (scripts\\start_ftmo.bat restarts every window).")
            continue
        ok = pd.Timestamp(b["last_scan_ok"]) if b.get("last_scan_ok") else None
        if b.get("state") != "ok" and (ok is None or now - ok > pd.Timedelta(minutes=down_minutes)):
            since = f"{ok:%a %H:%M} UTC" if ok is not None else "the start"
            out[(symbol, "down")] = (f"⚠️ {symbol}: no good scan since {since} ({b.get('state')}: "
                                     f"{b.get('detail') or 'no detail'}). Check the MT5 terminal and the window.")
        if b.get("news") and now.weekday() <= 3:
            until = pd.Timestamp(b["calendar_until"]) if b.get("calendar_until") else None
            if until is None or until < now:
                reach = f"ended {until:%a %d %b %H:%M} UTC" if until is not None else "is empty"
                out[(symbol, "calendar")] = (f"📰 {symbol}: the news calendar {reach}, no event ahead this week: the news "
                                             f"blackout sees nothing (ForexFactory not reached?).")
    return out


class Watchdog:
    def __init__(self, folder, send: Callable[[str], None], clock: Optional[Callable[[], pd.Timestamp]] = None,
                 max_age_minutes: float = 5.0, down_minutes: float = 15.0):
        self.folder, self.send = Path(folder), send
        self.clock = clock or (lambda: pd.Timestamp.now("UTC").tz_localize(None))
        self.limits = dict(max_age_minutes=max_age_minutes, down_minutes=down_minutes)
        self.open: Dict[Tuple[str, str], str] = {}

    def check(self) -> List[str]:
        """One round: a message for each new problem and for each one that is over; returns what it sent."""
        now = self.clock()
        current = problems(read_heartbeats(self.folder), now, **self.limits)
        sent: List[str] = []
        for key, text in current.items():
            if key not in self.open:
                sent.append(text)
        for key in list(self.open):
            if key not in current:
                symbol, kind = key
                sent.append({"silent": f"✅ {symbol}: scanning again.", "down": f"✅ {symbol}: scans run through again.",
                             "calendar": f"✅ {symbol}: the news calendar reaches far enough again."}[kind])
        self.open = current
        for text in sent:
            self.send(text)
        return sent

    def run_forever(self, every_seconds: float = 60.0) -> None:
        while True:
            try:
                self.check()
            except Exception as exc:                   # a bad file or a Telegram hiccup: say it on the console, go on
                print(f"[watchdog] {type(exc).__name__}: {exc}")
            time.sleep(every_seconds)
