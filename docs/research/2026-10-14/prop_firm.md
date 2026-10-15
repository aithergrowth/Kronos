# Prop-firm practice: FTMO 2-Step 10k, then a funded Standard account (14 October 2026)

Angle: what the published FTMO rules and the public evidence on failed challenges say, turned into rules for the guard, the
sizing and the schedule, each measured on our own ledgers. Read-only research; nothing in the repository was changed.

Ledgers: the four 2024-02 .. 2026-09 research ledgers (`aca/eutwo_EURUSD`, `base_XAUUSD`, `rr08_NAS100`, `base_BTCUSD`;
raw R, no costs) and the 2017-2023 out-of-sample ones (`oos_*`). Every replay rebuilds the live stake per trade (base
1.5 %, the ladder -3 % -> 1.0, -6 % -> 0.5, a 4H zone x2 on EURUSD/gold/NAS100, BTC x0.5, EURUSD's 1D+1H pair x0.5, a
50/50 month x0.5, BTC cut to FTMO's crypto margin), takes 0.10R a trade for costs (0.25R as a stress), and runs the
account the way the live guard does: two open (EURUSD two), the worst-case day check at 4 % of the initial balance
(day-start balance less every open stop and the new one), the worst-case total at 9.5 %, FTMO's own 5 % day (from the
midnight CE(S)T balance) and 10 % static on closed trades, phase 1 +10 % and phase 2 +5 % each with at least 4 trading
days (a day with a trade opened), a phase passed when the target holds with the account flat. Starts: every day
2024-02-01 .. 2025-12-31 ("2024-25", 700), every day 2026-01-01 .. 2026-07-31 ("2026", 212), every third day
2017-06 .. 2023-06 ("2017-23"). Code: `research/prop_lib.py`, `run_baseline.py`, `run_target.py`, `run_limits.py`,
`run_news.py`, `run_gaps.py`, `run_corr.py`, `prep_adjusted.py`, `run_funded.py`, `run_funded2.py`.

The replay agrees with the README's challenge numbers in shape (2024-25 starts funded within 3 months 41 % here against
52 % in the README, which did not model the guard's refusals and ran without the cost haircut; 2026 starts within
2 months 92 % against 97 %), and it is the guard's worst-case check that explains the difference between 0 % and 7 % failed.

## 1. The rules, from FTMO's own pages

