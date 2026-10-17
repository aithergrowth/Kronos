# Dorus's course against the code, rule by rule

Source: his 4.5-hour course "Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)" (YouTube HRPgdK8VhMc,
transcript "A" in this project's notes; the transcript itself stays outside the repository). Times are video times.
Read on 2 October 2026 against the second edition of the pure profile (`config/dorus_pure.yaml`, the frozen phase 2 run).
"Match" means the code already does what he says; "programming gap" means the code's model was narrower than his words;
"profile" means a setting that the words settle; "open" means his words do not settle it.

| # | Topic | What he says (video time) | What the code did | Verdict | Now |
|---|---|---|---|---|---|
| 1 | Market structure | Break of structure = trend continues; break of the previous higher low / lower high = break of market structure, change of character, reversal (14:06-16:50) | Body-close breaks, kinds BOS and BMS | match | - |
| 2 | Liquidity | Highs and lows are where stops rest; price moves from one pool to the next, "van het ene stuk naar het andere stuk" (22:15-25:55); a plain break of a high is often a sweep, not a reversal (47:03-48:22, 1:04:27-1:05:33) | Liquidity levels from swing highs/lows; sweeps wick-only (Max's rule); targets on liquidity | consistent; the wick-only sweep algorithm is ours | - |
| 3 | Fair value gap | Three candles; the gap runs from candle 1's wick to candle 3's wick ("vanaf de eerste candle, dus de bovenste ... naar de derde candle", 52:08-52:30); drawn as an orange box | Gap between candle 1 and candle 3, wick to wick | match | - |
| 4 | A used gap | A wick into the gap means it was already retested; fully through means nothing is left (33:13-33:56); a partial fill is enough for a reaction (38:40, 41:00) | `mitigated` when price re-enters, only the first return traded | match; what counts as "used" after a partial touch stays ours | - |
| 5 | Balance level and POI | Identified like a FVG, used differently: price wants to balance it; the full POI runs to the low and the stop goes under it (36:35-37:26); "Een POI is het gebied tussen je X en B/P" (2:15:09) | Zone from X (the liquidity the displacement took) to P | match | - |
| 6 | P | "De P is de candle die uiteindelijk de fair value gap heeft veroorzaakt" (1:41:51); "de candle die het gat heeft veroorzaakt" (1:46:20, 2:27:20) | P = candle 2 (the impulsive candle), its far extreme | match; Astra's "P always candle 2" is now sourced | - |
| 7 | Bias per timeframe | Liquidity and balance levels must agree; one bullish and the other bearish or 50/50 gives 50/50 (56:54-57:18, 2:03:37-2:04:02) | `timeframe_bias`: aligned or 50/50 | match | - |
| 8 | Bias 3 of 5 | Matches: M+W+D, M+D+4H, W+D+4H, M+D+1H; D+4H+1H for a scalp only; "alle andere varianten is geen match" (2:03:11-2:03:35, 2:14:01-2:14:20); worked example M, D and 4H bullish "betekent dus een match" (1:42:44-1:43:10) | Second edition: M+D+4H off, because Max's written list did not carry it | profile error | `extra_combos_enabled: true` in the third edition |
| 9 | Where to trade | "Ik trade nooit naar een POI toe. Ik trade altijd van een POI af" (1:18:40); between two POIs you wait (1:59:28-2:00:00, 2:07:33-2:08:58) | A signal needs price inside an active zone of the bias side | match | - |
| 10 | The shift | Price takes liquidity, then shows a balance shift on the lower timeframe; the first shift level is the nearest opposing gap, the next one if that fails (1:19:22-1:20:46); a close is required: "Ik vind het wel belangrijk dat we een closure hebben" (2:26:10) | Balance shift = close beyond the opposing gap that formed up to the touch; gaps left inside the zone during the visit were ignored | programming gap | the level to clear is the most recent opposing gap at that moment (commit 7ed54e0) |
| 11 | Shift threshold | Beyond the gap: "sterk genoeg om boven dit balance level uit te komen" (54:55, 1:31:52, 2:25:46); beyond the candle that caused it (1:07:49-1:08:34) | `bs_threshold` gap_edge, protector as option | both readings exist in his words | gap_edge kept; protector stays an option |
| 12 | BMS / BOS as confirmation | The written list names BMS; the course calls the standard break a trap: "daar maak ik ook niet zo heel veel gebruik van" (1:29:29), "Het is een liquiditeitssweep" (1:33:47), "Ik plaats meestal trades gebaseerd op een balance shift" (1:30:56) | BMS always accepted, BOS off | interpretation with source | `allow_bms` switch; off in the third edition |
| 13 | First candle | "na de shift ga ik altijd bij de eerste beste bullish candle erin" (1:21:00); listed as a way in (1:30:31) | Off in the second edition (entry timing, not a confirmation) | match | - |
| 14 | Entry timeframe | HTF = M, W, D, 4H; LTF = 1H down to the 1m, "entries doen we vanaf de 1 minuut" (1:12:34-1:13:08); 1m for a 4H zone (42:37), 15m and 5m for a 4H zone (1:27:20-1:27:40), 1H for a daily zone (1:04:24-1:09:00) | The written table (Monthly 4H, Weekly 1H, Daily 15m, 4H 5m, 1H 1m) as the lowest allowed timeframe; no 1m candles in the phase 2 runs | coverage gap in the runs; the table is the written rule | 1-minute cache built; runs R1-R3 use it; going below the table (1m for a 4H zone) stays off |
| 15 | Stop | "Stop los op de P" = the candle that caused the gap of the zone: the daily P for a daily zone (1:08:49-1:09:03); the 1H P is the minimum, the daily P chosen "om het volledige idee te beschermen" even at 0.73R (1:46:17-1:47:02); "op de protected" (2:27:15) | The most recent unviolated 1H balance level since the touch (the minimum) | interpretation with source | `stop_protection: poi` in the third edition (`recent_1h` kept) |
| 16 | R:R | "een aantrekkelijke risk reward ... boven de 0,5" from his 70 % win rate (1:44:00-1:45:07); 0.73R placed (1:46:45); he prefers 1R-2R (1:28:01, 2:26:41) | 0.7 | profile | 0.5 in the third edition |
| 17 | Take profit | Always on liquidity, decided before entry, the full scenario to the next pool, "echt de highs en de lows", not local liquidity, no partials (1:48:50-1:52:45, 1:54:49, 1:57:07) | `liquidity_nearest` with the 1H floor, no partials | match | - |
| 18 | Session | Entries 9-11 and 13-17 Amsterdam, 11-13 quiet, nothing at 17:00 (1:26:44-1:27:04, 2:24:07, 2:30:56-2:32:06) | Same windows | match | - |
| 19 | News | Not right before high-impact news; prop-firm rules; "ik ga niet 1 minuut voor nieuws traden" (1:21:26, 2:00:04-2:01:06) | 30 minutes either side | match; the minutes are ours | - |
| 20 | Exits | Intraday and scalp: break-even at 4R, no partial; swing: 2R, no partial (2:15:31) | Same | match | - |
| 21 | Bad conditions | Against the HTF bias, between POIs, news (1:58:37-2:01:06) | Bias gate, zone gate, news gate | match | - |
| 22 | Monthly | Monthly balance levels from years back matter (57:31-57:49, 1:14:49-1:15:36) | Monthly in bias and POIs | match | - |
| 23 | Backtesting | At least 100 trades, a mechanical plan, journal every trade, start at 09:00 (2:12:32, 2:19:21, 2:31:20, 2:34:01) | - | process | the practice material in `docs/practice/` |
| 24 | Win rate | "Ik heb een gemiddelde winrate van 70 %" (1:44:08); the minimum R:R follows from the win rate, 0.4-0.5 at 70 % (1:44:13-1:44:41; D 11:13: 0.67 at 60 %) | 35 % in R6, 28-33 % in the other runs: break-even R:R 1.84 against a median planned 1.27 | gap in results, not in rules | `docs/WINRATE_DORUS_vs_CODE.md` |
| 25 | Target distance | "Mijn keuze gaat eerder naar één of twee risk reward ... omdat je een hogere winrate hebt" (1:28:01); the target brought closer "zolang het risk-reward-wijs aantrekkelijk blijft" (1:28:18); "op de vorige 1H high" (H 9:14) | The nearest 1H+ liquidity whatever its distance: planned R:R above 2 won 12 % (81 trades in R6) | his stated preference, not applied | `risk.tp_max_rr`, `tp_cap_choice` |
| 26 | Stop room | "Kan je je stoploss nog wat ruimte geven ... kijken naar de linkerkant, wat wil ik beschermen?" (31:17-31:29); his entries sit at the zone's edge (`docs/dossiers/SOURCE_TRADES.md`) | Stop on the zone's P with no offset, the entry wherever the 1m shift closed: 29 stops under 5 pips, one won; entries deeper than half the zone 48 trades, 12 % | interpretation, data-supported | `risk.max_entry_depth` |
| 27 | Re-entry on a stopped zone | Not stated; no recap of his shows a second entry on a zone that stopped him out | A zone stays valid after a stop-out at its P (a violation needs a close on the zone's timeframe) and was re-entered on the next shift: 46 trades, 9 % won, -23.7R | interpretation, data-supported | `confirmation.one_trade_per_visit` |

## What changed in the code (programming), all tested

- The balance shift clears the opposing balance level that is current at that moment, including one left inside the zone
  during the visit (row 10). The old model knew only the gap that drove price into the zone.
- `confirmation.allow_bms` (row 12) and `risk.stop_protection` (row 15) exist as switches; defaults unchanged.
- A backtest that walks 5-minute candles with 1-minute candles loaded tells the engine its step, so a 1m shift that closed
  up to four minutes before the step still counts; the fill is at the step's close (row 14).

## What changed in the profile (interpretation with his words as source)

`config/dorus_course.yaml`, third edition: M+D+4H on (row 8), BMS off (row 12), stop on the zone's own P (row 15),
minimum R:R 0.5 (row 16). Everything else as in the second edition. Each line carries its timestamps.

## Still open (his words do not settle it)

The size below which a three-candle gap is ignored; when a visit ends; the zone's outer edge when X sits inside the gap;
whether a wick through P ends a zone; a liquidity take right before the shift as a hard requirement (he wants it, 1:19:22,
but every pullback into a zone makes a new low, so a rule needs a definition of "the" liquidity); 1m entries for zones
above the 1H (he does it, the written table does not).

## Runs

Started 2 October 04:17 UTC on commit `7ed54e0`, 2023-03-01 to 2026-09-25, bid quotes, 5-minute steps, prop-firm halt lifted:
R1 second edition with 1-minute candles (EURUSD), R2 third edition with 1-minute candles (EURUSD), R3 third edition with
1-minute candles (XAUUSD), R4 third edition on the 5-minute cache (EURUSD). R1 against the frozen run isolates the
1-minute coverage; R4 against R2 isolates it again under the new rules; R2 against R1 isolates the rules. Results go to
`docs/backtests/course/`.
