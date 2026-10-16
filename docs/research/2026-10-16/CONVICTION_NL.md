# Hogere inzet op zekere trades (16 oktober)

## Kort antwoord

**De inzet kan omhoog, maar via de gewone inzet (optie B), niet extra op een groep 'zekere' trades. Die kan de bot bij instap niet herkennen.** We hebben 295 pogingen gedaan om zekere trades te herkennen: Dorus' eigen A+-plan, de Kronos-voorspelling en 85 andere kenmerken bij instap. Daarnaast hebben we 711 manieren getest om ze hoger in te zetten. Nergens zijn 0,01-lot-trades gebruikt. Drie getallen beslissen het:

1. **Wat standhoudt, is een ver doel, en dat is juist minder zeker.** Trades met een geplande risk-reward boven 2 leveren meer op als ze winnen. Ze winnen alleen minder vaak: 49 van de 115 (43 %), tegen 114 van de 202 (56 %) voor de rest (feb 2024 – sep 2026).
2. **A+ hoger inzetten is trager dan op elke trade dezelfde, iets hogere inzet.**
   - A+ op 3 % en de rest op 1,5 %: beide fases in 73 dagen, met 1,4 % kans op falen (310 van 22.704).
   - Elke trade 1,75 %: 67 dagen, bij hetzelfde risico (322 van 22.704).
   - Willekeurige trades als 'A+' aanwijzen: 72 dagen.
   - Het label voegt dus niets toe; de snelheid komt van de inzet. Alle drie zijn gehusseld gemeten, met 4H ×1,25, BTC ×0,25 en de lock.
3. **Optie B zonder micro-trades is wél sneller:** 64 in plaats van 75 dagen. De kans op falen daalt ook: 2,5 % (575 van 22.704) in plaats van 2,9 % (652 van 22.704).

**Dag 3 zonder trade is normaal.**
- In de backtest (feb 2024 – sep 2026) gingen 3 werkdagen achter elkaar zonder nieuwe trade 121 van de 414 keer voorbij (29 %).
- Er waren 7 stiltes van meer dan 14 dagen. De langste duurde 27,9 dagen (24 juli – 21 augustus 2025).
- FTMO mag een account pas na 30 dagen zonder trade beëindigen.
- Een hogere inzet levert geen extra trades op.

Begrippen:
- *R:* het risico van één trade. +2R is twee keer je risico gewonnen, −1R is je stop. *Risk-reward:* hoe ver het doel ligt, gemeten in R. Alle R is na FTMO-kosten.
- *Echt:* de challenge nagespeeld vanaf elke startdag van feb 2024 – sep 2026 (967 starts). *Gehusseld:* 200 nagebootste geschiedenissen met dezelfde maanden in een andere volgorde (22.704 starts).
- *Falen:* een FTMO-breach, of vastgelopen: het account staat zo diep dat de guard elke trade weigert.
- *Lock* (code, nog niet gebouwd): zodra de fase 4 handelsdagen heeft, mikt een nieuwe trade niet verder dan de prijs waar je saldo precies het doel haalt.
- *Rem:* extra A+-inzet alleen zolang de fase niet in de min staat. Dorus doet iets vergelijkbaars. Zijn A+-setups gaan naar de accounts die in de plus staan, of naar challenges. De setups waar hij minder zeker van is, gaan naar de accounts in de min.

## Wat werkt

- **Een ver doel geeft een grotere winst, geen zekerdere trade.** Het gaat om trades met een geplande risk-reward boven 2: 115 van de 317 trades, 3,6 per maand.
  - Feb 2024 – mei 2025: 60 trades, 21 gewonnen, +0,58R per trade. De rest: 110 trades, 64 gewonnen, +0,42R.
  - Jun 2025 – sep 2026: 55 trades, 28 gewonnen, +1,93R. De rest: 92 trades, 50 gewonnen, +0,45R.
  - 2026: 25 trades, 20 gewonnen, +3,79R. De rest: 60 trades, 31 gewonnen, +0,42R.

  Dat haalt je lat. Het is ook de enige groep die overeind blijft als je corrigeert voor het aantal pogingen. Maar:
  - Het hangt af van de markt. In de trend van 2025–2026 werd een ver doel vaak geraakt. In feb 2024 – mei 2025 was het verschil klein.
  - Op de controle 2017–2023 (telt niet mee) won de groep maar 46 van de 219 trades (21 %), de rest 164 van de 479 (34 %). Per trade: +0,20R tegen −0,11R.
  - Eerlijk geschat is het voordeel ongeveer +0,3R per trade, niet de +0,8R van 2024–2026.
  - Op EURUSD was het juist slechter: 26 trades, 8 gewonnen, +0,71R, tegen 21 trades, 14 gewonnen, +1,15R.
