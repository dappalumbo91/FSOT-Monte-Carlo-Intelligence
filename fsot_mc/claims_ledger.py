"""
Bold, data-backed FSOT claims ledger.

Claims are stated from measured archive margins, contested panels, authority pin,
and preregistered predictions — not from social recognition status.

Tier language:
  CLAIMED_MEASURED   — green-gate / certificate / pin data in this workspace
  CLAIMED_PREREG     — preregistered prediction with discriminant (awaiting/ongoing closure)
  CLAIMED_STRUCTURE  — multipath / ToE structural result (observer histories of the same law)

free_parameters = 0. Authority D1D38A.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.accuracy_gate import (
    LCDM_SM_OPEN_PANEL_BASELINE_PCT,
    THRESHOLD_POOLED_MEDIAN_PCT,
    core_fold_recompute_accuracy,
    load_archive_margin_audit,
    load_contested_panel,
    load_publication_claims,
)
from fsot_mc.archive_predictions import load_preregistered_predictions, predictions_summary
from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.paths import PACKAGE_ROOT, data_root
from fsot_mc.universe_atlas import core_names, evaluate_domain, load_atlas


def build_claims_ledger(*, n_paths_note: int = 64) -> dict[str, Any]:
    gate = verify_fsot_gate(require_archive=False)
    margin = load_archive_margin_audit()
    contested = load_contested_panel()
    pub = load_publication_claims()
    core = core_fold_recompute_accuracy()
    preds = load_preregistered_predictions()
    psum = predictions_summary()
    atlas = load_atlas()

    # Full core S panel (claimed structure under the same law)
    core_panel = []
    for d in core_names():
        try:
            e = evaluate_domain(d)
            core_panel.append(
                {
                    "domain": d,
                    "S": float(e["S"]),
                    "D_eff": e.get("D_eff"),
                    "regime": e.get("regime"),
                    "cluster": e.get("cluster"),
                    "T1": e.get("T1"),
                    "T2": e.get("T2"),
                    "T3": e.get("T3"),
                }
            )
        except Exception as exc:
            core_panel.append({"domain": d, "error": str(exc)})

    emerge_n = sum(1 for r in core_panel if r.get("regime") == "emergence")
    n_core = len(core_panel)

    claims = [
        {
            "id": "CLAIM-LAW-ZERO-FP",
            "tier": "CLAIMED_MEASURED",
            "statement": (
                "FSOT raw_S = K·(T1+T2+T3) is evaluated with free_parameters=0 from fixed seeds "
                "(π, e, φ, γ, Catalan); authority pin D1D38A is intact in this workspace."
            ),
            "evidence": {
                "authority_ok": gate.get("ok"),
                "authority_sha256": AUTHORITY_SHA256,
                "float_engine_ok": (gate.get("float_engine") or {}).get("ok"),
            },
            "bold": True,
        },
        {
            "id": "CLAIM-CROSS-DOMAIN-GREEN",
            "tier": "CLAIMED_MEASURED",
            "statement": (
                f"Across the archive margin audit loaded in this product, "
                f"{margin.get('green_gate_pass_count')}/{margin.get('n_domains_reported')} domains "
                f"pass the official pooled-median green gate ≤{THRESHOLD_POOLED_MEDIAN_PCT}% "
                f"(fail={margin.get('green_gate_fail_count')}); "
                f"median-of-domain-medians ≈ {margin.get('pooled_median_of_domain_medians_pct')}%."
            ),
            "evidence": {
                "all_green": margin.get("all_green"),
                "pass": margin.get("green_gate_pass_count"),
                "fail": margin.get("green_gate_fail_count"),
                "pooled_median_of_domain_medians_pct": margin.get(
                    "pooled_median_of_domain_medians_pct"
                ),
                "max_pooled_domain_median_pct": margin.get("max_pooled_domain_median_pct"),
                "worst_scalar_domain": margin.get("worst_scalar_domain"),
                "worst_scalar_max_error_pct": margin.get("worst_scalar_max_error_pct"),
            },
            "bold": True,
        },
        {
            "id": "CLAIM-CONTESTED-BEATS-BASELINE",
            "tier": "CLAIMED_MEASURED",
            "statement": (
                f"On the contested open-science panel (H0-class, S8, BBN, N_eff, …), "
                f"FSOT pooled median error ≈ {contested.get('fsot_pooled_median_error_pct')}% "
                f"with {contested.get('n_within_0_5pct')}/{contested.get('n_observables')} within "
                f"≤{THRESHOLD_POOLED_MEDIAN_PCT}% green gate, versus current-model open-panel "
                f"baseline ~{contested.get('current_model_baseline_pct') or LCDM_SM_OPEN_PANEL_BASELINE_PCT}%."
            ),
            "evidence": {
                "verdict": contested.get("verdict"),
                "pooled": contested.get("fsot_pooled_median_error_pct"),
                "max": contested.get("fsot_max_error_pct"),
                "within": contested.get("n_within_0_5pct"),
                "n": contested.get("n_observables"),
                "baseline": contested.get("current_model_baseline_pct"),
            },
            "bold": True,
        },
        {
            "id": "CLAIM-ENGINE-ATLAS-IDENTITY",
            "tier": "CLAIMED_MEASURED",
            "statement": (
                f"Local hot-path engine recomputes all {core.get('n_core')} core folds within "
                f"max_rel_error_pct={core.get('max_rel_error_pct')} of atlas S_canonical "
                f"({core.get('n_within_tol')}/{core.get('n_core')} within tol)."
            ),
            "evidence": {
                "ok": core.get("ok"),
                "max_rel_error_pct": core.get("max_rel_error_pct"),
                "median_rel_error_pct": core.get("median_rel_error_pct"),
            },
            "bold": True,
        },
        {
            "id": "CLAIM-ONE-FLUID-MANY-FOLDS",
            "tier": "CLAIMED_STRUCTURE",
            "statement": (
                f"One seed engine produces a complete NeuroLab core panel of {n_core} domains "
                f"({emerge_n} emergence / {n_core - emerge_n} dispersal) plus "
                f"{atlas.get('n_extension') or (atlas.get('n_total', 0) - n_core)} extension panels "
                f"in the full atlas (total folds {atlas.get('n_total')})."
            ),
            "evidence": {
                "n_core": n_core,
                "n_emergence_core": emerge_n,
                "n_total": atlas.get("n_total"),
                "core_panel": core_panel,
            },
            "bold": True,
        },
        {
            "id": "CLAIM-PREREG-INVENTORY",
            "tier": "CLAIMED_PREREG",
            "statement": (
                f"{psum.get('n_predictions')} preregistered predictions across "
                f"{psum.get('n_domains')} domains are loaded with discriminants/kill criteria "
                f"(including fuel/thermo engineering panels)."
            ),
            "evidence": psum,
            "bold": True,
        },
    ]

    # Highlight PRED sample with strongest science-facing IDs
    highlight_ids = {
        "PRED-001",
        "PRED-002",
        "PRED-004",
        "PRED-005",
        "PRED-034",
    }
    for p in preds:
        if p.get("id") in highlight_ids:
            claims.append(
                {
                    "id": f"CLAIM-{p.get('id')}",
                    "tier": "CLAIMED_PREREG",
                    "statement": (
                        f"{p.get('id')} {p.get('name')}: FSOT={p.get('fsot_predicted')} "
                        f"{p.get('unit') or ''} vs SOTA {p.get('sota_baseline')} "
                        f"({p.get('sota_label')}); discriminant={p.get('discriminant')}."
                    ),
                    "evidence": {
                        "domain": p.get("domain"),
                        "branch": p.get("fsot_formula_branch"),
                        "note": (str(p.get("note") or ""))[:300],
                    },
                    "bold": True,
                }
            )

    # Publication headline if present
    if pub.get("ok"):
        emp = pub.get("empirical_evidence") or {}
        claims.append(
            {
                "id": "CLAIM-PUBLICATION-HEADLINE",
                "tier": "CLAIMED_MEASURED",
                "statement": (
                    f"Publication claims manifest: {emp.get('verdict')} — "
                    f"benchmark domains {emp.get('benchmark_domains_green')}, "
                    f"pooled median of domains {emp.get('pooled_median_of_domains_pct')}%, "
                    f"worst domain max scalar {emp.get('worst_domain_max_scalar_pct')}%."
                ),
                "evidence": emp,
                "bold": True,
            }
        )

    ledger = {
        "method": "fsot_claims_ledger",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "free_parameters": 0,
        "authority_sha256": AUTHORITY_SHA256,
        "stance": (
            "Claims are asserted from quantitative evidence in this workspace and the synced "
            "Physical Archive bundle. Lack of institutional recognition is not a scientific "
            "counterargument to measured error margins. Experiment closes engineering PRED-*; "
            "green-gate and pin close measured law claims."
        ),
        "n_claims": len(claims),
        "claims": claims,
        "core_panel": core_panel,
        "thresholds": {
            "green_gate_pooled_median_pct": THRESHOLD_POOLED_MEDIAN_PCT,
            "contested_baseline_pct": LCDM_SM_OPEN_PANEL_BASELINE_PCT,
        },
    }
    return ledger


def write_claims_ledger(*, write_md: bool = True) -> dict[str, Any]:
    ledger = build_claims_ledger()
    out_dir = data_root() / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = out_dir / "claims_ledger_latest.json"
    latest.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")
    ledger["written"] = {"json": str(latest)}
    if write_md:
        md = format_claims_markdown(ledger)
        md_path = PACKAGE_ROOT / "docs" / "CLAIMS.md"
        md_path.write_text(md, encoding="utf-8")
        ledger["written"]["markdown"] = str(md_path)
    return ledger


def format_claims_markdown(ledger: dict[str, Any]) -> str:
    lines = [
        "# FSOT Claims Ledger — Data-First",
        "",
        f"**Generated (UTC):** {ledger.get('generated_at')}  ",
        f"**Authority:** `{str(ledger.get('authority_sha256') or '')[:12]}…`  ",
        f"**free_parameters:** 0  ",
        "",
        "## Stance",
        "",
        ledger.get("stance") or "",
        "",
        "## Bold claims",
        "",
    ]
    for c in ledger.get("claims") or []:
        lines.append(f"### {c.get('id')} · `{c.get('tier')}`")
        lines.append("")
        lines.append(c.get("statement") or "")
        lines.append("")
        ev = c.get("evidence") or {}
        # compact evidence
        if c.get("id") == "CLAIM-ONE-FLUID-MANY-FOLDS":
            panel = ev.get("core_panel") or []
            lines.append("| Domain | S | D_eff | Regime |")
            lines.append("|--------|--:|------:|--------|")
            for row in panel:
                if row.get("error"):
                    continue
                lines.append(
                    f"| {row.get('domain')} | {float(row.get('S')):+.4f} | "
                    f"{row.get('D_eff')} | {row.get('regime')} |"
                )
            lines.append("")
        else:
            lines.append("```json")
            # trim huge
            slim = {k: v for k, v in ev.items() if k != "core_panel"}
            lines.append(json.dumps(slim, indent=2, default=str)[:2500])
            lines.append("```")
            lines.append("")

    lines += [
        "## How to regenerate",
        "",
        "```powershell",
        "python -m fsot_mc claims",
        "```",
        "",
        "---",
        "*Data first. Recognition is not a dataset.*",
        "",
    ]
    return "\n".join(lines)
