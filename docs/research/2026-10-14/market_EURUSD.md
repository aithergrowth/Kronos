# EURUSD: what has not been tested, with the evidence (14 October 2026)

Ledgers of the live profile as it ran on 12 October (`config/dorus_live.yaml`: two positions, limit 25 % back toward the
stop for 4 hours, 1D+1H pair, weekly and 4H veto, 24 h touch rule): in-sample `S/aca/eutwo_EURUSD.csv` (47 trades,
February 2024 - August 2026) and out-of-sample `S/aca/oos_eutwo_EURUSD.csv` (97 trades, April 2017 - December 2023).
Candles `S/fixed/EURUSD_*.csv` (UTC). Costs 0.10R a trade. Hours are Amsterdam. Scripts and outputs in `S/research/`
(`eurusd_research.py` anatomy / exits / fills / structure, `eurusd_candidates.py`, `eurusd_tables.py`; `*.out`, `eurusd_*.csv`).

**Base:** IS 47 trades, 47 % won, +0.84R a trade, +39.5R. OOS 97 trades, 26 %, -0.01R a trade, -1.2R.

**Method.** Every cut shows trades, win rate, R a trade and sum in both periods. A cut "holds" when its R a trade sits on
the same side of the base in both periods by more than 0.05R (a removal needs 3 trades or more in each period). The
candidates were then checked per calendar year (10 years), for sensitivity to their parameter, and stacked. The exit
and fill questions were simulated on the 5m candles: the plain simulation (stop before target in a candle, break-even
at 4R) reproduces all 144 ledger R's exactly, so the variants are comparable.

## The candidates in one table

| # | Rule | Knob / code | IS (base 47 tr, 47 %, +0.84, +39.5R) | OOS (base 97 tr, 26 %, -0.01, -1.2R) | Years better / worse | Code |
|---|---|---|---|---|---|---|
| 1 | No signal 14:30-16:00 (US data and NYSE open): windows 09-11, 13-14:30, 16-17 | `session.windows` | 36 tr, 56 %, +1.26, +45.3R | 82 tr, 26 %, +0.05, +3.9R | 6 / 3 | no |
| 2 | Session from 10:00 (no signal in the first London hour) | `session.windows` | 38 tr, 50 %, +1.00, +37.9R | 72 tr, 26 %, +0.05, +3.6R | 7 / 3 | no |
| 1+2 | both: windows 10-11, 13-14:30, 16-17 | `session.windows` | 27 tr, 63 %, +1.61, +43.6R | 57 tr, 26 %, +0.15, +8.8R | 8 / 2 | no |
| 3 | No entry while the entry price lies inside the day's Asia range (00:00-08:00 high-low) | new filter | 27 tr, 63 %, +1.25, +33.6R | 43 tr, 28 %, +0.20, +8.6R | 6 / 4 | yes |
| 3' | the same for shorts only | new filter | 42 tr, 52 %, +1.07, +45.0R | 67 tr, 31 %, +0.27, +18.2R | 8 / 1 | yes |
| 4 | No trade against the 60-trading-day daily return | new bias gate | 37 tr, 49 %, +1.02, +37.9R | 82 tr, 30 %, +0.17, +14.3R | 7 / 1 | yes |
| 5 | Stop at least 0.5 x the 1H ATR14 (skip the trade; the widen variant below) | `risk.min_stop_atr` | 42 tr, 50 %, +1.00, +41.8R | 82 tr, 29 %, +0.13, +10.6R | 6 / 1 | yes |
| 6 | The 1D+1H pair needs a third aligned timeframe | `bias.min_matching_timeframes: 3` | 40 tr, 50 %, +0.96, +38.5R | 80 tr, 28 %, +0.11, +8.6R | 5 / 3 | no |
| 7 | No entry on an NFP day | news day-blackout | 42 tr, 48 %, +0.92, +38.4R | 93 tr, 27 %, +0.03, +3.2R | 4 / 2 | yes (small) |
| 8 | Zone touched within 12 h of forming (24 now) | `confirmation.max_touch_age_hours: 12` | 43 tr, 49 %, +0.92, +39.6R | 90 tr, 27 %, +0.04, +3.4R | 6 / 2 | no |

Every exit variant (break-even at 1-2R, a 15m-swing trailing stop, time stops) lost in both periods, and every limit
fraction other than 25 % lost win rate in both periods and R out of sample: those are settled below, not candidates.

## 1. Loss anatomy

What separates the losers from the winners, both periods (medians):

| | IS winners | IS losers | OOS winners | OOS losers |
|---|---|---|---|---|
| Time in the trade | 2.9 h (q25 0.8, q75 10.1) | 0.5 h (0.2, 1.6) | 4.0 h (0.6, 18.0) | 0.3 h (0.0, 1.2) |
| Stop size | 10.0 pips | 6.8 pips | 8.9 pips | 7.4 pips |
| Stop / 1H ATR14 | 0.68 | 0.90 | 0.74 | 0.70 |
| Entry depth in the zone (negative = outside) | -0.12 | -0.09 | -0.13 | -0.03 |
| Target distance | 32 pips | 32 pips | 26 pips | 27 pips |

The losers die within the hour (IS 22 of 47 trades closed inside an hour at -1.2R together; OOS 55 of 97 at -32.0R); the
winners take hours. Depth and target distance separate nothing. The stop size separates only through the ratio to the
hourly range: a stop under half the 1H ATR14 won 1 of 20 (table below).

**Cuts that hold in both periods** (the rest of the tables are below, every cut, for the record):

- Signal 09:30-10:00: IS 6 trades 33 % -0.08R; OOS 15, 20 %, -0.43R. The whole first hour by fill time: IS 6, 17 %,
  -0.19R; OOS 19, 21 %, -0.27R. 76-89 % of these zones were touched before 09:00 and confirmed in the first hour after
  the London open.
