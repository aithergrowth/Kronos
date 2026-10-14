# Maximum adverse and favourable excursion (MAE/MFE) of every trade on the eight ledgers (14 October 2026)

Angle: what the price did between the fill and the exit of every trade, in R (stop distance = 1R), on the 5m candles,
and what that says about the stop, the target, the break-even and a time exit. A screen on the ledger's own trades
(trade interactions, limit prices and the signal set stay as they were), not a backtest; where an engine run exists it
is quoted next to the walk.

Scripts: `research/excursion/excursion.py` (the walk; writes `trades_<MARKET>_<IS|OOS>.csv`, one row a trade with
its MFE/MAE, its hourly profile and every variant's R) and `research/excursion/report.py` (writes `tables.md`, all
tables; the full file is appended at the end of this page). Runtime 25 s for the eight ledgers.

## 1. Method and the conventions that matter

- Ledgers: `aca/eutwo_EURUSD`, `base_XAUUSD`, `rr08_NAS100`, `base_BTCUSD` (2024 - Sep 2026) and their `oos_`
  counterparts (2017-2023; BTC June 2020-2023), 1 % units, guard off, 5m step, bid candles. Settings from each
  `.provenance.json`: spread EURUSD 1 pip, gold $0.20, NAS100 1.5 points, BTC $15; break-even after 4R (gold 2R);
  NAS100 closes after 48 h; minimum R:R 1.0 / 0.8 / 0.8 / 0.5; EURUSD and NAS100 enter by limit 25 % back toward the
  stop (every trade on those ledgers is a limit fill).
- The walk is `kronos_trader/execution/paper.py` bar for bar: a long's stop and target on the bid, a short's on the ask
  (bid + spread); the stop before the target in one candle; a candle that gaps through the stop fills at its open; the
  break-even moves the stop to the entry when a candle's favourable extreme reaches the trigger, and the same candle
  trading back through the entry closes it there; a time exit closes at the candle's close (bid / ask). A limit fill
  that its own fill candle stops is -1R at once (the runner's rule). **The walk reproduces all eight ledgers trade for
  trade (1,020 of 1,020 trades, every R within 0.02).**
- Excursions: the exit candle contributes the exit itself, not its range (the broker takes the stop first in that
  candle, so what else it did is unknown); a loser's MFE is therefore what the candles before the stop showed, a
  winner's MAE what the candles before the target showed. A sensitivity column with the exit candle's full range
  included is in table 3 (it moves the "90 % of the way" share by 0-2 points: the convention does not change a result).
- Variants keep the cash at risk constant: with a stop m times as wide the position is 1/m the size, so every outcome
  is counted in the new stop distance (a loss is still -1R of cash, a winner that reaches the same level earns R:R/m).
  Gold's "fixed 2R" fallback targets (66 of 143 trades in sample, 191 of 371 out of sample) move with the stop; every
  other target is a price level. The horizon is 30 days after the fill (no trade reached it).
- Costs: the same trades carry the same costs, so deltas are gross; where a variant drops trades under the minimum R:R
  the 0.10R a trade saved is added ("delta + costs"). A wider stop also lowers the commission and spread in R by
  (1 - 1/m) x 0.10R a trade, under 0.02R: ignored.

## 2. The answers in short

| Question | Answer | Both periods? |
|---|---|---|
| (1) Stop 10 / 20 / 30 % wider | In sample it costs every market: four markets together -23.4R / -47.2R / -52.3R on +238R (winners pay 9 / 17 / 23 % of their R, 0-5 losers a market are saved). Out of sample gold 2017-2023 gains +6R / +11R at 1.2 / 1.3 x (11-16 of 247 losers saved) and BTC +1R / -1R; EURUSD and NAS100 lose there too. 85-96 % of the stopped trades are stopped at 1.5 x the distance as well: the losers are not near misses. | no: fails 2024-2026 on all four |
| Stop 10 / 20 % tighter | -62.1R / -79.3R in sample (14-27 % of the winners go beyond 0.8R against before the target, 2-16 % beyond 0.9R), -10.8R / -43.0R out of sample. | no |
| (2) Target 5 / 10 / 20 % nearer | 5 %: in sample -6.1R (EURUSD -3.4, gold +0.5, NAS100 -0.1, BTC -3.1), out of sample +6.2R (EURUSD -1.1, gold +0.3, NAS100 +2.6, BTC +4.5): 4 of 8 cells better, a wash. 10 %: -21.2R / +0.4R. 20 %: -46.5R / -24.6R. Only 2-13 % of the losers got within 10 % of their target; the winners all pay. The backlog's "gold OOS +11.2R from 8 rescued trades" is not reproduced by the exact walk (+0.3R, 2 losers and 2 break-evens rescued, winners -11.1R). | no |
| (3) Break-even +1R / +2R / +3R | +1R: -82.3R in sample, -70.0R out of sample (17-32 % of losers see +1R first, but 17-41 % of the winners also return to the entry after +1R and each is worth 2-3R). +2R: -20.8R / -8.0R (EURUSD -12.7 / -7.4, NAS100 -4.5 / -0.6, BTC -3.5 / 0; gold's own rule). +3R: -4.5R / -3.4R (EURUSD 0 / 0, gold -2.0 / -5.4, NAS100 +1.0 / +2.0, BTC -3.5 / 0). The rules as they run (4R; gold 2R) are worth +3.0R in sample and +12.7R out of sample against no break-even; gold's 2R (7 October) is the one that pays in both (+2.0R / +5.7R). Reconciles with the README and the `oct14b` engine runs to 0.1-1.0R. | the current rules hold; no change passes both |
| (4) A time-based exit | None passes both periods. Max hold 24 h: -21.2R / -30.6R (NAS100's 48 h is right: 24 h -2.4R / -5.5R, 72 h -1.7R / -1.0R). A time stop (close at 8 h when under 0R): -16.9R / -12.7R. A no-progress exit (close at 4 h when +0.5R was never seen): -13.2R / +5.2R. The slow winners carry the ledgers: the 6-24 % of winners open longer than 24 h hold +17R (EURUSD), +23R (gold), +6.5R (NAS100, BTC) in sample and +28R / +58R / +16R out of sample. Confirms the README. | no |

What the paths say about the strategy: half of the losers never go a quarter R in profit (42 / 24 / 52 / 30 % in
sample; 51 / 40 / 38 / 58 % out of sample), their best moment is 0-30 minutes after the fill (median hours to MFE
0.0-0.5), and 85-96 % of them run through a stop 1.5 times as wide too. The management rules are not where the
R is lost; the entries are (the earlier loss-anatomy conclusion, now with the stop width ruled out as the cause).

## 3. The ledgers and the excursions

| market | trades | won | stopped | break-even | time | sum R | R a trade | median planned R:R | median hold h | stop (median, pips/$/pts) |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 47 | 47 % | 24 | 1 | 0 | +44.2 | 0.94 | 2.12 | 1.2 | 8.1 pips |
| XAUUSD IS | 143 | 49 % | 71 | 2 | 0 | +86.1 | 0.60 | 2.00 | 2.2 | $8.5 |
| NAS100 IS | 43 | 47 % | 23 | 0 | 1 | +37.2 | 0.87 | 1.67 | 0.9 | 27.5 pts |
| BTCUSD IS | 89 | 58 % | 37 | 0 | 0 | +70.6 | 0.79 | 1.52 | 1.6 | $446 |
| EURUSD OOS | 97 | 26 % | 68 | 4 | 0 | +8.5 | 0.09 | 1.73 | 0.7 | 7.8 pips |
| XAUUSD OOS | 371 | 30 % | 247 | 14 | 0 | -25.1 | -0.07 | 2.00 | 1.8 | $3.2 |
| NAS100 OOS | 100 | 32 % | 66 | 2 | 2 | +38.8 | 0.39 | 1.81 | 1.8 | 15.6 pts |
| BTCUSD OOS | 130 | 33 % | 86 | 1 | 0 | -28.6 | -0.22 | 1.41 | 1.4 | $219 |

### 3a. Winners: how close they came to the stop (MAE of the trades that reached the target)

| market | winners | MAE median | p75 | p90 | beyond 0.5R | beyond 0.8R | beyond 0.9R | never 0.1R against | hours to the MAE (median) | hours to the target (median) |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 22 | 0.41 | 0.79 | 0.84 | 45 % | 23 % | 9 % | 27 % | 0.2 | 2.9 |
| XAUUSD IS | 70 | 0.39 | 0.79 | 0.94 | 41 % | 26 % | 16 % | 17 % | 0.3 | 5.1 |
| NAS100 IS | 19 | 0.37 | 0.76 | 0.88 | 42 % | 16 % | 11 % | 26 % | 0.2 | 2.1 |
| BTCUSD IS | 52 | 0.40 | 0.62 | 0.87 | 35 % | 15 % | 8 % | 19 % | 0.2 | 1.7 |
| EURUSD OOS | 25 | 0.35 | 0.76 | 0.87 | 48 % | 20 % | 12 % | 24 % | 0.2 | 4.0 |
| XAUUSD OOS | 110 | 0.50 | 0.76 | 0.88 | 50 % | 20 % | 7 % | 5 % | 0.4 | 4.5 |
| NAS100 OOS | 30 | 0.50 | 0.81 | 0.86 | 50 % | 27 % | 10 % | 10 % | 0.1 | 3.3 |
| BTCUSD OOS | 43 | 0.41 | 0.70 | 0.84 | 40 % | 14 % | 2 % | 7 % | 0.2 | 1.7 |

The winners' adverse excursion comes early (median 0.1-0.4 h after the fill: the limit fill or the market fill sits in
the retrace, and the retrace runs on a little) and is deep: 35-50 % go beyond half the stop, 14-27 % beyond 0.8R. A
stop 20 % tighter would have stopped 14-27 % of the winners; 10 % tighter 2-16 %. The 4H-zone winners sit deeper
still (median MAE 0.7-0.8R on EURUSD and NAS100 in sample, table 11 in the appendix): at the double stake the
live set runs on those zones, a 4H trade is routinely 1.5-2.4 % of the account under water before it pays.

### 3b. Losers: how close they came to the target (MFE of the stopped trades)

| market | losers | MFE median | never 0.25R | reached 0.5R | reached 1R | reached 1.5R | reached 2R | half way to the target | 80 % | 90 % | R given back (sum of MFE of those >= 1R) | hours to the MFE (median) | hours to the stop (median) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 24 | 0.36 | 42 % | 38 % | 29 % | 8 % | 0 % | 25 % | 17 % | 8 % | 9.3 | 0.2 | 0.5 |
| XAUUSD IS | 71 | 0.59 | 24 % | 58 % | 20 % | 8 % | 0 % | 24 % | 8 % | 3 % | 19.9 | 0.3 | 1.8 |
| NAS100 IS | 23 | 0.24 | 52 % | 43 % | 17 % | 9 % | 4 % | 22 % | 13 % | 13 % | 7.9 | 0.0 | 0.4 |
| BTCUSD IS | 37 | 0.59 | 30 % | 54 % | 27 % | 5 % | 0 % | 32 % | 11 % | 3 % | 13.8 | 0.5 | 1.5 |
| EURUSD OOS | 68 | 0.19 | 51 % | 44 % | 28 % | 15 % | 7 % | 29 % | 16 % | 13 % | 31.1 | 0.0 | 0.3 |
| XAUUSD OOS | 247 | 0.41 | 40 % | 43 % | 22 % | 7 % | 0 % | 25 % | 5 % | 2 % | 74.9 | 0.2 | 1.3 |
| NAS100 OOS | 66 | 0.36 | 38 % | 45 % | 32 % | 14 % | 5 % | 29 % | 15 % | 12 % | 33.9 | 0.2 | 0.6 |
| BTCUSD OOS | 86 | 0.15 | 58 % | 24 % | 9 % | 5 % | 0 % | 19 % | 3 % | 2 % | 11.5 | 0.2 | 1.3 |

"Gave it back": 17-32 % of the losers saw +1R before the stop (9-27 % in the weak BTC years), 8-17 % got 80 % of
the way to their target, 2-13 % 90 %. The R they showed and lost (the sum of the MFE of the losers that reached 1R)
is 8-20R a market in sample, which is what a partial exit would be chasing; the trader's rule excludes partials, and
section 6 shows that a break-even at +1R, the no-partial way to keep it, costs more than it keeps.

### 3c. The trades closed at break-even or by the time limit

27 trades on the eight ledgers (IS: EURUSD 1, gold 2, NAS100 1 by time; OOS: EURUSD 4, gold 14, NAS100 2 + 2 by
time, BTC 1). The break-even trades' MFE was 2.0-9.4R (planned R:R 2.6-20.6; one gold trade reached its 2R in the
candle that also returned to the entry), the NAS100 time exits' 1.0-2.0R. The stop or target alone would have ended
25 of them at the stop (-1R each) and 2 at the target (gold OOS, +2.6R and +3.7R); the ledgers' 0 and the NAS100
time exits (+0.68R, +0.80R, +1.64R) are therefore worth +21.8R against stop/target alone over all eight ledgers,
+4.7R in sample. The full list is table 4 in the appendix.

### 3d. Target reach by planned R:R band (in sample; the out-of-sample table is in the appendix)

| market | R:R band | trades | reached the target | stopped | sum R | R a trade | losers' MFE median | odds needed (1/(1+R:R)) |
|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 1-1.5 | 12 | 67 % | 33 % | +12.3 | 1.02 | 1.19 | 43 % |
| EURUSD IS | 1.5-2 | 9 | 67 % | 33 % | +12.6 | 1.40 | 0.15 | 38 % |
| EURUSD IS | 2-3 | 11 | 36 % | 64 % | +6.6 | 0.60 | 0.40 | 29 % |
| EURUSD IS | 3-5 | 11 | 27 % | 73 % | +6.5 | 0.59 | 0.17 | 23 % |
| EURUSD IS | >5 | 4 | 25 % | 50 % | +6.3 | 1.57 | 0.23 | 13 % |
| XAUUSD IS | <1 | 7 | 57 % | 43 % | +0.3 | 0.04 | 0.64 | 53 % |
| XAUUSD IS | 1-1.5 | 20 | 50 % | 50 % | +1.8 | 0.09 | 0.39 | 45 % |
| XAUUSD IS | 1.5-2 | 11 | 36 % | 64 % | -0.1 | -0.01 | 0.24 | 37 % |
| XAUUSD IS | 2-3 | 81 | 51 % | 48 % | +43.8 | 0.54 | 0.60 | 33 % |
| XAUUSD IS | 3-5 | 13 | 54 % | 46 % | +21.8 | 1.68 | 0.83 | 20 % |
| XAUUSD IS | >5 | 11 | 36 % | 55 % | +18.5 | 1.69 | 0.63 | 13 % |
| NAS100 IS | <1 | 5 | 40 % | 60 % | 0.0 | 0.00 | 0.54 | 52 % |
| NAS100 IS | 1-1.5 | 12 | 33 % | 58 % | +1.6 | 0.13 | 0.04 | 44 % |
| NAS100 IS | 1.5-2 | 8 | 62 % | 38 % | +9.6 | 1.21 | 0.00 | 38 % |
| NAS100 IS | 2-3 | 8 | 50 % | 50 % | +9.9 | 1.24 | 1.05 | 30 % |
| NAS100 IS | 3-5 | 6 | 50 % | 50 % | +11.3 | 1.88 | 0.90 | 22 % |
| NAS100 IS | >5 | 4 | 25 % | 75 % | +4.7 | 1.18 | 0.04 | 9 % |
| BTCUSD IS | <1 | 20 | 90 % | 10 % | +10.7 | 0.53 | 0.33 | 56 % |
| BTCUSD IS | 1-1.5 | 24 | 62 % | 38 % | +8.7 | 0.36 | 0.08 | 45 % |
| BTCUSD IS | 1.5-2 | 11 | 18 % | 82 % | -5.3 | -0.48 | 0.88 | 37 % |
| BTCUSD IS | 2-3 | 28 | 50 % | 50 % | +20.4 | 0.73 | 0.78 | 28 % |
| BTCUSD IS | 3-5 | 3 | 33 % | 67 % | +1.5 | 0.51 | 0.36 | 21 % |
| BTCUSD IS | >5 | 3 | 67 % | 33 % | +34.7 | 11.55 | 0.71 | 6 % |

The reach rate falls with the R:R as it should, but every band clears its own odds in sample except gold's 1.5-2
(36 % against 37 % needed), NAS100's under 1 (40 % against 52 %; 5 trades) and 1-1.5 (33 % against 44 %) and BTC's
1.5-2 (18 % against 37 %; 11 trades).
Out of sample only the far bands (R:R over 3) clear their odds on EURUSD, gold and NAS100 (the README's "R:R >= 2
points the same way in six of eight" is the same observation): a nearer target cannot help a ledger whose profit sits
in the far targets. Gold's bands under 2 (38 trades, +2.0R in sample, 90 trades, -1.8R out of sample) are the
fallback and the sub-2R liquidity targets: no R in either period, which argues for the floor staying at 0.8 rather than
falling further, not for a change.

## 4. (1) A wider stop, the cash at risk constant

R in the new stop distance; "min R:R" drops the trades whose new R:R falls under the profile's minimum (+0.10R costs
saved each); "saved" = stopped trades that now reach the target; "overlap" = trades that now close after the next
trade's open (the engine, one open trade a market, would have skipped that next signal: the OOS gold gains below rest
partly on trades the engine could not have taken).

