"""
FSOT authority gate — fail-closed constant + optional hash verification.

Authority pin: D1D38A (I: archive / GitHub FSOT-2.1-Lean vendor/fsot_compute.py)
Hot path: fsot_mc.fast float engine must match pin constants within 1e-12.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from fsot_mc.fast import (
    ALPHA,
    C_FACTOR,
    ETA_EFF,
    K,
    PHI,
    POOF,
    PSI_CON,
    ScalarInputF,
    compute_scalar_fast,
)
from fsot_mc.paths import archive_compute_path

# Canonical pin (must match PIN.json)
AUTHORITY_SHA256 = "D1D38A185487B452E470AC68ECE2EB45AEB1CA9CE25FC9BF9564C19633FFBE70"

_PIN_PATH = Path(__file__).resolve().parent / "PIN.json"
_LOCAL_AUTHORITY = Path(__file__).resolve().parent / "compute_authority.py"

# Expected seed-derived values (archive canonical_constants.json)
EXPECTED = {
    "K": 0.4202216641606967,
    "C_FACTOR": 0.28760015181918397,
    "POOF": 0.1534822148944508,
    "PHI": 1.618033988749895,
    "PSI_CON": 0.6321205588285577,
    "ALPHA": 0.0008082937414140405,
    "ETA_EFF": 0.4669422069242599,
    "S_economics": 0.6460045206857493,
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def pin_metadata() -> dict[str, Any]:
    if _PIN_PATH.is_file():
        return json.loads(_PIN_PATH.read_text(encoding="utf-8"))
    return {"authority_sha256": AUTHORITY_SHA256}


def verify_float_engine(tol: float = 1e-12) -> dict[str, Any]:
    """Check hot-path seeds against pinned expected values."""
    checks = {
        "K": (K, EXPECTED["K"]),
        "C_FACTOR": (C_FACTOR, EXPECTED["C_FACTOR"]),
        "POOF": (POOF, EXPECTED["POOF"]),
        "PHI": (PHI, EXPECTED["PHI"]),
        "PSI_CON": (PSI_CON, EXPECTED["PSI_CON"]),
        "ALPHA": (ALPHA, EXPECTED["ALPHA"]),
        "ETA_EFF": (ETA_EFF, EXPECTED["ETA_EFF"]),
    }
    errors: dict[str, float] = {}
    for name, (got, exp) in checks.items():
        err = abs(float(got) - float(exp))
        if err > tol:
            errors[name] = err

    s_eco = compute_scalar_fast(
        ScalarInputF(D_eff=20.0, recent_hits=3.0, delta_psi=1.5, observed=True)
    )
    s_err = abs(s_eco - EXPECTED["S_economics"])
    if s_err > 1e-12:
        errors["S_economics"] = s_err

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "S_economics": float(s_eco),
        "free_parameters": 0,
    }


def verify_authority_bytes(*, require_archive: bool = False) -> dict[str, Any]:
    """Verify local compute_authority.py SHA-256; optionally match physical archive."""
    local_sha = file_sha256(_LOCAL_AUTHORITY) if _LOCAL_AUTHORITY.is_file() else None
    archive = archive_compute_path()
    archive_sha = file_sha256(archive) if archive is not None else None

    local_ok = local_sha == AUTHORITY_SHA256
    archive_ok = (archive_sha == AUTHORITY_SHA256) if archive_sha else None

    ok = local_ok
    if require_archive:
        ok = ok and bool(archive_ok)

    return {
        "ok": ok,
        "expected": AUTHORITY_SHA256,
        "local_sha256": local_sha,
        "local_matches": local_ok,
        "archive_path": str(archive) if archive else None,
        "archive_sha256": archive_sha,
        "archive_matches": archive_ok,
        "require_archive": require_archive,
    }


def verify_fsot_gate(*, require_archive: bool = False) -> dict[str, Any]:
    """Full gate: float engine + local authority bytes (+ optional archive)."""
    eng = verify_float_engine()
    byt = verify_authority_bytes(require_archive=require_archive)
    pin = pin_metadata()
    ok = bool(eng["ok"] and byt["ok"])
    return {
        "ok": ok,
        "authority_sha256": AUTHORITY_SHA256,
        "float_engine": eng,
        "authority_bytes": byt,
        "pin": {
            "formula": pin.get("formula"),
            "free_parameters": pin.get("free_parameters"),
            "epistemic_tier": pin.get("epistemic_tier"),
        },
        "method": "fsot_authority_gate",
        "free_parameters": 0,
    }
