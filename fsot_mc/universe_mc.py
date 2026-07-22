"""
FSOT Universe Monte Carlo — multipath simulation of fluid spacetime.

Ontology (not markets):
  - One seed engine; 35 domain folds are the map of the universe.
  - Each MC *path* is a possible observation history of the fluid.
  - Observer collapse couples measurement to the scalar (quirk_mod).
  - Collapse TRUE  → domain locks toward observed branch.
  - Collapse FALSE → Poof decoherence branch (weaker / flipped coupling).
  - Cross-scale bridges test As Above, So Below along the D_eff ladder.
  - Ensemble discovers which pathways are stable, contested, or novel.

free_parameters = 0 — only seeds + preregistered folds + path RNG.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, PHI, POOF, PSI_CON
from fsot_mc.universe_atlas import (
    atlas_meta,
    d_eff_ladder,
    domain_names,
    evaluate_domain,
    get_domain,
    snapshot_universe,
    wave1_anchors,
)

SEED_C = float(C_FACTOR)
SEED_PHI = float(PHI)
SEED_POOF = float(POOF)
SEED_PSI = float(PSI_CON)


def collapse_probability(
    phase_departure: float,
    sentiment: float = 0.0,
    consciousness: float = SEED_C,
) -> float:
    """p(collapse to observed branch) — same seed logistic as intelligence spine."""
    intensity = consciousness * SEED_PHI * abs(phase_departure)
    intensity = intensity + consciousness * math.atan(sentiment)
    p = 1.0 / (1.0 + math.exp(-intensity))
    return float(np.clip(p, SEED_POOF, 1.0 - SEED_POOF))


def _bridge_strength(s_low: float, s_high: float) -> float:
    """
    Cross-scale bridge: co-emergence when signs agree and magnitudes couple.
    Uses φ-normalized geometric mean of |S| when same-sign; Poof damp if conflict.
    """
    if s_low * s_high > 0:
        return float(math.sqrt(abs(s_low * s_high)) * (1.0 + SEED_C))
    if s_low * s_high < 0:
        return float(-math.sqrt(abs(s_low * s_high)) * SEED_POOF)
    return 0.0


def simulate_universe_path(
    rng: np.random.Generator,
    *,
    domains: list[str] | None = None,
    shared_phase_scale: float = 1.0,
    observe_fraction: float | None = None,
) -> dict[str, Any]:
    """
    One Monte Carlo path through the FSOT universe map.

    Path state:
      - global phase noise (fluid fluctuation)
      - per-domain collapse to observed vs decoherent branch
      - optional forced observation budget (observe_fraction)
    """
    names = domains or domain_names()
    ladder = [(n, get_domain(n)["D_eff"]) for n in names]
    ladder.sort(key=lambda x: (x[1], x[0]))

    # Global fluid phase (shared across domains — one medium)
    global_phase = float(rng.normal(0.0, shared_phase_scale * SEED_PSI))
    sentiment = float(rng.normal(0.0, SEED_POOF))  # weak external coupling noise

    domain_states: dict[str, Any] = {}
    n_collapse = 0

    for name, _d in ladder:
        base = get_domain(name)
        # Path perturbation of observer phase (not free: scaled by Poof)
        local_noise = float(rng.normal(0.0, SEED_POOF))
        phase_dep = global_phase + local_noise
        p_col = collapse_probability(phase_dep, sentiment=sentiment)
        if observe_fraction is not None:
            # Soft budget: raise/lower collapse by budget around Poof floor
            p_col = float(np.clip(observe_fraction, SEED_POOF, 1.0 - SEED_POOF))

        collapse_true = bool(rng.random() < p_col)
        if collapse_true:
            n_collapse += 1
            # Observed branch: preregistered observed flag + phase shift
            obs = True
            dp = float(base["delta_psi"]) + phase_dep * SEED_C
            hits = float(base["hits"]) + (1.0 if phase_dep > 0 else 0.0)
        else:
            # Decoherent branch: weaker observation, Poof-scaled phase
            obs = False
            dp = float(base["delta_psi"]) + phase_dep * SEED_POOF
            hits = float(base["hits"])

        ev = evaluate_domain(
            name,
            delta_psi=dp,
            recent_hits=hits,
            observed=obs,
            # Path amplitude from consciousness × |phase|
            amplitude=1.0 + SEED_C * abs(phase_dep),
            trend_bias=SEED_POOF * sentiment,
        )
        ev["collapse_true"] = collapse_true
        ev["p_collapse"] = p_col
        ev["phase_departure"] = phase_dep
        domain_states[name] = ev

    # Cross-scale bridges along D_eff ladder (As Above, So Below)
    bridges: list[dict[str, Any]] = []
    ordered = [n for n, _ in ladder]
    for i in range(len(ordered) - 1):
        a, b = ordered[i], ordered[i + 1]
        sa, sb = domain_states[a]["S"], domain_states[b]["S"]
        bridges.append(
            {
                "low": a,
                "high": b,
                "D_low": domain_states[a]["D_eff"],
                "D_high": domain_states[b]["D_eff"],
                "S_low": sa,
                "S_high": sb,
                "strength": _bridge_strength(sa, sb),
                "agree": 1 if sa * sb > 0 else (-1 if sa * sb < 0 else 0),
            }
        )

    # Long-range bridges: quantum ↔ cosmos (contested unification probe)
    long_range = []
    pairs = [
        ("Quantum_Mechanics", "Cosmology"),
        ("Particle_Physics", "Cosmology"),
        ("Biology", "Cosmology"),
        ("Neuroscience", "Cosmology"),
        ("Quantum_Mechanics", "Biology"),
        ("Consciousness_proxy", "Cosmology"),  # may skip if missing
    ]
    # Neuroscience stands in for consciousness fold when present
    if "Neuroscience" in domain_states and "Cosmology" in domain_states:
        pairs.append(("Neuroscience", "Quantum_Mechanics"))
    for a, b in pairs:
        if a not in domain_states or b not in domain_states:
            continue
        sa, sb = domain_states[a]["S"], domain_states[b]["S"]
        long_range.append(
            {
                "a": a,
                "b": b,
                "S_a": sa,
                "S_b": sb,
                "strength": _bridge_strength(sa, sb),
                "agree": 1 if sa * sb > 0 else (-1 if sa * sb < 0 else 0),
            }
        )

    emerge = [n for n, s in domain_states.items() if s["regime"] == "emergence"]
    disperse = [n for n, s in domain_states.items() if s["regime"] == "dispersal"]
    flips = [n for n, s in domain_states.items() if s.get("regime_flip")]

    mean_S = float(np.mean([s["S"] for s in domain_states.values()]))
    mean_bridge = float(np.mean([b["strength"] for b in bridges])) if bridges else 0.0
    agree_frac = float(np.mean([1.0 if b["agree"] > 0 else 0.0 for b in bridges])) if bridges else 0.0

    # Contested cosmology probe from path Cosmology S (bubble-bleed class)
    cosm = domain_states.get("Cosmology")
    quant = domain_states.get("Quantum_Mechanics")
    contested = None
    if cosm is not None:
        # Wave-1 style H0 bridge scalar proxy: 100*(1 + S_cosm * scale) — diagnostic only
        # Uses same structural form as archive wave1 without re-fitting
        S_c = float(cosm["S"])
        S_q = float(quant["S"]) if quant else 0.0
        h0_proxy = 100.0 * (1.0 + S_c * SEED_POOF)  # Poof-scaled diagnostic
        contested = {
            "S_cosm": S_c,
            "S_quant": S_q,
            "h0_proxy": h0_proxy,
            "regime_cosm": cosm["regime"],
            "collapse_cosm": cosm["collapse_true"],
        }

    return {
        "global_phase": global_phase,
        "sentiment": sentiment,
        "n_domains": len(domain_states),
        "collapse_true_fraction": n_collapse / max(len(domain_states), 1),
        "emergence_fraction": len(emerge) / max(len(domain_states), 1),
        "n_emergence": len(emerge),
        "n_dispersal": len(disperse),
        "regime_flips": flips,
        "n_regime_flips": len(flips),
        "mean_S": mean_S,
        "mean_bridge_strength": mean_bridge,
        "ladder_agree_fraction": agree_frac,
        "domains": domain_states,
        "adjacent_bridges": bridges,
        "long_range_bridges": long_range,
        "contested": contested,
        "free_parameters": 0,
    }


def run_universe_monte_carlo(
    *,
    n_paths: int = 256,
    seed: int | None = 0,
    domains: list[str] | None = None,
    shared_phase_scale: float = 1.0,
    store_paths: int = 16,
) -> dict[str, Any]:
    """
    Ensemble of universe pathways under FSOT law.

    Returns:
      - ensemble statistics over domains and bridges
      - discovery hooks (flip rates, bridge distributions, contested probes)
      - canonical baseline snapshot for comparison
    """
    rng = np.random.default_rng(seed)
    n_paths = int(max(n_paths, 8))
    store_paths = int(min(store_paths, n_paths))

    canonical = snapshot_universe()
    paths: list[dict[str, Any]] = []
    stored: list[dict[str, Any]] = []

    # Accumulators
    emerge_fracs: list[float] = []
    collapse_fracs: list[float] = []
    mean_Ss: list[float] = []
    bridge_means: list[float] = []
    agree_fracs: list[float] = []
    flip_counts: list[int] = []
    h0_proxies: list[float] = []
    flip_hist: dict[str, int] = {n: 0 for n in (domains or domain_names())}

    # Domain mean S across paths
    names = domains or domain_names()
    S_sum = {n: 0.0 for n in names}
    S_obs_sum = {n: 0.0 for n in names}
    S_unobs_sum = {n: 0.0 for n in names}
    n_obs = {n: 0 for n in names}
    n_unobs = {n: 0 for n in names}

    # Long-range bridge accumulators
    lr_keys = [
        ("Quantum_Mechanics", "Cosmology"),
        ("Particle_Physics", "Cosmology"),
        ("Biology", "Cosmology"),
        ("Neuroscience", "Cosmology"),
        ("Quantum_Mechanics", "Biology"),
        ("Neuroscience", "Quantum_Mechanics"),
    ]
    lr_strength: dict[tuple[str, str], list[float]] = {k: [] for k in lr_keys}

    for p in range(n_paths):
        path = simulate_universe_path(
            rng,
            domains=names,
            shared_phase_scale=shared_phase_scale,
        )
        paths.append(path)
        if p < store_paths:
            # store compact
            stored.append(
                {
                    "mean_S": path["mean_S"],
                    "emergence_fraction": path["emergence_fraction"],
                    "collapse_true_fraction": path["collapse_true_fraction"],
                    "n_regime_flips": path["n_regime_flips"],
                    "regime_flips": path["regime_flips"],
                    "mean_bridge_strength": path["mean_bridge_strength"],
                    "ladder_agree_fraction": path["ladder_agree_fraction"],
                    "contested": path["contested"],
                    "long_range_bridges": path["long_range_bridges"],
                }
            )

        emerge_fracs.append(path["emergence_fraction"])
        collapse_fracs.append(path["collapse_true_fraction"])
        mean_Ss.append(path["mean_S"])
        bridge_means.append(path["mean_bridge_strength"])
        agree_fracs.append(path["ladder_agree_fraction"])
        flip_counts.append(path["n_regime_flips"])
        for f in path["regime_flips"]:
            if f in flip_hist:
                flip_hist[f] += 1
        if path.get("contested"):
            h0_proxies.append(float(path["contested"]["h0_proxy"]))

        for n, st in path["domains"].items():
            if n not in S_sum:
                continue
            S_sum[n] += float(st["S"])
            if st["collapse_true"]:
                S_obs_sum[n] += float(st["S"])
                n_obs[n] += 1
            else:
                S_unobs_sum[n] += float(st["S"])
                n_unobs[n] += 1

        for br in path["long_range_bridges"]:
            key = (br["a"], br["b"])
            if key in lr_strength:
                lr_strength[key].append(float(br["strength"]))

    def _stats(arr: list[float]) -> dict[str, float]:
        a = np.asarray(arr, dtype=float)
        if len(a) == 0:
            return {"mean": 0.0, "std": 0.0, "p10": 0.0, "p50": 0.0, "p90": 0.0}
        return {
            "mean": float(np.mean(a)),
            "std": float(np.std(a)),
            "p10": float(np.quantile(a, 0.10)),
            "p50": float(np.quantile(a, 0.50)),
            "p90": float(np.quantile(a, 0.90)),
        }

    domain_ensemble = {}
    for n in names:
        can = get_domain(n)
        domain_ensemble[n] = {
            "S_canonical": can["S_canonical"],
            "S_path_mean": S_sum[n] / n_paths,
            "dS_mean": S_sum[n] / n_paths - can["S_canonical"],
            "S_observed_branch_mean": (S_obs_sum[n] / n_obs[n]) if n_obs[n] else None,
            "S_decoherent_branch_mean": (S_unobs_sum[n] / n_unobs[n]) if n_unobs[n] else None,
            "flip_rate": flip_hist.get(n, 0) / n_paths,
            "regime_canonical": can["regime"],
            "cluster": can["cluster"],
            "D_eff": can["D_eff"],
        }

    long_range_ensemble = {
        f"{a}__{b}": {
            "strength": _stats(vals),
            "a": a,
            "b": b,
        }
        for (a, b), vals in lr_strength.items()
        if vals
    }

    # Top flip-prone domains (discovery: where observation most rewrites regime)
    flip_ranked = sorted(
        ((n, domain_ensemble[n]["flip_rate"]) for n in names),
        key=lambda x: -x[1],
    )[:10]

    # Largest |dS| from canonical (pathway sensitivity)
    sens_ranked = sorted(
        ((n, abs(domain_ensemble[n]["dS_mean"])) for n in names),
        key=lambda x: -x[1],
    )[:10]

    return {
        "error": None,
        "method": "fsot_universe_monte_carlo",
        "free_parameters": 0,
        "n_paths": n_paths,
        "seed": seed,
        "atlas": atlas_meta(),
        "canonical_snapshot": {
            "emergence_fraction": canonical["emergence_fraction"],
            "mean_S": canonical["mean_S"],
            "n_emergence": canonical["n_emergence"],
            "n_dispersal": canonical["n_dispersal"],
        },
        "ensemble": {
            "emergence_fraction": _stats(emerge_fracs),
            "collapse_true_fraction": _stats(collapse_fracs),
            "mean_S": _stats(mean_Ss),
            "mean_bridge_strength": _stats(bridge_means),
            "ladder_agree_fraction": _stats(agree_fracs),
            "n_regime_flips": _stats([float(x) for x in flip_counts]),
            "h0_proxy": _stats(h0_proxies) if h0_proxies else None,
        },
        "domain_ensemble": domain_ensemble,
        "long_range_bridges": long_range_ensemble,
        "discovery_hints": {
            "top_flip_domains": [{"domain": n, "flip_rate": r} for n, r in flip_ranked if r > 0],
            "top_sensitivity_domains": [{"domain": n, "abs_dS_mean": s} for n, s in sens_ranked],
            "wave1_anchors": wave1_anchors(),
        },
        "sample_paths": stored,
        "note": (
            "FSOT universe multipath: one fluid, 35 domain folds, observer collapse, "
            "cross-scale bridges. Discovers pathway sensitivity and regime flips — "
            "not market signals. free_parameters=0."
        ),
    }
