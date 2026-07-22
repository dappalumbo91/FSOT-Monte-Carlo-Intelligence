#!/usr/bin/env python3
"""Smoke Buy/Hold/Sell layer on synthetic or history."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from fsot_mc import run_bhs_backtest


def synthetic(n: int = 500, seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0005, 0.015, size=n)
    close = 50.0 * np.cumprod(1.0 + r)
    return pd.DataFrame(
        {
            "time": pd.date_range("2019-01-01", periods=n, freq="D"),
            "open": close,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": rng.uniform(1e5, 2e6, size=n),
        }
    )


def load_history(symbol: str) -> pd.DataFrame:
    from fsot_mc.paths import ohlcv_csv

    p = ohlcv_csv(symbol)
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    df = df.rename(columns={c: str(c).lower() for c in df.columns}).reset_index()
    df = df.rename(columns={df.columns[0]: "time"})
    for c in ("open", "high", "low", "close", "volume"):
        if c not in df.columns:
            df[c] = df["close"] if c != "volume" else 0
    if len(df) > 2000:
        df = df.iloc[-2000:].copy()
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SYN")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--capital", type=float, default=10_000.0)
    args = ap.parse_args()

    df = load_history(args.symbol) if args.history else synthetic()
    sym = args.symbol.upper() if args.history else "SYN"
    r = run_bhs_backtest(df, capital=args.capital, symbol=sym)
    if r.get("error"):
        print("ERROR", r["error"])
        return
    print(f"{sym} BHS  free_params={r['free_parameters']}")
    print(f"  commit_acc={r.get('commit_directional_accuracy')}")
    print(f"  progress_70_80={r.get('progress_to_70_80')}")
    print(f"  pnl=${r['total_pnl']:+.2f}  ret={r['total_return']*100:+.2f}%")
    print(f"  trades={r['trades']}  hold%={r['pct_hold']*100:.1f}%  sharpe={r['sharpe']:+.2f}")


if __name__ == "__main__":
    main()
