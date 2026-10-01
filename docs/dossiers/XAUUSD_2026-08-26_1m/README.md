# Gold, 26 August 2026, on 1-minute candles: the K3 example walked past the gates

Astra's step 2 (control document of 1 October): a 1-minute replay with warm history that shows the bias per timeframe,
the candidate X/B/P's, the dropped gaps, the zones and their visit status, the confirmation, and the P the stop would
take, at the two moments used before (14:00 and 15:30 UTC). The clock of Dorus's own two entries is still unverified, so
these are the same two moments as in `docs/dossiers/XAUUSD_2026-08-26/`, not his entry minutes.

Data: HistData.com XAUUSD bid, 1-minute candles (`data/histdata_1m`, built from the raw archives with the same session
calendar; the 5m to monthly files are the frozen cache's own, linked). Settings `config/dorus_pure.yaml`. Visit memory:
a warm-up replay of 5,519 one-minute steps (20 to 26 August). `--assume short` makes the engine record a refusing gate and
walk on in that direction, reporting every later refusal; nothing it reaches is a signal.

## 14:00 UTC (16:00 Amsterdam), price 4614.40

- Bias refuses: 1M bearish, 1W 50/50, 1D bullish, 4H bullish, 1H bearish.
- Walking on as short: the only *active* bearish zone is the daily zone 4584.375-4665.445 (formed 17 May, touched 21 August
  09:59). It has a confirmation, but the stop would sit on the 1H P 4658.56 (the most recent 1H balance level in the trade
  direction since the touch), 44 points above the price, and the nearest 1H sell-side liquidity (4604.8) is 9.6 points below:
  0.22R, refused.
- The two bearish 1H zones, 4629.55-4686.65 (formed 25 August 03:00) and 4629.23-4658.56 (formed 26 August 08:00), are
  "tested" with the price below them. They are not candidates: the code trades a zone only while price is inside it on the
  zone's own timeframe, and the last closed 1H candle closed below both.
- On the 1H, the structure turned bearish with a BMS through 4629.235 five 1H candles earlier (around 09:00).

## 15:30 UTC (17:30 Amsterdam), price 4616.38

- Bias refuses: 1H is now 50/50 (sell-side liquidity at 4604.8 swept, balance still bearish).
- Walking on as short: the session window is closed (after 17:00 Amsterdam); the daily zone waits for a new confirmation
  (the last closed 15m candle is not one).

## Against Dorus's chart readings (Astra's labels from the K3 video, not verified fills)

| | Entry | Stop | Target distance | R:R shown |
|---|---|---|---|---|
| first short after the correction | 4624.53 | 4639.55 | 29.55 | 1.97 |
| second short | 4623.59 | 4633.72 | 27.97 | 2.76 |

Both entries lie below the X edge (4629.23) of the code's 1H zone, and both stops lie inside that zone, below its P
(4658.56). So after the bias gate there are at least two more differences, and the bias is not the only obstacle:

1. **Which P the stop takes.** The code uses the 1H P (or the zone's own P), 44 points away; his stops are 10 to 15 points
   above his entries, a protection that only a 1m or 5m structure can give. "Stoploss altijd op een minimale 1 uur P"
   (D 13:30) says the opposite for his written plan; his gold scalps in K3 do something else, and K3 names no rule for it.
2. **Which target.** The code aims at the nearest 1H sell-side liquidity, 9.6 points away; his targets are 28 to 30 points
   away (price covered on the chart). With his stop and his target the trade is 2R to 2.8R; with the code's stop and the
   code's target it is 0.22R.
3. **Zone status.** His entries come after price left the 1H zone downward; the code's zone must still hold the price.

None of this changes a rule. What the comparison still needs from the source: the verified chart clock of the two entries,
the zone he drew (bounds and P candle), and the target price. With the clock, the same command writes the dossier at his
entry minute: `python -m kronos_trader --config config/dorus_pure.yaml decision-dossier --symbol XAUUSD --data-dir
data/histdata_1m --at "2026-08-26 HH:MM" --warmup-days 6 --assume short --kronos off --out <folder>`.

Files: one folder per moment with `README.md`, `dossier.json` (bias, zones, dropped gaps, rejections, the diagnostic
walk-through, and the setup with its stop P when one is reached) and a chart per timeframe from the 1m to the monthly.
