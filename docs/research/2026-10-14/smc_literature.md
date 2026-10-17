# The Smart-Money / ICT / supply-demand literature against our ledgers (14 October 2026)

Angle: documented, testable refinements from the public SMC/ICT literature (not the course), set against the four
research ledgers. Every rule below has an exact definition and names the knob or the code change. Where a rule could
be replayed on the ledgers with the 5-minute candles it was, in both periods; where it changes which trades are taken
(zones, triggers) it can only be run through the engine and is listed as a candidate on the literature's evidence.

Scripts (read-only on the repository, run from the scratchpad): `research/smc_analysis.py` (the per-trade measures and the
5m walk), `research/smc_followup.py` (the dealing-range position from closed 1H candles, partials, target buffer),
`research/smc_followup2.py` (the day-open rule, conditional stale exits). Outputs: `smc_analysis_out.md`,
`smc_followup_out.md`, `smc_followup2_out.md`, `smc_analysis_trades3.csv` (one row a trade with every measure).

Ledgers: in sample (IS) 2024-01 to 2026-09 at 1 %, guard off, raw R (no 0.10R cost): EURUSD `eutwo` 47 trades +44.2R,
XAUUSD `base` 143 +86.1R, NAS100 `rr08` 43 +37.2R, BTCUSD `base` 89 +70.6R; out of sample (OOS) 2017-2023 (BTC
2020-06..2023): EURUSD 97 +8.5R, gold 371 -25.1R, NAS100 100 +38.8R, BTC 130 -28.6R. The 5m walk of each trade with its
own entry, stop and target reproduces the ledgers within a few R (the differences are the ledgers' break-even moves,
which the walk leaves out unless named): BTC +72.6 / -16.8, EURUSD +43.2 / +20.4, NAS100 +35.5 / +32.7, gold +84.1 /
-22.4 (IS / OOS). The management variants below are measured against that walk; the filters against the ledger R.

**A warning from this work.** The first pass measured the entry's position in the last 5 days' range from the daily
candles, and the daily candle of the entry day holds the rest of that day. That leak produced a spectacular "premium
entries lose" result (gold OOS -69.9R on 208 trades in the top quarter); recomputed from closed 1H candles only, the
effect is gone (below). Any per-trade measure built from a candle that is still open at the entry has to be rebuilt
from the lower timeframe before it is believed.

## 1. What the literature says, by theme (sources at the end)

**Stops.** The consensus is the stop beyond the extreme of the liquidity sweep that preceded the entry, with 1-3 pips or
ticks of buffer [S5]; a multi-candle sweep uses the extreme of the whole sequence, not the first candle that broke the
level [S5]. The order-block stop is rejected by the same source ("inside the sweep range, where price often retests").
One site adds "1 ATR below structure" [S13]; one gives a per-instrument percentage buffer (gold 0.3 %, BTC 0.1-0.3 %)
[S3]. No source gives an ATR multiple for a minimum stop. Academic: Kaminski & Lo (2014) show stop-loss rules add value
only when returns have momentum and subtract it under a random walk; volatility-scaled stops cut volatility more than
return [S14]. Our engine already does the literature's stop (`stop_basis: confirmation`, the sweep extreme since the
re-entry; `slbuf` "a few pips more" measured worse on all four markets in the README); the 14 October research knob
`confirmation.stop_window_includes_sweep` is exactly the "whole sweep sequence" rule of [S5].

**Liquidity targets.** The draw on liquidity is chosen from a ranked inventory: prior day/week/session highs and lows,
equal highs/lows (ranked above single swing points), old highs/lows beyond the range; "exits planned into the pool
rather than beyond it, because delivery often stalls once the liquidity is taken" [S6, S7]. A PDH/PDL guide gives T1 =
the opposite previous-day level, T2 = the weekly extreme, the day bounded at midnight New York [S8]; its own figure
(NQ, >200 sessions) is that the previous day's high is tested on 73 % of days and the low on 68 % (vendor, method not
shown) [S8]. The 2022-model guides target "opposing liquidity" with a minimum 1:2-1:3 [S2].

