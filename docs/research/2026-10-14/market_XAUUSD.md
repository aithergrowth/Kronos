# Gold (XAUUSD): what would make it better (14 October 2026)

Ledgers `S/aca/base_XAUUSD.csv` (in-sample, IS: 2024-01 to 2026-09, 143 trades) and `S/aca/oos_base_XAUUSD.csv` (out-of-sample, OOS:
2017-2023, 371 trades), the live gold profile at 1 % and the guard off, bid candles, a 2-pip spread, no commission. Every R below is
**after the 0.10R research cost** unless marked raw. Scripts and full outputs: `S/research/xau_work/` (`anatomy.py` ->
`anatomy_out.md`, `exits.py` -> `exits_out.md`, `final2.py`; per-trade CSVs next to them). The 5m walk reproduces the IS ledger trade
for trade (max deviation 0.00R) and the OOS ledger within 0.6R (one gap fill), so the exit and cost variants are like-for-like.

| | Trades | Won | R a trade | Sum R (raw) | Deepest dip | Median stop | Median stop / 1H ATR14 |
|---|---|---|---|---|---|---|---|
| IS 2024-2026 | 143 | 49 % | +0.50 | +71.8 (+86.1) | -9.0R | $8.50 | 0.89 |
| OOS 2017-2023 | 371 | 30 % | -0.17 | -62.2 (-25.1) | -83.2R | $3.23 | 1.10 |

**The short version.** The losers are entries, not management: break-even at 2R beats every other exit tested (BE at 1R, 1.5R, 3R, a 15m-swing
trail, time stops) in both periods. What is weak in *both* periods: entries in the 10:00-11:00 and 15:00-15:30 hours, entries that close
deep in the zone (more than a quarter of its height), entries after an expanded day (the last 24 hours spanning more than 8 hourly ATRs),
entries in a ranging daily regime (efficiency ratio under 0.2), and the fixed-2R fallback target (its trades pay better at 3R in both
periods). Costs: the measured 3.7-pip spread takes 0.05R a trade off the IS ledger and refuses, through the live spread cap, 30 OOS
trades the backtest took. Six candidates are set out in section 5; stacked, the four rule-level ones take IS from +71.8R to +79.5R
(dip -9.0R -> -4.8R) and OOS from -62.2R to -18.8R (dip -83R -> -43R), better than the ledger in 8 of 10 years, worse in 2023 (-2.5R)
and 2026 (-7.5R). A caution before the tables: 2026 is the year in which everything worked (38 trades, 61 %, +0.95R a trade), so every
filter below costs some 2026 R; the gains sit in the years that look like 2017-2022.

## 1. Loss anatomy, both periods

Columns: trades, won, R a trade, sum R, for IS and OOS; the last two columns give the change in the period's total if that bucket were
traded at **half the stake** (positive = the total improves). A bucket is "weak" when its R a trade is below the period's own average
(IS +0.50, OOS -0.17) in both periods.

### Hour of entry (Amsterdam)

| bucket | IS n | IS win % | IS R/t | IS sum R | OOS n | OOS win % | OOS R/t | OOS sum R | half-stake gain IS | OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| 09 | 31 | 48 | +0.57 | +17.6 | 86 | 29 | -0.10 | -8.4 | -8.8 | +4.2 |
| **10** | 21 | 33 | -0.28 | -5.9 | 66 | 24 | -0.33 | -22.1 | +3.0 | +11.0 |
| 13 | 28 | 46 | +0.61 | +17.2 | 57 | 28 | -0.15 | -8.8 | -8.6 | +4.4 |
| 14 | 24 | 62 | +1.18 | +28.4 | 55 | 35 | -0.04 | -2.4 | -14.2 | +1.2 |
| 15 | 19 | 47 | +0.25 | +4.7 | 48 | 23 | -0.44 | -21.4 | -2.4 | +10.7 |
| 16 | 20 | 55 | +0.49 | +9.9 | 59 | 39 | +0.01 | +0.8 | -4.9 | -0.4 |

Half hours (the ones that matter; the full table is in `anatomy_out.md`):

| bucket | IS n | IS win % | IS R/t | IS sum R | OOS n | OOS win % | OOS R/t | OOS sum R |
|---|---|---|---|---|---|---|---|---|
| 10:00-10:30 | 9 | 44 | -0.01 | -0.1 | 28 | 25 | -0.28 | -7.9 |
| 10:30-11:00 | 8 | 25 | -0.41 | -3.3 | 28 | 21 | -0.43 | -12.0 |
| 13:30-14:00 | 12 | 50 | +0.92 | +11.0 | 30 | 23 | -0.16 | -4.8 |
| 14:00-14:30 | 15 | 67 | +1.30 | +19.5 | 35 | 29 | -0.27 | -9.4 |
| 14:30-15:00 | 8 | 50 | +0.80 | +6.4 | 14 | 50 | +0.16 | +2.3 |
| **15:00-15:30** | 9 | 22 | -0.44 | -4.0 | 25 | 24 | -0.38 | -9.4 |
| 15:30-16:00 | 12 | 67 | +0.84 | +10.0 | 25 | 24 | -0.45 | -11.3 |
| 16:00-16:30 | 8 | 75 | +1.03 | +8.2 | 24 | 33 | -0.15 | -3.5 |
| 16:30-17:00 | 8 | 38 | +0.01 | +0.1 | 33 | 42 | +0.11 | +3.7 |

