# Trade frequency, and what the first weeks of the challenge look like (14 October 2026)

Max's question on day two of the FTMO challenge: "is the system really working? I want to see a trade tomorrow or the
day after." This note measures what the live set does in the first days and weeks from any starting day, so that silence
can be told from failure. Everything is from the research ledgers of the four live profiles (EURUSD `aca/eutwo`, gold
`aca/base_XAUUSD`, NAS100 `aca/rr08`, BTC `aca/base_BTCUSD`), in sample January 2024 - 24 September 2026 (716 trading
days, 33 months) and out of sample January 2017 - December 2023 (BTC June 2020 - 2023), plus an engine replay of the four
profiles over 2024-2026 that records the touch messages ("👀 ... waiting for a confirmation") and the signals the live
window would have sent. A trading day (td) is a weekday; no ledger trade opens on a weekend. A "start" is the beginning
of a trading day; a trade on that same day is a wait of 1 td. The frequency does not depend on the stake, so the live
multipliers only matter for the challenge replay (section 6), where they are the ones of `aca/challenge_sim.py` (1.5 %,
ladder -3 % -> 1.0, -6 % -> 0.5, 4H zones x2, EURUSD 1D+1H half, month 50/50 half, BTC half, two open, 0.10R costs).

Scripts and outputs: `research/frequency/freq_ledgers.py` (-> `freq_out.md`, `challenge_by_start.csv`), `freq_extra.py`
(-> `freq_extra_out.md`), `freq_spells.py` (-> `freq_spells_out.md`), `freq_first_market.py`, `touch_replay.py` +
`run_replay.sh` (-> `events_<SYMBOL>.csv`, `replay_<SYMBOL>.log`; the first pass, no trades marked), `touch_replay2.py` +
`run_replay2.sh` (-> `events2_<SYMBOL>.csv`; every signal marks its zone visit as traded, the pass the tables use),
`freq_touch.py` (`EVENTS_PREFIX=events2`, -> `freq_touch_out.md`), `assemble.py` (this file from `frequency_template.md`).
All under `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/research/frequency/`.

## 1. The plain table for the trader

The four markets together, the live profiles, from a random trading-day start. In sample 2024-2026 / starts in 2026
only / out of sample 2017-2023:

| From the start of a trading day | at least one trade | at least one touch message ("👀 waiting for a confirmation") |
|---|---|---|
| by the end of the first trading day | 35 % / 36 % / 31 % | 61 % / 55 % / (not replayed) |
| in the first 2 trading days | **55 % / 55 % / 51 %** | **81 % / 73 %** |
| in the first 3 trading days | 69 % / 68 % / 64 % | 88 % / 84 % |
| in the first 4 trading days | 77 % / 78 % / 74 % | - |
| in the first week (5 td) | **83 % / 84 % / 81 %** | **96 % / 95 %** |
| in the first two weeks (10 td) | **95 % / 97 % / 95 %** | **100 % / 100 %** |
| in the first month (20 td) | 100 % / 100 % / 100 % | 100 % / 100 % |
| median wait (p90) | 2 td (8) / 2 td (7) / 2 td (8) | 1 td (4) / 1 td (4) |

A confirmed setup (a "signal": the shift closed, before the guard, the limit and the R:R re-check at the fill) sits
between the two: 37 % of starts see one on the first day, 57 % within two trading days, 84 % within a week, 96 % within
two weeks (2026 starts 37 / 55 / 84 / 96 %); 81 % of signals became ledger trades.

In calendar days from a start at 00:00 UTC (in sample / 2026 / out of sample): a trade within 2 calendar days 52 / 50 /
48 %, within 3 days 61 / 56 / 57 %, within 7 days 83 / 84 / 81 %, within 14 days 95 / 97 / 95 %, within 30 days 100 %
everywhere; median 1.6 days, 90th percentile 9.3 days. A Monday start is the slowest (50 % with a trade by Tuesday's
close, 83 % by Friday's); a Tuesday to Thursday start reaches 58-60 % within two trading days. The challenge started on
Monday 13 October: by the close of Wednesday 15 October (3 td) the backtest gives 69 %, by Friday 17 October 83 %, by
Friday 24 October 95 %.

How many trades the first two weeks bring (10 td, all four markets): none 5 % (2026 3 %, out of sample 5 %), one 10 %,
two 12 %, three or more 74 %; mean 4.5 (10th percentile 1, 90th 8); the first week alone: mean 2.3 trades, no trade at
all 17 % (2026 16 %, out of sample 19 %). FTMO's minimum of four trading days with a trade takes a median of 11 td (p90
20; 2026: 10 and 17; out of sample 13 and 24).

Per market the picture is very different. The probability of **no trade at all in the first two weeks**: EURUSD 63 %
(2026 61 %, out of sample 67 %), NAS100 56 % (40 %, 62 %), BTC 38 % (43 %, 37 %), gold 16 % (13 %, 13 %). Gold is the
window that shows up; EURUSD and NAS100 are silent for weeks by design (12 of 33 months had no EURUSD trade, 13 none
on NAS100).

What the first trades look like (R after 0.10R costs, at the live multipliers; in sample / out of sample): the first
trade loses 49 % / 65 % of the time; the first three trades together are negative 32 % / 57 %; the first five 28 % / 56 %
(median +1.7R / -0.7R); the first ten 15 % / 58 %. The fifth trade closes a median 14 (18) calendar days after the
start, the tenth 30 (39). So with the 2024-2026 edge intact, roughly one start in four is still under water after two
weeks and five trades; out of sample, where the edge was absent, it is one in two. Five or ten trades cannot separate the
two cases; the edge meter in the 22:05 report (the R of the last 20 and 30 closed trades) is the instrument, and that is
two to three months away.

## 2. Trades per market, per month and per trading day

| market | trades | months | a month (mean) | median month | months with 0 | a trading day | trading days with ≥1 | with ≥2 | gap median (td) | gap p90 | longest gap (td) | gaps > 5 td | > 10 td | > 20 td |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 47 | 33 | 1.42 | 1 | 36 % | 0.066 | 5.3 % | 1.3 % | 11 | 45 | 61 | 57 % | 51 % | 41 % |
| XAUUSD | 143 | 33 | 4.33 | 4 | 3 % | 0.200 | 19.3 % | 0.7 % | 3 | 10 | 28 | 33 % | 10 % | 4 % |
| NAS100 | 43 | 33 | 1.30 | 1 | 39 % | 0.060 | 5.9 % | 0.1 % | 8 | 35 | 93 | 76 % | 44 % | 22 % |
| BTCUSD | 89 | 33 | 2.70 | 3 | 18 % | 0.125 | 11.2 % | 1.3 % | 5 | 19 | 82 | 47 % | 32 % | 9 % |
| **all four** | 322 | 33 | 9.76 | 9 | 0 % | 0.451 | 34.9 % | 9.1 % | 2 | 6 | 20 | 13 % | 3 % | 0 % |

