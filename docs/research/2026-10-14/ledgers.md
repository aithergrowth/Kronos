# Loss anatomy on the eight research ledgers (14 October 2026)

Angle: our own trade ledgers. Which observable features separate the losers from the winners, per market, in-sample (2024-01 to 2026-09) and out-of-sample (2017 to 2023; BTC 2020-06 to 2023), and which of them give a rule that holds in both periods and is not in the live profiles yet. Scripts and raw output: `research/ledgers_anatomy.py` (features, every cut: `ledgers_anatomy.out`, the feature frame `ledgers_features.csv`), `research/ledgers_candidates.py` (candidates, per year, sensitivity, stack: `ledgers_candidates.out`). Read-only on the repository; nothing was run from inside it.

## 1. The material

The ledgers are the research form of the live profiles (1 % risk, no stake multipliers, guard off, one open trade a market, EURUSD two): `aca/eutwo_EURUSD`, `aca/base_XAUUSD`, `aca/rr08_NAS100`, `aca/base_BTCUSD` and their `oos_` twins. R is the ledger's R minus 0.10R a trade for costs (the convention of the other research pages), a win is r > 0.05. Hours are Amsterdam; the signal time is the close of the confirmation candle (`confirmed_close_at`), the fill `opened_at` (gold and BTC market orders fill on the next candle, EURUSD and NAS100 on the limit). ATR14 is of the 1H candles closed before the fill (`fixed/<SYMBOL>_1H.csv`, BTC `btc_old/BTCUSD_1H.csv`). The confirmation type is BS on every trade and its timeframe follows the zone's (1H -> 5m, 4H -> 15m), so those two features are the zone timeframe.

| market | period | trades | win | R a trade | R | largest dip |
|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +0.84 | +39.5 | -5.5R |
| EURUSD | OOS | 97 | 26 % | -0.01 | -1.2 | -24.6R |
| XAUUSD | IS | 143 | 49 % | +0.50 | +71.8 | -9.0R |
| XAUUSD | OOS | 371 | 30 % | -0.17 | -62.2 | -83.2R |
| NAS100 | IS | 43 | 47 % | +0.77 | +32.9 | -5.8R |
| NAS100 | OOS | 100 | 32 % | +0.29 | +28.8 | -11.8R |
| BTCUSD | IS | 89 | 58 % | +0.69 | +61.7 | -4.9R |
| BTCUSD | OOS | 130 | 33 % | -0.32 | -41.6 | -49.8R |

What the two periods have in common is the shape of the losers, not the level: out of sample every market but NAS100 is at or under zero, so a cut is read on its R a trade against the period's own base, and on the sign of the R it removes.

## 2. Method

Every feature is cut into buckets; each bucket shows trades, win rate, R a trade and R, in both periods, for all four markets (the full tables are in section 7). A bucket is **worse** when its R a trade sits more than 0.05R under the period's base in both periods with at least 3 trades in each, **better** when above in both; a worse bucket whose R is negative in both periods (marked `neg`) is a removal that raises the sum in both. The candidates were then checked per calendar year (ten years), for sensitivity to the threshold (a plateau, not a spike), with a permutation p-value (the share of 5,000 random subsets of the same size whose R is at or below the bucket's: how unusual a bad bucket is inside its own period) and stacked per market.

