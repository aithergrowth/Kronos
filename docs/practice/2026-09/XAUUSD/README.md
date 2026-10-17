# XAUUSD, September 2026: the month the way we read it, for review against Dorus

Same reading and layout as `../EURUSD/README.md` (reading E of the source-trade suite). Review question per chart: would
Dorus take this, and if not, what is different?

## The trades the code took (6 in September; 1 won, -4.36R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P3 | Mon 14 Sep 13:25 | SHORT | 1H 4291.95-4311.53 (5m shift) | 4285.71 | 4297.64 | 4278.10 | 0.63 | 1H previous low 4278.10500 | take_profit +0.64R | [XAUUSD_003_20260914_1325_5m.png](charts/XAUUSD_003_20260914_1325_5m.png) |
| P4 | Tue 15 Sep 13:20 | SHORT | 1H 4282.09-4307.42 (5m shift) | 4274.19 | 4286.55 | 4253.44 | 1.67 | 1H previous low 4253.43800 | stop -1.00R | [XAUUSD_004_20260915_1320_5m.png](charts/XAUUSD_004_20260915_1320_5m.png) |
| P5 | Thu 17 Sep 07:40 | SHORT | 1H 4286.95-4355.85 (5m shift) | 4306.10 | 4314.99 | 4234.66 | 7.95 | 1H previous low 4234.66500 | stop -1.00R | [XAUUSD_005_20260917_0740_5m.png](charts/XAUUSD_005_20260917_0740_5m.png) |
| P6 | Tue 22 Sep 07:00 | SHORT | 1H 4339.77-4369.51 (5m shift) | 4323.39 | 4347.09 | 4234.66 | 3.73 | 1H previous low 4234.66500 | stop -1.00R | [XAUUSD_006_20260922_0700_5m.png](charts/XAUUSD_006_20260922_0700_5m.png) |
| P7 | Wed 23 Sep 11:50 | SHORT | 1H 4314.73-4345.65 (5m shift) | 4313.18 | 4318.84 | 4291.24 | 3.81 | 1H previous low 4291.24500 | stop -1.00R | [XAUUSD_007_20260923_1150_5m.png](charts/XAUUSD_007_20260923_1150_5m.png) |
| P8 | Thu 24 Sep 14:35 | SHORT | 1H 4267.15-4285.40 (5m shift) | 4272.69 | 4284.80 | 4243.93 | 2.36 | 1H previous low 4243.92500 | stop -1.00R | [XAUUSD_008_20260924_1435_5m.png](charts/XAUUSD_008_20260924_1435_5m.png) |

Reading before the review: five of the six are 5m shifts out of 1H zones in a market whose 1D and 4H read 50/50 or bullish
most of the month (the bias allowed scalps only on a handful of days); the previous-low target with a 72-candle window
reaches 3.7R-8R on gold, which the ledger's two far targets (P5, P6) show is not his distance. The ledger (`ledger_v5.csv`)
carries every field, including the August warm-up weeks (two trades).