| market | trades | months | a month (mean) | median month | months with 0 | a trading day | trading days with ≥1 | with ≥2 | gap median (td) | gap p90 | longest gap (td) | gaps > 5 td | > 10 td | > 20 td |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 13 | 9 | 1.44 | 1 | 22 % | 0.068 | 5.8 % | 1.0 % | 12 | 27 | 47 | 50 % | 50 % | 50 % |
| XAUUSD | 38 | 9 | 4.22 | 5 | 0 % | 0.199 | 19.9 % | 0.0 % | 3 | 11 | 22 | 35 % | 14 % | 3 % |
| NAS100 | 16 | 9 | 1.78 | 1 | 22 % | 0.084 | 7.9 % | 0.5 % | 8 | 22 | 35 | 79 % | 36 % | 14 % |
| BTCUSD | 18 | 9 | 2.00 | 1 | 22 % | 0.094 | 8.9 % | 0.5 % | 9 | 24 | 25 | 56 % | 50 % | 19 % |
| **all four** | 85 | 9 | 9.44 | 9 | 0 % | 0.445 | 36.1 % | 7.9 % | 2 | 6 | 16 | 13 % | 1 % | 0 % |

| market | trades | months | a month (mean) | median month | months with 0 | a trading day | trading days with ≥1 | with ≥2 | gap median (td) | gap p90 | longest gap (td) | gaps > 5 td | > 10 td | > 20 td |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 97 | 84 | 1.15 | 1 | 43 % | 0.053 | 4.1 % | 1.0 % | 12 | 55 | 110 | 74 % | 59 % | 45 % |
| XAUUSD | 371 | 84 | 4.42 | 4 | 0 % | 0.203 | 18.8 % | 1.5 % | 4 | 11 | 34 | 34 % | 12 % | 1 % |
| NAS100 | 100 | 84 | 1.19 | 1 | 43 % | 0.055 | 5.5 % | 0.0 % | 10 | 42 | 125 | 60 % | 48 % | 23 % |
| BTCUSD | 130 | 43 | 3.02 | 2 | 14 % | 0.139 | 12.2 % | 1.5 % | 4 | 22 | 54 | 46 % | 25 % | 12 % |
| **all four** | 698 | 84 | 8.31 | 8 | 0 % | 0.382 | 30.7 % | 6.0 % | 2 | 7 | 24 | 16 % | 3 % | 0 % |

The frequency is stable across the two periods (9.8 a month in sample, 8.3 out of sample, 9.4 in 2026) while the edge
is not: the set trades about as often in the years it loses. The "gap" columns count trading days between consecutive
trade days (a gap of 1 = the next trading day).

Three things that do not change the rhythm live: the account's two open slots refuse 1 of the 322 ledger trades and the
worst-case guard 7 (a replay of the whole period at 1.5 % with the ladder; trades hold a median 1.8 hours, p90 21.5 h);
the live spread cap (`risk.max_spread_stop_fraction: 0.3`, not in the research runs) binds on none of the 322 at the
spreads assumed (gold 0.34-0.37, EURUSD 1.2 pips, NAS100 1.5 points, BTC 25 USD: the smallest gold stop in the ledger is
3.5 USD); and the hour: 36 % of the opens fall in the 09-11 window and 60 % in 13-17 Amsterdam (4 % are limit fills
just after a window), so most of the first week's messages come in the afternoon.

## 3. Gaps between trades and the dry spells

Trading days *without* a trade between two trades, all four markets: in sample mean 1.9, median 1, p75 2, p90 5, p95 7,
longest 19; out of sample mean 2.2, median 1, p75 3, p90 6, p95 8, longest 23. A silence of more than two weeks (more
than 10 td) comes about 2.5 times a year in both periods:

| from (last trade) | to (next trade) | trading days without a trade | calendar days |
|---|---|---|---|
| 2025-07-24 | 2025-08-21 | 19 | 28 |
| 2024-06-21 | 2024-07-16 | 16 | 25 |
| 2026-03-31 | 2026-04-22 | 15 | 22 |
| 2025-03-04 | 2025-03-25 | 14 | 21 |
| 2025-11-06 | 2025-11-26 | 13 | 20 |
| 2024-06-06 | 2024-06-21 | 10 | 15 |
| 2025-04-23 | 2025-05-08 | 10 | 15 |

spells > 10 td a year: 2024: 2, 2025: 4, 2026: 1; average 2.5 a year
trading days without a trade between two trades: mean 1.9, median 1, p75 2, p90 5, p95 7, max 19

| from (last trade) | to (next trade) | trading days without a trade | calendar days |
|---|---|---|---|
| 2023-04-14 | 2023-05-18 | 23 | 34 |
| 2019-03-06 | 2019-04-02 | 18 | 27 |
| 2017-05-04 | 2017-05-30 | 17 | 26 |
| 2018-09-04 | 2018-09-27 | 16 | 23 |
| 2019-10-02 | 2019-10-25 | 16 | 23 |
| 2021-06-22 | 2021-07-15 | 16 | 23 |
| 2023-08-18 | 2023-09-12 | 16 | 25 |
| 2018-08-08 | 2018-08-28 | 13 | 20 |
| 2020-02-27 | 2020-03-18 | 13 | 20 |
| 2020-03-20 | 2020-04-09 | 13 | 20 |
| 2017-07-21 | 2017-08-09 | 12 | 19 |
| 2018-07-18 | 2018-08-03 | 11 | 16 |
| 2021-05-26 | 2021-06-11 | 11 | 16 |
| 2021-11-30 | 2021-12-16 | 11 | 16 |
| 2021-12-30 | 2022-01-17 | 11 | 18 |
| 2020-04-30 | 2020-05-15 | 10 | 15 |
| 2023-05-24 | 2023-06-08 | 10 | 15 |
| 2023-10-24 | 2023-11-08 | 10 | 15 |

spells > 10 td a year: 2017: 2, 2018: 3, 2019: 2, 2020: 3, 2021: 4, 2023: 4; average 2.5 a year
trading days without a trade between two trades: mean 2.2, median 1, p75 3, p90 6, p95 8, max 23

(The April-May 2023 spell falls in the months where the HistData 5m files miss 20-24 % of their slots, `BACKLOG_hand.md`
A.2, so it may be partly a data gap.)

