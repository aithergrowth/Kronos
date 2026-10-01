# Phase 1 backtests: EURUSD and XAUUSD on TradingView history (2026-10-01)

Code revision: the `feature/kronos-trader` head of 2026-10-01 (POI liquidity-to-protection, M+D+4H on, BS confirmations,
min R:R 1:3, sessions 09-11 / 13-17 Amsterdam, Kronos off). Data: `data/tv_cache/OANDA_*` pulled through the TradingView
MCP (latest 5000 bars per timeframe, so 15m covers eleven weeks, 1H ten months, 4H two to three years, 1D since 2007;
gold weekly and monthly resampled from daily). Spread model: the symbol's typical spread. Risk 1% of 100,000.

**These runs are not evidence for or against the strategy.** The samples are tiny, the rule definitions still have
open points (P wick or body, BS threshold) and zero chart fixtures have been checked. They show that the machine
works end to end on history and where the rules, as coded, stop trades from happening.

| Symbol | Step | Period | Trades | Realized R | Wins | Losses | Break-even | Open at end |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 1H | 2025-12-10 to 2026-10-01 (10 months) | 2 | +3.09 | 1 | 1 | 0 | none |
| EURUSD | 15m | 2026-07-21 to 2026-10-01 (10 weeks) | 1 | +4.05 | 1 | 0 | 0 | none |
| XAUUSD | 1H | 2025-11-26 to 2026-10-01 (10 months) | 7 | -4.00 | 0 | 4 | 2 | +8.77R unrealized |
| XAUUSD | 15m | 2026-07-16 to 2026-10-01 (11 weeks) | 5 | -2.00 | 0 | 2 | 2 | +8.77R unrealized |

## What the runs say

