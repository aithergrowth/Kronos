# BTCUSD: what the ledgers say, what the market does, and what has not been tested (14 October 2026)

Profile `config/dorus_live_btc.yaml` (no 1H requirement, R:R floor 0.5, previous-high target capped at 3R nearest, 60 USD
minimum stop, half stake). Ledgers: in-sample `aca/base_BTCUSD.csv` (89 trades, January 2024 - September 2026) and
out-of-sample `aca/oos_base_BTCUSD.csv` (130 trades, June 2020 - December 2023), 1 % units, guard off. Every R below is
after the research cost of 0.10R a trade. Candles: Bitstamp 5m/15m/1H/1D (`btc_old`, `btc_data`). Scripts and the full
tables: `research/btc_market.py` -> `research/btc_market_out.md` (every cut, both periods), `research/btc_intraday.py`
-> `research/btc_intraday_out.md` (the market's clock), `research/btc_market_trades.csv` (one row a trade with every
measure). Read-only on the repository; no backtest was run.

The 5m walk used for the exits reproduces both ledgers trade for trade (0 of 219 differ) once it applies the backtest's
$15 ask-side spread (a short's stop and target trigger on bid + 15) and the profile's break-even at +4R.

| | IS 2024-2026 | OOS 2020-2023 |
|---|---|---|
| Trades, won, sum, R a trade | 89, 58 %, +61.7R, +0.69 | 130, 33 %, -41.6R, -0.32 |
| By year | 2024 +10.3, 2025 +11.8, 2026 +39.6 | 2020 -9.2, 2021 -24.1, 2022 -13.0, 2023 +4.7 |
| Without the two June 2026 shorts (P82 +23.9R, P79 +11.8R) | +26.2R (57 % of the sum is two trades) | |
| Deepest dip | -4.9R | -48.7R |
| Losers that never saw +0.25R / that saw +1R first | 30 % / 27 % | 52 % / 10 % |
| Free MFE (stop only, 14 days) median; trades that would reach +3R / +5R | 2.05R; 44 % / 27 % | 0.51R; 22 % / 14 % |

Reading: the 2020-2023 trades did not run. Half the losers never went a quarter R in profit and the median trade would
not have reached +0.5R with no target at all. The in-sample edge is two trades plus a modest +26R over three years.

## 1. Loss anatomy (n, won, R a trade, sum; "weak in both" = R a trade under +0.2 IS and under -0.3 OOS with n >= 5 each)

Confirmation type (all BS) and visit (all 1) are single-valued in both ledgers: nothing to cut. Bins are right-closed.

### Hour of entry (Amsterdam) and the sessions

| Hour | IS | IS excl top2 | OOS | |
|---|---|---|---|---|
| 09 | 27, 67 %, +1.82, +49.3R | +13.8R | 36, 31 %, -0.34, -12.2R | |
| 10 | 15, 60 %, +0.28, +4.1R | +4.1R | 23, 30 %, -0.41, -9.5R | |
| 13 | 13, 38 %, +0.02, +0.2R | +0.2R | 29, 31 %, -0.34, -9.8R | weak in both |
| 14 | 15, 67 %, +0.50, +7.4R | +7.4R | 14, 57 %, +0.38, +5.3R | the only afternoon hour positive in both |
| 15 | 8, 75 %, +0.57, +4.5R | +4.5R | 15, 20 %, -0.75, -11.2R | |
| 16 | 11, 36 %, -0.35, -3.9R | -3.9R | 13, 38 %, -0.33, -4.2R | weak in both |
| Session 09-11 | 42, 64 %, +1.27, +53.4R | +17.9R | 59, 31 %, -0.37, -21.7R | IS by year +10.9 / +3.5 / +39.0; OOS -7.2 / -10.4 / -5.3 / +1.2 |
| Session 13-17 | 47, 53 %, +0.18, +8.3R | +8.3R | 71, 35 %, -0.28, -19.9R | IS -0.6 / +8.3 / +0.6; OOS -2.0 / -13.7 / -7.8 / +3.5 |
| 13:00-15:30 | 31, 58 %, +0.35, +11.0R | +11.0R | 51, 35 %, -0.25, -12.8R | |
| From 15:30 (the US cash open) | 15, 40 %, -0.21, -3.2R | -3.2R | 23, 30 %, -0.50, -11.6R | weak in both; IS by year 2024 -5.1, 2025 +0.4, 2026 +1.4; OOS -1.1 / -5.7 / -5.8 / +1.1 |

The morning carries the in-sample result even without the two outliers (+17.9R against +8.3R), but it loses as much as
the afternoon out of sample. The one block that is weak in both periods is the last ninety minutes. The trades entered
from 15:30 have the widest stops against the hour's range (median 1.15 ATR14(1H) IS, 1.54 OOS, against 0.8 / 1.0 for
the rest), the smallest excursions in their favour (median MFE 1.04R / 0.49R) and are mostly 1M+1W+1D swings entered
in the day's expansion hour.

### Weekday, month, quarter

| Cut | IS | OOS |
|---|---|---|
| Monday / Tuesday / Wednesday / Thursday / Friday | +7.0 (61 %) / +14.9 (50 %) / +6.5 (61 %) / +28.4 (62 %) / +5.0 (56 %) | -6.3 (26 %) / -0.1 (46 %) / -18.2 (19 %) / -11.4 (32 %) / -5.6 (43 %) |
| Months weak in both | August (5, 60 %, -0.3R) and September (11, 45 %, +1.1R) | August (13, 23 %, -6.8R), September (9, 11 %, -7.9R) |
| Quarters | 2026Q2 9 trades +39.2R (+3.8R excl top2); every other quarter between -1.7R and +9.7R | 2021Q4 14 trades, 0 won, -15.4R; 2022Q3 16 trades 19 %, -10.4R; 2023 the only positive year |

