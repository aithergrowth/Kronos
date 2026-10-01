# Independent execution verification — 1 October 2026

**103 offline tests pass after two execution guards, a workflow syntax correction and a CSV timestamp compatibility fix. A reproduced IBKR partial-fill cancellation defect and missing Dorus chart fixtures still prevent a readiness claim.**

Base: [`445cd256b599ec9a0a1722b2049699b1ad923095`](https://github.com/aithergrowth/Kronos/commit/445cd256b599ec9a0a1722b2049699b1ad923095), on `feature/kronos-trader`. Claude's runtime update at `40ae003` and merged research PR #5 are preserved. An earlier local patch against `375c16b` was discarded when these concurrent changes arrived.

## What was run

The exact current source, tests and required historical dataset were fetched and checked against their Git blob hashes. The unmodified base passed **93 tests**, with **1 skipped and 1 deselected**. After the changes below, `python -m pytest -q -ra tests/trader` passed **101 tests**, with **1 skipped and 1 deselected**, in 6.40 seconds.

- The skip is `test_examples.py`: no annotated Dorus examples load.
- The project default deselects the slow test requiring real Kronos model weights. Forecast-model inference was not verified.
- Tests used fake brokers, the built-in paper simulator and a dry-run notifier. No live broker session, Telegram delivery or order was exercised.
- [Machine-readable results and changed-file hashes](examples/research/execution_validation_2026-10-01.json) record the local environment and scope. These are local results, not a GitHub-hosted result.

## Scoped fixes

| Finding on the latest base | Reproduction | Change |
|---|---|---|
| Approval remains valid while underlying candle data becomes stale | A request at 09:00 expires at 09:15. With unchanged 5m data and the configured two-bar age limit, approval at 09:11 still submitted an order. | `LiveRunner.execute()` rechecks the existing freshness policy before submission. |
| Executable quote need not be a finite positive number | Positive infinity reached the paper broker. `None` and nonnumeric text raised outside the quote handler. Other invalid numeric values were blocked indirectly. | Convert to float and require finite, positive price within the existing exception handler. |
| CI workflow is invalid YAML | [Run 36817444857](https://github.com/aithergrowth/Kronos/actions/runs/36817444857) failed with zero jobs. Local YAML parsing failed at line 16's unquoted colon. | Quote that step name; YAML now parses and install/test commands are unchanged. The workflow then started successfully; its first hosted test run exposed the separate pandas compatibility issue below. |

Eight new regression cases cover seven invalid quote values and the stale queued approval. Before the patch, all eight failed; that count includes explicit error-reporting assertions for values previously blocked indirectly. Afterward, all **20 live-loop tests** passed, followed by the full **101-test** result. Existing tests cover Claude's late-approval, missing-quote, paper progression and delayed-fill changes; those fixes were not overwritten.

## Hosted-CI follow-up: pandas timestamp compatibility

The first working [hosted run](https://github.com/aithergrowth/Kronos/actions/runs/36818281885) installed pandas **3.0.6** and NumPy **2.5.3** under Python **3.12.14**. It reported **98 passed, 1 failed, 2 errors, 1 skipped and 1 deselected**. All three failures came from applying NumPy's dtype test to pandas `StringDtype` timestamp columns. The prior local pass used pandas **2.2.3** / NumPy **2.3.5**.

The CSV loader now uses pandas' [numeric-dtype predicate](https://pandas.pydata.org/docs/reference/api/pandas.api.types.is_numeric_dtype.html) for both the single timestamp and split date/time paths. Two regression cases explicitly request extension-string columns, reproducing the failure even on pandas 2. They failed before the correction and pass afterward; numeric Unix timestamp handling remains covered by the existing test. The full local suite then passed **103 tests**, with the same one skip and one deselection. Dependency constraints were not weakened or narrowed to conceal the failure. The follow-up commit must still pass hosted CI.

## Reproduced remaining defect: partial fill followed by cancellation

Using the repository's fake IBKR API with `connect=False`, inject a EURUSD parent requesting 100,000 units, with 25,000 filled at 1.1002 and status `Cancelled`. The fake account continues to hold 25,000 units.

1. If this terminal state is seen before `place_market_order()` returns, the adapter raises "not accepted", issues cancellation requests for both protective children, and creates no tracked position.
2. If it occurs after a pending position was returned, `open_positions()` reconciliation cancels both children and deletes the tracked position/order records. It returns an empty list while the fake account still holds 25,000 units. No closed trade is recorded.

See the [portable reproduction](examples/research/ibkr_partial_cancel_repro.py) and [observed states](examples/research/ibkr_partial_cancel_observation.json). Run from the repository with `python docs/examples/research/ibkr_partial_cancel_repro.py`; a successful run **reproduces the defect**, rather than verifying safety. It uses test doubles only. Real TWS event ordering, execution reports and protective-order semantics were not exercised.

No partial-fill lifecycle fix is claimed in this change. The adapter needs explicit reconciliation of executed quantity and remaining holdings, with protection handled for the actual exposure, before its paper integration gate can be considered complete. Merely retaining a full-size pending bracket would not establish correctness.

## Research and tool handoff

The [new source H review](DORUS_ENTRY_METHODS.md) and [shared workboard](ASTRA_TASKS.md) add another complete available Dutch-caption review; unreadable charts and audio remain unverified. Complete source-grounded chart fixtures remain **zero**. The gold target/clock and exact P/BS boundary are still unresolved.

[Tools and repositories](TOOLS_AND_REPOS.md) evaluates Hypothesis for generated event-sequence tests, Toxiproxy for later isolated network-failure tests, and reuse of the existing TradingView data route. None was installed or newly connected by this review. More integrations do not resolve the demonstrated execution defect or missing source annotations.

The next concrete gates are the partial-fill lifecycle correction with regressions, a successful CI run, source-observed chart fixtures, and documented forward-paper execution. Offline test counts do not establish strategy profitability or prop-firm readiness.
