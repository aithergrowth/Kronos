# Data and pipeline integrity: research candles against FTMO's MT5, the backtest clock, breaks and spreads

Angle: does the research pipeline (HistData 5m bid candles, Bitstamp for BTC, `scripts/build_mt5_like.py`, the 5m
backtest walk, the paper broker) measure what the four FTMO windows will experience? Read-only review of
`kronos_trader/data/*.py`, `backtest/*.py`, `execution/paper.py`, `execution/mt5.py`, `parity.py`, `live.py`,
`scripts/build_mt5_like.py`, `scripts/parity_week.bat`, plus measurements on the scratchpad data (`fixed/`, `btc_data/`,
the `aca/` ledgers). Scripts and outputs: `scratchpad/research/pipeline/` (`week_bounds.py`, `nfp_check.py`,
`fomc_check.py`, `day_bounds.py`, `sparse.py`, `ledger_checks.py`, `gold_spread.py`, `target_margin.py`, `oos_news.py`,
`btc_anchor.py`, the BTC reruns `btc_utc_*`, `btc_ny_*`, `btc_no1m_*`).

Short version: the backtester's clock is clean (no look-ahead found, the intra-candle rules are conservative); the data
is not clean in three places (BTC's candles are anchored at UTC midnight while FTMO's are at the New York close: the
same profile and code on New York-anchored candles gives +33.3R, 51 % won, drawdown -6.0R for 2024-2026 instead of the
ledger's +70.6R, 58 %, -3.5R; the HistData 5m files miss 20-24 % of their slots from February to July 2023 on all three
markets; the 2017-2018 HistData clock is an hour off in the six weeks where US and EU daylight saving disagree); and
the cost side has one material unknown (BTC's and NAS100's FTMO spreads were never measured, and at the $45 the README
once assumed, BTC's live spread cap would refuse the five trades that earned +25R of the ledger's +70.6R). Gold's
2-vs-3.7-pip gap is not material (-3.5R over 143 trades). The news calendar before 2021 holds a third of the
high-impact events the 2024-2026 one does, so the out-of-sample ledgers ran under a lighter blackout.

## 1. Are the research candles comparable to FTMO's MT5 candles?

**What MT5 on FTMO gives the windows.** Bid bars, stamped in server time; `MT5Broker.server_offset` reads the offset from
the last M30 bar before the weekend gap and, when that offset equals New York + 7 h, converts every stamp with the
daylight saving of its own moment (`stamps_to_utc`, the `_ny7` flag). 4H, daily, weekly and monthly bars start at server
midnight = 17:00 New York. `get_candles(...).closed_as_of(now)` drops the forming bar. That part is right.

