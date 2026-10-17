@echo off
rem The weekly parity check: the week of the FTMO journal (journal_ftmo\trades.csv) against a backtest of the same week on
rem the FTMO terminal's own candles, every market with the settings its window ran (its start record, journal_ftmo\starts).
rem Every signal on both sides by its setup id: match, outcome differs, backtest only, live only, and why they differ.
rem Reads only: it sends no order and changes nothing of the windows; it may run while they trade.
rem Writes journal_ftmo\parity\parity_<the week's Monday>.md (+ .csv, and the candles it used) and sends the summary to Telegram.
rem When: Friday evening (the week so far) or on a Monday (then it checks the week before). Another week:
rem   scripts\parity_week.bat --week last          scripts\parity_week.bat --week 2026-10-05
rem Your own values (MT5_PATH, ACCOUNT, NAS_NAME, BTC_NAME, PRODUCT) come from scripts\ftmo_local.bat, as for start_ftmo.bat.
rem Without the pause at the end (Windows Task Scheduler, Claude Code): scripts\parity_week_auto.bat
cd /d "%~dp0.."
set "MT5_PATH=C:\Program Files\FTMO MetaTrader 5\terminal64.exe"
rem FTMO's own installer puts the terminal here (6 October, Max's laptop)
if exist "C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe" set "MT5_PATH=C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe"
set "ACCOUNT=10000"
set "NAS_NAME=US100.cash"
set "BTC_NAME=BTCUSD"
set "PRODUCT="
if exist "%~dp0ftmo_local.bat" call "%~dp0ftmo_local.bat"
set MT5_LOGIN=
set MT5_PASSWORD=
set MT5_SERVER=
set "PYTHONUTF8=1"
set "PY=.\.venv\Scripts\python.exe"
set "EXTRA="
if defined PRODUCT set "EXTRA=--product %PRODUCT%"
%PY% -m kronos_trader --config config/dorus_live.yaml parity --journal journal_ftmo/trades.csv --account-size %ACCOUNT% --mt5-names NAS100=%NAS_NAME%,BTCUSD=%BTC_NAME% %EXTRA% --tag FTMO --telegram %*
set "RESULT=%ERRORLEVEL%"
if defined PARITY_AUTO exit /b %RESULT%
echo.
echo The report is the newest journal_ftmo\parity\parity_*.md (open it in Notepad, or ask Claude Code to explain it).
pause
