# NAS100: what the ledger, the candles and the market's own structure say (14 October 2026)

Scope: the live profile `config/dorus_live_nas100.yaml` as research ledgers (1 %, guard off, limit 25 % back for 4 h, BE at 4R,
48 h hold, R:R floor 0.8, 12-point minimum stop): `aca/rr08_NAS100.csv` (2024-01 to 2026-09, 43 trades, 47 %, +37.2R raw) and
`aca/oos_rr08_NAS100.csv` (2017-2023, 100 trades, 32 %, +38.8R raw). Candles `fixed/NAS100_{5min,15min,1H,1D}.csv` (UTC, bid).
Every R below is after the research cost of 0.10R a trade (IS +32.9R, OOS +28.8R); win = raw r > 0.05. Read-only; no backtest run.

Tooling (scratchpad/research/): `nas100_anatomy.py` (cuts, MFE/MAE, exit variants), `nas_lib.py` (the 5m walk and a limit-order
simulator), `nas100_limit.py`, `nas100_variants.py`, `nas100_dayclose.py`; outputs `nas100_*_out.md`, trades with every feature in
`nas100_anatomy_trades.csv`. The 5m walk replays the ledger's own rules (the fill candle counts only the stop; stop before target in
a candle; a short reads the ask = bid + 1.5; BE at 4R, a candle that reaches 4R and trades back through the entry closes at 0; the
48 h close at the close of the first candle labelled 48 h or more after the fill) and reproduces **every trade of both ledgers to
0.00R**, so the exit and limit variants below are measured on the same path the backtest saw.

Ledger conventions found on the way (useful for anyone reading these CSVs): `entry_planned` is the confirmation candle's close
(bid); the limit rests 25 % of the way from the ask (long: close + 1.5) or the bid (short: close) toward the stop, so against the
planned close a long fills about 19-21 % back and a short 25 %; `opened_at` is the fill candle's close time (label + 5 min) and
`closed_at` the exit candle's label.

## 0. What holds in both periods (the short answer)

| finding | 2024-2026 | 2017-2023 |
|---|---|---|
| The D+4H+1H scalps taken while the month reads 50/50: 1 of 11 won | 3 trades, 0 %, -3.3R | 8 trades, 12 %, -6.1R |
| Break-even at +3R instead of +4R | +1.0R (1 trade changes) | +2.0R (2 trades change) |
| A trailing stop behind the last 15m swing after +1R: fewer R, more winners, shallower dips | -1.9R, win 47 -> 49 %, dd -5.8 -> -4.7R | -1.9R, win 32 -> 39 %, dd -11.8 -> -9.3R, longest run 9 -> 6 |
| Confirmation close deeper than an eighth of the zone: dead trades | 9 trades, 22 %, -0.5R | 14 trades, 29 %, -0.9R |
| Daily 20-day efficiency ratio at or above 0.5 (closed candles) | 7 trades, 29 %, -1.6R | 10 trades, 20 %, -6.7R |
| The 13:00-15:30 (pre-market) signals are the biggest and best block; the overnight holds (8-48 h) carry 2017-2023 | 22 trades, +13.4R; holds 8-48 h +0.2R | 43 trades, +33.0R; holds 8-48 h +44.0R on 12 trades |
| The limit (25 % / 4 h) sits on its plateau: 15 % worse in both, 35 % and 2 h mixed, 50 % mixed | 25 %: +32.9R; 35 %: +31.7R; 15 %: +23.5R | 25 %: +28.7R; 35 %: +31.6R; 15 %: +12.6R |
| BE at 1R / 1.5R / 2R, a 24 h or 72 h hold, a day close (plain or losers only), BE before the cash open, a stop of at least half the zone: all worse in one or both periods | | |

Everything else cut by the ledger (hour, weekday, month, combination, direction, trend, gaps, cash-open distance, news, expiry
Fridays, stop size) turns between the periods or is too thin to act on. The tables follow.

## 1. Loss anatomy (both periods; n, win %, R a trade after costs, sum)

### Hour of the fill (Amsterdam)
| cut | IS | OOS |
|---|---|---|
| 09 | 3, 33 %, +0.96R (+2.9) | 9, 22 %, -0.46R (-4.2) |
| 10 | 8, 50 %, +0.53R (+4.3) | 12, 25 %, -0.36R (-4.3) |
| 11-13 (fills of 09-11 signals) | 5, 60 %, +1.44R (+7.2) | 10, 30 %, -0.02R (-0.2) |
| 13 | 7, 71 %, +2.39R (+16.8) | 15, 40 %, +1.42R (+21.3) |
| 14 | 9, 33 %, +0.35R (+3.2) | 13, 15 %, -0.27R (-3.6) |
| 15:00-15:30 | 2, 0 %, -1.10R (-2.2) | 7, 29 %, +0.51R (+3.6) |
| 15:30-16 | 7, 43 %, -0.07R (-0.5) | 12, 50 %, +0.91R (+10.9) |
| 16 | 1, 0 %, -1.10R (-1.1) | 15, 33 %, +0.25R (+3.8) |
| 17-18 (late fills of 13-17 signals) | - | 5, 60 %, +0.82R (+4.1) |
| >18 | 1, 100 %, +2.40R (+2.4) | 1, 0 %, -1.49R (-1.5) |

