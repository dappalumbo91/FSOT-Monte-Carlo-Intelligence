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
    # strong organization under pure S–D layout
    assert d["order_score_S_vs_east_x"] >= 0.85
    assert d["order_score_D_vs_radius"] >= 0.99
    # Fluid Dynamics (dispersal) should sit west of Particle Physics (emergence)
    by = {r["domain"]: r for r in d["core_table"]}
    assert by["Fluid_Dynamics"]["x_east"] < by["Particle_Physics"]["x_east"]
    # Cosmology high-D outer vs Particle_Physics low-D inner
    assert by["Cosmology"]["layout_r"] > by["Particle_Physics"]["layout_r"]


def test_full_layout_keeps_signed_s():
    g = build_universe_graph(scope="full", with_mc=True, n_paths=16)
    cores = [n for n in g["nodes"] if n.get("is_core")]
    neg = [n for n in cores if float(n.get("S") or 0) < 0]
    pos = [n for n in cores if float(n.get("S") or 0) > 0]
    assert len(neg) >= 5
    assert len(pos) >= 15
    # path-mean may differ but must not overwrite canonical S
    for n in cores:
        if n.get("S_path_mean") is not None and n.get("S_canonical") is not None:
            # S field is canonical for layout
            assert abs(float(n["S"]) - float(n["S_canonical"])) < 1e-9
    d = g["meta"]["layout_diagnostics"]
    assert d["order_score_D_vs_radius"] >= 0.9
    assert d["order_score_S_vs_east_x"] >= 0.75
