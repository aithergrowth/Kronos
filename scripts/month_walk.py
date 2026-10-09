"""One month, day by day, the way Max reads it: the bias per timeframe (3 of 5), the 4H and 1H zones near price with
X / B / P, and which zones price visited without the engine finding a confirmation.  Run from the repository root:

  PYTHONPATH=. python scripts/month_walk.py <config.yaml> <symbol> <data_dir> <YYYY-MM> <out_dir> [--warmup 5] [--step 5]

Writes <out_dir>/README_walk.md.  The trades themselves come from the backtester over the same month (``backtest --out``)
and their charts from ``trade-charts``; ``scripts/month_walk.py`` only reads, it executes nothing.
"""
import argparse
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from kronos_trader.config import Settings
from kronos_trader.core import POIStatus
from kronos_trader.core.timeframe import Timeframe as T
from kronos_trader.data.tv_cache import load_all
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy.engine import StrategyEngine, in_session
from kronos_trader.backtest.dossier import warm_up

AMS = ZoneInfo("Europe/Amsterdam")


def side(p) -> str:
    d = p.direction
    return getattr(d, "name", str(d)).lower()


def zone_line(p, dec):
    gap = getattr(p, "gap", None)
    b = f"{gap.low:.{dec}f}-{gap.high:.{dec}f}" if gap is not None else "-"
    x = getattr(p, "liquidity_level", None)
    return (f"{p.timeframe.label} {side(p)} {p.low:.{dec}f}-{p.high:.{dec}f} "
            f"(X {x:.{dec}f}, B {b}, P {p.protector_extreme:.{dec}f}; {p.status.value}; formed {pd.Timestamp(p.created_at):%d %b %H:%M})"
            if x is not None else f"{p.timeframe.label} {side(p)} {p.low:.{dec}f}-{p.high:.{dec}f} ({p.status.value})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("symbol"); ap.add_argument("data_dir"); ap.add_argument("month"); ap.add_argument("out_dir")
    ap.add_argument("--warmup", type=float, default=5.0, help="days replayed before the month so zone visits have history")
    ap.add_argument("--step", type=int, default=5, help="minutes between looks inside the session windows")
    ap.add_argument("--near-pct", type=float, default=1.0, help="zones within this %% of price are listed")
    args = ap.parse_args()
    settings = Settings.from_yaml(args.config); settings.kronos.mode = "off"
    spec = settings.symbol(args.symbol); dec = spec.price_decimals
    data = MultiTimeframeData(load_all(args.data_dir, args.symbol))
    engine = StrategyEngine(settings)
    first = pd.Timestamp(args.month + "-01")
    last = (first + pd.offsets.MonthEnd(1)).normalize() + pd.Timedelta(hours=23, minutes=59)
    warm_up(engine, data, args.symbol, first, args.warmup)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    lines = [f"# {args.symbol} {first:%B %Y}, day by day", "",
             f"Config `{args.config}`; one look every {args.step} minutes inside the session windows "
             f"({', '.join(f'{a}-{b}' for a, b in settings.session.windows)} {settings.session.timezone}); warm-up {args.warmup} days. "
             "Bias at the first look of the day. Zones: the 4H and 1H zones within "
             f"{args.near_pct:.1f} % of price at that moment, with X / B / P as the code maps them.", ""]
    day_rows = []
    for day in pd.date_range(first, last, freq="D"):
        if day.weekday() >= 5:
            continue
        looks = [t for t in pd.date_range(day, day + pd.Timedelta(hours=23, minutes=59), freq=f"{args.step}min")
                 if in_session(t, settings.session)[0]]
        if not looks:
            continue
        first_look = None
        visited = defaultdict(set)       # zone label -> set of rejection kinds seen
        signals = []
        for now in looks:
            views = data.as_of(now, lookback=settings.structure.lookback)
            if not views:
                continue
            a = engine.analyze(args.symbol, views, equity=settings.account_size, now=now)
            if first_look is None:
                first_look = (now, a)
            for r in a.rejections:
                if "POI" in r and ":" in r and ("waiting for confirmation" in r or "R:R" in r or "no room" in r or "already traded" in r):
                    label, _, why = r.partition(": ")
                    visited[label].add(why.split(" (")[0][:70])
            if a.has_valid_signal:
                st = a.signal.setup
                signals.append(f"{now:%H:%M} UTC {st.direction.name} entry {st.entry} stop {st.stop} target {st.take_profit} ({st.rr:.2f}R; "
                               f"{st.confirmation.type.value} on {st.confirmation.timeframe.label}; zone {st.poi.timeframe.label} {st.poi.low:.{dec}f}-{st.poi.high:.{dec}f})")
                engine.mark_traded(args.symbol, st.poi.key, getattr(st, "visit_number", None))
        if first_look is None:
            continue
        lowest = data.lowest
        if lowest.index_at_or_after(day) >= len(lowest) or lowest.ts_list[min(lowest.index_at_or_after(day), len(lowest) - 1)].date() != day.date():
            continue          # no candles of this day: the data ends earlier
        now, a = first_look
        bias = {tf.label: b.bias for tf, b in a.biases.items()}
        decision = a.decision.direction if a.decision.tradable else "none"
        mode = getattr(a.decision, "mode", None)
        price = a.price
        near = [p for p in a.pois if p.timeframe in (T.H_4, T.H_1) and p.status in (POIStatus.ACTIVE, POIStatus.TESTED, POIStatus.FRESH)
                and abs((p.low + p.high) / 2 - price) / price * 100 <= args.near_pct]
        near.sort(key=lambda p: abs((p.low + p.high) / 2 - price))
        day_rows.append((day, bias, decision, mode, price, near, visited, signals))
    lines.append("## The month at a glance")
    lines.append("")
    lines.append("| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for day, bias, decision, mode, price, near, visited, signals in day_rows:
        dec_txt = decision if decision == "none" else f"{decision} ({getattr(mode, 'value', mode)})"
        zones = "; ".join(f"{p.timeframe.label} {side(p)} {p.low:.{dec}f}-{p.high:.{dec}f}" for p in near[:4]) or "-"
        vis = "; ".join(f"{k.split(' (')[0]}: {'/'.join(sorted(v))}" for k, v in list(visited.items())[:3]) or "-"
        sig = "<br>".join(signals) or "-"
        lines.append(f"| {day:%a %d} | {bias.get('1M','-')} | {bias.get('1W','-')} | {bias.get('1D','-')} | {bias.get('4H','-')} | {bias.get('1H','-')} | {dec_txt} | {price:.{dec}f} | {zones} | {vis} | {sig} |")
    lines.append("")
    lines.append("## Zones per day, as mapped (X / B / P)")
    lines.append("")
    for day, bias, decision, mode, price, near, visited, signals in day_rows:
        lines.append(f"**{day:%A %d %B}** (price {price:.{dec}f}, bias {decision})")
        for p in near[:6]:
            lines.append(f"- {zone_line(p, dec)}")
        if not near:
            lines.append("- no 4H or 1H zone within reach")
        lines.append("")
    (out / "README_walk.md").write_text("\n".join(lines))
    print(f"written {out / 'README_walk.md'}: {len(day_rows)} days, {sum(len(r[7]) for r in day_rows)} signals")


if __name__ == "__main__":
    main()