### Hour of the signal (confirmation close, Amsterdam; the session gate applies here)
| cut | IS | OOS |
|---|---|---|
| 09 | 9, 44 %, +0.89R (+8.0) | 17, 18 %, -0.59R (-10.1) |
| 10 | 7, 57 %, +0.91R (+6.4) | 17, 29 %, -0.11R (-1.8) |
| 13 | 13, 54 %, +1.53R (+19.8) | 21, 33 %, +0.91R (+19.1) |
| 14 | 5, 20 %, -0.42R (-2.1) | 13, 31 %, -0.02R (-0.2) |
| 15:00-15:30 | 4, 0 %, -1.10R (-4.4) | 9, 44 %, +1.57R (+14.2) |
| 15:30-16 | 4, 75 %, +0.70R (+2.8) | 9, 44 %, +0.80R (+7.2) |
| 16 | 1, 100 %, +2.40R (+2.4) | 14, 36 %, +0.04R (+0.5) |
| **09-11 / 13-15:30 / 15:30-17** | 16, 50 %, +14.3R / 22, 36 %, +13.4R / 5, 80 %, +5.2R | 34, 24 %, -12.0R / 43, 35 %, +33.0R / 23, 39 %, +7.7R |

The morning window earns in 2024-2026 and loses before; the 13:00 hour is the best in both; 14:00 is at or under zero in both
(too small to act on). The pre-market block is the engine of 2017-2023.

### Weekday (0 = Monday) and month
| cut | IS | OOS |
|---|---|---|
| Mon | 2, 0 %, -2.2 | 17, 47 %, +22.2 |
| Tue | 7, 43 %, +2.7 | 17, 35 %, +1.3 |
| Wed | 12, 42 %, +12.1 | 29, 28 %, -5.2 |
| Thu | 9, 33 %, +1.7 | 21, 33 %, +19.9 |
| Fri | 13, 69 %, +18.6 | 16, 19 %, -9.4 |
| Months: Feb | 5, 60 %, +4.3 | 10, 0 %, -11.0 |
| Aug | 2, 0 %, -2.2 | 3, 0 %, -3.7 |
| Jan / Mar / Apr | +11.6 / +9.2 / +3.1 | +1.6 / +2.2 / +12.2 |
| Nov / Dec | -2.2 / -1.1 | +12.0 / +2.7 |

Every weekday and month turns between the periods (Friday +18.6R then -9.4R). Nothing to cut.

### Bias
| cut | IS | OOS |
|---|---|---|
| 1M+1W+1D | 27, 48 %, +0.64R (+17.3) | 56, 29 %, +0.34R (+18.9) |
| 1M+1D+1H | 6, 50 %, +1.83R (+11.0) | 23, 35 %, +0.20R (+4.7) |
| 1D+4H+1H (scalp) | 10, 40 %, +0.46R (+4.6) | 21, 38 %, +0.25R (+5.2) |
| 3 / 4 / 5 timeframes aligned | 8, 25 %, +2.4 / 23, 48 %, +19.7 / 12, 58 %, +10.8 | 28, 29 %, -1.2 / 47, 36 %, +34.2 / 25, 28 %, -4.2 |
| 4H among the aligned: no / yes | 17, 41 %, +13.0 / 26, 50 %, +19.9 | 44, 27 %, +20.0 / 56, 36 %, +8.8 |
| **Month at 50/50: no / yes** | 40, 50 %, +36.2 / **3, 0 %, -3.3** | 92, 34 %, +34.9 / **8, 12 %, -6.1** |

All three combinations earn in both periods. The month-at-50/50 trades (all D+4H+1H scalps, all but one a long in 2019-2020 and
2025) lost 10 of 11; the profile halves their stake since 8 October, on NAS100 the data says zero.

### Zone, confirmation, visit, direction
| cut | IS | OOS |
|---|---|---|
| 1H zone (5m shift) | 38, 47 %, +0.72R (+27.2) | 93, 30 %, +0.23R (+21.4) |
| 4H zone (15m shift) | 5, 40 %, +1.15R (+5.7) | 7, 57 %, +1.05R (+7.4) |
| Confirmation | all BS (balance shift); the timeframe follows the zone | |
| Visit | all first visits (one_trade_per_visit, no retest) | |
| LONG | 36, 44 %, +0.69R (+25.0) | 74, 31 %, +0.30R (+22.1) |
| SHORT | 7, 57 %, +1.13R (+7.9) | 26, 35 %, +0.26R (+6.7) |

Shorts on the index that trends up are fine in both periods (the weekly veto keeps them to downtrends).

