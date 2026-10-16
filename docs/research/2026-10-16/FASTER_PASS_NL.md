# Sneller slagen voor de FTMO 2-Step (16 oktober)

## Kort antwoord

**Ja, het kan zo'n 17–20 dagen sneller zonder meer kans op falen, maar niet door alleen `RISK` hoger te zetten.** Bij `RISK=2` riskeert een 4H-trade 4 %. De guard heeft een daggrens van 4 % en weigert die trade, dus je wordt juist trager: beide fases 85 dagen in plaats van 75 (gehusseld).

Optie B haalt de snelheid uit drie dingen samen:
- **Micro-trades:** je vult de 4 verplichte handelsdagen meteen met een trade van 0,01 lot. Vraag FTMO eerst of dat mag.
- **De lock** (code): de trade die je over het doel tilt, sluit precies op het doel.
- **Inzet 2,25 % met 4H ×1,25 en BTC ×0,25:** een hogere inzet, maar je 4H-trades passen dan nog onder de guard.

Drie getallen beslissen het:
1. **Beide fases, mediaan:** van 73 naar 53 dagen (gehusseld 75 → 58; starts in 2026: 42 → 31).
2. **Kans op falen:** van 2,9 naar 2,4 %, pessimistisch van 12–17 naar 10,5–15,5 %. B is dus sneller en niet riskanter.
3. **De grens:** voorbij optie C (52 dagen gehusseld) wordt snelheid duur. Nog 2–7 dagen winst kost 9,4–18,0 % kans op falen in plaats van 3,2 %, plus echte FTMO-breaches.

Zonder code (optie A) gaat het van 73 naar 60 dagen (gehusseld 75 → 66), met dezelfde 2,9 %. Je houdt dan wel maar de helft van je ruimte voor slippage over.

Begrippen:
- *Echt:* de challenge nagespeeld vanaf elke startdag van feb 2024 – sep 2026 (967 starts).
- *Gehusseld:* 200 nagebootste geschiedenissen met dezelfde maanden in een andere volgorde. Die zijn er omdat 2,7 jaar maar één pad is.
- *Falen:* een *breach* of *vastgelopen*.
  - Een breach is FTMO's grens van 5 % op een dag of 10 % in totaal.
  - Vastgelopen: het account staat zo diep dat de guard elke trade weigert, en dan ben je de challenge in de praktijk kwijt.
  - In de replay is de breach bij elke optie 0 %. Het risico zit dus in vastlopen.
- *Pessimistisch:* de tegencontrole met een derde minder winst per trade. Die is nodig omdat de regels op deze zelfde periode zijn afgesteld.
- *R:* het risico van één trade. *Slippage:* je stop vult slechter dan de stopprijs.
- *4H ×1,25:* een trade op een 4H-zone riskeert 1,25 keer `RISK` (nu 2 keer). *BTC ×0,25:* BTC handelt op een kwart van `RISK` (nu de helft).

## Opties

| Optie | Wat je instelt | Fase 1 mediaan dagen | Binnen 14 / 30 dagen | Kans op falen (replay / pessimistisch) |
|---|---|---|---|---|
| **Nu** | `RISK=1.5`, 4H ×2, BTC ×0,5, `TARGET=10`, `STOP_AT_TARGET=1` | 37 (40) | 10,3 / 41,7 % | 2,9 % / 12–17 % |
| **A. Veilig sneller, zonder code** | `RISK=1.75`, BTC ×0,25, micro-trades | 35 (35) | 17,2 / 45,3 % | 2,9 % / 11,5–17,6 % |
| **B. Veilig sneller, met lock** | `RISK=2.25`, 4H ×1,25, BTC ×0,25, micro-trades; code: lock | 31 (31) | 23,4 / 49,5 % | 2,4 % / 10,5–15,5 % |
| **C. Gebalanceerd** (alleen veilig met 2 guard-fixes) | `RISK=2.5`, 4H ×1,5, BTC ×0,25, micro-trades; code: lock + size-down | 28 (28) | 27,2 / 52,5 % | 3,2 % / 13,3–17,2 % |
| **D. Snel** (afgekeurd) | `RISK=2.5`, 4H ×2, BTC ×0,25, ladder `-4:1.0,-7:0.5`, micro-trades; code: lock + size-down | 27 (27) | 27,6 / 54,3 % | 9,4 % / 21–25 %, plus breaches |
| **E. Heel snel** (afgekeurd) | `RISK=3`, 4H ×1,5, BTC ×0,25, ladder `-3:2.0,-6:1.0`, micro-trades; code: lock + size-down | 24 (24) | 31,5 / 58,6 % | 18,0 % / 31–36 %, plus breaches |

