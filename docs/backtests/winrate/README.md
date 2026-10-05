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


## Profile version 2 (the origin target)

`config/dorus_live.yaml` version 2 (commit `6908860`): reading F with `tp_policy impulse_origin` (the low/high the zone's
creating move started from, 30 zone candles up to the P) instead of the 72-candle previous extreme, 1D/4H/1H zones.
Runs of 10:03-10:18 UTC (`v2_y26_*`, warm-up from 2025-10-01; `v2_jul/aug/sep_eurusd`, the review months).

| Market | 2026 trades | Win rate | Sum R | Expectancy | By zone timeframe (n / win / sum) | By month (sum R) | Version 1 (reading F) for comparison |
|---|---|---|---|---|---|---|---|
| EURUSD | 16 | 62 % | +5.2R | +0.32R | 1H 9 / 67 % / +3.9R; 4H 6 / 67 % / +2.3R; 1D 1 / 0 % / -1.0R | Jan +0.9, Mar -1.0, Apr +3.2, May +0.9, Jun +0.7, Jul -2.0, Aug -1.0, Sep +3.5 | 23 / 57 % / +11.2R |
| XAUUSD | 22 | 45 % | +11.3R | +0.51R | 1H 15 / 47 % / +7.8R; 4H 7 / 43 % / +3.5R | Jan +1.5, Feb +2.1, Mar +3.4, Apr +0.9, Jun +4.4, Aug +1.4, Sep -2.4 | 25 / 28 % / +0.9R |

The review months with version 2 on EURUSD: July 2 trades -2.0R, August 1 trade -1.0R, September 3 trades 3 won +3.5R
(version 1: -2.0R, -1.0R, +8.1R).

Reading. The origin target makes gold tradable in 2026 (+11.3R at 45 %, from +0.9R at 28 %: the 72-candle window had
reached lows from days before) and smooths EURUSD (five positive months of eight, no month under -2R) at a smaller sum:
nearer targets, and the 4H zones now take the September entries with wider stops than the 1H zones of version 1. Over
both markets version 2 gives +16.5R in 2026 against +12.1R for version 1, on 38 trades. Its whole-period run follows.

Whole period with the profile as it is (`full_v2_*`, 10:19-11:01 UTC, FTMO margins in the guard: halt at 8 % from the peak
or 4 % in a day): EURUSD 24 trades, 25 %, -9.4R, halted in May 2024 at -8.8 % from the peak and never traded again (200 of
224 signals refused by the guard); gold 21 trades, 43 %, -2.9R, halted in August 2023. So with the account rules of the
demo, version 2 would have lost a challenge in 2024 (EURUSD) and 2023 (gold), as version 1 did in July 2024. The run with
the halt lifted (`full_v2ng_*`), the one comparable with V7, follows.

Whole period with the halt lifted (`full_v2ng_*`, 11:02-11:43 UTC), against version 1 (reading F, `full_v7_intraday_*`):

| Profile | Market | Trades | Win rate | Total | End equity | Deepest drawdown | First 10 % breach | 2023 | 2024 | 2025 | 2026 | 1H zones | 4H zones |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Version 1 | EURUSD | 124 | 37 % | +13.0R | 110,869 | -17.7 % (Sep 2024) | 4 Jul 2024 | -3.4R | -1.4R | +6.6R | +11.2R | 90 / 41 % / +15.1R | 30 / 23 % / -1.7R |
| Version 2 | EURUSD | 110 | 44 % | +2.3R | 101,505 | -14.0 % (Oct 2024) | 5 Jul 2024 | -1.7R | -8.9R | +7.8R | +5.2R | 69 / 48 % / +11.4R | 36 / 39 % / -5.8R |
| Version 1 | XAUUSD | 172 | 27 % | -28.5R | 74,254 | -34.5 % (Oct 2025) | 17 Aug 2023 | -19.9R | -17.7R | +8.2R | +0.9R | 118 / 24 % / -21.5R | 50 / 36 % / -5.1R |
| Version 2 | XAUUSD | 158 | 39 % | +7.8R | 106,060 | -25.8 % (Oct 2024) | 3 Jan 2024 | -8.7R | -7.7R | +12.9R | +11.3R | 111 / 40 % / +11.2R | 43 / 37 % / -3.3R |

