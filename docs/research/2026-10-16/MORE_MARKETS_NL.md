# Meer FTMO-markten (16 oktober)

## Kort antwoord

**Nee. Ook in de rest van FTMO's lijst zit die ene goede trade per maand niet.** Aan de bot en de repository is niets veranderd.

- **Getest:** 47 FTMO-markten en 12 varianten. Dat zijn 21 forexparen, 7 indices, 7 metalen en grondstoffen en 12 munten. Elke markt draaide op het ongewijzigde profiel van de live-markt die er het meest op lijkt, van feb 2024 tot sep 2026, na kosten.
- **3 van de 47 halen je lat:** USDCAD en GER40 (uit het vorige rapport) en ETHUSD. Dat is wat toeval ook geeft. Alle 47 samen verliezen −0,25R per trade over 2.233 trades, en 39 ervan staan op min.
- **Geen van de drie maakt de challenge beter.** Met USDCAD of GER40 lopen 33 starts vast in plaats van 7, met alle drie samen 42. ETH brengt het naar 0, maar dat is geluk. Bij FTMO's spread haalt ETH je lat niet meer, en in 2021–2023 verloor hij −13,1R.
- **Vastlopen is geen vertraging maar verlies.** Volgens FTMO's FAQ kan een evaluatie na 30 dagen zonder activiteit worden beëindigd.

*Jouw lat:* positief in beide helften (feb 2024 – mei 2025 en jun 2025 – sep 2026) en niet negatief in 2026, na kosten.
*Vastgelopen:* het account staat zo dicht bij de −9,5 %-grens dat de guard elke nieuwe trade weigert, en er komt 30 dagen geen trade. Bij de live-set gebeurt dat nu in 7 van de 967 challenge-starts (feb 2024 – sep 2026).

## Markten die erdoor komen

- **ETHUSD** (BTC-profiel, halve inzet): 1,6 trades per maand, 59 % winst, +0,29R per trade, 2026 +6,1R (13 trades). Challenge: vastgelopen 7 → 0. Starts in 2026 halen fase 1 even snel: 72,5 % binnen 30 dagen, nu 72,1 %.
- **USDCAD** (EURUSD-profiel): 1,3 trades per maand, 34 % winst, +0,27R per trade, 2026 +12,9R (11 trades). Challenge: vastgelopen 7 → 33. Starts in 2026 zijn trager: 66 % binnen 30 dagen, nu 72 %.
- **GER40** (NAS100-profiel): 1,1 trades per maand, 40 % winst, +0,34R per trade, 2026 +5,1R (5 trades). Challenge: vastgelopen 7 → 33. Starts in 2026: 74 % binnen 30 dagen, nu 72 %.
- **Alle drie samen:** 3,4 trades per maand extra en fase 1 iets sneller (44,9 % binnen 30 dagen, nu 41,7 %), maar 42 vastgelopen starts.

Waarom ze er toch niet bij moeten:
- **ETH** wint alleen op Binance-koersen met 1 USD spread.
  - Bij de FTMO-spread die fxverify meet (2,56 USD) blijft +3,9R over, en de tweede helft is −0,7R.
  - Op Bitstamp-koersen, de koersbron van je BTC-backtest, is het −10,2R.
  - De 7 → 0 komt van één dag. Op 9 april 2024 hielden ETH en BTC beide plekken bezet, zodat een verliezende goudtrade niet doorging. Bij FTMO's spread lopen er weer 6 vast.
- **USDCAD en GER40** verliezen juist als de live-set verliest: USDCAD −2,4R in maart–juni 2024, GER40 −3,6R in de verliesmaanden van de live-set. Daar komen de vastgelopen starts vandaan, niet van bezette plekken.
- **Net niet:** EURJPY (+53,0R, in 2026 +22,6R).
  - Alle 7 trades in 2024 verloren.
  - +23,8R komt uit één trade die 107 dagen openstond.
  - Er lopen 51 starts vast.

## Alles wat getest is

Feb 2024 – sep 2026, 1 % risico, na spread en 0,10R kosten per trade, zoals bij de live-set. *Vastgelopen* telt de starts van de 967 waarin de markt naast de live-set draait (live-set alleen: 7). Een * betekent: al in het vorige rapport.

