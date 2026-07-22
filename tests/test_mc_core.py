"""Core MC + pattern memory + FSOT authority tests."""

from __future__ import annotations

import numpy as np
import pandas as pd

from fsot_mc import (
    AUTHORITY_SHA256,
    PatternMemory,
    SOLIDIFY_ACC,
    collapse_probability,
    multi_horizon_mc,
    run_dynamic_fsot_monte_carlo,
    run_fsot_monte_carlo,
    run_intelligence,
    verify_fsot_gate,
    SEED_C,
    SEED_POOF,
)


def _df(n: int = 150, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0003, 0.01, size=n)
    close = 100.0 * np.cumprod(1.0 + r)
    return pd.DataFrame(
        {
            "time": pd.date_range("2021-01-01", periods=n, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e6, 2e6, size=n),
        }
    )


def test_authority_gate():
    g = verify_fsot_gate(require_archive=False)
    assert g["ok"] is True
    assert g["authority_sha256"] == AUTHORITY_SHA256
    assert g["float_engine"]["ok"] is True
    assert g["authority_bytes"]["local_matches"] is True


def test_collapse_bounded():
    p = collapse_probability(1.5, 1.5, 0.0, SEED_C)
    assert SEED_POOF <= p <= 1.0 - SEED_POOF


def test_flat_mc():
    mc = run_fsot_monte_carlo(_df(), horizon=8, n_paths=32, seed=1)
    assert mc.get("error") is None
    assert mc["free_parameters"] == 0
    assert 0.0 <= mc["ensemble"]["p_up"] <= 1.0


def test_dynamic_mc():
    mc = run_dynamic_fsot_monte_carlo(
        _df(n=220, seed=3), horizon=8, n_paths=32, symbol="T", persist=False, seed=2
    )
    assert mc.get("error") is None
    assert mc["dynamic"] is True
    assert mc["free_parameters"] == 0


def test_pattern_solidify():
    mem = PatternMemory(symbol="X")
    key = "D19|mu1|d1|f1|s0|q1|p0|a1|imid"
    for i in range(14):
        mem.observe(key, 1, 1, bar_index=i)
    assert mem.get(key).solidified is True
    assert mem.get(key).acc_phi >= SOLIDIFY_ACC * 0.9


def test_intelligence_api():
    out = run_intelligence(
        _df(n=250, seed=5),
        symbol="SYN",
        horizon=8,
        n_paths=32,
        include_bhs=False,
        include_multi_horizon=True,
    )
    assert out.get("error") is None
    assert out["free_parameters"] == 0
    assert out["authority_gate"]["ok"] is True
    assert out["primary_signal"] in ("LONG", "SHORT", "FLAT")


def test_multi_horizon():
    r = multi_horizon_mc(_df(n=240, seed=7), symbol="SYN", n_paths=32, horizons=(5, 8, 13))
    assert r.get("error") is None
    assert r["free_parameters"] == 0
    assert "horizons" in r