- The 10:00 hour is negative in both periods and in both of its halves (the 4 October anatomy on the older gold profile found the same hour
  the worst: 28 trades, 32 %). 15:00-15:30 (09:00-09:30 New York: after the 08:30 data, before the 09:30 equity open) is the other
  half hour negative in both. Together: IS 32 trades, 31 %, -9.7R; OOS 86 trades, 24 %, -29.0R. Longs carry most of it (IS 22 trades
  -8.4R, OOS 46 trades -16.2R) but shorts lose too. Their losers rarely worked: MFE of at least 1R in 18 % (IS) and 21 % (OOS).
- Permutation check (5,000 random subsets of the same size): IS p = 0.002, OOS p = 0.11. Strong in-sample, consistent out-of-sample,
  not proof there.
- Session parts: 09-11: IS 52 trades +0.22R/t, OOS 152 -0.20; 13:00-14:30 (before the old COMEX pit open): IS 42, 52 %, **+0.79**; OOS 92,
  29 %, -0.10; 14:30-17:00: IS 45, 51 %, +0.46; OOS 121, 34 %, -0.15. Entries before 14:30 are as good or better in both periods: no
  rule there.

### Weekday and month

| weekday | IS n / win / R/t | OOS n / win / R/t | | month | IS n / win / R/t | OOS n / win / R/t |
|---|---|---|---|---|---|---|
| Mon | 27 / 48 % / +0.55 | 56 / 32 % / -0.07 | | Jan | 12 / 67 % / +0.84 | 41 / 27 % / -0.26 |
| Tue | 34 / 47 % / +0.63 | 71 / 27 % / -0.17 | | Sep | 15 / 33 % / -0.18 | 35 / 29 % / -0.11 |
| Wed | 29 / 52 % / +0.49 | 81 / 30 % / -0.22 | | Oct | 15 / 67 % / +1.52 | 36 / 14 % / -0.67 |
| Thu | 28 / 50 % / +0.33 | 87 / 32 % / -0.13 | | Nov | 9 / 44 % / -0.14 | 32 / 25 % / -0.35 |
| Fri | 25 / 48 % / +0.49 | 76 / 28 % / -0.23 | | others | in `anatomy_out.md` | |

No weekday is weak in both periods (Monday, the older profile's worst day, is IS's second-best). October is IS's best month and OOS's
worst: the month-of-year cut is noise. Nothing to act on.

### Bias combination, zone timeframe, target kind, planned R:R, visit

| bucket | IS n | IS win % | IS R/t | IS sum R | OOS n | OOS win % | OOS R/t | OOS sum R | half-stake gain IS | OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| 1D+1H | 33 | 39 | +0.31 | +10.2 | 151 | 30 | -0.13 | -20.0 | -5.1 | +10.0 |
| 1M+1D+1H | 12 | 75 | +1.08 | +12.9 | 50 | 30 | -0.20 | -10.0 | -6.5 | +5.0 |
| 1M+1W+1D | 49 | 47 | +0.48 | +23.3 | 52 | 21 | -0.28 | -14.4 | -11.6 | +7.2 |
| 4H+1H | 49 | 51 | +0.52 | +25.5 | 118 | 32 | -0.15 | -17.8 | -12.7 | +8.9 |
| zone 4H (15m shift) | 13 | 62 | +1.08 | +14.1 | 48 | 25 | -0.24 | -11.5 | -7.0 | +5.7 |
| zone 1H (5m shift) | 130 | 48 | +0.44 | +57.7 | 323 | 30 | -0.16 | -50.7 | -28.9 | +25.4 |
| target: impulse origin | 77 | 45 | +0.53 | +40.6 | 180 | 32 | -0.03 | -5.7 | -20.3 | +2.9 |
| **target: fixed 2R fallback** | 66 | 53 | +0.47 | +31.2 | 191 | 27 | -0.30 | -56.5 | -15.6 | +28.2 |
| planned R:R < 1 | 11 | 55 | -0.07 | -0.8 | 18 | 39 | -0.34 | -6.1 | +0.4 | +3.1 |
| 1-1.5 | 18 | 50 | +0.03 | +0.6 | 50 | 48 | -0.04 | -2.1 | -0.3 | +1.1 |
| 1.5-2 | 9 | 33 | -0.17 | -1.6 | 22 | 36 | -0.12 | -2.6 | +0.8 | +1.3 |
| = 2 (the fallback) | 66 | 53 | +0.47 | +31.2 | 192 | 28 | -0.28 | -54.7 | -15.6 | +27.3 |
| 2-3 | 15 | 40 | +0.30 | +4.5 | 32 | 22 | -0.30 | -9.8 | -2.2 | +4.9 |
| 3-5 | 13 | 54 | +1.58 | +20.5 | 30 | 20 | +0.10 | +3.1 | -10.2 | -1.6 |
| > 5 | 11 | 36 | +1.59 | +17.4 | 27 | 19 | +0.37 | +9.9 | -8.7 | -5.0 |
| visit 1 | 140 | 49 | +0.49 | +69.2 | 343 | 29 | -0.18 | -63.2 | | |
| visit 2+ | 3 | 67 | +0.87 | +2.6 | 28 | 39 | +0.03 | +1.0 | | |

- The whole OOS loss sits in the fixed-2R fallback trades (-56.5R of -62.2R; the origin-target trades are flat at -0.03R a trade). In
  IS the two kinds earn the same per trade, so the fallback as such is not weak in both periods; what is different is how far their
  target should sit (section 3: the same trades at a 3R target earn more in both periods).
