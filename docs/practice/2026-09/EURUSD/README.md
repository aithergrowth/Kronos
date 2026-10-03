# EURUSD, September 2026: the month the way we read it, for review against Dorus

Max, 2 October: "pak een maand, bijv. september 2026, zorg dat 3/5 een match is, kijk naar de chart, zoek een fair value gap
in combinatie met liquiditeit voor een mogelijke entry, 4H op bijv. 5 min." This folder is that month as the code reads it,
with the reading that reproduces his entries best so far (`docs/dossiers/SOURCE_TRADES_SUITE.md`, reading E: 5m shifts
for 1H zones, 15m for 4H zones, the sweep-extreme stop, the target on the previous low, one trade per zone per visit,
entries at most half the zone deep). Review question per chart: would Dorus take this, and if not, what is different?

## The trades the code took (7 in September; 4 won, +4.44R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Wed 02 Sep 07:20 | SHORT | 1H 1.15843-1.15917 (5m shift) | 1.1578 | 1.15824 | 1.15734 | 0.85 | 1H previous low 1.15734 | stop -1.00R | [EURUSD_001_20260902_0720_5m.png](charts/EURUSD_001_20260902_0720_5m.png) |
| P2 | Wed 02 Sep 08:00 | SHORT | 4H 1.15980-1.16589 (15m shift) | 1.15676 | 1.16081 | 1.15238 | 1.06 | 4H previous low 1.15238 | stop -1.00R | [EURUSD_002_20260902_0800_15m.png](charts/EURUSD_002_20260902_0800_15m.png) |
| P3 | Fri 11 Sep 08:15 | SHORT | 4H 1.16201-1.16403 (15m shift) | 1.16079 | 1.16287 | 1.15662 | 1.91 | 4H previous low 1.15662 | take_profit +2.00R | [EURUSD_003_20260911_0815_15m.png](charts/EURUSD_003_20260911_0815_15m.png) |
| P4 | Mon 14 Sep 08:45 | SHORT | 1H 1.15662-1.15816 (5m shift) | 1.1549 | 1.15704 | 1.15238 | 1.13 | 4H sell-side liquidity 1.15238 | take_profit +1.18R | [EURUSD_004_20260914_0845_5m.png](charts/EURUSD_004_20260914_0845_5m.png) |
| P5 | Tue 22 Sep 12:10 | SHORT | 1H 1.14619-1.14713 (5m shift) | 1.14622 | 1.14708 | 1.14337 | 2.97 | 1H previous low 1.14337 | take_profit +3.31R | [EURUSD_005_20260922_1210_5m.png](charts/EURUSD_005_20260922_1210_5m.png) |
| P6 | Wed 23 Sep 07:55 | SHORT | 1H 1.14823-1.15469 (5m shift) | 1.14248 | 1.14781 | 1.13744 | 0.93 | 4H sell-side liquidity 1.13744 | take_profit +0.95R | [EURUSD_006_20260923_0755_5m.png](charts/EURUSD_006_20260923_0755_5m.png) |
| P7 | Thu 24 Sep 13:05 | SHORT | 1H 1.13686-1.13819 (5m shift) | 1.13652 | 1.1369 | 1.13616 | 0.75 | 1H previous low 1.13616 | stop -1.00R | [EURUSD_007_20260924_1305_5m.png](charts/EURUSD_007_20260924_1305_5m.png) |

Each chart shows the 5m or 15m candles up to the entry, the zone with X / B / P, the stop and the target; the title gives
the outcome. The ledger (`ledger_v5.csv`) carries every field, including the August warm-up weeks.


