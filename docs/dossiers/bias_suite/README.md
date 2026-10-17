# The bias gate against his dated days: four readings, none his

`scripts/bias_suite.py` on `docs/dossiers/source_bias.yaml` (his conclusion on four dated days; his per-timeframe readings
only for 11 Nov 2025, from the dollar-index mirror shown in the course). Every reading uses the course's rule for one
timeframe (liquidity view and balance view must agree, else 50/50; A 00:56:54, 02:14:26) and the 3-of-5 rule.

| Reading | 11 Nov 2025 EURUSD (his: bearish on all five) | 18 Mar 2024 EURUSD (his: bearish) | 9 Dec 2025 EURUSD (his: bullish) | 26 Aug 2026 gold (his: bearish) |
|---|---|---|---|---|
| Own levels, balance = the last gap formed (the code so far) | 1M 50/50, 1W 50/50, 1D 50/50, 4H 50/50, 1H bearish: none | 1M 50/50, 1W bull, 1D 50/50, 4H bear, 1H bull: none | 1D+4H+1H bullish: scalp (his) | 1M bear, 1W 50/50, 1D bull, 4H bull, 1H bear: none |
| DXY mirror for 1M/1W/1D (A 00:56:25), inverted | 1M 50/50, 1W 50/50, 1D bullish: none | 1M 50/50, 1W bear, 1D 50/50: none | scalp (his) | all 50/50: none |
| Own levels, balance = the last balance level tested (A 00:57:51) | 1M 50/50, 1W 50/50, 1D bearish: none | 1W bull, 1D bull: none | scalp (his) | 1M bear, 1W bear, 1D bull: none |
| DXY mirror + last tested | all 50/50: none | none | scalp (his) | none |

Where the code reads 50/50 on the monthly and weekly, its liquidity view and balance view disagree: on 11 Nov 2025 the
monthly liquidity view is bearish (a buy-side sweep at 1.19092) and the balance view bullish (the last gap formed, and
also the last gap tested, is a bullish one). He read both bearish, from the dollar index; on the dollar index our
inverted reading gives the same disagreement the other way round. So the difference is not which chart but which balance
level and which liquidity event he counts. Four conclusions and one set of per-timeframe readings are too few to settle
that; the four readings above are left as options (`bias.balance_view`, `bias.mirror_symbol`, both off in the profiles)
until his per-timeframe readings on more dated days are in `source_bias.yaml`.
