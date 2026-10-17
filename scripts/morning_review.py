"""The morning Dorus review: the engine's view of each live market at one moment, laid out for a reviewer who reads it
the way Dorus would (docs/DORUS_REVIEW.md). Advice for Max: nothing here places, blocks or changes a trade.

  python scripts/morning_review.py build <dir> [<payload file> ...] [--no-btc]
      <dir>/cache: each saved ``mcp-tv-get-ohlcv`` payload (format rows or columns; the market and the timeframe are
      read from the payload, or given as SYMBOL:TF=<file>) for its market and timeframe, the
      weekly and monthly candles out of the daily ones, and BTCUSD from Bitstamp's public candles (the feed its profile
      was tested on). The candle still forming is left out.
  python scripts/morning_review.py dossiers <dir> [--warmup-days 2]
      per market a decision dossier at its last closed 5m candle (<dir>/<SYMBOL>/README.md, dossier.json, a chart per
      timeframe) with that market's live profile, and <dir>/summary.md: price, the decision, the bias per timeframe,
      the last breaks, the last day's move and path in average 1H ranges, the zones near price with their age, the
      setup if there is one, and the engine's refusals.

TradingView payloads: ask ``mcp-tv-get-ohlcv`` for OANDA:EURUSD, OANDA:XAUUSD and OANDA:NAS100USD with the counts in
``TV_REQUESTS`` and format=columns; answers that large are saved to a file by the session, whose path goes here.
Run from the repository root.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kronos_trader.core.candles import CandleSeries  # noqa: E402
from kronos_trader.core.timeframe import Timeframe  # noqa: E402
from kronos_trader.data.tradingview_mcp import parse_ohlcv_payload  # noqa: E402
from kronos_trader.data.tv_cache import save_series  # noqa: E402

PROFILES = {"EURUSD": "config/dorus_live.yaml", "XAUUSD": "config/dorus_live_gold.yaml",
            "NAS100": "config/dorus_live_nas100.yaml", "BTCUSD": "config/dorus_live_btc.yaml"}
TV_SYMBOLS = {"EURUSD": "OANDA:EURUSD", "XAUUSD": "OANDA:XAUUSD", "NAS100": "OANDA:NAS100USD"}
TV_REQUESTS = {"1D": 5000, "4h": 5000, "1h": 5000, "15m": 3000, "5m": 3000}     # interval -> count, per market
BTC_COUNTS = {Timeframe.MN_1: 70, Timeframe.W_1: 120, Timeframe.D_1: 400, Timeframe.H_4: 1000, Timeframe.H_1: 1000,
              Timeframe.MIN_15: 1000, Timeframe.MIN_5: 1000}
AGG = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
NEAR_DAILY_RANGES = 3.0          # zones whose near edge lies within this many average daily ranges of price


def closed_only(series: CandleSeries, now: pd.Timestamp) -> CandleSeries:
    """Leave out the candle still forming at ``now`` (TradingView and Bitstamp both send it)."""
    df = series.df
    end = pd.DatetimeIndex(df["timestamp"]) + pd.Timedelta(minutes=series.timeframe.minutes)
    return CandleSeries(df[end <= now].reset_index(drop=True), series.timeframe, series.symbol)


def from_sessions(daily: CandleSeries, timeframe: Timeframe, now: pd.Timestamp) -> CandleSeries:
    """Weekly and monthly candles out of TradingView's daily ones, each stamped at its session's open (17:00 New York):
    a week holds the sessions of one Monday-to-Friday trading week, a month those of one calendar month, each stamped
    at its first session's open. The week or month still running at ``now`` is left out."""
    df = daily.df.copy()
    day = (pd.DatetimeIndex(df["timestamp"]) + pd.Timedelta(hours=7)).normalize()      # 21:00/22:00 UTC -> trading date
    today = (now + pd.Timedelta(hours=7)).normalize()
    if timeframe is Timeframe.W_1:
        key, current = day - pd.to_timedelta(day.weekday, unit="D"), today - pd.Timedelta(days=today.weekday())
    else:
        key, current = day.to_period("M").to_timestamp(), today.to_period("M").to_timestamp()
    df["key"] = key
    out = df.groupby("key").agg({"timestamp": "first", **AGG})
    out = out[out.index < current].reset_index(drop=True)
    return CandleSeries(out[["timestamp", "open", "high", "low", "close", "volume"]], timeframe, daily.symbol)


