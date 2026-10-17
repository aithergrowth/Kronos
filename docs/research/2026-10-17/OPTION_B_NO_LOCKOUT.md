# Does option B refuse trades the old setup took? (17 October)

Asked by Max after three days without a trade. Checked on 95d60db against 6e290e8 (the old setup: RISK 1.5, 4H x2,
BTC x0.5, STOP_AT_TARGET, no lock) with the windows' own settings (cli.live_settings on start_ftmo.bat's flags):

- **October 1-16**: both setups take the same trades (EURUSD 5 and 6 October, BTC 2 October) and none on 14-16 October.
  The real LiveRunner on the tests' fake FTMO terminal placed every one of them at the same moment, with only the stake
  different; with 0 trading days it never used the finish stake, never moved a target and never skipped an entry.
- **Backtests Feb 2024 - Sep 2026 from 10,000, month by month**: all 314 old trades are in option B unchanged; option B
  adds 2 the old day limit refused. No minimum-lot, margin or other refusal. (Single 2.6-year runs per market differ only
  at balances a 10k challenge never reaches, 13,001-23,459, where the 4 % day limit on the 10,000 start binds.)
- **Account replay, 967 starts**: guard refusals 918 for option B against 2,198 today; a frozen account (every trade
  refused near -9.5 %) in 3 starts against 7.
- **Rare refusals**: a BTC setup with a very wide stop falls under 0.01 lot at the quarter stake (0 of 85 bot-backtest
  BTC trades at the start balance; 1 at -3 %, 6 more at -6 %); a second 1H trade on a day already 0.5 % down (never at
  challenge balances).
- **The lock** never refuses an entry, sleeps until the fourth trading day, and every failure in it falls back to the
  trade's own target (500 differential scenarios and 57 injected terminal faults: no entry lost).
- **The one operational risk**: a failed pull with RISK=1.75 already set runs the old x2 profiles at 3.5 % a 4H trade.
  So: pull, check `git grep -F "{4H: 1.25}" config` prints 3 lines, then raise RISK.

Nothing to fix before Monday. Files: scratchpad `nolockout/`.