| market | stop x | ledger R | all trades R | delta | min R:R: trades / R / delta + costs | saved | their gain | winners' cost | overlap |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 0.9 | +44.2 | +41.8 | -2.5 | 47 / +41.8 / -2.5 | 0 | 0 | -2.5 (2 winners stopped) | 0 |
| EURUSD IS | 1.1 | +44.2 | +38.0 | -6.2 | 47 / +38.0 / -6.2 | 0 | 0 | -6.2 | 0 |
| EURUSD IS | 1.2 | +44.2 | +32.9 | -11.4 | 47 / +32.9 / -11.4 | 0 | 0 | -11.4 | 1 |
| EURUSD IS | 1.3 | +44.2 | +31.9 | -12.4 | 47 / +31.9 / -12.4 | 1 | +3.4 | -15.7 | 3 |
| XAUUSD IS | 0.9 | +86.1 | +59.5 | -26.6 | 143 / +59.5 / -26.6 | 1 | +3.0 | -29.6 (11 winners stopped) | 0 |
| XAUUSD IS | 1.1 | +86.1 | +81.3 | -4.8 | 139 / +78.3 / -7.4 | 2 | +6.0 | -9.8 | 2 |
| XAUUSD IS | 1.2 | +86.1 | +73.6 | -12.5 | 136 / +73.9 / -11.5 | 3 | +8.0 | -19.5 | 2 |
| XAUUSD IS | 1.3 | +86.1 | +65.9 | -20.2 | 129 / +66.3 / -18.4 | 5 | +14.0 | -34.2 | 4 |
| NAS100 IS | 0.9 | +37.2 | +37.7 | +0.5 | 43 / +37.7 / +0.5 | 0 | 0 | -0.5 (2 winners stopped) | 0 |
| NAS100 IS | 1.1 | +37.2 | +32.7 | -4.5 | 43 / +32.7 / -4.5 | 0 | 0 | -5.4 | 0 |
| NAS100 IS | 1.2 | +37.2 | +28.2 | -9.0 | 43 / +28.2 / -9.0 | 0 | 0 | -9.9 | 0 |
| NAS100 IS | 1.3 | +37.2 | +32.9 | -4.3 | 43 / +32.9 / -4.3 | 1 | +2.8 | -13.7 | 0 |
| BTCUSD IS | 0.9 | +70.6 | +37.1 | -33.5 | 89 / +37.1 / -33.5 | 0 | 0 | -33.5 (4 winners stopped, 2026 -36.2) | 0 |
| BTCUSD IS | 1.1 | +70.6 | +62.7 | -7.9 | 86 / +61.3 / -9.0 | 1 | +1.9 | -9.8 | 1 |
| BTCUSD IS | 1.2 | +70.6 | +56.3 | -14.3 | 84 / +54.0 / -16.1 | 2 | +3.6 | -17.9 | 1 |
| BTCUSD IS | 1.3 | +70.6 | +55.2 | -15.4 | 80 / +51.1 / -18.6 | 4 | +9.4 | -24.8 | 1 |
| EURUSD OOS | 1.1 | +8.5 | +2.9 | -5.6 | 97 / +2.9 / -5.6 | 1 | +3.4 | -7.0 | 1 |
| EURUSD OOS | 1.2 | +8.5 | +9.0 | +0.6 | 97 / +9.0 / +0.6 | 4 | +15.3 | -12.7 | 3 |
| EURUSD OOS | 1.3 | +8.5 | +6.8 | -1.6 | 97 / +6.8 / -1.6 | 5 | +18.0 | -17.6 | 3 |
| XAUUSD OOS | 1.1 | -25.1 | -28.9 | -3.8 | 365 / -24.7 / +1.0 | 4 | +10.9 | -12.0 | 11 |
| XAUUSD OOS | 1.2 | -25.1 | -19.1 | +6.0 | 357 / -10.3 / +16.2 | 11 | +31.7 | -24.1 | 17 |
| XAUUSD OOS | 1.3 | -25.1 | -14.0 | +11.1 | 341 / -6.8 / +21.3 | 16 | +46.8 | -34.8 | 24 |
| NAS100 OOS | 1.1 | +38.8 | +29.0 | -9.8 | 100 / +29.0 / -9.8 | 0 | 0 | -9.3 | 0 |
| NAS100 OOS | 1.2 | +38.8 | +21.3 | -17.5 | 100 / +21.3 / -17.5 | 0 | 0 | -17.1 | 0 |
| NAS100 OOS | 1.3 | +38.8 | +26.3 | -12.4 | 100 / +26.3 / -12.4 | 4 | +12.6 | -23.7 | 1 |
| BTCUSD OOS | 1.1 | -28.6 | -26.3 | +2.4 | 126 / -25.2 / +3.8 | 3 | +7.6 | -5.2 | 1 |
| BTCUSD OOS | 1.2 | -28.6 | -27.6 | +1.0 | 125 / -27.0 / +2.1 | 5 | +10.5 | -9.6 | 1 |
| BTCUSD OOS | 1.3 | -28.6 | -30.0 | -1.4 | 119 / -32.1 / -2.3 | 6 | +11.9 | -13.2 | 1 |

The arithmetic: at 1.2 x the winners give up 17 % of their R (EURUSD IS 11.4R, gold 19.5R, NAS100 9.9R, BTC 17.9R)
and a saved loser pays R:R/1.2 + 1 (the saved ones measured: 1.8-3.4R each); EURUSD IS would need 3-4 of its 24
losers saved to break even and has 0, gold about 7 of 71 and has 3, NAS100 about 4 of 23 and has 0, BTC about 10 of
37 and has 2. Per year (appendix "by year"): the
wider stop loses in every in-sample year on EURUSD, gold and BTC, and in 2 of 3 on NAS100. The near-miss anatomy
(appendix table 10) says why: of the stopped trades, 0-4 % reach the target with a stop 1.1 x as wide, 0-6 % at 1.2 x,
4-11 % at 1.3 x, and 85-96 % are stopped at 1.5 x as well. The trader's "iets meer pips" instinct is the README's
`slbuf` result again (-27.9R over the four), now measured as a function of the distance: there is no width at which
the losers turn.

Out of sample the wider stop helps gold (+6R / +11R at 1.2 / 1.3 x on -25R; 11-16 losers saved) and BTC a little
(+1 / +2R), with 17-24 gold trades now overlapping the next signal and the gain concentrated in 2020 (+10.9R at
1.3 x); EURUSD +0.6R at 1.2 x; NAS100 -10 to -18R. A rule that only pays in years the strategy lost anyway, on one
market, is not one for the live set.

Rule tested and not proposed: `risk.sl_offset_pips` or a stop multiplier of 1.1-1.3 on any market. Keep the stops.

## 5. (2) A nearer target

The target moved y % of its distance toward the entry, the stop unchanged. Today's batch (`oct14h`, `tpf5_*`,
`risk.tp_buffer_fraction 0.05`) runs the 5 % case through the engine; these are the same trades re-walked.

| market | nearer | ledger R | all trades R | delta | won | rescued losers / their gain | rescued break-evens | winners' cost | min R:R: trades / delta + costs |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 5 % | +44.2 | +40.8 | -3.4 | 47 % | 0 / 0 | 0 | -3.4 | 46 / -5.1 |
| EURUSD IS | 10 % | +44.2 | +37.4 | -6.8 | 47 % | 0 / 0 | 0 | -6.8 | 45 / -10.0 |
| EURUSD IS | 20 % | +44.2 | +30.6 | -13.6 | 47 % | 0 / 0 | 0 | -13.6 | 44 / -15.4 |
| XAUUSD IS | 5 % | +86.1 | +86.6 | +0.5 | 51 % | 2 / +5.8 | 1 | -7.9 | 142 / -0.2 |
| XAUUSD IS | 10 % | +86.1 | +81.1 | -5.0 | 52 % | 3 / +8.2 | 1 | -15.7 | 140 / -6.9 |
| XAUUSD IS | 20 % | +86.1 | +70.9 | -15.2 | 54 % | 6 / +14.0 | 1 | -31.4 | 136 / -15.9 |
| NAS100 IS | 5 % | +37.2 | +37.1 | -0.1 | 49 % | 1 / +2.9 | 0 | -3.0 | 42 / -1.4 |
| NAS100 IS | 10 % | +37.2 | +34.0 | -3.2 | 49 % | 1 / +2.8 | 0 | -6.0 | 42 / -4.4 |
| NAS100 IS | 20 % | +37.2 | +32.3 | -4.9 | 51 % | 2 / +7.0 | 0 | -11.9 | 38 / -3.8 |
| BTCUSD IS | 5 % | +70.6 | +67.5 | -3.1 | 60 % | 1 / +2.2 | 0 | -5.4 | 89 / -3.1 |
| BTCUSD IS | 10 % | +70.6 | +64.4 | -6.2 | 61 % | 2 / +4.6 | 0 | -10.8 | 88 / -6.5 |
| BTCUSD IS | 20 % | +70.6 | +57.9 | -12.7 | 63 % | 4 / +8.8 | 0 | -21.5 | 84 / -14.4 |
| EURUSD OOS | 5 % | +8.5 | +7.3 | -1.1 | 27 % | 1 / +2.7 | 0 | -3.8 | 92 / -1.1 |
| EURUSD OOS | 10 % | +8.5 | +6.1 | -2.4 | 28 % | 2 / +5.3 | 0 | -7.6 | 87 / -4.4 |
| XAUUSD OOS | 5 % | -25.1 | -24.8 | +0.3 | 31 % | 2 / +5.9 | 2 | -11.1 | 367 / +2.9 |
| XAUUSD OOS | 10 % | -25.1 | -20.9 | +4.2 | 32 % | 7 / +18.5 | 3 | -22.3 | 364 / +8.4 |
| NAS100 OOS | 5 % | +38.8 | +41.4 | +2.6 | 35 % | 3 / +7.7 | 0 | -5.1 | 99 / +1.3 |
| NAS100 OOS | 10 % | +38.8 | +36.0 | -2.8 | 35 % | 3 / +7.5 | 0 | -10.3 | 99 / -4.0 |
| BTCUSD OOS | 5 % | -28.6 | -24.2 | +4.5 | 35 % | 3 / +7.3 | 0 | -2.9 | 127 / +6.3 |
| BTCUSD OOS | 10 % | -28.6 | -27.2 | +1.4 | 35 % | 3 / +7.1 | 0 | -5.7 | 127 / +3.2 |

