"""What every trade of a ledger would have made with a target capped at k R (min(planned, k)) or fixed at k R,
walking the 5m bars from the fill: stop first when stop and target sit in the same bar; open after 10 days -> last close.
Run from the repository root:

  python scripts/target_sweep.py EURUSD <ledger.csv> <5m bars.csv>
"""
import sys, numpy as np, pandas as pd
def sweep(label, ledger, bars_path, ks=(0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0)):
    t = pd.read_csv(ledger, parse_dates=["opened_at", "closed_at"])
    b = pd.read_csv(bars_path, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    hi, lo, cl, idx = b.high.values, b.low.values, b.close.values, b.index
    def walk(i0, long, entry, stop, target, i_end):
        risk = abs(entry - stop)
        for i in range(i0, i_end):
            if long:
                if lo[i] <= stop: return -1.0
                if hi[i] >= target: return (target - entry) / risk
            else:
                if hi[i] >= stop: return -1.0
                if lo[i] <= target: return (entry - target) / risk
        return ((cl[i_end - 1] - entry) if long else (entry - cl[i_end - 1])) / risk
    res = {}
    rows = []
    for r in t.itertuples():
        i0 = idx.searchsorted(r.opened_at); i_end = min(len(idx), idx.searchsorted(r.opened_at + pd.Timedelta(days=10)))
        if i0 >= i_end: continue
        long = r.direction == "LONG"; risk = abs(r.entry - r.stop)
        if risk == 0: continue
        sgn = 1 if long else -1
        row = {"ledger": r.r, "sim_orig": walk(i0, long, r.entry, r.stop, r.take_profit, i_end)}
        planned = abs(r.take_profit - r.entry) / risk
        for k in ks:
            row[f"cap{k}"] = walk(i0, long, r.entry, r.stop, r.entry + sgn * min(planned, k) * risk, i_end)
            row[f"fix{k}"] = walk(i0, long, r.entry, r.stop, r.entry + sgn * k * risk, i_end)
        rows.append(row)
    d = pd.DataFrame(rows)
    def stats(c):
        x = d[c]; eq = x.cumsum(); dd = (eq - eq.cummax().clip(lower=0)).min()
        return f"{c:9s} win {100 * (x > 0.05).mean():3.0f}%  {x.mean():+.2f}R/tr  total {x.sum():+6.1f}R  dd {dd:6.1f}R"
    print(f"== {label}: {len(d)} trades")
    for c in ["ledger", "sim_orig"] + [f"cap{k}" for k in ks] + [f"fix{k}" for k in ks]:
        print("  ", stats(c))
if __name__ == "__main__":
    sweep(sys.argv[1], sys.argv[2], sys.argv[3])
