"""What would have to close where for the bias to allow a trade (15 October, Max: "maar ondertussen zegt die geen
trade": the morning check said "geen short" and not what it waits for).

For the messages only: nothing here feeds a decision. The engine's own code is asked. The candle that is forming on a
timeframe is closed at a trial price (its open, high and low so far are kept, so a wick it already made still counts),
that timeframe is read again with ``timeframe_bias``, and ``combine_biases`` says whether the decision would then allow
a trade in that direction. The nearest such close, searched up to ``max_atr`` average candles away, is the answer. A
second trial lets the candle first take the nearest resting liquidity on the other side (a wick through it, the sweep
Dorus waits for) before it closes: a sweep turns the liquidity view, so the close that turns the timeframe can then be
much nearer. Reading it by eye goes wrong: the morning review of 15 October put gold's turn at a 1H close under 4,128,
where the engine needs either a close under the CPI low 4,073 or a sweep of 4,160 first.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple, Union

import pandas as pd

from ..core.candles import COLUMNS, CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import Bias, BiasDecision
from .bias import combine_biases, timeframe_bias
from .structure import analyze_structure

# the closes that can come first: the hour, the four hours, both at once, the day, all three
SCENARIOS: Tuple[Tuple[Timeframe, ...], ...] = (
    (Timeframe.H_1,), (Timeframe.H_4,), (Timeframe.H_1, Timeframe.H_4), (Timeframe.D_1,),
    (Timeframe.H_1, Timeframe.H_4, Timeframe.D_1),
)


@dataclass(frozen=True)
class Turn:
    """Closes of ``timeframes`` at ``close`` (or beyond it) turn the decision into a trade in ``direction``; with
    ``sweep`` the candle first takes the resting liquidity at that price on the other side."""

    timeframes: Tuple[Timeframe, ...]
    direction: Bias
    close: float
    distance_atr: float          # from the current price, in average candles (ATR14) of the largest timeframe
    decision: BiasDecision
    sweep: Optional[float] = None


def _atr(series: CandleSeries, n: int = 14) -> float:
    df = series.df.tail(n + 1)
    if len(df) < 2:
        return 0.0
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return float(tr.iloc[1:].mean())


class _Trial:
    """One timeframe's closed candles and its forming candle, read again with the forming candle closed at a price."""

    def __init__(self, raw: CandleSeries, now: pd.Timestamp, settings):
        self.settings = settings
        self.tf = raw.timeframe
        closed = raw.closed_as_of(now)
        self.closed = closed
        self.base = closed.df
        self.lookback = settings.structure.lookback_by_timeframe.get(self.tf, settings.structure.lookback)
        forming = raw.df[raw.df["timestamp"] > closed.last_timestamp]
        if len(forming):
            row = forming.iloc[0]
            self.stamp, self.open = pd.Timestamp(row["timestamp"]), float(row["open"])
            self.high, self.low = float(row["high"]), float(row["low"])
        else:
            self.stamp = pd.Timestamp(closed.last_timestamp) + self.tf.delta()
            self.open = self.high = self.low = float(closed.last.close)
        self.atr = _atr(closed)
        self.structure = analyze_structure(closed.tail(self.lookback), settings.structure)
        self._cache: Dict[Tuple[float, float, float], Bias] = {}

    def resting(self, direction: Bias, price: float) -> Optional[float]:
        """The nearest resting liquidity a move in ``direction`` would first sweep on the other side: the buy-side above
        before a short, the sell-side below before a long."""
        levels = self.structure.resting_liquidity_above(price) if direction is Bias.BEARISH \
            else self.structure.resting_liquidity_below(price)
        return float(levels[0].price) if levels else None

    def bias_at(self, close: float, high: Optional[float] = None, low: Optional[float] = None) -> Bias:
        high = max(self.high, close, high if high is not None else close)
        low = min(self.low, close, low if low is not None else close)
        key = (round(float(close), 10), round(high, 10), round(low, 10))
        if key not in self._cache:
            row = pd.DataFrame([[self.stamp, self.open, high, low, close, 0.0]], columns=COLUMNS)
            frame = pd.concat([self.base, row], ignore_index=True)
            series = CandleSeries(frame, self.tf, self.closed.symbol, validate=False).tail(self.lookback)
            self._cache[key] = timeframe_bias(analyze_structure(series, self.settings.structure), self.settings.bias).bias
        return self._cache[key]


