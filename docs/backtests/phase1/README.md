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
