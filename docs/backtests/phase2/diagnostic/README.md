# Phase 2 backtest: three and a half years, four instruments, 5-minute steps (2026-10-01) - DIAGNOSTIC RUN (code of 12:49, before the last simulator fixes; superseded by the frozen run)

Data: HistData.com 1-minute candles (bid), 2023-01 to 2026-09, resampled to 5m, 15m, 1H and 4H with the 4H bins
anchored to the New York close; daily and monthly candles from the TradingView history (OANDA EURUSD since 2007,
FOREX.com for the others). Weekly candles: FOREX.com history for GBPUSD, USDJPY and XAUUSD; for EURUSD the OANDA
weekly file only started in November 2023, so its weekly series was rebuilt from the OANDA daily candles (2007 on;
open, high and low identical to the OANDA weekly bars where both exist). Every run starts 2023-03-01 so each
timeframe has its full lookback behind it.

Shared rules (`docs/STRATEGY.md`, A1-A19): 3/5 bias with the listed combinations, POI from liquidity to protection,
balance-shift / BMS / BOS confirmations on the timeframe table, stop behind P, target on liquidity, 1 % risk of
100,000, one trade at a time, entries 09:00-17:00 Amsterdam, no entry 30 minutes either side of high-impact news
(1,340 events, TradingView calendar), Kronos off. Costs: the symbol's typical spread on every fill; no commission,
no slippage. The walk-forward steps every closed 5-minute candle, exactly as the live loop sees them.

Three profiles were run on the same data:

