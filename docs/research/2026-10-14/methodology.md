# Backtesting and validation methodology: what we do, what the toolkit adds, eight analyses to run

14 October 2026. Angle: validation methodology (not the rules). Read-only on the repository; pilots run from the
scratchpad on the research ledgers (`scratchpad/aca/*.csv`, 1 % risk, guard off, 0.10R a trade for costs).

## 1. Where we stand

What the research does today (docs/CURRENT_STATE.md, docs/backtests/winrate/README.md):

- one in-sample window, 2024-01..2026-09, on which every rule was chosen (the profiles are "chosen on 2024-2026 only"
  since 6 October);
- one out-of-sample window, 2017..2023 (BTC 2020-06..2023), read for most candidates, with "holds" meaning
  "the change is positive in both periods";
- the FTMO replay (`scripts/risk_steps.py`) on the one historical path, every calendar day a start;
- a plateau check by hand for two knobs (min R:R 1.5/2.0, the BTC cap);
- costs: a flat 0.10R a trade on top of the backtest's typical spread (gold 2 pips against 3.4-3.7 measured);
  no commission in the research ledgers (`provenance.json`: "commission: none modelled", "slippage: none modelled");
- no walk-forward, no Monte Carlo on the trade order, no bootstrap interval on the expectancy, no correction for the
  number of variants tried (hundreds a market: the README names 91 EURUSD variants on 7 October alone, 142 runs in the
  r26 workflow, 33 knob runs in oct14b; the scratchpad holds 600-900 ledgers a market).

What the ledgers themselves say (0.10R a trade off; `research/stats1.py`, `research/cscv.py`):

| Ledger | n | mean R | block-bootstrap 95 % CI | PSR(0) | MinTRL (trades) | DSR at N=100 / 300 trials | max DD | R without the top 3 |
|---|---|---|---|---|---|---|---|---|
| EURUSD 2024-26 (`eutwo`) | 47 | +0.84 | (+0.34, +1.34) | 0.998 | 16 | 0.48 / 0.32 | -5.5R | +21.6 of +39.5 |
| XAUUSD 2024-26 (`base`) | 143 | +0.50 | (+0.23, +0.78) | 1.000 | 30 | 0.79 / 0.65 | -9.0R | +52.6 of +71.8 |
| NAS100 2024-26 (`rr08`) | 43 | +0.77 | (+0.20, +1.34) | 0.994 | 19 | 0.34 / 0.20 | -5.8R | +15.4 of +32.9 |
| BTCUSD 2024-26 (`base`) | 89 | +0.69 | (+0.17, +1.43) | 1.000 | 16 | 0.22 / 0.07 | -4.9R | +22.8 of +61.7 |
| EURUSD 2017-23 | 97 | -0.01 | (-0.39, +0.42) | 0.48 | - | - | -24.6R | |
| XAUUSD 2017-23 | 371 | -0.17 | (-0.32, -0.02) | 0.03 | - | - | -83.2R | |
| NAS100 2017-23 | 100 | +0.29 | (-0.16, +0.76) | 0.91 | 156 | 0.05 / 0.02 | -11.8R | |
| BTCUSD 2020-23 | 130 | -0.32 | (-0.54, -0.08) | 0.00 | - | - | -49.8R | |

Reading: in-sample, every market's expectancy is clear of zero on its own trades (the bootstrap and the probabilistic
Sharpe ratio agree). Once the number of configurations tried is counted, none of the four in-sample Sharpe ratios is
distinguishable from the best of 100 zero-edge trials except gold's (DSR 0.79, still under 0.95). The true
out-of-sample period confirms that: only NAS100 keeps a positive mean, and its interval includes zero. The
in-sample window is also too short for the number of trials: at the observed annualised Sharpe (EURUSD 1.6,
gold 2.0, NAS100 1.4, BTC 1.3) 2.5-2.7 years of data allow at most about 23, 192, 10 and 9 independent trials before
the best in-sample result is what luck alone would show (Bailey et al. 2014, MinBTL < 2 ln N / SR^2).

