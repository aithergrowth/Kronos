# Risk and money management: what the four ledgers support (14 October 2026)

Angle: the risk model (base stake, multipliers, drawdown ladder, open-risk caps, equity-curve rules, phase stakes),
judged on how fast and how safely the FTMO 2-Step 10k passes. Read-only on the repository; everything below is
computed from the research ledgers in the scratchpad. The earlier pass of this angle (`research/part_a_kelly.py` ..
`part_g_final.py`, logs `a.log` .. `g.log`) ran out of budget before its write-up; every number from it that is
used here was re-run (`risk_verify2.py`: identical rows) and four things were added that it lacked: the multipliers
tested one at a time on halves and out of sample, the guard's refusals per scheme, a month-block bootstrap of the
whole 2-Step replay with the guard on, and the cushion rule rewritten as a plain config ladder (`risk_verify1.py`,
`risk_verify3.py`, `risk_verify4.py`, `risk_verify5.py`; outputs `risk_verify*.out`).

## 0. Where we stand, in one paragraph

The live model is: 1.5 % of equity a trade, a 4H zone on EURUSD, gold and NAS100 at twice that, BTC at half,
EURUSD's 1D+1H pair at half, a trade with the month at 50/50 at half, the ladder 1.0 % from -3 % and 0.5 % from -6 %
under the start, two open on the account, the guard's worst-case day check at 4 % and floor at 9.5 % of the start.
On the 2024-2026 ledgers (0.10R costs) that model is funded from every start, never breaks an FTMO limit, reaches
+10 % from a 2026 start in a median of 19 days (34 days to funded, 97 % within six weeks) and from a 2024-25 start
in a median of 56 days (113 to funded, 42 % within three months); on 1,000 resampled 24-month paths it is funded
in 98 % (60 % within 90 days, dead at the guard's floor 2 %); on 2017-2023, where the edge is gone, 11 % (none
failed, 89 % stall at the floor). With every trade 0.15R worse than the backtest it still fails nothing but stalls
19 % of the 2024-25 starts; with the winners halved it stalls 55 %. The base stake is right: 1.5 % sits at the knee
of speed against stalls (section 3), and the Kelly fraction (22 % in sample, 0 % out of sample) says nothing that
should move it. Three things in the model cost time without buying safety, all of them the same mechanism, the
double stake on a 4H zone: a 4H loss is -3.3 % with costs, which (a) is the only kind of day at -3 % or worse the
replay has (6 of 247 days), (b) lands exactly on the ladder's first step at -3 %, so one loss cuts the base to 1.0 %
for the rest of the drawdown, and (c) makes the worst-case check refuse the next trade that day (7 refusals, +4.8R).
A 4H multiplier of 1.5 removes all three (0 days at -3 %, 2 refusals), and a finer ladder that starts later and ends
lower (-4 % -> 1.25 ... -8 % -> 0.25, the cushion rule as config) keeps the account off the guard's floor when the
edge is thinner. Together, on the 2024-25 starts: funded within three months 54-57 % against 42 %, within six 81-82 %
against 68 %, median 66-70 days against 84; the 2026 starts +3 points; 2017-2023 unchanged; at 0.25R costs the stall
share 10 % against 19 %, with the winners halved 41 % against 55 %. On the resampled paths the gain is smaller but
never reverses: funded 99 % against 98 %, within 90 days 62 % against 60 %, dead 1.1 % against 2.1 %, and under the
two stresses dead 9.0 % against 12.0 % and 44 % against 50 %. Everything else in the brief (Kelly, a cap on
correlated open risk, stakes by grade, losing-streak and moving-average rules, phase-2 stakes, protection near the
target) is measured below; none of it beats that, and most of it is already done by the guard.

## 1. Method

- Ledgers: `aca/eutwo_EURUSD.csv`, `aca/base_XAUUSD.csv`, `aca/rr08_NAS100.csv`, `aca/base_BTCUSD.csv` (2024-01 ..
  2026-09, 1 % units, guard off: 322 trades) and the `oos_*` ledgers (2017-06 .. 2023-12, BTC 2020-06 .. 2023: 698
  trades). R after a flat 0.10R a trade for costs; the stresses use 0.25R, and the winners halved (the edge a third
  smaller).
- Account replay (`research/risk_model_lib.py`, the same semantics as `aca/challenge_sim.py`): trades first come,
  first served under two open slots; the stake = base % of the initial balance x the trade's multiplier; the guard
  refuses a trade whose worst case (every open stop and the new one) would take the day under -4 % of the start or
  the balance under -9.5 %; FTMO's own rules on closed trades: -5 % day, -10 % static, phase 1 +10 %, phase 2 +5 %,
  each with at least 4 trading days. Starts: every weekday 2024-01-02 .. 2026-06-30 (650) in sample, every 3rd
  weekday 2017-02 .. 2023-06 out of sample. "Dead" = unfinished at the guard's floor (under -9.1 % when the data
  ends), which for Max is the same as failed: the account is reset. The replay sizes on the initial balance; the live
  bot sizes on the broker's equity (`live.py`: `equity = self.broker.equity()`), which the replay also ran ("sized on
  the running balance": no difference, section 6).
