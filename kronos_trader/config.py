"""Configuration for the trading system.

Everything the rules need as a number lives here so nothing is hidden inside
the strategy code.  Defaults encode the Dorus Wanders rule set as given; the
items marked ``ASSUMPTION`` are interpretations that still need sign-off (see
docs/STRATEGY.md).  Secrets are read from environment variables, never from
YAML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .core.timeframe import Timeframe


@dataclass
class SymbolSpec:
    """Contract details needed for pip maths and lot sizing.

    ``pip_value_per_lot`` is the account-currency value of one pip for one
    standard lot.  VERIFY THESE WITH THE BROKER / PROP FIRM before going live:
    pip value for non-USD quote currencies moves with the exchange rate.
    """
    symbol: str
    pip_size: float
    pip_value_per_lot: float = 10.0
    lot_step: float = 0.01
    min_lot: float = 0.01
    max_lot: float = 100.0
    typical_spread_pips: float = 1.0
    price_decimals: int = 5
    tradingview_symbol: Optional[str] = None   # e.g. OANDA:EURUSD
    mt5_symbol: Optional[str] = None           # broker-specific name, e.g. EURUSD.r
    contract_size: float = 100_000.0           # units per 1.0 lot (forex standard lot)
    ibkr_contract: Optional[str] = None        # "forex" | "cfd:IBUST100" | "stock:AAPL:SMART:USD" | "crypto:BTC:PAXOS:USD"
    oanda_instrument: Optional[str] = None     # OANDA v20 name, e.g. EUR_USD (derived from the symbol when unset)

    def pips(self, distance: float) -> float:
        return distance / self.pip_size

    def round_price(self, price: float) -> float:
        return round(price, self.price_decimals)


DEFAULT_SYMBOLS: Dict[str, SymbolSpec] = {
    "EURUSD": SymbolSpec("EURUSD", 0.0001, 10.0, tradingview_symbol="OANDA:EURUSD"),
    "GBPUSD": SymbolSpec("GBPUSD", 0.0001, 10.0, typical_spread_pips=1.2, tradingview_symbol="OANDA:GBPUSD"),
    "AUDUSD": SymbolSpec("AUDUSD", 0.0001, 10.0, tradingview_symbol="OANDA:AUDUSD"),
    "NZDUSD": SymbolSpec("NZDUSD", 0.0001, 10.0, typical_spread_pips=1.5, tradingview_symbol="OANDA:NZDUSD"),
    "USDCAD": SymbolSpec("USDCAD", 0.0001, 7.3, typical_spread_pips=1.5, tradingview_symbol="OANDA:USDCAD"),
    "USDCHF": SymbolSpec("USDCHF", 0.0001, 11.0, typical_spread_pips=1.5, tradingview_symbol="OANDA:USDCHF"),
    "USDJPY": SymbolSpec("USDJPY", 0.01, 6.5, price_decimals=3, tradingview_symbol="OANDA:USDJPY"),
    "XAUUSD": SymbolSpec("XAUUSD", 0.1, 10.0, typical_spread_pips=2.0, price_decimals=2, tradingview_symbol="OANDA:XAUUSD",
                         contract_size=100.0, ibkr_contract="cfd:XAUUSD"),
    "NAS100": SymbolSpec("NAS100", 1.0, 1.0, typical_spread_pips=1.5, price_decimals=1, tradingview_symbol="OANDA:NAS100USD",
                         contract_size=1.0, ibkr_contract="cfd:IBUST100"),
    "US30": SymbolSpec("US30", 1.0, 1.0, typical_spread_pips=2.0, price_decimals=1, tradingview_symbol="OANDA:US30USD",
                       contract_size=1.0, ibkr_contract="cfd:IBUS30"),
    "BTCUSD": SymbolSpec("BTCUSD", 1.0, 1.0, typical_spread_pips=15.0, price_decimals=1, tradingview_symbol="BINANCE:BTCUSDT",
                         contract_size=1.0, ibkr_contract="crypto:BTC:PAXOS:USD"),
}


@dataclass
class StructureParams:
    swing_left: int = 2                 # fractal bars to the left of a swing
    swing_right: int = 2                # fractal bars to the right (confirmation delay)
    lookback: int = 400                 # candles analysed per timeframe (lower timeframes)
    lookback_by_timeframe: Dict[Timeframe, int] = field(default_factory=lambda: {   # "hou het lokaal" (S1)
        Timeframe.MN_1: 60, Timeframe.W_1: 104, Timeframe.D_1: 250, Timeframe.H_4: 300, Timeframe.H_1: 300})
    equal_level_tolerance_pct: float = 0.0003   # equal highs/lows clustering (0.03 %)
    full_body_break: bool = False       # a close beyond the level is the break ("closure", A 02:26:06); True = whole body beyond
    block_body_only: bool = False       # order block (candle 1) = full candle range (True = body only)
    min_gap_fraction: float = 0.2       # ASSUMPTION: a balance level (gap) must be >= this fraction of the median candle range
    poi_mode: str = "liquidity_to_protection"   # D 12:21 / F 03:00: zone = liquidity taken by the displacement (X) -> gap -> P; legacy: sweep_to_gap
    poi_break_window: int = 3           # the displacement must close through X between P and this many candles after candle 3
    max_bars_sweep_to_balance: int = 40 # legacy mode: the balance level must form within this many candles after the sweep
    poi_requires_break: bool = False    # legacy mode: also require a structure break
    poi_far_edge: str = "gap_bottom"    # legacy mode: gap_bottom | gap_top | protector


@dataclass
class BiasParams:
    liquidity_lookback: int = 80        # ASSUMPTION: a sweep older than this no longer drives the liquidity view
    balance_violation: str = "flip"     # when P breaks: "flip" = continuation in the break direction (A 01:41:49), "neutral" = 50/50
    min_matching_timeframes: int = 3    # rule: minimum 3/5 timeframes must match
    full_combos: Tuple[Tuple[Timeframe, ...], ...] = (                            # K1 02:17 (written plan)
        (Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1),
        (Timeframe.W_1, Timeframe.D_1, Timeframe.H_4),
        (Timeframe.MN_1, Timeframe.D_1, Timeframe.H_1),
    )
    extra_combos: Tuple[Tuple[Timeframe, ...], ...] = ((Timeframe.MN_1, Timeframe.D_1, Timeframe.H_4),)  # stated in A and D (two dated videos), absent from the K1 slide
    extra_combos_enabled: bool = True
    scalp_combo: Tuple[Timeframe, ...] = (Timeframe.D_1, Timeframe.H_4, Timeframe.H_1)

    @property
    def active_full_combos(self) -> Tuple[Tuple[Timeframe, ...], ...]:
        return tuple(self.full_combos) + (tuple(self.extra_combos) if self.extra_combos_enabled else ())


@dataclass
class SessionParams:
    """Entries only inside Dorus's stated windows (A 02:24:03 / 02:30:48, Amsterdam clock); open trades run on."""
    enabled: bool = True
    timezone: str = "Europe/Amsterdam"
    windows: Tuple[Tuple[str, str], ...] = (("09:00", "17:00"),)   # Max: Dorus works 9 to 5. A's split 09-11 / 13-17 and C's 08-17 are the variants
    weekdays: Tuple[int, ...] = (0, 1, 2, 3, 4)


