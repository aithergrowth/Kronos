# The fast loop: his dated trades against the engine, one table per reading

Max, 2 October: "misschien is de betere tactiek om bijv 1 trade te pakken en dat te vergelijken met Dorus; dat gaat veel
sneller en dan kan jij sneller en beter verbeteren."  This is that loop.  `docs/dossiers/source_trades.yaml` holds every
dated trade of his with his numbers; `scripts/source_trades.py` warms the engine up, walks the 30 minutes before and the
15 after his entry minute with his direction assumed past the gates, and prints his numbers next to the first setup the
code reaches.  One trade takes about a minute; a new screenshot is one more record.

```
PYTHONPATH=. python scripts/source_trades.py <config.yaml> [--ids K3a,K3b] [--before 30] [--after 15] [--warmup 3] [--out table.md]
```

Columns: his entry / stop / target (his R:R, outcome); the bias per timeframe at his minute; the gate (bias, session, news);
the code's first setup in the window ("signal" when every gate passes, "diagnostic" when walked past a refusing gate);
the differences in minutes and pips (positive = the code's number is higher); the first difference in words.

## Reading A: the new rules (`one_trade_per_visit`, `max_entry_depth 0.5`, `tp_max_rr 2 farthest`, stop on the zone's P, table exact)

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:22: 4627.27 / 4658.56 / 4604.81 (0.72R; BS on 1m; zone 1H 4629.23-4658.56) | -23 min; entry +27.4 pips; stop +190.1 pips; target +98.3 pips; R:R 0.72 vs 1.97 | bias refuses; 23 min earlier; stop 190 pips wider; target 98 pips nearer |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 14:40: 1.16023 / 1.16111 / 1.15934 (0.91R; BS on 1m; zone 1H 1.15967-1.16111) | -25 min; entry +6.0 pips; stop +5.1 pips; target +24.7 pips; R:R 0.91 vs 2.85 | bias refuses; 25 min earlier; stop 5 pips wider; target 25 pips nearer |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:20: 1.09023 / 1.0914 / 1.08805 (1.72R; BS on 1m; zone 1H 1.08994-1.09140) | -20 min; entry +7.3 pips; stop +9.0 pips; target +14.5 pips; R:R 1.72 vs 2.90 | bias refuses; 20 min earlier; stop 9 pips wider; target 14 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 5m |

## Reading B: the sweep-extreme stop (R7's reading: `stop_basis confirmation`, `stop_protection recent_1h`, table exact)

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:22: 4627.27 / 4629.82 / 4604.81 (8.48R; BS on 1m; zone 1H 4629.55-4686.65) | -23 min; entry +27.4 pips; stop -97.3 pips; target +98.3 pips; R:R 8.48 vs 1.97 | bias refuses; 23 min earlier; stop 97 pips tighter; target 98 pips nearer |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 14:40: 1.16023 / 1.16048 / 1.15468 (15.86R; BS on 1m; zone 1H 1.15967-1.16111) | -25 min; entry +6.0 pips; stop -1.2 pips; target -21.9 pips; R:R 15.86 vs 2.85 | bias refuses; 25 min earlier; target 22 pips farther |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:20: 1.09023 / 1.09061 / 1.08805 (4.54R; BS on 1m; zone 1H 1.08994-1.09140) | -20 min; entry +7.3 pips; stop +1.1 pips; target +14.5 pips; R:R 4.54 vs 2.90 | bias refuses; 20 min earlier; target 14 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 5m |

## Reading C: the table one step up, exact (1H zone -> 5m, 4H -> 15m, 1D -> 1H, W/M -> 4H), otherwise reading A

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:35: 4623.1 / 4658.56 / 4604.81 (0.51R; BS on 5m; zone 1H 4629.23-4658.56) | -10 min; entry -14.3 pips; stop +190.1 pips; target +98.3 pips; R:R 0.51 vs 1.97 | bias refuses; 10 min earlier; stop 190 pips wider; target 98 pips nearer |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 15:10: 1.15948 / 1.16111 / 1.15624 (1.87R; BS on 5m; zone 1H 1.15967-1.16111) | +5 min; entry -1.5 pips; stop +5.1 pips; target -6.3 pips; R:R 1.87 vs 2.85 | bias refuses; stop 5 pips wider; target 6 pips farther |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:40: 1.08966 / 1.0914 / 1.08805 (0.88R; BS on 5m; zone 1H 1.08994-1.09140) | +0 min; entry +1.6 pips; stop +9.0 pips; target +14.5 pips; R:R 0.88 vs 2.90 | bias refuses; stop 9 pips wider; target 14 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 15m |

## Reading D: reading C with the sweep-extreme stop (`stop_basis confirmation`, `stop_protection recent_1h`)

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:35: 4623.1 / 4632.66 / 4604.81 (1.89R; BS on 5m; zone 1H 4629.55-4686.65) | -10 min; entry -14.3 pips; stop -68.9 pips; target +98.3 pips; R:R 1.89 vs 1.97 | bias refuses; 10 min earlier; stop 69 pips tighter; target 98 pips nearer |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 15:10: 1.15948 / 1.16057 / 1.15468 (4.03R; BS on 5m; zone 1H 1.15967-1.16111) | +5 min; entry -1.5 pips; stop -0.3 pips; target -21.9 pips; R:R 4.03 vs 2.85 | bias refuses; target 22 pips farther |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:40: 1.08966 / 1.09061 / 1.08805 (1.53R; BS on 5m; zone 1H 1.08994-1.09140) | +0 min; entry +1.6 pips; stop +1.1 pips; target +14.5 pips; R:R 1.53 vs 2.90 | bias refuses; target 14 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 15m |

## Reading E: reading D with `tp_policy previous_extreme` (the extreme of 72 zone-timeframe candles before the touch), no R:R cap

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:35: 4623.1 / 4632.66 / 4450.36 (17.88R; BS on 5m; zone 1H 4629.55-4686.65) | -10 min; entry -14.3 pips; stop -68.9 pips; target -1446.2 pips; R:R 17.88 vs 1.97 | bias refuses; 10 min earlier; stop 69 pips tighter; target 1446 pips farther |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 15:10: 1.15948 / 1.16057 / 1.15188 (6.39R; BS on 5m; zone 1H 1.15967-1.16111) | +5 min; entry -1.5 pips; stop -0.3 pips; target -49.9 pips; R:R 6.39 vs 2.85 | bias refuses; target 50 pips farther |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:40: 1.08966 / 1.09061 / 1.0873 (2.25R; BS on 5m; zone 1H 1.08994-1.09140) | +0 min; entry +1.6 pips; stop +1.1 pips; target +7.0 pips; R:R 2.25 vs 2.90 | bias refuses; target 7 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 15m |

## Readings F and G: the minimum stop and the gap threshold (2 October, later)

- **F: reading E + `min_stop_pips 8`** gives the same five rows as E: his five trades all carry stops of 9.5 pips or more, so
  the minimum touches none of them. It exists for the stops of 3-4 pips the sweep-extreme basis produced in September 2026
  (P1, P7 in `docs/practice/2026-09/EURUSD/`), both hit within five minutes.
- **G: reading E with `min_gap_fraction 0.1`** (half the gap-size threshold) changes nothing on K3a and K3b: the missing
  balance level on K3b is not a dropped small gap; the 14:45-15:00 climb simply left no three-candle gap on the 1m or 5m.
  His entry there reads as the first bearish candle after the sweep of B, which the engine's first-candle option did not
  fire either (not traced further).

## Reading H: the live profile with `tp_policy impulse_origin` (30 zone candles up to the P), 1D/4H/1H zones only

| id | his_time | direction | his | bias | gate | code | delta | first_difference |
|---|---|---|---|---|---|---|---|---|
| K3a | 2026-08-26 13:45 | SHORT | 4624.53 / 4639.55 / 4594.98 (1.97R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish | bias refuses | diagnostic 13:35: 4623.1 / 4632.66 / 4594.01 (3.01R; BS on 5m; zone 1H 4629.55-4686.65) | -10 min; entry -14.3 pips; stop -68.9 pips; target -9.7 pips; R:R 3.01 vs 1.97 | bias refuses; 10 min earlier; stop 69 pips tighter; target 10 pips farther |
| K3b | 2026-08-26 15:05 | SHORT | 4623.59 / 4633.72 / 4595.62 (2.76R, won) | 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H 50/50 | bias refuses; session closed | none in the window | - | bias refuses; session closed / 1M bearish POI 4099.12500-4541.63000 (fresh, formed 2026-07-01 00:00:00): touched at 2026-08-21 15:21:00, waiting for confirmation on 4H |
| EU-2025-11-11 | 2025-11-11 15:05 | SHORT | 1.15963 / 1.1606 / 1.15687 (2.85R, won) | 1M 50/50, 1W 50/50, 1D 50/50, 4H bullish, 1H bullish | bias refuses | diagnostic 15:10: 1.15948 / 1.16057 / 1.15773 (1.47R; BS on 5m; zone 1H 1.15967-1.16111) | +5 min; entry -1.5 pips; stop -0.3 pips; target +8.6 pips; R:R 1.47 vs 2.85 | bias refuses; target 9 pips nearer |
| EU-2024-03-18 | 2024-03-18 12:40 | SHORT | 1.0895 / 1.0905 / 1.0866 (2.90R, won) | 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bullish | bias refuses | diagnostic 12:45: 1.08945 / 1.09061 / 1.08692 (2.01R; BS on 15m; zone 4H 1.08918-1.09312) | +5 min; entry -0.5 pips; stop +1.1 pips; target +3.2 pips; R:R 2.01 vs 2.90 | bias refuses; target 3 pips nearer |
| EU-2025-12-09 | 2025-12-09 15:36 | LONG | 1.16335 / 1.15908 / 1.16823 (1.14R, won) | 1M 50/50, 1W 50/50, 1D bullish, 4H bullish, 1H bullish | open | none in the window | - |  / 4H bullish POI 1.15903-1.16188 (tested, formed 2025-12-01 10:00:00): touched at 2025-12-08 15:41:00, waiting for confirmation on 15m |

Max's steer ("hij pakt een bepaald punt van higher low") and the course: "stop loss op de low en take profit bij de vorige
high" at every worked trade (A 00:43:39, 01:09:01, 01:20:52, 02:45:57), and the previous higher low as the level whose
break is the break of market structure (A 00:14:48). Implemented as the extreme of the candles up to the zone's P candle:
the low the move that created the zone started from. K3a lands 1.0 point from his target (4594.01 against 4594.98) and
18 Mar 2024 3.2 pips (1.08692 against 1.0866, now from the 4H zone, entry 0.5 pip and stop 1.1 pip from his). On 11 Nov
2025 the target sits 8.6 pips nearer than his (1.15773 against 1.15687): the code's zone 1.15967-1.16111 formed on 30 Oct,
so its creating move lies twelve days back; his low is the 12:45 dip of 11 Nov, the move back into the zone that day.
Two origins, then: the move that created the zone (K3a, 18 Mar) and the move that re-entered it (11 Nov); the first is
implemented, the second is open, and where they differ the implemented one gives the nearer target. Windows of 24 and
48 candles miss K3a (4607.6, 4508.6); 30 is the one that fits.

## What the tables say

1. **The bias gate refuses four of the five** on the pair's own levels (K3a, K3b, 11 Nov 2025, 18 Mar 2024); the weekly long
   of 9 Dec 2025 passes it. The gate is the first and largest difference on every intraday trade of his, and it is not a
   code gap: he read those biases from somewhere else (the dollar index on 11 Nov; not confirmed as a rule, see
   `SOURCE_TRADES.md`).
2. **The code's first shift comes 20-25 minutes before his entry** on all three reproduced trades (13:22 against 13:45;
   14:40 against 15:05; 12:20 against 12:40). He does not take the first 1m shift. On 18 Mar 2024 his entry is the 5m shift
   of 12:40; on K3b his 4623.59 is the close of the 15:00-15:05 5m candle (4623.89) within 0.3; on K3a his 13:45 is the
   close of the 13:40-13:45 5m candle (4623.30) within 1.2. **Reading C confirms it**: with the 5m as the entry timeframe
   for a 1H zone the code lands on 18 Mar 2024 at 12:40, 1.6 pips from his entry, on 11 Nov 2025 at 15:10, 1.5 pips from
   his, and on K3a at 13:35, 14 pips (1.4 points) from his and ten minutes early. His entries on 1H zones are 5m shifts,
   not the first 1m shift; the written table's "1H -> 1m" reads as a floor he does not use there.
3. **Stops.** On EURUSD his stops are the sweep extreme: reading D puts the code's stop 0.3 pip from his on 11 Nov 2025 and
   1.1 pip from his on 18 Mar 2024, with the entries matched as well (reading D is the closest reading of the four on both
   trades: entry, stop and minute). On gold he protects more: K3a the morning high 4639.14 (reading D's 4632.66, the 13:30
   sweep high, is 69 pips tighter), K3b the sweep high at B. The zone's P (readings A and C) is 5-190 pips wider than his
   on every trade.
4. **Targets.** His are the previous significant low: 1.15687 (the 12:45 low of the same day, 1.15684), 1.0866 (7 pips under
   the Friday low 1.0873), 4594.98 (1.0 over the 24 Aug low 4594.00). The liquidity map (readings A-D) gives a nearer level on
   K3a (4604.81, the 25 Aug low), 18 Mar (1.08805) and 11 Nov (1.15934, then 1.15468); his level is in none of the three
   maps at his minute. A fixed window (reading E, 72 candles) gets 18 Mar to 7 pips and overshoots the other two (the
   lookback reaches a deeper low from days before). What fits all three with the sweep-extreme stop is "the nearest resting
   low at least 2R away" (2.0R, 2.5R, 2.8R), which is a reading of three trades, not a rule of his; his own words give 0.7R
   and 1.4R examples as well. The target stays the open point; the fast loop will settle it with his next trades.
5. **K3b at 17:05 Amsterdam** is outside the session window the course states; on his chart's clock (UTC+1) it is 16:05.
