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
3. **Stops.** On EURUSD his stops are the sweep extreme (reading B: 1.2 pips tighter, 1.1 pip wider). On gold he protects
   more: K3a the morning high 4639.14 (reading B's 4629.82 is 97 pips tighter), K3b the sweep high at B. The zone's P
   (reading A) is 5-190 pips wider than his on every trade.
4. **Targets.** His are the previous significant low: 1.15687, 1.0866, 4594.0. The code's liquidity map gives a nearer level
   on K3a (4604.81), 18 Mar (1.08805) and 11 Nov (1.15934, then 1.15468 far below); his level is in none of the three maps.
   The target rule, not the cap, is the open point here.
5. **K3b at 17:05 Amsterdam** is outside the session window the course states; on his chart's clock (UTC+1) it is 16:05.
