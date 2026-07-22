"""Minimal import check for a new conversation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fsot_mc import (
    __version__,
    SOLIDIFY_ACC,
    SEED_C,
    run_fsot_monte_carlo,
    PatternMemory,
)

print("fsot_mc", __version__)
print("C", SEED_C, "SOLIDIFY", SOLIDIFY_ACC)
print("exports ok", PatternMemory, run_fsot_monte_carlo)