Four markets together: 5 % nearer -6.1R in sample (2024 -5.8, 2025 +2.2, 2026 -2.6), +6.2R out of sample; 10 %
-21.2R / +0.4R; 20 % -46.5R / -24.6R. The 5 % case rescues 0-3 losers a market (the losers that got within 5 % of the
target: 2-13 %, table 3b) and takes 5 % from every winner, which on EURUSD (median R:R 2.1, a quarter above 3.3) is
3.4R for nothing rescued. The backlog's B6 ("better in 5 of 8 cells, gold OOS +11.2R from 8 rescued trades") came from
a re-walk whose base did not match the ledger (-22.4R against -25.1R) and whose MFE included the exit candle; the exact
walk gives gold OOS +0.3R (2 losers and 2 break-evens rescued at 95 % of the distance, the 110 winners -11.1R) and 4 of
8 cells better. Expect `tpf5_*` to land within a few R of these; whatever it lands on, a change that is -6R on
2024-2026 does not pass the adoption rule. Not proposed.

## 6. (3) Break-even at +1R / +2R / +3R, reconciled with the README and the engine runs

| market | ledger (its rule) | BE +1R | BE +1.5R | BE +2R | BE +3R | BE +4R | none |
|---|---|---|---|---|---|---|---|
| EURUSD IS | +44.2R (4R) | +17.0R (-27.3; 17 at 0) | +21.9R (-22.4) | +31.5R (-12.7; 3 at 0) | +44.2R (0) | +44.2R | +43.2R (-1.0) |
| XAUUSD IS | +86.1R (2R) | +57.0R (-29.1; 33 at 0) | +76.2R (-9.9) | +86.1R (0; 2 at 0) | +84.1R (-2.0) | +84.1R (-2.0) | +84.1R (-2.0) |
| NAS100 IS | +37.2R (4R) | +21.3R (-15.9; 11 at 0) | +25.1R (-12.1) | +32.7R (-4.5; 3 at 0) | +38.2R (+1.0; 1 at 0) | +37.2R | +37.2R (0) |
| BTCUSD IS | +70.6R (4R) | +60.7R (-9.9; 19 at 0) | +64.0R (-6.6) | +67.1R (-3.5; 1 at 0) | +67.1R (-3.5) | +70.6R | +70.6R (0) |
| EURUSD OOS | +8.5R (4R) | -9.4R (-17.9; 34 at 0) | +1.2R (-7.3) | +1.0R (-7.4; 12 at 0) | +8.5R (0; 4 at 0) | +8.5R | +4.5R (-4.0) |
| XAUUSD OOS | -25.1R (2R) | -67.1R (-42.0; 108 at 0) | -40.0R (-14.9) | -25.1R (0; 14 at 0) | -30.5R (-5.4) | -29.8R (-4.7) | -30.8R (-5.7) |
| NAS100 OOS | +38.8R (4R) | +26.4R (-12.4; 32 at 0) | +37.1R (-1.7) | +38.2R (-0.6; 6 at 0) | +40.8R (+2.0; 4 at 0) | +38.8R | +36.8R (-2.0) |
| BTCUSD OOS | -28.6R (4R) | -26.4R (+2.3; 12 at 0) | -28.8R (-0.2) | -28.6R (0) | -28.6R (0) | -28.6R | -29.6R (-1.0) |

Trade by trade (against no break-even at all): a break-even at +1R turns 8 / 16 / 4 / 10 losers into 0 in sample
(EURUSD / gold / NAS100 / BTC: +8 / +16 / +4 / +10R) and cuts 9 / 17 / 6 / 9 winners to 0 (-34.3 / -43.1 / -19.2 /
-19.9R): the losers that see +1R are worth 1R each when saved, the winners that dip back to the entry after +1R were
worth 2-4R each. At +2R: 1 / 2 / 1 / 0 saved against 2 / 0 / 2 / 1 cut (-12.7 / 0 / -5.5 / -3.5R). At +3R: 1 / 0 / 1 / 0
saved, 0 / 0 / 0 / 1 cut. Out of sample the same shape with larger numbers (+1R: 23 / 67 / 23 / 9 saved, 11 / 41 / 9 /
3 cut for -36.9 / -103.3 / -32.4 / -5.7R).

Reconciliation: the `oct14b` engine runs (after 0.10R costs) gave BE +1R EURUSD -27.3R, gold -28.1R, BTC -9.3R; BE
+2R EURUSD -12.7R, NAS100 -4.5R, BTC -3.5R; BE +3R EURUSD 0, gold -2.0R, BTC -3.5R: the walk matches each within
1R (exactly on five of eight). The README's older set (break-even at 2R: EURUSD 0, NAS100 0, gold -1.6R, BTC +1.0R)
was measured before the limit entries and the 2R gold rule; the signs agree. The backlog's B7 ("NAS100 break-even at
+2R: re-walk +1.0R IS / +2.4R OOS") is refuted: -4.5R in sample (the engine run `be2_NAS100` says the same -4.5R) and
-0.6R out of sample. BE +3R on NAS100 is +1.0R / +2.0R (one and four trades; `be3_NAS100` in `oct14f` is running):
noise, not a rule.

What holds in both periods: the rules as they run are worth +3.0R in sample and +12.7R out of sample against no
break-even, and gold's +2R (taken 7 October) is +2.0R / +5.7R (it saves 2 / 12 losers at 0 and cuts 0 / 2 winners),
EURUSD's 4R +1.0R / +4.0R, NAS100's 4R 0 / +2.0R, BTC's 4R 0 / +1.0R. Keep them; do not lower any to +1R or +2R.

## 7. (4) A time-based exit

The paths first (appendix 9a-9c): winners show +0.5R within one hour in 69-89 % of cases in sample (losers 33-43 %),
within four hours in 91-100 % (losers 38-54 %); losers' best moment is 0-0.5 h after the fill and their stop comes at
a median 0.4-1.8 h; winners take a median 1.7-5.1 h to the target and 6-18 % of them more than 24 h, carrying +6.5R
(BTC, NAS100) to +23R (gold) in sample and +16R (NAS100) to +58R (gold) out of sample, none on BTC 2020-2023. A time
rule has to give up those.

Delta R against the ledger on the same trades:

| market | hold 4 h | hold 8 h | hold 12 h | hold 24 h | hold 48 h | hold 72 h | 4 h & <= 0R | 8 h & <= 0R | 8 h & <= -0.5R | 24 h & <= 0R | no +0.5R by 2 h | by 4 h | by 8 h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | -11.3 | -14.4 | -10.2 | -9.0 | -2.1 | -1.7 | -7.2 | -8.6 | -2.5 | -3.9 | -5.0 | -5.9 | -5.7 |
| XAUUSD IS | -46.4 | -26.3 | -25.5 | -9.7 | -9.6 | -6.9 | -14.1 | -4.0 | -10.2 | +2.6 | -9.7 | -7.1 | -2.1 |
| NAS100 IS (48 h runs) | -6.6 | -1.6 | -2.0 | -2.4 | 0 | -1.7 | -3.3 | +1.5 | +0.7 | 0 | -2.9 | +1.0 | 0 |
| BTCUSD IS | -41.7 | -7.4 | -4.3 | -0.2 | +1.1 | -0.5 | -13.0 | -5.7 | +1.9 | +0.3 | -4.2 | -1.2 | -0.1 |
| EURUSD OOS | -31.1 | -20.8 | -20.6 | -21.0 | -9.1 | -11.5 | -21.9 | -13.8 | -1.9 | -7.9 | -3.7 | -0.6 | +1.5 |
| XAUUSD OOS | -18.8 | -4.2 | -3.2 | -6.3 | +2.2 | -0.3 | -21.5 | -2.6 | -1.0 | -3.8 | +2.9 | +5.2 | +2.6 |
| NAS100 OOS (48 h runs) | -19.9 | -13.6 | -7.5 | -5.5 | 0 | -1.0 | -2.3 | +1.2 | -1.7 | -2.2 | -3.6 | -0.5 | 0 |
| BTCUSD OOS | -2.2 | +3.8 | +7.2 | +2.1 | +1.6 | 0 | -0.5 | +2.4 | +3.1 | +2.0 | +3.4 | +1.2 | +3.3 |

Nothing passes both periods on any market by more than one or two trades: a max hold of 24 h is -21R / -31R over the
four; a time stop at 8 h (close only when under 0R) -17R / -13R; a no-progress exit at 4 h -13R / +5R; NAS100's "8 h
and under 0R" is +1.5R / +1.2R (two trades each side) and BTC's 48 h hold +1.1R / +1.6R (one trade each): noise. BTC
2020-2023 likes every time rule because that ledger has no slow winners at all (none over 24 h) and 47-55 % of its
open positions are under water at any hour; 2024-2026 BTC loses with each of them. NAS100's 48 h close (taken 5
October) is confirmed as the right length: 24 h -2.4R / -5.5R, 72 h -1.7R / -1.0R against it, and the three trades it
closed were all headed for the stop (+3.1R against -3R).

Confirms the README ("time stops failed", `smc_literature.md` 2.x "time stops and stale exits"). Not proposed.

## 8. What this means for the live set

1. Nothing in the stop, the target, the break-even or the hold time is left on the table on 2024-2026: every
   variant in this page is 0 to -82R in sample over the four markets, and the handful that gain out of sample gain in
   years the strategy lost. The profiles stay as they are; the current rules (4R break-even, gold 2R, NAS100 48 h, no
   partials, no time stop) are each confirmed in both periods.
2. Two backlog items close: B6 (target 5 % nearer) is -6.1R on 2024-2026 by the exact walk and should not be adopted
   whatever `tpf5_*` returns unless the engine disagrees by more than 10R; B7 (NAS100 break-even +2R) is refuted by
   the walk (-4.5R / -0.6R) and by the engine run (`be2_NAS100` -4.5R).
3. The excursion profile is a readiness tool for the forward record: a live winner is routinely 0.4R under water
   (median) and 14-27 % of winners go beyond 0.8R; a 4H-zone trade at the double stake can show -2 % of the account
   before it pays. The day report's "open risk to the stops" is the right number to watch, not the floating P&L.
4. The near-miss message Max asked for (task 82) has its definition here: a stopped trade whose MFE reached 80 %
   of its target (8-17 % of the losers) or +1R (17-32 %); the data says such a trade is not evidence that the stop or
   the target was wrong, so the message should report it and propose nothing.
5. The anatomy repeats the earlier finding with the stop ruled out as the cause: 24-52 % of the losers never see
   +0.25R and 85-96 % run through 1.5 stops. If the win rate is to rise, it is the entry selection (the sweeps in
   `BACKLOG_hand.md` B1-B5, B9) and not the management.

## Appendix: all tables (`research/excursion/tables.md`)

# Excursion tables (generated by report.py)

## 1. The ledgers as they are

| market | trades | won | stopped | break-even | time | sum R | R a trade | median planned R:R | median hold h | stop pips (median) |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 47 | 47 % | 24 | 1 | 0 | 44.20 | 0.94 | 2.12 | 1.20 | 8.10 |
| XAUUSD IS | 143 | 49 % | 71 | 2 | 0 | 86.10 | 0.60 | 2.00 | 2.20 | 85.00 |
| NAS100 IS | 43 | 47 % | 23 | 0 | 1 | 37.20 | 0.87 | 1.67 | 0.90 | 27.50 |
| BTCUSD IS | 89 | 58 % | 37 | 0 | 0 | 70.60 | 0.79 | 1.52 | 1.60 | 446.00 |
| EURUSD OOS | 97 | 26 % | 68 | 4 | 0 | 8.50 | 0.09 | 1.73 | 0.70 | 7.80 |
| XAUUSD OOS | 371 | 30 % | 247 | 14 | 0 | -25.10 | -0.07 | 2.00 | 1.80 | 32.30 |
| NAS100 OOS | 100 | 32 % | 66 | 2 | 2 | 38.80 | 0.39 | 1.81 | 1.80 | 15.60 |
| BTCUSD OOS | 130 | 33 % | 86 | 1 | 0 | -28.60 | -0.22 | 1.41 | 1.40 | 219.00 |

## 2. How close the winners came to the stop (MAE of the trades that reached the target)

| market | winners | MAE median | MAE p75 | MAE p90 | beyond 0.3R | beyond 0.5R | beyond 0.8R | beyond 0.9R | never 0.1R against | hours to MAE (median) | hours to target (median) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 22 | 0.41 | 0.79 | 0.84 | 59 % | 45 % | 23 % | 9 % | 27 % | 0.20 | 2.90 |
| XAUUSD IS | 70 | 0.39 | 0.79 | 0.94 | 64 % | 41 % | 26 % | 16 % | 17 % | 0.30 | 5.10 |
| NAS100 IS | 19 | 0.37 | 0.76 | 0.88 | 53 % | 42 % | 16 % | 11 % | 26 % | 0.20 | 2.10 |
| BTCUSD IS | 52 | 0.40 | 0.62 | 0.87 | 56 % | 35 % | 15 % | 8 % | 19 % | 0.20 | 1.70 |
| EURUSD OOS | 25 | 0.35 | 0.76 | 0.87 | 56 % | 48 % | 20 % | 12 % | 24 % | 0.20 | 4.00 |
| XAUUSD OOS | 110 | 0.50 | 0.76 | 0.88 | 66 % | 50 % | 20 % | 7 % | 5 % | 0.40 | 4.50 |
| NAS100 OOS | 30 | 0.50 | 0.81 | 0.86 | 77 % | 50 % | 27 % | 10 % | 10 % | 0.10 | 3.30 |
| BTCUSD OOS | 43 | 0.41 | 0.70 | 0.84 | 70 % | 40 % | 14 % | 2 % | 7 % | 0.20 | 1.70 |

Reading: the share of winners that went beyond 0.8R against is what a stop 20 % tighter would have turned into losers (and beyond 0.9R a 10 % tighter one); a winner's MAE never reaches 1R by construction.

## 3. How close the losers came to the target (MFE of the stopped trades)

