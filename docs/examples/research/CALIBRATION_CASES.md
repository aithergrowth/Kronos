# Calibration cases: the engine's reading next to Dorus's own calls (2026-10-01)

The code's rules match the written plan; whether the code reads a chart the way Dorus does is a separate
question. These are the first dates where his view is on record (Astra's research files) and the engine's
reading can be put next to it. Engine readings come from `python -m kronos_trader scan --at <UTC>` on the
TradingView cache with the forward-test profile (Kronos off).

## Gold, 26 August 2026 (K3 public recap, a 1-minute scalp in a 4H context)

Dorus: short, entry 4624.53, stop 4639.55, risk 15.02, target distance 29.55, R:R 1.97 (corrected drawing at
02:40). Qualified as a scalp; the academy context chart is 4H.

Engine at 13:00 UTC (price 4614.47): bias 1M bearish, 1W 50/50, 1D bullish, 4H 50/50, 1H bearish -> no trade.
POIs: 1D bearish 4584.38-4665.44 (active), 1H bearish 4629.61-4658.82 (tested), 1H bearish 4630.02-4687.12.

- **Zone: agrees.** His entry and stop sit on the engine's 1H bearish zone (4629.6 low) inside the 1D bearish zone.
- **Bias: disagrees.** The scalp combo needs 1D+4H+1H aligned; the engine reads 1D bullish and 4H 50/50, so it
  stayed flat. Dorus took the short. What his 1D and 4H bias was that day is the open question for Astra.
- **R:R: disagrees.** His 1.97 is below the coded minimum of 3. With the 1:3 rule the engine would have skipped it
  even with the bias right.

## BTC, September 2026 (K5 daily scenarios 7 Sep, K4 4H recap mid Sep, K2 weekly condition 27 Sep)

Dorus: weekly view bullish, buying beneath successive liquidity levels (purchase area circled near the 16 Sep
22:00 crosshair, 76,148), the illustrated bullish path conditional on a weekly close above about 82,815 on 27 Sep.
These are spot purchases and conditional scenarios, not funded-account trades with a stated combo.

Engine: 7 Sep 12:00 UTC: 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bearish -> no trade. 16 Sep 22:00 UTC:
1M 50/50, 1W bullish, 1D bearish, 4H bearish, 1H 50/50 -> no trade; active zones 1D bullish 68,902-78,080 and 1W
bullish 62,751-76,670 under the price of 75,976. 28 Sep 00:00 UTC: 1M 50/50, 1W bullish, 1D bullish, 4H 50/50,
1H bearish -> no trade.

- **Weekly: agrees** on all three dates (bullish).
- **Zones: agree** in kind: the engine's weekly and daily bullish zones sit exactly where he was buying in mid September.
- **Monthly reads 50/50 all month**, which removes every combination that needs the monthly; the daily and 4H flip
  between bearish and 50/50. Whether Dorus's monthly was bullish, and which combination he would cite, is the
  open question. His purchases themselves are not strategy trades, so this case calibrates bias only.
- **What the engine did trade on BTC**: three shorts, 12 to 18 August, two from a monthly bearish zone with a target
  at 49,000, while his weekly view was bullish and he was accumulating. Under his own higher-timeframe-first
  principle those shorts look wrong; the monthly reading that allowed them is the suspect.

## What this says

Zone mapping is close to his. The per-timeframe bias reading is where the code and Dorus part ways, on the
monthly above all: it reads 50/50 almost always, which both blocks trades he takes and allows trades he would
not. The next fixtures should therefore state his bias per timeframe on a date, not only his entries.

## Asked of Astra

1. K3 (26 Aug gold): his stated bias for 1D, 4H and 1H that day, and the combination he used for the scalp.
2. K5 / K4 / K2 (BTC): his stated monthly and daily bias in September, with caption timestamps.
3. From the course: how he reads a timeframe's balance view when the last gap has been violated, and when the
   liquidity view and the balance view disagree; the code answers 50/50 in both cases and that is the suspect.
