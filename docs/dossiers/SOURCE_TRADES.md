# Dorus's own trades against the code

Every dated trade of his that Max has supplied so far, with his numbers (from screenshots of his recaps; the images stay
outside the repository), what the engine saw at that moment on 1-minute candles with the strict reading of the course
(`config/dorus_course.yaml` + `confirmation_tf_mode: exact`, `entry_outside_zone`, `stop_basis: confirmation`), and the
first difference. "Diagnostic" means the walk-through past the bias gate (`scripts/minute_walk.py`, `decision-dossier --assume`).

| # | Trade (his) | Zone in the code | Code's bias | Code's entry (diagnostic) | Code's stop | First difference |
|---|---|---|---|---|---|---|
| 1 | Gold short 26 Aug 2026, entry 4624.53, stop 4639.55, target about 29.5 points lower (K3; clock unverified) | 1H bearish 4629.23-4658.56, tested, price below it | refused (1M bear, 1W 50/50, 1D bull, 4H bull, 1H bear) | none: the only active zone (daily) gives 0.22R | - | bias; his stop 10-15 points from the entry |
| 2 | Gold short 26 Aug 2026, entry 4623.59, stop 4633.72 (K3) | as above | refused | none | - | as above |
| 3 | EURUSD short 11 Nov 2025 15:0x-15:16 UTC, entry 1.15963, stop 1.16060, target 1.15687, 2.85R, won | 4H bearish 1.15853-1.16283 and 1H bearish 1.15967-1.16111 | refused (1M, 1W, 1D 50/50; 4H, 1H bull); he read M/W/D bearish from DXY | short at 14:15 UTC, 1.15975, 5m shift at 14:10 | 1.16057 (sweep high); his 1.16060 | bias from another chart; target (code 1.15468, his 1.15687) |
| 4 | EURUSD short 18 Mar 2024 about 12:40 UTC, stop 9.5 pips, target 29.3 pips, 3.08R, won | 1H bearish 1.08994-1.09140, 4H bearish 1.08918-1.09312, daily and weekly bearish zones above | refused (1M 50/50, 1W bull, 1D 50/50, 4H bear, 1H bull) | short at 12:30 UTC 1.09034 (1m shift) and 12:40 UTC 1.08966 (5m shift) | 1.09061 (sweep high); his about 1.0905 | bias; target (code 1.08805, his about 1.0866) |
| 5 | EURUSD long 9 Dec 2025 15:36 UTC, entry 1.16335, stop 1.15908 ("protect de low" of the weekly P), target 1.16823 (the weekly high), 1.14R, won | 4H bullish 1.16204-1.16522 (active) and 1.15903-1.16188; the weekly zone is the 1 Dec candle | bullish, scalp only (1D+4H+1H) | none by 15:45: the 5m close of 15:30 (1.16353) stayed 0.4 pip under the top of the bearish 5m gap 1.16252-1.16357 | - | the shift threshold by 0.4 pip on our feed; his stop is the weekly P (swing), not a sweep extreme |
| 6 | EURUSD short, undated Short, stop 3.7 pips, target 4.6 pips, 1.24R | - | - | - | - | a scalp from a lower-timeframe zone; no date |

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

## Still needed from the source

More dated trades, with losers and refused setups; whether DXY is part of his EURUSD bias as a rule; the K3 clock.
