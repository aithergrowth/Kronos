"""kronos_trader - a rules-based trading system built on the Dorus Wanders methodology.

Layers (see docs/ARCHITECTURE.md):

* ``core``        - timeframes, candle series, domain types
* ``strategy``    - the trading rules (bias, structure, POI, confirmation, risk, exits)
* ``indicators``  - the Kronos candle-forecast indicator
* ``data``        - CSV loading, resampling, TradingView MCP adapter
* ``execution``   - broker abstraction (paper + MetaTrader 5), prop-firm risk guard
* ``notify``      - Telegram notifications
* ``backtest``    - event-driven backtester and reporting
"""

__version__ = "0.1.0"
