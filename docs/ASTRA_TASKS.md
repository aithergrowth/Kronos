# Shared workboard - Claude ⇄ Max ⇄ ChatGPT Astra 6

This file is the meeting point for the three of us. Keep it on the desktop
(it lives in the repo at `docs/ASTRA_TASKS.md`), let Astra write answers and
deliverables straight into it, commit, and Claude picks it up in the next
session. One rule: **answers replace the `> answer:` lines, nothing gets
deleted** - the decision log at the bottom is our memory.

Status legend: `[ ]` open · `[~]` in progress · `[x]` done

---


## Research status — 2026-09-30

**Partial evidence audit; not a completed review of every video or the academy.**
This updates definitions and records unresolved decisions. It does not change the
Python strategy, broker configuration, or execution settings. The original
questions and decision log are retained below.

Reviewed material: targeted passages in retrieved Dutch automatic captions for
three public videos (A–C), public Skool posts/comments, and four chart attachments.
Automatic captions can misrecognize technical terms and numbers. Short quotations
below preserve the retrieved wording; they have not received an independent
audio transcription check. Unreadable on-screen values are not reconstructed.

Further YouTube navigation encountered an unusual-traffic challenge on this
browser after one reload. The channel header displayed approximately 2,100 videos;
the inventory is **not complete**. Skool's six Classroom cards were visible, but
lessons required Level 1/Standard access and Analyses required Standard. No locked
lesson was reviewed. Public contribution pages 1–6 were inspected; those pages
also contain other members' posts on which Dorus merely commented.

**Confidence:** high = explicitly stated in the inspected source; medium = shown
in an example; low = inference. “Not assessed” means no supporting observation,
not a weakly supported guess. “Not stated” always means **not found in the
inspected material**, never that Dorus has never said it elsewhere. An access
restriction is recorded as “not accessible.”

The most consequential answers are Q1, Q5, Q6 and Q8. The confirmation-timeframe
matrix, exact zone bounds, neutralization rules, and several timing rules remain
unverified. Do not turn a missing answer into a Dorus-attributed default.

### Source register