- **Een hogere gewone inzet (optie B).** B zonder micro-trades haalt beide fases in 61 in plaats van 73 dagen (gehusseld 64 tegen 75; starts in 2026: 37 tegen 42). De kans op falen daalt, ook bij tegenslag (zie de tabel).

## Wat niet werkt

**Dorus' eigen A+-plan**, vooraf vastgelegd in zijn woorden. Geen enkel onderdeel is in beide helften beter dan de rest. Per cel: trades (gewonnen), dan R per trade van de groep / van de rest.

| Onderdeel | Hele periode | Feb 2024 – mei 2025 | Jun 2025 – sep 2026 | 2026 |
|---|---|---|---|---|
| Bias helemaal mee (4 of 5 tijdframes, geen tegen) | 127 (64): +0,59 / +0,80 | 69 (34): +0,31 / +0,59 | 58 (30): +0,93 / +1,05 | 26 (18): +1,61 / +1,32 |
| POI in een POI | 173 (90): +0,78 / +0,65 | 85 (40): +0,36 / +0,59 | 88 (50): +1,18 / +0,74 | 53 (33): +1,56 / +1,17 |
| Zone geboren uit het pakken van liquiditeit | 47 (23): +1,27 / +0,62 | 21 (10): +0,38 / +0,49 | 26 (13): +1,99 / +0,79 | 11 (6): +3,40 / +1,12 |
| Doel op liquiditeit op 1–2R | 106 (56): +0,38 / +0,89 | 57 (29): +0,22 / +0,60 | 49 (27): +0,57 / +1,22 | 37 (19): +0,47 / +2,14 |
| Liquiditeit gepakt tijdens het bezoek, dan de balance shift | 109 (62): +0,73 / +0,72 | 67 (36): +0,42 / +0,51 | 42 (26): +1,22 / +0,92 | 22 (18): +1,72 / +1,31 |
| Het hele plan (3 of meer van de 5) | 40 (19): +0,43 / +0,76 | 16 (6): −0,14 / +0,54 | 24 (13): +0,81 / +1,04 | 14 (7): +0,47 / +1,60 |

- *Liquiditeit gepakt, dan de shift* wint wel vaker: 62 van 109 (57 %) tegen 101 van 208 (49 %). In 2026 was dat 18 van 22 tegen 33 van 63. Hij levert alleen evenveel R op, en de challenge betaalt in R, niet in winrate.
- De winst van *zone uit liquiditeit* zit in 9 BTC-trades, met één van +23,5R.

**De Kronos-voorspelling.** Geen van de 10 versies haalt je lat. Bij de sterkste versie draait het teken om. Zo deden de trades waar Kronos het mee eens was het:
- feb 2024 – mei 2025: 34 trades, 11 gewonnen, −0,08R tegen +0,61R;
- jun 2025 – sep 2026: 30 trades, 21 gewonnen, +2,45R tegen +0,63R;
- 2026: 17 trades, 15 gewonnen, +3,76R tegen +0,82R.

Het model verwacht meestal dat de prijs terugloopt, terwijl jouw trades met de beweging meegaan.

**De andere kenmerken bij instap** (bias, gepakte liquiditeit, leeftijd en diepte van de zone, uur, weekdag). Van de 92 regels met genoeg trades halen er 27 je lat. Puur toeval geeft er al 31 tot 35.

**De 4H ×2 van nu is ook geen bewezen A+.**
- Op EURUSD, goud en NAS100 waren die 28 trades (14 gewonnen) in elke periode beter: +0,95R tegen +0,70R. In 2026 waren het 8 trades, 6 gewonnen, +2,01R tegen +1,35R. Dat zijn te weinig trades om iets te zeggen.
- Met de 4H-zones van BTC erbij (50 trades, 26 gewonnen) waren ze vanaf juni 2025 slechter: +0,66R tegen +1,06R (21 trades).

**Een A+-inzet zonder rem.** Zo werkt de bestaande instelling `far_target_rr`: de extra inzet geldt ook als de fase in de min staat. Falen gaat dan omhoog:
- echte starts: van 0,7 % (7 van 967) naar 9,1 % (88 van 967);
- gehusseld: van 2,9 % naar 10,9 % (2.465 van 22.704);
- de slechtste instelling liet 27,2 % vastlopen (263 van 967).

