# Live setup — MT5 candles, Telegram alerts and optional execution

Max's active route is **MetaTrader 5 candles → strategy analysis with optional Kronos forecasts → Telegram notifications**.
Use [the focused MT5/Telegram guide](MT5_TELEGRAM_READINESS.md). Without `--execute`,
the adapter only supplies candles: the runner receives no execution broker, does
not manage positions and does not poll approval commands. Configured Telegram
credentials still enable real notifications; without them messages print locally.

Optional execution is a separate mode, explicitly selected with `--execute`.
The default candle request includes 1m through monthly timeframes. TradingView
cache fallback is labelled by source and remains subject to freshness checks.

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

Market data: IBKR serves quotes and historical bars to the API only when the
account has market data permissions. A paper account has them when the live
account has them and sharing is on: Client Portal, Settings, User Settings,
Paper Trading Account, share real-time market data subscriptions. Without
them `ibkr-test` shows `Error 10089` (quotes) and `Error 162 ... No market
data permissions for IDEALPRO CASH` (bars); orders still work. In that case
run the loop with candles from OANDA (`--feed oanda`, section 3) and keep the
orders on IBKR.

Forex trades on IDEALPRO in units (1.0 lot = 100,000). Keep the paper account
the size of the real one: orders under roughly 25,000 units are odd lots with
worse fills. Gold and indices go through IBKR CFDs (`ibkr_contract` in the
symbol spec); check they are enabled for your region.

## 1b. MetaTrader 5 demo: live candles and a paper venue without a live account

An MT5 demo terminal can supply broker candles and simulated execution.
Available symbols and history depend on the broker and terminal settings.
Max uses MT5 for the candle feed; IBKR is not required.

1. Install MetaTrader 5 from metatrader5.com (or the terminal of the broker
   or prop firm you will use later). On first start it offers a demo account
   on the MetaQuotes-Demo server; accept, or open one under File, Open an
   Account. Note the login, the password and the server name.
2. Keep the terminal running and logged in.
3. On the laptop:

   ```powershell
   pip install MetaTrader5
   setx MT5_LOGIN "12345678"
   setx MT5_PASSWORD "your-password"
   setx MT5_SERVER "MetaQuotes-Demo"
   ```

   Open a new terminal. If the terminal is not found automatically, also set
   `MT5_PATH` to `C:\Program Files\MetaTrader 5\terminal64.exe`.
4. `python -m kronos_trader mt5-test --symbol EURUSD --tf 15m` prints the
   account, the configured timestamp correction (normally zero) and the last five bars.
5. `python -m kronos_trader live --symbol EURUSD --broker mt5` runs the loop
   with MT5 candles and Telegram notifications; it does not place or manage orders.

Brokers name symbols differently (`EURUSD.r`, `XAUUSD.m`): set
`mt5_symbol` in the symbol spec. MetaQuotes documents Python API candle/tick
epochs as UTC. They are preserved by default, including native 4H/daily opens.
`MT5_SERVER_OFFSET_HOURS` is a manual compatibility correction only; leave it
unset for the standard API. Tick age is never interpreted as a timezone.

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

The loop needs live candles for every timeframe the rules use (1M down to
1m, `live.broker_timeframes`) and takes them from one source, chosen with
`--feed`:

- `broker` (default with `--broker ibkr` or `mt5`): the broker's own bars.
  MT5 always has them (section 1b); IBKR needs market data permissions
  (section 1).
- `oanda`: a free OANDA practice account. Open one at oanda.com, create a
  token under *Manage API Access*, then

  ```powershell
  setx OANDA_TOKEN "your-token"
  ```

  open a new terminal and test with
  `python -m kronos_trader feed-test --symbol EURUSD --tf 15m`. Forex, gold
  and index CFDs are available; BTC is not in the EU.
- `cache`: the TradingView CSVs in `data/tv_cache/` only (default without a
  live broker). Filled through the TradingView MCP
  (`docs/TRADINGVIEW_BRIDGE.md`); only as fresh as the last import, fine for
  a dry run.

The cache is also the fallback for a timeframe the live source fails to
deliver, a source that fails for every timeframe is left alone for ten
minutes (`live.feed_retry_seconds`), and the loop prints where each timeframe
came from. When the newest candle of a timeframe closed more than two
candles ago the data is stale: the loop keeps analysing and managing
positions but opens no new setups and says why
(`live.max_data_age_bars`, `live.require_fresh_data`).

## 4. Run

