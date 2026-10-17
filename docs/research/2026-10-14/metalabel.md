# Meta-labeling on the eight research ledgers (14 October 2026)

Angle: Lopez de Prado's meta-labeling. The primary model is our own signal (the engine's entries on the four live markets); the secondary model takes the features known at the signal and tries to tell the winners from the losers. The question is whether a filter on its probability raises R after costs in BOTH periods (in sample 2024-01..2026-09, out of sample 2017..2023, BTC 2020-06..2023). Scripts under `research/metalabel/`: `build_features.py` (the feature frame, `features.csv`), `model.py` (purged CV, transfers, permutation tests, importances; one JSON a run), `report.py`, `posthoc.py`, `withinfold.py` (tables from the JSONs), `univariate.py`, `rr_bands.py`, `assemble.py` (this page). Read-only on the repository; everything ran from the scratchpad under nice.

## 1. Verdict

**Negative.** No model, no feature set and no threshold gives a filter that improves R in both periods. Over the 6 runs (models x feature sets) the out-of-fold AUC by purged CV runs from 0.26 to 0.65; 10 of the 120 AUC cells (CV and transfer) have a permutation p <= 0.05, against about 6 expected by chance (gb_all EURUSD/OOS 0.64 (p 0.01); gb_all NAS100/OOS 0.62 (p 0.02); gb_all POOLED/OOS 0.56 (p 0.03); lr_setup EURUSD/OOS 0.65 (p 0.04); lr_all POOLED/OOS->IS 0.56 (p 0.03); gb_all XAUUSD/IS->OOS 0.57 (p 0.03); gb_all POOLED/OOS->IS 0.56 (p 0.02); lr_context XAUUSD/IS->OOS 0.57 (p 0.02); lr_context POOLED/IS->OOS 0.55 (p 0.01); lr_context POOLED/OOS->IS 0.56 (p 0.02)), and not one of them yields a cut that improves R in both periods. In sample the CV AUC is below 0.5 in 25 of 30 cells (fitted noise), out of sample it sits at 0.37-0.65; the training-set fit AUC is 0.52-1.00 against 0.33-0.62 on the other period: the models learn the noise of 43-143 trades. Of 40 candidate cuts a run (five sets x two training periods x four thresholds), **1 of 240 pass** the both-periods test over the 6 runs; random cuts of the same sizes pass 0.8 of 40 (the in-sample side is the hard one: removing trades from a +0.64R-a-trade period rarely removes negative R), so the models do no better than random cuts. The one pass is the gradient boosting trained out of sample on EURUSD vetoing the lowest 30 % of its probabilities: -3.4R removed in its own period's CV, -0.9R removed on the 47 in-sample trades (14 trades), the margin of one trade. 7 of the 10 significant AUC cells score the out-of-sample period (2017-23, where n is 2-3 times larger): if there is a weak second-opinion structure in our signals it lived in those years (gradient boosting 0.62-0.64 on EURUSD and NAS100, p 0.01-0.02) and is absent from 2024-26 (the same sets 0.41-0.48), which is the wrong way round for a live decision.

What the models do learn is the planned R:R: it is the one feature whose univariate AUC against the win label is on the same side of 0.5 in both periods with |z| >= 1.5 (pooled 0.40 / 0.38, z -3.2 / -5.3; EURUSD and BTC on their own too), and the logistic probabilities track it (Spearman -0.4 to -0.5). A lower planned R:R means a nearer target, which is hit more often; it says nothing about R. That is the methodological point of this page: **a win-probability label is the wrong objective for this engine**, because the payoff differs by a factor of ten between trades. The planned R:R bands tell the R story directly (section 4): in both periods the trades with a planned R:R of 3 or more carry the R (+1.81R a trade in sample, +0.37 out of sample) while the rest is +0.40 / -0.21. That is a stake lever, not a filter, and it is the one concrete proposal here (with its caveats).

## 2. Material and method

- Trades: the research ledgers of the live profiles (`aca/eutwo_EURUSD`, `base_XAUUSD`, `rr08_NAS100`, `base_BTCUSD` and the `oos_` twins): 47 / 143 / 43 / 89 trades in sample, 97 / 371 / 100 / 130 out of sample, 1020 in all. R after costs = the ledger's R minus 0.10R; the label is a win (r > 0.05).
- Features at the signal (the close of the confirmation candle; candle features use only candles closed before it): zone timeframe (4H flag); the bias reading of each of the five timeframes relative to the trade (+1 with, 0 at 50/50, -1 against), the count at 50/50 and the count with; bias mode (scalp); direction; planned R:R; time of the signal (Amsterdam, decimal hour) and a morning flag; weekday; visit number; entry depth in the zone (fraction of its height from the near edge) and the same in 1H ATRs; stop / target / zone height in 1H ATR14 units; hours from the touch to the signal and from the zone forming to the touch; the 20-day efficiency ratio of the daily closes; the 14-day range (high-low of 14 daily candles / close) as a percentile of its trailing 252 days, and the same for the daily ATR14; the distance of the entry to the previous day's high and low in 1H ATRs (as "room ahead" and "range behind", direction-aware, and as the position inside that range); the day's drift (entry minus the 00:00 New York open, in 1H ATRs, signed with the trade); the 5-day return signed with the trade. Confirmation type and timeframe are constant (BS; 5m under a 1H zone, 15m under a 4H zone) and carry nothing. The pooled set adds market dummies.
- Models: logistic regression (standardized, L2, C = 0.3); HistGradientBoosting (depth 2, 60 trees, learning rate 0.05, leaf >= n/15, L2 = 1); ridge regression on R after costs (alpha 10; its "probability" is the predicted R, thresholds 0 and +0.25R). Three feature sets: all 31, the 22 setup features (ledger geometry and bias), the 9 context features (candles).
- Purged 5-fold CV inside each period: contiguous time folds; training trades whose [signal, close] overlaps the test block plus a one-day embargo are dropped. Out-of-fold AUC pooled over folds and the mean within-fold AUC (free of the base-rate drift between blocks). Filters: p >= 0.5, p >= 0.6, the top half by p (the OOF median), and a sweep of keep-above-quantile cuts (q = 0.2, 0.3, 0.5, 0.7).
- Transfer: train on one whole period, score the other, both directions; the "top" threshold is the training set's median fitted p (known before scoring).
- Permutation test: 200 shuffles of the outcome pair (win, R) against the features, same folds; p = share of shuffles with an AUC (or a filter gain in R a trade) at or above the observed. gb_context ran 100 shuffles.
- Importances: standardized logistic coefficients of the training fit; permutation importance (AUC drop) of the model on the OTHER period, 10 repeats.

## 3. Results

### 3.1 Out-of-fold AUC by purged CV inside each period (permutation p in brackets; 0.5 = no skill)

| set | period | n | win | R | lr_all | gb_all | ridge_all | lr_setup | lr_context | gb_context |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | 0.36 (0.86) | 0.48 (0.48) | 0.35 (0.93) | 0.41 (0.72) | 0.37 (0.74) | 0.43 (0.56) |
| EURUSD | OOS | 97 | 26 % | -1.2 | 0.58 (0.17) | 0.64 (0.01) | 0.60 (0.10) | 0.65 (0.04) | 0.48 (0.47) | 0.53 (0.30) |
| XAUUSD | IS | 143 | 49 % | +71.8 | 0.46 (0.69) | 0.42 (0.85) | 0.42 (0.89) | 0.44 (0.76) | 0.50 (0.39) | 0.41 (0.80) |
| XAUUSD | OOS | 371 | 30 % | -62.2 | 0.54 (0.15) | 0.56 (0.06) | 0.48 (0.64) | 0.52 (0.28) | 0.48 (0.54) | 0.48 (0.52) |
| NAS100 | IS | 43 | 47 % | +32.9 | 0.47 (0.48) | 0.41 (0.64) | 0.41 (0.72) | 0.45 (0.50) | 0.26 (0.90) | 0.55 (0.22) |
| NAS100 | OOS | 100 | 32 % | +28.8 | 0.55 (0.19) | 0.62 (0.02) | 0.56 (0.16) | 0.55 (0.19) | 0.54 (0.24) | 0.57 (0.16) |
| BTCUSD | IS | 89 | 58 % | +61.7 | 0.47 (0.61) | 0.61 (0.07) | 0.39 (0.95) | 0.51 (0.31) | 0.46 (0.62) | 0.43 (0.73) |
| BTCUSD | OOS | 130 | 33 % | -41.6 | 0.52 (0.39) | 0.54 (0.26) | 0.50 (0.52) | 0.60 (0.05) | 0.37 (0.95) | 0.45 (0.65) |
| POOLED | IS | 322 | 51 % | +206.0 | 0.45 (0.80) | 0.49 (0.48) | 0.37 (1.00) | 0.49 (0.53) | 0.48 (0.58) | 0.50 (0.38) |
| POOLED | OOS | 698 | 30 % | -76.3 | 0.50 (0.48) | 0.56 (0.03) | 0.43 (0.99) | 0.52 (0.24) | 0.47 (0.78) | 0.50 (0.42) |

### 3.2 Transfer AUC, train on one period and score the other (permutation p in brackets)

| set | train -> test | lr_all | gb_all | ridge_all | lr_setup | lr_context | gb_context |
|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 0.50 (0.48) | 0.44 (0.78) | 0.45 (0.77) | 0.59 (0.12) | 0.48 (0.67) | 0.33 (0.99) |
| EURUSD | OOS->IS | 0.62 (0.06) | 0.53 (0.46) | 0.51 (0.42) | 0.61 (0.08) | 0.44 (0.74) | 0.51 (0.42) |
| XAUUSD | IS->OOS | 0.52 (0.36) | 0.57 (0.03) | 0.48 (0.73) | 0.48 (0.66) | 0.57 (0.02) | 0.54 (0.19) |
| XAUUSD | OOS->IS | 0.53 (0.23) | 0.56 (0.10) | 0.46 (0.80) | 0.50 (0.47) | 0.56 (0.13) | 0.57 (0.06) |
| NAS100 | IS->OOS | 0.44 (0.74) | 0.43 (0.82) | 0.45 (0.71) | 0.46 (0.62) | 0.46 (0.71) | 0.46 (0.69) |
| NAS100 | OOS->IS | 0.52 (0.36) | 0.48 (0.60) | 0.48 (0.56) | 0.55 (0.27) | 0.51 (0.43) | 0.43 (0.72) |
| BTCUSD | IS->OOS | 0.51 (0.48) | 0.55 (0.20) | 0.43 (0.87) | 0.51 (0.47) | 0.44 (0.94) | 0.44 (0.84) |
| BTCUSD | OOS->IS | 0.57 (0.17) | 0.58 (0.17) | 0.53 (0.40) | 0.57 (0.18) | 0.42 (0.95) | 0.43 (0.92) |
| POOLED | IS->OOS | 0.53 (0.08) | 0.55 (0.05) | 0.43 (1.00) | 0.52 (0.23) | 0.55 (0.01) | 0.49 (0.54) |
| POOLED | OOS->IS | 0.56 (0.03) | 0.56 (0.02) | 0.45 (0.97) | 0.54 (0.09) | 0.56 (0.02) | 0.52 (0.24) |

### 3.3 Cuts that improve R in both periods

A cut keeps the trades with p above the q-quantile (q = 0.2 vetoes the worst fifth, q = 0.5 keeps the top half); it passes when it removes negative R both in its training period's purged CV and in the other period. Five sets x two training periods x four q = 40 cuts a run.

| run | cuts that improve R in both periods (of 40) |
|---|---|
| lr_all (logistic, all 31 features) | 0 |
| gb_all (gradient boosting (depth 2, 60 trees), all 31 features) | 1 |
| ridge_all (ridge regression on R after costs, all 31 features) | 0 |
| lr_setup (logistic, 22 setup features only) | 0 |
| lr_context (logistic, 9 context features only) | 0 |
| gb_context (gradient boosting, 9 context features only) | 0 |

Gradient boosting (depth 2, 60 trees, leaf >= n/15): out-of-fold AUC in sample EURUSD 0.48, XAUUSD 0.42, NAS100 0.41, BTCUSD 0.61, POOLED 0.49; out of sample EURUSD 0.64, XAUUSD 0.56, NAS100 0.62, BTCUSD 0.54, POOLED 0.56; the smallest permutation p over the 20 AUC cells is 0.01; training-set fit AUC 0.77-1.00 against transfer AUC 0.43-0.58; cuts that improve R in both periods: 1 of 40.

### 3.4 The filters in R (logistic, all features; p >= 0.5 and the top half; CV = out-of-fold inside the period, transfer = the model of the other period)

| set | period | n | base R | CV p>=0.5 kept | R | R removed | CV top half kept | R removed | transfer p>=0.5 kept | R | R removed | transfer top kept | R removed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | +39.5 | 18 | +0.2 | +39.4 | 24 | +29.7 | 8 | +2.9 | +36.7 | 19 | +18.5 |
| EURUSD | OOS | 97 | -1.2 | 16 | +20.2 | -21.5 | 49 | -13.0 | 40 | -4.7 | +3.4 | 48 | +4.2 |
| XAUUSD | IS | 143 | +71.8 | 70 | +17.7 | +54.1 | 72 | +53.8 | 12 | +0.6 | +71.2 | 57 | +45.8 |
| XAUUSD | OOS | 371 | -62.2 | 30 | -6.6 | -55.6 | 186 | -11.8 | 238 | -47.8 | -14.4 | 249 | -16.1 |
| NAS100 | IS | 43 | +32.9 | 22 | +8.4 | +24.5 | 22 | +24.5 | 5 | -2.1 | +35.0 | 19 | +13.6 |
| NAS100 | OOS | 100 | +28.8 | 19 | +10.1 | +18.7 | 50 | +5.8 | 39 | +6.5 | +22.3 | 44 | +27.8 |
| BTCUSD | IS | 89 | +61.7 | 53 | +14.6 | +47.1 | 45 | +50.0 | 13 | -0.8 | +62.5 | 39 | +54.8 |
| BTCUSD | OOS | 130 | -41.6 | 26 | -11.5 | -30.1 | 65 | -18.6 | 90 | -28.5 | -13.1 | 77 | -18.2 |
| POOLED | IS | 322 | +206.0 | 150 | +38.8 | +167.2 | 161 | +170.6 | 7 | +3.7 | +202.3 | 149 | +158.4 |
| POOLED | OOS | 698 | -76.3 | 37 | -9.6 | -66.7 | 349 | +46.1 | 379 | -82.4 | +6.1 | 360 | -2.6 |

Reading: inside the in-sample period every selection removes positive R (the top half removes +24.5 to +170.6R); inside the out-of-sample period the p >= 0.5 selections keep 16-37 trades of 97-698 because the models' prior is the period's 26-33 % win rate; the transfers from one period to the other remove R of the wrong sign on every set at least once. The lowest in-sample OOF quintile of the pooled logistic holds the best trades (+1.90R a trade, +123.6R of +206.0R): the model's confident losers are the high-R:R winners.

### 3.5 Gradient boosting, the same filters

| set | period | n | base R | CV p>=0.5 kept | R | R removed | CV top half kept | R removed | transfer p>=0.5 kept | R | R removed | transfer top kept | R removed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | +39.5 | 26 | +19.1 | +20.5 | 24 | +21.3 | 2 | -2.2 | +41.7 | 25 | +23.7 |
| EURUSD | OOS | 97 | -1.2 | 5 | +8.6 | -9.8 | 49 | -19.0 | 21 | -14.5 | +13.2 | 28 | +14.5 |
| XAUUSD | IS | 143 | +71.8 | 58 | +10.9 | +61.0 | 72 | +55.2 | 1 | +0.7 | +71.1 | 72 | +38.4 |
| XAUUSD | OOS | 371 | -62.2 | 19 | -1.4 | -60.8 | 186 | -19.7 | 213 | -10.4 | -51.8 | 206 | -48.2 |
| NAS100 | IS | 43 | +32.9 | 18 | +14.3 | +18.6 | 22 | +20.5 | 4 | +1.6 | +31.3 | 19 | +20.4 |
| NAS100 | OOS | 100 | +28.8 | 17 | -0.7 | +29.4 | 50 | +4.5 | 39 | -6.6 | +35.4 | 61 | +16.6 |
| BTCUSD | IS | 89 | +61.7 | 56 | +38.4 | +23.3 | 45 | +47.9 | 12 | +2.7 | +59.0 | 45 | +22.2 |
| BTCUSD | OOS | 130 | -41.6 | 11 | -0.5 | -41.1 | 65 | -13.9 | 102 | -31.0 | -10.6 | 80 | -18.1 |
| POOLED | IS | 322 | +206.0 | 171 | +43.8 | +162.1 | 161 | +165.5 | 8 | +6.1 | +199.8 | 128 | +184.2 |
| POOLED | OOS | 698 | -76.3 | 26 | -3.1 | -73.2 | 349 | -25.1 | 377 | -80.4 | +4.1 | 363 | +1.1 |

### 3.6 Ridge on R instead of the win label

The ridge model trained out of sample and scored in sample ranks by planned R:R (Spearman of its prediction with planned R:R +0.37); its top half keeps 160 of 322 in-sample trades with +154.3R of +206.0R (+0.96R a trade against +0.64), gain p 0.01, but the same model's purged CV inside the out-of-sample period removes -42.1R with its top half, and in sample the CV top half removes +146.6R: no cut passes both periods (0 of 40).

### 3.7 Power: what AUC the samples could have shown

From the permutation null of the OOF AUC (logistic, all features): the null sd is 0.11 on EURUSD and NAS100 in sample (n 43-47), 0.07-0.09 on gold, BTC and EURUSD out of sample, 0.03-0.05 pooled. A real AUC of 0.60 would not be detectable on any single market in sample at the 95 % level (the bar is 0.61-0.70); pooled the bar is 0.57 in sample and 0.55 out of sample, and the observed pooled AUCs are 0.45 and 0.50. So the sample cannot see a weak secondary edge, and shows no strong one. The power table is in the appendix.

### 3.8 Feature importances

Nothing stable. The permutation importances on the other period are 0.00-0.08 AUC and change feature from set to set and direction to direction (planned R:R, stop / ATR, zone height, touch-to-signal, the 20-day efficiency ratio, the previous-day room each top one list). The standardized logistic coefficients of the in-sample fits carry the known anatomy (touch-to-signal, depth, planned R:R, stop / ATR) and flip sign between the periods on most sets. The full lists are in the appendix.

### 3.9 Univariate screen (every feature, every set, both periods)

