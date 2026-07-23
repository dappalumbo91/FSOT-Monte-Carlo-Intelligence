"""Improvement cycle + PRED in-silico helpers (no GPU train)."""

from __future__ import annotations

from fsot_mc.pred_bench import (
    PRIORITY_PRED_IDS,
    _in_silico_discriminant,
    load_bench_ledger,
    run_in_silico_self_checks,
)


def test_priority_ids_exist_in_ledger():
    ledger = load_bench_ledger()
    entries = ledger.get("entries") or {}
    for pid in PRIORITY_PRED_IDS:
        assert pid in entries, pid


def test_h0_between_anchors_self_check():
    e = {
        "fsot_predicted": 70.75,
        "sota_baseline": 67.36,
        "discriminant": "strictly_between_planck_and_sh0es",
    }
    r = _in_silico_discriminant(e)
    assert r["ok"] is True
    assert r["tier"] == "STRUCTURE"


def test_in_silico_batch_runs():
    r = run_in_silico_self_checks(write=True)
    assert r.get("ok") is True
    assert r.get("free_parameters") == 0
    assert (r.get("n_ok") or 0) + (r.get("n_fail") or 0) + (r.get("n_skip") or 0) > 0
