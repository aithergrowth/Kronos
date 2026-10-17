# Extra trades op de vier markten (16 oktober)

## Kort antwoord

**Nee, niet echt.** Ik heb 36 regelsets getest en elke set vooraf vastgelegd. Ze vallen in vier groepen: geweigerde setups als kleine extra trades, bijkopen in winnaars, nieuwe soorten trades, en dag- en weekswings. Drie getallen beslissen het:

1. **5 van de 36 halen jouw lat. Als geen enkele regel iets zou verdienen, haalden er door toeval al ongeveer 6 de lat.** Een regel zonder enig voordeel haalt de lat ongeveer 1 op de 6 keer. Alle 5 zijn kleinere extra trades bovenop de live-set. Geen enkel nieuw soort trade haalt de lat.
2. **De challenge wordt er nauwelijks sneller van.** Neem de beste afweging, alles samen op lage inzet. Dan haalt 72,5 % van de starts in 2026 fase 1 binnen 30 dagen, tegen 72,1 % nu. Een kleine extra positie naast een lopende trade maakt fase 1 over feb 2024 – sep 2026 zelfs trager: 97 starts worden trager, 49 sneller.
3. **Wat de bot nu weigert, verliest.** De setups achter de 'bijna'-meldingen geven 143 trades en −34,4R. Alles buiten de vensters geeft 667 trades en −116,4R.

De bot, de regels en de repository zijn niet veranderd.

*Geteld:*
- 36 vooraf vastgelegde regelsets: geweigerde setups 15, bijkopen 3, sessiepatronen 13, swings 5.
- 2 sets achteraf gekozen: alleen goud, en alles samen.
- Ongeveer 140 account-varianten: inzet, slot, ladder en kosten.

*Let op:* alles is gemeten op feb 2024 – sep 2026, dezelfde periode waarop de profielen zijn afgesteld. Fase 2, het funded account en de echte FTMO-spreads zijn niet getest.

## Wat werkt

Dit werkt alleen op papier. 5 kandidaten halen jouw lat, maar geen ervan maakt de challenge duidelijk sneller.
- Ze komen allemaal bovenop de live-set: extra posities in een eigen slot, bijkopen zonder slot. Ze verdringen hooguit 1 live-trade.
- Binnen de huidige grens (2 open, 1 per markt) komt een extra positie naast een live-trade bijna nooit aan bod: 3 van de 60.
- Er is dus een eigen slot nodig, en dat verandert de bevroren live-set.

Uitleg bij de regels hieronder:
- *Gehusseld:* 100 nagebootste geschiedenissen met gehusselde maanden. De live-set haalt daar 38,0 % binnen 30 dagen, met 182 vastgelopen starts.
- *Zonder voordeel:* dezelfde extra trades, met hun gemiddelde R op 0 gezet.
- Tussen haakjes staat het aantal geprobeerde varianten.

- **Goud, zone ouder dan 24 candles** (5 + 2): 0,31 per maand, +1,47R per trade, 2026 +1,8R (2 trades), mrt–jun 2024 +3,7R. Challenge: 2026 gelijk (72,1 % binnen 30 dagen). Op 0,5 % verdwijnen de 7 vastgelopen starts, maar dat komt door 2 winsten in maart–april 2024: gehusseld +1,8 punt, zonder voordeel +0,05. Het rust op 10 trades, maar het is de enige kandidaat die niet meeloopt met de goede maanden van de live-set.
- **Kleine extra positie naast een lopende live-trade, 0,25 %** (8 + 2): 1,89 per maand, +0,26R, 2026 +12,7R (17 trades), mrt–jun 2024 +2,7R. Challenge: 2026 73,4 %, maar over de hele periode trager (97 starts trager, 49 sneller) en 8 vastgelopen in plaats van 7. Gehusseld +0,9 punt, zonder voordeel +0,6. Juni 2026 levert 69 % van de winst, en die winst zit in goud.
- **Idem, alleen goud** (achteraf gekozen; 2): 1,10 per maand, +0,52R, 2026 +13,2R (10 trades), mrt–jun 2024 +3,9R. Challenge: 2026 73,4 %, 1 vastgelopen in plaats van 7. Gehusseld +1,0 punt, zonder voordeel +0,7. Over de hele periode gemiddeld nog 2,1 dagen trager.
- **Bijkopen na +2R, 0,5 %** (12 + 2): 0,35 per maand, +0,93R per bijkoop, 2026 +0,2R (4 bijkopen), mrt–jun 2024 geen bijkopen. Challenge: neutraal. 7 vastgelopen (gelijk), 2026 iets trager (70,4 %).
- **Bijkopen na +1R, 0,5 %** (12 + 2): 1,10 per maand, +0,49R per bijkoop, 2026 +13,2R (8 bijkopen, waarvan +10,7R uit één BTC-bijkoop), mrt–jun 2024 −2,2R. Alle 6 bijkopen in je verliesmaanden verloren. Challenge: 2026 gelijk (72,1 %), 5 vastgelopen, op 0,75 % 16. Bij een bijkoop staat er tot 4,0 % risico open, precies de daggrens van de guard.
- **1H-zone, bezoek ouder dan 24 u** (EURUSD en BTC; 8 + 2): 0,41 per maand, +0,25R, 2026 geen trades, mrt–jun 2024 −0,5R. Challenge: 2026 gelijk, 12 vastgelopen in plaats van 7. Zonder zijn 3 beste trades −6,0R.
- **Alles samen op lage inzet** (de drie soorten extra posities op 0,25 % plus bijkopen na +2R op 0,5 %; beste van 4 combinaties): 2,9 per maand, +0,47R, 2026 +14,8R, mrt–jun 2024 +5,9R. Challenge: 2026 72,5 %, 11 vastgelopen in plaats van 7. Gehusseld +2,0 punt; zonder voordeel +0,6 punt en 53 vastgelopen starts meer.