145 feature x set cells; by chance about 1.3 would pass |z| >= 1.5 in both periods on the same side, and about 7 would pass |z| >= 1.0. Observed: 5 pass at 1.5 (all planned R:R or its sibling target / ATR, on BTC, EURUSD and pooled: lower R:R, more wins) and 7 more at 1.0 (gold's 14-day range percentile and daily ATR percentile at 0.41-0.45, entry depth, time of day; pooled touch-to-signal 0.575 / 0.527 and previous-day room 0.456 / 0.469). At chance level apart from the R:R mechanics. The new context features by themselves (logistic, 9 features) give a pooled transfer AUC of 0.548 / 0.556 (p 0.01 / 0.02), the strongest cells of the whole page, but the same features inside each period score 0.477 / 0.471 by purged CV (p 0.58 / 0.78) and their filters fail both periods; the bucket tables of the six context features flag 27 of 152 buckets as worse in both periods, 18 %, the chance rate of that criterion.

One coincidence is worth a line because it is the same bucket on all four markets: signals taken while the 14-day range sits in the top fifth of its trailing year are under the base in both periods everywhere (in sample BTC 17 trades +0.44R a trade against +0.69, EURUSD 13 +0.46 against +0.84, NAS100 7 +0.30 against +0.77, gold 37 +0.01 against +0.50; out of sample 31 -0.47 against -0.32, 24 -0.40 against -0.01, 19 +0.01 against +0.29, 72 -0.26 against -0.17). Pooled: 74 trades +15.8R in sample, 146 trades -42.3R out of sample. It is positive in sample, so a skip costs +15.8R there and the rule fails the both-periods test; a half stake in that regime would cost -7.9R in sample and save +21.2R out of sample. Not proposed; noted as a regime to watch (today's values: EURUSD 0.82, gold 0.02, NAS100 0.47, BTC 0.14 on the last daily candles of the research data).

## 4. The planned R:R bands: where the R comes from



| market | band | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | [0.0, 1.0) | 0 | nan % | +nan | +0.0 | 0 | nan % | +nan | +0.0 |
| EURUSD | [1.0, 1.5) | 12 | 67 % | +0.92 | +11.1 | 34 | 41 % | +0.12 | +4.2 |
| EURUSD | [1.5, 2.0) | 9 | 67 % | +1.30 | +11.7 | 16 | 25 % | -0.23 | -3.7 |
| EURUSD | [2.0, 3.0) | 11 | 36 % | +0.50 | +5.5 | 20 | 15 % | -0.44 | -8.8 |
| EURUSD | [3.0, 4.0) | 9 | 33 % | +0.84 | +7.6 | 13 | 23 % | +0.42 | +5.4 |
| EURUSD | [4.0, 6.0) | 3 | 0 % | -1.10 | -3.3 | 11 | 0 % | -0.92 | -10.1 |
| EURUSD | [6.0, 100.0) | 3 | 33 % | +2.32 | +7.0 | 3 | 33 % | +3.92 | +11.8 |
| XAUUSD | [0.0, 1.0) | 7 | 57 % | -0.06 | -0.4 | 16 | 31 % | -0.49 | -7.9 |
| XAUUSD | [1.0, 1.5) | 20 | 50 % | -0.01 | -0.2 | 51 | 49 % | -0.04 | -1.8 |
| XAUUSD | [1.5, 2.0) | 11 | 36 % | -0.11 | -1.2 | 23 | 39 % | -0.05 | -1.1 |
| XAUUSD | [2.0, 3.0) | 81 | 51 % | +0.44 | +35.7 | 224 | 27 % | -0.29 | -64.5 |
| XAUUSD | [3.0, 4.0) | 7 | 43 % | +0.79 | +5.6 | 21 | 19 % | +0.03 | +0.6 |
| XAUUSD | [4.0, 6.0) | 9 | 78 % | +3.41 | +30.7 | 19 | 26 % | +0.63 | +12.1 |
| XAUUSD | [6.0, 100.0) | 8 | 12 % | +0.21 | +1.7 | 17 | 12 % | +0.02 | +0.4 |
| NAS100 | [0.0, 1.0) | 5 | 40 % | -0.10 | -0.5 | 9 | 44 % | +0.05 | +0.5 |
| NAS100 | [1.0, 1.5) | 12 | 42 % | +0.03 | +0.4 | 28 | 36 % | -0.14 | -3.8 |
| NAS100 | [1.5, 2.0) | 8 | 62 % | +1.11 | +8.8 | 19 | 26 % | -0.18 | -3.4 |
| NAS100 | [2.0, 3.0) | 8 | 50 % | +1.14 | +9.1 | 15 | 33 % | +0.15 | +2.2 |
| NAS100 | [3.0, 4.0) | 4 | 75 % | +3.22 | +12.9 | 10 | 20 % | -0.24 | -2.4 |
| NAS100 | [4.0, 6.0) | 3 | 33 % | +1.81 | +5.4 | 10 | 50 % | +2.86 | +28.6 |
| NAS100 | [6.0, 100.0) | 3 | 0 % | -1.10 | -3.3 | 9 | 11 % | +0.80 | +7.2 |
| BTCUSD | [0.0, 1.0) | 20 | 90 % | +0.43 | +8.7 | 36 | 44 % | -0.34 | -12.1 |
| BTCUSD | [1.0, 1.5) | 24 | 62 % | +0.26 | +6.3 | 32 | 38 % | -0.29 | -9.3 |
| BTCUSD | [1.5, 2.0) | 11 | 18 % | -0.58 | -6.4 | 21 | 38 % | -0.06 | -1.4 |
| BTCUSD | [2.0, 3.0) | 28 | 50 % | +0.63 | +17.6 | 32 | 22 % | -0.31 | -9.9 |
| BTCUSD | [3.0, 4.0) | 3 | 33 % | +0.41 | +1.2 | 1 | 0 % | -1.10 | -1.1 |
| BTCUSD | [4.0, 6.0) | 0 | nan % | +nan | +0.0 | 4 | 0 % | -1.10 | -4.4 |
| BTCUSD | [6.0, 100.0) | 3 | 67 % | +11.45 | +34.4 | 4 | 0 % | -0.85 | -3.4 |
| POOLED | [0.0, 1.0) | 32 | 75 % | +0.24 | +7.8 | 61 | 41 % | -0.32 | -19.5 |
| POOLED | [1.0, 1.5) | 68 | 56 % | +0.26 | +17.6 | 145 | 42 % | -0.07 | -10.9 |
| POOLED | [1.5, 2.0) | 39 | 44 % | +0.33 | +12.9 | 79 | 33 % | -0.12 | -9.6 |
| POOLED | [2.0, 3.0) | 128 | 49 % | +0.53 | +67.9 | 291 | 26 % | -0.28 | -80.9 |
| POOLED | [3.0, 4.0) | 23 | 43 % | +1.18 | +27.2 | 45 | 20 % | +0.05 | +2.5 |
| POOLED | [4.0, 6.0) | 15 | 53 % | +2.19 | +32.8 | 44 | 23 % | +0.59 | +26.1 |
| POOLED | [6.0, 100.0) | 17 | 24 % | +2.34 | +39.7 | 33 | 12 % | +0.48 | +15.9 |

### Three bands

| market | band | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | <1.5 | 12 | 67 % | +0.92 | +11.1 | 34 | 41 % | +0.12 | +4.2 |
| EURUSD | 1.5-3 | 20 | 50 % | +0.86 | +17.2 | 36 | 19 % | -0.35 | -12.5 |
| EURUSD | >=3 | 15 | 27 % | +0.75 | +11.2 | 27 | 15 % | +0.26 | +7.1 |
| XAUUSD | <1.5 | 27 | 52 % | -0.02 | -0.6 | 67 | 45 % | -0.14 | -9.7 |
| XAUUSD | 1.5-3 | 92 | 49 % | +0.37 | +34.5 | 247 | 28 % | -0.27 | -65.6 |
| XAUUSD | >=3 | 24 | 46 % | +1.58 | +37.9 | 57 | 19 % | +0.23 | +13.0 |
| NAS100 | <1.5 | 17 | 41 % | -0.01 | -0.1 | 37 | 38 % | -0.09 | -3.4 |
| NAS100 | 1.5-3 | 16 | 56 % | +1.12 | +18.0 | 34 | 29 % | -0.03 | -1.2 |
| NAS100 | >=3 | 10 | 40 % | +1.50 | +15.0 | 29 | 28 % | +1.15 | +33.3 |
| BTCUSD | <1.5 | 44 | 75 % | +0.34 | +15.0 | 68 | 41 % | -0.32 | -21.5 |
| BTCUSD | 1.5-3 | 39 | 41 % | +0.29 | +11.1 | 53 | 28 % | -0.21 | -11.3 |
| BTCUSD | >=3 | 6 | 50 % | +5.93 | +35.6 | 9 | 0 % | -0.99 | -8.9 |
| POOLED | <1.5 | 100 | 62 % | +0.25 | +25.4 | 206 | 42 % | -0.15 | -30.4 |
| POOLED | 1.5-3 | 167 | 48 % | +0.48 | +80.8 | 370 | 27 % | -0.24 | -90.5 |
| POOLED | >=3 | 55 | 40 % | +1.81 | +99.7 | 122 | 19 % | +0.37 | +44.5 |



The band >= 3 is above the base in both periods on EURUSD, gold, NAS100 and pooled; on BTC it holds 6 in-sample trades (+35.6R, of which +34.4R in three trades at R:R >= 6) and 9 out-of-sample losers. A minimum R:R of 3 (`risk.min_rr: 3.0`, the config's own default) would keep 55 of 322 in-sample trades and 122 of 698 out of sample: +99.7R / +44.5R, a third of the in-sample R on a sixth of the trades, so not a filter for a challenge that needs trades. The README's min R:R runs of 5-6 October (2.0, 1.5, then the recent-years choice of 1.0 / 0.8 / 0.8 / 0.5) cover that ground.

### Stake by planned R:R, ledger level (a stake multiplier changes no trade list, so the ledger sum is exact; the drawdown ladder's interplay is not simulated)



| market | rule | IS trades touched | IS R | IS dip | OOS trades touched | OOS R | OOS dip |
|---|---|---|---|---|---|---|---|
| EURUSD | base | 0 | +39.5 | -5.5 | 0 | -1.2 | -24.6 |
| EURUSD | x2 at R:R >= 3 | 15 | +50.8 | -8.8 | 27 | +5.8 | -34.0 |
| EURUSD | x1.5 at R:R >= 3 | 15 | +45.2 | -7.1 | 27 | +2.3 | -29.3 |
| EURUSD | x2 at R:R >= 4 | 6 | +43.2 | -5.5 | 14 | +0.4 | -34.8 |
| EURUSD | x0.5 under R:R 1.5 | 12 | +34.0 | -4.4 | 34 | -3.3 | -21.4 |
| EURUSD | x2 at >= 3 and x0.5 under 1.5 | 27 | +45.2 | -7.7 | 61 | +3.7 | -32.8 |
| EURUSD | skip under R:R 3 (min_rr 3) | 32 | +11.2 | -3.4 | 70 | +7.1 | -12.7 |
| XAUUSD | base | 0 | +71.8 | -9.0 | 0 | -62.2 | -83.2 |
| XAUUSD | x2 at R:R >= 3 | 24 | +109.7 | -14.5 | 57 | -49.2 | -84.3 |
| XAUUSD | x1.5 at R:R >= 3 | 24 | +90.8 | -11.8 | 57 | -55.7 | -83.6 |
| XAUUSD | x2 at R:R >= 4 | 17 | +104.2 | -11.2 | 36 | -49.7 | -80.1 |
| XAUUSD | x0.5 under R:R 1.5 | 27 | +72.1 | -8.9 | 67 | -57.4 | -76.4 |
| XAUUSD | x2 at >= 3 and x0.5 under 1.5 | 51 | +110.0 | -14.4 | 124 | -44.3 | -79.8 |
| XAUUSD | skip under R:R 3 (min_rr 3) | 119 | +37.9 | -5.5 | 314 | +13.0 | -14.6 |
| NAS100 | base | 0 | +32.9 | -5.8 | 0 | +28.8 | -11.8 |
| NAS100 | x2 at R:R >= 3 | 10 | +47.9 | -6.9 | 29 | +62.1 | -18.6 |
| NAS100 | x1.5 at R:R >= 3 | 10 | +40.4 | -6.4 | 29 | +45.4 | -14.8 |
| NAS100 | x2 at R:R >= 4 | 6 | +35.0 | -6.9 | 19 | +64.5 | -15.3 |
| NAS100 | x0.5 under R:R 1.5 | 17 | +32.9 | -4.0 | 37 | +30.5 | -9.7 |
| NAS100 | x2 at >= 3 and x0.5 under 1.5 | 27 | +48.0 | -5.1 | 66 | +63.8 | -16.6 |
| NAS100 | skip under R:R 3 (min_rr 3) | 33 | +15.0 | -2.2 | 71 | +33.3 | -7.7 |
| BTCUSD | base | 0 | +61.7 | -4.9 | 0 | -41.6 | -48.7 |
| BTCUSD | x2 at R:R >= 3 | 6 | +97.3 | -6.0 | 9 | -50.5 | -55.4 |
| BTCUSD | x1.5 at R:R >= 3 | 6 | +79.5 | -5.4 | 9 | -46.1 | -52.1 |
| BTCUSD | x2 at R:R >= 4 | 3 | +96.1 | -4.9 | 8 | -49.4 | -54.3 |
| BTCUSD | x0.5 under R:R 1.5 | 44 | +54.2 | -6.8 | 68 | -30.9 | -37.9 |
| BTCUSD | x2 at >= 3 and x0.5 under 1.5 | 50 | +89.8 | -8.1 | 77 | -39.8 | -44.6 |
| BTCUSD | skip under R:R 3 (min_rr 3) | 83 | +35.6 | -3.3 | 121 | -8.9 | -8.9 |
| POOLED | base | 0 | +206.0 | -9.1 | 0 | -76.3 | -132.9 |
| POOLED | x2 at R:R >= 3 | 55 | +305.7 | -14.6 | 122 | -31.8 | -121.3 |
| POOLED | x1.5 at R:R >= 3 | 55 | +255.8 | -11.8 | 122 | -54.0 | -126.2 |
| POOLED | x2 at R:R >= 4 | 32 | +278.5 | -11.5 | 77 | -34.2 | -117.6 |
| POOLED | x0.5 under R:R 1.5 | 100 | +193.3 | -8.0 | 206 | -61.1 | -110.4 |
| POOLED | x2 at >= 3 and x0.5 under 1.5 | 155 | +293.0 | -13.5 | 328 | -16.6 | -102.2 |
| POOLED | skip under R:R 3 (min_rr 3) | 267 | +99.7 | -6.7 | 576 | +44.5 | -18.2 |



Per year, the doubled trades' R (= the extra R of "x2 at R:R >= 3"):



extra R:
market  BTCUSD  EURUSD  NAS100  XAUUSD
year                                  
2017       NaN    11.9    -2.6    -4.2
2018       NaN    -3.3     NaN    -6.6
2019       NaN    -2.2    11.4     8.4
2020       NaN     5.1    -6.6    -3.4
2021      -3.3    -5.6    14.0    -1.1
2022      -3.4    -5.6     2.9     8.2
2023      -2.2     6.8    14.2    11.8
2024      -2.2     2.3    -3.3    15.0
2025       2.3     3.7     9.6     1.5
2026      35.5     5.2     8.7    21.5

trades doubled:
market  BTCUSD  EURUSD  NAS100  XAUUSD
year                                  
2017       NaN     2.0     2.0     9.0
2018       NaN     3.0     NaN     6.0
2019       NaN     2.0     5.0    10.0
2020       NaN     3.0     6.0     4.0
2021       3.0     6.0    10.0     8.0
2022       4.0     6.0     4.0    10.0
2023       2.0     5.0     2.0    10.0
2024       2.0     8.0     3.0    11.0
2025       2.0     6.0     4.0     8.0
2026       2.0     1.0     3.0     5.0

years helped / hurt per market: {'EURUSD': (6, 4), 'XAUUSD': (6, 4), 'NAS100': (6, 3), 'BTCUSD': (2, 4)}



Reading: "x2 at R:R >= 3" adds R in both periods on EURUSD (+11.3 / +7.1), gold (+37.9 / +13.0), NAS100 (+15.0 / +33.3) and pooled (+99.7 / +44.5), and loses on BTC out of sample (-8.9); the dips grow by 1-10R (EURUSD out of sample -24.6 -> -34.0, NAS100 -11.8 -> -18.6, gold -83.2 -> -84.3). The years helped / hurt are 6 / 4 on EURUSD and gold, 6 / 3 on NAS100, 2 / 4 on BTC: the out-of-sample gain on gold sits in 2019, 2022 and 2023 against four losing years, so the rule is a plateau in the sums, not year by year. Caveats: it was found through the model's one transferring feature, so it has been looked at once; the high-R:R trades win 19-40 %, so a double stake lengthens the losing runs; stacked on the 4H double stake (`zone_risk_multiplier`) a 4H zone with R:R >= 3 would risk 6 % on a 1.5 % profile, above FTMO's 5 % day. 

**Proposal (to re-run in the backtester with the drawdown ladder before any adoption):** a new knob `risk.rr_risk_multiplier: {3.0: 2.0}` (a trade whose planned R:R at the signal is at least the key risks that multiple), applied in `setup_risk()` of `kronos_trader/strategy/risk.py` as one more `mult *=` line (the planned R:R is `TradeSetup.planned_rr`, the caller passes it like `combo` and `aligned`), with a cap of the combined multiplier at 2.0 so it never stacks with the 4H double stake, and BTC left at 1.0. Expected from the ledgers (1 % risk, no other multipliers): EURUSD +39.5 -> +50.8R / -1.2 -> +5.8R, gold +71.8 -> +109.7R / -62.2 -> -49.2R, NAS100 +32.9 -> +47.9R / +28.8 -> +62.1R; dips as in the table. "x1.5" is the gentler version (+45.2 / +2.3, +90.8 / -55.7, +40.4 / +45.4).

## 5. What this means for the live set

1. No meta-label filter goes live: nothing in 31 features x 3 models x 3 feature sets separates our winners from our losers in both periods, and the samples (43-143 trades a market in sample) could not show an AUC under 0.61-0.70 anyway. The engine's edge, where it exists, is in the signal and the R:R, not in a second opinion on the signal.
2. The win rate is not the target. Every filter on win probability prefers the low-R:R trades (the 2R fallback targets on gold, the sub-1.5 targets on BTC), which win 56-75 % in sample and make +0.25R a trade; the R sits in the far targets. Any future "quality score" must be scored on R, not on wins.
3. The one lever that holds in both periods is the stake by planned R:R (section 4), to be re-run in the backtester; the drawdown growth and the stacking cap are the open points.
4. The regime features (efficiency ratio, range percentile, previous-day distances, the day's drift) carry nothing usable; the top-quintile range regime is under the base on all four markets in both periods but positive in sample, so it is a watch item, not a rule.

## Appendix A: full tables a run (report.py)



<details><summary>lr_all: logistic, all 31 features</summary>


## lr_all.json: model=lr features=all (31) shuffles=200

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.358 | 0.86 | 18 | +0.2 | +0.01 | +39.4 | 15 | -0.1 | -0.00 | +39.6 | 24 | +9.8 | +0.41 | +29.7 | 0.96 / 0.84 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.582 | 0.17 | 16 | +20.2 | +1.26 | -21.5 | 7 | +0.9 | +0.13 | -2.1 | 49 | +11.7 | +0.24 | -13.0 | 0.02 / 0.13 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.456 | 0.69 | 70 | +17.7 | +0.25 | +54.1 | 43 | +13.1 | +0.30 | +58.7 | 72 | +18.0 | +0.25 | +53.8 | 0.88 / 0.92 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.542 | 0.15 | 30 | -6.6 | -0.22 | -55.6 | 14 | +2.0 | +0.14 | -64.2 | 186 | -50.4 | -0.27 | -11.8 | 0.50 / 0.85 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.467 | 0.48 | 22 | +8.4 | +0.38 | +24.5 | 19 | +7.5 | +0.39 | +25.4 | 22 | +8.4 | +0.38 | +24.5 | 0.70 / 0.76 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.550 | 0.19 | 19 | +10.1 | +0.53 | +18.7 | 12 | -0.4 | -0.04 | +29.2 | 50 | +23.0 | +0.46 | +5.8 | 0.25 / 0.25 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.468 | 0.61 | 53 | +14.6 | +0.28 | +47.1 | 42 | +10.1 | +0.24 | +51.6 | 45 | +11.7 | +0.26 | +50.0 | 0.90 / 0.86 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.518 | 0.39 | 26 | -11.5 | -0.44 | -30.1 | 14 | -5.4 | -0.38 | -36.3 | 65 | -23.1 | -0.35 | -18.6 | 0.70 / 0.63 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.452 | 0.80 | 150 | +38.8 | +0.26 | +167.2 | 69 | +10.1 | +0.15 | +195.8 | 161 | +35.4 | +0.22 | +170.6 | 1.00 / 1.00 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.499 | 0.48 | 37 | -9.6 | -0.26 | -66.7 | 9 | -3.2 | -0.36 | -73.1 | 349 | -122.4 | -0.35 | +46.1 | 0.59 / 1.00 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.504 | 0.48 | 0.907 | 40 | -4.7 | -0.12 | +3.4 | 27 | +4.0 | +0.15 | -5.2 | 48 | -5.5 | -0.11 | +4.2 | 0.63 / 0.66 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.616 | 0.06 | 0.856 | 8 | +2.9 | +0.36 | +36.7 | 7 | +0.7 | +0.10 | +38.9 | 19 | +21.0 | +1.11 | +18.5 | 0.70 / 0.18 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.519 | 0.36 | 0.733 | 238 | -47.8 | -0.20 | -14.4 | 168 | -54.6 | -0.33 | -7.6 | 249 | -46.1 | -0.19 | -16.1 | 0.68 / 0.65 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.532 | 0.23 | 0.722 | 12 | +0.6 | +0.05 | +71.2 | 5 | -0.6 | -0.13 | +72.5 | 57 | +26.0 | +0.46 | +45.8 | 0.71 / 0.61 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.442 | 0.74 | 0.926 | 39 | +6.5 | +0.17 | +22.3 | 29 | +0.7 | +0.02 | +28.1 | 44 | +1.0 | +0.02 | +27.8 | 0.60 / 0.79 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.522 | 0.36 | 0.800 | 5 | -2.1 | -0.42 | +35.0 | 1 | +2.3 | +2.32 | +30.6 | 19 | +19.3 | +1.01 | +13.6 | 0.89 / 0.20 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.510 | 0.48 | 0.803 | 90 | -28.5 | -0.32 | -13.1 | 81 | -21.7 | -0.27 | -19.9 | 77 | -23.4 | -0.30 | -18.2 | 0.53 / 0.46 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.572 | 0.17 | 0.779 | 13 | -0.8 | -0.06 | +62.5 | 10 | +0.3 | +0.03 | +61.4 | 39 | +6.9 | +0.18 | +54.8 | 0.96 / 0.93 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.533 | 0.08 | 0.662 | 379 | -82.4 | -0.22 | +6.1 | 216 | -51.6 | -0.24 | -24.7 | 360 | -73.7 | -0.20 | -2.6 | 0.96 / 0.90 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.556 | 0.03 | 0.643 | 7 | +3.7 | +0.53 | +202.3 | 4 | +2.0 | +0.50 | +204.0 | 149 | +47.5 | +0.32 | +158.4 | 0.64 / 1.00 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.571 | 110 | -35.3 | -0.32 | -6.3 | 107 | -36.2 | -0.34 | -5.5 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.522 | 36 | -7.0 | -0.20 | +5.8 | 34 | -4.8 | -0.14 | +3.6 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.462 | 33 | -0.2 | -0.01 | +29.0 | 30 | +3.1 | +0.10 | +25.7 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.536 | 200 | -39.8 | -0.20 | -22.4 | 189 | -35.8 | -0.19 | -26.4 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.535 | 4 | +2.1 | +0.53 | +59.6 | 55 | +8.1 | +0.15 | +53.6 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.533 | 3 | +1.5 | +0.52 | +38.0 | 17 | +9.0 | +0.53 | +30.5 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.511 | 0 | +0.0 | nan | +32.9 | 27 | +10.3 | +0.38 | +22.6 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.585 | 0 | +0.0 | nan | +71.8 | 50 | +20.1 | +0.40 | +51.7 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: stop_atr +0.056, planned_rr +0.047, n_neutral +0.040, long +0.020, touch_to_sig_h +0.012, behind_pd_atr +0.009; standardized coefficients (train fit), largest 8: sig_tod +0.55, stop_atr +0.49, planned_rr -0.43, s_1W -0.39, atr14d_pct +0.38, behind_pd_atr +0.35, zone_atr -0.33, dist_atr -0.30
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: zone_atr +0.084, morning +0.081, planned_rr +0.049, n_neutral +0.042, atr14d_pct +0.038, is4h +0.036; standardized coefficients (train fit), largest 8: is4h +0.65, morning -0.56, sig_tod -0.46, planned_rr -0.42, rng14_pct -0.37, n_neutral -0.33, zone_atr -0.28, drift_abs -0.27
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: depth +0.017, room_pd_atr +0.016, rng14_pct +0.015, atr14d_pct +0.014, planned_rr +0.007, morning +0.007; standardized coefficients (train fit), largest 8: touch_to_sig_h -0.47, long -0.44, room_pd_atr -0.40, behind_pd_atr -0.36, depth -0.34, morning -0.28, zone_atr +0.24, drift_abs -0.23
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: rng14_pct +0.030, sig_tod +0.026, depth +0.026, ret5d_dir +0.012, behind_pd_atr +0.009, stop_atr +0.008; standardized coefficients (train fit), largest 8: ret5d_dir +0.48, tp_atr -0.40, stop_atr +0.27, depth -0.25, touch_to_sig_h +0.24, rng14_pct -0.24, s_1D -0.24, long +0.23
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: dist_atr +0.024, zone_age_h +0.022, er20 +0.012, drift_abs +0.009, n_neutral +0.006, pd_pos +0.005; standardized coefficients (train fit), largest 8: behind_pd_atr -0.61, atr14d_pct +0.43, dist_atr +0.39, weekday +0.37, tp_atr -0.34, zone_age_h +0.32, n_neutral -0.29, long -0.28
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: er20 +0.048, planned_rr +0.038, n_neutral +0.018, dist_atr +0.009, zone_atr +0.003, rng14_pct +0.002; standardized coefficients (train fit), largest 8: er20 -0.59, dist_atr +0.43, atr14d_pct -0.37, n_neutral -0.29, depth +0.27, s_1W -0.27, stop_atr +0.24, scalp -0.21
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: zone_age_h +0.032, long +0.026, n_with +0.009, s_1W +0.006, tp_atr +0.005, zone_atr +0.005; standardized coefficients (train fit), largest 8: zone_age_h -0.65, er20 +0.35, s_4H -0.33, long -0.33, stop_atr +0.31, tp_atr -0.30, s_1H -0.28, drift_atr -0.27
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.041, zone_atr +0.037, n_with +0.028, er20 +0.027, tp_atr +0.020, behind_pd_atr +0.019; standardized coefficients (train fit), largest 8: planned_rr -0.70, zone_atr +0.55, touch_to_sig_h -0.44, long -0.32, er20 +0.27, s_1W -0.27, drift_atr +0.24, rng14_pct -0.24
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: stop_atr +0.020, tp_atr +0.016, room_pd_atr +0.013, depth +0.011, s_1W +0.007, sig_tod +0.007; standardized coefficients (train fit), largest 8: stop_atr +0.34, tp_atr -0.31, zone_age_h -0.26, long -0.25, s_1M +0.24, room_pd_atr -0.21, drift_atr -0.18, dist_atr -0.17
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.057, drift_abs +0.018, rng14_pct +0.014, is4h +0.009, zone_age_h +0.009, behind_pd_atr +0.007; standardized coefficients (train fit), largest 8: planned_rr -0.55, depth -0.20, stop_atr -0.19, drift_abs -0.19, is4h +0.16, rng14_pct -0.16, morning -0.14, drift_atr +0.13


</details>


<details><summary>gb_all: gradient boosting (depth 2, 60 trees), all 31 features</summary>


## gb_all.json: model=gb features=all (31) shuffles=200

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.478 | 0.48 | 26 | +19.1 | +0.73 | +20.5 | 15 | +8.6 | +0.57 | +31.0 | 24 | +18.2 | +0.76 | +21.3 | 0.51 / 0.51 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.644 | 0.01 | 5 | +8.6 | +1.71 | -9.8 | 5 | +8.6 | +1.71 | -9.8 | 49 | +17.7 | +0.36 | -19.0 | 0.03 / 0.02 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.418 | 0.85 | 58 | +10.9 | +0.19 | +61.0 | 17 | -0.9 | -0.05 | +72.7 | 72 | +16.6 | +0.23 | +55.2 | 0.93 / 0.91 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.563 | 0.06 | 19 | -1.4 | -0.07 | -60.8 | 1 | -1.1 | -1.10 | -61.1 | 186 | -42.5 | -0.23 | -19.7 | 0.30 / 0.67 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.407 | 0.64 | 18 | +14.3 | +0.80 | +18.6 | 12 | +15.9 | +1.32 | +17.0 | 22 | +12.4 | +0.56 | +20.5 | 0.37 / 0.58 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.621 | 0.02 | 17 | -0.7 | -0.04 | +29.4 | 9 | -2.1 | -0.24 | +30.9 | 50 | +24.3 | +0.49 | +4.5 | 0.55 / 0.18 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.611 | 0.07 | 56 | +38.4 | +0.69 | +23.3 | 48 | +12.8 | +0.27 | +48.9 | 45 | +13.8 | +0.31 | +47.9 | 0.53 / 0.80 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.536 | 0.26 | 11 | -0.5 | -0.05 | -41.1 | 5 | -0.1 | -0.02 | -41.5 | 65 | -27.7 | -0.43 | -13.9 | 0.16 / 0.75 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.485 | 0.48 | 171 | +43.8 | +0.26 | +162.1 | 58 | +2.8 | +0.05 | +203.2 | 161 | +40.5 | +0.25 | +165.5 | 1.00 / 0.99 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.564 | 0.03 | 26 | -3.1 | -0.12 | -73.2 | 1 | +0.7 | +0.68 | -77.0 | 349 | -51.2 | -0.15 | -25.1 | 0.48 / 0.63 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.444 | 0.78 | 1.000 | 21 | -14.5 | -0.69 | +13.2 | 16 | -15.6 | -0.98 | +14.4 | 28 | -15.7 | -0.56 | +14.5 | 1.00 / 1.00 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.531 | 0.46 | 0.989 | 2 | -2.2 | -1.10 | +41.7 | 0 | +0.0 | nan | +39.5 | 25 | +15.8 | +0.63 | +23.7 | 1.00 / 0.81 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.568 | 0.03 | 0.919 | 213 | -10.4 | -0.05 | -51.8 | 102 | -3.9 | -0.04 | -58.3 | 206 | -14.0 | -0.07 | -48.2 | 0.09 / 0.10 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.559 | 0.10 | 0.873 | 1 | +0.7 | +0.72 | +71.1 | 0 | +0.0 | nan | +71.8 | 72 | +33.4 | +0.46 | +38.4 | 0.28 / 0.60 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.428 | 0.82 | 1.000 | 39 | -6.6 | -0.17 | +35.4 | 19 | -9.6 | -0.51 | +38.4 | 61 | +12.1 | +0.20 | +16.6 | 0.91 / 0.62 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.482 | 0.60 | 0.988 | 4 | +1.6 | +0.39 | +31.3 | 1 | +2.3 | +2.32 | +30.6 | 19 | +12.5 | +0.66 | +20.4 | 0.60 / 0.63 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.554 | 0.20 | 0.963 | 102 | -31.0 | -0.30 | -10.6 | 84 | -26.9 | -0.32 | -14.7 | 80 | -23.5 | -0.29 | -18.1 | 0.45 / 0.40 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.578 | 0.17 | 0.956 | 12 | +2.7 | +0.22 | +59.0 | 3 | +0.3 | +0.08 | +61.4 | 45 | +39.5 | +0.88 | +22.2 | 0.67 / 0.40 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.549 | 0.05 | 0.857 | 377 | -80.4 | -0.21 | +4.1 | 83 | -22.1 | -0.27 | -54.2 | 363 | -77.4 | -0.21 | +1.1 | 0.92 / 0.92 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.558 | 0.02 | 0.774 | 8 | +6.1 | +0.77 | +199.8 | 1 | +0.4 | +0.43 | +205.5 | 128 | +21.8 | +0.17 | +184.2 | 0.10 / 1.00 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.546 | 95 | -36.1 | -0.38 | -5.5 | 94 | -37.9 | -0.40 | -3.8 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.601 | 39 | -2.4 | -0.06 | +1.2 | 38 | -1.3 | -0.03 | +0.1 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.554 | 48 | +6.9 | +0.14 | +21.9 | 47 | +5.4 | +0.12 | +23.4 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.531 | 195 | -48.8 | -0.25 | -13.4 | 184 | -43.6 | -0.24 | -18.6 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.561 | 5 | +2.6 | +0.51 | +59.1 | 51 | +2.0 | +0.04 | +59.7 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.582 | 1 | +1.7 | +1.74 | +37.8 | 14 | +2.9 | +0.21 | +36.7 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.413 | 0 | +0.0 | nan | +32.9 | 19 | -0.1 | -0.01 | +33.0 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.584 | 2 | +1.9 | +0.93 | +70.0 | 44 | +16.9 | +0.38 | +54.9 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: stop_atr +0.038, planned_rr +0.038, s_1M +0.031, touch_to_sig_h +0.011, er20 +0.007, drift_atr +0.005
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: room_pd_atr +0.027, planned_rr +0.021, depth +0.020, n_with +0.015, pd_pos +0.007, atr14d_pct +0.005
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: atr14d_pct +0.041, depth +0.030, behind_pd_atr +0.024, sig_tod +0.016, stop_atr +0.011, room_pd_atr +0.005
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: zone_atr +0.027, rng14_pct +0.018, atr14d_pct +0.012, er20 +0.012, zone_age_h +0.004, depth +0.004
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: depth +0.018, zone_age_h +0.016, planned_rr +0.001, n_neutral +0.001, is4h +0.000, s_1M +0.000
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: er20 +0.053, zone_age_h +0.024, zone_atr +0.019, drift_atr +0.011, atr14d_pct +0.007, drift_abs +0.006
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: planned_rr +0.071, zone_age_h +0.020, ret5d_dir +0.006, rng14_pct +0.003, sig_tod +0.002, depth +0.002
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.044, sig_tod +0.016, tp_atr +0.016, depth +0.015, atr14d_pct +0.004, zone_age_h +0.002
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: planned_rr +0.029, tp_atr +0.019, stop_atr +0.013, pd_pos +0.006, room_pd_atr +0.003, touch_to_sig_h +0.003
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.045, tp_atr +0.020, behind_pd_atr +0.012, pd_pos +0.008, rng14_pct +0.007, stop_atr +0.004


</details>


<details><summary>ridge_all: ridge regression on R after costs, all 31 features</summary>


## ridge_all.json: model=ridge features=all (31) shuffles=200

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.345 | 0.93 | 37 | +25.2 | +0.68 | +14.3 | 31 | +19.3 | +0.62 | +20.3 | 24 | +10.6 | +0.44 | +28.9 | 0.71 / 0.76 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.604 | 0.10 | 45 | +17.1 | +0.38 | -18.4 | 36 | +19.6 | +0.55 | -20.9 | 49 | +15.5 | +0.32 | -16.7 | 0.07 / 0.11 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.423 | 0.89 | 98 | +48.8 | +0.50 | +23.1 | 84 | +48.0 | +0.57 | +23.9 | 72 | +39.0 | +0.54 | +32.8 | 0.55 / 0.37 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.480 | 0.64 | 125 | -24.0 | -0.19 | -38.3 | 66 | -12.8 | -0.19 | -49.4 | 186 | -41.0 | -0.22 | -21.2 | 0.55 / 0.69 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.411 | 0.72 | 34 | +26.8 | +0.79 | +6.1 | 28 | +20.5 | +0.73 | +12.4 | 22 | +16.3 | +0.74 | +16.6 | 0.40 / 0.43 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.562 | 0.16 | 59 | +49.5 | +0.84 | -20.7 | 51 | +47.4 | +0.93 | -18.6 | 50 | +45.0 | +0.90 | -16.3 | 0.00 / 0.03 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.386 | 0.95 | 49 | +23.5 | +0.48 | +38.2 | 43 | +13.4 | +0.31 | +48.3 | 45 | +23.9 | +0.53 | +37.8 | 0.75 / 0.50 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.500 | 0.52 | 27 | -10.5 | -0.39 | -31.1 | 18 | -5.8 | -0.32 | -35.8 | 65 | -26.4 | -0.41 | -15.2 | 0.61 / 0.76 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.372 | 1.00 | 253 | +135.6 | +0.54 | +70.3 | 209 | +102.1 | +0.49 | +103.9 | 161 | +59.4 | +0.37 | +146.6 | 0.87 / 0.92 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.427 | 0.99 | 250 | -23.9 | -0.10 | -52.4 | 141 | +7.7 | +0.05 | -84.0 | 349 | -34.2 | -0.10 | -42.1 | 0.45 / 0.41 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.447 | 0.77 | 0.895 | 71 | -4.9 | -0.07 | +3.7 | 64 | +2.8 | +0.04 | -4.0 | 46 | -4.1 | -0.09 | +2.9 | 0.68 / 0.64 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.509 | 0.42 | 0.777 | 23 | +23.6 | +1.03 | +15.9 | 18 | +11.2 | +0.62 | +28.4 | 26 | +28.4 | +1.09 | +11.2 | 0.30 / 0.18 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.478 | 0.73 | 0.668 | 321 | -55.4 | -0.17 | -6.8 | 286 | -41.7 | -0.15 | -20.5 | 248 | -26.9 | -0.11 | -35.3 | 0.55 / 0.22 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.464 | 0.80 | 0.648 | 59 | +38.3 | +0.65 | +33.5 | 28 | +16.5 | +0.59 | +55.3 | 72 | +36.6 | +0.51 | +35.2 | 0.26 / 0.52 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.454 | 0.71 | 0.848 | 69 | +25.6 | +0.37 | +3.2 | 63 | +5.3 | +0.08 | +23.5 | 52 | +8.0 | +0.15 | +20.7 | 0.29 / 0.68 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.485 | 0.56 | 0.700 | 24 | +21.4 | +0.89 | +11.5 | 21 | +21.2 | +1.01 | +11.7 | 21 | +21.2 | +1.01 | +11.7 | 0.32 / 0.18 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.429 | 0.87 | 0.590 | 86 | -26.5 | -0.31 | -15.1 | 78 | -19.2 | -0.25 | -22.4 | 73 | -21.0 | -0.29 | -20.6 | 0.44 / 0.42 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.527 | 0.40 | 0.755 | 18 | +3.2 | +0.18 | +58.5 | 12 | +0.1 | +0.01 | +61.6 | 37 | +11.5 | +0.31 | +50.2 | 0.83 / 0.79 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.434 | 1.00 | 0.533 | 580 | -61.9 | -0.11 | -14.4 | 501 | -72.5 | -0.14 | -3.8 | 380 | -66.8 | -0.18 | -9.5 | 0.43 / 0.78 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.455 | 0.97 | 0.521 | 109 | +122.0 | +1.12 | +84.0 | 60 | +53.6 | +0.89 | +152.4 | 160 | +154.3 | +0.96 | +51.6 | 0.02 / 0.01 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.478 | 104 | -34.8 | -0.34 | -6.8 | 82 | -27.8 | -0.34 | -13.8 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.421 | 89 | -1.0 | -0.01 | -0.2 | 64 | -4.1 | -0.06 | +2.9 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.378 | 84 | +28.4 | +0.34 | +0.4 | 50 | +7.0 | +0.14 | +21.8 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.436 | 303 | -54.4 | -0.18 | -7.8 | 184 | -41.8 | -0.23 | -20.4 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.441 | 21 | +40.3 | +1.92 | +21.4 | 32 | +46.0 | +1.44 | +15.7 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.371 | 23 | +19.3 | +0.84 | +20.2 | 33 | +21.1 | +0.64 | +18.4 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.417 | 37 | +26.7 | +0.72 | +6.2 | 41 | +31.7 | +0.77 | +1.2 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.520 | 28 | +35.7 | +1.28 | +36.1 | 54 | +55.5 | +1.03 | +16.3 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: n_neutral +0.065, stop_atr +0.047, n_with +0.012, touch_to_sig_h +0.012, s_1M +0.007, visit +0.005
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: zone_atr +0.067, morning +0.035, room_pd_atr +0.035, behind_pd_atr +0.034, atr14d_pct +0.028, weekday +0.022
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: depth +0.019, rng14_pct +0.015, atr14d_pct +0.015, n_with +0.008, s_1D +0.006, n_neutral +0.005
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: depth +0.017, rng14_pct +0.016, sig_tod +0.015, behind_pd_atr +0.011, drift_abs +0.011, stop_atr +0.007
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: dist_atr +0.043, zone_age_h +0.025, morning +0.020, er20 +0.016, drift_abs +0.007, long +0.006
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: dist_atr +0.050, er20 +0.049, room_pd_atr +0.032, n_neutral +0.022, s_4H +0.016, drift_atr +0.014
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: long +0.032, zone_age_h +0.014, dist_atr +0.003, sig_tod +0.002, touch_to_sig_h +0.002, zone_atr +0.001
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: n_with +0.030, er20 +0.018, behind_pd_atr +0.017, zone_atr +0.017, s_4H +0.015, s_1W +0.013
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: rng14_pct +0.005, s_1W +0.003, n_neutral +0.002, touch_to_sig_h +0.002, depth +0.001, is4h +0.001
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: atr14d_pct +0.012, drift_abs +0.005, zone_age_h +0.005, touch_to_sig_h +0.004, depth +0.004, mkt_XAUUSD +0.003


</details>


<details><summary>lr_setup: logistic, 22 setup features only</summary>


## lr_setup.json: model=lr features=setup (22) shuffles=200

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.411 | 0.72 | 18 | +2.9 | +0.16 | +36.6 | 12 | -3.0 | -0.25 | +42.5 | 24 | +15.1 | +0.63 | +24.5 | 0.92 / 0.67 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.646 | 0.04 | 10 | +5.2 | +0.52 | -6.4 | 8 | +2.7 | +0.33 | -3.9 | 49 | +15.1 | +0.31 | -16.3 | 0.13 / 0.08 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.440 | 0.76 | 57 | +13.6 | +0.24 | +58.2 | 19 | -3.5 | -0.18 | +75.3 | 72 | +23.8 | +0.33 | +48.0 | 0.88 / 0.78 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.520 | 0.28 | 15 | -0.2 | -0.02 | -62.0 | 4 | +0.5 | +0.12 | -62.7 | 186 | -50.9 | -0.27 | -11.4 | 0.25 / 0.83 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.454 | 0.50 | 23 | +5.7 | +0.25 | +27.2 | 19 | +3.2 | +0.17 | +29.7 | 22 | +1.5 | +0.07 | +31.4 | 0.76 / 0.94 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.549 | 0.19 | 14 | +4.5 | +0.32 | +24.3 | 8 | +1.0 | +0.12 | +27.8 | 50 | +30.6 | +0.61 | -1.8 | 0.38 / 0.12 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.509 | 0.31 | 56 | +17.1 | +0.31 | +44.6 | 39 | +11.0 | +0.28 | +50.7 | 45 | +13.4 | +0.30 | +48.3 | 0.89 / 0.84 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.605 | 0.05 | 21 | -7.1 | -0.34 | -34.5 | 5 | +1.3 | +0.26 | -42.9 | 65 | -13.9 | -0.21 | -27.7 | 0.46 / 0.18 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.489 | 0.53 | 154 | +32.5 | +0.21 | +173.4 | 56 | +16.1 | +0.29 | +189.9 | 161 | +39.4 | +0.24 | +166.6 | 1.00 / 1.00 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.520 | 0.24 | 20 | -6.3 | -0.32 | -70.0 | 3 | -0.5 | -0.17 | -75.8 | 349 | -102.5 | -0.29 | +26.2 | 0.60 / 0.99 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.589 | 0.12 | 0.853 | 40 | +5.1 | +0.13 | -6.4 | 28 | +2.1 | +0.08 | -3.4 | 46 | +1.9 | +0.04 | -3.1 | 0.31 / 0.43 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.607 | 0.08 | 0.846 | 9 | +5.4 | +0.60 | +34.2 | 9 | +5.4 | +0.60 | +34.2 | 20 | +22.9 | +1.14 | +16.7 | 0.55 / 0.15 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.483 | 0.66 | 0.663 | 222 | -49.7 | -0.22 | -12.6 | 134 | -42.5 | -0.32 | -19.8 | 228 | -53.4 | -0.23 | -8.8 | 0.78 / 0.82 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.503 | 0.47 | 0.658 | 2 | -0.0 | -0.01 | +71.8 | 0 | +0.0 | nan | +71.8 | 48 | +9.2 | +0.19 | +62.6 | 0.78 / 1.00 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.460 | 0.62 | 0.800 | 30 | -11.5 | -0.38 | +40.2 | 16 | +3.9 | +0.25 | +24.8 | 30 | -11.5 | -0.38 | +40.2 | 0.97 / 1.00 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.548 | 0.27 | 0.736 | 2 | +1.2 | +0.61 | +31.7 | 1 | +2.3 | +2.32 | +30.6 | 17 | +18.0 | +1.06 | +14.9 | 0.49 / 0.11 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.513 | 0.47 | 0.762 | 93 | -24.8 | -0.27 | -16.8 | 79 | -27.2 | -0.34 | -14.4 | 79 | -27.2 | -0.34 | -14.4 | 0.31 / 0.59 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.567 | 0.18 | 0.758 | 18 | -1.2 | -0.07 | +62.9 | 8 | -1.1 | -0.14 | +62.8 | 39 | +13.1 | +0.34 | +48.6 | 0.93 / 0.75 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.522 | 0.23 | 0.655 | 383 | -86.1 | -0.22 | +9.8 | 199 | -39.6 | -0.20 | -36.7 | 368 | -77.7 | -0.21 | +1.4 | 0.97 / 0.90 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.540 | 0.09 | 0.622 | 9 | +6.8 | +0.76 | +199.2 | 4 | +2.0 | +0.50 | +204.0 | 154 | +43.1 | +0.28 | +162.9 | 0.44 / 1.00 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.565 | 108 | -31.5 | -0.29 | -10.1 | 106 | -29.3 | -0.28 | -12.3 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.503 | 39 | -6.3 | -0.16 | +5.1 | 38 | -5.2 | -0.14 | +4.0 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.462 | 36 | +6.3 | +0.17 | +22.5 | 34 | +5.3 | +0.15 | +23.5 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.520 | 200 | -54.6 | -0.27 | -7.6 | 190 | -48.5 | -0.26 | -13.7 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.542 | 3 | +1.6 | +0.55 | +60.1 | 58 | +12.3 | +0.21 | +49.4 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.565 | 5 | +6.3 | +1.25 | +33.3 | 18 | +11.3 | +0.63 | +28.2 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.441 | 0 | +0.0 | nan | +32.9 | 31 | +14.4 | +0.46 | +18.5 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.554 | 1 | -1.1 | -1.10 | +72.9 | 47 | +5.1 | +0.11 | +66.7 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: n_neutral +0.063, stop_atr +0.054, planned_rr +0.051, n_with +0.012, touch_to_sig_h +0.011, long +0.010; standardized coefficients (train fit), largest 8: planned_rr -0.52, sig_tod +0.47, zone_atr -0.41, stop_atr +0.37, n_neutral -0.29, s_1M +0.27, s_1W -0.25, dist_atr -0.25
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.068, morning +0.067, zone_atr +0.049, dist_atr +0.030, touch_to_sig_h +0.020, visit +0.015; standardized coefficients (train fit), largest 8: is4h +0.75, morning -0.54, planned_rr -0.48, sig_tod -0.45, n_neutral -0.30, touch_to_sig_h +0.20, zone_atr -0.19, dist_atr +0.16
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: depth +0.021, planned_rr +0.018, n_neutral +0.011, morning +0.004, stop_atr +0.002, s_1W +0.002; standardized coefficients (train fit), largest 8: depth -0.35, long -0.33, touch_to_sig_h -0.31, dist_atr -0.26, s_1M +0.25, morning -0.19, zone_age_h +0.16, zone_atr +0.16
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: depth +0.015, sig_tod +0.015, visit +0.009, stop_atr +0.006, s_4H +0.002, weekday +0.000; standardized coefficients (train fit), largest 8: tp_atr -0.44, stop_atr +0.30, touch_to_sig_h +0.29, dist_atr -0.24, n_neutral +0.21, depth -0.21, n_with -0.14, planned_rr -0.13
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: dist_atr +0.029, zone_age_h +0.020, n_neutral +0.010, s_1M +0.009, morning +0.006, touch_to_sig_h +0.006; standardized coefficients (train fit), largest 8: dist_atr +0.41, long -0.33, weekday +0.28, zone_age_h +0.26, tp_atr -0.23, zone_atr -0.23, scalp -0.19, is4h -0.18
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: n_neutral +0.090, planned_rr +0.046, depth +0.024, s_1M +0.023, scalp +0.013, dist_atr +0.011; standardized coefficients (train fit), largest 8: dist_atr +0.40, n_neutral -0.39, s_1M -0.29, touch_to_sig_h +0.29, s_1W -0.25, depth +0.23, tp_atr +0.22, weekday -0.20
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: zone_age_h +0.035, long +0.019, tp_atr +0.008, n_with +0.006, zone_atr +0.006, is4h +0.004; standardized coefficients (train fit), largest 8: zone_age_h -0.60, stop_atr +0.30, s_4H -0.29, tp_atr -0.29, s_1H -0.28, s_1M +0.23, sig_tod -0.22, depth +0.21
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.048, zone_atr +0.033, zone_age_h +0.020, n_with +0.020, s_4H +0.020, tp_atr +0.019; standardized coefficients (train fit), largest 8: planned_rr -0.67, zone_atr +0.53, touch_to_sig_h -0.42, long -0.24, s_1W -0.24, tp_atr -0.21, s_1M -0.19, n_neutral -0.16
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: tp_atr +0.018, stop_atr +0.016, depth +0.009, sig_tod +0.007, s_1W +0.006, planned_rr +0.004; standardized coefficients (train fit), largest 8: tp_atr -0.37, stop_atr +0.35, s_1M +0.27, zone_age_h -0.24, long -0.22, sig_tod +0.18, touch_to_sig_h +0.15, s_1H -0.15
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: planned_rr +0.050, zone_age_h +0.006, is4h +0.005, morning +0.004, depth +0.002, s_1D +0.000; standardized coefficients (train fit), largest 8: planned_rr -0.52, depth -0.19, is4h +0.17, morning -0.16, stop_atr -0.14, dist_atr -0.14, tp_atr +0.12, s_1M -0.12


</details>


<details><summary>lr_context: logistic, 9 context features only</summary>


## lr_context.json: model=lr features=context (9) shuffles=200

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.373 | 0.74 | 24 | +8.2 | +0.34 | +31.3 | 15 | +9.8 | +0.65 | +29.7 | 24 | +8.2 | +0.34 | +31.3 | 0.78 / 0.79 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.477 | 0.47 | 6 | +8.4 | +1.41 | -9.7 | 1 | +1.6 | +1.63 | -2.9 | 49 | +5.4 | +0.11 | -6.6 | 0.06 / 0.26 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.502 | 0.39 | 77 | +26.3 | +0.34 | +45.5 | 29 | +15.8 | +0.55 | +56.0 | 72 | +25.2 | +0.35 | +46.6 | 0.69 / 0.71 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.481 | 0.54 | 2 | -0.0 | -0.02 | -62.2 | 0 | +0.0 | nan | -62.2 | 186 | -50.5 | -0.27 | -11.7 | 0.26 / 0.78 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.263 | 0.90 | 16 | +0.5 | +0.03 | +32.4 | 7 | -7.7 | -1.10 | +40.6 | 22 | -1.0 | -0.05 | +33.9 | 0.86 / 0.93 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.544 | 0.24 | 6 | +1.1 | +0.18 | +27.7 | 3 | -3.3 | -1.10 | +32.1 | 50 | +34.0 | +0.68 | -5.2 | 0.34 / 0.07 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.463 | 0.62 | 69 | +48.6 | +0.70 | +13.1 | 38 | +21.6 | +0.57 | +40.1 | 45 | +24.2 | +0.54 | +37.5 | 0.55 / 0.62 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.366 | 0.95 | 8 | -7.8 | -0.98 | -33.8 | 1 | -1.1 | -1.10 | -40.5 | 65 | -29.7 | -0.46 | -11.9 | 0.93 / 0.83 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.477 | 0.58 | 172 | +73.6 | +0.43 | +132.4 | 48 | +11.7 | +0.24 | +194.3 | 161 | +61.5 | +0.38 | +144.5 | 0.88 / 0.92 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.471 | 0.78 | 4 | +0.3 | +0.07 | -76.6 | 0 | +0.0 | nan | -76.3 | 349 | -83.7 | -0.24 | +7.4 | 0.28 / 0.93 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.478 | 0.67 | 0.684 | 34 | +0.3 | +0.01 | -1.6 | 21 | +4.3 | +0.20 | -5.5 | 42 | -5.2 | -0.12 | +4.0 | 0.41 / 0.64 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.442 | 0.74 | 0.694 | 4 | +10.4 | +2.60 | +29.1 | 0 | +0.0 | nan | +39.5 | 22 | +10.0 | +0.46 | +29.5 | 0.05 / 0.95 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.569 | 0.02 | 0.651 | 216 | -29.5 | -0.14 | -32.7 | 107 | -14.8 | -0.14 | -47.4 | 216 | -29.5 | -0.14 | -32.7 | 0.38 / 0.33 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.559 | 0.13 | 0.612 | 3 | +1.5 | +0.50 | +70.3 | 0 | +0.0 | nan | +71.8 | 65 | +43.0 | +0.66 | +28.9 | 0.68 / 0.13 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.464 | 0.71 | 0.693 | 44 | +15.7 | +0.36 | +13.1 | 16 | -9.0 | -0.56 | +37.7 | 57 | +13.5 | +0.24 | +15.3 | 0.40 / 0.53 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.513 | 0.43 | 0.699 | 2 | -2.2 | -1.10 | +35.1 | 1 | -1.1 | -1.10 | +34.0 | 17 | +11.2 | +0.66 | +21.7 | 1.00 / 0.63 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.436 | 0.94 | 0.667 | 104 | -29.7 | -0.29 | -11.9 | 61 | -24.9 | -0.41 | -16.7 | 63 | -21.2 | -0.34 | -20.4 | 0.21 / 0.60 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.425 | 0.95 | 0.632 | 3 | -1.7 | -0.58 | +63.4 | 0 | +0.0 | nan | +61.7 | 46 | +21.2 | +0.46 | +40.5 | 0.92 / 0.75 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.548 | 0.01 | 0.602 | 365 | -50.1 | -0.14 | -26.2 | 94 | -15.2 | -0.16 | -61.1 | 323 | -51.9 | -0.16 | -24.5 | 0.70 / 0.81 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.556 | 0.02 | 0.578 | 0 | +0.0 | nan | +206.0 | 0 | +0.0 | nan | +206.0 | 154 | +103.6 | +0.67 | +102.3 | nan / 0.45 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.499 | 119 | -39.8 | -0.33 | -1.8 | 117 | -44.4 | -0.38 | +2.7 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.550 | 28 | +11.9 | +0.42 | -13.1 | 24 | +16.3 | +0.68 | -17.5 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.511 | 41 | +2.1 | +0.05 | +26.7 | 32 | +1.7 | +0.05 | +27.0 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.573 | 177 | -24.2 | -0.14 | -38.0 | 150 | -25.5 | -0.17 | -36.7 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.483 | 0 | +0.0 | nan | +61.7 | 56 | +32.5 | +0.58 | +29.2 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.525 | 0 | +0.0 | nan | +39.5 | 11 | +9.4 | +0.85 | +30.2 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.483 | 0 | +0.0 | nan | +32.9 | 26 | +17.7 | +0.68 | +15.2 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.608 | 0 | +0.0 | nan | +71.8 | 61 | +44.0 | +0.72 | +27.8 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: room_pd_atr +0.023, behind_pd_atr +0.017, rng14_pct +0.005, drift_atr +0.003, er20 +0.002, drift_abs -0.000; standardized coefficients (train fit), largest 8: behind_pd_atr +0.31, ret5d_dir +0.23, er20 -0.22, room_pd_atr -0.17, drift_atr +0.16, pd_pos -0.12, atr14d_pct +0.12, rng14_pct -0.02
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: atr14d_pct +0.013, drift_atr +0.009, behind_pd_atr +0.002, room_pd_atr -0.008, er20 -0.019, pd_pos -0.065; standardized coefficients (train fit), largest 8: rng14_pct -0.35, drift_abs -0.33, ret5d_dir -0.28, drift_atr +0.26, pd_pos +0.20, room_pd_atr -0.19, atr14d_pct +0.12, er20 +0.12
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: room_pd_atr +0.047, atr14d_pct +0.023, behind_pd_atr +0.015, rng14_pct +0.013, drift_abs +0.008, drift_atr +0.005; standardized coefficients (train fit), largest 8: room_pd_atr -0.43, behind_pd_atr -0.34, atr14d_pct -0.17, rng14_pct -0.14, drift_abs -0.13, drift_atr +0.13, er20 -0.12, pd_pos -0.05
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: rng14_pct +0.033, behind_pd_atr +0.015, room_pd_atr +0.015, atr14d_pct +0.004, drift_abs +0.001, drift_atr +0.000; standardized coefficients (train fit), largest 8: ret5d_dir +0.29, rng14_pct -0.22, drift_abs -0.17, room_pd_atr -0.16, behind_pd_atr -0.14, er20 +0.12, atr14d_pct -0.07, drift_atr +0.07
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: drift_abs +0.036, er20 +0.021, ret5d_dir +0.002, room_pd_atr -0.000, pd_pos -0.005, rng14_pct -0.014; standardized coefficients (train fit), largest 8: drift_abs +0.35, behind_pd_atr -0.31, atr14d_pct +0.25, drift_atr -0.25, rng14_pct -0.15, er20 -0.08, ret5d_dir +0.04, room_pd_atr -0.02
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: er20 +0.087, pd_pos +0.007, room_pd_atr +0.000, drift_abs -0.002, drift_atr -0.004, ret5d_dir -0.007; standardized coefficients (train fit), largest 8: er20 -0.53, atr14d_pct -0.37, room_pd_atr -0.17, behind_pd_atr +0.14, drift_atr +0.12, rng14_pct +0.08, pd_pos -0.07, ret5d_dir -0.02
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: room_pd_atr +0.003, ret5d_dir +0.001, pd_pos +0.000, behind_pd_atr +0.000, drift_abs -0.002, atr14d_pct -0.006; standardized coefficients (train fit), largest 8: atr14d_pct -0.30, er20 +0.28, drift_atr -0.28, rng14_pct +0.23, drift_abs +0.12, ret5d_dir +0.04, room_pd_atr -0.02, pd_pos +0.00
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: behind_pd_atr +0.018, drift_abs +0.010, room_pd_atr +0.003, ret5d_dir -0.001, pd_pos -0.002, er20 -0.002; standardized coefficients (train fit), largest 8: rng14_pct -0.29, drift_atr +0.25, pd_pos -0.20, atr14d_pct +0.17, drift_abs -0.13, room_pd_atr +0.08, behind_pd_atr -0.06, er20 +0.03
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: room_pd_atr +0.029, behind_pd_atr +0.015, ret5d_dir +0.010, rng14_pct +0.006, mkt_EURUSD +0.004, atr14d_pct +0.004; standardized coefficients (train fit), largest 8: room_pd_atr -0.30, behind_pd_atr -0.19, ret5d_dir +0.11, drift_abs +0.10, drift_atr -0.09, mkt_BTCUSD +0.09, rng14_pct -0.05, atr14d_pct -0.05
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: drift_abs +0.023, rng14_pct +0.021, room_pd_atr +0.018, drift_atr +0.013, behind_pd_atr +0.006, mkt_BTCUSD +0.005; standardized coefficients (train fit), largest 8: drift_abs -0.22, drift_atr +0.19, rng14_pct -0.19, room_pd_atr -0.11, ret5d_dir +0.07, mkt_EURUSD -0.06, er20 +0.04, mkt_BTCUSD +0.04


</details>


<details><summary>gb_context: gradient boosting, 9 context features only</summary>


## gb_context.json: model=gb features=context (9) shuffles=100

### Purged 5-fold CV within each period (out-of-fold probabilities)

| set | period | n | win | R | R/tr | OOF AUC | perm p | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top half by p: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 47 % | +39.5 | +0.84 | 0.431 | 0.56 | 24 | +17.7 | +0.74 | +21.8 | 16 | +13.5 | +0.85 | +26.0 | 24 | +17.7 | +0.74 | +21.8 | 0.50 / 0.48 |
| EURUSD | OOS | 97 | 26 % | -1.2 | -0.01 | 0.527 | 0.30 | 5 | +0.5 | +0.10 | -1.8 | 2 | +0.6 | +0.29 | -1.8 | 49 | +4.5 | +0.09 | -5.8 | 0.29 / 0.29 |
| XAUUSD | IS | 143 | 49 % | +71.8 | +0.50 | 0.407 | 0.80 | 53 | +11.1 | +0.21 | +60.7 | 19 | -4.1 | -0.21 | +75.9 | 72 | +30.8 | +0.43 | +41.0 | 0.88 / 0.51 |
| XAUUSD | OOS | 371 | 30 % | -62.2 | -0.17 | 0.483 | 0.52 | 15 | -5.6 | -0.37 | -56.6 | 2 | +0.8 | +0.41 | -63.0 | 186 | -48.1 | -0.26 | -14.1 | 0.54 / 0.73 |
| NAS100 | IS | 43 | 47 % | +32.9 | +0.77 | 0.549 | 0.22 | 20 | +17.8 | +0.89 | +15.1 | 16 | +12.3 | +0.77 | +20.6 | 22 | +18.7 | +0.85 | +14.2 | 0.27 / 0.32 |
| NAS100 | OOS | 100 | 32 % | +28.8 | +0.29 | 0.566 | 0.16 | 18 | +11.6 | +0.65 | +17.1 | 8 | -5.7 | -0.71 | +34.5 | 50 | +40.6 | +0.81 | -11.8 | 0.21 / 0.04 |
| BTCUSD | IS | 89 | 58 % | +61.7 | +0.69 | 0.431 | 0.73 | 56 | +18.0 | +0.32 | +43.7 | 38 | +8.6 | +0.23 | +53.1 | 45 | +13.2 | +0.29 | +48.5 | 0.91 / 0.87 |
| BTCUSD | OOS | 130 | 33 % | -41.6 | -0.32 | 0.446 | 0.65 | 22 | -4.3 | -0.20 | -37.3 | 6 | -0.2 | -0.03 | -41.5 | 65 | -28.2 | -0.43 | -13.4 | 0.32 / 0.74 |
| POOLED | IS | 322 | 51 % | +206.0 | +0.64 | 0.502 | 0.38 | 179 | +92.0 | +0.51 | +113.9 | 56 | +41.5 | +0.74 | +164.4 | 161 | +81.8 | +0.51 | +124.2 | 0.81 / 0.80 |
| POOLED | OOS | 698 | 30 % | -76.3 | -0.11 | 0.504 | 0.42 | 5 | +3.0 | +0.61 | -79.3 | 0 | +0.0 | nan | -76.3 | 349 | -34.7 | -0.10 | -41.6 | 0.12 / 0.43 |

### Transfer: train on one whole period, score the other (top = p above the training set's median fitted p)

| set | train -> test | n test | base R | R/tr | AUC | perm p | fit AUC (train) | p>=0.5: kept, R, R/tr, R removed | p>=0.6: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed | gain p (p>=0.5 / top) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | IS->OOS | 97 | -1.2 | -0.01 | 0.326 | 0.99 | 0.982 | 40 | -16.2 | -0.40 | +14.9 | 21 | -10.7 | -0.51 | +9.5 | 48 | -25.0 | -0.52 | +23.7 | 0.89 / 0.99 |
| EURUSD | OOS->IS | 47 | +39.5 | +0.84 | 0.505 | 0.42 | 0.975 | 2 | +1.0 | +0.50 | +38.5 | 1 | -1.1 | -1.10 | +40.6 | 28 | +10.2 | +0.36 | +29.3 | 0.59 / 0.88 |
| XAUUSD | IS->OOS | 371 | -62.2 | -0.17 | 0.535 | 0.19 | 0.868 | 204 | -33.4 | -0.16 | -28.8 | 92 | -1.9 | -0.02 | -60.3 | 221 | -41.7 | -0.19 | -20.5 | 0.51 / 0.55 |
| XAUUSD | OOS->IS | 143 | +71.8 | +0.50 | 0.565 | 0.06 | 0.798 | 0 | +0.0 | nan | +71.8 | 0 | +0.0 | nan | +71.8 | 71 | +32.4 | +0.46 | +39.4 | nan / 0.61 |
| NAS100 | IS->OOS | 100 | +28.8 | +0.29 | 0.462 | 0.69 | 0.998 | 46 | -10.9 | -0.24 | +39.7 | 27 | -9.1 | -0.34 | +37.9 | 58 | +7.2 | +0.12 | +21.6 | 0.94 / 0.66 |
| NAS100 | OOS->IS | 43 | +32.9 | +0.77 | 0.427 | 0.72 | 0.965 | 6 | -3.1 | -0.52 | +36.0 | 1 | +2.4 | +2.40 | +30.5 | 23 | +15.2 | +0.66 | +17.7 | 0.87 / 0.60 |
| BTCUSD | IS->OOS | 130 | -41.6 | -0.32 | 0.441 | 0.84 | 0.943 | 95 | -32.8 | -0.35 | -8.8 | 68 | -37.3 | -0.55 | -4.4 | 62 | -34.5 | -0.56 | -7.1 | 0.66 / 1.00 |
| BTCUSD | OOS->IS | 89 | +61.7 | +0.69 | 0.429 | 0.92 | 0.932 | 5 | +2.9 | +0.58 | +58.8 | 0 | +0.0 | nan | +61.7 | 36 | +35.6 | +0.99 | +26.1 | 0.38 / 0.19 |
| POOLED | IS->OOS | 698 | -76.3 | -0.11 | 0.494 | 0.54 | 0.809 | 414 | -62.4 | -0.15 | -14.0 | 149 | -31.8 | -0.21 | -44.5 | 364 | -71.3 | -0.20 | -5.0 | 0.73 / 0.84 |
| POOLED | OOS->IS | 322 | +206.0 | +0.64 | 0.523 | 0.24 | 0.718 | 0 | +0.0 | nan | +206.0 | 0 | +0.0 | nan | +206.0 | 158 | +84.9 | +0.54 | +121.1 | nan / 0.80 |

### Pooled model, per-market breakdown of the transfer selections

| train -> test | market | n | base R | AUC | p>=0.5: kept, R, R/tr, R removed | top: kept, R, R/tr, R removed |
|---|---|---|---|---|---|---|
| IS->OOS | BTCUSD | 130 | -41.6 | 0.469 | 91 | -27.7 | -0.30 | -13.9 | 86 | -27.4 | -0.32 | -14.2 |
| IS->OOS | EURUSD | 97 | -1.2 | 0.436 | 41 | -7.0 | -0.17 | +5.8 | 39 | -4.8 | -0.12 | +3.6 |
| IS->OOS | NAS100 | 100 | +28.8 | 0.530 | 56 | +20.3 | +0.36 | +8.5 | 42 | +6.3 | +0.15 | +22.5 |
| IS->OOS | XAUUSD | 371 | -62.2 | 0.499 | 226 | -47.9 | -0.21 | -14.3 | 197 | -45.3 | -0.23 | -16.9 |
| OOS->IS | BTCUSD | 89 | +61.7 | 0.429 | 0 | +0.0 | nan | +61.7 | 49 | +20.6 | +0.42 | +41.1 |
| OOS->IS | EURUSD | 47 | +39.5 | 0.560 | 0 | +0.0 | nan | +39.5 | 16 | +15.2 | +0.95 | +24.3 |
| OOS->IS | NAS100 | 43 | +32.9 | 0.474 | 0 | +0.0 | nan | +32.9 | 27 | +15.9 | +0.59 | +17.0 |
| OOS->IS | XAUUSD | 143 | +71.8 | 0.567 | 0 | +0.0 | nan | +71.8 | 66 | +33.2 | +0.50 | +38.6 |

### Importances

- EURUSD IS->OOS: permutation AUC drop on the test period, top 6: atr14d_pct -0.001, pd_pos -0.001, ret5d_dir -0.003, drift_atr -0.006, behind_pd_atr -0.011, er20 -0.020
- EURUSD OOS->IS: permutation AUC drop on the test period, top 6: drift_atr +0.032, atr14d_pct +0.015, rng14_pct +0.004, pd_pos +0.001, er20 -0.004, ret5d_dir -0.020
- XAUUSD IS->OOS: permutation AUC drop on the test period, top 6: atr14d_pct +0.030, behind_pd_atr +0.014, pd_pos +0.010, rng14_pct +0.005, drift_atr +0.001, room_pd_atr +0.000
- XAUUSD OOS->IS: permutation AUC drop on the test period, top 6: atr14d_pct +0.026, room_pd_atr +0.023, rng14_pct +0.022, er20 +0.016, behind_pd_atr +0.015, pd_pos +0.009
- NAS100 IS->OOS: permutation AUC drop on the test period, top 6: ret5d_dir +0.016, drift_atr +0.000, rng14_pct -0.003, atr14d_pct -0.005, pd_pos -0.005, drift_abs -0.008
- NAS100 OOS->IS: permutation AUC drop on the test period, top 6: er20 +0.035, behind_pd_atr +0.031, rng14_pct +0.002, drift_abs +0.001, pd_pos +0.000, ret5d_dir -0.021
- BTCUSD IS->OOS: permutation AUC drop on the test period, top 6: pd_pos +0.016, room_pd_atr +0.005, behind_pd_atr +0.002, drift_atr -0.001, drift_abs -0.002, rng14_pct -0.015
- BTCUSD OOS->IS: permutation AUC drop on the test period, top 6: behind_pd_atr -0.000, drift_abs -0.000, er20 -0.002, pd_pos -0.006, room_pd_atr -0.015, atr14d_pct -0.017
- POOLED IS->OOS: permutation AUC drop on the test period, top 6: room_pd_atr +0.012, rng14_pct +0.005, ret5d_dir +0.000, mkt_EURUSD +0.000, mkt_XAUUSD +0.000, mkt_NAS100 +0.000
- POOLED OOS->IS: permutation AUC drop on the test period, top 6: behind_pd_atr +0.012, atr14d_pct +0.005, pd_pos +0.005, room_pd_atr +0.003, rng14_pct +0.002, ret5d_dir +0.001


</details>


## Appendix B: post-hoc (threshold sweep, both-periods verdict, probability quintiles, power)


<details><summary>lr_all</summary>

## post-hoc on lr_all.json (model=lr, features=all)

### Threshold sweep: keep the trades with p above the q-quantile (q=0.2 = veto the worst fifth, q=0.5 = keep the top half). CV: the OOF p's own quantile; transfer: the training set's fitted-p quantile. Cells: kept trades | R removed (negative = the filter helped)

| set | model trained on | applied to | q=0.2 | q=0.3 | q=0.5 | q=0.7 |
|---|---|---|---|---|---|---|
| EURUSD | IS (n=47, R +39.5) | IS purged CV | 37 \| +12.5 | 33 \| +24.2 | 24 \| +29.7 | 14 \| +38.5 |
| EURUSD | IS | OOS transfer (n=97, R -1.2) | 73 \| +14.9 | 61 \| +8.7 | 48 \| +4.2 | 27 \| -5.2 |
| EURUSD | OOS (n=97, R -1.2) | OOS purged CV | 77 \| -0.5 | 68 \| -0.6 | 49 \| -13.0 | 29 \| -18.9 |
| EURUSD | OOS | IS transfer (n=47, R +39.5) | 34 \| +5.1 | 30 \| +3.8 | 19 \| +18.5 | 13 \| +29.4 |
| XAUUSD | IS (n=143, R +71.8) | IS purged CV | 114 \| +26.0 | 100 \| +36.5 | 72 \| +53.8 | 43 \| +58.7 |
| XAUUSD | IS | OOS transfer (n=371, R -62.2) | 318 \| +3.1 | 292 \| -3.3 | 249 \| -16.1 | 187 \| -7.4 |
| XAUUSD | OOS (n=371, R -62.2) | OOS purged CV | 297 \| -14.6 | 260 \| -20.7 | 186 \| -11.8 | 112 \| -45.9 |
| XAUUSD | OOS | IS transfer (n=143, R +71.8) | 105 \| +16.6 | 86 \| +24.4 | 57 \| +45.8 | 39 \| +57.8 |
| NAS100 | IS (n=43, R +32.9) | IS purged CV | 34 \| +2.2 | 30 \| +7.8 | 22 \| +24.5 | 13 \| +30.1 |
| NAS100 | IS | OOS transfer (n=100, R +28.8) | 65 \| +17.6 | 55 \| +32.8 | 44 \| +27.8 | 31 \| +26.0 |
| NAS100 | OOS (n=100, R +28.8) | OOS purged CV | 80 \| +6.4 | 70 \| +1.4 | 50 \| +5.8 | 30 \| +11.1 |
| NAS100 | OOS | IS transfer (n=43, R +32.9) | 28 \| +11.0 | 28 \| +11.0 | 19 \| +13.6 | 11 \| +30.7 |
| BTCUSD | IS (n=89, R +61.7) | IS purged CV | 71 \| +41.2 | 62 \| +42.7 | 45 \| +50.0 | 27 \| +64.2 |
| BTCUSD | IS | OOS transfer (n=130, R -41.6) | 102 \| -13.5 | 89 \| -14.2 | 77 \| -18.2 | 65 \| -26.7 |
| BTCUSD | OOS (n=130, R -41.6) | OOS purged CV | 104 \| -14.6 | 91 \| -4.2 | 65 \| -18.6 | 39 \| -34.8 |
| BTCUSD | OOS | IS transfer (n=89, R +61.7) | 60 \| +40.5 | 52 \| +42.1 | 39 \| +54.8 | 25 \| +61.9 |
| POOLED | IS (n=322, R +206.0) | IS purged CV | 257 \| +123.6 | 225 \| +146.6 | 161 \| +170.6 | 97 \| +186.3 |
| POOLED | IS | OOS transfer (n=698, R -76.3) | 522 \| +43.2 | 469 \| +11.4 | 360 \| -2.6 | 268 \| -14.5 |
| POOLED | OOS (n=698, R -76.3) | OOS purged CV | 558 \| +31.7 | 488 \| +0.5 | 349 \| +46.1 | 210 \| -6.2 |
| POOLED | OOS | IS transfer (n=322, R +206.0) | 259 \| +65.9 | 224 \| +84.9 | 149 \| +158.4 | 85 \| +187.9 |

### Both-periods verdict: a cut passes when it removes negative R both in its training period's purged CV and in the other period

| set | trained on | q | CV R removed | transfer R removed | verdict |
|---|---|---|---|---|---|
| EURUSD | IS | 0.2 | +12.5 | +14.9 | fail |
| EURUSD | IS | 0.3 | +24.2 | +8.7 | fail |
| EURUSD | IS | 0.5 | +29.7 | +4.2 | fail |
| EURUSD | IS | 0.7 | +38.5 | -5.2 | fail |
| EURUSD | OOS | 0.2 | -0.5 | +5.1 | fail |
| EURUSD | OOS | 0.3 | -0.6 | +3.8 | fail |
| EURUSD | OOS | 0.5 | -13.0 | +18.5 | fail |
| EURUSD | OOS | 0.7 | -18.9 | +29.4 | fail |
| XAUUSD | IS | 0.2 | +26.0 | +3.1 | fail |
| XAUUSD | IS | 0.3 | +36.5 | -3.3 | fail |
| XAUUSD | IS | 0.5 | +53.8 | -16.1 | fail |
| XAUUSD | IS | 0.7 | +58.7 | -7.4 | fail |
| XAUUSD | OOS | 0.2 | -14.6 | +16.6 | fail |
| XAUUSD | OOS | 0.3 | -20.7 | +24.4 | fail |
| XAUUSD | OOS | 0.5 | -11.8 | +45.8 | fail |
| XAUUSD | OOS | 0.7 | -45.9 | +57.8 | fail |
| NAS100 | IS | 0.2 | +2.2 | +17.6 | fail |
| NAS100 | IS | 0.3 | +7.8 | +32.8 | fail |
| NAS100 | IS | 0.5 | +24.5 | +27.8 | fail |
| NAS100 | IS | 0.7 | +30.1 | +26.0 | fail |
| NAS100 | OOS | 0.2 | +6.4 | +11.0 | fail |
| NAS100 | OOS | 0.3 | +1.4 | +11.0 | fail |
| NAS100 | OOS | 0.5 | +5.8 | +13.6 | fail |
| NAS100 | OOS | 0.7 | +11.1 | +30.7 | fail |
| BTCUSD | IS | 0.2 | +41.2 | -13.5 | fail |
| BTCUSD | IS | 0.3 | +42.7 | -14.2 | fail |
| BTCUSD | IS | 0.5 | +50.0 | -18.2 | fail |
| BTCUSD | IS | 0.7 | +64.2 | -26.7 | fail |
| BTCUSD | OOS | 0.2 | -14.6 | +40.5 | fail |
| BTCUSD | OOS | 0.3 | -4.2 | +42.1 | fail |
| BTCUSD | OOS | 0.5 | -18.6 | +54.8 | fail |
| BTCUSD | OOS | 0.7 | -34.8 | +61.9 | fail |
| POOLED | IS | 0.2 | +123.6 | +43.2 | fail |
| POOLED | IS | 0.3 | +146.6 | +11.4 | fail |
| POOLED | IS | 0.5 | +170.6 | -2.6 | fail |
| POOLED | IS | 0.7 | +186.3 | -14.5 | fail |
| POOLED | OOS | 0.2 | +31.7 | +65.9 | fail |
| POOLED | OOS | 0.3 | +0.5 | +84.9 | fail |
| POOLED | OOS | 0.5 | +46.1 | +158.4 | fail |
| POOLED | OOS | 0.7 | -6.2 | +187.9 | fail |

0 of 40 cuts pass (chance alone would pass about a quarter: each sign is a coin flip when the model has no skill).

### Probability deciles of the pooled transfers (n, win rate, R a trade after costs)

pooled IS->OOS (quintiles of p, 1 = lowest):
       n  p_mean    win    rpt       R
dec                                   
1    140   0.310  0.286  0.352  49.265
2    139   0.437  0.245 -0.325 -45.150
3    140   0.516  0.336 -0.100 -13.992
4    139   0.603  0.266 -0.316 -43.861
5    140   0.719  0.371 -0.161 -22.565

pooled OOS->IS (quintiles of p, 1 = lowest):
      n  p_mean    win    rpt       R
dec                                  
1    65   0.161  0.369  1.159  75.362
2    64   0.251  0.469  0.508  32.541
3    64   0.293  0.641  0.958  61.314
4    64   0.342  0.547  0.315  20.157
5    65   0.446  0.523  0.255  16.597

### Pooled purged-CV OOF quintiles

pooled IS OOF (quintiles of p):
      n  p_mean    win    rpt        R
dec                                   
1    65   0.292  0.615  1.901  123.552
2    64   0.429  0.516  0.567   36.291
3    64   0.492  0.422  0.241   15.422
4    64   0.559  0.453  0.253   16.171
5    65   0.683  0.538  0.224   14.535

pooled OOS OOF (quintiles of p):
       n  p_mean    win    rpt       R
dec                                   
1    140   0.140  0.286  0.227  31.727
2    139   0.238  0.345  0.053   7.356
3    140   0.295  0.307 -0.127 -17.819
4    139   0.360  0.245 -0.443 -61.626
5    140   0.473  0.321 -0.257 -35.942

### What AUC the sample could have detected (permutation null of the OOF AUC; one-sided 95 % = 0.5 + 1.65 sd)

| set | period | n | null AUC mean | null sd | detectable AUC | observed |
|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 0.481 | 0.111 | 0.683 | 0.358 |
| EURUSD | OOS | 97 | 0.482 | 0.090 | 0.649 | 0.582 |
| XAUUSD | IS | 143 | 0.489 | 0.068 | 0.611 | 0.456 |
| XAUUSD | OOS | 371 | 0.496 | 0.047 | 0.577 | 0.542 |
| NAS100 | IS | 43 | 0.464 | 0.120 | 0.698 | 0.467 |
| NAS100 | OOS | 100 | 0.478 | 0.085 | 0.640 | 0.550 |
| BTCUSD | IS | 89 | 0.488 | 0.076 | 0.625 | 0.468 |
| BTCUSD | OOS | 130 | 0.496 | 0.073 | 0.620 | 0.518 |
| POOLED | IS | 322 | 0.493 | 0.045 | 0.574 | 0.452 |
| POOLED | OOS | 698 | 0.497 | 0.033 | 0.554 | 0.499 |


</details>


<details><summary>gb_all</summary>

## post-hoc on gb_all.json (model=gb, features=all)

### Threshold sweep: keep the trades with p above the q-quantile (q=0.2 = veto the worst fifth, q=0.5 = keep the top half). CV: the OOF p's own quantile; transfer: the training set's fitted-p quantile. Cells: kept trades | R removed (negative = the filter helped)

| set | model trained on | applied to | q=0.2 | q=0.3 | q=0.5 | q=0.7 |
|---|---|---|---|---|---|---|
| EURUSD | IS (n=47, R +39.5) | IS purged CV | 37 \| +15.3 | 33 \| +18.7 | 24 \| +21.3 | 14 \| +29.9 |
| EURUSD | IS | OOS transfer (n=97, R -1.2) | 84 \| +0.8 | 75 \| +1.7 | 28 \| +14.5 | 8 \| +6.6 |
| EURUSD | OOS (n=97, R -1.2) | OOS purged CV | 77 \| -5.6 | 68 \| -3.4 | 49 \| -19.0 | 29 \| -18.9 |
| EURUSD | OOS | IS transfer (n=47, R +39.5) | 42 \| +4.6 | 37 \| -0.9 | 25 \| +23.7 | 15 \| +32.5 |
| XAUUSD | IS (n=143, R +71.8) | IS purged CV | 114 \| +39.3 | 100 \| +47.8 | 72 \| +55.2 | 43 \| +64.3 |
| XAUUSD | IS | OOS transfer (n=371, R -62.2) | 337 \| +4.8 | 305 \| -1.6 | 206 \| -48.2 | 135 \| -46.5 |
| XAUUSD | OOS (n=371, R -62.2) | OOS purged CV | 297 \| -7.6 | 260 \| -17.5 | 186 \| -19.7 | 112 \| -39.8 |
| XAUUSD | OOS | IS transfer (n=143, R +71.8) | 114 \| +36.0 | 100 \| +35.6 | 72 \| +38.4 | 39 \| +55.8 |
| NAS100 | IS (n=43, R +32.9) | IS purged CV | 34 \| +15.8 | 30 \| +18.4 | 22 \| +20.5 | 13 \| +18.1 |
| NAS100 | IS | OOS transfer (n=100, R +28.8) | 85 \| +3.8 | 83 \| +5.0 | 61 \| +16.6 | 7 \| +36.5 |
| NAS100 | OOS (n=100, R +28.8) | OOS purged CV | 80 \| -18.8 | 70 \| -8.9 | 50 \| +4.5 | 30 \| +27.9 |
| NAS100 | OOS | IS transfer (n=43, R +32.9) | 35 \| +5.1 | 33 \| +7.1 | 19 \| +20.4 | 8 \| +32.3 |
| BTCUSD | IS (n=89, R +61.7) | IS purged CV | 71 \| +2.1 | 62 \| +23.7 | 45 \| +47.9 | 27 \| +54.3 |
| BTCUSD | IS | OOS transfer (n=130, R -41.6) | 126 \| -1.4 | 123 \| -1.9 | 80 \| -18.1 | 39 \| -25.4 |
| BTCUSD | OOS (n=130, R -41.6) | OOS purged CV | 104 \| -9.5 | 91 \| -6.1 | 65 \| -13.9 | 39 \| -27.8 |
| BTCUSD | OOS | IS transfer (n=89, R +61.7) | 70 \| +9.9 | 57 \| +5.2 | 45 \| +22.2 | 30 \| +34.2 |
| POOLED | IS (n=322, R +206.0) | IS purged CV | 257 \| +112.0 | 225 \| +144.6 | 161 \| +165.5 | 97 \| +188.2 |
| POOLED | IS | OOS transfer (n=698, R -76.3) | 578 \| +11.6 | 512 \| +9.9 | 363 \| +1.1 | 182 \| -43.7 |
| POOLED | OOS (n=698, R -76.3) | OOS purged CV | 558 \| +0.3 | 488 \| -9.3 | 349 \| -25.1 | 210 \| -50.4 |
| POOLED | OOS | IS transfer (n=322, R +206.0) | 262 \| +102.3 | 237 \| +106.3 | 128 \| +184.2 | 69 \| +191.9 |

### Both-periods verdict: a cut passes when it removes negative R both in its training period's purged CV and in the other period

| set | trained on | q | CV R removed | transfer R removed | verdict |
|---|---|---|---|---|---|
| EURUSD | IS | 0.2 | +15.3 | +0.8 | fail |
| EURUSD | IS | 0.3 | +18.7 | +1.7 | fail |
| EURUSD | IS | 0.5 | +21.3 | +14.5 | fail |
| EURUSD | IS | 0.7 | +29.9 | +6.6 | fail |
| EURUSD | OOS | 0.2 | -5.6 | +4.6 | fail |
| EURUSD | OOS | 0.3 | -3.4 | -0.9 | PASS |
| EURUSD | OOS | 0.5 | -19.0 | +23.7 | fail |
| EURUSD | OOS | 0.7 | -18.9 | +32.5 | fail |
| XAUUSD | IS | 0.2 | +39.3 | +4.8 | fail |
| XAUUSD | IS | 0.3 | +47.8 | -1.6 | fail |
| XAUUSD | IS | 0.5 | +55.2 | -48.2 | fail |
| XAUUSD | IS | 0.7 | +64.3 | -46.5 | fail |
| XAUUSD | OOS | 0.2 | -7.6 | +36.0 | fail |
| XAUUSD | OOS | 0.3 | -17.5 | +35.6 | fail |
| XAUUSD | OOS | 0.5 | -19.7 | +38.4 | fail |
| XAUUSD | OOS | 0.7 | -39.8 | +55.8 | fail |
| NAS100 | IS | 0.2 | +15.8 | +3.8 | fail |
| NAS100 | IS | 0.3 | +18.4 | +5.0 | fail |
| NAS100 | IS | 0.5 | +20.5 | +16.6 | fail |
| NAS100 | IS | 0.7 | +18.1 | +36.5 | fail |
| NAS100 | OOS | 0.2 | -18.8 | +5.1 | fail |
| NAS100 | OOS | 0.3 | -8.9 | +7.1 | fail |
| NAS100 | OOS | 0.5 | +4.5 | +20.4 | fail |
| NAS100 | OOS | 0.7 | +27.9 | +32.3 | fail |
| BTCUSD | IS | 0.2 | +2.1 | -1.4 | fail |
| BTCUSD | IS | 0.3 | +23.7 | -1.9 | fail |
| BTCUSD | IS | 0.5 | +47.9 | -18.1 | fail |
| BTCUSD | IS | 0.7 | +54.3 | -25.4 | fail |
| BTCUSD | OOS | 0.2 | -9.5 | +9.9 | fail |
| BTCUSD | OOS | 0.3 | -6.1 | +5.2 | fail |
| BTCUSD | OOS | 0.5 | -13.9 | +22.2 | fail |
| BTCUSD | OOS | 0.7 | -27.8 | +34.2 | fail |
| POOLED | IS | 0.2 | +112.0 | +11.6 | fail |
| POOLED | IS | 0.3 | +144.6 | +9.9 | fail |
| POOLED | IS | 0.5 | +165.5 | +1.1 | fail |
| POOLED | IS | 0.7 | +188.2 | -43.7 | fail |
| POOLED | OOS | 0.2 | +0.3 | +102.3 | fail |
| POOLED | OOS | 0.3 | -9.3 | +106.3 | fail |
| POOLED | OOS | 0.5 | -25.1 | +184.2 | fail |
| POOLED | OOS | 0.7 | -50.4 | +191.9 | fail |

1 of 40 cuts pass (chance alone would pass about a quarter: each sign is a coin flip when the model has no skill).

### Probability deciles of the pooled transfers (n, win rate, R a trade after costs)

pooled IS->OOS (quintiles of p, 1 = lowest):
       n  p_mean    win    rpt       R
dec                                   
1    140   0.381  0.271  0.153  21.483
2    139   0.463  0.288 -0.074 -10.256
3    140   0.507  0.271 -0.221 -30.977
4    139   0.550  0.302 -0.163 -22.605
5    140   0.642  0.371 -0.242 -33.948

pooled OOS->IS (quintiles of p, 1 = lowest):
      n  p_mean    win    rpt        R
dec                                   
1    65   0.195  0.462  1.593  103.513
2    64   0.248  0.484  0.570   36.466
3    64   0.274  0.516  0.653   41.795
4    64   0.315  0.516  0.236   15.084
5    65   0.417  0.569  0.140    9.114

### Pooled purged-CV OOF quintiles

pooled IS OOF (quintiles of p):
      n  p_mean    win    rpt        R
dec                                   
1    65   0.360  0.538  1.723  112.022
2    64   0.458  0.594  0.840   53.750
3    64   0.508  0.469  0.421   26.919
4    64   0.560  0.391 -0.025   -1.610
5    65   0.671  0.554  0.229   14.890

pooled OOS OOF (quintiles of p):
       n  p_mean    win    rpt       R
dec                                   
1    140   0.182  0.243  0.002   0.327
2    139   0.241  0.288 -0.055  -7.615
3    140   0.282  0.257 -0.331 -46.358
4    139   0.334  0.317 -0.101 -14.107
5    140   0.439  0.400 -0.061  -8.549

### What AUC the sample could have detected (permutation null of the OOF AUC; one-sided 95 % = 0.5 + 1.65 sd)

| set | period | n | null AUC mean | null sd | detectable AUC | observed |
|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 0.466 | 0.112 | 0.685 | 0.478 |
| EURUSD | OOS | 97 | 0.468 | 0.084 | 0.639 | 0.644 |
| XAUUSD | IS | 143 | 0.486 | 0.070 | 0.616 | 0.418 |
| XAUUSD | OOS | 371 | 0.489 | 0.047 | 0.577 | 0.563 |
| NAS100 | IS | 43 | 0.452 | 0.120 | 0.698 | 0.407 |
| NAS100 | OOS | 100 | 0.471 | 0.081 | 0.634 | 0.621 |
| BTCUSD | IS | 89 | 0.471 | 0.083 | 0.637 | 0.611 |
| BTCUSD | OOS | 130 | 0.488 | 0.069 | 0.614 | 0.536 |
| POOLED | IS | 322 | 0.487 | 0.041 | 0.568 | 0.485 |
| POOLED | OOS | 698 | 0.497 | 0.033 | 0.555 | 0.564 |


</details>


<details><summary>ridge_all</summary>

## post-hoc on ridge_all.json (model=ridge, features=all)

### Threshold sweep: keep the trades with p above the q-quantile (q=0.2 = veto the worst fifth, q=0.5 = keep the top half). CV: the OOF p's own quantile; transfer: the training set's fitted-p quantile. Cells: kept trades | R removed (negative = the filter helped)

| set | model trained on | applied to | q=0.2 | q=0.3 | q=0.5 | q=0.7 |
|---|---|---|---|---|---|---|
| EURUSD | IS (n=47, R +39.5) | IS purged CV | 37 \| +14.3 | 33 \| +18.9 | 24 \| +28.9 | 14 \| +34.1 |
| EURUSD | IS | OOS transfer (n=97, R -1.2) | 65 \| -2.9 | 64 \| -4.0 | 58 \| +10.1 | 50 \| +4.4 |
| EURUSD | OOS (n=97, R -1.2) | OOS purged CV | 77 \| -3.3 | 68 \| -7.0 | 49 \| -16.7 | 29 \| -20.3 |
| EURUSD | OOS | IS transfer (n=47, R +39.5) | 21 \| +23.0 | 21 \| +23.0 | 20 \| +24.9 | 18 \| +28.4 |
| XAUUSD | IS (n=143, R +71.8) | IS purged CV | 114 \| +15.3 | 100 \| +22.5 | 72 \| +32.8 | 43 \| +64.4 |
| XAUUSD | IS | OOS transfer (n=371, R -62.2) | 264 \| -27.6 | 257 \| -29.3 | 242 \| -36.6 | 234 \| -36.0 |
| XAUUSD | OOS (n=371, R -62.2) | OOS purged CV | 297 \| -18.4 | 260 \| -10.0 | 186 \| -21.2 | 112 \| -39.4 |
| XAUUSD | OOS | IS transfer (n=143, R +71.8) | 33 \| +59.8 | 31 \| +57.6 | 27 \| +57.2 | 21 \| +53.7 |
| NAS100 | IS (n=43, R +32.9) | IS purged CV | 34 \| +6.1 | 30 \| +14.6 | 22 \| +16.6 | 13 \| +24.8 |
| NAS100 | IS | OOS transfer (n=100, R +28.8) | 64 \| +16.9 | 64 \| +16.9 | 58 \| +20.5 | 51 \| +22.2 |
| NAS100 | OOS (n=100, R +28.8) | OOS purged CV | 80 \| -6.5 | 70 \| -14.9 | 50 \| -16.3 | 30 \| +1.7 |
| NAS100 | OOS | IS transfer (n=43, R +32.9) | 22 \| +9.3 | 22 \| +9.3 | 21 \| +11.7 | 17 \| +22.5 |
| BTCUSD | IS (n=89, R +61.7) | IS purged CV | 71 \| +31.0 | 62 \| +32.0 | 45 \| +37.8 | 27 \| +47.5 |
| BTCUSD | IS | OOS transfer (n=130, R -41.6) | 76 \| -21.7 | 73 \| -20.6 | 64 \| -25.1 | 59 \| -28.1 |
| BTCUSD | OOS (n=130, R -41.6) | OOS purged CV | 104 \| -9.4 | 91 \| -17.5 | 65 \| -15.2 | 39 \| -31.6 |
| BTCUSD | OOS | IS transfer (n=89, R +61.7) | 15 \| +57.4 | 12 \| +61.6 | 11 \| +60.5 | 9 \| +62.1 |
| POOLED | IS (n=322, R +206.0) | IS purged CV | 257 \| +72.3 | 225 \| +94.9 | 161 \| +146.6 | 97 \| +176.9 |
| POOLED | IS | OOS transfer (n=698, R -76.3) | 436 \| -7.4 | 425 \| -9.6 | 405 \| -4.9 | 394 \| -6.1 |
| POOLED | OOS (n=698, R -76.3) | OOS purged CV | 558 \| -8.8 | 488 \| -15.2 | 349 \| -42.1 | 210 \| -66.4 |
| POOLED | OOS | IS transfer (n=322, R +206.0) | 64 \| +148.0 | 62 \| +150.7 | 53 \| +161.5 | 42 \| +168.6 |

### Both-periods verdict: a cut passes when it removes negative R both in its training period's purged CV and in the other period

| set | trained on | q | CV R removed | transfer R removed | verdict |
|---|---|---|---|---|---|
| EURUSD | IS | 0.2 | +14.3 | -2.9 | fail |
| EURUSD | IS | 0.3 | +18.9 | -4.0 | fail |
| EURUSD | IS | 0.5 | +28.9 | +10.1 | fail |
| EURUSD | IS | 0.7 | +34.1 | +4.4 | fail |
| EURUSD | OOS | 0.2 | -3.3 | +23.0 | fail |
| EURUSD | OOS | 0.3 | -7.0 | +23.0 | fail |
| EURUSD | OOS | 0.5 | -16.7 | +24.9 | fail |
| EURUSD | OOS | 0.7 | -20.3 | +28.4 | fail |
| XAUUSD | IS | 0.2 | +15.3 | -27.6 | fail |
| XAUUSD | IS | 0.3 | +22.5 | -29.3 | fail |
| XAUUSD | IS | 0.5 | +32.8 | -36.6 | fail |
| XAUUSD | IS | 0.7 | +64.4 | -36.0 | fail |
| XAUUSD | OOS | 0.2 | -18.4 | +59.8 | fail |
| XAUUSD | OOS | 0.3 | -10.0 | +57.6 | fail |
| XAUUSD | OOS | 0.5 | -21.2 | +57.2 | fail |
| XAUUSD | OOS | 0.7 | -39.4 | +53.7 | fail |
| NAS100 | IS | 0.2 | +6.1 | +16.9 | fail |
| NAS100 | IS | 0.3 | +14.6 | +16.9 | fail |
| NAS100 | IS | 0.5 | +16.6 | +20.5 | fail |
| NAS100 | IS | 0.7 | +24.8 | +22.2 | fail |
| NAS100 | OOS | 0.2 | -6.5 | +9.3 | fail |
| NAS100 | OOS | 0.3 | -14.9 | +9.3 | fail |
| NAS100 | OOS | 0.5 | -16.3 | +11.7 | fail |
| NAS100 | OOS | 0.7 | +1.7 | +22.5 | fail |
| BTCUSD | IS | 0.2 | +31.0 | -21.7 | fail |
| BTCUSD | IS | 0.3 | +32.0 | -20.6 | fail |
| BTCUSD | IS | 0.5 | +37.8 | -25.1 | fail |
| BTCUSD | IS | 0.7 | +47.5 | -28.1 | fail |
| BTCUSD | OOS | 0.2 | -9.4 | +57.4 | fail |
| BTCUSD | OOS | 0.3 | -17.5 | +61.6 | fail |
| BTCUSD | OOS | 0.5 | -15.2 | +60.5 | fail |
| BTCUSD | OOS | 0.7 | -31.6 | +62.1 | fail |
| POOLED | IS | 0.2 | +72.3 | -7.4 | fail |
| POOLED | IS | 0.3 | +94.9 | -9.6 | fail |
| POOLED | IS | 0.5 | +146.6 | -4.9 | fail |
| POOLED | IS | 0.7 | +176.9 | -6.1 | fail |
| POOLED | OOS | 0.2 | -8.8 | +148.0 | fail |
| POOLED | OOS | 0.3 | -15.2 | +150.7 | fail |
| POOLED | OOS | 0.5 | -42.1 | +161.5 | fail |
| POOLED | OOS | 0.7 | -66.4 | +168.6 | fail |

0 of 40 cuts pass (chance alone would pass about a quarter: each sign is a coin flip when the model has no skill).

### Probability deciles of the pooled transfers (n, win rate, R a trade after costs)

pooled IS->OOS (quintiles of p, 1 = lowest):
       n  p_mean    win    rpt       R
dec                                   
1    140  -0.316  0.364 -0.098 -13.691
2    139   0.289  0.353 -0.018  -2.462
3    140   0.673  0.271 -0.139 -19.418
4    139   1.038  0.259 -0.259 -35.942
5    140   1.878  0.257 -0.034  -4.790

pooled OOS->IS (quintiles of p, 1 = lowest):
      n  p_mean    win    rpt       R
dec                                  
1    65  -0.573  0.600  0.422  27.454
2    64  -0.315  0.500  0.238  15.254
3    64  -0.139  0.500  0.461  29.515
4    64   0.052  0.500  1.161  74.311
5    65   0.642  0.446  0.914  59.437

### Pooled purged-CV OOF quintiles

pooled IS OOF (quintiles of p):
      n  p_mean    win    rpt       R
dec                                  
1    65  -0.445  0.662  1.113  72.349
2    64   0.154  0.547  0.778  49.810
3    64   0.438  0.547  0.766  49.019
4    64   0.764  0.422  0.143   9.151
5    65   2.148  0.369  0.394  25.641

pooled OOS OOF (quintiles of p):
       n  p_mean    win    rpt       R
dec                                   
1    140  -0.724  0.371 -0.063  -8.764
2    139  -0.367  0.345 -0.132 -18.415
3    140  -0.146  0.314 -0.126 -17.617
4    139   0.084  0.245 -0.290 -40.273
5    140   0.574  0.229  0.063   8.767

### What AUC the sample could have detected (permutation null of the OOF AUC; one-sided 95 % = 0.5 + 1.65 sd)

| set | period | n | null AUC mean | null sd | detectable AUC | observed |
|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 0.486 | 0.108 | 0.679 | 0.345 |
| EURUSD | OOS | 97 | 0.485 | 0.086 | 0.641 | 0.604 |
| XAUUSD | IS | 143 | 0.495 | 0.065 | 0.606 | 0.423 |
| XAUUSD | OOS | 371 | 0.496 | 0.042 | 0.569 | 0.480 |
| NAS100 | IS | 43 | 0.472 | 0.112 | 0.685 | 0.411 |
| NAS100 | OOS | 100 | 0.484 | 0.080 | 0.633 | 0.562 |
| BTCUSD | IS | 89 | 0.501 | 0.068 | 0.612 | 0.386 |
| BTCUSD | OOS | 130 | 0.499 | 0.069 | 0.614 | 0.500 |
| POOLED | IS | 322 | 0.494 | 0.042 | 0.569 | 0.372 |
| POOLED | OOS | 698 | 0.497 | 0.030 | 0.549 | 0.427 |


</details>


## Appendix C: within-fold AUC and within-fold selections


<details><summary>lr_all</summary>

## within-fold view of lr_all.json (model=lr, features=all)

| set | period | n | pooled OOF AUC | mean within-fold AUC (sd over folds) | fold win rates | within-fold top half: kept, R, R removed | within-fold bottom fifth removed: R removed |
|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 0.358 | 0.363 (0.096) | 20% 50% 56% 56% 56% | 25, +11.4, +28.2 | +12.3 |
| EURUSD | OOS | 97 | 0.582 | 0.563 (0.169) | 45% 15% 26% 16% 26% | 50, +7.9, -9.2 | -5.0 |
| XAUUSD | IS | 143 | 0.456 | 0.460 (0.095) | 31% 48% 55% 54% 57% | 73, +21.1, +50.7 | +32.1 |
| XAUUSD | OOS | 371 | 0.542 | 0.554 (0.034) | 37% 22% 31% 24% 34% | 186, -35.2, -27.0 | -18.2 |
| NAS100 | IS | 43 | 0.467 | 0.442 (0.115) | 56% 33% 22% 75% 50% | 23, +1.6, +31.3 | +4.6 |
| NAS100 | OOS | 100 | 0.550 | 0.560 (0.178) | 30% 35% 25% 30% 40% | 50, +23.0, +5.8 | +6.4 |
| BTCUSD | IS | 89 | 0.468 | 0.482 (0.162) | 56% 50% 61% 61% 65% | 45, +18.0, +43.7 | +46.6 |
| BTCUSD | OOS | 130 | 0.518 | 0.521 (0.099) | 31% 27% 27% 27% 54% | 65, -29.0, -12.6 | -6.4 |
| POOLED | IS | 322 | 0.452 | 0.455 (0.084) | 37% 54% 53% 53% 58% | 162, +45.3, +160.7 | +115.8 |
| POOLED | OOS | 698 | 0.499 | 0.500 (0.022) | 34% 26% 27% 27% 36% | 350, -111.8, +35.5 | +37.0 |


</details>


<details><summary>gb_all</summary>

## within-fold view of gb_all.json (model=gb, features=all)

| set | period | n | pooled OOF AUC | mean within-fold AUC (sd over folds) | fold win rates | within-fold top half: kept, R, R removed | within-fold bottom fifth removed: R removed |
|---|---|---|---|---|---|---|---|
| EURUSD | IS | 47 | 0.478 | 0.515 (0.230) | 20% 50% 56% 56% 56% | 25, +16.3, +23.2 | +7.2 |
| EURUSD | OOS | 97 | 0.644 | 0.630 (0.113) | 45% 15% 26% 16% 26% | 50, +14.9, -16.2 | -8.8 |
| XAUUSD | IS | 143 | 0.418 | 0.420 (0.115) | 31% 48% 55% 54% 57% | 74, +9.3, +62.5 | +30.8 |
| XAUUSD | OOS | 371 | 0.563 | 0.584 (0.058) | 37% 22% 31% 24% 34% | 186, -35.4, -26.8 | -7.9 |
| NAS100 | IS | 43 | 0.407 | 0.396 (0.204) | 56% 33% 22% 75% 50% | 23, +15.0, +17.9 | +8.6 |
| NAS100 | OOS | 100 | 0.621 | 0.620 (0.125) | 30% 35% 25% 30% 40% | 50, +21.5, +7.3 | -16.0 |
| BTCUSD | IS | 89 | 0.611 | 0.643 (0.137) | 56% 50% 61% 61% 65% | 45, +16.5, +45.2 | +13.6 |
| BTCUSD | OOS | 130 | 0.536 | 0.576 (0.105) | 31% 27% 27% 27% 54% | 65, -22.7, -18.9 | -3.4 |
| POOLED | IS | 322 | 0.485 | 0.495 (0.053) | 37% 54% 53% 53% 58% | 162, +44.8, +161.1 | +94.7 |
| POOLED | OOS | 698 | 0.564 | 0.574 (0.045) | 34% 26% 27% 27% 36% | 350, -43.0, -33.3 | -16.2 |


</details>


## Appendix D: univariate screen and the context-feature bucket tables

<details><summary>univariate.py</summary>

## Univariate AUC of each feature (higher value -> more wins when AUC > 0.5); z = (AUC-0.5)/SE

145 feature x set cells; expected by chance at |z|>=1.5 in both periods with the same sign: about 1.3; at |z|>=1.0: about 7.3

### Cells that pass |z| >= 1.5 in both periods, same side

| set | feature | AUC IS | z IS | AUC OOS | z OOS |
|---|---|---|---|---|---|
| BTCUSD | planned_rr | 0.329 | -2.90 | 0.366 | -2.68 |
| BTCUSD | tp_atr | 0.361 | -2.31 | 0.406 | -1.83 |
| EURUSD | planned_rr | 0.294 | -2.73 | 0.336 | -2.77 |
| POOLED | planned_rr | 0.400 | -3.16 | 0.383 | -5.26 |
| POOLED | tp_atr | 0.423 | -2.42 | 0.442 | -2.49 |

### Cells that pass |z| >= 1.0 in both periods, same side (weaker)

| set | feature | AUC IS | z IS | AUC OOS | z OOS |
|---|---|---|---|---|---|
| EURUSD | tp_atr | 0.391 | -1.32 | 0.430 | -1.08 |
| POOLED | room_pd_atr | 0.456 | -1.39 | 0.469 | -1.32 |
| POOLED | touch_to_sig_h | 0.575 | +2.35 | 0.527 | +1.13 |
| XAUUSD | atr14d_pct | 0.441 | -1.24 | 0.442 | -1.80 |
| XAUUSD | depth | 0.428 | -1.50 | 0.467 | -1.01 |
| XAUUSD | rng14_pct | 0.414 | -1.81 | 0.453 | -1.46 |
| XAUUSD | sig_tod | 0.553 | +1.11 | 0.535 | +1.06 |

### Pooled set, every feature

| feature | AUC IS | z IS | AUC OOS | z OOS | same side |
|---|---|---|---|---|---|
| planned_rr | 0.400 | -3.16 | 0.383 | -5.26 | yes |
| tp_atr | 0.423 | -2.42 | 0.442 | -2.49 | yes |
| touch_to_sig_h | 0.575 | +2.35 | 0.527 | +1.13 | yes |
| room_pd_atr | 0.456 | -1.39 | 0.469 | -1.32 | yes |
| ret5d_dir | 0.537 | +1.14 | 0.517 | +0.71 | yes |
| s_1M | 0.536 | +1.11 | 0.472 | -1.20 | no |
| zone_age_h | 0.468 | -0.99 | 0.520 | +0.85 | no |
| depth | 0.470 | -0.93 | 0.468 | -1.34 | yes |
| s_1H | 0.474 | -0.82 | 0.504 | +0.17 | no |
| weekday | 0.526 | +0.81 | 0.490 | -0.42 | no |
| s_1W | 0.475 | -0.78 | 0.485 | -0.64 | yes |
| dist_atr | 0.525 | +0.76 | 0.543 | +1.79 | yes |
| rng14_pct | 0.476 | -0.75 | 0.445 | -2.36 | yes |
| sig_tod | 0.521 | +0.65 | 0.531 | +1.31 | yes |
| atr14d_pct | 0.483 | -0.53 | 0.458 | -1.80 | yes |
| zone_atr | 0.484 | -0.49 | 0.542 | +1.76 | no |
| long | 0.486 | -0.42 | 0.506 | +0.27 | no |
| drift_abs | 0.513 | +0.40 | 0.482 | -0.74 | no |
| er20 | 0.512 | +0.36 | 0.499 | -0.06 | no |
| s_4H | 0.510 | +0.31 | 0.512 | +0.51 | yes |
| behind_pd_atr | 0.492 | -0.25 | 0.503 | +0.14 | no |
| stop_atr | 0.506 | +0.18 | 0.538 | +1.60 | yes |
| morning | 0.496 | -0.12 | 0.469 | -1.34 | yes |
| drift_atr | 0.504 | +0.11 | 0.505 | +0.21 | yes |
| pd_pos | 0.504 | +0.11 | 0.500 | +0.01 | yes |
| n_with | 0.497 | -0.10 | 0.480 | -0.85 | yes |
| is4h | 0.503 | +0.10 | 0.525 | +1.05 | yes |
| scalp | 0.498 | -0.06 | 0.514 | +0.59 | no |
| s_1D | 0.501 | +0.03 | 0.493 | -0.31 | no |
| n_neutral | 0.501 | +0.02 | 0.496 | -0.17 | no |
| visit | 0.500 | -0.01 | 0.505 | +0.21 | no |

## Bucket tables for the new context features (R after costs; a bucket is flagged when its R a trade sits 0.05R under the base in both periods, n >= 3 each)

### drift_atr

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100.0, -1.0) | 8 | 75 % | +3.29 | +26.3 | 14 | 21 % | -0.47 | -6.6 |  |
| BTCUSD | [-1.0, -0.5) | 11 | 73 % | +0.96 | +10.5 | 12 | 17 % | -0.70 | -8.5 |  |
| BTCUSD | [-0.5, 0.0) | 9 | 33 % | -0.08 | -0.7 | 23 | 39 % | -0.11 | -2.5 |  |
| BTCUSD | [0.0, 0.5) | 17 | 59 % | +0.38 | +6.4 | 23 | 22 % | -0.63 | -14.5 | YES |
| BTCUSD | [0.5, 1.0) | 15 | 73 % | +0.58 | +8.8 | 23 | 52 % | +0.02 | +0.4 |  |
| BTCUSD | [1.0, 2.0) | 15 | 47 % | -0.10 | -1.5 | 21 | 33 % | -0.27 | -5.7 |  |
| BTCUSD | [2.0, 100.0) | 14 | 50 % | +0.85 | +12.0 | 14 | 36 % | -0.31 | -4.3 |  |
| EURUSD | [-100.0, -1.0) | 2 | 50 % | +1.09 | +2.2 | 6 | 0 % | -1.10 | -6.6 |  |
| EURUSD | [-1.0, -0.5) | 2 | 0 % | -1.10 | -2.2 | 8 | 25 % | -0.24 | -1.9 |  |
| EURUSD | [-0.5, 0.0) | 6 | 0 % | -1.10 | -6.6 | 9 | 22 % | -0.33 | -2.9 | YES |
| EURUSD | [0.0, 0.5) | 4 | 50 % | +0.83 | +3.3 | 16 | 44 % | +0.59 | +9.5 |  |
| EURUSD | [0.5, 1.0) | 6 | 50 % | +0.67 | +4.0 | 14 | 21 % | -0.22 | -3.0 | YES |
| EURUSD | [1.0, 2.0) | 18 | 61 % | +1.79 | +32.2 | 29 | 24 % | +0.26 | +7.6 |  |
| EURUSD | [2.0, 100.0) | 9 | 56 % | +0.74 | +6.6 | 15 | 27 % | -0.26 | -3.8 | YES |
| NAS100 | [-100.0, -1.0) | 3 | 100 % | +2.76 | +8.3 | 4 | 25 % | -0.42 | -1.7 |  |
| NAS100 | [-1.0, -0.5) | 3 | 0 % | -1.10 | -3.3 | 4 | 25 % | -0.39 | -1.5 | YES |
| NAS100 | [-0.5, 0.0) | 10 | 70 % | +1.79 | +17.9 | 14 | 14 % | -0.67 | -9.3 |  |
| NAS100 | [0.0, 0.5) | 2 | 0 % | -1.10 | -2.2 | 12 | 42 % | +0.15 | +1.7 |  |
| NAS100 | [0.5, 1.0) | 6 | 17 % | -0.36 | -2.2 | 19 | 16 % | -0.61 | -11.5 | YES |
| NAS100 | [1.0, 2.0) | 12 | 42 % | +0.82 | +9.8 | 28 | 50 % | +1.31 | +36.7 |  |
| NAS100 | [2.0, 100.0) | 7 | 57 % | +0.67 | +4.7 | 19 | 32 % | +0.76 | +14.4 |  |
| XAUUSD | [-100.0, -1.0) | 3 | 0 % | -1.10 | -3.3 | 11 | 9 % | -0.80 | -8.8 | YES |
| XAUUSD | [-1.0, -0.5) | 6 | 67 % | +0.98 | +5.9 | 12 | 50 % | +0.11 | +1.4 |  |
| XAUUSD | [-0.5, 0.0) | 14 | 36 % | -0.24 | -3.4 | 30 | 27 % | -0.18 | -5.5 |  |
| XAUUSD | [0.0, 0.5) | 22 | 55 % | +0.56 | +12.3 | 41 | 39 % | +0.25 | +10.3 |  |
| XAUUSD | [0.5, 1.0) | 21 | 43 % | +0.19 | +3.9 | 54 | 31 % | -0.02 | -0.8 |  |
| XAUUSD | [1.0, 2.0) | 40 | 55 % | +1.02 | +40.7 | 101 | 27 % | -0.30 | -30.8 |  |
| XAUUSD | [2.0, 100.0) | 37 | 49 % | +0.42 | +15.6 | 122 | 29 % | -0.23 | -28.0 | YES |

### er20

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [0.0, 0.15) | 24 | 46 % | +1.01 | +24.1 | 40 | 35 % | -0.29 | -11.6 |  |
| BTCUSD | [0.15, 0.25) | 23 | 52 % | +0.05 | +1.2 | 19 | 47 % | -0.10 | -1.9 |  |
| BTCUSD | [0.25, 0.35) | 16 | 69 % | +0.75 | +12.0 | 19 | 32 % | -0.34 | -6.5 |  |
| BTCUSD | [0.35, 0.5) | 16 | 81 % | +1.44 | +23.0 | 28 | 25 % | -0.54 | -15.3 |  |
| BTCUSD | [0.5, 1.01) | 10 | 50 % | +0.14 | +1.4 | 24 | 29 % | -0.26 | -6.3 |  |
| EURUSD | [0.0, 0.15) | 24 | 58 % | +1.28 | +30.7 | 25 | 24 % | +0.25 | +6.4 |  |
| EURUSD | [0.15, 0.25) | 9 | 11 % | -0.70 | -6.3 | 22 | 36 % | +0.34 | +7.5 |  |
| EURUSD | [0.25, 0.35) | 6 | 67 % | +1.28 | +7.7 | 17 | 24 % | -0.40 | -6.7 |  |
| EURUSD | [0.35, 0.5) | 8 | 38 % | +0.93 | +7.5 | 22 | 14 % | -0.51 | -11.3 |  |
| EURUSD | [0.5, 1.01) | 0 | nan % | +nan | +0.0 | 11 | 36 % | +0.26 | +2.9 |  |
| NAS100 | [0.0, 0.15) | 10 | 40 % | +0.75 | +7.5 | 22 | 45 % | +1.17 | +25.8 |  |
| NAS100 | [0.15, 0.25) | 9 | 56 % | +1.11 | +10.0 | 24 | 38 % | +0.07 | +1.6 |  |
| NAS100 | [0.25, 0.35) | 4 | 100 % | +3.06 | +12.2 | 24 | 25 % | +0.19 | +4.6 |  |
| NAS100 | [0.35, 0.5) | 13 | 38 % | +0.37 | +4.8 | 20 | 25 % | +0.17 | +3.5 | YES |
| NAS100 | [0.5, 1.01) | 7 | 29 % | -0.23 | -1.6 | 10 | 20 % | -0.67 | -6.7 | YES |
| XAUUSD | [0.0, 0.15) | 49 | 49 % | +0.40 | +19.6 | 123 | 27 % | -0.26 | -31.9 | YES |
| XAUUSD | [0.15, 0.25) | 20 | 50 % | +0.56 | +11.2 | 72 | 24 % | -0.42 | -30.0 |  |
| XAUUSD | [0.25, 0.35) | 35 | 60 % | +0.75 | +26.2 | 59 | 32 % | -0.05 | -3.1 |  |
| XAUUSD | [0.35, 0.5) | 13 | 38 % | +0.80 | +10.3 | 77 | 35 % | +0.06 | +5.0 |  |
| XAUUSD | [0.5, 1.01) | 26 | 38 % | +0.18 | +4.6 | 40 | 35 % | -0.06 | -2.2 |  |

### rng14_pct

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-0.01, 0.2) | 17 | 53 % | +0.32 | +5.5 | 27 | 41 % | -0.19 | -5.2 |  |
| BTCUSD | [0.2, 0.4) | 20 | 55 % | +0.59 | +11.8 | 18 | 39 % | -0.22 | -4.0 |  |
| BTCUSD | [0.4, 0.6) | 17 | 65 % | +1.89 | +32.1 | 26 | 27 % | -0.46 | -12.1 |  |
| BTCUSD | [0.6, 0.8) | 18 | 61 % | +0.27 | +4.8 | 28 | 36 % | -0.20 | -5.7 |  |
| BTCUSD | [0.8, 1.01) | 17 | 59 % | +0.44 | +7.5 | 31 | 26 % | -0.47 | -14.6 | YES |
| EURUSD | [-0.01, 0.2) | 17 | 41 % | +0.54 | +9.2 | 26 | 38 % | +0.74 | +19.3 |  |
| EURUSD | [0.2, 0.4) | 3 | 67 % | +1.11 | +3.3 | 8 | 38 % | +0.62 | +5.0 |  |
| EURUSD | [0.4, 0.6) | 4 | 0 % | -1.10 | -4.4 | 23 | 17 % | -0.56 | -12.9 | YES |
| EURUSD | [0.6, 0.8) | 10 | 80 % | +2.54 | +25.4 | 16 | 25 % | -0.19 | -3.1 |  |
| EURUSD | [0.8, 1.01) | 13 | 38 % | +0.46 | +5.9 | 24 | 17 % | -0.40 | -9.5 | YES |
| NAS100 | [-0.01, 0.2) | 10 | 50 % | +0.57 | +5.7 | 28 | 36 % | +0.54 | +15.2 |  |
| NAS100 | [0.2, 0.4) | 7 | 57 % | +1.52 | +10.6 | 16 | 31 % | +0.70 | +11.2 |  |
| NAS100 | [0.4, 0.6) | 11 | 45 % | +1.08 | +11.9 | 20 | 35 % | -0.06 | -1.1 |  |
| NAS100 | [0.6, 0.8) | 8 | 38 % | +0.33 | +2.7 | 17 | 18 % | +0.19 | +3.3 | YES |
| NAS100 | [0.8, 1.01) | 7 | 43 % | +0.30 | +2.1 | 19 | 37 % | +0.01 | +0.2 | YES |
| XAUUSD | [-0.01, 0.2) | 16 | 62 % | +0.83 | +13.3 | 74 | 39 % | -0.01 | -0.8 |  |
| XAUUSD | [0.2, 0.4) | 16 | 50 % | +0.74 | +11.9 | 83 | 27 % | -0.32 | -26.9 |  |
| XAUUSD | [0.4, 0.6) | 37 | 51 % | +0.50 | +18.5 | 70 | 27 % | -0.25 | -17.8 |  |
| XAUUSD | [0.6, 0.8) | 37 | 51 % | +0.75 | +27.9 | 72 | 31 % | +0.02 | +1.7 |  |
| XAUUSD | [0.8, 1.01) | 37 | 38 % | +0.01 | +0.3 | 72 | 25 % | -0.26 | -18.4 | YES |

### room_pd_atr

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100.0, 0.0) | 21 | 67 % | +1.15 | +24.1 | 39 | 33 % | -0.34 | -13.3 |  |
| BTCUSD | [0.0, 0.5) | 12 | 50 % | +0.23 | +2.7 | 10 | 30 % | -0.25 | -2.5 |  |
| BTCUSD | [0.5, 1.0) | 8 | 38 % | -0.14 | -1.1 | 16 | 38 % | -0.33 | -5.3 |  |
| BTCUSD | [1.0, 2.0) | 21 | 67 % | +0.57 | +12.0 | 29 | 17 % | -0.63 | -18.3 | YES |
| BTCUSD | [2.0, 4.0) | 19 | 47 % | -0.08 | -1.5 | 25 | 44 % | -0.01 | -0.4 |  |
| BTCUSD | [4.0, 100.0) | 8 | 75 % | +3.18 | +25.5 | 11 | 45 % | -0.17 | -1.8 |  |
| EURUSD | [-100.0, 0.0) | 17 | 65 % | +1.18 | +20.1 | 21 | 14 % | -0.38 | -8.0 |  |
| EURUSD | [0.0, 0.5) | 2 | 50 % | +0.45 | +0.9 | 14 | 43 % | +0.71 | +9.9 |  |
| EURUSD | [0.5, 1.0) | 2 | 50 % | +0.50 | +1.0 | 5 | 80 % | +3.65 | +18.2 |  |
| EURUSD | [1.0, 2.0) | 1 | 100 % | +2.51 | +2.5 | 18 | 22 % | -0.40 | -7.3 |  |
| EURUSD | [2.0, 4.0) | 15 | 27 % | +0.07 | +1.0 | 25 | 20 % | -0.31 | -7.6 | YES |
| EURUSD | [4.0, 100.0) | 10 | 40 % | +1.40 | +14.0 | 14 | 21 % | -0.46 | -6.5 |  |
| NAS100 | [-100.0, 0.0) | 9 | 33 % | -0.12 | -1.1 | 18 | 56 % | +0.95 | +17.1 |  |
| NAS100 | [0.0, 0.5) | 4 | 0 % | -1.10 | -4.4 | 10 | 20 % | -0.45 | -4.5 | YES |
| NAS100 | [0.5, 1.0) | 1 | 0 % | -1.10 | -1.1 | 8 | 50 % | +0.99 | +7.9 |  |
| NAS100 | [1.0, 2.0) | 13 | 62 % | +1.11 | +14.5 | 24 | 17 % | -0.66 | -15.8 |  |
| NAS100 | [2.0, 4.0) | 11 | 73 % | +1.98 | +21.8 | 22 | 32 % | +0.03 | +0.7 |  |
| NAS100 | [4.0, 100.0) | 5 | 20 % | +0.65 | +3.2 | 18 | 28 % | +1.30 | +23.5 |  |
| XAUUSD | [-100.0, 0.0) | 84 | 55 % | +0.51 | +42.4 | 184 | 29 % | -0.31 | -56.9 |  |
| XAUUSD | [0.0, 0.5) | 16 | 31 % | -0.18 | -2.9 | 33 | 27 % | -0.34 | -11.2 | YES |
| XAUUSD | [0.5, 1.0) | 5 | 80 % | +1.17 | +5.8 | 33 | 48 % | +0.44 | +14.6 |  |
| XAUUSD | [1.0, 2.0) | 12 | 42 % | -0.00 | -0.0 | 57 | 30 % | -0.09 | -5.4 |  |
| XAUUSD | [2.0, 4.0) | 19 | 42 % | +0.90 | +17.2 | 48 | 25 % | +0.03 | +1.3 |  |
| XAUUSD | [4.0, 100.0) | 7 | 29 % | +1.32 | +9.2 | 16 | 19 % | -0.29 | -4.6 |  |

### pd_pos

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100.0, 0.0) | 8 | 62 % | +1.63 | +13.0 | 18 | 50 % | +0.03 | +0.5 |  |
| BTCUSD | [0.0, 0.25) | 12 | 50 % | -0.13 | -1.6 | 20 | 40 % | -0.20 | -3.9 |  |
| BTCUSD | [0.25, 0.5) | 7 | 57 % | +0.14 | +1.0 | 19 | 26 % | -0.34 | -6.4 |  |
| BTCUSD | [0.5, 0.75) | 25 | 64 % | +1.25 | +31.4 | 27 | 37 % | -0.26 | -7.1 |  |
| BTCUSD | [0.75, 1.0) | 22 | 50 % | +0.33 | +7.2 | 24 | 29 % | -0.41 | -9.9 | YES |
| BTCUSD | [1.0, 100.0) | 15 | 67 % | +0.71 | +10.7 | 22 | 18 % | -0.68 | -14.9 |  |
| EURUSD | [-100.0, 0.0) | 7 | 71 % | +1.31 | +9.1 | 14 | 14 % | -0.29 | -4.0 |  |
| EURUSD | [0.0, 0.25) | 5 | 60 % | +2.10 | +10.5 | 19 | 37 % | +0.09 | +1.8 |  |
| EURUSD | [0.25, 0.5) | 15 | 20 % | -0.25 | -3.7 | 24 | 8 % | -0.82 | -19.6 | YES |
| EURUSD | [0.5, 0.75) | 8 | 50 % | +1.46 | +11.7 | 21 | 38 % | +0.24 | +5.0 |  |
| EURUSD | [0.75, 1.0) | 1 | 100 % | +2.10 | +2.1 | 11 | 45 % | +1.88 | +20.7 |  |
| EURUSD | [1.0, 100.0) | 11 | 55 % | +0.90 | +9.9 | 8 | 12 % | -0.63 | -5.1 |  |
| NAS100 | [-100.0, 0.0) | 3 | 33 % | +0.04 | +0.1 | 7 | 57 % | +0.42 | +2.9 |  |
| NAS100 | [0.0, 0.25) | 1 | 0 % | -1.10 | -1.1 | 19 | 21 % | +0.03 | +0.5 |  |
| NAS100 | [0.25, 0.5) | 8 | 50 % | +1.51 | +12.1 | 18 | 39 % | +1.52 | +27.4 |  |
| NAS100 | [0.5, 0.75) | 9 | 89 % | +2.70 | +24.3 | 15 | 27 % | -0.28 | -4.1 |  |
| NAS100 | [0.75, 1.0) | 16 | 31 % | -0.08 | -1.4 | 27 | 22 % | -0.39 | -10.6 | YES |
| NAS100 | [1.0, 100.0) | 6 | 33 % | -0.20 | -1.2 | 14 | 50 % | +0.90 | +12.7 |  |
| XAUUSD | [-100.0, 0.0) | 20 | 60 % | +0.64 | +12.7 | 75 | 29 % | -0.34 | -25.5 |  |
| XAUUSD | [0.0, 0.25) | 9 | 22 % | -0.46 | -4.2 | 60 | 30 % | -0.21 | -12.9 |  |
| XAUUSD | [0.25, 0.5) | 9 | 56 % | +1.91 | +17.2 | 39 | 18 % | -0.28 | -10.9 |  |
| XAUUSD | [0.5, 0.75) | 19 | 37 % | +0.56 | +10.6 | 47 | 30 % | +0.06 | +2.7 |  |
| XAUUSD | [0.75, 1.0) | 21 | 48 % | +0.28 | +5.9 | 41 | 44 % | +0.38 | +15.7 |  |
| XAUUSD | [1.0, 100.0) | 65 | 52 % | +0.46 | +29.6 | 109 | 28 % | -0.29 | -31.4 |  |

