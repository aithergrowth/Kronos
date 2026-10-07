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
  BTC around the clock by the hour (7 October, the run on 1 February 2024 to 25 September 2026 without sessions): in the
  entry windows 96 trades, 43 % won, +23.9R; at night (23:00-07:00 Amsterdam) 130 trades, 39 % won, +8.8R, +0.07R a
  trade, less than FTMO's crypto commission takes (about 0.13R at the median 431 USD stop); 02:00-05:00 alone 63
  trades, -21.5R; the other day hours 150 trades, -1.7R. The night of 6 to 7 October (six bullish 1H touches between
  03:30 and 04:06: the price fell through the upper zones to 83,562 inside the lowest, then rose to about 84,200) is one
  such night.
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

## Spent zones: the losing months on the set that runs (7 October)

Max: "ongeveer 1 op de 3 maanden is negatief ... kunnen we hier nog onderzoek naar doen". The four profiles as they run
(EURUSD re-entries and limit, gold 2R fallback, NAS100 limit, BTC balance shift), February 2024 to September 2026,
with FTMO's measured costs (the 6 October evening spreads; commission: forex $2.50 a lot a side, metals 0.0007 % a
side, crypto 0.0325 % a side, indices none), 0.10R haircut, two open, 1.25 % with 4H zones x2 and BTC half.

- 12 of 32 months lost, -37.2 % together; eight of them -3.1 % or less, four deep (March 2024 -5.5 %, April 2024
  -8.4 %, July 2025 -7.5 %, March 2026 -4.2 %). In those months BTC lost -17.4R, gold -9.1R, EURUSD -7.5R, NAS100 -3.0R.
- The one cut that loses in both halves (February 2024 - May 2025, June 2025 - September 2026) and in every market:
  the time from the zone forming to the first touch of the visit. Touched within a day: 299 trades, 53 %, +140.7R,
  +177 % on the account; one to three days: 25 trades, 24 %, -17.0R; later: 14 trades, 36 %, -8.0R. BTC 25 trades
  -14.2R, gold 9 -5.4R, NAS100 4 -4.4R, EURUSD 1 -1.0R. The 4 October anatomy found the same on the older profiles;
  the course calls a used zone spent. `max_zone_age_candles` counts candles of the zone's own timeframe, so a 4H zone
  could wait four days and a 1D zone 24: the new `confirmation.max_touch_age_hours` counts hours for every timeframe.
- Ledger replay of the limit: 12 h 8 losing months, 18 h 8, 24 h 9, 36 h 10, 48 h 10 (now 12): every limit helps, so
  the gain does not hang on the hour.
- Engine runs with 24 h (`*_ta24`): EURUSD 30 trades +25.6R (was 31, +24.6R), gold 142 +69.3R (138, +63.1R on the
  same window), NAS100 32 +31.9R, drawdown -3.0R (35, +28.9R, -5.0R), BTC 113 +69.6R, drawdown -6.0R (136, +61.7R,
  -10.3R). With FTMO's costs, combined:

| | Trades a month | R a trade | Month average / median | Losing months | Worst month | 2-Step from 2026 starts within 6 wk / 2 mo / 3 mo | 2024-25 starts within a year / failed | 14-day trial +5 % |
|---|---|---|---|---|---|---|---|---|
| As it ran | 10.6 | +0.34 | +4.6 % / +3.8 % | 12 | -8.4 % | 30 / 48 / 65 % | 84 / 15 % | 45 % |
| **Zone touched within 24 h** | 9.6 | **+0.47** | **+5.7 % / +4.6 %** | **10** | **-6.7 %** | **40 / 59 / 77 %** | **100 / 0 %** | 45 % |

- Taken into all four profiles (`max_touch_age_hours: 24`).
- Not taken, on top of it (ledger replay): half the stake after three losses in a row on the account (average +5.4 %,
  worst -6.9 %, losing months unchanged), no trade for three days after four (worse), a market's stop-out ending its
  day (10 losing months), two losses in a row pausing a market three days (11). As on 5 October: a stop does not
  remove losing months, the entries do.
- What is left is mostly chance: drawing months of 9.4 trades from this set's own trades gives 23 % losing months
  (9 % under -3 %); two months together 13 %, three 8 %.
- BTC's R rests on three shorts in June 2026 (+23.4R, +11.6R, +5.8R): without them its 135 trades of the run before
  the limit were -15.6R after FTMO's costs, its longs +3.3R over 73 trades. EURUSD, gold and NAS100 earn on both sides.

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

### The higher-timeframe veto, run (5 October): into the profiles

| Market | Run | Trades | Win | Sum R | Max dd | Per year | At 1 % |
|---|---|---|---|---|---|---|---|
| EURUSD 2023-2026 | profile, the book | 73 | 49 % | +11.8R | -11.3R | -0.6 / -6.1 / +12.5 / +5.9 | +11.7k, once 10 % under the start |
| | **no trade against the weekly (`eu_against_w_full`)** | **58** | **55 %** | **+21.1R** | **-5.3R** | +2.3 / -1.4 / +12.2 / +7.9 | **+22.7k, never** |
| | no trade against the monthly or the weekly (`eu_against_mw_full`) | 47 | 51 % | +13.0R | -6.7R | +2.3 / -5.7 / +10.0 / +6.3 | +13.3k, never |
| Gold 2023-2026 | profile, two of 1D/4H/1H | 163 | 44 % | +27.6R | -12.9R | +3.5 / +7.7 / +6.1 / +10.3 | +29.0k |
| | **no trade against the monthly or the weekly (`gold_against_mw_full`)** | **129** | **46 %** | **+30.4R** | **-10.8R** | +6.9 / +8.1 / +7.1 / +8.2 | **+33.0k** |

The runs match the ledger estimates almost trade for trade: the veto removes trades and changes little else. The
weekly veto was chosen on EURUSD; GBPUSD, not used to choose it, agrees on its ledger (the 19 weekly-against trades won
32 % for -4.5R, the 43 kept 58 % for +12.7R against 62 trades, +8.2R). In the profiles from 5 October:
`config/dorus_live.yaml` and `config/dorus_pilot.yaml` `no_trade_against: [1W]` (version 4), `config/dorus_live_gold.yaml`
`[1M, 1W]`; BTC none (its trades against the higher timeframes won more often).

Challenge (`scripts/challenge_sim.py`, 790 starts, EURUSD + gold with the veto + BTC with the 2R cap):

| Risk | Funded | Failed | Phase 1 | Phase 2 | To funded |
|---|---|---|---|---|---|
| 1 % | 91 % | 9 % | 54 / 104 / 191 | 27 / 35 / 62 | 113 / 164 / 241 |
| 1.5 % | 85 % | 15 % | 33 / 65 / 116 | 18 / 33 / 62 | 77 / 113 / 184 |

The veto does not make the challenge faster (fewer trades), it makes it safer: at 1.5 % the failures drop from 26 %
to 15 % because the drawdowns halve. That buys the higher risk.

### Into the BTC profile: the 2R cap (5 October)

`config/dorus_live_btc.yaml` takes `tp_max_rr: 2.0`, `tp_cap_choice: nearest` from 5 October. Plateau check at the same
moment (29 March 2025, the cap runs at 1.5R and 2.5R still going): uncapped +9.4R, 2R cap +12.6R, 1.5R about +14.6 %,
2.5R about +12.7 % equity, so the gain does not hang on the exact level.

Challenge on the confirmed profiles (EURUSD version 4, gold with the veto, BTC with the 2R cap), and the same for
starts in 2026 only (Jan-Jun, 181 starts; 2026 was a good year, so this is the favourable case):

| Starts | Risk | Funded | Phase 1 (p25 / median / p75) | To funded (median) |
|---|---|---|---|---|
| Feb 2024 - Mar 2026 | 1 % | 91 % | 54 / 104 / 191 days | 164 days |
| Feb 2024 - Mar 2026 | 1.5 % | 85 % | 33 / 65 / 116 days | 113 days |
| Jan - Jun 2026 | 1 % | 97 % | 24 / 51 / 85 days | 78 days |
| Jan - Jun 2026 | 1.5 % | 100 % | 18 / 32 / 61 days | 60 days |
| Jan - Jun 2026, gold with the NY session and retests (2026 run before the veto) | 1.5 % | 94 % | 13 / 31 / 82 days | 68 days |

### Lower zone timeframes, now that they are mapped (5 October)

Until commit `71af980` the engine mapped zones on 1M to 1H only, so every earlier "15m zones" run traded the profile's own
zones (no 15m trade in any ledger). With 15m (and 5m) zones mapped and entered on 1m shifts, each variant against its
profile over the same window (the 2026 runs start on 1 October 2025; stopped once the verdict was clear):

| Variant | Window | Trades | R | Profile, same window |
|---|---|---|---|---|
| Gold + 15m zones | Oct 2025 - 18 May 2026 | 56 | about +7.6R | 19 trades, +14.8R |
| Gold + 15m + 5m zones | Oct 2025 - 12 Mar 2026 | 71 | about -6.4R | 15 trades, +9.5R |
| Gold + 15m + NY session + second visits | Oct 2025 - 18 May 2026 | 94 | about -6.2R | 19 trades, +14.8R |
| Gold + the same, fresh zones only | Oct 2025 - 18 May 2026 | 74 | about +4.9R | 19 trades, +14.8R |
| Gold + NY session + second visits (version 4) | Oct 2025 - 22 Jul 2026 | 35 | about +12.8R | 21 trades, +15.2R |
| EURUSD + 15m zones | Oct 2025 - 3 Apr 2026 | 11 | about -3.0R | 4 trades, +0.1R |
| EURUSD intraday gate + 15m zones | Oct 2025 - 3 Apr 2026 | 47 | about -6.4R | 4 trades, +0.1R |
| BTC + 15m zones | Jan - 25 Jun 2026 | 56 | about +29.5R | 22 trades, +42.7R |

The lower zones multiply the trades by two to five and the trades they add lose; the edge is in the 1H-and-up zones,
as the course trades them. What does help is freshness: zones at most 24 candles of their own timeframe old
(`confirmation.max_zone_age_candles 24`) on the earlier profiles: gold to October 2025 112 trades, about +27.1R against
123 trades, +18.5R; BTC (previous high, no cap) to January 2026 90 trades, about +14.3R against 100, +8.7R. Running on
the current profiles (`v4_gold_age24_full`, `btc_cap2_age24_long`, `v4_eu_age24_full`).

### Fresh zones on the current profiles (5 October)

Guard off, 1 % per trade, each against its profile over the same data (EURUSD and gold to 24 September 2026, BTC to
4 October 2026):

| Market | Run | Trades | Win | Sum R | Per trade | Max dd | Per year |
|---|---|---|---|---|---|---|---|
| Gold | profile, veto 1M+1W (`gold_against_mw_full`) | 129 | 46 % | +30.4R | +0.24R | -10.8R | +6.9 / +8.1 / +7.1 / +8.2 |
| | **zones at most 24 candles old (`v4_gold_age24_full`)** | **119** | **45 %** | **+38.7R** | **+0.33R** | **-9.9R** | +8.3 / +12.1 / +9.2 / +9.2 |
| EURUSD | profile, version 4 (`eu_against_w_full`) | 58 | 55 % | +21.1R | +0.36R | -5.3R | +2.3 / -1.4 / +12.2 / +7.9 |
| | zones at most 24 candles old (`v4_eu_age24_full`) | 53 | 53 % | +21.1R | +0.40R | -5.3R | +2.3 / -1.0 / +13.1 / +6.7 |
| BTC | profile, 2R cap (`btc_cap2_long`) | 145 | 51 % | +62.3R | +0.43R | -10.1R | +9.5 / -0.1 / +52.9 |
| | zones at most 24 candles old (`btc_cap2_age24_long`) | 124 | 50 % | +54.4R | +0.44R | -13.7R | +10.7 / -5.4 / +49.0 |

Gold gains in every year with a smaller drawdown, so `config/dorus_live_gold.yaml` takes `max_zone_age_candles: 24`.
The plateau check was stopped once it was clear: at 16 April 2025 the 12-, 24- and 48-candle limits stood at 126,719,
126,276 and 126,239 against the profile's 123,587 (equity from 100,000), so the gain does not hang on the exact age.
EURUSD makes the same R with five trades fewer and keeps its profile; BTC loses 8R and gains drawdown, and keeps its
profile (its 12- and 48-candle runs were also under the profile when stopped, 16 April and 8 July 2025).

