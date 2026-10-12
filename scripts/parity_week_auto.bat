@echo off
rem The weekly parity check without the pause at the end: for the Windows Task Scheduler (docs/LIVE_SETUP.md, "The weekly
rem parity check") and for Claude Code. The same arguments as scripts\parity_week.bat (e.g. --week last).
set "PARITY_AUTO=1"
call "%~dp0parity_week.bat" %*
