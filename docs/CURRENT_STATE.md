# Kronos Trader: the current state (6 October 2026)

What runs, with which settings, and what the evidence says. The profile files are the source of truth: every setting
there carries its reason and date. Older pages describe how the rules came about: `docs/STRATEGY.md` starts from
Max's original rules (1:3 R:R, 1 % risk), which the profiles have since replaced with the values below.

## What runs where

| Script | Account | Markets | Orders |
|---|---|---|---|
| `scripts/start_live.bat` | MetaQuotes-Demo (MT5) | EURUSD, XAUUSD; BTCUSD on paper with Bitstamp prices | MT5 market orders with server-side stop and target, no approval |
| `scripts/start_ftmo.bat` | FTMO MT5 terminal, 10,000 (the free trial, then the 1-Step challenge: setup B) | EURUSD, XAUUSD, NAS100 (`US100.cash`), BTCUSD | the same, NAS100 by limit order (below); journal in `journal_ftmo/` |

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
  per market; break-even after 4R (intraday zones), no partial exits.
- Entries only 09:00-11:00 and 13:00-17:00 Amsterdam, and not within 30 minutes either side of high-impact news for
  the market's currencies (ForexFactory calendar).
- No entry while the spread exceeds 30 % of the stop distance.
- The Kronos model is off (`kronos.mode: off`): the rules alone decide.

## Where the markets differ

| | EURUSD (`dorus_live.yaml`) | XAUUSD (`dorus_live_gold.yaml`) | NAS100 (`dorus_live_nas100.yaml`) | BTCUSD (`dorus_live_btc.yaml`) |
|---|---|---|---|---|
| Bias gate | 3 of 5 timeframes aligned, the 1H among them | 2 aligned with the 1H among them (1D+1H, 4H+1H, or the book's combos) | as EURUSD | 3 of 5, no 1H rule |
| Higher-timeframe veto | weekly | none (since 6 October) | weekly | none |
| Zone age | any | at most 24 candles of its timeframe | any | any |
| Minimum R:R | 1.0 | 0.5 | 1.0 | 0.5 |
| Target | origin of the move that made the zone | as EURUSD | as EURUSD | the previous extreme, capped at 2R (nearest liquidity) |
| Minimum stop | 8 pips | 8 pips ($0.80) | 12 points | $60 |
| Time limit | none | none | 48 hours | none |
| Re-entry | after a stop in the same visit, and a second visit | no | no | no |
| Entry order | market | market | limit 25 % of the way back toward the stop, valid 4 hours | market (paper on the demo) |
| Stake (setup B) | a 4H zone twice | a 4H zone twice | a 4H zone twice | half |

The NAS100 limit is sized on its smaller stop and cancelled at its expiry or when the target trades first; while it
rests it holds the market's slot and its risk in the guard. Where the symbol takes an expiry time, the server also
lets it expire 10 minutes after the window's own cancel, so a window that is down leaves no order resting for days.
The window keeps its resting limits in `limits_<symbol>.json` next to the journal (a restart goes on watching them)
and cancels, at its first scan, a resting limit of its market it has no record of.

## Risk and the account guard

- Stake 1.5 % of the initial balance a trade on the demo, lowered to 1.0 % from -3 % and 0.5 % from -6 % below the
  start. FTMO, setup B (Max, 6 October): `RISK=1.0` and `PRODUCT=ftmo_1step` in `scripts/ftmo_local.bat`; a 4H zone on
  EURUSD, gold or NAS100 risks twice that, a BTC trade half.
- The guard refuses a trade when the worst case (every open trade, every resting limit and the new one stopped out)
  would reach the day's or the total limit: with `--product ftmo_1step` -2.9 % a day and -9 % from the highest
  day-start balance (FTMO 1-Step: 3 % and 10 % trailing), with `ftmo_2step` or none -4 % a day and -8 % from the
  initial balance (FTMO 2-Step: 5 % and 10 %). At most 2 open trades, 1 per market, resting limits included; a
  position may tie up at most 45 % of the equity in margin. The highest day-start balance survives a restart
  (`guard_day_high.json` next to the journal).
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
  over. It runs on the same computer: a computer that is off or asleep shows as a missing morning briefing.

## In the code, measured, not used

`risk.tp_fallback` (a target in place of one under the minimum R:R: failed on 2017-2023 for NAS100, gold and
EURUSD), `bias.reclaim_candles` and `bias.shift_flips_balance` (the bias switches: failed on 2017-2023),
`structure.poi_gap_zones` (more R, more failed challenges), `confirmation.poi_in_poi`, `risk.tp_fixed_rr`,
`prop_firm.weekend_close` (for a funded Standard account). Each is off by default; `docs/backtests/winrate/README.md`
has the measurements.

## What the evidence says

Backtests on 1-minute data with the corrected clock, one trade at a time, guard off, 1 % units; trades, win rate, R,
largest drawdown (`docs/backtests/winrate/README.md`; each run writes a `.provenance.json` with the code, settings,
data hashes and cost assumptions):

| Market | 2024 - Sep 2026 | 2017 - 2023 (BTC Jun 2020 - Jan 2024) |
|---|---|---|
| EURUSD (with re-entries) | 38, 50 %, +15.8R, -5.0R | 90, 34 %, +5.3R, -15.7R |
| XAUUSD | 105, 48 %, +32.3R, -9.2R | 319, 39 %, +8.8R, -22.6R |
| NAS100 (limit entry) | 36, 42 %, +27.9R, -5.0R | 96, 28 %, +33.6R, -10.6R |
| BTCUSD | 142, 49 %, +53.1R, -11.9R (+52.9R of it in 2026) | 152, 41 %, -11.2R, -12.5R |

The edge is the recent market's: NAS100 is the only market positive in both periods by a margin, and the FTMO 2-step
replay at 2 % passes from about half of the 2024-2026 starts but from 4-13 % of the 2018-2023 starts. Setup B (the
1-Step at 1 %, 4H zones x2, BTC half, the changes above) was funded from 59 % of the starts February 2024 - September
2025 within a year, 25 % within 3 months, 52 % within 6, and failed from none (README "Setup B"). The forward
record of the demo and the FTMO account is what will tell; the profiles stay frozen during a challenge unless a
change has passed both periods and the challenge replay.
