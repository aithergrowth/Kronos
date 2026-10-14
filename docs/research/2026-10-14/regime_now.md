# The four markets now (14 October 2026, 19:00 Amsterdam) and the next three weeks

Situational awareness for the trader, read the way the engine reads it. Nothing here changes a rule; the profiles
stay frozen during the challenge. Day 2 of the FTMO 2-Step.

## How this was measured

- Candles: the research files (HistData bid for EURUSD/XAUUSD/NAS100, Bitstamp for BTC; they end 24 Sep, 1 Oct and
  4 Oct) spliced with TradingView hourly bars (`FX:EURUSD`, `OANDA:XAUUSD`, `CAPITALCOM:US100`, `BITSTAMP:BTCUSD`) up to
  14 Oct 16:00 UTC. On the 41-50 overlapping hours the two sources differ by a constant the seam removes: EURUSD 0,
  gold -0.32 (0.02 of a median 1H range), NAS100 +2.99 points (0.05 of a median 1H range), BTC 0. The 4H/1D/1W/1MO
  candles were rebuilt with the research anchoring (17:00 New York) and are identical to the research files on every
  overlapping bar (max difference 0 on all timeframes, all four markets). 15m bars come from TradingView (last 4 days);
  there is no 5m, so the engine could not look for 1H-zone confirmations (5m) at this moment.
- Engine: `python -m kronos_trader --config config/dorus_live_<market>.yaml decision-dossier --at "2026-10-14 17:00"
  --warmup-days 2 --kronos off` on that cache (191 fifteen-minute warm-up steps, so zone visits carry history), plus the
  diagnostic `--assume long/short` runs. Output: `research/regime_now/dossiers/<MARKET>/` (README.md, dossier.json,
  1D/4H/1H/15m charts). BTC was run twice: on candles anchored at 17:00 New York (what an MT5 server shows) and at UTC
  midnight (what the research ledgers used).
- Regime: `S/regime/regime.py`'s definitions on closed daily candles (session of 13 Oct): 20-day efficiency ratio
  er20 = |close - close 20 days ago| / sum of the 20 daily absolute changes; ATR14 as % of price; 60-day return.
  Percentiles against the in-sample window 2024-01..2026-09 and against the last 250 days.
- Calendar: TradingView economic calendar (USD, EUR), converted to Amsterdam time with the bot's 30-minute blackout on
  either side. The bot itself reads ForexFactory's red list each hour; its 08:45 morning message names the day's exact
  blackouts, so this table is the map, not the territory.

## Today in one line per market

CPI (14:30 Amsterdam) came in hot: 3.7 % y/y (forecast 3.6, previous 3.4), core 2.6 % (2.5), headline +0.6 % m/m with
energy +5.2 % m/m. Markets price Fed hike risk into the 28 October FOMC (Fed funds 4.00 %, Chair Warsh). Session moves
from the 13 Oct 23:00 open to 19:00 Amsterdam: EURUSD 1.11982 -> 1.11236 (-0.7 %, a 16-month low at 1.11128); gold
4160.8 -> 4083.3 (-1.9 %, low 4073.5, third down day); NAS100 30563 -> 30047 (-1.7 %, low 29975); BTC 83094 -> 81925
(-1.4 %, low 81500). All four fell on the same print: the account's four markets are one USD trade today.

## The engine's reading at 17:00 UTC

### EURUSD (price 1.11236)

| TF | Bias | Liquidity | Balance | Last breaks |
|---|---|---|---|---|
| 1M | 50/50 | bearish | bullish | BMS bearish 1.14687 (May); BOS bearish 1.14108 (Aug) |
| 1W | bearish | bearish | bearish | BOS 1.14108 (Jun); BOS 1.13531 (week of 27 Sep) |
| 1D | bearish | bearish | bearish | BOS 1.13245 (30 Sep); BOS 1.11610 (11 Oct) |
| 4H | bearish | bearish | bearish | BMS bullish 1.12046 (14 Oct 03:00 Ams); BMS bearish 1.11516 (14 Oct 11:00) |
| 1H | bearish | bearish | bearish | BMS bearish 1.11931 (12:00 Ams); BOS 1.11851 (14:00) |

Decision: **bearish, full mode, matched as the 1D+1H pair** (four of five bearish, the month 50/50). The weekly and 4H
veto allow shorts. Stake: 1.5 % x 0.5 (month 50/50) x 0.5 (1D+1H pair) = **0.375 % on a 1H zone, 0.75 % on a 4H zone**
(the multipliers multiply, `risk.py` 280-287), before the drawdown ladder.

