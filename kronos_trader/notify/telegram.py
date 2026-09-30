"""Telegram notifications through the Bot API (no extra dependency beyond ``requests``)."""
from __future__ import annotations

import os
from typing import Optional

from ..config import SymbolSpec, TelegramParams
from ..core.types import Analysis, ForecastSummary, TradeSetup
from .formatting import format_analysis, format_setup

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None, parse_mode: str = "HTML",
                 dry_run: bool = False, params: Optional[TelegramParams] = None, timeout: float = 15.0):
        params = params or TelegramParams()
        self.token = token or params.bot_token
        self.chat_id = chat_id or params.chat_id
        self.parse_mode = parse_mode or params.parse_mode
        self.dry_run = dry_run or not (self.token and self.chat_id)
        self.timeout = timeout
        self.sent: list = []

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, text: str) -> bool:
        self.sent.append(text)
        if self.dry_run:
            print("[telegram dry-run]\n" + text)
            return False
        import requests
        resp = requests.post(
            API.format(token=self.token, method="sendMessage"),
            json={"chat_id": self.chat_id, "text": text[:4000], "parse_mode": self.parse_mode,
                  "disable_web_page_preview": True},
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Telegram sendMessage failed: {resp.status_code} {resp.text[:200]}")
        return True

    def send_setup(self, setup: TradeSetup, forecast: Optional[ForecastSummary] = None, spec: Optional[SymbolSpec] = None) -> bool:
        return self.send("🚨 " + format_setup(setup, forecast, spec))

    def send_analysis(self, analysis: Analysis, spec: Optional[SymbolSpec] = None) -> bool:
        return self.send(format_analysis(analysis, spec))

    def test(self) -> bool:
        return self.send("kronos_trader connected ✅")
