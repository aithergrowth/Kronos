# Calibration cases: the engine's reading next to Dorus's own calls (2026-10-01)

These are provisional comparisons, not complete source-verified trade fixtures. Several coded rules remain
unresolved in STRATEGY.md. The source chart's clock and exact contemporaneous timeframe biases are not
verified; the UTC scan times below are engineering comparison points, not established Dorus entry times. Engine readings come from `python -m kronos_trader scan --at <UTC>` on the
TradingView cache with the forward-test profile (Kronos off).

## Gold, 26 August 2026 (K3 public recap, a 1-minute scalp in a 4H context)

Dorus: short, entry 4624.53, stop 4639.55, risk 15.02, target distance 29.55, R:R 1.97 (corrected drawing at
02:40). Qualified as a scalp; the academy context chart is 4H.

Engine at 13:00 UTC (price 4614.47): bias 1M bearish, 1W 50/50, 1D bullish, 4H 50/50, 1H bearish -> no trade.
POIs: 1D bearish 4584.38-4665.44 (active), 1H bearish 4629.61-4658.82 (tested), 1H bearish 4630.02-4687.12.

- **Zone: unverified.** The stated entry 4624.53 is below the stated 1H zone low 4629.61; the stop is inside it. Both are inside the listed daily zone, which alone does not establish identical zone selection.
- **Bias: unresolved.** The scalp combo needs 1D+4H+1H aligned; the engine reads 1D bullish and 4H 50/50, so it
  stayed flat. Dorus took the short. What his 1D and 4H bias was that day is the open question for Astra.
- **R:R: code/source discrepancy.** His 1.97 is below the coded minimum of 3. With the 1:3 rule the engine would have skipped it
  even with the bias right.

## BTC, September 2026 (K5 daily scenarios 7 Sep, K4 4H recap mid Sep, K2 weekly condition 27 Sep)

Dorus: weekly view bullish, buying beneath successive liquidity levels (purchase area circled near the 16 Sep
22:00 crosshair, 76,148), the illustrated bullish path conditional on a weekly close above about 82,815 on 27 Sep.
These are spot purchases and conditional scenarios, not funded-account trades with a stated combo.

Engine: 7 Sep 12:00 UTC: 1M 50/50, 1W bullish, 1D 50/50, 4H bearish, 1H bearish -> no trade. 16 Sep 22:00 UTC:
1M 50/50, 1W bullish, 1D bearish, 4H bearish, 1H 50/50 -> no trade; active zones 1D bullish 68,902-78,080 and 1W
bullish 62,751-76,670 under the price of 75,976. 28 Sep 00:00 UTC: 1M 50/50, 1W bullish, 1D bullish, 4H 50/50,
1H bearish -> no trade.

- **Weekly: direction is consistent with the reported September bullish context.** Exact same-time agreement remains unverified.
- **Zones: overlap the reported purchase region.** This is insufficient to establish identical boundaries, candle selection or strategy eligibility.
- **Monthly reads 50/50 at these three scan times**, which removes every combination that needs the monthly; the daily and 4H flip
  between bearish and 50/50. Whether Dorus's monthly was bullish, and which combination he would cite, is the
  open question. His purchases themselves are not strategy trades, so this case calibrates bias only.
- **What the engine did trade on BTC**: three shorts, 12 to 18 August, two from a monthly bearish zone with a target
  at 49,000. The cited Dorus context is from September; it does not establish his August bias.
  These shorts cannot be classified as inconsistent with his method from these sources alone.

## What this says

These observations identify calibration questions; they do not establish that zone mapping matches Dorus
or that monthly bias is the cause of a discrepancy. A useful fixture must contain the chart clock, feed,
contemporaneous bias per timeframe and the final corrected trade drawing. Complete fixtures remain zero.

## Asked of Astra

1. K3 (26 Aug gold): his stated bias for 1D, 4H and 1H that day, and the combination he used for the scalp.
2. K5 / K4 / K2 (BTC): his stated monthly and daily bias in September, with caption timestamps.
3. From the course: how he reads a timeframe's balance view when the last gap has been violated, and when the
   liquidity view and the balance view disagree; the code answers 50/50 in both cases; compare each state with explicit source evidence.