Config `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/eval_2026_v5_prev_extreme.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Tue 01 | bearish | 50/50 | 50/50 | bearish | bearish | none | 4439.82 | 1H bearish 4441.38-4462.95; 4H bullish 4361.81-4471.76 | - | - |
| Wed 02 | bearish | 50/50 | 50/50 | bearish | bearish | none | 4319.73 | - | - | - |
| Thu 03 | bearish | 50/50 | 50/50 | bullish | bullish | none | 4430.95 | 4H bearish 4396.15-4445.82; 1H bearish 4441.38-4462.95; 1H bullish 4386.86-4406.49 | - | - |
| Fri 04 | bearish | 50/50 | 50/50 | bullish | 50/50 | none | 4471.94 | 4H bullish 4437.53-4472.40; 4H bearish 4450.36-4529.26; 1H bullish 4437.53-4456.35; 1H bearish 4486.56-4529.26 | - | - |
| Mon 07 | bearish | 50/50 | 50/50 | 50/50 | bearish | none | 4393.69 | 1H bullish 4386.86-4406.49; 1H bullish 4371.60-4387.15; 1H bearish 4411.95-4429.23; 4H bullish 4327.15-4397.48 | - | - |
| Tue 08 | bearish | 50/50 | 50/50 | 50/50 | 50/50 | none | 4419.02 | 1H bearish 4434.48-4475.62; 1H bullish 4371.60-4387.15 | - | - |
| Wed 09 | bearish | 50/50 | 50/50 | bearish | bullish | none | 4398.49 | 4H bearish 4380.94-4442.70; 1H bearish 4401.40-4437.41; 4H bullish 4327.15-4397.48 | - | - |
| Thu 10 | bearish | 50/50 | 50/50 | 50/50 | bullish | none | 4430.82 | 1H bearish 4401.40-4437.41; 4H bearish 4380.94-4442.70; 1H bearish 4434.48-4475.62; 1H bullish 4400.81-4407.82 | - | - |
| Fri 11 | bearish | 50/50 | bearish | bearish | bullish | bearish (full) | 4345.81 | 1H bearish 4323.91-4356.02; 4H bearish 4340.97-4412.68 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4380.93500-4442.70500: touched at 2026-09-09 03:52:00, waiting for confirmation on 15m; 4H bearish POI 4340.96500-4412.67500: touched at 2026-09-11 06:43:00, waiting for confirmation on 15m | - |
| Mon 14 | bearish | 50/50 | bearish | 50/50 | 50/50 | none | 4337.15 | 1H bullish 4328.05-4345.69; 1H bullish 4291.95-4380.27; 4H bearish 4340.97-4412.68 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4380.93500-4442.70500: touched at 2026-09-09 03:52:00, waiting for confirmation on 15m; 4H bearish POI 4340.96500-4412.67500: touched at 2026-09-11 06:43:00, waiting for confirmation on 15m | 13:25 UTC SHORT entry 4285.71 stop 4297.64 target 4278.1 (0.63R; BS on 5m; zone 1H 4291.95-4311.53) |
| Tue 15 | bearish | 50/50 | bearish | bearish | bullish | bearish (full) | 4290.77 | 4H bullish 4229.39-4303.74; 4H bearish 4291.95-4338.52 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: touched at 2026-09-11 06:43:00, waiting for confirmation on 15m; 4H bearish POI 4291.95100-4338.52500: touched at 2026-09-14 13:08:00, waiting for confirmation on 15m | 13:20 UTC SHORT entry 4274.19 stop 4286.55 target 4253.44 (1.67R; BS on 5m; zone 1H 4282.09-4307.42) |
| Wed 16 | bearish | 50/50 | bearish | 50/50 | 50/50 | none | 4326.16 | 4H bearish 4291.95-4338.52; 1H bullish 4281.72-4321.27 | - | - |
| Thu 17 | bearish | 50/50 | bearish | bearish | bullish | bearish (full) | 4304.23 | 4H bearish 4275.15-4364.60; 1H bearish 4286.95-4355.85; 4H bullish 4229.39-4303.74 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: touched at 2026-09-11 06:43:00, waiting for confirmation on 15m; 4H bearish POI 4275.15500-4364.60500: touched at 2026-09-17 01:09:00, waiting for confirmation on 15m | 07:40 UTC SHORT entry 4306.1 stop 4314.99 target 4234.66 (7.95R; BS on 5m; zone 1H 4286.95-4355.85) |
| Fri 18 | bearish | 50/50 | bearish | bullish | bullish | none | 4377.24 | 4H bearish 4340.97-4412.68; 1H bearish 4396.72-4412.68; 4H bearish 4380.94-4442.70; 1H bearish 4401.40-4437.41 | - | - |
| Mon 21 | bearish | 50/50 | bearish | bullish | bearish | bearish (full) | 4350.53 | 4H bullish 4352.30-4380.81; 4H bearish 4340.97-4412.68; 1H bullish 4304.77-4335.22; 4H bullish 4266.01-4364.60 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: touched at 2026-09-11 06:43:00, waiting for confirmation on 15m | - |
| Tue 22 | bearish | 50/50 | bearish | bearish | bearish | bearish (full) | 4323.39 | 1H bullish 4304.77-4335.22; 4H bullish 4266.01-4364.60; 1H bullish 4285.10-4318.12; 1H bearish 4339.77-4369.51 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: already traded on visit #1 - one trade per visit/touched at 2026-09-11 06:43:00, waiting for confirmation on 15m; 1H bearish POI 4339.76500-4369.50500: already traded on visit #1 - one trade per visit | 07:00 UTC SHORT entry 4323.39 stop 4347.09 target 4256.66 (2.80R; BS on 5m; zone 1H 4339.77-4369.51)<br>12:00 UTC SHORT entry 4321.52 stop 4337.69 target 4291.24 (1.86R; BS on 5m; zone 1H 4324.14-4347.09)<br>12:15 UTC SHORT entry 4314.89 stop 4347.09 target 4282.03 (1.02R; BS on 15m; zone 4H 4340.97-4412.68) |
| Wed 23 | bearish | 50/50 | bearish | 50/50 | 50/50 | none | 4334.43 | 4H bullish 4266.01-4364.60; 1H bearish 4339.77-4369.51; 1H bullish 4285.10-4318.12; 4H bearish 4340.97-4412.68 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: already traded on visit #1 - one trade per visit; 1H bearish POI 4314.72500-4345.65500: already traded on visit #1 - one trade per visit/touched at 2026-09-23 11:02:00, waiting for confirmation on 5m | 11:50 UTC SHORT entry 4313.18 stop 4318.84 target 4291.24 (3.81R; BS on 5m; zone 1H 4314.73-4345.65) |
| Thu 24 | bearish | 50/50 | bearish | bearish | 50/50 | bearish (full) | 4278.85 | 4H bullish 4229.39-4303.74; 4H bullish 4266.01-4364.60; 4H bearish 4291.24-4346.98 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: already traded on visit #1 - one trade per visit; 4H bearish POI 4291.24500-4346.98500: already traded on visit #1 - one trade per visit/touched at 2026-09-24 00:52:00, waiting for confirmation on 15m | 14:35 UTC SHORT entry 4272.69 stop 4284.8 target 4243.93 (2.36R; BS on 5m; zone 1H 4267.15-4285.40)<br>14:45 UTC SHORT entry 4273.03 stop 4296.06 target 4234.66 (1.66R; BS on 15m; zone 4H 4291.24-4346.98) |
| Fri 25 | bearish | 50/50 | bearish | bearish | 50/50 | bearish (full) | 4264.98 | 4H bullish 4229.39-4303.74; 1H bearish 4267.15-4285.40 | 1M bearish POI 4099.12500-4541.63000: touched at 2026-08-26 16:21:00, waiting for confirmation on 4H; 4H bearish POI 4340.96500-4412.67500: already traded on visit #1 - one trade per visit; 4H bearish POI 4291.24500-4346.98500: already traded on visit #1 - one trade per visit | - |

## Zones per day, as mapped (X / B / P)

**Tuesday 01 September** (price 4439.82, bias none)
- 1H bearish 4441.38-4462.95 (X 4445.20, B 4441.38-4451.77, P 4462.95; tested; formed 31 Aug 03:00)
- 4H bullish 4361.81-4471.76 (X 4406.32, B 4373.97-4471.76, P 4361.81; active; formed 19 Aug 17:00)

**Wednesday 02 September** (price 4319.73, bias none)
- no 4H or 1H zone within reach

**Thursday 03 September** (price 4430.95, bias none)
- 4H bearish 4396.15-4445.82 (X 4396.15, B 4419.94-4427.39, P 4445.82; active; formed 01 Sep 09:00)
- 1H bearish 4441.38-4462.95 (X 4445.20, B 4441.38-4451.77, P 4462.95; tested; formed 31 Aug 03:00)
- 1H bullish 4386.86-4406.49 (X 4397.48, B 4397.47-4406.49, P 4386.86; fresh; formed 03 Sep 03:00)

**Friday 04 September** (price 4471.94, bias none)
- 4H bullish 4437.53-4472.40 (X 4461.27, B 4445.78-4472.40, P 4437.53; tested; formed 03 Sep 17:00)
- 4H bearish 4450.36-4529.26 (X 4450.36, B 4462.51-4523.84, P 4529.26; active; formed 28 Aug 21:00)
- 1H bullish 4437.53-4456.35 (X 4445.82, B 4445.78-4456.35, P 4437.53; fresh; formed 03 Sep 14:00)
- 1H bearish 4486.56-4529.26 (X 4508.55, B 4486.56-4523.84, P 4529.26; tested; formed 28 Aug 18:00)
- 1H bullish 4424.72-4443.47 (X 4443.47, B 4429.78-4437.53, P 4424.72; fresh; formed 03 Sep 13:00)

**Monday 07 September** (price 4393.69, bias none)
- 1H bullish 4386.86-4406.49 (X 4397.48, B 4397.47-4406.49, P 4386.86; active; formed 03 Sep 03:00)
- 1H bullish 4371.60-4387.15 (X 4387.15, B 4379.47-4383.68, P 4371.60; tested; formed 02 Sep 21:00)
- 1H bearish 4411.95-4429.23 (X 4411.95, B 4416.48-4420.85, P 4429.23; tested; formed 07 Sep 02:00)
- 4H bullish 4327.15-4397.48 (X 4397.48, B 4332.85-4364.16, P 4327.15; tested; formed 03 Sep 01:00)
- 1H bullish 4330.49-4374.02 (X 4335.65, B 4344.12-4374.02, P 4330.49; tested; formed 02 Sep 15:00)

**Tuesday 08 September** (price 4419.02, bias none)
- 1H bearish 4434.48-4475.62 (X 4459.93, B 4434.48-4464.77, P 4475.62; tested; formed 04 Sep 14:00)
- 1H bullish 4371.60-4387.15 (X 4387.15, B 4379.47-4383.68, P 4371.60; tested; formed 02 Sep 21:00)

**Wednesday 09 September** (price 4398.49, bias none)
- 4H bearish 4380.94-4442.70 (X 4380.94, B 4407.80-4414.76, P 4442.70; active; formed 08 Sep 17:00)
- 1H bearish 4401.40-4437.41 (X 4401.40, B 4419.94-4431.15, P 4437.41; tested; formed 08 Sep 08:00)
- 4H bullish 4327.15-4397.48 (X 4397.48, B 4332.85-4364.16, P 4327.15; tested; formed 03 Sep 01:00)

**Thursday 10 September** (price 4430.82, bias none)
- 1H bearish 4401.40-4437.41 (X 4401.40, B 4419.94-4431.15, P 4437.41; active; formed 08 Sep 08:00)
- 4H bearish 4380.94-4442.70 (X 4380.94, B 4407.80-4414.76, P 4442.70; active; formed 08 Sep 17:00)
- 1H bearish 4434.48-4475.62 (X 4459.93, B 4434.48-4464.77, P 4475.62; tested; formed 04 Sep 14:00)
- 1H bullish 4400.81-4407.82 (X 4406.19, B 4404.57-4407.82, P 4400.81; tested; formed 10 Sep 03:00)
- 1H bullish 4380.10-4395.02 (X 4384.34, B 4382.35-4395.02, P 4380.10; tested; formed 09 Sep 07:00)

**Friday 11 September** (price 4345.81, bias bearish)
- 1H bearish 4323.91-4356.02 (X 4323.91, B 4332.80-4351.04, P 4356.02; active; formed 10 Sep 21:00)
- 4H bearish 4340.97-4412.68 (X 4340.97, B 4377.65-4403.88, P 4412.68; active; formed 10 Sep 17:00)

**Monday 14 September** (price 4337.15, bias none)
- 1H bullish 4328.05-4345.69 (X 4340.31, B 4335.23-4345.69, P 4328.05; tested; formed 11 Sep 07:00)
- 1H bullish 4291.95-4380.27 (X 4360.85, B 4342.38-4380.27, P 4291.95; active; formed 11 Sep 14:00)
- 4H bearish 4340.97-4412.68 (X 4340.97, B 4377.65-4403.88, P 4412.68; tested; formed 10 Sep 17:00)

**Tuesday 15 September** (price 4290.77, bias bearish)
- 4H bullish 4229.39-4303.74 (X 4303.74, B 4252.94-4260.43, P 4229.39; active; formed 07 Aug 09:00)
- 4H bearish 4291.95-4338.52 (X 4291.95, B 4318.15-4325.96, P 4338.52; tested; formed 14 Sep 09:00)

**Wednesday 16 September** (price 4326.16, bias none)
- 4H bearish 4291.95-4338.52 (X 4291.95, B 4318.15-4325.96, P 4338.52; active; formed 14 Sep 09:00)
- 1H bullish 4281.72-4321.27 (X 4310.44, B 4293.28-4321.27, P 4281.72; tested; formed 16 Sep 04:00)

**Thursday 17 September** (price 4304.23, bias bearish)
- 4H bearish 4275.15-4364.60 (X 4275.15, B 4275.81-4323.68, P 4364.60; active; formed 16 Sep 21:00)
- 1H bearish 4286.95-4355.85 (X 4323.68, B 4286.95-4341.39, P 4355.85; active; formed 16 Sep 20:00)
- 4H bullish 4229.39-4303.74 (X 4303.74, B 4252.94-4260.43, P 4229.39; tested; formed 07 Aug 09:00)

**Friday 18 September** (price 4377.24, bias none)
- 4H bearish 4340.97-4412.68 (X 4340.97, B 4377.65-4403.88, P 4412.68; active; formed 10 Sep 17:00)
- 1H bearish 4396.72-4412.68 (X 4405.44, B 4396.72-4403.88, P 4412.68; tested; formed 10 Sep 10:00)
- 4H bearish 4380.94-4442.70 (X 4380.94, B 4407.80-4414.76, P 4442.70; active; formed 08 Sep 17:00)
- 1H bearish 4401.40-4437.41 (X 4401.40, B 4419.94-4431.15, P 4437.41; tested; formed 08 Sep 08:00)

**Monday 21 September** (price 4350.53, bias bearish)
- 4H bullish 4352.30-4380.81 (X 4380.81, B 4365.23-4372.30, P 4352.30; tested; formed 18 Sep 09:00)
- 4H bearish 4340.97-4412.68 (X 4340.97, B 4377.65-4403.88, P 4412.68; active; formed 10 Sep 17:00)
- 1H bullish 4304.77-4335.22 (X 4335.22, B 4318.98-4322.94, P 4304.77; tested; formed 17 Sep 12:00)
- 4H bullish 4266.01-4364.60 (X 4364.60, B 4275.81-4285.10, P 4266.01; active; formed 17 Sep 13:00)

**Tuesday 22 September** (price 4323.39, bias bearish)
- 1H bullish 4304.77-4335.22 (X 4335.22, B 4318.98-4322.94, P 4304.77; active; formed 17 Sep 12:00)
- 4H bullish 4266.01-4364.60 (X 4364.60, B 4275.81-4285.10, P 4266.01; active; formed 17 Sep 13:00)
- 1H bullish 4285.10-4318.12 (X 4318.12, B 4298.69-4303.98, P 4285.10; active; formed 17 Sep 08:00)
- 1H bearish 4339.77-4369.51 (X 4339.77, B 4346.94-4351.06, P 4369.51; tested; formed 21 Sep 15:00)

**Wednesday 23 September** (price 4334.43, bias none)
- 4H bullish 4266.01-4364.60 (X 4364.60, B 4275.81-4285.10, P 4266.01; active; formed 17 Sep 13:00)
- 1H bearish 4339.77-4369.51 (X 4339.77, B 4346.94-4351.06, P 4369.51; tested; formed 21 Sep 15:00)
- 1H bullish 4285.10-4318.12 (X 4318.12, B 4298.69-4303.98, P 4285.10; tested; formed 17 Sep 08:00)
- 4H bearish 4340.97-4412.68 (X 4340.97, B 4377.65-4403.88, P 4412.68; tested; formed 10 Sep 17:00)

**Thursday 24 September** (price 4278.85, bias bearish)
- 4H bullish 4229.39-4303.74 (X 4303.74, B 4252.94-4260.43, P 4229.39; active; formed 07 Aug 09:00)
- 4H bullish 4266.01-4364.60 (X 4364.60, B 4275.81-4285.10, P 4266.01; active; formed 17 Sep 13:00)
- 4H bearish 4291.24-4346.98 (X 4291.24, B 4322.55-4333.01, P 4346.98; tested; formed 23 Sep 13:00)

**Friday 25 September** (price 4264.98, bias bearish)
- 4H bullish 4229.39-4303.74 (X 4303.74, B 4252.94-4260.43, P 4229.39; active; formed 07 Aug 09:00)
- 1H bearish 4267.15-4285.40 (X 4273.15, B 4267.15-4274.15, P 4285.40; tested; formed 24 Sep 10:00)
