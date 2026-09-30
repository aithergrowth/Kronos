# Live setup - Telegram, IBKR paper, the loop

The live loop is `python -m kronos_trader live`. It reads higher-timeframe
history from the TradingView cache, low-timeframe bars from the broker,
runs the engine on every poll, sends setups to Telegram, waits for your
Approve tap, places a bracket order (market + stop + target), moves the stop
to break-even per the rules and reports fills and closes with P&L.

## 1. Telegram (10 minutes)

1. In Telegram open **@BotFather**, send `/newbot`, pick a name, copy the token.
2. Start a chat with your new bot and send it any message.
3. Get your chat id: open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a
   browser and read `"chat":{"id":...}`.
4. Set the environment variables on the machine that runs the loop:
   `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
5. `python -m kronos_trader telegram-test` → the bot says "connected".

Only taps and `/approve` / `/skip` texts coming from that chat are accepted.

## 2. IBKR paper account

1. Install **Trader Workstation** or **IB Gateway**, log in with the *paper*
   credentials.
2. Configure → API → Settings: enable *ActiveX and Socket Clients*, note the
   port (paper TWS 7497, paper Gateway 4002), add `127.0.0.1` to trusted IPs,
   untick *Read-Only API*.
3. `pip install ib_async`.
4. Optional environment variables: `IBKR_HOST` (default 127.0.0.1),
   `IBKR_PORT` (default 7497), `IBKR_CLIENT_ID` (default 17), `IBKR_ACCOUNT`.
5. `python -m kronos_trader ibkr-test --symbol EURUSD --tf 15m` prints
   equity, the contract, the price and the last bars.

Forex trades on IDEALPRO in units (1.0 lot = 100,000). Keep the paper account
the size of the real one: orders under roughly 25,000 units are odd lots with
worse fills. Gold and indices go through IBKR CFDs (`ibkr_contract` in the
symbol spec); check they are enabled for your region.

## 3. Data

- Higher timeframes (1M/1W/1D, and 4H/1H if the broker feed is off): the CSV
  cache in `data/tv_cache/`, filled through the TradingView MCP
  (`docs/TRADINGVIEW_BRIDGE.md`). Refresh it at least once a day.
- Low timeframes: pulled from the broker on every poll
  (`live.broker_timeframes`, default 5m/15m/1H/4H).

## 4. Run

```shell
# 1) dry-run: signals to Telegram only, no orders
python -m kronos_trader live --symbol EURUSD --broker ibkr --data-dir data/tv_cache

# 2) execute with the Approve step (recommended for the challenge)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute

# 3) fully automatic (only after weeks of 1 and 2)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute --no-approval

# single scan, useful in cron
python -m kronos_trader live --symbol EURUSD --broker ibkr --once
```

Approval requests expire after one confirmation-timeframe candle (minimum 5
minutes); an approved order is re-checked against the risk guard and the
current price (R:R still ≥ 1:3) before it is sent.

## 5. Where it runs

Forex runs 24/5, so the loop needs a machine that never sleeps: the desktop
with sleep disabled and TWS logged in, or a small VPS. Use a process manager
(Windows Task Scheduler "at startup", `systemd` on Linux) so it restarts after
a crash. Secrets stay in environment variables on that machine only; never in
the repo and never in a third-party agent sandbox.

## 6. Prop-firm phase

The challenge runs on the firm's platform, not on IBKR. MetaTrader 5 is
supported through `MT5Broker` (`--broker mt5`, Windows, `MT5_LOGIN`,
`MT5_PASSWORD`, `MT5_SERVER`). cTrader or MatchTrader adapters are built once
the firm is chosen.