No weekday holds (Wednesday loses -18.2R OOS and makes +6.5R IS). August-September are weak in both periods on small
numbers; a seasonal rule is not proposed.

### Bias, zone, target, stop, entry

| Cut | IS | IS excl top2 | OOS | |
|---|---|---|---|---|
| 1M+1W+1D (swing) | 44, 57 %, +0.82, +36.0R | +12.2R | 76, 28 %, -0.43, -32.4R | the OOS loss lives here |
| 1D+4H+1H (scalp) | 24, 54 %, +0.07, +1.7R | +1.7R | 45, 36 %, -0.27, -12.1R | near zero IS, loses OOS |
| 1M+1D+1H | 10, 70 %, +1.77, +17.7R | +6.1R | 7, 71 %, +0.44, +3.1R | positive in both, thin |
| 1M+1D+4H | 11, 64 %, +0.57, +6.3R | +6.3R | 2, 50 %, -0.2R | |
| Zone 1H / 4H | 67, 60 %, +56.4R / 22, 55 %, +5.3R | +21.0R / +5.3R | 100, 31 %, -37.8R / 30, 40 %, -3.8R | |
| Planned R:R 0.5-1 | 23, 83 %, +0.32, +7.3R | +7.3R | 40, 42 %, -0.36, -14.6R | the win-rate carrier IS, a loser OOS |
| 1-2 | 33, 52 %, +0.09, +3.1R | +3.1R | 53, 36 %, -0.24, -12.7R | |
| 2-3 | 28, 46 %, +0.52, +14.6R | +14.6R | 27, 26 %, -0.16, -4.4R | |
| > 3 (far previous high, nothing nearer fits) | 5, 60 %, +7.33, +36.7R | +1.2R | 10, 0 %, -1.00, -10.0R | the two outliers; 0 of 10 paid OOS |
| Stop <= 60 USD (the minimum binds) | none | | 13, 46 %, +0.3R | |
| Stop 0.2-0.35 % of price | 16, 50 %, +0.33, +5.2R | +5.2R | 15, 53 %, +0.27, +4.0R | the only stop band positive in both |
| Stop 0.75-1 % of price | 11, 45 %, -0.24, -2.6R | -2.6R | 18, 28 %, -0.39, -7.1R | weak in both, but the bands either side are positive IS: a U, noise |
| Stop < 0.5 ATR14(1H) | 15, 53 %, +2.02, +30.4R | +6.6R | 25, 40 %, -0.13, -3.2R | |
| Stop 0.5-1 ATR | 41, 66 %, +28.1R | +16.4R | 49, 24 %, -24.5R | |
| Stop > 1.5 ATR | 16, 56 %, +0.23, +3.7R | +3.7R | 29, 34 %, -0.42, -12.3R | |
| Stop > 2 ATR | 9, 56 %, +0.15, +1.4R | +1.4R | 12, 33 %, -0.44, -5.3R | weak in both |
| Entry > 0.5 zone heights outside the zone | 15, 53 %, +0.08, +1.2R | +1.2R | 25, 28 %, -0.53, -13.2R | weak in both |
| Entry just outside (0-0.5 heights) | 52, 54 %, +0.38, +19.6R | +7.9R | 63, 37 %, -0.32, -20.2R | |
| Entry inside, 0-0.25 deep / 0.25-0.5 deep | 12, 58 %, +4.1R / 10, 90 %, +36.8R | +4.1R / +13.0R | 27, 33 %, -2.2R / 15, 27 %, -6.0R | |
| Long / short | 62, 58 %, +24.0R / 27, 59 %, +37.7R | +24.0R / +2.2R | 59, 25 %, -30.6R / 71, 39 %, -11.0R | OOS longs 25 % won through the 2021 bull market |
| Target < 0.25 ATR14(1D) | 45, 69 %, +0.41, +18.3R | +18.3R | 72, 38 %, -0.32, -22.8R | |
| Confirmation body > 2 x ATR14 of its timeframe | 8, 38 %, -0.16, -1.3R | -1.3R | 8, 12 %, -0.90, -7.2R | weak in both (climax candle) |
| Yesterday's opposite extreme already taken today before the entry | 9, 33 %, -0.55, -5.0R | -5.0R | 12, 33 %, -0.23, -2.8R | weak in both, every IS year negative |
| Wait touch -> shift > 24 h (4H zones) | 10, 60 %, +0.13, +1.3R | +1.3R | 10, 40 %, -0.35, -3.5R | weak in both |
| Zone age at touch < 4 h / 4-12 / 12-24 | 44, 68 %, +33.4R / 34, 53 %, +8.4R / 10, 30 %, +19.2R | +21.8 / +8.4 / -4.6R | 82, 34 %, -26.4R / 33, 33 %, -8.4R / 14, 29 %, -5.8R | |

### Regime at entry

