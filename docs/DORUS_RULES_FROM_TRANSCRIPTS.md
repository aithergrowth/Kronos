# Dorus's rules as he states them: the transcript pass of 1 October 2026

Read directly from the Dutch automatic captions of his YouTube videos (fetched with timestamps; the raw
transcripts stay out of the repository). Sources: **A** the 4.5-hour course (HRPgdK8VhMc), **B** strategy
walkthrough (xWR8M46iSW8), **C** A-Z (R07fGFejJ5w), **D** trading plan (81LThMAtj5o), **G** HTF context
(6NLVf8P-xP8), **H** entries (oe0tBQ47r3M). E and F could not be fetched this pass; Astra's reviews cover
them. The academy (Skool) needs a member login and is covered by Astra's screenshots only.

This pass answers the decisions that the diagnostic backtest showed to matter most. Each row gives the
quote, where it is, what the second pure profile (`config/dorus_pure.yaml`) now does, and what stays open.

| Decision | What he says | Where | Profile | Still open |
|---|---|---|---|---|
| Confirmation | "Opties qua confirmatie: een balance shift, een break of market structure, daar ben ik niet zo heel erg fan van, of de eerste bullish of bearish candle. Wat ik zelf meestal doe is dus een balance shift." | D 13:48-14:01 | balance shift and BMS on; BOS off (not in his list) | whether BMS should be off too ("niet zo'n fan") |
| First candle | "na de shift ga ik altijd bij de eerste beste bullish candle erin" | A 01:21:00 | first candle **off** as a confirmation: it is his entry timing after a shift | entering one candle after the shift instead of on its close |
| The shift needs a close | "Ik vind het wel belangrijk dat we een closure hebben. Dat hebben we nog niet... Ja, nu wel. Oké, dan kunnen we de trade erbij pakken." | A 02:26:00 | close through the opposing balance level (`bs_threshold: gap_edge`) | gap edge versus the origin candle (A 01:07:49) |
| Stop | "Stop loss op de P... de candle die dit gat heeft veroorzaakt. Dus daar wil je de stoploss onder zetten." "als je stoploss niet op de candle die het gat heeft veroorzaakt, dan ga je veel vaker stoplosses krijgen." "Stoploss altijd op een minimale 1 uur P" | A 01:08:10-01:09:30, D 13:30 | behind P, at least the 1H P, no buffer | exact wick of P |
| Target | "Dus ik zet ten alle tijden mijn take profit op liquiditeit." "dit is meer lokale liquiditeit. We willen uiteindelijk echt de highs en de lows meenemen." Replays: "take profit bij de vorige high" on the 1H chart, "op de vorige Asia high" on the 1H | A 01:50:40, A 01:54:49, A 02:26:10, H 09:00 | nearest liquidity above the confirmation timeframe **and at least on the 1H** | which previous high when several qualify |
| R:R | "Het is een 0,73 risk reward. Niet de meest spannende trade... maar wel een trade die precies volgens het plannetje is." "dan hebben we een 1,4 risk reward. Mogen we deze trade plaatsen." "Ik ben het meest gaan verdienen... doordat ik ben gaan focussen op de lage risk rewards. Dus op de consistentie, dus op de hogere winrate." | A 01:46:40, A 02:26:20-02:26:50, D 11:01 | floor 0.7 (his lowest accepted example; D's 60 %-win-rate arithmetic gives 0.67) | a higher floor is Max's choice, not his; the report shows the result per R:R band |
| Session | "ik mag alleen een trade executeren van 9 tot en met 11 en van 1 tot en met 5." "nu mogen we niet meer de trade plaatsen, want het is 5 uur." "Nu gaan we naar de zone met wat minder prijsactie. Dus wachten we even. Wachten we op 1 uur." | A 02:30:56, A 02:30:30, A 01:20:20 | entries 09:00-11:00 and 13:00-17:00 Amsterdam | H says 09-17 with 11-13 quieter; C says 08-17; the replay plan is the explicit one |
| News | "ik ga met nieuws traden niet 1 minuut voor nieuws traden. Dat doe ik niet. Maar... als ik een trade heb om 1:30, dan laat ik gewoon lopen tot het nieuws event." | A 01:21:20 | no entry 30 minutes before or after high-impact news; open trades run | his "after" window is not stated |
| Frequency | "Ik plaats gemiddeld, laat ik zeggen, 2 tot 8 trades per maand. Soms heb ik ook maanden dat ik misschien maar één of geen trade heb." | A 04:09:09 | not a rule; a check: the profile should land in this range across the traded markets | |
| Returns | "als jij 1 tot 2% per maand kan behalen op een consistente basis kan jij supergoed verdienen" | A 02:27:30 | the benchmark for the forward test | |
| Balance level | "vanaf de eerste candle, dus de bovenste... naar de derde candle. En het gat hiertussen, dit is voor ons het balance level." Price may react before filling it, in the middle, after filling it, or at the candle that made it | A 00:52:10-00:53:30 | gap between candle 1 and 3, wick to wick; zone from X to P | which of several gaps |
| Journal | "Heb je je aan je tradingplan gehouden... dit is dus buiten mijn tijdslot. Dus dit is een trade die eigenlijk niet volgens mijn strategie zou zijn." | A 02:31:10 | the journal records every rule check | |

## Why this matters for the numbers

The diagnostic run of the first pure profile (first candle on, no target floor, 09-17) made 397 trades:
202 of them were first-candle entries and they lost 35.7R, while balance-shift and BMS entries were
near break-even. Entries within an hour of the zone touch, which is what a first candle usually is, lost
56.7R; entries one to four hours after the touch made 14.6R. Targets on 15m swings lost; targets on 4H
and higher levels won. The second profile does not use any of those numbers: it follows the quotes above.
That the quotes and the numbers point the same way is the reason to expect the second run to differ.

## Not changed, still interpretation

X and P selection among nearby candidates, the 20 % gap threshold, first-return-only, the inside-zone
requirement for a confirmation, the 1.5-zone-height visit allowance, and the news "after" window. Each is
named in `config/dorus_pure.yaml` or `kronos_trader/config.py` as an assumption.

## Additions from the full read of the course (video A, 2 October 2026)

Rule by rule against the code in `docs/DORUS_COURSE_vs_CODE.md`. The quotes that settle something:

| Rule | Quote | Where | Effect |
|---|---|---|---|
| Bias combinations | "de monthly is bullish, de daily is bullish en de 4 uur is bullish. Betekent dus een match"; "monthly daily 4 hour ... is een match ... Alle andere varianten is geen match" | A 01:43:00, 02:03:11-02:03:35, 02:14:01-02:14:20 | M+D+4H on in the third edition |
| The shift level | "voor mij zit de eerste beste balance shift hier ... Nee, doet het niet. Gaan we wachten tot de volgende shift. Die zit hier" | A 01:20:33-01:20:46 | the most recent opposing gap at that moment (code) |
| The shift needs a close | "Ik vind het wel belangrijk dat we een closure hebben. Dat hebben we nog niet ... Ja, nu wel" | A 02:26:10 | unchanged (body close) |
| Shift threshold | "sterk genoeg om boven dit balance level uit te komen" / "sterk genoeg om hierboven te komen. Dus de candle die dit gat heeft veroorzaakt" | A 01:31:52, 02:25:46 / A 01:08:22 | gap_edge default, protector option |
| Structure break alone | "de standaard break of structure ... daar maak ik ook niet zo heel veel gebruik van"; "De meeste mensen zien dit als een break of structure. Maar wat is het nou eigenlijk? Het is een liquiditeitssweep" | A 01:29:29, 01:33:47 | BMS off in the third edition |
| P | "De P is de candle die uiteindelijk de fair value gap heeft veroorzaakt" | A 01:41:51, 01:46:20 | candle 2, as coded |
| Stop | "Stop los op de P ... dit is uiteindelijk de candle die dit gat hier heeft veroorzaakt [on the daily]"; "ik heb altijd mijn regel minimaal op een 1 uur P ... Ik ga hem hierop plaatsen op de P [the daily one]. Het mag ook. Het is een 0,73 risk reward" | A 01:08:49-01:09:03, 01:46:17-01:47:02 | stop on the zone's own P in the third edition |
| R:R | "een aantrekkelijke risk reward ... boven de 0,5"; "Mijn keuze gaat eerder naar één of twee risk reward" | A 01:45:00-01:45:07, 01:28:01 | 0.5 in the third edition |
| Entry timeframe | "entries doen we vanaf de 1 minuut. Dus dan is het de 1 uur tot en met uiteindelijk de 1 minuut" | A 01:13:00-01:13:08 | 1-minute cache for the runs |
| Where to trade | "Ik trade nooit naar een POI toe. Ik trade altijd van een POI af" | A 01:18:40 | as coded |
| Fair value gap | "vanaf de eerste candle, dus de bovenste ... naar de derde candle. En het gat hiertussen, dit is voor ons het balance level" | A 00:52:08-00:52:30 | as coded |