**HistData (EURUSD, gold, NAS100).** `histdata.to_utc` treats the stamps as London time minus 5 h (the 5 October
finding). Checked independently on the 5m files with the 08:30/14:00 New York release minutes (the 5m range at the slot
against the week's median range, `fomc_check.py`, `nfp_check.py`):

| Day | Release | Expected UTC slot | Range at the expected slot | One hour later |
|---|---|---|---|---|
| 2017-03-15 | CPI 08:30 + FOMC 14:00 (US on DST, EU not) | 12:30 / 18:00 | 0.5x / 1.1x | **2.5x / 22.0x** |
| 2017-11-03 | NFP (mismatch week) | 12:30 | 1.7x | **12.2x** |
| 2018-03-13 | CPI (mismatch week) | 12:30 | 1.6x | **10.5x** |
| 2018-03-21 | FOMC (mismatch week) | 18:00 | 1.2x | **17.5x** |
| 2018-11-02 | NFP (mismatch week) | 12:30 | 0.7x | **4.8x** |
| 2017-07-07 / 2018-07-06 | NFP (both on DST) | 12:30 | **17.8x / 8.4x** | 1.7x / 1.8x |
| 2017-06-14 / 2017-12-13 | FOMC (summer / winter) | 18:00 / 19:00 | **12.0x / 9.6x** | 3.4x / 1.4x |
| 2019-03-20 | FOMC (mismatch week, 2019) | 18:00 | **20.5x** | 2.6x |
| 2024-11-01 | NFP (mismatch week, 2024) | 12:30 | **16.9x** | 2.5x |

Gold shows the same pattern (2017-03-15 FOMC 23.1x at 19:00 UTC, 2018-03-13 CPI 17.9x at 13:30). So: from 2019 on
HistData's clock is indeed "London minus 5 h"; in 2017 and 2018 it followed the **US** clock. The London rule is right
in both years except in the weeks where the US is on summer time and Europe is not (two to three weeks in March, one in
late October/November): six weeks in all, where every candle is stamped an hour late, the Sunday open shows at 18:00
New York (12 candles lost to the weekend cut, `week_bounds.py`: those six weeks hold 1428 candles, a normal week 1440),
and the sessions, the news blackouts and the 17:00 anchors sit an hour off. Seven out-of-sample trades fall in those
weeks (EURUSD 1, -1.0R; gold 5, +4.2R; NAS100 1, -1.0R). Small, but it is the same bug as the 5 October one on a
smaller scale, and the test that found it belongs in the test suite (candidate 3).

**The weekend cut and the day.** `build_mt5_like.py` keeps Sunday 17:00 to Friday 17:00 New York: 478 of 508 EURUSD
weeks open Sunday 17:00 and 491 close Friday 16:55, matching a New York + 7 server's Monday 00:00 to Saturday 00:00.
Per trading day (2023-2026, `day_bounds.py`): EURUSD 17:00-16:55 New York; gold 18:00-16:55 (the one-hour break at the
rollover); **NAS100 18:00-16:10** (the last candle opens 16:10, so the data's break runs 16:15-18:00 New York, 1 h 45,
= 22:15-00:00 Amsterdam in summer, as the README says). What FTMO's US100.cash does between 16:15 and 17:00 New York
is not recorded anywhere in the repository (the README's day-close note says the clock "must sit before FTMO's US100
daily close" and leaves it open). If FTMO quotes those 45 minutes, the research 4H/1D highs and lows and the stop/target
checks miss them every day (candidate 6 measures it from the parity export).

**Holidays.** The HistData NAS100 and gold feeds trade on US holidays with early closes (NAS100 18:00-12:55 New York
on MLK, Presidents, Memorial, Juneteenth, Independence, Labor Day and Thanksgiving: the CME schedule; gold 18:00-14:25),
and have no candles on Good Friday, Christmas and New Year; EURUSD trades Good Friday and most of Christmas Eve. The
in-sample ledgers hold 13 entries on such days: gold 6 (-1.0R), NAS100 2 (-2.0R: Thanksgiving 2025 and 31 December
2025), BTC 4 (+0.5R), EURUSD 1 (+2.0R). Whether FTMO's US100.cash and XAUUSD are open those mornings decides whether
those trades exist live; immaterial in R either way.

**The 2023 hole.** `sparse.py` counts the 5m slots missing inside the trading day (gaps of 10-120 minutes):

| Market | Normal share missing (the daily break) | Feb 2023 | Mar | Apr | May | Jun | Jul | Aug 2023 on |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 0.0-0.1 % | 9.7 % | 22.9 % | 20.7 % | 23.5 % | 24.2 % | 22.1 % | 0.1 % |
| XAUUSD | 3.3 % (17:00-18:00 NY) | 9.8 % | 18.6 % | 20.7 % | 22.0 % | 23.0 % | 21.3 % | 3.3 % |
| NAS100 | 5.8 % (16:15-18:00 NY) | 9.6 % | 20.4 % | 21.5 % | 20.2 % | 22.4 % | 21.5 % | 6.0 % |

One in five 5m candles is missing for six months on all three feeds at once: a provider outage pattern, not a market
one. A missing 5m candle is a missed 5m shift, a missed sweep extreme, a wrong 15m/1H/4H high or low. The out-of-sample
ledgers take 25 trades in those months: NAS100 3 (+12.6R, all won, of its 2023 +17.3R and its 2017-2023 +38.8R), gold
15 (+7.0R of 2023's +19.1R), EURUSD 7 (+5.3R of +1.1R). The 2024-2026 ledgers are not affected (0.1 % missing).
Candidate 2 fills the hole from Dukascopy (the loader exists) and reruns 2023.

**BTC.** The research candles are Bitstamp bars anchored at UTC midnight: 4H at 00/04/08/... UTC, days at 00:00 UTC,
weeks from Monday 00:00 UTC (`btc_data/`, the Bitstamp feed's own convention and the demo's). The FTMO window trades
BTCUSD on the MT5 terminal, whose 4H/1D/1MO start at 17:00 New York and whose weekly bar (a 24/7 symbol) opens Sunday
00:00 server = Saturday 17:00 New York. Rebuilding the higher timeframes from the 5m file the MT5 way (`btc_anchor.py`):
21 % of the daily candles differ in high or low by more than 0.25 % from the UTC-day candle of the same date, 16 % have
the other colour; of the 4H swing highs of 2024-2026, 13 % exist in one set and not the other. The zones (4H) and the
bias (1D/1W/1M) the live window reads are therefore not the ones the BTC ledger was measured on. The rerun with the
same code and settings on both candle sets is in section 5 below.

Also in the BTC research directory and nowhere live: `BTCUSD_1min.csv`. `MultiTimeframeData.from_directory` loads every
file present, so the BTC backtest's lowest timeframe is 1m (the visit tracker, `price`, the touch time), the FTMO
window's is 5m. Section 5 measures that too.

## 2. The backtester's clock: look-ahead or late decisions?

Reviewed `Backtester.run` + `MultiTimeframeData.as_of` + `Timeframe.close_times` + `CandleSeries.closed_as_of`:

- Each step is one closed 5m candle; `now` = its close; `as_of(now)` returns, per timeframe, the candles whose
  `open + length <= now` (monthly: the session-calendar close, `_monthly_close_times`). The broker processes the candle
  before the engine sees it. No forming candle reaches the engine. The 15m confirmation candles close on 5m boundaries,
  so a 4H-zone entry is seen at the same step live and in the backtest.
- The 4H/1D/1W candles of `fixed/` are anchored at 17:00 New York by `anchored_resample`; the US clock change happens
  Sunday 02:00 New York while the market is shut, so no 4H or daily candle straddles a switch (the 4H test in
  `test_histdata.py` checks the hours). The only wrinkle: in the spring switch week the previous weekly candle (opened
  Sunday 22:00 UTC) counts as closed at Sunday 22:00 UTC while the new week already trades from 21:00 UTC: the weekly
  view lags one candle for that Sunday hour, outside the entry windows. Immaterial. Monthly stamps mix 00:00 (the old
  TradingView bars before 2016) and 21:00/22:00 (rebuilt); `close_times` reads each by its own offset.
- The entry fills at the close of the confirmation candle at the configured spread (bid candles: ask = bid + spread);
  live, the window polls every 60 s and sends at the then-current ask, so live is 0-60 s later at a price the backtest
  cannot know. The forward report (`forward.py`) measures exactly this slippage per trade; the 0.10R haircut stands for
  it. The limit entries (EURUSD, NAS100: all 47 and 43 in-sample trades are limit fills, median 10 minutes after the
  confirmation) fill on a 5m touch of the limit, a same-candle stop counted as hit, a same-candle target not counted:
  conservative.
- Inside a candle the paper broker takes the stop before the target and a break-even stop before a later target
  (`PaperBroker.on_candle`); in the 322 in-sample trades no 5m candle spans both the stop and the target
  (`target_margin.py`), so the ordering never decided a trade.
- The target is a touch fill at the level. How thin the hits are: EURUSD 7 of 22 winners reached the target by under
  1 pip, gold 7 of 70 by under 1 pip (18 of 70 by under 5 % of the stop), NAS100 1 of 19, BTC 1 of 52 by under $1
  (9 of 52 by under $30). Those are the winners a slower fill or a wider spread turns into open trades; the haircut is
  sized for about that.
- Live and backtest agree on the gates' clocks: `in_session` and the news blackout evaluate `now` (the 5m close in the
  backtest, the poll time live) in Amsterdam time; every in-sample confirmation closes inside 09-11/13-17 Amsterdam,
  none on a weekend (`ledger_checks.py`). The 24 h touch and visit ages count wall-clock hours on both sides; the zone
  age counts candles of the zone's timeframe on both sides.

Verdict: no look-ahead, no systematic late decision beyond the 0-60 s poll, which the forward report measures. An
optional guard for the future: an assertion in `MultiTimeframeData.as_of` (debug mode) that every returned candle's
close time is at or before `now`, and a unit test over a DST switch week; cheap, not a candidate on its own.

## 3. Weekend, holiday, the 23:00 Amsterdam restart, the NAS100 break

- **Weekend:** the research data has no Friday 17:00 - Sunday 17:00 New York candles; FTMO's forex/gold/index week is
  Monday 00:00 - Saturday 00:00 server, the same instant. The session gate (`weekdays` 0-4) refuses weekend entries on
  both sides. BTC: Bitstamp trades through the weekend and FTMO's crypto does too; the gate still refuses Saturday and
  Sunday entries. A 1H zone formed Friday afternoon is "24 hours old" Sunday evening on both sides (hours, not
  candles).
- **The 23:00 Amsterdam restart** is the server's midnight (17:00 New York) rollover: the link drops for about a minute,
  the window skips a scan, stops and targets are server-side, the break-even move waits a minute, the paper BTC account
  catches up (`advance_paper` feeds the missed closed candles once). Outside every entry window. Nothing to model. What
  the backtest does not model at that minute is the **spread widening at the rollover**: gold's and EURUSD's ask jumps
  for minutes around 17:00-18:00 New York, and a short's stop triggers on the ask. Exposure measured on the gold ledger
  (`gold_spread.py`): 36 of 143 trades were open through an 18:00 New York open; in those first 15 minutes the nearest
  approach to the stop was under 10 pips once (P125, a short, 8.2 pips, stopped anyway), under 20 pips once, under 40
  pips twice. Negligible at today's stops (median 85 pips).
- **NAS100's daily break:** the data's 16:15-18:00 New York. Positions held through it: the README measured the night
  gaps (one night in five gaps more than a median 4H-zone stop; no gap through a stop in the 38 trades) and built
  `exits.day_close` (off). The open point is whether FTMO's break starts at 16:15 or 17:00 New York (candidate 6).
- **Holidays:** see section 1; 13 in-sample entries on US holiday mornings, net -0.5R. FTMO publishes holiday hours
  per occasion in its Trading Updates (an early close of the US100 symbols on Good Friday 2026 was listed at 16:14
  platform time, for instance), says the standard hours are the ones in the terminal's symbol Specification window,
  that the day for the daily-loss rule resets at midnight Prague time (what `prop_firm.day_timezone` does), and that
  weekend hours on cryptocurrencies vary per platform with the weekly maintenance window (sources: FTMO's FAQ pages
  "what are the trading hours and where can I check them", "do I have to close my positions overnight or before
  weekend", the simulated-assets page and the January 2026 trading update). None of that is in the repository: the
  parity export is the place to read the actual hours from (candidate 6).

## 4. Spreads: gold's 2 vs 3.7 pips, and BTC/NAS100

What the ledgers assume (`.provenance.json`): EURUSD 1.0 pip, gold 2.0 pips, NAS100 1.5 points, BTC $15, no
commission, no slippage, no swap; the account replays then add FTMO's commission and a 0.10R haircut. What is measured
at FTMO: EURUSD 0.1 pip raw plus $3 a lot round turn (0.3 pip), gold 3.4-3.7 pips. **NAS100 and BTC were never measured**
(`docs/LAPTOP_TASKS.md`, "the two never measured"); the README's "$45 FTMO spread" line for BTC was a what-if.

Replayed trade by trade on the 5m candles (`ledger_checks.py`, `gold_spread.py`, `target_margin.py`):

| Market (ledger) | Spread assumed -> measured | R change on the ledger | Trades the live 30 % cap would refuse at the measured spread | Other effects |
|---|---|---|---|---|
| EURUSD (`eutwo`, 47 trades, +44.2R) | 1.0 -> 0.4 all-in | **+3.1R** (+0.07R a trade: the research is 0.6 pip too dear) | 0 | - |
| XAUUSD (`base`, 143, +86.1R) | 2.0 -> 3.7 | **-3.5R** (-0.025R a trade) | 0 (smallest stop 17 pips, the cap bites under 12.3) | 0 shorts newly stopped; 1 short target no longer reached; 8 of 70 winners reached the target by less than the 1.7-pip gap; 4 trades fall under R:R 0.8 at fill (+3.3R booked) |
| NAS100 (`rr08`, 43, +37.2R) | 1.5 -> 2.0 (guess) | -0.8R | 0 | - |
| BTCUSD (`base`, 89, +70.6R) | $15 -> $45 + 0.065 % commission (what-if) | **-20.2R** (-0.23R a trade) | **5 trades, +25.0R booked, 60 % won** (stops under $150) | 9 of 52 winners reached the target by less than $30; 3 short targets lost; 6 trades under R:R 0.5 |
| XAUUSD out of sample (371, -25.1R) | 2.0 -> 3.7 | -23.5R | 31 trades (-12.0R: refusing them helps) | 2017-2023 stops were tighter (median 32 pips) |
| BTCUSD out of sample (130, -28.6R) | $15 -> $45 | -38.5R | 50 trades (38 %; but the spread scales with the price, so this overstates) | - |

So gold's assumption is not material: 3.5R over 2.7 years, inside the haircut, no refusals. What is material is BTC,
and it hinges on a number nobody has: the FTMO BTCUSD spread in the 09-11/13-17 Amsterdam windows. At $45 the cap
refuses the five small-stop trades that carry a third of the ledger and the costs take 29 % of the rest; at $25 the cap
refuses nothing and the costs take about 0.15R a trade. The 14 October note (live refused a gold stop under 12 pips
while the research took it) shows the mechanism; in these ledgers it cannot happen on gold (no stop under 17 pips), it
can on BTC.

How to measure and feed back (existing tools): `python -m kronos_trader --config config/dorus_live.yaml mt5-spreads
--symbols NAS100=US100.cash,BTCUSD,XAUUSD,EURUSD --day <date>` reads the terminal's tick history over the two windows
and prints the median, 90th percentile and maximum against `typical_spread_pips` and the stop the cap refuses at the
median. The forward report (`ftmo_report.bat`) already gives the realised entry slippage per trade. What is missing is
the spread at the moment of every live entry (the journal only carries it on a refusal) and a weekly line that sets
the measured medians against the assumptions (candidates 4 and 7).

## 5. BTC on the candles FTMO stamps: the rerun

Same code (source `6812136f998f`), same settings (`aca/base_BTCUSD.yaml`, the calendar by absolute path), same window
(2024-01-01 to 2026-09-24, 5m step, bid quotes, 1 % units, guard off), three data directories:

| Data | Trades | Won | R | Drawdown / longest losing run | R per year 2024 / 2025 / 2026 | Note |
|---|---|---|---|---|---|---|
| `btc_data/` as the ledgers used (UTC-anchored, with the 1m file) | 89 | 58 % | **+70.6R** | -3.5R / 3 | +15.2 / +14.0 / +41.4 | reproduces `aca/base_BTCUSD.csv` trade for trade |
| the same without `BTCUSD_1min.csv` (live's lowest timeframe is 5m) | 91 | 57 % | +68.6R | -3.5R / 3 | +14.2 / +13.0 / +41.4 | all 89 setups shared, 2 added |
| NY-anchored 4H/1D/1MO, weekly from Saturday 17:00 NY (MT5's Sunday 00:00 server), with the 1m file | 94 | 51 % | **+33.3R** | -6.0R / 5 | +10.2 / +6.2 / +16.9 | the candles the FTMO window sees |

Both candle sets give 116 signals; 54 of the 89 ledger setups (zone timeframe, side, confirmation candle) recur on the
New York candles. The 4H-zone trades go from 22, +7.5R to 19, -2.0R; the 1H-zone trades from 67, +63.1R to 75,
+35.3R. June 2026, the month that carries the ledger (8 trades, +41.1R), has 4 trades, +16.1R on the New York
candles: the +11.8R short of 2 June is in both, the +23.9R short of 25 June (the ledger's largest trade) has no
counterpart. Shorts +40.4R -> +18.0R, longs +30.2R -> +15.4R; 2024Q4 +11.8R -> +0.7R, 2026Q2 +40.1R -> +14.7R.
Profit factor 3.1 -> 1.7. With FTMO's crypto costs (0.18R a trade at a $15 spread, 0.24R at $45, section 4) the
New York ledger nets roughly +11 to +16R over 2.7 years before the 0.10R haircut (-9R), so about flat.

Two cautions. The 1D and 4H anchoring of an MT5 server on New York + 7 is certain; the weekly's Sunday-00:00-server
start is MT5's convention and should be read off the terminal's W1 stamps (the parity export under `journal_ftmo/
parity/` has them). And it is one rerun on one alternative anchoring: the honest reading is not "BTC makes +33R" but
"BTC's +70.6R is not robust to how the day is cut, and the cut the live window trades on is the unfavourable one".
The README already noted that BTC's R rests on three June 2026 shorts; this is the same fragility seen from the data
side. The 1m file changes nothing worth keeping (2 trades, -2.0R).

## Candidates

1. **Rebuild BTC's research candles the way FTMO's server stamps them and re-measure the BTC profile.** Rule: 4H, 1D
   and 1MO anchored at 17:00 New York (`anchored_resample(..., session_tz="America/New_York")`, no weekend cut), the
   weekly from Sunday 00:00 server = Saturday 17:00 New York (`resample("W-SUN", closed="left", label="left")` on the
   series shifted by +7 h from New York local time); 5m/15m/1H unchanged. Set: a `--crypto` mode in
   `scripts/build_mt5_like.py` (skip the weekend mask, weekly rule W-SUN) run as `python scripts/build_mt5_like.py
   btc_data btc_ny BTCUSD:BTCUSD_1min.csv --crypto`, then `backtest --data-dir btc_ny` with `config/dorus_live_btc.yaml`
   for 2024-2026 and 2020-2023; the profile's numbers in `docs/CURRENT_STATE.md` and the README move to that ledger,
   and BTC's place in the live set (half stake, the 3R cap) is re-decided on it. Before the rebuild, read the W1 and D1
   stamps off the terminal's exported candles (`journal_ftmo/parity/`) to confirm the weekly convention. Evidence:
   our data (21 % of daily candles differ materially, 13 % of 4H swings; the rerun in section 5: 94 trades, 51 %,
   +33.3R, drawdown -6.0R against 89, 58 %, +70.6R, -3.5R; after FTMO's crypto costs about flat). Needs code.
2. **Fill February-July 2023 from Dukascopy and rerun 2023.** Rule: for each of EURUSD, XAUUSD, NAS100 fetch the
   1-minute bid days 2023-02-01..2023-07-31 (`python -m kronos_trader dukascopy --symbol EURUSD --instrument EURUSD
   --start 2023-02-01 --end 2023-07-31 --raw-dir data/dukascopy/raw --out-dir <tmp>`; gold `XAUUSD`, NAS100 the
   Dukascopy CFD instrument `USATECHIDXUSD`), take Dukascopy's minute where HistData has none (a 15-line merge on the
   timestamp index, HistData first), rebuild with `scripts/build_mt5_like.py`, rerun the three out-of-sample ledgers
   for 2023 (and any 2023-2026 tuning run that is still cited). Evidence: our data (20-24 % of the slots missing in
   those months on all three feeds; 25 out-of-sample trades in them, NAS100's +12.6R of its 2023 +17.3R). Needs code
   (the merge).
3. **Fix `histdata.to_utc` for 2017-2018 and keep a clock test.** Rule: stamps before 2019-01-01 are New York local
   time (`tz_localize("America/New_York")`), stamps from 2019 on are London local minus 5 h (as now); the boundary sits
   in winter where both rules agree. Add `tests/trader/test_histdata.py` cases for 2017-03-15 and 2018-11-02 and a data
   test (the `nfp_check.py` logic: the 12:30/13:30 UTC range peak per week must follow the US clock) that runs over any
   rebuilt `fixed/` file. Rebuild 2017-2018 and rerun the out-of-sample ledgers. Evidence: our data (the release-minute
   table in section 1; 6 weeks, 7 out-of-sample trades). Needs code (3 lines + tests).
4. **Measure NAS100 and BTC spreads in the windows and put the measured spread of every market into the research
   profiles.** Rule: three weekdays of `python -m kronos_trader --config config/dorus_live.yaml mt5-spreads --symbols
   NAS100=US100.cash,BTCUSD,XAUUSD,EURUSD --day <date>` (the `docs/LAPTOP_TASKS.md` command); then in the research
   yamls `symbols: {XAUUSD: {typical_spread_pips: 3.7}, EURUSD: {typical_spread_pips: 0.4}, NAS100: {typical_spread_pips:
   <median>}, BTCUSD: {typical_spread_pips: <median>}}` (the yaml `symbols` block merges into `SymbolSpec`), so the
   ledger R carries the real spread and the backtester's `max_spread_stop_fraction` refuses the same stops live refuses;
   if BTC's window median is $40 or more, `risk.min_stop_pips: 150` in `config/dorus_live_btc.yaml` (the README's
   measured -6.2R) rather than letting the cap refuse at random. Evidence: our data (the table in section 4). No code.
5. **One news calendar for 2017-2026.** Rule: rebuild `data/calendar/high_impact.csv` for 2017-2022 from the same source
   and the same importance filter as 2023-2026 (the TradingView economic calendar month by month through
   `from_tradingview` + `save_events`, or ForexFactory's monthly archive through `from_forexfactory`), so that USD
   high-impact events number about 250 a year throughout and the 10:00 ET releases (ISM, consumer confidence, JOLTs,
   Michigan) and FOMC exist before 2021; rerun the out-of-sample ledgers. Evidence: our data (USD 96/94/105/134/192 events
   a year 2017-2021 against 249-261 from 2023; 2019 has no event outside 12/13/15 UTC; 0 ISM events before 2021; the
   out-of-sample 09:30-10:30 ET entries: gold 51 trades -8.8R, BTC 16 -8.7R, EURUSD 11 -4.3R against +18.2R / +3.6R /
   +12.6R in sample). Needs code (a fetch loop).
6. **A trading-hours and holiday line in the weekly parity report.** Rule: from the candles `export_candles` already
   saves, per market the first and last 5m candle of each day (New York clock) and the days without candles, against
   the research data's (EURUSD 17:00-16:55, gold 18:00-16:55, NAS100 18:00-16:10 plus the holiday early closes), and
   `mt5.symbol_info_session_trade` for the symbol's own schedule; a difference is printed as a notice. Set: about 30
   lines in `parity.markdown` / `run_parity`. Evidence: our data (the day bounds; 13 holiday entries, -0.5R; the
   unknown 16:15-17:00 New York of US100.cash). Needs code.
7. **Journal the spread and the slippage at every live entry and compare weekly.** Rule: `live._open_locked` already
   computes the spread for the cap; write it on every `setup` and `filled` row (`spread=` in `self.note(...)`), and
   `parity.markdown` adds per market "spread at entry: median X pips (assumed Y); entry slippage: median Z R (haircut
   0.10R)" from the journal and `forward_trades.csv`; a market whose median exceeds the assumption by 25 % is flagged.
   Set: ~10 lines in `live.py`, ~20 in `parity.py`. Evidence: reasoning (today the spread is recorded only on a refusal,
   the slippage only in the forward report nobody compares with the research assumptions). Needs code.
8. **Take `BTCUSD_1min.csv` out of the BTC research directory.** Rule: the research directory holds the timeframes the
   live window fetches (5m, 15m, 1H, 4H, 1D, 1W, 1MO) and nothing finer; `MultiTimeframeData.from_directory` loads what
   is there, and the FTMO window's lowest timeframe is 5m. Set: move the file (no code), or `--base-tf 5m` as a loader
   filter if the 1m file is wanted for `scripts/minute_walk.py`. Evidence: our data (section 5: without the file 91
   trades, +68.6R against 89, +70.6R, every ledger setup kept, two added). No R at stake; it is hygiene so that the
   research directory and the window's feed hold the same timeframes and the weekly parity lines up. No code.
