# Regime gates per market (14 October 2026)

The regime at the signal against the trade's outcome, per market, in-sample 2024-01..2026-09 (IS) and out-of-sample
2017..2023 (OOS; BTC 2020-06..2023), on the research ledgers of the live set (`aca/eutwo_EURUSD`, `aca/base_XAUUSD`,
`aca/rr08_NAS100`, `aca/base_BTCUSD` and their `oos_` twins; R after 0.10R costs; a win is r > 0). Every feature is read
on CLOSED candles at the signal time (`confirmed_close_at`); the daily bar still forming at the signal is never used
(the earlier `regime/regime.py` labelled with the forming bar, `searchsorted - 1`, a one-day look-ahead; the 0.35 line
it reported for gold is that artefact, see `market_XAUUSD.md`). BTC was labelled on the UTC candles the ledgers were
built from and again on the New-York-anchored `btc_ny_old/` candles: the two labellings agree on every conclusion.

Features: `er20` = daily 20-day efficiency ratio |c - c[-20]| / sum|dc|; `atr_pct` = the last closed daily ATR14
ranked among the previous 252 daily ATR14 values (0-100); `t4h` = the last closed 4H close above / below the simple
mean of the last 50 closed 4H closes, `with4h` = that state relative to the trade's direction (long above / short
below = with); `wk` = the week's range so far (closed 1H candles since Sunday 17:00 New York) / the mean range of the
previous 20 full weeks, `pace` = the same per elapsed share of the 120-hour week; `wd_formed` / `wd_touch` /
`wd_open` = the weekday (Amsterdam) of the zone's formation, the visit's first touch and the fill.

Scripts (all under `S/research/regime_gate/`, S = the scratchpad): `regime_gate.py` (labels, bucket tables, the rule
scan with the subset-permutation p of `ledgers_candidates.py`, plateaus; output `regime_gate.out`, on the NY-anchored
BTC candles `regime_gate_ny.out`; the labelled trades `regime_trades.csv`, the scan `regime_scan.csv`), `checks.py`
(plateau of the trend rule over the mean's length and timeframe, by year, composition, the gold stacks, NAS100 and BTC
checks; `checks.out`), `regime_sim.py` (the FTMO 2-Step replay of `aca/challenge_sim_btc.py` / `challenge_sim_oos.py`
with the gates applied to the labelled trades, both periods; `regime_sim.out`), `now.py` + `now_bars.json` (today's
regime from TradingView bars; `now.out`).

## 1. The short answer

- **One new rule holds in both periods: gold, no trade against the 4H 50-candle mean** (a long only with the last closed
  4H close above the mean of the last 50 closed 4H closes, a short only below). It removes 18 of 143 in-sample trades
  worth +0.5R (33 % won; 2024 +3.1R, 2025 -0.3R, 2026 -2.3R) and 67 of 371 out-of-sample trades worth -30.3R (18 %
  won, 50 stopped), negative in all seven out-of-sample years; permutation p IS 0.12 / OOS 0.03. It is a plateau, not a
  peak: the against-the-mean bucket is -23 to -36R out of sample for every mean from 4H x 40 to 4H x 120, 1H x 200-300
  and daily x 10-20, while the in-sample bucket is between -3.5R and +7.8R (+0.5R at 50, -3.5R at 60, -3.1R at 80).
  Gold's out-of-sample ledger goes -62.2R -> -31.9R, the dip -83 -> -55R; in sample +71.8 -> +71.3R.
- The two regime rules already on the table are confirmed on the closed-bar labelling: **gold at half stake when
  ER20 < 0.2** (IS -9.8R of 71.8, OOS +30.7R; the task's 0.25 line is a worse line: -15.4R IS for +31.0R OOS) and **no
  NAS100 trade at ER20 >= 0.5** (7 trades -1.6R IS, 10 trades -6.7R OOS; thin).
- **Nothing else holds.** The ATR14 percentile against the trailing year, the week's range spent, its pace, and the
  weekday of the zone's formation or first touch all turn between the periods on every market. BTC has no regime cut
  at all (every in-sample bucket positive, every out-of-sample bucket negative, on UTC and on New-York candles).
  EURUSD's only both-period signal (against a 4H x 20-40 mean: 6-7 % won OOS) wins in sample and flips sign at 50.
- **NAS100's counter-trend trades are its best in both periods** (against the daily 5-candle mean: IS 10 trades +8.0R,
  +0.80 a trade; OOS 22 trades +34.1R, +1.55 a trade against a base of +0.29): the index's whole out-of-sample edge is
  pullback longs below a falling short mean. Too thin for a double stake; it says a trend filter on NAS100 would remove
  its best trades, so the gold rule is gold's only.
