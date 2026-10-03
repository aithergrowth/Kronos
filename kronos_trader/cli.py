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


def _calendar(settings: Settings):
    """High-impact news calendar from settings.news (None when the blackout is disabled)."""
    if not settings.news.enabled:
        return None
    from .data.calendar import NewsCalendar, load_events
    n = settings.news
    return NewsCalendar(load_events(n.calendar_csv), n.before_minutes, n.after_minutes, n.min_importance)


def _engine(settings: Settings) -> StrategyEngine:
    return StrategyEngine(settings, _forecaster(settings), calendar=_calendar(settings))


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
    engine = _engine(settings)
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
    from .backtest.provenance import code_snapshot, write_provenance
    code = code_snapshot()          # the program loaded now, before the run; recorded as such in the provenance
    print(f"code: {code.get('commit')} source {code['source_sha256'][:12]}{' (uncommitted changes)' if code.get('dirty') else ''}")
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    data = _load_data(args, settings, symbol)
    print(data.describe())
    bt = Backtester(settings, data, symbol, step_tf=args.step_tf, engine=_engine(settings),
                    start=args.start, end=args.end, use_spread=not args.no_spread, progress=args.progress,
                    quote_basis=args.quote_basis, dossier_dir=args.dossier_dir, dossier_limit=args.dossier_limit)
    cal = getattr(bt.engine, "calendar", None)
    if settings.news.enabled:
        events = getattr(cal, "events", None) or []
        if events:
            times = [e.time for e in events]
            print(f"news calendar: {len(events)} events {min(times)} -> {max(times)} ({settings.news.calendar_csv})")
        else:
            print(f"news calendar: ENABLED BUT EMPTY ({settings.news.calendar_csv}): no blackout applied")
    result = bt.run()
    print(format_report(result))
    if result.zones_by_reason:
        print("  distinct zones behind the rejections (bars above count every candle):")
        for key, n in sorted(result.zones_by_reason.items(), key=lambda kv: -kv[1])[:12]:
            print(f"    {n:6d}  {key}")
    if args.out:
        result.trades_frame().to_csv(args.out, index=False)
        out = Path(args.out)
        pd.DataFrame(result.equity_curve, columns=["time", "equity"]).to_csv(out.with_suffix(".equity.csv"), index=False)
        write_provenance(out.with_suffix(".provenance.json"), settings=settings, symbol=symbol,
                         data_dir=getattr(args, "data_dir", None) or settings.tradingview.cache_dir, result=result,
                         quote_basis=args.quote_basis, code=code)
        print(f"trades written to {args.out} (+ .equity.csv, .provenance.json)")
    return 0


def cmd_trade_charts(args) -> int:
    from .backtest.charts import render_trade_charts
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    data = _load_data(args, settings, symbol)
    trades = pd.read_csv(args.trades)
    if "symbol" in trades.columns:
        trades = trades[trades["symbol"].str.upper() == symbol.upper()]
    paths = render_trade_charts(settings, data, symbol, trades, args.out, engine=_engine(settings),
                                max_charts=args.max, lookback=args.lookback, max_zones=args.zones, blind=args.blind)
    for path in paths:
        print(path)
    print(f"{len(paths)} charts in {args.out}")
    return 0


def cmd_decision_dossier(args) -> int:
    from .backtest.dossier import write_decision_dossier
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    data = _load_data(args, settings, symbol)
    out = write_decision_dossier(settings, data, symbol, args.at, args.out, engine=_engine(settings), lookback=args.lookback,
                                 warmup_days=args.warmup_days, assume=args.assume)
    print(f"dossier written to {out}")
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


def _broker(args, settings: Settings):
    kind = getattr(args, "broker", "none")
    if kind == "none":
        return None
    if kind == "paper":
        from .execution.paper import PaperBroker
        return PaperBroker(settings)
    if kind == "ibkr":
        from .execution.ibkr import IBKRBroker
        return IBKRBroker(settings)
    if kind == "mt5":
        from .execution.mt5 import MT5Broker
        return MT5Broker(settings)
    raise SystemExit(f"unknown broker {kind}")


