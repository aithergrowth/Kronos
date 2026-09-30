# Shared workboard - Claude ⇄ Max ⇄ ChatGPT Astra 6

This file is the meeting point for the three of us. Keep it on the desktop
(it lives in the repo at `docs/ASTRA_TASKS.md`), let Astra write answers and
deliverables straight into it, commit, and Claude picks it up in the next
session. One rule: **answers replace the `> answer:` lines, nothing gets
deleted** - the decision log at the bottom is our memory.

Status legend: `[ ]` open · `[~]` in progress · `[x]` done

---

## A. Questions Claude needs answered (strategy definitions)

The code runs today with the interpretations listed in `docs/STRATEGY.md`
section 3. These questions decide whether those interpretations are right.
Short answers are fine; a chart screenshot description or a worked example is
even better.

- [ ] **Q1 - Balance.** How does Dorus define *balance* on a timeframe? Is it the order block of the last break (what the code does), the equilibrium of the current range (premium/discount), or something else?
  > answer:
- [ ] **Q2 - Sweep without break.** A timeframe swept sell-side liquidity but has not broken structure yet. Bullish, or still 50/50?
  > answer:
- [ ] **Q3 - Opposing votes.** 1M+1W+1D bullish, 4H+1H bearish. Trade the bullish bias, or wait?
  > answer:
- [ ] **Q4 - Scalp only.** With only 1D+4H+1H aligned: which POI timeframes may be used, which confirmation timeframes, and is management different (break-even, session)?
  > answer:
- [ ] **Q5 - First candle confirmation.** When is "first bullish/bearish candle" an acceptable confirmation instead of a BOS/BMS body close?
  > answer:
- [ ] **Q6 - TP choice.** Liquidity line vs. unmitigated balance block when both exist: nearest, or always liquidity?
  > answer:
- [ ] **Q7 - The 1-pip buffer.** Extra stop distance, sizing only, or both?
  > answer:
- [ ] **Q8 - Break-even 4R vs TP 3R.** Confirm the numbers (intraday BE after 4R, swing BE after 2R, TP ≥ 3R).
  > answer:
- [ ] **Q9 - Entry style.** Market on the confirmation close, or a limit back at the break level?
  > answer:
- [ ] **Q10 - Sessions and candle anchoring.** Trade only London/New York? Broker day start (22:00 UTC?) for 4H/daily candles?
  > answer:
- [ ] **Q11 - Prop firm.** Which firm, account size, daily loss %, max drawdown %, min trading days, news and weekend rules?
  > answer:
- [ ] **Q12 - Instruments.** Which pairs / indices / metals, and the broker's pip value, lot step and spread for each?
  > answer:

## B. Deliverables Astra can build (drop the result path here)

- [ ] **B1 - Annotated examples.** 5–10 real chart examples from Dorus's material as CSV + a short note per example: which candle is the sweep, which is the BOS, where the POI is, where the SL/TP went. Claude turns each into a regression test (`tests/trader/`). Format: `docs/examples/<pair>_<date>.csv` (timestamp,open,high,low,close,volume) + `docs/examples/<pair>_<date>.md`.
  > path:
- [ ] **B2 - Prop-firm rulebook** as numbers (`config/propfirm.yaml`): daily loss, max drawdown (static/trailing), profit target, min days, allowed instruments, news rule, weekend rule, max lot.
  > path:
- [ ] **B3 - Symbol specs** for the chosen broker (`config/local.yaml` → `symbols:`): pip size, pip value per lot in account currency, lot step, min/max lot, typical spread, MT5 symbol name, TradingView symbol (`OANDA:EURUSD` style).
  > path:
- [ ] **B4 - Telegram bot.** Create the bot with @BotFather, get the chat id, and set `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` as environment variables on the desktop. Then run `python -m kronos_trader telegram-test`.
  > status:
- [ ] **B5 - Backtest review.** Read `docs/backtests/*.md` when they appear and mark trades that Dorus would *not* have taken, with the reason. This is how we calibrate the detectors.
  > notes:
- [ ] **B6 - News policy.** Which calendar events (per currency) block entries, and for how long before/after? Claude wires them into `prop_firm.news_blackout_minutes` and the TradingView economic calendar.
  > notes:
- [ ] **B7 - TradingView data pulls.** Astra can't call the MCP, but can list which symbols/timeframes to keep warm in the cache (`data/tv_cache/`). Claude pulls them in each session.
  > list:

## C. What Claude did / will do

- [x] C1 - Rule set codified with tests (`kronos_trader/strategy`, `tests/trader`) - 2026-09-30
- [x] C2 - Kronos forecast indicator wired (`kronos_trader/indicators`) - needs model weights on the desktop (Hugging Face is blocked from the cloud session)
- [x] C3 - TradingView MCP adapter + CSV cache, verified against the live server tools - 2026-09-30
- [x] C4 - Paper broker, prop-firm guard, MT5 adapter skeleton, Telegram notifier
- [x] C5 - Backtester + CLI + first runs on the bundled 6-year 5-minute dataset
- [ ] C6 - Turn B1 examples into regression tests
- [ ] C7 - Forex backtests on real TradingView history (needs cached bars, see `docs/TRADINGVIEW_BRIDGE.md`)
- [ ] C8 - Live dry-run loop on the desktop with Telegram (Phase 4 in `docs/ROADMAP.md`)

## D. Decision log

| Date | Decision | By |
|---|---|---|
| 2026-09-30 | Confirmation defaults to BOS/BMS body close; first-candle confirmations are a switch (`--first-candle`) until Q5 is answered. | Claude |
| 2026-09-30 | Kronos runs in *advisory* mode by default; `filter` mode exists for A/B backtests. | Claude |
| 2026-09-30 | TP policy defaults to *nearest* valid target until Q6 is answered. | Claude |
| 2026-09-30 | Guards default to 4 % daily loss / 8 % drawdown until Q11 gives the real numbers. | Claude |
