"""Configuration for the trading system.

Everything the rules need as a number lives here so nothing is hidden inside
the strategy code.  Defaults encode the Dorus Wanders rule set as given; the
items marked ``ASSUMPTION`` are interpretations that still need sign-off (see
docs/STRATEGY.md).  Secrets are read from environment variables, never from
YAML.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field, fields, is_dataclass, replace
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
    commission_per_lot: float = 0.0           # backtest costs: account currency a 1.0 lot round turn (FTMO forex: about 3)
    commission_pct: float = 0.0               # and/or % of the entry's notional, round turn (FTMO crypto: about 0.065)

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
    "US500": SymbolSpec("US500", 1.0, 1.0, typical_spread_pips=0.5, price_decimals=1, tradingview_symbol="OANDA:SPX500USD",
                        contract_size=1.0),         # S&P 500 CFD: a "pip" is one index point (HistData SPXUSD)
    "GER40": SymbolSpec("GER40", 1.0, 1.0, typical_spread_pips=1.0, price_decimals=1, tradingview_symbol="OANDA:DE30EUR",
                        contract_size=1.0),         # DAX CFD, one index point (HistData GRXEUR); P&L in EUR on the broker
    "XAGUSD": SymbolSpec("XAGUSD", 0.01, 50.0, typical_spread_pips=2.5, price_decimals=3, tradingview_symbol="OANDA:XAGUSD",
                         contract_size=5000.0),     # silver, 5,000 oz a lot: 50 USD a 0.01 move
    "US30": SymbolSpec("US30", 1.0, 1.0, typical_spread_pips=2.0, price_decimals=1, tradingview_symbol="OANDA:US30USD",
                       contract_size=1.0, ibkr_contract="cfd:IBUS30"),
    # more FTMO index and oil CFDs for research (HistData JPXJPY, ETXEUR, FRXEUR, AUXAUD, HKXHKD, WTIUSD, BCOUSD); a "pip" is one
    # index point or 0.01 of oil; P&L in the index's own currency on the broker, the backtests count in R
    "JP225": SymbolSpec("JP225", 1.0, 1.0, typical_spread_pips=8.0, price_decimals=1, tradingview_symbol="OANDA:JP225USD",
                        contract_size=1.0),
    "EU50": SymbolSpec("EU50", 1.0, 1.0, typical_spread_pips=1.5, price_decimals=1, tradingview_symbol="OANDA:EU50EUR",
                       contract_size=1.0),
    "FRA40": SymbolSpec("FRA40", 1.0, 1.0, typical_spread_pips=1.2, price_decimals=1, tradingview_symbol="OANDA:FR40EUR",
                        contract_size=1.0),
    "AUS200": SymbolSpec("AUS200", 1.0, 1.0, typical_spread_pips=1.5, price_decimals=1, tradingview_symbol="OANDA:AU200AUD",
                         contract_size=1.0),
    "HK50": SymbolSpec("HK50", 1.0, 1.0, typical_spread_pips=8.0, price_decimals=1, tradingview_symbol="OANDA:HK33HKD",
                       contract_size=1.0),
    "USOIL": SymbolSpec("USOIL", 0.01, 10.0, typical_spread_pips=3.0, price_decimals=3, tradingview_symbol="OANDA:WTICOUSD",
                        contract_size=1000.0),   # WTI, 1,000 barrels a lot: 10 USD a 0.01 move
    "UKOIL": SymbolSpec("UKOIL", 0.01, 10.0, typical_spread_pips=3.0, price_decimals=3, tradingview_symbol="OANDA:BCOUSD",
                        contract_size=1000.0),   # Brent, the same
    "BTCUSD": SymbolSpec("BTCUSD", 1.0, 1.0, typical_spread_pips=15.0, price_decimals=1, tradingview_symbol="BINANCE:BTCUSDT",
                         contract_size=1.0, ibkr_contract="crypto:BTC:PAXOS:USD"),
    "ETHUSD": SymbolSpec("ETHUSD", 0.1, 0.1, typical_spread_pips=10.0, price_decimals=2, tradingview_symbol="BINANCE:ETHUSDT",
                         contract_size=1.0, max_lot=1000.0),   # one ETH a lot: a pip of 0.1 USD is worth 0.1 USD
    "DXY": SymbolSpec("DXY", 0.01, 1.0, typical_spread_pips=3.0, price_decimals=3, tradingview_symbol="TVC:DXY",
                      contract_size=1.0),            # the dollar index as a CFD (ICE DX): a pip of 0.01 is 0.01 % of price, like EURUSD's
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
    gap_median_window: int = 100        # ... of the candles before it (as-of, so later candles never reclassify an old gap)
    poi_mode: str = "liquidity_to_protection"   # D 12:21 / F 03:00: zone = liquidity taken by the displacement (X) -> gap -> P; legacy: sweep_to_gap
    poi_break_window: int = 3           # the displacement must close through X between P and this many candles after candle 3
    poi_extent: str = "liquidity"       # how far a zone reaches from P: liquidity = to X, the level the displacement took (the course's
                                        # "X to b/P", K1 03:54, D 12:21); gap = to the balance level's near edge (b/P, without the run to X);
                                        # protector = P alone, the candle that made the gap. Max, 7 October: "Dorus doet het wat anders"
    poi_gap_choice: str = "first"       # several gaps in one impulse before its break: first = the earliest, the deepest P (the zone from the
                                        # impulse's start); last = the gap nearest the break, the P closest to X (a tighter zone)
    poi_gap_zones: bool = False         # also a gap whose displacement took no liquidity maps a zone, from its P to the gap's far edge (his
                                        # "price gap" trades: gold 12 Aug 2025, bought at the top of the daily gap the NFP candle of 1 Aug left)
    max_bars_sweep_to_balance: int = 40 # legacy mode: the balance level must form within this many candles after the sweep
    poi_requires_break: bool = False    # legacy mode: also require a structure break
    poi_far_edge: str = "gap_bottom"    # legacy mode: gap_bottom | gap_top | protector


@dataclass
class BiasParams:
    liquidity_lookback: int = 80        # ASSUMPTION: a sweep older than this no longer drives the liquidity view
    balance_violation: str = "flip"     # when P breaks: "flip" = continuation in the break direction (A 01:41:49), "neutral" = 50/50
    balance_view: str = "last_gap"      # last_gap: the most recent balance level formed gives the view; last_tested: the most recent balance
                                        # level price has traded into ("een balance level wat we hier hebben getest", A 00:57:51) gives it, held
                                        # = its direction, broken = the continuation; a reading tested on his dated days (bias suite)
    min_matching_timeframes: int = 3    # rule: minimum 3/5 timeframes must match
    full_combos: Tuple[Tuple[Timeframe, ...], ...] = (                            # K1 02:17 (written plan)
        (Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1),
        (Timeframe.W_1, Timeframe.D_1, Timeframe.H_4),
        (Timeframe.MN_1, Timeframe.D_1, Timeframe.H_1),
    )
    extra_combos: Tuple[Tuple[Timeframe, ...], ...] = ((Timeframe.MN_1, Timeframe.D_1, Timeframe.H_4),)  # stated in A and D (two dated videos), absent from the K1 slide
    extra_combos_enabled: bool = True
    scalp_combo: Tuple[Timeframe, ...] = (Timeframe.D_1, Timeframe.H_4, Timeframe.H_1)
    scalp_enabled: bool = True          # False: the scalp combination is not a match (loss anatomy, 4 October: on EURUSD 2023-2026 the
                                        # 49 scalps won 43 % for -1.5R, the 24 full-combination trades 62 % for +13.3R)
    no_trade_against: Tuple[Timeframe, ...] = ()   # timeframes that veto a match when they read the opposite direction (loss anatomy,
                                        # 4 October: gold shorts 2023-2026 38 %, -8.6R against a bullish monthly; longs 47 %, +36.2R)
    conflict_rule: str = "neutral"      # what a timeframe reads when its liquidity view and balance view disagree: "neutral" = 50/50
                                        # (A 00:56:54, 02:14:26); "recent" = the more recent of the two events decides (a break after the
                                        # gap formed beats the gap, a gap formed after the break beats the break). Max, 4 October: "week en
                                        # maand gaan vaak ook wel goed" where the code read 50/50 because an old unmitigated gap outvoted
                                        # a fresh break (docs/practice/2026-09/EURUSD/v3, the 1W and 1M notes of every dossier)
    required_aligned: Tuple[Timeframe, ...] = ()   # timeframes that must be among the aligned ones for any match (data, 2 October: with the
                                                   # 1H aligned the whole-period version-2 trades gave EURUSD +6.8R against -4.5R without it,
                                                   # gold +14.8R against -7.0R; not a rule of his in words, kept as an option)
    reclaim_candles: int = 0            # 0 = off; else a break whose broken level a close takes back within this many candles reads as a sweep
                                        # of that level in the liquidity view. His gold long of 18 Sep 2025: the 1H closed under the FOMC low at
                                        # 06:00 UTC and back above it at 07:00; he traded the sweep, the code read the break and kept the 1H bearish
    shift_flips_balance: bool = False   # the balance view turns when a close goes beyond the far edge of the last gap (the balance shift the
                                        # confirmation trades, bs_threshold gap_edge), not only when its P is closed through
    mirror_symbol: Optional[str] = None     # read the bias of these timeframes from another market and invert it: his EURUSD short of
                                            # 11 Nov 2025 was read from the dollar index ("waarom zit ik in EURUSD shorts? ... laten we beginnen
                                            # met de DXY", A 00:56:25-00:57:25); DXY = EURUSD mirrored. None = the pair's own levels
    mirror_data_dir: Optional[str] = None   # cache directory with <mirror_symbol>_<TF>.csv (data/dxy: TradingView TVC:DXY daily, weekly, monthly)
    mirror_timeframes: Tuple[Timeframe, ...] = (Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1)   # the course mirrors the monthly down
    mirror_invert: bool = True              # EURUSD moves against the dollar index

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
    allow_bms: bool = True              # the written list names BMS (K1 06:30); his course treats the plain structure break as a liquidity sweep
                                        # and enters on the balance shift instead (A 01:29:29, 01:30:56, 01:33:47): off in config/dorus_course.yaml
    entry_after_shift: bool = False     # "na de shift ga ik altijd bij de eerste beste bullish candle erin" (A 01:21:00): the entry is the
                                        # first candle closing in the trade direction at or after the shift candle, not the shift close itself
    entry_after_shift_max_candles: int = 3   # give up when no such candle closes within this many candles after the shift
    bs_threshold: str = "gap_edge"      # gap_edge: close beyond the opposing gap (A 02:25:40); protector: beyond the candle that caused it (A 01:07:49)
    bs_requires_structure: bool = False # True: a balance shift counts once the entry timeframe's structure has also broken in the trade's
                                        # direction since the touch (a close through its last swing: the liquidity); a break up to
                                        # bs_structure_window candles after the shift moves the entry to that candle (Max, 7 October: he
                                        # "stapt pas in als de liquiditeit [en het] balance level in de 5m candle doorbreekt")
    bs_structure_window: int = 12
    bs_requires_sweep: bool = False     # True: a balance shift counts only when the entry timeframe swept liquidity in the trade's favour
                                        # since the touch (a wick through a swing low for a long, the body closing back above it): the
                                        # liquidity is taken, then price shifts (Max, 7 October: "marktstructuur en liquiditeit")
    opposing_gap_lookback: int = 60     # how far before the touch the opposing balance level may have formed
    search_from_reentry: bool = True    # the confirmation search starts at price's latest entry into the zone within the open visit, not at the
                                        # visit's first touch: a zone can be left and re-entered while the visit stays open, and the shift and the
                                        # sweep extreme belong to the last approach (his EURUSD short of 11 Nov 2025: the 4H zone touched on 7 Nov,
                                        # re-entered by the spike of 11 Nov 13:22; the stop above that spike's high)
    max_extension_zones: float = 1.5    # ASSUMPTION: confirmation must close within N POI-heights beyond the zone
    allow_retest: bool = False          # ASSUMPTION: only the first return to a POI is traded (Q13 not stated)
    max_adverse_move_atr: float = 0.0   # 0 = off; else no entry when the last 24 closed 1H candles moved this many average 1H ranges
                                        # (ATR 24) against the trade: the zone is being run through, not tested (entry anatomy, 5 October,
                                        # five markets 2023-2026: 14 trades at 3 or more won 21 %, -7.9R, negative in 2024, 2025 and 2026)
    min_volatility_percentile: float = 0.0  # 0 = off; else no entry unless the average 4H range of the last day (6 candles) ranks at
                                        # least this high among the last 360 4H candles (60 days): the zones pay when the market moves
                                        # (big-winner anatomy, 5 October: BTC 2024-2026 in the top 40 % 71 trades, 65 %, +75.2R; below it
                                        # 74 trades, 38 %, -12.9R)
    max_zone_age_candles: int = 0       # 0 = off; else a zone older than this many candles of its own timeframe is not a candidate (loss
                                        # anatomy, 4 October, three markets: zones under 24 h old won 43-48 %, older ones 12-33 %; BTC
                                        # 2024-2026 the 44 trades from zones older than a day -19R, the 89 from fresh zones +72R)
    max_zone_age_by_tf: Dict[Timeframe, int] = field(default_factory=dict)   # the same limit per zone timeframe, in place of
                                        # max_zone_age_candles for the timeframes it names (0 = no limit there), e.g. {1H: 24}
    max_touch_age_hours: float = 0.0    # 0 = off; else a visit that began more than this many hours after the zone formed is not
                                        # traded, whatever the zone's timeframe (7 October, the set that runs, 2024-02 to 2026-09
                                        # with FTMO's costs: touched within a day 299 trades, 53 %, +140.7R; later 39 trades, 28 %,
                                        # -25.0R, losing in both halves and in every market)
    poi_in_poi: bool = False            # a zone is traded only when it lies in a zone of a higher timeframe in the same direction that
                                        # is not invalidated: "POI in een POI = trade pas plaatsen bij een aantrekkelijke RR" (the DV-Institute
                                        # trade plan board, between the POI and the entry step). Off = every zone of poi_timeframes
    one_trade_per_visit: bool = False   # a zone traded during a visit is not traded again in that visit: the stop sat on its P, so a stop-out means
                                        # the P was traded through (R6: 46 re-entries after a stop-out on the same zone, 9 % won, -23.7R; first
                                        # attempts 43 %). Off here so the frozen profiles reproduce; on in config/dorus_course.yaml
    entry_outside_zone: bool = False    # the shift is the move away from the zone, so at its close price is often just outside it: with True a zone
                                        # whose visit is still open (no close 1.5 zone heights beyond it) stays a candidate after price left it
                                        # ("als we in een POI zitten, we hebben de juiste shift, dan ga ik", A 01:18:44; his EURUSD short of
                                        # 11 Nov 2025 at the 1H zone's edge, his gold shorts below the 1H zone); False = price must be inside
    # Rule: Monthly POI -> min. 4H, Weekly -> 1H, Daily -> 15m, 4H -> 5m, 1H -> 1m
    confirmation_tf_mode: str = "at_least"   # at_least: the table's timeframe and anything between it and the zone's timeframe, smallest first
                                             # (the course shows a 1H shift for a daily zone, A 01:04:24); exact: the table's timeframe only
                                             # (Max, 2 October: "voor 4H is het 5 min"); a missing timeframe is then a visible rejection
    min_confirmation_tf: Dict[Timeframe, Timeframe] = field(default_factory=lambda: {
        Timeframe.MN_1: Timeframe.H_4,
        Timeframe.W_1: Timeframe.H_1,
        Timeframe.D_1: Timeframe.MIN_15,
        Timeframe.H_4: Timeframe.MIN_5,
        Timeframe.H_1: Timeframe.MIN_1,
    })
    scalp_poi_timeframes: Tuple[Timeframe, ...] = (Timeframe.H_4, Timeframe.H_1)  # ASSUMPTION: "scalp only" = intraday POIs
    poi_timeframes: Tuple[Timeframe, ...] = (Timeframe.MN_1, Timeframe.W_1, Timeframe.D_1, Timeframe.H_4, Timeframe.H_1)
                                        # the zone timeframes traded in full mode (scalp mode keeps scalp_poi_timeframes); the demo profile
                                        # leaves the weekly and monthly out: with the sweep-extreme stop and the previous-extreme target a
                                        # weekly zone gave a 375-pip stop, a 765-pip target and a trade that sat open from June 2025 to the
                                        # end of the data, blocking every other entry (reading F over 2023-2026, 2 October)


@dataclass
class RiskParams:
    risk_pct: float = 1.0               # rule: 1 % risk per trade (K1 06:30)
    min_rr: float = 3.0                 # Max's rule. Dorus's accepted examples run 0.7R-1.7R (A/B/C) - decide, see STRATEGY.md
    spread_buffer_pips: float = 1.0     # Max's rule (not found in Dorus's material, Q7)
    sl_offset_pips: float = 1.0         # ASSUMPTION: 1 pip beyond the protection level
    tp_policy: str = "liquidity"        # "Dus ik zet ten alle tijden mijn take profit op liquiditeit" (A 01:50:40): nearest liquidity on the POI timeframe or higher;
                                        # liquidity_nearest: nearest liquidity on any timeframe above the confirmation timeframe (dorus_pure.yaml); legacy: nearest | liquidity_first | balance_first
    tp_floor_tf: Optional[Timeframe] = None   # with liquidity_nearest: only liquidity on this timeframe or higher counts ("we willen echt de highs en de lows", not local liquidity, A 01:54:49)
    tp_lookback_candles: int = 72       # tp_policy previous_extreme: the target is the lowest low (short) / highest high (long) of this many candles on
                                        # the zone's timeframe before the touch, i.e. the previous significant low/high of the move ("take profit bij het
                                        # vorige liquiditeitsgebied", A 01:54:47; his targets: the 12:45 low on 11 Nov 2025, the 15 Mar low on 18 Mar 2024,
                                        # the 24 Aug low on K3, all within 72 candles of a 1H zone); falls back to liquidity_nearest when nothing lies beyond entry
    tp_buffer_pips: float = 0.0         # previous_extreme: the target sits this many pips before the extreme (his: 0.3 pip and 1.0 point before the low)
    tp_fixed_rr: float = 0.0            # 0 = off; else the target sits this many R beyond the entry (R = the sizing distance) whatever the policy finds
                                        # tp_policy pullback_origin: the extreme from the zone's P candle to the touch, the high (long) / low (short)
                                        # the move back into the zone started from (Max, 7 October: "de vorige high die iets triggerde")
    tp_origin_candles: int = 30         # tp_policy impulse_origin: the target is the extreme of this many zone-timeframe candles before the zone formed,
                                        # i.e. the low (short) / high (long) the move that created the zone started from: "stop loss op de low en take profit
                                        # bij de vorige high" (A 00:43:39, 01:09:01, 01:20:52, 02:45:57), the previous higher low whose break is the
                                        # break of market structure (A 00:14:48); his three intraday targets sit 1.0-7 pips from that low
    min_stop_pips: float = 0.0          # 0 = off; else a stop nearer than this is moved out to this distance ("kan je je stoploss nog wat ruimte geven",
                                        # A 00:31:22). His stops: 9.7 and 10 pips on EURUSD, 10.1 and 15.0 points on gold, never under 9; stops under
                                        # 5 pips won 3 % in R6 and were hit in the same candle twice in September 2026 with the sweep-extreme stop
    stop_basis: str = "protector"       # "SL ALTIJD op minimale 1H P" (K1 06:30); legacy: confirmation (LTF invalidation swing)
    stop_protection: str = "recent_1h"  # which P the stop sits behind for zones above the 1H: recent_1h = the most recent unviolated 1H balance level
                                        # since the touch (the minimum the plan allows); poi = the zone's own P, his choice in the course
                                        # (daily P for a daily zone: A 01:08:49-01:09:03, 01:46:40-01:47:02; "op de protected", A 02:27:15)
    rr_includes_buffer: bool = True     # ASSUMPTION: R:R measured on the same distance used for sizing
    drawdown_steps: Tuple[Tuple[float, float], ...] = ()   # (level %, risk %) pairs: with the balance at or below level % from the
                                        # initial balance (account_size) a trade risks at most that risk %, e.g. ((-3, 1.0), (-6, 0.5));
                                        # empty = risk_pct always. Only the stake changes, never which trades are taken
    max_entry_depth: float = 0.0        # 0 = off; else the entry may lie at most this fraction of the zone's height inside it, measured from the
                                        # edge price enters by (an entry outside the zone counts as 0): deeper, the P is a few pips away and the stop
                                        # has no room ("kan je stoploss nog wat ruimte geven", A 00:31:22; his entries sit at the zone's edge,
                                        # docs/dossiers/SOURCE_TRADES.md). R6: entries deeper than half the zone 48 trades, 12 % won
    max_entry_outside: float = 0.0      # 0 = off; else with entry_outside_zone the shift's close may lie at most this fraction of the zone's height
                                        # outside it (beyond the edge price left by). His entries sit 1.5-1.6 pips from the zone's edge (suite
                                        # readings C, D); the live replay of Aug-Sep 2026 entered 39 pips under a 61-pip 4H zone (14 Sep) and
                                        # 11 pips above a 29-pip 1H zone (3 Aug): docs/practice/2026-09/EURUSD/v3/README.md
    max_entry_outside_pips: float = 0.0 # 0 = off; else the same cap in pips, whichever of the two is hit first
    max_spread_stop_fraction: float = 0.0   # live only, 0 = off; else no entry while the broker's spread is wider than this fraction of the
                                        # stop distance (a market opening, a news spike): normal spreads are 3-8 % of the live profiles'
                                        # stops (2024-2026 ledgers), so 0.3 refuses only abnormal ones; the backtests do not use it
    min_stop_zone_fraction: float = 0.0 # 0 = off; else the stop lies at least this fraction of the zone's height from the entry (a sweep-extreme
                                        # stop closer than that is widened). Loss anatomy, 4 October: on EURUSD 2023-2026 the third of the trades
                                        # with the tightest stop against the zone (0.31 of its height) won 38 % for -1.0R, the widest third (0.9)
                                        # 64 % for +12.7R; "SL altijd op minimale 1H P" (K1 06:30) is the course's version of the same idea
    tp_max_rr: float = 0.0              # 0 = off; else when the nearest liquidity on tp_floor_tf or higher lies beyond this R:R, the nearest liquidity
                                        # on any timeframe above the confirmation timeframe that still gives min_rr is taken instead ("mijn keuze gaat
                                        # eerder naar één of twee risk reward ... zolang het risk-reward-wijs aantrekkelijk blijft", A 01:28:01-01:28:23;
                                        # the previous 1H high as the target, H 09:14). When no nearer liquidity fits, the far target stays
    tp_cap_choice: str = "nearest"      # with tp_max_rr: nearest = the nearest liquidity that gives min_rr; farthest = the farthest liquidity
                                        # that stays within tp_max_rr ("het volledige scenario uit te spelen, van het ene stuk naar het andere", A 01:50:31)
    tp_fallback: str = ""               # "" = off: a setup whose target gives less than min_rr (or that has no target) is refused; "liquidity" = the
                                        # nearest resting liquidity on any timeframe above the confirmation timeframe that gives min_rr (at most
                                        # tp_fallback_rr when that is > 0) is the target instead, the next piece of liquidity ("van het ene stuk naar
                                        # het andere", A 01:50:31); "fixed" = the target sits tp_fallback_rr R beyond the entry. Setups whose own
                                        # target gives min_rr do not change
    tp_fallback_rr: float = 0.0
    zone_risk_multiplier: Dict[str, float] = field(default_factory=dict)   # e.g. {"4H": 2.0}: a zone of that timeframe risks
                                        # that multiple of risk_pct (after the drawdown steps). 6 October: 4H zones on EURUSD, gold
                                        # and NAS100 won 47 % / 64 % at +0.49R / +1.04R a trade (2017-2023 / 2024-2026)
    combo_risk_multiplier: Dict[str, float] = field(default_factory=dict)   # e.g. {"1D+1H": 0.75}: a trade the bias allowed
                                        # through that combination (the matched timeframes joined by +) risks that multiple as well
    stake_multiplier: float = 1.0       # the profile's stake as a multiple of risk_pct (BTC 0.5 on the FTMO 1-step: setup B)
    target_pct: float = 0.0             # the challenge phase's profit target in % of the initial balance (FTMO 2-Step: 10, then 5 in
                                        # the verification); 0 = none known. With target_protect_pct: within that many % of the target
    target_protect_pct: float = 0.0     # every trade risks at most half of risk_pct (multipliers on top), so a losing run near the
                                        # target does not undo the phase. 6 October, 2-Step at 1.25 %, starts Feb 2024 - Sep 2025:
                                        # 4 % -> funded within a year 74 % against 63 %, 2018-2022 starts 22 % against 20 %; slower
                                        # (median 159 against 126 days). 0 = off
    limit_entry_fraction: float = 0.0   # 0 = a market entry at the signal; else a limit order rests this fraction of the way from the
                                        # signal's price back toward the stop, valid limit_entry_minutes, cancelled when the target
                                        # trades first; the size follows the smaller stop and the order holds its slot and its risk in
                                        # the guard while it rests (6 October: 25 % for 4 hours added R on NAS100 in 2017-2023 and
                                        # 2024-2026; the backtest and the live runner, paper and MT5)
    limit_entry_minutes: int = 240


@dataclass
class ExitParams:
    breakeven_r_swing: float = 2.0      # rule: swing (M, W POI) -> break-even after 2R
    breakeven_r_intraday: float = 4.0   # rule: intraday/scalp (D, 4H, 1H POI) -> break-even after 4R
    partials: bool = False              # rule: no partials
    breakeven_offset_pips: float = 0.0  # 0 = exact entry
    max_hold_hours: float = 0.0         # 0 = off; else a trade still open this many hours after its fill is closed at the market


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
    max_open_per_symbol: int = 1        # open trades in one market (the backtests ran one market at a time with one trade open)
    daily_loss_limit_pct: float = 4.0   # stay inside the typical 5 % rule with margin
    monthly_loss_limit_pct: float = 0.0 # 0 = off; else no new trade once the month's closed loss reaches this much of the account
    max_drawdown_pct: float = 8.0       # stay inside the typical 10 % rule with margin
    drawdown_basis: str = "peak"        # peak: from the highest equity seen (stricter); initial: static floor below the starting balance
                                        # (FTMO 2-step); day_high: from the highest balance at a day's start (FTMO 1-step, trailing)
    day_timezone: str = "Europe/Prague" # the day for the daily-loss rule starts at midnight here (FTMO: CE(S)T)
    record_daily_loss_pct: float = 5.0  # the published limits the first breach is recorded against (FTMO 2-step: 5 % daily,
    record_max_loss_pct: float = 10.0   # 10 % static below the initial balance), whatever the halting limits above are set to
    news_blackout_minutes: int = 0      # optional: block entries N minutes around high-impact news
    min_minutes_between_trades: int = 0
    max_margin_pct: float = 45.0        # live: one position ties up at most this much of equity as margin (and 90 % of the
                                        # free margin), lots cut to fit: two still fit, and a 1:2 crypto CFD is not refused; 0 = off
    weekend_close: str = ""             # "" = off; "16:45": every position closed at Friday 16:45 New York and no new one until
                                        # the Sunday 17:00 open (FTMO Account, Standard type: flat before the weekend)


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
    filling: str = "ORDER_FILLING_IOC"            # the first try when the symbol allows it; on retcode 10030 (unsupported filling mode)
                                                  # the deal goes out again with the symbol's other modes (MT5Broker.filling_modes)


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
    summary_time: Optional[str] = "22:00"    # the day's closed trades, R, P&L and equity per market at this local time (weekdays)
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
    symbols: Dict[str, SymbolSpec] = field(default_factory=lambda: {k: replace(v) for k, v in DEFAULT_SYMBOLS.items()})   # own copies: a
                                        # live run sets its symbol's contract from the broker (MT5Broker.align_spec)
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
        if path:
            if not Path(path).exists():     # a typo or a renamed profile must stop the start, not trade the built-in defaults
                raise FileNotFoundError(f"config file not found: {path}")
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
