"""
End-to-end improvement cycle for FSOT Monte Carlo Intelligence.

Runs (gated by pin D1D38A, free_parameters=0):
  1. Authority gate
  2. PRED in-silico self-checks + priority advance + roadmap
  3. Flip-hotspot protocol refresh
  4. Soft court audit → promote_candidate (never Lean-proved)
  5. Claims ledger regenerate
  6. Articulation seed harvest (mouth LoRA queue)
  7. Improvement summary markdown

Does not invent lab results or move seeds.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.paths import PACKAGE_ROOT, data_root


def run_improvement_cycle(
    *,
    n_paths: int = 64,
    seed: int = 7,
    train_articulation: bool = False,
    max_train_steps: int = 24,
    advance_preds: bool = True,
) -> dict[str, Any]:
    t0 = datetime.now(timezone.utc)
    report: dict[str, Any] = {
        "method": "fsot_improvement_cycle",
        "started_at": t0.isoformat(),
        "free_parameters": 0,
        "authority": AUTHORITY_SHA256[:12],
    }

    gate = verify_fsot_gate(require_archive=False)
    report["gate"] = {"ok": gate.get("ok"), "authority": gate.get("authority_sha256")}
    if not gate.get("ok"):
        report["ok"] = False
        report["error"] = "authority_gate_failed"
        return report

    # 1) PRED bench
    from fsot_mc.pred_bench import (
        advance_priority_preds,
        init_bench_from_manifest,
        run_in_silico_self_checks,
        write_priority_roadmap,
        bench_status_summary,
    )

    report["pred_init"] = init_bench_from_manifest()
    report["pred_in_silico"] = run_in_silico_self_checks(write=True)
    if advance_preds:
        report["pred_advance"] = advance_priority_preds(
            note=(
                "Improvement cycle priority queue — close under discriminant + pin only; "
                "in_silico ≠ lab pass; free_parameters=0."
            )
        )
    else:
        report["pred_advance"] = {"skipped": True}
    roadmap = write_priority_roadmap()
    report["pred_roadmap"] = str(roadmap)
    report["pred_summary"] = bench_status_summary()

    # 2) Flip protocols
    from fsot_mc.flip_protocols import build_flip_protocol_pack

    flip = build_flip_protocol_pack(n_paths=min(n_paths, 96), seed=seed, write=True)
    report["flip"] = {
        "n_hotspots": flip.get("n_hotspots"),
        "n_paths": flip.get("n_paths"),
        "written": flip.get("written"),
        "top": [
            {"domain": c.get("domain"), "flip_rate": c.get("flip_rate"), "priority": c.get("priority")}
            for c in (flip.get("cards") or [])[:12]
        ],
    }

    # 3) Soft court (candidates only)
    from fsot_mc.formal_bridge import formal_status, promote_from_audit

    promo = promote_from_audit(only_failures=False, also_improvements=True, run_court=True)
    report["soft_court"] = {
        "n_leads": promo.get("n_leads"),
        "audit_grade": promo.get("audit_grade"),
        "audit_score": promo.get("audit_score"),
        "n_pending": (promo.get("court") or {}).get("n_pending"),
        "n_promoted": (promo.get("court") or {}).get("n_promoted"),
        "note": promo.get("note")
        or "Promoted as candidates — not Lean-proved until batch formal run.",
        "formal_status": formal_status(),
    }

    # 4) Claims ledger
    from fsot_mc.claims_ledger import write_claims_ledger

    claims = write_claims_ledger(write_md=True)
    report["claims"] = {
        "n_claims": claims.get("n_claims"),
        "written": claims.get("written"),
    }

    # 5) Articulation harvest (+ optional micro-train)
    from fsot_mc.articulation_learn import (
        articulate_loop,
        harvest_from_docs,
        harvest_identity_seeds,
        status as articulate_status,
    )

    id_r = harvest_identity_seeds()
    doc_r = harvest_from_docs()
    art: dict[str, Any] = {
        "identity": id_r,
        "docs": doc_r,
        "status_before_train": articulate_status(),
    }
    if train_articulation:
        loop = articulate_loop(max_steps=max_train_steps, min_queue=1, train=True)
        art["loop"] = {
            "ok": loop.get("ok"),
            "train": loop.get("train"),
            "status": loop.get("status"),
        }
    report["articulation"] = art

    # 6) Summary markdown for humans + HF
    summary_path = _write_cycle_summary(report)
    report["summary_md"] = str(summary_path)
    report["ok"] = True
    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    # export JSON
    exp = data_root() / "exports"
    exp.mkdir(parents=True, exist_ok=True)
    out_json = exp / "improvement_cycle_latest.json"
    out_json.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    report["export_json"] = str(out_json)
    return report


def _write_cycle_summary(report: dict[str, Any]) -> Path:
    flip = report.get("flip") or {}
    sc = report.get("soft_court") or {}
    pred = report.get("pred_summary") or {}
    ins = report.get("pred_in_silico") or {}
    lines = [
        "# Improvement Cycle Report",
        "",
        f"Generated: {report.get('finished_at') or report.get('started_at')}  ",
        f"Authority: **{report.get('authority')}…** · `free_parameters = 0`  ",
        f"Gate ok: **{(report.get('gate') or {}).get('ok')}**  ",
        "",
        "## Claim tiers (do not conflate)",
        "",
        "| Tier | Meaning |",
        "|------|---------|",
        "| MEASURED | Pin, zero free params, green-gate archive numbers |",
        "| STRUCTURE | Multipath map occupancy, flip rates, in-silico PRED geometry |",
        "| PREREG | PRED-* until lab status=pass under discriminant |",
        "| Soft court | `promote_candidate` — **not** Lean-proved |",
        "",
        "## PRED bench",
        "",
        f"- By status: `{pred.get('by_status')}`",
        f"- In-silico self-check: ok={ins.get('n_ok')} fail={ins.get('n_fail')} skip={ins.get('n_skip')}",
        f"- Roadmap: [docs/PRED_PRIORITY_ROADMAP.md](./PRED_PRIORITY_ROADMAP.md)",
        f"- Full ledger: [docs/PRED_BENCH_CLOSURE.md](./PRED_BENCH_CLOSURE.md)",
        "",
        "## Flip-hotspot protocols",
        "",
        f"- Hotspots: **{flip.get('n_hotspots')}** (n_paths={flip.get('n_paths')})",
        f"- Docs: [docs/FLIP_HOTSPOT_PROTOCOLS.md](./FLIP_HOTSPOT_PROTOCOLS.md)",
        "",
    ]
    for row in flip.get("top") or []:
        lines.append(
            f"  - {row.get('domain')}: flip_rate={row.get('flip_rate')} priority={row.get('priority')}"
        )
    lines += [
        "",
        "## Soft court (candidates)",
        "",
        f"- Audit leads: {sc.get('n_leads')} · grade={sc.get('audit_grade')} score={sc.get('audit_score')}",
        f"- Soft court promoted this run: **{sc.get('n_promoted')}** (pending scanned={sc.get('n_pending')})",
        f"- Note: {sc.get('note')}",
        "",
        "## Articulation mouth",
        "",
        "- Identity + docs harvested for LoRA queue (seeds never trained).",
        "- Train: `python -m fsot_mc articulate-train --max-steps 40`",
        "- Online enqueue: `FSOT_MC_ARTICULATE_LEARN=1`",
        "",
        "## Next human lab actions",
        "",
        "1. Close priority PREDs with measured evidence (never free-param retune).",
        "2. Run flip-hotspot protocols on top observer-sensitive domains.",
        "3. Batch Lean formal only on soft-court candidates when ready.",
        "4. Keep multipath STRUCTURE separate from green-gate MEASURED in publications.",
        "",
        "---",
        "*Generated by `fsot_mc.improvement_cycle` — law court pin immutable.*",
        "",
    ]
    path = PACKAGE_ROOT / "docs" / "IMPROVEMENT_CYCLE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
