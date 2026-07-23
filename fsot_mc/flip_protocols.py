"""
Flip-hotspot experiment protocol cards.

Domains with high multipath flip_rate are observer-sensitive folds.
Each card: hypothesis, measurements, pass/kill, linked PRED/archive notes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fsot_mc.fast import POOF
from fsot_mc.paths import PACKAGE_ROOT, data_root
from fsot_mc.universe_atlas import core_names, evaluate_domain
from fsot_mc.universe_mc import run_universe_monte_carlo

SEED_POOF = float(POOF)


def measure_flip_hotspots(
    *,
    n_paths: int = 96,
    seed: int = 7,
    min_rate: float | None = None,
) -> list[dict[str, Any]]:
    min_rate = SEED_POOF if min_rate is None else float(min_rate)
    cores = list(core_names())
    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        domains=cores,
        store_paths=8,
        train_pathway_memory=False,
    )
    de = mc.get("domain_ensemble") or {}
    hot = []
    for d in cores:
        row = de.get(d) or {}
        rate = float(row.get("flip_rate") or 0.0)
        try:
            ev = evaluate_domain(d)
            S_can = float(ev["S"])
            regime = ev.get("regime")
            D = ev.get("D_eff")
            cluster = ev.get("cluster")
        except Exception:
            S_can = row.get("S_canonical")
            regime = None
            D = row.get("D_eff")
            cluster = row.get("cluster")
        if rate < min_rate:
            continue
        hot.append(
            {
                "domain": d,
                "flip_rate": rate,
                "S_path_mean": row.get("S_path_mean"),
                "S_canonical": S_can,
                "D_eff": D,
                "cluster": cluster,
                "regime": regime or ("emergence" if (S_can or 0) > 0 else "dispersal"),
                "n_paths": mc.get("n_paths"),
            }
        )
    hot.sort(key=lambda x: -float(x["flip_rate"]))
    return hot


def protocol_card_for_flip(h: dict[str, Any]) -> dict[str, Any]:
    d = h["domain"]
    rate = float(h["flip_rate"])
    return {
        "id": f"FLIP-PROTO-{d}",
        "class": "flip_hotspot_protocol",
        "title": f"Observer protocol: {d} flip hotspot",
        "domain": d,
        "epistemic_tier": "measured_application",
        "free_parameters": 0,
        "flip_rate": rate,
        "S_canonical": h.get("S_canonical"),
        "S_path_mean": h.get("S_path_mean"),
        "D_eff": h.get("D_eff"),
        "cluster": h.get("cluster"),
        "hypothesis": (
            f"{d} flips regime under multipath observer coupling at rate {rate:.3f} "
            f"(≥ Poof floor {SEED_POOF:.4f}). Same seed engine; observer branch selection "
            f"alters path-mean S relative to canonical S={h.get('S_canonical')}."
        ),
        "materials_methods": [
            "Fix authority pin D1D38A; free_parameters=0.",
            f"Run multipath MC with n_paths≥64 on core set including {d}; record flip_rate and path-mean S.",
            "Vary observer coupling (observed=True/False, δψ noise) without changing seeds.",
            "Log canonical S vs path ensemble (p10/p50/p90 of S on this fold).",
            "If lab/instrument exists for this domain, pre-register observable + kill threshold.",
        ],
        "measurements": [
            {"quantity": "flip_rate", "target": rate, "unit": "fraction_of_paths"},
            {"quantity": "S_canonical", "value": h.get("S_canonical")},
            {"quantity": "S_path_mean", "value": h.get("S_path_mean")},
            {"quantity": "D_eff", "value": h.get("D_eff")},
        ],
        "pass_criteria": [
            "flip_rate reproducible within ±0.05 across seeds for same n_paths",
            "Seeds/pin unchanged",
            "Canonical S matches atlas recompute",
        ],
        "kill_criteria": [
            "flip_rate collapses to 0 under all observer settings while claiming observer-sensitivity",
            "Requires free-parameter retune to match path statistics",
            "Authority pin mismatch",
        ],
        "priority": "high" if rate >= 0.5 else "medium",
        "status": "ready_for_experiment",
    }


def build_flip_protocol_pack(
    *,
    n_paths: int = 96,
    seed: int = 7,
    write: bool = True,
) -> dict[str, Any]:
    hot = measure_flip_hotspots(n_paths=n_paths, seed=seed)
    cards = [protocol_card_for_flip(h) for h in hot]
    pack = {
        "method": "fsot_flip_hotspot_protocols",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "free_parameters": 0,
        "n_hotspots": len(cards),
        "min_rate_floor": SEED_POOF,
        "n_paths": n_paths,
        "cards": cards,
        "note": (
            "Observer-sensitive folds from full-core multipath. "
            "These are experiment priorities under the same ToE law."
        ),
    }
    if write:
        out = data_root() / "exports"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "flip_protocols_latest.json"
        path.write_text(json.dumps(pack, indent=2, default=str), encoding="utf-8")
        # also markdown summary
        md_path = PACKAGE_ROOT / "docs" / "FLIP_HOTSPOT_PROTOCOLS.md"
        lines = [
            "# Flip-Hotspot Experiment Protocols",
            "",
            f"Generated: {pack['generated_at']}  ",
            f"Hotspots: **{len(cards)}** (flip_rate ≥ Poof={SEED_POOF:.4f})  ",
            f"n_paths={n_paths}  · free_parameters=0  ",
            "",
            "| Domain | Flip rate | S_can | S_path | D_eff | Priority |",
            "|--------|----------:|------:|-------:|------:|----------|",
        ]
        for c in cards:
            lines.append(
                f"| {c['domain']} | {c['flip_rate']:.3f} | {c.get('S_canonical')} | "
                f"{c.get('S_path_mean')} | {c.get('D_eff')} | {c.get('priority')} |"
            )
        lines += ["", "## Cards", ""]
        for c in cards:
            lines.append(f"### {c['id']}")
            lines.append("")
            lines.append(c["hypothesis"])
            lines.append("")
            lines.append("**Kill:** " + "; ".join(c["kill_criteria"]))
            lines.append("")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        pack["written"] = {"json": str(path), "markdown": str(md_path)}
    return pack
