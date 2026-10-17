# XAUUSD, August 2026: the month the way we read it, for review against Dorus

Same reading and layout as `../../2026-09/EURUSD/README.md` (reading E of the source-trade suite: 5m shifts for 1H zones, 15m for 4H, the sweep-extreme stop, the target on the previous low, one trade per zone per visit, entries at most half the zone deep). Review question per chart: would Dorus take this, and if not, what is different?

## The trades the code took (3 in August; 1 won, +0.49R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Thu 06 Aug 13:00 | LONG | 1H 4248.19-4267.72 (5m shift) | 4263.40 | 4253.90 | 4303.74 | 4.31 | 1H previous high 4303.74500 | stop -1.00R | [XAUUSD_001_20260806_1300_5m.png](charts/XAUUSD_001_20260806_1300_5m.png) |
| P2 | Wed 12 Aug 07:00 | LONG | 1H 4317.74-4361.89 (5m shift) | 4391.01 | 4361.49 | 4434.97 | 1.50 | 1H previous high 4434.96500 | take_profit +1.49R | [XAUUSD_002_20260812_0700_5m.png](charts/XAUUSD_002_20260812_0700_5m.png) |
| P3 | Mon 17 Aug 13:55 | LONG | 1H 4367.57-4396.77 (5m shift) | 4384.19 | 4376.78 | 4449.45 | 8.97 | 1H previous high 4449.45500 | breakeven +0.00R | [XAUUSD_003_20260817_1355_5m.png](charts/XAUUSD_003_20260817_1355_5m.png) |

Each chart shows the candles of the entry timeframe up to the entry, the zone with X / B / P, the stop and the target; the title gives the outcome. The ledger (`ledger_v5.csv`) carries every field, including the warm-up weeks before the month (0 trades, +0.00R).


