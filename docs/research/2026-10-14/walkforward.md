# Probability of backtest overfitting (CSCV) and walk-forward on the variant matrix

14 October 2026. Angle: how far the 2024-2026 in-sample window can be trusted for choosing rules, per market.
Read-only on the repository. Scripts and outputs: `research/walkforward/` (paths at the end). Companion:
`research/methodology.md` sections A1 (CSCV) and A2 (walk-forward); the pilot `research/cscv.py` ran 24-28 variants
with S = 10; this is the full run.

## 0. The answer in one paragraph

Four grids of 116-220 distinct variants per market were rebuilt from every provenance-backed backtest on the live data
directory over 2024-01..2026-09 (0.10R costs, 16 time slices, trades crossing a slice edge purged). Picking the
variant with the highest in-sample sum R is a coin flip or worse on **EURUSD** (PBO 0.58, the pick lands below the
out-of-sample median in 58 % of the 12,870 splits, loses money in 21 %, keeps 28 % of its in-sample sum; the
anchored walk-forward keeps 14 % and is positive in 1 of 4 half-years) and on **NAS100** (PBO 0.73, loses in 43 %,
keeps 7 %; walk-forward positive 2 of 4). **Gold** passes both gates by sum R (PBO 0.22, loses in 1 %, keeps 60 %;
walk-forward efficiency 0.84, 4 of 4 positive) but not by mean R per trade (PBO 0.58) and not in its own
neighbourhood (PBO 0.74 among the 23 variants within 3 settings of the live profile), and its whole grid loses in
2017-2023: the ranking is stable inside the gold bull regime, which is not the same as an edge that carries.
**BTC** is borderline (PBO 0.45 at S = 16, 0.53 at S = 12; anchored walk-forward 0.79 and 4 of 4, rolling 0.36;
+38 of its +50R out-of-sample came in 2026-H1 when 99 % of all variants made money). The live profiles were not the
in-sample peaks (full-window rank 7/220, 16/131, 13/116, 19/161; never the in-sample best in any split), which is
why they held in every half-year of the window; that is not evidence of robustness, because they were chosen on the
whole window, and the 2017-2023 ratios stay what they were (EURUSD -0.02, gold -0.33, NAS100 +0.38, BTC -0.46).
Practical rule: nothing is adopted on EURUSD or NAS100 from 2024-2026 evidence alone; on gold and BTC a candidate has
to pass the overfit screen below (`candidate_check.py`), carry a haircut of 0.75 / 0.5 on its in-sample gain, beat
one standard error of the live total after the haircut, not lose on 2017-2023, and then show 20 forward trades.

## 1. Data: the grids

Source: every `*.provenance.json` in the scratchpad (1,700 files, `inventory.py`). Kept per market: the same symbol,
the live research ledger's data directory (`fixed` for EURUSD/XAUUSD/NAS100, `btc_data` for BTC), a run period
covering the window (start <= window start, end >= 2026-09-24), the ledger present. Window 2024-01-01..2026-09-25
(BTC 2024-02-01..2026-09-25: 147 of its runs start 2024-02-01; the 2024-01-01 runs were clipped, see the warm-up
check in section 7). Excluded: runs on other data directories (EURUSD `data/histdata_1m` 73, `hd_full` 3,
`livelike` 6, `fixed1m` 4; gold `data/histdata_1m` 38, `livelike` 4; NAS100 `more_data` 10, `fixed1m` 1; BTC
`btc_old` 3, `research/pipeline/*` 2), shorter periods (the 2026-only `q4_r26_*` runs: 108 BTC, 78 EURUSD, 51 NAS100,
59 gold), other symbols, and the 1,217 root ledgers without a provenance file (the derived `ev_*` ledgers: 802 of them
span the window but their period and data cannot be verified, so they are not in the grid). Ledgers with identical
trade sets in the window were collapsed to one variant (32 / 20 / 16 / 31 duplicates; the `wt_*` worktree copies and
the re-runs of the live profile among them). The cost of 0.10R a trade was taken off every trade; S = 16 slices of
62 days (BTC 60); a trade whose `closed_at` falls past the end of the slice it opened in was dropped (purge: 1.1 %,
0.3 %, 2.6 %, 0.6 % of the trades). Variants with fewer than 10 trades were left out of the statistics (2 / 2 / 1 / 0;
leaving them in changes nothing, Table 3).

The grids are not knob neighbourhoods: 84-184 variants per market differ from the live profile in more than 10
settings (the older `q4_*` candidate families: other bias rules, BOS/BMS confirmations, other targets), 23-28 sit
within 3 settings (the `aca`/`oct14` batches). Both views are reported: the full grid is the set of trials actually
run, the near-live sub-grid is where the next knob change comes from.

## 2. CSCV: probability of backtest overfitting (Table 2, sensitivities Table 3)

Method (Bailey, Borwein, Lopez de Prado, Zhu 2017): the 16 x N matrix of sum R after costs is split into every
symmetric 8/8 combination (12,870); in each split the in-sample (IS) best variant is found (ties: fewest setting
changes from the live profile), its out-of-sample (OOS) rank among the N variants gives omega = rank/(N+1) and the
logit; PBO is the share of splits with the IS-best below the OOS median. Beside it: Prob[OOS sum R of the IS-best
<= 0], the median OOS/IS ratio of the IS-best (the haircut), the Spearman rank correlation between the IS and OOS
columns (median over 600 splits), and the live profile's own OOS rank distribution.

| market | N | PBO | P(IS-best loses OOS) | OOS/IS of the IS-best | Spearman IS/OOS | IS-best: IS R -> OOS R (grid OOS median) | gate PBO <= 0.5 |
|---|---|---|---|---|---|---|---|
| EURUSD | 218 | **0.58** | 0.21 | 0.28 | 0.34 | +30.8 -> +8.7 (+10.1) | FAIL |
| XAUUSD | 129 | 0.22 | 0.01 | 0.60 | 0.66 | +49.4 -> +29.6 (+24.7) | pass |
| NAS100 | 115 | **0.73** | 0.43 | 0.07 | 0.20 | +27.7 -> +2.1 (+9.4) | FAIL |
| BTCUSD | 161 | 0.45 | 0.15 | 0.51 | 0.38 | +50.2 -> +20.3 (+24.7) | pass (0.53 at S = 12, 0.36 at S = 8) |

