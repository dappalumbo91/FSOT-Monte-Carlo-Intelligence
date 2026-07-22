"""
FSOT Discovery Engine — find new pathways, physics candidates, and bridges.

Uses Universe Monte Carlo ensembles + optional real-data anchors from the
FSOT physical archive. Does **not** trade markets.

Discovery classes:
  1. pathway_novelty     — paths that rewrite multi-domain regime structure
  2. physics_candidates  — contested-sector / unification probes
  3. bridge_candidates   — strong long-range As Above So Below couplings
  4. flip_hotspots       — domains most sensitive to observation
  5. real_data_alignment — where ensemble meets measured anchors (when available)
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, PHI, POOF
from fsot_mc.universe_atlas import get_domain, load_atlas, wave1_anchors
from fsot_mc.universe_mc import run_universe_monte_carlo

SEED_C = float(C_FACTOR)
SEED_PHI = float(PHI)
SEED_POOF = float(POOF)


def _score_bridge(strength_mean: float, strength_std: float) -> float:
    """Higher when strong and stable (seed-normalized)."""
    return float(strength_mean / (SEED_POOF + abs(strength_std)))


def classify_physics_candidates(mc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Contested / unification style candidates from ensemble.

    H0 proxy distribution vs Wave-1 measured anchors (diagnostic, not a refit).
    Quantum↔Cosmology bridge sign structure.
    """
    out: list[dict[str, Any]] = []
    ens = mc.get("ensemble") or {}
    h0 = ens.get("h0_proxy")
    anchors = wave1_anchors()
    if h0 and anchors.get("H0"):
        meas = anchors["H0"].get("measured")
        comp = anchors["H0"].get("computed")
        # Does path ensemble straddle Planck-class and local-class readouts?
        p10, p90 = h0["p10"], h0["p90"]
        span = p90 - p10
        out.append(
            {
                "id": "PHYS-H0-BRIDGE-SPAN",
                "class": "physics_candidate",
                "title": "Hubble bridge span under observer paths",
                "h0_proxy_mean": h0["mean"],
                "h0_proxy_p10": p10,
                "h0_proxy_p90": p90,
                "span": span,
                "wave1_computed": comp,
                "wave1_measured": meas,
                "score": float(min(1.0, span / max(abs(meas or 67.4) * SEED_POOF, 1e-6))),
                "hypothesis": (
                    "Observer-coupled Cosmology folds produce a distribution of H0 proxies; "
                    "wide span with stable Quantum↔Cosmos bridge suggests bubble-bleed dual-anchor structure."
                ),
                "epistemic_tier": "scaffold",
            }
        )

    lr = mc.get("long_range_bridges") or {}
    for key, payload in lr.items():
        st = payload["strength"]
        score = _score_bridge(st["mean"], st["std"])
        if abs(st["mean"]) < SEED_POOF * SEED_C:
            continue
        out.append(
            {
                "id": f"PHYS-BRIDGE-{key}",
                "class": "bridge_candidate",
                "title": f"Long-range bridge {payload['a']} ↔ {payload['b']}",
                "a": payload["a"],
                "b": payload["b"],
                "strength_mean": st["mean"],
                "strength_std": st["std"],
                "score": score,
                "hypothesis": (
                    "Stable co-emergence (or controlled decoherence) across distant D_eff folds "
                    "is an As Above So Below discovery target for formal panel follow-up."
                ),
                "epistemic_tier": "scaffold",
            }
        )

    # Rank by score
    out.sort(key=lambda x: -float(x.get("score") or 0.0))
    return out


