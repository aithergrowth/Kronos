# How sure are we of the bias?

*The trader's question: "Hoe zeker zijn we van de bias eigenlijk?" This note answers it for the four live markets. Written 15 October 2026.*

Each market was studied once and then checked by an independent second run. Where a check found a problem, this note uses its corrected number, or leaves the number out and says why. Numbers in brackets are 95 % confidence intervals.

- **Periods.** In-sample (IS) is 2024-01 to 2026-09, the period the live profiles were tuned on. Out-of-sample (OOS) is 2017 to 2023. For BTC, OOS is 2020-06 to 2023-12.
- **Code.** Commit 06f1004, the commit the live windows run. The bias code (`bias.py`, `structure.py`, `engine.py`, `core/`) and the four live profiles are identical in today's HEAD (b41b3d5), so the results apply to the current code too.

## The short answer

1. **The bot reads the bias exactly as tested.**
   - In all four markets, the bias rebuilt from the candles equals `StrategyEngine.analyze` at every hour compared. That covers all 59,758 EURUSD hours, all 56,794 NAS100 hours, and 1,981 gold and 2,520 BTC hours. For gold and BTC, the engine's own cut-and-read functions also agree at every hour.
   - It also equals the bias stored on every one of the 955 ledger trades.
2. **We cannot be sure the bias knows the direction.**
   - The comparison is a guess that knows nothing about direction but goes long and short in the same mix as the bias, on the same hours.
   - At the hours the bias allows a trade, price went its way about as often as for that guess.
   - Across 4 markets, 2 periods and 3 horizons (4, 24 and 72 hours), the difference runs from -2.4 to +2.8 percentage points. All 24 intervals include zero.
3. **Two small effects show in the size of the move, each in one period only.**
   - Gold in 2024-26 over 4 hours: +0.10 hourly ATR [+0.02, +0.16].
   - BTC in 2020-23 over 24 and 72 hours: +0.12 [+0.03, +0.23] and +0.23 [+0.03, +0.46] daily ATR.
   - Neither shows in the market's other period.
4. **More timeframes agreeing does not mean more certainty.**
   - In the hourly readings, no market does better against the same-mix guess with more aligned timeframes in both periods.
   - In the trades the picture is small and points different ways:
     - 5 aligned was gold's weakest group in both periods and EURUSD's strongest;
     - BTC's 3-aligned trades beat its 4-aligned ones.
   - The only differences that were tested (gold) were not significant.
5. **The bias is a gate, not a forecast.**
   - The side holds for days to weeks. The 1H switches the permission on and off.
   - A tradable decision lasts a median 4-6 hours, and the 1H is the reading that changed at 82-99 % of its ends.
   - Only 9 of 6,101 decisions ended by flipping straight to the other side.
6. **Small price differences barely move it; the candle grid moves it a lot.**
   - Noise the size of half a spread changes long/none/short in 0.8-2.2 % of 2024-26 hours. It practically never turns a long into a short.
   - A second real feed changed 3-4 % of 2026 hours.
   - Cutting gold's 4H and daily candles one hour early changes 7-10 % of its decisions.
   - UTC candles instead of New York candles change BTC's trade state in 14 % of 2024-26 hours.

## How it was measured

- **Readings.**
  - Each timeframe's bias comes from the engine's own `analyze_structure` and `timeframe_bias`. Only closed candles are used: the last 60 monthly, 104 weekly, 250 daily, 300 4H and 300 1H.
  - The bias is read at every close of that timeframe and held until the next close.
  - At every 1H close, the engine's `combine_biases` gives the decision under the live profile.
  - Hours read (IS / OOS): gold 16,169 / 40,737; EURUSD 17,021 / 42,737; NAS100 16,162 / 40,632; BTC 24,096 / 31,416. BTC trades every hour of the week.
- **Candles.**
  - Gold, EURUSD and NAS100 use HistData bid. Their 4H, daily, weekly and monthly candles are already cut at 17:00 New York, the same cut as FTMO's New York+7 server. This was checked on every timestamp since 2016.
  - BTC uses the New York-anchored files the nybase ledgers were built on (`btc_ny_old`); their sha256 equals the ledgers' provenance. The week opens Saturday 17:00 New York.
- **Moves.**
  - Each move runs from the 1H close at the reading's hour to 4, 24 and 72 hours later.
  - Gold and EURUSD count 1H candles (trading hours). NAS100 takes the last close at or before the clock time. BTC trades around the clock, so the two counts are the same. Each study also ran the other count, with the same conclusions.
  - Moves are in ATR14, the engine's `risk.atr`: the mean range of the last 14 closed candles. The 4 h move uses the 1H ATR; the 24 h and 72 h moves use the daily ATR. So +0.10 at 4 h means a tenth of a typical hourly candle.
- **Hit rate.** The share of tradable hours where price moved the bias's way. Zero moves count as misses; EURUSD leaves them out instead (at most 21 hours).
- **The no-skill guess.**
  - It knows nothing about direction but goes long and short in the same mix as the bias, on the same hours.
  - Its hit rate is share_long × P(up) + share_short × P(down), with P taken over those same hours.
  - Its mean move is (share_long − share_short) × the drift of those hours.
  - This removes both the market's drift and the bias's long/short mix.
  - The gold and BTC studies first took P over all hours of the period. The checks showed that flatters gold and misstates BTC. This note uses the same-hours guess everywhere; for gold, its mean-move version was computed for this note from the check's hourly table.
- **Intervals.**
  - Block bootstrap by trading day (17:00 New York; UTC day for BTC), 2,000 resamples. Each statistic is paired with its reference in the same resample.
  - The 24 h and 72 h windows overlap across days, so day blocks can be too narrow. Where a conclusion depends on it, week or month blocks are given.
- **Noise test.**
  - Every open, high, low and close of the 1H, 4H, 1D, 1W and 1M files gets independent uniform noise of half a typical spread: gold ±0.2 USD, EURUSD ±0.5 pip, NAS100 ±1 point, BTC ±10 USD. High and low are then reset so they still contain the open and close.
  - Five seeds, plus one more seed run by each check. The five-seed range is a range, not an interval.

### The profiles as they really are

The question described minimum 3 everywhere, a 4H-only veto for EURUSD and a scalp mode. The live profiles differ:
- The EURUSD profile needs only 2 timeframes (1D+1H) and vetoes on both the 1W and the 4H.
- The scalp mode never fires for EURUSD or gold.

| | XAUUSD | EURUSD | NAS100 | BTCUSD |
|---|---|---|---|---|
| Timeframes that must agree | 3 | **2** | 3 | 3 |
| Full combinations | M+W+D, M+D+1H, D+1H, 4H+1H | M+W+D, M+D+1H, D+1H | M+W+D, M+D+1H | M+W+D, M+D+1H |
| Extra combination M+D+4H | never the match | never the match | never the match | matched (6 % of tradable hours IS) |
| 1H required | yes | yes | yes | no |
| No trade against | none | **1W and 4H** | 1W | none |
| Scalp D+4H+1H | never reached (D+1H is checked first) | never reached | 13 % / 22 % of tradable hours | 24 % / 38 % of tradable hours |
| Tradable, in practice | 3+ agree with the 1H among them, except exactly M+W+1H | the 1D and 1H agree, and neither the 1W nor the 4H is against | M+W+D or M+D+1H with the 1H, or D+4H+1H; the 1W not against | 3+ agree and contain M+W+D, M+D+1H, M+D+4H or D+4H+1H |
| Share of hours tradable (IS / OOS) | 30.7 / 29.1 % | 14.1 / 15.2 % | 18.6 / 19.6 % | 21.8 / 19.2 % |
| Long share of tradable hours | 81.7 / 55.1 % | 53.8 / 43.7 % | 89.5 / 84.3 % | 80.0 / 31.0 % |

### How the readings were proven to be the engine's

| | Compared with `StrategyEngine.analyze` | Ledger trades whose bias columns match |
|---|---|---|
| XAUUSD | 1,200 + 781 sampled hours, all equal. The check's independent cut at all 56,906 hours equals the table. | 514 of 514 |
| EURUSD | Every hour: 59,758 of 59,758 (check). Also 2,320 + 834 hours with a fresh engine fed as the backtest feeds it. | 144 of 144 |
| NAS100 | Every hour: 56,794 of 56,794 (check). Also 1,000 + 785 sampled rows; 1,285 of them were run in both the backtest and the live call style. | 143 of 143 |
| BTCUSD | 1,398 + 1,122 sampled engine calls, all equal. The check's independent cut at all 55,512 hours equals the table. | 154 of 154 |

## The four markets side by side

### Does price go the bias's way?

**Table 1. Tradable hours, next 24 hours.** "No-skill" is the same-mix guess on the same hours.

| Market | Period | Hit rate | No-skill | Difference, points | Mean move its way, daily ATR |
|---|---|---|---|---|---|
| XAUUSD | 2024-26 | 54.9 % [51.3, 58.6] | 54.1 % | +0.8 [-1.8, +3.5] | +0.114 [+0.051, +0.176] |
| XAUUSD | 2017-23 | 49.1 % [46.8, 51.5] | 50.1 % | -1.1 [-3.4, +1.2] | +0.007 [-0.032, +0.047] |
| EURUSD | 2024-26 | 49.9 % [44.4, 55.3] | 49.6 % | +0.3 [-5.2, +5.5] | -0.025 [-0.108, +0.054] |
| EURUSD | 2017-23 | 49.3 % [46.2, 52.3] | 50.2 % | -0.9 [-3.9, +2.1] | +0.021 [-0.024, +0.066] |
| NAS100 | 2024-26 | 52.9 % [47.8, 57.7] | 54.0 % | -1.1 [-3.9, +1.8] | -0.015 [-0.097, +0.065] |
| NAS100 | 2017-23 | 52.9 % [49.7, 56.1] | 53.0 % | -0.1 [-2.3, +2.0] | +0.014 [-0.034, +0.061] |
| BTCUSD | 2024-26 | 47.9 % [43.7, 52.1] | 50.2 % | -2.4 [-5.5, +0.6] | +0.025 [-0.045, +0.095] |
| BTCUSD | 2020-23 | 50.1 % [46.6, 53.8] | 49.6 % | +0.5 [-2.7, +3.8] | +0.091 [+0.017, +0.175] |

