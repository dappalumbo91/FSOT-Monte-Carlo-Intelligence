"""FSOT adaptive memory (STM / LTM) tests."""

from __future__ import annotations

from fsot_mc.adaptive_memory import AdaptiveMemory, HIT_THRESHOLD, SOLIDIFY_ACC, score_observation_quality
from fsot_mc.mind import FSOTMind


def test_score_quality_bounds():
    q = score_observation_quality(text="short", domains=["Biology"], mc=None)
    assert 0.0 <= q <= 1.0


def test_stm_and_ltm_observe_recall(tmp_path, monkeypatch):
    # isolate LTM path under tmp
    from fsot_mc import adaptive_memory as am

    monkeypatch.setattr(am, "memory_dir", lambda: tmp_path)
    mem = AdaptiveMemory(persist=True)
    r = mem.observe_text(
        "FSOT designed fuel thermochemistry PRED-034 is priority experiment",
        source="test",
        domains=["Chemistry", "Biology"],
        force_hit=True,
    )
    assert r["ok"]
    assert r["hit"] == 1.0
    hits = mem.recall("fuel PRED-034 experiment", limit=3)
    assert len(hits) >= 1
    assert any("fuel" in (h.get("text") or "").lower() or "PRED" in (h.get("text") or "") for h in hits)
    s = mem.summary()
    assert s["ltm_size"] >= 1
    assert s["stm_size"] >= 1
    assert s["free_parameters"] == 0
    assert SOLIDIFY_ACC > 0.5
    assert HIT_THRESHOLD > 0.5


def test_mind_trains_adaptive_memory(tmp_path, monkeypatch):
    from fsot_mc import adaptive_memory as am

    monkeypatch.setattr(am, "memory_dir", lambda: tmp_path)
    mind = FSOTMind(n_paths=12, seed=5)
    mind.adaptive = am.AdaptiveMemory(persist=True)
    r = mind.think(
        "Remember: multipath emergence is map co-emergence not Bayesian life probability",
        with_chew=False,
    )
    assert r.get("error") is None
    assert "adaptive_memory" in r["thinking"]
    assert r["session"]["adaptive_memory"]["ltm_size"] >= 1
