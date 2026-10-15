# Pre-mortem: the FTMO 2-Step 10k challenge, 14 October - 30 November 2026

Angle: imagine the challenge has gone wrong by 30 November and work back to how. Read-only: the code as it is on
`feature/kronos-trader` (fecf55e, 14 October), the four live profiles, the start script, the docs, the research ledgers
(2024-02..2026-09 in sample, 2017..2023 out of sample) and FTMO's published rules. Every failure mode below carries the
mechanism (file:line), a likelihood over the six weeks, the impact in R or % of the account, how it shows (which
Telegram message, heartbeat field or journal row) and the mitigation, marked as a **read-only check**, a **manual rule**
for Max, or the **smallest code change**. Nothing in the repository was changed; the scripts are in
`research/premortem/` (`analyses.py`, `extra.py`).

Reference: 1R = 1.5 % of the initial balance ($150) on a 1H zone, 3 % ($300) on a 4H zone of EURUSD, gold or NAS100,
0.75 % on BTC; the guard refuses a trade when the worst case (every open stop and the new one) would pass -4 % of the
initial balance on the day or -9.5 % in total (`cli.py:367-372`); FTMO fails the account at -5 % of the initial
balance below the midnight-Prague balance (equity-based) or -10 % static.

## 0. The calendar of the window (Amsterdam clock)

| When | What | What it means for the bot |
|---|---|---|
| Thu 15 Oct | PPI 14:30, retail sales 15:30 | USD blackout 14:00-16:00 (the two windows join) |
| Sun 25 Oct | Europe leaves daylight saving: Amsterdam and Prague UTC+1 | sessions and the FTMO day stay on their clocks |
| Mon 26 Oct - Sun 1 Nov | **the mismatch week**: New York UTC-4, FTMO's server (New York + 7) stays UTC+3 | server midnight (daily candle open, the nightly restart) at **22:00 Amsterdam**; 4H candles open 22, 02, 06, 10, 14, 18 Amsterdam; US 08:30 releases at **13:30** Amsterdam; the New York open at 14:30 |
| Tue 27 Oct | durable goods 13:30 | USD blackout 13:00-14:00: the afternoon window's first hour |
| Wed 28 Oct | FOMC decision 19:00, press conference 19:30 (Fed calendar: two-day meeting 27-28 October) | outside the windows; open positions run through it as in the backtest |
| Thu 29 Oct | GDP advance and core PCE 13:30; ECB decision 14:15, press conference 14:45 | USD blackout 13:00-14:00; EURUSD also 13:45-15:15 |
| Fri 30 Oct | euro-area flash GDP and CPI 11:00 | EURUSD blackout 10:30-11:30 |
| Sun 1 Nov | the US leaves daylight saving; the server goes to UTC+2 | the forex week opens 23:00 Amsterdam; the bot re-reads the offset from the Friday bar |
| Mon 2 Nov, Wed 4 Nov | ISM 16:00 | the seeded calendar has these at 15:00 (section 12) |
| Tue 3 Nov | US midterm elections (results overnight into 4 Nov) | no rule in the bot; a gap risk for a position held that night |
| Fri 6 Nov | **NFP 14:30** (BLS: 6 November, 08:30 ET) | blackout 14:00-15:00; the seeded calendar ends 4 Nov, so this event comes from ForexFactory alone |
| Tue 10 Nov | **CPI 14:30** (BLS: 10 November, 08:30 ET); Windows Patch Tuesday | blackout 14:00-15:00; an update restart that night |
| Wed 18 Nov | FOMC minutes 20:00 | outside the windows |
| Thu 26 Nov | Thanksgiving: US day session closed (CME reopens 00:00 Amsterdam) | US100.cash and gold close early afternoon New York; the windows end before that |
| Fri 27 Nov | early close around 12:00 CT = 19:00 Amsterdam | a NAS100 position open at 19:00 holds into the weekend from then |

The news dates: FOMC from the Federal Reserve's October 2026 page; NFP and CPI from the BLS release schedules
(Employment Situation for October 2026 on 6 November, CPI for October 2026 on 10 November, both 08:30 ET); the
Thanksgiving pattern from CME's holiday schedule as summarised by a third party (the product-specific times are
published about two weeks before; FTMO's US100.cash hours are in the terminal's symbol specification).

## 1. Ranking