Zones the engine can still trade (fresh, visited within 24 h of forming, the rest are spent or too old):

| Zone | Range | Above price | Formed (Amsterdam) | Tradable until |
|---|---|---|---|---|
| 1H supply | 1.11374 - 1.11985 | 14 pips to its low | 14 Oct 15:00 (the CPI candle) | first touch by 15 Oct 15:00 |
| 4H supply | 1.11516 - 1.12113 | 28 pips | 14 Oct 11:00 | first touch by 15 Oct 11:00 |

Everything else near price is spent (the 4H supply 1.12028-1.12629 was touched 29 h after forming, the 4H 1.11838-1.12103
is 56 h old) and the weekly demand 1.07782-1.09369 is 2.6 daily ranges away. What has to happen for a trade: a pullback
into 1.11374-1.11985 tomorrow inside 09-11 or 13-17 Amsterdam (14:00-15:00 is PPI/retail-sales blackout), a 5m balance
shift down inside the 1H zone (or a 15m shift inside the 4H zone), entry by a limit 25 % back toward the stop, stop
beyond the sweep extreme (min 8 pips), target at the origin of the move that made the zone. The engine refuses longs
(bias), and the diagnostic walk-on finds no tradable demand at all (the 1M zone 1.03883-1.12140 is spent).

### XAUUSD (price 4083.3)

| TF | Bias | Liquidity | Balance | Last breaks |
|---|---|---|---|---|
| 1M | bearish | bearish | bearish | BOS bullish 3499.91 (Sep); BMS bearish 4098.27 (May) |
| 1W | bearish | bearish | bearish | BMS bearish 4401.04 (Jun); BOS 4098.27 (Jun) |
| 1D | 50/50 | bullish (sell-side swept at 4110.5) | bearish | BOS 4282.03 (16 Sep); BOS 4234.66 (28 Sep) |
| 4H | bearish | bearish | bearish | BOS 4150.46 (14 Oct 07:00 Ams); BOS 4105.18 (11:00) |
| 1H | bearish | bearish | bearish | BMS 4144.13 (10:00); BOS 4105.18 (14:00) |

Decision: **bearish, full mode (4H+1H aligned, four of five with the 1H)**. Month bearish, so no 50/50 halving: stake
**1.5 % on a 1H zone, 3.0 % on a 4H zone** (the largest stake in the book). No weekly veto on gold.

| Zone | Range | Above price | Formed (Amsterdam) | Tradable until |
|---|---|---|---|---|
| 1H and 4H supply | 4105.18 - 4155.51 | $22 to its low | 14 Oct 15:00 (the CPI candle) | first touch by 15 Oct 15:00 |
| 4H supply | 4154.40 - 4189.38 | $71 | 13 Oct 19:00 (tested once) | first touch by 14 Oct 19:00 (closing) |

The 1D demand 4065-4223 that price sits in is spent (touched 1524 h after it formed) and daily zones are not traded
anyway. The diagnostic short run reached the 1H zone 4105-4155 and stopped only at "no 5m data": on the laptop the
window will look for a 5m shift there. A short from that zone would be a late entry by the gold study's measure: the last
24 hours moved -4.3 hourly ATRs (the "chase" bucket, IS +0.45R a trade, OOS -0.31R), though the day's span (5.5 ATR) is
under the 8-ATR expanded-day cut.

### NAS100 (price 30078.7 HistData level, 30080 on Capital.com)

| TF | Bias | Liquidity | Balance | Last breaks |
|---|---|---|---|---|
| 1M | 50/50 | bearish | bullish | BOS bullish 22243.6 (Jun); BOS bullish 26219 (Apr) |
| 1W | bullish | bullish | bullish | BMS bullish 30244.5 (week of 20 Sep); BOS bullish 30759.9 (27 Sep) |
| 1D | bullish | bullish (sell-side swept at 30552) | bullish (gap 29704-30366 mitigated) | BOS 30642 (2 Oct); BOS 30797 (5 Oct) |
| 4H | bearish | bearish | bearish | BOS 30370.7 (14 Oct 11:00 Ams); BOS 30260.8 (15:00) |
| 1H | bearish | bearish | bearish | BOS 30260.8 (17:00); BOS 30093.2 (18:00) |

