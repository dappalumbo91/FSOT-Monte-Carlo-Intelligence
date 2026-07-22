"""
FSOT Monte Carlo Intelligence — independent universe discovery workspace.

All required law/data/PFLT eyes live under this folder (vendor/ + fsot_mc/).
External I:/D:/Desktop paths are optional refresh only.
"""

from fsot_mc.accuracy_gate import format_readings_text, run_accuracy_readings
from fsot_mc.adaptive_memory import AdaptiveMemory
from fsot_mc.api_adapters import run_api_bundle, seed_demo_cache
from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.bio_emergence import analyze_biological_emergence
from fsot_mc.discovery import run_discovery
from fsot_mc.formal_bridge import (
    export_lead_obligation,
    formal_status,
    promote_from_intelligence,
    run_soft_court,
)
from fsot_mc.intelligence import run_intelligence, run_universe_scan
from fsot_mc.language_relay import relay_discovery, relay_lead, relay_universe_state
from fsot_mc.mind import FSOTMind, ask, get_mind
from fsot_mc.paths import independence_status
from fsot_mc.pi_ring import PiRing, demo_ring_from_mc
from fsot_mc.pflt_bridge import eyes_with_mc, sample_scene_to_ring
from fsot_mc.polar_student import train_polar_student
from fsot_mc.real_data import build_real_data_bundle
from fsot_mc.realities_client import couple_to_intelligence, poll_runtime
from fsot_mc.universe_atlas import (
    atlas_meta,
    domain_names,
    domains_by_cluster,
    evaluate_domain,
    snapshot_universe,
)
from fsot_mc.universe_mc import run_universe_monte_carlo, simulate_universe_path

from fsot_mc.fast import C_FACTOR as SEED_C
from fsot_mc.fast import PHI as SEED_PHI
from fsot_mc.fast import POOF as SEED_POOF

__version__ = "1.0.0"
__all__ = [
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
    "PiRing",
    "demo_ring_from_mc",
    "eyes_with_mc",
    "sample_scene_to_ring",
    "relay_discovery",
    "relay_lead",
    "relay_universe_state",
    "FSOTMind",
    "ask",
    "get_mind",
    "train_polar_student",
    "export_lead_obligation",
    "formal_status",
    "run_soft_court",
    "promote_from_intelligence",
    "poll_runtime",
    "couple_to_intelligence",
    "run_api_bundle",
    "seed_demo_cache",
    "independence_status",
    "verify_fsot_gate",
    "AUTHORITY_SHA256",
    "SEED_C",
    "SEED_PHI",
    "SEED_POOF",
    "__version__",
]