@dataclass
class ConfirmationParams:
    allow_balance_shift: bool = True    # K1 06:30 option "BS" (balance shift) - the plan's primary confirmation
    allow_first_candle: bool = False    # K1 06:30 lists it; G 10:49 shows it as the entry after a shift, not instead of one. Off for the defensive forward test
    accept_bos: bool = True             # a continuation break is accepted as well (not in the written option list)
    bs_threshold: str = "gap_edge"      # gap_edge: close beyond the opposing gap (A 02:25:40); protector: beyond the candle that caused it (A 01:07:49)
    opposing_gap_lookback: int = 60     # how far before the touch the opposing balance level may have formed
    max_extension_zones: float = 1.5    # ASSUMPTION: confirmation must close within N POI-heights beyond the zone
    allow_retest: bool = False          # ASSUMPTION: only the first return to a POI is traded (Q13 not stated)
    # Rule: Monthly POI -> min. 4H, Weekly -> 1H, Daily -> 15m, 4H -> 5m, 1H -> 1m
    min_confirmation_tf: Dict[Timeframe, Timeframe] = field(default_factory=lambda: {
        Timeframe.MN_1: Timeframe.H_4,
        Timeframe.W_1: Timeframe.H_1,
        Timeframe.D_1: Timeframe.MIN_15,
        Timeframe.H_4: Timeframe.MIN_5,
        Timeframe.H_1: Timeframe.MIN_1,
    })
    scalp_poi_timeframes: Tuple[Timeframe, ...] = (Timeframe.H_4, Timeframe.H_1)  # ASSUMPTION: "scalp only" = intraday POIs