- Signal 14:30-16:00 (three half-hour slots, each negative in both periods): IS 11, 18 %, -0.52R a trade; OOS 15, 27 %,
  -0.34R. Fill 15:00-16:00: IS 8, 38 %, +0.30R; OOS 8, 12 %, -0.73R.
- Direction against the 60-day daily return: IS 10, 40 %, +0.17R; OOS 15, 0 %, -1.03R.
- The bare 1D+1H alignment (4H, week and month all 50/50): IS 7, 29 %, +0.15R; OOS 17, 18 %, -0.58R.
- Stop under 0.5 x the 1H ATR14: IS 5, 20 %, -0.46R; OOS 15, 7 %, -0.79R.
- Entry inside the Asia range: IS 20, 25 %, +0.30R; OOS 54, 24 %, -0.18R (the shorts: IS 5, 0 %; OOS 30, 13 %, -0.65R).
- Fill within 5 minutes of the signal: IS 19, 42 %, +0.51R; OOS 42, 17 %, -0.21R; a fill 15-30 minutes after the signal
  IS 6, 67 %, +1.86R; OOS 16, 56 %, +1.01R. Not reproducible as a rule (section 4).
- NFP day: IS 5, 40 %, +0.22R; OOS 4, 0 %. US CPI day the other way (IS 3, +2.86R; OOS 8, +0.98R). FOMC mixed.
- Touch to signal under 1 h: IS 18, 50 %, +0.76R (just under the base); OOS 31, 16 %, -0.55R. Zone age 12-24 h at the
  touch: IS 3, +0.36R; OOS 6, 0 %.
- Direction: longs better in both (IS +1.09 vs +0.53; OOS +0.39 vs -0.33), but the 4 October anatomy on the older
  profile (2023-2026) had the shorts ahead (59 % vs 43 %): unstable across profile versions, not a rule on its own.
- Weekday: nothing holds (Friday best in both, Monday worst in IS only). Month: March and August worse in both
  (5-9 trades), December worse in OOS (15 trades, IS none): thin, noted.
- Planned R:R, stop pips, stop / zone height, target pips, entry depth: non-monotonic bands (a bad band between two
  good ones), read as noise.
- 4H zones: IS 10, 40 %, +0.43R; OOS 10, 80 %, +3.12R (mixed, the double stake already chosen). Second visits: IS 3,
  +0.8R; OOS 7, -4.5R (mixed).

### The tables

Base (0.10R costs): IS 47 trades, 47 %, +0.84 R/trade, +39.5R; OOS 97 trades, 26 %, -0.01 R/trade, -1.2R. 'both' = the cut's R/trade is better (worse) than the base by more than 0.05R in BOTH periods (WORSE needs 3+ trades in each).

**Hour of the fill (Amsterdam)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 6 | 17 % | -0.19 | -1.1 | 19 | 21 % | -0.27 | -5.1 | WORSE |
| 10 | 5 | 60 % | +0.72 | +3.6 | 20 | 30 % | +0.12 | +2.4 |  |
| 11 | 2 | 50 % | +0.96 | +1.9 | 6 | 17 % | -0.41 | -2.5 |  |
| 13 | 4 | 0 % | -0.85 | -3.4 | 13 | 54 % | +0.99 | +12.8 |  |
| 14 | 7 | 43 % | +1.34 | +9.4 | 13 | 23 % | +0.57 | +7.4 | better |
| 15 | 8 | 38 % | +0.30 | +2.4 | 8 | 12 % | -0.73 | -5.8 | WORSE |
| 16 | 11 | 73 % | +1.53 | +16.8 | 11 | 18 % | -0.59 | -6.4 |  |
| 17 | 4 | 75 % | +2.48 | +9.9 | 5 | 0 % | -0.90 | -4.5 |  |
| 18 |  |  |  |  | 1 | 100 % | +1.63 | +1.6 |  |
| 19 |  |  |  |  | 1 | 0 % | -1.10 | -1.1 |  |

**Time of the signal (the session knob acts here), half hours**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [9.0, 9.5) | 3 | 33 % | +0.72 | +2.2 | 10 | 30 % | +0.16 | +1.6 |  |
| [9.5, 10.0) | 6 | 33 % | -0.08 | -0.5 | 15 | 20 % | -0.43 | -6.4 | WORSE |
| [10.0, 11.0) | 4 | 50 % | +0.69 | +2.7 | 20 | 25 % | -0.02 | -0.3 |  |
| [13.0, 13.5) | 5 | 40 % | +0.66 | +3.3 | 12 | 58 % | +1.21 | +14.5 |  |
| [13.5, 14.0) | 2 | 0 % | -1.10 | -2.2 | 6 | 17 % | -0.64 | -3.9 |  |
| [14.0, 14.5) | 3 | 67 % | +3.60 | +10.8 | 8 | 25 % | +1.19 | +9.5 | better |
| [14.5, 15.0) | 4 | 0 % | -1.10 | -4.4 | 3 | 33 % | -0.19 | -0.6 | WORSE |
| [15.0, 15.5) | 6 | 33 % | -0.04 | -0.2 | 5 | 20 % | -0.51 | -2.5 | WORSE |
| [15.5, 16.0) | 1 | 0 % | -1.10 | -1.1 | 7 | 29 % | -0.29 | -2.0 |  |
| [16.0, 16.5) | 6 | 83 % | +2.20 | +13.2 | 4 | 0 % | -0.85 | -3.4 |  |
| [16.5, 17.01) | 7 | 86 % | +2.25 | +15.7 | 7 | 0 % | -1.10 | -7.7 |  |

