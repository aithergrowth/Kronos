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

- Zones on 4H and 1H (daily zones off since 8 October: under the 24 h touch rule none ever traded, see the profiles); the entry is a balance shift (a close beyond the opposing gap's edge) on one timeframe per
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
| Higher-timeframe veto | weekly and 4H (8 October; weekly since 5 October), and the 1H balance view turns on a balance shift (`shift_flips_balance`) | none (since 6 October) | weekly | none |
| Zone age | any | at most 24 candles of its timeframe | any | any |
| Zone first visited (since 7 October) | within 24 hours of forming | the same | the same | the same |
| Signal after the visit's first touch (since 9 October) | within 24 hours on a 1H zone, any on a 4H zone | the same | the same | the same |
| Smallest gap (of the median candle range) | 0.1 (7 October; was 0.2) | 0.2 | 0.1 (7 October) | 0.2 |
| The zone's gap when an impulse left several | the first (the deepest P) | the one nearest the break (`poi_gap_choice: last`, 8 October) | the first | the first |
| Minimum R:R | 1.0 | 0.8 (7 October; was 0.5) | 0.8 (13 October; was 1.0) | 0.5 |
| Open in the market | 2 (13 October): a second trade while the first runs, never while a limit rests | 1 | 1 | 1 |
| Break-even | after 4R | after 2R (7 October) | after 4R | after 4R |
| Target | origin of the move that made the zone | as EURUSD; a fixed 2R where none reaches the minimum R:R (`tp_fallback`) | as EURUSD | the previous extreme, capped at 3R (nearest liquidity; 2R before 7 October) |
| Minimum stop | 8 pips | 8 pips ($0.80) | 12 points | $60 |
| Time limit | none | none | 48 hours | none |
| Re-entry | after a stop in the same visit, and a second visit | a second visit (8 October), not after a stop in the same visit | no | no |
| Entry order | limit 25 % of the way back toward the stop, valid 4 hours | market | limit, as EURUSD | market (paper on the demo) |
| Stake (setup B) | a 4H zone twice | a 4H zone twice | a 4H zone twice | half |

The EURUSD and NAS100 limit is sized on its smaller stop and cancelled at its expiry or when the target trades first; while it
rests it holds the market's slot and its risk in the guard. Where the symbol takes an expiry time, the server also
lets it expire 10 minutes after the window's own cancel, so a window that is down leaves no order resting for days.
The window keeps its resting limits in `limits_<symbol>.json` next to the journal (a restart goes on watching them)
and cancels, at its first scan, a resting limit of its market it has no record of.

## Risk and the account guard

- Stake 1.5 % of the current equity a trade on the demo, lowered to 1.0 % from -3 % and 0.5 % from -6 % below the
  start (the steps read the closed balance against the initial balance; the stake itself is on equity, stack review
  of 15 October, A23). FTMO, setup B on the 2-Step: `RISK=1.5` (Max, 7 October, evening; 1.25 since 6 October) and
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
  trades, 1 per market (EURUSD 2 since 13 October), resting limits included, and no new setup in a market while its limit rests; a position may tie up at most 45 % of the equity in margin. The
  highest day-start balance survives a restart (`guard_day_high.json` next to the journal), and so does the day's start
  balance (`guard_day_start.json`, 14 October): a window that starts mid-day while the terminal's trade history does not
  list the morning's stop yet keeps the highest baseline the account's windows saw that day, so the morning's loss still
  counts against the day.
- A window remembers the setups it handled for a week (`seen_<symbol>.json`, 14 October): a restart inside a setup's
  confirmation candle does not take the same setup again (with two places in EURUSD it could have).
- The zones' visit memory survives a restart too (`visits_<symbol>.json`, 14 October, the engine review): a fresh
  window used to date a visit's first touch to the first candle it had, which moved the 24 h touch-age and visit-age
  gates away from the backtest's. The touch notice and the chart age a zone from its candle's close, as the engine does.
- The setup chart goes to Telegram after an executed entry (with the resting limit's price on it), not only in the
  dry run or with the approval step (14 October).
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
- `scripts\parity_week.bat` (`python -m kronos_trader parity`, reads only, 12 October): the week's journal against a
  backtest of the same week on the FTMO terminal's candles, each market with the settings its window ran (rebuilt from
  its start record, the fingerprint compared). Every setup carries the same id in the journal and in the backtest's
  signal log (`journal.setup_id`: zone and confirmation candle), so each signal is a match, an outcome that differs, a
  backtest-only or a live-only signal, with what the files say about why (the window down, a restart, a live-only
  rule). Output: `journal_ftmo/parity/parity_<Monday>.md` and `.csv`, the candles it used, a Telegram summary;
  `parity_week_auto.bat` runs it without the pause (Task Scheduler every Friday at 22:30, `docs/LIVE_SETUP.md`).
- Every window writes `heartbeat_<symbol>.json` next to its journal after each scan; a watchdog window (started
  by both scripts) says on Telegram when a window has not scanned for 5 minutes, has had no good scan for 15
  (MT5 link down, errors), or its news calendar has nothing ahead on a Monday to Thursday, and again when it is
  over. It runs on the same computer, so for a computer that is off, asleep or offline it calls a healthchecks.io
  check every 5 minutes (`WATCHDOG_PING_URL`, `docs/LIVE_SETUP.md` "When the whole computer stops"): when the calls
  stop, that service sends the alert.
- The FTMO watchdog sends the account's day at 22:05 Amsterdam (`--report-at`, read from the terminal like
  `ftmo_report.bat`): balance and equity against the start, the day's trades with R after costs and their entry
  slippage, what is open and its risk to the stops, the room under FTMO's floors, the distance to the target and the
  trading days, and (9 October) the edge meter: the R after costs of the last 20 and the last 30 closed bot trades,
  a warning when the last 20 are under 0R or the last 30 under -5R (a losing month is noise, a lost edge is not). Once a day, also after a restart (`journal_ftmo/day_report.json`); a computer that was off at 22:05
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
`prop_firm.weekend_close` (for a funded Standard account), `exits.day_close` (every position closed at a clock before the
daily break: on NAS100 -1.6R over 2024-2026 and no overnight gap through a stop; gold -11R in 2026, so not there),
`risk.limit_entry_at: break_level` (the limit on the balance level the shift closed through: worse on gold, EURUSD and
NAS100). Each is off by default; `docs/backtests/winrate/README.md` has the measurements.

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

