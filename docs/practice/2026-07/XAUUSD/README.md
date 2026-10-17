# XAUUSD, July 2026: the month the way we read it, for review against Dorus

The live profile `config/dorus_live.yaml` (reading F: 5m shifts for 1H zones, 15m for 4H, 1H for daily; the sweep-extreme stop with an 8-pip minimum; the target on the previous low/high; one trade per zone per visit; entries at most half the zone deep; 1D/4H/1H zones only; sessions, news, FTMO margins). Review question per chart: would Dorus take this, and if not, what is different?

## The trades the code took (1 in July; 0 won, -1.00R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P2 | Fri 03 Jul 07:45 | LONG | 4H 3969.03-4063.20 (15m shift) | 4171.02 | 4061.01 | 4382.12 | 1.92 | 4H previous high 4382.12500 | stop -1.00R | [XAUUSD_002_20260703_0745_15m.png](charts/XAUUSD_002_20260703_0745_15m.png) |

Each chart shows the candles of the entry timeframe up to the entry, the zone with X / B / P, the stop and the target; the title gives the outcome. The ledger (`ledger_v5.csv`) carries every field, including the warm-up weeks before the month (1 trades, +1.58R).


Config `config/dorus_live.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Wed 01 | bearish | bearish | 50/50 | bearish | 50/50 | none | 3973.82 | 1H bullish 3967.95-4022.14 | - | - |
| Thu 02 | bearish | bearish | 50/50 | bullish | bullish | none | 4065.86 | - | - | - |
| Fri 03 | bearish | bearish | bullish | bullish | bullish | bullish (scalp) | 4171.02 | 4H bearish 4146.80-4198.44; 1H bearish 4163.30-4198.44; 1H bullish 4122.62-4146.19 | 4H bullish POI 3969.03500-4063.20500: already traded on visit #1 - one trade per visit/touched at 2026-07-02 00:20:00, waiting for confirmation on 15m | 07:45 UTC LONG entry 4170.82 stop 4061.01 target 4382.12 (1.92R; BS on 15m; zone 4H 3969.03-4063.20) |
| Mon 06 | bearish | bearish | bullish | 50/50 | 50/50 | none | 4147.78 | 4H bullish 4122.62-4160.23; 1H bullish 4122.62-4146.19; 4H bearish 4146.80-4198.44; 1H bearish 4163.30-4198.44 | - | - |
| Tue 07 | bearish | bearish | bullish | bullish | bearish | none | 4123.74 | 1H bullish 4122.62-4146.19; 4H bullish 4122.62-4160.23; 1H bearish 4136.31-4162.45; 1H bullish 4061.01-4109.22 | - | - |
| Wed 08 | bearish | bearish | bullish | bearish | bullish | none | 4127.53 | 4H bearish 4115.60-4148.09; 1H bearish 4127.48-4145.03; 4H bearish 4128.27-4162.45 | - | - |
| Thu 09 | bearish | bearish | bullish | bearish | 50/50 | none | 4081.72 | 4H bullish 4030.53-4115.48; 1H bearish 4060.95-4121.06; 4H bearish 4086.24-4121.06 | - | - |
| Fri 10 | bearish | bearish | bullish | 50/50 | bullish | none | 4116.59 | 4H bearish 4115.60-4148.09; 1H bearish 4127.48-4145.03; 4H bearish 4128.27-4162.45; 1H bullish 4063.41-4089.78 | - | - |
| Mon 13 | bearish | bearish | bullish | bearish | bearish | none | 4053.36 | 1H bearish 4060.20-4069.07; 4H bullish 4030.53-4115.48; 1H bullish 3981.11-4063.20; 4H bearish 4072.59-4103.27 | - | - |
| Tue 14 | bearish | bearish | 50/50 | bearish | bullish | none | 4031.14 | 1H bearish 4020.26-4046.80; 1H bullish 3981.11-4063.20; 4H bearish 4017.72-4067.36; 4H bullish 3969.03-4063.20 | - | - |
| Wed 15 | bearish | bearish | 50/50 | 50/50 | bearish | none | 4034.72 | 4H bearish 4017.72-4067.36; 1H bullish 4022.93-4070.72; 1H bullish 3981.11-4063.20; 1H bearish 4041.95-4061.88 | - | - |
| Thu 16 | bearish | bearish | 50/50 | bearish | 50/50 | none | 4026.97 | 1H bullish 3981.11-4063.20; 4H bullish 3969.03-4063.20; 4H bearish 4017.72-4067.36; 1H bullish 4022.93-4070.72 | - | - |
| Fri 17 | bearish | bearish | 50/50 | bearish | 50/50 | none | 3984.64 | 4H bullish 3969.03-4063.20 | - | - |
| Mon 20 | bearish | bearish | 50/50 | 50/50 | bullish | none | 4008.47 | 4H bullish 3969.03-4063.20; 1H bearish 4008.32-4043.07; 4H bearish 4017.16-4061.07; 4H bearish 4017.72-4067.36 | - | - |
| Tue 21 | bearish | bearish | 50/50 | bullish | 50/50 | none | 4061.11 | 4H bearish 4017.72-4067.36; 4H bearish 4017.16-4061.07; 4H bearish 4072.59-4103.27; 1H bearish 4072.59-4103.27 | - | - |
| Wed 22 | bearish | bearish | 50/50 | bullish | 50/50 | none | 4130.73 | 4H bearish 4115.60-4148.09; 1H bearish 4127.48-4145.03; 4H bearish 4128.27-4162.45; 1H bullish 4096.36-4118.53 | - | - |
| Thu 23 | bearish | bearish | 50/50 | bullish | bullish | none | 4123.73 | 4H bullish 4107.27-4141.47; 1H bullish 4112.61-4143.85; 1H bullish 4096.36-4118.53; 4H bearish 4128.27-4162.45 | - | - |
| Fri 24 | bearish | bearish | 50/50 | bearish | bearish | none | 4022.72 | 4H bullish 4003.49-4043.36; 4H bullish 3969.03-4063.20; 1H bullish 4003.49-4017.95; 1H bearish 4033.30-4048.30 | - | - |
| Mon 27 | bearish | bearish | 50/50 | bullish | bullish | none | 4092.97 | 4H bullish 4080.62-4084.36; 1H bearish 4097.53-4119.35; 4H bearish 4099.31-4130.40; 1H bullish 4049.12-4082.09 | - | - |
| Tue 28 | bearish | bearish | 50/50 | bearish | bearish | none | 4044.97 | 1H bearish 4048.84-4060.07; 4H bullish 4003.49-4043.36; 1H bearish 4060.07-4073.86; 4H bullish 3969.03-4063.20 | - | - |
| Wed 29 | bearish | bearish | 50/50 | 50/50 | 50/50 | none | 4032.74 | 1H bearish 4021.51-4041.49; 4H bullish 4003.49-4043.36; 4H bullish 3969.03-4063.20; 1H bearish 4048.84-4060.07 | - | - |
| Thu 30 | bearish | bearish | 50/50 | bullish | 50/50 | none | 4033.47 | 4H bullish 4007.47-4047.64; 1H bullish 4007.47-4047.64; 4H bullish 4003.49-4043.36; 4H bullish 3969.03-4063.20 | - | - |
| Fri 31 | bearish | bearish | 50/50 | 50/50 | 50/50 | none | 4073.97 | 1H bearish 4097.53-4119.35 | - | - |

## Zones per day, as mapped (X / B / P)

**Wednesday 01 July** (price 3973.82, bias none)
- 1H bullish 3967.95-4022.14 (X 4022.14, B 3970.89-3974.86, P 3967.95; active; formed 30 Jun 07:00)

**Thursday 02 July** (price 4065.86, bias none)
- no 4H or 1H zone within reach

**Friday 03 July** (price 4171.02, bias bullish)
- 4H bearish 4146.80-4198.44 (X 4169.48, B 4146.80-4186.51, P 4198.44; active; formed 23 Jun 05:00)
- 1H bearish 4163.30-4198.44 (X 4169.48, B 4163.30-4178.10, P 4198.44; active; formed 23 Jun 03:00)
- 1H bullish 4122.62-4146.19 (X 4144.80, B 4131.90-4146.19, P 4122.62; fresh; formed 03 Jul 02:00)

**Monday 06 July** (price 4147.78, bias none)
- 4H bullish 4122.62-4160.23 (X 4143.72, B 4131.90-4160.23, P 4122.62; tested; formed 03 Jul 05:00)
- 1H bullish 4122.62-4146.19 (X 4144.80, B 4131.90-4146.19, P 4122.62; tested; formed 03 Jul 02:00)
- 4H bearish 4146.80-4198.44 (X 4169.48, B 4146.80-4186.51, P 4198.44; active; formed 23 Jun 05:00)
- 1H bearish 4163.30-4198.44 (X 4169.48, B 4163.30-4178.10, P 4198.44; tested; formed 23 Jun 03:00)

**Tuesday 07 July** (price 4123.74, bias none)
- 1H bullish 4122.62-4146.19 (X 4144.80, B 4131.90-4146.19, P 4122.62; active; formed 03 Jul 02:00)
- 4H bullish 4122.62-4160.23 (X 4143.72, B 4131.90-4160.23, P 4122.62; active; formed 03 Jul 05:00)
- 1H bearish 4136.31-4162.45 (X 4136.31, B 4147.74-4156.60, P 4162.45; tested; formed 07 Jul 04:00)
- 1H bullish 4061.01-4109.22 (X 4079.70, B 4072.05-4109.22, P 4061.01; tested; formed 02 Jul 14:00)

**Wednesday 08 July** (price 4127.53, bias none)
- 4H bearish 4115.60-4148.09 (X 4116.52, B 4115.60-4135.55, P 4148.09; active; formed 07 Jul 21:00)
- 1H bearish 4127.48-4145.03 (X 4135.55, B 4127.48-4140.23, P 4145.03; tested; formed 07 Jul 20:00)
- 4H bearish 4128.27-4162.45 (X 4128.27, B 4140.99-4156.60, P 4162.45; tested; formed 07 Jul 05:00)

**Thursday 09 July** (price 4081.72, bias none)
- 4H bullish 4030.53-4115.48 (X 4115.48, B 4044.22-4052.95, P 4030.53; active; formed 02 Jul 13:00)
- 1H bearish 4060.95-4121.06 (X 4091.84, B 4060.95-4114.61, P 4121.06; active; formed 08 Jul 10:00)
- 4H bearish 4086.24-4121.06 (X 4091.84, B 4086.24-4114.61, P 4121.06; active; formed 08 Jul 13:00)

**Friday 10 July** (price 4116.59, bias none)
- 4H bearish 4115.60-4148.09 (X 4116.52, B 4115.60-4135.55, P 4148.09; tested; formed 07 Jul 21:00)
- 1H bearish 4127.48-4145.03 (X 4135.55, B 4127.48-4140.23, P 4145.03; tested; formed 07 Jul 20:00)
- 4H bearish 4128.27-4162.45 (X 4128.27, B 4140.99-4156.60, P 4162.45; tested; formed 07 Jul 05:00)
- 1H bullish 4063.41-4089.78 (X 4089.78, B 4064.36-4081.14, P 4063.41; fresh; formed 09 Jul 07:00)

**Monday 13 July** (price 4053.36, bias none)
- 1H bearish 4060.20-4069.07 (X 4060.70, B 4060.20-4064.12, P 4069.07; tested; formed 13 Jul 05:00)
- 4H bullish 4030.53-4115.48 (X 4115.48, B 4044.22-4052.95, P 4030.53; active; formed 02 Jul 13:00)
- 1H bullish 3981.11-4063.20 (X 4063.20, B 3985.78-3997.47, P 3981.11; active; formed 01 Jul 14:00)
- 4H bearish 4072.59-4103.27 (X 4072.59, B 4090.80-4107.94, P 4103.27; fresh; formed 13 Jul 01:00)
- 1H bearish 4072.59-4103.27 (X 4072.59, B 4084.64-4107.94, P 4103.27; tested; formed 13 Jul 02:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)

**Tuesday 14 July** (price 4031.14, bias none)
- 1H bearish 4020.26-4046.80 (X 4021.53, B 4020.26-4041.70, P 4046.80; active; formed 13 Jul 16:00)
- 1H bullish 3981.11-4063.20 (X 4063.20, B 3985.78-3997.47, P 3981.11; active; formed 01 Jul 14:00)
- 4H bearish 4017.72-4067.36 (X 4021.53, B 4017.72-4046.28, P 4067.36; active; formed 13 Jul 17:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bearish 4046.28-4067.36 (X 4046.28, B 4046.80-4053.36, P 4067.36; fresh; formed 13 Jul 15:00)
- 1H bullish 3967.95-4022.14 (X 4022.14, B 3970.89-3974.86, P 3967.95; tested; formed 30 Jun 07:00)

**Wednesday 15 July** (price 4034.72, bias none)
- 4H bearish 4017.72-4067.36 (X 4021.53, B 4017.72-4046.28, P 4067.36; active; formed 13 Jul 17:00)
- 1H bullish 4022.93-4070.72 (X 4034.01, B 4031.55-4070.72, P 4022.93; active; formed 14 Jul 14:00)
- 1H bullish 3981.11-4063.20 (X 4063.20, B 3985.78-3997.47, P 3981.11; active; formed 01 Jul 14:00)
- 1H bearish 4041.95-4061.88 (X 4042.61, B 4041.95-4048.59, P 4061.88; fresh; formed 15 Jul 03:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bullish 3967.95-4022.14 (X 4022.14, B 3970.89-3974.86, P 3967.95; tested; formed 30 Jun 07:00)

**Thursday 16 July** (price 4026.97, bias none)
- 1H bullish 3981.11-4063.20 (X 4063.20, B 3985.78-3997.47, P 3981.11; active; formed 01 Jul 14:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 4H bearish 4017.72-4067.36 (X 4021.53, B 4017.72-4046.28, P 4067.36; active; formed 13 Jul 17:00)
- 1H bullish 4022.93-4070.72 (X 4034.01, B 4031.55-4070.72, P 4022.93; active; formed 14 Jul 14:00)
- 1H bullish 3967.95-4022.14 (X 4022.14, B 3970.89-3974.86, P 3967.95; tested; formed 30 Jun 07:00)

**Friday 17 July** (price 3984.64, bias none)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)

**Monday 20 July** (price 4008.47, bias none)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bearish 4008.32-4043.07 (X 4022.74, B 4008.32-4020.99, P 4043.07; tested; formed 16 Jul 14:00)
- 4H bearish 4017.16-4061.07 (X 4017.16, B 4037.76-4054.86, P 4061.07; active; formed 16 Jul 13:00)
- 4H bearish 4017.72-4067.36 (X 4021.53, B 4017.72-4046.28, P 4067.36; tested; formed 13 Jul 17:00)

**Tuesday 21 July** (price 4061.11, bias none)
- 4H bearish 4017.72-4067.36 (X 4021.53, B 4017.72-4046.28, P 4067.36; tested; formed 13 Jul 17:00)
- 4H bearish 4017.16-4061.07 (X 4017.16, B 4037.76-4054.86, P 4061.07; tested; formed 16 Jul 13:00)
- 4H bearish 4072.59-4103.27 (X 4072.59, B 4090.80-4107.94, P 4103.27; tested; formed 13 Jul 01:00)
- 1H bearish 4072.59-4103.27 (X 4072.59, B 4084.64-4107.94, P 4103.27; active; formed 13 Jul 02:00)

**Wednesday 22 July** (price 4130.73, bias none)
- 4H bearish 4115.60-4148.09 (X 4116.52, B 4115.60-4135.55, P 4148.09; tested; formed 07 Jul 21:00)
- 1H bearish 4127.48-4145.03 (X 4135.55, B 4127.48-4140.23, P 4145.03; tested; formed 07 Jul 20:00)
- 4H bearish 4128.27-4162.45 (X 4128.27, B 4140.99-4156.60, P 4162.45; tested; formed 07 Jul 05:00)
- 1H bullish 4096.36-4118.53 (X 4100.78, B 4102.38-4118.53, P 4096.36; active; formed 22 Jul 03:00)

**Thursday 23 July** (price 4123.73, bias none)
- 4H bullish 4107.27-4141.47 (X 4141.47, B 4123.01-4128.73, P 4107.27; tested; formed 22 Jul 17:00)
- 1H bullish 4112.61-4143.85 (X 4135.06, B 4134.19-4143.85, P 4112.61; active; formed 22 Jul 15:00)
- 1H bullish 4096.36-4118.53 (X 4100.78, B 4102.38-4118.53, P 4096.36; tested; formed 22 Jul 03:00)
- 4H bearish 4128.27-4162.45 (X 4128.27, B 4140.99-4156.60, P 4162.45; tested; formed 07 Jul 05:00)
- 4H bullish 4076.32-4109.02 (X 4100.78, B 4086.26-4109.02, P 4076.32; active; formed 22 Jul 05:00)
- 1H bullish 4076.32-4096.36 (X 4086.78, B 4082.59-4096.36, P 4076.32; fresh; formed 22 Jul 02:00)

**Friday 24 July** (price 4022.72, bias none)
- 4H bullish 4003.49-4043.36 (X 4040.43, B 4010.49-4043.36, P 4003.49; tested; formed 21 Jul 05:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bullish 4003.49-4017.95 (X 4017.86, B 4010.28-4017.95, P 4003.49; fresh; formed 21 Jul 02:00)
- 1H bearish 4033.30-4048.30 (X 4039.68, B 4033.30-4039.47, P 4048.30; active; formed 24 Jul 04:00)
- 4H bearish 4039.68-4085.80 (X 4039.68, B 4054.47-4072.76, P 4085.80; active; formed 24 Jul 01:00)

**Monday 27 July** (price 4092.97, bias none)
- 4H bullish 4080.62-4084.36 (X 4081.89, B 4055.80-4084.36, P 4080.62; fresh; formed 27 Jul 01:00)
- 1H bearish 4097.53-4119.35 (X 4111.81, B 4097.53-4116.53, P 4119.35; tested; formed 23 Jul 09:00)
- 4H bearish 4099.31-4130.40 (X 4107.27, B 4099.31-4111.81, P 4130.40; tested; formed 23 Jul 09:00)
- 1H bullish 4049.12-4082.09 (X 4081.89, B 4057.74-4082.09, P 4049.12; tested; formed 26 Jul 23:00)

**Tuesday 28 July** (price 4044.97, bias none)
- 1H bearish 4048.84-4060.07 (X 4048.99, B 4048.84-4057.20, P 4060.07; active; formed 28 Jul 03:00)
- 4H bullish 4003.49-4043.36 (X 4040.43, B 4010.49-4043.36, P 4003.49; tested; formed 21 Jul 05:00)
- 1H bearish 4060.07-4073.86 (X 4070.34, B 4060.07-4069.59, P 4073.86; fresh; formed 28 Jul 02:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bullish 4003.49-4017.95 (X 4017.86, B 4010.28-4017.95, P 4003.49; fresh; formed 21 Jul 02:00)

**Wednesday 29 July** (price 4032.74, bias none)
- 1H bearish 4021.51-4041.49 (X 4021.51, B 4030.18-4036.41, P 4041.49; active; formed 28 Jul 23:00)
- 4H bullish 4003.49-4043.36 (X 4040.43, B 4010.49-4043.36, P 4003.49; active; formed 21 Jul 05:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bearish 4048.84-4060.07 (X 4048.99, B 4048.84-4057.20, P 4060.07; tested; formed 28 Jul 03:00)
- 1H bullish 4003.49-4017.95 (X 4017.86, B 4010.28-4017.95, P 4003.49; tested; formed 21 Jul 02:00)
- 4H bearish 4052.32-4073.86 (X 4065.07, B 4052.32-4069.59, P 4073.86; tested; formed 28 Jul 05:00)

**Thursday 30 July** (price 4033.47, bias none)
- 4H bullish 4007.47-4047.64 (X 4047.64, B 4033.30-4043.62, P 4007.47; active; formed 29 Jul 21:00)
- 1H bullish 4007.47-4047.64 (X 4047.64, B 4013.55-4026.99, P 4007.47; active; formed 29 Jul 19:00)
- 4H bullish 4003.49-4043.36 (X 4040.43, B 4010.49-4043.36, P 4003.49; active; formed 21 Jul 05:00)
- 4H bullish 3969.03-4063.20 (X 4063.20, B 3982.47-4012.55, P 3969.03; active; formed 01 Jul 13:00)
- 1H bullish 4003.49-4017.95 (X 4017.86, B 4010.28-4017.95, P 4003.49; tested; formed 21 Jul 02:00)

**Friday 31 July** (price 4073.97, bias none)
- 1H bearish 4097.53-4119.35 (X 4111.81, B 4097.53-4116.53, P 4119.35; tested; formed 23 Jul 09:00)