def turning_closes(raw: Dict[Timeframe, CandleSeries], biases: Dict[Timeframe, Bias], settings, now: pd.Timestamp,
                   price: float, max_atr: float = 3.0, step_atr: float = 0.25, refine: int = 6, budget_s: float = 20.0,
                   scenarios: Iterable[Tuple[Timeframe, ...]] = SCENARIOS,
                   directions: Iterable[Bias] = (Bias.BEARISH, Bias.BULLISH),
                   full: Iterable[Bias] = (Bias.BEARISH, Bias.BULLISH)) -> Dict[Bias, Union[Turn, BiasDecision]]:
    """Per direction the nearest close that turns the decision into a trade (an intraday turn, the hour or the four
    hours, before one that needs the day's close; then the nearest close; then the fewest timeframes), or, when none
    within ``max_atr`` does, the decision at the farthest close tried (what still blocks it, e.g. a weekly veto).
    ``raw`` are the feed's candles (the forming candle included), ``biases`` the readings the decision was made from.
    A direction not in ``full`` is tried on the intraday closes only and left out when none turns it (the side the
    higher timeframes lean against is worth a line only when it is near). The sweep trial runs on the intraday closes
    only: a day that sweeps one side and closes beyond the other is no level to watch. Stops after ``budget_s``
    seconds with what it has: a briefing must never hold the loop up."""
    b = settings.bias
    t0 = time.monotonic()
    mirrored = set(b.mirror_timeframes) if getattr(b, "mirror_symbol", None) else set()
    scenarios = tuple(scenarios)
    trials: Dict[Timeframe, _Trial] = {}
    for tf in sorted({tf for scen in scenarios for tf in scen}):
        if tf in raw and tf not in mirrored and len(raw[tf].closed_as_of(now)) >= 10:
            trials[tf] = _Trial(raw[tf], now, settings)
    out: Dict[Bias, Union[Turn, BiasDecision]] = {}
    full = set(full)
    for direction in directions:
        sign = -1.0 if direction is Bias.BEARISH else 1.0
        found = []
        blocked: Optional[BiasDecision] = None
        named: Optional[BiasDecision] = None      # a refusal that names this side (a veto, a missing timeframe) beats a count
        for scen in scenarios:
            daily = Timeframe.D_1 in scen
            if not all(tf in trials for tf in scen) or (daily and direction not in full):
                continue
            unit = trials[max(scen)].atr
            if unit <= 0:
                continue
            sweeps = [] if daily else [trials[tf].resting(direction, price) for tf in scen]
            sweeps = [x for x in sweeps if x is not None and abs(x - price) <= max_atr * unit]
            variants = [None] + ([max(sweeps) if direction is Bias.BEARISH else min(sweeps)] if sweeps else [])
            for sweep in variants:
                if time.monotonic() - t0 > budget_s:
                    break
                wick = None if sweep is None else sweep + sign * -1e-6 * max(abs(sweep), 1.0)

                def decide(x: float) -> BiasDecision:
                    close = price + sign * x * unit
                    votes = dict(biases)
                    for tf in scen:
                        if direction is Bias.BEARISH:
                            votes[tf] = trials[tf].bias_at(close, high=wick)
                        else:
                            votes[tf] = trials[tf].bias_at(close, low=wick)
                    return combine_biases(votes, b)

                def allows(d: BiasDecision) -> bool:
                    return d.tradable and d.direction is direction

                prev, hit, last = None, None, None
                for k in range(0, int(round(max_atr / step_atr)) + 1):
                    last = decide(k * step_atr)
                    if allows(last):
                        hit = (k * step_atr, last)
                        break
                    if last.reason.startswith(f"{direction}:"):
                        named = last
                    prev = k * step_atr
                if hit is None:
                    if sweep is None and last is not None:
                        blocked = last                    # the scenarios run small to large: the last one holds most
                    continue
                x, d = hit
                if prev is not None:                      # the turn lies between the last step that did not and this one
                    lo, hi = prev, x
                    for _ in range(refine):
                        mid = (lo + hi) / 2
                        dm = decide(mid)
                        if allows(dm):
                            hi, d = mid, dm
                        else:
                            lo = mid
                    x = hi
                found.append(Turn(tuple(scen), direction, price + sign * x * unit, x, d, sweep))
        if found:
            found.sort(key=lambda t: (Timeframe.D_1 in t.timeframes, abs(t.close - price), len(t.timeframes), t.sweep is not None))
            out[direction] = found[0]
        elif (named or blocked) is not None and direction in full:
            out[direction] = named or blocked
    return out


TF_WORDS = {Timeframe.H_1: "1H", Timeframe.H_4: "4H", Timeframe.D_1: "dag"}


def turn_text(turn: Turn, price_text, zone_text: Optional[str] = None) -> str:
    """'de 1H veegt 4,160.10 weg en sluit onder 4,111.20 → short uit de 4H supply 4,105.23–4,155.33 (prijs erin)'
    (``price_text`` formats a price the way the message does)."""
    names = [TF_WORDS.get(tf, tf.label) for tf in turn.timeframes]
    who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " en " + names[-1]
    plural = len(names) > 1
    way = "onder" if turn.direction is Bias.BEARISH else "boven"
    side = "short" if turn.direction is Bias.BEARISH else "long"
    if getattr(turn.decision.mode, "value", "") == "scalp":
        side += " (scalp)"
    kind = "supply" if turn.direction is Bias.BEARISH else "demand"
    where = f"uit de {zone_text}" if zone_text else f"maar eerst een verse {kind}-zone"
    if turn.sweep is not None:
        first = f"de {who} {'vegen' if plural else 'veegt'} {price_text(turn.sweep)} weg en {'sluiten' if plural else 'sluit'}"
    else:
        first = f"de {who} {'sluiten' if plural else 'sluit'}"
    return f"{first} {way} {price_text(turn.close)} → {side} {where}"
