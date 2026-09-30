# Master checklist - from today to a funded account

Owner codes: **M** = Max · **C** = Claude · **A** = Astra (ChatGPT / Dot). Tick items in this file; it is the single list all three of us work from.

## 0. Foundation (done 2026-09-30)

- [x] C - Rule set as code, 67 tests, CLI, docs (`kronos_trader/`, PR #1)
- [x] C - TradingView MCP verified live (bars, quotes, news, calendar); EURUSD sample cached
- [x] C - Kronos indicator wrapper (advisory / filter)
- [x] C - Paper broker, IBKR adapter (fake-API tested), MT5 skeleton, risk guard
- [x] C - Telegram notifier with Approve / Skip, live loop, backtester

## 1. Definitions locked (this week - nothing else matters more)

- [ ] M+A - Answer Q1–Q12 in `docs/ASTRA_TASKS.md` (balance, sweep-without-break, opposing votes, scalp rules, first-candle, TP choice, buffer, break-even numbers, entry style, sessions, prop firm, instruments)
- [ ] M+A - 5–10 annotated chart examples from Dorus's material as CSV + notes (`docs/examples/`)
- [ ] M - Confirm the instrument list and each broker's pip value / lot step / spread (B3)
- [ ] M - Choose the prop firm and write its rulebook as numbers (B2)
- [ ] C - Encode the examples as regression tests; adjust detectors until they pass
- [ ] C - Close every `ASSUMPTION` in `docs/STRATEGY.md` with the answers

## 2. Data and forex backtests

- [ ] C - Pull TradingView history for each instrument (1M/1W/1D/4H/1H/15m/5m, up to 5,000 bars each) into `data/tv_cache/`
- [ ] C - Backtest per instrument; write `docs/backtests/<symbol>.md`
- [ ] C - A/B: first-candle on/off, TP policy, Kronos off/advisory/filter
- [ ] A - Review the trade lists and flag trades Dorus would not take (B5)
- [ ] Exit: expectancy > 0 over ≥ 2 years on ≥ 3 instruments after spread, drawdown inside prop-firm limits

## 3. Kronos value test

- [ ] M - Run the model once on the desktop (`python -m kronos_trader forecast ...`, weights download automatically) or allow `huggingface.co` in the cloud environment
- [ ] C - Measure whether Kronos agreement improves win rate / R; decide `kronos.mode` and `horizon` from data

## 4. Live dry-run (Telegram only)

- [ ] M - Desktop: pull the branch, `pip install -r kronos_trader/requirements.txt`, `python -m pytest`
- [ ] M - Telegram bot via BotFather; `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`; `python -m kronos_trader telegram-test`
- [ ] M - IBKR paper: enable the API in TWS (port 7497); `python -m kronos_trader ibkr-test --symbol EURUSD`
- [ ] M - A machine that never sleeps (desktop with sleep off, or a small VPS) with a restart-on-crash service
- [ ] M - Start `python -m kronos_trader live --symbol EURUSD --broker ibkr --data-dir data/tv_cache` and leave it running
- [ ] C - Fix whatever the real TWS session disagrees with in the adapter
- [ ] C - Refresh the higher-timeframe cache daily through the MCP
- [ ] Exit: 2–4 weeks, zero rule violations in alerts, no crashes, latency under one candle

## 5. IBKR paper execution with the Approve step

- [ ] M - Same command with `--execute`; tap Approve / Skip in Telegram
- [ ] Exit: one month without a guard breach; realised results match the backtest distribution

## 5b. Prop-firm demo

- [ ] M - Demo account at the chosen firm; platform credentials in env vars
- [ ] C - Adapter for the firm's platform if it is not MT5 (cTrader / MatchTrader)
- [ ] Exit: the demo mirrors the IBKR paper results

## 6. Challenge

- [ ] M - Funded challenge, small size, Approve step on
- [ ] M+C - Weekly review of the decision log; no parameter changes mid-challenge

## Instruments

| Market | Status | Notes |
|---|---|---|
| Forex majors | ready | specs in `config.py`; verify pip values with the broker |
| Gold (XAUUSD) | ready | pip 0.1, 1 lot = 100 oz; IBKR via CFD |
| BTC | ready with a caveat | 24/7 market: weekend handling to be added before live; wide spreads; check the prop firm's crypto rules |
| Indices (NAS100, US30) | ready | CFD specs to verify |
| Options | not now | the rules are written in price of the underlying (POI, sweep, SL/TP, 1:3); option premium, expiry and greeks break the risk maths; prop firms rarely allow them |
