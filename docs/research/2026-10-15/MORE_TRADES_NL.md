## Kort antwoord

**Nee. Meer trades zonder dat het slechter wordt, lukt nu niet.** Ik heb ook niets veranderd.

- **Heb ik iets veranderd?** Nee. De regels, de profielen en de code van de bot zijn hetzelfde als vóór vandaag. Alle tests liepen op kopieën. Het enige nieuwe in de repository is het onderzoeksverslag in `docs/research/2026-10-15/`.
- **Huidige setup:** 49 % van de trades wint. Een winnaar levert gemiddeld +2,20R op en een verliezer kost −1,08R, dus ongeveer 2:1 (feb 2024 – sep 2026, na kosten). In 2026 wint 60 %. R is het risico van één trade.
- **Verandert de setup?** Nee. Alleen als jij de extra vangnet-trede goedkeurt, en die verandert alleen de inzet onder −8 %.
- **Waarom geen extra trades:**
  - Van 9 extra markten haalden er 2 jouw lat: USDCAD en GER40. Dat is wat toeval ook geeft. Een markt zonder voordeel haalt de lat ongeveer 1 op de 6 keer, dus bij 9 markten verwacht je er al 1 à 2.
  - Die twee maken de challenge slechter. In de replay lopen 33 starts vast in plaats van 7 als je één van de twee toevoegt, en 45 met allebei.
  - Geen tweede setup haalt de lat zodra hij het account met de live-set deelt.
  - 2026 gaat al snel: elke start haalde fase 1 binnen 60 dagen (mediaan 24 dagen). Extra trades winnen daar hooguit een dag.
- **Wat wel kan:** de extra vangnet-trede. Die geeft geen trades, maar maakt vastlopen minder waarschijnlijk. Hij staat nog niet aan; dat beslis jij.

*Jouw lat:* positief in beide helften van feb 2024 – sep 2026 (feb 2024 – mei 2025 en jun 2025 – sep 2026) en niet negatief in 2026, na FTMO-kosten.
*Replay:* de challenge naspelen vanaf elke startdag (967 starts, feb 2024 – sep 2026), met echte inzet, ladder en guard.
*Vastgelopen:* het account staat zo dicht bij de −9,5 %-grens dat de guard elke nieuwe trade weigert.

## Huidige setup (ongewijzigd)

- **Markten:** EURUSD (maximaal 2 posities), goud, NAS100 (US100.cash) en BTC (halve inzet).
- **Inzet:** 1,5 % per trade, een 4H-zone 2×. Vanaf −3 % zakt de inzet naar 1,0 %, vanaf −6 % naar 0,5 %. Maximaal 2 trades open, 1 per markt (EURUSD 2).
- **Guard:** stopt bij −4 % op een dag en bij −9,5 % onder de start, maar alleen als `PRODUCT=ftmo_2step` in `ftmo_local.bat` staat. Anders stopt hij al bij −8 %.
- **Minimale R:R:** EURUSD 1,0, goud 0,8, NAS100 0,8, BTC 0,5.

Backtest feb 2024 – sep 2026, maximaal 2 open, na 0,10R kosten per trade. De geplande R:R is de afstand tot het doel gedeeld door de afstand tot de stop bij de instap.

| | Trades/mnd | Winrate | Gem. winnaar / verliezer | Geplande R:R (mediaan) | R per trade |
|---|---|---|---|---|---|
| **Alles samen** | 10,1 | 49 % | +2,20R / −1,08R | 2,0 | +0,53R |
| EURUSD | 1,5 | 47 % | +3,00R / −1,06R | 2,12 | +0,84R |
| Goud | 4,5 | 49 % | +2,14R / −1,07R | 2,00 | +0,51R |
| NAS100 | 1,4 | 47 % | +2,91R / −1,10R | 1,67 | +0,77R |
| BTC | 2,8 | 51 % | +1,58R / −1,10R | 1,52 | +0,27R |
| **2026 (jan–sep)** | 9,6 | 60 % | +2,54R / −1,10R | | +1,07R |

