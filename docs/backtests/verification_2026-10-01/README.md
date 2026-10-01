# Independent strategy/repository verification — 2026-10-01

**The prototype runs, but it is not a verified replica of Dorus's discretionary method and these tests do not establish a profitable edge.** Nine YouTube caption sources and selected academy slides are covered in [STRATEGY.md](../../STRATEGY.md). No independent audio certification, complete academy/channel review or complete source-annotated trade fixture is claimed.

## Scope and pinned evidence

- Original baseline: `6ccfd06dd767e0d8e13a760bb2fb7b39a9719fff`; the materialized runtime/data/test inputs used for reproduction matched their Git blob hashes (102 files).
- Concurrent feature work preserved through `a2a29aa12c0284ead7fea356717b51a921d27f8e`: terminal discovery/login, news/calendar comparisons, the 09:00–17:00 forward profile and briefing/POI notifications. Astra fixes are integrated on `astra/definitions`, with `feature/kronos-trader` as the PR target.
- `input_manifest.json`: 36 cached OANDA/BINANCE CSVs, **121,129 rows**. Finite OHLCV, ordered unique timestamps and high/low bounds pass. This checks file integrity, not exchange authenticity, completeness, executable quotes or MT5 feed equivalence.
- All six original trade lists reproduce, including the empty NAS100 list. `baseline_*` preserves that result. `corrected_*` uses corrected fills/BE and the integrated code; `corrected_news_*` adds the stored calendar, with the project-selected ±30-minute window. The three benchmark columns keep **Kronos off**, minimum RR3, 1% risk, first-candle option enabled and split Amsterdam sessions, pinned explicitly in the script. The current forward profile instead uses 09:00–17:00, first-candle off and news on; its separate result is recorded below. No parameters were tuned to improve the result.
- Each symbol starts an independent 100,000 account; the step is 15m with the available native 1H/4H/D/W/M series. There is no 1m/5m entry history in this experiment. M15 coverage begins 16 July for gold/NAS,21 July for FX and10 August for BTC, ending 1 October 2026. Exact per-symbol open-time intervals are in JSON.

## Observed results

Cells show completed trade count / sum of trade R. End-of-data liquidation marks are excluded from completed/realized statistics and reported separately.

| Symbol | Original simulator | Corrected, news off | Corrected, news on |
|---|---|---|---|
| EURUSD | 1 / +4.05R | 1 / +3.97R | 1 / +3.97R |
| GBPUSD | 1 / -0.98R | 1 / -0.95R | 1 / -0.95R |
| USDJPY | 4 / -3.90R | 4 / -3.81R | 3 / -2.86R |
| XAUUSD | 4 / -2.00R; +8.77R end mark | 6 / -3.96R | 6 / -3.96R |
| BTCUSD | 1 / -1.01R | 1 / -1.00R | 3 / -2.99R |
| NAS100 | 0 / +0.00R | 0 / +0.00R | 0 / +0.00R |

These sums are **not a pooled portfolio return**: each symbol has a separate account and position cap. R uses the configured risk distance, including its sizing buffer; losses can differ from −1R. Cash PnL/lots are in the trade CSVs. Observed sums: original −3.84R across 11 completed trades plus one end mark; corrected news-off −5.76R across 13; corrected news-on −6.80R across 14. See `summary.json` for exact totals.

The sample is small, uses partially unresolved strategy definitions, and is not an out-of-sample profitability demonstration. Gold's original positive end mark cannot be treated as a realized winner. Corrected entry prices and BE ordering materially change its path. These results assess this implementation/data/policy combination, not Dorus's personal trading record.

**Timing limitation affecting the sole winning symbol:** EURUSD's native monthly opens include broker/session-shifted dates rather than only the first of the month. The runtime's open-plus-one-month closure assumption is not independently verified for this feed. Some labels imply a close before the next monthly open; therefore EURUSD's result and any total including it are **timing-unvalidated**, not a clean lookahead-free benchmark. Other symbols have first-day monthly labels, but feed provenance and session alignment still need verification. Calendar-month arithmetic consistency alone does not prove broker closure times.

## Current forward profile, independently rerun

Pinned to feature commit `a2a29aa`: 09:00–17:00 Amsterdam, first-candle confirmation off, news ±30 minutes enabled from the stored CSV, Kronos off. Same six datasets and corrected simulator; no parameter optimization.

| Symbol | Completed trades | Sum trade R | End marks / R |
|---|---:|---:|---:|
| BTCUSD | 3 | -2.99R | 0 / +0.00R |
| EURUSD | 1 | +3.97R | 0 / +0.00R |
| GBPUSD | 1 | -0.95R | 0 / +0.00R |
| NAS100 | 0 | +0.00R | 0 / +0.00R |
| USDJPY | 2 | -1.94R | 0 / +0.00R |
| XAUUSD | 4 | -2.96R | 1 / +8.70R |

Total: **11 completed trades, -4.88R**, with 1 winner(s), 9 losses and 1 break-even exits. Separate end marks: 1 / +8.70R. This remains a sum across independent accounts, with the same EURUSD monthly-timing and cost limitations.

## Corrections tested