Decision: **neutral, no trade** (1M 50/50, 1W and 1D bullish, 4H and 1H bearish: fewer than three agree). The weekly veto
blocks shorts regardless; longs need the 4H and 1H to turn (a 1H close back above 30274 then 30370 would start that).
Fresh supply at 30126-30274 (1H, formed 18:00) and 30370.7-30632.7 (4H, 15:00) sits 47 and 292 points above price but
cannot be traded. The demand below (4H 29616-29776, 1D 28942-29731) is 24 days old: too old by the 24 h rule, and the
weekly/4H demand 29616-30244 price is in is spent. Expect no NAS100 signal until the intraday structure re-aligns with
the weekly and daily, or the daily flips (a daily close under 29704).

### BTCUSD (price 81925)

The reading depends on how the daily and 4H candles are anchored, which is the open item of the research backlog
(`BACKLOG_hand.md` 1, task 80):

| Anchoring | 1M | 1W | 1D | 4H | 1H | Decision |
|---|---|---|---|---|---|---|
| 17:00 New York (an MT5 server; what the FTMO window most likely sees) | bullish | bullish | bearish | bearish (gap 83012-83252 unmitigated) | bearish | **bearish, scalp (1D+4H+1H)**: 4H and 1H zones, stake 1.5 % x 0.5 = 0.75 % |
| UTC midnight (the research ledgers) | bullish | bullish | bearish | 50/50 (its bearish P broken) | bearish | **neutral, no trade** |

Zones under the New York anchoring: fresh 4H supply 82880-83844 and 1H supply 83012-83844 (both formed 15:00 Amsterdam,
$955 above price, tradable until 15 Oct 15:00); the 1H demand 81337-83032 price sits in has a 29-hour-old visit (stale by
`max_visit_age_by_tf`), the 4H demand 80395-81914 and the 1D demand 80578-85094 are spent. The regime work's BTC caveat
stands: +39R of the +62R in-sample came from one quarter (2026Q2).

## Regime now against the regime the edge was measured in

| | er20 now | IS median / percentile | ATR14 % now | IS median / percentile | last-year ATR pct | 20 d / 60 d return | last 24 h (hourly ATRs): span, net |
|---|---|---|---|---|---|---|---|
| EURUSD | **0.57** | 0.21 / **97th** | 0.63 % (70 pips) | 0.59 / 60th | 82nd | -3.0 % / -2.5 % | 6.9, -4.6 |
| XAUUSD | 0.21 | 0.20 / 53rd | 1.92 % ($78) | 1.55 / 62nd | **12th** | -4.2 % / -1.1 % | 5.5, -4.3 |
| NAS100 | 0.25 | 0.19 / 63rd | 1.44 % (434 pt) | 1.56 / 39th | 24th | +3.9 % / +3.4 % | 6.3, -4.0 |
| BTCUSD | 0.19 | 0.19 / 49th | 2.50 % ($2051) | 3.44 / **15th** | 23rd | -2.9 % / +30.0 % | 5.1, -2.8 |

What the ledgers said about these buckets (R after 0.10R costs, `S/regime/regime.out`):

- EURUSD: er20 0.57 is beyond every in-sample trade (the IS trades sat at 0-0.5; the best bucket 0.2-0.5 made +1.1R a
  trade). Out-of-sample the 0.5-1.0 bucket held 14 trades, 36 % won, +0.34R a trade. The edge was not measured in a
  trend this efficient; it was not negative there either. The ATR band (0.57-0.72 %) is the IS bucket that earned +1.31R
  a trade.
- Gold: er20 0.21 is the 0.2-0.35 bucket: IS 41 trades, 51 %, +0.44R; OOS 99 trades, 28 %, -0.21R. The note from the
  regime work (gold lost 72R OOS under er20 0.35 and earned +10R above) applies now. ATR 1.92 % is normal for the IS
  years (+0.54R bucket) and calm against the last year (12th percentile).
- NAS100: er20 0.25 is the one bucket negative OOS (34 trades, 18 %, -0.54R) and positive IS (9 trades, +0.76R); the
  ATR band 1.38-2.06 % is the best in both periods (+1.31R IS, +1.14R OOS). The bias makes the question moot for now.
- BTC: the calm bucket (ATR under 3.6 %) was +0.50R a trade IS and the only OOS-positive bucket (+0.20R); er20 0-0.2
  IS +0.41R, OOS -0.23R.

Verdict on the regime: gold and NAS100 sit inside the measured range with mixed in- and out-of-sample signs; BTC sits in
its best-measured volatility band; EURUSD is in an unmeasured, unusually efficient down-trend after a USD shock.