- **Trades are rare.** Most steps are rejected with *fewer than 3 timeframes agree*: the bias engine reads 50/50 on
  several timeframes most of the time, because its liquidity view and its balance view conflict. On EURUSD that
  leaves two trades in ten months. Whether Dorus would also have stayed flat that often is exactly what the bias
  fixtures (course_bias_rejection, D's no-trade chart) have to settle; this is the first calibration target.
- **The gold shorts of September 2026** all come from one monthly POI: three were stopped or scratched within
  hours, the fourth was still open at the end of the data with the move going its way. One POI, one idea, five
  attempts: the re-entry policy after a stop-out is a rule we have not pinned down.
- **Realized:** EURUSD +3.1R (1H step) and +4.1R (15m step, the same 22 September short, seen through a BS
  confirmation); gold -4.0R (1H step) and -2.0R (15m step). Nothing here is statistically meaningful.
- **Costs:** the typical-spread model only. Commission, slippage and swap are not modelled yet.

## Next

1. Bias calibration against Astra's fixtures before anything else; then re-run.
2. Deeper intraday history from the MT5 terminal (`copy_rates_range`, years of M5/M15) for the 100-trade target.
3. Re-entry rule after a stop-out on the same POI; cost model with commission and slippage.

## Trade lists

### EURUSD, step 1H

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-06 11:00:00 | 2026-07-06 17:00:00 | SHORT | 1D | BMS | 1.14201 | 1.14343 | 1.13618 | 1.14343 | stop | -0.97 |
| 2026-09-22 11:00:00 | 2026-09-23 17:00:00 | SHORT | 4H | first_candle | 1.14658 | 1.14878 | 1.13746 | 1.13746 | take_profit | +4.05 |

### EURUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-22 11:00:00 | 2026-09-23 17:00:00 | SHORT | 4H | BS | 1.14658 | 1.14878 | 1.13746 | 1.13746 | take_profit | +4.05 |

### XAUUSD, step 1H

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-03 13:00:00 | 2026-03-03 13:00:00 | LONG | 1D | first_candle | 5224.56 | 5166.89 | 5602.23 | 5166.89 | stop | -1.00 |
| 2026-04-02 07:00:00 | 2026-05-18 00:00:00 | LONG | 1D | first_candle | 4598.95 | 4482.56 | 5238.77 | 4482.56 | stop | -1.00 |
| 2026-09-11 07:00:00 | 2026-09-11 07:00:00 | SHORT | 1M | BMS | 4316.92 | 4356.28 | 3942.1 | 4356.28 | stop | -1.00 |
| 2026-09-14 13:00:00 | 2026-09-14 16:00:00 | SHORT | 1M | BOS | 4271.17 | 4312.03 | 3942.1 | 4312.03 | stop | -1.00 |
| 2026-09-15 07:00:00 | 2026-09-15 14:00:00 | SHORT | 1M | BOS | 4299.42 | 4307.88 | 3942.1 | 4299.42 | breakeven | -0.00 |
| 2026-09-22 07:00:00 | 2026-09-22 12:00:00 | SHORT | 1M | first_candle | 4343.45 | 4347.59 | 3942.1 | 4343.45 | breakeven | -0.00 |
| 2026-09-23 11:00:00 | 2026-10-01 06:00:00 | SHORT | 1M | BOS | 4318.25 | 4333.08 | 3942.1 | 4188.23 | end_of_data | +8.77 |

### XAUUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-11 07:00:00 | 2026-09-11 07:00:00 | SHORT | 1M | BMS | 4316.92 | 4356.28 | 3942.1 | 4356.28 | stop | -1.00 |
| 2026-09-14 13:00:00 | 2026-09-14 16:45:00 | SHORT | 1M | BOS | 4271.17 | 4312.03 | 3942.1 | 4312.03 | stop | -1.00 |
| 2026-09-15 07:00:00 | 2026-09-15 14:00:00 | SHORT | 1M | BOS | 4299.42 | 4307.88 | 3942.1 | 4299.42 | breakeven | -0.00 |
| 2026-09-22 07:00:00 | 2026-09-22 12:30:00 | SHORT | 1M | first_candle | 4343.45 | 4347.59 | 3942.1 | 4343.45 | breakeven | -0.00 |
| 2026-09-23 11:00:00 | 2026-10-01 05:45:00 | SHORT | 1M | BOS | 4318.25 | 4333.08 | 3942.1 | 4188.23 | end_of_data | +8.77 |

## The last eleven weeks across six instruments (15m step)

Same code, same settings; the 15m history reaches back to mid or late July (BTC: 10 August). *Zones* counts distinct
POI-and-target pairs, so repeated attempts at one zone show up as trades > zones.

| Symbol | Period | Trades | Zones | Realized R | Wins | Losses | Break-even | Open at end |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 2026-07-21 to 2026-10-01 | 1 | 1 | +4.05 | 1 | 0 | 0 | none |
| GBPUSD | 2026-07-21 to 2026-10-01 | 1 | 1 | -0.98 | 0 | 1 | 0 | none |
| USDJPY | 2026-07-21 to 2026-10-01 | 4 | 3 | -3.90 | 0 | 4 | 0 | none |
| XAUUSD | 2026-07-16 to 2026-10-01 | 5 | 1 | -2.00 | 0 | 2 | 2 | +8.77R |
| BTCUSD | 2026-08-10 to 2026-10-01 | 1 | 1 | -1.01 | 0 | 1 | 0 | none |
| NAS100 | 2026-07-16 to 2026-10-01 | 0 | 0 | +0.00 | 0 | 0 | 0 | none |
| **all six** | | **12** | | **-3.84** | **1** | **8** | **2** | **+8.77R** |

Eleven decided trades: one winner (+4.1R), eight stops, two scratches, -3.8R realized, with one gold
short still open at +8.8R. A method that targets 1:3 or better needs roughly one win in four to break even;
one in nine is below that. The sample is far too small to call it, and the open gold trade alone would flip
the sign, but the direction of the evidence is clear: the rules as coded do not yet make money, and the
first job is still to check them against Dorus's own calls on these same weeks (Astra's K3, K4 and K5 records
cover gold and BTC in August and September 2026).

Patterns worth a rule: USDJPY lost four times on three zones, twice within an hour on the same one; BTC blocked
four signals because its one open trade was still running; NAS100 never found three agreeing timeframes.

## Trade lists, 15m runs

### EURUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-22 11:00:00 | 2026-09-23 17:00:00 | SHORT | 4H | BS | 1.14658 | 1.14878 | 1.13746 | 1.13746 | take_profit | +4.05 |

### GBPUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-21 14:15:00 | 2026-07-21 14:30:00 | LONG | 1D | BMS | 1.33997 | 1.33792 | 1.35582 | 1.33792 | stop | -0.98 |

