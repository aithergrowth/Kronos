"""Chart images for Telegram and the briefing: candles, POI zones, the setup and Kronos's possible paths.

Pure matplotlib (Agg), no chart library, so it runs on the laptop and on a VPS
without a display.  The forecast fan is drawn to the right of the last candle:
every sampled Kronos path as a thin line, the mean path thicker, and the
expected high / low band.  It is a picture of possibilities, not a signal.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd

from ..core.candles import CandleSeries
from ..core.timeframe import Timeframe
from ..core.types import POI, Bias, ForecastSummary, TradeSetup

# chart file names: the minute and the month differ only in case ("1m", "1M"), one file on Windows and macOS, so the
# second overwrites the first and git reads the other as modified for ever (9 October, Max's laptop); the live charts
# never render a minute chart, the dossiers and the run charts do
CHART_LABELS = {Timeframe.MIN_1: "1min", Timeframe.MN_1: "1MO"}


def chart_label(tf: Timeframe) -> str:
    return CHART_LABELS.get(tf, tf.label)


UP, DOWN = "#2e9e5b", "#d9534f"
BULL_ZONE, BEAR_ZONE = (0.18, 0.62, 0.36, 0.18), (0.85, 0.33, 0.31, 0.18)


def render_chart(
    series: CandleSeries,
    path,
    *,
    pois: Iterable[POI] = (),
    setup: Optional[TradeSetup] = None,
    forecast: Optional[ForecastSummary] = None,
    title: str = "",
    subtitle: str = "",
    lookback: int = 120,
    price_decimals: int = 5,
    max_zones: int = 6,
    extra_boxes: Iterable = (),
    extra_lines: Iterable = (),
    mark_zones: bool = False,
    last_price: Optional[float] = None,
) -> Path:
    """Draw ``series`` (last ``lookback`` candles) with zones, setup lines and the forecast fan; return the PNG path.

    Each zone is a band from the candle it formed on to the right edge, named at the right edge with its timeframe, side
    and prices. Dorus's X, B and P marks go on the setup's zone, or on every zone with ``mark_zones`` (the dossiers); a
    dashed line is the last price. The price axis follows the candles: a zone far away is left out of the picture
    instead of squeezing the candles flat (14 October, Max: the monthly zone made the briefing chart unreadable)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    view = series.tail(lookback)
    n = len(view)
    if n == 0:
        raise ValueError("nothing to draw")
    opens, highs, lows, closes = (view.df[c].to_numpy(dtype=float) for c in ("open", "high", "low", "close"))
    times = list(view.timestamps)
    paths = getattr(forecast, "paths_ohlc", None) or []
    horizon = max((len(p) for p in paths), default=0)
    x_right = n - 1 + max(horizon, 1) + 1

    fig, ax = plt.subplots(figsize=(11, 6), dpi=130)
    fig.patch.set_facecolor("white")
    d = price_decimals

    # the price axis: the candles (and the setup), with room for the zones that lie near them ----------------------------
    last = float(closes[-1])
    lo, hi = float(lows.min()), float(highs.max())
    if setup is not None:
        lo, hi = min(lo, setup.stop, setup.take_profit), max(hi, setup.stop, setup.take_profit)
    span = (hi - lo) or abs(hi) * 1e-3 or 1e-6
    near_lo, near_hi = lo - 0.5 * span, hi + 0.5 * span
    zones = sorted(pois, key=lambda p: abs((p.low + p.high) / 2 - last))[:max_zones]
    if setup is not None and getattr(setup, "poi", None) is not None and setup.poi not in zones:
        zones.append(setup.poi)
    zones = [p for p in zones if p.high >= near_lo and p.low <= near_hi
             or (setup is not None and getattr(setup, "poi", None) is not None and p.key == setup.poi.key)]
    for p in zones:
        lo, hi = min(lo, max(p.low, near_lo)), max(hi, min(p.high, near_hi))
    if paths:
        lo = min(lo, max(float(forecast.expected_low), near_lo))
        hi = max(hi, min(float(forecast.expected_high), near_hi))
    pad = (hi - lo) * 0.06 or 1e-6
    y_lo, y_hi = lo - pad, hi + pad

    # zones -------------------------------------------------------------------------------
    if setup is not None and getattr(setup, "poi", None) is not None:
        marked = {setup.poi.key}
    else:
        marked = {p.key for p in zones} if mark_zones else set()
    labels = []
    for poi in zones:
        colour = BULL_ZONE if poi.direction is Bias.BULLISH else BEAR_ZONE
        start = max(0, view.index_at_or_after(poi.created_at) - 1) if poi.created_at is not None else 0
        ax.add_patch(Rectangle((start, poi.low), x_right - start, poi.high - poi.low, facecolor=colour, edgecolor="none", zorder=1))
        bullish = poi.direction is Bias.BULLISH
        side = "demand" if bullish else "supply"
        labels.append(((max(poi.low, y_lo) + min(poi.high, y_hi)) / 2,
                       f"{poi.timeframe.label} {side} {poi.low:.{d}f}–{poi.high:.{d}f}", "#1f6f3f" if bullish else "#a3312b"))
        # Dorus's three marks on the zone's left edge: X the liquidity taken, B the balance level (the gap), P the protected candle.
        # With a setup only its own zone carries the marks, the other zones stay plain bands.
        if poi.key not in marked:
            continue
        line_colour = "#1f6f3f" if bullish else "#a3312b"
        x_level = getattr(poi, "liquidity_level", None)
        if x_level:
            ax.hlines(x_level, start, x_right, colors=line_colour, linestyles="--", linewidth=0.9, zorder=4)
            ax.text(start + 0.3, x_level, "X", fontsize=8, fontweight="bold", va="top" if bullish else "bottom", ha="left",
                    color=line_colour, zorder=5)
        gap = getattr(poi, "gap", None)
        if gap is not None:
            ax.add_patch(Rectangle((start, gap.low), x_right - start, gap.high - gap.low, facecolor="none", edgecolor=line_colour,
                                   linewidth=0.9, linestyle=":", zorder=4))
            ax.text(start + 1.2, (gap.low + gap.high) / 2, "B", fontsize=8, fontweight="bold", va="center", ha="left",
                    color=line_colour, zorder=5)
        p_level = getattr(poi, "protection_level", None)
        if p_level:
            ax.hlines(p_level, start, x_right, colors=line_colour, linestyles="-", linewidth=1.1, zorder=4)
            ax.text(start + 0.3, p_level, "P", fontsize=8, fontweight="bold", va="bottom" if bullish else "top", ha="left",
                    color=line_colour, zorder=5)

    # candles -----------------------------------------------------------------------------
    for i in range(n):
        up = closes[i] >= opens[i]
        colour = UP if up else DOWN
        ax.plot([i, i], [lows[i], highs[i]], color=colour, linewidth=0.8, zorder=3)
        body_low, body_high = min(opens[i], closes[i]), max(opens[i], closes[i])
        ax.add_patch(Rectangle((i - 0.3, body_low), 0.6, max(body_high - body_low, 1e-9), facecolor=colour, edgecolor=colour, zorder=3))

    for low, high, label in extra_boxes:          # e.g. the recorded zone of a trade the replay could not reproduce
        ax.add_patch(Rectangle((0, low), x_right, high - low, facecolor="none", edgecolor="#555555", linestyle="--", linewidth=1.0, zorder=2))
        ax.text(0.3, high, f" {label}", fontsize=7, va="bottom", color="#555555", zorder=5)

    for price, label, from_ts in extra_lines:     # e.g. the 1H P the stop sits behind when it is not the zone's own P
        xs = 0
        if from_ts is not None:
            try:
                xs = min(max(view.index_at_or_after(pd.Timestamp(from_ts)), 0), n - 1)
            except Exception:
                xs = 0
        ax.hlines(price, xs, x_right, colors="#8B0000", linestyles="dashdot", linewidth=1.0, zorder=4)
        ax.text(xs + 0.3, price, f" {label}", fontsize=7, va="bottom", color="#8B0000", zorder=5)

    # setup: the position tool from the confirmation candle to the right edge -----------------
    if setup is not None:
        conf = getattr(setup, "confirmation", None)
        ci = view.index_at_or_after(conf.timestamp) if conf is not None else n - 1
        ci = min(max(ci, 0), n - 1)
        x0, width = ci + 0.5, x_right - (ci + 0.5)
        risk_lo, risk_hi = sorted((setup.entry, setup.stop))
        reward_lo, reward_hi = sorted((setup.entry, setup.take_profit))
        ax.add_patch(Rectangle((x0, risk_lo), width, risk_hi - risk_lo, facecolor=(0.85, 0.33, 0.31, 0.22), edgecolor=DOWN, linewidth=0.8, zorder=2))
        ax.add_patch(Rectangle((x0, reward_lo), width, reward_hi - reward_lo, facecolor=(0.18, 0.62, 0.36, 0.22), edgecolor=UP, linewidth=0.8, zorder=2))
        ax.axhline(setup.entry, color="#333333", linewidth=1.0, zorder=4)
        short = setup.direction.sign < 0
        ax.plot([ci], [setup.entry], marker="v" if short else "^", markersize=9, color="#333333", zorder=6)
        d = price_decimals
        how = f"{conf.type.value} op {conf.timeframe.label}" if conf is not None else "confirmation"
        ax.text(x0 + 0.3, setup.entry, f" {'SELL' if short else 'BUY'} {setup.entry:.{d}f}  ({how})", fontsize=8,
                va="bottom", color="#222222", zorder=5)
        ax.text(x0 + 0.3, setup.stop, f" SL {setup.stop:.{d}f}  -1R", fontsize=8, va="bottom" if setup.stop > setup.entry else "top",
                color=DOWN, zorder=5)
        ax.text(x0 + 0.3, setup.take_profit, f" TP {setup.take_profit:.{d}f}  +{setup.rr:.1f}R", fontsize=8,
                va="top" if setup.take_profit < setup.entry else "bottom", color=UP, zorder=5)

    # forecast fan ------------------------------------------------------------------------
    if paths:
        xs_future = np.arange(n, n + horizon)
        for p in paths:
            c = p["close"].to_numpy(dtype=float)[:horizon]
            ax.plot(np.concatenate(([n - 1], xs_future[:len(c)])), np.concatenate(([last], c)), color="#7f8c8d", linewidth=0.7, alpha=0.6, zorder=2)
        mean = np.mean(np.stack([p["close"].to_numpy(dtype=float)[:horizon] for p in paths if len(p) >= horizon]), axis=0)
        verdict = (f"{forecast.direction.name.lower()} {forecast.confidence:.0%}" if forecast.direction is not Bias.NEUTRAL else "neutral")
        ax.plot(np.concatenate(([n - 1], xs_future)), np.concatenate(([last], mean)), color="#1f4e79", linewidth=1.8, zorder=4,
                label=f"Kronos: {verdict}, {forecast.pct_change:+.2f}% expected, mean of {len(paths)} paths")
        ax.add_patch(Rectangle((n - 0.5, forecast.expected_low), horizon + 1, forecast.expected_high - forecast.expected_low,
                               facecolor=(0.12, 0.31, 0.47, 0.10), edgecolor="none", zorder=1))
        ax.axvline(n - 0.5, color="#999999", linewidth=0.6, linestyle=":", zorder=2)
        ax.legend(loc="upper right", fontsize=8, frameon=False)

    # the last price, and the zone names at the right edge, spread so that none covers another ---------------------------
    now_price = float(last_price) if last_price is not None and y_lo <= float(last_price) <= y_hi else last
    ax.axhline(now_price, color="#555555", linewidth=0.8, linestyle="--", zorder=4)
    labels.append((now_price, f"{now_price:.{d}f}", "#222222"))
    gap = (y_hi - y_lo) * 0.045
    placed = []
    for y, text, colour in sorted(labels, key=lambda t: t[0]):
        y = min(max(y, y_lo + gap / 2), y_hi - gap / 2)
        if placed and y - placed[-1][0] < gap:
            y = placed[-1][0] + gap
        placed.append((y, text, colour))
    if placed and placed[-1][0] > y_hi - gap / 2:                  # pushed past the top: shift the whole stack down
        shift = placed[-1][0] - (y_hi - gap / 2)
        placed = [(y - shift, t, c) for y, t, c in placed]
    # with a setup the right edge carries the entry, stop and target: the zone names go to the left edge then
    label_x, label_ha = (0.3, "left") if setup is not None else (x_right - 0.5, "right")
    for y, text, colour in placed:
        ax.text(label_x, y, text, fontsize=8.5, va="center", ha=label_ha, color=colour, zorder=7,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=colour, linewidth=0.6, alpha=0.9))

    # axes --------------------------------------------------------------------------------
    ax.set_xlim(-1, x_right)
    ax.set_ylim(y_lo, y_hi)
    step = max(1, n // 8)
    ticks = list(range(0, n, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([pd.Timestamp(times[i]).strftime("%d %b %H:%M") for i in ticks], fontsize=9, rotation=0)
    ax.tick_params(axis="y", labelsize=9)
    ax.grid(True, color="#eeeeee", linewidth=0.6)
    fig.suptitle(title or f"{series.symbol} {series.timeframe.label}", x=0.01, y=0.985, ha="left", fontsize=12, fontweight="bold")
    if subtitle:
        ax.set_title(subtitle, loc="left", fontsize=9.5, color="#444444", pad=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def forecast_rows(forecast: ForecastSummary, last_time: pd.Timestamp, timeframe, server_offset: pd.Timedelta = pd.Timedelta(0)):
    """Rows for the MT5 overlay file: mean path OHLC per future candle, in server time (epoch seconds)."""
    paths = getattr(forecast, "paths_ohlc", None) or []
    if not paths:
        return []
    horizon = min(len(p) for p in paths)
    stacked = np.stack([p[["open", "high", "low", "close"]].to_numpy(dtype=float)[:horizon] for p in paths])
    mean = stacked.mean(axis=0)
    times = timeframe.future_timestamps(last_time, horizon)
    rows = []
    for k in range(horizon):
        t = int((pd.Timestamp(times.iloc[k]) + server_offset).timestamp())
        rows.append((t, *[float(v) for v in mean[k]]))
    return rows
