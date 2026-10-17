# Liquidity map: what else a chart could show, and whether it carries information (14 October 2026)

Angle: the trader wants to "see everything in such a chart". Eight candidate elements were rebuilt for every trade of
the eight research ledgers as they stood at the close of the confirmation candle (the moment the Telegram chart is
drawn), and measured against the outcome in both periods. Verdict in one line: **the elements explain the trade and are
worth drawing; none of them carries a four-market rule that holds in both periods.** The apparent rules ("the target
before yesterday's high wins more often") are planned-R:R effects: a target that sits before a level is a nearer target.
One market-specific candidate survives the scan (EURUSD: a sweep too small for the 8-pip minimum), neutral in sample,
+8.9R out of sample, a third of EURUSD's trades; it needs a backtest.

Scripts: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/liquidity_map/measure.py`
(the features), `measure_extra.py` (the engine's own liquidity levels, the raw levels, the chart-picture flags),
`tables.py` / `tables_extra.py` (every bucket, four markets and pooled: `tables.md`, `tables_extra.md`),
`followup.py` (the filter scan, the R:R control, the widened stops, the in-picture shares, the per-market check:
`followup.md`). Features: `liquidity_map/features.csv` (1020 rows, 103 columns). Runtime 50 s + 26 s; no backtest was run.

## 1. Data and method

- Ledgers: 2024-01..2026-09 (IS) and 2017..2023 (OOS; BTC 2020-06..2023) of the four live profiles: EURUSD 47 / 97
  trades, XAUUSD 143 / 371, NAS100 43 / 100, BTCUSD 89 / 130 (322 IS, 698 OOS). R is the ledger's raw R (no 0.10R cost);
  base: IS 51 % won, +0.74R a trade; OOS 30 %, -0.01R.
- Every element is computed from candles closed at or before the confirmation close (`confirmed_close_at`), the moment
  the setup chart is drawn, so nothing uses later data. Zone-timeframe objects use the engine's own code
  (`find_swings` 2/2, `analyze_structure`, `map_pois`) on the profile's structure parameters.
- "At the level" = within 0.1 ATR14 of the zone timeframe (the task's tolerance; a 0.25 ATR variant is given for pools).
  A level on the target side is classed `behind_entry` (the entry already lies beyond it), `before_target` (between
  entry and target), `at_target`, `beyond_target` (the target sits before it, within one reward distance), else `none`.
  A level on the stop side: `between_entry_stop` (the stop sits beyond it: the sweep took it), `just_beyond_stop`
  (within 0.1 ATR beyond the stop), `far_beyond_stop`, `swept_already` (the entry itself lies beyond it).
- The both-period test: the bucket's R a trade minus the rest's, pooled over the markets, the same sign in both periods
  with at least 20 trades in each; then the same within planned-R:R bands (<1.5, 1.5-2.5, 2.5-4, >4), because every
  "target before the level" bucket is also a "nearer target" bucket; then per market (`followup.md` E).
- The chart picture: the last 120 candles of the confirmation timeframe (5m: 10 hours; 15m: 30 hours), the price axis
  widened to hold the stop and the target, 6 % padding (`render_chart`).

## 2. Results per element (pooled over the four markets; cell = trades / won % / R a trade; IS then OOS)

### 2.1 Equal highs/lows (pools) on the zone timeframe

| nearest untaken pool on the target side | 0.1 ATR IS | 0.1 ATR OOS | 0.25 ATR IS | 0.25 ATR OOS | engine levels (touches >= 2) IS | OOS |
|---|---|---|---|---|---|---|
| none within one reward past the target | 302 / 51 % / +0.73 | 645 / 30 % / -0.01 | 275 / 51 % / +0.70 | 588 / 30 % / -0.01 | 296 / 51 % / +0.74 | 630 / 30 % / +0.00 |
| before_target (a pool in the path) | 7 / 57 % / +1.04 | 11 / 45 % / +0.61 | 13 / 62 % / +0.98 | 24 / 46 % / +0.45 | 10 / 60 % / +1.11 | 16 / 44 % / +0.43 |
| at_target | 5 / 60 % / +1.80 | 18 / 39 % / +0.08 | 18 / 44 % / +0.97 | 43 / 35 % / -0.07 | 4 / 25 % / +0.11 | 19 / 32 % / -0.23 |
| beyond_target (the target sits before the pool) | 8 / 25 % / +0.00 | 24 / 17 % / -0.36 | 16 / 56 % / +1.00 | 43 / 21 % / -0.22 | 12 / 42 % / +0.55 | 33 / 15 % / -0.36 |

Equal highs/lows are rare objects in our trade pictures: a pool within one reward of the trade exists in 6 % (0.1 ATR),
15-16 % (0.25 ATR) and 8-14 % (the engine's 0.03 % stacking) of the trades. A pool *in the path* is better than the
base in both periods in every definition (10-13 IS trades at 60 %, 16-24 OOS trades at 44-46 % against 30 %), but at
these counts that is a hint, not a rule. The target *before* a pool, the literature's favourite, is mixed: worse out of
sample in every definition (15-21 % won), in sample 25-56 %. A pool on the stop side just beyond the stop: 2 IS and 3
OOS trades, so the stop practically never sits in front of resting equal lows. **No rule. Draw the pools in the path
and the first one beyond the target.**

### 2.2 Resting swing liquidity on the zone timeframe (every untaken swing high/low, the engine's own levels)

| nearest resting level on the target side | fractal swings IS | OOS | engine `StructureAnalysis.levels` IS | OOS |
|---|---|---|---|---|
| none | 79 / 54 % / +0.56 | 169 / 34 % / -0.08 | 80 / 54 % / +0.54 | 169 / 33 % / -0.10 |
| before_target | 113 / 46 % / +0.93 | 274 / 27 % / -0.01 | 113 / 46 % / +0.93 | 274 / 27 % / +0.01 |
| at_target | 83 / 55 % / +0.83 | 157 / 31 % / +0.12 | 82 / 56 % / +0.85 | 154 / 31 % / +0.09 |
| beyond_target | 47 / 49 % / +0.43 | 98 / 33 % / -0.09 | 47 / 49 % / +0.43 | 101 / 33 % / -0.08 |

`at_target` is the one bucket of the whole study that is better in both periods *and* within the R:R bands (+0.10 /
+0.13 fractal, +0.16 / +0.10 engine). It does not survive the per-market check: NAS100 +1.38 / +0.95 (10 / 28 trades),
BTC +0.05 / +0.09 (36 / 44), gold -0.12 / +0.12, EURUSD -0.46 / -0.42 (13 / 27). By target kind it is inconsistent
too: an origin target on a swing IS +0.75 against +0.88, OOS +0.26 against +0.10; a previous-extreme target (BTC's
profile) IS +0.92 against +0.63, OOS -0.13 against -0.06. Swings in the path: the win rate falls with their number in
both periods (0: 54 % / 32 %; 1: 45 % / 26 %; 2: 46 % / 25 %) while R a trade does not (those targets are farther).
**No rule. Draw the resting levels between the entry and one reward past the target.**

### 2.3 The previous day's and week's high/low

| yesterday's extreme on the target side (PDH for a long) | IS | OOS | within R:R bands IS / OOS |
|---|---|---|---|
| behind_entry (the entry already beyond it) | 131 / 56 % / +0.75 | 262 / 30 % / -0.13 | +0.23 / -0.11 |
| before_target | 70 / 43 % / +0.44 | 179 / 34 % / +0.21 | -0.15 / +0.30 |
| at_target | 79 / 44 % / +1.11 | 183 / 24 % / +0.01 | +0.38 / -0.21 |
| beyond_target (the target sits before it) | 42 / 60 % / +0.50 | 74 / 35 % / -0.16 | +0.16 / -0.05 |

Raw, "the target on yesterday's extreme" is better in both periods (+0.49 / +0.02 against the rest) and "the target
before it" worse (-0.27 / -0.17); within the R:R bands both turn (the at_target trades carry a planned R:R of 3.5 / 3.2
against 2.4 / 2.1). The literature's T1 (yesterday's extreme as the target) was already measured in
`smc_literature.md` 2.5: worse than the origin target in both periods on three markets. Yesterday's extreme more than 4R
ahead: IS 49 trades, 53 %, +1.88R a trade (the trend days); OOS 81 trades, 19 %, +0.09: in-sample only. On the stop
side yesterday's low is almost never involved: the sweep took it in 6 / 15 trades, it sits just beyond the stop in 7 /
5. Last week's extreme: every bucket's sign turns between the periods (table 3d/3e). **No rule. Draw yesterday's high
and low (in the picture 88-92 % on the target side); last week's only when it is in the picture (40 %).**

### 2.4 The Asia range (00:00-08:00 Amsterdam) of the signal day

| | IS | OOS |
|---|---|---|
| entry ahead of the Asia extreme on its side (a long above the Asia high) | 128 / 52 % / +0.70 | 315 / 29 % / +0.01 |
| entry inside the range | 184 / 51 % / +0.67 | 364 / 31 % / -0.01 |
| entry behind (a long below the Asia low) | 10 / 50 % / +2.63 | 19 / 21 % / -0.40 |
| the Asia extreme between entry and target | 125 / 45 % / +0.89 | 262 / 30 % / +0.07 |
| the target at or before the Asia extreme | 69 / 61 % / +0.54 | 120 / 33 % / -0.23 |
| the stop beyond the Asia extreme (the sweep took it) | 33 / 48 % / +0.49 | 108 / 29 % / -0.22 |

Pooled, the entry's position sorts nothing. Per market it is EURUSD's story and the EURUSD angle already has the rule
(`head.md` 3, `eurusd_tables.md`: no entry inside the Asia range; the shorts): on these ledgers EURUSD inside the
range IS 20 trades, 25 %, +0.40 against ahead 25 trades, 64 %, +1.36; OOS 54, 24 %, -0.08 against 40, 30 %, +0.40. On
gold the inside entries are the *better* ones in both periods (+0.72 / +0.11 against +0.45 / -0.22), on BTC in sample,
on NAS100 the sign turns: not a four-market rule. "The Asia extreme between entry and target" is better in both periods
raw (+0.25 / +0.12) and nothing within the R:R bands (+0.04 / -0.02): the target beyond the Asia extreme is simply a
farther target. The sweep through the Asia extreme (the stop beyond it) is under the base in both periods (-0.28 /
-0.24) but positive in sample (+16R on 33 trades) and only BTC has both periods (-0.56 / -0.47 on 14 / 29 trades); the
README's 8 October screen and `smc_literature.md` 2.7 found the same sweep "mixed". The range's height (in 1H ATR) is
not monotonic. **No four-market rule (EURUSD's is the other angle's). Draw the Asia high and low as lines from the left
edge.**

### 2.5 The day's and the entry window's high/low at the signal

| | IS | OOS | within R:R bands IS / OOS |
|---|---|---|---|
| the target needs a new day extreme | 183 / 46 % / +0.86 | 441 / 27 % / +0.04 | -0.21 / +0.17 |
| the target lies inside the day's range so far | 137 / 58 % / +0.56 | 252 / 35 % / -0.09 | (the complement) |
| the sweep extreme is the window's extreme so far | 173 / 51 % / +0.83 | 348 / 31 % / +0.02 | per market: NAS100 only |
| the sweep extreme is the day's extreme so far | 47 / 51 % / +0.96 | 131 / 27 % / -0.21 | sign turns |
| entry 0.5-1 ATR(1H) from the day's extreme on the stop side | 26 / 54 % / +0.46 | 49 / 27 % / -0.25 | NAS100, BTC agree; EURUSD, gold too few IS |

"The target inside the day's range so far" is the largest both-period raw effect of the study (-0.31 / -0.13 against
the rest, 137 / 252 trades) and it is entirely the planned R:R (1.5-1.9 inside against 2.9-3.3): within the bands the
IS sign turns (1.5-2.5R band IS: inside 39 trades 54 % +0.72 against 91 trades 49 % +0.59; OOS: 81 trades 23 % -0.29
against 240 trades 30 % -0.10). Half the sweeps are the window's extreme (EURUSD 45 / 40 %, gold 52 / 50 %, NAS100
56 / 52 %, BTC 61 / 54 %), a quarter the day's (8-28 %); neither sorts the outcome in a stable way (`followup.md` E:
the window's-extreme bucket agrees with itself on NAS100 only, +0.82 / +0.68 on 24 / 52 trades). **No rule. Label the
stop "sweep = sessie-low" when they coincide rather than adding lines.**

### 2.6 The balance level the shift closed through (the engine's `break_level`)

Rebuilt with the engine's structure code for 100 % of the trades (the far edge of the latest opposing gap the
confirmation close was the first to cross). The planned entry minus the level, as a share of the stop distance:

| share of the stop distance | IS | OOS |
|---|---|---|
| <5 % | 81 / 53 % / +0.67 | 178 / 30 % / +0.13 |
| 5-10 % | 59 / 49 % / +0.56 | 132 / 31 % / -0.11 |
| 10-20 % | 86 / 52 % / +0.94 | 164 / 29 % / -0.20 |
| 20-35 % | 64 / 53 % / +0.95 | 133 / 29 % / -0.15 |
| >35 % | 32 / 41 % / +0.30 | 91 / 33 % / +0.39 |

In ATR14 of the confirmation timeframe: <0.25: 137 / 48 % / +0.58 and 306 / 29 % / +0.00; 0.25-0.5: 94 / 51 % / +0.94
and 186 / 30 % / -0.14; 0.5-1: 73 / 58 % / +0.91 and 133 / 28 % / -0.06; 1-2: 16 and 60 / 37 % / +0.17. In ATR of the
zone timeframe (table 6c) the same picture. Nothing monotonic in any unit; the entry sits within a quarter ATR of the
level in 43-44 % of the trades, which is why the README's limit on the level (`risk.limit_entry_at: break_level`,
8-9 October) gained nothing and missed fills: the level is only 0.1-0.2 R below the entry. **No rule. Draw it as a
dotted line from the confirmation candle: it is the "balance shift" the trader looks for, and it is always in the
picture.**

### 2.7 The sweep extreme against the stop

The stop sits *exactly on* the sweep extreme (`sl_offset_pips: 0` in all four profiles; the 1-pip spread buffer is in
the sizing only) in every trade whose sweep reaches the minimum stop: EURUSD 64 / 72 % of the trades, gold 100 / 98 %,
NAS100 100 / 65 %, BTC 100 / 87 %. The rest are widened to the minimum (8 pips EURUSD and gold, 12 points NAS100, $60
BTC):

| widened to the minimum | IS | OOS | the rest IS | the rest OOS |
|---|---|---|---|---|
| EURUSD | 17 (36 %) / 24 % / -0.00 (-0.0R) | 27 (28 %) / 15 % / -0.33 (-8.9R) | 30 / 60 % / +1.48 | 70 / 30 % / +0.25 |
| XAUUSD | 0 | 6 / 33 % / +0.45 | 143 / 49 % / +0.60 | 365 / 30 % / -0.08 |
| NAS100 | 0 (12 points never binds at 15-20k) | 35 (35 %) / 26 % / +0.07 | 43 / 47 % / +0.87 | 65 / 35 % / +0.56 |
| BTCUSD | 0 | 17 (13 %) / 35 % / -0.14 | 89 / 58 % / +0.79 | 113 / 33 % / -0.23 |

The filter scan over every bucket of every element (about 150 buckets with 15+ trades in each period) returns exactly
one bucket that removes negative R in both periods: this one (IS -0.0R on 17 trades, OOS -6.2R on 85: EURUSD -8.9,
gold +2.7, NAS100 +2.3, BTC -2.4). It is a EURUSD result: neutral in sample (the 17 trades sum to 0.0R at 24 % won
against 60 % for the rest), -8.9R out of sample, and it costs 36 % of EURUSD's trades. The widening by 25-50 % of the
final stop distance is the worst slice (IS 10 trades 30 % +0.26R; OOS 33 trades 9 % -0.73R a trade). It overlaps little
with the ledgers angle's candidate D (EURUSD stops under 0.5 ATR(1H): widened AND under 0.5 ATR = 2 IS / 19 OOS
trades): the two rules catch different small sweeps. Today's batch (`RESULTS_14oct.md`) shows the stop is sensitive in
the other direction: a larger minimum (ms10 -5.7R, ms12 -8.3R) and an offset beyond the extreme (slo1 -4.9R, slo2
-8.8R; gold slo3 -7.0R; BTC slo20 -3.7R) all lose in sample, so the sweep extreme itself is the right stop and the
only question is whether to refuse the sweep that is too small. The sweep through the zone's P (the stop beyond P): IS
16 / 56 % / +0.89, OOS 59 / 27 % / -0.16: the ledgers angle's weak candidate E, nothing more here. The stop distance in
1H ATR is not monotonic (0.5-0.75 ATR is the best in sample, 89 trades 61 % +1.11, and -0.04 out of sample).

### 2.8 Untested opposing zones (1H and 4H, never touched) between the entry and the target

| fresh opposing zones | IS | OOS |
|---|---|---|
| none in the path | 299 / 52 % / +0.71 | 650 / 30 % / -0.05 |
| one in the path | 21 / 33 % / +1.11 | 37 / 30 % / +0.56 |
| two or more | 2 | 11 / 36 % / +0.48 |
| one within one reward beyond the target (the target sits before it) | 23 / 48 % / +0.69 | 49 / 22 % / -0.27 |

A fresh opposing zone in the path lowers the win rate in sample (33 % against 52 %) and the R a trade is two outliers
(BTC 8 trades +2.72, NAS100 OOS 4 trades +4.80): nothing to act on at 21 / 37 trades. A fresh zone just beyond the
target is the only bucket here that holds within the R:R bands (-0.01 / -0.36): out of sample 22 % won, in sample at
the base, 7 % of the trades. Tested (touched, not broken) zones in the path sort nothing. The setup chart today hides
these zones (`chart_zones` keeps only the bias direction once the bias is tradable). **No rule. Draw the fresh
opposing zones in the path and the first one beyond the target as dashed boxes.**

## 3. The follow-up in numbers (`followup.md`)

- **A, the filter scan:** 1 candidate of ~150 buckets (the widened stop, above). Every "better in both periods" bucket
  costs in-sample R when read as a filter on its complement.
- **B, the R:R control:** of the 14 target-side buckets with 20+ trades in both periods and the same raw sign, 9 are
  R:R effects (yesterday's extreme at / beyond the target, the day's extreme in all three classes, the Asia extreme in
  all three, the engine level before / beyond the target); 5 survive within the bands (the resting swing at the target,
  the engine level at the target, no resting level ahead, the fresh zone beyond the target), all between -0.07 and
  +0.16R a trade out of sample and none agreeing across the four markets.
- **C, the widened stop against the ATR cut:** above.
- **D, in the picture:** yesterday's extreme on the target side 88 / 92 % (the stop side 20 / 21 %, on 5m charts
  10 %); last week's 41 / 40 % (stop side 3-4 %); the Asia extreme 98-99 % (stop side 72-79 %; the range's hours lie
  on the chart in 25 % of the 5m charts, 100 % of the 15m charts); the break level 100 %; the nearest resting swing
  87-89 %; the nearest 0.25-ATR pool 38-47 %; the engine's nearest equal high/low 33-49 %. Median distance ahead of the
  entry: yesterday's extreme 1.5R, the nearest swing 1.9R, last week's extreme 3.9R.
- **E, per market:** no signal agrees with itself in both periods on all four markets with the same sign; "no resting
  swing within one reward past the target" agrees on four markets but with EURUSD's sign reversed (+1.09 / +0.34
  against -0.5 / -0.2 elsewhere). NAS100-only both-period signals: the target on a resting swing (+1.38 / +0.95 on
  10 / 28 trades), the sweep extreme = the window's extreme (+0.82 / +0.68 on 24 / 52); for the NAS100 angle, not a rule.

## 4. Recommendations

### 4a. What to DRAW on the Telegram setup chart (explains the trade; no predictive claim)

The runner draws the setup chart in `live.py` `send_chart` -> `notify/chart.py` `render_chart(series, pois=..., setup=...,
extra_lines=[(price, label, from_ts)], extra_boxes=[(low, high, label)], shade_spans=...)`. Lines are drawn in dark red
dash-dot from `from_ts` (or the left edge) to the right edge; boxes as grey dashed rectangles over the full width; a
line outside the price axis is simply not visible, so none of these stretches the picture. In order of value:

1. **Yesterday's high and low on the setup chart.** `chart_context` already makes the two lines ("vorige dag high/low")
   and the session shading from `self.closed_daily(now)`, but `send_chart` skips it when there is a setup
   (`extra_lines, spans = self.chart_context(...) if setup is None else ([], [])`). Change: call it for the setup chart
   too (and in `dorus_review`'s three charts). The target-side line is in the picture 88-92 % of the time and tells the
   trader whether the target needs a new day extreme (IS 46 % won, +0.86R a trade) or lies inside yesterday's range.
2. **The Asia range as two lines from the left edge**, labels "Azië high 00-08" / "Azië low 00-08": from the drawn
   series (`view = series.tail(lookback)`; the candles of the signal's Amsterdam day with hour < 8; when the chart starts
   after 08:00, from `self._views[Timeframe.MIN_5]`). A box would be clipped on 75 % of the 5m charts; lines are not.
   In the picture 98 % (target side) / 72-79 % (stop side). It shows the EURUSD rule of the EURUSD angle at a glance
   (the entry inside the range) and the sweep that took the Asia low (the stop under it).
3. **The sweep extreme, marked and named.** `setup.confirmation.invalidation_price` is the extreme since the re-entry;
   the runner finds its candle by scanning the confirmation-timeframe view from `setup.touched_at` to
   `setup.confirmation.timestamp` for the low (high) equal to it. Draw a small marker there with the label "sweep", and
   extend the SL label: "SL 1.07413 = sweep" when the stop is on it (64-100 % of the trades per market), "SL 8 pips
   (sweep 5.2 pips)" when `setup.notes` carries "moved out ... to the 8-pip minimum" — the one case that loses on
   EURUSD, so the trader sees it. Add "= sessie-low" / "= dag-low" when the extreme equals the window's or the day's
   extreme so far (`in_session` gives the window candles; the day's from the local date).
4. **The break level** (`setup.confirmation.break_level`): one dotted line from the confirmation candle, label
   "B-level (shift door 1.07328)". Always in the picture. No predictive content; it is the balance shift itself and the
   level a `limit_entry_at: break_level` would rest on.
5. **Resting liquidity on the zone timeframe ahead of the entry.** The engine's `StructureAnalysis.levels` (resting,
   on the target side, between the entry and one reward past the target) are the exact objects of section 2.2; `touches
   >= 2` marks an equal high/low. The live `Analysis` carries POIs but not the structures (the engine builds
   `structures` inside `analyze`), so the smallest change is to keep `self.last_structures` on the engine (one line in
   `analyze`) and in `send_chart` pass the levels as `extra_lines` with labels "liq 1H" / "liq 1H x2". Thin lines,
   at most three (the nearest). The nearest level sits exactly at the target in 26 % of the trades and within one
   reward beyond it in 15 %: "the target is the pool" / "the pool is just past the target" become visible.
6. **Fresh opposing zones in the path or within one reward beyond the target.** `analysis.pois` has them (status FRESH,
   the opposite direction); `chart_zones` drops them. Pass them as `extra_boxes` with the label "ongetest 1H supply"
   (dashed grey, so they are not mistaken for the setup's zone). 7 % of the trades have one just beyond the target
   (OOS 22 % won), 7 % one in the path.
7. **Last week's high and low** from `self._views.get(Timeframe.W_1)` (`closed_as_of(now)`, the bias holds the weekly):
   two lines, labels "vorige week high/low"; in the picture 40 % (3 % on the stop side), no information in the data;
   lowest priority, harmless.

Not worth drawing: the day's range so far as lines (the candles show it), the Asia range's height, the number of swings
in the path (a count, not a picture).

### 4b. Rules

- **Four-market rules that hold in both periods: none.** The both-period raw effects (the target inside the day's
  range, the Asia extreme in the path, yesterday's extreme at the target) are planned-R:R effects; the ones that
  survive the R:R control (the target on a resting swing, no level ahead, a fresh zone beyond the target) are
  one-market effects or under 0.2R a trade with the markets disagreeing.
- **One market-specific candidate, for a backtest, not for the profile yet:** EURUSD, refuse a setup whose sweep extreme
  lies nearer than the 8-pip minimum instead of widening the stop to it. Exact rule: in `kronos_trader/strategy/risk.py`
  `build_setup`, at the branch `if params.min_stop_pips > 0 and abs(entry - stop) < params.min_stop_pips * spec.pip_size:`,
  a new `risk.min_stop_reject: bool = False` (config.py, beside `min_stop_pips`) returns `None, ["stop nearer than the
  8-pip minimum: refused (min_stop_reject)"]` instead of widening; `min_stop_reject: true` in `config/dorus_live.yaml`
  only. Ledger-level expectation: IS 47 -> 30 trades, R unchanged (+0.0R removed, 24 % won among the removed against
  60 %), OOS +8.9R on 27 trades removed; on gold, NAS100 and BTC it is not proposed (NAS100 OOS +2.3R removed, gold
  +2.7R). The ledger check is approximate: EURUSD allows a re-entry in the same visit after a stop, so a refused setup
  can free the visit for a later shift; and 36 % fewer EURUSD trades slow the challenge. Command when a worker is free:
  the standard backtest with the knob on, both periods, then the challenge replay.
- **Negative results, stated so they are not run again:** the equal-highs pool position (any tolerance), the previous
  week's extreme in any class, the Asia range's height and the sweep through it as a four-market filter, the sweep
  extreme = the day's / the window's extreme, the break-level distance in any unit, the stop distance beyond the sweep
  extreme (it is zero by design; the offsets and larger minimums lose in today's batch), the count of untested zones in
  the path, "the target inside the day's range" as a filter or a stake rule (+0.56R a trade in sample on 137 trades).

## 5. Files

- Report: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/liquidity_map.md`
- Scripts and tables: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/liquidity_map/`
  (`measure.py`, `measure_extra.py`, `tables.py`, `tables_extra.py`, `followup.py`; `features.csv`, `tables.md`,
  `tables_extra.md`, `followup.md`, `measure.log`, `measure_extra.log`).