| Rule | What FTMO says (October 2026) | Source |
|---|---|---|
| Profit target | 10 % of the initial balance in the Challenge, 5 % in the Verification, none on the FTMO Account | [Trading Objectives](https://ftmo.com/en/trading-objectives/) |
| Maximum daily loss (2-Step) | 5 % of the initial balance. The limit is recalculated at 00:00 CE(S)T as *the balance at 00:00 CE(S)T minus 5 % of the initial balance*; **equity** (balance + open P/L, swaps and commissions included) may not fall below it. Open positions count through equity only, never through the midnight balance. Example: $100k, day 1 limit $95,000; midnight balance $102,000 -> day 2 limit $97,000. Applies on the FTMO Account too | [Trading Objectives](https://ftmo.com/en/trading-objectives/), [Academy lesson](https://academy.ftmo.com/lesson/maximum-daily-loss/) |
| Maximum loss (2-Step) | 10 % of the initial balance, static; equity may not fall below it. Applies on the FTMO Account too | [Trading Objectives](https://ftmo.com/en/trading-objectives/) |
| Minimum trading days | 4 per phase. A trading day is a day (00:00:00-23:59:59 CE(S)T) on which at least one position is **opened**; closing alone does not count. No time limit | [Trading Objectives](https://ftmo.com/en/trading-objectives/) |
| Consistency rule | None on the 2-Step (1-Step and Instant only) | [FAQ: consistency](https://ftmo.com/en/faq/how-does-your-consistency-rule-work/) |
| A breach | The platform closes every open position and the account is failed | [FAQ: trading objectives](https://ftmo.com/en/faq/what-are-the-trading-objectives/) |
| News on the FTMO Account (Standard) | No order execution 2 minutes before and 2 minutes after selected releases, on every instrument carrying the affected currency (USD events: USD pairs, gold, US indices, DXY ...). "This restriction applies to any order execution, including your Stop Loss, Take Profit or any other pending orders." A position opened earlier may be held through the window. Not on the Challenge or Verification, not on Swing accounts. Restricted events are marked "Restricted event" in FTMO's calendar. Violation "may result in termination of an FTMO Account" | [FAQ: news](https://ftmo.com/en/faq/can-i-trade-news/) |
| Weekend / breaks on the FTMO Account (Standard) | No position may be held through a market break longer than 2 hours (the weekend); close before the break begins. Not on the Challenge or Verification, not on Swing | [FAQ: overnight and weekend](https://ftmo.com/en/faq/can-i-hold-positions-overnight-or-over-the-weekend/) |
| Payouts | The first Reward can be requested on the 14th day after the first trade on the account, then on any following day. "All open positions and pending orders must be closed before requesting the Reward." 2-Step: 80 % of the profit, 90 % once the Scaling Plan or Premium conditions are met (1-Step and Instant: 90 %). Minimum $20 (bank/card), $50 (crypto). Review 1-2 business days | [FAQ: withdraw](https://ftmo.com/en/faq/how-do-i-withdraw-my-profits/) |
| Scaling plan | +25 % account size every 4 months when the previous 4 months show at least 10 % net profit, at least 2 processed Rewards in that window and a positive balance at the scale-up; the split becomes 90 % (2-Step); cap $2M across accounts | [Scaling plan](https://ftmo.com/en/scaling-plan/) |
| FTMO's own advice | Stop at a 4 % day when the limit is 5 %; commissions and swaps count ("a stop at -$500 ... -$515 breaches"); stops do not guarantee the price (slippage, spreads widen on news); close positions instead of hedging near a limit; the day is CE(S)T | [Tips for completing the FTMO Challenge](https://ftmo.com/en/blog/tips-for-completing-the-ftmo-challenge-how-to-avoid-mistakes/) |

The guard already matches the day definition (`prop_firm.day_timezone: Europe/Prague`), FTMO's balance-based midnight
reset (`day_start_balance` is the closed balance) and the static floor (`drawdown_basis: initial`). Its worst-case check
bounds the open risk at any moment to under 4 % of the initial balance, so one position carried over midnight cannot
breach the 5 % day by its stop alone; only a gap or slippage through a stop can. With a second position, or a NAS100
position's swaps over several nights, the margin is smaller (stack review of 15 October, A2 and A20; the guard counts
the accrued swap since then).

## 2. What fails challenges (public evidence)

- A Traders Union survey of traders who failed (self-reported): 43 % breached the daily loss limit, 24 % the maximum
  drawdown, 18 % never reached the target; two thirds failed on a risk rule, not on the edge
  ([Traders Union](https://tradersunion.com/news/financial-news/show/2656095-traders-fail-challenges/), via search
  summary; the page itself refuses robots).
- FTMO has cited pass rates around 9-10 % for its challenge; most firms that publish land between 5 and 15 %; the
  common failure pattern is sizing up after a loss to "make it back before the daily limit resets"
  ([HackerNoon](https://hackernoon.com/the-real-reason-traders-blow-prop-firm-evaluations); the piece's "70 % of
  failures are loss-limit breaches" carries no source).
- Third-party guides on the news rule agree that a stop or take-profit executed inside the window counts as a breach
  ([propfirmsfinder](https://propfirmsfinder.com/guides/prop-firm-news-trading-rules/)); on correlated USD trades they
  warn that per-trade risk looks fine in isolation while the combined loss is what hits the daily limit
  ([tradezella](https://www.tradezella.com/blog/pass-prop-firm-challenge)).

For a rule-based bot the first two are the guard's job; our data below say the guard does it, and that the failure
modes left are the ones a backtest cannot show: an execution inside FTMO's 2-minute window on the funded account, a
gap through a stop at double stake, and trading on after the target.

## 3. Our data

### 3.1 The guard against FTMO's rules (challenge replay, 1.5 % with the ladder, 0.10R costs)

| Variant | 2024-25 starts: funded / failed / within 3 months / median days | 2026 starts: within 6 weeks / 2 months | 2017-23 starts: funded in a year |
|---|---|---|---|
| **Rules now** (worst-case day 4.0 %, floor 9.5 %) | 98.9 % / 0 % / 41.0 % / 110 | 56.1 % / 92.0 % | 11.7 % (0 % failed, the rest stalled at the floor) |
| Guard off (FTMO's limits only) | 92.9 % / **7.1 %** / 44.7 % / 95 | 56.1 % / 92.0 % | 12.0 % / 87.6 % failed |
| Worst-case day 4.5 % | identical to 4.0 (the 1.5 + 3 % combination is refused at both) | | |
| Worst-case day 4.9 % | 98.9 % / 0 % / 44.7 % / 103 | same | 12.3 % |
| ... at 0.25R costs | 74.1 % / **9.4 %** against 83.6 % / 0 % at 4.0 | | 9.2 % / 13.9 % failed against 10.9 % / 0 % |
| Floor 8 % (the demo's) | 83.3 % (stalls) / 0 % / 41.0 % | same | 11.6 % |
| No ladder | 90.0 % / 0 % / 51.6 % / 81 | 56.6 % / 92.0 % | 12.1 % |

The guard turns the 7 % of starts that break FTMO's limits into 0 % and costs about four points of three-month passes:
it refuses 0.4 trades a challenge on the worst-case day check (those trades averaged +0.92R, 54 % won) and holds the
account at -9.5 % instead of letting it fail. Raising the day limit to 4.9 % buys back those points only while the edge
is as backtested; at 0.25R costs it fails 9-14 % of the starts. 4.0 % stays (FTMO's own tip is the same number).

Day clustering at the live stakes (no ladder): 239 FTMO days with a closed trade; 7 days at -3.3 % (every one a single
4H-zone loss at the double stake), one day at -6.6 % (21 August 2025: two EURUSD 4H longs, the second a same-visit
re-entry stopped in its first candle; the guard refuses the second: worst case 6 %). After a 4H loss the guard lets
nothing but a 0.75 % BTC trade in for the rest of the day. Trades opened on a day after a closed loss: 43, 51 % won,
+31.9R (after the day's loss reached 1.5 %: 20 trades, +22.4R): no cool-down rule is warranted. Trading days: 7.6 a
month on average, 2 of 32 months under 4; trades on one day: 1 (179 days), 2 (59), 3 (6).

### 3.2 Correlated positions

EURUSD and gold: daily return correlation 0.39 (2024-2026), 0.42 (2017-2023), the same direction on 63-66 % of days;
NAS100 0.05-0.19 with both, BTC about 0. Trades open at the same time across markets: 30 pairs in 32 months (EURUSD x
gold 7), 28 of them in the same dollar direction; both lost in 14 % of those pairs against 13 % expected if
independent; days with two or more trades in the same dollar direction: 60, all lost on 11, average day +1.75 %. A
dollar-cluster rule in the replay (second trade in the same dollar direction at half stake): 2024-25 funded 97.4 %
(98.9), 2026 within 6 weeks 49.1 % (56.1), 2017-23 11.7 % (11.7); refusing it: worse; EURUSD and gold only: no change.
The worst-case check already caps the joint stop loss at under 4 %; nothing to add.

### 3.3 Around the target and the four trading days

- The target reached before the 4th trading day: 7 % of the 2024-25 starts, **32 % of the 2026 starts**, 18 % of
  2017-23. Trading on at full stake until day 4 took the balance back under +10 % in 33 % / 10 % / 17 % of those cases
  (worst dip 3.0 / 1.4 / 4.5 % under the target).
- After the target with 4 days logged, the live bot keeps trading (nothing in `live.py` or the guard reads the target;
  only the 22:05 report shows it). Trading on at full stake puts the balance back under +10 % within 1 day in 1-3 %
  of cases, within 3 days in 7-12 %, within 10 days in 16-36 %.
- Finishing at 0.10 % once the target is reached before day 4 (minimum lots, the days still count): 2026 within 6 weeks
  56.1 -> 59.4 %, 2024-25 within 3 months 41.0 -> 42.1 %, 2017-23 funded 11.7 -> 12.6 %; never worse.
- `risk.target_protect_pct` 4 (half the stake in the last 4 %): slower everywhere (2026 within 6 weeks 44.3 %, median
  44.5 days against 40; 2024-25 within 3 months 39.1 %) and no fewer failures (0 either way); at 0.25R costs +2.3
  points on 2024-25, -1.0 on 2017-23. Within 2 %: a wash. A gap-sized stake (stake = the distance to the target over
  the planned R:R, floor half, in the last 4-6 %): 2024-25 43.1 % (+2.1), 2017-23 14.0-14.4 % (+2.3-2.7), 2026 52.4 %
  (-3.7): mixed.

### 3.4 News on the funded Standard account

Exits inside the 2-minute window of a high-impact event of the market's currencies (the forward-looking rule): 2024-2026
8 of 322 trades (2.5 %), 2017-2023 23 of 698 (3.3 %); of a core restricted set (NFP, CPI, Fed, ISM, PPI, retail sales,
PCE, JOLTs, ECB) 7 and 17. The eight: EURUSD stop at ISM 1 Aug 2024, EURUSD stop at NFP 11 Feb 2026, gold stop at ISM
5 Sep 2024, NAS100 targets at NFP 4 Oct 2024, CPI 11 Jun 2025, ISM 4 Mar 2026, BTC target at NFP 5 Sep 2025 and stop at
the NFP revision 9 Sep 2025. Entries inside the window: none (the 30-minute blackout; a resting limit could still fill
there). On the funded Standard account each such execution is a termination risk; nothing in the code prevents it.

The cost of going flat 5 minutes before a restricted event (the position closed at the 5m close 5 minutes before,
no re-entry): trades open across a core event 2024-2026: 41, held +93.3R, flat +38.2R (**-55R**, 23 % of the period's
R; the two BTC winners of June 2026 are 30R of it, EURUSD 12 trades +26.7 -> +7.8R, gold 15 trades +11.0 -> +11.5R);
2017-2023: 47 trades, +28.6 -> +24.1R (-4.5R). FTMO's instrument list for USD events names USD pairs, gold, US indices
and DXY, not crypto: if BTCUSD is exempt, the 2024-2026 cost is about 22R instead of 55R (ask FTMO support).

### 3.5 Gaps through a stop at the double stake

A 4H-zone trade risks 3 % (3.3 % with costs); a gap of 1.67 stops on the wrong side is a -5 % day, the challenge gone
in one print, and nothing in the guard can stop it. Gaps since 2024 in units of the median 4H-zone stop:

| Market (median 4H stop) | Nights: P(gap > 1 stop) / > 1.67 / > 3 | Weekends: > 1 / > 1.67 / > 3 | 4H trades held over a break in the ledger |
|---|---|---|---|
| NAS100 (0.197 % of price) | 16.0 % / 8.8 % / 3.1 % | 42.2 % / 29.9 % / 18.4 % | 2 of 5 (overnight; +3.1R) |
| EURUSD (0.153 %) | 7.1 % / 0 / 0 (few breaks) | 18.1 % / 12.5 % / 4.2 % | 1 of 10 (weekend, +3.85R) |
| XAUUSD (0.548 %) | 0.5 % / 0 / 0 | 13.0 % / 7.5 % / 1.4 % | 9 of 13 (2 over a weekend, +1.99R each) |

Per weekend-held double-stake position the chance of an instant fail is roughly half of the > 1.67 column: NAS100
15 %, EURUSD 6 %, gold 4 %; per NAS100 night 4 %. Closing only the double-stake positions on Friday costs, on the ledger,
-6.7R over 3 trades in 2024-2026 (all three were winners held over a weekend) and -7.2R over 7 in 2017-2023; the full
weekend close -9.3R over 10 and -7.4R over 26 (the README: about -8R over 2023-2026). NAS100 4H zones at the single
stake in the replay: 2024-25 funded 100 % (98.9), within 3 months the same 41.0 %, 2026 within 6 weeks 53.3 % (56.1),
2017-23 11.3 % (11.7): a wash on the ledger, and the overnight tail of a 3 % NAS100 position is gone.

### 3.6 The funded account (1.0 %, ladder -3 % -> 0.5, 12 months from weekly starts, 80 % split)

"Standard with the rules" uses ledgers rewritten as a Standard account must trade: flat before a restricted event and
flat before the weekend (3.4, 3.5); "Swing" keeps every trade but sizes at 1:30 forex, 1:10 gold and indices, 1:1
crypto with one position at most 45 % of equity in margin.

| Account | 2024-26, 0.10R: payout a month / stalled under -8 % | 2024-26, 0.20R | 2017-23, 0.10R |
|---|---|---|---|
| Standard, rules ignored (the README's model) | 4.15 % / 0 % | 3.48 % | 0.24 % / 76 % |
| **Standard with the rules** | 3.19 % / 0 % | 2.43 % / 0 % | 0.24 % / 76 % |
| Swing | 3.27 % / 0 % | 2.57 % | 0.16 % / - |
| Standard with the rules, 1.0 % flat | 3.38 % / 1 % | 2.57 % / 11 % | 0.36 % / 84 % |
| Standard with the rules, the challenge stake 1.5 % | 4.36 % / **22 %** | 3.12 % / **71 %** | 0.27 % / 93 % |
| Standard with the rules, keep a 3 % cushion | 3.12 % / 0 % | 2.39 % / 0 % | 0.23 % / 74 % |
| Standard with the rules, payouts every 14 days | 3.11 % / 0 % | 2.44 % / 0 % | 0.22 % / 76 % |

The rules cost a Standard account about a quarter of its payout; Swing's leverage costs the same quarter: the two come
out equal (3.19 against 3.27 %, 0.24 against 0.16 %). The funded stake matters more than either: at the challenge
stake 22-71 % of the accounts drift to the guard's floor within a year, at 1.0 % with the ladder none. A cushion kept
in the account and a 14-day cadence change nothing but the timing; the Scaling Plan's two payouts in four months with
10 % net profit is met from 98-100 % of the 2024-26 starts under either cadence.

## 4. Candidates

1. **Stop at the target, finish the days at minimum stake** (needs code). Rule: with `risk.target_pct` set (10, then 5),
   once the account's closed balance is at or above the phase's target: with fewer than 4 trading days logged
   (`prop_firm.min_trading_days: 4`, days with a position opened, Prague clock, counted from the terminal's history
   like the day report does) every new trade risks `prop_firm.finish_risk_pct` 0.10 % (the minimum lots); with 4 or
   more logged the window opens no new trade, lets the open ones run, and tells Max on Telegram to request the next
   phase (`prop_firm.stop_at_target: true`). Evidence 3.3: the target before day 4 in 32 % of the 2026 starts;
   full-stake trading until day 4 undid it in 10-33 % of those cases; after a qualifying pass trading on undoes it
   within 3 days in 7-12 % of cases. Finish mode: 2026 within 6 weeks 56 -> 59 %, 2024-25 within 3 months 41 -> 42 %,
   2017-23 funded 11.7 -> 12.6 %, never worse. Markets: all (account-level).
2. **No execution inside FTMO's 2-minute news window on the funded Standard account** (needs code). Rule:
   `prop_firm.news_flat_minutes: 5` (off by default, set with `FUNDED=1`): every open position of a market whose
   currencies have a restricted event ahead is closed at the market 5 minutes before it and every resting limit of
   that market cancelled; nothing opens again until `news.after_minutes` has passed (already 30). The event list is
   FTMO's "Restricted event" calendar, loaded like the ForexFactory feed; until that feed exists, the core set
   (NFP, CPI, Fed decision and press conference, FOMC minutes, GDP advance, ISM, PPI, retail sales, core PCE, JOLTs;
   ECB decision, press conference and the flash CPI for EURUSD). Evidence 3.4: 2.5-3.3 % of all exits land in the window
   (8 in 32 months), each a termination risk on the funded account; cost on the ledger -55R of 241R over 2024-2026
   (-22R if BTC is exempt), -4.5R over 2017-2023; in the funded replay the payout goes from 4.15 to 3.19 % a month with
   the weekend close included. Alternative for the next purchase: a Swing account (no news or weekend rule, 1:30/1:10/1:1
   leverage) pays about the same (3.27 % against 3.19 %) with no rule to execute. Markets: EURUSD, XAUUSD, NAS100, BTCUSD
   (BTC until FTMO support says crypto is exempt).
3. **Double-stake positions flat before the weekend, in the challenge too** (needs code: a filter on the existing
   weekend close). Rule: `prop_firm.weekend_close: "15:45"` with a new `prop_firm.weekend_close_min_risk_pct: 2.0`: at
   Friday 15:45 New York only positions whose risk to the stop is 2 % of the initial balance or more (the 4H zones at
   x2) are closed; the rest hold as now; no new double-stake trade from 15:45 Friday. Evidence 3.5: a wrong-side weekend
   gap of 1.67 stops is a -5 % day; such gaps follow 30 % of NAS100 weekends, 12.5 % of EURUSD's, 7.5 % of gold's, so a
   weekend-held 3 % position fails the challenge with about 4-15 % probability; the ledger held three such positions in
   32 months (all winners, -6.7R if closed Friday) and seven in 2017-2023 (-7.2R). Roughly a wash on expectation (about
   -2 % of balance a challenge against a 1-2 % chance of an instant fail), all of it variance; the one failure mode the
   guard cannot see. Markets: EURUSD, XAUUSD, NAS100 (BTC has no weekend break).
4. **NAS100 4H zones at the single stake** (config). Rule: in `config/dorus_live_nas100.yaml` set
   `risk.zone_risk_multiplier: {}` (a NAS100 4H zone risks 1.5 %, not 3 %); EURUSD and gold keep x2. Evidence 3.5: NAS100's
   night gap exceeds the median 4H stop one night in six and 1.67 stops one in eleven; 2 of its 5 4H trades were held
   overnight; at 3 % such a gap is a -5 % day, at 1.5 % a -2.5 % day the ladder absorbs. Replay: 2024-25 funded 100 %
   (98.9), within 3 months 41.0 % (same), 2026 within 6 weeks 53.3 % (56.1), 2017-23 11.3 % (11.7): neutral on the
   ledger (5 trades, +6.2R), the tail gone. Markets: NAS100.
5. **Keep the worst-case day limit at 4.0 % and the floor at 9.5 %** (config, unchanged). Evidence 3.1: 4.5 % changes
   nothing (the 1.5 + 3 % combination is refused at both), 4.9 % buys +3.7 points of three-month passes at 0.10R costs
   but fails 9.4 % of the 2024-25 starts and 13.9 % of 2017-23 at 0.25R, where 4.0 % fails none; the demo's 8 % floor
   stalls 17 % of the starts. Also measured and not worth adding: a day stop after a 3 % closed loss (identical, the
   worst-case check already blocks the day), a dollar-cluster rule (3.2: slower, no fewer failures), a cool-down after a
   loss (after-loss trades +31.9R). Markets: account-level.
6. **Funded account: 1.0 % with the ladder, payouts every 14 days from day 14, no cushion, requested on Friday after the
   weekend close** (config and schedule; `FUNDED=1` already sets the stake and the weekend close). Rule: on funding
   `risk.risk_pct 1.0`, `drawdown_steps [[-3, 0.5]]`; the first Reward requested on day 14 after the first trade if the
   closed profit is $20 or more, then every 14 days, always after the Friday 15:45 close when the account is flat (FTMO
   requires it), withdrawing everything above the initial balance. Evidence 3.6: at the challenge stake 22 % (0.10R) to
   71 % (0.20R) of funded accounts drift to the floor within a year, at 1.0 % with the ladder none; a 3 % cushion
   lowers the payout by 0.07 % a month and prevents nothing; the 14-day cadence pays the same as monthly (3.11 against
   3.19 %) and meets the Scaling Plan's two payouts per four months from 98-100 % of the starts, which brings the 90 %
   split. Markets: account-level.
7. **Leave `risk.target_protect_pct` off** (config: `PROTECT` unset in `scripts/ftmo_local.bat`). Evidence 3.3: halving
   the stake in the last 4 % costs 12 points of six-week passes in 2026 and 4-6 days of median time with no fewer
   failures; only at 0.25R costs it gains 2.3 points on 2024-25 and loses 1.0 on 2017-23. If a protection is wanted,
   the gap-sized variant (stake = distance to the target over the planned R:R, floor half; needs code in
   `strategy/risk.py` next to the half rule) is the one that is not slower: +2.1 points on 2024-25, +2.3-2.7 on
   2017-23, -3.7 on 2026. Markets: account-level.
8. **The guard's news check extends to resting limits and to the restricted feed** (needs code, small). Rule: a limit
   order that would still rest inside a news blackout (`news.before_minutes` before an event of its currencies) is
   cancelled at the blackout's start, and a fill inside the window is impossible; on the funded account the same
   feed drives candidate 2. Evidence: FTMO counts any order execution; EURUSD and NAS100 enter by limits valid 4 hours
   (`limit_entry_minutes: 240`), so a limit placed at 13:00 can fill at 14:30 on CPI; the ledgers show no entry inside
   the 2-minute window over 1,020 trades only because the backtest fills limits on candle prices. Expected effect on
   the ledger: none measurable; it closes the one entry path the 30-minute blackout does not cover. Markets: EURUSD,
   NAS100.

## 5. Not supported by the data

- A monthly loss stop, a week stop, a pause after a losing run (README, 5 October) and a day stop after a loss (3.1):
  the worst-case check already ends a day after a 4H loss, and the trades after a loss won.
- A dollar-exposure rule beyond the worst-case check (3.2).
- A cushion in the funded account, or a slower payout cadence (3.6).
- Raising the stake near the end of a phase (every protect variant that reduces it is slower; raising it was not
  tested and the failure evidence argues against it).

## 6. Files

`research/prop_firm.md` (this), `prop_lib.py` (replay library), `run_*.py` (the studies), `adj_*.csv` (the ledgers as a
funded Standard account trades them), `funded_results.csv`, `baseline_starts_2024_25.csv`.
