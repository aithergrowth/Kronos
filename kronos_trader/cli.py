"""Command-line interface.

    python -m kronos_trader scan      --symbol EURUSD --data-dir data/tv_cache
    python -m kronos_trader backtest  --symbol 09988 --csv finetune_csv/data/HK_ali_09988_kline_5min_all.csv --base-tf 5m --step-tf 15m
    python -m kronos_trader forecast  --csv data.csv --tf 1H --horizon 12
    python -m kronos_trader import-tv --symbol OANDA:EURUSD --tf 4H --json bars.json
    python -m kronos_trader telegram-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .config import Settings
from .core.candles import CandleSeries
from .core.timeframe import BIAS_TIMEFRAMES, Timeframe
from .data.resample import MultiTimeframeData
from .data.tv_cache import load_all, save_payload, save_series
from .notify.formatting import format_analysis, format_forecast
from .notify.telegram import TelegramNotifier
from .strategy.engine import StrategyEngine

DEFAULT_TIMEFRAMES = [Timeframe.MIN_5, Timeframe.MIN_15, Timeframe.H_1, Timeframe.H_4, Timeframe.D_1, Timeframe.W_1, Timeframe.MN_1]


def _load_settings(args) -> Settings:
    settings = Settings.load(getattr(args, "config", None))
    kronos_mode = getattr(args, "kronos", None)
    if kronos_mode:
        settings.kronos.mode = kronos_mode
    if getattr(args, "first_candle", False):
        settings.confirmation.allow_first_candle = True
    if getattr(args, "no_first_candle", False):
        settings.confirmation.allow_first_candle = False
    if getattr(args, "risk", None):
        settings.risk.risk_pct = args.risk
    if getattr(args, "account", None):
        settings.account_size = args.account
    return settings


def _ensure_symbol(settings: Settings, symbol: str) -> str:
    key = symbol.upper()
    if key not in settings.symbols:
        from .config import SymbolSpec
        print(f"[warn] no SymbolSpec for {key}; using pip_size=0.01, pip_value_per_lot=1.0 - add it to config for real sizing")
        settings.symbols[key] = SymbolSpec(key, 0.01, 1.0, price_decimals=2)
    return key


def _load_data(args, settings: Settings, symbol: str) -> MultiTimeframeData:
    if getattr(args, "csv", None):
        base_tf = Timeframe.parse(args.base_tf)
        base = CandleSeries.from_csv(args.csv, base_tf, symbol=symbol)
        tfs = [tf for tf in DEFAULT_TIMEFRAMES if tf >= base_tf]
        return MultiTimeframeData.from_base(base, tfs, session_offset_hours=getattr(args, "session_offset", 0.0) or 0.0)
    data_dir = getattr(args, "data_dir", None) or settings.tradingview.cache_dir
    found = load_all(data_dir, symbol)
    if not found:
        spec = settings.symbols.get(symbol)
        alt = spec.tradingview_symbol if spec else None
        if alt:
            found = load_all(data_dir, alt)
    if not found:
        raise SystemExit(f"no cached candles for {symbol} in {data_dir}; use --csv or import-tv first")
    return MultiTimeframeData(found)


def _plain(html_text: str) -> str:
    """Telegram HTML -> terminal text."""
    import html
    import re
    return html.unescape(re.sub(r"</?(b|i|code)>", "", html_text))


def _forecaster(settings: Settings):
    if settings.kronos.mode == "off":
        return None
    from .indicators.kronos_forecast import KronosForecaster
    return KronosForecaster(settings.kronos)


# ------------------------------------------------------------------ commands

def cmd_scan(args) -> int:
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    data = _load_data(args, settings, symbol)
    print(data.describe())
    engine = StrategyEngine(settings, _forecaster(settings))
    views = data.as_of(pd.Timestamp(args.at)) if args.at else data.series
    analysis = engine.analyze(symbol, views, max_confirmation_age=args.max_age, compute_forecasts=args.forecasts)
    spec = settings.symbol(symbol)
    if args.json:
        print(json.dumps(analysis.to_dict(), indent=2, default=str))
    else:
        print(_plain(format_analysis(analysis, spec)))
        if args.verbose:
            for tf, tb in analysis.biases.items():
                print(f"\n[{tf.label}] {tb.bias}")
                for note in tb.notes:
                    print("   ", note)
            print("\nPOIs:")
            for p in analysis.pois:
                print("   ", p.describe())
            print("\nRejections:")
            for r in analysis.rejections:
                print("   ", r)
    if args.telegram:
        TelegramNotifier(params=settings.telegram).send_analysis(analysis, spec)
    return 0


def cmd_backtest(args) -> int:
    from .backtest.runner import Backtester
    from .backtest.report import format_report
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    data = _load_data(args, settings, symbol)
    print(data.describe())
    bt = Backtester(settings, data, symbol, step_tf=args.step_tf, forecaster=_forecaster(settings),
                    start=args.start, end=args.end, use_spread=not args.no_spread, progress=args.progress)
    result = bt.run()
    print(format_report(result))
    if args.out:
        result.trades_frame().to_csv(args.out, index=False)
        print(f"trades written to {args.out}")
    return 0


def cmd_forecast(args) -> int:
    settings = _load_settings(args)
    from .indicators.kronos_forecast import KronosForecaster
    tf = Timeframe.parse(args.tf)
    series = CandleSeries.from_csv(args.csv, tf, symbol=args.symbol)
    if args.paths:
        settings.kronos.n_paths = args.paths
    if args.horizon:
        settings.kronos.horizon = args.horizon
    fc = KronosForecaster(settings.kronos)
    print(f"loading {settings.kronos.model} ...")
    summary = fc.forecast(series)
    print(format_forecast(summary))
    mean = fc.mean_path()
    if mean is not None:
        print(mean.round(5).to_string())
    return 0


def cmd_import_tv(args) -> int:
    settings = _load_settings(args)
    payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
    tf = Timeframe.parse(args.tf)
    path = save_payload(payload, tf, args.data_dir or settings.tradingview.cache_dir, args.symbol)
    print(f"saved {path}")
    return 0


def cmd_resample(args) -> int:
    base = CandleSeries.from_csv(args.csv, Timeframe.parse(args.base_tf), symbol=args.symbol)
    from .data.resample import resample
    out = resample(base, Timeframe.parse(args.to), args.session_offset or 0.0)
    if args.out:
        out.df.to_csv(args.out, index=False)
        print(f"{out} -> {args.out}")
    else:
        print(out.df.tail(20).to_string())
    return 0


def cmd_telegram_test(args) -> int:
    settings = _load_settings(args)
    notifier = TelegramNotifier(params=settings.telegram)
    if not notifier.configured:
        print("set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID first")
        return 1
    notifier.test()
    print("sent")
    return 0


def cmd_tv_tools(args) -> int:
    settings = _load_settings(args)
    from .data.tradingview_mcp import TradingViewMCPClient
    client = TradingViewMCPClient(settings.tradingview.url, settings.tradingview.token)
    for tool in client.discover_tools():
        print(f"{tool['name']:40s} {tool.get('description', '')[:90]}")
    return 0


# ------------------------------------------------------------------ parser

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kronos_trader", description="Dorus Wanders rules + Kronos forecasts")
    p.add_argument("--config", help="YAML settings file (default: KRONOS_TRADER_CONFIG or built-in defaults)")
    sub = p.add_subparsers(dest="command", required=True)

    def data_args(sp):
        sp.add_argument("--symbol", required=True)
        sp.add_argument("--csv", help="base-timeframe CSV to resample from")
        sp.add_argument("--base-tf", default="5m", help="timeframe of the CSV (default 5m)")
        sp.add_argument("--data-dir", help="cache directory with <SYMBOL>_<TF>.csv files")
        sp.add_argument("--session-offset", type=float, default=0.0, help="hours to shift daily/weekly boundaries")
        sp.add_argument("--kronos", choices=["off", "advisory", "filter"], help="Kronos indicator mode")
        sp.add_argument("--first-candle", action="store_true", help="allow first bullish/bearish candle confirmations")
        sp.add_argument("--no-first-candle", action="store_true")
        sp.add_argument("--risk", type=float, help="risk per trade in %")
        sp.add_argument("--account", type=float, help="account size")

    sp = sub.add_parser("scan", help="analyse the latest candles and print / send the decision")
    data_args(sp)
    sp.add_argument("--at", help="analyse as of this UTC timestamp instead of the latest candle")
    sp.add_argument("--max-age", type=int, default=3, help="accept confirmations up to N candles old")
    sp.add_argument("--forecasts", action="store_true", help="also run advisory Kronos forecasts")
    sp.add_argument("--telegram", action="store_true")
    sp.add_argument("--json", action="store_true")
    sp.add_argument("-v", "--verbose", action="store_true")
    sp.set_defaults(func=cmd_scan)

    sp = sub.add_parser("backtest", help="walk-forward backtest with the paper broker")
    data_args(sp)
    sp.add_argument("--step-tf", default=None, help="candle size to step through (default: lowest available)")
    sp.add_argument("--start")
    sp.add_argument("--end")
    sp.add_argument("--no-spread", action="store_true")
    sp.add_argument("--progress", action="store_true")
    sp.add_argument("--out", help="write the trade list to this CSV")
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("forecast", help="run the Kronos indicator on a CSV")
    sp.add_argument("--csv", required=True)
    sp.add_argument("--tf", required=True)
    sp.add_argument("--symbol")
    sp.add_argument("--horizon", type=int)
    sp.add_argument("--paths", type=int)
    sp.set_defaults(func=cmd_forecast)

    sp = sub.add_parser("import-tv", help="store a saved mcp-tv-get-ohlcv JSON payload in the cache")
    sp.add_argument("--symbol", required=True)
    sp.add_argument("--tf", required=True)
    sp.add_argument("--json", required=True)
    sp.add_argument("--data-dir")
    sp.set_defaults(func=cmd_import_tv)

    sp = sub.add_parser("resample", help="resample a CSV to a higher timeframe")
    sp.add_argument("--csv", required=True)
    sp.add_argument("--base-tf", required=True)
    sp.add_argument("--to", required=True)
    sp.add_argument("--symbol")
    sp.add_argument("--session-offset", type=float)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_resample)

    sp = sub.add_parser("telegram-test", help="send a test message")
    sp.set_defaults(func=cmd_telegram_test)

    sp = sub.add_parser("tv-tools", help="list tools of the TradingView MCP server (needs TRADINGVIEW_MCP_TOKEN)")
    sp.set_defaults(func=cmd_tv_tools)
    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