New markets on the EURUSD version 4 profile, stopped where the verdict was clear (equity from 100,000 at 1 %):
US500 94,255 after 46 trades (21 April 2025), GER40 93,611 after 43 (6 August 2025), XAGUSD 92,277 after 24 (21 April
2025). Not taken. NAS100, GBPUSD and USDJPY run to the end.

### Targets, new markets and the account (5 October, afternoon)

**Closer targets.** `scripts/target_sweep.py` walks every trade of a profile ledger on the 5m bars again with the target
capped at k R (or fixed at k R); the stop counts first when stop and target sit in one bar, and the walk reproduces the
ledgers within 1-2R (EURUSD +21.3R against +21.1R, gold +39.6R against +38.7R, BTC +64.2R against +62.3R):

| Market | Profile target | Capped 1R | Capped 1.5R | Capped 2R | Fixed 2R | Fixed 3R |
|---|---|---|---|---|---|---|
| EURUSD | 55 %, +21.1R | 60 %, +7.9R | 60 %, +15.6R | 60 %, +20.0R | 50 %, +25.8R | 40 %, +27.1R |
| Gold | 45 %, +38.7R | 59 %, +15.4R | 51 %, +13.9R | 49 %, +18.7R | 41 %, +28.0R | 33 %, +37.0R |
| BTC | 51 %, +62.3R | 61 %, +21.9R | 57 %, +25.1R | 54 %, +19.7R | 43 %, +39.3R | 35 %, +51.7R |

Closer targets lift the win rate to 60-70 % and cost half the R or more: the profit is in the far targets, the
profiles keep theirs.

**Markets** on the EURUSD version 4 profile (2023 to 24 September 2026, guard off, 1 %), ETH on the BTC profile:

| Market | Trades | Win | Sum R | Max dd | Per year | Taken |
|---|---|---|---|---|---|---|
| GBPUSD (`mk_gbpusd_full`) | 43 | 58 % | +12.7R | -5.0R | +0.2 / +1.1 / +7.2 / +4.2 | yes, `config/dorus_live.yaml` |
| NAS100, 12-point stop minimum (`mk_nas100_full`) | 76 | 47 % | +13.6R | -7.2R | +8.2 / -4.6 / +3.2 / +6.9 | yes, `config/dorus_live_nas100.yaml` |
| USDJPY (`mk_usdjpy_full`) | 54 | 41 % | -8.2R | | | no |
| ETH 2026 (`eth_cap2_y26`; 2024 to 29 Oct -9.6 %, 2025 to 17 Oct +3.8 % when stopped) | 37 | 38 % | -10.7R | | | no |
| EURUSD, stop at least half the zone (`v4_eu_stopzone_full`) | 60 | 57 % | +19.6R (+17.5R to 24 Sep) | -5.3R | | no |

**The account.** In a single-market run the one-open-trade rule already skips signals (BTC 54 of 204, EURUSD 18 of 84,
gold 12 of 136); on one account the markets share it as well. `scripts/portfolio.py` combines the ledgers first come,
first served under an account-wide cap (one per market, as in the runs) and `scripts/challenge_sim.py` takes the
result (790 starts, February 2024 to March 2026; the month statistics over February 2024 to September 2026):

| Markets | Open at once | Risk | Funded | Phase 1 days (p25 / median / p75) | To funded (median) | Month avg / median / worst |
|---|---|---|---|---|---|---|
| EURUSD, gold, BTC | 1 | 1 % | 91 % | 61 / 92 / 135 | 168 days | |
| EURUSD, gold, BTC | 1 | 1.5 % | 86 % | 36 / 56 / 100 | 97 days | +4.8 % / +3.2 % / -11.0 % |
| EURUSD, gold, BTC | 2 | 1.5 % | 82 % | 35 / 61 / 107 | 104 days | +4.9 % / +2.6 % / -11.0 % |
| + GBPUSD, NAS100 | 1 | 1.5 % | 74 % | 32 / 51 / 97 | 86 days | +5.0 % / +2.0 % / -11.0 % |
| **+ GBPUSD, NAS100** | **2** | **1.5 %** | **85 %** | **26 / 42 / 66** | **79 days** | **+6.0 % / +3.6 % / -11.0 %** |
| + GBPUSD, NAS100 | 2 | 1 % | 92 % | 45 / 66 / 134 | 117 days | |

With five markets one slot turns good trades away (74 % funded); two slots, one per market, keep the pass rate of three
markets at 1.5 % and shorten phase 1 from 56 to 42 days; a month in the best quarter makes +10.5 % or more. Taken
from 5 October: risk 1.5 % (Max's choice), `prop_firm.max_open_trades: 2` with `max_open_per_symbol: 1` (new in the
guard), GBPUSD and NAS100 in `scripts/start_live.bat` (NAS100 later moved to `scripts/start_ftmo.bat`: MetaQuotes-Demo has no Nasdaq-100). The guard's 8 % now counts from the initial balance
(`drawdown_basis: initial`) like FTMO's static 10 %: from the peak it stopped the bot after an ordinary swing back from
a gain (8 % is 5.3R at 1.5 %), which the challenge simulations never counted as a failure. Running: BTC in the
morning session only, break-even at +1R and two BTC trades at once (each in yearly chunks), and AUDUSD, USDCAD,
USDCHF and NZDUSD on the EURUSD profile.

### Losing months and the monthly stop (5 October, afternoon)

The five-market account (two open, 1.5 %) lost in 10 of 32 months, five of them more than 3 % (April 2024 -11.0 %:
BTC -4.3R and gold -3.0R; June 2024 -5.4 %; August 2026 -5.2 %: BTC -2.9R, NAS100 -2.0R). July to September 2026 as a
whole: 31 trades, 48 %, +0.6R. The August 2026 BTC losers were shorts with the monthly, weekly and daily bearish while
the 4H had turned up at the bottom of the fall (six of eight lost, most never 0.4R in profit). Over the whole BTC
ledger the trades against the 4H lost (19, 47 %, -3.5R; with the 4H 99, 59 %, +57.2R); `no_trade_against: [4H]` on
BTC is running as a backtest. Both directions are traded: EURUSD 36 long / 22 short, gold 97 / 22 (the veto keeps it
out of shorts against the bullish monthly), BTC 94 / 51, GBPUSD 22 / 21, NAS100 57 / 19.

`scripts/loss_limits.py` replays the combined ledger with a rule that skips trades while it is active:

| Rule | Trades | Sum R | Month avg / median | Losing months | Worst month | Drawdown |
|---|---|---|---|---|---|---|
| none | 365 | +128.0R | +6.00 % / +3.60 % | 10 | -11.0 % | -24.2 % |
| no new trade after a month's closed loss of 2R | 261 | +109.7R | +5.14 % / -0.34 % | 17 | -4.2 % | -14.9 % |
| **the same at 3R (4.5 % at 1.5 %)** | **311** | **+118.4R** | **+5.55 % / +2.77 %** | **13** | **-5.2 %** | **-15.3 %** |
| the same at 4R | 342 | +123.9R | +5.81 % / +3.36 % | 11 | -6.3 % | -18.3 % |
| a week's closed loss of 3R | 356 | +131.8R | +6.18 % / +3.60 % | 10 | -8.7 % | -21.9 % |
| a pause of 7 days after 4 losses in a row on the account | 340 | +125.9R | +5.90 % / +3.60 % | 9 | -8.0 % | -21.5 % |

A month stop cannot remove losing months (a stopped month cannot recover, so there are more of them), it caps how
deep they go. At 3R the worst month is -5.2 % instead of -11.0 % and the drawdown halves for about 0.45 % a month; the
challenge (790 starts) is funded in 91 % instead of 85 %, phase 1 in a median of 56 days instead of 42. Taken:
`prop_firm.monthly_loss_limit_pct: 4.5` in the live profiles (new in the guard: the month's closed loss from the
balance at the start of the month). The guard also takes its day and month baselines from the broker's closed P&L
when it starts (`realized_pnl_since` on the paper and MT5 brokers), so a restart no longer forgets the day's or the
month's losses. With the BTC 4H rule (ledger estimate) on top: +125.1R, average +5.86 %, worst month -5.1 %, funded
90 %, phase 1 48 days. The FTMO 10k average payout Max aims at (780 EUR, 7.8 % a month) is +7.8 % on this ledger at
2 % risk, where the challenge is funded in 74 % of the starts.

