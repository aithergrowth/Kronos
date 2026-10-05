"""Combine ledgers under an account-wide cap of N open trades (first come, first served), write one ledger,
print trades, R, monthly stats at a given risk.  Run from the repository root:

  python scripts/portfolio.py <max open> <risk %> <out.csv> EURUSD=<ledger> XAUUSD=<ledger> ...

The written ledger goes into scripts/challenge_sim.py as one --ledger ALL=<out.csv>.
"""
import sys, pandas as pd
def combine(paths, n_open, lo="2024-02-01", hi="2026-09-25"):
    fr = []
    for sym, p in paths.items():
        t = pd.read_csv(p, parse_dates=["opened_at", "closed_at"]); t["sym"] = sym; fr.append(t[["sym", "opened_at", "closed_at", "r"]])
    t = pd.concat(fr); t = t[(t.opened_at >= lo) & (t.opened_at < hi)].sort_values("opened_at").reset_index(drop=True)
    kept, open_until = [], []
    for r in t.itertuples():
        open_until = [c for c in open_until if c > r.opened_at]
        if len(open_until) < n_open:
            kept.append(r.Index); open_until.append(r.closed_at)
    return t, t.loc[kept]
if __name__ == "__main__":
    n_open, risk, out = int(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    paths = dict(a.split("=", 1) for a in sys.argv[4:])
    allt, k = combine(paths, n_open)
    k.to_csv(out, index=False)
    m = k.groupby(k.opened_at.dt.to_period("M")).r.sum() * risk
    eq = (k.sort_values("closed_at").r * risk).cumsum(); dd = (eq - eq.cummax().clip(lower=0)).min()
    print(f"{'+'.join(paths)} max {n_open} open at {risk}%: {len(k)}/{len(allt)} trades, {k.r.sum():+.1f}R, win {100*(k.r>0).mean():.0f}%, "
          f"month avg {m.mean():+.2f}% median {m.median():+.2f}% p25 {m.quantile(.25):+.2f}% p75 {m.quantile(.75):+.2f}% worst {m.min():+.1f}%, "
          f"positive {int((m>0).sum())}/{len(m)}, max dd {dd:.1f}%")