- Bootstrap (`risk_verify1.py` section 4, `risk_verify5.py`): 1,000 paths, each 24 calendar months drawn with
  replacement from the 33 in-sample months (a month's trades stay together, re-dated to a synthetic calendar), the
  2-Step from day 1 of the path with the guard on; 600 paths for the stresses. This answers "how much of a ranking
  is the one historical order of the months".
- Kelly: f* = the fraction of the account risked per 1R that maximises E[log(1 + f R)] over the ledger's R, by grid;
  half-Kelly = f*/2; bootstrap percentiles from 400 resamples.

## 2. The R distribution and Kelly

| Market | Period | n | won | mean R | avg win / loss | PF | Kelly f* | half | bootstrap p10 / p50 / p90 | 1.5 % as a share of f* | growth at 1.5 % as a share of the optimum |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 2024-26 | 47 | 47 % | +0.84 | +3.00 / -1.06 | 2.49 | 24.5 % | 12.2 % | 12 / 24 / 36 % | 0.06 | 0.13 |
| XAUUSD | 2024-26 | 143 | 49 % | +0.50 | +2.14 / -1.07 | 1.92 | 19.5 % | 9.8 % | 12 / 20 / 26 % | 0.08 | 0.16 |
| NAS100 | 2024-26 | 43 | 47 % | +0.77 | +2.91 / -1.10 | 2.30 | 22.0 % | 11.0 % | 10 / 22 / 35 % | 0.07 | 0.15 |
| BTCUSD | 2024-26 | 89 | 58 % | +0.69 | +1.97 / -1.10 | 2.52 | 23.2 % | 11.6 % | 13 / 24 / 34 % | 0.06 | 0.16 |
| **all four** | 2024-26 | 322 | 51 % | +0.64 | +2.30 / -1.08 | 2.21 | **21.8 %** | **10.9 %** | 17 / 22 / 27 % | 0.07 | 0.15 |
| all four, live weights | 2024-26 | 322 | | +0.59 (w x R) | | | 22.2 % | 11.1 % | 18 / 23 / 27 % | | |
| EURUSD | 2017-23 | 97 | 26 % | -0.01 | +2.96 / -1.04 | 0.98 | 0 | 0 | 0 / 0 / 6 % | | |
| XAUUSD | 2017-23 | 371 | 30 % | -0.17 | +1.92 / -1.05 | 0.77 | 0 | 0 | 0 / 0 / 0 | | |
| NAS100 | 2017-23 | 100 | 32 % | +0.29 | +3.19 / -1.08 | 1.39 | 6.0 % | 3.0 % | 0 / 6 / 14 % | 0.25 | 0.46 |
| BTCUSD | 2020-23 | 130 | 33 % | -0.32 | +1.23 / -1.09 | 0.56 | 0 | 0 | 0 / 0 / 0 | | |
| all four | 2017-23 | 698 | 30 % | -0.11 | +2.10 / -1.06 | 0.85 | 0 | 0 | 0 / 0 / 0 | | |

By year in sample: 2024 Kelly 9.8 % (129 trades, +0.24R), 2025 21.8 % (+0.56R), 2026 36.8 % (+1.34R).

Reading:

- In sample every market's growth-optimal fraction is about a fifth of the account per R, and the four agree within
  their bootstrap intervals (p10 10-13 %): no market earns a different base stake from the others on the recent
  years, and 1.5 % is 6-8 % of Kelly, at which the growth rate is 13-16 % of the optimum. Out of sample the Kelly
  fraction is zero for three markets and 6 % for NAS100: the R distribution that justifies any stake above a minimum
  is the recent one. A fixed fraction chosen on Kelly (even a tenth of it) is therefore not a candidate: the
  in-sample f* is a 2024-2026 number, and the account's constraint is not growth.
- The constraint is the barriers. FTMO's -5 % day and -10 % static floor, with a +10 % then +5 % target, make the
  challenge a first-passage problem: with a positive edge P(target before floor) rises as the stake falls and the
  time to the target grows as 1/stake, so the stake trades P(pass) against time and the right objective is "funded
  within N months, not stalled" (section 3), not E[log]. The worst single trade after costs is -1.10R in sample (no
  stop was gapped through) and -1.49R out of sample; at 3 % a trade (a 4H zone at x2) a -1.67R print is a -5 % day.
  The ledgers hold none; the price history does (`prop_firm.md` 3.5: a wrong-side weekend gap of 1.67 median 4H
  stops follows 30 % of NAS100 weekends, 12.5 % of EURUSD's, 7.5 % of gold's).

## 3. Optimal fixed fraction for the challenge: the base sweep

Live weights and the ladder scaled with the base (2/3 and 1/3 of the base at -3 % and -6 %). Historical starts
(`a.log` A3; the 1.25 / 1.5 / 2.0 rows re-run in `risk_verify2.out`) and the month-block bootstrap
(`risk_verify1.out` section 4):

| Base | 2026 starts funded within 6 wk / 2 mo | 2024-25 starts within 3 / 6 mo | stalled at the floor | median days (all starts) | worst month | bootstrap: funded / within 90 d / dead / median days |
|---|---|---|---|---|---|---|
| 0.5 % | 5 / 25 % | 10 / 54 % | 0 % | 140 | -2.0 % | |
| 0.75 % | 19 / 61 % | 28 / 62 % | 0 % | 116 | -3.0 % | |
| 1.0 % | 46 / 86 % | 40 / 70 % | 0 % | 89 | -4.5 % | 100 % / 49 % / 0.2 % / 92 |
| 1.25 % | 57 / 98 % | 42 / 72 % | 0 % | 84 | -5.1 % | 99 % / 56 % / 1.2 % / 79 |
| **1.5 % (live)** | **71 / 98 %** | **42 / 68 %** | **0 %** | **84** | **-5.6 %** | **98 % / 60 % / 2.1 % / 72** |
| 1.75 % | 72 / 98 % | 44 / 66 % | 12 % | 73 | -6.5 % | 94 % / 60 % / 5.5 % / 67 |
| 2.0 % | 81 / 99 % | 51 / 78 % | 18 % | 69 | -9.1 % | 91 % / 54 % / 8.8 % / 76 |
| 2.5 % | 84 / 99 % | 47 / 69 % | 20 % | 65 | -9.6 % | 83 % / 57 % / 16.9 % / 62 |
| 3.0 % | 84 / 98 % | 55 / 64 % | 28 % | 48 | -8.8 % | |
| 1.5 % without the ladder | 71 / 98 % | 46 / 79 % | 5 % | 70 | -5.9 % | 92 % / 63 % / 8.2 % / 62 |

Reading: speed saturates at 1.5 % (bootstrap: funded within 90 days 49 / 56 / 60 / 60 / 54 / 57 % from 1.0 to
2.5 %) while the stall share is monotone (0.2 / 1.2 / 2.1 / 5.5 / 8.8 / 16.9 %); from 1.75 % up the ladder's cuts
and the guard's refusals eat the speed the larger stake was meant to buy, and on the historical path 2.0 % touches
-10.7 % from the start in early 2024 (an FTMO fail). Below 1.5 % the 2026 starts lose 14-25 points of six-week
passes for no stall reduction that matters (2.1 % -> 1.2 %). 1.5 % is the knee; the day-block bootstrap of the
earlier pass without the guard (`a.log` A4) puts the same knee at 1.5-1.75 % (fail 8 %) with a cliff at 2.5 %
(27 %). With the winners halved no base passes within two months from more than 5 % of the 2026 starts (1.0 %: 2 %,
1.5 %: 34 %, 2.0 %: 39 %) and 1.0 % is not safer (dead 45 % against 55 % and 75 %): a smaller base does not rescue a
thinner edge, it only slows it down.