Reading. On EURUSD and NAS100 the IS-best does worse out of sample than the median variant of its own grid
(+8.7 against +10.1; +2.1 against +9.4): the in-sample ranking carries no information about the next period there,
and a NAS100 winner loses money out of sample in 43 % of the splits. Gold's ranking is informative (Spearman 0.66),
BTC's weakly (0.38). The degradation slope (OLS of the IS-best's OOS sum on its IS sum over the splits) is -0.78 to
-0.86 on all four; it is mostly an artefact here (for a variant that wins most splits OOS = total - IS exactly, slope
-1), so it is reported in `cscv_results.csv` but not read.

What changes the picture (Table 3):

- Metric: with mean R per trade instead of sum R, gold's PBO rises to 0.58 and NAS100's falls to 0.31, BTC's to 0.21.
  Gold's sum-R winners are the many-trade variants (g25, gz: 122-170 trades), whose edge per trade is ordinary but
  whose trade count is stable; by mean R the picks become few-trade variants and gold is as overfit as the others.
  The rule as practised (sum R) is the right one for gold and the wrong one for NAS100.
- Sub-grids by provenance: the old `q4_*` families alone (root): EURUSD 0.56, gold 0.10, NAS100 0.78, BTC 0.22; the
  12-14 October batches (`aca`, `adopt`, `oct14*`, 30-43 variants): 0.52, 0.65, 0.61, 0.91; within 3 settings of the
  live profile (23-28 variants): **0.44, 0.74, 0.59, 0.76**; the 14 October knob grid (`oct14b`, 4-11 variants, coarse):
  0.82, 0.27, 0.43, 0.81. The knob neighbourhood of the live profile, which is where every recent proposal comes
  from, has PBO at or above 0.5 on gold, NAS100 and BTC: the best small modification of the live profile is below the
  OOS median more often than not. The low full-grid PBO of gold and BTC comes from the old families being clearly
  worse than the recent ones (easy to beat OOS), not from the knob grid being decidable.
- Slices: S = 8 and 12 give 0.56-0.73 (NAS100), 0.36-0.53 (BTC), stable elsewhere.

The live profiles in the CSCV: median OOS relative rank 0.93 (EURUSD), 0.85, 0.79, 0.81; above the OOS median in
92-100 % of the splits; the IS-best in 0 % of the splits; and better than the IS-best out of sample in 98 %, 80 %,
92 %, 74 % of the splits. These numbers describe how the live profiles were chosen (a tempered choice, not the
peak); they are not evidence that the profiles hold in the future, because every split's OOS half is inside the window
they were chosen on.

## 3. Walk-forward with the selection rule frozen (Tables 4-6)

Rule: the variant with the highest sum R after costs in the IS window (ties: fewest setting changes). Anchored: IS
from the window start to 2024-12 / 2025-06 / 2025-12 / 2026-06, OOS the next half-year (2026-Q3 to 24 September).
Rolling: IS the 18 months before the OOS window (the first two steps coincide with the anchored ones). Trades
crossing the IS/OOS edge are purged. WFE (Pardo) = OOS R per month of the picks, pooled over the four steps, over
their IS R per month; the per-trade ratio beside it.

| market | mode | picks (OOS rank of N) | OOS R per step | WFE month (trade) | steps > 0 | gate | excess over the grid's OOS median, 4 steps |
|---|---|---|---|---|---|---|---|
| EURUSD | anchored | d1h_revA (138/218), bosonly (198), bosonly (202), d1h_revB (170) | +11.5, -3.3, -2.3, -1.1 | **0.14** (0.15) | 1/4 | FAIL | -14.1R |
| EURUSD | rolling | d1h_revA, bosonly, d1h_bos (180), noreq_two (107, 0 trades) | +11.5, -3.3, -0.4, 0.0 | 0.17 (0.23) | 1/4 | FAIL | -11.1R |
| XAUUSD | anchored | g25 every step (21, 72, 47, 28 of 129) | +18.5, +2.9, +17.0, +9.7 | 0.84 (0.96) | 4/4 | pass | +11.9R |
| XAUUSD | rolling | g25, g25, g25, gz (25) | +18.5, +2.9, +17.0, +10.2 | 0.76 (0.87) | 4/4 | pass | +12.4R |
| NAS100 | anchored | stopP (109/115, 6 IS trades), inside (65, 9 IS trades), mw (41), mw (4) | -0.1, -2.1, +22.3, +1.9 | 1.09 (1.07) | 2/4 | FAIL | -1.7R |
| NAS100 | rolling | stopP, inside, mw, cand_revD (115/115) | -0.1, -2.1, +22.3, -9.0 | 0.39 (0.33) | 1/4 | FAIL | -12.5R |
| BTCUSD | anchored | cap3_bosonly every step (53, 19, 74, 10 of 161) | +5.7, +5.7, +38.0, +0.4 | 0.79 (1.64) | 4/4 | pass | +9.6R |
| BTCUSD | rolling | cap3_bosonly, cap3_bosonly, forming (143), cand_cap3_fc (119) | +5.7, +5.7, +14.7, -3.1 | 0.36 (0.61) | 3/4 | FAIL | n/a |

Reading. EURUSD's in-sample winners are one-window wonders: `bosonly` made +42.5R in 2025-H1 (rank 1 of 218 in
that window) and lost in 2024, 2025-H2 and 2026-H1; `d1h_bos`, the full-window top at +46.0R, is above the grid
median in 2 of the 5 half-year windows. Every anchored pick ranked in the bottom third out of sample. NAS100's first
two picks had 6 and 9 in-sample trades; its one good step (2026-H1, +22.3R) is a half-year in which 98 % of the
variants were positive (grid median +18.9R), and the rolling pick for 2026-Q3 was the worst variant of the grid.
Gold's pick (`g25`, 122 trades) is a consistent middle-of-the-table variant out of sample (ranks 21-72 of 129) and
adds +11.9R over the grid median across the four steps. BTC's anchored pick is the same variant throughout and adds
+9.6R over the grid median, but the 4/4 record is carried by 2026-H1 (+38.0R of +49.8R; grid median +37.0R, 99 % of
the variants positive) and in 2026-Q3 the grid median was -1.5R with 6 % of the variants positive; the rolling version
fails. Selecting the IS top 5 with equal weight instead of the single best (Table 5) lifts EURUSD to 0.37-0.39 and
NAS100 to 0.62-0.67, still 1-2 positive steps of 4; requiring 20 IS trades or ranking by mean R (Table 6) does not
rescue EURUSD (0.14-0.54, 1-2 of 4) and makes NAS100 0.24-1.06 depending on the window: unstable. On the near-live
and recent sub-grids (Table 6) the WFE is 0.6-1.5 with 3 of 4 positive on EURUSD, gold and NAS100; those pools were
built on 12-14 October around the profile chosen on the whole window, so they are the optimistic bound.

