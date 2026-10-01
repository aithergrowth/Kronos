# Dorus Wanders strategy - rule set and implementation spec

This document is the contract between the trader's rules and the code in
`kronos_trader/`. Section 1 is the rule set as Max gave it. Section 2 is what
Astra's source audit (`docs/ASTRA_TASKS.md`, 2026-09-30) established in Dorus's
own words. Section 3 maps every rule to the code. Section 4 lists the
interpretations the code still makes (each one a config knob). Section 5 lists
the decisions only Max can take, and section 6 what is still open.

Source IDs (A, B, C, K1-K5, S1-S5) refer to the register in `docs/ASTRA_TASKS.md`.

## 1. The rules as given (Max, 2026-09-30)

**Bias rules**
- Minimum 3/5 timeframes must match (1M, 1W, 1D, 4H, 1H)
- Valid combos: 1M+1W+1D · 1W+1D+4H · 1M+1D+1H
- 1D+4H+1H = scalp only
- All other combinations = no match, no trade
- Per timeframe: liquidity + balance align → bullish or bearish; conflicting → 50/50

**POI rules**
- Look at both sides, don't be biased
- POI = area between liquidity and balance level (protected zone)
- Map POIs on 1M, 1W, 1D, 4H, 1H

**Entry rules**
- Only enter when risk/reward is attractive
- Max 1 trade per funded account, 1% risk
- Don't let external factors influence you

**Confirmation** (BOS, BMS, or first bullish/bearish candle)
- Monthly POI → min. 4H · Weekly → min. 1H · Daily → min. 15m · 4H → min. 5m · 1H → min. 1m

**Exit rules**
- Intraday/scalp (D, 4H, 1H POI): break-even after 4R · Swing (M, W POI): break-even after 2R
- No partials · Let SL and TP run · Start small

**Additions (Max)**
- SL strictly behind the invalidation swing that created the lower-timeframe confirmation break.
- TP at the opposite high-timeframe external liquidity line or the next unmitigated higher-timeframe balance block.
- Minimum R:R 1:3. Lot sizing includes a 1-pip spread buffer.
- HTF sweep = wick pierce only, body closes back inside. LTF confirmation = full candle body close past the structural high/low.

## 2. What Dorus actually says (verified, with sources)

| Term | Dorus | Source, confidence |
|---|---|---|
| Liquidity (X) | "Liquiditeit is eigenlijk het liquideren van het aantal orders": structure highs/lows, consolidation edges, patterns, trendlines, across timeframes; Asia-session liquidity | C 15:07-21:05, A 01:09:15 - high for the categories |
| Balance level (b) | "dit gat noemen wij dus het balance level" - the **gap** between candle 1 and candle 3 of a displacement, drawn **wick to wick** | B 03:21-03:47, C 27:04-27:18, D 03:05, F 00:58; K6 07:30 (diagram) - high |
| Protected zone (P) | "De beschermde zone is de candle die de balance level heeft gecreëerd" - the candle that created the gap; "P is the candle that caused the gap" | B 05:29-05:40, D 12:21-12:54 - high |
| POI | "X to b/P": the area runs from the liquidity the displacement took (X, "begint ten alle tijden bij het punt van liquiditeit") through the gap to P; price may react just inside, midway, after filling the gap or deeper at P; interest ends below P ("wanneer die onder de P komt"); both directions; on M, W, D, 4H, 1H | K1 03:54, D 12:21-12:54, F 03:00-03:36 - high (wick/body of the P edge unresolved) |
| Bias per timeframe | liquidity and balance agree → direction; conflict **or neutrality** → 50/50 | A 02:03:43-02:04:07 - high |
| Bias combinations | the trading-plan video lists M+W+D, **M+D+4H**, W+D+4H, M+D+1H; D+4H+1H scalp only; others fail. The K1 slide omits M+D+4H | D 01:05-01:43, A 01:42:38 - high; K1 02:17 - conflict recorded |
| P breaks | continued decline (continuation) when P breaks | A 01:32:04, 01:41:49 - high for the statement |
| BOS / BMS / BS | BOS = continuation, BMS/CHoCH = reversal through the prior opposing swing; **BS = balance shift**, distinguished from a plain structural break by overcoming the opposing balance level; entries wait for a **close** above the gap (A 02:25:40) or above the candle that caused it (A 01:07:49) | A 14:06-16:44, 55:18, 01:29:29-01:30:22, D 14:03-14:38 - high for the concept, threshold provisional |
| Confirmation options | "BS, BMS, Eerste bullish of bearish candle"; minimum timeframe table Monthly 4H, Weekly 1H, Daily 15m, 4H 5m, 1H 1m, each written as "minimum … BS" | K1 06:30-06:37 - high |
| "Closure" | "Ik vind het wel belangrijk dat we een closure hebben" - a candle close matters | A 02:26:06 - high |
| Stop | "SL ALTIJD op minimale 1H P" - always at minimum the 1H protected zone | K1 06:30 - high |
| Target | "Dus ik zet ten alle tijden mijn take profit op liquiditeit"; "TP ALTIJD op x"; prefers substantial highs/lows over nearby local liquidity | A 01:50:40, K1 06:30, A 01:54:49 - high |
| R:R | accepted examples at 0.73R, 1.47R, 1.3R, 1.7R; "attractive RR" linked to win rate: a hypothetical 60 % win rate gives a 0.67 minimum | A 01:43:58-01:47:06, B, C, D 11:01-11:34 - high |
| Break-even | 4RR intraday/scalp, 2RR swing; no partials; no emotional BE changes; TP predetermined | K1 06:49-06:55, A 01:48:50-01:58:02, 04:03:59 - high |
| Sessions | entries 09:00-11:00 and 13:00-17:00 Amsterdam (A); 08:00-17:00 (C); a 17:00 entry is rejected | A 02:24:03, 02:30:48-02:32:02; C 10:28 - high, variant recorded |
| News / holidays | avoid bank holidays and pre-news entries; open trades may continue | A 01:21:11, 02:09:01-02:10:59 - high, no minutes stated |
| Local analysis | "Hou het vooral lokaal als je gaat kijken per timeframes" | S1 - high, no numeric cap |
| Risk / accounts | 1 % risk, one trade per funded account; FTMO / FundedNext preferred historically (5 %/10 %, four days); broker Vantage (historical) | K1 06:30, A 03:27-03:56, S3 - high for the statements |
| Frequency | 2-8 trades a month on average, sometimes none | A 04:09:09 - descriptive |
| Not found | wick-only sweep algorithm, 1-pip buffer, first-visit-only rule, a Kronos-style veto, an approval timer, premium/discount or breaker filters | complete A/B/C caption review |

