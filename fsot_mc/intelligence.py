"""
FSOT Monte Carlo Intelligence — unified high-level API.

Builds out the intelligence stack:
  1) Authority gate (FSOT fidelity)
  2) Pattern memory training (solidify accurate signatures)
  3) Dynamic multipath Monte Carlo (observer collapse)
  4) Optional dual-scale BHS commit layer
  5) Multi-horizon ensemble
  6) Crypto / high-vol regime awareness (seed-scaled, not free fits)
  7) Forward journal scoring hooks

free_parameters = 0 throughout.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from fsot_mc.authority_gate import verify_fsot_gate
from fsot_mc.bhs_engine import decide_bhs, dual_scale_state, run_bhs_backtest
from fsot_mc.intrinsic import (
    SEED_C,
    SEED_GAMMA,
    SEED_PHI,
    SEED_POOF,
    evaluate_market_bar,
    route_for_window,
)
from fsot_mc.monte_carlo import (
    run_dynamic_fsot_monte_carlo,
    run_fsot_monte_carlo,
    train_pattern_memory,
)
from fsot_mc.pattern_memory import PatternMemory, pred_dir_from_ev


# Crypto-class tickers get Finance fold + vol-aware path counts (not free params)
_CRYPTO_HINTS = {
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK", "LTC",
    "DOT", "MATIC", "ATOM", "NEAR", "APT", "ARB", "OP", "SUI", "TIA", "INJ",
}


def is_crypto_symbol(symbol: str) -> bool:
    s = symbol.upper().replace("-USD", "").replace("USDT", "").replace("USD", "")
    return s in _CRYPTO_HINTS or s.endswith("BTC") or s.endswith("ETH")


def vol_regime(rets: np.ndarray, window: int = 21) -> dict[str, float]:
    """Classify volatility regime using seed γ as scale (not free threshold)."""
    r = rets[np.isfinite(rets)]
    if len(r) < window:
        return {"sig": 0.0, "sig_gamma": 0.0, "high_vol": 0.0}
    block = r[-window:]
    sig = float(np.std(block, ddof=1)) if len(block) > 1 else 0.0
    # High vol when σ > γ · median(|r|)  (seed-only)
    med = float(np.median(np.abs(block))) if len(block) else 0.0
    thresh = SEED_GAMMA * max(med, 1e-8)
    high = 1.0 if sig > thresh * SEED_PHI else 0.0  # φ elevates bar slightly
    return {
        "sig": sig,
        "sig_gamma_units": sig / max(SEED_GAMMA * 0.01, 1e-12),
        "high_vol": high,
        "thresh": thresh * SEED_PHI,
    }


def recommend_paths(symbol: str, rets: np.ndarray, base: int = 256) -> int:
    """
    Path count from Fib ladder, boosted for crypto/high-vol.
    More paths stabilize quantiles under thicker tails — not a free fit coeff.
    """
    reg = vol_regime(rets)
    n = base
    if is_crypto_symbol(symbol) or reg["high_vol"] > 0:
        # next Fib step
        n = 512 if base <= 256 else 832  # 512+φ-ish bump; clamp later
        n = 512
    # clamp to practical
    return int(min(max(n, 64), 1024))


def multi_horizon_mc(
    df: pd.DataFrame,
    *,
    symbol: str = "",
    horizons: tuple[int, ...] = (5, 8, 13, 21),
    n_paths: int | None = None,
    seed: int = 1,
    persist: bool = False,
) -> dict[str, Any]:
    """
    Run dynamic FSOT MC across Fib horizons; fuse signals by consciousness-weighted vote.
    """
    if df is None or len(df) < 80:
        return {"error": "insufficient_data"}

    close = df["close"].astype(float).values
    rets = pd.Series(close).pct_change().fillna(0.0).values
    n_paths = n_paths or recommend_paths(symbol, rets)

    # Train memory once on full history, reuse across horizons
    mem, train_diag = train_pattern_memory(
        df, window=21, symbol=symbol, step=1, max_bars=900, resume=False
    )

    per_h: dict[str, Any] = {}
    votes: list[tuple[str, float]] = []  # (signal, weight)

    for h in horizons:
        mc = run_fsot_monte_carlo(
            df,
            horizon=h,
            n_paths=n_paths,
            symbol=symbol,
            seed=seed + h,
            memory=mem,
            dynamic=True,
        )
        if mc.get("error"):
            continue
        conf = float(mc.get("confidence", 0.0))
        # Weight by conf × (1 + solid) × 1/√h  (longer horizon less weight — φ-free 1/sqrt)
        solid = float((mc.get("pattern") or {}).get("bias", {}).get("solidified", 0))
        w = conf * (1.0 + SEED_C * solid) / math.sqrt(max(h, 1))
        per_h[str(h)] = {
            "signal": mc["signal"],
            "confidence": conf,
            "p_up_obs": mc["ensemble"]["p_up_observed_branch"],
            "expected_return_obs": mc["ensemble"]["expected_return_observed_branch"],
            "gated": mc.get("gated_unsolidified"),
            "solidified": solid > 0,
            "weight": w,
        }
        votes.append((str(mc["signal"]), w))

    # Fuse
    score = {"LONG": 0.0, "SHORT": 0.0, "FLAT": 0.0}
    for sig, w in votes:
        score[sig] = score.get(sig, 0.0) + w
    fused = max(score, key=score.get) if votes else "FLAT"
    total_w = sum(score.values()) or 1.0
    fused_conf = float(score[fused] / total_w)

    # Require solid agreement: if fused is directional but majority not solid → FLAT
    solid_dirs = [
        per_h[h]["signal"]
        for h in per_h
        if per_h[h].get("solidified") and per_h[h]["signal"] != "FLAT"
    ]
    if fused in ("LONG", "SHORT"):
        if not solid_dirs:
            fused = "FLAT"
            fused_conf *= SEED_POOF
        elif solid_dirs.count(fused) < max(1, len(solid_dirs) // 2):
            fused = "FLAT"
            fused_conf *= SEED_POOF

    reg = vol_regime(rets)
    route = route_for_window(21)
    return {
        "error": None,
        "method": "fsot_multi_horizon_intelligence",
        "free_parameters": 0,
        "symbol": symbol,
        "crypto": is_crypto_symbol(symbol),
        "vol_regime": reg,
        "route": {"name": route["name"], "D_eff": route["D_eff"]},
        "n_paths": n_paths,
        "horizons": per_h,
        "fused_signal": fused,
        "fused_confidence": fused_conf,
        "vote_mass": score,
        "training": train_diag,
        "memory": mem.summary(),
        "authority_gate": verify_fsot_gate(require_archive=False),
        "note": (
            "Multi-horizon FSOT dynamic MC; fuse by consciousness-weighted votes; "
            "directional only when solidified patterns agree. free_parameters=0."
        ),
    }


def run_intelligence(
    df: pd.DataFrame,
    *,
    symbol: str = "",
    horizon: int = 13,
    n_paths: int | None = None,
    seed: int = 1,
    include_bhs: bool = True,
    include_multi_horizon: bool = True,
    capital: float = 10_000.0,
) -> dict[str, Any]:
    """
    Full intelligence snapshot for one OHLCV series.
    """
    gate = verify_fsot_gate(require_archive=False)
    if not gate["ok"]:
        return {
            "error": "fsot_authority_gate_failed",
            "authority_gate": gate,
            "free_parameters": 0,
        }

    if df is None or len(df) < 100:
        return {"error": "insufficient_data", "authority_gate": gate}

    close = df["close"].astype(float).values
    rets = pd.Series(close).pct_change().fillna(0.0).values
    n_paths = n_paths or recommend_paths(symbol, rets)

    dyn = run_dynamic_fsot_monte_carlo(
        df,
        horizon=horizon,
        n_paths=n_paths,
        symbol=symbol,
        seed=seed,
        persist=False,
        max_train_bars=900,
    )

    out: dict[str, Any] = {
        "error": dyn.get("error"),
        "method": "fsot_monte_carlo_intelligence_v1",
        "free_parameters": 0,
        "symbol": symbol,
        "crypto": is_crypto_symbol(symbol),
        "authority_gate": gate,
        "vol_regime": vol_regime(rets),
        "monte_carlo": {
            "signal": dyn.get("signal"),
            "confidence": dyn.get("confidence"),
            "gated_unsolidified": dyn.get("gated_unsolidified"),
            "ensemble": dyn.get("ensemble"),
            "pattern": dyn.get("pattern"),
            "training": dyn.get("training"),
            "state0": dyn.get("state0"),
            "horizon": dyn.get("horizon"),
            "n_paths": dyn.get("n_paths"),
        },
    }

    if include_multi_horizon and dyn.get("error") is None:
        out["multi_horizon"] = multi_horizon_mc(
            df, symbol=symbol, n_paths=min(n_paths, 256), seed=seed
        )
        out["primary_signal"] = out["multi_horizon"].get("fused_signal", dyn.get("signal"))
        out["primary_confidence"] = out["multi_horizon"].get(
            "fused_confidence", dyn.get("confidence")
        )
    else:
        out["primary_signal"] = dyn.get("signal")
        out["primary_confidence"] = dyn.get("confidence")

    if include_bhs and len(df) >= 120:
        bhs = run_bhs_backtest(df, capital=capital, symbol=symbol)
        out["bhs"] = {
            "commit_directional_accuracy": bhs.get("commit_directional_accuracy"),
            "progress_to_70_80": bhs.get("progress_to_70_80"),
            "total_return": bhs.get("total_return"),
            "trades": bhs.get("trades"),
            "pct_hold": bhs.get("pct_hold"),
            "sharpe": bhs.get("sharpe"),
            "n_solidified": (bhs.get("pattern_memory") or {}).get("n_solidified"),
        }
        # Live dual-scale commit suggestion (not full backtest)
        vols = df["volume"].astype(float).values if "volume" in df.columns else None
        st = dual_scale_state(rets, vols, 0.0, window=21)
        # Use MC memory if available
        mem_sum = (dyn.get("pattern") or {}).get("memory_summary") or {}
        bias = (dyn.get("pattern") or {}).get("bias") or {
            "solidified": 0.0,
            "strength": 0.0,
            "dir": 0.0,
            "trials": 0.0,
            "accuracy": 0.5,
        }
        live_action = decide_bhs(st, bias, recent_rets=rets[-8:])
        out["live_bhs_action"] = live_action
        out["live_dual_scale"] = {
            "mu": st.get("mu"),
            "scale_agree": st.get("scale_agree"),
            "S_fast": st.get("S_fast"),
            "S_slow": st.get("S_slow"),
            "pred_dir": st.get("pred_dir"),
            "pattern_memory_n_solid": mem_sum.get("n_solidified"),
        }

    out["epistemic_tier"] = "measured_application"
    out["note"] = (
        "FSOT 2.1 seed engine applied to multipath observer-collapse intelligence. "
        "Authority pin D1D38A. Research only — not financial advice."
    )
    return out