- The combination, zone timeframe and visit cuts turn between the periods (1D+1H is IS's weakest, OOS's least bad). Second visits are
  fine in both. Nothing to act on.

### Stop size, stop relative to the 1H ATR14, entry depth

| bucket | IS n | IS win % | IS R/t | IS sum R | OOS n | OOS win % | OOS R/t | OOS sum R | half-stake gain IS | OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| stop < $2 | 2 | 0 | -1.10 | -2.2 | 92 | 25 | -0.26 | -24.2 | +1.1 | +12.1 |
| $2-3 | 8 | 50 | +1.55 | +12.4 | 74 | 32 | +0.07 | +5.2 | -6.2 | -2.6 |
| $3-5 | 21 | 29 | -0.11 | -2.3 | 98 | 30 | -0.25 | -24.6 | +1.2 | +12.3 |
| $5-8 | 35 | 49 | +0.42 | +14.7 | 58 | 38 | +0.01 | +0.7 | -7.4 | -0.4 |
| $8-12 | 38 | 55 | +0.57 | +21.6 | 31 | 29 | -0.26 | -8.0 | -10.8 | +4.0 |
| $12-20 | 20 | 60 | +0.80 | +16.0 | 17 | 12 | -0.77 | -13.1 | -8.0 | +6.6 |
| > $20 | 19 | 53 | +0.61 | +11.6 | 1 | 100 | +1.88 | +1.9 | | |
| stop / ATR1H < 0.5 | 15 | 33 | +0.35 | +5.2 | 26 | 27 | +0.05 | +1.4 | -2.6 | -0.7 |
| 0.5-0.75 | 33 | 58 | +0.86 | +28.4 | 69 | 29 | -0.17 | -11.9 | -14.2 | +5.9 |
| 0.75-1 | 33 | 48 | +0.47 | +15.5 | 57 | 32 | +0.02 | +1.4 | -7.8 | -0.7 |
| 1-1.5 | 30 | 37 | +0.03 | +1.0 | 110 | 29 | -0.25 | -27.9 | -0.5 | +13.9 |
| 1.5-2 | 14 | 64 | +0.64 | +9.0 | 38 | 32 | -0.20 | -7.8 | -4.5 | +3.9 |
| > 2 | 18 | 56 | +0.71 | +12.8 | 71 | 30 | -0.25 | -17.5 | -6.4 | +8.7 |
| entry outside the zone (depth < 0) | 107 | 54 | +0.63 | +67.1 | 292 | 30 | -0.20 | -58.9 | -33.6 | +29.5 |
| depth 0-0.25 of the height | 18 | 44 | +0.59 | +10.6 | 50 | 30 | +0.09 | +4.5 | -5.3 | -2.3 |
| **depth 0.25-0.5** | 18 | 22 | -0.33 | -5.9 | 29 | 24 | -0.27 | -7.8 | +3.0 | +3.9 |

- Dollar stops are not comparable across the periods (gold at $1,573 with a $2.91 hourly ATR against $3,226 and $8.07), and in ATR
  units no band is weak in both with a monotonic story ($3-5 and 1-1.5 ATR are weak in both, but the bands either side are fine): stop
  size is not a lever. The engine's 8-pip minimum never binds in IS; OOS 30 stops were under $1.23 (section 4).
- Depth is monotonic in both periods: the shallower the entry, the better (IS +0.63 / +0.59 / -0.33 R a trade; OOS the 0-0.25 band is the
  best bucket of the period). The deep entries' losers never worked (MFE of at least 1R: 23 % IS, 10 % OOS). Permutation p: IS 0.015,
  OOS 0.38 (n 29). The depth is what `risk.max_entry_depth` measures (`strategy/risk.py`: height from the near edge), now capped at 0.5.

### Direction, the daily trend, the regime, compression

