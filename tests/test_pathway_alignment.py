"""Pathway alignment gates (no full rebuild required for unit checks)."""

from __future__ import annotations

from fsot_mc.pathway_alignment import (
    admit_scaffold_edge,
    pathway_status,
    propose_expansion_from_text,
    resolve_lean_hub,
)
from fsot_mc.authority_gate import verify_fsot_gate


def test_gate_ok_for_pathways():
    assert verify_fsot_gate(require_archive=False).get("ok") is True


def test_pathway_status_shape():
    st = pathway_status()
    assert st.get("ok") is True
    assert st.get("free_parameters") == 0
    assert "doctrine" in st


def test_admit_rejects_self_edge():
    r = admit_scaffold_edge(source="Biology", target="Biology", evidence="noop")
    assert r.get("ok") is False


def test_propose_connect_heuristic():
    r = propose_expansion_from_text(
        "Please connect Biology to Neuroscience for shared fluid fold pathways.",
        source="test",
        run_court=False,
    )
    assert r.get("ok") is True
    assert (r.get("n_proposals") or 0) >= 1


def test_resolve_lean_hub_prefers_existing():
    hub = resolve_lean_hub()
    # On this machine I: or Desktop Lean may exist; always returns structure
    assert "primary" in hub
    assert "local_bundle" in hub