@dataclass
class RiskParams:
    risk_pct: float = 1.0               # rule: 1 % risk per trade (K1 06:30)
    min_rr: float = 3.0                 # Max's rule. Dorus's accepted examples run 0.7R-1.7R (A/B/C) - decide, see STRATEGY.md
    spread_buffer_pips: float = 1.0     # Max's rule (not found in Dorus's material, Q7)
    sl_offset_pips: float = 1.0         # ASSUMPTION: 1 pip beyond the protection level
    tp_policy: str = "liquidity"        # "Dus ik zet ten alle tijden mijn take profit op liquiditeit" (A 01:50:40): nearest liquidity on the POI timeframe or higher;
                                        # liquidity_nearest: nearest liquidity on any timeframe above the confirmation timeframe (dorus_pure.yaml); legacy: nearest | liquidity_first | balance_first
    stop_basis: str = "protector"       # "SL ALTIJD op minimale 1H P" (K1 06:30); legacy: confirmation (LTF invalidation swing)
    rr_includes_buffer: bool = True     # ASSUMPTION: R:R measured on the same distance used for sizing


@dataclass
class ExitParams:
    breakeven_r_swing: float = 2.0      # rule: swing (M, W POI) -> break-even after 2R
    breakeven_r_intraday: float = 4.0   # rule: intraday/scalp (D, 4H, 1H POI) -> break-even after 4R
    partials: bool = False              # rule: no partials
    breakeven_offset_pips: float = 0.0  # 0 = exact entry


@dataclass
class KronosParams:
    mode: str = "advisory"              # advisory = shown on charts and in messages, never a gate; filter = a gate (phase 1: it removed the only winner); off = model not loaded
    model: str = "NeoQuasar/Kronos-small"
    tokenizer: str = "NeoQuasar/Kronos-Tokenizer-base"
    device: Optional[str] = None        # None = auto (cuda / mps / cpu)
    max_context: int = 512
    lookback: int = 400
    horizon: int = 12                   # candles forecast on the confirmation timeframe
    n_paths: int = 5                    # sampled paths -> confidence
    temperature: float = 1.0
    top_p: float = 0.9
    top_k: int = 0
    neutral_band_pct: float = 0.1       # |expected move| below this % of price counts as neutral
    min_confidence: float = 0.6         # filter mode: reject when the forecast conflicts with >= this confidence
    forecast_timeframes: Tuple[Timeframe, ...] = (Timeframe.H_4, Timeframe.H_1)  # extra advisory forecasts


@dataclass
class PropFirmParams:
    """FTMO-style limits with margin: FTMO stops you at 5 % daily loss and 10 % total loss; this guard stops at 4 % and 8 %."""
    max_open_trades: int = 1            # rule: max 1 trade per funded account
    daily_loss_limit_pct: float = 4.0   # stay inside the typical 5 % rule with margin
    max_drawdown_pct: float = 8.0       # stay inside the typical 10 % rule with margin
    drawdown_basis: str = "peak"        # peak: from the highest equity seen (stricter); initial: static floor below the starting balance (FTMO)
    day_timezone: str = "Europe/Prague" # the day for the daily-loss rule starts at midnight here (FTMO: CE(S)T)
    news_blackout_minutes: int = 0      # optional: block entries N minutes around high-impact news
    min_minutes_between_trades: int = 0


@dataclass
class TelegramParams:
    enabled: bool = False
    bot_token_env: str = "TELEGRAM_BOT_TOKEN"
    chat_id_env: str = "TELEGRAM_CHAT_ID"
    parse_mode: str = "HTML"

    @property
    def bot_token(self) -> Optional[str]:
        return os.environ.get(self.bot_token_env)

    @property
    def chat_id(self) -> Optional[str]:
        return os.environ.get(self.chat_id_env)