- **The challenge replay** (FTMO 2-Step, the live stakes, two slots): the gold trend gate doubles the out-of-sample pass
  rate (both phases 11 % -> 20 % of 1,694 starts; funded month -0.57 -> +0.01 %) and costs speed in sample (both phases
  median 84 -> 97 days; 2026 starts passing within 6 weeks 71 -> 67 %): the two in-sample 4H-zone trades it removes
  were worth +3.5R at the double stake. All three gates together: OOS 25 %, +0.39 %/month; IS median 75 days but within 6 weeks 47 %.
- **Today** (14 October, TradingView, closed bars): gold's 4H close 4083.6 sits 1.65 % below its 50-candle mean and its
  ER20 is 0.17: the trend gate would refuse gold longs and allow shorts this week, the ER rule would halve gold's stake.
  NAS100 ER20 0.36 (gate off). EURUSD ER20 0.55, 4H below. BTC ER20 0.08, 4H below.

## 2. Base

| market | IS n / win / R a trade / sum | OOS n / win / R a trade / sum |
|---|---|---|
| BTCUSD | 89 / 58 % / +0.69 / +61.7R | 130 / 33 % / -0.32 / -41.6R |
| EURUSD | 47 / 47 % / +0.84 / +39.6R | 97 / 26 % / -0.01 / -1.3R |
| NAS100 | 43 / 47 % / +0.77 / +32.9R | 100 / 32 % / +0.29 / +28.8R |
| XAUUSD | 143 / 49 % / +0.50 / +71.8R | 371 / 30 % / -0.17 / -62.2R |

## 3. Buckets (n / win % / R a trade / sum R; IS then OOS)

### 3.1 Daily ER20 on the last closed bar

| market | < 0.25 | 0.25-0.35 | 0.35-0.5 | > 0.5 |
|---|---|---|---|---|
| BTC IS | 47 / 49 / +0.54 / +25.3 | 16 / 69 / +0.75 / +12.0 | 16 / 81 / +1.44 / +23.0 | 10 / 50 / +0.14 / +1.4 |
| BTC OOS | 59 / 39 / -0.23 / -13.5 | 19 / 32 / -0.34 / -6.5 | 28 / 25 / -0.54 / -15.3 | 24 / 29 / -0.26 / -6.3 |
| EURUSD IS | 33 / 45 / +0.74 / +24.4 | 6 / 67 / +1.28 / +7.7 | 8 / 38 / +0.93 / +7.5 | 0 |
| EURUSD OOS | 47 / 30 / +0.30 / +13.9 | 17 / 24 / -0.40 / -6.7 | 22 / 14 / -0.51 / -11.3 | 11 / 36 / +0.26 / +2.9 |
| NAS100 IS | 19 / 47 / +0.92 / +17.5 | 4 / 100 / +3.06 / +12.2 | 13 / 38 / +0.37 / +4.8 | **7 / 29 / -0.23 / -1.6** |
| NAS100 OOS | 46 / 41 / +0.59 / +27.3 | 24 / 25 / +0.19 / +4.6 | 20 / 25 / +0.17 / +3.5 | **10 / 20 / -0.67 / -6.7** |
| XAUUSD IS | 69 / 49 / +0.45 / +30.7 | 35 / 60 / +0.75 / +26.2 | 13 / 38 / +0.80 / +10.4 | 26 / 38 / +0.18 / +4.6 |
| XAUUSD OOS | **195 / 26 / -0.32 / -61.9** | 59 / 32 / -0.05 / -3.1 | 77 / 35 / +0.06 / +5.0 | 40 / 35 / -0.06 / -2.2 |

