# Win-rate runs: the three rules from Dorus's words and the R6 ledger, one at a time

Five runs of 2 October 2026 (06:50-07:54 UTC) on commit `37b6874` (the ledgers' provenance names the working tree of
`2ae5ca8` plus the rules, captured at start), EURUSD 2023-03-01 to 2026-09-25, HistData bid 1-minute candles, 5-minute
steps, 1 % risk, prop-firm halt lifted, one account of 100,000 per run. The base is R6 (`docs/backtests/course/`): the
strict third edition, table exact, entries outside the zone, every opposing gap a shift, the stop on the zone's P. The
rules are documented in `docs/WINRATE_DORUS_vs_CODE.md`.

| Run | Adds | Trades | Win rate | Expectancy | Total | Profit factor | End equity | Deepest drawdown | 2026 only (n / win / sum) |
|---|---|---|---|---|---|---|---|---|---|
| R6 (base) | - | 227 | 35 % | -0.18R | -40.5R | 0.73 | 71,649 | -36.6 % | 36 / 33 % / -6.8R |
| R10 | one trade per zone per visit | 177 | 42 % | -0.08R | -14.9R | 0.86 | 90,082 | -23.4 % | 28 / 39 % / -1.1R |
| R11 | + entry at most half the zone deep | 165 | 44 % | -0.04R | -6.8R | 0.92 | 92,041 | -19.9 % | 26 / 46 % / +5.3R |
| R8 | + R:R cap 2.0, nearest fitting liquidity | 163 | 47 % | -0.05R | -8.5R | 0.90 | 90,894 | -15.4 % | 26 / 46 % / +2.1R |
| R8b | + R:R cap 2.0, farthest fitting liquidity | 164 | 46 % | -0.06R | -10.4R | 0.88 | 89,202 | -17.6 % | 26 / 46 % / +2.1R |
| R9 | R8b + no entries 14:00-15:59 Amsterdam | 158 | 46 % | -0.05R | -7.1R | 0.92 | 91,987 | -16.3 % | 26 / 50 % / +4.3R |

Per year (sum of R): R10 2023 -3.8, 2024 +10.7, 2025 -20.6, 2026 -1.1; R11 -6.7, +9.0, -14.4, +5.3; R8 -6.7, +7.1, -10.9, +2.1;
R8b -6.7, +8.0, -13.8, +2.1; R9 -7.4, +7.9, -12.0, +4.3. (`headline.csv` holds the figures; win rates there count
break-even exits as neither.)

## Reading it

1. **The win rate moves from 35 % to 42-47 %, the expectancy from -0.18R to about -0.05R, and no run is positive over the
   whole period.** The first rule alone (one trade per zone per visit) removes 50 trades and 25.6R of loss; the depth rule
   another 8R; the cap and the hour rule change little. 2024 is positive in every run (+7R to +11R), 2025 negative in
   every run (-11R to -21R), 2026 slightly positive from R11 on (26 trades, 46-50 %, +2R to +5R).
2. **What still loses, in every run:** stops wider than 20 pips (83-90 trades, 41-44 %, -15R to -19R: the zone's P far
   from a 1m entry), longs (-14R to -17R against shorts +2R to +10R), and targets on daily, weekly or monthly liquidity
   (30-35 trades, 2 won). The 1H targets are positive in every run (+4R to +10R); stops of 5-8 pips win 62-67 %.
3. **The cap did not help.** The 22-25 trades whose target was moved to a nearer 5m/15m level lost -4R to -6R together;
   the far targets they replaced lost as well in R11. Reading A-E of `docs/dossiers/SOURCE_TRADES_SUITE.md` says why: his
   target is the previous significant low, which the liquidity map does not hold at his minute.
4. **The suite found the larger gap after these runs started:** his 1H-zone entries are 5m shifts, not the first 1m shift
   (readings C and D), and his stop is the sweep extreme on EURUSD. These runs still enter on the 1m. The ten 2026 runs
   that follow (`run_2026_runs.sh`: V1 at-least, V2 15m-up, V3 5m-up, V4 5m-up with the sweep stop, V5 with the
   previous-low target, on EURUSD and gold) measure that reading; their rows are added below when they finish.

## 2026 and the wider entry timeframes

