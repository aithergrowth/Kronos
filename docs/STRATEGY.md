# Dorus Wanders strategy - rule set and implementation spec

This document is the contract between the trader's rules and the code in
`kronos_trader/`. Section 1 is the rule set exactly as given. Section 2 maps
every rule to the code that enforces it. Section 3 lists the interpretations
the code had to make (each one is a config knob). Section 4 holds the open
questions that need a human answer before live trading.

## 1. The rules (source of truth)

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
- SL / TP: to be decided (superseded by the addition below)
- Don't let external factors influence you

**Confirmation** (BOS, BMS, or first bullish/bearish candle)
- Monthly POI → min. 4H
- Weekly POI → min. 1H
- Daily POI → min. 15m
- 4H POI → min. 5m
- 1H POI → min. 1m

**Exit rules**
- Intraday/scalp (D, 4H, 1H POI): break-even after 4R
- Swing (M, W POI): break-even after 2R
- No partials
- Let SL and TP run
- Start small

**Entry rules (addition)**
- SL placement: strictly behind the invalidation swing high/low that created the lower-timeframe confirmation break.
- TP placement: directly at the opposite high-timeframe external liquidity sweep line or the next unmitigated higher-timeframe balance block / order block.
- Mathematical filter: minimum R:R of 1:3 to authorise execution.
- Spread buffer: lot sizing factors in a 1-pip protection buffer.

**Confirmation (addition - wicks vs. closes)**
- High-timeframe sweep: wick pierce only; the body must close back inside the range.
- Lower-timeframe confirmation (BOS/BMS): full candle body close past the structural high/low. Wicks do not count.

## 2. Rule → code map

