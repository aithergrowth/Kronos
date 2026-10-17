# Gold (XAUUSD): the out-of-sample loss, the candidates together, the stop, the target, the hours, the 4H stake (14 October 2026, evening)

Ledgers `S/aca/base_XAUUSD.csv` (in sample, IS: 2024-01 to 2026-09, 143 trades, 1 % risk, guard off) and `S/aca/oos_base_XAUUSD.csv` (out of
sample, OOS: 2017-2023, 371 trades); the engine variants of today's batch `S/oct14d/` (`ban`, `dep25`, `tpfb3`, `sp37`, `stack`, `stack37`
and their `oos_` twins, read with `S/aca/eval_batch.py`). R is **after the 0.10R research cost** unless marked raw; a win is r > 0.05;
hours are Amsterdam; the fill (`opened_at`) is the close of the confirmation candle, which is also the time the session windows are
checked on (verified: the engine `ban` ledgers hold no trade in the banned slots). Scripts and full outputs:
`S/research/gold/gold_analysis.py` -> `gold_out.md` (+ `gold_trades.csv`, `gold_walk_trades.csv`), `gold_followup.py` ->
`gold_followup_out.md`, `gold_trail.py` -> `gold_trail_out.md`, `gold_x4h_sim.py` -> `gold_x4h_sim_out.txt` (the challenge replay of
`S/aca/challenge_sim_set.py` with gold's 4H multiplier as a parameter). The 5m walk reproduces the IS ledger trade for trade (0 trades off by
more than 0.05R) and the OOS ledger within 0.6R (one gap fill), as in `market_XAUUSD.md`. This page adds what `market_XAUUSD.md`,
`ledgers.md` and `regime.out` do not have; it does not repeat their tables.

| | trades | won | R a trade | R | deepest dip | a month | median stop |
|---|---|---|---|---|---|---|---|
| IS 2024-2026 | 143 | 49 % | +0.50 | +71.8 | -9.0R | 4.4 | 85 pips ($8.50) |
| OOS 2017-2023 | 371 | 30 % | -0.17 | -62.2 | -83.2R | 4.4 | 32 pips ($3.23) |

What today's engine runs already settled (`RESULTS_14oct.md`): the ban of 10:00-11:00 and 15:00-15:30 is better in both periods
(IS +11.6R, OOS +18.7R), so is the depth cut at a quarter of the zone (+3.1R / +11.0R); the 3R fallback target is flat in sample and
+21.5R out (-0.1R / +21.5R); the stack of the three +10.7R / +33.2R; the measured 3.7-pip spread with the live cap costs -11.6R in sample
and nothing out of sample (-0.4R). The sections below say where the out-of-sample loss comes from, how the candidates interact, what the
stop and the target do, and what the 4H double stake is worth on gold alone.

## The short version

1. **The -62R is 2018-2022** (-73.3R in those five years; 2017 -3.6R, 2023 +14.8R). It is not a "range" problem in the sense of more
   ranges: gold spent the same half of its days under ER20 0.2 in every block (50 % / 49 % / 51 %) and the bot took the same 42-49 %
   of its trades in them in every year. What differs is the **volatility**: the daily ATR was 0.98 % of price in 2017-2019, 1.34 % in
   2020-2023, 1.54 % in 2024-2026, and the days with an ATR over 1.43 % were 9 % / 39 % / 62 %. In that high-volatility regime the bot
   is flat out of sample (86 trades, 33 %, -0.02R a trade) and +0.50R in sample; the low-volatility regime (ATR under 1.08 %) holds 55 % of
   the OOS loss (157 trades, -34.1R) and has had 11 trades in sample (+8.0R), none in 2026. The ranging-days bucket (ER20 < 0.2) is where
   the loss shows up out of sample (-61.4R, p 0.006) and where the bot still earns in sample (+19.6R, p 0.18): the same trades, a
   different market. A volatility gate is information, not a rule (p 0.29, better in 6 of 9 years, 11 IS trades).
2. **The ban and the depth cut barely overlap** (4 IS / 11 OOS trades in both) and the ban carries the weight: on the trades the
   depth cut keeps, the banned trades are still -7.8R (28 trades, IS) and -20.0R (75, OOS); on the trades the ban keeps, the deep ones
   are -4.0R (14, IS) and +1.1R (18, OOS). On the engine's ban ledger the depth cut adds +2.9R / +3.4R. Order: the ban, then the depth cut.
3. **The 3R fallback does not add on top of them in the engine**: the stack's fallback trades gain (+9.6R IS, +16.3R OOS against the
   same rules at 2R) but its origin-target trades lose (-11.9R / -14.2R), because a 3R trade holds gold's one slot longer and pushes the
   next entry out. Net against ban + depth: -2.4R / +2.2R (ledger approximation) or -3.8R / +11.2R (engine ban ledger). Not settled;
   the engine must run ban + depth without the 3R, and the 3R with the break-even at 2.5R (section 4).
4. **The stop is not a problem in the live market**: no in-sample stop under 17 pips, the live cap (3.7 / 0.3 = 12.3 pips) never binds,
   the full spread is 5.4 % of R a trade. Out of sample 30 trades (8 %) had stops under 12.3 pips (20 % won, -14.0R, negative in each
   of the four years they occur); in 2017-2019 the median stop was 21-24 pips and a 3.7-pip spread is 16-18 % of R a trade, which turns
   those years' -35.9R into -50.7R. The cap refuses what should be refused; the 8-pip minimum never decides; nothing to change.
5. **The 2R break-even is the right level for the ledger as it is** (1R and 1.5R cost 29R / 10R IS and 41R / 14R OOS raw; 2.5R, 3R and
   none are within 2R IS and 1-6R worse OOS); it changes 2 IS trades and 14 OOS trades. The target is where the money is: **of the trades
   that reach 2R before their stop, 86 % (IS) / 78 % (OOS) reach 3R, and their median MFE is 7.0R / 6.0R**; a fixed target's expectancy
   rises with its distance up to 5R in both periods. On the 5m walk a 3.5R fallback with the break-even at 2.5R gives IS +104.6R raw
   (+0.63 a trade) and OOS +1.5R (-0.10 a trade), better than the ledger in 9 of 10 years, but the engine's slot effect (point 3) has
   to be measured first. A 1H-swing trail cuts the winners like the 15m one did (-10R IS); no-target variants with a trail after 3-4R
   make more R in both periods at a 15-29 % win rate and 30-day holds: not for a challenge account.
6. **London open against the US session**: the 09:00-10:00 hour is +17.6R in sample (3 of 3 years) and -8.4R out (negative in 6 of 7
   years); 14:30-17:00 +26.4R / -19.8R; 13:00-14:30 +33.8R / -11.9R. Every slot but the banned hours turns between the periods, and
   inside the engine stack the US session is the only slot positive out of sample (+4.8R). No session rule beyond the ban.
