# BTC daily scenarios — not a completed trade

Source: [K5 — Bitcoin koersverwachting, scenario’s en koopmomenten, 02:30](https://www.skool.com/dorusview/classroom/304766fd?md=1262146f8aee4d35a29c63b1b6e95950).
Confidence: **medium** for chart application.

The header identifies INDEX:BTCUSD, 1D. The public caption at 00:06 explicitly names 7 September 2026. The 02:30 crosshair reads **Thu 16 Apr 26** and **75223.19**; neither is an entry assertion. P, B and X annotations and shaded areas are visible. Exact boundary prices cannot be read and are omitted. The exact requested daily retrieval window is supplied below as researcher-selected padding. Source event dates and required candle coverage remain unverified.

Raw academy frame omitted from the PR; verify the timestamp in the linked lesson.

This remains a research record. Missing fields are omitted from the YAML; no
synthetic candles, tolerance or detector expectations are supplied.

Public playback captions reviewed continuously to the end (player displayed 07:46); no independent audio verification. At 01:15–01:56 he describes a prior spot/DCA purchase and an exceptional trendline-close rationale. At 02:32–03:07 he explains conditional scenarios; at 03:15–05:08 he combines liquidity, the remaining gap and protection. At 06:35–06:58 he describes monthly technically informed spot buying through January. These passages do not establish funded-account trade frequency, exact fills, or a complete regression case.

## Exact retrieval handoff — 2026-10-01

Daily conditional analysis with X, B and P annotations; no complete executed trade or selected numerical POI asserted.

These exact windows are **researcher-selected retrieval padding**, not dates Dorus is claimed to have marked as trade events. Request metadata is complete; no OHLC or completed regression fixture is supplied.

| Request | Feed / symbol | Timeframe | Requested dates, inclusive | Role |
|---|---|---|---|---|
| k5_btc_daily | `INDEX:BTCUSD` | 1D | 2025-01-01 through 2026-09-07 | daily analysis context; exact formal POI selection unresolved |

Source date evidence: 2026-04-16 (chart crosshair Thu 16 Apr 26; not trade execution); 2026-09-07 (dated lesson and 00:06 caption; not a chart event timestamp).

For daily/weekly requests use the provider's native bar dates and preserve its candle alignment. Intraday request dates are explicit UTC retrieval boundaries, not an inferred screenshot timezone. Export actual provider candle-open timestamps in UTC. After retrieval, identify the relevant source scenario and verify 60 actual pre-sweep bars and any demonstrated post-break return; extend the interval if needed. These checks have **not** passed yet.

Unshown annotation fields may remain omitted. A missing entry, stop or target is not by itself a reason to withhold this handoff. The displayed chart timeframe must not silently become a verified formal POI timeframe. See [all retrieval requests](RETRIEVAL_REQUESTS.md) and [the request manifest](retrieval_requests.yaml).

### Readable candle anchor

K5 at **00:09** displays **INDEX:BTCUSD, 1D**, with the selected candle dated
**Fri 30 Jan 2026**. Its header reads **O 84550.82, H 84638.35, L 81047.80,
C 84149.17**. All digits received an independent second visual check; confidence
is medium. This is a source-to-data matching anchor, not a trade event or a
verified UTC opening time. The separate crosshair price 100311.06 and live quote
79109.80 are excluded from the candle values.
