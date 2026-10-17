# Reading the bot's view the way Dorus reads a chart

Max, 8 October 2026: "kunnen we iets daaraan doen? Bijv jou laten kijken op de analyses op basis van hoe Dorus zou
denken?" Two checks use this page: the morning review (a scheduled Claude session, `scripts/morning_review.py`) and
the per-trade check in the live bot. The reviewer gets the engine's view (bias per timeframe, zones, breaks, the setup
if there is one, the refusals) and the charts, and answers as Dorus would read the same chart. Both are advice: they
never place a trade, and nothing here changes a profile. His words, with timestamps, are in `docs/STRATEGY.md`
section 2.

## The questions, in order

1. **Where is the liquidity?** Structure highs and lows, equal highs and lows, consolidation edges, the Asia range,
   on every timeframe from month to hour. What has been taken (swept or broken), and what still lies there as a
   target? His target is always liquidity ("TP altijd op x"), preferably a substantial high or low.
2. **The bias, top down.** Per timeframe: liquidity and balance agree -> that direction; conflict or neutrality ->
   50/50. The valid combinations are in the profiles (`bias.full_combos`; D+4H+1H is a scalp). Then ask whether the
   lower timeframes agree, or whether one just broke the other way.
3. **The zone: demand or supply.** X (the liquidity the move took) -> the balance level (the gap, wick to wick) -> P
   (the candle that made the gap). Is this the first return? How old is it? The bot trades a zone only when price
   comes back within 24 h of it forming (later touches lost in every market, 7 October), and the summary says which
   zones are still tradable by age. A broken P means continuation the other way.
4. **How does price arrive?** A slow, overlapping approach into the zone is a test. A fresh displacement through
   the lower-timeframe structure into the zone (a break of structure against the trade on the 1H or 4H, large
   candles, the summary's day move several average 1H ranges against the trade) means the zone is being run through,
   not tested: wait for the structure to turn first.
5. **Consolidation?** Overlapping candles, sweeps on both sides, no clean displacement, little net progress (the
   summary's efficiency near 0): the edges of the range are liquidity. Dorus waits for an edge to be swept and a
   balance shift; he does not trade from the middle.
6. **The confirmation.** A balance shift on the lower timeframe (a close through the last opposite gap; BOS and BMS
   count too), with a closure. The entry near the zone, not long after the move has gone; the stop behind the
   shift's invalidation, the target on liquidity, the R:R attractive for the market's win rate.
7. **News and the session.** No new entry just before high-impact news or on a bank holiday; entries 09:00-11:00 and
   13:00-17:00 Amsterdam.

## The verdict, per market or per trade

- ✅ **eens**: the bot's view and Dorus's reading agree; name what would trigger a trade today.
- ⚠️ **let op**: one point argues against it (for example the 1H just broke against the bias, or the only zone is old);
  name it.
- ❌ **niet**: Dorus would not take the bot's side today; one line why.

Write for Max: Dutch, short, no jargon beyond Dorus's own words (liquiditeit, demand, supply, balance level, balance
shift, BOS).

## The case that started this

7 October 2026, BTC: long at 84,249 in a 1H demand zone formed 30 September and first touched 160 hours later, right
after a 1H displacement of about 1,100 points down that broke the 1H structure (BOS through 83,841). Month, week and
day were bullish, which allowed it; the entry came 640 points above the zone. Stopped out. By the questions: the
zone was old (3), it was run through rather than tested (4), and the entry came far from the zone (6) -> ❌. The 24 h
touch rule in the profiles since that evening refuses it.

## The two checks, and how to switch the per-trade one on

- **Morning review**: a scheduled Claude session every weekday at 08:35 Amsterdam fetches the candles (TradingView for
  EURUSD, gold and NAS100, Bitstamp for BTC), runs `scripts/morning_review.py build` and `dossiers`, reads the summary
  and the charts, and sends Max the verdict per market.
- **Per-trade check** (`kronos_trader/notify/dorus_check.py`, `live.dorus_check: advisory` in the four live profiles):
  after an entry, or a limit order placed, the bot draws the 4H, 1H and confirmation charts and sends them with the
  setup to the Anthropic Messages API. The answer goes to Telegram (`🧭 Dorus-check EURUSD long: ✅ eens - ...`) and to
  `dorus_checks.csv` next to the journal. The call runs beside the loop, so the entry never waits, and a failed call
  changes nothing. It stays off until the computer that runs the bot has `ANTHROPIC_API_KEY` and `DORUS_CHECK_MODEL`
  set, for the FTMO windows in `scripts\ftmo_local.bat` (not in git); the key never goes into a file of this
  repository or into a chat.
- Neither check blocks a trade. Whether the per-trade verdict may ever veto one is decided on `dorus_checks.csv`
  against the results: only when the ❌ trades lose clearly more than the ✅ ones over enough trades.
