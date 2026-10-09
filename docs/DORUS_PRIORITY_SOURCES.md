# Priority sources — restored access and new rule evidence

Reviewed 2026-09-30. This update supersedes the earlier access-block status in
`DORUS_FOCUSED_AUDIT.md`. All available **Dutch automatic captions** for the
three sources below were reviewed end-to-end, with a second independent read.
This is not independent audio verification or a complete visual review.

| ID | Exact source | Published | Caption coverage |
|---|---|---|---|
| D | [Mijn Winstgevende Tradingplan Waarmee Ik Elke Dag Trade](https://www.youtube.com/watch?v=81LThMAtj5o), currently displayed in English as *My Profitable Trading Plan With Which I Trade Every Day* | 2026-05-01 | 419 segments, 00:00–16:23; player 16:25 |
| E | [How to Trade Liquidity (Like a Pro)](https://www.youtube.com/watch?v=F5ciF74Uzr8) | 2026-09-02 | 391 segments, 00:00–14:13; player 14:15 |
| F | [How to Use Fair Value Gaps to Find Better Trades](https://www.youtube.com/watch?v=O6IgD2llrq0) | 2026-09-28 | 288 segments, 00:00–10:26; player 10:28 |

Dates were read in the expanded video descriptions. E initially exported an
English automatic-caption track; the Dutch track was then explicitly selected
and retrieved. Only the Dutch export supports this update. E 00:42–01:10 and
F 00:27–00:40 say their material comes from the free community; identical edits
or timestamp offsets with the academy recordings have not been established.

## POI: liquidity to protection, with numerical endpoints still open

**D 12:21–12:54, high confidence:** the buying area runs between liquidity and
protection. Buying interest ends below P; P is the candle that caused the gap.
The short Dutch caption excerpt at 12:42–12:48 is:

> wanneer die onder de P komt

The earlier caption at 12:01 renders the second label as B; the later explanation
explicitly names P. Neither passage specifies wick versus body, the exact candle
index, whether penetration or a candle close invalidates the zone, or which
invalidation timeframe applies. Loss of buying interest is not automatically a
50/50 bias reset.

**F 03:00–03:36, high confidence:** the POI starts at liquidity. It can react
just inside the area, midway, after filling the gap, or deeper at protection.
At 03:07–03:09:

> begint ten alle tijden bij het punt van liquiditeit

**Historical implementation comparison, explicitly an inference (dd79d29):** the then-current
`map_pois` bounds are `sweep.extreme` and a selected gap edge. With `gap_bottom`,
the bullish interval is `[sweep.extreme, gap.low]`; the bearish interval is
`[gap.high, sweep.extreme]`. These do not explicitly use the two objects Dorus
names: the liquidity level and protection. They should no longer be described
as a source-confirmed full POI. A gap-only cutoff can omit the deeper protection
scenario; substituting the piercing wick for the liquidity point also needs
justification. This does not establish the exact replacement OHLC formula.

Changing only `poi_far_edge` to `protector` is not a verified repair: that mode
still retains `sweep.extreme` and uses protector-high for bullish or protector-low
for bearish. The source does not establish that pair of endpoints.

**Code follow-up, 2026-10-01:** Claude's `d008dac` replaces that default with
liquidity-to-protection, retains the old mapping as legacy, enables M+D+4H and
adds selectable BS thresholds. The historical mismatch above describes the
earlier code. The new P far-wick boundary, P candle index, displacement window
and exact BS candidate/edge still require chart evidence; this source audit
does not independently validate those implementation choices.

The requested K6 *Entry & Poi* frame establishes the local bearish gap's wick
geometry, not the full POI. A further academy **K7** check —
[Balance levels](https://www.skool.com/dorusview/classroom/1924b124?md=074a2908adac42c7b6c6a2d68aff4da8),
**03:19–03:20** — shows a lower horizontal line meeting the first drawn candle's
**lower wick**, below its body. X and B are readable; **P is not labeled** in that
frame. Medium visual confidence, independently checked. This observation alone
cannot establish that line as P or a universal zone endpoint. No academy/YouTube
timestamp conversion is assumed.

## Answers strengthened by the trading-plan source

All entries below have **high confidence for the captioned statements**;
implementation details listed as unresolved remain unverified.

| Question / concept | Source | Finding and limit |
|---|---|---|
| Balance | D 03:05–03:41; F 00:58–01:42 | Three-candle gap, identified like an FVG; distinct from its origin candle. No universal active-gap selection rule. |
| Valid bias combinations | D 01:05–01:43 | M+W+D, **M+D+4H**, W+D+4H, M+D+1H; D+4H+1H is scalp only; other combinations fail. |
| Opposing votes | D 01:05–01:43 | Does not explicitly answer the exact M/W/D-bullish, H4/H1-bearish hypothetical. |
| Scalp permissions | D 01:31–01:42; 14:56–15:17 | Scalp uses lower timeframes; no exact scalp-only POI subset or special session filter stated. Exit categories match K1. |
| First-candle confirmation | D 13:48–14:01 | Listed alongside BS and BMS; BS preferred. Exact first-candle eligibility still unspecified. |
| Stop / target / risk | D 13:22–13:45 | One trade per funded account, 1% risk, minimum H1 P for stop and liquidity-area target, subject to acceptable RR. No fixed pip buffer or deterministic liquidity tie-break. |
| Minimum RR | D 11:01–11:34 | Hypothetical 60% win rate gives 0.67 minimum RR. This is neither his measured win rate nor a project threshold; it contradicts attributing a universal 3R minimum to him. |
| Confirmation matrix | D 13:10–13:20 | M→4H BS; W→1H BS; D→15m BS; 4H→5m BS; H1→1m BS. |
| Break-even / exits | D 14:56–15:27 | D/4H/H1 POIs: 4RR; M/W POIs: 2RR; no partials. Record TP/BE/SL outcome and journal. |
| Daily process | D 15:25–15:38 | Bias → POI → entry → exit; journal the trade. |

**Combination conflict retained:** D's dated M+D+4H statement reinforces A's
previously recorded examples. K1's inspected written table omits this combination,
and its publication date is unknown. Do not silently treat either source as
superseding the other. Claude's disabled extra-combination switch remains unchanged.

**Narration inconsistency:** D 08:45–08:52 calls H1 decisive after M bullish,
W bearish, D bearish and H4 bullish. Neither possible directional H1 result would
complete one of D's listed combinations. The actual H1 conclusion is 50/50 and
the actual outcome is no trade (09:21–10:28). Do not invent an additional valid
combination from the earlier remark.

## BS and liquidity: what these sources do not resolve

D **14:03–14:38** reinforces the difference between overcoming opposing balance
and a plain BMS that may only take liquidity. It does **not** explicitly supply a
close rule or precise boundary. A's 02:25:40–02:26:15 and 02:30:39–02:30:56 remain
the close evidence. Latest-gap choice, lookback length, gap edge versus origin
candle, mandatory retest and numerical expiry remain unresolved.

E **00:20–00:25** describes liquidity as orders/stop-losses on the chart;
**03:31–03:39** uses X; **05:21–06:51** and **07:29–08:17** cover consolidation
and pattern examples. High confidence for the captioned descriptions. No
wick-only sweep, mandatory close back inside, or minimum penetration is stated
in its complete available captions.

D/E/F add no verified candle anchoring, one-pip buffer, same-zone second-return
rule, Kronos veto, or approval-expiry number. Their absence here is not proof
that Dorus never states them elsewhere.

## Chart leads and remaining work

| Source passage | Candidate | Still missing |
|---|---|---|
| D 03:48–10:28 | Rejected setup: M bull, W bear, D bear, H4 bull, H1 50/50 | Instrument/feed, chart date/clock, actual zone/event candles, candle data. |
| E 09:00–11:19, especially 09:53–10:12 | BTC short, weekly chart context, claimed still open | Readable orders, formal POI frame, feed, historical interval and UTC clock. The ambiguous caption “124” is not a chart price. |
| F 06:48–08:23 | BTC gap/liquidity examples; Daily named at 07:58 | Dates, prices and execution metadata. |
| F 08:58–09:23 | Gold Daily example | Dates, prices and execution metadata. |

The requested D POI passage could not be visually inspected. Playback remained
black/buffering, including after one reload and playback attempt, despite
successful caption export. No chart values
are attributed to that unrendered frame. The additional academy diagram is a
schematic, not market OHLC data.

Gold K3's corrected labels remain as recorded in the focused audit; its final
TP price label and timezone have not been recovered. **Complete fixtures: 0.**
No runtime code, raw full transcript or raw academy screenshot is published.
