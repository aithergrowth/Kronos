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
    "XAUUSD": SymbolSpec("XAUUSD", 0.1, 10.0, typical_spread_pips=2.0, price_decimals=2, tradingview_symbol="OANDA:XAUUSD"),
    "NAS100": SymbolSpec("NAS100", 1.0, 1.0, typical_spread_pips=1.5, price_decimals=1, tradingview_symbol="OANDA:NAS100USD"),
    "US30": SymbolSpec("US30", 1.0, 1.0, typical_spread_pips=2.0, price_decimals=1, tradingview_symbol="OANDA:US30USD"),
    "BTCUSD": SymbolSpec("BTCUSD", 1.0, 1.0, typical_spread_pips=15.0, price_decimals=1, tradingview_symbol="BINANCE:BTCUSDT"),
}


@dataclass
class StructureParams:
    swing_left: int = 2                 # fractal bars to the left of a swing
    swing_right: int = 2                # fractal bars to the right (confirmation delay)
    lookback: int = 400                 # candles analysed per timeframe
    equal_level_tolerance_pct: float = 0.0003   # equal highs/lows clustering (0.03 %)
    full_body_break: bool = False       # ASSUMPTION: BOS = close beyond level (True = whole body beyond)
    block_body_only: bool = False       # balance block = full candle range (True = body only)
    max_bars_sweep_to_break: int = 40   # a sweep must be followed by a break within this many candles to form a POI


@dataclass
class BiasParams:
    liquidity_lookback: int = 80        # ASSUMPTION: a sweep older than this no longer drives the liquidity view
    min_matching_timeframes: int = 3    # rule: minimum 3/5 timeframes must match
    full_combos: Tuple[Tuple[Timeframe, ...], ...] = (
        (Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1),
        (Timeframe.W_1, Timeframe.D_1, Timeframe.H_4),
        (Timeframe.MN_1, Timeframe.D_1, Timeframe.H_1),
    )
    scalp_combo: Tuple[Timeframe, ...] = (Timeframe.D_1, Timeframe.H_4, Timeframe.H_1)


@dataclass
class ConfirmationParams:
    allow_first_candle: bool = False    # rule lists "first bullish/bearish candle"; off by default (see STRATEGY.md Q5)
    max_extension_zones: float = 1.5    # ASSUMPTION: confirmation must close within N POI-heights beyond the zone
    allow_retest: bool = False          # ASSUMPTION: only the first return to a POI is traded
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
    risk_pct: float = 1.0               # rule: 1 % risk per trade
    min_rr: float = 3.0                 # rule: minimum 1:3
    spread_buffer_pips: float = 1.0     # rule: 1-pip protection buffer in lot sizing
    sl_offset_pips: float = 1.0         # ASSUMPTION: "strictly behind" = 1 pip beyond the invalidation swing
    tp_policy: str = "nearest"          # nearest | liquidity_first | balance_first
    rr_includes_buffer: bool = True     # ASSUMPTION: R:R measured on the same distance used for sizing


@dataclass
class ExitParams:
    breakeven_r_swing: float = 2.0      # rule: swing (M, W POI) -> break-even after 2R
    breakeven_r_intraday: float = 4.0   # rule: intraday/scalp (D, 4H, 1H POI) -> break-even after 4R
    partials: bool = False              # rule: no partials
    breakeven_offset_pips: float = 0.0  # 0 = exact entry


@dataclass
class KronosParams:
    mode: str = "advisory"              # off | advisory | filter
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
    max_open_trades: int = 1            # rule: max 1 trade per funded account
    daily_loss_limit_pct: float = 4.0   # stay inside the typical 5 % rule with margin
    max_drawdown_pct: float = 8.0       # stay inside the typical 10 % rule with margin
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
class Settings:
    account_size: float = 100_000.0
    account_currency: str = "USD"
    symbols: Dict[str, SymbolSpec] = field(default_factory=lambda: dict(DEFAULT_SYMBOLS))
    structure: StructureParams = field(default_factory=StructureParams)
    bias: BiasParams = field(default_factory=BiasParams)
    confirmation: ConfirmationParams = field(default_factory=ConfirmationParams)
    risk: RiskParams = field(default_factory=RiskParams)
    exits: ExitParams = field(default_factory=ExitParams)
    kronos: KronosParams = field(default_factory=KronosParams)
    prop_firm: PropFirmParams = field(default_factory=PropFirmParams)
    telegram: TelegramParams = field(default_factory=TelegramParams)
    tradingview: TradingViewParams = field(default_factory=TradingViewParams)

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
        return cls.from_dict(data)

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
            return {Timeframe.parse(k): Timeframe.parse(v) for k, v in value.items()}
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