| bucket | IS n | IS win % | IS R/t | IS sum R | OOS n | OOS win % | OOS R/t | OOS sum R | half-stake gain IS | OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| LONG | 110 | 47 | +0.43 | +47.6 | 190 | 32 | -0.07 | -13.2 | -23.8 | +6.6 |
| SHORT | 33 | 55 | +0.73 | +24.2 | 181 | 28 | -0.27 | -49.0 | -12.1 | +24.5 |
| with the 60-day return | 106 | 46 | +0.43 | +45.1 | 261 | 31 | -0.11 | -28.8 | -22.5 | +14.4 |
| against the 60-day return | 37 | 57 | +0.72 | +26.8 | 110 | 25 | -0.30 | -33.4 | -13.4 | +16.7 |
| with the 20-day return | 106 | 50 | +0.56 | +59.0 | 262 | 31 | -0.12 | -30.2 | -29.5 | +15.1 |
| against the 20-day return | 37 | 46 | +0.35 | +12.9 | 109 | 28 | -0.29 | -32.0 | -6.4 | +16.0 |
| ER20 tercile low (< 0.15) | 49 | 49 | +0.40 | +19.6 | 123 | 27 | -0.26 | -31.9 | -9.8 | +15.9 |
| ER20 mid (0.15-0.333) | 47 | 53 | +0.55 | +25.7 | 124 | 26 | -0.31 | -38.3 | -12.9 | +19.2 |
| ER20 high (> 0.333) | 47 | 45 | +0.56 | +26.5 | 124 | 36 | +0.06 | +8.0 | -13.3 | -4.0 |
| **ER20 < 0.2** (fixed band) | 59 | 47 | +0.33 | +19.6 | 169 | 24 | -0.36 | -61.4 | -9.8 | +30.7 |
| ER20 0.2-0.35 | 45 | 60 | +0.83 | +37.3 | 85 | 33 | -0.04 | -3.6 | -18.7 | +1.8 |
| ER20 0.35-0.5 | 13 | 38 | +0.80 | +10.3 | 77 | 35 | +0.06 | +5.0 | -5.2 | -2.5 |
| ER20 > 0.5 | 26 | 38 | +0.18 | +4.6 | 40 | 35 | -0.06 | -2.2 | -2.3 | +1.1 |
| 24h range / ATR1H tercile compressed (< 5.6) | 57 | 56 | +0.72 | +41.1 | 116 | 28 | -0.12 | -13.4 | -20.5 | +6.7 |
| mid (5.6-7.3) | 42 | 38 | +0.15 | +6.5 | 127 | 35 | -0.06 | -7.2 | -3.2 | +3.6 |
| expanded (> 7.3) | 44 | 50 | +0.55 | +24.3 | 128 | 25 | -0.33 | -41.6 | -12.1 | +20.8 |
| **24h range > 8 x ATR1H** | 30 | 40 | +0.13 | +3.9 | 87 | 21 | -0.46 | -40.0 | -2.0 | +20.0 |
| range 8-9 / 9-10 / 10-12 / > 12 | 22 / 5 / 2 / 1 | | +0.09 / +0.45 / +0.41 / -1.10 | | 39 / 24 / 14 / 10 | | -0.45 / -0.34 / -0.66 / -0.50 | | | |
| net 24h move in the trade direction > 4 ATR ("chasing") | 53 | 53 | +0.45 | +23.6 | 147 | 27 | -0.31 | -45.7 | -11.8 | +22.9 |
| net 24h move against the trade (0 to -4 ATR) | 22 | 32 | +0.72 | +15.9 | 45 | 33 | +0.21 | +9.5 | | |

- Direction and the 60-day trend turn between the periods (shorts and counter-trend entries are IS's best and OOS's worst): no rule.
  Entries against the 20-day return rank below entries with it in both periods, but the IS bucket is still positive (+0.35), so a half
  stake costs 6.4R IS for 16.0R OOS. Kept as an observation.
- The efficiency ratio on **closed** daily bars (the regime note of `S/regime/regime.py` labelled with the forming bar) puts the line at
  0.2, not 0.35: under 0.2 is below the period average in both (IS +0.33 against +0.50; OOS -0.36 against -0.17, 169 trades, 24 %
  won), while 0.2-0.35 is IS's best band (60 %, +0.83) and flat OOS. Permutation p: IS 0.19, OOS 0.014. Of the IS low-ER trades the
  three best years (2023, 2025, 2026) are the ones that would pay for a half stake there.
- The expanded day (the last 24 closed 1H candles spanning more than 8 hourly ATRs) is the one volatility cut weak in both periods
  (IS +0.13 a trade, p 0.11; OOS -0.46, p 0.016), and monotonic within OOS. 82 of its 87 OOS trades came after the market had already
  moved more than 4 ATR in the trade's direction: these are late entries, not reversals. The existing `confirmation.max_adverse_move_atr`
  measures the opposite thing (the move against the trade) and was not taken (README, 8 October).
- Also screened and not weak in both: the Asia range (00-08 Amsterdam) relative to the ATR (narrow IS +0.42, OOS -0.31: IS at average),
  the week at 50/50 (above average in both), the month at 50/50 (IS 11 trades -0.12 a trade; OOS 106 trades -0.06, better than the OOS
  average: the live half stake there does not protect the out-of-sample years).

### Year by year (ledger, after the cost)

| year | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| trades | 60 | 57 | 58 | 51 | 41 | 61 | 43 | 57 | 48 | 38 |
| won | 35 % | 30 % | 22 % | 31 % | 20 % | 28 % | 42 % | 39 % | 52 % | 61 % |
| R | -3.6 | -15.7 | -16.6 | -12.0 | -17.3 | -11.7 | +14.8 | +13.7 | +21.9 | +36.3 |

## 2. Market structure (public knowledge and our own candles)

The clock in Amsterdam (London is always one hour behind Amsterdam; New York six hours, apart from the two to three weeks a year when the
US and Europe change their clocks on different dates):

| Amsterdam | Event | What the data and the ledger say |
|---|---|---|
| 00:00 | CME Globex reopens (18:00 ET); the 5m data's first candle of the day | |
| 01:00-09:00 | Asian hours (Tokyo from 01:00/02:00, Shanghai from 02:30/03:30) | own candles: median hourly range 0.7-0.8 ATR, mean return +0.1 to +0.6 bp an hour (the "hat" of the literature: a small, steady rise) |
| 09:00 | London 08:00: the morning's first move | the 09:00 hour has the morning's widest range (1.1-1.3 ATR); the bot's first entry hour (IS +0.57 a trade) |
| 10:00-11:00 | London 09:00-10:00: the hour after the opening move | the weakest entry hour in both periods (section 1) |
| 11:30 | LBMA Gold Price AM auction (10:30 London) | inside the 11-13 break: no entries |
| 13:00 | the afternoon window opens (US pre-market) | 13:00-14:30 entries: IS 52 %, +0.79 a trade; OOS -0.10 |
| 14:20 | the old COMEX pit open (08:20 ET); the pits closed (futures 2015, options 30 December 2016), retail still calls it the New York open | no visible edge either side of it |
| 14:30 | US data (08:30 ET) | the 14:00 and 15:00 hours are the day's widest (1.5-1.9 ATR); the news blackout already covers 14:00-15:00 on data days |
| 15:00-15:30 | after the data, before the equity open | negative in both periods (section 1) |
| 15:30 | NYSE open (09:30 ET) | 15:30-16:00 entries: IS +0.84, OOS -0.45 (turns) |
| 16:00 | LBMA Gold Price PM auction (15:00 London) | 16:00-16:30 entries: IS +1.03, OOS -0.15 (turns); no fix effect visible in 514 trades |
| 17:00 | the session ends (16:00 London) | |
| 19:30 | COMEX settlement window 13:29-13:30 ET | outside the session |
| 23:00-00:00 | the CME daily break (17:00-18:00 ET): the data's last candle 22:55, the next 00:00 (on the DST-mismatch nights 22:00-23:00) | trades held across it: IS 36 trades, 67 %, **+1.28 a trade, +46.0R of the period's +71.8**; OOS 84 trades, 42 %, +0.27 a trade, +23.0R while the same-day trades lost -85.2R. The winners are the trades that survive into the next day: a day close (README: -24.1R) or a weekend close (`wkclose` -7.7R) cuts the edge, not the losses |

