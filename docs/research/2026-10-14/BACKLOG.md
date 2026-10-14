# Research backlog, 14 October 2026 (evening): merged from the hand draft, the six verified angles and the batches

Inputs: `BACKLOG_hand.md` (14 October, written while the verify stage was down), the six angle files
(`skeptic_smc_verdicts.md`, `prop_firm.md`, `methodology.md`, `ledgers.md`, `pipeline.md`, `risk_model.md`) with the
verified results of the skeptic passes, and `RESULTS_14oct.md` (the engine's own numbers: oct14b, oct14c and, since
this evening, oct14d in both periods). Where the hand draft and the verified results disagree, the verified result
and the engine run win; every such correction is listed in section 0. The post-verify angle files that appeared this
evening (`walkforward.md`, `baselines.md`, `costs.md`, `excursion.md`, `metalabel.md`, `regime_gate.md`,
`premortem.md`, `regime_now.md`) are not verified; where they bear on an item they are quoted as such and listed in
section F.

Conventions. R is after a flat 0.10R a trade for costs; in sample (IS) = 2024-01..2026-09, out of sample (OOS) =
2017..2023 (BTC 2020-06..2023); the research ledgers are the live profiles at 1 % units, guard off
(`aca/eutwo_EURUSD`, `aca/base_XAUUSD`, `aca/rr08_NAS100`, `aca/base_BTCUSD`, `aca/oos_*`). `$S` =
`/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad`; `research/...` = `$S/research/...`;
repository paths are relative to `/home/user/Kronos`. Engine runs: `python3 -m kronos_trader --config <yaml> backtest
--symbol <SYM> --data-dir $S/fixed --step-tf 5m --start ... --end ... --kronos off --quote-basis bid --out <csv>`
(BTC: `--data-dir $S/btc_data` IS on UTC candles, `$S/btc_old` OOS, `$S/btc_ny_old` New-York-anchored, both periods,
no 1m file). A batch = a `jobs.json` run with `python3 $S/aca/run_jobs_resume.py <dir>/jobs.json 3` (resumable; it
skips the jobs whose `run.log` line says rc=0); read with `python3 $S/research/backlog_eval.py <dir>` (delta,
halves, years, added/gone against the base ledgers). Replay: `cd $S/aca && XAU=<ledger> EU=<ledger> NAS=<ledger>
python3 challenge_sim_set.py $S 0.10 [<btc ledger>|none] [<extra R per BTC trade>]` (the 2-Step at the live stakes,
two open, the guard's worst-case check; the base prints: both phases 100 %, median 84 d, 2026 starts within 6 weeks
71 %, 2024-25 starts within 3 months 42 %, funded +5.7 %/mo). Replay levels are comparable only within one script
(`prop_lib.py` gives 56 % / 41 % / 110 d for the same base, `risk_model_lib.py` 71 % / 42 % / 84 d).

Status words: DONE (the engine has run it, numbers in `RESULTS_14oct.md`), RUNNING, QUEUED (a job file exists in
`$S/oct14e..h`, not run: no batch has run since 19:00 UTC), NEW (a job to write), NEEDS CODE, NEEDS DATA, LAPTOP (a
read-only measurement on Max's laptop, `docs/LAPTOP_TASKS.md`), FOR MAX (a decision), NEGATIVE (measured, not to be
rerun).

Two adoption rules sit side by side and both are stated per item:

- the house rule (`docs/CURRENT_STATE.md`): a change goes into a frozen challenge profile only when it is positive
  in both periods and the challenge replay does not slow down (Max's judge: the 2026 starts);
- the strict rule (`walkforward.md` section 5, `research/walkforward/candidate_check.py SYMBOL ledger.csv`): the
  market's grid passes PBO <= 0.5 (gold 0.22 and BTC 0.45 pass; EURUSD 0.58 and NAS100 0.73 fail, so on those two
  nothing is adopted on 2024-2026 evidence alone), the candidate passes the CSCV screen and the time-consistency
  test, and its haircut gain (0.75 x on gold, 0.5 x on EURUSD/BTC, 0.4 x on NAS100) reaches one standard error of
  the live total (gold 22R, EURUSD 16R, NAS100 15R, BTC 29R); then 2017-2023 not below the live profile, then 20
  forward trades.

Nothing in the 14 October batches passes the strict rule; three oct14d runs pass the house rule (A4, A5, A8), one of
them with a slower 2026 (A4). That is the state of play.

## 0. Corrections to the hand draft

| Hand draft | What the verified results and the engine say | Now |
|---|---|---|
| A1 BTC candles: QUEUED OOS, NEEDS CODE for `--crypto` | Verified (pipeline 1): the FTMO window takes 4H/D1/W1/MN1 from MT5 at 17:00 New York; the rerun 94 tr, 51 %, +33.3R against 89, 58 %, +70.6R is sound; `$S/btc_ny_old` covers 2019-12..2026-10 and has no 1m file, so the queued `nybase_BTCUSD` (oct14g) measures both periods without any code; the 1m file adds 2 trades, -2.0R (pipeline 8) | A1, B2 |
| A2 2023 hole: NEEDS DATA | Confirmed in the 1-minute source (38-48 % of the 10-23 UTC slots present Feb-Jul 2023); needs the merge, a `SCALE` entry for `USATECHIDXUSD` and the network from the laptop (429/503 from the cloud) | B4 |
| A3 2017-2018 clock: NEEDS CODE, low | Confirmed on NAS100's 09:30 ET cash-open spike (six mismatch weeks late, 28 of 2019-2026 on time); 7 OOS trades | B6 |
| A4 thin pre-2023 calendar: NEEDS CODE + network | Confirmed (the TradingView importance tags of 2019 are the cause); effect -2..-4R of OOS losers; bundle with A2's rebuild | B5 |
| A5 BTC true cost 0.18R: no code | Confirmed (`costs.md`); the engine's gold run at 3.7 pips is -11.6R IS (`sp37`), not the -3.5R of the ledger replay: the engine re-sizes on the spread-inclusive stop and enters on the ask | A2 |
| A6 spread/slippage journal, hours line | Reasoning only, no R; after the measurement | B7, B9 |
| A7 clock clean | Confirmed again: the append-only check (`lookahead/eutwo_EURUSD_to_june.csv`: 44 trades identical) | E |
| B1 gold 10:00-11:00: RUNNING `ban`, `stack` | DONE both periods: `ban` IS +11.6R, OOS +18.7R, but the job also cut 15:00-15:30, and the replay is slower on the 2026 starts (66 % against 71 % within 6 weeks); `stack` (+ depth 0.25 + 3R fallback) IS +10.7R, OOS +33.2R, 2026 -7.0R | A4 |
| B2 EURUSD 14:30-16:00: RUNNING `usob`, `both` | DONE: `usob` IS +5.7R, OOS +3.0R, replay not slower; `both` adds the 09:00 cut, which fails IS alone (`from10` -1.7R) | A5, E |
| B3 depth 0.25: RUNNING gold, NAS100 0.125 | DONE gold: IS +3.1R, OOS +11.0R, 2026 -3.2R, replay not slower; the whole IS gain sits in the 0.25-0.30 slice; NAS100's band is +2.8R IS on the engine's measure (fails) | A8, E |
| B4 EURUSD stop >= 0.5 ATR: RUNNING `msa05` | QUEUED (oct14f), and the ledger feature is not the knob's measure: on the knob's measure 4 IS trades -1.2R (p 0.17), 2 OOS +2.5R: expect flat | A10, E |
| B5 BTC 16:00-17:00: RUNNING `end1530*` | QUEUED (oct14e); OOS p 0.52 (the OOS base rate), all of the IS loss is 2024, and the ledger sits on UTC candles | E |
| B6 target 5 % short: QUEUED `tpb`, `tpf5` | Knob exists; with the live break-even in the walk it is worse in all four IS cells (gold -12.1R, BTC -5.9R, EURUSD -3.4R, NAS100 -3.0R on the winners); `excursion.md` agrees (-6.1R IS exact walk) | E |
| B7 NAS100 break-even 2R: RUNNING `be2` | DONE: -4.5R IS in the engine (3 of 43 trades), -0.6R OOS by the walk; `be3_NAS100` queued, immaterial (+1.0 / +2.0R by the walk) | E, A10 |
| B8 shift beyond P: QUEUED `prot` | The one unmeasured existing knob; expect a loss | A6 |
| B9 30 min after the touch: QUEUED `mva30` | Knob exists; the loss is 2024's on both markets, 2026 gives it back (gold +3.2R, BTC +0.5R), plateau 20-30 min only | A9 |
| B10 day-open drift: QUEUED `drift` | Knob exists; holds on the exact clock, flips one hour later (01:00 NY: +10.0R OOS removed), 10 IS trades, 24 of 33 already at half stake | E |
| B11 min target ATR, stop inside zone | On the engine's ATR (closed 1H candles at the signal) the target rule removes -0.3R IS (zero); the stop rule 7 IS trades, 4 of them in B's band | E |
| B12 breakers, age of X | Breaker direction wrong in sample (-0.45..-0.57 zone heights in 24 h); young-X zones are the best in sample (+0.98R a trade at 1-3 candles) | E |
| Section C, 14 October knobs `swp`, `sss` ("0 of 16 run") | DONE (oct14c): `sss` BTC -2.3R, EURUSD -3.0R, NAS100 -0.3R, gold +0.8R; `swp` 0 / -1.1 / 0 / 0R; `fv` 0 / -2.2 / 0 / -1.1R; `nop` 0 / -7.3 / -4.7 / -14.2R | E |
| C1 stop at the target | The replay's baseline already stops at the target, so the published +1..+3 points overstate it; the finish mode alone is +0.3 / +1.0 / +0.9 points, never worse; the stake must round UP to the minimum lot | B3, D4 |
| C2 funded Standard news rule: FOR MAX | FTMO's FAQ confirms stops, targets and pending orders count; 2.5 % of exits in the window: a violation is likelier than not within 28 trades; the cost is regime-dependent (-55R of 241R IS, -4.5R OOS, +11R without two trades); lifting SL/TP for the window is out (an -8.0R fill on 11 Feb 2026); code before funding | B1, D2 |
| C3 double-stake weekend filter | The filter removes about 0.3 % of fail chance a challenge and costs 2-9 points of passes; the existing full weekend close is no worse and removes the whole tail | E, D5 |
| C4 NAS100 4H single stake | Tail 0.2 % a challenge; 2026 six weeks 56.1 -> 53.3 %; `exits.day_close` is the knob if the tail must go | E, D6 |
| D methodology to build: A5 bootstrap, A7 cost model, A8 nulls | A1-A5 and A8 are run in full (`walkforward.md`, `risk_model.md` section 3, `baselines.md`); A6 narrows to one knob, A7 to one measurement | A2, A7, C |
| Risk angle (not in the draft) | 4H zones at x1.5 passes every column; the cushion ladder, the open-risk cap, Kelly, the phase-2 stake and sizing on the initial balance do not | A3, E |

