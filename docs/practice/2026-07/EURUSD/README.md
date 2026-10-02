# EURUSD, July 2026: the month the way we read it, for review against Dorus

The live profile `config/dorus_live.yaml` (reading F: 5m shifts for 1H zones, 15m for 4H, 1H for daily; the sweep-extreme stop with an 8-pip minimum; the target on the previous low/high; one trade per zone per visit; entries at most half the zone deep; 1D/4H/1H zones only; sessions, news, FTMO margins). Review question per chart: would Dorus take this, and if not, what is different?

## The trades the code took (2 in July; 0 won, -2.00R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P3 | Thu 02 Jul 11:15 | SHORT | 4H 1.14178-1.14618 (15m shift) | 1.14073 | 1.14210 | 1.13245 | 5.63 | 4H previous low 1.13245 | stop -1.00R | [EURUSD_003_20260702_1115_15m.png](charts/EURUSD_003_20260702_1115_15m.png) |
| P4 | Wed 29 Jul 08:05 | LONG | 1H 1.13902-1.13943 (5m shift) | 1.13948 | 1.13858 | 1.14181 | 2.70 | 1H previous high 1.14181 | stop -1.00R | [EURUSD_004_20260729_0805_5m.png](charts/EURUSD_004_20260729_0805_5m.png) |

Each chart shows the candles of the entry timeframe up to the entry, the zone with X / B / P, the stop and the target; the title gives the outcome. The ledger (`ledger_v5.csv`) carries every field, including the warm-up weeks before the month (2 trades, +1.50R).


