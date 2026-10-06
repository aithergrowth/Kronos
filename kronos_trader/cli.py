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
    try:
        settings = Settings.load(getattr(args, "config", None))
    except FileNotFoundError as exc:
        raise SystemExit(f"{exc}: not started (a missing profile would trade the built-in defaults). Check the --config path.")
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


def _apply_mt5_symbol(args, settings: Settings, symbol: str) -> None:
    """--mt5-symbol: the broker's own name for the market (MetaQuotes-Demo, prop firms: BTCUSD.x, XAUUSD.m), for this run."""
    name = getattr(args, "mt5_symbol", None)
    if name:
        settings.symbols[symbol].mt5_symbol = name


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


# FTMO's commission (October 2026, account currency USD): forex about 3 a 1.0 lot round turn, crypto 0.0325 % of the
# notional a side, metals and indices none (their cost is in the spread, which the backtest models separately)
FX_PAIRS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "EURGBP")
FTMO_COSTS = {**{pair: (3.0, 0.0) for pair in FX_PAIRS}, "BTCUSD": (0.0, 0.065), "ETHUSD": (0.0, 0.065)}


def cmd_backtest(args) -> int:
    from .backtest.runner import Backtester
    from .backtest.report import format_report
    from .backtest.provenance import code_snapshot, write_provenance
    code = code_snapshot()          # the program loaded now, before the run; recorded as such in the provenance
    print(f"code: {code.get('commit')} source {code['source_sha256'][:12]}{' (uncommitted changes)' if code.get('dirty') else ''}")
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    if getattr(args, "costs", "none") == "ftmo":
        spec = settings.symbol(symbol)
        spec.commission_per_lot, spec.commission_pct = FTMO_COSTS.get(symbol, (0.0, 0.0))
        print(f"costs: FTMO commission {spec.commission_per_lot:g} a lot + {spec.commission_pct:g} % of the notional, round turn")
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
    """Check the token with getMe, then the chat with a test message; name what is wrong when something is."""
    from .notify.telegram import TelegramError, masked
    settings = _load_settings(args)
    notifier = TelegramNotifier(params=settings.telegram)
    if not notifier.token:
        print("set TELEGRAM_BOT_TOKEN first: the API token from @BotFather (/mybots, your bot, API Token)")
        return 1
    try:
        bot = notifier.check()
    except TelegramError as exc:
        print(f"token rejected ({exc.status} {exc.description}): TELEGRAM_BOT_TOKEN must be the API token from "
              f"@BotFather, digits, a colon and 35 characters, without a 'bot' prefix; yours is {masked(notifier.token)}")
        return 1
    print(f"bot @{bot}: token ok")

    def seen() -> str:
        chats = notifier.chats_seen()
        if not chats:
            return f"no chat has messaged @{bot} yet (or longer than a day ago): open its chat, send it a message, run this again"
        return "chats that messaged the bot: " + ", ".join(f"{c['id']} ({c['name']})" for c in chats)

    if not notifier.chat_id:
        print(f"TELEGRAM_CHAT_ID is not set. {seen()}")
        return 1
    try:
        notifier.test()
    except TelegramError as exc:
        if exc.status in (400, 403):
            print(f"chat {notifier.chat_id} rejected ({exc.description}): check TELEGRAM_CHAT_ID. {seen()}")
            return 1
        raise
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
    """Live candle source: 'broker' (IBKR / MT5 bars), 'oanda' (practice API), 'bitstamp' (public crypto candles)
    or 'cache' (TradingView CSVs only)."""
    kind = getattr(args, "feed", None)
    if kind is None:
        kind = "broker" if getattr(args, "broker", "none") in ("ibkr", "mt5") else "cache"
    if kind == "broker" and broker is None:
        raise SystemExit("--feed broker needs --broker ibkr or mt5")
    feed = None
    if kind == "oanda":
        from .data.oanda import OandaFeed
        feed = OandaFeed(settings=settings)
    if kind == "bitstamp":
        from .data.bitstamp import BitstampFeed
        feed = BitstampFeed()
    return kind, feed


