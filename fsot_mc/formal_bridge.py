"""
Soft bridge: Monte Carlo discovery leads ↔ FSOT formal verification court.

Hard rule: formal spine is a *batch court*, not an online per-path solver.

Soft path (this module):
  1) Export lead as candidate obligation JSON
  2) Optionally invoke archive verification scripts if hub present
  3) Attach certificate / report refs when available from synced bundle
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.paths import PACKAGE_ROOT, archive_root

BUNDLE = PACKAGE_ROOT / "vendor" / "archive_bundle"


def load_synced_certificate() -> dict[str, Any] | None:
    p = BUNDLE / "data__certificate.json"
    if not p.is_file():
        # try alternate naming
        for cand in BUNDLE.glob("*certificate*"):
            p = cand
            break
        else:
            return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_cross_proof_summary() -> dict[str, Any] | None:
    for name in ("data__cross_proof_verification_report.json",):
        p = BUNDLE / name
        if p.is_file():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                return {
                    "overall_ok": raw.get("overall_ok"),
                    "github_ready": raw.get("github_ready"),
                    "seven_way_bare_metal": raw.get("seven_way_bare_metal"),
                    "generated_at": raw.get("generated_at"),
                    "source": str(p),
                }
            except Exception:
                return None
    return None


def export_lead_obligation(lead: dict[str, Any], out_dir: Path | None = None) -> Path:
    """Write a discovery lead as a candidate for formal / numeric promotion."""
    out_dir = out_dir or (PACKAGE_ROOT / "data" / "obligations_pending")
    out_dir.mkdir(parents=True, exist_ok=True)
    lid = str(lead.get("id") or "LEAD").replace("/", "_")
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "epistemic_tier": lead.get("epistemic_tier", "scaffold"),
        "status": "pending_formal",
        "lead": lead,
        "promotion_policy": (
            "Do not mark proved until Lean/cross-proof batch accepts a numeric obligation. "
            "MC discovery is proposal-only."
        ),
        "free_parameters": 0,
    }
    path = out_dir / f"{lid}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def formal_status() -> dict[str, Any]:
    """What formal evidence is locally available to the MC intelligence."""
    cert = load_synced_certificate()
    cross = load_cross_proof_summary()
    hub = archive_root()
    hub_lean = None
    if hub:
        p = hub / "02_FSOT-2.1-Lean-Full"
        hub_lean = str(p) if p.is_dir() else None
    return {
        "method": "fsot_formal_soft_bridge",
        "free_parameters": 0,
        "synced_bundle": BUNDLE.is_dir(),
        "certificate_present": cert is not None,
        "certificate_proved_claims": len(cert.get("proved_claims") or []) if cert else 0,
        "cross_proof": cross,
        "archive_hub": hub_lean,
        "online_lean_per_path": False,
        "policy": "batch_court_not_per_path",
        "note": (
            "Connecting formal verification is easy at the *soft* layer (export + batch). "
            "Running full multi-prover rebuild per Monte Carlo path is intentionally unsupported."
        ),
    }
