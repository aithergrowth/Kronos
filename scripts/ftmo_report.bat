@echo off
rem The forward record of the FTMO account: every position against the bot's plan in journal_ftmo\trades.csv, fills,
rem slippage, commission and swap, R before and after costs, the code each trade ran on, and the account against the
rem product's loss limits (what is left today and in total, open risk to every stop, manual positions included).
rem Reads only: it sends no order and changes nothing. Writes journal_ftmo\report\forward_report.html and opens it.
rem Your own values (ACCOUNT, NAS_NAME, BTC_NAME, PRODUCT) come from scripts\ftmo_local.bat, as for start_ftmo.bat.
cd /d "%~dp0.."
set "MT5_PATH=C:\Program Files\FTMO MetaTrader 5\terminal64.exe"
rem FTMO's own installer puts the terminal here (6 October, Max's laptop)
if exist "C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe" set "MT5_PATH=C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe"
set "ACCOUNT=10000"
set "NAS_NAME=US100.cash"
set "BTC_NAME=BTCUSD"
set "PRODUCT=ftmo_2step"
if exist "%~dp0ftmo_local.bat" call "%~dp0ftmo_local.bat"
set MT5_LOGIN=
set MT5_PASSWORD=
set MT5_SERVER=
set "PY=.\.venv\Scripts\python.exe"
%PY% -m kronos_trader --config config/dorus_live.yaml forward-report --journal journal_ftmo/trades.csv --product %PRODUCT% --account-size %ACCOUNT% --mt5-names NAS100=%NAS_NAME%,BTCUSD=%BTC_NAME%
if exist "journal_ftmo\report\forward_report.html" start "" "journal_ftmo\report\forward_report.html"
pause