| Cut | IS | IS excl top2 | OOS |
|---|---|---|---|
| With / against the 60-day return | 68, 60 %, +45.6R / 21, 52 %, +16.1R | +21.8 / +4.4R | 101, 31 %, -37.4R / 29, 41 %, -4.3R |
| With / against the 20-day return | 76, 59 %, +55.2R / 13, 54 %, +6.5R | +19.8 / +6.5R | 113, 30 %, -44.8R / 17, 53 %, +3.2R |
| Daily efficiency ratio (20 d) < 0.2 / 0.2-0.35 / 0.35-0.5 / > 0.5 | +25.3 (49 %) / +12.0 (62 %) / +23.0 (81 %) / +1.4 (50 %) | +1.5 / +12.0 / +11.3 / +1.4 | -12.3 (37 %) / -7.7 (37 %) / -15.3 (25 %) / -6.3 (29 %) |
| 24 h 1H range / ATR14(1H) < 4 / 4-5 / 5-6.5 / > 6.5 | +6.2 (83 %) / -4.4 (25 %) / +8.9 (65 %) / +51.0 (64 %) | +6.2 / -4.4 / +8.9 / +15.6 | -4.5 (28 %) / -3.1 (44 %) / -20.4 (28 %) / -13.7 (31 %) |
| ATR14(1H) as % of price < 0.6 / 0.6-0.8 / 0.8-1.2 / > 1.2 | +15.8 (58 %) / +36.8 (57 %) / +5.3 (56 %) / +3.7 (71 %) | +15.8 / +1.4 / +5.3 / +3.7 | +1.8 (50 %) / -7.4 (29 %) / -20.1 (30 %) / -15.9 (27 %) |
| Entry in the top quarter of the 5-day range (closed 1H candles) | 57, 58 %, +32.6R | +5.3R | 91, 35 %, -25.4R |
| Timeframes aligned: 3 / 4 / 5 of 5 | 46, 63 %, +40.7R / 30, 60 %, +20.7R / 13, 38 %, +0.3R | +16.9 / +9.0 / +0.3R | 54, 37 %, -13.7R / 63, 32 %, -19.3R / 13, 23 %, -8.7R |
| Timeframes against: 0 / 1 / 2 | 49, 59 %, +27.0R / 31, 55 %, +30.3R / 9, 67 %, +4.4R | +15.3 / +6.5 / +4.4R | 87, 26 %, -44.2R / 31, 45 %, +1.6R / 12, 50 %, +1.0R |

No regime cut holds: the in-sample winners sit in choppy (ER < 0.2) and expanded (24 h range > 6.5 ATR) days, the
out-of-sample losers everywhere. The out-of-sample years were much more volatile (80 of 130 trades at an hourly ATR
above 0.8 % of price, 23 of 89 in-sample), and those trades lost -36R; in-sample the same bucket made +9R on 23
trades, so a volatility gate cannot be chosen on this evidence. Trades against the 20-day return won 53-54 % in both
periods (13 / 17 trades), with-trend trades 59 % / 30 %: the strategy's out-of-sample edge on with-trend entries is nil.
The one bias cut weak in both periods is "all five timeframes aligned" (38 % / 23 % won): when everything already
agrees the entry is late. Note on the premium/discount cut: the earlier `smc_analysis_out.md` showed the top quarter of
the 5-day range as the loser; that cut used the current day's full daily candle (a look-ahead). On closed 1H candles
the top quarter holds 64-70 % of all trades and is +32.6R in-sample: no cut.

### The 0.25x stake on the weak buckets (R at 1x elsewhere; the bucket at a quarter)

| Bucket | IS: bucket -> total at 0.25x / skipped | OOS: bucket -> total at 0.25x / skipped |
|---|---|---|
| Entries from 15:30 | -3.2R (15) -> +64.1 (+2.4) / +64.9 (+3.2) | -11.6R (23) -> -33.0 (+8.7) / -30.1 (+11.6) |
| The 16:00 hour alone | -3.9R (11) -> +64.6 (+2.9) / +65.6 (+3.9) | -4.2R (13) -> -38.4 (+3.2) / -37.4 (+4.2) |
| The 13:00 hour alone | +0.2R (13) -> +61.5 (-0.2) / +61.5 (-0.2) | -9.8R (29) -> -34.3 (+7.3) / -31.8 (+9.8) |
| All five timeframes aligned | +0.3R (13) -> +61.5 (-0.2) / +61.4 (-0.3) | -8.7R (13) -> -35.1 (+6.5) / -33.0 (+8.7) |
| Yesterday's opposite extreme taken | -5.0R (9) -> +65.4 (+3.7) / +66.7 (+5.0) | -2.8R (12) -> -39.5 (+2.1) / -38.8 (+2.8) |
| Confirmation body > 2 ATR | -1.3R (8) -> +62.7 (+1.0) / +63.0 (+1.3) | -7.2R (8) -> -36.2 (+5.4) / -34.5 (+7.2) |
| Entry > 0.5 zone heights outside | +1.2R (15) -> +60.8 (-0.9) / +60.5 (-1.2) | -13.2R (25) -> -31.7 (+9.9) / -28.5 (+13.2) |
| Scalp 1D+4H+1H | +1.7R (24) -> +60.4 (-1.3) / +60.0 (-1.7) | -12.1R (45) -> -32.6 (+9.1) / -29.5 (+12.1) |
| Stop > 1.5 ATR14(1H) | +3.7R (16) -> +58.9 (-2.8) / +58.0 (-3.7) | -12.3R (29) -> -32.4 (+9.2) / -29.3 (+12.3) |
| 1H against | +29.9R (10) -> +39.3 (-22.4) / +31.8 (-29.9) | -5.3R (14) -> -37.6 (+4.0) / -36.3 (+5.3) |
| Planned R:R under 1 | +7.3R (23) -> +56.2 (-5.5) / +54.4 (-7.3) | -15.5R (39) -> -30.0 (+11.6) / -26.2 (+15.5) |
| Far target kept (planned > 3) | +36.7R (5) -> +34.2 (-27.5) / +25.0 (-36.7) | -10.0R (10) -> -34.1 (+7.5) / -31.6 (+10.0) |

