# EURUSD, August 2026: the month the way we read it, for review against Dorus

Same reading and layout as `../../2026-09/EURUSD/README.md` (reading E of the source-trade suite: 5m shifts for 1H zones, 15m for 4H, the sweep-extreme stop, the target on the previous low, one trade per zone per visit, entries at most half the zone deep). Review question per chart: would Dorus take this, and if not, what is different?

## The trades the code took (1 in August; 0 won, -1.00R)

| # | Opened (UTC) | Side | Zone | Entry | Stop | Target | Planned R:R | Target rule | Result | Chart |
|---|---|---|---|---|---|---|---|---|---|---|
| P2 | Mon 03 Aug 07:00 | LONG | 1H 1.15238-1.15429 (5m shift) | 1.15380 | 1.15267 | 1.15587 | 1.92 | 1H previous high 1.15587 | stop -1.00R | [EURUSD_002_20260803_0700_5m.png](charts/EURUSD_002_20260803_0700_5m.png) |

Each chart shows the candles of the entry timeframe up to the entry, the zone with X / B / P, the stop and the target; the title gives the outcome. The ledger (`ledger_v5.csv`) carries every field, including the warm-up weeks before the month (1 trades, -1.00R).


Config `/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad/eval_2026_v5_prev_extreme.yaml`; one look every 5 minutes inside the session windows (09:00-11:00, 13:00-17:00 Europe/Amsterdam); warm-up 5.0 days. Bias at the first look of the day. Zones: the 4H and 1H zones within 1.0 % of price at that moment, with X / B / P as the code maps them.

## The month at a glance