### behind_pd_atr

| market | bucket | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R | worse in both |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | [-100, 0) | 2 | 50 % | -0.22 | -0.4 | 1 | 0 % | -1.10 | -1.1 |  |
| BTCUSD | [0, 1) | 0 | nan % | +nan | +0.0 | 1 | 0 % | -1.10 | -1.1 |  |
| BTCUSD | [1, 2) | 4 | 75 % | +0.12 | +0.5 | 5 | 40 % | +0.06 | +0.3 |  |
| BTCUSD | [2, 4) | 27 | 59 % | +1.19 | +32.2 | 49 | 35 % | -0.22 | -10.7 |  |
| BTCUSD | [4, 8) | 39 | 56 % | +0.31 | +12.3 | 67 | 33 % | -0.37 | -24.6 |  |
| BTCUSD | [8, 100) | 17 | 59 % | +1.01 | +17.2 | 7 | 29 % | -0.64 | -4.5 |  |
| EURUSD | [-100, 0) | 1 | 0 % | -1.10 | -1.1 | 1 | 0 % | -1.10 | -1.1 |  |
| EURUSD | [0, 1) | 0 | nan % | +nan | +0.0 | 1 | 0 % | -1.10 | -1.1 |  |
| EURUSD | [1, 2) | 6 | 33 % | +1.50 | +9.0 | 8 | 0 % | -1.10 | -8.8 |  |
| EURUSD | [2, 4) | 15 | 53 % | +1.07 | +16.0 | 27 | 37 % | +0.59 | +15.8 |  |
| EURUSD | [4, 8) | 22 | 41 % | +0.42 | +9.3 | 46 | 26 % | -0.08 | -3.5 | YES |
| EURUSD | [8, 100) | 3 | 100 % | +2.12 | +6.4 | 14 | 21 % | -0.18 | -2.6 |  |
| NAS100 | [-100, 0) | 0 | nan % | +nan | +0.0 | 3 | 33 % | -0.50 | -1.5 |  |
| NAS100 | [0, 1) | 0 | nan % | +nan | +0.0 | 6 | 17 % | +0.52 | +3.1 |  |
| NAS100 | [1, 2) | 1 | 0 % | -1.10 | -1.1 | 6 | 0 % | -1.17 | -7.0 |  |
| NAS100 | [2, 4) | 11 | 64 % | +1.81 | +19.9 | 19 | 37 % | +0.76 | +14.4 |  |
| NAS100 | [4, 8) | 22 | 36 % | +0.39 | +8.6 | 52 | 33 % | +0.18 | +9.4 | YES |
| NAS100 | [8, 100) | 9 | 56 % | +0.62 | +5.5 | 14 | 43 % | +0.74 | +10.4 |  |
| XAUUSD | [-100, 0) | 1 | 0 % | -0.10 | -0.1 | 0 | nan % | +nan | +0.0 |  |
| XAUUSD | [0, 1) | 0 | nan % | +nan | +0.0 | 1 | 100 % | +3.83 | +3.8 |  |
| XAUUSD | [1, 2) | 4 | 50 % | +0.85 | +3.4 | 8 | 0 % | -1.10 | -8.8 |  |
| XAUUSD | [2, 4) | 21 | 48 % | +0.70 | +14.8 | 73 | 29 % | -0.02 | -1.8 |  |
| XAUUSD | [4, 8) | 84 | 54 % | +0.62 | +51.8 | 212 | 32 % | -0.15 | -31.2 |  |
| XAUUSD | [8, 100) | 33 | 39 % | +0.06 | +1.9 | 77 | 27 % | -0.32 | -24.3 | YES |