The frozen live profiles over the same four OOS steps: EURUSD +16.7, +5.1, +10.0, +3.6 (4/4; ranks 88, 16, 11, 27
of 218), gold +20.4, +1.5, +24.9, +11.3 (4/4; 5, 85, 7, 6), NAS100 +8.0, -3.2, +24.5, +0.2 (3/4; 48, 79, 21, 9),
BTC +5.8, +6.0, +41.1, -1.5 (3/4; 47, 15, 22, 35). Their "WFE" of 1.4-2.4 means their second half was better than
their first, not that they generalise: the profiles were chosen on 6-13 October on the whole window. The number that
is out of sample for them is the 2017-2023 ratio (mean R OOS / mean R IS, `aca/oos_*`): EURUSD -0.02 (97 trades,
-0.01R), gold -0.33 (371 trades, -0.17R), NAS100 +0.38 (100 trades, +0.29R), BTC 2020-23 -0.46 (130 trades, -0.32R).

## 4. How much an in-sample winner can be trusted (Table 7)

Variants in the IS top decile (12-22 per split) land above the OOS median 62 % (EURUSD), 80 % (gold), 46 % (NAS100),
63 % (BTC) of the time, in the OOS top decile 10 %, 11 %, 6 %, 9 % of the time (chance is 10 %), lose money out of
sample 10 %, 0 %, 19 %, 9 % of the time, and keep a median 53 %, 75 %, 40 %, 52 % of their IS sum. So an in-sample
screen separates the bad variants from the rest; it does not find the best one, on any market. Variants that beat the
live profile in the IS half by 5R or more beat it in the OOS half 2-7 % of the time (BTC 4-19 %); that number is a lower
bound (the live profile was chosen on the whole window) but it is the one the recent "+X R over base" proposals are
measured against, and it says that an in-sample gain of a few R over the live profile is noise: one standard error of
the live totals is 15.7R (EURUSD, 47 trades, sd 2.3R), 22.1R (gold), 15.0R (NAS100), 28.9R (BTC).

Per market:

- **EURUSD: fails both gates.** PBO 0.58, WFE 0.14, picks in the bottom third OOS every step, IS/OOS rank correlation
  0.34, top-decile haircut 0.53. The 2024-2026 window cannot rank EURUSD variants. Any new EURUSD winner is trusted
  at most for not being bad (62 % above median), its expected forward gain is half its in-sample gain, and only the
  2017-2023 period (where the live profile is at zero) and the forward journal can decide.
- **XAUUSD: passes both gates by sum R; the gates say less than they seem.** PBO 0.22, WFE 0.84 and 4/4, haircut
  0.60-0.75; but by mean R PBO 0.58, in the live profile's neighbourhood 0.74, and the whole grid, live profile
  included, loses on 2017-2023 (-0.17R a trade on 371 trades). The in-sample ranking is stable inside one regime.
  A gold winner can be trusted to keep about three quarters of its in-sample gain while the regime lasts; whether the
  regime lasts is not a backtest question.
- **NAS100: fails both gates.** PBO 0.73, P(loss) 0.43, haircut 0.07-0.40, WFE 0.39-1.09 with 1-2 positive steps,
  picks with 6-9 trades. The 43-trade live ledger is too short for a grid of 115: a NAS100 winner is a coin flip with
  a 2-in-5 chance of losing. NAS100 is the market with the best 2017-2023 ratio (+0.38), which is the evidence to use.
- **BTCUSD: borderline.** PBO 0.45 (0.53 at S = 12), haircut 0.51, anchored WFE 0.79 and 4/4 on the strength of
  2026-H1, rolling 0.36; neighbourhood PBO 0.76; 2017-2023 (2020-23) -0.46. A BTC winner keeps about half its
  in-sample gain inside the window and has lost outside it.

## 5. The rule that follows (exact)

A candidate backtested on 2024-01..2026-09 is adopted only when all of the following hold; `candidate_check.py
SYMBOL ledger.csv` computes 1-4 from the matrix in about 10 seconds.

1. **Grid gate**: the market's grid has PBO <= 0.50 (S = 16, sum R after 0.10R costs, variants with >= 10 trades).
   Today: gold 0.22 and BTC 0.45 pass; EURUSD 0.58 and NAS100 0.73 fail, so on those two markets no change is
   adopted on 2024-2026 evidence; it needs 2017-2023 not below the live profile and 20 forward trades.
2. **Candidate overfit screen** (CSCV, 12,870 splits with the candidate added to the grid): P(OOS sum R <= 0) <= 0.20
   and P(above the OOS median | the candidate is IS top decile) >= 0.60 (the unconditional P(above the OOS median)
   >= 0.60 when it is top decile in fewer than 20 % of the splits).
3. **Time consistency**: positive and above the grid median in at least 4 of the 5 windows 2024, 2025-H1, 2025-H2,
   2026-H1, 2026-Q3. This is what catches the full-window peaks that CSCV passes by construction (`d1h_bos` on EURUSD
   passes 2, fails 3).
4. **Haircut and floor**: expected forward gain over the live profile = h x (candidate total - live total), with
   h = 0.5 on EURUSD and BTC, 0.75 on gold, 0.4 on NAS100 (the IS-top-decile median OOS/IS); adopt only when it is at
   least one standard error of the live total: 16R (EURUSD), 22R (gold), 15R (NAS100), 29R (BTC). That is an
   in-sample gain of +32R, +29R, +37R, +58R over the live totals of +39.5, +71.8, +32.9, +64.5R: no knob change in
   the 14 October batch comes near (the largest, `cap3_bosonly` on BTC, is +26R raw, +13R after the haircut).
5. **2017-2023** (BTC 2020-23): the candidate's total on `aca/oos_*`-style ledgers not below the live profile's.
6. **Forward**: the change counts as proven after 20 live trades on it.

