# BTCUSD, 14-16 September 2026: Dorus's third buy of the 21,000 EUR BTC trade, as the engine read it

Source: three frames of the academy recording "21.000 euro verdiend met bitcoin" (INDEX:BTCUSD, chart clock UTC+2),
relayed by Astra on 4 October: the daily overview with the crosshair on Saturday 8 August (the first buy), the 4H with
the marked highs and lows (x) and the crosshair on Thursday 3 September 02:00, and the 4H with the circled low at
Monday 14 September 14:00 (12:00 UTC), the area of the third buy. No order labels: entry, stop and target are not
confirmed. The frames themselves stay out of the repository.

What he drew: sell-side liquidity (x) at the lows 75,500-76,000 and buy-side liquidity (x) at 82,400 above; the low
is swept on 14-16 September and price runs to 81,300 by 4 October. The read is a long after the sweep of the lows
with the weekly bullish, target the liquidity above.

## What the engine read (BTC profile with the previous-high target and W+D+4H, `eval_btc_prevext_wd4h`, 3-day warm-up)

At 14 September 12:00 UTC (the circled low's crosshair):

- 1W bullish, 1H bullish. 1D 50/50: liquidity view bullish (sell side swept at 76,228 two candles earlier), balance
  view bearish (a bullish P 76,941-82,281 broken, read as continuation bearish). 4H 50/50: liquidity bullish (BMS up
  through 77,480), balance bearish (mitigated bearish gap 77,506-77,680). Two of five aligned: no trade.
- Diagnostic setup the code would reach: LONG from the 1H zone 76,040-77,459 (formed 11 Sep 13:00), entry 77,730,
  stop 77,348, target 79,836 (R:R about 5.5), i.e. the same side as his buy, at a higher price.
- 16 September 04:00-16:00 UTC: 1D and 4H read bearish, 1W bullish, 1H bullish; refused all day. Diagnostic: LONG from
  the 1D zone 68,858-78,003, entry 75,923, stop 74,913, target 82,280 (R:R about 6.3): his entry area and his target.

So the engine saw the zone, the sweep and the target and refused on the bias: the daily and 4H balance views read a
broken bullish P as bearish continuation while he reads the sweep of the lows as the bullish event. Two readings that
turn this into a trade are running on BTC 2026: `bias.conflict_rule recent` (the sweep, two candles old, outranks the
older P break) and `bias.balance_violation neutral` (a broken P is 50/50 instead of a flip). Results in
`docs/backtests/winrate/README.md`.

## Minute walk, distinct engine states (`scripts/minute_walk.py`, long)

### 14 September 08:00-18:00 UTC

- 08:00: px 77841.41000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 09:05: px 77730.41000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | diagnostic: 1H bullish POI 76040.02000-77459.39000 (tested, formed 2026-09-11 13:00:00) would give LONG entry 77730.4 stop 77348.0 target 79836.8 (BS  || DIAG LONG entry 77730.4 stop 77348.0 (the low si
- 09:10: px 77774.31000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 09:51: px 78047.11000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (tested, formed 2026
- 10:13: px 77994.78000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 10:15: px 78007.90000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (tested, formed 2026
- 10:17: px 77997.20000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 10:23: px 78010.44000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (tested, formed 2026
- 10:24: px 77960.77000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 11:30: px 77886.90000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | diagnostic: 1H bullish POI 76040.02000-77459.39000 (tested, formed 2026-09-11 13:00:00) would give LONG entry 77886.9 stop 77348.0 target 79836.8 (BS  || DIAG LONG entry 77886.9 stop 77348.0 (the low si
- 11:35: px 77689.68000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (tested, formed 2026-08-24 00:00:00): touched at 2026-09-11 01:34:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026
- 12:05: px 77783.74000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=50/50, 4H=50/50, 1H=bullish) -> no trade | diagnostic: 1H bullish POI 76040.02000-77459.39000 (tested, formed 2026-09-11 13:00:00) would give LONG entry 77783.7 stop 77348.0 target 79836.8 (BS  || DIAG LONG entry 77783.7 stop 77348.0 (the low si

### 16 September 04:00-16:00 UTC

- 04:00: px 75764.18000 bias=bearish | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 2026-08-21 00:00:00): touched at 2026-09-12 21:21:00, waiting for confirmation on 1H
- 09:00: px 75649.84000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=50/50) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 20
- 10:00: px 75922.65000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=50/50) -> no trade | diagnostic: 1D bullish POI 68858.17000-78002.74000 (active, formed 2026-08-21 00:00:00) would give LONG entry 75922.6 stop 74913.4 target 82280.6 (BS  || DIAG LONG entry 75922.6 stop 74913.4 (the low 
- 11:00: px 75898.07000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 12:16: px 76030.83000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 12:17: px 76058.26000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 12:19: px 76022.84000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 12:20: px 76043.23000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 12:21: px 75987.50000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 13:11: px 75622.61000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 13:14: px 75729.20000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 
- 13:33: px 75642.61000 bias=refused: fewer than 3 timeframes agree (1M=50/50, 1W=bullish, 1D=bearish, 4H=bearish, 1H=bullish) -> no trade | 1W bullish POI 62689.89000-76664.18000 (active, formed 2026-08-24 00:00:00): touched at 2026-09-13 09:24:00, waiting for confirmation on 4H || 1D bullish POI 68858.17000-78002.74000 (active, formed 