def classify_flip_hotspots(mc: dict[str, Any], *, min_rate: float | None = None) -> list[dict[str, Any]]:
    min_rate = SEED_POOF if min_rate is None else min_rate
    de = mc.get("domain_ensemble") or {}
    hot = []
    for name, row in de.items():
        rate = float(row.get("flip_rate") or 0.0)
        if rate < min_rate:
            continue
        hot.append(
            {
                "id": f"FLIP-{name}",
                "class": "flip_hotspot",
                "domain": name,
                "cluster": row.get("cluster"),
                "D_eff": row.get("D_eff"),
                "flip_rate": rate,
                "S_canonical": row.get("S_canonical"),
                "dS_mean": row.get("dS_mean"),
                "score": rate,
                "hypothesis": (
                    f"{name} regime flips under observation more often than Poof floor — "
                    "priority domain for observer-coupled experiments and formal panels."
                ),
                "epistemic_tier": "measured_application",
            }
        )
    hot.sort(key=lambda x: -x["score"])
    return hot


def classify_pathway_novelty(mc: dict[str, Any]) -> list[dict[str, Any]]:
    """Paths that rewrite emergence fraction / flip many regimes vs canonical."""
    can = (mc.get("canonical_snapshot") or {}).get("emergence_fraction", 0.5)
    ens = (mc.get("ensemble") or {}).get("emergence_fraction") or {}
    samples = mc.get("sample_paths") or []
    out = []
    for i, p in enumerate(samples):
        ef = float(p.get("emergence_fraction") or 0.0)
        flips = int(p.get("n_regime_flips") or 0)
        delta = abs(ef - float(can))
        if delta < SEED_POOF and flips < 2:
            continue
        out.append(
            {
                "id": f"PATH-{i}",
                "class": "pathway_novelty",
                "emergence_fraction": ef,
                "canonical_emergence_fraction": can,
                "delta_emergence": delta,
                "n_regime_flips": flips,
                "regime_flips": p.get("regime_flips"),
                "mean_S": p.get("mean_S"),
                "ladder_agree_fraction": p.get("ladder_agree_fraction"),
                "score": float(delta + SEED_C * flips / 35.0),
                "hypothesis": (
                    "This observation history yields a non-canonical vitality landscape; "
                    "inspect flipped domains for new formal obligations / lab tests."
                ),
                "epistemic_tier": "scaffold",
            }
        )
    out.sort(key=lambda x: -x["score"])
    return out[:12]