**Entry triggers.** The ICT 2022 model: a liquidity sweep, then displacement that shifts the lower-timeframe structure
(MSS/CHoCH), then an entry on the retrace into the FVG that displacement left; stop beyond the sweep swing [S2]. CISD
(change in the state of delivery): a close through the opening price of the candle, or candle series, that started the
opposing delivery, wicks ignored; sold as an earlier signal than the MSS [S9]. The inverse FVG: a gap that a candle
*closes* through flips to the other side; the entry is the retest from the other side, the stop beyond the gap's far
edge, the target the nearest liquidity [S10]; the breaker block is the same idea on an order block [S11]. The documented
ancestor of the sweep entry is Connors & Raschke's Turtle Soup (1995): a new 20-day low whose prior low is at least four
sessions old, a buy stop back above that prior low, the stop under the day's low [S12].

**Session models.** Killzones: London 02:00-05:00, New York AM 07:00-10:00, PM 13:30-16:00 New York; silver bullets
03-04, 10-11 and 14-15 New York [S3, S4]. One vendor's 1,000-setup sample claims +0.64R a trade inside the London
(07-10 GMT) and New York (12-15 GMT) killzones against -0.22R outside [S15] (method undisclosed). The Asia range
(variously 19:00-02:00 or 20:00-00:00 New York) and the London Judas swing: London sweeps one Asian extreme in
"70-75 % of sessions" (unsourced) and the entry is the reversal after the sweep [S16]. The "true day open" at 00:00 New
York: price below it is discount for the day, above it premium; buy below, sell above, given the daily bias [S17].
Academic: Breedon & Ranaldo (SNB 2011 / J. Int. Money & Finance 2013) find a significant tendency for currencies to
depreciate during their own local trading hours, a time-of-day effect in FX returns and order flow that holds across
currencies [S18]: a real, published intraday drift, but a slow one.

**Trade management.** The common ICT retail rule: a partial at TP1 (+1R), the stop to break-even, the rest trailed to
the pool [S3]; trailing to the last confirmed swing low with an ATR buffer [S13]; no ICT source with a formal
break-even timing was found. Time stops: forum anecdotes only [S19]; the formal framework is the triple barrier (profit,
loss, time) of Lopez de Prado (2018) [S20].

**Filters.** Displacement: the candle "significantly larger than surrounding candles" (2x the average of the last five,
often 3-5x), a body-to-range ratio above about 75 % (below 60 % skip), the next candle continuing [S21]. A quant
translation: FVG size > 0.35 x ATR(14), sweep depth > 0.25 x ATR(14), "range > k x ATR" for displacement [S22].
Premium/discount: the dealing range from the last significant displacement leg, equilibrium at 50 %, longs only from
the discount half, the OTE band 62-79 % (0.705) of the retrace [S23, S24].

**How good is the evidence.** The one test with a disclosed method (StatOasis: order blocks, FVGs, liquidity sweeps and
OTE codified on daily bars of SPY/QQQ/DIA/IWM, 648 backtests, 1993-2025) found no statistically significant forward
edge (best t = +1.22, one of 32 t-stats above 2) and nothing that beat buy-and-hold [S1]. The 60-80 % win rates of the
vendor pages are unaudited; independent reports cluster at 50-65 % [S25]. So the literature gives definitions, not
evidence; our ledgers are the evidence.

## 2. What our ledgers say

### 2.1 Hour of entry (killzones)

Amsterdam hour of the fill: trades / won / sum R.

