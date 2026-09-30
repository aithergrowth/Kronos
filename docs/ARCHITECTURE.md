# Architecture

```
                 TradingView MCP  ──►  data/tv_cache (CSV)  ─┐
                 MetaTrader 5     ──►  MT5Broker.get_candles ─┼─►  MultiTimeframeData ──►  StrategyEngine ──►  Analysis / Signal
                 any CSV          ──►  CandleSeries.from_csv ─┘          │                     │                    │
                                                                        as_of(ts)        KronosForecaster       RiskGuard
                                                                     (closed only)     (extra indicator)          │
                                                                                                             PaperBroker / MT5Broker
                                                                                                                     │
                                                                                                             TelegramNotifier
```

## Packages

| Package | Responsibility |
|---|---|
| `kronos_trader.core` | `Timeframe` (ordering, bin maths), `CandleSeries` (validated OHLCV), all domain dataclasses (`POI`, `TradeSetup`, `Analysis`, …) |
| `kronos_trader.strategy` | the rules: `structure` (swings, liquidity, sweeps, breaks, balance blocks) → `bias` → `poi` → `confirmation` → `risk` → `exits`; `engine` orchestrates |
| `kronos_trader.indicators` | `KronosForecaster`: lazy model load, sampled paths → `ForecastSummary` |
| `kronos_trader.data` | `resample`, `MultiTimeframeData.as_of` (no look-ahead), TradingView MCP client + payload parser, CSV cache |
| `kronos_trader.execution` | `Broker` interface, `PaperBroker` (spread, SL/TP/BE simulation), `MT5Broker`, `RiskGuard` |
| `kronos_trader.notify` | Telegram Bot API + message formatting |
| `kronos_trader.backtest` | walk-forward `Backtester`, statistics, report |
| `kronos_trader.live` | `LiveRunner`: fetch → analyse → notify → execute loop |
| `kronos_trader.cli` | `scan`, `backtest`, `forecast`, `import-tv`, `resample`, `telegram-test`, `tv-tools` |

## Guarantees

- **No look-ahead.** `MultiTimeframeData.as_of(ts)` returns only candles whose close time ≤ ts; the engine re-applies `closed_as_of`. Swings need `swing_right` later candles before they exist; sweeps/breaks are detected in a single forward pass.
- **Deterministic rules.** Same candles in → same `Analysis` out. Kronos sampling is the only stochastic element and is isolated behind `ForecastSummary`.
- **Explainable decisions.** Every rejection is a sentence in `Analysis.rejections`; every bias carries its `notes`.
- **Risk before execution.** Nothing reaches a broker without `RiskGuard.can_open`.

## Extension points

- New data source: return `{Timeframe: CandleSeries}` and pass it to `MultiTimeframeData` or `LiveRunner(fetch=...)`.
- New broker: implement `execution.base.Broker`.
- New confirmation type: add to `ConfirmationType` and `confirmation.find_confirmation`.
- New indicator: give the engine any object with `forecast(series) -> ForecastSummary`.

## Performance

Structure analysis is cached per (symbol, timeframe, last candle); swing detection is vectorised. A 15-minute-step backtest runs at roughly 200–400 steps per second on a laptop CPU.