| market | losers | MFE median | never 0.25R | reached 0.5R | reached 1R | reached 1.5R | reached 2R | half way to target | 80 % of the way | 90 % of the way | 90 % incl. exit candle | reached 1R incl. exit candle | R given back (sum of MFE >= 1R) | hours to MFE (median) | hours to stop (median) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 24 | 0.36 | 42 % | 38 % | 29 % | 8 % | 0 % | 25 % | 17 % | 8 % | 8 % | 29 % | 9.30 | 0.20 | 0.50 |
| XAUUSD IS | 71 | 0.59 | 24 % | 58 % | 20 % | 8 % | 0 % | 24 % | 8 % | 3 % | 3 % | 20 % | 19.90 | 0.30 | 1.80 |
| NAS100 IS | 23 | 0.24 | 52 % | 43 % | 17 % | 9 % | 4 % | 22 % | 13 % | 13 % | 13 % | 17 % | 7.90 | 0.00 | 0.40 |
| BTCUSD IS | 37 | 0.59 | 30 % | 54 % | 27 % | 5 % | 0 % | 32 % | 11 % | 3 % | 3 % | 27 % | 13.80 | 0.50 | 1.50 |
| EURUSD OOS | 68 | 0.19 | 51 % | 44 % | 28 % | 15 % | 7 % | 29 % | 16 % | 13 % | 13 % | 29 % | 31.10 | 0.00 | 0.30 |
| XAUUSD OOS | 247 | 0.41 | 40 % | 43 % | 22 % | 7 % | 0 % | 25 % | 5 % | 2 % | 2 % | 23 % | 74.90 | 0.20 | 1.30 |
| NAS100 OOS | 66 | 0.36 | 38 % | 45 % | 32 % | 14 % | 5 % | 29 % | 15 % | 12 % | 14 % | 33 % | 33.90 | 0.20 | 0.60 |
| BTCUSD OOS | 86 | 0.15 | 58 % | 24 % | 9 % | 5 % | 0 % | 19 % | 3 % | 2 % | 2 % | 9 % | 11.50 | 0.20 | 1.30 |

'Gave it back' = a stopped trade whose favourable excursion reached at least 1R (or the given fraction of its own target) before the stop. The exit candle counts the stop only, so a loser's MFE is what the candles before it showed.

## 4. The trades closed by break-even or the time limit: their excursion and where stop/target alone would have ended

| market | id | opened | exit | R | planned R:R | MFE | MAE | hold h | stop/target alone | its R | closed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | P30 | 2025-09-03 11:25 | breakeven | 0.00 | 6.87 | 5.78 | 0.73 | 21.90 | stop | -1.00 | 2025-09-04 12:35 |
| XAUUSD IS | P16 | 2024-04-23 14:55 | breakeven | 0.00 | 9.17 | 2.00 | 0.86 | 17.10 | stop | -1.00 | 2024-04-24 09:15 |
| XAUUSD IS | P105 | 2025-12-23 12:40 | breakeven | 0.00 | 2.85 | 2.68 | 0.35 | 0.80 | stop | -1.00 | 2025-12-23 13:50 |
| NAS100 IS | P8 | 2024-10-18 13:50 | time | 0.68 | 1.37 | 1.01 | 0.78 | 58.20 | stop | -1.00 | 2024-10-21 06:40 |
| EURUSD OOS | P38 | 2020-02-13 16:05 | breakeven | -0.00 | 20.61 | 4.13 | 0.60 | 191.10 | stop | -1.00 | 2020-02-24 17:25 |
| EURUSD OOS | P42 | 2020-06-03 08:10 | breakeven | 0.00 | 5.42 | 5.63 | 0.61 | 342.10 | stop | -1.00 | 2020-06-19 14:55 |
| EURUSD OOS | P53 | 2021-01-26 13:30 | breakeven | 0.00 | 4.03 | 4.51 | 0.27 | 3.30 | stop | -1.00 | 2021-01-27 09:10 |
| EURUSD OOS | P71 | 2022-04-25 08:50 | breakeven | -0.00 | 3.90 | 4.00 | 0.34 | 2.50 | stop | -1.00 | 2022-04-25 12:00 |
| XAUUSD OOS | P32 | 2017-06-26 11:15 | breakeven | -0.00 | 3.58 | 2.95 | 0.25 | 1.20 | stop | -1.00 | 2017-06-26 12:45 |
| XAUUSD OOS | P60 | 2017-12-13 09:35 | breakeven | -0.00 | 6.22 | 2.01 | 0.35 | 3.60 | stop | -1.00 | 2017-12-13 13:30 |
| XAUUSD OOS | P113 | 2018-12-05 15:15 | breakeven | 0.00 | 2.88 | 2.01 | 0.83 | 15.20 | stop | -1.00 | 2018-12-06 07:05 |
| XAUUSD OOS | P136 | 2019-05-15 11:45 | breakeven | 0.00 | 4.46 | 3.03 | 0.55 | 1.20 | stop | -1.00 | 2019-05-15 14:15 |
| XAUUSD OOS | P151 | 2019-08-14 14:30 | breakeven | 0.00 | 3.91 | 2.03 | 0.47 | 16.00 | stop | -1.00 | 2019-08-16 09:10 |
| XAUUSD OOS | P184 | 2020-02-05 12:15 | breakeven | -0.00 | 3.03 | 0.92 | 0.81 | 1.00 | stop | -1.00 | 2020-02-05 14:05 |
| XAUUSD OOS | P243 | 2021-04-30 07:00 | breakeven | -0.00 | 10.54 | 3.07 | 0.68 | 1.40 | stop | -1.00 | 2021-05-03 02:15 |
| XAUUSD OOS | P246 | 2021-05-21 11:35 | breakeven | 0.00 | 3.17 | 2.79 | 0.65 | 2.20 | stop | -1.00 | 2021-05-21 13:50 |
| XAUUSD OOS | P254 | 2021-09-20 13:40 | breakeven | 0.00 | 2.72 | 2.49 | 0.79 | 17.70 | take_profit | 2.59 | 2021-09-21 10:10 |
| XAUUSD OOS | P264 | 2021-11-30 08:05 | breakeven | 0.00 | 3.04 | 2.43 | 0.79 | 3.70 | stop | -1.00 | 2021-11-30 12:25 |
| XAUUSD OOS | P311 | 2022-09-20 08:10 | breakeven | -0.00 | 3.17 | 3.11 | 0.07 | 22.10 | stop | -1.00 | 2022-09-21 06:20 |
| XAUUSD OOS | P318 | 2022-10-27 08:45 | breakeven | -0.00 | 5.04 | 3.01 | 0.23 | 3.70 | stop | -1.00 | 2022-10-28 01:55 |
| XAUUSD OOS | P334 | 2023-02-01 08:45 | breakeven | 0.00 | 2.58 | 2.05 | 0.92 | 6.20 | stop | -1.00 | 2023-02-01 15:00 |
| XAUUSD OOS | P337 | 2023-02-09 08:00 | breakeven | 0.00 | 4.14 | 3.16 | 0.58 | 1.30 | take_profit | 3.71 | 2023-02-09 13:50 |
| NAS100 OOS | P1 | 2017-03-03 15:25 | time | 0.80 | 2.96 | 1.99 | 0.90 | 55.60 | stop | -1.00 | 2017-03-06 15:20 |
| NAS100 OOS | P21 | 2019-05-29 13:45 | time | 1.64 | 3.66 | 1.79 | 0.71 | 48.00 | stop | -1.00 | 2019-06-06 19:30 |
| NAS100 OOS | P66 | 2021-07-16 09:05 | breakeven | 0.00 | 7.86 | 4.81 | 0.01 | 5.00 | stop | -1.00 | 2021-07-16 14:10 |
| NAS100 OOS | P81 | 2022-09-08 12:20 | breakeven | -0.00 | 14.97 | 9.39 | 0.00 | 2.00 | stop | -1.00 | 2022-09-08 14:35 |
| BTCUSD OOS | P87 | 2022-08-15 11:20 | breakeven | -0.00 | 7.27 | 5.19 | 0.81 | 14.00 | stop | -1.00 | 2022-08-17 06:00 |

| market | n | ledger R | stop/target alone R | of them to the target | to the stop | still open after 30 d |
|---|---|---|---|---|---|---|
| EURUSD IS | 1 | 0.00 | -1.00 | 0 | 1 | 0 |
| XAUUSD IS | 2 | 0.00 | -2.00 | 0 | 2 | 0 |
| NAS100 IS | 1 | 0.70 | -1.00 | 0 | 1 | 0 |
| EURUSD OOS | 4 | 0.00 | -4.00 | 0 | 4 | 0 |
| XAUUSD OOS | 14 | 0.00 | -5.70 | 2 | 12 | 0 |
| NAS100 OOS | 4 | 2.40 | -4.00 | 0 | 4 | 0 |
| BTCUSD OOS | 1 | 0.00 | -1.00 | 0 | 1 | 0 |

## 5. Target reach by planned R:R band


### IS

| market | R:R band | trades | reached target | stopped | sum R | R a trade | losers' MFE median | losers half way | break-even odds |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 1-1.5 | 12 | 67 % | 33 % | 12.30 | 1.02 | 1.19 | 100 % | 43 % |
| EURUSD IS | 1.5-2 | 9 | 67 % | 33 % | 12.60 | 1.40 | 0.15 | 0 % | 38 % |
| EURUSD IS | 2-3 | 11 | 36 % | 64 % | 6.60 | 0.60 | 0.40 | 14 % | 29 % |
| EURUSD IS | 3-5 | 11 | 27 % | 73 % | 6.50 | 0.59 | 0.17 | 12 % | 23 % |
| EURUSD IS | >5 | 4 | 25 % | 50 % | 6.30 | 1.57 | 0.23 | 0 % | 13 % |
| XAUUSD IS | <1 | 7 | 57 % | 43 % | 0.30 | 0.04 | 0.64 | 100 % | 53 % |
| XAUUSD IS | 1-1.5 | 20 | 50 % | 50 % | 1.80 | 0.09 | 0.39 | 40 % | 45 % |
| XAUUSD IS | 1.5-2 | 11 | 36 % | 64 % | -0.10 | -0.01 | 0.24 | 14 % | 37 % |
| XAUUSD IS | 2-3 | 81 | 51 % | 48 % | 43.80 | 0.54 | 0.60 | 23 % | 33 % |
| XAUUSD IS | 3-5 | 13 | 54 % | 46 % | 21.80 | 1.68 | 0.83 | 0 % | 20 % |
| XAUUSD IS | >5 | 11 | 36 % | 55 % | 18.50 | 1.69 | 0.63 | 0 % | 13 % |
| NAS100 IS | <1 | 5 | 40 % | 60 % | -0.00 | -0.00 | 0.54 | 67 % | 52 % |
| NAS100 IS | 1-1.5 | 12 | 33 % | 58 % | 1.60 | 0.13 | 0.04 | 14 % | 44 % |
| NAS100 IS | 1.5-2 | 8 | 62 % | 38 % | 9.60 | 1.21 | 0.00 | 0 % | 38 % |
| NAS100 IS | 2-3 | 8 | 50 % | 50 % | 9.90 | 1.24 | 1.05 | 50 % | 30 % |
| NAS100 IS | 3-5 | 6 | 50 % | 50 % | 11.30 | 1.88 | 0.90 | 0 % | 22 % |
| NAS100 IS | >5 | 4 | 25 % | 75 % | 4.70 | 1.18 | 0.04 | 0 % | 9 % |
| BTCUSD IS | <1 | 20 | 90 % | 10 % | 10.70 | 0.53 | 0.33 | 50 % | 56 % |
| BTCUSD IS | 1-1.5 | 24 | 62 % | 38 % | 8.70 | 0.36 | 0.08 | 22 % | 45 % |
| BTCUSD IS | 1.5-2 | 11 | 18 % | 82 % | -5.30 | -0.48 | 0.88 | 56 % | 37 % |
| BTCUSD IS | 2-3 | 28 | 50 % | 50 % | 20.40 | 0.73 | 0.78 | 29 % | 28 % |
| BTCUSD IS | 3-5 | 3 | 33 % | 67 % | 1.50 | 0.51 | 0.36 | 0 % | 21 % |
| BTCUSD IS | >5 | 3 | 67 % | 33 % | 34.70 | 11.55 | 0.71 | 0 % | 6 % |

### OOS