| Market | 09 | 10 | 13 | 14 | 15:00-15:30 | 15:30-16 | 16 |
|---|---|---|---|---|---|---|---|
| BTC IS | 30 / 67 % / +52.3 | 12 / 58 % / +5.3 | 12 / 33 % / +0.9 | 15 / 67 % / +8.9 | 4 / 100 % / +4.3 | 7 / 43 % / -0.3 | 8 / 38 % / -1.4 |
| BTC OOS | 39 / 31 % / -9.5 | 20 / 30 % / -6.3 | 27 / 30 % / -7.6 | 15 / 53 % / +5.7 | 9 / 22 % / -5.8 | 6 / 33 % / -1.9 | 12 / 33 % / -3.9 |
| EURUSD IS | 7 / 14 % / -1.5 | 5 / 60 % / +4.1 | 4 / 0 % / -3.0 | 8 / 38 % / +9.1 | 4 / 50 % / +2.4 | 3 / 33 % / +1.8 | 13 / 69 % / +20.3 |
| EURUSD OOS | 21 / 24 % / -2.1 | 22 / 27 % / +3.4 | 13 / 54 % / +14.1 | 14 / 21 % / +7.7 | 4 / 25 % / -1.0 | 3 / 0 % / -3.0 | 13 / 15 % / -7.3 |
| NAS100 IS | 3 / 33 % / +3.2 | 9 / 44 % / +4.1 | 7 / 71 % / +17.5 | 9 / 33 % / +4.1 | 2 / 0 % / -2.0 | 7 / 43 % / +0.2 | 1 / 0 % / -1.0 |
| NAS100 OOS | 9 / 22 % / -3.3 | 12 / 25 % / -3.1 | 15 / 40 % / +22.8 | 15 / 13 % / -4.3 | 8 / 50 % / +14.3 | 10 / 40 % / +3.0 | 16 / 44 % / +10.3 |
| Gold IS | 35 / 46 % / +18.5 | 17 / 35 % / -1.6 | 27 / 44 % / +16.2 | 23 / 61 % / +28.2 | 9 / 22 % / -3.1 | 12 / 67 % / +11.2 | 16 / 56 % / +9.9 |
| Gold OOS | 96 / 29 % / -1.0 | 56 / 23 % / -14.3 | 57 / 30 % / +5.7 | 49 / 35 % / -2.3 | 25 / 24 % / -6.9 | 25 / 24 % / -8.8 | 57 / 39 % / +5.9 |

(EURUSD and NAS100 limit fills can land in the 11-13 gap: 1-10 trades, left out.) No hour keeps its sign across the two
periods on any market except NAS100's 13:00 (good in both) and 14:00 (weak in both), on 7-15 trades each; the silver
bullet hour (16:00-17:00 Amsterdam = 10-11 New York) is EURUSD's best hour in sample (+20.3R, 69 %) and its worst out of
sample (-7.3R, 15 %). As the README found for 2017-2026, the hour cuts turn. No session candidate.

### 2.2 Time stops and stale exits

Closing every trade still open after T hours (R, against the walk):

| Market | 4 h | 8 h | 12 h | 24 h | 48 h | walk |
|---|---|---|---|---|---|---|
| BTC IS / OOS | +29.2 / -27.8 | +61.8 / -24.6 | +65.4 / -19.3 | +70.4 / -26.5 | +71.7 / -27.0 | +72.6 / -16.8 |
| EURUSD IS / OOS | +33.4 / -21.5 | +29.5 / -10.8 | +34.4 / -9.2 | +34.8 / -10.9 | +41.9 / +1.9 | +43.2 / +20.4 |
| NAS100 IS / OOS | +29.7 / +18.8 | +34.9 / +25.4 | +34.2 / +32.7 | +33.8 / +34.3 | +34.7 / +39.9 | +35.5 / +32.7 |
| Gold IS / OOS | +39.2 / -42.2 | +60.9 / -28.3 | +60.5 / -25.4 | +76.1 / -30.4 | +76.7 / -22.6 | +84.1 / -22.4 |

Only NAS100's 48 h (already live) helps. Winners show themselves fast (median time to +1R: EURUSD 0.2-0.5 h, NAS100
0.6-0.8 h, BTC 1.1-1.5 h, gold 1.2-1.4 h) but the big ones run for days (EURUSD winners open 24-48 h: 100 % won, +10.6R
IS). A conditional stale exit (only trades still under 0R after T hours are closed at that price): at 4 h BTC +70.6 ->
+66.0 / -28.6 -> -28.2, EURUSD +44.2 -> +38.9 / +8.5 -> -4.7, NAS100 +37.2 -> +34.6 / +38.8 -> +40.7, gold +86.1 ->
+81.5 / -25.1 -> -18.6; at 12 h BTC 0 / +4.3, EURUSD -5.2 / -1.8, NAS100 0 / 0, gold -4.0 / +6.1. Gold's OOS gain
comes with an IS loss, EURUSD loses in both. Not a candidate.

