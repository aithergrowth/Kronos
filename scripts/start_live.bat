@echo off
rem Start the live windows: EURUSD, XAUUSD and GBPUSD on the MT5 demo, orders without the Approve tap, and
rem BTCUSD on Bitstamp prices with paper fills. Double-click this file in Explorer, or run scripts\start_live.bat.
rem Before: MT5 open and logged in, Algo Trading on. To stop a market, press Ctrl+C in its window or close it.
rem NAS100 is left out: MetaQuotes-Demo has no Nasdaq-100 (5 October: the window ran on stale cached bars).
rem Your own settings go in scripts\live_local.bat (not in git, so an update never clashes with them), e.g.
rem   set "MT5_PATH=D:\MetaTrader 5\terminal64.exe"
rem The pull and the windows sit in one block that ends with exit /b: cmd reads the whole block before it runs it and
rem stops after it, so a pull that updates this file cannot run lines of the new version (a second window).
cd /d "%~dp0.."
rem The demo terminal by its own path, also when MT5_PATH points at another terminal: a window must never log the FTMO
rem terminal in to the demo account.
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" set "MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe"
if exist "%~dp0live_local.bat" call "%~dp0live_local.bat"
set "PY=.\.venv\Scripts\python.exe"
(
  git pull --ff-only || (echo. & echo UPDATE FAILED: the windows start on the code already here. Read the message above. & pause)
  start "EURUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live.yaml live --symbol EURUSD --broker mt5 --execute --no-approval"
  start "XAUUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live_gold.yaml live --symbol XAUUSD --broker mt5 --execute --no-approval"
  start "GBPUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live.yaml live --symbol GBPUSD --broker mt5 --execute --no-approval"
  start "BTCUSD" powershell -NoExit -Command "%PY% -m kronos_trader --config config/dorus_live_btc.yaml live --symbol BTCUSD --broker paper --feed bitstamp --account-size 10000 --execute --no-approval"
  exit /b
)