- **Hoe je de tabel leest:**
  - De snelheid is gemeten op de echte starts; tussen haakjes staat de gehusselde mediaan.
  - *Replay* is de kans op een breach of vastlopen in de 200 gehusselde geschiedenissen.
  - Alles wat de tabel niet noemt, blijft zoals nu: de ladder `-3:1.0,-6:0.5`, de guard, 2 open.
- **Size-down en guard-fixes** (allebei code):
  - *Size-down:* past een trade niet meer in de 4 % dagruimte, dan neemt de bot hem kleiner in plaats van hem te weigeren.
  - *Guard-fixes:* de guard telt elke open stop als 1,3R, en winst die je die dag al hebt gesloten geeft geen extra ruimte.
- **Breach door slippage:**
  - Als 1 op de 10 stops 0,3–0,5R slechter vult: nu 0–0,9 %, A 0,4–3,7 %, B 0 %, C 2,2–2,7 %, D 2,6–3,4 %, E 3,1–4,5 %.
  - Als élke stop slechter vult, beginnen de breaches bij 0,20–0,25R voor A en C, bij 0,30–0,40R voor B en bij 0,40–0,50R nu.
- **Gaps:** bij elke optie, ook nu, is er ongeveer 1,5–2 % kans per challenge dat een koersgat over nacht of weekend door een stop een breach geeft (B 1,3–1,8 %). Dat is een schatting: geen van de 165 stops in 2024–2026 werd overgesprongen.
- **Wachttijd tussen de fases:** FTMO zet je pas na 1–2 werkdagen door naar fase 2. Daardoor wordt "beide fases" gehusseld 3–7 dagen langer (nu 76 → 79, B 58 → 64, C 53 → 60; gemeten op 100 geschiedenissen).
- **Equity of startsaldo:** de bot rekent de inzet op equity, de replay op het startsaldo. Op equity is het even snel en 0,5–2 punten veiliger, dus de tabel zit aan de voorzichtige kant.

Alle cijfers:

| Optie | Fase 1 binnen 7/14/21/30 d, echt | Idem, gehusseld | Beide fases mediaan, echt / gehusseld | 2026-starts: fase 1 / beide (mediaan) | Vastgelopen echt / gehusseld | Idem bij 0,25R kosten |
|---|---|---|---|---|---|---|
| Nu | 0,5 / 10,3 / 23,4 / 41,7 % | 0,6 / 9,9 / 22,4 / 38,1 % | 73 / 75 d | 24 / 42 d | 0,7 / 2,9 % | 11,5 / 12,9 % |
| A | 6,3 / 17,2 / 29,2 / 45,3 % | 6,3 / 17,8 / 29,9 / 44,2 % | 60 / 66 d | 23 / 38 d | 0,3 / 2,9 % | 15,1 / 12,9 % |
| B | 10,2 / 23,4 / 37,5 / 49,5 % | 10,7 / 24,8 / 37,5 / 49,7 % | 53 / 58 d | 17 / 31 d | 0,4 / 2,4 % | 8,2 / 12,0 % |
| C | 12,5 / 27,2 / 41,2 / 52,5 % | 12,5 / 27,7 / 41,1 / 53,4 % | 48 / 52 d | 15 / 30 d | 1,7 / 3,2 % | 14,4 / 13,7 % |
| D | 13,0 / 27,6 / 42,2 / 54,3 % | 13,1 / 28,6 / 41,9 / 54,5 % | 47 / 50 d | 15 / 28 d | 9,4 / 9,4 % | 18,5 / 21,9 % |
| E | 15,7 / 31,5 / 46,4 / 58,6 % | 15,2 / 31,2 / 46,0 / 58,1 % | 45 / 45 d | 13 / 26 d | 24,7 / 18,0 % | 27,6 / 29,6 % |

