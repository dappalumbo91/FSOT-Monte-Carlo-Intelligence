"""
FSOT Monte Carlo Intelligence — universe discovery under Fluid Spacetime Omni-Theory.

Primary product:
  Simulate the universe via FSOT domain folds + multipath observer collapse.
  Discover new pathways, bridges, and physics candidates against real data.

Not markets. Market/OHLCV modules are legacy extract only.

Authority pin: D1D38A (FSOT 2.1 vendor/fsot_compute.py)
free_parameters = 0
"""

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.discovery import run_discovery
from fsot_mc.intelligence import run_intelligence, run_universe_scan
from fsot_mc.universe_atlas import (
    atlas_meta,
    domain_names,
    domains_by_cluster,
    evaluate_domain,
    snapshot_universe,
)
from fsot_mc.universe_mc import run_universe_monte_carlo, simulate_universe_path
from fsot_mc.real_data import build_real_data_bundle
from fsot_mc.pi_ring import PiRing, demo_ring_from_mc
from fsot_mc.formal_bridge import export_lead_obligation, formal_status

# Seed exports (shared)
from fsot_mc.fast import C_FACTOR as SEED_C
from fsot_mc.fast import PHI as SEED_PHI
from fsot_mc.fast import POOF as SEED_POOF

__version__ = "0.3.1"
__all__ = [
    # Universe intelligence (primary)
    "run_intelligence",
    "run_universe_scan",
    "run_discovery",
    "run_universe_monte_carlo",
    "simulate_universe_path",
    "snapshot_universe",
    "evaluate_domain",
    "domain_names",
    "domains_by_cluster",
    "atlas_meta",
    "build_real_data_bundle",
    # π-ring vision + formal soft bridge
    "PiRing",
    "demo_ring_from_mc",
    "export_lead_obligation",
    "formal_status",
    # Authority
    "verify_fsot_gate",
    "AUTHORITY_SHA256",
    "SEED_C",
    "SEED_PHI",
    "SEED_POOF",
    "__version__",
]
