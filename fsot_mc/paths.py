"""
Portable path resolution for FSOT Monte Carlo Intelligence.

Never hardcode drive letters in library code. Override with env vars:

  FSOT_MC_DATA_ROOT      root for OHLCV + patterns + journals
  FSOT_MC_OHLCV_DIR      OHLCV CSV directory
  FSOT_MC_PATTERN_DIR    pattern ledger directory
  FSOT_MC_JOURNAL_DIR    forward journal directory
  FSOT_ARCHIVE_ROOT      optional physical archive (authority checks)
"""

from __future__ import annotations

import os
from pathlib import Path

# Package root (…/FSOT-Monte-Carlo-Intelligence)
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def data_root() -> Path:
    env = os.environ.get("FSOT_MC_DATA_ROOT")
    if env:
        return Path(env)
    # Prefer local project data/, then optional market-history drive
    local = PACKAGE_ROOT / "data"
    legacy = Path(r"D:\training data\FSOT-Market-History")
    if (local / "ohlcv").is_dir():
        return local
    if legacy.is_dir():
        return legacy
    return local


def ohlcv_dir() -> Path:
    env = os.environ.get("FSOT_MC_OHLCV_DIR")
    if env:
        return Path(env)
    return data_root() / "ohlcv"


def pattern_dir() -> Path:
    env = os.environ.get("FSOT_MC_PATTERN_DIR")
    if env:
        return Path(env)
    return data_root() / "patterns"


def journal_dir() -> Path:
    env = os.environ.get("FSOT_MC_JOURNAL_DIR")
    if env:
        return Path(env)
    return data_root() / "journals"


def archive_root() -> Path | None:
    env = os.environ.get("FSOT_ARCHIVE_ROOT")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    default = Path(r"I:\FSOT-Physical-Archive")
    return default if default.is_dir() else None


def archive_compute_path() -> Path | None:
    root = archive_root()
    if root is None:
        return None
    p = root / "02_FSOT-2.1-Lean-Full" / "vendor" / "fsot_compute.py"
    return p if p.is_file() else None


def ohlcv_csv(symbol: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in symbol.upper())
    return ohlcv_dir() / f"{safe}.csv"


def ensure_data_dirs() -> None:
    for d in (data_root(), pattern_dir(), journal_dir(), PACKAGE_ROOT / "data" / "exports"):
        d.mkdir(parents=True, exist_ok=True)
