# Kronos Trader: the current state (7 October 2026)

What runs, with which settings, and what the evidence says. The profile files are the source of truth: every setting
there carries its reason and date. Older pages describe how the rules came about: `docs/STRATEGY.md` starts from
Max's original rules (1:3 R:R, 1 % risk), which the profiles have since replaced with the values below.

## What runs where

| Script | Account | Markets | Orders |
|---|---|---|---|
| `scripts/start_live.bat` | MetaQuotes-Demo (MT5) | EURUSD, XAUUSD; BTCUSD on paper with Bitstamp prices | MT5 market orders with server-side stop and target, no approval |
| `scripts/start_ftmo.bat` | FTMO MT5 terminal, 10,000 (the free trial, then the 2-Step challenge: setup B) | EURUSD, XAUUSD, NAS100 (`US100.cash`), BTCUSD | the same, NAS100 by limit order (below); journal in `journal_ftmo/` |

Each market runs in its own window and polls every 60 seconds; signals come from closed candles (5m the smallest).
Both scripts `git pull` before they start, so a change on this branch reaches the windows at their next start and
never a running one. Local values (risk, symbol names) go in `scripts/*_local.bat`, which git ignores; passwords stay
in the MT5 terminal and tokens in environment variables.

## The rules all four profiles share

- Zones on 1D, 4H and 1H; the entry is a balance shift (a close beyond the opposing gap's edge) on one timeframe per
  zone timeframe: 1D zone -> 1H, 4H -> 15m, 1H -> 5m. No BMS/BOS or first-candle entries.
- The entry may lie at most half the zone deep; one trade per zone visit and no second visit to a zone (EURUSD excepted,
  below).
- Stop beyond the sweep extreme since price re-entered the zone (`stop_basis: confirmation`), with a minimum distance
  per market; break-even after 4R (intraday zones; gold 2R since 7 October), no partial exits.
- Entries only 09:00-11:00 and 13:00-17:00 Amsterdam, and not within 30 minutes either side of high-impact news for
  the market's currencies (ForexFactory calendar).
- No entry while the spread exceeds 30 % of the stop distance.
- The Kronos model is off (`kronos.mode: off`): the rules alone decide.

## Where the markets differ

| | EURUSD (`dorus_live.yaml`) | XAUUSD (`dorus_live_gold.yaml`) | NAS100 (`dorus_live_nas100.yaml`) | BTCUSD (`dorus_live_btc.yaml`) |
|---|---|---|---|---|
| Bias gate | 3 of 5 timeframes aligned, the 1H among them; or the 1D and the 1H, then at half the stake (7 October; any trade read as that pair, also a 1D+4H+1H one) | 3 of 5 with the 1H among them (since 7 October; was 2) | as EURUSD | 3 of 5, no 1H rule; the balance turns on a close beyond the last gap's far edge (`shift_flips_balance`); a broken P reads 50/50 (`balance_violation: neutral`, 7 October) |
| Higher-timeframe veto | weekly | none (since 6 October) | weekly | none |
| Zone age | any | at most 24 candles of its timeframe | any | any |
| Zone first visited (since 7 October) | within 24 hours of forming | the same | the same | the same |
| Smallest gap (of the median candle range) | 0.1 (7 October; was 0.2) | 0.2 | 0.1 (7 October) | 0.2 |
| Minimum R:R | 1.0 | 0.8 (7 October; was 0.5) | 1.0 | 0.5 |
| Break-even | after 4R | after 2R (7 October) | after 4R | after 4R |
| Target | origin of the move that made the zone | as EURUSD; a fixed 2R where none reaches the minimum R:R (`tp_fallback`) | as EURUSD | the previous extreme, capped at 3R (nearest liquidity; 2R before 7 October) |
| Minimum stop | 8 pips | 8 pips ($0.80) | 12 points | $60 |
| Time limit | none | none | 48 hours | none |
| Re-entry | after a stop in the same visit, and a second visit | no | no | no |
| Entry order | limit 25 % of the way back toward the stop, valid 4 hours | market | limit, as EURUSD | market (paper on the demo) |
| Stake (setup B) | a 4H zone twice | a 4H zone twice | a 4H zone twice | half |

The EURUSD and NAS100 limit is sized on its smaller stop and cancelled at its expiry or when the target trades first; while it
rests it holds the market's slot and its risk in the guard. Where the symbol takes an expiry time, the server also
lets it expire 10 minutes after the window's own cancel, so a window that is down leaves no order resting for days.
The window keeps its resting limits in `limits_<symbol>.json` next to the journal (a restart goes on watching them)
and cancels, at its first scan, a resting limit of its market it has no record of.

## Risk and the account guard

- Stake 1.5 % of the initial balance a trade on the demo, lowered to 1.0 % from -3 % and 0.5 % from -6 % below the
  start. FTMO, setup B on the 2-Step: `RISK=1.5` (Max, 7 October, evening; 1.25 since 6 October) and
  `PRODUCT=ftmo_2step` in `scripts/ftmo_local.bat`; a 4H zone on EURUSD, gold or NAS100 risks twice that, a BTC trade
  half, and from -3 % below the start the base is 1.0 %, from -6 % 0.5 %. The challenge replay of tonight's set at
  1.5 % against 1.25 %: the 2026 starts funded within 6 weeks 64 % (37 %), within 2 months 97 % (93 %); the 2024-25
  starts within 3 months 52 % (50 %), failed 4 % (1 %); the average month +8.6 % (+7.2 %), the worst -6.0 % (-5.0 %);
  at 1.75 % 7 % failed, at 2 % 17 %. (On the 1-Step:
  `RISK=1.0`, `PRODUCT=ftmo_1step`.) `TARGET` and `PROTECT` (e.g. 10 and 4; 5 in the verification) halve the stake
  within `PROTECT` % of the phase's target (`risk.target_protect_pct`, off unless set).
- The guard refuses a trade when the worst case (every open trade, every resting limit and the new one stopped out)
  would reach the day's or the total limit: with `--product ftmo_2step` -4 % a day and -9.5 % from the initial
  balance (FTMO 2-Step: 5 % and 10 %), with `ftmo_1step` -2.9 % a day and -9 % from the highest day-start balance
  (FTMO 1-Step: 3 % and 10 % trailing), without a product (the demo) the profiles' -4 % and -8 %. At most 2 open
  trades, 1 per market, resting limits included; a position may tie up at most 45 % of the equity in margin. The
  highest day-start balance survives a restart (`guard_day_high.json` next to the journal).
- The open-slot and worst-case checks and the order run under one lock shared by the account's windows. A window that
  cannot get the lock defers the entry and tries again every scan until it expires; it never trades without it.
- Every start writes a `start` row to the journal and `starts/<symbol>_<time>.json` next to it: code revision, source
  hash, package versions, resolved settings (secrets as variable names only) and their hash. Each forward trade traces to the program
  and the profile that took it; `python -m kronos_trader journal` summarises the forward record.
- `scripts\ftmo_report.bat` (`python -m kronos_trader forward-report`, reads only) puts every position of the MT5
  account beside the journal's plan: fill against the planned entry, exit against the stop or target (after a
  break-even move against the moved stop), commission, swap and fee, R before and after costs, the code each trade
  ran on, journal fills the history lacks, and positions that are not the bot's. It also reads the account against
  the product's limits (`--product ftmo_2step` or `ftmo_1step`): what is left of the day and of the total, the open
  risk to every stop and the worst case. Output: `journal_ftmo/report/forward_report.html` and `forward_trades.csv`.