### USDJPY, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-30 11:00:00 | 2026-07-30 11:00:00 | LONG | 4H | first_candle | 162.831 | 162.714 | 163.908 | 162.714 | stop | -0.96 |
| 2026-07-30 12:00:00 | 2026-07-30 12:30:00 | LONG | 4H | first_candle | 162.899 | 162.714 | 163.908 | 162.714 | stop | -0.97 |
| 2026-09-08 12:30:00 | 2026-09-08 18:15:00 | SHORT | 4H | BMS | 153.964 | 154.393 | 152.27 | 154.393 | stop | -0.99 |
| 2026-09-29 13:00:00 | 2026-09-30 00:45:00 | LONG | 1D | BMS | 157.353 | 157.07 | 159.037 | 157.07 | stop | -0.98 |

### XAUUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-11 07:00:00 | 2026-09-11 07:00:00 | SHORT | 1M | BMS | 4316.92 | 4356.28 | 3942.1 | 4356.28 | stop | -1.00 |
| 2026-09-14 13:00:00 | 2026-09-14 16:45:00 | SHORT | 1M | BOS | 4271.17 | 4312.03 | 3942.1 | 4312.03 | stop | -1.00 |
| 2026-09-15 07:00:00 | 2026-09-15 14:00:00 | SHORT | 1M | BOS | 4299.42 | 4307.88 | 3942.1 | 4299.42 | breakeven | -0.00 |
| 2026-09-22 07:00:00 | 2026-09-22 12:30:00 | SHORT | 1M | first_candle | 4343.45 | 4347.59 | 3942.1 | 4343.45 | breakeven | -0.00 |
| 2026-09-23 11:00:00 | 2026-10-01 05:45:00 | SHORT | 1M | BOS | 4318.25 | 4333.08 | 3942.1 | 4188.23 | end_of_data | +8.77 |

### BTCUSD, step 15m

| opened_at | closed_at | direction | poi_tf | confirmation | entry | stop | take_profit | exit | reason | r |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-11 13:30:00 | 2026-08-18 14:15:00 | SHORT | 1D | BMS | 64192.1 | 64712.4 | 62275 | 64712.4 | stop | -1.01 |

## Filters on the same eleven weeks: news blackout and Kronos

Same runs with two filters, each on its own. *News*: no new entry from 30 minutes before to 30 minutes after a
high-impact event of the symbol's currencies (TradingView economic calendar, `data/calendar/high_impact.csv`;
Dorus, source G 11:08). *Kronos*: the forecast must agree with the setup direction (`--kronos filter`); the gold
run did not finish in the time allowed.

| Symbol | Rules only | With news blackout | With Kronos filter |
|---|---|---|---|
| EURUSD | 1 trades, +4.1R realized (1W 0L) | 1 trades, +4.1R realized (1W 0L) | n/a |
| GBPUSD | 1 trades, -1.0R realized (0W 1L) | 1 trades, -1.0R realized (0W 1L) | 1 trades, -1.0R realized (0W 1L) |
| USDJPY | 4 trades, -3.9R realized (0W 4L) | 3 trades, -2.9R realized (0W 3L) | 3 trades, -2.9R realized (0W 3L) |
| XAUUSD | 5 trades, -2.0R realized (0W 2L), +8.8R open | 5 trades, -2.0R realized (0W 2L), +8.8R open | n/a |
| BTCUSD | 1 trades, -1.0R realized (0W 1L) | 3 trades, -3.1R realized (0W 3L) | 3 trades, -3.1R realized (0W 3L) |

- **News** removed one USDJPY loss (the 30 July entry half an hour before US GDP and PCE) and the 11 August
  BTC short that sat half an hour before a US housing release. That BTC short had blocked four later signals
  for a week; without it those fired and all three lost. Net across the five: USDJPY +1.0R better, BTC -2.1R
  worse. The rule stays on because it is Dorus's own rule, not because of this sample; which events count as
  high impact deserves a second look (TradingView marks housing data high, ForexFactory does not).
- **Kronos** removed the only winner (EURUSD, 22 September) and, by removing the same BTC short, let the three
  BTC losers through. It stays advisory, not a filter, until a larger sample says otherwise.
