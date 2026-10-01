# Dorus source check — four requested follow-ups

Reviewed 2026-09-30; follow-up inspected 2026-10-01. See
[DORUS_PRIORITY_SOURCES.md](DORUS_PRIORITY_SOURCES.md) for the complete D/E/F caption review and stronger POI evidence. This supplements `ASTRA_TASKS.md`; it does not change the
trading code. The implementation was read at `feature/kronos-trader` commit
`dd79d29cda7b569f41b4e5dff62804de8eb72392`.
Claude subsequently merged this research and updated the implementation at
`d008dac7e9ebe4f760b022808912727d2380e8e0`: liquidity-to-protection is the new
default, M+D+4H is enabled, and BS thresholds are selectable. Comparisons below
to the old sweep/gap code are historical. Exact P and BS geometry remain
unverified; the new code is not treated as source evidence.

| Requested item | Result | Confidence |
|---|---|---|
| Gold, 26 August: corrected entry/SL/TP and clock | Corrected drawing entry and stop recovered; target distance/RR readable. Target-price label and timezone remain obscured. No complete fixture. | Medium for visual labels; unassessed for missing values and broker fills. |
| Liquidity and trading-plan priority videos | Both exact priority videos now have complete available Dutch-caption reviews; the additional FVG video is also reviewed. | High for explicit captioned statements; no independent audio/full visual verification. |
| Entry & POI: exact zone endpoints | The bearish **gap** is visibly wick-to-wick. New D/F evidence explicitly names liquidity-to-protection; exact P wick/body endpoints remain unresolved. K6 alone does not settle the full zone. | Medium for the gap diagram; not assessed for a complete POI rule. |
| BS = close through opposing balance | Supported conceptually and by explicit close-based entry examples. The universal threshold and gap-selection algorithm are not fully established. | High for the conceptual/close evidence; unassessed for the exact universal threshold. |

## 1. Gold: corrected drawing, not a complete execution fixture

Source **K3**: [Analyses → €8.000 verdiend binnen één uur.](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411),
Loom title *Goud scalps, liquiditeitsruns en twee shorts*, chart date 2026-08-26.

The **02:40** frame, after the stop is raised, shows:

| Screen object | Readable value | Treatment |
|---|---:|---|
| Entry axis label | 4624.53 | Corrected illustration, not verified broker fill. |
| Stop axis label | 4639.55 | Supersedes the earlier illustrated 4636.61 stop. |
| Stop distance | 15.02 | Position-tool label. |
| Target distance | 29.55 | Position-tool label, independently checked. |
| Risk/reward | 1.97 | Position-tool label, independently checked. |
| Target price axis label | Not readable | Covered by the recorded webcam. Omitted as an expected TP. |
| Chart clock | Only `17:23…` is readable | Seconds/timezone obscured; this is not an execution timestamp. |

The separate 4629.48 label is the crosshair. It is not an entry or stop. The
02:34 and 02:37 drawings are earlier states; neither is the corrected drawing.
At 02:38 the target is still being adjusted, so that frame is also intermediate.
Additional frames checked at **02:43, 02:57, 03:08 and 03:20** do not establish
the missing final target axis label or chart timezone. The separately recorded
S5 clock (UTC-4) must not silently define K3's clock.

The two readable prices and the target distance are preserved in
[the gold YAML](examples/research/xauusd_2026-08-26_public_recap.yaml), under
`illustrated_position_states`. The target price is not supplied by subtraction
and presented as a direct chart reading. `expect` remains absent and
`regression_ready` remains false.

### Attachment check — 2026-10-01

The same K3 lesson contains two mobile chart images. Both were inspected and
independently checked. These are separate feed observations, not replacements
for the corrected FOREXCOM drawing:

| Attachment | Symbol / chart timeframe | Phone clock | Green displayed quote | Reliably readable axis labels |
|---|---|---|---:|---|
| `IMG_3573.PNG` | `XAUUSD.pro` / M1 | 17:02 | 4602.10 | 26 Aug 16:42, 17:14, 17:46, 18:18 |
| `IMG_3574.PNG` | `XAUUSD.raw` / M15 | 17:03 | 4596.58 | 25 Aug 21:00; 26 Aug 14:00; 26 Aug 22:00 |

The green labels mark displayed quotes. Red/blue markers and connecting paths
have no numeric fill labels; neither image labels a stop or target. No year,
chart timezone, or broker/server identity is readable. Phone time does not
establish chart time. Consequently neither quote is a verified TP or fill, and
neither image resolves the final K3 target or authorizes copying S5's UTC−4.
Confidence: **medium**, visual evidence. The images remain private research
material; their factual readings are recorded in the gold YAML.