def cmd_build(a) -> None:
    cache = Path(a.dir) / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    by_tv = {v: k for k, v in TV_SYMBOLS.items()}
    for spec in a.payloads:
        key, _, path = spec.rpartition("=")
        payload = json.loads(Path(path).read_text())
        if key:                                       # SYMBOL:TF=path
            symbol, _, label = key.partition(":")
        else:                                         # the payload names both
            symbol, label = by_tv.get(payload.get("symbol"), str(payload.get("symbol", ""))), str(payload.get("interval", ""))
        symbol, tf = symbol.upper(), Timeframe.parse(label.upper() if label[-1:] in "hd" else label)
        series = closed_only(parse_ohlcv_payload(payload, tf, symbol), now)
        save_series(series, cache, symbol, merge=False)
        print(f"{symbol} {tf.label}: {len(series)} candles to {series.df['timestamp'].iloc[-1]}")
        if tf is Timeframe.D_1:
            for htf in (Timeframe.W_1, Timeframe.MN_1):
                save_series(from_sessions(series, htf, now), cache, symbol, merge=False)
    if not a.no_btc:
        from kronos_trader.data.bitstamp import BitstampFeed
        feed = BitstampFeed()
        for tf, count in BTC_COUNTS.items():
            series = closed_only(feed.get_candles("BTCUSD", tf, count), now)
            save_series(series, cache, "BTCUSD", merge=False)
        print(f"BTCUSD: Bitstamp candles to {series.df['timestamp'].iloc[-1]}")


def day_path(cache: Path, symbol: str):
    """The last 24 closed 1H candles: the move from their open to the last close and the path it took, in average
    1H ranges, and how much of that path went anywhere (net move / sum of the hourly moves; low = going sideways)."""
    h = pd.read_csv(cache / f"{symbol}_1H.csv", parse_dates=["timestamp"]).tail(24)
    rng = float((h.high - h.low).mean())
    move = float(h.close.iloc[-1] - h.open.iloc[0])
    path = float(np.abs(np.diff(np.r_[h.open.iloc[0], h.close.values])).sum())
    span = float(h.high.max() - h.low.min())
    return {"move": move / rng if rng else 0.0, "efficiency": abs(move) / path if path else 0.0,
            "span": span / rng if rng else 0.0}


def summarize(symbol: str, folder: Path, cache: Path, touch_limit_h: float) -> str:
    d = json.loads((folder / "dossier.json").read_text())
    at, price = pd.Timestamp(d["at"]), float(d["price"])
    daily = pd.read_csv(cache / f"{symbol}_1D.csv", parse_dates=["timestamp"]).tail(14)
    adr = float((daily.high - daily.low).mean())
    p = day_path(cache, symbol)
    dec = d["decision"]
    out = [f"## {symbol}", "", f"At {at:%Y-%m-%d %H:%M} UTC, price {price:g}. Engine: **{dec['direction'].lower()}**, "
           f"{dec['mode']}: {dec['reason']}", "",
           f"Last 24 1H candles: moved {p['move']:+.1f} average 1H ranges, spanned {p['span']:.1f}, "
           f"efficiency {p['efficiency']:.2f} (near 0 = sideways, near 1 = one way). Average daily range {adr:g}.", "",
           "| TF | Bias | Liquidity | Balance | Last breaks |", "|---|---|---|---|---|"]
    for tf in ("1M", "1W", "1D", "4H", "1H"):
        v = d["timeframes"].get(tf)
        if not v:
            continue
        b = v.get("bias") or {}
        breaks = "; ".join(f"{x['kind']} {x['direction'].lower()} {x['level']:g} ({x['time'][5:16]})" for x in (v.get("breaks") or [])[-2:])
        out.append(f"| {tf} | {str(b.get('bias', '')).lower()} | {str(b.get('liquidity', '')).lower()} | "
                   f"{str(b.get('balance', '')).lower()} | {breaks} |")
    out += ["", "Bias notes: " + " / ".join(f"{tf}: " + "; ".join((d['timeframes'][tf].get('bias') or {}).get('notes', []))
                                             for tf in ("1D", "4H", "1H") if tf in d["timeframes"]), ""]
    near = []
    for tf in ("1W", "1D", "4H", "1H"):
        for z in (d["timeframes"].get(tf) or {}).get("zones") or []:
            if z.get("status") == "invalidated":
                continue
            lo, hi = float(z["low"]), float(z["high"])
            dist = 0.0 if lo <= price <= hi else min(abs(price - lo), abs(price - hi))
            if dist > NEAR_DAILY_RANGES * adr:
                continue
            formed = pd.Timestamp(z["formed"]) if z.get("formed") else None
            age = (at - formed) / pd.Timedelta(hours=1) if formed is not None else float("nan")
            kind = "demand" if z["direction"] == "BULLISH" else "supply"
            touch = (z.get("visit") or {}).get("touch")
            if touch and formed is not None:          # the visit under way: its start counts (max_touch_age_hours)
                waited = (pd.Timestamp(touch) - formed) / pd.Timedelta(hours=1)
                fresh = "yes" if waited <= touch_limit_h else f"no (touched {waited:.0f} h after it formed)"
            else:                                     # a later first touch would come at least this late
                fresh = "yes" if age <= touch_limit_h else f"no (formed {age:.0f} h ago)"
            near.append((dist, f"| {tf} {kind} | {lo:g} - {hi:g} | {dist / adr:.1f} | {z.get('status')} | "
                               f"{formed:%m-%d %H:%M} ({age:.0f} h) | {fresh} |"))
    out += ["Zones near price (within {:.0f} average daily ranges):".format(NEAR_DAILY_RANGES), "",
            "| Zone | Range | Distance (daily ranges) | Status | Formed (age) | Still tradable by age |", "|---|---|---|---|---|---|"]
    out += [row for _, row in sorted(near)[:12]] or ["| none | | | | | |"]
    s = d.get("setup")
    if s:
        out += ["", f"Setup: {s['direction']} {s.get('poi_tf')} zone {s.get('poi')}, {s.get('confirmation')} on "
                    f"{s.get('confirmation_tf')}, entry {s.get('entry')}, stop {s.get('stop')}, target {s.get('take_profit')} "
                    f"({s.get('tp_source')}), R:R {float(s.get('rr') or 0):.1f}"]
    out += ["", "Refusals:", ""] + [f"- {r}" for r in d.get("rejections", [])[:15]]
    for side in ("long", "short"):
        f = folder / f"assume_{side}" / "dossier.json"
        if f.exists():
            past = [r for r in json.loads(f.read_text()).get("rejections", [])     # the zones price is in, and the gates
                    if "no active visit" not in r and not r.startswith("diagnostic:")]
            out += ["", f"Walking on as a {side} past the bias, session and news gates (diagnostic, never a signal):", ""]
            out += [f"- {r}" for r in past[:15]] or ["- nothing refused"]
    out += ["", f"Charts: {folder}/1D.png, 4H.png, 1H.png, 15m.png, 5m.png; full notes in {folder}/README.md", ""]
    return "\n".join(out)