- **Hele periode:** +169,0R over 320 trades, grootste daling −10,9R, beide helften positief (+64,5R en +104,5R). Het vorige rapport telde vanaf januari 2024 en kwam daardoor op 328 trades en +167,1R.
- **2026:** +89,8R over 84 trades, grootste daling −3,3R.
- **Challenge, starts in 2026:** fase 1 binnen 30 dagen in 72 % van de starts, binnen 60 dagen in 100 % (mediaan 24 dagen). Beide fases binnen 60 dagen: 94 % (mediaan 42 dagen).
- **Let op:** de profielen zijn op deze zelfde periode afgesteld, en 2017–2023 is op jouw keuze niet gedraaid. Op de 9 nieuwe markten haalden dezelfde profielen gemiddeld −0,29R per trade. Live valt dus waarschijnlijk lager uit dan deze backtest.

## Extra markten

Elke markt draaide met het ongewijzigde profiel van de live-markt die er het meest op lijkt: forex met het EURUSD-profiel, zilver met het goudprofiel, indices met het NAS100-profiel. Alleen pipgrootte, minimale stop, FTMO-naam en spread zijn aangepast. Periode feb 2024 – sep 2026, 1 % risico. In totaal zijn 9 markten en 7 varianten geprobeerd.

| Markt | Trades/mnd | Winrate | R per trade | Helften | 2026: R (trades) | Advies |
|---|---|---|---|---|---|---|
| GBPUSD | 0,9 | 17 % | −0,39R | −5,2 / −6,7R | −9,4R (9, geen winnaar) | niet |
| USDJPY | 1,5 | 15 % | −0,20R | +8,3 / −17,6R | −11,4R (14) | niet |
| AUDUSD | 0,7 | 14 % | −0,60R | −9,4 / −3,2R | −3,1R (3) | niet |
| USDCHF | 1,1 | 15 % | −0,50R | −7,4 / −9,4R | −10,1R (14) | niet |
| NZDUSD | 0,7 | 26 % | +0,04R | −9,1 / +10,0R | +1,0R (3) | niet |
| USDCAD | 1,3 | 34 % | +0,31R | +5,0 / +7,9R | +13,4R (11) | niet |
| Zilver | 4,8 | 25 % | −0,36R | −22,4 / −32,6R | −14,2R (56) | niet |
| US500 | 1,3 | 22 % | −0,35R | +1,8 / −16,0R | −6,6R (10) | niet |
| GER40 | 1,1 | 40 % | +0,34R | +5,6 / +6,2R | +5,1R (5) | niet |

- **USDCAD** haalt de lat alleen op papier. Dit is de versie met CAD-nieuws in de blackout, zoals hij live zou draaien.
  - Van zijn +12,9R komt +9,9R uit 3 trades in juni 2026. In 2025 stond hij op −5,5R, en zonder zijn 3 beste trades op −0,4R.
  - In de replay lopen 33 starts vast in plaats van 7. Van de starts in 2026 haalt 66 % fase 1 binnen 30 dagen, tegen 72 % nu.
- **GER40** haalt de lat, maar met 35 trades. Zonder zijn 3 beste trades blijft er +1,2R over, dus het is niet te onderscheiden van geluk.
  - In 2026 gaf hij maar 0,6 trade per maand.
  - In de replay lopen 33 starts vast in plaats van 7, en op halve inzet 12.
  - Alleen het middagvenster 13–17 zag er beter uit (+17,7R). Maar dat venster is achteraf gekozen, en er lopen dan nog steeds 32 starts vast.
- **De rest:** het EURUSD-profiel wint op de andere forexparen maar 14–34 % van de trades, tegen 47 % op EURUSD zelf. Het profiel is op EURUSD afgesteld. Een ruimere stop op USDJPY en drie manieren om US500 om te rekenen veranderen dat niet.
- **Waarom extra markten de challenge niet helpen:** USDCAD en GER40 pakken bijna nooit de plek van een live-trade in (0 en 1 keer in 32 maanden). Maar hun verliezen vallen in dezelfde slechte periode, maart–juni 2024. De grootste daling van het account wordt dan −14,0R met GER40, −15,3R met USDCAD en −17,4R met beide, in plaats van −10,9R.
- **Kosten:**
  - De forexcijfers zijn na spread en commissie. Zilver, US500 en GER40 zijn ook na de vaste 0,10R per trade.
  - De spreads zijn de standaardwaarden uit de repo. De echte FTMO-spreads zijn nooit gemeten.
  - Geen advies hangt ervan af: de verliezende forexparen verliezen ook bij nul spread, en GER40 blijft positief bij 2× en 3× zoveel spread.