Applied to today's candidates (`candidate_check_out.txt`): NAS100 `be2` (B7, break-even at +2R) passes the overfit
screen but its gain over the live profile is -4.5R raw; gold `mw` and `rr10`, BTC `ny` pass the screen with gains of
+1.6, -4.4, +0.8R raw; EURUSD `mw` and NAS100 `ny` fail the screen; the four full-window tops pass the screen on gold,
NAS100 and BTC and fail the time test on EURUSD, and none reaches the floor of step 4. In short: the 14 October
batches contain nothing adoptable, as RESULTS_14oct.md already concluded, and this analysis says the window could not
have shown an adoptable knob change on EURUSD, NAS100 or BTC in the first place.

A process consequence: the 2024-2026 window is spent for EURUSD and NAS100. Further rule research on them is read
on 2017-2023 first (the candidate must not be worse than the live profile there) and decided by the forward journal;
the 2024-2026 run is the sanity check, not the evidence. On gold the window still ranks variants, with the 0.75
haircut; on BTC the window ranks weakly (0.5 haircut) and the true test is outside it.

## 6. Limitations

- The pool is hindsight-contaminated: every variant was built between October 2025 and 14 October 2026 with the
  whole window visible, and the live profiles were chosen on it. A matrix walk-forward tests the selection rule on a
  fixed pool; it cannot test the research process itself, which would need fresh backtests per window (the batch job
  named in methodology A2). This makes the walk-forward optimistic for the live profiles and for the near-live grids;
  it does not help the IS-best rule, which fails anyway.
- Variants are correlated (near-duplicates of a few families): N overstates the number of independent trials; the
  near-live grids (23-28) are the honest count for the knob question, and their PBO is 0.44-0.76.
- The degradation slope is uninformative here (artefact, section 2). The CSCV passes full-window peaks by
  construction (the best total is above the median of both halves); the half-year consistency test is the complement.
- PBO on 4-11 variants (the `oct14b` knob grid) is coarse; S = 16 with 62-day slices puts a whole half-year's regime
  in 3 slices, so the splits do not mix regimes finely; S = 8 and 12 agree within 0.1 except NAS100 (0.56-0.73) and BTC
  (0.36-0.53), the two borderline cases.
- Costs are the flat 0.10R; A7's per-trade costs (BTC 0.18R median) would lower every BTC cell and shift its PBO.
- 802 derived `ev_*` ledgers without provenance were left out; they are post-hoc filters of the same backtests and
  would add correlated columns, not information.

## 7. Checks and files

- BTC start-date pooling: 147 of the BTC runs start 2024-02-01 and 39 start 2024-01-01; the live BTC profile re-run
  from 2024-02-01 (`research/walkforward/btcfeb_BTCUSD.csv`, same yaml and data as `aca/base_BTCUSD`) reproduces all
  85 trades of the 2024-01-01 run inside the common window (+73.03R raw in both, no trade differs), so the engine's
  warm-up does not depend on the start date and the two sets pool exactly.
- NAS100: 88 runs end 2026-09-30 and 39 end 2026-09-24 on the same data file (identical sha256); all were clipped
  to 2026-09-25, so they are the same window.
- Live profile = research ledger: `aca/eutwo_EURUSD` (47 trades, +39.5R), `aca/base_XAUUSD` (143, +71.8R),
  `aca/rr08_NAS100` (43, +32.9R), `aca/base_BTCUSD` (85 trades from February, +64.5R; 89 and +61.7R from January).
- Two to four identical re-runs of each live profile existed in the folders and collapsed into the live variant.

Scripts (all under `research/walkforward/`, run from the scratchpad with `nice -n 10 python3 ...`):

| file | what |
|---|---|
| `inventory.py` -> `inventory.csv` | one row per provenance file: symbol, period, data dir, data sha, settings hash, flattened settings |
| `build_matrix.py` -> `variants_<SYM>.csv`, `trades_<SYM>.csv`, `matrix_<SYM>_S{8,12,16}.csv`, `count_*.csv`, `grid_summary.csv` | the grids: filter, clip, de-duplicate, slice, purge; settings distance from the live profile |
| `cscv_full.py` -> `cscv_results.csv` | PBO, P(OOS loss), slope, Spearman, live rank distribution; sensitivities (S, metric, sub-grids) |
| `walkforward.py` -> `walkforward_steps.csv`, `walkforward_summary.csv` | anchored and rolling walk-forward, IS-best and IS top-5, WFE per month and per trade, the frozen live profile |
| `walkforward_sens.py` -> `walkforward_sens.csv`, `walkforward_sens_steps.csv` | minimum IS trades, mean-R rule, near-live and recent pools |
| `calibration.py` -> `calibration.csv` | IS top decile -> OOS rank; beats-live-IS -> beats-live-OOS by margin |
| `candidate_check.py SYMBOL ledger.csv [label]` -> stdout; `candidate_check_out.txt` | the overfit screen of section 5 for one new ledger |
| `report_tables.py` -> `tables.md` | the tables below |
| `btcfeb_BTCUSD.csv/.log` | the BTC warm-up re-run |

Runtime: the matrix build about 2 minutes, each CSCV run under a minute (12,870 x N matrix products), the BTC
re-run 17 minutes on the loaded machine. Nothing in the repository was changed.

## 8. Tables

### Table 1. The grids (2024-01-01..2026-09-24; BTC from 2024-02-01; 0.10R costs; de-duplicated on identical trade sets)

| market | runs | variants | dup_dropped | n_ge10 | folders | trades | purged | live | live_R | live_rank | best | grid_median_R | positive |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 252 | 220 | 32 | 218 | root q4_*/q4_r26_* 177, aca 30, oct14* 12, adopt 1 | 9403 | 106 (1.1%) | aca/eutwo_EURUSD | +39.5 (47 tr) | 7/220 | q4_EURUSD_cand_d1h_bos +46.0 | +20.6 | 205/220 |
| XAUUSD | 151 | 131 | 20 | 129 | root q4_*/q4_r26_* 100, aca 22, oct14* 9 | 15959 | 54 (0.3%) | aca/base_XAUUSD | +71.8 (143 tr) | 16/131 | q4_XAUUSD_cand_g25 +84.9 | +49.0 | 127/131 |
| NAS100 | 132 | 116 | 16 | 115 | root q4_*/q4_r26_* 85, aca 23, oct14* 5, adopt 2, wdh 1 | 5386 | 140 (2.6%) | aca/rr08_NAS100 | +32.9 (43 tr) | 13/116 | oct14/mw_NAS100 +44.3 | +23.1 | 110/116 |
| BTCUSD | 192 | 161 | 31 | 161 | root q4_*/q4_r26_* 129, aca 23, oct14* 9 | 18388 | 105 (0.6%) | aca/base_BTCUSD | +64.5 (85 tr) | 19/161 | q4_BTCUSD_cap3_bosonly +90.8 | +48.0 | 155/161 |

