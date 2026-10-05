@echo off
rem FTMO windows beside the demo: EURUSD, XAUUSD and NAS100 on the FTMO MT5 terminal, orders without the
rem Approve tap, their own journal (journal_ftmo\) and "[FTMO]" in front of every Telegram message.
rem Before: the FTMO terminal installed, logged in to the trial or challenge account, Algo Trading on (green).
rem The password stays in the terminal: MT5_LOGIN, MT5_PASSWORD and MT5_SERVER are cleared for these windows, so they
rem trade the account the FTMO terminal is logged in to. A window whose symbol the server lacks stops at the start.
rem
rem Your own values go in scripts\ftmo_local.bat (not in git, so an update never clashes with them), one per line:
rem   set "MT5_PATH=D:\FTMO MetaTrader 5\terminal64.exe"     the terminal (right-click its shortcut, Properties, Target)
rem   set "ACCOUNT=25000"                                     the challenge size: the guard's -4 %% day and -8 %% count from it
rem   set "NAS_NAME=US100.cash"                               the server's name for the Nasdaq-100
rem   set "FUNDED=1"                                          once funded: 1.0 %% risk (0.5 %% from -3 %%) and flat by Friday 15:45 New York
rem To list the server's names, in PowerShell in the Kronos folder:
rem   $env:MT5_PATH="C:\Program Files\FTMO MetaTrader 5\terminal64.exe"; Remove-Item Env:MT5_LOGIN,Env:MT5_PASSWORD,Env:MT5_SERVER -ErrorAction SilentlyContinue
rem   .\.venv\Scripts\python.exe -m kronos_trader mt5-symbols --search 100
rem Out since 5 October (docs/backtests/winrate/README.md): GBPUSD (-25.3R over 2017-2026 on the corrected clock) and BTCUSD
rem (2020-2025 about -2R, all its profit in 2026; in the challenge replay from 2020 it cut the funded share from 75 % to 42 %).
rem The pull and the windows sit in one block that ends with exit /b (see start_live.bat).
cd /d "%~dp0.."
set "MT5_PATH=C:\Program Files\FTMO MetaTrader 5\terminal64.exe"
set "ACCOUNT=10000"
set "NAS_NAME=US100.cash"
set "FUNDED="
set "WEEKEND_CLOSE="
if exist "%~dp0ftmo_local.bat" call "%~dp0ftmo_local.bat"
set MT5_LOGIN=
set MT5_PASSWORD=
set MT5_SERVER=
set "PY=.\.venv\Scripts\python.exe"
set "COMMON=--broker mt5 --execute --no-approval --account-size %ACCOUNT% --journal journal_ftmo/trades.csv --tag FTMO"
rem The challenge and the verification may hold over the weekend; a funded FTMO Account of the Standard type may not.
rem 15:45: an hour before the forex close, so US100.cash (whose Friday may end at 16:00 New York) is closed in time too
if defined FUNDED set "COMMON=%COMMON% --risk-pct 1.0 --drawdown-steps=-3:0.5 --weekend-close 15:45"
if not defined FUNDED if defined WEEKEND_CLOSE set "COMMON=%COMMON% --weekend-close %WEEKEND_CLOSE%"
(
  git pull --ff-only || (echo. & echo UPDATE FAILED: the windows start on the code already here. Read the message above. & pause)
  start "FTMO EURUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live.yaml live --symbol EURUSD %COMMON%"
  start "FTMO XAUUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live_gold.yaml live --symbol XAUUSD %COMMON%"
  start "FTMO NAS100" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live_nas100.yaml live --symbol NAS100 --mt5-symbol %NAS_NAME% %COMMON%"
  exit /b
)