### Planned R:R and R:R at the fill
| planned R:R | IS | OOS |
|---|---|---|
| 0.8-1 | 5, 40 %, -0.10R (-0.5) | 9, 44 %, +0.05R (+0.5) |
| 1-1.5 | 12, 42 %, +0.03R (+0.4) | 28, 36 %, -0.14R (-3.8) |
| 1.5-2 | 8, 62 %, +1.11R (+8.8) | 19, 26 %, -0.18R (-3.4) |
| 2-3 | 8, 50 %, +1.14R (+9.1) | 15, 33 %, +0.15R (+2.2) |
| 3-5 | 6, 50 %, +1.78R (+10.7) | 18, 28 %, +0.60R (+10.7) |
| >5 | 4, 25 %, +1.08R (+4.3) | 11, 27 %, +2.06R (+22.6) |
| at the fill >5 | 8, 25 %, +0.76R (+6.1) | 24, 33 %, +1.63R (+39.2) |

The R comes from the far targets in both periods (R:R >= 3: IS +15.0R of +32.9R on 10 trades, OOS +33.3R of +28.8R on 29);
the 0.8-2 band earns +8.7R in-sample and loses 6.7R before. Already known (README: R:R >= 2 "points the same way"); the floor
of 0.8 was chosen on 13 October for the recent years and holds out of sample by +8.8R, so nothing new here.

### Stop size
| cut | IS | OOS |
|---|---|---|
| 12-15 points (the minimum) | 6, 33 %, +0.00R | 48, 27 %, +0.12R (+6.0) |
| 15-20 | 4, 25 %, -0.25R (-1.0) | 14, 29 %, +0.55R (+7.7) |
| 20-30 | 14, 50 %, +1.29R (+18.1) | 16, 44 %, +0.53R (+8.5) |
| 30-50 | 12, 50 %, +0.76R (+9.1) | 7, 43 %, +1.26R (+8.8) |
| 50-80 | 3, 67 %, +0.88R (+2.7) | 10, 30 %, -0.22R (-2.2) |
| >80 | 4, 50 %, +1.02R (+4.1) | 5, 40 %, -0.01R (-0.1) |
| stop < 0.10 % of price | 15, 33 %, -0.02R (-0.4) | 16, 19 %, +0.61R (+9.8) |
| stop / 1H ATR14 <0.5 / 0.5-0.75 / 0.75-1 / 1-1.5 / >1.5 | +12.3 (46 %) / +21.4 (60 %) / -5.8 (12 %) / +6.0 / -1.0 | +2.4 (15 %) / +8.0 (42 %) / -1.2 (22 %) / +4.9 / +14.8 (58 %) |
| stop / daily ATR14 <0.10 | 29, 45 %, +0.88R (+25.5) | 43, 28 %, +0.43R (+18.7) |

Half of the 2017-2023 trades sit on the 12-point minimum (prices 5,000-16,000) and still earn. The 0.75-1 ATR(1H) band loses
in both (26 trades, 19 %) with the bands either side fine: noise, not a rule. The prior analysis (`smc_analysis_out.md`) already
showed ATR-minimum stops cost R in both periods; a stop of at least half the zone's height is measured below (worse in both).

### Entry depth in the zone (fraction of its height; negative = the shift closed outside the zone)
| planned entry (what `max_entry_depth` checks) | IS | OOS |
|---|---|---|
| < -0.5 (far outside) | 16, 56 %, +1.10R (+17.6) | 22, 41 %, +0.67R (+14.7) |
| -0.5..-0.25 | 6, 33 %, +0.23R (+1.4) | 12, 25 %, +0.23R (+2.8) |
| -0.25..0 | 10, 50 %, +0.82R (+8.2) | 42, 33 %, +0.11R (+4.7) |
| 0..0.125 | 2, 100 %, +3.07R (+6.1) | 10, 20 %, +0.76R (+7.6) |
| **0.125..0.5 (the cap is 0.5)** | **9, 22 %, -0.05R (-0.5)** | **14, 29 %, -0.07R (-0.9)** |
| fill 0.25-0.5 deep | 7, 14 %, -0.50R (-3.5) | 12, 17 %, -0.40R (-4.7) |

Cap sweep on the planned entry (trades removed / kept): 0.125: IS 9 (-0.5R) / 34 trades 53 % +33.4R, OOS 14 (-0.9R) / 86
trades 33 % +29.7R; 0.25: IS 6 (+2.8R: two 3-4R winners) / 37, OOS 12 (-1.3R) / 88; 0.3: IS 4 (+0.9R), OOS 7 (-3.3R). Only the
eighth removes dead weight in both periods; the gain is in the win rate, not in R.

### Zone height and the stop against the zone
| cut | IS | OOS |
|---|---|---|
| zone height / 1H ATR14 <0.5 | 2, 0 %, -2.2 | 1, 0 %, -1.1 |
| 0.5-1 | 8, 88 %, +23.4 | 12, 33 %, +7.8 |
| 1-1.5 / 1.5-2 | 10, 40 %, +1.5 / 4, 25 %, -1.4 | 22, 27 %, -5.7 / 20, 20 %, -8.9 |
| >2 | 19, 42 %, +11.6 | 45, 40 %, +36.7 |
| stop / zone height 0.25-0.5 | 12, 25 %, -2.9 | 35, 26 %, -2.0 |
| stop inside the near half of the zone | 31, 48 %, +28.0 | 58, 34 %, +24.5 |

