# EURUSD, 1 August - 25 September 2026 with the live profile: watch the engine find the gap and the liquidity

Max, 4 October: "kunnen we nog een test doen met de huidige setup waarbij ik mee kan kijken of die goed de fair value
gaps zoekt in combinatie met liquiditeit zodat die precies goed instapt?" This folder is that test on the last weeks we
hold minute data for (HistData to 25 September): `config/dorus_live.yaml` exactly as the demo runs it (version 3),
replayed in 5-minute steps from 1 August, with a decision dossier written at every signal from the run's own engine
state (`backtest --dossier-dir`). Nothing here is tuned to the month; the profile was fixed on 2 October.

## How to watch along

For each signal below, open the same chart in TradingView or MT5 (times are UTC; Amsterdam is two hours later) and
check three things against the dossier (`dossiers/<date_time>/README.md`, one chart per timeframe with the zones
drawn as X / B / P):

1. **The zone (B).** On the zone's timeframe, is the three-candle gap at the B range the fair value gap you would draw,
   with the sweep X and the protector extreme P where the code puts them? The zone table in the dossier gives the
   formation time and every zone near price, the bias notes above it say which sweep or break set the bias.
2. **The liquidity (X).** Did price take X (the low or high the zone protects) before the entry, the way Dorus wants
   liquidity taken before a shift? X is marked on the chart and named in the table.
3. **The entry.** On the confirmation timeframe (15m for a 4H zone, 5m for a 1H zone, from the course's table one
   step up), is the candle at *shift* the balance shift you would enter on, and is the entry its close? Then the
   stop (the extreme since price entered the zone, 8 pips minimum) and the target (the origin low/high of the move
   that made the zone, or the next liquidity when that is nearer).

Write what differs per signal (zone, liquidity, candle, price) in the review column of the table, or send the chart
with a note; the fast loop (`scripts/source_trades.py`) turns each difference into a reading to test.

## The signals (4 trades, +2.5R; September 3 of 3, +3.5R)

| # | Signal (UTC) | Side | Zone | X | B (the gap) | P | Formed | Touched | Shift | Entry | Stop | Target (rule) | R:R | Result | Dossier | Chart | Review |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Mon 03 Aug 07:00 | LONG | 1H 1.14971-1.15261 | 1.15261 | 1.15063-1.15122 | 1.14971 | 31 Jul 18:00 | 31 Jul 19:46 | BS 5m 06:55 | 1.15370 | 1.15238 (5m low since the zone was entered) | 1.15587 (15m buy-side liquidity, nearer than the origin) | 1.53 | stop -1.00R, 07:45 | [dossier](dossiers/2026-08-03_0700/README.md) | [chart](charts/EURUSD_001_20260803_0700_5m.png) | entry 11 pips above the zone |
| 2 | Fri 11 Sep 08:15 | SHORT | 4H 1.16201-1.16403 | 1.16201 | 1.16315-1.16355 | 1.16403 | 10 Sep 13:00 | 10 Sep 17:00 | BS 15m 08:00 | 1.16079 | 1.16287 (15m high since the zone was entered) | 1.15847 (4H origin low) | 1.06 | take profit +1.12R, 13:30 | [dossier](dossiers/2026-09-11_0815/README.md) | [chart](charts/EURUSD_002_20260911_0815_15m.png) | |
| 3 | Mon 14 Sep 07:15 | SHORT | 4H 1.15980-1.16589 | 1.16364 | 1.15980-1.16392 | 1.16589 | 28 Aug 17:00 | 31 Aug 08:43 | BS 15m 07:00 | 1.15587 | 1.15986 (15m high since the zone was entered) | 1.15238 (4H sell-side liquidity) | 0.85 | take profit +0.87R, 16 Sep 19:00 | [dossier](dossiers/2026-09-14_0715/README.md) | [chart](charts/EURUSD_003_20260914_0715_15m.png) | entry 39 pips under the zone, two weeks after the touch: is that still his entry? |
| 4 | Tue 22 Sep 12:15 | SHORT | 4H 1.14736-1.15469 | 1.15270 | 1.14736-1.15278 | 1.15469 | 16 Sep 21:00 | 17 Sep 07:22 | BS 15m 12:00 | 1.14609 | 1.14781 (15m high since the zone was entered) | 1.14342 (4H sell-side liquidity) | 1.47 | take profit +1.55R, 16:35 | [dossier](dossiers/2026-09-22_1215/README.md) | [chart](charts/EURUSD_004_20260922_1215_15m.png) | |

Two more valid setups on 14 September were not traded because the 07:15 short was still open (one position at a
time): 08:45 from the 1H zone 1.15662-1.15816 (BS on 5m at 08:40, entry 1.15490, stop 1.15704, target 1.15238,
R:R 1.13, [dossier](dossiers/2026-09-14_0845/README.md)) and 13:30 from the 4H zone 1.15497-1.15706 (BS on 15m at
13:15, entry 1.15410, stop 1.15511, target 1.15342, R:R 0.61, [dossier](dossiers/2026-09-14_1330/README.md)). The
08:45 one is the tighter entry at a zone price was actually in; the 07:15 trade from the zone 39 pips above is the
open question "zone priority when a 4H and a 1H zone overlap" (`docs/WINRATE_DORUS_vs_CODE.md`).

The first trade shows the same thing on 3 August: the 5m shift closed 11 pips above the 1H zone and the stop at the
5m low was hit 45 minutes later. His entries sit at the zone's edge (suite readings C, D: 1.5-1.6 pips from his
price); a cap on how far outside the zone the shift may close is a reading to test once he says where his limit is.

## What is in the dossiers

Each `dossiers/<date_time>/` holds the moment the signal fired: `README.md` with the decision and its reason, the bias
per timeframe with the notes that made it (which sweep or break, which balance level), the zone table per timeframe
(low, high, X, B, P, formation time, status, visits), the balance levels kept and dropped by the size threshold, the
rejections of every other zone at that moment, and the setup; one chart per timeframe (`1m.png` to `1M.png`) with
the zones drawn. The `charts/` images come from `trade-charts` and draw the ledger's zone, stop and target on the
confirmation timeframe; their title flags a "replay mismatch" when a fresh engine without the run's memory maps the
zone differently, which is why the dossiers, not these, are the reference. `ledger_v3.csv` carries every field of
the four trades.

## Reproduce

```shell
python -m kronos_trader --config config/dorus_live.yaml backtest --symbol EURUSD --data-dir data/histdata_1m \
  --step-tf 5m --start 2026-08-01 --end 2026-09-25 --kronos off --quote-basis bid \
  --out ledger_v3.csv --dossier-dir dossiers --dossier-limit 40
python -m kronos_trader --config config/dorus_live.yaml trade-charts --symbol EURUSD --data-dir data/histdata_1m \
  --trades ledger_v3.csv --out charts --max 0
```