### 2.3 Break-even, trailing, partials

R of the 5m walk under each management (BE k = stop to entry once +kR was seen; trail k = from +kR on, the stop
trails the lowest low / highest high of the last 12 five-minute candles, the structure proxy):

| Market | walk | BE 1 | BE 1.5 | BE 2 | trail 1 | trail 1.5 | trail 2 |
|---|---|---|---|---|---|---|---|
| BTC IS / OOS | +72.6 / -16.8 | +62.7 / -17.9 | +67.0 / -17.0 | +69.1 / -15.8 | +38.4 / -18.5 | +36.1 / -15.4 | +40.9 / -16.3 |
| EURUSD IS / OOS | +43.2 / +20.4 | +31.1 / -0.5 | +32.3 / +14.1 | +39.8 / +17.0 | +17.9 / +1.5 | +15.5 / +15.0 | +29.1 / +18.1 |
| NAS100 IS / OOS | +35.5 / +32.7 | +28.5 / +32.5 | +28.1 / +39.0 | **+36.5 / +35.1** | +20.0 / +25.8 | +19.4 / +19.5 | +30.3 / +18.2 |
| Gold IS / OOS | +84.1 / -22.4 | +62.7 / -41.8 | +76.2 / -34.3 | +86.1 / -12.7 (live) | +41.1 / -23.3 | +52.7 / -27.7 | +58.4 / -16.7 |

Trailing to structure costs 20-50 % of the R everywhere (winners' median adverse excursion is 0.35-0.49R and a third of
them go past 0.5R before they run). Break-even at +1R loses in sample on all four. Break-even at +2R: gold (live) and
NAS100 are at or above the walk in both periods; NAS100 by halves IS +12.2 -> +12.2 and +23.3 -> +24.3, OOS +1.7 ->
+1.1 and +31.0 -> +34.0. Partials (half off at +1R, the rest to break-even): BTC +48.4 / -16.8, EURUSD +23.1 / +5.6,
NAS100 +16.8 / +22.3, gold +45.8 / -22.3; half off at +2R with break-even: +52.1 / -13.8, +30.9 / +18.4, +26.3 / +22.5,
+72.7 / -6.2. Partials lose a third of the in-sample R on every market; not a candidate.

### 2.4 ATR-scaled minimum stop

Stops narrower than k x ATR14(1H) widened to it, the target kept, R re-walked:

| Market | walk | 0.5 x ATR | 0.75 x ATR | 1.0 x ATR |
|---|---|---|---|---|
| BTC IS / OOS | +72.6 / -16.8 | +56.9 / -19.7 | +48.6 / -17.6 | +43.1 / -19.9 |
| EURUSD IS / OOS | +43.2 / +20.4 | +42.7 / +18.9 | +34.8 / +18.9 | +25.4 / +25.1 |
| NAS100 IS / OOS | +35.5 / +32.7 | +31.6 / +28.4 | +22.4 / +23.7 | +30.0 / +22.0 |
| Gold IS / OOS | +84.1 / -22.4 | +82.1 / -27.2 | +74.8 / -32.4 | +60.6 / -27.1 |

Worse in 11 of 12 cells. The tight sweep stop *is* the edge: stops under 0.75 x ATR(1H) carry EURUSD IS +36.0R of +43.2
(25 trades), NAS100 IS +29.8R of +35.5 (29), BTC IS (under 1.0) +64.1R of +72.6 (56), gold IS (under 0.75) +40.3R of
+84.1 (49). The fixed pip minimum stays; no ATR minimum.

### 2.5 Previous-day / previous-week extreme as the target

When yesterday's high (long) or low (short) lies between entry and target and at least 0.8R away, the target moves to
it: BTC +75.4 / -18.3 (walk +72.6 / -16.8), EURUSD +38.8 / +22.6 (+43.2 / +20.4), NAS100 +32.2 / +32.9 (+35.5 / +32.7),
gold +82.9 / -28.4 (+84.1 / -22.4). The previous week's extreme: +70.7 / -17.3, +36.0 / +23.1, +34.6 / +26.4, +79.0 /
-18.3. The impulse-origin target beats the literature's first draw on both periods on three markets. The distance to
the previous-day level ahead of the entry sorts nothing consistent either (EURUSD OOS <0.8R ahead: 15 trades 47 % +24.4R;
NAS100 IS <0.8R: 4 trades 0 %). Not a candidate.

