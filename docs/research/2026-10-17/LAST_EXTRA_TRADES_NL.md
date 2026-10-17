# De laatste bronnen van extra trades (17 oktober)

**Nee, ook hier zitten geen goede extra trades in.**

- **Getest:** de laatste 6 forexparen (EURNZD, GBPCAD, GBPNZD, NZDCAD, NZDCHF, NZDJPY) en BTC op zaterdag en zondag, met dezelfde regels en vensters.
- **Extra trades:** samen bijna 8 per maand. Elk paar geeft er ongeveer 1, het BTC-weekend 1 à 1,5.
- **Ze verliezen allemaal.** Na FTMO-kosten staan alle 7 in de min, in beide helften (feb 2024 – mei 2025 en jun 2025 – sep 2026). Samen is dat ongeveer −140R. Zelfs zonder spread haalt er geen één je lat.
- **BTC in het weekend** wint maar ongeveer 1 op de 3 trades, doordeweeks de helft of meer. Op FTMO's candles zakt BTC daardoor van +19,9R naar −4,8R.
- **De challenge wordt er slechter van.** Met één van de paren erbij lopen in de replay 19 tot 97 starts vast, in plaats van 7.
- **Toeval:** van 7 kandidaten zonder voordeel haalt er gemiddeld 1 je lat. Hier haalde er geen één het.

**Advies:** niets toevoegen, en BTC blijft alleen maandag t/m vrijdag. Alle 21 forex-crosses zijn nu getest, en geen enkele haalt je lat. Verder zoeken raad ik af: van de 53 geteste markten haalden er 3 je lat. Dat is minder dan de 8 die je bij toeval al zou verwachten.

| Markt | Trades | Per maand | R per trade | Helften (R) | 2026 (trades) | Lat |
|---|---|---|---|---|---|---|
| EURNZD | 33 | 1.04 | -0.52 | -10.7 / -6.6 | -6.1 (8) | nee |
| GBPCAD | 30 | 0.94 | -0.48 | -7.5 / -6.9 | -1.4 (7) | nee |
| GBPNZD | 32 | 1.01 | -0.51 | -3.5 / -12.9 | -9.3 (16) | nee |
| NZDCAD | 44 | 1.38 | -0.81 | -18.5 / -17.2 | -7.2 (11) | nee |
| NZDCHF | 31 | 0.97 | -0.37 | -5.2 / -6.4 | +2.1 (4) | nee |
| NZDJPY | 31 | 0.97 | -1.04 | -14.1 / -18.2 | -13.8 (11) | nee |
| BTC weekend | 45 | 1.41 | -0.41 | -15.5 / -3.1 | -0.7 (4) | nee |
| BTC weekdays, live profile (reference) | 85 | 2.66 | +0.72 | +16.9 / +44.0 | +39.0 (18) | haalt |
| BTC weekend, FTMO-day candles | 34 | 1.06 | -0.66 | -14.0 / -8.5 | -1.9 (4) | nee |
| BTC weekdays, live profile, FTMO-day candles (reference) | 89 | 2.78 | +0.22 | +7.5 / +12.5 | +14.5 (17) | haalt |
| BTC weekend, Sunday only | 23 | 0.72 | -0.11 | -5.1 / +2.5 | +0.3 (3) | nee |

De twee BTC-rijen "weekdays" zijn de eigen BTC-trades van de live-set (ter vergelijking), geen extra trades.
Bronnen: scratchpad `lastextra/` (runs per paar, BTC-weekend, de beoordeling in `judge/`).