## 4. Correlated open risk

What the ledgers say about two trades at once (`b.log` B1-B2, re-read):

- 38 overlapping pairs in 32 months (a trade opened while another ran), 34 of them in the same long/short direction;
  both lost in 21 % of the pairs against 24 % expected if independent (both won 32 %); the R correlation of the two
  legs is +0.15. Out of sample 79 pairs, both lost 44 % against 49 % expected. The daily P&L correlation between
  markets on days both traded is -0.52 (EURUSD x gold, 12 days), +0.37 (BTC x gold, 18 days), -0.28 (BTC x NAS100);
  by month the largest is EURUSD x gold -0.48. The markets' trades do not lose together more than chance.
- Combined open risk when two run: median 1.5 x the base, p90 2.65 x, max 3.0 x (a 4H zone at x2 beside a normal
  trade: 4.5 % of the start, which the worst-case check refuses).

Guard refusals and day clustering per scheme (`risk_verify3.py`: one account 2024-01 .. 2026-09, no reset, the day
check at 4 %, the total floor off so that only the day check counts):

| Scheme | Trades taken | Refused by the day check (their R) | Days at -3 % or worse | Worst day | Lowest point from the start |
|---|---|---|---|---|---|
| **live** (1.5 %, ladder, 4H x2) | 314 | 7 (+4.8R) | 6 (every one a single 4H loss) | -3.3 % | -8.5 % |
| live without the ladder | 314 | 7 (+4.8R) | 8 | -3.3 % | -7.2 % |
| 4H x1.5 | 318 | 2 (-2.2R) | 0 | -2.5 % | -9.0 % |
| 4H x1 | 320 | 0 | 1 | -3.3 % | -7.7 % |
| flat 1.5 % (no multipliers) | 318 | 2 (+0.9R) | 6 | -3.3 % | **-9.6 %** (the floor: the EURUSD run of early 2024 at the full stake) |
| 2.0 % base, 4H x2 | 296 | 25 (+33.5R) | 2 | -3.3 % | **-10.7 %** (an FTMO fail) |
| 1.25 % base, 4H x2 | 316 | 4 (+1.2R) | 0 | -2.8 % | -7.1 % |
| 4H x1.5 + cushion rule (section 6) | 318 | 2 (-2.2R) | 0 | -2.5 % | -7.3 % |
| 4H x2 + open-risk cap 2.5 % (second trade cut to fit) | 315 | 5 (+0.1R) | 0 | -2.8 % | -8.5 % |

So the "correlated open risk" problem is already solved by the worst-case check, and what it refuses at the live
stakes is the trade after a 4H loss (7 trades, +0.69R each on average): the cost of the double stake is paid twice,
once in the -3.3 % day and once in the trade the guard then refuses. An explicit cap on combined open risk
(`risk_verify2.out`: 2.5 % of the start, the second trade cut to fit, never below a quarter of its stake) changes the
2024-25 starts within six months from 68 % to 78 % and the 2026 starts within six weeks from 71 % to 74 %, with the
same median and worst month; bootstrap funded 98 % / within 90 days 60 % / dead 2.0 % against 98 / 60 / 2.1 (no
difference); at 0.25R costs the stall share is 17 % against 19 %. At 3.0 % nothing changes and skipping instead of
cutting is worse (2026 six weeks 61 %). A factor on a second trade in the same direction (x0.5, x0.75, skip) is
neutral to worse, and so is a cap on the stakes opened in one day (3 % or 4.5 %). One open trade on the account
instead of two: 2026 six weeks 58 % against 71 %, bootstrap within 90 days 57 % against 60 %. The cap is a real but
second-order gain, and it is what the 4H x1.5 setting gives for free (a 2.25 % trade beside a 1.5 % one is 3.75 %,
under the check).

## 5. Risk per trade by the setup's grade

Two tests. First, each live multiplier on its own against a flat stake, as R per unit of risk (sum of w x R over the
sum of w) on the two halves of the in-sample window and out of sample (`risk_verify1.out` section 2):

