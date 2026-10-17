"""His bias per timeframe on a dated day next to the engine's: the fast loop for the bias gate.

  PYTHONPATH=. python scripts/bias_suite.py <config.yaml> [--bias docs/dossiers/source_bias.yaml] [--data-dir data/histdata_1m]
      [--at 07:00] [--warmup 2] [--out table.md]

For every record the engine reads the bias at <date> <at> UTC (09:00 Amsterdam in summer) and the table shows, per timeframe,
his reading, the code's, and the code's reason (liquidity view, balance view); then the 3-of-5 outcome on both sides.
"""
import argparse, sys
from pathlib import Path
import pandas as pd, yaml
from kronos_trader.config import Settings
from kronos_trader.data.tv_cache import load_all
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy.engine import StrategyEngine
from kronos_trader.backtest.dossier import warm_up

NORM = {"bull": "bullish", "bullish": "bullish", "bear": "bearish", "bearish": "bearish", "50/50": "50/50", "50-50": "50/50", "neutral": "50/50"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config"); ap.add_argument("--bias", default="docs/dossiers/source_bias.yaml"); ap.add_argument("--data-dir", default="data/histdata_1m")
    ap.add_argument("--at", default="07:00"); ap.add_argument("--warmup", type=float, default=2.0); ap.add_argument("--out", default="")
    args = ap.parse_args()
    settings = Settings.from_yaml(args.config); settings.kronos.mode = "off"
    records = yaml.safe_load(open(args.bias)) or []
    data = {}
    lines = ["| Date | Symbol | TF | His | Code | Code's reason |", "|---|---|---|---|---|---|"]
    for r in records:
        sym = r["symbol"]
        if sym not in data:
            data[sym] = MultiTimeframeData(load_all(args.data_dir, sym))
        now = pd.Timestamp(f"{r['date']} {args.at}")
        engine = StrategyEngine(settings)
        warm_up(engine, data[sym], sym, now, args.warmup)
        a = engine.analyze(sym, data[sym].as_of(now, lookback=settings.structure.lookback), equity=settings.account_size, now=now)
        agree = 0; n = 0
        for tf, b in a.biases.items():
            his = NORM.get(str(r.get("his", {}).get(tf.label, "")).lower(), str(r.get("his", {}).get(tf.label, "-")))
            code = str(b.bias)
            why = (f"liquidity {b.liquidity_view}, balance {b.balance_view}" + ("; " + "; ".join(b.notes) if b.notes else ""))[:160]
            mark = "=" if his == code else "x"
            if his != "-": n += 1; agree += his == code
            lines.append(f"| {r['date']} | {sym} | {tf.label} | {his} | {code} {mark} | {why} |")
        gate = a.decision.direction if a.decision.tradable else "none"
        lines.append(f"| {r['date']} | {sym} | 3 of 5 | {r.get('match', '-')} | {gate} | {a.decision.reason[:140]} ({agree}/{n} timeframes agree) |")
        print(f"{r['date']} {sym}: {agree}/{n} timeframes agree; his {r.get('match','-')}, code {gate}", file=sys.stderr)
    table = "\n".join(lines); print(table)
    if args.out:
        Path(args.out).write_text(f"Config `{args.config}`, read at {args.at} UTC, warm-up {args.warmup} days.\n\n" + table + "\n")


if __name__ == "__main__":
    main()