With the 0.2 line (the gold report's): gold < 0.2 IS 59 / 47 / +0.33 / +19.6, OOS 169 / 24 / -0.36 / -61.4; 0.2-0.35 IS
45 / 60 / +0.83 / +37.3, OOS 85 / 33 / -0.04 / -3.6. The plateau of a gate below a line (IS delta / OOS delta): gold
0.15: -19.6 / +31.9; 0.2: -19.6 / +61.4; 0.25: -30.7 / +61.9; 0.3: -36.9 / +73.3; 0.35: -56.9 / +65.0. So 0.2 is the
cheapest line for the same OOS gain (as a half stake: -9.8 / +30.7); 0.25 costs 11R more in sample for 0.5R more out.
Above a line: NAS100 0.5: +1.6 / +6.7 (17 trades, negative in six of seven year-cells); 0.45: -0.6 / +2.5; 0.55: +2.4 /
+3.0. EURUSD, BTC: every ER cut costs in sample what it gains out of sample or the reverse (table in `regime_gate.out`).

### 3.2 Daily ATR14 percentile over the previous 252 days (new; period-neutral by construction)

| market | < 30 | 30-70 | > 70 |
|---|---|---|---|
| BTC IS | 30 / 53 / +1.23 / +36.9 | 22 / 82 / +0.87 / +19.2 | 37 / 49 / +0.15 / +5.6 |
| BTC OOS | 49 / 41 / -0.11 / -5.4 | 43 / 16 / -0.68 / -29.4 | 38 / 42 / -0.18 / -6.8 |
| EURUSD IS | 18 / 44 / +0.55 / +10.0 | 14 / 43 / +0.71 / +9.9 | 15 / 53 / +1.31 / +19.6 |
| EURUSD OOS | 44 / 32 / +0.41 / +17.9 | 30 / 23 / -0.35 / -10.5 | 23 / 17 / -0.38 / -8.7 |
| NAS100 IS | 9 / 33 / -0.07 / -0.6 | 13 / 46 / +1.02 / +13.2 | 21 / 52 / +0.97 / +20.3 |
| NAS100 OOS | 34 / 38 / +0.97 / +33.0 | 33 / 30 / +0.13 / +4.3 | 33 / 27 / -0.26 / -8.5 |
| XAUUSD IS | 3 / 67 / +1.10 / +3.3 | 52 / 56 / +0.73 / +38.2 | 88 / 44 / +0.34 / +30.3 |
| XAUUSD OOS | 131 / 34 / -0.10 / -13.4 | 135 / 26 / -0.28 / -38.0 | 105 / 29 / -0.10 / -10.9 |

Nothing holds: the best in-sample band is the worst out-of-sample band on BTC (30-70), EURUSD and NAS100 (> 70), and
gold's > 70 is under the base in sample and above it out of sample. Plateau sweeps (gate below 10-50, above 50-90)
show no threshold with the same sign of delta in both periods on any market. Negative result, not to be rerun.

### 3.3 The 4H trend: the last closed 4H close against the mean of the last 50 closed 4H closes

Raw state (above / below) turns between the periods on every market (BTC below: IS +1.07 a trade, OOS -0.28; EURUSD
above: IS +1.54, OOS -0.00; NAS100 below: IS +1.47, OOS +0.61; gold above/below: IS +0.50/+0.50, OOS -0.15/-0.19).
Relative to the direction:

| market | with (IS) | against (IS) | with (OOS) | against (OOS) |
|---|---|---|---|---|
| BTC | 84 / 61 / +0.78 / +65.2 | 5 / 20 / -0.70 / -3.5 | 121 / 31 / -0.39 / -46.6 | 9 / 56 / +0.56 / +5.0 |
| EURUSD | 40 / 50 / +0.93 / +37.0 | 7 / 29 / +0.36 / +2.5 | 84 / 27 / -0.06 / -4.8 | 13 / 15 / +0.27 / +3.5 |
| NAS100 | 40 / 45 / +0.65 / +26.1 | 3 / 67 / +2.26 / +6.8 | 85 / 33 / +0.18 / +15.5 | 15 / 27 / +0.89 / +13.3 |
| XAUUSD | 125 / 51 / +0.57 / +71.3 | **18 / 33 / +0.03 / +0.5** | 304 / 32 / -0.10 / -31.9 | **67 / 18 / -0.45 / -30.3** |

Gold's against-the-mean bucket is under the base in both periods (p 0.12 / 0.03; a gate helps 2 of 3 IS years, 7 of 7
OOS years). The plateau over the mean's length and timeframe (against bucket: n / win / sum R, IS | OOS):

