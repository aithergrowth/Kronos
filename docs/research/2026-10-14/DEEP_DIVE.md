# Deep dive, 14 October 2026 (evening): the six verified angles and what they change for the FTMO 2-Step

Day 2 of the challenge (live since 13 October on EURUSD, XAUUSD, NAS100, BTCUSD, one window a market, from the laptop;
repository HEAD 326e028, read-only here). Inputs: the six angle files written this afternoon (`walkforward.md`,
`baselines.md`, `excursion.md`, `costs.md`, `premortem.md`, `regime_now.md`) and their skeptic notes
(`verify_walkforward.md`, `verify_baselines.md`, `verify_excursion.md`, `verify_costs.md`, `verify_premortem.md`,
`verify_regime_now.md`: each a re-derivation from the raw ledgers, the 5m candles or the code with independent scripts
under `research/verify_*/`), plus `RESULTS_14oct.md` (the engine's own batch numbers) and `BACKLOG_hand.md` /
`BACKLOG.md` for what is already queued or settled.

Conventions. R is after a flat 0.10R a trade unless "true" or "walk" is said. In sample (IS) = 2024-01..2026-09 on the
live profiles at 1 % units, guard off: `aca/eutwo_EURUSD` 47 trades +39.5R, `aca/base_XAUUSD` 143 +71.8R,
`aca/rr08_NAS100` 43 +32.9R, `aca/base_BTCUSD` 89 +61.7R (+206.0R together). Out of sample (OOS) = 2017..2023 (BTC
2020-06..2023): 97 / 371 / 100 / 130 trades, -1.2 / -62.2 / +28.8 / -41.6R. Replay levels are comparable only within
one script (`BACKLOG.md`): the pre-mortem's account walk (`prop_lib`-style; both phases within 42 days 54 % of the 2026
starts) and the costs replay (`challenge_sim_costs.py`; both phases within six weeks 71 % of the 2026 starts) score the
same base at different levels, so every replay number below names its script.

Rule of the write-up: a number is quoted as the skeptic re-derived it; where the angle and the skeptic disagree, the
paragraph says which reading is followed and why. Nothing here changes a live profile during the challenge. Section 1
ranks the items by how much they move the odds of passing inside the window (14 October - 30 November) and gives each
one of five actions: none / config after the challenge / code, off by default / laptop check / decision for Max.

The one item with a cost tomorrow: `data/calendar/high_impact.csv` line 2860 puts the 15 October retail sales at
13:30 UTC where the release is 12:30 UTC (the PPI slot); `Calendar.add` appends and never removes, so on 15 October
every market is blacked out 14:00-16:00 Amsterdam instead of 14:00-15:00 (item 8).

## 1. What changes the odds of this challenge, ranked

| # | What | The verified number | Action |
|---|---|---|---|
| 1 | The regime, not a rule, sets the pass rate | phase 1 within 47 days: 99 % of 2026 starts, 46 % of 2024-25, 9 % of 2017-23 (pre-mortem walk); 2026 carries +114.2 of the +206.0R in sample | none: no stake increase; the ladder and BTC's half stake stay |
| 2 | +10 % comes early and the windows trade on at full stake | +10 % before the 4th trading day in 31 % of 2026 starts; trading on after a pass undoes it within 3 days in 7-12 %; the finish rule lifts both phases within 42 days from 54.1 to 57.3 % | decision for Max (a manual rule now); code, off by default, after the challenge |
| 3 | A gap through a double-stake 4H position: the one instant fail the guard cannot see | 0.28 weekend-held x2 positions expected in the window; 31.2 / 12.7 / 7.7 % of NAS100 / EURUSD / gold weekends gap more than 1.67 median 4H stops; about 1.7 % over the window | decision for Max (Friday rule in New York time; NAS100 single stake or x1.5 as config at the next restart) |
| 4 | BTC: an unmeasured spread and an unverified candle anchoring decide its contribution | +35.7R of BTC's +70.6R raw are two shorts stopped at any spread above $15.4 / $21.8; New-York-anchored candles +33.3R against +70.6R; without BTC both phases 99 %, six weeks 50 % against 78 % (costs replay, base) | laptop check (window spreads, D1/W1 bar stamps); decision for Max after |
| 5 | True execution costs | both phases 100 % base, 94 % pessimistic, 89 % pessimistic + cap (costs replay); the 6-11 % "unfinished" are parked at the -9.5 % floor; 2026 starts 33-40 days in every scenario | none now; config after the challenge |
| 6 | The daily-loss guard is FTMO's rule up to a 1 % buffer and blind to hand-opened positions | guard off: 7.1 % of 2024-25 starts break a limit; on: 0 %; `open_positions` keeps only the bot's magic number | decision for Max (manual rule: no hand trade beside a running window) |
| 7 | A restart runs the branch head untested | 44 commits since 7 October, no tests and no pip install on the laptop; the notice bug fixed (adc3f64), no PIN line | code (one guarded checkout line) + a manual diff rule |
| 8 | The seeded news calendar | 15 Oct: 14:00-16:00 Ams lost on all four markets; nothing after 13 Nov; the Friday watchdog gap | data fix; decision for Max on a restart before 15:00 Ams on 15 Oct |
| 9 | NAS100's unmeasured morning spread | median cost 0.055 / 0.109 / 0.182R at 1.5 / 3 / 5 points, 21 % refused at 5; the cap at a limit is effectively 40 % | laptop check; config after |
| 10 | A sleeping laptop, Patch Tuesday 10 Nov, a reboot | 2.3 trades a week at +0.66R; nothing restarts the windows | laptop check |
| 11 | Telegram is the healthchecks check's only integration | the watchdog's alerts and the check's alert die with Telegram | config now (an e-mail integration) |
| 12 | The DST-mismatch week 26 Oct - 1 Nov | code and tests confirmed; mismatch-week trades +0.74R a trade against +0.76R elsewhere | laptop check on Monday 26 Oct |
| 13 | Trade management: nothing left on the table | stop 1.2x -47.2R, break-even +2R -20.8R, hold 24 h -21.2R, target 5 % nearer -6.1R (in sample, four markets) | none; backlog B6 and B7 close |
| 14 | The knob batches | the largest oct14b gain +0.8R (paired t 0.12); a knob's paired SE 5.5-7.7R | none during the challenge; a process rule |

### 1. The regime, not a rule, sets the pass rate (none)

- The pre-mortem's account walk (live stakes, ladder, guard, 0.10R costs, `research/verify_premortem/ledger_checks.py`):
  phase 1 within 47 days from 99 % of the 220 2026 starts (92 % at 0.25R costs, 97 % without BTC), 46 % of the 700
  2024-25 starts, 9 % of the 2,314 2017-23 starts; both phases within 42 days 54.1 % of the 2026 starts. The costs
  replay says the same in its own units: 2026 starts reach both phases in a median 33-40 days under every cost
  scenario, 2024 starts in 65-91 days and 2025 starts in 109-133 days.
- The in-sample result is one year's: 2026 is +36.3 of gold's +71.8R, +24.7 of NAS100's +32.9R, +39.6 of BTC's +61.7R,
  +13.6 of EURUSD's +39.5R (+114.2 of +206.0R), and the direction z is highest in 2026 on every market (gold +3.14,
  NAS100 +2.14).
- How much of that is regime: across 37 market-years the real R a trade correlates 0.60 with what a trade random in
  both direction and timing makes with the same geometry (0.68 on the 33 years with 10+ trades), but most of that is
  the null trades walking the same price paths (trade-level correlation 0.47 with the own both-random mean, 0.73 with
  the after-signal mean); net of the trade's own baseline the yearly excess correlates 0.36 with the baseline (13 % of
  the variance, p about 0.03), and last year's baseline predicts this year's result at 0.30. Followed: the skeptic's
  "small but real" over the angle's "40 %": the 40 % is mostly shared path.
- The honest out-of-sample numbers are the 2017-2023 ratios of mean R (OOS / IS): EURUSD -0.02, gold -0.33, NAS100
  +0.38, BTC -0.42, and the direction call has no support there in any market (z +1.24 / +0.42 / +1.04 / -1.63,
  combined +0.73; -0.3 once EURUSD and NAS100 are read on their market-order ledgers).
- Implication: the replay's pass rate is a property of the start year; the challenge's odds are good because 2026 is
  the expansive regime (a random trade with a 1R stop and a 2-3R target made about 0R a trade in 2024-26 and -0.05 to
  -0.33R in 2017-23), and nothing in the rules can be tuned to keep that. Action: none; no stake increase from any
  in-sample figure; the ladder (-3 %: 1.0, -6 %: 0.5) and BTC's half stake are the hedges and stay.

