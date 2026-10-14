# Random-direction and random-timing baselines for the entry logic (methodology A8)

14 October 2026. Angle: are the ledgers' results better than what random trades with the same stops, targets,
break-even rule, sessions and costs would make? Eight research ledgers (the live profiles at 1 % risk, guard off:
EURUSD `eutwo`, gold `base`, NAS100 `rr08`, BTC `base`; 2024-01..2026-09 in sample and 2017..2023 out of sample,
BTC 2020-06..2023), 300 null runs each, 0.10R a trade for costs on real and null trades alike. Read-only on the
repository; everything ran from the scratchpad.

Script: `research/baselines/baselines.py` (argument: the number of runs; `nice -n 10 python3 baselines.py 300`, about
25 s for the eight ledgers). Outputs: `research/baselines/baselines_results.json` (every number below),
`research/baselines/trades_<SYMBOL>_<period>.csv` (one row a trade: the ledger's R, the walker's R, the mirror trade's
R, the per-trade means of the timing nulls, the real entry's percentile among its window's candidates),
`research/baselines/tables.py` -> `tables.md`.

## 1. Summary

- The walker reproduces the ledgers: 1,017 of the 1,020 trades to 0.01R and the same sum R on seven of the eight
  ledgers (the three others are EURUSD 2017-23 limit fills stopped in their own candle, 1.0R in total). The null
  comparisons are therefore apples to apples.
- In sample (2024-26) every market beats both nulls at the 5 % level except NAS100 on the timing null (p 0.13 on the
  whole-window null, 0.057 on the look-ahead-free one). Random direction at the real candles: p 0.027 / 0.000 /
  0.007 / 0.000 (EURUSD / gold / NAS100 / BTC); the real direction at a random later candle of the same window:
  p 0.000 / 0.003 / 0.057 / 0.003. The four combined: z +5.4 on the direction null, +5.3 on the timing null,
  +6.6 against trades random in both. A trade random in both direction and timing makes -0.08..+0.04R a trade: the
  geometry and the sessions carry no edge of their own, the entry logic produces the whole in-sample result.
- Out of sample (2017-23) the direction call has no support in any market (p 0.14 / 0.32 / 0.14 / 0.96; sign test:
  the real direction beats its mirror image in 60 % / 50 % / 54 % / 43 % of the decided trades) and for BTC it is
  inverted (the mirror image won 58 of 101 decided trades, z -1.6). The timing of the signal candle does survive:
  EURUSD z +3.9 (the same directions entered at random later candles would have lost 46.8R instead of 2.2R), NAS100
  z +3.0 (-11.7R instead of +28.8R), gold z +1.6 (p 0.063), BTC z -0.9. Combined out of sample: timing z +4.1,
  direction z +0.7.
- So the README's reading, "the edge, where there is one, is the direction call", holds in sample (the direction
  term is the largest piece for gold, NAS100 and BTC) but not out of sample, where the only component with support
  is the entry candle, and only on the two markets that enter by limit (EURUSD, NAS100). The in-sample p-values are
  on the window that chose the rules and are not deflated for the hundreds of variants tried (A4); the 2017-23
  figures are the honest ones.
- The specified timing null (any candle of the same window) has a look-ahead: candles before the signal trade the
  direction of a balance shift that has not happened yet and so collect the shift's own impulse (gold 2024-26: the
  before-the-signal null makes +58.9R, the after-the-signal null +25.7R; gold 2017-23: -22.9R against -88.5R). The
  after-the-signal variant is the clean test and is used for every reading below; the whole-window numbers are
  reported because A8 asked for them.
- The year-by-year result tracks the regime: across 37 market-years the real R a trade correlates 0.60 with what a
  trade random in both direction and timing makes (0.68 on the 33 years with 10+ trades), but last year's baseline
  predicts this year's result at only 0.30. 2026 carries the in-sample result (gold +36.3 of +71.8R, NAS100 +24.7 of
  +32.9R, BTC +39.6 of +61.7R) and is the year in which the direction z is highest.
- Per subset: the morning window's direction calls have no support in any market in either period (direction z
  2024-26 / 2017-23: EURUSD -0.0 / +0.6, gold +0.6 / -0.8, NAS100 +1.4 / -1.1, BTC +2.1 / -1.1); the afternoon window
  carries the direction edge of EURUSD, gold and NAS100. EURUSD's 4H zones pass both nulls in both periods (10 + 10
  trades); gold's 4H zones pass nothing out of sample (48 trades, -11.5R, direction z -0.0, timing z -1.1) although
  they risk twice the stake.

## 2. Method

**The nulls.** For every real trade the walker keeps its stop distance (|entry - stop|, the ledger's own risk
distance), its target distance, the break-even trigger (gold 2R, the others 4R; the stop moves to the entry, the
trigger candle that also trades back through it closes at break-even, as `paper.py`), NAS100's 48 h time exit at the
candle close (market) and the ledger's backtest end (open null trades are flattened at the last candle, as the
backtest does).

