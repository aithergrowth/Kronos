# Win rate: what Dorus does, what the code did, and what changes

Max, 2 October 2026: "Hoe kunnen we de winrate omhoog krijgen? Ga onderzoek naar hoe Dorus dit doet. Het is te laag, want met
zo'n winrate moet onze risk reward echt goed zijn."  Two sources: his own words in the course and the clips (transcripts stay
outside the repository; timestamps given), and the ledgers of the course runs (`docs/backtests/course/`).

## 1. What Dorus says about win rate and R:R

| Source | What he says |
|---|---|
| A 01:44:08 | "Ik heb een gemiddelde winrate van 70 %." He then asks ChatGPT for the minimum R:R at that win rate: "ongeveer 0,4 tot 0,5". |
| A 01:45:00 | "Een aantrekkelijke risk reward? Dat is dus een R boven de 0,5." A 0.73R trade is placed at 01:46:45. |
| D 00:11:13 | "Een aantrekkelijke risk reward hangt af van de winrate bij jou. Stel jij een winrate hebt van 60 %, dan is de minimale risk reward 0,67. Dit is een rekensommetje die je als trader altijd moet berekenen." |
| A 01:27:57 / H 00:05:36 | "Ik ben niet zo fan van hele hoge risk-reward trades. Mijn keuze gaat eerder naar één of twee risk reward. Waarom? Omdat je een hogere winrate hebt." |
| A 01:28:18 | The target may be brought closer: "misschien kunnen we hem hier naartoe zetten, zolang het risk-reward-wijs natuurlijk maar aantrekkelijk blijft." |
| A 02:26:41 | On a 1.4R trade: "Ik ben het meest gaan verdienen doordat ik ben gaan focussen op de lage risk rewards. Dus op de consistentie, dus op de hogere winrate." |
| A 02:27:06 | "Het voordeel van een lage risk reward is: je beschermt meestal het gedeelte wat je moet beschermen." |
| B 00:09:42 | "We willen minimaal dit stuk eruit nemen. Dus dan hebben we minimaal 1,3. ... als je consistent voor die 1,3 R gaat, krijg je ook een hogere winrate." |
| A 01:50:40 | "Ik zet ten alle tijden mijn take profit op liquiditeit"; the full scenario "van het ene stuk naar het andere stuk" (01:50:31). |
| A 01:54:47 | "Take profit bij het vorige liquiditeitsgebied ... we willen echt de highs en de lows meenemen", not "lokale liquiditeit". |
| H 00:09:14 | Target "op de vorige 1H high. Dat is een mooi target." |
| A 00:31:17 | "Kan je je stoploss nog wat ruimte geven, wat je wilt. Wat ik zelf altijd fijn vind is om hier te kijken naar de linkerkant: wat wil ik beschermen?" |
| A 01:46:12 | "Ik wil hem minimaal op mijn P zetten ... ik heb altijd mijn regel: minimaal op een 1 uur P, oftewel de protector." |
| A 00:03:55 | "Ik mag trades executeren van 9 uur 's ochtends tot 5 uur 's middags. Alles daarbuiten mag ik niet." (The course later splits it 9-11 and 13-17, A 02:24:07.) |
| G 00:11:13 | News: "Ik ga niet 1 minuut voor nieuws traden", otherwise trades run through news. |
| H 00:11:01 | The plain break of structure is often a liquidity sweep; after a balance and a break of the balance level "kan je dus echt heel veel slechte trades eruit filteren." |

His arithmetic: at a 70 % win rate a 0.5R target is profitable; at our 35 % the break-even R:R is 1.84 and the code's median
planned R:R was 1.27.  Max's point is right.  Dorus does not solve it with a higher R:R: he solves it with the win rate, and
his win rate comes with low targets (the nearest previous high or low, 1-2R), stops with room, and entries limited to the
sessions.

## 2. What the R6 ledger shows (227 trades, 35 % won, -40.5R)

`scratchpad/winrate_analysis.py` on `docs/backtests/course/r6_course_strict_1m_eurusd.csv`.  n / win rate / sum of R.

| Cut | Bucket | n | Win | Sum R | Reading |
|---|---|---|---|---|---|
| Planned R:R | below 1 | 90 | 54 % | -4.1 | the near targets win half the time |
| | 1-1.5 | 35 | 34 % | -9.3 | |
| | 1.5-2 | 21 | 38 % | +1.8 | |
| | 2-3 | 30 | 13 % | -13.8 | |
| | above 5 | 31 | 6 % | -17.0 | far targets with tiny stops: 2 of 31 reached |
| Stop size | below 5 pips | 29 | 3 % | -15.5 | one win in 29; spread and noise take the stop |
| | 5-8 pips | 19 | 42 % | +5.2 | |
| | 12-20 pips | 56 | 43 % | -2.7 | |
| Entry depth in the zone | outside / at the edge | 102 | 46 % | -10.3 | |
| | 0-25 % in | 44 | 41 % | -5.2 | |
| | 50-75 % in | 26 | 19 % | +2.0 | |
| | 75-100 % in | 22 | 5 % | -22.2 | price has nearly gone through the zone; the P is 2-5 pips away |
| Attempt on the zone | first | 169 | 43 % | -9.8 | |
| | after a stop-out on the same zone | 46 | 9 % | -23.7 | the stop sat on the P, so the P was traded through, and the engine re-entered |
| Target timeframe | 4H liquidity | 28 | 43 % | +13.9 | |
| | 1H liquidity | 166 | 39 % | -29.7 | |
| | 1D, 1W, 1M liquidity | 33 | 6 % | -24.6 | |
| Hour (Amsterdam) | 09-10 | 106 | 40 % | -12.7 | |
| | 13 | 40 | 38 % | -5.1 | |
| | 14-15 | 46 | 26 % | -23.1 | the US data window (14:30) and the New York open |
| | 16 | 35 | 31 % | +0.4 | |
| Touch to shift | under 15 min | 33 | 48 % | +4.4 | the immediate reaction |
| | over 24 h | 39 | 23 % | -21.0 | |

