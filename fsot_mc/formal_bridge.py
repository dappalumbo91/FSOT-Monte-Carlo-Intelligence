"""
Formal promote / batch court loop.

MC discovery proposes leads → export obligations → soft verify against
synced certificate/cross-proof → optional archive batch scripts.

Never runs Lean per Monte Carlo path.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.paths import PACKAGE_ROOT, archive_root

BUNDLE = PACKAGE_ROOT / "vendor" / "archive_bundle"
PENDING = PACKAGE_ROOT / "data" / "obligations_pending"
PROMOTED = PACKAGE_ROOT / "data" / "obligations_promoted"
LEDGER = PACKAGE_ROOT / "data" / "formal_promotion_ledger.jsonl"


def load_synced_certificate() -> dict[str, Any] | None:
    p = BUNDLE / "data__certificate.json"
    if not p.is_file():
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
    p = BUNDLE / "data__cross_proof_verification_report.json"
    if not p.is_file():
        return None
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


def formal_status() -> dict[str, Any]:
    cert = load_synced_certificate()
    cross = load_cross_proof_summary()
    hub = archive_root()
    hub_lean = None
    if hub:
        p = hub / "02_FSOT-2.1-Lean-Full"
        hub_lean = str(p) if p.is_dir() else None
    pending_n = len(list(PENDING.glob("*.json"))) if PENDING.is_dir() else 0
    promoted_n = len(list(PROMOTED.glob("*.json"))) if PROMOTED.is_dir() else 0
    return {
        "method": "fsot_formal_soft_bridge",
        "free_parameters": 0,
        "synced_bundle": BUNDLE.is_dir(),
        "certificate_present": cert is not None,
        "certificate_proved_claims": len(cert.get("proved_claims") or []) if cert else 0,
        "cross_proof": cross,
        "archive_hub": hub_lean,
        "pending_obligations": pending_n,
        "promoted_obligations": promoted_n,
        "online_lean_per_path": False,
        "policy": "batch_court_not_per_path",
        "note": (
            "Soft court: export leads, score against synced certificate/cross-proof, "
            "optional archive batch. No per-path Lean rebuild."
        ),
    }


def export_lead_obligation(lead: dict[str, Any], out_dir: Path | None = None) -> Path:
    out_dir = out_dir or PENDING
    out_dir.mkdir(parents=True, exist_ok=True)
    lid = str(lead.get("id") or "LEAD").replace("/", "_").replace("\\", "_")
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "epistemic_tier": lead.get("epistemic_tier", "scaffold"),
        "status": "pending_formal",
        "lead": lead,
        "promotion_policy": (
            "Do not mark proved until batch court accepts. MC is proposal-only."
        ),
        "free_parameters": 0,
    }
    path = out_dir / f"{lid}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def export_discovery_leads(
    discovery: dict[str, Any],
    *,
    top_n: int = 15,
) -> dict[str, Any]:
    """Export top discovery ledger entries as pending obligations."""
    leads = (discovery.get("top_ledger") or discovery.get("discovery", {}).get("top_ledger") or [])
    if not leads and "discovery" in discovery:
        leads = discovery["discovery"].get("top_ledger") or []
    paths = []
    for lead in leads[:top_n]:
        paths.append(str(export_lead_obligation(lead)))
    return {
        "exported": len(paths),
        "paths": paths,
        "pending_dir": str(PENDING),
        "free_parameters": 0,
    }


def _score_lead_against_court(lead: dict[str, Any], cert: dict | None, cross: dict | None) -> dict[str, Any]:
    """
    Soft scoring (not a Lean rebuild):
      - cross_proof overall_ok → court is green
      - score thresholds + epistemic tier
      - optional name overlap with proved claim ids
    """
    court_green = bool(cross and cross.get("overall_ok"))
    score = float(lead.get("score") or 0.0)
    tier = str(lead.get("epistemic_tier") or "scaffold")
    lid = str(lead.get("id") or "")

    proved_ids = set()
    if cert:
        for c in cert.get("proved_claims") or []:
            if isinstance(c, dict) and c.get("id"):
                proved_ids.add(str(c["id"]))
            elif isinstance(c, str):
                proved_ids.add(c)

    name_hit = any(lid.lower() in p.lower() or p.lower() in lid.lower() for p in proved_ids)

    if not court_green:
        status = "hold_court_not_green"
        action = "re_sync_or_run_archive_cross_proof"
    elif name_hit:
        status = "linked_existing_claim"
        action = "attach_certificate_id"
    elif score >= 0.9 and tier in ("measured", "measured_application"):
        status = "promote_candidate"
        action = "queue_for_lean_panel_or_strict_empirical"
    elif score >= 0.7:
        status = "watchlist"
        action = "gather_more_paths_and_real_data"
    else:
        status = "scaffold_only"
        action = "keep_exploring"

    return {
        "id": lid,
        "status": status,
        "action": action,
        "score": score,
        "epistemic_tier": tier,
        "court_green": court_green,
        "name_hit_certificate": name_hit,
    }


def run_soft_court(
    *,
    pending_dir: Path | None = None,
    promote: bool = True,
) -> dict[str, Any]:
    """
    Batch-process pending obligations with soft court rules.
    Promotes high-confidence leads to obligations_promoted/ (still not 'proved').
    """
    pending_dir = pending_dir or PENDING
    PROMOTED.mkdir(parents=True, exist_ok=True)
    cert = load_synced_certificate()
    cross = load_cross_proof_summary()
    results = []
    promoted = []

    files = sorted(pending_dir.glob("*.json")) if pending_dir.is_dir() else []
    for f in files:
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:
            results.append({"file": str(f), "error": str(exc)})
            continue
        lead = payload.get("lead") or payload
        decision = _score_lead_against_court(lead, cert, cross)
        decision["file"] = str(f)
        results.append(decision)

        if promote and decision["status"] in ("promote_candidate", "linked_existing_claim"):
            out = {
                **payload,
                "status": decision["status"],
                "court_decision": decision,
                "promoted_at": datetime.now(timezone.utc).isoformat(),
                "note": "Promoted as candidate — not Lean-proved until batch formal run.",
            }
            dest = PROMOTED / f.name
            dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
            promoted.append(str(dest))
            # append ledger
            LEDGER.parent.mkdir(parents=True, exist_ok=True)
            with LEDGER.open("a", encoding="utf-8") as lf:
                lf.write(json.dumps(decision) + "\n")

    return {
        "method": "fsot_soft_court_batch",
        "free_parameters": 0,
        "n_pending": len(files),
        "n_promoted": len(promoted),
        "court": formal_status(),
        "results": results,
        "promoted_paths": promoted,
    }


def run_archive_cross_proof_optional(*, timeout_s: int = 120) -> dict[str, Any]:
    """
    Optionally invoke archive cross-proof script if hub + python available.
    Default: dry status only if timeout risk — use --run flag from CLI.
    """
    hub = archive_root()
    if hub is None:
        return {"ok": False, "error": "archive_root_missing"}
    lean = hub / "02_FSOT-2.1-Lean-Full"
    script = lean / "scripts" / "run_cross_proof_verification.py"
    if not script.is_file():
        return {"ok": False, "error": "cross_proof_script_missing", "path": str(script)}
    # Prefer soft: report command only unless FSOT_MC_RUN_CROSSPROOF=1
    import os

    if os.environ.get("FSOT_MC_RUN_CROSSPROOF") != "1":
        return {
            "ok": None,
            "skipped": True,
            "command": f'cd "{lean}" && python scripts/run_cross_proof_verification.py',
            "note": "Set FSOT_MC_RUN_CROSSPROOF=1 to execute (may take minutes).",
        }
    try:
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(lean),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout_tail": (proc.stdout or "")[-2000:],
            "stderr_tail": (proc.stderr or "")[-1000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "timeout_s": timeout_s}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def promote_from_intelligence(
    intel: dict[str, Any],
    *,
    top_n: int = 12,
) -> dict[str, Any]:
    """End-to-end: export intel top ledger → soft court."""
    disc = intel.get("discovery") or intel
    exported = export_discovery_leads({"top_ledger": disc.get("top_ledger") or []}, top_n=top_n)
    court = run_soft_court(promote=True)
    return {
        "method": "fsot_promote_from_intelligence",
        "free_parameters": 0,
        "exported": exported,
        "court": court,
        "formal_status": formal_status(),
    }
