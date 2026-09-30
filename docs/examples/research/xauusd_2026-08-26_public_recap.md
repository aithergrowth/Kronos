# Gold scalp — source drawings, incomplete fixture

Source: [K3, academy lesson](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411), *Goud scalps, liquiditeitsruns en twee shorts*.
Chart date 2026-08-26. Confidence: **medium** for drawn prices; **high** for
captioned scalp qualification. This is not a verified broker execution record.

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
