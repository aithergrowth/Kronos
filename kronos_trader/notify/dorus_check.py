"""The Dorus check per trade (Max, 8 October 2026): the setup the bot just took, with its charts, read by Claude through
the Anthropic Messages API the way Dorus reads a chart (``docs/DORUS_REVIEW.md``). Advice in Telegram: it never places,
blocks or changes a trade. Every verdict goes into ``dorus_checks.csv`` next to the journal, so that after enough trades
the verdicts can be held against the results before anyone lets the check veto a trade.

It needs two environment variables on the computer that runs the bot, set there by Max and never written into a file
of this repository: ``ANTHROPIC_API_KEY`` and ``DORUS_CHECK_MODEL`` (the model id). Without either the check is off.
"""
from __future__ import annotations

import base64
import csv
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
ICONS = {"eens": "✅", "let op": "⚠️", "niet": "❌"}
RUBRIC_PATH = Path(__file__).resolve().parents[2] / "docs" / "DORUS_REVIEW.md"
SYSTEM = ("You review one trade of a rules-based trading bot that follows Dorus Wanders' method, the way Dorus reads a chart. "
          "You get the bot's setup, its bias per timeframe and its charts. Judge only what the charts and the numbers show.")
ANSWER = ('Answer with one JSON object and nothing else: {"verdict": "eens" | "let op" | "niet", "reason": "<at most two '
          'short sentences in Dutch, in Dorus\'s words: liquiditeit, demand, supply, balance level, balance shift, BOS>"}')
CSV_FIELDS = ["time", "symbol", "id", "direction", "zone_tf", "entry", "stop", "target", "rr", "verdict", "reason"]


@dataclass
class Verdict:
    verdict: str          # eens, let op or niet
    reason: str

    @property
    def icon(self) -> str:
        return ICONS.get(self.verdict, "❔")


def parse_verdict(text: str) -> Verdict:
    """The JSON object in the model's answer; an answer that is not one reads as "let op" with the text as reason."""
    match = re.search(r"\{.*\}", text or "", flags=re.S)
    if match:
        try:
            data = json.loads(match.group(0))
            verdict = str(data.get("verdict", "")).strip().lower()
            if verdict in ICONS:
                return Verdict(verdict, str(data.get("reason", "")).strip())
        except (ValueError, AttributeError):
            pass
    return Verdict("let op", "antwoord niet leesbaar: " + (text or "").strip()[:160])


class DorusCheck:
    """``review(context, images)`` -> a ``Verdict``. ``post`` replaces the HTTP call (tests)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: float = 60.0,
                 rubric: Optional[str] = None, post: Optional[Callable[[dict], dict]] = None):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "") if api_key is None else api_key
        self.model = os.environ.get("DORUS_CHECK_MODEL", "") if model is None else model
        self.timeout = timeout
        if rubric is None:
            rubric = RUBRIC_PATH.read_text(encoding="utf-8") if RUBRIC_PATH.exists() else ""
        self.rubric = rubric
        self._post = post or self._http_post

    @property
    def available(self) -> bool:
        return bool(self.api_key and self.model)

    def _http_post(self, body: dict) -> dict:
        request = urllib.request.Request(API_URL, data=json.dumps(body).encode("utf-8"), method="POST", headers={
            "x-api-key": self.api_key, "anthropic-version": API_VERSION, "content-type": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def request_body(self, context: str, images: Sequence[Tuple[str, bytes]]) -> dict:
        content: List[Dict] = []
        for label, png in images:
            content.append({"type": "text", "text": label})
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.b64encode(png).decode("ascii")}})
        content.append({"type": "text", "text": f"{context}\n\n{ANSWER}"})
        system = SYSTEM + ("\n\n" + self.rubric if self.rubric else "")
        return {"model": self.model, "max_tokens": 600, "system": system, "messages": [{"role": "user", "content": content}]}

    def review(self, context: str, images: Sequence[Tuple[str, bytes]] = ()) -> Verdict:
        answer = self._post(self.request_body(context, images))
        text = "".join(block.get("text", "") for block in answer.get("content", []) if block.get("type") == "text")
        return parse_verdict(text)


def log_verdict(path: Path, row: Dict[str, object]) -> None:
    """Append one verdict to ``dorus_checks.csv`` (header on the first row)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        if new:
            writer.writeheader()
        writer.writerow(row)
