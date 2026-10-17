"""Three-way comparison of the EURUSD May-September 2025 slice: frozen ledger vs. slice ledgers from each checkout."""
import sys
import pandas as pd
S = "/tmp/claude-0/-home-user-Kronos/957948be-b952-557c-9d67-3d08ec248496/scratchpad"
key = ["opened_at", "direction"]
cols = ["entry", "stop", "take_profit", "closed_at", "exit", "r", "lots"]
frozen = pd.read_csv("docs/backtests/phase2/EURUSD_5m_pure.csv", parse_dates=["opened_at"])
frozen = frozen[(frozen.opened_at >= "2025-05-01") & (frozen.opened_at < "2025-10-01")]
print(f"frozen ledger rows in the window: {len(frozen)}")
for tag in sys.argv[1:]:
    sl = pd.read_csv(f"{S}/slice_eurusd_{tag}.csv", parse_dates=["opened_at"])
    m = frozen[key + cols].merge(sl[key + cols], on=key, how="outer", suffixes=("_f", "_s"), indicator=True)
    both = m[m._merge == "both"]
    same = all((abs(both[f"{c}_f"] - both[f"{c}_s"]) < 1e-9).all() for c in ("entry", "stop", "take_profit", "r")) and \
        (both["closed_at_f"].astype(str) == both["closed_at_s"].astype(str)).all()
    print(f"{tag}: {len(sl)} rows; matched {len(both)}, only frozen {int((m._merge=='left_only').sum())}, only slice {int((m._merge=='right_only').sum())}; "
          f"entry/stop/target/exit/R identical on matched rows: {same}; sum R slice {sl.r.sum():+.2f} vs frozen {frozen.r.sum():+.2f}")