## 14 October, evening: what changed on the first day of the challenge

Nothing in the live profiles (frozen on 13 October). On the branch, for the next restart outside the sessions:

- Telegram: near-miss messages (a zone in play, a shift seen, the trade refused and why), approach notices within half
  a 1H ATR of a zone, the morning check with the regime, today's news and its blackouts, the stake after the ladder,
  the room to the limits and what a trade needs, a midday check at 12:55, charts with the previous day's high and low
  and the entry windows shaded (`live.notify_near_miss`, `notify_approach`, `approach_atr`, `midday_time`). Every
  notice runs on its own in the step: one that fails can never skip the setup.
- Research knobs, all off by default (the behaviour is unchanged, proven trade for trade): the conditional time stop,
  the daily trend filter, the ATR stop floor, the climax-candle gate, the aligned-count stake, the target a fraction
  short of the pool, the minimum visit age, the New York day-open gate, and the morning's four review variants.
- The news calendar: two ISM rows of November moved to 15:00 UTC (the US clock change), the 15 October retail-sales
  row to 12:30 UTC, the releases of 6-13 November added.
- The backtester ends a limit order at its expiry before a candle after a closure can fill it; the weekly parity check
  calls a profile with only new settings at their defaults "identical but for N new settings".
- Known since today: the BTC research candles cut the day at UTC midnight while the window's MT5 candles cut it at
  17:00 New York; on the window's candles the BTC profile makes +22.8R in sample (not +61.7R) and -3.8R out of sample
  (not -41.6R). BTC stays at half stake; the decision whether it stays at all comes after the laptop's spread
  measurement. The research of the day: `docs/backtests/winrate/README.md` (the 14 October evening section) and
  `docs/research/2026-10-14/`.
