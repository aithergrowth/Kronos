# Metamorphic and property tests of the engine and the backtester (14 October 2026)

Angle: evidence against look-ahead and silent breakage, by testing rather than reading. Four checks, all read-only on the
repository; scripts and outputs under `scratchpad/research/invariants/` (absolute:
`/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/invariants/`). No backtest was
rerun for this; the one background run (the EURUSD live profile to 2026-06-30) was already finished when this started.

| # | Check | Result | Script / output |
|---|---|---|---|
| 1 | Append-only invariance: the run to 2026-06-30 against the run to 2026-09-24 | **PASS**: 44 trades identical in 25 entry columns and 6 exit columns; equity curves identical on all 186,328 bars; on two different code revisions | `append_only.py` -> `append_only.out` |
| 2 | Determinism across the day's batches, from the provenance files | **PASS**: 6 pairs identical in every column (incl. the pure rerun of the BTC base on a later code revision); 4 "no-op" variants of RESULTS_14oct.md are not no-ops at trade level (the knob changed 1-4 trades, R unchanged); one data manifest and one calendar behind every run | `determinism.py` -> `determinism.out`, `determinism_pairs.out`, `inventory.csv` |
| 3 | Ledger invariants on 58 ledgers (the 8 live ones, 33 oct14b, 16 oct14c, the look-ahead run), 5,421 trades, 30 checks a trade, replayed against the 5m candles | **5,420 of 5,421 pass**; the one violation is a limit that filled 4 h 50 after its expiry across the Memorial Day 2020 closure (NAS100 out of sample, -1.0R) | `ledger_invariants.py` -> `ledger_invariants.out`, `ledger_summary.csv`, `ledger_violations.csv`, `ledger_mfe.csv` |
| 4 | Time-shift property of `StrategyEngine.analyze()` with and without future candles in the arrays | **PASS**: 9,492 five-minute steps (17 Mar - 30 Apr 2025), 0 differing analyses among three engines (as_of views / full arrays with the future / physically truncated fresh objects); visit memory identical; the 6 ledger trades of April 2025 reproduced exactly | `time_shift.py` -> `time_shift.out`, `time_shift_signals.csv` |

## 1. Append-only invariance

`aca/eutwo_EURUSD.csv` (2024-01-01 to 2026-09-24, code a607b7b7 of 12 October) against `lookahead/eutwo_EURUSD_to_june.csv`
(the same yaml, data and calendar, to 2026-06-30, code fecf55e8 of 14 October 16:54):

- trades opened before 25 June: 44 in both; opened up to the part's end (30 June 23:55): 44 in both; no trade open at the end;
- every entry column equal (opened_at, direction, entry, stop, take_profit, lots, zone, confirmation candle, touch, planned R:R,
  target source, bias readings, visit number, risk budget: 25 columns, 0 differences, exact float equality);
- every exit column equal for the 44 trades closed before the cut (closed_at, exit, final_stop, pnl, r, reason: 0 differences);
- the equity curves equal bar for bar: 186,328 bars, 0 rows only in one file, 0 bars with a different equity; the part's final
  equity 142,771.14 = the full run's equity at that bar;
- run counters: 56 signals / 44 trades / 5 refusals (part) against 61 / 47 / 5 (full); the two extra "limit expired" refusals
  of the full run fall after June.

Adding three months of candles after a date changes nothing before it. Because the two runs were made by different code
revisions (and the resolved settings in the provenance differ by 10 knobs the newer code added with their defaults), the
same comparison also says that the 14 October commits (6b2d7b7 .. fecf55e: the spread cap in the backtester, the research
knobs, the Telegram work) did not move a single EURUSD trade.

## 2. Determinism from the provenance files

Each pair: the flattened resolved settings of both runs (knobs one code revision does not know are defaults and are listed
separately), the data manifest (sha256 per candle file), the calendar sha, the ledgers column by column (exact equality),
the run counters.