| Markt | Tr/mnd | R/trade | Helften (R) | 2026: R (trades) | Mrt–jun 2024 (R) | Vastgelopen | Advies |
|---|---|---|---|---|---|---|---|
| **Forex: USD-paren** (EURUSD-profiel) | | | | | | | |
| USDCAD* | 1,3 | +0,27 | +4,3 / +6,7 | +12,9 (11) | −2,4 | 33 | nee (haalt lat, zie boven) |
| NZDUSD* | 0,7 | −0,02 | −9,9 / +9,6 | +0,9 (3) | −4,4 | 19 | nee |
| USDJPY* | 1,5 | −0,25 | +6,8 / −18,8 | −12,2 (14) | −5,5 | 43 | nee |
| GBPUSD* | 0,9 | −0,46 | −6,0 / −7,7 | −9,9 (9) | −2,2 | 19 | nee |
| USDCHF* | 1,1 | −0,56 | −8,1 / −10,9 | −11,0 (14) | −2,2 | 32 | nee |
| AUDUSD* | 0,7 | −0,66 | −10,0 / −3,7 | −3,3 (3) | −1,1 | 21 | nee |
| **Forex: crosses** (EURUSD-profiel) | | | | | | | |
| EURJPY | 1,2 | +1,39 | −2,4 / +55,3 | +22,6 (16) | −3,3 | 51 | nee (+23,8R uit 1 trade) |
| EURGBP | 0,8 | +0,10 | +2,2 / +0,5 | −2,2 (2) | −4,4 | 37 | nee |
| CADCHF | 0,6 | −0,02 | +3,1 / −3,5 | −5,1 (3) | +3,6 | 6 | nee |
| GBPJPY | 0,8 | −0,46 | −15,1 / +3,4 | +6,3 (6) | −6,6 | 78 | nee |
| AUDCAD | 0,9 | −0,46 | −0,4 / −12,4 | −7,5 (9) | +2,0 | 23 | nee |
| CHFJPY | 1,7 | −0,51 | −6,1 / −21,2 | −8,4 (17) | −7,0 | 80 | nee (FTMO-limiet in 66 starts) |
| AUDJPY | 1,2 | −0,59 | −9,0 / −12,8 | −8,8 (11) | −3,4 | 51 | nee |
| EURCHF | 0,6 | −0,59 | −5,4 / −5,8 | +0,8 (9) | −3,2 | 7 | nee |
| EURCAD | 1,0 | −0,61 | −18,1 / −2,1 | −2,4 (10) | −2,2 | 84 | nee |
| AUDNZD | 1,2 | −0,61 | −9,1 / −13,4 | −5,7 (8) | −0,8 | 37 | nee |
| GBPAUD | 1,7 | −0,67 | −14,4 / −21,6 | −5,1 (9) | −3,5 | 98 | nee |
| GBPCHF | 1,0 | −0,69 | −13,6 / −7,8 | −8,4 (7) | −2,2 | 14 | nee |
| CADJPY | 1,2 | −0,77 | −20,4 / −8,2 | −6,0 (8) | −4,6 | 16 | nee |
| EURAUD | 1,4 | −0,78 | −18,0 / −17,2 | −8,1 (17) | +0,7 | 79 | nee |
| AUDCHF | 0,8 | −0,87 | −12,2 / −10,4 | −1,5 (4) | −3,4 | 23 | nee |
| **Indices** (NAS100-profiel) | | | | | | | |
| GER40* | 1,1 | +0,34 | +5,6 / +6,2 | +5,1 (5) | −0,2 | 33 | nee (haalt lat, zie boven) |
| UK100 | 1,2 | +0,04 | −1,2 / +2,6 | +3,9 (8) | −3,4 | 50 | nee (1e helft net negatief) |
| JP225 | 1,0 | −0,19 | −5,9 / −0,1 | −2,1 (12) | −2,2 | 45 | nee (ook op Tokio-klok) |
| HK50 | 0,7 | −0,34 | −11,6 / +4,1 | −2,2 (2) | −3,7 | 74 | nee (ook op Hongkong-klok) |
| US500* | 1,3 | −0,35 | +1,8 / −16,0 | −6,6 (10) | −2,5 | 75 | nee |
| FRA40 | 1,0 | −0,38 | +1,1 / −12,7 | −6,4 (10) | +3,5 | 64 | nee |
| AUS200 | 1,0 | −0,51 | −8,1 / −8,1 | −0,3 (6) | +0,6 | 73 | nee (ook op Sydney-klok) |
| **Metalen en grondstoffen** (goudprofiel) | | | | | | | |
| Palladium (XPDUSD) | 0,3 | +0,02 | +0,0 / +0,3 | −0,2 (5) | +0,0 | 7 | nee (11 trades; ook bij smallere spread) |
| Koper (XCUUSD) | 3,7 | −0,12 | −0,0 / −14,1 | −7,7 (36) | +1,4 | 122 | nee (FTMO-limiet in 38 starts) |
| Brent (UKOIL) | 4,7 | −0,15 | −17,0 / −5,5 | −2,0 (38) | −5,5 | 194 | nee (FTMO-limiet in 7 starts) |
| WTI (USOIL) | 3,9 | −0,17 | −22,6 / +0,8 | −9,8 (32) | −1,3 | 104 | nee (FTMO-limiet in 4 starts) |
| Aardgas (NATGAS) | 0,6 | −0,33 | +3,3 / −9,9 | −7,7 (7) | +1,7 | 0 | nee (ook bij smallere spread) |
| Zilver (XAGUSD)* | 4,8 | −0,36 | −22,4 / −32,6 | −14,2 (56) | +0,5 | 180 | nee |
| Platina (XPTUSD) | 1,9 | −0,47 | +0,9 / −28,4 | −19,7 (31) | +1,8 | 107 | nee |
| **Crypto** (BTC-profiel) | | | | | | | |
| ETHUSD | 1,6 | +0,29 | +5,9 / +8,7 | +6,1 (13) | −2,4 | 0 (6 bij FTMO-spread) | nee (haalt lat, zie boven) |
| XRPUSD | 1,8 | +0,02 | −2,4 / +3,7 | +4,0 (22) | −1,1 | 3 | nee |
| XLMUSD | 1,4 | −0,04 | +0,6 / −2,2 | −4,8 (19) | +1,8 | 0 | nee |
| SOLUSD | 2,3 | −0,13 | −8,0 / −1,9 | −2,9 (19) | −2,6 | 17 | nee |
| DOGEUSD | 1,9 | −0,18 | +3,3 / −14,4 | −7,9 (19) | +0,3 | 9 | nee |
| BNBUSD | 2,2 | −0,19 | −3,8 / −9,1 | −2,0 (15) | −7,2 | 60 | nee |
| AAVEUSD | 1,4 | −0,24 | −11,2 / +0,5 | +4,2 (9) | −3,4 | 25 | nee |
| LINKUSD | 1,5 | −0,26 | −5,4 / −7,1 | −4,8 (14) | +0,9 | 15 | nee |
| DOTUSD | 1,2 | −0,27 | −7,5 / −2,6 | −1,8 (10) | −1,6 | 15 | nee |
| AVAXUSD | 1,6 | −0,29 | −4,2 / −10,4 | −6,5 (13) | −2,3 | 21 | nee |
| ADAUSD | 2,4 | −0,32 | +3,8 / −28,7 | −25,1 (31) | +1,4 | 11 | nee |
| LTCUSD | 1,6 | −0,36 | −4,0 / −14,6 | −6,0 (21) | −2,5 | 16 | nee |