### 2.6 Premium / discount, the day open, the week open

Entry position in the range of the last N closed 1H candles (0 = the trade's best price in the range, 1 = its worst;
R a trade, trades):

| Market | window | <0.25 | 0.25-0.5 | 0.5-0.75 | >0.75 |
|---|---|---|---|---|---|
| BTC IS / OOS | 5 d | - / - | -0.19 (4) / 0.00 (10) | +1.18 (28) / -0.43 (29) | +0.67 (57) / -0.18 (91) |
| EURUSD IS / OOS | 5 d | -1.00 (2) / - | +1.13 (11) / -0.44 (14) | +0.74 (13) / +0.36 (24) | +1.15 (21) / +0.10 (59) |
| NAS100 IS / OOS | 5 d | -1.00 (1) / +7.82 (2) | +1.01 (5) / +0.45 (13) | +1.12 (8) / +0.47 (20) | +0.83 (29) / +0.12 (65) |
| Gold IS / OOS | 5 d | -0.50 (2) / +0.07 (13) | +0.66 (16) / -0.27 (37) | +1.35 (25) / -0.06 (69) | +0.43 (100) / -0.05 (252) |

Most of our trades sit in the top quarter of their 5-day range (a demand zone in a rally is near the highs); refusing
them halves the R (BTC +70.6 -> +32.3, gold +86.1 -> +43.2, EURUSD +44.2 -> +20.1, NAS100 +37.2 -> +13.1 in sample; OOS
+16.2 / +11.9 / -6.0 / -8.0 better), and the half stake loses R in every in-sample cell. The 1-day, 3-day, 10-day and
20-day windows show the same non-monotonic picture (the deepest-discount band is the worst in gold OOS at 20 days: 20
trades, 10 % won). The ICT reading "deeper discount, better long" does not hold for zone entries. Not a candidate.

The "true day open" (00:00 New York): a long *below* the open / a short above it (the literature's side) against the
other side:

| Market | literature side (n, won, R, R/trade) | other side |
|---|---|---|
| BTC IS / OOS | 28, 61 %, +38.9, +1.39 / 49, 29 %, -12.6, -0.26 | 61, 57 %, +31.7, +0.52 / 81, 36 %, -16.0, -0.20 |
| EURUSD IS / OOS | 10, 10 %, -5.6, -0.56 / 23, 17 %, -9.1, -0.40 | 37, 57 %, +49.9, +1.35 / 74, 28 %, +17.6, +0.24 |
| NAS100 IS / OOS | 16, 62 %, +24.4, +1.53 / 22, 18 %, -10.3, -0.47 | 27, 37 %, +12.8, +0.47 / 78, 36 %, +49.1, +0.63 |
| Gold IS / OOS | 23, 39 %, +1.5, +0.07 / 53, 28 %, -7.6, -0.14 | 120, 51 %, +84.6, +0.71 / 318, 30 %, -17.5, -0.06 |

For zone entries the rule reads the other way: a long below the day's open is a long into a day that is falling, and on
EURUSD those lose in both periods (33 trades, 15 % won, -14.7R). Gold agrees weakly, BTC and NAS100 in sample do not. The
Amsterdam midnight open and the week's open (Sunday 17:00 New York) sort nothing. Candidate 6, EURUSD only.

### 2.7 Judas / Asia-range sweeps, displacement strength

Yesterday's opposite extreme swept earlier in the day before the entry (a long after a sweep of yesterday's low): BTC
IS 9 trades 33 % -4.1R against 80 at 61 %; OOS 33 % both; EURUSD IS 46 % against 47 %, OOS 26 % both; NAS100 OOS 23 %
against 35 %; gold IS 33 % against 50 %, OOS 32 % against 29 %. The Asia range (00:00-08:00 Amsterdam) swept before the
entry: BTC IS +1.20R a trade (19) against +0.68, OOS 23 % won against 37 %; gold OOS 39 % against 28 %, IS 46 % against
49 %; EURUSD worse in both. As the README's 8 October screen found: nothing stable.

