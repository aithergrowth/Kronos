# True execution costs on FTMO instead of the flat 0.10R (14 October 2026)

Angle: what every trade on the eight research ledgers really pays on FTMO (spread, commission, stop slippage), per
market and per trade, against the flat 0.10R the research subtracts; and the FTMO 2-Step replay with a cost per market.
Read-only on the repository. Scripts and outputs in `research/costs/`:

- `research/costs/cost_model.py`: the per-trade model on the eight ledgers (46 s); writes `costed/<ledger>.csv` (the
  ledger plus `cost_<scen>`, `extra_<scen>`, `extra_mech_<scen>`, `comm_R_<scen>`, `slip5`, `slip1`, `D`, `h_open`,
  `h_close`), `cost_summary.csv`, `cost_by_hour.csv`, `slippage.csv`, `tables.md` (every table in full).
- `research/costs/cost_cuts.py`: stop-size quartiles after true costs, a cost-threshold refusal rule, the commission
  share, the R:R after costs (`cuts.md`, `refusal_rule.csv`).
- `research/costs/challenge_sim_costs.py`: `aca/challenge_sim_btc.py` extended to a cost per market and per trade
  (`sim_<scenario>.out`, one file a scenario; the no-BTC runs in `sim_base_nobtc.out`, `sim_pess_nobtc.out`).

## 1. The model

For every trade, in the instrument's price units, divided by the initial stop distance D = |entry - stop| (the ledger
sizes exactly on it: risk_amount = lots x D x value, the identity holds to 4 decimals on all 1,020 trades):

    cost_R = (spread at entry + spread at a non-target exit + commission + gap through the stop) / D

- a target exit fills at the limit (no spread crossed); a stop, break-even or time exit is a market exit and pays a
  second spread (the task's convention; the one-spread variant "mech" below is what MT5 mechanics give: a long pays
  the spread at entry and exits on the bid, a short enters on the bid and pays it at the exit, stop or target alike);
- commission, round turn: forex $3 a lot (0.3 pip on EURUSD), gold $3 a lot ($0.03 an ounce = 0.3 pip), indices none,
  crypto 0.0325 % a side of the notional (0.065 % x entry price, per BTC); the pessimistic scenario uses the README's
  FTMO figures instead (forex $2.50 a side = 0.5 pip; metals 0.0007 % a side of the volume);
