"""MetaTrader 5 broker adapter (Windows only, ``pip install MetaTrader5``).

Most prop firms hand out MT5 accounts, so this is the intended live path.  It
is deliberately thin: the strategy and the risk guard decide, this module only
translates to ``order_send``.  Everything here is untested against a live
terminal until the demo-account phase (see docs/ROADMAP.md).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pandas as pd

from ..config import Settings
from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Direction
from .base import Broker, ClosedTrade, Position

MT5_TIMEFRAMES = {
    Timeframe.MIN_1: "TIMEFRAME_M1", Timeframe.MIN_5: "TIMEFRAME_M5", Timeframe.MIN_15: "TIMEFRAME_M15",
    Timeframe.MIN_30: "TIMEFRAME_M30", Timeframe.H_1: "TIMEFRAME_H1", Timeframe.H_4: "TIMEFRAME_H4",
    Timeframe.D_1: "TIMEFRAME_D1", Timeframe.W_1: "TIMEFRAME_W1", Timeframe.MN_1: "TIMEFRAME_MN1",
}


class MT5Broker(Broker):
    def __init__(self, settings: Optional[Settings] = None, magic: int = 20260930, deviation_points: int = 20):
        try:
            import MetaTrader5 as mt5  # type: ignore
        except ImportError as exc:  # pragma: no cover - platform specific
            raise RuntimeError("MetaTrader5 package not available (Windows + `pip install MetaTrader5`)") from exc
        self.mt5 = mt5
        self.settings = settings or Settings()
        self.magic = magic
        self.deviation = deviation_points
        login = os.environ.get("MT5_LOGIN")
        password = os.environ.get("MT5_PASSWORD")
        server = os.environ.get("MT5_SERVER")
        kwargs: Dict[str, Any] = {}
        if login and password and server:
            kwargs = {"login": int(login), "password": password, "server": server}
        if not mt5.initialize(**kwargs):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    # ------------------------------------------------------------ helpers
    def _mt5_symbol(self, symbol: str) -> str:
        spec = self.settings.symbol(symbol)
        return spec.mt5_symbol or symbol.upper()

    def _position_from_mt5(self, p) -> Position:
        direction = Direction.LONG if p.type == self.mt5.POSITION_TYPE_BUY else Direction.SHORT
        risk_distance = abs(p.price_open - p.sl) if p.sl else 0.0
        return Position(id=str(p.ticket), symbol=p.symbol, direction=direction, lots=p.volume, entry=p.price_open,
                        stop=p.sl, take_profit=p.tp, opened_at=pd.Timestamp(p.time, unit="s"), risk_amount=0.0,
                        risk_distance=risk_distance, breakeven_r=0.0, initial_stop=p.sl, meta={"comment": p.comment})

    # ------------------------------------------------------------ Broker API
    def equity(self) -> float:
        info = self.mt5.account_info()
        return float(info.equity)

    def balance(self) -> float:
        info = self.mt5.account_info()
        return float(info.balance)

    def open_positions(self, symbol: Optional[str] = None) -> List[Position]:
        raw = self.mt5.positions_get(symbol=self._mt5_symbol(symbol)) if symbol else self.mt5.positions_get()
        return [self._position_from_mt5(p) for p in (raw or []) if p.magic == self.magic]

    def current_price(self, symbol: str) -> float:
        tick = self.mt5.symbol_info_tick(self._mt5_symbol(symbol))
        return float((tick.bid + tick.ask) / 2.0)

    def place_market_order(self, symbol, direction, lots, stop, take_profit, risk_amount, risk_distance, breakeven_r,
                           meta=None, price=None, ts=None) -> Position:
        mt5 = self.mt5
        name = self._mt5_symbol(symbol)
        mt5.symbol_select(name, True)
        tick = mt5.symbol_info_tick(name)
        is_long = direction is Direction.LONG
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": name,
            "volume": float(lots),
            "type": mt5.ORDER_TYPE_BUY if is_long else mt5.ORDER_TYPE_SELL,
            "price": tick.ask if is_long else tick.bid,
            "sl": float(stop),
            "tp": float(take_profit),
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": (meta or {}).get("comment", "kronos_trader")[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"order_send failed: {getattr(result, 'retcode', None)} {getattr(result, 'comment', '')}")
        return Position(id=str(result.order), symbol=name, direction=direction, lots=float(lots), entry=float(result.price),
                        stop=float(stop), take_profit=float(take_profit), opened_at=pd.Timestamp.utcnow(),
                        risk_amount=float(risk_amount), risk_distance=float(risk_distance), breakeven_r=float(breakeven_r),
                        initial_stop=float(stop), meta=dict(meta or {}))

    def modify_stop(self, position_id: str, stop: float) -> None:
        mt5 = self.mt5
        pos = next((p for p in mt5.positions_get() or [] if str(p.ticket) == str(position_id)), None)
        if pos is None:
            raise KeyError(f"position {position_id} not found")
        request = {"action": mt5.TRADE_ACTION_SLTP, "position": pos.ticket, "symbol": pos.symbol,
                   "sl": float(stop), "tp": float(pos.tp), "magic": self.magic}
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"modify stop failed: {getattr(result, 'retcode', None)}")

    def close_position(self, position_id, reason="manual", price=None, ts=None) -> ClosedTrade:
        mt5 = self.mt5
        pos = next((p for p in mt5.positions_get() or [] if str(p.ticket) == str(position_id)), None)
        if pos is None:
            raise KeyError(f"position {position_id} not found")
        tick = mt5.symbol_info_tick(pos.symbol)
        is_long = pos.type == mt5.POSITION_TYPE_BUY
        request = {
            "action": mt5.TRADE_ACTION_DEAL, "symbol": pos.symbol, "volume": pos.volume, "position": pos.ticket,
            "type": mt5.ORDER_TYPE_SELL if is_long else mt5.ORDER_TYPE_BUY,
            "price": tick.bid if is_long else tick.ask, "deviation": self.deviation, "magic": self.magic,
            "comment": reason[:31], "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"close failed: {getattr(result, 'retcode', None)}")
        direction = Direction.LONG if is_long else Direction.SHORT
        return ClosedTrade(id=str(pos.ticket), symbol=pos.symbol, direction=direction, lots=pos.volume, entry=pos.price_open,
                           exit=float(result.price), stop=pos.sl, take_profit=pos.tp, opened_at=pd.Timestamp(pos.time, unit="s"),
                           closed_at=pd.Timestamp.utcnow(), reason=reason, pnl=float(pos.profit), r=0.0, risk_amount=0.0,
                           initial_stop=pos.sl)

    # ------------------------------------------------------------ data
    def get_candles(self, symbol: str, timeframe: Timeframe, count: int = 500) -> CandleSeries:
        mt5 = self.mt5
        tf = getattr(mt5, MT5_TIMEFRAMES[Timeframe.parse(timeframe)])
        rates = mt5.copy_rates_from_pos(self._mt5_symbol(symbol), tf, 0, count)
        if rates is None:
            raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df["timestamp"] = pd.to_datetime(df["time"], unit="s")
        df = df.rename(columns={"tick_volume": "volume"})
        return CandleSeries(df[["timestamp", "open", "high", "low", "close", "volume"]], timeframe, symbol.upper())
