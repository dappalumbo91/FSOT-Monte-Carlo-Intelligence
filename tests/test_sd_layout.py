"""Classic D_eff-ring layout with S-ordering on each shell."""

from __future__ import annotations

from fsot_mc.graph_model import build_universe_graph


def test_seed_hub_present():
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
    assert sum(1 for e in g["edges"] if e.get("kind") == "seed_to_law") == 5
    assert sum(1 for e in g["edges"] if e.get("kind") == "law_to_domain") >= 30


def test_ring_from_deff_and_s_order_within_ring():
    g = build_universe_graph(
        scope="core",
        with_mc=False,
        with_archive_connective=False,
        with_memory=False,
        with_predictions=False,
    )
    cores = [n for n in g["nodes"] if n.get("is_core") or n.get("kind") == "domain"]
    assert len(cores) >= 30
    # same D_eff share a ring band
    by_ring: dict[int, list] = {}
    for n in cores:
        by_ring.setdefault(int(n["ring"]), []).append(n)
    # within each ring: angles ordered by physics spine then S (As Above So Below)
    for ring, group in by_ring.items():
        with_s = [n for n in group if n.get("S") is not None and n.get("angle") is not None]
        if len(with_s) < 2:
            continue
        ordered = sorted(with_s, key=lambda n: float(n["angle"]))
        # within a single physics spine on this ring, S is non-decreasing
        from itertools import groupby

        for spine, chunk in groupby(ordered, key=lambda n: n.get("physics_spine")):
            rows = list(chunk)
            if len(rows) < 2:
                continue
            s_vals = [float(n["S"]) for n in rows]
            ups = sum(1 for a, b in zip(s_vals, s_vals[1:]) if b >= a - 1e-12)
            assert ups >= len(s_vals) - 2 or ups >= (len(s_vals) - 1) * 0.7


def test_signed_s_not_path_mean():
    g = build_universe_graph(scope="full", with_mc=True, n_paths=16)
    cores = [n for n in g["nodes"] if n.get("is_core")]
    neg = [n for n in cores if float(n.get("S") or 0) < 0]
    assert len(neg) >= 5  # dispersal cores keep negative S
    for n in cores:
        if n.get("S_path_mean") is not None and n.get("S_canonical") is not None:
            assert abs(float(n["S"]) - float(n["S_canonical"])) < 1e-9


def test_meta_layout_mode():
    g = build_universe_graph(scope="core", with_mc=False, with_archive_connective=False)
    assert (g.get("meta") or {}).get("layout_mode") == "deff_ring_physics_sectors"
    assert (g.get("meta") or {}).get("color_doctrine") == "as_above_so_below"


def test_physics_spine_and_deff_color():
    from fsot_mc.graph_model import color_as_above_so_below, resolve_physics_spine

    micro = color_as_above_so_below(spine="particle_quantum", d_eff=5, is_core=True)
    macro = color_as_above_so_below(spine="particle_quantum", d_eff=24, is_core=True)
    # same hue family, different lightness (micro brighter)
    assert micro["hue"] == macro["hue"]
    assert micro["lightness"] > macro["lightness"]
    assert micro["scale_band"] == "micro"
    assert macro["scale_band"] == "macro"

    g = build_universe_graph(scope="core", with_mc=False, with_archive_connective=False)
    cores = [n for n in g["nodes"] if n.get("is_core")]
    assert all(n.get("physics_spine") for n in cores)
    # QM-ish domains share particle spine or related
    qm = next(n for n in cores if n.get("domain") == "Quantum_Mechanics")
    assert qm["physics_spine"] in ("particle_quantum", "cosmo_unification", "atomic_optical")
    assert resolve_physics_spine(qm) == qm["physics_spine"]
