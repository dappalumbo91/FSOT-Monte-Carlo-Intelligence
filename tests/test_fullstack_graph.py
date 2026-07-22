"""Full-stack graph + protocols + solidify smoke tests."""

from __future__ import annotations

from fsot_mc.experiment_protocols import get_protocol, list_protocol_cards
from fsot_mc.graph_model import build_universe_graph
from fsot_mc.server import FRONTEND_DIR, handle_api


def test_graph_has_seeds_and_domains():
    g = build_universe_graph(
        n_paths=12,
        seed=1,
        scope="core",
        with_mc=True,
        with_memory=False,
        with_predictions=True,
        with_archive_connective=False,
    )
    assert g.get("error") is None
    assert g["n_nodes"] > 20
    assert g["n_edges"] > 20
    kinds = {n["kind"] for n in g["nodes"]}
    assert "seed" in kinds
    assert "law" in kinds
    assert "domain" in kinds
    assert any(e["kind"] == "seed_to_law" for e in g["edges"])


def test_full_archive_connective_graph():
    from fsot_mc.archive_connective import get_connective_tissue

    tissue = get_connective_tissue(force_rebuild=True)
    assert tissue.get("n_nodes", 0) >= 100
    assert tissue.get("n_edges", 0) >= 50
    assert tissue.get("n_extension", 0) >= 50 or tissue.get("n_core", 0) >= 30

    g = build_universe_graph(
        n_paths=8,
        seed=0,
        scope="full",
        with_mc=False,
        with_memory=False,
        with_predictions=False,
        with_archive_connective=True,
    )
    assert g["n_nodes"] >= 100
    kinds = {n["kind"] for n in g["nodes"]}
    assert "seed" in kinds and "law" in kinds
    # should include archive route or coupling edges
    edge_kinds = {e.get("kind") for e in g["edges"]}
    assert any(
        k and ("route" in k or "coupling" in k or "problem" in k or k == "routes_to_core")
        for k in edge_kinds
    )
    ac = (g.get("meta") or {}).get("archive_connective") or {}
    assert ac.get("coupling_raw_edge_count") is None or ac.get("coupling_raw_edge_count") >= 1000 or ac.get("n_archive_edges", 0) >= 50


def test_protocols():
    r = list_protocol_cards(limit=5)
    assert r["ok"] and r["n"] >= 1
    card = r["cards"][0]
    assert "kill_criteria" in card and "pass_criteria" in card
    p = get_protocol("PRED-001")
    assert p is not None
    assert p["id"] == "PRED-001"


def test_api_health_and_graph():
    code, body, ct = handle_api("GET", "/api/health", {}, b"")
    assert code == 200 and "json" in ct
    import json

    h = json.loads(body)
    assert h.get("ok") is True
    assert h.get("free_parameters") == 0

    code, body, _ = handle_api("GET", "/api/graph", {"n_paths": ["8"], "seed": ["0"]}, b"")
    assert code == 200
    g = json.loads(body)
    assert g.get("n_nodes", 0) > 10


def test_frontend_exists():
    assert (FRONTEND_DIR / "index.html").is_file()
    assert (FRONTEND_DIR / "app.js").is_file()
    assert (FRONTEND_DIR / "styles.css").is_file()