**Weekday of the fill (0 = Monday)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 9 | 22 % | -0.35 | -3.1 | 15 | 33 % | -0.05 | -0.7 |  |
| 1 | 6 | 67 % | +1.24 | +7.4 | 20 | 20 % | -0.40 | -8.0 |  |
| 2 | 12 | 58 % | +2.07 | +24.8 | 22 | 23 % | -0.05 | -1.1 |  |
| 3 | 12 | 42 % | +0.24 | +2.8 | 20 | 30 % | -0.00 | -0.1 |  |
| 4 | 8 | 50 % | +0.95 | +7.6 | 20 | 25 % | +0.43 | +8.6 | better |

**Month of the fill**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 100 % | +2.24 | +4.5 | 6 | 50 % | +1.05 | +6.3 | better |
| 2 | 2 | 0 % | -1.10 | -2.2 | 5 | 20 % | +0.04 | +0.2 |  |
| 3 | 5 | 20 % | +0.16 | +0.8 | 8 | 12 % | -0.64 | -5.1 | WORSE |
| 4 | 8 | 50 % | +0.65 | +5.2 | 14 | 43 % | +0.66 | +9.3 |  |
| 5 | 3 | 67 % | +2.05 | +6.2 | 9 | 44 % | +0.45 | +4.1 | better |
| 6 | 7 | 43 % | +1.46 | +10.2 | 10 | 20 % | +0.74 | +7.4 | better |
| 7 | 1 | 0 % | -1.10 | -1.1 | 6 | 33 % | -0.07 | -0.4 |  |
| 8 | 8 | 38 % | +0.45 | +3.6 | 9 | 0 % | -1.10 | -9.9 | WORSE |
| 9 | 5 | 80 % | +1.89 | +9.5 | 6 | 17 % | -0.56 | -3.4 |  |
| 10 | 5 | 40 % | +0.09 | +0.4 | 2 | 0 % | -1.10 | -2.2 |  |
| 11 | 1 | 100 % | +2.43 | +2.4 | 7 | 43 % | +0.48 | +3.4 | better |
| 12 |  |  |  |  | 15 | 13 % | -0.72 | -10.8 |  |

**Bias combination**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 1D+1H | 34 | 41 % | +0.53 | +18.0 | 65 | 23 % | -0.09 | -6.0 | WORSE |
| 1M+1D+1H | 9 | 56 % | +1.04 | +9.4 | 10 | 30 % | +0.32 | +3.2 | better |
| 1M+1W+1D | 4 | 75 % | +3.04 | +12.2 | 22 | 32 % | +0.07 | +1.5 | better |

**Timeframes aligned at the signal**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 1D+1H | 7 | 29 % | +0.15 | +1.1 | 17 | 18 % | -0.58 | -9.9 | WORSE |
| 1D+4H+1H | 9 | 67 % | +1.13 | +10.2 | 12 | 8 % | -0.71 | -8.5 |  |
| 1M+1D+1H | 4 | 50 % | +1.11 | +4.4 | 5 | 40 % | +0.45 | +2.3 | better |
| 1M+1D+4H+1H | 5 | 60 % | +0.98 | +4.9 | 5 | 20 % | +0.18 | +0.9 | better |
| 1M+1W+1D+1H | 1 | 100 % | +8.17 | +8.2 | 6 | 0 % | -1.10 | -6.6 |  |
| 1M+1W+1D+4H+1H | 3 | 67 % | +1.33 | +4.0 | 16 | 44 % | +0.51 | +8.1 | better |
| 1W+1D+1H | 9 | 44 % | +1.05 | +9.5 | 21 | 29 % | +0.57 | +12.0 | better |
| 1W+1D+4H+1H | 9 | 22 % | -0.30 | -2.7 | 15 | 33 % | +0.03 | +0.4 |  |

**Zone timeframe**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 1H | 37 | 49 % | +0.95 | +35.3 | 87 | 20 % | -0.37 | -32.4 |  |
| 4H | 10 | 40 % | +0.43 | +4.3 | 10 | 80 % | +3.12 | +31.2 |  |

**Direction**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| LONG | 26 | 50 % | +1.09 | +28.4 | 43 | 33 % | +0.39 | +16.7 | better |
| SHORT | 21 | 43 % | +0.53 | +11.1 | 54 | 20 % | -0.33 | -17.9 | WORSE |

**Visit number**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 44 | 48 % | +0.88 | +38.7 | 90 | 27 % | +0.04 | +3.2 |  |
| 2 | 2 | 50 % | +0.96 | +1.9 | 6 | 17 % | -0.56 | -3.4 |  |
| 3 | 1 | 0 % | -1.10 | -1.1 | 1 | 0 % | -1.10 | -1.1 |  |

**Planned R:R**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0.0, 1.5) | 12 | 67 % | +0.92 | +11.1 | 34 | 41 % | +0.12 | +4.2 | better |
| [1.5, 2.0) | 9 | 67 % | +1.30 | +11.7 | 16 | 25 % | -0.23 | -3.7 |  |
| [2.0, 3.0) | 11 | 36 % | +0.50 | +5.5 | 20 | 15 % | -0.44 | -8.8 | WORSE |
| [3.0, 5.0) | 11 | 27 % | +0.49 | +5.4 | 19 | 16 % | -0.01 | -0.2 |  |
| [5.0, 100.0) | 4 | 25 % | +1.47 | +5.9 | 8 | 12 % | +0.91 | +7.3 | better |

**Stop size (pips)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0, 10) | 28 | 39 % | +0.64 | +17.9 | 70 | 24 % | +0.01 | +0.4 |  |
| [10, 12) | 2 | 100 % | +4.20 | +8.4 | 6 | 17 % | -0.32 | -1.9 |  |
| [12, 15) | 4 | 50 % | +0.45 | +1.8 | 9 | 11 % | -0.77 | -6.9 | WORSE |
| [15, 20) | 8 | 62 % | +1.00 | +8.0 | 5 | 60 % | +1.07 | +5.3 | better |
| [20, 30) | 2 | 50 % | +0.96 | +1.9 | 3 | 67 % | +0.86 | +2.6 | better |
| [30, 1000) | 3 | 33 % | +0.52 | +1.5 | 4 | 25 % | -0.17 | -0.7 | WORSE |