## 4. The wait for the first trade from a random start

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 5 | 10 | 14 | 22 | 37 | 62 | 15 | 38 | 714 |
| XAUUSD | 19 | 35 | 47 | 63 | 84 | 97 | 4 | 14 | 714 |
| NAS100 | 6 | 11 | 17 | 26 | 44 | 66 | 12 | 53 | 714 |
| BTCUSD | 11 | 20 | 27 | 39 | 62 | 85 | 7 | 28 | 714 |
| **all four** | 35 | 55 | 69 | 83 | 95 | 100 | 2 | 8 | 714 |

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 6 | 11 | 15 | 24 | 38 | 70 | 13 | 34 | 191 |
| XAUUSD | 20 | 34 | 47 | 63 | 87 | 99 | 4 | 12 | 191 |
| NAS100 | 8 | 15 | 22 | 35 | 59 | 84 | 7 | 22 | 191 |
| BTCUSD | 9 | 14 | 20 | 30 | 57 | 92 | 9 | 20 | 191 |
| **all four** | 36 | 55 | 68 | 84 | 97 | 100 | 2 | 7 | 191 |

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 4 | 8 | 12 | 19 | 33 | 54 | 18 | 53 | 1825 |
| XAUUSD | 19 | 35 | 47 | 65 | 87 | 98 | 4 | 12 | 1825 |
| NAS100 | 5 | 10 | 15 | 23 | 38 | 59 | 15 | 58 | 1825 |
| BTCUSD | 12 | 22 | 29 | 42 | 63 | 85 | 7 | 25 | 935 |
| **all four** | 31 | 51 | 64 | 81 | 95 | 100 | 2 | 8 | 1825 |

By the start's month of the year (all four markets):

| start month | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | start months |
|---|---|---|---|---|---|---|---|---|---|
| Jan | 32 | 56 | 72 | 90 | 100 | 100 | 2 | 5 | 68 |
| Feb | 33 | 59 | 77 | 93 | 100 | 100 | 2 | 5 | 61 |
| Mar | 41 | 58 | 66 | 75 | 92 | 100 | 2 | 9 | 64 |
| Apr | 26 | 45 | 61 | 76 | 89 | 100 | 3 | 10 | 66 |
| May | 47 | 70 | 83 | 97 | 100 | 100 | 2 | 4 | 66 |
| Jun | 35 | 54 | 65 | 78 | 90 | 100 | 2 | 10 | 63 |
| Jul | 22 | 39 | 54 | 75 | 90 | 100 | 3 | 13 | 69 |
| Aug | 30 | 50 | 61 | 73 | 92 | 100 | 3 | 11 | 64 |
| Sep | 46 | 70 | 83 | 95 | 100 | 100 | 1 | 3 | 61 |
| Oct | 50 | 74 | 87 | 93 | 100 | 100 | 2 | 4 | 46 |
| Nov | 39 | 51 | 61 | 76 | 90 | 100 | 2 | 10 | 41 |
| Dec | 22 | 40 | 58 | 78 | 100 | 100 | 3 | 7 | 45 |

| start month | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | start months |
|---|---|---|---|---|---|---|---|---|---|
| Jan | 34 | 55 | 68 | 84 | 99 | 100 | 2 | 7 | 155 |
| Feb | 37 | 59 | 73 | 88 | 99 | 100 | 2 | 6 | 140 |
| Mar | 22 | 40 | 50 | 69 | 90 | 100 | 3 | 10 | 157 |
| Apr | 33 | 52 | 66 | 83 | 93 | 97 | 2 | 7 | 148 |
| May | 30 | 49 | 60 | 73 | 90 | 100 | 3 | 10 | 156 |
| Jun | 28 | 45 | 59 | 78 | 96 | 100 | 3 | 8 | 151 |
| Jul | 27 | 46 | 59 | 77 | 96 | 100 | 3 | 8 | 153 |
| Aug | 29 | 48 | 64 | 78 | 93 | 100 | 3 | 9 | 157 |
| Sep | 30 | 53 | 68 | 83 | 95 | 100 | 2 | 8 | 149 |
| Oct | 32 | 51 | 62 | 80 | 95 | 100 | 2 | 7 | 154 |
| Nov | 32 | 57 | 73 | 91 | 100 | 100 | 2 | 5 | 152 |
| Dec | 35 | 55 | 71 | 88 | 98 | 100 | 2 | 6 | 153 |

In sample the months differ (a July or December start 39-40 % within two trading days, a September or October start
70-74 %), out of sample they do not (40-59 % in every month, 45-59 % outside March). Two Octobers are not a season: there
is no month-of-year rule to take from this. By weekday of the start:

| start on | 1 td | 2 td | 3 td | 5 td | 10 td | median wait (td) |
|---|---|---|---|---|---|---|
| Monday | 29 % | 50 % | 66 % | 83 % | 95 % | 3 |
| Tuesday | 36 % | 58 % | 73 % | 82 % | 95 % | 2 |
| Wednesday | 35 % | 60 % | 73 % | 86 % | 95 % | 2 |
| Thursday | 39 % | 59 % | 66 % | 82 % | 96 % | 2 |
| Friday | 35 % | 49 % | 65 % | 82 % | 95 % | 3 |

| set | P(trade within 1 day) | 2 days | 3 days | 7 days | 14 days | 30 days | median (days) | p90 (days) |
|---|---|---|---|---|---|---|---|---|
| EURUSD in sample | 5 | 9 | 12 | 22 | 37 | 67 | 20.5 | 52.5 |
| XAUUSD in sample | 19 | 32 | 38 | 63 | 84 | 98 | 4.6 | 19.4 |
| NAS100 in sample | 6 | 11 | 15 | 27 | 44 | 69 | 16.3 | 72.5 |
| BTCUSD in sample | 11 | 18 | 23 | 39 | 62 | 87 | 9.3 | 37.7 |
| **all four, in sample** | 35 | 52 | 61 | 83 | 95 | 100 | 1.6 | 9.3 |
| **all four, 2026** | 36 | 50 | 56 | 84 | 97 | 100 | 1.6 | 8.9 |
| **all four, out of sample** | 31 | 48 | 57 | 81 | 95 | 100 | 2.4 | 9.6 |

| period | P(0 trades) | P(1) | P(2) | P(3+) | mean | p10 | p90 | mean in the first 5 td | P(0 in 5 td) |
|---|---|---|---|---|---|---|---|---|---|
| in sample 2024-2026 | 5 % | 10 % | 12 % | 74 % | 4.5 | 1 | 8 | 2.3 | 17 % |
| 2026 | 3 % | 5 % | 16 % | 76 % | 4.4 | 2 | 8 | 2.2 | 16 % |
| out of sample 2017-2023 | 5 % | 11 % | 19 % | 66 % | 3.8 | 1 | 7 | 1.9 | 19 % |

| market | in sample | 2026 | out of sample |
|---|---|---|---|
| EURUSD | 63 % | 61 % | 67 % |
| XAUUSD | 16 % | 13 % | 13 % |
| NAS100 | 56 % | 40 % | 62 % |
| BTCUSD | 38 % | 43 % | 37 % |

| period | median (td) | p75 | p90 | within 10 td | within 20 td |
|---|---|---|---|---|---|
| in sample 2024-2026 | 11 | 15 | 20 | 48 % | 90 % |
| 2026 | 10 | 13 | 17 | 53 % | 97 % |
| out of sample 2017-2023 | 13 | 18 | 24 | 37 % | 82 % |