Ten runs of 2 October (07:54-08:28 UTC, commit `d132dde` + the rules of `37b6874`..`d14948d`), warm-up from 2025-10-01,
reported for 1 January to 25 September 2026 only; the Oct-Dec 2025 warm-up quarter is shown apart. Same data and settings
as above otherwise. The entry-timeframe readings come from the source-trade suite (`docs/dossiers/SOURCE_TRADES_SUITE.md`).

| Run | Market | 2026 trades | Win rate | Sum R | Expectancy | By entry timeframe (n, sum R) | Oct-Dec 2025 warm-up (n, sum R) |
|---|---|---|---|---|---|---|---|
| R8b: three rules, table exact (1m for 1H zones), zone's P stop, cap 2 farthest | EURUSD | 26 | 46 % | +2.1R | +0.08R | 1m 23/+5.1, 5m 3/-3.0 | 9, -4.0R |
| V1: R8b, entries on the table's timeframe up to below the zone's (1H zone: 1m/5m/15m) | EURUSD | 25 | 48 % | +1.6R | +0.06R | 15m 1/+1.7, 1D 1/-1.0, 1H 1/+0.6, 1m 18/+2.7, 5m 4/-2.5 | 9, -4.0R |
| V2: R8b, entries on 15m and up only (1H zone: 15m; 4H: 15m/1H; 1D: 1H/4H) | EURUSD | 9 | 56 % | +3.1R | +0.34R | 15m 6/+4.5, 1D 1/-1.0, 1H 2/-0.4 | 1, -1.0R |
| V3: R8b, table one step up, exact (1H zone: 5m; 4H: 15m; 1D: 1H) | EURUSD | 17 | 59 % | +3.8R | +0.22R | 15m 1/-1.0, 1H 1/-1.0, 5m 15/+5.8 | 2, -2.0R |
| V4: V3 + the sweep-extreme stop | EURUSD | 19 | 53 % | +3.4R | +0.18R | 15m 4/-0.4, 1H 1/-1.0, 5m 14/+4.8 | 4, +0.1R |
| V5: V4 + target on the previous low/high (72 zone candles), no cap | EURUSD | 23 | 48 % | +9.5R | +0.41R | 15m 5/-2.0, 1H 1/-1.0, 5m 17/+12.5 | 4, -4.0R |
| R8b: three rules, table exact (1m for 1H zones), zone's P stop, cap 2 farthest | XAUUSD | 28 | 61 % | +3.8R | +0.13R | 1m 20/+2.8, 5m 8/+0.9 | 17, +0.7R |
| V2: R8b, entries on 15m and up only (1H zone: 15m; 4H: 15m/1H; 1D: 1H/4H) | XAUUSD | 11 | 36 % | -1.6R | -0.15R | 15m 10/-0.6, 1H 1/-1.0 | 4, +2.0R |
| V3: R8b, table one step up, exact (1H zone: 5m; 4H: 15m; 1D: 1H) | XAUUSD | 16 | 56 % | +3.0R | +0.19R | 15m 4/+1.7, 5m 12/+1.4 | 10, +4.4R |
| V5: V4 + target on the previous low/high (72 zone candles), no cap | XAUUSD | 25 | 28 % | +0.9R | +0.04R | 15m 8/-0.4, 5m 17/+1.3 | 14, +8.7R |
| V6 (reading F): V5 + 8-pip minimum stop | EURUSD | 23 | 57 % | +11.2R | +0.49R | 15m 5/-2.0, 1H 1/-1.0, 5m 17/+14.2 | 4, -4.0R |
| V6 (reading F): V5 + 8-pip minimum stop | XAUUSD | 25 | 28 % | +0.9R | +0.04R | 15m 8/-0.4, 5m 17/+1.3 | 14, +8.7R |

V6 (08:29-08:40 UTC, commit `9d3bbf8`): the 8-pip minimum stop turns the four EURUSD stops under 5 pips of V5 (1 won) into
8-pip stops (12 trades of 8-12 pips, 58 %, +9.0R together) and lifts 2026 to 23 trades, 57 %, +11.2R; gold is unchanged
(no stop under 8 points). By month, EURUSD V6: Jan -0.6, Feb no trade, Mar -2.0, Apr +7.6, May -0.4, Jun +1.5, Jul -2.0,
Aug -1.0, Sep +8.1: two months carry the year, five are flat or negative. The reading is the best of the day on EURUSD
and the weakest on gold, where its target window is wrong; that asymmetry is the next thing the fast loop has to settle.