## Tweede setup

Dit is een apart type trade naast de live-regels; die blijven zoals ze zijn. Periode feb 2024 – sep 2026, 9 regelsets geprobeerd. "Op het account" betekent: samen met de live-set, onder de grens van 2 open trades.

- *Gap-zones:* dezelfde instap als live, maar op 1H-prijsgaten die de live-profielen nu overslaan. Alleen als de laatste 4H-structuurbreuk dezelfde kant op wijst.
- *ORB (opening range breakout):* instappen zodra de prijs uit het eerste uur van Londen of New York breekt, met de stop aan de andere kant van dat uur.
- *RSI(2):* kopen na een scherpe daling in een stijgende trend (en omgekeerd), en eruit bij het herstel.
- *Vaste 0,10R:* de kostenpost per trade die ook in de live-cijfers zit.

| Setup | Trades/mnd | Winrate | R per trade | 2026 | Advies |
|---|---|---|---|---|---|
| Gap-zones (vooraf vastgelegd) | 3,3 (op het account +2,4) | 37 % | +0,15R (+0,05R met de vaste 0,10R) | +15,4R (op het account +6,3R) | niet |
| ORB, 4 markten, doel 1,5R / 2R | 164 | 42 % / 39 % | −0,05R / −0,04R | −34,8R / −4,7R | niet |
| ORB alleen New York op NAS100, 2R (achteraf gekozen) | 20,9 | 44 % | +0,08R (−0,02R met de vaste 0,10R) | +5,9R (−12,9R met de vaste 0,10R) | niet |
| RSI(2) op de daggrafiek | 2,1 | 70 % | +0,04R | −2,1R | niet |

- **Gap-zones:**
  - In de eerste helft verdient hij op het account niets: −2,1R, of +0,1R als je de kosten precies zo rekent als bij de live-set.
  - 17 % van zijn trades is precies dezelfde trade als een live-trade.
  - In de replay lopen 39 starts vast in plaats van 7. Van de starts in 2026 haalt 68 % fase 1 binnen 30 dagen, tegen 72 % nu.
  - Twee varianten waren slechter.
- **ORB:**
  - In totaal −260,8R met een doel van 1,5R en −193,3R met 2R.
  - Bij 71–76 % van de live-trades zou de plek al bezet zijn.
  - De New York-versie op NAS100 is de beste van 16 combinaties, en die is pas achteraf gekozen. Zijn winst krimpt elk jaar (2024 +30,3R, 2025 +18,6R, 2026 +5,9R), en in de replay lopen 191 starts vast.
- **RSI(2):**
  - Hij wint 70 %, maar een winnaar levert +0,38R op en een verliezer kost −0,75R.
  - Zijn posities blijven dagen open en bezetten zo plekken van live-trades. Op het account is het daardoor −0,3R.
  - De versie met grenzen 10/90 maakt de challenge trager: mediaan 58 dagen in plaats van 37. Op de 1H-grafiek is het −52,6R.

## Extra vangnet (−8 % → 0,25 %)

**Veilig: ja.** De trede is nu nagecontroleerd.

- **Wat hij doet:** vanaf 8 % onder de start riskeert een trade nog 0,25 %. Nu is dat 1,0 % vanaf −3 % en 0,5 % vanaf −6 %.
- Boven −8 % verandert er niets, en er komen geen trades bij.

Replay van fase 1 en fase 2, 967 starts (feb 2024 – sep 2026):

| | Nu | Met de trede |
|---|---|---|
| Vastgelopen, kosten 0,10R per trade | 7 | 0 |
| Beide fases uiteindelijk gehaald, 0,10R | 99,2 % | 100 % |
| Vastgelopen, hoge kosten 0,25R per trade | 111 | 71 |
| Beide fases uiteindelijk gehaald, 0,25R | 87,7 % | 92,1 % |
| FTMO-limiet geraakt | 0 | 0 |

