# Backtrace of October 2026: did the strategy have trades the bot missed?

Asked by Max on 16 October, the third FTMO day without a trade. The live code (HEAD ad76f2d, and separately the exact
commits the FTMO windows ran: 3e2a4d2 from 13 October 19:14 and 26fce7a from 14/15 October) with the four live
profiles and the windows' FTMO settings (account 10k, RISK 1.5, ftmo_2step guard, TARGET 10, STOP_AT_TARGET), 5m steps,
FTMO costs, on TradingView OANDA candles (EURUSD, XAUUSD, NAS100USD; continuous 5m from 27 September, no holes in the
entry windows) and Bitstamp BTC cut both on FTMO's day (17:00 New York) and on UTC, from 1 October to 16 October 16:50
Amsterdam. An independent rerun reproduced every trade and every per-step decision (EURUSD, gold); 112 jittered reruns
gave no FTMO-day signal.

- **FTMO days 14-16 October: 0 trades on all four markets, as live.** Both code versions the windows ran agree. Mostly
  the bias refused (the higher timeframes disagreed all three days). The one setup the bias allowed, a gold short on 14
  October at 14:35 Amsterdam, fell in the CPI blackout; without the calendar it is taken and loses 1R.
- **1-16 October: 4 trades, all before 7 October.** EURUSD shorts on 5 October (twice) and 6 October, all stopped
  (-3.1R together), and a BTC long on 2 October (+7.0R, before any BTC window ran). Nothing on any market from 7 October.
- **The setups the rules refused would have lost**: about -14R over the period at their own stops and targets
  (EURUSD about -5R, gold -1.45R, NAS100 about -0.4R, BTC on FTMO's day -6.8R).
- **The two pre-challenge trades** (Max's screenshots): the EURUSD short of 8 October 16:07 is what the code of that
  day did (a 1H visit 29 hours old); the 1H visit-age rule of 9 October refuses it now. The BTC trade stopped on
  7 October at 83,489.6 is reproduced by no code version on either BTC day cut.
- Caveats: OANDA prices are not FTMO's feed (no few-tick difference turned a miss into a trade); the backtest keeps a
  visit memory from 1 October, the windows only since 14 October (no decision changed).

Files: scratchpad `october/` (cache, per-market runs `bt_<SYM>/`, `explain/` with the old-code runs, `verify/`).
