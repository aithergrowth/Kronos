"""The FTMO challenge and the funded account on a portfolio of trade ledgers, with risk rules that change the stake only:
a base risk % and drawdown steps (level % from the start, risk %). The ledgers are combined first come, first served under an
account-wide cap (scripts/portfolio.py); a trade's stake comes from the balance realised before it opened.

Challenge: phase 1 +10 %, phase 2 +5 %, each at least 4 trading days; failed at -10 % static or a -5 % day (closed trades);
every calendar day in [first, last] is a start. Funded: every 7th day in [funded-first, funded-last] is a start; at each
month end a positive balance is paid out (split) and the balance goes back to the start; lost at -10 % static or a -5 % day.
--haircut subtracts that many R from every trade (live worse than the backtest). Run from the repository root:

  python scripts/risk_steps.py EURUSD=<ledger> XAUUSD=<ledger> GBPUSD=<ledger> NAS100=<ledger> BTCUSD=<ledger> \
      --risk 1.5 --steps=-3:1.0,-6:0.5 --funded-risk 1.0 --funded-steps=-3:0.5 --haircut 0.15
"""
import argparse, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from portfolio import combine  # noqa: E402


def parse_steps(text):
    return tuple(tuple(float(x) for x in part.split(":")) for part in text.split(",") if part) if text else ()


class Book:
    def __init__(self, trades, haircut=0.0):
        t = trades.sort_values("closed_at").reset_index(drop=True)
        self.open, self.close, self.r = t.opened_at.values, t.closed_at.values, t.r.values - haircut

    def walk(self, start, end=None):
        """Trades opened in [start, end), in close order."""
        keep = (self.open >= np.datetime64(start)) & ((self.open < np.datetime64(end)) if end is not None else True)
        return [i for i in np.flatnonzero(keep)]


def stake(base, steps, balance):
    risk = base
    for level, r in steps:
        if balance <= level:
            risk = min(risk, r)
    return risk


def phase(book, start, target, base, steps, min_days=4, max_loss=10.0, daily=5.0):
    bal, days, day_pnl, realised = 0.0, set(), {}, []
    for i in book.walk(start):
        o = book.open[i]
        pnl = book.r[i] * stake(base, steps, sum(p for c, p in realised if c <= o))
        realised.append((book.close[i], pnl)); bal += pnl
        d = pd.Timestamp(book.close[i]).normalize()
        day_pnl[d] = day_pnl.get(d, 0.0) + pnl
        days.add(pd.Timestamp(o).normalize())
        if day_pnl[d] <= -daily or bal <= -max_loss:
            return "fail", book.close[i]
        if bal >= target and len(days) >= min_days:
            return "pass", book.close[i]
    return "open", None


def challenge(book, base, steps, first, last):
    starts = pd.date_range(first, last, freq="D")
    funded, failed, days = 0, 0, []
    for st in starts:
        r1, e1 = phase(book, st, 10.0, base, steps)
        if r1 != "pass":
            failed += r1 == "fail"; continue
        r2, e2 = phase(book, pd.Timestamp(e1), 5.0, base, steps)
        if r2 == "pass":
            funded += 1; days.append((pd.Timestamp(e2) - st).days)
        else:
            failed += r2 == "fail"
    q = f"{np.percentile(days, 25):.0f} / {np.median(days):.0f} / {np.percentile(days, 75):.0f}" if days else "-"
    return funded / len(starts), failed / len(starts), q


def funded_account(book, base, steps, first, last, months=12, split=0.8):
    lost, paid = 0, []
    starts = pd.date_range(first, last, freq="7D")
    for st in starts:
        end = st + pd.DateOffset(months=months)
        bal, total, day_pnl, realised, dead = 0.0, 0.0, {}, [], False
        month_end = st + pd.DateOffset(months=1)
        for i in book.walk(st, end):
            c = pd.Timestamp(book.close[i])
            while c >= month_end and month_end <= end:
                if bal > 0:
                    total += split * bal; bal = 0.0; realised = []
                month_end += pd.DateOffset(months=1)
            pnl = book.r[i] * stake(base, steps, sum(p for cc, p in realised if cc <= book.open[i]))
            realised.append((book.close[i], pnl)); bal += pnl
            d = c.normalize(); day_pnl[d] = day_pnl.get(d, 0.0) + pnl
            if day_pnl[d] <= -5.0 or bal <= -10.0:
                dead = True; break
        if not dead and bal > 0:
            total += split * bal
        lost += dead; paid.append(total / months)
    return lost / len(starts), float(np.mean(paid))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledgers", nargs="+", help="SYMBOL=path to a trade list CSV (backtest --out)")
    ap.add_argument("--max-open", type=int, default=2)
    ap.add_argument("--risk", type=float, default=1.5); ap.add_argument("--steps", default="")
    ap.add_argument("--funded-risk", type=float, default=1.0); ap.add_argument("--funded-steps", default="")
    ap.add_argument("--haircut", type=float, default=0.0, help="R subtracted from every trade")
    ap.add_argument("--first", default="2024-02-01"); ap.add_argument("--last", default="2026-03-31")
    ap.add_argument("--funded-first", default="2024-02-01"); ap.add_argument("--funded-last", default="2025-09-30")
    ap.add_argument("--ledger-from", default="2024-02-01"); ap.add_argument("--ledger-to", default="2026-09-25")
    a = ap.parse_args()
    _, kept = combine(dict(x.split("=", 1) for x in a.ledgers), a.max_open, lo=a.ledger_from, hi=a.ledger_to)
    book = Book(kept, a.haircut)
    f, x, q = challenge(book, a.risk, parse_steps(a.steps), a.first, a.last)
    lost, pay = funded_account(book, a.funded_risk, parse_steps(a.funded_steps), a.funded_first, a.funded_last)
    print(f"{len(kept)} trades, mean {book.r.mean():+.2f}R (haircut {a.haircut:g}R)")
    print(f"challenge at {a.risk:g} % steps {a.steps or '-'}: funded {f:.0%}, failed {x:.0%}, days to funded p25 / median / p75 {q}")
    print(f"funded at {a.funded_risk:g} % steps {a.funded_steps or '-'}: lost within 12 months {lost:.0%}, payout {pay:.1f} % of the account a month")


if __name__ == "__main__":
    main()