Two caveats that apply to every number here. (1) A ledger cut cannot see the slot: a refused trade frees the market for the next signal, so the backtester's re-run of a rule differs from the ledger's subtraction (NAS100's R:R 0.8 is the example: the ledger reads its R:R-under-1.0 trades as flat, the re-run of 13 October read the added trades as +8.8R out of sample). Every candidate below is a rule to re-run, with the ledger numbers as the expectation. (2) About 30 features x 4 markets x several buckets were looked at; with the both-periods rule roughly one bucket in five would flag by chance, so the candidates are ranked by n, by the size of the effect, by the permutation p in-sample and by the years helped.

## 3. What separates the losers from the winners

Medians of winners against losers (the feature frame):

| market | period | who | n | stop / ATR1H | depth in zone | dist. outside (ATR) | zone / ATR | planned R:R | target / ATR | TFs at 50/50 | zone age at touch (h) | touch -> signal (h) | hours held |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | IS | winners | 52 | 0.81 | -0.16 | 0.26 | 1.71 | 1.23 | 1.07 | 1 | 3.3 | 3.4 | 1.7 |
| BTCUSD | IS | losers | 37 | 0.82 | -0.18 | 0.38 | 1.79 | 1.81 | 1.69 | 1 | 5.2 | 0.9 | 1.5 |
| BTCUSD | OOS | winners | 43 | 1.01 | -0.24 | 0.37 | 2.18 | 1.18 | 1.20 | 1 | 2.1 | 4.9 | 1.7 |
| BTCUSD | OOS | losers | 86 | 0.88 | -0.19 | 0.29 | 1.48 | 1.56 | 1.35 | 1 | 2.8 | 5.0 | 1.3 |
| EURUSD | IS | winners | 22 | 0.68 | -0.12 | 0.16 | 1.92 | 1.60 | 2.55 | 2 | 1.2 | 2.0 | 2.9 |
| EURUSD | IS | losers | 24 | 0.90 | -0.09 | 0.18 | 1.77 | 2.83 | 2.85 | 2 | 2.8 | 1.6 | 0.5 |
| EURUSD | OOS | winners | 25 | 0.74 | -0.13 | 0.38 | 1.76 | 1.35 | 1.79 | 1 | 3.1 | 3.8 | 4.0 |
| EURUSD | OOS | losers | 68 | 0.70 | -0.03 | 0.05 | 1.71 | 2.04 | 2.09 | 2 | 1.6 | 1.9 | 0.3 |
| NAS100 | IS | winners | 20 | 0.63 | -0.30 | 0.29 | 1.22 | 1.66 | 1.82 | 0 | 1.5 | 1.7 | 2.1 |
| NAS100 | IS | losers | 23 | 0.65 | -0.12 | 0.22 | 1.95 | 1.76 | 1.87 | 1 | 1.2 | 1.9 | 0.4 |
| NAS100 | OOS | winners | 32 | 0.96 | -0.08 | 0.25 | 2.12 | 1.61 | 2.71 | 1 | 2.0 | 2.2 | 4.1 |
| NAS100 | OOS | losers | 66 | 0.76 | -0.05 | 0.10 | 1.82 | 1.87 | 2.45 | 1 | 1.4 | 1.2 | 0.6 |
| XAUUSD | IS | winners | 70 | 0.88 | -0.34 | 0.45 | 1.67 | 2.00 | 1.97 | 0 | 1.5 | 3.2 | 5.1 |
| XAUUSD | IS | losers | 71 | 0.94 | -0.22 | 0.38 | 1.62 | 2.00 | 2.06 | 0 | 1.6 | 2.3 | 1.8 |
| XAUUSD | OOS | winners | 110 | 1.11 | -0.38 | 0.59 | 1.70 | 2.00 | 1.97 | 1 | 1.8 | 2.2 | 4.5 |
| XAUUSD | OOS | losers | 247 | 1.10 | -0.35 | 0.53 | 1.55 | 2.00 | 2.45 | 1 | 1.8 | 2.7 | 1.3 |

Reading, feature by feature (the tables of section 7 carry every bucket):

- **Zone timeframe.** No cut. 4H zones are the better half on NAS100 (both periods) and on EURUSD out of sample, the worse on BTC; 1H zones carry the trade count everywhere.
- **Bias combination.** EURUSD's 1D+1H pair is under the base in both periods (34 trades +0.53 / 65 trades -0.09) but positive in-sample: that is the half-stake rule already in the profile. Gold's four combinations sit within 0.2R of each other in both periods; BTC's 1M+1D+1H is the best in both (10 trades +1.77 / 7 trades +0.44), its D+4H+1H scalp the worst (24, +0.07 / 45, -0.27), still positive in-sample.
- **Direction.** BTC longs and EURUSD shorts are under the base in both periods (BTC longs 62, +0.39 / 59, -0.52; EURUSD shorts 21, +0.53 / 54, -0.33) but positive in-sample, so no direction is switched off; the EURUSD angle's Asia-range rule is the shape of that short problem.
- **Hour of the signal.** The one hour that loses in both periods on more than one market is 15:00-16:00 (EURUSD 7 trades -1.3R / 12 trades -4.6R; gold's first half-hour 11 trades -3.7R / 20 trades -6.9R; BTC under the base both, negative out of sample), but NAS100's 15:00 hour is +21.4R out of sample, so it is not a four-market rule. Per market: **gold's 10:00-11:00 hour** loses in both periods and in both half-hours (21 trades, 33 %, -5.9R; 66 trades, 24 %, -22.1R; candidate A); **BTC's 16:00-17:00** likewise (11 trades -3.9R; 13 trades -4.2R; candidate C); EURUSD's 09:30-10:00 and 14:30-16:00 (the EURUSD angle's candidates, cross-checked here: the 14:30-16:00 cut is EURUSD-only, gold's 14:30-16:00 is +16.6R in-sample).
- **Weekday.** Nothing that holds across markets: BTC's Wednesday and NAS100's Tuesday are under the base in both periods but positive in-sample; the other markets' worst weekday changes between the periods. No rule.
- **Month of the year.** Noise at these sizes: no month is under the base on more than one market in both periods, and the in-sample months hold 1-18 trades. Gold's September and November are negative in both periods (-2.7 / -3.8R and -1.3 / -11.4R) and nothing else is. No rule.
- **Planned R:R band.** Gold with an origin target under 2R (the band between the 0.8 minimum and the 2R fallback) is flat in-sample (38 trades, -1.8R) and -10.8R on 90 trades out of sample; the README's min R:R 1.2 / 1.5 runs with the fallback already measured that re-targeting (+81.4R / +74.8R against +84.2R), so it stays. NAS100 under 1.5 is flat in-sample (17 trades -0.1R) and -3.4R out of sample (near miss J, against the 13 October re-run). EURUSD's 4-6R targets lost 14 of 14 across both periods while 6R and up won big: no monotonic rule.
- **Stop against the 1H ATR.** Only EURUSD has a tight-stop problem: stops under 0.5 ATR won 2 of 20 trades across both periods (5, -2.3R; 15, -11.8R; candidate D, the EURUSD angle's `min_stop_atr`). On gold, NAS100 and BTC the same floor would remove R in both periods or in-sample (gold +5.2 / +1.4R, NAS100 +12.3 / +2.4R, BTC +30.4 / -3.7R), so the floor is EURUSD's only. Above that the buckets are not monotonic on any market.
- **Visit number.** Second and third visits are 3-8 % of the trades (EURUSD, gold) and carry no signal either way.
- **Depth of the entry in the zone.** Entries in the deepest allowed quarter (25-50 % of the zone's height) lose in both periods on gold (16 trades -3.7R; 28 trades -6.7R) and NAS100 (7, -3.5R; 12, -4.7R): candidate B. On BTC the same quarter holds +36.8R of the in-sample R (10 trades, 90 % won), on EURUSD +8.9R: not there.
- **Distance of the entry outside the zone (in ATR).** No monotonic pattern: BTC's entries 0-0.5 ATR outside are under the base in both periods, its entries inside the zone the best; gold alternates bucket by bucket. No rule from this feature; `max_entry_outside` stays off.
- **Which timeframes read 50/50.** The month at 50/50 is under the base in both periods on BTC, EURUSD and NAS100 (the half stake already in the profiles). The week at 50/50 is not consistent (better on gold and BTC in both periods, worse on NAS100). All five timeframes aligned is under the base in both periods on gold (32 trades +0.29 / 29 trades -0.33) and BTC (13, +0.02 / 13, -0.67): near miss H, the `aligned_count_risk_multiplier` knob of 14 October; it fails the in-sample test on gold (+9.4R removed).
- **Consecutive losses before the trade.** No state predicts the next trade in both periods: after 3 or more losses EURUSD and NAS100 do better in both periods, gold better in-sample and at the base out of sample, BTC better in-sample (3 trades) and worse out of sample. After a loss the next trade is at or above the base in-sample on every market and 0.1-0.4R under it out of sample on three: nothing to act on. A pause or a smaller stake after losses has nothing to pick (as the README of 8 October found on the account).
- **Touch to signal.** A confirmation that closes within 30 minutes of the visit's first touch loses in both periods on gold (14 trades, 21 %, -4.7R; 59 trades, 31 %, -8.4R) and BTC (19 trades, 32 %, -7.0R; 14 trades, 29 %, -6.0R): candidate F. On NAS100 and EURUSD those quick shifts are winners in-sample.
- **Zone age at the touch** (under the 24 h rule already): nothing monotonic within the day.
- **Stop beyond the zone's far edge** (the sweep ran through the whole zone): gold 7 trades -2.2R / 37 trades -4.7R, NAS100 2 / 12 trades -3.3R out of sample: candidate E, weak.
- **Target against the 1H ATR.** Gold targets under one ATR away lose in both periods (24 trades -1.4R; 47 trades -8.2R): candidate G, narrow.
- **Hours held** is an outcome (the losers die in the first hour on every market), not a filter.

## 4. The candidates

Each row: the rule, the knob, what it removes in both periods (trades, win rate, R), the permutation p in-sample, the years it helped / hurt (of the years with a removed trade), and the result after it. All four markets were checked for every rule; the markets named are the ones where it holds in both periods.

| # | rule | knob | markets | IS removed | OOS removed | p (IS) | years helped / hurt | IS after | OOS after |
|---|---|---|---|---|---|---|---|---|---|
| A | no signal 10:00-10:59 Amsterdam | `session.windows: [[09:00, 10:00], [13:00, 17:00]]` | XAUUSD | 21 tr, 33 %, -5.9R | 66 tr, 24 %, -22.1R | 0.012 | 6 / 4 | 122 tr, 52 %, +0.64, +77.7R, dip -6.8R | 305 tr, 31 %, -0.13, -40.2R |
| F | no signal whose confirmation closes within 30 min of the visit's first touch | new `confirmation.min_visit_age_minutes: 30` (the lower bound of the `since_touch` the `max_visit_age` check already computes) | XAUUSD, BTCUSD | gold 14 tr, 21 %, -4.7R; BTC 19 tr, 32 %, -7.0R | gold 59 tr, 31 %, -8.4R; BTC 14 tr, 29 %, -6.0R | 0.030 / 0.004 | gold 7 / 3, BTC 5 / 2 | gold +76.5R (dip -6.8R), BTC 70 tr, 66 %, +0.98, +68.7R | gold -53.8R, BTC -35.6R |
| D | stop at least 0.5 x ATR14 of the 1H, else no trade | `risk.min_stop_atr: 0.5` (`min_stop_atr_tf: 1H`; in the code since 14 October) | EURUSD | 5 tr, 20 %, -2.3R | 15 tr, 7 %, -11.8R | 0.091 | 6 / 1 | 42 tr, 50 %, +1.00, +41.8R | 82 tr, 29 %, +0.13, +10.6R, dip -13.9R |
| B | entry at most a quarter of the zone deep | `risk.max_entry_depth: 0.25` (now 0.5) | XAUUSD (NAS100 weakly) | gold 16 tr, 25 %, -3.7R; NAS100 9 tr, 22 %, -0.5R | gold 28 tr, 25 %, -6.7R; NAS100 15 tr, 27 %, -2.0R | 0.041 / 0.116 | gold 8 / 2, NAS100 5 / 5 | gold 127 tr, 52 %, +0.59, +75.6R (dip -5.9R); NAS100 34 tr, 53 %, +0.98, +33.4R | gold -55.5R; NAS100 +30.8R |
| C | no signal 16:00-16:59 Amsterdam | `session.windows: [[09:00, 11:00], [13:00, 16:00]]` | BTCUSD | 11 tr, 36 %, -3.9R | 13 tr, 38 %, -4.2R | 0.029 | 4 / 3 | 78 tr, 62 %, +0.84, +65.6R, dip -3.3R | 117 tr, -37.4R |
| G | target at least one ATR14 of the 1H from the entry, else no trade | new `risk.min_tp_atr: 1.0` | XAUUSD | 24 tr, 46 %, -1.4R | 47 tr, 40 %, -8.2R | 0.048 | 7 / 3 | 119 tr, 50 %, +0.62, +73.3R | 324 tr, -54.0R |
| E | no trade when the stop lies beyond the zone's far edge | new `confirmation.stop_within_zone: true` | XAUUSD | 7 tr, 29 %, -2.2R | 37 tr, 30 %, -4.7R | 0.099 | 5 / 4 | 136 tr, +74.0R | 334 tr, -57.5R |
| K | no signal 14:30-15:59 (the EURUSD angle's rule, cross-checked) | `session.windows: [[09:00, 11:00], [13:00, 14:30], [16:00, 17:00]]` | EURUSD only (gold's slot is +16.6R in-sample) | 11 tr, 18 %, -5.7R | 15 tr, 27 %, -5.2R | 0.008 | 6 / 3 | 36 tr, 56 %, +1.26, +45.3R, dip -3.3R | 82 tr, +3.9R |

### Sensitivity (R removed in-sample / out of sample; the rule holds where both are negative)

| rule | threshold | XAUUSD | BTCUSD | EURUSD | NAS100 |
|---|---|---|---|---|---|
| A: signal window removed | 09:30-11:00 | +10.8 / -32.7 | +47.3 / -1.9 | +2.2 / -6.8 | +8.4 / -3.4 |
| | 10:00-10:30 | -4.5 / -11.7 | +2.6 / -4.8 | +0.8 / -2.6 | -1.1 / -3.9 |
| | 10:30-11:00 | -1.4 / -10.4 | +1.6 / -4.8 | +1.9 / +2.3 | +7.5 / +2.0 |
| | **10:00-11:00** | **-5.9 / -22.1** | +4.1 / -9.5 | +2.7 / -0.3 | +6.4 / -1.8 |
| | 15:00-15:30 | -3.7 / -6.9 | +3.9 / -3.9 | -0.2 / -2.5 | -4.4 / +14.2 |
| B: max depth | 0.15 | -0.8 / +0.5 | +40.3 / -7.2 | +16.2 / -13.3 | +0.9 / -4.7 |
| | 0.20 | -2.2 / -2.1 | +39.1 / -6.1 | +15.7 / -9.9 | -0.5 / -3.1 |
| | **0.25** | **-3.7 / -6.7** | +36.8 / -6.0 | +12.4 / -7.2 | **-0.5 / -2.0** |
| | 0.30 | -3.2 / -11.2 | +32.0 / -5.0 | +2.4 / -6.1 | +1.7 / -0.9 |
| | 0.35 | +0.3 / -7.5 | +5.6 / -3.4 | +3.5 / -6.9 | +2.8 / -5.1 |
| C: signal window removed | 15:30-17:00 | +18.3 / -13.6 | -3.2 / -11.6 | +27.8 / -13.1 | +5.2 / +7.7 |
| | 16:00-16:30 | +7.0 / -0.3 | -2.4 / -2.7 | +13.2 / -3.4 | 0 / -2.3 |
| | 16:30-17:00 | +2.9 / +1.2 | -1.5 / -1.6 | +15.7 / -7.7 | +2.4 / +2.8 |
| | **16:00-17:00** | +9.9 / +0.8 | **-3.9 / -4.2** | +28.9 / -11.1 | +2.4 / +0.5 |
| D: min stop / ATR | 0.40 | -0.2 / +0.6 | +27.4 / -2.1 | -1.2 / +1.4 | +5.0 / +2.4 |
| | 0.45 | -1.6 / +3.1 | +31.6 / +1.0 | -1.2 / -4.1 | +9.6 / +8.7 |
| | **0.50** | +5.2 / +1.4 | +30.4 / -3.7 | **-2.3 / -11.8** | +12.3 / +2.4 |
| | 0.55 | +14.2 / +6.9 | +30.3 / -6.5 | -0.3 / -13.2 | +13.9 / +2.5 |
| | 0.60 | +22.8 / +4.8 | +34.3 / -11.4 | +11.9 / -19.8 | +18.0 / +8.7 |
| F: min minutes touch -> signal | 15 | -0.4 / +3.0 | -5.6 / -0.3 | +6.6 / +2.0 | -1.1 / -4.4 |
| | 20 | -2.4 / -8.8 | -6.8 / -1.7 | +3.3 / -2.5 | +0.5 / +1.1 |
| | **30** | **-4.7 / -8.4** | **-7.0 / -6.0** | +4.4 / -8.0 | +9.9 / +13.2 |
| | 45 | +4.0 / -7.1 | +7.1 / -8.9 | +6.4 / -17.9 | +9.2 / +15.1 |
| | 60 | +13.8 / -14.2 | +7.3 / -6.5 | +13.8 / -16.9 | +20.5 / +16.7 |
| G: min target / ATR | 0.75 | +1.5 / -8.4 | +10.3 / -3.5 | 0 / 0 | +1.0 / -0.7 |
| | **1.00** | **-1.4 / -8.2** | +10.5 / -10.8 | +2.1 / +2.6 | +1.0 / -2.6 |
| | 1.25 | +3.6 / -3.4 | +19.8 / -18.4 | +3.6 / +5.3 | +0.2 / -4.5 |

What the grid says: A is a plateau over both half-hours and stops sharply at 10:00 (the 09:30-10:00 slot is +16.7R in-sample on gold); B holds on
gold from 0.20 to 0.30; D holds on EURUSD from 0.45 to 0.55; C holds on both BTC half-hours; F holds at 20 and 30 minutes and breaks at 45 on
both markets (a narrow plateau: the loss sits in the shifts that close 10-30 minutes after the touch); G holds only at 1.0 (0.75 and 1.25 fail
in-sample). Ranked by the evidence: A, F, D, B, C, then G and E.

### Per year (R of the removed trades; negative = the year improved)

| rule | market | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | XAUUSD | +0.3 | -5.4 | +1.5 | -8.0 | -7.3 | +3.4 | -6.6 | -6.2 | -1.2 | +1.5 |
| B | XAUUSD | -2.2 | -3.3 | -2.2 | -2.3 | -0.4 | -1.7 | +5.3 | -2.7 | -4.2 | +3.2 |
| B | NAS100 | +1.4 | -1.1 | -2.2 | +1.3 | -4.4 | +0.6 | +2.3 | +3.1 | -1.3 | -2.2 |
| C | BTCUSD | | | | -1.1 | -3.9 | -1.4 | +2.2 | -5.1 | +0.4 | +0.7 |
| D | EURUSD | 0 | 0 | -2.2 | +0.4 | -2.2 | -6.7 | -1.1 | 0 | -1.2 | -1.1 |
| E | XAUUSD | -1.3 | +1.4 | -1.6 | +1.5 | -1.5 | -9.9 | +6.7 | -3.3 | +1.1 | 0 |
| F | XAUUSD | -4.4 | -7.9 | -1.1 | +0.9 | -1.9 | +9.4 | -3.3 | -7.0 | -0.9 | +3.2 |
| F | BTCUSD | | | | +2.5 | -2.8 | -4.4 | -1.3 | -5.6 | -1.9 | +0.5 |
| G | XAUUSD | -1.7 | +3.2 | -0.2 | -1.7 | -3.3 | -5.2 | +0.8 | -2.1 | -0.2 | +0.8 |

2026 is the year the gold rules give something back (A +1.5R, B +3.2R, F +3.2R, G +0.8R, E 0): the rules trim 2024-2025 and the out-of-sample
years, not the best year. That is the expected shape of a loss filter and also the reason to re-run before adopting: 2026 is where the live edge is.

### The stack per market

| market | rules | IS before | IS after | OOS before | OOS after | years better / worse |
|---|---|---|---|---|---|---|
| XAUUSD | A+B+E+F+G | 143 tr, 49 %, +0.50, +71.8R, dip -9.0R | 78 tr, 63 %, +1.09, +84.9R, dip -4.4R | 371 tr, 30 %, -0.17, -62.2R, dip -83.2R | 189 tr, 26 %, -0.24, -45.8R, dip -61.2R | 6 / 4 |
| NAS100 | B | 43 tr, 47 %, +0.77, +32.9R, dip -5.8R | 34 tr, 53 %, +0.98, +33.4R, dip -3.3R | 100 tr, 32 %, +0.29, +28.8R | 85 tr, 33 %, +0.36, +30.8R | 5 / 5 |
| BTCUSD | C+F | 89 tr, 58 %, +0.69, +61.7R, dip -4.9R | 64 tr, 69 %, +1.11, +70.8R, dip -3.3R | 130 tr, 33 %, -0.32, -41.6R | 105 tr, 32 %, -0.32, -33.5R | 4 / 3 |
| EURUSD | D | 47 tr, 47 %, +0.84, +39.5R | 42 tr, 50 %, +1.00, +41.8R | 97 tr, 26 %, -0.01, -1.2R, dip -24.6R | 82 tr, 29 %, +0.13, +10.6R, dip -13.9R | 6 / 1 |

The gold stack removes 45 % of the in-sample trades for +13.1R; its out-of-sample R a trade falls (-0.17 -> -0.24) while the sum rises, which
says the five rules overlap on the same bad trades and the remainder is not better per trade out of sample. Taken one at a time the order is
A, F, B (then G, E only if the re-run agrees). The challenge needs trades as well as R: at 1.5 % and 4H zones x2, gold's in-sample stack
turns 143 trades into 78 over 33 months (2.4 a month instead of 4.3), so the account replay (`scripts/risk_steps.py`) decides, not this table.

## 5. Correlation of daily R between the markets

R after costs summed by the day the trade closed (Amsterdam); Pearson on all calendar days with zero where a market had no trade, on the
days when at least one market traded, on weekly and on monthly sums.

| period | pair | daily (all days) | daily (trading days) | weekly | monthly | shared days | both lost / both won on shared days |
|---|---|---|---|---|---|---|---|
| IS | EURUSD / XAUUSD | -0.02 | -0.04 | +0.11 | -0.13 | 11 | 18 % / 18 % |
| IS | EURUSD / NAS100 | +0.03 | +0.02 | +0.08 | +0.29 | 5 | 20 % / 60 % |
| IS | EURUSD / BTCUSD | -0.03 | -0.04 | +0.03 | +0.08 | 6 | 17 % / 0 % |
| IS | XAUUSD / NAS100 | -0.04 | -0.06 | +0.05 | +0.26 | 5 | 0 % / 20 % |
| IS | XAUUSD / BTCUSD | +0.09 | +0.08 | +0.09 | +0.20 | 19 | 26 % / 53 % |
| IS | NAS100 / BTCUSD | +0.05 | +0.03 | 0.00 | -0.07 | 8 | 0 % / 38 % |
| OOS | EURUSD / XAUUSD | -0.01 | -0.01 | -0.04 | -0.19 | 22 | 50 % / 9 % |
| OOS | EURUSD / NAS100 | 0.00 | 0.00 | +0.01 | -0.01 | 5 | 60 % / 0 % |
| OOS | EURUSD / BTCUSD | +0.02 | +0.02 | -0.04 | -0.06 | 8 | 38 % / 25 % |
| OOS | XAUUSD / NAS100 | 0.00 | 0.00 | +0.01 | +0.02 | 25 | 64 % / 0 % |
| OOS | XAUUSD / BTCUSD | -0.02 | -0.03 | -0.08 | -0.05 | 22 | 41 % / 9 % |
| OOS | NAS100 / BTCUSD | +0.01 | +0.02 | -0.06 | -0.11 | 10 | 50 % / 10 % |

- Daily and weekly correlations are inside +-0.11 in both periods: the four markets' trades are independent bets at the horizon the FTMO
  daily limit works on. The monthly in-sample correlations of 0.2-0.3 (EURUSD/NAS100, gold/NAS100, gold/BTC) are what 32 months of a shared
  trend regime give; they vanish out of sample.
- Days with trades in two or more markets: 44 of 244 trading days in-sample (18 %), 78 of 548 out of sample (14 %); three or more: 5 and 7.
  On the shared days both markets lost 0-26 % of the time in-sample and 38-64 % out of sample, which is what the periods' win rates (50 % and
  30 %) make of independent draws: no clustering of losses beyond chance.
- When two markets signal the same direction on the same day the trades are better in both periods (same direction: +1.28R a trade on 74
  trades in-sample, -0.10R on 84 out of sample; mixed directions +0.59R on 23 and -0.25R on 102). A correlation rule would cut the better
  days; none is proposed.
- Account level, the daily sum over the four markets (1 % units): in-sample 9 of 244 trading days at -2R or worse, one at -3R, the worst
  -3.3R; out of sample 58 of 548 at -2R, 7 at -3R, 4 at -4R, the worst -5.5R. The FTMO day limit (4 % at 1.5 % a trade is 2.7R; with a 4H
  zone at twice the stake a single trade can be 3R) is reached by a bad day of two or three stops, not by correlated markets. After the stack:
  6 / 0 / 0 in-sample (worst -2.2R), 32 / 6 / 2 out of sample (worst -4.4R).

## 6. Negative results, kept so they are not run again

- Consecutive losses before a trade (0, 1, 2, 3+): no bucket is under the base in both periods on any market except NAS100's 2-3 losses
  (7 trades -0.5R; 28 trades -4.6R), while its 3+ bucket is +8.9R / +20.2R. The previous trade's result does not predict the next one
  (after a loss: BTC +0.85 / -0.44, EURUSD +1.15 / +0.02, NAS100 +0.97 / +0.24, gold +0.51 / -0.19 a trade, each at or above the base
  in-sample). No pause and no stake step after losses.
- Weekday: no weekday is under the base in both periods on more than one market; the worst weekday changes between the periods on every
  market (BTC Wednesday / Wednesday is the one match, +6.5R in-sample).
- Month of the year: 1-18 in-sample trades a cell; no month holds across markets. Gold's September and November are negative in both periods,
  BTC's August to November under the base in both periods, with -0.3R to +7.1R in-sample. Not a rule at these sizes.
- Visit number, zone timeframe, bias combination, direction: no removal that is negative in both periods.
- Distance of the entry outside the zone (`max_entry_outside`): not monotonic on any market.
- Zone height against the ATR: NAS100's 1-2 ATR zones are flat in-sample and -16.9R out of sample, gold's 1.5-2 ATR zones flat in both;
  nothing monotonic.
- The daily against the trade on gold (near miss I): 14 trades +1.6R in-sample, 53 trades -16.8R out of sample, 7 of 10 years helped. It
  fails the in-sample test by 1.6R; a `bias.no_trade_against: [1D]` on gold is the first thing to re-run if the 2017-2023 column ever decides.
- All five timeframes aligned at a reduced stake (near miss H, `risk.aligned_count_risk_multiplier`): gold 32 trades +0.29 a trade in-sample
  (+9.4R), 29 trades -0.33 out of sample; BTC 13 trades +0.02 and 13 trades -0.67. The in-sample R is positive on gold, so the half stake
  costs 4.7R there; on BTC alone it is flat in-sample and +8.7R out of sample. Not a candidate under the both-periods rule.
- NAS100 planned R:R under 1.5 (near miss J): flat in-sample (17 trades -0.1R, p 0.036), -3.4R out of sample, 4 of 9 years helped, and the
  re-run of 13 October read the 0.8-1.0 trades as +8.8R out of sample once the slot effect is counted. Left as it is.

## 7. Every cut, both periods, four markets

Columns: trades, win rate (%), R a trade, R, for the in-sample (IS) and the out-of-sample (OOS) ledgers; `both` marks a bucket under the base in both periods with at least 3 trades each (`neg` when its R is negative in both) or above in both. Base R a trade: EURUSD +0.84 / -0.01, XAUUSD +0.50 / -0.17, NAS100 +0.77 / +0.29, BTCUSD +0.69 / -0.32.


#### Zone timeframe

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 1H | 67 | 60 | 0.84 | 56.4 | 100 | 31 | -0.38 | -37.8 |  |
| BTCUSD | 4H | 22 | 55 | 0.24 | 5.3 | 30 | 40 | -0.13 | -3.8 |  |
| EURUSD | 1H | 37 | 49 | 0.95 | 35.3 | 87 | 20 | -0.37 | -32.4 |  |
| EURUSD | 4H | 10 | 40 | 0.43 | 4.3 | 10 | 80 | 3.12 | 31.2 |  |
| NAS100 | 1H | 38 | 47 | 0.72 | 27.2 | 93 | 30 | 0.23 | 21.4 | worse |
| NAS100 | 4H | 5 | 40 | 1.15 | 5.7 | 7 | 57 | 1.05 | 7.4 | better |
| XAUUSD | 1H | 130 | 48 | 0.44 | 57.7 | 323 | 30 | -0.16 | -50.7 |  |
| XAUUSD | 4H | 13 | 62 | 1.08 | 14.1 | 48 | 25 | -0.24 | -11.5 |  |

#### Bias combination

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 1D+4H+1H | 24 | 54 | 0.07 | 1.7 | 45 | 36 | -0.27 | -12.1 |  |
| BTCUSD | 1M+1D+1H | 10 | 70 | 1.77 | 17.7 | 7 | 71 | 0.44 | 3.1 | better |
| BTCUSD | 1M+1D+4H | 11 | 64 | 0.57 | 6.3 | 2 | 50 | -0.10 | -0.2 |  |
| BTCUSD | 1M+1W+1D | 44 | 57 | 0.82 | 36.0 | 76 | 28 | -0.43 | -32.4 |  |
| EURUSD | 1D+1H | 34 | 41 | 0.53 | 18.0 | 65 | 23 | -0.09 | -6.0 | worse |
| EURUSD | 1M+1D+1H | 9 | 56 | 1.04 | 9.4 | 10 | 30 | 0.32 | 3.2 | better |
| EURUSD | 1M+1W+1D | 4 | 75 | 3.04 | 12.2 | 22 | 32 | 0.07 | 1.5 | better |
| NAS100 | 1D+4H+1H | 10 | 40 | 0.46 | 4.6 | 21 | 38 | 0.25 | 5.2 |  |
| NAS100 | 1M+1D+1H | 6 | 50 | 1.83 | 11.0 | 23 | 35 | 0.20 | 4.7 |  |
| NAS100 | 1M+1W+1D | 27 | 48 | 0.64 | 17.3 | 56 | 29 | 0.34 | 18.9 |  |
| XAUUSD | 1D+1H | 33 | 39 | 0.31 | 10.2 | 151 | 30 | -0.13 | -20.0 |  |
| XAUUSD | 1M+1D+1H | 12 | 75 | 1.08 | 12.9 | 50 | 30 | -0.20 | -10.0 |  |
| XAUUSD | 1M+1W+1D | 49 | 47 | 0.48 | 23.3 | 52 | 21 | -0.28 | -14.4 |  |
| XAUUSD | 4H+1H | 49 | 51 | 0.52 | 25.5 | 118 | 32 | -0.15 | -17.8 |  |

#### Direction

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | LONG | 62 | 58 | 0.39 | 24.0 | 59 | 25 | -0.52 | -30.6 | worse |
| BTCUSD | SHORT | 27 | 59 | 1.40 | 37.7 | 71 | 39 | -0.15 | -11.0 | better |
| EURUSD | LONG | 26 | 50 | 1.09 | 28.4 | 43 | 33 | 0.39 | 16.7 | better |
| EURUSD | SHORT | 21 | 43 | 0.53 | 11.1 | 54 | 20 | -0.33 | -17.9 | worse |
| NAS100 | LONG | 36 | 44 | 0.69 | 25.0 | 74 | 31 | 0.30 | 22.1 |  |
| NAS100 | SHORT | 7 | 57 | 1.13 | 7.9 | 26 | 35 | 0.26 | 6.7 |  |
| XAUUSD | LONG | 110 | 47 | 0.43 | 47.6 | 190 | 32 | -0.07 | -13.2 |  |
| XAUUSD | SHORT | 33 | 55 | 0.73 | 24.2 | 181 | 28 | -0.27 | -49.0 |  |

#### Hour of the signal (confirmation close, Amsterdam)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 9 | 27 | 67 | 1.82 | 49.3 | 36 | 31 | -0.34 | -12.2 |  |
| BTCUSD | 10 | 15 | 60 | 0.28 | 4.1 | 23 | 30 | -0.41 | -9.5 | worse |
| BTCUSD | 13 | 13 | 38 | 0.02 | 0.2 | 29 | 31 | -0.34 | -9.8 |  |
| BTCUSD | 14 | 15 | 67 | 0.50 | 7.4 | 14 | 57 | 0.38 | 5.3 |  |
| BTCUSD | 15 | 8 | 75 | 0.57 | 4.5 | 15 | 20 | -0.75 | -11.2 | worse |
| BTCUSD | 16 | 11 | 36 | -0.35 | -3.9 | 13 | 38 | -0.33 | -4.2 |  |
| EURUSD | 9 | 9 | 33 | 0.19 | 1.7 | 25 | 24 | -0.20 | -4.9 | worse |
| EURUSD | 10 | 4 | 50 | 0.69 | 2.7 | 20 | 25 | -0.02 | -0.3 |  |
| EURUSD | 13 | 7 | 29 | 0.16 | 1.1 | 18 | 44 | 0.59 | 10.7 |  |
| EURUSD | 14 | 7 | 29 | 0.92 | 6.4 | 11 | 27 | 0.82 | 9.0 | better |
| EURUSD | 15 | 7 | 29 | -0.19 | -1.3 | 12 | 25 | -0.38 | -4.6 | worse (neg) |
| EURUSD | 16 | 13 | 85 | 2.22 | 28.9 | 11 | 0 | -1.01 | -11.1 |  |
| NAS100 | 9 | 9 | 44 | 0.89 | 8.0 | 17 | 18 | -0.59 | -10.1 |  |
| NAS100 | 10 | 7 | 57 | 0.91 | 6.4 | 17 | 29 | -0.11 | -1.8 |  |
| NAS100 | 13 | 13 | 54 | 1.53 | 19.8 | 21 | 33 | 0.91 | 19.1 | better |
| NAS100 | 14 | 5 | 20 | -0.42 | -2.1 | 13 | 31 | -0.02 | -0.2 | worse (neg) |
| NAS100 | 15 | 8 | 38 | -0.20 | -1.6 | 18 | 44 | 1.19 | 21.4 |  |
| NAS100 | 16 | 1 | 100 | 2.40 | 2.4 | 14 | 36 | 0.04 | 0.5 |  |
| XAUUSD | 9 | 31 | 48 | 0.57 | 17.6 | 86 | 29 | -0.10 | -8.4 | better |
| XAUUSD | 10 | 21 | 33 | -0.28 | -5.9 | 66 | 24 | -0.33 | -22.1 | worse (neg) |
| XAUUSD | 13 | 28 | 46 | 0.61 | 17.2 | 57 | 28 | -0.15 | -8.8 |  |
| XAUUSD | 14 | 24 | 62 | 1.18 | 28.4 | 55 | 35 | -0.04 | -2.4 | better |
| XAUUSD | 15 | 19 | 47 | 0.25 | 4.7 | 48 | 23 | -0.44 | -21.4 | worse |
| XAUUSD | 16 | 20 | 55 | 0.49 | 9.9 | 59 | 39 | 0.01 | 0.8 |  |

#### Half hour of the signal

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [9.0, 9.5) | 17 | 59 | 0.36 | 6.1 | 18 | 0 | -1.10 | -19.8 | worse |
| BTCUSD | [9.5, 10.0) | 10 | 80 | 4.31 | 43.1 | 18 | 61 | 0.42 | 7.6 | better |
| BTCUSD | [10.0, 10.5) | 10 | 60 | 0.26 | 2.6 | 14 | 29 | -0.34 | -4.8 |  |
| BTCUSD | [10.5, 11.0) | 5 | 60 | 0.32 | 1.6 | 9 | 33 | -0.53 | -4.8 | worse |
| BTCUSD | [13.0, 13.5) | 5 | 40 | -0.47 | -2.3 | 15 | 40 | -0.07 | -1.0 |  |
| BTCUSD | [13.5, 14.0) | 8 | 38 | 0.32 | 2.6 | 14 | 21 | -0.62 | -8.7 | worse |
| BTCUSD | [14.0, 14.5) | 7 | 57 | 0.17 | 1.2 | 3 | 100 | 2.27 | 6.8 |  |
| BTCUSD | [14.5, 15.0) | 8 | 75 | 0.78 | 6.3 | 11 | 45 | -0.14 | -1.5 | better |
| BTCUSD | [15.0, 15.5) | 4 | 100 | 0.97 | 3.9 | 5 | 20 | -0.78 | -3.9 |  |
| BTCUSD | [15.5, 16.0) | 4 | 50 | 0.17 | 0.7 | 10 | 20 | -0.73 | -7.3 | worse |
| BTCUSD | [16.0, 16.5) | 7 | 43 | -0.35 | -2.4 | 8 | 38 | -0.33 | -2.7 |  |
| BTCUSD | [16.5, 17.01) | 4 | 25 | -0.36 | -1.5 | 5 | 40 | -0.31 | -1.6 |  |
| EURUSD | [9.0, 9.5) | 3 | 33 | 0.72 | 2.2 | 10 | 30 | 0.16 | 1.6 |  |
| EURUSD | [9.5, 10.0) | 6 | 33 | -0.08 | -0.5 | 15 | 20 | -0.43 | -6.4 | worse (neg) |
| EURUSD | [10.0, 10.5) | 2 | 50 | 0.41 | 0.8 | 8 | 12 | -0.33 | -2.6 |  |
| EURUSD | [10.5, 11.0) | 2 | 50 | 0.96 | 1.9 | 12 | 33 | 0.19 | 2.3 |  |
| EURUSD | [13.0, 13.5) | 5 | 40 | 0.66 | 3.3 | 12 | 58 | 1.21 | 14.5 |  |
| EURUSD | [13.5, 14.0) | 2 | 0 | -1.10 | -2.2 | 6 | 17 | -0.64 | -3.9 |  |
| EURUSD | [14.0, 14.5) | 3 | 67 | 3.60 | 10.8 | 8 | 25 | 1.19 | 9.5 | better |
| EURUSD | [14.5, 15.0) | 4 | 0 | -1.10 | -4.4 | 3 | 33 | -0.19 | -0.6 | worse (neg) |
| EURUSD | [15.0, 15.5) | 6 | 33 | -0.04 | -0.2 | 5 | 20 | -0.51 | -2.5 | worse (neg) |
| EURUSD | [15.5, 16.0) | 1 | 0 | -1.10 | -1.1 | 7 | 29 | -0.29 | -2.0 |  |
| EURUSD | [16.0, 16.5) | 6 | 83 | 2.20 | 13.2 | 4 | 0 | -0.85 | -3.4 |  |
| EURUSD | [16.5, 17.01) | 7 | 86 | 2.25 | 15.7 | 7 | 0 | -1.10 | -7.7 |  |
| NAS100 | [9.0, 9.5) | 4 | 50 | 1.49 | 6.0 | 13 | 15 | -0.66 | -8.6 |  |
| NAS100 | [9.5, 10.0) | 5 | 40 | 0.40 | 2.0 | 4 | 25 | -0.39 | -1.5 | worse |
| NAS100 | [10.0, 10.5) | 1 | 0 | -1.10 | -1.1 | 9 | 22 | -0.43 | -3.9 |  |
| NAS100 | [10.5, 11.0) | 6 | 67 | 1.25 | 7.5 | 8 | 38 | 0.25 | 2.0 |  |
| NAS100 | [13.0, 13.5) | 5 | 80 | 2.62 | 13.1 | 17 | 35 | 1.24 | 21.0 | better |
| NAS100 | [13.5, 14.0) | 8 | 38 | 0.84 | 6.8 | 4 | 25 | -0.47 | -1.9 |  |
| NAS100 | [14.0, 14.5) | 3 | 0 | -1.10 | -3.3 | 6 | 50 | 0.81 | 4.9 |  |
| NAS100 | [14.5, 15.0) | 2 | 50 | 0.61 | 1.2 | 7 | 14 | -0.73 | -5.1 |  |
| NAS100 | [15.0, 15.5) | 4 | 0 | -1.10 | -4.4 | 9 | 44 | 1.57 | 14.2 |  |
| NAS100 | [15.5, 16.0) | 4 | 75 | 0.70 | 2.8 | 9 | 44 | 0.80 | 7.2 |  |
| NAS100 | [16.0, 16.5) |  |  |  |  | 5 | 20 | -0.47 | -2.3 |  |
| NAS100 | [16.5, 17.01) | 1 | 100 | 2.40 | 2.4 | 9 | 44 | 0.31 | 2.8 |  |
| XAUUSD | [9.0, 9.5) | 15 | 40 | 0.06 | 0.9 | 53 | 30 | 0.04 | 2.2 |  |
| XAUUSD | [9.5, 10.0) | 16 | 56 | 1.04 | 16.7 | 33 | 27 | -0.32 | -10.6 |  |
| XAUUSD | [10.0, 10.5) | 12 | 33 | -0.38 | -4.5 | 32 | 22 | -0.36 | -11.7 | worse (neg) |
| XAUUSD | [10.5, 11.0) | 9 | 33 | -0.16 | -1.4 | 34 | 26 | -0.31 | -10.4 | worse (neg) |
| XAUUSD | [13.0, 13.5) | 17 | 41 | 0.30 | 5.2 | 28 | 32 | 0.04 | 1.0 |  |
| XAUUSD | [13.5, 14.0) | 11 | 55 | 1.09 | 12.0 | 29 | 24 | -0.34 | -9.8 |  |
| XAUUSD | [14.0, 14.5) | 15 | 60 | 1.10 | 16.6 | 34 | 29 | -0.09 | -3.1 | better |
| XAUUSD | [14.5, 15.0) | 9 | 67 | 1.31 | 11.8 | 21 | 43 | 0.03 | 0.7 | better |
| XAUUSD | [15.0, 15.5) | 11 | 27 | -0.34 | -3.7 | 20 | 25 | -0.35 | -6.9 | worse (neg) |
| XAUUSD | [15.5, 16.0) | 8 | 75 | 1.06 | 8.5 | 28 | 21 | -0.52 | -14.4 |  |
| XAUUSD | [16.0, 16.5) | 10 | 60 | 0.70 | 7.0 | 20 | 40 | -0.02 | -0.3 | better |
| XAUUSD | [16.5, 17.01) | 10 | 50 | 0.29 | 2.9 | 39 | 38 | 0.03 | 1.2 |  |

#### Hour of the fill (Amsterdam)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 9 | 27 | 67 | 1.82 | 49.3 | 36 | 31 | -0.34 | -12.2 |  |
| BTCUSD | 10 | 15 | 60 | 0.28 | 4.1 | 23 | 30 | -0.41 | -9.5 | worse |
| BTCUSD | 13 | 13 | 38 | 0.02 | 0.2 | 29 | 31 | -0.34 | -9.8 |  |
| BTCUSD | 14 | 15 | 67 | 0.50 | 7.4 | 14 | 57 | 0.38 | 5.3 |  |
| BTCUSD | 15 | 8 | 75 | 0.57 | 4.5 | 15 | 20 | -0.75 | -11.2 | worse |
| BTCUSD | 16 | 11 | 36 | -0.35 | -3.9 | 13 | 38 | -0.33 | -4.2 |  |
| EURUSD | 9 | 6 | 17 | -0.19 | -1.1 | 19 | 21 | -0.27 | -5.1 | worse (neg) |
| EURUSD | 10 | 5 | 60 | 0.72 | 3.6 | 20 | 30 | 0.12 | 2.4 |  |
| EURUSD | 11 | 2 | 50 | 0.96 | 1.9 | 6 | 17 | -0.41 | -2.5 |  |
| EURUSD | 13 | 4 | 0 | -0.85 | -3.4 | 13 | 54 | 0.99 | 12.8 |  |
| EURUSD | 14 | 7 | 43 | 1.34 | 9.4 | 13 | 23 | 0.57 | 7.4 | better |
| EURUSD | 15 | 8 | 38 | 0.30 | 2.4 | 8 | 12 | -0.73 | -5.8 | worse |
| EURUSD | 16 | 11 | 73 | 1.53 | 16.8 | 11 | 18 | -0.59 | -6.4 |  |
| EURUSD | 17 | 4 | 75 | 2.48 | 9.9 | 5 | 0 | -0.90 | -4.5 |  |
| EURUSD | 18 |  |  |  |  | 1 | 100 | 1.63 | 1.6 |  |
| EURUSD | 19 |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| NAS100 | 0 |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| NAS100 | 9 | 3 | 33 | 0.96 | 2.9 | 9 | 22 | -0.46 | -4.2 |  |
| NAS100 | 10 | 8 | 50 | 0.53 | 4.3 | 12 | 25 | -0.36 | -4.3 | worse |
| NAS100 | 11 | 2 | 50 | 0.61 | 1.2 | 7 | 43 | 0.44 | 3.1 |  |
| NAS100 | 12 | 3 | 67 | 2.00 | 6.0 | 3 | 0 | -1.10 | -3.3 |  |
| NAS100 | 13 | 7 | 71 | 2.39 | 16.8 | 15 | 40 | 1.42 | 21.3 | better |
| NAS100 | 14 | 9 | 33 | 0.35 | 3.2 | 13 | 15 | -0.27 | -3.6 | worse |
| NAS100 | 15 | 9 | 33 | -0.30 | -2.7 | 19 | 42 | 0.76 | 14.4 |  |
| NAS100 | 16 | 1 | 0 | -1.10 | -1.1 | 15 | 33 | 0.25 | 3.8 |  |
| NAS100 | 17 |  |  |  |  | 5 | 60 | 0.82 | 4.1 |  |
| NAS100 | 18 | 1 | 100 | 2.40 | 2.4 | 1 | 0 | -1.49 | -1.5 |  |
| XAUUSD | 9 | 31 | 48 | 0.57 | 17.6 | 86 | 29 | -0.10 | -8.4 | better |
| XAUUSD | 10 | 21 | 33 | -0.28 | -5.9 | 66 | 24 | -0.33 | -22.1 | worse (neg) |
| XAUUSD | 13 | 28 | 46 | 0.61 | 17.2 | 57 | 28 | -0.15 | -8.8 |  |
| XAUUSD | 14 | 24 | 62 | 1.18 | 28.4 | 55 | 35 | -0.04 | -2.4 | better |
| XAUUSD | 15 | 19 | 47 | 0.25 | 4.7 | 48 | 23 | -0.44 | -21.4 | worse |
| XAUUSD | 16 | 20 | 55 | 0.49 | 9.9 | 59 | 39 | 0.01 | 0.8 |  |

#### Weekday of the fill (0 = Monday)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 18 | 61 | 0.39 | 7.0 | 23 | 26 | -0.27 | -6.3 |  |
| BTCUSD | 1 | 16 | 50 | 0.93 | 14.9 | 26 | 46 | -0.00 | -0.1 | better |
| BTCUSD | 2 | 18 | 61 | 0.36 | 6.5 | 27 | 19 | -0.67 | -18.2 | worse |
| BTCUSD | 3 | 21 | 62 | 1.35 | 28.4 | 31 | 32 | -0.37 | -11.4 |  |
| BTCUSD | 4 | 16 | 56 | 0.31 | 5.0 | 23 | 43 | -0.24 | -5.6 |  |
| EURUSD | 0 | 9 | 22 | -0.35 | -3.1 | 15 | 33 | -0.05 | -0.7 |  |
| EURUSD | 1 | 6 | 67 | 1.24 | 7.4 | 20 | 20 | -0.40 | -8.0 |  |
| EURUSD | 2 | 12 | 58 | 2.07 | 24.8 | 22 | 23 | -0.05 | -1.1 |  |
| EURUSD | 3 | 12 | 42 | 0.24 | 2.8 | 20 | 30 | -0.00 | -0.1 |  |
| EURUSD | 4 | 8 | 50 | 0.95 | 7.6 | 20 | 25 | 0.43 | 8.6 | better |
| NAS100 | 0 | 2 | 0 | -1.10 | -2.2 | 17 | 47 | 1.31 | 22.2 |  |
| NAS100 | 1 | 7 | 43 | 0.38 | 2.7 | 17 | 35 | 0.08 | 1.3 | worse |
| NAS100 | 2 | 12 | 42 | 1.01 | 12.1 | 29 | 28 | -0.18 | -5.2 |  |
| NAS100 | 3 | 9 | 33 | 0.19 | 1.7 | 21 | 33 | 0.95 | 19.9 |  |
| NAS100 | 4 | 13 | 69 | 1.43 | 18.6 | 16 | 19 | -0.59 | -9.4 |  |
| XAUUSD | 0 | 27 | 48 | 0.55 | 14.8 | 56 | 32 | -0.07 | -3.8 |  |
| XAUUSD | 1 | 34 | 47 | 0.63 | 21.4 | 71 | 27 | -0.17 | -12.0 |  |
| XAUUSD | 2 | 29 | 52 | 0.49 | 14.2 | 81 | 30 | -0.22 | -17.6 |  |
| XAUUSD | 3 | 28 | 50 | 0.33 | 9.3 | 87 | 32 | -0.13 | -11.0 |  |
| XAUUSD | 4 | 25 | 48 | 0.49 | 12.2 | 76 | 28 | -0.23 | -17.8 |  |

#### Month of the year

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 1 | 8 | 38 | -0.23 | -1.8 | 8 | 50 | 0.02 | 0.2 |  |
| BTCUSD | 2 | 7 | 86 | 0.90 | 6.3 | 13 | 31 | -0.13 | -1.8 | better |
| BTCUSD | 3 | 11 | 55 | 0.26 | 2.9 | 8 | 50 | -0.02 | -0.2 |  |
| BTCUSD | 4 | 4 | 50 | 0.13 | 0.5 | 10 | 30 | -0.56 | -5.6 | worse |
| BTCUSD | 5 | 6 | 50 | -0.05 | -0.3 | 13 | 38 | -0.26 | -3.4 |  |
| BTCUSD | 6 | 9 | 89 | 4.63 | 41.6 | 8 | 38 | -0.09 | -0.7 | better |
| BTCUSD | 7 | 3 | 33 | -0.42 | -1.2 | 5 | 40 | -0.28 | -1.4 |  |
| BTCUSD | 8 | 5 | 60 | -0.07 | -0.3 | 13 | 23 | -0.52 | -6.8 | worse (neg) |
| BTCUSD | 9 | 11 | 45 | 0.10 | 1.1 | 9 | 11 | -0.88 | -7.9 | worse |
| BTCUSD | 10 | 10 | 60 | 0.31 | 3.1 | 15 | 20 | -0.53 | -8.0 | worse |
| BTCUSD | 11 | 12 | 58 | 0.59 | 7.1 | 8 | 25 | -0.62 | -5.0 | worse |
| BTCUSD | 12 | 3 | 67 | 0.93 | 2.8 | 20 | 45 | -0.05 | -1.0 | better |
| EURUSD | 1 | 2 | 100 | 2.24 | 4.5 | 6 | 50 | 1.05 | 6.3 |  |
| EURUSD | 2 | 2 | 0 | -1.10 | -2.2 | 5 | 20 | 0.04 | 0.2 |  |
| EURUSD | 3 | 5 | 20 | 0.16 | 0.8 | 8 | 12 | -0.64 | -5.1 | worse |
| EURUSD | 4 | 8 | 50 | 0.65 | 5.2 | 14 | 43 | 0.66 | 9.3 |  |
| EURUSD | 5 | 3 | 67 | 2.05 | 6.2 | 9 | 44 | 0.45 | 4.1 | better |
| EURUSD | 6 | 7 | 43 | 1.46 | 10.2 | 10 | 20 | 0.74 | 7.4 | better |
| EURUSD | 7 | 1 | 0 | -1.10 | -1.1 | 6 | 33 | -0.07 | -0.4 |  |
| EURUSD | 8 | 8 | 38 | 0.45 | 3.6 | 9 | 0 | -1.10 | -9.9 | worse |
| EURUSD | 9 | 5 | 80 | 1.89 | 9.5 | 6 | 17 | -0.56 | -3.4 |  |
| EURUSD | 10 | 5 | 40 | 0.09 | 0.4 | 2 | 0 | -1.10 | -2.2 |  |
| EURUSD | 11 | 1 | 100 | 2.43 | 2.4 | 7 | 43 | 0.48 | 3.4 |  |
| EURUSD | 12 |  |  |  |  | 15 | 13 | -0.72 | -10.8 |  |
| NAS100 | 1 | 3 | 67 | 3.87 | 11.6 | 9 | 22 | 0.18 | 1.6 |  |
| NAS100 | 2 | 5 | 60 | 0.87 | 4.3 | 10 | 0 | -1.10 | -11.0 |  |
| NAS100 | 3 | 5 | 80 | 1.85 | 9.2 | 8 | 50 | 0.27 | 2.2 |  |
| NAS100 | 4 | 1 | 100 | 3.15 | 3.1 | 11 | 36 | 1.11 | 12.2 |  |
| NAS100 | 5 | 10 | 30 | 0.16 | 1.6 | 6 | 17 | -0.66 | -4.0 | worse |
| NAS100 | 6 | 4 | 50 | 0.85 | 3.4 | 5 | 40 | 1.16 | 5.8 | better |
| NAS100 | 7 | 4 | 50 | 0.72 | 2.9 | 9 | 44 | 0.74 | 6.6 |  |
| NAS100 | 8 | 2 | 0 | -1.10 | -2.2 | 3 | 0 | -1.23 | -3.7 |  |
| NAS100 | 9 | 2 | 50 | 0.39 | 0.8 | 10 | 30 | 0.30 | 3.0 |  |
| NAS100 | 10 | 4 | 50 | 0.37 | 1.5 | 10 | 30 | 0.13 | 1.3 | worse |
| NAS100 | 11 | 2 | 0 | -1.10 | -2.2 | 10 | 50 | 1.20 | 12.0 |  |
| NAS100 | 12 | 1 | 0 | -1.10 | -1.1 | 9 | 44 | 0.30 | 2.7 |  |
| XAUUSD | 1 | 12 | 67 | 0.84 | 10.1 | 41 | 27 | -0.26 | -10.8 |  |
| XAUUSD | 2 | 9 | 67 | 1.02 | 9.2 | 37 | 35 | -0.12 | -4.6 |  |
| XAUUSD | 3 | 17 | 41 | 0.44 | 7.5 | 24 | 38 | 0.11 | 2.7 |  |
| XAUUSD | 4 | 10 | 30 | 0.26 | 2.6 | 22 | 32 | -0.21 | -4.5 |  |
| XAUUSD | 5 | 18 | 44 | 0.19 | 3.4 | 32 | 34 | 0.01 | 0.4 |  |
| XAUUSD | 6 | 10 | 50 | 0.66 | 6.6 | 28 | 39 | 0.14 | 3.9 | better |
| XAUUSD | 7 | 9 | 44 | 0.08 | 0.7 | 32 | 28 | -0.13 | -4.2 |  |
| XAUUSD | 8 | 11 | 64 | 1.07 | 11.8 | 26 | 27 | -0.31 | -8.1 |  |
| XAUUSD | 9 | 15 | 33 | -0.18 | -2.7 | 35 | 29 | -0.11 | -3.8 |  |
| XAUUSD | 10 | 15 | 67 | 1.52 | 22.8 | 36 | 14 | -0.67 | -24.1 |  |
| XAUUSD | 11 | 9 | 44 | -0.14 | -1.3 | 32 | 25 | -0.35 | -11.4 | worse (neg) |
| XAUUSD | 12 | 8 | 38 | 0.16 | 1.3 | 26 | 35 | 0.08 | 2.2 |  |

#### Planned R:R band

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0.0, 1.0) | 20 | 90 | 0.43 | 8.7 | 36 | 44 | -0.34 | -12.1 |  |
| BTCUSD | [1.0, 1.5) | 24 | 62 | 0.26 | 6.3 | 32 | 38 | -0.29 | -9.3 |  |
| BTCUSD | [1.5, 2.0) | 11 | 18 | -0.58 | -6.4 | 21 | 38 | -0.06 | -1.4 |  |
| BTCUSD | [2.0, 2.5) | 12 | 50 | 0.52 | 6.2 | 15 | 7 | -0.90 | -13.5 | worse |
| BTCUSD | [2.5, 3.0) | 16 | 50 | 0.71 | 11.4 | 17 | 35 | 0.21 | 3.6 |  |
| BTCUSD | [3.0, 4.0) | 3 | 33 | 0.41 | 1.2 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | [4.0, 6.0) |  |  |  |  | 4 | 0 | -1.10 | -4.4 |  |
| BTCUSD | [6.0, 100.0) | 3 | 67 | 11.45 | 34.4 | 4 | 0 | -0.85 | -3.4 |  |
| EURUSD | [1.0, 1.5) | 12 | 67 | 0.92 | 11.1 | 34 | 41 | 0.12 | 4.2 | better |
| EURUSD | [1.5, 2.0) | 9 | 67 | 1.30 | 11.7 | 16 | 25 | -0.23 | -3.7 |  |
| EURUSD | [2.0, 2.5) | 6 | 50 | 1.03 | 6.2 | 12 | 17 | -0.39 | -4.7 |  |
| EURUSD | [2.5, 3.0) | 5 | 20 | -0.13 | -0.7 | 8 | 12 | -0.51 | -4.1 | worse (neg) |
| EURUSD | [3.0, 4.0) | 9 | 33 | 0.84 | 7.6 | 13 | 23 | 0.42 | 5.4 |  |
| EURUSD | [4.0, 6.0) | 3 | 0 | -1.10 | -3.3 | 11 | 0 | -0.92 | -10.1 | worse (neg) |
| EURUSD | [6.0, 100.0) | 3 | 33 | 2.32 | 7.0 | 3 | 33 | 3.92 | 11.8 | better |
| NAS100 | [0.0, 1.0) | 5 | 40 | -0.10 | -0.5 | 9 | 44 | 0.05 | 0.5 | worse |
| NAS100 | [1.0, 1.5) | 12 | 42 | 0.03 | 0.4 | 28 | 36 | -0.14 | -3.8 | worse |
| NAS100 | [1.5, 2.0) | 8 | 62 | 1.11 | 8.8 | 19 | 26 | -0.18 | -3.4 |  |
| NAS100 | [2.0, 2.5) | 5 | 60 | 1.47 | 7.4 | 9 | 33 | 0.27 | 2.4 |  |
| NAS100 | [2.5, 3.0) | 3 | 33 | 0.59 | 1.8 | 6 | 33 | -0.03 | -0.2 | worse |
| NAS100 | [3.0, 4.0) | 4 | 75 | 3.22 | 12.9 | 10 | 20 | -0.24 | -2.4 |  |
| NAS100 | [4.0, 6.0) | 3 | 33 | 1.81 | 5.4 | 10 | 50 | 2.86 | 28.6 | better |
| NAS100 | [6.0, 100.0) | 3 | 0 | -1.10 | -3.3 | 9 | 11 | 0.80 | 7.2 |  |
| XAUUSD | [0.0, 1.0) | 7 | 57 | -0.06 | -0.4 | 16 | 31 | -0.49 | -7.9 | worse (neg) |
| XAUUSD | [1.0, 1.5) | 20 | 50 | -0.01 | -0.2 | 51 | 49 | -0.04 | -1.8 |  |
| XAUUSD | [1.5, 2.0) | 11 | 36 | -0.11 | -1.2 | 23 | 39 | -0.05 | -1.1 |  |
| XAUUSD | [2.0, 2.5) | 73 | 53 | 0.50 | 36.2 | 211 | 28 | -0.25 | -53.2 |  |
| XAUUSD | [2.5, 3.0) | 8 | 25 | -0.06 | -0.5 | 13 | 0 | -0.87 | -11.3 | worse (neg) |
| XAUUSD | [3.0, 4.0) | 7 | 43 | 0.79 | 5.6 | 21 | 19 | 0.03 | 0.6 | better |
| XAUUSD | [4.0, 6.0) | 9 | 78 | 3.41 | 30.7 | 19 | 26 | 0.63 | 12.1 | better |
| XAUUSD | [6.0, 100.0) | 8 | 12 | 0.21 | 1.7 | 17 | 12 | 0.02 | 0.4 |  |

#### Stop distance / ATR14 of the 1H at entry

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0.0, 0.3) | 3 | 67 | 8.43 | 25.3 | 2 | 0 | -1.10 | -2.2 |  |
| BTCUSD | [0.3, 0.5) | 12 | 50 | 0.42 | 5.1 | 22 | 41 | -0.07 | -1.5 |  |
| BTCUSD | [0.5, 0.75) | 26 | 62 | 0.43 | 11.2 | 23 | 30 | -0.43 | -9.8 | worse |
| BTCUSD | [0.75, 1.0) | 13 | 69 | 1.22 | 15.9 | 24 | 17 | -0.67 | -16.0 |  |
| BTCUSD | [1.0, 1.5) | 17 | 53 | 0.08 | 1.3 | 29 | 45 | 0.04 | 1.3 |  |
| BTCUSD | [1.5, 2.0) | 8 | 62 | 0.33 | 2.6 | 18 | 33 | -0.45 | -8.1 | worse |
| BTCUSD | [2.0, 3.0) | 6 | 17 | -0.82 | -4.9 | 7 | 29 | -0.58 | -4.1 | worse (neg) |
| BTCUSD | [3.0, 100.0) | 4 | 100 | 1.31 | 5.2 | 5 | 40 | -0.24 | -1.2 | better |
| EURUSD | [0.3, 0.5) | 5 | 20 | -0.46 | -2.3 | 15 | 7 | -0.79 | -11.8 | worse (neg) |
| EURUSD | [0.5, 0.75) | 19 | 63 | 1.79 | 34.0 | 40 | 32 | 0.12 | 4.7 | better |
| EURUSD | [0.75, 1.0) | 7 | 14 | -0.68 | -4.8 | 21 | 19 | -0.29 | -6.2 | worse (neg) |
| EURUSD | [1.0, 1.5) | 9 | 33 | 0.27 | 2.5 | 12 | 25 | 0.72 | 8.6 |  |
| EURUSD | [1.5, 2.0) | 2 | 50 | 0.71 | 1.4 | 3 | 33 | 0.15 | 0.5 |  |
| EURUSD | [2.0, 3.0) | 5 | 80 | 1.75 | 8.8 | 4 | 50 | 0.28 | 1.1 | better |
| EURUSD | [3.0, 100.0) |  |  |  |  | 2 | 50 | 0.94 | 1.9 |  |
| NAS100 | [0.0, 0.3) | 2 | 50 | 0.40 | 0.8 | 3 | 0 | -1.10 | -3.3 |  |
| NAS100 | [0.3, 0.5) | 11 | 45 | 1.05 | 11.5 | 23 | 17 | 0.25 | 5.7 |  |
| NAS100 | [0.5, 0.75) | 15 | 60 | 1.43 | 21.4 | 20 | 45 | 0.52 | 10.3 | better |
| NAS100 | [0.75, 1.0) | 8 | 12 | -0.73 | -5.8 | 18 | 22 | -0.12 | -2.1 | worse (neg) |
| NAS100 | [1.0, 1.5) | 3 | 100 | 1.99 | 6.0 | 17 | 24 | 0.20 | 3.4 |  |
| NAS100 | [1.5, 2.0) | 1 | 0 | -1.10 | -1.1 | 8 | 62 | 0.98 | 7.9 |  |
| NAS100 | [2.0, 3.0) | 3 | 33 | 0.04 | 0.1 | 10 | 50 | 0.53 | 5.3 |  |
| NAS100 | [3.0, 100.0) |  |  |  |  | 1 | 100 | 1.54 | 1.5 |  |
| XAUUSD | [0.0, 0.3) |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| XAUUSD | [0.3, 0.5) | 15 | 33 | 0.35 | 5.2 | 25 | 28 | 0.10 | 2.5 |  |
| XAUUSD | [0.5, 0.75) | 33 | 58 | 0.86 | 28.4 | 69 | 29 | -0.17 | -11.9 |  |
| XAUUSD | [0.75, 1.0) | 33 | 48 | 0.47 | 15.5 | 57 | 32 | 0.02 | 1.4 |  |
| XAUUSD | [1.0, 1.5) | 30 | 37 | 0.03 | 1.0 | 110 | 29 | -0.25 | -27.9 | worse |
| XAUUSD | [1.5, 2.0) | 14 | 64 | 0.64 | 9.0 | 38 | 32 | -0.20 | -7.8 |  |
| XAUUSD | [2.0, 3.0) | 10 | 50 | 0.66 | 6.6 | 44 | 27 | -0.33 | -14.6 |  |
| XAUUSD | [3.0, 100.0) | 8 | 62 | 0.77 | 6.2 | 27 | 33 | -0.11 | -2.9 | better |

#### Stop size (pips; gold USD x 100 i.e. pips of 0.01; NAS100 points; BTC USD)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [50.0, 100.0) |  |  |  |  | 32 | 38 | -0.17 | -5.4 |  |
| BTCUSD | [100.0, 1000000000.0) | 89 | 58 | 0.69 | 61.7 | 98 | 32 | -0.37 | -36.2 |  |
| EURUSD | [0.0, 8.01) | 23 | 35 | 0.32 | 7.4 | 52 | 17 | -0.43 | -22.6 | worse |
| EURUSD | [8.01, 10.0) | 5 | 60 | 2.10 | 10.5 | 18 | 44 | 1.28 | 23.0 | better |
| EURUSD | [10.0, 12.0) | 2 | 100 | 4.20 | 8.4 | 6 | 17 | -0.32 | -1.9 |  |
| EURUSD | [12.0, 15.0) | 4 | 50 | 0.45 | 1.8 | 9 | 11 | -0.77 | -6.9 | worse |
| EURUSD | [15.0, 20.0) | 8 | 62 | 1.00 | 8.0 | 5 | 60 | 1.07 | 5.3 | better |
| EURUSD | [20.0, 30.0) | 2 | 50 | 0.96 | 1.9 | 3 | 67 | 0.86 | 2.6 |  |
| EURUSD | [30.0, 50.0) | 3 | 33 | 0.52 | 1.5 | 4 | 25 | -0.17 | -0.7 | worse |
| NAS100 | [8.01, 10.0) |  |  |  |  | 2 | 100 | 4.50 | 9.0 |  |
| NAS100 | [10.0, 12.0) |  |  |  |  | 38 | 26 | 0.05 | 1.8 |  |
| NAS100 | [12.0, 15.0) | 6 | 33 | 0.00 | 0.0 | 8 | 12 | -0.60 | -4.8 | worse |
| NAS100 | [15.0, 20.0) | 4 | 25 | -0.25 | -1.0 | 14 | 29 | 0.55 | 7.7 |  |
| NAS100 | [20.0, 30.0) | 14 | 50 | 1.29 | 18.1 | 16 | 44 | 0.53 | 8.5 | better |
| NAS100 | [30.0, 50.0) | 12 | 50 | 0.76 | 9.1 | 7 | 43 | 1.26 | 8.8 |  |
| NAS100 | [50.0, 100.0) | 3 | 67 | 0.88 | 2.7 | 12 | 33 | -0.15 | -1.8 |  |
| NAS100 | [100.0, 1000000000.0) | 4 | 50 | 1.02 | 4.1 | 3 | 33 | -0.15 | -0.4 |  |
| XAUUSD | [50.0, 100.0) |  |  |  |  | 9 | 44 | 0.52 | 4.7 |  |
| XAUUSD | [100.0, 1000000000.0) | 143 | 49 | 0.50 | 71.8 | 362 | 29 | -0.18 | -66.9 |  |

#### Visit number

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 1 | 89 | 58 | 0.69 | 61.7 | 130 | 33 | -0.32 | -41.6 |  |
| EURUSD | 1 | 44 | 48 | 0.88 | 38.7 | 90 | 27 | 0.04 | 3.2 |  |
| EURUSD | 2 | 2 | 50 | 0.96 | 1.9 | 6 | 17 | -0.56 | -3.4 |  |
| EURUSD | 3 | 1 | 0 | -1.10 | -1.1 | 1 | 0 | -1.10 | -1.1 |  |
| NAS100 | 1 | 43 | 47 | 0.77 | 32.9 | 100 | 32 | 0.29 | 28.8 |  |
| XAUUSD | 1 | 140 | 49 | 0.49 | 69.2 | 343 | 29 | -0.18 | -63.2 |  |
| XAUUSD | 2 | 1 | 100 | 1.89 | 1.9 | 26 | 38 | 0.04 | 1.0 |  |
| XAUUSD | 3 | 2 | 50 | 0.36 | 0.7 | 2 | 50 | -0.03 | -0.1 |  |

#### Entry depth into the zone from its near edge (fraction of the zone's height; negative = outside)

Depth as the engine measures it (`risk.py`): LONG (poi_high - entry) / height, SHORT (entry - poi_low) / height.

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100.0, -1.0) | 4 | 25 | -0.53 | -2.1 | 3 | 0 | -1.10 | -3.3 | worse (neg) |
| BTCUSD | [-1.0, -0.5) | 11 | 64 | 0.30 | 3.3 | 22 | 32 | -0.45 | -9.9 | worse |
| BTCUSD | [-0.5, -0.25) | 22 | 68 | 0.93 | 20.4 | 31 | 42 | -0.24 | -7.3 | better |
| BTCUSD | [-0.25, 0.0) | 30 | 43 | -0.03 | -0.9 | 32 | 31 | -0.40 | -12.9 | worse (neg) |
| BTCUSD | [0.0, 0.25) | 12 | 58 | 0.35 | 4.1 | 27 | 33 | -0.08 | -2.2 |  |
| BTCUSD | [0.25, 0.5) | 10 | 90 | 3.68 | 36.8 | 15 | 27 | -0.40 | -6.0 |  |
| EURUSD | [-100.0, -1.0) | 2 | 100 | 1.96 | 3.9 |  |  |  |  |  |
| EURUSD | [-1.0, -0.5) | 5 | 40 | 0.96 | 4.8 | 12 | 33 | 0.11 | 1.4 | better |
| EURUSD | [-0.5, -0.25) | 7 | 57 | 1.20 | 8.4 | 17 | 24 | 0.48 | 8.1 | better |
| EURUSD | [-0.25, 0.0) | 15 | 40 | 0.31 | 4.7 | 31 | 39 | 0.40 | 12.4 |  |
| EURUSD | [0.0, 0.25) | 11 | 36 | 0.49 | 5.4 | 18 | 6 | -0.89 | -16.0 | worse |
| EURUSD | [0.25, 0.5) | 3 | 67 | 2.96 | 8.9 | 10 | 20 | -0.38 | -3.8 |  |
| EURUSD | [0.5, 100.0) | 4 | 50 | 0.88 | 3.5 | 9 | 22 | -0.38 | -3.4 |  |
| NAS100 | [-1.0, -0.5) | 8 | 50 | 1.09 | 8.7 | 11 | 45 | 0.42 | 4.6 | better |
| NAS100 | [-0.5, -0.25) | 14 | 50 | 0.73 | 10.3 | 12 | 42 | 1.09 | 13.1 |  |
| NAS100 | [-0.25, 0.0) | 9 | 56 | 1.04 | 9.3 | 39 | 28 | 0.10 | 4.0 |  |
| NAS100 | [0.0, 0.25) | 3 | 67 | 1.68 | 5.0 | 23 | 30 | 0.40 | 9.1 | better |
| NAS100 | [0.25, 0.5) | 7 | 14 | -0.50 | -3.5 | 12 | 17 | -0.40 | -4.7 | worse (neg) |
| NAS100 | [0.5, 100.0) | 2 | 50 | 1.53 | 3.1 | 3 | 67 | 0.90 | 2.7 |  |
| XAUUSD | [-100.0, -1.0) | 12 | 58 | 0.46 | 5.5 | 34 | 41 | 0.07 | 2.4 |  |
| XAUUSD | [-1.0, -0.5) | 33 | 52 | 0.56 | 18.5 | 115 | 28 | -0.31 | -35.3 |  |
| XAUUSD | [-0.5, -0.25) | 33 | 55 | 0.86 | 28.4 | 79 | 30 | -0.22 | -17.2 |  |
| XAUUSD | [-0.25, 0.0) | 30 | 53 | 0.45 | 13.6 | 77 | 29 | -0.03 | -2.0 |  |
| XAUUSD | [0.0, 0.25) | 19 | 42 | 0.50 | 9.5 | 38 | 29 | -0.09 | -3.5 |  |
| XAUUSD | [0.25, 0.5) | 16 | 25 | -0.23 | -3.7 | 28 | 25 | -0.24 | -6.7 | worse (neg) |

