# Shared workboard - Claude ⇄ Max ⇄ ChatGPT Astra 6

This file is the meeting point for the three of us. Keep it on the desktop
(it lives in the repo at `docs/ASTRA_TASKS.md`), let Astra write answers and
deliverables straight into it, commit, and Claude picks it up in the next
session. One rule: **answers replace the `> answer:` lines, nothing gets
deleted** - the decision log at the bottom is our memory.

Status legend: `[ ]` open · `[~]` in progress · `[x]` done

---


## Research status — 2026-09-30, full course-caption audit

**Partial source audit. Every question is addressed, but this is not a completed
review of every YouTube video, every academy lesson, or five complete test cases.**
This source-review update changes no runtime code. Claude’s subsequent code
recalibration is preserved in the decision log. The original questions remain.

**Focused follow-up:** [four requested source checks](DORUS_FOCUSED_AUDIT.md).
K3’s corrected drawing now supplies entry 4624.53 and stop 4639.55 at 02:40;
the final target-price label and chart timezone remain obscured. K6 confirms
the illustrated bearish gap uses wick tips, but not the full POI endpoint.
A explicitly uses a close for BS entries; the precise universal boundary and
gap-selection algorithm remain provisional.

**Restored-access update:** [priority sources D/E/F](DORUS_PRIORITY_SOURCES.md)
now have complete available Dutch-caption reviews. D/F explicitly describe POI
as liquidity to protection, which exposes a conceptual mismatch with the coded
sweep-extreme/gap-edge object pair. Exact P wick/body and invalidation predicates
remain unresolved. D independently includes M+D+4H. Complete fixtures: **0**.

Skool sign-in succeeded. Its academy is now accessible. The earlier access-block
assessment is superseded. This update adds direct inspection of the **Tradingplan**
slides and selected academy analysis charts, plus end-to-end public playback
caption review of the four accessible Loom analyses. All six visible course cards
and their 30 lesson links are inventoried; inventory is not content review. Core lessons without a
usable Dutch transcript have not received a complete spoken-content review.

YouTube’s earlier unusual-traffic challenge cleared after the user handoff.
D/E/F caption exports are now available; D’s requested chart frame still
rendered black/buffering after one player recovery attempt. Its channel displayed
approximately 2,100 videos. All 2,097 lines of A’s available Dutch automatic captions have now been
reviewed, from the opening through the final caption at 04:28:24 of the 04:28:28
video. B’s 345 timestamped captions (00:00–11:46) and C’s 1,266 timestamped
captions (00:00–47:05) have also been reviewed end-to-end. This is complete
coverage of the available retrieved caption text for A/B/C, not independent
audio verification or a full visual review of those videos. D’s 419 Dutch
caption segments (00:00–16:23), E’s 391 (00:00–14:13) and F’s 288 (00:00–10:26)
were subsequently reviewed end-to-end and independently checked. E’s initial
English export was replaced with its explicitly selected Dutch track.
Loom playback/captions work; its full transcript/download panels require a
separate sign-in. Gated transcript text is not used as evidence. Automatic captions
are not an independently checked audio transcription.

**Confidence:** high = explicit wording or written rule; medium = demonstrated
chart application; low = inference. **Not assessed** is used where no supporting
observation exists. **Not stated** means not found in the inspected material;
it never means that all Dorus material has been searched. Missing data is omitted,
not supplied from general SMC knowledge.

Short quotations retain Dutch wording. Linked titles plus timestamps identify
passages; the tables use cross-references to avoid repeating source text. These
are evidence notes, not a complete verbatim transcript.

### Source register

