# Kronos Trader: the current state (6 October 2026)

What runs, with which settings, and what the evidence says. The profile files are the source of truth: every setting
there carries its reason and date. Older pages describe how the rules came about: `docs/STRATEGY.md` starts from
Max's original rules (1:3 R:R, 1 % risk), which the profiles have since replaced with the values below.

## What runs where

| Script | Account | Markets | Orders |
|---|---|---|---|
| `scripts/start_live.bat` | MetaQuotes-Demo (MT5) | EURUSD, XAUUSD; BTCUSD on paper with Bitstamp prices | MT5 market orders with server-side stop and target, no approval |
| `scripts/start_ftmo.bat` | FTMO MT5 terminal, 10,000 (trial, then the 2-step challenge) | EURUSD, XAUUSD, NAS100 (`US100.cash`), BTCUSD | the same, journal in `journal_ftmo/` |

Each market runs in its own window and polls every 60 seconds; signals come from closed candles (5m the smallest).
Both scripts `git pull` before they start, so a change on this branch reaches the windows at their next start and
never a running one. Local values (risk, symbol names) go in `scripts/*_local.bat`, which git ignores; passwords stay
in the MT5 terminal and tokens in environment variables.

## The rules all four profiles share

- Zones on 1D, 4H and 1H; the entry is a balance shift (a close beyond the opposing gap's edge) on one timeframe per
  zone timeframe: 1D zone -> 1H, 4H -> 15m, 1H -> 5m. No BMS/BOS or first-candle entries.
- The entry may lie at most half the zone deep; one trade per zone visit; no second visit to a zone.
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

## Risk and the account guard

- Stake 1.5 % of the initial balance a trade (FTMO: `RISK` in `scripts/ftmo_local.bat`, 2.0 % for the trial and the
  challenge), lowered to 1.0 % from -3 % and 0.5 % from -6 % below the start.
- The guard refuses a trade when the worst case (every open trade and the new one stopped out) would reach a -4 % day
  or -8 % from the initial balance (FTMO's limits are -5 % and -10 %); at most 2 open trades, 1 per market; a position
  may tie up at most 45 % of the equity in margin.
- The open-slot and worst-case checks and the order run under one lock shared by the account's windows. A window that
  cannot get the lock defers the entry and tries again every scan until it expires; it never trades without it.
- Every start writes a `start` row to the journal and `starts/<symbol>_<time>.json` next to it: code revision, source
  hash, resolved settings (secrets as variable names only) and their hash. Each forward trade traces to the program
  and the profile that took it; `python -m kronos_trader journal` summarises the forward record.

## In the code, measured, not used

`risk.tp_fallback` (a target in place of one under the minimum R:R), `bias.reclaim_candles` and
`bias.shift_flips_balance` (the bias switches: failed on 2017-2023), `structure.poi_gap_zones` (more R, more failed
challenges), `confirmation.poi_in_poi`, `confirmation.allow_retest`, `risk.tp_fixed_rr`, `prop_firm.weekend_close`
(for a funded Standard account). Each is off by default; `docs/backtests/winrate/README.md` has the measurements.

## What the evidence says

Backtests on 1-minute data with the corrected clock, one trade at a time, guard off, 1 % units; trades, win rate, R,
largest drawdown (`docs/backtests/winrate/README.md`; each run writes a `.provenance.json` with the code, settings,
data hashes and cost assumptions):

| Market | 2024 - Sep 2026 | 2017 - 2023 (BTC Jun 2020 - Jan 2024) |
|---|---|---|
| EURUSD | 31, 48 %, +11.2R, -4.0R | 74, 30 %, -2.3R, -13.1R |
| XAUUSD | 105, 48 %, +32.3R, -9.2R | 319, 39 %, +8.8R, -22.6R |
| NAS100 | 45, 47 %, +21.5R, -5.0R | 114, 36 %, +23.6R, -9.9R |
| BTCUSD | 142, 49 %, +53.1R, -11.9R (+52.9R of it in 2026) | 152, 41 %, -11.2R, -12.5R |

The edge is the recent market's: NAS100 is the only market positive in both periods by a margin, and the FTMO 2-step
replay at 2 % passes from about half of the 2024-2026 starts but from 4-13 % of the 2018-2023 starts. The forward
record of the demo and the FTMO account is what will tell; the profiles stay frozen during a challenge unless a
change has passed both periods and the challenge replay.