| # | Failure mode | Likelihood (six weeks) | Impact | Detected by | Mitigation class |
|---|---|---|---|---|---|
| 1 | The target comes early and the windows trade on at full stake (section 2) | high: +10 % within 47 days from 100 % of the 2026 starts (47 % of 2024-25), 31 % of the 2026 starts before the 4th trading day | weeks of delay: 10-33 % of early hits fall back under +10 %; after day 4, 7-12 % within 3 days; a fail from it under 1 % | the 22:05 report line `target +10 %: reached; N trading day(s)` | manual rule now, code later |
| 2 | A weekend or overnight gap through a double-stake 4H position (section 3) | 1-2 % chance of an instant fail: 0.29 weekend-held double-stake positions expected in 6.5 weeks, each with a 4-15 % chance of a 1.67-stop gap | -5 % to -16 % in one print: the challenge | `🛑 ... closed (stop) ... (-x.xxR)` with R under -1 at the Monday open, the 22:05 report, FTMO's dashboard | manual Friday rule, or config (NAS100 single stake) |
| 3 | A pulled commit changes a window's behaviour; a notification bug stops entries (section 4) | every restart; a regression reaches the windows in 10-20 % of restarts (41 commits since 7 October, no tests on the laptop) | mostly fail-closed (no trades for days), sometimes a wrong trade | `⚠️ ... live loop error`, the watchdog's `no good scan since`, the Friday parity report | code (try/except around the notices, a pinned commit) |
| 4 | The daily-loss model against FTMO's equity rule (section 5) | low: the worst case caps the open risk under 4 %, the buffer to FTMO's 5 % is 1 % of the account | a fail only with a gap or slippage of a third of a double stake's stop; manual positions are invisible to the guard | `⛔ ... daily loss would reach ...` (the guard working), the 22:05 `left today` line | manual rule (no manual positions beside the windows) |
| 5 | The DST-mismatch week (section 6) | low for the clock paths (verified against FTMO's own notices and tested); the behavioural side is in the backtest | a wrong offset would stale the 5m feed (no trades, said within 20 minutes) or age the zones by an hour | `⏸ setup ignored, the data is stale`, `⚠️ geen nieuwe 5m-candles`, `stale` journal rows | read-only checks on Monday 26 October |
| 6 | Telegram or the watchdog goes silent (section 7) | medium: an outage, a token or environment problem after a restart | nothing for the account; Max does not know what is open | the absence of the 08:45, 12:55, 22:00 and 22:05 messages; `[telegram] message not sent` on the console | config (healthchecks.io e-mail), a read-only daily check |
| 7 | The laptop sleeps, Windows updates, MT5 reconnects (section 8) | medium: Patch Tuesday 10 November inside the window; nothing restarts the windows after a reboot | missed entries (about +0.6R each) and missed break-even moves; positions keep their server-side stop and target | healthchecks.io after 15 minutes (if configured); the heartbeats' `time`; `start` rows | laptop settings, a logon task (Max's choice) |
| 8 | The spread cap refuses or passes NAS100 and BTC trades (section 9) | the NAS100 spread is unmeasured; the morning window trades on the thin Globex book | 0.05-0.18R a NAS100 trade; a fifth of NAS100 trades refused at a 5-point spread; BTC fine to $45 | `⛔ ... spread ... is NN % of the stop distance`, `not_executed` rows with `spread` | laptop measurement, then profile spreads |
| 9 | The margin cap on 10k (section 10) | certain for BTC (74 % of trades cut), NAS100 4H zones 40 % at 1:50 | smaller positions, never larger; a `No money` refusal only when the server does not answer | `💸 ... (margin: lots cut from ...)`, `⛔ not enough margin` | read-only check at the restart |
| 10 | The 22:00/23:00 break, NAS100's daily break, Thanksgiving (section 11) | nightly, known | a minute without a scan; a close past the break; thin Friday liquidity | `⚠️ ... MT5 ... al 5 min`, `closing ... failed ... trying every scan` | nothing; a manual note for 26-27 November |
| 11 | The parity check's assumptions (section 13) | weekly | it validates the plumbing, not the edge; it cannot see what both sides share | the report's verdicts | read with its explanations |
| 12 | The news calendar after 4 November (section 12) | 5 % per NFP/CPI day that ForexFactory is unreachable | an entry inside the 30-minute window: a -1R to -2R print, twice that on a 4H zone | `📰 ... the news calendar ended` (Monday-Thursday only), the 08:45 `📰 Nieuws vandaag` line | data (extend the seeded CSV) |
| 13 | Phase 2 on a new login (section 14) | once, if phase 1 passes | a window trading nothing (`logged in to account X, this window trades Y`), a wrong `TARGET`, a day count that includes phase 1 | the link-down message, the 22:05 line | manual checklist |

## 2. The target with fewer than four trading days, and trading on after it