In de replay is er bij elke optie 0 breaches, ook bij 0,25R kosten. De starts in 2026 hebben bij elke optie 0 breaches en 0 vastgelopen. Bij D en E vond de tegencontrole wél breaches: na een winnende dag liet de guard daar een 4H-trade van 4,5–5 % door.

## Trucs binnen de FTMO-regels

**Werkt**
- **Micro-trades voor de 4 handelsdagen** (geen code, met de hand).
  - FTMO telt elke dag (Praagse tijd) waarop je minstens één positie opent, zonder minimumgrootte.
  - In 2026 wachtte 24 % van de fase-1-passes en 36 % van de fase-2-passes alleen nog op die dagen. Over alle starts was de mediane wachttijd 3,7 en 5,7 dagen.
  - Effect: fase 1 binnen 7 dagen gaat van 0,5 naar 4,4 %, en in 2026 gaan beide fases van 42 naar 39 dagen. Het risico blijft hetzelfde.
  - Geen FTMO-tekst verbiedt het, maar FTMO heeft het ook niet bevestigd: vraag het eerst.
- **De lock** (code).
  - Zodra de fase 4 handelsdagen heeft, mikt een nieuwe trade op de prijs waar je saldo precies het doel haalt, als die dichterbij ligt dan zijn eigen doel. Zo verlies je geen pass meer aan een trade die het doel aantikt en dan omdraait.
  - Voorbeeld: een goud-4H-long op 2 juli 2025 liep naar +1,9R, terwijl 1,11R genoeg was, en raakte daarna zijn stop. Met de lock haalt de start van 14 mei 2025 het op 2 juli 2025 in plaats van op 21 januari 2026.
  - Alleen de lock: van 75 naar 70 dagen gehusseld. Op het echte pad is hij sneller in 597 starts en trager in 3.
  - Lock plus micro-trades: van 75 naar 66 dagen, bij hetzelfde risico.
- **`STOP_AT_TARGET=1` houden:** dat is een verzekering en levert geen snelheid op (ongeveer een halve dag).
- **Al in gebruik en toegestaan:** posities over nacht en in het weekend houden, en er is geen tijdslimiet. Nieuws handelen mag in de evaluatie, maar houd de 30/30-blackout van de bot aan: zonder die blackout kostte het 6,0R.

**Werkt niet** (gemeten)
- **Alleen `RISK` omhoog:** `RISK=2` is trager (85 in plaats van 75 dagen gehusseld), loopt vaker vast (5,1 in plaats van 2,9 %) en geeft bij hoge kosten 3,4 % breaches. 2,5 en 3 maken beide fases niet sneller. Alleen 1,75 helpt iets: 72 dagen, maar 4,0 % vastgelopen.
- **PROTECT of een sprint** (eerst hoog inzetten, dan laag): trager, en er is geen breach om te voorkomen.
- **Hogere inzet in fase 2:** gehusseld trager (bij 2,0 %: 80–81 in plaats van 75–76 dagen).
- **Trade-management** (eerder break-even, deels winst nemen, trailing stop, tijdstop, een dichterbij doel): allemaal trager.
  - Een hogere winrate is geen snelheid, want de challenge betaalt in R.
  - Voorbeeld: de helft sluiten op 1R plus break-even wint 61 % van de trades, maar haalt fase 1 binnen 30 dagen in maar 14,5 % van de starts (nu 41,7 %).
