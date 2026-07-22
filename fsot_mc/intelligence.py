"""
FSOT Monte Carlo Intelligence — universe discovery API (primary).

This project simulates the **universe** under Fluid Spacetime Omni-Theory:
  - 35 domain folds (quantum → cosmos)
  - multipath observer collapse
  - cross-scale bridges (As Above, So Below)
  - discovery of novel pathways and physics candidates
  - optional real-data alignment from the FSOT archive

Market / OHLCV modules remain under the package for historical extract only.
They are **not** the product.
"""

from __future__ import annotations

from typing import Any

from fsot_mc.authority_gate import verify_fsot_gate
from fsot_mc.discovery import run_discovery
from fsot_mc.real_data import build_real_data_bundle
from fsot_mc.universe_atlas import atlas_meta, domains_by_cluster, snapshot_universe
from fsot_mc.universe_mc import run_universe_monte_carlo


def run_intelligence(
    *,
    n_paths: int = 256,
    seed: int | None = 0,
    use_real_data: bool = True,
    store_paths: int = 24,
) -> dict[str, Any]:
    """
    Primary intelligence entrypoint — universe discovery under FSOT law.
    """
    gate = verify_fsot_gate(require_archive=False)
    if not gate["ok"]:
        return {
            "error": "fsot_authority_gate_failed",
            "authority_gate": gate,
            "free_parameters": 0,
        }

    real_bundle = build_real_data_bundle(use_archive=use_real_data) if use_real_data else None
    anchors = (real_bundle or {}).get("anchors")

    discovery = run_discovery(
        n_paths=n_paths,
        seed=seed,
        real_data=anchors,
        store_paths=store_paths,
    )
    if discovery.get("error"):
        return discovery

    canonical = snapshot_universe()
    return {
        "error": None,
        "method": "fsot_universe_monte_carlo_intelligence",
        "free_parameters": 0,
        "purpose": "Simulate the universe under FSOT; discover pathways and physics — not markets",
        "authority_gate": gate,
        "atlas": atlas_meta(),
        "clusters": {k: len(v) for k, v in domains_by_cluster().items()},
        "canonical_universe": {
            "emergence_fraction": canonical["emergence_fraction"],
            "mean_S": canonical["mean_S"],
            "n_emergence": canonical["n_emergence"],
            "n_dispersal": canonical["n_dispersal"],
        },
        "discovery": {
            "top_ledger": discovery["top_ledger"],
            "candidates": discovery["candidates"],
            "ensemble": discovery["monte_carlo"]["ensemble"],
        },
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
) -> dict[str, Any]:
    """Lighter scan: MC ensemble only (no full discovery classification)."""
    gate = verify_fsot_gate(require_archive=False)
    mc = run_universe_monte_carlo(n_paths=n_paths, seed=seed, store_paths=8)
    return {
        "error": mc.get("error"),
        "method": "fsot_universe_scan",
        "free_parameters": 0,
        "authority_gate": gate,
        "ensemble": mc.get("ensemble"),
        "discovery_hints": mc.get("discovery_hints"),
        "canonical_snapshot": mc.get("canonical_snapshot"),
    }


# ---------------------------------------------------------------------------
# Legacy market API (deprecated — not the project direction)
# ---------------------------------------------------------------------------

def run_market_intelligence_legacy(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    DEPRECATED: former OHLCV / market intelligence.
    Kept for reference only. Prefer run_intelligence() universe discovery.
    """
    from fsot_mc.monte_carlo import run_dynamic_fsot_monte_carlo  # local import

    # Accept df as first positional for old signature compatibility
    if args:
        df = args[0]
        symbol = kwargs.get("symbol", "")
        return {
            "error": None,
            "deprecated": True,
            "method": "legacy_market_mc",
            "note": "Market MC is legacy extract — project is universe discovery.",
            "result": run_dynamic_fsot_monte_carlo(df, persist=False, **{k: v for k, v in kwargs.items() if k != "include_bhs"}),
            "free_parameters": 0,
        }
    return {
        "error": "legacy_requires_ohlcv_dataframe",
        "deprecated": True,
        "free_parameters": 0,
    }