def _feed(args, settings: Settings, broker):
    """Live candle source: 'broker' (IBKR / MT5 bars), 'oanda' (practice API) or 'cache' (TradingView CSVs only)."""
    kind = getattr(args, "feed", None)
    if kind is None:
        kind = "broker" if getattr(args, "broker", "none") in ("ibkr", "mt5") else "cache"
    if kind == "broker" and broker is None:
        raise SystemExit("--feed broker needs --broker ibkr or mt5")
    feed = None
    if kind == "oanda":
        from .data.oanda import OandaFeed
        feed = OandaFeed(settings=settings)
    return kind, feed


def cmd_live(args) -> int:
    from .live import LiveRunner, build_fetch
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    broker = _broker(args, settings)
    data_dir = args.data_dir or settings.tradingview.cache_dir
    kind, feed = _feed(args, settings, broker)
    fetch = build_fetch(settings, symbol, cache_dir=data_dir, broker=broker if kind == "broker" else None,
                        broker_timeframes=[] if kind == "cache" else None, feed=feed)
    notifier = TelegramNotifier(params=settings.telegram)
    runner = LiveRunner(settings, symbol, fetch, broker=broker, notifier=notifier,
                        engine=_engine(settings),
                        dry_run=not args.execute, require_approval=not args.no_approval,
                        notify_every_scan=args.notify_every_scan)
    mode = "EXECUTE" if args.execute else "dry-run"
    print(f"live {symbol}: broker={args.broker} feed={kind} mode={mode} approval={'off' if args.no_approval else 'on'} "
          f"telegram={'on' if notifier.configured else 'dry-run'} poll={args.poll}s")
    if args.once:
        print("scanning... (the first scan loads Kronos and can take a minute or two)")
        analysis = runner.step()
        print(_plain(format_analysis(analysis, settings.symbol(symbol))))
        return 0
    runner.run_forever(args.poll)
    return 0


def cmd_ibkr_test(args) -> int:
    from .execution.ibkr import IBKRBroker
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    broker = IBKRBroker(settings)
    diag = broker.diagnostics()
    print(f"connected to {settings.ibkr.host}:{settings.ibkr.port}  accounts {diag['accounts']}  "
          f"base currency {diag['base_currency']}")
    for tag in ("NetLiquidation", "TotalCashValue", "AvailableFunds", "BuyingPower", "UnrealizedPnL", "RealizedPnL"):
        print(f"  {tag:16s} {diag.get(tag) or '-'}")
    equity = broker.equity()
    print(f"equity {equity:,.2f} {diag['base_currency']}  balance {broker.balance():,.2f}")
    if equity <= 0:
        print("  !! equity is 0: the paper account has no funds. Client Portal -> Settings -> Paper Trading Account -> reset the balance.")
    if diag["base_currency"] != settings.account_currency:
        print(f"  note: account base currency is {diag['base_currency']}, settings.account_currency is {settings.account_currency}")
    print("contract:", broker.contract(symbol))
    bars = broker.get_candles(symbol, Timeframe.parse(args.tf), 5)
    print(bars.df.to_string())
    try:
        print("price:", broker.current_price(symbol))
    except Exception as exc:
        print("price: FAILED -", exc)
    broker.disconnect()
    return 0


def cmd_mt5_test(args) -> int:
    from .execution.mt5 import MT5Broker
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    broker = MT5Broker(settings)
    d = broker.diagnostics()
    algo = "on" if d["algo_trading"] else "OFF (click 'Algo Trading' in the terminal toolbar before --execute)"
    account = "allowed" if d["account_trade_allowed"] else "NOT allowed (investor login: use the master password)"
    print(f"connected: {d['connected']}  terminal {d['version']}")
    print(f"algo trading: {algo}  account trading: {account}")
    print(f"account {d['login']} on {d['server']}  {d['currency']}  balance {d['balance']}  equity {d['equity']}  leverage 1:{d['leverage']}")
    print(f"server time offset to UTC: {d['server_offset']}")
    print(f"symbol: {broker.mt5_symbol(symbol)}")
    bars = broker.get_candles(symbol, Timeframe.parse(args.tf), 5)
    print(bars.df.to_string())
    print("price:", broker.current_price(symbol))
    broker.disconnect()
    return 0


