"""
FSOT Universe Domain Atlas — the map of reality folds.

Not markets. This is the preregistered 35-domain NeuroLab spine from FSOT 2.1
authority (D1D38A). Domains are *routes* of one scalar engine, not siloed theories.

As Above, So Below = walk the D_eff ladder; same seeds, different folds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fsot_mc.fast import ScalarInputF, compute_scalar_fast, compute_scalar_terms_fast

_ATLAS_PATH = Path(__file__).resolve().parent / "universe_atlas.json"
_CACHE: dict[str, Any] | None = None


def load_atlas() -> dict[str, Any]:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(_ATLAS_PATH.read_text(encoding="utf-8"))
    return _CACHE


def domain_names() -> list[str]:
    return list(load_atlas()["domains"].keys())


def get_domain(name: str) -> dict[str, Any]:
    domains = load_atlas()["domains"]
    if name not in domains:
        raise KeyError(f"Unknown domain fold: {name}")
    return dict(domains[name])


def domains_by_cluster() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name, d in load_atlas()["domains"].items():
        out.setdefault(d["cluster"], []).append(name)
    for k in out:
        out[k].sort(key=lambda n: get_domain(n)["D_eff"])
    return out


def d_eff_ladder() -> list[tuple[str, int]]:
    """Domains sorted by effective dimension (quantum → cosmos)."""
    items = [(n, int(d["D_eff"])) for n, d in load_atlas()["domains"].items()]
    items.sort(key=lambda x: (x[1], x[0]))
    return items


def evaluate_domain(
    name: str,
    *,
    delta_psi: float | None = None,
    delta_theta: float | None = None,
    recent_hits: float | None = None,
    observed: bool | None = None,
    N: float = 1.0,
    P: float = 1.0,
    rho: float = 1.0,
    scale: float = 1.0,
    amplitude: float = 1.0,
    trend_bias: float = 0.0,
) -> dict[str, Any]:
    """
    Evaluate FSOT scalar S at a domain fold, with optional pathway perturbations.
    Perturbations are *path state*, not free fit parameters.
    """
    base = get_domain(name)
    dp = float(base["delta_psi"] if delta_psi is None else delta_psi)
    dt = float(base["delta_theta"] if delta_theta is None else delta_theta)
    hits = float(base["hits"] if recent_hits is None else recent_hits)
    obs = bool(base["observed"] if observed is None else observed)
    D = float(base["D_eff"])

    si = ScalarInputF(
        N=N,
        P=P,
        D_eff=D,
        delta_psi=dp,
        delta_theta=dt,
        recent_hits=hits,
        observed=obs,
        rho=rho,
        scale=scale,
        amplitude=amplitude,
        trend_bias=trend_bias,
    )
    terms = compute_scalar_terms_fast(si)
    S = terms["S"]
    S_can = float(base["S_canonical"])
    return {
        "domain": name,
        "cluster": base["cluster"],
        "D_eff": int(base["D_eff"]),
        "delta_psi": dp,
        "delta_theta": dt,
        "recent_hits": hits,
        "observed": obs,
        "S": float(S),
        "S_canonical": S_can,
        "dS": float(S - S_can),
        "T1": terms["T1"],
        "T2": terms["T2"],
        "T3": terms["T3"],
        "K": terms["K"],
        "regime": "emergence" if S > 0 else "dispersal",
        "canonical_regime": base["regime"],
        "regime_flip": (S > 0) != (S_can > 0),
    }


def snapshot_universe(
    *,
    observed_override: bool | None = None,
    psi_shift: float = 0.0,
) -> dict[str, Any]:
    """Evaluate all 35 domains (optionally shared observer / phase shift)."""
    rows = []
    for name in domain_names():
        base = get_domain(name)
        rows.append(
            evaluate_domain(
                name,
                delta_psi=float(base["delta_psi"]) + psi_shift,
                observed=observed_override if observed_override is not None else base["observed"],
            )
        )
    emerge = sum(1 for r in rows if r["regime"] == "emergence")
    return {
        "n_domains": len(rows),
        "n_emergence": emerge,
        "n_dispersal": len(rows) - emerge,
        "emergence_fraction": emerge / max(len(rows), 1),
        "mean_S": sum(r["S"] for r in rows) / max(len(rows), 1),
        "domains": {r["domain"]: r for r in rows},
        "ladder": sorted(rows, key=lambda r: r["D_eff"]),
        "free_parameters": 0,
    }


def wave1_anchors() -> dict[str, Any]:
    return dict(load_atlas().get("wave1_anchors") or {})


def atlas_meta() -> dict[str, Any]:
    a = load_atlas()
    return {
        "version": a.get("version"),
        "authority_sha256": a.get("authority_sha256"),
        "domain_count": len(a.get("domains") or {}),
        "S_cosm": a.get("S_cosm"),
        "S_quant": a.get("S_quant"),
        "purpose": a.get("purpose"),
        "free_parameters": 0,
    }
