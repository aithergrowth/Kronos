"""MetaTrader 5 broker adapter (Windows only, ``pip install MetaTrader5``).

Most prop firms hand out MT5 accounts, so this is the intended challenge
path, and any MT5 demo account (the MetaQuotes demo the terminal offers on
first start, or a broker's) doubles as a real-time candle feed plus paper
venue when the IBKR paper account has no market data.  The strategy and the
risk guard decide; this module only translates to ``order_send`` and reads
positions and deals back.

Server time: MT5 stamps candles and ticks in the broker's server time.  The
offset to UTC is estimated from the latest tick (rounded to 30 minutes) and
removed, so the engine's clock and the session windows stay in UTC; pin it
with ``MT5_SERVER_OFFSET_HOURS`` when the estimate is wrong.
"""
from __future__ import annotations

import glob
import os
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import MT5Params, Settings
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Direction
from .base import Broker, ClosedTrade, Position

MT5_TIMEFRAMES = {
    Timeframe.MIN_1: "TIMEFRAME_M1", Timeframe.MIN_5: "TIMEFRAME_M5", Timeframe.MIN_15: "TIMEFRAME_M15",
    Timeframe.MIN_30: "TIMEFRAME_M30", Timeframe.H_1: "TIMEFRAME_H1", Timeframe.H_4: "TIMEFRAME_H4",
    Timeframe.D_1: "TIMEFRAME_D1", Timeframe.W_1: "TIMEFRAME_W1", Timeframe.MN_1: "TIMEFRAME_MN1",
}


def utc_now() -> pd.Timestamp:
    return pd.Timestamp.now(tz="UTC").tz_localize(None)


HOUR = pd.Timedelta(1, unit="h")
NY_CLOSE_HOUR = 17          # the forex week ends Friday 17:00 New York; most servers put that instant at midnight
WEEK_CLOSE_BARS = 3 * 7 * 48  # three weeks of M30 bars: at least two weekend gaps to read the close from


def ny_utcoffset(ts_utc: pd.Timestamp) -> pd.Timedelta:
    """New York's offset to UTC at a UTC instant: -4 h under daylight saving, -5 h otherwise."""
    return pd.Timedelta(ts_utc.tz_localize("UTC").tz_convert("America/New_York").utcoffset())


def forex_week_open(ts_utc: pd.Timestamp) -> bool:
    """False from Friday 20:00 UTC to Sunday 23:00 UTC: the weekend close with an hour of slack on both sides."""
    wd, hour = ts_utc.weekday(), ts_utc.hour
    return not (wd == 5 or (wd == 4 and hour >= 20) or (wd == 6 and hour < 23))


def terminal_candidates() -> List[str]:
    """Where a 64-bit MT5 terminal usually lives on Windows (used when MT5_PATH is not set)."""
    patterns = [r"C:\Program Files\MetaTrader 5\terminal64.exe", r"C:\Program Files\*\terminal64.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\*\terminal64.exe")]
    found: List[str] = []
    for pattern in patterns:
        for hit in sorted(glob.glob(pattern)):
            if hit not in found:
                found.append(hit)
    return found