def _valid_clock(text: str) -> bool:
    import re
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", str(text).strip())
    return bool(m) and int(m.group(1)) < 24 and int(m.group(2)) < 60


def _parse_steps(text: str):
    """``-3:1.0,-6:0.5`` -> ((-3.0, 1.0), (-6.0, 0.5)); ``none`` -> ()."""
    if str(text).strip().lower() in ("", "none", "off"):
        return ()
    try:
        steps = tuple(tuple(float(x) for x in part.split(":")) for part in str(text).split(",") if part.strip())
    except ValueError:
        steps = ((0.0,),)
    if any(len(st) != 2 or st[0] >= 0 or not 0 < st[1] <= 5 for st in steps):
        raise SystemExit(f"--drawdown-steps {text!r}: give level:risk pairs below the start, e.g. -3:1.0,-6:0.5")
    return steps


def _print_margin(broker, settings: Settings, symbol: str, currency: str) -> None:
    """The server's margin for one lot and the leverage it implies, with what the live loop does about it."""
    from .core.types import Direction
    spec = settings.symbol(symbol)
    try:
        price = broker.current_price(symbol)
        per_lot = broker.margin_per_lot(symbol, Direction.LONG, price)
    except Exception:
        return
    if not per_lot:
        return
    leverage = price / spec.pip_size * spec.pip_value_per_lot / per_lot
    pct = settings.prop_firm.max_margin_pct
    print(f"margin: 1 lot {symbol} ties up {per_lot:,.0f} {currency} at {price:.{spec.price_decimals}f} (about 1:{leverage:.3g}); "
          + (f"a position may use {pct:g} % of equity as margin, larger ones are cut to fit" if pct
             else "no margin cap (prop_firm.max_margin_pct 0)"))


# the guard's limits per funding product, inside the product's own (FTMO 2-Step: 5 % a day, 10 % static; FTMO 1-Step: 3 % a
# day, 10 % under the highest balance at a day's start)
PRODUCT_GUARDS = {
    # 6 October, evening (Max: the 2-Step): 9.5 % from the start instead of the profiles' 8 %. Setup B, starts 2024-25, at 1 %:
    # funded within a year 68 % against 61 % with 8 %, none failed (README "1-Step or 2-Step"); the day stays at 4 %
    "ftmo_2step": {"daily_loss_limit_pct": 4.0, "max_drawdown_pct": 9.5, "drawdown_basis": "initial"},
    "ftmo_1step": {"daily_loss_limit_pct": 2.9, "max_drawdown_pct": 9.0, "drawdown_basis": "day_high"},
}


def apply_product(settings: Settings, product: str) -> None:
    """Set the guard's day and total limits and the total's basis for a funding product (PRODUCT_GUARDS)."""
    if product not in PRODUCT_GUARDS:
        raise SystemExit(f"--product {product}: one of {', '.join(PRODUCT_GUARDS)}")
    for key, value in PRODUCT_GUARDS[product].items():
        setattr(settings.prop_firm, key, value)


