# TradingView data bridge

TradingView's official MCP server (`https://mcp.tradingview.com/mcp`, OAuth
login, Essential plan or higher) exposes, among others:

| Tool | Use |
|---|---|
| `mcp-tv-get-ohlcv` | historical bars: `symbol` (`OANDA:EURUSD`), `interval` (`1m 5m 15m 30m 1h 4h 1D 1W`, `1mo` for monthly), `count` ≤ 5000. Returns `bars: [{t,o,h,l,c,v}]`, `t` in unix seconds UTC. Bars are delayed 15+ minutes and the last bar may still change. |
| `mcp-tv-get-symbol-data` | live-ish quote (`close`, `bid`, `ask`, `update_mode`) |
| `mcp-tv-get-news` / `mcp-tv-get-news-story` | headlines (paged, ≤ 200) and full text |
| `mcp-tv-get-economic-calendar` | macro events by currency / importance (for blackout windows) |
| `mcp-tv-search-symbols` | resolve `EURUSD` → `OANDA:EURUSD`, `FX:EURUSD`, `FX_IDC:EURUSD`, … |
| `mcp-tv-get-technicals-rating`, screener, watchlists, alerts | not used by the strategy |

Rate limit ≈ 100 calls/minute.

## Path 1 - Claude Code as the bridge (today)

When a Claude Code session has the TradingView MCP connected, Claude pulls
bars and writes them into the cache. Per symbol and timeframe:

1. `mcp-tv-get-ohlcv` with `symbol=OANDA:EURUSD interval=4h count=5000`.
2. Save the payload JSON to a file and run
   `python -m kronos_trader import-tv --symbol OANDA:EURUSD --tf 4H --json bars_4h.json`
   (or call `kronos_trader.data.save_payload` directly). Saving **merges** with
   existing rows, so repeated pulls extend the history.
3. The engine reads `data/tv_cache/OANDA_EURUSD_<TF>.csv` for every timeframe
   (file labels `1min 5min 15min 30min 1H 4H 1D 1W 1MO`, chosen so that minute
   and month files cannot collide on Windows or macOS):
   `python -m kronos_trader scan --symbol EURUSD --data-dir data/tv_cache`
   (`EURUSD` is mapped to `OANDA:EURUSD` through `symbols.EURUSD.tradingview_symbol`).

Which bars to keep warm for one pair (all within the 5,000-bar limit):

| TF | bars | covers |
|---|---|---|
| 1M | 300 | 25 years |
| 1W | 1000 | 19 years |
| 1D | 3000 | 12 years |
| 4H | 5000 | ~3.3 years |
| 1H | 5000 | ~8 months |
| 15m | 5000 | ~2 months |
| 5m | 5000 | ~2.5 weeks |

Because 1-minute history is short, 1H-POI confirmations (min. 1m) are only
possible live or from a broker export; backtests use 5m/15m confirmations for
4H/1D POIs and above.

## Path 2 - direct client

`kronos_trader.data.TradingViewMCPClient` speaks the MCP streamable-HTTP
protocol (JSON-RPC over POST, SSE responses supported) with a bearer token in
`TRADINGVIEW_MCP_TOKEN`. `python -m kronos_trader tv-tools` lists the tools the
server currently exposes and re-maps the names if they changed. The transport
is untested from the cloud session (no token there); the payload parser is
covered by tests with a real payload.

## Symbol naming

Use one feed consistently. `OANDA:EURUSD` (default in `config.py`) has 24/5
forex bars; `FX:EURUSD` is FXCM; `FX_IDC:EURUSD` is the ICE composite. Daily
bars from these feeds open at 21:00/22:00 UTC (New York close); when
resampling intraday bars yourself, pass `--session-offset 2` (or 3 in summer)
so the daily/weekly candles line up with the platform.

## Headlines in the Telegram messages (7 October)

With `TRADINGVIEW_MCP_TOKEN` set on the computer that runs the windows, the POI-touch notice and the message after a
trade carry up to three TradingView headlines of the last 24 hours for that market (`live.news_headlines: 3`, 0 = off;
`live.news_headlines_hours: 24`), read at most every 15 minutes per market. They are context for the trader, not an
input to a trade. Without the token, or when a read fails, the messages are as before and nothing else changes. The
news blackout does not need the token: its calendar is `data/calendar/high_impact.csv` (from the TradingView economic
calendar, refreshed in the repository) beside the ForexFactory weekly feed.

## Rule: news is not a signal

The rule set says external factors must not influence the trade. The calendar
is therefore only used for **blackout windows** (`prop_firm.news_blackout_minutes`,
`data.tradingview_mcp.news_blackout_windows`), never to pick a direction.
