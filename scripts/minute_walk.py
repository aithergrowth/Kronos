"""Walk the engine minute by minute through a window with a diagnostic direction, after a warm-up: which gate refuses when,
and what setup the code would reach.  Run from the repository root:
  PYTHONPATH=. python scripts/minute_walk.py <config.yaml> <symbol> <data_dir> "<start>" "<end>" long|short [warmup_days]"""
import sys
import pandas as pd
from kronos_trader.config import Settings
from kronos_trader.core.types import Direction
from kronos_trader.data.tv_cache import load_all
from kronos_trader.data.resample import MultiTimeframeData
from kronos_trader.strategy.engine import StrategyEngine
from kronos_trader.backtest.dossier import warm_up
cfg, symbol, data_dir, start, end, side = sys.argv[1:7]
warm = float(sys.argv[7]) if len(sys.argv) > 7 else 3.0
s = Settings.from_yaml(cfg); s.kronos.mode = "off"
data = MultiTimeframeData(load_all(data_dir, symbol))
engine = StrategyEngine(s)
start, end = pd.Timestamp(start), pd.Timestamp(end)
warm_up(engine, data, symbol, start, warm)
direction = Direction.SHORT if side.lower().startswith("s") else Direction.LONG
last = None
for now in pd.date_range(start, end, freq="1min"):
    views = data.as_of(now, lookback=s.structure.lookback)
    a = engine.analyze(symbol, views, equity=s.account_size, now=now, assume_direction=direction, step_minutes=1)
    diag = getattr(a, "diagnostic_setup", None)
    key = [r for r in a.rejections if "would give" in r] or [r for r in a.rejections if "POI" in r and ("waiting" in r or "R:R" in r or "below minimum" in r)][:3]
    gate = a.decision.direction if a.decision.tradable else ("refused: " + a.decision.reason[:110])
    line = f"{now:%H:%M} px {a.price:.5f} bias={gate} | " + " || ".join(k[:150] for k in key)
    if a.has_valid_signal:
        st = a.signal.setup; line += f" || SIGNAL {st.direction.name} entry {st.entry} stop {st.stop} tp {st.take_profit} rr {st.rr:.2f}"
    if diag is not None:
        line += f" || DIAG {diag.direction.name} entry {diag.entry} stop {diag.stop} ({diag.stop_detail.get('stop_basis','')[:40]}) tp {diag.take_profit} ({diag.tp_source}) rr {diag.rr:.2f} conf {diag.confirmation.type.value} {diag.confirmation.timeframe.label} @ {diag.confirmation.timestamp}"
    if line != last:
        print(line, flush=True); last = line
