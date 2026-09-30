# Roadmap - from rule set to funded account

Each phase has an exit criterion. We do not move on before it is met.

## Phase 0 - Foundation (done 2026-09-30)

- Package `kronos_trader/` with the rules as code, tests, CLI, docs.
- Kronos indicator wrapper, TradingView MCP adapter, Telegram, paper broker,
  MT5 adapter skeleton, backtester.
- Exit: `python -m pytest` green; a backtest runs end to end. ✅

## Phase 1 - Definitions locked (next)

- Answer the open questions in `docs/ASTRA_TASKS.md` section A.
- Encode Dorus's chart examples as regression tests (B1).
- Adjust detectors until every example test passes.
- Exit: examples pass; no `ASSUMPTION` left unanswered in `docs/STRATEGY.md`.

## Phase 2 - Data and forex backtests

- Cache TradingView history for the chosen pairs (all timeframes, 5,000 bars each; Claude pulls via the MCP, see `docs/TRADINGVIEW_BRIDGE.md`).
- Run `backtest` per pair; produce `docs/backtests/<pair>.md` with the trade list.
- A/B: confirmation types, TP policy, Kronos `off` vs `advisory` vs `filter`.
- Exit: expectancy > 0 over ≥ 2 years on ≥ 3 pairs after spread, with max drawdown inside the prop-firm limits.

## Phase 3 - Kronos value test

- Run the model on the desktop (GPU optional; Kronos-small is fine on CPU).
- Measure: does agreement between Kronos and the setup direction improve win rate / R? Choose the mode from data, not opinion.
- Exit: documented decision for `kronos.mode` and `horizon`.

## Phase 4 - Live dry-run

- `LiveRunner` on the desktop, `dry_run=True`: signals to Telegram, no orders.
- Run for 2–4 weeks; compare every alert with what Dorus's rules say manually.
- Exit: zero rule violations in alerts; no crashes; latency under one candle.

## Phase 5 - Demo account

- MT5 demo with the prop firm's broker; `dry_run=False`.
- Guard rails live: 1 % risk, 1 trade, daily-loss / drawdown stops.
- Exit: one month without a guard breach; realised results match the backtest distribution.

## Phase 6 - Prop firm challenge

- Same code, funded challenge account. Start small (rule: "start small").
- Weekly review of the decision log; no parameter changes mid-challenge.