| first k trades | P(sum R < 0) | P(all k lost) | median sum R | p10 | p90 | median calendar days until the k-th trade closed |
|---|---|---|---|---|---|---|
| 1 | 49 % | 49 % | +0.23R | -1.10R | +2.67R | 2 |
| 3 | 32 % | 12 % | +1.27R | -2.21R | +7.55R | 8 |
| 5 | 28 % | 2 % | +1.73R | -2.79R | +9.55R | 14 |
| 10 | 15 % | 0 % | +6.15R | -1.70R | +14.78R | 30 |

| start month | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | start months |
|---|---|---|---|---|---|---|---|---|---|
| Jan | 34 | 55 | 68 | 84 | 99 | 100 | 2 | 7 | 155 |
| Feb | 37 | 59 | 73 | 88 | 99 | 100 | 2 | 6 | 140 |
| Mar | 22 | 40 | 50 | 69 | 90 | 100 | 3 | 10 | 157 |
| Apr | 33 | 52 | 66 | 83 | 93 | 97 | 2 | 7 | 148 |
| May | 30 | 49 | 60 | 73 | 90 | 100 | 3 | 10 | 156 |
| Jun | 28 | 45 | 59 | 78 | 96 | 100 | 3 | 8 | 151 |
| Jul | 27 | 46 | 59 | 77 | 96 | 100 | 3 | 8 | 153 |
| Aug | 29 | 48 | 64 | 78 | 93 | 100 | 3 | 9 | 157 |
| Sep | 30 | 53 | 68 | 83 | 95 | 100 | 2 | 8 | 149 |
| Oct | 32 | 51 | 62 | 80 | 95 | 100 | 2 | 7 | 154 |
| Nov | 32 | 57 | 73 | 91 | 100 | 100 | 2 | 5 | 152 |
| Dec | 35 | 55 | 71 | 88 | 98 | 100 | 2 | 6 | 153 |

## 5. Touch messages and signals: the heartbeat between trades

The backtest logs carry no touches, so `touch_replay.py` walks the engine over the 5m candles of 2024-2026 with each live
profile and applies the live window's own rule (`live.py` `announce_poi_touch` + `spent_zone`: a bias-allowed zone of a
traded timeframe that price is inside, during an entry window, not spent, said once per zone) and records the signals
(a confirmed setup before the guard, deduplicated as the backtest runner does). The replay reproduces the backtest's
signal counts (EURUSD 61 signals in both), so the touches are the ones the live window would have sent on these candles
(the live window also sends near-miss and approach notices since 14 October; those are not counted here).

| market | touches | a month | trading days with ≥1 touch | signals (setups before the guard) | a month | days with ≥1 signal | ledger trades | trades per signal | trades per touch |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 281 | 8.5 | 18 % | 61 | 1.8 | 6 % | 47 | 0.77 | 0.17 |
| XAUUSD | 273 | 8.3 | 29 % | 173 | 5.2 | 20 % | 143 | 0.83 | 0.52 |
| NAS100 | 304 | 9.2 | 22 % | 60 | 1.8 | 7 % | 43 | 0.72 | 0.14 |
| BTCUSD | 298 | 9.0 | 19 % | 105 | 3.2 | 12 % | 89 | 0.85 | 0.30 |
| **all** | 1156 | 35.0 | 61 % | 399 | 12.1 | 37 % | 322 | 0.81 | 0.28 |

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 18 | 31 | 39 | 50 | 69 | 88 | 5 | 22 | 714 |
| XAUUSD | 29 | 47 | 61 | 78 | 94 | 100 | 3 | 9 | 714 |
| NAS100 | 22 | 37 | 46 | 59 | 80 | 93 | 4 | 17 | 714 |
| BTCUSD | 19 | 31 | 40 | 54 | 74 | 92 | 4 | 17 | 714 |
| **all** | 61 | 81 | 88 | 96 | 100 | 100 | 1 | 4 | 714 |
| **all, starts in 2026** | 55 | 73 | 84 | 95 | 100 | 100 | 1 | 4 | 191 |

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 6 | 12 | 16 | 24 | 40 | 65 | 15 | 37 | 714 |
| XAUUSD | 20 | 35 | 47 | 63 | 83 | 97 | 4 | 15 | 714 |
| NAS100 | 7 | 14 | 21 | 32 | 51 | 73 | 10 | 47 | 714 |
| BTCUSD | 12 | 20 | 28 | 40 | 63 | 85 | 7 | 28 | 714 |
| **all** | 37 | 57 | 70 | 84 | 96 | 100 | 2 | 7 | 714 |
| **all, starts in 2026** | 37 | 55 | 68 | 84 | 96 | 100 | 2 | 8 | 191 |

| start month | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | start months |
|---|---|---|---|---|---|---|---|---|---|
| Jan | 41 | 62 | 79 | 96 | 100 | 100 | 2 | 5 | 68 |
| Feb | 66 | 92 | 97 | 100 | 100 | 100 | 1 | 2 | 61 |
| Mar | 58 | 75 | 83 | 94 | 100 | 100 | 1 | 5 | 64 |
| Apr | 47 | 68 | 76 | 86 | 100 | 100 | 2 | 6 | 66 |
| May | 77 | 92 | 97 | 100 | 100 | 100 | 1 | 2 | 66 |
| Jun | 62 | 84 | 94 | 100 | 100 | 100 | 1 | 3 | 63 |
| Jul | 58 | 83 | 91 | 96 | 100 | 100 | 1 | 2 | 69 |
| Aug | 59 | 81 | 91 | 97 | 100 | 100 | 1 | 3 | 64 |
| Sep | 74 | 88 | 93 | 100 | 100 | 100 | 1 | 2 | 61 |
| Oct | 76 | 87 | 89 | 93 | 100 | 100 | 1 | 4 | 46 |
| Nov | 76 | 95 | 100 | 100 | 100 | 100 | 1 | 2 | 41 |
| Dec | 42 | 62 | 73 | 91 | 100 | 100 | 2 | 5 | 45 |

| month | touches | signals | ledger trades |
|---|---|---|---|
| 2026-01 | 26 | 9 | 8 |
| 2026-02 | 31 | 13 | 9 |
| 2026-03 | 41 | 17 | 15 |
| 2026-04 | 32 | 6 | 5 |
| 2026-05 | 42 | 13 | 11 |
| 2026-06 | 36 | 18 | 15 |
| 2026-07 | 16 | 5 | 5 |
| 2026-08 | 31 | 13 | 11 |
| 2026-09 | 29 | 8 | 6 |

| market | 1H touches | -> signal on that zone within 24 h | 4H touches | -> signal within 24 h |
|---|---|---|---|---|
| EURUSD | 202 | 15 % | 79 | 6 % |
| XAUUSD | 207 | 45 % | 66 | 15 % |
| NAS100 | 218 | 16 % | 86 | 9 % |
| BTCUSD | 203 | 26 % | 95 | 19 % |