## A. Run now (prioritised)

| # | P | Status | Candidate (markets) | Exact definition and the setting | Expected (ledger / engine so far) | Decides (IS and OOS both required) |
|---|---|---|---|---|---|---|
| A1 | 1 | QUEUED oct14g `nybase_BTCUSD` (IS + OOS); LAPTOP W1 stamps | BTC profile on the candles FTMO stamps, no 1m file (BTCUSD) | the live BTC profile unchanged; `--data-dir $S/btc_ny_old` (4H/1D/1MO at 17:00 NY, W1 from Saturday 17:00 NY, 5m/15m/1H unchanged) for 2024-01..2026-09 and 2020-06..2023 | IS 94 tr, 51 %, +33.3R, dd -6.0R against 89, 58 %, +70.6R (the pipeline rerun, with the 1m file); 4H-zone trades -2.0R; shorts +18.0R against +40.4R; OOS unknown; replay with this ledger at +0.08R extra cost: both phases 95 %, 2026 six weeks 54 %, funded +5.0 %/mo against 71 % / +5.7 % (UTC ledger) and 45 % / +4.7 % without BTC | R a trade after true costs in both periods; the replay with and without BTC; BTC stays at half stake or goes off at the next restart (FOR MAX) |
| A2 | 1 | LAPTOP (3 days), then NEW 8 engine runs + replay | FTMO spreads of NAS100 and BTC measured; every research ledger rerun with the measured spread, the commission and the 30 % cap (all four) | `mt5-spreads` on the laptop; then the `symbols:` block below in the four research yamls and `risk.max_spread_stop_fraction: 0.3`; BTC on the A1 directory | gold at 3.7 pips: `sp37` IS -11.6R (-0.08R a trade), OOS -0.4R; BTC at $15/$30/$45: +56.5/+51.1/+45.6R after true costs (at $45 the cap refuses 5 trades, +25R); NAS100 at 1.5/3/5 points +35.7/+31.7/+26.4R; EURUSD +3.1R in live's favour | the decision rules of `costs.md` 7.1: BTC median <= $30 stays; $30-45 stays at +0.5R a trade; > $45 fails the cost gate (x0.25 stake); NAS100 <= 2 points nothing, 3 a 0.10R haircut, 5 points `min_stop_pips: 17`; the account replay beside it |
| A3 | 1 | RUN replay (scratchpad), then FOR MAX at the next restart | 4H zones at 1.5 x the stake instead of 2 x (EURUSD, XAUUSD, NAS100) | `risk.zone_risk_multiplier: {4H: 1.5}` in `config/dorus_live.yaml`, `dorus_live_gold.yaml`, `dorus_live_nas100.yaml` | research replay: 2024-25 within 3 / 6 months 46 / 78 % against 42 / 68 %, median 77 d against 84, 2026 six weeks 74 % against 71 %, worst month -5.3 % against -5.6 %, bootstrap dead 2.0 % against 2.1 %, at 0.25R costs stalls 11 % against 19 %, winners halved 47 % against 55 %; mechanical: a 4H loss is -2.5 % instead of -3.3 %, 0 days at -3 % instead of 6, 2 guard refusals instead of 7 | the paired replay on the repository-side script never worse on any column (speed, dead, worst month, both stresses); no R changes, so no IS/OOS question |
| A4 | 2 | DONE `ban` (both periods + replay); NEW `ban10`, `ban15` (IS + OOS) | Gold: no signal 10:00-10:59 Amsterdam, attributed (XAUUSD) | `session.windows: [["09:00","10:00"],["13:00","17:00"]]` (the pure cut, `ban10`) and `[["09:00","11:00"],["13:00","15:00"],["15:30","17:00"]]` (`ban15`), base `$S/q4_r26_XAUUSD_visit1h_full.yaml` | `ban` (both cuts): IS 124 tr, 53 %, +83.4R (+11.6R: 2024 +10.1, 2025 -1.7, 2026 +3.2), dd -7.9R; OOS 316 tr, -43.6R (+18.7R, 6 of 7 years, 2022 -9.3); replay median 79 d (84), 2024-25 3 months 45 % (42), funded +6.3 %/mo (5.7), but 2026 six weeks 66 % (71), 2026 median 38 d (34), 9.2 trades a month (9.8); screen PASS, haircut gain +8.7R (floor 22R); ledger expectation for the pure cut: removed 21 tr -5.9R IS, 66 tr -22.1R OOS; the 15:00-15:30 slot -3.7 / -6.9R | the pure cut keeps >= +15R OOS and >= 0 IS after the slot effect AND the 2026 six-week share stays >= 71 %; otherwise NEGATIVE for the challenge and a funded-phase candidate (the gain is in the OOS years and 2024) |
| A5 | 2 | DONE (both periods + replay + screen); FOR MAX | EURUSD: no signal 14:30-15:59 Amsterdam (EURUSD only) | `session.windows: [["09:00","11:00"],["13:00","14:30"],["16:00","17:00"]]` in `config/dorus_live.yaml` | IS 36 tr, 56 %, +45.3R (+5.7R, every year: 2024 +3.3, 2025 +1.3, 2026 +1.1; 11 trades gone, 18 % won), dd -3.3R; OOS 84 tr, +1.7R (+3.0R: 2021 +4.4, 2023 +2.2, the other years -0.7..0); replay median 80 d, 2024-25 3 months 44 %, 2026 six weeks 71 % (unchanged), funded +5.8 %/mo; screen PASS 5 of 5 windows, haircut gain +2.9R (floor 16R); gold's slot +16.6R IS, BTC's +10.8R, NAS100 -0.4R: EURUSD only | house rule: passes; strict rule: no (EURUSD's grid fails PBO, gain under the floor); a mechanism (US data / NYSE open), 11 trades; adopt at the next restart or after 20 forward trades; the paired bootstrap (C4) is the one unrun check |
| A6 | 2 | QUEUED oct14g `prot_*` (4 markets; IS first) | Balance shift counted beyond the P candle, not the gap edge (all four) | `confirmation.bs_threshold: protector` (`confirmation.py` `shift_level`); jobs written against the four research bases | never measured; the ledgers cannot replay it; every stricter trigger so far lost (`bs_requires_sweep` BTC -20.9R, `bs_requires_structure` worse on all four, `conf15` -5..-44R); expect fewer and later entries at a lower planned R:R | R a trade and the replay, never the sum; run OOS only for a market whose IS R a trade is at or above the base |
| A7 | 2 | NEW batch (gold, EURUSD, NAS100; BTC after A1) | The one non-plateau knob mapped: `structure.min_gap_fraction` x `confirmation.max_touch_age_hours` | gap {0.05, 0.1, 0.15, 0.2, 0.3} x touch age {12, 24, 48} per market (live cells gold 0.2/24, EURUSD 0.1/24, NAS100 0.1/24); IS for every cell, OOS for the live row, the live column and the best cell | known cells: BTC 0.15/0.2/0.25 = -14.0 / 0 / -11.9R; gold and BTC -24.7R / -37.1R at 0.1; EURUSD and NAS100 took 0.1 on two points each; touch age 12/24/48 flat on the three (README "Spent zones"); 24 of 26 other knob-market cells are plateaus (`skeptic_method/check_out.txt`) | the reading rule: live >= 0.75 x the neighbours' median and every IS neighbour positive = plateau; live > 1.33 x = a peak: move to the plateau centre only if the OOS map has the same shape; a 2-D ridge means the two knobs interact and are set together |
| A8 | 3 | DONE `dep25` (both periods + replay + screen); NEW `dep20`, `dep30` (IS + OOS) | Gold: entry at most a quarter of the zone deep (XAUUSD) | `risk.max_entry_depth: 0.25` (measured on the confirmation close, `risk.py` 426), plus 0.20 and 0.30 | `dep25`: IS 132 tr, 52 %, +74.9R (+3.1R: 2024 +2.1, 2025 +4.2, 2026 -3.2), dd -5.9R; OOS 348 tr, -51.2R (+11.0R, 6 of 7 years, 2023 -3.4); replay median 76 d, 2024-25 46 %, 2026 six weeks 71 %, funded +5.8 %/mo; screen PASS 5 of 5, haircut gain +2.3R (floor 22R); the ledger puts the whole IS gain in the 0.25-0.30 slice (depth > 0.30 alone -0.4R IS), 2025 carries it; NAS100's half fails (band +2.8R IS on the engine's measure) | a plateau over 0.20-0.30 in both periods, 2026 not worse than the base, the replay not slower; else NEGATIVE |
| A9 | 3 | QUEUED oct14h `mva30_XAUUSD`, `mva30_BTCUSD` (IS + OOS; BTC on `$S/btc_ny_old`) | No signal within 30 minutes of the visit's first touch (XAUUSD, BTCUSD) | `confirmation.min_visit_age_minutes: 30` (engine `minutes_since_touch`, line 608); change the BTC jobs' `--data-dir` to `$S/btc_ny_old` before running | ledger: gold 14 tr, 21 %, -4.7R IS (p 0.025), 59 tr -8.4R OOS (p 0.57); BTC 19 tr, 32 %, -7.0R IS (p 0.004), 14 tr -6.0R OOS (p 0.37); 2024 carries both (gold -7.0R, BTC -5.6R), 2026 gives back +3.2R / +0.5R; plateau 20-30 min only (15 fails OOS, 45 fails IS) | 2026 >= 0 and the replay not slower in both markets, else NEGATIVE (the shape of a fitted cut) |
| A10 | 4 | QUEUED oct14f (run as written, except `ts8`) | The rest of the per-market chain: `nm0`, `be3`, `dep125`, `nstack` (NAS100), `msa05`, `tr60` (EURUSD), `al5`, `clx2` (BTC) | as in `$S/oct14f/make_jobs.py`: `neutral_bias_risk_multiplier {1M: 0.0}`, `breakeven_r_intraday 3.0`, `max_entry_depth 0.125`, both; `min_stop_atr 0.5`, `bias.trend_filter_days 60`; `aligned_count_risk_multiplier {5: 0.25}`, `confirmation.max_body_atr 2.0` | expectations: `nm0` costs IS (the 50/50-month trades are +0.10 / +0.49R a trade in the two halves); `be3` +1.0 / +2.0R by the walk, immaterial; `dep125` fails (the deeper band is +2.8R IS); `msa05` flat (4 trades -1.2R IS); `tr60` fails (no EURUSD trend cut holds in both periods, `regime_gate.md`); `al5` flat IS, +8.7R OOS on UTC candles; `clx2` unknown; BTC jobs re-read on NY candles only | both periods positive, R a trade, the replay; none is expected to pass; remove `ts8_*` from `jobs.json` (the time stop is -16.9R / -12.7R by the exact walk) |