</details>


## Appendix E: planned R:R bands and the stake simulation (rr_bands.py)

<details><summary>rr_bands.py</summary>

## Planned R:R bands (R after costs)

| market | band | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | [0.0, 1.0) | 0 | nan % | +nan | +0.0 | 0 | nan % | +nan | +0.0 |
| EURUSD | [1.0, 1.5) | 12 | 67 % | +0.92 | +11.1 | 34 | 41 % | +0.12 | +4.2 |
| EURUSD | [1.5, 2.0) | 9 | 67 % | +1.30 | +11.7 | 16 | 25 % | -0.23 | -3.7 |
| EURUSD | [2.0, 3.0) | 11 | 36 % | +0.50 | +5.5 | 20 | 15 % | -0.44 | -8.8 |
| EURUSD | [3.0, 4.0) | 9 | 33 % | +0.84 | +7.6 | 13 | 23 % | +0.42 | +5.4 |
| EURUSD | [4.0, 6.0) | 3 | 0 % | -1.10 | -3.3 | 11 | 0 % | -0.92 | -10.1 |
| EURUSD | [6.0, 100.0) | 3 | 33 % | +2.32 | +7.0 | 3 | 33 % | +3.92 | +11.8 |
| XAUUSD | [0.0, 1.0) | 7 | 57 % | -0.06 | -0.4 | 16 | 31 % | -0.49 | -7.9 |
| XAUUSD | [1.0, 1.5) | 20 | 50 % | -0.01 | -0.2 | 51 | 49 % | -0.04 | -1.8 |
| XAUUSD | [1.5, 2.0) | 11 | 36 % | -0.11 | -1.2 | 23 | 39 % | -0.05 | -1.1 |
| XAUUSD | [2.0, 3.0) | 81 | 51 % | +0.44 | +35.7 | 224 | 27 % | -0.29 | -64.5 |
| XAUUSD | [3.0, 4.0) | 7 | 43 % | +0.79 | +5.6 | 21 | 19 % | +0.03 | +0.6 |
| XAUUSD | [4.0, 6.0) | 9 | 78 % | +3.41 | +30.7 | 19 | 26 % | +0.63 | +12.1 |
| XAUUSD | [6.0, 100.0) | 8 | 12 % | +0.21 | +1.7 | 17 | 12 % | +0.02 | +0.4 |
| NAS100 | [0.0, 1.0) | 5 | 40 % | -0.10 | -0.5 | 9 | 44 % | +0.05 | +0.5 |
| NAS100 | [1.0, 1.5) | 12 | 42 % | +0.03 | +0.4 | 28 | 36 % | -0.14 | -3.8 |
| NAS100 | [1.5, 2.0) | 8 | 62 % | +1.11 | +8.8 | 19 | 26 % | -0.18 | -3.4 |
| NAS100 | [2.0, 3.0) | 8 | 50 % | +1.14 | +9.1 | 15 | 33 % | +0.15 | +2.2 |
| NAS100 | [3.0, 4.0) | 4 | 75 % | +3.22 | +12.9 | 10 | 20 % | -0.24 | -2.4 |
| NAS100 | [4.0, 6.0) | 3 | 33 % | +1.81 | +5.4 | 10 | 50 % | +2.86 | +28.6 |
| NAS100 | [6.0, 100.0) | 3 | 0 % | -1.10 | -3.3 | 9 | 11 % | +0.80 | +7.2 |
| BTCUSD | [0.0, 1.0) | 20 | 90 % | +0.43 | +8.7 | 36 | 44 % | -0.34 | -12.1 |
| BTCUSD | [1.0, 1.5) | 24 | 62 % | +0.26 | +6.3 | 32 | 38 % | -0.29 | -9.3 |
| BTCUSD | [1.5, 2.0) | 11 | 18 % | -0.58 | -6.4 | 21 | 38 % | -0.06 | -1.4 |
| BTCUSD | [2.0, 3.0) | 28 | 50 % | +0.63 | +17.6 | 32 | 22 % | -0.31 | -9.9 |
| BTCUSD | [3.0, 4.0) | 3 | 33 % | +0.41 | +1.2 | 1 | 0 % | -1.10 | -1.1 |
| BTCUSD | [4.0, 6.0) | 0 | nan % | +nan | +0.0 | 4 | 0 % | -1.10 | -4.4 |
| BTCUSD | [6.0, 100.0) | 3 | 67 % | +11.45 | +34.4 | 4 | 0 % | -0.85 | -3.4 |
| POOLED | [0.0, 1.0) | 32 | 75 % | +0.24 | +7.8 | 61 | 41 % | -0.32 | -19.5 |
| POOLED | [1.0, 1.5) | 68 | 56 % | +0.26 | +17.6 | 145 | 42 % | -0.07 | -10.9 |
| POOLED | [1.5, 2.0) | 39 | 44 % | +0.33 | +12.9 | 79 | 33 % | -0.12 | -9.6 |
| POOLED | [2.0, 3.0) | 128 | 49 % | +0.53 | +67.9 | 291 | 26 % | -0.28 | -80.9 |
| POOLED | [3.0, 4.0) | 23 | 43 % | +1.18 | +27.2 | 45 | 20 % | +0.05 | +2.5 |
| POOLED | [4.0, 6.0) | 15 | 53 % | +2.19 | +32.8 | 44 | 23 % | +0.59 | +26.1 |
| POOLED | [6.0, 100.0) | 17 | 24 % | +2.34 | +39.7 | 33 | 12 % | +0.48 | +15.9 |

