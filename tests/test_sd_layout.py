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
    # within each ring with 2+ nodes that have S, angles follow S order
    for ring, group in by_ring.items():
        with_s = [n for n in group if n.get("S") is not None and n.get("angle") is not None]
        if len(with_s) < 2:
            continue
        ordered = sorted(with_s, key=lambda n: float(n["angle"]))
        s_vals = [float(n["S"]) for n in ordered]
        # non-decreasing S as we walk the shell angles (allowing wrap at cut)
        # check majority of consecutive pairs increase or stay
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
    assert (g.get("meta") or {}).get("layout_mode") == "deff_ring_s_ordered"