| market | R:R band | trades | reached target | stopped | sum R | R a trade | losers' MFE median | losers half way | break-even odds |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD OOS | 1-1.5 | 34 | 41 % | 59 % | 7.60 | 0.22 | 0.81 | 60 % | 46 % |
| EURUSD OOS | 1.5-2 | 16 | 25 % | 75 % | -2.10 | -0.13 | 0.19 | 33 % | 38 % |
| EURUSD OOS | 2-3 | 20 | 15 % | 85 % | -6.80 | -0.34 | 0.17 | 12 % | 30 % |
| EURUSD OOS | 3-5 | 19 | 16 % | 74 % | 1.70 | 0.09 | 0.25 | 14 % | 21 % |
| EURUSD OOS | >5 | 8 | 12 % | 62 % | 8.10 | 1.01 | 0.00 | 0 % | 15 % |
| XAUUSD OOS | <1 | 16 | 31 % | 69 % | -6.30 | -0.39 | 0.35 | 36 % | 52 % |
| XAUUSD OOS | 1-1.5 | 51 | 49 % | 51 % | 3.30 | 0.06 | 0.29 | 27 % | 45 % |
| XAUUSD OOS | 1.5-2 | 23 | 39 % | 61 % | 1.20 | 0.05 | 0.50 | 36 % | 38 % |
| XAUUSD OOS | 2-3 | 224 | 27 % | 72 % | -42.10 | -0.19 | 0.44 | 28 % | 33 % |
| XAUUSD OOS | 3-5 | 30 | 20 % | 53 % | 6.10 | 0.20 | 0.21 | 0 % | 22 % |
| XAUUSD OOS | >5 | 27 | 19 % | 70 % | 12.60 | 0.47 | 0.17 | 0 % | 12 % |
| NAS100 OOS | <1 | 9 | 44 % | 56 % | 1.40 | 0.15 | 0.10 | 40 % | 52 % |
| NAS100 OOS | 1-1.5 | 28 | 36 % | 64 % | -1.00 | -0.04 | 0.49 | 39 % | 46 % |
| NAS100 OOS | 1.5-2 | 19 | 26 % | 74 % | -1.50 | -0.08 | 0.31 | 29 % | 37 % |
| NAS100 OOS | 2-3 | 15 | 27 % | 67 % | 3.70 | 0.25 | 0.93 | 30 % | 31 % |
| NAS100 OOS | 3-5 | 18 | 22 % | 72 % | 12.50 | 0.70 | 0.29 | 15 % | 20 % |
| NAS100 OOS | >5 | 11 | 27 % | 55 % | 23.70 | 2.16 | 0.07 | 17 % | 12 % |
| BTCUSD OOS | <1 | 36 | 44 % | 56 % | -8.50 | -0.24 | 0.14 | 25 % | 55 % |
| BTCUSD OOS | 1-1.5 | 32 | 38 % | 62 % | -6.10 | -0.19 | 0.13 | 15 % | 45 % |
| BTCUSD OOS | 1.5-2 | 21 | 38 % | 62 % | 0.70 | 0.04 | 0.40 | 38 % | 37 % |
| BTCUSD OOS | 2-3 | 32 | 22 % | 78 % | -6.70 | -0.21 | 0.22 | 12 % | 28 % |
| BTCUSD OOS | 3-5 | 2 | 0 % | 100 % | -2.00 | -1.00 | 0.10 | 0 % | 20 % |
| BTCUSD OOS | >5 | 7 | 0 % | 86 % | -6.00 | -0.86 | 0.11 | 0 % | 14 % |

'break-even odds' = the win rate at which the band's median R:R pays for itself before costs (1 / (1 + R:R)).

## 6. A wider (or tighter) stop on the same trades, the cash at risk constant

R counted in the new stop distance (the position shrinks with the stop); gold's fixed-2R targets move with the stop, every other target is the same price level. 'all' keeps every trade; 'min R:R' drops the trades whose new R:R falls under the profile's minimum (the engine would not take them; +0.10R of costs saved each). 'saved' = stopped trades that reach the target with the new stop; 'overlap' = trades that now close after the next trade's open (the engine, one open trade per market, would have skipped that next trade).


### IS

| market | stop x | ledger R | all trades R | delta | won | min R:R: trades | min R:R R | delta + costs | saved | their gain | winners' cost | winners now stopped | overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 0.80 | 44.20 | 37.70 | -6.60 | 36 % | 47 | 37.70 | -6.60 | 0 | 0.00 | -6.60 | 5 | 0 |
| EURUSD IS | 0.90 | 44.20 | 41.80 | -2.50 | 43 % | 47 | 41.80 | -2.50 | 0 | 0.00 | -2.50 | 2 | 0 |
| EURUSD IS | 1.10 | 44.20 | 38.00 | -6.20 | 47 % | 47 | 38.00 | -6.20 | 0 | 0.00 | -6.20 | 0 | 0 |
| EURUSD IS | 1.20 | 44.20 | 32.90 | -11.40 | 47 % | 47 | 32.90 | -11.40 | 0 | 0.00 | -11.40 | 0 | 1 |
| EURUSD IS | 1.30 | 44.20 | 31.90 | -12.40 | 49 % | 47 | 31.90 | -12.40 | 1 | 3.40 | -15.70 | 0 | 3 |
| EURUSD IS | 1.50 | 44.20 | 23.50 | -20.70 | 49 % | 47 | 23.50 | -20.70 | 1 | 3.00 | -22.70 | 0 | 3 |
| XAUUSD IS | 0.80 | 86.10 | 58.80 | -27.40 | 38 % | 143 | 58.80 | -27.40 | 3 | 9.00 | -36.40 | 16 | 0 |
| XAUUSD IS | 0.90 | 86.10 | 59.50 | -26.60 | 42 % | 143 | 59.50 | -26.60 | 1 | 3.00 | -29.60 | 11 | 0 |
| XAUUSD IS | 1.10 | 86.10 | 81.30 | -4.80 | 50 % | 139 | 78.30 | -7.40 | 2 | 6.00 | -9.80 | 1 | 2 |
| XAUUSD IS | 1.20 | 86.10 | 73.60 | -12.50 | 50 % | 136 | 73.90 | -11.50 | 3 | 8.00 | -19.50 | 2 | 2 |
| XAUUSD IS | 1.30 | 86.10 | 65.90 | -20.20 | 49 % | 129 | 66.30 | -18.40 | 5 | 14.00 | -34.20 | 5 | 4 |
| XAUUSD IS | 1.50 | 86.10 | 67.00 | -19.10 | 52 % | 125 | 68.70 | -15.70 | 10 | 27.10 | -46.20 | 6 | 5 |
| NAS100 IS | 0.80 | 37.20 | 38.40 | 1.20 | 40 % | 43 | 38.40 | 1.20 | 0 | 0.00 | 1.00 | 3 | 0 |
| NAS100 IS | 0.90 | 37.20 | 37.70 | 0.50 | 42 % | 43 | 37.70 | 0.50 | 0 | 0.00 | -0.50 | 2 | 0 |
| NAS100 IS | 1.10 | 37.20 | 32.70 | -4.50 | 47 % | 43 | 32.70 | -4.50 | 0 | 0.00 | -5.40 | 0 | 0 |
| NAS100 IS | 1.20 | 37.20 | 28.20 | -9.00 | 47 % | 43 | 28.20 | -9.00 | 0 | 0.00 | -9.90 | 0 | 0 |
| NAS100 IS | 1.30 | 37.20 | 32.90 | -4.30 | 51 % | 43 | 32.90 | -4.30 | 1 | 2.80 | -13.70 | 0 | 0 |
| NAS100 IS | 1.50 | 37.20 | 25.90 | -11.30 | 51 % | 43 | 25.90 | -11.30 | 1 | 2.60 | -19.80 | 0 | 0 |
| BTCUSD IS | 0.80 | 70.60 | 24.30 | -46.30 | 46 % | 89 | 24.30 | -46.30 | 0 | 0.00 | -46.30 | 10 | 0 |
| BTCUSD IS | 0.90 | 70.60 | 37.10 | -33.50 | 54 % | 89 | 37.10 | -33.50 | 0 | 0.00 | -33.50 | 4 | 0 |
| BTCUSD IS | 1.10 | 70.60 | 62.70 | -7.90 | 60 % | 86 | 61.30 | -9.00 | 1 | 1.90 | -9.80 | 0 | 1 |
| BTCUSD IS | 1.20 | 70.60 | 56.30 | -14.30 | 61 % | 84 | 54.00 | -16.10 | 2 | 3.60 | -17.90 | 0 | 1 |
| BTCUSD IS | 1.30 | 70.60 | 55.20 | -15.40 | 63 % | 80 | 51.10 | -18.60 | 4 | 9.40 | -24.80 | 0 | 1 |
| BTCUSD IS | 1.50 | 70.60 | 43.40 | -27.20 | 63 % | 79 | 39.50 | -30.10 | 4 | 8.70 | -35.90 | 0 | 1 |

### OOS

| market | stop x | ledger R | all trades R | delta | won | min R:R: trades | min R:R R | delta + costs | saved | their gain | winners' cost | winners now stopped | overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD OOS | 0.80 | 8.50 | 5.00 | -3.50 | 21 % | 97 | 5.00 | -3.50 | 0 | 0.00 | -3.50 | 5 | 0 |
| EURUSD OOS | 0.90 | 8.50 | 3.70 | -4.80 | 23 % | 97 | 3.70 | -4.80 | 0 | 0.00 | -4.80 | 3 | 0 |
| EURUSD OOS | 1.10 | 8.50 | 2.90 | -5.60 | 27 % | 97 | 2.90 | -5.60 | 1 | 3.40 | -7.00 | 0 | 1 |
| EURUSD OOS | 1.20 | 8.50 | 9.00 | 0.60 | 30 % | 97 | 9.00 | 0.60 | 4 | 15.30 | -12.70 | 0 | 3 |
| EURUSD OOS | 1.30 | 8.50 | 6.80 | -1.60 | 31 % | 97 | 6.80 | -1.60 | 5 | 18.00 | -17.60 | 0 | 3 |
| EURUSD OOS | 1.50 | 8.50 | 4.60 | -3.90 | 35 % | 97 | 4.60 | -3.90 | 8 | 23.10 | -25.50 | 0 | 4 |
| XAUUSD OOS | 0.80 | -25.10 | -56.10 | -31.00 | 25 % | 371 | -56.10 | -31.00 | 5 | 15.00 | -46.80 | 21 | 0 |
| XAUUSD OOS | 0.90 | -25.10 | -31.20 | -6.10 | 28 % | 371 | -31.20 | -6.10 | 3 | 9.00 | -15.70 | 7 | 0 |
| XAUUSD OOS | 1.10 | -25.10 | -28.90 | -3.80 | 30 % | 365 | -24.70 | 1.00 | 4 | 10.90 | -12.00 | 1 | 11 |
| XAUUSD OOS | 1.20 | -25.10 | -19.10 | 6.00 | 32 % | 357 | -10.30 | 16.20 | 11 | 31.70 | -24.10 | 2 | 17 |
| XAUUSD OOS | 1.30 | -25.10 | -14.00 | 11.10 | 33 % | 341 | -6.80 | 21.30 | 16 | 46.80 | -34.80 | 3 | 24 |
| XAUUSD OOS | 1.50 | -25.10 | -21.10 | 4.00 | 35 % | 326 | -16.60 | 13.00 | 20 | 54.30 | -47.20 | 3 | 33 |
| NAS100 OOS | 0.80 | 38.80 | 34.80 | -3.90 | 23 % | 100 | 34.80 | -3.90 | 0 | 0.00 | -3.20 | 8 | 0 |
| NAS100 OOS | 0.90 | 38.80 | 36.80 | -2.00 | 28 % | 100 | 36.80 | -2.00 | 0 | 0.00 | 0.80 | 3 | 0 |
| NAS100 OOS | 1.10 | 38.80 | 29.00 | -9.80 | 32 % | 100 | 29.00 | -9.80 | 0 | 0.00 | -9.30 | 0 | 0 |
| NAS100 OOS | 1.20 | 38.80 | 21.30 | -17.50 | 32 % | 100 | 21.30 | -17.50 | 0 | 0.00 | -17.10 | 0 | 0 |
| NAS100 OOS | 1.30 | 38.80 | 26.30 | -12.40 | 36 % | 100 | 26.30 | -12.40 | 4 | 12.60 | -23.70 | 0 | 1 |
| NAS100 OOS | 1.50 | 38.80 | 21.40 | -17.40 | 39 % | 100 | 21.40 | -17.40 | 6 | 16.90 | -34.20 | 0 | 1 |
| BTCUSD OOS | 0.80 | -28.60 | -33.90 | -5.30 | 28 % | 130 | -33.90 | -5.30 | 0 | 0.00 | -5.30 | 6 | 0 |
| BTCUSD OOS | 0.90 | -28.60 | -26.60 | 2.00 | 32 % | 130 | -26.60 | 2.00 | 0 | 0.00 | 2.20 | 1 | 0 |
| BTCUSD OOS | 1.10 | -28.60 | -26.30 | 2.40 | 35 % | 126 | -25.20 | 3.80 | 3 | 7.60 | -5.20 | 0 | 1 |
| BTCUSD OOS | 1.20 | -28.60 | -27.60 | 1.00 | 37 % | 125 | -27.00 | 2.10 | 5 | 10.50 | -9.60 | 0 | 1 |
| BTCUSD OOS | 1.30 | -28.60 | -30.00 | -1.40 | 38 % | 119 | -32.10 | -2.30 | 6 | 11.90 | -13.20 | 0 | 1 |
| BTCUSD OOS | 1.50 | -28.60 | -25.60 | 3.00 | 42 % | 112 | -24.40 | 6.00 | 12 | 22.10 | -19.10 | 0 | 4 |

### Stop variants by year (all trades, delta R against the ledger)

