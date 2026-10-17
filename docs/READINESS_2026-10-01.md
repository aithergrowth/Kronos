# Dorus/Kronos readiness — 1 October 2026

**Ready to continue source calibration and historical testing. Not yet demonstrated ready for reliable autonomous paper execution or a prop-firm challenge.**

Reviewed code/data revision: [`375c16b`](https://github.com/aithergrowth/Kronos/commit/375c16bda89ce74cef824062308dcf7f61a4cdd4). Research PR #4 is merged. This update changes research documentation and delivery metadata only.

## What is available now

| Area | Verified result | Remaining limit |
|---|---|---|
| Repository handoff | Research updates are merged; Claude's newer candle delivery is present. | Documentation and unit-test counts alone are not evidence of correct execution. |
| Candle data | Seven repository CSVs, **13,599 rows**, independently checked against their Git blob hashes. Required columns, increasing unique timestamps, finite prices/volume, OHLC bounds and nonnegative volume pass. | Six requested timeframes are supplied. Gold's August entry request is **1m**, but its substitute is **15m**. That request remains incomplete. |
| Chart/data match | K5's 30 January 2026 INDEX:BTCUSD daily OHLC matches all four screenshot values exactly. | This validates one selected candle, not trade annotations or every provider/time alignment. |
| Requested date windows | Every delivered series spans its selected date envelope and has at least 60 rows before the window. | A before-window count is not 60 candles before an identified sweep. Market-calendar continuity and the source sweep/break/return have not been validated. |
| New Dorus evidence | Source G, *De Kracht van HTF Context in LTF Trades* (20 August 2025), adds **375 reviewed Dutch caption segments**. At 10:49–10:55 the first bullish candle follows a shift in the gold example. | This is not proof of candle-only confirmation, exact market/limit order timing, or a universal P/BS boundary. Audio and chart frames remain unverified. |
| Source regression tests | The fixture loader and test exist. | **Zero complete loadable Dorus chart fixtures.** The real-example test skips when no examples load. |
| Broker/paper workflow | IBKR, built-in paper, Telegram approval and live-loop code exist; analysis filters forming candles. | Five execution-path review items need reproduction and correction; no end-to-end execution result was verified here. |
| Performance | A committed historical Phase 0 report exists. | Its three overlapping stock-data simulations report negative R; they are neither calibrated Dorus results nor forward-paper evidence. No committed 100-trade forward-paper journal was found. |

## Essential is sufficient for the MCP route

TradingView's [official MCP documentation](https://www.tradingview.com/mcp/docs), checked 1 October 2026, includes access with **Essential and higher paid plans**, excluding trials. The [launch announcement](https://www.tradingview.com/blog/en/tradingview-mcp-server-public-beta-60864/) states the same. This is distinct from the website's native **Download chart data** feature, whose [plan comparison](https://www.tradingview.com/pricing/?source=header_goass%3D) starts at Plus.

The project already received MCP-derived CSVs through Claude. No upgrade is needed merely to use the plan-eligible MCP route. This Astra session exposes no TradingView data tool, and a plugin-directory search returned no TradingView result; that does not establish that the user's account or other clients are disconnected. Existing GitHub access lets Astra audit the delivered files. A broad plugin inventory is not a readiness test.

## Execution review items for Claude

These are **static code-review findings, not reproduced runtime failures**. See the [pinned runtime audit](RUNTIME_READINESS_REVIEW.md) for exact source links and verification cases:

1. Process an approval's expiry before accepting a queued approval.
2. Define and test freshness/provider consistency when broker history falls back to cached data.
3. Do not represent the old setup entry as a verified current quote when pricing fails.
4. Drive the built-in live paper broker with each new closed candle so simulated SL/TP outcomes advance.
5. Distinguish submitted, pending, rejected, partial and confirmed IBKR fills; do not report a quote fallback as a confirmed execution.

No GitHub Actions runs, check runs or commit status results were observed for the reviewed revision; no workflows were present. This is absence of observed CI evidence, not a claim that tests failed. Local desktop results may exist outside the inspected repository.

## Concrete next sequence

1. Reproduce the execution findings with offline broker doubles, repair them, and record the current test results and skipped tests for the exact revision.
2. Use the six exact-timeframe datasets to finish source annotation work. Keep student critiques separate from Dorus trades; do not fill missing P/BS, entry or target labels from an algorithm's own predictions. Obtain the gold 1m source through an authorized historical source if needed; 15m OHLC cannot recover those candles.
3. Promote at least five chart-grounded examples to the loader's CSV/YAML format, including the requested POI coverage and rejected setup. Run the source comparison tests and inspect discrepancies.
4. Run reproducible, cost-aware historical tests on the intended instruments with a held-out period, then record forward-paper execution and its full journal. Do not count synthetic tests, overlapping backtests or model forecasts as paper trades.
5. Before a challenge, apply the selected firm's current account rules and broker specifications, and assess the recorded drawdown, expectancy, costs and rule adherence. No readiness or profitability claim is established by this report.

## Evidence files

- [Machine-readable candle audit](examples/research/candle_validation_2026-10-01.json)
- [Updated retrieval manifest](examples/research/retrieval_requests.yaml)
- [Claude's delivery index](examples/research/CANDLES_DELIVERED.md)
- [Source G review](DORUS_HTF_CONTEXT.md)
- [Runtime audit](RUNTIME_READINESS_REVIEW.md)
- [Shared questions and decisions](ASTRA_TASKS.md)