Reading. (1) Both versions, both markets: 2023 and 2024 lose, 2025 and 2026 earn. The entry mechanics are now his; what
decides the year is the bias gate, which has never been checked against his own readings. (2) Version 2 is the better
profile over both markets together (+10.1R against -15.5R), with higher win rates (44 %, 39 %) and smaller drawdowns;
on EURUSD alone version 1 earns more (+13.0R against +2.3R) through 2026's far targets. (3) The 4H zones lose in all
four runs (-1.7R to -5.8R); the 1H zones carry every positive result. Restricted to 1H zones, 2024 still loses in every
run (-4.5R to -8.7R), so the zone choice does not replace the bias work. (4) An FTMO account breaches 10 % in July 2024
on EURUSD under both versions, and in 2023-2024 on gold.

## Profile version 3 (the gate: the 1H must be aligned, no W+D+4H combination)

The whole-period version-2 ledgers with the bias each trade was taken under (`full_v2b_*`, 11:48-12:29 UTC) showed two
cuts that win on both markets: trades where the 1H is among the aligned timeframes (EURUSD 65 trades +6.8R against 45
trades -4.5R without; gold 77 trades +14.8R against 81 trades -7.0R) and trades not taken on the W+D+4H combination (that
combination: EURUSD 35 trades -3.0R, gold 21 trades -10.1R; the combinations with the monthly: EURUSD +8.1R, gold
+11.4R). Max's suggestion to drop the monthly reads the other way round in this data. Version 3 (`bias.required_aligned:
[1H]`, `full_combos` without W+D+4H, scalp combination kept) ran 12:31-13:09 UTC (`v3_y26_*`, `v3_full_*`):

| Profile | Market | Period | Trades | Win rate | Total | End equity | Deepest drawdown | First 10 % breach | Per year |
|---|---|---|---|---|---|---|---|---|---|
| Version 3 | EURUSD | 2026 (warm-up from Oct 2025) | 10 | 70 % | +5.9R | - | - | - | Jan +1.2, Mar -1.0, Apr +2.6, May +1.0, Jun +0.7, Jul -1.0, Aug -1.0, Sep +3.5 |
| Version 3 | XAUUSD | 2026 | 14 | 50 % | +8.9R | - | - | - | Jan +1.0, Feb -2.0, Mar +4.4, Jun +4.4, Aug +1.4, Sep -0.4 |
| Version 3 | EURUSD | 2023-03 to 2026-09 | 73 | 49 % | +11.8R | 111,032 | -9.8 % (Oct 2024) | never | -0.6R / -6.1R / +12.5R / +5.9R |
| Version 2 | EURUSD | 2023-03 to 2026-09 | 110 | 44 % | +2.3R | 101,505 | -14.0 % | 5 Jul 2024 | -1.7R / -8.9R / +7.8R / +5.2R |
| Version 3 | XAUUSD | 2023-03 to 2026-09 | 84 | 38 % | +7.8R | 106,597 | -17.9 % (Sep 2024) | 2 May 2024 | -3.6R / -1.3R / +3.8R / +8.9R |
| Version 2 | XAUUSD | 2023-03 to 2026-09 | 158 | 39 % | +7.8R | 106,060 | -25.8 % | 3 Jan 2024 | -8.7R / -7.7R / +12.9R / +11.3R |

Reading. On EURUSD version 3 is the first reading that never breaches 10 % over the whole period (deepest drawdown 9.8 %)
and wins 49 % of 73 trades; 2024 still loses (-6.1R). On gold the sum is unchanged at fewer trades and the drawdown
shrinks from 25.8 % to 17.9 %; the 10 % line is still crossed in May 2024. Inside version 3 the full-mode trades (the
monthly aligned) carry EURUSD (24 trades, 62 %, +13.3R) while the scalp combination D+4H+1H loses slightly (49 trades,
43 %, -1.5R) and is flat on gold (+0.5R); it stays because it is his rule. Both cuts are read from the same ledgers they
improve, so the demo decides.

Files per run: `<run>.csv` (ledger), `.equity_1H.csv`, `.equity.csv.gz`, `.provenance.json`, `.run.txt`, `<run>_equity.png`;
`equity_all.png`, `headline.csv`.

## Frequency: more trades without lower quality (4 October 2026)

Max, 4 October: the challenge pace is too slow (+0.7R a month on EURUSD in 2026; +10 % at 1 % risk takes 14 months), "kunnen
we het verhogen, bijv. 10 trades per maand?", and the markets he wants are EURUSD, gold and BTC. Everything below is the
live profile (`config/dorus_live.yaml`, version 3) with one line changed per run, 2026 = 1 January to 25 September
(HistData), BTC to 4 October (Bitstamp). Ledgers: `<tag>.csv` with `.run.txt` and `.provenance.json` in this folder.

Where the signals die in 2026 (EURUSD, `out_base_y26.run.txt`): most scans have fewer than three timeframes aligned
because the monthly and the weekly read 50/50 (an old unmitigated gap outvotes a fresh break, see the 1W and 1M notes of
every dossier in `docs/practice/2026-09/EURUSD/v3`); then "no active visit"; then 18 zones refused as a second or third
visit, 7 zones for R:R under 0.5, 2 signals for the open position.

### EURUSD, one knob at a time

| Variant (EURUSD) | 2026 trades | Win | Sum R | Max dd | 2023-2026 (guard off) | Verdict |
|---|---|---|---|---|---|---|
| Live profile | 10 | 70 % | +5.9R | -2.0R | 73 trades, 49 %, +11.8R, dd -11.3R | the reference |
| Two open trades (`prop_firm.max_open_trades 2`, `lev_open2_y26`, `ng_open2_full`) | 11 | 73 % | +7.1R | -2.0R | 87 trades, 46 %, +10.3R, dd -15.3R (2024 -8.4R) | the 14 September 08:45 setup in 2026, but worse over the whole period; not taken (the demo runs one process per market with one open trade each) |
| Sessions 08-18 (`lev_sess0818_y26`, `ng_sess0818_full`) | 19 | 58 % | +6.7R | -3.0R | 103 trades, 46 %, +0.9R, dd -9.8R | twice the trades, the edge gone over the whole period; GBPUSD 2026 16 trades, +2.0R (from +3.1R); not taken |
| Second visits traded (`allow_retest`) | 10 | 70 % | +5.9R | -2.0R | - | no change: the refused visits never confirmed |
| News filter off | 10 | 70 % | +5.9R | -2.0R | - | no change in 2026 |
| Entry at most 20 pips outside the zone (`out_p20_y26`) | 9 | 67 % | +5.6R | -2.0R | - | the far entries (39, 23 pips) won; 25 % of the height: 6 trades +4.3R; 10 pips: 6, +3.4R |
| Bias conflict rule "recent" (`rec_eu_y26`) | 30 | 40 % | -3.8R | -5.0R | - | more M+W+D swings, the scalps -7.5R; rejected |

2023-2026 with the guard off (the halting limits at 1000 %, as in the version-3 runs above): the live profile 73 trades,
49 %, +11.8R, dd -11.3R.

### A second market: GBPUSD on the same profile

| GBPUSD | Trades | Win | Sum R | Max dd | By year |
|---|---|---|---|---|---|
| 2026 (`gbp_base_y26`) | 11 | 55 % | +3.1R | -2.0R | - |
| 2023-03 to 2026-09 (`gbp_base_full`, guard at the live margins, never halted) | 62 | 50 % | +8.2R | -5.4R | 2023 +0.1, 2024 -1.2, 2025 +6.2, 2026 +3.1 |
| 2026, bias conflict rule "recent" (`rec_gb_y26`) | 43 | 42 % | +3.1R | -8.0R | four times the trades, the same sum, four times the drawdown |

EURUSD and GBPUSD together in 2026: 21 trades, 62 %, +9.0R, max dd -3.0R, no overlapping open trades, one same-day entry,
worst day -1.0R; by month Jan +2.2, Feb +0.9, Mar -1.1, Apr +1.6, May +1.0, Jun +1.9, Jul +0.3, Aug -0.3, Sep +2.5. Over
2023-2026 the pair gives 135 trades, +20.0R, max dd -15.1R (2024 -7.3R for the two together).

### BTC on the same profile (Bitstamp BTC/USD, 5m from 20 December 2025, 1H from 2023, 4H from 2019, 1D from 2015)

The stop minimum is scaled to price: 8 pips on EURUSD is 0.07 % of price, 0.07 % of BTC at 85,000 is 60 USD.

| BTC 2026 | Trades | Win | Sum R | Without the top 2 | Max dd | Note |
|---|---|---|---|---|---|---|
| Live profile, stop minimum 60 USD (`btc_base_y26`) | 25 | 40 % | +15.8R | -3.3R | -3.0R | 2 June short 69818 -> 65696 +11.8R, 2 October long +7.4R |
| 1H not required in the bias (`btc_noreq_y26`) | 31 | 45 % | +26.6R | +7.4R | -5.4R | the ten added trades +9.5R, M+W+D swings; in `config/dorus_live_btc.yaml` |
| Sessions off, 24/7 (`btc_allday_y26`) | 15 | 33 % | -0.7R | -6.7R | -4.2R | 8.3 % drawdown by February halted the run: night and weekend setups lose |
| Two open trades | 27 | 33 % | +11.0R | -8.2R | -5.3R | the added trades -4.8R |
| 15m zones with 1m entries | 26 | 38 % | +14.9R | -4.3R | -4.0R | one added trade, a loser |
| Bias conflict rule "recent" | 46 | 37 % | +2.8R | - | -6.5R | rejected |
| Target capped at 3R | 25 | 40 % | +15.8R | -3.3R | -3.0R | no change: `tp_max_rr` only caps the liquidity target, not the origin target |

BTC pays through a few far targets (planned R:R 8-17 on the origin rule) at a 40 % win rate, the opposite shape of the
EURUSD profile; the sum is strong, the month-to-month swing wide (June +11.7R / +22.2R, August -1.4R / -4.4R).

### September 2026 as a challenge month on the four markets Max watches

EURUSD, gold, BTC and the dollar index, the live profile (BTC without the 1H requirement), 100k, each market its own
process. DXY (`dxy_sep`): Yahoo 5m/15m/1H bars from 26 July, the committed TradingView daily/weekly/monthly
(`data/dxy`), a 0.01 pip; four trades, one won (+0.6R), three longs stopped on 2, 18 and 21 September while the EURUSD
shorts of the same dollar view won. Together 12 trades, -0.3R: EURUSD +3.5R, gold -0.4R, BTC -1.0R, DXY -2.4R. At 1 %
risk -0.3 %, max dd -2.5 %, worst day -1.0 %; at 2 % -0.8 %, dd -4.9 %, worst day -2.0 %. No rule broken, nothing
earned. DXY stays the bias mirror for EURUSD (`bias.mirror_symbol`), not a market.

2026 month by month on EURUSD + gold + BTC (R, closed trades): Jan +1.2, Feb -0.6, Mar +4.2, Apr +4.8, May 0.0,
Jun +27.3 (BTC +22.2 in one trade), Jul -1.0, Aug -4.0, Sep +2.1, Oct +7.4. Compounded at 1 % of equity per trade:
+10 % on 3 June, +48.7 % by the end of September, max dd -7.7 %, worst day -2.8 %, inside FTMO's 5 % / 10 %. At 1.5 %:
max dd -11.4 % and a -5.0 % day in August, the challenge lost. So 1 % per trade, three markets, and months, not weeks.

### What goes into the demo and what does not

- Per market one process with at most one open trade (EURUSD, GBPUSD on the live profile; BTC on
  `config/dorus_live_btc.yaml`: stop minimum 60 USD, no 1H requirement). The guard reads the account's equity in every
  process, so the FTMO margins hold account-wide.
- Not taken: wider sessions, retests, the "recent" bias rule, an entry cap, 15m zones, BTC around the clock, a target cap.
- The pace in 2026 for the three markets together, 1 % risk: about +3R a month (EURUSD +7.1R, GBPUSD +3.1R,
  BTC +26.6R over nine months); without BTC's two best trades about +1.4R a month. At 1 % that is +10 % in 3 to 7 months,
  at 2 % in 2 to 4 months with a deepest 2026 dip of about -8 % on the three together; 1.5 % keeps the dip near -6 %.
- The open lever is the week and month bias: every mechanical rule tried reads them more often but worse. It needs
  Max's own readings on dated days (`docs/dossiers/source_bias.yaml`).

## BTC and gold over the years, the intraday bias, Dorus's BTC target (4 October 2026, evening)

Max, 4 October: "ga echt veel meer kijken naar btc", "en doe ook goud", "we hoeven niet op maanden te traden, het kan op
1 uur en 4 uur". The afternoon's 2026 findings were run over the years they can be run over: BTC February 2024 to
October 2026 (Bitstamp 5m back to January 2024), gold and EURUSD March 2023 to September 2026. Guard off in every
run here (halting limits 1000 %); "at 1 %" compounds 1 % of equity per trade. Ledgers `<tag>.csv` in this folder.

### The intraday bias (two of 1D/4H/1H, or 4H+1H alone; the 1H always required)

| Market, 2023-2026 (BTC 2024-2026) | Book's gate (live profile) | Two of 1D/4H/1H | 4H+1H alone |
|---|---|---|---|
| EURUSD | 73 trades, 49 %, +11.8R, dd -11.3R | 2026 only: 37, 41 %, +4.6R | 149 trades, 38 %, -7.3R, dd -21.7R (`intra_a_eu_full`); 2026 alone 27, 48 %, +11.4R |
| GBPUSD | 62, 50 %, +8.2R | 2026: 46, 33 %, -8.9R | 2026: 33, 36 %, -8.0R |
| Gold | 84, 38 %, +7.8R, dd -19.8R, through 10 % static in May 2024 | **163, 44 %, +27.6R, dd -12.9R, 2023 +3.5 / 2024 +7.7 / 2025 +6.1 / 2026 +10.3, never 10 % under the start** (`gold_intra_c_full`) | 2026 not run |
| BTC | 92, 45 %, +30.8R (`btc_base_long`) | 2026: 69, 41 %, +23.6R, dd -10.8R | 2026: 62, 44 %, +29.0R, dd -7.4R |

The same gate that loses on the currency pairs is gold's best reading by far: more trades, a higher win rate, every
year positive. It goes into `config/dorus_live_gold.yaml`. EURUSD and GBPUSD keep the book's gate; 2026 was their
exception, not their rule. Gold without the 1H requirement (`gold_noreq_full`): 143 trades, +11.9R, dd -25.9R, no.

### BTC over 2024-2026

| BTC, Feb 2024 - Oct 2026 | Trades | Win | Sum R | Without top 3 | Max dd | 2024 / 2025 / 2026 | At 1 % |
|---|---|---|---|---|---|---|---|
| Live profile, 1H required, stop minimum 60 USD (`btc_base_long`) | 92 | 45 % | +30.8R | +7.3R | -9.4R | +22.0 / -6.1 / +14.9 | +33 % |
| No 1H requirement, the demo profile (`btc_noreq_long`) | 128 | 48 % | +40.6R | +16.2R | -9.1R | +19.9 / -4.9 / +25.6 | +44 % |
| **Previous-high target (`btc_prevext_long`), the BTC profile from 5 October** | 133 | 35 % | **+55.0R** | +15.8R | -10.3R | +12.5 / -2.8 / +45.2 | +65 %, peak dd -9.9 %, longest losing run 8 |
| Previous-high target + W+D+4H (`btc_prevext_wd4h_long`) | 155 | 33 % | +51.2R | +11.9R | -13.8R | +10.7 / -7.7 / +48.1 | +58 %, peak dd -13.2 % |

BTC 2026 variants, all on the demo profile unless named (the morning's rows are in "Frequency" above): the New York
session 13-22 (`btc_sess_ny_y26`) 33 trades -3.5R, no; two open trades 27, +11.0R, no; 15m zones with 1m entries 26,
+14.9R, no; the plan's W+D+4H combination back in (`btc_wd4h_y26`) 38, 45 %, +26.2R, neutral; the target at the
previous high/low instead of the origin (`btc_prevext_y26`, Astra: in his BTC recap he targets the liquidity above
earlier highs) 34, 35 %, +45.2R, without the top 2 +13.4R, dd -5.0R, median planned R:R 4.0; previous high/low with
W+D+4H (`btc_prevext_wd4h_y26`) 41, 37 %, +48.1R, without the top 2 +16.3R, dd -5.0R. The two bias readings that would
let the 14-16 September long through (`docs/dossiers/BTCUSD_2026-09-14`): conflict rule "recent" 97 trades, 27 %,
+39.8R but +0.6R without the top 3 and runs of 8 losers, no; a broken P read as 50/50 (`btc_pw_noflip_y26`) 34, 38 %,
+46.1R, the same trades as the target profile, and neither takes his long. His read of that sweep is still open.

### Gold 2026 variants (on the live profile)

New York session 13-22: 18 trades, 50 %, +9.7R (`gold_sess_ny_y26`), a little better than the book's windows, not
taken for one year. Previous-high target: 16, 31 %, +2.0R (`gold_prevext_y26`): on gold the origin target is the right
one, on BTC the previous high. Stop minimum 2.6 USD: identical to the profile, the minimum never binds. No 1H
requirement: 22, 45 %, +11.3R in 2026 but -25.9R drawdown over the years.

### What the demo runs from 5 October

EURUSD on `config/dorus_live.yaml` (the book), XAUUSD on `config/dorus_live_gold.yaml` (two of 1D/4H/1H), BTCUSD on
`config/dorus_live_btc.yaml` (no 1H requirement, stop minimum 60 USD, the previous-high target: +55.0R over 2024-2026 against
+40.6R for the origin target, at a 35 % win rate and runs of 8 losers). One process per market, one open trade each, 1 % per trade, the FTMO margins
account-wide. 2026 on the three together at 1 %: EURUSD +5.9R, gold +10.3R, BTC +26.6R (origin) or +48.1R
(previous high); the pace of a challenge is set by BTC's few far targets and by gold's steady 4 trades a month.

## Loss anatomy: what the losers did before the stop, and what separates them (4 October 2026, night)

Max: "winrate moet wel wat omhoog ... analyseer de trades en zie of er wat mist of fout gaat". `scripts/loss_anatomy.py`
takes a ledger and the 5m bars and adds to every trade its maximum favourable and adverse excursion in R (MFE, MAE),
then cuts the ledger by zone timeframe, bias combination, hour, weekday, planned R:R, zone age and the wait between the
touch and the shift. Outputs in `anatomy/` for the three demo profiles over the years: `v3_full_eurusd` (EURUSD, the
book), `gold_intra_c_full` (gold, two of 1D/4H/1H), `btc_prevext_long` (BTC, previous-high target).

| | EURUSD 2023-2026 | Gold 2023-2026 | BTC 2024-2026 |
|---|---|---|---|
| Trades, win, sum | 73, 49 %, +11.8R | 163, 44 %, +27.6R | 133, 35 %, +55.0R |
| Losers that never went 0.25R in profit | 44 % | 33 % | 36 % |
| Losers that saw +1R before the stop | 14 % | 16 % | 32 % |
| Winners' median adverse excursion | 0.38R (33 % went past 0.5R) | 0.31R | 0.39R |
| Stop size, losers vs winners (median) | 11.6 vs 16.5 pips | 5.7 vs 7.1 USD | 482 vs 402 USD |
| Zones under 24 h old: trades, win, sum | 54, 48 %, +10.1R | 126, 45 %, +25.5R | 89, 43 %, +72.0R |
| Zones 1-3 days old | 6, 33 %, -2.7R | 18, 28 %, -4.7R | 22, 23 %, -7.8R |
| Zones older than 3 days | 13, 54 %, +4.3R (the swing zones) | 19, 47 %, +6.8R | 22, 9 %, -9.2R |
| Bias combination, best / worst | M+W+D 19, 63 %, +11.5R / D+4H+1H (scalps) 49, 43 %, -1.5R | 4H+1H 70, 51 %, +25.3R / 1D+1H 44, 36 %, -6.0R | M+W+D 73, 30 %, +41.3R / D+4H+1H 39, 41 %, +9.6R |
| Direction | shorts 29, 59 %, +11.2R; longs 44, 43 %, +0.6R | longs 113, 47 %, +36.2R; shorts 50, 38 %, -8.6R | shorts 48, 33 %, +39.6R; longs 85, 35 %, +15.4R |
| Hour (Amsterdam), worst | 09:00: 21, 38 %, -3.9R | 10:00: 28, 32 %, -0.7R | 16:00: 14, 14 %, -8.9R |
| Weekday, worst | Thursday 21, 38 %, -5.4R | Monday 37, 32 %, -8.9R | Wednesday 30, 23 %, -8.8R |
| Wait touch -> shift, worst | 4-12 h: 11, 18 %, -3.0R | 4-12 h: 38, 37 %, -1.2R | 12-48 h: 29, 24 %, -10.3R |
| Break-even at +1R, losers that saw it to zero (optimistic) | +16.8R | +41.6R | +82.0R |

What it says:

- **Half of the losers are bad entries, not bad management**: 33-44 % never go a quarter R in profit, and only 14-16 % on
  the currency pair and gold ever see +1R. Tighter management does little there; on BTC a third of the losers see +1R
  first, so a break-even at +1R is worth a run (`btc_pe_be1_y26`, below).
- **Stale zones lose on all three markets.** Under a day old 43-48 %; one to three days old 23-33 %; on BTC anything
  older than a day is -17R on 44 trades. The course says a zone that price has "volledig gebruikt" is spent
  (A 00:33:37-00:33:56) and prefers the level the higher timeframe also balanced (A 02:05:53); the age limit is the
  data's proxy for freshness. `confirmation.max_zone_age_candles 24` is running over the years on all three.
- **On EURUSD the scalps lose and the swings win**: the 49 D+4H+1H trades 43 % for -1.5R, the 24 full-combination trades
  62 % for +13.3R. `bias.scalp_enabled false` is running (`eu_noscalp_full`). Fewer trades, the win rate Dorus names.
- **On gold the 1D+1H pair loses** (44 trades, 36 %, -6.0R) while 4H+1H carries the profile (70, 51 %, +25.3R):
  `gold_no1d1h_full` drops it. Gold shorts against the bullish monthly lose (50, 38 %, -8.6R): `bias.no_trade_against
  [1M]` is running on gold and EURUSD (`gold_against1m_full`, `eu_against1m_full`).
- **The first hour on EURUSD** (09:00-10:00 Amsterdam: 21 trades, 38 %, -3.9R) is the worst hour; `eu_sess10_full`
  starts at 10:00. On BTC the last hour (16:00) is the worst; on gold 10:00.
- **Stops**: EURUSD and gold losers have the tighter stops (11.6 vs 16.5 pips; 5.7 vs 7.1 USD), BTC the wider. A larger
  stop minimum on EURUSD (12 pips) is a reading to run after these.
- The weekday and wait-time cuts differ per market and are left as observations.

### The win-rate levers over the years (5 October 2026)

Guard off, compounded at 1 % per trade; the profile row is each market's demo profile.

| Market | Run | Trades | Win | Sum R | Max dd | Per year | At 1 % |
|---|---|---|---|---|---|---|---|
| EURUSD 2023-2026 | profile, the book (`v3_full_eurusd`) | 73 | 49 % | +11.8R | -11.3R | -0.6 / -6.1 / +12.5 / +5.9 | +11.7k |
| | target capped at 2R (`eu_cap2_full`) | 73 | 52 % | +5.1R | -11.3R | -4.0 / -4.5 / +7.7 / +5.9 | +4.8k |
| | stop at least half the zone's height (`eu_stopzone_full`) | 71 | 52 % | +12.7R | -10.3R | +0.5 / -4.0 / +12.0 / +4.2 | +12.8k, never 10 % under the start |
| | stop minimum 12 pips (`eu_stop12_full`) | 72 | 50 % | +7.7R | -11.4R | -2.1 / -6.9 / +11.9 / +4.8 | +7.4k |
| Gold 2023-2026 | profile, two of 1D/4H/1H (`gold_intra_c_full`) | 163 | 44 % | +27.6R | -12.9R | +3.5 / +7.7 / +6.1 / +10.3 | +29.0k |
| | target capped at 2R (`gold_cap2_full`) | 165 | 50 % | +15.5R | -11.7R | +0.1 / -0.9 / +1.6 / +14.6 | +15.2k |
| | stop at least half the zone's height (`gold_stopzone_full`) | 152 | 49 % | +25.3R | -12.3R | +4.9 / +4.5 / +2.0 / +13.9 | +26.7k |
| BTC 2024-2026 | profile, previous-high target (`btc_prevext_long`) | 133 | 35 % | +55.0R | -10.3R | +12.5 / -2.8 / +45.2 | +64.6k |
| | **target capped at 2R (`btc_cap2_long`)** | **145** | **51 %** | **+62.3R** | **-10.1R** | +9.5 / -0.1 / +52.9 | **+77.7k** |
| | stop at least half the zone's height (`btc_stopzone_long`) | 125 | 40 % | +15.0R | -14.2R | +6.6 / +2.3 / +6.2 | +14.5k |

2026 only (no full-period run, the break-even rule changes nothing material): break-even at +1R on BTC 34 trades, 35 % won
and 15 % at zero, +49.2R (`btc_pe_be1_y26`); on gold 46 %, +8.2R (`gold_g_be1_y26`); on EURUSD no change (`eu_be1_y26`).

Reading: the 2R cap takes the nearest liquidity when the previous-high target lies beyond 2R and keeps the far target
when nothing nearer fits, so BTC keeps its few far winners and wins half its trades: 35 % to 51 % with more R and a
smaller drawdown, in every year but 2024. On the currency pair and gold the same cap raises the win rate and costs
R: their profit is in the far targets. The stop of at least half the zone's height is a small gain on EURUSD only
(the anatomy's "tight stops lose"), within noise on gold, and costs BTC most of its edge.

### Dorus on "slechte marktcondities" and the higher-timeframe veto

Course A 01:58:09-01:59:24: "zelfs met perfecte levels en met een perfecte strategie zijn er bepaalde condities waar je
gewoon niet in wil traden ... als jij tegen je higher timeframe bias gaat traden ... Als de higher timeframe voor mij
tegenzit, dan ga ik überhaupt niet een trade plaatsen ... als de higher timeframe zegt we zijn bullish, dan kijk ik voor
longs." Then trading between POIs (waiting) and news (A 01:59:28-02:00:08). And A 01:23:25: "nooit een trade plaatsen
die niet klopt met de bias ... dan is het voor mij überhaupt al geen A+ set-up." The code lets a scalp (D+4H+1H) and the
gold profile's two-of-three gate through while the monthly or the weekly reads the other way. `bias.no_trade_against`
is that rule. Estimated on the profile ledgers before any run (trades whose bias string shows the timeframe against):

| Ledger | 1M against: vetoed | 1W against: vetoed | 1M or 1W against: vetoed | kept with 1M or 1W veto |
|---|---|---|---|---|
| EURUSD 2023-2026 | 14, 71 %, +8.4R | 15, 27 %, -9.3R | 26, 46 %, -1.2R | 47, 51 %, +13.0R (1W only: 58, 55 %, +21.1R) |
| Gold 2023-2026 | 23, 35 %, -2.3R | 19, 37 %, -2.7R | 36, 36 %, -4.8R | 127, 46 %, +32.4R |
| BTC 2024-2026 (2R cap) | 30, 53 %, +7.1R | 29, 55 %, +14.0R | 43, 56 %, +20.1R | 102, 49 %, +42.2R |

The rule holds on gold, holds for the weekly on EURUSD (the monthly-against trades won there), and fails on BTC, where
trades against the higher timeframes won more often. Runs: `eu_against_w_full`, `eu_against_mw_full`,
`gold_against_mw_full` (with `eu_against1m_full`, `gold_against1m_full` from the anatomy batch).

### How fast a challenge passes on these trades (`scripts/challenge_sim.py`)

Max, 5 October: "hoe snel kunnen we nu zo'n challenge als we alle markten pakken?" Every calendar day from 1 February
2024 to 31 March 2026 is a start (790 starts); from that day the profiles' real trades count, P&L = R x risk % of the
initial balance at the close. Phase 1 +10 %, phase 2 +5 % on a fresh account, each at least 4 trading days; a phase
fails on -10 % static or a -5 % day. Calendar days, p25 / median / p75:

| Markets | Risk | Funded | Failed | Phase 1 | Phase 2 | To funded |
|---|---|---|---|---|---|---|
| EURUSD + gold + BTC (BTC profile as pushed, previous-high target) | 1 % | 86 % | 14 % | 68 / 110 / 171 | 28 / 49 / 124 | 113 / 196 / 256 |
| EURUSD + gold + BTC (BTC with the 2R cap) | 1 % | 90 % | 10 % | 52 / 108 / 202 | 26 / 34 / 62 | 108 / 154 / 255 |
| EURUSD + gold + BTC (2R cap) + GBPUSD | 1 % | 89 % | 11 % | 51 / 101 / 175 | 26 / 29 / 62 | 98 / 139 / 231 |
| EURUSD + gold + BTC (2R cap) + GBPUSD | 1.5 % | 72 % | 28 % | 33 / 55 / 107 | 17 / 27 / 37 | 64 / 91 / 152 |
| EURUSD alone | 1 % | 55 % | 3 % (42 % unfinished) | 165 / 260 / 426 | | 390 / 477 / 648 |
| gold alone | 1 % | 40 % | 6 % (54 % unfinished) | 131 / 234 / 325 | | 144 / 263 / 392 |
| BTC alone (2R cap) | 1 % | 99 % | 1 % | 191 / 300 / 435 | | 282 / 419 / 595 |

All markets together at 1 %: phase 1 in a median of about three and a half months, a quarter of the starts in seven
weeks or less, funded in a median of four and a half months, one start in nine fails. 1.5 % halves the time and fails
one start in four. No single market comes close; the markets together are what makes it work.

Results of the anatomy runs (zone age, scalps, the 10:00 start, gold's 1D+1H pair), the higher-timeframe veto runs,
the BTC cap at 1.5R and 2.5R (a plateau check) and the Kronos filter judged on the profiles' trades are added below
when they finish.