The confirmation candle's body/range (the displacement rule's ratio): >0.75 against 0.6-0.75, R a trade: BTC +0.69 /
+0.35 IS and -0.32 / -0.18 OOS; EURUSD +1.02 / +1.00 and -0.15 / +0.94; NAS100 +1.00 / +1.72 and +0.74 / +0.96; gold
+0.37 / +0.66 and -0.05 / -0.24. Its body or range against the ATR14 of its timeframe sorts nothing either (the only
consistent cell, EURUSD body/range < 0.4, holds 4 and 14 trades). The README's "strong shift candle" (better in 5 of 8,
half the trades) stands; no sharper version found.

### 2.8 The target a little before the pool

The target at 95 % (90 %) of the planned distance, the rest unchanged (R; near-misses = stopped trades that had reached
the shorter target):

| Market | walk | 95 % | 90 % | near-misses rescued at 95 % |
|---|---|---|---|---|
| BTC IS / OOS | +72.6 / -16.8 | +72.0 / -15.2 | +66.4 / -16.9 | 2 / 2 |
| EURUSD IS / OOS | +43.2 / +20.4 | +39.8 / +22.0 | +36.4 / +18.0 | 0 / 2 |
| NAS100 IS / OOS | +35.5 / +32.7 | +35.4 / +35.3 | +32.4 / +32.9 | 1 / 3 |
| Gold IS / OOS | +84.1 / -22.4 | +85.6 / -11.2 | +80.1 / -14.5 | 3 / 8 |

5 % before the pool is better in 5 of 8 cells and costs little where it is not (EURUSD IS -3.4R, the others at most
-0.6R); 10 % costs the in-sample R. Gold's out-of-sample gain is +11.2R from 8 rescued trades. Candidate 1.

## 3. Candidates for the engine (6-8)

1. **Target 5 % short of the liquidity pool.** The target the policy finds (origin, previous extreme, fallback) is
   moved 5 % of its distance back toward the entry; the minimum R:R is then checked on the shorter target. Knob: new
   `risk.tp_buffer_fraction: 0.05` (about five lines in `build_setup` after `find_take_profit`); `risk.tp_buffer_pips`
   exists today in pips and gives a config-only approximation per market (EURUSD 2 pips, gold 70-100 pips = $0.7-1.0,
   NAS100 4 points, BTC $40) but it scales with nothing. Markets: all four, gold and NAS100 first. Expected: table 2.8;
   live it also covers FTMO's gold spread (3.4-3.7 pips against the backtest's 2), which sits exactly on a target at the
   extreme. Evidence: our data (+ [S6]: exits into the pool, not beyond it).
2. **NAS100 break-even at +2R.** Knob: `exits.breakeven_r_intraday: 2.0` in `config/dorus_live_nas100.yaml` (gold runs it).
   Expected: +1.0R IS (+35.5 -> +36.5), +2.4R OOS (+32.7 -> +35.1), 3 of 4 halves at or above; small. The README's
   6 October run on the older NAS100 profile was mixed; this is the limit-entry profile. Evidence: our data.
3. **CISD-style shift threshold: `confirmation.bs_threshold: protector`.** The balance shift counts only when the
   close goes beyond the extreme of the candle that caused the opposing gap (the P), not merely beyond the gap's edge;
   the engine's nearest object to the CISD close through the candle that started the opposing delivery [S9]. Never
   measured (the README has only `gap_edge`, chosen on his words). Expected: later and fewer shifts, a stop window one
   or two candles longer, fewer fake shifts by the literature's claim; sign unknown, a cheap run on four markets and
   both periods. Evidence: literature.
