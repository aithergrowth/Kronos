# EURUSD short of 11 November 2025: Dorus's trade against the code

Source: Max's screenshots of Dorus's recap (FXCM EURUSD 5m and 1H, TVC DXY 5m; chart clock UTC+1; the images stay outside
the repository). His trade: short EURUSD in the 16:00 Amsterdam hour (15:00 UTC) of Tuesday 11 November 2025, entry
1.15963, stop 1.16060, target 1.15687 (the 1H position tool: 9.7 pips risk, 27.6 pips reward, 2.85R; a second ticket on the
5m chart: entry about 1.1593, stop 1.16056, target 1.15681, 1.98R); closed at the target on 12 November. The mirror on
DXY: a long from a 5-minute balance level after the sweep of the 99.37 low, stop 99.287, target 99.598. On our HistData bid
candles his entry prices traded between 15:06 and 15:16 UTC.

Dossiers in this folder: `2025-11-11_15_05`, `_15_10`, `_15_15` (course profile, before today's fixes) and the two `_strict`
ones (exact table, entry outside the zone allowed, before the search fix). The numbers below come from the minute-by-minute
walk-through (`scripts/minute_walk.py`) on the final code of this commit, 1-minute data, 3-day warm-up, diagnostic direction short.

## What the engine saw

**Bias refuses.** 1M 50/50 (liquidity bearish: the 1.19092 high swept; balance bullish: last gap 1.0955-1.1065), 1W 50/50
(BMS through 1.15420 bearish; bullish gap 1.1615-1.1708), 1D 50/50 (BOS through 1.15420; bullish gap 1.1498-1.1530), 4H
bullish, 1H bullish after the 13:30 UTC spike. No three timeframes agree, so no trade. Dorus was short with the monthly,
weekly and daily bearish, read from the dollar index: the course video (A 56:17-1:02:00, recorded in this period: "op dit
moment zit ik in DXY long ... EURUSD short") shows the DXY monthly, weekly and daily balance levels tested and holding.
EURUSD's own chart has price inside bullish weekly (1.1454-1.1708) and daily (1.1392-1.1597) balance levels, which is what
the code reads. Not a programming error: a cross-market reading his written plan does not contain. It is the one gate that
would have kept the code out of this trade.

**Zones match.** A 4H bearish zone 1.15853-1.16283 (formed 30 Oct 13:00, touched 7 Nov 15:21, re-entered by the spike of
11 Nov 13:22) and a 1H bearish zone 1.15967-1.16111 (formed 30 Oct 12:00, touched 11 Nov 13:26). His entry 1.15963 sits
0.4 pip under the 1H zone's edge, inside the 4H zone.

**Confirmation: two programming gaps, fixed in this commit.** Before: the balance-shift search started at the visit's first
touch (7 November) and ended at the first close beyond an old gap on 10 November, when price was below the zone; and a zone
price had just left (status tested, or fresh while the zone's own candle was still open) was no candidate. Now the search
starts at price's latest re-entry into the zone, gaps crossed before that window count as crossed, and with
`entry_outside_zone` the visit tracker decides. Result at 14:15 UTC: a short from the 4H zone, entry 1.15975, stop 1.16057,
target 1.15468, 5m balance shift at 14:10 (close 1.15975 under the 14:00 bullish gap 1.15979-1.16006), R:R 5.5. Dorus about
an hour later: entry 1.15963, stop 1.16060. A first 1m shift on the 1H zone at 13:49 would have entered at 1.15938 with the
stop at 1.16017, the high so far, and been stopped by the 1.16057 print minutes later; whether he took that one too is not in
the recap.

**Stop.** With `stop_basis: confirmation` (the extreme since the re-entry) the code's stop is 0.3 pip from his. With the
zone's own P it is 1.16283, 32 pips away; the most recent 1H P would be the same here. His three intraday examples (the two
gold shorts, this one) put the stop just beyond the sweep extreme; his two swing examples in the course put it on the zone's
P. Which is the rule stays open; R6 (zone's P) and R7 (sweep extreme) measure both.

**Target.** The nearest 1H liquidity below gave 1.15468, the Asia low; his target was the low before the impulse, 1.15687,
hit on 12 November 09:00. The code's target was not reached by the end of our 12 November data.

## In short

| Step | Dorus | Code after this commit | Difference |
|---|---|---|---|
| Bias | M, W, D bearish from DXY | M, W, D 50/50 on EURUSD's own levels | information, not a rule |
| Zone | at the 1H zone's edge, inside the 4H zone | the same two zones | none |
| Shift | second 5m shift, about 15:10 UTC | 5m shift at 14:10 (first after the re-entry) | timing |
| Entry | 1.15963 | 1.15975 | 1.2 pips |
| Stop | 1.16060 | 1.16057 (sweep extreme) or 1.16283 (zone's P) | which P is the rule |
| Target | 1.15687 (pre-impulse low) | 1.15468 (Asia low) | which liquidity is "the previous low" |