| Multiplier alone | H1 2024-01..2025-05 (175 trades) | H2 2025-06..2026-09 (147) | 2017-2023 (698) | Verdict |
|---|---|---|---|---|
| flat (reference) | +0.389R | +0.938R | -0.109R | |
| 4H zone x2 (not BTC) | +0.416R | +0.940R | -0.065R | better in H1 and OOS, equal in H2 |
| 4H zone x1.5 | +0.403R | +0.939R | -0.086R | the same, half the effect |
| BTC x0.5 | +0.416R | +0.865R | -0.088R | better in H1 and OOS, worse in H2 (BTC's 2026) |
| EURUSD 1D+1H x0.5 | +0.396R | +0.940R | -0.110R | a little better in H1, equal elsewhere |
| month at 50/50 x0.5 | +0.424R | +0.957R | -0.099R | **better in all three** |
| the four together (live) | +0.529R | +0.873R | -0.056R | better in H1 and OOS, worse in H2 |

Second, the grade cells themselves (mean R after costs, n, win rate): a 4H zone on EURUSD, gold or NAS100 +0.75R
(14) in H1, +0.97R (14) in H2, +0.42R (65) out of sample against the 1H zones +0.42R (100), +0.75R (105), -0.12R
(503); a trade with the month at 50/50 +0.10R (37), +0.49R (12), -0.18R (184) against the rest +0.47R, +0.98R,
-0.09R; EURUSD's 1D+1H pair +0.28R (20), +0.89R (14), -0.09R (65) against its other combinations +2.55R (2), +1.49R
(11), +0.15R (32); BTC +0.26R (61), +1.63R (28), -0.32R (130). The 4H cell per market is thin: EURUSD 10 trades in
sample (+0.43R) and 10 out (+3.12R, 80 % won), gold 13 (+1.08R) and 48 (-0.24R, 25 %), NAS100 5 (+1.15R) and 7
(+1.05R).

Through the replay (`risk_verify2.out`, `risk_verify4.out`, `c.log` C2, bootstrap `risk_verify1.out`):

| Weights (1.5 %, live ladder unless said) | 2026 within 6 wk | 2024-25 within 3 / 6 mo | dead | median | worst month | 2017-23 | bootstrap funded / 90 d / dead / median |
|---|---|---|---|---|---|---|---|
| **live** (4H x2, 1D+1H x0.5, 50/50 x0.5, BTC x0.5) | 71 % | 42 / 68 % | 0 % | 84 | -5.6 % | 11 % | 98 / 60 / 2.1 / 72 |
| flat 1.5 %, no multipliers | 78 % | 53 / 78 % | 4 % | 67 | -5.3 % | 13 % | 95 / 62 / 4.8 / 68 |
| 4H x1.5 | 74 % | 46 / 78 % | 0 % | 77 | -5.3 % | 11 % | 98 / 60 / 2.0 / 71 |
| 4H x1 | 70 % | 52 / 78 % | 0 % | 76 | -5.0 % | 11 % | 99 / 57 / 0.9 / 76 |
| 4H x3 | 61 % | 45 / 78 % | 11 % | 74 | -7.5 % | | |
| 4H x1.5 on EURUSD and NAS100, gold's 4H x1 | 73 % | 52 / 77 % | 0 % | 74 | -5.0 % | 11 % | |
| month 50/50 x1 (no halving) | 78 % | 41 / 68 % | 4 % | 76 | -6.3 % | 12 % | |
| EURUSD 1D+1H x1 | 71 % | 44 / 69 % | 2 % | 76 | -5.6 % | | |
| BTC x1 | 71 % | 45 / 72 % | 0 % | 81 | -5.6 % | 11 % | |
| BTC x0.25 | 66 % | 39 / 68 % | 1 % | 85 | -5.6 % | | |
| all five timeframes aligned x0.5 | 69 % | 39 / 65 % | 0 % | 90 | -4.5 % | 12 % | |
| NAS100 x1.5 | 74 % | 42 / 73 % | 4 % | 78 | -5.6 % | 14 % | |
| gold x1.25 / x0.75 | 81 / 59 % | 45 / 66 %, 44 / 75 % | 9 / 0 % | 67 / 83 | -6.8 / -4.6 % | - / 11 % | |

Reading: per unit of risk the multipliers point the right way, the month-at-50/50 half most robustly (it is the one
that holds in both halves and out of sample, and without it a flat 1.5 % account touches -9.6 % in early 2024: the
EURUSD run of eleven losses with the month at 50/50), the 4H double stake on the pooled cell (+0.86R in sample,
+0.42R out of sample against +0.59R / -0.12R for the 1H zones). But the account replay prefers a flat stake to the
live weights on the historical path (2024-25 within three months 53 % against 42 %), and the reason is not the grade
information, it is the size: x2 on a 1.5 % base is 3 % a trade, the one stake in the model that makes a -3 % day,
trips the ladder's first step and the day check. Between x1 (52 %, the slowest phase 1: median 48 days against 40)
and x2 (42 %, 40 days), x1.5 keeps the speed of x2 with the safety of x1 (46 %, 37 days; six months 78 % against
68 %; bootstrap +10 % in a median of 28 days against 34). Gold's 4H cell is the one that is negative out of sample;
gold at x1 with EURUSD and NAS100 at x1.5 is a wash against x1.5 everywhere (52 / 77 % against 46 / 78 %, the same
stress numbers) and keeps three profiles different for 13 trades of evidence: not worth it. A Kelly-proportional
weight per grade cell (`c.log` C1: f* per cell 4H 26 %, 1H 21 %, month decided 25 %, month 50/50 6 %, by combination
9-45 %) is an in-sample fit on 5-50 trades a cell whose ranking does not hold out of sample (the best in-sample
combination 1M+1D+1H, +1.38R on 37 trades, is +0.01R on 90 out of sample); all five timeframes aligned at x0.5 is
slower. Per-market stakes from Kelly: the four in-sample f* agree (19-25 %); out of sample only NAS100's is
positive, and NAS100 x1.5 is a wash with a longer tail. BTC at x1 is +3 points of six-month passes for a market
whose candles the research directory anchors differently from the FTMO terminal (`BACKLOG_hand.md` A1: +70.6R
becomes +33.3R on New-York-anchored candles): the half stays until that is settled.

## 6. Equity-curve rules: the ladder, streaks, moving averages, a cushion rule

Does the account's recent state predict the next trade? (`d.log` D1, in sample: 322 trades, 51 % won, +0.64R)

| State before the trade | n | won | mean R | Out of sample (698, 30 %, -0.11R) |
|---|---|---|---|---|
| after 1 loss in a row | 162 | 56 % | +0.83R | 483, 28 %, -0.14R |
| after 2 or more | 69 | 52 % | +0.59R | 349, 29 %, -0.13R |
| after 3 or more | 34 | 50 % | +0.61R | 246, 29 %, -0.15R |
| after a win | 160 | 46 % | +0.45R | 215, 34 %, -0.04R |
| closed balance under its 10-trade mean | 64 | 48 % | +0.53R | 415, 30 %, -0.06R |
| at or above it | 248 | 52 % | +0.70R | 273, 29 %, -0.19R |
| last 30 days under -3R | 17 | 59 % | +1.01R | 215, 30 %, -0.00R |

Nothing in the account's past picks the next loser (the README of 8 October found the same for pauses). The rules
through the replay (1.5 %, live weights unless said; `risk_verify2.out`, `risk_verify4.out`, `d.log` D2):

| Rule | 2026 within 6 wk / 2 mo | 2024-25 within 3 / 6 mo | dead | median days | worst month | 2017-23 | bootstrap funded / 90 d / dead / median |
|---|---|---|---|---|---|---|---|
| **live ladder** -3 % -> 1.0, -6 % -> 0.5 | 71 / 98 % | 42 / 68 % | 0 % | 84 | -5.6 % | 11 % | 98 / 60 / 2.1 / 72 |
| no ladder | 71 / 98 % | 46 / 79 % | 5 % | 70 | -5.9 % | 12 % | 92 / 63 / 8.2 / 62 |
| later ladder -5 % -> 0.75, -7 % -> 0.5 | 71 / 98 % | 45 / 79 % | 4 % | 75 | -5.9 % | 12 % | |
| later ladder -5 % -> 1.125, -7 % -> 0.75 | 71 / 98 % | 45 / 79 % | 5 % | 75 | -5.9 % | 12 % | 94 / 63 / 6.5 / 64 |
| earlier ladder -2 % -> 1.0, -4 % -> 0.5 | 62 / 98 % | 39 / 67 % | 0 % | 89 | -5.3 % | 12 % | |
| steeper -3 % -> 0.75, -6 % -> 0.5 | 64 / 98 % | 41 / 71 % | 0 % | 85 | -5.4 % | 11 % | |
| ladder + after 2 losses in a row x0.5 until a win | 58 / 82 % | 40 / 66 % | 0 % | 89 | -5.8 % | | |
| ladder + after 3 losses x0.5 | 71 / 98 % | 41 / 68 % | 0 % | 86 | -5.6 % | 11 % | |
| ladder + after 3 losses skip until a win | 71 / 98 % | 44 / 75 % | 0 % | 82 | -5.6 % | | |
| ladder + under the 10-trade mean of the balance x0.5 | 71 / 98 % | 41 / 67 % | 0 % | 86 | -5.6 % | 11 % | |
| ladder + under the 20-trade mean x0.5 | 71 / 98 % | 41 / 67 % | 0 % | 85 | -5.6 % | 11 % | |
| ladder + under the 10-trade mean skip | 71 / 98 % | 34 / 48 % | 22 % | 67 | -5.6 % | | |
| ladder, sized on the running balance (as the live bot) | 72 / 98 % | 42 / 68 % | 0 % | 84 | -5.6 % | 11 % | |
| cushion rule k = 0.25 capped at 1.5 % (4H x2) | 71 / 98 % | 44 / 74 % | 2 % | 79 | -6.3 % | 12 % | 97 / 63 / 2.9 / 68 |
| fine ladder -5:1.25 -6:1.0 -7:0.75 -8:0.5 -9:0.25 (4H x2) | 71 / 98 % | 45 / 76 % | 4 % | 76 | -5.9 % | 12 % | |
| **4H x1.5 + cushion rule k = 0.25 capped at 1.5 %** | 74 / 99 % | **57 / 83 %** | 0 % | 68 | -5.3 % | 11 % | 98 / 63 / 2.5 / 69 |
| **4H x1.5 + fine ladder -5:1.25 ... -9:0.25** (config only) | 74 / 99 % | 57 / 82 % | 2 % | 66 | -5.1 % | 11 % | 96 / 63 / 3.7 / 66 |
| **4H x1.5 + fine ladder -4:1.25 -5:1.0 -6:0.75 -7:0.5 -8:0.25** (config only) | 74 / 99 % | 54 / 81 % | 0 % | 70 | -5.5 % | 11 % | **99 / 62 / 1.1 / 70** |
| 4H x1.5 + later ladder -5 % -> 1.125, -7 % -> 0.75 | 74 / 99 % | 57 / 83 % | 3 % | 67 | -5.1 % | 11 % | 96 / 63 / 4.4 / 65 |

The ladder is a trade between speed and the stall: without it 5 % of the 2024-25 starts end at the guard's floor
(bootstrap 8 %; and the 2017-2023 replay, where the edge is gone, stalls 86-89 % of the starts whatever the rule),
with it none, for 14 days of median time. Its first step at -3 % is the problem, not the idea: one 4H loss (-3.3 %)
is enough to reach it. The cushion rule (CPPI: stake = k x (balance - the floor - open risk), capped at the base)
keeps 1.5 % down to -4 %, then 1.25 % at -5 %, 1.0 % at -6 %, 0.75 % at -7 %, 0.5 % at -8 %, 0.25 % at -9 %: later
than the ladder at the top, lower at the bottom, and it never lets one stake cross the floor. It needs no code: a
`drawdown_steps` ladder with those five rungs reproduces it to within 2 points (dead 2 % instead of 0 %, because the
plain ladder does not subtract the open risk from the cushion and does not go under 0.25 % at -9.5 %); one rung
earlier (-4 % -> 1.25 ... -8 % -> 0.25) gives back the 0 % and is the robust one under stress (section 8). With the
4H zones at x1.5 these are the best rows of the whole study on the 2024-25 starts and cost nothing on the 2026 starts
or out of sample; on the bootstrap the gain is 3 points of 90-day passes and 3 days of median time, within the
noise, with the stall share up by half a point: the large historical gap is partly the one order of the months (the
losing run of early 2024 at the start of the window). The streak and moving-average rules do what D1 predicts:
nothing, or harm (the skip rules stall accounts). Sizing on the running balance (compounding, as the live bot does)
changes nothing measurable; it only makes the guard's and the ladder's arithmetic approximate.

## 7. Time to the target

Calendar days, historical starts (`risk_verify2.out`; p10 / p25 / p50 / p75 / p90):

| Model | Starts | +10 % | within 30 / 42 / 61 d | +5 % on its own | funded | within 90 / 180 d | trades to +10 % (median) |
|---|---|---|---|---|---|---|---|
| live | 2026 | 9 / 13 / 19 / 26 / 35 | 82 / 97 / 100 % | 7 / 11 / 16 / 19 / 27 | 24 / 28 / 34 / 45 / 54 | 100 / 100 % | 6 |
| live | 2024-25 | 14 / 25 / 56 / 150 / 210 | 32 / 41 / 53 % | 9 / 14 / 27 / 48 / 108 | 35 / 62 / 113 / 208 / 254 | 42 / 68 % | 15 |
| flat 1.5 % | 2026 | 8 / 12 / 18 / 23 / 28 | 93 / 99 / 100 % | 6 / 9 / 16 / 22 / 30 | 25 / 29 / 35 / 42 / 46 | 100 / 100 % | 6 |
| flat 1.5 % | 2024-25 | 13 / 24 / 49 / 86 / 191 | 30 / 42 / 63 % | 8 / 14 / 26 / 49 / 107 | 36 / 57 / 83 / 160 / 218 | 53 / 78 % | 14 |
| 4H x1.5 | 2026 | 9 / 13 / 19 / 26 / 35 | 82 / 97 / 100 % | 6 / 9 / 16 / 18 / 27 | 23 / 28 / 34 / 43 / 49 | 100 / 100 % | 6 |
| 4H x1.5 | 2024-25 | 14 / 25 / 49 / 126 / 216 | 32 / 44 / 59 % | 8 / 14 / 27 / 49 / 114 | 36 / 64 / 105 / 172 / 235 | 46 / 78 % | 14 |
| 4H x1 | 2024-25 | 16 / 34 / 56 / 117 / 211 | 22 / 32 / 56 % | 8 / 14 / 22 / 49 / 107 | 37 / 65 / 90 / 169 / 238 | 52 / 78 % | 18 |
| 4H x1.5 + cushion rule | 2026 | 9 / 13 / 19 / 26 / 35 | 82 / 97 / 100 % | 6 / 9 / 16 / 18 / 27 | 23 / 28 / 34 / 43 / 49 | 100 / 100 % | 6 |
| 4H x1.5 + cushion rule | 2024-25 | 14 / 25 / 48 / 102 / 207 | 32 / 45 / 60 % | 9 / 14 / 27 / 46 / 52 | 34 / 56 / 82 / 147 / 235 | 57 / 83 % | 14 |
| 1.25 % | 2026 | 9 / 13 / 20 / 27 / 35 | 81 / 96 / 100 % | 10 / 12 / 17 / 24 / 29 | 26 / 32 / 41 / 47 / 53 | 100 / 100 % | 6 |
| 1.25 % | 2024-25 | 15 / 29 / 55 / 120 / 210 | 27 / 39 / 55 % | 8 / 15 / 27 / 48 / 135 | 41 / 65 / 113 / 203 / 246 | 42 / 72 % | 15 |
| 2.0 % (18 % stall) | 2026 | 8 / 12 / 18 / 23 / 29 | 91 / 99 / 99 % | 6 / 10 / 16 / 22 / 28 | 25 / 29 / 35 / 41 / 47 | 100 / 100 % | 6 |
| 2.0 % (18 % stall) | 2024-25 | 14 / 26 / 49 / 67 / 119 | 26 / 36 / 55 % | 9 / 15 / 22 / 46 / 100 | 36 / 52 / 80 / 125 / 160 | 51 / 78 % | 13 |
| phase 2 at 2.0 % | 2026 | 9 / 13 / 19 / 26 / 35 | 82 / 97 / 100 % | 6 / 9 / 16 / 18 / 27 | 23 / 28 / 34 / 42 / 49 | 100 / 100 % | 6 |
| target_protect 4 % | 2026 | 9 / 13 / 20 / 28 / 35 | 78 / 96 / 100 % | 9 / 12 / 18 / 24 / 33 | 25 / 31 / 42 / 49 / 55 | | 8 |

Bootstrap (24-month paths from day 1, live weights): +10 % in a median of 34 days (live), 28 (4H x1.5 and the
cushion variants), 32 (flat), 46 (4H x1), 48 (1.0 %), 36 (1.25 %), 43 (2.0 %); funded p25 / p50 / p75: live
43 / 72 / 118, 4H x1.5 42 / 71 / 120, 4H x1.5 + cushion 38 / 69 / 114, flat 42 / 68 / 111, 1.25 % 49 / 79 / 129.

Reading: the phase-1 time is a property of the ledger more than of the stake (the median 2026 start needs 6 trades
and 18-20 days whatever the model; the 2024-25 starts 13-18 trades and 48-56 days); the stake model moves the
upper quartile (p75 of the 2024-25 starts to funded: live 208 days, 4H x1.5 172, with the cushion rule 147, flat
160): what the model buys is fewer long tails, not a faster typical pass. The 1.5 % base against 1.25 % is 10 days
of median on the 2026 starts (34 against 41 to funded) and the same on the 2024-25 starts.

## 8. Stresses: costs 0.25R and the winners halved

Historical starts (`risk_verify2.out`, `risk_verify4.out`); 2017-2023 with the winners halved funds 0 % under
every model and is left out:

| Model | 0.25R: 2026 within 6 wk | 2024-25 within 3 / 6 mo | dead | funded (all) | 2017-23 | winners halved: 2026 within 3 mo | 2024-25 within 6 mo | dead | funded (all) |
|---|---|---|---|---|---|---|---|---|---|
| **live** | 57 % | 38 / 59 % | 19 % | 85 % | 10 % | 69 % | 29 % | 55 % | 55 % |
| flat 1.5 % | 61 % | 38 / 62 % | 19 % | 85 % | 6 % | 56 % | 11 % | 73 % | 39 % |
| 4H x1.5 | 63 % | 37 / 65 % | **11 %** | 91 % | 10 % | 52 % | 26 % | 47 % | 60 % |
| 4H x1 | 61 % | 38 / 64 % | 6 % | 95 % | 10 % | 44 % | 20 % | 42 % | 63 % |
| 4H x1.5 + cushion rule k = 0.25 | 60 % | 39 / 67 % | 17 % | 86 % | 9 % | 65 % | 30 % | 46 % | 61 % |
| 4H x1.5 + fine ladder -5 ... -9 | 60 % | 38 / 68 % | 18 % | 85 % | 9 % | 65 % | 30 % | 52 % | 57 % |
| **4H x1.5 + fine ladder -4 ... -8** | 60 % | 38 / 66 % | **10 %** | 92 % | 9 % | 60 % | 27 % | **41 %** | 63 % |
| 4H x1.5 + later ladder -5 / -7 | 60 % | 41 / 70 % | 21 % | 83 % | 9 % | 65 % | 30 % | 51 % | 57 % |
| 4H x2 + cushion rule | 58 % | 40 / 60 % | 24 % | 81 % | 9 % | 78 % | 37 % | 56 % | 55 % |
| open-risk cap 2.5 % (4H x2) | 57 % | 39 / 65 % | 17 % | 86 % | 10 % | 67 % | 28 % | 47 % | 62 % |
| 1.25 % base | 50 % | 37 / 65 % | 8 % | 94 % | 9 % | 42 % | 24 % | 46 % | 60 % |
| gold's 4H x1, EURUSD/NAS100 x1.5 | 61 % | 38 / 66 % | 10 % | 92 % | 10 % | 52 % | 25 % | 42 % | 63 % |

Bootstrap under the same stresses (600 paths; `risk_verify1.out`, `risk_verify5.out`):

| Model | as backtested: funded / within 90 d / dead / median days | 0.25R costs: funded / 90 d / dead / median | winners halved: funded / within 180 d / dead / median |
|---|---|---|---|
| **live** | 98 / 60 / 2.1 / 72 | 88 / 49 / 12.0 / 82 | 47 / 26 / 49.8 / 169 |
| flat 1.5 % | 95 / 62 / 4.8 / 68 | 82 / 49 / 18.5 / 74 | 34 / 22 / 65.3 / 146 |
| 4H x1.5 | 98 / 60 / 2.0 / 71 | 91 / 48 / 8.8 / 86 | 51 / 26 / 45.3 / 178 |
| 4H x1 | 99 / 57 / 0.9 / 76 | 93 / 46 / 7.2 / 91 | 46 / 23 / 49.2 / 181 |
| 4H x1.5 + cushion rule k = 0.25 | 98 / 63 / 2.5 / 69 | 88 / 49 / 12.0 / 80 | 51 / 27 / 47.2 / 171 |
| 4H x1.5 + fine ladder -5 ... -9 | 96 / 63 / 3.7 / 66 | 85 / 50 / 15.2 / 77 | 51 / 27 / 48.7 / 172 |
| **4H x1.5 + fine ladder -4 ... -8** | **99 / 62 / 1.1 / 70** | **91 / 49 / 9.0 / 82** | **52 / 26 / 44.2 / 178** |
| 4H x1.5 + later ladder -5 / -7 | 96 / 63 / 4.4 / 65 | 83 / 50 / 17.2 / 75 | 52 / 28 / 47.7 / 172 |
| 2-week blocks instead of months: live | 98 / 63 / 2.3 / 71 | | |
| 2-week blocks: flat 1.5 % | 96 / 66 / 3.7 / 64 | | |
| 2-week blocks: 4H x1.5 + cushion rule | 98 / 67 / 1.7 / 68 | | |

Reading: 0.15R more cost a trade turns 0 % stalls into 10-24 %; the one lever that halves that share is the size of
the largest stake (4H x1.5 or x1: 6-11 %) and, with it, a ladder that does not hold 1.5 % too long under the start
(the fine ladder from -4 %: 10 %; from -5 %: 18 %; the "later" ladders 21-24 %). With the winners halved nothing
passes a 2026 start within two months from more than a third of the starts; the models that stall least are again
the ones with the smallest largest stake (4H x1 42 %, fine ladder from -4 % 41 %, 4H x1.5 47 %, live 55 %, flat
73 %). The model to run is therefore the one that is fastest when the edge is as backtested and stalls least when it
is not: 4H x1.5 with the fine ladder from -4 %.

## 9. Candidates

1. **4H zones at 1.5 x the stake instead of 2 x** (config: `risk.zone_risk_multiplier: {4H: 1.5}` in
   `config/dorus_live.yaml`, `dorus_live_gold.yaml`, `dorus_live_nas100.yaml`; BTC has none). Rule: a trade on a 4H
   zone risks 1.5 x the stepped base (2.25 % at the start), every other multiplier as now. Evidence (sections 4-8):
   historical 2024-25 starts funded within 3 / 6 months 46 / 78 % against 42 / 68 %, median 77 days against 84, 2026
   six weeks 74 % against 71 %, worst month -5.3 % against -5.6 %, 2017-2023 11 % either way; the day check refuses 2
   trades instead of 7 and no day closes at -3 %; bootstrap the same (98 % funded, 60 % within 90 days, dead 2.0 %
   against 2.1 %) with +10 % in a median of 28 days against 34; at 0.25R costs the stall share 11 % against 19 %,
   with the winners halved 47 % against 55 %; per unit of risk the 4H cell keeps its edge in both halves and out of
   sample (+0.403 / +0.939 / -0.086R against flat +0.389 / +0.938 / -0.109R). Markets: EURUSD, XAUUSD, NAS100.
2. **The cushion ladder in place of the two-step ladder** (config: `risk.drawdown_steps: [[-4, 1.25], [-5, 1.0],
   [-6, 0.75], [-7, 0.5], [-8, 0.25]]` in all four profiles, with candidate 1). Rule: the base is 1.5 % until the
   balance is 4 % under the start, then 1.25 %, and 0.25 % less for every further 1 % down to 0.25 % from -8 %; the
   multipliers on top as now. It is the CPPI rule "stake = 0.25 x (balance - floor)" capped at 1.5 %, written as rungs.
   Evidence: with 4H x1.5, historical 2024-25 within 3 / 6 months 54 / 81 % against 42 / 68 %, median 70 days against
   84, dead 0 %, 2026 six weeks 74 % against 71 %, worst month -5.5 %, 2017-2023 11 %; at 0.25R costs dead 10 %
   against 19 % (funded 92 % against 85 %), with the winners halved dead 41 % against 55 % (funded 63 % against 55 %);
   bootstrap: funded 99 % against 98 %, within 90 days 62 % against 60 %, dead 1.1 % against 2.1 %, median 70 days
   against 72; at 0.25R costs dead 9.0 % against 12.0 %, with the winners halved 44 % against 50 %: never worse than
   the live model on any column. The rungs from -5 % (ending at -9 %) are 3 points faster on the historical path
   (57 / 82 %, 66 days) and worse under stress (dead 18 % / 52 % historical, 15 % / 49 % bootstrap): the -4 % version
   is the one. Markets: account-level (all
   four profiles carry the same risk block). The exact rule (open risk subtracted from the cushion, no 0.25 % floor)
   would be about 15 lines in `strategy/risk.py` `stepped_risk` (`risk.cushion_fraction`, `risk.cushion_floor_pct`)
   and buys 2 points of dead share over the rungs from -5 %, nothing over the rungs from -4 %: not needed.
3. **The base stays 1.5 %** (config, unchanged: `RISK=1.5` in `scripts/ftmo_local.bat`). Rule: 1.5 % of the start a
   trade before the multipliers and the ladder. Evidence (section 3): the bootstrap's share funded within 90 days is
   flat from 1.5 % up (60 / 60 / 54 / 57 % at 1.5 / 1.75 / 2.0 / 2.5 %) while the stall share rises 2.1 / 5.5 / 8.8 /
   16.9 %; on the historical path 2.0 % stalls 18 % of the 2024-25 starts and touches -10.7 % in early 2024; 1.25 %
   costs 14 points of six-week passes on the 2026 starts (57 % against 71 %) and 10 days of median time for a stall
   share of 1.2 % against 2.1 %; Kelly (22 % in sample, 0 % out of sample) gives no reason to move either way. The
   edge-halved stress shows a smaller base does not rescue a thinner edge (1.0 %: dead 45 %, two-month passes 2 %).
   Markets: account-level.
4. **Keep the three halving multipliers** (config, unchanged: `neutral_bias_risk_multiplier: {1M: 0.5}` in the four
   profiles, `combo_risk_multiplier`-equivalent 1D+1H half on EURUSD, `stake_multiplier: 0.5` on BTC). Rule: as now.
   Evidence (section 5): the month-at-50/50 half beats flat per unit of risk in both halves and out of sample
   (+0.424 / +0.957 / -0.099R against +0.389 / +0.938 / -0.109R); without it the flat account reaches the guard's floor
   in early 2024 and with the winners halved stalls 73 % against 55 %; BTC's half is better in H1 and out of sample,
   worse only in BTC's 2026, and BTC's research candles differ from the terminal's (A1 of the backlog); EURUSD's 1D+1H
   half is neutral to slightly positive and halves EURUSD's drawdown. Markets: EURUSD, XAUUSD, NAS100, BTCUSD.
5. **A cap on combined open risk, 2.5 % of the start, the second trade cut to fit** (needs code: `prop_firm.max_open_risk_pct:
   2.5` in the guard, next to the worst-case check: the new stake is reduced to the room left under the cap, and
   refused when the room is under a quarter of it). Rule as stated. Evidence (section 4): with the live x2 the 2024-25
   starts funded within six months 78 % against 68 % and the 2026 starts within six weeks 74 % against 71 % at the same
   median and worst month; bootstrap identical to live (98 / 60 / 2.0 %); at 0.25R costs dead 17 % against 19 %. It is
   the alternative to candidate 1 for keeping x2 on paper (the cap turns a 3 % 4H trade into 2.5 % and blocks a second
   trade beside it); with candidate 1 in place it adds nothing (identical rows). Markets: account-level.
6. **Phase 2 at the same base as phase 1** (config, unchanged: `RISK=1.5` through the verification, `TARGET=5`).
   Rule: no change of stake between the phases. Evidence (sections 6-7): phase 2 at 2.0 % is +7 points of six-week
   passes on the 2026 starts (78 % against 71 %) but stalls 2 % of the 2024-25 starts and 7.7 % of the bootstrap paths
   (against 2.1 %); phase 2 at 1.0 % funds 16 % instead of 11 % of the 2017-2023 starts (a thinner edge wants a smaller
   stake for +5 %) but loses 11 points on the 2026 starts (60 % against 71 %). Neither holds on both periods. Markets:
   account-level.
7. **`risk.target_protect_pct` stays off** (config, unchanged: `PROTECT` unset). Rule: no half stake near the target.
   Evidence (`e.log` E1-E2, bootstrap): half the base in the last 3 % is 57 % within 90 days against 60 % on the
   bootstrap with the same stall share (2.1 %), 2026 six weeks 67 % against 71 % (2 %), 52 % (4 %), and +5 % on its own
   takes 18 instead of 16 days at 4 %; no failure to prevent (0 % under every setting). Markets: account-level.
8. **Size on the initial balance, not on the equity** (needs code, small: `risk.size_basis: initial` read in
   `live.py` where `size_position` gets `equity`; the replay and the guard already work from `account_size`). Rule:
   the stake is `risk_pct` x the initial balance (x the multipliers and the ladder), not of the broker's equity with
   its open P&L. Evidence: the replay sized on the running balance is identical to the live rows (2026 six weeks 72 %
   against 71 %, everything else equal), so the measurable effect is nil; what it changes is that a floating +2R open
   trade no longer enlarges the next stake, the ladder's rungs and the guard's worst case become exact, and the
   forward record becomes comparable with the replay trade for trade. Lowest priority; a hygiene change for the
   next restart, not the challenge. Markets: account-level.

## 10. Not supported by the data

- A base stake from Kelly or half-Kelly (section 2): the in-sample f* (22 %, half 11 %) is a 2024-2026 number; out of
  sample it is 0 %; the challenge objective is first passage, not growth.
- A larger base: 1.75-2.0 % with the ladder scaled stalls 12-18 % of the historical starts and 5.5-8.8 % of the
  bootstrap paths and is no faster within 90 days (section 3). A smaller base (1.0-1.25 %) is 14-25 points slower on
  the 2026 starts for 1 point of stall share.
- Per-market stakes from the R distribution, grade weights beyond the three in place, gold's 4H at x1, all-five-aligned
  at half, a Kelly-proportional weight per grade (section 5).
- Losing-streak and moving-average rules (section 6), one open trade on the account, a factor on same-direction
  trades, a cap on the stakes opened in one day (section 4).
- Dropping the ladder: bootstrap dead 8.2 % against 2.1 % for 3 points of 90-day passes; the later two-step ladders
  (-5 / -7) stall 4-6.5 %.
- Half the stake near the target (candidate 7), a different phase-2 base (candidate 6).

## 11. Files

`research/risk_model.md` (this), `risk_model_lib.py` (replay library of the earlier pass, read and reused),
`risk_verify1.py` / `.out` (Kelly, the multipliers one at a time, refusals, the month-block bootstrap and its
stresses), `risk_verify2.py` / `.out` (the historical-start replays, both periods, time to target, stresses),
`risk_verify3.py` (refusals with the floor off), `risk_verify4.py` / `.out` (the fine ladders and the per-market 4H
multipliers, both periods, stresses), `risk_verify5.py` / `.out` (bootstrap of the fine ladders), the earlier pass's
`part_a_kelly.py` .. `part_g_final.py` and `a.log` .. `g.log`.
