import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kronos_trader.core import CandleSeries, Timeframe  # noqa: E402

HK_CSV = REPO_ROOT / "finetune_csv" / "data" / "HK_ali_09988_kline_5min_all.csv"

#: swing low 100 (idx 2) -> swing high 110 (idx 6) -> pullback that SWEEPS the low with a wick
#: (idx 10: low 99, body inside) -> last bearish candle (idx 11) -> impulse closing above 110 (idx 13)
SWEEP_BREAK_ROWS = [
    (103, 104, 101, 102),      # 0
    (102, 103, 100.5, 101),    # 1
    (101, 101.5, 100, 101),    # 2  swing low 100
    (101, 103, 100.8, 102.5),  # 3
    (102.5, 105, 102, 104.5),  # 4
    (104.5, 108, 104, 107.5),  # 5
    (107.5, 110, 107, 109),    # 6  swing high 110
    (109, 109.5, 106, 106.5),  # 7
    (106.5, 107, 104, 104.5),  # 8
    (104.5, 105, 102, 102.5),  # 9
    (102.5, 103, 99, 101),     # 10 sweep of 100 (wick to 99, close 101)
    (101, 102, 100.5, 100.8),  # 11 last bearish candle before the impulse -> balance block
    (100.8, 106, 100.6, 105.5),  # 12
    (105.5, 111, 105, 110.8),  # 13 body close above 110 -> bullish BOS
    (110.8, 112, 110, 111.5),  # 14
    (111.5, 113, 111, 112.5),  # 15
]


@pytest.fixture
def scenario() -> CandleSeries:
    return CandleSeries.from_records(SWEEP_BREAK_ROWS, Timeframe.H_1, symbol="TEST")


@pytest.fixture
def scenario_rows():
    return list(SWEEP_BREAK_ROWS)


@pytest.fixture(autouse=True)
def _scratch_working_dir(tmp_path, monkeypatch):
    """Every test runs in its own empty directory: the live runner's relative journal/ and charts/ paths (Settings())
    land there, not in the repository's journal of the forward test."""
    monkeypatch.chdir(tmp_path)