Mid-sized zones (1-2 ATR tall) earn nothing in-sample and lose 14.6R before; a mechanism is missing and the in-sample side is
flat, so an observation only. The "stop / zone 0.25-0.5" band (47 trades, 25 % won) contradicts the next row (stops inside the
near half are the best group): noise.

### Trend, regime, gaps, the cash open, expiry, news, timing
| cut | IS | OOS |
|---|---|---|
| with / against the 60-day return | 36, 47 %, +27.5 / 7, 43 %, +5.4 | 82, 30 %, +27.7 / 18, 39 %, +1.1 |
| with / against the 200-day average | 38, 45 %, +26.2 / 5, 60 %, +6.7 | 85, 31 %, +23.9 / 15, 40 %, +4.8 |
| 60-day return >10 % | 15, 60 %, +17.4 | 31, 19 %, -10.8 |
| daily efficiency ratio (20 d, closed candles) <0.20 / 0.20-0.35 / 0.35-0.50 / **>=0.50** | +11.8 (50 %) / +17.9 (67 %) / +4.8 (38 %) / **-1.6 (7, 29 %)** | +34.6 (50 %) / -2.7 (22 %) / +3.5 (25 %) / **-6.7 (10, 20 %)** |
| the day's gap (open vs previous close) within 0.1 daily ATR | 34, 44 %, +24.9 | 90, 33 %, +25.9 |
| gap 0.1-0.3 ATR with the trade / against | 4, 75 %, +4.2 / 5, 40 %, +3.8 | 2, 0 %, -2.2 / 6, 17 %, +0.1 |
| fill 150-30 min before the cash open | 15, 47 %, +17.6 | 28, 29 %, +17.7 |
| fill 0-30 min after the open | 7, 57 %, +2.9 | 12, 50 %, +10.9 |
| fill 30-60 min after the open | 1, 0 %, -1.1 | 8, 25 %, -4.1 |
| fill after the open, entry vs the 09:30 NY open price: -0.5..0 / 0..0.5 / 0.5..1 R | +0.8 (2) / +1.8 (3) / +1.4 (1) | +6.6 (13, 54 %) / +8.9 (5, 60 %) / -4.4 (4, 0 %) |
| options-expiry Friday (third Friday) | 4, 75 %, +9.0 | 3, 0 %, -2.3 |
| nearest high-impact USD event 30-45 min away | 5, 20 %, -0.2 | 1, 0 %, -1.1 |
| next high-impact event within 30-60 min | 4, 25 %, +0.9 | 2, 50 %, +12.9 |
| wait touch -> shift <1 h / 1-3 h / 12-24 h | +20.5 (56 %) / -1.9 (25 %) / +8.2 | +16.0 (29 %) / +2.7 (25 %) / +6.7 (47 %) |
| zone age at the touch <2 h / 2-6 h | 27, 44 %, +13.8 / 11, 45 %, +13.6 | 63, 22 %, -3.1 / 27, 52 %, +32.4 |
| limit filled within 10 min of the signal / after more than 60 min | 17, 53 %, +16.1 / 6, 50 %, +6.2 | 29, 41 %, +14.5 / 25, 20 %, -11.0 |
| resolved within 30 min of the fill | 16, 25 %, -3.8 | 30, 3 %, -30.3 |
| held 8-24 h / 24-48 h / >48 h (time exit) | 3, 33 %, +0.2 / - / 3, 100 %, +6.9 | 9, 67 %, +28.2 / 3, 100 %, +15.8 / 2, 100 %, +2.2 |

Regime: the README's finding (no regime cut holds on NAS100) stands at the 0.35 split (the >= 0.35 trades make +3.2R in-sample,
+10.2R of it in 2026); only the >= 0.50 band is negative in both periods (17 trades, negative in six of the seven year-cells it
touches, 2017 +1.0R the exception). The daily candle in `regime.py` is read with `searchsorted(t) - 1`, which is the candle still
open at the entry; here only closed daily candles count. Gaps: 124 of 143 fills come on days whose open sits within 0.1 ATR of the
previous close; the few gap days are too thin. The cash open: 45 fills come after 15:30 (10 in-sample), the price distance from the
open shows nothing in both periods (the first version of this cut used the open of the same day for pre-market fills, a
look-ahead; it is dropped). About half of the losers (12 of 23, 29 of 66) are stopped within 30 minutes of the fill: the index's
noise around a 12-30 point stop, not a management problem.

### Trades open at the cash open (filled before 15:30, still open at 15:30)
| | IS | OOS |
|---|---|---|
| open at 15:30 | 5 of 43: 60 %, +9.9R | 27 of 100: 48 %, +1.31R a trade, +35.4R |
| of them stopped in the first hour after the open | 2 (-2.2R) | 11 (-8.5R) |
| median adverse excursion in that hour | -0.79R | -0.64R |
| the trades not open at 15:30 | 38, 45 %, +23.0R | 73, 26 %, -6.6R |

The opening hour stops out 40 % of the pre-market trades it meets, and the survivors pay for them several times over, in both
periods. Protecting them before the open is measured in section 3 (mixed).

## 2. The market's structure (public knowledge) against the ledger

What is documented, with the source read today:

