# The odds of a trade on a day like 16 October (no market tradable at 08:35)

Asked by Max on Friday 16 October, the third day of the challenge without a trade: "Dus weer niks voor vandaag?"
Measured on the baseline backtest of the live profiles (2024-02-01..2026-09-24, FTMO costs; 2026 = January-September),
Amsterdam weekdays, with the engine's 08:35 bias decision recomputed per market and day (fidelity 142/142, 47/47, 43/43,
85/85 against the trades' recorded bias). Three independent checks reproduced every row; the corrections are below.

| Question | 2024-02..2026-09 | 2026 |
|---|---|---|
| A trade in any market on a weekday | 244/691 = 35 % | 69/191 = 36 % |
| ... when no market was tradable at 08:35 | 49/280 = 18 % | 17/88 = 19 % |
| ... and the previous 2 weekdays were empty | 20/139 = 14 % | 6/40 = 15 % |
| ... and NAS100 and BTC could not turn that day (as on 16 Oct) | 11/118 = 9 % | 4/33 = 12 % |
| EURUSD with the week against (as on 16 Oct) | 0/91 | 0/32 |
| XAUUSD with "1H not aligned" (as on 16 Oct) | 27/201 = 13 % | 4/32 = 13 % |
| NAS100 with no side left for the day (1D 50/50 or 1W against 1D) | 0/177 | 0/45 |
| On days like this that still traded: first trade 13:00-17:00 | 41/49 | 14/17 |
| ... and it was gold | 29/49 | 10/17 |

Correction from the checks: the cloud review reads BTC on UTC-midnight candles, while the live window's candles cut the
day at 17:00 New York; the two 08:35 decisions differ on 379 of 691 mornings. On the window's candles the odds for a day
like 16 October rise to about 13-17 % (from 6-14 %), so the honest range is about 9-17 % (no trade about 83-91 %).

Empty runs (no trade in any market): 141 runs, median 2 weekdays, longest 19 (2025-07-25..2025-08-20; in 2026 15,
2026-04-01..04-21); 40 % of runs reach 3 weekdays (2026: 50 %). From the third empty weekday: a trade on the next weekday
27 %, within 5 weekdays 79 %, within 10 weekdays 91 % (2026: 28 %, 78 %, 94 %). A start like the challenge's (any
weekday as day 1) has no trade in its first 3 weekdays 31 % of the time; then the median first trade is weekday 6 (2026:
weekday 5), 75 % come by weekday 8 and 92 % by weekday 13 (2026: 82 %, 95 %).

The portfolio cap (2 open, 1 per market, EURUSD 2) and the live guard's day room remove 8 of 317 trades and no trade
day. Files: scratchpad `today_odds/` (per-market tables `morning_<SYM>/days.csv`, `combine/results.md`, the checks).
