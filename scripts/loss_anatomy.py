"""Loss anatomy of a ledger with the maximum excursion of every trade from the 5m bars: where do the losers go before
the stop, what separates them from the winners (zone timeframe, bias combination, hour, weekday, planned R:R, zone age,
wait between touch and shift), and what a break-even at +1R would have done.  Run from the repository root:

  PYTHONPATH=. python scripts/loss_anatomy.py <label> <ledger.csv> <5m bars.csv> <pip size> [out_dir]

Writes <out_dir>/anatomy_<label>.csv (the ledger plus mfe / mae in R) and prints the tables.
"""
import sys, pandas as pd, numpy as np
from zoneinfo import ZoneInfo
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
AMS = ZoneInfo("Europe/Amsterdam")

def load_bars(path):
    b = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp").sort_index()
    return b

def anatomy(label, ledger, bars_path, pip, out_dir="."):
    df = pd.read_csv(ledger)
    for c in ("opened_at", "closed_at", "touched_at", "confirmed_at", "poi_formed"):
        if c in df: df[c] = pd.to_datetime(df[c], errors="coerce")
    bars = load_bars(bars_path)
    mfe, mae = [], []
    for t in df.itertuples():
        w = bars.loc[t.opened_at: t.closed_at]
        risk = abs(t.entry - t.stop)
        if len(w) == 0 or risk == 0: mfe.append(np.nan); mae.append(np.nan); continue
        if t.direction == "LONG":
            mfe.append((w.high.max() - t.entry) / risk); mae.append((t.entry - w.low.min()) / risk)
        else:
            mfe.append((t.entry - w.low.min()) / risk); mae.append((w.high.max() - t.entry) / risk)
    df["mfe"] = mfe; df["mae"] = mae
    df["win"] = df.r > 0.05; df["loss"] = df.r < -0.05
    df["stop_pips"] = (df.entry - df.stop).abs() / pip
    df["hour"] = df.opened_at.dt.tz_localize("UTC").dt.tz_convert(AMS).dt.hour
    df["weekday"] = df.opened_at.dt.dayofweek
    df["wait_h"] = (df.confirmed_at - df.touched_at).dt.total_seconds() / 3600
    df["zone_age_h"] = (df.opened_at - df.poi_formed).dt.total_seconds() / 3600
    df["hold_h"] = (df.closed_at - df.opened_at).dt.total_seconds() / 3600
    L = df[df.loss]; W = df[df.win]
    print(f"\n===== {label}: {len(df)} trades, win {df.win.mean():.0%}, {df.r.sum():+.1f}R")
    print(f"losers: {len(L)}; of them reached +0.5R first: {(L.mfe >= 0.5).mean():.0%}, +1R: {(L.mfe >= 1).mean():.0%}, +2R: {(L.mfe >= 2).mean():.0%}; never beyond +0.25R: {(L.mfe < 0.25).mean():.0%}")
    print(f"winners: {len(W)}; max adverse before the target: median {W.mae.median():.2f}R, >0.5R adverse {(W.mae > 0.5).mean():.0%}, >0.8R {(W.mae > 0.8).mean():.0%}")
    print(f"planned R:R losers median {L.planned_rr.median():.2f} vs winners {W.planned_rr.median():.2f}; stop pips losers median {L.stop_pips.median():.1f} vs winners {W.stop_pips.median():.1f}")
    print(f"hold hours losers median {L.hold_h.median():.1f} vs winners {W.hold_h.median():.1f}; wait touch->shift losers {L.wait_h.median():.1f}h vs winners {W.wait_h.median():.1f}h; zone age losers {L.zone_age_h.median():.0f}h vs winners {W.zone_age_h.median():.0f}h")
    for col in ("poi_tf", "confirmation", "confirmation_tf", "bias_combo", "visit", "direction"):
        if col in df:
            g = df.groupby(col).agg(n=("r", "size"), win=("win", "mean"), sumR=("r", "sum")).round(2)
            print(f"by {col}:", g.to_dict("index"))
    g = df.groupby("hour").agg(n=("r", "size"), win=("win", "mean"), sumR=("r", "sum")).round(2); print("by hour (Amsterdam):", g.to_dict("index"))
    g = df.groupby("weekday").agg(n=("r", "size"), win=("win", "mean"), sumR=("r", "sum")).round(2); print("by weekday:", g.to_dict("index"))
    df["rr_bucket"] = pd.cut(df.planned_rr, [0, 1, 1.5, 2, 3, 5, 100]); print("by planned R:R:", df.groupby("rr_bucket", observed=True).agg(n=("r","size"), win=("win","mean"), sumR=("r","sum")).round(2).to_dict("index"))
    df["age_bucket"] = pd.cut(df.zone_age_h, [0, 24, 72, 168, 720, 1e6]); print("by zone age (h):", df.groupby("age_bucket", observed=True).agg(n=("r","size"), win=("win","mean"), sumR=("r","sum")).round(2).to_dict("index"))
    df["wait_bucket"] = pd.cut(df.wait_h, [-1, 1, 4, 12, 48, 1e6]); print("by wait touch->shift (h):", df.groupby("wait_bucket", observed=True).agg(n=("r","size"), win=("win","mean"), sumR=("r","sum")).round(2).to_dict("index"))
    # what a break-even at 1R would have done: losers that reached +1R become 0
    be1 = df.r.where(~((df.loss) & (df.mfe >= 1.0)), 0.0)
    print(f"if break-even at +1R (losers that saw +1R -> 0): win {(be1 > 0.05).mean():.0%}, loss share {(be1 < -0.05).mean():.0%}, sum {be1.sum():+.1f}R (winners untouched, optimistic)")
    df.to_csv(f"{out_dir}/anatomy_{label}.csv", index=False)


if __name__ == "__main__":
    label, ledger, bars, pip = sys.argv[1:5]
    anatomy(label, ledger, bars, float(pip), sys.argv[5] if len(sys.argv) > 5 else ".")
