"""FSOT Monte Carlo conversational mind tests."""

from __future__ import annotations

from fsot_mc.archive_predictions import load_preregistered_predictions, match_predictions, predictions_summary
from fsot_mc.mind import FSOTMind, ask, route_query_to_domains


def test_route_cosmology():
    d = route_query_to_domains("What about Hubble tension and cosmology?")
    assert "Cosmology" in d


def test_route_quantum():
    d = route_query_to_domains("quantum entanglement and observer effect")
    assert any("Quantum" in x for x in d)


def test_ask_returns_simulation_grounded_answer():
    r = ask("What is the vitality of biology versus cosmology?", n_paths=24, with_chew=False)
    assert r.get("error") is None
    assert r["method"] == "fsot_monte_carlo_mind"
    assert r["free_parameters"] == 0
    assert "thinking" in r
    assert r["thinking"]["process"] == "multipath_observer_collapse_monte_carlo"
    assert len(r["thinking"]["steps"]) >= 4
    assert r["thinking"]["n_paths"] == 24
    assert isinstance(r["answer"], str) and len(r["answer"]) > 80
    assert "FSOT" in r["answer"] or "emergence" in r["answer"].lower()
    # must define emergence fraction when discussing vitality
    assert "emergence" in r["answer"].lower()
    # science-grade ToE framing
    assert "free_parameters" in r["answer"].lower() or "D1D38A" in r["answer"] or "seed" in r["answer"].lower()


def test_emergence_percent_explained():
    r = ask(
        "What does the multipath emergence percentage mean for biology?",
        n_paths=20,
        with_chew=False,
    )
    ans = r["answer"].lower()
    assert "not" in ans and ("probability" in ans or "bayesian" in ans or "p(biology" in ans)
    assert "s>0" in ans or "s > 0" in ans or "vitality" in ans
    assert r["thinking"].get("emergence_fraction_definition")
    # clarify map % vs biology S
    assert "map" in ans or "share of folds" in ans or "not" in ans


def test_compare_gr():
    r = ask("Compare FSOT to general relativity", n_paths=20, with_chew=False)
    assert "relativity" in r["answer"].lower() or "einstein" in r["answer"].lower() or "gr" in r["answer"].lower()
    assert "Cosmology" in r["thinking"]["routed_domains"] or "Quantum_Gravity" in r["thinking"]["routed_domains"]
    assert "architecture" in r["answer"].lower() or "fluid" in r["answer"].lower()


def test_mind_session_history_and_reuse():
    mind = FSOTMind(n_paths=16, seed=1)
    a = mind.think("Tell me about quantum mechanics", with_chew=False)
    b = mind.think("And how does that relate to cosmology?", with_chew=False)
    assert a.get("error") is None and b.get("error") is None
    assert len(mind.history) == 2
    assert b["session"]["n_turns"] == 2
    # second turn should often reuse when overlapping
    assert "session_reused_prior_mc" in b["thinking"]


def test_archive_predictions_load():
    preds = load_preregistered_predictions()
    assert len(preds) >= 10
    summary = predictions_summary()
    assert summary["n_predictions"] >= 10
    fuel = match_predictions("fuel thermochemistry hydrogen algae hemp", limit=5)
    assert any("fuel" in str(p.get("name") or "").lower() or "fuel" in str(p.get("domain") or "").lower() for p in fuel)


def test_fuel_engineering_in_mind():
    r = ask(
        "What FSOT-designed fuels and engineering predictions should we experiment on?",
        n_paths=16,
        with_chew=False,
    )
    assert r.get("error") is None
    ans = r["answer"].lower()
    assert "fuel" in ans or "engineering" in ans or "preregistered" in ans
    eng = r["thinking"].get("engineering") or []
    assert len(eng) >= 1
    assert any(
        "fuel" in str(e.get("name") or "").lower()
        or "PRED" in str(e.get("id") or "")
        or e.get("class") in ("preregistered_prediction", "engineering_inventory")
        for e in eng
    )


def test_bio_emergence_paradigm_dual_frame():
    from fsot_mc.bio_emergence import analyze_biological_emergence
    from fsot_mc.universe_mc import run_universe_monte_carlo

    mc = run_universe_monte_carlo(n_paths=24, seed=3, store_paths=4)
    analysis = analyze_biological_emergence(mc, query="biology emergence complexity")
    assert analysis.get("error") is None
    hyp = analysis["hypothesis"]
    assert hyp["id"] == "BIO-EMERGENCE-MAP-WINDOW"
    assert hyp["map_emergence_mean"] is not None
    assert hyp["biology_S"] is not None and float(hyp["biology_S"]) > 0
    assert hyp["biology_complexity_proxy"] is not None
    assert hyp["biology_energy_proxy"] is not None
    assert len(analysis["life_corridor"]) >= 5
    # mind surfaces dual frame
    r = ask(
        "Is the 69% the emergence probability for biological complexity and energy?",
        n_paths=20,
        with_chew=False,
    )
    ans = r["answer"].lower()
    assert "co-emergence" in ans or "occupancy" in ans or "paradigm" in ans
    assert "complexity" in ans or "energy" in ans
    assert r["thinking"].get("biological_emergence", {}).get("hypothesis")
