"""
FSOT Universe Domain Atlas — core folds + extension panels.

Loads full_atlas.json (35 + 367) when built; falls back to portable core atlas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fsot_mc.fast import ScalarInputF, compute_scalar_terms_fast

_DIR = Path(__file__).resolve().parent
_CORE_PATH = _DIR / "universe_atlas.json"
_FULL_PATH = _DIR / "full_atlas.json"
_CACHE: dict[str, Any] | None = None


def load_atlas(*, prefer_full: bool = True) -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if prefer_full and _FULL_PATH.is_file():
        _CACHE = json.loads(_FULL_PATH.read_text(encoding="utf-8"))
    else:
        _CACHE = json.loads(_CORE_PATH.read_text(encoding="utf-8"))
    return _CACHE


def reload_atlas() -> dict[str, Any]:
    global _CACHE
    _CACHE = None
    return load_atlas(prefer_full=True)


def domain_names(*, kind: str | None = None) -> list[str]:
    """kind: None=all, 'core', 'extension_panel'."""
    domains = load_atlas()["domains"]
    if kind is None:
        return list(domains.keys())
    return [n for n, d in domains.items() if d.get("kind", "core") == kind or (
        kind == "core" and d.get("kind") in (None, "core")
    )]


def core_names() -> list[str]:
    a = load_atlas()
    if "core_names" in a:
        return list(a["core_names"])
    return domain_names(kind="core")


def extension_names() -> list[str]:
    a = load_atlas()
    if "extension_names" in a:
        return list(a["extension_names"])
    return [n for n, d in a["domains"].items() if d.get("kind") == "extension_panel"]


def get_domain(name: str) -> dict[str, Any]:
    domains = load_atlas()["domains"]
    if name not in domains:
        raise KeyError(f"Unknown domain fold: {name}")
    return dict(domains[name])


def domains_by_cluster() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name, d in load_atlas()["domains"].items():
        out.setdefault(d.get("cluster") or "unknown", []).append(name)
    for k in out:
        out[k].sort(key=lambda n: get_domain(n)["D_eff"])
    return out


def d_eff_ladder(names: list[str] | None = None) -> list[tuple[str, int]]:
    names = names or domain_names()
    items = [(n, int(get_domain(n)["D_eff"])) for n in names]
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
    base = get_domain(name)
    dp = float(base["delta_psi"] if delta_psi is None else delta_psi)
    dt = float(base.get("delta_theta", 1.0) if delta_theta is None else delta_theta)
    hits = float(base.get("hits", base.get("recent_hits", 0)) if recent_hits is None else recent_hits)
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
        "kind": base.get("kind", "core"),
        "cluster": base.get("cluster"),
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
        "canonical_regime": base.get("regime"),
        "regime_flip": (S > 0) != (float(S_can) > 0),
        "routes_to_core": base.get("routes_to_core"),
        "lean_module": base.get("lean_module"),
    }


def snapshot_universe(
    *,
    names: list[str] | None = None,
    observed_override: bool | None = None,
    psi_shift: float = 0.0,
) -> dict[str, Any]:
    names = names or domain_names()
    rows = []
    for name in names:
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
        "n_core": a.get("n_core") or len(a.get("core_names") or []),
        "n_extension": a.get("n_extension") or len(a.get("extension_names") or []),
        "S_cosm": a.get("S_cosm"),
        "S_quant": a.get("S_quant"),
        "purpose": a.get("purpose"),
        "built_at": a.get("built_at"),
        "free_parameters": 0,
    }
