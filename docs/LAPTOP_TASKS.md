# Claude Code on the laptop: the standing tasks (14 October)

The bot runs on Max's laptop; this session runs in the cloud and cannot see the laptop. Claude Code on the laptop can:
it reads the journal, the terminal's history and the windows, runs the read-only scripts and explains them. It changes
nothing: no code, no config, no orders, no git writes on `feature/kronos-trader` (the windows pull that branch at every
restart). The rules it works under are in `C:\Users\maxge\.claude\CLAUDE.md`; the prompts below are pasted as they are.

Each prompt starts in `C:\Users\maxge\Kronos`. Reports go to `C:\Users\maxge\kronos_notes\` (outside the repository).

## Every evening (2 minutes)

```
Dagstatus. Alleen lezen. 1) Zijn de vier heartbeat_*.json in journal_ftmo jonger dan 5 minuten, status ok? 2) Draai het
forward-report zoals scripts\ftmo_report.bat het doet, zonder de pause en zonder de browser: balans, trades van vandaag
met R na kosten, open posities en limits, de ruimte tot de FTMO-grenzen (dag en totaal). 3) Staan er vandaag regels
not_executed, skipped, stale, deferred, did_not_fill, limit_gone, breakeven_failed of no_stop in journal_ftmo\trades.csv?
Geef ze met de reden. 4) Vergelijk elke trade van vandaag met het setup-bericht: instap, stop, doel, lots. Sla op in
kronos_notes\dag_<datum>.md en vat samen in tien regels.
```

## After every trade (when a 💸 fill came in)

```
Trade-check van de laatste fill in journal_ftmo\trades.csv. Alleen lezen. Geef: markt, richting, zone (timeframe,
prijzen, wanneer ontstaan, wanneer voor het eerst aangeraakt), bevestiging (type, timeframe, tijd), instap, stop,
doel, R:R, lots, risico in dollars, en de spread/slippage uit het forward-report (scripts\ftmo_report.bat zonder pause).
Open de nieuwste chart van die markt in charts\ en beschrijf wat erop staat. Klopt de stop met "achter de sweep sinds
de re-entry" en het doel met "de oorsprong van de beweging"? Zeg precies wat afwijkt.
```

## Friday evening, after 22:30 (the parity check ran by itself)

```
Weekreview. Alleen lezen. 1) Leg het nieuwste rapport in journal_ftmo\parity uit: elk signaal dat geen match is, met de
reden; is er een "live only" of "outcome differs" die op een bug wijst? 2) Uit journal_ftmo\trades.csv: alle trades van
deze week met R na kosten, winrate, gemiddelde winst en verlies in R, en de dagen zonder trade. 3) Uit het forward-report:
spread en slippage per trade tegen de aannames (EURUSD 1 pip, goud 2 pips, NAS 1.5 punt, BTC 15 dollar, plus commissie).
4) Wat ging anders dan verwacht? Sla op in kronos_notes\week_<maandag>.md.
```

## Once: the spreads of NAS100 and BTC (the two never measured)

```
Spreadmeting, alleen lezen, de botvensters mogen doordraaien. Zet MT5_PATH op
"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe" en haal MT5_LOGIN, MT5_PASSWORD en MT5_SERVER uit de
omgeving van dit proces. Draai voor de laatste drie werkdagen:
.venv\Scripts\python.exe -m kronos_trader --config config/dorus_live.yaml mt5-spreads --symbols NAS100=US100.cash,BTCUSD --day <datum>
Staat er "no prices", open dan in MT5 een M1-grafiek van US100.cash en BTCUSD, wacht een minuut en probeer opnieuw. Geef
per markt mediaan, 90e percentiel en maximum in punten/dollars, en vergelijk met de aannames van de backtest (NAS 1.5
punt, BTC 15 dollar). Sla op in kronos_notes\spreads.md.
```

## Once: the BTC candle stamps (the research data cuts the day at a different hour than FTMO)

```
Alleen lezen. Zoek de nieuwste geëxporteerde kaarsen van BTCUSD in journal_ftmo\parity\ (of journal\parity\ van de
trial): de bestanden met 4H, 1D en 1W in de naam. Geef per bestand de eerste tien tijdstempels (UTC) en zeg op welk uur
de dagkaars begint en op welke weekdag en welk uur de weekkaars begint. Doe hetzelfde voor EURUSD en XAUUSD ter
vergelijking. Sla op in kronos_notes\kaarsen.md.
```

## When the account reaches +10 % (the windows do not stop by themselves)

The windows never stop at the target: `TARGET` (when set in `ftmo_local.bat`) only drives the protect step, and the
day report shows the distance. When the day report shows +10 % or more: with four trading days done, let the open
positions finish, stop the windows outside the sessions and request the verification in the FTMO dashboard; with
fewer than four days, Max decides between trading on and waiting (a day with a position opened counts, whatever its
size). Then:

```
Alleen lezen. Hoeveel handelsdagen telt de FTMO-challenge tot nu toe (dagen met een geopende positie, Praagse tijd) in
journal_ftmo\trades.csv en in het forward-report? Wat is de gesloten balans en wat staat er open? Zijn alle vier de
vensters gestopt (geen verse heartbeat_*.json)?
```

## Once: the dashboard

```
Start het dashboard met scripts\dashboard.bat en controleer in de browser op http://127.0.0.1:8765/ dat elke markt
groen is, dat de commit per venster gelijk is, en dat de grafieken en de parity-check verschijnen. Meld wat ontbreekt.
Laat het venster open; sluit het alleen als Max dat vraagt.
```

## Once: the laptop itself

```
Alleen lezen. 1) Is de slaapstand aan de lader uit (powercfg /query) en staat het deksel dichtklappen op "niets doen"?
2) Staat er een Windows-update met herstart klaar en wat zijn de actieve uren? 3) Bestaat de geplande taak "Kronos parity"
(schtasks /Query /TN "Kronos parity")? 4) Hoeveel vrije schijfruimte en geheugen is er, en hoe groot is journal_ftmo\?
Geef per punt ✅ of ⚠️.
```

## When the bot has to be restarted (Max does it; Claude Code checks)

Only outside the sessions (after 17:30, before 08:30 or at the weekend). Max closes the five windows and runs
`scripts\start_ftmo.bat`; then:

```
Controleer de herstart. Lees de nieuwste journal_ftmo\starts\*.json per markt: dezelfde commit voor alle vier, zonder
local changes, account_size 10000, risk_pct 1.5, max_open_trades 2, max_open_per_symbol 2 bij EURUSD en 1 bij de rest,
min_rr EURUSD 1.0, XAUUSD 0.8, NAS100 0.8, BTCUSD 0.5. Zijn de heartbeats vers? Kwamen de vier startmeldingen op Telegram?
```

## What Claude Code must not do

Change code, profiles or `scripts\ftmo_local.bat`; place, change or close orders; log in to MT5; restart or stop the
windows on its own; commit, push, reset or checkout; show secrets (tokens, passwords, the ping address); download or
install anything. A finding that needs a change goes to the cloud session, which tests it first.