| mean | IS | OOS | | mean | IS | OOS |
|---|---|---|---|---|---|---|
| 4H x 20 | 13 / 31 % / +7.8 | 37 / 22 % / -3.3 | | 4H x 100 | 18 / 39 % / +6.0 | 70 / 23 % / -28.4 |
| 4H x 30 | 15 / 27 % / +5.8 | 48 / 23 % / -13.0 | | 4H x 120 | 19 / 42 % / +6.9 | 80 / 26 % / -25.8 |
| 4H x 40 | 18 / 33 % / +7.7 | 59 / 20 % / -22.6 | | 1H x 200 | 15 / 33 % / +0.8 | 63 / 19 % / -26.8 |
| **4H x 50** | **18 / 33 % / +0.5** | **67 / 18 % / -30.3** | | 1H x 300 | 17 / 29 % / -2.0 | 66 / 23 % / -25.6 |
| 4H x 60 | 14 / 29 % / -3.5 | 66 / 20 % / -27.3 | | 1D x 10 | 29 / 41 % / +6.0 | 100 / 24 % / -31.6 |
| 4H x 80 | 18 / 28 % / -3.1 | 65 / 22 % / -28.6 | | 1D x 15 | 25 / 36 % / +3.7 | 90 / 23 % / -35.7 |

With the entry price instead of the last 4H close as "price": IS 13 trades -2.7R, OOS 59 trades -27.4R (the same
rule). What the removed gold trades are: IS 16 1H-zone + 2 4H-zone (the 4H pair +3.5R at double stake, which is what
slows the in-sample replay), 14 longs / 4 shorts, 10 of 18 with ER20 < 0.2; OOS 59 1H / 8 4H (-21.5 / -8.8R), 36 longs
(-8.2R) / 31 shorts (-22.1R), 41 of 67 with ER20 < 0.2, 50 stopped, 12 targets, 5 break-evens. By year: IS 2024 8 trades
+3.1R, 2025 3 -0.3R, 2026 7 -2.3R; OOS 2017 -6.0, 2018 -2.9, 2019 -2.1, 2020 -4.7, 2021 -7.9 (0 of 9 won), 2022 -6.7
(0 of 7), 2023 -0.1.

Same bucket on the other markets: EURUSD against a 4H x 20 / 30 / 40 mean loses OOS (16 / 15 / 12 trades, 6 / 7 / 0 %
won, -13.7 / -12.3 / -13.2R) but wins IS (+8.8 / +6.6 / +2.5R) and from 50 on the OOS sign flips (+3.5R at 50, +6.8 at
60): a narrow window, no rule. NAS100's against bucket is above the base in both periods at every length (4H x 20-60:
IS +4.6 to +8.1R on 3-7 trades, OOS +13.3 to +15.9R on 9-24; daily x 5: IS 10 trades +8.0R, OOS 22 trades +34.1R of the
period's +28.8R; 18 of the 22 are longs). BTC: 5-12 trades either way, the sign turns at 40 (IS -5.7 / OOS +2.7).

### 3.4 The week's range so far against the average week (new)

| market | < 0.5 | 0.5-1.0 | > 1.0 |
|---|---|---|---|
| BTC IS / OOS | 29 / +0.40 / +11.6 ; 56 / -0.23 / -12.7 | 35 / +1.39 / +48.8 ; 35 / -0.64 / -22.2 | 25 / +0.05 / +1.3 ; 39 / -0.17 / -6.8 |
| EURUSD IS / OOS | 19 / +0.85 / +16.2 ; 35 / -0.33 / -11.4 | 20 / +0.43 / +8.6 ; 40 / +0.44 / +17.4 | 8 / +1.85 / +14.8 ; 18 / -0.31 / -5.6 |
| NAS100 IS / OOS | 15 / +0.49 / +7.4 ; 41 / +0.60 / +24.6 | 22 / +0.46 / +10.0 ; 49 / +0.11 / +5.6 | 6 / +2.58 / +15.5 ; 10 / -0.13 / -1.4 |
| XAUUSD IS / OOS | 44 / +0.85 / +37.2 ; 119 / -0.05 / -6.0 | 65 / +0.38 / +24.7 ; 191 / -0.28 / -53.8 | 34 / +0.29 / +9.9 ; 61 / -0.04 / -2.4 |

