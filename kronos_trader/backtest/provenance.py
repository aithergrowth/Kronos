"""What a backtest ran on: code revision, settings, command, data, calendar and cost assumptions."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


PACKAGE_DIR = Path(__file__).resolve().parents[1]      # kronos_trader/


def source_manifest(package_dir=None) -> Dict[str, Any]:
    """SHA-256 of every source file of the package on disk, and one hash over all of them."""
    root = Path(package_dir) if package_dir else PACKAGE_DIR
    files: Dict[str, str] = {}
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        files[p.relative_to(root.parent).as_posix()] = _sha256(p)
    combined = hashlib.sha256("".join(f"{k}:{v}\n" for k, v in files.items()).encode("utf-8")).hexdigest()
    return {"files": files, "sha256": combined}


def code_snapshot(cwd: Optional[str] = None) -> Dict[str, Any]:
    """The code identity *now*.  Call it when the process starts, before the run: Python imports the
    package once, so the files on disk at that moment are the program that runs, whatever the checkout
    holds hours later when the results are written."""
    doc = git_revision(cwd)
    manifest = source_manifest()
    doc.update({"captured": "at start", "taken_at": str(pd.Timestamp.now("UTC").tz_localize(None)),
                "source_sha256": manifest["sha256"], "source_files": manifest["files"]})
    return doc


def git_revision(cwd: Optional[str] = None) -> Dict[str, Any]:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=cwd, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd, check=True).stdout.strip()
        return {"commit": rev, "dirty": bool(dirty), "local_changes": dirty.splitlines()[:50]}
    except Exception as exc:    # not a git checkout, git missing
        return {"commit": None, "dirty": None, "error": str(exc)}


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(getattr(k, "label", k)): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(getattr(obj, "label", obj))


def settings_dict(settings) -> Dict[str, Any]:
    """Resolved settings as plain JSON (enums and timeframes as text; secrets are env var *names* only)."""
    return _jsonable(dataclasses.asdict(settings))


def data_manifest(data_dir, symbol: str) -> Dict[str, Any]:
    folder = Path(data_dir)
    out: Dict[str, Any] = {}
    for path in sorted(folder.glob(f"{symbol.upper()}_*.csv")):
        try:
            frame = pd.read_csv(path, usecols=["timestamp"])
            first, last, rows = str(frame["timestamp"].iloc[0]), str(frame["timestamp"].iloc[-1]), len(frame)
        except Exception:
            first = last = None; rows = None
        out[path.name] = {"sha256": _sha256(path), "rows": rows, "first": first, "last": last}
    return out


def calendar_manifest(path) -> Dict[str, Any]:
    p = Path(path) if path else None
    if p is None or not p.exists():
        return {"path": str(path), "present": False}
    frame = pd.read_csv(p)
    return {"path": str(p), "present": True, "sha256": _sha256(p), "events": len(frame),
            "first": str(frame["time"].min()), "last": str(frame["time"].max()),
            "currencies": sorted(frame["currency"].astype(str).unique().tolist()) if "currency" in frame else None}


def write_provenance(path, *, settings, symbol: str, data_dir, result=None, quote_basis: str = "mid",
                     command: Optional[str] = None, extra: Optional[Dict[str, Any]] = None,
                     code: Optional[Dict[str, Any]] = None) -> Path:
    """``code`` is the :func:`code_snapshot` taken when the process started; without it the record can
    only name the checkout at write time, which is flagged as such."""
    at_write = git_revision()
    manifest_now = source_manifest()
    at_write["source_sha256"] = manifest_now["sha256"]
    if code is None:
        code_doc: Dict[str, Any] = {**at_write, "captured": "at write: names the checkout when the results were written; "
                                    "the process may have been started on an earlier revision"}
    else:
        code_doc = dict(code)
        code_doc["changed_since_start"] = (code.get("commit") != at_write.get("commit")
                                           or code.get("source_sha256") != manifest_now["sha256"])
    doc: Dict[str, Any] = {
        "written": str(pd.Timestamp.now("UTC").tz_localize(None)),
        "code": code_doc,
        "code_at_write": at_write,
        "command": command if command is not None else " ".join(sys.argv),
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
        "symbol": symbol.upper(),
        "settings": settings_dict(settings),
        "data": data_manifest(data_dir, symbol) if data_dir else {},
        "calendar": calendar_manifest(getattr(settings.news, "calendar_csv", None)) if settings.news.enabled else {"enabled": False},
        "costs": {"quote_basis": quote_basis, "spread_pips": settings.symbol(symbol).typical_spread_pips,
                  "commission": "none modelled", "slippage": "none modelled", "swap": "none modelled"},
    }
    if result is not None:
        doc["run"] = {"start": str(result.start), "end": str(result.end), "step_tf": result.step_tf.label, "steps": result.steps,
                      "signals": result.signals, "trades": len(result.trades), "rejected_by_guard": result.rejected_by_guard,
                      "guard_reasons": result.guard_reasons, "zones_by_reason": result.zones_by_reason,
                      "first_breach": None if not result.first_breach else {"time": str(result.first_breach[0]), "rule": result.first_breach[1]},
                      "guard_rules": result.guard_rules,
                      "initial_equity": result.initial_equity, "final_equity": result.final_equity, "runtime_seconds": result.runtime_seconds}
    if extra:
        doc.update(extra)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, default=str), encoding="utf-8")
    return out
