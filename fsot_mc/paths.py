"""
Portable path resolution — **workspace-independent by default**.

All required data lives under this package tree:
  vendor/archive_bundle/   — FSOT law bundle (D1D38A, navigator, certificates)
  vendor/pflt/             — vendored PFLT eyes + language core
  vendor/linguistics/      — linguistic anchors
  data/realities_snapshot/ — offline Realities runtime snapshot
  fsot_mc/full_atlas.json  — 402-domain atlas
  fsot_mc/compute_authority.py — pin D1D38A

Optional overrides (never required):
  FSOT_MC_DATA_ROOT, FSOT_ARCHIVE_ROOT, REALITIES_OS_ROOT, PFLT_ROOT
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def data_root() -> Path:
    env = os.environ.get("FSOT_MC_DATA_ROOT")
    if env:
        return Path(env)
    local = PACKAGE_ROOT / "data"
    local.mkdir(parents=True, exist_ok=True)
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


def vendor_root() -> Path:
    return PACKAGE_ROOT / "vendor"


def archive_bundle_dir() -> Path:
    return vendor_root() / "archive_bundle"


def pflt_vendor_dir() -> Path:
    env = os.environ.get("PFLT_ROOT")
    if env and Path(env).is_dir():
        return Path(env)
    return vendor_root() / "pflt"


def linguistics_dir() -> Path:
    return vendor_root() / "linguistics"


def realities_snapshot_dir() -> Path:
    return PACKAGE_ROOT / "data" / "realities_snapshot"


def archive_root() -> Path | None:
    """
    Optional *external* archive for refresh / pathway alignment.

    Independent runtime uses archive_bundle_dir() and does not *require* this.
    Set FSOT_MC_USE_PHYSICAL_ARCHIVE=1 (or FSOT_ARCHIVE_ROOT) to prefer I: hub
    when present — used by formal cross-proof + pathway alignment.
    """
    env = os.environ.get("FSOT_ARCHIVE_ROOT")
    if env:
        p = Path(env)
        return p if p.is_dir() else None
    default = Path(r"I:\FSOT-Physical-Archive")
    use_phys = os.environ.get("FSOT_MC_USE_PHYSICAL_ARCHIVE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if use_phys and default.is_dir():
        return default
    # Prefer local bundle existence as "archive available" for independence
    if archive_bundle_dir().is_dir() and (archive_bundle_dir() / "MANIFEST.json").is_file():
        # Still expose physical hub when it exists for optional alignment tools
        if default.is_dir():
            return default
        return None
    return default if default.is_dir() else None


def archive_compute_path() -> Path | None:
    """Local authority first, then optional external."""
    local = PACKAGE_ROOT / "fsot_mc" / "compute_authority.py"
    if local.is_file():
        return local
    bundled = archive_bundle_dir() / "vendor__fsot_compute.py"
    if bundled.is_file():
        return bundled
    vendor = vendor_root() / "fsot_compute.py"
    if vendor.is_file():
        return vendor
    root = archive_root()
    if root is None:
        return None
    p = root / "02_FSOT-2.1-Lean-Full" / "vendor" / "fsot_compute.py"
    return p if p.is_file() else None


def ohlcv_csv(symbol: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in symbol.upper())
    return ohlcv_dir() / f"{safe}.csv"


def ensure_data_dirs() -> None:
    for d in (
        data_root(),
        pattern_dir(),
        journal_dir(),
        PACKAGE_ROOT / "data" / "exports",
        PACKAGE_ROOT / "data" / "api_cache",
        PACKAGE_ROOT / "data" / "obligations_pending",
        PACKAGE_ROOT / "data" / "obligations_promoted",
        PACKAGE_ROOT / "data" / "pathways",
        realities_snapshot_dir(),
    ):
        d.mkdir(parents=True, exist_ok=True)


def independence_status() -> dict:
    """Report whether the tree can run without external drives."""
    checks = {
        "compute_authority": (PACKAGE_ROOT / "fsot_mc" / "compute_authority.py").is_file(),
        "full_atlas": (PACKAGE_ROOT / "fsot_mc" / "full_atlas.json").is_file(),
        "archive_bundle": (archive_bundle_dir() / "MANIFEST.json").is_file(),
        "navigator": (archive_bundle_dir() / "data__fsot_domain_navigator.json").is_file(),
        "pflt_vision": (pflt_vendor_dir() / "fsot_multilayer_vision.py").is_file(),
        "pflt_core": (pflt_vendor_dir() / "PFLT_FSOT_2_1_aligned.py").is_file(),
        "linguistics": (linguistics_dir() / "linguistics_derivations.json").is_file(),
        "realities_snapshot": (realities_snapshot_dir() / "runtime" / "emergence.jsonl").is_file()
        or (realities_snapshot_dir() / "runtime" / "heartbeat").is_file(),
    }
    return {
        "independent": all(checks.values()),
        "checks": checks,
        "package_root": str(PACKAGE_ROOT),
        "external_archive_optional": archive_root() is not None,
        "free_parameters": 0,
    }
