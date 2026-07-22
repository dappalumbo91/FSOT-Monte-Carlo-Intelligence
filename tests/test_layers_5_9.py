"""Layers 5–9: eyes, formal, realities, apis, publish checks."""

from __future__ import annotations

from fsot_mc.api_adapters import run_api_bundle, seed_demo_cache
from fsot_mc.formal_bridge import (
    export_lead_obligation,
    formal_status,
    promote_from_intelligence,
    run_soft_court,
)
from fsot_mc.intelligence import run_intelligence
from fsot_mc.pflt_bridge import eyes_with_mc
from fsot_mc.pi_ring import PiRing
from fsot_mc.realities_client import poll_runtime
from fsot_mc.universe_mc import run_universe_monte_carlo


def test_pi_ring_and_eyes():
    ring = PiRing()
    ring.write_mc_state(d_eff=12, phase=0.5, S=0.4, mass=1.0)
    ring.write_text_as_ring("test")
    r = ring.readout()
    assert r["interior_area_pi_r2"] > 1.0
    mc = run_universe_monte_carlo(n_paths=8, seed=1, scope="core", store_paths=2)
    eyes = eyes_with_mc(mc, text="FSOT")
    assert eyes["ring"]["vision_backend"] in (
        "pflt_multilayer_vendored",
        "pflt_multilayer",
        "fsot_fallback_field",
    )
    assert eyes["n_domains_projected"] == 35


def test_formal_soft_court():
    st = formal_status()
    assert st["free_parameters"] == 0
    lead = {"id": "TEST-UNIT", "score": 0.95, "epistemic_tier": "measured_application"}
    p = export_lead_obligation(lead)
    assert p.is_file()
    court = run_soft_court(promote=True)
    assert court["n_pending"] >= 1


def test_formal_from_intel():
    intel = run_intelligence(
        n_paths=12, seed=2, scope="core", with_eyes=False, with_formal_promote=False
    )
    out = promote_from_intelligence(intel, top_n=5)
    assert out["exported"]["exported"] >= 1
    assert "court" in out


def test_realities_poll():
    # May or may not have live kernel — must not crash
    poll = poll_runtime()
    assert "ok" in poll
    assert poll["free_parameters"] == 0


def test_api_offline_demo():
    seed_demo_cache()
    r = run_api_bundle()
    assert r["n_ok"] >= 1
    assert "anchors" in r


def test_intel_stack_flags():
    out = run_intelligence(
        n_paths=10,
        seed=3,
        scope="core",
        with_eyes=True,
        with_formal_promote=True,
        with_apis=True,
        with_realities=True,
    )
    assert out.get("error") is None
    assert out.get("eyes") is not None
    assert out.get("formal") is not None
    assert out.get("apis") is not None