#### Entry distance outside the zone's near edge, in 1H ATRs (negative = inside)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100.0, -0.25) | 14 | 71 | 2.41 | 33.7 | 23 | 35 | -0.14 | -3.1 | better |
| BTCUSD | [-0.25, 0.0) | 8 | 75 | 0.90 | 7.2 | 19 | 26 | -0.27 | -5.1 | better |
| BTCUSD | [0.0, 0.1) | 4 | 50 | -0.25 | -1.0 | 5 | 20 | -0.78 | -3.9 | worse (neg) |
| BTCUSD | [0.1, 0.25) | 11 | 64 | 0.48 | 5.3 | 13 | 31 | -0.47 | -6.1 | worse |
| BTCUSD | [0.25, 0.5) | 19 | 42 | 0.54 | 10.2 | 17 | 29 | -0.40 | -6.7 | worse |
| BTCUSD | [0.5, 1.0) | 21 | 57 | 0.20 | 4.3 | 32 | 38 | -0.33 | -10.5 |  |
| BTCUSD | [1.0, 100.0) | 12 | 58 | 0.16 | 2.0 | 21 | 38 | -0.29 | -6.2 |  |
| EURUSD | [-100.0, -0.25) | 11 | 45 | 1.13 | 12.4 | 26 | 19 | -0.43 | -11.1 |  |
| EURUSD | [-0.25, 0.0) | 7 | 43 | 0.77 | 5.4 | 11 | 0 | -1.10 | -12.1 | worse |
| EURUSD | [0.0, 0.1) | 1 | 100 | 2.51 | 2.5 | 8 | 38 | 0.08 | 0.7 |  |
| EURUSD | [0.1, 0.25) | 9 | 33 | 0.19 | 1.7 | 10 | 30 | 0.24 | 2.4 |  |
| EURUSD | [0.25, 0.5) | 9 | 44 | 0.53 | 4.8 | 19 | 26 | -0.11 | -2.1 | worse |
| EURUSD | [0.5, 1.0) | 5 | 60 | 1.46 | 7.3 | 12 | 33 | 1.34 | 16.0 | better |
| EURUSD | [1.0, 100.0) | 5 | 60 | 1.09 | 5.5 | 11 | 45 | 0.44 | 4.9 | better |
| NAS100 | [-100.0, -0.25) | 11 | 36 | 0.52 | 5.7 | 22 | 27 | 0.40 | 8.8 |  |
| NAS100 | [-0.25, 0.0) | 1 | 0 | -1.10 | -1.1 | 16 | 31 | -0.11 | -1.8 |  |
| NAS100 | [0.0, 0.1) | 5 | 60 | 1.44 | 7.2 | 10 | 20 | -0.07 | -0.7 |  |
| NAS100 | [0.1, 0.25) | 4 | 50 | 0.86 | 3.4 | 15 | 20 | -0.26 | -3.9 |  |
| NAS100 | [0.25, 0.5) | 8 | 50 | 0.55 | 4.4 | 21 | 33 | 0.49 | 10.3 |  |
| NAS100 | [0.5, 1.0) | 11 | 45 | 0.74 | 8.1 | 8 | 50 | 1.12 | 9.0 |  |
| NAS100 | [1.0, 100.0) | 3 | 67 | 1.73 | 5.2 | 8 | 62 | 0.87 | 6.9 | better |
| XAUUSD | [-100.0, -0.25) | 20 | 40 | 0.30 | 6.1 | 37 | 30 | 0.02 | 0.7 |  |
| XAUUSD | [-0.25, 0.0) | 15 | 27 | -0.02 | -0.3 | 29 | 24 | -0.37 | -10.8 | worse (neg) |
| XAUUSD | [0.0, 0.1) | 7 | 57 | 0.58 | 4.1 | 23 | 30 | 0.22 | 5.1 | better |
| XAUUSD | [0.1, 0.25) | 7 | 43 | 0.21 | 1.5 | 28 | 18 | -0.37 | -10.5 | worse |
| XAUUSD | [0.25, 0.5) | 31 | 65 | 1.30 | 40.4 | 64 | 33 | -0.10 | -6.7 | better |
| XAUUSD | [0.5, 1.0) | 31 | 42 | -0.02 | -0.7 | 82 | 32 | -0.20 | -16.8 |  |
| XAUUSD | [1.0, 100.0) | 32 | 56 | 0.65 | 20.7 | 108 | 31 | -0.21 | -23.2 |  |