A positive mean move is not by itself an edge: gold's +0.114 in 2024-26 is mostly gold's rise (Table 3).

**Table 2. Hit rate minus the no-skill guess, in points.** Day blocks.

| Market | Period | 4 h | 24 h | 72 h |
|---|---|---|---|---|
| XAUUSD | 2024-26 | +1.4 [-0.3, +2.9] | +0.8 [-1.8, +3.5] | +1.2 [-1.7, +4.5] |
| XAUUSD | 2017-23 | -0.8 [-2.3, +0.6] | -1.1 [-3.4, +1.2] | -2.0 [-4.8, +0.6] |
| EURUSD | 2024-26 | -0.3 [-3.4, +2.8] | +0.3 [-5.2, +5.5] | +0.5 [-5.2, +6.4] |
| EURUSD | 2017-23 | +0.3 [-1.7, +2.1] | -0.9 [-3.9, +2.1] | -1.2 [-4.9, +2.3] |
| NAS100 | 2024-26 | +0.7 [-1.0, +2.6] | -1.1 [-3.9, +1.8] | 0.0 [-3.5, +3.4] |
| NAS100 | 2017-23 | -0.2 [-1.3, +1.1] | -0.1 [-2.3, +2.0] | +2.1 [-0.2, +4.5] |
| BTCUSD | 2024-26 | -0.7 [-2.3, +0.9] | -2.4 [-5.5, +0.6] | -1.8 [-5.1, +1.6] |
| BTCUSD | 2020-23 | -0.4 [-2.1, +1.4] | +0.5 [-2.7, +3.8] | +2.8 [-0.8, +6.4] |

**Table 3. Mean move in the bias's direction minus the no-skill guess.** In hourly ATR at 4 h and daily ATR at 24 h and 72 h. Day blocks.

| Market | Period | 4 h | 24 h | 72 h |
|---|---|---|---|---|
| XAUUSD | 2024-26 | **+0.097 [+0.034, +0.157]** | +0.036 [-0.007, +0.082] | +0.090 [+0.001, +0.188] |
| XAUUSD | 2017-23 | +0.032 [-0.021, +0.081] | +0.003 [-0.035, +0.041] | -0.025 [-0.101, +0.046] |
| EURUSD | 2024-26 | +0.021 [-0.092, +0.132] | -0.020 [-0.101, +0.058] | +0.006 [-0.138, +0.148] |
| EURUSD | 2017-23 | +0.019 [-0.053, +0.088] | +0.021 [-0.024, +0.066] | 0.000 [-0.088, +0.088] |
| NAS100 | 2024-26 | +0.010 [-0.054, +0.081] | -0.045 [-0.100, +0.008] | -0.050 [-0.129, +0.022] |
| NAS100 | 2017-23 | -0.005 [-0.058, +0.047] | -0.022 [-0.058, +0.012] | +0.004 [-0.048, +0.062] |
| BTCUSD | 2024-26 | +0.023 [-0.036, +0.086] | +0.019 [-0.034, +0.074] | +0.038 [-0.069, +0.155] |
| BTCUSD | 2020-23 | +0.067 [-0.008, +0.144] | **+0.123 [+0.040, +0.218]** | **+0.231 [+0.085, +0.401]** |

Only the three bold cells survive longer blocks:
- Gold 4 h with month blocks: [+0.023, +0.161].
- BTC with 7-day blocks: [+0.029, +0.234] and [+0.034, +0.463].
- BTC with 28-day blocks: [+0.032, +0.217] and [+0.045, +0.428].

Gold's 72 h cell does not survive: with week blocks it is [-0.024, +0.213].

### How steady is it?

**Table 4. Changes of each timeframe's reading per month** (IS / OOS).

| Market | 1M | 1W | 1D | 4H | 1H |
|---|---|---|---|---|---|
| XAUUSD | 0.06 / 0.12 | 0.37 / 0.77 | 3.2 / 3.9 | 19.9 / 21.6 | 81.9 / 80.6 |
| EURUSD | 0.2 / 0.2 | 0.9 / 0.8 | 4.3 / 4.5 | 25.6 / 26.2 | 101.0 / 98.5 |
| NAS100 | 0.09 / 0.16 | 0.73 / 0.73 | 4.3 / 4.1 | 24.9 / 23.7 | 91.8 / 89.2 |
| BTCUSD | 0.24 / 0.12 | 0.73 / 0.70 | 5.4 / 4.7 | 30.5 / 29.8 | 125.9 / 117.0 |

A 1H reading stands a median of about 4 hours in every market. BTC has more 1H closes a month because it trades every hour.

**Table 5. How long a tradable decision lasts, and how it ends** (IS / OOS). Durations are in hours the market is open.

| Market | Median length (quartiles) | Lasts 1 hour | Ends by flipping to the other side | 1H changed at the end (1H alone) | Comes back on the same side |
|---|---|---|---|---|---|
| XAUUSD | 6 h (3-10) / 5 h (3-10) | 13.4 / 12.4 % | 0 of 657 / 8 of 1,655 | 93.8 / 93.5 % (90.3 / 88.5 %) | within 25 h: 73.7 / 70.7 % |
| EURUSD | 4 h (2-8) / 5 h (2-9) | 17.8 / 14.1 % | 0 of 410 / 0 of 1,011 | 98.5 / 98.1 % (97.3 / 96.4 %) | next decision: 94.1 / 94.9 % |
| NAS100 | 5 h (3-10) / 5 h (3-9) | 12.2 / 10.7 % | 0 of 433 / 0 of 1,162 | 96.3 / 96.7 % (91.0 / 92.9 %) | next decision: 96.1 / 96.6 % |
| BTCUSD | 5 h (2-10) / 5 h (2-10) | 12.6 / 15.3 % | 1 of 341 / 0 of 432 | 81.8 / 87.0 % (77.1 / 80.3 %) | next decision: 89.1 / 89.8 % |

### How much do data differences move it?

**Table 6. Noise of half a spread.** Share of hours whose long/none/short decision changes. Five-seed mean [range]; then the check's own seed.

| Market | Noise | 2024-26 | 2017-23 | Tradable hours lost (IS / OOS) | Side reversed |
|---|---|---|---|---|---|
| XAUUSD | ±0.2 USD | 2.14 % [1.86-2.33]; check 1.71 % | 5.41 % [4.72-5.89]; check 5.61 % | 3.3 / 9.6 % | none / at most 0.05 % of hours |
| EURUSD | ±0.5 pip | 2.23 % [1.86-2.47]; check 2.24 % | 2.15 % [1.93-2.29]; check 2.12 % | 8.3 / 6.9 % | never |
| NAS100 | ±1 point | 1.15 % [0.90-1.45]; check 1.12 % | 2.99 % [2.75-3.19]; check 2.94 % | 3.6 / 7.3 % | never |
| BTCUSD | ±10 USD | 0.83 % [0.70-0.99]; check 0.81 % | 1.83 % [1.48-2.24]; check 2.24 % | 2.3 / 4.6 % (check 6.7 % OOS) | never |

- The noise works almost entirely through the 1H and the 4H.
  - The 1H reading changes in 3-10 % of 2024-26 hours.
  - The month never moved, except in one NAS100 seed (OOS).
  - The week moved in at most 0.85 % of hours, in the five-seed means. The checks' own seeds went higher: 1.41 % for EURUSD IS, 1.97 % for NAS100 OOS and 2.28 % for gold OOS.
- Since one point or 0.2 USD is a smaller share of today's ranges, the effect is smallest now. For gold it fell from 6.1 % in 2017 to 0.6 % in 2026; for NAS100 from 7.3 % to 0.65 %.

Other probes:
- **A second real feed.** No FTMO candles were available, so OANDA was used, January to September 2026.
  - Gold: the decision differs in 3.0 % of hours.
  - NAS100: 3.9 % of hours. With OANDA's own weekly and monthly bars, which are built differently, it is 6.2 %.
  - Never a flip. Real feeds differ in their opens, not by small random noise. That is why their effect is several times the noise test's.
- **The candle grid.**
  - Gold, cut one hour early (16:00 New York): about a third of the 4H readings change (31.8 / 31.7 % of hours) and 7.2 / 10.0 % of the decisions. 15 of 143 and 66 of 371 ledger trades would not have been allowed.
  - BTC on UTC-midnight candles instead of New York ones: the trade state changes in 14.0 % of 2024-26 hours.
  - BTC with the week starting Sunday instead of Saturday 17:00 New York: the weekly reading changes in 18-19 % of hours, but the trade state only in 0.4 %.
  - EURUSD and NAS100 are already on FTMO's cut. Moving NAS100's weekly stamp to MT5's Sunday 00:00 server time changed 0 hours.

### What can make a reading wrong

**1. Data differences.**
- The candle grid matters most: where the day and the 4H are cut. Next comes how much history the server delivers.
  - BTC's research files start in 2020, so its monthly view reads 50/50 in every hour of 2020-21. Then only the scalp combination could trade.
  - The live window asks MT5 for 72 monthly and 120 weekly bars against lookbacks of 60 and 104. Whether FTMO's server holds that much was not checked.
