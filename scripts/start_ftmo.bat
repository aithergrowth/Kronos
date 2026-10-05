@echo off
rem FTMO windows beside the demo: EURUSD, XAUUSD, GBPUSD, NAS100 and BTCUSD on the FTMO MT5 terminal, orders without the
rem Approve tap, their own journal (journal_ftmo\) and "[FTMO]" in front of every Telegram message.
rem Before: the FTMO terminal installed, logged in to the trial or challenge account, Algo Trading on (green).
rem Check the SET lines once: the terminal (right-click its shortcut, Properties, Target) and the symbol names, which
rem list with:  set MT5_PATH=<the terminal>  then  python -m kronos_trader mt5-symbols --search 100  (and --search BTC).
rem The password stays in the terminal: MT5_LOGIN, MT5_PASSWORD and MT5_SERVER are cleared for these windows, so they
rem trade the account the FTMO terminal is logged in to. A window whose symbol the server lacks stops at the start.
rem ACCOUNT is the challenge size: the guard counts its -4 % day and -8 % from that start (FTMO: 5 % and 10 %).
cd /d "%~dp0.."
set "MT5_PATH=C:\Program Files\FTMO MetaTrader 5\terminal64.exe"
set "ACCOUNT=10000"
set "NAS_NAME=US100.cash"
set "BTC_NAME=BTCUSD"
set MT5_LOGIN=
set MT5_PASSWORD=
set MT5_SERVER=
rem The challenge and the verification may hold over the weekend. A funded FTMO Account of the Standard type may not:
rem set WEEKEND_CLOSE=16:45 there, and every position is closed Friday 16:45 New York with no new one until Sunday.
set "WEEKEND_CLOSE="
set "COMMON=--broker mt5 --execute --no-approval --account-size %ACCOUNT% --journal journal_ftmo/trades.csv --tag FTMO"
if defined WEEKEND_CLOSE set "COMMON=%COMMON% --weekend-close %WEEKEND_CLOSE%"
(
  git pull --ff-only
  start "FTMO EURUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live.yaml live --symbol EURUSD %COMMON%"
  start "FTMO XAUUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_gold.yaml live --symbol XAUUSD %COMMON%"
  start "FTMO GBPUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live.yaml live --symbol GBPUSD %COMMON%"
  start "FTMO NAS100" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_nas100.yaml live --symbol NAS100 --mt5-symbol %NAS_NAME% %COMMON%"
  start "FTMO BTCUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_btc.yaml live --symbol BTCUSD --mt5-symbol %BTC_NAME% %COMMON%"
)
