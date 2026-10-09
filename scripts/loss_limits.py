"""Loss-limit overlays on a combined ledger (scripts/portfolio.py): trades in open order, a trade is skipped while a rule
is active (a weekly or monthly closed loss, a pause after losses in a row).  Run from the repository root:

  python scripts/loss_limits.py <combined ledger.csv>
"""
import sys, pandas as pd
RISK = 1.5
def stats(name, k):
    m = k.groupby(k.opened_at.dt.to_period("M")).r.sum() * RISK
    full = pd.period_range("2024-02", "2026-09", freq="M"); m = m.reindex(full, fill_value=0.0)
    eq = (k.sort_values("closed_at").r * RISK).cumsum(); dd = (eq - eq.cummax().clip(lower=0)).min()
    print(f"{name:44s} {len(k):3d} tr {k.r.sum():+6.1f}R  avg {m.mean():+5.2f}%  median {m.median():+5.2f}%  neg months {int((m<0).sum()):2d}  "
          f"worst {m.min():+5.1f}%  under -3%: {int((m<-3).sum())}  dd {dd:+5.1f}%")
    return k
def run(k, period=None, limit_r=None, streak=None, pause_days=None, per_market=False):
    keep, pnl, losses, paused_until = [], {}, {}, {}
    closed = []   # (closed_at, r, sym) for realised P&L
    for r in k.sort_values("opened_at").itertuples():
        # realised P&L of trades closed before this open, in this period
        ok = True
        if period:
            key = r.opened_at.to_period(period)
            real = sum(x[1] for x in closed if x[0] <= r.opened_at and x[0].to_period(period) == key)
            if real <= -limit_r: ok = False
        if streak:
            scope = r.sym if per_market else "ALL"
            if paused_until.get(scope) is not None and r.opened_at < paused_until[scope]: ok = False
        if ok:
            keep.append(r.Index); closed.append((r.closed_at, r.r, r.sym))
            if streak:
                scope = r.sym if per_market else "ALL"
                # streak counted on close order approximately by open order
                losses[scope] = losses.get(scope, 0) + 1 if r.r < 0 else 0
                if losses[scope] >= streak:
                    paused_until[scope] = r.closed_at + pd.Timedelta(days=pause_days); losses[scope] = 0
    return k.loc[keep]
k = pd.read_csv(sys.argv[1], parse_dates=["opened_at", "closed_at"])
stats("no overlay", k)
for lim in (2, 3, 4):
    stats(f"month stop at -{lim}R (-{lim*RISK:.1f}%)", run(k, period="M", limit_r=lim))
for lim in (2, 3):
    stats(f"week stop at -{lim}R", run(k, period="W", limit_r=lim))
for st, d in ((3, 3), (3, 7), (4, 7)):
    stats(f"market pause {d}d after {st} losses in a row", run(k, streak=st, pause_days=d, per_market=True))
    stats(f"account pause {d}d after {st} losses in a row", run(k, streak=st, pause_days=d))
stats("week -3R + month -4R", run(run(k, period="W", limit_r=3), period="M", limit_r=4))