4. **Breaker / inverse-gap zones.** A zone whose P is closed through (`gap.is_violated`) becomes, from the violating
   close, a zone of the opposite direction over the original gap (`gap.low`-`gap.high`), created at the violating candle,
   traded with the normal rules (first visit within 24 h, the table's shift timeframe, the sweep stop, the origin of the
   breaking move as the target). Code: `structure.breaker_zones: true` in `poi.py` `_map_liquidity_to_protection`
   (one more POI per violated gap, `created_index = gap.violated_index`), label BRK for the ledger. Markets: all; expect
   more trades (continuation entries after a failed zone); must pass the challenge replay, where the gap zones (more
   trades at a lower R a trade) failed. Evidence: literature [S10, S11].
5. **Significant liquidity: the age of X.** The swing X that the displacement closed through must be at least N
   candles older than the displacement's P (`structure.min_x_age_candles: 6`, zone-timeframe candles; in
   `_map_liquidity_to_protection` from `brk.broken_swing.index` against `gap.protector_index`). The Turtle Soup rule
   (the prior extreme at least four sessions old) and the draw-on-liquidity ranking (older and higher-timeframe pools
   above fresh swings) [S12, S6]. Expected: zones built on the break of a two-candle-old swing drop out; fewer trades,
   quality unknown. Evidence: literature + reasoning.
6. **EURUSD: no entry on the discount side of the 00:00 New York open.** A long only when the fill lies above the
   day's open at midnight New York, a short only below it (the literature's rule reversed for zone entries). Code:
   `confirmation.require_day_drift: true` (the open from the first 5m candle at or after 00:00 America/New_York, about
   15 lines in `engine.py` before the setup). Expected: EURUSD removes 10 trades (10 % won, -5.6R) IS and 23 (17 %,
   -9.1R) OOS; gold weaker (IS +0.07R a trade removed against +0.71 kept; OOS -0.14 against -0.06); NAS100 and BTC lose
   in-sample winners (+24.4R, +38.9R): EURUSD only, gold second. Caveats: one of three open definitions tried, small
   n, a per-market pick; needs the halves and the challenge replay. Evidence: our data (against [S17]).
7. **The stop beyond the whole sweep sequence.** The 14 October knob `confirmation.stop_window_includes_sweep: true`:
   when price re-entered the zone, the candles wholly outside it right before the re-entry are the sweep of P, and the
   stop window starts at the first of them, so the stop sits beyond that sweep instead of inside it; with
   `risk.short_stop_spread: true` for the ask-side stop of a short. This is the literature's stop rule word for word
   ("the absolute extreme of the full sweep sequence, not the first candle that broke the level" [S5]). Built, off,
   measured by the 14 October knob batch (`oct14b`): wider stops on the re-entry trades, so fewer stop-outs by a wick and
   less R a winner; the batch decides. Evidence: literature.

Not candidates, measured here and not worth a run: killzone or silver-bullet windows (2.1), time stops and stale exits
(2.2), trailing to structure, break-even at +1R, partials (2.3), ATR-scaled minimum stops (2.4), the previous day's or
week's extreme as the target (2.5), premium/discount of the 1-20 day range and the week open (2.6), Judas / Asia-range
sweeps and displacement strength (2.7).

## Sources

