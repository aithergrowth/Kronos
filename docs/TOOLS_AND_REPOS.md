# Tools and repositories that address Kronos's remaining gaps

Research checked 1 October 2026. These are integration proposals, not claims that the tools have been installed, connected, tested against Kronos, or that they validate Dorus's rules. Primary sources only. Existing readiness documents were used to identify gaps; the main review must recheck those gaps against current repository HEAD.

| Candidate | Specific purpose | Decision |
|---|---|---|
| Hypothesis | Exercise approval/order/exit event sequences and timestamp boundaries against the existing implementation. | **Now**, as an offline development dependency after ordinary regression cases. |
| Shopify Toxiproxy | Test what the IBKR paper adapter does when its TCP connection delays or drops around order submission. | **Later**, during an isolated paper integration test. |
| Official TradingView MCP | Continue retrieving and archiving exact named feeds already used for the chart research. | **Reuse now** where exposed; it does not resolve all old 1-minute history. |

## 1. Hypothesis: meaningful generated execution tests

[Repository](https://github.com/HypothesisWorks/hypothesis) · [Stateful testing documentation](https://hypothesis.readthedocs.io/en/latest/stateful.html) · [Releases](https://github.com/HypothesisWorks/hypothesis/releases) · [License](https://github.com/HypothesisWorks/hypothesis/blob/master/LICENSE.txt)

The official documentation describes generated sequences of rules and invariants checked after each step. The current release page lists 6.168.3, released 28 September; recent releases also address datetime edge cases. The repository license is MPL 2.0 except where explicitly noted.

**Proposed Kronos use:** wrap the existing fake broker and controllable clock. Generate time advances, approvals, duplicate approvals, repeated candle polls, submission failures, delayed fills, partial fills and reconnect observations. Assert independent execution requirements: an expired approval submits nothing; one decision cannot submit twice; a fill is never announced before observed filled quantity; processing the same candle twice does not apply P&L twice. Persist minimal failing cases as ordinary regression tests. Begin with whichever current review findings remain reproducible.

**Limitations:** a model test can reproduce the same mistaken assumption as the production code. It cannot establish Dorus's P/BS definition, prove profitability, or replace source-grounded chart examples and real paper-session evidence. Prefer simple parameterized tests for each known defect before adding a state machine. No runtime trading dependency or new strategy engine is needed.

## 2. Toxiproxy: network failure testing around submissions

[Official repository and documentation](https://github.com/Shopify/toxiproxy) · [Releases](https://github.com/Shopify/toxiproxy/releases) · [License](https://github.com/Shopify/toxiproxy/blob/main/LICENSE)

The project supplies a TCP proxy controlled through HTTP, with latency, timeout and connection-reset controls. The repository identifies an MIT license. The latest release shown in the official release list is **2.12.0, 18 March 2025**, confirmed by asset timestamps. The documentation remains available, but this review could not verify recent commit activity; do not describe it as newly released or infer maintenance from popularity.

**Proposed Kronos use:** put the test-only connection between the adapter and an isolated TWS/IB Gateway paper session. Drop the downstream connection after submission, reconnect, and verify that the application reconciles open orders/executions before retrying; no duplicate order or fabricated fill should result. Also test loss of quotes while an approval is pending. First run deterministic fake-broker cases locally.

**Limitations:** this injects transport failures; it is not a broker simulator, order reconciliation implementation or market-fill model. It cannot deterministically create every broker rejection/partial-fill case. It adds a service and routing configuration, so defer it until the adapter's ordinary lifecycle tests pass. No live-account network changes are proposed.

## 3. Reuse the official TradingView MCP within its actual limits

[Official MCP documentation](https://www.tradingview.com/mcp/docs) · [Official chart-history limits](https://www.tradingview.com/support/solutions/43000480679-historical-intraday-data-bars-and-limits-explained/)

The official, currently documented beta service uses OAuth and includes paid Essential and higher plans, excluding trials. Its `get_ohlcv` schema accepts `symbol`, `interval`, `count` and `summary`; it returns Unix-second UTC bar timestamps, with a maximum **5,000 bars**. The published OHLCV schema shows **no date-from/date-to or pagination cursor**. It is a proprietary hosted service, not an open-source repository; no OSS license is asserted.

**Proposed Kronos use:** keep exact identifiers such as `FOREXCOM:XAUUSD` and `INDEX:BTCUSD`, preserve the raw response and retrieval metadata, and validate the returned first/last timestamp against each request before calling it fulfilled. Continue archiving new bars on the existing authorized route so recent low-timeframe windows are not lost. The current Astra tool registry does not expose TradingView operations; Claude's prior authorized MCP deliveries are present in the repository. Account eligibility and connector availability are separate.

**Limits that matter now:** 5,000 one-minute bars do not establish arbitrary August coverage in October. Essential's separate chart-history limit of 10,000 intraday bars is not the MCP request limit. A larger timeframe cannot reconstruct missing one-minute candles. A different broker's XAUUSD feed cannot be labelled exact FOREXCOM evidence. No new connection or plan upgrade is justified solely by this research.

## Integration priority

The most useful small addition is Hypothesis after the current deterministic regressions, with exact commit test results in CI. Retain the existing Dorus strategy/backtester, broker adapters and approval flow. Toxiproxy is a later verification tool. None of these tools supplies missing chart annotations or transforms the existing zero-complete-fixture state into validated Dorus examples.