- Every window writes `heartbeat_<symbol>.json` next to its journal after each scan; a watchdog window (started
  by both scripts) says on Telegram when a window has not scanned for 5 minutes, has had no good scan for 15
  (MT5 link down, errors), or its news calendar has nothing ahead on a Monday to Thursday, and again when it is
  over. It runs on the same computer, so for a computer that is off, asleep or offline it calls a healthchecks.io
  check every 5 minutes (`WATCHDOG_PING_URL`, `docs/LIVE_SETUP.md` "When the whole computer stops"): when the calls
  stop, that service sends the alert.
- The FTMO watchdog sends the account's day at 22:05 Amsterdam (`--report-at`, read from the terminal like
  `ftmo_report.bat`): balance and equity against the start, the day's trades with R after costs and their entry
  slippage, what is open and its risk to the stops, the room under FTMO's floors, the distance to the target and the
  trading days. Once a day, also after a restart (`journal_ftmo/day_report.json`); a computer that was off at 22:05
  sends it when it is back that evening. `ftmo_report.bat` with `--telegram` sends the same message by hand.
  The scripts pass it their markets (`--expect`): a market whose window never started is named 5 minutes after the
  watchdog's start (6 October, evening: start_ftmo.bat opened every window but NAS100's and nothing said so); the
  last session's heartbeats wait those 5 minutes too, so a restart no longer sends "no scan since" for every market.
