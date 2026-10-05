@echo off
rem Start the three live windows: EURUSD and XAUUSD on the MT5 demo (orders without the Approve tap) and
rem BTCUSD on Bitstamp prices with paper fills. Double-click this file in Explorer, or run scripts\start_live.bat.
rem Before: MT5 open and logged in, Algo Trading on. To stop a market, press Ctrl+C in its window or close it.
cd /d "%~dp0.."
rem the latest profiles first; when the pull fails (no network) the windows start on the code already here
git pull --ff-only
start "EURUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live.yaml live --symbol EURUSD --broker mt5 --execute --no-approval"
start "XAUUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_gold.yaml live --symbol XAUUSD --broker mt5 --execute --no-approval"
start "BTCUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_btc.yaml live --symbol BTCUSD --broker paper --feed bitstamp --account-size 10000 --execute --no-approval"