Config `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/eval_2026_v5_prev_extreme.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The same month with the 8-pip minimum stop (reading F, `ledger_v6.csv`)

The two trades flagged above, P1 (stop 4.4 pips) and P7 (3.8 pips), were stopped within five minutes with the sweep
extreme as the stop. With `min_stop_pips 8` (his stops are never under 9) the same seven entries give 6 wins of 7 and
+8.09R: P1 reaches its target for +0.58R, P7 (now entered 14:10, 1.13702, stop 1.13782) for +1.08R; the other five are
unchanged. August is unchanged (one trade, -1.0R). This is the month the rule was found on, so it is a check that the rule
does what it says, not evidence of an edge; the 2026 run with reading F is the test.

## Profile version 2 (`config/dorus_live.yaml`, origin target, 1D/4H/1H zones; `ledger_v2.csv`)

3 trades, 3 won, +3.5R: the 4H zones now take the entries of 11, 14 and 22 September with wider stops than the 1H zones of version 1 (7 trades, +8.1R with the minimum stop); the zone priority when a 4H and a 1H zone overlap is open.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Tue 01 | 50/50 | 50/50 | bearish | 50/50 | bearish | none | 1.16082 | 1H bullish 1.15950-1.16121; 1H bullish 1.15846-1.15944; 4H bullish 1.15806-1.15954; 4H bearish 1.15980-1.16589 | - | - |
| Wed 02 | 50/50 | 50/50 | bearish | bearish | bearish | bearish (scalp) | 1.15800 | 1H bearish 1.15843-1.15917; 4H bullish 1.15614-1.15808; 1H bearish 1.15916-1.15986; 4H bullish 1.15502-1.15656 | 4H bearish POI 1.15980-1.16589: already traded on visit #1 - one trade per visit/touched at 2026-08-31 08:43:00, waiting for confirmation on 15m; 1H bearish POI 1.16206-1.16589: R:R 0.05 below minimum 0.5/touched at 2026-08-31 16:48:00, waiting for confirmation on 5m; 1H bearish POI 1.15843-1.15917: already traded on visit #1 - one trade per visit/touched at 2026-09-02 07:13:00, waiting for confirmation on 5m | 07:20 UTC SHORT entry 1.1578 stop 1.15824 target 1.15734 (0.85R; BS on 5m; zone 1H 1.15843-1.15917)<br>08:00 UTC SHORT entry 1.15676 stop 1.16081 target 1.15238 (1.06R; BS on 15m; zone 4H 1.15980-1.16589) |
| Thu 03 | 50/50 | 50/50 | 50/50 | 50/50 | bullish | none | 1.16000 | 1H bullish 1.15709-1.15849; 4H bearish 1.15980-1.16589; 4H bullish 1.15614-1.15808; 1H bearish 1.16206-1.16589 | - | - |
| Fri 04 | 50/50 | 50/50 | 50/50 | bullish | 50/50 | none | 1.16278 | 4H bearish 1.15980-1.16589; 1H bullish 1.16212-1.16326; 1H bearish 1.16206-1.16589; 4H bullish 1.16081-1.16212 | - | - |
| Mon 07 | 50/50 | 50/50 | 50/50 | bullish | bearish | none | 1.16142 | 1H bearish 1.16084-1.16206; 4H bullish 1.16081-1.16212; 4H bearish 1.15980-1.16589; 4H bullish 1.15835-1.16091 | - | - |
| Tue 08 | 50/50 | 50/50 | 50/50 | bullish | bullish | none | 1.16305 | 4H bearish 1.15980-1.16589; 1H bullish 1.16229-1.16331; 1H bearish 1.16206-1.16589; 1H bullish 1.16112-1.16209 | - | - |
| Wed 09 | 50/50 | 50/50 | 50/50 | bearish | 50/50 | none | 1.16341 | 4H bearish 1.15980-1.16589; 1H bearish 1.16206-1.16589; 1H bearish 1.16467-1.16580; 4H bullish 1.16081-1.16212 | - | - |
| Thu 10 | 50/50 | 50/50 | bearish | bullish | bullish | none | 1.16401 | 1H bearish 1.16206-1.16589; 4H bearish 1.15980-1.16589; 1H bearish 1.16467-1.16580; 1H bearish 1.16510-1.16587 | - | - |
| Fri 11 | 50/50 | 50/50 | bearish | bearish | bearish | bearish (scalp) | 1.16096 | 1H bearish 1.16053-1.16126; 4H bullish 1.15835-1.16091; 4H bearish 1.15980-1.16589; 4H bearish 1.16201-1.16403 | 4H bearish POI 1.15980-1.16589: already traded on visit #1 - one trade per visit; 1H bearish POI 1.16206-1.16589: touched at 2026-08-31 16:48:00, waiting for confirmation on 5m; 1H bearish POI 1.16053-1.16126: touched at 2026-09-11 05:10:00, waiting for confirmation on 5m | - |
| Mon 14 | 50/50 | 50/50 | bearish | bearish | bearish | bearish (scalp) | 1.15699 | 4H bullish 1.15614-1.15808; 1H bearish 1.15662-1.15816; 4H bullish 1.15502-1.15656; 1H bearish 1.15816-1.15884 | 4H bearish POI 1.15980-1.16589: already traded on visit #1 - one trade per visit; 1H bearish POI 1.15662-1.15816: touched at 2026-09-14 06:22:00, waiting for confirmation on 5m; 1H bearish POI 1.15662-1.15816: already traded on visit #1 - one trade per visit/touched at 2026-09-14 06:22:00, waiting for confirmation on 5m | 08:45 UTC SHORT entry 1.1549 stop 1.15704 target 1.15238 (1.13R; BS on 5m; zone 1H 1.15662-1.15816)<br>13:30 UTC SHORT entry 1.1541 stop 1.15511 target 1.15342 (0.61R; BS on 15m; zone 4H 1.15497-1.15706) |
| Tue 15 | 50/50 | 50/50 | bearish | 50/50 | bearish | none | 1.15350 | 4H bullish 1.15366-1.15502; 1H bearish 1.15425-1.15482; 4H bearish 1.15497-1.15706; 1H bearish 1.15662-1.15816 | - | - |
| Wed 16 | 50/50 | 50/50 | bearish | 50/50 | bullish | none | 1.15495 | 4H bearish 1.15497-1.15706; 1H bullish 1.15321-1.15440; 1H bearish 1.15662-1.15816; 4H bearish 1.15706-1.15956 | 4H bearish POI 1.15980-1.16589: already traded on visit #1 - one trade per visit; 4H bearish POI 1.15497-1.15706: already traded on visit #1 - one trade per visit | - |
| Thu 17 | 50/50 | 50/50 | bearish | 50/50 | 50/50 | none | 1.14665 | 4H bullish 1.14371-1.14762; 4H bearish 1.14736-1.15469; 1H bearish 1.14823-1.15469; 4H bullish 1.13766-1.14467 | - | - |
| Fri 18 | 50/50 | 50/50 | bearish | 50/50 | bullish | none | 1.14787 | 1H bullish 1.14717-1.14849; 1H bullish 1.14592-1.14731; 4H bullish 1.14371-1.14762; 4H bearish 1.14736-1.15469 | - | - |
| Mon 21 | 50/50 | 50/50 | bearish | bullish | bearish | none | 1.14729 | 1H bearish 1.14754-1.14831; 4H bullish 1.14371-1.14762; 4H bearish 1.14736-1.15469; 1H bearish 1.14823-1.15469 | - | - |
| Tue 22 | 50/50 | 50/50 | bearish | 50/50 | bearish | none | 1.14711 | 1H bearish 1.14710-1.14867; 4H bullish 1.14371-1.14762; 4H bearish 1.14736-1.15469; 1H bearish 1.14823-1.15469 | 4H bearish POI 1.14736-1.15469: R:R 0.33 below minimum 0.5/touched at 2026-09-17 07:22:00, waiting for confirmation on 15m; 1H bearish POI 1.14823-1.15469: R:R 0.21 below minimum 0.5/touched at 2026-09-17 07:53:00, waiting for confirmation on 5m; 1H bearish POI 1.14619-1.14713: already traded on visit #1 - one trade per visit/touched at 2026-09-22 09:52:00, waiting for confirmation on 5m | 12:10 UTC SHORT entry 1.14622 stop 1.14708 target 1.14337 (2.97R; BS on 5m; zone 1H 1.14619-1.14713) |
| Wed 23 | 50/50 | 50/50 | bearish | bearish | bearish | bearish (scalp) | 1.14258 | 1H bearish 1.14293-1.14464; 4H bullish 1.13766-1.14467; 1H bearish 1.14337-1.14550; 1H bearish 1.14619-1.14713 | 4H bearish POI 1.14736-1.15469: R:R 0.45 below minimum 0.5/touched at 2026-09-17 07:22:00, waiting for confirmation on 15m; 1H bearish POI 1.14823-1.15469: already traded on visit #1 - one trade per visit/touched at 2026-09-17 07:53:00, waiting for confirmation on 5m; 1H bearish POI 1.14337-1.14550: already traded on visit #1 - one trade per visit/touched at 2026-09-23 00:19:00, waiting for confirmation on 5m | 07:55 UTC SHORT entry 1.14248 stop 1.14781 target 1.13744 (0.93R; BS on 5m; zone 1H 1.14823-1.15469)<br>08:45 UTC SHORT entry 1.14223 stop 1.14489 target 1.13744 (1.74R; BS on 5m; zone 1H 1.14337-1.14550)<br>12:25 UTC SHORT entry 1.14132 stop 1.14299 target 1.13744 (2.19R; BS on 5m; zone 1H 1.14293-1.14464) |
| Thu 24 | 50/50 | 50/50 | bearish | 50/50 | 50/50 | none | 1.13764 | 4H bullish 1.13766-1.14467; 1H bearish 1.14293-1.14464; 1H bearish 1.14337-1.14550; 1H bearish 1.14619-1.14713 | 1H bearish POI 1.13686-1.13819: already traded on visit #1 - one trade per visit; 1H bearish POI 1.13686-1.13819: already traded on visit #1 - one trade per visit; 1H bearish POI 1.13686-1.13819: already traded on visit #1 - one trade per visit | 13:05 UTC SHORT entry 1.13652 stop 1.1369 target 1.13616 (0.75R; BS on 5m; zone 1H 1.13686-1.13819) |
| Fri 25 | 50/50 | 50/50 | bearish | bearish | 50/50 | none | 1.13739 | 1H bearish 1.13686-1.13819; 1H bearish 1.14293-1.14464; 1H bearish 1.14337-1.14550; 1H bearish 1.14619-1.14713 | - | - |

## Zones per day, as mapped (X / B / P)

**Tuesday 01 September** (price 1.16082, bias none)
- 1H bullish 1.15950-1.16121 (X 1.16058, B 1.16009-1.16121, P 1.15950; active; formed 31 Aug 16:00)
- 1H bullish 1.15846-1.15944 (X 1.15944, B 1.15913-1.15929, P 1.15846; tested; formed 31 Aug 09:00)
- 4H bullish 1.15806-1.15954 (X 1.15882, B 1.15871-1.15954, P 1.15806; active; formed 19 Aug 09:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; tested; formed 28 Aug 17:00)
- 1H bullish 1.15764-1.15808 (X 1.15807, B 1.15777-1.15808, P 1.15764; tested; formed 19 Aug 04:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; tested; formed 28 Aug 16:00)

**Wednesday 02 September** (price 1.15800, bias bearish)
- 1H bearish 1.15843-1.15917 (X 1.15846, B 1.15843-1.15904, P 1.15917; fresh; formed 02 Sep 02:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; active; formed 17 Aug 01:00)
- 1H bearish 1.15916-1.15986 (X 1.15916, B 1.15931-1.15945, P 1.15986; tested; formed 01 Sep 17:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 4H bullish 1.15366-1.15502 (X 1.15454, B 1.15392-1.15502, P 1.15366; fresh; formed 14 Aug 09:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; tested; formed 28 Aug 17:00)

**Thursday 03 September** (price 1.16000, bias none)
- 1H bullish 1.15709-1.15849 (X 1.15849, B 1.15726-1.15755, P 1.15709; tested; formed 02 Sep 14:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; tested; formed 17 Aug 01:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; tested; formed 28 Aug 16:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; tested; formed 27 Aug 10:00)

**Friday 04 September** (price 1.16278, bias none)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 1H bullish 1.16212-1.16326 (X 1.16301, B 1.16273-1.16326, P 1.16212; active; formed 03 Sep 18:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; active; formed 28 Aug 16:00)
- 4H bullish 1.16081-1.16212 (X 1.16206, B 1.16143-1.16212, P 1.16081; tested; formed 03 Sep 17:00)
- 1H bullish 1.16081-1.16171 (X 1.16147, B 1.16143-1.16171, P 1.16081; tested; formed 03 Sep 14:00)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; tested; formed 27 Aug 10:00)

**Monday 07 September** (price 1.16142, bias none)
- 1H bearish 1.16084-1.16206 (X 1.16084, B 1.16133-1.16175, P 1.16206; active; formed 06 Sep 22:00)
- 4H bullish 1.16081-1.16212 (X 1.16206, B 1.16143-1.16212, P 1.16081; active; formed 03 Sep 17:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 4H bullish 1.15835-1.16091 (X 1.16091, B 1.15899-1.15934, P 1.15835; tested; formed 03 Sep 09:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; tested; formed 28 Aug 16:00)
- 1H bullish 1.15709-1.15849 (X 1.15849, B 1.15726-1.15755, P 1.15709; tested; formed 02 Sep 14:00)

**Tuesday 08 September** (price 1.16305, bias none)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 1H bullish 1.16229-1.16331 (X 1.16331, B 1.16229-1.16252, P 1.16229; active; formed 08 Sep 02:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; active; formed 28 Aug 16:00)
- 1H bullish 1.16112-1.16209 (X 1.16200, B 1.16193-1.16209, P 1.16112; tested; formed 07 Sep 09:00)
- 4H bullish 1.16081-1.16212 (X 1.16206, B 1.16143-1.16212, P 1.16081; active; formed 03 Sep 17:00)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; tested; formed 27 Aug 10:00)

**Wednesday 09 September** (price 1.16341, bias none)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; active; formed 28 Aug 16:00)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; tested; formed 27 Aug 10:00)
- 4H bullish 1.16081-1.16212 (X 1.16206, B 1.16143-1.16212, P 1.16081; tested; formed 03 Sep 17:00)
- 1H bearish 1.16510-1.16587 (X 1.16510, B 1.16532-1.16554, P 1.16587; tested; formed 26 Aug 15:00)
- 4H bearish 1.16510-1.16749 (X 1.16510, B 1.16543-1.16602, P 1.16749; tested; formed 26 Aug 17:00)

**Thursday 10 September** (price 1.16401, bias none)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; active; formed 28 Aug 16:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; tested; formed 27 Aug 10:00)
- 1H bearish 1.16510-1.16587 (X 1.16510, B 1.16532-1.16554, P 1.16587; tested; formed 26 Aug 15:00)
- 4H bearish 1.16510-1.16749 (X 1.16510, B 1.16543-1.16602, P 1.16749; tested; formed 26 Aug 17:00)
- 1H bearish 1.16583-1.16712 (X 1.16583, B 1.16663-1.16695, P 1.16712; tested; formed 26 Aug 13:00)

**Friday 11 September** (price 1.16096, bias bearish)
- 1H bearish 1.16053-1.16126 (X 1.16053, B 1.16077-1.16107, P 1.16126; active; formed 11 Sep 04:00)
- 4H bullish 1.15835-1.16091 (X 1.16091, B 1.15899-1.15934, P 1.15835; active; formed 03 Sep 09:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
- 4H bearish 1.16201-1.16403 (X 1.16201, B 1.16315-1.16355, P 1.16403; tested; formed 10 Sep 13:00)
- 1H bearish 1.16284-1.16380 (X 1.16292, B 1.16284-1.16312, P 1.16380; tested; formed 10 Sep 12:00)
- 1H bearish 1.16206-1.16589 (X 1.16364, B 1.16206-1.16371, P 1.16589; tested; formed 28 Aug 16:00)

**Monday 14 September** (price 1.15699, bias bearish)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; tested; formed 17 Aug 01:00)
- 1H bearish 1.15662-1.15816 (X 1.15662, B 1.15706-1.15809, P 1.15816; tested; formed 14 Sep 05:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 1H bearish 1.15816-1.15884 (X 1.15827, B 1.15816-1.15833, P 1.15884; fresh; formed 14 Sep 04:00)
- 4H bullish 1.15366-1.15502 (X 1.15454, B 1.15392-1.15502, P 1.15366; active; formed 14 Aug 09:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; tested; formed 28 Aug 17:00)

**Tuesday 15 September** (price 1.15350, bias none)
- 4H bullish 1.15366-1.15502 (X 1.15454, B 1.15392-1.15502, P 1.15366; active; formed 14 Aug 09:00)
- 1H bearish 1.15425-1.15482 (X 1.15425, B 1.15438-1.15467, P 1.15482; fresh; formed 15 Sep 02:00)
- 4H bearish 1.15497-1.15706 (X 1.15662, B 1.15497-1.15690, P 1.15706; tested; formed 14 Sep 09:00)
- 1H bearish 1.15662-1.15816 (X 1.15662, B 1.15706-1.15809, P 1.15816; tested; formed 14 Sep 05:00)
- 4H bearish 1.15706-1.15956 (X 1.15847, B 1.15706-1.15894, P 1.15956; fresh; formed 14 Sep 05:00)
- 1H bearish 1.15816-1.15884 (X 1.15827, B 1.15816-1.15833, P 1.15884; fresh; formed 14 Sep 04:00)

**Wednesday 16 September** (price 1.15495, bias none)
- 4H bearish 1.15497-1.15706 (X 1.15662, B 1.15497-1.15690, P 1.15706; tested; formed 14 Sep 09:00)
- 1H bullish 1.15321-1.15440 (X 1.15440, B 1.15362-1.15397, P 1.15321; tested; formed 16 Sep 05:00)
- 1H bearish 1.15662-1.15816 (X 1.15662, B 1.15706-1.15809, P 1.15816; tested; formed 14 Sep 05:00)
- 4H bearish 1.15706-1.15956 (X 1.15847, B 1.15706-1.15894, P 1.15956; fresh; formed 14 Sep 05:00)
- 1H bearish 1.15816-1.15884 (X 1.15827, B 1.15816-1.15833, P 1.15884; fresh; formed 14 Sep 04:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; tested; formed 28 Aug 17:00)

**Thursday 17 September** (price 1.14665, bias none)
- 4H bullish 1.14371-1.14762 (X 1.14762, B 1.14566-1.14693, P 1.14371; active; formed 30 Jul 13:00)
- 4H bearish 1.14736-1.15469 (X 1.15270, B 1.14736-1.15278, P 1.15469; fresh; formed 16 Sep 21:00)
- 1H bearish 1.14823-1.15469 (X 1.15318, B 1.14823-1.15304, P 1.15469; active; formed 16 Sep 20:00)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; tested; formed 29 Jul 21:00)
- 4H bearish 1.15497-1.15706 (X 1.15662, B 1.15497-1.15690, P 1.15706; tested; formed 14 Sep 09:00)
- 1H bearish 1.15662-1.15816 (X 1.15662, B 1.15706-1.15809, P 1.15816; tested; formed 14 Sep 05:00)

**Friday 18 September** (price 1.14787, bias none)
- 1H bullish 1.14717-1.14849 (X 1.14835, B 1.14790-1.14849, P 1.14717; active; formed 17 Sep 14:00)
- 1H bullish 1.14592-1.14731 (X 1.14731, B 1.14614-1.14632, P 1.14592; tested; formed 17 Sep 07:00)
- 4H bullish 1.14371-1.14762 (X 1.14762, B 1.14566-1.14693, P 1.14371; tested; formed 30 Jul 13:00)
- 4H bearish 1.14736-1.15469 (X 1.15270, B 1.14736-1.15278, P 1.15469; active; formed 16 Sep 21:00)
- 1H bearish 1.14823-1.15469 (X 1.15318, B 1.14823-1.15304, P 1.15469; active; formed 16 Sep 20:00)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; tested; formed 29 Jul 21:00)

**Monday 21 September** (price 1.14729, bias none)
- 1H bearish 1.14754-1.14831 (X 1.14754, B 1.14780-1.14804, P 1.14831; active; formed 21 Sep 04:00)
- 4H bullish 1.14371-1.14762 (X 1.14762, B 1.14566-1.14693, P 1.14371; tested; formed 30 Jul 13:00)
- 4H bearish 1.14736-1.15469 (X 1.15270, B 1.14736-1.15278, P 1.15469; active; formed 16 Sep 21:00)
- 1H bearish 1.14823-1.15469 (X 1.15318, B 1.14823-1.15304, P 1.15469; tested; formed 16 Sep 20:00)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; tested; formed 29 Jul 21:00)
- 4H bearish 1.15497-1.15706 (X 1.15662, B 1.15497-1.15690, P 1.15706; tested; formed 14 Sep 09:00)

**Tuesday 22 September** (price 1.14711, bias none)
- 1H bearish 1.14710-1.14867 (X 1.14710, B 1.14759-1.14836, P 1.14867; tested; formed 21 Sep 16:00)
- 4H bullish 1.14371-1.14762 (X 1.14762, B 1.14566-1.14693, P 1.14371; active; formed 30 Jul 13:00)
- 4H bearish 1.14736-1.15469 (X 1.15270, B 1.14736-1.15278, P 1.15469; tested; formed 16 Sep 21:00)
- 1H bearish 1.14823-1.15469 (X 1.15318, B 1.14823-1.15304, P 1.15469; tested; formed 16 Sep 20:00)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; tested; formed 29 Jul 21:00)
- 4H bearish 1.15497-1.15706 (X 1.15662, B 1.15497-1.15690, P 1.15706; tested; formed 14 Sep 09:00)

**Wednesday 23 September** (price 1.14258, bias bearish)
- 1H bearish 1.14293-1.14464 (X 1.14293, B 1.14390-1.14447, P 1.14464; tested; formed 23 Sep 04:00)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; active; formed 29 Jul 21:00)
- 1H bearish 1.14337-1.14550 (X 1.14337, B 1.14440-1.14516, P 1.14550; tested; formed 22 Sep 16:00)
- 1H bearish 1.14619-1.14713 (X 1.14619, B 1.14647-1.14702, P 1.14713; tested; formed 22 Sep 08:00)
- 1H bearish 1.14710-1.14867 (X 1.14710, B 1.14759-1.14836, P 1.14867; tested; formed 21 Sep 16:00)
- 4H bearish 1.14736-1.15469 (X 1.15270, B 1.14736-1.15278, P 1.15469; tested; formed 16 Sep 21:00)

**Thursday 24 September** (price 1.13764, bias none)
- 4H bullish 1.13766-1.14467 (X 1.14052, B 1.13969-1.14467, P 1.13766; active; formed 29 Jul 21:00)
- 1H bearish 1.14293-1.14464 (X 1.14293, B 1.14390-1.14447, P 1.14464; tested; formed 23 Sep 04:00)
- 1H bearish 1.14337-1.14550 (X 1.14337, B 1.14440-1.14516, P 1.14550; tested; formed 22 Sep 16:00)
- 1H bearish 1.14619-1.14713 (X 1.14619, B 1.14647-1.14702, P 1.14713; tested; formed 22 Sep 08:00)
- 1H bearish 1.14710-1.14867 (X 1.14710, B 1.14759-1.14836, P 1.14867; tested; formed 21 Sep 16:00)

**Friday 25 September** (price 1.13739, bias none)
- 1H bearish 1.13686-1.13819 (X 1.13686, B 1.13756-1.13794, P 1.13819; active; formed 24 Sep 12:00)
- 1H bearish 1.14293-1.14464 (X 1.14293, B 1.14390-1.14447, P 1.14464; tested; formed 23 Sep 04:00)
- 1H bearish 1.14337-1.14550 (X 1.14337, B 1.14440-1.14516, P 1.14550; tested; formed 22 Sep 16:00)
- 1H bearish 1.14619-1.14713 (X 1.14619, B 1.14647-1.14702, P 1.14713; tested; formed 22 Sep 08:00)
- 1H bearish 1.14710-1.14867 (X 1.14710, B 1.14759-1.14836, P 1.14867; tested; formed 21 Sep 16:00)
