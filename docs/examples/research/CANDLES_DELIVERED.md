# Candles delivered for the retrieval requests

Pulled on 2026-10-01 through the TradingView MCP (`mcp-tv-get-ohlcv`) and saved in `data/tv_cache/`
(columns `timestamp,open,high,low,close,volume`, timestamps are candle opens in UTC, naive).
The feed serves only the latest N bars per call (max 5000), so every file runs up to the pull time;
the requested windows sit inside. Daily and weekly bars are the provider's native bars.

| Request | Feed, timeframe | File | First candle (UTC) | Last candle (UTC) | Rows | Bars before window | Covers window | Note |
|---|---|---|---|---|---|---|---|---|
| `k2_btc_weekly` | `INDEX:BTCUSD`, 1W | `data/tv_cache/INDEX_BTCUSD_1W.csv` | 2009-10-05 00:00:00 | 2026-09-28 00:00:00 | 879 | 735 | yes | weekly analysis context |
| `k3_gold_context_4h` | `FOREXCOM:XAUUSD`, 4H | `data/tv_cache/FOREXCOM_XAUUSD_4H.csv` | 2025-06-17 06:00:00 | 2026-10-01 02:00:00 | 2000 | 1604 | yes | context only; not a verified 4H POI |
| `k3_gold_detail_1m` | `FOREXCOM:XAUUSD`, 15m | `data/tv_cache/FOREXCOM_XAUUSD_15min.csv` | 2026-07-31 14:00:00 | 2026-10-01 04:15:00 | 4000 | 1508 | yes | requested 1m; the feed serves only the latest 5000 bars per call, so 1m reaches back about three days: delivered 15m |
| `k4_btc_context_4h` | `INDEX:BTCUSD`, 4H | `data/tv_cache/INDEX_BTCUSD_4H.csv` | 2025-11-02 00:00:00 | 2026-10-01 04:00:00 | 2000 | 1446 | yes | context only; not a verified 4H POI |
| `k5_btc_daily` | `INDEX:BTCUSD`, 1D | `data/tv_cache/INDEX_BTCUSD_1D.csv` | 2024-10-12 00:00:00 | 2026-10-01 00:00:00 | 720 | 81 | yes | anchor candle verified, see below |
| `s1_eurusd_student_4h` | `OANDA:EURUSD`, 4H | `data/tv_cache/OANDA_EURUSD_4H.csv` | 2025-06-18 21:00:00 | 2026-10-01 01:00:00 | 2000 | 1471 | yes | student chart context |
| `s2_usdjpy_student_daily` | `FOREXCOM:USDJPY`, 1D | `data/tv_cache/FOREXCOM_USDJPY_1D.csv` | 2019-01-20 22:00:00 | 2026-09-30 21:00:00 | 2000 | 1869 | yes | student daily context |

## Anchor check (K5)

`INDEX:BTCUSD` daily candle 2026-01-30 in the file: O 84550.82 / H 84638.35 / L 81047.8 / C 84149.17.
Astra's chart reading: O 84550.82 / H 84638.35 / L 81047.8 / C 84149.17. All four digits match, so the feed and the date alignment are confirmed.

## Using the files in a fixture

An example is `<name>.yaml` plus `<name>.csv` in the same directory (`docs/examples/`), optionally
`<name>_ltf.csv` with the confirmation-timeframe candles. Copy the requested window plus the padding
from the cache file into `<name>.csv` (same columns; `python -m kronos_trader resample` is not needed),
fill `expect:` from a readable source and only then drop `regression_ready: false`.

## Not delivered

- `k3_gold_detail_1m` at 1-minute resolution: unreachable for August through this feed. The 15m file covers the window;
  5m would reach back about 17 trading days only.