- 15 October: the stop at the phase's target (`prop_firm.stop_at_target`, off; `STOP_AT_TARGET=1` with `TARGET=10` in
  `scripts/ftmo_local.bat`): at the target no new trade once four trading days are logged (FTMO's days, Prague
  calendar, from the terminal's deal history), 0.1 % a trade until they are; the open positions run; a 🏁 message once
  a day and a line in the morning check.
- 15 October: `risk.far_target_rr` (off; with `far_target_multiplier` 2.0 and `far_target_max_multiple` 2.0): a setup whose
  planned R:R is at least that risks double, never above twice the laddered stake; the engine, the backtester and the
  live window size on it alike. Meant for the funded account (the challenge replay: faster when it goes well, more stalls
  when not); the profiles do not set it.

## 15 October: the stack review and its fixes (the restart of 15 October, evening)

Every component of the live system was reviewed and each finding attacked by an independent check (three stack
reviews, two fix checks). Nothing in the profiles changed. What the windows do differently after the restart:

- **Orders.** A limit order whose reply is lost is looked up on the server for 2 s (an instant fill included) and never
  sent a second time; its zone visit counts as used. A resting limit of the window's market that it has no record of
  is cancelled at every scan; a position on the server it has no record of, opened since the window started, is said
  once on Telegram (its journal row carries the risk, so the forward record counts its R). A limit whose history says
  filled before its position is listed is asked again next scan, not reported "closed again". After a start, when the
  link comes back, or when the window attached a restarted terminal again (also inside one check that never showed the
  link down), an entry waits until the positions have been listed twice: a terminal that has just started can list
  none yet, and read so a second trade went through the per-market cap. While it waits, the window's own resting limit
  is never read as gone and no unrecorded limit is cancelled (an unsynced listing cancelled the window's own limit).
- **The guard.** The worst case counts the swap the open positions have accrued (FTMO's equity does). A position or
  limit whose loss at the stop the terminal cannot price refuses new entries until it can. The morning check adds the
  room after every open stop ("Na alle open stops"), the number the guard decides on.
- **Sizing.** When price ran so far toward the stop before the order went out that the stop lies under half the
  profile's minimum, the lots are held to those of the minimum stop (the fraction's share of it for a limit); the stop
  stays and the trade is taken. Above half the minimum the sizing is the running code's (frozen); holding every order
  to the minimum's lots (about 1 in 5 EURUSD trades, a median 10 % smaller) is Max's decision.
- **Exits.** Break-even reads only fresh bars from the terminal (never the TradingView cache, never a candle before the
  fill, a market fill's own candle included). A refused time exit is retried every scan while the market trades and
  every 15 minutes while it is shut. The exits run even in a scan where the account read fails.
- **The terminal.** A window never logs a terminal in to another account, and never sends credentials to a terminal
  whose account it cannot read (still starting after a minute, or at "authorization failed": log it in by hand);
  credentials only log a terminal in again to the login it shows when it lost its server. A terminal on another login
  is refused, in one line on the heartbeat and Telegram. A window that connected before the terminal had an account
  adopts the first one it shows and says which on Telegram.
- **Messages and records.** Guard refusals are journaled; a close without a price books the closing deal's; the 22:05
  report reads a flat account, and fails loudly only when money moved and the deal history lists nothing at all (an
  unloaded history; a balance correction or trades before the range are read). `ftmo_report.bat` opens the page only
  when that run wrote it. The heartbeat names the current reason of an outage.
- **The morning check's "Trade als" line:** what the next hour's close would have to be for a trade (with the 4H and
  the day when they close with it), as a band where a close beyond it reads 50/50 again; nothing about a later close,
  which depends on the hours in between.
- **The news calendar** reaches 31 December (rows checked against the publishers); a failed ForexFactory read falls
  back on the saved week.
- **Open, for Max to decide:** counting the coming night's swap (a NAS100 4H long into the Friday rollover), the
  finish stake of 0.1 % against the 0.01-lot minimum, an equity protector, a remote pause and automatic window
  restarts. The tests that pin each fix are in `tests/trader/test_review_fixes_15oct.py`,
  `tests/trader/test_fixcheck3_15oct.py`, `tests/trader/test_fixcheck4_15oct.py` and `tests/trader/test_whatif_15oct.py`.
