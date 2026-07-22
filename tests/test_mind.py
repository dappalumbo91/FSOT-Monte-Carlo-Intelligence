"""FSOT Monte Carlo conversational mind tests."""

from __future__ import annotations

from fsot_mc.mind import FSOTMind, ask, route_query_to_domains


def test_route_cosmology():
    d = route_query_to_domains("What about Hubble tension and cosmology?")
    assert "Cosmology" in d


def test_route_quantum():
    d = route_query_to_domains("quantum entanglement and observer effect")
    assert any("Quantum" in x for x in d)


def test_ask_returns_simulation_grounded_answer():
    r = ask("What is the vitality of biology versus cosmology?", n_paths=24)
    assert r.get("error") is None
    assert r["method"] == "fsot_monte_carlo_mind"
    assert r["free_parameters"] == 0
    assert "thinking" in r
    assert r["thinking"]["process"] == "multipath_observer_collapse_monte_carlo"
    assert len(r["thinking"]["steps"]) >= 4
    assert r["thinking"]["n_paths"] == 24
    assert isinstance(r["answer"], str) and len(r["answer"]) > 40
    assert "FSOT" in r["answer"] or "path" in r["answer"].lower() or "emergence" in r["answer"].lower()


def test_mind_session_history():
    mind = FSOTMind(n_paths=16, seed=1)
    a = mind.think("Tell me about quantum mechanics")
    b = mind.think("And biology?")
    assert a.get("error") is None and b.get("error") is None
    assert len(mind.history) == 2
    assert b["session"]["n_turns"] == 2