- A different feed changes a few percent of hours; spread-sized noise changes 1-2 %.
- None of these turned a long into a short. They add or remove permissions.
- The HistData research files miss many 1H candles in February-July 2023, for gold, EURUSD and NAS100. NAS100 also has a 9-day hole in February 2017. Leaving those months out changes the OOS 24 h hit rate by less than half a point for EURUSD and NAS100. For gold this was not measured.

**2. Readings right after a big move.** There is no reliable pattern.
- A short-term pullback after a big push in the bias's direction shows in some market-periods, but never clearly in both periods of one market.
  - Gold 2024-26: after more than 2 daily ATR in 24 hours, the 4 h hit rate was 39.2 % against 51.3 %. That is 74 hours on 21 days, and the difference is -12.1 points [-25.1, +0.2]. In 2017-23: -5.3 points [-15.5, +3.2].
  - EURUSD 2024-26: after a 1-2 daily ATR run, the 24 h hit rate was 35.4 % [25.4, 45.3] (week blocks). In 2017-23 the same cut scored 51.1 %, and 66.4 % after runs of more than 2 ATR.
  - NAS100: after a 24-hour move of at least one daily ATR, the next day went the bias's way 45.0 % against 54.2 % otherwise (IS, -9.2 points [-21.6, +3.9]). OOS: 48.1 % against 53.8 % (-5.7 [-13.1, +1.9]). This cut counts moves in either direction, but nearly all of them were in the bias's direction.
  - BTC: after a 1H candle of more than 2 ATR in the bias's direction, the 4 h hit rate was 45.8 % (IS) and 45.0 % (OOS). The 7-day intervals reach 51.9 % and 51.3 %.
- At 72 hours, big pushes tended to continue rather than reverse.
  - Gold: 62.2 % against 52.9 % (IS) and 56.7 % against 51.8 % (OOS).
  - BTC: 59.2 % [30.5, 76.9] (IS) and 77.3 % [65.1, 86.7] (OOS), after more than 2 daily ATR in 24 hours.

**3. The 1H flipping.**
- The 1H reading changes 80-126 times a month and decides when a permission starts and ends. On its own it does not tell the direction.
  - EURUSD's 1H alone was right 48.3 % [46.9, 49.6] (IS) and 48.9 % [48.0, 49.8] (OOS) of the time over 4 hours.
  - BTC's 1H alone was 3.5 [2.3, 4.7] (IS) and 4.1 [3.0, 5.2] (OOS) points below the no-skill guess over 4 hours.
  - Gold's 1H alone was slightly positive in move size (+0.041 [+0.004, +0.076] OOS, day blocks).
  - NAS100's 1H alone was within 0.7 points of the guess over 24 hours.
- It is also the reading that small noise moves most.
- So when a permission ends, it is usually the 1H going 50/50 while the higher timeframes stand still. The same side tends to come back within a day.

### Trades through the bias

**Table 7. Ledger trades.** Net of the 0.10R cost per trade. The interval is for the mean R, from a bootstrap over trades.

| Market | 2024-26 | 2017-23 |
|---|---|---|
| XAUUSD | 143 trades, 49 % won, +0.50R [+0.21, +0.80], +71.8R | 371 trades, 30 %, -0.17R [-0.32, -0.01], -62.2R |
| EURUSD | 47 trades, 46.8 %, +0.84R [+0.20, +1.55], +39.5R | 97 trades, 25.8 %, -0.01R [-0.40, +0.42], -1.2R |
| NAS100 | 43 trades, 46.5 %, +0.765R [+0.09, +1.47], +32.9R | 100 trades, 32.0 %, +0.288R [-0.18, +0.84], +28.8R |
| BTCUSD | 95 trades, 50.5 %, +0.240R [-0.10, +0.65], +22.8R | 59 trades (2020-06 to 2023), 44.1 %, -0.065R [-0.37, +0.25], -3.8R |

- Most splits by combination, aligned count or 4H/1D agreement do not repeat between periods.
- The few that repeat within one market point different ways in different markets:
  - 5 aligned was gold's weakest group in both periods, but EURUSD's strongest (on 3 and 16 trades);
  - BTC's 3-aligned trades beat its 4-aligned ones in both periods;
  - NAS100's 4-aligned trades beat its 3-aligned ones in both periods.
- The groups are small. The only differences that were tested (gold) were not significant.

---

## XAUUSD (gold)

Tradable when at least three timeframes agree with the 1H among them, except exactly M+W+1H. The matches that occur are 1D+1H, 4H+1H, M+W+D and M+D+1H. There is no veto and no scalp. The bias was tradable 30.7 % of the time in 2024-26 (81.7 % long) and 29.1 % in 2017-23 (55.1 % long).

**Direction at the tradable hours.** Day blocks. Mean moves are in hourly ATR at 4 h and daily ATR at 24 h and 72 h.

| Period | Horizon | Hit rate | No-skill | Difference, points | Mean move its way | Difference |
|---|---|---|---|---|---|---|
| 2024-26 (4,959 h) | 4 h | 54.1 % [51.8, 56.2] | 52.7 % | +1.4 [-0.3, +2.9] | +0.174 [+0.099, +0.243] | +0.097 [+0.034, +0.157] |
| | 24 h | 54.9 % [51.3, 58.6] | 54.1 % | +0.8 [-1.8, +3.5] | +0.114 [+0.051, +0.176] | +0.036 [-0.007, +0.082] |
| | 72 h | 57.5 % [53.3, 61.8] | 56.3 % | +1.2 [-1.7, +4.5] | +0.288 [+0.161, +0.418] | +0.090 [+0.001, +0.188] |
| 2017-23 (11,849 h) | 4 h | 49.2 % [47.7, 50.6] | 50.0 % | -0.8 [-2.3, +0.6] | +0.037 [-0.018, +0.087] | +0.032 [-0.021, +0.081] |
| | 24 h | 49.1 % [46.8, 51.5] | 50.1 % | -1.1 [-3.4, +1.2] | +0.007 [-0.032, +0.047] | +0.003 [-0.035, +0.041] |
| | 72 h | 48.3 % [45.4, 50.9] | 50.3 % | -2.0 [-4.8, +0.6] | -0.017 [-0.094, +0.057] | -0.025 [-0.101, +0.046] |

- **The one effect that holds is short, and only in 2024-26.**
  - Over 4 hours, price moved about a tenth of an hourly candle further the bias's way than the guess. Month blocks: [+0.023, +0.161].
  - Against each calendar year's own drift it is +0.102 [+0.017, +0.165].
  - After long calls, price moved 0.32 hourly ATR [+0.11, +0.49] more than after short calls (month blocks). But it went up only 4.5 points more often [-0.7, +9.2].
  - In 2017-23 the up share after long calls was 1.5 points lower than after short calls [-4.2, +1.1].
- **Simply being long did as well.** On the same 2024-26 hours, always-long was right 54.3 / 56.4 / 59.8 % of the time. Bias minus always-long (month blocks):
  - 4 h: -0.2 [-1.7, +1.4] points;
  - 24 h: -1.5 [-4.8, +1.6];
  - 72 h: -2.2 [-5.7, +0.9].
- **Against each year's own up share** (2024-26), which removes the credit for being long in gold's best years:
  - hit rate: +1.3 [-1.1, +3.0], +0.3 [-2.7, +2.6] and +0.9 [-4.2, +4.5] points at 4, 24 and 72 h;
  - 24 h move: +0.040 [-0.018, +0.086].
- **Splits, 24 h, against the same-hours guess.**
  - Timeframes aligned, 2024-26 (3 / 4 / 5): 48.8 % against 50.2 %; 58.1 % against 57.2 %; 57.2 %, all long, so no different from always-long.
  - Timeframes aligned, 2017-23 (3 / 4 / 5): 49.7 % against 50.0 %; 48.9 % against 50.1 %; 45.8 % against 52.7 % (-6.9 [-12.9, -1.6], day blocks only, one of many subgroups).
  - Combinations, 2017-23:
    - M+W+D: 44.4 % against 51.5 % (-7.1 [-12.8, -1.8], day blocks).
    - D+1H 48.2 % against 50.0 %; 4H+1H 51.9 % against 50.4 %; M+D+1H 50.3 % against 49.9 %.
  - Combinations, 2024-26: all within 3.2 points of the guess.
  - Long and short, against the period's own up and down shares:
    - 2024-26: long 56.9 % against 55.6 %; short 45.8 % against 44.4 %.
    - 2017-23: long 50.6 % against 52.5 %; short 47.2 % against 47.5 %.
  - The scalp mode never occurs.
- **Entry windows** (09-11 and 13-17 Amsterdam):
  - 2024-26 at 4 h: 57.5 % [53.9, 61.1] against 52.2 % for the period's long/short mix. That is +5.3 points, [+1.7, +8.7] with month blocks. A same-hours reference was not computed for this split.
  - 2017-23: 50.4 % against 50.0 %.
- **Per year**, the 4 h hit rate against that year's reference:
  - 2024: 53.4 % against 53.1 %; 2025: 55.1 % against 54.4 %; 2026: 53.6 % against 50.0 %.
  - Every year of 2017-23 was below its reference (47.6-51.9 % against 49.3-52.7 %).
- **Refused hours were no worse than tradable ones.**
  - Refused only because the 1H did not agree (4,411 h, 2024-26): 54.4 % against 52.9 % at 4 h.
  - Refused as exactly M+W+1H: 50.6 % against 52.5 % (2024-26), and 45.8 % [41.8, 49.8] against 50.3 % (2017-23).

**Stability** (IS / OOS):
- A daily reading stands a median 92 hours; a 1H reading 4 hours (quartiles 2-8).
- Direct bull-to-bear flips of the daily: 6 of 104 / 29 of 326 changes. The rest pass through 50/50.
- A tradable decision lasts a median 6 / 5 hours, and almost always ends by going neutral (Table 5).