Still needed for the illustrated example: an unobscured final target label;
verified chart timezone and entry candle; formal POI timeframe, sweep/break
identities and zone bounds; and real candle data covering the required interval.
Verified broker fills are not a prerequisite for a clearly labeled illustration
or replay fixture; no broker execution claim would be made for such a fixture.
The displayed 4H context and 1m entry drawing alone do not establish a valid
4H-POI/1m-confirmation case under K1. A completed gold fixture has not been claimed.

## 2. Priority recordings — access restored

After the user handoff, both exact requested sources became retrievable:
**D / 81LThMAtj5o** (419 Dutch caption segments, through 16:23) and
**E / F5ciF74Uzr8** (391 Dutch caption segments, through 14:13). Additional
**F / O6IgD2llrq0** has 288 Dutch segments through 10:26. All were read end-to-end
and received a second independent read. Original audio and complete chart visuals
remain unverified. D’s requested POI frame buffered despite one player recovery.

The [priority-source update](DORUS_PRIORITY_SOURCES.md) gives dates, timestamps,
findings and chart leads. Earlier blocked/unreviewed status is historical, not
current. No raw full transcript is delivered. E’s initial English automatic
export is excluded in favor of its explicitly selected Dutch track.

## 3. Entry & POI: gap geometry is not full-zone geometry