| market | stop x | 2024 | 2025 | 2026 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 0.90 | -4.20 | 3.50 | -1.80 |  |  |  |  |  |  |  |
| EURUSD IS | 1.10 | -1.40 | -2.90 | -1.90 |  |  |  |  |  |  |  |
| EURUSD IS | 1.20 | -2.60 | -5.30 | -3.50 |  |  |  |  |  |  |  |
| EURUSD IS | 1.30 | -3.60 | -7.30 | -1.50 |  |  |  |  |  |  |  |
| XAUUSD IS | 0.90 | -4.90 | -9.30 | -12.40 |  |  |  |  |  |  |  |
| XAUUSD IS | 1.10 | -2.80 | -1.50 | -0.60 |  |  |  |  |  |  |  |
| XAUUSD IS | 1.20 | -4.70 | -3.20 | -4.50 |  |  |  |  |  |  |  |
| XAUUSD IS | 1.30 | -3.40 | -6.70 | -10.10 |  |  |  |  |  |  |  |
| NAS100 IS | 0.90 | 0.90 | 2.20 | -2.60 |  |  |  |  |  |  |  |
| NAS100 IS | 1.10 | -0.70 | -1.80 | -1.90 |  |  |  |  |  |  |  |
| NAS100 IS | 1.20 | -1.40 | -3.30 | -4.40 |  |  |  |  |  |  |  |
| NAS100 IS | 1.30 | 3.90 | -1.70 | -6.50 |  |  |  |  |  |  |  |
| BTCUSD IS | 0.90 | 1.90 | 0.80 | -36.20 |  |  |  |  |  |  |  |
| BTCUSD IS | 1.10 | -1.50 | -2.00 | -4.40 |  |  |  |  |  |  |  |
| BTCUSD IS | 1.20 | -4.40 | -3.70 | -6.30 |  |  |  |  |  |  |  |
| BTCUSD IS | 1.30 | -6.80 | -1.20 | -7.40 |  |  |  |  |  |  |  |
| EURUSD OOS | 0.90 |  |  |  | -1.20 | 1.50 | 0.50 | -5.50 | 1.00 | 0.60 | -1.60 |
| EURUSD OOS | 1.10 |  |  |  | -1.70 | -1.20 | 3.00 | -2.20 | -0.80 | -1.50 | -1.10 |
| EURUSD OOS | 1.20 |  |  |  | -3.20 | -1.20 | 2.40 | 0.40 | 6.00 | -1.90 | -2.00 |
| EURUSD OOS | 1.30 |  |  |  | -4.40 | -2.00 | 2.00 | 2.90 | 4.90 | -2.30 | -2.80 |
| XAUUSD OOS | 0.90 |  |  |  | 2.10 | -1.30 | 5.90 | -1.20 | -2.70 | -1.80 | -7.10 |
| XAUUSD OOS | 1.10 |  |  |  | -2.10 | -4.20 | -1.30 | -0.20 | 0.90 | 6.20 | -3.20 |
| XAUUSD OOS | 1.20 |  |  |  | 2.90 | -1.90 | -1.80 | 2.10 | -0.00 | 3.90 | 1.00 |
| XAUUSD OOS | 1.30 |  |  |  | 2.50 | -2.60 | -0.90 | 10.90 | 0.10 | 2.00 | -1.00 |
| NAS100 OOS | 0.90 |  |  |  | -1.60 | 0.80 | -0.50 | -4.10 | 3.20 | -1.90 | 2.10 |
| NAS100 OOS | 1.10 |  |  |  | -0.60 | -0.70 | -1.90 | -0.70 | -2.70 | -1.50 | -1.80 |
| NAS100 OOS | 1.20 |  |  |  | -0.60 | -1.20 | -3.50 | -1.30 | -4.90 | -2.80 | -3.20 |
| NAS100 OOS | 1.30 |  |  |  | -0.70 | 5.10 | -4.80 | 1.30 | -7.70 | -1.10 | -4.50 |
| BTCUSD OOS | 0.90 |  |  |  |  |  |  | 0.80 | 0.90 | -1.60 | 2.00 |
| BTCUSD OOS | 1.10 |  |  |  |  |  |  | -0.60 | -0.80 | 5.40 | -1.60 |
| BTCUSD OOS | 1.20 |  |  |  |  |  |  | 0.60 | 0.20 | 3.20 | -3.00 |
| BTCUSD OOS | 1.30 |  |  |  |  |  |  | 0.10 | 1.30 | 1.30 | -4.20 |

## 7. A nearer target on the same trades

The target moved the given share of its distance toward the entry; the stop unchanged. 'rescued' = stopped trades that reach the nearer target; 'winners' cost' = what the winners give up (each loses y x its R:R); 'min R:R' drops the trades whose nearer target falls under the profile's minimum R:R.


### IS

| market | target nearer | ledger R | all trades R | delta | won | rescued losers | their gain | rescued break-evens | winners' cost | min R:R: trades | min R:R R | delta + costs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 5 % | 44.20 | 40.80 | -3.40 | 47 % | 0 | 0.00 | 0 | -3.40 | 46 | 39.10 | -5.10 |
| EURUSD IS | 10 % | 44.20 | 37.40 | -6.80 | 47 % | 0 | 0.00 | 0 | -6.80 | 45 | 34.00 | -10.00 |
| EURUSD IS | 20 % | 44.20 | 30.60 | -13.60 | 47 % | 0 | 0.00 | 0 | -13.60 | 44 | 28.60 | -15.40 |
| EURUSD IS | 30 % | 44.20 | 23.80 | -20.50 | 47 % | 0 | 0.00 | 0 | -20.50 | 36 | 17.90 | -25.20 |
| XAUUSD IS | 5 % | 86.10 | 86.60 | 0.50 | 51 % | 2 | 5.80 | 1 | -7.90 | 142 | 85.90 | -0.20 |
| XAUUSD IS | 10 % | 86.10 | 81.10 | -5.00 | 52 % | 3 | 8.20 | 1 | -15.70 | 140 | 78.90 | -6.90 |
| XAUUSD IS | 20 % | 86.10 | 70.90 | -15.20 | 54 % | 6 | 14.00 | 1 | -31.40 | 136 | 69.50 | -15.90 |
| XAUUSD IS | 30 % | 86.10 | 62.50 | -23.60 | 57 % | 10 | 21.60 | 1 | -47.10 | 128 | 59.40 | -25.30 |
| NAS100 IS | 5 % | 37.20 | 37.10 | -0.10 | 49 % | 1 | 2.90 | 0 | -3.00 | 42 | 35.70 | -1.40 |
| NAS100 IS | 10 % | 37.20 | 34.00 | -3.20 | 49 % | 1 | 2.80 | 0 | -6.00 | 42 | 32.70 | -4.40 |
| NAS100 IS | 20 % | 37.20 | 32.30 | -4.90 | 51 % | 2 | 7.00 | 0 | -11.90 | 38 | 32.90 | -3.80 |
| NAS100 IS | 30 % | 37.20 | 25.70 | -11.50 | 51 % | 2 | 6.40 | 0 | -17.90 | 34 | 30.70 | -5.60 |
| BTCUSD IS | 5 % | 70.60 | 67.50 | -3.10 | 60 % | 1 | 2.20 | 0 | -5.40 | 89 | 67.50 | -3.10 |
| BTCUSD IS | 10 % | 70.60 | 64.40 | -6.20 | 61 % | 2 | 4.60 | 0 | -10.80 | 88 | 64.00 | -6.50 |
| BTCUSD IS | 20 % | 70.60 | 57.90 | -12.70 | 63 % | 4 | 8.80 | 0 | -21.50 | 84 | 55.70 | -14.40 |
| BTCUSD IS | 30 % | 70.60 | 49.30 | -21.30 | 64 % | 5 | 11.00 | 0 | -32.30 | 80 | 45.60 | -24.10 |

### OOS

| market | target nearer | ledger R | all trades R | delta | won | rescued losers | their gain | rescued break-evens | winners' cost | min R:R: trades | min R:R R | delta + costs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD OOS | 5 % | 8.50 | 7.30 | -1.10 | 27 % | 1 | 2.70 | 0 | -3.80 | 92 | 6.90 | -1.10 |
| EURUSD OOS | 10 % | 8.50 | 6.10 | -2.40 | 28 % | 2 | 5.30 | 0 | -7.60 | 87 | 3.00 | -4.40 |
| EURUSD OOS | 20 % | 8.50 | 2.60 | -5.90 | 29 % | 2 | 4.90 | 1 | -15.30 | 77 | -2.10 | -8.60 |
| EURUSD OOS | 30 % | 8.50 | 8.90 | 0.50 | 34 % | 6 | 14.20 | 2 | -22.90 | 65 | -3.90 | -9.10 |
| XAUUSD OOS | 5 % | -25.10 | -24.80 | 0.30 | 31 % | 2 | 5.90 | 2 | -11.10 | 367 | -22.60 | 2.90 |
| XAUUSD OOS | 10 % | -25.10 | -20.90 | 4.20 | 32 % | 7 | 18.50 | 3 | -22.30 | 364 | -17.40 | 8.40 |
| XAUUSD OOS | 20 % | -25.10 | -26.80 | -1.70 | 35 % | 11 | 26.00 | 7 | -44.50 | 355 | -21.30 | 5.40 |
| XAUUSD OOS | 30 % | -25.10 | -15.60 | 9.50 | 39 % | 24 | 54.40 | 10 | -66.80 | 337 | -12.30 | 16.20 |
| NAS100 OOS | 5 % | 38.80 | 41.40 | 2.60 | 35 % | 3 | 7.70 | 0 | -5.10 | 99 | 40.00 | 1.30 |
| NAS100 OOS | 10 % | 38.80 | 36.00 | -2.80 | 35 % | 3 | 7.50 | 0 | -10.30 | 99 | 34.70 | -4.00 |
| NAS100 OOS | 20 % | 38.80 | 25.20 | -13.60 | 35 % | 3 | 7.00 | 0 | -20.50 | 91 | 22.90 | -14.90 |
| NAS100 OOS | 30 % | 38.80 | 19.50 | -19.30 | 37 % | 5 | 11.50 | 0 | -30.80 | 82 | 14.50 | -22.50 |
| BTCUSD OOS | 5 % | -28.60 | -24.20 | 4.50 | 35 % | 3 | 7.30 | 0 | -2.90 | 127 | -22.60 | 6.30 |
| BTCUSD OOS | 10 % | -28.60 | -27.20 | 1.40 | 35 % | 3 | 7.10 | 0 | -5.70 | 127 | -25.70 | 3.20 |
| BTCUSD OOS | 20 % | -28.60 | -32.00 | -3.40 | 36 % | 4 | 8.10 | 0 | -11.50 | 123 | -33.80 | -4.40 |
| BTCUSD OOS | 30 % | -28.60 | -26.80 | 1.80 | 39 % | 7 | 13.90 | 1 | -17.20 | 119 | -28.50 | 1.20 |

### Target variants by year (all trades, delta R against the ledger)

| market | nearer | 2024 | 2025 | 2026 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 5 % | -0.80 | -1.60 | -1.00 |  |  |  |  |  |  |  |
| EURUSD IS | 10 % | -1.60 | -3.20 | -2.10 |  |  |  |  |  |  |  |
| EURUSD IS | 20 % | -3.10 | -6.30 | -4.20 |  |  |  |  |  |  |  |
| XAUUSD IS | 5 % | -2.70 | 3.00 | 0.20 |  |  |  |  |  |  |  |
| XAUUSD IS | 10 % | -2.70 | 0.40 | -2.70 |  |  |  |  |  |  |  |
| XAUUSD IS | 20 % | -8.20 | -1.20 | -5.80 |  |  |  |  |  |  |  |
| NAS100 IS | 5 % | -0.40 | 1.90 | -1.60 |  |  |  |  |  |  |  |
| NAS100 IS | 10 % | -0.70 | 0.80 | -3.20 |  |  |  |  |  |  |  |
| NAS100 IS | 20 % | -1.50 | -1.40 | -2.00 |  |  |  |  |  |  |  |
| BTCUSD IS | 5 % | -1.90 | -1.10 | -0.20 |  |  |  |  |  |  |  |
| BTCUSD IS | 10 % | -3.70 | 0.20 | -2.70 |  |  |  |  |  |  |  |
| BTCUSD IS | 20 % | -5.30 | 0.20 | -7.60 |  |  |  |  |  |  |  |
| EURUSD OOS | 5 % |  |  |  | 1.80 | -0.70 | -0.20 | -0.70 | -0.40 | -0.30 | -0.60 |
| EURUSD OOS | 10 % |  |  |  | 0.70 | -1.30 | -0.40 | 1.30 | -0.90 | -0.60 | -1.20 |
| EURUSD OOS | 20 % |  |  |  | -1.40 | -2.60 | -0.90 | -0.20 | 2.80 | -1.10 | -2.40 |
| XAUUSD OOS | 5 % |  |  |  | -2.00 | 1.50 | -1.60 | -1.40 | 1.70 | 1.30 | 0.80 |
| XAUUSD OOS | 10 % |  |  |  | -1.00 | -0.10 | 1.80 | -2.70 | 3.50 | 1.40 | 1.40 |
| XAUUSD OOS | 20 % |  |  |  | -3.50 | 1.80 | -1.80 | -2.80 | 3.60 | -0.70 | 1.60 |
| NAS100 OOS | 5 % |  |  |  | -0.20 | -0.40 | -1.00 | 2.20 | 1.30 | 1.60 | -1.00 |
| NAS100 OOS | 10 % |  |  |  | -0.30 | -0.70 | -1.90 | 1.70 | -0.30 | 0.70 | -1.90 |
| NAS100 OOS | 20 % |  |  |  | -0.60 | -1.50 | -3.90 | 0.70 | -3.40 | -1.10 | -3.90 |
| BTCUSD OOS | 5 % |  |  |  |  |  |  | 1.70 | 2.10 | 1.60 | -0.90 |
| BTCUSD OOS | 10 % |  |  |  |  |  |  | 1.30 | 1.60 | 0.30 | -1.80 |
| BTCUSD OOS | 20 % |  |  |  |  |  |  | 1.90 | 0.50 | -2.30 | -3.60 |

## 8. Break-even at +1R / +1.5R / +2R / +3R / +4R / none on the same trades

The ledger's own rule: EURUSD, NAS100, BTC 4R; gold 2R (NAS100 keeps its 48 h close in every variant).


### IS

| market | ledger | BE 1 | BE 1.5 | BE 2 | BE 3 | BE 4 | BE none |
|---|---|---|---|---|---|---|---|
| EURUSD IS | +44.2R (4R) | +17.0R (-27.3, 17 at 0, won 28 %) | +21.9R (-22.4, 9 at 0, won 34 %) | +31.5R (-12.7, 3 at 0, won 43 %) | +44.2R (+0.0, 1 at 0, won 47 %) | +44.2R (+0.0, 1 at 0, won 47 %) | +43.2R (-1.0, 0 at 0, won 47 %) |
| XAUUSD IS | +86.1R (2R) | +57.0R (-29.1, 33 at 0, won 37 %) | +76.2R (-9.9, 14 at 0, won 45 %) | +86.1R (-0.0, 2 at 0, won 49 %) | +84.1R (-2.0, 0 at 0, won 49 %) | +84.1R (-2.0, 0 at 0, won 49 %) | +84.1R (-2.0, 0 at 0, won 49 %) |
| NAS100 IS | +37.2R (4R) | +21.3R (-15.9, 11 at 0, won 30 %) | +25.1R (-12.1, 7 at 0, won 35 %) | +32.7R (-4.5, 3 at 0, won 42 %) | +38.2R (+1.0, 1 at 0, won 47 %) | +37.2R (+0.0, 0 at 0, won 47 %) | +37.2R (+0.0, 0 at 0, won 47 %) |
| BTCUSD IS | +70.6R (4R) | +60.7R (-9.9, 19 at 0, won 48 %) | +64.0R (-6.6, 5 at 0, won 55 %) | +67.1R (-3.5, 1 at 0, won 57 %) | +67.1R (-3.5, 1 at 0, won 57 %) | +70.6R (+0.0, 0 at 0, won 58 %) | +70.6R (+0.0, 0 at 0, won 58 %) |