- A zone touch ("👀 ... waiting for a confirmation") is said only inside the entry windows; a zone price is still in
  when a window opens is said then (7 October: six BTC touches at night read as trades about to happen).
- A window says on Telegram that MT5 lost its trade server once the link has been down 5 minutes, and again when it
  is back; a shorter outage stays on the console (FTMO's server restarts every night at 23:00 Amsterdam: on 6
  October each market sent a down message at 23:01 and a back message at 23:02).
- One window per market and journal: `window_<symbol>.lock` next to the journal, held by the operating system while
  the window runs and let go however it ends. A second window for the market (the script run again, a market started
  by hand beside it) says which process runs it and stops before it touches the terminal; the scripts close that
  window after 5 seconds, so running a script again starts exactly the missing windows. A window on code from before
  the lock is recognised by its heartbeat (written in the last 10 minutes by a process that still runs).

## In the code, measured, not used

`bias.reclaim_candles` (failed on 2017-2023), `structure.poi_gap_zones` (more R, more failed challenges), `confirmation.poi_in_poi`, `risk.tp_fixed_rr`,
`prop_firm.weekend_close` (for a funded Standard account). Each is off by default; `docs/backtests/winrate/README.md`
has the measurements.

## What the evidence says

Backtests on 1-minute data with the corrected clock, one trade at a time, guard off, 1 % units; trades, win rate, R,
largest drawdown (`docs/backtests/winrate/README.md`; each run writes a `.provenance.json` with the code, settings,
data hashes and cost assumptions):

| Market | 2024 - Sep 2026 | June 2017 - 2023 (BTC June 2020 - 2023) |
|---|---|---|
| EURUSD (re-entries, limit; the 1D+1H pair at half) | 54, 39 %, +30.0R, -5.5R | 136, 21 %, -0.6R, -22.4R |
| XAUUSD (three of five, 2R fallback target) | 132, 51 %, +88.3R, -4.2R | 309, 28 %, -30.9R, -54.8R |
| NAS100 (limit entry) | 38, 47 %, +37.3R, -4.0R | 82, 26 %, +30.3R, -9.0R |
| BTCUSD (balance shift, target capped at 3R) | 89, 61 %, +82.9R, -3.5R (+48.0R of it in 2026) | 134, 33 %, -28.3R, -38.9R |

Both columns are the profiles of the 7 October restart: the zone visited within 24 hours of forming, the smaller gaps
on EURUSD and NAS100, gold's three of five, BTC's neutral broken P and 3R cap, EURUSD's daily-plus-hourly pair at half
(its R counted at that stake). With FTMO's measured costs (spread and commission) the four together, two open,
1.25 %, 4H zones x2, BTC half: 9.8 trades a month, 51 % won, +0.63R a trade, an average month +7.2 %, 7 of 32 months
losing, the worst -5.0 %; the 2-Step from the 2026 starts within 6 weeks 37 %, 2 months 93 %, 3 months 100 %; from the
2024-25 starts within 2 months 25 %, 3 months 50 %, 1 % failed (README "Into the profiles (7 October)"). The set that
ran until then: 10.6 trades a month, +0.34R a trade, an average month +5.0 %, 12 losing months, the worst -9.1 %,
15 % of the 2024-25 starts failed.

Since 6 October (evening) the profiles are chosen on 2024-2026 only (Max): the older column is kept for the record.
The edge is the recent market's: NAS100 is the only market positive in both periods by a margin, and the FTMO 2-step
replay at 2 % passes from about half of the 2024-2026 starts but from 4-13 % of the 2018-2023 starts. Setup B (4H
zones x2, BTC half, the changes above), starts February 2024 - September 2025: on the 2-Step at 1.25 % funded within
3 months from 25 %, within 6 from 43 %, within a year from 64 %, median 129 days; on the 1-Step at 1 % 26 %, 52 %,
59 %, median 97 days; neither failed (README "1-Step or 2-Step"). In 14 days (the free trial) it takes a median of
4 trades. The forward
record of the demo and the FTMO account is what will tell; the profiles stay frozen during a challenge unless a
change has passed both periods and the challenge replay.