| ID | Primary source | Date and review scope |
|---|---|---|
| A | [Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)](https://www.youtube.com/watch?v=HRPgdK8VhMc), 4:28:28 | Published 2026-02-18. All available Dutch automatic-caption lines reviewed through 04:28:24; audio and unreadable chart frames not independently verified. |
| B | [Mijn Volledige Trading Strategie Uitleg (Stap voor Stap)](https://www.youtube.com/watch?v=xWR8M46iSW8) | Publication date unverified. All 345 available timestamped Dutch automatic captions reviewed, 00:00–11:46; no independent audio or full visual verification. |
| C | [Hoe Start Je Met Traden In 2026 (A-Z Uitleg)](https://www.youtube.com/watch?v=R07fGFejJ5w) | Publication date unverified. All 1,266 available timestamped Dutch automatic captions reviewed, 00:00–47:05; no independent audio or full visual verification. |
| D | [Mijn Winstgevende Tradingplan Waarmee Ik Elke Dag Trade](https://www.youtube.com/watch?v=81LThMAtj5o), displayed English title *My Profitable Trading Plan With Which I Trade Every Day*, 16:25 | Published 2026-05-01. All 419 Dutch automatic-caption segments reviewed through 16:23. Requested chart frame did not render. |
| E | [How to Trade Liquidity (Like a Pro)](https://www.youtube.com/watch?v=F5ciF74Uzr8), 14:15 player | Published 2026-09-02. All 391 Dutch automatic-caption segments reviewed through 14:13; English export excluded. |
| F | [How to Use Fair Value Gaps to Find Better Trades](https://www.youtube.com/watch?v=O6IgD2llrq0), 10:28 | Published 2026-09-28. All 288 Dutch automatic-caption segments reviewed through 10:26. |
| K1 | [2. De strategie leren → Tradingplan](https://www.skool.com/dorusview/classroom/1924b124?md=0eb0cc9b327e47db845b3fcfb4b64f83), 18:19 | Publication date not displayed. Written slides inspected at 02:17, 03:54, 04:30, 06:30, 06:37, 06:49 and 06:55. |
| K2 | [Analyses → Bitcoin analyse ∣ 27-09-2026](https://www.skool.com/dorusview/classroom/304766fd?md=78ef5903bc4f435997de67e79210c4dd), Loom title *Mijn Bitcoin visie en weekly kansen*, 2:57 | Lesson date 2026-09-27. Public playback captions reviewed continuously through the 02:57 end; selected monthly/weekly frames; no independent audio verification. |
| K3 | [Analyses → €8.000 verdiend binnen één uur.](https://www.skool.com/dorusview/classroom/304766fd?md=1dc24e5ce9664d918a1d6212b68d4411), Loom title *Goud scalps, liquiditeitsruns en twee shorts*, 4:05 | Chart date 2026-08-26. Public playback captions reviewed continuously through the 04:05 end; selected 4H/1m frames, including the corrected 02:40 entry/stop, distance and RR labels, independently checked; later frames through 03:20 did not resolve target-price label or timezone. No independent audio verification. |
| K4 | [Analyses → €21.000 verdiend met bitcoin](https://www.skool.com/dorusview/classroom/304766fd?md=9e375caa007041fdb4cfd1c4d89726bf), Loom title *Zo verdiende ik 21.000 euro met liquiditeit*, 2:27 | Displayed 11 days ago on 2026-09-30; exact publication timestamp unverified. Public playback captions reviewed continuously through the 02:27 end; selected daily/4H frames; no independent audio verification. |
| K5 | [Analyses → Bitcoin analyse ∣ 7-09-2026](https://www.skool.com/dorusview/classroom/304766fd?md=1262146f8aee4d35a29c63b1b6e95950), Loom title *Bitcoin koersverwachting, scenario’s en koopmomenten*, 7:45 | Date explicitly captioned at 00:03–00:08. Public playback captions reviewed through the end (player 07:46; poster 07:45); selected daily charts; no independent audio verification. |
| K6 | [2. De strategie leren → Entry & Poi](https://www.skool.com/dorusview/classroom/1924b124?md=cb63d3041eac47caa148cbf218e0dde8), player title *5-0 Entries*, 10:25 | Publication date not displayed. Selected line sketches and chart frames inspected; bearish gap at 07:30–07:31 independently checked. No complete spoken-content review. |
| K7 | [2. De strategie leren → Balance levels](https://www.skool.com/dorusview/classroom/1924b124?md=074a2908adac42c7b6c6a2d68aff4da8), 10:08 | Selected diagram frames; 03:19–03:20 lower line at first candle’s lower wick independently checked. No readable P label; no complete spoken review. |
| S1 | [EURUSD Short (DXY Long)](https://www.skool.com/dorusview/eurusd-short-dxy-long), Dorus replying to Jelle Engels | Reply Aug 19; attached student chart dated 2026-08-19. |
| S2 | [Long trade USDJPY](https://www.skool.com/dorusview/long-trade-usdjpy), Dorus replying to Jelle Engels | Reply Aug 19; student chart shows August 2026. |
| S3 | [Platform](https://www.skool.com/dorusview/platform), Dorus replying to Mees Vriends | Reply Aug 20; year not printed in the inspected comment. |
| S4 | [Verliezende trade](https://www.skool.com/dorusview/verliezende-trade), Dorus | Displayed 27d on 2026-09-30; exact publication date unverified. H1 chart inspected. |
| S5 | [€8.000 verdiend binnen één uur.](https://www.skool.com/dorusview/8000-verdiend-binnen-een-uur), public recap | Separate 1:37 Loom video, title dated 26 August 2026; frame near 00:05. K3 supplies the longer academy explanation. |

## A. Questions Claude needs answered (strategy definitions)

### Part 2 — Fifteen questions

The **Now** assumptions are the implementation described in `docs/STRATEGY.md`
and Max’s original brief; they preserve the questions as asked, rather than
asserting that every original default still matches the latest code. Claude’s
subsequent changes are in the decision log. “Unverified” does not mean “false.”
No missing rule is converted into a Dorus-attributed default.

- [~] **Q1 - Balance.** How does Dorus define *balance* on a timeframe? Is it the order block of the last break (what the code does), the equilibrium of the current range (premium/discount), or something else?
  > **Answer:** Object definition contradicted; the proposed close-through → 50/50 transition is **not stated**. Balance is the gap, while P is its originating/protecting candle. See Part 1, items 3–4.
  > **Source:** B 02:13–03:47, 05:25–05:42; A 01:32:04–01:32:19 and 01:41:49–01:42:06; D 03:05–03:41; F 00:58–01:42. Full linked titles are in the source register.
  > **Confidence:** High for explicit definitions; not assessed for the coded transition.
  > **Notes:** A discusses continued decline if P breaks. That is not the code’s automatic neutralization rule, and the gap, protector, and last opposing candle must not be conflated.

- [ ] **Q2 - Sweep without break.** A timeframe swept sell-side liquidity but has not broken structure yet. Bullish, or still 50/50?
  > **Answer:** **Not stated** for this exact case. The agreement test alone does not prove the code’s requirement to wait for a structure break.
  > **Source:** A 02:03:43–02:04:07: liquidity/balance agreement; conflict or neutrality → 50/50. Full linked titles are in the source register.
  > **Confidence:** High for the agreement test; not assessed for the mandatory break.
  > **Notes:** Neither “already bullish” nor “always wait for BOS” can be made a confirmed rule here.

- [~] **Q3 - Opposing votes.** 1M+1W+1D bullish, 4H+1H bearish. Trade the bullish bias, or wait?
  > **Answer:** The listed combination is confirmed in K1 and D. A veto from the two opposing timeframes is **not stated**. D also explicitly lists M+D+4H; see the source-variation log.
  > **Source:** K1 02:17; A 01:00:58–01:01:05 and 02:03:09–02:03:35; D 01:05–01:43. Full linked titles are in the source register.
  > **Confidence:** High for the combination; low for the exact case with two explicitly bearish opposing votes.
  > **Notes:** A says the 1H/4H are unnecessary in one existing higher-timeframe trade discussion. Their directions are not specified there. This strengthens the context but does not prove the exact hypothetical.

- [~] **Q4 - Scalp only.** With only 1D+4H+1H aligned: which POI timeframes may be used, which confirmation timeframes, and is management different (break-even, session)?
  > **Answer:** Scalp designation and the confirmation/exit tables are verified below. The code’s **4H/1H-only POI subset is not stated**.
  > **Source:** K1 02:17, 03:54, 06:37, 06:49–06:55; K3 00:39–00:43; D 01:31–01:42 and 14:56–15:17. Full linked titles are in the source register.
  > **Confidence:** High for written categories; not assessed for the subset or special session rule.
  > **Notes:** K3 explicitly qualifies its scalp context (conflict log). Do not assume that example establishes every permission for the baseline D+4H+1H branch.

- [~] **Q5 - First candle confirmation.** When is "first bullish/bearish candle" an acceptable confirmation instead of a BOS/BMS body close?
  > **Answer:** A total first-candle prohibition is contradicted. A lists a first bullish/bearish candle in a POI as an option; another example enters on the first bullish candle after a shift. BS means balance shift, not a silent substitute for BOS.
  > **Source:** A 55:18, 01:21:02–01:21:11, 01:29:29–01:31:01; K1 06:30–06:37; B 08:49–09:20; D 13:48–14:01. Full linked titles are in the source register.
  > **Confidence:** High for the named options; medium for example-specific sequencing.
  > **Notes:** Exact timeframe eligibility is **not stated**. At A 43:24–43:34 a hoped-for additional liquidity take does not occur, yet the discussion proceeds to entry. This does not prove there was no earlier sweep, but it does not support requiring every extra local sweep.

- [x] **Q6 - TP choice.** Liquidity line vs. unmitigated balance block when both exist: nearest, or always liquidity?
  > **Answer:** “Dus ik zet ten alle tijden mijn take profit op liquiditeit.”
  > **Source:** A 01:50:40; K1 06:30 and D 13:22–13:45 also support the target object. Full linked titles are in the source register.
  > **Confidence:** High: explicit personal rule and written plan.
  > **Notes:** The code’s nearest-of-liquidity-or-block rule is contradicted as a blanket attribution. B 09:23–09:58 accepts 1.3R while allowing a further target; C 35:35–36:33 prefers the illustrated 1.7R target over extending it. Which liquidity candidate wins as a deterministic rule, and its exact timeframe floor, remain unresolved.

- [ ] **Q7 - The 1-pip buffer.** Extra stop distance, sizing only, or both?
  > **Answer:** **Not stated.** No verified one-pip buffer was located in the complete available A/B/C captions.
  > **Source:** A 02:43:31–02:46:01; complete available B/C caption review. Full linked titles are in the source register.
  > **Confidence:** Not assessed for a buffer rule.
  > **Notes:** K3 02:24–02:30 describes placing the stop above protection without a fixed one-pip rule. A uses a lot-size calculator and checks the intended protective level against the execution feed. Its captioned numerical distance is ambiguous and has not been turned into a pip specification. Neither an extra stop pip nor another sizing pip is confirmed.

- [~] **Q8 - Break-even 4R vs TP 3R.** Confirm the numbers (intraday BE after 4R, swing BE after 2R, TP ≥ 3R).
  > **Answer:** 4RR intraday/scalp and 2RR swing break-even thresholds are confirmed in K1. A universal minimum 3R is contradicted by accepted examples, including A’s 0.73R, B’s 1.47R/1.3R and C’s 1.7R. D 11:01–11:34 also gives a hypothetical 60% win rate → 0.67 minimum RR; it is not his measured win rate or the project threshold.
  > **Source:** K1 06:49–06:55; A 01:43:58–01:47:06; B 05:46–05:57, 09:23–09:58; C 35:35–36:33; D 11:01–11:34 and 14:56–15:17. Full linked titles are in the source register.
  > **Confidence:** High for the written thresholds and explicitly described examples.
  > **Notes:** A connects attractive RR with his claimed win rate. These are source statements, not verified performance or a new project threshold. A fixed 3R target closes before 4R; that arithmetic is not his stated explanation for the exit table.

- [~] **Q9 - Entry style.** Market on the confirmation close, or a limit back at the break level?
  > **Answer:** Market execution is demonstrated; an exclusive market-at-confirmation-close rule is **not stated**. First-candle-after-shift entry is described separately.
  > **Source:** A 43:34–43:48, 01:21:02–01:21:11, 02:26:06–02:26:20, 02:44:30–02:46:01. Full linked titles are in the source register.
  > **Confidence:** Medium for application; not assessed for one universal order-type/timing predicate.
  > **Notes:** The execution tutorial also adjusts the protective level for the broker feed. It does not establish a mandatory limit retest or permission to delay by a fixed number of candles.

- [~] **Q10 - Sessions and candle anchoring.** Trade only London/New York? Broker day start (22:00 UTC?) for 4H/daily candles?
  > **Answer:** The all-sessions assumption is contradicted by his stated entry windows. A’s replay selects Amsterdam time, then uses 09:00–11:00 and 13:00–17:00. C instead gives 08:00–17:00 through London’s close. Broker daily/4H candle anchoring is **not stated**.
  > **Source:** A 03:54–04:15, 02:20:59–02:21:07, 02:24:03–02:24:20 and 02:30:48–02:32:02; published 2026-02-18. C 10:28–10:53; publication date unverified. Full linked titles are in the source register.
  > **Confidence:** High for the stated windows and A’s explicit replay timezone; medium for extending that clock to other examples; not assessed for broker anchoring.
  > **Notes:** A rejects a 17:00 entry and demonstrates it only as a violation to journal. C advises timezone adjustment when travelling without naming its displayed timezone in the captions. Europe/Amsterdam is not a fixed UTC offset. The differing windows must not be silently merged or assigned a chronology.

- [~] **Q11 - Prop firm.** Which firm, account size, daily loss %, max drawdown %, min trading days, news and weekend rules?
  > **Answer:** Historical source: FTMO and Funded Next are preferred; FTMO Swing is preferred; 5% daily / 10% overall loss, four minimum days, and 10%/5% phase targets are described. Funding Pips and Alpha Capital also appear. Max’s chosen contract is **not stated**.
  > **Source:** A 03:27:00–03:27:17, 03:32:00–03:33:30, 03:35:29–03:36:34, 03:43:30–03:44:03 and 03:55:36–03:56:07. Full linked titles are in the source register.
  > **Confidence:** High for historical statements; not assessed for present contractual rules.
  > **Notes:** A explicitly compares 4%/8% with 5%/10% and prefers the latter; this does not select an account for Max. Account size, phase, drawdown basis/reset time, news and weekend permissions still require the actual contract. Do not copy historical promotional prices or caps into live guards.

- [~] **Q12 - Instruments.** Which pairs / indices / metals, and the broker's pip value, lot step and spread for each?
  > **Answer:** Named or observed instruments include XAUUSD/gold, EURUSD, BTCUSD, and a GC gold-futures chart. C identifies EURUSD and gold as his two favourites, selected using his data. A explicitly describes DXY long trades, without specifying the executable product or contract. A complete allowed/avoided instrument list is **not stated**.
  > **Source:** A 56:12–56:33, 01:37:33–01:37:42, 02:40:54–02:41:45; B 06:25–06:28; C 08:20–09:20; K2–K5; S4/S5. Full linked titles are in the source register.
  > **Confidence:** High for explicit instrument mentions; medium for chart observations; not assessed for an exhaustive whitelist.
  > **Notes:** A selects OANDA for the gold replay at 02:19:08 and checks feed differences at 02:45:12–02:45:50. FOREXCOM/INDEX in academy charts are feeds, not proven execution brokers. No instrument-specific lot step, pip value, spread, or contract size for Max is verified.

- [ ] **Q13 — A second visit to the same zone.** Current assumption: first return only.
  > **Answer:** **Not stated** as a universal first-return-only or second-return permission.
  > **Source:** Complete available A/B/C captions; especially A 41:45–41:54 and 01:31:14–01:31:29. Full linked titles are in the source register.
  > **Confidence:** Not assessed for the universal rule.
  > **Notes:** A discusses price already having been in a gap and separately discusses a scale-in. K3 02:18 and 03:24–03:51 describe two shorts, the latter after liquidity and a shift. None establishes a second visit to the exact same formally defined POI after mitigation. First-visit-only remains an implementation choice.

- [ ] **Q14 — Extra indicators/models and Kronos.** Current assumption: advisory only.
  > **Answer:** FVG indicators are used. A also asks ChatGPT to calculate RR from a stated win rate. A Kronos forecast/veto rule is **not stated**.
  > **Source:** A 39:23–39:46, 01:44:15–01:45:08, 02:20:44–02:20:59; C 27:41–27:58. Full linked titles are in the source register.
  > **Confidence:** High for those explicit uses; not assessed for Kronos.
  > **Notes:** Indicator-assisted identification, arithmetic assistance, journaling, and a predictive trade veto are different uses. Advisory-only remains the project’s policy; these examples authorize no Dorus-attributed Kronos filter.

- [ ] **Q15 — Setup/approval expiry.** Current assumption: one confirmation candle (earlier brief also specified a five-minute minimum).
  > **Answer:** **Not stated** for a numerical post-confirmation approval expiry. The code’s one-candle rule and earlier five-minute minimum remain unverified.
  > **Source:** Complete available A/B/C captions; A 02:30:48–02:32:02 explicitly rejects an entry after the allowed session; 02:38:28–02:39:00 discusses readiness to execute after an alert. Full linked titles are in the source register.
  > **Confidence:** High for the session rejection; not assessed for a numerical approval timer.
  > **Notes:** A zone lifetime, an entry-signal lifetime, a session cutoff, and a human approval timer are different quantities. The session example must not be converted into a one-candle timeout. His advice to keep execution available when an alert arrives supplies no numerical expiry either.

## A2. Definitions in Dorus's own words

### Part 1 — Definitions and chart identification

| # | Term | Evidence and identification | Confidence / unresolved points |
|---|---|---|---|
| 1 | Liquidity | C 15:07: “Liquiditeit is eigenlijk het liquideren van het aantal orders.” C identifies structure highs/lows (18:21), consolidation edges (19:03), patterns (19:46), trendlines (20:31) and multiple timeframes (21:05). A also names Asia-session liquidity at 01:09:15. | E 00:20–00:25, 03:31–03:39, 05:21–06:51 and 07:29–08:17 additionally name orders/stop-losses, X, consolidation and patterns. High for named categories. Swing lengths, equal-high tolerance, previous-day/week/month hierarchy, a complete session taxonomy and internal/external definitions: **not stated** as complete algorithms. |
| 2 | Sweep | No complete wick/close/minimum-penetration definition was verified. A 46:58–48:22 distinguishes a structural break from its liquidity interpretation without supplying a wick-only algorithm. K2 00:26 is a weekly-close condition, not a universal sweep predicate. | **Not assessed** for a complete predicate, including after E’s full Dutch-caption review. A line marked X does not alone establish whether a body close beyond is permitted. |
| 3 | Balance | B 03:44–03:47: “dit gat noemen wij dus het balance level.” B’s three-candle gap (03:21–03:47); C’s wick-to-wick drawing description (27:04–27:18). K6 07:30–07:31 visually shows a bearish gap from candle 3’s upper wick to candle 1’s lower wick. | High for definition; medium for this independently checked diagram geometry. Gap is distinct from the originating candle. No deterministic active-gap selection/reset rule verified. |
| 4 | Protected zone / POI | B 05:29–05:40: “De beschermde zone is de candle die de balance level heeft gecreëerd.” K1’s POI notation is in the plan table. | High for wording. D 12:21–12:54 and F 03:00–03:36 explicitly name liquidity-to-protection, including reactions before full gap fill and deeper at protection. This conflicts conceptually with attributing the coded sweep-extreme/gap-edge pair to Dorus. Exact OHLC endpoints remain unresolved; K7’s lower-wick line has no readable P label. See the priority-source audit. Invalidating timeframe/close condition and first-return-only: **not stated** as complete rules. |
| 5 | BOS / BMS / BS | A 14:06–16:44 explicitly teaches BOS as continuation and BMS/CHoCH as reversal through the prior opposing swing. A 55:18 defines BS as balance shift; 01:29:29–01:30:22 distinguishes it from a plain structural break by the opposing balance level. C 12:14–12:18: “wij nog steeds in dezelfde trend bevinden”. C 12:37–13:02 also calls a prior-low break/reversal BOS. | High for the stated terminology, which varies across passages. A 42:52 and B 08:54 use looser BOS/BMS language when explaining balance shift. A 02:25:40–02:26:15 and 02:30:39–02:30:56 explicitly wait for a close in BS entry examples. The universal price boundary and gap-selection algorithm remain unspecified; A 01:07:49–01:08:30 also refers to the candle that caused the gap. See the focused audit. |
| 6 | Confirmation | Q5 plus the verified K1 matrix below. | High for explicit options/matrix. Close-based BS entry is explicitly demonstrated (item 5). Required independent LTF sweep and a stricter full-body-beyond predicate: **not stated** as universal requirements. A close beyond and the entire body beyond are different tests. |
| 7 | Stop / invalidation | K1 06:30: “SL ALTIJD op minimale 1H P”. B 05:25–05:46 connects protection with the origin candle in item 4. | High for wording. A stop based solely on a smaller confirmation swing is not supported as a blanket rule. Exact extra distance is **not stated**. |
| 8 | Target | Q6; K1 06:30: “TP ALTIJD op x”. B 09:23–09:45 returns to 1H for protection/target context. A 01:54:49–01:55:16 prefers more substantial high/low liquidity over nearby local liquidity in that example. | High for object; medium for application. A deterministic candidate tie-break and universal target-timeframe floor: **not stated**. |
| 9 | Other concepts | FVG geometry is used (item 3); C’s FVG indicator is in Q14. | High for FVG use. Mandatory premium/discount, equilibrium or breaker-block filters were **not found**. This is not proof of absence from all lessons. |
| 10 | Scalp / intraday / swing | Written K1 categories below; K3’s scalp qualification in the conflict log. | High for written category labels. Duration cutoffs and exact POI permissions within the scalp-only bias branch remain **not stated**. |

**New priority-source reconciliation:** [DORUS_PRIORITY_SOURCES.md](DORUS_PRIORITY_SOURCES.md) supplies the D/E/F findings, the exact coded endpoint comparison, and K7’s limited diagram observation. D adds a no-trade example and a narration inconsistency; neither produces a complete fixture.

### Verified plan table — K1, written slides

These are transcribed rule data from the academy screen. They do not resolve
questions the screen leaves unspecified.

| Section / timestamp | Verified content |
|---|---|
| Bias, 02:17 | M+W+D; W+D+4H; M+D+1H qualify. D+4H+1H is scalp-only. Other combinations fail. |
| POI, 03:54 | Consider both directions; X to b/P; frames M, W, D, 4H, 1H. |
| Entry, 06:30 | Attractive/profitable RR; one trade per funded account; 1% risk; avoid external influence. Stop/target wording is quoted in items 7–8. |
| Options, 06:30 | BS, BMS, “Eerste bullish of bearish candle”. |
| Monthly POI, 06:37 | Minimum 4H BS. |
| Weekly POI, 06:37 | Minimum 1H BS. |
| Daily POI, 06:37 | Minimum 15m BS. |
| 4H POI, 06:37 | Minimum 5m BS. |
| 1H POI, 06:37 | Minimum 1m BS. |
| Intraday/scalp, 06:49 | D/4H/1H POI; BE after 4RR. |
| Swing, 06:55 | M/W POI; BE after 2RR; no partials. |

**Confidence: high** for the visible written rules. A 55:18 explicitly
identifies BS as balance shift. The matrix must not silently be rewritten as
a plain BOS matrix. An exit group does not establish every
allowed POI/confirmation combination for a restricted bias state.

### Variations and contradictions

D (2026-05-01) explicitly includes M+D+4H at 01:09–01:13, reinforcing A; K1’s inspected written table omits it and its date remains unknown. D/F also strengthen the POI definition to liquidity-to-protection, without resolving the exact P endpoint or invalidation close. These findings do not silently alter the code.

| Issue | Sources and dates | What remains unresolved |
|---|---|---|
| Extra bias combination | A 01:42:38–01:43:07 demonstrates M+D+4H and repeats it at 02:03:18 and 02:14:00 (2026-02-18); K1 02:17’s table omits it and excludes other variants (publication date unavailable). | This is repeated and demonstrated in A, not merely one ambiguous utterance. It conflicts with the inspected K1 table; do not silently pick a version or infer chronology. |
| Countertrend scope | A 02:02:27–02:02:44 permits a possible lower-timeframe short after monthly balancing with very clear confirmation. At 02:06:58–02:07:24 he rejects a short against the formed W+D+4H bullish bias. Both are in the 2026-02-18 course. | High for the explicit statements; low for reconciling their scope. The first passage does not specify the complete bias state. Do not infer either unrestricted countertrend permission or an exception-free ban from these examples alone. |
| BOS / BMS / BS | Part 1 item 5: A dated 2026-02-18; B/C/K1 dates unavailable. | A’s introductory BOS/BMS distinction is explicit; its later balance-shift descriptions use looser labels. C also calls a reversal BOS. Keep BS separate until operational equivalence is demonstrated. |
| Session windows | Q10: A’s 09:00–17:00 and 09:00–11:00 / 13:00–17:00; C 10:28–10:53 gives 08:00–17:00. | A’s later passage narrows its earlier window. C differs in start time; publication order is unknown. Amsterdam is explicit only for A’s replay, not every recording or broker candle anchor. |
| Replay capital | C 32:07–32:16 says simulated starting balance does not matter and chooses 100K. A 02:18:29–02:18:55 requires realistic intended capital. | High for the differing instructions. Do not silently resolve the variation; C’s date is unavailable. |
| B example direction | B 09:11–09:20 describes a bullish-candle entry; 10:08–10:12 describes a downward move reaching the target. | Caption-only direction ambiguity. Require visual/audio verification before turning this example into trade expectations. |
| Scalp context | K3 00:39–00:43, chart dated 2026-08-26: “de monthly, weekly, daily keek ik minder naar.” | At 00:47 he adds “iets anders wat ik dan normaliter doe”. Special emphasis differs from the baseline’s automatic voting model. It does not specify a replacement Boolean rule. 4H context and 1m entry drawings are shown; their relationship to K1’s minimum-BS table needs resolution. |
| Gold drawing correction | K3 02:34 shows an initial position drawing. At 02:35–02:41 he extends its target and says “stoploss had ik ook iets hoger”. Chart date 2026-08-26. | High for the captioned correction; medium for the visible labels. The initial labels are superseded: corrected 02:40 entry 4624.53, stop 4639.55, target distance 29.55 and RR 1.97 are readable. Final TP axis label and chart timezone remain obscured. Neither drawing state is a verified broker fill. |
| Readiness | C 38:28–38:35: 5–10% monthly backtest; 39:42–39:53: 5% forward test. A 04:23:53–04:24:26: 1–5% for both. | Captioned thresholds differ. A is dated 2026-02-18; C date unavailable. These are stated thresholds, not independently verified results. |
| Practice-count ambiguity | A 02:49:33–02:50:06 alternates captioned three/five practice challenges; 03:47:57–03:48:05 says three consecutive challenges. | Possible speech/caption inconsistency; do not silently erase it. Audio verification is still needed. |
| Practice-route sequence | A 02:49:25–02:50:06 presents practice challenges as an alternative to the three-month demo route. The recap at 03:47:47–03:48:05 places practice challenges after forward readiness. | High for the stated routes; their required sequencing remains unresolved. Do not silently require both routes or declare either optional everywhere. |
| Win-rate context | A 01:44:06 gives 70%; 03:06:03–03:06:20 gives 50–60% while discussing challenges. | Different contexts, not proven equivalent samples. Do not use either as an audited system performance estimate. |
| Code mismatches | Q1, Q5, Q6, Q8, Q10 and Part 1 item 7. | Differences between code and teaching are not automatically contradictions between Dorus sources. |

## A3. New rules

### Part 4 — Additional rules and limits

| Topic | Evidence | Confidence / implementation limit |
|---|---|---|
| News / holidays | A 01:21:11–01:21:29, 02:09:01–02:10:11: avoid bank holidays/pre-news entries; existing trades may continue. | High. Exact blackout minutes, currency/event mapping and account exceptions **not stated**. |
| Closure | A 02:26:06: “Ik vind het wel belangrijk dat we een closure hebben.” | High for wording; medium for application. It does not establish a universal full-body-beyond test. |
| Local history | S1, Aug 19 reply: “Hou het vooral lokaal als je gaat kijken per timeframes.” | High. No numerical lookback cap. Student prices are not endorsed expectations. |
| Bias errors | S2, Aug 19 reply: “Want ik zie bij je bias nog wel een paar foutjes.” | High. The reply does not identify every erroneous label; no silent correction is made. |
| Broker | S3, Aug 20 reply: “Ik gebruik zelf Vantage.” | High for the historical comment; not current contract specifications. |
| Firm age | A 03:27:54–03:28:10 states that he will not seek funding at a firm younger than 1.5 years. | High for his historical personal selection rule. This neither verifies any firm's current age nor replaces its actual contract. |
| Loss | S4: “Dit was volgens mijn strategie een goede trade, maar toch liep hij anders dan verwacht.” | High for Dorus’s assessment. Technical reasons for this loss **not stated** in the public post. |
| Weekly condition | K2 00:26: “En dan wil ik eigenlijk wel dat hij hierboven sluit”. | High for caption wording; medium for chart application. This conditional weekly view is not an executed trade or an automatic general sweep rule. |
| Trade frequency | A 04:09:09–04:09:21 reports an average 2–8 trades/month, sometimes one or none. | High for the statement; descriptive frequency, not a maximum or minimum quota. K1’s per-account cap remains distinct. |
| Feed matching | A 02:45:12–02:46:01 checks execution-feed protection and target levels against the analysis chart. | High. A copied chart price is not automatically the correct broker price; no fixed conversion/buffer is specified. |
| Calendar scope | A 02:10:35–02:10:59 and 04:13:03–04:14:26 filters high-impact events and bank holidays for relevant currencies. | High for the practice. No numerical pre/post-news blackout is supplied. |
| Position management | A 01:48:50–01:52:45 predetermines TP; 01:57:06–01:58:02 rejects partial TP-taking; 04:03:59–04:04:14 rejects emotional BE changes. | High for the stated policy. The K1 scheduled BE rule still applies. |
| Account allocation | A 03:54:30–03:55:36 rotates account batches; 04:14:43–04:15:40 chooses accounts and risk before seeing a setup. | High. This does not provide a numerical cross-account/correlation exposure cap. |
| Correlation | A 56:12–56:33 and 01:01:05–01:01:21 uses DXY/EURUSD directional context. | High for that analysis; no formal correlation coefficient, simultaneous-pair ban, or combined-risk formula is stated. |
| Scenario / spot context | K5 01:15–01:56 describes a spot/DCA purchase with an exceptional trendline-close rationale; 02:32–03:07 explains conditional scenarios; 06:35–06:58 describes monthly technically informed purchases. | High for statements, not verified fills. These are spot accumulation context, not a funded-account monthly trade quota or a universal trendline entry rule. |
| Crypto context | K2 02:00–02:37 consults TOTAL/TOTAL2/TOTAL3 and comments on a trendline while saying he does not really focus on trendlines here. | High for captioned use. No fixed market-cap filter or trendline veto is supplied. |
| Trailing / timers | A complete trailing-stop rule and numerical setup/approval expiry are **not stated**. | Do not derive them from the descriptive account routine or Q15’s session cutoff. |

## A4. Part 5 — His process

D 15:25–15:38 independently describes the daily sequence bias → POI → entry → exit and journaling. D 13:22–13:45 repeats one trade per funded account and 1% risk. Confidence: high for the captioned process; no new numerical definition of “start small.”

| Stage | Finding | Source / confidence |
|---|---|---|
| Preparation | Calendar → account/risk → monthly-down analysis → alerts. | A 04:13:03–04:18:19; high. |
| Earlier daily routine | 08:45 start; about 15 minutes analysis; alerts at POIs, then leave the screen. | A 04:02:23–04:03:11; high for his described earlier routine, not a mandatory current timetable. |
| Instrument learning | Start with one pair; develop expertise and data before adding another. Favourite instruments are recorded in Q12. | C 08:20–09:20; high for the learning instruction, not an exhaustive instrument whitelist. |
| Replay exercise | Specific plan first; realistic account balance; gold/OANDA example; Amsterdam display clock; at least 100 trades. | A 02:12:28–02:13:27, 02:18:29–02:21:07; high. His examples use 10K for a funded-account simulation and €1K own capital. |
| Backtest progression | At least 100 trades; stated benchmark 1–5% average monthly; then forward testing. | A 02:33:57–02:34:27; high for source instructions, not verified performance. C differs in the conflict log. |
| Forward practice | Live prices with demo money; realistic sizing; journal every trade. Assessment over 2–3 months, preferably three, with stated 1–5% monthly and plan adherence. | A 02:35:43–02:37:59 and 02:47:31–02:48:52; high for explicit instruction. |
| Practice challenges | Three consecutive practice challenges in the later recap; an earlier three/five caption ambiguity remains. Earlier presented as an alternative to the three-month demo route, later placed after forward readiness. | A 02:49:25–02:50:06 and 03:47:47–03:48:05; high for the statements; count and required sequence remain unresolved as recorded in the conflict log. |
| Exercise review | Tag rule violations, including an after-17:00 entry; inspect day/time, monthly results, win rate and RR. | A 02:30:48–02:33:38; high. This is an exercise, not permission to trade outside the plan. |
| Journaling | Reasons, checklist adherence, mistakes, emotions and triggers; a winning trade can still violate the plan. | A 02:37:28–02:37:59, 04:21:13–04:22:05, 04:25:19–04:27:06; high. |
| Start small | Later examples: 10K funded / €1K own capital; maximum 1% risk. Earlier introduction also gives €100/€500/€1K possibilities. | A 10:12–10:35 and 03:30:47–03:31:33; high. These are contextual examples, not one mandatory account denomination. |
| Scaling / payouts | Review discipline before scaling; use payouts for additional accounts; take available payouts after trades close; rotate account batches. C describes roughly 60% challenge completion. | A 03:37:43–03:38:31, 03:51:30–03:52:52, 03:54:30–03:55:36; C 43:06–43:19. High for historical statements; C’s figure is neither a trade win rate nor verified performance. |
| Quiet markets | Revisit historical trades and refine backtests instead of forcing entries. | A 04:10:36–04:12:25; high. No compulsory daily trade quota. |
| Weekly timetable / sizing costs | Fixed weekly schedule, instrument-specific costs, and broker candle anchoring: **not stated**. | Complete available A/B/C caption review. Replay display timezone is addressed separately in Q10. |
| Academy journaling resource | Bibliotheek contains **Claude Journal Prompt**, 19:21, with a linked Google Drive resource. | Lesson located; substantive contents not reviewed. Automatic approval review blocked the separate potentially private Drive file pending explicit resource authorization. No workaround attempted; no Kronos rule inferred from its title. |

### Part 3 — Example files and readiness

**Five Dorus-authored chart records, two student-chart critiques and three caption
leads; zero complete regression fixtures.** The requested five fully worked
CSV/YAML pairs are still incomplete. No OHLC export was obtained. Gold has preserved intermediate states and the corrected 02:40 drawing’s entry,
stop, distances and RR. Its corrected target-price label, verified execution prices
and UTC execution time remain unresolved. A daily,
weekly or 4H chart on screen does not by itself establish the POI timeframe.

Raw academy screenshots are excluded from the PR following automatic approval
review; the sourced readings and lesson links remain. Public-post chart assets
are retained. Each example YAML has a same-name Markdown handoff. They stay under
`docs/examples/research/` so the non-recursive production loader cannot mistake
partial evidence for a passing test. No research record has an `expect` field. Gold prices are preserved under
`illustrated_position_states`, not treated as final trade expectations.
The separate [caption audit](examples/research/course_caption_audit.yaml) is a
coverage manifest, not an example fixture.

| Record | Files relative to `docs/` | Evidence / gap |
|---|---|---|
| Gold scalp / 4H context | [YAML](examples/research/xauusd_2026-08-26_public_recap.yaml) · [handoff](examples/research/xauusd_2026-08-26_public_recap.md) | K3 02:40 corrected 1m drawing: entry 4624.53, stop 4639.55, target distance 29.55, RR 1.97. Final target-price label, verified fills, POI classification and UTC timing incomplete. |
| BTC loss, H1 | [YAML](examples/research/btcusd_undated_1h_loss.yaml) · [handoff](examples/research/btcusd_undated_1h_loss.md) | Dorus’s loss assessment; year/feed/timezone and exact order labels missing. |
| BTC trade recap, 4H chart | [YAML](examples/research/btcusd_2026-09_4h_recap.yaml) · [handoff](examples/research/btcusd_2026-09_4h_recap.md) | K4 marks a purchase area. Selected candle label is not proven entry time. |
| BTC daily scenarios | [YAML](examples/research/btcusd_2026-09-07_daily_scenarios.yaml) · [handoff](examples/research/btcusd_2026-09-07_daily_scenarios.md) | K5 chart annotation, not a documented completed trade. |
| BTC monthly/weekly condition | [YAML](examples/research/btcusd_2026-09-27_weekly_condition.yaml) · [handoff](examples/research/btcusd_2026-09-27_weekly_condition.md) | K2 conditional weekly close and alert label; no execution asserted. |
| EURUSD critique | [YAML](examples/research/eurusd_2026-08-19_4h_review.yaml) · [handoff](examples/research/eurusd_2026-08-19_4h_review.md) | Student proposal; Dorus questions history relevance. |
| USDJPY critique | [YAML](examples/research/usdjpy_2026-08-19_bias_review.yaml) · [handoff](examples/research/usdjpy_2026-08-19_bias_review.md) | Student scalp claim; Dorus flags bias errors. |
| Stop example locator | [YAML](examples/research/course_stop_example.yaml) · [handoff](examples/research/course_stop_example.md) | Caption-only; not chart-verified. |
| Rejected short locator | [YAML](examples/research/course_bias_rejection.yaml) · [handoff](examples/research/course_bias_rejection.md) | Caption-only; not chart-verified. |
| Rejected session entry | [YAML](examples/research/course_session_rejection.yaml) · [handoff](examples/research/course_session_rejection.md) | Explicit 17:00 rejection and rule-violation exercise; no invented chart values. |

**Data fallback:** symbol/feed/displayed timeframes and readable date labels are
recorded individually. Where an exact historical interval or UTC conversion is
missing, that fallback is explicitly incomplete. No convenient date range has
been presented as something Dorus showed, and no surrounding candles have been
invented from one screenshot.

### Continuation queue

The four-priority follow-up is recorded in [DORUS_FOCUSED_AUDIT.md](DORUS_FOCUSED_AUDIT.md).
The priority D/E videos and additional F video now have complete available Dutch-caption reviews; see [the update](DORUS_PRIORITY_SOURCES.md). For gold, obtain an unobscured corrected target and chart timezone; for POI/BS, verify exact P bounds and the precise BS threshold. D’s requested picture still did not render.

1. A’s full available caption text is now reviewed; unreadable chart frames and
   audio remain unverified. Review remaining academy spoken content using reliable Dutch transcripts or
   authorized lesson exports; Skool sign-in itself is now resolved. The external
   journal-prompt Drive file remains blocked by automatic approval review. Coverage is tracked
   in [source_coverage.yaml](examples/research/source_coverage.yaml).
2. Resolve the K1/A combination difference and K3 scalp/confirmation context.
   Complete active-balance selection, exact POI/invalidation geometry, sweep and
   candle-close predicates before treating the definitions as detector-ready.
3. D/E/F caption review is complete; inspect their remaining diagrams/chart frames and original audio when readable. New candidate locators are in the priority-source audit. Titles and captioned price fragments are not chart evidence.
4. For each case, verify the actual POI frame, feed, timezone, complete date range,
   sweep and break candle; export real candles with the exact CSV schema in the brief.
5. Only after complete CSV/YAML pairs exist in `docs/examples/`, run
   `python -m pytest tests/trader/test_examples.py`. Document review checks are
   not strategy-validation or trading-performance tests.

## B. Deliverables Astra can build (drop the result path here)

- [~] **B1 - Annotated examples.** 5–10 real chart examples from Dorus's material in the format of `docs/examples/README.md`: `<name>.csv` (candles) + `<name>.yaml` (sweep candle, break candle, balance block, POI, entry, stop, target). They become tests automatically (`python -m pytest tests/trader/test_examples.py`).
  > path: `docs/examples/research/` — five Dorus chart records, two student critiques, three caption-only leads; zero complete CSV/YAML fixtures. See Part 3. B1 remains incomplete.
- [ ] **B2 - Prop-firm rulebook** as numbers (`config/propfirm.yaml`): daily loss, max drawdown (static/trailing), profit target, min days, allowed instruments, news rule, weekend rule, max lot.
  > path:
- [ ] **B3 - Symbol specs** for the chosen broker (`config/local.yaml` → `symbols:`): pip size, pip value per lot in account currency, lot step, min/max lot, typical spread, MT5 symbol name, TradingView symbol (`OANDA:EURUSD` style).
  > path:
- [ ] **B4 - Telegram bot.** Create the bot with @BotFather, get the chat id, and set `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` as environment variables on the desktop. Then run `python -m kronos_trader telegram-test`.
  > status:
- [ ] **B5 - Backtest review.** Read `docs/backtests/*.md` when they appear and mark trades that Dorus would *not* have taken, with the reason. This is how we calibrate the detectors.
  > notes:
- [ ] **B6 - News policy.** Which calendar events (per currency) block entries, and for how long before/after? Claude wires them into `prop_firm.news_blackout_minutes` and the TradingView economic calendar.
  > notes:
- [ ] **B7 - TradingView data pulls.** Astra can't call the MCP, but can list which symbols/timeframes to keep warm in the cache (`data/tv_cache/`). Claude pulls them in each session.
  > list:
- [ ] **B8 - Dot on GitHub.** If Astra runs as a ChatGPT Dot: connect it to the `aithergrowth/kronos` repository, work on branches named `astra/<topic>`, open pull requests for Claude to review, and keep all secrets out of its computer. It should read `docs/STRATEGY.md` and `docs/ASTRA_TASKS.md` first.
  > status:
- [ ] **B9 - IBKR paper + Telegram on the desktop.** Follow `docs/LIVE_SETUP.md` sections 1 and 2, then run `python -m kronos_trader ibkr-test` and `python -m kronos_trader telegram-test`.
  > status:

## C. What Claude did / will do

- [x] C1 - Rule set codified with tests (`kronos_trader/strategy`, `tests/trader`) - 2026-09-30
- [x] C2 - Kronos forecast indicator wired (`kronos_trader/indicators`) and verified with the real Kronos-small weights (110 MB download, CPU) - 2026-09-30
- [x] C3 - TradingView MCP adapter + CSV cache, verified against the live server tools - 2026-09-30
- [x] C4 - Paper broker, prop-firm guard, MT5 adapter skeleton, Telegram notifier
- [x] C5 - Backtester + CLI + first runs on the bundled 6-year 5-minute dataset
- [ ] C6 - Turn B1 examples into regression tests
- [ ] C7 - Forex backtests on real TradingView history (needs cached bars, see `docs/TRADINGVIEW_BRIDGE.md`)
- [x] C8 - Live loop with IBKR paper adapter, Telegram approve/skip flow and close reports (`kronos_trader/live.py`, `execution/ibkr.py`) - 2026-09-30
- [ ] C9 - Run the loop for real on the desktop (needs B9)

## D. Decision log

| Date | Decision | By |
|---|---|---|
| 2026-09-30 | Confirmation defaults to BOS/BMS body close; first-candle confirmations are a switch (`--first-candle`) until Q5 is answered. | Claude |
| 2026-09-30 | Kronos runs in *advisory* mode by default; `filter` mode exists for A/B backtests. | Claude |
| 2026-09-30 | TP policy defaults to *nearest* valid target until Q6 is answered. | Claude |
| 2026-09-30 | Guards default to 4 % daily loss / 8 % drawdown until Q11 gives the real numbers. | Claude |
| 2026-09-30 | Added a scoped primary-source audit in A/A2/A3/A4. Q1/Q6/Q8 expose baseline mismatches; unresolved rules remain open. No runtime defaults changed. | Codex/Astra |
| 2026-09-30 | Kept incomplete chart records under `docs/examples/research/`; did not fabricate OHLC or promote student/rejected setups into regression expectations. Complete academy/all-video coverage remains blocked. | Codex/Astra |
| 2026-09-30 | Academy sign-in resolved. Verified K1 plan matrix and RR units; added K2–K5 chart evidence and gold position-tool prices. All-video/all-lesson review and complete regression fixtures remain unfinished. | Codex/Astra |
| 2026-09-30 | Reviewed all available A captions through 04:28:24; clarified BOS/BMS/BS, Amsterdam replay time, session rejection, practice gates, instrument/feed context and account process. Kept full-video/academy completion false and all incomplete fixtures disabled. | Codex/Astra |
| 2026-09-30 | Expanded B/C and academy public-caption review; retained source variations and removed intermediate gold drawing prices from final trade expectations. No runtime rules changed. | Codex/Astra |
| 2026-09-30 | Code recalibrated to the audit: balance level = the gap, P = the candle that created it (B 03:44, 05:29); balance view flips when P breaks (A 01:41:49); confirmation options BS / BMS / first candle per K1 06:30, BS = close through the opposing balance level; TP on liquidity only (A 01:50:40); stop at minimum the 1H P (K1 06:30); Amsterdam entry windows (A 02:24:03); local lookbacks (S1). Wick-only sweep, 1-pip buffer and 1:3 stay as Max's rules pending his decision. | Claude |
| 2026-09-30 | M+D+4H combination kept available but off (`bias.extra_combos_enabled`) because K1's written table omits it. | Claude |
| 2026-09-30 | Focused follow-up: independently checked K3 corrected entry/stop/distance/RR and K6 wick-to-wick bearish gap; rechecked A’s explicit close-based BS examples. Full POI boundary, universal BS threshold, gold target/clock and priority-video access remain unresolved. No runtime change or completed fixture claimed. | Codex/Astra |
| 2026-09-30 | User handoff cleared YouTube verification. Reviewed all available Dutch captions for D/E/F (419/391/288 segments). D/F clarify POI starts at liquidity and can reach protection; D explicitly includes M+D+4H. Exact P endpoint/BS algorithm and complete fixtures remain unresolved; no runtime change. | Codex/Astra |