**Een A+-inzet met rem** is even veilig als elke trade 1,75 %, maar trager: 73 tegen 67 dagen gehusseld, 65 tegen 60 echt.
- Dat hij veiliger is dan nu, komt van de 4H ×1,25, de lock en de rem, niet van het label.
- Tegenslag: als elke stop 0,25R slechter vult, falen 9 van de 10 A+-instellingen vaker dan elke trade 1,75 %. Ze zitten op 6,3 tot 17,6 % (61 tot 170 van 967), tegen 6,5 % (63) bij 1,75 % en 21,6 % (209) nu.
- De enige A+-instelling die even snel was als B valt ook af. Op 2017–2023 is zijn voordeel bijna weg: +0,10R per trade over 382 trades, en negatief in 2017–2020.

## Opties

| Optie | Wat verandert | Fase 1, mediaan dagen | Beide fases, mediaan dagen | Kans op falen | Bij tegenslag |
|---|---|---|---|---|---|
| **Nu** | niets: `RISK=1.5`, 4H ×2, BTC ×0,5 | 37 (40) | 73 (75); 2026: 42 | 2,9 % (652 van 22.704); echt 7 van 967 | 21,6 % (209 van 967) |
| **B zonder micro-trades** | `RISK=2.25`, 4H ×1,25, BTC ×0,25; code: lock | 32 (32) | 61 (64); 2026: 37 | 2,5 % (575 van 22.704); echt 4 van 967 | 13,5 % (131 van 967) |
| **B, maar op 1,75 %** | `RISK=1.75`, 4H ×1,25, BTC ×0,25; code: lock | 36 (37) | 60 (67); 2026: 39 | 1,4 % (322 van 22.704); echt 3 van 967 | 6,5 % (63 van 967) |
| **A+ met rem** | `RISK=1.5`, 4H ×1,25, BTC ×0,25; ver doel op 3 % zolang de fase niet in de min staat; code: lock + A+ | 41 (40) | 65 (73); 2026: 38 | 1,4 % (310 van 22.704); echt 0 van 967 | 9,9 % (96 van 967) |
| **A+ zonder rem** (afgeraden) | idem, maar de 3 % ook in de min (zo werkt `far_target_rr`); code: lock | 35 (37) | 60 (70); 2026: 37 | 10,9 % (2.465 van 22.704); echt 88 van 967 | 24,7 % (239 van 967) |

- **Zo lees je de tabel:**
  - De dagen zijn gemeten op de echte starts; tussen haakjes staat gehusseld. "2026" zijn de starts in 2026.
  - Kans op falen is gehusseld, met de echte starts erachter.
  - Bij tegenslag: als élke stop 0,25R slechter vult (echte starts).
  - De rest blijft zoals nu: de ladder (1 % vanaf −3 %, 0,5 % vanaf −6 %), de guard, 2 open trades, en de halve inzet bij een 50/50-maand en bij EURUSD 1D+1H.
- **Start in 4 slechte maanden:** nu 49,6 % falen (794 van 1.600), B 41,6 % (665), B op 1,75 % 29,3 % (468), A+ met rem 29,3 % (469), A+ zonder rem 79,8 % (1.276).
- **Willekeurige trades als 'A+'** (evenveel per markt, dezelfde inzet): 66 dagen (72), 1,4 % falen. Dat is even snel als A+ met rem.
- **FTMO-breaches:** 0 in elke rij; falen is hier dus vastlopen. Alleen als elke stop 0,25R slechter vult, gaven nu en B in de gehusselde geschiedenissen soms een echte breach: 47 en 26 van de 22.704 starts. B op 1,75 % en A+ met rem gaven er 0.
- **Geen micro-trades:** in elke rij komen de 4 handelsdagen uit de eigen trades van de bot. Haal je het doel vóór de 4e handelsdag, dan neemt de bot zijn eigen setups op 0,1 % tot de dagen vol zijn. Zo staat het nu ingesteld, met `STOP_AT_TARGET=1`. Wil je dat ook niet, zeg het; dan reken ik het zonder.
- Gehusseld zijn dezelfde 200 geschiedenissen als in het rapport over sneller slagen (nu 75 dagen, 2,9 %). De aanvulling daar gebruikte andere geschiedenissen (nu 76 dagen en 3,1 %, B 64 dagen en 2,4 %). Het beeld is hetzelfde.

## Advies

