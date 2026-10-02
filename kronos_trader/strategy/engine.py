"""The strategy engine: candles in, a fully reasoned trade decision out.

Order of operations (mirrors how the rules are written):

1. Bias per timeframe (liquidity + balance) on 1M, 1W, 1D, 4H, 1H.
2. Combine: 3/5 rule and the valid-combination table -> full / scalp / none.
3. Map POIs on all five timeframes, both sides.
4. For POIs in the bias direction that price is visiting *now*: look for a
   confirmation on an allowed lower timeframe (BOS/BMS body close).
5. Build the setup: SL behind the invalidation swing, TP at opposite
   liquidity / next unmitigated balance block, R:R >= 1:3, 1 % risk sizing.
6. Kronos forecast as an extra indicator (advisory or hard filter).

The engine is stateless apart from a structure cache; whether a trade may be
opened (one trade per account, prop-firm limits) is the risk guard's job.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from ..config import Settings
from ..core.candles import CandleSeries
from ..core.timeframe import BIAS_TIMEFRAMES, POI_TIMEFRAMES, Timeframe
from ..core.types import (
    Analysis,
    Bias,
    Direction,
    ForecastSummary,
    POI,
    POIStatus,
    Signal,
    SignalStatus,
    TradeMode,
)
from ..config import SessionParams
from .bias import combine_biases, timeframe_bias
from .confirmation import allowed_confirmation_timeframes, find_confirmation
from .exits import breakeven_trigger_r
from .poi import current_visit, map_pois, update_poi_status, VisitTracker
from .risk import build_setup
from .structure import StructureAnalysis, analyze_structure


def _candle_open(series: CandleSeries, index: int) -> Optional[pd.Timestamp]:
    """Open time of the candle at ``index`` of ``series`` (None when the index is not in the view)."""
    try:
        return pd.Timestamp(series.ts_list[index])
    except Exception:
        return None


def confirmation_age(max_age: int, step_minutes: Optional[int], tf: Timeframe) -> int:
    """How many closed candles back a confirmation on ``tf`` may lie: ``max_age``, or for a timeframe finer than the
    caller's step the candles that closed inside the last step (a 1m shift two minutes before a 5m step is still new)."""
    if step_minutes is None or tf.minutes >= step_minutes:
        return max_age
    return max(max_age, step_minutes // tf.minutes - 1)


def _diagnostic_zone_notes(pois: List[POI], side: Bias, allowed: Tuple[Timeframe, ...], price: float) -> List[str]:
    """The same-side zones that were not candidates (tested, fresh, invalidated) and where price sits relative to them."""
    others = [p for p in pois if p.direction is side and p.timeframe in allowed and p.status is not POIStatus.ACTIVE]
    notes = []
    for p in sorted(others, key=lambda p: (p.timeframe, p.created_at), reverse=True)[:8]:
        where = "below" if price < p.low else "above" if price > p.high else "inside"
        notes.append(f"diagnostic: {p.describe()} is {p.status.name.lower()}, price {where} it")
    return notes


def in_session(now: pd.Timestamp, params: SessionParams) -> Tuple[bool, str]:
    """Is ``now`` (naive UTC) inside one of the entry windows?  Returns ``(inside, local time label)``."""
    ts = pd.Timestamp(now)
    local = (ts.tz_localize("UTC") if ts.tzinfo is None else ts).tz_convert(params.timezone)
    label = local.strftime("%a %H:%M")
    if local.weekday() not in params.weekdays:
        return False, label
    minutes = local.hour * 60 + local.minute
    for start, end in params.windows:
        h1, m1 = (int(x) for x in start.split(":"))
        h2, m2 = (int(x) for x in end.split(":"))
        if h1 * 60 + m1 <= minutes < h2 * 60 + m2:
            return True, label
    return False, label


class LazyStructures(dict):
    """Structure analysis per timeframe, computed on first use.

    The bias and the zones need the monthly to hourly structures every step; the 15m and 5m structures
    are only needed when a zone is actually looking for a confirmation, which is a small share of steps.
    ``items()``/``keys()``/``values()`` compute every timeframe (the target search wants them all).
    """

    def __init__(self, engine: "StrategyEngine", symbol: str, views: Dict[Timeframe, CandleSeries]):
        super().__init__()
        self._engine, self._symbol, self._views = engine, symbol, views

    def __missing__(self, tf: Timeframe) -> StructureAnalysis:
        st = self._engine.structure_for(self._symbol, self._views[tf])
        self[tf] = st
        return st

    def __contains__(self, tf) -> bool:
        return tf in self._views

    def get(self, tf, default=None):
        return self[tf] if tf in self._views else default

    def _all(self) -> None:
        for tf in self._views:
            self[tf]

    # iteration follows the order of the views (the order the data was loaded in), exactly as the eager dict did,
    # so a tie between two levels at the same price resolves to the same timeframe as before
    def items(self):
        self._all()
        return [(tf, self[tf]) for tf in self._views]

    def keys(self):
        self._all()
        return list(self._views)

    def values(self):
        self._all()
        return [self[tf] for tf in self._views]

    def __iter__(self):
        self._all()
        return iter(list(self._views))


class StrategyEngine:
    def __init__(self, settings: Optional[Settings] = None, forecaster=None, calendar=None):
        self.settings = settings or Settings()
        self.forecaster = forecaster
        self.calendar = calendar            # NewsCalendar: no new entries around high-impact news (G 11:08)
        self._structure_cache: Dict[Tuple[str, Timeframe], Tuple[pd.Timestamp, int, StructureAnalysis]] = {}
        self.visits: Dict[str, VisitTracker] = {}      # per symbol: visit history per zone beyond the analysis window
        self.traded: Dict[str, Dict[Tuple[str, int, str], int]] = {}   # per symbol: zone key -> visit number a trade was opened on
        self._poi_cache: Dict[Tuple[str, Timeframe], Tuple[pd.Timestamp, int, List[POI]]] = {}

    # ------------------------------------------------------------------ helpers
    def structure_for(self, symbol: str, view: CandleSeries) -> StructureAnalysis:
        key = (symbol, view.timeframe)
        if len(view) == 0:
            return analyze_structure(view, self.settings.structure)
        stamp = (view.last_timestamp, len(view))
        cached = self._structure_cache.get(key)
        if cached is not None and cached[0] == stamp[0] and cached[1] == stamp[1]:
            return cached[2]
        st = analyze_structure(view, self.settings.structure)
        self._structure_cache[key] = (stamp[0], stamp[1], st)
        return st

    def pois_for(self, symbol: str, tf: Timeframe, st: StructureAnalysis, view: CandleSeries, price: float) -> List[POI]:
        """The zones of one timeframe: mapped once per closed candle of that timeframe, status refreshed every call."""
        key = (symbol, tf)
        stamp = (view.last_timestamp, len(view))
        cached = self._poi_cache.get(key)
        if cached is not None and cached[0] == stamp[0] and cached[1] == stamp[1]:
            pois = cached[2]
            for poi in pois:
                update_poi_status(poi, st.series, price)
            return pois
        pois = map_pois(st, self.settings.structure, price)
        self._poi_cache[key] = (stamp[0], stamp[1], pois)
        return pois

    def mark_traded(self, symbol: str, poi_key: Tuple[str, int, str], visit: Optional[int]) -> None:
        """Record that a trade was opened on this zone during this visit; with ``one_trade_per_visit`` the zone
        gives no second signal in the same visit (the runner and the live loop call this after the order)."""
        if visit is not None:
            self.traded.setdefault(symbol, {})[poi_key] = int(visit)

    def _protection_level(self, poi: POI, direction: Direction, touch_ts, structures: Dict[Timeframe, StructureAnalysis]) -> float:
        """The P the stop sits behind (see :meth:`_protection`)."""
        return self._protection(poi, direction, touch_ts, structures)[0]

    def _protection(self, poi: POI, direction: Direction, touch_ts, structures: Dict[Timeframe, StructureAnalysis]) -> Tuple[float, Dict[str, object]]:
        """The P the stop sits behind, and where it comes from: the most recent 1H balance level in the
        trade direction formed since the touch and not yet violated, else the POI's own protector
        ("SL ALTIJD op minimale 1H P").  The detail names the timeframe, the P candle's open and close
        and the selection ground, so a ledger can show which P a stop belongs to."""
        h1 = structures.get(Timeframe.H_1)
        if h1 is not None and poi.timeframe > Timeframe.H_1 and self.settings.risk.stop_protection != "poi":
            start = h1.series.index_at_or_after(touch_ts)
            recent = [g for g in h1.gaps_in(direction.bias) if g.index >= start and not g.is_violated]
            if recent:
                gap = recent[-1]
                opened = _candle_open(h1.series, gap.protector_index)
                return gap.protection_level, {
                    "stop_tf": Timeframe.H_1.label, "stop_p_open": opened,
                    "stop_p_close": None if opened is None else Timeframe.H_1.close_time(opened),
                    "stop_basis": "P of the most recent 1H balance level in the trade direction formed since the touch and not violated",
                }
        own = structures.get(poi.timeframe)
        opened = _candle_open(own.series, poi.gap.protector_index) if (own is not None and poi.gap is not None) else None
        why = ("stop_protection=poi: the zone's own P, as in his course examples" if self.settings.risk.stop_protection == "poi"
               else "no 1H balance level in the trade direction formed since the touch" if poi.timeframe > Timeframe.H_1
               else f"the zone is on the {poi.timeframe.label}")
        return poi.protector_extreme, {
            "stop_tf": poi.timeframe.label, "stop_p_open": opened,
            "stop_p_close": None if opened is None else poi.timeframe.close_time(opened),
            "stop_basis": f"P of the POI itself ({why})",
        }

    def _forecast(self, view: CandleSeries, notes: List[str]) -> Optional[ForecastSummary]:
        if self.forecaster is None or self.settings.kronos.mode == "off":
            return None
        try:
            return self.forecaster.forecast(view)
        except Exception as exc:  # the indicator must never take the strategy down
            notes.append(f"kronos forecast failed on {view.timeframe.label}: {exc}")
            return None

    # ------------------------------------------------------------------ main
    def analyze(
        self,
        symbol: str,
        series_by_tf: Dict[Timeframe, CandleSeries],
        equity: Optional[float] = None,
        now: Optional[pd.Timestamp] = None,
        max_confirmation_age: int = 0,
        compute_forecasts: bool = False,
        assume_direction: Optional[Direction] = None,
        step_minutes: Optional[int] = None,
    ) -> Analysis:
        """``assume_direction`` is diagnostic only: when the bias, session or news gate refuses, the analysis
        records that refusal and walks on in the given direction through the remaining gates, so a dossier can
        show every later refusal too (is the bias really the only obstacle?).  Nothing found that way is a
        signal; a setup reached is kept as ``analysis.diagnostic_setup`` and listed under the rejections.

        ``step_minutes`` is the caller's step (a backtest walking 5-minute candles): a confirmation on a
        timeframe finer than the step may have closed up to ``step // tf - 1`` candles ago and is still
        the newest thing the caller could have acted on; coarser timeframes keep ``max_confirmation_age``."""
        s = self.settings
        spec = s.symbol(symbol)
        equity = s.account_size if equity is None else equity
        if not series_by_tf:
            raise ValueError("series_by_tf is empty")

        # closed candles only, limited to the (local) analysis lookback ---------------
        views: Dict[Timeframe, CandleSeries] = {}
        for tf, series in series_by_tf.items():
            view = series.closed_as_of(now) if now is not None else series
            view = view.tail(s.structure.lookback_by_timeframe.get(tf, s.structure.lookback))
            if len(view):
                views[tf] = view
        if not views:
            raise ValueError("no closed candles available")
        lowest_tf = min(views)
        lowest = views[lowest_tf]
        price = lowest.last.close
        if now is None:
            now = lowest.last_close_time

        structures = LazyStructures(self, symbol, views)

        # 1 + 2: bias ----------------------------------------------------------------
        biases = {tf: timeframe_bias(structures[tf], s.bias) for tf in BIAS_TIMEFRAMES if tf in views}
        decision = combine_biases({tf: b.bias for tf, b in biases.items()}, s.bias)

        # 3: POIs on every mapped timeframe, both sides --------------------------------
        pois: List[POI] = []
        for tf in POI_TIMEFRAMES:
            if tf in views:
                pois.extend(self.pois_for(symbol, tf, structures[tf], views[tf], price))

        # visits are history, not eligibility: fold this step's candles into every zone's record before any
        # bias / session / news gate can return, so a touch during a closed session still counts as a visit
        tracker = self.visits.setdefault(symbol, VisitTracker())
        for poi in pois:
            if poi.status is not POIStatus.INVALIDATED:
                tracker.observe(poi, lowest, s.confirmation.max_extension_zones)

        analysis = Analysis(symbol=symbol, timestamp=now, price=price, biases=biases, decision=decision,
                            pois=pois, signal=None)
        missing = [tf.label for tf in BIAS_TIMEFRAMES if tf not in views]
        if missing:
            analysis.rejections.append(f"bias timeframes without data: {', '.join(missing)}")

        if compute_forecasts:
            for tf in s.kronos.forecast_timeframes:
                if tf in views:
                    fc = self._forecast(views[tf], analysis.rejections)
                    if fc is not None:
                        analysis.forecasts[tf] = fc

        diagnostic = False
        if not decision.tradable:
            analysis.rejections.append(decision.reason)
            if assume_direction is None:
                return analysis
            diagnostic = True
            direction = assume_direction
            allowed_poi_tfs = tuple(POI_TIMEFRAMES)
            analysis.rejections.append(f"diagnostic: walking on as {direction.name} past the bias gate; nothing below is a signal")
        else:
            direction = Direction.from_bias(decision.direction)
            allowed_poi_tfs = tuple(POI_TIMEFRAMES) if decision.mode is TradeMode.FULL else tuple(s.confirmation.scalp_poi_timeframes)
            if assume_direction is not None and assume_direction is not direction:
                diagnostic = True
                direction = assume_direction
                allowed_poi_tfs = tuple(POI_TIMEFRAMES)
                analysis.rejections.append(f"diagnostic: the bias allows {decision.direction}, walking on as {direction.name}; nothing below is a signal")
        bias_side = direction.bias

        # session windows: no new entries outside them (A 02:30:56 rejects a 17:00 entry) ---------
        if s.session.enabled:
            inside, local_label = in_session(now, s.session)
            if not inside:
                analysis.rejections.append(f"outside the entry windows ({local_label} {s.session.timezone}); open trades run on")
                if assume_direction is None:
                    return analysis
                diagnostic = True

        # news blackout: no new entries around high-impact news of the symbol's currencies (G 11:08) ---
        if self.calendar is not None and s.news.enabled:
            event = self.calendar.blackout(symbol, now)
            if event is not None:
                analysis.rejections.append(f"news blackout: {event.title} ({event.currency}) at {event.time:%H:%M} UTC; open trades run on")
                if assume_direction is None:
                    return analysis
                diagnostic = True

        # 4: POIs being visited now, highest timeframe first ------------------------------
        # with entry_outside_zone the visit tracker (lowest timeframe) decides, not the zone's own-timeframe status: a touch inside
        # the still-open candle of the zone's timeframe leaves the status FRESH although the visit is already running
        eligible = ((POIStatus.ACTIVE, POIStatus.TESTED, POIStatus.FRESH) if s.confirmation.entry_outside_zone else (POIStatus.ACTIVE,))
        candidates = [p for p in pois
                      if p.direction is bias_side and p.timeframe in allowed_poi_tfs
                      and p.status in eligible]           # a zone price is not inside only survives the visit gate below while its visit is open
        candidates.sort(key=lambda p: p.timeframe, reverse=True)
        if not candidates:
            n_dir = sum(1 for p in pois if p.direction is bias_side and p.timeframe in allowed_poi_tfs
                        and p.status is not POIStatus.INVALIDATED)
            analysis.rejections.append(f"price is not inside a {bias_side} POI ({n_dir} valid zones mapped)")
            if diagnostic:
                analysis.rejections.extend(_diagnostic_zone_notes(pois, bias_side, allowed_poi_tfs, price))
            return analysis

        for poi in candidates:
            touch_ts, visits, invalid = tracker.observe(poi, lowest, s.confirmation.max_extension_zones)
            label = poi.describe()
            if invalid:
                analysis.rejections.append(f"{label}: invalidated on {lowest_tf.label}")
                continue
            if touch_ts is None:
                analysis.rejections.append(f"{label}: no active visit on {lowest_tf.label}")
                continue
            if visits > 1 and not s.confirmation.allow_retest:
                analysis.rejections.append(f"{label}: visit #{visits} - only the first return is traded")
                continue
            if s.confirmation.one_trade_per_visit and self.traded.get(symbol, {}).get(poi.key) == visits:
                analysis.rejections.append(f"{label}: already traded on visit #{visits} - one trade per visit")
                continue

            conf_tfs = [tf for tf in allowed_confirmation_timeframes(poi.timeframe, s.confirmation) if tf in views]
            if not conf_tfs:
                needed = [tf.label for tf in allowed_confirmation_timeframes(poi.timeframe, s.confirmation)]
                analysis.rejections.append(f"{label}: no confirmation timeframe data ({'/'.join(needed)} needed)")
                continue
            confirmation = None
            for ctf in conf_tfs:
                confirmation = find_confirmation(views[ctf], poi, touch_ts, s.confirmation, s.structure,
                                                 confirmation_age(max_confirmation_age, step_minutes, ctf), structure=structures.get(ctf))
                if confirmation is not None:
                    break
            if confirmation is None:
                analysis.rejections.append(
                    f"{label}: touched at {touch_ts}, waiting for confirmation on {'/'.join(tf.label for tf in conf_tfs)}")
                continue

            # 5: the setup ---------------------------------------------------------------
            entry = spec.round_price(confirmation.close)
            protection, stop_detail = self._protection(poi, direction, touch_ts, structures)
            setup, reasons = build_setup(symbol, spec, direction, poi, confirmation, entry, structures,
                                         s.risk, equity, breakeven_trigger_r(poi.timeframe, s.exits),
                                         protection_level=protection, touch_ts=touch_ts)
            if setup is None:
                note = f" [stop would be {spec.round_price(protection)} = {stop_detail.get('stop_basis')}]" if diagnostic else ""
                analysis.rejections.append(f"{label}: {'; '.join(reasons)}{note}")
                continue
            setup.touched_at = pd.Timestamp(touch_ts)
            setup.visit_number = visits
            if s.risk.stop_basis == "confirmation":      # the stop sits beyond the extreme since the (re-)entry, not behind a P
                stop_detail = {"stop_tf": confirmation.timeframe.label, "stop_p_open": None, "stop_p_close": None,
                               "stop_basis": f"the {'low' if direction is Direction.LONG else 'high'} since price last entered the zone, "
                                             f"on the {confirmation.timeframe.label} (stop_basis=confirmation)"}
                protection = confirmation.invalidation_price
            setup.stop_detail = {"stop_p": protection, **stop_detail}
            if diagnostic:
                analysis.diagnostic_setup = setup
                analysis.rejections.append(
                    f"diagnostic: {label} would give {direction.name} entry {setup.entry} stop {setup.stop} target {setup.take_profit} "
                    f"({setup.confirmation.type.value} on {setup.confirmation.timeframe.label} at {setup.confirmation.timestamp}, "
                    f"R:R 1:{setup.rr:.2f}); not a signal")
                return analysis

            # 6: Kronos as an extra indicator ---------------------------------------------------
            notes: List[str] = []
            forecast = self._forecast(views[confirmation.timeframe], notes)
            if forecast is not None:
                analysis.forecasts.setdefault(confirmation.timeframe, forecast)
                if s.kronos.mode == "filter" and forecast.conflicts_with(decision.direction) \
                        and forecast.confidence >= s.kronos.min_confidence:
                    reason = (f"{label}: Kronos forecast {forecast.direction} ({forecast.confidence:.0%}, "
                              f"{forecast.pct_change:+.2f}%) conflicts with {decision.direction} bias")
                    analysis.rejections.append(reason)
                    analysis.signal = Signal(now, SignalStatus.REJECTED, setup, forecast, [reason])
                    continue
                elif forecast.conflicts_with(decision.direction):
                    setup.notes.append(f"Kronos disagrees ({forecast.direction} {forecast.confidence:.0%}) - advisory only")
                else:
                    setup.notes.append(f"Kronos {forecast.direction} ({forecast.confidence:.0%}, {forecast.pct_change:+.2f}%)")
            setup.notes.extend(notes)
            analysis.signal = Signal(now, SignalStatus.VALID, setup, forecast, [])
            return analysis

        if diagnostic:
            analysis.rejections.extend(_diagnostic_zone_notes(pois, bias_side, allowed_poi_tfs, price))
        return analysis