```shell
# 1) dry-run: setups to Telegram (or the terminal) only, no orders
python -m kronos_trader live --symbol EURUSD --broker ibkr

# same on an MT5 demo account: candles and paper orders from MetaTrader 5
python -m kronos_trader live --symbol EURUSD --broker mt5

# IBKR orders with candles from OANDA (only where OANDA hands out API tokens)
python -m kronos_trader live --symbol EURUSD --broker ibkr --feed oanda

# 2) execute with the Approve step (the mode for the challenge)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute

# 3) fully automatic (only after weeks of 1 and 2)
python -m kronos_trader live --symbol EURUSD --broker ibkr --execute --no-approval

# single scan and exit, useful for a quick check
python -m kronos_trader live --symbol EURUSD --broker ibkr --once
```

Approval requests expire after one confirmation-timeframe candle (minimum 5
minutes); an approval that arrives after that is refused. An approved order
is re-checked against the risk guard and a fresh current price (R:R still
≥ 1:3) before it is sent, and not sent at all when no current price can be
had. An order counts as filled only once the broker confirms the fill;
otherwise the loop reports it as submitted and confirms it, or reports that
it did not fill, on a later poll.

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
   python -m kronos_trader live --symbol EURUSD --broker mt5
   ```

   Windows Task Scheduler ("at log on", restart on failure) brings it back
   after a reboot.
4. While testing, add `--notify-every-scan` to get one message per poll on
   the phone; drop it once you trust the loop.

Configured notifications: morning analysis on the first weekday scan at or
after 08:45 Amsterdam (bias, decision, POI map), a heads-up for a POI touch,
and confirmed setups. Approval buttons, fills, break-even moves and closes
belong to execution mode; notification-only mode sends setup alerts. The
current defaults use 09:00–17:00 Amsterdam, first-candle confirmation off
and Kronos advisory. The recorded verification backtests retain their earlier
Kronos-off profile; they do not test the new advisory forecast output. These
are project choices. The news gate uses loaded events
and does not establish complete calendar coverage.

The guard uses 4 % daily loss, 8 % total drawdown, one open trade and 1 %
planned risk. These are project settings; the selected firm's current
contract and account-specific calculation rules remain unverified.

### Generated charts and Kronos on the chart

With `live.send_charts: true`, the runner attempts to attach a generated image
to briefing, POI-touch and setup notifications. The default image lookback is
120 candles (`live.chart_lookback`); files are written under `live.charts_dir`.
It can show input candles, engine-mapped zones and, for a setup, an entry
marker, stop/target boxes and R:R. These are system-generated illustrations,
not Dorus screenshots or verified reconstructions of his chart readings.

When model forecasts are available, the image can also show sampled paths,
their mean and the expected band. `kronos.mode: advisory` does not veto trades;
`filter` remains a separate selectable mode, and `off` avoids loading the
model. Install the model dependencies from `requirements.txt` and provide
access to the configured weights to use real forecasts. Rendering a supplied
or fake forecast in a test does not verify model inference or predictive value.

The optional MT5 indicator is installed by copying `mt5/KronosForecast.mq5`
into the terminal's `MQL5\Indicators` folder (File → Open Data Folder), then
compiling it in MetaEditor and attaching it to a chart. Enable Chart Shift
to leave space to the right. The indicator is designed to read
`kronos_forecast_<SYMBOL>.csv` from the terminal's common files folder every
30 seconds, displaying the mean path and band. It only draws; it does not trade.

Export is conditional on an available forecast, `live.mt5_overlay` and an MT5
adapter being available to the chart path. The notification-only runner has
no execution broker, so do not assume that selecting `--broker mt5` alone
proves overlay export in that mode. Confirm an updated file, the exact broker
symbol, chart timeframe and chart-time alignment on the terminal before
relying on the display. This export does not provide a TradingView overlay.

Live Telegram photo delivery, trained-model inference, MQL5 compilation and
the on-terminal overlay have not been verified here. Chart errors are logged;
an accompanying text notification is not proof that its image or overlay
was produced. The chart feature is independent of the recorded Kronos-off
backtest results.

Secrets stay in environment variables on that machine only; never in the repo
and never in a third-party agent sandbox. A small VPS is the alternative if
the laptop cannot stay on.

News: the engine rejects new signals from 30 minutes before to 30 minutes
after a loaded high-impact event of the symbol's currencies (`news:` in the
config). These durations are project choices, not verified Dorus rules. It
loads `data/calendar/high_impact.csv` and attempts to refresh this and next
week from the free ForexFactory feed every hour. Setup messages name the
next loaded event within four hours. A missing CSV supplies no events; a
failed refresh retains the events already loaded. This does not verify that
calendar coverage is complete or current.

## 6. Prop-firm phase

The challenge runs on the firm's platform, not on IBKR. MetaTrader 5 is
supported through `MT5Broker` (`--broker mt5`, Windows, `MT5_LOGIN`,
`MT5_PASSWORD`, `MT5_SERVER`). cTrader or MatchTrader adapters are built once
the firm is chosen.