| Day | 1M | 1W | 1D | 4H | 1H | 3 of 5 | Price 09:00 | Zones near price (4H/1H) | Visited, no confirmation | Signals |
|---|---|---|---|---|---|---|---|---|---|---|
| Mon 03 | 50/50 | bearish | bullish | bullish | bullish | bullish (scalp) | 1.15370 | 1H bullish 1.15238-1.15429; 4H bullish 1.15122-1.15369; 4H bearish 1.15084-1.15961; 1H bullish 1.14971-1.15261 | 4H bullish POI 1.14693-1.15136: touched at 2026-07-31 02:45:00, waiting for confirmation on 15m; 4H bullish POI 1.15122-1.15369: touched at 2026-08-03 01:01:00, waiting for confirmation on 15m; 1H bullish POI 1.14971-1.15261: R:R 0.03 below minimum 0.5/R:R 0.46 below minimum 0.5/touched at 2026-07-31 19:46:00, waiting for confirmation on 5m | 07:00 UTC LONG entry 1.1537 stop 1.15267 target 1.15587 (1.92R; BS on 5m; zone 1H 1.15238-1.15429) |
| Tue 04 | 50/50 | bearish | bullish | 50/50 | bullish | none | 1.15073 | 1H bullish 1.14971-1.15261; 1H bearish 1.15141-1.15274; 4H bullish 1.14693-1.15136; 4H bearish 1.15084-1.15961 | - | - |
| Wed 05 | 50/50 | bearish | bullish | 50/50 | bullish | none | 1.15356 | 1H bullish 1.15266-1.15351; 1H bullish 1.15226-1.15308; 4H bearish 1.15084-1.15961; 1H bullish 1.14971-1.15261 | - | - |
| Thu 06 | 50/50 | bearish | bullish | bearish | bearish | none | 1.15491 | 4H bearish 1.15084-1.15961; 1H bullish 1.15394-1.15466; 1H bullish 1.15266-1.15351; 1H bullish 1.15226-1.15308 | - | - |
| Fri 07 | 50/50 | bearish | bullish | bearish | bearish | none | 1.15221 | 1H bearish 1.15227-1.15356; 1H bullish 1.14971-1.15261; 4H bearish 1.15084-1.15961; 4H bullish 1.14693-1.15136 | - | - |
| Mon 10 | 50/50 | 50/50 | bullish | bullish | 50/50 | none | 1.15544 | 4H bearish 1.15084-1.15961; 4H bullish 1.15269-1.15594; 1H bullish 1.15269-1.15564; 4H bearish 1.15330-1.16427 | - | - |
| Tue 11 | 50/50 | 50/50 | bullish | bullish | bearish | none | 1.15410 | 1H bullish 1.15269-1.15564; 4H bullish 1.15269-1.15594; 4H bearish 1.15084-1.15961; 1H bearish 1.15478-1.15637 | - | - |
| Wed 12 | 50/50 | 50/50 | bullish | bullish | bearish | none | 1.15336 | 1H bullish 1.15269-1.15564; 4H bullish 1.15269-1.15594; 4H bearish 1.15084-1.15961; 1H bullish 1.14971-1.15261 | - | - |
| Thu 13 | 50/50 | 50/50 | bullish | bearish | 50/50 | none | 1.15250 | 4H bearish 1.15280-1.15401; 1H bullish 1.14971-1.15261; 1H bearish 1.15312-1.15543; 4H bearish 1.15084-1.15961 | - | - |
| Fri 14 | 50/50 | 50/50 | bullish | 50/50 | bullish | none | 1.15417 | 1H bearish 1.15312-1.15543; 4H bearish 1.15280-1.15401; 4H bearish 1.15084-1.15961; 1H bullish 1.15230-1.15337 | 4H bullish POI 1.14693-1.15136: touched at 2026-07-31 02:45:00, waiting for confirmation on 15m | - |
| Mon 17 | 50/50 | 50/50 | 50/50 | bullish | bullish | none | 1.15870 | 1H bullish 1.15633-1.15808; 4H bullish 1.15614-1.15808; 1H bullish 1.15556-1.15626; 4H bullish 1.15502-1.15656 | - | - |
| Tue 18 | 50/50 | 50/50 | 50/50 | 50/50 | 50/50 | none | 1.15730 | 1H bullish 1.15633-1.15808; 4H bullish 1.15614-1.15808; 1H bullish 1.15556-1.15626; 4H bullish 1.15502-1.15656 | - | - |
| Wed 19 | 50/50 | 50/50 | 50/50 | 50/50 | bullish | none | 1.15885 | 1H bullish 1.15764-1.15808; 1H bullish 1.15633-1.15808; 4H bullish 1.15614-1.15808; 1H bullish 1.15556-1.15626 | - | - |
| Thu 20 | 50/50 | 50/50 | bullish | bullish | bullish | bullish (scalp) | 1.16760 | 1H bullish 1.16023-1.16354; 4H bullish 1.15954-1.16141; 1H bullish 1.15876-1.15997; 4H bullish 1.15806-1.15954 | - | - |
| Fri 21 | 50/50 | 50/50 | 50/50 | bullish | bullish | none | 1.16978 | 1H bullish 1.16023-1.16354; 4H bullish 1.15954-1.16141; 1H bullish 1.15876-1.15997; 4H bullish 1.15806-1.15954 | - | - |
| Mon 24 | 50/50 | 50/50 | 50/50 | bullish | bullish | none | 1.16806 | 1H bearish 1.16866-1.17030; 1H bullish 1.16023-1.16354; 4H bullish 1.15954-1.16141; 1H bullish 1.15876-1.15997 | - | - |
| Tue 25 | 50/50 | 50/50 | 50/50 | bearish | bearish | none | 1.16533 | 1H bearish 1.16552-1.16687; 1H bearish 1.16683-1.16804; 4H bearish 1.16687-1.16829; 1H bullish 1.16023-1.16354 | - | - |
| Wed 26 | 50/50 | 50/50 | 50/50 | 50/50 | bearish | none | 1.16642 | 1H bearish 1.16683-1.16804; 4H bearish 1.16687-1.16829; 1H bearish 1.16866-1.17030; 1H bullish 1.16023-1.16354 | - | - |
| Thu 27 | 50/50 | 50/50 | 50/50 | bearish | 50/50 | none | 1.16541 | 1H bearish 1.16510-1.16587; 4H bearish 1.16510-1.16749; 1H bearish 1.16583-1.16712; 1H bearish 1.16683-1.16804 | - | - |
| Fri 28 | 50/50 | 50/50 | 50/50 | bearish | bearish | none | 1.16444 | 1H bearish 1.16467-1.16580; 1H bearish 1.16510-1.16587; 4H bearish 1.16510-1.16749; 1H bearish 1.16583-1.16712 | - | - |
| Mon 31 | 50/50 | 50/50 | 50/50 | bearish | bullish | none | 1.15902 | 4H bullish 1.15806-1.15954; 1H bullish 1.15764-1.15808; 4H bullish 1.15614-1.15808; 1H bullish 1.15556-1.15626 | - | - |