- (a) **direction**: the real entry time and price (the fill is moved by one spread to the other side of the quote:
  a short fills at the bid, a long at the ask), a fair coin for the direction. The mirror trade's R is computed once
  per trade, so the null's mean and variance are exact and the 300 runs only sample the coin.
- (b) **timing, whole window** (A8 as specified): the real direction and distances, the entry at a uniformly random
  5-minute candle whose close falls in the same session window (09:00-11:00 or 13:00-17:00 Amsterdam, on the close
  time, half-open, weekdays, exactly `engine.in_session`) on the same local day as the signal
  (`confirmed_close_at`), excluding candles whose close lies within 30 minutes of a high-impact event of the
  symbol's currencies (`data/calendar/high_impact.csv`: EUR+USD for EURUSD, USD for the others, importance >= 1, the
  calendar the ledgers ran with). The fill is the candle's close (plus the spread for a long), checked from the next
  candle on, as a market order in the backtest. Candidates: 24 in the morning window, 48 in the afternoon, 35 on an
  afternoon with a US release (median 35, minimum 11).
- (b') **timing, after the signal only**: the same, restricted to candles after the signal candle (the look-ahead-free
  version; a signal at the window's last candle has no candidate and falls back to the signal candle itself:
  2-11 trades a ledger).
- (b'') **timing, before the signal only**: the complement, reported to size the look-ahead.
- (c) **both random**: the coin and the random window candle together (the pure session-and-geometry baseline).
- (d) **near timing**: the random candle within 6 candles (30 min) either side of the signal candle; (d') within the
  6 candles after it.

**The walk.** 5-minute bid candles (`scratchpad/fixed/<SYMBOL>_5min.csv`; BTC `btc_data` for 2024-26 and `btc_old`
for 2020-23, the folders the ledgers ran on), ask = bid + the ledger's spread (EURUSD 1.0 pip, gold 2.0 pips = $0.20,
NAS100 1.5 points, BTC $15). Per candle: stop first (a candle gapping through it fills at its open), then target, then
break-even, then the time exit; a long is checked on the bid, a short on the ask. This is `PaperBroker.on_candle`
with `quote_basis=bid`, vectorised per trade with numpy (first-hit indices over growing chunks of candles, a safety
cap of 720 h that no trade reached). Costs: 0.10R a trade, which cancels in every comparison since real and null
have the same number of trades; the tables show sums after it.

**Statistics.** Per ledger: the real sum R (the walker's replay; the ledger's own figure beside it), the null's
mean and standard deviation of the sum R from the exact per-trade moments (trades independent under the null),
z = (real - mean) / sd and the normal p beside the Monte Carlo p (the share of the 300 runs at or above the real
sum; resolution 1/300, standard error about 0.01-0.03; seed 1). Combined: the per-market null runs summed run by run
(independent draws), the moments added. Subsets (window, year, zone timeframe, direction): the real sum of the
subset against the exact moments of its trades.

T1 calibration of the walker against the ledgers (sum R after 0.10R a trade)

| Ledger | n | ledger | walker replay | trades matching to 0.01R | note |
|---|---|---|---|---|---|
| EURUSD 2024-26 | 47 | +39.55 | +39.55 | 47/47 |  |
| XAUUSD 2024-26 | 143 | +71.82 | +71.82 | 143/143 |  |
| NAS100 2024-26 | 43 | +32.90 | +32.90 | 43/43 |  |
| BTCUSD 2024-26 | 89 | +61.70 | +61.70 | 89/89 |  |
| EURUSD 2017-23 | 97 | -1.25 | -2.24 | 94/97 | 3 limit fills stopped in their own candle (the ledger books -1.0R at the stop, the walker the gap fill at the next open: -1.16, -1.26, -1.58R) |
| XAUUSD 2017-23 | 371 | -62.22 | -62.22 | 371/371 |  |
| NAS100 2017-23 | 100 | +28.78 | +28.78 | 100/100 |  |
| BTCUSD 2017-23 | 130 | -41.62 | -41.62 | 130/130 |  |

## 3. Results

T2 the nulls per ledger: null mean (sd) of the sum R after costs, p = share of the 300 null runs at or above the real sum, z from the exact null moments