Results of the anatomy runs (zone age, scalps, the 10:00 start, gold's 1D+1H pair), the higher-timeframe veto runs,
the BTC cap at 1.5R and 2.5R (a plateau check) and the Kronos filter judged on the profiles' trades are added below
when they finish.

### Risk steps for the challenge and the funded account (5 October, evening)

The month stop above was switched off again the same day (Max: better entries, not a stop; `monthly_loss_limit_pct:
0.0` in the live profiles). What does help the account without skipping a single trade is the stake:
`risk.drawdown_steps` lowers the risk per trade while the balance is under the start (level % from `account_size`,
risk %), in the backtest runner and live alike. `scripts/risk_steps.py` replays the five-market ledger (two open, one
per market, 365 trades February 2024 to September 2026, +0.35R a trade) on the FTMO rules: the challenge from every
day of February 2024 to March 2026 (phase 1 +10 %, phase 2 +5 %, -10 % static, -5 % a day), the funded account from
every 7th day to September 2025 for 12 months (80 % of a positive month paid out, the balance back to the start).
`--haircut` takes that many R off every trade, for a live result worse than the backtest:

| Challenge | Funded (backtest) | Funded, -0.10R a trade | Funded, -0.15R a trade | Failed (backtest / -0.15R) |
|---|---|---|---|---|
| 1.5 % flat | 85 % | 72 % | 65 % | 15 % / 35 % |
| **1.5 %, 1.0 % from -3 %, 0.5 % from -6 %** | **92 %** | **87 %** | **75 %** | **8 % / 25 %** |
| 2.0 % with the same steps | 91 % | 89 % | 65 % | 9 % / 35 % |
| 1.0 % flat | 92 % | | | 8 % / |

| Funded account, 12 months | Lost (backtest) | Lost, -0.10R | Lost, -0.15R | Paid out a month (backtest / -0.15R) |
|---|---|---|---|---|
| 1.5 % flat | 21 % | 59 % | 90 % | 4.1 % / 1.3 % |
| 1.0 % flat | 11 % | 16 % | 21 % | 2.9 % / 1.6 % |
| **1.0 %, 0.5 % from -3 %** | **2 %** | **10 %** | **11 %** | **2.8 % / 1.4 %** |
| 0.75 % flat | 8 % | 11 % | 13 % | 2.3 % / 1.3 % |

The median time to funded grows with the steps (1.5 % flat 80 days, with the steps 96, 1.0 % flat 118).

Taken: `drawdown_steps: [[-3, 1.0], [-6, 0.5]]` at 1.5 % in the live profiles (challenge mode). On a funded account
the plan is 1.0 % with `[[-3, 0.5]]`: paying out every month keeps no buffer, and at 1.5 % flat a live edge a third
smaller than the backtest's loses most funded accounts within a year. The steps only change the stake, so the
replay on fixed ledgers is exact apart from the compounding (the replay risks a share of the start, the bot of the
equity).

### Strategy sweep on recent data (5 October, afternoon)

The backtester got about four times faster the same day (CandleSeries views instead of frame copies, cached zone
scans, a bisect news check; trades and equity byte-identical to the old code on NAS100, EURUSD and gold over
July 2025 to September 2026 and on BTC, February to March 2026), so each profile could be tried with a dozen changes
on July 2025 to September 2026 (one open trade, guard off). Change in R against the profile (`sweep3`):

| Variant | BTCUSD | XAUUSD | EURUSD | GBPUSD | NAS100 |
|---|---|---|---|---|---|
| base (R, trades, win %) | +45.0 (57, 44 %) | +14.0 (39, 54 %) | +17.6 (28, 71 %) | +4.8 (11, 64 %) | +3.3 (34, 44 %) |
| nod1 | -0.7 | +0.0 | -0.2 | +0.0 | +1.0 |
| minrr1 | -19.4 | -0.1 | -0.6 | -0.1 | -0.2 |
| minrr15 | -22.3 | -5.6 | -12.2 | -2.9 | +1.9 |
| tp_near | -10.7 | -1.6 | -0.6 | +0.0 | +4.4 |
| tp_far | -9.6 | +0.4 | -3.8 | -2.4 | +0.6 |
| stop_tight | +0.0 | +0.0 | -1.9 | +0.0 | +0.0 |
| stop_wide | +0.0 | +0.0 | -6.1 | -0.4 | +0.0 |
| depth03 | -27.7 | +1.7 | -2.9 | -1.0 | +1.2 |
| conf15 | -43.7 | -12.1 | -11.6 | -6.0 | -5.3 |
| bms | -6.8 | -13.8 | +2.3 | +5.8 | -3.9 |
| sess_wide | -15.6 | +4.8 | -7.2 | -3.8 | +2.5 |
| cap3 | -14.9 |  |  |  |  |

nod1 = no daily zones; minrr1/minrr15 = minimum R:R 1.0/1.5; tp_near/tp_far = 2/3 or 5/3 of the target's lookback;
stop_tight/stop_wide = 0.6/1.5 times the minimum stop; depth03 = entry at most 30 % into the zone; conf15 = 1H zones
confirmed on 15m; bms = the plain structure break as a confirmation; sess_wide = 08-12 and 13-18; cap3 = BTC's R:R cap
at 3. Checked over 2023-2026 where the recent window looked better:

| Change | Recent window | 2023-2026 | Taken |
|---|---|---|---|
| Gold, sessions 08-12 and 13-18 | +4.8R | 150 trades, +28.1R against 119, +38.7R; drawdown -14.2R against -9.9R | no |
| NAS100, the same sessions | +2.5R | 97 trades, +13.0R against 76, +13.6R | no |
| EURUSD / GBPUSD, structure break entries | +2.3R / +5.8R | +21.3R against +21.1R / +17.5R against +12.7R with a -8.2R drawdown | no |
| Minimum R:R 1.0 | about the same R, fewer trades | EURUSD +22.9R (42 trades) against +21.1R; GBPUSD, gold, NAS100 worse | no |
| EURUSD fixed target 2R / 3R | +1.1R / -1.4R | +18.2R / +25.7R against +21.1R; drawdown -11R / -12R against -5.3R | no |
| Gold fixed target 2R / 3R | +4.3R / +8.3R | +42.0R / +60.6R against +38.7R; 3R: +43.3R in 2025, worse in the other three years | no |
| BTC 1H zones at most 24 candles old | | 128 trades, +59.3R against 145, +62.3R | no |
| Break-even at 2R (EURUSD / GBPUSD / NAS100 / gold / BTC) | 0 / 0 / 0 / -1.6R / +1.0R | | no |
| Entry on the first candle after the shift | identical on all five | | no |
| **NAS100, close after 48 h (`exits.max_hold_hours`)** | | **78 trades, 53 %, +25.6R, drawdown -5.4R against 76, 47 %, +13.6R, -7.2R** (24 h: +26.8R) | **yes** |
| The same 48 h limit on the others | | EURUSD +22.1R, GBPUSD +10.3R, gold +33.9R, BTC +53.5R (against +21.1R / +12.7R / +38.7R / +62.3R) | no |

New markets on the EURUSD profile (10-pip minimum stop) and UK100 on the NAS100 profile (5 points), 2023-2026:
GBPJPY 45 trades -22.7R, AUDJPY 45 trades -13.2R, UK100 67 trades -5.0R, EURJPY 48 trades +22.4R (2023 -5.8R,
2024 -0.7R, 2025 +20.0R with one trade of +17.7R, 2026 +8.9R): none taken; EURJPY is watched. A correlation rule
(no EURUSD and GBPUSD trade the same way at once) changed the five-market account by 4 trades: they overlapped six times
in two and a half years. BTC's confirmation-candle volume (against the day's median) sorted nothing: the quartiles
won 59 / 53 / 44 / 47 %, without a pattern across the years. Costs the backtests leave out (commission, slippage) take
3-24 % of the R at FTMO-like rates: EURUSD +21.1R to +18.0-19.2R, gold +38.7R to +36.1-37.4R, BTC +62.3R to
+47.2-55.8R with 15-35 points more per trade.

### The daily candles live sees (5 October, evening)

A review of live against backtest found that the 1D/1W/1M candles of `data/histdata*` are TradingView OANDA bars,
not built from the HistData minutes the rest uses, and that HistData's week holds a Friday hour in summer that no
New York + 7 server has. `scripts/build_mt5_like.py` rebuilds every timeframe from the minutes (GBPUSD from its 5m bars): the weekend
cut at Friday 17:00 to Sunday 17:00 New York, 4H and up anchored at 17:00 New York, the TradingView bars kept only
before the first rebuilt one. The same profiles over 2023-2026:

| Market | TradingView higher timeframes | MT5-like candles |
|---|---|---|
| EURUSD | 58 trades, 55 %, +21.1R, -5.3R | 57 trades, 49 %, +11.3R, -6.0R (+3.2 / -0.4 / +1.8 / +6.7) |
| GBPUSD | 43 trades, 58 %, +12.7R, -5.0R | 48 trades, 54 %, +8.6R, -6.1R |
| Gold | 119 trades, 45 %, +38.7R, -9.9R | 118 trades, 45 %, +36.6R, -8.2R (+8.5 / +10.4 / +8.6 / +9.1) |

Gold holds; EURUSD and GBPUSD keep about half. On these candles, two open at 1.5 % with the drawdown steps, February
2024 to September 2026: the four demo markets (EURUSD, GBPUSD, gold, BTC) 9.6 trades a month, the median month +1.7 %,
the average +4.8 % (+2.6 % without June 2026), the challenge funded in 89 % of the starts (median 140 days); with
NAS100 and its 48 h limit 11.4 trades a month, median +3.2 %, average +5.7 % (+3.6 % without June 2026), funded 98 %
(median 105 days), 81 % with every trade 0.10R worse. From here on the research runs on these candles.

### Margin on a 10k FTMO account (5 October, evening)

The backtests size every trade at its risk with no margin limit. A broker does have one: exposure divided by
leverage has to fit in the free margin, or MT5 refuses the order ("No money", 10019). At 1.5 % risk the exposure a
trade needs is 1.5 % of the account divided by the stop as a share of the price (MT5-like candles, 2023-2026):

| Market | Stop, median (smallest) | Exposure, median / 90th pct / largest | R at 1:100 / 1:50 / 1:30 / 1:20 / 1:10 |
|---|---|---|---|
| EURUSD | 0.12 % (0.07 %) | 12x / 20x / 22x | 11.3 / - / 8.6 / - / - |
| GBPUSD | 0.11 % (0.06 %) | 14x / 21x / 24x | 8.6 / - / 9.2 / - / - |
| Gold | 0.19 % (0.05 %) | 8x / 15x / 31x | - / 36.9 / 35.3 / 31.0 / 20.8 |
| NAS100 (48 h) | 0.17 % (0.07 %) | 9x / 15x / 21x | - / 25.6 / - / 27.7 / 20.2 |
| BTC | 0.60 % (0.09 %) | 2.5x / 7.4x / 17x | at 1:3.3 24.3, at 1:2 15.2, at 1:1 7.4 (62.3 unlimited) |

The R columns assume one position may hold 45 % of equity as margin, cut to fit. FTMO's Standard account
gives about 1:100 on forex and 1:50 on indices and gold, which never binds. Crypto gets about 1:2 to 1:3.3, and
there 81-91 % of the BTC trades need more. The live loop now cuts the lots to fit instead of sending an order the
server refuses. `margin_per_lot` (order_calc_margin) gives the server's own leverage, and one position ties up at
most `prop_firm.max_margin_pct` (45) of equity and 90 % of the free margin, so the second open position still fits.
Below the minimum lot the setup is skipped with a message. The fill message says when the lots were cut, and the
window prints the leverage at start (`margin: 1 lot BTCUSD ties up ... (about 1:2)`). On FTMO, BTC therefore adds
roughly a quarter to a third of its backtest R. The Swing account type (1:30 forex, 1:10 indices and gold, 1:1
crypto) would cost gold and NAS100 a third and BTC almost everything, so the Standard type fits these profiles.

Which account type to buy: FTMO's FAQ (October 2026) lets the Challenge and the Verification hold over the weekend
and through news on either type. On the funded FTMO Account, the Standard type has to be flat shortly before the
weekend close (and over a market break longer than 2 hours), and it keeps the news restrictions. Closing every
position at Friday 16:45 New York, on the trade ledgers above (MT5-like candles, 2023-2026), costs little because
few trades are still open then:

| Market | Open at a Friday 16:45 | Their R as held / closed on Friday | Total R |
|---|---|---|---|
| EURUSD | 2 of 57 | -0.4 / +0.1 | +11.3 -> +11.7 |
| GBPUSD | 5 of 48 | +2.8 / +1.8 | +8.6 -> +7.6 |
| Gold | 5 of 118 | +8.5 / +5.0 | +36.6 -> +33.1 |
| NAS100 (48 h) | 1 of 78 | +4.1 / +3.4 | +25.6 -> +25.0 |

About 5R in all, against a third of gold and NAS100 and most of BTC on Swing's leverage. Standard is the type to
buy.

Built since: `prop_firm.weekend_close` ("16:45"; `--weekend-close` on the live command, the `WEEKEND_CLOSE` line in
`scripts/start_ftmo.bat`) closes every position at Friday 16:45 New York and opens nothing until the Sunday open, in
the backtest and live. Run as backtests on the same candles: EURUSD +12.0R (3 weekend exits), GBPUSD +6.6R (5), gold
+30.8R (5), NAS100 +24.9R (1). That is about 8R in all over three and a half years, 5.8R of it gold: a little more
than the estimate, because a trade closed on Friday also frees the market for the next signal. Off until the account
is funded.