What is documented, and what our data says about continuation versus mean reversion:

- **The fixes.** The LBMA Gold Price is set in two auctions, 10:30 and 15:00 London, run by ICE Benchmark Administration. Caminschi and
  Heaney (Journal of Futures Markets, 2014, "Fixing a leaky fixing") found, on GC futures and GLD before the 2014 reform, a jump in
  volume and volatility in the first minutes of the PM fixing and a direction in those minutes that predicted the fix (70 % at 15:01,
  80 % within five minutes), and nothing after publication. A University of Zurich study reports gold's mean returns around the AM and
  PM fixes as the most negative of the trading day; a Copenhagen Business School thesis (Donati and Jung) reports a "hat-shaped" intraday
  seasonality: gold rising in Asian hours and declining over the rest of the day, with drops around the fixes in the years of the alleged
  manipulation. In our 514 trades neither fix shows an effect (the AM fix falls in the break; the half hours around the PM fix turn
  between the periods), and the own-candle profile shows the hat only faintly (Asian hours +0.1 to +0.6 bp an hour, the overlap flat,
  New York afternoon -0.1 bp in 2017-2023): not tradeable by itself.
- **Intraday momentum.** The literature's "first half-hour predicts the last half-hour" result (Gao, Han, Li and Zhou, on the S&P 500
  ETF) has mixed evidence for gold: for Chinese gold futures (Bouri, Ma, Xu and Zhou) the first half-hour predicted later half hours
  only before night trading began; no rigorous study of spot gold's hourly continuation turned up. Our own evidence is about
  *multi-session* continuation: the trades that pay are held 4-24 hours or across the daily break, the ledger's winners take a median
  5 hours (IS) and reach +1R in a median 1.2-1.4 hours, and the entries that lose in both periods are the late ones (after an expanded
  day, in the hour after the London opening move, in the half hour between the US data and the equity open). The edge is a fresh zone
  early in a move, not a chase after a move.
- **Spread.** FTMO's measured gold spread in the session windows is 3.4-3.7 pips ($0.34-0.37; README, 6 October); the backtest assumes
  2.0 pips. FTMO's own symbols page renders its live spreads in the browser only (the fetch returned no table) and no dated per-hour
  figure for FTMO exists in public; the generic public picture (broker guides) is a spread two to five times wider in the 23:00-01:00
  break and the early Asian hours and briefly around 14:30 data. Entries are session-only, and the live cap refuses an entry when the
  spread exceeds 30 % of the stop (section 4). FTMO's commission on metals is 0.0007 % of the volume a side (its September 2025 trading
  update), the figure the README's "FTMO costs" use: about $2 a lot a side at today's prices, or 0.2 pips.
- **The daily break.** CME Globex trades gold Sunday 18:00 to Friday 17:00 ET with a 60-minute break from 17:00 ET: 23:00-00:00 Amsterdam
  (22:00-23:00 in the DST-mismatch weeks), exactly the data's gap (713 gaps in 2024-2026, 626 of them 22:55 -> 00:00, 54 at 21:55 ->
  23:00). FTMO's exact XAUUSD session should be read from the MT5 specification (the README asks the same for US100); the data's break
  is where the risk sits: the 99th-percentile overnight gap was $13 against a median stop of $14.8 (README, 8-9 October). The ledger
  answer is above: the trades that cross the break are the winners in both periods, so the break is a risk to size for, not to avoid.

## 3. Exits: MFE and the alternatives, both periods (5m walk, raw R)

Maximum favourable excursion, measured to the ledger's own exit:

| | IS losers (71) | OOS losers (247) | IS winners (70) | OOS winners (110) |
|---|---|---|---|---|
| MFE at least 0.25R / 0.5R / 1R / 1.5R | 77 / 59 / 20 / 8 % | 61 / 44 / 23 / 8 % | median MFE 2.10R | 2.08R |
| median MAE | | | -0.39R | -0.51R |
| MAE worse than -0.5R | | | 41 % | 51 % |
| All trades: MFE at least 1R / 1.5R / 2R / 3R | IS 59 / 47 / 35 / 8 % | OOS 49 / 34 / 22 / 6 % | | |

Half of the winners go more than half an R against the trade first; a fifth of the losers see +1R and one in twelve +1.5R.