class MT5Broker(Broker):
    def __init__(self, settings: Optional[Settings] = None, params: Optional[MT5Params] = None,
                 api=None, connect: bool = True, clock=None):
        if api is None:
            try:
                import MetaTrader5 as api  # type: ignore
            except ImportError as exc:  # pragma: no cover - platform specific
                raise RuntimeError("MetaTrader5 package not available (Windows + `pip install MetaTrader5`)") from exc
        self.mt5 = api
        self.settings = settings or Settings()
        self.params = params or self.settings.mt5
        self.magic = self.params.magic
        self.deviation = self.params.deviation_points
        self.clock = clock or utc_now
        self._positions: Dict[str, Position] = {}
        self._closed: List[ClosedTrade] = []
        self._close_cursor = 0
        self._offset: Optional[pd.Timedelta] = None
        self._offset_at: Optional[pd.Timestamp] = None
        if connect:
            self.connect()

    # ------------------------------------------------------------ connection
    def connect(self) -> None:
        """Attach to the terminal (MT5_PATH, else the running one, else the usual install paths) and log in.

        The account comes from MT5_LOGIN / MT5_PASSWORD / MT5_SERVER when all three are set and is passed to
        ``initialize`` itself, so a terminal that sits at "authorization failed" on its last account (password not
        saved, demo expired) still connects with ours. Without them the terminal's current account is used.
        """
        p = self.params
        path = os.environ.get(p.path_env)
        login, password, server = os.environ.get(p.login_env), os.environ.get(p.password_env), os.environ.get(p.server_env)
        creds: Dict[str, Any] = {"login": int(login), "password": password, "server": server} if login and password and server else {}
        attempts: List[Optional[str]] = [path] if path else [None] + terminal_candidates()
        errors = []
        for candidate in attempts:
            kwargs: Dict[str, Any] = dict(creds)
            if candidate:
                kwargs["path"] = candidate
            if self.mt5.initialize(**kwargs):
                self.terminal_path = candidate
                break
            errors.append(f"{candidate or 'running terminal'}: {self.mt5.last_error()}")
        else:
            account = f" for login {login} on {server}" if creds else " on the terminal's current account"
            raise RuntimeError("MT5 initialize failed" + account + ": " + "; ".join(errors) + ". Start the terminal "
                               "and log in (Journal tab shows why a login fails), run PowerShell and the terminal as "
                               "the same user (not one of them as administrator), set MT5_PATH to the full path of "
                               "terminal64.exe, and check MT5_LOGIN / MT5_PASSWORD (the master password, not the "
                               "investor one) / MT5_SERVER on 'Authorization failed'")

    def disconnect(self) -> None:
        self.mt5.shutdown()

    # ------------------------------------------------------------ helpers
    retry_seconds: float = 1.0

    def find_symbols(self, text: str) -> List[str]:
        """Names of the server's symbols that contain ``text`` (case-insensitive), e.g. BTC -> BTCUSD, BTCEUR."""
        try:
            found = self.mt5.symbols_get(f"*{text.upper()}*") or self.mt5.symbols_get() or []
        except Exception:
            return []
        names = [getattr(x, "name", str(x)) for x in found]
        return sorted(n for n in names if text.upper() in n.upper())

    def symbol_details(self, name: str) -> Dict[str, Any]:
        """What the terminal says about one symbol: description, digits, contract size, volume limits, trade mode."""
        info = self.mt5.symbol_info(name)
        if info is None:
            return {"name": name, "found": False}
        keys = ("description", "digits", "point", "trade_contract_size", "volume_min", "volume_step", "volume_max",
                "trade_mode", "currency_profit", "spread")
        return {"name": name, "found": True, **{k: getattr(info, k, None) for k in keys}}

    def mt5_symbol(self, symbol: str) -> str:
        spec = self.settings.symbols.get(symbol.upper())
        return spec.mt5_symbol if spec and spec.mt5_symbol else symbol.upper()

    def our_symbol(self, name: str) -> str:
        for sym, spec in self.settings.symbols.items():
            if spec.mt5_symbol == name:
                return sym
        return name.upper()

    def server_offset(self, symbol: Optional[str] = None) -> pd.Timedelta:
        """Broker server time minus UTC.

        ``MT5_SERVER_OFFSET_HOURS`` pins it. Otherwise it is read from the last bar before the weekend gap (the
        forex week ends Friday 17:00 New York, see ``offset_from_week_close``) and, while the week is open,
        checked against the latest tick, which is exact when fresh: the tick wins when the two agree within
        1.5 hours (a broker that closes a little early), the week-close reading when the tick is stale (a
        holiday, a weekend) or the bars are missing. Re-read every hour so a daylight-saving switch is followed.
        """
        pinned = os.environ.get(self.params.offset_env)
        if pinned:
            return pd.Timedelta(float(pinned) * 60, unit="min")
        now = self.clock()
        if self._offset is not None and self._offset_at is not None and now - self._offset_at < HOUR:
            return self._offset
        name = self.offset_symbol(symbol)
        week = self.offset_from_week_close(name, now)
        tick = self.offset_from_tick(name, now) if forex_week_open(now) else None
        if tick is not None and (week is None or abs(tick - week) <= 1.5 * HOUR):
            offset = tick
        elif week is not None:
            offset = week
        else:
            offset = tick if tick is not None else pd.Timedelta(0)
        self._offset, self._offset_at = offset, now
        return offset

    def offset_symbol(self, symbol: Optional[str] = None) -> str:
        """The symbol the offset is read from: EURUSD when it is configured (its week ends on the New York close
        on every broker), else the symbol asked for, else the first configured one."""
        if "EURUSD" in self.settings.symbols:
            return self.mt5_symbol("EURUSD")
        return self.mt5_symbol(symbol or next(iter(self.settings.symbols)))

    def offset_from_tick(self, name: str, now: pd.Timestamp) -> Optional[pd.Timedelta]:
        """The latest tick's server stamp against the clock, rounded to half hours; None when that is not a
        plausible offset (-12 h to +14 h), which means the tick is stale."""
        tick = self.mt5.symbol_info_tick(name)
        seconds = int(getattr(tick, "time", 0) or 0) if tick is not None else 0
        if not seconds:
            return None
        raw = (pd.Timestamp(seconds, unit="s") - now).total_seconds()
        if not -12 * 3600 <= raw <= 14 * 3600:
            return None
        return pd.Timedelta(round(raw / 1800.0) * 30, unit="min")

    def offset_from_week_close(self, name: str, now: pd.Timestamp) -> Optional[pd.Timedelta]:
        """The offset read from the last M30 bar before a weekend gap.

        The forex week ends Friday 17:00 New York, so that bar starts 30 minutes before that instant in UTC and
        its server stamp minus that start is the offset. A server whose week ends at 23:30 keeps its midnight on
        the New York close and follows US daylight saving with it: its offset now is New York's plus 7 hours.
        Gaps that match no Friday within 14 hours (a holiday) are skipped; None without a usable gap.
        """
        try:
            self.mt5.symbol_select(name, True)
            rates = self.mt5.copy_rates_from_pos(name, self.mt5.TIMEFRAME_M30, 0, WEEK_CLOSE_BARS)
        except Exception:                                   # pragma: no cover - terminal hiccup, tick fallback
            return None
        if rates is None or len(rates) < 2:
            return None
        t = np.asarray(rates["time"], dtype="int64")
        for i in reversed(np.where(np.diff(t) >= 24 * 3600)[0]):
            last = pd.Timestamp(int(t[i]), unit="s")       # server wall time of the week's last bar
            best = None
            for days in (-1, 0, 1):
                day = (last + pd.Timedelta(days, unit="D")).normalize()
                if day.weekday() != 4:
                    continue
                close_utc = ((day + pd.Timedelta(NY_CLOSE_HOUR, unit="h")).tz_localize("America/New_York")
                             .tz_convert("UTC").tz_localize(None))
                offset = last - (close_utc - pd.Timedelta(30, unit="min"))
                if abs(offset) <= 14 * HOUR and (best is None or abs(offset) < abs(best[0])):
                    best = (offset, close_utc)
            if best is None:
                continue
            offset, close_utc = best
            aligned = abs(offset - (ny_utcoffset(close_utc) + 7 * HOUR)) < pd.Timedelta(1, unit="min")
            return ny_utcoffset(now) + 7 * HOUR if aligned else offset
        return None

    def to_utc(self, server_seconds) -> pd.Timestamp:
        return pd.Timestamp(int(server_seconds), unit="s") - self.server_offset()

    def _position_from_mt5(self, p) -> Position:
        direction = Direction.LONG if p.type == self.mt5.POSITION_TYPE_BUY else Direction.SHORT
        sl = float(p.sl or 0.0)
        risk_distance = abs(float(p.price_open) - sl) if sl else 0.0
        return Position(id=str(p.ticket), symbol=self.our_symbol(p.symbol), direction=direction, lots=float(p.volume),
                        entry=float(p.price_open), stop=sl, take_profit=float(p.tp or 0.0), opened_at=self.to_utc(p.time),
                        risk_amount=0.0, risk_distance=risk_distance, breakeven_r=0.0, initial_stop=sl,
                        meta={"comment": getattr(p, "comment", "")})

    def _finish(self, pos: Position, exit_price: float, reason: str, ts, pnl: float) -> ClosedTrade:
        self._positions.pop(pos.id, None)
        trade = ClosedTrade(
            id=pos.id, symbol=pos.symbol, direction=pos.direction, lots=pos.lots, entry=pos.entry, exit=float(exit_price),
            stop=pos.stop, take_profit=pos.take_profit, opened_at=pos.opened_at,
            closed_at=pd.Timestamp(ts) if ts is not None else self.clock(), reason=reason, pnl=float(pnl),
            r=pos.r_at(float(exit_price)), risk_amount=pos.risk_amount, initial_stop=pos.initial_stop, meta=dict(pos.meta),
        )
        self._closed.append(trade)
        return trade

    def _deal_pnl(self, deals) -> float:
        return sum(float(d.profit) + float(getattr(d, "commission", 0.0) or 0.0) + float(getattr(d, "swap", 0.0) or 0.0)
                   for d in deals)

    def _sync_closed(self) -> None:
        """Tracked positions gone from the terminal: read their closing deal(s) from the history."""
        open_ids = {str(p.ticket) for p in (self.mt5.positions_get() or [])}
        for pid, pos in list(self._positions.items()):
            if pid in open_ids or pos.status == "pending":
                continue
            deals = list(self.mt5.history_deals_get(position=int(pid)) or [])
            outs = [d for d in deals if d.entry == self.mt5.DEAL_ENTRY_OUT]
            if not outs:
                continue                                  # closing deal not in the history yet; next poll
            last = outs[-1]
            if last.reason == self.mt5.DEAL_REASON_SL:
                reason = "breakeven" if pos.breakeven_done else "stop"
            elif last.reason == self.mt5.DEAL_REASON_TP:
                reason = "take_profit"
            else:
                reason = "closed"
            self._finish(pos, float(last.price), reason, self.to_utc(last.time), self._deal_pnl(outs))

    def algo_trading_on(self) -> bool:
        """The terminal's Algo Trading button (MT5 refuses orders from the API while it is off)."""
        return bool(getattr(self.mt5.terminal_info(), "trade_allowed", False))

    def diagnostics(self) -> Dict[str, Any]:
        info = self.mt5.account_info()
        term = self.mt5.terminal_info()
        algo = bool(getattr(term, "trade_allowed", False))              # the terminal's Algo Trading button
        account_ok = bool(getattr(info, "trade_allowed", True))          # False on an investor (read-only) login
        offset = self.server_offset()
        out: Dict[str, Any] = {"version": self.mt5.version(), "connected": bool(getattr(term, "connected", False)),
                               "algo_trading": algo, "account_trade_allowed": account_ok,
                               "trade_allowed": algo and account_ok,
                               "server_offset": f"{offset.total_seconds() / 3600:+.1f} h"}
        for key in ("login", "server", "currency", "balance", "equity", "leverage", "trade_mode"):
            out[key] = getattr(info, key, None)
        return out

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        return float(self.mt5.account_info().equity)

    def balance(self) -> float:
        return float(self.mt5.account_info().balance)

    def realized_pnl_since(self, since: pd.Timestamp) -> Optional[float]:
        """Closed P&L (profit, commission, swap, fee) of the account's trade deals since ``since`` (naive UTC); deposits
        and other balance operations are left out.  None when the terminal does not answer."""
        start = pd.Timestamp(since) + self.server_offset() - pd.Timedelta(days=1)      # server time, a day early
        deals = self.mt5.history_deals_get(start.to_pydatetime(), (pd.Timestamp.now() + pd.Timedelta(days=2)).to_pydatetime())
        if deals is None:
            return None
        trade_types = {getattr(self.mt5, "DEAL_TYPE_BUY", 0), getattr(self.mt5, "DEAL_TYPE_SELL", 1)}
        total = 0.0
        for d in deals:
            if getattr(d, "type", 0) not in trade_types or self.to_utc(d.time) < pd.Timestamp(since):
                continue
            total += self._deal_pnl([d]) + float(getattr(d, "fee", 0.0) or 0.0)
        return total

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        raw = self.mt5.positions_get(symbol=self.mt5_symbol(symbol)) if symbol else self.mt5.positions_get()
        out: List[Position] = []
        for p in (raw or []):
            if p.magic != self.magic:
                continue
            pid = str(p.ticket)
            pos = self._positions.get(pid)
            if pos is None:
                pos = self._positions[pid] = self._position_from_mt5(p)
            else:
                pos.stop, pos.take_profit = float(p.sl or 0.0), float(p.tp or 0.0)
                if pos.status == "pending":                  # the order has become a position: confirmed
                    pos.entry, pos.status = float(p.price_open), "filled"
                    pos.meta.pop("entry_unconfirmed", None)
            if not pos.breakeven_done and pos.stop and pos.direction.sign * (pos.stop - pos.entry) >= 0:
                pos.breakeven_done = True                    # the stop already sits at or beyond the entry
            out.append(pos)
        self._sync_closed()
        return out

    def current_price(self, symbol: str) -> float:
        tick = self.mt5.symbol_info_tick(self.mt5_symbol(symbol))
        if tick is None or not tick.bid or not tick.ask:
            raise RuntimeError(f"no price for {symbol}: {self.mt5.last_error()}")
        return float((tick.bid + tick.ask) / 2.0)

    def fill_price(self, symbol: str, direction: Direction, base: Optional[float] = None) -> float:
        """The live ask for a long, the live bid for a short (``base`` is ignored: the terminal has the quote)."""
        tick = self.mt5.symbol_info_tick(self.mt5_symbol(symbol))
        if tick is None or not tick.bid or not tick.ask:
            raise RuntimeError(f"no price for {symbol}: {self.mt5.last_error()}")
        return float(tick.ask if direction is Direction.LONG else tick.bid)

    def place_market_order(self, symbol, direction, lots, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                           meta=None, price=None, ts=None, price_is_fill=False) -> Position:
        """Market order with stop and target attached; ``status="filled"`` only on TRADE_RETCODE_DONE with a price."""
        mt5 = self.mt5
        name = self.mt5_symbol(symbol)
        mt5.symbol_select(name, True)
        tick = mt5.symbol_info_tick(name)
        if tick is None:
            raise RuntimeError(f"no tick for {symbol}: {mt5.last_error()}")
        is_long = direction is Direction.LONG
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": name,
            "volume": float(lots),
            "type": mt5.ORDER_TYPE_BUY if is_long else mt5.ORDER_TYPE_SELL,
            "price": float(tick.ask if is_long else tick.bid),
            "sl": float(stop),
            "tp": float(take_profit),
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": str((meta or {}).get("comment", "kronos_trader"))[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": getattr(mt5, self.params.filling),
        }
        result = mt5.order_send(request)
        if result is None or result.retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_PLACED):
            raise RuntimeError(f"{symbol} order not accepted: retcode {getattr(result, 'retcode', None)} "
                               f"{getattr(result, 'comment', '')}")
        confirmed = result.retcode == mt5.TRADE_RETCODE_DONE and float(getattr(result, "price", 0.0) or 0.0) > 0
        pid = str(result.order)
        deal = int(getattr(result, "deal", 0) or 0)
        if deal:
            found = list(mt5.history_deals_get(ticket=deal) or [])
            if found and getattr(found[0], "position_id", 0):
                pid = str(found[0].position_id)
        entry = float(result.price) if confirmed else float(request["price"])
        pos = Position(
            id=pid, symbol=symbol.upper(), direction=direction, lots=float(lots), entry=entry, stop=float(stop),
            take_profit=float(take_profit), opened_at=pd.Timestamp(ts) if ts is not None else self.clock(),
            risk_amount=float(risk_amount), risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
            initial_stop=float(stop), meta=dict(meta or {}), status="filled" if confirmed else "pending",
        )
        if not confirmed:
            pos.meta["entry_unconfirmed"] = True
        self._positions[pos.id] = pos
        return pos

    def modify_stop(self, position_id: str, stop: float) -> None:
        mt5 = self.mt5
        p = next((x for x in mt5.positions_get() or [] if str(x.ticket) == str(position_id)), None)
        if p is None:
            raise KeyError(f"position {position_id} not found")
        request = {"action": mt5.TRADE_ACTION_SLTP, "position": p.ticket, "symbol": p.symbol,
                   "sl": float(stop), "tp": float(p.tp), "magic": self.magic}
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"modify stop failed: retcode {getattr(result, 'retcode', None)} {getattr(result, 'comment', '')}")
        tracked = self._positions.get(str(position_id))
        if tracked is not None:
            tracked.stop = float(stop)

    def close_position(self, position_id, reason="manual", price=None, ts=None) -> ClosedTrade:
        mt5 = self.mt5
        p = next((x for x in mt5.positions_get() or [] if str(x.ticket) == str(position_id)), None)
        if p is None:
            raise KeyError(f"position {position_id} not found")
        tick = mt5.symbol_info_tick(p.symbol)
        is_long = p.type == mt5.POSITION_TYPE_BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": float(p.volume), "position": p.ticket,
            "type": mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY,
            "price": float(tick.bid if is_long else tick.ask), "deviation": self.deviation, "magic": self.magic,
            "comment": str(reason)[:31], "type_time": mt5.ORDER_TIME_GTC, "type_filling": getattr(mt5, self.params.filling),
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"close failed: retcode {getattr(result, 'retcode', None)} {getattr(result, 'comment', '')}")
        pos = self._positions.get(str(position_id)) or self._position_from_mt5(p)
        deals = list(mt5.history_deals_get(ticket=int(getattr(result, "deal", 0) or 0)) or []) if getattr(result, "deal", 0) else []
        pnl = self._deal_pnl(deals) if deals else float(getattr(p, "profit", 0.0) or 0.0)
        return self._finish(pos, float(result.price), reason, ts, pnl)

    def recent_closes(self) -> List[ClosedTrade]:
        self._sync_closed()
        out = self._closed[self._close_cursor:]
        self._close_cursor = len(self._closed)
        return out

    # ------------------------------------------------------------ data
    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        timeframe = Timeframe.parse(timeframe)
        mt5 = self.mt5
        name = self.mt5_symbol(symbol)
        if mt5.symbol_select(name, True) is False:
            near = self.find_symbols(symbol[:3])
            raise RuntimeError(f"MT5 has no symbol {name!r} on this server" + (f"; it has: {', '.join(near[:12])}" if near else "")
                               + f". Set symbols: {symbol.upper()}: mt5_symbol: <name> in the profile "
                               f"(`python -m kronos_trader mt5-symbols --search {symbol[:3]}` lists them)")
        rates = None
        for attempt in range(3):          # the first request after selecting a symbol can fail while the terminal loads history
            rates = mt5.copy_rates_from_pos(name, getattr(mt5, MT5_TIMEFRAMES[timeframe]), 0, int(count))
            if rates is not None and len(rates) > 0:
                break
            time.sleep(self.retry_seconds)
        if rates is None or len(rates) == 0:
            near = [n for n in self.find_symbols(symbol[:3]) if n != name]
            raise RuntimeError(f"MT5 returned no bars for {symbol} {timeframe.label} ({name!r}): {mt5.last_error()}"
                               + (f". Symbols on this server like it: {', '.join(near[:12])}" if near else "")
                               + f"; check the name in Market Watch (right-click, Symbols) and set mt5_symbol in the profile")
        df = pd.DataFrame(rates)
        df["timestamp"] = pd.to_datetime(df["time"].astype("int64"), unit="s") - self.server_offset(symbol)
        df = df.rename(columns={"tick_volume": "volume"})
        return CandleSeries(df[["timestamp", "open", "high", "low", "close", "volume"]].reset_index(drop=True),
                            timeframe, symbol.upper())
