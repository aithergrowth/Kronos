"""Telegram notifications and the approve / skip flow (Bot API, ``requests`` only).

Messages: setups, fills, break-even moves, closes.  Approval requests carry an
inline keyboard; ``poll_decisions`` reads the taps (or ``/approve <id>`` and
``/skip <id>`` texts) and only accepts them from the configured chat.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..config import SymbolSpec, TelegramParams
from ..core.types import Analysis, ForecastSummary, TradeSetup
from .formatting import format_analysis, format_setup

API = "https://api.telegram.org/bot{token}/{method}"


def clean_token(token: Optional[str]) -> Optional[str]:
    """The token as BotFather gives it: surrounding whitespace and quotes dropped, a pasted ``bot`` prefix removed."""
    if not token:
        return None
    token = token.strip().strip("\"'").strip()
    if token[:3].lower() == "bot" and token[3:4].isdigit():
        token = token[3:]
    return token or None


def masked(token: Optional[str]) -> str:
    """The token's shape for a message: first four and last two characters, length; never the token."""
    if not token:
        return "(empty)"
    return f"{token[:4]}...{token[-2:]} ({len(token)} characters)"


class TelegramError(RuntimeError):
    def __init__(self, method: str, status: int, description: str, retry_after: Optional[float] = None):
        super().__init__(f"Telegram {method} failed: {status} {description}")
        self.method, self.status, self.description, self.retry_after = method, status, description, retry_after


@dataclass
class Decision:
    short_id: str
    approved: bool
    user_id: Optional[int] = None
    via: str = "button"