| management (everything else as the ledger) | IS sum R (raw) | IS R a trade (after cost) | IS won | OOS sum R (raw) | OOS R a trade (after cost) | OOS won |
|---|---|---|---|---|---|---|
| **ledger: break-even at +2R, hold to the target** | **+86.1** | **+0.50** | **49 %** | **-25.1** | **-0.17** | **30 %** |
| no break-even | +84.1 | +0.49 | 49 % | -31.3 | -0.18 | 30 % |
| break-even at +1R | +57.0 | +0.30 | 37 % | -67.1 | -0.28 | 19 % |
| break-even at +1.5R | +76.2 | +0.43 | 45 % | -40.0 | -0.21 | 26 % |
| break-even at +3R | +84.1 | +0.49 | 49 % | -31.1 | -0.18 | 30 % |
| trail behind the last confirmed 15m swing after +1R (no BE) | +42.4 | +0.20 | 50 % | -43.8 | -0.22 | 37 % |
| the same trail with the 2R break-even kept | +43.4 | +0.20 | 50 % | -39.8 | -0.21 | 37 % |
| time stop: close at the market 2 h after the fill if under -0.5R | +84.1 | +0.49 | 48 % | -23.8 | -0.16 | 29 % |
| the same at 4 h | +84.0 | +0.49 | 48 % | -22.4 | -0.16 | 30 % |
| the same at 8 h | +86.4 | +0.51 | 49 % | -22.9 | -0.16 | 30 % |

- Break-even at 2R is the best of the four break-even levels in both periods: at 1R it costs 29R IS and 42R OOS (the winners' median
  adverse excursion is -0.4 to -0.5R, and the pullback after +1R takes most of them out at zero); at 3R it is the same as none.
- The 15m-swing trail wins more often (50 % / 37 %) and earns half: it cuts the 2R-plus winners (35 % of IS trades reach 2R, 8 % 3R) to
  the first 15m pullback. It turns some losers that reached +1R into small winners (hence the higher win rate), and that is worth far less than the 2R-plus winners it cuts: "smaller losses" cannot come from the trail.
- The conditional time stops move one to twenty trades and change the totals by -2R to +3R: a trade under -0.5R after 2-8 hours ends at
  about -0.7R either way. Not worth a run.
- The exit the fallback trades want is further, not nearer (section 5, candidate E): the fixed-target trades at 2.5R / 3R / 3.5R / 4R
  (break-even at 2R kept): IS +39.3 / +47.3 / +53.3 / +49.0 against +37.8 raw; OOS -23.6 / -18.8 / -16.3 / -26.8 against -37.4. At 3R
  without any break-even IS +48.3, OOS -10.4; with break-even at 1.5R +50.3 / -27.1.

## 4. Costs: the 3.7-pip spread and the stop minimum

One lot of gold is 100 oz: $10 a pip (0.1) a lot, so the extra 1.7 pips cost $17 a lot a trade, or 0.17 / stop-in-dollars R (the ledger
sizes on the stop distance exactly: risk_amount = lots x 100 x |entry - stop|). At the IS median stop ($8.50) that is 0.02R a trade; at
the OOS median ($3.23) 0.05R; at a $2 stop 0.085R; at the $1.23 stop the live cap allows 0.14R; at the 8-pip minimum ($0.80) 0.21R.

| | IS (143) | OOS (371) |
|---|---|---|
| ledger, 2-pip spread, raw | +86.1R, +0.60 a trade | -25.1R, -0.07 a trade |
| 3.7 pips, the extra charged per trade (0.17 / stop) | +82.6R (-3.5R, -0.025 a trade) | -48.6R (-23.5R, -0.063 a trade) |
| **3.7 pips walked on the 5m candles** (longs fill 0.37 over the bid, shorts stop and target on the ask) | **+78.7R, +0.55 a trade (-7.4R, -0.052 a trade)** | **-38.2R, -0.10 a trade (-13.1R, -0.035 a trade)** |
| the same with every stop under $1.23 widened to $1.23 (`min_stop_pips` 12.3) | +78.7R (none widened) | -41.0R (25 widened; worse by 2.8R) |
| the same with every stop under $1.23 refused instead (the live cap) | +78.7R (none refused) | about -24R (30 trades refused, their ledger R -14.0, 23 % won) |

- **Realistic R a trade** with the measured spread: IS +0.55R raw on the walk; the commission (0.0007 % a side, about 0.4 pips a round
  turn, 0.005R on the median stop) is noise next to it, so about +0.54R before slippage against the ledger's +0.60R raw. The 0.10R
  research haircut therefore covers the spread gap with room to spare in IS (0.05R) and is about right in OOS, where the stops are smaller
  (0.035-0.063R a trade). The ledger's +0.50 / -0.17 after the haircut is a fair live expectation; a $17-a-lot
  spread gap is not what separates the periods.
- **The stop minimum should follow the spread through the cap, not through widening.** With `max_spread_stop_fraction 0.3` and a
  3.7-pip spread the live bot refuses every stop under 12.3 pips ($1.23); 8 pips is reachable only when the spread is at most 2.4 pips.
  Widening those stops to $1.23 loses (the target stays, the R:R falls: OOS -2.8R), refusing them gains (+14R OOS, 0 trades IS). So:
  keep `min_stop_pips 8`, make the research runs carry the measured spread (`typical_spread_pips 3.7` for XAUUSD; a code constant in
  `kronos_trader/config.py`, or a `--spread` override for `PaperBroker.spread_pips`) and apply the 30 % cap in the backtest as well, so
  research refuses what live refuses. The relation to keep in mind: the minimum stop that passes the cap is spread / 0.3, 11.3-12.3 pips
  at the measured 3.4-3.7 pips; the 8-pip knob is below it and never decides.