| Variant vs base | Code (base / variant) | Settings diff | Ledger | What differs |
|---|---|---|---|---|
| ms12_XAUUSD vs base_XAUUSD | fc476b22 / 6812136f | min_stop_pips 8 -> 12 | 143 = 143, identical in every column | nothing; the smallest planned gold stop is 15 pips, so the knob cannot bite |
| fv_BTCUSD vs base_BTCUSD | fc476b22 / e708a5e6 | touch_age_from_first_visit true | 89 = 89 identical | only the rejection texts (counts of "touched N h after it formed") |
| fv_NAS100 vs rr08_NAS100 | fc476b22 / 2e6dca1e | touch_age_from_first_visit true | 43 = 43 identical | only the rejection texts |
| nop_BTCUSD vs base_BTCUSD | fc476b22 / e708a5e6 | tp_origin_includes_p false | 89 = 89 identical | nothing (the BTC profile targets previous_extreme; the knob only touches impulse_origin) |
| swp_XAUUSD vs base_XAUUSD | fc476b22 / 2e6dca1e | stop_window_includes_sweep true | 143 = 143 identical | nothing |
| **btc_utc_BTCUSD vs base_BTCUSD** (the pure rerun of `base_BTCUSD.yaml`, research/pipeline) | fc476b22 / 6812136f | none (the calendar named by its absolute path, same file sha) | 89 = 89 identical, counters identical | nothing: the same settings and data reproduce the ledger on a later code revision |
| be3_EURUSD vs eutwo_EURUSD | fc476b22 / 6812136f | breakeven_r_intraday 4 -> 3 | 47 = 47, **4 trades differ in final_stop only** (P19 2025-04-09, P25 2025-06-27, P31 2025-09-03, P43 2026-06-02) | the stop moved to the entry at +3R; all four went on to the target, so exits and R are the same. No stop exit ever reached +3R (max favourable excursion among the 24 stop exits: 1.74R; 9 target exits passed 3R) |
| ms100_BTCUSD vs base_BTCUSD | fc476b22 / 9a7e250f | min_stop_pips 60 -> 100 | 89 = 89, **1 trade differs** (P35 2024-10-24 08:05 LONG: planned stop 92 $ -> 100 $, lots 9.65 -> 8.99, closed one candle later, R -1.0 both) | final equity 193,991.36 -> 193,990.06; the only base trade with a planned stop under 100 $ |
| swp_BTCUSD vs base_BTCUSD | fc476b22 / e708a5e6 | stop_window_includes_sweep true | 89 = 89, **1 trade differs** (P17 2024-05-16 13:55: stop 65,839 -> 65,812, lots 2.13 -> 2.02, R -1.0 both); signals 116 -> 115 | the sweep candle widened one stop |
| swp_NAS100 vs rr08_NAS100 | fc476b22 / 2e6dca1e | stop_window_includes_sweep true | 43 = 43, **1 trade differs** (P17 2025-06-18 13:35: entry 21,736.6 -> 21,736.4, stop 21,631.4 -> 21,630.8, R -1.0 both) | one stop 0.6 points wider |

So: identical settings and data give identical ledgers across three code revisions of the day (the property under test
holds); and four of the variants that `RESULTS_14oct.md` books as "delta +0.0R (+0 tr)" did change one to four trades.
The R-sum at one decimal is too coarse to call a variant a no-op; the trade-level comparison (opened_at, entry, stop,
take_profit, exit) is the right test and is cheap (`determinism.py` does it in seconds).

Inventory (`inventory.csv`, 177 provenance files under aca, oct14b, oct14c, lookahead):

- one distinct data manifest per (symbol, data directory, start): BTCUSD btc_data 38 runs, EURUSD fixed 47 runs, NAS100 fixed
  34 runs, XAUUSD fixed 37 runs, all on identical candle files (sha256 equal);
- one calendar (sha 6576f82a, 2,888 events, 2017-01-06 .. 2026-11-04) in every run except the six deliberate `nonews_*`
  runs (news.enabled false); no run silently lost the calendar;
- the day's ledgers come from six to seven code revisions per market (source hashes fc476b22, 6812136f, 9a7e250f,
  e708a5e6, 2e6dca1e, c3808b28, ...), with the trade sets agreeing wherever the settings agree.