class TelegramNotifier:
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None, parse_mode: str = "HTML",
                 dry_run: bool = False, params: Optional[TelegramParams] = None, timeout: float = 15.0,
                 allowed_user_ids: Optional[List[int]] = None):
        params = params or TelegramParams()
        self.token = clean_token(token or params.bot_token)
        self.chat_id = (chat_id or params.chat_id or "").strip() or None
        self.parse_mode = parse_mode or params.parse_mode
        self.dry_run = dry_run or not (self.token and self.chat_id)
        self.timeout = timeout
        self.allowed_user_ids = set(allowed_user_ids or [])
        self.sent: list = []
        self._offset: Optional[int] = None
        self._queued: List[Decision] = []
        self._warned_at = 0.0
        self.prefix = ""                     # e.g. "[FTMO] ": which account a message is about when two run side by side

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    # ------------------------------------------------------------ transport
    def _call(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        import requests
        resp = requests.post(API.format(token=self.token, method=method), json=payload, timeout=self.timeout)
        if resp.status_code != 200:
            retry_after = None
            try:
                body = resp.json()
                description = str(body.get("description", resp.text[:200]))
                retry_after = (body.get("parameters") or {}).get("retry_after")
            except ValueError:
                description = resp.text[:200]
            raise TelegramError(method, resp.status_code, description, retry_after)
        return resp.json()

    def _warn(self, text: str) -> None:
        """A delivery problem on the console, at most once a minute (the scan goes on without the message)."""
        now = time.time()
        if now - self._warned_at >= 60:
            self._warned_at = now
            print(f"[telegram] {text}", flush=True)

    def check(self) -> str:
        """``getMe``: the bot's username when the token is accepted (TelegramError otherwise)."""
        me = self._call("getMe", {}).get("result") or {}
        return str(me.get("username") or me.get("first_name") or "?")

    def chats_seen(self) -> List[Dict[str, Any]]:
        """The chats that have messaged the bot, from ``getUpdates``: ``[{"id": ..., "name": ...}]``, newest last.
        A chat shows up only after someone sent the bot a message, and updates older than 24 h are gone."""
        seen: Dict[int, Dict[str, Any]] = {}
        for update in self._call("getUpdates", {"timeout": 0}).get("result") or []:
            msg = update.get("message") or update.get("edited_message") or update.get("channel_post") or {}
            chat = msg.get("chat") or {}
            if "id" in chat:
                name = chat.get("username") or " ".join(x for x in (chat.get("first_name"), chat.get("last_name")) if x) \
                    or chat.get("title") or chat.get("type") or ""
                seen[int(chat["id"])] = {"id": int(chat["id"]), "name": name}
        return list(seen.values())

    def send(self, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        text = f"{self.prefix}{text}" if self.prefix else text
        self.sent.append(text)
        if self.dry_run:
            print("[telegram dry-run]\n" + text)
            return False
        payload: Dict[str, Any] = {"chat_id": self.chat_id, "text": text[:4000], "parse_mode": self.parse_mode,
                                   "disable_web_page_preview": True}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        # never raises: a message is not worth a scan, let alone the process (an error text with a "<" in it was not
        # valid HTML, Telegram answered 400, and the second failure inside the loop's error handler ended the window)
        for attempt in range(3):
            try:
                self._call("sendMessage", payload)
                return True
            except TelegramError as exc:
                if exc.status == 400 and "parse" in exc.description.lower() and payload.get("parse_mode"):
                    payload = {k: v for k, v in payload.items() if k != "parse_mode"}     # send the text as it is
                    continue
                if exc.status == 429 and attempt < 2:
                    time.sleep(min(10.0, float(exc.retry_after or 1.0)))
                    continue
                self._warn(f"message not sent: {exc}")
                return False
            except Exception as exc:                     # no network, a timeout
                self._warn(f"message not sent: {exc}")
                return False
        return False

    def send_photo(self, path, caption: str = "") -> bool:
        """sendPhoto with an optional caption; in dry-run the path is printed."""
        caption = f"{self.prefix}{caption}" if self.prefix else caption
        self.sent.append(f"[photo] {path} {caption}".strip())
        if self.dry_run:
            print(f"[telegram dry-run photo] {path}\n{caption}")
            return False
        import requests
        try:
            with open(path, "rb") as fh:
                r = requests.post(API.format(token=self.token, method="sendPhoto"), data={"chat_id": self.chat_id, "caption": caption[:1000],
                                                                       "parse_mode": self.parse_mode},
                                  files={"photo": fh}, timeout=self.timeout * 2)
            return r.ok
        except Exception as exc:                         # never raises, as send
            self._warn(f"chart not sent: {exc}")
            return False

    # ------------------------------------------------------------ messages
    def send_setup(self, setup: TradeSetup, forecast: Optional[ForecastSummary] = None, spec: Optional[SymbolSpec] = None) -> bool:
        return self.send("🚨 " + format_setup(setup, forecast, spec))

    def send_analysis(self, analysis: Analysis, spec: Optional[SymbolSpec] = None) -> bool:
        return self.send(format_analysis(analysis, spec))

    def send_approval_request(self, setup: TradeSetup, short_id: str, forecast: Optional[ForecastSummary] = None,
                              spec: Optional[SymbolSpec] = None, expires_at=None) -> bool:
        lines = ["⏳ <b>APPROVAL NEEDED</b>", format_setup(setup, forecast, spec)]
        if expires_at is not None:
            lines.append(f"Expires {expires_at:%Y-%m-%d %H:%M} UTC")
        lines.append(f"id <code>{short_id}</code>  (or reply /approve {short_id} · /skip {short_id})")
        keyboard = {"inline_keyboard": [[
            {"text": "✅ Approve", "callback_data": f"approve:{short_id}"},
            {"text": "❌ Skip", "callback_data": f"skip:{short_id}"},
        ]]}
        return self.send("\n".join(lines), reply_markup=keyboard)

    def test(self) -> bool:
        """One message straight through the API: unlike send(), a refusal (a wrong chat id) raises TelegramError, so the
        telegram-test command can say what is wrong."""
        text = f"{self.prefix}kronos_trader connected ✅"
        self.sent.append(text)
        if self.dry_run:
            print("[telegram dry-run]\n" + text)
            return False
        self._call("sendMessage", {"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True})
        return True

    # ------------------------------------------------------------ decisions
    def queue_decision(self, short_id: str, approved: bool, user_id: Optional[int] = None) -> None:
        """Inject a decision (tests, or a local console in dry-run mode)."""
        self._queued.append(Decision(short_id, approved, user_id, via="queued"))

    def _authorised(self, user_id: Optional[int], chat_id: Optional[int]) -> bool:
        if user_id is not None and user_id in self.allowed_user_ids:
            return True
        return chat_id is not None and self.chat_id is not None and str(chat_id) == str(self.chat_id)

    def poll_decisions(self) -> List[Decision]:
        decisions: List[Decision] = list(self._queued)
        self._queued.clear()
        if self.dry_run:
            return decisions
        payload: Dict[str, Any] = {"timeout": 0, "allowed_updates": json.dumps(["callback_query", "message"])}
        if self._offset is not None:
            payload["offset"] = self._offset
        result = self._call("getUpdates", payload).get("result", [])
        for update in result:
            self._offset = int(update["update_id"]) + 1
            cq = update.get("callback_query")
            if cq:
                data = str(cq.get("data", ""))
                user_id = cq.get("from", {}).get("id")
                chat_id = cq.get("message", {}).get("chat", {}).get("id")
                verb, _, short_id = data.partition(":")
                ok = verb in ("approve", "skip") and short_id and self._authorised(user_id, chat_id)
                try:
                    self._call("answerCallbackQuery", {"callback_query_id": cq.get("id"),
                                                       "text": ("Approved ✅" if verb == "approve" else "Skipped") if ok else "Not allowed"})
                except Exception:
                    pass
                if ok:
                    decisions.append(Decision(short_id, verb == "approve", user_id, via="button"))
                continue
            msg = update.get("message")
            if msg and isinstance(msg.get("text"), str):
                parts = msg["text"].strip().split()
                if len(parts) == 2 and parts[0] in ("/approve", "/skip"):
                    user_id = msg.get("from", {}).get("id")
                    chat_id = msg.get("chat", {}).get("id")
                    if self._authorised(user_id, chat_id):
                        decisions.append(Decision(parts[1], parts[0] == "/approve", user_id, via="command"))
        return decisions