### Three bands

| market | band | IS n | IS win | IS R/tr | IS R | OOS n | OOS win | OOS R/tr | OOS R |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | <1.5 | 12 | 67 % | +0.92 | +11.1 | 34 | 41 % | +0.12 | +4.2 |
| EURUSD | 1.5-3 | 20 | 50 % | +0.86 | +17.2 | 36 | 19 % | -0.35 | -12.5 |
| EURUSD | >=3 | 15 | 27 % | +0.75 | +11.2 | 27 | 15 % | +0.26 | +7.1 |
| XAUUSD | <1.5 | 27 | 52 % | -0.02 | -0.6 | 67 | 45 % | -0.14 | -9.7 |
| XAUUSD | 1.5-3 | 92 | 49 % | +0.37 | +34.5 | 247 | 28 % | -0.27 | -65.6 |
| XAUUSD | >=3 | 24 | 46 % | +1.58 | +37.9 | 57 | 19 % | +0.23 | +13.0 |
| NAS100 | <1.5 | 17 | 41 % | -0.01 | -0.1 | 37 | 38 % | -0.09 | -3.4 |
| NAS100 | 1.5-3 | 16 | 56 % | +1.12 | +18.0 | 34 | 29 % | -0.03 | -1.2 |
| NAS100 | >=3 | 10 | 40 % | +1.50 | +15.0 | 29 | 28 % | +1.15 | +33.3 |
| BTCUSD | <1.5 | 44 | 75 % | +0.34 | +15.0 | 68 | 41 % | -0.32 | -21.5 |
| BTCUSD | 1.5-3 | 39 | 41 % | +0.29 | +11.1 | 53 | 28 % | -0.21 | -11.3 |
| BTCUSD | >=3 | 6 | 50 % | +5.93 | +35.6 | 9 | 0 % | -0.99 | -8.9 |
| POOLED | <1.5 | 100 | 62 % | +0.25 | +25.4 | 206 | 42 % | -0.15 | -30.4 |
| POOLED | 1.5-3 | 167 | 48 % | +0.48 | +80.8 | 370 | 27 % | -0.24 | -90.5 |
| POOLED | >=3 | 55 | 40 % | +1.81 | +99.7 | 122 | 19 % | +0.37 | +44.5 |