**Data sensitivity:**
- Noise of ±0.2 USD: see Table 6. Ledger trades still allowed: 98.6 % (1-3 of 143 lost per seed) / 90.4 % (29-45 of 371).
- Per timeframe, the share of hours with a different reading (IS / OOS):
  - 1H 5.0 / 11.0 %; 4H 1.6 / 5.2 %; 1D 0.1 / 1.9 %.
  - 1W 0 / 0.7 % (the check's seed: 2.3 % OOS); 1M 0.
- 0.2 USD is 5.9 % of the median hourly ATR in 2017-23 and about 1 % in 2026, which is why the effect shrinks.
- OANDA, January-September 2026 (4,307 hours):
  - The decision differs in 3.0 % of hours; 6.1 % of tradable hours are lost; no flips.
  - Readings differ: 1H 4.5 %, 4H 3.5 %, 1D 3.7 % of hours.
  - OANDA's daily opens differ by a median 2.5 USD.
- Candle grid: research and FTMO both cut at 17:00 New York, so no offset applies.
  - A cut one hour early would change 7.2 / 10.0 % of decisions.
  - A UTC-midnight cut would change 8.1 / 10.2 % of decisions and refuse 19 / 66 ledger trades.
  - In about three weeks a year in 2017-18, HistData's stamps are one hour off; this affects only OOS.

**Trades by bias.** Each cell: trades, won (gross R above zero), mean net R, total net R.

| Group | 2024-26 | 2017-23 |
|---|---|---|
| All | 143, 49 %, +0.50 [+0.21, +0.80], +71.8 | 371, 30 %, -0.17 [-0.32, -0.01], -62.2 |
| Long | 110, 47 %, +0.43, +47.6 | 190, 32 %, -0.07, -13.2 |
| Short | 33, 55 %, +0.73, +24.2 | 181, 28 %, -0.27 [-0.46, -0.06], -49.0 |
| Combination M+W+D | 49, 47 %, +0.48 [-0.02, +1.08], +23.3 | 52, 21 %, -0.28, -14.4 |
| Combination M+D+1H | 12, 75 %, +1.08, +12.9 | 50, 30 %, -0.20, -10.0 |
| Combination D+1H | 33, 39 %, +0.31 [-0.33, +0.98], +10.2 | 151, 30 %, -0.13, -20.0 |
| Combination 4H+1H | 49, 51 %, +0.52 [+0.06, +1.04], +25.5 | 118, 32 %, -0.15, -17.8 |
| 3 aligned | 46, 46 %, +0.53, +24.4 | 212, 34 %, -0.06, -12.8 |
| 4 aligned | 65, 52 %, +0.58, +38.0 | 130, 25 %, -0.31 [-0.54, -0.04], -40.0 |
| 5 aligned | 32, 47 %, +0.29 [-0.20, +0.82], +9.4 | 29, 21 %, -0.33, -9.5 |
| 4H and 1D both agree | 72, 50 %, +0.45 [+0.07, +0.84], +32.5 | 179, 27 %, -0.23 [-0.45, -0.01], -41.6 |
| Only the 4H agrees | 49, 51 %, +0.52, +25.5 | 118, 32 %, -0.15, -17.8 |
| Only the 1D agrees | 22, 41 %, +0.63, +13.9 | 74, 31 %, -0.04, -2.8 |

By aligned set (2024-26 | 2017-23):
- M+W+D+4H+1H: 32, 47 %, +0.29, +9.4 | 29, 21 %, -0.33, -9.5
- M+W+4H+1H: 29, 52 %, +0.48, +14.0 | 29, 24 %, -0.40, -11.5
- D+4H+1H: 21, 48 %, +0.62, +13.0 | 72, 32 %, -0.12, -8.5
- M+W+D+1H: 17, 47 %, +0.82, +13.9 | 23, 22 %, -0.21, -4.9
- M+4H+1H: 15, 47 %, +0.33, +5.0 | 52, 29 %, -0.20, -10.6
- M+D+4H+1H: 11, 82 %, +1.27, +14.0 | 28, 29 %, -0.31, -8.7
- W+D+4H+1H: 8, 25 %, -0.49, -3.9 | 50, 24 %, -0.30, -14.9
- W+4H+1H: 5, 60 %, +1.29, +6.5 | 37, 43 %, +0.11, +4.2
- W+D+1H: 4, 25 %, +0.27, +1.1 | 29, 38 %, +0.12, +3.4
- M+D+1H: 1, 0 %, -1.10, -1.1 | 22, 32 %, -0.06, -1.3

**More agreement did not help, and the differences are not significant.**
- The most-agreeing groups were the weakest in both periods: 5 aligned in 2024-26 (+0.29R a trade, against +0.53 and +0.58R), and 4-5 aligned in 2017-23.
- None of these differences is significant:
  - 2017-23, 4-5 aligned minus 3 aligned: -0.25R [-0.55, +0.08];
  - 2017-23, 4H and 1D both agreeing minus one agreeing: -0.12R [-0.44, +0.18];
  - 2024-26, 5 aligned minus the rest: -0.27R [-0.89, +0.35].

**Settled results, with their numbers.**
- **M+W+1H as a match** (14 October):
  - 2024-26: 27 added trades, 33 % won, +0.5R on their own (+1.6R for the whole run).
  - 2017-23: 37 added trades, 14 % won, -24.9R (-24.7R for the run).
- **Reversal trades against the bias** (7 October). Recount of the REV rows, 2024-01 to 2026-09, after costs:
  - A: 32 trades, 16 % won, -22.5R. B: 6 trades, 0 %, -6.6R.
  - C: 95 trades, 28 %, -26.5R. D: 60 trades, 23 %, -25.8R.
  - The README's gross figures: 31 / 6 / 90 / 55 trades, -18.7 / -6.0 / -16.0 / -17.4R.
  - No 2017-23 reversal run exists.

**What the check corrected.**
- **The baseline.** The study scored its reference over all hours of the period. On the same hours, the 2024-26 hit edges shrink from +1.9 / +1.3 / +2.6 to +1.4 / +0.8 / +1.2 points, and every interval includes zero.
- **Gold's rise.** Against each year's own drift, only the 4 h move survives.
- **Overlapping windows.** These side results lose significance with week or month blocks:
  - the OOS calendar-72 h edge;
  - "the 1D alone runs against the move at 72 h" (OOS);
  - "the 1W alone at 72 h" (IS);
  - the IS 24 h move edge.
- **The big-move warning** rests on 74 hours. Those same hours did better than the reference at 72 h.
- **The trade tables.** "More agreement did worse" is not significant; read it as "no evidence that more agreement helps".
- **Not found:** no forming candle at any of the 56,906 hours, no grid error and no arithmetic error.

**Verdict for gold.** The bias is read exactly as tested and it is steady; only the 1H switches the permission on and off. As a direction call it is weak.
- **2024-26.** This was a strong gold bull market, and 82 % of the tradable hours were long.
  - Price went the bias's way about as often as the same-mix guess (54.9 % against 54.1 % over 24 hours), and no more often than simply being long.
  - The one effect that holds is short: over 4 hours, about a tenth of an hourly candle more in the bias's direction.
- **2017-23.** That effect and every other is gone (49.1 % against 50.1 % at 24 hours), and the 371 trades taken under the bias lost 62.2R.
- **What can make a reading wrong:**
  - the candle cut: one hour off changes a third of the 4H readings and 7-10 % of decisions;
  - a different feed: 3 % of 2026 hours;
  - spread-sized noise: 0.6 % of 2026 hours.
- **Treat it as a short-term momentum filter that worked in the 2024-26 trend, not as an edge.**

---

## EURUSD

Tradable exactly when the 1D and the 1H read the same side and neither the 1W nor the 4H reads the other side. The match is:
- M+W+D when the month and week also agree;
- otherwise M+D+1H when the month agrees;
- otherwise D+1H.

The scalp and M+D+4H can never be reached. The bias was tradable 14.1 % of the time in 2024-26 (53.8 % long) and 15.2 % in 2017-23 (43.7 % long).

**Direction at the tradable hours.** Day blocks.

| Period | Horizon | Hit rate | No-skill | Difference, points | Mean move its way | Difference |
|---|---|---|---|---|---|---|
| 2024-26 (2,400 h) | 4 h | 49.7 % [46.6, 52.8] | 50.0 % | -0.3 [-3.4, +2.8] | +0.022 [-0.094, +0.138] | +0.021 [-0.092, +0.132] |
| | 24 h | 49.9 % [44.4, 55.3] | 49.6 % | +0.3 [-5.2, +5.5] | -0.025 [-0.108, +0.054] | -0.020 [-0.101, +0.058] |
| | 72 h | 50.6 % [45.0, 56.4] | 50.1 % | +0.5 [-5.2, +6.4] | +0.007 [-0.136, +0.147] | +0.006 [-0.138, +0.148] |
| 2017-23 (6,501 h) | 4 h | 50.3 % [48.4, 52.1] | 50.0 % | +0.3 [-1.7, +2.1] | +0.021 [-0.052, +0.089] | +0.019 [-0.053, +0.088] |
| | 24 h | 49.3 % [46.2, 52.3] | 50.2 % | -0.9 [-3.9, +2.1] | +0.021 [-0.024, +0.066] | +0.021 [-0.024, +0.066] |
| | 72 h | 48.9 % [45.2, 52.4] | 50.1 % | -1.2 [-4.9, +2.3] | -0.008 [-0.096, +0.078] | 0.000 [-0.088, +0.088] |

- **Week-block hit intervals** at 4 / 24 / 72 h:
  - 2024-26: [46.5, 52.4] / [43.5, 55.5] / [41.7, 58.4];
  - 2017-23: [48.6, 52.0] / [45.7, 52.7] / [43.8, 53.6].
- **Move after long calls minus after short calls:** every interval contains zero.
  - 2024-26: +0.042, -0.040 and +0.011.
  - 2017-23: +0.039, +0.043 and 0.000.
- **Timeframes aligned**, hit rate at 4 / 24 / 72 h. There is no order by count.
  - 2024-26:
    - 2 aligned: 50.5 / 45.6 / 42.1.
    - 3 aligned: 51.8 / 51.0 / 59.4. The 72 h cell has week-block interval [47.8, 69.7].
    - 4 aligned: 47.6 / 47.6 / 46.6.
    - 5 aligned: 47.9 / 62.4 / 40.2 (194 hours on 28 days).
  - 2017-23: 2 aligned 48.3 / 51.9 / 53.8; 3 aligned 49.9 / 52.6 / 52.7; 4 aligned 50.5 / 45.9 / 46.3; 5 aligned 51.8 / 49.3 / 44.8.
- **Other splits, 24 h** (2024-26 / 2017-23):
  - Combinations: D+1H 48.8 / 49.6 %; M+D+1H 49.0 / 52.5 %; M+W+D 56.9 / 47.4 %.
  - The 4H agreeing: 51.4 / 48.7 %. The 4H at 50/50: 47.0 / 50.7 %.
  - Longs: 45.6 / 47.3 %. Shorts: 54.9 / 50.9 %. In 2024-26 the tradable hours fell more often than they rose (up share 45.4 %); the long and short numbers mirror that.
- **Entry windows** (4 / 24 / 72 h):
  - 2024-26: 52.1 [46.3, 57.7] / 47.2 [40.0, 54.4] / 52.2 [44.4, 59.5].
  - 2017-23: 50.8 [47.5, 54.1] / 50.7 [46.5, 54.7] / 48.9 [44.2, 53.4].
- **Each timeframe alone:** none is above 52 % in both periods. The 1H and 4H alone are slightly contrarian at 4 h. This is a 1-2 point effect, one of about 30 such tests.
- **A race to ±0.5 or ±1 daily ATR:**
  - 2024-26: 53.6 % [48.1, 58.9] and 55.1 % [48.8, 61.4], against 49.6 % for a direction-blind call.
  - 2017-23: 50.8 % and 49.6 %.
  - These intervals use day blocks only.
- **Per year:** the 24 h hit rate wanders from 42.9 % (2019) to 56.0 % (2020).
- **Refusals,** corrected by the check:
  - The permissions the 1W/4H veto removed (1D and 1H on one side, the 1W or 4H against) went the refused way:
    - 2024-26 (1,154 h): 46.0 / 49.3 / 56.8 %.
    - 2017-23 (2,667 h): 48.5 / 46.4 / 45.1 %.
    - Their 72 h move, +0.232 (IS) and -0.123 (OOS), does not hold with week blocks.
  - The permissions removed by the 1H requirement went the refused way 43.8 % [35.2, 52.9] (IS, 867 h) and 49.3 % [44.7, 54.1] (OOS, 3,466 h) over 24 h.
  - So the refused hours are neither clearly worse nor clearly better.

**Stability** (IS / OOS):
- A 1H reading lasts 5.1 / 5.2 hours on average; a daily one 120 / 113 hours. 93-95 % of daily changes pass through 50/50.
- Of the permissions that ended because the 1H alone turned while the day held, 73.2 / 74.4 % came back on the same side within 24 trading hours.

**Data sensitivity:**
- Noise of ±0.5 pip: see Table 6. No flips. 1.24 / 1.29 % of non-tradable hours gained a permission.
- Readings changed (IS / OOS):
  - 1H 9.5 / 7.7 %; 4H 5.2 / 4.2 %; 1D 1.2 / 1.2 %; 1M 0.
  - 1W 0.85 / 0.26 %. Two of the five seeds moved the same three weekly closes of 2024.
- At their signal hour, 3-7 of 47 IS trades (mean 5.0) and 6-12 of 97 OOS trades (mean 9.4) would not have been allowed under noise. What the backtest would have done instead was not rerun.
- **Candle grid.** The research candles sit on FTMO's 17:00 New York anchor; every stamp since 2016-06 was checked. The live code converts server stamps with their own daylight-saving offset. A misread server offset was not measured; gold's probe shows the scale.
- **No second real feed was compared.**
- **The 2023 gap.**
  - The research 1H misses 781 hours in February-July 2023.
  - Without those months the OOS 24 h hit rate is 48.9 % (49.3 % with them).
  - The 7 OOS trades in the gap made +4.6R. Without them: 90 trades, 25.6 % won, -5.9R.

**Trades by bias.** Each cell: trades, won, mean net R, total net R.
- The 1D agreed with every trade, because the profile requires it.
- The 4H never disagreed, because the veto removes those trades.

| Group | 2024-26 | 2017-23 |
|---|---|---|
| All | 47, 46.8 % [31.9, 61.7], +0.84 [+0.20, +1.55], +39.5 | 97, 25.8 % [17.5, 34.0], -0.01 [-0.40, +0.42], -1.2 |
| Long | 26, 50.0 %, +1.09, +28.4 | 43, 32.6 %, +0.39, +16.7 |
| Short | 21, 42.9 %, +0.53, +11.1 | 54, 20.4 %, -0.33, -17.9 |
| Combination D+1H | 34, 41.2 %, +0.53, +18.0 | 65, 23.1 %, -0.09, -6.0 |
| Combination M+D+1H | 9, 55.6 %, +1.04, +9.4 | 10, 30.0 %, +0.32, +3.2 |
| Combination M+W+D | 4, 75.0 %, +3.04, +12.2 | 22, 31.8 %, +0.07, +1.5 |
| 2 aligned | 7, 28.6 %, +0.15, +1.1 | 17, 17.6 %, -0.58, -9.9 |
| 3 aligned | 22, 54.5 %, +1.09, +24.1 | 38, 23.7 %, +0.15, +5.7 |
| 4 aligned | 15, 40.0 %, +0.69, +10.4 | 26, 23.1 %, -0.20, -5.3 |
| 5 aligned | 3, 66.7 %, +1.33, +4.0 | 16, 43.8 %, +0.51, +8.1 |
| 4H agrees (1D always agrees) | 26, 50.0 %, +0.63, +16.4 | 48, 29.2 %, +0.02, +0.9 |
| 4H at 50/50 | 21, 42.9 %, +1.10, +23.2 | 49, 22.4 %, -0.04, -2.2 |

By aligned set (2024-26 | 2017-23):
- D+1H: 7, 28.6 %, +0.15, +1.1 | 17, 17.6 %, -0.58, -9.9
- D+4H+1H: 9, 66.7 %, +1.13, +10.2 | 12, 8.3 %, -0.71, -8.5
- W+D+1H: 9, 44.4 %, +1.05, +9.5 | 21, 28.6 %, +0.57, +12.0
- W+D+4H+1H: 9, 22.2 %, -0.30, -2.7 | 15, 33.3 %, +0.03, +0.4
- M+D+1H: 4, 50.0 %, +1.11, +4.4 | 5, 40.0 %, +0.45, +2.3
- M+D+4H+1H: 5, 60.0 %, +0.98, +4.9 | 5, 20.0 %, +0.18, +0.9
- M+W+D+1H: 1, 100 %, +8.17, +8.2 | 6, 0 %, -1.10, -6.6
- M+W+D+4H+1H: 3, 66.7 %, +1.33, +4.0 | 16, 43.8 %, +0.51, +8.1

- **A market with no direction** would let each trade reach its target before its stop 1/(1+R:R) of the time: 23.3 % (IS) and 24.8 % (OOS) for these trades.
  - The trades won 46.8 % in 2024-26.
  - In 2017-23 they won 25.8 %, exactly the directionless rate.
- **By count, 5 aligned did best and 2 aligned worst in both periods.**
  - 2024-26: +1.33R and +0.15R a trade, on 3 and 7 trades.
  - 2017-23: +0.51R and -0.58R, on 16 and 17 trades.
  - No test of these differences was run, and the hourly readings show no such order.
- **Shorts with the 4H at 50/50:** +3.9R (9 trades, IS) but -21.2R (28 trades, 10.7 % won, OOS).

**Settled results, with their numbers.**
- **M+W+1H as a match** (14 October), after costs:
  - 2024-26: 15 added trades, 6.7 % won, -9.2R. The whole run: 62 trades, +30.3R, against 47 trades, +39.5R without it.
  - 2017-23: 63 added trades, 20.6 % won, -11.8R. The run: 160 trades, -13.0R, against 97 trades, -1.2R.
- **Reversal trades against the bias** (7 October; February 2024 to September 2026 only; no OOS run exists). After costs, gross in brackets:
  - A: 54 trades, 33.3 % won, -3.0R (+2.4R).
  - B: 11 trades, 27.3 %, +5.4R (+6.5R). Two trades of 8.3R and 6.1R carry it.
  - C: 138 trades, 28.3 %, -8.5R (+5.3R).
  - D: 90 trades, 28.9 %, -6.9R (+2.1R).
  - On EURUSD the reversals lost only after costs.

**What the check corrected.**
- **The "price goes against a fresh reading" sentence quoted the wrong statistic.** At the first hour of a new reading, over 4 h:
  - the 1H is right 47.9 % [45.5, 50.2] (IS) and 48.6 % [47.2, 50.0] (OOS);
  - the 4H is right 47.1 % (IS) but 52.4 % [49.4, 55.3] (OOS), the wrong sign.
- **The refusal comparisons used the wrong set of hours.** The corrected numbers are given above. The true range is about 44-57 %, not 47.6-52.1 %.
- **Several 72 h splits are too narrow on day blocks:** 3 aligned, the 1D in non-tradable hours, and the 1W alone. The 1-2 ATR big-move cut holds with week blocks.
- **The study did not report the 2023 data gap.**
- **Counts:**
  - non-tradable hours are 14,621 / 36,236;
  - the 1W noise changes were three weekly closes, not one;
  - the repository's HEAD has moved on, but without changes on the bias path.
- **Not found:** no look-ahead and no grid error. The baselines were correct. The engine matched at all 59,758 hours.

**Verdict for EURUSD.**
- **As a direction call it is a coin**, in both periods and at every horizon: 49.7 / 49.9 / 50.6 % in 2024-26 and 50.3 / 49.3 / 48.9 % in 2017-23, against a same-mix guess of about 50 %. Every interval sits around zero, and no split rescues it.
- **It works as a gate.** It keeps the bot on the day's side and out of about 85 % of the hours, and the 1H switches the permission on and off within the day.
- **The trades through that gate** made +0.84R a trade in 2024-26 and -0.01R in 2017-23. Nothing measured here credits the 2024-26 result to the bias knowing the direction.
- **Half a pip of noise** changes about 2 % of decisions and would have stopped about 1 in 10 past trades at the signal hour, but never flips a side.
- **Do not read more aligned timeframes as more certainty.**

---

## NAS100

A valid match is M+W+D or M+D+1H with the 1H aligned (full), or the scalp D+4H+1H. The 1W must not be against. The bias was tradable 18.6 % of the time in 2024-26 (89.5 % long; scalp 13 % of tradable hours) and 19.6 % in 2017-23 (84.3 % long; scalp 22 %).

**Direction at the tradable hours.** Clock horizons, day blocks.

| Period | Horizon | Hit rate | No-skill | Difference, points | Mean move its way | Difference |
|---|---|---|---|---|---|---|
| 2024-26 (2,978 h) | 4 h | 54.3 % [51.4, 57.2] | 53.6 % | +0.7 [-1.0, +2.6] | +0.082 [-0.050, +0.211] | +0.010 [-0.054, +0.081] |
| | 24 h | 52.9 % [47.8, 57.7] | 54.0 % | -1.1 [-3.9, +1.8] | -0.015 [-0.097, +0.065] | -0.045 [-0.100, +0.008] |
| | 72 h | 54.4 % [48.6, 60.0] | 54.4 % | 0.0 [-3.5, +3.4] | -0.047 [-0.184, +0.082] | -0.050 [-0.129, +0.022] |
| 2017-23 (7,880 h) | 4 h | 52.6 % [50.9, 54.3] | 52.8 % | -0.2 [-1.3, +1.1] | +0.038 [-0.037, +0.113] | -0.005 [-0.058, +0.047] |
| | 24 h | 52.9 % [49.7, 56.1] | 53.0 % | -0.1 [-2.3, +2.0] | +0.014 [-0.034, +0.061] | -0.022 [-0.058, +0.012] |
| | 72 h | 57.1 % [53.8, 60.4] | 55.1 % | +2.1 [-0.2, +4.5] | +0.052 [-0.022, +0.127] | +0.004 [-0.048, +0.062] |

- **Longer blocks.** With week blocks the 24 h intervals barely move: [46.9, 58.4] and [49.5, 56.1]. The 72 h difference becomes [-3.9, +3.8] (IS) and [-1.3, +5.6] (OOS).
- **Weekends.** The clock horizons stop at weekends: 17.0 / 15.6 % of the 24 h windows end before 20 hours. Counting candles instead gives the same picture. At 24 h it gives 53.9 % against 55.2 % for the guess (IS) and 54.3 % against 54.2 % (OOS).
- **What the bias mostly says is "the index tends to rise".** A guess with the same long share already knows that.
- **Splits, 24 h.**
  - Long: 54.5 % [49.1, 59.5] (IS) and 54.3 % [50.8, 57.7] (OOS). Short: 39.6 % [25.3, 53.7] and 45.2 % [37.8, 52.3].
  - Full: 53.7 % and 54.5 %.
  - Scalp: 47.9 % [34.3, 60.5] and 47.1 % [41.1, 53.1]. The IS scalp edge of +7.1 points clears zero on day blocks but not on week blocks ([-2.3, +15.0]). OOS it is -3.6 points [-9.2, +2.0].
  - 3 / 4 / 5 aligned: 43.9 / 56.6 / 52.4 % (IS) and 49.8 / 53.0 / 54.2 % (OOS).
  - Every split is within about ±7 points of its no-skill guess. None clears zero with week blocks.
- **Entry windows, 24 h:** 55.9 % [49.5, 62.2] against 55.4 % (IS); 52.1 % [48.2, 56.1] against 53.0 % (OOS).
- **Each timeframe alone,** 24 h minus no-skill, in points:
  - IS: 1W -0.7, 1D -1.0, 4H -0.9, 1H +0.3. The month read bullish all the time.
  - OOS: 1M +1.5, 1W +1.6, 1D +0.7, 4H -0.5, 1H -0.7.
  - The OOS month and week move edges (+0.04 daily ATR) clear zero only just with month blocks (1M [+0.001, +0.075]) or not at all (1W [-0.001, +0.076]). The month changed only 13 times in 84 months.
- **Hours refused only because the 1H did not agree did as well as tradable hours.**
  - IS: 52.5 % against 52.9 % (-0.4 [-5.7, +4.6]).
  - OOS: 57.2 % against 52.9 %. That is +4.3 [+0.5, +7.9] raw, but +2.0 [-0.8, +5.0] after allowing for those hours' long/short mix (both with week blocks).

**Stability:**
- The side itself reversed only 17 times in 33 months (IS) and 40 times in 84 months (OOS). A same-side run lasts a median 28.9 / 28.8 days.
- Within it, tradable decisions come 13.1 / 13.9 times a month and last a median 5 market hours (Table 5).
- The 1H alone ended 91.0 / 92.9 % of them, always to no trade.

**Data sensitivity:**
- **Noise of ±1 point:** see Table 6. Readings changed (IS / OOS):
  - 1H 3.3 / 7.9 %; 4H 1.5 / 3.6 %.
  - 1D 0.2 / 1.6 % (the check's seed: 2.15 % OOS).
  - 1W 0 / 0.4 %; 1M 0 / 0.2 %.
- **Ledger signals.** Under at least one of the five seeds, 3 of 43 (IS) and 26 of 100 (OOS) ledger signals would have lost their side, always to no trade.
- **Why the effect shrinks.** The noise band (2 points wide) was 31 % of the median 1H range in 2017 and 2.6 % in 2026.
- **OANDA NAS100USD,** January-September 2026 (4,391 hours):
  - The decision changes in 3.9 % of hours, with no flips. Readings differ: 1D 7.3 %, 4H 10.2 %, 1H 11.2 %.
  - With OANDA's own weekly and monthly bars: 6.2 %, and the weekly reading differs in 28.1 % of hours.
  - So the live weekly and monthly must be FTMO's own bars, with their full lookback.
- **Broker offset.** The research daily, 4H and monthly already open at 17:00 New York. Moving the weekly stamp to MT5's Sunday 00:00 server time changed 0 hours. Rebuilding the pre-2016 weekly and monthly bars changed 0 hours.
- **Data holes.** A 9-day hole in February 2017 and about 770 missing 1H hours in February-July 2023. Leaving out February-July 2023: OOS 24 h is 52.5 % against 52.7 %.
- **History depth.** Whether FTMO's server holds enough history (72 monthly and 120 weekly bars requested) was not checked.

**Trades by bias.** Each cell: trades, won, mean net R, total net R.
- The 1D agreed with every trade, because every valid combination contains it.
- The 1W is never against, because of the veto.

| Group | 2024-26 | 2017-23 |
|---|---|---|
| All | 43, 46.5 %, +0.765 [+0.09, +1.47], +32.9 | 100, 32.0 %, +0.288 [-0.18, +0.84], +28.8 |
| Long | 36, 44.4 %, +0.695, +25.0 | 74, 31.1 %, +0.298, +22.1 |
| Short | 7, 57.1 %, +1.127, +7.9 | 26, 34.6 %, +0.258, +6.7 |
| Combination M+W+D | 27, 48.1 %, +0.641 [-0.09, +1.41], +17.3 | 56, 28.6 %, +0.338 [-0.36, +1.18], +18.9 |
| Combination M+D+1H | 6, 50.0 %, +1.834 [-0.60, +4.74], +11.0 | 23, 34.8 %, +0.204 [-0.48, +0.93], +4.7 |
| Scalp D+4H+1H | 10, 40.0 %, +0.459 [-0.75, +1.80], +4.6 | 21, 38.1 %, +0.247 [-0.54, +1.18], +5.2 |
| 3 aligned | 8, 25.0 %, +0.298, +2.4 | 28, 28.6 %, -0.043, -1.2 |
| 4 aligned | 23, 47.8 %, +0.856, +19.7 | 47, 36.2 %, +0.728, +34.2 |
| 5 aligned | 12, 58.3 %, +0.902, +10.8 | 25, 28.0 %, -0.170, -4.2 |
| 4H agrees (1D always agrees) | 26, 50.0 %, +0.765 [-0.03, +1.58], +19.9 | 56, 35.7 %, +0.157 [-0.32, +0.67], +8.8 |
| 4H at 50/50 | 12, 41.7 %, +0.880, +10.6 | 28, 25.0 %, +0.271, +7.6 |
| 4H against | 5, 40.0 %, +0.490, +2.5 | 16, 31.2 %, +0.774 [-0.59, +2.46], +12.4 |

By aligned set (2024-26 | 2017-23):
- M+W+D+4H+1H: 12, 58.3 %, +0.902, +10.8 | 25, 28.0 %, -0.170, -4.2
- M+W+D+1H: 15, 40.0 %, +0.432, +6.5 | 31, 29.0 %, +0.747, +23.2
- W+D+4H+1H: 4, 75 %, +2.184, +8.7 | 6, 50 %, +0.534, +3.2
- M+D+4H+1H: 4, 50 %, +1.119, +4.5 | 10, 50 %, +0.787, +7.9
- M+D+1H: 2, 50 %, +3.264, +6.5 | 13, 23.1 %, -0.245, -3.2
- D+4H+1H: 6, 16.7 %, -0.691, -4.1 | 15, 33.3 %, +0.132, +2.0

Most splits do not repeat between periods:
- 5 aligned was best in 2024-26 and worst in 2017-23.
- The 4H against did best in 2017-23.
- Only 4 aligned beat 3 aligned in both periods, on 8 and 28 trades at 3 aligned. No test of that difference was run.

**Settled results, with their numbers.**
- **Reversal trades against the bias** (7 October; February 2024 to September 2026; no OOS run exists). After costs:
  - A: 31 trades, 16 % won, -17.0R. B: 6 trades, 17 %, -5.1R.
  - C: 89 trades (README: 88), 17 %, -28.6R.
  - D: 51 trades, 24 %, -2.7R (+2.4R before costs).
- **M+W+1H as a match** (14 October):
  - 2024-26: 27 added trades, 25.9 % won, +11.4R.
  - 2017-23: 76 added trades, 15.8 % won, -31.1R.

**What the check corrected.** No headline number changed.
- **Side results that only clear zero on day blocks:** the IS scalp edge, the OOS 3-aligned 72 h move, the bar-count 72 h results, and the OOS 1W reading. They fail with week or month blocks; none feeds the verdict.
- **Framing:**
  - The study's verdict cited M+W+1H only for 2017-23 (-31.1R). It also added +11.4R in 2024-26.
  - "Refused-for-1H hours pointed the right way more often" mostly reflects their higher up share.
- **Unreported:** the weekend cut-off of the clock horizons and the 2017 and 2023 data holes.
- **Not found:** no look-ahead, and every higher-timeframe bar is an exact aggregate of the lower one. The engine matched at every one of the 56,794 hours.

**Verdict for NAS100.** The bias says "long, but not every hour".
- **It is right exactly as often as the index's own drift.** It is long at 84-90 % of the hours it allows a trade. Over 24 hours it is right 52.9 % of the time in both periods, against 54.0 % and 53.0 % for a same-mix guess.
- **No split beats the guess in both periods:** not aligned count, full or scalp, long or short, or entry windows. The hours refused only for the 1H did as well.
- **The readings are solid and robust.** One point of noise changes 1.2 % of 2024-26 hours and OANDA's feed 3.9 %, never a flip.
- **The ledger made money in both periods** (+32.9R and +28.8R). Nothing here credits that to the bias calling the direction.
- **Trust it as a trend gate. Do not read a tradable hour as a forecast.**

---

## BTCUSD

The profile has no 1H requirement and no veto. A match is M+W+D, M+D+1H, M+D+4H or the scalp D+4H+1H.
- 2024-26: tradable 21.8 % of the time; 80.0 % long; scalp 24 %. Matches: M+W+D 56 %, D+4H+1H 24 %, M+D+1H 13 %, M+D+4H 6 %.
- 2020-23: tradable 19.2 % of the time; 31.0 % long; scalp 38 %.

The New York files start in January 2020. So in 2020-23 the monthly view has only 5-48 closed candles instead of 60, and it reads 50/50 in every hour of 2020 and 2021. In those two years only the scalp combination could trade.

**Direction at the tradable hours.** Day blocks.

| Period | Horizon | Hit rate | No-skill | Difference, points | Mean move its way | Difference |
|---|---|---|---|---|---|---|
| 2024-26 (5,252 h) | 4 h | 49.5 % [47.5, 51.4] | 50.2 % | -0.7 [-2.3, +0.9] | +0.013 [-0.068, +0.097] | +0.023 [-0.036, +0.086] |
| | 24 h | 47.9 % [43.7, 52.1] | 50.2 % | -2.4 [-5.5, +0.6] | +0.025 [-0.045, +0.095] | +0.019 [-0.034, +0.074] |
| | 72 h | 48.6 % [43.9, 53.6] | 50.4 % | -1.8 [-5.1, +1.6] | +0.054 [-0.091, +0.193] | +0.038 [-0.069, +0.155] |
| 2020-23 (6,040 h) | 4 h | 49.2 % [47.3, 51.1] | 49.6 % | -0.4 [-2.1, +1.4] | +0.049 [-0.025, +0.127] | +0.067 [-0.008, +0.144] |
| | 24 h | 50.1 % [46.6, 53.8] | 49.6 % | +0.5 [-2.7, +3.8] | +0.091 [+0.017, +0.175] | +0.123 [+0.040, +0.218] |
| | 72 h | 50.2 % [46.0, 54.6] | 47.5 % | +2.8 [-0.8, +6.4] | +0.134 [-0.009, +0.293] | +0.231 [+0.085, +0.401] |

- **2024-26: nothing, and if anything the wrong way.** Price rose less often after long calls than after short calls (-2.3, -7.5 and -5.6 points, not significant).
- **2020-23: an effect in move size, not in hit rate.**
  - After long calls, price moved +0.29 [+0.08, +0.49] daily ATR more than after short calls at 24 h, and +0.54 [+0.11, +1.02] at 72 h (28-day blocks).
  - It did not go up significantly more often.
  - The long calls caught some large rallies: the long-call 72 h hit rate was 61.0 % [54.5, 67.5].
- **A full-history monthly** (the check's proxy, with the UTC monthly from 2015) gives a somewhat better 2020-23:
  - tradable 24.5 % of hours, 46 % long;
  - 24 h hit rate 53.1 % [49.3, 56.7] against 49.6 %, a difference of +3.4 [-0.3, +6.7];
  - 72 h: +5.1 [-0.5, +10.3] (7-day blocks).
  - Still not significant, and the opposite sign to 2024-26.
- **Splits, 24 h** (2024-26 / 2020-23):
  - 3 / 4 / 5 aligned: 46.1 / 48.8 / 54.5 % and 52.0 / 49.4 / 40.1 %.
  - Full 48.3 / 51.3 %; scalp 46.4 / 48.2 %.
  - Long 48.9 / 51.7 %; short 43.6 % [35.2, 51.7] / 49.4 %.
  - Entry hours: 48.4 / 51.4 %.
  - Per year: 2024 49.6 %, 2025 42.4 % [34.9, 49.9], 2026 51.5 %; 2020 54.8 %, 2021 45.7 %, 2022 52.3 %, 2023 44.7 %.
  - These splits fail with 7-day blocks: the 2026 72 h move, the 2020-23 scalp and 3-aligned 24 h moves, and the 72 h hit of the hours where 3+ timeframes agreed outside the table.
- **Each timeframe alone, against the same-hours guess:**
  - The week, which the study reported at 52-53 % against 50 %, is only +1.3 [-1.9, +4.1] (IS) and +1.7 [-0.8, +3.9] (OOS) points above the guess at 24 h. That is not distinguishable from no skill.
  - The 1H is contrarian over 4 hours in both periods: 3.5 (IS) and 4.1 (OOS) points below the guess. This holds with 28-day blocks.
  - When the 1H reads bearish, price is up 4 hours later 55.4 / 55.2 % of the time.

**Stability:**
- Spells that start as scalp last a median 4 hours. Spells that start as full last 9.5 (IS) and 18.5 (OOS) hours.
- An hour picked at random inside a tradable decision belongs to a spell with a median of 96 / 49 hours.
- After a spell ends, the next one starts a median 19 / 15 hours later.

**Data sensitivity:**
- **Noise of ±10 USD:** see Table 6. The full decision record, including mode and combination, changes in 2.15 / 4.31 % of hours. Readings changed:
  - 1H 4.7 / 10.3 %; 4H 1.6 / 4.8 %; 1D 0.8 / 1.3 %.
  - 1W 0 / 0.1 %; 1M 0.
  - Hit rates under noise move by less than one point.
  - The effect on ledger trades was not computed.
- **Anchoring: UTC-midnight candles instead of New York 17:00.**
  - 2024-26: the trade state changes in 14.0 % of hours (2024 16.6 %, 2025 11.9 %, 2026 13.2 %), and 30.5 % of the New York tradable hours are lost or flipped (0.15 % flipped).
  - The weekly reading differs in 26.0 % of hours, the daily in 26.5 % and the 4H in 31.6 %.
  - 2020-23, anchoring alone: the trade state changes in 7.5 % of hours.
- **Anchoring at the trade level.**
  - In 2024-26 the same rules on UTC candles made 89 trades, 58 % won, +61.7R, against 95 trades, 51 %, +22.8R on New York candles. The UTC run's 1-minute file explains about 2 trades and -2R of that.
  - The 2020-23 comparison (-41.6R against -3.8R) is left out. The two runs also differ in history length, and about 23R of the 37.8R gap falls in 2020-21, where the monthly differs for that reason.
- **The week start.** The research week opens Saturday 17:00 New York; the other MT5 convention is Sunday 17:00. FTMO's choice is not verified.
  - The weekly reading differs in 17.8 / 19.4 % of hours.
  - The trade state differs in only 0.45 / 0.39 %, with no flips.
- **DST.**
  - On the two daylight-saving fall-back days a year, the files' daily and weekly candles hold one more hour than the engine assumes. That is a one-hour look-ahead at 4 hours in 2024-26 and 8 in 2020-23; it never changed the trade state.
  - On those nights the 4H file is missing a candle (6 candles in all).

**Trades by bias.** Each cell: trades, won, mean net R, total net R. The 1D agreed with every trade, because every valid combination contains it.

| Group | 2024-26 | 2020-23 |
|---|---|---|
| All | 95, 50.5 %, +0.240 [-0.10, +0.65], +22.8 | 59, 44.1 %, -0.065 [-0.37, +0.25], -3.8 |
| Long | 68, 50.0 %, +0.111, +7.6 | 27, 40.7 %, -0.166, -4.5 |
| Short | 27, 51.9 %, +0.565, +15.3 | 32, 46.9 %, +0.020, +0.7 |
| Combination M+W+D | 36, 44.4 %, +0.048 [-0.39, +0.49], +1.7 | 11, 36.4 %, -0.054, -0.6 |
| Combination M+D+1H | 14, 64.3 %, +1.144 [-0.16, +3.10], +16.0 | 7, 57.1 %, +0.120, +0.8 |
| Combination M+D+4H | 9, 44.4 %, +0.019, +0.2 | 3, 66.7 %, +0.681, +2.0 |
| Scalp D+4H+1H | 36, 52.8 %, +0.136 [-0.31, +0.65], +4.9 | 38, 42.1 %, -0.161 [-0.54, +0.23], -6.1 |
| 3 aligned | 61, 54.1 %, +0.402 [-0.07, +0.94], +24.5 | 25, 52.0 %, +0.102, +2.5 |
| 4 aligned | 26, 50.0 %, +0.100, +2.6 | 33, 39.4 %, -0.190 [-0.58, +0.22], -6.3 |
| 5 aligned | 8, 25.0 %, -0.538, -4.3 | 1, 0 %, -0.100, -0.1 |
| 4H agrees (1D always agrees) | 66, 47.0 %, +0.071 [-0.26, +0.43], +4.7 | 51, 43.1 %, -0.098 [-0.42, +0.23], -5.0 |
| 4H at 50/50 | 26, 61.5 %, +0.762 [-0.04, +1.85], +19.8 | 5, 40.0 %, +0.111, +0.6 |
| 4H against | 3, 33.3 %, -0.559, -1.7 | 3, 66.7 %, +0.203, +0.6 |

By aligned set (2024-26 | 2020-23):
- D+4H+1H: 29, 51.7 %, +0.186, +5.4 | 21, 47.6 %, -0.017, -0.4
- M+D+1H: 13, 69.2 %, +1.316, +17.1 | 1, 100 %, +0.851, +0.9
- M+D+4H: 9, 44.4 %, +0.019, +0.2 | 3, 66.7 %, +0.681, +2.0
- M+D+4H+1H: 1, 0 %, -1.100, -1.1 | 6, 50.0 %, -0.002, 0.0
- M+W+D: 10, 50.0 %, +0.186, +1.9 | none
- M+W+D+1H: 6, 50.0 %, -0.137, -0.8 | 7, 42.9 %, +0.045, +0.3
- M+W+D+4H: 12, 50.0 %, +0.417, +5.0 | 3, 33.3 %, -0.268, -0.8
- M+W+D+4H+1H: 8, 25.0 %, -0.538, -4.3 | 1, 0 %, -0.100, -0.1
- W+D+4H+1H: 7, 57.1 %, -0.070, -0.5 | 17, 35.3 %, -0.339, -5.8

- **Where the 2024-26 total came from.** The +22.8R comes mostly from a few groups: M+D+1H (+16.0R on 14 trades), the 4H at 50/50 (+19.8R on 26), and 2026 (+15.2R on 17 trades). None of their intervals excludes zero.
- **The first hours of a decision.** The 42 trades taken in the first 3 hours of a decision lost 4.8R. The interval of their mean, [-0.46, +0.24], includes zero.
- **Monthly starved.** In 2020-23, the 34 trades with the monthly at 50/50 made -7.2R.

**Settled results, with their numbers.** These were measured on UTC candles.
- **M+W+1H as a match:**
  - 2024-26: 48 added trades, 35 % won, -13.2R (the run -17.5R against base).
  - 2020-23: 44 added trades, 43 %, -7.3R (the run -6.7R).
- **M+W alone:** 60 added trades, 40 %, -7.8R (2024-26); 62 added, 39 %, -15.2R (2020-23).
- **Reversal trades against the bias** (February 2024 to September 2026). Recount after costs:
  - A: -12.0R (README: 64 trades, 42 %).
  - B: 8 trades, +1.5R.
  - C: -16.5R (README: 140 trades).
  - D: -30.1R (README: 97 trades).
  - No OOS reversal run exists.

**What the check corrected.**
- **The no-skill guess used all hours.** On the same hours:
  - the 2024-26 shortfall is smaller (-2.4 instead of -3.4 points at 24 h);
  - the 2020-23 move edges are larger (+0.123 and +0.231 daily ATR).
- **"Only the week shows an edge" was measured against 50 %.** Against the guess, it is no edge.
- **The 2020-23 numbers come from a starved monthly** (above).
- **Several splits fail with 7-day blocks.**
- **"Readings right after a big move" as a failure mode is not supported.** The 4 h intervals reach 51-52 %, and after a big 24 h run the 72 h move continued.
- **The UTC/New York trade comparison is confounded for 2020-23.**
- **The DST look-ahead is negligible.**
- **Small slips:**
  - the 1H changes 117-126 times a month, not 118-126;
  - the monthly history in 2020-21 is 5-24 candles;
  - the same-side share is 89.1 % over the neutral ends.

**Verdict for BTC.**
- **2024-26:** the bias tells next to nothing about direction (47.9 % over 24 hours against 50.2 % for a same-mix guess).
- **2020-23:** it tells a little about move size (+0.12 daily ATR over 24 hours, from long calls catching rallies). In that period its monthly view was starved of history.
- **The 1H reading on its own runs slightly against the next 4 hours,** in both periods.
- **The biggest risk is the candle grid.** UTC instead of New York daily candles changes 14 % of trade states and the whole strategy's result.
- **Treat it as a slow backdrop with a noisy 1H switch, not as a forecast.**

---

## What this means for the live bot

1. **Trust the readings.** The live code reads the bias exactly as the backtests did. If a live reading ever differs from the research, look at the data, not the code.
2. **Use the bias as a gate, not as confidence in a trade.**
   - A tradable hour means "the bot may look for an entry on this side now". It does not mean "price will go this way".
   - At those hours price went the bias's way about as often as a guess with the same long/short mix.
   - Do not give a trade more stake or more trust because more timeframes agree, or because the 4H and 1D both agree. Nothing measured supports that.
3. **The trade results do not come from the bias calling direction.**
   - In 2024-26, the tuning period, all four ledgers made money: gold +71.8R, EURUSD +39.5R, NAS100 +32.9R, BTC +22.8R.
   - In 2017-23 (BTC 2020-23): gold -62.2R, EURUSD -1.2R, NAS100 +28.8R, BTC -3.8R.
   - Whatever edge the trades have, nothing here credits it to the bias knowing the direction.
4. **Expect the permission to blink.**
   - A tradable decision usually lasts 4-6 hours and ends because the 1H went 50/50.
   - It almost never flips to the other side, and usually comes back on the same side within a day.
   - A missed entry for that reason is normal, not a sign the bias turned. The side itself, set by the day, week and month, holds for days to weeks.
5. **Keep the settled rules.**
   - Reversal trades against the bias lost in all four markets after costs. Only the small variant B made money, in EURUSD (11 trades) and BTC (8 trades).
   - M+W+1H as a match lost in 2017-23 in all four. In 2024-26 it lost in EURUSD and BTC and added a little in gold (+1.6R for the run) and NAS100 (+11.4R).
6. **Check the data, because that is where the bias can really go wrong.**
   - **The candle cut.** The 4H, day, week and month must be cut at 17:00 New York, as in the research. A one-hour slip changes a third of the 4H readings and 7-10 % of gold's decisions. This is the largest data effect measured.
   - **BTC.**
     - The daily must be New York 17:00, not UTC; UTC changes 14 % of trade states.
     - FTMO's week start (Saturday or Sunday 17:00 New York) is not verified, but it moves the trade state in only 0.4 % of hours.
   - **History depth.**
     - The monthly needs 60 closed candles and the weekly 104. The live window asks for 72 and 120.
     - Whether FTMO's server delivers that much was not checked.
     - Without it, the monthly reads 50/50 and the full combinations cannot trade, as in BTC's 2020-21 research data.
   - **A different feed** moves 3-4 % of hours; spread-sized noise 1-2 %. Neither turned a long into a short.
   - **A simple live check.** Compare the bot's readings with the research readings on the same hours. More than a few percent apart points to a grid or history problem.

## What was not computed

- **FTMO's own candles** were not available. The second-feed comparisons use OANDA, for gold and NAS100 only. EURUSD and BTC were not compared with a second feed.
- **A misread server offset** was not measured for EURUSD; its research candles already sit on FTMO's cut. For NAS100 the offset probe was 0 %. Gold's grid probe gives the scale.
- **Whether FTMO's server holds enough history** for the 60-month and 104-week lookbacks.
- **The effect of noise on BTC's ledger trades.**
- **For gold's entry-window split,** the same-hours reference.
- **Any 2017-23 reversal results.** No out-of-sample reversal ledger exists for any market.

## Where the numbers are

- Gold: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/bias/XAUUSD/`. Outputs are in `out/`; the check is in `check/` and `check/out/`.
- EURUSD: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/bias/EURUSD/`. Outputs are the `*.out` files; the check is in `check/`.
- NAS100: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/bias/NAS100/`. Outputs are in `out/`; the check is in `check/` and `check/out/`.
- BTCUSD: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/bias/BTCUSD/`. Outputs are in `out/`; the check is in `check/` and `check/out/`.
- The one comparison computed for this note: `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/bias/synthesis/gold_mean_same.py` and `gold_mean_same.json`. It is gold's mean move against the same-hours guess, from the gold check's hourly table and its bootstrap.
