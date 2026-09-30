# Dorus source check — four requested follow-ups

Reviewed 2026-09-30. This supplements `ASTRA_TASKS.md`; it does not change the
trading code. The implementation was read at `feature/kronos-trader` commit
`dd79d29cda7b569f41b4e5dff62804de8eb72392`.

| Requested item | Result | Confidence |
|---|---|---|
| Gold, 26 August: corrected entry/SL/TP and clock | Corrected drawing entry and stop recovered; target distance/RR readable. Target-price label and timezone remain obscured. No complete fixture. | Medium for visual labels; unassessed for missing values and broker fills. |
| Liquidity and trading-plan priority videos | No readable primary-source transcript or independent official recording located. Existing YouTube browser block remains unresolved; neither video newly reviewed. | Not assessed for their contents. |
| Entry & POI: exact zone endpoints | The bearish **gap** is visibly wick-to-wick. The full **POI** endpoint and P boundary are not determined by that frame or the inspected line sketches. | Medium for the gap diagram; not assessed for a complete POI rule. |
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

Still needed: an unobscured final target label or explicit execution record;
verified chart timezone and entry candle; formal POI timeframe, sweep/break
identities and zone bounds; and real candle data covering the required interval.
The displayed 4H context and 1m entry drawing alone do not establish a valid
4H-POI/1m-confirmation case under K1. A completed gold fixture has not been claimed.

## 2. Priority recordings

| Video | Current evidence/access result |
|---|---|
| `81LThMAtj5o` — *Mijn Winstgevende Tradingplan Waarmee Ik Elke Dag Trade* | Existing unusual-traffic verification blocked the browser after its allowed reload. No further YouTube retry, proxy or alternate endpoint was used. No independent creator-published transcript/recording found. |
| `F5ciF74Uzr8` — *How to Trade Liquidity (Like a Pro)* | Earlier transcript panel did not load. The subsequent site-wide browser block remains applicable. No independently verified creator-published transcript/recording found. |

The academy [Liquiditeit](https://www.skool.com/dorusview/classroom/1924b124?md=d0e255d8877e47bbb6812849b56b41a5)
and [Tradingplan](https://www.skool.com/dorusview/classroom/1924b124?md=0eb0cc9b327e47db845b3fcfb4b64f83)
lessons are known sources. Their identity with the two YouTube videos has **not**
been established. A third-party transcript compilation surfaced in search but
was excluded because provenance/creator authorization could not be verified.
Titles, promotional pages and snippets do not count as video review.

Continuation requires accessible authorized recordings or Dutch captions for
those exact videos, or resolution of the existing browser verification block.

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

**Code conclusion:** the current `poi_far_edge="gap_bottom"` is still an
implementation choice. In `poi.py`, it means `gap.low` for a bullish POI and
`gap.high` for a bearish POI; the name does not mean the numerically lower edge
in both directions. This inspection does **not** verify that setting, nor the
choice of sweep-wick extreme rather than swept liquidity level at the other end.
No readable P annotation in the inspected frame establishes P's wick/body bounds
or its deterministic candle index.

## 4. BS: what can be confirmed for the function

Source **A**: [Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)](https://www.youtube.com/watch?v=HRPgdK8VhMc),
published 2026-02-18. These findings use the already retrieved Dutch automatic
captions; this follow-up did not bypass the current YouTube block.
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
algorithm** for every case. In particular, the existing `confirmation.py` selects
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

## Verification and limits

Corrected gold labels and the wick-to-wick gap reading received an independent
second visual check. Raw academy frames remain private research intermediates
and were not uploaded to the repository. The Entry & Poi media-export attempt
produced no downloadable file; the reviewed evidence is its rendered frames.
No new complete CSV/YAML fixture, fabricated candle, runtime rule change, or
all-video completion claim is included.
