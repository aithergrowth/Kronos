# Exact candle-retrieval requests

**Seven requests across six cases: four Dorus analyses/recaps and two student critiques.** These are exact metadata handoffs, not OHLC exports or runnable regression fixtures. No required candle-coverage check has passed.

The user permits symbol, timeframe, feed and an exact date range instead of a candle CSV. The date ranges here are explicitly **researcher-selected padding windows**. Source-observed dates are recorded separately in each YAML and handoff. A window endpoint does not assert a source event, execution time or visible chart boundary.

| Source / case | Request | Observed feed and timeframe | Requested dates, inclusive | Scope |
|---|---|---|---|---|
| [K2](https://www.skool.com/dorusview/classroom/304766fd?md=78ef5903bc4f435997de67e79210c4dd) · [btcusd_2026-09-27_weekly_condition](btcusd_2026-09-27_weekly_condition.md) | `k2_btc_weekly` | `INDEX:BTCUSD`, 1W | 2024-01-01 through 2026-09-27 | weekly analysis context |
| [K3](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411) · [xauusd_2026-08-26_public_recap](xauusd_2026-08-26_public_recap.md) | `k3_gold_context_4h` | `FOREXCOM:XAUUSD`, 4H | 2026-07-01 through 2026-08-31 | context only; not a verified 4H POI |
| [K3](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411) · [xauusd_2026-08-26_public_recap](xauusd_2026-08-26_public_recap.md) | `k3_gold_detail_1m` | `FOREXCOM:XAUUSD`, 1m | 2026-08-25 through 2026-08-28 | supplemental entry-detail candles; not the main POI timeframe |
| [K4](https://www.skool.com/dorusview/classroom/304766fd?md=9e375caa007041fdb4cfd1c4d89726bf) · [btcusd_2026-09_4h_recap](btcusd_2026-09_4h_recap.md) | `k4_btc_context_4h` | `INDEX:BTCUSD`, 4H | 2026-07-01 through 2026-09-30 | context only; not a verified 4H POI |
| [K5](https://www.skool.com/dorusview/classroom/304766fd?md=1262146f8aee4d35a29c63b1b6e95950) · [btcusd_2026-09-07_daily_scenarios](btcusd_2026-09-07_daily_scenarios.md) | `k5_btc_daily` | `INDEX:BTCUSD`, 1D | 2025-01-01 through 2026-09-07 | daily analysis context; exact formal POI selection unresolved |
| [S1](https://www.skool.com/dorusview/eurusd-short-dxy-long) · [eurusd_2026-08-19_4h_review](eurusd_2026-08-19_4h_review.md) | `s1_eurusd_student_4h` | `OANDA:EURUSD`, 4H | 2026-06-01 through 2026-08-19 | student chart context; Dorus-approved POI unresolved |
| [S2](https://www.skool.com/dorusview/long-trade-usdjpy) · [usdjpy_2026-08-19_bias_review](usdjpy_2026-08-19_bias_review.md) | `s2_usdjpy_student_daily` | `FOREXCOM:USDJPY`, 1D | 2026-04-01 through 2026-08-31 | student daily context; Dorus-approved POI unresolved |

[Machine-readable request manifest](retrieval_requests.yaml). Each linked case retains its source URL, source timestamps, readable observations and omitted fields.

## Scope and verification

- **Formal POI classification is not verified by these requests.** K3/K4 timeframes are observed chart context; K3 1m is supplemental entry detail. K2/K5 are conditional analyses. S1/S2 are student-authored and their POIs are not approved by Dorus.
- The student cases remain critiques, not accepted trade expectations or automatically proven rejected trades. K2/K5 remain conditional analysis; no executed trade is invented.
- Fetch daily/weekly bars using native provider dates and preserve their alignment. For intraday requests the dates are UTC retrieval boundaries selected for coverage; they are not a conversion of the screenshot clock.
- Export real candle-open timestamps in UTC. Do not fabricate OHLC, timezone offsets, numeric annotations or missing order fields.
- Identify the relevant source scenario and then count at least 60 actual candles before its sweep. Verify coverage through any demonstrated post-break return. Extend the requested window if either check fails; no count or outcome is asserted here.
- Unshown YAML fields may remain omitted. A readable illustrative analysis does not require broker-fill verification or every stop/target field.
- These files stay outside the main example-test scan. A complete metadata request is distinct from a matching CSV/YAML regression fixture and from satisfying every example category in the brief.

No raw academy screenshot is included. All source descriptions and numerical observations remain in the existing case records; this index adds retrieval parameters only.

## Native export attempt and matching anchor

On 2026-10-01 the exact `INDEX:BTCUSD` daily chart was opened in TradingView
with a UTC clock and the requested 2025-01-01–2026-09-07 range. The native
Download action opened an upgrade prompt recommending Premium and produced no
CSV. The [official plan comparison](https://www.tradingview.com/pricing/?source=header_goass%3D),
checked 2026-10-01, lists chart-data download on **Plus, Premium and Ultimate**,
but not **Basic or Essential**. Plus is the minimum listed plan; the Premium
upsell was a recommendation. No account, payment or alternative-extraction
action was taken.

K5 at 00:09 supplies a useful independent matching anchor: selected daily
candle **2026-01-30**, **O 84550.82 / H 84638.35 / L 81047.80 / C 84149.17**.
Two readers verified the chart digits. The case YAML records this as a chart
candle, not a trade event. Compare it with the native exported bar before
assuming the feed and date alignment match; that comparison is still pending.

## Delivered

Candles for all seven requests are in `data/tv_cache/`; coverage, the K5 anchor check and fixture notes are in [CANDLES_DELIVERED.md](CANDLES_DELIVERED.md).