**Stop / 1H ATR14 at the entry**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0.0, 0.5) | 5 | 20 % | -0.46 | -2.3 | 15 | 7 % | -0.79 | -11.8 | WORSE |
| [0.5, 0.75) | 19 | 63 % | +1.79 | +34.0 | 40 | 32 % | +0.12 | +4.7 | better |
| [0.75, 1.0) | 7 | 14 % | -0.68 | -4.8 | 21 | 19 % | -0.29 | -6.2 | WORSE |
| [1.0, 1.5) | 9 | 33 % | +0.27 | +2.5 | 12 | 25 % | +0.72 | +8.6 |  |
| [1.5, 2.0) | 2 | 50 % | +0.71 | +1.4 | 3 | 33 % | +0.15 | +0.5 |  |
| [2.0, 100.0) | 5 | 80 % | +1.75 | +8.8 | 6 | 50 % | +0.50 | +3.0 | better |

**1H ATR14 at the entry (pips)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [5, 7) | 6 | 17 % | -0.19 | -1.1 | 8 | 25 % | -0.20 | -1.6 | WORSE |
| [7, 9) | 8 | 62 % | +0.99 | +7.9 | 14 | 29 % | +0.83 | +11.6 | better |
| [9, 12) | 13 | 46 % | +0.71 | +9.2 | 27 | 30 % | -0.04 | -1.0 |  |
| [12, 100) | 20 | 50 % | +1.18 | +23.5 | 48 | 23 % | -0.21 | -10.2 |  |

**Entry depth in the zone (fraction of the zone height; negative = outside the zone)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [-10.0, -0.25) | 14 | 57 % | +1.22 | +17.1 | 29 | 28 % | +0.33 | +9.5 | better |
| [-0.25, 0.0) | 15 | 40 % | +0.31 | +4.7 | 31 | 39 % | +0.40 | +12.4 |  |
| [0.0, 0.25) | 11 | 36 % | +0.49 | +5.4 | 18 | 6 % | -0.89 | -16.0 | WORSE |
| [0.25, 0.5) | 3 | 67 % | +2.96 | +8.9 | 10 | 20 % | -0.38 | -3.8 |  |
| [0.5, 10.0) | 4 | 50 % | +0.88 | +3.5 | 9 | 22 % | -0.38 | -3.4 |  |

**Target distance (pips)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0, 20) | 8 | 50 % | +0.45 | +3.6 | 26 | 35 % | -0.02 | -0.5 |  |
| [20, 30) | 12 | 50 % | +0.66 | +7.9 | 31 | 23 % | -0.36 | -11.1 | WORSE |
| [30, 45) | 14 | 50 % | +0.93 | +13.1 | 18 | 22 % | -0.05 | -0.8 |  |
| [45, 60) | 3 | 67 % | +2.26 | +6.8 | 15 | 27 % | +0.19 | +2.9 | better |
| [60, 90) | 4 | 50 % | +2.50 | +10.0 | 3 | 0 % | -1.10 | -3.3 |  |
| [90, 1000) | 6 | 17 % | -0.29 | -1.8 | 4 | 25 % | +2.91 | +11.7 |  |

**Time in the trade (hours; outcome-defined, not a rule)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0, 1) | 22 | 32 % | -0.06 | -1.2 | 55 | 16 % | -0.58 | -32.0 | WORSE |
| [1, 2) | 6 | 33 % | +0.48 | +2.9 | 12 | 17 % | -0.60 | -7.2 | WORSE |
| [2, 4) | 6 | 83 % | +2.47 | +14.8 | 6 | 17 % | -0.23 | -1.4 |  |
| [4, 8) | 5 | 40 % | +0.12 | +0.6 | 11 | 45 % | +1.07 | +11.8 |  |
| [8, 24) | 4 | 50 % | +1.42 | +5.7 | 3 | 67 % | +0.74 | +2.2 | better |
| [24, 1000) | 4 | 100 % | +4.20 | +16.8 | 10 | 60 % | +2.53 | +25.3 | better |

**Direction against the 1D 60-trading-day return**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| against | 10 | 40 % | +0.17 | +1.7 | 15 | 0 % | -1.03 | -15.5 | WORSE |
| with | 37 | 49 % | +1.02 | +37.9 | 82 | 30 % | +0.17 | +14.3 | better |

**Minutes from the signal to the fill**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [-1.0, 5.1) | 19 | 42 % | +0.51 | +9.7 | 42 | 17 % | -0.21 | -8.8 | WORSE |
| [5.1, 15.1) | 14 | 43 % | +0.80 | +11.2 | 26 | 23 % | -0.19 | -5.0 |  |
| [15.1, 30.1) | 6 | 67 % | +1.86 | +11.1 | 16 | 56 % | +1.01 | +16.2 | better |
| [30.1, 60.1) | 2 | 0 % | -1.10 | -2.2 | 6 | 17 % | -0.33 | -2.0 |  |
| [60.1, 120.1) | 5 | 80 % | +2.16 | +10.8 | 4 | 25 % | -0.27 | -1.1 |  |
| [120.1, 241.0) | 1 | 0 % | -1.10 | -1.1 | 3 | 33 % | -0.19 | -0.6 |  |