| Ledger | n | real | (a) direction coin | (b) timing, whole window | (b') timing, after the signal only | (b'') timing, before the signal only | (c) both random |
|---|---|---|---|---|---|---|---|
| EURUSD 2024-26 | 47 | +39.5 | +14.9 (13.1), p 0.027, z +1.88 | +3.4 (9.6), p 0.000, z +3.77 | +9.5 (7.2), p 0.000, z +4.18 | +6.9 (8.2), p 0.000, z +3.96 | +1.9 (13.5), p 0.007, z +2.78 |
| XAUUSD 2024-26 | 143 | +71.8 | +10.9 (17.0), p 0.000, z +3.58 | +36.4 (14.9), p 0.013, z +2.37 | +25.7 (12.6), p 0.003, z +3.67 | +58.9 (11.5), p 0.160, z +1.12 | -6.2 (17.9), p 0.000, z +4.36 |
| NAS100 2024-26 | 43 | +32.9 | +2.7 (10.7), p 0.007, z +2.82 | +13.8 (16.8), p 0.130, z +1.14 | +11.9 (13.4), p 0.057, z +1.57 | +25.3 (14.1), p 0.373, z +0.54 | -3.3 (15.1), p 0.010, z +2.40 |
| BTCUSD 2024-26 | 89 | +61.7 | +16.3 (17.9), p 0.000, z +2.54 | +31.1 (14.9), p 0.000, z +2.05 | +36.2 (12.3), p 0.003, z +2.08 | +30.6 (12.7), p 0.010, z +2.45 | +3.5 (17.3), p 0.000, z +3.37 |
| EURUSD 2017-23 | 97 | -2.2 | -20.2 (14.5), p 0.140, z +1.24 | -40.7 (13.0), p 0.003, z +2.95 | -46.8 (11.4), p 0.000, z +3.92 | -27.3 (8.8), p 0.007, z +2.85 | -32.4 (15.8), p 0.020, z +1.92 |
| XAUUSD 2017-23 | 371 | -62.2 | -71.9 (23.2), p 0.320, z +0.42 | -62.9 (19.7), p 0.497, z +0.04 | -88.5 (16.6), p 0.063, z +1.58 | -22.9 (15.6), p 0.997, z -2.52 | -80.9 (25.5), p 0.217, z +0.73 |
| NAS100 2017-23 | 100 | +28.8 | +9.8 (18.2), p 0.137, z +1.04 | -10.1 (14.2), p 0.010, z +2.74 | -11.7 (13.7), p 0.007, z +2.95 | -2.7 (11.8), p 0.003, z +2.67 | -5.4 (19.6), p 0.063, z +1.74 |
| BTCUSD 2017-23 | 130 | -41.6 | -20.7 (12.9), p 0.957, z -1.63 | -33.2 (9.0), p 0.827, z -0.93 | -34.3 (8.0), p 0.833, z -0.91 | -24.8 (6.9), p 0.983, z -2.42 | -22.2 (13.8), p 0.923, z -1.41 |

T2b the near-timing nulls: +-30 min around the signal candle, and the 30 min after it

| Ledger | real | (d) +-6 candles: null mean (sd), p, z | (d') 1-6 candles after: null mean (sd), p, z | candidates (median) d / d' | fallbacks d' |
|---|---|---|---|---|---|
| EURUSD 2024-26 | +39.5 | +16.6 (7.3), p 0.000, z +3.15 | +11.3 (6.4), p 0.000, z +4.41 | 12 / 6 | 3 |
| XAUUSD 2024-26 | +71.8 | +59.6 (10.7), p 0.110, z +1.14 | +37.2 (8.9), p 0.000, z +3.90 | 13 / 6 | 2 |
| NAS100 2024-26 | +32.9 | +13.1 (10.7), p 0.043, z +1.85 | +8.8 (9.2), p 0.023, z +2.62 | 12 / 6 | 5 |
| BTCUSD 2024-26 | +61.7 | +49.3 (13.6), p 0.233, z +0.92 | +47.9 (5.2), p 0.007, z +2.68 | 13 / 6 | 2 |
| EURUSD 2017-23 | -2.2 | -41.3 (10.8), p 0.000, z +3.62 | -50.3 (10.0), p 0.000, z +4.82 | 12 / 6 | 6 |
| XAUUSD 2017-23 | -62.2 | -22.8 (16.7), p 0.993, z -2.36 | -71.2 (13.8), p 0.247, z +0.65 | 13 / 6 | 11 |
| NAS100 2017-23 | +28.8 | +0.5 (12.1), p 0.007, z +2.34 | -8.1 (7.2), p 0.000, z +5.11 | 13 / 6 | 2 |
| BTCUSD 2017-23 | -41.6 | -23.3 (6.8), p 0.997, z -2.68 | -35.7 (5.8), p 0.787, z -1.01 | 13 / 6 | 0 |

T3 the four markets combined (independent null draws per market summed)

| Period | n | real | direction | timing, whole window | timing, after the signal | both random |
|---|---|---|---|---|---|---|
| 2024-26 | 322 | +206.0 | +44.8, p 0.000, z +5.39 | +84.6, p 0.000, z +4.24 | +83.2, p 0.000, z +5.28 | -4.1, p 0.000, z +6.55 |
| 2017-23 | 698 | -77.3 | -103.0, p 0.230, z +0.73 | -147.0, p 0.013, z +2.40 | -181.3, p 0.000, z +4.06 | -140.9, p 0.040, z +1.66 |
| all | 1020 | +128.7 | -58.2, p 0.000, z +4.04 | -62.4, p 0.000, z +4.69 | -98.1, p 0.000, z +6.55 | -145.0, p 0.000, z +5.47 |

Reading against A8's pass/fail rule (p <= 0.05 per market on both nulls in 2024-26, p <= 0.01 for the four combined;
p > 0.20 on a null means no edge of that kind):

| Market | 2024-26 direction | 2024-26 timing (after the signal) | 2017-23 direction | 2017-23 timing (after the signal) |
|---|---|---|---|---|
| EURUSD | pass (0.027) | pass (0.000) | no (0.14) | pass (0.000) |
| XAUUSD | pass (0.000) | pass (0.003) | none (0.32) | marginal (0.063) |
| NAS100 | pass (0.007) | marginal (0.057; whole window 0.13) | no (0.14) | pass (0.007) |
| BTCUSD | pass (0.000) | pass (0.003) | none, inverted (0.96, z -1.6) | none (0.83) |
| combined | pass (z +5.4) | pass (z +5.3) | none (z +0.7) | pass (z +4.1) |

## 4. What carries the result: the decomposition and the sign test

T4 decomposition, R a trade after costs (each cell is the null's mean per trade; the real trade in the last column)

| Ledger | n | both random | real direction at a random later candle (b') | real direction at a random window candle (b) | random direction at the real candle (a) | real | interaction (real - b' - a + both) |
|---|---|---|---|---|---|---|---|
| EURUSD 2024-26 | 47 | +0.040 | +0.203 | +0.072 | +0.317 | +0.841 | +0.362 |
| XAUUSD 2024-26 | 143 | -0.043 | +0.179 | +0.255 | +0.076 | +0.502 | +0.203 |
| NAS100 2024-26 | 43 | -0.076 | +0.277 | +0.320 | +0.064 | +0.765 | +0.349 |
| BTCUSD 2024-26 | 89 | +0.039 | +0.406 | +0.349 | +0.183 | +0.693 | +0.143 |
| EURUSD 2017-23 | 97 | -0.334 | -0.483 | -0.420 | -0.208 | -0.023 | +0.333 |
| XAUUSD 2017-23 | 371 | -0.218 | -0.239 | -0.170 | -0.194 | -0.168 | +0.046 |
| NAS100 2017-23 | 100 | -0.054 | -0.117 | -0.101 | +0.098 | +0.288 | +0.253 |
| BTCUSD 2017-23 | 130 | -0.171 | -0.264 | -0.256 | -0.159 | -0.320 | -0.068 |

The two single terms are "the direction call at a random later candle" (b') and "a coin at the real candle" (a);
the interaction is what the two do together beyond their sum.

- EURUSD 2024-26: a coin at the signal candles earns +0.32R a trade (the candle marks an expansion: either side
  pays at planned R:R 3.3), the direction at random later candles +0.20, together +0.84: the interaction (+0.36) is
  the largest piece. Out of sample the same directions at later candles lose -0.48R a trade, worse than a coin at
  the real candle (-0.21) and than a trade random in both (-0.33), yet the real trades break even (-0.02): the
  interaction (+0.33) is the one term that holds in both periods.
- NAS100: the same shape (interaction +0.35 in sample, +0.25 out of sample), with the direction-at-a-later-candle
  term the largest single piece in sample (+0.28 of +0.77).
- Gold: the direction call at a random later candle makes +0.18, the coin at the real candle +0.08, the interaction
  +0.20; out of sample all three are about zero (-0.24, -0.19, +0.05 against a baseline of -0.22).
- BTC: the direction at a random later candle makes +0.41 of the +0.69: BTC's result is the direction in the window,
  not the candle; out of sample that term is -0.26 against a baseline of -0.17 (the direction call hurt).

T5 sign test on the direction: the real trade against its mirror image at the same moment

| Ledger | real better | tie | mirror better | real better, share of the non-ties | one-sided binomial p |
|---|---|---|---|---|---|
| EURUSD 2024-26 | 23 | 17 | 7 | 77% | 0.003 |
| XAUUSD 2024-26 | 73 | 29 | 41 | 64% | 0.002 |
| NAS100 2024-26 | 20 | 16 | 7 | 74% | 0.010 |
| BTCUSD 2024-26 | 47 | 20 | 22 | 68% | 0.002 |
| EURUSD 2017-23 | 29 | 49 | 19 | 60% | 0.097 |
| XAUUSD 2017-23 | 125 | 122 | 124 | 50% | 0.500 |
| NAS100 2017-23 | 34 | 37 | 29 | 54% | 0.307 |
| BTCUSD 2017-23 | 43 | 29 | 58 | 43% | 0.945 |

## 5. Where the components sit

T6 by session window: n, real R, z against the direction null, z against the after-the-signal timing null

| Ledger | 09-11 | 13-17 |
|---|---|---|
| EURUSD 2024-26 | n 13, R +4.4, dir z -0.01, timing z +2.53 | n 34, R +35.1, dir z +2.25, timing z +3.42 |
| XAUUSD 2024-26 | n 52, R +11.6, dir z +0.62, timing z +2.87 | n 91, R +60.2, dir z +4.04, timing z +2.62 |
| NAS100 2024-26 | n 16, R +14.3, dir z +1.41, timing z +2.61 | n 27, R +18.6, dir z +2.49, timing z +0.80 |
| BTCUSD 2024-26 | n 42, R +53.4, dir z +2.11, timing z +1.33 | n 47, R +8.3, dir z +1.46, timing z +1.88 |
| EURUSD 2017-23 | n 45, R -5.6, dir z +0.57, timing z +1.99 | n 52, R +3.4, dir z +1.12, timing z +3.39 |
| XAUUSD 2017-23 | n 152, R -30.5, dir z -0.79, timing z +1.75 | n 219, R -31.7, dir z +1.32, timing z +0.78 |
| NAS100 2017-23 | n 34, R -12.0, dir z -1.05, timing z +1.53 | n 66, R +40.7, dir z +1.80, timing z +2.62 |
| BTCUSD 2017-23 | n 59, R -21.7, dir z -1.12, timing z -1.40 | n 71, R -19.9, dir z -1.18, timing z -0.19 |

T7 by year, in sample: n, real R, direction z, after-the-signal timing z

| Market | 2024 | 2025 | 2026 |
|---|---|---|---|
| EURUSD | n 15, R +4.1, dir z +0.07, timing z +2.24 | n 19, R +21.8, dir z +1.65, timing z +4.53 | n 13, R +13.6, dir z +1.54, timing z +0.07 |
| XAUUSD | n 57, R +13.7, dir z +1.35, timing z +0.62 | n 48, R +21.9, dir z +1.82, timing z +2.73 | n 38, R +36.3, dir z +3.14, timing z +3.47 |
| NAS100 | n 8, R +3.3, dir z +1.36, timing z -0.01 | n 19, R +4.8, dir z +1.39, timing z +0.15 | n 16, R +24.7, dir z +2.14, timing z +3.80 |
| BTCUSD | n 49, R +10.3, dir z +1.36, timing z +2.31 | n 22, R +11.8, dir z +2.24, timing z +2.36 | n 18, R +39.6, dir z +1.47, timing z +0.37 |

T7b by year, out of sample (n, real R, direction z, after-the-signal timing z)

- EURUSD: 2017: 11, +10.9, +1.53, +3.26; 2018: 13, +3.8, +1.75, +1.87; 2019: 10, -4.5, -0.19, +0.41; 2020: 17, +0.7, -0.10, +2.70; 2021: 15, -2.9, +1.95, +1.92; 2022: 17, -9.3, -1.01, -0.09; 2023: 14, -0.9, -0.10, +0.48
- XAUUSD: 2017: 60, -3.6, +1.00, +1.04; 2018: 57, -15.7, -0.47, +1.23; 2019: 58, -16.6, +0.64, +1.60; 2020: 51, -12.0, +0.00, -0.11; 2021: 41, -17.3, -1.52, -0.32; 2022: 61, -11.7, -0.87, +0.76; 2023: 43, +14.8, +2.38, +0.28
- NAS100: 2017: 8, -2.3, -0.00, +1.39; 2018: 8, +1.5, +0.51, -0.32; 2019: 17, +9.2, +0.60, +1.44; 2020: 19, -9.8, -0.78, +1.18; 2021: 20, +13.2, +0.41, +0.98; 2022: 22, +0.3, +0.14, +2.28; 2023: 6, +16.7, +1.84, +2.01
- BTCUSD: 2020: 20, -9.2, -1.10, -0.17; 2021: 38, -24.1, -2.19, -1.94; 2022: 49, -13.0, -0.92, -0.33; 2023: 23, +4.7, +0.80, +0.79

T8 by zone timeframe: n, real R, direction z, after-the-signal timing z

| Ledger | 1H zones | 4H zones |
|---|---|---|
| EURUSD 2024-26 | n 37, R +35.3, dir z +1.36, timing z +3.83 | n 10, R +4.3, dir z +1.98, timing z +1.70 |
| XAUUSD 2024-26 | n 130, R +57.7, dir z +3.19, timing z +3.59 | n 13, R +14.1, dir z +1.72, timing z +0.77 |
| NAS100 2024-26 | n 38, R +27.2, dir z +2.90, timing z +1.09 | n 5, R +5.7, dir z +0.50, timing z +2.46 |
| BTCUSD 2024-26 | n 67, R +56.4, dir z +2.35, timing z +1.96 | n 22, R +5.3, dir z +1.02, timing z +0.71 |
| EURUSD 2017-23 | n 87, R -33.4, dir z -0.28, timing z +2.45 | n 10, R +31.2, dir z +2.34, timing z +3.25 |
| XAUUSD 2017-23 | n 323, R -50.7, dir z +0.46, timing z +2.23 | n 48, R -11.5, dir z -0.02, timing z -1.05 |
| NAS100 2017-23 | n 93, R +21.4, dir z +0.65, timing z +2.83 | n 7, R +7.4, dir z +1.78, timing z +0.82 |
| BTCUSD 2017-23 | n 100, R -37.8, dir z -1.81, timing z -0.95 | n 30, R -3.8, dir z -0.08, timing z -0.08 |

T9 by direction: n, real R, direction z, after-the-signal timing z

| Ledger | LONG | SHORT |
|---|---|---|
| EURUSD 2024-26 | n 26, R +28.4, dir z +2.23, timing z +4.15 | n 21, R +11.1, dir z +0.33, timing z +1.24 |
| XAUUSD 2024-26 | n 110, R +47.6, dir z +2.91, timing z +3.31 | n 33, R +24.2, dir z +2.11, timing z +1.80 |
| NAS100 2024-26 | n 36, R +25.0, dir z +2.27, timing z +1.34 | n 7, R +7.9, dir z +1.89, timing z +1.07 |
| BTCUSD 2024-26 | n 62, R +24.0, dir z +2.38, timing z +4.05 | n 27, R +37.7, dir z +1.48, timing z +0.20 |
| EURUSD 2017-23 | n 43, R +16.1, dir z +1.75, timing z +3.74 | n 54, R -18.3, dir z -0.15, timing z +1.67 |
| XAUUSD 2017-23 | n 190, R -13.2, dir z +0.69, timing z +1.26 | n 181, R -49.0, dir z -0.15, timing z +0.96 |
| NAS100 2017-23 | n 74, R +22.1, dir z +0.78, timing z +2.11 | n 26, R +6.7, dir z +0.78, timing z +2.47 |
| BTCUSD 2017-23 | n 59, R -30.6, dir z -1.98, timing z -2.50 | n 71, R -11.0, dir z -0.49, timing z +0.74 |

T10 market-years (37; 33 with n >= 10): correlation of the real R a trade with the both-random baseline 0.60 (0.68 with n >= 10), with the real-direction-after-the-signal null 0.84, with the coin-at-the-real-candle null 0.87; the previous year's both-random baseline against this year's real R a trade: 0.30 (33 pairs).

| Market | year | n | real R/t | both random | real dir, after signal | coin at the real candle |
|---|---|---|---|---|---|---|
| EURUSD | 2024 | 15 | +0.27 | +0.09 | -0.30 | +0.24 |
| EURUSD | 2025 | 19 | +1.15 | +0.06 | +0.04 | +0.39 |
| EURUSD | 2026 | 13 | +1.05 | -0.05 | +1.03 | +0.31 |
| XAUUSD | 2024 | 57 | +0.24 | -0.06 | +0.15 | -0.01 |
| XAUUSD | 2025 | 48 | +0.46 | -0.05 | +0.12 | +0.10 |
| XAUUSD | 2026 | 38 | +0.95 | -0.00 | +0.30 | +0.18 |
| NAS100 | 2024 | 8 | +0.42 | -0.31 | +0.43 | -0.17 |
| NAS100 | 2025 | 19 | +0.25 | +0.07 | +0.16 | -0.24 |
| NAS100 | 2026 | 16 | +1.55 | -0.14 | +0.34 | +0.54 |
| BTCUSD | 2024 | 49 | +0.21 | -0.15 | +0.01 | -0.02 |
| BTCUSD | 2025 | 22 | +0.54 | -0.04 | -0.01 | -0.02 |
| BTCUSD | 2026 | 18 | +2.20 | +0.66 | +1.98 | +0.99 |
| EURUSD | 2017 | 11 | +0.99 | -0.34 | -0.55 | -0.06 |
| EURUSD | 2018 | 13 | +0.30 | -0.40 | -0.19 | -0.29 |
| EURUSD | 2019 | 10 | -0.45 | -0.31 | -0.60 | -0.38 |
| EURUSD | 2020 | 17 | +0.04 | -0.18 | -0.64 | +0.08 |
| EURUSD | 2021 | 15 | -0.19 | -0.52 | -0.60 | -0.61 |
| EURUSD | 2022 | 17 | -0.55 | -0.34 | -0.52 | -0.22 |
| EURUSD | 2023 | 14 | -0.07 | -0.28 | -0.26 | -0.02 |
| XAUUSD | 2017 | 60 | -0.06 | -0.22 | -0.16 | -0.21 |
| XAUUSD | 2018 | 57 | -0.27 | -0.26 | -0.38 | -0.20 |
| XAUUSD | 2019 | 58 | -0.29 | -0.39 | -0.45 | -0.39 |
| XAUUSD | 2020 | 51 | -0.24 | -0.18 | -0.22 | -0.24 |
| XAUUSD | 2021 | 41 | -0.42 | -0.23 | -0.39 | -0.13 |
| XAUUSD | 2022 | 61 | -0.19 | -0.18 | -0.27 | -0.04 |
| XAUUSD | 2023 | 43 | +0.34 | -0.03 | +0.29 | -0.13 |
| NAS100 | 2017 | 8 | -0.29 | -0.47 | -0.56 | -0.29 |
| NAS100 | 2018 | 8 | +0.18 | +0.06 | +0.31 | -0.06 |
| NAS100 | 2019 | 17 | +0.54 | +0.36 | +0.13 | +0.26 |
| NAS100 | 2020 | 19 | -0.52 | -0.33 | -0.75 | -0.26 |
| NAS100 | 2021 | 20 | +0.66 | +0.10 | +0.16 | +0.44 |
| NAS100 | 2022 | 22 | +0.01 | -0.18 | -0.42 | -0.03 |
| NAS100 | 2023 | 6 | +2.78 | +0.02 | +1.41 | +0.82 |
| BTCUSD | 2020 | 20 | -0.46 | -0.17 | -0.44 | -0.19 |
| BTCUSD | 2021 | 38 | -0.63 | -0.26 | -0.43 | -0.30 |
| BTCUSD | 2022 | 49 | -0.27 | -0.15 | -0.23 | -0.11 |
| BTCUSD | 2023 | 23 | +0.20 | -0.07 | +0.09 | -0.01 |

The baseline that needs no strategy (a trade random in both direction and timing, with the live geometry) explains
about 40 % of the variance of the yearly result; it is a nowcast, not a forecast (0.30 one year ahead). Its level
differs between the periods: about zero a trade in 2024-26 (+0.04, -0.04, -0.08, +0.04 after costs) and -0.33 /
-0.22 / -0.05 / -0.17 in 2017-23. The spread explains part of it (spread over stop distance, median: gold 0.062
against 0.024 in sample, NAS100 0.096 against 0.055, BTC 0.068 against 0.034) but not EURUSD's (0.128 against
0.123): in 2017-23 a random entry with a 1R stop and a 2-3R target lost at the stop scale (mean reversion), in
2024-26 it did not. A strategy whose target is 2-3 stops away is a bet on expansion, and 2024-26 (gold 2,000 to
4,266, the 2026 trends) is the expansive regime.

## 6. What it means for the live set

1. **The in-sample result is the entry logic, not the geometry or the sessions.** Random trades with the same
   stops, targets, break-even and windows make about zero in 2024-26 (combined -4.1R on 322 trades against the real
   +206.0R, z +6.6). The challenge is not running on a favourable stop/target asymmetry.
2. **Out of sample only the entry candle has support, and only where the entry is a limit.** EURUSD and NAS100
   (limit 25 % back toward the stop, valid 4 h) keep a timing edge in both periods (after-the-signal z +4.2 / +3.9
   and +1.6 / +3.0); gold's is marginal out of sample (+1.6), BTC's absent (-0.9). The README's limit-entry test
   (gold loses with a limit, "its winners leave without coming back") fits: gold's edge is the direction in the
   afternoon window, not the candle. No new limit-entry proposal follows for gold or BTC; the finding says where the
   edge of each market lives, which is where research on it should go: entry mechanics for EURUSD/NAS100, the bias
   and the window for gold/BTC.
3. **The direction call, the largest in-sample term for gold, NAS100 and BTC, is the term without out-of-sample
   support, and BTC's was inverted in 2020-23.** The live set's expectation rests on the 2024-26 regime continuing.
   This supports the current hedges (the drawdown ladder, BTC at half stake) and argues against any stake increase
   from the in-sample figures; it does not argue for removing a market, since no market's out-of-sample timing or
   direction term is significantly negative except BTC's direction (z -1.6, p 0.96).
4. **A direction meter beside the edge meter** (proposal, code, about 40 lines in the weekly parity check that runs
   on the laptop against the FTMO candles, `kronos_trader/parity.py`): for every closed live trade walk its mirror
   image (the opposite direction at the same fill time and price, the same stop and target distances, break-even
   trigger and time exit) on the FTMO 5-minute candles; the direction score of a market is the sum over its last 30
   closed trades of (r_real - r_mirror) / 2. The backtest's values a trade: 2024-26 EURUSD +0.52, gold +0.43,
   NAS100 +0.70, BTC +0.51; 2017-23 +0.19, +0.03, +0.19, -0.16. The per-trade standard deviation is 1.4-1.9R, so a
   30-trade score separates the in-sample edge (+13..+21R) from a coin (0R) at 1.5-2 standard deviations. Reading:
   a 30-trade direction score <= 0 says the market's direction calls are running as coins (BTC's 2020-23 state);
   with the edge meter still above its threshold that market is living on its timing only. The same walk gives a
   timing score (r_real against the mean of the 6 candles after the signal in the same direction). The walker in
   `baselines.py` (`Market.walk`) is the implementation.
5. **Gold's 4H double stake rests on 13 in-sample trades** (+14.1R, direction z +1.7, timing z +0.8) and fails both
   nulls out of sample on the current profile's ledger (48 trades, -11.5R, direction z -0.0, timing z -1.1, worse a
   trade than gold's 1H zones at -0.16). The pooled evidence the profile cites (EURUSD, gold and NAS100 4H zones
   +0.49R a trade in 2017-23) is EURUSD's 10 trades (+31.2R) carrying gold's 48. For Max: `dorus_live_gold.yaml`
   `risk.zone_risk_multiplier: {4H: 1.0}` (EURUSD and NAS100 keep 2.0; EURUSD's 4H zones pass both nulls in both
   periods, NAS100's are 5 and 7 trades) would have given up +15.4R of the 2024-26 account replay and the 7.2R ->
   9.2R drawdown step, and saved 11.5R in 2017-23. Medium-low confidence: 13 against 48 trades, a decision taken
   with Max on 6 October.
6. **The morning window's direction calls are coins in every market and both periods**; the morning's edge, where
   it exists, is the entry candle (timing z 2024-26: EURUSD +2.5, gold +2.9, NAS100 +2.6; 2017-23 +2.0, +1.8, +1.5),
   except BTC where the morning direction call is the whole in-sample result (09-11: +53.4R of +61.7R, direction z
   +2.1) and was -21.7R out of sample. No rule follows (the hour cuts in `ledgers.md` section 7 cover the same
   ground and a morning-only BTC session was tested before); it is the reason to keep BTC's stake at half and to
   measure the 09:00 crypto spread (A7) before anything else on BTC.
7. **Method note for the backlog**: a random-timing null must draw its candidates after the signal candle; the
   A8 wording (any candle of the window) flatters the null by the shift's own impulse (gold 2024-26: the
   before-the-signal null makes +58.9R against +25.7R after; NAS100 +25.3R against +11.9R). Masters' third null,
   permuted 5-minute returns through the whole engine, stays the heavier follow-up; it would test the zone and bias
   logic that this analysis holds fixed.

