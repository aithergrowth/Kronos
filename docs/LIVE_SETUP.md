# Live setup - IBKR paper, Telegram, the loop, working from your phone

The live loop is `python -m kronos_trader live`. On every poll it pulls candles
from the broker (every timeframe the rules need, 1M down to 5m; the
TradingView cache is the fallback), runs the engine, sends setups to Telegram,
waits for your Approve tap, places a bracket order (market + stop + target),
moves the stop to break-even per the rules and reports fills and closes with
P&L.

Install the trader dependencies once:

```shell
pip install -r requirements-trader.txt
```

(`requirements.txt` is Kronos itself: torch and the model loader, only needed
for the forecast indicator.)

## 1. IBKR paper account (TWS)

1. Start **Trader Workstation** and log in with the *paper* credentials
   (IB Gateway works the same way; its paper port is 4002).
2. File → Global Configuration → API → Settings:
   - tick *Enable ActiveX and Socket Clients*
   - untick *Read-Only API*
   - Socket port **7497**
   - add `127.0.0.1` to *Trusted IPs* (or leave the prompt on and accept the
     connection once)
   - leave *Download open orders on connection* ticked
3. Optional environment variables: `IBKR_HOST` (default 127.0.0.1),
   `IBKR_PORT` (default 7497), `IBKR_CLIENT_ID` (default 17), `IBKR_ACCOUNT`
   (only when the login holds more than one account).
4. Test the connection; TWS must be running and logged in:

   ```shell
   python -m kronos_trader ibkr-test --symbol EURUSD --tf 15m
   ```

   It prints equity, the contract, the price and the last five bars. Send the
   output back when anything looks wrong: the adapter was written against the
   `ib_async` API and still has to be exercised against a real TWS session.

Forex trades on IDEALPRO in units (1.0 lot = 100,000). Keep the paper account
the size of the real one: orders under roughly 25,000 units are odd lots with
worse fills. Gold and indices go through IBKR CFDs (`ibkr_contract` in the
symbol spec); check they are enabled for your region.

## 2. Telegram (10 minutes)

Telegram is what makes the phone workflow possible: setups, the
Approve / Skip buttons, fills, break-even moves and closes all arrive in the
bot chat, and `/approve <id>` or `/skip <id>` typed in the chat work too.
Without it the same messages are printed in the terminal
(`[telegram dry-run]`), fine for a dry run, useless for approving a trade
from the sofa.

1. In Telegram open **@BotFather**, send `/newbot`, pick a name, copy the token.
2. Start a chat with your new bot and send it any message.
3. Get your chat id: open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a
   browser and read `"chat":{"id":...}`.
4. Set the environment variables on the machine that runs the loop. Windows:

   ```powershell
   setx TELEGRAM_BOT_TOKEN "123456:ABC..."
   setx TELEGRAM_CHAT_ID "123456789"
   ```

   then open a new terminal.
5. `python -m kronos_trader telegram-test` → the bot says "connected".

Only taps and `/approve` / `/skip` texts coming from that chat are accepted.

## 3. Data

- With `--broker ibkr` (or `mt5`) every timeframe comes from the broker on
  each poll (`live.broker_timeframes`, default 5m 15m 1H 4H 1D 1W 1M). The
  `data/tv_cache/` CSVs are the fallback for a timeframe the broker fails to
  deliver, and the data for backtests.
- With `--broker none` or `paper` everything comes from the cache, filled
  through the TradingView MCP (`docs/TRADINGVIEW_BRIDGE.md`); refresh it at
  least once a day.

## 4. Run

```shell
# 1) dry-run: setups to Telegram (or the terminal) only, no orders
python -m kronos_trader live --symbol EURUSD --broker ibkr

# 2) execute with the Approve step (the mode for the challenge)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute

# 3) fully automatic (only after weeks of 1 and 2)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute --no-approval

# single scan and exit, useful for a quick check
python -m kronos_trader live --symbol EURUSD --broker ibkr --once
```

Approval requests expire after one confirmation-timeframe candle (minimum 5
minutes); an approved order is re-checked against the risk guard and the
current price (R:R still ≥ 1:3) before it is sent.

## 5. Working from your phone

The loop runs on the laptop; the phone only needs Telegram. Keep the laptop
on mains power, awake and logged in to TWS:

1. Power: in an administrator PowerShell

   ```powershell
   powercfg /change standby-timeout-ac 0
   powercfg /change hibernate-timeout-ac 0
   powercfg /change monitor-timeout-ac 10
   ```

   and Settings → System → Power → "closing the lid" → *Do nothing*.
2. TWS logs itself out once a day. Global Configuration → Lock and Exit:
   choose *Auto restart* with a time outside the sessions (for example
   23:45). It then restarts without a login prompt, except for the full
   login once a week on Sunday.
3. Start the loop in a terminal that stays open (mode 1 first, then 2):

   ```shell
   python -m kronos_trader live --symbol EURUSD --broker ibkr
   ```

   Windows Task Scheduler ("at log on", restart on failure) brings it back
   after a reboot.
4. While testing, add `--notify-every-scan` to get one message per poll on
   the phone; drop it once you trust the loop.

Secrets stay in environment variables on that machine only; never in the repo
and never in a third-party agent sandbox. A small VPS is the alternative if
the laptop cannot stay on.

## 6. Prop-firm phase

The challenge runs on the firm's platform, not on IBKR. MetaTrader 5 is
supported through `MT5Broker` (`--broker mt5`, Windows, `MT5_LOGIN`,
`MT5_PASSWORD`, `MT5_SERVER`). cTrader or MatchTrader adapters are built once
the firm is chosen.