Detail per item (the settings an engineer needs; nothing here changes a live profile until Max says so).

**A1. BTC on the candles FTMO stamps.** Run `nybase_BTCUSD` and `oos_nybase_BTCUSD` from `$S/oct14g/jobs.json` (with
`prot_*`, without `tpb_*`: filter the file with
`python3 -c "import json;J=json.load(open('$S/oct14g/jobs.json'));json.dump([j for j in J if '/tpb_' not in j['log'] and '/oos_tpb_' not in j['log']],open('$S/oct14g/jobs_run.json','w'),indent=1)"`
then `python3 $S/aca/run_jobs_resume.py $S/oct14g/jobs_run.json 3`; about 12 minutes IS, 15 OOS). Read with
`python3 $S/research/backlog_eval.py oct14g` (the "added/gone" columns compare against the UTC ledgers: 54 of 89
setups are shared) and replay with `cd $S/aca && python3 challenge_sim_set.py $S 0.10 $S/oct14g/nybase_BTCUSD.csv 0.08`
(0.08 = the measured 0.18R median true cost of a BTC trade minus the flat 0.10) and `... none`. Before the reading,
the W1 convention must come off the terminal: the laptop prompt "Once: the BTC candle stamps" (`docs/LAPTOP_TASKS.md`)
gives the hour the daily bar starts (expected 17:00 New York) and the weekday/hour of the weekly bar (expected
Saturday 17:00 New York = Sunday 00:00 server); if the weekly starts Monday 00:00 server instead, rebuild
`$S/btc_ny_old` with `W-MON` and rerun. The reading is "BTC's +70.6R is not robust to where the day is cut and the
live cut is the unfavourable one", not "BTC makes +33R"; after FTMO's crypto costs the NY ledger is roughly flat, and
the replay says BTC at half stake is still a small plus over no BTC (2026 six weeks 54 % against 45 %, +5.0 against
+4.7 %/mo). FOR MAX after the OOS run: half stake and the 3R cap stay, or BTC goes off at the next restart. Every BTC
candidate (A9, A10, A7's BTC map) is read on these candles. The reproducible rebuild is B2; until then
`$S/btc_ny_old` (built by `research/pipeline/btc_anchor.py`) is the directory.

**A2. Spreads measured, costs in the research ledgers.** Laptop, read-only, three weekdays:
`.venv\Scripts\python.exe -m kronos_trader --config config/dorus_live.yaml mt5-spreads --symbols NAS100=US100.cash,BTCUSD,XAUUSD,EURUSD --day <date>`
(the standing prompt; median, p90 and maximum over 09-11 and 13-17 Amsterdam, and the stop the 30 % cap refuses at
the median). Then in `$S/aca/eutwo_EURUSD.yaml`, `$S/q4_r26_XAUUSD_visit1h_full.yaml`, `$S/aca/rr08_NAS100.yaml`,
`$S/q4_r26_BTCUSD_visit1h_full.yaml` (copies under `$S/oct14j/`):

```yaml
symbols:
  EURUSD: {typical_spread_pips: 0.1, commission_per_lot: 3.0}      # FTMO: 0.1 pip raw, $3 a lot round turn
  XAUUSD: {typical_spread_pips: 3.7, commission_pct: 0.0014}       # 3.4-3.7 pips measured 6 October; metals 0.0007 % a side
  NAS100: {typical_spread_pips: <measured median, points>}         # never measured; 1.5 assumed, 3 and 5 are the what-ifs
  BTCUSD: {typical_spread_pips: <measured median, USD>, commission_pct: 0.065}   # crypto 0.0325 % a side on the notional
risk:
  max_spread_stop_fraction: 0.3                                    # live refuses these stops; the backtester applies it since 14 October (runner.py 301-311)
```

Eight engine runs (IS and OOS; BTC on `$S/btc_ny_old`), `backlog_eval.py oct14j`, the replay with the four costed
ledgers at `COST=0.05` (fill slippage only; the spread and commission are now inside the R), and `research/costs/
cost_model.py` on them (C6). Expected: EURUSD +0.07R a trade better than the flat haircut, gold -0.08R a trade
(the engine's `sp37`: 142 tr, 46 %, +60.2R IS, 2024 -4.9, 2025 -6.3, 2026 -0.4; OOS -0.4R; 1 trade refused),
NAS100 -0.04R at 3 points, BTC -0.12R at $30. Decision rules from `costs.md` 7.1 (above); gold's 3.7 pips and
EURUSD's 0.1 go in now whatever the laptop measures. `min_stop_pips: 150` on BTC only if the median comes in at $40
or more (the README measured -6.2R for it). Nothing here changes a live profile; it changes what the research
ledgers say, which every later item is read against.

**A3. 4H zones at x1.5.** Config only, three profiles. The research lib's rows (`risk_model.md` sections 4-8,
`skeptic_risk/check1.out`: the whole historical speed gain sits in the 2025 cohorts, the bootstrap shows no speed
gain, the tail gain is mechanical and robust) are confirmed on the repository-side replay before anything moves:
copy `$S/aca/challenge_sim_set.py` to `challenge_sim_x15.py`, change `{True: 2.0, False: 1.0}` to `{True: 1.5,
False: 1.0}` on the `poi_tf` line, run both with the same ledgers, and put the rows side by side (both phases, median,
2026 six weeks, 2024-25 three months, funded %/mo, worst month at 1.5 %); then the two stresses with
`python3 challenge_sim_x15.py $S 0.25` and the winners halved (a one-line `T.loc[T.r > 0, "r"] *= 0.5` after the cost
line). Adopt when no column is worse (expected: every column equal or better). `scripts/risk_steps.py` cannot
express a zone multiplier (`portfolio.combine` carries no weights), so the scratchpad script is the replay; the
profiles' comments cite it. FOR MAX: the risk block is shared by the four profiles and the profiles are frozen in
the challenge; a stake multiplier changes no trade, only the size, so it is Max's call whether it counts as a change
before phase 2 or waits for the funded account.

**A4. Gold 10:00-10:59, attributed.** `$S/oct14i/make_jobs.py` on the oct14d pattern:

```python
V = {"XAUUSD": {"ban10": setp("session", "windows", [["09:00", "10:00"], ["13:00", "17:00"]]),
                "ban15": setp("session", "windows", [["09:00", "11:00"], ["13:00", "15:00"], ["15:30", "17:00"]]),
                "dep20": setp("risk", "max_entry_depth", 0.20), "dep30": setp("risk", "max_entry_depth", 0.30)}}   # A8's two slices in the same batch
```

(base `$S/q4_r26_XAUUSD_visit1h_full.yaml`, `--data-dir $S/fixed`, IS 2024-01-01..2026-09-24 23:55 and OOS
2017-01-02..2023-12-31 23:55; about 7.5 and 18 minutes a job). Read with `backlog_eval.py oct14i`, screen with
`cd $S/research/walkforward && python3 candidate_check.py XAUUSD ../../oct14i/ban10_XAUUSD.csv ban10`, replay with
`XAU=$S/oct14i/ban10_XAUUSD.csv python3 challenge_sim_set.py $S 0.10`. The engine's `in_session` treats the window
end as exclusive, so `["09:00","10:00"]` admits a confirmation closing at 09:55 and refuses 10:00. What the combined
`ban` run already says: the 10:00 hour's loss is 2024's (the ledger: -6.2R of -5.9R; 2025 -1.2R, 2026 +1.5R given
back) and the replay is 5 points slower on the 2026 starts; the OOS gain (+18.7R, six of seven years) is the strong
part. If `ban10` reproduces that shape, the rule is a funded-account candidate (where the OOS years are the hedge),
not a challenge change.

**A5. EURUSD 14:30-15:59.** Nothing more to run in the engine. The decision table is complete: both periods positive,
the replay equal on the 2026 starts and 2 points better on 2024-25, the overfit screen passed, the haircut gain under
the floor, EURUSD's grid under PBO (0.58: a 2024-26 pick is a coin flip on this market), 11 trades behind it, 4 of
them in the 14:30-15:00 half (all lost), EURUSD's trade count 1.1 a month after it (36 trades in 33 months; Max asked
for more EURUSD trades on 7 October, not fewer). FOR MAX: adopt at the next restart (house rule) or let 20 forward
trades decide (strict rule). If adopted: the yaml line above in `config/dorus_live.yaml` with the evidence in its
comment, and the README row from C1.