Distance from the live profile (number of flattened settings that differ) and trade counts:

| market | variants | live_dup_runs | diffs_le3 | diffs_4_10 | diffs_gt10 | median_diffs | median_trades | min_trades | max_trades |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 220 | 2 | 26 | 10 | 184 | 24 | 41 | 2 | 187 |
| XAUUSD | 131 | 4 | 23 | 5 | 103 | 20 | 133 | 0 | 214 |
| NAS100 | 116 | 0 | 25 | 7 | 84 | 20 | 44 | 3 | 134 |
| BTCUSD | 161 | 3 | 28 | 8 | 125 | 19 | 103 | 39 | 376 |

### Table 2. CSCV, main grid: S = 16 slices, 12,870 symmetric splits, sum R after costs, variants with >= 10 trades

| market | N | splits | PBO | P(OOS R of IS-best <= 0) | Spearman IS/OOS rank (median) | OOS/IS of IS-best (median) | IS R of IS-best (median) | OOS R of IS-best (median) | grid OOS median | degradation slope | live IS rel. rank | live OOS rel. rank | live OOS rel. rank p10 | P(live > IS-best OOS) | live is IS-best | gate PBO<=0.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 218 | 12870 | 0.58 | 0.21 | 0.34 | 0.28 | 30.78 | 8.70 | 10.06 | -0.78 | 0.93 | 0.93 | 0.82 | 0.98 | 0.00 | FAIL |
| XAUUSD | 129 | 12870 | 0.22 | 0.01 | 0.66 | 0.60 | 49.36 | 29.63 | 24.74 | -0.86 | 0.84 | 0.85 | 0.67 | 0.80 | 0.00 | pass |
| NAS100 | 115 | 12870 | 0.73 | 0.43 | 0.20 | 0.07 | 27.74 | 2.09 | 9.37 | -0.80 | 0.78 | 0.79 | 0.54 | 0.92 | 0.00 | FAIL |
| BTCUSD | 161 | 12870 | 0.45 | 0.15 | 0.38 | 0.51 | 50.20 | 20.27 | 24.68 | -0.78 | 0.80 | 0.81 | 0.70 | 0.74 | 0.00 | pass |

### Table 3. CSCV sensitivities (PBO / P(OOS loss) / Spearman): slices, metric, sub-grids

| case | EURUSD | XAUUSD | NAS100 | BTCUSD |
|---|---|---|---|---|
| S=16 all sum | N=218: 0.58 / 0.21 | N=129: 0.22 / 0.01 | N=115: 0.73 / 0.43 | N=161: 0.45 / 0.15 |
| S=16 all sum n>=1 | N=220: 0.58 / 0.21 | N=130: 0.21 / 0.01 | N=116: 0.73 / 0.43 | N=161: 0.45 / 0.15 |
| S=8 all sum | N=218: 0.59 / 0.23 | N=129: 0.20 / 0.03 | N=115: 0.56 / 0.46 | N=161: 0.36 / 0.10 |
| S=12 all sum | N=218: 0.58 / 0.20 | N=129: 0.19 / 0.01 | N=115: 0.62 / 0.35 | N=161: 0.53 / 0.19 |
| S=16 all mean | N=218: 0.62 / 0.26 | N=129: 0.58 / 0.21 | N=115: 0.31 / 0.11 | N=161: 0.21 / 0.08 |
| S=16 root sum | N=176: 0.56 / 0.22 | N=99: 0.10 / 0.00 | N=85: 0.78 / 0.45 | N=130: 0.22 / 0.06 |
| S=16 recent sum | N=43: 0.52 / 0.01 | N=31: 0.65 / 0.01 | N=30: 0.61 / 0.15 | N=32: 0.91 / 0.23 |
| S=16 knob sum | N=11: 0.82 / 0.00 | N=8: 0.27 / 0.00 | N=4: 0.43 / 0.07 | N=7: 0.81 / 0.02 |
| S=16 near3 sum | N=26: 0.44 / 0.01 | N=23: 0.74 / 0.01 | N=25: 0.59 / 0.14 | N=28: 0.76 / 0.04 |
| S=16 near6 sum | N=33: 0.45 / 0.01 | N=24: 0.64 / 0.01 | N=27: 0.59 / 0.14 | N=33: 0.91 / 0.23 |

### Table 4a. Anchored walk-forward, rule = highest IS sum R after costs (all variants with >= 10 trades)

**EURUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_EURUSD_cand_d1h_revA | +17.2 (44) | +11.5 (18) | 138/218 | +4.1 (37) | +16.7 (10, 88) | +15.7 / 97% | +42.5 (148) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_EURUSD_cand_bosonly | +41.1 (30) | -3.3 (8) | 198/218 | +20.9 (50) | +5.1 (9, 16) | +1.1 / 64% | +11.7 (87) |
| 2024-01-01..2026-01-01 | 2026-01-01..2026-07-01 | q4_EURUSD_cand_bosonly | +37.8 (38) | -2.3 (8) | 202/218 | +25.9 (28) | +10.0 (10, 11) | +2.1 / 74% | +13.3 (168) |
| 2024-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_EURUSD_cand_d1h_revB | +43.1 (51) | -1.1 (4) | 170/218 | +35.9 (12) | +3.6 (3, 27) | +0.0 / 49% | +12.5 (31) |

**XAUUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_XAUUSD_cand_g25 | +36.8 (49) | +18.5 (24) | 21/129 | +13.7 (57) | +20.4 (25, 5) | +14.6 / 90% | +24.6 (55) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_XAUUSD_cand_g25 | +55.3 (73) | +2.9 (20) | 72/129 | +34.1 (34) | +1.5 (23, 85) | +3.6 / 80% | +20.3 (39) |
| 2024-01-01..2026-01-01 | 2026-01-01..2026-07-01 | q4_XAUUSD_cand_g25 | +58.2 (93) | +17.0 (20) | 47/129 | +35.6 (47) | +24.9 (25, 7) | +10.7 / 92% | +29.4 (102) |
| 2024-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_XAUUSD_cand_g25 | +75.2 (113) | +9.7 (9) | 28/129 | +60.5 (19) | +11.3 (13, 6) | +7.2 / 93% | +14.3 (63) |

