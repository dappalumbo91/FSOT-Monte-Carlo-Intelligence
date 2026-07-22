"""Layers 2–4: full atlas, pathway memory, contested physics."""

from __future__ import annotations

from fsot_mc.atlas_build import build_full_atlas
from fsot_mc.contested_physics import run_contested_physics_pack
from fsot_mc.pathway_memory import PathwayMemory, pathway_signature, pathway_quality
from fsot_mc.universe_atlas import extension_names, reload_atlas, domain_names
from fsot_mc.universe_mc import run_universe_monte_carlo
from fsot_mc.discovery import run_discovery


def test_build_full_atlas():
    a = build_full_atlas(write=True)
    assert a["n_core"] == 35
    assert a["n_extension"] >= 360
    assert a["n_total"] == len(a["domains"])
    assert a["n_total"] == a["n_core"] + a["n_extension"]
    reload_atlas()
    assert len(domain_names()) == a["n_total"]
    assert len(extension_names()) == a["n_extension"]


def test_core_mc_with_pathway_memory():
    mc = run_universe_monte_carlo(
        n_paths=24, seed=1, scope="core", store_paths=8, train_pathway_memory=True
    )
    assert mc["error"] is None
    assert mc["n_domains"] == 35
    assert mc["pathway_memory"]["n_updates"] == 24
    # signatures exist
    for s in mc["sample_paths"]:
        assert s.get("pathway_key")


def test_pathway_memory_unit():
    mem = PathwayMemory()
    path = {
        "emergence_fraction": 0.72,
        "collapse_true_fraction": 0.55,
        "ladder_agree_fraction": 0.8,
        "n_regime_flips": 2,
        "regime_flips": ["Cosmology"],
        "mean_S": 0.3,
        "mean_bridge_strength": 0.2,
        "contested": {"S_cosm": -0.5},
        "long_range_bridges": [
            {"a": "Quantum_Mechanics", "b": "Cosmology", "agree": -1}
        ],
        "global_phase": 0.1,
    }
    key = pathway_signature(path)
    assert "|" in key
    assert pathway_quality(path) > 0.3
    for i in range(14):
        mem.observe_path(path, path_index=i)
    assert mem.summary()["n_updates"] == 14


def test_contested_pack():
    mc = run_universe_monte_carlo(n_paths=16, seed=2, scope="core", store_paths=4)
    pack = run_contested_physics_pack(mc)
    assert pack["n_probes"] >= 3
    assert pack["probes"][0]["class"] == "contested_physics"


def test_discovery_core():
    d = run_discovery(n_paths=20, seed=3, scope="core", store_paths=6)
    assert d["error"] is None
    assert "pathway_memory" in d
    assert "contested_physics" in d
    assert len(d["top_ledger"]) >= 1
