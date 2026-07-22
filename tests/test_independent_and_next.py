"""Independence + language relay + polar student."""

from __future__ import annotations

from fsot_mc.language_relay import relay_discovery, relay_lead
from fsot_mc.paths import independence_status, pflt_vendor_dir
from fsot_mc.polar_student import train_polar_student
from fsot_mc.intelligence import run_intelligence


def test_workspace_independent():
    st = independence_status()
    assert st["independent"] is True
    assert st["checks"]["archive_bundle"]
    assert st["checks"]["pflt_vision"]
    assert st["checks"]["full_atlas"]
    assert st["checks"]["compute_authority"]
    # vendor path is under package, not Desktop
    assert "FSOT-Monte-Carlo-Intelligence" in str(pflt_vendor_dir())


def test_eyes_use_vendored_pflt():
    from fsot_mc.pflt_bridge import find_pflt_root, eyes_with_mc
    from fsot_mc.universe_mc import run_universe_monte_carlo

    root = find_pflt_root()
    assert root is not None
    assert root.name == "pflt"
    mc = run_universe_monte_carlo(n_paths=8, seed=1, scope="core", store_paths=2)
    eyes = eyes_with_mc(mc)
    assert eyes["ring"]["vision_backend"] in (
        "pflt_multilayer_vendored",
        "fsot_fallback_field",
    )


def test_language_relay():
    lead = {
        "id": "TEST-LEAD",
        "class": "physics_candidate",
        "title": "Quantum cosmos bridge",
        "score": 0.9,
        "epistemic_tier": "scaffold",
        "hypothesis": "Long-range bridge under observation.",
    }
    r = relay_lead(lead)
    assert "FSOT" in r["relay_text"]
    assert r["free_parameters"] == 0

    intel = run_intelligence(
        n_paths=12, seed=2, scope="core", with_eyes=False, with_language_relay=True
    )
    lang = intel.get("language_relay") or {}
    assert lang.get("n_relayed", 0) >= 1
    assert lang.get("universe_state")


def test_polar_student_train():
    r = train_polar_student(n_paths=40, seed=3, scope="core")
    assert r.get("ok") is True
    assert r["test_acc"] >= 0.0
    assert r["n_samples"] >= 8


def test_realities_local_snapshot():
    from fsot_mc.realities_client import poll_runtime

    poll = poll_runtime()
    assert poll.get("ok") is True
    assert poll.get("mode") == "local_snapshot"