(n / R a trade / sum.) The pace variant (range per elapsed share of the week: < 0.8 / 0.8-1.2 / > 1.2) is as mixed:
gold +0.56 / +0.67 / +0.43 in sample, -0.27 / -0.12 / -0.17 out; BTC +0.77 / +0.05 / +0.93 then -0.08 / -0.43 / -0.37.
Not monotonic on any market in either period; gold's middle band is under the base in both but still +24.7R in sample
(a half stake there: -12.4R IS for +26.9R OOS, no mechanism). Negative result. "A week that has spent its range" does
not hurt the zones: gold's > 1.0 band is under the base in sample (+0.29 against +0.50) and above it out of sample
(-0.04 against -0.17).

### 3.5 The weekday of the move's origin (the zone's formation), the first touch, the fill

Sum R (n, win %) by the formation weekday, Mon / Tue / Wed / Thu / Fri:

| market | IS | OOS |
|---|---|---|
| BTC | +12.2 (20, 60) / +7.7 (17, 41) / +29.6 (21, 67) / +9.6 (25, 60) / +2.6 (6, 67) | -11.2 (31, 26) / -8.6 (23, 30) / -16.6 (37, 30) / +2.4 (18, 56) / -11.1 (17, 24) |
| EURUSD | +0.2 (10, 30) / +3.1 (6, 50) / +20.9 (14, 50) / +1.6 (4, 50) / +13.8 (13, 54) | -3.2 (15, 27) / -4.6 (26, 19) / +6.5 (25, 28) / -3.1 (19, 26) / +1.5 (11, 27) |
| NAS100 | -4.2 (6, 17) / +8.6 (5, 60) / +15.4 (14, 50) / -1.1 (10, 30) / +14.2 (8, 75) | +16.7 (25, 36) / +2.2 (23, 39) / -0.2 (18, 28) / +21.6 (21, 38) / -11.5 (13, 8) |
| XAUUSD | +14.9 (35, 46) / +20.7 (32, 47) / +19.0 (30, 57) / +8.4 (28, 50) / +8.9 (18, 44) | -12.2 (76, 30) / +3.4 (81, 33) / -21.1 (87, 29) / -29.7 (76, 22) / -6.4 (49, 33) |

No formation weekday is negative in both periods on any market; the only "under the base in both" cells are positive
in sample (gold Thursday +8.4R IS / -29.7R OOS; BTC Monday, Tuesday, Friday +2.6..+12.2R IS). By the touch weekday two
cells are negative in both: BTC Friday touches (10 trades -1.6R, 40 %; 20 trades -11.2R, 25 %; the trades are opened on
the Friday itself, median 2 h after the touch) and EURUSD Monday touches (9 trades -3.1R; 15 trades -3.7R), both thin
and without a mechanism beyond the weekday; NAS100 Friday touches turn (+14.3R IS, -9.7R OOS). The fill weekday is the
table of `ledgers.md` (nothing holds). Negative result; the weekday cuts stay observations.

### 3.6 Interactions

ER20 x ATR percentile: no cell with the same sign in both periods beyond the ER story (gold < 0.25 is negative in all
three ATR bands out of sample: -0.22 / -0.51 / -0.19 a trade on 65 / 71 / 59 trades, and +0.72 / +0.90 / +0.24 in
sample). 4H with/against x ER20 on gold: against x < 0.25 IS +0.07 (12) / OOS -0.54 (45); against x 0.25-0.35 +0.65
(3) / -0.43 (9); against x 0.35-0.5 -0.60 (2) / -0.01 (11). A trend gate limited to the ranging regime (against AND
ER20 < 0.35) costs 2.8R IS for +28.2R OOS; the plain gate costs 0.5R for +30.3R, so the plain rule is the better one.

## 4. The gold stacks (ledger, R after costs; dip = the largest fall of cumulative R from a peak)

