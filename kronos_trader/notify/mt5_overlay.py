"""Write the Kronos forecast to a file the MT5 indicator (mt5/KronosForecast.mq5) draws on the chart.

The file goes to the terminal's *common* files folder so every chart can read
it: ``%APPDATA%\\MetaQuotes\\Terminal\\Common\\Files`` on Windows (override with
``MT5_FILES_DIR``).  One line per future candle, ``time;open;high;low;close``
with the time in the broker's server time as epoch seconds, after a header
``# direction;confidence;pct_change;expected_high;expected_low``.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd

from ..core.types import ForecastSummary
from .chart import forecast_rows


def common_files_dir() -> Path:
    override = os.environ.get("MT5_FILES_DIR")
    if override:
        return Path(override)
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"
    return Path("charts") / "mt5"


def write_forecast_file(symbol: str, forecast: ForecastSummary, last_time: pd.Timestamp, timeframe,
                        server_offset: pd.Timedelta = pd.Timedelta(0), directory: Optional[Path] = None,
                        mt5_symbol: Optional[str] = None) -> Optional[Path]:
    directory = Path(directory) if directory is not None else common_files_dir()
    # MT5 reads the exact _Symbol, including the broker's case-sensitive suffix.
    path = directory / f"kronos_forecast_{mt5_symbol or symbol}.csv"
    rows = forecast_rows(forecast, last_time, timeframe, server_offset)
    if not rows:
        path.unlink(missing_ok=True)
        return None
    directory.mkdir(parents=True, exist_ok=True)
    lines = [f"# {forecast.direction.name.lower()};{forecast.confidence:.4f};{forecast.pct_change:.4f};"
             f"{forecast.expected_high:.6f};{forecast.expected_low:.6f}"]
    lines += [f"{t};{o:.6f};{h:.6f};{l:.6f};{c:.6f}" for t, o, h, l, c in rows]
    # The indicator must see a complete forecast, never a partially written file.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", dir=directory, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write("\n".join(lines) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path