**A6. Shift threshold `protector`.** The four IS jobs of `$S/oct14g` (`prot_EURUSD`, `prot_XAUUSD`, `prot_NAS100`,
`prot_BTCUSD`; the BTC one should be re-pointed at `$S/btc_ny_old`). The ledgers carry no opposing-gap P, so only
the engine answers. Stop after the IS batch for every market that loses on R a trade; run the OOS job for a market
that does not. The 2-Step replay decides, not the sum: a stricter trigger trades less, and the challenge needs
trades as well as R.

**A7. The gap-size x touch-age map.** `$S/oct14k/make_jobs.py` on the oct14d pattern with
`V[sym] = {f"g{g}_a{a}": many(setp("structure", "min_gap_fraction", g), setp("confirmation", "max_touch_age_hours", a)) for g in (0.05, 0.1, 0.15, 0.2, 0.3) for a in (12, 24, 48)}`
for XAUUSD (base `$S/q4_r26_XAUUSD_visit1h_full.yaml`), EURUSD (`$S/aca/eutwo_EURUSD.yaml`) and NAS100
(`$S/aca/rr08_NAS100.yaml`), the live cell and the cells the README already measured left out (touch age 12/24/48
at the live gap; the other gap at 24 h): 11 IS cells a market, 33 runs, 4-5 hours at three workers; OOS for the live
row and column and the best IS cell (about 12 runs, 4 hours). Reading: C3. Why this knob: `min_gap_fraction` defines
which gaps become zones, BTC's 0.15 / 0.2 / 0.25 = -14.0 / 0 / -11.9R is the one single-cell optimum in the whole
knob set, and gold and BTC lose 24.7R / 37.1R at 0.1 while EURUSD and NAS100 gained on it; 0.05 and 0.15 were never
run on the three. BTC's map waits for A1 (a map on UTC candles maps the wrong surface).

**A8. Gold depth 0.20 / 0.30.** In the oct14i batch (A4). The engine's `dep25` is +3.1R IS with 2026 -3.2R, so the
question is only whether 0.20-0.30 is a plateau in both periods (the ledger says the IS gain lives in five trades
between 0.25 and 0.30) and whether the replay stays at 71 % / 46 %. If it is a peak: NEGATIVE. If a plateau: FOR MAX
with A5 (same reading: house rule yes, strict rule no, +2.3R after the haircut).

**A9. 30 minutes after the touch.** The oct14h jobs as written, BTC re-pointed at `$S/btc_ny_old` (both periods:
`--start 2024-01-01` and `--start 2020-06-01` on the same directory). Expect the engine to confirm the ledger
(gold -4.7R / -8.4R removed, BTC -7.0R / -6.0R) and 2026 to give it back; adoption needs 2026 >= 0 in the engine,
which the ledger says it will not be. Low priority because the result is foreseeable; it runs because it is free.

**A10. The rest of oct14f.** Run as written minus `ts8_*` (remove the four `ts8` entries from `$S/oct14f/jobs.json`;
the time stop is refuted by the exact walk in both periods). Read with `backlog_eval.py oct14f`; a job that is
positive in both periods goes through `candidate_check.py` and the replay before it is mentioned to Max; the rest is
one line each in the README's negative table.

## B. Needs code (the smallest change each)

