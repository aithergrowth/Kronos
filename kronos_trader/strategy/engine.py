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
from .poi import current_visit, map_pois
from .risk import build_setup
from .structure import StructureAnalysis, analyze_structure


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


class StrategyEngine:
    def __init__(self, settings: Optional[Settings] = None, forecaster=None, calendar=None):
        self.settings = settings or Settings()
        self.forecaster = forecaster
        self.calendar = calendar            # Optional configured news gate; window durations are project choices.
        self._structure_cache: Dict[Tuple[str, Timeframe], Tuple[pd.Timestamp, int, StructureAnalysis]] = {}

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

    def _protection_level(self, poi: POI, direction: Direction, touch_ts, structures: Dict[Timeframe, StructureAnalysis]) -> float:
        """The P the stop sits behind: the most recent 1H balance level in the trade direction formed
        since the touch, else the POI's own protector ("SL ALTIJD op minimale 1H P")."""
        h1 = structures.get(Timeframe.H_1)
        if h1 is not None and poi.timeframe > Timeframe.H_1:
            start = h1.series.index_at_or_after(touch_ts)
            recent = [g for g in h1.gaps_in(direction.bias) if g.index >= start and not g.is_violated]
            if recent:
                return recent[-1].protection_level
        return poi.protector_extreme

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
    ) -> Analysis:
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

        structures = {tf: self.structure_for(symbol, view) for tf, view in views.items()}

        # 1 + 2: bias ----------------------------------------------------------------
        biases = {tf: timeframe_bias(structures[tf], s.bias) for tf in BIAS_TIMEFRAMES if tf in views}
        decision = combine_biases({tf: b.bias for tf, b in biases.items()}, s.bias)

        # 3: POIs on every mapped timeframe, both sides --------------------------------
        pois: List[POI] = []
        for tf in POI_TIMEFRAMES:
            if tf in views:
                pois.extend(map_pois(structures[tf], s.structure, price))

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

        if not decision.tradable:
            analysis.rejections.append(decision.reason)
            return analysis

        direction = Direction.from_bias(decision.direction)
        allowed_poi_tfs = tuple(POI_TIMEFRAMES) if decision.mode is TradeMode.FULL else tuple(s.confirmation.scalp_poi_timeframes)

        # session windows: no new entries outside them (A 02:30:56 rejects a 17:00 entry) ---------
        if s.session.enabled:
            inside, local_label = in_session(now, s.session)
            if not inside:
                analysis.rejections.append(f"outside the entry windows ({local_label} {s.session.timezone}); open trades run on")
                return analysis

        # Configured news blackout: reject new signals around relevant high-impact events. ---
        if self.calendar is not None and s.news.enabled:
            event = self.calendar.blackout(symbol, now)
            if event is not None:
                analysis.rejections.append(f"news blackout: {event.title} ({event.currency}) at {event.time:%H:%M} UTC; open trades run on")
                return analysis

        # 4: POIs being visited now, highest timeframe first ------------------------------
        candidates = [p for p in pois
                      if p.direction is decision.direction and p.timeframe in allowed_poi_tfs
                      and p.status is POIStatus.ACTIVE]
        candidates.sort(key=lambda p: p.timeframe, reverse=True)
        if not candidates:
            n_dir = sum(1 for p in pois if p.direction is decision.direction and p.timeframe in allowed_poi_tfs
                        and p.status is not POIStatus.INVALIDATED)
            analysis.rejections.append(f"price is not inside a {decision.direction} POI ({n_dir} valid zones mapped)")
            return analysis

        for poi in candidates:
            visit_start, visits, invalid = current_visit(poi, lowest, s.confirmation.max_extension_zones)
            label = poi.describe()
            if invalid:
                analysis.rejections.append(f"{label}: invalidated on {lowest_tf.label}")
                continue
            if visit_start is None:
                analysis.rejections.append(f"{label}: no active visit on {lowest_tf.label}")
                continue
            if visits > 1 and not s.confirmation.allow_retest:
                analysis.rejections.append(f"{label}: visit #{visits} - only the first return is traded")
                continue
            touch_ts = lowest.timestamps.iloc[visit_start]

            conf_tfs = [tf for tf in allowed_confirmation_timeframes(poi.timeframe, s.confirmation) if tf in views]
            if not conf_tfs:
                needed = [tf.label for tf in allowed_confirmation_timeframes(poi.timeframe, s.confirmation)]
                analysis.rejections.append(f"{label}: no confirmation timeframe data ({'/'.join(needed)} needed)")
                continue
            confirmation = None
            for ctf in conf_tfs:
                confirmation = find_confirmation(views[ctf], poi, touch_ts, s.confirmation, s.structure,
                                                 max_confirmation_age, structure=structures.get(ctf))
                if confirmation is not None:
                    break
            if confirmation is None:
                analysis.rejections.append(
                    f"{label}: touched at {touch_ts}, waiting for confirmation on {'/'.join(tf.label for tf in conf_tfs)}")
                continue

            # 5: the setup ---------------------------------------------------------------
            entry = spec.round_price(confirmation.close)
            protection = self._protection_level(poi, direction, touch_ts, structures)
            setup, reasons = build_setup(symbol, spec, direction, poi, confirmation, entry, structures,
                                         s.risk, equity, breakeven_trigger_r(poi.timeframe, s.exits),
                                         protection_level=protection)
            if setup is None:
                analysis.rejections.append(f"{label}: {'; '.join(reasons)}")
                continue

            # 6: Kronos as an extra indicator ---------------------------------------------------
            notes: List[str] = []
            forecast = self._forecast(views[confirmation.timeframe], notes)
            if s.kronos.mode == "filter" and forecast is None:
                reason = f"{label}: Kronos forecast unavailable; filter mode requires a forecast"
                setup.notes.extend(notes)
                analysis.rejections.extend(notes)
                analysis.rejections.append(reason)
                analysis.signal = Signal(now, SignalStatus.REJECTED, setup, None, [reason])
                continue
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

        return analysis