**Mechanism.** Nothing in the live path reads the target: `risk.target_pct` only halves the stake within
`target_protect_pct` of it (`strategy/risk.py:318-334`), and `TARGET`/`PROTECT` are unset in `ftmo_local.bat` (Max,
7 October; the replay says the protect step is slower with no fewer failures). The watchdog alone knows the target:
`start_ftmo.bat` gives it `--target-pct 10` when `TARGET` and `FUNDED` are unset, and the 22:05 message ends with
`target +10 %: <left> to go` or `reached; N trading day(s)` (`forward.py:306-311`, the days counted as distinct Prague
dates with a fill in the account's history, manual trades included). The windows keep taking every setup at the full
stake, before and after the target. FTMO counts a trading day when a position is opened (00:00-23:59 CE(S)T) and needs
four of them; the target is evaluated on the closed balance.

**Numbers** (replay of the ledgers with the live stakes, the guard and 0.10R costs, `research/premortem/analyses.py`,
`extra.py`): phase 1 passed within 47 days from 100 % of the 2026 starts (220 starts; 93 % at 0.25R costs; 98 % without
BTC) and 47 % of the 2024-25 starts (700; 38 % at 0.25R; 45 % without BTC), 9 % of 2017-23. The +10 % was first touched
before the fourth trading day in 31 % of the 2026 starts and 7 % of 2024-25 (4 % of 2017-23). Trading on at full stake
until day 4 took the balance back under +10 % in 10 % (2026) / 33 % (2024-25) / 17 % (2017-23) of those cases, the
worst dip 1.4 / 3.0 / 4.5 % under the target; after a qualifying pass, trading on undoes it within 3 days in 7-12 % of
cases (prop_firm.md 3.3). Trading days in 47 days: median 6 (2026, p10 4), 9 (2024-25); no start had fewer than four.
The median time to +10 % in 2026 is about three weeks, so there is room inside the window to give it back.

**Likelihood / impact.** The most likely way this challenge disappoints: the target is reached, then lost again, and
the clock runs. Not a fail by itself (the guard still holds the day at 4 %), but a delay of weeks and a loss of the
2026-sized head start.

**Detection.** The 22:05 line (balance-based, open positions excluded). The dashboard shows the week's closes.

**Mitigation (manual rule, exact).** When the 22:05 report says `target +10 %: reached` (closed balance at or above
11,000):

- with 4 or more trading days: after 17:00 Amsterdam close the five windows (the open positions keep their server-side
  stop and target; let them finish, or close them by hand if the balance stays at or above 11,000 after the close), and
  request the Verification in the FTMO dashboard once nothing is open (FTMO requires it);
- with fewer than 4 days: close the windows the same way; on each missing day open one EURUSD position of 0.01 lot by
  hand with a 10-pip stop and close it (about $1 at risk; FTMO's day counts an opened position of any size), until the
  count reads 4 in the 22:05 report; then request the Verification. This is the replay's "finish at 0.10 %" rule, which
  raised the 2026 six-week passes from 56 to 59 % and was never worse (prop_firm.md 3.3).

Do not keep the windows running while hand trades are open: the guard does not see them (section 5). **Smallest code
change** (after the challenge, or now with Max's OK): `prop_firm.stop_at_target: true` and `prop_firm.finish_risk_pct:
0.10` in `live.py` next to `planned_risk` (`live.py:1485-1500`), with the trading days counted as the day report counts
them (`forward.py:306`); on `--target-pct` only, off by default.

## 3. A weekend or overnight gap through a double-stake position

**Mechanism.** A 4H zone risks 3 % (`risk.zone_risk_multiplier {4H: 2.0}` in the EURUSD, gold and NAS100 profiles;
`strategy/risk.py:284-285`). The stop lives on the server (`mt5.py:637-649`), and a gap fills it at the open, not at the
stop. There is no weekend close in the challenge (`WEEKEND_CLOSE` unset; `prop_firm.weekend_close ""`,
`config.py:440`) and no day close (`exits.day_close ""`, `config.py:397`). A gap of 1.67 stops against a 3 % position is
a -5 % day: FTMO closes every position and fails the account (the guard can refuse new trades, never undo a fill).

**Numbers** (the ledgers, `analyses.py` (b), (f)). Double-stake trades (4H zones, EURUSD/gold/NAS100): 28 in 32 months
in sample (0.88 a month, 1.37 expected in 6.5 weeks), 65 in 83 months out of sample. Held over a weekend: 6 of 28 in
sample (gold 4 of 13, EURUSD 1 of 10, NAS100 1 of 5; median hold of gold's 4H trades 22 hours), 10 of 65 out of sample:
0.29 (0.19) weekend-held double-stake positions expected in the window. With the account combined (two open), 89 % of
the 139 weekends had nothing open, 5 % had 3 % or more at risk, none 4.5 %. The six weekend-held double-stake trades
in sample all won (+3.85, +4.06, +4.68, +1.99 x3); out of sample gold's nine were 6 losers, one at -1.37R (a gap filled
beyond the stop: -4.1 % at the double stake, under the 5 % by 0.9 %). NAS100 crossed its daily break in 6 of 43 trades
(two of the five 4H trades). Gap sizes since 2024 in units of the median 4H stop (prop_firm.md 3.5): a weekend gap over
1.67 stops follows 30 % of NAS100 weekends, 12.5 % of EURUSD's, 7.5 % of gold's; a NAS100 night 8.8 %. Half of those
are on the wrong side: per weekend-held double-stake position about 15 % (NAS100), 6 % (EURUSD), 4 % (gold); per
NAS100 night 4 %.

**Likelihood / impact.** About 0.29 x 5 % = 1.5 % chance over the window of losing the challenge in one print (most
weekend holds are gold's), plus roughly 0.16 x 0.4 x 4 % = 0.3 % from NAS100 nights; the single 1.5 % positions can
gap too (-2.5 % at 1.67 stops: survivable). Impact when it happens: -5 % to -16 % (the README's 5.5-stop NAS100 night).

**Detection.** The window's `🛑 {symbol} closed (stop) @ ... P&L ... (-x.xxR)` at the Monday open (Sunday 23:00
Amsterdam, `live.py:1999-2003`) with R under -1; the 22:05 report; FTMO's breach e-mail. Too late by then.

**Mitigation.** Manual rule for the challenge: on Friday after 21:30 Amsterdam (the windows open nothing after 17:00),
read the dashboard's open positions; a position whose risk to the stop is 2 % of the account or more (a 4H zone at
x2) and whose stop is not yet at break-even is closed by hand if it is NAS100; for gold and EURUSD Max chooses (the
ledger says a wash: the three in-sample cases were winners, -6.7R if closed on Friday, against a 4-6 % chance each of
an instant fail). The window records the close as `closed (closed)` and does not re-enter (the zone's visit is spent).
Config alternative, at the next restart: `risk.zone_risk_multiplier: {}` in `config/dorus_live_nas100.yaml` (NAS100's
4H zones at the single stake; the replay is neutral: 2026 passes within 47 days 100 % either way, 5 trades +6.2R at
stake), which removes the one market whose night gap exceeds the median 4H stop one night in six. Smallest code change:
`prop_firm.weekend_close_min_risk_pct: 2.0` as a filter on the existing weekend close (`live.py:1897-1913`,
`exits.py:38-45`): at Friday 15:45 New York only positions with 2 % or more at risk are closed.

## 4. A restart pulls the branch; a notification bug stops the entries

**Mechanism.** `scripts/start_ftmo.bat` runs `git pull --ff-only` and starts the windows on whatever
`origin/feature/kronos-trader` holds: 41 commits since 7 October, no test run and no `pip install` on the laptop, and
the profiles can change in the same pull (1d87337 did, with Max's OK). A failed pull (a local change, a diverged branch)
prints `UPDATE FAILED` and **pauses before any window starts**: nothing runs until a key is pressed. "Inert" research
knobs are inert through their defaults in `config.py`; a behavioural change in `live.py` (124 KB, changed today) is not
inert. The order inside one scan matters: `step()` runs the morning check, the evening summary, the touch notice, the
midday check, the near-miss and approach notices **before** `handle_signal` (`live.py:446-453`), and the first three
of those notices are only partly guarded (`announce_near_misses` wraps the Telegram send, not
`classify_near_miss`/`self.note`, `live.py:655-666`; `announce_poi_touch` calls `spent_zone` -> `touch_age_hours`
outside any try, `live.py:1084, 1101-1122`). An exception there ends the scan in `run_forever`'s handler
(`live.py:1134-1136`): the loop survives, but no setup is handled while the error repeats, i.e. the bot stops trading
without stopping. The same holds for a crash at import (a new package in `requirements-trader.txt`; unchanged since
early October).

**Likelihood / impact.** A restart is certain (profile changes keep arriving). A regression that reaches the windows:
10-20 % per restart given the volume and the absence of laptop tests; the 14 October review found and fixed several
such paths. Impact: fail-closed most of the time (days without entries, about +0.6R expected per missed trade), a wrong
trade occasionally; a pause-blocked start leaves no windows at all until noticed.

**Detection.** `⚠️ {symbol}: live loop error: ...` once and then at most every 30 minutes (`live.py:1176-1188`); the
heartbeat's `state: error` and the watchdog's `⚠️ {symbol}: no good scan since ... (error: ...)` after 15 minutes
(`watchdog.py:64-68`); the journal's `start` row and `starts/<symbol>_<time>.json` with the commit; the dashboard's
commit per window with a warning when they differ; the Friday parity report (`backtest only` with "the window was down"
is the benign case, `live only` the one to read).

**Mitigation.** Smallest code change (two parts): (1) a `try/except` around each of the five notice calls in `step()`
(`live.py:446-451`), as the notices themselves promise "never fatal"; (2) a `PIN=<commit>` line in `ftmo_local.bat`
that makes `start_ftmo.bat` check out that commit instead of pulling the branch head, so a restart runs the code Max
chose (one `git checkout` line guarded by `if defined PIN`). Manual rule until then: before a restart, the cloud session
names the commit to run and lists what changed in `live.py`, `mt5.py`, `risk_guard.py` and the profiles since the
commit the windows run (`git log --oneline <old>..<new> -- kronos_trader/live.py ...`); the restart check in
`docs/LAPTOP_TASKS.md` then compares the four start records.

## 5. The daily-loss guard's worst-case model against FTMO's equity rule

**Mechanism.** FTMO: equity (floating P/L, swaps and commissions included) may not fall below the balance at 00:00
Prague minus 5 % of the initial balance, nor below 90 % of the initial balance, at any instant. The guard
(`execution/risk_guard.py:162-206`): the day starts at Prague midnight (`:50-56`), its baseline is the closed balance
then, rebuilt after a restart from the terminal's deal history (`:65-77`, `mt5.py:563-579`) and kept at the highest
value any window saw that day (`live.py:904-937`); before every order the worst case `balance - open_risk - new_risk`
is checked against -4 % of the initial balance on the day and -9.5 % in total (`:186-194`), where `open_risk` is each
position's loss from its entry to its stop by the server's own profit calculation plus every resting limit's risk
(`:139-160`); an unknown day start refuses (`:172-173`), a stopless position refuses (`live.py:1511-1515`), a limit
resting in the market refuses (`:1518-1525`). Equity at the stop equals balance minus the loss from entry, so the
worst case is FTMO's number up to three omissions: (a) commissions and swaps ($3 a lot round turn on EURUSD, 0.0325 %
a side on BTC, gold's swap a few dollars a night: under 0.1 % of the account; not so NAS100: a 4H long pays 0.34-0.41 %
a night and 1.0-1.24 % on the triple night, which the guard counts as accrued since 15 October, stack review A2);
(b) slippage and gaps beyond the stop;
(c) **positions not opened by the windows**: `open_positions` keeps only this program's magic number
(`mt5.py:597`), so a manual position carries no risk and takes no slot in the guard (the day report does count it,
`forward.py:248-251`). The buffer between the guard's 4 % and FTMO's 5 % is 1 % of the account, $100; between 9.5 %
and 10 % only $50, and between -5.5 % and -6 % the ladder still has the base at 1.0 % (`strategy/risk.py:329-331`): two
4H trades at 2 % each are admitted from -5.5 %, and a gap of a quarter stop past both stops breaks the 10 % (stack
review of 15 October, A20).

**Numbers** (prop_firm.md 3.1, 3.2). At the live stakes 239 FTMO days with a closed trade: 7 days at -3.3 % (a single
4H loss), one at -6.6 % (two EURUSD 4H longs, the second refused by the worst-case check: 6 %); after a 4H loss the
guard lets nothing but a 0.75 % BTC trade in for the rest of the day; the guard turns the 7 % of starts that break
FTMO's limits with the guard off into 0 %; a 3 % position needs a gap or slippage of a third of its stop to eat the
$100 buffer (NAS100 nights: 16 % exceed one stop, section 3). Positions held over a Prague midnight: 61 of 315
combined trades (19 %), 12 of them double stake, +94.7R together: the overnight carry is where the edge sits, not a
thing to cut.

**Likelihood / impact.** A breach without a gap needs the day already at -3.x % and a second loss with slippage: under
0.5 % over the window. The manual-position hole is only a risk if Max trades by hand beside the windows (section 2's
day-count trades: with the windows closed).

**Detection.** The guard working: `⛔ {symbol}: setup NOT executable - daily loss would reach x.xx % if the open
trades and this one were stopped out` (`live.py:1348`, `risk_guard.py:189-190`), the `not_executed` journal row with the
reason; the 22:05 `left today` and `worst case` lines (`forward.py:299-305`); `🚨 ... has NO STOP on the server`
(`live.py:1947`).

**Mitigation.** Manual rule: no hand-opened position while a window runs; if one is needed (section 2), close the
windows first. Read-only check once: the day-report line `if every stop is hit the equity ... is under a floor` must
never appear with the windows' positions alone. No code change: the 4.0 % and 9.5 % stay (4.5 % changes nothing, 4.9 %
fails 9-14 % of starts at 0.25R costs; prop_firm.md 3.1).

## 6. The DST-mismatch week (26 October - 1 November)

**Mechanism.** FTMO's platform clock follows the US switch: its trading updates give the platform time as "GMT+3 until
3 November 2025, GMT+2 thereafter" and "from Sunday 8 March 2026 ... GMT+3" (the US switch dates), and FTMO warned in
October 2025 that for one week the offset between Prague midnight and platform midnight is two hours instead of one,
the daily reset staying at midnight CE(S)T with a countdown in the Account MetriX tooltip. So from 26 October to
1 November the server is UTC+3 while Amsterdam and Prague are UTC+1. The code reads the server offset from the last
M30 bar before the weekend gap (`mt5.py:355-389`): the Friday 23 October bar sits 30 minutes before the New York
close plus 7 hours, so `_ny7` is set (`:386-387`) and the offset is `New York's offset now + 7 h` = +3 h all week
(`:388`), +2 h from the Friday 30 October bar read on 1-2 November; the fresh tick is checked against it every hour
and wins when the two agree within 1.5 h (`:309-334`). Every candle stamp is converted with the daylight saving of
its own moment (`:394-405`), so bars from before the switch keep their UTC hour (tested:
`tests/trader/test_mt5.py:230-238, 560-570`). Sessions are evaluated on the laptop clock in Europe/Amsterdam
(`engine.py:94-107`), the FTMO day in Europe/Prague (`risk_guard.py:50-56`), the ForexFactory events carry their own
offset (`calendar.py:40-42, 69-77`), the seeded CSV is UTC. The nightly server restart moves to 22:00 Amsterdam for
the week (`live.py:367-368` tolerates 5 minutes before a message), the 4H candles open at 22, 02, 06, 10, 14, 18
Amsterdam, the US 08:30 releases fall at 13:30 Amsterdam (the blackout covers 13:00-14:00) and the New York open at
14:30. The research candles were built the same way (`scripts/build_mt5_like.py`, New York + 7), so the backtest
traded these weeks as the bot will.

**Numbers** (`analyses.py` (a)). Trades opened in mismatch weeks (both switches, 2017-2026): in sample 25 trades,
+18.5R, +0.74R a trade against +0.76R in other weeks (gold 13 trades +11.9R); out of sample 31 trades, +9.1R, +0.29R
against -0.02R. By New York hour the 10:00 bucket (the 10:00 ET releases, 15:00 Amsterdam) lost in both periods (7
trades -1.8R, 4 trades -2.4R): small samples, no rule.

**Likelihood / impact.** Low for the clock paths: the convention is confirmed by FTMO's own dates and the code's
`_ny7` branch is the tested one. If the server nevertheless switched on 25 October (an EET convention), the tick
would set the offset to +2 h but `_ny7` would still convert stamps as New York + 7: every bar an hour early, the 5m
feed read as stale, no new setups all week (`live.py:1223-1235, 1327-1330`; `config.py:566-567`), the zones aged by
an hour. The behavioural side (the data hour, the 4H boundaries) is in the backtest's weeks. A laptop clock error
(Windows time sync off) has the same symptom at any time: the sessions, the blackout and the stale test all run on the
laptop clock.

**Detection.** `⚠️ {symbol}: geen nieuwe 5m-candles sinds 20m tijdens de handelstijden` within 20 minutes of a
session start (`live.py:1237-1254`), `⏸ {symbol}: setup ignored, the data is stale (5m 60m old)` and `stale` journal
rows (`live.py:1327-1330`), the heartbeat's `stale` and `last_candle` fields (`live.py:1162-1166`), the console
`[live] {symbol} data: ... | stale: ...` line.

**Mitigation (read-only checks on Monday 26 October, 09:00-09:15 Amsterdam, by Claude Code on the laptop).**
(1) `mt5-test --symbol EURUSD --tf 5m` with `MT5_PATH` set and the login variables cleared: the printed server offset
must read `+3.0 h` (and `+2.0 h` on Monday 2 November) and the last bar's UTC time must be the current five-minute
boundary; (2) the four `heartbeat_*.json`: `stale` empty and `last_candle` within ten minutes of now (UTC);
(3) the windows' console lines around 22:00-22:03 Amsterdam on 26 October: `connected again after 1 min` confirms the
server's midnight at 22:00 Amsterdam, i.e. no switch on FTMO's side; (4) the Account MetriX tooltip: the daily reset
countdown must point at midnight Prague (02:00 platform time that week); (5) `w32tm /query /status` for the laptop
clock. If (1) prints `+2.0 h` during the week, pin `MT5_SERVER_OFFSET_HOURS=2` in `ftmo_local.bat` and restart
outside the sessions; the pin bypasses the New York path (`mt5.py:318-320`). Nothing to change otherwise.

## 7. Telegram or the watchdog goes silent

**Mechanism.** `TelegramNotifier.send` never raises: a failed message is a console line at most once a minute
(`notify/telegram.py:120-148, 95-100`), `send_photo` the same (`:150-166`). The watchdog's own alerts go through the
same `send` (`watchdog.py:88-105`), so a Telegram outage silences the alarm with the alarm. The healthchecks.io ping
(`watchdog.py:124-144`, `cli.py:626-630`) is independent of Telegram, but its alert reaches Max through whatever
integrations the check has; with Telegram as the only one, a Telegram outage also hides the ping alert. A token
rotated, a chat id lost, `TELEGRAM_*` missing from the environment of a new window, or a corporate/DNS block are the
other silent cases: the window prints `telegram=dry-run` at its start and `[telegram dry-run]` lines, and trades on.

**Likelihood / impact.** Medium that some silence occurs in six weeks; nothing for the account (the bot does not need
Telegram), everything for Max's awareness (a position he does not know about, a loop error nobody reads).

**Detection.** The absence of the 08:45, 12:55, 22:00 (four markets) and 22:05 messages; the dashboard
(`scripts/dashboard.bat`, local) keeps showing the heartbeats; the console `[telegram] message not sent: ...`.

**Mitigation.** Config: add an e-mail integration to the healthchecks.io check beside Telegram (so a Telegram outage
with the pings alive still has a second channel for everything else, and a dead laptop reaches Max by e-mail); a
read-only check in the restart prompt: each window's start line must say `telegram=on`, and
`findstr /C:"WATCHDOG_PING_URL" scripts\ftmo_local.bat | find /c /v ""` must print 1 (the line exists; the address
itself is not shown). Manual rule: no 08:45 messages by 09:00 means a look at the windows before the window opens.
Smallest code change (optional): the watchdog pings healthchecks only when its last Telegram send succeeded within
the hour, so Telegram silence becomes a missed ping and healthchecks' e-mail says so.

## 8. The laptop sleeps, Windows updates, MT5 reconnects during a position

**Mechanism.** The windows poll every 60 s (`live.py:1124-1145`); a closed terminal or a server restart is re-initialised
at most once a minute (`mt5.py:494-536`) and reported after 5 minutes (`live.py:1256-1284`); a sleeping laptop stops
everything, including the watchdog and its pings. While down: the stop and target are on the server (`mt5.py:637-649`),
a resting limit expires on the server 10 minutes after its own expiry where the symbol allows it
(`mt5.py:730-746`), break-even moves are missed (the original stop stays: a +4R winner can come back to -1R, inside the
guard's model), NAS100's 48-hour time stop is missed (`manage_positions`, `live.py:1894-1923`; it closes at the first
scan back), entries are missed. On waking: the day start is rebuilt from the deal history (`risk_guard.py:65-77`), a
restored position gets its break-even trigger from the order comment and its risk from the original stop
(`mt5.py:407-441`), the limits file is re-read (`live.py:1679-1688`), the handled-setups file prevents a double entry
(`live.py:1321-1325`). After a reboot nothing restarts the windows: `start_ftmo.bat` is run by hand (no logon task in
the docs). Patch Tuesday 10 November falls inside the window.

**Likelihood / impact.** Medium: one unplanned stop in six weeks is more likely than not. Impact: missed entries
(about +0.6R each, 2-3 a week across the four markets), a missed break-even move (at most the position's 1R, x2 on a
4H zone), never a breach beyond the worst case.

**Detection.** healthchecks.io within 15 minutes (period 5, grace 10) if the ping line is set; the dashboard cards
red after 5 minutes (local only); the heartbeats' `time`; a `start` journal row after the restart; the watchdog's
`✅ ... scanning again` once back.

**Mitigation (laptop, Max's choice).** The existing read-only check in `docs/LAPTOP_TASKS.md` ("Once: the laptop
itself"), run again before 10 November: sleep on mains off, lid closed = nothing, active hours covering 08:00-23:00,
no pending restart. Two settings to consider: Windows "use my sign-in info to finish setting up after an update" and a
Task Scheduler task at logon that runs `scripts\start_ftmo.bat` (the windows then come back after an update restart;
the script starts only the missing windows, `live.py:233-293`). Manual rule after any restart: the restart prompt in
`LAPTOP_TASKS.md` (four start records on one commit, risk 1.5, fresh heartbeats, four start messages).

## 9. The spread cap on NAS100 and BTC

**Mechanism.** `risk.max_spread_stop_fraction 0.3` in all four profiles: at execution the ask-bid spread is read twice
from the terminal and the entry refused when it exceeds 30 % of the distance from the market price to the stop
(`live.py:1560-1571`); the spread at that moment only, never at a limit's fill; for a limit entry the test uses the
market price's stop distance, while the limit's own stop is 25 % shorter (`_place_limit`, `live.py:1620-1655`), so the
effective cap at the limit is 40 % of its stop. A spread under the cap passes with its cost. The research assumed
NAS100 1.5 points and BTC $15; neither is measured on FTMO (the laptop task in `LAPTOP_TASKS.md`). The NAS100 morning
window (09:00-11:00 Amsterdam, 03:00-05:00 New York) trades on the overnight Globex book, where index CFD spreads are
widest.

**Numbers** (`analyses.py` (c), `extra.py`). NAS100 stops at the fill (in sample) p10/25/50/75 = 14.5 / 21 / 27.5 / 44
points: at a 1.5-point spread the median cost is 0.055R and nothing is refused; at 3 points 0.11R and nothing refused;
at 5 points 0.18R and **21 % of the trades refused** (out of sample, with its smaller stops: 56 %). NAS100's morning
trades: 13 of 43 in sample, +0.74R a trade (afternoon +0.92R), median stop 21.6 points against 27.8; out of sample the
morning lost (-0.12R a trade over 29). BTC stops p50 $432: $15 costs 0.035R, $30 0.07R, $45 0.10R with 5 % refused
(out of sample, stops half the size: 25-38 % refused at $30-45). Gold at the measured $0.37: 0.043R median, nothing
refused (out of sample 8 %). EURUSD at 0.1 pip plus $3 a lot: 0.05R. So the 0.10R research assumption holds for
EURUSD, gold and BTC at the measured or assumed spreads and for NAS100 up to about 3 points.

**Likelihood / impact.** The NAS100 morning spread is the open question; if it runs 3-5 points there, a fifth of the
morning signals are refused and the rest cost 0.1-0.2R each. No path to a fail; an edge cost of a few R over the window.

**Detection.** `⛔ {symbol}: not executed - spread N is NN % of the stop distance (max 30 %)` and the `not_executed` row
with `price` and `spread` (`live.py:1568-1571`); the forward report's slippage columns per trade.

**Mitigation (laptop, read-only).** The spread measurement in `LAPTOP_TASKS.md` ("Once: the spreads of NAS100 and
BTC") for the last three sessions, split by window (`mt5-spreads --day`); then, as config, the measured medians as
`typical_spread_pips` in `config/dorus_live_nas100.yaml` and `config/dorus_live_btc.yaml`, so the backtest's own spread
cap (6b2d7b7) and the cost haircut match the live refusals. If the NAS100 morning median is 4 points or more: the
morning window off for NAS100 only is the rule to test (`session.windows [[13:00, 17:00]]` in that profile; out of
sample the morning lost anyway, in sample it gave +9.6R over 13 trades, so it needs the replay before adoption).

## 10. The margin check on 10k

**Mechanism.** Before an order the window asks the server for the margin of one lot (`mt5.py:276-288`) and the free
margin (`:290-293`), caps a position at 45 % of equity and 90 % of the free margin (`prop_firm.max_margin_pct`,
`config.py:438-439`; `live.py:1463-1483`) and cuts the lots to fit, refusing only below the minimum lot
(`live.py:1593-1605`, limits `:1637-1644`). The window prints `margin: 1 lot ... (about 1:X)` at its start
(`cli.py:347-362`). FTMO's Standard account: "up to 1:100" (its FAQ); the README read about 1:100 forex, 1:50 indices and
gold, 1:2-1:3.3 crypto in the terminal.

**Numbers** (`analyses.py` (d), the live stakes on 10k, leverage 100/50/50/2). BTC: median 0.17 lot, margin 60 % of
equity at the median, cut in 74 % of trades, 59 % of the planned risk kept (known, in the replay). NAS100: median 5.4
lots (max 14), margin median 26 %, p90 51 %; cut in 19 % of trades, 40 % of the 4H-zone trades, 84 % of the risk kept;
none at 1:100. EURUSD (median 0.63 lot, max 3.7) and gold (0.18 lot, max 0.76) never reach the cap. Two positions at
once: the cap is 45 % each, so 90 % of equity in margin at worst, a margin level of 111 %: far from any stop-out with
3 % stops.

**Likelihood / impact.** Certain and risk-reducing; the only failure is the server not answering `order_calc_margin`
(then no cap, and a `No money` refusal: `⛔ order failed - ... retcode 10019`, harmless).

**Detection.** `💸 ... (margin: lots cut from X, risk NN % of planned)` and `⛔ not enough margin for the minimum lot`
(`live.py:1598-1602`); the forward report's margin fields.

**Mitigation.** Read-only, at every restart: the margin line of each window (BTC about 1:2, NAS100 1:50 or 1:100).
Nothing to change.

## 11. The nightly break, NAS100's daily break, Thanksgiving

**Mechanism.** FTMO's server restarts at its midnight (23:00 Amsterdam; 22:00 in the mismatch week): the link check
fails for about a minute, the scan is skipped (`live.py:1129-1133`), a message only after 5 minutes (`:1273-1276`);
the 22:00 summaries and the 22:05 day report read the terminal before it (`DailyJob` retries three rounds then says
`📒 The day report could not read the account`, `watchdog.py:168-189`, `cli.py:646-647`). NAS100's daily break: a
48-hour time stop that falls in the break cannot close (`⚠️ closing ... failed ... trying every scan`,
`live.py:1916-1923`) and closes at the reopen; outside the sessions the feed check is silent (`:1245-1247`).
Thanksgiving: the sessions end at 17:00 Amsterdam, before the US early closes; Friday 27 November's early close puts a
NAS100 position into the weekend from 19:00 Amsterdam.

**Numbers.** Thanksgiving weeks in the ledgers (`analyses.py` (g)): 24 trades over seven years, +8.6R, 2024's three
Thursday/Friday-morning trades all lost (-3.0R), 2025's four +4.3R: no pattern. The election week of 2024: two trades,
+1.2R.

**Mitigation.** Nothing to change. A manual note: on Friday 27 November apply section 3's Friday rule at 18:30
Amsterdam instead of 21:30, and treat the night of 3 November (midterm results) like a weekend for a NAS100 double-stake
position.

## 12. The news calendar after 4 November

**Mechanism.** The blackout refuses entries 30 minutes either side of a high-impact event of the market's currencies
(`calendar.py:132-144`, `engine.py:449-456`); the events are the seeded `data/calendar/high_impact.csv` plus
ForexFactory's this-week and next-week files, refreshed hourly and cached next to the journal (`live.py:1191-1221`).
The seeded CSV **ends on 4 November 2026** (five rows in November), and its USD rows of 2 and 4 November (ISM) are at
14:00 UTC where the winter clock puts them at 15:00 UTC (the 2025 rows have 15:00): a spurious USD blackout
14:30-15:30 Amsterdam on those two days and the real one only if ForexFactory delivers. From 5 November every blackout,
NFP on the 6th and CPI on the 10th included, depends on ForexFactory being reachable. The watchdog says
`📰 {symbol}: the news calendar ended ..., no event ahead this week` only on Monday to Thursday (`watchdog.py:69-74`),
so a feed that fails from Thursday evening leaves Friday's NFP uncovered without a word. A resting EURUSD or NAS100
limit (valid four hours) can still fill inside a window (prop_firm.md candidate 8).

**Likelihood / impact.** ForexFactory returned 429 to five windows an hour before the cache was built; a day without
the feed is plausible once or twice in six weeks (about 5 % per release day). An entry at 14:25 before NFP: a -1R
print is the usual outcome, -2R or worse with slippage, twice that on a 4H zone; no fail by itself.

**Detection.** The 08:45 and 12:55 briefing line `📰 Nieuws vandaag: ...` must name the day's events (`live.py:567-584`);
`📰 Geen high-impact nieuws meer vandaag` on 6 or 10 November means the feed failed; the heartbeat's `calendar_until`.

**Mitigation (data).** Extend the seeded CSV through December with the USD and EUR high-impact dates (a 20-row change
to `data/calendar/high_impact.csv`, the UTC hours winter-correct: NFP 6 Nov 13:30, CPI 10 Nov 13:30, PPI and retail
sales mid-November, FOMC minutes 18 Nov 19:00, ISM 1 and 3 Dec, NFP 4 Dec, CPI 10 Dec, FOMC 16 Dec 19:00; EUR: ECB
17 Dec, flash CPI 2 Dec) and fix the two ISM rows; or run `from_tradingview` + `save_events` over November-December.
Manual rule meanwhile: on 6 and 10 November read the 08:45 line; if it shows no 14:30 event, close the windows before
14:00 Amsterdam or accept a blackout-less afternoon.

## 13. The parity check's assumptions

The weekly check (`parity.py:1-19`) rebuilds each window's settings from its start record, exports the terminal's
candles (`EXPORT_COUNTS`, `:36-38`: 5000 5m bars reach back about three weeks), warms the backtester up 7 days
before the week (`warmup_days`, `:649`; a shortage is noted as `short warm-up ... zone and visit memory before it is
missing`, `:793-796`) and matches setups by id. It assumes: one market at a time (the account lock, the other
markets' slots and the margin are "live-only rules", `:439-443`); fills on candle prices (bid) and limit fills on a
trade-through, against live ask/bid fills; the backtest's spread cap on `typical_spread_pips` against the live spread;
the same code on both sides, so a bug shared by the engine and the backtester is invisible; the laptop awake and logged
in on Friday 22:30 with the terminal running (`schtasks`), else no report. It validates the plumbing: that the windows
signal what the engine signals on the same candles. It cannot tell whether the edge is there (the forward journal's R
and the day report's edge meter do that: `edge_line`, `forward.py:322-333`, a warning under 0R over the last 20 trades
or under -5R over 30). Read it as: `live only` is the serious verdict; `backtest only` with "the window was down" is
expected after restarts; `outcome differs` on a stop versus target is a fill difference worth a look, on a refusal a
live-only rule.

## 14. Phase 2 on a new login

If phase 1 passes inside the window, the Verification runs on a fresh account with its own login: the terminal is
logged in to the new account, `MT5_LOGIN` stays cleared (`start_ftmo.bat`), and a window still running from phase 1
reports `MT5 is logged in to account X, this window trades Y: not trading` (`mt5.py:529-532`) until restarted. Then:
`set "TARGET=5"` in `ftmo_local.bat` (the watchdog's target line; `PROTECT` stays unset), the restart check, and a
note that the 22:05 report's `N trading day(s)` counts the journal's fill days since the journal's first day
(`forward.py:306`, `cli.py:503-509` with `since` None), so it keeps phase 1's days unless the journal is started afresh
(a new `--journal` path in `ftmo_local.bat` is the clean way: new heartbeat folder, new memory files; the old folder
stays as the record). `guard_day_high.json` carries over for the same account size (harmless: the 2-Step floor is
static, `drawdown_basis initial`).

## 15. What is not a risk here

- The 23:00 restart, the one-window lock, the account lock (deferral, never a trade without it, `live.py:152-199,
  1806-1816`), a stopless position (refuses new trades and says so), the approval flow (off), the Dorus check (a
  thread, advisory), the chart rendering (never fatal), the two EURUSD positions (modelled, the worst case covers
  both), the BTC candle anchoring (a research-data question; the window trades the terminal's candles).
- The ladder and the target protection: the replay says keep the ladder, leave `PROTECT` off (prop_firm.md 3.3, 5).
- Correlated USD positions: the worst-case check caps the joint stop loss under 4 % (prop_firm.md 3.2).

## Appendix: the numbers

`research/premortem/analyses.py` (run 14 October, 15 s) and `extra.py`. Ledgers: `aca/eutwo_EURUSD`, `base_XAUUSD`,
`rr08_NAS100`, `base_BTCUSD` (2024-02..2026-09, 317 trades) and the `oos_*` set (2017..2023, 698 trades); the live
stakes rebuilt per trade by `research/prop_lib.py` (4H x2, BTC x0.5, EURUSD's 1D+1H pair x0.5, a 50/50 month x0.5,
BTC cut to the crypto margin), the guard as live, 0.10R costs.

- Phase 1 within 47 days: 2026 starts 100 % (93 % at 0.25R; 98 % without BTC; 100 % with NAS100 4H at the single
  stake); 2024-25 starts 47 % (38 %; 45 %); 2017-23 starts 9 %. The +10 % touched before the 4th trading day: 31 % /
  7 % / 4 % of starts. Trading days in 47 days: median 6 / 9, never under 4 (1 % out of sample).
- Double-stake trades: 0.88 a month in sample, 21 % held over a weekend; 0.78 a month out of sample, 15 %. Weekends
  with 3 % or more open: 5 % of 139. Positions held over a Prague midnight: 19 %, +94.7R.
- Mismatch weeks: +0.74R a trade (25) in sample, +0.29R (31) out of sample, against +0.76R and -0.02R elsewhere.
- Spread cost at the fill (median R): NAS100 1.5 / 3 / 5 points 0.055 / 0.11 / 0.18 (refused 0 / 0 / 21 %); BTC $15 /
  30 / 45 0.035 / 0.07 / 0.10 (0 / 0 / 5 %); gold $0.37 0.043 (0 %); EURUSD 0.4 pip 0.05.
- Margin on 10k: BTC cut in 74 % of trades (59 % of risk kept), NAS100 19 % (4H 40 %, 84 % kept), EURUSD and gold
  never.
- Thanksgiving weeks: 24 trades, +8.6R over seven years.

## Sources

- FTMO trading objectives and FAQ (daily loss from the midnight CE(S)T balance, equity-based; 10 % static; four
  trading days with an opened position; positions closed before requesting the next phase): prop_firm.md section 1.
- FTMO's platform time and the US switch: the FTMO/OANDA FAQ "MetaTrader 5 = GMT+2 +DST" and "up to 1:100" on the
  Standard account (https://ftmo.oanda.com/faq/what-are-the-account-specifications/); FTMO trading updates quoted in
  search results: "GMT+3 (until 3 Nov 2025) and GMT+2 thereafter", "Starting on Sunday, 8 Mar 2026, following the DST
  change ... GMT+3 / CET+2", and the October 2025 notice of a one-week two-hour offset between Prague midnight and
  platform midnight with the daily reset countdown in the Account MetriX tooltip (https://ftmo.oanda.com/?p=2254,
  https://ftmo.oanda.com/?p=2707). The general convention: https://www.mql5.com/en/blogs/post/774934.
- FOMC 27-28 October 2026: https://www.federalreserve.gov/newsevents/2026-october.htm. NFP 6 November 2026 08:30 ET:
  https://www.bls.gov/schedule/news_release/empsit.htm. CPI 10 November 2026 08:30 ET:
  https://www.bls.gov/schedule/news_release/cpi.htm. Thanksgiving 2026 (CME): https://www.cmegroup.com/trading-hours.html
  and https://blog.crosstrade.io/cme-trading-hours-2026/ (product times final about two weeks before).