Source **K6**: [2. De strategie leren → Entry & Poi](https://www.skool.com/dorusview/classroom/1924b124?md=cb63d3041eac47caa148cbf218e0dde8),
player title *5-0 Entries*, duration 10:25; publication date not displayed.

| Frame(s) | Observation | What it resolves |
|---|---|---|
| 00:55–00:56; 01:31 | Bullish line sketch with an X-marked horizontal level and an orange area below it. No candle bodies/wicks or explicit gap/P endpoints. | Cannot decide wick versus body or select `gap_bottom`, `gap_top`, or `protector`. |
| 02:30–02:31; 02:50–02:51; 03:33 | Additional line sketches and confirmation-timeframe notes. | These are not an exact OHLC boundary specification. |
| **07:30–07:31** | In a bearish three-candle sequence, the orange rectangle's top aligns with candle 1's **lower wick tip**; its bottom aligns with candle 3's **upper wick tip**. Their body edges are visibly elsewhere. | Supports a **wick-to-wick bearish gap**, not a body-to-body gap. Medium visual confidence; independently checked. |
| 07:40–07:41 | The same local gap is extended to the right. | No readable P label or full POI boundary is added. |
| 06:01; 07:50–08:01; 09:01 | Broader orange chart area and local candle examples are visible. | Does not establish how the full zone's edge maps to a particular gap/P boundary. |

For the inspected bearish gap, if candles are numbered 1, 2, 3 in time order:
the observed price interval is **[high(candle 3), low(candle 1)]**. This is a
description of the orange **gap** in this frame, not a new POI definition.
No bull-side mirror is presented here as a separately observed diagram.

**Historical code conclusion (dd79d29):** D 12:21–12:54 and F 03:00–03:36 explicitly name liquidity-to-protection and allow reaction before complete gap fill or deeper at protection. The former `poi_far_edge="gap_bottom"` and use of `sweep.extreme` therefore had a conceptual source mismatch; they were not verified full-zone endpoints. In that version of `poi.py`, it meant `gap.low` for a bullish POI and
`gap.high` for a bearish POI; the name does not mean the numerically lower edge
in both directions. This inspection does **not** verify that setting, nor the
choice of sweep-wick extreme rather than swept liquidity level at the other end.
No readable P annotation in the inspected frame establishes P's wick/body bounds
or its deterministic candle index.

**Additional check, 2026-10-01:** K7 was inspected at 03:46, 07:50 and 08:50.
The later chart frames show gap rectangles but no readable P label that resolves
the full-zone boundary. The authenticated embedded player works; opening the
same Vimeo media standalone was refused by its privacy settings. The lesson
was therefore inspected within Skool. No endpoint was inferred from that refusal.

## 4. BS: what can be confirmed for the function

Source **A**: [Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)](https://www.youtube.com/watch?v=HRPgdK8VhMc),
published 2026-02-18. These findings use the previously retrieved Dutch automatic captions. D 14:03–14:38 reinforces the BS/gap concept but adds no explicit close rule or exact boundary.
Source **B**, used for the alternative thresholds below:
[Mijn Volledige Trading Strategie Uitleg (Stap voor Stap)](https://www.youtube.com/watch?v=xWR8M46iSW8);
publication date unverified; available Dutch automatic captions previously reviewed.

| Passage | Finding | Confidence |
|---|---|---|
| 54:25–55:26; 01:06:09–01:07:19; 01:29:29–01:30:01 | Overcoming the relevant opposing balance/gap distinguishes BS from merely breaking local structure, which can be liquidity being taken. | High for conceptual distinction. |
| **02:25:40–02:26:15** | Identifies the gap, wants price above it and explicitly waits for a close before entry. | High for that demonstrated entry. |
| **02:30:39–02:30:56** | The 1m BS requires a break with a close; it has not happened before the session cutoff. | High for that example. |
| **01:07:49–01:08:30** | In the explanation he also points to getting above the candle that caused the gap. Captions do not identify its exact relation to the gap edge. | High for the stated object reference; unresolved price threshold. |
| 42:52–43:16; B 08:54–09:11 | More than one potential threshold is discussed. | No deterministic candidate-selection rule established. |

**Answer:** A close through the opposing balance level is a supported concise
description of the demonstrated BS concept. It is **not yet a verified complete
algorithm** for every case. In particular, the inspected dd79d29 `confirmation.py` selected
the latest opposing gap in its configured lookback, then tests `close > gap.high`
for bullish or `close < gap.low` for bearish. The source does not fully verify:

- always using that gap's far edge instead of an originating-candle boundary;
- always choosing the latest gap, the 60-candle lookback, or its relation to touch;
- requiring both candle open and close beyond the boundary (the examples establish
  a close, not that stricter full-body test);
- a mandatory retest, separate local sweep, or fixed expiry.

Therefore the close-based interpretation is supported, while the precise
threshold/selection assumptions must stay labeled provisional. This source
review supplies no justified replacement boundary for that function yet.

## Exact evidence still needed

### Candle delivery now has an exact metadata fallback

[Seven exact retrieval requests](examples/research/RETRIEVAL_REQUESTS.md) cover
six source cases: four Dorus analyses and two explicitly separated student
critiques. They supply feed, observed timeframe and exact requested date ranges.
The ranges are researcher-selected padding, not prices/times attributed to Dorus.
Unshown annotation fields remain omitted. This handoff is useful before a record
becomes an executable regression fixture; it does not establish missing formal
POI classifications or satisfy all requested example categories.

K5 at **00:09** provides a directly readable daily candle anchor:
**INDEX:BTCUSD, Fri 30 Jan 2026; O 84550.82, H 84638.35, L 81047.80,
C 84149.17**. An independent second visual check confirmed every digit.
Confidence: medium. This is not an entry/sweep/break timestamp. The crosshair
price and live quote are separate objects and are excluded.

On 2026-10-01 the exact INDEX:BTCUSD daily chart and UTC clock were selected in
TradingView, and the 2025-01-01–2026-09-07 retrieval range was applied. The native
**Download chart data → Download** action opened a **Premium upgrade gate**.
No CSV was produced, no account or payment change was made, and no alternative
extraction was attempted. Consequently the source candle has not yet been
matched against exported OHLC. Coverage and regression readiness remain open.

The additional gold recap XJ0iAKv0amQ (2026-04-25, 09:00) and coaching video
ZGwP57Xd2TU (2026-05-16, 1:19:33) were also checked for readable captions.
Their watch-page metadata was readable, but exports returned no transcript and
the transcript panels exposed no readable text. No strategy claim was added
from their titles or unavailable content.

| Open item | Source location to inspect | Evidence required before using it as a code expectation |
|---|---|---|
| Corrected gold drawing | K3 02:35–02:43, plus its entry and chart clock | Unobscured final target price, chart timezone, entry candle; separate identification of the first and second short. The mobile attachments do not supply these. |
| Alternative completed replay fixture | A 02:19:00–02:27:41, particularly 02:25:43–02:26:34 | Readable replay date/feed/timeframe, entry/SL/TP and event/zone labels. Caption references to Amsterdam and 1.4R do not supply the missing chart values. |
| Exact POI endpoints | K6 diagram; K7 03:19–03:35; D 12:21–12:54; F 03:00–03:36 | An unambiguous P annotation identifying the candle and wick/body boundary, together with the liquidity endpoint. |
| Deterministic BS threshold | A 01:07:49–01:08:30 and 02:25:40–02:26:15 | The labeled opposing boundary and its originating candle, sufficient to distinguish gap edge from candle edge; a stated or repeated candidate-selection rule. |

On 2026-10-01 A was opened directly at **02:24:30** and playback was attempted.
The watch page loaded, but the video remained black/buffering. No replay chart
values were read. This is a playback limitation, not a new CAPTCHA claim or
evidence that the source is silent. The earlier complete available-caption
review remains valid. Complete fixtures remain **0**.

## Verification and limits

Corrected gold labels and the wick-to-wick gap reading received an independent
second visual check. Raw academy frames remain private research intermediates
and were not uploaded to the repository. The Entry & Poi media-export attempt
produced no downloadable file; the reviewed evidence is its rendered frames.
No new complete CSV/YAML fixture, fabricated candle, runtime rule change, or
all-video completion claim is included.
