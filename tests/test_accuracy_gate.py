"""Cross-domain accuracy / margin-of-error readings tests."""

from __future__ import annotations

from fsot_mc.accuracy_gate import (
    THRESHOLD_POOLED_MEDIAN_PCT,
    core_fold_recompute_accuracy,
    load_archive_margin_audit,
    load_contested_panel,
    run_accuracy_readings,
)


def test_margin_thresholds():
    assert THRESHOLD_POOLED_MEDIAN_PCT == 0.5


def test_archive_margin_audit_loads():
    m = load_archive_margin_audit()
    assert m.get("ok") is True
    assert m.get("green_gate_pass_count", 0) > 0
    assert m.get("all_green") is True or m.get("green_gate_fail_count") == 0


def test_contested_panel_within_green_gate():
    c = load_contested_panel()
    assert c.get("ok") is True
    assert c.get("n_observables", 0) >= 5
    assert c.get("fsot_pooled_median_error_pct") is not None
    assert float(c["fsot_pooled_median_error_pct"]) < 1.0
    # majority within 0.5%
    assert c.get("n_within_0_5pct", 0) >= c["n_observables"] // 2


def test_core_recompute_tight():
    core = core_fold_recompute_accuracy()
    assert core.get("ok") is True
    assert core.get("n_core", 0) >= 10
    assert float(core.get("max_rel_error_pct") or 1) < 0.01


def test_run_accuracy_readings():
    r = run_accuracy_readings(n_paths=16, seed=2, with_multipath=True, write=False)
    assert r.get("error") is None
    assert r["integrity_checks"]["authority_ok"] is True
    assert r["integrity_checks"]["core_recompute_ok"] is True
    assert r["headline"]["archive_domains_green"]
    assert "acceptable_margins" in r
    multi = r.get("multipath_exploratory") or {}
    assert multi.get("ok") is True
    assert multi.get("map_emergence_mean") is not None