- **1-Step:**
  - Niet sneller: 77 dagen bij 1,0 %, tegen 74 voor beide 2-Step-fases samen.
  - Boven 1,0 % faalt 6–39 % van de starts.
  - Voor aankopen vanaf 12 oktober geldt de Consistency-regel: je beste dag mag hooguit 50 % van de winst zijn.
- **Swing-account:** trager (beide fases 81 in plaats van 73 dagen) door de lagere hefboom.
- **Losser guard** (4,5 % per dag, 9,8 % totaal): bij hoge kosten 22–30 % echte breaches.
- **Meer markten, een tweede setup, lossere regels** (onderzoek van 15–16 okt): meer vastgelopen accounts, en in 2026 hooguit 1–2 dagen sneller.

**Wat FTMO verbiedt** (ftmo.com/en/forbidden-trading-practices/)
- meer dan 2.000 serververzoeken per dag (EA-hyperactiviteit);
- gap trading: een trade openen terwijl groot nieuws, macrocijfers of earnings gepland staan, of 2 uur of minder voordat een markt 2 uur of langer dichtgaat;
- manipulatie, en tegengestelde posities over accounts heen;
- software of AI voor een oneerlijk voordeel;
- trades die niet op echt handelen lijken (overleveraging, eenzijdig gokken, account rolling);
- winst over dagen spreiden om de Best Day- of Consistency-regel te omzeilen;
- substantieel grotere posities. B maakt je grootste trade juist kleiner: 2,81 %, nu 3 %;
- iemand anders op je account laten handelen.

Geen van de trucs hierboven raakt deze lijst, en EA's en algo-trading zijn expliciet toegestaan. Let wel op één ding: een EURUSD- of NAS100-limietorder die vrijdag laat 4 uur blijft liggen, kan binnen 2 uur voor de sluiting vullen. Bijkopen in een lopende winnaar (pyramiding) laat ik liggen, omdat FTMO "herhaald risico verhogen per trade-idee" noemt.

## Mijn advies

**Kies optie B: veilig sneller, met lock.**
- **Het grootste voordeel zonder extra risico:** beide fases van 73 naar 53 dagen (gehusseld 75 → 58, in 2026 42 → 31). Fase 1 binnen 14 dagen gaat van 10,3 naar 23,4 %.
- **De tegencontrole:** B was in 41 van de 45 stresstests even veilig als nu of veiliger. Begint de challenge in vier slechte maanden, dan loopt B in 41 % van de gevallen vast, tegen 48 % nu.
- **Niet C:** C is 3–6 dagen sneller dan B, maar alleen veilig met drie codewijzigingen (lock, size-down en de guard-fixes). Met de fixes kost C 55 dagen bij 3,4 % (gehusseld). Dat kan later, als B goed draait. Overweeg daar dan ook de −8 %-trede die je afwees: in de snellere combinaties kost hij geen mediane dagen en verlaagt hij het risico (bij heel snel van 18,0 naar 12,0 %).
- **Niet A:** A is 9–13 dagen sneller, maar met 4H-trades van 3,5 % houd je maar de helft van je ruimte voor slippage over.
- **Niet D en E:** de tegencontrole heeft ze afgekeurd. Ze geven echte breaches en 9,4–18,0 % in plaats van 2,4 % kans op falen.
- **Eerlijk gezegd:**
  - De regels zijn op 2024–2026 afgesteld, en de gehusselde geschiedenissen gebruiken dezelfde trades opnieuw. Live gaat het dus waarschijnlijk trager.
  - BTC op een kwart rust op het zwakke voordeel van BTC in diezelfde data.
  - De lock is nog niet gebouwd, en de micro-trades wachten op FTMO.

## Wat jij moet doen