## 7. Caveats

- The in-sample ledgers are the rules chosen on this window; their p-values describe the chosen rules on the data
  that chose them and carry no correction for the trials (A4: DSR 0.22-0.79 at N = 100). The 2017-23 ledgers are
  the test.
- Null trades are treated as independent across trades and markets; the real trades cluster (same day, same
  regime), which the null's variance understates, so the z-scores are upper bounds in that respect. The sign test
  (T5) is the distribution-free check and agrees.
- The timing nulls enter at market at the random candle while EURUSD's and NAS100's real trades are limit fills:
  their timing edge includes the limit's conditional fill (8 of 61 EURUSD signals expired unfilled) and its price
  improvement. The nulls keep the post-fill distances, so the geometry is the same; the anchoring is not.
- The news blackout is the calendar the ledgers ran with (the file is denser since 2023: 427-486 events a year
  against 158 in 2017), applied identically to the null candidates.
- Spread sensitivity (FTMO's gold 3.4-3.7 pips, NAS100 3-5 points, BTC $30-45) shifts real and null alike and does
  not move the p-values; the per-trade cost model (A7) is the place for it.
- BTC's research candles are UTC-anchored (task 80 on the FTMO 17:00 New York anchoring is open); the null and the
  real use the same candles.
- 300 runs give p to about +-0.02; the exact z and its normal p are the precise figures and agree with the runs
  everywhere (NAS100 timing: Monte Carlo 0.130, normal 0.127).

## 8. Files

- `research/baselines/baselines.py`: the walker, the nulls, the runs (the script path A8 asked for).
- `research/baselines/baselines_results.json`: every statistic, the subset tables, the null quantiles.
- `research/baselines/trades_<SYMBOL>_<period>.csv`: per-trade outcomes (ledger R, walker R, mirror R, the
  timing-null means, the real entry's percentile among its window's candidates).
- `research/baselines/tables.py`, `tables.md`: the tables above.
