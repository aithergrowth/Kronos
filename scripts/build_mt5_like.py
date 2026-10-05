"""Candles as an MT5 server on New York + 7 builds them, from HistData minutes (or 5-minute bars):
the weekend cut at Friday 17:00 to Sunday 17:00 New York (HistData's week ends at 17:00 EST all year, so in summer it
holds a Friday hour no such server has), 5m/15m/1H on the clock, 4H/1D/1W/1MO anchored at 17:00 New York, and the
daily, weekly and monthly bars of the source directory kept only before the first rebuilt one (the monthly and weekly
readings need years). Run from the repository root:

  python scripts/build_mt5_like.py <source dir> <out dir> EURUSD:EURUSD_1min.csv XAUUSD:XAUUSD_1min.csv GBPUSD:GBPUSD_5min.csv
"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kronos_trader.core.candles import CandleSeries  # noqa: E402
from kronos_trader.core.timeframe import Timeframe as T  # noqa: E402
from kronos_trader.data.resample import resample  # noqa: E402
from kronos_trader.data.dukascopy import anchored_resample  # noqa: E402
from kronos_trader.data.tv_cache import load_all  # noqa: E402

NAMES = {T.MIN_5: "5min", T.MIN_15: "15min", T.H_1: "1H", T.H_4: "4H", T.D_1: "1D", T.W_1: "1W", T.MN_1: "1MO"}
KEEP_BEFORE = {T.D_1: pd.Timedelta(days=1), T.W_1: pd.Timedelta(days=7), T.MN_1: pd.Timedelta(days=31)}


def build(source: Path, out: Path, sym: str, fname: str) -> None:
    df = pd.read_csv(source / fname, parse_dates=["timestamp"])
    tf = T.MIN_1 if "1min" in fname else T.MIN_5
    ny = pd.DatetimeIndex(df.timestamp).tz_localize("UTC").tz_convert("America/New_York")
    weekend = ((ny.weekday == 4) & (ny.hour >= 17)) | (ny.weekday == 5) | ((ny.weekday == 6) & (ny.hour < 17))
    base = CandleSeries(df.loc[~weekend].reset_index(drop=True), tf, sym)
    old = load_all(source, sym)
    for target, name in NAMES.items():
        bars = base if target == tf else resample(base, target) if target < T.H_4 else \
            anchored_resample(base, target, session_tz="America/New_York")
        frame = bars.df[["timestamp", "open", "high", "low", "close", "volume"]].dropna(subset=["timestamp"])
        if target in KEEP_BEFORE and target in old:
            first = frame.timestamp.iloc[0]
            past = old[target].df[old[target].df.timestamp < first - KEEP_BEFORE[target]]
            frame = pd.concat([past[frame.columns], frame]).sort_values("timestamp").drop_duplicates("timestamp")
        frame.to_csv(out / f"{sym}_{name}.csv", index=False)
        print(f"{sym} {name}: {len(frame)} rows {frame.timestamp.iloc[0]} .. {frame.timestamp.iloc[-1]}")


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    dst.mkdir(parents=True, exist_ok=True)
    for spec in sys.argv[3:]:
        sym, fname = spec.split(":", 1)
        build(src, dst, sym, fname)