- **Volume and range are U-shaped over the US cash session; the opening half hour is a large share of the day's range.** A
  practitioner write-up puts the 09:30-10:00 ET half hour at about a third of the ES daily range in 8 % of the session's time
  (NexusFi, "Intraday seasonality in futures trading", unverified trader figure). The first and last half hours are also where
  intraday return patterns are strongest in the academic record (Heston, Korajczyk and Sadka, Journal of Finance 2010,
  "Intraday patterns in the cross-section of stock returns": continuation at daily lags, reversal within the hour from liquidity
  imbalances and bid-ask bounce; https://www.kellogg.northwestern.edu/academics-research/research/detail/2010/intraday-patterns-in-the-cross-section-of-stock-returns).
- **Continuation after the opening range into the close.** Gao, Han, Li and Zhou, "Market intraday momentum", Journal of
  Financial Economics 2018: the first half-hour return of the S&P 500 ETF predicts the last half-hour return with the same sign
  (1993-2013), strongest on volatile, high-volume and macro-news days (https://profiles.wustl.edu/en/publications/market-intraday-momentum/;
  https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/). The
  "10:00 ET reversal" of trader lore has no documented statistic; a tastylive study summary names 10:30-11:00 ET (16:30-17:00
  Amsterdam) as the day's weakest point in bull markets (anecdotal).
- **The opening-range breakout as a strategy** (Zarattini and Aziz 2023, SSRN 4416622, QQQ 5-minute range): a 24 % hit rate and
  +0.13R a trade gross; an independent 2015-2026 CFD replication reproduces the gross figure on NQ (+0.131R) and finds it not
  distinguishable from zero net of costs (https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy;
  https://www.mql5.com/en/blogs/post/776235). Breakouts of the opening range are not an edge after costs; our entries are the
  opposite (pullbacks into zones), which is the side the record favours.
- **The overnight drift.** Boyarchenko, Larsen and Whelan ("The overnight drift", NY Fed Staff Report 917, RFS 2023): nearly all
  of the S&P 500 futures premium 1998-2019 was earned 02:00-03:00 ET (08:00-09:00 Amsterdam), about 3.6 % a year, also in NQ;
  the same authors report it near zero since 2021 (Liberty Street Economics, "The disappearing overnight drift", 2026;
  https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/). Index returns accrue overnight, not
  intraday, which is why a day close hurts a long-biased index strategy.
- **Options-expiry Fridays** (third Friday): pinning to large strikes is a vendor observation (SpotGamma) and "real but modest"
  in academic work, diluted since daily expiries exist (LuxAlgo library, "Expiration effects"). Our ledger has 7 such trades
  (+9.0R, then -2.3R): nothing to build on.
- **The 10:00 ET data** (ISM manufacturing on the first business day, ISM services on the third, consumer confidence, new home
  sales) sits in `data/calendar/high_impact.csv` as high-impact USD events at 16:00 Amsterdam; the 30-minute blackout already
  blocks 15:30-16:30 on those days, i.e. the opening hour is closed on ISM days by an existing rule. Payrolls (14:30) block
  14:00-15:00 on their Friday.
- **Hours and the break.** FTMO publishes the index hours in the platform (Market Watch, Specification, "Trade") and names the
  Nasdaq CFD `US100.sim` in its holiday notices (early close 16:14 platform time on Good Friday 2026); the historic XTB schedule
  for `US100.cash` was 00:00-22:15 CET plus a short late session. The HistData feed used here trades 00:00-22:15 Amsterdam
  Monday to Friday with the break 22:15-00:00 (reopen 00:05 in summer), and the week reopens Monday 00:00 UTC. Clock caveat for
  the cash open: 09:30 New York is 15:30 Amsterdam except the two to three weeks a year when only one side has switched to summer
  time (then 14:30); the figures above use New York time, not 15:30.

Against the ledger:

- **Pre-market (13:00-15:30) against after the open (15:30-17:00), by the signal:** IS 22 trades, 36 %, +13.4R against 5, 80 %,
  +5.2R; OOS 43, 35 %, +33.0R against 23, 39 %, +7.7R. Both blocks earn in both periods; pre-market is three to four times the
  R. A window **starting at 15:30** would keep IS 21 trades +19.5R (of +32.9R) and OOS 57 trades -4.3R (of +28.8R): no.
- **Ending at 18:00 instead of 17:00:** none of the rr08 trades was confirmed or touched 17:00-18:00 in 2024-2026 (the gate); the
  wider-session ledgers on the same base (R:R 1.0, `q4_NAS100_cand_s1320`, `_us21_full`, `_s0818`) add exactly two signals in
  that hour over 2024-2026: a 1H long of 12 November 2024 16:50 (-1.0R) and a 1H long of 30 July 2025 17:20 (break-even, 0.0R).
  No wider-session ledger exists for 2017-2023 (`q4_NAS100_oos_s08` only moves the start to 08:00: its 25 trades before 09:00
  won 12 %, -20.5R). 11:00-13:00 (the break Dorus keeps): 14 trades, 21 %, -6.0R (`s917`). 18:00-21:00: 15 trades, -0.7R
  (`s0921`). The windows stand. Fills after 17:00 from 13-17 signals (the limit's 4 h): IS 1 (+2.4R), OOS 6 (+2.6R): fine.
- **The opening range:** fills in the first 30 minutes after the open are good in both periods (+2.9R, +10.9R: the limit catches
  the opening dip); the opening hour's volatility stops 2 of 5 and 11 of 27 pre-market trades still open, but that group is the
  best in both periods (section 1), so neither a pause of the limit over the open nor a start at 15:30 helps.
- **The close and the break:** trades held over the break are OOS's biggest earners (8-48 h: +44.0R on 12 trades); every
  day-close variant costs (section 3). The 48 h hold is the local optimum on both sides (24 h -2.4R / -5.5R, 72 h -1.7R / -1.0R).
- **Expiry Fridays, ISM days, gap days:** too thin to act on, and no sign in either direction.

## 3. Exits

MFE / MAE on the trade's own path (fill to exit):

| | IS | OOS |
|---|---|---|
| losers that reached +0.25R / +0.5R / +1R / +1.5R / +2R before the stop | 48 / 43 / 17 / 9 / 4 % (23 losers) | 62 / 45 / 32 / 14 / 5 % (66 losers) |
| winners' adverse excursion: median; worse than -0.5R; worse than -0.8R | -0.51R; 50 %; 15 % | -0.57R; 56 %; 28 % |
| winners' MFE median | 2.53R | 2.31R |
| winners' hours to +1R (prior analysis) | median 0.6 h | median 0.8 h |

Half the winners go half-way to the stop first, so anything that moves the stop early costs winners; a third of the 2017-2023
losers saw +1R first, but the variants show the winners lost outweigh them.

| variant (sum R after costs; the base is the ledger) | IS | IS win | changed | OOS | OOS win | changed |
|---|---|---|---|---|---|---|
| base (BE at 4R, hold 48 h) | +32.9 | 47 % | 0 | +28.8 | 32 % | 0 |
| no break-even | +32.9 | 47 % | 0 | +26.8 | 32 % | 2 |
| BE at +1R | +17.0 | 30 % | 11 | +16.4 | 23 % | 29 |
| BE at +1.5R | +20.8 | 35 % | 7 | +27.1 | 29 % | 11 |
| BE at +2R | +28.4 | 42 % | 3 | +28.2 | 31 % | 4 |
| BE at +2R, stop to +0.2R | +29.0 | 49 % | 3 | +23.5 | 37 % | 7 |
| **BE at +3R** | **+33.9** | 47 % | 1 | **+30.8** | 32 % | 2 |
| trail the last 15m swing (2/2 fractal, confirmed) after +1R, never back | +31.0 | **49 %** | 6 | +26.9 | **39 %** | 29 |
| trail after +1.5R / +2R | +29.3 / +31.3 | 47 % | 3 / 2 | +21.1 / +20.2 | 35 / 34 % | 16 / 7 |
| hold 24 h | +30.5 | 47 % | 1 | +23.3 | 31 % | 4 |
| hold 72 h | +31.2 | 44 % | 1 | +27.8 | 31 % | 2 |
| no time limit | +31.2 | 44 % | 1 | +25.3 | 30 % | 2 |
| stop to entry at 15:25 (before the cash open) when the trade shows +0.5R / +1R / +1.5R | +31.5 / +30.5 / +32.9 | 44-47 % | 3 / 2 / 0 | +31.3 / +30.8 / +29.8 | 31-32 % | 6 / 2 / 1 |
| day close 22:10, every trade (the README's) | +29.8 | 49 % | 6 | +8.2 | 32 % | 12 |
| day close 22:10 only when under water | +33.9 | 47 % | 1 | +24.6 | 30 % | 3 |
| stop to entry at 22:10 when +1R or more | +32.9 | 47 % | 0 | +28.8 | 32 % | 0 |
| stop at least half the zone's height (`min_stop_zone_fraction 0.5`, same fill, target kept) | +31.5 on 37 trades (6 refused under R:R 0.8) | 51 % | 23 widened | +17.9 on 93 | 38 % | 56 widened |

By year (base / BE2 / trail after +1R / hold 24 / hold 72): 2017 -2.3 / -2.3 / 0.0 / -2.3 / -4.1; 2018 +1.5 / +2.5 / +0.4 /
+1.5 / +1.5; 2019 +9.2 / +9.2 / +7.3 / +5.7 / +10.0; 2020 -9.8 / -12.4 / -3.8 / -9.8 / -9.8; 2021 +13.2 / +14.2 / +9.8 / +13.2
/ +13.2; 2022 +0.3 / +0.3 / +1.9 / +0.3 / +0.3; 2023 +16.7 / +16.7 / +11.3 / +14.8 / +16.7; 2024 +3.3 / +3.3 / +2.1 / +3.3 /
+1.7; 2025 +4.8 / +4.8 / +7.7 / +4.8 / +4.8; 2026 +24.7 / +20.2 / +21.1 / +22.4 / +24.7.

Drawdown (R after costs, trades in order) and the longest losing run:

| variant | IS sum / dd / run | OOS sum / dd / run |
|---|---|---|
| base | +32.9 / -5.8 / 4 | +28.8 / -11.8 / 9 |
| trail 15m swing after +1R | +31.0 / -4.7 / 4 | +26.9 / -9.3 / 6 |
| BE at +3R | +33.9 / -5.8 / 4 | +30.8 / -10.8 / 9 |
| month-50/50 scalps skipped | +36.2 / -5.8 / 4 | +34.9 / -9.0 / 6 |

Reading: the profile's exits are at their local optimum. The only both-period gain is 4R -> 3R (three trades, +1.0R / +2.0R).
The 15m-swing trail is the one variant that raises the win rate and cuts the drawdown and the losing run in both periods, for
about 0.7R a year less: a challenge trade-off rather than an edge. Of the three trades the 48 h rule closed (IS P8 +0.68R, OOS
P1 +0.80R, P21 +1.64R), two would have been stopped at -1R with 72 h or no limit; P21 would have made +2.4R with 72 h and 0 with
none. Net: 72 h -1.7R / -1.0R, no limit -1.7R / -3.5R.

## 4. The limit entry

`entry_planned` is the confirmation close; the fill lies 25 % from the ask/bid toward the stop (19-21 % of the planned-to-stop
distance for longs because of the 1.5-point spread, 25 % for shorts). Fill delay: in-sample median 10 min (17 of 43 in the next
candle, 6 after more than an hour), out-of-sample median 18 min (29 at once, 25 after an hour, and those 25 won 20 % for -11.0R
while the in-sample late fills won 50 % for +6.2R). In the real runs 8 of 51 limits went unfilled in 2024-2026 (2 target first,
6 expired) and 22 of 122 in 2017-2023 (14 target first, 8 expired).

Simulated with the same walk (fills from the candle after the confirmation, missed when the target trades first, expired when a
candle closes at or after the validity; BE 4R, 48 h hold; the 25 %/240 column reproduces both ledgers to 0.1R):

| fraction / validity | IS market universe: 46 setups at R:R >= 1.0 (`aca/market_NAS100.csv`): fills, win, sum R, R per placed | IS filled trades (43): fills, win, sum R | OOS filled trades (100): fills, win, sum R |
|---|---|---|---|
| market (0 %) | 46, 52 %, +21.2R, +0.46 | 43, 47 %, +12.9R | 100, 32 %, -6.5R |
| 15 % / 120 | 38, 47 %, +22.5R, +0.49 | 41, 46 %, +21.2R | 94, 34 %, +19.6R |
| 15 % / 240 | 42, 48 %, +25.9R, +0.56 | 43, 47 %, +23.5R | 100, 32 %, +12.6R |
| 25 % / 120 | 37, 46 %, +29.5R, +0.64 | 41, 46 %, +30.1R | 90, 33 %, +34.9R |
| **25 % / 240 (the profile)** | **39, 46 %, +32.3R, +0.70** | **43, 47 %, +32.9R** | **100, 32 %, +28.7R** |
| 25 % / 480 | 40, 45 %, +31.2R, +0.68 | 43, +32.9R | 100, +28.7R (+ the 8 expired: unknown) |
| 35 % / 120 | 32, 38 %, +23.0R, +0.50 | 36, 39 %, +24.4R | 80, 34 %, +37.7R |
| 35 % / 240 | 35, 40 %, +30.4R, +0.66 | 39, 41 %, +31.7R | 91, 32 %, +31.6R |
| 35 % / 480 | 36, 39 %, +29.3R, +0.64 | 39, +31.7R | 95, 31 %, +27.2R |
| 50 % / 240 | 32, 34 %, +29.0R, +0.63 | 35, 34 %, +29.4R | 81, 27 %, +44.7R |

Where the 25 % limit's edge comes from (IS universe): the 39 setups it fills made +13.5R at the market and +32.3R with the
limit (the same trades, a better price and a smaller stop); the 6 it misses (expired) made +6.7R at the market (83 % won) and
the 1 whose target traded first +1.0R. A shallower limit (15 %) fills three more and earns less in both periods (the price
improvement is what pays). A deeper limit (35 %) is -1.2R in-sample on 4 fewer fills (universe -1.9R) and +2.9R out of sample:
mixed, with a lower win rate in both (41 % / 32 %). Two hours of validity: -2.8R / +6.2R, mixed. Eight hours: -1.1R in the
universe, unknown out of sample. 50 %: -3.5R in-sample (the README's 50 % run agreed), +16R out of sample on 19 fewer trades
and a 27 % win rate. The deeper fractions' out-of-sample columns are complete (a deeper limit fills a subset of the 25 % fills);
the shallower ones miss the 22 out-of-sample setups the 25 % limit never filled. The profile's 25 % / 4 h is the plateau's best
point in both periods.

## 5. Candidates (exact rule, knob or code, expected effect, pre-screen in both periods)

| # | rule | knob / code | IS (2024-2026) | OOS (2017-2023) | code |
|---|---|---|---|---|---|
| 1 | **No NAS100 trade while the monthly bias reads 50/50.** Every such trade is a D+4H+1H scalp (the full combinations need the month); 1 of 11 won. The profile halves their stake; the data says none. | `risk.neutral_bias_risk_multiplier: {1M: 0.0}` in `config/dorus_live_nas100.yaml`. A zero multiplier sizes 0 lots, which the backtest refuses ("stop too wide for the minimum lot") and the live runner does not execute; a two-line message in `setup_risk`/the runner ("skipped: the month reads 50/50") is cosmetic. | 3 trades out (0 %, -3.3R): 40 trades, 50 %, +36.2R (+3.3R) | 8 out (12 %, -6.1R): 92 trades, 34 %, +34.9R (+6.1R), drawdown -11.8 -> -9.0R, longest run 9 -> 6 | no |
| 2 | **Break-even after +3R instead of +4R** on NAS100. | `exits.breakeven_r_intraday: 3.0` | +1.0R (1 trade; 47 %) | +2.0R (2 trades; dd -11.8 -> -10.8R) | no |
| 3 | **Trail the stop behind the last confirmed 15m swing once the trade has been +1R** (2-left/2-right fractal, usable two 15m candles after it forms, never moved back; BE at 4R stays). Fewer R, more winners, shallower dips: a challenge variant, not an edge. | new `exits.trail_after_r: 1.0`, `exits.trail_swing_tf: 15m` in `ExitParams`; the trailing in `PaperBroker.on_candle` and `live.py`'s position management (the 15m structure is already computed) | -1.9R (+31.0R), win 47 -> 49 %, dd -5.8 -> -4.7R | -1.9R (+26.9R), win 32 -> 39 %, dd -11.8 -> -9.3R, run 9 -> 6 | yes |
| 4 | **The confirmation close at most an eighth of the zone deep** (now half). | `risk.max_entry_depth: 0.125` | 9 trades out (22 %, -0.5R): 34 trades, 53 %, +33.4R, dd -3.3R, run 3 | 14 out (29 %, -0.9R): 86 trades, 33 %, +29.7R | no |
| 5 | **No entry while the daily 20-day efficiency ratio (closed candles) is 0.5 or more.** Thin (17 trades) but negative in six of seven year-cells; the 0.35 split does not hold. | new `confirmation.max_daily_efficiency: 0.5`, computed like `min_volatility_percentile` from the daily candles the engine already holds | 7 out (29 %, -1.6R): 36 trades, 50 %, +34.5R | 10 out (20 %, -6.7R): 90 trades, 33 %, +35.4R | yes |

Stacked (the knob-only ones first; R after costs, trades in order):

| set | IS | OOS |
|---|---|---|
| the profile | 43 trades, 47 %, +32.9R, +0.77R a trade, dd -5.8R, run 4 | 100, 32 %, +28.8R, +0.29R, dd -11.8R, run 9 |
| 1 + 2 | 40, 50 %, +37.2R, +0.93R, dd -5.8R, run 4 | 92, 34 %, +35.9R, +0.39R, dd -9.0R, run 6 |
| 1 + 2 + 4 | 31, 58 %, +36.7R, +1.18R, dd -3.3R, run 3 | 79, 34 %, +35.8R, +0.45R, dd -10.7R, run 8 |
| 1 + 2 + 5 | 35, 51 %, +36.6R, +1.05R, dd -7.7R, run 7 | 82, 35 %, +42.6R, +0.52R, dd -9.2R, run 8 |
| 1 + 2 + 4 + 5 | 27, 59 %, +35.0R, +1.30R, dd -4.4R, run 4 | 70, 37 %, +43.8R, +0.63R, dd -10.7R, run 8 |

By year, 1 + 2 + 5 against the profile: 2017 -3.4 (-2.3), 2018 +1.5 (+1.5), 2019 +15.4 (+9.2), 2020 -3.2 (-9.8), 2021 +15.3
(+13.2), 2022 +0.3 (+0.3), 2023 +16.7 (+16.7), 2024 +3.3 (+3.3), 2025 +7.3 (+4.8), 2026 +25.9 (+24.7).

None of these adds trades: the market takes 1.3 a month and every way of adding (wider hours, 11-13, second visits, 15m zones,
breaks of structure, the W+D+1H and M+W+1H combinations, a two-of-five bias) was measured earlier or here and lost out of sample.
What the ledger says instead is that the index's R lives in the far targets (R:R >= 3) and in the trades held over the break,
and that the profile's exits and limit are already on their plateaus; the candidates above are subtractions with a both-period
sign, worth about 5-9R over 2024-2026 and 9-15R over 2017-2023 at one trade a month fewer.

Measured here and not candidates (both periods): limit 15 % (worse), 35 % and 2 h validity (mixed), 50 % (mixed); BE at 1R /
1.5R / 2R (worse), trail after 1.5R / 2R (worse), hold 24 h / 72 h / none (worse); BE before the cash open at 0.5-1.5R (mixed);
the day close plain (worse) and losers-only (mixed, +1.0R / -4.2R); a stop of at least half the zone's height (worse, -1.4R /
-10.9R); a window starting at 15:30 (loses the best block) or ending at 18:00 (two trades, -1.2R, no out-of-sample ledger);
cuts by weekday, month, direction, the 60-day return, the 200-day average, the gap, expiry Fridays and news distance (all turn
between the periods or are too thin).