## Stake by planned R:R at the ledger level (the trade's R times the multiplier; dip = largest fall of the cumulative R)

| market | rule | IS trades touched | IS R | IS dip | OOS trades touched | OOS R | OOS dip |
|---|---|---|---|---|---|---|---|
| EURUSD | base | 0 | +39.5 | -5.5 | 0 | -1.2 | -24.6 |
| EURUSD | x2 at R:R >= 3 | 15 | +50.8 | -8.8 | 27 | +5.8 | -34.0 |
| EURUSD | x1.5 at R:R >= 3 | 15 | +45.2 | -7.1 | 27 | +2.3 | -29.3 |
| EURUSD | x2 at R:R >= 4 | 6 | +43.2 | -5.5 | 14 | +0.4 | -34.8 |
| EURUSD | x0.5 under R:R 1.5 | 12 | +34.0 | -4.4 | 34 | -3.3 | -21.4 |
| EURUSD | x2 at >= 3 and x0.5 under 1.5 | 27 | +45.2 | -7.7 | 61 | +3.7 | -32.8 |
| EURUSD | skip under R:R 3 (min_rr 3) | 32 | +11.2 | -3.4 | 70 | +7.1 | -12.7 |
| XAUUSD | base | 0 | +71.8 | -9.0 | 0 | -62.2 | -83.2 |
| XAUUSD | x2 at R:R >= 3 | 24 | +109.7 | -14.5 | 57 | -49.2 | -84.3 |
| XAUUSD | x1.5 at R:R >= 3 | 24 | +90.8 | -11.8 | 57 | -55.7 | -83.6 |
| XAUUSD | x2 at R:R >= 4 | 17 | +104.2 | -11.2 | 36 | -49.7 | -80.1 |
| XAUUSD | x0.5 under R:R 1.5 | 27 | +72.1 | -8.9 | 67 | -57.4 | -76.4 |
| XAUUSD | x2 at >= 3 and x0.5 under 1.5 | 51 | +110.0 | -14.4 | 124 | -44.3 | -79.8 |
| XAUUSD | skip under R:R 3 (min_rr 3) | 119 | +37.9 | -5.5 | 314 | +13.0 | -14.6 |
| NAS100 | base | 0 | +32.9 | -5.8 | 0 | +28.8 | -11.8 |
| NAS100 | x2 at R:R >= 3 | 10 | +47.9 | -6.9 | 29 | +62.1 | -18.6 |
| NAS100 | x1.5 at R:R >= 3 | 10 | +40.4 | -6.4 | 29 | +45.4 | -14.8 |
| NAS100 | x2 at R:R >= 4 | 6 | +35.0 | -6.9 | 19 | +64.5 | -15.3 |
| NAS100 | x0.5 under R:R 1.5 | 17 | +32.9 | -4.0 | 37 | +30.5 | -9.7 |
| NAS100 | x2 at >= 3 and x0.5 under 1.5 | 27 | +48.0 | -5.1 | 66 | +63.8 | -16.6 |
| NAS100 | skip under R:R 3 (min_rr 3) | 33 | +15.0 | -2.2 | 71 | +33.3 | -7.7 |
| BTCUSD | base | 0 | +61.7 | -4.9 | 0 | -41.6 | -48.7 |
| BTCUSD | x2 at R:R >= 3 | 6 | +97.3 | -6.0 | 9 | -50.5 | -55.4 |
| BTCUSD | x1.5 at R:R >= 3 | 6 | +79.5 | -5.4 | 9 | -46.1 | -52.1 |
| BTCUSD | x2 at R:R >= 4 | 3 | +96.1 | -4.9 | 8 | -49.4 | -54.3 |
| BTCUSD | x0.5 under R:R 1.5 | 44 | +54.2 | -6.8 | 68 | -30.9 | -37.9 |
| BTCUSD | x2 at >= 3 and x0.5 under 1.5 | 50 | +89.8 | -8.1 | 77 | -39.8 | -44.6 |
| BTCUSD | skip under R:R 3 (min_rr 3) | 83 | +35.6 | -3.3 | 121 | -8.9 | -8.9 |
| POOLED | base | 0 | +206.0 | -9.1 | 0 | -76.3 | -132.9 |
| POOLED | x2 at R:R >= 3 | 55 | +305.7 | -14.6 | 122 | -31.8 | -121.3 |
| POOLED | x1.5 at R:R >= 3 | 55 | +255.8 | -11.8 | 122 | -54.0 | -126.2 |
| POOLED | x2 at R:R >= 4 | 32 | +278.5 | -11.5 | 77 | -34.2 | -117.6 |
| POOLED | x0.5 under R:R 1.5 | 100 | +193.3 | -8.0 | 206 | -61.1 | -110.4 |
| POOLED | x2 at >= 3 and x0.5 under 1.5 | 155 | +293.0 | -13.5 | 328 | -16.6 | -102.2 |
| POOLED | skip under R:R 3 (min_rr 3) | 267 | +99.7 | -6.7 | 576 | +44.5 | -18.2 |