Side note for the weekly parity check: `settings_fingerprint` hashes the fully resolved settings, so it changes whenever a
commit adds a knob with a default (10 to 17 such knobs between the day's revisions). After a `git pull` on the laptop the
parity report will say "NOT identical to the window's" and list only new defaults. Proposal (code, ~5 lines in
`kronos_trader/backtest/provenance.py`): fingerprint only the keys whose value differs from `Settings()` defaults, so the
hash is stable across added knobs; keep the full dict in the record.

## 3. Ledger invariants (58 ledgers, 5,421 trades)

Each ledger is checked with its own resolved settings from the provenance (min_rr, min_stop_pips, the spread, the session
windows, the calendar, the limit fraction, break-even R, the zone and confirmation tables, the veto and required timeframes)
and replayed against the 5m bid candles of its data directory. Per trade (the full list is in the script's docstring):

| Group | Checks | Violations in 5,421 trades |
|---|---|---|
| geometry | stop behind the entry; target beyond the entry | 0 |
| R:R | planned R:R >= min_rr; R:R at the fill >= min_rr; rr_at_fill == abs(tp-entry)/abs(entry-stop) | 0 |
| stop size | abs(entry_planned - stop) >= min_stop_pips (8 pips EURUSD/gold, 12 points NAS100, 60 $ BTC; the variants' own values) | 0 |
| sizing | lots > 0, a multiple of 0.01; (stop + 1-pip buffer) x lots <= risk_budget and one more lot step would not fit; risk_amount == abs(entry-stop) x lots <= budget | 0 |
| r, pnl | r == sign x (exit-entry)/abs(entry-stop); pnl == sign x (exit-entry)/pip x pip value x lots | 0 |
| signal moment | the first 5m close at or after confirmed_close_at (within the confirmation candle's length) that passes the session and news gates; market profiles: opened_at == that moment and entry == that candle's close (+ spread for a long); limit profiles: the limit = round(ask/bid - 0.25 x abs(ask/bid - stop)) from that candle == entry, the fill candle reached it, the fill after the signal | 0 (4,082 market fills, 1,339 limit fills) |
| session, news, weekday | the signal moment inside 09-11 / 13-17 Amsterdam (the ny variants: + 17-21), not inside a 30-min blackout of the symbol's currencies, on a weekday | 0 |
| gates | touch within 24 h of the zone's close (skipped for the first-visit knob); signal within 24 h of a 1H zone's touch; gold's 24-candle zone age; entry at most half the zone deep; zone timeframe in [4H, 1H] (+15m for scalp15); the table's confirmation timeframe (4H -> 15m, 1H -> 5m); the confirmation candle closes after the touch | 0 |
| bias | every timeframe of the matched combination reads the trade's direction; the required 1H among the aligned ones; no veto timeframe against | 0 |
| exits | the exit candle traded through the stop / the target / the break-even stop; exit == stop (or the open when the candle gapped through), == target, == entry at break-even; the target's candle did not also trade through the stop | 0 |
| break-even logic | no stop exit reached the trigger (2R gold, 4R others) before its exit candle; every break-even exit did | 0 |
| overlap | never more than max_open_per_symbol open (2 EURUSD, 1 others) | 0 |
| equity | initial + sum(pnl) == the provenance's final equity | 0 |
| time | opened_at <= closed_at | 0 |
| limit expiry | a limit fills before its 240 minutes are over | **1** |

The one violation: `aca/oos_rr08_NAS100` P40, signal Monday 2020-05-25 13:15 UTC (Memorial Day; the feed's early close at
17:00 UTC), limit valid to 17:15, no candle between 16:55 and the 22:00 reopen; `Backtester._work_limit` tests the fill
before the expiry, so the reopen candle (low 9,509.9 under the 9,512 limit) filled an order that had expired 4 h 50 earlier.
Live, the MT5 order carries an expiry (ORDER_TIME_SPECIFIED, +10 min) or the window cancels it at the first scan past
`expires_at`, so the trade does not exist live. Rule: in `kronos_trader/backtest/runner.py::_work_limit`, check
`now >= pending["expires"]` before testing `filled`. Effect: that one out-of-sample trade (-1.0R) disappears; no in-sample
ledger has such a fill (0 of 1,339 - 100 limit fills in the 2024-2026 ledgers). Code, 2 lines.

Things the suite measured that are not violations but are worth knowing:

- **Stamps.** `PaperBroker.on_candle` stamps a stop / target / break-even exit with the exit candle's *open* time
  (`close_ts = candle.timestamp`), while a fill is stamped with its candle's *close* time (`now`), a limit stopped in its own
  candle with the close time, and `end_of_data` with the close time. A trade stopped in the candle after its fill therefore
  shows `closed_at == opened_at`: 214 of 5,421 rows (4 %). Holding times read from the ledgers are one 5m candle short, and
  the BTC paper window's journal (the same broker live) stamps its closes 5 minutes early. R is untouched. Rule, if wanted:
  `on_candle(symbol, candle, close_ts=None)` with the runner passing `now`; 3 lines, shifts every `closed_at` by +5 min and
  moves the `max_hold_hours` (NAS100, 48 h) and `time_stop` clocks by one candle.
- **Signals delayed by a gate.** 15 trades were taken one or two 5m steps after the confirmation's close because the first
  moment was outside the windows or inside a blackout. The engine's rule is that the confirmation must still be the last
  closed candle of its timeframe, so only a 15m confirmation (4H zones) has a second and third chance, at close + 5 and
  close + 10 minutes; a 5m confirmation refused at its close is gone. The limit prices reproduce from the later candle in
  all 15, which is the backtester's walk working as described.
- **Resting limits fill inside blackouts.** 108 of the 1,339 limit fills (8 %) happened inside a 30-minute news window; the
  entry rule is applied at the signal, not at the fill, in the backtest and live alike (MT5 keeps the order). On the live
  ledgers: EURUSD in sample 4 fills, 2 won, +5.1R; NAS100 in sample 5 fills, 1 won, +0.3R; out of sample 4 fills, 0 won,
  -4.0R. Thirteen trades, 23 % won against 47-50 % for the rest: cancelling the limit when a blackout starts would have
  cost +5.4R in sample and saved 4.0R out of sample, so by the house rule (both periods) it is a negative result; recorded,
  not proposed.
- **Break-even geometry.** 16 break-even exits had trigger and return in the same candle (the broker takes the stop, by
  design); 6 limit entries were stopped in their fill candle. Among the live ledgers' stop exits, the favourable excursion
  before the exit candle reached 1R in 7 of 24 (EURUSD), 14 of 71 (gold), 4 of 23 (NAS100), 10 of 37 (BTC) and 2R in none
  but one NAS100 trade (3.71R, under its 4R trigger): the `be1` / `be2` variants of the batch are where those numbers come
  from, and the suite confirms every be1/be2 ledger moved the stop exactly when the candles say it should.
- **Rounding.** The first version of this suite reported 78 limit fills one price unit off; the cause was the suite rounding
  numpy floats (numpy's `round` is half-to-even on the scaled value) where the engine rounds Python floats, and the limits
  landing on exact 5-decimal ties. The engine, the runner and the live loop all round Python floats (`float(candle.close)`,
  MT5 ticks), so this is a trap for anyone re-deriving prices in pandas, not an engine inconsistency.

## 4. The time-shift property of the engine

`time_shift.py` runs three `StrategyEngine` instances (the EURUSD live research profile, the news calendar attached as the CLI
does, equity 100,000) over every 5m step from 2025-03-17 (two weeks of warm-up for the visit memory) to 2025-04-30:

- A: the backtester's views, `MultiTimeframeData.as_of(now, lookback=400)` (numpy slices of arrays that still hold the future);
- B: the complete series of every timeframe, future candles included, with `now` (the engine's own `closed_as_of` must cut);
- C: fresh `CandleSeries` objects per step built from frames physically truncated to the candles closed at `now` by an
  independent cut (`open + length <= now`; the monthly's session-calendar close taken from `Timeframe.close_times`).

Compared per step as a JSON digest: price, the bias per timeframe (reading, liquidity view, balance view), the combined
decision (tradable, direction, mode, matched combination, aligned timeframes, reason), every zone (timeframe, side, bounds,
formation time, status), every rejection text, and the signal's setup (direction, entry, stop, target, R:R, lots,
confirmation candle and type, touch time, visit number, combination).

Result: 9,492 steps, 0 differing steps; 13,814 rejection texts equal; 11 signal steps in all three engines; the visit
trackers hold 127 zones with identical state at the end. The six EURUSD trades the ledger opened in April 2025 (P17-P22) are
all among the engine's signals with the same confirmation candle, entry_planned, stop and target; the walk found one more
setup (2025-04-18 14:00 LONG 1.13859 / 1.13349 / 1.14736) that is not a ledger trade, which is the backtester's guard or
limit handling (the full run refused 5 signals and let 8 limits expire).

What this does and does not show: the analysis at a moment depends only on the candles closed at that moment, through
three different ways of presenting them, and the engine's state (visit memory, caches) evolves identically; the stop and
target of a trade are fixed at the signal and reproduce from the data at that moment. It does not test the paper broker
(check 3 does, against the candles) or the live feed's candle completeness (the parity check does).

## Verdict

No look-ahead found, by construction and by test: the append-only run, the time-shift walk and the candle-level replay of
5,421 trades agree with the ledgers to the last digit. The one real defect is the limit expiry across a market closure
(one out-of-sample trade). The one process finding is that "no-op" should be decided at trade level, not by the R-sum.