- **Het probleem zijn niet de plekken, maar de maanden.**
  - Van de 2.233 trades openden er maar 29 terwijl de live-set beide plekken bezet hield.
  - De maandcorrelatie met de live-set is laag (−0,37 tot +0,49).
  - Maar 33 van de 47 verloren in maart–juni 2024, toen de live-set −7,6R maakte. Daar ontstaan de meeste vastgelopen starts.
- **Weinig vastgelopen starts bij een verliezer zegt weinig** (aardgas en XLM 0, XRP 3). Een kleine kostenwijziging verschuift dat getal met 5 tot 90 starts.
- **Kosten:** FTMO publiceert geen spreads, dus die zijn geschat. Geen advies hangt ervan af, met twee uitzonderingen:
  - UK100 haalt de lat net wél zonder de vaste 0,10R per trade.
  - ETH haalt de lat niet meer bij FTMO's spread.

**Niet getest** (wel op FTMO's lijst van 166 symbolen):
- **Forex:** EURNZD, GBPCAD, GBPNZD, NZDCAD, NZDCHF en NZDJPY (de data is klaar, maar er was geen tijd meer voor de backtest). Ook de 4 EUR-exoten (EURCZK, EURHUF, EURNOK, EURPLN) en de 11 USD-exoten.
- **Indices:** US30, US2000, EU50, SPN35 en N25. Er was geen gratis 1-minuutdata te krijgen: HistData heeft ze niet en Dukascopy was te traag. Ook DXY.cash niet.
- **Grondstoffen:** HEATOIL en de landbouw-CFD's (cacao, koffie, maïs, soja, tarwe, katoen, suiker). Ook goud en zilver in EUR en AUD.
- **Crypto:** DASH, XMR (niet meer op Binance), NEO en de overige altcoins.
- **Aandelen:** geen van de 59.

## Waarom niet meer

Een markt zonder voordeel haalt je lat bij toeval ongeveer 1 op de 6 keer: bij 47 markten verwacht je er dan al 7,5, en zelfs met de verliezende edges die deze profielen op nieuwe markten echt halen (gemiddeld −0,32R per trade) komen er in 31 % van de gevallen 3 of meer door, net als nu. Elke extra markt die we testen voegt ongeveer 0,04 verwachte doorkomers toe, bijna allemaal vals, dus meer testen levert vooral meer toevalstreffers op en niet die ene goede trade.

## Beslissingen voor jou

1. **USDCAD, GER40 of ETHUSD toevoegen aan de FTMO-vensters?** Advies: **nee.** USDCAD en GER40 laten elk 33 starts vastlopen in plaats van 7, alle drie samen 42. ETH's 7 → 0 is geluk. Een wijziging aan de FTMO-vensters gaat sowieso alleen met jouw uitdrukkelijke OK.
2. **ETHUSD eerst op het demovenster zetten?** Advies: **nee.** Het bewijs is te zwak, en een demo beslist het niet. Bij 1,6 trades per maand duurt het zelfs met ETH's beste backtestcijfers ongeveer 3,5 jaar om zijn voordeel van nul te onderscheiden. Bij FTMO's spread duurt het tientallen jaren.
3. **FTMO's echte spreads meten met mt5-spreads op de laptop?** Advies: **ja.** Het verandert niets aan de bot.
   - Voor ETH beslist het meteen: bij 2 USD haalt hij je lat nog, bij 2,56 USD niet meer.
   - Belangrijker zijn je live-markten. De gepubliceerde spreads liggen ver boven wat de backtest rekent:
     - BTC ongeveer 59 USD (fxverify), tegen 15 USD in de backtest;
     - goud 45 cent als weekgemiddelde (PropSpread) en 34–37 cent binnen de handelsvensters op 6 oktober, tegen 20 cent in de backtest.
   - Kloppen die cijfers, dan zijn de backtestcijfers van BTC en goud te rooskleurig.
4. **De extra vangnet-trede (−8 % → 0,25 %) uit het vorige rapport aanzetten, in plaats van een markt toe te voegen?** Advies: **ja**, maar alleen met jouw uitdrukkelijke OK, want het verandert de FTMO-vensters. In de replay gaan de vastgelopen starts van 7 naar 0, zonder dat het trager wordt. Het vorige rapport liet open of FTMO een account na 30 dagen zonder trade stopt. Volgens FTMO's FAQ kan dat, dus elke vastgelopen start is een verloren challenge.
5. **Nog meer FTMO-markten screenen (US30, US2000, EU50, de overige crosses, aandelen)?** Advies: **nee.** Met geleende profielen levert dat vooral valse treffers op.

Bronnen (alles in de scratchpad, niets in de repository):
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/markets (de vier screens: fx_crosses, indices, commodities, crypto)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/markets/combine/out/summary.txt (challenge-replay)
- /tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/markets/skeptic/out/stats.json (tegencontrole van alle 47 markten)