CSCV on the variant ledgers that cover the whole window in `scratchpad/aca/` (S = 10 slices, 252 symmetric splits,
sum of R after costs per slice): probability of backtest overfitting EURUSD 0.47 (28 variants), gold 0.45 (24),
NAS100 0.61 (28), BTC 0.84 (24). In the anchored 60/40 split the in-sample best variant's out-of-sample rank is
18/28, 11/24, 3/28 and 22/24; the live profiles rank 2/28, 1/24, 15/28 and 6/24. The grid is small and includes
variants built to be worse (the academy literal rules), which flatters PBO; the full run is analysis 1 below.

## 2. The standard toolkit, in one paragraph each

- **Walk-forward analysis** (Pardo 2008): optimise on an in-sample window, trade the next window with the chosen
  parameters, step forward; anchored (the in-sample start fixed, the window grows) or rolling (fixed length). The
  walk-forward efficiency, out-of-sample return rate over in-sample return rate, is the summary; 0.5 is the usual
  convention for "the parameters carry over". Window lengths are free choices, so they are fixed before the run.
- **Purging and embargo, combinatorial purged CV** (Lopez de Prado 2018, ch. 7): training observations whose labels
  (here: trades) overlap in time with the test fold are removed (purge), plus a buffer after the test fold (embargo);
  with N groups and k test groups, C(N, k) backtest paths give a distribution of out-of-sample results instead of one.
- **Probability of backtest overfitting, CSCV** (Bailey, Borwein, Lopez de Prado, Zhu 2017): a T x N matrix of
  performance (time slices x configurations) is cut into S even submatrices; for each of the C(S, S/2) symmetric
  in-sample/out-of-sample splits, take the in-sample best configuration n*, its out-of-sample relative rank
  omega = rank/(N+1), the logit lambda = ln(omega/(1-omega)); PBO = share of splits with lambda < 0 (the in-sample
  winner below the out-of-sample median). The paper also reads the degradation slope (OOS vs IS of n*) and
  Prob[OOS R of n* < 0].
- **Probabilistic Sharpe ratio, minimum track record length** (Bailey and Lopez de Prado 2012):
  PSR(SR*) = Phi[(SR - SR*) sqrt(n-1) / sqrt(1 - g3 SR + (g4-1)/4 SR^2)] with skewness g3 and raw kurtosis g4;
  MinTRL = 1 + (1 - g3 SR + (g4-1)/4 SR^2) (Z_0.95/(SR - SR*))^2 observations. Per-trade R works as the return series
  when trades are close to independent.
- **Deflated Sharpe ratio** (Bailey and Lopez de Prado 2014) and **minimum backtest length** (Bailey et al. 2014):
  the expected maximum of N zero-edge Sharpe estimates is
  E[max_N] ~ sqrt(V[SR]) [(1-g) Z^-1(1-1/N) + g Z^-1(1-1/(N e))], g = 0.5772 (Euler-Mascheroni);
  DSR = PSR(E[max_N]); MinBTL (years) ~ (E[max_N]/SR)^2 < 2 ln N / SR^2 for an annualised SR. N is the number of
  independent trials; correlated variants count for less (the paper suggests a PCA count).
- **Haircut Sharpe ratio** (Harvey and Liu 2015): the single-test p-value of the Sharpe ratio, adjusted for N tests
  with Bonferroni, Holm or BHY (BHY unless a false discovery is severe), converted back to a Sharpe ratio; their
  example: SR 0.75 on 240 months, N = 200 tests, haircut to 0.32 (-60 %). Their point: the 50 % haircut rule of thumb
  is wrong in both directions; low Sharpes get haircuts above 50 %, high ones under 25 %.
- **Data-snooping tests over a universe of rules** (White 2000 reality check, Hansen 2005 SPA, model confidence
  set): bootstrap the best rule's excess performance against the whole set tried. Our variant grids are such a universe.
- **Bootstrap intervals on the expectancy** (Politis and Romano 1994 stationary bootstrap): resample the per-trade R
  with replacement, iid or in blocks of about n^(1/3) trades (or calendar blocks), take percentiles. Trades are not
  independent (same zone, same day, same regime), so block resampling is the honest one and the coverage is checked.
- **Monte Carlo on the trade order** (trade resampling): reorder or resample the trades, read the distribution of
  the maximum drawdown and the probability of touching a barrier (the prop-firm limits); plain shuffling scatters the
  loss clusters and is optimistic, so block resampling (weeks, months) is the rule.
