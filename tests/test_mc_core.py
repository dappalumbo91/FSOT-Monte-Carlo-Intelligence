"""Legacy market modules still importable (not product tests)."""

from __future__ import annotations

import numpy as np
import pandas as pd

# Keep a thin smoke that legacy extract does not crash — product tests in test_universe_core.py


def test_legacy_import_smoke():
    from fsot_mc.monte_carlo import run_fsot_monte_carlo
    from fsot_mc.pattern_memory import PatternMemory

    rng = np.random.default_rng(0)
    r = rng.normal(0.0003, 0.01, size=120)
    close = 100.0 * np.cumprod(1.0 + r)
    df = pd.DataFrame(
        {
            "time": pd.date_range("2021-01-01", periods=120, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e6, 2e6, size=120),
        }
    )
    mc = run_fsot_monte_carlo(df, horizon=5, n_paths=16, seed=1)
    assert mc.get("error") is None
    assert PatternMemory is not None