## High-impact calendar, 14 October - 7 November, Amsterdam time

Blackout = no new entry 30 minutes either side; the windows are 09-11 and 13-17. USD events apply to all four markets,
EUR events to EURUSD only (`currencies_of`: gold, indices and crypto read USD only). Times already include the clock
changes (Amsterdam 25 Oct, New York 1 Nov).

| Day | Time (Ams) | Ccy | Event | Blackout | Window hit |
|---|---|---|---|---|---|
| Thu 15 Oct | 14:30 | USD | PPI, Retail Sales (plus claims, Philly Fed, Empire State at 14:30) | 14:00-15:00 | afternoon |
| Fri 16 Oct | 05:30 | USD | Fed Chair Warsh speech | 05:00-06:00 | none |
| Tue 20 Oct | 11:00 | EUR | ZEW | 10:30-11:30 | morning, last half hour (EURUSD) |
| Tue 20 Oct | 14:30 | USD | Housing starts, building permits | 14:00-15:00 | afternoon |
| Fri 23 Oct | 09:30 / 10:00 | EUR | German / eurozone flash PMIs | 09:00-10:30 | morning (EURUSD) |
| Fri 23 Oct | 15:45 | USD | US flash PMIs (medium on TradingView, often red on ForexFactory) | 15:15-16:15 | afternoon |
| Mon 26 Oct | 10:00 | EUR | Ifo | 09:30-10:30 | morning (EURUSD) |
| Tue 27 Oct | 13:30 | USD | Durable goods (08:30 ET lands at 13:30 this week) | 13:00-14:00 | afternoon, first hour |
| Tue 27 Oct | 15:00 | USD | CB consumer confidence (medium on TV) | 14:30-15:30 | afternoon |
| Wed 28 Oct | 08:00 | EUR | GfK | 07:30-08:30 | none |
| Wed 28 Oct | **19:00 / 19:30** | USD | **FOMC decision / press conference** | 18:30-20:00 | none: open positions run through it |
| Thu 29 Oct | 13:30 | USD | GDP advance, core PCE, personal income/spending, claims | 13:00-14:00 | afternoon, first hour |
| Thu 29 Oct | 14:15 / 14:45 | EUR | **ECB decision / press conference** | 13:45-15:15 | afternoon (EURUSD blacked out 13:00-15:15) |
| Fri 30 Oct | 10:00 / 11:00 | EUR | German and eurozone GDP flash | 09:30-11:00 | morning (EURUSD) |
| Fri 30 Oct | 14:00 | EUR | German CPI prelim | 13:30-14:30 | afternoon (EURUSD) |
| Fri 30 Oct | 14:30 | USD | Employment cost index (medium) | 14:00-15:00 | afternoon |
| Mon 2 Nov | 15:00 | USD | ISM manufacturing | 14:30-15:30 | afternoon |
| Tue 3 Nov | 01:00 | USD | Midterm elections (results through the European morning of 4 Nov) | 00:30-01:30 | none |
| Tue 3 Nov | 16:00 | USD | JOLTS | 15:30-16:30 | afternoon |
| Wed 4 Nov | 11:00 | EUR | Eurozone CPI flash | 10:30-11:30 | morning (EURUSD) |
| Wed 4 Nov | 14:15 / 15:00 | USD | ADP (medium) / ISM services | 13:45-15:30 | afternoon |
| Fri 6 Nov | 14:30 | USD | **Non-farm payrolls, unemployment, earnings** | 14:00-15:00 | afternoon |
| Fri 6 Nov | 16:00 | USD | Michigan sentiment prelim | 15:30-16:30 | afternoon |

Weekly jobless claims fall every Thursday at 14:30 (13:30 in the mismatch week); ForexFactory usually marks them red.
Note: the repo's fallback file `data/calendar/high_impact.csv` has 15 Oct retail sales at 13:30 UTC (14:30 Amsterdam
would be 12:30 UTC); only the hourly ForexFactory refresh makes this harmless.

## The clock-change week, 26 October - 1 November

Amsterdam moves to winter time on Sunday 25 October, New York on Sunday 1 November, so for one week the gap is 5 hours:

| | until 24 Oct | 26-30 Oct | from 2 Nov |
|---|---|---|---|
| US 08:30 ET releases | 14:30 Ams, blackout 14:00-15:00 | **13:30 Ams, blackout 13:00-14:00 (the afternoon window's first hour)** | 14:30 Ams |
| US cash open 09:30 ET | 15:30 | **14:30** | 15:30 |
| FOMC 14:00 ET (28 Oct) | 20:00 | **19:00** | 20:00 |
| US cash close 16:00 ET | 22:00 | **21:00** | 22:00 |
| FTMO server day roll and nightly restart (17:00 ET) | 23:00 (the 23:01 "server lost" messages) | **22:00** | 23:00 |
| FX week open (Sunday 17:00 ET) | 23:00 | **22:00 on Sunday 25 Oct** | 23:00 |

For the bot nothing structural changes: the entry windows are Amsterdam clock, the daily candle stays anchored at the New
York close, and `MT5Broker.offset_from_week_close` re-reads the server offset every hour, so the server's own switch on
1 November is followed automatically. Two things to check on the laptop: (1) `scripts/ftmo_local.bat` must not pin
`MT5_SERVER_OFFSET_HOURS`; if it does, the value changes from 3 to 2 on 1 November; (2) on Monday 26 October read the
08:45 message's blackout minutes against this table (durable goods 13:30 Tuesday, GDP/PCE 13:30 Thursday). The watchdog's
nightly "MT5 lost its trade server" pair will arrive at 22:01/22:02 instead of 23:01/23:02 that week. FTMO's daily-loss
reset stays at midnight Prague time.

## Verdict per market

**EURUSD: trade as the engine says, with caution.** Shorts only, and only from the two fresh CPI-day supply zones
(1.11374-1.11985 within 24 h, 1.11516-1.12113 until 11:00 tomorrow), at a quarter of the stake (0.375 % on the 1H zone,
0.75 % on the 4H) because the month reads 50/50 and the match is the 1D+1H pair. The regime (er20 0.57, 97th percentile
of 2024-2026) is one the edge was never measured in: no in-sample trade came in a trend this efficient, and the
out-of-sample bucket was thin and mildly positive. A 16-month low with USD bid into FOMC is also where sharp counter-moves
start; the small stake is the right size for that. ECB day (29 Oct) blacks EURUSD out from 13:00 to 15:15.

**XAUUSD: expect signals, and know they come at the largest stake in the book.** Four of five timeframes bearish; the
fresh supply 4105-4155 is $22 above price and a 5m shift inside it tomorrow morning is a 1.5 % short (3 % if the 4H
version is the zone matched). The daily reads 50/50 after sweeping sell-side at 4110, the day moved -4.3 hourly ATRs
(the chase bucket that won out-of-sample 27 %), and gold's er20 0.21 is in the band where the 2017-2023 ledger lost.
None of this is a rule in the profile; it is the reason to accept the trade size with eyes open and not to add to it.

**NAS100: expect few signals.** Neutral with the weekly veto against shorts and the intraday structure against longs;
the demand below is too old by the 24 h rule. A long needs the 1H and 4H to flip back up (closes above 30274 and 30370)
and a fresh demand zone to form; a short needs the daily and the weekly to turn. The regime (ATR 1.44 %) is the best
measured band, so when a signal comes it is in familiar conditions. Earnings season and the 3 November midterms are gap
risks for a 48-hour position.

**BTCUSD: caution, and verify the candles first.** On New-York-anchored candles the window reads bearish-scalp with a
fresh 4H/1H supply at 82880-83844 ($955 above, half stake 0.75 %); on UTC-anchored candles it reads no trade. The same
market, two readings, because the 4H's last bearish gap survives in one anchoring and its P breaks in the other. The
regime itself is benign (ATR 2.5 %, the calm band that was positive in both periods). The anchoring question (task 80)
decides whether tonight's live reading matches the ledgers: export the terminal's D1 and W1 bars for BTCUSD and read the
hour the daily bar starts and the weekday the weekly bar starts; the TradingView feed `FTMO_OANDA:BTCUSD.SIM` exists but
this account has no permission for it (connecting the FTMO broker in TradingView would show the same bars).

## Files

- Report: `research/regime_now.md` (this file); scripts and data: `research/regime_now/` (`build_cache.py`, `add_15m.py`,
  `regime_now.py`, `calendar_ams.py`, `tv/*.json` raw TradingView payloads, `cache/` and `cache_utc/` the spliced candles).
- Dossiers with charts: `research/regime_now/dossiers/{EURUSD,XAUUSD,NAS100,BTCUSD,BTCUSD_UTC}/` (README.md, dossier.json,
  1D.png, 4H.png, 1H.png, 15m.png; `assume_long/`, `assume_short/` for the diagnostic walks).
