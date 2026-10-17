# What else there is to find: the six late angles, verified (14 October 2026, night)

Inputs: the six angle files written after the backlog stage (`metalabel.md`, `regime_gate.md`, `liquidity_map.md`,
`invariants.md`, `frequency.md`, `gold.md`) and their skeptic passes (`verify_metalabel.md`, `verify_regime_gate.md`,
`verify_liquidity_map.md`, `verify_invariants.md`, `verify_frequency.md`, `verify_gold.md`), read against
`BACKLOG_hand.md` (the afternoon's hand backlog, the reference for "new"), `BACKLOG.md` (the evening merge, which carries
the metalabel and regime angles as the unverified B11-B13) and `RESULTS_14oct.md` (the engine's own numbers). All under
`$S/research/`, `$S` = `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad`.

Conventions as everywhere today: R is after a flat 0.10R a trade unless marked raw; in sample (IS) = 2024-01..2026-09,
out of sample (OOS) = 2017..2023 (BTC 2020-06..2023); the research ledgers are the live profiles at 1 % units, guard off
(`aca/eutwo_EURUSD`, `aca/base_XAUUSD`, `aca/rr08_NAS100`, `aca/base_BTCUSD` and the `oos_` twins; 322 IS trades +206.0R,
698 OOS trades -76.3R). A rule counts only when it holds in both periods. Where the skeptic and the angle disagree the
skeptic's number is used and the reason is given at the item; every number below is from one of the files named above.

The verdict in one paragraph: nothing in the six angles changes a live profile during the challenge. What is new is
(a) what the trader should expect from the first weeks, in numbers; (b) a gold plan whose strongest new lever is the
fallback target distance, blocked until two engine runs settle the slot effect; (c) two out-of-sample insurance rules
for gold that need code and a decision; (d) a stake-by-planned-R:R lever for gold and NAS100 that needs code and a
replay; (e) seven chart elements that explain a trade without predicting it; (f) three small code items on the
backtester and the parity check; (g) a long list of negatives that close backlog lines. Of the 57 findings in the six
angles 3 are dropped outright, 24 are kept with a caveat and 30 reproduce as written (section 6 lists what was struck).

## 1. New beyond `BACKLOG_hand.md`, ranked by what it changes for the live set or the challenge

Actions use the house words: none / config after the challenge / code, off by default / chart / laptop / decision for
Max; "engine run" marks the backtest that must come first. "Touches the live path" means `live.py` or the watchdog,
which `BACKLOG_hand.md` A.6 reserves for after the challenge or Max's OK even when the change is a note.

| # | item (angle) | verified number, IS / OOS | action |
|---|---|---|---|
| 1 | **What the first weeks look like** (frequency 1-6, 8-9) | from any weekday start the four windows give a trade by the end of day 1 in 35 %, within 2 trading days (td) 55 %, a week 83 %, two weeks 95 %, a month 100 % (2026 starts 36 / 55 / 84 / 97 %; OOS 31 / 51 / 81 / 95 %); median wait 2 td, p90 8; the first trade comes from gold 50 %, BTC 23 %, EURUSD 13 %, NAS100 13 %; no EURUSD trade in two weeks 63 %, NAS100 56 %; the first five trades are negative 28 % of the time with the edge (OOS 56 %); +10 % median 40 d, both phases 84 d (2026 starts 19 / 34) | none for the profiles (section 2 is the text for Max); one reference line in the 22:05 report: "n trading days since the last trade (backtest median 2, 90 % within 8, longest 19), m since the last touch" in `kronos_trader/forward.py` `day_message` (the skeptic's location, not `live.py`): code, no profile change, touches the watchdog |
| 2 | **Gold: the fallback target at 3R or 3.5R, break-even 2.5R as the tie-break** (gold 4-5) | 5m walk, paired bootstrap against the ledger: 3.5R + BE 2.5 IS +18.5R [90 % CI +1.1, +35.4], P(<= 0) 0.04, OOS +27.1R [+6.2, +48.0], P 0.017; 3R + BE 2.5 +11.5R (P 0.09) / +23.7R (P 0.008); raw grid +97.6 / -2.0 and +104.6 / +1.5 against the ledger's +86.1 / -25.7; on the trades the ban and depth cut keep +101.6 / +10.0 and +106.1 / +8.5 against +95.2 / -8.2; of the trades that reach 2R before the stop 86 % / 78 % reach 3R, median MFE 7.0R / 6.0R; engine `tpfb3` (3R, BE 2) -0.1R IS / +21.5R OOS, the IS zero being six pushed-out trades worth +9.2R against +9.1R gained on 63 common trades | engine runs after `bd` (item 3): `bd` + `risk.tp_fallback_rr: 3.0` and `3.5` with `exits.breakeven_r_intraday: 2.5`, `breakeven_r_swing: 2.5` on `$S/q4_r26_XAUUSD_visit1h_full.yaml`, both periods, judged on the common-trade gain and the pushed-out trades' expected value, then `challenge_sim_set.py`; config after the challenge only if the engine holds in both periods |
| 3 | **Gold: the ban carries the stack, the depth cut is in-sample support; `bd` is the adoption pair** (gold 2) | 2 x 2 on the ledgers: banned-not-deep 28 trades -7.8R / 75 trades -20.0R (-0.28 / -0.27 a trade), deep-not-banned 14 trades -4.0R (p 0.021) / 18 trades +1.1R; on the engine ban ledger the depth cut adds +2.9R / +3.4R, but the OOS +3.4R is 24 trades at -0.14 a trade, the ban ledger's own average (p 0.52); engine singles ban +11.6R (124 trades, 53 %) / +18.7R (6 of 7 years), dep25 +3.1R / +11.0R; replay ban median 79 d vs 84, funded +6.3 vs +5.7 %/mo, 2024-25 within 3 months 45 vs 42 %, but 2026 starts within 6 weeks 66 vs 71 % | engine run `bd` (`session.windows [["09:00","10:00"],["13:00","15:00"],["15:30","17:00"]]` + `risk.max_entry_depth 0.25`, no 3R) beside the queued `ban10` / `ban15` / `dep20` / `dep30` of `BACKLOG.md` A4 / A8; config after the challenge at the earliest; with the 2026 slowdown the ban is a funded-account candidate in the house reading, the depth cut rides with it |
| 4 | **Stake by planned R:R on gold and NAS100; EURUSD dropped** (metalabel 3) | x2 at planned R:R >= 3 on the ledgers: gold +71.8 -> +109.7 / -62.2 -> -49.2 (24 / 57 trades doubled; subset-permutation p 0.002 / 0.020; beats a uniform multiplier of the same total risk, +83.9 / -71.8), NAS100 +32.9 -> +47.9 / +28.8 -> +62.1 (10 / 29; p 0.127 / 0.020), EURUSD p 0.571 / 0.214 and -16.0R OOS under the proposal's own cap at 1 % flat; the >= 3 band is 40 % / 19 % won at +1.81 / +0.37 a trade (55 of 322 IS trades make +99.7R of +206.0R); dips grow 20-60 % OOS; 1.5 % x 2 = 3 % a trade, 6 % with two open against the 5 % day | code, off by default: `risk.planned_rr_risk_multiplier: {3.0: 2.0}` as one more `mult *=` line in `setup_risk` (`strategy/risk.py` 272-293), the combined multiplier capped at 2.0 and inside the guard's worst-case check; the backtester rerun with the ladder for gold and NAS100 only (`BACKLOG.md` B13 rescoped); then decision for Max |
| 5 | **Gold's 4H zones at x2 have no out-of-sample support** (gold 6) | IS 13 trades, 62 %, +1.08 a trade, +14.1R; OOS 48 trades, 25 %, -0.24 a trade, -11.5R (the 1H zones -0.16); ledger x1 / x1.5 / x2 IS +71.8 / +78.9 / +85.9, OOS -62.2 / -68.0 / -73.7 (dips -83 / -90 / -96R); neither period separates the bucket (p 0.12 / 0.38); the replay is mixed: x1 against x2 both-phases median 77 vs 84 d, 2024-25 within 3 months 47 vs 42 %, phase 1 47 vs 40 d, 2026 six weeks 69 vs 71 %, funded +5.3 vs +5.7 %/mo; the pooled README figure for 4H zones OOS rests on EURUSD 10 and NAS100 7 trades | decision for Max, config only (`risk.zone_risk_multiplier: {}` or `{4H: 1.5}` in `config/dorus_live_gold.yaml`); the three-market x1.5 of `RESULTS_14oct.md` (median 77 d, 2026 six weeks 74 %, worst month -3.8 vs -4.2 %) is the same question; the data cannot choose between x1, x1.5 and x2 |
| 6 | **Gold: no trade against the 4H 50-candle mean, out-of-sample insurance** (regime 1) | against the mean: IS 18 trades, 33 %, +0.5R (2024 +3.1, 2025 -0.3, 2026 -2.3; about 4R at the live stakes because the two removed 4H-zone trades are +7.0R at x2); OOS 67 trades, 18 %, -30.3R, negative in 7 of 7 years, a plateau of -22.6 to -35.7R at every mean length 4H x 40-120; ledger OOS -62.2 -> -31.9R, dip -83 -> -55R; the IS neutrality is the cheapest of 17 definitions (1D x 20 costs +12.8R) and the existing `bias.trend_filter_days` cannot substitute (+13..+26R IS cost at N 3-20); replay OOS both phases 11 -> 20 %, IS median 84 -> 97 d, 2026 six weeks 71 -> 67 % | code, off by default (`bias.trend_filter_4h_candles: 50`, about 10 lines beside `trend_filter_days`, `engine.py` 468-477, closed 4H candles only) + engine rerun in both periods; decision for Max for the funded account, not for the challenge (`BACKLOG.md` B11's house verdict stands) |
| 7 | **Gold at half stake when the daily ER20 < 0.2, second insurance** (regime 2) | the bucket: IS 59 trades, 47 %, +19.6R (p 0.18: not below the base), OOS 169 trades, 24 %, -61.4R (p 0.012); half stake IS +71.8 -> +62.0R (dip -9.0 -> -6.6), OOS -62.2 -> -31.5R (dip -83 -> -51); the 0.25 line costs 11.1R more IS for 0.5R more OOS; replay 2026 six weeks 71 -> 57 %, OOS 11 -> 13 %; stacked on item 6 OOS -12.2R, IS six-week passes 47 % | code, off by default (`risk.regime_risk_multiplier {er20_below: 0.2, multiplier: 0.5}`, ER20 of the last 21 closed daily closes handed to `setup_risk`); decision for Max after item 6, if at all (`BACKLOG.md` B12); a restatement of `market_XAUUSD.md` candidate D on closed-bar labels |
| 8 | **Seven chart elements** (liquidity map 2-10; section 4) | yesterday's high/low are computed (`chart_context`) but skipped on the setup chart (`live.py` 1019) while in the picture 88 / 92 % of the time; the Asia extreme is in the picture 98-99 % (stop side 72-79 %); the break level 100 %; the nearest resting swing 87-89 % and on the target 26 / 22 %; fresh opposing zones hidden by `chart_zones`; the stop sits on the sweep extreme in 100 % of non-widened trades; no four-market rule in 99 qualifying buckets (1 both-negative, dropped) | chart: code in `live.py` `send_chart` / `notify/chart.py`, one engine line (`self.last_structures`); no profile change; touches the live path, so with Max's OK or after the challenge |
| 9 | **Backtester defect: a resting limit fills after its expiry across a closure** (invariants 4) | 1 of 1,339 limit fills: `oos_rr08_NAS100` P40, Memorial Day 2020, signal 13:15, last candle 16:55, fill at the 22:00 reopen (530 min after the signal, -1.0R); the next-longest lag is 235 min; `runner.py` 173-187 tests `filled` before `expires`; live cancels at the first scan past `expires_at` (`live.py` 1745) and MT5 carries expiry + 10 min | code (2 lines in `_work_limit`: refuse when `pd.Timestamp(candle.timestamp) >= pending["expires"]` before the fill test, the skeptic's form; identical ledgers on all 58 runs but that trade); a bug fix, so the both-periods rule does not apply |
| 10 | **The weekly parity check will flag a false "NOT identical" after a knob-adding pull** (invariants 7) | the same yaml recorded by fc476b22 and 2e6dca1e: sha db3f89ef vs 491886fe, 17 keys added at their defaults, 0 shared values changed; `parity.py` 767-771 prints "NOT identical" on any difference; the trigger is the week a restart pulled such a commit (the start scripts pull, `parity_week.bat` does not) | code, laptop-facing: in `parity.py` classify a diff whose keys are all "(absent)" on one side as "identical apart from N knobs the newer code added at their defaults"; keep the full hash (the angle's non-default-only hash is blind to a changed default, which is what the check exists to catch); the first restart after the laptop pulls the 14 October commits will show it |
| 11 | **"No-op" is decided at trade identity, not by the R sum** (invariants 5) | four of `RESULTS_14oct.md`'s "+0.0R (+0 tr)" variants changed trades: `be3_EURUSD` 4 final_stop values, `ms100_BTCUSD` P35 (stop 66,991 -> 66,983, lots 9.65 -> 8.99, exit one candle later), `swp_BTCUSD` P17, `swp_NAS100` P17; six other pairs identical column for column across three code revisions; `oct14b/eval.py` prints R statistics only | code (scripts): a trade-identity line (rows differing in opened_at, entry, stop, take_profit, exit) beside the delta in `eval.py` / `backlog_eval.py` |
| 12 | **Gold's out-of-sample loss is 2018-2022's low-volatility gold, not more ranges; today's state** (gold 1, regime 9) | 2018-2022 -73.4R (2017 -3.6, 2023 +14.8); days under ER20 0.2 50 / 49 / 51 % per block, median daily ATR% 0.98 / 1.34 / 1.54, days over 1.433: 9 / 39 / 62 %; ATR% < 1.08: OOS 157 trades -34.1R (p 0.29), IS 11 trades +8.0R, 0 in 2026; ATR% > 1.433: OOS 86 trades -0.02 a trade; 2017-19 median stop 22 pips, a 3.7-pip spread 18 % of R (-35.9 -> -50.7R); today (14 Oct, closed bars) gold's 4H close 4083.6 vs the 50-mean 4152.2 (-1.65 %, under one daily ATR of 1.82 %), ER20 0.166 | none: an ATR% figure beside ER20 in the morning regime line is its only use; a per-signal note that both unadopted gold rules (items 6-7) would be active this week, which the house verdicts on B11 / B12 decide, not the state |
| 13 | **Resting limits fill inside news blackouts, by design** (invariants 10) | 108 of 1,339 limit fills (8 %) land inside the 30-minute window; on the live ledgers 13 trades, 3 won, +5.4R IS / -4.0R OOS; live does the same (`live.py` 1745 cancels only on expiry or the target trading first) | none: a fact for whoever reads the journal, so a fill during news is not taken for a bug; it bears on `BACKLOG.md` B1 (funded Standard), where cancelling costs +1.4R net over 13 trades |
| 14 | **The gold research yamls should carry the live spread and the cap** (gold 3; confirms hand A.5 / `BACKLOG.md` A2) | `sp37`: IS -11.6R (spread on the common trades -7.3R, 3 trades swapped), OOS -0.4R; the cap at 3.7 / 0.3 = 12.3 pips refuses 30 OOS stops (20 % won, -14.0R, negative in each of 2017-2020) and 0 IS (the smallest IS stop 17 pips); `runner.py` 301-311 applies the cap in the backtest since 14 October (the profile comment "live only" is stale) | research yamls only (`symbols: XAUUSD: {typical_spread_pips: 3.7}`, `risk.max_spread_stop_fraction: 0.3`); future gold deltas are measured against `sp37`, not `base`; no live change |
| 15 | **Negatives that close backlog lines** (all six angles) | meta-labeling 1 of 240 cuts passes both periods against 0.66 of 40 for random cuts, IS CV AUC under 0.5 in 25 of 30 cells, detection bars 0.61-0.70 (150-400 trades a market needed); context features pooled CV AUC 0.477 / 0.471; ATR14 percentile, the week's range and pace, the weekday of formation / touch / fill, BTC regime on UTC and NY candles (every IS bucket positive, every OOS bucket negative), NAS100 ER20 >= 0.5 (7 / 10 trades); equal highs/lows (in 6-16 % of pictures), last week's extremes, the break-level distance (Spearman +0.007 / -0.003), the Asia range on four markets, sweep = day's / window's extreme, untested zones in the path; BE 1 / 1.5 / 3R on gold (IS +57.0 / +76.2 / +84.1 raw against +86.1), the 1H-swing trail (+75.6 / -32.7 against +86.1 / -25.7), a 20-pip or ATR stop floor (92 OOS trades -24.2R against 2 IS -2.2R), every session slot beyond the ban (09:00-10:00 +17.6 / -8.4R, 14:30-17:00 +26.4 / -19.8R); the more-trades sets (`eum15` +41.6 / -22.8R, academy EURUSD -36.3R); the month of the year | none; not to be rerun (one line each in the README's negative table) |
| 16 | **Observations for other angles, not rules** (regime 8, liquidity 5-6, 10) | NAS100: no trend filter (counter-trend trades OOS +34.1R on 22, IS +0.80 against +0.75 a trade on 10: an OOS-only edge), the target on a resting swing +1.39 / +0.95 against the rest on 10 / 28 trades, the sweep = the window's extreme +0.83 / +0.78 on 22 / 54; EURUSD: the Asia-inside rule of the EURUSD angle reproduces EURUSD-only (inside IS 20 trades 25 % +0.40 against ahead 25 at 64 % +1.36; OOS 54 at 24 % -0.08 against 40 at 30 % +0.40), gold's inside entries are the better ones in both periods (+0.72 / +0.11 against +0.45 / -0.22) | none |
| 17 | **Exit stamps carry the exit candle's open** (invariants 8) | 214 of 5,421 rows have closed_at == opened_at; 5,377 of 5,410 broker exits traded through the level only in the candle opening at closed_at; the true exit is 0-5 minutes later; R and P&L untouched; the BTC paper window's journal inherits it | none now (a 3-line `on_candle(close_ts)` change would move the `max_hold_hours` / `time_stop` clocks by one candle and needs the NAS100 48 h ledgers rerun) |
| 18 | **BTC's anchoring changes the R, not the rhythm** (frequency 9; hand A.1 for the R) | on the NY-anchored ledger (94 trades +33.3R against 89 +70.6R) BTC's first trade comes a median 6 td after a start (UTC 7), the four together 36 / 57 / 85 / 97 % by 1 / 2 / 5 / 10 td; challenge medians 42 / 82 d against 40 / 84; 7 of 651 starts unfinished (March-April 2024), not one | none: the expectation tables of section 2 stand whatever A.1 decides |

Where the skeptic and the angle disagree, and whose number this page follows:

- Item 2: `gold.md` reads the engine's `tpfb3` zero as structural non-additivity ("a 3R trade holds gold's one slot
  and pushes the next entry out"); `verify_gold.md` 3 shows the pushed-out six IS trades were worth +9.2R (+1.5R a
  trade against a +0.5R ledger average) while the common 63 trades gained +9.1R, and that on the walk the target pair is
  beyond paired-bootstrap noise in both periods. The skeptic is followed: the slot effect is real, its in-sample size
  is a six-trade accident, so the engine runs are judged on the common-trade gain plus the expected value of what gets
  pushed out, not on the sum. The break-even at 2.5R changes 6 IS / 10 OOS trades for +2-3R / +4.5-5.5R (P(<= 0)
  0.19-0.41): set with the target, one engine run at 2.5, no comparison run.
- Item 3: the angle says the depth cut "adds about 3R in both periods on top of the ban"; the skeptic shows the OOS
  increment is 24 trades at the ban ledger's own average (p 0.52), so the depth cut's both-period claim is a sum, not
  an edge, once the ban is in (in sample 15 trades at -0.19 a trade against +0.67, p 0.021). Followed: the order
  (ban, then depth) stands, the depth cut is presented as in-sample support.
- Item 4: the angle proposes the stake on EURUSD, gold and NAS100; the skeptic's permutation test puts EURUSD at
  random (p 0.571 / 0.214) and flips its OOS sign under the cap variant (+5.8R on the live chain, -16.0R at 1 % flat).
  Followed: EURUSD out, NAS100 in on its OOS leg with 10 IS trades behind it, gold the market with both periods.
- Item 5: the angle says x1 "passes as often, 7 days faster"; the skeptic's reading of the same replay table is mixed
  (faster on two columns, slower on three). Followed: a stake choice the data cannot make.
- Item 6: the angle says "no in-sample cost in R"; the skeptic shows +0.5R is the cheapest of 17 mean definitions and
  about 4R at the live stakes, and that the OOS p 0.036 is one of 32 gold buckets scanned. Followed: the robust part is
  the OOS plateau (7 of 7 years at every length); an insurance rule, not an edge.
- Item 16: the angle calls NAS100's counter-trend trades "its edge in both periods"; the skeptic shows IS +0.80 against
  +0.75 a trade on 10 trades (p 0.87 on the 4H-50 bucket). Followed: OOS-only; the actionable half (no trend filter on
  NAS100, README 844) stands.
- Items 9-10: the angle's rule forms (`now >= expires` first; a non-default-only settings hash) are replaced by the
  skeptic's (the expiry tested on the candle's open, which matches what live can still fill; the full hash with the
  diff classified), for the reasons in the table.

## 2. What the trader should expect in the first weeks (the frequency tables in plain words)

All from the four research ledgers (714 weekdays in sample, 33 months; 1,825 out of sample) and the touch replay of
the live profiles over 2024-2026 (`verify_frequency.md` reproduces every table).

**No trade on day one or day two is the median case.** From the start of any trading day the four windows together
produce a trade by that day's close 35 % of the time, within two trading days 55 %, within three 69 %, within a week
83 %, within two weeks 95 %, within a month always. The 2026 starts (36 / 55 / 68 / 84 / 97 %) and the 2017-2023
starts (31 / 51 / 64 / 81 / 95 %) say the same: the rhythm does not depend on whether the edge is there. A Monday
start is the slowest: 29 % by Monday's close, 50 % by Tuesday's, 66 % by Wednesday's, 83 % by Friday's, 95 % by the
second Friday. The challenge started on Monday 13 October, so by the close of Wednesday 15 October the backtest gives
two chances in three of a first trade, by Friday 17 October five in six, by Friday 24 October nineteen in twenty, and
by 10 November (20 trading days) every start in both periods had traded. In calendar days: median 1.6 days to the
first trade, 90 % within 9.3 days.

**The first trade comes from gold.** Gold trades 4.3 times a month (on 19 % of trading days, 3 % of months empty),
BTC 2.7 (18 % of months empty), EURUSD 1.4 (36 % of months empty), NAS100 1.3 (39 %); out of sample 4.4 / 3.0 / 1.2 /
1.2, in 2026 4.2 / 2.0 / 1.4 / 1.8. The first trade after a random start is gold's 50 % of the time, BTC's 23 %,
EURUSD's 13 %, NAS100's 13 % (2026 starts: gold 53 %, NAS100 22 %, BTC 15 %, EURUSD 10 %; out of sample gold 64 %).
Per market the median wait is gold 4 trading days, BTC 7, NAS100 12, EURUSD 15 (p90 14 / 28 / 53 / 38). The chance of
no EURUSD trade at all in the first two weeks is 63 % (2026 61 %, OOS 67 %), of no NAS100 trade 56 % (40 %, 62 %), of
no BTC trade 38 %, of no gold trade 16 %. EURUSD and NAS100 are silent for weeks by design, not by fault: 12 of 33
months had no EURUSD trade and 13 none on NAS100.

**The heartbeat is the touch message, not the trade.** The four windows send about 35 "waiting for a confirmation"
touch notices a month (8-9 a market) on 61 % of trading days; this is a floor, because the replay looks only at 5m
closes and never repeats a zone while the live window repeats a zone still in play after a restart. From a start,
61 % see a touch on the first day, 81 % within two trading days, 96 % within a week, 100 % within two weeks (2026
starts 55 / 73 / 95 / 100 %). A confirmed setup (the shift closed, before the guard and the fill checks) comes 12.1
times a month on 37 % of trading days: 57 % of starts see one within two trading days, 84 % within a week, 96 % within
two weeks; 77-81 % of signals become trades (the rest: the guard, an expired limit, the R:R or the spread at the
fill). Which touch to take seriously: a gold 1H touch confirms on that zone within 24 hours 45 % of the time, a BTC 1H
touch 26 %, NAS100 16 %, EURUSD 15 %, a 4H touch 6-19 %. Two weeks without a single touch message would be outside
everything the backtest did; two weeks without a trade is 5 % of starts.

**How much the first two weeks bring.** Mean 4.5 trades (10th percentile 1, 90th 8); none at all 5 % of starts (2026
3 %, OOS 5 %), one 10 %, two 12 %, three or more 74 %. The first week alone: 2.3 trades on average, none 17 % (2026
16 %, OOS 19 %). FTMO's four trading days with a trade take a median of 11 trading days, 90 % within 20 (2026 10 and
17; OOS 13 and 24). The opens fall 36 % in the 09-11 window and 60 % in 13-17 Amsterdam, so most first-week messages
come in the afternoon; a trade is open a median 1.8 hours, 90 % under 21.5 hours.

**Dry spells.** Between two trades the set is quiet a median 1 trading day (p90 5, p95 7 in sample; 6 and 8 out of
sample). A spell of ten trading days or more without a trade comes 2.5 times a year in both periods (7 in 2.83 years,
18 in 7.24; strictly more than ten: 1.8 and 2.1 a year); the longest in sample was 19 trading days (24 July-21 August
2025), out of sample 23 (April-May 2023, partly a data hole). A window that scans, sends its morning check and its
touches and takes no trade is doing what the backtest did on 65 % of its trading days.

**The first trades cannot say whether it works.** At the live multipliers and after costs the first trade loses 49 %
of the time with the edge intact (OOS 65 %); the first three together are negative 32 % (57 %), the first five 28 %
(56 %; median +1.7R against -0.7R, 10th percentile -2.8R against -4.0R), the first ten 15 % (58 %; median +6.2R against
-0.8R). The fifth trade closes a median 14 days after the start (OOS 18), the tenth 30 (39). So one start in four is
still under water after two weeks and five trades even when the edge is there, and one in two when it is not: five or
ten trades do not separate the two cases. The instrument is the edge meter already in the 22:05 report (R of the last
20 and 30 closed trades, a warning under 0R over 20 or under -5R over 30), which at 9.8 trades a month is two to three
months away; the reference line of item 1 puts the wait against its backtest distribution in the same report.

**The pace.** Over all 2024-2026 starts +10 % took a median 40 days and the funded account 84 (90th percentiles 195 and
244); the 2026 starts did it in 19 and 34 days, the 2024 starts in 54 and 91, the 2025 starts in 58 and 131. A pass
within 14 days is 15 % of all starts (33 % of the 2026 starts); +10 % within a month 42 % (2026 82 %); both phases
within two months 38 % (2026 97 %). The slow starts are January-May 2024 (a median 4.3-8.5 months to +10 %) and
April-October 2025 (1.6-5.8 months to +10 %, 4.0-9.2 months to the funded account: the set first lost and then earned
the loss back). October starts took 15 days in 2024 and 96 in 2025: the month says nothing, the regime does. The
flat-cost replay fails no start; the README's replays with FTMO's measured costs lost 1-4 % of the 2024-25 starts
depending on the stake and set, so "0 % failed" means the limits are never hit at flat costs, not a guarantee. Budget
three months for +10 % and four for the funded account as the base case.

**Nothing to pull for more trades.** The two sets that add trades raise the chance of a trade in the first two days
from 55 % to 58 % (EURUSD 15m zones, 2017-2023 -22.8R on 71 trades) and 67 % (the academy's literal rules, -187.8R in
sample), pass no faster and lose more months; the month of the year carries nothing out of sample (40-59 % within two
trading days in every month). The profiles stay as they are.

## 3. The gold plan

Gold is the window that trades (4.3 a month; the first gold trade a median 4.6 days after any start, 75 % within 9.6,
90 % within 18.5) and the one with a both-period story on three rules. Ranked, with the skeptic's caveats in, each
config only and each after the challenge unless marked:

| rank | change | knob | IS / OOS | replay | status |
|---|---|---|---|---|---|
| 1 | no entry 10:00-11:00 and 15:00-15:30 Amsterdam | `session.windows: [["09:00","10:00"],["13:00","15:00"],["15:30","17:00"]]` | engine +11.6R (124 trades, 53 %, dip -7.9R; 2024 +10.1, 2025 -1.7, 2026 +3.2) / +18.7R (6 of 7 years, 2022 -9.3); per trade the banned bucket is -0.28 / -0.27 against +0.88 / -0.13 for the kept; its weight is the 10:00 hour (21 / 66 trades, -5.9 / -22.1R), the 15:00 half-hour 11 / 20 trades (-3.7 / -6.9R) | median 79 against 84 d, funded +6.3 against +5.7 %/mo, 2024-25 within 3 months 45 against 42 %, 2026 six weeks 66 against 71 %; 3.8 instead of 4.4 trades a month, the first gold trade a median 5.5 days (90 % within 21.5) | the one gold rule with both-period evidence per trade; `ban10` / `ban15` (`BACKLOG.md` A4) attribute it; config after the challenge, and a funded-account candidate first because of the 2026 slowdown |
| 2 | entry at most a quarter of the zone deep | `risk.max_entry_depth: 0.25` | engine alone +3.1R (2024 +2.1, 2025 +4.2, 2026 -3.2) / +11.0R; on top of the ban +2.9R (15 trades at -0.19 a trade, p 0.021) / +3.4R (24 trades at the ledger average, p 0.52); per year on top of the ban better in 6 of 10 | dep25 alone: median 76 d, 2024-25 46 %, 2026 six weeks 71 %, +5.8 %/mo | in-sample support with an out-of-sample that neither helps nor hurts per trade; second, with the ban; `dep20` / `dep30` (A8) say whether 0.20-0.30 is a plateau |
| 3 | gold's 4H zones at x1 or x1.5 | `risk.zone_risk_multiplier: {}` or `{4H: 1.5}` | x1 gives up +14.1R of multiplier gain IS and takes back -11.5R and 13R of dip OOS; the bucket is 13 trades IS (p 0.12) and 48 OOS (p 0.38) | x1 against x2: both-phases median 77 against 84 d, 2024-25 within 3 months 47 against 42 %, phase 1 47 against 40 d, 2026 six weeks 69 against 71 %, funded +5.3 against +5.7 %/mo, worst month -3.8 against -4.2 % | decision for Max; a multiplier changes no trade, so whether it counts as a profile change during the challenge is his call; "7 days faster" is not a claim this page makes |
| 4 | the fallback target at 3R or 3.5R, break-even 2.5R with it | `risk.tp_fallback_rr: 3.0` or `3.5`, `exits.breakeven_r_intraday: 2.5`, `breakeven_r_swing: 2.5` | walk (raw) +97.6 / -2.0 and +104.6 / +1.5 against +86.1 / -25.7; paired bootstrap 3.5R + BE 2.5 +18.5R (P 0.04) / +27.1R (P 0.017), 3R + BE 2.5 +11.5R (P 0.09) / +23.7R (P 0.008); better than the ledger in 9 of 10 years (2026 -0.5R); engine `tpfb3` -0.1R / +21.5R with the slot effect | not yet | the strongest both-period lever after the ban on the walk; only after the engine runs `bd` + 3R / 3.5R + BE 2.5 (both periods, judged on the common-trade gain), then the replay |
| 5 | the research yamls carry the live spread and the cap | `symbols: XAUUSD: {typical_spread_pips: 3.7}`, `risk.max_spread_stop_fraction: 0.3` (research yamls only) | `sp37` IS -11.6R / OOS -0.4R; `stack37` against `stack` -3.4 / -2.8R | | hygiene so the ledgers say what the account pays; the IS research ledger then reads 11.6R lower and every later gold delta is measured against `sp37` |
| 6 | the out-of-sample insurance: no trade against the 4H 50-mean, then half stake at ER20 < 0.2 | `bias.trend_filter_4h_candles: 50`; `risk.regime_risk_multiplier {er20_below: 0.2, multiplier: 0.5}` (both new code, off by default) | the trend gate removes 18 IS trades worth +0.5R (about 4R at the live stakes) and 67 OOS trades worth -30.3R (7 of 7 years); the ER20 half stake IS -9.8R / OOS +30.7R; together OOS -12.2R | trend gate OOS both phases 11 -> 20 %, 2026 six weeks 71 -> 67 %; ER20 half 2026 six weeks 71 -> 57 %; together IS six-week 47 %, OOS 25 % | decision for Max for the funded account, after an engine rerun of the trend gate; not for the challenge; the ER rule only after the trend gate, if at all |

What to leave as it is: the break-even at 2R while the fallback is 2R (BE 1R / 1.5R cost 29 / 10R IS and 41 / 14R OOS
raw; 2.5R, 3R and none are within 2R IS and 1-6R worse OOS; the 2R rule changes 2 IS and 14 OOS trades); the 8-pip
minimum and the cap at 0.3 (no IS stop under 17 pips, the cap refuses 30 OOS stops worth -14.0R, a 20-pip floor is
OOS-only: 92 OOS trades -24.2R against 2 IS -2.2R); every session slot beyond the ban (the London open 09:00-10:00
+17.6R in 3 of 3 IS years and -8.4R in 6 of 7 OOS years; the US session 14:30-17:00 +26.4 / -19.8R; 13:00-14:30
+33.8 / -11.9R); the month-at-50/50 half stake (OOS 106 trades -6.5R, IS 11 trades -1.4R, neutral); the 1.5 % stake and
the ladder (not gold's to decide). Nothing during the challenge.

What the engine must still measure, one at a time, both periods, then `challenge_sim_set.py`: (1) `bd` = the ban +
`max_entry_depth 0.25` without the 3R (expected IS about +85R, OOS about -31 to -40R); (2) `bd` + `tp_fallback_rr 3.0`
+ BE 2.5 and `bd` + 3.5 + BE 2.5 (walk on the kept trades +101.6 / +10.0 and +106.1 / +8.5 raw), read as above; (3) the
gold yamls at 3.7 pips with the cap; (4) the trend gate in the engine (item 6) when Max wants the insurance read.
Not worth a run: break-even 1 / 1.5 / 3R, a BE 2 against 2.5 comparison, the 1H-swing trail (-10R IS on the ledger's
targets, better in 2 of 10 years), a 20-pip or ATR-based stop floor, a session rule beyond the ban, a hard ER20 or ATR%
gate (the half-stake versions stay the only regime candidates and need code), a volatility gate (ATR% < 1.08 holds
11 IS trades).

Where the loss lives, for the morning line: the 2017-2023 loss is 2018-2022's (-73.4R), low-volatility gold (median
daily ATR 0.98-1.34 % of price against 1.54 % since 2024; days over 1.43 %: 9 / 39 / 62 % per block); in the
low-volatility bucket the bot is -34.1R on 157 OOS trades and has had 11 trades since 2024, none in 2026; in the
high-volatility bucket it was flat out of sample (86 trades, -0.02 a trade) and +0.50 a trade in sample. The share of
trades taken in ranging days (ER20 < 0.2) is the same in both periods (41 % / 46 %); what differs is what a range is
worth. Today's state (14 October, closed bars): the 4H close 1.65 % under its 50-candle mean, ER20 0.166, daily ATR
1.82 %. In the ledgers that state (ER20 < 0.2 and a long against the mean) is 8 IS trades +2.3R and 22 OOS trades
-7.8R; a short with the mean 15 IS trades +8.6R and 76 OOS trades -35.0R. The state can flip within days (1.65 % is
under one daily ATR); it is a per-signal note, not a weekly stance, and the rules it would trigger are not adopted.

## 4. The chart elements to add, and why

The finding behind all of them: none of the eight liquidity elements carries a four-market rule that holds in both
periods (99 qualifying buckets, one both-negative, and that one is a EURUSD subset of a rule the EURUSD angle already
has). The apparent rules are planned-R:R effects: a target inside the day's range so far wins 58 % at +0.56 a trade
against 46 % at +0.86 for a target that needs a new extreme, because the first has a mean planned R:R of 1.70 and the
second 3.32; within R:R bands the sign turns (-0.21 IS / +0.17 OOS). So the chart explains the trade, it does not grade
it, and the labels must not read as a verdict. In order of value (`live.py` `send_chart` -> `notify/chart.py`
`render_chart(series, pois, setup, extra_lines=[(price, label, from_ts)], extra_boxes=[(low, high, label)],
shade_spans)`; the axis is set from candles, setup, zones and the last price only, so an off-axis line is invisible and
never stretches the picture):

1. **Yesterday's high and low on the setup chart.** Already computed by `chart_context` for the context chart and
   skipped on the setup chart (`live.py` 1019: `extra_lines, spans = self.chart_context(...) if setup is None else
   ([], [])`); `dorus_review` 1420-1422 passes none either. In the picture on the target side 88 / 92 % of the time
   (5m charts 89 %, 15m 99 %), on the stop side 20 / 21 %; median 1.5R ahead of the entry. It shows whether the target
   needs a new day extreme or lies inside yesterday's range. One-line change. Note for BTC: the research days are
   UTC-anchored while the live `closed_daily` is the broker's 17:00 New York day, harmless for a chart.
2. **The Asia range (00:00-08:00 Amsterdam) as two lines from the left edge**, "Azië high / low 00-08". In the picture
   98-99 % on the target side, 72-79 % on the stop side; the range's hours lie on the chart in only 25 % of the 5m
   charts, so lines, not a box. It makes the EURUSD angle's inside-the-range rule visible at a glance (EURUSD inside
   25 % / 24 % won against 64 % / 30 % ahead) and shows a sweep that took the Asia low. On gold the inside entries are
   the better ones in both periods, so no four-market reading.
3. **The sweep extreme, marked and named, and the stop label extended.** The stop sits exactly on the sweep extreme in
   100 % of non-widened trades on all four markets (`sl_offset_pips: 0.0`); the rest were widened to the minimum (8
   pips EURUSD and gold, 12 points NAS100, $60 BTC): EURUSD 36 % / 28 % of its trades, gold 0 / 2 %, NAS100 0 / 35 %,
   BTC 0 / 13 %. Labels: "SL = sweep" when on it; "SL 8 pips (sweep 5.2 pips)" when `setup.notes` carries "moved out
   from ... to the 8-pip minimum" (`risk.py` 463), the one case that loses on EURUSD (24 % / 15 % won, -0.02R /
   -8.9R); "= sessie-low / dag-low" when the sweep is the window's or the day's extreme so far (with the proper 09:00
   / 13:00 windows that is 52 % / 51 % of sweeps pooled: EURUSD 32 / 63 %, gold 57 / 47 %, NAS100 51 / 54 %, BTC
   55 / 48 %; the day's extreme 8-28 %). Neither sorts the outcome stably (day's extreme +0.48 / -0.32 against the
   rest).
4. **The break level** (`setup.confirmation.break_level`): a dotted line from the confirmation candle, "B-level
   (shift door ...)". Rebuilt for 100 % of trades, always in the picture, the entry within a quarter ATR of it in
   43-44 % of trades; carries no information (Spearman of R on the distance +0.007 / -0.003), which is why the limit
   on it gained nothing on 8-9 October. It is the balance shift the trader looks for.
5. **Resting liquidity on the zone timeframe ahead of the entry**: the engine's `StructureAnalysis.levels` on the
   target side between the entry and one reward past the target, at most the nearest three, labels "liq 1H" and "liq
   1H x2" for equal highs/lows (`touches >= 2`). The nearest resting swing is in the picture 87-89 %, median 1.9R
   ahead; it sits on the target in 26 / 22 % of trades and just past it in 15 / 14 %. The target-on-a-swing bucket is
   the only one better in both periods within R:R bands (+0.10 / +0.13) and it is a NAS100 effect (+1.39 / +0.95 on
   10 / 28 trades) with EURUSD reversed (-0.46 / -0.43): a picture, not a rule. Smallest change: `Analysis` carries no
   structures (`types.py` 384), the engine builds them inside `analyze` (`engine.py` 379), so keep `self.last_structures`
   on the engine and pass the levels as `extra_lines`.
6. **Fresh opposing zones in the path or within one reward beyond the target**, as dashed grey boxes labelled
   "ongetest 1H supply". `analysis.pois` has them; `chart_zones` keeps only the bias direction once tradable
   (`live.py` 1053). 7 % of trades have one just beyond the target (OOS 22 % won, -0.27 a trade; IS at the base) and
   7 % one in the path (21 / 37 trades, the R two outliers). Nothing to act on; worth seeing.
7. **Last week's high and low** from the weekly view: in the picture 41 / 40 % (stop side 3-4 %), median 3.9R ahead,
   every bucket's sign turns between the periods. Lowest priority, harmless.

Not worth drawing: the day's range so far as lines (the candles show it), the Asia range's height, the number of
swings in the path (a count), equal highs/lows as a class (a 0.1-ATR pool within one reward of the trade exists in
6-8 % of trades, 0.25 ATR in 15-16 %; a pool in the path is better in both periods on 7-24 trades, too few to say
anything). Everything above changes no trade; it touches `live.py`, so it goes in with Max's OK or after the
challenge, together with the report line of item 1.

## 5. What the invariants say about trusting the backtester

What holds, by test rather than by reading:

- **Append-only invariance.** The EURUSD live profile run to 30 June 2026 against the run to 24 September: 44 = 44
  trades, all 45 shared columns identical to exact float equality, 186,328 equity bars matched with a maximum
  difference of 0.000000, counters 56 / 44 / 5 against 61 / 47 / 5 with the two extra refusals after June; and the two
  runs come from different code revisions (17 knobs added at their defaults, 0 shared values changed), so the 14
  October commits moved no EURUSD trade. Its limit: the last trade before the cut opened on 3 June, so this test alone
  cannot see a look-ahead shorter than four weeks.
- **The time-shift property of `analyze()`.** 9,492 five-minute steps (17 March - 30 April 2025) through three engines
  (the backtester's views, the full arrays with the future inside, fresh objects physically truncated by an independent
  cut): 0 differing steps, 13,814 rejection texts equal, 11 / 11 / 11 signals, 127 zones with identical tracker state,
  the six ledger trades P17-P22 with the same confirmation, entry, stop and target; re-run unchanged by the skeptic in
  167 s. The analysis at a moment depends only on the candles closed at that moment. Scope: one profile, six weeks,
  `analyze()` only.
- **Ledger invariants.** 5,420 of 5,421 trades in 58 ledgers pass 30 candle-level checks (geometry, R and P&L
  recomputed, the 0.01 lot step and the budget fit, the minimum stop, planned R:R, the exit candle trading through the
  booked level at the booked price, break-even at the entry, the signal moment inside the windows and outside the
  blackout, market fill = the signal close plus the spread, limit price = `round(ask/bid - 0.25 x distance)`, the fill
  after the signal, the overlap limit, equity = initial + sum of P&L); the skeptic's independently written 15-check
  subset gives 0 violations on the 8 live ledgers (1,020 trades) and the stamp scan agrees on all 58.
- **Determinism.** Identical settings and data give identical ledgers across three code revisions of the day (six
  pairs identical column for column, including a pure rerun of the BTC base on a later revision); 177 provenance files
  show one data manifest per (symbol, data directory, start) and one calendar sha (6576f82a) in every run with news on.

What is wrong, and how small:

- **One defect**: a resting limit fills after its validity when the market is closed across the expiry (item 9; one
  OOS NAS100 trade of 1,339 limit fills, -1.0R; no in-sample ledger has one). Two lines.
- **One convention**: exits are stamped with the exit candle's open, fills with the close (item 17); 214 rows read
  closed_at == opened_at; the true exit is 0-5 minutes after the stamp; R untouched.
- **Two process points**: a variant booked as "+0.0R (+0 tr)" can still have changed one to four trades (item 11), so
  no-op is decided on trade identity; and the settings fingerprint changes whenever a commit adds a knob (item 10), so
  the parity check needs to classify that diff instead of calling it "NOT identical".
- **Two facts to know**: 8 % of limit fills land inside a news blackout by design (item 13), backtest and live alike;
  and a break-even at 2R could rescue 1 of 155 in-sample stop exits (NAS100 P30 at 3.71R; EURUSD 0 of 24 past 2R, max
  1.74R; gold 0 of 71, 1.91R; BTC 0 of 37, 1.80R) and 8 of 467 out of sample, which is the mechanism behind the
  batch's be1 / be2 costs (-27.3 / -28.1 / -9.3R and -12.7 / -4.5 / -3.5R) and why gold alone has BE 2R.

What the tests do not cover: the paper broker is covered only by the candle-level replay of the ledgers (which it
passes), the live feed's candle completeness only by the weekly parity check, and nothing here tests the live loop
itself. And what no invariant can say: whether 2024-2026 generalises. The arithmetic and the clock can be trusted to
the last digit; the sample cannot. The meta-labeling angle measured that directly: with 43-143 trades a market in
sample the ledgers cannot show a secondary edge under an AUC of 0.61-0.70 (pooled 0.574), a true AUC of 0.60 would need
150-200 trades a market for even odds of detection and about 400 for 80 %, and the in-sample CV AUC sits under 0.5 in
25 of 30 cells. The same limit is behind the strict adoption rule of `BACKLOG.md` (the EURUSD and NAS100 grids fail the
overfitting screen at PBO 0.58 and 0.73; gold 0.22 and BTC 0.45 pass). So: the backtester is believed; a 2024-2026
number on its own is not, which is why every item above carries both periods.

## 6. What was dropped in verification, and why

Findings dropped outright (3):

- Meta-labeling 8, the top-quintile 14-day range regime as a watch item: the numbers hold (pooled 74 trades +15.8R IS,
  146 trades -42.3R OOS) but a random bucket of those sizes is under the base in both periods 26-32 % of the time per
  market, all four at once 0.006 per bucket value, about 38 values in the tables, expected coincidences 0.23, i.e. one
  table in five shows one, not "about 6 %"; the bucket is positive in sample, so any rule helps one period only.
- Regime 3, NAS100 no trade at ER20 >= 0.5: 7 IS / 10 OOS trades (-1.6 / -6.7R), p 0.100 / 0.085, both under the
  15-trade bar, the 0.45 line costs in sample (+0.6R), the replay flat or adverse depending on the model; already an
  observation in `market_NAS100.md` 189-191.
- Liquidity map 1, EURUSD refuse the setup instead of widening the stop to 8 pips: IS -0.02R on 17 trades (passes the
  both-negative screen by 0.02R), 2026 +3.3R lost on 4 trades, and the whole effect is the Asia-inside subset (widened
  and inside -7.0 / -13.9R; widened and not inside +7.0 / +5.0R), so stacked on the EURUSD angle's rule it would cost
  in both periods.

Claims struck or corrected inside findings that are otherwise kept (the 24 keep-with-caveat verdicts, plus small
corrections inside findings that hold as written):

- Metalabel 3: EURUSD removed from the stake proposal (p 0.571 / 0.214; OOS sign flips with the cap variant).
- Metalabel 5: "structure lived in 2017-23 and left" becomes "no evidence in either period" (10 of 120 cells at
  p <= 0.05 is chance, binomial p 0.079; the IS bars are 0.61-0.70).
- Metalabel 2: the ridge's Spearman with planned R:R is +0.37, not +0.6; and `posthoc.py` thresholds the ridge run by
  refitting a classifier (a bug), which refit changes no count (still 1 of 240).
- Regime 1: "no in-sample cost" is the cheapest of 17 mean definitions and about 4R at the live stakes; the OOS p is
  one of 32 gold buckets.
- Regime 8: "NAS100's edge in both periods" is OOS-only (IS +0.80 against +0.75 a trade on 10 trades); the
  counter-trend double stake stays an observation.
- Regime 9: "both gold rules active this week" is a per-signal note on unadopted rules, not an instruction; the state
  sits under one daily ATR from flipping.
- Liquidity 3 and 10: the "window's extreme" was computed from 00:00 and 12:00 instead of the 09:00 / 13:00 opens; with
  proper windows the shares are 52 / 51 % pooled (EURUSD 32 / 63 %, gold 57 / 47 %, NAS100 51 / 54 %, BTC 55 / 48 %)
  and "only NAS100 agrees with itself" does not reproduce (every market agrees with itself; EURUSD's -1.78 / -0.79 is
  the widened and Asia-inside trades); the 1 % "stop exactly on the sweep" for gold in `followup.md` is a strict-equality
  artefact (100 % within price rounding).
- Liquidity 1 (the EURUSD overlap with the 0.5-ATR cut): 2 / 3 trades EURUSD-only, not the pooled 2 / 19; the scan had
  99 qualifying buckets, not about 150.
- Invariants 1: 17 knobs added for the pair compared, not 10; 6: code revisions per market 6 / 7 / 5 / 5, not "six to
  seven"; 4: the expiry test goes on the candle's open, not `now`; 7: the non-default-only hash is replaced by the diff
  classification (blind to a changed default); 8: the stamp is 0-5 minutes early, not a full candle, low priority; 9:
  "0 of 155 stop exits reached 2R" is 1 of 155, and 8 of 467 out of sample, so "cannot rescue" is a 2024-2026 statement;
  10: "cancelling limits in blackouts is a negative result" rests on 13 trades pointing opposite ways, kept as a fact
  only.
- Frequency 2: "every ledger trade's confirmation is among the replay's signals (46 / 47, 142 / 143, 43 / 43, 89 / 89)"
  is 47 / 47, 141 / 143, 43 / 43, 88 / 89 = 319 of 322 by the skeptic's matching; "81 % of signals became trades" is
  77 % against the runner's own 418 signals; the replay's 35 touches a month is a lower bound on live notices.
- Frequency 4: the report line belongs in `forward.py` `day_message`, not `live.py`; the touch part needs all four
  windows' journals.
- Frequency 5: "April-October 2025 starts waited 4-9 months for +10 %" is wrong (1.6-5.8 months to +10 %; 4.0-9.2 is
  the funded account); "lost 4 %" and "lost 1 %" are two README replays at 1.5 % and 1.25 %.
- Frequency 6: "more than two weeks, 2.5 a year" counts spells of ten trading days or more; strictly more than ten
  gives 1.8 / 2.1 a year.
- Frequency 1: the smallest gold stop is 1.705 USD (P3, 4 March 2024), not 3.5 USD; the cap still does not bind (22 %);
  the period has 714 weekdays, not 716.
- Frequency 7: the "more trades" finding restates four README sections; only the two to three points of first-trade
  visibility are new, and Set A's BTC half was never run out of sample.
- Frequency 9: 7 of 651 starts are unfinished on the NY ledger (1 %), not one; 10: the calendar also gained the
  15 October 2026 retail-sales row, after the window and harmless.
- Gold 1: the share of range trades is 35-49 % by year, not "42-49 % in every year" (2024: 35 %); the high-volatility
  OOS bucket is not distinguishable from the OOS average (p 0.16).
- Gold 2: the depth cut's "+3R in both periods on top of the ban" is the removal of 24 OOS trades at the ledger
  average (p 0.52); on top of the engine ban it is better in 6 of 10 years, not 7.
- Gold 3: the engine's in-sample "non-additivity" of the 3R fallback is six pushed-out trades worth +9.2R against +9.1R
  gained on 63 common trades, not a structural cost; the "-11.9R on origin trades" is one pushed-out +8.4R trade plus
  five new trades at -3.5R.
- Gold 4: the spread effect in `sp37` is 11.5R on the common OOS trades, not "about 13R"; the profile comment "live
  only" on the cap is stale.
- Gold 5: "a 3R+ fallback wants the break-even at 2.5R" rests on 6 IS / 10 OOS trades (P 0.19-0.41): a tie-break, set
  with the target, no comparison run.
- Gold 8: "x1 passes as often, 7 days faster" and "slows the challenge" become "mixed" (faster on two replay columns,
  slower on three); "worse than the 1H zones" is inside the noise (p 0.38).
- Gold 10: the plan's wording follows the four corrections above; the order of the plan is unchanged.
