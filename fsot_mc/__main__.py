"""python -m fsot_mc — CLI for FSOT Monte Carlo Intelligence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _load_df(symbol: str | None, history: bool, n: int) -> tuple[pd.DataFrame, str]:
    if history and symbol:
        from fsot_mc.paths import ohlcv_csv

        p = ohlcv_csv(symbol)
        if not p.exists():
            raise SystemExit(f"OHLCV not found: {p}")
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        df = df.rename(columns={c: str(c).lower() for c in df.columns}).reset_index()
        df = df.rename(columns={df.columns[0]: "time"})
        for c in ("open", "high", "low", "close", "volume"):
            if c not in df.columns:
                df[c] = df["close"] if c != "volume" else 0
        if len(df) > 1500:
            df = df.iloc[-1500:].copy()
        return df, symbol.upper()

    rng = np.random.default_rng(0)
    r = rng.normal(0.0004, 0.012, size=n)
    close = 100.0 * np.cumprod(1.0 + r)
    df = pd.DataFrame(
        {
            "time": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.uniform(1e6, 2e6, size=n),
        }
    )
    return df, symbol or "SYN"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="FSOT Monte Carlo Intelligence")
    ap.add_argument("command", nargs="?", default="gate", choices=["gate", "intel", "mc", "journal", "bhs"])
    ap.add_argument("--symbol", default="SYN")
    ap.add_argument("--history", action="store_true")
    ap.add_argument("--n-paths", type=int, default=128)
    ap.add_argument("--horizon", type=int, default=13)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    from fsot_mc import __version__, verify_fsot_gate

    if args.command == "gate":
        g = verify_fsot_gate(require_archive=False)
        if args.json:
            print(json.dumps(g, indent=2))
        else:
            print(f"fsot_mc {__version__}")
            print(f"authority_ok={g['ok']}  sha={g['authority_sha256'][:12]}…")
            print(f"float_engine={g['float_engine']['ok']}  bytes={g['authority_bytes']['local_matches']}")
        return 0 if g["ok"] else 2

    df, sym = _load_df(args.symbol, args.history, n=400)

    if args.command == "mc":
        from fsot_mc import run_dynamic_fsot_monte_carlo

        r = run_dynamic_fsot_monte_carlo(
            df, horizon=args.horizon, n_paths=args.n_paths, symbol=sym, persist=False
        )
    elif args.command == "bhs":
        from fsot_mc import run_bhs_backtest

        r = run_bhs_backtest(df, symbol=sym)
    elif args.command == "journal":
        from fsot_mc import run_forward_journal_walk

        r = run_forward_journal_walk(
            df, symbol=sym, horizon=5, n_paths=min(args.n_paths, 64), max_steps=24
        )
    else:  # intel
        from fsot_mc import run_intelligence

        r = run_intelligence(
            df, symbol=sym, horizon=args.horizon, n_paths=args.n_paths, include_bhs=args.history
        )

    if args.json:
        # compact non-curve dump
        print(json.dumps(r, indent=2, default=str))
    else:
        print(f"fsot_mc {__version__}  symbol={sym}  bars={len(df)}")
        if r.get("error"):
            print("ERROR", r["error"])
            return 1
        if args.command == "intel":
            print(f"primary={r.get('primary_signal')} conf={r.get('primary_confidence')}")
            mc = r.get("monte_carlo") or {}
            print(f"mc={mc.get('signal')} conf={mc.get('confidence')}")
            if r.get("bhs"):
                print(f"bhs_commit_acc={r['bhs'].get('commit_directional_accuracy')}")
            print(f"authority_ok={r.get('authority_gate', {}).get('ok')}")
        elif args.command == "journal":
            print(f"decisions={r.get('n_decisions')} acc={r.get('directional_accuracy')}")
            print(f"solid_acc={r.get('solid_directional_accuracy')} conf_acc={r.get('solid_confident_accuracy')}")
        elif args.command == "bhs":
            print(f"commit_acc={r.get('commit_directional_accuracy')} progress={r.get('progress_to_70_80')}")
            print(f"ret={r.get('total_return')} trades={r.get('trades')}")
        else:
            print(f"signal={r.get('signal')} conf={r.get('confidence')}")
            ens = r.get("ensemble") or {}
            print(f"p_up_obs={ens.get('p_up_observed_branch')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
