"""
Experiment protocol cards for preregistered FSOT predictions.

Each card: hypothesis, discriminant/kill criteria, materials, measurement,
pass/fail — ready for lab bench. free_parameters = 0.
"""

from __future__ import annotations

from typing import Any

from fsot_mc.archive_predictions import load_preregistered_predictions, match_predictions


def protocol_card(pred: dict[str, Any]) -> dict[str, Any]:
    pid = pred.get("id")
    name = pred.get("name")
    domain = pred.get("domain")
    fsot = pred.get("fsot_predicted")
    unit = pred.get("unit") or ""
    sota = pred.get("sota_baseline")
    sota_label = pred.get("sota_label")
    disc = pred.get("discriminant")
    note = pred.get("note") or ""
    branch = pred.get("fsot_formula_branch") or pred.get("formula_branch")

    return {
        "id": pid,
        "title": f"Protocol {pid}: {name}",
        "domain": domain,
        "epistemic_tier": "preregistered_design",
        "free_parameters": 0,
        "hypothesis": (
            f"Under FSOT seed engine (branch {branch}), observable '{name}' evaluates to "
            f"{fsot} {unit}, with discriminant '{disc}' versus SOTA {sota} ({sota_label})."
        ),
        "fsot_predicted": fsot,
        "unit": unit,
        "sota_baseline": sota,
        "sota_label": sota_label,
        "discriminant": disc,
        "formula_branch": branch,
        "materials_methods": [
            "Use same seed engine authority D1D38A (no free-parameter retune).",
            "Record computed FSOT value from archive panel or recompute path.",
            "Record independent measured / SOTA reference under stated label.",
            f"Apply discriminant: {disc}.",
            "Log environment, software pin, and timestamp for reproducibility.",
        ],
        "measurements": [
            {"quantity": "fsot_value", "target": fsot, "unit": unit},
            {"quantity": "sota_or_measured", "target": sota, "unit": unit, "label": sota_label},
            {"quantity": "relative_error_pct", "formula": "100*|fsot-meas|/|meas|"},
        ],
        "pass_criteria": [
            f"Discriminant satisfied: {disc}",
            "No post-hoc seed or constant retuning",
            "Pin D1D38A verified at run time",
        ],
        "kill_criteria": [
            f"Discriminant fails on pre-registered threshold: {disc}",
            "Requires free-parameter fit to match measured value",
            "Authority pin mismatch or engine drift",
        ],
        "notes": note,
        "status": "ready_for_experiment",
    }


def list_protocol_cards(*, query: str = "", limit: int = 20) -> dict[str, Any]:
    if query:
        preds = match_predictions(query, limit=limit)
        # match_predictions returns enriched; reload full fields if needed
        full = {p.get("id"): p for p in load_preregistered_predictions()}
        cards = []
        for p in preds:
            base = full.get(p.get("id"), p)
            merged = {**base, **p}
            cards.append(protocol_card(merged))
    else:
        preds = load_preregistered_predictions()[:limit]
        cards = [protocol_card(p) for p in preds]
    return {
        "ok": True,
        "n": len(cards),
        "cards": cards,
        "free_parameters": 0,
        "note": "Preregistered experiment protocols — bench still closes engineering claims.",
    }


def get_protocol(pred_id: str) -> dict[str, Any] | None:
    for p in load_preregistered_predictions():
        if str(p.get("id")) == str(pred_id):
            return protocol_card(p)
    return None
