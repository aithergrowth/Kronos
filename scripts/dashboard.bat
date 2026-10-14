@echo off
rem The dashboard of the FTMO windows: one page in the browser with every window's last scan (red when it stopped),
rem the open positions and resting limits as journal_ftmo\trades.csv knows them, today's and the week's closes with R
rem and P&L, the room under the guard's floors, the last briefing per market, the last events, the newest chart images
rem and the latest parity check. Reads only: it sends no order, asks the terminal nothing and changes nothing of the
rem windows; it may run while they trade. The page is rebuilt every minute and reloads itself in the browser.
rem It is served on this computer only (http://127.0.0.1:8765/); close this window to stop it.
rem Your own values (ACCOUNT, PRODUCT) come from scripts\ftmo_local.bat, as for start_ftmo.bat.
cd /d "%~dp0.."
set "ACCOUNT=10000"
set "PRODUCT=ftmo_2step"
if exist "%~dp0ftmo_local.bat" call "%~dp0ftmo_local.bat"
set MT5_LOGIN=
set MT5_PASSWORD=
set MT5_SERVER=
set "PYTHONUTF8=1"
set "PY=.\.venv\Scripts\python.exe"
if not defined PRODUCT set "PRODUCT=ftmo_2step"
rem the browser opens once, 4 seconds later, when the page is built and served (a detached cmd waits with ping)
start "" /min cmd /c "ping -n 5 127.0.0.1 >nul & start "" http://127.0.0.1:8765/"
%PY% -m kronos_trader dashboard --journal journal_ftmo/trades.csv --charts charts --out journal_ftmo/dashboard/index.html --every 60 --serve 8765 --account-size %ACCOUNT% --product %PRODUCT%
pause