| # | P | Item | Smallest change | Evidence | Status |
|---|---|---|---|---|---|
| B1 | 1 (before funding; earliest plausible late November) | No execution inside FTMO's 2-minute news window on the funded Standard account: flat 5 minutes before a restricted event, resting limits cancelled at the blackout's start | `prop_firm.news_flat_minutes: 5` (0 = off; `start_ftmo.bat` adds `--news-flat-minutes 5` under `FUNDED=1`): in `live.py`'s position loop beside the weekend close (line 1903): a position in a market whose currencies have a restricted event within the window is closed at the market and its resting limit cancelled, journal event `news_flat`; `manage_limits` (line 1721): a resting limit is cancelled when `NewsCalendar.blackout(symbol, now)` (as `engine.py` 451) is true, journal `limit_cancelled: news`; `paper.py` `_work_limits` (206) fills nothing inside the blackout, so the backtester can rerun the ledgers under the rule; the restricted set = FTMO's "Restricted event" titles once parsed, until then NFP, CPI, Fed decision and press conference, FOMC minutes, GDP advance, ISM, PPI, retail sales, core PCE, JOLTs, ECB decision, press conference and the flash CPI (EURUSD); tests: a limit resting across a 14:30 CPI is cancelled at 14:00; a position open at 14:25 is closed at 14:25. About 60 lines + tests, no new feed | FTMO FAQ (14 October): stops, targets and pending orders count, violation "may result in termination"; 8 of 322 exits (2.5 %) and 23 of 698 landed in the window; limit fills inside the 30-minute blackout 13 of 190, +1.4R, 23 % won (cancelling costs nothing); the cost of going flat: -55R of 241R IS (-22R if BTC is exempt), -4.5R OOS (+11R without the two largest trades): regime-dependent; lifting SL/TP for the window is out (EURUSD 11 Feb 2026 would have filled at -8.0R) | NEEDS CODE; D2 |
| B2 | 2 | `scripts/build_mt5_like.py --crypto`: the BTC research directory rebuilt the way the server stamps it, every time | skip the weekend mask (line 28) under `--crypto`; weekly rule `W-SUN` on the series shifted +7 h from New York local (Sunday 00:00 server = Saturday 17:00 NY), 4H/1D/1MO at 17:00 NY, no 1m file in the output; `python scripts/build_mt5_like.py btc_data btc_ny BTCUSD:BTCUSD_1min.csv --crypto`; a unit test on one week's bar stamps. About 20 lines | A1's rerun was done by `research/pipeline/btc_anchor.py` (scratchpad); the BTC rows of `docs/CURRENT_STATE.md` and the README move to the NY ledger once it is reproducible (task 81) | NEEDS CODE after A1's reading and the W1 stamp readout |
| B3 | 3 | Stop at the target; finish the four trading days at the minimum stake | `prop_firm.stop_at_target: false`, `prop_firm.finish_risk_pct: 0.10`, `prop_firm.min_trading_days: 4`; in `live.py` where the stake comes from equity (1481-1504, `stepped_risk`): closed balance >= `risk.target_pct` and trading days (Prague clock, days with a position opened, counted as the 22:05 report counts them) < 4 -> risk = `finish_risk_pct`, lots rounded UP to `spec.min_lot` (the min-lot skips at 1603 / 1646 must not skip in finish mode: gold's 1 oz is about 0.2 % of 10k); days >= 4 -> no new entries, open ones run, one Telegram line "target reached: request the next phase". About 40 lines + tests | the replay's baseline already stops at the target: the bot trading on and the bot stopping give identical results in all three periods when the request is made at the 22:05 report; the finish mode alone is +0.3 (2024-25 within 3 months), +1.0 (2026 within 6 weeks), +0.9 (2017-23 funded) points, never worse; mostly phase 2 (5 % comes before day 4 more often) | NEEDS CODE; until then D4 |
| B4 | 3 | Fill the February-July 2023 holes from Dukascopy and rerun 2023 | `python -m kronos_trader dukascopy --symbol EURUSD --instrument EURUSD --start 2023-02-01 --end 2023-07-31 --raw-dir data/dukascopy/raw --out-dir <tmp>` (XAUUSD; NAS100 = `USATECHIDXUSD` after `"USATECHIDXUSD": 1e3` is added to `SCALE`, `kronos_trader/data/dukascopy.py` line 33, checked on one day against HistData); a 15-line merge on the timestamp index (HistData first, Dukascopy where HistData has none); `scripts/build_mt5_like.py`; the three OOS ledgers rerun for 2023; a missing-slot share per month in the provenance (`research/pipeline/sparse.py` logic). Network: datafeed.dukascopy.com answered 429 then 503 from the cloud; run from the laptop or with the loader's back-off | 20-24 % of the 5m slots missing Feb-Jul 2023 on all three feeds, 38-48 % of the 10-23 UTC slots present (both entry windows); 25 OOS trades inside the hole: NAS100 3 (+12.6R of its 2023 +17.3R), gold 15 (+7.0R), EURUSD 7 (+5.3R); 2024-2026 clean (0.0-0.1 %) | NEEDS DATA + CODE; until then the 2023 OOS figures are unreliable; bundle B5 |
| B5 | 5 | One news calendar 2017-2026 | fetch the TradingView calendar month by month 2017-2022 at importance 0, keep the titles that are high-impact in 2024-2026 (`from_tradingview` + `save_events`), target about 250 USD events a year with ISM/JOLTs/FOMC present; `news.calendar_csv` is the knob; rerun the OOS ledgers under B4's rebuild | 96/96/94/105/134/192 USD events a year 2017-2022 against 249-261 from 2023, 0 ISM titles before 2021; what a full calendar blocks: about a fifth of the OOS 09:30-10:30 ET entries (gold 51 tr -8.8R, BTC 16 -8.7R, EURUSD 11 -4.3R): roughly -2..-4R of losers removed over seven years; 2024-2026 unchanged | NEEDS CODE + network; not on its own |
| B6 | 4 | `histdata.to_utc` for 2017-2018, and a weekly clock test | `kronos_trader/data/histdata.py` `to_utc` (line 35): stamps before 2019-01-01 are New York local (`tz_localize("America/New_York")`), from 2019 London local minus 5 h as now (the boundary sits in winter where both agree); `tests/trader/test_histdata.py` cases for 2017-03-15 and 2018-11-02 (the line-21 pattern); a data test over any rebuilt `fixed/` file: the NAS100 13:30/14:30 UTC range peak per week follows the US clock (`research/skeptic_pipeline/c3_clock.py` logic); rebuild 2017-2018, rerun the OOS ledgers | six weeks (2017-03-13, 03-20, 10-30, 2018-03-12, 03-19, 10-29) stamped an hour late, verified on the cash-open spike (14:30 wins at 3.6-5.2 x the week's median range) and on time in all 28 mismatch weeks of 2019-2026; 7 OOS trades (EURUSD 1 -1.0R, gold 5 +4.2R, NAS100 1 -1.0R) | NEEDS CODE (3 lines + tests); after B4 |
| B7 | 4 | The spread and the entry slippage journaled at every live entry, compared weekly | `live.py` `_open_locked` (1553): `spread=` on the `setup`, `limit_placed` and `filled` notes (or a `spread` column in `journal.FIELDS`, `journal.py` 17); `parity.py` `markdown`: a line per market "spread at fill: median X (assumed Y); entry slippage: median Z R (haircut 0.10R)" from the journal and `forward_trades.csv`, flagged when the median spread exceeds 1.25 x the assumption or the slippage 0.10R. About 10 + 20 lines | today the spread is written only on a refusal; the weekly laptop prompt compares by hand; 0.05R of fill slippage costs 5 points of the 2026 six-week pass rate (`costs.md`) | NEEDS CODE after A2 (then the first line has a measured value to compare with) |
| B8 | 4 | A direction meter beside the edge meter (unverified angle, `baselines.md` 6.4) | `parity.py`: for every closed live trade walk its mirror image (opposite direction, same fill time and price, same stop and target distances, break-even and time exit) on the FTMO 5m candles (`research/baselines/baselines.py` `Market.walk` is the walker); direction score = the sum over the last 30 closed trades of (r_real - r_mirror) / 2; the same walk gives a timing score (r_real against the mean of the 6 candles after the signal). About 40 lines | backtest values a trade: EURUSD +0.52, gold +0.43, NAS100 +0.70, BTC +0.51 (2024-26); +0.19, +0.03, +0.19, -0.16 (2017-23); a 30-trade score <= 0 says the market's direction calls run as coins (BTC's 2020-23 state) while the edge meter may still pass on timing | NEEDS CODE; not before the parity report has a month of trades |
| B9 | 5 | A trading-hours and holiday line per market in the parity report | one-off first (D7, no code): first and last 5m candle per day in New York time and the days without candles from the exported candles under `journal_ftmo/parity/`, plus the symbol's Specification window; build the ~30-line `parity.markdown` line only if a bound differs from the research data (EURUSD 17:00-16:55, gold 18:00-16:55, NAS100 18:00-16:10 NY; holiday early closes 12:55 / 14:25) | 6 of 43 IS NAS100 trades held through the 16:15-18:00 break (+7.7R); 13 IS entries on US holiday mornings net -0.5R; the US100.cash schedule 16:15-17:00 NY is recorded nowhere | NEEDS CODE only after the readout |
| B10 | 5 | `scripts/risk_steps.py --bootstrap N --block month|2w --seed S` | resample calendar-month blocks of the combined ledger before `challenge()` (about 40 lines, scripts only) | the research already ran it (`risk_verify1.py` section 4: 1,000 paths, guard on); a convenience, not evidence; build when the research scripts are retired | NEEDS CODE, last |
| B11 | 5 | Gold: no trade against the 4H 50-candle mean (unverified angle, `regime_gate.md` 6.1) | `bias.trend_filter_4h_candles: 50` (0 = off) in `BiasParams`; in `engine.py` next to `trend_filter_days` (468-477): `closes = views[Timeframe.H_4].close; mean = closes[-50:].mean(); reject when (closes[-1] - mean) * direction.sign < 0`; about 10 lines + a test; the 4H view must hold closed candles only (the live loop fetches 400 4H bars) | ledger: IS 143 -> 125 trades, +71.8 -> +71.3R (2024 +3.1, 2025 -0.3, 2026 -2.3), OOS 371 -> 304, -62.2 -> -31.9R, better in 7 of 7 OOS years; plateau 50-80 candles; replay OOS both phases 11 -> 20 %, IS median 84 -> 97 d, 2026 six weeks 71 -> 67 % | house rule: fails (IS flat, slower in sample); FOR MAX whether an OOS-only insurance is wanted on the funded account; not for the challenge |
| B12 | 5 | Gold at half stake when ER20 < 0.2; NAS100 no trade at ER20 >= 0.5 (unverified, `regime_gate.md` 6.2-6.3) | `risk.regime_risk_multiplier` (ER20 of the last 21 closed daily closes handed to `setup_risk` like `aligned_count`, `risk.py` 272-300, about a dozen lines); `bias.max_er20` in the same engine block | gold IS -9.8R of 71.8 for OOS +30.7R; NAS100 7 trades -1.6R IS, 10 trades -6.7R OOS | after B11, if at all |
| B13 | 5 | Stake by planned R:R (unverified, `metalabel.md` section 4) | a `risk.planned_rr_risk_multiplier` table in `setup_risk` (`risk.py` 272-300), about 10 lines; judged in the backtester with the ladder and the guard (drawdown growth and the stacking cap are the open points) | the trades with a planned R:R of 3 or more carry the R in both periods (+1.81R a trade IS, +0.37 OOS) while the rest is +0.40 / -0.21; a stake lever, not a filter | after A3; only with the replay |

Dropped code items (reasons in E): `prop_firm.max_open_risk_pct`, `risk.size_basis`, `risk.min_tp_atr`,
`confirmation.stop_within_zone`, `structure.breaker_zones`, `structure.min_x_age_candles`,
`prop_firm.weekend_close_min_risk_pct`, the gap-sized target protection, the exact cushion rule, the engine's
spread-by-hour table and the stop-slippage model in `paper.py`.

## C. Methodology analyses on the existing ledgers (script outlines)

C1. **The evidence block per change** (for task 81 and every adoption from now on). `research/evidence_block.py
SYMBOL candidate.csv [oos_candidate.csv]`, one markdown row plus a details block: (1) n, won %, sum R and mean R after
0.10R, IS and OOS; (2) the month-block bootstrap 95 % interval on the mean and P(mean <= 0) (`research/stats1.py`,
`research/skeptic_method/check.py`: lag-1 autocorrelation -0.13..+0.11, so month blocks and iid agree); (3) the mean
without the top 3 winners (NAS100's whole OOS total is its three best trades: -0.6R on 97 without them; in sample the
top 3 carry 63 % of BTC's and 53 % of NAS100's total); (4) the DSR at N_eff from `research/walkforward/inventory.csv`
(N_eff = variants whose trade sets differ by >= 20 %: 146 / 73 / 75 / 98; DSR 0.42 / 0.82 / 0.38 / 0.22 at the iid
variance); (5) `candidate_check.py`'s verdict (screen, the five windows, the haircut gain against the floor); (6)
the OOS total against the live profile's; (7) the replay row (`challenge_sim_set.py` with the env var); (8) for a
numeric knob the plateau line (live against +-1 / +-2 steps). Today's rows for A4, A5, A8 are in section A.

C2. **The overfit screen on every engine run as it lands.** `cd $S/research/walkforward && python3 candidate_check.py
SYMBOL <ledger.csv> <label>` (10 s). Done on oct14d: `ban` PASS (4 of 5 windows above the grid median, haircut gain
+8.7R of a 22R floor), `stack` PASS (+8.0R), `dep25` PASS (5 of 5, +2.3R), `usob` PASS (5 of 5, +2.9R of 16R),
`both` PASS (+2.0R): every oct14d winner is a genuine small improvement on 2024-2026 and none is large enough to be
distinguishable from the grid's luck. Applied to oct14b/c earlier: nothing adoptable (`candidate_check_out.txt`).

C3. **Reading the A7 map.** `research/plateau_map.py <dir>`: for each market a 5 x 3 table of IS R (and OOS where
run), the live cell's ratio to the median of its 1-D neighbours along each axis, the minimum neighbour, the 2-D
ridge (the best cell per row and per column: a ridge along one axis says the knobs interact); verdict per the rule
in A7 (plateau / peak / ridge), and for a ridge the pair to set together. Pattern: `research/skeptic_method/check.py`
(the reading of the existing 26 knob-market cells: 24 plateaus; EURUSD `be_at_r` and NAS100's cap are range-end
artefacts, not peaks).

C4. **A paired month-block bootstrap of the 2-Step for a candidate set.** The `risk_verify1.py` section-4 pattern
(1,000 paths of 24 calendar months drawn with replacement from the 33 IS months, re-dated, the 2-Step from day 1 of
the path, the guard on, the live multipliers and ladder; 600 paths for the two stresses), run with the SAME seed for
the base and for the candidate ledger set (A4, A5, A8; A3 is done in the research): outputs funded %, within 90 days,
dead %, median days, and under 0.25R costs and the winners halved for a stake change. This is what separates "the
one historical order of the months" from a real speed gain (A3's historical gain sat in the 2025 cohorts; the paired
bootstrap showed none, and the tail gain was what remained).

