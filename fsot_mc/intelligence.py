"""
FSOT Monte Carlo Intelligence — universe discovery API (primary).

Full stack:
  atlas → multipath MC → pathway memory → contested → π-ring eyes
  → formal soft court → optional Realities/API anchors
"""

from __future__ import annotations

from typing import Any

from fsot_mc.authority_gate import verify_fsot_gate
from fsot_mc.discovery import run_discovery
from fsot_mc.formal_bridge import promote_from_intelligence
from fsot_mc.pflt_bridge import eyes_with_mc
from fsot_mc.real_data import build_real_data_bundle
from fsot_mc.universe_atlas import atlas_meta, domains_by_cluster, snapshot_universe
from fsot_mc.universe_mc import run_universe_monte_carlo


def run_intelligence(
    *,
    n_paths: int = 256,
    seed: int | None = 0,
    use_real_data: bool = True,
    store_paths: int = 24,
    scope: str = "core",
    with_eyes: bool = True,
    with_formal_promote: bool = False,
    with_realities: bool = False,
    with_apis: bool = False,
    vision_mode: str = "auto",
) -> dict[str, Any]:
    """
    Primary intelligence entrypoint — universe discovery under FSOT law.

    scope: "core" | "full" | "extensions"
    with_eyes: π-ring + PFLT/fallback sensory projection
    with_formal_promote: export top leads + soft court batch
    with_realities: poll Realities OS runtime (if present)
    with_apis: offline-first API anchors (FSOT_MC_ONLINE=1 for network)
    """
    gate = verify_fsot_gate(require_archive=False)
    if not gate["ok"]:
        return {
            "error": "fsot_authority_gate_failed",
            "authority_gate": gate,
            "free_parameters": 0,
        }

    real_bundle = build_real_data_bundle(use_archive=use_real_data) if use_real_data else None
    anchors = dict((real_bundle or {}).get("anchors") or {})

    api_bundle = None
    if with_apis:
        from fsot_mc.api_adapters import run_api_bundle, seed_demo_cache

        seed_demo_cache()  # ensure offline demos exist
        api_bundle = run_api_bundle()
        for k, v in (api_bundle.get("anchors") or {}).items():
            anchors[k] = v

    realities = None
    if with_realities:
        from fsot_mc.realities_client import couple_to_intelligence

        realities = couple_to_intelligence(project_ring=True)

    discovery = run_discovery(
        n_paths=n_paths,
        seed=seed,
        real_data=anchors,
        store_paths=store_paths,
        scope=scope,
        train_pathway_memory=True,
    )
    if discovery.get("error"):
        return discovery

    meta = atlas_meta()
    names = None
    if scope == "core" and meta.get("n_core"):
        from fsot_mc.universe_atlas import core_names

        names = core_names()
    canonical = snapshot_universe(names=names)

    eyes = None
    if with_eyes:
        eyes = eyes_with_mc(
            {"domain_ensemble": discovery.get("domain_ensemble") or {}},
            text="FSOT universe discovery",
            vision_mode=vision_mode,
        )

    formal = None
    if with_formal_promote:
        formal = promote_from_intelligence(
            {"discovery": discovery},
            top_n=12,
        )

    return {
        "error": None,
        "method": "fsot_universe_monte_carlo_intelligence",
        "free_parameters": 0,
        "purpose": "Simulate the universe under FSOT; discover pathways and physics — not markets",
        "scope": scope,
        "authority_gate": gate,
        "atlas": meta,
        "clusters": {k: len(v) for k, v in domains_by_cluster().items()},
        "canonical_universe": {
            "emergence_fraction": canonical["emergence_fraction"],
            "mean_S": canonical["mean_S"],
            "n_emergence": canonical["n_emergence"],
            "n_dispersal": canonical["n_dispersal"],
            "n_domains": canonical["n_domains"],
        },
        "discovery": {
            "top_ledger": discovery["top_ledger"],
            "candidates": discovery["candidates"],
            "ensemble": discovery["monte_carlo"]["ensemble"],
            "pathway_memory": discovery.get("pathway_memory"),
            "contested_physics": discovery.get("contested_physics"),
        },
        "eyes": eyes,
        "formal": formal,
        "realities": realities,
        "apis": api_bundle,
        "domain_ensemble": discovery["domain_ensemble"],
        "long_range_bridges": discovery["long_range_bridges"],
        "real_data_meta": (real_bundle or {}).get("meta"),
        "sample_paths": discovery.get("sample_paths"),
        "epistemic_tier": "measured_application",
        "note": discovery.get("note"),
    }


def run_universe_scan(
    *,
    n_paths: int = 128,
    seed: int | None = 1,
    scope: str = "core",
) -> dict[str, Any]:
    gate = verify_fsot_gate(require_archive=False)
    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        store_paths=8,
        scope=scope,
        train_pathway_memory=True,
    )
    public = {k: v for k, v in mc.items() if not k.startswith("_")}
    return {
        "error": public.get("error"),
        "method": "fsot_universe_scan",
        "free_parameters": 0,
        "scope": public.get("scope"),
        "n_domains": public.get("n_domains"),
        "authority_gate": gate,
        "ensemble": public.get("ensemble"),
        "discovery_hints": public.get("discovery_hints"),
        "pathway_memory": public.get("pathway_memory"),
        "canonical_snapshot": public.get("canonical_snapshot"),
    }