#### Stop distance / zone height

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0.0, 0.25) | 16 | 44 | 1.46 | 23.4 | 17 | 47 | 0.20 | 3.3 | better |
| BTCUSD | [0.25, 0.5) | 32 | 62 | 0.88 | 28.1 | 44 | 41 | -0.13 | -5.6 | better |
| BTCUSD | [0.5, 0.75) | 20 | 75 | 0.51 | 10.2 | 30 | 27 | -0.56 | -16.7 | worse |
| BTCUSD | [0.75, 1.0) | 9 | 44 | 0.10 | 0.9 | 17 | 12 | -0.89 | -15.1 | worse |
| BTCUSD | [1.0, 1.5) | 10 | 50 | -0.10 | -1.0 | 16 | 31 | -0.32 | -5.2 |  |
| BTCUSD | [1.5, 100.0) | 2 | 50 | 0.04 | 0.1 | 6 | 33 | -0.41 | -2.4 |  |
| EURUSD | [0.0, 0.25) | 10 | 40 | 0.90 | 9.0 | 14 | 36 | 0.51 | 7.2 | better |
| EURUSD | [0.25, 0.5) | 20 | 40 | 0.59 | 11.7 | 49 | 22 | -0.07 | -3.4 | worse |
| EURUSD | [0.5, 0.75) | 7 | 57 | 0.80 | 5.6 | 16 | 6 | -0.91 | -14.5 |  |
| EURUSD | [0.75, 1.0) | 4 | 25 | -0.16 | -0.6 | 13 | 38 | 0.45 | 5.8 |  |
| EURUSD | [1.0, 1.5) | 6 | 83 | 2.30 | 13.8 | 4 | 75 | 1.18 | 4.7 | better |
| EURUSD | [1.5, 100.0) |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| NAS100 | [0.0, 0.25) | 11 | 55 | 1.08 | 11.9 | 21 | 29 | 0.56 | 11.8 | better |
| NAS100 | [0.25, 0.5) | 12 | 25 | -0.24 | -2.9 | 35 | 26 | -0.06 | -2.0 | worse (neg) |
| NAS100 | [0.5, 0.75) | 12 | 50 | 0.84 | 10.1 | 14 | 43 | 0.73 | 10.2 | better |
| NAS100 | [0.75, 1.0) | 6 | 50 | 1.97 | 11.8 | 14 | 43 | 0.54 | 7.6 | better |
| NAS100 | [1.0, 1.5) | 1 | 100 | 0.58 | 0.6 | 11 | 27 | 0.21 | 2.4 |  |
| NAS100 | [1.5, 100.0) | 1 | 100 | 1.44 | 1.4 | 5 | 40 | -0.23 | -1.2 |  |
| XAUUSD | [0.0, 0.25) | 10 | 50 | 0.65 | 6.5 | 19 | 26 | 0.29 | 5.5 | better |
| XAUUSD | [0.25, 0.5) | 45 | 44 | 0.37 | 16.7 | 95 | 29 | -0.16 | -15.3 |  |
| XAUUSD | [0.5, 0.75) | 33 | 48 | 0.50 | 16.5 | 80 | 24 | -0.41 | -32.9 |  |
| XAUUSD | [0.75, 1.0) | 26 | 50 | 0.75 | 19.4 | 73 | 32 | -0.13 | -9.2 |  |
| XAUUSD | [1.0, 1.5) | 22 | 59 | 0.58 | 12.7 | 75 | 31 | -0.16 | -12.0 |  |
| XAUUSD | [1.5, 100.0) | 7 | 43 | 0.01 | 0.1 | 29 | 41 | 0.06 | 1.6 |  |

