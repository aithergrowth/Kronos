# Runtime and readiness review — 2026-10-01

> **Historical snapshot at `375c16b`.** Claude subsequently changed the runtime at `40ae003` and added CI at `445cd25`. See [the independent execution verification](EXECUTION_VERIFICATION_2026-10-01.md) for current test results and remaining defects. The original findings below are retained as the audit trail.

Pinned branch: `feature/kronos-trader` at [`375c16bda89ce74cef824062308dcf7f61a4cdd4`](https://github.com/aithergrowth/Kronos/commit/375c16bda89ce74cef824062308dcf7f61a4cdd4).

This is a read-only source and repository-evidence review. The findings below were **identified by code inspection, not reproduced by running the system**. No tests, broker calls, orders, deployments, settings changes, or secret reads were performed. These are review items for Claude. Candle-file content validation is a separate audit.

## Current integration and evidence status

- [PR #4](https://github.com/aithergrowth/Kronos/pull/4) is merged into `feature/kronos-trader` (merge commit `a4a8af632f45c33d8e8ef61b1215c5f9e037fdea`). The pinned HEAD is four commits ahead of the PR's final correction commit `049870bf089f1701ce4947d9e0bebadd086e676e`, with zero commits behind. The research changes are included.
- New real candle caches and IBKR equity/price-fallback changes exist at HEAD. Data delivery does not establish tested order execution or strategy fidelity.
- GitHub API checks at this HEAD returned **zero Actions runs, zero check runs, and an empty combined-status list**. The recursive repository tree contains no `.github/workflows` directory. No automated CI result was observed; this does not mean the tests failed. Historical test-count statements in documentation are not a test run for this HEAD.
- There are **no loaded source-grounded chart fixtures**: the top level of `docs/examples/` contains only its README, the template YAML, and `research/`. [The loader scans only top-level YAML and requires same-name CSV](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/examples.py#L57); [the real-example test skips when that list is empty](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/tests/trader/test_examples.py#L6). Cache CSVs and research records do not load automatically. The separate synthetic-loader test is not source validation.
- The only committed trader backtest report found is [the Phase 0 Alibaba stock report](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/docs/backtests/phase0_09988.md#L3). It explicitly says it is not a strategy verdict and had no Dorus-example calibration. Its three overlapping historical runs report **11, 6, and 10 trades**, with **−4.7R, −5.9R, and −0.9R** respectively ([table](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/docs/backtests/phase0_09988.md#L15)). These are stored report claims, not rerun results or 27 independent trades.
- **No 100-trade forward-paper result or trade journal was found in the inspected repository.** No such result can be inferred from connected accounts, unit tests, prediction-output JSON, or historical backtests. This does not rule out uncommitted desktop evidence. [The documented forward gates](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/docs/CHECKLIST.md#L40) remain unchecked: 2–4 weeks of alerts and one month of approved IBKR paper execution.
- [LIVE_SETUP.md](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/docs/LIVE_SETUP.md#L33) explicitly says the adapter's fake-API coverage still needs a real TWS session. [IBKR tests use a fake API with immediate market fills](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/tests/trader/test_ibkr.py#L1). Connected-session status and completed end-to-end execution were not independently verified.

## Concrete code review items

### 1. Late approval is processed before expiration

[LiveRunner.process_decisions, lines 208–222](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L208) removes a queued decision from `pending` and calls `execute` before checking expiration. The later expiration loop only checks requests still in the dictionary. Thus, an approved response first processed after its deadline can reach execution if other guards pass.

Suggested verification: queue an approval at or after `expires_at` and assert no order is submitted. [The existing expiry test](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/tests/trader/test_live.py#L80) covers expiration without a simultaneous queued approval.

### 2. Cached feed fallback has no freshness or feed-consistency gate

[build_fetch, lines 68–82](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L68) loads cached TradingView series, overwrites successful timeframes with broker bars, and keeps cached timeframes when the broker fails. It logs the fallback but performs no maximum-age or provider-consistency check. A returned view can therefore combine IBKR bars with cached OANDA/FOREXCOM bars, potentially stale. This is a code path, not proof it happened in the user's live session.

Suggested verification: fail one broker timeframe with an old cache and require an explicit reject/degraded-analysis policy, plus recorded provider and candle anchoring.

### 3. Failure to obtain a current price falls back to the old setup entry

[LiveRunner.execute, lines 180–197](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L180) catches any `current_price` exception and uses `setup.entry` for the execution R:R check and order call. This can allow execution despite being unable to verify a current price. Separately, [IBKR's minute-bar fallback](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/execution/ibkr.py#L224) accepts the last positive close without testing its timestamp.

Suggested verification: current-price failure and stale fallback bars must have explicit tested behavior; a historical setup price must not be represented as a verified current quote.

### 4. The built-in live paper loop does not advance its simulated broker

[cmd_live, lines 203–225](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/cli.py#L203) builds a cache fetch and LiveRunner for `--broker paper`. [LiveRunner.step](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L122) fetches/analyzes/manages positions, but the live module never calls PaperBroker's `set_price` or `on_candle`. [PaperBroker.on_candle](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/execution/paper.py#L110) is what processes simulated stops, targets, and equity updates. [The live test manually invokes it](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/tests/trader/test_live.py#L74) to generate a close.

As written, the standalone built-in paper live path does not itself produce candle-driven SL/TP outcomes. This is separate from the historical backtester, which does call `on_candle`, and from IBKR's external paper engine.

Suggested verification: drive each newly closed candle through the built-in paper broker exactly once, then demonstrate entry, stop/target, equity, and close-report behavior across repeated polls.

### 5. IBKR submissions can be reported as filled without confirmation

[IBKRBroker.place_market_order, lines 249–269](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/execution/ibkr.py#L249) submits the bracket, waits a fixed period, and if `avgFillPrice` is zero substitutes the provided/current quote. It then stores and returns a Position without requiring a Filled status or filled quantity. [LiveRunner subsequently announces “filled”](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L199).

Suggested verification: pending, rejected, partial, and delayed-fill cases must remain distinguishable from a confirmed fill and retain explicit bracket/reconciliation state.

## Protection already present

The live analysis does have a closed-bar filter: [LiveRunner passes `now`](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/live.py#L122), [StrategyEngine uses `closed_as_of(now)`](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/strategy/engine.py#L117), and [CandleSeries computes a timeframe-duration cutoff](https://github.com/aithergrowth/Kronos/blob/375c16bda89ce74cef824062308dcf7f61a4cdd4/kronos_trader/core/candles.py#L178). This filters forming bars for analysis; it does not validate provider matching, timestamp anchoring, or freshness.

## Most useful next step

Claude should reproduce and repair the five execution-path review items with offline fake-broker regression tests, run the full current suite with reported skip counts, and establish CI for the exact revision. In parallel, promote actual source-observed expectations into loadable chart fixtures using the audited candle files. After those checks, record a reproducible dry-run and forward-paper journal; distinguish synthetic tests, historical simulations, and actual paper-session evidence in readiness claims.

