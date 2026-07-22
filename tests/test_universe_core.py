"""Universe Monte Carlo intelligence tests (primary product)."""

from __future__ import annotations

from fsot_mc import (
    AUTHORITY_SHA256,
    domain_names,
    evaluate_domain,
    run_discovery,
    run_intelligence,
    run_universe_monte_carlo,
    snapshot_universe,
    verify_fsot_gate,
)


def test_authority_gate():
    g = verify_fsot_gate(require_archive=False)
    assert g["ok"] is True
    assert g["authority_sha256"] == AUTHORITY_SHA256


def test_atlas_35():
    names = domain_names()
    assert len(names) == 35
    assert "Cosmology" in names
    assert "Quantum_Mechanics" in names
    qm = evaluate_domain("Quantum_Mechanics")
    cos = evaluate_domain("Cosmology")
    assert qm["S"] > 0  # emergence
    assert cos["S"] < 0  # dispersal
    assert qm["regime"] == "emergence"
    assert cos["regime"] == "dispersal"


def test_snapshot():
    snap = snapshot_universe()
    assert snap["n_domains"] == 35
    assert 0.0 < snap["emergence_fraction"] < 1.0
    assert snap["free_parameters"] == 0


def test_universe_mc():
    mc = run_universe_monte_carlo(n_paths=32, seed=1, store_paths=4)
    assert mc.get("error") is None
    assert mc["free_parameters"] == 0
    assert mc["n_paths"] == 32
    assert "domain_ensemble" in mc
    assert "Cosmology" in mc["domain_ensemble"]
    assert mc["ensemble"]["emergence_fraction"]["mean"] > 0


def test_discovery():
    d = run_discovery(n_paths=48, seed=2, store_paths=8)
    assert d.get("error") is None
    assert d["free_parameters"] == 0
    assert "top_ledger" in d
    assert "candidates" in d


def test_intelligence_universe():
    out = run_intelligence(n_paths=32, seed=3, use_real_data=True, store_paths=4)
    assert out.get("error") is None
    assert out["method"] == "fsot_universe_monte_carlo_intelligence"
    assert "market" not in out["purpose"].lower() or "not market" in out["purpose"].lower()
    assert out["authority_gate"]["ok"] is True
    assert len(out["discovery"]["top_ledger"]) >= 1