## 3. Rule → code map

| Rule | Where | How |
|---|---|---|
| Swings, liquidity levels | `strategy/structure.py` | fractal swings; swing high = buy-side liquidity, swing low = sell-side; equal levels stack (`equal_level_tolerance_pct`). Session and trendline liquidity: not yet (see §6) |
| Sweep (wick only) | `structure.py` (`Sweep`) | wick beyond the level with the body back inside; a close through is a break instead. Max's rule; Dorus states no algorithm |
| BOS / BMS | `structure.py` (`StructureBreak`) | a candle **close** through the level ("closure"); `full_body_break` for the stricter reading |
| Balance level and P | `structure.py` (`Gap`) | gap between candle 1 and 3 (`min_gap_fraction` of the median range); P = candle 2; candle 1 kept as order block; `mitigated` when price re-enters the gap, `violated` when a close passes P's far extreme |
| Bias per timeframe | `strategy/bias.py` | liquidity view = last sweep/break; balance view = direction of the last balance level, flipped when its P breaks (`balance_violation`); agreement → direction, conflict or neutrality → 50/50 |
| 3/5 rule + combos | `bias.py`, `BiasParams` | K1's table; M+D+4H available behind `extra_combos_enabled` |
| POI = X to b/P | `strategy/poi.py` | `poi_mode="liquidity_to_protection"`: for every balance level, X = the level the displacement closed through (a break between P and `poi_break_window` candles after candle 3); zone = P's far extreme → max(X, gap edge); one zone per impulse (deepest P); invalidated by a close beyond P. Legacy `sweep_to_gap` kept |
| Confirmation options | `strategy/confirmation.py` | **BS**: body close through the opposing balance level that drove price into the zone (`bs_threshold`: the gap edge, or the far edge of the candle that caused it); **BMS/BOS**: body close through the LTF swing; **first candle** in the POI direction; earliest wins, ties BS > BMS > BOS > first candle |
| Confirmation table | `confirmation.py`, `min_confirmation_tf` | Monthly ≥ 4H … 1H ≥ 1m, below the POI timeframe |
| SL at minimum 1H P | `strategy/risk.py`, `engine._protection_level` | stop behind the most recent 1H balance level (P) formed since the touch, else the POI's own P, minus `sl_offset_pips`; `stop_basis="confirmation"` restores Max's LTF-swing rule |
| TP on liquidity | `risk.py: find_take_profit` | nearest resting opposite liquidity on the POI timeframe, then higher timeframes (`tp_policy="liquidity"`); legacy policies keep order blocks |
| R:R ≥ min | `risk.py: build_setup` | `min_rr` (3.0 = Max's rule; see §5) |
| 1 % risk, buffer | `risk.py: size_position` | risk distance = stop distance + `spread_buffer_pips`; lots floored to `lot_step` |
| Sessions | `engine.in_session`, `SessionParams` | no new entries outside 09:00-11:00 / 13:00-17:00 Amsterdam on weekdays; open trades run on |
| Local analysis | `StructureParams.lookback_by_timeframe` | 60 monthly, 104 weekly, 250 daily, 300 4H/1H candles |
| Break-even 4R/2R, no partials | `strategy/exits.py`, brokers, `live.py` | scheduled by POI timeframe; nothing else touches the stop |
| One trade, prop-firm limits | `execution/risk_guard.py` | 1 open trade, daily loss, drawdown, news blackout, spacing |
| Kronos | `indicators/`, `engine.py` | advisory by default; `filter` exists for A/B tests only (Q14: no Dorus veto exists) |

## 4. Interpretations still made by the code (knobs)

| # | Interpretation | Knob |
|---|---|---|
| A1 | A sweep older than 80 candles no longer drives the liquidity view | `bias.liquidity_lookback` |
| A2 | The balance view uses the **last** balance level of a timeframe; gaps smaller than 20 % of the median candle range are ignored | `structure.min_gap_fraction` |
| A3 | "P breaks" = a close beyond P's far extreme → continuation bias (A); `neutral` available | `bias.balance_violation` |
| A4 | Opposing votes do not veto a valid combo (Q3 not stated) | - |
| A5 | "Scalp only" = 4H and 1H zones (Q4 subset not stated) | `confirmation.scalp_poi_timeframes` |
| A6 | The zone's P edge is P's far wick extreme (wick vs body not stated); the X edge is the broken level, extended to the gap edge when the level sits inside the gap | `structure.poi_mode` |
| A7 | The displacement must close through X no later than 3 candles after candle 3; a prior sweep is recorded but not required | `structure.poi_break_window` |
| A8 | Only the first return into a POI is traded (Q13 not stated) | `confirmation.allow_retest` |
| A9 | The confirmation must close within 1.5 zone-heights beyond the zone | `confirmation.max_extension_zones` |
| A10 | BS = close through the far edge of the most recent opposing gap formed up to 60 candles before the touch | `confirmation.opposing_gap_lookback` |
| A11 | Entry = market at the close of the confirmation candle (Q9: demonstrated, not stated as the only way) | - |
| A12 | The stop sits 1 pip beyond P | `risk.sl_offset_pips` |
| A13 | Break-even = exactly entry | `exits.breakeven_offset_pips` |
| A14 | Session windows follow A (09-11, 13-17 Amsterdam); C's 08-17 is the alternative | `session.windows` |
| A15 | A continuation break (BOS) on the LTF is accepted although the plan lists BS/BMS/first candle | `confirmation.accept_bos` |
| A16 | BS threshold = the far edge of the opposing gap; the alternative "above the candle that caused the gap" is selectable | `confirmation.bs_threshold` |

## 5. Decisions for Max (the code follows your rule until you change it)

- **Minimum R:R.** Your rule says 1:3. Dorus's own accepted trades run 0.7R-1.7R and his plan says "attractive/profitable RR" without a number. At 1:3 the system will pass on most of the trades he takes. `risk.min_rr`.
- **1-pip buffer.** Not found in his material. Kept as your rule. `risk.spread_buffer_pips`.
- **Wick-only sweep.** Not found as an algorithm. Kept as your rule.
- **Session variant.** A's 09-11 / 13-17 or C's 08-17. `session.windows`.
- **Combination M+D+4H.** Now **on**: two dated videos state it (A, D); only the plan slide omits it. `bias.extra_combos_enabled`.
- **Prop firm.** FTMO / FundedNext were his historical preference; the guards need the real contract numbers.

## 6. Still open (needs recordings, transcripts or Dorus)

- The exact P boundary (wick or body) and the P candle on his diagrams: K6/K7 show the gap wick to wick but carry no P label.
- The BS threshold: gap edge versus the candle that caused the gap, and which opposing gap counts.
- The gold scalp of 26 August: corrected entry 4624.53, stop 4639.55, target distance 29.55, RR 1.97 are readable; the final target label, the chart timezone and the candles are not.
- Session-based liquidity (Asia highs/lows) and trendline liquidity as levels: not implemented.
- Whether a lower-timeframe sweep is required before the BS; which liquidity candidate wins as the target when several exist.
- Numerical news blackout, first-visit rule, approval timer: not stated.
- Zero complete chart fixtures so far (`docs/examples/research/` holds the partial records). The XAUUSD 2026-08-26 scalp, BTC 2026-09 charts and the EURUSD/USDJPY student reviews are the candidates once candles and readable prices exist.
