"""Domain types for the trading system.

Everything the strategy reasons about is an explicit, serialisable dataclass so
analyses can be logged, sent to Telegram, compared with hand-drawn charts and
shared with collaborators.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .timeframe import Timeframe


class Bias(Enum):
    BULLISH = 1
    NEUTRAL = 0   # the "50/50" of the rule set
    BEARISH = -1

    @property
    def opposite(self) -> "Bias":
        return Bias(-self.value)

    @property
    def sign(self) -> int:
        return self.value

    def __str__(self) -> str:
        return {1: "bullish", 0: "50/50", -1: "bearish"}[self.value]


class Direction(Enum):
    LONG = 1
    SHORT = -1

    @classmethod
    def from_bias(cls, bias: Bias) -> "Direction":
        if bias is Bias.NEUTRAL:
            raise ValueError("No direction for a 50/50 bias")
        return cls(bias.value)

    @property
    def bias(self) -> Bias:
        return Bias(self.value)

    @property
    def sign(self) -> int:
        return self.value


class SwingKind(Enum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True)
class SwingPoint:
    index: int
    timestamp: pd.Timestamp
    price: float
    kind: SwingKind


class LiquiditySide(Enum):
    BUY_SIDE = "buy_side"    # resting above swing highs (BSL)
    SELL_SIDE = "sell_side"  # resting below swing lows (SSL)


@dataclass
class LiquidityLevel:
    price: float
    side: LiquiditySide
    swing: SwingPoint
    touches: int = 1                 # equal highs / lows stacked on this level
    swept_index: Optional[int] = None
    broken_index: Optional[int] = None

    @property
    def index(self) -> int:
        return self.swing.index

    @property
    def timestamp(self) -> pd.Timestamp:
        return self.swing.timestamp

    @property
    def is_swept(self) -> bool:
        return self.swept_index is not None

    @property
    def is_broken(self) -> bool:
        return self.broken_index is not None

    @property
    def is_resting(self) -> bool:
        """Liquidity that has neither been swept nor closed through (a valid target)."""
        return not self.is_swept and not self.is_broken


@dataclass
class Sweep:
    """A wick pierce through a liquidity level with the body closing back inside."""
    level: LiquidityLevel
    index: int
    timestamp: pd.Timestamp
    extreme: float          # the wick extreme (the actual liquidity line that was taken)
    close: float

    @property
    def implied_bias(self) -> Bias:
        # sell-side liquidity taken -> expect the move up (and vice versa)
        return Bias.BULLISH if self.level.side is LiquiditySide.SELL_SIDE else Bias.BEARISH


class BreakKind(Enum):
    BOS = "BOS"   # break of structure - continuation
    BMS = "BMS"   # break of market structure - reversal (a.k.a. CHoCH)


@dataclass
class StructureBreak:
    index: int
    timestamp: pd.Timestamp
    direction: Bias
    kind: BreakKind
    broken_level: float
    broken_swing: SwingPoint
    origin_index: int      # candle holding the invalidation extreme that created the break
    origin_price: float    # the invalidation swing high/low
    close: float


@dataclass
class BalanceBlock:
    """Balance / order block: the last opposing candle before the impulse that broke structure."""
    direction: Bias
    low: float
    high: float
    index: int
    timestamp: pd.Timestamp
    break_index: int
    mitigated_index: Optional[int] = None
    violated_index: Optional[int] = None   # a close through the far side of the block

    @property
    def is_mitigated(self) -> bool:
        return self.mitigated_index is not None

    @property
    def is_violated(self) -> bool:
        return self.violated_index is not None

    @property
    def height(self) -> float:
        return self.high - self.low


@dataclass
class Gap:
    """Balance level in Dorus's vocabulary: the gap between candle 1 and candle 3 of a
    displacement (an imbalance).  ``protector`` is candle 2, the candle that created the
    balance level - the protected zone (P).  ``origin`` is candle 1 (the order block)."""
    direction: Bias
    low: float
    high: float
    index: int                 # candle 3: the gap exists once this candle closes
    timestamp: pd.Timestamp
    protector_index: int
    protector_low: float
    protector_high: float
    origin_index: int
    mitigated_index: Optional[int] = None   # price traded back into the gap
    violated_index: Optional[int] = None    # a close beyond the protector's far extreme ("P breaks")

    @property
    def height(self) -> float:
        return self.high - self.low

    @property
    def is_mitigated(self) -> bool:
        return self.mitigated_index is not None

    @property
    def is_violated(self) -> bool:
        return self.violated_index is not None

    @property
    def protection_level(self) -> float:
        """Far extreme of the protector candle: the level a stop sits behind."""
        return self.protector_low if self.direction is Bias.BULLISH else self.protector_high


class POIStatus(Enum):
    FRESH = "fresh"              # price has not returned since the POI formed
    ACTIVE = "active"            # price is inside the zone now
    TESTED = "tested"            # price returned earlier and left again
    INVALIDATED = "invalidated"  # a close beyond the protecting liquidity line


@dataclass
class POI:
    """Point of interest: "X to b/P" - from the liquidity the displacement took (X) through the
    balance level (b, the gap) down to the protector candle (P) that created it.  Price can react
    just inside the area, midway, after filling the gap, or deeper at protection (F 03:00-03:36);
    interest ends below P (D 12:42)."""
    timeframe: Timeframe
    direction: Bias
    low: float
    high: float
    sweep: Optional[Sweep]
    balance: Optional[BalanceBlock]
    created_index: int
    created_at: pd.Timestamp
    gap: Optional[Gap] = None
    liquidity_level: Optional[float] = None      # X: the level the displacement closed through
    liquidity_break: Optional[StructureBreak] = None
    status: POIStatus = POIStatus.FRESH
    first_touch_index: Optional[int] = None

    @property
    def height(self) -> float:
        return self.high - self.low

    @property
    def protection_level(self) -> float:
        """The liquidity line that protects the zone (an invalidation if closed through)."""
        return self.low if self.direction is Bias.BULLISH else self.high

    @property
    def protector_low(self) -> float:
        if self.gap is not None:
            return self.gap.protector_low
        return self.balance.low if self.balance is not None else self.low

    @property
    def protector_high(self) -> float:
        if self.gap is not None:
            return self.gap.protector_high
        return self.balance.high if self.balance is not None else self.high

    @property
    def protector_extreme(self) -> float:
        """Far extreme of P: where "SL altijd op minimale 1H P" puts the stop for this timeframe."""
        return self.protector_low if self.direction is Bias.BULLISH else self.protector_high

    @property
    def key(self) -> Tuple[str, int, str]:
        return (self.timeframe.label, self.direction.value, str(self.created_at))

    def contains(self, price: float, tolerance: float = 0.0) -> bool:
        return (self.low - tolerance) <= price <= (self.high + tolerance)

    def describe(self) -> str:
        return (f"{self.timeframe.label} {self.direction} POI {self.low:.5f}-{self.high:.5f} "
                f"({self.status.value}, formed {self.created_at})")


@dataclass
class TimeframeBias:
    timeframe: Timeframe
    bias: Bias
    liquidity_view: Bias
    balance_view: Bias
    notes: List[str] = field(default_factory=list)


class TradeMode(Enum):
    FULL = "full"      # a valid 3/5 combo -> swing / intraday trades allowed
    SCALP = "scalp"    # 1D+4H+1H only -> scalp only
    NONE = "none"      # no match -> no trade


@dataclass
class BiasDecision:
    direction: Bias
    mode: TradeMode
    aligned: Tuple[Timeframe, ...]
    conflicting: Tuple[Timeframe, ...]
    neutral: Tuple[Timeframe, ...]
    matched_combo: Optional[Tuple[Timeframe, ...]]
    reason: str

    @property
    def tradable(self) -> bool:
        return self.mode is not TradeMode.NONE and self.direction is not Bias.NEUTRAL


class ConfirmationType(Enum):
    BS = "BS"                    # balance shift: body close through the opposing balance level
    BMS = "BMS"                  # break of market structure (reversal of the lower-timeframe trend)
    BOS = "BOS"                  # continuation break (accepted, not in the written plan's option list)
    FIRST_CANDLE = "first_candle"

    @property
    def priority(self) -> int:
        return {"BS": 0, "BMS": 1, "BOS": 2, "first_candle": 3}[self.value]


@dataclass
class Confirmation:
    type: ConfirmationType
    timeframe: Timeframe
    index: int
    timestamp: pd.Timestamp
    direction: Bias
    break_level: float
    invalidation_price: float
    close: float


@dataclass
class ForecastSummary:
    """Kronos forecast distilled into what the strategy needs."""
    timeframe: Timeframe
    horizon: int
    direction: Bias
    confidence: float              # share of sampled paths agreeing with the mean path
    last_close: float
    expected_close: float
    expected_high: float
    expected_low: float
    pct_change: float
    paths: int
    model: str
    paths_ohlc: Optional[List[pd.DataFrame]] = field(default=None, repr=False, compare=False)   # sampled paths, for charts

    def agrees_with(self, bias: Bias) -> bool:
        return self.direction is bias

    def conflicts_with(self, bias: Bias) -> bool:
        return self.direction is not Bias.NEUTRAL and self.direction is not bias


@dataclass
class TradeSetup:
    symbol: str
    direction: Direction
    poi: POI
    confirmation: Confirmation
    entry: float
    stop: float
    take_profit: float
    risk_distance: float       # entry->stop distance used for sizing (includes the spread buffer)
    reward_distance: float
    rr: float
    lots: float
    risk_amount: float
    breakeven_r: float
    tp_source: str
    notes: List[str] = field(default_factory=list)

    @property
    def stop_pips(self) -> Optional[float]:
        return None


class SignalStatus(Enum):
    VALID = "valid"
    REJECTED = "rejected"


@dataclass
class Signal:
    timestamp: pd.Timestamp
    status: SignalStatus
    setup: Optional[TradeSetup]
    forecast: Optional[ForecastSummary]
    reasons: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.status is SignalStatus.VALID and self.setup is not None


@dataclass
class Analysis:
    symbol: str
    timestamp: pd.Timestamp
    price: float
    biases: Dict[Timeframe, TimeframeBias]
    decision: BiasDecision
    pois: List[POI]
    signal: Optional[Signal]
    rejections: List[str] = field(default_factory=list)
    forecasts: Dict[Timeframe, ForecastSummary] = field(default_factory=dict)

    @property
    def has_valid_signal(self) -> bool:
        return self.signal is not None and self.signal.is_valid

    def to_dict(self) -> dict:
        def conv(o):
            if isinstance(o, Enum):
                return o.value if not isinstance(o, Timeframe) else o.label
            if isinstance(o, pd.Timestamp):
                return o.isoformat()
            if isinstance(o, pd.DataFrame):
                return None
            if hasattr(o, "__dataclass_fields__"):
                return {k: conv(getattr(o, k)) for k in o.__dataclass_fields__ if k != "paths_ohlc"}
            if isinstance(o, dict):
                return {str(conv(k)): conv(v) for k, v in o.items()}
            if isinstance(o, (list, tuple)):
                return [conv(v) for v in o]
            return o
        return conv(self)
