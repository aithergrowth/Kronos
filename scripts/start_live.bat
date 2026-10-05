@echo off
rem Start the live windows: EURUSD, XAUUSD and GBPUSD on the MT5 demo, orders without the Approve tap, and
rem BTCUSD on Bitstamp prices with paper fills. Double-click this file in Explorer, or run scripts\start_live.bat.
rem Before: MT5 open and logged in, Algo Trading on. To stop a market, press Ctrl+C in its window or close it.
rem NAS100 is left out: MetaQuotes-Demo has no Nasdaq-100 (5 October: the window ran on stale cached bars). On a
rem server that has it add a line like XAUUSD's with config/dorus_live_nas100.yaml, --symbol NAS100 and
rem --mt5-symbol NAME, e.g. US100.cash on FTMO (the names: python -m kronos_trader mt5-symbols --search 100).
rem The pull and the windows sit in one block: cmd reads the whole block before it runs it, so a pull that updates
rem this file cannot garble the lines still to come; the new version takes effect the next time. Without network
rem the pull fails and the windows start on the code already here.
cd /d "%~dp0.."
(
  git pull --ff-only
  start "EURUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live.yaml live --symbol EURUSD --broker mt5 --execute --no-approval"
  start "XAUUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_gold.yaml live --symbol XAUUSD --broker mt5 --execute --no-approval"
  start "GBPUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live.yaml live --symbol GBPUSD --broker mt5 --execute --no-approval"
  start "BTCUSD" powershell -NoExit -Command ".\.venv\Scripts\Activate.ps1; python -m kronos_trader --config config/dorus_live_btc.yaml live --symbol BTCUSD --broker paper --feed bitstamp --account-size 10000 --execute --no-approval"
)