What the margin cut does to the challenge (`scripts/risk_steps.py`, the five ledgers of "The daily candles live
sees", two open, 1.5 % with the steps). Each BTC trade is scaled by what the margin allows, and the cost haircut
is scaled with it:

| BTC in the ledger | Funded (backtest) | Median days | Funded, -0.10R a trade | Median days |
|---|---|---|---|---|
| Full size (no margin limit) | 98 % | 105 | 81 % | 139 |
| Cut at 1:3.3 | 100 % | 107 | 95 % | 166 |
| Cut at 1:2 | 100 % | 106 | 99 % | 155 |
| Flat half size | 100 % | 115 | 85 % | 150 |
| No BTC | 100 % | 124 | 100 % | 169 |

The cut shrinks the tight-stop trades most (they need the most exposure), and those carried BTC's 2026: per year
+5.6 / +1.8 / +7.9R cut at 1:2 against +9.5 / -0.1 / +52.9R full. On FTMO the bot therefore trades a smaller,
steadier BTC that passes about as often as no BTC and gets there faster. The full-size BTC of the paper account
is the variance the challenge can least afford. That is one more reason the demo's monthly numbers overstate a
challenge account.

## The HistData clock, and the strategy over 2017-2026 (5 October, night)

**The clock.** The HistData loader added a fixed 5 hours, as HistData documents ("EST without daylight saving"). The data
says otherwise. The 08:30 New York payrolls spike sat exactly 60 minutes late in every European-summer release of
2024-2026 checked, and on time in every winter one, including the weeks when only the US is on summer time. The
stamps plus 5 hours are London time (`kronos_trader/data/histdata.py`, `to_utc`).

For about seven months a year, every HistData backtest above (EURUSD, GBPUSD, gold, NAS100, US500, GER40, silver) had
its sessions, its news blackouts and its 17:00 New York anchors an hour off what a live MT5 feed shows. The
"extra Friday hour" of "The daily candles live sees" was this shift, and its weekend cut removed the real last hour
of every summer week. BTC (Bitstamp, UTC) is not affected. All numbers above the BTC ones are on the shifted clock.

**2017-2026 on the corrected clock** (`fixed/`: HistData minutes 2016/2017 to September 2026 read right, MT5-like
candles, daily/weekly/monthly history from 2007; the live profiles; one trade at a time; guard off; R):

| Market | Trades | Win | 2017-2022 | 2023-2026 | Total | Max dd | Per year 2017 ... 2026 |
|---|---|---|---|---|---|---|---|
| NAS100 (48 h) | 230 | 48 % | +8.2R | +31.3R | **+39.5R** | -9.0R | -6.3 / +2.2 / +8.1 / -1.0 / +5.8 / -0.6 / +11.5 / -3.3 / +14.9 / +8.2 |
| Gold | 285 | 40 % | -14.8R | +44.5R | +29.7R | -27.6R | -3.6 / -0.9 / +11.0 / -11.1 / -6.4 / -3.8 / +18.4 / +9.3 / +6.3 / +10.5 |
| EURUSD | 163 | 41 % | -8.5R | +5.9R | -2.6R | -16.4R | +0.1 / -5.8 / -4.3 / -0.3 / +12.7 / -11.0 / +1.5 / -1.9 / -0.8 / +7.1 |
| GBPUSD | 190 | 39 % | -31.4R | +6.1R | -25.3R | -38.9R | -1.4 / -11.9 / -4.7 / -1.5 / -8.9 / -2.9 / -1.0 / -3.9 / +4.7 / +6.3 |

The profiles were read and tuned on 2023-2026, so only 2017-2022 is out of sample. NAS100 holds in both periods.
Gold earns in its 2023-2026 rally and loses before it. EURUSD has no edge over the ten years, and GBPUSD loses.

**Where the trades go** (`scripts/trade_paths.py`, on the live ledgers):

- Between a third and a half of the losers never go 0.25R our way, and only 15-23 % see +1R before the stop. They are
  entries the move never confirms, not trades managed badly.
- 50-68 % of the stopped trades reach their target within 72 hours after the stop. Wider stops still lose, because
  they cost more R per winner than they save. Re-entering the same zone after a stop lost before (R6: 9 % won).
- Is the direction right? 72 hours after the fill, 2023-2026: gold our way in 62 % (median +2.1R), GBPUSD 60 %,
  EURUSD 54 %, NAS100 54 %, BTC 51 %, ETH 39 % (median -0.85R). 2017-2022: EURUSD 40 %, GBPUSD 45 %, gold 40 %. The
  edge, where there is one, is the direction call, and it holds in some years and not in others.

**Tried on both periods and not taken:**

- a daily trend filter (200-day average, 12-month or 60-day return: helps GBPUSD and gold in 2023-2026, costs NAS100
  and EURUSD);
- regime filters (efficiency ratio, ADX, distance to the 200-day average, volatility rank: no direction holds in both
  periods);
- earlier break-even (BTC +0.4R, NAS100 +1.3R in real runs);
- the trigger candle's position in last week's range;
- the session half, Monday/Friday;
- the zone timeframe and the bias combination: the cuts that look good in one period turn in the other.

**One cut points the same way in six of eight market-periods:** trades whose planned R:R is at least 2.

| Market | R:R ≥ 2 | All trades |
|---|---|---|
| EURUSD | +7.8R (41 trades) | -2.6R |
| Gold | +45.6R (106) | +29.7R |
| NAS100 | +24.6R (79) | +39.5R |
| GBPUSD | -14.4R (58) | -25.3R |

It is running as real backtests (`risk.min_rr` 2.0 and 1.5) on the corrected candles.

**Taken (5 October, night):** GBPUSD is out of `scripts/start_live.bat` and `scripts/start_ftmo.bat`. It lost 25.3R over
2017-2026, and 14.4R even on its trades at R:R 2 or more. EURUSD stays for now. The minimum R:R runs decide its place.

**Minimum R:R 2, run (5 October, night).** `risk.min_rr` 2.0 against 0.5, 2017-2026 on the corrected candles:

| Market | Trades | Win | 2017-2022 | 2023-2026 | Total | Max dd |
|---|---|---|---|---|---|---|
| EURUSD | 163 -> 49 | 41 % -> 27 % | -8.5R -> +0.2R | +5.9R -> +9.6R | -2.6R -> **+9.7R** | -16.4R -> -9.2R |
| Gold | 285 -> 113 | 40 % -> 26 % | -14.8R -> -3.3R | +44.5R -> +39.0R | +29.7R -> **+35.7R** | -27.6R -> -15.5R |
| NAS100 (48 h) | 230 -> 85 | 48 % -> 36 % | +8.2R -> +16.0R | +31.3R -> +24.0R | +39.5R -> **+47.9R** | -9.0R -> -7.3R |

All three are better in total, in the out-of-sample years and in drawdown, on a third of the trades. The challenge
on these three ledgers (`scripts/risk_steps.py`, two open, steps, 0.10R a trade off for costs; FTMO has no time
limit):

| Ledgers, risk | Funded, all starts 2017-2025 | Starts 2017-2022 | Starts 2023-2025 | Median days to funded |
|---|---|---|---|---|
| R:R 0.5, 1.5 % | 31 % | 5 % | 79 % | 193 |
| **R:R 2, 1.5 %** | **50 %** | 25 % | 94 % (none failed) | 404 |
| R:R 2, 1.0 % | 62 % | | | 473 |
| R:R 2, 2.0 % | 44 % | | | 219 |

Taken: `min_rr: 2.0` in `config/dorus_live.yaml` (EURUSD), `config/dorus_live_gold.yaml` and
`config/dorus_live_nas100.yaml`. BTC keeps 0.5 for now, because its target is capped at 2R. BTC over 2020-2026 (5m
from Bitstamp since 2020): 296 trades, 46 %, +52.0R, but -10.0R in 2020-2023 and +53.8R in 2026 alone. Like gold, it
earns in one regime. The price of R:R 2 is time: about 26 trades a year on the three markets, and a challenge that
takes most of a year.

**Minimum R:R 1.5 against 2 (5 October, night).** The same runs at `min_rr` 1.5:

| Market | Trades | Total | 2017-2022 | 2023-2026 | Max dd |
|---|---|---|---|---|---|
| EURUSD | 67 | +14.4R | +2.5R | +11.8R | -10.0R |
| Gold | 144 | +33.0R | -1.5R | +34.3R | -13.4R |
| NAS100 | 114 | +51.2R | +17.9R | +33.4R | -10.0R |

Both thresholds are a plateau above 0.5, not a single lucky value. The challenge at 1.5 % on the R:R 1.5 ledgers is
funded from 52 % of all starts (2017-2022 31 %, 2023-2025 92 %), with a median of 285 days. At R:R 2 it is 50 %
and 404 days, at 1.0 % risk 64 % and 497 days. Taken: `min_rr: 1.5` in the three profiles (it replaces the 2.0
above), for the same edge on a third more trades.

**BTC out of the FTMO set (5 October, night).** BTC 2020-2026 with minimum R:R 2 is worse (target capped at 3R:
+28.4R, -23.7R drawdown; uncapped: +35.1R, -22.0R; the profile: +52.0R, -13.3R), and 2020-2023 stays negative in
all three. In the challenge replay from June 2020, EURUSD, gold and NAS100 at R:R 1.5 are funded from 75 % of the
starts (2020-2022: 55 %). With the profile's BTC added it is 42 % (2020-2022: 9 %): the variance of a market with
no edge outside one year. Max's decision (5 October): BTC stays in `scripts/start_ftmo.bat`. The bot trades the
present, not 2020, and on FTMO the margin cap trades BTC at roughly half size anyway.

**Can a 14-day trial pass? (5 October, night)** FTMO's free trial runs 14 days. On the corrected ledgers (EURUSD,
gold and NAS100 at R:R 1.5, BTC from June 2020 cut to FTMO's margin, two open, 0.10R a trade for costs), every start
day from June 2020 was replayed. The target is +10 % with at least 4 trading days, before a -5 % day or -10 %, and a
trade counts when it opens and closes inside the window:

| Risk a trade | Passed in 14 days | Failed | Trades in the window (median / 90th pct) |
|---|---|---|---|
| 1.5 % | 2 % | 0 % | 3 / 6 |
| 2 % | 2-3 % | 1 % | 3 / 6 |
| 3 % | 6-8 % | 7-10 % | 3 / 6 |
| 5 % | 4 % | 55-75 % | 3 / 6 |

Three trades in two weeks cannot make 10 % without gambling: at 5 % one loser and its costs breach the daily limit.
The trial is a test of the set-up on FTMO's server (orders, names, sizing, the margin cut, Telegram). The challenge
has no time limit. More trades with the same edge can only come from more markets that hold in both periods:
AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY, silver, US500 and GER40 are running on the corrected candles.

**More markets on the corrected candles (5 October, night).** Each market below ran on the live profile of its
kind at R:R 1.5 (the EURUSD profile for the pairs, gold's for silver, NAS100's for the indices), 2018 to September
2026, one trade at a time:

| Market | Trades | R | Max dd | 2018-2022 | 2023-2026 |
|---|---|---|---|---|---|
| AUDUSD | 55 | +4.9R | -14.1R | +15.7R | -10.7R |
| NZDUSD | 45 | -2.9R | -9.1R | | |
| USDCAD | 59 | -20.4R | -27.0R | | |
| USDCHF | 53 | -13.2R | -22.2R | | |
| USDJPY | 54 | -2.4R | -9.0R | | |
| Silver | 132 | -30.4R | -39.2R | | |
| US500 | 84 | -17.1R | -29.1R | | |
| GER40 | 65 | -0.3R | -15.7R | | |
| *NAS100, for comparison* | 105 | +56.5R | -10.0R | | |
| *Gold, for comparison* | 133 | +40.8R | -13.4R | | |

None is taken. The edge sits in gold and NAS100, and a little in EURUSD. Out of a dozen markets tried, a few
positive ones could also be luck, so the live results stay the judge. `scripts/start_ftmo.bat` gets a `RISK`
line for `scripts/ftmo_local.bat`, for a calmer challenge (1.0 %) or a deliberate trial gamble (see the 14-day table).

## More opportunities, a higher win rate? (6 October)

Max: "er is zoveel liquiditeit en fair value gaps in alle 3 de markten ... kijk of je de winrate kan verbeteren of
meer opportuniteiten kan pakken". Where the profiles stand on the corrected candles (R:R 1.5; BTC on its profile):

| Market | Trades a year | Win | Average win / loss | R a trade | Longest losing run |
|---|---|---|---|---|---|
| NAS100 | 12 | 38 % (2023-2026: 47 %) | +2.76R / -0.99R | +0.45R | 10 |
| Gold | 15 | 27 % (34 %) | +3.52R / -1.00R | +0.23R | 9 |
| EURUSD | 7 | 31 % (41 %) | +2.92R / -1.04R | +0.21R | 9 |
| BTC | 47 | 46 % | +1.53R / -1.00R | +0.18R | 6 |

The engine already trades the liquidity and the gaps. A zone runs from the liquidity taken (X) through the gap (b)
to the protector (P). The bias per timeframe reads the last sweep against the last gap. The shift is a close beyond
the opposing gap. Each idea below was measured on both 2017-2022 and 2023-2026:

- **The session windows**, never tested on the right clock before: 08:00-20:00 Amsterdam gives EURUSD 109 trades and
  -5.2R (against 67 and +14.4R), gold 260 trades and +17.0R (144 and +33.0R), and NAS100 175 trades and +51.6R (114
  and +51.2R; better in 2023-2026, worse before). The US session 14:00-21:00 gives NAS100 98 trades and +28.7R. The
  windows of the profiles (09-11, 13-17) stay. The extra hours add trades without edge.
- **A liquidity sweep before the shift** (the 24 h low or high taken between the touch and the confirmation) is rare.
  On NAS100 and BTC those trades did worse (NAS100 2023-2026: +0.05R a trade against +0.83R). A zone price runs that
  deep through is often broken. Not a filter.
- **A strong shift candle** (body over the 14-candle average range, top half) is better in five of eight market-
  periods and worse in two, and it halves the trades. Not taken.
- **A limit entry back into the zone** (25 % or 50 % of the way to the stop, valid 1 or 4 hours; missed when the
  target comes first) gives NAS100 more in both periods in all four variants (25 % / 4 h: +24.4R / +45.4R against
  +12.8R / +29.5R). EURUSD gains a little, gold loses in all of them (its winners leave without coming back), and BTC
  is mixed. It needs pending orders in the backtest and on MT5. It is a candidate for NAS100 only, with fewer trades
  (74-87 % filled).
- **Second visits** (`confirmation.allow_retest`): five to seven more trades in nine years per market. EURUSD 72
  trades +18.7R (drawdown -14.0R against -10.0R), gold 150 and +33.7R, NAS100 121 and +43.2R (against +51.2R). Not
  taken.

So the profiles stand. What can still add R is the limit entry on NAS100, once pending orders exist in the backtest.
Measured first as a real backtest on both periods, then on MT5. More trades with an edge do not come from wider
hours, second visits or more markets: those were all tried on the corrected candles.

## The recent window: timeframes, R:R and more coins (6 October)

Max: judge on the recent years ("we zitten niet op jaren te traden"), and look at 1, 5 and 15 minutes and 1 and 4
hours. All runs are on the corrected candles from January 2024 (BTC and the coins from February 2024), one trade at
a time:

| Variant | EURUSD | Gold | NAS100 |
|---|---|---|---|
| Profiles (zones 1D/4H/1H, shifts on 1H/15m/5m), R:R 1.5 | 20 trades, 40 %, +8.8R | 41, 32 %, +18.5R | 31, 45 %, +20.5R |
| + 15m zones (5m shifts) | 23, 43 %, +15.6R | 66, 27 %, +11.1R | 42, 40 %, +18.6R |
| The book's table (1H zone -> 1m, 4H -> 5m, 1D -> 15m), 1m steps | 50, 24 %, -4.8R | 125, 22 %, -15.4R | 90, 31 %, +14.6R |
| R:R 1.0 | **31, 48 %, +11.2R** | 58, 38 %, +22.1R | **45, 47 %, +21.5R** |
| R:R 0.5 | 45, 47 %, +4.5R | **84, 48 %, +26.1R** | 67, 54 %, +19.8R |

Lower timeframes add trades, but worse ones: 1m shifts double or treble the trades and lose. On the recent years a
lower R:R floor gives more trades, a higher win rate and as much or more R. The BTC profile on other Bitstamp coins
(February 2024 to October 2026) loses on all of them: SOL -12.0R, XRP -3.5R, LTC -41.8R, DOGE -4.3R (BTC +63.2R).

Challenge replay on February 2024 to September 2026 (EURUSD, gold and NAS100 plus BTC, two open, 0.10R a trade):
the profiles at 1.5 are funded from 78 % of the starts. EURUSD at 1.0, gold at 0.5 and NAS100 at 1.0 are funded
from 91 %, median 166 days, on 295 trades against 233. A third open slot changes nothing. The 14-day trial (BTC cut
to FTMO's margin) passes in 3 % of the starts at 1.5 % risk and 11 % at 3 % (10 % fail), with a median of 4 trades.

Taken (Max: the recent years decide): `min_rr` 1.0 in `config/dorus_live.yaml` (EURUSD), 0.5 in
`config/dorus_live_gold.yaml`, 1.0 in `config/dorus_live_nas100.yaml`. Over 2017-2026 the floor of 1.5 did better
before 2023. That is the trade-off of judging on the recent years only.

## Dorus's own trades against the bot, and his trade plan (6 October)

Max sent screenshots of three of Dorus's trades and of his trade-plan board. The screenshots stay out of the repository;
the prices below come from FOREX.com's feed (TradingView) and our corrected candles.

**Gold long, 18 September 2025.** Entry about 3655.7 at 10:10 Amsterdam, after the London open swept the FOMC low
(3645.8) to 3633.5. His stop, about 3626.8, sits on the low of 15 September (3626.69 on FOREX.com), the daily candle
that made the zone, about $7 under that morning's sweep. Target 3706.6, just under the FOMC high (3707.65). R:R 1.76.
The bot saw the same long at 10:00 (1D zone 3626-3674, 1H balance shift; entry 3658.78, stop 3633.49 on the sweep
low, target 3685.34, R:R 1.05) and refused it: gold needs the 1H aligned, and the 1H read the 06:00 UTC close under
the FOMC low as a break down. The dip to 3627.47 at 15:43 would have stopped the bot's version; his stop held by
about $1 and his target filled on 22 September.

**Gold long, 12 August 2025.** Price sat at the top of the daily gap 3314.7-3344.75 that the NFP candle of 1 August
left. The session lows were swept to about 3336 at 13:35 Amsterdam; he bought about 3345.7 at 13:41, stop $8.04
lower (at the tip of the sweep wick), target $13.10 higher (R:R 1.63). The CPI spike at 14:30 reached it; his
positions closed at 3357.85 and 3355.71. The bot had no trade: the gap is no zone for the code (the NFP candle closed
through no daily high, so there is no X), the 4H zone of that move was 64 candles old, and only the monthly and
weekly were bullish (daily 50/50, 4H bearish, 1H 50/50).

**EURUSD long, 17 July 2025.** The US retail sales candle at 14:30 Amsterdam swept the 16 July low (1.1562, the
origin of the Powell spike) to 1.1557 and closed back up. Entry about 1.1586, stop 29.7 pips (0.3 pip under that
wick), target 17.9 pips (under the morning high), R:R 0.6; the target filled at 00:30. The bot: monthly, weekly
and daily bullish, 4H and 1H 50/50, so the 1H rule refused it; the news blackout (30 minutes either side) and the
1H shift its daily zone waits for would have kept it out as well, and 0.6 is under EURUSD's minimum R:R of 1.0.

**His trade-plan board** (DV-Institute): bias, then only POIs in the bias direction, then "POI in een POI = trade
pas plaatsen bij een aantrekkelijke RR", then the entry (monthly POI at least a 4H shift, weekly 1H, daily 15m, 4H
5m, 1H 1m), then the exit (intraday and scalp, daily/4H/1H zones: break-even only after 4R, no partials; swing,
monthly/weekly: break-even after 2R, no partials), then TP / BE / SL and the journal. The code follows all of it
except the POI-in-a-POI step; its entry timeframes sit one step above the minimum the board names. The 1H rule
of the bias gate is data, not his words.

**Measured on 2024-2026** (the recent window; one trade at a time, guard off, 1 % risk; trades, win rate, R,
drawdown). New switches, all off in the profiles: `risk.stop_basis protector` with `stop_protection poi` (the
stop on the zone's P, his stop of 18 September), `bias.reclaim_candles` (a break taken back by the next close is a
sweep), `bias.shift_flips_balance` (a close beyond the far edge of the last gap turns the balance view),
`confirmation.poi_in_poi` (a zone counts only inside a zone of a higher timeframe on the same side):

| Variant | Gold | EURUSD | NAS100 | BTC |
|---|---|---|---|---|
| live profiles (`now`) | 84, 48 %, +26.1R, -7.2R | 31, 48 %, +11.2R, -4.0R | 45, 47 %, +21.5R, -5.0R | 142, 49 %, +53.1R, -11.9R |
| stop on the zone's P (`zp`) | 49, 49 %, +5.1R, -6.4R | 13, 46 %, +1.4R, -3.7R | 22, 50 %, +6.0R, -4.0R | 109, 60 %, +22.3R, -7.1R |
| a break taken back = sweep (`reclaim1`) | 63, 44 %, +14.7R, -10.5R | 25, 40 %, +3.8R, -5.0R | 39, 51 %, +23.0R, -4.0R | 108, 49 %, +33.7R, -9.0R |
| a balance shift turns the balance view (`shift`) | 71, 52 %, +24.6R, -6.2R | 27, 41 %, +5.0R, -6.2R | 41, 46 %, +20.6R, -6.0R | 136, 52 %, +61.7R, -10.3R |
| both (`bias2`) | 58, 47 %, +10.8R, -6.3R | 25, 60 %, +19.8R, -3.0R | 32, 56 %, +25.6R, -3.0R | 103, 49 %, +28.4R, -9.9R |
| both + stop on the zone's P (`bias2_zp`) | 36, 44 %, -0.8R, -6.1R | 11, 73 %, +11.5R, -1.0R | 18, 61 %, +10.1R, -2.0R | 78, 64 %, +23.6R, -5.0R |
| bias M+W+D only (`htf`) | 72, 46 %, +20.1R, -9.5R | 16, 44 %, +4.6R, -6.9R | 55, 33 %, -4.8R, -12.3R | 79, 44 %, +34.7R, -11.6R |
| bias 3 of 5, book combos, no 1H rule (`book`) | 88, 47 %, +20.1R, -10.8R | 41, 34 %, +1.2R, -8.1R | 69, 35 %, +2.3R, -13.3R | 110, 47 %, +41.4R, -13.0R |
| POI in een POI (`pip`) | 49, 53 %, +19.2R, -6.0R | 21, 38 %, +3.8R, -4.0R | 17, 41 %, +2.2R, -5.5R | 95, 46 %, +25.7R, -7.4R |
| M+W+D + POI in een POI (`htf_pip`) | 30, 53 %, +12.4R, -4.0R | 13, 46 %, +3.3R, -4.9R | 24, 29 %, -6.1R, -8.8R | 53, 43 %, +26.3R, -7.6R |

- His stop on the zone's P saved the trade of 18 September, and loses as a rule on all four markets: the wider stop
  lowers the R:R, fewer setups pass the minimum, and the winners pay less. On the same trades a stop 1.25 times as
  wide costs EURUSD 12.8R -> 9.0R and NAS100 19.4R -> 12.9R (`scripts/trade_paths.py`).
- A bias read on the higher timeframes alone (the A+ month+week+day, or the book's 3 of 5 without the 1H rule) is
  worse on all four. The 1H rule is the check that the lower timeframe has turned his way; without it the entries
  come while the 1H still runs against them (NAS100 33 % won).
- POI in een POI removes more good trades than bad ones; on gold it raises the win rate (53 %) and the R per trade,
  not the total.
- The bias switches help EURUSD and NAS100 together (`bias2`) and BTC alone (`shift`), hurt gold, and on EURUSD each
  switch alone is worse than none. That pattern can be noise; the 2017-2023 check (BTC 2020-2023) decides.

Entries far from the zone, on the four live ledgers of 2024-2026 (302 trades; how far the entry lies outside the zone,
in zone heights): inside 82 trades, 43 %, +38.4R; up to half 154, 50 %, +52.9R; half to one 47, 57 %, +24.7R; more
than one 19, 37 %, -4.1R (17 of the 19 on 1H zones). His "op de POI, niet er vanaf" holds for the far ones only.

**The 2017-2023 check (BTC 2020-2023) of the bias switches:**

| Market | Live profile | With the switches |
|---|---|---|
| EURUSD 2017-06 to 2023 | 74 trades, 30 %, -2.3R, drawdown -13.1R | both: 45, 31 %, -5.8R, -8.9R |
| NAS100 2017-03 to 2023 | 114, 36 %, +23.6R, -9.9R | both: 68, 28 %, -16.3R, -20.4R |
| BTC 2020-06 to 2024-01 | 152, 41 %, -11.2R, -12.5R | shift: 178, 35 %, -37.6R, -38.0R |

The gains of 2024-2026 do not hold before: on NAS100 the switches turn +23.6R into -16.3R, on BTC -11.2R into -37.6R.
Not taken; the switches stay in the code, off. Every variant that looks better on the recent window gets this check
before it goes into a profile.

**Entries at the zone, and the price gap as a zone** (2024-2026, then 2017-2023 / BTC 2020-2023 for what looked better):

| Variant | Gold | EURUSD | NAS100 | BTC |
|---|---|---|---|---|
| live profiles | 84, 48 %, +26.1R, -7.2R | 31, 48 %, +11.2R, -4.0R | 45, 47 %, +21.5R, -5.0R | 142, 49 %, +53.1R, -11.9R |
| entry at most one zone height outside (`risk.max_entry_outside 1.0`) | 80, 49 %, +28.9R, -7.2R | 29, 48 %, +11.0R, -4.0R | 41, 49 %, +22.7R, -4.0R | 140, 49 %, +50.9R, -12.3R |
| entry inside the zone only (`entry_outside_zone false`) | 26, 38 %, +5.3R, -6.0R | 13, 23 %, -4.9R, -7.0R | 13, 31 %, -1.6R, -4.0R | 67, 42 %, +37.5R, -10.8R |
| a gap without liquidity taken is a zone (`structure.poi_gap_zones`) | 113, 47 %, +35.7R, -11.9R | 40, 45 %, +15.3R, -5.0R | 63, 44 %, +25.0R, -6.5R | 181, 48 %, +59.3R, -13.7R |
| 2017-2023 live profiles | 201, 37 %, +3.6R, -27.6R | 74, 30 %, -2.3R, -13.1R | 114, 36 %, +23.6R, -9.9R | 152, 41 %, -11.2R, -12.5R |
| 2017-2023 entry cap | 194, 36 %, +0.1R, -28.3R | 70, 29 %, -5.3R, -13.5R | 112, 34 %, +17.9R, -12.2R | 146, 42 %, -8.5R, -12.5R |
| 2017-2023 gap zones | 247, 36 %, +8.4R, -25.5R | 103, 31 %, -0.4R, -14.1R | 163, 36 %, +22.7R, -11.9R | 188, 42 %, -6.8R, -19.6R |

The entry cap loses its small gain before 2024. The gap zones are the first variant that adds R in both periods (gold,
EURUSD, BTC; NAS100 level before 2024), with 25-45 % more trades. The challenge replay (`scripts/risk_steps.py`, the
four markets, two open, 1.5 % with the steps, 0.10R haircut) says what that does to an FTMO account:

| 2024-2026 | Funded | Failed | Median days | Funded account lost within 12 months |
|---|---|---|---|---|
| live profiles | 81 % | 19 % | 148 | 13 % |
| gap zones on all four | 69 % | 31 % | 128 | 32 % |
| gap zones on gold only | 70 % | 30 % | 135 | 54 % |
| gap zones on EURUSD and NAS100 | 81 % | 19 % | 160 | 8 % |
| live profiles at 1 % (steps -3:0.75, -6:0.5) | 90 % | 10 % | 242 | 11 % (0.75 %) |
| gap zones at 1 % | 71 % | 29 % | 178 | 21 % (0.75 %) |

On 2018-2023 the live profiles pass from 14 % of the starts, gap zones on EURUSD and NAS100 from 13 %, on all four
from 6 %. More trades at a slightly lower R a trade fail more challenges: the total R rises, the path to +10 % before
-10 % gets worse. Not taken for the FTMO set; the switch stays in the code, off. Max decided on the bias switches:
not taken.

**The 08:00 start and the news filter** (Dorus entered two of the three trades between 08:10 and 08:20, and one ten
minutes after US retail sales; 2024-2026, then 2017-2023 where it looked better):

| Variant | Gold | EURUSD | NAS100 | BTC |
|---|---|---|---|---|
| live profiles (09-11, 13-17; no entry 30 minutes either side of high-impact news) | +26.1R | +11.2R | +21.5R | +53.1R |
| windows 08-11, 13-17 | 92, 45 %, +17.7R, -13.5R | 40, 50 %, +15.0R, -5.0R | 49, 47 %, +24.1R, -6.0R | 159, 49 %, +42.7R, -14.9R |
| 2017-2023 windows 08-11, 13-17 | - | 86, 30 %, -3.7R (live -2.3R) | 132, 33 %, +7.9R (live +23.6R) | - |
| news blackout 30 before, 5 after | 85, 47 %, +25.1R | 28, 46 %, +8.5R | 46, 46 %, +18.0R | 148, 50 %, +54.1R |
| no news filter | 90, 46 %, +23.9R | 28, 46 %, +8.5R | 48, 44 %, +16.5R | 153, 50 %, +53.9R |

The 08:00 hour adds R on EURUSD and NAS100 in 2024-2026 and loses it before (NAS100 +23.6R -> +7.9R). The news filter
earns its keep on the three markets with US news; BTC does not care. Both stay as they are.

**What stands after the day.** None of the readings taken from his trades and his board beat the live profiles on
both periods and on the FTMO replay. His stop under the zone's P, the higher-timeframe bias without the 1H, POI in een
POI, the bias switches, entries at the zone only, the 08:00 hour and a shorter news blackout were each worse on at
least one of the three checks. The gap zones add R on both periods and fail more FTMO challenges. The profiles stay.

## Gold without the veto (6 October): into the profile

The monthly and weekly veto on gold (`bias.no_trade_against [1M, 1W]`, 5 October) was chosen on the 2023-2026 candles
before the clock correction. On the corrected candles with the current gold profile it costs trades and R on both
periods (one trade at a time, guard off, 1 % risk; trades, win rate, R, drawdown):

| Gold | With the veto (5 October) | Without |
|---|---|---|
| 2024-2026 | 84, 48 %, +26.1R, -7.2R | 105, 48 %, +32.3R, -9.2R |
| 2017-2023 | 201, 37 %, +3.6R, -27.6R | 319, 39 %, +8.8R, -22.6R |

Without the veto gold keeps every trade it had and adds 21 in 2024-2026 (+6.2R: 2024 +0.2, 2025 +1.3, 2026 +4.6).
FTMO challenge replay (`fast_sim`: the four markets, two open, 0.10R a trade, BTC at FTMO margin, the guard's day and
total limits; every day a start), share of starts:

| Starts | Rules | Set | Within 28 days | Within 56 days | Passed | Failed |
|---|---|---|---|---|---|---|
| Feb 2024 - Mar 2026 | 2-step, 2 % | with the veto | 1 % | 4 % | 53 % | 0 % |
| | | without | 1 % | 3 % | 53 % | 0 % |
| | 1-step, 1.25 % | with the veto | 2 % | 6 % | 69 % | 0 % |
| | | without | 2 % | 13 % | 69 % | 0 % |
| Jan 2018 - Jun 2023 | 2-step, 2 % | with the veto | 0 % | 2 % | 4 % | 4 % |
| | | without | 0 % | 4 % | 7 % | 3 % |
| | 2-step, 1.5 % | with the veto | 0 % | 0 % | 8 % | 0 % |
| | | without | 1 % | 3 % | 13 % | 0 % |

**Taken (Max, 6 October: "Ja aanzetten maar we doen sws de 2 step verificatie"):** `no_trade_against: []` in
`config/dorus_live_gold.yaml`; EURUSD and NAS100 keep their weekly veto (without it 5 and 6 more trades, -2.7R and
-0.2R). The FTMO account runs the 2-step challenge. Before 2024 the same four markets pass that challenge from 4-13 %
of the starts: the edge of 2024-2026 is the recent market's, not a constant.

## A month on 100,000 (6 October)

Each calendar month from February 2024 to September 2026 starts at 100,000; the live profiles' ledgers of 2024-2026
are combined under two open trades (`scripts/portfolio.py`); the stake is 1.5 % of the balance, 1.0 % from -3 % and
0.5 % from -6 % under the month's start; a -4 % day stops the day and -8 % the month; every trade pays 0.10R for
costs and slippage. BTC is sized as an FTMO account allows it (crypto 1:2, margin at most 45 % of equity, so a
notional of at most 0.9 times the balance): 129 of its 142 trades get a smaller stake and its +53.1R becomes +9.6R
in 1.5 % units. As backtested, two BTC trades of June 2026 (+23.9R and +11.8R on stops of 0.2 %) made that month
+80 % - not a size a live account could hold.

| Account | Average month | Median | Best | Worst | Positive months | Last 12 months, average |
|---|---|---|---|---|---|---|
| EURUSD + gold (the demo) | +1,160 | +747 | +18,002 | -6,430 | 18 of 32 | +2,864 |
| EURUSD + gold + NAS100 | +1,912 | +998 | +16,055 | -6,982 | 19 of 32 | +4,111 |
| EURUSD + gold + NAS100 + BTC at FTMO margin | +1,691 | +1,085 | +15,652 | -7,258 | 19 of 32 | +4,314 |

Months without a trade count as zero. 2026 carries the last twelve months; on 2018-2023 the same profiles were weak
(the challenge replay passed from 14 % of the starts), so the recent months are no promise.

**On 10,000 and at other stakes** (the same months; EURUSD + gold + NAS100 + BTC at FTMO margin; the challenge
replay with these four ledgers and the funded account at its own stake):

| Challenge stake (steps) | Average month on 10k | Median | Worst | Last 12, average | Challenge funded | Median days |
|---|---|---|---|---|---|---|
| 1.0 % (-3:0.75, -6:0.5) | +109 | +113 | -700 | +293 | 91 % | 255 |
| 1.5 % (-3:1.0, -6:0.5), live | +169 | +108 | -726 | +431 | 90 % | 226 |
| 2.0 % (-3:1.0, -6:0.5) | +236 | +141 | -768 | +555 | 89 % | 222 |
| 3.0 % (-3:1.5, -6:0.5) | +303 | -108 | -783 | +828 | 35 % | 160 |

Funded account: 1 % with -3:0.5 lost within a year from 9 % of the starts and pays 0.8 % of the account a month;
1.5 % with -3:1.0, -6:0.5 from 14 % and 1.1 %; 2 % the same as 1.5 % (the steps cut it). With BTC sized as FTMO's
margin allows, the 1.5 % challenge passes from 90 % of the starts against 81 % with BTC at full size.

## Setup B for the FTMO 1-Step (6 October)

Nearly all of the R comes from a few large trades: of 317 trades on the four live profiles in 2024-2026, the 19 of
3R or more made +117R of the +118.9R. A challenge is passed by catching one or two of them without hitting a loss
limit first, so setup B weights the stake by the quality of the zone and keeps the trades that make the big ones.
Every change below was measured on 2024-2026 and on 2017-2023 (BTC June 2020 - January 2024); one trade at a time,
guard off, 1 % units; trades, win rate, R, largest drawdown.

| Change | Market | 2024-2026 | 2017-2023 | Taken |
|---|---|---|---|---|
| Re-entry after a stop in the same visit, and a second visit (`one_trade_per_visit: false`, `allow_retest: true`) | EURUSD | 38, 50 %, +15.8R, -5.0R (was 31, 48 %, +11.2R, -4.0R) | 90, 34 %, +5.3R, -15.7R (was 74, 30 %, -2.3R, -13.1R) | yes |
| | gold | 95, 45 %, +20.9R (was 105, 48 %, +32.3R) | | no |
| | NAS100 | 52, 44 %, +19.8R (was 45, 47 %, +21.5R) | | no |
| | BTC | 228, 46 %, +47.2R, -17.1R (was 142, 49 %, +53.1R, -11.9R) | | no |
| Limit 25 % of the way back toward the stop, 4 hours (`limit_entry_fraction: 0.25`) | NAS100 | 36, 42 %, +27.9R, -5.0R (was 45, 47 %, +21.5R, -5.0R) | 96, 28 %, +33.6R, -10.6R (was 114, 36 %, +23.6R, -9.9R) | yes |
| | NAS100, 50 % | 29, 28 %, +23.1R, -6.0R | | no |
| | EURUSD | 26, 46 %, +19.9R, -4.0R | running | not yet |
| Break-even at 2R instead of 4R | NAS100 | 45, 44 %, +20.6R | 114, 36 %, +27.6R | no (mixed) |
| | EURUSD | 31, 48 %, +12.2R | running | not yet |
| | gold | 105, 48 %, +34.3R, -8.2R | running | not yet |
| Swing trades on 1W/1D zones (a separate layer) | NAS100 | 13, 31 %, +7.6R, -2.0R | running | not yet |
| | gold | 7, 29 %, -2.6R | 20, 25 %, +3.4R, -9.0R | no |
| A second trade on a market already in a trade (`open2b`) | NAS100 | 47, 45 %, +19.5R | | no |
| | gold | 90, 47 %, +24.2R | | no |
| Without the 2R cap on BTC's target | BTC | 130, 34 %, +48.3R, -16.8R | 146, 32 %, -6.0R, -19.4R | no |

The quality of the zone: a 4H zone on EURUSD, gold or NAS100 won 47 % at +0.49R a trade in 2017-2023 and 64 % at
+1.04R in 2024-2026, well above the markets' other zones on both periods. It risks twice the stake
(`zone_risk_multiplier: {4H: 2.0}`). BTC made its R in a few trades of 2026 (2024 +2.9R, 2025 -2.8R, 2026 +52.9R;
2020-2023 -11.2R) and trades at half the stake (`stake_multiplier: 0.5`): it keeps its large trades in the account
at a cost a challenge can carry. The target fallbacks of 6 October (a target in place of one under the minimum R:R)
added R on 2024-2026 and lost it on 2017-2023 for NAS100, gold and EURUSD; they stay off.

FTMO challenge replay of the combined ledgers (two open, 0.10R a trade for costs, BTC at FTMO margin, the guard's
day and total limits counted where the guard stops trading), starts February 2024 - September 2025:

| Setup | Within 3 months | Within 6 | Within 12 | Failed | Median |
|---|---|---|---|---|---|
| 2-Step, 1 %, 4H x2, without BTC | 2 % | 38 % | 81 % | 0 % | 190 days |
| 2-Step, 1 %, 4H x2, BTC half | 7 % | 39 % | 73 % | 0 % | 173 days |
| **1-Step, 1 %, 4H x2, BTC half (setup B)** | **25 %** | **52 %** | **59 %** | **0 %** | **103 days** |
| 1-Step, 2 %, BTC full | 31 % | 44 % | 47 % | 0 % | 62 days |
| 2-Step, 2 %, BTC full (the FTMO set before) | 25 % | 38 % | 42 % | 0 % | 84 days |

**Taken (Max, 6 October: "oke top doen we dat go"):** setup B. `RISK=1.0` and `PRODUCT=ftmo_1step` in
`scripts/ftmo_local.bat`: the guard stops at a -2.9 % day and 9 % under the highest day-start balance (FTMO 1-Step:
3 % and 10 % trailing); 4H zones x2 on EURUSD, gold and NAS100; BTC at half; EURUSD re-entries; the NAS100 limit
entry (in the live runner, MT5 and paper, since the evening of 6 October). The replay starts end in September 2025, so the
12-month column of the last starts reaches into 2026: the recent market is in it, and before 2024 the same markets
passed far less often.

## 1-Step or 2-Step (6 October, evening)

The same setup B ledgers (EURUSD with re-entries, gold without the veto, NAS100 with the limit entry, BTC; two open,
0.10R a trade for costs, BTC at FTMO margin), stakes as live (a 4H zone on EURUSD, gold and NAS100 twice the base,
BTC half, the ladder -3 % -> base 1.0, -6 % -> 0.5), the bot's guard on the worst case, the products' own rules
(2-Step: +10 % then +5 %, at least 4 trading days, 5 % a day, 10 % static; 1-Step: +10 %, the best-day rule, 3 % a
day, 10 % under the highest day-start balance). Share of starts funded within the time, "failed" = a product limit
broken; the rest stalled at the guard's floor or ran out of data:

| Product | Base | Bot's guard | Within 3 months | 6 | 12 | Failed | Median | 2018-2022 starts: 12 months |
|---|---|---|---|---|---|---|---|---|
| 1-Step | 1.0 % | -2.9 % day, -9 % from the day high | 26 % | 52 % | 59 % | 0 % | 97 days | 25 % |
| 1-Step | 1.5 % | the same | 41 % | 61 % | 63 % | 0 % | 74 days | 13 % |
| 2-Step | 1.0 % | -4 % day, -8 % from the start | 15 % | 43 % | 61 % | 0 % | 138 days | 20 % |
| 2-Step | 1.0 % | -4 % day, -9.5 % | 15 % | 43 % | 68 % | 0 % | 158 days | 23 % |
| 2-Step | 1.25 % | -4 % day, -9.5 % (live) | 25 % | 43 % | 64 % | 0 % | 129 days | 20 % |
| 2-Step | 1.5 % | -4.9 % day, -9.5 % | 19 % | 42 % | 60 % | 0 % | 138 days | 16 % |
| 2-Step | 2.0 % | -4.9 % day, -9.5 % | 20 % | 26 % | 38 % | 19 % | 124 days | 7 % |

The 2-Step is not faster at any stake: it needs +15 % over two phases. At 1 % it is funded a little more often within
a year, and its funded account keeps 5 % a day and a static 10 % (the 1-Step's stays at 3 % and trailing). More
stake does not buy speed: at 2 % (4 % on a 4H zone) two losses on one day break the 5 % (19 % of the starts). The
day limit of the guard (4.0, 4.5 or 4.9 %) made no difference at 1-1.25 %; the floor did (9.5 % against 8 %).

In 14 days (the free trial, 2-Step guard, 1.25 %): a median of 4 trades (3-6), the account after 14 days at a median
of +0.0 % in 2024-2026 (half of the windows between -1.7 % and +3.8 %, +10 % reached in 9 %) and +1.7 % in 2026 (22 %);
below -5 % in 2 %. Trades a month by market: BTC 4.4, gold 3.1, EURUSD 1.2, NAS100 1.1.

**Taken (Max, 6 October, evening: the 2-Step, "dan duurt het maar langer"):** `PRODUCT=ftmo_2step` with `RISK=1.25`;
the 2-Step guard's floor goes from 8 % to 9.5 % from the start, its day stays at 4 %.

## Stake near the target, EURUSD limit, a true swing layer (6 October, evening)

Setup B on the 2-Step (base 1.25 %, a 4H zone on EURUSD, gold and NAS100 twice, BTC half), the same replay as above;
starts every 3 days February 2024 - September 2025 and every 6 days 2018-2022. "Half near the target" =
`risk.target_protect_pct`: within that many % of the phase's target (`risk.target_pct`: 10, then 5) a trade risks
half of the base (the multipliers on top); "late steps" = -5 % -> 0.75, -7 % -> 0.5 instead of -3 % -> 1.0, -6 % -> 0.5.

| Plan | Within 3 months | 6 | 12 | Failed | Median | 2018-2022 starts: 12 months |
|---|---|---|---|---|---|---|
| Rules now | 26 % | 43 % | 63 % | 0 % | 126 days | 20 % |
| Late steps, half in the last 2 % | 20 % | 51 % | 64 % | 0 % | 116 days | 23 % |
| Half in the last 4 % | 15 % | 41 % | 74 % | 0 % | 159 days | 22 % |
| 1.0 %, late steps, half in the last 3 % | 13 % | 37 % | 76 % | 0 % | 192 days | 23 % |
| Without BTC: early steps, half in the last 3 % | 12 % | 40 % | 88 % | 0 % | 218 days | 17 % |

Three open trades instead of two changed nothing. A lower stake near the target passes more challenges on both
periods and slower: a losing run close to +10 % no longer undoes the phase.

**EURUSD with re-entries and the limit 25 % back toward the stop:** 2024-2026 31 trades, 45 %, +24.6R, -5.0R (re-entries
alone: 38, 50 %, +15.8R, -5.0R); 2017-2023 85 trades, 26 %, +7.3R, -15.0R (90, 34 %, +5.3R, -15.7R). More R on both, a
lower win rate on both; in the replay (rules now) funded within a year 72 % against 63 % on the recent starts but
14 % against 20 % on 2018-2022. Not taken: the challenge needs the win rate more than the R. (The limit alone on the
old profile: 2017-2023 68 trades, 22 %, -1.3R against 74, 30 %, -2.3R.)

**A true swing layer** (only 1M, 1W and 1D zones, `scalp_poi_timeframes: []`): NAS100 2024-2026 3 trades, -1.0R;
EURUSD 2 trades, -1.0R. Too few trades to matter. The first swing runs (earlier this evening) set only
`poi_timeframes`, so in scalp mode they traded 1H and 4H zones with the swing targets (a median hold of 3 hours): not a
swing layer, and not used.

## The last three years (6 October, evening): into the profiles

**Max's rule from here:** intraday changes are judged on 2024-2026 only ("echt niet voor scalp" on the older years).
Every 2024-2026 variant that differs from a live profile in a few settings was screened (about 160 ledgers): its R in
2024, 2025 and 2026, and the 2-Step replay (1.25 %, 4H zones x2, BTC half, no half stake near the target) with its
ledger in place of the live one. The winners combined (two open, 0.10R a trade for costs, BTC at FTMO margin):

| Set | Trades a month | R a trade after costs | Average month | Median month | 2026 starts: within 6 weeks / 2 months / 3 months | 2024-25 starts: within 3 months / 12 months / lost |
|---|---|---|---|---|---|---|
| Live before | 9.8 | +0.28R | +3.4 % | +2.3 % | 27 % / 43 % / 65 % | 26 % / 63 % / 29 % |
| **EURUSD limit 25 %, gold 2R fallback target, BTC shift** | 10.6 | +0.40R | +5.0 % | +4.2 % | **34 % / 53 % / 70 %** | **43 % / 92 % / 8 %** |
| the same, BTC at a $45 FTMO spread | | | | | 26 % / 44 % / 62 % | 43 % / 94 % / 6 % |
| plus NAS100 08:00-20:00 | 11.1 | | +4.9 % | | 39 % / 55 % / 70 % | 38 % / 87 % / 13 % |

"Lost" = an FTMO limit broken or the guard's floor reached (the challenge stalls). Per market, 2024-2026 (2024 / 2025 /
2026), against the profile before:

| Change | Trades, won, R | Per year | Before |
|---|---|---|---|
| EURUSD: limit 25 % back toward the stop, 4 hours (`limit_entry_fraction: 0.25`) | 31, 45 %, +24.6R | +1.7 / +16.7 / +6.2 | 38, 50 %, +15.8R (-1.4 / +9.9 / +7.3) |
| Gold: a 2R target where none reaches the minimum R:R (`tp_fallback: fixed`, `tp_fallback_rr: 2.0`) | 138, 51 %, +63.1R | +27.0 / +25.8 / +10.4 | 100, 48 %, +32.1R (+9.3 / +7.6 / +15.1) |
| BTC: the balance turns on a close beyond the last gap's far edge (`shift_flips_balance: true`) | 136, 52 %, +61.7R | +3.7 / +8.0 / +50.1 | 142, 49 %, +53.1R (+2.9 / -2.8 / +52.9) |

For the record, the same three on the older years: EURUSD 2017-2023 +7.3R against +5.3R; gold 382 trades, +3.4R,
-32.5R drawdown against 319, +8.8R, -22.6R; BTC 2020-2023 178 trades, -37.6R, -38.0R drawdown against 152, -11.2R,
-12.5R. Measured and not taken on 2024-2026: wider hours (08:00-20:00) on gold (164 trades, +16.9R against +32.3R),
EURUSD (64, +12.4R against +15.8R) and BTC (206, +48.5R against +53.1R); NAS100 08:00-20:00 (51 trades, +32.6R
against +28.9R, better in each year) left out because with it more 2024-25 challenges stalled (13 % against 8 %);
BMS/BOS entries on EURUSD (73 trades, +13.3R, -11.8R drawdown) and NAS100 (73, +31.5R, more lost challenges).

**Taken (Max, 6 October, evening: "pak echt de laatste 3 jaar alleen en wat daar goed werkt en erbij kan ... en zorg
dat de kans hoog blijft dat we de challenge halen"):** the three changes above.

## Into the profiles (7 October)

Max, 7 October: "We kunnen vanavond alle verbeterpunten erbij doen ... focus vooral op de tests en ons systeem en dat
we wel genoeg doen op een dag". Everything below: February 2024 to September 2026 (BTC to 4 October), the 24 h touch
rule in place, FTMO's measured costs (6 October spreads, the commission per market), per market one open trade,
halves H1 = February 2024 - May 2025 and H2 = June 2025 - September 2026.

### The changes taken

| Market | Change | Trades | R after costs | Drawdown | Halves (change) | Before |
|---|---|---|---|---|---|---|
| EURUSD | a gap counts from a tenth of the median candle range (`structure.min_gap_fraction: 0.1`, was 0.2) | 28 | +31.2R | -2.9R | +0.0 / +4.2R | 30, +27.0R, -4.7R |
| NAS100 | the same | 38 | +37.3R | -4.0R | +0.8 / +3.7R | 31, +32.9R, -3.0R |
| Gold | three of five (was two), R:R floor 0.8 (was 0.5), break-even at +2R (was 4R) | 132 | +84.2R | -4.5R | +1.6 / +15.6R | 135, +66.9R, -6.6R |
| BTC | a broken P reads 50/50 until a new gap forms (`bias.balance_violation: neutral`, was the flip) | 89 | +60.8R | -4.0R | +6.0 / +6.6R | 112, +48.3R, -7.9R |

Each change was measured on all four markets; the markets not in a row lose with it (gaps: gold -24.7R, BTC -37.1R;
neutral: EURUSD -3.6R, NAS100 -14.8R, gold -9.2R).

The edited profile files themselves, run with the guard's limits off and one open trade, give the research ledgers
trade for trade: EURUSD 28 of 28, NAS100 38 of 38, gold 132 of 132, BTC 90 of 90, every R the same.

Together (two open, 1.25 %, 4H zones x2, BTC half, 0.10R a trade for slippage on top of the costs):

| Set | Trades a month | R a trade | Month average | Losing months | Worst month | 2026 starts funded within 6 wk / 2 mo / 3 mo | 2024-25 starts within 2 mo / 3 mo / lost |
|---|---|---|---|---|---|---|---|
| The 24 h set (the profiles of the 7 October morning; the live windows ran the set before it until the restart) | 9.6 | +0.47 | +5.7 % | 10 of 32 | -6.7 % | 40 / 59 / 77 % | 15 / 41 / 0 % |
| **With the four changes** | 9.0 | **+0.64** | **+6.6 %** | **9** | **-5.4 %** | 38 / **85** / **100 %** | **24 / 51** / 1 % |

Not taken on top (same replay): a third open slot (no change: three open at once almost never happens), GER40 as a
fifth market (2024-25 starts lost 7 % against 1 %), US500 (2024-25 faster, 2026 slower: 72 % against 85 % within two
months), BTC at a full stake (3-4 points faster in both periods, inside the noise; it stays at half).

### EURUSD: more trades (7 October, afternoon)

Max: EURUSD trades too seldom (the set above: 0.9 a month, 3 trades in April-September 2026). 91 EURUSD variants on
the set above (FTMO's costs, February 2024 to September 2026), each through the account replay. The lesson of most of
them: more EURUSD trades from a looser gate win 28-35 % of the time; the sum barely moves, the dips deepen and more
challenges fail. Not taken:

| Variant | Trades a month | R | 2024-25 challenge starts lost |
|---|---|---|---|
| Two of five with gold's 1D+1H and 4H+1H combinations | 2.7 | +39.0 | 3 % |
| No 1H requirement, two positions | 2.0 | +41.1 | 16 % |
| No weekly veto, two of five | 3.6 | +30.4 | 21 % |
| The previous high as the target, capped at 2R (BTC's rule) | 1.6 | +18.0 | |
| Wider hours (08-11, 08-18, 07-20, 13-20) | 1.1-1.7 | +16.8 to +25.5 | |
| 15m zones with 1-minute entries; 5m zones with 1-minute entries | 2.4; 3.4 | +15.0; +11.8 | |
| Fixed 1.5R / 2R / 3R targets | 1.6-1.8 | +13.8 / +6.4 / +1.4 | |
| A 4H zone confirmed on the 5m; a 1H zone on the 15m; any timeframe | 1.0; 0.4; 1.0 | +14.6; +8.8; +27.3 | |

One combination holds: **the daily and the hourly agreeing** ([1D, 1H] as a match, two of five). Its extra trades
earned in every period (2024-02..2025-05 14 trades +3.3R, 2025-06..2026-03 5 trades +1.6R, 2026-04..09 7 trades
+4.8R), where the 4H+1H ones lost (-3.5R, +2.5R, -1.0R). With it EURUSD trades 54 times (1.7 a month), 39 %, +40.9R
against 28, 46 %, +31.2R; halves +3.3 / +6.4R; April-September 2026 10 trades +5.6R against 3, +0.8R. At full stake
6 % of the 2024-25 challenge starts fail (1 % before), so those trades risk half
(`risk.combo_risk_multiplier: {1D+1H: 0.5}`, new). The account replay by that stake (EURUSD's trades only):

| Stake of the 1D+1H trades | 2026 starts within 6 weeks / 2 months | 2024-25 starts within 2 / 3 months | Lost |
|---|---|---|---|
| (without the combination) | 38 % / 85 % | 24 % / 51 % | 1 % |
| **0.5** | **41 % / 90 %** | **25 % / 50 %** | **1 %** |
| 0.75 | 41 % / 90 % | 27 % / 50 % | 3 % |
| 1.0 | 47 % / 89 % | 30 % / 45 % | 6 % |

The worst month is -5.0 % at each. **Taken at 0.5.** (A first replay put the three quarters on gold's 1D+1H trades as
well and read 1 % lost at 0.75; on EURUSD alone it is 3 %.)

The half stake falls on every trade the pair matches, 44 of the 54: the full combinations are tried before the scalp
combination, so 18 trades the 1D+4H+1H scalp combination took at full stake before read as 1D+1H now (the replay
above already counts them at half). With only the 26 new ones at half (and BTC at 3R, below): 2026 starts within
6 weeks 41 % against 37 %, 2024-25 starts lost 2 % against 1 %. Left as it is.

On top of it, the 15m zones: 77 trades (2.4 a month), +47.1R, both halves better, but the 2024-25 starts slow to 40 %
within three months (worst month -6.8 %, lost 2 % at a 0.6 or 0.75 stake); two positions on top: lost 3 %. Kept for later, as are 15m zones with two positions (49 trades, +35.8R,
the challenge unchanged) and two of five on NAS100 (+9 trades, +1.6R, April-September 2026 -2.0R).

Chance: of the ten variants best on February 2024 - March 2026, two to five were also better on April - September
2026 (`holdout.py`), so a single winner on the whole period means little; the daily-plus-hourly combination was
better on both.

### BTC: the previous high, capped at 3R (7 October, afternoon)

Max: "is een fixed btc doel wel slim ipv gewoon op de vorige high zetten?" BTC's target is the previous high (the low
for a sell); the cap only decides what happens when that high lies far: beyond the cap the nearest liquidity within
it, the far high when nothing nearer fits. On the BTC line of the table above (the neutral broken P, FTMO's costs):

| Cap | Trades | Won | R after costs | Drawdown | Halves |
|---|---|---|---|---|---|
| 2R (until the restart) | 89 | 62 % | +60.8R | -4.0R | +19.0 / +41.8R |
| 2.5R | 88 | 61 % | +59.2R | -4.0R | +21.1 / +38.1R |
| **3R** | 88 | 60 % | **+64.7R** | -4.0R | +21.6 / +43.1R |
| 4R | 88 | 57 % | +67.6R | -4.1R | +26.1 / +41.5R |
| none (always the previous high) | 86 | 47 % | +60.6R | -11.7R | +17.8 / +42.8R |

**Taken: 3R** (`risk.tp_max_rr: 3.0` in `config/dorus_live_btc.yaml`). The account replay of the set
(EURUSD's pair at half): an average month +7.2 % (+7.1 %), 2026 starts funded within 6 weeks 37 % (41 %), within
2 months 93 % (90 %), within 3 months 100 %; the 2024-25 starts unchanged (25 % / 50 %, 1 % lost); the worst month
-5.0 % at both. Between 2R and 4R the sum moves within the noise (2.5R lies below 2R); what the cap does is keep the
drawdown at -4R against -11.7R. 4R in the replay: the 2024-25 starts within 3 months 46 % against 50 %, the worst
month -5.5 %. 3R is the one with both halves above 2R, and it sends more trades to the previous high, his target.
The edited profile, run with the guard's limits off, gives the 3R ledger trade for trade (89 of 89, every R the same).

The other BTC variants on the same line, none taken (R against +60.8R): break-even at +2R or +1.5R (-2.5R, -1.5R),
a 24 h holding limit (-2.2R), stops of at least 150 USD (-6.2R), no scalp combination (-2.8R, drawdown -6.5R), gaps
from 0.15 or 0.25 of the median range (-14.0R, -11.9R), swing points of one or three candles (-62.0R, -6.9R), the
daily-plus-hourly pair (-6.5R), the week end as well (-16.6R), the stop behind the protector (-47.1R), other targets
(the impulse origin -24.2R, the pullback origin -2.7R, the nearest liquidity -24.9R, a look-back of 48 or 120 candles
-2.1R, -2.7R). A liquidity look-back of 40 and stops of at least 100 USD change no trade.

### June 2017 - 2023 for tonight's changes

Since 6 October the profiles are chosen on 2024-2026 (Max); the older years are for the record. Each change on the set
before it, FTMO's costs, halves split in September 2020 (BTC: June 2020 - 2023, split in March 2022):

| Market | Change | Before | After |
|---|---|---|---|
| EURUSD | the smaller gap | 71, +3.9R, -13.0R (+12.0 / -8.1R) | 82, -8.4R, -22.1R (+9.9 / -18.3R) |
| EURUSD | the daily-plus-hourly pair, on the smaller gap | 82, -8.4R | 136, +2.1R, -25.5R (+23.8 / -21.7R) |
| EURUSD | the pair without the smaller gap | 71, +3.9R | 120, +6.3R, -19.7R |
| NAS100 | the smaller gap | 82, +37.4R, -11.4R (+2.8 / +34.6R) | 82, +30.3R, -9.0R (-5.5 / +35.8R) |
| Gold | three of five, R:R floor 0.8, break-even at +2R | 375, -38.8R, -65.1R | 291, -41.6R, -62.9R |
| BTC | a broken P reads 50/50 | 157, -40.9R, -41.4R (-18.1 / -22.7R) | 136, -29.8R, -35.4R (-17.5 / -12.3R) |
| BTC | the cap at 3R (was 2R), on the neutral P | 136, -29.8R, -35.4R | 134, -29.9R, -40.3R (-24.7 / -5.2R) |

The smaller gap loses in these years on both markets that took it (EURUSD -12.3R, NAS100 -7.1R) and wins on
2024-2026 (+4.2R, +4.4R); the daily-plus-hourly pair wins in both periods on either gap. Gold has no edge in these
years with or without its changes, BTC none either (its commission scaled to the price of those years); the neutral
broken P helps there too.

### More trades, not more profit (7 October, afternoon)

Max: "kijk nog verder voor btc en eurusd ... nog meer verbeteren en meer trades doen". On tonight's set (FTMO's costs,
the account replay as above):

| Variant | Trades a month (market) | R after costs | Drawdown | Halves (change) | Replay: 2026 within 2 mo; 2024-25 within 3 mo; lost; worst month |
|---|---|---|---|---|---|
| (tonight's set) | | | | | 93 %; 50 %; 1 %; -5.0 % |
| EURUSD 15m zones (5m entries) at half the stake | 1.7 -> 2.4 | +31.4R -> +32.9R (at its stakes) | -5.2R -> -4.7R | +1.5 / +0.0R | 93 %; 49 %; 1 %; -5.7 % |
| BTC until 20:00 (09-11, 13-20) | 2.8 -> 3.6 | +64.7R -> +67.2R | -4.0R -> -5.2R | +0.3 / +2.2R | 90 %; 54 %; 1 %; -5.1 % |
| BTC until 22:00 | 2.8 -> 4.1 | +63.9R | -6.0R | -0.7 / -0.2R | 90 %; 58 %; 1 %; -5.0 % |
| BTC 08:00-22:00 | 2.8 -> 4.5 | +59.8R | -9.7R | | |
| Both the EURUSD 15m zones and BTC until 20:00 | 9.8 -> 11.3 (the set) | | | | 90 %; 46 %; 1 %; -5.7 % |
| NAS100 09-11, 13-20 | 1.2 -> 1.5 | +37.3R -> +38.4R | -4.0R -> -5.0R | +0.1 / +1.0R | 89 %; 58 %; 2 %; -5.1 % |
| NAS100 08:00-18:00 | 1.2 -> 1.7 | +26.8R | -9.3R | -4.6 / -6.0R | |

The extra trades earn next to nothing after costs, and the challenge replay is no faster with them. **Max: nothing extra
tonight.** The EURUSD 15m profile is ready (run with the guard's limits off it gives its research ledger trade for
trade, 77 of 77). Not more trades either: BTC with a second position at once (no trade changes: two BTC trades never
overlap), BTC re-entries after a stop (107 trades, -7.5R), a plain break of structure as BTC's confirmation
(107 trades, -15.0R), BTC's reclaim within 3 candles (58 trades, -32.8R), the sweep before the shift (52, -20.9R).

### The set of the 7 October restart

The four markets together, two open, 1.25 %, 4H zones x2, BTC half, FTMO's costs and 0.10R a trade for slippage,
February 2024 - September 2026:

| | Until the restart | From the restart |
|---|---|---|
| Trades a month | 10.6 | 9.8 |
| Won | 50 % | 51 % |
| R a trade | +0.34 | +0.63 |
| Average win / loss | +1.84R / -1.14R | +2.31R / -1.12R |
| Month average | +5.0 % | +7.2 % |
| Losing months (of 32) | 12 | 7 |
| Worst month | -9.1 % | -5.0 % |
| 2026 starts funded within 6 weeks / 2 months / 3 months | 30 / 48 / 65 % | 37 / 93 / 100 % |
| 2024-25 starts funded within 2 / 3 months | 16 / 39 % | 25 / 50 % |
| 2024-25 starts lost | 15 % | 1 % |

Per market (FTMO's costs, one open): EURUSD 1.0 trades a month +26.1R -> 1.7 a month +40.9R; gold +59.0R -> +84.2R;
NAS100 +28.9R -> +37.3R; BTC +38.7R with a -14.4R drawdown -> +64.7R with -4.0R.
