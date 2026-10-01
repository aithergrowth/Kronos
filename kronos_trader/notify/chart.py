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
from ..core.types import POI, Bias, ForecastSummary, TradeSetup

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
) -> Path:
    """Draw ``series`` (last ``lookback`` candles) with zones, setup lines and the forecast fan; return the PNG path."""
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

    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=110)
    fig.patch.set_facecolor("white")

    # zones -------------------------------------------------------------------------------
    last = float(closes[-1])
    zones = sorted(pois, key=lambda p: abs((p.low + p.high) / 2 - last))[:max_zones]
    for poi in zones:
        colour = BULL_ZONE if poi.direction is Bias.BULLISH else BEAR_ZONE
        start = max(0, view.index_at_or_after(poi.created_at) - 1) if poi.created_at is not None else 0
        ax.add_patch(Rectangle((start, poi.low), x_right - start, poi.high - poi.low, facecolor=colour, edgecolor="none", zorder=1))
        arrow = "▲" if poi.direction is Bias.BULLISH else "▼"
        ax.text(start + 0.3, poi.high, f"{poi.timeframe.label} {arrow} POI", fontsize=7.5, va="bottom", ha="left", color="#333", zorder=5)

    # candles -----------------------------------------------------------------------------
    for i in range(n):
        up = closes[i] >= opens[i]
        colour = UP if up else DOWN
        ax.plot([i, i], [lows[i], highs[i]], color=colour, linewidth=0.8, zorder=3)
        body_low, body_high = min(opens[i], closes[i]), max(opens[i], closes[i])
        ax.add_patch(Rectangle((i - 0.3, body_low), 0.6, max(body_high - body_low, 1e-9), facecolor=colour, edgecolor=colour, zorder=3))

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
        how = f"{conf.type.value} on {conf.timeframe.label}" if conf is not None else "confirmation"
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

    # axes --------------------------------------------------------------------------------
    ax.set_xlim(-1, x_right)
    lo = min(float(lows.min()), *(p.low for p in zones), *(float(getattr(forecast, "expected_low", lows.min())) for _ in [0]))
    hi = max(float(highs.max()), *(p.high for p in zones), *(float(getattr(forecast, "expected_high", highs.max())) for _ in [0]))
    if setup is not None:
        lo, hi = min(lo, setup.stop, setup.take_profit), max(hi, setup.stop, setup.take_profit)
    pad = (hi - lo) * 0.05 or 1e-6
    ax.set_ylim(lo - pad, hi + pad)
    step = max(1, n // 8)
    ticks = list(range(0, n, step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([pd.Timestamp(times[i]).strftime("%d %b %H:%M") for i in ticks], fontsize=8, rotation=0)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, color="#eeeeee", linewidth=0.6)
    fig.suptitle(title or f"{series.symbol} {series.timeframe.label}", x=0.01, y=0.985, ha="left", fontsize=11, fontweight="bold")
    if subtitle:
        ax.set_title(subtitle, loc="left", fontsize=8.5, color="#555555", pad=6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def forecast_rows(forecast: ForecastSummary, last_time: pd.Timestamp, timeframe, server_offset: pd.Timedelta = pd.Timedelta(0)):
    """Mean OHLC in server time, preserving the model's actual future calendar.

    Dated paths must agree on their timestamps. Undated legacy paths retain
    the timeframe's default calendar; a dated path is never silently relabeled.
    """
    paths = getattr(forecast, "paths_ohlc", None) or []
    if not paths:
        return []
    horizon = min(len(p) for p in paths)
    if not horizon:
        return []
    stacked = np.stack([p[["open", "high", "low", "close"]].to_numpy(dtype=float)[:horizon] for p in paths])
    mean = stacked.mean(axis=0)
    dates = []
    for path in paths:
        raw = path["timestamp"].iloc[:horizon] if "timestamp" in path else (
            path.index[:horizon] if isinstance(path.index, pd.DatetimeIndex) else None
        )
        dates.append(None if raw is None else pd.DatetimeIndex(pd.to_datetime(raw, utc=True)).tz_convert(None))
    if any(date is not None for date in dates):
        if any(date is None for date in dates):
            raise ValueError("forecast paths must all supply the same timestamps")
        times = dates[0]
        last_utc = pd.Timestamp(last_time)
        if last_utc.tzinfo is not None:
            last_utc = last_utc.tz_convert("UTC").tz_localize(None)
        if (times.hasnans or not times.is_monotonic_increasing or not times.is_unique
                or times[0] <= last_utc or any(not times.equals(date) for date in dates[1:])):
            raise ValueError("forecast timestamps must agree and increase after the last candle")
    else:
        times = pd.DatetimeIndex(timeframe.future_timestamps(last_time, horizon))
    rows = []
    for k in range(horizon):
        t = int((pd.Timestamp(times[k]) + server_offset).timestamp())
        rows.append((t, *[float(v) for v in mean[k]]))
    return rows
