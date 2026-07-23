"""
Contested physics probes — deeper dual-anchor / tension readouts under FSOT MC.

Uses:
  - wave1 anchors from atlas
  - optional synced contested_observables_closure / cosmology benchmarks
  - universe path contested proxies

free_parameters = 0
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, PHI, POOF
from fsot_mc.paths import PACKAGE_ROOT
from fsot_mc.universe_atlas import wave1_anchors

SEED_C = float(C_FACTOR)
SEED_PHI = float(PHI)
SEED_POOF = float(POOF)

BUNDLE = PACKAGE_ROOT / "vendor" / "archive_bundle"


def _load_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_contested_closure() -> dict[str, Any] | None:
    p = BUNDLE / "benchmarks" / "contested_observables_closure.json"
    if not p.is_file():
        # alternate flat name
        for cand in BUNDLE.rglob("contested_observables_closure.json"):
            p = cand
            break
        else:
            return None
    data = _load_json(p)
    return data if isinstance(data, dict) else None


def load_cosmology_anomalies() -> dict[str, Any] | None:
    for cand in BUNDLE.rglob("cosmology_anomalies_benchmark.json"):
        data = _load_json(cand)
        return data if isinstance(data, dict) else None
    return None


def live_recompute_wave1_anchors() -> dict[str, Any]:
    """
    Live recompute of wave1 anchors from atlas engine — claimed measured structure.
    Compares atlas wave1 computed/measured pairs and reports relative errors.
    """
    anchors = wave1_anchors()
    rows = []
    for name, payload in (anchors or {}).items():
        if not isinstance(payload, dict):
            continue
        comp = payload.get("computed")
        meas = payload.get("measured")
        err = None
        if comp is not None and meas is not None and float(meas) != 0:
            err = abs(float(comp) - float(meas)) / abs(float(meas)) * 100.0
        rows.append(
            {
                "name": name,
                "formula": payload.get("formula"),
                "computed": comp,
                "measured": meas,
                "rel_error_pct": err,
                "within_0_5": err is not None and err <= 0.5,
                "within_2": err is not None and err <= 2.0,
            }
        )
    within = sum(1 for r in rows if r.get("within_0_5"))
    return {
        "id": "CONT-WAVE1-LIVE-RECOMPUTE",
        "class": "contested_physics",
        "title": "Wave-1 anchors live recompute vs measured",
        "n": len(rows),
        "n_within_0_5pct": within,
        "rows": rows,
        "score": (within / len(rows)) if rows else 0.0,
        "epistemic_tier": "measured_application",
        "hypothesis": (
            "Seed-engine wave1 anchors recomputed live match archive measured targets "
            "within tight relative error without free-parameter refit."
        ),
        "free_parameters": 0,
    }


def probe_h0_bridge(mc: dict[str, Any]) -> dict[str, Any]:
    """
    Dual-anchor style H0 probe from path ensemble h0_proxy + wave1 anchors.
    Diagnostic — not a least-squares H0 fit.
    """
    ens = (mc.get("ensemble") or {}).get("h0_proxy") or {}
    anchors = wave1_anchors()
    h0_w1 = anchors.get("H0") or {}
    measured = h0_w1.get("measured")  # typically Planck-class 67.4 in wave1 suite
    computed = h0_w1.get("computed")

    # SH0ES-class local ~73 as literature anchor (external constant, not free fit)
    sh0es = 73.04
    planck = float(measured) if measured is not None else 67.4

    mean = ens.get("mean")
    p10, p50, p90 = ens.get("p10"), ens.get("p50"), ens.get("p90")
    span = (p90 - p10) if (p10 is not None and p90 is not None) else None

    between = None
    if mean is not None:
        lo, hi = min(planck, sh0es), max(planck, sh0es)
        between = lo <= float(mean) <= hi

    score = 0.0
    if span is not None:
        score += min(1.0, float(span) / max(abs(sh0es - planck), 1e-6))
    if between:
        score = min(1.0, score + SEED_C)

    return {
        "id": "CONT-H0-DUAL-ANCHOR",
        "class": "contested_physics",
        "title": "H0 dual-anchor bridge under observer paths",
        "planck_like": planck,
        "sh0es_like": sh0es,
        "wave1_computed": computed,
        "ensemble_h0_proxy": ens,
        "proxy_between_anchors": between,
        "span": span,
        "score": score,
        "hypothesis": (
            "Observer-coupled Cosmology folds produce an H0-proxy distribution; "
            "span covering Planck–SH0ES class anchors is a bubble-bleed dual-anchor lead."
        ),
        "epistemic_tier": "scaffold",
        "free_parameters": 0,
    }


def probe_quantum_cosmos_bridge(mc: dict[str, Any]) -> dict[str, Any]:
    lr = mc.get("long_range_bridges") or {}
    key = "Quantum_Mechanics__Cosmology"
    payload = lr.get(key) or {}
    st = payload.get("strength") or {}
    mean = float(st.get("mean") or 0.0)
    std = float(st.get("std") or 0.0)
    score = abs(mean) / (SEED_POOF + abs(std))
    return {
        "id": "CONT-QM-COSMO-BRIDGE",
        "class": "contested_physics",
        "title": "Quantum ↔ Cosmology long-range bridge stability",
        "strength": st,
        "score": float(score),
        "hypothesis": (
            "Stable (or controlled-sign) QM–Cosmology bridge under multipath observation "
            "is a unification-structure lead for formal panel follow-up."
        ),
        "epistemic_tier": "scaffold",
        "free_parameters": 0,
    }


def probe_regime_flip_cosmos(mc: dict[str, Any]) -> dict[str, Any]:
    de = mc.get("domain_ensemble") or {}
    cosm = de.get("Cosmology") or {}
    flip = float(cosm.get("flip_rate") or 0.0)
    return {
        "id": "CONT-COSMO-FLIP",
        "class": "contested_physics",
        "title": "Cosmology regime flip rate under observation",
        "flip_rate": flip,
        "S_canonical": cosm.get("S_canonical"),
        "S_path_mean": cosm.get("S_path_mean"),
        "score": flip,
        "hypothesis": (
            "High Cosmology flip rate means observation history rewrites dispersal/emergence — "
            "priority for dual-anchor and bubble-bleed formal work."
        ),
        "epistemic_tier": "measured_application",
        "free_parameters": 0,
    }


def probe_archive_contested_summary() -> dict[str, Any] | None:
    """Surface headline stats from synced contested_observables_closure if present."""
    raw = load_contested_closure()
    if not raw:
        return None
    # Flexible schema — extract common fields
    summary = {
        "id": "CONT-ARCHIVE-CLOSURE",
        "class": "contested_physics",
        "title": "Archive contested observables closure (synced)",
        "source": "vendor/archive_bundle/.../contested_observables_closure.json",
        "keys": list(raw.keys())[:20],
        "score": 1.0 if raw.get("verdict") or raw.get("overall") or raw.get("status") else 0.5,
        "raw_excerpt": {
            k: raw[k]
            for k in list(raw.keys())[:8]
            if not isinstance(raw[k], (list, dict))
        },
        "epistemic_tier": "measured",
        "free_parameters": 0,
    }
    # Try nested stats
    for k in ("pooled_median_error_pct", "fsot_pooled_median", "headline", "verdict", "status"):
        if k in raw:
            summary[k] = raw[k]
    return summary


def run_contested_physics_pack(mc: dict[str, Any]) -> dict[str, Any]:
    probes = [
        probe_h0_bridge(mc),
        probe_quantum_cosmos_bridge(mc),
        probe_regime_flip_cosmos(mc),
        live_recompute_wave1_anchors(),
    ]
    arch = probe_archive_contested_summary()
    if arch:
        probes.append(arch)

    # Domain flip hotspots already in MC — lift cosmo-adjacent
    de = mc.get("domain_ensemble") or {}
    for name in ("Particle_Astrophysics", "Quantum_Gravity", "Astrophysics", "Dark_Energy"):
        # Dark_Energy may be extension-only after full atlas
        row = de.get(name)
        if not row:
            continue
        fr = float(row.get("flip_rate") or 0.0)
        if fr >= SEED_POOF:
            probes.append(
                {
                    "id": f"CONT-FLIP-{name}",
                    "class": "contested_physics",
                    "title": f"{name} observation flip hotspot",
                    "domain": name,
                    "flip_rate": fr,
                    "score": fr,
                    "epistemic_tier": "measured_application",
                    "free_parameters": 0,
                }
            )

    probes.sort(key=lambda p: -float(p.get("score") or 0.0))
    return {
        "method": "fsot_contested_physics_pack",
        "free_parameters": 0,
        "n_probes": len(probes),
        "probes": probes,
        "top": probes[:10],
        "note": (
            "Contested-sector probes under FSOT multipath observation. "
            "Leads for formal panels — not automatic new physics claims."
        ),
    }