The same cuts on R1, R2, R4, R5, R7 and the gold run R3 point the same way: in every run the re-entries after a stop-out
and the entries deep in the zone win 0-17 %, and planned R:R above 2 wins 6-20 %.  A crude sweep test (the 1m price taking
out the previous four hours' extreme in the hour before the shift) does not separate winners from losers (30 % against
40 %), so "sweep before shift" is not added.

Post-hoc, keeping only first attempts, entries at most half the zone deep and planned R:R at most 2 gives, on the same
trades: R6 119 trades 54 % +6.5R (per year -0.7, +6.9, -1.7, +2.1), R2 29 trades 45 % +2.8R, R5 16 trades 44 % +1.3R,
R1 67 trades 45 % +1.7R, gold R3 36 trades 50 % -0.2R, R7 76 trades 41 % -7.4R.  Post-hoc selection flatters; the runs
below apply the rules inside the engine, where a skipped trade frees the account for the next one.

## 3. The rules added (commit after `2ae5ca8`)

| Rule | Setting | Source | Status |
|---|---|---|---|
| One trade per zone per visit | `confirmation.one_trade_per_visit: true` | the stop sits on the P ("minimaal op een 1 uur P", A 01:46:12); a stop-out means the P was traded through. Not stated by him in words; his recaps never show a second entry on a stopped zone | interpretation, data-supported |
| Entry at most half the zone deep | `risk.max_entry_depth: 0.5` | "kan je je stoploss nog wat ruimte geven" (A 00:31:22); his entries sit at the zone's edge (trades 3 and 5 in `docs/dossiers/SOURCE_TRADES.md`) | interpretation, data-supported |
| R:R cap at 2 with a nearer liquidity level | `risk.tp_max_rr: 2.0`, `tp_cap_choice: nearest` or `farthest` | "één of twee risk reward" (A 01:28:01), the target brought closer "zolang het aantrekkelijk blijft" (A 01:28:18), "de vorige 1H high" (H 09:14) | his stated preference |
| No entries 14:00-15:59 Amsterdam | `session.windows` | not his; the 14-15 hour loses in every run (R6 -23.1R, R1 -24.6R, R7 -48.2R) | data only, kept separate |

The runner and the live loop tell the engine which zone they traded (`StrategyEngine.mark_traded`), so a signal the guard
refused does not retire a zone.  The engine rejects a second signal on a traded zone with "already traded on visit #n".
With the cap, the ledger's `tp_source` names both levels ("5m buy-side liquidity ... [nearer than 1H ... at 1:4.3; R:R
cap 2.0]").

## 4. Runs

EURUSD 2023-03-01 to 2026-09-25, HistData bid 1-minute candles, 5-minute steps, 1 % risk, prop-firm halt lifted, the
strict reading of R6 as the base (`config/dorus_course.yaml` + table exact + entry outside the zone).

| Run | Adds | Trades | Win rate | Expectancy | Total | 2026 only (n / win / sum) |
|---|---|---|---|---|---|---|
| R6 (base) | - | 227 | 35 % | -0.18R | -40.5R | 36 / 33 % / -6.8R |
| R10 | one trade per zone per visit | 177 | 42 % | -0.08R | -14.9R | 28 / 39 % / -1.1R |
| R11 | + entry at most half the zone deep | 165 | 44 % | -0.04R | -6.8R | 26 / 46 % / +5.3R |
| R8 | + R:R cap 2.0, nearest fitting liquidity | 163 | 47 % | -0.05R | -8.5R | 26 / 46 % / +2.1R |
| R8b | + R:R cap 2.0, farthest fitting liquidity | 164 | 46 % | -0.06R | -10.4R | 26 / 46 % / +2.1R |
| R9 | R8b + no entries 14:00-15:59 Amsterdam | 158 | 46 % | -0.05R | -7.1R | 26 / 50 % / +4.3R |

Ledgers, equity series, provenance and the reading: `docs/backtests/winrate/README.md`. In short: the win rate rises from
35 % to 42-47 % and the loss shrinks from -40.5R to -7R to -15R, but no run is positive over the whole period; 2024 wins,
2025 loses, 2026 is slightly positive from R11 on. What still loses is stops wider than 20 pips (the zone's P far from a
1m entry), longs, and daily-or-higher targets. The source-trade suite (`docs/dossiers/SOURCE_TRADES_SUITE.md`), built
after these runs started, found the larger gap: his 1H-zone entries are 5m shifts with the sweep extreme as the stop;
these runs still enter on the first 1m shift. The 2026 runs below measure that reading.

## 5. What this does not do

- It does not give his 70 %.  His three winning recaps have no losing counterpart yet; his selection among look-alike
  shifts, and the bias he reads from the dollar index, are not in the rules (see `docs/backtests/course/README.md`, point 6).
- The hour rule is a pattern in this data, not a rule of his.  It stays an overlay until he or the academy names it.
- A win rate measured on 100-200 trades over three and a half years moves by 5-8 points on chance alone.