- **Parameter plateaus** (parameter stability): a robust setting sits inside a region whose neighbours perform
  alike; pick the plateau centre, not the peak; report the best, the top-10 % and the standard deviation of the grid.
- **Permutation and randomisation tests** (Masters 2018/2020): a null model with the same number of trades, the same
  exits and the same hours but random entries (direction or timing), or permuted price changes; the p-value is the
  share of null results at least as good as the real one; a few hundred iterations for central values, thousands for
  tails.
- **Execution models**: fill rules (a limit fills on a trade-through, not a touch, in the conservative convention;
  stops fill at the next available price when a bar gaps through), costs scaled by spread, volatility, hour and
  order type; stops treated more harshly than resting limits. Gold spreads widen into the 23:00 server-time rollover
  and in Asian hours; no public hour-by-hour dataset exists, so the profile is measured from the broker's own ticks.
  FTMO crypto: commission 0.0325 % a side on the notional since 28 July 2025, spread not published.

## 3. The eight analyses

Each: statistic, inputs (ledger columns), procedure, pass/fail, how it is run, what the pilot says.

### A1. Probability of backtest overfitting (CSCV) on the variant matrix, per market

- **Statistic:** PBO = share of the C(S, S/2) symmetric splits in which the in-sample best variant ranks below the
  out-of-sample median; with it the degradation slope (OOS sum R of n* against its IS sum R) and
  Prob[OOS sum R of n* <= 0].
- **Inputs:** every variant ledger run on 2024-01..2026-09 for the market (`scratchpad/aca/`, `aca_ex/`, `adopt/`,
  `oct14*/`, `q4_r26_*`; N >= 100 a market after de-duplicating identical trade sets); columns `opened_at`,
  `closed_at`, `r`. Cell (s, n) = sum of (r - cost) of variant n's trades opened in slice s; S = 16 equal-length
  slices (12,870 splits). Purge: a trade whose `closed_at` crosses a slice boundary is dropped from both halves
  (hold times: median 1-2 h, p90 <= 35 h, so a 48 h purge window); embargo one slice when S = 16 gives 2-month
  slices and a trade's effect can carry over (the visit memory).