@dataclass
class TradingViewParams:
    url: str = "https://mcp.tradingview.com/mcp"
    token_env: str = "TRADINGVIEW_MCP_TOKEN"
    default_exchange: str = "OANDA"
    cache_dir: str = "data/tv_cache"

    @property
    def token(self) -> Optional[str]:
        return os.environ.get(self.token_env)


@dataclass
class IBKRParams:
    """Interactive Brokers connection (TWS or IB Gateway). Paper TWS listens on 7497, paper Gateway on 4002."""
    host_env: str = "IBKR_HOST"
    port_env: str = "IBKR_PORT"
    client_id_env: str = "IBKR_CLIENT_ID"
    account_env: str = "IBKR_ACCOUNT"
    default_host: str = "127.0.0.1"
    default_port: int = 7497
    default_client_id: int = 17
    what_to_show: str = "MIDPOINT"      # bar type for forex structure (MIDPOINT | BID | ASK | TRADES)
    fill_wait_seconds: float = 2.0      # how long place_market_order waits for the fill confirmation
    max_quote_age_seconds: float = 300.0  # a 1-minute bar older than this is not a usable price

    @property
    def host(self) -> str:
        return os.environ.get(self.host_env, self.default_host)

    @property
    def port(self) -> int:
        return int(os.environ.get(self.port_env, self.default_port))

    @property
    def client_id(self) -> int:
        return int(os.environ.get(self.client_id_env, self.default_client_id))

    @property
    def account(self) -> str:
        return os.environ.get(self.account_env, "")


@dataclass
class NewsParams:
    """No new entries around high-impact news of the symbol's currencies (Dorus, source G 11:08: no entry right before news).

    Open trades run on.  Events come from ``calendar_csv`` (filled from the TradingView economic calendar) and,
    in the live loop, from the free ForexFactory weekly feed when ``forexfactory`` is on.
    """
    enabled: bool = True
    before_minutes: int = 30
    after_minutes: int = 30
    min_importance: int = 1                      # 1 = high-impact only, 0 = medium and high
    calendar_csv: str = "data/calendar/high_impact.csv"
    forexfactory: bool = True                    # live loop refreshes this week's events from ForexFactory
    refresh_minutes: int = 60


@dataclass
class MT5Params:
    """MetaTrader 5 terminal (Windows). Credentials and the terminal path come from environment variables."""
    login_env: str = "MT5_LOGIN"
    password_env: str = "MT5_PASSWORD"
    server_env: str = "MT5_SERVER"
    path_env: str = "MT5_PATH"                    # terminal64.exe, only when the terminal is not found automatically
    offset_env: str = "MT5_SERVER_OFFSET_HOURS"   # pin the server-time offset instead of estimating it from ticks
    magic: int = 20260930                         # marks the positions this program opened
    deviation_points: int = 20                    # max slippage for market orders
    filling: str = "ORDER_FILLING_IOC"            # ORDER_FILLING_FOK for brokers that reject IOC


@dataclass
class LiveParams:
    poll_seconds: int = 60
    require_approval: bool = True                  # human taps Approve in Telegram before an order is sent
    approval_timeout_minutes: Optional[int] = None  # None = one confirmation-timeframe candle (min 5 minutes)
    # every timeframe the engine needs comes from the broker; the TradingView cache is the fallback
    broker_timeframes: Tuple[Timeframe, ...] = (Timeframe.MIN_5, Timeframe.MIN_15, Timeframe.H_1, Timeframe.H_4,
                                                Timeframe.D_1, Timeframe.W_1, Timeframe.MN_1)
    broker_bar_counts: Dict[Timeframe, int] = field(default_factory=lambda: {
        Timeframe.MIN_5: 500, Timeframe.MIN_15: 500, Timeframe.H_1: 500, Timeframe.H_4: 400,
        Timeframe.D_1: 300, Timeframe.W_1: 120, Timeframe.MN_1: 72})
    notify_every_scan: bool = False
    briefing_time: Optional[str] = "08:45"   # Dorus analyses before the open: a bias and POI briefing at this local time (session timezone)
    notify_poi_touch: bool = True            # a heads-up when price enters a POI in the bias direction, before any confirmation
    send_charts: bool = True                 # a chart image with the briefing, the POI touch and every setup
    charts_dir: str = "charts"
    chart_lookback: int = 120                # candles on the image
    mt5_overlay: bool = True                 # with --broker mt5: write the forecast file the KronosForecast indicator draws
    journal_path: Optional[str] = "journal/trades.csv"   # every setup, decision, fill and close of the forward test
    max_data_age_bars: int = 2          # a timeframe is stale when its last candle closed more than N candles ago
    require_fresh_data: bool = True     # stale data: analyse and manage positions, but open no new setups
    feed_retry_seconds: int = 600       # after the live feed fails for every timeframe, leave it alone this long