- **A** forward-test profile, minimum R:R 1:3 (Max's rule): M+D+4H combination on, no lone first candle, 1-pip stop buffer.
- **B** the same profile with minimum R:R 1:2.
- **C** Dorus's written list and nothing else (`config/dorus_pure.yaml`): the four listed combinations only, first candle
  accepted as a confirmation, no stop buffer, minimum R:R 1.5 standing in for "attractive" until Max sets a number.

## Comparison

| Symbol | Trades A | Win A | Exp A | Total A | Trades B | Win B | Exp B | Total B | Trades C | Win C | Exp C | Total C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 78 | 24% | -0.04R | -3.4R |
| GBPUSD | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 72 | 19% | -0.38R | -27.3R |
| USDJPY | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 122 | 27% | +0.01R | +1.3R |
| XAUUSD | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 125 | 18% | -0.19R | -23.5R |
| **all four** | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 397 | 22% | -0.13R | -52.9R |

Decided trades exclude positions still open at the end of the data. Expectancy is the average R per decided trade;
worst run is the deepest drawdown of the R equity curve; win rate counts wins against losses (break-evens shown separately).

## Profile C: Dorus's written list only (`config/dorus_pure.yaml`): R:R 1.5, first candle on, no M+D+4H, no stop buffer

| Symbol | Period | Decided trades | Win rate | Expectancy | Average winner | Planned R:R | Profit factor | Total | Net of commission | Worst run | Open at end |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 2023-03-01 to 2026-09-25 | 78 | 24% (18W 57L 3BE) | -0.04R | +2.8R | 4.5 | 0.94 | -3.4R | -8.0R | -20.2R | none |
| GBPUSD | 2023-03-01 to 2026-09-25 | 72 | 19% (13W 56L 3BE) | -0.38R | +2.3R | 3.5 | 0.52 | -27.3R | -30.5R | -31.8R | none |
| USDJPY | 2023-03-01 to 2026-09-25 | 122 | 27% (32W 86L 4BE) | +0.01R | +2.7R | 6.2 | 1.02 | +1.3R | -9.3R | -9.7R | +1.6R |
| XAUUSD | 2023-03-01 to 2026-09-25 | 125 | 18% (22W 98L 5BE) | -0.19R | +3.5R | 9.2 | 0.77 | -23.5R | -25.7R | -26.1R | +0.4R |
| **all four** | | **397** | **22%** (85W 297L 15BE) | **-0.13R** | +2.9R | 6.3 | 0.82 | **-52.9R** | -73.5R | -68.7R | +2.1R |

Distinct zones behind each rejection (not candles; a zone can appear under several reasons)

| Reason | EURUSD | GBPUSD | USDJPY | XAUUSD |
|---|---|---|---|---|
| (not recorded in this run) | | | | |

By year

| Year | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 2023 | 97 | 22 | 71 | -0.14R | -13.8R |
| 2024 | 104 | 20 | 78 | -0.17R | -17.6R |
| 2025 | 148 | 33 | 110 | -0.09R | -13.5R |
| 2026 | 48 | 10 | 38 | -0.17R | -8.1R |

By POI timeframe

| POI | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 1D | 35 | 7 | 27 | -0.30R | -10.4R |
| 1H | 224 | 45 | 175 | -0.20R | -45.4R |
| 1M | 4 | 0 | 3 | -0.72R | -2.9R |
| 1W | 10 | 3 | 3 | +1.77R | +17.7R |
| 4H | 124 | 30 | 89 | -0.10R | -11.9R |

By confirmation

| Confirmation | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| BMS | 85 | 24 | 59 | -0.01R | -0.9R |
| BOS | 43 | 12 | 29 | -0.05R | -2.3R |
| BS | 67 | 10 | 54 | -0.21R | -14.1R |
| first_candle | 202 | 39 | 155 | -0.18R | -35.7R |

By direction

| Direction | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| LONG | 302 | 67 | 222 | -0.11R | -32.8R |
| SHORT | 95 | 18 | 75 | -0.21R | -20.1R |

By target timeframe

| Target on | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 15m | 163 | 35 | 126 | -0.14R | -23.3R |
| 1D | 51 | 6 | 38 | -0.44R | -22.7R |
| 1H | 109 | 24 | 82 | -0.24R | -26.1R |
| 1M | 4 | 1 | 3 | +0.82R | +3.3R |
| 1W | 8 | 2 | 3 | +1.77R | +14.2R |
| 4H | 62 | 17 | 45 | +0.03R | +1.8R |

By planned R:R

| Planned R:R | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 1.5-2 | 133 | 41 | 91 | -0.10R | -13.8R |
| 2-3 | 106 | 24 | 81 | -0.16R | -16.9R |
| 3-5 | 72 | 13 | 57 | -0.10R | -7.2R |
| <1.5 | 2 | 0 | 2 | -0.97R | -1.9R |
| >5 | 84 | 7 | 66 | -0.16R | -13.1R |

By entry hour (UTC)

| Hour | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 7 | 44 | 8 | 33 | -0.28R | -12.4R |
| 8 | 58 | 13 | 45 | +0.02R | +1.4R |
| 9 | 51 | 7 | 41 | -0.48R | -24.2R |
| 10 | 44 | 11 | 32 | -0.02R | -0.8R |
| 11 | 42 | 13 | 28 | +0.13R | +5.5R |
| 12 | 29 | 5 | 23 | -0.47R | -13.7R |
| 13 | 50 | 11 | 38 | +0.04R | +1.8R |
| 14 | 56 | 15 | 38 | +0.07R | +4.1R |
| 15 | 23 | 2 | 19 | -0.63R | -14.5R |

By time from the zone touch to the entry

| Since touch | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 1-3d | 50 | 13 | 34 | -0.06R | -3.0R |
| 1-4h | 60 | 19 | 40 | +0.24R | +14.6R |
| 4-24h | 65 | 14 | 48 | -0.29R | -19.1R |
| <1h | 202 | 34 | 162 | -0.28R | -56.7R |
| >3d | 20 | 5 | 13 | +0.56R | +11.2R |

By entry distance beyond the zone edge (in zone heights)

| Entry | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| 0-25% beyond | 25 | 3 | 21 | -0.60R | -14.9R |
| inside zone | 372 | 82 | 276 | -0.10R | -38.0R |

By visit number (1 = first return to the zone)

| Visit | Trades | Wins | Losses | Expectancy | Total |
|---|---|---|---|---|---|
| n/a (older run) | | | | | |

FTMO lens (1 % risk per trade, R curve per symbol)

| Symbol | Trades | Total | Worst run | First 10R drawdown | 10R drawdowns | Worst single day |
|---|---|---|---|---|---|---|
| EURUSD | 78 | -3.4R | -20.2R | 2025-04-11 | 4 | -3.4R |
| GBPUSD | 72 | -27.3R | -31.8R | 2023-12-18 | 1 | -3.0R |
| USDJPY | 122 | +1.3R | -9.7R | never | 0 | -3.0R |
| XAUUSD | 125 | -23.5R | -26.1R | 2023-12-28 | 5 | -3.2R |

By exit

| Exit | Trades | Total |
|---|---|---|
| breakeven | 16 | -1.9R |
| stop | 296 | -296.6R |
| take_profit | 85 | +245.6R |

## Reading it

(pending: the 1:2 and pure-list batches are still running)

## Trade lists

One CSV per symbol and profile next to this file (`EURUSD_5m.csv`, `EURUSD_5m_rr2.csv`, `EURUSD_5m_pure.csv` ...),
with entry, stop, target, exit, reason, planned R:R and realised R per trade.
