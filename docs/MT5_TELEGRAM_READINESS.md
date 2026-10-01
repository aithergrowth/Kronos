# MT5 candles and Telegram notifications — 1 October 2026

Max's active pipeline is **MetaTrader 5 candles → strategy scan → optional Kronos forecast → Telegram notification**. IBKR is not required for this route.

## What is implemented and checked

- MT5 Python API epochs are preserved as UTC by default. A stale tick cannot create a guessed timezone offset. Native 4H and daily bar openings are preserved rather than moved to a midnight-UTC grid. This follows [MetaQuotes' UTC documentation](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesfrom_py).
- Default feed requests include 1m through monthly candles, including the 1m confirmation input for an hourly POI. Available history still depends on the terminal and broker.
- Without `--execute`, the runner has no execution broker. It does not place orders, change existing stops, advance paper positions or poll Telegram approval commands. The MT5 adapter supplies candles only.
- A failed setup notification remains eligible for retry on a later scan. A successful send is deduplicated within the running process. If both a scan and its error notification fail, the loop continues at the next poll.
- The offline trader suite passes **141 tests**, with one skipped source-fixture test and one deselected model-weights test. The MT5 module contributes 13 tests; CLI isolation and live-loop regressions cover the notification path. Details: [validation record](examples/research/mt5_telegram_validation_2026-10-01.json).

These checks use fake terminals and notifiers. No running MT5 terminal, real Telegram delivery or broker order was tested in this environment. Hosted CI status for the published revision is recorded in [PR #6](https://github.com/aithergrowth/Kronos/pull/6).

## Verify on the Windows machine running MT5

Use the existing logged-in terminal and local environment configuration. Keep credentials out of repository files and shared command output. Install the dependencies listed in `requirements-trader.txt`; the MetaTrader5 package is needed on the terminal's Windows host.

1. Read the last five bars and connection diagnostics:

   ```powershell
   python -m kronos_trader mt5-test --symbol EURUSD --tf 15m
   ```

   Check that the symbol resolves to the intended broker instrument, the configured timestamp correction is normally zero, and the latest bars are plausible for the market session. Broker suffixes belong in the symbol specification's `mt5_symbol`. `MT5_SERVER_OFFSET_HOURS` is an explicit compatibility override, not a broker-clock setting to guess from the displayed terminal clock.

2. Send an intentional delivery test to the configured Telegram destination:

   ```powershell
   python -m kronos_trader telegram-test
   ```

   With configured credentials this sends a real message. Without them the notifier prints locally; local printing does not verify Telegram delivery.

3. Scan once using MT5 candles and notifications only:

   ```powershell
   python -m kronos_trader live --symbol EURUSD --broker mt5 --feed broker --once
   ```

   A valid setup is needed for a setup alert. A quiet scan alone does not demonstrate a failed connection. Review the reported feed/freshness diagnostics.

4. Run continued monitoring:

   ```powershell
   python -m kronos_trader live --symbol EURUSD --broker mt5 --feed broker
   ```

   Omit `--execute` for this notification route. The optional execution mode and its approval buttons have separate integration requirements.

## What remains unverified

- Actual terminal connectivity, symbol mapping, sufficient history and Telegram delivery on Max's machine.
- Alert behavior over real market sessions. Deduplication and retry state are in memory: restart can repeat alerts, and a failed alert is retried only if the setup remains eligible on another scan. This is not a persistent delivery queue.
- End-to-end Kronos model loading and forecast behavior in this environment; the slow model-weights test was not run in this validation.
- Dorus fidelity: complete source-grounded chart fixtures remain **zero**. All-video/all-academy review is incomplete. The new [gold drawing observations](examples/research/xauusd_2026-08-26_second_short_0348.md) do not resolve the obscured target price and chart timezone.
- MT5 execution and strategy performance. Passing notification tests establishes neither autonomous order reliability nor profitability.

MT5 candles can support forward scanning and backtests for the chosen broker. They cannot silently replace the FOREXCOM candles in an exact Dorus illustration fixture: feed differences and candle alignment must remain identified.