1. **Vraag het FTMO-support** (kan vandaag, in het Engels): *"Does a day count as a trading day if I open and close one 0.01-lot position that day, and is that allowed?"*
2. **Na hun ja: doe de micro-trades.** Je challenge loopt sinds 14 oktober, dus dit helpt al in fase 1.
   - Op elke werkdag waarop de bot nog niets opende: open in de MT5-app één positie van 0,01 lot en sluit hem meteen. Neem
     liefst een markt die de bot niet handelt, zoals GBPUSD. Een handmatige positie stoort de bot ook op zijn eigen markten
     niet: de vensters en de guard lezen alleen posities met het magic number van de bot, en de teller van de handelsdagen
     telt elke positie mee (nagekeken in `kronos_trader/execution/mt5.py`).
   - Ga door tot MetriX 4 handelsdagen toont. Begin in fase 2 opnieuw vanaf dag 1.
   - Dat zijn ongeveer 3–4 trades per fase, van een paar cent elk.
3. **Zeg ja tegen B; ik pas de code aan na jouw ja.**
   - De profielen: dat is config en geen code, maar het verandert wel de bevroren live-set.
     - `config/dorus_live.yaml`, `config/dorus_live_gold.yaml`, `config/dorus_live_nas100.yaml`: `zone_risk_multiplier: {4H: 2.0}` wordt `zone_risk_multiplier: {4H: 1.25}`
     - `config/dorus_live_btc.yaml`: `stake_multiplier: 0.5` wordt `stake_multiplier: 0.25`
   - De lock bouw en test ik op een kopie. Daarna is een herstart nodig.
4. **Zet daarna in `scripts\ftmo_local.bat`:**
   ```
   set "RISK=2.25"
   set "PRODUCT=ftmo_2step"
   set "TARGET=10"
   set "STOP_AT_TARGET=1"
   ```
   - Doe dit pas als de profielwijziging binnen is; `start_ftmo.bat` haalt hem op met `git pull`.
   - Zet geen `PROTECT`. In fase 2: `set "TARGET=5"` en herstarten; `RISK` blijft 2.25.
   - Let op: `RISK=2.25` met de oude 4H ×2 maakt een 4H-trade 4,5 %, en die weigert de guard bijna altijd.
   - Tot de lock er is, geven deze inzet en de micro-trades samen al 68 dagen gehusseld bij 2,8 % (nu 75 dagen bij 2,9 %).

Bronnen (in de repository is niets veranderd):
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/fast/combine/out/final_table.txt
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/fast/combine/out/points.txt
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/fast/skeptic/out/skeptic_table.txt
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/fast (deelstudies: stakes, management, ftmo_rules, earlier_research)
## Aanvulling: optie B zonder mini-trades

Max wees de mini-trades af. Optie B is daarom opnieuw nagespeeld zonder mini-trades: de inzet (`RISK=2.25`, 4H ×1,25,
BTC ×0,25) plus de lock. De handelsdagen komen dan alleen van de eigen trades van de bot. Dit is gerekend met dezelfde
replay als de tegencontrole. Die geeft voor "nu" exact de cijfers uit de tabel hierboven.

| | Nu | B zonder mini-trades | B met mini-trades |
|---|---|---|---|
| Fase 1, mediaan (echt / gehusseld) | 37 / 40 d | 32 / 32 d | 31 / 31 d |
| Beide fases, mediaan (echt / gehusseld) | 73 / 76 d | 61 / 64 d | 53 / 58 d |
| Starts in 2026: fase 1 / beide fases | 24 / 42 d | 20 / 37 d | 17 / 31 d |
| Fase 1 binnen 30 dagen (echt) | 41,7 % | 48,4 % | 49,5 % |
| Vastgelopen (echt, van 967 / gehusseld) | 7 / 3,1 % | 4 / 2,4 % | 4 / 2,3 % |
| Breaches | 0 | 0 | 0 |

Alleen de inzet, zonder lock: beide fases 65 dagen echt en 72 gehusseld, met 2,5 % vastgelopen. De lock levert dus
ongeveer de helft van de winst. Winrate en R per trade blijven gelijk, want B kiest dezelfde trades. Gehusseld betekent
200 maand-geschiedenissen (seed 7, zoals bij de tegencontrole), bij 0,10R kosten. Bronnen:
`scratchpad/bnomicro/` (`run_b.py`, `summ_b.py`).
