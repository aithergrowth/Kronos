# Astra's findings of 1 October 2026: reproduced, refuted or still uncertain

Status per finding, with the evidence. "Programming error" means the code did not do what the written
rule says; "interpretation" means the rule itself is a choice the sources do not settle. The two are kept
apart on purpose: the first kind is fixed without discussion, the second kind only with source material.

## Package "EURUSD tien beslismomenten" (CLAUDE_HANDOFF.md)

| # | Finding | Status | Evidence | Kind |
|---|---|---|---|---|
| 1 | 13 Aug 13:45 UTC: the bearish 4H gap of 12 Aug 17:00 (1.15307-1.15325, 1.80 pip) is dropped; minimum 3.05 pip; adding it turns the 4H bias bullish into 50/50 and removes the scalp combination | **Reproduced** on Astra's OANDA data with `decision-dossier`: the dossier lists exactly that gap as dropped (width 0.00018, required 0.000305) and the decision "1D+4H+1H aligned -> scalp only" | interpretation (the 20 % threshold is an assumption; Dorus names no size) |
| 2 | The 4H zone 1.15230-1.15597 stays "visit 1" from 7 Aug 17:00 to 13 Aug 13:45 (140.75 h) although price left it fully five times; the exit line is 1.161475 | **Reproduced**: on Astra's 15m data our rule gives visits=1 over the window; a strict rule (one full 15m candle outside ends the visit) gives 6 visits and 5 exits; 140.75 h | interpretation (the 1.5-zone-height allowance is ours) |
| 3 | A fresh engine at 21 Aug counts the 1H zone of 17 Aug 01:00 as visit 1; the replay counts 2 | **Reproduced**: cold dossier visits=1, dossier with a six-day warm-up visits=2. Fixed in the tooling: backtests now write dossiers from their own engine at every signal (`--dossier-dir`), and standalone dossiers can warm up (`--warmup-days`); every dossier states which it is | programming gap in the diagnostic tool, not in the strategy |
| 4 | X/B/P selection not 1:1: P is always candle 2; the outer edge sometimes runs beyond X; the 3-candle wait in `entry_after_shift` is own policy | **Uncertain**: all three are interpretations the sources do not settle; `entry_after_shift` is off in the frozen profile | interpretation |
| - | 24 tests pass, 78 files hash-verified, 60 gap traces equal to the detector, eight moments stop on bias, one on news, one waits for confirmation | **Consistent** with our own runs; nothing to add | - |

## Package addendum "Goud-En-Recente-Trades-Controle.md"

| # | Finding | Status | Evidence | Kind |
|---|---|---|---|---|
| 1 | Gold 26 Aug 14:00 and 15:30 UTC: the bias gate refuses, but the last bearish 1H zone (4629.235-4658.555) is `tested` with price below it, so even without the gate no entry would follow; `inside=true` in the dossier is visit memory, not zone overlap | **Reproduced** from our own dossiers; the dossier label now reads "visit open / no visit" and names the 1.5-zone rule instead of "inside" | reporting clarity (fixed); the strategy question stays open |
| 2 | K3 says the monthly, weekly and daily were weighed less, but gives no replacement rule; Dorus's two entries (4624.53, 4623.59) lie below the lower edge of the code's zone | **Uncertain**, and the entries-below-the-zone observation is **reproduced**: his stop (4639.55) sits inside our zone, his entries below it, so his zone was smaller and lower than any zone the code draws on 1H and up. The open question is whether his gold scalps use zones from timeframes below the 1H, which his written plan does not list | interpretation; needs a source example on a verified clock and feed |
| 3 | The four September trades: planned R:R and R:R at fill differ (3.76 vs 1.91, 0.86 vs 0.86, 1.44 vs 1.74, 0.90 vs 1.54) and all four `rr_at_fill` values are arithmetically right | **Reproduced**; the chat table had shown only the planned column, the repository README shows both. Reports now carry both | reporting (fixed) |
| 4 | Keep the bias rule until the K3 variant is substantiated; compare one source example on the same feed and clock; judge the gap threshold and the visit definition on the ten moments; show both R:R columns; evaluate one frozen profile on unused data | **Adopted** as the working order | - |

## Earlier today (second and third review)

All closed: executable-price sizing with risk reconciled to the fill, month-end closes across DST, shorts
valued on the ask, pandas 3, visits tracked before the entry gates, chart identity, first breach exported,
news coverage, the as-of gap threshold. Astra's probe scripts pass on the current code.

## What stays separate

Programming errors found today were all fixed and tested. The strategy choices that Astra and I both mark
as interpretation (gap size, visit end, P selection, outer edge, target choice, R:R floor, first candle,
session windows, news minutes) are unchanged unless a quote or a chart of Dorus's own says otherwise, and
each change carries its source in `config/dorus_pure.yaml` and `docs/DORUS_RULES_FROM_TRANSCRIPTS.md`.