1. **Bouw geen A+-inzet.**
   - De bot herkent geen zekere trades. Het enige echte verschil, een ver doel, gaat over hoeveel een trade oplevert, niet over hoe zeker hij is.
   - In de challenge is A+ niet sneller dan elke trade iets hoger (73 tegen 67 dagen bij hetzelfde risico). Bij tegenslag is hij zwakker.
   - Het vraagt code in de motor, de backtester en het live-pad, plus tests.
   - Het maakt sommige posities 2 tot 4 keer zo groot als de rest. FTMO's regels vragen je "substantially larger position sizes compared to your other simulated trades" te vermijden. Ze noemen geen getal, en wat FTMO dan doet, bepaalt FTMO zelf.
   - Op EURUSD zou een A+-positie van 3 % in 22 van de 47 setups meer lots hebben dan de grootste EURUSD-positie van de live-set in 2024–2026. B maakt je grootste trade juist kleiner: 2,81 % in plaats van 3 %.
   - `far_target_rr` (A+ zonder rem) blijft dus uit.
2. **Wil je sneller, kies dan optie B zonder micro-trades.**
   - Beide fases duren 61 in plaats van 73 dagen (gehusseld 64 tegen 75), en fase 1 32 in plaats van 37.
   - De kans op falen is lager, ook bij tegenslag: 13,5 % (131 van 967) tegen 21,6 % (209).
   - Wil je het zekere voor het onzekere, neem dan dezelfde instellingen op `RISK=1.75`.
     - Fase 1 duurt dan 36 in plaats van 32 dagen, en beide fases gehusseld 67 in plaats van 64.
     - De kans op falen is bijna de helft: 1,4 % (322) tegen 2,5 % (575). Bij tegenslag 6,5 % (63) tegen 13,5 % (131).
   - Wat het vraagt:
     - Jouw ja.
     - De profielen: 4H ×1,25 voor EURUSD, goud en NAS100, en BTC ×0,25. Dat pas ik aan. Het is config, maar het verandert de bevroren live-set.
     - De lock: dat is code. Ik bouw en test hem eerst op een kopie.
     - Daarna zet je `RISK=2.25` (of `1.75`) in `scripts\ftmo_local.bat` en herstart je de bot.
   - Eerst de profielen, dan `RISK`. Met de oude 4H ×2 wordt een 4H-trade op `RISK=2.25` een trade van 4,5 %, en die weigert de guard bijna altijd.
   - Tot de lock er is, geeft de nieuwe inzet alleen al 65 in plaats van 73 dagen (gehusseld 71 tegen 75). De kans op falen is dan 2,8 % in plaats van 2,9 % (633 tegen 652 van 22.704). Op 1,75 %: 66 dagen (73), bij 1,5 % (341).
3. **Laat de bot zijn eigen setups afwachten.** Dag 3 zonder trade is normaal. Meer trades forceren (extra soorten trades, meer markten) maakte de challenge in het onderzoek van vandaag niet duidelijk sneller.

Ik verander niets zonder jouw ja.

**Eerlijk:** geen trade is zeker. Ook de trades met een ver doel verloren in feb 2024 – mei 2025 38 van de 60 keer.

Hoe hoger de inzet, hoe harder een verliesreeks aankomt. Met B kosten twee verliezers op rij 4,5 % in plaats van 3 %. Daarna zet de ladder je inzet op 1 %, en duurt terugkomen langer. Een A+-inzet zonder rem liet in de replay 9,1 % van de challenges vastlopen (88 van 967), tegen 0,7 % (7) nu.

*Let op:* alles is gemeten op feb 2024 – sep 2026, de periode waarop de regels zijn afgesteld. Live gaat het waarschijnlijk trager.

Als controle (telt niet mee) is ook 2017–2023 bekeken. Daar verdiende de strategie zelf niets, en liep bij elke inzet 84–88 % van de starts vast: nu 2.092 van 2.371, B zonder lock 2.006, A+ 1.986–2.095. Een A+-label redt geen periode zonder voordeel.

Bronnen (in de repository is niets veranderd):
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/size/table.txt (de challenge-replay, alle 711 instellingen)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/skeptic/out/skeptic_summary.json (de tegencontrole)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/dorus/PREREG.txt (de vooraf vastgelegde regels van Dorus' A+-plan)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/features/PREREG.txt (de vooraf vastgelegde regels van de kenmerken bij instap)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/kronos/PREREG.txt (de vooraf vastgelegde regels van de Kronos-voorspelling)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/limits/out/ftmo_quotes.txt (de FTMO-teksten)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/report/b_nolock.py (B zonder lock)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/conviction/report/stress_rows.py (dezelfde tegenslag-tests voor elke rij van de tabel; de rijen die de tegencontrole al had, kwamen exact terug)