#### Stop inside the zone (True) or beyond its far edge (False)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | False | 4 | 75 | 1.12 | 4.5 | 14 | 36 | -0.23 | -3.2 | better |
| BTCUSD | True | 85 | 58 | 0.67 | 57.2 | 116 | 33 | -0.33 | -38.4 |  |
| EURUSD | False | 3 | 100 | 2.46 | 7.4 | 8 | 25 | -0.17 | -1.4 |  |
| EURUSD | True | 44 | 43 | 0.73 | 32.2 | 89 | 26 | 0.00 | 0.1 |  |
| NAS100 | False | 2 | 50 | 1.53 | 3.1 | 12 | 33 | -0.27 | -3.3 |  |
| NAS100 | True | 41 | 46 | 0.73 | 29.9 | 88 | 32 | 0.36 | 32.1 |  |
| XAUUSD | False | 7 | 29 | -0.32 | -2.2 | 37 | 30 | -0.13 | -4.7 |  |
| XAUUSD | True | 136 | 50 | 0.54 | 74.0 | 334 | 30 | -0.17 | -57.5 |  |

#### Zone height / 1H ATR14

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0.0, 0.5) | 1 | 100 | 2.63 | 2.6 |  |  |  |  |  |
| BTCUSD | [0.5, 1.0) | 13 | 69 | 0.71 | 9.2 | 18 | 22 | -0.60 | -10.7 |  |
| BTCUSD | [1.0, 1.5) | 25 | 56 | 0.20 | 5.1 | 42 | 29 | -0.48 | -20.0 | worse |
| BTCUSD | [1.5, 2.0) | 15 | 60 | 1.04 | 15.5 | 18 | 22 | -0.50 | -9.0 |  |
| BTCUSD | [2.0, 3.0) | 16 | 50 | 1.51 | 24.1 | 26 | 38 | -0.25 | -6.5 | better |
| BTCUSD | [3.0, 5.0) | 11 | 45 | -0.11 | -1.3 | 19 | 58 | 0.43 | 8.2 |  |
| BTCUSD | [5.0, 100.0) | 8 | 75 | 0.80 | 6.4 | 7 | 29 | -0.50 | -3.5 |  |
| EURUSD | [0.0, 0.5) |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| EURUSD | [0.5, 1.0) | 7 | 43 | 0.71 | 5.0 | 7 | 43 | 0.28 | 1.9 |  |
| EURUSD | [1.0, 1.5) | 12 | 50 | 0.84 | 10.0 | 29 | 17 | -0.46 | -13.2 |  |
| EURUSD | [1.5, 2.0) | 9 | 56 | 1.15 | 10.4 | 21 | 29 | -0.12 | -2.5 |  |
| EURUSD | [2.0, 3.0) | 9 | 44 | 1.18 | 10.6 | 27 | 22 | 0.31 | 8.3 | better |
| EURUSD | [3.0, 5.0) | 5 | 60 | 0.85 | 4.2 | 7 | 29 | 0.33 | 2.3 |  |
| EURUSD | [5.0, 100.0) | 5 | 20 | -0.13 | -0.7 | 5 | 60 | 0.62 | 3.1 |  |
| NAS100 | [0.0, 0.5) | 2 | 0 | -1.10 | -2.2 | 1 | 0 | -1.10 | -1.1 |  |
| NAS100 | [0.5, 1.0) | 8 | 88 | 2.93 | 23.4 | 13 | 38 | 0.78 | 10.1 | better |
| NAS100 | [1.0, 1.5) | 10 | 40 | 0.15 | 1.5 | 21 | 24 | -0.38 | -8.0 | worse |
| NAS100 | [1.5, 2.0) | 4 | 25 | -0.35 | -1.4 | 20 | 20 | -0.45 | -8.9 | worse (neg) |
| NAS100 | [2.0, 3.0) | 11 | 36 | 0.73 | 8.0 | 28 | 43 | 1.34 | 37.5 |  |
| NAS100 | [3.0, 5.0) | 8 | 50 | 0.45 | 3.6 | 12 | 42 | 0.18 | 2.2 | worse |
| NAS100 | [5.0, 100.0) |  |  |  |  | 5 | 20 | -0.58 | -2.9 |  |
| XAUUSD | [0.0, 0.5) | 2 | 50 | -0.18 | -0.4 | 7 | 43 | -0.09 | -0.7 |  |
| XAUUSD | [0.5, 1.0) | 18 | 39 | 0.51 | 9.3 | 65 | 28 | -0.10 | -6.7 |  |
| XAUUSD | [1.0, 1.5) | 47 | 53 | 0.65 | 30.4 | 98 | 26 | -0.37 | -36.3 |  |
| XAUUSD | [1.5, 2.0) | 35 | 40 | -0.03 | -1.1 | 60 | 37 | -0.00 | -0.3 |  |
| XAUUSD | [2.0, 3.0) | 26 | 58 | 0.91 | 23.7 | 84 | 38 | 0.12 | 10.3 | better |
| XAUUSD | [3.0, 5.0) | 13 | 54 | 0.70 | 9.1 | 48 | 19 | -0.47 | -22.6 |  |
| XAUUSD | [5.0, 100.0) | 2 | 50 | 0.37 | 0.7 | 9 | 11 | -0.66 | -6.0 |  |