- gap through the stop: the 5m candle at `closed_at` (the exit candle's open time) opening beyond the stop; the first
  1m candle through the stop (`fix_src/*_1min.csv`, `btc_data/BTCUSD_1min.csv`) as the finer check;
- the hour is Amsterdam, from the UTC ledger stamps.

What the ledger R already carries (`.provenance.json`, `kronos_trader/execution/paper.py`): one spread a trade at the
backtest's width (EURUSD 1.0 pip, gold 2.0 pips, NAS100 1.5 points, BTC $15; bid candles, ask = bid + spread), the gap
fill at the 5m open, no commission. So the figure to set against the flat 0.10R is the **extra**:

    extra_R = cost_R(true) - (modelled spread + 5m gap) / D        sum R true = sum (r - extra_R)

Scenarios (spread / commission): **base** EURUSD 0.1 pip / $3, gold 3.4 pips / $3, NAS100 1.5 pt / none, BTC $15 /
0.065 %; **mid** gold 3.7, NAS100 3, BTC $30; **pess** EURUSD 0.2 pip / $5, gold 3.7 / 0.0014 % of the notional,
NAS100 5, BTC $45 / 0.065 %. EURUSD and gold are measured (6-7 October, `mt5-spreads`); NAS100 and BTC are not.

## 2. Per market: the cost a trade, and the sum after true costs against the flat 0.10R

2024-01 .. 2026-09 (the live set's research ledgers, 1 % risk, guard off):

| Market (n) | Scenario | cost_R p50 / p90 / max | > 0.10R (full) | extra_R p50 / p90 | > 0.10R (extra) | sum R raw | flat 0.10 | **true** | true, one spread | flat - true |
|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD (47) | base | 0.051 / 0.083 / 0.08 | 0 % | -0.070 / -0.027 | 0 % | +44.2 | +39.5 | **+47.1** | +47.4 | -7.5R (flat too harsh) |
| EURUSD | pess | 0.091 / 0.150 / 0.15 | 45 % | -0.017 / -0.007 | 0 % | | | **+45.2** | +45.8 | -5.7R |
| XAUUSD (143) | base | 0.062 / 0.176 / 0.42 | 28 % | +0.033 / +0.127 | 16 % | +86.1 | +71.8 | **+78.6** | +82.6 | -6.7R |
| XAUUSD | mid | 0.067 / 0.191 / 0.45 | 30 % | +0.039 / +0.142 | 18 % | | | +77.6 | +82.0 | -5.8R |
| XAUUSD | pess | 0.068 / 0.191 / 0.45 | 31 % | +0.040 / +0.142 | 19 % | | | **+77.3** | +81.7 | -5.5R |
| NAS100 (43) | base | 0.068 / 0.197 / 0.25 | 37 % | +0.020 / +0.099 | 9 % | +37.2 | +32.9 | **+35.7** | +37.2 | -2.8R |
| NAS100 | mid (3 pt) | 0.137 / 0.394 / 0.50 | 72 % | +0.094 / +0.296 | 49 % | | | +31.7 | +34.7 | +1.2R |
| NAS100 | pess (5 pt) | 0.228 / 0.657 / 0.83 | 86 % | +0.194 / +0.558 | 77 % | | | **+26.4** (+29.8 after the cap refuses 9) | +31.4 | +6.5R (flat too lenient) |
| BTCUSD (89) | base ($15) | 0.154 / 0.370 / 0.69 | 80 % | +0.123 / +0.314 | 69 % | +70.6 | +61.7 | **+56.5** | +58.1 | +5.2R |
| BTCUSD | mid ($30) | 0.207 / 0.489 / 0.97 | 88 % | +0.173 / +0.418 | 84 % | | | +51.1 | +54.2 | +10.6R |
| BTCUSD | pess ($45) | 0.257 / 0.632 / 1.25 | 92 % | +0.219 / +0.546 | 89 % | | | **+45.6** (+24.5 after the cap refuses 5) | +50.4 | +16.1R |

2017 .. 2023 (BTC 2020-06 .. 2023), the same model:

| Market (n) | Scenario | cost_R p50 / p90 | > 0.10R (full) | extra_R p50 / p90 | sum R raw | flat 0.10 | **true** | cap refuses (n, flat R) | flat - true |
|---|---|---|---|---|---|---|---|---|---|
| EURUSD (97) | base | 0.057 / 0.083 | 2 % | -0.067 / -0.034 | +8.5 | -1.2 | **+14.5** | 0 | -15.7R |
| EURUSD | pess | 0.103 / 0.150 | 52 % | -0.015 / -0.007 | | | +10.1 | 0 | -11.4R |
| XAUUSD (371) | base | 0.183 / 0.520 | 75 % | +0.112 / +0.349 | -25.1 | -62.2 | **-82.6** | 19, -4.1R | +20.3R |
| XAUUSD | pess | 0.195 / 0.555 | 76 % | +0.125 / +0.383 | | | -88.4 (-62.0 after the cap) | 31, -15.1R | +26.2R |
| NAS100 (100) | base | 0.149 / 0.297 | 67 % | +0.063 / +0.149 | +38.8 | +28.8 | **+31.9** | 0 | -3.1R |
| NAS100 | mid | 0.297 / 0.594 | 85 % | +0.189 / +0.446 | | | +15.5 (+6.6 after the cap) | 2, +9.0R | +13.3R |
| NAS100 | pess | 0.495 / 0.990 | 94 % | +0.370 / +0.842 | | | **-6.5** (+6.3 after the cap) | 56, +17.7R | +35.2R |
| BTCUSD (130) | base | 0.209 / 0.537 | 82 % | +0.141 / +0.351 | -28.6 | -41.6 | **-49.9** | 0 | +8.2R |
| BTCUSD | pess | 0.448 / 1.283 | 91 % | +0.367 / +1.085 | | | -90.8 (-46.7 after the cap) | 50, -6.8R | +49.2R |

Reading:

- The flat 0.10R is **too harsh on EURUSD** by 0.16R a trade (FTMO's 0.1 pip plus 0.3 pip of commission, even
  counted twice on a stop, is 0.5 pip; the ledger charges 1.0 pip): +7.5R in sample, +15.7R out of sample. The
  EURUSD out-of-sample ledger, flat at -1.2R after the haircut, is +14.5R at FTMO's real cost.
- **Gold** pays 0.05R a trade extra at the measured 3.4-3.7 pips (16-19 % of its trades above 0.10R; the stops are
  85 pips at the median): the flat haircut over-covers it by 5-7R in sample. Out of sample the stops were 32 pips
  and the same spread costs 0.11-0.13R a trade: the flat figure understates gold's 2017-2023 loss by 20-26R.
- **NAS100** at 1.5 points is inside the haircut; at 3 points it is the haircut (0.09R extra at the median, 49 %
  above 0.10R); at 5 points it costs 0.19R a trade extra, 77 % of its trades above 0.10R, 10.8R of its 37.2R, and
  the live 30 % cap refuses 9 of 43 trades (stops under 16.7 points).
- **BTC** is the market the flat figure gets wrong in the expensive direction: the commission alone is 0.106R at the
  median stop ($446 against 0.065 % of a $60-120k price: $40-80 a BTC) and is 70 % of its cost; 69 % of its trades
  pay more than 0.10R extra at a $15 spread, 89 % at $45. Its +61.7R "after costs" is +56.5R at $15, +51.1R at
  $30, +45.6R at $45, and **+24.5R once the live cap refuses the 5 trades with stops under $150 (they booked
  +24.5R, 60 % won)**. The A7 gate (mean R after per-trade costs >= +0.30R and >= 70 % of the flat figure): BTC
  passes at $15-30 (+0.63 / +0.57 a trade), fails at $45 with the cap (+0.29, 42 % of the flat +0.69).
- The second spread on non-target exits (the task's convention against MT5 mechanics) is worth 0.3R EURUSD, 4.0R
  gold, 1.5R NAS100, 1.6R BTC in sample: 7.4R on 322 trades, 0.023R a trade. The flat figure covers it.
- In account money at the challenge stake (1.5 % of $10,000 = $150 a 1R): the median trade pays $7.7 EURUSD,
  $9.3 gold, $10.3 NAS100, $23 BTC (BTC runs at half stake, so $11.5); a 4H zone at double stake pays double.

## 3. Stop slippage: gaps through the stop

| Ledger | Stop exits | 5m gap > 0 | max (5m) | sum R | 1m gap > 0 | max (1m) | sum R (1m) |
|---|---|---|---|---|---|---|---|
| EURUSD 2024-26 | 25 | 0 | - | 0 | 1 | 0.1 pip | 0.017 |
| XAUUSD 2024-26 | 73 | 0 | - | 0 | 0 | - | 0 |
| NAS100 2024-26 | 23 | 0 | - | 0 | 0 | - | 0 |
| BTCUSD 2024-26 | 37 | 0 | - | 0 | 0 | - | 0 |
| EURUSD 2017-23 | 72 | 2 | 20.8 pips | 0.67 | 3 | 20.8 pips | 1.00 |
| XAUUSD 2017-23 | 261 | 2 | 47.9 pips | 0.70 | 2 | 47.9 pips | 0.70 |
| NAS100 2017-23 | 68 | 1 | 4.0 pt | 0.39 | 1 | 4.0 pt | 0.39 |
| BTCUSD 2020-23 | 87 | 0 | - | 0 | no 1m data | | |

In 2024-2026 no stop on any market was gapped through on the 5m or the 1m candles (158 stop exits; the engine
booked every one at its level: exit = stop on all). In 2017-2023, 5 of 488 stops gapped on the 5m candles (1.8R in
total, already in the ledger R; 6 on the 1m candles, 2.1R). The gap is not a cost to model; what the candles cannot show is the broker's fill slippage on a
triggered stop (ticks, the 60-second poll on a market entry). The forward report measures it; the sensitivity below
prices it at 0.05R a trade.

## 4. Hours (Amsterdam)

The spreads in the model are flat by hour (FTMO publishes no hour profile; the measured figures are session-window
medians), so the hour effect is the stop size of the trades taken in that hour. Base scenario, 2024-2026, entry hour:

| Market | Worst entry hours (cost_R p50, share > 0.10R, stop median) | Best | Note |
|---|---|---|---|
| EURUSD | 09:00: 0.081R, 0 %, 6.2 pips (pess 0.145R, 67 %) | 11:00: 0.017R (26.7 pips) | the 09:00 stops are the minimum-stop trades; -1.1R flat / -0.1R true on 6 trades |
| XAUUSD | 09:00: 0.078R, 42 %, 62 pips; 10:00: 0.064R, 29 %, 81 pips | 15:00-16:00: 0.037-0.047R, 10-16 %, 111-118 pips | the morning stops are half the afternoon's; stop exits at 11:00 are the dearest (7 trades, 35-pip stops, 0.20R) |
| NAS100 | 09:00: 0.139R, 67 %, 21.6 pt; 11:00: 0.168R, 50 %, 14.3 pt (pess 0.46 / 0.56R) | 12:00: 0.054R; 16:00+: 0.02-0.03R | stop exits 14:00: 7 trades, 20.8-pt stops, 0.14R (pess 0.48R) |
| BTCUSD | 09:00: 0.222R, 85 %, $362 (pess 0.335R, 93 %) | 15:00: 0.138R (still 75 % above 0.10R) | 09:00 holds 27 of 89 trades and +47.2R of BTC's +56.5R true: the dearest hour is the one that pays |

No hour to cut on cost grounds: the expensive hours are either immaterial (EURUSD, 6 trades) or the profitable ones
(BTC 09:00, gold 09:00 +18.8R true). Exits outside 08:00-22:00 Amsterdam (the rollover and Asian hours, where
spreads widen two to five times) are rare on this set: 7 of 73 gold stop exits, 3 of 23 NAS100, 2 of 37 BTC, 1 of
25 EURUSD; tripling the exit spread there costs 0.24R gold, 0.12R NAS100, 0.07R BTC over the 2.7 years.

## 5. The minimum stop that keeps cost_R under 0.10R for 80 % of the trades

D_min = 80th percentile of the trade's cost in price units / 0.10:

| Market | D median / p10 | live min stop | cap floor (spread / 0.3) | D_min base | D_min mid | D_min pess | trades under D_min (base), flat R, **true R** |
|---|---|---|---|---|---|---|---|
| EURUSD | 8.1 / 6.0 pips | 8 pips | 0.3 pip | **5 pips** | 5 | 9 | 0 (pess: 26 trades, +16.9R) |
| XAUUSD | 85 / 35 pips | 8 pips | 11.3-12.3 pips | **71 pips** | 77 | 79 | 57 of 143, +15.6R flat, **+16.1R true** (pess +15.3R), 40 % won |
| NAS100 | 27.5 / 14.5 pt | 12 pt | 5 / 10 / 16.7 pt | **30 pt** | 60 | 100 | 24 of 43, +17.1R flat, **+18.3R true** (pess +11.0R), 42 % won |
| BTCUSD | $446 / $189 | $60 | $50 / $100 / $150 | **$856** | $1,075 | $1,370 | 76 of 89, +54.1R flat, **+48.3R true** (pess +37.9R), 57 % won |

Only EURUSD's live minimum (8 pips) already satisfies the 80 % rule at the base cost. For gold, NAS100 and BTC the
cost-based floor would be 9x, 2.5x and 14x the live minimum and would remove 40-85 % of the trades, which are net
positive after true costs. By stop quartile after true costs (base / pess):

| Market | q1 smallest stops (median) | R flat | R true base | R true pess | won | q4 largest (median) | R true base |
|---|---|---|---|---|---|---|---|
| EURUSD | 6.0 pips (14) | -3.5 | -0.9 | -1.8 | 21 % | 18.9 pips (12) | +14.1 |
| XAUUSD | 38 pips (36) | +6.0 | +5.5 | +4.9 | 33 % | 213 pips (36) | +29.0 |
| NAS100 | 14.6 pt (11) | -2.1 | -1.8 | -6.3 | 27 % | 74 pt (11) | +14.4 |
| BTCUSD | $201 (23) | +36.1 | +31.5 | +26.1 | 65 % | $920 (22) | +7.9 |

BTC's smallest-stop quartile pays 0.35R a trade (base) and still earns +31.5R, 65 % won: the cost is paid out of
the R:R of those trades, not a reason to widen or refuse. The two weak quartiles are EURUSD's 6-pip stops (14 trades,
21 % won, about -1R either way: the 8-pip minimum already bounds them) and NAS100's stops under 17 points (11 trades,
27 % won, -1.8R base, -6.3R at a 5-point spread). A refusal on the cost itself (no entry when 2 x spread + commission
exceeds X R of the stop, decided at entry) removes winners at every X in sample (base: X = 0.25 refuses 27 BTC trades
worth +31.0R true, 10 gold worth +9.6R, 0 NAS100, 0 EURUSD) and helps only out of sample, where every bucket is
negative anyway (`cuts.md`). Not a rule to adopt.

The live cap (`max_spread_stop_fraction 0.3`) is the one floor that matters, and it moves with the spread: at the
base spreads it refuses nothing on any in-sample ledger; at NAS100 5 points it refuses 9 of 43 (stops under 16.7:
+0.1R flat, so harmless); at BTC $45 it refuses 5 of 89 that booked +24.5R.

## 6. The FTMO 2-Step and the funded month with a cost per market

`challenge_sim_costs.py`: the four ledgers at the live stakes (two open, 1.5 % with the ladder -3 %: 1.0, -6 %: 0.5,
4H zones x2 on EURUSD/gold/NAS100, EURUSD's 1D+1H pair x0.5, 1M=50/50 x0.5, BTC x0.5), 651 starts (every weekday
2024-01 .. 2026-06), phase 1 +10 %, phase 2 +5 %, 4 trading days each, fail at -10 % or a -5 % day; the funded
account at 1 % with -3 %: 0.5, month by month on a flat $10k.

| Scenario | Phase 1 | Both phases | Median days (25-75 %) | 2026 starts: 6 wk / 2 mo | 2024-25 starts: 3 mo | Funded month avg / median / worst | Losing months | Avg R a trade | Per market R after costs |
|---|---|---|---|---|---|---|---|---|---|
| flat 0.10R (the research convention) | 100 % | 100 % | 84 (43-187) | 71 % / 98 % | 42 % | +5.7 / +5.0 / -4.2 % | 9 of 33 | +0.64 | EU +39.5, gold +71.8, NAS +32.9, BTC +61.7 |
| **base** (EURUSD 0.1 pip, gold 3.4, NAS100 1.5, BTC $15, commissions) | 100 % | **100 %** | **80 (39-144)** | 78 % / 98 % | 45 % | **+6.0 / +5.4 / -4.4 %** | 9 | +0.68 | EU +47.1, gold +78.6, NAS +35.7, BTC +56.5 |
| base, one spread a round trip | 100 % | 100 % | 78 (39-152) | 78 % / 98 % | 46 % | +6.2 / +5.4 / -4.2 % | 7 | +0.70 | EU +47.4, gold +82.6, NAS +37.2, BTC +58.1 |
| mid (gold 3.7, NAS100 3, BTC $30) | 97 % | 97 % | 78 (40-171) | 71 % / 98 % | 43 % | +5.8 / +5.4 / -4.6 % | 9 | +0.64 | EU +47.1, gold +77.6, NAS +31.7, BTC +51.1 |
| **pessimistic** (EURUSD 0.2 + $5, gold 3.7 + 0.0014 %, NAS100 5, BTC $45) | 94 % | **94 %** (6 % unfinished, 0 % failed) | **76 (41-166)** | 71 % / 98 % | 39 % | **+5.5 / +5.3 / -4.2 %** | 9 | +0.60 | EU +45.2, gold +77.3, NAS +26.4, BTC +45.6 |
| pessimistic, one spread | 100 % | 100 % | 81 (41-180) | 71 % / 98 % | 44 % | +5.8 / +5.4 / -4.4 % | 8 | +0.65 | EU +45.8, gold +81.7, NAS +31.4, BTC +50.4 |
| **pessimistic + the live cap** (NAS100 -9 trades, BTC -5) | 90 % | **89 %** (11 % unfinished) | **69 (42-123)** | 60 % / 94 % | 46 % | **+5.3 / +5.3 / -4.9 %** | 9 | +0.57 | EU +45.2, gold +77.3, NAS +29.8, BTC +24.5 |
| base + 0.05R fill slippage | 95 % | 95 % | 78 (42-148) | 71 % / 98 % | 39 % | +5.7 / +5.1 / -4.2 % | 9 | +0.63 | |
| pessimistic + 0.05R fill slippage | 92 % | 92 % | 74 (44-165) | 62 % / 96 % | 39 % | +5.2 / +4.4 / -4.5 % | 12 | +0.55 | |
| base, without BTC | 99 % | 99 % | 84 (49-152) | 50 % / 91 % | 40 % | +5.1 / +5.5 / -4.4 % | 11 | +0.69 | |
| pessimistic, without BTC | 95 % | 95 % | 78 (49-173) | 50 % / 91 % | 39 % | +4.7 / +4.9 / -4.2 % | 11 | +0.64 | |

By year of the start (both phases, median days): base 2024 100 % / 91 d, 2025 100 % / 109 d, 2026 100 % / 33 d;
pessimistic 85 % / 70 d, 100 % / 133 d, 100 % / 35 d; pessimistic + cap 77 % / 65 d, 97 % / 110 d, 100 % / 40 d. The
"unfinished" starts are 2024 starts that have not reached phase 2's +5 % before the data ends, not failures: no
scenario breaks an FTMO limit on the historical path (the guard's -4 % day and -9.5 % floor hold). At 1.5 % the
average month is +8.6 % base, +7.7 % pessimistic, +7.4 % with the cap (flat: +7.9 %); the worst month -5.2 / -5.8 /
-7.1 % (flat -5.6 %).

Reading: the flat 0.10R sits between the base and the pessimistic account figure (funded +5.7 % against +6.0 and
+5.5 %), so as a portfolio haircut it was about right; it is wrong per market (EURUSD +7.5R too harsh, BTC 5-16R
too lenient). What moves the account is not the cost level but the live cap at an unmeasured BTC spread: at $45 the
five refused BTC trades take the funded month from +5.5 % to +5.3 %, the 2026 six-week pass from 71 % to 60 %, and
BTC's own contribution from +45.6R to +24.5R.

## 7. What it means for the live set, as rules

1. **Measure NAS100 and BTC spreads in the windows this week (laptop, no code).** Three weekdays of
   `.venv\Scripts\python.exe -m kronos_trader --config config/dorus_live.yaml mt5-spreads --symbols NAS100=US100.cash,BTCUSD,XAUUSD,EURUSD --day <date>`
   (the command in `docs/LAPTOP_TASKS.md`); read the median and p90 over 09-11 and 13-17. Decision rule from this
   note: BTC median spread <= $30 -> BTC stays as it is (mean R after true costs +0.57..+0.63, A7 passes);
   $30-45 -> BTC stays, expect +0.5R a trade, not +0.69; > $45 -> BTC fails the A7 gate with the cap (+0.29R a trade,
   42 % of the flat figure): halve its stake again (x0.25) until a month of forward fills says otherwise. NAS100:
   median <= 2 points -> nothing changes; 3 points -> the research haircut for NAS100 becomes 0.10R extra
   (+0.09R a trade); 5 points -> NAS100 loses 0.19R a trade and 21 % of its trades to the cap, and its 2017-2023
   result turns negative (-6.5R): then the NAS100 minimum stop goes to 17 points (`risk.min_stop_pips: 17`, the cap's
   floor at 5 points, so research refuses what live refuses).
2. **Research costs per market instead of the flat 0.10R (yaml only, no code):** in the research profiles' `symbols`
   block set `EURUSD: {typical_spread_pips: 0.2, commission_per_lot: 3.0}`, `XAUUSD: {typical_spread_pips: 3.7,
   commission_per_lot: 3.0}`, `NAS100: {typical_spread_pips: 3.0}` (1.5 once measured so), `BTCUSD:
   {typical_spread_pips: 30, commission_pct: 0.065}` (the knobs exist in `kronos_trader/config.py` lines 33-41 and the
   paper broker charges them), and drop the 0.10R haircut to 0.05R for fill slippage. Expected ledger effect against
   today's "ledger - 0.10R" (extra cost at the mid spreads plus the 0.05R, against 0.10R): EURUSD 0.16R a trade
   better, gold the same (0.05 + 0.05), NAS100 0.04R a trade worse (0.09 + 0.05), BTC 0.12R a trade worse
   (0.17 + 0.05). Then the minimum R:R, the 3R cap on BTC and the 0.8 floor on gold are judged after costs: today 33 of 89
   BTC trades and 7 of 143 gold trades have an R:R under 0.8 once the cost is taken off the target and added to the
   stop (BTC planned R:R median 1.45 -> 1.14 after costs).
3. **No cost-based stop floor and no cost-threshold refusal.** D_min at the 80 % rule is 71 pips gold, 30 points
   NAS100, $856 BTC; the trades under it earn +16.1R, +18.3R and +48.3R after true costs (base; +15.3, +11.0 and
   +37.9R pessimistic). The one existing floor that
   should stay is the 30 % cap, and it should be applied in the backtests too (candidate in `market_XAUUSD.md`
   section 4 and `pipeline.md` candidate 4), so that research refuses what live refuses.
4. **Keep `min_stop_pips` 8 on EURUSD and consider 17 on NAS100 only if the spread measures 5 points.** EURUSD's
   6-pip stops (the 14 smallest) are -0.9R true on 47 trades: immaterial. NAS100's stops under 17 points: 11 trades,
   27 % won, -1.8R base, -6.3R at 5 points; out of sample 36 trades at +5.0R base, -16.9R at 5 points. The decision
   waits for the measurement (rule 1).
5. **Journal the spread at every live fill and the fill slippage, and read them weekly against this note's
   figures** (BACKLOG item 6: `live._open_locked` computes the spread for the cap; the journal only carries it on a
   refusal). The sensitivity to price it: 0.05R a trade of fill slippage costs 5 points of the 2026 six-week pass
   rate and 0.3 % a month funded; 0.10R would cost about double. The weekly line: median spread at fill per market
   against 0.1 pip / 3.7 pips / 1.5 points / $15, and median |fill - signal price| / stop per market against 0.05R.
6. **The stop-gap slippage needs no model.** 0 of 158 stops in 2024-2026 gapped on the 5m or 1m candles (one
   0.1-pip 1m gap on EURUSD); 5 of 488 in 2017-2023 (1.8R on the 5m candles, 2.1R on the 1m, already in the ledger
   R). Leave the paper broker's gap-at-the-open fill as it is.
7. **The flat 0.10R stays as the portfolio figure until rule 2 is in**: with per-market costs the account's funded
   month is +6.0 % (base) to +5.3 % (pessimistic with the cap) against +5.7 % flat, both phases 100 % to 89 %,
   median 69-80 days against 84. Nothing in the cost picture changes the stake or the set; only the BTC spread
   measurement can (rule 1). Beside it the UTC-against-New-York candle finding (`pipeline.md` section 5: BTC +33.3R
   on the candles FTMO stamps against +70.6R) is the larger BTC unknown: at the base costs (-14R) and the
   pessimistic ones (-25R) a +33R ledger is +19R and +8R.

## 8. Caveats

- EURUSD's 0.1 pip is a raw session median; FTMO's forex spread widens at the rollover and on news, hours the set
  does not enter. Gold's 3.4-3.7 pips are the 6 October evening medians of the session windows; the pessimistic
  scenario does not add a widening because the exits outside 08-22 are too few to matter (section 4).
- The task's convention charges a second spread on stop, break-even and time exits; MT5 mechanics charge one spread
  a round trip whichever way the trade ends (the "one spread" columns). Both are given; the difference is 0.023R a
  trade on this set.
- The research BTC ledger is on Binance-anchored UTC candles; the FTMO BTCUSD CFD is a different price series with
  its own spread. The commission (0.065 % of the notional) is a published figure and applies to any BTC price.
- Lot rounding on a $10k account (0.01-lot steps) and swaps are not modelled; at the challenge stake the lots are
  1.8 EURUSD, 0.17 gold, 5.5 NAS100, 0.17 BTC at the median stops, so rounding is within 3 % of the stake.

## Appendix A: every table (`research/costs/tables.md`)

## Per-trade cost per ledger and scenario

| ledger | scenario | n | spread | comm R median | cost_R p50 | cost_R p90 | cost_R max | share > 0.10 (full) | extra_R p50 | extra_R p90 | share > 0.10 (extra) | sum R raw | sum R flat 0.10 | sum R true | sum R true (one spread) | sum R true (off-hours x3) | cap refuses n | cap refuses R(flat) | sum R true, cap applied |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| eutwo_EURUSD | base | 47 | 0.10 | 0.037 | 0.051 | 0.083 | 0.08 | 0% | -0.070 | -0.027 | 0% | +44.2 | +39.5 | +47.1 | +47.4 | +47.1 | 0 | +0.0 | +47.1 |
| eutwo_EURUSD | mid | 47 | 0.10 | 0.037 | 0.051 | 0.083 | 0.08 | 0% | -0.070 | -0.027 | 0% | +44.2 | +39.5 | +47.1 | +47.4 | +47.1 | 0 | +0.0 | +47.1 |
| eutwo_EURUSD | pess | 47 | 0.20 | 0.062 | 0.091 | 0.150 | 0.15 | 45% | -0.017 | -0.007 | 0% | +44.2 | +39.5 | +45.2 | +45.8 | +45.2 | 0 | +0.0 | +45.2 |
| base_XAUUSD | base | 143 | 3.40 | 0.004 | 0.062 | 0.176 | 0.42 | 28% | +0.033 | +0.127 | 16% | +86.1 | +71.8 | +78.6 | +82.6 | +78.3 | 0 | +0.0 | +78.6 |
| base_XAUUSD | mid | 143 | 3.70 | 0.004 | 0.067 | 0.191 | 0.45 | 30% | +0.039 | +0.142 | 18% | +86.1 | +71.8 | +77.6 | +82.0 | +77.3 | 0 | +0.0 | +77.6 |
| base_XAUUSD | pess | 143 | 3.70 | 0.006 | 0.068 | 0.191 | 0.45 | 31% | +0.040 | +0.142 | 19% | +86.1 | +71.8 | +77.3 | +81.7 | +77.1 | 0 | +0.0 | +77.3 |
| rr08_NAS100 | base | 43 | 1.50 | 0.000 | 0.068 | 0.197 | 0.25 | 37% | +0.020 | +0.099 | 9% | +37.2 | +32.9 | +35.7 | +37.2 | +35.6 | 0 | +0.0 | +35.7 |
| rr08_NAS100 | mid | 43 | 3.00 | 0.000 | 0.137 | 0.394 | 0.50 | 72% | +0.094 | +0.296 | 49% | +37.2 | +32.9 | +31.7 | +34.7 | +31.5 | 0 | +0.0 | +31.7 |
| rr08_NAS100 | pess | 43 | 5.00 | 0.000 | 0.228 | 0.657 | 0.83 | 86% | +0.194 | +0.558 | 77% | +37.2 | +32.9 | +26.4 | +31.4 | +26.0 | 9 | +0.1 | +29.8 |
| base_BTCUSD | base | 89 | 15.00 | 0.106 | 0.154 | 0.370 | 0.69 | 80% | +0.123 | +0.314 | 69% | +70.6 | +61.7 | +56.5 | +58.1 | +56.4 | 0 | +0.0 | +56.5 |
| base_BTCUSD | mid | 89 | 30.00 | 0.106 | 0.207 | 0.489 | 0.97 | 88% | +0.173 | +0.418 | 84% | +70.6 | +61.7 | +51.1 | +54.2 | +50.9 | 0 | +0.0 | +51.1 |
| base_BTCUSD | pess | 89 | 45.00 | 0.106 | 0.257 | 0.632 | 1.25 | 92% | +0.219 | +0.546 | 89% | +70.6 | +61.7 | +45.6 | +50.4 | +45.4 | 5 | +24.5 | +24.5 |
| oos_eutwo_EURUSD | base | 97 | 0.10 | 0.038 | 0.057 | 0.083 | 0.59 | 2% | -0.067 | -0.034 | 0% | +8.5 | -1.2 | +14.5 | +15.4 | +14.5 | 0 | +0.0 | +14.5 |
| oos_eutwo_EURUSD | mid | 97 | 0.10 | 0.038 | 0.057 | 0.083 | 0.59 | 2% | -0.067 | -0.034 | 0% | +8.5 | -1.2 | +14.5 | +15.4 | +14.5 | 0 | +0.0 | +14.5 |
| oos_eutwo_EURUSD | pess | 97 | 0.20 | 0.064 | 0.103 | 0.150 | 0.60 | 52% | -0.015 | -0.007 | 0% | +8.5 | -1.2 | +10.1 | +11.9 | +10.1 | 0 | +0.0 | +10.1 |
| oos_base_XAUUSD | base | 371 | 3.40 | 0.009 | 0.183 | 0.520 | 0.89 | 75% | +0.112 | +0.349 | 55% | -25.1 | -62.2 | -82.6 | -48.6 | -85.8 | 19 | -4.1 | -72.2 |
| oos_base_XAUUSD | mid | 371 | 3.70 | 0.009 | 0.198 | 0.564 | 0.96 | 76% | +0.127 | +0.390 | 60% | -25.1 | -62.2 | -89.7 | -52.8 | -93.2 | 31 | -15.1 | -62.9 |
| oos_base_XAUUSD | pess | 371 | 3.70 | 0.007 | 0.195 | 0.555 | 0.95 | 76% | +0.125 | +0.383 | 59% | -25.1 | -62.2 | -88.4 | -51.5 | -92.0 | 31 | -15.1 | -62.0 |
| oos_rr08_NAS100 | base | 100 | 1.50 | 0.000 | 0.149 | 0.297 | 0.69 | 67% | +0.063 | +0.149 | 36% | +38.8 | +28.8 | +31.9 | +38.8 | +30.8 | 0 | +0.0 | +31.9 |
| oos_rr08_NAS100 | mid | 100 | 3.00 | 0.000 | 0.297 | 0.594 | 0.99 | 85% | +0.189 | +0.446 | 71% | +38.8 | +28.8 | +15.5 | +29.2 | +13.3 | 2 | +9.0 | +6.6 |
| oos_rr08_NAS100 | pess | 100 | 5.00 | 0.000 | 0.495 | 0.990 | 1.38 | 94% | +0.370 | +0.842 | 91% | +38.8 | +28.8 | -6.5 | +16.5 | -10.1 | 56 | +17.7 | +6.3 |
| oos_base_BTCUSD | base | 130 | 15.00 | 0.091 | 0.209 | 0.537 | 0.73 | 82% | +0.141 | +0.351 | 64% | -28.6 | -41.6 | -49.9 | -42.0 | -50.4 | 0 | +0.0 | -49.9 |
| oos_base_BTCUSD | mid | 130 | 30.00 | 0.091 | 0.321 | 0.902 | 1.23 | 88% | +0.255 | +0.719 | 85% | -28.6 | -41.6 | -70.3 | -54.5 | -71.4 | 32 | -5.4 | -47.3 |
| oos_base_BTCUSD | pess | 130 | 45.00 | 0.091 | 0.448 | 1.283 | 1.73 | 91% | +0.367 | +1.085 | 89% | -28.6 | -41.6 | -90.8 | -67.1 | -92.4 | 50 | -6.8 | -46.7 |

## Minimum stop that keeps cost_R under 0.10R for 80 % of the trades

| ledger | scenario | D median | D p10 | live min stop | cap floor | D_min 80% | trades under D_min | R(flat) of those |
|---|---|---|---|---|---|---|---|---|
| eutwo_EURUSD | base | 8.1 | 6.0 | 8.0 | 0.3 | 5.0 | 0 | +0.0 |
| eutwo_EURUSD | mid | 8.1 | 6.0 | 8.0 | 0.3 | 5.0 | 0 | +0.0 |
| eutwo_EURUSD | pess | 8.1 | 6.0 | 8.0 | 0.7 | 9.0 | 26 | +16.9 |
| base_XAUUSD | base | 85.0 | 35.5 | 8.0 | 11.3 | 71.0 | 57 | +15.6 |
| base_XAUUSD | mid | 85.0 | 35.5 | 8.0 | 12.3 | 77.0 | 63 | +20.5 |
| base_XAUUSD | pess | 85.0 | 35.5 | 8.0 | 12.3 | 78.7 | 66 | +22.6 |
| rr08_NAS100 | base | 27.5 | 14.5 | 12.0 | 5.0 | 30.0 | 24 | +17.1 |
| rr08_NAS100 | mid | 27.5 | 14.5 | 12.0 | 10.0 | 60.0 | 37 | +27.5 |
| rr08_NAS100 | pess | 27.5 | 14.5 | 12.0 | 16.7 | 100.0 | 39 | +28.8 |
| base_BTCUSD | base | 446.0 | 188.6 | 60.0 | 50.0 | 855.6 | 76 | +54.1 |
| base_BTCUSD | mid | 446.0 | 188.6 | 60.0 | 100.0 | 1074.9 | 82 | +54.8 |
| base_BTCUSD | pess | 446.0 | 188.6 | 60.0 | 150.0 | 1369.5 | 85 | +58.1 |
| oos_eutwo_EURUSD | base | 7.8 | 6.0 | 8.0 | 0.3 | 5.0 | 0 | +0.0 |
| oos_eutwo_EURUSD | mid | 7.8 | 6.0 | 8.0 | 0.3 | 5.0 | 0 | +0.0 |
| oos_eutwo_EURUSD | pess | 7.8 | 6.0 | 8.0 | 0.7 | 9.0 | 59 | +2.1 |
| oos_base_XAUUSD | base | 32.3 | 13.0 | 8.0 | 11.3 | 71.0 | 306 | -49.8 |
| oos_base_XAUUSD | mid | 32.3 | 13.0 | 8.0 | 12.3 | 77.0 | 316 | -41.4 |
| oos_base_XAUUSD | pess | 32.3 | 13.0 | 8.0 | 12.3 | 76.5 | 316 | -41.4 |
| oos_rr08_NAS100 | base | 15.6 | 10.1 | 12.0 | 5.0 | 30.0 | 78 | +22.2 |
| oos_rr08_NAS100 | mid | 15.6 | 10.1 | 12.0 | 10.0 | 60.0 | 89 | +32.0 |
| oos_rr08_NAS100 | pess | 15.6 | 10.1 | 12.0 | 16.7 | 100.0 | 97 | +29.2 |
| oos_base_BTCUSD | base | 219.0 | 66.3 | 60.0 | 50.0 | 585.1 | 111 | -28.6 |
| oos_base_BTCUSD | mid | 219.0 | 66.3 | 60.0 | 100.0 | 885.1 | 116 | -34.1 |
| oos_base_BTCUSD | pess | 219.0 | 66.3 | 60.0 | 150.0 | 1185.1 | 120 | -34.3 |

## Stop slippage: gaps through the stop at the exit (5m candle at closed_at; first 1m candle through the stop)

| ledger | stop exits | 5m gap > 0 | 5m gap max | 5m gap sum R | 1m gap > 0 | 1m gap max | 1m gap sum R | 1m rows found | exit candle reaches stop (5m) |
|---|---|---|---|---|---|---|---|---|---|
| eutwo_EURUSD | 25 | 0 | 0.00 | 0.000 | 1.0 | 0.10 | 0.017 | 25.0 | 25 |
| base_XAUUSD | 73 | 0 | 0.00 | 0.000 | 0.0 | 0.00 | 0.000 | 73.0 | 73 |
| rr08_NAS100 | 23 | 0 | 0.00 | 0.000 | 0.0 | 0.00 | 0.000 | 23.0 | 23 |
| base_BTCUSD | 37 | 0 | 0.00 | 0.000 | 0.0 | 0.00 | 0.000 | 37.0 | 37 |
| oos_eutwo_EURUSD | 72 | 2 | 20.80 | 0.673 | 3.0 | 20.80 | 0.998 | 72.0 | 71 |
| oos_base_XAUUSD | 261 | 2 | 47.86 | 0.702 | 2.0 | 47.86 | 0.702 | 261.0 | 261 |
| oos_rr08_NAS100 | 68 | 1 | 3.97 | 0.393 | 1.0 | 3.97 | 0.393 | 68.0 | 67 |
| oos_base_BTCUSD | 87 | 0 | 0.00 | 0.000 | - | - | - | - | 87 |

## Cost by hour (Amsterdam), base scenario, 2024-2026 ledgers

| market | by | hour | n | D median | cost_R p50 | cost_R p90 | share > 0.10 | R flat | R true |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | entry hour | 9 | 27 | 362.3 | 0.222 | 0.396 | 85% | +49.3 | +47.2 |
| BTCUSD | entry hour | 10 | 15 | 447.0 | 0.154 | 0.481 | 87% | +4.1 | +3.1 |
| BTCUSD | entry hour | 13 | 13 | 535.0 | 0.145 | 0.374 | 69% | +0.2 | -0.5 |
| BTCUSD | entry hour | 14 | 15 | 420.0 | 0.140 | 0.348 | 73% | +7.4 | +6.6 |
| BTCUSD | entry hour | 15 | 8 | 545.5 | 0.138 | 0.316 | 75% | +4.5 | +4.3 |
| BTCUSD | entry hour | 16 | 11 | 518.0 | 0.143 | 0.170 | 82% | -3.9 | -4.1 |
| BTCUSD | stop exit hour | 3 | 1 | 451.0 | 0.170 | 0.170 | 100% | -1.1 | -1.1 |
| BTCUSD | stop exit hour | 8 | 1 | 518.0 | 0.143 | 0.143 | 100% | -1.1 | -1.1 |
| BTCUSD | stop exit hour | 9 | 2 | 195.0 | 0.443 | 0.509 | 100% | -2.2 | -2.7 |
| BTCUSD | stop exit hour | 10 | 5 | 362.3 | 0.228 | 0.542 | 100% | -5.5 | -6.3 |
| BTCUSD | stop exit hour | 11 | 2 | 958.5 | 0.109 | 0.145 | 50% | -2.2 | -2.2 |
| BTCUSD | stop exit hour | 12 | 3 | 543.0 | 0.141 | 0.302 | 100% | -3.3 | -3.5 |
| BTCUSD | stop exit hour | 13 | 2 | 353.0 | 0.246 | 0.326 | 100% | -2.2 | -2.4 |
| BTCUSD | stop exit hour | 14 | 4 | 289.5 | 0.372 | 0.582 | 100% | -4.4 | -5.2 |
| BTCUSD | stop exit hour | 15 | 5 | 446.0 | 0.227 | 0.275 | 60% | -5.5 | -5.8 |
| BTCUSD | stop exit hour | 16 | 5 | 719.0 | 0.122 | 0.281 | 80% | -5.5 | -5.7 |
| BTCUSD | stop exit hour | 17 | 2 | 564.9 | 0.125 | 0.132 | 100% | -2.2 | -2.2 |
| BTCUSD | stop exit hour | 18 | 3 | 640.0 | 0.146 | 0.290 | 67% | -3.3 | -3.4 |
| BTCUSD | stop exit hour | 19 | 2 | 676.5 | 0.128 | 0.153 | 50% | -2.2 | -2.2 |
| EURUSD | entry hour | 9 | 6 | 6.2 | 0.081 | 0.083 | 0% | -1.1 | -0.1 |
| EURUSD | entry hour | 10 | 5 | 12.8 | 0.039 | 0.068 | 0% | +3.6 | +4.4 |
| EURUSD | entry hour | 11 | 2 | 26.7 | 0.017 | 0.018 | 0% | +1.9 | +2.2 |
| EURUSD | entry hour | 13 | 4 | 16.2 | 0.046 | 0.074 | 0% | -3.4 | -2.8 |
| EURUSD | entry hour | 14 | 7 | 8.1 | 0.051 | 0.078 | 0% | +9.4 | +10.6 |
| EURUSD | entry hour | 15 | 8 | 14.7 | 0.031 | 0.083 | 0% | +2.4 | +3.6 |
| EURUSD | entry hour | 16 | 11 | 7.7 | 0.056 | 0.069 | 0% | +16.8 | +18.7 |
| EURUSD | entry hour | 17 | 4 | 11.1 | 0.041 | 0.059 | 0% | +9.9 | +10.5 |
| EURUSD | stop exit hour | 10 | 3 | 12.8 | 0.039 | 0.074 | 0% | -3.3 | -2.8 |
| EURUSD | stop exit hour | 11 | 5 | 6.7 | 0.075 | 0.083 | 0% | -4.5 | -3.7 |
| EURUSD | stop exit hour | 13 | 1 | 6.4 | 0.078 | 0.078 | 0% | -1.1 | -0.9 |
| EURUSD | stop exit hour | 14 | 3 | 6.8 | 0.074 | 0.081 | 0% | -3.3 | -2.8 |
| EURUSD | stop exit hour | 15 | 7 | 6.7 | 0.075 | 0.083 | 0% | -7.7 | -6.6 |
| EURUSD | stop exit hour | 16 | 3 | 9.8 | 0.051 | 0.055 | 0% | -3.3 | -2.9 |
| EURUSD | stop exit hour | 17 | 2 | 6.6 | 0.076 | 0.082 | 0% | -2.2 | -1.8 |
| EURUSD | stop exit hour | 19 | 1 | 31.3 | 0.016 | 0.016 | 0% | -1.1 | -1.0 |
| NAS100 | entry hour | 9 | 3 | 21.6 | 0.139 | 0.141 | 67% | +2.9 | +3.0 |
| NAS100 | entry hour | 10 | 8 | 38.2 | 0.065 | 0.196 | 38% | +4.3 | +4.8 |
| NAS100 | entry hour | 11 | 2 | 14.3 | 0.168 | 0.229 | 50% | +1.2 | +1.3 |
| NAS100 | entry hour | 12 | 3 | 37.1 | 0.054 | 0.076 | 0% | +6.0 | +6.3 |
| NAS100 | entry hour | 13 | 7 | 26.2 | 0.066 | 0.127 | 43% | +16.8 | +17.3 |
| NAS100 | entry hour | 14 | 9 | 22.7 | 0.087 | 0.230 | 44% | +3.2 | +3.6 |
| NAS100 | entry hour | 15 | 9 | 33.8 | 0.062 | 0.154 | 33% | -2.7 | -2.1 |
| NAS100 | entry hour | 16 | 1 | 103.6 | 0.029 | 0.029 | 0% | -1.1 | -1.0 |
| NAS100 | entry hour | 18 | 1 | 73.7 | 0.020 | 0.020 | 0% | +2.4 | +2.5 |
| NAS100 | stop exit hour | 1 | 1 | 103.6 | 0.029 | 0.029 | 0% | -1.1 | -1.0 |
| NAS100 | stop exit hour | 2 | 2 | 76.7 | 0.045 | 0.059 | 0% | -0.5 | -0.4 |
| NAS100 | stop exit hour | 9 | 2 | 21.4 | 0.140 | 0.141 | 100% | -2.2 | -2.1 |
| NAS100 | stop exit hour | 10 | 2 | 31.7 | 0.129 | 0.183 | 50% | -2.2 | -2.1 |
| NAS100 | stop exit hour | 11 | 1 | 12.3 | 0.244 | 0.244 | 100% | -1.1 | -1.1 |
| NAS100 | stop exit hour | 13 | 2 | 26.1 | 0.139 | 0.186 | 50% | -2.2 | -2.1 |
| NAS100 | stop exit hour | 14 | 7 | 20.8 | 0.144 | 0.235 | 86% | -7.7 | -7.5 |
| NAS100 | stop exit hour | 15 | 5 | 33.8 | 0.089 | 0.180 | 40% | -5.5 | -5.3 |
| NAS100 | stop exit hour | 16 | 2 | 51.1 | 0.078 | 0.110 | 50% | -2.2 | -2.1 |
| XAUUSD | entry hour | 9 | 31 | 62.2 | 0.078 | 0.187 | 42% | +17.6 | +18.8 |
| XAUUSD | entry hour | 10 | 21 | 81.1 | 0.064 | 0.158 | 29% | -5.9 | -5.2 |
| XAUUSD | entry hour | 13 | 28 | 72.0 | 0.053 | 0.207 | 36% | +17.2 | +18.3 |
| XAUUSD | entry hour | 14 | 24 | 91.9 | 0.060 | 0.164 | 25% | +28.4 | +29.7 |
| XAUUSD | entry hour | 15 | 19 | 117.7 | 0.037 | 0.108 | 16% | +4.7 | +5.9 |
| XAUUSD | entry hour | 16 | 20 | 111.1 | 0.047 | 0.088 | 10% | +9.9 | +11.2 |
| XAUUSD | stop exit hour | 1 | 1 | 75.8 | 0.094 | 0.094 | 0% | -1.1 | -1.1 |
| XAUUSD | stop exit hour | 2 | 2 | 143.9 | 0.052 | 0.060 | 0% | -2.2 | -2.1 |
| XAUUSD | stop exit hour | 4 | 1 | 214.5 | 0.033 | 0.033 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 7 | 1 | 406.8 | 0.017 | 0.017 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 9 | 4 | 75.0 | 0.095 | 0.176 | 50% | -4.4 | -4.3 |
| XAUUSD | stop exit hour | 10 | 4 | 53.8 | 0.132 | 0.172 | 75% | -3.4 | -3.4 |
| XAUUSD | stop exit hour | 11 | 7 | 35.0 | 0.203 | 0.383 | 100% | -7.7 | -8.2 |
| XAUUSD | stop exit hour | 12 | 4 | 80.2 | 0.092 | 0.143 | 50% | -4.4 | -4.3 |
| XAUUSD | stop exit hour | 13 | 5 | 85.5 | 0.083 | 0.223 | 40% | -5.5 | -5.4 |
| XAUUSD | stop exit hour | 14 | 18 | 72.1 | 0.099 | 0.255 | 50% | -18.8 | -18.6 |
| XAUUSD | stop exit hour | 15 | 13 | 84.1 | 0.084 | 0.145 | 38% | -14.3 | -13.9 |
| XAUUSD | stop exit hour | 16 | 6 | 126.8 | 0.059 | 0.119 | 33% | -6.6 | -6.3 |
| XAUUSD | stop exit hour | 17 | 4 | 59.1 | 0.133 | 0.189 | 50% | -4.4 | -4.4 |
| XAUUSD | stop exit hour | 18 | 1 | 87.8 | 0.081 | 0.081 | 0% | -1.1 | -1.1 |
| XAUUSD | stop exit hour | 19 | 1 | 255.7 | 0.028 | 0.028 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 20 | 1 | 320.7 | 0.022 | 0.022 | 0% | -1.1 | -1.0 |

## Cost by hour (Amsterdam), pessimistic scenario, 2024-2026 ledgers

| market | by | hour | n | D median | cost_R p50 | cost_R p90 | share > 0.10 | R flat | R true |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSD | entry hour | 9 | 27 | 362.3 | 0.335 | 0.654 | 93% | +49.3 | +43.6 |
| BTCUSD | entry hour | 10 | 15 | 447.0 | 0.268 | 0.682 | 93% | +4.1 | +1.1 |
| BTCUSD | entry hour | 13 | 13 | 535.0 | 0.257 | 0.607 | 85% | +0.2 | -2.3 |
| BTCUSD | entry hour | 14 | 15 | 420.0 | 0.220 | 0.563 | 93% | +7.4 | +4.9 |
| BTCUSD | entry hour | 15 | 8 | 545.5 | 0.201 | 0.461 | 88% | +4.5 | +3.6 |
| BTCUSD | entry hour | 16 | 11 | 518.0 | 0.240 | 0.303 | 100% | -3.9 | -5.2 |
| BTCUSD | stop exit hour | 3 | 1 | 451.0 | 0.303 | 0.303 | 100% | -1.1 | -1.3 |
| BTCUSD | stop exit hour | 8 | 1 | 518.0 | 0.259 | 0.259 | 100% | -1.1 | -1.2 |
| BTCUSD | stop exit hour | 9 | 2 | 195.0 | 0.751 | 0.809 | 100% | -2.2 | -3.3 |
| BTCUSD | stop exit hour | 10 | 5 | 362.3 | 0.394 | 0.962 | 100% | -5.5 | -7.5 |
| BTCUSD | stop exit hour | 11 | 2 | 958.5 | 0.193 | 0.262 | 100% | -2.2 | -2.3 |
| BTCUSD | stop exit hour | 12 | 3 | 543.0 | 0.227 | 0.556 | 100% | -3.3 | -4.0 |
| BTCUSD | stop exit hour | 13 | 2 | 353.0 | 0.449 | 0.594 | 100% | -2.2 | -2.8 |
| BTCUSD | stop exit hour | 14 | 4 | 289.5 | 0.648 | 1.089 | 100% | -4.4 | -6.4 |
| BTCUSD | stop exit hour | 15 | 5 | 446.0 | 0.361 | 0.455 | 100% | -5.5 | -6.4 |
| BTCUSD | stop exit hour | 16 | 5 | 719.0 | 0.206 | 0.459 | 100% | -5.5 | -6.2 |
| BTCUSD | stop exit hour | 17 | 2 | 564.9 | 0.232 | 0.245 | 100% | -2.2 | -2.4 |
| BTCUSD | stop exit hour | 18 | 3 | 640.0 | 0.240 | 0.498 | 100% | -3.3 | -3.9 |
| BTCUSD | stop exit hour | 19 | 2 | 676.5 | 0.228 | 0.280 | 100% | -2.2 | -2.4 |
| EURUSD | entry hour | 9 | 6 | 6.2 | 0.145 | 0.150 | 67% | -1.1 | -0.4 |
| EURUSD | entry hour | 10 | 5 | 12.8 | 0.070 | 0.121 | 40% | +3.6 | +4.2 |
| EURUSD | entry hour | 11 | 2 | 26.7 | 0.030 | 0.031 | 0% | +1.9 | +2.1 |
| EURUSD | entry hour | 13 | 4 | 16.2 | 0.084 | 0.134 | 50% | -3.4 | -3.0 |
| EURUSD | entry hour | 14 | 7 | 8.1 | 0.092 | 0.141 | 43% | +9.4 | +10.3 |
| EURUSD | entry hour | 15 | 8 | 14.7 | 0.054 | 0.150 | 38% | +2.4 | +3.3 |
| EURUSD | entry hour | 16 | 11 | 7.7 | 0.101 | 0.125 | 55% | +16.8 | +18.2 |
| EURUSD | entry hour | 17 | 4 | 11.1 | 0.072 | 0.104 | 25% | +9.9 | +10.4 |
| EURUSD | stop exit hour | 10 | 3 | 12.8 | 0.070 | 0.134 | 33% | -3.3 | -3.0 |
| EURUSD | stop exit hour | 11 | 5 | 6.7 | 0.134 | 0.150 | 60% | -4.5 | -3.9 |
| EURUSD | stop exit hour | 13 | 1 | 6.4 | 0.141 | 0.141 | 100% | -1.1 | -1.0 |
| EURUSD | stop exit hour | 14 | 3 | 6.8 | 0.132 | 0.146 | 100% | -3.3 | -3.0 |
| EURUSD | stop exit hour | 15 | 7 | 6.7 | 0.134 | 0.150 | 71% | -7.7 | -6.9 |
| EURUSD | stop exit hour | 16 | 3 | 9.8 | 0.092 | 0.099 | 33% | -3.3 | -3.0 |
| EURUSD | stop exit hour | 17 | 2 | 6.6 | 0.137 | 0.147 | 100% | -2.2 | -2.0 |
| EURUSD | stop exit hour | 19 | 1 | 31.3 | 0.029 | 0.029 | 0% | -1.1 | -1.0 |
| NAS100 | entry hour | 9 | 3 | 21.6 | 0.463 | 0.470 | 100% | +2.9 | +2.2 |
| NAS100 | entry hour | 10 | 8 | 38.2 | 0.218 | 0.655 | 88% | +4.3 | +3.1 |
| NAS100 | entry hour | 11 | 2 | 14.3 | 0.561 | 0.763 | 100% | +1.2 | +0.5 |
| NAS100 | entry hour | 12 | 3 | 37.1 | 0.181 | 0.252 | 67% | +6.0 | +5.9 |
| NAS100 | entry hour | 13 | 7 | 26.2 | 0.221 | 0.425 | 100% | +16.8 | +16.0 |
| NAS100 | entry hour | 14 | 9 | 22.7 | 0.290 | 0.768 | 89% | +3.2 | +1.2 |
| NAS100 | entry hour | 15 | 9 | 33.8 | 0.207 | 0.512 | 89% | -2.7 | -4.0 |
| NAS100 | entry hour | 16 | 1 | 103.6 | 0.097 | 0.097 | 0% | -1.1 | -1.1 |
| NAS100 | entry hour | 18 | 1 | 73.7 | 0.068 | 0.068 | 0% | +2.4 | +2.5 |
| NAS100 | stop exit hour | 1 | 1 | 103.6 | 0.097 | 0.097 | 0% | -1.1 | -1.1 |
| NAS100 | stop exit hour | 2 | 2 | 76.7 | 0.151 | 0.196 | 50% | -0.5 | -0.6 |
| NAS100 | stop exit hour | 9 | 2 | 21.4 | 0.467 | 0.471 | 100% | -2.2 | -2.8 |
| NAS100 | stop exit hour | 10 | 2 | 31.7 | 0.431 | 0.609 | 100% | -2.2 | -2.7 |
| NAS100 | stop exit hour | 11 | 1 | 12.3 | 0.813 | 0.813 | 100% | -1.1 | -1.7 |
| NAS100 | stop exit hour | 13 | 2 | 26.1 | 0.464 | 0.619 | 100% | -2.2 | -2.8 |
| NAS100 | stop exit hour | 14 | 7 | 20.8 | 0.481 | 0.784 | 100% | -7.7 | -10.1 |
| NAS100 | stop exit hour | 15 | 5 | 33.8 | 0.296 | 0.601 | 100% | -5.5 | -6.7 |
| NAS100 | stop exit hour | 16 | 2 | 51.1 | 0.261 | 0.366 | 100% | -2.2 | -2.4 |
| XAUUSD | entry hour | 9 | 31 | 62.2 | 0.087 | 0.204 | 45% | +17.6 | +18.4 |
| XAUUSD | entry hour | 10 | 21 | 81.1 | 0.072 | 0.172 | 33% | -5.9 | -5.4 |
| XAUUSD | entry hour | 13 | 28 | 72.0 | 0.061 | 0.230 | 39% | +17.2 | +18.0 |
| XAUUSD | entry hour | 14 | 24 | 91.9 | 0.068 | 0.178 | 25% | +28.4 | +29.5 |
| XAUUSD | entry hour | 15 | 19 | 117.7 | 0.044 | 0.118 | 21% | +4.7 | +5.8 |
| XAUUSD | entry hour | 16 | 20 | 111.1 | 0.053 | 0.096 | 10% | +9.9 | +11.0 |
| XAUUSD | stop exit hour | 1 | 1 | 75.8 | 0.104 | 0.104 | 100% | -1.1 | -1.1 |
| XAUUSD | stop exit hour | 2 | 2 | 143.9 | 0.058 | 0.068 | 0% | -2.2 | -2.1 |
| XAUUSD | stop exit hour | 4 | 1 | 214.5 | 0.037 | 0.037 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 7 | 1 | 406.8 | 0.020 | 0.020 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 9 | 4 | 75.0 | 0.106 | 0.196 | 50% | -4.4 | -4.4 |
| XAUUSD | stop exit hour | 10 | 4 | 53.8 | 0.145 | 0.189 | 100% | -3.4 | -3.4 |
| XAUUSD | stop exit hour | 11 | 7 | 35.0 | 0.222 | 0.417 | 100% | -7.7 | -8.3 |
| XAUUSD | stop exit hour | 12 | 4 | 80.2 | 0.101 | 0.156 | 50% | -4.4 | -4.3 |
| XAUUSD | stop exit hour | 13 | 5 | 85.5 | 0.092 | 0.242 | 40% | -5.5 | -5.5 |
| XAUUSD | stop exit hour | 14 | 18 | 72.1 | 0.107 | 0.279 | 56% | -18.8 | -18.9 |
| XAUUSD | stop exit hour | 15 | 13 | 84.1 | 0.095 | 0.159 | 46% | -14.3 | -14.0 |
| XAUUSD | stop exit hour | 16 | 6 | 126.8 | 0.066 | 0.130 | 33% | -6.6 | -6.3 |
| XAUUSD | stop exit hour | 17 | 4 | 59.1 | 0.144 | 0.205 | 50% | -4.4 | -4.4 |
| XAUUSD | stop exit hour | 18 | 1 | 87.8 | 0.092 | 0.092 | 0% | -1.1 | -1.1 |
| XAUUSD | stop exit hour | 19 | 1 | 255.7 | 0.031 | 0.031 | 0% | -1.1 | -1.0 |
| XAUUSD | stop exit hour | 20 | 1 | 320.7 | 0.025 | 0.025 | 0% | -1.1 | -1.0 |

## Appendix B: cuts (`research/costs/cuts.md`)

```
## Stop-size buckets: R flat (ledger - 0.10) against R after true costs (base / pess)
          ledger        bucket  n  stop median  cost_R base p50  R flat  R true base  R true pess won
    eutwo_EURUSD q1 (smallest) 14          6.0            0.081    -3.5         -0.9         -1.8 21%
    eutwo_EURUSD            q2 10          7.0            0.059    13.3         15.1         14.6 60%
    eutwo_EURUSD            q3 11         10.2            0.040    17.2         18.8         18.5 55%
    eutwo_EURUSD  q4 (largest) 12         18.9            0.022    12.6         14.1         13.9 58%
     base_XAUUSD q1 (smallest) 36         38.3            0.154     6.0          5.5          4.9 33%
     base_XAUUSD            q2 36         70.0            0.076    22.6         24.4         24.1 50%
     base_XAUUSD            q3 35        102.9            0.040    17.3         19.7         19.5 57%
     base_XAUUSD  q4 (largest) 36        212.5            0.025    25.9         29.0         28.9 56%
     rr08_NAS100 q1 (smallest) 11         14.6            0.196    -2.1         -1.8         -6.3 27%
     rr08_NAS100            q2 11         22.7            0.109     8.4          9.1          6.5 45%
     rr08_NAS100            q3 10         35.8            0.061    13.1         13.9         12.5 50%
     rr08_NAS100  q4 (largest) 11         73.7            0.029    13.4         14.4         13.6 64%
     base_BTCUSD q1 (smallest) 23        201.0            0.346    36.1         31.5         26.1 65%
     base_BTCUSD            q2 22        372.6            0.183    22.0         20.7         18.2 64%
     base_BTCUSD            q3 22        520.5            0.143    -3.5         -3.6         -5.6 45%
     base_BTCUSD  q4 (largest) 22        920.0            0.076     7.1          7.9          6.9 59%
oos_eutwo_EURUSD q1 (smallest) 29          6.0            0.083   -21.3        -16.0        -17.8  7%
oos_eutwo_EURUSD            q2 20          6.9            0.065    -1.4          2.1          1.1 30%
oos_eutwo_EURUSD            q3 24          9.3            0.050    24.4         28.2         27.3 42%
oos_eutwo_EURUSD  q4 (largest) 24         15.1            0.032    -3.0          0.2         -0.4 29%
 oos_base_XAUUSD q1 (smallest) 93         14.6            0.445   -20.3        -40.2        -43.1 26%
 oos_base_XAUUSD            q2 93         26.6            0.241    -4.0         -9.3        -10.8 31%
 oos_base_XAUUSD            q3 92         43.3            0.155   -20.9        -20.9        -21.9 30%
 oos_base_XAUUSD  q4 (largest) 93         80.6            0.067   -17.1        -12.2        -12.7 31%
 oos_rr08_NAS100 q1 (smallest) 36         10.1            0.297     5.4          5.0        -16.9 28%
 oos_rr08_NAS100            q2 14         13.5            0.214    -1.6         -1.5         -8.2 21%
 oos_rr08_NAS100            q3 25         22.3            0.122    18.2         19.6         12.7 40%
 oos_rr08_NAS100  q4 (largest) 25         56.8            0.048     6.8          8.8          6.0 36%
 oos_base_BTCUSD q1 (smallest) 33         71.0            0.483    -6.5        -13.1        -35.9 36%
 oos_base_BTCUSD            q2 32        147.7            0.294    -4.6         -7.1        -17.3 41%
 oos_base_BTCUSD            q3 32        289.3            0.172   -13.2        -13.8        -19.5 28%
 oos_base_BTCUSD  q4 (largest) 33        734.1            0.074   -17.3        -15.8        -18.1 27%

## Refusal rule: skip the trade when the full cost at entry (two spreads for a stop exit assumed, commission) exceeds X R
scenario    X           ledger  refused  of  R true refused  R true kept  R true all won refused
    base 0.15     eutwo_EURUSD        0  47             0.0         47.1        47.1           -
    base 0.15      base_XAUUSD       28 143            10.5         68.1        78.6         36%
    base 0.15      rr08_NAS100       10  43            -0.7         36.4        35.7         30%
    base 0.15      base_BTCUSD       56  89            52.4          4.1        56.5         62%
    base 0.15 oos_eutwo_EURUSD        0  97             0.0         14.5        14.5           -
    base 0.15  oos_base_XAUUSD      259 371           -70.0        -12.6       -82.6         29%
    base 0.15  oos_rr08_NAS100       62 100            14.0         17.9        31.9         27%
    base 0.15  oos_base_BTCUSD       93 130           -35.7        -14.1       -49.9         34%
    base 0.20     eutwo_EURUSD        0  47             0.0         47.1        47.1           -
    base 0.20      base_XAUUSD       15 143             7.0         71.5        78.6         33%
    base 0.20      rr08_NAS100        6  43             0.2         35.5        35.7         33%
    base 0.20      base_BTCUSD       37  89            47.9          8.6        56.5         62%
    base 0.20 oos_eutwo_EURUSD        0  97             0.0         14.5        14.5           -
    base 0.20  oos_base_XAUUSD      209 371           -58.3        -24.3       -82.6         28%
    base 0.20  oos_rr08_NAS100       48 100             5.7         26.2        31.9         27%
    base 0.20  oos_base_BTCUSD       74 130           -24.3        -25.6       -49.9         36%
    base 0.25     eutwo_EURUSD        0  47             0.0         47.1        47.1           -
    base 0.25      base_XAUUSD       10 143             9.6         69.0        78.6         40%
    base 0.25      rr08_NAS100        0  43             0.0         35.7        35.7           -
    base 0.25      base_BTCUSD       27  89            31.0         25.5        56.5         59%
    base 0.25 oos_eutwo_EURUSD        0  97             0.0         14.5        14.5           -
    base 0.25  oos_base_XAUUSD      151 371           -47.0        -35.6       -82.6         27%
    base 0.25  oos_rr08_NAS100       40 100            10.5         21.4        31.9         30%
    base 0.25  oos_base_BTCUSD       59 130           -24.4        -25.5       -49.9         36%
    base 0.30     eutwo_EURUSD        0  47             0.0         47.1        47.1           -
    base 0.30      base_XAUUSD        2 143            -2.6         81.1        78.6          0%
    base 0.30      rr08_NAS100        0  43             0.0         35.7        35.7           -
    base 0.30      base_BTCUSD       23  89            27.6         28.9        56.5         57%
    base 0.30 oos_eutwo_EURUSD        0  97             0.0         14.5        14.5           -
    base 0.30  oos_base_XAUUSD      124 371           -59.5        -23.0       -82.6         24%
    base 0.30  oos_rr08_NAS100        2 100             9.2         22.7        31.9        100%
    base 0.30  oos_base_BTCUSD       52 130           -16.0        -33.9       -49.9         40%
    base 0.40     eutwo_EURUSD        0  47             0.0         47.1        47.1           -
    base 0.40      base_XAUUSD        1 143            -1.3         79.9        78.6          0%
    base 0.40      rr08_NAS100        0  43             0.0         35.7        35.7           -
    base 0.40      base_BTCUSD       11  89            25.6         30.9        56.5         64%
    base 0.40 oos_eutwo_EURUSD        0  97             0.0         14.5        14.5           -
    base 0.40  oos_base_XAUUSD       72 371           -35.4        -47.2       -82.6         24%
    base 0.40  oos_rr08_NAS100        0 100             0.0         31.9        31.9           -
    base 0.40  oos_base_BTCUSD       39 130           -10.4        -39.5       -49.9         44%
    pess 0.15     eutwo_EURUSD        6  47            -2.9         48.2        45.2         17%
    pess 0.15      base_XAUUSD       37 143             3.8         73.6        77.3         32%
    pess 0.15      rr08_NAS100       37  43            20.8          5.6        26.4         46%
    pess 0.15      base_BTCUSD       80  89            37.3          8.4        45.6         56%
    pess 0.15 oos_eutwo_EURUSD       10  97            -9.8         20.0        10.1          0%
    pess 0.15  oos_base_XAUUSD      266 371           -74.7        -13.7       -88.4         29%
    pess 0.15  oos_rr08_NAS100       94 100            -5.5         -0.9        -6.5         32%
    pess 0.15  oos_base_BTCUSD      115 130           -82.6         -8.2       -90.8         34%
    pess 0.20     eutwo_EURUSD        0  47             0.0         45.2        45.2           -
    pess 0.20      base_XAUUSD       19 143             6.1         71.3        77.3         32%
    pess 0.20      rr08_NAS100       36  43            19.4          7.0        26.4         44%
    pess 0.20      base_BTCUSD       71  89            39.1          6.6        45.6         58%
    pess 0.20 oos_eutwo_EURUSD        0  97             0.0         10.1        10.1           -
    pess 0.20  oos_base_XAUUSD      217 371           -63.1        -25.3       -88.4         28%
    pess 0.20  oos_rr08_NAS100       85 100            -4.2         -2.3        -6.5         32%
    pess 0.20  oos_base_BTCUSD      109 130           -75.6        -15.1       -90.8         36%
    pess 0.25     eutwo_EURUSD        0  47             0.0         45.2        45.2           -
    pess 0.25      base_XAUUSD       10 143             9.4         68.0        77.3         40%
    pess 0.25      rr08_NAS100       30  43            15.2         11.2        26.4         43%
    pess 0.25      base_BTCUSD       59  89            40.2          5.4        45.6         59%
    pess 0.25 oos_eutwo_EURUSD        0  97             0.0         10.1        10.1           -
    pess 0.25  oos_base_XAUUSD      167 371           -49.0        -39.4       -88.4         28%
    pess 0.25  oos_rr08_NAS100       81 100            -3.0         -3.4        -6.5         32%
    pess 0.25  oos_base_BTCUSD      102 130           -77.2        -13.5       -90.8         34%
    pess 0.30     eutwo_EURUSD        0  47             0.0         45.2        45.2           -
    pess 0.30      base_XAUUSD        4 143             4.5         72.8        77.3         25%
    pess 0.30      rr08_NAS100       25  43            14.1         12.3        26.4         44%
    pess 0.30      base_BTCUSD       48  89            46.0         -0.4        45.6         65%
    pess 0.30 oos_eutwo_EURUSD        0  97             0.0         10.1        10.1           -
    pess 0.30  oos_base_XAUUSD      133 371           -48.3        -40.1       -88.4         26%
    pess 0.30  oos_rr08_NAS100       79 100            -9.4          3.0        -6.5         32%
    pess 0.30  oos_base_BTCUSD       95 130           -74.2        -16.6       -90.8         35%
    pess 0.40     eutwo_EURUSD        0  47             0.0         45.2        45.2           -
    pess 0.40      base_XAUUSD        1 143            -1.3         78.7        77.3          0%
    pess 0.40      rr08_NAS100       17  43            -5.9         32.3        26.4         29%
    pess 0.40      base_BTCUSD       29  89            26.1         19.5        45.6         62%
    pess 0.40 oos_eutwo_EURUSD        0  97             0.0         10.1        10.1           -
    pess 0.40  oos_base_XAUUSD       86 371           -47.5        -40.9       -88.4         23%
    pess 0.40  oos_rr08_NAS100       68 100           -23.3         16.8        -6.5         26%
    pess 0.40  oos_base_BTCUSD       81 130           -66.5        -24.3       -90.8         35%

## Commission against spread (base), and the planned R:R before and after the full cost
          ledger   n  commission R p50  spread-only R p50 commission share of cost  planned R:R p50  R:R after cost p50  trades R:R<0.8 after cost  cost $ a trade at 1.5 % of 10k (median)
    eutwo_EURUSD  47             0.037              0.015                      66%             3.29                3.11                          0                                      7.7
     base_XAUUSD 143             0.004              0.057                       6%             1.97                1.84                          7                                      9.3
     rr08_NAS100  43             0.000              0.068                       0%             2.55                2.39                          0                                     10.3
     base_BTCUSD  89             0.106              0.046                      70%             1.45                1.14                         33                                     23.1
oos_eutwo_EURUSD  97             0.038              0.022                      43%             2.80                2.53                          0                                      8.6
 oos_base_XAUUSD 371             0.009              0.171                       5%             1.97                1.53                         40                                     27.5
 oos_rr08_NAS100 100             0.000              0.149                       0%             2.59                2.15                          0                                     22.3
 oos_base_BTCUSD 130             0.091              0.116                      46%             1.27                0.91                         55                                     31.4

## The second spread on non-target exits: its weight in the extra cost (base)
          ledger  non-target exits  extra two-spread  extra one-spread  difference R
    eutwo_EURUSD                25              -2.8              -3.1           0.3
     base_XAUUSD                73               7.6               3.5           4.0
     rr08_NAS100                24               1.5               0.0           1.5
     base_BTCUSD                37              14.1              12.5           1.6
oos_eutwo_EURUSD                72              -6.0              -6.9           0.9
 oos_base_XAUUSD               261              57.4              23.5          34.0
 oos_rr08_NAS100                70               6.9               0.0           6.9
 oos_base_BTCUSD                87              21.2              13.3           7.9
```

## Appendix C: the replay outputs (`research/costs/sim_*.out`)

```
scenario flat (flat 0.10R); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 100%: median 40 days, 25-75% 20-110
  both phases 100%: median 84 days, 25-75% 43-187
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 90 days, failed 0%
    starts 2025: both phases 100%, median 131 days, failed 0%
    starts 2026: both phases 100%, median 34 days, failed 0%
  funded at 1 %: average month +5.7%, median +5.0%, worst -4.2%, best +27.8%, losing months 9 of 33
  by year: 2024 +2.9%/mo  2025 +4.7%/mo  2026 +10.9%/mo
  trades 322 (9.8/month), won 51%, avg R +0.64 after costs; wins avg +2.30R
  at 1.5 %: average month +7.9%, worst -5.6%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 42%
  per market after costs: BTCUSD +61.7R/89  EURUSD +39.5R/47  NAS100 +32.9R/43  XAUUSD +71.8R/143

scenario base (column extra_base); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 100%: median 37 days, 25-75% 20-84
  both phases 100%: median 80 days, 25-75% 39-144
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 91 days, failed 0%
    starts 2025: both phases 100%, median 109 days, failed 0%
    starts 2026: both phases 100%, median 33 days, failed 0%
  funded at 1 %: average month +6.0%, median +5.4%, worst -4.4%, best +28.4%, losing months 9 of 33
  by year: 2024 +3.0%/mo  2025 +4.8%/mo  2026 +11.5%/mo
  trades 322 (9.8/month), won 51%, avg R +0.68 after costs; wins avg +2.34R
  at 1.5 %: average month +8.6%, worst -5.2%
  2026 starts both phases within 6 weeks 78%, within 2 months 98%
  2024-25 starts both phases within 3 months 45%
  per market after costs: BTCUSD +56.5R/89  EURUSD +47.1R/47  NAS100 +35.7R/43  XAUUSD +78.6R/143

scenario mid (column extra_mid); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 97%: median 36 days, 25-75% 20-104
  both phases 97%: median 78 days, 25-75% 40-171
  failed: phase 1 0%, phase 2 0%; unfinished 3%
    starts 2024: both phases 92%, median 76 days, failed 0%
    starts 2025: both phases 100%, median 125 days, failed 0%
    starts 2026: both phases 100%, median 35 days, failed 0%
  funded at 1 %: average month +5.8%, median +5.4%, worst -4.6%, best +28.2%, losing months 9 of 33
  by year: 2024 +2.8%/mo  2025 +4.5%/mo  2026 +11.3%/mo
  trades 322 (9.8/month), won 51%, avg R +0.64 after costs; wins avg +2.32R
  at 1.5 %: average month +8.2%, worst -5.5%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 43%
  per market after costs: BTCUSD +51.1R/89  EURUSD +47.1R/47  NAS100 +31.7R/43  XAUUSD +77.6R/143

scenario pess (column extra_pess); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 94%: median 36 days, 25-75% 20-103
  both phases 94%: median 76 days, 25-75% 41-166
  failed: phase 1 0%, phase 2 0%; unfinished 6%
    starts 2024: both phases 85%, median 70 days, failed 0%
    starts 2025: both phases 100%, median 133 days, failed 0%
    starts 2026: both phases 100%, median 35 days, failed 0%
  funded at 1 %: average month +5.5%, median +5.3%, worst -4.2%, best +27.9%, losing months 9 of 33
  by year: 2024 +2.5%/mo  2025 +4.3%/mo  2026 +11.1%/mo
  trades 322 (9.8/month), won 51%, avg R +0.60 after costs; wins avg +2.29R
  at 1.5 %: average month +7.7%, worst -5.8%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 39%
  per market after costs: BTCUSD +45.6R/89  EURUSD +45.2R/47  NAS100 +26.4R/43  XAUUSD +77.3R/143

scenario pess+cap (column extra_pess, cap: dropped {'EURUSD': 0, 'XAUUSD': 0, 'NAS100': 9, 'BTCUSD': 5}); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 90%: median 33 days, 25-75% 19-62
  both phases 89%: median 69 days, 25-75% 42-123
  failed: phase 1 0%, phase 2 0%; unfinished 11%
    starts 2024: both phases 77%, median 65 days, failed 0%
    starts 2025: both phases 97%, median 110 days, failed 0%
    starts 2026: both phases 100%, median 40 days, failed 0%
  funded at 1 %: average month +5.3%, median +5.3%, worst -4.9%, best +22.6%, losing months 9 of 33
  by year: 2024 +2.5%/mo  2025 +4.8%/mo  2026 +9.8%/mo
  trades 308 (9.3/month), won 52%, avg R +0.57 after costs; wins avg +2.18R
  at 1.5 %: average month +7.4%, worst -7.1%
  2026 starts both phases within 6 weeks 60%, within 2 months 94%
  2024-25 starts both phases within 3 months 46%
  per market after costs: BTCUSD +24.5R/84  EURUSD +45.2R/47  NAS100 +29.8R/34  XAUUSD +77.3R/143

scenario base_mech (column extra_mech_base); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 100%: median 36 days, 25-75% 19-80
  both phases 100%: median 78 days, 25-75% 39-152
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 91 days, failed 0%
    starts 2025: both phases 100%, median 106 days, failed 0%
    starts 2026: both phases 100%, median 33 days, failed 0%
  funded at 1 %: average month +6.2%, median +5.4%, worst -4.2%, best +28.4%, losing months 7 of 33
  by year: 2024 +3.3%/mo  2025 +5.0%/mo  2026 +11.6%/mo
  trades 322 (9.8/month), won 51%, avg R +0.70 after costs; wins avg +2.34R
  at 1.5 %: average month +9.0%, worst -5.4%
  2026 starts both phases within 6 weeks 78%, within 2 months 98%
  2024-25 starts both phases within 3 months 46%
  per market after costs: BTCUSD +58.1R/89  EURUSD +47.4R/47  NAS100 +37.2R/43  XAUUSD +82.6R/143

scenario pess_mech (column extra_mech_pess); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 100%: median 38 days, 25-75% 20-103
  both phases 100%: median 81 days, 25-75% 41-180
  failed: phase 1 0%, phase 2 0%; unfinished 0%
    starts 2024: both phases 100%, median 91 days, failed 0%
    starts 2025: both phases 100%, median 113 days, failed 0%
    starts 2026: both phases 100%, median 35 days, failed 0%
  funded at 1 %: average month +5.8%, median +5.4%, worst -4.4%, best +28.0%, losing months 8 of 33
  by year: 2024 +3.0%/mo  2025 +4.7%/mo  2026 +11.3%/mo
  trades 322 (9.8/month), won 51%, avg R +0.65 after costs; wins avg +2.29R
  at 1.5 %: average month +8.3%, worst -5.3%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 44%
  per market after costs: BTCUSD +50.4R/89  EURUSD +45.8R/47  NAS100 +31.4R/43  XAUUSD +81.7R/143

scenario base+slip0.05 (column extra_base) + 0.05R slippage; 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 95%: median 36 days, 25-75% 20-99
  both phases 95%: median 78 days, 25-75% 42-148
  failed: phase 1 0%, phase 2 0%; unfinished 5%
    starts 2024: both phases 88%, median 71 days, failed 0%
    starts 2025: both phases 100%, median 123 days, failed 0%
    starts 2026: both phases 100%, median 35 days, failed 0%
  funded at 1 %: average month +5.7%, median +5.1%, worst -4.2%, best +27.8%, losing months 9 of 33
  by year: 2024 +2.7%/mo  2025 +4.7%/mo  2026 +11.1%/mo
  trades 322 (9.8/month), won 51%, avg R +0.63 after costs; wins avg +2.29R
  at 1.5 %: average month +7.9%, worst -5.6%
  2026 starts both phases within 6 weeks 71%, within 2 months 98%
  2024-25 starts both phases within 3 months 39%
  per market after costs: BTCUSD +52.0R/89  EURUSD +44.7R/47  NAS100 +33.5R/43  XAUUSD +71.4R/143

scenario pess+slip0.05 (column extra_pess) + 0.05R slippage; 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 92%: median 36 days, 25-75% 20-107
  both phases 92%: median 74 days, 25-75% 44-165
  failed: phase 1 0%, phase 2 0%; unfinished 8%
    starts 2024: both phases 81%, median 70 days, failed 0%
    starts 2025: both phases 100%, median 137 days, failed 0%
    starts 2026: both phases 100%, median 39 days, failed 0%
  funded at 1 %: average month +5.2%, median +4.4%, worst -4.5%, best +27.4%, losing months 12 of 33
  by year: 2024 +2.1%/mo  2025 +4.1%/mo  2026 +10.7%/mo
  trades 322 (9.8/month), won 51%, avg R +0.55 after costs; wins avg +2.25R
  at 1.5 %: average month +7.1%, worst -6.2%
  2026 starts both phases within 6 weeks 62%, within 2 months 96%
  2024-25 starts both phases within 3 months 39%
  per market after costs: BTCUSD +41.2R/89  EURUSD +42.9R/47  NAS100 +24.2R/43  XAUUSD +70.2R/143

scenario base (column extra_base); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 99%: median 37 days, 25-75% 21-86
  both phases 99%: median 84 days, 25-75% 49-152
  failed: phase 1 0%, phase 2 0%; unfinished 1%
    starts 2024: both phases 98%, median 88 days, failed 0%
    starts 2025: both phases 100%, median 120 days, failed 0%
    starts 2026: both phases 100%, median 43 days, failed 0%
  funded at 1 %: average month +5.1%, median +5.5%, worst -4.4%, best +20.7%, losing months 11 of 33
  by year: 2024 +2.5%/mo  2025 +4.4%/mo  2026 +9.3%/mo
  trades 233 (7.1/month), won 48%, avg R +0.69 after costs; wins avg +2.53R
  at 1.5 %: average month +7.3%, worst -5.2%
  2026 starts both phases within 6 weeks 50%, within 2 months 91%
  2024-25 starts both phases within 3 months 40%
  per market after costs: EURUSD +47.1R/47  NAS100 +35.7R/43  XAUUSD +78.6R/143

scenario pess (column extra_pess); 651 challenge starts (every weekday 2024-01 .. 2026-06)
  phase 1 passed 95%: median 37 days, 25-75% 21-113
  both phases 95%: median 78 days, 25-75% 49-173
  failed: phase 1 0%, phase 2 0%; unfinished 5%
    starts 2024: both phases 87%, median 76 days, failed 0%
    starts 2025: both phases 100%, median 133 days, failed 0%
    starts 2026: both phases 100%, median 43 days, failed 0%
  funded at 1 %: average month +4.7%, median +4.9%, worst -4.2%, best +19.7%, losing months 11 of 33
  by year: 2024 +2.2%/mo  2025 +4.1%/mo  2026 +9.0%/mo
  trades 233 (7.1/month), won 48%, avg R +0.64 after costs; wins avg +2.49R
  at 1.5 %: average month +6.7%, worst -5.8%
  2026 starts both phases within 6 weeks 50%, within 2 months 91%
  2024-25 starts both phases within 3 months 39%
  per market after costs: EURUSD +45.2R/47  NAS100 +26.4R/43  XAUUSD +77.3R/143

```