| variant | IS R / dip | IS by year 2024 / 25 / 26 | OOS R / dip | OOS by year 2017..2023 |
|---|---|---|---|---|
| base | +71.8 / -9.0 | 13.7 / 21.9 / 36.3 | -62.2 / -83.2 | -3.6 / -15.7 / -16.6 / -12.0 / -17.3 / -11.7 / +14.8 |
| A: trend gate (against 4H x 50 out) | +71.3 / -7.9 | 10.5 / 22.2 / 38.5 | -31.9 / -54.6 | +2.4 / -12.8 / -14.6 / -7.3 / -9.4 / -5.0 / +14.9 |
| A as a half stake | +71.6 / -8.5 | 12.1 / 22.1 / 37.4 | -47.0 / -68.2 | -0.6 / -14.2 / -15.6 / -9.7 / -13.4 / -8.4 / +14.8 |
| B: ER20 < 0.2 at half | +62.0 / -6.6 | 14.0 / 19.1 / 29.0 | -31.5 / -50.9 | +1.7 / -9.4 / -8.3 / -11.3 / -10.4 / -6.7 / +12.7 |
| C: ER20 < 0.25 at half | +56.5 / -6.6 | 12.8 / 17.8 / 26.0 | -31.3 / -46.7 | +1.9 / -9.1 / -8.1 / -10.2 / -8.7 / -5.9 / +8.9 |
| A gate + B half | +61.5 / -6.6 | 12.0 / 19.2 / 30.3 | -12.2 / -37.1 | +6.0 / -6.9 / -9.5 / -7.6 / -5.9 / -1.7 / +13.4 |
| A half + B half | +61.8 / -6.6 | 13.0 / 19.1 / 29.7 | -21.9 / -43.6 | +3.8 / -8.1 / -8.9 / -9.4 / -8.1 / -4.2 / +13.1 |

A and B overlap (41 of A's 67 OOS trades have ER20 < 0.2) and still add up: together they take gold's out-of-sample
ledger from -62R to -12R for 10R of the 72R in sample. The gate form of A is what carries the OOS gain; as a half stake
it keeps half the loss.

## 5. The challenge replay (`regime_sim.py`; FTMO 2-Step 10 % then 5 %, 4 trading days, the live stakes: 1.5 % with
the -3 % / -6 % ladder, 4H zones x2, EURUSD 1D+1H x0.5, month 50/50 x0.5, BTC x0.5, two slots, guard 4 % / 9.5 %)

In sample, 651 starts every weekday 2024-01-02..2026-06-30, funded months at 1 %:

| set | trades (a month), avg R | phase 1 median | both phases, median | funded %/month (worst, losing months) | 2026 starts within 6 weeks / 2 months |
|---|---|---|---|---|---|
| base (live set) | 322 (9.8), +0.64 | 100 %, 40 d | 100 %, 84 d | +5.73 (-4.2, 9/33) | 71 % / 98 % |
| G1 gold trend gate | 304 (9.2), +0.68 | 100 %, 47 d | 100 %, 97 d | +5.57 (-4.2, 9/33) | 67 % / 99 % |
| G1 as a half stake | 322 (9.8), +0.64 | 100 %, 43 d | 100 %, 90 d | +5.65 (-4.2, 8/33) | 71 % / 98 % |
| G2 gold ER20 < 0.2 half | 322 (9.8), +0.64 | 100 %, 47 d | 100 %, 82 d | +5.30 (-3.8, 9/33) | 57 % / 98 % |
| G3 NAS100 ER20 >= 0.5 gate | 315 (9.5), +0.66 | 100 %, 38 d | 100 %, 83 d | +5.78 (-4.2, 8/33) | 74 % / 99 % |
| G1 + G3 | 297 (9.0), +0.70 | 100 %, 47 d | 100 %, 91 d | +5.62 (-4.2, 9/33) | 57 % / 99 % |
| G1 + G2 + G3 | 297 (9.0), +0.70 | 99 %, 47 d | 99 %, 75 d | +5.24 (-3.2, 10/33) | 47 % / 97 % |

Out of sample, 1,694 starts 2017-01-03..2023-06-30 (replayed to the end of 2023), funded months 2017-2023:

| set | trades (a month), avg R | phase 1 | both phases, median | funded %/month (worst, losing months) | both phases by start year 2017 / 19 / 22 / 23 |
|---|---|---|---|---|---|
| base | 698 (8.3), -0.11 | 25 %, 63 d | 11 %, 136 d | -0.57 (-7.7, 55/84) | 0 / 0 / 22 / 100 % |
| G1 | 631 (7.5), -0.07 | 40 %, 81 d | 20 %, 145 d | +0.01 (-7.7, 47/84) | 30 / 26 / 23 / 100 % |
| G1 half | 698 (8.3), -0.11 | 30 %, 70 d | 11 %, 136 d | -0.39 (-7.7, 53/84) | 0 / 0 / 22 / 100 % |
| G2 | 698 (8.3), -0.11 | 35 %, 71 d | 13 %, 136 d | -0.03 (-6.6, 50/84) | 9 / 2 / 25 / 100 % |
| G3 | 688 (8.2), -0.10 | 26 %, 63 d | 11 %, 136 d | -0.42 (-7.7, 53/84) | 0 / 1 / 22 / 100 % |
| G1 + G3 | 621 (7.4), -0.06 | 37 %, 78 d | 23 %, 158 d | +0.12 (-7.7, 47/84) | 33 / 43 / 23 / 100 % |
| G1 + G2 + G3 | 621 (7.4), -0.06 | 44 %, 91 d | 25 %, 150 d | +0.39 (-6.6, 44/84) | 49 / 36 / 25 / 100 % |

(2018, 2020 and 2021 starts pass in no variant.) The gold trend gate is the only single rule that moves the
out-of-sample account (both phases 11 -> 20 %, the funded month from -0.57 to +0.01 %); its price in sample is about
two weeks on the median challenge (84 -> 97 days) and 4 points on the 6-week pass rate of 2026 starts, from the two
4H-zone winners it removes. G3 is free in sample (+0.05 %/month, 74 % within 6 weeks) and worth nothing in the replay
out of sample. G2 costs the most in-sample speed (71 -> 57 % within 6 weeks) for a smaller OOS gain than G1.

## 6. Proposals (exact rules, both periods, the knob or the smallest code change)

1. **Gold: no trade against the 4H 50-candle mean.** A long only when the last closed 4H close is above the simple mean
   of the last 50 closed 4H closes, a short only when below; the plateau is 50-80 candles (40 and 100-120 cost 6-8R in
   sample). Ledger: IS 143 -> 125 trades, +71.8 -> +71.3R, dip -9.0 -> -7.9R; OOS 371 -> 304 trades, -62.2 -> -31.9R, dip
   -83 -> -55R, better in 7 of 7 OOS years and 2 of 3 IS years. Knob: none; code: `bias.trend_filter_4h_candles: 50`
   (an int in `BiasParams`, 0 = off) implemented in `kronos_trader/strategy/engine.py` in the block of
   `trend_filter_days` (lines 468-477): `closes = views[Timeframe.H_4].close; mean = closes[-n:].mean(); if
   (closes[-1] - mean) * direction.sign < 0: reject "against the 4H 50-candle mean"`, about ten lines plus a test; the
   4H view must hold closed candles only (the live loop fetches 400 4H bars, `LiveParams.broker_bar_counts`, enough).
   Engine rerun to confirm in both periods (`q4_r26_XAUUSD_visit1h_full.yaml` with the knob; the ledger removal is exact
   for market-order gold, so the rerun should match within the usual noise). Replay: OOS both phases 11 -> 20 %, IS
   median 84 -> 97 days. FOR MAX: adopt now (fewer gold trades: 1 in 8, and a slower in-sample challenge) or after the
   challenge; it is the one regime rule with an out-of-sample story and no in-sample cost in R.
2. **Gold at half stake when ER20 < 0.2** (candidate D of `market_XAUUSD.md`, confirmed here on closed bars; the 0.25
   edge is the worse line). Knob: none; code: `risk.regime_risk_multiplier: {er20_below: 0.2, multiplier: 0.5}` with
   the ER20 of the last 21 closed daily closes computed in the engine and handed to `setup_risk` like `aligned_count`
   (a `TradeSetup` field and a multiplier line in `strategy/risk.py`, about a dozen lines). Ledger IS +71.8 -> +62.0R
   (dip -9.0 -> -6.6), OOS -62.2 -> -31.5R (dip -83 -> -51); replay IS 6-week passes 71 -> 57 %, OOS 11 -> 13 %, funded
   month -0.57 -> -0.03 %. Together with rule 1: OOS -12.2R, replay 25 % / +0.39 %/month, IS 6-week passes 47 %.