Config `config/dorus_live.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Wed 01 | 50/50 | bearish | bearish | 50/50 | 50/50 | none | 1.14057 | 1H bullish 1.13908-1.14151; 1H bullish 1.13825-1.13933; 4H bullish 1.13684-1.13879; 1H bullish 1.13684-1.13879 | 1D bearish POI 1.13845-1.14391: touched at 2026-06-25 17:17:00, waiting for confirmation on 1H; 4H bearish POI 1.14178-1.14618: touched at 2026-06-26 13:56:00, waiting for confirmation on 15m; 1D bearish POI 1.13845-1.14391: touched at 2026-06-25 17:17:00, waiting for confirmation on 1H | - |
| Thu 02 | 50/50 | bearish | bearish | bearish | bearish | bearish (full) | 1.13857 | 4H bullish 1.13684-1.13879; 1H bullish 1.13684-1.13879; 1H bullish 1.13362-1.13710; 4H bearish 1.14178-1.14618 | 1D bearish POI 1.13845-1.14391: touched at 2026-06-25 17:17:00, waiting for confirmation on 1H; 4H bearish POI 1.14178-1.14618: already traded on visit #1 - one trade per visit/touched at 2026-06-26 13:56:00, waiting for confirmation on 15m | 11:15 UTC SHORT entry 1.14073 stop 1.1421 target 1.13245 (5.63R; BS on 15m; zone 4H 1.14178-1.14618) |
| Fri 03 | 50/50 | bearish | bearish | bullish | 50/50 | none | 1.14486 | 4H bearish 1.14178-1.14618; 1H bearish 1.14566-1.14668; 1H bullish 1.13953-1.14385; 4H bearish 1.14778-1.15138 | - | - |
| Mon 06 | 50/50 | bearish | bearish | bullish | bearish | none | 1.14235 | 1H bullish 1.13953-1.14385; 4H bearish 1.14178-1.14618; 1H bullish 1.13904-1.14118; 4H bullish 1.13815-1.14118 | - | - |
| Tue 07 | 50/50 | bearish | 50/50 | bullish | 50/50 | none | 1.14317 | 4H bullish 1.14250-1.14410; 1H bullish 1.14153-1.14410; 4H bearish 1.14178-1.14618; 1H bullish 1.13953-1.14385 | - | - |
| Wed 08 | 50/50 | bearish | 50/50 | bearish | 50/50 | none | 1.14194 | 4H bearish 1.14083-1.14299; 1H bearish 1.14083-1.14299; 1H bullish 1.13953-1.14385; 1H bullish 1.13904-1.14118 | - | - |
| Thu 09 | 50/50 | bearish | 50/50 | bearish | bullish | none | 1.14307 | 4H bearish 1.14178-1.14618; 4H bearish 1.14083-1.14299; 1H bullish 1.13947-1.14141; 1H bullish 1.13904-1.14118 | - | - |
| Fri 10 | 50/50 | bearish | 50/50 | bullish | 50/50 | none | 1.14395 | 4H bearish 1.14178-1.14618; 1H bullish 1.14303-1.14421; 1H bullish 1.13947-1.14141; 1H bullish 1.13904-1.14118 | - | - |
| Mon 13 | 50/50 | bearish | 50/50 | 50/50 | bearish | none | 1.13985 | 4H bullish 1.13815-1.14118; 1H bullish 1.13904-1.14118; 1H bullish 1.13853-1.13904; 4H bullish 1.13684-1.13879 | - | - |
| Tue 14 | 50/50 | bearish | 50/50 | bearish | bearish | none | 1.13916 | 4H bullish 1.13815-1.14118; 4H bullish 1.13684-1.13879; 4H bearish 1.13843-1.14333; 1H bearish 1.13956-1.14333 | - | - |
| Wed 15 | 50/50 | bearish | 50/50 | 50/50 | bullish | none | 1.14402 | 4H bearish 1.14178-1.14618; 1H bullish 1.14038-1.14457; 1H bullish 1.13897-1.14058; 4H bullish 1.13815-1.14118 | - | - |
| Thu 16 | 50/50 | bearish | 50/50 | bullish | bullish | none | 1.14633 | 1H bullish 1.14419-1.14659; 4H bullish 1.14303-1.14596; 4H bearish 1.14778-1.15138; 1H bullish 1.14038-1.14457 | - | - |
| Fri 17 | 50/50 | bearish | 50/50 | 50/50 | bearish | none | 1.14396 | 4H bullish 1.14303-1.14596; 1H bullish 1.14038-1.14457; 1H bullish 1.13897-1.14058; 4H bullish 1.13815-1.14118 | - | - |
| Mon 20 | 50/50 | bearish | 50/50 | bearish | 50/50 | none | 1.14399 | 1H bullish 1.14038-1.14457; 1H bullish 1.13897-1.14058; 4H bullish 1.13815-1.14118; 4H bearish 1.14778-1.15138 | - | - |
| Tue 21 | 50/50 | bearish | 50/50 | bearish | 50/50 | none | 1.14177 | 1H bullish 1.14038-1.14457; 1H bearish 1.14245-1.14300; 4H bearish 1.14234-1.14455; 1H bullish 1.13897-1.14058 | - | - |
| Wed 22 | 50/50 | bearish | 50/50 | bearish | 50/50 | none | 1.14094 | 4H bearish 1.14023-1.14204; 1H bullish 1.13897-1.14058; 4H bullish 1.13815-1.14118; 1H bearish 1.14245-1.14300 | - | - |
| Thu 23 | 50/50 | bearish | 50/50 | bullish | bullish | none | 1.14298 | 4H bearish 1.14234-1.14455; 1H bullish 1.14160-1.14230; 1H bullish 1.14103-1.14159; 1H bullish 1.13897-1.14058 | - | - |
| Fri 24 | 50/50 | bearish | bullish | bearish | bullish | none | 1.13776 | 4H bullish 1.13684-1.13879; 1H bullish 1.13750-1.13816; 1H bearish 1.13955-1.14065; 4H bearish 1.13942-1.14250 | - | - |
| Mon 27 | 50/50 | bearish | 50/50 | bullish | bullish | none | 1.14059 | 4H bearish 1.13942-1.14250; 1H bullish 1.13947-1.14016; 1H bearish 1.14054-1.14250; 4H bullish 1.13875-1.14011 | - | - |
| Tue 28 | 50/50 | bearish | 50/50 | 50/50 | 50/50 | none | 1.13657 | 1H bearish 1.14012-1.14099; 4H bearish 1.13942-1.14250; 1H bearish 1.14054-1.14250; 4H bearish 1.14234-1.14455 | - | - |
| Wed 29 | 50/50 | bearish | bullish | bullish | bullish | bullish (scalp) | 1.13982 | 1H bullish 1.13902-1.13943; 1H bearish 1.14012-1.14099; 4H bearish 1.13942-1.14250; 1H bearish 1.14054-1.14250 | 1H bullish POI 1.13902-1.13943: already traded on visit #1 - one trade per visit/touched at 2026-07-29 07:20:00, waiting for confirmation on 5m; 1H bullish POI 1.13902-1.13943: already traded on visit #1 - one trade per visit | 08:05 UTC LONG entry 1.13938 stop 1.13858 target 1.14181 (2.70R; BS on 5m; zone 1H 1.13902-1.13943) |
| Thu 30 | 50/50 | bearish | bullish | bullish | 50/50 | none | 1.14500 | 4H bullish 1.13766-1.14467; 4H bearish 1.14778-1.15138; 1H bullish 1.13844-1.13969; 1H bullish 1.13657-1.13734 | 4H bullish POI 1.13766-1.14467: R:R 0.17 below minimum 0.5/touched at 2026-07-30 07:06:00, waiting for confirmation on 15m | - |
| Fri 31 | 50/50 | bearish | bullish | bullish | 50/50 | none | 1.15060 | 4H bullish 1.14693-1.15136; 1H bullish 1.14693-1.15024; 4H bearish 1.15084-1.15961; 4H bullish 1.14371-1.14727 | 4H bullish POI 1.13766-1.14467: touched at 2026-07-30 07:06:00, waiting for confirmation on 15m; 4H bullish POI 1.14693-1.15136: touched at 2026-07-31 02:45:00, waiting for confirmation on 15m; 1H bullish POI 1.14693-1.15024: touched at 2026-07-31 11:22:00, waiting for confirmation on 5m | - |

## Zones per day, as mapped (X / B / P)

**Wednesday 01 July** (price 1.14057, bias none)
- 1H bullish 1.13908-1.14151 (X 1.14094, B 1.14069-1.14151, P 1.13908; active; formed 30 Jun 16:00)
- 1H bullish 1.13825-1.13933 (X 1.13933, B 1.13852-1.13927, P 1.13825; tested; formed 29 Jun 07:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13750, P 1.13684; tested; formed 26 Jun 09:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; tested; formed 23 Jun 05:00)
- 1H bullish 1.13362-1.13710 (X 1.13710, B 1.13458-1.13490, P 1.13362; tested; formed 25 Jun 15:00)

**Thursday 02 July** (price 1.13857, bias bearish)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13750, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bullish 1.13362-1.13710 (X 1.13710, B 1.13458-1.13490, P 1.13362; tested; formed 25 Jun 15:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; tested; formed 23 Jun 05:00)
- 1H bearish 1.14566-1.14668 (X 1.14566, B 1.14568-1.14601, P 1.14668; tested; formed 22 Jun 05:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)

**Friday 03 July** (price 1.14486, bias none)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 1H bearish 1.14566-1.14668 (X 1.14566, B 1.14568-1.14601, P 1.14668; tested; formed 22 Jun 05:00)
- 1H bullish 1.13953-1.14385 (X 1.14210, B 1.14146-1.14385, P 1.13953; tested; formed 02 Jul 14:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 1H bearish 1.14778-1.15138 (X 1.14778, B 1.14858-1.15064, P 1.15138; tested; formed 18 Jun 10:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)

**Monday 06 July** (price 1.14235, bias none)
- 1H bullish 1.13953-1.14385 (X 1.14210, B 1.14146-1.14385, P 1.13953; active; formed 02 Jul 14:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; fresh; formed 02 Jul 13:00)
- 1H bullish 1.13853-1.13904 (X 1.13883, B 1.13886-1.13904, P 1.13853; fresh; formed 02 Jul 08:00)
- 1H bearish 1.14566-1.14668 (X 1.14566, B 1.14568-1.14601, P 1.14668; tested; formed 22 Jun 05:00)

**Tuesday 07 July** (price 1.14317, bias none)
- 4H bullish 1.14250-1.14410 (X 1.14410, B 1.14260-1.14395, P 1.14250; active; formed 06 Jul 21:00)
- 1H bullish 1.14153-1.14410 (X 1.14410, B 1.14200-1.14250, P 1.14153; active; formed 06 Jul 19:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 1H bullish 1.13953-1.14385 (X 1.14210, B 1.14146-1.14385, P 1.13953; active; formed 02 Jul 14:00)
- 1H bearish 1.14566-1.14668 (X 1.14566, B 1.14568-1.14601, P 1.14668; tested; formed 22 Jun 05:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)

**Wednesday 08 July** (price 1.14194, bias none)
- 4H bearish 1.14083-1.14299 (X 1.14083, B 1.14171-1.14221, P 1.14299; active; formed 07 Jul 21:00)
- 1H bearish 1.14083-1.14299 (X 1.14083, B 1.14193-1.14222, P 1.14299; active; formed 07 Jul 22:00)
- 1H bullish 1.13953-1.14385 (X 1.14210, B 1.14146-1.14385, P 1.13953; active; formed 02 Jul 14:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)

**Thursday 09 July** (price 1.14307, bias none)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 4H bearish 1.14083-1.14299 (X 1.14083, B 1.14171-1.14221, P 1.14299; tested; formed 07 Jul 21:00)
- 1H bullish 1.13947-1.14141 (X 1.14137, B 1.14119-1.14141, P 1.13947; tested; formed 08 Jul 18:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 1H bullish 1.13853-1.13904 (X 1.13883, B 1.13886-1.13904, P 1.13853; fresh; formed 02 Jul 08:00)

**Friday 10 July** (price 1.14395, bias none)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 1H bullish 1.14303-1.14421 (X 1.14421, B 1.14338-1.14379, P 1.14303; active; formed 10 Jul 02:00)
- 1H bullish 1.13947-1.14141 (X 1.14137, B 1.14119-1.14141, P 1.13947; tested; formed 08 Jul 18:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; tested; formed 02 Jul 09:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 1H bullish 1.13853-1.13904 (X 1.13883, B 1.13886-1.13904, P 1.13853; fresh; formed 02 Jul 08:00)

**Monday 13 July** (price 1.13985, bias none)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 1H bullish 1.13904-1.14118 (X 1.14118, B 1.14045-1.14067, P 1.13904; active; formed 02 Jul 09:00)
- 1H bullish 1.13853-1.13904 (X 1.13883, B 1.13886-1.13904, P 1.13853; tested; formed 02 Jul 08:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13750, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bearish 1.14118-1.14310 (X 1.14118, B 1.14181-1.14294, P 1.14310; fresh; formed 12 Jul 22:00)

**Tuesday 14 July** (price 1.13916, bias none)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; active; formed 02 Jul 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 4H bearish 1.13843-1.14333 (X 1.13843, B 1.14025-1.14239, P 1.14333; active; formed 13 Jul 17:00)
- 1H bearish 1.13956-1.14333 (X 1.13956, B 1.14160-1.14204, P 1.14333; tested; formed 13 Jul 17:00)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; tested; formed 23 Jun 05:00)
- 1H bearish 1.14355-1.14491 (X 1.14355, B 1.14444-1.14473, P 1.14491; tested; formed 10 Jul 09:00)

**Wednesday 15 July** (price 1.14402, bias none)
- 4H bearish 1.14178-1.14618 (X 1.14178, B 1.14333-1.14414, P 1.14618; active; formed 23 Jun 05:00)
- 1H bullish 1.14038-1.14457 (X 1.14457, B 1.14091-1.14414, P 1.14038; active; formed 14 Jul 14:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; fresh; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)

**Thursday 16 July** (price 1.14633, bias none)
- 1H bullish 1.14419-1.14659 (X 1.14437, B 1.14422-1.14659, P 1.14419; tested; formed 15 Jul 19:00)
- 4H bullish 1.14303-1.14596 (X 1.14437, B 1.14414-1.14596, P 1.14303; fresh; formed 15 Jul 21:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 1H bullish 1.14038-1.14457 (X 1.14457, B 1.14091-1.14414, P 1.14038; tested; formed 14 Jul 14:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; fresh; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)

**Friday 17 July** (price 1.14396, bias none)
- 4H bullish 1.14303-1.14596 (X 1.14437, B 1.14414-1.14596, P 1.14303; active; formed 15 Jul 21:00)
- 1H bullish 1.14038-1.14457 (X 1.14457, B 1.14091-1.14414, P 1.14038; tested; formed 14 Jul 14:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; fresh; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)

**Monday 20 July** (price 1.14399, bias none)
- 1H bullish 1.14038-1.14457 (X 1.14457, B 1.14091-1.14414, P 1.14038; active; formed 14 Jul 14:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; fresh; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; tested; formed 17 Jun 21:00)

**Tuesday 21 July** (price 1.14177, bias none)
- 1H bullish 1.14038-1.14457 (X 1.14457, B 1.14091-1.14414, P 1.14038; active; formed 14 Jul 14:00)
- 1H bearish 1.14245-1.14300 (X 1.14272, B 1.14245-1.14278, P 1.14300; fresh; formed 20 Jul 14:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; fresh; formed 20 Jul 13:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; tested; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)

**Wednesday 22 July** (price 1.14094, bias none)
- 4H bearish 1.14023-1.14204 (X 1.14023, B 1.14107-1.14163, P 1.14204; active; formed 21 Jul 17:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; tested; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; active; formed 02 Jul 13:00)
- 1H bearish 1.14245-1.14300 (X 1.14272, B 1.14245-1.14278, P 1.14300; tested; formed 20 Jul 14:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)

**Thursday 23 July** (price 1.14298, bias none)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)
- 1H bullish 1.14160-1.14230 (X 1.14215, B 1.14203-1.14230, P 1.14160; fresh; formed 23 Jul 04:00)
- 1H bullish 1.14103-1.14159 (X 1.14126, B 1.14117-1.14159, P 1.14103; fresh; formed 23 Jul 02:00)
- 1H bullish 1.13897-1.14058 (X 1.14058, B 1.14016-1.14038, P 1.13897; tested; formed 14 Jul 13:00)
- 4H bullish 1.13815-1.14118 (X 1.14118, B 1.13883-1.14004, P 1.13815; tested; formed 02 Jul 13:00)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)

**Friday 24 July** (price 1.13776, bias none)
- 4H bullish 1.13684-1.13879 (X 1.13879, B 1.13715-1.13829, P 1.13684; tested; formed 26 Jun 09:00)
- 1H bullish 1.13750-1.13816 (X 1.13807, B 1.13798-1.13816, P 1.13750; tested; formed 24 Jul 02:00)
- 1H bearish 1.13955-1.14065 (X 1.14002, B 1.13955-1.14030, P 1.14065; fresh; formed 23 Jul 13:00)
- 4H bearish 1.13942-1.14250 (X 1.13942, B 1.13955-1.14195, P 1.14250; fresh; formed 23 Jul 13:00)
- 1H bearish 1.14054-1.14250 (X 1.14054, B 1.14151-1.14195, P 1.14250; tested; formed 23 Jul 11:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)

**Monday 27 July** (price 1.14059, bias none)
- 4H bearish 1.13942-1.14250 (X 1.13942, B 1.13955-1.14195, P 1.14250; active; formed 23 Jul 13:00)
- 1H bullish 1.13947-1.14016 (X 1.14011, B 1.13951-1.14016, P 1.13947; tested; formed 27 Jul 02:00)
- 1H bearish 1.14054-1.14250 (X 1.14054, B 1.14151-1.14195, P 1.14250; active; formed 23 Jul 11:00)
- 4H bullish 1.13875-1.14011 (X 1.14011, B 1.13733-1.13947, P 1.13875; fresh; formed 27 Jul 01:00)
- 1H bullish 1.13666-1.13928 (X 1.13928, B 1.13721-1.13875, P 1.13666; fresh; formed 27 Jul 00:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)

**Tuesday 28 July** (price 1.13657, bias none)
- 1H bearish 1.14012-1.14099 (X 1.14012, B 1.14031-1.14055, P 1.14099; tested; formed 27 Jul 09:00)
- 4H bearish 1.13942-1.14250 (X 1.13942, B 1.13955-1.14195, P 1.14250; tested; formed 23 Jul 13:00)
- 1H bearish 1.14054-1.14250 (X 1.14054, B 1.14151-1.14195, P 1.14250; tested; formed 23 Jul 11:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)

**Wednesday 29 July** (price 1.13982, bias bullish)
- 1H bullish 1.13902-1.13943 (X 1.13923, B 1.13924-1.13943, P 1.13902; active; formed 29 Jul 04:00)
- 1H bearish 1.14012-1.14099 (X 1.14012, B 1.14031-1.14055, P 1.14099; tested; formed 27 Jul 09:00)
- 4H bearish 1.13942-1.14250 (X 1.13942, B 1.13955-1.14195, P 1.14250; active; formed 23 Jul 13:00)
- 1H bearish 1.14054-1.14250 (X 1.14054, B 1.14151-1.14195, P 1.14250; tested; formed 23 Jul 11:00)
- 1H bullish 1.13657-1.13734 (X 1.13734, B 1.13684-1.13712, P 1.13657; fresh; formed 28 Jul 15:00)
- 4H bearish 1.14234-1.14455 (X 1.14234, B 1.14300-1.14339, P 1.14455; tested; formed 20 Jul 13:00)

**Thursday 30 July** (price 1.14500, bias none)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; active; formed 29 Jul 21:00)
- 4H bearish 1.14778-1.15138 (X 1.14778, B 1.14875-1.15064, P 1.15138; tested; formed 18 Jun 13:00)
- 1H bullish 1.13844-1.13969 (X 1.13969, B 1.13859-1.13894, P 1.13844; fresh; formed 29 Jul 19:00)
- 1H bullish 1.13657-1.13734 (X 1.13734, B 1.13684-1.13712, P 1.13657; fresh; formed 28 Jul 15:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; tested; formed 17 Jun 21:00)

**Friday 31 July** (price 1.15060, bias none)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)
- 1H bullish 1.14693-1.15024 (X 1.14841, B 1.14832-1.15024, P 1.14693; tested; formed 30 Jul 15:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 4H bullish 1.14371-1.14727 (X 1.14727, B 1.14566-1.14693, P 1.14371; fresh; formed 30 Jul 13:00)
- 1H bullish 1.14479-1.14612 (X 1.14566, B 1.14555-1.14612, P 1.14479; fresh; formed 30 Jul 11:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; tested; formed 05 Jun 17:00)
