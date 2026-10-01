# usdjpy_2026-08-19_bias_review

**Status:** student_scalp_claim_with_dorus_bias_warning. **Regression ready:** no.

**Source:** [S2 — Long trade USDJPY; Dorus reply dated Aug 19; attached 43-second chart video](https://www.skool.com/dorusview/long-trade-usdjpy)

**Attribution:** Dorus Wanders (critique only). Chart author: Jelle Engels.

Dorus identifies errors in the student’s bias analysis but does not enumerate the exact incorrect levels or votes.

## Data handoff

No candle CSV accompanies this record. The exact retrieval request below supplies the metadata fallback; source event timestamps and actual candle coverage remain unverified. Do not invent a UTC event time from a publication date or chart display clock. The earlier metadata block records source observations, not the bounds of the new request.

```yaml
symbol: USDJPY
feed: FOREXCOM
displayed_timeframes:
- 1H
- 1D
chart_month: 2026-08
source_event_utc_range_established: false
```

## Missing evidence

- which bias votes Dorus corrects
- Dorus-approved POI timeframe
- exact entry/sweep/break candle times
- verified required candle coverage within the requested interval
- OHLC export

The YAML separates student price labels from Dorus’s assessment. They are not `expect` values for the strategy detector and are not approved executable trade parameters.

## Inspected frame

![Inspected chart attachment](assets/usdjpy_student_daily.jpg)

## Exact retrieval handoff — 2026-10-01

Student chart with Dorus warning that its bias has errors. Exact corrected votes and approved POI remain unverified.

These exact windows are **researcher-selected retrieval padding**, not dates Dorus is claimed to have marked as trade events. Request metadata is complete; no OHLC or completed regression fixture is supplied.

| Request | Feed / symbol | Timeframe | Requested dates, inclusive | Role |
|---|---|---|---|---|
| s2_usdjpy_student_daily | `FOREXCOM:USDJPY` | 1D | 2026-04-01 through 2026-08-31 | student daily context; Dorus-approved POI unresolved |

Source date evidence: 2026-08-07 (selected chart date Fri 07 Aug 26; not entry time); 2026-08-24 (separate date/drawing label Mon 24 Aug 26; not execution).

For daily/weekly requests use the provider's native bar dates and preserve its candle alignment. Intraday request dates are explicit UTC retrieval boundaries, not an inferred screenshot timezone. Export actual provider candle-open timestamps in UTC. After retrieval, identify the relevant source scenario and verify 60 actual pre-sweep bars and any demonstrated post-break return; extend the interval if needed. These checks have **not** passed yet.

Unshown annotation fields may remain omitted. A missing entry, stop or target is not by itself a reason to withhold this handoff. The displayed chart timeframe must not silently become a verified formal POI timeframe. See [all retrieval requests](RETRIEVAL_REQUESTS.md) and [the request manifest](retrieval_requests.yaml).