## 5. Candidates

Each with the exact rule, the knob or the smallest code change, the expected effect and the pre-screen on both ledgers (R after the 0.10R
cost; "half" = that bucket at half the stake, the trades themselves unchanged). The permutation p-values are per period and uncorrected
for the number of cuts looked at (about 25): treat a p under 0.02 in one period plus the same sign in the other as the bar.

**A. The weak hours at half the stake.** Rule: an entry whose confirmation closes in 10:00-11:00 or 15:00-15:30 Amsterdam risks half.
Knob: none for a half stake by hour; code: `risk.hour_risk_multiplier: {"10:00-11:00": 0.5, "15:00-15:30": 0.5}` in the session's
timezone, applied where `neutral_bias_risk_multiplier` is (a dozen lines in the sizing). The ban is a knob today: `session.windows
[["09:00","10:00"],["13:00","15:00"],["15:30","17:00"]]`. Pre-screen: the bucket IS 32 trades, 31 %, -9.7R (p 0.002); OOS 86 trades, 24 %,
-29.0R (p 0.11). Half: IS +71.8 -> +76.7R (dip -9.0 -> -7.4R), OOS -62.2 -> -47.7R (dip -83 -> -73R); ban: IS +81.5R, 54 % won, dip
-5.7R; OOS -33.2R. By year the half stake is better in six years and worse in four (2019 -0.2, 2022 -2.6, 2025 -0.2, 2026 -0.3R).
Effect expected: fewer losers in the two hours where a 5m shift is a small signal inside the day's widest candles; win rate +0 (half) to
+5 points (ban). Needs code: yes for the half stake, no for the ban.

**B. Shallow entries only.** Rule: the shift's close may lie at most a quarter of the zone's height inside it. Knob: `risk.max_entry_depth:
0.25` (now 0.5). Pre-screen: the 0.25-0.5 bucket IS 18 trades, 22 %, -5.9R (p 0.015); OOS 29 trades, 24 %, -7.8R (p 0.38). Ban: IS +77.8R,
53 % won, dip -9.0 -> -5.9R; OOS -54.4R; better in eight years, worse in 2023 (-5.3R) and 2026 (-3.3R). Half (no knob): IS +3.0R, OOS +3.9R.
Caveat: an engine run can differ from the replay, since a refused deep shift may be followed by a shallower one in the same visit.
Effect expected: win rate +4 points, the dip nearly halved in IS. Needs code: no.

