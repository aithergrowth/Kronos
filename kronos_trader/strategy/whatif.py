"""What the next close would have to be for the bias to allow a trade (15 October, Max: "maar ondertussen zegt die geen
trade": the morning check said "geen short" and not what it waits for).

For the messages only: nothing here feeds a decision. The engine's own code is asked. The candle forming on the hour
(and on the four hours and the day when they close with it) is closed at a trial price (its open, high and low so far
are kept, so a wick it already made still counts), those timeframes are read again with ``timeframe_bias``, and
``combine_biases`` says whether the decision would then allow a trade in that direction. The answer is the band of
such closes nearest to the price, searched up to ``max_atr`` average candles away: where it starts and, when a close
farther out no longer turns it (a close beyond a gap's P reads 50/50 on BTC), where it ends. A second trial lets the
candle first take the nearest resting liquidity on the other side (a wick through it, the sweep Dorus waits for)
before it closes. Only the next close is asked: a later 4H or day close depends on the hours in between, which no
trial knows (15 October fix check). Reading it by eye goes wrong: the morning review of 15 October put gold's turn at
a 1H close under 4,128, where the engine needed a sweep of 4,160 first.
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

@dataclass(frozen=True)
class Turn:
    """Closes of ``timeframes`` at ``close`` (or beyond it) turn the decision into a trade in ``direction``; with
    ``sweep`` the candle first takes the resting liquidity at that price on the other side."""

    timeframes: Tuple[Timeframe, ...]
    direction: Bias
    close: float                 # the nearest close that turns it
    distance_atr: float          # from the current price, in average candles (ATR14) of the largest timeframe
    decision: BiasDecision
    sweep: Optional[float] = None
    until: Optional[float] = None          # a close beyond this no longer turns it (None: none within the search)
    at: Optional[pd.Timestamp] = None      # when that close comes (UTC)


class WhatIf(dict):
    """``turning_closes``' answer: per direction a ``Turn``, or the decision at the farthest close tried. ``complete`` is
    False when the time budget cut the search or nothing could be tried (then nothing may be said about what is not
    in it); ``at`` is the close it is about (UTC)."""

    complete: bool = False
    at: Optional[pd.Timestamp] = None


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


def _closes_at(raw: Dict[Timeframe, CandleSeries], trials: Dict[Timeframe, "_Trial"], biases, now: pd.Timestamp):
    """The next hour's close and the tried timeframes that close with it (the hour; the four hours and the day when it
    is their last hour), or ``(None, ())`` when that moment changes a vote that is not tried (the week or the month
    closing then too) or the hour cannot be tried."""
    if Timeframe.H_1 not in trials:
        return None, ()
    at = trials[Timeframe.H_1].stamp + Timeframe.H_1.delta()
    for tf, series in raw.items():
        if tf in biases and tf not in trials and len(series.closed_as_of(at)) > len(series.closed_as_of(now)):
            return None, ()
    return at, tuple(sorted(tf for tf, trial in trials.items() if trial.stamp + tf.delta() == at))


def turning_closes(raw: Dict[Timeframe, CandleSeries], biases: Dict[Timeframe, Bias], settings, now: pd.Timestamp,
                   price: float, max_atr: float = 3.0, step_atr: float = 0.25, fine_atr: float = 0.1, refine: int = 6,
                   budget_s: float = 20.0, scenarios: Optional[Iterable[Tuple[Timeframe, ...]]] = None,
                   directions: Iterable[Bias] = (Bias.BEARISH, Bias.BULLISH), full=None) -> "WhatIf":
    """Per direction the band of closes of the next hour (with the four hours and the day when they close with it)
    that turns the decision into a trade: its nearest edge (``Turn.close``) and, when a close farther out no longer
    turns it, its far edge (``Turn.until``); or, when no close within ``max_atr`` average candles turns it, the
    decision at the farthest close tried. Only that close is exact: every other vote stays as it is until then (15
    October fix check: a later 4H or day close was tried with the hours in between frozen, and the engine refused
    such levels when they came). ``raw`` are the feed's candles (the forming candle included), ``biases`` the readings
    the decision was made from. A second trial lets the candle first take the nearest resting liquidity on the other
    side. Stops after ``budget_s`` seconds; ``WhatIf.complete`` then says the answer is partial. ``scenarios`` replaces
    the next close (tests); ``full`` is accepted and not used."""
    b = settings.bias
    t0 = time.monotonic()
    out = WhatIf()
    mirrored = set(b.mirror_timeframes) if getattr(b, "mirror_symbol", None) else set()
    trials: Dict[Timeframe, _Trial] = {}
    wanted = {Timeframe.H_1, Timeframe.H_4, Timeframe.D_1} if scenarios is None else {tf for s in scenarios for tf in s}
    for tf in sorted(wanted):
        if tf in raw and tf not in mirrored and len(raw[tf].closed_as_of(now)) >= 10:
            trials[tf] = _Trial(raw[tf], now, settings)
    if scenarios is None:
        out.at, scen = _closes_at(raw, trials, biases, pd.Timestamp(now))
        scenarios = (scen,) if scen else ()
    scenarios = tuple(scenarios)
    cut, evaluated = False, False
    for direction in directions:
        sign = -1.0 if direction is Bias.BEARISH else 1.0
        found = []
        blocked: Optional[BiasDecision] = None
        named: Optional[BiasDecision] = None      # a refusal that names this side (a veto, a missing timeframe) beats a count
        for scen in scenarios:
            if not scen or not all(tf in trials for tf in scen):
                continue
            unit = trials[max(scen)].atr
            if unit <= 0:
                continue
            sweeps = [trials[tf].resting(direction, price) for tf in scen]
            sweeps = [x for x in sweeps if x is not None and abs(x - price) <= max_atr * unit]
            variants = [None] + ([max(sweeps) if direction is Bias.BEARISH else min(sweeps)] if sweeps else [])
            for sweep in variants:
                if time.monotonic() - t0 > budget_s:
                    cut = True
                    break
                evaluated = True
                wick = None if sweep is None else sweep + sign * -1e-6 * max(abs(sweep), 1.0)

                def decide(x: float, scen=scen, wick=wick, unit=unit, sign=sign) -> BiasDecision:
                    close = price + sign * x * unit
                    votes = dict(biases)
                    for tf in scen:
                        votes[tf] = (trials[tf].bias_at(close, high=wick) if sign < 0 else trials[tf].bias_at(close, low=wick))
                    return combine_biases(votes, b)

                def allows(d: BiasDecision, direction=direction) -> bool:
                    return d.tradable and d.direction is direction

                def edge(ok: float, no: float) -> float:
                    """The turning close nearest to ``no`` between ``ok`` (turns) and ``no`` (does not)."""
                    for _ in range(refine):
                        mid = (ok + no) / 2
                        if allows(decide(mid)):
                            ok = mid
                        else:
                            no = mid
                    return ok

                def walk(start: float, step: float) -> Optional[float]:
                    """From ``start`` (turns) outward by ``step`` until a close no longer turns: the last one that does;
                    None when every close up to ``max_atr`` turns."""
                    x = start
                    while abs(x + step) <= max_atr + 1e-9:
                        if not allows(decide(x + step)):
                            return edge(x, x + step)
                        x += step
                    return None

                prev, hit, last = None, None, None
                for k in range(0, int(round(max_atr / step_atr)) + 1):
                    last = decide(k * step_atr)
                    if allows(last):
                        hit = k * step_atr
                        break
                    if last.reason.startswith(f"{direction}:"):
                        named = last
                    prev = k * step_atr
                if hit is None:
                    if sweep is None and last is not None:
                        blocked = last
                    continue
                if prev is None:                      # closing at the price already turns it: where does the band start?
                    near = walk(0.0, -fine_atr)
                    near = -max_atr if near is None else near
                else:
                    near = edge(hit, prev)
                far = walk(max(near, hit), fine_atr)
                found.append(Turn(tuple(scen), direction, price + sign * near * unit, near, decide(near), sweep,
                                  None if far is None else price + sign * far * unit, out.at))
        if found:
            found.sort(key=lambda t: (Timeframe.D_1 in t.timeframes, abs(t.close - price), len(t.timeframes), t.sweep is not None))
            out[direction] = found[0]
        elif (named or blocked) is not None:
            out[direction] = named or blocked
    out.complete = evaluated and not cut
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
    level = f"{way} {price_text(turn.close)}" if turn.until is None else \
        f"tussen {price_text(turn.close)} en {price_text(turn.until)}"     # beyond the band the bias reads 50/50 again
    return f"{first} {level} → {side} {where}"