### OOS

| market | ledger | BE 1 | BE 1.5 | BE 2 | BE 3 | BE 4 | BE none |
|---|---|---|---|---|---|---|---|
| EURUSD OOS | +8.5R (4R) | -9.4R (-17.9, 34 at 0, won 14 %) | +1.2R (-7.3, 19 at 0, won 21 %) | +1.0R (-7.4, 12 at 0, won 23 %) | +8.5R (+0.0, 4 at 0, won 26 %) | +8.5R (+0.0, 4 at 0, won 26 %) | +4.5R (-4.0, 0 at 0, won 26 %) |
| XAUUSD OOS | -25.1R (2R) | -67.1R (-42.0, 108 at 0, won 19 %) | -40.0R (-14.9, 47 at 0, won 26 %) | -25.1R (+0.0, 14 at 0, won 30 %) | -30.5R (-5.4, 5 at 0, won 30 %) | -29.8R (-4.7, 1 at 0, won 30 %) | -30.8R (-5.7, 0 at 0, won 30 %) |
| NAS100 OOS | +38.8R (4R) | +26.4R (-12.4, 32 at 0, won 23 %) | +37.1R (-1.7, 14 at 0, won 29 %) | +38.2R (-0.6, 6 at 0, won 31 %) | +40.8R (+2.0, 4 at 0, won 32 %) | +38.8R (+0.0, 2 at 0, won 32 %) | +36.8R (-2.0, 0 at 0, won 32 %) |
| BTCUSD OOS | -28.6R (4R) | -26.4R (+2.3, 12 at 0, won 31 %) | -28.8R (-0.2, 7 at 0, won 32 %) | -28.6R (+0.0, 1 at 0, won 33 %) | -28.6R (+0.0, 1 at 0, won 33 %) | -28.6R (+0.0, 1 at 0, won 33 %) | -29.6R (-1.0, 0 at 0, won 33 %) |

### What a break-even at +1R and +2R does trade by trade (against stop/target alone: no break-even)

| market | break-even | no-BE R | with BE R | delta | losers turned to 0 | R saved | winners cut to 0 | R lost |
|---|---|---|---|---|---|---|---|---|
| EURUSD IS | +1R | 43.20 | 17.00 | -26.30 | 8 | 8.00 | 9 | -34.30 |
| EURUSD IS | +2R | 43.20 | 31.50 | -11.70 | 1 | 1.00 | 2 | -12.70 |
| EURUSD IS | +3R | 43.20 | 44.20 | 1.00 | 1 | 1.00 | 0 | -0.00 |
| XAUUSD IS | +1R | 84.10 | 57.00 | -27.10 | 16 | 16.00 | 17 | -43.10 |
| XAUUSD IS | +2R | 84.10 | 86.10 | 2.00 | 2 | 2.00 | 0 | -0.00 |
| XAUUSD IS | +3R | 84.10 | 84.10 | 0.00 | 0 | 0.00 | 0 | -0.00 |
| NAS100 IS | +1R | 37.20 | 21.30 | -15.90 | 4 | 4.00 | 6 | -19.20 |
| NAS100 IS | +2R | 37.20 | 32.70 | -4.50 | 1 | 1.00 | 2 | -5.50 |
| NAS100 IS | +3R | 37.20 | 38.20 | 1.00 | 1 | 1.00 | 0 | -0.00 |
| BTCUSD IS | +1R | 70.60 | 60.70 | -9.90 | 10 | 10.00 | 9 | -19.90 |
| BTCUSD IS | +2R | 70.60 | 67.10 | -3.50 | 0 | 0.00 | 1 | -3.50 |
| BTCUSD IS | +3R | 70.60 | 67.10 | -3.50 | 0 | 0.00 | 1 | -3.50 |
| EURUSD OOS | +1R | 4.50 | -9.40 | -13.90 | 23 | 23.00 | 11 | -36.90 |
| EURUSD OOS | +2R | 4.50 | 1.00 | -3.40 | 9 | 9.00 | 3 | -12.40 |
| EURUSD OOS | +3R | 4.50 | 8.50 | 4.00 | 4 | 4.00 | 0 | -0.00 |
| XAUUSD OOS | +1R | -30.80 | -67.10 | -36.30 | 67 | 67.00 | 41 | -103.30 |
| XAUUSD OOS | +2R | -30.80 | -25.10 | 5.70 | 12 | 12.00 | 2 | -6.30 |
| XAUUSD OOS | +3R | -30.80 | -30.50 | 0.30 | 4 | 4.00 | 1 | -3.70 |
| NAS100 OOS | +1R | 36.80 | 26.40 | -10.40 | 23 | 23.00 | 9 | -32.40 |
| NAS100 OOS | +2R | 36.80 | 38.20 | 1.40 | 5 | 5.00 | 1 | -3.60 |
| NAS100 OOS | +3R | 36.80 | 40.80 | 4.00 | 4 | 4.00 | 0 | -0.00 |
| BTCUSD OOS | +1R | -29.60 | -26.40 | 3.30 | 9 | 9.00 | 3 | -5.70 |
| BTCUSD OOS | +2R | -29.60 | -28.60 | 1.00 | 1 | 1.00 | 0 | -0.00 |
| BTCUSD OOS | +3R | -29.60 | -28.60 | 1.00 | 1 | 1.00 | 0 | -0.00 |

### Break-even by year (delta R against no break-even)

| market | BE | 2024 | 2025 | 2026 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | +1R | -0.50 | -19.70 | -6.10 |  |  |  |  |  |  |  |
| EURUSD IS | +2R | -4.50 | -7.30 | 0.00 |  |  |  |  |  |  |  |
| EURUSD IS | +3R | 0.00 | 1.00 | 0.00 |  |  |  |  |  |  |  |
| XAUUSD IS | +1R | -10.60 | -5.80 | -10.80 |  |  |  |  |  |  |  |
| XAUUSD IS | +2R | 1.00 | 1.00 | 0.00 |  |  |  |  |  |  |  |
| XAUUSD IS | +3R | 0.00 | 0.00 | 0.00 |  |  |  |  |  |  |  |
| NAS100 IS | +1R | 0.30 | -0.80 | -15.50 |  |  |  |  |  |  |  |
| NAS100 IS | +2R | 0.00 | 0.00 | -4.50 |  |  |  |  |  |  |  |
| NAS100 IS | +3R | 0.00 | 0.00 | 1.00 |  |  |  |  |  |  |  |
| BTCUSD IS | +1R | -5.20 | -6.70 | 2.00 |  |  |  |  |  |  |  |
| BTCUSD IS | +2R | 0.00 | -3.50 | 0.00 |  |  |  |  |  |  |  |
| BTCUSD IS | +3R | 0.00 | -3.50 | 0.00 |  |  |  |  |  |  |  |
| EURUSD OOS | +1R |  |  |  | 3.00 | -7.40 | -0.60 | -3.50 | 3.70 | 2.00 | -11.10 |
| EURUSD OOS | +2R |  |  |  | 1.00 | -6.00 | 1.00 | -3.40 | 2.00 | 1.00 | 1.00 |
| EURUSD OOS | +3R |  |  |  | 0.00 | 0.00 | 0.00 | 2.00 | 1.00 | 1.00 | 0.00 |
| XAUUSD OOS | +1R |  |  |  | -1.90 | -1.40 | -9.80 | -4.50 | 3.70 | -5.30 | -17.00 |
| XAUUSD OOS | +2R |  |  |  | 2.00 | 1.00 | 2.00 | 1.00 | 0.40 | 2.00 | -2.70 |
| XAUUSD OOS | +3R |  |  |  | 0.00 | 0.00 | 1.00 | 0.00 | 1.00 | 2.00 | -3.70 |
| NAS100 OOS | +1R |  |  |  | 1.00 | -1.50 | 2.30 | -2.10 | -0.70 | 5.00 | -14.40 |
| NAS100 OOS | +2R |  |  |  | 0.00 | 1.00 | 0.00 | -2.60 | 2.00 | 1.00 | 0.00 |
| NAS100 OOS | +3R |  |  |  | 0.00 | 0.00 | 0.00 | 1.00 | 2.00 | 1.00 | 0.00 |
| BTCUSD OOS | +1R |  |  |  |  |  |  | 2.00 | 3.00 | -0.60 | -1.20 |
| BTCUSD OOS | +2R |  |  |  |  |  |  | 0.00 | 0.00 | 1.00 | 0.00 |
| BTCUSD OOS | +3R |  |  |  |  |  |  | 0.00 | 0.00 | 1.00 | 0.00 |

## 9. Time: where the trades are at a given age, and time-based exits

### 9a. The favourable excursion reached by a given age (share of trades that had seen +0.5R / +1R by then)

| market | 0.5h W>=0.5R | 0.5h L>=0.5R | 1h W>=0.5R | 1h L>=0.5R | 2h W>=0.5R | 2h L>=0.5R | 4h W>=0.5R | 4h L>=0.5R | 8h W>=0.5R | 8h L>=0.5R | 24h W>=0.5R | 24h L>=0.5R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 77 % | 29 % | 86 % | 33 % | 91 % | 38 % | 91 % | 38 % | 91 % | 38 % | 100 % | 38 % |
| XAUUSD IS | 56 % | 35 % | 74 % | 39 % | 84 % | 49 % | 91 % | 54 % | 97 % | 55 % | 99 % | 56 % |
| NAS100 IS | 79 % | 30 % | 89 % | 35 % | 95 % | 39 % | 100 % | 39 % | 100 % | 43 % | 100 % | 43 % |
| BTCUSD IS | 50 % | 38 % | 69 % | 43 % | 83 % | 51 % | 94 % | 51 % | 96 % | 51 % | 100 % | 54 % |
| EURUSD OOS | 80 % | 38 % | 88 % | 41 % | 88 % | 41 % | 96 % | 43 % | 100 % | 43 % | 100 % | 44 % |
| XAUUSD OOS | 49 % | 24 % | 67 % | 32 % | 77 % | 34 % | 89 % | 38 % | 96 % | 40 % | 99 % | 43 % |
| NAS100 OOS | 63 % | 27 % | 77 % | 38 % | 87 % | 44 % | 97 % | 45 % | 100 % | 45 % | 100 % | 45 % |
| BTCUSD OOS | 35 % | 12 % | 60 % | 19 % | 79 % | 23 % | 93 % | 23 % | 100 % | 23 % | 100 % | 23 % |

W = the trades that reached the target, L = the stopped trades: a winner that had not shown +0.5R by 4 h against a loser that had.

### 9b. The position at a given age: R at the close of that candle (the final R once the trade has ended)

| market | 1h: still open | 1h: of them under 0 | 1h: their final R | 1h: final R of those under 0 | 1h: n | 2h: still open | 2h: of them under 0 | 2h: their final R | 2h: final R of those under 0 | 2h: n | 4h: still open | 4h: of them under 0 | 4h: their final R | 4h: final R of those under 0 | 4h: n | 8h: still open | 8h: of them under 0 | 8h: their final R | 8h: final R of those under 0 | 8h: n | 24h: still open | 24h: of them under 0 | 24h: their final R | 24h: final R of those under 0 | 24h: n |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 53 % | 24 % | 1.73 | 0.82 | 6 | 40 % | 21 % | 2.10 | 2.10 | 4 | 26 % | 25 % | 2.12 | 1.30 | 3 | 17 % | 25 % | 2.91 | 2.46 | 2 | 9 % | 0 % | 4.30 |  | 0 |
| XAUUSD IS | 71 % | 32 % | 0.89 | 0.30 | 32 | 52 % | 31 % | 1.12 | -0.03 | 23 | 39 % | 29 % | 1.40 | -0.09 | 16 | 27 % | 24 % | 1.41 | -0.45 | 9 | 10 % | 33 % | 1.13 | -0.40 | 5 |
| NAS100 IS | 47 % | 20 % | 2.20 | 0.54 | 4 | 35 % | 27 % | 1.90 | -0.58 | 4 | 16 % | 43 % | 1.55 | 0.69 | 3 | 14 % | 33 % | 1.28 | -1.00 | 2 | 7 % | 0 % | 2.39 |  | 0 |
| BTCUSD IS | 63 % | 39 % | 1.13 | 0.82 | 22 | 43 % | 24 % | 1.49 | -0.24 | 9 | 27 % | 29 % | 2.33 | 0.39 | 7 | 16 % | 21 % | 1.69 | 0.61 | 3 | 6 % | 0 % | 0.90 |  | 0 |
| EURUSD OOS | 42 % | 32 % | 0.88 | 0.17 | 13 | 31 % | 37 % | 1.36 | 0.69 | 11 | 23 % | 41 % | 1.86 | 0.44 | 9 | 13 % | 31 % | 2.21 | -0.23 | 4 | 10 % | 40 % | 2.63 | 0.02 | 4 |
| XAUUSD OOS | 62 % | 46 % | 0.17 | -0.12 | 105 | 48 % | 45 % | 0.28 | -0.31 | 80 | 36 % | 40 % | 0.45 | -0.36 | 53 | 24 % | 40 % | 0.40 | -0.30 | 36 | 14 % | 24 % | 0.62 | -0.29 | 12 |
| NAS100 OOS | 57 % | 30 % | 1.13 | 0.74 | 17 | 45 % | 22 % | 1.51 | -0.39 | 10 | 28 % | 21 % | 2.01 | -0.58 | 6 | 14 % | 14 % | 3.40 | -1.00 | 2 | 5 % | 20 % | 3.70 | 1.64 | 1 |
| BTCUSD OOS | 58 % | 55 % | -0.06 | -0.46 | 41 | 42 % | 54 % | 0.01 | -0.58 | 29 | 19 % | 32 % | 0.29 | -0.28 | 8 | 12 % | 47 % | 0.06 | -0.41 | 7 | 2 % | 67 % | -1.00 | -1.00 | 2 |