@dataclass
class Settings:
    account_size: float = 100_000.0
    account_currency: str = "USD"
    symbols: Dict[str, SymbolSpec] = field(default_factory=lambda: dict(DEFAULT_SYMBOLS))
    structure: StructureParams = field(default_factory=StructureParams)
    bias: BiasParams = field(default_factory=BiasParams)
    session: SessionParams = field(default_factory=SessionParams)
    confirmation: ConfirmationParams = field(default_factory=ConfirmationParams)
    risk: RiskParams = field(default_factory=RiskParams)
    exits: ExitParams = field(default_factory=ExitParams)
    kronos: KronosParams = field(default_factory=KronosParams)
    prop_firm: PropFirmParams = field(default_factory=PropFirmParams)
    telegram: TelegramParams = field(default_factory=TelegramParams)
    tradingview: TradingViewParams = field(default_factory=TradingViewParams)
    ibkr: IBKRParams = field(default_factory=IBKRParams)
    mt5: MT5Params = field(default_factory=MT5Params)
    news: NewsParams = field(default_factory=NewsParams)
    live: LiveParams = field(default_factory=LiveParams)

    # ------------------------------------------------------------------ access
    def symbol(self, name: str) -> SymbolSpec:
        key = name.upper()
        if key not in self.symbols:
            raise KeyError(f"No SymbolSpec for {name!r}; add it to settings.symbols")
        return self.symbols[key]

    # ------------------------------------------------------------------ loading
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        settings = cls()
        for key, value in (data or {}).items():
            if key == "symbols":
                for sym, spec in value.items():
                    base = settings.symbols.get(sym.upper(), SymbolSpec(sym.upper(), 0.0001))
                    settings.symbols[sym.upper()] = _merge_dataclass(base, spec)
                continue
            if not hasattr(settings, key):
                raise KeyError(f"Unknown settings key {key!r}")
            current = getattr(settings, key)
            if is_dataclass(current) and isinstance(value, dict):
                setattr(settings, key, _merge_dataclass(current, value))
            else:
                setattr(settings, key, value)
        return settings

    @classmethod
    def from_yaml(cls, path: "str | Path") -> "Settings":
        import yaml  # local import: optional dependency for users who only use defaults
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        settings = cls.from_dict(data)
        if isinstance(settings.kronos.mode, bool):     # YAML 1.1 reads an unquoted `off` as False
            settings.kronos.mode = "off" if not settings.kronos.mode else "advisory"
        return settings

    @classmethod
    def load(cls, path: Optional["str | Path"] = None) -> "Settings":
        """Load ``path`` if given, else ``KRONOS_TRADER_CONFIG`` if set, else defaults."""
        path = path or os.environ.get("KRONOS_TRADER_CONFIG")
        if path and Path(path).exists():
            return cls.from_yaml(path)
        return cls()


def _coerce(field_type: Any, value: Any) -> Any:
    """Turn YAML scalars into the enum types the dataclasses use."""
    if value is None:
        return None
    text = str(field_type)
    if "Timeframe" in text:
        if isinstance(value, (list, tuple)):
            out = []
            for v in value:
                out.append(tuple(Timeframe.parse(x) for x in v) if isinstance(v, (list, tuple)) else Timeframe.parse(v))
            return tuple(out)
        if isinstance(value, dict):
            return {Timeframe.parse(k): (Timeframe.parse(v) if isinstance(v, str) else v) for k, v in value.items()}
        return Timeframe.parse(value)
    return value


def _merge_dataclass(instance: Any, overrides: Dict[str, Any]) -> Any:
    kwargs = {f.name: getattr(instance, f.name) for f in fields(instance)}
    types = {f.name: f.type for f in fields(instance)}
    for key, value in overrides.items():
        if key not in kwargs:
            raise KeyError(f"Unknown key {key!r} for {type(instance).__name__}")
        kwargs[key] = _coerce(types[key], value)
    return type(instance)(**kwargs)