- [S1] StatOasis, "I backtested ICT / Smart Money Concepts: what survives" (648 daily-bar backtests, no significant edge): https://statoasis.com/overfit/research/ict-backtest-what-survives
- [S2] ICT 2022 model guides: https://www.algokings.net/learn/ict-2022-model/ ; https://www.quantum-algo.com/blog/guides/ict-2022-model-complete-guide/ ; https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/
- [S3] ChartWhisperer, "ICT Silver Bullet and Killzones" (windows, entry/stop/target rules, partial at +1R): https://chartwhisperer.ca/blog/ict-silver-bullet-killzones-trading-guide
- [S4] Backtrex, "ICT kill zone times": https://backtrex.com/en/blog/ict-kill-zones-trading-hours-strategy ; LuxAlgo, "ICT Silver Bullet setup": https://www.luxalgo.com/blog/ict-silver-bullet-setup-trading-methods/
- [S5] SmartMoneyTrader, "ICT stop loss placement on CISD entries" (beyond the sweep extreme, 1-3 pips, the whole sweep sequence, not the order block): https://www.smartmoneytrader.co/blog/ict-stop-loss-placement
- [S6] LuxAlgo, "Draw on liquidity" (pool inventory, ranking, exits into the pool): https://www.luxalgo.com/library/concept/draw-on-liquidity/
- [S7] LuxAlgo, "Equal highs/lows as liquidity": https://www.luxalgo.com/library/concept/equal-highs-lows-as-liquidity/
- [S8] ICTKillzone, "Previous day high and low" (T1/T2, midnight New York day, 73 %/68 % NQ figure): https://www.ictkillzone.com/ict-previous-day-high-low
- [S9] CISD definitions: https://www.luxalgo.com/library/indicator/BtusXc4G-cisd-with-alerts/ ; https://www.metalsmine.com/thread/1344619-cisd-in-ict-trading-a-comprehensive-guide
- [S10] Inverse fair value gap (close through the gap, retest entry, stop beyond the far edge): https://www.theinnercircletraders.com/ict-ifvg-inversion-fvg/
- [S11] Breaker blocks: https://fxnx.com/en/blog/ict-breaker-blocks-master-art-trading-failed-order-blocks ; https://innercircletrader.net/tutorials/ict-breaker-block-trading/
- [S12] Turtle Soup (Connors & Raschke, Street Smarts, 1995): https://www.luxalgo.com/library/concept/turtle-soup/ ; https://proea.app/en/blog/turtle-soup
- [S13] Trailing to swing lows with an ATR buffer: https://www.tradingwithrayner.com/trailing-stop-loss/ ; https://www.tradingsim.com/blog/swing-high
- [S14] Kaminski & Lo, "When do stop-loss rules stop losses?", Journal of Financial Markets 18 (2014): https://dspace.mit.edu/entities/publication/bb69ca4b-0cdc-487f-831d-63b2e84fafee
- [S15] FXNX, "Do smart money concepts work? Backtest data" (1,000 setups, killzone expectancy): https://fxnx.com/en/blog/smart-money-concepts-work-backtest-evidence
- [S16] Asian range and the London Judas swing: https://www.theinnercircletraders.com/ict-asian-session/ ; https://www.theinnercircletraders.com/ict-power-of-3/
- [S17] The true day open (midnight New York): https://www.luxalgo.com/library/indicator/y5sLA4Ls-ict-ny-midnight-open-and-divider/ ; https://www.luxalgo.com/library/indicator/jn9UMJzf-ict-opening-price-line/
- [S18] Breedon & Ranaldo, "Intraday patterns in FX returns and order flow", SNB Working Paper 2011-04 (J. Int. Money & Finance 2013): https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04 ; https://qmul.ac.uk/sef/research/workingpapers/2012/items/694.html
- [S19] Time stops, intraday (forum anecdotes only): https://www.elitetrader.com/et/threads/time-stops-for-intraday-trades.58721/post-896419
- [S20] Triple-barrier labelling (profit / loss / time exit), Lopez de Prado, Advances in Financial Machine Learning (2018), ch. 3: https://medium.com/@jpolec_72972/stop-loss-take-profit-triple-barrier-time-exit-advanced-strategies-for-backtesting-8b51836ec5a2
- [S21] ICTKillzone, "ICT displacement" (2x the recent range, body/range > 75 %, next-candle continuation): https://www.ictkillzone.com/ict-displacement
- [S22] Build Alpha, "How to backtest ICT and SMC" (FVG > 0.35 ATR, sweep depth > 0.25 ATR, delayed swing confirmation): https://www.buildalpha.com/backtest-ict-and-smc/
- [S23] Premium/discount and the dealing range: https://www.theinnercircletraders.com/ict-premium-and-discount-zones/ ; https://www.theinnercircletraders.com/ict-dealing-range/
- [S24] OTE 62-79 %: https://forexbee.co/ict-optimal-trade-entry-ote-strategy/ ; https://strefatradingu.pl/en/blog/optimal-trade-entry-ote/
- [S25] Independent win-rate ranges (50-65 %) against promotional 70-80 %: https://fundingpips.com/blog/ict-silver-bullet-strategy-explained ; https://howtotrade.com/wp-content/uploads/2024/04/ICT-Silver-Bullet-Trading-Strategy.pdf