3. **NAS100: no trade when ER20 >= 0.5** (candidate 5 of `market_NAS100.md`; here 7 trades -1.6R IS, 10 trades -6.7R
   OOS, all longs, negative in 2019, 2020, 2021, 2025, 2026, positive only in 2017 +1.0R). Knob: none; code:
   `bias.max_er20: 0.5` (0 = off) in the same engine block, the same ER20 computation as rule 2. Free in sample
   (replay 74 % within 6 weeks, +5.78 %/month), nothing out of sample in the replay (11 -> 11 %). Cheap, thin, last.

Not proposed, recorded: (a) NAS100 counter-trend trades at a double stake (against the daily 5-candle mean: IS 10
trades +8.0R, OOS 22 trades +34.1R; against the 4H x 50: 3 trades +6.8R, 15 trades +13.3R): positive in both periods
but 3-10 in-sample trades; an observation that the index's edge is the pullback long, to be re-read when the sample
grows. (b) EURUSD against a 4H x 20-40 mean (OOS 12-16 trades, 0-7 % won, -12 to -14R; IS +2.5 to +8.8R): a narrow
window that flips at 50, no rule. (c) BTC Friday touches and EURUSD Monday touches (both negative in both periods,
24-30 trades, no mechanism): observations.

## 7. Negative results (measured, not to be rerun)

- The daily ATR14 percentile against the trailing year (< 30 / 30-70 / > 70): the best in-sample band is the worst
  out-of-sample band on BTC, EURUSD and NAS100; gold's > 70 band is under the base in sample and above it out of
  sample. No threshold below or above holds in both periods on any market.
- The week's range so far against the average week, and its pace: not monotonic in either period on any market.
- The weekday of the zone's formation and of the first touch: no cell negative in both periods beyond the two thin
  touch-weekday cells above; the fill weekday as in `ledgers.md`.
- BTC: no regime cut of any kind (ER20, ATR percentile, 4H trend with or against, week range, weekday) on the UTC
  candles or on the New-York-anchored ones: every in-sample bucket is positive and every out-of-sample bucket negative.
- EURUSD and NAS100: no ER20 or ATR cut with the same sign in both periods except NAS100's >= 0.5 band (17 trades).
- The 4H trend as a raw state (above / below) without the direction: turns on every market.
- The ER20 line at 0.25 or 0.3 on gold: 11-17R more in-sample cost than 0.2 for the same out-of-sample gain.
- A gold trend gate limited to the ranging regime (against AND ER20 < 0.35): worse than the plain gate in both periods.

## 8. Today's regime (TradingView OANDA / Bitstamp bars fetched 14 October, closed bars; `now.out`)

| market | 4H close vs its 50-candle mean | daily ER20 | daily ATR14 (% of price; percentile of the file's last year to 24 Sep / 30 Sep / 4 Oct) | the rules this week |
|---|---|---|---|---|
| XAUUSD | 4083.6 vs 4152.2: below (-1.65 %) | 0.17 | 75.7 (1.82 %; 9th percentile) | trend gate: longs refused, shorts allowed; ER half stake active |
| EURUSD | 1.1124 vs 1.1205: below (-0.73 %) | 0.55 | 0.0066 (0.59 %; 73rd) | no rule |
| NAS100 | 30112 vs 30896: below (-2.54 %) | 0.36 | 432 (1.41 %; 33rd) | ER gate off |
| BTCUSD | 81549 vs 83198: below (-1.98 %) | 0.08 | 2139 (2.57 %; 35th) | no rule |

Gold today is the textbook case for both gold rules: a ranging daily (ER20 0.17, the quietest ATR of the year) with
price under its 8-day mean. The ledgers in this state (ER20 < 0.2): a long against the 4H mean won 38 % in sample
(8 trades, +2.3R) and 23 % out of sample (22 trades, -7.8R); a short with the mean 60 % (15 trades, +8.6R) and 21 %
(76 trades, -35.0R). The trend gate stops the longs; the half stake is what covers the shorts.