**Hours from the first touch to the signal**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [-1, 1) | 18 | 50 % | +0.76 | +13.8 | 31 | 16 % | -0.55 | -16.9 | WORSE |
| [1, 2) | 8 | 25 % | +0.16 | +1.3 | 16 | 31 % | +0.21 | +3.3 |  |
| [2, 4) | 6 | 50 % | +2.07 | +12.4 | 11 | 27 % | +0.03 | +0.3 |  |
| [4, 8) | 4 | 75 % | +1.23 | +4.9 | 15 | 20 % | -0.08 | -1.2 |  |
| [8, 24) | 6 | 33 % | +0.15 | +0.9 | 20 | 30 % | -0.11 | -2.3 | WORSE |
| [24, 1000) | 5 | 60 % | +1.25 | +6.3 | 4 | 75 % | +3.88 | +15.5 | better |

**Hours from the zone forming to its first touch**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| [0, 4) | 30 | 53 % | +1.15 | +34.5 | 67 | 19 % | -0.33 | -22.2 |  |
| [4, 8) | 12 | 42 % | +0.52 | +6.2 | 17 | 47 % | +1.29 | +21.9 |  |
| [8, 12) | 1 | 0 % | -1.10 | -1.1 | 6 | 50 % | +0.62 | +3.7 |  |
| [12, 24) | 3 | 33 % | +0.36 | +1.1 | 6 | 0 % | -1.10 | -6.6 | WORSE |
| [24, 1000) | 1 | 0 % | -1.10 | -1.1 | 1 | 100 % | +1.98 | +2.0 |  |

**Entry price against the Asia range (00:00-08:00 Amsterdam)**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| above asia high | 11 | 82 % | +1.94 | +21.4 | 22 | 23 % | +0.17 | +3.7 | better |
| below asia low | 16 | 50 % | +0.77 | +12.3 | 21 | 33 % | +0.23 | +4.9 |  |
| inside asia range | 20 | 25 % | +0.30 | +5.9 | 54 | 24 % | -0.18 | -9.8 | WORSE |

**Entry on a macro day**

| cut | IS trades | IS win | IS R/trade | IS R | OOS trades | OOS win | OOS R/trade | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|
| ECB | 2 | 0 % | -1.10 | -2.2 |  |  |  |  |  |
| EUCPI | 3 | 33 % | +0.36 | +1.1 | 3 | 0 % | -1.10 | -3.3 | WORSE |
| FOMC | 4 | 50 % | +1.51 | +6.0 | 4 | 0 % | -1.10 | -4.4 |  |
| NFP | 5 | 40 % | +0.22 | +1.1 | 4 | 0 % | -1.10 | -4.4 | WORSE |
| USCPI | 3 | 100 % | +2.86 | +8.6 | 8 | 38 % | +0.98 | +7.8 | better |
| none | 30 | 47 % | +0.83 | +25.0 | 78 | 28 % | +0.04 | +3.0 |  |

## 2. Market structure: what is public, and what the ledger says

Public knowledge (not course material), each checked against the ledger:

