"""One trade of Dorus's against the engine, fast: for every record in a trades file, warm the engine up, walk minute by
minute around his entry minute with his direction assumed past the gates, and print his numbers next to the code's.

  PYTHONPATH=. python scripts/source_trades.py <config.yaml> [--trades docs/dossiers/source_trades.yaml] [--ids K3a,K3b]
      [--data-dir data/histdata_1m] [--before 30] [--after 15] [--warmup 3] [--out table.md]

Per trade: the bias per timeframe at his minute, the gate that refuses (bias / session / news), the first setup the engine
reaches in the window (a signal when every gate passes, else the diagnostic setup), and the differences in minutes and pips.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

from kronos_trader.config import Settings
from kronos_trader.core.types import Direction
from kronos_trader.data.tv_cache import load_all
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy.engine import StrategyEngine
from kronos_trader.backtest.dossier import warm_up


def rr_of(entry, stop, target):
    risk = abs(entry - stop)
    return abs(target - entry) / risk if risk > 0 else float("nan")


def run_trade(t, settings, data, args):
    symbol, spec = t["symbol"], settings.symbol(t["symbol"])
    pip = spec.pip_size
    his_t = pd.Timestamp(t["time"])
    direction = Direction.SHORT if str(t["direction"]).lower().startswith("s") else Direction.LONG
    engine = StrategyEngine(settings)
    start = his_t - pd.Timedelta(minutes=args.before)
    warm_up(engine, data, symbol, start, args.warmup)
    at_his = None
    first = None            # (kind, time, setup)
    last_zone_note = ""
    for now in pd.date_range(start, his_t + pd.Timedelta(minutes=args.after), freq="1min"):
        views = data.as_of(now, lookback=settings.structure.lookback)
        a = engine.analyze(symbol, views, equity=settings.account_size, now=now, assume_direction=direction, step_minutes=1)
        if now == his_t:
            at_his = a
        zone_notes = [r for r in a.rejections if "POI" in r and ("waiting" in r or "R:R" in r or "no room" in r or "already traded" in r)]
        if zone_notes:
            last_zone_note = zone_notes[0]
        if first is None:
            if a.has_valid_signal:
                first = ("signal", now, a.signal.setup)
            elif getattr(a, "diagnostic_setup", None) is not None:
                first = ("diagnostic", now, a.diagnostic_setup)
    row = {"id": t["id"], "symbol": symbol, "his_time": f"{his_t:%Y-%m-%d %H:%M}", "direction": direction.name,
           "his": f"{t['entry']} / {t['stop']} / {t['target']} ({rr_of(t['entry'], t['stop'], t['target']):.2f}R, {t.get('result', '?')})"}
    if at_his is not None:
        row["bias"] = ", ".join(f"{tf.label} {b.bias}" for tf, b in at_his.biases.items())
        gate = "open" if at_his.decision.tradable else "bias refuses"
        if any(r.startswith("outside the entry windows") for r in at_his.rejections):
            gate += "; session closed"
        if any(r.startswith("news blackout") for r in at_his.rejections):
            gate += "; news"
        row["gate"] = gate
    else:
        row["bias"], row["gate"] = "-", "no candle at his minute"
    if first is None:
        row["code"] = "none in the window"
        row["delta"] = "-"
        row["first_difference"] = (row["gate"] if row.get("gate", "open") != "open" else "") + (" | " + last_zone_note[:160] if last_zone_note else "")
    else:
        kind, when, st = first
        conf = st.confirmation
        row["code"] = (f"{kind} {when:%H:%M}: {st.entry} / {st.stop} / {st.take_profit} ({st.rr:.2f}R; {conf.type.value} on {conf.timeframe.label}; "
                       f"zone {st.poi.timeframe.label} {st.poi.low:.{spec.price_decimals}f}-{st.poi.high:.{spec.price_decimals}f})")
        d_min = int((when - his_t).total_seconds() // 60)
        sign = 1 if direction is Direction.LONG else -1
        row["delta"] = (f"{d_min:+d} min; entry {(st.entry - t['entry']) / pip:+.1f} pips; stop {(st.stop - t['stop']) / pip:+.1f} pips; "
                        f"target {(st.take_profit - t['target']) / pip:+.1f} pips; R:R {st.rr:.2f} vs {rr_of(t['entry'], t['stop'], t['target']):.2f}")
        diff = []
        if row.get("gate", "open") != "open":
            diff.append(row["gate"])
        if abs(d_min) > 5:
            diff.append(f"{abs(d_min)} min {'later' if d_min > 0 else 'earlier'}")
        if abs(st.stop - t["stop"]) / pip > 3:
            diff.append(f"stop {abs(st.stop - t['stop']) / pip:.0f} pips {'wider' if sign * (t['stop'] - st.stop) > 0 else 'tighter'}")
        if abs(st.take_profit - t["target"]) / pip > 3:
            diff.append(f"target {abs(st.take_profit - t['target']) / pip:.0f} pips {'nearer' if sign * (t['target'] - st.take_profit) > 0 else 'farther'}")
        row["first_difference"] = "; ".join(diff) if diff else "matches within 5 minutes and 3 pips"
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config")
    ap.add_argument("--trades", default="docs/dossiers/source_trades.yaml")
    ap.add_argument("--ids", default="")
    ap.add_argument("--data-dir", default="data/histdata_1m")
    ap.add_argument("--before", type=int, default=30)
    ap.add_argument("--after", type=int, default=15)
    ap.add_argument("--warmup", type=float, default=3.0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    settings = Settings.from_yaml(args.config)
    settings.kronos.mode = "off"
    trades = yaml.safe_load(open(args.trades))
    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",")}
        trades = [t for t in trades if t["id"] in wanted]
    data_by_symbol = {}
    rows = []
    for t in trades:
        if t["symbol"] not in data_by_symbol:
            data_by_symbol[t["symbol"]] = MultiTimeframeData(load_all(args.data_dir, t["symbol"]))
        print(f"{t['id']} ...", file=sys.stderr, flush=True)
        rows.append(run_trade(t, settings, data_by_symbol[t["symbol"]], args))
    cols = ["id", "his_time", "direction", "his", "bias", "gate", "code", "delta", "first_difference"]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")).replace("|", "/") for c in cols) + " |")
    table = "\n".join(lines)
    print(table)
    if args.out:
        Path(args.out).write_text(f"Config `{args.config}`, window -{args.before}/+{args.after} min, warm-up {args.warmup} days.\n\n" + table + "\n")


if __name__ == "__main__":
    main()