C5. **BTC on the NY ledger, re-read.** Once `nybase` exists: `research/baselines/baselines.py` on it (direction and
timing nulls, both periods; on UTC candles BTC's direction call was inverted in 2020-23, z -1.6, and the 09-11 window
was the whole IS result, +53.4R of +61.7R); the hour table of `research/ledgers_anatomy.py`; `research/costs/
cost_model.py` with the measured spread (A2); `research/regime_gate/` found no regime cut on either candle set.
The decision table for Max: R a trade after true costs IS and OOS, the replay with and without BTC (today 54 % against
45 % six-week passes, +5.0 against +4.7 %/mo), the 2020-23 column.

C6. **The per-trade cost model on the costed ledgers** (after A2): `research/costs/cost_model.py` on `$S/oct14j/`:
cost_R p50 / p90 per market, the share of trades above 0.10R, the cap's refusals, the by-hour table; the engine's
spread-by-hour table in `paper.py` (about 60 lines) is built only if the measured 09:00 crypto spread differs from
the day's median by more than the 0.10R it would move (the 09:00 Amsterdam hour carries +49.3R of BTC's +61.7R at
cost_R p50 0.22 on the assumed spread). The stop-slippage model is not built: 0 of 158 IS stops gapped at 5m or 1m.

C7. **Trials and N.** `research/walkforward/inventory.py` over the provenance files is the trials ledger (1,700
files; 252 / 151 / 132 / 192 runs on the window, 220 / 131 / 116 / 161 distinct trade sets); the README states N and
N_eff beside each in-sample total and treats EURUSD, NAS100 and BTC in-sample gains as undeflated; MinBTL at N_eff
is 4.2 / 2.2 / 4.9 / 5.3 years against a 2.7-year window (only gold's window is long enough for its grid).

C8. **Process rules (no code).** (1) Pass criteria and the windows are written before a run; 2017-2023 is read once
per candidate; the forward journal and the weekly parity check are the only holdout that regenerates. (2) A change is
adopted under the strict rule above; the house rule is the minimum and is stated beside it. (3) The 2024-2026 window
is spent for EURUSD and NAS100 (PBO 0.58 / 0.73): a candidate there is read on 2017-2023 first (not below the live
profile) and decided by the forward journal, the 2024-2026 run being the sanity check; on gold (0.22, haircut 0.75)
and BTC (0.45, 0.5) the window still ranks. (4) A random-timing null draws its candidates after the signal candle
(the whole-window null collects the shift's own impulse: gold +58.9R before against +25.7R after). (5) Replay levels
are compared within one script only. (6) Every batch's `jobs.json` carries its expectation and decision rule in the
backlog before it runs (A6, A9, A10 above).

## D. Prop-firm and operational items (the challenge now, the funded phase after)

D1. **Status quo, settled, nothing to run (FOR MAX: no change).** The guard's worst-case day limit 4.0 % and floor
9.5 % (`PRODUCT=ftmo_2step`; 4.5 % identical, 4.9 % fails 9-14 % of starts at 0.25R costs, the 8 % floor stalls
17 %); `PROTECT` unset (half the stake in the last 4 % costs 12 points of 2026 six-week passes, 0 failures either
way); the base 1.5 % (the knee: within 90 days flat from 1.5 % up, stalls 2.1 / 5.5 / 8.8 / 16.9 % at 1.5 / 1.75 /
2.0 / 2.5 %); the three halving multipliers (the 50/50-month half holds in both halves and OOS; EURUSD's 1D+1H half
neutral per unit of risk, halves the drawdown; BTC's half until A1 is settled); phase 2 at the same base (2.0 % stalls
7.7 % of paths, 1.0 % loses 11 points on 2026); the ladder -3 -> 1.0, -6 -> 0.5 (no ladder: dead 8.2 % against
2.1 %); two open on the account; no month, week or day stop and no cool-down (after-loss trades +31.9R).

D2. **Before the first funded day (Standard account).** B1 must exist and be on (`FUNDED=1`). Ask FTMO support in
writing whether BTCUSD is in the USD restricted set (its table names USD pairs, XAUUSD, US indices and DXY, not
crypto): the cost of the rule is -55R of 241R IS with BTC and -22R without. No new purchase helps the running account;
for the NEXT purchase a Swing account (no news or weekend rule, 1:30 / 1:10 / 1:1 leverage) pays the same as Standard
with the rules (3.27 against 3.19 %/month) with nothing to execute. The rule-based cousin, A5, removes the EURUSD
14:30-16:00 entries whatever the calendar says.

D3. **Funded settings and the payout rhythm (set, calendar only).** `FUNDED=1` in `scripts/ftmo_local.bat` gives
`--risk-pct 1.0 --drawdown-steps=-3:0.5 --weekend-close 15:45` (lost within 12 months 2 % at 1.0 % with the step; at
the challenge stake 22-71 % of accounts drift to the floor); the first Reward on day 14 after the first trade when
the closed profit is $20 or more, then every 14 days, requested on Friday after the 15:45 close with every position
and pending order closed (FTMO requires it), everything above the initial balance withdrawn; the 14-day cadence pays
the same as monthly (3.11 against 3.19 %) and meets the Scaling Plan's two payouts per four months from 98-100 % of
starts (then the 90 % split). No cushion (-0.07 %/month, prevents nothing).

D4. **At +10 % (until B3 exists): the manual rule** in `docs/LAPTOP_TASKS.md`: with four trading days logged, let
the open positions finish, stop the windows outside the sessions, request the verification; with fewer than four,
Max chooses between trading on (the replay: trading on and stopping give the same result when the request is made at
the 22:05 report) and the minimum stake. Phase 2: a new login, `TARGET=5`, the day count starts again (premortem
section 14 checklist).

D5. **Weekends in the challenge: no filter.** FTMO allows holding over the weekend in the Challenge and Verification;
the double-stake positions carry 3.5 of the 17.6 summed instant-fail points over 32 months (about 0.3 % a
challenge) and closing only them costs 2-9 points of passes; the full close (`WEEKEND_CLOSE=15:45`, one line in
`ftmo_local.bat`) is no worse on passes (42.7 / 52.8 / 81.1 / 11.2 %), costs about 8R over 32 months and removes the
whole weekend tail (about 1.9 % a challenge). FOR MAX only if the variance should go; the largest wrong-side weekend
gap met in 2024-26 was 0.26 stops.

D6. **NAS100 overnight.** The single stake on NAS100 4H zones halves a 0.2 %-a-challenge tail and costs 3 points of
2026 six-week passes: not taken. If the tail must go, `exits.day_close: "22:10"` (built, -1.6R over 38 trades) removes
all of it including the 1H-zone share; the clock must sit before FTMO's US100.cash daily close (D7's readout). Not
during the challenge.

D7. **Laptop, read-only (prompts in `docs/LAPTOP_TASKS.md`; results to `kronos_notes\`).** (1) The spreads of NAS100
and BTC over three weekdays (A2). (2) The BTCUSD W1/D1/4H stamps from the parity export (A1's W1 convention). (3) The
trading hours and holidays of US100.cash and XAUUSD from the exported 5m candles (first and last candle per day in New
York time, the days without candles) and the Specification window (B9's readout). (4) The restart checklist after any
profile change. (5) The DST-mismatch week 26 October - 1 November: on Monday 26 October check `MT5_SERVER_OFFSET`
in the start rows, the 5m feed's freshness and the session clock in the 08:45 briefing (premortem section 6). (6)
Patch Tuesday 10 November and Thanksgiving 26-27 November: the windows do not restart themselves; a logon task is
Max's choice. (7) No manual positions beside the windows (the guard cannot see them).

D8. **Data to keep current (no code).** `data/calendar/high_impact.csv` ends 13 November 2026; the live loop refreshes
this week's events from ForexFactory every hour, so the seeded file matters only when that feed fails (about 5 % per NFP/CPI day): extend
it through December before 13 November. The spread cap live: at a $45 BTC spread it refuses the small-stop trades
(5 of 89 IS, +25R booked) and at 5 points a fifth of NAS100's; A2 decides whether the profiles' `min_stop_pips` move
(BTC 150 at >= $40, NAS100 17 at 5 points), not before.

## E. Dropped (one line each, why)

SMC literature (`skeptic_smc_verdicts.md`):
- Target 5 % short of the pool (`risk.tp_buffer_fraction 0.05`, `tp_buffer_pips`; jobs `tpb_*`, `tpf5_*`): worse in all four IS cells with the live break-even (gold -12.1R on the winners), rescues 0-5 near-misses a cell, not monotonic at 97.5 / 95 / 90 %, sign flips by year; the exact walk says -6.1R IS; remove `tpb`/`tpf5` from oct14g/h.
- NAS100 break-even at +2R: engine -4.5R IS (three trades), -0.6R OOS; the README's 6 October "no (mixed)" stands.
- Breaker / inverse-gap zones: needs code; after the zone's P is closed through the 24 h move in the break's direction is negative in sample (-0.45..-0.57 zone heights), 26-45 % won at 2:1 before costs.
- Minimum age of the swing X: needs code; the young-X buckets are the best in sample (+0.98R a trade at 1-3 candles), the rule at 6 removes +142.2R and keeps +95.2R; nothing OOS.
- EURUSD day-open drift (`require_day_drift`, job `drift_EURUSD`): holds on the exact clock (10 IS trades), flips one hour later (OOS +10.0R removed), 2023 and 2024 carry it, 2026 goes the other way, 24 of 33 removed trades already at half stake; remove from oct14h (if run anyway, the 23:00 / 01:00 variants and the replay sit on the same table).
- Stop beyond the whole sweep sequence (`stop_window_includes_sweep`, `swp`) and the short's spread stop (`short_stop_spread`, `sss`): engine 0 / -1.1 / 0 / 0R and -2.3 / -3.0 / -0.3 / +0.8R; touches 0-2 % of trades; the README's "a few pips more" at a smaller size.
- Killzone and silver-bullet windows, time stops and stale exits, trailing to structure, partials, ATR-scaled minimum stops, previous-day/week extremes as targets, premium/discount of the 1-20 day range or the week open, Judas / Asia-range sweeps, displacement strength (`smc_literature.md` 2.1-2.7): all negative on zone entries.

Prop-firm (`prop_firm.md`):
- Double-stake positions flat before the weekend as a filter: removes about 0.3 % of fail chance a challenge for 2-9 points of passes; the existing full weekend close dominates (D5).
- NAS100 4H zones at the single stake: a 0.2 %-a-challenge tail, 2026 six weeks 56.1 -> 53.3 %; `exits.day_close` is the knob (D6).
- Raising the guard to 4.5 / 4.9 %: identical / fails 9-14 % at 0.25R; the 8 % floor: stalls 17 %.
- `risk.target_protect_pct` (2 / 3 / 4 %), the gap-sized protection (needs code, -3.7 points on 2026): slower, no fewer failures.
- A cushion in the funded account, a slower or faster payout cadence, a dollar-cluster rule, a day / week / month stop, a cool-down after losses, raising the stake near the end of a phase: measured, worse or neutral.

Methodology (`methodology.md`, `walkforward.md`, `baselines.md`):
- A1 CSCV, A2 walk-forward, A3 bootstrap intervals, A4 DSR / MinBTL, A5 Monte Carlo of the 2-Step, A8 random-entry baselines: run in full today; nothing left to compute (the numbers go in the README via C1); the "full" A2 (500 engine runs per window) cannot cure the hindsight contamination of the variants and would not change the verdict.
- Full plateau maps of every knob: 24 of 26 cells are plateaus and the knob-grid PBO (0.82 / 0.27 / 0.43 / 0.81) says the window cannot pick a better value; only `min_gap_fraction` is mapped (A7).
- The engine's spread-by-hour table and the stop-slippage model in `paper.py`: limit fills are already trade-through in 87 of 90 cases, no IS stop was gapped, the by-hour table moves under 0.10R unless A2's crypto measurement says otherwise.
- Masters' permuted-returns null through the whole engine: the heavier follow-up, not before the forward record has a month.

Loss anatomy (`ledgers.md`):
- BTC no signal 16:00-16:59 (jobs `end1530*`, oct14e): 11 IS trades all 2024, OOS p 0.52 (the base rate), UTC candles; remove oct14e's `end1530`, `end1530b` and `stack` (and `meo`, `tpfloor3`: BTC jobs on UTC candles; re-written on `btc_ny_old` only if A1 keeps BTC).
- Gold target at least 1 ATR away (`min_tp_atr`): on the engine's ATR the IS effect is zero (-0.3R), needs code.
- Gold stop beyond the zone's far edge (`stop_within_zone`): 7 IS trades, 4 of them in the depth band, OOS noise cancelling (2022 -9.9R against 2023 +6.7R), needs code.
- EURUSD stop >= 0.5 ATR (`msa05`): the ledger feature is the fill-to-stop distance, the knob measures the confirmation close at the signal (4 IS trades -1.2R); the queued run confirms the null, nothing to adopt.
- NAS100 depth 0.25 / 0.125 (`dep125`): the band is +2.8R IS on the engine's measure.
- The gold stack A+B+E+F+G: removes 45 % of the IS trades for +13R, the OOS R a trade falls (-0.17 -> -0.24); one rule at a time.
- Consecutive losses, weekday, month of the year, visit number, zone timeframe, bias combination, direction, entry distance outside the zone, zone height against ATR: no cut negative in both periods; near misses kept for the record only (gold `no_trade_against: [1D]` +1.6R IS / -16.8R OOS; all-five-aligned at half stake; NAS100 planned R:R under 1.5).

Pipeline (`pipeline.md`):
- The backtester's clock: clean (no look-ahead; append-only check identical; intra-candle rules conservative); the `MultiTimeframeData.as_of` debug assertion is optional hygiene, not a candidate.
- The 1m file in the BTC directory: 2 trades, -2.0R; gone with A1 (the NY directory has none).
- The 23:00 Amsterdam restart and the rollover spread widening: outside the windows; the nearest approach to a gold stop in the first 15 minutes after 18:00 NY was 8.2 pips once in 36 exposures.

Risk (`risk_model.md`):
- The cushion ladder (`drawdown_steps [[-4,1.25],[-5,1.0],[-6,0.75],[-7,0.5],[-8,0.25]]`): half a point of rung placement moves the stress result by 8-15 points, the paired bootstrap adds +1 funded / +2 within 90 days over A3 alone and nothing under either stress; with x1.5 a single 4H loss no longer reaches -3 %, which removes the motive; revisit with forward data.
- A cap on combined open risk (2.5 %, needs code): identical to A3 once A3 is in (58 of 651 starts differ in timing only).
- Kelly or half-Kelly as the base (22 % in sample, 0 % OOS for three markets): the wrong objective for a barrier problem.
- Per-market stakes, grade weights beyond the three, gold's 4H at x1 (a wash against x1.5 everywhere; 13 IS trades against 48 OOS), all-five-aligned at half, a Kelly weight per grade cell, losing-streak and moving-average rules, one open on the account, a same-direction factor, a per-day stake cap, a different phase-2 base, dropping the ladder: measured, neutral or worse.
- Sizing on the initial balance (`risk.size_basis`, needs code): changes 80 of 651 starts' timing and no aggregate; hygiene for a later restart, not research.

Batches (`RESULTS_14oct.md`):
- oct14b (33 knob runs, IS): break-even 1 / 2 / 3R, caps 2 / 3R, depth 0.3, minimum stop 10 / 12 / 100, R:R 0.8 / 1.0 / 1.2, stop offset 1 / 2 / 3 / 20, the 15-minute scalp set (BTC -18.2R), the New York window (gold -13.3R): nothing above the base (0 to -28R); the profiles sit on a plateau.
- oct14c (`fv`, `nop`, `sss`, `swp`): the engine review's fidelity variants, none adoptable (above).
- oct14d losers: `tpfb3` (gold 3R fallback: IS -0.1R, OOS +21.5R: flat IS, the OOS gain is the 2R fallback's own weakness there), `mm3` (EURUSD three of five: IS -1.1R, OOS +9.9R; the 1D+1H pair is at half stake live already), `ta12` (12 h touch age: -2.2R / +0.2R), `from10` (EURUSD no 09:00 hour: -1.7R / +4.9R), `both` (usob + from10: 27 trades; its extra OOS R is the 09:00 cut's, which fails IS), `stack` and `stack37` (gold depth + 3R fallback + ban: IS +10.7R but 2026 -7.0R, replay 2026 +10.0 against +10.9 %/mo: the stack trims the best year).
- `ts8` (time stop 8 h at -0.5R, oct14f): -16.9R / -12.7R by the exact walk; remove from the chain.

Post-verify angles (unverified, recorded so they are not rerun):
- Meta-labeling (`metalabel.md`): no model, feature set or threshold improves R in both periods (31 features x 3 models x 3 sets; CV AUC under 0.5 in 25 of 30 IS cells); the win label prefers the low-R:R trades; nothing goes live.
- MAE / MFE (`excursion.md`): a wider or tighter stop, a nearer target, break-even at 1 / 2 / 3R, a time or no-progress exit: 0 to -82R IS over the four markets, none passes both periods; the current rules are each confirmed; 85-96 % of the losers run through a stop 1.5 x as wide (the entries lose, not the management).
- Regime (`regime_gate.md`): the daily ATR percentile, the week's range spent and its pace, the weekday of the zone's formation or first touch, BTC regime cuts of any kind, EURUSD / NAS100 ER20 or ATR cuts (except NAS100 >= 0.5, 17 trades), the 4H trend as a raw state, gold's ER line at 0.25 / 0.3, a gold gate limited to the ranging regime: turn between the periods.

## F. Angles written after the verify pass (not merged into A-E as verified; where they were folded)

- `walkforward.md`: the strict adoption rule and `candidate_check.py` (preamble, C2, C8); CSCV PBO 0.58 / 0.22 / 0.73 / 0.45, anchored WFE 0.14 / 0.84 / 1.09 / 0.79; the 2024-2026 window is spent for EURUSD and NAS100.
- `baselines.md`: the direction meter (B8); the morning window's direction calls are coins in every market and both periods; gold's 4H double stake rests on 13 IS trades and fails both nulls OOS (A3 reduces it to x1.5; gold at x1 stays dropped); a method note on the timing null (C8).
- `costs.md`: the per-market cost rules (A2, C6), the funded month +6.0 % (base) to +5.3 % (pessimistic with the cap) against +5.7 % flat; the BTC NY ledger at the base costs about +19R, pessimistic +8R.
- `excursion.md`: closes B6 and B7 of the hand draft (E); the near-miss message's definition (a stopped trade whose MFE reached 80 % of its target or +1R: report it, propose nothing); the "open risk to the stops" line, not the floating P&L, is the number to watch (a live winner is routinely 0.4R under water).
- `metalabel.md`: negative (E); the stake-by-planned-R:R lever (B13); any future quality score is scored on R, not on wins.
- `regime_gate.md`: the gold 4H-50 trend gate (B11), the ER20 rules (B12), the negatives (E); NAS100's counter-trend trades are its best in both periods (3-10 IS trades: an observation).
- `premortem.md`: the ranking of failure modes for 14 October - 30 November (D4-D8): the early target, the double-stake gap, a pulled commit at a restart (a pinned commit and try/except around the notices are its code items, outside this research backlog), the DST week, Telegram silence, the laptop's sleep and updates, the spread cap, the margin cap on 10k (BTC lots cut in 74 % of trades), the calendar after 13 November, phase 2 on a new login.
- `regime_now.md`: situational (the four markets on 14 October and the calendar to 7 November); no backlog item.
- `research/liquidity_map/` and `research/invariants/` were still being written at 17:30 and are not read here.

## G. The ten to run now, in order

1. A1 `nybase_BTCUSD` IS + OOS on `$S/btc_ny_old` (oct14g, 2 jobs), replay with and without BTC; LAPTOP: the W1/D1 stamp readout.
2. A2 LAPTOP: three days of `mt5-spreads` on NAS100 and BTC; then the four research ledgers with the measured spreads, commission and the 30 % cap (8 jobs) and the replay at 0.05R.
3. A3 the 4H x1.5 replay on the repository-side script (base, x1.5, both stresses), then FOR MAX.
4. A4 `ban10_XAUUSD` and `ban15_XAUUSD` IS + OOS (oct14i), screen and replay: attribute the gold 10:00 cut and read the 2026 speed.
5. A8 `dep20_XAUUSD` and `dep30_XAUUSD` IS + OOS (same batch): plateau or peak.
6. A5 FOR MAX: EURUSD 14:30-15:59 (every number is in); the paired month-block bootstrap (C4) beside it.
7. A6 `prot_*` IS on the four markets (oct14g), OOS only where IS holds.
8. A7 the `min_gap_fraction` x touch-age map on gold, EURUSD, NAS100 (oct14k, 33 IS + about 12 OOS jobs), read with C3.
9. A9 `mva30_XAUUSD`, `mva30_BTCUSD` (oct14h; BTC on `btc_ny_old`).
10. A10 the oct14f remainder without `ts8`; B1's build starts in parallel (the one code item with a deadline).

Prune the chain before restarting it: drop `tpb_*` (oct14g), `tpf5_*` and `drift_EURUSD` (oct14h), `ts8_*` (oct14f)
and all of oct14e; they are measured or on the wrong candles (E). The order above puts the two items that change
what every later ledger says (A1, A2) first.
