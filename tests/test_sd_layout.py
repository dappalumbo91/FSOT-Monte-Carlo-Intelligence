"""S–D_eff polar layout: geometry must track signed S and D_eff."""

from __future__ import annotations

from fsot_mc.graph_model import build_universe_graph, layout_diagnostics, s_to_angle, deff_to_radius


def test_s_to_angle_hemispheres():
    # emergence (S>0) → smaller |angle from east| than dispersal
    a_pos = s_to_angle(1.0)
    a_neg = s_to_angle(-1.0)
    a_zero = s_to_angle(0.0)
    assert abs(a_pos) < 0.5  # near east (0)
    assert abs(a_neg - 3.14159) < 0.5 or abs(a_neg + 3.14159) < 0.5  # near west (π)
    assert 1.2 < a_zero < 1.9  # near north (π/2)


def test_deff_radius_monotonic():
    assert deff_to_radius(5) < deff_to_radius(15) < deff_to_radius(25)


def test_core_layout_organization():
    g = build_universe_graph(
        scope="core",
        with_mc=False,
        with_archive_connective=False,
        with_memory=False,
        with_predictions=False,
    )
    d = layout_diagnostics(g["nodes"])
    assert d["n_dispersal_S_lt_0"] >= 5
    assert d["n_emergence_S_gt_0"] >= 15
    # hemispheric rank layout: strong S→east and D→radius
    assert d["order_score_S_vs_east_x"] >= 0.85
    assert d["order_score_D_vs_radius"] >= 0.99
    by = {r["domain"]: r for r in d["core_table"]}
    # dispersal west (x<0), emergence east (x>0)
    assert by["Fluid_Dynamics"]["x_east"] < 0
    assert by["Particle_Physics"]["x_east"] > 0
    assert by["Fluid_Dynamics"]["x_east"] < by["Particle_Physics"]["x_east"]
    assert by["Cosmology"]["layout_r"] > by["Particle_Physics"]["layout_r"]


def test_seed_hub_connected():
    g = build_universe_graph(
        scope="core",
        with_mc=False,
        with_archive_connective=False,
        with_memory=False,
        with_predictions=False,
    )
    seeds = [n for n in g["nodes"] if n.get("kind") == "seed"]
    law = [n for n in g["nodes"] if n.get("kind") == "law"]
    assert len(seeds) == 5
    assert len(law) == 1
    assert float(law[0].get("layout_r") or 0) == 0.0
    for s in seeds:
        assert float(s.get("layout_r") or 0) > 0
        # seeds inside hub, cores outside
        assert float(s["layout_r"]) < 80
    cores = [n for n in g["nodes"] if n.get("is_core")]
    min_core_r = min(float(n["layout_r"]) for n in cores)
    max_seed_r = max(float(n["layout_r"]) for n in seeds)
    assert min_core_r > max_seed_r + 40  # clear gap so spokes read
    kinds = {e.get("kind") for e in g["edges"]}
    assert "seed_to_law" in kinds
    assert "law_to_domain" in kinds
    seed_edges = [e for e in g["edges"] if e.get("kind") == "seed_to_law"]
    assert len(seed_edges) == 5


def test_full_layout_keeps_signed_s():
    g = build_universe_graph(scope="full", with_mc=True, n_paths=16)
    cores = [n for n in g["nodes"] if n.get("is_core")]
    neg = [n for n in cores if float(n.get("S") or 0) < 0]
    pos = [n for n in cores if float(n.get("S") or 0) > 0]
    assert len(neg) >= 5
    assert len(pos) >= 15
    for n in cores:
        if n.get("S_path_mean") is not None and n.get("S_canonical") is not None:
            assert abs(float(n["S"]) - float(n["S_canonical"])) < 1e-9
    d = g["meta"]["layout_diagnostics"]
    assert d["order_score_D_vs_radius"] >= 0.9
    assert d["order_score_S_vs_east_x"] >= 0.85
    # seeds still present in full graph
    assert sum(1 for n in g["nodes"] if n.get("kind") == "seed") == 5