**NAS100**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | aca/stopP_NAS100 | +9.5 (6) | -0.1 (4) | 109/115 | +3.3 (10) | +8.0 (10, 48) | +7.2 / 93% | +15.4 (69) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | aca/inside_NAS100 | +15.5 (9) | -2.1 (8) | 65/115 | +11.3 (16) | -3.2 (9, 79) | -1.3 / 25% | +18.3 (108) |
| 2024-01-01..2026-01-01 | 2026-01-01..2026-07-01 | oct14/mw_NAS100 | +20.1 (51) | +22.3 (15) | 41/115 | +8.2 (34) | +24.5 (13, 21) | +18.9 / 98% | +30.9 (101) |
| 2024-01-01..2026-07-01 | 2026-07-01..2026-09-25 | oct14/mw_NAS100 | +42.5 (66) | +1.9 (4) | 4/115 | +32.7 (16) | +0.2 (3, 9) | -1.1 / 32% | +5.3 (100) |

**BTCUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-02-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_BTCUSD_cap3_bosonly | +42.1 (65) | +5.7 (13) | 53/161 | +13.1 (50) | +5.8 (12, 47) | +3.6 / 77% | +27.2 (155) |
| 2024-02-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_BTCUSD_cap3_bosonly | +47.8 (78) | +5.7 (15) | 19/161 | +18.9 (44) | +6.0 (10, 15) | +1.2 / 55% | +11.0 (79) |
| 2024-02-01..2026-01-01 | 2026-01-01..2026-07-01 | q4_BTCUSD_cap3_bosonly | +53.5 (93) | +38.0 (12) | 74/161 | +24.9 (21) | +41.1 (15, 22) | +37.0 / 99% | +50.8 (37) |
| 2024-02-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_BTCUSD_cap3_bosonly | +91.5 (105) | +0.4 (4) | 10/161 | +66.1 (20) | -1.5 (3, 35) | -1.5 / 6% | +4.7 (116) |

### Table 4b. Rolling walk-forward, rule = highest IS sum R after costs (all variants with >= 10 trades)

**EURUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_EURUSD_cand_d1h_revA | +17.2 (44) | +11.5 (18) | 138/218 | +4.1 (37) | +16.7 (10, 88) | +15.7 / 97% | +42.5 (148) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_EURUSD_cand_bosonly | +41.1 (30) | -3.3 (8) | 198/218 | +20.9 (50) | +5.1 (9, 16) | +1.1 / 64% | +11.7 (87) |
| 2024-07-01..2026-01-01 | 2026-01-01..2026-07-01 | q4_EURUSD_cand_d1h_bos | +49.3 (56) | -0.4 (14) | 180/218 | +28.0 (38) | +10.0 (10, 11) | +2.1 / 74% | +13.3 (158) |
| 2025-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_EURUSD_cand_noreq_two | +40.5 (42) | +0.0 (0) | 107/218 | +31.8 (13) | +3.6 (3, 27) | +0.0 / 49% | +12.5 (7) |

**XAUUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_XAUUSD_cand_g25 | +36.8 (49) | +18.5 (24) | 21/129 | +13.7 (57) | +20.4 (25, 5) | +14.6 / 90% | +24.6 (55) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_XAUUSD_cand_g25 | +55.3 (73) | +2.9 (20) | 72/129 | +34.1 (34) | +1.5 (23, 85) | +3.6 / 80% | +20.3 (39) |
| 2024-07-01..2026-01-01 | 2026-01-01..2026-07-01 | q4_XAUUSD_cand_g25 | +56.7 (72) | +17.0 (20) | 47/129 | +41.6 (30) | +24.9 (25, 7) | +10.7 / 92% | +29.4 (97) |
| 2025-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_XAUUSD_cand_gz | +55.6 (91) | +10.2 (14) | 25/129 | +46.8 (7) | +11.3 (13, 6) | +7.2 / 93% | +14.3 (77) |

**NAS100**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-01-01..2025-01-01 | 2025-01-01..2025-07-01 | aca/stopP_NAS100 | +9.5 (6) | -0.1 (4) | 109/115 | +3.3 (10) | +8.0 (10, 48) | +7.2 / 93% | +15.4 (69) |
| 2024-01-01..2025-07-01 | 2025-07-01..2026-01-01 | aca/inside_NAS100 | +15.5 (9) | -2.1 (8) | 65/115 | +11.3 (16) | -3.2 (9, 79) | -1.3 / 25% | +18.3 (108) |
| 2024-07-01..2026-01-01 | 2026-01-01..2026-07-01 | oct14/mw_NAS100 | +26.7 (37) | +22.3 (15) | 41/115 | +7.4 (41) | +24.5 (13, 21) | +18.9 / 98% | +30.9 (101) |
| 2025-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_NAS100_cand_revD | +44.5 (51) | -9.0 (10) | 115/115 | +29.4 (20) | +0.2 (3, 9) | -1.1 / 32% | +5.3 (87) |

**BTCUSD**

| IS | OOS | selected | sel IS R (n) | sel OOS R (n) | sel OOS rank | live IS R (rank) | live OOS R (n, rank) | grid OOS median / share > 0 | hindsight best OOS (its IS rank) |
|---|---|---|---|---|---|---|---|---|---|
| 2024-02-01..2025-01-01 | 2025-01-01..2025-07-01 | q4_BTCUSD_cap3_bosonly | +42.1 (65) | +5.7 (13) | 53/161 | +13.1 (50) | +5.8 (12, 47) | +3.6 / 77% | +27.2 (155) |
| 2024-02-01..2025-07-01 | 2025-07-01..2026-01-01 | q4_BTCUSD_cap3_bosonly | +47.8 (78) | +5.7 (15) | 19/161 | +18.9 (44) | +6.0 (10, 15) | +1.2 / 55% | +11.0 (79) |
| 2024-07-01..2026-01-01 | 2026-01-01..2026-07-01 | aca/forming_BTCUSD | +30.8 (68) | +14.7 (20) | 143/161 | +19.8 (20) | +41.1 (15, 22) | +37.0 / 99% | +50.8 (46) |
| 2025-01-01..2026-07-01 | 2026-07-01..2026-09-25 | q4_BTCUSD_cand_cap3_fc | +69.4 (56) | -3.1 (5) | 119/161 | +52.9 (7) | -1.5 (3, 35) | -1.5 / 6% | +4.7 (137) |