def cmd_dukascopy(args) -> int:
    """Pull Dukascopy day files and build the engine cache for a symbol."""
    import datetime as dt
    from .data.dukascopy import build_cache, fetch_days
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    instrument = args.instrument or symbol
    if not args.build_only:
        counts = fetch_days(instrument, dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end), args.raw_dir,
                            pause=args.pause, progress=print)
        print("download:", counts)
    kwargs = {}
    if args.timeframes:
        kwargs["timeframes"] = [Timeframe.parse(t.strip()) for t in args.timeframes.split(",") if t.strip()]
    written = build_cache(symbol, instrument, args.raw_dir, args.out_dir, session_offset_hours=args.session_offset, **kwargs)
    print("cache written:", written, "->", args.out_dir)
    return 0


def cmd_histdata(args) -> int:
    """Pull HistData.com 1-minute history (past years whole, this year by month) and build the engine cache."""
    from .data.histdata import build_cache, fetch_history
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    pair = args.pair or symbol
    end_year, end_month = (int(x) for x in args.to.split("-"))
    minutes = fetch_history(pair, int(args.start_year), end_year, end_month, args.raw_dir, pause=args.pause, progress=print)
    tfs = [Timeframe.parse(t.strip()) for t in args.timeframes.split(",")] if args.timeframes else None
    kwargs = {"timeframes": tfs} if tfs else {}
    written = build_cache(symbol, pair, args.raw_dir, args.out_dir, session_offset_hours=args.session_offset, minutes=minutes,
                          session_tz=args.session_tz or None, **kwargs)
    print(f"{len(minutes)} minute candles {minutes['timestamp'].iloc[0]} -> {minutes['timestamp'].iloc[-1]}; cache written: {written} -> {args.out_dir}")
    return 0


def cmd_journal(args) -> int:
    from .journal import format_summary, summary
    print(format_summary(summary(args.path)))
    return 0


