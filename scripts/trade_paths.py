"""Where the trades of a ledger go: how far each went our way before its exit (MFE) and against (MAE), whether the price
moved our way at all (+4 h / +24 h / +72 h from the fill, in R), what a stopped trade's price did next (the target
reached within 72 h), and what other exits and stops would have made, walking the 5m bars from the fill.

The walk follows the paper broker: bid bars, a short's stop and target on the ask (bid + the spread), the stop first
when stop and target sit in one bar, a stop move (break-even, lock) taking effect from the next bar, still open after
10 days -> the last close. Exit variants keep the trade's stop and target; stop variants move the stop (x m of the
distance, the same target) and count R in the new risk (the size shrinks to keep the cash at risk). Trade
interactions (one trade per market, the next signal) are left out: a screen, not a backtest. Run from the repository
root:

  python scripts/trade_paths.py <label> <ledger.csv> <5m bars.csv> <spread in price> [--csv out.csv]
"""
import argparse
import numpy as np
import pandas as pd

SWING_POI = ("1W", "1M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label"); ap.add_argument("ledger"); ap.add_argument("bars"); ap.add_argument("spread", type=float)
    ap.add_argument("--csv")
    a = ap.parse_args()
    t = pd.read_csv(a.ledger, parse_dates=["opened_at", "closed_at"])
    b = pd.read_csv(a.bars, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    idx, hi, lo, cl = b.index, b.high.values, b.low.values, b.close.values
    sp = a.spread

    def walk(i0, i_end, long, entry, stop, target, be_at=0.0, locks=()):
        """R of one trade: stop/target on the bars from i0, a break-even at be_at R and (trigger R, lock R) steps."""
        risk = abs(entry - stop)
        cur = stop
        for i in range(i0, i_end):
            if long:
                if lo[i] <= cur:
                    return (cur - entry) / risk
                if hi[i] >= target:
                    return (target - entry) / risk
                fav = (hi[i] - entry) / risk
            else:
                if hi[i] + sp >= cur:
                    return (entry - cur) / risk
                if lo[i] + sp <= target:
                    return (entry - target) / risk
                fav = (entry - (lo[i] + sp)) / risk
            moved = cur
            if be_at and fav >= be_at:
                moved = max(moved, entry) if long else min(moved, entry)
            for trig, lock in locks:
                if fav >= trig:
                    level = entry + lock * risk if long else entry - lock * risk
                    moved = max(moved, level) if long else min(moved, level)
            cur = moved
        last = cl[i_end - 1] + (0 if long else sp)
        return (last - entry) / risk if long else (entry - last) / risk

    rows = []
    for r in t.itertuples():
        long = r.direction == "LONG"
        sgn = 1.0 if long else -1.0
        risk = abs(r.entry - r.stop)
        if risk <= 0:
            continue
        i0 = idx.searchsorted(r.opened_at)
        i_end = min(len(idx), idx.searchsorted(r.opened_at + pd.Timedelta(days=10)))
        i_exit = min(len(idx), max(i0 + 1, idx.searchsorted(r.closed_at) + 1))
        if i0 >= i_end:
            continue
        be = 2.0 if str(r.poi_tf) in SWING_POI else 4.0
        # excursions up to the exit, our side: a long sells at the bid, a short buys at the ask
        h, l = hi[i0:i_exit], lo[i0:i_exit]
        fav = ((h.max() - r.entry) if long else (r.entry - (l.min() + sp))) / risk
        adv = ((r.entry - l.min()) if long else ((h.max() + sp) - r.entry)) / risk
        row = {"opened_at": r.opened_at, "direction": r.direction, "r": r.r, "reason": r.reason, "poi_tf": r.poi_tf,
               "planned_rr": abs(r.take_profit - r.entry) / risk, "mfe": fav, "mae": adv}
        for hours in (4, 24, 72):
            j = min(len(idx) - 1, idx.searchsorted(r.opened_at + pd.Timedelta(hours=hours)))
            row[f"move{hours}h"] = sgn * (cl[j] - r.entry) / risk
        if r.reason == "stop":
            j_end = min(len(idx), idx.searchsorted(r.closed_at + pd.Timedelta(hours=72)))
            seg_h, seg_l = hi[i_exit:j_end], lo[i_exit:j_end]
            reached = (seg_h >= r.take_profit).any() if long else ((seg_l + sp) <= r.take_profit).any()
            row["tp_after_stop"] = bool(len(seg_h) and reached)
        row["sim"] = walk(i0, i_end, long, r.entry, r.stop, r.take_profit, be_at=be)
        for k in (1.0, 1.5, 2.0, 3.0):
            row[f"be{k:g}"] = walk(i0, i_end, long, r.entry, r.stop, r.take_profit, be_at=k)
        row["lock1at2"] = walk(i0, i_end, long, r.entry, r.stop, r.take_profit, be_at=be, locks=((2.0, 1.0),))
        row["trail"] = walk(i0, i_end, long, r.entry, r.stop, r.take_profit, be_at=1.5, locks=((2.5, 1.0), (3.5, 2.0), (4.5, 3.0)))
        for m in (0.75, 1.25, 1.5, 2.0):
            wide = r.entry - sgn * m * risk
            row[f"stop{m:g}x"] = walk(i0, i_end, long, r.entry, wide, r.take_profit, be_at=be)
        rows.append(row)
    d = pd.DataFrame(rows)
    if a.csv:
        d.to_csv(a.csv, index=False)
    losers, winners = d[d.r < -0.05], d[d.r > 0.05]
    stopped = d[d.reason == "stop"]
    print(f"== {a.label}: {len(d)} trades, {len(winners)} won, {len(losers)} lost, ledger {d.r.sum():+.1f}R, walk {d.sim.sum():+.1f}R")
    print(f"   losers that went our way first: >=0.5R {100 * (losers.mfe >= 0.5).mean():.0f} %, >=1R {100 * (losers.mfe >= 1).mean():.0f} %, "
          f">=2R {100 * (losers.mfe >= 2).mean():.0f} %; never 0.25R {100 * (losers.mfe < 0.25).mean():.0f} %")
    print(f"   winners' adverse excursion: median {winners.mae.median():.2f}R, past 0.5R {100 * (winners.mae > 0.5).mean():.0f} %, "
          f"past 0.75R {100 * (winners.mae > 0.75).mean():.0f} %")
    if len(stopped):
        print(f"   stopped trades whose target was reached within 72 h after the stop: {100 * stopped.tp_after_stop.mean():.0f} % "
              f"({int(stopped.tp_after_stop.sum())} of {len(stopped)})")
    for hours in (4, 24, 72):
        col = d[f"move{hours}h"]
        print(f"   price from the fill after {hours:>2} h: our way in {100 * (col > 0).mean():.0f} %, median {col.median():+.2f}R, "
              f"mean {col.clip(-5, 5).mean():+.2f}R (clipped at 5R)")
    cols = ["sim", "be1", "be1.5", "be2", "be3", "lock1at2", "trail", "stop0.75x", "stop1.25x", "stop1.5x", "stop2x"]
    yr = d.opened_at.dt.year
    out = []
    for c in cols:
        x = d[c]
        eq = x.cumsum()
        rec = {"exit": c, "win%": round(100 * (x > 0.05).mean()), "R": round(x.sum(), 1),
               "dd": round((eq - eq.cummax().clip(lower=0)).min(), 1)}
        for y, g in x.groupby(yr):
            rec[str(y)] = round(g.sum(), 1)
        out.append(rec)
    print(pd.DataFrame(out).to_string(index=False))


if __name__ == "__main__":
    main()