## Wat niet werkt

**De setups die de bot nu weigert:**
- **Buiten de vensters 09–11 / 13–17:** 667 trades (21 per maand), −116,4R, mrt–jun 2024 −24,2R. Alleen 2026 is positief (+15,4R).
- **'Bijna'** (shift gezien, maar te diep of R:R te laag): 143 trades (4,5 per maand). 49 % wint, maar een winnaar levert gemiddeld maar +0,62R. Totaal −34,4R, 2026 −7,8R, mrt–jun 2024 −9,2R.
- **Overige weigeringen:**
  - R:R onder het minimum: −27,0R
  - zonder 1H-eis: −17,3R
  - zone pas na 24 u aangeraakt: −17,0R
  - zonder veto: −12,2R
  - bias 2 van 5: −9,1R
  - tweede bezoek: −7,5R
  - instap dieper dan halve zone: −7,4R
  - R:R gezakt bij de fill: −3,4R
  - zonder nieuws-blackout: −1,2R
- **Tweede trade in hetzelfde bezoek:** +5,7R, maar de eerste helft staat op −4,1R.
- **Spreadgrens:** hield in de backtest geen enkele setup tegen.

**Nieuwe soorten trades** (geen enkele haalt de lat):
- **Aziatische range-sweep** (goud, EURUSD, NAS100; 6 varianten). De high of low van 00–08 uur wordt geraakt, de prijs sluit terug binnen, en de trade gaat naar de overkant. Met de live-bias 24 trades en −17,0R; zonder bias 521 trades (16 per maand) en −70,3R.
- **NAS100-openingsgap terug** (3 varianten). Om 15:30 tegen de gap in, met de slotkoers van gisteren als doel. De beste versie geeft +7,5R over 208 trades, maar de tweede helft staat op −9,3R en 2026 op −5,3R, en de winst krimpt elk jaar. Wel de enige die duidelijk won in mrt–jun 2024 (+18,1R).
- **BTC: CME-gap op maandag en weekend-uitbraak** (4 varianten): −6,7R tot −32,3R. De versies die dagen openstaan, nemen de plek van live BTC-trades in.
- **Dag- en weekzones** (5 varianten): dagzones 10 trades, −0,2R, 2026 −4,5R. Sweep van de high of low van vorige week: 74 trades, −17,4R. De enige plus (+3,1R) is één goudtrade uit maart 2024.

**Bijkopen zodra de stop op break-even staat:** 8 bijkopen in 32 maanden, 2026 −0,9R.

## Beslissingen voor jou

Iets nieuws gaat altijd eerst op de demo. Geen enkele kandidaat heeft bewijs dat sterk genoeg is om dat over te slaan.

1. **Kleine extra posities naast de live-set (los, alleen goud of alles samen)?** Advies: **nee.**
   - Het is vooral dubbel inzetten op dezelfde richting: alle 46 extra posities die naast een live-trade liepen, gingen dezelfde kant op.
   - Het meeste valt in maanden die toch al goed gaan.
   - Op hogere inzet gaat het sneller, maar dat komt van het extra risico. Alles samen op hogere inzet geeft gehusseld +4,7 punt. Zonder voordeel blijft er +1,7 punt over, met 157 vastgelopen starts meer.
   - Bouwen kost ongeveer 1 dag (alles samen 3–5 dagen) en verandert de bevroren live-set.
2. **Bijkopen in winnaars (na +1R of +2R)?** Advies: **nee.** Na +2R is het neutraal en in 2026 iets trager. Na +1R verloor elke bijkoop in je verliesmaanden, en staat er tot 4,0 % risico open. Bouwen kost 2–4 dagen plus een nieuwe review van de live-code.
3. **De weigeringen 'zone te oud' op goud bijhouden?** Advies: **ja.** De bot logt elke weigering al, dus het kost niets en de live-set blijft gelijk. Verwacht geen snel oordeel: het gaat om 10 setups in 32 maanden. De regel zelf losser zetten blijft "losser, later", en dan eerst op de demo.
4. **Ruimere vensters, of R:R, 1H-eis, nieuws-blackout of 'bijna'-setups losser?** Advies: **nee.** Buiten de vensters kost −116,4R, 'bijna' kost −34,4R. Wil je de vensters toch veranderen, dan alleen met jouw uitdrukkelijke OK. De code-aanpassing doe ik pas na jouw ja.
5. **Een nieuw soort trade op de demo?** Advies: **nee.** Geen van de 13 sessiepatronen en 5 swing-varianten haalt de lat. De NAS100-gap is de enige die duidelijk tegen de live-set in beweegt (+18,1R in mrt–jun 2024). Maar zijn winst krimpt elk jaar en 2026 staat op −5,3R. Hooguit is hij het waard om ooit te toetsen op data van vóór 2024.

Bronnen (niets in de repository):
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/extra/combine/out/summary.txt (challenge-replay van alle kandidaten)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/extra/skeptic/out/sk_stats.json (tegencontrole)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/extra (alle runs, met de vooraf vastgelegde regels in de PREREG.txt van elk onderwerp)