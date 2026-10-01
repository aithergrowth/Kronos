"""Reproduce this bounded audit with cached data only; never connects to a broker."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import pandas as pd
from kronos_trader.config import Settings
from kronos_trader.core.timeframe import Timeframe
from kronos_trader.data.tv_cache import load_all, cache_path
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy.engine import StrategyEngine
from kronos_trader.backtest.runner import Backtester

SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'NAS100']
EMPTY_COLUMNS = ['symbol', 'direction', 'opened_at', 'closed_at', 'entry', 'exit', 'stop', 'take_profit', 'r', 'reason']


def run(job):
    symbol, cache, output, label, calendar_path, profile = job
    settings = Settings()  # Ignore environment-specific config; no credentials read.
    settings.kronos.mode = 'off'
    # Pin behavior independently of later default-profile edits.
    settings.session.windows = (("09:00", "17:00"),) if profile == 'forward' else (("09:00", "11:00"), ("13:00", "17:00"))
    settings.confirmation.allow_first_candle = profile != 'forward'
    if hasattr(settings, 'news'):
        settings.news.enabled = bool(calendar_path)
        settings.news.forexfactory = False
    calendar = None
    if calendar_path:
        from kronos_trader.data.calendar import NewsCalendar, load_events
        if not Path(calendar_path).is_file():
            raise FileNotFoundError(calendar_path)
        n = settings.news
        calendar = NewsCalendar(load_events(calendar_path), n.before_minutes, n.after_minutes, n.min_importance)
    feed = settings.symbol(symbol).tradingview_symbol
    frames = load_all(cache, feed)
    engine = StrategyEngine(settings, calendar=calendar) if calendar_path else StrategyEngine(settings)
    result = Backtester(settings, MultiTimeframeData(frames), symbol,
                        step_tf=Timeframe.MIN_15, engine=engine).run()
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    trades = result.trades_frame()
    csv_path = output / f'{label}_{symbol.lower()}_15m.csv'
    (trades if not trades.empty else pd.DataFrame(columns=EMPTY_COLUMNS)).to_csv(csv_path, index=False)
    closed = [t for t in result.trades if t.reason != 'end_of_data']
    marked = [t for t in result.trades if t.reason == 'end_of_data']
    input_files = []
    for tf, series in frames.items():
        path = cache_path(cache, feed, tf)
        if not path.is_file():
            raise FileNotFoundError(f'Audit expects canonical cache filenames: {path}')
        input_files.append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'timeframe': tf.label, 'rows': len(series),
                            'first_open': str(series.timestamps.iloc[0]), 'last_open': str(series.timestamps.iloc[-1])})
    metrics = {'symbol': symbol, 'feed': feed, 'step': '15m', 'kronos': 'off',
               'news_blackout': bool(calendar_path), 'profile': profile, 'initial_equity': settings.account_size,
               'period': [str(result.start), str(result.end)], 'steps': result.steps, 'signals': result.signals,
               'trades_including_end_marks': len(result.trades), 'decided_trades': len(closed),
               'wins': sum(t.pnl > 0 for t in closed), 'losses': sum(t.pnl < 0 for t in closed),
               'breakeven': sum(t.pnl == 0 for t in closed), 'realized_r': sum(t.r for t in closed),
               'end_of_data_mark_r': sum(t.r for t in marked), 'end_of_data_mark_count': len(marked),
               'runtime_seconds': result.runtime_seconds, 'input_files': input_files,
               'guard_rejection_counts': result.guard_reasons,
               'execution_rejection_counts': {k:v for k,v in result.rejection_reasons.items() if k.startswith('execution')},
               'trade_csv_sha256': hashlib.sha256(csv_path.read_bytes()).hexdigest()}
    if calendar_path:
        metrics['calendar_sha256'] = hashlib.sha256(Path(calendar_path).read_bytes()).hexdigest()
        metrics['news_window_minutes'] = [settings.news.before_minutes, settings.news.after_minutes]
    (output / f'{label}_{symbol.lower()}_15m.json').write_text(json.dumps(metrics, indent=2)+'\n')
    return {k:v for k,v in metrics.items() if k not in ['input_files', 'guard_rejection_counts']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', default='data/tv_cache')
    parser.add_argument('--out', default='docs/backtests/verification_2026-10-01')
    parser.add_argument('--label', default='corrected')
    parser.add_argument('--calendar', help='Optional local news CSV; no live calendar fetch')
    parser.add_argument('--symbols', nargs='+', default=SYMBOLS, choices=SYMBOLS)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--profile', choices=['audited', 'forward'], default='audited', help='audited: split sessions/first candle on; forward: 09–17/first candle off')
    args = parser.parse_args()
    jobs = [(s, args.cache, args.out, args.label, args.calendar, args.profile) for s in args.symbols]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(run, jobs):
            print(json.dumps(row), flush=True)

if __name__ == '__main__':
    main()