def align_real_data(mc: dict[str, Any], real: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    Compare ensemble domain means to optional real-data anchors.
    `real` format: {domain: {measured_proxy: float, source: str, ...}}
    """
    if not real:
        return []
    de = mc.get("domain_ensemble") or {}
    out = []
    for domain, anchor in real.items():
        if domain not in de:
            continue
        meas = anchor.get("measured_proxy")
        if meas is None:
            continue
        pred = de[domain]["S_path_mean"]
        err = abs(pred - float(meas)) / max(abs(float(meas)), SEED_POOF)
        out.append(
            {
                "id": f"REAL-{domain}",
                "class": "real_data_alignment",
                "domain": domain,
                "S_path_mean": pred,
                "measured_proxy": float(meas),
                "rel_err": float(err),
                "source": anchor.get("source"),
                "score": float(1.0 / (1.0 + err)),
                "epistemic_tier": "measured" if err < 0.5 else "scaffold",
            }
        )
    out.sort(key=lambda x: -x["score"])
    return out


def classify_engineering_leads(
    mc: dict[str, Any],
    *,
    query: str = "",
    limit: int = 12,
) -> list[dict[str, Any]]:
    """
    Archive preregistered engineering / fuel / technology predictions as discovery leads.

    FSOT is treated as a ToE that already produces design-level predictions (fuels,
    thermochemistry, machine-molecule catalog, etc.). These are discovery *targets*
    for experiment — not free invention — and sit on the same seed engine as multipath MC.
    """
    from fsot_mc.archive_predictions import engineering_leads_for_mc, predictions_summary

    leads = engineering_leads_for_mc(mc, query=query, limit=limit)
    summary = predictions_summary()
    # Attach summary as a meta lead so mind/CLI can report inventory
    if summary.get("n_predictions"):
        leads.append(
            {
                "id": "ENG-ARCHIVE-INVENTORY",
                "class": "engineering_inventory",
                "title": "FSOT archive preregistered prediction inventory",
                "n_predictions": summary["n_predictions"],
                "n_engineering_fuel_related": summary.get("n_engineering_fuel_related"),
                "source": summary.get("source"),
                "score": 0.15,
                "hypothesis": (
                    f"{summary['n_predictions']} preregistered predictions loaded from archive bundle; "
                    f"{summary.get('n_engineering_fuel_related', 0)} fuel/thermo-related. "
                    "Each carries FSOT value, SOTA baseline, and kill discriminant."
                ),
                "epistemic_tier": "preregistered_design",
            }
        )
    return leads


def run_discovery(
    *,
    n_paths: int = 256,
    seed: int | None = 0,
    real_data: dict[str, Any] | None = None,
    store_paths: int = 24,
    scope: str = "core",
    train_pathway_memory: bool = True,
    query: str = "",
) -> dict[str, Any]:
    """
    Full discovery pipeline: universe MC → pathway memory → contested pack →
    archive engineering predictions → ledgers.
    """
    from fsot_mc.contested_physics import run_contested_physics_pack

    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        store_paths=store_paths,
        scope=scope,
        train_pathway_memory=train_pathway_memory,
    )
    if mc.get("error"):
        return mc

    physics = classify_physics_candidates(mc)
    flips = classify_flip_hotspots(mc)
    pathways = classify_pathway_novelty(mc)
    real_align = align_real_data(mc, real_data)
    engineering = classify_engineering_leads(mc, query=query, limit=12)
    contested = run_contested_physics_pack(mc)
    contested_leads = contested.get("probes") or []

    from fsot_mc.bio_emergence import analyze_biological_emergence

    bio = analyze_biological_emergence(mc, query=query)
    bio_leads = []
    if bio.get("hypothesis"):
        h = dict(bio["hypothesis"])
        h["class"] = "biological_emergence"
        bio_leads.append(h)

    pathway_mem = mc.get("pathway_memory") or {}

    # Master ranked ledger (mixed classes)
    ledger = contested_leads + physics + flips + pathways + real_align + engineering + bio_leads
    ledger.sort(key=lambda x: -float(x.get("score") or 0.0))

    # Drop internal object if present
    mc_public = {k: v for k, v in mc.items() if not k.startswith("_")}

    return {
        "error": None,
        "method": "fsot_universe_discovery",
        "free_parameters": 0,
        "purpose": "Discover new pathways and physics under FSOT law — not markets",
        "scope": mc_public.get("scope"),
        "n_domains": mc_public.get("n_domains"),
        "monte_carlo": {
            "n_paths": mc_public["n_paths"],
            "ensemble": mc_public["ensemble"],
            "canonical_snapshot": mc_public["canonical_snapshot"],
            "atlas": mc_public["atlas"],
        },
        "pathway_memory": pathway_mem,
        "contested_physics": contested,
        "candidates": {
            "contested": contested_leads[:15],
            "physics": physics[:15],
            "bridges": [c for c in physics if c["class"] == "bridge_candidate"][:15],
            "flip_hotspots": flips[:15],
            "novel_pathways": pathways[:12],
            "real_data": real_align[:20],
            "engineering": engineering[:15],
            "biological_emergence": bio_leads[:5],
        },
        "biological_emergence": bio,
        "top_ledger": ledger[:30],
        "domain_ensemble": mc_public["domain_ensemble"],
        "long_range_bridges": mc_public["long_range_bridges"],
        "sample_paths": mc_public.get("sample_paths"),
        "epistemic_note": (
            "Candidates are discovery *leads* for formal verification and lab panels. "
            "Engineering predictions (fuels, devices) are FSOT-derived designs with preregistered "
            "discriminants — high precision raises prior confidence; physical build still required. "
            "Biological ~69% map occupancy is dual-framed: operational co-emergence + paradigm "
            "natural complexity/energy window for life folds. Proved claims live in FSOT-2.1-Lean."
        ),
        "note": (
            "Universe Monte Carlo intelligence under Fluid Spacetime Omni-Theory (ToE paradigm shift). "
            "Maps domains → pathways → bridges → physics + engineering + bio-emergence. free_parameters=0."
        ),
    }
