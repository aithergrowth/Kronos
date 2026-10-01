# Dorus Wanders strategy — source evidence and implementation contract

Updated 2026-10-01. **This is a partial source audit, not a fully verified automated Dorus strategy.** Section 1 preserves Max's baseline. Section 2 distinguishes source evidence from implementation choices; sections 3–6 describe the code and unresolved decisions. [ASTRA_TASKS.md](ASTRA_TASKS.md) retains the detailed workboard and historical decisions. [Source coverage](examples/research/source_coverage.yaml) records what has and has not been inspected.

All available Dutch automatic captions from nine YouTube videos A–I have been reviewed, including the four-hour course A. **Audio has not been independently checked.** Academy K1/K6/K7 were checked through selected slides/frames; this is not a complete spoken review of the academy or every video on the channel. Exact excerpts below match captions or screen text, with that medium explicitly labeled. They must not be represented as audio-certified speech. Long transcripts and raw academy recordings are not reproduced.

High confidence means explicit in the identified caption or written slide, medium means illustrated application, low means inference. “Not stated” means not found in the inspected material, not proven absent from all Dorus content. A literal match to automatic captions can still contain a transcription error.

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

## 2. Source verification

### Source register

| ID | Title / original source | Published; inspected evidence |
|---|---|---|
| A | [Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)](https://www.youtube.com/watch?v=HRPgdK8VhMc) | 2026-02-18; all 2,097 available caption lines, last at 04:28:24 / 04:28:28. Rechecked in full this pass. |
| B | [Mijn Volledige Trading Strategie Uitleg (Stap voor Stap)](https://www.youtube.com/watch?v=xWR8M46iSW8) | Date unverified; 345 caption segments through 11:46; prior full review, excerpt recheck this pass. |
| C | [Hoe Start Je Met Traden In 2026 (A-Z Uitleg)](https://www.youtube.com/watch?v=R07fGFejJ5w) | Date unverified; 1,266 caption segments through 47:05; prior full review, excerpt recheck this pass. |
| D | [Mijn Winstgevende Tradingplan Waarmee Ik Elke Dag Trade](https://www.youtube.com/watch?v=81LThMAtj5o) | 2026-05-01; 419 caption segments through 16:23. |
| E | [How to Trade Liquidity (Like a Pro)](https://www.youtube.com/watch?v=F5ciF74Uzr8) | 2026-09-02; 391 Dutch caption segments through 14:13. |
| F | [How to Use Fair Value Gaps to Find Better Trades](https://www.youtube.com/watch?v=O6IgD2llrq0) | 2026-09-28; 288 Dutch caption segments through 10:26. |
| G | [De Kracht van HTF Context in LTF Trades](https://www.youtube.com/watch?v=6NLVf8P-xP8) | 2025-08-20; 375 caption segments through 12:31. |
| H | [Hoe Je Entries 5x Beter Worden Als Je Dít Ene Ding Begrijpt](https://www.youtube.com/watch?v=oe0tBQ47r3M) | 2025-08-12; 414 caption segments through 13:37. |
| I | [Zo Gebruik Je Claude Om Winstgevend Te Worden Met Traden](https://www.youtube.com/watch?v=FZPN1jEGWH4) | 2026-05-19; newly reviewed 515 Dutch caption segments through 19:19 / 19:20. Displayed English title later: How to Use Claude to Become Profitable with Trading. |
| K1 | [Academy → Tradingplan](https://www.skool.com/dorusview/classroom/1924b124?md=0eb0cc9b327e47db845b3fcfb4b64f83) | Date undisplayed; selected written slides, freshly rechecked at 02:18, 03:53, 06:28, 06:38, 06:53. |
| K6 | [Academy → Entry & Poi](https://www.skool.com/dorusview/classroom/1924b124?md=cb63d3041eac47caa148cbf218e0dde8) | Date undisplayed; selected diagrams including 07:31; no readable captions. |
| K7 | [Academy → Balance levels](https://www.skool.com/dorusview/classroom/1924b124?md=074a2908adac42c7b6c6a2d68aff4da8) | Date undisplayed; selected diagrams including 02:29 and 03:19; no readable captions. |

K2–K5 analysis videos and S1–S5 posts retain their separate links, dates and evidence limitations in [the workboard source register](ASTRA_TASKS.md#source-register). D–H were re-read end-to-end this pass. Caption hashes and coverage are in the manifest. Publication dates are not trade dates.

### Exact Dutch excerpts — canonical quotation location

These short excerpts are the quotation bank for this revision. Explanations elsewhere are paraphrases or implementation analysis. K1 is **written text**, not a spoken transcript. Caption spelling is preserved, including H1's apparent “beish” error. Adjacent caption segments are joined with a space; no words are silently repaired.

| Quote ID | Exact excerpt | Source / timestamp | Evidence / confidence |
|---|---|---|---|
| A1 | “Dus ik zet ten alle tijden mijn take profit op liquiditeit.” | A 01:50:40 | Automatic captions; high for wording in captions |
| A2 | “Ik vind het wel belangrijk dat we een closure hebben.” | A 02:26:06 | Automatic captions; high |
| B1 | “dit gat noemen wij dus het balance level.” | B 03:44–03:47 | Automatic captions; high |
| B2 | “De beschermde zone is de candle die de balance level heeft gecreëerd.” | B 05:29–05:34 | Automatic captions; high |
| C1 | “Liquiditeit is eigenlijk het liquideren van het aantal orders.” | C 15:07–15:10 | Automatic captions; high |
| D1 | “wanneer die onder de P komt” | D 12:42–12:45 | Automatic captions; high; bullish example |
| D2 | “de P is de candle die dit gat heeft veroorzaakt.” | D 12:45–12:48 | Automatic captions; high |
| E1 | “naar orders en naar stoplosses die ergens op de chart liggen.” | E 00:22–00:25 | Automatic captions; high |
| F1 | “Dat noemen we het balance level.” | F 01:34 | Automatic captions; high |
| F2 | “begint ten alle tijden bij het punt van liquiditeit” | F 03:07–03:09 | Automatic captions; high |
| G1 | “na de shift ga ik altijd bij de eerste beste bullish candle” | G 10:49–10:53 | Automatic captions; high, example-specific sequence |
| G2 | “niet 1 minuut voor nieuws traden” | G 11:13–11:16 | Automatic captions; high, not a complete news schedule |
| H1 | “de eerste beste bullish of beish candle” | H 08:14–08:16 | Automatic captions; high; apparent caption error retained |
| H2 | “Dat hij daarna sterk genoeg is om door het balance level te breken” | H 07:28–07:33 | Automatic captions; high |
| I1 | “uiteindelijk wil je AI niet voor je laten traden” | I 00:10–00:12 | Automatic captions; high |
| I2 | “We gaan dus een volledig journal programma maken” | I 02:02–02:04 | Automatic captions; high |
| K1a | “Een POI is het gebied tussen je X en b / P” | K1 03:53 | Written slide; high |
| K1b | “SL ALTIJD op minimale 1H P zolang het RR winstgevend is” | K1 06:28 | Written slide; high |

### Part 1 — Definitions and chart identification

| Concept | What the inspected source supports | Source / confidence / unresolved detail |
|---|---|---|
| Liquidity | Orders/stops associated with highs/lows; C covers structure, ranges, patterns and trendlines. | C 15:07–21:05; E 00:22–00:45, 03:31–05:13. High concept; exhaustive previous-day/week/month/session hierarchy and internal/external algorithm **not stated**. |
| Sweep | Taking liquidity is discussed; a universal minimum wick penetration and mandatory wick-only/re-entry predicate are **not stated**. | E 03:31–05:13; A 01:09:15. Do not promote Max's predicate to a quotation. |
| Balance and P | Balance is a gap; P is its originating/protecting candle, not automatically the last opposing order block. K6 illustrates a bearish gap bounded by flanking wick tips. | B1/B2, D2, F 01:00–01:42: high concepts. K6 07:31: medium geometry. **P's exact candle index and wick/body endpoints remain unresolved.** |
| POI | Liquidity to balance/protection; below P ends interest in D's bullish example. | K1a, D 12:21–12:54, F 03:00–03:36: high. Neither this nor the gap drawing proves a universal sweep-extreme→gap-bottom zone, invalidation close/timeframe or first-return-only rule. |
| BOS / BMS / BS | Introductory BOS=continuation and BMS=reversal; BS overcomes opposing balance, beyond a plain swing break. Terminology varies in examples. | A 14:06–16:44; C 12:37–13:02 also calls a reversal BOS; D 14:03–14:38, H2. High conceptual evidence; BS's exact selected gap and boundary unresolved. |
| Confirmation | BS, BMS and first-directional-candle alternatives appear. H ties alternatives to the plan; G describes first bullish candle after a shift. | D 13:48–14:01, H 08:10–08:38, G1: high. Universal first-candle activation/prior-sweep rule **not stated**. A2 supports a close in its example, not an entire-body-beyond predicate. |
| Stop and target | Minimum H1 P stop and liquidity target, subject to profitable RR. | K1b; D 13:29–13:37; A1. High. LTF invalidation swing is Max's addition; numeric buffer and nearest-target tie-break remain unconfirmed. |
| Other concepts | The gap is associated with FVG terminology. This does not establish generic SMC filters. | F 01:00–01:42; H 09:44–10:05: high. Premium/discount, equilibrium and breaker entry filters **not stated** in the inspected set. |
| Trade style | Exit groups distinguish D/4H/H1 POIs from M/W POIs. | K1 06:38–06:53, D 14:56–15:17: high. Duration alone is not established as the formal classification. |

### Confirmation and management mapping

The earlier K1 06:37 written matrix records M→minimum 4H, W→minimum 1H, D→minimum 15m, 4H→minimum 5m, H1→minimum 1m. This pass rechecked entry options, **not every row of that matrix**. K6 03:31 independently shows 4H→5m and H1→1m. Implementation accepts eligible confirmation timeframes below the POI timeframe; precise upper-limit behavior is an implementation choice.

Fresh K1 06:38/06:53 and D 14:56–15:17 corroborate BE after **4R for D/4H/H1 POIs**, **2R for M/W POIs**, and no partials. High for written/captioned rules. The fixed **minimum 3R** remains Max's constraint: B 05:46–05:57, 09:23–09:58 and C 35:35–36:33 contain accepted sub-3R examples. Those examples do not establish a frequency distribution.

### Current repository forward profile

Concurrent commit `a2a29aa12c0284ead7fea356717b51a921d27f8e` changes the defaults to **Kronos off, 09:00–17:00 Amsterdam, first-candle confirmation off**, plus a morning briefing and POI-touch alerts. These are retained as project choices. G's after-shift example does not cancel H's alternative-method passage; disabling the option is not a newly proven universal Dorus rule. The ±30-minute news window and 4%/8% loss guards are configuration policies, not verification of Max's current prop contract. Historical benchmark profiles are pinned separately in the replay script.

### Part 2 — The fifteen questions

“Now” refers to Max's original brief, not necessarily today's changed defaults. Full historical answers remain in workboard section A.

| # | Answer / does Dorus agree with the original assumption? | Source / confidence | Notes for code |
|---|---|---|---|
| 1 | **Object definition contradicted:** balance is gap, P is protector. Close-through→50/50 **not stated**. | B1/B2, D2; high concept | Last-gap selection and state transition require explicit implementation assumptions. |
| 2 | Exact sweep-without-break case **not stated**. Agreement/uncertainty rule alone does not mandate BOS. | D 02:13–02:42, 09:21–09:43; high general rule, exact case not assessed | Neither automatic bullish nor mandatory BOS can be source-certified. |
| 3 | M+W+D is listed; exact two-opposing-votes veto **not stated**. | K1 02:18; high combo, low inference for hypothetical | Current no-veto choice remains provisional. |
| 4 | D+4H+H1 is scalp; **4H/H1-only POI subset not stated**. Use documented exit groups above. | D 01:31–01:42; K1 02:18, 06:38; high categories | Special session or subset permission unresolved. |
| 5 | Blanket first-candle prohibition contradicted. H's alternative and G's after-shift example differ in scope. | H1 at 08:10–08:38, G1; high | Neither unconditional candle-only entry nor universal prior-BS requirement is established. |
| 6 | Liquidity is the stated target object; nearest block/liquidity arbitration **not stated**. | A1, D 13:33–13:37; high | Current nearest-level and timeframe priority are code choices. |
| 7 | One-pip stop/sizing buffer **not stated**. | Reviewed A–I/K1; not assessed | Applying it twice is Max's/current-code choice, not a sourced Dorus instruction. |
| 8 | **4R/2R supported.** Universal minimum 3R not supported by cited sub-3R examples. | Mapping above; high | A 3R target closes before a 4R trigger; code behavior need not imply a source contradiction. |
| 9 | Exclusive market-at-confirmation-close versus limit order **not stated**. | G 10:18–10:55, H 07:24–07:39; medium example sequence | A historical confirmation price is not a valid later market fill. |
| 10 | All-session assumption contradicted by stated hours. A:09–11/13–17 Amsterdam; C:08–17; H:09–17 with quieter midday. **Broker candle anchor not stated.** | A 02:24:03, 02:30:48–02:32:02; C 10:28; H 04:23–04:46. High, differing scopes | Do not infer 22UTC or midnightUTC from those entry hours. |
| 11 | 1% and one funded-account trade supported. Historical firm discussion is not current contract verification. | D 13:22–13:29; A **03:27:00–03:56:07**; high historical statement | Firm/account loss, news and weekend terms must match Max's actual contract;4%/8% placeholders unverified. |
| 12 | Gold/BTC examples; I describes focusing on gold and reserving EURUSD for A++ setups after reviewing his journal. No universal instrument whitelist/specs. | E 08:38–11:29; I 12:38–13:11,16:23–16:36; high captioned statements | Symbol mapping, lot sizes, spreads and pip values require MT5 broker data. |
| 13 | Universal same-zone second-return permission/prohibition **not stated**. | H 09:03–09:07,10:32–10:49; exact case not assessed | Scale-in/another BS does not prove identical-zone revisit policy. |
| 14 | I discourages AI trading/predicting decisions and demonstrates AI journal review. **No Kronos-specific advisory/veto rule stated.** | I1/I2,00:10–00:17,01:19–02:05; high | The earlier advisory policy and current off-by-default forward profile are project choices, not Dorus endorsements of Kronos. |
| 15 | Numeric post-confirmation approval lifetime **not stated**. | G/H reviewed; not assessed | One-candle/minimum-five-minute expiry is an engineering policy. |

### Part 4 — Additional rules and source variations

- **Combination disagreement:** K1 02:18 lists M+W+D, W+D+4H, M+D+H1, plus scalp D+4H+H1. D 01:05–01:43 (2026-05-01) also lists **M+D+4H**. K1's date is unavailable; do not invent a chronology that resolves this.
- **News:** G2 excludes a one-minute-pre-news entry (2025-08-20), while G 11:13–11:24 allows an existing plan-compliant trade to continue. A complete pre/post blackout or event severity table is **not stated**.
- **Local analysis:** Dorus's written S1 reply favors local timeframe analysis; see workboard S1. No numeric lookback follows from it.
- **Risk context:** A's challenge-risk discussion at 03:45:56–03:46:11 is conditional and differs from its beginner maximum 1% guidance at 03:30:47–03:31:33. Neither silently changes the K1/D plan. Its one-trade-per-day discussion at 03:36:41–03:37:11 is a personal checklist example, not an established universal daily cap.
- **No universal additions established:** a correlation veto, trailing-stop algorithm, fixed expiry or entire-body-beyond BS cannot be filled in from general SMC knowledge.

### Part 5 — Process, practice and AI journal

D 15:25–15:38 orders the workflow as bias→POI→entry→exit with journaling. E 08:19–08:32 and F 09:34–09:53 emphasize repeated chart practice. A 02:33:57–02:34:27 calls for 100 historical trades; 02:35:43–02:37:59 / 02:47:31–02:48:52 describes 2–3 demo months; those are learning checkpoints, not this bot's achieved validation. Its qualitative monthly return examples are not promised returns.

I 03:55–05:13 proposes MT5 journal import with a manual alternative. I 15:50–16:18 reviews setup components, emotion and commissions. The same demonstration has import, starting-capital and RR corrections (08:34–12:03;14:31–14:54;16:47–17:31); its displayed performance is **not independently audited**. AI accountability/journaling is distinct from a predictive trade filter. A fixed day/week review timetable or universally quantified “start small” rule is **not established** beyond the separately scoped risk statements.

### Part 3 — Example files and remaining source blockers

See [example inventory](examples/README.md), [retrieval requests](examples/research/RETRIEVAL_REQUESTS.md), and [coverage](examples/research/source_coverage.yaml). **Zero complete source-annotated fixtures.** Seven candle exports exist; the gold entry export is 15m instead of requested 1m. Real market backtests are separate from Dorus chart-example fixtures.

K3's corrected first drawing at 02:40 and second drawing at 03:48 supply selected visible prices; final target labels and chart clock remain obscured. Do not calculate an unseen label from RR and represent it as observed. The K6 gap drawing does not resolve P's full boundary; K7's lower line is not labeled P. Fresh [academy checks](examples/research/skool_verification_2026-10-01.md) document these limits. Source A's requested replay frame remained black after recovery; all caption text was still available from the saved export.

## 3. Rule → code map

| Rule | Where | How |
|---|---|---|
| Swings, liquidity levels | `strategy/structure.py` | fractal swings; swing high = buy-side liquidity, swing low = sell-side; equal levels stack (`equal_level_tolerance_pct`). Session and trendline liquidity: not yet (see §6) |
| Sweep (wick only) | `structure.py` (`Sweep`) | wick beyond the level with the body back inside; a close through is a break instead. Max's rule; no complete algorithm found in the reviewed sources |
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
| Sessions | `engine.in_session`, `SessionParams` | current forward-profile default permits 09:00–17:00 Amsterdam on weekdays; split hours remain configurable; open trades run on |
| News | `engine`, `NewsCalendar`, `NewsParams` | Configurable blackout; the default 30 minutes before/after is a project choice, not Dorus's stated window. Open trades run on. Missing/stale calendar coverage is not a verified no-news period. |
| Local analysis | `StructureParams.lookback_by_timeframe` | 60 monthly, 104 weekly, 250 daily, 300 4H/1H candles |
| Break-even 4R/2R, no partials | `strategy/exits.py`, brokers, `live.py` | scheduled by POI timeframe; the scheduled automatic exit policy; runtime correctness is tested separately |
| One trade, prop-firm limits | `execution/risk_guard.py` | 1 open trade, daily loss, drawdown, news blackout, spacing |
| Kronos | `indicators/`, `engine.py` | off by default for the current forward profile; advisory/filter remain available (Q14: no Kronos-specific policy found); unavailable forecasts reject in filter mode |

## 4. Interpretations still made by the code (not all have config knobs)

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
| A11 | Strategy reference entry = confirmation close; backtest execution must use the currently available price and recompute size/RR (exclusive order style unconfirmed) | - |
| A12 | The stop sits 1 pip beyond P | `risk.sl_offset_pips` |
| A13 | Break-even = exactly entry | `exits.breakeven_offset_pips` |
| A14 | Current forward profile uses 09:00–17:00 Amsterdam; A's split windows and C's 08:00–17:00 remain source variants | `session.windows` |
| A15 | A continuation break (BOS) on the LTF is accepted although the plan lists BS/BMS/first candle | `confirmation.accept_bos` |
| A16 | BS threshold = the far edge of the opposing gap; the alternative "above the candle that caused the gap" is selectable | `confirmation.bs_threshold` |

Additional unconfirmed choices: P=candle 2; which gap is active; X/displacement association; deepest-P zone merging; first-candle eligibility; earliest-confirmation and tie priorities; latest H1 P/fallback selection; nearest-liquidity/timeframe priority; closed-only use of native candles. These are model assumptions to validate against examples, not fully sourced Dorus definitions.

## 5. Decisions for Max (the code follows your rule until you change it)

- **Minimum R:R.** Your rule says 1:3. The cited accepted examples include 0.73R, 1.47R, 1.3R and 1.7R and his plan says "attractive/profitable RR" without a number. At 1:3 the system excludes the cited accepted sub-3R examples; their share of all his trades is unknown. `risk.min_rr`.
- **1-pip buffer.** Not found in the reviewed material. Kept as your rule. `risk.spread_buffer_pips`.
- **Wick-only sweep.** Not found as an algorithm. Kept as your rule.
- **Session variant.** A's 09-11 / 13-17 or C's 08-17. `session.windows`.
- **Combination M+D+4H.** Now **on**: two dated videos state it (A, D); only the plan slide omits it. `bias.extra_combos_enabled`.
- **Prop firm.** FTMO / FundedNext were his historical preference; the guards need the real contract numbers.

## 6. Still open (needs recordings, transcripts or Dorus)

- The exact P boundary (wick or body) and the P candle on his diagrams: K6 shows the local bearish gap wick to wick; K7 supplies a rough schematic and an unlabeled lower outer line, not proof of P.
- The BS threshold: gap edge versus the candle that caused the gap, and which opposing gap counts.
- The gold scalp of 26 August: corrected entry 4624.53, stop 4639.55, target distance 29.55, RR 1.97 are readable; the final target label and chart timezone remain unresolved; a 15m candle substitute exists, not the requested 1m.
- Session-based liquidity (Asia highs/lows) and trendline liquidity as levels: not implemented.
- Whether a lower-timeframe sweep is required before the BS; which liquidity candidate wins as the target when several exist.
- Complete news blackout schedule, first-visit rule and approval timer: not stated in reviewed material; G specifically excludes one minute before news.
- Zero complete chart fixtures so far (`docs/examples/research/` holds the partial records). The XAUUSD 2026-08-26 scalp, BTC 2026-09 charts and the EURUSD/USDJPY student reviews are the candidates once candles and readable prices exist.


## 7. Repo and backtest readiness

See [the independent backtest audit](backtests/verification_2026-10-01/README.md) for pinned source/data, baseline reproduction, simulator corrections and model/connection limits. Unit-test success, source fidelity and profitable out-of-sample performance are separate questions. MT5 supplies candles in Max's current stack; TradingView cache data does not verify live MT5 synchronization. Neither cached backtests nor a fake forecaster demonstrate trained Kronos predictive value.
