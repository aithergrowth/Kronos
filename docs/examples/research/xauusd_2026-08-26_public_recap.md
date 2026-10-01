# Gold scalp — source drawings, incomplete fixture

Source: [K3, academy lesson](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411), *Goud scalps, liquiditeitsruns en twee shorts*.
Chart date 2026-08-26. Confidence: **medium** for drawn prices; **high** for
captioned scalp qualification. This is not a verified broker execution record.
A fixture may describe a source-verified illustration without broker fills;
its labels and timestamps must still be established. The remaining chart and
candle-data gaps below keep this record incomplete.

At 00:39–00:43 he qualifies the higher-timeframe emphasis; see the workboard
conflict log. At 01:45 the chart is FOREXCOM:XAUUSD, 4H. At 02:34 it is 1m and
shows a short-position tool: entry **4624.53**, stop **4636.61**, target **4605.28**.
The tool independently displays stop distance 12.08, target distance 19.25 and
RR 1.59. These are an **intermediate drawing state**, not the final trade.
At 02:35–02:41 he extends the illustrated target and says his actual stop was
higher. The 02:37 frame shows target distance 20.88 and RR 1.73; its target-price
axis label is obscured. No missing price has been calculated and presented as a
chart reading. The YAML therefore has **no `expect` entry/stop/target fields**.

Raw academy frame omitted from the PR; verify the timestamp in the linked lesson.

Readable local labels: 2026-08-26 12:00 (4H crosshair), 2026-08-26 14:45 and
26 15:39 (drawing/crosshair labels on 1m). They do **not** prove execution times.
The academy recording's timezone is obscured; the separate public S5 recording
shows UTC-4 and must not silently define K3’s clock.

Data needed: FOREXCOM:XAUUSD 4H context and 1m entry detail around the shown date.
Exact UTC interval, formal POI classification and event candles remain unresolved.
The visible 4H-to-1m sequence does not by itself prove a permitted 4H-POI/1m-BS
combination. Do not turn the drawing's far-right endpoint into a target-hit time.
No candle CSV was fabricated. Readable drawing labels are preserved only under
`illustrated_position_states`, explicitly separate from final execution.

Public playback captions were reviewed continuously through the 04:05 end;
audio was not independently verified. At 00:37–00:47 he qualifies this scalp as
different from his normal approach. At 03:24–03:51 he explains a second short
after liquidity and a shift. Two described trades do not prove a second entry
on the same formally defined, previously visited POI.

## Focused correction check — 2026-09-30

At **02:40**, the corrected drawing directly shows entry **4624.53**, stop **4639.55**, stop distance **15.02**, target distance **29.55**, and RR **1.97**. These labels received an independent second visual check (medium confidence). The target axis price and chart timezone remain behind the recorded webcam; only `17:23…` of the recording clock is readable. That clock is not an execution timestamp. The separate **4629.48** label is the crosshair.

Later frames at 02:43, 02:57, 03:08, 03:20 did not resolve the missing target price/timezone. The latest corrected state is now preserved alongside the earlier, superseded states; no expected target price is invented from subtraction. See [the focused audit](../../DORUS_FOCUSED_AUDIT.md). The fixture remains incomplete.

## Lesson attachment check — 2026-10-01

The same K3 lesson contains two additional chart images. Their readable labels
received an independent second visual check; confidence is **medium**. These are
separate chart observations, not replacements for the FOREXCOM drawing.

| Lesson attachment | Displayed symbol / timeframe | Phone clock | Green chart quote | Readable chart-axis labels |
|---|---|---|---:|---|
| `IMG_3573.PNG` | `XAUUSD.pro` / M1 | 17:02 | 4602.10 | 26 Aug 16:42; 17:14; 17:46; 18:18 |
| `IMG_3574.PNG` | `XAUUSD.raw` / M15 | 17:03 | 4596.58 | 25 Aug 21:00; 26 Aug 14:00; 26 Aug 22:00 |

Marker connectors are visible, but neither image supplies a readable order
ticket, stop, target or numeric fill. The green quotes cannot be assigned as
entry fills, exit fills or TP prices. The readable labels also do not associate
either image with the corrected first short at K3 02:40.

Neither attachment establishes a readable year, chart timezone or broker name.
The phone clocks are not chart candle clocks or execution timestamps. Preserve
`XAUUSD.pro` and `XAUUSD.raw` separately; do not substitute FOREXCOM or transfer
the public S5 recording's UTC-4 clock. No uncertain axis tick is recorded.

The sourced observations are in the YAML under `lesson_attachment_observations`.
Raw academy attachments remain excluded from the repository. No `expect` fields
or CSV were added; `regression_ready` remains false.