| Defect | Correction / evidence |
|---|---|
| Bounded backtest closed at a later dataset price | Uses the last processed candle. Long/short regressions compare bounded and physically truncated inputs. |
| A still-eligible old confirmation supplied a later market fill outside the current bar | Fills at current step close with modeled executable-side spread; recomputes size, risk and RR; rejects crossed SL/TP, low RR or undersized orders. CSV includes `signal_entry`/`signal_rr` separately. |
| Stop gaps filled at unreachable stop price | Uses executable opening price when the opening quote has crossed the stop. |
| BE activation ignored a same-bar return | Explicit conservative OHLC ordering, including opening events, old-stop priority and reachable BE returns. A 3R target precedes a 4R trigger. This is a simulation assumption, not recovered ticks. |
| End liquidation/equity omitted exit spread | Both use executable-side liquidation; SL/TP prices are not charged spread twice. |
| Monthly slice arithmetic disagreed | `closed_as_of` uses forward close times consistently. Shifted monthly resampling that can expose future OHLC now raises and requires verified native data/period boundaries. This does not certify shifted native labels. |
| Dense candles passed as a slower timeframe | Cadence validation rejects 30m-as-H1 while retaining calendar-month and session-gap tolerance. |
| Kronos filter failed open on unavailable forecasts | Filter mode rejects missing/failed forecasts; advisory mode keeps its documented commentary behavior. |
| BTC forecasts skipped weekends | Explicit `weekend_symbols` controls continuous calendars; defaults include BTCUSD, BTCUSDT and BINANCE:BTCUSDT, with other aliases requiring configuration. Not a full exchange-holiday calendar. |
| Briefing/POI alerts marked as sent before delivery | Sent-state now updates only on successful delivery; offline retry regressions cover both notifications. |
| Approval could cross into a news blackout | Execution rechecks the existing calendar before broker access. Missing/stale calendar coverage remains an independent limitation. |

**Local test result: 222 passed, 1 skipped, 1 deselected** (`tests/trader`, excluding `slow`). The skipped test is the absent complete source-fixture case; the deselected test requires real Kronos weights/input. Focused failing-before/passing-after regressions support the corrections. Full test log and tested runtime hashes are in `validation.json`. Hosted CI on the initial publication exposed a pandas 3 microsecond/nanosecond search incompatibility. The follow-up explicitly normalizes search resolution and adds a before/at/after boundary regression. Hosted CI is checked separately on the follow-up commit; a local pass is not a claim of live connectivity.

## Kronos, TradingView, MT5 and Telegram

| Component | What is established | What is still unverified |
|---|---|---|
| Dorus rule implementation | Source/code mapping, explicit assumptions and deterministic tests | P candle/endpoints, universal BS threshold/selection, several first-candle/revisit rules; zero complete Dorus fixtures |
| Kronos | Offline adapter/gating/calendar regressions; current forward-profile default is off | Trained-model inference and predictive benefit. This local snapshot lacks materialized model package/dependencies/cached weights and regression input. The attempt stopped locally; this is not a claim that the remote repo lacks model code. Claude's stored filter results were preserved, not independently reproduced with real weights. |
| TradingView | Cached data schema/cadence checks and six baseline replays | Fresh live connector retrieval, source-clock completeness and MT5 price alignment. No callable TradingView connector is exposed to this audit turn. Existing cache files are not proof of a current connection. |
| MT5 | Mocked API tests cover UTC handling, terminal discovery/login, native timeframe requests and M1 | Actual Windows terminal login, broker candle clocks/contract specs and operational uptime |
| Telegram | Offline formatting/retry tests and notification-only isolation | Actual authorized destination delivery; no message was sent in this audit |
| News | CSV parsers/window logic; local-calendar backtests; approval-time gate | Live feed fetching, full event coverage, freshness and importance consistency across providers |

## Material limits before live reliance

1. Native candle open/close provenance must be verified on the actual broker. Shifted monthly labels need explicit period metadata; do not infer it from a fixed UTC anchor. Partial first resampling buckets/missing constituents are still not fully quarantined. Input normalization can repair/drop bad rows, so raw-file audits remain necessary.
2. Current OHLC is treated as a midpoint with constant configured spread. No commission, swap, latency, liquidity/slippage beyond opening gaps or variable MT5 bid/ask history is modeled. SL/TP exit timestamps label the processed candle opening, not a known intrabar fill instant.
3. The small M15 sample cannot validate 1m/5m confirmation branches. A timestamped MT5 replay with broker specs and a held-out period is still needed; no profitable result is inferred from the unit tests or this sample.
4. Prop loss guards update on entry checks; this run is not proof of continuous intrabar account-risk enforcement. It also does not test a single shared account across instruments.
5. Missing/failed news refresh can leave an empty/stale calendar without a coverage gate. That cannot establish absence of news. The default 30-minute window is an engineering choice; G only names a specific one-minute-before-news exclusion.
6. End-to-end evidence must still show an MT5 closed candle becoming a correctly timed signal and reaching the intended Telegram chat in notification-only mode. Actual trade execution is outside this audit; no orders, stop changes or external notifications were issued.

## Reproduce

From the repository root, with its test dependencies installed:

```sh
python -m pytest tests/trader -q -m 'not slow'
PYTHONPATH=. python docs/backtests/verification_2026-10-01/replay.py --label corrected --profile audited
PYTHONPATH=. python docs/backtests/verification_2026-10-01/replay.py --label corrected_news --profile audited --calendar data/calendar/high_impact.csv
PYTHONPATH=. python docs/backtests/verification_2026-10-01/replay.py --label forward --profile forward --calendar data/calendar/high_impact.csv
```

The script performs offline cache replays only. Per-run JSON records data/CSV hashes, timeframes, account assumptions and whether the calendar is enabled. Original baseline reproduction was run separately against the pinned 6ccfd06 snapshot, without news or Kronos. The audit does not select optimized settings from these results.