def cmd_live(args) -> int:
    from .live import LiveRunner, build_fetch
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    _apply_mt5_symbol(args, settings, symbol)
    if getattr(args, "account_size", None):
        settings.account_size = float(args.account_size)
    if getattr(args, "weekend_close", None):
        settings.prop_firm.weekend_close = args.weekend_close
    if settings.prop_firm.weekend_close and not _valid_clock(settings.prop_firm.weekend_close):
        raise SystemExit(f"weekend close {settings.prop_firm.weekend_close!r} is not a time like 16:45 (New York)")
    if getattr(args, "risk_pct", None):
        if not 0 < args.risk_pct <= 5:
            raise SystemExit(f"--risk-pct {args.risk_pct} is outside 0-5 %")
        settings.risk.risk_pct = float(args.risk_pct)
    if getattr(args, "drawdown_steps", None):
        settings.risk.drawdown_steps = _parse_steps(args.drawdown_steps)
    if getattr(args, "target_pct", None) is not None:
        settings.risk.target_pct = float(args.target_pct)
    if getattr(args, "protect_pct", None) is not None:
        settings.risk.target_protect_pct = float(args.protect_pct)
    if settings.risk.target_protect_pct and not settings.risk.target_pct:
        raise SystemExit("--protect-pct needs the phase's target: --target-pct 10 (2-Step phase 1) or 5 (the verification)")
    if getattr(args, "product", None):
        apply_product(settings, args.product)
    if getattr(args, "journal", None):
        settings.live.journal_path = args.journal
        settings.live.charts_dir = str(Path(args.journal).parent / "charts")
    broker = _broker(args, settings)
    sizing_note = None
    if broker is not None and args.broker == "mt5":
        spec = settings.symbol(symbol)
        before = spec.pip_value_per_lot
        try:
            changes = broker.align_spec(symbol)
            currency = broker.account_currency()
            print(f"sizing: 1 lot {symbol} = {spec.pip_value_per_lot:.4g} {currency} per pip of {spec.pip_size:g}, lots "
                  f"{spec.min_lot:g}-{spec.max_lot:g} step {spec.lot_step:g}" + (f" (server: {'; '.join(changes)})" if changes else ""))
            if before > 0 and abs(spec.pip_value_per_lot - before) > 0.2 * before:
                sizing_note = (f"ℹ️ {symbol}: lots sized with MT5's contract: 1 lot = {spec.pip_value_per_lot:.4g} {currency} per pip "
                               f"of {spec.pip_size:g} (the profile assumed {before:g})")
            _print_margin(broker, settings, symbol, currency)
        except Exception as exc:
            hint = "`python -m kronos_trader mt5-symbols --search <text>` lists the server's names"
            if args.execute:                # real orders on a symbol the server lacks: stop here instead of idling on old bars
                raise SystemExit(f"{symbol}: could not read the contract from MT5 ({exc}). Not started: set the broker's "
                                 f"name with --mt5-symbol NAME ({hint}).")
            print(f"[warn] {symbol}: could not read the contract from MT5 ({exc}); lots sized with the profile's numbers ({hint})")
    data_dir = args.data_dir or settings.tradingview.cache_dir
    kind, feed = _feed(args, settings, broker)
    fetch = build_fetch(settings, symbol, cache_dir=data_dir, broker=broker if kind == "broker" else None,
                        broker_timeframes=[] if kind == "cache" else None, feed=feed)
    notifier = TelegramNotifier(params=settings.telegram)
    if getattr(args, "tag", None):
        notifier.prefix = f"[{args.tag}] "
    if sizing_note:
        notifier.send(sizing_note)
    runner = LiveRunner(settings, symbol, fetch, broker=broker, notifier=notifier,
                        engine=_engine(settings),
                        dry_run=not args.execute, require_approval=not args.no_approval,
                        notify_every_scan=args.notify_every_scan, keep_paper_account=args.broker == "paper")
    import hashlib
    from .backtest.provenance import code_snapshot, settings_dict
    code = code_snapshot()
    resolved = settings_dict(settings)
    settings_sha = hashlib.sha256(json.dumps(resolved, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    print(f"code: {code.get('commit')} source {code['source_sha256'][:12]}{' (uncommitted changes)' if code.get('dirty') else ''}, "
          f"settings {settings_sha[:12]}")
    runner.record_start(code, resolved, settings_sha, " ".join(sys.argv))
    mode = "EXECUTE" if args.execute else "dry-run"
    print(f"live {symbol}: broker={args.broker} feed={kind} mode={mode} approval={'off' if args.no_approval else 'on'} "
          f"telegram={'on' if notifier.configured else 'dry-run'} poll={args.poll}s")
    pf = settings.prop_firm
    month = f", a month of -{pf.monthly_loss_limit_pct}%" if pf.monthly_loss_limit_pct else ""
    steps = "".join(f", {float(r):g}% from {float(lvl):g}%" for lvl, r in settings.risk.drawdown_steps)
    if settings.risk.target_pct and settings.risk.target_protect_pct:
        steps += (f", half from +{settings.risk.target_pct - settings.risk.target_protect_pct:g}% (target +{settings.risk.target_pct:g}%)")
    print(f"guard: account {settings.account_size:,.0f}, risk {settings.risk.risk_pct}% a trade{steps}, stop at a day of -{pf.daily_loss_limit_pct}%{month} "
          f"or -{pf.max_drawdown_pct}% from the {dict(initial='start', peak='peak', day_high='highest day-start balance').get(pf.drawdown_basis, pf.drawdown_basis)}, max {pf.max_open_trades} open "
          f"({pf.max_open_per_symbol} per market)" + (f", flat by Friday {pf.weekend_close} New York" if pf.weekend_close else ""))
    if broker is not None and args.broker in ("mt5", "ibkr"):
        try:
            balance = float(broker.balance())
            if balance > 0 and abs(balance - settings.account_size) / settings.account_size > 0.2:
                print(f"[warn] the broker's balance is {balance:,.0f} but the guard counts from {settings.account_size:,.0f}: "
                      f"pass --account-size with the account's initial balance (e.g. 10000 on a 10k challenge)")
        except Exception as exc:
            print(f"[warn] could not read the broker's balance ({exc})")
    if args.once:
        print("scanning... (the first scan loads Kronos and can take a minute or two)")
        analysis = runner.step()
        print(_plain(format_analysis(analysis, settings.symbol(symbol))))
        return 0
    runner.run_forever(args.poll)
    return 0


def cmd_forward_report(args) -> int:
    """The forward record from the MT5 terminal (read only): every position of the account against the journal's plan,
    slippage and costs, R before and after costs, the code each trade ran on, and the account against the product's
    loss limits. Writes forward_trades.csv and forward_report.html."""
    from .execution.mt5 import MT5Broker
    from .forward import (PRODUCTS, account_from_mt5, deals_from_mt5, funding_status, read_journal, reconcile, summary,
                          unmatched_fills, write_report)
    settings = _load_settings(args)
    for pair in (args.mt5_names or "").split(","):
        if "=" in pair:
            sym, name = (x.strip() for x in pair.split("=", 1))
            settings.symbols[_ensure_symbol(settings, sym)].mt5_symbol = name
    journal = read_journal(args.journal) if Path(args.journal).exists() else pd.DataFrame(columns=["time", "symbol", "event", "id", "note"])
    if args.since:
        since = pd.Timestamp(args.since)
    elif len(journal) and journal["time"].notna().any():
        since = journal["time"].min().normalize()
    else:
        since = pd.Timestamp.now().normalize() - pd.Timedelta(days=30)
    if args.product not in PRODUCTS:
        raise SystemExit(f"--product {args.product}: one of {', '.join(PRODUCTS)}")
    broker = MT5Broker(settings)
    try:
        deals = deals_from_mt5(broker, since)
        account = account_from_mt5(broker)
    finally:
        broker.disconnect()
    rec = reconcile(journal, deals, magic=broker.magic)
    summ = summary(rec)
    initial = float(args.account_size or settings.account_size)
    status = funding_status(account, deals, PRODUCTS[args.product], initial, pd.Timestamp.now("UTC").tz_localize(None))
    out_dir = args.out_dir or str(Path(args.journal).parent / "report")
    page = write_report(out_dir, rec, summ, status, unmatched_fills(journal, rec), account["positions"],
                        title=f"Kronos forward record - {account.get('server', '')} {account.get('login', '')}")
    print(f"account {account.get('login')} on {account.get('server')}: balance {status['balance']:,.2f} equity {status['equity']:,.2f}")
    print(f"{status['product']}: {status['left_today']:,.2f} left today ({status['left_today_pct']:.2f} % of {initial:,.0f}), "
          f"{status['left_total']:,.2f} to the total floor ({status['left_total_pct']:.2f} %); open risk to the stops "
          f"{status['open_risk']:,.2f} on {status['open_positions']} position(s), {status['manual_positions']} not the bot's")
    if status["positions_without_stop"]:
        print(f"!! positions without a stop: {status['positions_without_stop']} - the worst case is unbounded")
    if len(summ):
        print(summ.to_string(index=False))
    else:
        print("no closed trades since", since.date())
    print(f"report: {page}")
    return 0


def cmd_watchdog(args) -> int:
    """Read the windows' heartbeats next to the journal and say on Telegram when one stops, its scans fail or its news
    calendar runs dry; once when it starts and once when it is over."""
    from .watchdog import Watchdog
    settings = _load_settings(args)
    folder = Path(args.journal).parent
    notifier = TelegramNotifier(params=settings.telegram)
    if getattr(args, "tag", None):
        notifier.prefix = f"[{args.tag}] "
    dog = Watchdog(folder, notifier.send, max_age_minutes=args.max_age, down_minutes=args.down_minutes)
    print(f"watchdog on {folder}: a window is reported after {args.max_age:g} min without a scan, after {args.down_minutes:g} "
          f"min without a good one; telegram={'on' if notifier.configured else 'dry-run'}")
    if args.once:
        for text in dog.check():
            print(text)
        return 0
    dog.run_forever(args.every)
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


def cmd_mt5_symbols(args) -> int:
    """The server's symbols matching --search, so the profile's mt5_symbol can be set to the broker's own name."""
    from .execution.mt5 import MT5Broker
    settings = _load_settings(args)
    broker = MT5Broker(settings)
    names = broker.find_symbols(args.search)
    if not names:
        print(f"no symbol containing {args.search!r} on this server; this account may not offer it (check Market Watch, right-click, Symbols)")
        broker.disconnect()
        return 1
    for name in names:
        d = broker.symbol_details(name)
        print(f"{name:14s} {str(d.get('description') or ''):32s} digits {d.get('digits')}  contract {d.get('trade_contract_size')}  "
              f"lots {d.get('volume_min')}-{d.get('volume_max')} step {d.get('volume_step')}  profit in {d.get('currency_profit')}  trade_mode {d.get('trade_mode')}")
    print("set it in the profile, e.g.:\nsymbols:\n  BTCUSD:\n    mt5_symbol: <name from the list>")
    broker.disconnect()
    return 0


def spread_report(broker, settings: Settings, symbols, minutes: float = 10.0, every: float = 5.0,
                  sleep=None, clock=None) -> list:
    """The server's live spread per market, sampled every ``every`` seconds for ``minutes``: median, 90th percentile and
    maximum in the profile's pips, against the spread the backtest assumed (typical_spread_pips), and the stop below which
    the live spread cap (risk.max_spread_stop_fraction) refuses an entry at the median spread. One line per market."""
    import time as _time
    sleep, clock = sleep or _time.sleep, clock or _time.time
    samples = {s: [] for s in symbols}
    for s in symbols:
        try:
            broker.mt5.symbol_select(broker.mt5_symbol(s), True)
        except Exception:
            pass
    end = clock() + max(0.0, float(minutes)) * 60.0
    while True:
        for s in symbols:
            try:
                tick = broker.mt5.symbol_info_tick(broker.mt5_symbol(s))
            except Exception:
                tick = None
            if tick is not None and getattr(tick, "ask", 0) and getattr(tick, "bid", 0):
                samples[s].append(float(tick.ask) - float(tick.bid))
        if clock() >= end:
            break
        sleep(max(0.5, float(every)))
    cap = float(settings.risk.max_spread_stop_fraction or 0.0)
    lines = []
    for s in symbols:
        spec, v = settings.symbol(s), sorted(samples[s])
        if not v:
            lines.append(f"{s} ({broker.mt5_symbol(s)}): no prices (market closed, or the symbol is missing from Market Watch)")
            continue
        pip = spec.pip_size
        med, p90 = v[len(v) // 2], v[int(0.9 * (len(v) - 1))]
        line = (f"{s} ({broker.mt5_symbol(s)}): {len(v)} samples, spread median {med / pip:.1f} pips ({med:.{spec.price_decimals}f}), "
                f"90 % {p90 / pip:.1f}, max {v[-1] / pip:.1f}; the backtest assumed {spec.typical_spread_pips:g}")
        if cap:
            line += f"; the {cap:.0%} cap refuses stops under {med / cap / pip:.1f} pips at the median"
        lines.append(line)
    return lines


def cmd_mt5_spreads(args) -> int:
    from .execution.mt5 import MT5Broker
    settings = _load_settings(args)
    symbols = []
    for item in str(args.symbols).split(","):
        name, _, server = item.partition("=")
        if not name.strip():
            continue
        key = _ensure_symbol(settings, name.strip())
        if server.strip():
            settings.symbols[key].mt5_symbol = server.strip()
        symbols.append(key)
    broker = MT5Broker(settings)
    print(f"sampling {', '.join(symbols)} every {args.every:g} s for {args.minutes:g} min ...")
    for line in spread_report(broker, settings, symbols, args.minutes, args.every):
        print(line)
    broker.disconnect()
    return 0


def cmd_mt5_test(args) -> int:
    from .execution.mt5 import MT5Broker
    settings = _load_settings(args)
    symbol = _ensure_symbol(settings, args.symbol)
    _apply_mt5_symbol(args, settings, symbol)
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
    sp.add_argument("--costs", choices=("none", "ftmo"), default="none",
                    help="commission per trade: none (default) or FTMO's (forex 3 a lot round turn, crypto 0.065 %% of "
                         "the notional, metals and indices in the spread)")
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
    sp.add_argument("--mt5-symbol", help="the broker's name for the symbol when it differs (see mt5-symbols), e.g. BTCUSD.x")
    sp.add_argument("--execute", action="store_true", help="send real orders (default: dry-run, Telegram only)")
    sp.add_argument("--no-approval", action="store_true", help="execute without the Telegram approve step")
    sp.add_argument("--poll", type=int, default=60, help="seconds between scans")
    sp.add_argument("--once", action="store_true", help="run a single scan and exit")
    sp.add_argument("--notify-every-scan", action="store_true")
    sp.add_argument("--feed", choices=["broker", "oanda", "bitstamp", "cache"],
                    help="live candle source (default: broker bars with --broker ibkr/mt5, otherwise the cache); "
                         "bitstamp: BTCUSD/ETHUSD around the clock, with --broker paper")
    sp.add_argument("--account-size", type=float, help="account size for the paper broker and the guard, e.g. 10000")
    sp.add_argument("--journal", help="the journal file (default: the profile's live.journal_path, journal/trades.csv); a second "
                                      "account beside the demo needs its own, e.g. journal_ftmo/trades.csv")
    sp.add_argument("--tag", help="a label in front of every Telegram message, e.g. FTMO, when two accounts share the chat")
    sp.add_argument("--weekend-close", metavar="HH:MM", help="flat by this Friday time (New York) and no new trade until the "
                    "Sunday open, e.g. 16:45 on a funded FTMO Standard account (prop_firm.weekend_close)")
    sp.add_argument("--risk-pct", type=float, help="risk per trade in %% of equity, in place of the profile's (e.g. 1.0 on a "
                    "funded account)")
    sp.add_argument("--drawdown-steps", help="risk.drawdown_steps in place of the profile's: level %%:risk %% pairs below the "
                    "start, e.g. --drawdown-steps=-3:0.5 (the = keeps the minus sign from reading as a flag); 'none' for none")
    sp.add_argument("--target-pct", type=float, help="the challenge phase's profit target in %% of the initial balance (FTMO 2-Step: "
                    "10, then 5 in the verification); used by --protect-pct")
    sp.add_argument("--protect-pct", type=float, help="within this many %% of --target-pct every trade risks half of the stake "
                    "(risk.target_protect_pct), e.g. 4")
    sp.add_argument("--product", help="the guard's limits for a funding product: ftmo_2step (4 %% a day, 9.5 %% from the start) or "
                    "ftmo_1step (2.9 %% a day, 9 %% under the highest day-start balance)")
    sp.set_defaults(func=cmd_live)

    sp = sub.add_parser("ibkr-test", help="connect to TWS / IB Gateway and print account, contract, price and bars")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--tf", default="15m")
    sp.set_defaults(func=cmd_ibkr_test)
    sp = sub.add_parser("feed-test", help="pull the last bars from the OANDA feed (needs OANDA_TOKEN)")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--tf", default="15m")
    sp.set_defaults(func=cmd_feed_test)

    sp = sub.add_parser("mt5-symbols", help="list the MT5 server's symbols that contain a text (e.g. BTC) with contract size and lot limits")
    sp.add_argument("--search", required=True)
    sp.set_defaults(func=cmd_mt5_symbols)
    sp = sub.add_parser("mt5-spreads", help="the server's live spreads per market against the backtest's and the live spread cap")
    sp.add_argument("--symbols", default="EURUSD,XAUUSD,NAS100=US100.cash,BTCUSD",
                    help="markets, with the server's name where it differs: NAS100=US100.cash")
    sp.add_argument("--minutes", type=float, default=10.0, help="how long to sample")
    sp.add_argument("--every", type=float, default=5.0, help="seconds between samples")
    sp.set_defaults(func=cmd_mt5_spreads)
    sp = sub.add_parser("mt5-test", help="connect to the MetaTrader 5 terminal and print account, server time offset and bars")
    sp.add_argument("--symbol", default="EURUSD")
    sp.add_argument("--mt5-symbol", help="the broker's name for the symbol when it differs (see mt5-symbols)")
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

    sp = sub.add_parser("forward-report", help="MT5 deals against the journal: fills, slippage, costs, R after costs, the "
                        "code each trade ran on, and the account against the product's loss limits (reads only)")
    sp.add_argument("--journal", default="journal_ftmo/trades.csv")
    sp.add_argument("--since", help="first day to read, YYYY-MM-DD (default: the journal's first day)")
    sp.add_argument("--product", default="ftmo_2step", help="loss limits: ftmo_2step or ftmo_1step")
    sp.add_argument("--account-size", type=float, help="the account's initial balance (the limits are %% of it)")
    sp.add_argument("--mt5-names", help="the server's names where they differ, e.g. NAS100=US100.cash,BTCUSD=BTCUSD")
    sp.add_argument("--out-dir", help="where forward_trades.csv and forward_report.html go (default: report/ next to the journal)")
    sp.set_defaults(func=cmd_forward_report)

    sp = sub.add_parser("watchdog", help="watch the live windows' heartbeats (next to the journal) and say on Telegram when "
                        "one stops, its scans fail or its news calendar runs dry")
    sp.add_argument("--journal", default="journal/trades.csv", help="the windows' journal: their heartbeats sit next to it")
    sp.add_argument("--max-age", type=float, default=5.0, help="minutes without a scan before a window is reported")
    sp.add_argument("--down-minutes", type=float, default=15.0, help="minutes without a good scan (MT5 link down, errors)")
    sp.add_argument("--every", type=float, default=60.0, help="seconds between checks")
    sp.add_argument("--tag", help="put [TAG] in front of every message, e.g. FTMO")
    sp.add_argument("--once", action="store_true", help="one check, print what it would send, stop")
    sp.set_defaults(func=cmd_watchdog)

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