- **Pass/fail:** a rule change is adoptable when the grid it was picked from has PBO <= 0.50 (the MinervaScore
  threshold; the original paper's Neyman-Pearson 0.05 would reject nearly every discretionary grid); "robust" needs
  PBO <= 0.30 and Prob[OOS loss of n*] <= 0.20. Report the live profile's own OOS rank distribution beside it.
- **How:** `research/cscv.py` (the pilot) extended to all folders; no repository change.
- **Pilot:** PBO EURUSD 0.47, gold 0.45, NAS100 0.61, BTC 0.84 on 24-28 variants (above). BTC and NAS100 fail
  the gate on the small grid; the live profiles were not the in-sample peaks, which is why they held in the anchored
  split.

### A2. Walk-forward with the selection rule frozen (anchored and rolling), walk-forward efficiency

- **Statistic:** WFE = (mean R after costs of the selected variant out-of-sample) / (its mean R in-sample), pooled
  over the steps; the count of out-of-sample steps with sum R > 0; the same for the frozen live profile.
- **Inputs:** the variant matrix of A1 (or, in the full version, fresh backtests per window); the selection rule as
  actually practised: highest sum R after costs in the in-sample window, ties to the fewest changes from the base.
- **Procedure:** anchored: IS 2024-01..2024-12 -> OOS 2025-H1; IS ..2025-06 -> OOS 2025-H2; IS ..2025-12 -> OOS
  2026-H1; IS ..2026-06 -> OOS 2026-Q3. Rolling: IS the last 18 months. The 2017-2023 ledgers give the long
  out-of-sample ratio beside it (mean R OOS / mean R IS of the live profile).
- **Pass/fail:** WFE >= 0.5 and at least 3 of the 4 OOS steps positive (Pardo's convention); report the 2017-2023
  ratio as the second number, where only NAS100 (0.37) is above zero today.
- **How:** a scratchpad driver on the matrix (no code change); the full version re-runs
  `python -m kronos_trader --config <variant.yaml> backtest --symbol <S> --start <IS start> --end <OOS end> --out <csv>`
  per window on the 33-knob grid (`oct14b`), which is a batch job, not a code change.
- **Pilot:** anchored 60/40 on the small grid: the IS-best's OOS/IS (per-slice scaled, median over the CSCV
  splits) EURUSD 0.60, gold 0.77, NAS100 0.53, BTC 0.47; the 2017-2023 ratios EURUSD ~0.0, gold < 0, NAS100 0.37,
  BTC < 0.

### A3. Bootstrap interval on the expectancy, PSR, MinTRL and top-k dependence

- **Statistic:** mean R after costs with its 2.5/97.5 percentiles from (a) 10,000 iid resamples and (b) a circular
  block bootstrap with block length ceil(n^(1/3)) (4-5 trades) and with calendar-month blocks; P(mean <= 0);
  PSR(0) on the per-trade R; MinTRL in trades; the same interval with the 3 largest winners removed.
- **Inputs:** `r`, `opened_at`, `closed_at` per ledger (and the four combined through `scripts/portfolio.py` for
  the account figure); cost per trade from A7 or the flat 0.10R until then.
- **Pass/fail:** the block-bootstrap lower bound > 0, PSR(0) >= 0.95, n >= MinTRL, and the mean without the top 3
  winners still > 0. A market that passes only on the iid interval and not on the block interval is clustered, not
  robust.
- **How:** `research/stats1.py` (pilot), no repository change; add the three numbers to the README's result tables.
- **Pilot:** in-sample all four pass (lower bounds +0.17..+0.34R, PSR >= 0.99, MinTRL 16-30 trades); 2017-2023
  none passes (NAS100 the closest: PSR 0.91, MinTRL 156 trades against 100). Without the top 3 winners NAS100 keeps
  +15.4 of +32.9R and BTC +22.8 of +61.7R: those two edges live in 3 trades each.

### A4. Deflated Sharpe ratio and minimum backtest length with the trial count from the research log

- **Statistic:** N = the number of distinct configurations backtested on 2024-2026 per market (count the
  `*.provenance.json` files, de-duplicated by settings hash); N_eff = the number of variants whose trade sets differ
  by at least 20 % of the trades (the cheap stand-in for the paper's PCA count). SR0 = sqrt(1/(n-1)) [(1-g) Z^-1(1-1/N)
  + g Z^-1(1-1/(N e))]; DSR = PSR(SR0). MinBTL (years) = (E[max_N]/SR_annual)^2 with the upper bound 2 ln N / SR^2.
- **Inputs:** `r` per ledger; the provenance files for N.
- **Pass/fail:** DSR >= 0.95 at N_eff and the backtest span >= MinBTL at N_eff; otherwise the in-sample result is
  not evidence on its own and the candidate needs the 2017-2023 period or the forward journal to decide.
- **How:** scratchpad script; a convention, not code: one `trials_<symbol>.csv` row per backtest run, kept with
  the ledgers (the provenance files already carry the settings hash).
- **Pilot:** at N = 100, DSR EURUSD 0.48, gold 0.79, NAS100 0.34, BTC 0.22; at N = 300: 0.32 / 0.65 / 0.20 / 0.07.
  MinBTL at the observed annualised Sharpe: 2.5 years cover N = 23 (EURUSD), 192 (gold), 10 (NAS100), 9 (BTC)
  independent trials. Gold is the one market whose in-sample evidence has room for a grid; the other three are
  decided by the long out-of-sample period and the forward record, not by 2024-2026.

### A5. Monte Carlo of the FTMO challenge on block-bootstrap paths through `risk_steps.py`

- **Statistic:** over 2,000 resampled paths: P(fail), P(funded within 90 / 180 days), median days to funded, the
  5th percentile of the 36-month maximum drawdown, P(a day <= -5 %), P(a losing streak >= 8), each at base risk
  1.0 / 1.25 / 1.5 / 1.75 / 2.0 %.
- **Inputs:** the four ledgers combined as the account trades them (`scripts/portfolio.py`: two open, the guard's
  worst-case refusals, 4H zones x2 on EURUSD/gold/NAS100, BTC x0.5, EURUSD's 1D+1H pair x0.5, the ladder
  -3 %: 1.0, -6 %: 0.5, FTMO costs); columns `opened_at`, `closed_at`, `r`, `poi_tf`, `bias_combo`, `symbol`.
- **Procedure:** resample calendar-month blocks with replacement (36 months a path; 2-week blocks as the
  sensitivity), re-date them consecutively, run the 2-Step from day 1 (phase 1 +10 %, phase 2 +5 %, 4 trading
  days each, fail at -10 % static or a -5 % day) and a 36-month funded replay; keep the seed.
- **Pass/fail:** the stake is the largest base risk with bootstrap P(fail) <= 5 % and the 5th-percentile 36-month
  drawdown shallower than -10 %; the historical path's numbers are reported beside it, never alone.
- **How:** needs code in `scripts/risk_steps.py`: `--bootstrap N --block month|2w --seed S`, resampling the
  combined ledger before `challenge()` (about 40 lines).
- **Pilot** (`research/mc_challenge.py`, without the two-open cap and the guard, so not the live number): the
  historical starts fail 15.6 % against 8.7 % on 1,500 month-block paths; funded within 90 days 42 % against 64 %;
  68 % of the paths hold a day <= -5 % at 1.5 % with the 4H double stake, exactly the case the live guard refuses,
  which is why the real run must go through `risk_steps.py`. Flat 1.5 % over 36 months: median max drawdown -14 %,
  5th percentile -21.7 %.

### A6. Parameter-plateau maps for every live knob (1-D, and 2-D for the pairs that interact)

- **Statistic:** for each knob, 5 values (live, +-1 step, +-2 steps), each a full backtest over 2024-2026 and
  2017-2023: R_live, the median and the minimum of the four neighbours, the plateau score = mean of the five; 2-D
  heat maps for min_rr x tp_fallback_rr (gold), min_gap_fraction x touch age (EURUSD, NAS100), be_at_r x min_rr
  (gold), tp_max_rr x min_rr (BTC).
- **Inputs:** the four profiles' numeric knobs: min_rr, tp_fallback_rr, be_at_r, min_gap_fraction, the 24 h visit
  and touch ages, the 24-candle zone age, min stop, spread_buffer_pips, session windows, the 30-minute news
  blackout, the 25 % limit offset and 4 h validity, max_hold_hours 48, tp_max_rr 3; one yaml copy per value (the
  `age_sweep.py` pattern), ledgers with `r`, `opened_at`.
- **Pass/fail:** R_live >= 0.75 x the neighbours' median and every neighbour positive in 2024-2026; when
  R_live > 1.33 x the neighbours' median the live value is a peak: move it to the plateau centre or keep it only if
  the 2017-2023 map shows the same shape. Steps and criteria are fixed before the runs.
- **How:** the backtest CLI with a yaml per value (a batch job; the `oct14b` set already covers 33 knobs, so the
  new part is the reading rule); results as a table in the README.
- **Pilot** (touch age, filter-based ledgers, after costs): EURUSD 12-48 h +25.1/+24.0/+24.0/+24.0/+24.0 (flat);
  gold +48.1/+48.8/+50.6/+46.7/+46.7 (plateau); NAS100 +27.5/+29.8/+29.8/+29.8/+28.7 (plateau); BTC +22.2 (12 h),
  +43.2 (18 h), +39.3 (24 h), +36.4 (36 h), +33.0 (48 h), +25.2 (none): BTC's 24 h sits on a slope and 18 h is a
  peak to distrust, not to move to.

### A7. A per-trade execution cost model instead of the flat 0.10R (spread by hour, commission, stop slippage)

- **Statistic:** cost_R = [spread(symbol, weekday, hour) + commission + slippage(exit type)] / |entry - stop| per
  trade; mean R after per-trade costs; the share of trades with cost_R > 0.10R; the p90 of cost_R.
- **Inputs:** `entry`, `stop`, `opened_at`, `closed_at`, `reason`, `lots`, `symbol`; the spread table from the FTMO
  terminal's tick history (`MT5Broker.spread_history`, which reads `copy_ticks_range`; the CLI's
  `spread_history_report` already samples a day's session windows): median and p90 per (weekday, hour) over the
  last 90 days, written to `spread_profile_<symbol>.json`. Commission: FTMO $3 a lot round turn on forex and gold,
  crypto 0.0325 % a side of the notional. Slippage: a stop fills at the open of the first 1-minute candle beyond it
  when a candle gaps through (news, the 23:00 break); a market entry at the next 1-minute candle's ask; a limit
  fills on a trade-through by one tick, not on a touch.
- **Pass/fail:** a market stays in the set when its mean R after per-trade costs >= +0.30R and >= 70 % of the
  flat-cost figure; a market with cost_R p90 > 0.25R gets a wider minimum stop before anything else is tuned.
- **How:** two knobs exist: `symbols.BTCUSD.commission_pct: 0.065`, `symbols.EURUSD.commission_per_lot: 3`,
  `symbols.XAUUSD.commission_per_lot: 3`, and `typical_spread_pips` set to the measured values (gold 3.5); the
  hour table and the gap-through-stop fill need code in `kronos_trader/execution/paper.py` (about 60 lines, the
  table looked up by the candle's weekday and hour).
- **Pilot** (ledger stop distances, FTMO's measured spreads and commissions): cost_R p50/p90 EURUSD 0.049/0.067R
  (the flat 0.10R is conservative: 2.1R true against 4.7R assumed); gold 0.045/0.107R, 12 % of trades above
  0.10R; NAS100 0.065/0.124R, 21 % above; BTC 0.178/0.447R, 83 % above, max 0.69R, 20.2R in total against the
  8.9R flat assumption: BTC's +70.6R gross is about +50R after true costs, not +61.7R (0.065 % of a $100k notional
  is about $65 against a $446 median stop, 0.15R from commission alone). The BTC hour that carries its result
  (09:00 Amsterdam: 15 trades, +42.7R of +70.6R) is pre-London, where crypto CFD spreads are not measured yet.

### A8. Random-entry and permutation baselines for the entry logic

- **Statistic:** p = share of 1,000 null runs with sum R >= the real sum R (and the z-score), per market and for
  the four combined, under two nulls: (a) direction: keep each real trade's entry time, stop distance, target
  distance, break-even rule and session, flip a fair coin for the direction; (b) timing: keep direction and
  distances, move the entry to a uniformly random 5-minute candle of the same session window on the same day
  (09-11 / 13-17 Amsterdam, the news blackout respected). Masters' third null, permuted 5-minute log returns through
  the whole engine, is the heavier follow-up.
- **Inputs:** `opened_at`, `direction`, `entry`, `stop`, `take_profit`, `poi_tf`, `confirmation_tf` per ledger;
  `scratchpad/fixed/<SYMBOL>_5min.csv` (and the BTC folders) for the exits, walked candle by candle with the stop
  first when both are hit in a candle.
- **Pass/fail:** p <= 0.05 per market on both nulls in 2024-2026 and p <= 0.01 for the four combined; a market
  with p > 0.20 on the timing null has no entry-timing edge, its result is the session plus the direction call
  (the README's own finding: "the edge, where there is one, is the direction call").
- **How:** a scratchpad script; no repository change.
- **Expected:** with a median planned R:R of 1.5-2.1 the coin-flip null's expectancy is about -0.1R after costs, so
  a real +0.5..+0.8R mean on 43-143 trades should sit at p < 0.01 if the entry carries information; the 2017-2023
  ledgers (mean R about 0) would not.

## 4. Process rules that follow (no code)

1. A candidate's pass criteria and its windows are written down before the run (A1-A8 each have one). The 2017-2023
   period is read once per candidate; the forward journal and the weekly parity check are the only holdout that
   regenerates.
2. Every backtest run counts as a trial: the provenance files give N; the README's result tables carry N, the
   block-bootstrap interval and the DSR at N beside each total.
3. A change is adopted when it passes A3 on both periods, the grid it came from passes A1, and the account replay
   passes A5 at the stake; the plateau map (A6) decides the value within the rule.
4. The live edge meter (last 20 / 30 trades) is kept; its thresholds (0R / -5R) can be read as a sequential test
   with the bootstrap distribution of A3 giving the expected spread of a 20-trade sum.

## 5. Sources

- Bailey, Borwein, Lopez de Prado, Zhu (2014), Pseudo-Mathematics and Financial Charlatanism: The Effects of
  Backtest Overfitting on Out-of-Sample Performance, Notices of the AMS 61(5): https://carmamaths.org/jon/backtest.pdf
  (also https://scholarworks.wmich.edu/math_pubs/40/)
- Bailey, Borwein, Lopez de Prado, Zhu (2017), The Probability of Backtest Overfitting, Journal of Computational
  Finance 20(4): https://papers.ssrn.com/abstract=2326253 ; https://escholarship.org/content/qt4w1110bb/qt4w1110bb.pdf
- Bailey, Lopez de Prado (2014), The Deflated Sharpe Ratio, Journal of Portfolio Management 40(5):
  https://papers.ssrn.com/abstract=2460551
- Bailey, Lopez de Prado (2012), The Sharpe Ratio Efficient Frontier, Journal of Risk 15(2):
  https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier ; the PSR formula and worked
  examples: https://www.quantconnect.com/research/17112/probabilistic-sharpe-ratio/
- Santoni, Jouanne, Scullin (2026), Equity Strategy Backtesting: Luck or Edge? The MinervaScore, arXiv 2608.23808
  (thresholds DSR >= 0.95, PBO <= 0.50, SPA p <= 0.10, T >= MinTRL): https://arxiv.org/html/2608.23808v2
- Harvey, Liu (2015), Backtesting, Journal of Portfolio Management 41(1):
  https://people.duke.edu/~charvey/Research/Published_Papers/P120_Backtesting.PDF
- Arnott, Harvey, Markowitz (2019), A Backtesting Protocol in the Era of Machine Learning, Journal of Financial Data
  Science 1(1): https://papers.ssrn.com/abstract=3275654
- Lopez de Prado (2018), Advances in Financial Machine Learning, ch. 7 (purging, embargo, CPCV); summaries:
  https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/ ;
  https://skfolio.org/generated/skfolio.model_selection.CombinatorialPurgedCV.html
- Pardo (2008), The Evaluation and Optimization of Trading Strategies (walk-forward analysis and efficiency);
  summaries: https://www.luxalgo.com/library/concept/walk-forward-analysis/ ;
  https://quantammsim.readthedocs.io/en/latest/tutorials/walk_forward_analysis.html
- White (2000) Reality Check; Hansen (2005) SPA: https://ideas.repec.org/a/oup/jfinec/v3y2005i4p606-628.html ;
  applied to trading rules: https://ageconsearch.umn.edu/record/19039/files/cp05pa01.pdf ; model confidence set in
  Python: https://arch.readthedocs.io/en/stable/multiple-comparison/generated/arch.bootstrap.MCS.html
- Politis, Romano (1994), The Stationary Bootstrap, JASA 89: https://gnosis.library.ucy.ac.cy/handle/7/57533
- Masters (2018), Testing and Tuning Market Trading Systems: Algorithms in C++ (Apress), ch. Permutation Tests:
  https://eld.bl.uk/catalog/019109628 ; interview:
  https://bettersystemtrader.libsyn.com/185-how-to-avoid-creating-trading-strategies-that-degrade-quickly-timothy-masters
- Randomisation tests, random-entry baselines: https://www.luxalgo.com/library/concept/randomization-tests/
- Monte Carlo trade resampling and risk of ruin: https://www.mql5.com/en/blogs/post/774072 ;
  https://backtrex.com/en/blog/probability-of-ruin-trading-monte-carlo ; https://www.luxalgo.com/library/concept/risk-of-ruin.md
- Parameter stability and plateaus: https://www.luxalgo.com/library/concept/parameter-stability/ ;
  https://harbourfrontquant.substack.com/p/overfitting-and-parameter-selection
- Fill and slippage models: https://nautilustrader.io/docs/latest/concepts/backtesting/fill-models/ ;
  https://ninjatrader.com/support/helpGuides/nt8/isfilllimitontouch.htm ; https://www.mql5.com/en/blogs/post/775565
- FTMO crypto pricing (commission 0.0325 % a side, 28 July 2025):
  https://ftmo.com/en/ftmo-enhances-crypto-trading-new-instruments-and-better-spreads/
- Gold spread behaviour by session and rollover: https://www.mql5.com/en/blogs/post/773690 ;
  https://dev.to/xauusdrobot/the-xauusd-spread-the-hidden-cost-that-quietly-decides-your-trading-results-574d

Pilot scripts and outputs in this folder: `stats1.py` (+ `stats1_out.csv`), `cscv.py`, `mc_challenge.py`; the
paper texts extracted for the formulas in `pdftxt/`.