| Rule | Where | How |
|---|---|---|
| Swing highs/lows | `strategy/structure.py: find_swings` | fractal: `swing_left` lower bars on the left, `swing_right` not-higher bars on the right; a swing is only *known* `swing_right` candles later (no look-ahead) |
| Liquidity levels | `structure.py: analyze_structure` | every swing high = buy-side liquidity (BSL), every swing low = sell-side liquidity (SSL); equal highs/lows within `equal_level_tolerance_pct` stack as `touches` |
| HTF sweep = wick only | `structure.py` (`Sweep`) | wick beyond the level **and** `max(open, close)` (or min) back inside → `Sweep`; a close through the level is a break instead |
| BOS/BMS = body close | `structure.py` (`StructureBreak`) | `close` beyond the level (option `full_body_break` demands the whole body beyond); BOS continues the last break direction, BMS reverses it |
| Balance block | `structure.py` (`BalanceBlock`) | last opposing candle before the impulse that produced the break; `mitigated` when price trades back into it, `violated` when price closes through it |
| Per-timeframe bias | `strategy/bias.py: timeframe_bias` | liquidity view = most recent sweep/break implication; balance view = direction of the last break unless its block was violated; aligned → bias, else 50/50 |
| 3/5 rule + combos | `bias.py: combine_biases`, `config.BiasParams` | full combos `1M+1W+1D`, `1W+1D+4H`, `1M+1D+1H`; `1D+4H+1H` = scalp; a superset of a combo counts; anything else = no trade |
| POI both sides | `strategy/poi.py: map_pois` | every sweep followed (within `max_bars_sweep_to_break`) by a break in the implied direction forms a POI: zone from the sweep wick to the balance block edge; mapped on 1M/1W/1D/4H/1H regardless of bias |
| Protected zone | `poi.py: update_poi_status` | a close (on the POI's own timeframe) beyond the sweep wick = `INVALIDATED`; `ACTIVE` when price is inside now |
| Confirmation table | `strategy/confirmation.py: allowed_confirmation_timeframes` | Monthly→≥4H, Weekly→≥1H, Daily→≥15m, 4H→≥5m, 1H→≥1m (and below the POI timeframe) |
| Confirmation types | `confirmation.py: find_confirmation` | BOS/BMS body close in the POI direction after the touch; optional first bullish/bearish candle (`allow_first_candle`) |
| SL behind invalidation swing | `strategy/risk.py: compute_stop` | the break's `origin_price` (the extreme the impulse started from) ∓ `sl_offset_pips` |
| TP at opposite liquidity / unmitigated balance | `risk.py: find_take_profit` | candidates on the POI timeframe **and higher**: resting (unswept, unbroken) opposite liquidity, or unmitigated opposite balance blocks; policy `nearest` / `liquidity_first` / `balance_first` |
| R:R ≥ 1:3 | `risk.py: build_setup` | reward / risk distance, `min_rr = 3.0` |
| 1 % risk + 1-pip buffer | `risk.py: size_position` | risk distance = |entry − SL| + `spread_buffer_pips`; lots = 1 % equity / (pips × pip value), floored to `lot_step` |
| Max 1 trade per account | `execution/risk_guard.py` | `max_open_trades = 1`, plus daily-loss / drawdown guards below the prop-firm limits |
| Break-even 4R / 2R | `strategy/exits.py`, `execution/paper.py`, `live.py` | trigger by POI timeframe (M/W → 2R, D/4H/1H → 4R); stop moves to entry; no partials |
| Let SL and TP run | `execution/paper.py: on_candle` | only stop, target or break-even close a position |
| Don't let external factors influence you | design | the engine is deterministic; news is used only as an optional *blackout* (`news_blackout_minutes`), never as a signal |
| Kronos as an extra indicator | `indicators/kronos_forecast.py`, `strategy/engine.py` | sampled forecast paths on the confirmation timeframe → direction + confidence; `advisory` (reported) or `filter` (rejects conflicting setups) |

## 3. Interpretations and assumptions (config knobs)

| # | Assumption | Knob |
|---|---|---|
| A1 | *Liquidity view* = what the most recent liquidity event implies: a sell-side sweep → bullish, a buy-side sweep → bearish, a body-close break → its own direction. Older than `liquidity_lookback` candles → 50/50. | `bias.liquidity_lookback` |
| A2 | *Balance view* = direction of the last structure break, void once its balance block is closed through. | – |
| A3 | Both views must be non-neutral and equal to give a bias; one missing view = 50/50. | – |
| A4 | Opposing votes do not veto: 3 bullish + 2 bearish with a valid combo = bullish. The decision reports `conflicting` timeframes. | – |
| A5 | "Scalp only" restricts POIs to 4H and 1H. | `confirmation.scalp_poi_timeframes` |
| A6 | POI zone = sweep wick → balance-block far edge (full candle range; `block_body_only` uses the body). | `structure.block_body_only` |
| A7 | A sweep only forms a POI if the break follows within 40 candles and no opposite break happens in between. | `structure.max_bars_sweep_to_break` |
| A8 | Only the first return into a POI is traded. | `confirmation.allow_retest` |
| A9 | The confirmation candle must close within 1.5 zone-heights beyond the POI (otherwise the move is already gone). | `confirmation.max_extension_zones` |
| A10 | First-candle confirmations are **off** by default: the addition defines confirmation as a body-close break and, when enabled, the first candle always fires before any BOS (it dominated the first backtest). | `confirmation.allow_first_candle` |
| A11 | "Strictly behind" = 1 pip beyond the invalidation extreme; the 1-pip spread buffer is added on top for sizing and for R:R. | `risk.sl_offset_pips`, `risk.spread_buffer_pips`, `risk.rr_includes_buffer` |
| A12 | TP = the *nearest* valid target (liquidity or balance) at or above the POI timeframe; a balance block is targeted at its near edge. | `risk.tp_policy` |
| A13 | Entry = market at the close of the confirmation candle. | – |
| A14 | Break-even = exactly entry (no offset). | `exits.breakeven_offset_pips` |
| A15 | Structure is evaluated on the last 400 closed candles per timeframe. | `structure.lookback` |
| A16 | Prop-firm guards default to 4 % daily loss and 8 % drawdown (inside the usual 5 % / 10 %). | `prop_firm.*` |

## 4. Open questions (answers go in docs/ASTRA_TASKS.md)

- **Q1 (A1/A2)** How exactly does Dorus define *balance* on a timeframe? The code uses the last structure break and its order block. If balance means "price is in discount/premium relative to the range", the balance view needs a premium/discount rule.
- **Q2 (A3)** With a sweep but no break yet on a timeframe, is the bias 50/50 (current) or does the sweep alone set it?
- **Q3 (A4)** Should two timeframes voting the *opposite* way block a trade even when a valid combo agrees?
- **Q4 (A5)** What does "scalp only" allow: which POI timeframes, which confirmation timeframes, any different exit rule?
- **Q5 (A10)** When is the "first bullish/bearish candle" confirmation allowed? Only on certain POI timeframes? Only after a sweep on the confirmation timeframe?
- **Q6 (A12)** When both an opposite liquidity line and an unmitigated balance block are available, which is the TP? Nearest, or always liquidity?
- **Q7 (A11)** Is the 1-pip buffer meant as extra stop distance (stop placed 1 pip further) or only as a sizing buffer (current: both, via two knobs)?
- **Q8** Break-even after 4R while the minimum TP is 3R means break-even rarely triggers for intraday trades. Intended, or should it be 4R *target* and break-even earlier?
- **Q9 (A13)** Market at the confirmation close, or a limit order back at the break level / the POI edge?
- **Q10** Session filter: only London/New York hours? Weekend / rollover handling for 4H candles (broker day start = 22:00 UTC?) - set `--session-offset`.
- **Q11** Which prop firm and account size? (daily loss, max drawdown, min trading days, news rules, weekend holding).
- **Q12** Which pairs / instruments? Pip values in `config/example.yaml` must be verified per broker.

## 5. What is deliberately not implemented yet

- Premium/discount (equilibrium) logic, fair value gaps, breaker blocks - not in the rule set.
- Partial take-profits - explicitly forbidden.
- Trailing stops beyond the single break-even move.
- Any discretionary "external factor".
