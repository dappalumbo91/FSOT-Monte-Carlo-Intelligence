"""Tests for gap-fill refinements: formal promote, flip protocols, pred bench."""

from __future__ import annotations

from fsot_mc.formal_bridge import promote_from_audit, formal_status
from fsot_mc.flip_protocols import build_flip_protocol_pack, measure_flip_hotspots
from fsot_mc.pred_bench import init_bench_from_manifest, update_pred_status, bench_status_summary


def test_pred_bench_init():
    r = init_bench_from_manifest()
    assert r["ok"]
    assert r["n"] >= 10
    s = bench_status_summary()
    assert s["n"] >= 10


def test_pred_bench_update_roundtrip():
    # mark a PRED in_progress then back to open so we don't false-claim pass
    r = update_pred_status("PRED-001", status="in_progress", note="audit smoke")
    assert r.get("ok")
    assert r["entry"]["status"] == "in_progress"
    r2 = update_pred_status("PRED-001", status="open", note="reset after smoke")
    assert r2.get("ok")


def test_flip_hotspots_measured():
    hot = measure_flip_hotspots(n_paths=24, seed=1)
    assert isinstance(hot, list)
    # with 24 paths we may still see some flips
    pack = build_flip_protocol_pack(n_paths=24, seed=1, write=False)
    assert pack["n_hotspots"] == len(pack["cards"])
    if pack["cards"]:
        c = pack["cards"][0]
        assert "kill_criteria" in c and "pass_criteria" in c
        assert c["free_parameters"] == 0


def test_promote_from_audit_exports():
    # light audit path already exists; promote without re-running full if we pass stub
    stub = {
        "grade": "A",
        "overall_score": 0.9,
        "checks": [
            {
                "id": "TEST-UNIT",
                "title": "unit test lead",
                "ok": True,
                "score": 0.95,
                "severity": "info",
                "layer": "test",
                "finding": "smoke",
                "improvement": "none",
                "evidence": {},
            }
        ],
        "improvement_ledger": [],
    }
    r = promote_from_audit(stub, run_court=True)
    assert r["n_leads"] >= 1
    assert r["free_parameters"] == 0
    st = formal_status()
    assert "pending_obligations" in st
