# The last month on his rules: gold and EURUSD, 24 August to 25 September 2026

Second pure profile (`config/dorus_pure.yaml` at 1f7e2b5), bid quotes, 5-minute steps, no guard halt.

| Symbol | Opened (UTC) | Side | Zone | Confirmation | Entry | Stop | Target | Planned R:R | Result |
|---|---|---|---|---|---|---|---|---|---|
| XAUUSD | 2026-09-22 07:00 | short | 1M | BMS on 4H | 4323.39 | 4369.51 | 4235.16 | 3.8 | -1.00R stop |
| XAUUSD | 2026-09-23 11:15 | short | 1H | BS on 15m | 4316.40 | 4345.65 | 4291.24 | 0.9 | +0.86R target |
| EURUSD | 2026-09-11 08:05 | short | 4H | BMS on 5m | 1.16079 | 1.16126 | 1.15997 | 1.4 | +1.74R target |
| EURUSD | 2026-09-24 13:25 | short | 1H | BS on 15m | 1.13706 | 1.13819 | 1.13532 | 0.9 | -1.00R stop |

Four trades, two winners, +0.6R. A third gold signal was refused because a trade was already open.

## 26 August: Dorus's two gold shorts, and why the code took none

Dorus's K3 lesson shows two shorts on 26 August (entries 4624.53 and 4623.59, stops 4639.55 and 4633.72,
targets about 29 points lower, 1.97R and 2.76R). The decision dossiers in `docs/dossiers/XAUUSD_2026-08-26/`
at 14:00 and 15:30 UTC show what the code saw: a bearish 1H zone being touched, but the bias table said
no trade (1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50: no listed combination). The daily and
4H were read bullish from a bullish break and a sell-side sweep. K3 itself says these scalps give less
weight to the monthly, weekly and daily than usual. So the first direct comparison with one of his own
trades says: the zone was there, the gate that stopped the code was the bias table, and either his
reading of the 1D/4H differs from the code's or his gold scalps do not use the table. That question is
in the handoff to Astra.
