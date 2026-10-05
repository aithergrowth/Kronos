"""How fast would a prop-firm challenge pass on real trade sequences?  Every calendar day in [first, last] is a start;
the trades of the given ledgers opened from that day on count, P&L = R x risk % of the initial balance, realised at the
close.  Phase 1 needs +target1 %, phase 2 (a fresh account from the day phase 1 passes) +target2 %, each at least
`min_days` trading days; a phase fails on -max_loss % static or a day of -daily_loss % (closed trades).  Run from the
repository root:

  python scripts/challenge_sim.py --ledger EURUSD=docs/backtests/winrate/v3_full_eurusd.csv \
      --ledger XAUUSD=docs/backtests/winrate/gold_intra_c_full.csv --ledger BTCUSD=docs/backtests/winrate/btc_cap2_long.csv \
      --risk 1.0 --first 2024-02-01 --last 2026-03-31
"""
import argparse
import numpy as np
import pandas as pd


def load(spec):
    sym, path = spec.split("=", 1)
    df = pd.read_csv(path, usecols=["opened_at", "closed_at", "r"])
    df["opened_at"] = pd.to_datetime(df["opened_at"]); df["closed_at"] = pd.to_datetime(df["closed_at"]); df["sym"] = sym
    return df


def phase(trades, start, target, risk, max_loss, daily_loss, min_days):
    t = trades[trades.opened_at >= start].sort_values("closed_at")
    bal, days, day_pnl = 0.0, set(), {}
    for row in t.itertuples():
        pnl = row.r * risk
        bal += pnl
        d = row.closed_at.normalize()
        day_pnl[d] = day_pnl.get(d, 0.0) + pnl
        days.add(row.opened_at.normalize())
        if day_pnl[d] <= -daily_loss or bal <= -max_loss:
            return "fail", row.closed_at, (row.closed_at - start).days
        if bal >= target and len(days) >= min_days:
            return "pass", row.closed_at, (row.closed_at - start).days
    return "open", None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", action="append", required=True, help="SYMBOL=path to a trade list CSV (backtest --out)")
    ap.add_argument("--risk", type=float, default=1.0, help="risk per trade, %% of the initial balance")
    ap.add_argument("--first", required=True); ap.add_argument("--last", required=True)
    ap.add_argument("--target1", type=float, default=10.0); ap.add_argument("--target2", type=float, default=5.0)
    ap.add_argument("--max-loss", type=float, default=10.0); ap.add_argument("--daily-loss", type=float, default=5.0)
    ap.add_argument("--min-days", type=int, default=4)
    a = ap.parse_args()
    trades = pd.concat([load(x) for x in a.ledger])
    starts = pd.date_range(a.first, a.last, freq="D")
    p1, p2, total, fails, opens = [], [], [], 0, 0
    for st in starts:
        r1, e1, d1 = phase(trades, st, a.target1, a.risk, a.max_loss, a.daily_loss, a.min_days)
        if r1 != "pass":
            fails += r1 == "fail"; opens += r1 == "open"
            continue
        p1.append(d1)
        r2, _, d2 = phase(trades, e1, a.target2, a.risk, a.max_loss, a.daily_loss, a.min_days)
        if r2 == "pass":
            p2.append(d2); total.append(d1 + d2)
        elif r2 == "fail":
            fails += 1
        else:
            opens += 1
    n = len(starts)
    q = lambda v: f"{np.percentile(v, 25):.0f} / {np.median(v):.0f} / {np.percentile(v, 75):.0f}" if v else "-"
    print(f"{'+'.join(x.split('=')[0] for x in a.ledger)} at {a.risk:.1f} %, {n} starts: funded {len(total) / n:.0%}, failed {fails / n:.0%}, "
          f"unfinished {opens / n:.0%}; calendar days (p25 / median / p75): phase 1 {q(p1)}, phase 2 {q(p2)}, to funded {q(total)}")


if __name__ == "__main__":
    main()