Read: the four windows together send about 35 touch messages a month (8-9 per market), on 61 % of trading days; a
start sees one on its first day 61 % of the time, within two trading days 81 %, within a week 96 %, within two weeks
always (2026 starts: 55 / 73 / 95 / 100 %). Confirmed setups come 12.1 a month on 37 % of trading days; 81 % of them
became ledger trades (the rest: the guard, an expired limit, the R:R or the spread at the fill). About one touch in 2.9
is followed by a signal and one in 3.6 by a trade. The share of touches that confirm within 24 h on that zone says which
message to take seriously: a gold 1H touch 45 %, BTC 1H 26 %, NAS100 1H 16 %, EURUSD 1H 15 %, a 4H touch 6-19 %. In
2026 the months brought 16-42 touches, 5-18 signals and 5-15 trades.

Check of the replay against the ledger runs: every ledger trade's confirmation is among the replay's signals (EURUSD 46
of 47, gold 142 of 143, NAS100 43 of 43, BTC 89 of 89; the two misses are a 15m-close label against the 5m step). A
first replay that took no trades counted 229 / 73 / 154 signals on gold / NAS100 / BTC against the ledger runs' 181 / 60
/ 116, because the runner tells the engine which zone visit it traded (`engine.mark_traded`) and `one_trade_per_visit`
then refuses a second confirmation in that visit; EURUSD (re-entries allowed) matched exactly, 61 = 61. With every
signal marked as traded (`touch_replay2.py`, the tables above) the counts are 173 / 60 / 105: the remaining difference
is the visits whose first signal the guard refused, which the runner leaves open. The touch counts are the same in both
replays (one notice per zone, independent of trades). The code of 14 October differs from the ledgers' 12 October code
only by research knobs that are off by default (`git diff a607b7b7 HEAD -- kronos_trader/strategy`), and the candle
files are the ones the provenance hashes name.

## 6. Days to +10 % and to both phases, by start month (the challenge replay)

`challenge_sim.py` ported unchanged (checked: the same medians, 40 and 84 days, and the same pass rates as the original
run): every weekday start from 2 January 2024 to 30 June 2026, phase 1 = +10 % (at least 4 trading days), phase 2 = +5 %
from the day after. d1 = calendar days from the start to +10 %, d2 = to the end of phase 2. Rows: all starts, by year, by
month of the year (pooled over the years), and by start month.

| starts | n | +10 % within 14 d | 30 d | 60 d | 90 d | median d1 | p90 d1 | both phases within 60 d | 90 d | 120 d | median d2 | p90 d2 | failed (either phase) | unfinished |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 651 | 15 % | 42 % | 62 % | 71 % | 40 | 195 | 38 % | 52 % | 62 % | 84 | 244 | 0 % | 0 % |
| 2024 | 261 | 12 % | 32 % | 54 % | 59 % | 54 | 230 | 30 % | 50 % | 58 % | 91 | 244 | 0 % | 0 % |
| 2025 | 261 | 8 % | 32 % | 51 % | 67 % | 58 | 163 | 16 % | 31 % | 47 % | 131 | 259 | 0 % | 0 % |
| 2026 | 129 | 33 % | 82 % | 100 % | 100 % | 19 | 35 | 97 % | 100 % | 100 % | 34 | 54 | 0 % | 0 % |
| Jan | 67 | 24 % | 58 % | 67 % | 67 % | 26 | 264 | 61 % | 67 % | 67 % | 54 | 278 | 0 % | 0 % |
| Feb | 61 | 13 % | 52 % | 66 % | 66 % | 27 | 229 | 51 % | 52 % | 66 % | 60 | 242 | 0 % | 0 % |
| Mar | 64 | 0 % | 30 % | 61 % | 67 % | 36 | 215 | 30 % | 53 % | 67 % | 88 | 225 | 0 % | 0 % |
| Apr | 66 | 12 % | 33 % | 42 % | 59 % | 70 | 174 | 33 % | 33 % | 33 % | 182 | 288 | 0 % | 2 % |
| May | 66 | 23 % | 47 % | 50 % | 55 % | 62 | 150 | 32 % | 32 % | 32 % | 148 | 256 | 0 % | 0 % |
| Jun | 63 | 22 % | 44 % | 62 % | 78 % | 49 | 114 | 37 % | 38 % | 70 % | 104 | 228 | 0 % | 0 % |
| Jul | 46 | 0 % | 28 % | 54 % | 65 % | 50 | 196 | 0 % | 46 % | 50 % | 136 | 222 | 0 % | 0 % |
| Aug | 43 | 7 % | 16 % | 65 % | 65 % | 46 | 167 | 35 % | 51 % | 51 % | 67 | 194 | 0 % | 0 % |
| Sep | 43 | 26 % | 67 % | 74 % | 74 % | 24 | 124 | 49 % | 49 % | 53 % | 113 | 147 | 0 % | 0 % |
| Oct | 46 | 24 % | 52 % | 52 % | 67 % | 21 | 104 | 46 % | 50 % | 74 % | 90 | 131 | 0 % | 0 % |
| Nov | 41 | 20 % | 20 % | 61 % | 100 % | 57 | 75 | 0 % | 71 % | 100 % | 75 | 102 | 0 % | 0 % |
| Dec | 45 | 2 % | 44 % | 100 % | 100 % | 33 | 46 | 69 % | 100 % | 100 % | 50 | 73 | 0 % | 0 % |
| 2024-01 | 22 | 0 % | 0 % | 0 % | 0 % | 258 | 271 | 0 % | 0 % | 0 % | 272 | 285 | 0 % | 0 % |
| 2024-02 | 21 | 0 % | 0 % | 0 % | 0 % | 223 | 231 | 0 % | 0 % | 0 % | 238 | 245 | 0 % | 0 % |
| 2024-03 | 21 | 0 % | 0 % | 0 % | 0 % | 207 | 223 | 0 % | 0 % | 0 % | 221 | 231 | 0 % | 0 % |
| 2024-04 | 22 | 0 % | 0 % | 0 % | 0 % | 168 | 197 | 0 % | 0 % | 0 % | 182 | 205 | 0 % | 5 % |
| 2024-05 | 23 | 0 % | 0 % | 0 % | 13 % | 131 | 146 | 0 % | 0 % | 0 % | 148 | 157 | 0 % | 0 % |
| 2024-06 | 20 | 0 % | 0 % | 50 % | 100 % | 60 | 70 | 0 % | 0 % | 100 % | 108 | 118 | 0 % | 0 % |
| 2024-07 | 23 | 0 % | 57 % | 100 % | 100 % | 30 | 42 | 0 % | 91 % | 100 % | 77 | 90 | 0 % | 0 % |
| 2024-08 | 22 | 14 % | 27 % | 100 % | 100 % | 38 | 49 | 68 % | 100 % | 100 % | 56 | 63 | 0 % | 0 % |
| 2024-09 | 21 | 48 % | 100 % | 100 % | 100 % | 15 | 27 | 100 % | 100 % | 100 % | 29 | 41 | 0 % | 0 % |
| 2024-10 | 23 | 43 % | 100 % | 100 % | 100 % | 15 | 20 | 91 % | 100 % | 100 % | 26 | 35 | 0 % | 0 % |
| 2024-11 | 21 | 38 % | 38 % | 95 % | 100 % | 51 | 59 | 0 % | 100 % | 100 % | 67 | 71 | 0 % | 0 % |
| 2024-12 | 22 | 5 % | 55 % | 100 % | 100 % | 30 | 42 | 100 % | 100 % | 100 % | 42 | 49 | 0 % | 0 % |
| 2025-01 | 23 | 57 % | 100 % | 100 % | 100 % | 13 | 28 | 83 % | 100 % | 100 % | 36 | 62 | 0 % | 0 % |
| 2025-02 | 20 | 10 % | 60 % | 100 % | 100 % | 26 | 47 | 55 % | 60 % | 100 % | 60 | 110 | 0 % | 0 % |
| 2025-03 | 21 | 0 % | 62 % | 81 % | 100 % | 28 | 71 | 0 % | 57 % | 100 % | 89 | 98 | 0 % | 0 % |
| 2025-04 | 22 | 0 % | 0 % | 27 % | 77 % | 70 | 160 | 0 % | 0 % | 0 % | 280 | 293 | 0 % | 0 % |
| 2025-05 | 22 | 5 % | 45 % | 55 % | 55 % | 48 | 153 | 0 % | 0 % | 0 % | 250 | 261 | 0 % | 0 % |
| 2025-06 | 21 | 14 % | 33 % | 33 % | 33 % | 103 | 218 | 10 % | 10 % | 10 % | 223 | 244 | 0 % | 0 % |
| 2025-07 | 23 | 0 % | 0 % | 9 % | 30 % | 176 | 198 | 0 % | 0 % | 0 % | 203 | 225 | 0 % | 0 % |
| 2025-08 | 21 | 0 % | 5 % | 29 % | 29 % | 159 | 169 | 0 % | 0 % | 0 % | 186 | 196 | 0 % | 0 % |
| 2025-09 | 22 | 5 % | 36 % | 50 % | 50 % | 75 | 133 | 0 % | 0 % | 9 % | 140 | 160 | 0 % | 0 % |
| 2025-10 | 23 | 4 % | 4 % | 4 % | 35 % | 96 | 107 | 0 % | 0 % | 48 % | 123 | 132 | 0 % | 0 % |
| 2025-11 | 20 | 0 % | 0 % | 25 % | 100 % | 66 | 77 | 0 % | 40 % | 100 % | 94 | 104 | 0 % | 0 % |
| 2025-12 | 23 | 0 % | 35 % | 100 % | 100 % | 36 | 49 | 39 % | 100 % | 100 % | 63 | 76 | 0 % | 0 % |
| 2026-01 | 22 | 14 % | 73 % | 100 % | 100 % | 22 | 34 | 100 % | 100 % | 100 % | 46 | 51 | 0 % | 0 % |
| 2026-02 | 20 | 30 % | 100 % | 100 % | 100 % | 20 | 26 | 100 % | 100 % | 100 % | 34 | 42 | 0 % | 0 % |
| 2026-03 | 22 | 0 % | 27 % | 100 % | 100 % | 34 | 43 | 86 % | 100 % | 100 % | 54 | 61 | 0 % | 0 % |
| 2026-04 | 22 | 36 % | 100 % | 100 % | 100 % | 18 | 27 | 100 % | 100 % | 100 % | 29 | 35 | 0 % | 0 % |
| 2026-05 | 21 | 67 % | 100 % | 100 % | 100 % | 13 | 19 | 100 % | 100 % | 100 % | 28 | 31 | 0 % | 0 % |
| 2026-06 | 22 | 50 % | 95 % | 100 % | 100 % | 15 | 21 | 95 % | 100 % | 100 % | 33 | 44 | 0 % | 0 % |