#### Target distance / 1H ATR14

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0, 1) | 33 | 73 | 0.32 | 10.5 | 44 | 41 | -0.25 | -10.8 |  |
| BTCUSD | [1, 2) | 30 | 47 | 0.23 | 6.9 | 53 | 34 | -0.30 | -16.0 |  |
| BTCUSD | [2, 3) | 12 | 75 | 1.05 | 12.5 | 17 | 12 | -0.77 | -13.1 |  |
| BTCUSD | [3, 4) | 5 | 20 | -0.44 | -2.2 | 7 | 57 | 0.86 | 6.0 |  |
| BTCUSD | [4, 6) | 4 | 25 | 5.12 | 20.5 | 6 | 17 | -0.73 | -4.4 |  |
| BTCUSD | [6, 10) | 3 | 33 | 3.16 | 9.5 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | [10, 1000) | 2 | 100 | 1.99 | 4.0 | 2 | 0 | -1.10 | -2.2 |  |
| EURUSD | [0, 1) | 1 | 100 | 2.10 | 2.1 | 1 | 100 | 2.57 | 2.6 |  |
| EURUSD | [1, 2) | 9 | 78 | 1.43 | 12.9 | 41 | 29 | -0.20 | -8.3 |  |
| EURUSD | [2, 3) | 16 | 38 | 0.48 | 7.7 | 20 | 10 | -0.68 | -13.6 | worse |
| EURUSD | [3, 4) | 5 | 20 | 0.16 | 0.8 | 16 | 44 | 0.83 | 13.4 |  |
| EURUSD | [4, 6) | 12 | 42 | 0.84 | 10.1 | 11 | 9 | -0.52 | -5.7 |  |
| EURUSD | [6, 10) | 2 | 100 | 4.06 | 8.1 | 5 | 20 | -0.48 | -2.4 |  |
| EURUSD | [10, 1000) | 2 | 0 | -1.10 | -2.2 | 3 | 33 | 4.25 | 12.8 |  |
| NAS100 | [0, 1) | 4 | 50 | 0.26 | 1.0 | 7 | 29 | -0.37 | -2.6 | worse |
| NAS100 | [1, 2) | 18 | 44 | 0.42 | 7.6 | 33 | 27 | -0.24 | -8.1 | worse |
| NAS100 | [2, 3) | 11 | 64 | 1.64 | 18.0 | 22 | 41 | 0.54 | 11.9 | better |
| NAS100 | [3, 4) | 2 | 0 | -1.10 | -2.2 | 9 | 11 | -0.86 | -7.7 |  |
| NAS100 | [4, 6) | 4 | 50 | 2.35 | 9.4 | 18 | 22 | 0.32 | 5.8 |  |
| NAS100 | [6, 10) | 2 | 50 | 0.61 | 1.2 | 8 | 75 | 3.64 | 29.1 |  |
| NAS100 | [10, 1000) | 2 | 0 | -1.10 | -2.2 | 3 | 33 | 0.11 | 0.3 |  |
| XAUUSD | [0, 1) | 24 | 46 | -0.06 | -1.4 | 47 | 40 | -0.17 | -8.2 |  |
| XAUUSD | [1, 2) | 47 | 51 | 0.38 | 18.0 | 104 | 36 | -0.10 | -10.3 |  |
| XAUUSD | [2, 3) | 32 | 47 | 0.48 | 15.3 | 91 | 20 | -0.40 | -36.7 |  |
| XAUUSD | [3, 4) | 14 | 50 | 1.01 | 14.2 | 41 | 32 | 0.08 | 3.4 | better |
| XAUUSD | [4, 6) | 15 | 53 | 1.35 | 20.2 | 45 | 29 | -0.09 | -4.1 | better |
| XAUUSD | [6, 10) | 10 | 40 | 0.10 | 1.0 | 36 | 28 | 0.04 | 1.4 |  |
| XAUUSD | [10, 1000) | 1 | 100 | 4.58 | 4.6 | 7 | 0 | -1.10 | -7.7 |  |

#### The 1M reading relative to the trade (with / neutral = 50/50 / against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 18 | 50 | -0.04 | -0.7 | 17 | 53 | 0.21 | 3.5 |  |
| BTCUSD | neutral | 6 | 67 | 0.40 | 2.4 | 28 | 25 | -0.56 | -15.6 | worse |
| BTCUSD | with | 65 | 60 | 0.92 | 60.0 | 85 | 32 | -0.35 | -29.5 |  |
| EURUSD | against | 5 | 60 | 1.25 | 6.3 | 23 | 30 | -0.08 | -1.8 |  |
| EURUSD | neutral | 29 | 38 | 0.40 | 11.7 | 42 | 19 | -0.10 | -4.1 | worse |
| EURUSD | with | 13 | 62 | 1.66 | 21.5 | 32 | 31 | 0.15 | 4.7 | better |
| NAS100 | against | 7 | 57 | 1.13 | 7.9 | 13 | 54 | 0.87 | 11.3 | better |
| NAS100 | neutral | 3 | 0 | -1.10 | -3.3 | 8 | 12 | -0.76 | -6.1 | worse (neg) |
| NAS100 | with | 33 | 48 | 0.86 | 28.3 | 79 | 30 | 0.30 | 23.6 |  |
| XAUUSD | against | 27 | 48 | 0.67 | 18.0 | 82 | 33 | -0.11 | -9.3 | better |
| XAUUSD | neutral | 11 | 27 | -0.12 | -1.4 | 106 | 33 | -0.06 | -6.5 |  |
| XAUUSD | with | 105 | 51 | 0.53 | 55.2 | 183 | 26 | -0.25 | -46.4 |  |

#### The 1W reading relative to the trade (with / neutral = 50/50 / against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 17 | 53 | 0.41 | 7.0 | 17 | 59 | 0.33 | 5.6 |  |
| BTCUSD | neutral | 22 | 73 | 0.91 | 20.1 | 21 | 38 | -0.28 | -5.8 |  |
| BTCUSD | with | 50 | 54 | 0.69 | 34.7 | 92 | 27 | -0.45 | -41.4 |  |
| EURUSD | neutral | 25 | 52 | 0.82 | 20.6 | 39 | 18 | -0.39 | -15.2 |  |
| EURUSD | with | 22 | 41 | 0.86 | 18.9 | 58 | 31 | 0.24 | 14.0 |  |
| NAS100 | neutral | 12 | 33 | 0.57 | 6.9 | 38 | 34 | 0.18 | 6.7 | worse |
| NAS100 | with | 31 | 52 | 0.84 | 26.0 | 62 | 31 | 0.36 | 22.1 | better |
| XAUUSD | against | 25 | 48 | 0.39 | 9.7 | 75 | 27 | -0.30 | -22.4 | worse |
| XAUUSD | neutral | 23 | 61 | 0.92 | 21.2 | 99 | 33 | -0.07 | -6.7 | better |
| XAUUSD | with | 95 | 46 | 0.43 | 40.9 | 197 | 29 | -0.17 | -33.1 |  |

#### The 1D reading relative to the trade (with / neutral = 50/50 / against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | with | 89 | 58 | 0.69 | 61.7 | 130 | 33 | -0.32 | -41.6 |  |
| EURUSD | with | 47 | 47 | 0.84 | 39.5 | 97 | 26 | -0.01 | -1.2 |  |
| NAS100 | with | 43 | 47 | 0.77 | 32.9 | 100 | 32 | 0.29 | 28.8 |  |
| XAUUSD | against | 14 | 43 | 0.11 | 1.6 | 53 | 28 | -0.32 | -16.8 | worse |
| XAUUSD | neutral | 35 | 54 | 0.68 | 23.9 | 65 | 35 | -0.02 | -1.1 | better |
| XAUUSD | with | 94 | 48 | 0.49 | 46.4 | 253 | 28 | -0.18 | -44.4 |  |

