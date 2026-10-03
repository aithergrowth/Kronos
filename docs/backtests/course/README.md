# Course evaluation runs: the second and third edition with and without 1-minute candles

Five runs of 2 October 2026 (04:17-05:10 UTC), EURUSD and XAUUSD 2023-03-01 to 2026-09-25, HistData bid candles, 5-minute
steps, 1 % risk, one account of 100,000 per run, prop-firm halt lifted (first breach of the 10 % line recorded). R1-R4 ran on
commit `7ed54e0` (the balance shift over the latest opposing gap, `allow_bms`, `stop_protection`, confirmation age under
coarser steps), R5 on `9672505` (`confirmation_tf_mode: exact`). None of them has the fixes of `9cfd67b` (search from the
latest re-entry, gaps crossed before the window, entries outside the zone); those run as R6 and R7 and follow.

| Run | Profile | Candles | Market | Trades | Win rate | Expectancy | Total | Profit factor | End equity | Deepest drawdown | 10 % line crossed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| frozen (phase 2) | second edition | 5m | EURUSD | 75 | 33 % | -0.20R | -15.0R | 0.69 | 87,006 | -16.4 % | 2026-06-02 |
| R1 | second edition | 1m | EURUSD | 172 | 28 % | -0.14R | -23.3R | 0.82 | 82,488 | -26.1 % | 2026-03-16 |
| R2 | third edition | 1m | EURUSD | 55 | 29 % | -0.20R | -10.8R | 0.72 | 90,323 | -16.9 % | 2026-04-30 |
| R4 | third edition | 5m | EURUSD | 44 | 30 % | -0.16R | -7.2R | 0.77 | 92,736 | -14.2 % | 2026-07-29 |
| R5 | third edition, table exact | 1m | EURUSD | 30 | 30 % | -0.13R | -3.9R | 0.81 | 95,819 | -11.3 % | never |
| R6 | strict: third edition, table exact, entry outside the zone, search from the re-entry, every gap a shift; stop on the zone's P | 1m | EURUSD | 227 | 35 % | -0.18R | -40.5R | 0.73 | 71,649 | -36.6 % | 2024-03-08 |
| R7 | the same, stop beyond the sweep extreme | 1m | EURUSD | 378 | 21 % | -0.36R | -137.1R | 0.55 | 34,922 | -69.4 % | 2023-05-24 |
| frozen (phase 2) | second edition | 5m | XAUUSD | 104 | 31 % | -0.11R | -11.8R | 0.83 | 88,006 | -19.0 % | 2025-07-03 |
| R3 | third edition | 1m | XAUUSD | 80 | 32 % | -0.13R | -10.4R | 0.81 | 89,499 | -17.0 % | 2026-06-08 |

R6 and R7 ran on `bfdfec8` (06:02 UTC) with the three fixes found on Dorus's own trades (`docs/dossiers/SOURCE_TRADES.md`).
R6: 200 of its 227 trades are 1m shifts on 1H zones (-35.3R); 2024 is its only positive year (+9.8R over 61 trades), 2025
-34.6R over 92. R7: 305 of 378 trades on 1H zones (-113.2R); the stop beyond the sweep extreme is hit on four trades in five.

Trades by confirmation timeframe (count, sum of R): R1 1m 113 (-11.3R), 5m 39 (-2.5R), 15m 9 (-9.0R); R2 1m 18 (-7.7R), 5m 15
(+4.9R), 15m 15 (-6.6R), 1H 6 (-0.5R); R4 5m 14 (+7.4R), 15m 24 (-11.1R), 1H 5 (-2.5R); R5 1m 28 (-1.9R), 5m 2 (-2.0R); R3 1m 27
(-12.4R), 5m 20 (-4.9R), 15m 26 (+5.5R), 1H 6 (+0.2R).

## Reading it

1. **No version is positive.** The expectancy per trade sits between -0.13R and -0.20R in every run; the rule changes change
   how many trades are taken, not how good they are.
2. **The 1-minute candles do not help the second edition** (R1 against the frozen run): the 1m confirmations add 97 trades
   on 1H zones, -11.3R together, and the account breaches the 10 % line three months earlier. With the 1m the 1H-zone trades
   are finally taken as the table says, and they lose as the 5m-confirmed ones did.
3. **The third edition halves the trades and the loss** (R2 55 trades -10.8R against R1 172 trades -23.3R; R4 44 trades -7.2R
   against the frozen 75 trades -15.0R) through BMS off and the 0.5 R:R floor letting the sweep-and-shift entries through.
   The stop on the zone's own P lowers the planned R:R and raises nothing visible in the win rate (29-30 %).
4. **The table taken as the one timeframe** (R5) takes the fewest trades (30), loses the least (-3.9R) and never crosses the
   10 % line; it is also the smallest sample, and still negative.
5. **Gold** follows EURUSD: the third edition with 1m candles loses as much per trade as the frozen second edition.

6. **The fixes that reproduce his trades multiply the losing ones.** With the search from the latest re-entry, every
   opposing gap a shift, and entries allowed just outside the zone, the engine's diagnostic entries land within a pip or two
   of his on 11 November 2025 and 18 March 2024. Run over three and a half years the same reading takes 227 trades (R6)
   or 378 (R7) instead of 30 (R5), almost all 1m shifts on 1H zones, and loses -40.5R and -137.1R. The sweep-extreme stop
   that matches his intraday stops to 0.3 pip is hit on four trades in five when applied to every shift. What separates his
   three winning examples from the hundreds of look-alikes is not in the rules the code has: which shift to take, when to
   wait, and the bias he reads from another chart (the dollar index on 11 November).

Every run in this folder is negative. The honest reading of the whole set: the mechanical rules, read as literally as his
course and his trades allow, do not carry an edge on this data; his results come from choices the rules do not express.

Files per run: `<run>.csv` (ledger with `confirmed_close_at`, `stop_p`, `stop_tf`, `stop_p_open`, `stop_p_close`,
`stop_basis`), `.equity_1H.csv`, `.equity.csv.gz`, `.provenance.json` (code identity at start), `.run.txt`, `<run>_equity.png`;
`equity_all.png`, `headline.csv`.