Reading. (1) **Every EURUSD variant is positive in 2026** (+1.6R to +9.5R over nine months), where the 1m reading R8b
lost -6.8R in R6; the trade counts are 9 to 26, so a win rate here moves by 10 points on chance. (2) **The 5m shift
for 1H zones raises the win rate** on EURUSD from 46-48 % (1m readings R8b, V1) to 53-59 % (V3, V4) on 17-19 trades,
and the 5m entries carry the profit (V3: 15 trades +5.8R; V5: 17 trades +12.5R); the 15m-and-up reading V2 trades
least (9) at 56 %. (3) **The previous-low target** (V5) doubles the sum on EURUSD (+9.5R) at a lower win rate (48 %),
and on gold it is the weakest reading (28 %, +0.9R): the 72-candle window reaches too far on gold, as the K3 trades
showed. (4) **Gold** prefers the 1m reading by win rate (R8b 61 %, +3.8R) and the 5m reading by expectancy (V3 +0.19R);
V2 loses. (5) The warm-up quarter (Oct-Dec 2025) is negative on EURUSD in every reading and positive on gold, a
reminder of how much one quarter moves these sums. The V6 reading (V5 + 8-pip minimum stop) runs next.


## Reading F over the whole period

First attempt (08:50-09:30 UTC, packaged as `full_v6_minstop8_*` and kept as the evidence of the blocking trade): on EURUSD the run took 68 trades, 34 %, +2.7R
through June 2025 (2023 +0.9R, 2024 -1.4R, 2025 +3.2R; first 10 % breach from the initial balance on 22 August 2024) and
then nothing: trade P68, a long from a weekly zone (entry 1.15849, stop 1.12103, target 1.23496, 4H confirmation),
opened 16 June 2025 and sat open to the end of the data, blocking every other entry for fifteen months. With the
sweep-extreme stop and the previous-extreme target a weekly zone gives a 375-pip stop and a 765-pip target; neither
fits his weekly trade of 9 Dec 2025 (stop on the weekly P, target the weekly high). On gold the same reading gave 170
trades, 28 %, -28.5R (2023 -19.9R, 2024 -17.7R, 2025 +8.2R, 2026 +0.9R).

So `confirmation.poi_timeframes` now names the zone timeframes traded in full mode, and the demo profile
(`config/dorus_live.yaml`) trades 1D, 4H and 1H zones only. The run of that reading over the whole period (V7,
`wr_full_v7_intraday_*`) follows below.

Second attempt, V7 (09:33-10:14 UTC, commit `5dba5e5`, `full_v7_intraday_*`): reading F with 1D, 4H and 1H zones only,
the demo profile's reading (version 1).

| Market | Trades | Win rate | Expectancy | Total | End equity | Deepest drawdown | First 10 % breach | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 124 | 37 % | +0.10R | +13.0R | 110,869 | -17.7 % (25 Sep 2024) | 4 Jul 2024 | 22 / 27 % / -3.4R | 38 / 29 % / -1.4R | 41 / 39 % / +6.6R | 23 / 57 % / +11.2R |
| XAUUSD | 172 | 27 % | -0.17R | -28.5R | 74,254 | -34.5 % (3 Oct 2025) | 17 Aug 2023 | 37 / 19 % / -19.9R | 53 / 28 % / -17.7R | 57 / 32 % / +8.2R | 25 / 28 % / +0.9R |

On EURUSD the 1H zones with 5m entries carry it (90 trades, 41 %, +15.1R); the 4H zones with 15m entries lose (30 trades,
23 %, -1.7R); shorts +17.5R, longs -4.5R. So the reading is positive over the whole period, but 2023 and 2024 are
negative, the account would have breached FTMO's 10 % line in July 2024 and sat 17.7 % under its peak in September 2024,
and the profit is 2025-2026 (+17.8R over 21 months). Gold is not tradable with this reading.


Files per run: `<run>.csv` (ledger), `.equity_1H.csv`, `.equity.csv.gz`, `.provenance.json`, `.run.txt`, `<run>_equity.png`;
`equity_all.png`, `headline.csv`.