#### The 4H reading relative to the trade (with / neutral = 50/50 / against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 4 | 100 | 0.73 | 2.9 | 7 | 43 | -0.02 | -0.2 |  |
| BTCUSD | neutral | 20 | 60 | 1.51 | 30.2 | 37 | 30 | -0.41 | -15.1 |  |
| BTCUSD | with | 65 | 55 | 0.44 | 28.6 | 86 | 34 | -0.31 | -26.3 |  |
| EURUSD | neutral | 21 | 43 | 1.10 | 23.2 | 49 | 22 | -0.04 | -2.2 |  |
| EURUSD | with | 26 | 50 | 0.63 | 16.4 | 48 | 29 | 0.02 | 0.9 |  |
| NAS100 | against | 5 | 40 | 0.49 | 2.5 | 16 | 31 | 0.77 | 12.4 |  |
| NAS100 | neutral | 12 | 42 | 0.88 | 10.6 | 28 | 25 | 0.27 | 7.6 |  |
| NAS100 | with | 26 | 50 | 0.76 | 19.9 | 56 | 36 | 0.16 | 8.8 |  |
| XAUUSD | against | 10 | 40 | 1.41 | 14.1 | 17 | 18 | -0.43 | -7.2 |  |
| XAUUSD | neutral | 12 | 42 | -0.02 | -0.2 | 57 | 35 | 0.08 | 4.5 |  |
| XAUUSD | with | 121 | 50 | 0.48 | 58.0 | 297 | 29 | -0.20 | -59.4 |  |

#### The 1H reading relative to the trade (with / neutral = 50/50 / against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 10 | 70 | 2.99 | 29.9 | 14 | 29 | -0.38 | -5.3 |  |
| BTCUSD | neutral | 25 | 60 | 0.41 | 10.4 | 30 | 27 | -0.46 | -13.7 | worse |
| BTCUSD | with | 54 | 56 | 0.40 | 21.5 | 86 | 36 | -0.26 | -22.6 |  |
| EURUSD | with | 47 | 47 | 0.84 | 39.5 | 97 | 26 | -0.01 | -1.2 |  |
| NAS100 | with | 43 | 47 | 0.77 | 32.9 | 100 | 32 | 0.29 | 28.8 |  |
| XAUUSD | with | 143 | 49 | 0.50 | 71.8 | 371 | 30 | -0.17 | -62.2 |  |

#### Number of timeframes at 50/50

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 31 | 52 | 0.26 | 8.1 | 41 | 37 | -0.20 | -8.1 |  |
| BTCUSD | 1 | 43 | 58 | 1.03 | 44.1 | 62 | 35 | -0.27 | -16.8 |  |
| BTCUSD | 2 | 15 | 73 | 0.63 | 9.5 | 27 | 22 | -0.62 | -16.7 | worse |
| EURUSD | 0 | 4 | 50 | 0.73 | 2.9 | 24 | 46 | 0.54 | 13.0 |  |
| EURUSD | 1 | 17 | 53 | 1.17 | 20.0 | 28 | 14 | -0.51 | -14.2 |  |
| EURUSD | 2 | 20 | 45 | 0.72 | 14.5 | 33 | 24 | 0.21 | 7.0 |  |
| EURUSD | 3 | 6 | 33 | 0.36 | 2.2 | 12 | 17 | -0.60 | -7.1 | worse |
| NAS100 | 0 | 20 | 60 | 1.16 | 23.1 | 44 | 34 | 0.33 | 14.7 |  |
| NAS100 | 1 | 19 | 37 | 0.29 | 5.5 | 38 | 34 | 0.53 | 20.1 |  |
| NAS100 | 2 | 4 | 25 | 1.08 | 4.3 | 18 | 22 | -0.33 | -6.0 |  |
| XAUUSD | 0 | 76 | 49 | 0.53 | 40.4 | 113 | 24 | -0.32 | -35.6 |  |
| XAUUSD | 1 | 53 | 47 | 0.36 | 19.3 | 189 | 29 | -0.23 | -43.4 | worse |
| XAUUSD | 2 | 14 | 57 | 0.87 | 12.1 | 69 | 41 | 0.24 | 16.8 | better |

#### Number of timeframes reading with the trade

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 3 | 46 | 63 | 0.88 | 40.7 | 54 | 37 | -0.25 | -13.7 | better |
| BTCUSD | 4 | 30 | 60 | 0.69 | 20.7 | 63 | 32 | -0.31 | -19.3 |  |
| BTCUSD | 5 | 13 | 38 | 0.02 | 0.3 | 13 | 23 | -0.67 | -8.7 | worse |
| EURUSD | 2 | 7 | 29 | 0.15 | 1.1 | 17 | 18 | -0.58 | -9.9 | worse |
| EURUSD | 3 | 22 | 55 | 1.09 | 24.1 | 38 | 24 | 0.15 | 5.7 | better |
| EURUSD | 4 | 15 | 40 | 0.69 | 10.4 | 26 | 23 | -0.20 | -5.3 | worse |
| EURUSD | 5 | 3 | 67 | 1.33 | 4.0 | 16 | 44 | 0.51 | 8.1 | better |
| NAS100 | 3 | 8 | 25 | 0.30 | 2.4 | 28 | 29 | -0.04 | -1.2 | worse |
| NAS100 | 4 | 23 | 48 | 0.86 | 19.7 | 47 | 36 | 0.73 | 34.2 | better |
| NAS100 | 5 | 12 | 58 | 0.90 | 10.8 | 25 | 28 | -0.17 | -4.2 |  |
| XAUUSD | 3 | 46 | 46 | 0.53 | 24.4 | 212 | 34 | -0.06 | -12.8 |  |
| XAUUSD | 4 | 65 | 52 | 0.58 | 38.0 | 130 | 25 | -0.31 | -40.0 |  |
| XAUUSD | 5 | 32 | 47 | 0.29 | 9.4 | 29 | 21 | -0.33 | -9.5 | worse |

#### Which timeframes are 50/50

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 1H | 15 | 53 | 0.29 | 4.4 | 15 | 20 | -0.54 | -8.1 | worse |
| BTCUSD | 1M | 4 | 50 | 0.21 | 0.9 | 17 | 35 | -0.33 | -5.6 |  |
| BTCUSD | 1M+1W | 2 | 100 | 0.77 | 1.5 | 11 | 9 | -0.91 | -10.0 |  |
| BTCUSD | 1W | 11 | 64 | 1.02 | 11.2 | 9 | 78 | 0.59 | 5.3 | better |
| BTCUSD | 1W+1H | 6 | 83 | 0.89 | 5.4 |  |  |  |  |  |
| BTCUSD | 1W+4H | 3 | 67 | 0.65 | 2.0 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | 4H | 13 | 62 | 2.13 | 27.6 | 21 | 29 | -0.40 | -8.4 |  |
| BTCUSD | 4H+1H | 4 | 50 | 0.15 | 0.6 | 15 | 33 | -0.38 | -5.6 | worse |
| BTCUSD | none | 31 | 52 | 0.26 | 8.1 | 41 | 37 | -0.20 | -8.1 |  |
| EURUSD | 1M | 8 | 25 | -0.20 | -1.6 | 7 | 14 | -0.64 | -4.5 | worse (neg) |
| EURUSD | 1M+1W | 7 | 57 | 0.71 | 5.0 | 8 | 12 | -0.64 | -5.1 | worse |
| EURUSD | 1M+1W+4H | 6 | 33 | 0.36 | 2.2 | 12 | 17 | -0.60 | -7.1 | worse |
| EURUSD | 1M+4H | 8 | 38 | 0.77 | 6.2 | 15 | 27 | 0.84 | 12.6 |  |
| EURUSD | 1W | 7 | 71 | 1.44 | 10.1 | 9 | 11 | -0.28 | -2.5 |  |
| EURUSD | 1W+4H | 5 | 40 | 0.67 | 3.3 | 10 | 30 | -0.05 | -0.5 |  |
| EURUSD | 4H | 2 | 100 | 5.73 | 11.5 | 12 | 17 | -0.60 | -7.2 |  |
| EURUSD | none | 4 | 50 | 0.73 | 2.9 | 24 | 46 | 0.54 | 13.0 |  |
| NAS100 | 1M | 1 | 0 | -1.10 | -1.1 | 2 | 0 | -1.10 | -2.2 |  |
| NAS100 | 1M+1W | 2 | 0 | -1.10 | -2.2 | 6 | 17 | -0.65 | -3.9 |  |
| NAS100 | 1W | 8 | 38 | 0.32 | 2.5 | 20 | 45 | 0.63 | 12.7 |  |
| NAS100 | 1W+4H | 2 | 50 | 3.26 | 6.5 | 12 | 25 | -0.17 | -2.1 |  |
| NAS100 | 4H | 10 | 40 | 0.40 | 4.0 | 16 | 25 | 0.60 | 9.7 |  |
| NAS100 | none | 20 | 60 | 1.16 | 23.1 | 44 | 34 | 0.33 | 14.7 |  |
| XAUUSD | 1D | 24 | 46 | 0.35 | 8.4 | 38 | 34 | -0.15 | -5.7 |  |
| XAUUSD | 1M | 5 | 20 | -0.73 | -3.7 | 59 | 25 | -0.32 | -19.1 | worse (neg) |
| XAUUSD | 1M+1D | 4 | 50 | 1.12 | 4.5 | 12 | 50 | 0.60 | 7.2 | better |
| XAUUSD | 1M+1W | 1 | 0 | -1.10 | -1.1 | 25 | 36 | -0.00 | -0.1 |  |
| XAUUSD | 1M+4H | 1 | 0 | -1.10 | -1.1 | 10 | 50 | 0.55 | 5.5 |  |
| XAUUSD | 1W | 14 | 57 | 0.89 | 12.5 | 52 | 31 | -0.21 | -10.8 |  |
| XAUUSD | 1W+1D | 7 | 86 | 1.56 | 10.9 | 15 | 27 | -0.17 | -2.5 |  |
| XAUUSD | 1W+4H | 1 | 0 | -1.10 | -1.1 | 7 | 57 | 0.97 | 6.8 |  |
| XAUUSD | 4H | 10 | 50 | 0.20 | 2.0 | 40 | 28 | -0.19 | -7.8 |  |
| XAUUSD | none | 76 | 49 | 0.53 | 40.4 | 113 | 24 | -0.32 | -35.6 |  |

#### Month x week state (w = with, n = 50/50, a = against)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | MaWa | 7 | 57 | 0.35 | 2.5 | 12 | 50 | 0.09 | 1.0 |  |
| BTCUSD | MaWn | 9 | 56 | -0.11 | -1.0 | 4 | 75 | 0.90 | 3.6 |  |
| BTCUSD | MaWw | 2 | 0 | -1.10 | -2.2 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | MnWa |  |  |  |  | 2 | 100 | 1.16 | 2.3 |  |
| BTCUSD | MnWn | 2 | 100 | 0.77 | 1.5 | 11 | 9 | -0.91 | -10.0 |  |
| BTCUSD | MnWw | 4 | 50 | 0.21 | 0.9 | 15 | 27 | -0.53 | -7.9 | worse |
| BTCUSD | MwWa | 10 | 50 | 0.45 | 4.5 | 3 | 67 | 0.75 | 2.2 |  |
| BTCUSD | MwWn | 11 | 82 | 1.77 | 19.5 | 6 | 67 | 0.10 | 0.6 | better |
| BTCUSD | MwWw | 44 | 57 | 0.82 | 36.0 | 76 | 28 | -0.43 | -32.4 |  |
| EURUSD | MaWn | 3 | 67 | 1.36 | 4.1 | 9 | 11 | -0.68 | -6.1 |  |
| EURUSD | MaWw | 2 | 50 | 1.09 | 2.2 | 14 | 43 | 0.31 | 4.3 |  |
| EURUSD | MnWn | 13 | 46 | 0.55 | 7.1 | 20 | 15 | -0.61 | -12.3 | worse |
| EURUSD | MnWw | 16 | 31 | 0.29 | 4.6 | 22 | 23 | 0.37 | 8.1 |  |
| EURUSD | MwWn | 9 | 56 | 1.04 | 9.4 | 10 | 30 | 0.32 | 3.2 | better |
| EURUSD | MwWw | 4 | 75 | 3.04 | 12.2 | 22 | 32 | 0.07 | 1.5 | better |
| NAS100 | MaWn | 4 | 25 | -0.49 | -1.9 | 9 | 44 | 0.66 | 5.9 |  |
| NAS100 | MaWw | 3 | 100 | 3.28 | 9.8 | 4 | 75 | 1.35 | 5.4 | better |
| NAS100 | MnWn | 2 | 0 | -1.10 | -2.2 | 6 | 17 | -0.65 | -3.9 |  |
| NAS100 | MnWw | 1 | 0 | -1.10 | -1.1 | 2 | 0 | -1.10 | -2.2 |  |
| NAS100 | MwWn | 6 | 50 | 1.83 | 11.0 | 23 | 35 | 0.20 | 4.7 |  |
| NAS100 | MwWw | 27 | 48 | 0.64 | 17.3 | 56 | 29 | 0.34 | 18.9 |  |
| XAUUSD | MaWa | 14 | 43 | 0.25 | 3.5 | 14 | 29 | -0.28 | -3.9 | worse |
| XAUUSD | MaWn | 6 | 67 | 1.77 | 10.6 | 15 | 47 | 0.27 | 4.0 | better |
| XAUUSD | MaWw | 7 | 43 | 0.56 | 3.9 | 53 | 30 | -0.18 | -9.5 |  |
| XAUUSD | MnWa |  |  |  |  | 18 | 17 | -0.48 | -8.6 |  |
| XAUUSD | MnWn | 1 | 0 | -1.10 | -1.1 | 25 | 36 | -0.00 | -0.1 |  |
| XAUUSD | MnWw | 10 | 30 | -0.03 | -0.3 | 63 | 37 | 0.03 | 2.2 |  |
| XAUUSD | MwWa | 11 | 55 | 0.56 | 6.2 | 43 | 30 | -0.23 | -10.0 |  |
| XAUUSD | MwWn | 16 | 62 | 0.73 | 11.7 | 59 | 29 | -0.18 | -10.6 |  |
| XAUUSD | MwWw | 78 | 49 | 0.48 | 37.3 | 81 | 22 | -0.32 | -25.8 |  |

#### Consecutive losses before the trade (same market, banded)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | 0 | 53 | 49 | 0.59 | 31.0 | 45 | 42 | -0.09 | -3.8 |  |
| BTCUSD | 1 | 26 | 73 | 0.50 | 13.0 | 24 | 42 | -0.21 | -5.1 |  |
| BTCUSD | 2 | 7 | 57 | 1.75 | 12.3 | 14 | 29 | -0.57 | -7.9 |  |
| BTCUSD | 3+ | 3 | 100 | 1.78 | 5.4 | 47 | 21 | -0.53 | -24.8 |  |
| EURUSD | 0 | 23 | 43 | 0.52 | 11.9 | 28 | 25 | -0.11 | -3.1 | worse |
| EURUSD | 1 | 12 | 42 | 0.79 | 9.5 | 19 | 37 | 0.18 | 3.4 |  |
| EURUSD | 2 | 7 | 57 | 1.36 | 9.6 | 13 | 8 | -0.66 | -8.6 |  |
| EURUSD | 3+ | 5 | 60 | 1.73 | 8.6 | 37 | 27 | 0.19 | 7.1 | better |
| NAS100 | 0 | 21 | 38 | 0.55 | 11.5 | 33 | 33 | 0.46 | 15.2 |  |
| NAS100 | 1 | 13 | 62 | 0.98 | 12.7 | 22 | 23 | -0.33 | -7.3 |  |
| NAS100 | 2 | 4 | 25 | -0.05 | -0.2 | 17 | 29 | 0.04 | 0.6 | worse |
| NAS100 | 3+ | 5 | 60 | 1.78 | 8.9 | 28 | 39 | 0.72 | 20.2 | better |
| XAUUSD | 0 | 71 | 51 | 0.52 | 36.9 | 116 | 29 | -0.13 | -15.1 |  |
| XAUUSD | 1 | 35 | 46 | 0.54 | 18.8 | 78 | 29 | -0.21 | -16.3 |  |
| XAUUSD | 2 | 18 | 39 | 0.15 | 2.8 | 56 | 27 | -0.14 | -7.6 |  |
| XAUUSD | 3+ | 19 | 58 | 0.71 | 13.4 | 121 | 31 | -0.19 | -23.3 |  |