### 2. +10 % comes early and the windows trade on at full stake (decision for Max now; code, off by default, later)

- Numbers (pre-mortem walk, re-derived): +10 % first touched before the 4th trading day in 31 % of the 2026 starts
  (7 % of 2024-25, 4 % of 2017-23); trading days in 47 days median 6, p10 4, minimum 4; median days to +10 % 20
  (2026); back under +10 % at any close before the qualifying pass 10 % (2026; 68 overlapping daily starts) and 33 %
  (2024-25; 46 starts, the same few trade sequences); after a qualifying pass, trading on undoes it within 3 days in
  7 % (2026) / 12 % (2024-25) / 13 % (2017-23).
- The finish rule (0.01-lot day-count trades, the account otherwise flat): both phases within 42 days 54.1 -> 57.3 % of
  the 2026 starts in the skeptic's walk (the pre-mortem quoted prop_firm.md 3.3's own walk, 56.1 -> 59.4 %); phase 1
  within 42 days unchanged (92.7 %). Followed: the skeptic's reading that the rule buys time for phase 2, not a
  phase-1 pass; the magnitude (+3 points) is the same in both walks.
- Code as it stands: `stepped_risk` halves only within `target_protect_pct` (off); nothing else in `live.py` reads the
  target; `forward.day_message` prints `target +10 %: reached; N trading day(s)` (distinct Prague fill dates, manual
  fills included); `start_ftmo.bat` gives the watchdog `--target-pct 10`.