### Table 5. Walk-forward efficiency (Pardo: OOS R per month / IS R per month of the selected variant, pooled over the 4 steps) and the frozen live profile

| market | mode | rule | sel OOS R/month | sel IS R/month | WFE (per month) | WFE (per trade) | OOS steps > 0 | OOS total R | live OOS R/month | live WFE (per month) | live steps > 0 | live OOS total R | gate WFE>=0.5 & 3/4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | anchored | IS-best | 0.23 | 1.68 | 0.14 | 0.15 | 1/4 | 4.84 | 1.71 | 1.80 | 4/4 | 35.42 | FAIL |
| EURUSD | anchored | IS top-5 equal weight | 0.55 | 1.49 | 0.37 | 0.39 | 1/4 | 11.32 | 1.71 | 1.80 | 4/4 | 35.42 | FAIL |
| EURUSD | rolling | IS-best | 0.38 | 2.18 | 0.17 | 0.23 | 1/4 | 7.82 | 1.71 | 1.41 | 4/4 | 35.42 | FAIL |
| EURUSD | rolling | IS top-5 equal weight | 0.74 | 1.93 | 0.39 | 0.47 | 2/4 | 15.47 | 1.71 | 1.41 | 4/4 | 35.42 | FAIL |
| XAUUSD | anchored | IS-best | 2.32 | 2.77 | 0.84 | 0.96 | 4/4 | 48.11 | 2.80 | 1.71 | 4/4 | 58.14 | pass |
| XAUUSD | anchored | IS top-5 equal weight | 2.16 | 2.40 | 0.90 | 1.01 | 4/4 | 44.78 | 2.80 | 1.71 | 4/4 | 58.14 | pass |
| XAUUSD | rolling | IS-best | 2.34 | 3.09 | 0.76 | 0.87 | 4/4 | 48.63 | 2.80 | 1.41 | 4/4 | 58.14 | pass |
| XAUUSD | rolling | IS top-5 equal weight | 2.11 | 2.69 | 0.79 | 0.88 | 4/4 | 43.89 | 2.80 | 1.41 | 4/4 | 58.14 | pass |
| NAS100 | anchored | IS-best | 1.06 | 0.98 | 1.09 | 1.07 | 2/4 | 22.05 | 1.42 | 2.43 | 3/4 | 29.56 | FAIL |
| NAS100 | anchored | IS top-5 equal weight | 0.56 | 0.84 | 0.67 | 0.53 | 2/4 | 11.67 | 1.42 | 2.43 | 3/4 | 29.56 | FAIL |
| NAS100 | rolling | IS-best | 0.54 | 1.40 | 0.39 | 0.33 | 1/4 | 11.24 | 1.42 | 1.93 | 3/4 | 29.56 | FAIL |
| NAS100 | rolling | IS top-5 equal weight | 0.70 | 1.13 | 0.62 | 0.49 | 2/4 | 14.55 | 1.42 | 1.93 | 3/4 | 29.56 | FAIL |
| BTCUSD | anchored | IS-best | 2.40 | 3.03 | 0.79 | 1.64 | 4/4 | 49.80 | 2.47 | 1.74 | 3/4 | 51.39 | pass |
| BTCUSD | anchored | IS top-5 equal weight | 1.76 | 2.33 | 0.76 | 1.25 | 3/4 | 36.50 | 2.47 | 1.74 | 3/4 | 51.39 | pass |
| BTCUSD | rolling | IS-best | 1.11 | 3.05 | 0.36 | 0.61 | 3/4 | 22.97 | 2.47 | 1.56 | 3/4 | 51.39 | FAIL |
| BTCUSD | rolling | IS top-5 equal weight | 1.77 | 2.37 | 0.75 | 1.14 | 3/4 | 36.83 | 2.47 | 1.56 | 3/4 | 51.39 | pass |

Excess of the selected variant (and of the live profile) over the grid's OOS median, per step (what the selection adds beyond the market regime):

| market | mode | sel OOS R - grid median, per step | sum | live OOS R - grid median, per step | live sum |
|---|---|---|---|---|---|
| EURUSD | anchored | -4.2 | -4.4 | -4.4 | -1.1 | -14.1 | +1.1 | +4.0 | +7.9 | +3.6 | +16.5 |
| EURUSD | rolling | -4.2 | -4.4 | -2.5 | +0.0 | -11.1 | +1.1 | +4.0 | +7.9 | +3.6 | +16.5 |
| XAUUSD | anchored | +3.9 | -0.7 | +6.3 | +2.5 | +11.9 | +5.8 | -2.2 | +14.2 | +4.1 | +21.9 |
| XAUUSD | rolling | +3.9 | -0.7 | +6.3 | +3.0 | +12.4 | +5.8 | -2.2 | +14.2 | +4.1 | +21.9 |
| NAS100 | anchored | -7.3 | -0.7 | +3.4 | +3.0 | -1.7 | +0.7 | -1.8 | +5.6 | +1.3 | +5.8 |
| NAS100 | rolling | -7.3 | -0.7 | +3.4 | -7.9 | -12.5 | +0.7 | -1.8 | +5.6 | +1.3 | +5.8 |
| BTCUSD | anchored | +2.1 | +4.6 | +1.1 | +1.9 | +9.6 | +2.2 | +4.9 | +4.2 | +0.0 | +11.2 |
| BTCUSD | rolling | +2.1 | +4.6 | -22.3 | -1.6 | -17.2 | +2.2 | +4.9 | +4.2 | +0.0 | +11.2 |

### Table 6. Walk-forward sensitivities: candidate pool and selection rule (WFE per month, OOS steps > 0, OOS total R, median OOS rank of the pick)