#### The previous trade's result (same market)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | be |  |  |  |  | 1 | 100 | 1.10 | 1.1 |  |
| BTCUSD | loss | 36 | 72 | 0.85 | 30.7 | 85 | 28 | -0.44 | -37.8 |  |
| BTCUSD | none | 1 | 0 | -1.10 | -1.1 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | win | 52 | 50 | 0.62 | 32.1 | 43 | 42 | -0.09 | -3.8 |  |
| EURUSD | be | 1 | 100 | 3.75 | 3.7 | 4 | 50 | 0.47 | 1.9 |  |
| EURUSD | loss | 24 | 50 | 1.15 | 27.7 | 67 | 25 | 0.02 | 1.1 |  |
| EURUSD | none | 1 | 0 | -1.10 | -1.1 | 1 | 0 | -1.10 | -1.1 |  |
| EURUSD | win | 21 | 43 | 0.44 | 9.2 | 25 | 24 | -0.13 | -3.1 | worse |
| NAS100 | be |  |  |  |  | 2 | 0 | -1.10 | -2.2 |  |
| NAS100 | loss | 22 | 55 | 0.97 | 21.4 | 65 | 32 | 0.24 | 15.8 |  |
| NAS100 | none | 1 | 0 | -1.10 | -1.1 | 1 | 100 | 0.70 | 0.7 |  |
| NAS100 | win | 20 | 40 | 0.63 | 12.6 | 32 | 31 | 0.45 | 14.5 |  |
| XAUUSD | be | 2 | 0 | -1.10 | -2.2 | 14 | 36 | -0.20 | -2.7 |  |
| XAUUSD | loss | 71 | 48 | 0.51 | 36.1 | 246 | 29 | -0.19 | -47.2 |  |
| XAUUSD | none | 1 | 0 | -1.10 | -1.1 | 1 | 100 | 2.56 | 2.6 |  |
| XAUUSD | win | 69 | 52 | 0.57 | 39.1 | 110 | 29 | -0.13 | -14.8 |  |

#### Minutes from the visit's first touch to the signal close

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-1.0, 10.0) | 2 | 50 | 0.04 | 0.1 |  |  |  |  |  |
| BTCUSD | [10.0, 15.0) | 7 | 14 | -0.80 | -5.6 | 3 | 33 | -0.11 | -0.3 |  |
| BTCUSD | [15.0, 20.0) | 3 | 33 | -0.40 | -1.2 | 3 | 33 | -0.45 | -1.3 | worse (neg) |
| BTCUSD | [20.0, 30.0) | 7 | 43 | -0.03 | -0.2 | 8 | 25 | -0.55 | -4.4 | worse (neg) |
| BTCUSD | [30.0, 45.0) | 8 | 62 | 1.76 | 14.1 | 7 | 29 | -0.42 | -2.9 |  |
| BTCUSD | [45.0, 60.0) | 6 | 50 | 0.03 | 0.2 | 2 | 100 | 1.22 | 2.4 |  |
| BTCUSD | [60.0, 120.0) | 8 | 50 | 0.03 | 0.3 | 14 | 36 | -0.18 | -2.5 |  |
| BTCUSD | [120.0, 1000000000.0) | 48 | 71 | 1.13 | 54.1 | 93 | 32 | -0.35 | -32.6 |  |
| EURUSD | [-1.0, 10.0) | 1 | 100 | 4.58 | 4.6 |  |  |  |  |  |
| EURUSD | [10.0, 15.0) | 1 | 100 | 1.99 | 2.0 | 1 | 100 | 2.00 | 2.0 |  |
| EURUSD | [15.0, 20.0) | 3 | 0 | -1.10 | -3.3 | 8 | 12 | -0.56 | -4.5 | worse (neg) |
| EURUSD | [20.0, 30.0) | 5 | 40 | 0.22 | 1.1 | 5 | 0 | -1.10 | -5.5 | worse |
| EURUSD | [30.0, 45.0) | 4 | 50 | 0.51 | 2.0 | 9 | 0 | -1.10 | -9.9 | worse |
| EURUSD | [45.0, 60.0) | 4 | 75 | 1.83 | 7.3 | 8 | 38 | 0.12 | 1.0 | better |
| EURUSD | [60.0, 120.0) | 8 | 25 | 0.16 | 1.3 | 16 | 31 | 0.21 | 3.3 |  |
| EURUSD | [120.0, 1000000000.0) | 21 | 52 | 1.17 | 24.5 | 50 | 30 | 0.25 | 12.3 | better |
| NAS100 | [10.0, 15.0) | 1 | 0 | -1.10 | -1.1 | 4 | 0 | -1.10 | -4.4 |  |
| NAS100 | [15.0, 20.0) | 2 | 50 | 0.78 | 1.6 | 2 | 50 | 2.75 | 5.5 |  |
| NAS100 | [20.0, 30.0) | 2 | 100 | 4.70 | 9.4 | 11 | 36 | 1.10 | 12.1 |  |
| NAS100 | [30.0, 45.0) | 6 | 33 | -0.11 | -0.6 | 16 | 25 | 0.12 | 1.8 | worse |
| NAS100 | [45.0, 60.0) | 5 | 80 | 2.26 | 11.3 | 5 | 40 | 0.33 | 1.6 |  |
| NAS100 | [60.0, 120.0) | 7 | 29 | -0.11 | -0.8 | 17 | 24 | -0.21 | -3.6 | worse (neg) |
| NAS100 | [120.0, 1000000000.0) | 20 | 45 | 0.66 | 13.2 | 45 | 38 | 0.35 | 15.7 |  |
| XAUUSD | [-1.0, 10.0) | 2 | 50 | 0.42 | 0.8 | 1 | 0 | -1.10 | -1.1 |  |
| XAUUSD | [10.0, 15.0) | 2 | 0 | -0.60 | -1.2 | 6 | 50 | 0.68 | 4.1 |  |
| XAUUSD | [15.0, 20.0) | 4 | 25 | -0.50 | -2.0 | 19 | 21 | -0.62 | -11.8 | worse (neg) |
| XAUUSD | [20.0, 30.0) | 6 | 17 | -0.39 | -2.3 | 33 | 33 | 0.01 | 0.4 |  |
| XAUUSD | [30.0, 45.0) | 14 | 43 | 0.62 | 8.7 | 34 | 41 | 0.04 | 1.4 | better |
| XAUUSD | [45.0, 60.0) | 12 | 58 | 0.82 | 9.8 | 25 | 32 | -0.29 | -7.2 |  |
| XAUUSD | [60.0, 120.0) | 23 | 48 | 0.56 | 12.8 | 48 | 27 | -0.17 | -8.1 |  |
| XAUUSD | [120.0, 1000000000.0) | 80 | 54 | 0.56 | 45.2 | 205 | 28 | -0.19 | -39.9 |  |

#### Hours from the zone forming to its first touch

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0, 2) | 29 | 69 | 0.88 | 25.5 | 56 | 34 | -0.32 | -17.8 |  |
| BTCUSD | [2, 4) | 14 | 64 | 0.54 | 7.5 | 24 | 38 | -0.27 | -6.4 |  |
| BTCUSD | [4, 8) | 26 | 62 | 0.35 | 9.0 | 29 | 28 | -0.36 | -10.5 |  |
| BTCUSD | [8, 12) | 9 | 33 | -0.02 | -0.2 | 6 | 50 | -0.01 | -0.0 |  |
| BTCUSD | [12, 24) | 10 | 30 | 1.92 | 19.2 | 14 | 29 | -0.41 | -5.8 |  |
| BTCUSD | [24, 1000) | 1 | 100 | 0.67 | 0.7 | 1 | 0 | -1.10 | -1.1 |  |
| EURUSD | [0, 2) | 27 | 59 | 1.40 | 37.8 | 54 | 17 | -0.43 | -23.2 |  |
| EURUSD | [2, 4) | 3 | 0 | -1.10 | -3.3 | 13 | 31 | 0.07 | 0.9 |  |
| EURUSD | [4, 8) | 12 | 42 | 0.52 | 6.2 | 17 | 47 | 1.29 | 21.9 |  |
| EURUSD | [8, 12) | 1 | 0 | -1.10 | -1.1 | 6 | 50 | 0.62 | 3.7 |  |
| EURUSD | [12, 24) | 3 | 33 | 0.36 | 1.1 | 6 | 0 | -1.10 | -6.6 | worse |
| EURUSD | [24, 1000) | 1 | 0 | -1.10 | -1.1 | 1 | 100 | 1.98 | 2.0 |  |
| NAS100 | [0, 2) | 27 | 44 | 0.51 | 13.8 | 63 | 22 | -0.05 | -3.1 | worse |
| NAS100 | [2, 4) | 5 | 40 | 1.36 | 6.8 | 20 | 55 | 1.35 | 26.9 | better |
| NAS100 | [4, 8) | 7 | 57 | 1.18 | 8.2 | 9 | 44 | 0.64 | 5.7 | better |
| NAS100 | [8, 12) | 3 | 33 | 0.59 | 1.8 | 2 | 0 | -1.10 | -2.2 |  |
| NAS100 | [12, 24) | 1 | 100 | 2.31 | 2.3 | 5 | 60 | 0.50 | 2.5 |  |
| NAS100 | [24, 1000) |  |  |  |  | 1 | 0 | -1.10 | -1.1 |  |
| XAUUSD | [0, 2) | 86 | 47 | 0.49 | 41.9 | 194 | 31 | -0.10 | -18.6 |  |
| XAUUSD | [2, 4) | 22 | 55 | 0.49 | 10.7 | 64 | 31 | -0.19 | -12.4 |  |
| XAUUSD | [4, 8) | 27 | 48 | 0.48 | 13.1 | 73 | 23 | -0.29 | -21.1 |  |
| XAUUSD | [8, 12) | 5 | 40 | 0.11 | 0.5 | 18 | 39 | 0.05 | 0.9 |  |
| XAUUSD | [12, 24) | 3 | 100 | 1.87 | 5.6 | 22 | 27 | -0.50 | -11.0 |  |

#### With / against the sign of the 60-day daily return

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 21 | 52 | 0.77 | 16.1 | 29 | 41 | -0.15 | -4.3 | better |
| BTCUSD | with | 68 | 60 | 0.67 | 45.6 | 101 | 31 | -0.37 | -37.4 |  |
| EURUSD | against | 10 | 40 | 0.17 | 1.7 | 15 | 0 | -1.03 | -15.5 | worse |
| EURUSD | with | 37 | 49 | 1.02 | 37.9 | 82 | 30 | 0.17 | 14.3 | better |
| NAS100 | against | 7 | 43 | 0.77 | 5.4 | 18 | 39 | 0.06 | 1.1 |  |
| NAS100 | with | 36 | 47 | 0.76 | 27.5 | 82 | 30 | 0.34 | 27.7 |  |
| XAUUSD | against | 37 | 57 | 0.72 | 26.8 | 110 | 25 | -0.30 | -33.4 |  |
| XAUUSD | with | 106 | 46 | 0.43 | 45.1 | 261 | 31 | -0.11 | -28.8 |  |

#### With / against the sign of the 20-day daily return

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | against | 13 | 54 | 0.50 | 6.5 | 17 | 53 | 0.19 | 3.2 |  |
| BTCUSD | with | 76 | 59 | 0.73 | 55.2 | 113 | 30 | -0.40 | -44.8 |  |
| EURUSD | against | 11 | 27 | -0.16 | -1.8 | 17 | 35 | 0.73 | 12.4 |  |
| EURUSD | with | 36 | 53 | 1.15 | 41.3 | 80 | 24 | -0.17 | -13.7 |  |
| NAS100 | against | 6 | 50 | 1.92 | 11.5 | 11 | 36 | 0.30 | 3.3 |  |
| NAS100 | with | 37 | 46 | 0.58 | 21.4 | 89 | 31 | 0.29 | 25.5 |  |
| XAUUSD | against | 37 | 46 | 0.35 | 12.9 | 109 | 28 | -0.29 | -32.0 | worse |
| XAUUSD | with | 106 | 50 | 0.56 | 59.0 | 262 | 31 | -0.12 | -30.2 | better |

#### Hours in the trade (an outcome, not a filter)

| market | bucket | IS n | IS win | IS R/t | IS R | OOS n | OOS win | OOS R/t | OOS R | both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0, 1) | 32 | 56 | 0.05 | 1.6 | 51 | 27 | -0.57 | -29.3 | worse |
| BTCUSD | [1, 2) | 18 | 56 | 0.37 | 6.7 | 24 | 38 | -0.26 | -6.3 |  |
| BTCUSD | [2, 4) | 15 | 53 | -0.00 | -0.1 | 29 | 24 | -0.41 | -12.0 | worse (neg) |
| BTCUSD | [4, 8) | 10 | 70 | 3.13 | 31.3 | 11 | 64 | 0.60 | 6.6 | better |
| BTCUSD | [8, 24) | 9 | 67 | 2.03 | 18.2 | 12 | 50 | 0.22 | 2.7 | better |
| BTCUSD | [24, 48) | 3 | 67 | 1.29 | 3.9 | 1 | 0 | -1.10 | -1.1 |  |
| BTCUSD | [48, 1000) | 2 | 50 | 0.06 | 0.1 | 2 | 0 | -1.10 | -2.2 |  |
| EURUSD | [0, 1) | 22 | 32 | -0.06 | -1.2 | 55 | 16 | -0.58 | -32.0 | worse (neg) |
| EURUSD | [1, 2) | 6 | 33 | 0.48 | 2.9 | 12 | 17 | -0.60 | -7.2 | worse |
| EURUSD | [2, 4) | 6 | 83 | 2.47 | 14.8 | 6 | 17 | -0.23 | -1.4 |  |
| EURUSD | [4, 8) | 5 | 40 | 0.12 | 0.6 | 11 | 45 | 1.07 | 11.8 |  |
| EURUSD | [8, 24) | 4 | 50 | 1.42 | 5.7 | 3 | 67 | 0.74 | 2.2 | better |
| EURUSD | [24, 48) | 2 | 100 | 5.18 | 10.4 | 3 | 100 | 2.59 | 7.8 |  |
| EURUSD | [48, 1000) | 2 | 100 | 3.21 | 6.4 | 7 | 43 | 2.50 | 17.5 |  |
| NAS100 | [0, 1) | 23 | 22 | -0.39 | -9.1 | 42 | 12 | -0.75 | -31.5 | worse (neg) |
| NAS100 | [1, 2) | 5 | 80 | 3.00 | 15.0 | 12 | 17 | -0.24 | -2.9 |  |
| NAS100 | [2, 4) | 8 | 75 | 2.10 | 16.8 | 18 | 50 | 0.53 | 9.6 | better |
| NAS100 | [4, 8) | 1 | 100 | 3.09 | 3.1 | 14 | 36 | 0.53 | 7.4 |  |
| NAS100 | [8, 24) | 3 | 33 | 0.07 | 0.2 | 9 | 67 | 3.13 | 28.2 |  |
| NAS100 | [24, 48) |  |  |  |  | 3 | 100 | 5.26 | 15.8 |  |
| NAS100 | [48, 1000) | 3 | 100 | 2.29 | 6.9 | 2 | 100 | 1.12 | 2.2 |  |
| XAUUSD | [0, 1) | 39 | 33 | -0.19 | -7.4 | 132 | 21 | -0.54 | -71.9 | worse (neg) |
| XAUUSD | [1, 2) | 28 | 43 | 0.15 | 4.2 | 58 | 22 | -0.34 | -19.7 | worse |
| XAUUSD | [2, 4) | 19 | 42 | 0.18 | 3.4 | 47 | 23 | -0.39 | -18.2 | worse |
| XAUUSD | [4, 8) | 19 | 58 | 1.16 | 22.0 | 45 | 49 | 0.47 | 21.1 | better |
| XAUUSD | [8, 24) | 23 | 74 | 1.48 | 34.2 | 38 | 29 | 0.00 | 0.1 | better |
| XAUUSD | [24, 48) | 6 | 33 | -0.11 | -0.6 | 20 | 55 | 0.91 | 18.2 |  |
| XAUUSD | [48, 1000) | 9 | 78 | 1.79 | 16.1 | 31 | 45 | 0.26 | 8.1 | better |
