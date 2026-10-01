# Partial-fill handling and readiness — 1 October 2026

This follow-up builds on PR #6 at `400f30b4889fdf817fe041a8b37c8faaa98394f5`. That revision passed hosted CI with **103 passed, 1 skipped and 1 deselected**. The earlier [execution review](EXECUTION_VERIFICATION_2026-10-01.md) records how the partial-cancellation defect was reproduced.

This is a separate IBKR adapter correction. Max's active [MT5/Telegram notification route](MT5_TELEGRAM_READINESS.md) does not depend on IBKR integration.

## Intended behavior

The adapter must retain evidence of a partial fill when the remaining order is cancelled. Requested size and observed filled size are separate. A partial fill enters `attention` state with protection explicitly unverified; it is not a claim that the original stop and target are active for the actual quantity.

The patch preserves owned parent and child references, remembers the highest observed cumulative fill, adjusts displayed lots and estimated risk to the observed fill, and stops new entries through the same broker instance. It does not cancel, resize, replace, or automatically close the uncertain protective orders. Automatic stop changes and close requests for an attention position are rejected before mutation.

An account holding without attributable fill metadata is reported as **unverified exposure**, not assigned to the parent and not represented as a confirmed zero position. Later incomplete snapshots do not erase a previously observed fill. The attention state remains set even if the parent subsequently fills completely: that alone does not verify protective-order state.

The live loop emits an explicit attention alert, retains the tracked position, removes it from ordinary pending-fill notifications, and skips automatic break-even management. Alerts update when the observed exposure/status changes. A failed notification is retried on the next observation rather than permanently suppressed by deduplication.

## Why cancellation is not sufficient

[IBKR's current status documentation](https://www.interactivebrokers.com/docs/tws-api/doc/order-management/order-status/understanding-order-status-message) distinguishes a pending cancellation, during which executions may still arrive, from cancellation of the remaining balance. [Its order-placement guidance](https://www.interactivebrokers.com/docs/tws-api/doc/orders/place-order/order-placement-considerations) calls for monitoring errors, status, open-order and execution callbacks together. [Execution metadata](https://www.interactivebrokers.com/docs/tws-api/doc/order-management/execution-details/the-execution-object) includes account and order identity; cumulative order exposure cannot safely be reconstructed by assigning account-wide net holdings to each parent.

The chosen attention policy is an engineering safeguard, not a Dorus strategy rule or a verified IBKR recovery procedure.

## Validation

The full offline suite passes **141 tests**, with one source-fixture skip and one deselected model-weights test. All **24 IBKR adapter tests** pass, alongside live attention-alert and entry-halt regressions. Cases include pending/terminal partial fills, stale fill snapshots, unattributable exposure and failed alert delivery. An independent fake-broker check retained a 25,000-unit fill from a 100,000-unit request, left the original three order submissions untouched and rejected further mutation of the attention position.

See the [machine-readable validation record](examples/research/mt5_telegram_validation_2026-10-01.json). All broker and notification checks in this change use test doubles; no real session or order is involved. Hosted CI for the published revision is tracked in [PR #6](https://github.com/aithergrowth/Kronos/pull/6).

## Remaining limits

- The entry halt is **in memory on one broker instance**. It is not a durable, account-wide lock across process restarts or separate adapters. Restart is not a supported way to clear uncertain exposure.
- Automated recovery still requires durable order/execution identity, reconciliation across reconnects, execution corrections and broker-confirmed protection for the remaining position. A conservative cumulative-fill record is not a complete execution ledger.
- The change cannot assert the broker actually has a working stop or target. Real TWS paper integration remains necessary before claiming reliable autonomous execution.
- Complete source-grounded Dorus chart fixtures remain absent. Unit tests and CI results do not verify that the strategy matches his chart decisions or establish trading performance.

The historical [defect reproduction](examples/research/ibkr_partial_cancel_repro.py) intentionally asserts the old behavior; use it against its recorded baseline. The current regression tests in `tests/trader/test_ibkr.py`, `test_live.py` and `test_exits_and_broker.py` verify the new behavior.
