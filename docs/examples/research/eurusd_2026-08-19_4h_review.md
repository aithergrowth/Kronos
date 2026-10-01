# eurusd_2026-08-19_4h_review

**Status:** student_plan_reviewed_critically_by_dorus. **Regression ready:** no.

**Source:** [S1 — EURUSD Short (DXY Long); Dorus reply dated Aug 19 and attached EURUSD_2026-08-19_15-52-31.png](https://www.skool.com/dorusview/eurusd-short-dxy-long)

**Attribution:** Dorus Wanders (critique only). Chart author: Jelle Engels.

Dorus says the analysis looks too far back and is no longer relevant; he gives no numerical lookback threshold.

## Data handoff

No candle CSV accompanies this record. The exact retrieval request below supplies the metadata fallback; source event timestamps and actual candle coverage remain unverified. Do not invent a UTC event time from a publication date or chart display clock. The earlier metadata block records source observations, not the bounds of the new request.

```yaml
symbol: EURUSD
feed: OANDA
displayed_timeframe: 4H
chart_snapshot_date: '2026-08-19'
source_event_utc_range_established: false
```

## Missing evidence

- Dorus-approved POI and bias
- actual entry confirmation
- event candle times
- verified required candle coverage within the requested interval
- OHLC export

The YAML separates student price labels from Dorus’s assessment. They are not `expect` values for the strategy detector and are not approved executable trade parameters.

## Inspected frame

![Inspected chart attachment](assets/eurusd_student_4h.jpg)

## Exact retrieval handoff — 2026-10-01

Student-authored proposed trade, critically reviewed by Dorus. Student levels are not Dorus-approved expectations; an executed or expressly rejected trade is not asserted.

These exact windows are **researcher-selected retrieval padding**, not dates Dorus is claimed to have marked as trade events. Request metadata is complete; no OHLC or completed regression fixture is supplied.

| Request | Feed / symbol | Timeframe | Requested dates, inclusive | Role |
|---|---|---|---|---|
| s1_eurusd_student_4h | `OANDA:EURUSD` | 4H | 2026-06-01 through 2026-08-19 | student chart context; Dorus-approved POI unresolved |

Source date evidence: 2026-08-19 15:52 UTC+2 (chart-creation header; not entry time).

For daily/weekly requests use the provider's native bar dates and preserve its candle alignment. Intraday request dates are explicit UTC retrieval boundaries, not an inferred screenshot timezone. Export actual provider candle-open timestamps in UTC. After retrieval, identify the relevant source scenario and verify 60 actual pre-sweep bars and any demonstrated post-break return; extend the interval if needed. These checks have **not** passed yet.

Unshown annotation fields may remain omitted. A missing entry, stop or target is not by itself a reason to withhold this handoff. The displayed chart timeframe must not silently become a verified formal POI timeframe. See [all retrieval requests](RETRIEVAL_REQUESTS.md) and [the request manifest](retrieval_requests.yaml).