Read: a 14-day pass is 15 % of all starts (33 % of the 2026 starts); +10 % within a month 42 % (2026: 82 %); the base
case over the whole period is a median 40 days to +10 % and 84 to the funded account, with a long tail (90th percentile
195 and 244 days: the starts of January-May 2024 and April-October 2025 waited 4-9 months for +10 %, because the set
first lost and then had to earn the loss back before the target). An October start: 2024 a median 15 days, 2025 a median
96 days. This replay fails no start (flat 0.10R costs); the README's replay with FTMO's measured per-market costs
(`risk_steps.py`) lost 4 % of the 2024-25 starts at 1.5 %, so "0 % failed" here reads as "the flat-cost replay never
hits the limits", not as a guarantee.

With BTC on the New-York-anchored candles (`research/pipeline/btc_ny_BTCUSD.csv`, 94 trades, +33.3R instead of +70.6R)
the pace barely moves: all starts median 42 / 82 days, 2026 starts 21 / 39 days, +10 % within 30 days 40 % (was 42 %):

| starts | n | +10 % within 14 d | 30 d | 60 d | 90 d | median d1 | p90 d1 | both phases within 60 d | 90 d | 120 d | median d2 | p90 d2 | failed (either phase) | unfinished |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 651 | 12 % | 40 % | 61 % | 71 % | 42 | 198 | 36 % | 54 % | 63 % | 82 | 251 | 0 % | 1 % |
| 2024 | 261 | 10 % | 31 % | 53 % | 61 % | 57 | 222 | 27 % | 50 % | 58 % | 91 | 247 | 0 % | 3 % |
| 2025 | 261 | 8 % | 30 % | 49 % | 66 % | 63 | 170 | 18 % | 34 % | 49 % | 125 | 261 | 0 % | 0 % |
| 2026 | 129 | 26 % | 78 % | 100 % | 100 % | 21 | 37 | 91 % | 100 % | 100 % | 39 | 59 | 0 % | 0 % |
| Jan | 67 | 24 % | 58 % | 67 % | 67 % | 26 | 261 | 61 % | 67 % | 67 % | 53 | 276 | 0 % | 0 % |
| Feb | 61 | 11 % | 52 % | 66 % | 66 % | 27 | 216 | 52 % | 59 % | 66 % | 54 | 239 | 0 % | 0 % |
| Mar | 64 | 0 % | 28 % | 64 % | 67 % | 38 | 206 | 28 % | 53 % | 67 % | 88 | 221 | 0 % | 2 % |
| Apr | 66 | 12 % | 33 % | 45 % | 61 % | 64 | 172 | 33 % | 36 % | 36 % | 176 | 308 | 0 % | 9 % |
| May | 66 | 23 % | 47 % | 47 % | 58 % | 76 | 150 | 32 % | 32 % | 32 % | 145 | 261 | 0 % | 0 % |
| Jun | 63 | 8 % | 38 % | 62 % | 78 % | 49 | 214 | 25 % | 38 % | 70 % | 104 | 242 | 0 % | 0 % |
| Jul | 46 | 2 % | 28 % | 50 % | 72 % | 58 | 206 | 0 % | 46 % | 50 % | 136 | 230 | 0 % | 0 % |
| Aug | 43 | 9 % | 14 % | 63 % | 65 % | 50 | 167 | 23 % | 51 % | 51 % | 84 | 188 | 0 % | 0 % |
| Sep | 43 | 26 % | 58 % | 60 % | 60 % | 26 | 135 | 49 % | 49 % | 53 % | 113 | 156 | 0 % | 0 % |
| Oct | 46 | 17 % | 52 % | 52 % | 67 % | 24 | 106 | 46 % | 50 % | 83 % | 91 | 126 | 0 % | 0 % |
| Nov | 41 | 7 % | 20 % | 56 % | 100 % | 58 | 75 | 0 % | 80 % | 100 % | 76 | 96 | 0 % | 0 % |
| Dec | 45 | 2 % | 40 % | 100 % | 100 % | 34 | 47 | 69 % | 100 % | 100 % | 51 | 67 | 0 % | 0 % |
| 2024-01 | 22 | 0 % | 0 % | 0 % | 0 % | 256 | 267 | 0 % | 0 % | 0 % | 272 | 282 | 0 % | 0 % |
| 2024-02 | 21 | 0 % | 0 % | 0 % | 0 % | 191 | 230 | 0 % | 0 % | 0 % | 235 | 245 | 0 % | 0 % |
| 2024-03 | 21 | 0 % | 0 % | 0 % | 0 % | 201 | 211 | 0 % | 0 % | 0 % | 216 | 226 | 0 % | 5 % |
| 2024-04 | 22 | 0 % | 0 % | 0 % | 0 % | 166 | inf | 0 % | 0 % | 0 % | 180 | inf | 0 % | 27 % |
| 2024-05 | 23 | 0 % | 0 % | 0 % | 30 % | 97 | 132 | 0 % | 0 % | 0 % | 145 | 151 | 0 % | 0 % |
| 2024-06 | 20 | 0 % | 0 % | 50 % | 100 % | 60 | 70 | 0 % | 0 % | 100 % | 108 | 118 | 0 % | 0 % |
| 2024-07 | 23 | 4 % | 57 % | 100 % | 100 % | 29 | 42 | 0 % | 91 % | 100 % | 77 | 90 | 0 % | 0 % |
| 2024-08 | 22 | 18 % | 27 % | 95 % | 100 % | 41 | 58 | 45 % | 100 % | 100 % | 61 | 82 | 0 % | 0 % |
| 2024-09 | 21 | 48 % | 100 % | 100 % | 100 % | 15 | 27 | 100 % | 100 % | 100 % | 30 | 42 | 0 % | 0 % |
| 2024-10 | 23 | 30 % | 100 % | 100 % | 100 % | 19 | 23 | 91 % | 100 % | 100 % | 32 | 40 | 0 % | 0 % |
| 2024-11 | 21 | 14 % | 38 % | 86 % | 100 % | 51 | 61 | 0 % | 100 % | 100 % | 70 | 75 | 0 % | 0 % |
| 2024-12 | 22 | 5 % | 45 % | 100 % | 100 % | 32 | 44 | 82 % | 100 % | 100 % | 46 | 62 | 0 % | 0 % |
| 2025-01 | 23 | 57 % | 100 % | 100 % | 100 % | 14 | 28 | 83 % | 100 % | 100 % | 36 | 62 | 0 % | 0 % |
| 2025-02 | 20 | 5 % | 60 % | 100 % | 100 % | 26 | 48 | 60 % | 80 % | 100 % | 50 | 110 | 0 % | 0 % |
| 2025-03 | 21 | 0 % | 62 % | 90 % | 100 % | 28 | 48 | 0 % | 57 % | 100 % | 89 | 96 | 0 % | 0 % |
| 2025-04 | 22 | 0 % | 0 % | 36 % | 82 % | 64 | 159 | 0 % | 9 % | 9 % | 292 | 307 | 0 % | 0 % |
| 2025-05 | 22 | 5 % | 45 % | 45 % | 45 % | 136 | 157 | 0 % | 0 % | 0 % | 258 | 265 | 0 % | 0 % |
| 2025-06 | 21 | 14 % | 33 % | 33 % | 33 % | 209 | 244 | 10 % | 10 % | 10 % | 237 | 256 | 0 % | 0 % |
| 2025-07 | 23 | 0 % | 0 % | 0 % | 43 % | 94 | 210 | 0 % | 0 % | 0 % | 197 | 234 | 0 % | 0 % |
| 2025-08 | 21 | 0 % | 0 % | 29 % | 29 % | 159 | 169 | 0 % | 0 % | 0 % | 180 | 190 | 0 % | 0 % |
| 2025-09 | 22 | 5 % | 18 % | 23 % | 23 % | 124 | 139 | 0 % | 0 % | 9 % | 146 | 160 | 0 % | 0 % |
| 2025-10 | 23 | 4 % | 4 % | 4 % | 35 % | 96 | 111 | 0 % | 0 % | 65 % | 117 | 132 | 0 % | 0 % |
| 2025-11 | 20 | 0 % | 0 % | 25 % | 100 % | 66 | 77 | 0 % | 60 % | 100 % | 88 | 98 | 0 % | 0 % |
| 2025-12 | 23 | 0 % | 35 % | 100 % | 100 % | 36 | 49 | 57 % | 100 % | 100 % | 57 | 70 | 0 % | 0 % |
| 2026-01 | 22 | 14 % | 73 % | 100 % | 100 % | 20 | 34 | 100 % | 100 % | 100 % | 40 | 51 | 0 % | 0 % |
| 2026-02 | 20 | 30 % | 100 % | 100 % | 100 % | 20 | 26 | 100 % | 100 % | 100 % | 36 | 45 | 0 % | 0 % |
| 2026-03 | 22 | 0 % | 23 % | 100 % | 100 % | 35 | 44 | 82 % | 100 % | 100 % | 55 | 61 | 0 % | 0 % |
| 2026-04 | 22 | 36 % | 100 % | 100 % | 100 % | 18 | 26 | 100 % | 100 % | 100 % | 29 | 51 | 0 % | 0 % |
| 2026-05 | 21 | 67 % | 100 % | 100 % | 100 % | 13 | 19 | 100 % | 100 % | 100 % | 28 | 39 | 0 % | 0 % |
| 2026-06 | 22 | 9 % | 77 % | 100 % | 100 % | 24 | 40 | 64 % | 100 % | 100 % | 56 | 67 | 0 % | 0 % |