def cmd_dossiers(a) -> None:
    out, cache = Path(a.dir), Path(a.dir) / "cache"
    parts = [f"# Morning review data, {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC", ""]
    for symbol, profile in PROFILES.items():
        five = cache / f"{symbol}_5min.csv"
        if not five.exists():
            parts += [f"## {symbol}", "", "no candles", ""]
            continue
        at = pd.read_csv(five, parse_dates=["timestamp"]).timestamp.max() + pd.Timedelta(minutes=5)
        folder = out / symbol
        cmd = [sys.executable, "-m", "kronos_trader", "--config", profile, "decision-dossier", "--symbol", symbol,
               "--data-dir", str(cache), "--at", str(at), "--out", str(folder), "--warmup-days", str(a.warmup_days)]
        run = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if run.returncode != 0:
            parts += [f"## {symbol}", "", "dossier failed: " + (run.stderr or run.stdout)[-800:], ""]
            continue
        direction = json.loads((folder / "dossier.json").read_text())["decision"]["direction"]
        sides = {"BULLISH": ["long"], "BEARISH": ["short"]}.get(direction, ["long", "short"])
        for side in sides:                            # what the engine would refuse past the gates
            subprocess.run(cmd[:cmd.index("--out")] + ["--out", str(folder / f"assume_{side}"), "--warmup-days",
                                                        str(a.warmup_days), "--assume", side],
                           cwd=ROOT, capture_output=True, text=True)
        import yaml
        limit = float((yaml.safe_load((ROOT / profile).read_text()).get("confirmation") or {}).get("max_touch_age_hours") or 0) or float("inf")
        parts.append(summarize(symbol, folder, cache, limit))
    (out / "summary.md").write_text("\n".join(parts))
    print(f"summary written to {out / 'summary.md'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("dir")
    b.add_argument("payloads", nargs="*", help="a saved mcp-tv-get-ohlcv payload file (its symbol and interval are read from it), or SYMBOL:TF=path")
    b.add_argument("--no-btc", action="store_true")
    b.set_defaults(func=cmd_build)
    d = sub.add_parser("dossiers")
    d.add_argument("dir")
    d.add_argument("--warmup-days", type=float, default=2.0)
    d.set_defaults(func=cmd_dossiers)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