7. **Gold's 4H zones do not carry the double stake out of sample**: 13 trades, 62 %, +1.08R a trade in sample; 48 trades, 25 %, -0.24R a
   trade out (worse than the 1H zones' -0.16). At x2 the ledger goes +71.8 -> +85.9R (dip -9.0 -> -11.2R) in sample and -62.2 -> -73.7R
   (dip -83 -> -96R) out. The README's "4H zones 47 %, +0.49R in 2017-2023" is the three markets pooled; gold's own bucket is the one
   that turns. In the challenge replay gold at x1 passes as often (100 %), faster (median 77 against 84 days; 2024-25 starts within
   3 months 47 % against 42 %) and gives 0.4 %/month less in the funded account (+5.3 against +5.7 %).
8. **Frequency, for "a trade soon"**: from a random weekday the first gold trade comes within a median 4 days (90 % within 18) on the live
   profile; the ban makes it 5 days (90 % within 21) and 3.8 instead of 4.4 trades a month; the stack 3.4 a month.

## 1. The out-of-sample loss by year and regime

Per year (R after cost; the regime columns use the closed daily bar before the fill: ER20 = |close - close 20 days back| / the sum of the
20 absolute daily changes; ATR% = ATR14 / close; the ATR% bands are `regime.out`'s pooled terciles 1.08 and 1.43):

| year | trades | win % | R/t | R | dip | median stop pips | median ATR% at the trades | share of trades ER20 < 0.2 | R in ER20 < 0.2 | R in ER20 >= 0.2 | R at ATR% < 1.08 | 1.08-1.43 | > 1.43 | the year: median daily ATR% | days ER20 < 0.2 | return |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017 | 60 | 35 | -0.06 | -3.6 | -12.3 | 21 | 1.01 | 45 % | -10.7 (27) | +7.1 (33) | -1.1 (41) | -2.6 (19) | 0 (0) | 0.99 | 46 % | +12 % |
| 2018 | 57 | 30 | -0.27 | -15.7 | -21.8 | 24 | 0.98 | 49 % | -12.6 (28) | -3.1 (29) | -6.7 (47) | -9.0 (10) | 0 (0) | 0.96 | 51 % | -3 % |
| 2019 | 58 | 22 | -0.29 | -16.6 | -17.2 | 23 | 1.01 | 45 % | -16.6 (26) | 0.0 (32) | -19.5 (35) | +2.4 (10) | +0.4 (13) | 0.98 | 52 % | +18 % |
| 2020 | 51 | 31 | -0.24 | -12.0 | -14.0 | 48 | 1.36 | 43 % | -1.5 (22) | -10.5 (29) | -3.0 (9) | -6.9 (20) | -2.2 (22) | 1.52 | 52 % | +24 % |
| 2021 | 41 | 20 | -0.42 | -17.3 | -16.2 | 36 | 1.35 | 49 % | -13.9 (20) | -3.4 (21) | -1.3 (4) | -12.6 (23) | -3.5 (14) | 1.30 | 45 % | -6 % |
| 2022 | 61 | 28 | -0.19 | -11.7 | -19.3 | 46 | 1.45 | 46 % | -10.1 (28) | -1.6 (33) | -3.3 (3) | -11.5 (26) | +3.0 (32) | 1.37 | 53 % | +1 % |
| 2023 | 43 | 42 | +0.34 | +14.8 | -7.9 | 34 | 1.14 | 42 % | +4.0 (18) | +10.7 (25) | +0.7 (18) | +13.9 (20) | +0.2 (5) | 1.20 | 47 % | +12 % |
| 2024 | 57 | 39 | +0.24 | +13.7 | -5.9 | 52 | 1.43 | 35 % | -0.6 (20) | +14.3 (37) | +1.1 (6) | +13.9 (22) | -1.3 (29) | 1.33 | 53 % | +27 % |
| 2025 | 48 | 52 | +0.46 | +21.9 | -9.0 | 83 | 1.43 | 44 % | +5.7 (21) | +16.2 (27) | +6.9 (5) | +4.6 (19) | +10.4 (24) | 1.45 | 50 % | +63 % |
| 2026 | 38 | 61 | +0.95 | +36.3 | -2.2 | 136 | 2.29 | 47 % | +14.5 (18) | +21.8 (20) | 0 (0) | 0 (0) | +36.3 (38) | 2.43 | 49 % | -2 % |

| block | days ER20 < 0.2 | median daily ATR% | days ATR% > 1.43 | trades | win % | R/t | R | trades in ER20 < 0.2 | their R/t | trades at ATR% > 1.43 | their R/t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017-2019 | 50 % | 0.98 | 9 % | 175 | 29 | -0.21 | -35.9 | 81 | -0.49 | 13 | +0.03 |
| 2020-2023 | 49 % | 1.34 | 39 % | 196 | 30 | -0.13 | -26.3 | 88 | -0.24 | 73 | -0.03 |
| 2024-2026 | 51 % | 1.54 | 62 % | 143 | 49 | +0.50 | +71.8 | 59 | +0.33 | 91 | +0.50 |

| ATR% band | IS n / win / R/t / R | OOS n / win / R/t / R | half-stake gain IS | OOS | years the bucket is negative (of those with trades) |
|---|---|---|---|---|---|
| < 1.08 | 11 / 64 % / +0.72 / +8.0 | 157 / 30 % / -0.22 / -34.1 | -4.0 | +17.0 | 6 of 9 |
| 1.08-1.43 | 41 / 44 % / +0.45 / +18.5 | 128 / 27 % / -0.20 / -26.2 | -9.3 | +13.1 | 5 of 9 |
| > 1.43 | 91 / 49 % / +0.50 / +45.3 | 86 / 33 % / -0.02 / -2.0 | -22.7 | +1.0 | 3 of 8 |

- Years: 2018-2022 are the loss (-73.3R of -62.2R); 2017 is flat and 2023 is a good year on the OOS rules. Within the years the
  10:00-11:00 hour is negative in 2018, 2020, 2021, 2023, 2024, 2025 (`ledgers.md` A row), the fallback trades in 2019, 2021, 2022
  (section 4), the 4H zones in 2018, 2020, 2021 (section 6): the loss is spread over the cuts, no single one is the year.
- Regime: the efficiency ratio under 0.2 is OOS's loss bucket (169 trades, 24 %, -61.4R; permutation p 0.006) and IS's second-best
  (59 trades, 47 %, +19.6R; p 0.18, i.e. not below the IS average by anything a permutation would not give). The share of trades in it
  is the same in every year (42-49 %) because gold spends about half its days under 0.2 in every block. So "gold loses in ranges" is
  true only out of sample: the ranges of 2017-2022 were low-volatility ranges (ATR 1.0-1.35 % of price), the ranges of 2024-2026
  are 1.4-2.4 % ones, and inside the latter the bot earns (regime grid in `gold_out.md`: IS ER20 < 0.2 at ATR% > 1.43: 46 trades,
  46 %, +11.9R; OOS the same cell 37 trades, 32 %, -5.4R, the least bad OOS ER < 0.2 cell).
- The volatility regime is the one that separates the periods, but it is not a rule: the ATR% < 1.08 bucket's OOS R a trade (-0.22) is
  near the OOS average (-0.17; permutation p 0.29) and the in-sample bucket has 11 trades. It says where the loss lives (a market gold
  has not been in since 2023: 0 of 38 trades in 2026, 5 of 48 in 2025 at ATR% < 1.08) and that the live regime (ATR% 2.0 today, `regime.out`)
  is the one where gold was flat even in 2017-2023. It belongs in the morning regime line (ATR% next to ER20), not in a knob.
- The spread share of R moves with the same regime (section 3): 2017-2019 stops of 21-24 pips make a 3.7-pip spread 16-18 % of R; the
  ledger's 2-pip assumption flatters those years by 5-6R each.

## 2. The ban and the depth cut together (2 x 2, both periods)

"Banned" = the fill in 10:00-11:00 or 15:00-15:30 Amsterdam (`session.windows [[09:00,10:00],[13:00,15:00],[15:30,17:00]]`); "deep" = the
planned entry more than a quarter of the zone's height inside it (`risk.max_entry_depth 0.25`). Cells: n / win % / R a trade / sum R.

| IS | not deep (kept by dep25) | deep (refused by dep25) | all |
|---|---|---|---|
| not banned (kept by the ban) | 97 / 59 % / +0.88 / +85.5 | 14 / 21 % / -0.29 / -4.0 | 111 / 54 % / +0.73 / +81.5 |
| banned | 28 / 32 % / -0.28 / -7.8 | 4 / 25 % / -0.47 / -1.9 | 32 / 31 % / -0.30 / -9.7 |
| all | 125 / 53 % / +0.62 / +77.8 | 18 / 22 % / -0.33 / -5.9 | 143 / 49 % / +0.50 / +71.8 |

| OOS | not deep (kept by dep25) | deep (refused by dep25) | all |
|---|---|---|---|
| not banned (kept by the ban) | 267 / 31 % / -0.13 / -34.4 | 18 / 33 % / +0.06 / +1.1 | 285 / 31 % / -0.12 / -33.2 |
| banned | 75 / 27 % / -0.27 / -20.0 | 11 / 9 % / -0.81 / -9.0 | 86 / 24 % / -0.34 / -29.0 |
| all | 342 / 30 % / -0.16 / -54.4 | 29 / 24 % / -0.27 / -7.8 | 371 / 30 % / -0.17 / -62.2 |

| the rule applied second, on what the first keeps | IS | OOS |
|---|---|---|
| the ban on top of dep25 (banned trades among the not-deep) | 28 / 32 % / -0.28 / -7.8 | 75 / 27 % / -0.27 / -20.0 |
| dep25 on top of the ban (deep trades among the not-banned) | 14 / 21 % / -0.29 / -4.0 | 18 / 33 % / +0.06 / +1.1 |
| overlap (banned and deep) | 4 / 25 % / -0.47 / -1.9 | 11 / 9 % / -0.81 / -9.0 |

Engine cross-check (the ledger-level cut of one rule applied to the engine run of the other; the engine re-fills slots, the ledger
removal does not, which is why the two approximations differ by up to 9R out of sample):

| set | IS n / win / R/t / R | IS dip | OOS n / win / R/t / R | OOS dip |
|---|---|---|---|---|
| engine ban | 124 / 53 % / +0.67 / +83.4 | -7.9 | 316 / 31 % / -0.14 / -43.6 | -69.8 |
| engine dep25 | 132 / 52 % / +0.57 / +74.9 | -5.9 | 348 / 30 % / -0.15 / -51.2 | -68.8 |
| engine ban, then dep25 on the ledger | 109 / 57 % / +0.79 / +86.3 | -4.4 | 292 / 32 % / -0.14 / -40.2 | -61.0 |
| engine dep25, then the ban on the ledger | 102 / 58 % / +0.83 / +84.9 | -3.7 | 273 / 32 % / -0.11 / -31.2 | -55.3 |
| engine tpfb3 | 137 / 43 % / +0.52 / +71.7 | -7.1 | 357 / 27 % / -0.11 / -40.7 | -63.6 |
| engine tpfb3, then ban + dep25 on the ledger | 93 / 51 % / +0.88 / +81.6 | -3.7 | 258 / 28 % / -0.09 / -22.0 | -51.9 |
| engine stack (ban + dep25 + tpfb3) | 111 / 48 % / +0.74 / +82.5 | -4.4 | 286 / 27 % / -0.10 / -29.0 | -58.4 |
| engine stack37 (+ the 3.7-pip spread and the cap) | 110 / 47 % / +0.72 / +79.1 | -4.4 | 268 / 28 % / -0.12 / -31.8 | -54.6 |

| where the 3R fallback earns and loses inside the stack | IS n / win / R/t / R | OOS n / win / R/t / R |
|---|---|---|
| fallback trades at 2R (dep25 engine, ban on the ledger) | 50 / 60 % / +0.68 / +33.9 | 153 / 28 % / -0.27 / -41.4 |
| fallback trades at 3R (stack engine) | 55 / 44 % / +0.79 / +43.5 | 162 / 22 % / -0.15 / -25.1 |
| origin-target trades (dep25 engine, ban on the ledger) | 52 / 56 % / +0.98 / +51.0 | 120 / 36 % / +0.09 / +10.3 |
| origin-target trades (stack engine) | 56 / 52 % / +0.70 / +39.1 | 124 / 34 % / -0.03 / -3.9 |

- The ban holds once the depth cut is in (both periods, -0.28 / -0.27 a trade); the depth cut holds once the ban is in only in
  sample (-4.0R on 14 trades) and is flat out (+1.1R on 18): dep25's OOS gain was the 11 overlap trades (-9.0R) that the ban removes
  anyway. On the engine's own ban ledger the depth cut still adds +2.9R / +3.4R, so it is a small both-period plus, not the second
  pillar. Per year the two together (dep25 engine + the ban): better than the base in 7 of 10 years (2022 -4.0R, 2023 -0.1R, 2026 -3.8R).
- The 3R fallback is where the stack stops being additive: the engine's stack keeps 5 more fallback trades (a 3R trade that would
  have hit 2R stays open, the next setup in the same visit or slot is skipped) and loses 4 origin trades' worth of R in both
  periods (-11.9R / -14.2R). The three rules sum to +14.6R / +51.2R on their own engine runs and give +10.7R / +33.2R together. The
  walk's +9.5R in-sample gain for the 3R target (`market_XAUUSD.md` E) was -0.1R in the engine for the same reason. Measure
  ban + dep25 alone (`bd`) before anything with the target is adopted.

## 3. The stop against the 3.7-pip spread

The live profile: `min_stop_pips 8`, `max_spread_stop_fraction 0.3` (at 3.7 pips the cap refuses every stop under 12.3 pips),
`spread_buffer_pips 1` (sizing only). Stop = |fill - stop| in pips (0.1 = 1 pip; gold's R is the stop distance, so the spread's cost in
R is spread / stop).

| period | stop pips q10 / q25 / median / q75 / q90 | min | < 8 | < 11.1 (3 x the spread) | < 12.3 (the cap) | < 20 | < 37 (spread over 10 % of R) | full 3.7-pip spread, R a trade | the 1.7 pips over the research spread |
|---|---|---|---|---|---|---|---|---|---|
| IS | 35 / 52 / 85 / 126 / 282 | 17.0 | 0 | 0 | 0 | 2 | 17 (12 %) | 0.054 | 0.025 |
| OOS | 13 / 20 / 32 / 56 / 88 | 8.0 | 3 (at the 8-pip minimum) | 16 (4.3 %) | 30 (8.1 %) | 92 | 215 (58 %) | 0.138 | 0.063 |

| stop bucket | IS n / win / R/t / R | OOS n / win / R/t / R | OOS years negative (of those with trades) |
|---|---|---|---|
| < 11.1 pips | 0 | 16 / 25 % / -0.19 / -3.0 | 3 of 4 |
| 11.1-12.3 | 0 | 14 / 14 % / -0.79 / -11.0 | 3 of 3 |
| < 12.3 (refused live) | 0 | 30 / 20 % / -0.47 / -14.0 | 4 of 4 |
| 12.3-20 | 2 / 0 % / -1.10 / -2.2 | 62 / 27 % / -0.16 / -10.2 | 4 of 7 |
| 20-37 | 15 / 40 % / +0.71 / +10.6 | 123 / 30 % / -0.05 / -5.8 | 5 of 7 |
| 37-60 | 26 / 38 % / +0.13 / +3.3 | 71 / 32 % / -0.27 / -19.0 | 5 of 7 |
| > 60 | 100 / 54 % / +0.60 / +60.1 | 85 / 32 % / -0.16 / -13.2 | 5 of 7 |

| year | median stop pips | stops < 12.3 | their R | 3.7 / stop, mean (R a trade) | ledger R | R with the full 3.7-pip spread (R - 1.7 / stop) |
|---|---|---|---|---|---|---|
| 2017 | 21 | 13 | -5.1 | 0.199 | -3.6 | -9.1 |
| 2018 | 24 | 7 | -4.2 | 0.175 | -15.7 | -20.3 |
| 2019 | 23 | 9 | -3.6 | 0.175 | -16.6 | -21.3 |
| 2020 | 48 | 1 | -1.1 | 0.091 | -12.0 | -14.1 |
| 2021 | 36 | 0 | | 0.105 | -17.3 | -19.3 |
| 2022 | 46 | 0 | | 0.087 | -11.7 | -14.2 |
| 2023 | 34 | 0 | | 0.111 | +14.8 | +12.6 |
| 2024 | 52 | 0 | | 0.077 | +13.7 | +11.7 |
| 2025 | 83 | 0 | | 0.048 | +21.9 | +20.8 |
| 2026 | 136 | 0 | | 0.027 | +36.3 | +35.8 |

- In the live market the stop is a non-issue: the smallest in-sample stop is 17 pips (4.6 x the spread), the cap never binds, the
  8-pip minimum never binds, and the full spread is 5 % of R a trade (2.7 % in 2026). The two stops under 20 pips lost (-2.2R).
- Out of sample the trades the cap refuses are the worst bucket of the ledger (30 trades, 20 %, -0.47R a trade, every year negative)
  and the next bucket (12.3-20 pips) is still bad (-0.16); refusing under 20 pips would take 92 OOS trades and -24.2R, but 2 IS trades
  and -2.2R: a 20-pip floor is an OOS-only rule, not adoptable, and the cap at 0.3 already does the part that matters. Widening
  instead of refusing loses (`market_XAUUSD.md` 4: -2.8R).
- The engine's `sp37` run agrees: out of sample 33 base trades are gone (base R -17.3R, median stop 11.2 pips), 8 new ones came in
  (-6.2R), the spread took about 13R: net -0.4R. In sample 3 trades swapped (-4.4R net) and the spread took 7R: -11.6R. The research
  spread for gold should be 3.7 pips so that the ledgers carry what the account pays (`symbols: XAUUSD: typical_spread_pips: 3.7` in the
  yaml works, as `sp37_XAUUSD.yaml` shows; the cap `max_spread_stop_fraction 0.3` in the research yaml refuses what live refuses).
- Among the trades the ban and dep25 keep, the OOS stops under 12.3 pips are 21 trades, -10.5R: the cap and the stack are complements.
- The 1H ATR14 at the trades: $8.07 (IS) against $2.91 (OOS) and $2.05 in 2017-2019; stop / 1H ATR 0.89 against 1.10: the OOS stops were
  wider in ATR terms and smaller in dollars; the dollar size is what the spread sees.

## 4. The target: MFE before the stop, and the break-even level (5m walk, raw R)

MFE before the original stop is hit (no target, no break-even, up to 30 days; "stopped" = the stop was hit within 30 days):

| set | n | 0.5R | 1R | 1.5R | 2R | 2.5R | 3R | 4R | 5R | of those at 1R: 2R | of those at 2R: 3R | stopped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IS all | 143 | 79 % | 60 % | 51 % | 45 % | 41 % | 38 % | 34 % | 30 % | 74 % | 86 % | 88 % |
| IS origin target | 77 | 78 % | 56 % | 43 % | 39 % | 35 % | 34 % | 31 % | 29 % | 70 % | 87 % | 92 % |
| IS fixed-2R fallback | 66 | 80 % | 65 % | 61 % | 52 % | 47 % | 44 % | 36 % | 32 % | 79 % | 85 % | 83 % |
| IS not banned, not deep | 97 | 79 % | 68 % | 60 % | 54 % | 48 % | 46 % | 41 % | 36 % | 79 % | 87 % | 85 % |
| IS banned or deep | 46 | 78 % | 43 % | 33 % | 26 % | 24 % | 22 % | 17 % | 17 % | 60 % | 83 % | 96 % |
| OOS all | 371 | 62 % | 48 % | 38 % | 31 % | 28 % | 24 % | 20 % | 18 % | 65 % | 78 % | 95 % |
| OOS origin target | 180 | 61 % | 47 % | 41 % | 36 % | 30 % | 24 % | 22 % | 21 % | 76 % | 69 % | 96 % |
| OOS fixed-2R fallback | 191 | 63 % | 50 % | 35 % | 27 % | 26 % | 24 % | 18 % | 16 % | 55 % | 88 % | 94 % |
| OOS not banned, not deep | 267 | 62 % | 50 % | 39 % | 32 % | 29 % | 25 % | 22 % | 19 % | 64 % | 78 % | 95 % |
| OOS banned or deep | 104 | 62 % | 44 % | 35 % | 30 % | 26 % | 23 % | 16 % | 16 % | 67 % | 77 % | 95 % |

By year, the share reaching 1R / 2R / 3R / 4R before the stop: 2017 53 / 35 / 27 / 22 %, 2018 51 / 30 / 21 / 18, 2019 41 / 26 / 19 / 14,
2020 49 / 27 / 22 / 22, 2021 46 / 29 / 22 / 17, 2022 43 / 30 / 25 / 21, 2023 56 / 44 / 37 / 30, 2024 49 / 35 / 32 / 25, 2025 65 / 48 / 44 / 42,
2026 71 / 55 / 42 / 37.

| fixed target T (no break-even) | IS P(reach T before the stop) | IS expectancy P x T - (1 - P) | OOS P | OOS expectancy |
|---|---|---|---|---|
| 1R | 60 % | +0.20 | 48 % | -0.04 |
| 2R | 45 % | +0.34 | 31 % | -0.06 |
| 3R | 38 % | +0.54 | 24 % | -0.03 |
| 4R | 34 % | +0.68 | 20 % | +0.01 |
| 5R | 30 % | +0.80 | 18 % | +0.10 |
| 6R / 8R | 25 % / 20 % | +0.76 / +0.76 | 16 % / 12 % | +0.09 / +0.04 |

The median MFE of a trade that reaches 2R before its stop is 7.0R (IS) and 6.0R (OOS); 20 % (IS) and 12 % (OOS) of all trades run 8R or
more before their stop. The edge is the tail, and the fixed 2R target (half of the trades) sells it at 2R.

The break-even level with everything else as the ledger (the knobs `exits.breakeven_r_intraday` / `_swing`, both 2.0 in the gold profile):

| management | IS sum R | IS R/t (after cost) | IS win % | IS dip | OOS sum R | OOS R/t | OOS win % | OOS dip | years better than BE 2R (of 10) |
|---|---|---|---|---|---|---|---|---|---|
| no break-even | +84.1 | +0.49 | 49 | -7.2 | -31.3 | -0.18 | 30 | -61.0 | 1 |
| BE at +1R | +57.0 | +0.30 | 37 | -5.2 | -67.1 | -0.28 | 19 | -83.0 | 1 |
| BE at +1.5R | +76.2 | +0.43 | 45 | -6.0 | -40.0 | -0.21 | 26 | -56.7 | 2 |
| **BE at +2R (the ledger)** | **+86.1** | **+0.50** | **49** | **-7.2** | **-25.7** | **-0.17** | **30** | **-52.9** | |
| BE at +2.5R | +85.1 | +0.50 | 49 | -7.2 | -27.1 | -0.17 | 30 | -53.0 | 1 |
| BE at +3R | +84.1 | +0.49 | 49 | -7.2 | -31.1 | -0.18 | 30 | -57.0 | 1 |

Against no break-even the 2R rule changes 2 IS trades (both saved: -2.0R avoided, nothing given up) and 14 OOS trades (12 saved,
-12.0R avoided; 2 cut, +6.3R given up). With the fallback at 2R the break-even never fires on half the trades (the target is the
trigger), so the level is nearly inert in the live market; it earns its keep out of sample.

The fallback target distance and the break-even level together, whole ledger (raw R; the fallback trades get the new target, the origin
trades keep theirs; every trade gets the break-even):

| fallback target \ break-even | none | 1.5R | 2R | 2.5R | 3R |
|---|---|---|---|---|---|
| 2R (the ledger) | IS +84.1 / OOS -31.3 | +76.2 / -40.0 | **+86.1 / -25.7** | +85.1 / -27.1 | +84.1 / -31.1 |
| 2.5R | +87.6 / -10.9 | +80.1 / -30.8 | +87.6 / -11.4 | +88.6 / -6.6 | +87.6 / -10.6 |
| 3R (`tpfb3`) | +94.6 / -3.8 | +87.6 / -21.8 | +95.6 / -6.5 | **+97.6 / -2.0** | +94.6 / -3.5 |
| 3.5R | +99.6 / +0.9 | +93.1 / -19.3 | +101.6 / -4.1 | **+104.6 / +1.5** | +101.6 / +0.4 |
| 4R | +102.4 / -9.0 | +88.4 / -20.8 | +97.4 / -14.6 | +101.4 / -8.0 | +98.4 / -8.6 |
| 5R | +110.9 / +2.4 | +89.0 / -10.8 | +98.9 / -6.6 | +99.9 / -0.7 | +96.9 / -0.2 |

| variant | IS win % | IS R/t (after cost) | IS dip | OOS win % | OOS R/t | OOS dip | years better than the ledger (of 10) |
|---|---|---|---|---|---|---|---|
| the ledger (2R, BE 2R) | 49 | +0.50 | -7.2 | 30 | -0.17 | -52.9 | |
| 3R, BE 2R (`tpfb3`) | 43 | +0.57 | -6.0 | 27 | -0.12 | -45.2 | 8 |
| 3R, BE 2.5R | 45 | +0.58 | -6.0 | 28 | -0.11 | -44.2 | 9 |
| 3.5R, BE 2.5R | 43 | +0.63 | -8.0 | 26 | -0.10 | -43.5 | 9 |
| 3.5R, BE 3R | 43 | +0.61 | -8.0 | 27 | -0.10 | -41.8 | 9 |
| 4R, BE 3R | 41 | +0.59 | -8.0 | 25 | -0.12 | -52.8 | 8 |

Per year (raw): the ledger +2.4 / -10.5 / -10.8 / -6.9 / -13.2 / -5.6 / +19.1 / +19.4 / +26.7 / +40.1 (2017..2026); 3.5R with BE 2.5R
+7.3 / -5.4 / -4.7 / -6.8 / -10.8 / -1.2 / +23.0 / +25.2 / +39.8 / +39.5: better in every year but 2026 (-0.6R). On the trades the ban and
dep25 keep: the ledger IS +95.2 / OOS -8.2, 3R with BE 2.5R +101.6 / +10.0, 3.5R with BE 2.5R +106.1 / +8.5, 4R with BE 3R +102.6 / +18.8.

A 1H-swing trail (the stop follows the last confirmed 1H swing, 0.1 beyond, after +kR; `gold_trail.py`):

| management | IS sum R | IS win % | IS R/t | IS dip | OOS sum R | OOS win % | OOS R/t | OOS dip | years better (of 10) |
|---|---|---|---|---|---|---|---|---|---|
| targets kept, trail after +2R instead of the break-even | +75.6 | 49 | +0.43 | -8.1 | -32.7 | 31 | -0.19 | -62.4 | 2 |
| fallback 3.5R, trail after +2R | +77.2 | 44 | +0.44 | -9.5 | -13.6 | 29 | -0.14 | -55.0 | 6 |
| fallback 3.5R, BE 2R, trail after +3R | +92.8 | 43 | +0.55 | -7.7 | -6.5 | 27 | -0.12 | -48.2 | 7 |
| no target, trail after +1R | +62.9 | 36 | +0.34 | -7.3 | +16.4 | 25 | -0.06 | -49.7 | 7 |
| no target, trail after +2R | +83.0 | 35 | +0.48 | -9.7 | +7.2 | 23 | -0.08 | -57.8 | 6 |
| no target, BE 2R, trail after +3R | +92.6 | 29 | +0.55 | -7.0 | +22.1 | 18 | -0.04 | -53.0 | 7 |
| no target, BE 2R, trail after +4R | +117.3 | 25 | +0.72 | -7.0 | +13.2 | 15 | -0.07 | -53.2 | 8 |

- The break-even at 2R is right for the ledger as it is and wrong by half an R once the fallback target moves out: with a 3R or 3.5R
  fallback the best break-even is 2.5R in both periods (the pullback from 2R takes out trades that would have paid 3R; `market_XAUUSD.md`'s
  "3R without break-even OOS -10.4" is the same effect). If the engine confirms the 3R or 3.5R fallback, `breakeven_r_intraday` and
  `_swing` go to 2.5 with it, not before.
- The trail is a negative result as a replacement for the target (it cuts the winners at the first 1H pullback: -10R IS on the ledger's
  targets); the no-target variants show the size of the tail (IS +117R raw at a 25 % win rate) and are not for a challenge account
  (15-29 % won, trades held up to 30 days in gold's one slot, the day-5 and total limits on a 10k account). Information for the funded
  account later, not a rule now.
- All of these are 5m walks on the ledger's trades: the engine's slot effect (section 2) took the whole in-sample gain of `tpfb3` back
  (+9.5R on the walk, -0.1R in the engine). Every target variant has to be an engine run, with the ban and dep25 in and the challenge
  replay after it.

## 5. London open against the US session

| slot | IS n / win / R/t / R | IS years positive (of 3) | OOS n / win / R/t / R | OOS years positive (of 7) | engine stack IS | engine stack OOS |
|---|---|---|---|---|---|---|
| 09:00-09:30 | 15 / 40 % / +0.06 / +0.9 | 2 | 53 / 30 % / +0.04 / +2.2 | 3 | 14 / 36 % / +0.15 / +2.1 | 48 / 23 % / -0.20 / -9.8 |
| 09:30-10:00 | 16 / 56 % / +1.04 / +16.7 | 3 | 33 / 27 % / -0.32 / -10.6 | 2 | 12 / 50 % / +0.81 / +9.8 | 29 / 24 % / -0.21 / -6.0 |
| 10:00-11:00 (banned) | 21 / 33 % / -0.28 / -5.9 | 1 | 66 / 24 % / -0.33 / -22.1 | 3 | | |
| 13:00-14:30 | 43 / 51 % / +0.79 / +33.8 | 3 | 91 / 29 % / -0.13 / -11.9 | 1 | 42 / 52 % / +1.00 / +42.1 | 102 / 23 % / -0.18 / -18.0 |
| 14:30-17:00 | 48 / 54 % / +0.55 / +26.4 | 3 | 128 / 34 % / -0.15 / -19.8 | 1 | 43 / 47 % / +0.66 / +28.6 | 107 / 35 % / +0.05 / +4.8 |

By year (R after cost, trades): 09:00-10:00 2017 -3.8 (11), 2018 -6.6 (13), 2019 -3.0 (13), 2020 -0.7 (10), 2021 -7.1 (10), 2022 -3.7 (15),
2023 +16.5 (14), 2024 +8.0 (11), 2025 +4.7 (15), 2026 +4.9 (5); 14:30-17:00 +0.6 (25), -0.9 (24), -12.6 (18), -2.8 (15), -1.3 (9), -1.9 (24),
-1.0 (13), +4.9 (19), +9.6 (16), +11.9 (13); 13:00-14:30 -0.8 (15), -2.9 (13), -2.5 (16), -0.5 (16), -1.7 (10), -9.5 (11), +5.9 (10), +7.0 (17),
+8.7 (12), +18.0 (14).

- The London open is in-sample's steadiest slot (+0.57 a trade, every year positive) and out-of-sample's most consistent loser by
  years (6 of 7 negative, -0.10 a trade); its first half hour is flat in both periods, its second half turns (+1.04 / -0.32). Its trades
  resolve fast (median 1.9 / 1.8 hours open) and half are fallback trades in both periods.
- The US session is the larger slot in both periods (48 / 128 trades), IS +0.55, OOS -0.15 a trade; it is OOS's least bad slot per
  trade after 09:00-09:30 and, inside the engine stack, the only slot positive out of sample (+4.8R on 107 trades), while the stack's
  13:00-14:30 is OOS -18.0R: the afternoon halves turn between the periods. By weekday the US session is positive on every day in
  sample and negative on Tuesday, Wednesday and Friday out of sample: no pattern.
- Nothing to act on beyond the ban; the two half-hour slots that lose in both periods are already the ban.

## 6. The 4H zones at the double stake

| period | 4H n / win / R/t / R | 1H n / win / R/t / R | ledger R at x1 | at x1.5 | at x2 | dip at x1 | at x1.5 | at x2 | 4H median stop pips | median hours open | held across the daily break | across a weekend |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IS | 13 / 62 % / +1.08 / +14.1 | 130 / 48 % / +0.44 / +57.7 | +71.8 | +78.9 | +85.9 | -9.0 | -10.1 | -11.2 | 132 | 22 | 69 % | 31 % |
| OOS | 48 / 25 % / -0.24 / -11.5 | 323 / 30 % / -0.16 / -50.7 | -62.2 | -68.0 | -73.7 | -83.2 | -89.6 | -96.2 | 68 | 7 | 44 % | 23 % |

4H-zone trades by year (R, n): 2017 +0.5 (5), 2018 -5.9 (8), 2019 +5.3 (5), 2020 -6.6 (6), 2021 -5.5 (5), 2022 -1.0 (11), 2023 +1.8 (8),
2024 +8.0 (6), 2025 +2.3 (5), 2026 +3.8 (2); in the engine stack -0.0 (4), -5.6 (6), +5.3 (5), -5.5 (5), -3.3 (3), -2.0 (7), -1.0 (7),
+9.2 (7), +7.3 (5), +2.8 (2). MFE before the stop: IS 4H zones reach 2R in 62 %, OOS in 25 % (the 1H zones 43 % / 32 %).

The FTMO 2-Step replay (`gold_x4h_sim.py`: the four markets' ledgers, two open, 0.10R a trade, 1.5 % with the ladder, EURUSD's and NAS100's
4H zones at x2, the month-50/50 half, BTC half; gold's 4H multiplier varied; starts every weekday 2024-01 to 2026-06):

| gold ledger | gold 4H at | both phases | median days | 2026 starts within 6 weeks | 2024-25 starts within 3 months | funded at 1 %: average month | worst month | losing months of 33 |
|---|---|---|---|---|---|---|---|---|
| base (live) | x2 | 100 % | 84 | 71 % | 42 % | +5.7 % | -4.2 % | 9 |
| base | x1.5 | 100 % | 79 | 71 % | 46 % | +5.5 % | -3.8 % | 9 |
| base | x1 | 100 % | 77 | 69 % | 47 % | +5.3 % | -3.8 % | 8 |
| engine ban | x2 | 100 % | 79 | 66 % | 45 % | +6.3 % | -4.2 % | 8 |
| engine ban | x1 | 100 % | 73 | 64 % | 51 % | +5.7 % | -2.9 % | 8 |
| engine stack | x2 | 100 % | 70 | 62 % | 56 % | +6.3 % | -2.9 % | 9 |
| engine stack | x1 | 100 % | 70 | 62 % | 58 % | +5.7 % | -2.9 % | 7 |

- Gold's 4H zones are the one bucket where the periods disagree most: the best bucket in sample (+1.08 a trade on 13 trades, 8
  winners) and worse than the 1H zones out of sample (25 % won, -0.24 a trade on 48 trades; 2018, 2020, 2021 at -5.5 to -6.6R each).
  The x2 adds +14.1R in sample and takes -11.5R and 13R of dip out of sample. The README's pooled 2017-2023 figure (47 %, +0.49R)
  belongs to EURUSD and NAS100.
- For the account: x1 passes the same 100 %, faster in median (77 against 84 days), more often within 3 months from the 2024-25
  starts (47 against 42 %), with a shallower worst month (-3.8 against -4.2 %), and 0.4 %/month less in the funded replay (+5.3 against
  +5.7 %). The x2 is a funded-account lever with in-sample support only; on a 10k challenge it is variance (a 3 % position across
  the daily break in 69 % of the trades and a weekend in 31 %).
- Proposal: `risk.zone_risk_multiplier: {}` in `config/dorus_live_gold.yaml` (x1), or `{4H: 1.5}` as the middle; config only, no trade
  changes, so for Max whether a multiplier counts as a profile change during the challenge (the x1.5 note of `RESULTS_14oct.md` is the
  three-market version of the same question).

## 7. The ranked gold plan

What to change after the challenge (each config only, each passes both periods in the engine):

| rank | change | knob | IS | OOS | challenge replay | note |
|---|---|---|---|---|---|---|
| 1 | no entry 10:00-11:00 and 15:00-15:30 | `session.windows: [["09:00","10:00"],["13:00","15:00"],["15:30","17:00"]]` | +11.6R (124 trades, 53 %, dip -7.9R) | +18.7R (dip -70R) | median 79 against 84 days, funded +6.3 against +5.7 %/mo | holds in both periods after the depth cut; 3.8 instead of 4.4 trades a month |
| 2 | entries at most a quarter of the zone deep | `risk.max_entry_depth: 0.25` | +3.1R alone, +2.9R on top of the ban | +11.0R alone, +3.4R on top of the ban | (in the stack: 70 days, +6.3 %/mo, 56 % within 3 months) | small, both periods; its OOS gain alone is mostly the overlap with the ban |
| 3 | gold's 4H zones at x1 (or x1.5) | `risk.zone_risk_multiplier: {}` | -14.1R of multiplier gain | +11.5R, dip -96 -> -83R | passes as often, 7 days faster in median, +5.3 against +5.7 %/mo funded | a stake rule, no trade changes: for Max, possibly during the challenge |
| 4 | the fallback target at 3R or 3.5R with the break-even at 2.5R | `risk.tp_fallback_rr: 3.0` / `3.5`, `exits.breakeven_r_intraday: 2.5`, `_swing: 2.5` | walk +11.5R / +18.5R raw; engine `tpfb3` -0.1R | walk +23.7R / +27.2R; engine +21.5R | not yet | only after the engine runs below: the slot effect ate the in-sample gain of `tpfb3` |

What to leave: the break-even at 2R while the fallback is 2R (every other level is worse in both periods); `min_stop_pips 8` and the
spread cap at 0.3 (the cap refuses the OOS trades that lose, 0 trades in sample; a wider minimum or a 20-pip floor is an OOS-only rule);
the session otherwise (every other slot turns between the periods); the month-at-50/50 half stake (OOS 106 trades -6.5R, neutral); the
1.5 % stake and the ladder (not gold's to decide); nothing during the challenge: the live profile gives the first gold trade within a
median 4 days of any start and 90 % within 18 days.

What the engine must still measure (one at a time, both periods, then `challenge_sim_set.py`):

1. `bd`: the ban + `max_entry_depth 0.25` without the 3R fallback (expected IS about +85R, OOS about -31 to -40R): the adoption pair.
2. `tpfb3be25`: `bd` + `tp_fallback_rr 3.0` + break-even 2.5 (walk: IS +101.6 / OOS +10.0 raw on the kept trades); `tpfb35be25`: the same
   at 3.5R (+106.1 / +8.5). The engine's slot effect decides; if either beats `bd` in both periods, it replaces `tpfb3` in the stack.
3. The research yamls with `symbols: XAUUSD: typical_spread_pips: 3.7` and `max_spread_stop_fraction 0.3`, so the ledgers and the
   account agree (the `stack37` run shows the shape: -3.4R IS, -2.8R OOS against `stack`).
4. The stack with gold's 4H at x1 through the challenge replay is done here (table in section 6); the funded-account replay on the
   2017-2023 ledgers (`challenge_sim_oos.py`) with the same multiplier is the remaining both-period check of the stake.
5. Not worth a run: break-even 1R / 1.5R / 3R (both periods worse or equal), the 1H-swing trail on the ledger's targets (-10R IS), a
   20-pip or ATR-based minimum stop on gold, a session rule beyond the ban, a volatility (ATR%) or ER20 gate as a hard filter (the
   half-stake versions of `market_XAUUSD.md` C and D stay the only regime candidates, and they need code).


---

# Appendix A: full computed tables (`gold_analysis.py` -> `gold_out.md`)



Base: IS 143 / 49 % / +0.50 / +71.8  OOS 371 / 30 % / -0.17 / -62.2  (n / win % / R a trade / sum R, after 0.10R; win = r > 0.05)

## 1. The loss by year and regime

| year | trades | win % | R/t | R | dip | median stop $ | median stop pips | median ATR% (trades) | ER20<0.2 share of trades | R in ER20<0.2 | R in ER20>=0.2 | R ATR%<1.08 | R 1.08-1.43 | R >1.43 | year: median daily ATR% | days ER20<0.2 | year return |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017 | 60 | 35 | -0.06 | -3.6 | -12.3 | 2.08 | 21 | 1.01 | 45 % | -10.7 (27) | +7.1 (33) | -1.1 (41) | -2.6 (19) | +0.0 (0) | 0.99 | 46 % | +12 % |
| 2018 | 57 | 30 | -0.27 | -15.7 | -21.8 | 2.37 | 24 | 0.98 | 49 % | -12.6 (28) | -3.1 (29) | -6.7 (47) | -9.0 (10) | +0.0 (0) | 0.96 | 51 % | -3 % |
| 2019 | 58 | 22 | -0.29 | -16.6 | -17.2 | 2.28 | 23 | 1.01 | 45 % | -16.6 (26) | +0.0 (32) | -19.5 (35) | +2.4 (10) | +0.4 (13) | 0.98 | 52 % | +18 % |
| 2020 | 51 | 31 | -0.24 | -12.0 | -14.0 | 4.80 | 48 | 1.36 | 43 % | -1.5 (22) | -10.5 (29) | -3.0 (9) | -6.9 (20) | -2.2 (22) | 1.52 | 52 % | +24 % |
| 2021 | 41 | 20 | -0.42 | -17.3 | -16.2 | 3.63 | 36 | 1.35 | 49 % | -13.9 (20) | -3.4 (21) | -1.3 (4) | -12.6 (23) | -3.5 (14) | 1.30 | 45 % | -6 % |
| 2022 | 61 | 28 | -0.19 | -11.7 | -19.3 | 4.61 | 46 | 1.45 | 46 % | -10.1 (28) | -1.6 (33) | -3.3 (3) | -11.5 (26) | +3.0 (32) | 1.37 | 53 % | +1 % |
| 2023 | 43 | 42 | +0.34 | +14.8 | -7.9 | 3.38 | 34 | 1.14 | 42 % | +4.0 (18) | +10.7 (25) | +0.7 (18) | +13.9 (20) | +0.2 (5) | 1.20 | 47 % | +12 % |
| 2024 | 57 | 39 | +0.24 | +13.7 | -5.9 | 5.16 | 52 | 1.43 | 35 % | -0.6 (20) | +14.3 (37) | +1.1 (6) | +13.9 (22) | -1.3 (29) | 1.33 | 53 % | +27 % |
| 2025 | 48 | 52 | +0.46 | +21.9 | -9.0 | 8.30 | 83 | 1.43 | 44 % | +5.7 (21) | +16.2 (27) | +6.9 (5) | +4.6 (19) | +10.4 (24) | 1.45 | 50 % | +63 % |
| 2026 | 38 | 61 | +0.95 | +36.3 | -2.2 | 13.55 | 136 | 2.29 | 47 % | +14.5 (18) | +21.8 (20) | +0.0 (0) | +0.0 (0) | +36.3 (38) | 2.43 | 49 % | -2 % |

Period blocks (market days from the daily file; trades from the ledgers):

| block | days ER20<0.2 | median daily ATR% | days ATR%>1.43 | trades | win % | R/t | R | trades ER20<0.2 | their R/t | trades ATR%>1.43 | their R/t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017-2019 | 50 % | 0.98 | 9 % | 175 | 29 | -0.21 | -35.9 | 81 | -0.49 | 13 | +0.03 |
| 2020-2023 | 49 % | 1.34 | 39 % | 196 | 30 | -0.13 | -26.3 | 88 | -0.24 | 73 | -0.03 |
| 2024-2026 | 51 % | 1.54 | 62 % | 143 | 49 | +0.50 | +71.8 | 59 | +0.33 | 91 | +0.50 |

Regime grid (ER20 band x ATR% band), n / win % / R a trade / sum R:

| ER20 \ ATR% | IS <1.08 | IS 1.08-1.43 | IS >1.43 | OOS <1.08 | OOS 1.08-1.43 | OOS >1.43 |
|---|---|---|---|---|---|---|
| <0.2 | 3 / 67 % / +1.06 / +3.2 | 10 / 50 % / +0.45 / +4.5 | 46 / 46 % / +0.26 / +11.9 | 69 / 22 % / -0.40 / -27.7 | 63 / 22 % / -0.45 / -28.3 | 37 / 32 % / -0.15 / -5.4 |
| 0.2-0.35 | 5 / 60 % / +0.65 / +3.3 | 11 / 55 % / +0.69 / +7.6 | 29 / 62 % / +0.91 / +26.4 | 36 / 47 % / +0.29 / +10.5 | 31 / 26 % / -0.07 / -2.1 | 18 / 17 % / -0.67 / -12.0 |
| 0.35-0.5 | 1 / 100 % / +1.87 / +1.9 | 5 / 40 % / +1.38 / +6.9 | 7 / 29 % / +0.22 / +1.6 | 34 / 26 % / -0.37 / -12.5 | 25 / 40 % / +0.24 / +6.0 | 18 / 44 % / +0.64 / +11.5 |
| >0.5 | 2 / 50 % / -0.18 / -0.4 | 15 / 33 % / -0.03 / -0.5 | 9 / 44 % / +0.60 / +5.4 | 18 / 33 % / -0.25 / -4.4 | 9 / 33 % / -0.20 / -1.8 | 13 / 38 % / +0.31 / +4.0 |

ATR% bands alone and the half-stake arithmetic (positive = the period total improves):

| ATR% band | IS n / win / R/t / R | OOS n / win / R/t / R | half-stake gain IS | OOS | years better (of 10) |
|---|---|---|---|---|---|
| <1.08 | 11 / 64 % / +0.72 / +8.0 | 157 / 30 % / -0.22 / -34.1 | -4.0 | +17.0 | 6 of 9 |
| 1.08-1.43 | 41 / 44 % / +0.45 / +18.5 | 128 / 27 % / -0.20 / -26.2 | -9.3 | +13.1 | 5 of 9 |
| >1.43 | 91 / 49 % / +0.50 / +45.3 | 86 / 33 % / -0.02 / -2.0 | -22.7 | +1.0 | 3 of 8 |
- IS: ATR% < 1.08 bucket n=11, R/t +0.72; permutation p (mean R/t at or below the observed) = 0.673
- OOS: ATR% < 1.08 bucket n=157, R/t -0.22; permutation p (mean R/t at or below the observed) = 0.292
- IS: ER20 < 0.2 bucket n=59, R/t +0.33; permutation p = 0.182
- OOS: ER20 < 0.2 bucket n=169, R/t -0.36; permutation p = 0.006

## 2. The ban (10:00-11:00, 15:00-15:30) and the depth cut (> 0.25) together

Cells: n / win % / R a trade / sum R. "banned" = the fill in 10:00-11:00 or 15:00-15:30 Amsterdam; "deep" = planned entry more than a quarter of the zone inside it.

| IS | not deep (kept by dep25) | deep (refused by dep25) | all |
|---|---|---|---|
| not banned (kept by the ban) | 97 / 59 % / +0.88 / +85.5 | 14 / 21 % / -0.29 / -4.0 | 111 / 54 % / +0.73 / +81.5 |
| banned | 28 / 32 % / -0.28 / -7.8 | 4 / 25 % / -0.47 / -1.9 | 32 / 31 % / -0.30 / -9.7 |
| all | 125 / 53 % / +0.62 / +77.8 | 18 / 22 % / -0.33 / -5.9 | 143 / 49 % / +0.50 / +71.8 |

| OOS | not deep (kept by dep25) | deep (refused by dep25) | all |
|---|---|---|---|
| not banned (kept by the ban) | 267 / 31 % / -0.13 / -34.4 | 18 / 33 % / +0.06 / +1.1 | 285 / 31 % / -0.12 / -33.2 |
| banned | 75 / 27 % / -0.27 / -20.0 | 11 / 9 % / -0.81 / -9.0 | 86 / 24 % / -0.34 / -29.0 |
| all | 342 / 30 % / -0.16 / -54.4 | 29 / 24 % / -0.27 / -7.8 | 371 / 30 % / -0.17 / -62.2 |

Conditional reads (the rule applied second, on the trades the first rule keeps):

| | IS | OOS |
|---|---|---|
| ban on top of dep25: the banned trades among the not-deep | 28 / 32 % / -0.28 / -7.8 | 75 / 27 % / -0.27 / -20.0 |
| dep25 on top of the ban: the deep trades among the not-banned | 14 / 21 % / -0.29 / -4.0 | 18 / 33 % / +0.06 / +1.1 |
| overlap: banned AND deep | 4 / 25 % / -0.47 / -1.9 | 11 / 9 % / -0.81 / -9.0 |

Ledger-level totals (trades removed, nothing re-filled):

| set | IS n / win / R/t / R | IS dip | OOS n / win / R/t / R | OOS dip |
|---|---|---|---|---|
| base | 143 / 49 % / +0.50 / +71.8 | -9.0 | 371 / 30 % / -0.17 / -62.2 | -83.2 |
| ban | 111 / 54 % / +0.73 / +81.5 | -5.7 | 285 / 31 % / -0.12 / -33.2 | -62.4 |
| dep25 | 125 / 53 % / +0.62 / +77.8 | -4.8 | 342 / 30 % / -0.16 / -54.4 | -70.5 |
| ban + dep25 | 97 / 59 % / +0.88 / +85.5 | -3.7 | 267 / 31 % / -0.13 / -34.4 | -56.6 |

Engine cross-check (oct14d ledgers; the ledger-level cut applied to the engine run of the other rule):

| set | IS n / win / R/t / R | IS dip | OOS n / win / R/t / R | OOS dip |
|---|---|---|---|---|
| engine ban | 124 / 53 % / +0.67 / +83.4 | -7.9 | 316 / 31 % / -0.14 / -43.6 | -69.8 |
| engine dep25 | 132 / 52 % / +0.57 / +74.9 | -5.9 | 348 / 30 % / -0.15 / -51.2 | -68.8 |
| engine ban, then dep25 on the ledger | 109 / 57 % / +0.79 / +86.3 | -4.4 | 292 / 32 % / -0.14 / -40.2 | -61.0 |
| engine dep25, then the ban on the ledger | 102 / 58 % / +0.83 / +84.9 | -3.7 | 273 / 32 % / -0.11 / -31.2 | -55.3 |
| engine tpfb3 | 137 / 43 % / +0.52 / +71.7 | -7.1 | 357 / 27 % / -0.11 / -40.7 | -63.6 |
| engine tpfb3, then ban + dep25 on the ledger | 93 / 51 % / +0.88 / +81.6 | -3.7 | 258 / 28 % / -0.09 / -22.0 | -51.9 |
| engine stack (ban + dep25 + tpfb3) | 111 / 48 % / +0.74 / +82.5 | -4.4 | 286 / 27 % / -0.10 / -29.0 | -58.4 |
| engine stack37 (+ spread 3.7, cap) | 110 / 47 % / +0.72 / +79.1 | -4.4 | 268 / 28 % / -0.12 / -31.8 | -54.6 |

Engine ban ledger: trades in the banned slots after the ban = 0 (0 expected); engine dep25 ledger: deep trades = 0 (0 expected; a planned entry can sit a hair over 0.25 by rounding).

Where tpfb3 earns on top of ban + dep25: the fallback trades of the engine dep25-then-ban set (2R target) against the fallback trades of the engine stack (3R target):

| | IS n / win / R/t / R | OOS n / win / R/t / R |
|---|---|---|
| fallback trades at 2R (dep25 engine, ban on the ledger) | 50 / 60 % / +0.68 / +33.9 | 153 / 28 % / -0.27 / -41.4 |
| fallback trades at 3R (stack engine) | 55 / 44 % / +0.79 / +43.5 | 162 / 22 % / -0.15 / -25.1 |
| origin-target trades (dep25 engine, ban on the ledger) | 52 / 56 % / +0.98 / +51.0 | 120 / 36 % / +0.09 / +10.3 |
| origin-target trades (stack engine) | 56 / 52 % / +0.70 / +39.1 | 124 / 34 % / -0.03 / -3.9 |

Per year, engine sets against the base (R after cost):

| set | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| base | -3.6 | -15.7 | -16.6 | -12.0 | -17.3 | -11.7 | +14.8 | +13.7 | +21.9 | +36.3 |
| ban | +1.3 | -11.7 | -15.1 | -4.2 | -10.2 | -21.1 | +17.4 | +23.7 | +20.2 | +39.5 |
| dep25 | -1.4 | -12.4 | -14.4 | -8.6 | -15.2 | -10.5 | +11.4 | +15.8 | +26.1 | +33.0 |
| tpfb3 | +1.9 | -10.9 | -12.5 | -10.8 | -17.2 | -3.8 | +12.7 | +7.4 | +30.2 | +34.1 |
| stack | +10.2 | -7.7 | -10.8 | -4.9 | -10.2 | -18.2 | +12.8 | +19.6 | +33.7 | +29.3 |
| stack37 | +8.7 | -9.6 | -8.8 | -4.1 | -10.5 | -15.4 | +7.9 | +18.2 | +31.9 | +29.0 |
| dep25 engine + ban (ledger) | +3.8 | -6.7 | -15.9 | -4.5 | -6.9 | -15.7 | +14.7 | +25.3 | +27.1 | +32.5 |

## 3. The stop against the 3.7-pip spread

Stop = |fill - stop| in pips (0.1 = 1 pip); the live profile: min_stop_pips 8, max_spread_stop_fraction 0.3 (a 3.7-pip spread refuses every stop under 12.3 pips), spread_buffer_pips 1 (sizing only).

| period | stop pips q10 / q25 / median / q75 / q90 | min | stops < 8 | < 11.1 (3 x spread) | < 12.3 (the cap) | < 20 | < 37 (spread > 10 % of R) | mean 3.7/stop (R a trade of the full spread) | mean 1.7/stop (extra over the 2-pip research spread) |
|---|---|---|---|---|---|---|---|---|---|
| IS | 35 / 52 / 85 / 126 / 282 | 17.0 | 0 | 0 (0.0 %) | 0 (0.0 %) | 2 | 17 (12 %) | 0.054 | 0.025 |
| OOS | 13 / 20 / 32 / 56 / 88 | 8.0 | 3 | 16 (4.3 %) | 30 (8.1 %) | 92 | 215 (58 %) | 0.138 | 0.063 |

The small-stop trades and their R:

| bucket | IS n / win / R/t / R | OOS n / win / R/t / R | OOS years negative (of 7) |
|---|---|---|---|
| < 11.1 pips (3 x spread) | 0 | 16 / 25 % / -0.19 / -3.0 | 3 of 4 |
| 11.1-12.3 (3 x spread to the cap) | 0 | 14 / 14 % / -0.79 / -11.0 | 3 of 3 |
| < 12.3 (refused by the live cap) | 0 | 30 / 20 % / -0.47 / -14.0 | 4 of 4 |
| 12.3-20 | 2 / 0 % / -1.10 / -2.2 | 62 / 27 % / -0.16 / -10.2 | 4 of 7 |
| 20-37 | 15 / 40 % / +0.71 / +10.6 | 123 / 30 % / -0.05 / -5.8 | 5 of 7 |
| 37-60 | 26 / 38 % / +0.13 / +3.3 | 71 / 32 % / -0.27 / -19.0 | 5 of 7 |
| > 60 | 100 / 54 % / +0.60 / +60.1 | 85 / 32 % / -0.16 / -13.2 | 5 of 7 |

By year: the stop in pips and the spread share of R:

| year | median stop pips | stops < 12.3 | their R | median 3.7/stop | mean 3.7/stop (R a trade) | ledger R | R after the full 3.7-pip spread (simple: R - 1.7/stop) |
|---|---|---|---|---|---|---|---|
| 2017 | 21 | 13 | -5.1 | 0.178 | 0.199 | -3.6 | -9.1 |
| 2018 | 24 | 7 | -4.2 | 0.156 | 0.175 | -15.7 | -20.3 |
| 2019 | 23 | 9 | -3.6 | 0.162 | 0.175 | -16.6 | -21.3 |
| 2020 | 48 | 1 | -1.1 | 0.077 | 0.091 | -12.0 | -14.1 |
| 2021 | 36 | 0 | +0.0 | 0.102 | 0.105 | -17.3 | -19.3 |
| 2022 | 46 | 0 | +0.0 | 0.080 | 0.087 | -11.7 | -14.2 |
| 2023 | 34 | 0 | +0.0 | 0.110 | 0.111 | +14.8 | +12.6 |
| 2024 | 52 | 0 | +0.0 | 0.072 | 0.077 | +13.7 | +11.7 |
| 2025 | 83 | 0 | +0.0 | 0.045 | 0.048 | +21.9 | +20.8 |
| 2026 | 136 | 0 | +0.0 | 0.027 | 0.027 | +36.3 | +35.8 |
- engine sp37 IS: 142 trades against 143; base trades absent from sp37: 3 (their base R +2.2, stop pips median 63.9, max 64.9); trades new in sp37: 2 (-2.2R); sp37 min stop 18.8 pips
- engine sp37 OOS: 346 trades against 371; base trades absent from sp37: 33 (their base R -17.3, stop pips median 11.2, max 77.8); trades new in sp37: 8 (-6.2R); sp37 min stop 12.4 pips
- 4H-zone trades: median stop pips IS 132, OOS 68; 1H-zone: IS 82, OOS 31
- stop / 1H ATR14 median: IS 0.89, OOS 1.10; 1H ATR14 median IS $8.07, OOS $2.91; 2017-2019 $2.05

## 4. The target: MFE before the stop, and the break-even level (5m walk, raw R)

- IS: walk (BE 2R) reproduces the ledger: sum +86.1 against +86.1 raw, trades off by > 0.05R: 0
- OOS: walk (BE 2R) reproduces the ledger: sum -25.7 against -25.1 raw, trades off by > 0.05R: 1

MFE before the original stop is hit (no target, no break-even, up to 30 days): share of trades reaching at least

| set | n | 0.5R | 1R | 1.5R | 2R | 2.5R | 3R | 4R | 5R | of those at 1R: 2R | of those at 2R: 3R | stopped within 30 d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IS all | 143 | 79 % | 60 % | 51 % | 45 % | 41 % | 38 % | 34 % | 30 % | 74 % | 86 % | 88 % |
| IS origin target | 77 | 78 % | 56 % | 43 % | 39 % | 35 % | 34 % | 31 % | 29 % | 70 % | 87 % | 92 % |
| IS fixed-2R fallback | 66 | 80 % | 65 % | 61 % | 52 % | 47 % | 44 % | 36 % | 32 % | 79 % | 85 % | 83 % |
| IS 4H zones | 13 | 85 % | 77 % | 69 % | 62 % | 62 % | 62 % | 46 % | 38 % | 80 % | 100 % | 69 % |
| IS not banned, not deep | 97 | 79 % | 68 % | 60 % | 54 % | 48 % | 46 % | 41 % | 36 % | 79 % | 87 % | 85 % |
| IS banned or deep | 46 | 78 % | 43 % | 33 % | 26 % | 24 % | 22 % | 17 % | 17 % | 60 % | 83 % | 96 % |
| OOS all | 371 | 62 % | 48 % | 38 % | 31 % | 28 % | 24 % | 20 % | 18 % | 65 % | 78 % | 95 % |
| OOS origin target | 180 | 61 % | 47 % | 41 % | 36 % | 30 % | 24 % | 22 % | 21 % | 76 % | 69 % | 96 % |
| OOS fixed-2R fallback | 191 | 63 % | 50 % | 35 % | 27 % | 26 % | 24 % | 18 % | 16 % | 55 % | 88 % | 94 % |
| OOS 4H zones | 48 | 56 % | 42 % | 31 % | 25 % | 21 % | 19 % | 12 % | 10 % | 60 % | 75 % | 98 % |
| OOS not banned, not deep | 267 | 62 % | 50 % | 39 % | 32 % | 29 % | 25 % | 22 % | 19 % | 64 % | 78 % | 95 % |
| OOS banned or deep | 104 | 62 % | 44 % | 35 % | 30 % | 26 % | 23 % | 16 % | 16 % | 67 % | 77 % | 95 % |

By year:

| year | n | >=1R | >=2R | >=3R | >=4R |
|---|---|---|---|---|---|
| 2017 | 60 | 53 % | 35 % | 27 % | 22 % |
| 2018 | 57 | 51 % | 30 % | 21 % | 18 % |
| 2019 | 58 | 41 % | 26 % | 19 % | 14 % |
| 2020 | 51 | 49 % | 27 % | 22 % | 22 % |
| 2021 | 41 | 46 % | 29 % | 22 % | 17 % |
| 2022 | 61 | 43 % | 30 % | 25 % | 21 % |
| 2023 | 43 | 56 % | 44 % | 37 % | 30 % |
| 2024 | 57 | 49 % | 35 % | 32 % | 25 % |
| 2025 | 48 | 65 % | 48 % | 44 % | 42 % |
| 2026 | 38 | 71 % | 55 % | 42 % | 37 % |

Break-even level, everything else as the ledger (raw R; the ledger is BE at 2R):

| management | IS sum R | IS R/t (after cost) | IS win % | IS dip | OOS sum R | OOS R/t | OOS win % | OOS dip | years better than BE 2R (of 10) |
|---|---|---|---|---|---|---|---|---|---|
| no break-even | +84.1 | +0.488 | 49 | -7.2 | -31.3 | -0.184 | 30 | -61.0 | 1 |
| BE at +1R | +57.0 | +0.299 | 37 | -5.2 | -67.1 | -0.281 | 19 | -83.0 | 1 |
| BE at +1.5R | +76.2 | +0.433 | 45 | -6.0 | -40.0 | -0.208 | 26 | -56.7 | 2 |
| BE at +2R (ledger) | +86.1 | +0.502 | 49 | -7.2 | -25.7 | -0.169 | 30 | -52.9 | 0 |
| BE at +2.5R | +85.1 | +0.495 | 49 | -7.2 | -27.1 | -0.173 | 30 | -53.0 | 1 |
| BE at +3R | +84.1 | +0.488 | 49 | -7.2 | -31.1 | -0.184 | 30 | -57.0 | 1 |

What the 2R break-even does trade by trade (against no break-even):

- IS: 2 trades change; saved (no-BE result a loss, BE result 0): 2, -2.0R avoided; cut (no-BE result a win, BE result 0): 0, +0.0R given up; other 0
- OOS: 14 trades change; saved (no-BE result a loss, BE result 0): 12, -12.0R avoided; cut (no-BE result a win, BE result 0): 2, +6.3R given up; other 0

The fallback trades at a 3R target with the break-even level (raw R; the knob `tp_fallback_rr 3.0` + `breakeven_r_intraday`):

| fallback trades | IS n | IS sum R at 2R (ledger) | 3R, no BE | 3R, BE 1.5R | 3R, BE 2R | 3R, BE 2.5R | 2.5R, BE 2R | OOS n | OOS at 2R | 3R, no BE | 3R, BE 1.5R | 3R, BE 2R | 3R, BE 2.5R | 2.5R, BE 2R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 66 | +37.8 | +48.3 | +50.3 | +47.3 | +50.3 | +39.3 | 191 | -37.4 | -10.4 | -27.1 | -18.8 | -12.8 | -23.6 |
| not banned, not deep | 48 | +40.9 | +46.3 | +46.3 | +45.3 | +48.3 | +39.8 | 149 | -30.9 | -10.0 | -18.1 | -15.8 | -12.8 | -21.1 |

Per year, the fallback trades: 2R (ledger) / 3R no BE / 3R BE 2R:

| year | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2R (ledger) | +10.1 | -2.7 | -15.6 | -1.7 | -13.1 | -15.0 | +0.6 | +14.4 | +18.3 | +5.0 |
| 3R, no BE | +16.0 | +2.4 | -11.4 | +2.7 | -12.8 | -12.0 | +4.6 | +19.3 | +28.0 | +1.0 |
| 3R, BE 2R | +14.3 | +0.4 | -12.0 | -1.1 | -14.0 | -12.0 | +5.6 | +17.3 | +26.0 | +4.0 |
| 3R, BE 2.5R | +17.0 | +2.4 | -12.0 | -1.1 | -12.8 | -12.0 | +5.6 | +19.3 | +29.0 | +2.0 |

## 5. London open against the US session

| slot | IS n / win / R/t / R | IS years positive (of 3) | OOS n / win / R/t / R | OOS years positive (of 7) | engine stack IS | engine stack OOS |
|---|---|---|---|---|---|---|
| 09:00-09:30 | 15 / 40 % / +0.06 / +0.9 | 2 | 53 / 30 % / +0.04 / +2.2 | 3 | 14 / 36 % / +0.15 / +2.1 | 48 / 23 % / -0.20 / -9.8 |
| 09:30-10:00 | 16 / 56 % / +1.04 / +16.7 | 3 | 33 / 27 % / -0.32 / -10.6 | 2 | 12 / 50 % / +0.81 / +9.8 | 29 / 24 % / -0.21 / -6.0 |
| 10:00-11:00 | 21 / 33 % / -0.28 / -5.9 | 1 | 66 / 24 % / -0.33 / -22.1 | 3 | 0 | 0 |
| 13:00-14:30 | 43 / 51 % / +0.79 / +33.8 | 3 | 91 / 29 % / -0.13 / -11.9 | 1 | 42 / 52 % / +1.00 / +42.1 | 102 / 23 % / -0.18 / -18.0 |
| 14:30-17:00 | 48 / 54 % / +0.55 / +26.4 | 3 | 128 / 34 % / -0.15 / -19.8 | 1 | 43 / 47 % / +0.66 / +28.6 | 107 / 35 % / +0.05 / +4.8 |
- London open 09:00-10:00: IS 31 / 48 % / +0.57 / +17.6 (dip -3.0); OOS 86 / 29 % / -0.10 / -8.4 (dip -27.5); 4H-zone share IS 3 %, OOS 17 %; fallback share IS 45 %, OOS 50 %; median hours open IS 1.9, OOS 1.8
- US session 14:30-17:00: IS 48 / 54 % / +0.55 / +26.4 (dip -5.7); OOS 128 / 34 % / -0.15 / -19.8 (dip -27.6); 4H-zone share IS 15 %, OOS 15 %; fallback share IS 50 %, OOS 58 %; median hours open IS 5.2, OOS 3.5
- 13:00-14:30: IS 43 / 51 % / +0.79 / +33.8 (dip -3.5); OOS 91 / 29 % / -0.13 / -11.9 (dip -20.9); 4H-zone share IS 7 %, OOS 9 %; fallback share IS 42 %, OOS 51 %; median hours open IS 1.9, OOS 0.9

London open by year (09:00-10:00) and the US session by year (14:30-17:00), R after cost:

| year | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| 09:00-10:00 | -3.8 (11) | -6.6 (13) | -3.0 (13) | -0.7 (10) | -7.1 (10) | -3.7 (15) | +16.5 (14) | +8.0 (11) | +4.7 (15) | +4.9 (5) |
| 10:00-11:00 | +0.3 (9) | -5.4 (7) | +1.5 (11) | -8.0 (10) | -7.3 (12) | +3.4 (11) | -6.6 (6) | -6.2 (10) | -1.2 (5) | +1.5 (6) |
| 13:00-14:30 | -0.8 (15) | -2.9 (13) | -2.5 (16) | -0.5 (16) | -1.7 (10) | -9.5 (11) | +5.9 (10) | +7.0 (17) | +8.7 (12) | +18.0 (14) |
| 14:30-17:00 | +0.6 (25) | -0.9 (24) | -12.6 (18) | -2.8 (15) | -1.3 (9) | -1.9 (24) | -1.0 (13) | +4.9 (19) | +9.6 (16) | +11.9 (13) |

The US session on the week's days and the news days (the blackout covers 14:00-15:00 on data days): US-session trades by weekday, n / R:

- IS: Mon 8 / +12.1, Tue 9 / +2.0, Wed 10 / +5.9, Thu 15 / +5.1, Fri 6 / +1.3
- OOS: Mon 17 / +1.9, Tue 22 / -6.7, Wed 31 / -7.4, Thu 28 / +1.0, Fri 30 / -8.7

## 6. The 4H zones at double stake

| period | 4H n / win / R/t / R | 1H n / win / R/t / R | ledger R at x1 | at x1.5 | at x2 | dip at x1 | x1.5 | x2 | 4H trades: median stop pips | median hours open | held across the daily break | across a weekend |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IS | 13 / 62 % / +1.08 / +14.1 | 130 / 48 % / +0.44 / +57.7 | +71.8 | +78.9 | +85.9 | -9.0 | -10.1 | -11.2 | 132 | 22 | 69 % | 31 % |
| OOS | 48 / 25 % / -0.24 / -11.5 | 323 / 30 % / -0.16 / -50.7 | -62.2 | -68.0 | -73.7 | -83.2 | -89.6 | -96.2 | 68 | 7 | 44 % | 23 % |

4H-zone trades by year (n / R at x1):

| year | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| 4H zones | +0.5 (5) | -5.9 (8) | +5.3 (5) | -6.6 (6) | -5.5 (5) | -1.0 (11) | +1.8 (8) | +8.0 (6) | +2.3 (5) | +3.8 (2) |
| 4H zones in the engine stack | -0.0 (4) | -5.6 (6) | +5.3 (5) | -5.5 (5) | -3.3 (3) | -2.0 (7) | -1.0 (7) | +9.2 (7) | +7.3 (5) | +2.8 (2) |

- engine stack IS: 4H 14 / 57 % / +1.38 / +19.3; total at x1 +82.5 (dip -4.4), at x2 +101.8 (dip -5.5)
- engine stack OOS: 4H 37 / 19 % / -0.33 / -12.1; total at x1 -29.0 (dip -58.4), at x2 -41.1 (dip -69.6)
- engine ban IS: 4H 14 / 64 % / +1.14 / +15.9; total at x1 +83.4 (dip -7.9), at x2 +99.3 (dip -10.1)
- engine ban OOS: 4H 41 / 29 % / -0.15 / -6.1; total at x1 -43.6 (dip -69.8), at x2 -49.7 (dip -77.7)
- 4H zones IS: MFE before the stop >= 1R 77 %, >= 2R 62 %, >= 3R 62 %; fallback share 69 %; median planned R:R 2.00
- 4H zones OOS: MFE before the stop >= 1R 42 %, >= 2R 25 %, >= 3R 19 %; fallback share 58 %; median planned R:R 2.00
- live stakes (4H x2, month 50/50 half) IS: +86.6R-units (dip -11.2) against x1 +71.8 (dip -9.0); month-50/50 trades 11, their R -1.4
- live stakes (4H x2, month 50/50 half) OOS: -68.6R-units (dip -82.3) against x1 -62.2 (dip -83.2); month-50/50 trades 106, their R -6.5
---

# Appendix B: follow-up tables (`gold_followup.py` -> `gold_followup_out.md`)



## (a) Fallback target distance x break-even level, whole ledger (raw R; the ledger = orig target, BE 2R)

| fallback target \ BE | none | 1.5R | 2R | 2.5R | 3R |
|---|---|---|---|---|---|
| 2R (ledger) | IS +84.1 / OOS -31.3 | IS +76.2 / OOS -40.0 | IS +86.1 / OOS -25.7 | IS +85.1 / OOS -27.1 | IS +84.1 / OOS -31.1 |
| 2.5R | IS +87.6 / OOS -10.9 | IS +80.1 / OOS -30.8 | IS +87.6 / OOS -11.4 | IS +88.6 / OOS -6.6 | IS +87.6 / OOS -10.6 |
| 3.0R | IS +94.6 / OOS -3.8 | IS +87.6 / OOS -21.8 | IS +95.6 / OOS -6.5 | IS +97.6 / OOS -2.0 | IS +94.6 / OOS -3.5 |
| 3.5R | IS +99.6 / OOS +0.9 | IS +93.1 / OOS -19.3 | IS +101.6 / OOS -4.1 | IS +104.6 / OOS +1.5 | IS +101.6 / OOS +0.4 |
| 4.0R | IS +102.4 / OOS -9.0 | IS +88.4 / OOS -20.8 | IS +97.4 / OOS -14.6 | IS +101.4 / OOS -8.0 | IS +98.4 / OOS -8.6 |
| 5.0R | IS +110.9 / OOS +2.4 | IS +89.0 / OOS -10.8 | IS +98.9 / OOS -6.6 | IS +99.9 / OOS -0.7 | IS +96.9 / OOS -0.2 |

Win rate and dip for the candidates (after cost; dip of the cumulative R in closed order):

| variant | IS win % | IS R/t | IS dip | OOS win % | OOS R/t | OOS dip | years better than the ledger (of 10) |
|---|---|---|---|---|---|---|---|
| ledger (2R, BE 2R) | 49 | +0.502 | -7.2 | 30 | -0.169 | -52.9 | 0 |
| 3R, BE 2R (tpfb3) | 43 | +0.568 | -6.0 | 27 | -0.118 | -45.2 | 8 |
| 3R, BE 2.5R | 45 | +0.582 | -6.0 | 28 | -0.105 | -44.2 | 9 |
| 3R, no BE | 45 | +0.561 | -6.0 | 29 | -0.110 | -47.8 | 8 |
| 3.5R, BE 2.5R | 43 | +0.631 | -8.0 | 26 | -0.096 | -43.5 | 9 |
| 3.5R, BE 3R | 43 | +0.610 | -8.0 | 27 | -0.099 | -41.8 | 9 |
| 4R, BE 2.5R | 41 | +0.609 | -8.0 | 25 | -0.122 | -55.2 | 7 |
| 4R, BE 3R | 41 | +0.588 | -8.0 | 25 | -0.123 | -52.8 | 8 |
| 4R, no BE | 42 | +0.616 | -9.0 | 27 | -0.124 | -53.4 | 7 |
| 5R, BE 3R | 38 | +0.578 | -8.0 | 24 | -0.101 | -47.8 | 8 |

Per year (raw R): ledger / 3R BE 2R / 3R BE 2.5R / 3.5R BE 2.5R / 4R BE 3R

| variant | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| ledger | +2.4 | -10.5 | -10.8 | -6.9 | -13.2 | -5.6 | +19.1 | +19.4 | +26.7 | +40.1 |
| 3R, BE 2R | +6.6 | -6.9 | -7.2 | -6.3 | -14.1 | -2.7 | +24.1 | +22.2 | +34.3 | +39.0 |
| 3R, BE 2.5R | +8.3 | -5.9 | -7.2 | -6.3 | -11.3 | -2.7 | +23.1 | +23.2 | +37.3 | +37.0 |
| 3.5R, BE 2.5R | +7.3 | -5.4 | -4.7 | -6.8 | -10.8 | -1.2 | +23.0 | +25.2 | +39.8 | +39.5 |
| 4R, BE 3R | +6.3 | -5.9 | -10.6 | -4.5 | -15.3 | +0.3 | +21.0 | +26.2 | +43.3 | +28.8 |

The same on the trades the ban and dep25 keep (ledger-level):

| variant | IS n | IS sum R | OOS n | OOS sum R |
|---|---|---|---|---|
| ledger (2R, BE 2R) | 97 | +95.2 | 267 | -8.2 |
| 3R, BE 2R | 97 | +99.6 | 267 | +7.5 |
| 3R, BE 2.5R | 97 | +101.6 | 267 | +10.0 |
| 3R, no BE | 97 | +99.6 | 267 | +11.5 |
| 3.5R, BE 2.5R | 97 | +106.1 | 267 | +8.5 |
| 4R, BE 3R | 97 | +102.6 | 267 | +18.8 |

## (b) Fixed-target expectancy from the MFE-before-stop distribution (no break-even; a trade not stopped within 30 days counted at its MFE floor)

| target | IS P(reach) | IS EV = P x T - (1-P) | OOS P(reach) | OOS EV |
|---|---|---|---|---|
| 1R | 60 % | +0.20 | 48 % | -0.04 |
| 1.5R | 51 % | +0.28 | 38 % | -0.06 |
| 2R | 45 % | +0.34 | 31 % | -0.06 |
| 2.5R | 41 % | +0.42 | 28 % | -0.02 |
| 3R | 38 % | +0.54 | 24 % | -0.03 |
| 4R | 34 % | +0.68 | 20 % | +0.01 |
| 5R | 30 % | +0.80 | 18 % | +0.10 |
| 6R | 25 % | +0.76 | 16 % | +0.09 |
| 8R | 20 % | +0.76 | 12 % | +0.04 |

The MFE distribution tail: median MFE of the trades that reach 2R before the stop: IS 7.0R, OOS 6.0R; share of trades with MFE >= 8R: IS 20 %, OOS 12 %

## (c) The ban and the depth cut inside the volatility regime (n / win % / R a trade / sum R, after cost)

| regime | period | all | banned | deep (not banned) | kept by both |
|---|---|---|---|---|---|
| ATR% > 1.43 (the live regime) | IS | 91 / 49 % / +0.50 / +45.3 | 20 / 35 % / -0.27 / -5.4 | 9 / 22 % / -0.39 / -3.5 | 62 / 58 % / +0.87 / +54.2 |
| ATR% > 1.43 (the live regime) | OOS | 86 / 33 % / -0.02 / -2.0 | 22 / 27 % / -0.09 / -1.9 | 3 / 33 % / -0.14 / -0.4 | 61 / 34 % / +0.01 / +0.3 |
| ATR% <= 1.43 | IS | 52 / 48 % / +0.51 / +26.5 | 12 / 25 % / -0.36 / -4.3 | 5 / 20 % / -0.11 / -0.5 | 35 / 60 % / +0.90 / +31.3 |
| ATR% <= 1.43 | OOS | 285 / 29 % / -0.21 / -60.2 | 64 / 23 % / -0.42 / -27.1 | 15 / 33 % / +0.10 / +1.5 | 206 / 30 % / -0.17 / -34.7 |
| ER20 < 0.2 | IS | 59 / 47 % / +0.33 / +19.6 | 14 / 36 % / -0.19 / -2.6 | 6 / 0 % / -1.10 / -6.6 | 39 / 59 % / +0.74 / +28.8 |
| ER20 < 0.2 | OOS | 169 / 24 % / -0.36 / -61.4 | 42 / 21 % / -0.45 / -19.0 | 8 / 25 % / -0.29 / -2.3 | 119 / 25 % / -0.34 / -40.0 |
| ER20 >= 0.2 | IS | 84 / 50 % / +0.62 / +52.3 | 18 / 28 % / -0.39 / -7.0 | 8 / 38 % / +0.32 / +2.6 | 58 / 59 % / +0.98 / +56.7 |
| ER20 >= 0.2 | OOS | 202 / 34 % / -0.00 / -0.8 | 44 / 27 % / -0.23 / -9.9 | 10 / 40 % / +0.34 / +3.4 | 148 / 36 % / +0.04 / +5.7 |

## (d) Small stops among the trades the ban and dep25 keep (the cap refuses < 12.3 pips live)

| stop pips | IS | OOS |
|---|---|---|
| < 12.3 | 0 | 21 / 19 % / -0.50 / -10.5 |
| 12.3-20 | 0 | 41 / 29 % / -0.07 / -2.8 |
| 20-37 | 11 / 55 % / +1.37 / +15.0 | 86 / 33 % / +0.06 / +4.8 |
| >= 37 | 86 / 59 % / +0.82 / +70.5 | 119 / 33 % / -0.22 / -25.9 |
- IS: refusing stops under 20 pips (a 'spread at most 18.5 % of R' rule) removes 2 trades with -2.2R; under 12.3: 0 with +0.0R
- OOS: refusing stops under 20 pips (a 'spread at most 18.5 % of R' rule) removes 92 trades with -24.2R; under 12.3: 30 with -14.0R
---

# Appendix C: the 1H-swing trail (`gold_trail.py` -> `gold_trail_out.md`)

## A 1H-swing trail instead of (or after) the break-even (raw R; 5m walk)

| management | IS sum R | IS win % | IS R/t (after cost) | IS dip | OOS sum R | OOS win % | OOS R/t | OOS dip | years better than the ledger (of 10) |
|---|---|---|---|---|---|---|---|---|---|
| ledger (targets, BE 2R) | +86.1 | 49 | +0.502 | -7.2 | -25.7 | 30 | -0.169 | -52.9 | 0 |
| targets kept, 1H trail after +2R (no BE) | +75.6 | 49 | +0.429 | -8.1 | -32.7 | 31 | -0.188 | -62.4 | 2 |
| fallback 3.5R, BE 2.5R | +104.6 | 43 | +0.631 | -8.0 | +1.5 | 26 | -0.096 | -43.5 | 9 |
| fallback 3.5R, 1H trail after +2R | +77.2 | 44 | +0.440 | -9.5 | -13.6 | 29 | -0.137 | -55.0 | 6 |
| fallback 3.5R, BE 2R, 1H trail after +3R | +92.8 | 43 | +0.549 | -7.7 | -6.5 | 27 | -0.118 | -48.2 | 7 |
| no target, 1H trail after +1R | +62.9 | 36 | +0.340 | -7.3 | +16.4 | 25 | -0.056 | -49.7 | 7 |
| no target, 1H trail after +2R | +83.0 | 35 | +0.481 | -9.7 | +7.2 | 23 | -0.080 | -57.8 | 6 |
| no target, BE 2R, 1H trail after +3R | +92.6 | 29 | +0.547 | -7.0 | +22.1 | 18 | -0.040 | -53.0 | 7 |
| no target, BE 2R, 1H trail after +4R | +117.3 | 25 | +0.720 | -7.0 | +13.2 | 15 | -0.065 | -53.2 | 8 |

Per year (raw R):

| variant | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| ledger | +2.4 | -10.5 | -10.8 | -6.9 | -13.2 | -5.6 | +19.1 | +19.4 | +26.7 | +40.1 |
| fallback 3.5R, BE 2.5R | +7.3 | -5.4 | -4.7 | -6.8 | -10.8 | -1.2 | +23.0 | +25.2 | +39.8 | +39.5 |
| no target, BE 2R, trail after +3R | +28.1 | -4.3 | -3.0 | -2.6 | -11.7 | -17.8 | +33.4 | +15.1 | +53.7 | +23.8 |
| no target, trail after +2R | +27.3 | -11.9 | -5.0 | -2.3 | -10.2 | -16.3 | +25.6 | +12.7 | +46.8 | +23.6 |
---

# Appendix D: the challenge replay with gold 4H at x2 / x1.5 / x1 (`gold_x4h_sim.py` -> `gold_x4h_sim_out.txt`)

```
=== gold base x2
  phase 1 passed 100%: median 40 days, 25-75% 20-110
  both phases 100%: median 84 days, 25-75% 43-187
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 90 days, failed 0%
    starts 2025: both phases 100%, median 131 days, failed 0%
    starts 2026: both phases 100%, median 34 days, failed 0%
  funded at 1 %: average month +5.7%, median +5.0%, worst -4.2%, best +27.8%, losing months 9 of 33
  by year: 2024 +2.9%/mo  2025 +4.7%/mo  2026 +10.9%/mo
  trades 322 (9.8/month), won 51%, avg R +0.64 after costs; wins avg +2.30R
  at 1.5 %: average month +7.9%, worst -5.6%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 42%
=== gold base x1
  phase 1 passed 100%: median 47 days, 25-75% 21-110
  both phases 100%: median 77 days, 25-75% 46-161
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 94 days, failed 0%
    starts 2025: both phases 100%, median 111 days, failed 0%
    starts 2026: both phases 100%, median 34 days, failed 0%
  funded at 1 %: average month +5.3%, median +4.3%, worst -3.8%, best +27.8%, losing months 8 of 33
  by year: 2024 +2.2%/mo  2025 +4.5%/mo  2026 +10.5%/mo
  trades 322 (9.8/month), won 51%, avg R +0.64 after costs; wins avg +2.30R
  at 1.5 %: average month +7.4%, worst -5.0%
  2026 starts both phases within 6 weeks 69%, within 2 months 98%
  2024-25 starts both phases within 3 months 47%
=== gold base x1.5
  phase 1 passed 100%: median 42 days, 25-75% 20-118
  both phases 100%: median 79 days, 25-75% 46-154
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 91 days, failed 0%
    starts 2025: both phases 100%, median 109 days, failed 0%
    starts 2026: both phases 100%, median 34 days, failed 0%
  funded at 1 %: average month +5.5%, median +5.0%, worst -3.8%, best +27.8%, losing months 9 of 33
  by year: 2024 +2.5%/mo  2025 +4.6%/mo  2026 +10.7%/mo
  trades 322 (9.8/month), won 51%, avg R +0.64 after costs; wins avg +2.30R
  at 1.5 %: average month +7.7%, worst -5.3%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 46%
=== gold stack x2
  phase 1 passed 100%: median 34 days, 25-75% 19-64
  both phases 100%: median 70 days, 25-75% 41-116
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 104 days, failed 0%
    starts 2025: both phases 100%, median 73 days, failed 0%
    starts 2026: both phases 98%, median 36 days, failed 0%
  funded at 1 %: average month +6.3%, median +3.2%, worst -2.9%, best +29.9%, losing months 9 of 33
  by year: 2024 +3.4%/mo  2025 +6.5%/mo  2026 +10.0%/mo
  trades 290 (8.8/month), won 51%, avg R +0.75 after costs; wins avg +2.47R
  at 1.5 %: average month +8.8%, worst -3.4%
  2026 starts both phases within 6 weeks 62%, within 2 months 88%
  2024-25 starts both phases within 3 months 56%
=== gold stack x1
  phase 1 passed 100%: median 40 days, 25-75% 20-68
  both phases 100%: median 70 days, 25-75% 41-108
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 101 days, failed 0%
    starts 2025: both phases 100%, median 71 days, failed 0%
    starts 2026: both phases 98%, median 37 days, failed 0%
  funded at 1 %: average month +5.7%, median +3.1%, worst -2.9%, best +29.9%, losing months 7 of 33
  by year: 2024 +2.6%/mo  2025 +5.8%/mo  2026 +9.7%/mo
  trades 290 (8.8/month), won 51%, avg R +0.75 after costs; wins avg +2.47R
  at 1.5 %: average month +8.1%, worst -3.4%
  2026 starts both phases within 6 weeks 62%, within 2 months 88%
  2024-25 starts both phases within 3 months 58%
=== gold ban x2
  phase 1 passed 100%: median 35 days, 25-75% 20-90
  both phases 100%: median 79 days, 25-75% 43-148
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 86 days, failed 0%
    starts 2025: both phases 100%, median 113 days, failed 0%
    starts 2026: both phases 100%, median 38 days, failed 0%
  funded at 1 %: average month +6.3%, median +5.0%, worst -4.2%, best +28.9%, losing months 8 of 33
  by year: 2024 +3.7%/mo  2025 +5.1%/mo  2026 +11.3%/mo
  trades 303 (9.2/month), won 53%, avg R +0.72 after costs; wins avg +2.32R
  at 1.5 %: average month +8.7%, worst -5.6%
  2026 starts both phases within 6 weeks 66%, within 2 months 98%
  2024-25 starts both phases within 3 months 45%
=== gold ban x1
  phase 1 passed 100%: median 41 days, 25-75% 20-78
  both phases 100%: median 73 days, 25-75% 43-145
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 91 days, failed 0%
    starts 2025: both phases 100%, median 90 days, failed 0%
    starts 2026: both phases 100%, median 38 days, failed 0%
  funded at 1 %: average month +5.7%, median +4.3%, worst -2.9%, best +28.9%, losing months 8 of 33
  by year: 2024 +3.0%/mo  2025 +4.7%/mo  2026 +10.8%/mo
  trades 303 (9.2/month), won 53%, avg R +0.72 after costs; wins avg +2.32R
  at 1.5 %: average month +8.1%, worst -5.0%
  2026 starts both phases within 6 weeks 64%, within 2 months 98%
  2024-25 starts both phases within 3 months 51%
```
