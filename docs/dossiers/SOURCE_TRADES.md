# Dorus's own trades against the code

Every dated trade of his that Max has supplied so far, with his numbers (from screenshots of his recaps; the images stay
outside the repository), what the engine saw at that moment on 1-minute candles with the strict reading of the course
(`config/dorus_course.yaml` + `confirmation_tf_mode: exact`, `entry_outside_zone`, `stop_basis: confirmation`), and the
first difference. "Diagnostic" means the walk-through past the bias gate (`scripts/minute_walk.py`, `decision-dossier --assume`).

| # | Trade (his) | Zone in the code | Code's bias | Code's entry (diagnostic) | Code's stop | First difference |
|---|---|---|---|---|---|---|
| 1 | Gold short 26 Aug 2026 about 13:45 UTC (his chart runs on UTC+1: the position tool starts 14:46, and 4624.53 traded 13:44-13:45 and 13:50-13:51 UTC), entry 4624.53, stop 4639.55 (0.4 above the morning high 4639.14 of 08:00-08:15 UTC), target 4594.98 (1.0 above the 24 Aug low 4594.00), 1.97R, won 16:02 UTC | 1H bearish 4629.23-4658.56 (B 4643.97-4654.60), tested, visit open, price just below it | refused (1M bear, 1W 50/50, 1D bull, 4H bull, 1H bear) | none at 13:45: both 1H zones "waiting for confirmation on 1m" (no opposing 1m balance level since the 13:27-13:30 re-entry; the 13:13 bullish gap was dropped by the size threshold) | - | bias; then no 1m shift in the code's model at his minute |
| 2 | Gold short 26 Aug 2026 15:05 UTC (tool start 16:05 on the UTC+1 chart; 4623.59 traded in the 15:05 candle), entry 4623.59, stop 4633.72 (0.46 above the 15:00 sweep high 4633.27, which is also his B label 4633.25), target 4595.62 (1.6 above the 24 Aug low), 2.76R, won 16:02 UTC; 17:05 Amsterdam, after his stated 17:00 cut-off (16:05 on his chart's clock) | as above | refused (1H 50/50 by 15:30) | none at 15:05: "waiting for confirmation on 1m" (the climb 14:45-15:00 left no bullish 1m or 5m gap, so the 15:01 drop closes through nothing the model calls a balance level) | - | bias; then no balance level to shift through; the session clock |
| 3 | EURUSD short 11 Nov 2025 15:0x-15:16 UTC, entry 1.15963, stop 1.16060, target 1.15687, 2.85R, won | 4H bearish 1.15853-1.16283 and 1H bearish 1.15967-1.16111 | refused (1M, 1W, 1D 50/50; 4H, 1H bull); he read M/W/D bearish from DXY | short at 14:15 UTC, 1.15975, 5m shift at 14:10 | 1.16057 (sweep high); his 1.16060 | bias from another chart; target (code 1.15468, his 1.15687) |
| 4 | EURUSD short 18 Mar 2024 about 12:40 UTC, stop 9.5 pips, target 29.3 pips, 3.08R, won | 1H bearish 1.08994-1.09140, 4H bearish 1.08918-1.09312, daily and weekly bearish zones above | refused (1M 50/50, 1W bull, 1D 50/50, 4H bear, 1H bull) | short at 12:30 UTC 1.09034 (1m shift) and 12:40 UTC 1.08966 (5m shift) | 1.09061 (sweep high); his about 1.0905 | bias; target (code 1.08805, his about 1.0866) |
| 5 | EURUSD long 9 Dec 2025 15:36 UTC, entry 1.16335, stop 1.15908 ("protect de low" of the weekly P), target 1.16823 (the weekly high), 1.14R, won | 4H bullish 1.16204-1.16522 (active) and 1.15903-1.16188; the weekly zone is the 1 Dec candle | bullish, scalp only (1D+4H+1H) | none by 15:45: the 5m close of 15:30 (1.16353) stayed 0.4 pip under the top of the bearish 5m gap 1.16252-1.16357 | - | the shift threshold by 0.4 pip on our feed; his stop is the weekly P (swing), not a sweep extreme |
| 6 | EURUSD short, undated Short, stop 3.7 pips, target 4.6 pips, 1.24R | - | - | - | - | a scalp from a lower-timeframe zone; no date |
| 7 | BTCUSD short, 2 Sep 2026 about 13:00-14:00 UTC, entry about 77,100, closed about 77,780 on 3 Sep about 02:00 UTC: his own post calls it a loss that fits his strategy (Astra's control of 2 October, p. 6; the H1 screenshot has no order fields; the year follows from the price path on Bitstamp: 2 Sep low 76,229, 3 Sep rally to 82,281) | not mapped: no BTC history in the project; TradingView reaches back to 2 Sep on 15m and 1H only | - | - | - | read from the bars: a short into the bearish 1H zone left by the 2 Sep 08:00 drop (77,431 to 76,701), after the sweep of the 10:00 low; stop above the 03:00 swing high 77,747; stopped by the 02:00 candle of 3 Sep (high 77,860) before price fell back to 77,080 and then ran to 82,000. His losers look like ours: a correct zone, a sweep, a stop over the previous high, taken out by the next push |

## What the trades settled, and what they changed in the code

- Trade 3 exposed two programming gaps (fixed, commit `9cfd67b`): the balance-shift search started at the visit's first touch and
  stopped at an old crossing far from the zone; a zone price had just left was no candidate.
- Trades 4 and 5 exposed a third (fixed in this commit): the search kept only the first in-reach crossing, so a shift that
  fell outside the entry window, or was not taken, blocked every later one. Every opposing gap now gives its own candidate.
- With these, the engine's diagnostic entries sit within 1.2 pips of his on trades 3 and 4, and its sweep-extreme stop within
  0.3 pip of his on both. The bias gate still refuses both: on EURUSD's own levels the monthly, weekly and daily read 50/50,
  he read them bearish (trade 3 from the dollar index, as the course shows for that period).
- Stops: his intraday entries (1, 2, 3, 4) sit just beyond the sweep extreme; his swing entry (5) sits on the weekly P.
  The written plan's "minimaal 1H P" fits neither literally. Reading: intraday and scalp trades protect the sweep extreme,
  swing trades the zone's P. Measured by R6 (zone's P) and R7 (sweep extreme).
- Targets: his are the nearest previous low/high of the move (trades 3, 4: the pre-impulse low; trade 5: the weekly high),
  the code's `liquidity_nearest` with the 1H floor sometimes picks a deeper pool (trade 3: the Asia low). Open.
- K3 (2 October, with Astra's drawn positions and the 1-minute prices): the clock is settled by price, not by the tool labels:
  his chart runs on UTC+1, the entries are about 13:45 and 15:05 UTC. His stops sit 0.4-0.5 above the previous high (the
  morning high for the first, the sweep high at B for the second); his targets sit 1.0-1.6 above the 24 Aug low, 29.5 and
  28.0 points away (2.0R and 2.8R), past the nearer 25 Aug low 4604.8 that the code's `liquidity_nearest` picked. The engine,
  walked past the bias gate at both minutes, finds no balance shift: the 1m climb before each drop left no gap the model calls
  a balance level (`docs/dossiers/XAUUSD_2026-08-26_1m/2026-08-26_13_45`, `..._15_05`). Walked minute by minute (`minute_walk_*.txt` in that folder), the engine's shift for the first short comes at 13:46 UTC: a diagnostic short at 13:47, entry 4619.3, stop 4632.66 (the 13:30 sweep high), target 4604.81 (the 25 Aug low), 1.08R, two minutes after his and 5 points lower, with a 7-point tighter stop and a 10-point nearer target. For the second short nothing comes in either variant (balance shift, first candle): the 1H reads 50/50 by then and no opposing gap exists.
- DXY (Astra's control, 2 October): the course couples a DXY long to an EURUSD short (56:15-1:02:07) and from 1:01:23
  analyses EURUSD itself; no rule that DXY decides or overrides the EURUSD bias was found in the course or the academy lesson.
  The DXY filter stays a hypothesis, not a rule, and is not in any profile.

## Still needed from the source

More dated trades, with losers and refused setups (one loser so far, trade 7, without order fields); the academy's bias lesson in
his words (DXY); his session clock when he trades from another time zone (trade 2); BTC 1-minute history if trade 7 is to be replayed.