### Per year, x2 at R:R >= 3: extra R against the base (sum of rc over the doubled trades)

extra R:
market  BTCUSD  EURUSD  NAS100  XAUUSD
year                                  
2017       NaN    11.9    -2.6    -4.2
2018       NaN    -3.3     NaN    -6.6
2019       NaN    -2.2    11.4     8.4
2020       NaN     5.1    -6.6    -3.4
2021      -3.3    -5.6    14.0    -1.1
2022      -3.4    -5.6     2.9     8.2
2023      -2.2     6.8    14.2    11.8
2024      -2.2     2.3    -3.3    15.0
2025       2.3     3.7     9.6     1.5
2026      35.5     5.2     8.7    21.5

trades doubled:
market  BTCUSD  EURUSD  NAS100  XAUUSD
year                                  
2017       NaN     2.0     2.0     9.0
2018       NaN     3.0     NaN     6.0
2019       NaN     2.0     5.0    10.0
2020       NaN     3.0     6.0     4.0
2021       3.0     6.0    10.0     8.0
2022       4.0     6.0     4.0    10.0
2023       2.0     5.0     2.0    10.0
2024       2.0     8.0     3.0    11.0
2025       2.0     6.0     4.0     8.0
2026       2.0     1.0     3.0     5.0

years helped / hurt per market: {'EURUSD': (6, 4), 'XAUUSD': (6, 4), 'NAS100': (6, 3), 'BTCUSD': (2, 4)}

### Where the >= 3 R:R targets come from

               size  mean    sum
period poi_tf                   
IS     1H        46  2.02  92.91
       4H         9  0.76   6.82
OOS    1H       108  0.12  12.90
       4H        14  2.26  31.65
/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/metalabel/rr_bands.py:57: DeprecationWarning: DataFrameGroupBy.apply operated on the grouping columns. This behavior is deprecated, and in a future version of pandas the grouping columns will be excluded from the operation. Either pass `include_groups=False` to exclude the groupings or explicitly select the grouping columns after groupby to silence this warning.
  print(T[T.planned_rr >= 3].groupby(["period"]).apply(lambda d: d.tp_source.str.split(" ").str[0:3].str.join(" ").value_counts().head(6).to_dict()).to_string())
period
IS     {'1H origin high': 30, '1H origin low': 9, '4H...
OOS    {'1H origin high': 49, '1H origin low': 43, '4...


</details>