| case | mode | EURUSD | XAUUSD | NAS100 | BTCUSD |
|---|---|---|---|---|---|
| all, IS n>=20, sum R | anchored | N=218: WFE 0.14, 1/4, +4.8R, med. OOS rank 184 | N=129: WFE 0.84, 4/4, +48.1R, med. OOS rank 38 | N=115: WFE 0.91, 2/4, +17.7R, med. OOS rank 60 | N=161: WFE 0.79, 4/4, +49.8R, med. OOS rank 36 |
| all, IS n>=20, sum R | rolling | N=218: WFE 0.17, 1/4, +7.8R, med. OOS rank 159 | N=129: WFE 0.76, 4/4, +48.6R, med. OOS rank 36 | N=115: WFE 0.24, 1/4, +6.8R, med. OOS rank 96 | N=161: WFE 0.36, 3/4, +23.0R, med. OOS rank 86 |
| all, IS n>=20, mean R/trade | anchored | N=218: WFE 0.54, 2/4, +14.6R, med. OOS rank 120 | N=129: WFE 0.83, 4/4, +45.1R, med. OOS rank 58 | N=115: WFE 1.06, 2/4, +17.3R, med. OOS rank 70 | N=161: WFE 0.64, 3/4, +33.0R, med. OOS rank 72 |
| all, IS n>=20, mean R/trade | rolling | N=218: WFE 0.37, 2/4, +13.2R, med. OOS rank 145 | N=129: WFE 0.55, 4/4, +29.9R, med. OOS rank 70 | N=115: WFE 0.89, 2/4, +21.0R, med. OOS rank 60 | N=161: WFE 0.31, 3/4, +16.7R, med. OOS rank 72 |
| near3, IS n>=0, sum R | anchored | N=26: WFE 0.63, 3/4, +15.5R, med. OOS rank 13 | N=23: WFE 1.10, 3/4, +43.2R, med. OOS rank 16 | N=25: WFE 1.09, 2/4, +22.1R, med. OOS rank 14 | N=28: WFE 0.64, 3/4, +26.6R, med. OOS rank 9 |
| near3, IS n>=0, sum R | rolling | N=26: WFE 0.48, 3/4, +15.5R, med. OOS rank 13 | N=23: WFE 0.76, 3/4, +35.7R, med. OOS rank 18 | N=25: WFE 0.80, 2/4, +22.1R, med. OOS rank 14 | N=28: WFE 0.56, 3/4, +25.5R, med. OOS rank 18 |
| near3, IS n>=20, sum R | anchored | N=26: WFE 1.22, 3/4, +27.2R, med. OOS rank 12 | N=23: WFE 1.10, 3/4, +43.2R, med. OOS rank 16 | N=25: WFE 1.16, 3/4, +19.3R, med. OOS rank 12 | N=28: WFE 0.64, 3/4, +26.6R, med. OOS rank 9 |
| near3, IS n>=20, sum R | rolling | N=26: WFE 0.92, 3/4, +27.2R, med. OOS rank 12 | N=23: WFE 0.76, 3/4, +35.7R, med. OOS rank 18 | N=25: WFE 0.81, 3/4, +19.3R, med. OOS rank 12 | N=28: WFE 0.56, 3/4, +25.5R, med. OOS rank 18 |
| recent, IS n>=0, sum R | anchored | N=43: WFE 1.13, 3/4, +29.2R, med. OOS rank 6 | N=31: WFE 1.10, 3/4, +43.2R, med. OOS rank 21 | N=30: WFE 1.09, 2/4, +22.1R, med. OOS rank 14 | N=32: WFE 0.44, 2/4, +18.6R, med. OOS rank 18 |
| recent, IS n>=0, sum R | rolling | N=43: WFE 0.88, 3/4, +29.2R, med. OOS rank 6 | N=31: WFE 0.76, 3/4, +35.7R, med. OOS rank 24 | N=30: WFE 0.80, 2/4, +22.1R, med. OOS rank 14 | N=32: WFE 0.38, 2/4, +17.5R, med. OOS rank 28 |
| recent, IS n>=20, sum R | anchored | N=43: WFE 1.13, 3/4, +29.2R, med. OOS rank 6 | N=31: WFE 1.10, 3/4, +43.2R, med. OOS rank 21 | N=30: WFE 1.49, 3/4, +25.7R, med. OOS rank 13 | N=32: WFE 0.44, 2/4, +18.6R, med. OOS rank 18 |
| recent, IS n>=20, sum R | rolling | N=43: WFE 0.88, 3/4, +29.2R, med. OOS rank 6 | N=31: WFE 0.76, 3/4, +35.7R, med. OOS rank 24 | N=30: WFE 1.04, 3/4, +25.7R, med. OOS rank 13 | N=32: WFE 0.38, 2/4, +17.5R, med. OOS rank 28 |

### Table 7a. Variants in the IS top decile: where they land out of sample (CSCV, main grid)

| market | N | top-decile size | OOS rel. rank (median) | P(above OOS median) | P(in OOS top decile) | P(OOS R <= 0) | OOS/IS (median) |
|---|---|---|---|---|---|---|---|
| EURUSD | 218 | 22 | 0.60 | 0.62 | 0.10 | 0.10 | 0.53 |
| XAUUSD | 129 | 13 | 0.68 | 0.80 | 0.11 | 0.00 | 0.75 |
| NAS100 | 115 | 12 | 0.47 | 0.46 | 0.06 | 0.19 | 0.40 |
| BTCUSD | 161 | 16 | 0.59 | 0.63 | 0.09 | 0.09 | 0.52 |

### Table 7b. Variants that beat the live profile in the IS half, by margin: share that also beat it in the OOS half (a lower bound: the live profile was chosen on the whole window)

| market | beats live IS by 0-2R: P(beats live OOS) [median dOOS] | beats live IS by 2-5R: P(beats live OOS) [median dOOS] | beats live IS by 5-10R: P(beats live OOS) [median dOOS] | beats live IS by 10-infR: P(beats live OOS) [median dOOS] |
|---|---|---|---|---|
| EURUSD | 0.04 [-8.9] | 0.05 [-11.2] | 0.02 [-12.1] | 0.00 [-13.1] |
| XAUUSD | 0.26 [-2.6] | 0.11 [-5.1] | 0.07 [-7.6] | 0.06 [-11.2] |
| NAS100 | 0.18 [-2.7] | 0.11 [-4.7] | 0.09 [-8.9] | 0.04 [-15.2] |
| BTCUSD | 0.31 [-2.2] | 0.26 [-4.7] | 0.04 [-9.7] | 0.19 [-7.8] |