- **Snelle passes en 2026:** geen snelle pass werd trager (fase 1 binnen 30 dagen, of beide fases binnen 60), en geen van de 267 starts in 2026 veranderde.
- **De prijs:** passes die al traag waren (191–247 dagen) duren ongeveer 19 dagen langer. Bij hoge kosten ging 1 start verloren die zonder de trede na 312 dagen was geslaagd.
- **Diepste stand** als alle open trades tegelijk hun stop raken (kosten 0,10R): −9,64 % met de trede, −9,49 % nu. Geen enkele run met de live-set kwam voorbij FTMO's −10 %.
- **Verwacht niet dat hij alles redt.** Ik heb 80 andere geschiedenissen nagebootst door maanden te husselen (alleen fase 1). Daarin redt de trede ongeveer de helft:
  - vastgelopen starts gaan van 164 naar 87;
  - 76 passes komen erbij en 15 gaan verloren, en die 15 duurden al meer dan 114 dagen.
- **Voorwaarde:** `PRODUCT=ftmo_2step` moet in `ftmo_local.bat` op de laptop staan. Zonder die regel stopt de guard al bij −8 % en komt de trede nooit aan de beurt. Dit is nog niet gecontroleerd.
- **Op tijd:** de trede moet aan staan voordat het saldo ongeveer 9,25 % onder de start staat. Daaronder past geen trade meer.
- **Aanzetten:**
  - Kan op twee manieren: de regel `drawdown_steps` in alle vier de profielen aanpassen, of `--drawdown-steps=-3:1.0,-6:0.5,-8:0.25` toevoegen aan de COMMON-regel van `scripts/start_ftmo.bat`. Via `ftmo_local.bat` kan het niet.
  - Beide manieren veranderen de bevroren live-set, dus alleen met jouw OK.
  - Het funded account houdt zijn eigen ladder: 0,5 % vanaf −3 %.
- **Niet gemeten:**
  - Het funded account is niet nagespeeld.
  - Of FTMO een account na 30 dagen zonder trade echt sluit, is nog niet nagekeken. Als dat zo is, ben je een vastgelopen account kwijt en is de trede nog belangrijker.

## Beslissingen voor jou

1. **De extra vangnet-trede aanzetten?** Advies: **ja.** Hij geeft geen extra trades, vertraagt geen snelle pass en raakte nooit een FTMO-limiet, terwijl er minder accounts vastlopen (in de replay 7 → 0, in de nagebootste geschiedenissen ongeveer de helft minder).
2. **Eerst op de laptop checken of `PRODUCT=ftmo_2step` in `ftmo_local.bat` staat?** Advies: **ja.** Zonder die regel stopt de guard bij −8 % in plaats van −9,5 % en doet de trede niets.
3. **USDCAD toevoegen?** Advies: **nee.** De winst hangt aan 3 trades in juni 2026, en in de replay lopen 33 starts vast in plaats van 7.
4. **GER40 toevoegen, ook op halve inzet?** Advies: **nee.** Te weinig bewijs (35 trades) en meer vastgelopen starts (33 in plaats van 7, op halve inzet 12). Een demo beslist het ook niet: bij 0,6 trade per maand duurt dat 4–8 jaar. Op de demo zetten heeft alleen zin om de echte GER40.cash-spread te meten.
5. **Een tweede setup (gap-zones, ORB of RSI(2))?** Advies: **nee.** Geen van de 9 regelsets haalt jouw lat op het account.
6. **De andere markten (GBPUSD, USDJPY, AUDUSD, USDCHF, NZDUSD, zilver, US500)?** Advies: **nee.** Elk verliest in minstens één helft, en op NZDUSD na ook in 2026.

Bronnen (alles in de scratchpad, niets in de repository):
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/more/combine/out/summary.txt (challenge-replay van alle combinaties)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/more/ladder_step/out/summary.txt (vangnet-trede)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/more/skeptic/out/stats.json (tegencontrole)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/more (de runs per onderwerp)