## 2. The market's structure (public knowledge and our candles) and the ledger

- **CME.** Until 29 May 2026 CME bitcoin futures traded Sunday 17:00 to Friday 16:00 Central with a 60-minute break
  at 16:00 CT, which is 00:00 Amsterdam in both seasons (reopen 01:00), and the weekend gap ran Friday 16:00 CT to
  Sunday 17:00 CT; trading-desk commentary puts historical gap fills at 70-95 % (not audited). Since 29 May 2026 CME's
  crypto futures and options trade around the clock with a short weekly maintenance window on Saturday, so no new CME
  gaps form (existing ones stay on the chart). The bot's windows never touch the old close/open hours or the Monday
  reopen; nothing to change. Sources: Yahoo Finance on the first gap-free Monday
  (https://finance.yahoo.com/markets/crypto/articles/bitcoin-first-cme-gap-free-174649486.html), CME's 24/7 launch
  coverage (https://fxnewsgroup.com/forex-news/exchanges/cme-group-launches-24-7-trading-for-cryptocurrency-futures-and-options/,
  https://decrypt.co/342709/cme-group-24-7-trading-options-futures-ahead-xrp-solana-debut), TradingView gap notes
  (https://www.tradingview.com/ideas/cmegaps/).
- **The US cash open, 15:30 Amsterdam.** A Kraken study of 2016-2025 hourly data (87,672 hours) finds the nine hours
  13:00-21:59 UTC carried 50.6 % of bitcoin's daily realized variance in 2022-2025 (38.4 % in 2016-2018) for 37.5 % of
  the day; the most volatile hour moved from 14:00 UTC in US daylight time to 15:00 UTC in standard time, i.e. 16:00
  Amsterdam in both; on US market holidays the US-hours share drops 13.9 points; weekend volume and volatility fell
  (https://cryptoslate.com/crypto-never-closes-but-bitcoin-ethereum-xrp-and-solana-now-move-on-wall-street-time/).
  Our 1H candles agree: in 2024-2026 the 15:00 and 16:00 Amsterdam hours run 1.78x and 1.85x the hourly ATR and hold
  6.7 % and 7.4 % of the day's range (the next hours 1.42x, 1.23x; the morning hours 0.9-1.0x; 05:00-08:00 0.76-0.80x).
  Direction: the 15:30-16:30 move continues slightly over the next three hours (same sign 50-52 % of days, correlation
  +0.11 in both 2020-23 and 2024-26), while the 13:00-14:00 and 14:30-15:30 moves revert (correlation -0.10 / -0.20 in
  2020-23, -0.04 in both windows in 2024-26): the pre-open drift is faded at the open, the open's own move is not. The
  literature: Quantpedia on Gemini 2015-2022 finds no statistically negative hour, the weakest returns at 03:00-04:00
  UTC and the strongest at 22:00-23:00 UTC, and on NYSE-open days an overnight return that dominates while the intraday
  (15:00-21:00 UTC) return is "small and volatile"
  (https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/); Bespoke in May 2022 saw
  bitcoin fall on average once the US market opened, a stress-period anecdote
  (https://www.advisorperspectives.com/articles/2022/05/24/bitcoin-falls-when-the-us-market-opens-pointing-to-cash-raising).
  Ledger: entries from 15:30 are the one block weak in both periods (section 1); the 14:00 hour is the only afternoon
  hour positive in both.
- **BTC and NAS100.** The average correlation with the Nasdaq 100 was 0.23 in 2024 and 0.52 in 2025 (Yahoo Finance,
  https://finance.yahoo.com/markets/crypto/articles/five-big-tech-earnings-could-150000548.html); about 0.75 on a
  30-day window in January 2026, a 90-day correlation near 0.33 by September 2026 while the 30-day correlation with
  gold reached 0.8 on 1 September 2026 (https://cryptobriefing.com/bitcoin-decouples-nasdaq-aligns-gold/); the
  20-day figure was negative (-0.43) in early December 2025 (https://eco3min.fr/bitcoin-ou-nasdaq/). It swings with
  the regime; what it means for the account is that a BTC and a NAS100 position open at the same time (the guard allows
  two) are not two independent risks in the US afternoon. No ledger test is possible with one market's ledger.
- **The daily and weekly close, 00:00 UTC** (01:00/02:00 Amsterdam): the 00 UTC hour's range is average in 2024-2026
  (0.75 % against 0.74 % for the other hours) and 15 % above average in 2020-2023. It lies outside the windows.
- **Funding resets 00:00 / 08:00 / 16:00 UTC** (Binance, Bybit, every eight hours). No published evidence of a price
  effect at the settlement minute was found (the perpetual-futures literature covers the mechanism, e.g.
  https://arxiv.org/abs/2506.08573). The 08:00 UTC settlement falls inside the morning window (09:00 Amsterdam in
  winter, 10:00 in summer); that hour is a quiet one on our candles (0.63 % range against 0.74 %); 16:00 UTC is the US
  open hour itself. Nothing to act on.
- **Weekend and Asia.** Saturday and Sunday carry half a weekday's range in 2024-2026 (summed hourly ranges 9.3 % and
  11.6 % against 17.8 %; 17-18 % against 23 % in 2020-2023). The bot does not trade weekends (the README: weekends
  -7.7R). Asia 05:00-08:00 Amsterdam are the quietest hours (0.55-0.60 % range, 3.0-3.3 % of the day); the Asia
  range's direction does not carry into 08:00-11:00 (correlation +0.05). Asian hours' share of spot volume rose to
  about 30 % in 2025 (FalconX via coverage), a volume fact, not a return fact.
- **Weekday**: 2024-2026 mean daily returns Monday +0.47 %, Tuesday -0.31 %, Thursday -0.25 %, the rest near zero;
  the ledger shows no weekday that holds in both periods.

**09-11 against 13-17 on the ledger**: the morning made +53.4R in-sample (+17.9R without the two outliers, positive in
2024, 2025 and 2026) and -21.7R out of sample (negative in 2020, 2021 and 2022); the afternoon +8.3R and -19.9R. Neither
session has an out-of-sample edge; the morning's in-sample edge is real beyond the outliers but small.

**The +23.9R and +11.8R trades of June 2026: one-offs.** Both are 1H-zone shorts at 09:30-09:50 Amsterdam with stops
of 0.19 % and 0.50 % of price (0.25 and 0.77 hourly ATRs) and far previous-low targets (23.7R, 11.7R) kept because no
nearer liquidity fitted within 3R. Trades that closed at +5R or more: in-sample 2 (these two), out of sample 0; no
2020-2023 trade closed above +2.94R. Trades with +5R in hand before their exit: in-sample the same 2; out of sample 2
(P59 within the candle that hit its 2R target, and P87, a 7.4R far target that reached +5.4R and ended at break-even
after the +4R rule). The far-target bucket (planned R:R over 3, the target that stays when nothing nearer fits): 5
in-sample trades, 3 won, +36.7R; 10 out-of-sample trades, none won, -10.0R, nine of them never +1.1R in profit. With
no target at all 27 % of in-sample trades would have run to +5R against 14 % out of sample (medians 2.05R and 0.51R).
The in-sample R without those two trades is +26.2R, of which 2026Q2 is +3.8R: the one-quarter dependence is exactly the
two trades.

## 3. Exits on the 5m path (R after costs; the base reproduces the ledgers)

| Variant | IS sum | IS won | IS excl top2 | IS dip | OOS sum | OOS won | OOS dip | trades changed IS / OOS |
|---|---|---|---|---|---|---|---|---|
| The profile (3R cap, nearest; break-even +4R) | +61.7 | 58 % | +26.2 | -4.9 | -41.6 | 33 % | -48.7 | |
| Hard 2R cap (every target at most 2R) | +22.1 | 58 % | +18.3 | -4.9 | -43.9 | 34 % | -48.6 | 16 / 8 |
| 2R cap, far targets kept (nothing nearer fits) | +55.3 | 58 % | +19.8 | -4.9 | -45.9 | 33 % | -50.6 | 13 / 7 |
| Hard 3R cap (the far targets at 3R) | +31.5 | 58 % | +25.7 | -4.9 | -38.6 | 34 % | -45.7 | 3 / 1 |
| No cap (always the previous high, parsed from tp_source) | +57.2 | 44 % | +21.8 | -10.2 | -29.0 | 25 % | -32.9 | 21 / 17 |
| Break-even at +1R / +2R | +51.8 / +58.2 | 48 / 57 % | +16.3 / +22.7 | -5.4 / -4.9 | -39.4 / -41.6 | 31 / 33 % | | 19 / 11, 1 / 0 |
| Trail behind the last 15m swing (1-candle fractal) after +1R / +2R / +3R | +24.9 / +32.0 / +36.2 | 60 / 58 / 58 % | +13.8 / +20.9 / +25.1 | | -39.1 / -42.4 / -41.2 | 35 / 34 / 34 % | | 21 / 12, 6 / 2, 3 / 1 |
| Trail after +2R, 2-candle fractal | +33.7 | 58 % | +23.1 | | -41.2 | 34 % | | 4 / 1 |
| Trail after +2R with no target (let it run) | +45.4 | 46 % | +34.3 | -8.1 | -42.3 | 23 % | -43.8 | 52 / 43 |
| Fixed 3R target, every trade (`tp_fixed_rr 3`; README 5 Oct on the older set: +51.7R vs +62.3R) | +58.1 | 44 % | +52.3 | -6.6 | -31.0 | 22 % | -39.5 | |
| 3R floor: targets under 3R lifted to 3R, far ones kept | +88.3 | 44 % | +52.8 | -6.6 | -34.0 | 21 % | -42.5 | |
| 2R floor / 2.5R floor | +76.7 / +82.1 | 51 / 47 % | +41.2 / +46.7 | -5.5 / -5.5 | -41.7 / -35.4 | 25 / 23 % | -47.1 / -41.7 | |

The caps: the 2R cap (as run) costs R in both periods; no cap is -4.5R in-sample with a dip twice as deep and +12.6R out
of sample (the README's real runs of 6 October agree in direction: without the 2R cap 2020-2023 -6.0R against -11.2R);
the 3R cap is where the in-sample sum and the dip meet, and that is where the profile sits. A 3R floor (not a cap) is
the one target rule that improves both periods: +26.6R in-sample with the R coming from every year (2024 +30.1, 2025
+8.3, 2026 +49.9) and +52.8R without the two outliers, +7.6R out of sample; the price is the win rate (58 % -> 44 %,
33 % -> 21 %) and a deeper in-sample dip (-6.6R). Trailing behind the 15m swing after +2R is a clear no: it changes six
in-sample trades and cuts them from +46.9R to +17.2R (P82 to +4.2R, P79 to +7.2R) while changing two trades out of
sample (+2.9R -> +2.1R).

**Time stops** (a trade still open after N hours is closed once it trades at or below the threshold, every candle after
N h; "once" = looked at only at N h; "unconditional" = closed at N h whatever its R). IS / OOS, R after costs:

| Hours | at <= 0R | <= -0.25R | <= -0.5R | <= -0.75R | once at -0.5R | unconditional (max_hold) |
|---|---|---|---|---|---|---|
| 4 | +48.7 / -42.1 | +46.7 / -44.1 | +48.6 / -41.5 | +60.4 / -40.2 | +60.5 / -41.4 | +20.0 / -43.8 |
| 6 | +57.2 / -40.2 | +58.3 / -37.8 | +64.4 / -40.9 | +63.2 / -39.6 | +61.7 / -43.2 | +48.5 / -40.2 |
| 8 | +56.0 / -39.2 | +57.5 / -38.2 | **+63.6 / -38.5** | +62.9 / -40.1 | +61.7 / -40.8 | +54.3 / -37.8 |
| 12 | +59.9 / -36.4 | +60.3 / -37.0 | +63.2 / -38.7 | +62.6 / -40.3 | +61.7 / -41.6 | +57.4 / -34.4 |
| 16 | +63.6 / -37.3 | +63.6 / -38.0 | +63.1 / -39.2 | +62.6 / -40.5 | +61.9 / -40.6 | +59.0 / -36.3 |
| 24 | +62.0 / -39.7 | +62.8 / -39.9 | +62.3 / -40.2 | +62.1 / -40.9 | +61.7 / -41.2 | +61.5 / -39.5 |

A 4-hour stop cuts winners that were still underwater (IS -13R). From 8 hours on, a trade at or below -0.5R is a
loser: all 5 in-sample and all 7 out-of-sample trades that met the 8 h / -0.5R condition were stopped out later (they
had been +1.0 to +1.8R in profit first in-sample, +0.0 to +1.2R out of sample), so closing them saves 0.4R each: IS
+1.9R, OOS +3.1R. The settings that improve both periods form a plateau: 8-12 h at -0.5 to -0.75R (IS +0.9 to +1.9R,
OOS +1.3 to +3.1R) and 16 h at any threshold from 0 to -0.75R (IS +0.9 to +1.9R, OOS +1.1 to +4.3R); a threshold of 0
or -0.25R at 8-12 h loses in-sample (-1.4 to -5.7R) because trades that are merely flat after 8 h still win. The
unconditional holding limit (the README's 24 h and 48 h tests) loses in-sample at every horizon under 24 h.

## 4. The 1H rule

| 1H bias relative to the trade | IS | IS excl top2 | OOS |
|---|---|---|---|
| with | 54, 56 %, +0.40, +21.5R | +9.8R | 86, 36 %, -0.26, -22.6R |
| 50/50 | 25, 60 %, +0.41, +10.4R | +10.4R | 30, 27 %, -0.46, -13.7R |
| against | 10, 70 %, +2.99, +29.9R | +6.1R | 14, 29 %, -0.38, -5.3R |

The 1H-against trades are all 1M+1W+1D swings (the one combination that does not need the 1H). In-sample: ten trades,
seven won, +29.9R of which P82 is +23.9R; without it nine trades, 67 %, +6.1R; the three shorts +25.3R, the seven longs
+4.6R. Out of sample: 14 trades (12 shorts), 29 %, -5.3R, 2022 -6.1R. Requiring the 1H (`required_aligned: [1H]`, the
EURUSD/gold rule) would drop the against and the 50/50 trades: in-sample +61.7R -> +21.5R (-40.2R; -16.4R without the
outliers), out of sample -41.6R -> -22.6R (+19.0R), win rate 58 -> 56 % and 33 -> 36 %. A half stake on the 1H-against
trades: IS -15.0R, OOS +2.6R. The largest single contribution to the in-sample result is a trade the 1H rule refuses;
the rule cannot be chosen on this evidence either way, and the profile's choice (no 1H) stands on the sum. The same
pattern holds one level up: trades with no timeframe against won 59 % / 26 % (IS / OOS) and trades with one or two
against 55-67 % / 45-50 %; the out-of-sample edge, such as it is, sits in the trades the higher timeframes disagree with
(the README's veto finding for BTC).

## 5. Candidates (exact rule, knob or smallest code change, expected effect, the pre-screen on both ledgers)

The pre-screens take the ledger's trades and remove, re-stake or re-exit them on the 5m candles; a removed trade may
have freed the one-open-trade slot for another signal, which only a run shows. "IS" = 89 trades 2024-2026 at +61.7R,
"OOS" = 130 trades 2020-2023 at -41.6R, R after costs, base stake.

1. **Session end at 15:30 (no entry from the US cash open on).** Rule: windows 09:00-11:00 and 13:00-15:30 Amsterdam.
   Knob: `session.windows: [["09:00", "11:00"], ["13:00", "15:30"]]` in `config/dorus_live_btc.yaml`; no code.
   Expected: fewer trades (15 of 89, 23 of 130), a higher win rate, a smaller dip, little R lost. Pre-screen: IS the
   removed trades 40 % won, -3.2R -> +64.9R (+3.2R), 58 -> 62 % won, dip -4.9 -> -4.4R, by year 2024 +5.1, 2025 -0.4,
   2026 -1.4; OOS the removed trades 30 % won, -11.6R -> -30.1R (+11.6R), dip -48.7 -> -35.1R, by year +1.1 / +5.7 /
   +5.8 / -1.1. The market's reason: 15:00-17:00 are the day's expansion hours (1.8x the hourly ATR, the Kraken
   "most volatile hour" is 16:00 Amsterdam in both seasons) and a 5m shift inside them carries the widest stops and
   the smallest excursions of the day. The README's 7 October runs went the other way (until 20:00: +2.5R) and never
   tried an earlier end. Variant 1b, also no 13:00-14:00 entries (windows 09-11 and 14:00-15:30): IS +64.7R (+3.0R),
   67 % won; OOS -20.3R (+21.3R), dip -25.6R; the 13:00 hour is the quietest hour of the trading day (11-13 hold 3.2 %
   of the range each), but two cuts on hours is more hour-picking than one.
2. **A conditional time stop: 8 hours and at or below -0.5R.** Rule: a trade still open 8 h after its fill that trades
   at or below -0.5R (close-based, every candle) is closed at the market; a trade in profit runs on. Knob: none; the
   smallest change is `exits.time_stop_hours: 8.0` and `exits.time_stop_r: -0.5` beside `max_hold_hours` in
   `kronos_trader/config.py` (ExitParams) and the hold check in `kronos_trader/execution/paper.py` (line 305) plus the
   live runner. Expected: smaller losses, nothing else changes. Pre-screen: IS +1.9R (5 trades, every one a -1R loser
   that had been +1R in profit, now -0.5 to -0.8R), OOS +3.1R (7 trades, all -1R losers); a plateau: 8-12 h at -0.5
   to -0.75R and 16 h at 0 to -0.75R all improve both periods (IS +0.9 to +1.9R, OOS +1.1 to +4.3R); 4 h hurts (IS
   -13R), a flat-or-worse threshold at 8-12 h hurts in-sample, the unconditional hold (`max_hold_hours`, the README's
   24 h: -2.2R) hurts. Needs code (small).
3. **No entry when today already took yesterday's opposite extreme before the signal** (for a long: today's low under
   yesterday's low, Amsterdam day; for a short: today's high over yesterday's high). Knob: none (a gate in the
   confirmation step using the session day; the 8 October screen across markets kept it as a candidate at half stake,
   this is the BTC-only check in both periods). Expected: 9-12 trades fewer per period, every one a 33 % bucket.
   Pre-screen: IS 9 trades, 33 %, -5.0R -> +66.7R (+5.0R; the bucket by year 2024 -1.2, 2025 -2.2, 2026 -1.5), OOS
   12 trades, 33 %, -2.8R -> -38.8R (+2.8R; the bucket 2020 +1.3, 2021 -1.1, 2022 -3.0); at a quarter stake +3.7R /
   +2.1R. Thin but one-directional in five of six years. Needs code.
4. **All five timeframes aligned: a quarter stake (or no trade).** Rule: when `bias_aligned` lists 1M, 1W, 1D, 4H
   and 1H, the stake is 0.25x. Knob: none that keys on the aligned set (`combo_risk_multiplier` keys on the matched
   combination); add `risk.aligned_risk_multiplier: {5: 0.25}` or `bias.max_aligned: 4`. Expected: the late entries
   (38 % / 23 % won against 60-63 % / 32-37 %) stop costing. Pre-screen: IS 13 trades, +0.3R -> -0.2R at 0.25x
   (-0.3R skipped), win rate 58 -> 62 %; OOS 13 trades, 23 %, -8.7R -> +6.5R at 0.25x (+8.7R skipped), the bucket by
   year +0.4 / -2.3 / -5.7 / -1.1. Neutral in-sample, a gain out of sample. Needs code.
5. **Refuse an entry more than half a zone height beyond the zone.** Rule: the shift's close may lie at most 0.5
   zone heights outside the zone. Knob: `risk.max_entry_outside: 0.5` (built, off; `confirmation.max_extension_zones`
   is the related 1.5 default); no code. Expected: 15-25 trades fewer, the chased ones. Pre-screen: IS 15 trades,
   53 %, +1.2R -> -1.2R (the bucket by year 2024 +1.6, 2025 -0.6, 2026 +0.2), dip -4.9 -> -6.1R; OOS 25 trades,
   28 %, -13.2R -> +13.2R (the bucket 2020 -2.7, 2021 -7.5, 2022 +0.6, 2023 -3.7), dip -48.7 -> -38.7R. The README's 2026-only run of the extension cap
   at 0.5 lost 2.3R on four trades; on this ledger the 2026 bucket is +0.2R. Neutral in-sample, strong out of sample;
   a full run on both periods decides.
6. **A 3R floor on the target, the far previous high kept.** Rule: a target that gives less than 3R is placed at 3R; a
   previous high beyond 3R with nothing nearer stays the target (as now). Knob: `risk.min_rr: 3.0` with
   `risk.tp_fallback: fixed`, `risk.tp_fallback_rr: 3.0` (the fallback replaces a target under min_rr; with the 3R
   nearest cap nothing within 3R reaches 3R, so the far target stays), or a new `risk.tp_floor_rr: 3.0` to keep
   min_rr at 0.5 for the refusal logic; the gold profile uses the same fallback at 2R. Expected: R from every year,
   not two trades, at a lower win rate. Pre-screen: IS +88.3R (+26.6R; 2024 +30.1, 2025 +8.3, 2026 +49.9 against
   +10.3 / +11.8 / +39.6), won 58 -> 44 %, dip -4.9 -> -6.6R, without the two outliers +52.8R against +26.2R, three
   later signals would have been blocked by the longer holds (median winner 5.2 h against 1.7 h); OOS -34.0R (+7.6R;
   by year 2020 +7.2, 2021 +2.3, 2022 +0.1, 2023 -2.0), won 33 -> 21 %, dip -48.7 -> -42.5R, but on top of candidate 1 the
   out-of-sample gain disappears (-32.7R against -30.1R). The 5 October sweep rejected a fixed 3R on every trade on the
   older set (35 %, +51.7R against +62.3R); on this set that variant is +58.1R (-3.6R) with +52.3R excl. the outliers
   and OOS +10.6R. This candidate buys independence from June 2026 with the win rate; against Max's "winrate omhoog".
7. **The scalp combination at a quarter stake.** Rule: a 1D+4H+1H trade risks 0.25x. Knob:
   `risk.combo_risk_multiplier: {"1D+4H+1H": 0.25}`; no code. Expected: the 24 / 45 scalps (54 % / 36 % won, +0.07 /
   -0.27R a trade) stop mattering. Pre-screen: IS the bucket +1.7R -> -1.3R on the total at 0.25x, OOS the bucket
   -12.1R (by year 2020 -7.0, 2021 -3.1, 2022 -2.2, 2023 +0.2) -> +9.1R on the total at 0.25x. The README's removal (7 October) cost -2.8R in-sample and a worse account replay; the stake
   version halves that cost. Neutral in-sample, a gain out of sample.
8. **No entry on a climax shift candle.** Rule: no entry when the confirmation candle's body exceeds 2x the ATR14 of
   its timeframe. Knob: none; `confirmation.max_body_atr: 2.0` in the balance-shift check. Pre-screen: IS 8 trades,
   38 %, -1.3R -> +1.3R (the bucket by year 2024 -3.9, 2025 +2.8, 2026 -0.2); OOS 8 trades, 12 %, -7.2R -> +7.2R (the
   bucket 2020 +0.5, 2021 -5.5, 2022 -1.1, 2023 -1.1). Thin (8 / 8), mixed by year in-sample; related to candidate 5 (chasing), overlap 1 / 3 trades.
   Needs code.

**Together** (candidates 1, 3, 4 as skips and 2; the profile's target): IS 58 trades, 69 % won, +66.9R (+5.2R; 2024
+12.9, 2025 +14.9, 2026 +39.2; without the two outliers +31.5R), dip -2.2R; OOS 90 trades, 33 %, -24.1R (+17.5R; 2020
-10.1, 2021 -16.1, 2022 -3.1, 2023 +5.2), dip -29.7R. With the 3R floor instead of the profile's target on the same set:
IS +80.8R (48 % won, excl. outliers +45.3R), OOS -32.9R (18 %). The robust set raises the win rate and shortens the
losing runs in both periods; it does not turn 2020-2023 positive. Nothing here changes the reading that BTC's edge
outside 2024-2026 is unproven.

## 6. Checked and not candidates

- The 1H requirement: IS -40.2R (-16.4R without the outliers), OOS +19.0R (section 4).
- R:R floor 1.0: IS -7.3R (the 0.5-1R targets win 83 % in-sample), OOS +15.5R. The 2R cap: IS -6.4R (far kept) to
  -39.6R (hard), OOS worse too. No cap: IS -4.5R and a -10.2R dip, OOS +12.6R. Break-even at +1R / +2R: IS -9.9R / -3.5R.
- A trailing stop behind the last 15m swing after +2R (and +1R, +3R, a 2-candle fractal, with no target): IS -16 to
  -37R; it cuts the two far winners; OOS between -1.8R and +2.5R.
- Unconditional time stops at 4-16 h: IS -2.7R to -41.7R; 24 h -0.2R.
- Stops wider than 1.5 ATR14(1H) (IS -3.7R, OOS +12.3R); the hourly ATR above 1.2 % of price (IS -3.7R, OOS +15.9R):
  the out-of-sample losses sit in high volatility, the in-sample trades there won.
- The far-target rule (planned R:R over 3): skipping it is IS -36.7R, OOS +10.0R; a hard 3R cap IS -30.2R, OOS +3.0R.
- Premium/discount (the top quarter of the 5-, 10-, 20-day range): no cut once computed on closed candles; the earlier
  `smc_analysis_out.md` figure was a look-ahead.
- The 60-day and 20-day trend, the daily efficiency ratio, the 24 h range against ATR, weekday, calendar month, zone
  age, the wait from touch to shift, target size against the daily ATR, stop in dollars or as a share of price: no bucket
  with enough trades is weak in both periods except those listed in section 1 (stop 0.75-1 %: a U-shape; stop over 2 ATR:
  9 / 12 trades, part of candidate 5's chasing pattern; wait over 24 h: 10 / 10 trades, the 4H visits).
- The 16:00 hour alone (IS +3.9R, OOS +4.2R) is inside candidate 1; the 13:00 hour alone (IS -0.2R, OOS +9.8R) is
  candidate 1b.
- The Asia-range sweep before the entry: IS 19 trades 53 % +1.20R a trade, OOS 39 trades 23 % -0.42R: opposite signs.
