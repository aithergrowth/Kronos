"""MT5 adapter against a fake MetaTrader5 module: server time, candles, orders, break-even, closes."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from kronos_trader.config import Settings
from kronos_trader.core import Direction, Timeframe as T
from kronos_trader.execution.mt5 import MT5Broker

NOW = pd.Timestamp("2026-10-01 09:00")          # UTC
OFFSET_H = 3                                     # the broker server runs on UTC+3


def server_seconds(ts: pd.Timestamp) -> int:
    return int((ts + pd.Timedelta(OFFSET_H, unit="h")).timestamp())


class FakeMT5:
    TIMEFRAME_M1, TIMEFRAME_M5, TIMEFRAME_M15, TIMEFRAME_M30, TIMEFRAME_H1, TIMEFRAME_H4 = 1, 5, 15, 30, 16385, 16388
    TIMEFRAME_D1, TIMEFRAME_W1, TIMEFRAME_MN1 = 16408, 32769, 49153
    POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
    ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
    TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
    ORDER_TIME_GTC, ORDER_FILLING_FOK, ORDER_FILLING_IOC = 0, 0, 1
    TRADE_RETCODE_DONE, TRADE_RETCODE_PLACED = 10009, 10008
    DEAL_ENTRY_IN, DEAL_ENTRY_OUT = 0, 1
    DEAL_REASON_CLIENT, DEAL_REASON_SL, DEAL_REASON_TP = 0, 4, 5

    def __init__(self, bid=1.1000, ask=1.1001):
        self.bid, self.ask = bid, ask
        self.init_kwargs = None
        self.positions = []
        self.deals = []
        self.requests = []
        self._ticket = 500
        self.accept = True

    def initialize(self, **kwargs):
        self.init_kwargs = kwargs
        return True

    def login(self, login, password=None, server=None, timeout=None):
        self.login_args = (login, password, server)
        return True

    def shutdown(self):
        self.init_kwargs = None

    def last_error(self):
        return (0, "ok")

    def version(self):
        return (500, 4000, "01 Jan 2026")

    def account_info(self):
        return SimpleNamespace(login=62724281, server="MetaQuotes-Demo", currency="EUR", balance=50000.0,
                               equity=50010.0, leverage=100, trade_mode=0)

    def terminal_info(self):
        return SimpleNamespace(connected=True, trade_allowed=True)

    known = ("EURUSD", "XAUUSD", "BTCUSD.x", "BTCEUR.x")

    def symbol_select(self, name, enable=True):
        return name in self.known

    def symbols_get(self, group="*"):
        text = group.strip("*").upper()
        return [SimpleNamespace(name=n) for n in self.known if text in n.upper()]

    def symbol_info(self, name):
        if name not in self.known:
            return None
        return SimpleNamespace(description=f"{name} CFD", digits=2, point=0.01, trade_contract_size=1.0, volume_min=0.01,
                               volume_step=0.01, volume_max=100.0, trade_mode=4, currency_profit="USD", spread=20)

    def symbol_info_tick(self, name):
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=server_seconds(NOW))

    def copy_rates_from_pos(self, name, tf, start, count):
        rows = [(server_seconds(NOW - pd.Timedelta(15 * (count - 1 - i), unit="min")), 1.1, 1.101, 1.099, 1.1005, 12, 1, 0)
                for i in range(count)]
        return np.array(rows, dtype=[("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                                     ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])

    def _deal(self, position_id, entry, reason, price, profit, when):
        self._ticket += 1
        d = SimpleNamespace(ticket=self._ticket, position_id=position_id, entry=entry, reason=reason, price=price,
                            profit=profit, commission=-0.5, swap=0.0, time=server_seconds(when))
        self.deals.append(d)
        return d

    def order_send(self, request):
        self.requests.append(request)
        if not self.accept:
            return SimpleNamespace(retcode=10013, order=0, deal=0, price=0.0, comment="Invalid request")
        if request["action"] == self.TRADE_ACTION_SLTP:
            for p in self.positions:
                if p.ticket == request["position"]:
                    p.sl, p.tp = request["sl"], request["tp"]
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=0, deal=0, price=0.0, comment="")
        price = self.ask if request["type"] == self.ORDER_TYPE_BUY else self.bid
        if request.get("position"):                                                     # closing deal
            pos = next(p for p in self.positions if p.ticket == request["position"])
            if request["volume"] < pos.volume - 1e-9:                                   # a partial close
                pos.volume = round(pos.volume - request["volume"], 8)
                d = self._deal(pos.ticket, self.DEAL_ENTRY_OUT, self.DEAL_REASON_CLIENT, price, 40.0, NOW)
                return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=d.ticket, deal=d.ticket, price=price, comment="")
            self.positions.remove(pos)
            d = self._deal(pos.ticket, self.DEAL_ENTRY_OUT, self.DEAL_REASON_CLIENT, price, 15.0, NOW)
            return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=d.ticket, deal=d.ticket, price=price, comment="")
        self._ticket += 1
        ticket = self._ticket
        self.positions.append(SimpleNamespace(ticket=ticket, symbol=request["symbol"], type=request["type"],
                                              volume=request["volume"], price_open=price, sl=request["sl"], tp=request["tp"],
                                              time=server_seconds(NOW), magic=request["magic"], comment=request["comment"],
                                              profit=0.0))
        d = self._deal(ticket, self.DEAL_ENTRY_IN, self.DEAL_REASON_CLIENT, price, 0.0, NOW)
        return SimpleNamespace(retcode=self.TRADE_RETCODE_DONE, order=ticket, deal=d.ticket, price=price, comment="")

    def positions_get(self, symbol=None):
        return [p for p in self.positions if symbol is None or p.symbol == symbol]

    def history_deals_get(self, *args, position=None, ticket=None):
        if ticket is not None:
            return [d for d in self.deals if d.ticket == ticket]
        if position is not None:
            return [d for d in self.deals if d.position_id == position]
        return list(self.deals)

    def server_closes(self, ticket, how="sl"):
        """The server closes a position at its stop or target an hour later."""
        pos = next(p for p in self.positions if p.ticket == ticket)
        self.positions.remove(pos)
        reason = self.DEAL_REASON_SL if how == "sl" else self.DEAL_REASON_TP
        self._deal(ticket, self.DEAL_ENTRY_OUT, reason, pos.sl if how == "sl" else pos.tp,
                   -100.0 if how == "sl" else 300.0, NOW + pd.Timedelta(1, unit="h"))


@pytest.fixture
def broker(monkeypatch):
    for key in ("MT5_PATH", "MT5_SERVER_OFFSET_HOURS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MT5_LOGIN", "62724281")
    monkeypatch.setenv("MT5_PASSWORD", "pw")
    monkeypatch.setenv("MT5_SERVER", "MetaQuotes-Demo")
    return MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)


def test_initialize_uses_the_environment(broker):
    assert broker.mt5.init_kwargs == {"login": 62724281, "password": "pw", "server": "MetaQuotes-Demo"}
    d = broker.diagnostics()
    assert d["server"] == "MetaQuotes-Demo" and d["currency"] == "EUR" and d["connected"] and d["equity"] == 50010.0


def test_without_credentials_the_terminal_account_is_used(monkeypatch):
    for key in ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER", "MT5_PATH"):
        monkeypatch.delenv(key, raising=False)
    b = MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)
    assert b.mt5.init_kwargs == {} and b.terminal_path is None


def test_initialize_failure_names_the_account(monkeypatch):
    monkeypatch.setenv("MT5_PATH", r"C:\mt5\terminal64.exe")
    monkeypatch.setenv("MT5_LOGIN", "62724281")
    monkeypatch.setenv("MT5_PASSWORD", "pw")
    monkeypatch.setenv("MT5_SERVER", "MetaQuotes-Demo")

    class Refusing(FakeMT5):
        def initialize(self, **kwargs):
            self.init_kwargs = kwargs
            return False

        def last_error(self):
            return (-6, "Terminal: Authorization failed")

    with pytest.raises(RuntimeError, match="for login 62724281 on MetaQuotes-Demo.*Authorization failed"):
        MT5Broker(Settings(), api=Refusing(), clock=lambda: NOW)


def test_server_time_is_converted_to_utc(broker):
    assert broker.server_offset("EURUSD") == pd.Timedelta(3, unit="h")
    s = broker.get_candles("EURUSD", T.MIN_15, 4)
    assert len(s) == 4 and s.symbol == "EURUSD" and str(s.timestamps.iloc[-1]) == "2026-10-01 09:00:00"
    assert s.last.close == pytest.approx(1.1005)


class WeekFake(FakeMT5):
    """A terminal whose M30 history has real weekend gaps, stamped in server time (UTC + ``offset_h``)."""

    def __init__(self, offset_h, last_bar_utc, tick_utc=None, close_hour_server=None):
        super().__init__()
        self.offset_h, self.last_bar_utc, self.tick_utc = offset_h, last_bar_utc, tick_utc
        self.close_hour_server = close_hour_server        # bars after this server hour on Friday are dropped

    def symbol_info_tick(self, name):
        when = int((self.tick_utc + pd.Timedelta(self.offset_h, unit="h")).timestamp()) if self.tick_utc is not None else 0
        return SimpleNamespace(bid=self.bid, ask=self.ask, time=when)

    def copy_rates_from_pos(self, name, tf, start, count):
        rows = []
        slot = self.last_bar_utc
        while len(rows) < count:
            server = slot + pd.Timedelta(self.offset_h, unit="h")
            ny = slot.tz_localize("UTC").tz_convert("America/New_York")      # the week runs Sun 17:00 - Fri 17:00 New York
            open_week = ny.weekday() < 4 or (ny.weekday() == 4 and ny.hour < 17) or (ny.weekday() == 6 and ny.hour >= 17)
            if self.close_hour_server is not None and server.weekday() == 4 and server.hour >= self.close_hour_server:
                open_week = False
            if open_week:
                rows.append((int(server.timestamp()), 1.1, 1.101, 1.099, 1.1005, 12, 1, 0))
            slot -= pd.Timedelta(30, unit="min")
        rows.reverse()
        return np.array(rows, dtype=[("time", "<i8"), ("open", "<f8"), ("high", "<f8"), ("low", "<f8"), ("close", "<f8"),
                                     ("tick_volume", "<u8"), ("spread", "<i4"), ("real_volume", "<u8")])


FRIDAY_LAST_BAR = pd.Timestamp("2026-10-02 20:30")   # the week's last M30 bar: 16:30 New York under daylight saving


def test_weekend_offset_comes_from_the_friday_close(monkeypatch):
    """Saturday: the latest tick is Friday's close, 18 hours old, which read as -15 h before (and then shifted
    every candle of the week by 18 hours). The last bar before the weekend gap gives +3 h."""
    monkeypatch.delenv("MT5_SERVER_OFFSET_HOURS", raising=False)
    saturday = pd.Timestamp("2026-10-03 15:00")
    api = WeekFake(3, FRIDAY_LAST_BAR, tick_utc=pd.Timestamp("2026-10-02 20:59"))
    b = MT5Broker(Settings(), api=api, clock=lambda: saturday)
    assert b.offset_from_tick("EURUSD", saturday) is None                      # -15 h is no offset: stale
    assert b.server_offset() == pd.Timedelta(3, unit="h")
    assert str(b.get_candles("EURUSD", T.MIN_30, 3).timestamps.iloc[-1]) == "2026-10-02 20:30:00"


def test_offset_follows_us_daylight_saving(monkeypatch):
    """A server whose week ends at 23:30 keeps midnight on the New York close: +3 h in October, +2 h the Monday
    after the US switch (1 Nov 2026), read from the same Friday bar."""
    monkeypatch.delenv("MT5_SERVER_OFFSET_HOURS", raising=False)
    api = WeekFake(3, pd.Timestamp("2026-10-30 20:30"))
    before = MT5Broker(Settings(), api=api, clock=lambda: pd.Timestamp("2026-10-31 12:00"))
    assert before.server_offset() == pd.Timedelta(3, unit="h")
    after = MT5Broker(Settings(), api=api, clock=lambda: pd.Timestamp("2026-11-02 10:00"))
    assert after.server_offset() == pd.Timedelta(2, unit="h")


def test_fixed_offset_server_and_an_early_close(monkeypatch):
    monkeypatch.delenv("MT5_SERVER_OFFSET_HOURS", raising=False)
    monday = pd.Timestamp("2026-10-05 10:00")
    utc_server = WeekFake(0, FRIDAY_LAST_BAR, tick_utc=monday)
    assert MT5Broker(Settings(), api=utc_server, clock=lambda: monday).server_offset() == pd.Timedelta(0)
    # a broker that stops quoting at 23:00 server: the bars say +2 h, the fresh tick +3 h, within 1.5 h -> tick
    early = WeekFake(3, FRIDAY_LAST_BAR, tick_utc=monday, close_hour_server=23)
    b = MT5Broker(Settings(), api=early, clock=lambda: monday)
    assert b.offset_from_week_close("EURUSD", monday) == pd.Timedelta(2, unit="h")
    assert b.server_offset() == pd.Timedelta(3, unit="h")


def test_stale_holiday_tick_loses_to_the_week_close(monkeypatch):
    monkeypatch.delenv("MT5_SERVER_OFFSET_HOURS", raising=False)
    thursday = pd.Timestamp("2026-10-08 14:00")
    api = WeekFake(3, FRIDAY_LAST_BAR, tick_utc=thursday - pd.Timedelta(5, unit="h"))   # closed since 09:00
    b = MT5Broker(Settings(), api=api, clock=lambda: thursday)
    assert b.offset_from_tick("EURUSD", thursday) == pd.Timedelta(-2, unit="h")
    assert b.server_offset() == pd.Timedelta(3, unit="h")


def test_offset_is_reread_hourly(monkeypatch):
    monkeypatch.delenv("MT5_SERVER_OFFSET_HOURS", raising=False)
    now = {"t": pd.Timestamp("2026-10-05 10:00")}
    api = WeekFake(3, FRIDAY_LAST_BAR, tick_utc=pd.Timestamp("2026-10-05 10:00"))
    b = MT5Broker(Settings(), api=api, clock=lambda: now["t"])
    assert b.server_offset() == pd.Timedelta(3, unit="h")
    api.offset_h, api.tick_utc = 2, pd.Timestamp("2026-10-05 10:30")
    now["t"] = pd.Timestamp("2026-10-05 10:30")
    assert b.server_offset() == pd.Timedelta(3, unit="h")          # cached within the hour
    now["t"] = pd.Timestamp("2026-10-05 11:01")
    api.tick_utc = now["t"]
    assert b.server_offset() == pd.Timedelta(2, unit="h")


def test_diagnostics_separate_algo_trading_from_the_account(broker):
    d = broker.diagnostics()
    assert d["algo_trading"] and d["account_trade_allowed"] and d["trade_allowed"] and d["server_offset"] == "+3.0 h"
    broker.mt5.terminal_info = lambda: SimpleNamespace(connected=True, trade_allowed=False)
    d = broker.diagnostics()
    assert not d["algo_trading"] and d["account_trade_allowed"] and not d["trade_allowed"]


def test_pinned_offset(monkeypatch):
    monkeypatch.setenv("MT5_SERVER_OFFSET_HOURS", "2")
    b = MT5Broker(Settings(), api=FakeMT5(), clock=lambda: NOW)
    assert b.server_offset() == pd.Timedelta(2, unit="h")


def test_market_order_tracking_breakeven_and_close(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0,
                                    meta={"comment": "test"}, ts=NOW)
    req = broker.mt5.requests[-1]
    assert req["symbol"] == "EURUSD" and req["volume"] == 0.5 and req["sl"] == 1.0950 and req["tp"] == 1.12
    assert req["magic"] == broker.magic and req["type_filling"] == FakeMT5.ORDER_FILLING_IOC
    assert pos.status == "filled" and pos.entry == pytest.approx(1.1001) and pos.opened_at == NOW
    assert broker.open_positions("EURUSD") == [pos] and broker.open_positions()[0] is pos     # same object every poll
    assert not pos.breakeven_done
    broker.modify_stop(pos.id, 1.1001)
    assert broker.open_positions("EURUSD")[0].stop == 1.1001 and pos.breakeven_done
    trade = broker.close_position(pos.id, "manual", ts=NOW)
    assert trade.reason == "manual" and trade.pnl == pytest.approx(14.5) and broker.open_positions() == []


def test_stop_and_target_hits_are_reported(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0, ts=NOW)
    broker.mt5.server_closes(int(pos.id), "sl")
    closes = broker.recent_closes()
    assert len(closes) == 1 and closes[0].reason == "stop" and closes[0].exit == 1.0950
    assert closes[0].pnl == pytest.approx(-100.5) and closes[0].r == pytest.approx(-1.0)
    assert str(closes[0].closed_at) == "2026-10-01 10:00:00"
    assert broker.recent_closes() == []
    pos2 = broker.place_market_order("EURUSD", Direction.SHORT, 0.5, 1.1050, 1.0800, 500.0, 0.0050, 4.0, ts=NOW)
    broker.mt5.server_closes(int(pos2.id), "tp")
    assert broker.recent_closes()[0].reason == "take_profit"


def test_rejected_order_raises(broker):
    broker.mt5.accept = False
    with pytest.raises(RuntimeError, match="not accepted"):
        broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0)
    assert broker.open_positions() == []


def test_unknown_symbol_names_the_servers_alternatives(broker):
    """A symbol the server does not have (MetaQuotes-Demo names BTC differently) fails with the names it does have."""
    with pytest.raises(RuntimeError, match=r"no symbol 'BTCUSD'.*BTCUSD\.x.*mt5_symbol"):
        broker.get_candles("BTCUSD", T.MIN_15, 5)
    assert broker.find_symbols("btc") == ["BTCEUR.x", "BTCUSD.x"]
    d = broker.symbol_details("BTCUSD.x")
    assert d["found"] and d["trade_contract_size"] == 1.0 and d["volume_min"] == 0.01
    assert broker.symbol_details("NOPE") == {"name": "NOPE", "found": False}


def test_bars_are_retried_once_the_terminal_has_loaded_the_history(broker):
    calls = {"n": 0}
    real = broker.mt5.copy_rates_from_pos

    def slow(name, tf, start, count):
        if tf != FakeMT5.TIMEFRAME_M15:                     # the server-offset read asks for M30 bars; not counted
            return real(name, tf, start, count)
        calls["n"] += 1
        return None if calls["n"] == 1 else real(name, tf, start, count)

    broker.mt5.copy_rates_from_pos = slow
    broker.retry_seconds = 0.0
    assert len(broker.get_candles("EURUSD", T.MIN_15, 4)) == 4 and calls["n"] == 2




def test_realized_pnl_since_counts_trade_deals_only(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0, ts=NOW)
    broker.mt5.server_closes(int(pos.id), "sl")                     # entry deal 09:00 (-0.5), exit deal 10:00 (-100.5)
    broker.mt5.deals.append(SimpleNamespace(ticket=999, position_id=0, entry=0, reason=0, price=0.0, profit=100_000.0,
                                            commission=0.0, swap=0.0, time=server_seconds(NOW), type=2))   # a deposit
    assert broker.realized_pnl_since(NOW - pd.Timedelta(hours=1)) == pytest.approx(-101.0)
    assert broker.realized_pnl_since(NOW + pd.Timedelta(minutes=30)) == pytest.approx(-100.5)
    assert broker.realized_pnl_since(NOW + pd.Timedelta(hours=2)) == pytest.approx(0.0)



def test_partial_close_banks_a_share_and_the_close_counts_the_whole_trade(broker):
    pos = broker.place_market_order("EURUSD", Direction.LONG, 0.5, 1.0950, 1.1200, 500.0, 0.0051, 4.0, ts=NOW)
    assert pos.initial_lots == 0.5
    pnl = broker.close_partial(pos.id, 1 / 3)
    req = broker.mt5.requests[-1]
    assert req["volume"] == pytest.approx(0.16) and req["position"] == int(pos.id) and req["comment"] == "partial"
    assert pnl == pytest.approx(39.5) and pos.partial_done and pos.lots == pytest.approx(0.34)   # 40 profit - 0.5 commission
    assert broker.open_positions("EURUSD")[0].lots == pytest.approx(0.34)
    broker.mt5.server_closes(int(pos.id), "sl")
    trade = broker.recent_closes()[0]
    assert trade.pnl == pytest.approx(39.5 - 100.5) and trade.lots == pytest.approx(0.5)
    assert trade.meta["partial_pnl"] == pytest.approx(39.5)