- Rule (exact, for Max; the pre-mortem's, with the guard caveat of item 6): when the 22:05 report says `target +10 %:
  reached` (closed balance at or above 11,000): with 4 or more trading days, after 17:00 Amsterdam close the windows,
  let the open positions finish on their server-side stop and target (or close them by hand while the balance stays
  at or above 11,000), request the Verification once nothing is open; with fewer than 4 days, close the windows the
  same way and on each missing day open one EURUSD position of 0.01 lot by hand with a 10-pip stop (about $1 at
  risk) and close it, until the count reads 4, then request the Verification. Never with a window running: the guard
  does not see hand-opened positions.
- Code after the challenge (or now with Max's OK): `prop_firm.stop_at_target: true` and `prop_firm.finish_risk_pct:
  0.10` next to `planned_risk` (`live.py:1485-1500`), days counted as the day report counts them, active on
  `--target-pct` only, off by default (prop_firm.md candidate 1).
- Caveat: the "4 or more days" half of the rule lived in `docs/LAPTOP_TASKS.md` at fecf55e (108 lines); commit 326e028
  wrote the empty blob (0 bytes on HEAD), so today the rule exists only in `premortem.md` until that file is restored.

### 3. A gap through a double-stake 4H position (decision for Max)

- Exposure (ledger, re-derived): 28 double-stake trades in 32 months (0.88 a month, 1.32 in 6.5 weeks); 6 of 28 held
  over a weekend (gold 4 of 13, EURUSD 1 of 10, NAS100 1 of 5), so 0.28 weekend-held x2 positions expected in the
  window; on the combined account 5.0 % of 139 Saturdays had 3 % or more at risk, 0 % had 4.5 %. The six in-sample
  weekend holds all won (+4.68, +1.99, +3.85, +1.99, +4.06, +1.99R; the pre-mortem's three qualifying cases, at 2 % or
  more at risk, would have given up -6.7R if closed on Friday); out of sample 10 of 65 were held, one at -1.37R (a gap
  beyond the stop, -4.1 % at the double stake).
- Gaps (5m candles since 2024, Sunday open against Friday close, in median 4H stops of 0.153 % EURUSD / 0.197 % NAS100
  / 0.548 % gold of price): NAS100 141 weekends, |gap| over 1.67 stops 31.2 % (over 1 stop 43 %, over 3 stops 19 %;
  25 % since 2017); NAS100 nights 8.8 % (577 breaks); EURUSD weekends 12.7 %; gold 7.7 %. Half on the wrong side: 0.28
  x (4/6 x 4 % + 1/6 x 6 % + 1/6 x 15 %) = about 1.7 % over the window of a -5 % day in one print. Order of magnitude
  only: six weekend holds, and NAS100's stop yardstick is 5 trades (at its p25 stop 48 % of weekends gap through, at
  its p75 11 %).
- Mechanism: the stop lives on the server and a gap fills at the open; `prop_firm.weekend_close` and `exits.day_close`
  are empty in the challenge; a 1.67-stop gap against a 3 % position is a -5 % day and FTMO closes the account.
- The Friday rule's clock (followed: the skeptic): state it in New York time, about 15:30-15:45, before the symbol's
  Friday close; "after 21:30 Amsterdam" is after NAS100's close in the mismatch week (the data's last Friday NAS100
  candle opens 21:10 Amsterdam on 31 October 2025 and 13 March 2026, so on 30 October 2026 too). Rule: on Friday read
  the dashboard's open positions; a position with 2 % or more at risk to its stop and not yet at break-even is closed by
  hand if it is NAS100; for gold and EURUSD Max chooses (a wash on expectation, all variance). On 27 November
  (Thanksgiving Friday, early close) the same at about 12:00 New York; the night of 3 November (midterm results) like a
  weekend for a NAS100 x2 position.
- Config alternatives, Max's call whether a stake multiplier counts as a profile change during the challenge (it
  changes no trade): (a) `risk.zone_risk_multiplier: {}` in `config/dorus_live_nas100.yaml` (NAS100 4H at the single
  stake: 5 in-sample trades +6.2R at stake, replay neutral, 2026 passes 100 % either way; `BACKLOG_hand.md` C4); (b) 4H
  zones at x1.5 on all three (`RESULTS_14oct.md`, `aca/challenge_sim_x15.py`): at 0.10R costs both phases 100 % /
  77 days / 2026 six weeks 74 % against 100 % / 84 / 71 %; at 0.25R costs 91 % against 85 %, six weeks 63 % against
  57 %, worst funded month -4.7 % against -5.0 %, for about 0.4 % a month of funded profit; (c) gold's 4H x2 to 1.0:
  the baselines angle's proposal, supported by 13 in-sample trades (+14.1R; 2024 6 trades +8.6, 2025 5 +2.8, 2026 2
  +4.0; the top three trades 10.6 of 15.4R; direction z +1.72, timing +0.77) and contradicted by nothing (48 OOS
  trades -11.5R, direction z -0.02, timing -1.05: no edge, not harm); it gives up +15.4R of the account replay.
  Followed: the skeptic over the angle: a variance decision, not an edge decision, and by the same standard it
  applies to EURUSD's x2 (10 + 10 trades, one 13.1R trade carrying the OOS) and NAS100's (5 + 7 trades). Gold is where
  the exposure sits (4 of its 13 4H trades crossed a weekend, median hold 22 h) and tomorrow's gold short, if it comes
  from the 4H version of 4105-4155, is a 3 % position (section 4).
- Code, off by default: `prop_firm.weekend_close_min_risk_pct: 2.0` as a filter on the existing weekend close (close at
  Friday 15:45 New York only positions with 2 % or more at risk; prop_firm.md candidate 3).

### 4. BTC: the spread and the candle anchoring are unmeasured and decide its contribution (laptop check; decision for Max after)

- What BTC does for the challenge (costs replay, base costs, `challenge_sim_costs.py`): with BTC both phases 100 %,
  median 80 days, funded +6.0 % a month, 2026 starts within six weeks 78 %; without BTC 99 %, 84 days, +5.1 %, 50 %.
  BTC is the speed term, not the pass term; the README's margin cut (crypto 1:2, mean BTC weight 0.33) is not in that
  sim and takes the flat run to 97 % / +5.2 % / 64 %.
- The spread (verify_costs `btc_edge.py`, `exact_walk2.py`, the paper broker's mechanics): the two largest winners,
  P79 (2 June 2026, +11.8R) and P82 (25 June 2026, +23.9R), ran within $0.38 and $6.78 of their stop on the ask at the
  assumed $15; at any spread above $15.4 / $21.8 they are stopped at entry, which takes +35.7R of BTC's +70.6R raw
  away: +58.1R at $15, +17.0R (+0.19R a trade) at $30, +14.0R at $45 in the walk; the 36 long winners lose only 4.1R per
  extra $15. Followed: the skeptic over the costs angle's smooth brackets ("median spread <= $30: nothing changes"):
  the ledger sizes on the stop (`risk_amount = lots x D x value`, exact on 1,020 trades), a stopped trade loses -1R
  whatever the spread, so the additive -5R per $15 is the wrong shape and the in-sample BTC result above about $20 is
  a coin flip on two trades.
- Commission is structural: 0.065 % x entry / stop = 0.106R at the median stop (70 % of BTC's cost); cost_R p50 0.154
  at $15 with 80 % of trades above 0.10R; 33 of 89 trades fall under R:R 0.8 after the full cost (planned p50 1.45 ->
  1.14); at $45 the 30 % cap refuses 5 of 89 that booked +24.5R.
- Anchoring (`BACKLOG_hand.md` A.1, re-checked on today's bars in verify_regime_now): the research candles are
  UTC-anchored, an MT5 server on New York + 7 anchors at 17:00 New York; the rerun on New-York-anchored candles gives
  94 trades, 51 %, +33.3R against 89 trades, 58 %, +70.6R; tonight the 4H bearish gap 83012.38-83251.78 exists on the
  New York bars (bearish scalp, 0.75 % stake) and not on the UTC bars (50/50, no trade). Which anchoring the FTMO
  terminal uses is unverified (task 80). The OOS rerun on `btc_ny_old` is queued.
- The edge's shape: BTC's in-sample result is the direction in the morning window (09-11: 42 trades +53.4R of +61.7R,
  direction-only +32.8R, direction z +2.11), its dearest hour (09:00 Amsterdam, 27 trades, cost p50 0.222R, 85 % above
  0.10R, stops $362) and its most profitable (+47.2R true); out of sample the direction is inverted (z -1.63) and
  2020-23 is -0.320R a trade. The margin cap cuts the lots in 74 % of BTC trades (59 % of the planned risk kept).
- Action: laptop check, this week, no code: `mt5-spreads --symbols NAS100=US100.cash,BTCUSD,XAUUSD,EURUSD --day <date>`
  over three weekdays, median and p90 per window; the D1 and W1 bar stamps of BTCUSD from the parity export (the hour
  the daily bar starts, the weekday the weekly bar starts). Decision for Max after both: BTC stays at half stake and
  the 3R cap (the replay says a small plus either way) or goes off at the next restart if the window median spread is
  above about $20 or the terminal's bars are New-York-anchored and the queued OOS rerun is negative. Nothing changes
  during the challenge on today's evidence.

### 5. True execution costs (none now; config after the challenge)

- Per market the flat 0.10R is wrong in both directions and about right together (additive model from the raw ledgers,
  `verify_costs/recost.py`): EURUSD cost_R p50 0.051, 0 % of trades above 0.10R, +47.1R true against +39.5R flat
  (broker walk +46.5R); gold 0.062, 28 %, +78.6R (walk +79.7R); NAS100 0.068, 37 %, +35.7R (walk +37.1R); BTC 0.154,
  80 %, +56.5R (walk +58.1R at $15). In account money at 1.5 %: the median trade pays $7.7 / $9.3 / $10.3 / $23.1.
- The replay (`challenge_sim_costs.py`, re-run instrumented): flat 100 % both phases / 84 days / funded +5.7 % / 2026 six
  weeks 71 %; base 100 % / 80 / +6.0 % / 78 %; pessimistic (EURUSD 0.2 pip + $5, gold 3.7 pips + 0.0014 %, NAS100 5
  points, BTC $45) 94 % / 76 / +5.5 % / 71 %; pessimistic + the live cap 89 % / 69 / +5.3 % / 60 %; base + 0.05R fill
  slippage 95 % / +5.7 %. Followed: the skeptic's reading of "unfinished": every unfinished start ends at a balance of
  9,036-9,062 with 236-250 later trades blocked by the 9.5 % floor, which the README's replays count as lost, so
  pessimistic 6 % lost, pessimistic + cap 11 %, base + slippage 5 %, mid 3 % (starts up to July 2025); the 2026-start
  figures (33-40 days to both phases) hold in every scenario.
- Out of sample the additive model is 2-5x too dear (gold -82.6R against the walk's -38.6R; NAS100 at 5 points -6.5R
  against +15.1R): dropped (section 5). Stop-gap slippage needs no model: 0 of 158 stop exits in 2024-2026 gapped on
  the 5m or 1m candles, 4 booked gaps of 488 in 2017-2023 (one a 65-minute data hole). No cost-based stop floor: the
  80 % floors would be 71 pips gold, 30 points NAS100, $856 BTC and would remove trades worth +16.1 / +18.3 / +48.3R
  true; the 30 % cap is the one floor that matters and refuses nothing at the base spreads in sample.
- Action: none now. After the challenge, config: the measured spreads as `typical_spread_pips` in the research profiles
  and `backtest --costs ftmo` (`cli.py:920`; BACKLOG A5, pipeline candidate 4), keeping the 0.10R haircut on top until
  the forward journal measures fill slippage (BACKLOG A6, pipeline candidate 7); the angle's 0.05R haircut is dropped
  for want of a measurement. A BTC rerun at a measured spread is read as a new ledger, not a shifted one.

### 6. The daily-loss guard against FTMO's equity rule (decision for Max: a manual rule)

- The guard's worst case (`balance - open_risk - new_risk` against -4 % on the day and -9.5 % in total,
  `risk_guard.py:186-194`) is FTMO's number up to commissions and swaps (under 0.1 % of the account), slippage beyond
  the stop, and positions the windows did not open: `open_positions` keeps only `p.magic == self.magic` (`mt5.py:597`),
  so a hand-opened position carries no risk and takes no slot in the guard; the day report counts it.
- Numbers (live stakes, no ladder): 239 FTMO days with a closed trade, 7 at -3.3 % (single 4H losses), one at -6.6 %
  (21 August 2025, two EURUSD 4H longs; the guard refuses the second, worst case 6 %); with the guard off 7.1 % of the
  2024-25 starts break an FTMO limit (69 % of 2017-23), with it on 0 %; the 4.0 % day at 0.25R costs fails 0 %, 4.9 %
  fails 5.6 % (2024-25) / 10.8 % (2017-23) phase-1-only. The buffers are $100 (4 -> 5 %) and $50 (9.5 -> 10 %, where
  the ladder already has the stake at 0.5 %); a 3 % position needs slippage of a third of its stop to eat the $100.
  Positions held over a Prague midnight: 61 of 315 (19 %), 12 double stake, +94.7R raw: the overnight carry is where
  the edge sits, not a thing to cut.
- Action: manual rule, free: no hand-opened position while a window runs (for item 2's day-count trades the windows
  are closed first). The 4.0 % / 9.5 % stay (prop_firm.md 3.1, candidate 5).

### 7. A restart runs the branch head untested (code; a manual diff rule)

- `scripts/start_ftmo.bat` runs `git pull --ff-only || (echo UPDATE FAILED & pause)` and starts the windows: no test
  run, no `pip install` (`requirements-trader.txt` unchanged since 1 October), 44 commits since 7 October, a failed pull
  pauses before any window starts. The pre-mortem's notice bug (a notice raising before `handle_signal` ended the
  scan while the loop lived on) was real at fecf55e and is fixed on HEAD by adc3f64 (each of the six notices in
  `step()` in its own try/except, `live.py:446-458`, with `test_a_failing_notice_never_blocks_the_setup`). No PIN or
  checkout logic exists in either start script. The "10-20 % per restart" likelihood is a judgment and is not quoted
  as a number.
- Cost of a fail-closed day: 2.3 trades a week at +0.66R a trade after costs; a wrong trade is the rarer case.
- Action: code (a `PIN=<commit>` line in `ftmo_local.bat` and one `git checkout %PIN%` guarded by `if defined PIN` in
  `start_ftmo.bat`, off when unset); manual rule until then: before a restart the cloud session names the commit and
  lists the diff of `live.py`, `mt5.py`, `risk_guard.py` and the four profiles since the commit the windows run.

### 8. The seeded news calendar (data fix; decision for Max for tomorrow)

- Tomorrow: line 2860 of `data/calendar/high_impact.csv` is `2026-10-15 13:30,USD,1,Retail Sales MoM`; TradingView
  (the angle's payload and a fresh pull) and the BLS clock put it at 12:30 UTC with PPI. `Calendar.add`
  (`calendar.py:123-130`) appends events whose (time, currency, title) is new and never removes one, the fallback file
  is loaded at start (`cli.py:98`), so ForexFactory's 12:30 row and the fallback's 13:30 row both stay: all four markets
  blacked out 14:00-15:00 and 15:00-16:00 Amsterdam. Followed: the skeptic over the angle's "only the hourly refresh
  makes that harmless". The fix is one character pair (13:30 -> 12:30) plus a restart before 15:00 Amsterdam (the
  scripts pull at start); the alternative is to accept one lost hour on one afternoon.
- The rest of the window: on HEAD (5e26184) the file runs to 13 November with the ISM rows at 15:00 UTC (right; the
  TradingView times of 14:00 UTC for ISM on 2 and 4 November and 13:30 UTC for the ECI on 30 October contradict the
  official clock across the DST switch and must not be copied), NFP 6 Nov 13:30, CPI 10 Nov 13:30; nothing after 13
  November (retail sales about 17 Nov, FOMC minutes 18 Nov 19:00 UTC, flash PMIs 23 Nov, the 25 Nov GDP/PCE batch) and no
  EUR row after 4 November. The watchdog's "calendar ended" message fires only Monday-Thursday (`watchdog.py:69`,
  `weekday() <= 3`) and only once the last seeded event is past, so a ForexFactory failure (a 429 is documented at
  `live.py:1198-1230`) before 14 November is silent. Blackout slots inside the windows from 15 October to 7 November:
  18 (20 with today's), 6 of them USD slots covering a full window hour (the angle's 21 / 3 match nothing).
- Action: data (the one-line fix now; the 14 November - December USD and EUR rows), and the manual rule on release days
  stays: the 08:45 line must name the day's 14:30 event; the "-1R to -2R" cost of an entry inside a window is a
  judgment (the ledgers hold no such entry).

### 9. NAS100's unmeasured morning spread (laptop check; config after)

- Stops at the fill p10/25/50/75 14.5 / 21 / 27.5 / 44 points; median cost 0.055 / 0.109 / 0.182R at 1.5 / 3 / 5
  points, refused by the 30 % cap 0 / 0 / 21 % (out of sample 56 % at 5 points, stops p50 15.7); the broker walk in
  sample +37.1 / +34.7 / +28.1R and out of sample +38.8 / +26.5 / +15.1R, so the angle's "loses its edge at 5 points"
  does not hold out of sample (followed: the skeptic) and the conditional `min_stop_pips: 17` (9 refused trades, an
  11-trade quartile) is dropped. The cap is checked once at the market price, never at a limit's fill, and `_place_limit`
  sizes on a 25 % shorter stop, so the effective cap at the limit is 0.3 / 0.75 = 40 %. The morning window: 13
  in-sample trades +9.6R (+0.74R a trade, median stop 21.6 points), 29 out-of-sample trades -0.12R a trade.
- Action: the same `mt5-spreads` measurement as item 4, split by window; then the measured medians as
  `typical_spread_pips` in `config/dorus_live_nas100.yaml` and `config/dorus_live_btc.yaml` (config after the challenge,
  or at a restart with Max's OK) so the backtester's cap (6b2d7b7) refuses what live refuses; the morning window off for
  NAS100 only after a replay, never from the 13 trades.

### 10. A sleeping laptop, Patch Tuesday 10 November, a reboot (laptop check)

- 317 trades in 138 weeks = 2.3 a week at +0.66R a trade after costs (out of sample 1.9 a week at -0.11R); the stop and
  target sit in the deal request (`mt5.py:637-649`), a limit expires server-side 10 minutes after its own expiry
  (`mt5.py:736`), break-even moves and NAS100's 48 h close are missed while down (`live.py:1894-1923`), the day start is
  rebuilt from the deal history (`risk_guard.py:65-77`); no logon task exists in any script or doc. No path to a breach
  beyond the worst case; the cost is missed entries and missed break-even moves.
- Action: laptop check before 10 November (sleep on mains off, lid closed = nothing, active hours 08:00-23:00, no
  pending restart); a Task Scheduler task at logon running `scripts\start_ftmo.bat` is Max's choice (the script starts
  only the missing windows). The "Once: the laptop itself" prompt is gone from HEAD with the emptied LAPTOP_TASKS.md.

### 11. Telegram is the healthchecks check's only integration (config now)

- `TelegramNotifier.send` and `send_photo` never raise (a failure is a console line at most once a minute,
  `telegram.py:95-100, 120-166`); the watchdog's alerts go through the same `send` (`watchdog.py:88-105`); the Pinger is
  independent (`watchdog.py:124-144`, attached in `cli.py:626-630`) but `docs/LIVE_SETUP.md` ("When the whole computer
  stops", step 2) sets Telegram as the check's only integration, so a Telegram outage hides the alarm with the alarm.
  `telegram=dry-run` at a window's start means a missing token or chat id; a rotated token prints `telegram=on` and
  then `[telegram] message not sent`.
- Action: config, free: an e-mail integration on the healthchecks.io check; manual rule: no 08:45 messages by 09:00
  means a look at the windows before the window opens.

### 12. The DST-mismatch week, 26 October - 1 November (laptop check)

- Amsterdam goes to UTC+1 on 25 October, New York to UTC-5 on 1 November: for one week US 08:30 releases fall at 13:30
  Amsterdam (blackout 13:00-14:00, the afternoon window's first hour: durable goods 27 Oct, GDP/PCE 29 Oct), FOMC 28
  Oct at 19:00 / 19:30, ECB 29 Oct at 14:15 / 14:45 (EURUSD out 13:00-15:15), the server day rolls at 22:00 Amsterdam
  (the restart messages at 22:01 / 22:02).
- Code and data confirmed: `offset_from_week_close` sets `_ny7` and returns `ny_utcoffset(now) + 7 h` (`mt5.py:355-389`),
  re-read hourly (`:322`), the env pin short-circuits it (`:318`), tests `test_offset_follows_us_daylight_saving` and
  `test_bar_times_keep_their_hour_across_a_dst_switch` exist; the research 4H bars open at 21:00 UTC in the 27-31
  October 2025 mismatch week and 22:00 from 3 November, so the backtest traded those weeks as the bot will; mismatch-week
  trades 25, +0.74R a trade against +0.76R elsewhere (out of sample 31, +0.29R against -0.02R): no rule. Nothing in the
  repository sets `MT5_SERVER_OFFSET_HOURS` (`ftmo_local.bat` is git-ignored and must not either). Assumed, not
  verifiable here: FTMO's server follows the US switch.
- Action: Monday 26 October 09:00-09:15 Amsterdam, read-only: `mt5-test --symbol EURUSD --tf 5m` must print `+3.0 h`
  (`+2.0 h` on 2 November) and the last bar's UTC time on the current five-minute boundary; the four heartbeats with
  `stale` empty and `last_candle` within ten minutes; the 22:00-22:03 console lines on 26 October (`connected again
  after 1 min` = server midnight at 22:00 Amsterdam); the Account MetriX reset countdown pointing at midnight Prague;
  `w32tm /query /status`. If `+2.0 h` prints during the week, pin `MT5_SERVER_OFFSET_HOURS=2` and restart outside the
  sessions. These five checks exist only in `premortem.md` until LAPTOP_TASKS.md is restored.

### 13. Trade management: nothing left on the table (none)

- From the 5m paths of all 1,020 trades (the excursion walk reproduces every ledger trade to 0.02R): a stop 1.1 / 1.2
  / 1.3x costs the four markets -23.4 / -47.2 / -52.3R in sample on +238R raw, negative in every in-sample year on all
  four, and 85-96 % of the stopped trades are stopped at 1.5x as well (gold 2017-2023 gains +6.0 / +11.1R, mostly in
  2020: not a live rule); a stop 0.9x -62.1R (winners' MAE median 0.37-0.41R, 15-26 % beyond 0.8R); a target 5 % nearer
  -6.1R in sample and +6.2R out (4 of 8 cells; B6's +11.2R gold OOS came from a re-walk whose base did not match the
  ledger); break-even +1R -82.3 / -70.0R, +2R -20.8 / -8.0R, +3R -4.5 / -3.4R, the rules as they run +3.0R in sample
  (three trades) and +12.7R out of sample against none, gold's 2R +2.0 / +5.7R, and `be2_NAS100` -4.5R in the engine
  (B7 refuted); max hold 24 h -21.2 / -30.6R, an 8 h time stop -16.9 / -12.7R; NAS100's 48 h: nothing argues against
  it (24 h changes one in-sample trade, +4.06R cut to +1.68R).
- The anatomy: 24-52 % of the losers never see +0.25R (an upper bound on EURUSD and NAS100, where the limit fill sits
  inside its candle: 9-22 % with that candle counted), their best moment is 0-0.5 h after the fill. If the win rate is to
  rise it is the entry selection, not the management.
- Action: none; B6 and B7 close; the "near miss" the excursion angle defined (MFE of 80 % of the target or +1R before
  the stop: 21-29 % of the stopped trades, 7.9-19.9R shown and lost) is a post-trade note for the closed-trade message,
  not task 82's refusal-based near-miss message, and proposes nothing.

### 14. The knob batches and the adoption rule (none during the challenge)

- oct14b (33 knob variants, in sample): the largest gain over the live profile is +0.8R (BTC `ny`, paired t 0.12); the
  paired SE of a knob change is 5.5-7.7R; only `be1` (EURUSD -27.3R, gold -28.1R) and BTC `scalp15` (-18.2R) are more than
  two paired SEs from zero, all negative. RESULTS_14oct's "nothing adoptable" stands under any version of the rule.
- oct14d (both periods): gold `ban` +11.6R IS / +18.7R OOS, `stack` +10.7 / +33.2R, `dep25` +3.1 / +11.0R, EURUSD `usob`
  +5.7 / +3.0R and `both` +4.0 / +7.8R pass the CSCV screen (P(OOS loss) 0, 4-5 of 5 windows above the grid median);
  their gains are under two paired SEs (about +8 to +15R) and the house rule needs 2017-2023 plus 20 forward trades:
  adoptable after the challenge at the earliest, and not during it (the profiles are frozen).
- The adoption rule (walkforward.md section 5, `candidate_check.py`): steps 1-3, 5 and 6 are sound (the grid gate PBO
  <= 0.5: gold 0.22 and BTC 0.45 pass, EURUSD 0.58 and NAS100 0.73 fail; the CSCV screen; 4 of 5 windows positive and
  above the median; 2017-2023 not below the live profile; 20 forward trades). Step 4's floor (one SE of the live total:
  raw gains of +32 / +29 / +37 / +58R) is replaced by "gain >= 2 paired SEs" because it would have rejected both changes
  the README adopted and then confirmed out of sample (EURUSD two positions +5.5R IS / +6.9R OOS; NAS100 R:R 0.8 +1.0R /
  +8.8R); the conditional switch (be2 NAS100 passing with P(above the OOS median | top decile) = 0.02) and the
  float-tie ranking (`g.values > cs`; round to 1e-6) are to fix before the script moves next to `scripts/`, where it
  must rebuild its matrices from the repository's ledgers.
- Process rule that replaces the dropped per-window batch: a knob batch is proposed and frozen on data up to a cut
  date and scored on the months after it; the forward journal is the only clean holdout.

## 2. How much to trust the 2024-2026 edge, five sentences a market

**EURUSD.** (1) The 218-variant grid cannot rank EURUSD variants: PBO 0.58, P(IS-best loses OOS) 0.21, the IS-best
keeps 28 % of its in-sample sum and lands below its own grid's OOS median (+8.7 against +10.1R), Spearman 0.34, anchored
walk-forward WFE 0.14 with 1 of 4 steps positive and every pick in the bottom third (ranks 138-202 of 218), so nothing
is adopted on 2024-2026 evidence alone (the README's practice since 6 October, now with a number). (2) The live profile
ranks 7 of 220 and sits above the OOS median in 100 % of the splits, but it was chosen on the whole window (provenance
12 October), so its only true out-of-sample number is 2017-2023: 97 trades, -0.013R a trade, ratio -0.02 at the flat
cost and +14.5R (additive) to +20.6R (broker walk) at FTMO's measured 0.1 pip + $3, because the flat 0.10R over-charges
EURUSD by 0.07R a trade (cost_R p50 0.051, 0 % of trades above 0.10R). (3) In sample the entry logic beats both nulls
(direction p 0.0285, after-signal timing p 0.000, both-random +0.040R a trade against the real +0.84), but measured at
the signal close instead of the limit fill the passes become p 0.13 and p 0.06, and on the 45-trade market-order ledger
direction z +1.12 and timing +1.55: EURUSD passes the A8 gate through the limit (the skeptic's reading, followed because
the angle's timing null gave random market fills the limit's tighter geometry). (4) Out of sample the limit is the
stable term (+0.29R a trade on the filled trades; the same trades as market orders -30.6R against the ledger's -2.2R),
the direction call has none (z -0.69 at the signal close, sign share 60 %, p 0.11) and the candle a modest one (z +1.48,
p 0.07 on the 74-trade market ledger). (5) Trust the EURUSD edge as entry mechanics the profile already runs (limit
25 % back, two positions), expect its +0.84R a trade to shrink toward the 2017-2023 +0.15R at true cost when the regime
turns, and read the 4H x2 (10 trades +4.3R in sample; 10 trades +31.2R out, of which one 13.1R and two 5.2R trades)
as thin on both sides.

**XAUUSD.** (1) Gold passes the CSCV gate by sum R (129 variants: PBO 0.22, P(loss) 0.01, keeps 60 %, Spearman 0.66)
and the anchored walk-forward (g25 every step: +18.5 / +2.9 / +17.0 / +9.7R, ranks 21-72 of 129, WFE 0.84, +11.9R over
the grid median), but by mean R a trade PBO is 0.58 and in the 23-variant neighbourhood of the live profile 0.74: the
ranking is stable because the many-trade variants (g25 122 trades, gz 169) ride the same regime, not because the knob
grid is decidable. (2) The live profile's frozen record (+20.4 / +1.5 / +24.9 / +11.3R per step, ranks 5 / 85 / 7 / 6)
is hindsight; the true out-of-sample number is 2017-2023: 371 trades, -0.168R a trade, ratio -0.33 at the flat cost,
and about -39R rather than -83R once the spread is charged the way the broker charges it (losers pay -1R whatever the
spread; the skeptic's walk, followed; the angle's "20-26R deeper" dropped), so the stop size separates the periods (85
pips in sample at the median against 32 pips), not the spread. (3) In sample gold's direction call is the strongest of
the four (z +3.58, exact p 0.0000, sign share 64 %) and its timing z +3.67; out of sample both are gone (direction z
+0.42, sign share 50 %; timing +1.58, p 0.06): the edge is the direction in the afternoon window (13-17 direction z
+4.04 in sample) inside the 2024-2026 gold trend, and 2026 alone is +36.3 of +71.8R. (4) The costs are benign: the
measured 3.4-3.7 pips cost +0.033-0.040R a trade over the flat figure (walk: 5.8-6.5R over 143 trades), the cap refuses
0 trades in sample (smallest stop 17.05 pips against an 11.3-12.3 floor) and 8 % out of sample, and gold's dearest hour
(09:00 Amsterdam, 0.078R p50, 62-pip stops) is its most profitable (+18.8R true). (5) A gold winner keeps about three
quarters of its in-sample gain while the regime lasts (top-decile OOS/IS 0.75, 80 % above the OOS median) and whether
it lasts is not a backtest question; the live rules are each confirmed in both periods (2R break-even +2.0R in sample /
+5.7R out, the fixed-2R fallback 66 in-sample trades +37.8R, the R:R floor 0.8), and the 4H x2 (13 trades) is the one
gold setting with in-sample support only.

**NAS100.** (1) CSCV fails hardest: 115 variants, PBO 0.73, P(IS-best loses OOS) 0.43, keeps 7 %, Spearman 0.19; the
anchored walk-forward's WFE 1.09 is 2 of 4 steps with 6- and 9-trade picks, its good step (2026-H1, +22.3R) came when
98 % of the grid was positive, and the rolling WFE is 0.39 with the 2026-Q3 pick the worst variant of the grid. (2)
NAS100 has the best true out-of-sample ratio of the four (100 trades 2017-2023, +0.288R a trade, +0.38), which is the
evidence to use on it, and it survives the pessimistic 5-point spread in the broker walk (+15.1R out of sample,
+28.1R in sample; the angle's "turns negative" was the additive model's artefact). (3) In sample the direction holds
either way (p 0.0013 at the limit fill, p 0.006 on the 46-trade market ledger, sign share 74 %) and the candle's timing
is nil (z +0.17 to +0.22), so the in-sample result is the direction call plus the limit (the same trades as market
orders +12.9R against +32.9R). (4) Out of sample the direction is unsupported (z +0.45 on the market ledger, sign share
54 %), the limit is the stable term (+0.35R a trade; market orders -6.5R against +28.8R; the profile's own test: limit
+33.6R against market +23.6R for 2017-2023) and the candle keeps a modest edge (z +1.98, p 0.02 on 114 trades). (5) The
43-trade ledger is too short for a 115-variant grid (an in-sample NAS100 winner is a coin flip with a 2-in-5 chance of
losing out of sample) and its in-sample R lives in three trades (+15.4 of +32.9R without the top three), so the profile
stays as it is, the morning spread gets measured (13 morning trades +9.6R in sample, 29 trades -0.12R a trade out) and
the 48 h close stands (24 h changes one in-sample trade).

**BTCUSD.** (1) CSCV is borderline: 161 variants, PBO 0.45 at S = 16, 0.53 at S = 12, 0.36 at S = 8, neighbourhood
0.76; the anchored walk-forward's 0.79 and 4 of 4 are carried by 2026-H1 (+38.0 of +49.8R, a half-year in which 99 % of
the grid was positive and the median variant made +37.0R), the rolling WFE is 0.36, and in 2026-Q3 the grid median was
-1.5R with 6 % positive. (2) The true out-of-sample record is the worst of the four: 130 trades 2020-06..2023, -0.320R
a trade, ratio -0.42, the direction call inverted (the mirror trade better in 58 of 101 decided trades, z -1.63: a
lean, not a finding) and the timing z -0.91. (3) In sample the result is the direction in the morning window
(direction-only +0.41 of +0.69R a trade; 09-11: 42 trades +53.4R of +61.7R, direction z +2.11; 09:00 Amsterdam 27
trades +47.2R true), and 2026 is +39.6 of +61.7R. (4) The costs are structural: the 0.065 % commission is 0.106R at the
median stop (70 % of BTC's cost), 80 % of trades pay more than 0.10R at $15, 33 of 89 fall under R:R 0.8 after the full
cost, and the two largest shorts (P79 +11.8R, P82 +23.9R) are stopped at entry at any spread above $15.4 / $21.8, so BTC
is +58.1R at $15 and +17.0R at $30 in the broker walk, while the margin cap already cuts 74 % of its trades to 59 % of
the planned risk. (5) Trust it least: the half stake and the 3R cap are the right hedges, the terminal's candle
anchoring (New York rerun 94 trades +33.3R against 89 trades +70.6R) and the window spread are the two measurements that
decide whether BTC stays, and the challenge does not depend on it (99 % both phases without it, at the cost of speed:
six weeks 50 % against 78 % in the costs replay).

## 3. The pre-mortem's top five risks and their mitigations (as verified)

| Rank | Risk | Mechanism and the verified number | Mitigation |
|---|---|---|---|
| 1 | The target comes early and the windows trade on at full stake | nothing in the live path reads the target (`stepped_risk` halves only within `target_protect_pct`, off; the watchdog alone knows it); +10 % before the 4th trading day in 31 % of the 2026 starts, median days to +10 % 20, trading days in 47 days median 6 (p10 4); after a qualifying pass trading on undoes it within 3 days in 7-12 %; back under +10 % before the pass 10 % (2026) / 33 % (2024-25, 46 overlapping starts) | manual rule at `target +10 %: reached` (item 2; windows closed, positions finish on their server stops, 0.01-lot day-count trades only with the windows closed, then the Verification); code off by default after: `prop_firm.stop_at_target`, `finish_risk_pct 0.10` (+3.2 points on both phases within 42 days, phase 1 unchanged); restore `docs/LAPTOP_TASKS.md` (0 bytes on HEAD) |
| 2 | A weekend or overnight gap through a double-stake 4H position | the stop is server-side and a gap fills at the open; no weekend or day close in the challenge; 0.28 weekend-held x2 positions expected, gaps over 1.67 median 4H stops on 31.2 % of NAS100 weekends (nights 8.8 %), 12.7 % EURUSD, 7.7 % gold; about 1.7 % over the window of a -5 % print (order of magnitude: 6 holds, a 5-trade NAS100 stop yardstick) | the Friday rule stated in New York time (about 15:30-15:45; 21:30 Amsterdam is after NAS100's Friday close on 30 October): NAS100 positions with 2 % or more at risk and not at break-even closed by hand, gold and EURUSD Max's choice (a wash: three in-sample cases, -6.7R if closed); config at the next restart: NAS100 4H at the single stake (replay neutral) or x1.5 on all three (at 0.25R costs 91 % against 85 % both phases); code off by default: `prop_firm.weekend_close_min_risk_pct 2.0`; the same rule on 27 November at the early close and on the night of 3 November |
| 3 | A restart pulls the branch head untested; a notification bug stops entries | `git pull --ff-only` then the windows, no tests, no pip install, 44 commits since 7 October; the notice-before-`handle_signal` path was real at fecf55e and is fixed on HEAD (adc3f64, with a test); no PIN logic; the "10-20 % per restart" is a judgment, not a number | code: `PIN=<commit>` in `ftmo_local.bat` and a guarded `git checkout` in `start_ftmo.bat`; manual rule until then: name the commit and list the diff of `live.py`, `mt5.py`, `risk_guard.py` and the profiles before a restart; the restart check (four start records on one commit, risk 1.5, fresh heartbeats, four start messages) |
| 4 | The daily-loss guard's worst case against FTMO's equity rule | the worst case is FTMO's number up to commissions (under 0.1 %), slippage beyond the stop, and hand-opened positions (`mt5.py:597` keeps only the bot's magic number); 239 days: 7 at -3.3 %, one at -6.6 % (the guard refuses the second trade); guard off 7.1 % fail, on 0 %; the buffer to 5 % is $100, a 3 % position needs a third of its stop in slippage to eat it | manual rule: no hand-opened position while a window runs; the day-report line "if every stop is hit the equity ... is under a floor" must never appear with the windows' positions alone; 4.0 % and 9.5 % stay (4.9 % fails 5.6-10.8 % of phase-1 starts at 0.25R costs) |
| 5 | The DST-mismatch week 26 October - 1 November | the server stays UTC+3 while Amsterdam goes to UTC+1; `_ny7` converts with New York's offset + 7 h, re-read hourly, tested; the research candles were built the same way (4H bars at 21:00 UTC in the 2025 mismatch week); mismatch-week trades +0.74R a trade (25) against +0.76R elsewhere; a wrong offset stales the 5m feed within 20 minutes (fail-closed, said by `check_feed`) | five read-only checks on Monday 26 October 09:00-09:15 (item 12): the printed offset +3.0 h, fresh heartbeats, the 22:00-22:03 reconnect line, the MetriX reset countdown, `w32tm`; pin `MT5_SERVER_OFFSET_HOURS=2` only if +2.0 h prints; `ftmo_local.bat` must not pin the offset; read the 08:45 blackout minutes against 13:30 Amsterdam for the US 08:30 releases that week |

Ranks 6-13 (Telegram silence, laptop sleep, the spread cap, the margin cap, the nightly break and Thanksgiving, the
parity check's assumptions, the calendar after 13 November, phase 2 on a new login) are in items 8-11 of section 1 and
in `premortem.md` sections 7-14; the margin cap (BTC lots cut in 74 % of trades, NAS100 19 %, 2 of the 5 4H trades;
EURUSD and gold never reach 45 %) and the nightly break need nothing.

## 4. The markets now (14 October 2026, 17:00 UTC, on the spliced TradingView candles; the splice reproduces the research 4H/1D/1W/1MO files on every overlapping bar, max difference 0)

**EURUSD (1.11236).** The CPI print (3.7 % y/y against 3.6 forecast, core 2.6, +0.6 % m/m) took the session from
1.11982 to 1.11236 (-0.67 %) with a low at 1.11128, the lowest 1H low since 13 May 2025 (17 months). The engine reads
bearish in full mode matched as the 1D+1H pair (four of five bearish, the month 50/50), the weekly and 4H veto allow
shorts, and the stake is 1.5 x 0.5 (month 50/50) x 0.5 (1D+1H pair) = 0.375 % on a 1H zone ($37.5) and 0.75 % on a 4H
zone, the smallest trade in the book before the ladder. Three supplies can still be traded, not two, and each deadline
is one bar later than the angle's because the 24 h count from the candle's close and from the current visit's touch
(`engine.py:208-213`): the 1H supply 1.11374-1.11985 (13.8 pips above price, first touch until 16:00 Amsterdam on 15
October), the 4H supply 1.11516-1.12113 (28 pips, until 15:00) and the once-tested 1H supply 1.11931-1.12066 (70-83
pips, a second visit until 13:00; `allow_retest` is true). The weekly demand 1.07782-1.09369 is 2.65 daily ATRs away and
the diagnostic walk finds no tradable demand. The regime is one the edge was never measured in: 20-day efficiency 0.57
on the forming and the closed daily bar (in-sample median 0.21, 97th percentile, highest at any in-sample entry 0.43;
the out-of-sample 0.5-1.0 bucket 14 trades, 35.7 %, +0.34R a trade), ATR14 0.59 % of price on the closed bar (inside the
0.574-0.724 % band that earned +1.31R a trade on 14 trades), 20-day return -3.0 %. Caution is the right strength and no
rule follows (README 846 files regime filters under not taken); the quarter stake is already the right size for a
17-month low with the USD bid into the 28 October FOMC. Blackouts: 15 October 14:00-16:00 (item 8); 20 October ZEW
10:30-11:30; 23 October flash PMIs 09:00-10:30; ECB day 29 October 13:00-15:15.

**XAUUSD (4083.62).** From 4161.08 to 4083.62 (-1.86 %, low 4073.55, the third down day). Four of five timeframes
bearish (the daily 50/50 after sweeping sell-side at 4110.5; 4H BOS 4150.46 and 4105.18, 1H BMS 4144.13); the month
bearish, so no halving: 1.5 % on a 1H zone ($150) and 3.0 % on a 4H zone ($300), the largest stake in the book. The
zone is the 1H and 4H supply 4105.18-4155.51, $21.9 above price: the 1H version already has an open visit (the 15m bar
of 14:30 UTC touched 4105.80), so its clock is the visit age, tradable until 16:30 Amsterdam on 15 October; the 4H
version is fresh and may be first touched until 19:00 Amsterdam. On the laptop the window will look for a 5m shift
there (the cloud run stopped at "no 5m data"). Followed, the skeptic against the angle: a short taken inside the zone is
not a "chase" trade by gold's own study (the trailing-24 h net move at an entry at or above 4105.2 is -2.0 to -2.5
hourly ATRs, -3.2 to -3.7 even with price flat at 4083; the chase bucket needs more than 4), and the day's span of 5.5
ATR is under the 8-ATR expanded-day cut. The closed-bar regime: er20 0.16 (the 0-0.2 bucket: in sample 52 trades, 48 %,
+0.37R; out of sample 152 trades, 25 %, -0.34R; the angle quoted the forming bar's 0.21), ATR14 1.82 % (60th in-sample
percentile, 8th of the last year); gold lost 72.2R out of sample under er20 0.35 and made +10.0R above it, which is the
reason to take tomorrow's trade at its size with eyes open and not to add to it. Guard arithmetic for a second trade:
after a -3 % loss the ladder gives a 1.0 % base and a second gold 1H trade makes the worst day 4.0 % >= 4 % (refused); a
0.375 % EURUSD trade passes at 3.375 %. A 4H-zone gold short at 3 % is exactly the position item 3 is about (gold held 4
of its 13 4H trades over a weekend).

**NAS100 (30075.7).** From 30560.3 to 30075.7 (-1.59 %, low 29975). Neutral, no trade: the month 50/50, the weekly
and daily bullish (BMS 30244.5, BOS 30759.9; daily BOS 30642 and 30797), the 4H and 1H bearish (BOS 30370.7, 30260.8,
30093.2); the weekly veto (`no_trade_against: [1W]`) blocks shorts regardless, and the fresh supplies at 30126-30274
(1H) and 30370.7-30632.7 (4H), 47 and 292 points above, cannot be traded. The demand below (4H 29616-29776, 1D
28942-29731, stamped 20-21 September) is 23-24 days old, so no first touch can come within 24 h of forming; the
weekly/4H demand 29616-30244 price sits in is spent (touched 233 h / 549 h after forming). A long needs the 1H balance
view to flip on a close beyond the last gap (30125.99-30200.79) plus a bullish break, then a fresh demand zone and a
1M/1W/1D combination; a short needs the daily and the weekly to turn. The two regime sentences of the angle are dropped:
on the last closed daily bar NAS100 sits at er20 0.39 (the 0.35-0.5 bucket: in sample +0.29R on 10 trades, out of sample
+0.35R on 20) and ATR14 1.36 % (the band under 1.379 %: in sample -0.23R on 11, out of sample +0.13R on 36), both flip
with the bar chosen and rest on 9-36 trades a cell. Expect few signals; earnings season and the night of 3 November are
gap risks for a 48 h position; in the mismatch week NAS100's Friday close is 21:10 Amsterdam.

**BTCUSD (81925.1).** From the server-day open 83342.8 to 81925.1 (-1.70 %; -1.4 % from the UTC-day open). The reading
depends on the candle anchoring, which is the open research question (task 80): on New-York-anchored 4H bars
(05:00 / 09:00 / 13:00 UTC) the 05:00 bar's low 83251.78 and the 13:00 bar's high 83012.38 leave a bearish gap
83012.38-83251.78 with price below it, the 4H balance view is bearish and the window reads bearish scalp (1D+4H+1H),
stake 1.5 x 0.5 = 0.75 % ($75), with a fresh 4H supply 82880-83844 and 1H supply 83012-83844 $955 above price; on
UTC-anchored bars (04:00 / 08:00 / 12:00) the 12:00 bar's high 83844 runs through that range, the last bearish P is
broken, the 4H reads 50/50 and the decision is no trade. The 1H demand 81337-83032 price sits in has a 29-hour-old visit
(stale), the 4H 80395-81914 and 1D 80578-85094 demands are spent. The month and week read bullish, the daily bearish.
The regime is benign (ATR14 2.47 % on the closed bar, the 14th in-sample percentile, the calm band that was positive in
both periods; er20 0.08), but the BTC edge is the one with nothing out of sample (section 2), 2026 is +39.6 of its
+61.7R, the morning spread is unmeasured and the margin cap will cut the lots in about three trades of four. The laptop
read of the terminal's D1 and W1 bar stamps decides which of the two readings tonight's window is trading; the stake
stays at half either way.

## 5. What was dropped in verification and why (one line each)

Disagreements resolved in the skeptic's favour throughout, because every skeptic number came from an independent
re-derivation that reproduced the angle's arithmetic first and then showed where its convention or label failed.

- walkforward F8 (hindsight contamination needs fresh backtests per window; a 2-day gold/BTC batch): dropped; the engine
  is append-only invariant (44 of 44 EURUSD trades identical to 25 June, 85 of 85 BTC from a February start), so a
  per-window backtest equals the full ledger clipped and the batch reproduces the matrices; the run count was 4x
  overstated (33 x 4 = 132, not 528); replaced by the prospective freeze rule.
- walkforward F5, the "beats live IS by >= 5R -> beats live OOS 2-7 %" sentence: dropped as evidence; dOOS = dTotal - dIS,
  and only 2 / 3 / 3 / 4 variants a market beat the live profile by 5R on the full window, so it restates that the
  live profile is near the top.
- walkforward F5/F6, "one SE of the live total" as the floor (15.7 / 22.1 / 15.0 / 28.7R): dropped; the paired SE of a
  knob change is 5.5-7.7R (0.19-0.49 of it) and the floor would have rejected the two README-adopted, OOS-confirmed
  changes; "gain >= 2 paired SEs" instead; h is a variant's own OOS/IS, not the shrinkage of a gain.
- walkforward F6, candidate_check.py's conditional switch (be2 NAS100 passes with P = 0.02) and the float-tie rank
  (be2 shown #23 where the identical live total ranks #10): to fix before the script moves.
- walkforward F7, "gold's whole grid loses on 2017-2023": kept only for the handful of gold variants with 2017-2023 runs
  (README lines 1102-1104, 1152, 1341), not the 129-variant grid.
- walkforward F3, the oct14b sub-grid PBOs (0.82 / 0.27 / 0.43 / 0.81): quoted as coarse (4-11 variants, tie-dependent:
  EURUSD 0.72 / 0.83, BTC 0.64 / 0.89 under the two tie conventions); the near3 numbers (0.44 / 0.74 / 0.59 / 0.76) are
  the ones to cite.
- baselines F5 (the stable term is the direction call at the shift candle on EURUSD and NAS100): the title is wrong;
  the interaction term is +0.03 / +0.02 (EURUSD) and +0.08 / +0.12 (NAS100) on the market-order ledgers against +0.36 /
  +0.33 and +0.35 / +0.25 on the limit ledgers: the stable term is the limit fill.
- baselines F3, the OOS timing half (EURUSD z +3.9, NAS100 +3.0): mostly the limit; the candle's OOS timing is z +1.48
  (p 0.07) and +1.98 (p 0.02) on the market ledgers, the four combined +2.3 (p 0.012) instead of +4.1.
- baselines F2, EURUSD's per-market gate passes (direction p 0.03, timing p 0.000): measured at the limit fill; p 0.13 and
  p 0.06 at the signal close; NAS100's candle timing is nil (z +0.2), not borderline.
- baselines F8's title ("coins in every market"): BTC's morning direction z +2.11 (p 0.02) in sample is not a coin, and
  the morning call is half of BTC's result (+32.8 of +61.7R), not the whole.
- baselines F9's "40 % of the variance": mostly the null trades sharing the real trades' paths; net regime signal r 0.36
  (13 %).
- baselines F7's wording: "worse than gold's 1H zones" is noise (-0.14 against -0.06R before costs, t -0.3); "EURUSD's
  4H zones pass both periods" rests on 10 trades a period.
- baselines F6 (the direction meter): kept as cheap code (about 40 lines in `parity.py`) with the caveats that 30 closed
  trades is about two years on EURUSD and seven months on gold, a dead call reads <= 0 only half the time, and the timing
  score on EURUSD/NAS100 must be computed from the signal close.
- excursion F7's implication ("the sub-2R fallback band on gold"): the fixed-2R fallback trades have planned R:R exactly
  2.00 and sit in the 2-3 band (66 in-sample trades, 53 %, +37.8R; 191 OOS, 27 %, -37.4R); the bands under 2 are
  liquidity targets; the fallback-versus-none and min_rr ladder are already in the gold profile comments (+84.2R with
  against +51.3R without; 0.8 / 1.2 / 1.5 = +84.2 / +81.4 / +74.8R).
- excursion F8 (the near-miss definition for task 82): wrong feature; task 82's `notify_near_miss` announces an engine
  refusal while a zone is in play; re-scoped as a post-trade "showed +xR before the stop" note that proposes nothing.
- excursion F3's "4H winners sit deeper" (median MAE 0.7-0.8R): 18 trades on two markets (EURUSD 12 winners 0.76R,
  NAS100 6 at 0.70R); gold's 20 4H winners sit shallower (0.31R) and BTC's 24 at 0.44R; not general.
- excursion F6's "48 h confirmed": 1-4 trades either side; "nothing argues against 48 h", and the README's older run had
  24 h marginally better (+26.8R against +25.6R).
- excursion F1's "24-58 % never see +0.25R": exact on gold and BTC, an upper bound on EURUSD and NAS100 (9-22 % with the
  fill candle counted); the 1.5x result is unaffected.
- excursion F2's "under 0.02R" for the ignored cost term: 2.4R on gold at 1.2x over 143 trades; no sign changes.
- costs F9 (gold's 3.4-3.7 pips cost 0.11-0.13R a trade in 2017-2023, "20-26R deeper"): dropped; the sign is wrong because
  losers do not pay the spread in R (the walk: 9.4-11.1R, about -39R after costs, 23R shallower than the flat -62.2R);
  the in-sample half duplicates `market_XAUUSD.md` section 4.
- costs F1's OOS column and the smooth BTC sensitivity (-5R per $15): artefacts of charging losers a spread the sizing
  absorbs; the in-sample direction holds.
- costs F2's decision brackets (<= $30 nothing changes, $30-45 expect +0.5R): dropped for "above about $20 the in-sample
  BTC result is a coin flip on two trades"; the 5 cap refusals and the A7 gate are pipeline.md section 4 and a proposed,
  not adopted, criterion.
- costs F3's `min_stop_pips: 17` for NAS100 at a 5-point spread: 9 refused trades (+0.1R) and an 11-trade quartile; the
  live cap already refuses those stops; the OOS "turns negative" does not hold in the walk (+15.1R).
- costs F5 (the hour table): a null result by construction (one session median a market makes the hour effect the stop
  size); most cells under 10 trades; BTC 09:00's +47.2R holds the two knife-edge shorts; no hour decision either way.
- costs F6's D_min: a definition ((2 x spread + commission) / 0.10), not a measurement; the null action is already
  `market_XAUUSD.md` section 4 and pipeline candidate 4; the EURUSD/NAS100 small-stop buckets are 11-14 trades.
- costs F7's "0 % failed, no scenario breaks a limit": the unfinished starts are parked at the 9.5 % floor (lost by the
  README's convention); the sim omits the BTC margin cut; the mid/pessimistic account figures are upper bounds.
- costs F8's haircut to 0.05R: rests on an unmeasured fill slippage; 0.10R stays on top of the per-market costs; the
  `--costs ftmo` flag and the 7 October sets already run the commissions.
- costs F4's tallies: off-hours stop exits gold 5 (text 7), BTC 1 (text 2), EURUSD 0 (text 1); the two EURUSD "gaps" are
  limit fills and stops in the same candle (booked -1R), not slippage already in the ledger R.
- premortem F1's "56 -> 59 %, never worse": the two-phase number (54.1 -> 57.3 % in the re-derivation); phase 1 within
  42 days unchanged; the 33 % fall-back is 46 overlapping starts.
- premortem F2's Friday clock "after 21:30 Amsterdam": after NAS100's Friday close in the mismatch week; restated in New
  York time; the per-position fail chance is an order of magnitude (6 holds, a 5-trade stop yardstick).
- premortem F3's "10-20 % per restart": a judgment with no measurement; the mechanism kept, the number dropped; half
  the fix is on HEAD (adc3f64).
- premortem F12's "ends 4 November, two ISM rows an hour early": stale, fixed on HEAD by 5e26184 through 13 November;
  what remains is 14 November onward, EUR rows after 4 November and the Monday-Thursday watchdog gap; "5 % per release
  day" and "-1R to -2R" are judgments.
- premortem F9's "40 % of the 4H-zone NAS100 trades" cut by the margin cap: 2 of 5; the README (5 October) already
  settles the margin mechanics; action none.
- regime_now F3's "chase" label for tomorrow's gold short: an entry inside 4105-4155 is a -2.0 to -2.5 ATR trailing move,
  not more than 4; the er20 bucket is 0-0.2 on closed candles (same sign).
- regime_now F4's two NAS100 regime lines: both flip on the closed bar (er20 0.39, ATR 1.36 %) and rest on 9-36 trades a
  cell.
- regime_now F8's headline (21 blackout slots, three full hours): 18-20 and 6 from the same payload; and "only the hourly
  refresh makes the fallback error harmless" is wrong (`Calendar.add` never removes): the fix is the action.
- regime_now F2's deadlines (15:00 / 11:00 Amsterdam) and "two zones": one bar early (16:00 / 15:00) and a third zone
  (1.11931-1.12066) is live on a second visit; "56 h old" is not the reason the 4H 1.11838-1.12103 is out (EURUSD has no
  zone-age limit; the touch-age rule is).
- regime_now F1's "energy +5.2 % m/m" and "a hike priced": narrative, not in any data here; "one USD bet" is already
  measured milder in `risk_model.md` 4 (38 overlapping pairs, both lost 21 % against 24 % independent, R correlation
  +0.15) and capped by the worst-case guard.
- regime_now F9's "0 difference proves the splice": it proves self-consistency with the research convention, not
  fidelity to the FTMO terminal's candles (the laptop parity export is that test).

## Files

- This note: `research/DEEP_DIVE.md`. The six angles and their skeptic notes: `research/{walkforward,baselines,excursion,
  costs,premortem,regime_now}.md`, `research/verify_*.md`, scripts under `research/verify_*/`.
- Engine batch numbers: `research/RESULTS_14oct.md` (oct14b/c/d, the append-only check, the x1.5 replay). Backlogs:
  `research/BACKLOG_hand.md`, `research/BACKLOG.md`.
- Repository facts read directly for this note (HEAD 326e028): `docs/LAPTOP_TASKS.md` 0 bytes;
  `data/calendar/high_impact.csv` line 2860 `2026-10-15 13:30,USD,1,Retail Sales MoM`, last row `2026-11-13 13:30,USD,1,PPI MoM`.