| Window | What is documented | The ledger (IS / OOS) |
|---|---|---|
| Frankfurt open 08:00, London open 09:00 | Intraday FX volatility is lowest in the Sydney-Tokyo hours and rises from the London open; a practitioner ATR profile puts a first peak around 07:00 GMT (08:00-09:00 Amsterdam) ([model-free periodicity study](https://dr.lib.sjp.ac.lk/items/04f21dd4-fbb1-4886-84cb-3ea1ce9ce5f5), [quanthedge](https://quanthedge.substack.com/p/seasonality-of-intraday-volatility), [tradethatswing](https://tradethatswing.com/analyzing-eur-usd-volatility-for-day-trading-purposes/)). A published 2016-2026 backtest of the London breakout of the Asian range on EURUSD lost (-28 %, profit factor 0.87): the range break is where the orders sit ([backtrex](https://backtrex.com/en/backtests/london-breakout-eur-usd)) | The bot never trades 08:00-09:00. Signals 09:00-09:30 are fine in both periods (IS 3, +0.72R; OOS 10, +0.16R); 09:30-10:00 loses in both (IS 6, -0.08R; OOS 15, -0.43R). Entries inside the Asia range lose in both; outside it win 63 % (IS) |
| New York desks 14:00, US data 14:30, NYSE open 15:30, 16:00 data and the 10:00 NY option cut | The London-New York overlap carries the highest EURUSD volatility of the day on every weekday (the same study); the option-expiry cut at 10:00 New York (16:00 Amsterdam) is a daily fixture with published strike lists but no public reversal statistics ([fxstreet](https://www.fxstreet.com/amp/news/fx-option-expiries-for-aug-28-ny-cut-202408280715), [investinglive](https://investinglive.com/Orders/!/option-expiries-for-the-10-am-ny-cut-today-23-sept-20160923/)) | Signals 14:00-14:30 win in both (IS 3, +3.60R; OOS 8, +1.19R). Signals 14:30-16:00 lose in both: IS 11 trades, 2 won, -5.7R; OOS 15, 4 won, -5.1R. 9 of the 11 IS signals came on a day with a high-impact US release at 14:30 or 16:00, outside the 30-minute blackout (OOS 6 of 15, so the effect is not only the calendar). 16:00-17:00 is mixed: IS 13, 69 %, +19.0R; OOS 13, 15 %, -8.6R |
| The 17:00 fix (16:00 London, WM/Reuters) | Pre- and post-fix rate changes are unusually volatile and negatively serially correlated, i.e. partly reversed, in all 21 pairs, strongest at month-end ([Evans 2018, Journal of Banking and Finance](https://ideas.repec.org/a/eee/jbfina/v87y2018icp233-247.html), [MPRA copy](https://mpra.ub.uni-muenchen.de/81583/1/MPRA_paper_81583.pdf)); dealers' pre-fix positions reverse during the fix ([Norges Bank, Panagiotou](https://www.norges-bank.no/contentassets/619c8b75e1ed4ba691e8ad6a006855e6/39-panagiotou---the-wmr-fix-and-its-impact-on-currency-markets-.pdf)) | Entries 16:30-17:00 (into the fix): IS 9, 56 %, +0.80R; OOS 7, 0 %, -1.10R: mixed. Trades still open at 17:00 won 79 % / 36 %, but that is the survivors (the losers die in the first hour), not a rule |
| The Asia range as liquidity | The overnight high and low are the first liquidity of the European day; the losing London-breakout backtest above is the public evidence that the break of that range tends to fail | Entry outside the day's 00:00-08:00 range: IS 27 trades, 63 %, +1.25R; OOS 43, 28 %, +0.20R. Inside: IS 20, 25 %, +0.30R; OOS 54, 24 %, -0.18R. The whole effect is in the shorts (inside: IS 0 of 5, OOS 4 of 30, -19.5R); longs inside the range are fine (IS +0.76R, OOS +0.40R). The 8 October screen ("Asia range taken before the signal") was a sweep test and mixed; this is the entry's position, a different cut |
| The weekly open gap | EURUSD Monday gaps fill 70-86 % of the time over short samples ([tradethatswing, Edgeful data](https://tradethatswing.com/eurusd-monday-gap-fill-strategy-and-statistics/)); no long-run study | Too few trades meet an unfilled gap: IS 3, OOS 4. Nothing to say |
| NFP, FOMC, ECB, CPI days | NFP moves EURUSD about 36 pips at the release against about 4 pips in a normal minute, with a tight pre-release range ([DailyFX](https://www.dailyfx.com/forex/fundamental/us_dollar_index/special_reports/2019/10/31/eurusd-expect-nfp-jobs-report-to-spark-us-dollar-price-action-nonfarm-payrolls.html)); no public event study of the whole day was found | The 30-minute blackout stays. Whole days: NFP IS 5 trades +1.1R (2 won), OOS 4 all lost; FOMC IS 4 +6.0R, OOS 4 all lost; ECB IS 2 both lost; US CPI IS 3 +8.6R, OOS 8 +7.8R; EU CPI IS 3 +1.1R, OOS 3 all lost. Any macro day: IS 17, +0.86R (as the base); OOS 19, -0.22R. Only NFP holds, thinly |
| Intraday reversal windows | What is documented with numbers is the fix reversal (above) and the failing London breakout; the New York-open and 10 am reversals exist as practitioner lore without published statistics | The first 30 minutes of a window are not worse (signals: IS 8, +0.69R; OOS 22, +0.73R). The bad slots are 09:30-10:00 and 14:30-16:00, both periods |

## 3. Exits

Maximum favourable and adverse excursion from the 5m candles between the fill and the close:

| | IS (24 losers, 22 winners) | OOS (68 losers, 25 winners) |
|---|---|---|
| Losers that reached +0.5R / +1R / +1.5R / +2R before the stop | 42 % / 33 % / 8 % / 0 % | 49 % / 32 % / 19 % / 9 % |
| Losers that never saw +0.25R | 38 % | 46 % |
| Losers' MFE: median / q75 / q90 / max | 0.44R / 1.18R / 1.36R / 1.74R | 0.40R / 1.19R / 1.81R / 2.91R |
| Winners' adverse excursion: median, share past 0.5R, past 0.75R | 0.41R, 45 %, 23 % | 0.35R, 44 %, 28 % |
| Winners' R: median / mean | 2.61 / 3.10 | 2.23 / 3.06 |

A third of the losers see +1R first; almost none see +2R. But half the winners also dip more than 0.5R against the entry,
and 23-28 % more than 0.75R, so every stop that moves to the entry cuts winners. Simulated on the 5m candles (stop before
target in a candle; the ledger's 4R break-even reproduced exactly):

| Exit rule | IS: won / at zero / R a trade / sum | OOS: won / at zero / R a trade / sum |
|---|---|---|
| The ledger (break-even at 4R) | 47 % / 2 % / +0.84 / +39.5R | 26 % / 4 % / -0.01 / -1.2R |
| Break-even at +1R | 34 % / 32 % / +0.56 / +26.4R | 15 % / 36 % / -0.15 / -14.8R |
| Break-even at +1.5R | 38 % / 15 % / +0.59 / +27.6R | 21 % / 22 % / -0.07 / -6.5R |
| Break-even at +2R | 45 % / 4 % / +0.75 / +35.1R | 23 % / 12 % / -0.09 / -8.7R |
| Break-even at +3R | as the ledger | as the ledger |
| Trail to the latest 15m swing (2-candle fractal, 1 pip beyond), from the fill | 45 % / 2 % / +0.47 / +22.2R | 23 % / 3 % / -0.39 / -37.4R |
| the same from +0.5R / +1R / +1.5R / +2R | +27.4R / +27.2R / +26.0R / +33.4R | -33.3R / -26.9R / -15.4R / -15.0R |
| Trail from +1R and break-even at +1.5R | 45 % / 11 % / +0.42 / +19.9R | 27 % / 16 % / -0.22 / -21.3R |
| Time stop: from N hours on, close at a 5m close at or under -0.5R; N = 1 / 2 / 4 / 8 / 12 | +36.9R / +35.8R / +35.2R / +37.0R / +40.0R | -9.8R / -6.3R / -1.0R / -2.5R / -2.6R |
| Close at N hours if under 0R; N = 2 / 4 / 8 / 12 / 24 | +30.1R / +34.7R / +33.8R / +34.3R / +39.5R | -11.4R / -12.9R / -1.4R / -2.3R / -3.1R |
| Close at N hours if under -0.5R (once); N = 4 / 8 / 12 | +36.6R / +36.6R / +39.5R | -3.5R / -1.2R / -0.9R |

Nothing improves both periods; the time stop at 12 hours is the only variant that is not worse in IS (+0.5R) and it
costs 1.4R in OOS. Why: of the trades open and under 0R two hours after the fill, 3 of 4 (IS) and 5 of 10 (OOS) still
reached the target; under -0.5R at four hours 1 of 1 and 1 of 2. The losers are already gone by then. The exits stay as
they are (the 4 October finding, "bad entries, not bad management", holds on this profile in both periods).

## 4. Entry: the limit

**Fill share.** IS: 61 signals, 3 refused on R:R before an order, 1 on the open-trade cap, 1 while a limit rested; 56
limits placed, 47 filled (84 %), 8 expired after 4 hours, 1 cancelled because the target traded first. OOS: 122
signals, 7 refused on R:R, 5 while a limit rested; 110 placed, 97 filled (88 %), 6 expired, 7 target-first. The limit
sits a median 2.2 pips from the signal close (`entry` against `entry_planned`); the ledger's mean fill fraction is 0.22
of the signal-to-stop distance because a 5m open beyond the limit fills at the open.

**The pullback distribution** (the deepest move toward the stop inside the 4-hour window, as a fraction of the
signal-to-stop distance): winners q25 / median / q75 = 0.37 / 0.56 / 0.78 (IS) and 0.37 / 0.56 / 0.80 (OOS); losers 0.91 /
1.11 / 1.22 and 0.98 / 1.11 / 1.34 (they go through the stop). 77-80 % of the winners pull back to 35 %, 55-56 % to 50 %;
every loser does. So a deeper limit keeps all the losers and loses a fifth of the winners, while the winners that do
fill pay less risk per pip of target:

| Limit | IS: fills, won, R a trade, sum | OOS: fills, won, R a trade, sum |
|---|---|---|
| 15 % (ledger estimate, all fill at a worse price) | 47, 47 %, +0.70, +32.7R | 97, 26 %, -0.09, -8.5R |
| 15 % in the engine (`eulim15`, one position, 2024-2026) | 41 trades, 46 %, +29.4R against 41, +38.8R at 25 %: 7 limits expired against 6, one signal swapped, no extra fills | not run |
| 25 % (the ledger) | 47, 47 %, +0.84, +39.5R | 97, 26 %, -0.01, -1.2R |
| 35 % | 42 (89 %), 40 %, +1.03, +43.1R | 92 (95 %), 22 %, -0.06, -5.9R |
| 50 % | 36 (77 %), 33 %, +1.25, +45.2R | 84 (87 %), 17 %, -0.02, -1.5R |
| The limit active only from 5 / 15 / 30 minutes after the signal | +30.3R / +15.9R / +16.2R | -3.4R / -6.5R / -3.3R |

15 % is worse in both periods and adds no fills: the signals that do not come back 25 % do not come back 15 % either
(they run). 35 % trades win rate for R: IS +3.6R and 7 points of win rate lost, OOS -4.7R and 4 points; 50 % the same
further. With the challenge judged on win rate as much as R, 25 % stays. The late-fill pattern of section 1 (fills
15-30 minutes after the signal won 56-67 %) is a path effect (the price runs first and returns), not a timing rule: a
limit that only becomes active after 5-30 minutes is worse in both periods, because the immediate-fill trades still
fill later and the three IS winners that filled at once and never returned (+9.2R) are lost.

## 5. The candidates

Each: the exact rule, the knob or the smallest code change, the expected effect, the pre-screen on the ledger in both
periods (trades, won, R a trade, sum; base IS 47, 47 %, +0.84, +39.5R; OOS 97, 26 %, -0.01, -1.2R), the per-year count
and the caveats. The session rules are judged by the signal time, which is what `session.windows` acts on; the
anatomy's fill-time tables tell the same story.

**1. No signal 14:30-16:00 Amsterdam.** `session.windows: [["09:00","11:00"], ["13:00","14:30"], ["16:00","17:00"]]`.
IS 36 trades, 56 %, +1.26R, +45.3R; OOS 82, 26 %, +0.05R, +3.9R; better in 6 years, worse in 3 (2017 -0.6R, 2018 -0.5R,
2022 -0.8R), 2024-2026 all better. Removed: IS 11 signals (2 won, -5.7R), OOS 15 (4 won, -5.1R). The 90 minutes hold the
14:30 US releases, the 15:30 NYSE open and the 16:00 releases; the news blackout only covers 30 minutes around the
high-impact ones, and 9 of the 11 IS signals fell on such a day between the blackouts. Expected: 1.1 trades a month
instead of 1.5, the win rate up 9 points, more R in the recent years. The sub-windows do not hold alone (14:30-15:30
fails OOS, 15:00-16:00 fails IS), so the rule is the whole 90 minutes or nothing. No code.

**2. Session from 10:00.** `session.windows: [["10:00","11:00"], ["13:00","17:00"]]`. IS 38, 50 %, +1.00R, +37.9R; OOS
72, 26 %, +0.05R, +3.6R; better 7 years, worse 3 (2018, 2023, 2025 -3.9R). Removed: IS 9 signals (3 won, +1.7R: a gain per
trade, not in sum), OOS 25 (6 won, -4.8R). The 09:00-09:30 signals are fine in both periods, 09:30-10:00 is the bad slot;
a 09:00-09:30 + 10:00-11:00 window would be a cherry-pick, so the honest knob is 10:00. Flagged by the 4 October anatomy
(`eu_sess10_full`); no result was recorded. Combined with 1 (windows 10-11, 13-14:30, 16-17): IS 27, 63 %, +1.61R, +43.6R;
OOS 57, 26 %, +0.15R, +8.8R; better 8 years, worse 2; 0.84 trades a month. No code.

**3. No entry while the planned entry lies inside the day's Asia range** (the 00:00-08:00 Amsterdam high-low of the
5m candles). New filter, e.g. `confirmation.outside_overnight_range: true` with `overnight_start/end` (a signal whose
entry price lies between the range's low and high is refused). IS 27, 63 %, +1.25R, +33.6R; OOS 43, 28 %, +0.20R, +8.6R;
better 6 years, worse 4 (2025 -9.2R). Sensitivity: the 23:00-08:00, 01:00-08:00 and 02:00-08:00 ranges hold, 00:00-09:00
and a 3-pip tolerance inside the range fail OOS. The effect is the shorts: inside the range IS 0 of 5, OOS 4 of 30
(-19.5R); longs inside are as good as the base. The shorts-only variant: IS 42, 52 %, +1.07R, +45.0R; OOS 67, 31 %,
+0.27R, +18.2R; better 8 years, worse 1, but it rests on 5 IS trades and has no reason to be one-sided. Expected from
the symmetric rule: a higher win rate, fewer trades (0.84 a month), less sum in 2025. Needs code.

**4. No trade against the 60-trading-day daily return** (close of the last closed daily candle against the close 60
rows earlier; a long needs it positive, a short negative). New gate, e.g. `bias.trend_filter_days: 60` next to
`no_trade_against`. IS 37, 49 %, +1.02R, +37.9R; OOS 82, 30 %, +0.17R, +14.3R; better 7 years, worse 1 (2026 -4.3R).
Removed: IS 10 (4 won, +1.7R), OOS 15 (0 won, -15.5R). Lookback: the against-trend trades lose in OOS from 40 to 120 days
(-0.23 to -1.03R a trade) and are close to the base in IS at 80-120 days, under it at 40-60: the IS side is weak, the
OOS 0 of 15 carries it. Distinct from the regime screen (`S/regime/regime.py`, the 60-day return as a market state, not
relative to the direction), which found nothing on EURUSD. Needs code.

**5. Stop at least half the 1H ATR14.** `risk.min_stop_atr: 0.5` with `risk.min_stop_atr_tf: 1H`. As a skip (the
pre-screen): IS 42, 50 %, +1.00R, +41.8R; OOS 82, 29 %, +0.13R, +10.6R; better 6 years, worse 1. The 20 trades under it
won 2 (stops of 6-17 pips on hourly ranges of 12-41 pips: 7 April 2025, March 2020, the November 2020 election, seven
days of 2022). As a widen, the `min_stop_pips` semantics (the stop moved out to 0.5 ATR, the trade re-walked on the 5m
candles, R:R 1.0 kept): IS 47, 47 %, +0.83R, +39.1R (-0.4R); OOS 97, 28 %, +0.07R, +6.4R (+7.6R): the OOS gain, no IS
change. Caveat: a narrow plateau; 0.4 removes three trades and changes nothing, 0.6 removes 2025 winners (IS +27.7R).
Needs code (an ATR input to `risk.py`).

**6. The 1D+1H pair needs a third aligned timeframe.** `bias.min_matching_timeframes: 3` (the code counts aligned
timeframes of any kind; the three-timeframe combinations already have three). IS 40, 50 %, +0.96R, +38.5R; OOS 80, 28 %,
+0.11R, +8.6R; better 5 years, worse 3 (2024 -2.2R). Removed: IS 7 (2 won, +1.1R), OOS 17 (3 won, -9.9R). A new twist on
the settled pair (7 October): the pair's trades with the 4H, the week or the month also aligned are the ones that
earned. Those bare-pair trades already run at half stake under the month-at-50/50 rule, so the live effect is half
this. No code.

**7. No entry on an NFP day** (the day's whole session, not the 30 minutes). A title-based day blackout in `news`.
IS 42, 48 %, +0.92R, +38.4R; OOS 93, 27 %, +0.03R, +3.2R; better 4 years, worse 2, same 4. Nine trades, two won. The
weakest candidate, listed because the mechanism is documented (a dead morning, a spike at 14:30) and it is cheap.
Needs a small code change.

**8. Zone touched within 12 hours of forming.** `confirmation.max_touch_age_hours: 12`. IS 43, 49 %, +0.92R, +39.6R
(the sum unchanged); OOS 90, 27 %, +0.04R, +3.4R; better 6 years, worse 2. Removed: IS 4 (-0.1R), OOS 7 (-4.6R). Small,
free. The 7 October ledger replay across markets found every limit from 12 to 48 h helping and chose 24.

**Stacking.** The filters overlap (IS: about 15 of the 33 trades that any of 1-5 removes are removed by two or more): 1+2+5 IS
24, 67 %, +1.82R, +43.7R, OOS 46, 30 %, +0.35R, +16.2R (better 8 years, worse 2); the knobs-only set 1+2+6+8 IS 23, 61 %,
+1.51R, +34.8R, OOS 46, 30 %, +0.38R, +17.6R (6 / 4); all of 1-6 IS 11 trades, 91 %, +26.7R. Each added filter raises the
win rate and lowers the IS sum, and the trade count falls to under one a month. Order of testing: 1 (the only rule
that raises the IS sum while cutting trades), then 2, then the knob checks 6 and 8; 3-5 need code and each costs IS
sum for OOS gain.

## 6. Settled by this screen (not candidates)

- Break-even at +1R, +1.5R, +2R: worse in both periods (IS -4.4 to -13.1R; OOS -5.3 to -13.6R).
- A trailing stop to the latest 15m swing, from the fill or from +0.5 / +1 / +1.5 / +2R: worse in both.
- Time stops (-0.5R after 1-24 h; flat after 2-24 h): worse or flat in both.
- Limit 15 % (worse in both, no extra fills), 35 % and 50 % (R for win rate; OOS worse), a delayed limit (worse in both).
- The first 30 minutes of a window: not worse. The 13:00-13:30 and 09:00-09:30 slots are fine in both periods.
- The 16:00-17:00 fix hour, FOMC, ECB and CPI days, the weekly gap, weekday, month, planned R:R band, stop pips band,
  entry depth, stop / zone height, target distance, second visits: mixed or non-monotonic.
- Entry outside the zone only (`max_entry_depth: 0`): IS +0.75R a trade on 29 trades, under the base.