| start | P(≥1 in 1 td) | 2 td | 3 td | 5 td (a week) | 10 td (two weeks) | 20 td (a month) | median wait (td) | p90 wait (td) | starts |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD (NY) | 12 | 23 | 31 | 45 | 69 | 92 | 6 | 19 | 714 |
| **all four (BTC NY)** | 36 | 57 | 71 | 85 | 97 | 100 | 2 | 6 | 714 |

## 7. The "more trades" sets the README already measured

The README has measured every lever that adds trades ("Frequency" 4 October; "EURUSD: more trades" and "More trades, not
more profit" 7 October; "More EURUSD trades (Max: Dorus kan bij EURUSD echt 3-7 per maand)" and "Academy rules" 13-14
October). The two sets that were run as whole sets:

| Set | Trades a month | R, 2024-2026 | 2017-2023 | Challenge replay (README, FTMO's costs) | First-trade wait (this note) |
|---|---|---|---|---|---|
| The live set (reference) | 9.8 (EURUSD 1.4, gold 4.3, NAS100 1.3, BTC 2.7) | +231.7R raw (EURUSD +38.8, gold +86.1, NAS100 +36.2, BTC +70.6); +0.63R a trade after costs | EURUSD -0.6R, gold -30.9R, NAS100 +30.3R, BTC -28.3R (CURRENT_STATE) | 2026 starts within 2 months 93 %; 2024-25 starts within 3 months 50 %; lost 1 %; worst month -5.0 % | P(≥1 trade in 2 td) 55 %, in a week 83 %; median 2 td, p90 8 |
| A: EURUSD 15m zones (5m entries) at half the stake + BTC until 20:00 ("More trades, not more profit") | 11.3 (EURUSD 1.7 -> 2.4, BTC 2.8 -> 3.6) | EURUSD +31.4R -> +32.9R at its stakes, BTC +64.7R -> +67.2R after costs: the added trades earn next to nothing | EURUSD's 15m zones 2017-2023: 71 trades, 17 % won, -22.8R; BTC until 20:00 not run out of sample | 2026 within 2 months 90 %; 2024-25 within 3 months 46 %; lost 1 %; worst month -5.7 % (each half alone: 93/49/1/-5.7 and 90/54/1/-5.1) | with the 15m EURUSD ledger (`aca/eum15`) in the set: P(≥1 in 2 td) 58 %, a week 84 %, median 2 td, p90 7; EURUSD alone: P(none in two weeks) 63 % -> 54 % |
| B: his rules read literally (`academy`: his bias table, market orders, 9-17, the next liquidity as target) | 15.1 (EURUSD 3.6, "his own 3-7"; gold 4.3, NAS100 4.1, BTC 3.2) | EURUSD 25 % won, -36.3R (-75.0R against the profile); the four together -187.8R against the profiles | not run (negative in sample already) | not run | P(≥1 in 2 td) 67 %, a week 91 %; median 2 td, p90 5; EURUSD alone: median wait 7 td, P(none in two weeks) 35 % |

The single EURUSD levers (README "More EURUSD trades"): two positions 1.4 a month, +44.2R in sample / +8.5R out of sample
(taken 13 October, in the live set above); 15m zones 1.9, +41.6 / -22.8R; no 1H requirement 1.6, +42.4 / -20.4R; both
1.8, +50.0 / -7.3R; no weekly/4H veto 1.7, +34.3R; sessions 9-21 1.7, +32.3R; R:R 0.8 1.5, +28.8R. Only the second
position held in both periods, and it adds 0.2 trades a month. The faster-visible sets (A, B) raise P(a trade in the
first two days) from 55 % to 58 % and 67 %: a few points of visibility for an edge that is gone out of sample (A's EURUSD
half) or gone in sample (B). Both are negative results for the challenge: no faster pass, more losing months.

## 8. What it means, and what to do

1. **Silence in the first two days is the median case, not a fault.** P(no trade in the first 2 trading days) = 45 %
   in sample (49 % out of sample); no trade in the first week 17 %; none in two weeks 5 %. The whole set goes quiet for
   more than two weeks about 2.5 times a year in both periods (longest 19 td in sample, July-August 2025). A window that
   scans, sends its morning check and its touch messages and takes no trade is doing what the backtest did on 65 % of
   its trading days.
2. **The windows the trader watches most are the quietest.** EURUSD takes 1.4 trades a month (36 % of months none),
   NAS100 1.3 (39 % none): the chance of no EURUSD trade in the first two weeks is 63 %, no NAS100 trade 56 %. Gold (4.3 a
   month, a trade on 19 % of trading days, p90 wait 14 td) and BTC (2.7) are where the first trade comes from: the
   first trade after a random start comes from gold 50 % of the time, BTC 23 %, EURUSD 13 %, NAS100 13 % (2026 starts:
   gold 53 %, NAS100 22 %, BTC 15 %, EURUSD 10 %; out of sample gold 64 %).
3. **The heartbeat is the touch message, not the trade.** The four windows send about 35 "👀 waiting for a
   confirmation" messages a month, on 61 % of trading days: 81 % of starts have one within two trading days, 96 % within
   a week, 100 % within two weeks; a confirmed setup follows within two days for 57 % of starts and within a week for
   84 %. Two weeks without a single touch message would be outside everything the backtest did; two weeks without a
   trade is 5 % of starts. The message to watch is a gold 1H touch (45 % confirm within 24 h); an EURUSD or NAS100 1H
   touch confirms 15-16 % of the time, a 4H touch 6-19 %.
4. **"Is it working" cannot be read from the first trades.** With the backtest's edge intact one start in four is under
   water after five trades (two weeks); without an edge (out of sample) one in two. The first ten trades (a month) are
   negative 15 % of the time with the edge and 58 % without: the two are told apart only around 20-30 trades, which is
   what the edge meter in the 22:05 report measures (a warning under 0R over the last 20 or under -5R over the last 30).
   Proposal, the smallest code change (`kronos_trader/live.py`, the FTMO day report): one line "n trading days since the
   last trade (backtest: median 2, 90 % within 8, longest 19), m since the last touch", so the daily message carries the
   reference the trader is comparing against. No profile change.
5. **The pace to expect**: budget three months for +10 % and four for the funded account as the base case (medians 40
   and 84 days over all 2024-2026 starts; 90th percentiles 195 and 244 days); the 2026 starts did it in 19 and 34 days,
   the 2024 and 2025 starts in 54-58 and 91-131. A 14-day pass is 15 % of starts (33 % of the 2026 ones). The October
   starts of 2024 and 2025 took 15 and 96 days to +10 %: the month says nothing, the regime does.
6. **No frequency lever to pull.** Every set with more trades fails out of sample (EURUSD 15m zones -22.8R; his literal
   rules lose in sample) or leaves the wait unchanged (A: 55 % -> 58 % within two days, the challenge no faster). More
   trades with an edge can only come from another market that holds in both periods, and the README found none
   (GER40 +15.1R in sample but 7 % of starts lost with it at full stake). The profiles stay frozen.
7. **BTC's candle anchoring changes the R, not the rhythm**: on the New-York-anchored candles BTC trades 94 times instead
   of 89, the first-trade wait and the challenge pace are the same to within a day or two.
8. **Month of the year: nothing to use.** The in-sample differences (July/December 39-40 % within two days, September/
   October 70-74 %) are two years of noise; out of sample every month sits at 40-59 %.