Config `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/eval_2026_v5_prev_extreme.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 03 | bearish | bearish | 50/50 | bullish | bearish | none | 4068.64 | 1H bearish 4067.95-4079.01; 1H bearish 4097.53-4119.35 | - | - |
| Tue 04 | bearish | bearish | 50/50 | bullish | bullish | none | 4061.57 | 1H bearish 4067.95-4079.01; 4H bullish 4007.47-4047.64; 1H bullish 4007.47-4047.64; 4H bullish 4003.49-4043.36 | - | - |
| Wed 05 | bearish | bearish | 50/50 | bullish | bullish | none | 4161.15 | 4H bearish 4146.80-4198.44; 4H bearish 4128.27-4162.45 | - | - |
| Thu 06 | bearish | bearish | bullish | bullish | 50/50 | none | 4266.81 | 1H bullish 4248.19-4267.72; 4H bearish 4218.81-4292.65 | 1H bullish POI 4248.19500-4267.71500: already traded on visit #1 - one trade per visit/touched at 2026-08-06 04:17:00, waiting for confirmation on 5m; 1H bullish POI 4248.19500-4267.71500: already traded on visit #1 - one trade per visit/touched at 2026-08-06 04:17:00, waiting for confirmation on 5m | 13:00 UTC LONG entry 4263.2 stop 4253.9 target 4303.74 (4.31R; BS on 5m; zone 1H 4248.19-4267.72) |
| Fri 07 | bearish | bearish | bullish | bullish | bullish | bullish (scalp) | 4278.47 | 4H bearish 4218.81-4292.65 | 4H bullish POI 4229.38500-4303.74500: R:R 0.26 below minimum 0.5/touched at 2026-08-07 13:29:00, waiting for confirmation on 15m; 1H bullish POI 4288.83500-4303.74500: touched at 2026-08-07 13:29:00, waiting for confirmation on 5m | - |
| Mon 10 | bearish | bearish | bullish | bullish | 50/50 | none | 4347.03 | 4H bearish 4283.80-4382.12 | 4H bullish POI 4229.38500-4303.74500: touched at 2026-08-07 13:29:00, waiting for confirmation on 15m | - |
| Tue 11 | bearish | bearish | bullish | bullish | 50/50 | none | 4375.24 | 4H bullish 4350.80-4385.51; 1H bullish 4317.74-4361.89; 4H bearish 4347.15-4475.65 | - | - |
| Wed 12 | bearish | bearish | bullish | bullish | bullish | bullish (scalp) | 4390.81 | 1H bullish 4366.06-4403.94; 4H bullish 4350.80-4385.51 | 4H bullish POI 4350.79500-4385.50500: already traded on visit #1 - one trade per visit/touched at 2026-08-11 06:30:00, waiting for confirmation on 15m; 1H bullish POI 4317.74500-4361.88500: already traded on visit #1 - one trade per visit; 1H bullish POI 4366.06500-4403.94500: already traded on visit #1 - one trade per visit/touched at 2026-08-12 04:37:00, waiting for confirmation on 5m | 07:00 UTC LONG entry 4390.81 stop 4361.49 target 4434.97 (1.50R; BS on 5m; zone 1H 4317.74-4361.89)<br>08:00 UTC LONG entry 4403.05 stop 4383.64 target 4434.97 (1.64R; BS on 15m; zone 4H 4350.80-4385.51)<br>08:30 UTC LONG entry 4402.34 stop 4383.64 target 4434.97 (1.74R; BS on 5m; zone 1H 4366.06-4403.94) |
| Thu 13 | bearish | bearish | bullish | 50/50 | 50/50 | none | 4382.90 | 1H bullish 4366.06-4403.94; 4H bullish 4350.80-4385.51; 1H bullish 4317.74-4361.89 | - | - |
| Fri 14 | bearish | bearish | bullish | 50/50 | bearish | none | 4333.40 | 1H bearish 4316.31-4341.23; 1H bearish 4341.23-4361.78; 1H bullish 4288.84-4303.74 | - | - |
| Mon 17 | bearish | 50/50 | bullish | 50/50 | 50/50 | none | 4394.41 | 1H bearish 4385.36-4407.12; 1H bullish 4367.57-4396.77 | 1H bullish POI 4367.57500-4396.76500: touched at 2026-08-17 03:00:00, waiting for confirmation on 5m; 1H bullish POI 4367.57500-4396.76500: touched at 2026-08-17 03:00:00, waiting for confirmation on 5m | 13:55 UTC LONG entry 4383.98 stop 4376.78 target 4449.45 (8.97R; BS on 5m; zone 1H 4367.57-4396.77) |
| Tue 18 | bearish | 50/50 | bullish | bullish | bearish | none | 4394.02 | 1H bullish 4381.69-4405.65; 1H bullish 4367.57-4396.77; 1H bearish 4397.85-4435.90 | - | - |
| Wed 19 | bearish | 50/50 | bullish | bearish | 50/50 | none | 4335.47 | 1H bullish 4329.51-4364.01; 1H bearish 4346.27-4358.52; 1H bullish 4288.84-4303.74 | - | - |
| Thu 20 | bearish | 50/50 | bullish | bullish | bearish | none | 4481.27 | 1H bearish 4484.06-4509.78; 1H bullish 4423.82-4454.90 | - | - |
| Fri 21 | bearish | 50/50 | bullish | bearish | bullish | none | 4553.34 | - | 4H bullish POI 4361.80500-4471.75500: touched at 2026-08-20 12:45:00, waiting for confirmation on 15m | - |
| Mon 24 | bearish | 50/50 | bullish | bullish | bullish | bullish (scalp) | 4640.51 | 1H bullish 4587.03-4608.89 | - | - |
| Tue 25 | bearish | 50/50 | bullish | bullish | bearish | none | 4642.80 | 1H bearish 4629.55-4686.65; 1H bullish 4587.03-4608.89 | - | - |
| Wed 26 | bearish | 50/50 | bullish | bullish | 50/50 | none | 4639.30 | 1H bearish 4629.55-4686.65; 1H bullish 4587.03-4608.89 | - | - |
| Thu 27 | bearish | 50/50 | bullish | bearish | bullish | none | 4606.61 | 1H bullish 4593.94-4606.27; 1H bullish 4587.03-4608.89; 4H bearish 4604.35-4633.27; 1H bearish 4629.23-4658.56 | - | - |
| Fri 28 | bearish | 50/50 | bullish | bearish | bearish | none | 4573.01 | 4H bullish 4529.05-4559.05; 1H bearish 4582.78-4621.36 | - | - |
| Mon 31 | bearish | 50/50 | 50/50 | bearish | bearish | none | 4442.53 | 1H bearish 4441.38-4462.95; 4H bullish 4361.81-4471.76 | - | - |

## Zones per day, as mapped (X / B / P)

**Monday 03 August** (price 4068.64, bias none)
- 1H bearish 4067.95-4079.01 (X 4071.59, B 4067.95-4072.57, P 4079.01; tested; formed 31 Jul 09:00)
- 1H bearish 4097.53-4119.35 (X 4111.81, B 4097.53-4116.53, P 4119.35; tested; formed 23 Jul 09:00)

**Tuesday 04 August** (price 4061.57, bias none)
- 1H bearish 4067.95-4079.01 (X 4071.59, B 4067.95-4072.57, P 4079.01; tested; formed 31 Jul 09:00)
- 4H bullish 4007.47-4047.64 (X 4047.64, B 4033.30-4043.62, P 4007.47; tested; formed 29 Jul 21:00)
- 1H bullish 4007.47-4047.64 (X 4047.64, B 4013.55-4026.99, P 4007.47; tested; formed 29 Jul 19:00)
- 4H bullish 4003.49-4043.36 (X 4040.43, B 4010.49-4043.36, P 4003.49; tested; formed 21 Jul 05:00)

**Wednesday 05 August** (price 4161.15, bias none)
- 4H bearish 4146.80-4198.44 (X 4169.48, B 4146.80-4186.51, P 4198.44; active; formed 23 Jun 05:00)
- 4H bearish 4128.27-4162.45 (X 4128.27, B 4140.99-4156.60, P 4162.45; tested; formed 07 Jul 05:00)

**Thursday 06 August** (price 4266.81, bias none)
- 1H bullish 4248.19-4267.72 (X 4267.72, B 4253.80-4264.19, P 4248.19; active; formed 06 Aug 01:00)
- 4H bearish 4218.81-4292.65 (X 4218.81, B 4276.52-4287.23, P 4292.65; active; formed 18 Jun 17:00)

**Friday 07 August** (price 4278.47, bias bullish)
- 4H bearish 4218.81-4292.65 (X 4218.81, B 4276.52-4287.23, P 4292.65; active; formed 18 Jun 17:00)

**Monday 10 August** (price 4347.03, bias none)
- 4H bearish 4283.80-4382.12 (X 4313.01, B 4283.80-4319.66, P 4382.12; active; formed 17 Jun 21:00)

**Tuesday 11 August** (price 4375.24, bias none)
- 4H bullish 4350.80-4385.51 (X 4361.89, B 4359.34-4385.51, P 4350.80; active; formed 10 Aug 21:00)
- 1H bullish 4317.74-4361.89 (X 4361.89, B 4339.68-4343.10, P 4317.74; active; formed 10 Aug 19:00)
- 4H bearish 4347.15-4475.65 (X 4423.69, B 4347.15-4458.18, P 4475.65; active; formed 05 Jun 17:00)

**Wednesday 12 August** (price 4390.81, bias bullish)
- 1H bullish 4366.06-4403.94 (X 4403.94, B 4374.23-4377.90, P 4366.06; active; formed 12 Aug 03:00)
- 4H bullish 4350.80-4385.51 (X 4361.89, B 4359.34-4385.51, P 4350.80; tested; formed 10 Aug 21:00)

**Thursday 13 August** (price 4382.90, bias none)
- 1H bullish 4366.06-4403.94 (X 4403.94, B 4374.23-4377.90, P 4366.06; active; formed 12 Aug 03:00)
- 4H bullish 4350.80-4385.51 (X 4361.89, B 4359.34-4385.51, P 4350.80; active; formed 10 Aug 21:00)
- 1H bullish 4317.74-4361.89 (X 4361.89, B 4339.68-4343.10, P 4317.74; tested; formed 10 Aug 19:00)

**Friday 14 August** (price 4333.40, bias none)
- 1H bearish 4316.31-4341.23 (X 4316.31, B 4322.84-4328.91, P 4341.23; active; formed 14 Aug 03:00)
- 1H bearish 4341.23-4361.78 (X 4343.36, B 4341.23-4348.06, P 4361.78; fresh; formed 14 Aug 02:00)
- 1H bullish 4288.84-4303.74 (X 4303.74, B 4297.74-4302.15, P 4288.84; tested; formed 07 Aug 10:00)

**Monday 17 August** (price 4394.41, bias none)
- 1H bearish 4385.36-4407.12 (X 4395.98, B 4385.36-4391.38, P 4407.12; active; formed 13 Aug 07:00)
- 1H bullish 4367.57-4396.77 (X 4396.77, B 4384.80-4391.89, P 4367.57; tested; formed 17 Aug 02:00)

**Tuesday 18 August** (price 4394.02, bias none)
- 1H bullish 4381.69-4405.65 (X 4405.65, B 4398.64-4403.48, P 4381.69; active; formed 17 Aug 15:00)
- 1H bullish 4367.57-4396.77 (X 4396.77, B 4384.80-4391.89, P 4367.57; tested; formed 17 Aug 02:00)
- 1H bearish 4397.85-4435.90 (X 4397.85, B 4407.77-4418.55, P 4435.90; active; formed 18 Aug 04:00)

**Wednesday 19 August** (price 4335.47, bias none)
- 1H bullish 4329.51-4364.01 (X 4364.01, B 4336.51-4341.72, P 4329.51; active; formed 14 Aug 12:00)
- 1H bearish 4346.27-4358.52 (X 4351.41, B 4346.27-4352.57, P 4358.52; active; formed 18 Aug 21:00)
- 1H bullish 4288.84-4303.74 (X 4303.74, B 4297.74-4302.15, P 4288.84; tested; formed 07 Aug 10:00)

**Thursday 20 August** (price 4481.27, bias none)
- 1H bearish 4484.06-4509.78 (X 4484.06, B 4499.56-4503.23, P 4509.78; active; formed 20 Aug 06:00)
- 1H bullish 4423.82-4454.90 (X 4449.45, B 4442.20-4454.90, P 4423.82; fresh; formed 19 Aug 15:00)

**Friday 21 August** (price 4553.34, bias none)
- no 4H or 1H zone within reach

**Monday 24 August** (price 4640.51, bias bullish)
- 1H bullish 4587.03-4608.89 (X 4604.57, B 4603.53-4608.89, P 4587.03; tested; formed 21 Aug 17:00)

**Tuesday 25 August** (price 4642.80, bias none)
- 1H bearish 4629.55-4686.65 (X 4629.55, B 4661.27-4674.93, P 4686.65; active; formed 25 Aug 03:00)
- 1H bullish 4587.03-4608.89 (X 4604.57, B 4603.53-4608.89, P 4587.03; tested; formed 21 Aug 17:00)

**Wednesday 26 August** (price 4639.30, bias none)
- 1H bearish 4629.55-4686.65 (X 4629.55, B 4661.27-4674.93, P 4686.65; active; formed 25 Aug 03:00)
- 1H bullish 4587.03-4608.89 (X 4604.57, B 4603.53-4608.89, P 4587.03; tested; formed 21 Aug 17:00)

**Thursday 27 August** (price 4606.61, bias none)
- 1H bullish 4593.94-4606.27 (X 4604.35, B 4596.44-4606.27, P 4593.94; active; formed 27 Aug 00:00)
- 1H bullish 4587.03-4608.89 (X 4604.57, B 4603.53-4608.89, P 4587.03; active; formed 21 Aug 17:00)
- 4H bearish 4604.35-4633.27 (X 4604.81, B 4604.35-4613.19, P 4633.27; tested; formed 26 Aug 17:00)
- 1H bearish 4629.23-4658.56 (X 4629.23, B 4643.97-4654.60, P 4658.56; tested; formed 26 Aug 08:00)

**Friday 28 August** (price 4573.01, bias none)
- 4H bullish 4529.05-4559.05 (X 4540.80, B 4543.52-4559.05, P 4529.05; fresh; formed 21 Aug 09:00)
- 1H bearish 4582.78-4621.36 (X 4582.78, B 4611.48-4616.68, P 4621.36; active; formed 27 Aug 10:00)

**Monday 31 August** (price 4442.53, bias none)
- 1H bearish 4441.38-4462.95 (X 4445.20, B 4441.38-4451.77, P 4462.95; tested; formed 31 Aug 03:00)
- 4H bullish 4361.81-4471.76 (X 4406.32, B 4373.97-4471.76, P 4361.81; active; formed 19 Aug 17:00)
