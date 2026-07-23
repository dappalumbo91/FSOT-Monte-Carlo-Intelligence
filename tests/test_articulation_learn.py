"""Gated articulation learning — no GPU train required for unit tests."""

from __future__ import annotations

from fsot_mc.articulation_learn import (
    IDENTITY_SFT,
    admit_sample,
    gate_for_training,
    harvest_identity_seeds,
    status,
)
from fsot_mc.authority_gate import verify_fsot_gate


def test_gate_for_training_matches_authority():
    g = gate_for_training()
    pin = verify_fsot_gate(require_archive=False)
    assert g["ok"] == pin["ok"]
    assert g["free_parameters"] == 0


def test_identity_seeds_defined():
    assert len(IDENTITY_SFT) >= 5
    for s in IDENTITY_SFT:
        low = s["assistant"].lower()
        assert "fluid spacetime" in low
        assert any(k in s["assistant"] or k in low for k in ("FSOT", "D1D38A", "free_parameters", "pin", "vitality", "lean"))


def test_admit_rejects_wrong_acronym(tmp_path, monkeypatch):
    # use real gate; only test forbidden claim filter
    r = admit_sample(
        "What is FSOT?",
        "FSOT means Feature Selection Optimization Toolkit and we invent free parameters.",
        source="manual",
    )
    assert r.get("ok") is False
    assert r.get("error") in ("forbidden_claim", "missing_fluid_spacetime_identity")


def test_admit_and_status_identity():
    r = harvest_identity_seeds()
    assert r.get("ok") is True
    st = status()
    assert st["free_parameters"] == 0
    assert st["n_samples"] >= 1
    assert "trains" in (st.get("doctrine") or {})