## Zones per day, as mapped (X / B / P)

**Monday 03 August** (price 1.15370, bias bullish)
- 1H bullish 1.15238-1.15429 (X 1.15374, B 1.15360-1.15429, P 1.15238; active; formed 02 Aug 22:00)
- 4H bullish 1.15122-1.15369 (X 1.15369, B 1.15186-1.15238, P 1.15122; active; formed 02 Aug 21:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; tested; formed 05 Jun 17:00)

**Tuesday 04 August** (price 1.15073, bias none)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; active; formed 31 Jul 18:00)
- 1H bearish 1.15141-1.15274 (X 1.15168, B 1.15141-1.15216, P 1.15274; tested; formed 03 Aug 16:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; active; formed 30 Jul 17:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 4H bullish 1.14371-1.14727 (X 1.14727, B 1.14566-1.14693, P 1.14371; tested; formed 30 Jul 13:00)
- 1H bullish 1.14479-1.14612 (X 1.14566, B 1.14555-1.14612, P 1.14479; tested; formed 30 Jul 11:00)

**Wednesday 05 August** (price 1.15356, bias none)
- 1H bullish 1.15266-1.15351 (X 1.15351, B 1.15316-1.15344, P 1.15266; tested; formed 05 Aug 04:00)
- 1H bullish 1.15226-1.15308 (X 1.15308, B 1.15264-1.15295, P 1.15226; tested; formed 04 Aug 20:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; active; formed 05 Jun 17:00)

**Thursday 06 August** (price 1.15491, bias none)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bullish 1.15394-1.15466 (X 1.15466, B 1.15408-1.15447, P 1.15394; active; formed 05 Aug 13:00)
- 1H bullish 1.15266-1.15351 (X 1.15351, B 1.15316-1.15344, P 1.15266; tested; formed 05 Aug 04:00)
- 1H bullish 1.15226-1.15308 (X 1.15308, B 1.15264-1.15295, P 1.15226; tested; formed 04 Aug 20:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; active; formed 05 Jun 17:00)

**Friday 07 August** (price 1.15221, bias none)
- 1H bearish 1.15227-1.15356 (X 1.15310, B 1.15227-1.15303, P 1.15356; active; formed 06 Aug 17:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; active; formed 31 Jul 18:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; tested; formed 05 Jun 17:00)
- 4H bullish 1.14371-1.14727 (X 1.14727, B 1.14566-1.14693, P 1.14371; tested; formed 30 Jul 13:00)

**Monday 10 August** (price 1.15544, bias none)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 4H bullish 1.15269-1.15594 (X 1.15594, B 1.15331-1.15573, P 1.15269; active; formed 07 Aug 17:00)
- 1H bullish 1.15269-1.15564 (X 1.15467, B 1.15331-1.15564, P 1.15269; active; formed 07 Aug 14:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; active; formed 05 Jun 17:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)

**Tuesday 11 August** (price 1.15410, bias none)
- 1H bullish 1.15269-1.15564 (X 1.15467, B 1.15331-1.15564, P 1.15269; active; formed 07 Aug 14:00)
- 4H bullish 1.15269-1.15594 (X 1.15594, B 1.15331-1.15573, P 1.15269; active; formed 07 Aug 17:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bearish 1.15478-1.15637 (X 1.15478, B 1.15579-1.15594, P 1.15637; tested; formed 10 Aug 13:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 4H bearish 1.15330-1.16427 (X 1.16081, B 1.15330-1.16317, P 1.16427; active; formed 05 Jun 17:00)

**Wednesday 12 August** (price 1.15336, bias none)
- 1H bullish 1.15269-1.15564 (X 1.15467, B 1.15331-1.15564, P 1.15269; active; formed 07 Aug 14:00)
- 4H bullish 1.15269-1.15594 (X 1.15594, B 1.15331-1.15573, P 1.15269; active; formed 07 Aug 17:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)
- 1H bearish 1.15478-1.15637 (X 1.15478, B 1.15579-1.15594, P 1.15637; tested; formed 10 Aug 13:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)

**Thursday 13 August** (price 1.15250, bias none)
- 4H bearish 1.15280-1.15401 (X 1.15312, B 1.15280-1.15329, P 1.15401; tested; formed 12 Aug 21:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; active; formed 31 Jul 18:00)
- 1H bearish 1.15312-1.15543 (X 1.15312, B 1.15438-1.15458, P 1.15543; fresh; formed 12 Aug 17:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bearish 1.15478-1.15637 (X 1.15478, B 1.15579-1.15594, P 1.15637; tested; formed 10 Aug 13:00)
- 4H bullish 1.14693-1.15136 (X 1.14762, B 1.14841-1.15136, P 1.14693; tested; formed 30 Jul 17:00)

**Friday 14 August** (price 1.15417, bias none)
- 1H bearish 1.15312-1.15543 (X 1.15312, B 1.15438-1.15458, P 1.15543; active; formed 12 Aug 17:00)
- 4H bearish 1.15280-1.15401 (X 1.15312, B 1.15280-1.15329, P 1.15401; tested; formed 12 Aug 21:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; active; formed 17 Jun 21:00)
- 1H bullish 1.15230-1.15337 (X 1.15311, B 1.15284-1.15337, P 1.15230; tested; formed 13 Aug 11:00)
- 1H bearish 1.15478-1.15637 (X 1.15478, B 1.15579-1.15594, P 1.15637; tested; formed 10 Aug 13:00)
- 1H bullish 1.14971-1.15261 (X 1.15261, B 1.15063-1.15122, P 1.14971; tested; formed 31 Jul 18:00)

**Monday 17 August** (price 1.15870, bias none)
- 1H bullish 1.15633-1.15808 (X 1.15808, B 1.15663-1.15723, P 1.15633; tested; formed 17 Aug 02:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; fresh; formed 17 Aug 01:00)
- 1H bullish 1.15556-1.15626 (X 1.15576, B 1.15561-1.15626, P 1.15556; tested; formed 14 Aug 13:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 4H bearish 1.15084-1.15961 (X 1.15748, B 1.15084-1.15809, P 1.15961; tested; formed 17 Jun 21:00)
- 1H bullish 1.15429-1.15502 (X 1.15454, B 1.15444-1.15502, P 1.15429; fresh; formed 14 Aug 09:00)

**Tuesday 18 August** (price 1.15730, bias none)
- 1H bullish 1.15633-1.15808 (X 1.15808, B 1.15663-1.15723, P 1.15633; active; formed 17 Aug 02:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; active; formed 17 Aug 01:00)
- 1H bullish 1.15556-1.15626 (X 1.15576, B 1.15561-1.15626, P 1.15556; tested; formed 14 Aug 13:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 1H bullish 1.15429-1.15502 (X 1.15454, B 1.15444-1.15502, P 1.15429; fresh; formed 14 Aug 09:00)
- 4H bullish 1.15366-1.15502 (X 1.15454, B 1.15392-1.15502, P 1.15366; fresh; formed 14 Aug 09:00)

**Wednesday 19 August** (price 1.15885, bias none)
- 1H bullish 1.15764-1.15808 (X 1.15807, B 1.15777-1.15808, P 1.15764; tested; formed 19 Aug 04:00)
- 1H bullish 1.15633-1.15808 (X 1.15808, B 1.15663-1.15723, P 1.15633; tested; formed 17 Aug 02:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; tested; formed 17 Aug 01:00)
- 1H bullish 1.15556-1.15626 (X 1.15576, B 1.15561-1.15626, P 1.15556; tested; formed 14 Aug 13:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 1H bullish 1.15429-1.15502 (X 1.15454, B 1.15444-1.15502, P 1.15429; fresh; formed 14 Aug 09:00)

**Thursday 20 August** (price 1.16760, bias bullish)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 4H bullish 1.15954-1.16141 (X 1.16141, B 1.15985-1.16023, P 1.15954; fresh; formed 19 Aug 13:00)
- 1H bullish 1.15876-1.15997 (X 1.15997, B 1.15893-1.15915, P 1.15876; tested; formed 19 Aug 10:00)
- 4H bullish 1.15806-1.15954 (X 1.15882, B 1.15871-1.15954, P 1.15806; fresh; formed 19 Aug 09:00)
- 1H bullish 1.15764-1.15808 (X 1.15807, B 1.15777-1.15808, P 1.15764; tested; formed 19 Aug 04:00)
- 1H bullish 1.15633-1.15808 (X 1.15808, B 1.15663-1.15723, P 1.15633; tested; formed 17 Aug 02:00)

**Friday 21 August** (price 1.16978, bias none)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 4H bullish 1.15954-1.16141 (X 1.16141, B 1.15985-1.16023, P 1.15954; fresh; formed 19 Aug 13:00)
- 1H bullish 1.15876-1.15997 (X 1.15997, B 1.15893-1.15915, P 1.15876; tested; formed 19 Aug 10:00)
- 4H bullish 1.15806-1.15954 (X 1.15882, B 1.15871-1.15954, P 1.15806; fresh; formed 19 Aug 09:00)

**Monday 24 August** (price 1.16806, bias none)
- 1H bearish 1.16866-1.17030 (X 1.16866, B 1.16910-1.16961, P 1.17030; tested; formed 21 Aug 14:00)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 4H bullish 1.15954-1.16141 (X 1.16141, B 1.15985-1.16023, P 1.15954; fresh; formed 19 Aug 13:00)
- 1H bullish 1.15876-1.15997 (X 1.15997, B 1.15893-1.15915, P 1.15876; tested; formed 19 Aug 10:00)
- 4H bullish 1.15806-1.15954 (X 1.15882, B 1.15871-1.15954, P 1.15806; fresh; formed 19 Aug 09:00)
- 1H bullish 1.15764-1.15808 (X 1.15807, B 1.15777-1.15808, P 1.15764; tested; formed 19 Aug 04:00)

**Tuesday 25 August** (price 1.16533, bias none)
- 1H bearish 1.16552-1.16687 (X 1.16552, B 1.16646-1.16671, P 1.16687; fresh; formed 25 Aug 06:00)
- 1H bearish 1.16683-1.16804 (X 1.16724, B 1.16683-1.16740, P 1.16804; tested; formed 24 Aug 09:00)
- 4H bearish 1.16687-1.16829 (X 1.16687, B 1.16734-1.16765, P 1.16829; tested; formed 24 Aug 09:00)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 1H bearish 1.16866-1.17030 (X 1.16866, B 1.16910-1.16961, P 1.17030; tested; formed 21 Aug 14:00)
- 4H bullish 1.15954-1.16141 (X 1.16141, B 1.15985-1.16023, P 1.15954; fresh; formed 19 Aug 13:00)

**Wednesday 26 August** (price 1.16642, bias none)
- 1H bearish 1.16683-1.16804 (X 1.16724, B 1.16683-1.16740, P 1.16804; tested; formed 24 Aug 09:00)
- 4H bearish 1.16687-1.16829 (X 1.16687, B 1.16734-1.16765, P 1.16829; tested; formed 24 Aug 09:00)
- 1H bearish 1.16866-1.17030 (X 1.16866, B 1.16910-1.16961, P 1.17030; tested; formed 21 Aug 14:00)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 4H bullish 1.15954-1.16141 (X 1.16141, B 1.15985-1.16023, P 1.15954; fresh; formed 19 Aug 13:00)
- 1H bullish 1.15876-1.15997 (X 1.15997, B 1.15893-1.15915, P 1.15876; tested; formed 19 Aug 10:00)

**Thursday 27 August** (price 1.16541, bias none)
- 1H bearish 1.16510-1.16587 (X 1.16510, B 1.16532-1.16554, P 1.16587; active; formed 26 Aug 15:00)
- 4H bearish 1.16510-1.16749 (X 1.16510, B 1.16543-1.16602, P 1.16749; active; formed 26 Aug 17:00)
- 1H bearish 1.16583-1.16712 (X 1.16583, B 1.16663-1.16695, P 1.16712; tested; formed 26 Aug 13:00)
- 1H bearish 1.16683-1.16804 (X 1.16724, B 1.16683-1.16740, P 1.16804; tested; formed 24 Aug 09:00)
- 4H bearish 1.16687-1.16829 (X 1.16687, B 1.16734-1.16765, P 1.16829; tested; formed 24 Aug 09:00)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)

**Friday 28 August** (price 1.16444, bias none)
- 1H bearish 1.16467-1.16580 (X 1.16467, B 1.16484-1.16516, P 1.16580; active; formed 27 Aug 10:00)
- 1H bearish 1.16510-1.16587 (X 1.16510, B 1.16532-1.16554, P 1.16587; tested; formed 26 Aug 15:00)
- 4H bearish 1.16510-1.16749 (X 1.16510, B 1.16543-1.16602, P 1.16749; tested; formed 26 Aug 17:00)
- 1H bearish 1.16583-1.16712 (X 1.16583, B 1.16663-1.16695, P 1.16712; tested; formed 26 Aug 13:00)
- 1H bullish 1.16023-1.16354 (X 1.16141, B 1.16085-1.16354, P 1.16023; fresh; formed 19 Aug 14:00)
- 1H bearish 1.16683-1.16804 (X 1.16724, B 1.16683-1.16740, P 1.16804; tested; formed 24 Aug 09:00)

**Monday 31 August** (price 1.15902, bias none)
- 4H bullish 1.15806-1.15954 (X 1.15882, B 1.15871-1.15954, P 1.15806; tested; formed 19 Aug 09:00)
- 1H bullish 1.15764-1.15808 (X 1.15807, B 1.15777-1.15808, P 1.15764; tested; formed 19 Aug 04:00)
- 4H bullish 1.15614-1.15808 (X 1.15808, B 1.15702-1.15736, P 1.15614; tested; formed 17 Aug 01:00)
- 1H bullish 1.15556-1.15626 (X 1.15576, B 1.15561-1.15626, P 1.15556; tested; formed 14 Aug 13:00)
- 4H bullish 1.15502-1.15656 (X 1.15656, B 1.15512-1.15619, P 1.15502; tested; formed 14 Aug 13:00)
- 4H bearish 1.15980-1.16589 (X 1.16364, B 1.15980-1.16392, P 1.16589; active; formed 28 Aug 17:00)
