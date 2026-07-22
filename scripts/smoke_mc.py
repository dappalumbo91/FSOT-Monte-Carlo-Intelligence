#!/usr/bin/env python3
"""Smoke FSOT Monte Carlo intelligence (synthetic or history CSV)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from fsot_mc import (
    SEED_C,
    SEED_POOF,
    SOLIDIFY_ACC,
    run_dynamic_fsot_monte_carlo,
    run_fsot_monte_carlo,
    train_pattern_memory,
)


def synthetic(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0004, 0.012, size=n)
    close = 100.0 * np.cumprod(1.0 + r)
    return pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e6, 2e6, size=n),
        }
    )


def load_history(symbol: str) -> pd.DataFrame:
    from fsot_mc.paths import ohlcv_csv

    p = ohlcv_csv(symbol)
    if not p.exists():
        raise FileNotFoundError(p)
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df = df.rename(columns={c: str(c).lower() for c in df.columns}).reset_index()
    df = df.rename(columns={df.columns[0]: "time"})
    for c in ("open", "high", "low", "close", "volume"):
        if c not in df.columns:
            df[c] = df["close"] if c != "volume" else 0
    if len(df) > 1200:
        df = df.iloc[-1200:].copy()
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SYN")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--n-paths", type=int, default=128)
    args = ap.parse_args()

    print(f"C={SEED_C:.4f}  Poof={SEED_POOF:.4f}  SOLIDIFY_ACC={SOLIDIFY_ACC:.4f}")
    print(f"free_parameters=0\n")

    if args.history:
        df = load_history(args.symbol)
        sym = args.symbol.upper()
    else:
        df = synthetic()
        sym = "SYN"

    print(f"bars={len(df)}  symbol={sym}")
    mem, diag = train_pattern_memory(df, window=21, symbol=sym, step=1)
    print(
        f"train patterns={diag['memory']['n_patterns']} solid={diag['memory']['n_solidified']} "
        f"raw_acc={diag.get('raw_directional_accuracy')}"
    )
    if diag.get("refinement_lift") is not None:
        print(
            f"  refine early={diag['anchored_early']:.3f} late={diag['anchored_late']:.3f} "
            f"lift={diag['refinement_lift']:+.3f}"
        )

    flat = run_fsot_monte_carlo(
        df, horizon=13, n_paths=args.n_paths, symbol=sym, seed=1, dynamic=False
    )
    dyn = run_dynamic_fsot_monte_carlo(
        df,
        horizon=13,
        n_paths=args.n_paths,
        symbol=sym,
        seed=1,
        persist=False,
        max_train_bars=800,
    )
    print(
        f"flat MC: signal={flat['signal']} p_up_obs={flat['ensemble']['p_up_observed_branch']:.3f}"
    )
    print(
        f"dyn  MC: signal={dyn['signal']} conf={dyn['confidence']:.3f} "
        f"p_up_obs={dyn['ensemble']['p_up_observed_branch']:.3f} "
        f"solid_bias={dyn.get('pattern', {}).get('bias', {}).get('solidified')}"
    )
    print(f"method={dyn['method']}")


if __name__ == "__main__":
    main()
