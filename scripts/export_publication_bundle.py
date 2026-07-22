#!/usr/bin/env python3
"""Export JSON/CSV intelligence artifacts for Hugging Face + Kaggle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd


def load_df(symbol: str, history: bool) -> pd.DataFrame:
    if history:
        from fsot_mc.paths import ohlcv_csv

        p = ohlcv_csv(symbol)
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        df = df.rename(columns={c: str(c).lower() for c in df.columns}).reset_index()
        df = df.rename(columns={df.columns[0]: "time"})
        for c in ("open", "high", "low", "close", "volume"):
            if c not in df.columns:
                df[c] = df["close"] if c != "volume" else 0
        return df.iloc[-1200:].copy() if len(df) > 1200 else df

    rng = np.random.default_rng(0)
    r = rng.normal(0.0004, 0.012, size=500)
    close = 100.0 * np.cumprod(1.0 + r)
    return pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=500, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e6, 2e6, size=500),
        }
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SYN")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "data" / "exports"))
    args = ap.parse_args()

    from fsot_mc import run_intelligence, verify_fsot_gate, __version__

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    gate = verify_fsot_gate()
    df = load_df(args.symbol, args.history)
    intel = run_intelligence(
        df,
        symbol=args.symbol.upper(),
        horizon=13,
        n_paths=128,
        include_bhs=args.history,
        include_multi_horizon=True,
    )

    meta = {
        "package": "fsot-monte-carlo-intelligence",
        "version": __version__,
        "symbol": args.symbol.upper(),
        "bars": len(df),
        "authority_gate": gate,
        "free_parameters": 0,
        "license": "Apache-2.0",
        "author": "Damian Arthur Palumbo",
        "theory": "https://github.com/dappalumbo91/FSOT-2.1-Lean",
        "disclaimer": "Research only — not financial advice",
    }

    (out / f"{args.symbol.upper()}_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    # Drop heavy equity curves if present
    slim = dict(intel)
    if isinstance(slim.get("bhs"), dict):
        slim["bhs"] = {k: v for k, v in slim["bhs"].items() if k != "equity_curve"}
    (out / f"{args.symbol.upper()}_intelligence.json").write_text(
        json.dumps(slim, indent=2, default=str), encoding="utf-8"
    )

    # Compact CSV for Kaggle/HF tables
    row = {
        "symbol": args.symbol.upper(),
        "primary_signal": intel.get("primary_signal"),
        "primary_confidence": intel.get("primary_confidence"),
        "mc_signal": (intel.get("monte_carlo") or {}).get("signal"),
        "crypto": intel.get("crypto"),
        "free_parameters": 0,
        "authority_ok": gate.get("ok"),
    }
    pd.DataFrame([row]).to_csv(out / f"{args.symbol.upper()}_summary.csv", index=False)
    print(f"Wrote exports → {out}")
    print(f"  signal={row['primary_signal']} conf={row['primary_confidence']} authority_ok={row['authority_ok']}")


if __name__ == "__main__":
    main()