| ID | Primary source | Date / inspection limit |
|---|---|---|
| A | [Hoe Start Je Met Traden in 2026 (Volledige 4-Uur Beginnerscursus)](https://www.youtube.com/watch?v=HRPgdK8VhMc), DorusView, 4:28:28 | Published 2026-02-18. Retrieved captions inspected; chart/plan slides were not readable in the available video player. |
| B | [Mijn Volledige Trading Strategie Uitleg (Stap voor Stap)](https://www.youtube.com/watch?v=xWR8M46iSW8), DorusView | Retrieved captions; exact publication date not verified. Do not infer it from the title or a relative age. |
| C | [Hoe Start Je Met Traden In 2026 (A-Z Uitleg)](https://www.youtube.com/watch?v=R07fGFejJ5w), DorusView | Retrieved captions; exact publication date not verified. |
| S1 | [EURUSD Short (DXY Long)](https://www.skool.com/dorusview/eurusd-short-dxy-long), Dorus's reply to Jelle Engels | Reply displayed Aug 19; attached chart identifies 2026-08-19. The chart and proposed trade are Jelle's. |
| S2 | [Long trade USDJPY](https://www.skool.com/dorusview/long-trade-usdjpy), Dorus's reply to Jelle Engels | Reply displayed Aug 19; attachment shows August 2026. The chart and entry claim are Jelle's. |
| S3 | [Platform](https://www.skool.com/dorusview/platform), Dorus's reply to Mees Vriends | Reply displayed Aug 20; year not printed in the inspected comment. |
| S4 | [Verliezende trade](https://www.skool.com/dorusview/verliezende-trade), Dorus Wanders | Displayed “27d” on 2026-09-30; exact publication timestamp not obtained. BTCUSD H1 attachment inspected. |
| S5 | [€8.000 verdiend binnen één uur.](https://www.skool.com/dorusview/8000-verdiend-binnen-een-uur), Dorus Wanders | Public Loom recap, title dated 26 August 2026; frame near 00:05 inspected. |
| S6 | [Classroom](https://www.skool.com/dorusview/classroom) | Access status inspected 2026-09-30. Course descriptions are not lesson evidence. |

Timestamps below identify the beginning of the relevant passage. The source
register supplies the full video titles. Facts are stated once and cross-referenced
between parts to keep the audit short and quotations limited.

## A. Questions Claude needs answered (strategy definitions)

### Part 2 — Fifteen questions

The code runs today with the interpretations listed in `docs/STRATEGY.md`
section 3. These questions decide whether those interpretations are right.
Short answers are fine; a chart screenshot description or a worked example is
even better.

- [~] **Q1 - Balance.** How does Dorus define *balance* on a timeframe? Is it the order block of the last break (what the code does), the equilibrium of the current range (premium/discount), or something else?
  > **Answer:** Object definition contradicted: see Part 1, items 3–4. The close-through → 50/50 transition is **not stated**.
  > **Source:** B, [2:13–3:47](https://www.youtube.com/watch?v=xWR8M46iSW8&t=133s), [5:25–5:42](https://www.youtube.com/watch?v=xWR8M46iSW8&t=325s); A, [1:32:04–1:32:19](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=5524s).
  > **Confidence:** High for the object distinction; not assessed for the proposed state transition.
  > **Notes:** Do not conflate the gap, its origin/protector candle, and a last-opposing-candle order block. Which gap determines the current balance vote, and exactly what invalidates that vote, still need evidence.

- [ ] **Q2 - Sweep without break.** A timeframe swept sell-side liquidity but has not broken structure yet. Bullish, or still 50/50?
  > **Answer:** The exact sweep-without-break case is **not stated**. Liquidity and balance must agree; a conflicting or neutral component yields 50/50.
  > **Source:** A, [2:03:43–2:04:07](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=7423s).
  > **Confidence:** High for the two-component test; not assessed for a mandatory structure break.
  > **Notes:** The code currently derives one component from a break. That dependency is the unverified step; the general agreement test does not establish it.

- [~] **Q3 - Opposing votes.** 1M+1W+1D bullish, 4H+1H bearish. Trade the bullish bias, or wait?
  > **Answer:** MWD qualifies. An explicit opposite-vote veto is **not stated**.
  > **Source:** A, [2:13:43–2:14:16](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8023s).
  > **Confidence:** High for the listed combination; low for extending it to the exact two-opposing-votes case.
  > **Notes:** The current superset/no-veto behavior is plausible but not fully confirmed. The complete on-screen combination table still needs inspection; see Part 4.

- [~] **Q4 - Scalp only.** With only 1D+4H+1H aligned: which POI timeframes may be used, which confirmation timeframes, and is management different (break-even, session)?
  > **Answer:** D+4H+1H is scalp-only. Daily/4H/1H POIs are grouped under intraday/scalp exits.
  > **Source:** A, [2:14:08–2:15:39](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8048s).
  > **Confidence:** High for those spoken statements; not assessed for the exact permitted POI/confirmation matrix.
  > **Notes:** An exit category is not proof that every category member is permitted with the scalp-only bias combination. The 4H/1H-only restriction is unverified. All five minimum-confirmation mappings in the baseline still need the slide at 2:15:13–2:15:26. See Q8 and Q10 for management/timing evidence.

- [~] **Q5 - First candle confirmation.** When is "first bullish/bearish candle" an acceptable confirmation instead of a BOS/BMS body close?
  > **Answer:** B shows the first bullish candle **after a balance shift**. A also presents first-candle entry as an alternative.
  > **Source:** B, [8:49–9:20](https://www.youtube.com/watch?v=xWR8M46iSW8&t=529s); A, [1:30:31–1:31:01](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=5431s).
  > **Confidence:** High for the stated alternatives; medium for their application in the example.
  > **Notes:** These are distinct contexts. Neither a universal first-candle trigger nor the code’s complete prohibition is established. Exact eligible timeframes and a compulsory separate lower-timeframe sweep are not stated.

- [x] **Q6 - TP choice.** Liquidity line vs. unmitigated balance block when both exist: nearest, or always liquidity?
  > **Answer:** “Dus ik zet ten alle tijden mijn take profit op liquiditeit.”
  > **Source:** A, [1:50:40](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=6640s).
  > **Confidence:** High: explicit personal rule in this source.
  > **Notes:** This contradicts treating “nearest of liquidity or balance block” as his confirmed rule. The exact algorithm selecting between several liquidity candidates is still unresolved. This is a source-specific answer, not a claim about every later lesson.

- [ ] **Q7 - The 1-pip buffer.** Extra stop distance, sizing only, or both?
  > **Answer:** **Not stated.** No verified one-pip strategy buffer was located.
  > **Source:** Targeted searches of A–C captions; relevant sizing passage A, [2:43:31–2:44:41](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=9811s).
  > **Confidence:** Not assessed.
  > **Notes:** Neither one extra pip on the stop nor another in sizing is confirmed. Distinguish price placement, actual spread, commission, and sizing reserve. The numerical sizing demonstration needs chart verification before it can resolve this question.

- [~] **Q8 - Break-even 4R vs TP 3R.** Confirm the numbers (intraday BE after 4R, swing BE after 2R, TP ≥ 3R).
  > **Answer:** Spoken break-even thresholds: 4 intraday/scalp, 2 swing; no partials. The R unit needs slide verification. B accepts an example at 1.47 R.
  > **Source:** A, [2:15:31–2:15:39](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8131s); B, [5:46–5:57](https://www.youtube.com/watch?v=xWR8M46iSW8&t=346s).
  > **Confidence:** High for the spoken numbers and B’s example; not assessed for independently reading the R unit on the plan.
  > **Notes:** The universal minimum 3R assumption is contradicted. Mathematically, a fixed 3R target closes a trade before a 4R break-even trigger can activate; that is a consequence of the baseline, not Dorus’s explanation. Frequency cannot be concluded without target-distribution data.

- [~] **Q9 - Entry style.** Market on the confirmation close, or a limit back at the break level?
  > **Answer:** A market-order example exists. An exclusive market-at-confirmation-close rule is **not stated**.
  > **Source:** A, [43:34–43:48](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=2614s); B, [9:11–9:20](https://www.youtube.com/watch?v=xWR8M46iSW8&t=551s).
  > **Confidence:** Medium for the example; not assessed for a universal execution rule.
  > **Notes:** See Q5 and Part 4’s closure passage. Neither a mandatory retest limit nor an “always market at this exact candle close” rule is fully established.

- [~] **Q10 - Sessions and candle anchoring.** Trade only London/New York? Broker day start (22:00 UTC?) for 4H/daily candles?
  > **Answer:** 09:00–17:00 initially; later 09:00–11:00 and 13:00–17:00. Timezone and candle anchoring: **not stated**.
  > **Source:** A, [3:54–4:15](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=234s), [2:24:03–2:24:20](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8643s).
  > **Confidence:** High for the spoken windows; not assessed for UTC/DST conversion or broker bar alignment.
  > **Notes:** The second passage narrows the first within the same 2026-02-18 video. “All sessions” is not source-confirmed. A chart display clock does not determine a broker’s daily or 4H candle construction. Neither midnight UTC nor 22:00 UTC can be selected from this evidence.

- [~] **Q11 - Prop firm.** Which firm, account size, daily loss %, max drawdown %, min trading days, news and weekend rules?
  > **Answer:** FTMO recommended; Swing preferred for news/weekend flexibility. Examples: 5% daily/10% overall loss, four minimum days (A); 10%/5% phase targets (C).
  > **Source:** A, [11:38–11:46](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=698s), [3:32:00](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=12720s), [3:33:22](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=12802s), [3:35:29–3:36:34](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=12929s); C, [42:09–42:23](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2529s).
  > **Confidence:** High for historical statements; not assessed for today’s account contract.
  > **Notes:** These are not current firm specifications or Max’s selected account. The 4%/8% placeholders remain engineering choices. Drawdown basis/reset timezone, phase-specific restrictions, precise news blackout, and the chosen account must be verified separately. Starting-account examples are in Part 5. S3 is a broker comment, not a prop-firm rulebook.

- [~] **Q12 - Instruments.** Which pairs / indices / metals, and the broker's pip value, lot step and spread for each?
  > **Answer:** S4/S5 show BTCUSD/XAUUSD charts. B demonstrates gold; a complete instrument list is **not stated**.
  > **Source:** B, [6:25–6:28](https://www.youtube.com/watch?v=xWR8M46iSW8&t=385s); S4 and S5, linked in the source register and example index. Further review pointer for forex: A, [2:41:34–2:41:45](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=9694s).
  > **Confidence:** High for the spoken gold identification; medium for chart observations.
  > **Notes:** No complete instrument allowlist/denylist was established. DXY as analysis context is not automatically an executed instrument. Student charts do not establish Dorus’s instrument preferences. Pip values, contract size, lot step, commissions and current spreads for Max’s broker are not verified.


- [ ] **Q13 — A second visit to the same zone.** Current assumption: first return only.
  > **Answer:** **Not stated.**
  > **Source:** Targeted A–C caption review; A [1:31:21](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=5481s) is a scale-in research lead, not proof about a second zone visit.
  > **Confidence:** Not assessed.
  > **Notes:** A second order, a scale-in, and a second return after mitigation are different events. No verified source equates them. Keep this question open.

- [ ] **Q14 — Extra indicators/models and Kronos.** Current assumption: advisory only.
  > **Answer:** C uses an FVG indicator. A Kronos forecast or veto policy is **not stated**.
  > **Source:** C, [27:41–27:58](https://www.youtube.com/watch?v=R07fGFejJ5w&t=1661s).
  > **Confidence:** High for the indicator example; not assessed for Kronos.
  > **Notes:** Neither permission for Kronos to block a trade nor an absolute ban on indicators follows. “Advisory” remains the project’s choice. The discovered video “How to Use Claude to Become Profitable with Trading” (FZPN1jEGWH4) was not reviewed; its title is not evidence of a trading-model rule.

- [ ] **Q15 — Setup/approval expiry.** Current assumption: one confirmation candle (earlier brief also specified a five-minute minimum).
  > **Answer:** **Not stated.** No verified numerical expiry was located.
  > **Source:** Targeted A–C caption review; S1 is a qualitative relevance comment, not an approval timer.
  > **Confidence:** Not assessed.
  > **Notes:** The lifetime of an analysis, a zone, an entry signal, and a human approval request are separate quantities. Neither the candle-based expiry nor the five-minute floor is attributable to Dorus from the inspected material.

## A2. Definitions in Dorus's own words

For each term, a quote plus the video / lesson and timestamp it comes from: liquidity (which highs and lows count), sweep, balance / balance block, protected zone / POI, BOS, BMS, confirmation, invalidation, target, premium / discount, scalp vs intraday vs swing.

### Part 1 — Definitions and chart identification

1. **Liquidity.** C [15:07–15:10](https://www.youtube.com/watch?v=R07fGFejJ5w&t=907s): “Liquiditeit is eigenlijk het liquideren van het aantal orders.”
   Identification in C: structure highs/lows (18:21), consolidation edges (19:03), patterns (19:46), trendlines (20:31), and higher/lower-timeframe context (21:05). **Confidence: high** for those named categories.
   Exact swing/fractal lengths, equality tolerance, previous-day/week/month hierarchy, internal/external labels, and a complete session-liquidity taxonomy are **not established**. The Asia-session reference at A 1:18:52 needs chart inspection; it is not an algorithmic session-high/low definition.

2. **Sweep.** The inspected examples discuss taking liquidity, but a universal wick-only/close-back rule and minimum penetration are **not stated**. **Confidence: not assessed** for either code predicate. Review C [18:21–20:59](https://www.youtube.com/watch?v=R07fGFejJ5w&t=1101s) alongside its charts before assigning exact event candles. Do not substitute a generic SMC definition.

3. **Balance / balance block.** B [3:44–3:47](https://www.youtube.com/watch?v=xWR8M46iSW8&t=224s): “dit gat noemen wij dus het balance level.” B identifies a three-candle gap after an impulsive/corrective move (3:21–3:47). C draws between the relevant wicks ([27:04–27:18](https://www.youtube.com/watch?v=R07fGFejJ5w&t=1624s)). This is FVG geometry; it is distinct from the origin candle in item 4. **Confidence: high** for the spoken identification; medium for precise geometry until the diagram is independently inspected.
   Body-only/full-opposing-candle bounds are not supported by those definitions. Selection among multiple gaps, mitigation bookkeeping, and a deterministic vote-reset rule remain **not stated**. See Q1.

4. **Protected zone / POI.** B [5:29–5:40](https://www.youtube.com/watch?v=xWR8M46iSW8&t=329s): “De beschermde zone is de candle die de balance level heeft gecreëerd.” A describes POI as X to B/P ([2:15:01](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8101s)). **Confidence: high** for the words, not assessed for a complete numeric drawing rule.
   Which exact wick/body boundary corresponds to each marker, the invalidating timeframe/close predicate, and first-return-only status remain unresolved. Do not replace the protected candle with an automatically chosen opposing candle without evidence.

5. **BOS versus BMS.** C [12:14–12:18](https://www.youtube.com/watch?v=R07fGFejJ5w&t=734s) describes continuation: “wij nog steeds in dezelfde trend bevinden”. Its preceding-low break/reversal example follows at 12:37–13:02. B calls a balance shift a BMS accounting for a balance level ([8:54–9:09](https://www.youtube.com/watch?v=xWR8M46iSW8&t=534s)); A calls it BOS ([42:52](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=2572s)). **Confidence: high** for this terminology variation.
   This does not establish the code’s exhaustive BOS=continuation/BMS=reversal classification. A close past a level and an entire candle body past a level are different predicates; do not treat them as equivalent. See the closure example in Part 4.

6. **Confirmation.** The strongest sourced sequence is in Q5; the balance-shift passage is item 5. **Confidence: high** for stated options, medium for application. A required independent lower-timeframe sweep, universal full-body rule, and the baseline’s minimum-timeframe matrix remain **not established**. No detector-ready formula is supplied here.

7. **Invalidation swing / stop.** B places its stop at the protected candle (item 4, [5:25–5:46](https://www.youtube.com/watch?v=xWR8M46iSW8&t=325s)); A mentions a minimum 1H protector ([1:46:10–1:46:26](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=6370s)). **Confidence: high** for those statements. Exact buffer and a mandatory stop behind the lower-timeframe break-origin swing are **not stated**. The two objects must be kept distinct pending chart evidence.

8. **Target.** Use Q6’s direct quotation. B’s example returns to 1H for protection/target selection ([9:23–9:45](https://www.youtube.com/watch?v=xWR8M46iSW8&t=563s)). **Confidence: high** for the named rule, medium for its example application. A universal target-timeframe floor and tie-break among multiple eligible levels are **not stated**.

9. **Premium/discount, equilibrium, FVG, breakers.** FVG use is explicit in item 3 and Q14. A required premium/discount, equilibrium, or breaker-block filter was **not found** in A–C. **Confidence: high** for FVG use; not assessed for the other filters. Absence from this review does not prove absence from the academy or later videos.

10. **Scalp, intraday, swing.** See Q4 and Q8 for the spoken classification/exit evidence. **Confidence: high** for those passages. Precise duration cutoffs and independent confirmation of M/W as the swing POI pair remain unresolved; the baseline is not itself a primary source.

### Variations, conflicts, and dates

| Issue | Evidence on each side | Interpretation limit |
|---|---|---|
| Sessions | Q10: A 3:54–4:15 versus A 2:24:03–2:24:20; same publication, 2026-02-18 | Later passage refines the earlier window; no timezone conversion is warranted. |
| BOS/BMS terminology | Part 1 item 5: A 42:52 (2026-02-18) versus B 8:54–9:09 (publication date unverified) | Report both labels; no unsupported chronology or universal taxonomy. |
| Readiness thresholds | C [38:28–38:35](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2308s): 5–10% monthly backtest; C [39:42–39:53](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2382s): 5% forward test. A [4:23:53–4:24:26](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=15833s): 1–5% for both. | High confidence for the captioned numbers. A dated 2026-02-18; C date unverified. These are his stated thresholds, not independently validated performance. |
| Code versus teaching | Q1, Q6, Q8 | A code mismatch is not necessarily Dorus contradicting himself. |



## A3. New rules

Rules Dorus states that are not in our rule set (sessions, news, max trades per day, anything on partials or trailing, time-of-day for entries).

### Part 4 — Additional rules and unresolved implementation details

| Topic | Direct evidence / result | Confidence / limit |
|---|---|---|
| Additional bias combination | A [2:14:00](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8040s): M+D+4H also qualifies. | High. Another spoken combination is duplicated in the captions; inspect the slide before adding more. |
| Sessions | Q10. | The default session filter remains unresolved in UTC. |
| News / holidays | A [1:21:11–1:21:29](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=4871s), [2:09:01–2:10:11](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=7741s): avoid bank holidays/pre-news entries; existing trades may continue through news. | High. Exact blackout minutes, event/currency mapping and account-specific exceptions are not established. |
| Confirmation closure | A [2:26:06](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=8766s): “Ik vind het wel belangrijk dat we een closure hebben.” | High for this example; medium for application. It does not settle close-only versus full-body-beyond across all confirmations. |
| Relevant history | S1, Dorus's Aug 19 reply: “Hou het vooral lokaal als je gaat kijken per timeframes.” | High. Qualitative relevance; no numeric lookback cap stated. The student's follow-up asks how far is too far; no answer was visible. |
| Faulty bias | S2, Dorus's Aug 19 reply: “Want ik zie bij je bias nog wel een paar foutjes.” | High. The reply does not enumerate which chart labels are wrong, so none is silently corrected here. |
| Broker use | S3, Dorus's Aug 20 reply: “Ik gebruik zelf Vantage.” | High for the historical comment. Broker symbol specifications and Max’s account choice are still unknown. |
| Loss versus rule adherence | S4: “Dit was volgens mijn strategie een goede trade, maar toch liep hij anders dan verwacht.” | High for Dorus's assessment. No detailed technical loss diagnosis is given in the public text. |
| Trades/day, simultaneous positions, correlation, trailing, second visits, expiry | **Not established** as complete operational rules in this review. Leads: A 3:36:41–3:37:04 (checklist), 56:40–1:01:13 (cross-instrument context), 1:31:21 (scale-in). | These references are a review queue, not confirmed rules. Distinguish illustrative examples from personal hard limits. Q8 supplies the verified partial-exit evidence. |

## A4. Part 5 — Dorus's process

| Stage | Sourced finding | Source / confidence |
|---|---|---|
| Daily preparation | Calendar → account/risk choice → monthly-down analysis → alerts. | A [4:13:03–4:18:19](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=15183s); high. |
| Journal | Record reasons, adherence and emotions. | A [4:25:19–4:27:06](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=15919s); high. |
| Practice sequence | 100 backtests → forward test (C); three consecutive practice challenges (A). | C [38:28–39:35](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2308s); A [3:47:57–3:48:05](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=13677s); high. Threshold variation is logged in Part 1. |
| Start small | 10K funded / €1K own capital (C); maximum 1% risk (A). | C [40:57–41:01](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2457s), [43:37–43:45](https://www.youtube.com/watch?v=R07fGFejJ5w&t=2617s); A [3:31:27–3:31:33](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=12687s); high. |
| Weekly timetable, exact alert actions, sizing costs | **Not established** as complete numerical specifications. | A [4:16:00–4:19:29](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=15360s), [2:43:31–2:44:41](https://www.youtube.com/watch?v=HRPgdK8VhMc&t=9811s) are follow-up passages. An analysis demonstrated on a weekend is not proof of a mandatory weekly appointment. |

### Part 3 — Example file index and readiness

**Zero complete regression fixtures. Four chart records and two caption-only
research leads are included. The requested minimum of five worked examples is
not yet met.** No OHLC candles were exported. No missing timestamp, broker, price
or bar was invented. These YAML files live in `docs/examples/research/`, outside
the loader's non-recursive `*.yaml` scan, and have no matching candle CSV.

Each YAML has a matching `.md` handoff describing what can be read, what is
missing, and the data request. Student annotations are stored separately from
detector expectations: Dorus’s criticism is not approval of those prices.

| Record | Files (relative to `docs/`) | What it can establish |
|---|---|---|
| Public gold recap | [YAML](examples/research/xauusd_2026-08-26_public_recap.yaml) · [handoff](examples/research/xauusd_2026-08-26_public_recap.md) | Dorus-authored chart; displayed 1m is not independently proven to be the POI timeframe. |
| BTC loss | [YAML](examples/research/btcusd_undated_1h_loss.yaml) · [handoff](examples/research/btcusd_undated_1h_loss.md) | Dorus's loss post and H1 chart; no exact entry/SL/TP or full dated data range. |
| EURUSD rejected analysis | [YAML](examples/research/eurusd_2026-08-19_4h_review.yaml) · [handoff](examples/research/eurusd_2026-08-19_4h_review.md) | Student plan with Dorus's relevance critique; readable price labels, not an approved Dorus trade. |
| USDJPY bias critique | [YAML](examples/research/usdjpy_2026-08-19_bias_review.yaml) · [handoff](examples/research/usdjpy_2026-08-19_bias_review.md) | Student scalp claim and Dorus's warning; does not validate the scalp-only setup. |
| Course stop example | [YAML](examples/research/course_stop_example.yaml) · [handoff](examples/research/course_stop_example.md) | Caption locator only; not a chart-verified fixture. |
| Course rejected short | [YAML](examples/research/course_bias_rejection.yaml) · [handoff](examples/research/course_bias_rejection.md) | Caption locator only; not a chart-verified fixture. |

Coverage still needed: a verified M/W POI trade, daily POI trade, 4H POI trade,
1H POI trade, and an accepted scalp-only setup. A screenshot of a timeframe does
not prove that timeframe supplied the entry POI. Neither a profit announcement
nor a student's claim is a substitute for Dorus's explanation.

### Continuation queue

1. Obtain authorized academy access or user-provided lesson exports/screenshots.
   Specifically inspect **2. De strategie leren**, **Bibliotheek** and **Analyses**.
2. Read the plan slide in A at **2:13:35–2:15:39**: all combinations, entry matrix,
   exact break-even units, risk/trade-count text.
3. Review the discovered dedicated plan video **81LThMAtj5o**, recent liquidity
   video **F5ciF74Uzr8**, and FVG video **O6IgD2llrq0** when access is available.
   These titles were discovered, not their lessons verified.
4. Read the chart frames at B **6:19–10:12**, A **1:35:27–1:47:19**,
   **2:04:34–2:07:24**, and **2:21:56–2:27:06**. Record symbol/feed, POI timeframe,
   exact dates, timezone and readable labels before requesting candles.
5. Only then create matching CSV/YAML fixtures in `docs/examples/`: exact
   `timestamp,open,high,low,close,volume` columns, UTC candle opens, at least 60
   pre-sweep candles and enough post-break history. Do not copy screenshot OHLC
   into invented surrounding bars. Run `python -m pytest tests/trader/test_examples.py`
   once complete fixtures exist.

The source-access inventory is in
[examples/research/source_coverage.yaml](examples/research/source_coverage.yaml).



## B. Deliverables Astra can build (drop the result path here)

- [~] **B1 - Annotated examples.** 5–10 real chart examples from Dorus's material in the format of `docs/examples/README.md`: `<name>.csv` (candles) + `<name>.yaml` (sweep candle, break candle, balance block, POI, entry, stop, target). They become tests automatically (`python -m pytest tests/trader/test_examples.py`).
  > path: `docs/examples/research/` — four chart records, two caption-only leads; zero complete CSV/YAML fixtures. See Part 3. B1 remains incomplete.
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
- [x] C2 - Kronos forecast indicator wired (`kronos_trader/indicators`) - needs model weights on the desktop (Hugging Face is blocked from the cloud session)
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
