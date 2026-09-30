"""Annotated chart examples (docs/examples) as regression checks.

An example is ``<name>.csv`` (POI-timeframe candles) plus ``<name>.yaml``
(annotations, see ``docs/examples/example_template.yaml``).  ``check_example``
runs the structure detector over the candles and compares what it finds with
what the trader drew: sweep candle, break candle, balance block, POI zone and,
when given, the stop and the target implied by the rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .config import Settings, StructureParams
from .core.candles import CandleSeries
from .core.timeframe import Timeframe
from .core.types import Bias
from .strategy.poi import map_pois
from .strategy.structure import analyze_structure

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "docs" / "examples"


@dataclass
class Example:
    name: str
    symbol: str
    timeframe: Timeframe
    direction: Bias
    csv: Path
    expect: Dict[str, Any]
    confirmation_timeframe: Optional[Timeframe] = None
    ltf_csv: Optional[Path] = None
    source: str = ""
    notes: str = ""

    @property
    def tolerance(self) -> float:
        pips = float(self.expect.get("tolerance_pips", 3))
        return pips * Settings().symbols.get(self.symbol, None).pip_size if self.symbol in Settings().symbols else pips * 0.0001


@dataclass
class ExampleResult:
    example: Example
    mismatches: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatches


def load_examples(directory: "str | Path" = EXAMPLES_DIR) -> List[Example]:
    import yaml
    directory = Path(directory)
    examples: List[Example] = []
    for yml in sorted(directory.glob("*.yaml")):
        if yml.name == "example_template.yaml":
            continue
        data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
        csv = yml.with_suffix(".csv")
        if not csv.exists():
            continue
        ltf = directory / f"{yml.stem}_ltf.csv"
        examples.append(Example(
            name=yml.stem,
            symbol=str(data.get("symbol", "EURUSD")).upper(),
            timeframe=Timeframe.parse(data.get("timeframe", "4H")),
            direction=Bias.BULLISH if str(data.get("direction", "bullish")).lower().startswith("bull") else Bias.BEARISH,
            csv=csv,
            expect=data.get("expect", {}) or {},
            confirmation_timeframe=Timeframe.parse(data["confirmation_timeframe"]) if data.get("confirmation_timeframe") else None,
            ltf_csv=ltf if ltf.exists() else None,
            source=str(data.get("source", "")),
            notes=str(data.get("notes", "")),
        ))
    return examples


def _near(a: float, b: float, tol: float) -> bool:
    return abs(float(a) - float(b)) <= tol


def check_example(example: Example, params: Optional[StructureParams] = None) -> ExampleResult:
    result = ExampleResult(example)
    series = CandleSeries.from_csv(example.csv, example.timeframe, symbol=example.symbol)
    st = analyze_structure(series, params or StructureParams())
    tol = example.tolerance
    exp = example.expect
    result.details.append(st.summary())

    def index_of(ts) -> Optional[int]:
        stamp = pd.Timestamp(ts)
        hits = series.timestamps[series.timestamps == stamp]
        return int(hits.index[0]) if len(hits) else None

    # sweep ---------------------------------------------------------------------
    if "sweep" in exp and exp["sweep"].get("candle"):
        idx = index_of(exp["sweep"]["candle"])
        if idx is None:
            result.mismatches.append(f"sweep candle {exp['sweep']['candle']} not in the CSV")
        else:
            found = [s for s in st.sweeps if s.index == idx]
            if not found:
                near = [s for s in st.sweeps if abs(s.index - idx) <= 2]
                result.mismatches.append(f"no sweep detected on {exp['sweep']['candle']}"
                                         + (f" (nearest at {near[0].timestamp})" if near else ""))
            elif exp["sweep"].get("level") is not None and not any(_near(s.level.price, exp["sweep"]["level"], tol) for s in found):
                result.mismatches.append(f"sweep level {found[0].level.price:.5f} != {exp['sweep']['level']}")

    # break ---------------------------------------------------------------------
    if "break" in exp and exp["break"].get("candle"):
        idx = index_of(exp["break"]["candle"])
        if idx is None:
            result.mismatches.append(f"break candle {exp['break']['candle']} not in the CSV")
        else:
            found = [b for b in st.breaks if b.index == idx and b.direction is example.direction]
            if not found:
                near = [b for b in st.breaks if abs(b.index - idx) <= 2]
                result.mismatches.append(f"no {example.direction} break detected on {exp['break']['candle']}"
                                         + (f" (nearest {near[0].kind.value} at {near[0].timestamp})" if near else ""))
            else:
                brk = found[0]
                if exp["break"].get("level") is not None and not _near(brk.broken_level, exp["break"]["level"], tol):
                    result.mismatches.append(f"broken level {brk.broken_level:.5f} != {exp['break']['level']}")
                if exp["break"].get("kind") and brk.kind.value != str(exp["break"]["kind"]).upper():
                    result.mismatches.append(f"break kind {brk.kind.value} != {exp['break']['kind']}")
                if "balance_block" in exp:
                    block = st.block_for_break(brk)
                    bb = exp["balance_block"]
                    if block is None or not (_near(block.low, bb["low"], tol) and _near(block.high, bb["high"], tol)):
                        got = f"{block.low:.5f}-{block.high:.5f}" if block else "none"
                        result.mismatches.append(f"balance block {got} != {bb['low']}-{bb['high']}")

    # POI -----------------------------------------------------------------------
    if "poi" in exp:
        pois = [p for p in map_pois(st) if p.direction is example.direction]
        want = exp["poi"]
        match = [p for p in pois if _near(p.low, want["low"], tol) and _near(p.high, want["high"], tol)]
        if not match:
            got = ", ".join(f"{p.low:.5f}-{p.high:.5f}" for p in pois) or "none"
            result.mismatches.append(f"POI {want['low']}-{want['high']} not mapped (mapped: {got})")

    # stop / target implied by the rules ------------------------------------------
    if exp.get("stop") is not None and st.breaks:
        brk = next((b for b in st.breaks if b.direction is example.direction), None)
        if brk is not None and not _near(brk.origin_price, exp["stop"], tol * 3):
            result.details.append(f"invalidation swing {brk.origin_price:.5f} vs drawn stop {exp['stop']} (stop sits behind the swing)")
    if exp.get("target") is not None:
        price = float(exp.get("entry", {}).get("price", series.last.close))
        if example.direction is Bias.BULLISH:
            candidates = [l.price for l in st.resting_liquidity_above(price)] + [b.low for b in st.unmitigated_blocks(Bias.BEARISH) if b.low > price]
        else:
            candidates = [l.price for l in st.resting_liquidity_below(price)] + [b.high for b in st.unmitigated_blocks(Bias.BULLISH) if b.high < price]
        if not any(_near(c, exp["target"], tol * 3) for c in candidates):
            result.mismatches.append(f"target {exp['target']} is not among the targets the rules see ({', '.join(f'{c:.5f}' for c in sorted(candidates)[:6]) or 'none'})")
    return result


def report(results: List[ExampleResult]) -> str:
    lines = []
    for r in results:
        mark = "OK " if r.ok else "FAIL"
        lines.append(f"[{mark}] {r.example.name} ({r.example.symbol} {r.example.timeframe.label} {r.example.direction})")
        for m in r.mismatches:
            lines.append(f"       - {m}")
    return "\n".join(lines)