### 9c. Hours to the target (winners) and to the stop (losers)

| market | winners p25 / median / p75 / p90 h | winners over 24 h | over 48 h | R of winners over 24 h | losers p25 / median / p75 / p90 h | losers over 24 h | losers' hours to +0.5R (median, of those that saw it) |
|---|---|---|---|---|---|---|---|
| EURUSD IS | 0.8 / 2.9 / 10.1 / 24.8 | 18 % | 9 % | 17.20 | 0.2 / 0.5 / 1.6 / 4.6 | 0 % | 0.20 |
| XAUUSD IS | 1.2 / 5.1 / 15.6 / 37.9 | 13 % | 10 % | 23.00 | 0.6 / 1.8 / 4.1 / 21.8 | 8 % | 0.20 |
| NAS100 IS | 1.1 / 2.1 / 3.4 / 17.8 | 11 % | 11 % | 6.50 | 0.1 / 0.4 / 0.9 / 3.7 | 0 % | 0.20 |
| BTCUSD IS | 0.6 / 1.7 / 5.8 / 14.8 | 6 % | 2 % | 6.50 | 0.6 / 1.5 / 3.2 / 12.8 | 5 % | 0.20 |
| EURUSD OOS | 0.6 / 4.0 / 18.0 / 68.4 | 24 % | 12 % | 28.30 | 0.0 / 0.3 / 1.2 / 4.2 | 3 % | 0.10 |
| XAUUSD OOS | 0.9 / 4.5 / 22.2 / 73.7 | 23 % | 13 % | 57.80 | 0.5 / 1.3 / 5.4 / 24.9 | 11 % | 0.30 |
| NAS100 OOS | 2.2 / 3.3 / 10.3 / 23.1 | 10 % | 0 % | 16.10 | 0.2 / 0.6 / 2.3 / 4.7 | 0 % | 0.20 |
| BTCUSD OOS | 0.6 / 1.7 / 4.6 / 8.7 | 0 % | 0 % | 0.00 | 0.4 / 1.3 / 3.1 / 6.7 | 3 % | 0.50 |

### 9d. Time exits on the same trades: a max hold (close at the market), a time stop (close only when under the level), a no-progress exit (close when +0.5R was never seen by then)


#### IS (delta R against the ledger)

| market | ledger | hold 2 h | hold 4 h | hold 8 h | hold 12 h | hold 24 h | hold 48 h | hold 72 h | 4 h & <=0R | 4 h & <=-0.5R | 8 h & <=0R | 8 h & <=-0.5R | 24 h & <=0R | 24 h & <=-0.5R | no +0.5R by 2 h | no +0.5R by 4 h | no +0.5R by 8 h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 44.20 | -23.00 | -11.30 | -14.40 | -10.20 | -9.00 | -2.10 | -1.70 | -7.20 | -4.80 | -8.60 | -2.50 | -3.90 | 0.00 | -5.00 | -5.90 | -5.70 |
| XAUUSD IS | 86.10 | -53.40 | -46.40 | -26.30 | -25.50 | -9.70 | -9.60 | -6.90 | -14.10 | -14.20 | -4.00 | -10.20 | 2.60 | -0.20 | -9.70 | -7.10 | -2.10 |
| NAS100 IS | 37.20 | -13.70 | -6.60 | -1.60 | -2.00 | -2.40 | 0.00 | -1.70 | -3.30 | -3.80 | 1.50 | 0.70 | 0.00 | 0.00 | -2.90 | 1.00 | 0.00 |
| BTCUSD IS | 70.60 | -47.00 | -41.70 | -7.40 | -4.30 | -0.20 | 1.10 | -0.50 | -13.00 | -13.10 | -5.70 | 1.90 | 0.30 | 0.60 | -4.20 | -1.20 | -0.10 |

#### OOS (delta R against the ledger)

| market | ledger | hold 2 h | hold 4 h | hold 8 h | hold 12 h | hold 24 h | hold 48 h | hold 72 h | 4 h & <=0R | 4 h & <=-0.5R | 8 h & <=0R | 8 h & <=-0.5R | 24 h & <=0R | 24 h & <=-0.5R | no +0.5R by 2 h | no +0.5R by 4 h | no +0.5R by 8 h |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD OOS | 8.50 | -24.50 | -31.10 | -20.80 | -20.60 | -21.00 | -9.10 | -11.50 | -21.90 | -0.60 | -13.80 | -1.90 | -7.90 | -1.70 | -3.70 | -0.60 | 1.50 |
| XAUUSD OOS | -25.10 | -17.30 | -18.80 | -4.20 | -3.20 | -6.30 | 2.20 | -0.30 | -21.50 | -0.90 | -2.60 | -1.00 | -3.80 | -3.10 | 2.90 | 5.20 | 2.60 |
| NAS100 OOS | 38.80 | -30.10 | -19.90 | -13.60 | -7.50 | -5.50 | 0.00 | -1.00 | -2.30 | 0.60 | 1.20 | -1.70 | -2.20 | -2.20 | -3.60 | -0.50 | 0.00 |
| BTCUSD OOS | -28.60 | 3.80 | -2.20 | 3.80 | 7.20 | 2.10 | 1.60 | 0.00 | -0.50 | 0.20 | 2.40 | 3.10 | 2.00 | 1.40 | 3.40 | 1.20 | 3.30 |

### 9e. Time exits by year (delta R against the ledger)

| market | exit | 2024 | 2025 | 2026 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | hold 24 h | 0.00 | -8.20 | -0.70 |  |  |  |  |  |  |  |
| EURUSD IS | hold 48 h | 0.00 | -2.10 | 0.00 |  |  |  |  |  |  |  |
| EURUSD IS | 8 h & <=0R | 0.00 | -3.90 | -4.80 |  |  |  |  |  |  |  |
| EURUSD IS | no +0.5R by 4 h | 0.00 | -0.00 | -5.90 |  |  |  |  |  |  |  |
| XAUUSD IS | hold 24 h | -6.80 | 1.20 | -4.10 |  |  |  |  |  |  |  |
| XAUUSD IS | hold 48 h | -6.50 | 0.50 | -3.60 |  |  |  |  |  |  |  |
| XAUUSD IS | 8 h & <=0R | 1.70 | -1.60 | -4.00 |  |  |  |  |  |  |  |
| XAUUSD IS | no +0.5R by 4 h | -1.60 | -0.10 | -5.50 |  |  |  |  |  |  |  |
| NAS100 IS | hold 24 h | 0.00 | 0.00 | -2.40 |  |  |  |  |  |  |  |
| NAS100 IS | hold 48 h | 0.00 | 0.00 | 0.00 |  |  |  |  |  |  |  |
| NAS100 IS | 8 h & <=0R | 0.00 | 1.50 | 0.00 |  |  |  |  |  |  |  |
| NAS100 IS | no +0.5R by 4 h | 0.00 | 1.00 | 0.00 |  |  |  |  |  |  |  |
| BTCUSD IS | hold 24 h | -0.10 | -0.00 | 0.00 |  |  |  |  |  |  |  |
| BTCUSD IS | hold 48 h | 1.10 | 0.00 | 0.00 |  |  |  |  |  |  |  |
| BTCUSD IS | 8 h & <=0R | -3.10 | -2.60 | 0.00 |  |  |  |  |  |  |  |
| BTCUSD IS | no +0.5R by 4 h | -0.70 | 0.00 | -0.50 |  |  |  |  |  |  |  |
| EURUSD OOS | hold 24 h |  |  |  | -11.30 | -2.80 | -1.40 | -3.80 | 0.00 | 0.00 | -1.60 |
| EURUSD OOS | hold 48 h |  |  |  | -9.10 | 0.00 | 0.00 | 0.10 | 0.00 | 0.00 | -0.10 |
| EURUSD OOS | 8 h & <=0R |  |  |  | -1.60 | -3.40 | -2.00 | -5.10 | 0.00 | 0.00 | -1.70 |
| EURUSD OOS | no +0.5R by 4 h |  |  |  | 0.70 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00 | -1.90 |
| XAUUSD OOS | hold 24 h |  |  |  | 0.20 | 1.50 | -1.40 | -1.30 | 2.00 | -2.80 | -4.40 |
| XAUUSD OOS | hold 48 h |  |  |  | 1.60 | -0.60 | 2.70 | -2.10 | 2.90 | 1.90 | -4.10 |
| XAUUSD OOS | 8 h & <=0R |  |  |  | -5.40 | -1.50 | 4.70 | 0.80 | 3.80 | -1.70 | -3.40 |
| XAUUSD OOS | no +0.5R by 4 h |  |  |  | -3.90 | -0.40 | 1.40 | 0.50 | 4.60 | 1.20 | 1.80 |
| NAS100 OOS | hold 24 h |  |  |  | 0.00 | 0.00 | -3.60 | 0.00 | 0.00 | 0.00 | -1.90 |
| NAS100 OOS | hold 48 h |  |  |  | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| NAS100 OOS | 8 h & <=0R |  |  |  | 0.00 | 0.00 | 0.20 | 1.00 | 0.00 | 0.00 | 0.00 |
| NAS100 OOS | no +0.5R by 4 h |  |  |  | 0.00 | 0.00 | -1.90 | 0.50 | 0.00 | 0.90 | 0.00 |
| BTCUSD OOS | hold 24 h |  |  |  |  |  |  | 1.60 | 0.50 | 0.00 | 0.00 |
| BTCUSD OOS | hold 48 h |  |  |  |  |  |  | 1.40 | 0.20 | 0.00 | 0.00 |
| BTCUSD OOS | 8 h & <=0R |  |  |  |  |  |  | 2.30 | 0.70 | -2.30 | 1.70 |
| BTCUSD OOS | no +0.5R by 4 h |  |  |  |  |  |  | 1.70 | 1.60 | -3.10 | 1.00 |

## 10. The near-miss losers: how far beyond the stop did the price go before turning?

For every stopped trade, the walk with the stop 1.5 x as wide tells whether the price turned within 1.5 stops and reached the target (a near miss), was stopped at 1.5 x too (a real loser) or was still open after 30 days.

| market | stopped | target with stop x1.1 | target with stop x1.2 | target with stop x1.3 | target with stop x1.5 | stopped at 1.5x too | BE / time / open at 1.5x | x1.2: saved R (cash) | x1.2: winners give up |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 24 | 0 | 0 | 1 | 1 | 23 | 0 | 0.00 | 11.40 |
| XAUUSD IS | 71 | 2 | 3 | 5 | 10 | 60 | 1 | 8.00 | 19.50 |
| NAS100 IS | 23 | 0 | 0 | 1 | 1 | 20 | 2 | 0.00 | 9.90 |
| BTCUSD IS | 37 | 1 | 2 | 4 | 4 | 33 | 0 | 3.60 | 17.90 |
| EURUSD OOS | 68 | 1 | 4 | 5 | 8 | 59 | 1 | 15.30 | 12.70 |
| XAUUSD OOS | 247 | 4 | 11 | 16 | 20 | 227 | 0 | 31.70 | 24.10 |
| NAS100 OOS | 66 | 0 | 0 | 4 | 6 | 58 | 2 | 0.00 | 17.10 |
| BTCUSD OOS | 86 | 3 | 5 | 6 | 12 | 74 | 0 | 10.50 | 9.60 |

## 11. Excursions by zone timeframe (IS + OOS together)

| market | zone | trades | won | sum R | winners MAE median | winners beyond 0.5R | losers MFE median | losers >= 1R | median hold h |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD IS | 1H | 37 | 49 % | 39.00 | 0.30 | 39 % | 0.23 | 28 % | 0.80 |
| EURUSD IS | 4H | 10 | 40 % | 5.30 | 0.79 | 75 % | 0.67 | 33 % | 4.80 |
| XAUUSD IS | 1H | 130 | 48 % | 70.70 | 0.42 | 45 % | 0.59 | 18 % | 2.10 |
| XAUUSD IS | 4H | 13 | 62 % | 15.40 | 0.27 | 12 % | 0.51 | 40 % | 21.80 |
| NAS100 IS | 1H | 38 | 47 % | 31.00 | 0.23 | 35 % | 0.30 | 15 % | 0.90 |
| NAS100 IS | 4H | 5 | 40 % | 6.20 | 0.71 | 100 % | -0.03 | 33 % | 3.70 |
| BTCUSD IS | 1H | 67 | 60 % | 63.10 | 0.29 | 30 % | 0.61 | 22 % | 1.20 |
| BTCUSD IS | 4H | 22 | 55 % | 7.50 | 0.50 | 50 % | 0.54 | 40 % | 4.20 |
| EURUSD OOS | 1H | 87 | 20 % | -23.70 | 0.22 | 41 % | 0.18 | 27 % | 0.50 |
| EURUSD OOS | 4H | 10 | 80 % | 32.20 | 0.72 | 62 % | 0.87 | 50 % | 10.70 |
| XAUUSD OOS | 1H | 323 | 30 % | -18.40 | 0.50 | 50 % | 0.42 | 22 % | 1.50 |
| XAUUSD OOS | 4H | 48 | 25 % | -6.70 | 0.45 | 50 % | 0.37 | 22 % | 7.00 |
| NAS100 OOS | 1H | 93 | 30 % | 30.70 | 0.49 | 46 % | 0.31 | 33 % | 1.70 |
| NAS100 OOS | 4H | 7 | 57 % | 8.10 | 0.67 | 75 % | 0.59 | 0 % | 2.40 |
| BTCUSD OOS | 1H | 100 | 31 % | -27.80 | 0.42 | 42 % | 0.14 | 10 % | 1.20 |
| BTCUSD OOS | 4H | 30 | 40 % | -0.80 | 0.36 | 33 % | 0.31 | 6 % | 3.10 |