def cmd_feed_test(args) -> int:
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    from .data.oanda import OandaFeed
    feed = OandaFeed(settings=settings)
    series = feed.get_candles(symbol, Timeframe.parse(args.tf), 5)
    print(f"{symbol} {args.tf} from OANDA {feed.environment}:")
    print(series.df.to_string())
    print("price:", feed.current_price(symbol))
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
        sp.add_argument("--risk", type=float, help="risk per trade in %%")
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
    sp.add_argument("--quote-basis", choices=("mid", "bid"), default="mid",
                    help="what the candles are: mid prices (default) or bid quotes (HistData, Dukascopy bid files)")
    sp.add_argument("--progress", action="store_true")
    sp.add_argument("--dossier-dir", help="write a decision dossier (charts, bias notes, gaps, zones, rejections) at every signal, from the run's own engine state")
    sp.add_argument("--dossier-limit", type=int, default=200, help="at most this many dossiers per run")
    sp.add_argument("--out", help="write the trade list to this CSV")
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("trade-charts", help="draw backtest trades (zone, X/B/P, entry, stop, target) as PNG images")
    data_args(sp)
    sp.add_argument("--trades", required=True, help="trade list CSV written by `backtest --out`")
    sp.add_argument("--out", default="charts/backtest", help="directory for the images")
    sp.add_argument("--max", type=int, default=20, help="at most this many charts, spread over the list (0 = all)")
    sp.add_argument("--lookback", type=int, default=120, help="candles on each image")
    sp.add_argument("--zones", type=int, default=3, help="other zones drawn besides the trade's own")
    sp.add_argument("--blind", action="store_true", help="hide the outcome (result, exit reason): for judging a chart against a source example")
    sp.set_defaults(func=cmd_trade_charts)

    sp = sub.add_parser("decision-dossier", help="everything the engine saw at one moment: a chart per timeframe, bias notes, gaps kept and dropped, zones, rejections, setup")
    data_args(sp)
    sp.add_argument("--at", required=True, help="UTC timestamp, e.g. '2024-03-13 10:35'")
    sp.add_argument("--out", required=True, help="folder for README.md, dossier.json and the charts")
    sp.add_argument("--lookback", type=int, default=120, help="candles on each chart")
    sp.add_argument("--warmup-days", type=float, default=0.0, help="replay this many days before the moment first, so zone visits are counted with history (slow: ~15 s per day)")
    sp.add_argument("--assume", choices=["long", "short"], help="diagnostic: walk on in this direction past a refusing bias/session/news gate and report every later refusal (never a signal)")
    sp.set_defaults(func=cmd_decision_dossier)

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

    sp = sub.add_parser("live", help="run the live loop: cache + broker bars -> engine -> Telegram (approve) -> broker")
    data_args(sp)
    sp.add_argument("--broker", choices=["none", "paper", "ibkr", "mt5"], default="none")
    sp.add_argument("--execute", action="store_true", help="send real orders (default: dry-run, Telegram only)")
    sp.add_argument("--no-approval", action="store_true", help="execute without the Telegram approve step")
    sp.add_argument("--poll", type=int, default=60, help="seconds between scans")
    sp.add_argument("--once", action="store_true", help="run a single scan and exit")
    sp.add_argument("--notify-every-scan", action="store_true")
    sp.add_argument("--feed", choices=["broker", "oanda", "cache"],
                    help="live candle source (default: broker bars with --broker ibkr/mt5, otherwise the cache)")
    sp.set_defaults(func=cmd_live)

    sp = sub.add_parser("ibkr-test", help="connect to TWS / IB Gateway and print account, contract, price and bars")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--tf", default="15m")
    sp.set_defaults(func=cmd_ibkr_test)
    sp = sub.add_parser("feed-test", help="pull the last bars from the OANDA feed (needs OANDA_TOKEN)")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--tf", default="15m")
    sp.set_defaults(func=cmd_feed_test)

    sp = sub.add_parser("mt5-test", help="connect to the MetaTrader 5 terminal and print account, server time offset and bars")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--tf", default="15m")
    sp.set_defaults(func=cmd_mt5_test)
    sp = sub.add_parser("dukascopy", help="free Dukascopy history: pull 1-minute day files and build the cache for a symbol")
    sp.add_argument("--symbol", required=True)
    sp.add_argument("--instrument", help="Dukascopy instrument name (default: the symbol)")
    sp.add_argument("--start", required=True, help="first day, YYYY-MM-DD")
    sp.add_argument("--end", required=True, help="last day, YYYY-MM-DD")
    sp.add_argument("--raw-dir", default="data/dukascopy/raw")
    sp.add_argument("--out-dir", default="data/dukascopy")
    sp.add_argument("--pause", type=float, default=0.4, help="seconds between requests (the feed rate-limits)")
    sp.add_argument("--session-offset", type=float, default=3.0, help="hours: 3 = the day and the 4H bins start at 21:00 UTC")
    sp.add_argument("--build-only", action="store_true", help="skip the download, decode what is on disk")
    sp.add_argument("--timeframes", help="comma list to write, e.g. 5m,15m,1H,4H (default: 5m to 1M)")
    sp.set_defaults(func=cmd_dukascopy)

    sp = sub.add_parser("journal", help="win rate, expectancy and R:R of the forward test from journal/trades.csv")
    sp.add_argument("--path", default="journal/trades.csv")
    sp.set_defaults(func=cmd_journal)
    sp = sub.add_parser("histdata", help="free HistData.com 1-minute history: past years whole, this year by month; builds the cache")
    sp.add_argument("--symbol", required=True)
    sp.add_argument("--pair", help="HistData pair name (default: the symbol)")
    sp.add_argument("--start-year", required=True, type=int)
    sp.add_argument("--to", required=True, help="last month, YYYY-MM")
    sp.add_argument("--raw-dir", default="data/histdata/raw")
    sp.add_argument("--out-dir", default="data/histdata")
    sp.add_argument("--pause", type=float, default=1.5)
    sp.add_argument("--session-offset", type=float, default=3.0, help="fixed hours before midnight UTC for the session boundary when --session-tz is empty")
    sp.add_argument("--session-tz", default="America/New_York", help="time zone whose 17:00 ends the trading day (DST-aware); '' for the fixed offset")
    sp.add_argument("--timeframes", help="comma list to write, e.g. 5m,15m,1H,4H (default: 5m to 1M)")
    sp.set_defaults(func=cmd_histdata)
    return p


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