**C. The expanded day at half the stake.** Rule: when the last 24 closed 1H candles span more than 8 x the 1H ATR14 (the same candles
and ATR `max_adverse_move_atr` uses), the trade risks half. Knob: none; code: `risk.expanded_day_risk_multiplier: {8.0: 0.5}` next to
`max_adverse_move_atr` (the range is one line; the multiplier the same dozen lines as A), or `confirmation.max_range_24h_atr: 8.0` as a
refusal. Pre-screen: the bucket IS 30 trades, 40 %, +3.9R (+0.13 a trade, p 0.11); OOS 87 trades, 21 %, -40.0R (p 0.016), monotonic from
8 upward in OOS. Half: IS +71.8 -> +69.9R, OOS -62.2 -> -42.2R (dip -83 -> -62R); better in eight years, worse in 2025 (-2.2R) and 2026
(-1.9R). Effect expected: the chase entries (94 % of the bucket came after a move of 4 ATR or more in the trade's direction) at half;
the smallest IS cost of the four regime-type cuts. Needs code: yes (small).

**D. The ranging regime at half the stake.** Rule: when the 20-day efficiency ratio of the last closed daily bar (|close - close 20 days
ago| / the sum of the 20 daily absolute changes) is under 0.20, the trade risks half. Knob: none; code: `risk.regime_risk_multiplier:
{er20_below: 0.20, multiplier: 0.5}` on the daily closes the bias already loads (known at the day's open, so live and backtest agree).
Pre-screen: the bucket IS 59 trades, 47 %, +19.6R (+0.33 a trade, p 0.19); OOS 169 trades, 24 %, -61.4R (p 0.014). Half: IS +71.8 -> +62.0R
(dip -9.0 -> -6.6R), OOS -62.2 -> -31.5R (dip -83 -> -51R); better in seven years, worse in 2023 (-2.1R), 2025 (-2.8R) and 2026 (-7.3R).
This is the direct answer to "gold loses in ranges": it halves the out-of-sample loss for 14 % of the in-sample R, with the cost in the
best years. The regime note's 0.35 line (forming bar) was the wrong line: 0.2-0.35 is IS's best band and flat OOS. Needs code: yes.

**E. The fallback target at 3R.** Rule: where no origin target reaches the 0.8 minimum, the fixed target sits at 3R instead of 2R;
break-even at 2R as it runs. Knob: `risk.tp_fallback_rr: 3.0`. Pre-screen on the 5m walk: the fixed-target trades IS 66, +37.8R raw at 2R ->
+47.3R at 3R (won 53 % -> 41 %); OOS 191, -37.4R -> -18.8R (27 % -> 21 %). Whole ledger: IS +71.8 -> +81.3R (dip -9.0 -> -7.0R), OOS
-62.2 -> -43.6R (dip -83 -> -74R); IS halves +5.4 / +4.1R, OOS halves +10.9 / +7.6R; better in eight years, worse in 2021 (-0.9R) and
2026 (-1.1R). The sweep: 2.5R +1.5 / +13.8R, 3R +9.5 / +18.6R, 3.5R +15.5 / +21.1R, 4R +11.2 / +10.6R; 2.5R keeps more of the win rate
(44 % / 25 % on these trades). Effect expected: more R a trade, a lower win rate (IS 49 -> 43 %), fewer break-even exits turned into
2R exits. Needs code: no. (The README's 8 October test was fallback against none, not the target distance; its "target capped at 3R"
concerned the origin targets.)

**F. Research costs equal to live costs.** Rule: gold research runs carry a 3.7-pip spread and the live spread cap, `min_stop_pips` stays
8. Knob: `typical_spread_pips` is a code constant (`SymbolSpec("XAUUSD", ...)` in `kronos_trader/config.py`; a `--spread` override of
`PaperBroker.spread_pips` is the smaller change) and the cap is live-only (`max_spread_stop_fraction`: a few lines to check it in the
backtest's setup path). Pre-screen: IS the same trades, -7.4R raw (+0.55 a trade raw, the realistic figure); OOS 30 trades refused
(+14R) against -13R of spread. Expected effect: no change in the live trades, a research ledger that matches the account, and the
8-pip knob seen for what it is (the cap's 12.3 pips decides). Needs code: yes (small).

**Together.** A (half) + B + C (half) + E: IS +79.5R, 45 % won, dip -4.8R, 130 trades of which 78 at the full stake; OOS -18.8R, 27 %, dip
-43R; by year 2017 +4.6, 2018 -6.2, 2019 -6.1, 2020 -6.0, 2021 -11.4, 2022 -6.1, 2023 +12.3, 2024 +20.7, 2025 +30.0, 2026 +28.8
(ledger: -3.6, -15.7, -16.6, -12.0, -17.3, -11.7, +14.8, +13.7, +21.9, +36.3). With D on top: IS +65.2R, OOS -7.8R, dip -29R. Without C:
A + B + E IS +88.6R (dip -5.3R), OOS -28.5R. The stacked sets lose 5.6-7.5R of 2026's +36.3R and the single rules 0.3-7.3R; the gains are in the years that
look like 2017-2022. The order to run them, by evidence in both periods: E (knob), B (knob), A (ban as a knob first, the half stake when
the multiplier exists), then C and D as the stake rules for the ranging years.

## 6. Tested here and not worth a run

- Break-even at +1R, +1.5R or +3R (worse or equal in both periods); the 15m-swing trail after +1R (-44R IS, -19R OOS); time stops at
  -0.5R after 2, 4 or 8 hours (within 3R either way); a day close or weekend close (the trades across the break are the winners).
- A wider minimum stop (12.3 pips): the widened trades lose more than before; the cap's refusal is the better rule (section 4).
- Weekday, month of year, bias combination, zone timeframe, visit number, direction, the 60-day trend, the Asia range, the month at
  50/50 (the live half stake there is neutral out of sample), stop size in dollars or ATR units: each turns between the periods or is
  flat in one of them.
- Entries 13:00-14:30 against 14:30-17:00: the earlier ones are as good or better in both periods; the London PM fix and the old COMEX
  pit open leave no mark in 514 trades.

## Sources (public)

- LBMA, the LBMA Gold Price (auctions at 10:30 and 15:00 London, IBA): https://www.lbma.org.uk/prices-and-data/lbma-gold-price/lbma-gold-price and https://www.lbma.org.uk/lbma-prices-summary
- Caminschi, A. and Heaney, R. (2014), "Fixing a leaky fixing: short-term market reactions to the London PM gold price fixing", Journal of Futures Markets 34(11): https://ideas.repec.org/a/wly/jfutmk/v34y2014i11p1003-1039.html ; UWA summary: https://www.news.uwa.edu.au/201410067021/research/uwa-research-finds-gold-and-silver-price-setting-open-exploitation
- University of Zurich, returns around the gold fixings: https://www.merlin.uzh.ch/publication/show/11299
- Donati and Jung, "Gold Price Dynamics Around the Clock" (CBS thesis, the hat-shaped intraday seasonality): https://research.cbs.dk/en/studentProjects/gold-price-dynamics-around-the-clock/
- Gao, Han, Li and Zhou, "Market intraday momentum" (the first half-hour predicts the last): https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/ ; Chinese gold and metal futures before and after night trading: https://ideas.repec.org/a/eee/finlet/v58y2023ipas154461232300394x.html
- CME Group, gold futures contract specifications (Globex Sunday-Friday 18:00-17:00 ET, a 60-minute break at 17:00 ET; settlement 13:29-13:30 ET): https://cmegroup.com/trading/metals/precious/gold_contractSpecs_futures and https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-5147.html
- CFTC filing on the end of COMEX open outcry (30 December 2016): https://www.cftc.gov/filings/orgrules/rule112216comexdcm001.pdf ; Reuters/Fortune on the New York floor closing: https://fortune.com/2016/04/14/cme-new-york-trading-floor
- FTMO metals commission (0.0007 % a side, the September 2025 update, via a third-party summary) and gold trading-hours notes: https://www.camovia.com/en/blog/ftmo-xauusd-trading-hours/ ; FTMO symbols page (live spreads, renders in the browser only): https://ftmo.com/en/symbols/
- Pepperstone trading hours (server time GMT+2/+3, the rollover break): https://pepperstone.com/en/trading/trading-hours/
