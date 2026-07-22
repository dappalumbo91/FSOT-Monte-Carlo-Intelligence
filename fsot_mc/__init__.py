"""
FSOT Monte Carlo Intelligence — standalone package.

Fluid Spacetime Omni-Theory (FSOT 2.1) applied as observer-collapse multipath
Monte Carlo intelligence with pattern solidification.

Authority: vendor/fsot_compute.py pin D1D38A (I: archive / GitHub FSOT-2.1-Lean)
Zero free parameters: seeds π, e, φ, γ, Catalan + preregistered folds only.
"""

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.bhs_engine import HOLD_HORIZON, decide_bhs, dual_scale_state, run_bhs_backtest
from fsot_mc.forward_journal import ForwardJournal, run_forward_journal_walk
from fsot_mc.intelligence import multi_horizon_mc, run_intelligence
from fsot_mc.intrinsic import (
    SEED_C,
    SEED_PHI,
    SEED_POOF,
    evaluate_market_bar,
    spine_scalars,
)
from fsot_mc.monte_carlo import (
    collapse_probability,
    mc_walkforward_hit,
    run_dynamic_fsot_monte_carlo,
    run_fsot_monte_carlo,
    train_pattern_memory,
)
from fsot_mc.pattern_memory import SOLIDIFY_ACC, PatternMemory

__version__ = "0.2.0"
__all__ = [
    "run_fsot_monte_carlo",
    "run_dynamic_fsot_monte_carlo",
    "train_pattern_memory",
    "mc_walkforward_hit",
    "collapse_probability",
    "PatternMemory",
    "SOLIDIFY_ACC",
    "decide_bhs",
    "run_bhs_backtest",
    "dual_scale_state",
    "HOLD_HORIZON",
    "evaluate_market_bar",
    "spine_scalars",
    "SEED_C",
    "SEED_PHI",
    "SEED_POOF",
    "verify_fsot_gate",
    "AUTHORITY_SHA256",
    "run_intelligence",
    "multi_horizon_mc",
    "ForwardJournal",
    "run_forward_journal_walk",
    "__version__",
]
