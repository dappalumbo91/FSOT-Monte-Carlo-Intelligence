"""
Build the full FSOT universe atlas: 35 core folds + 367 extension panels.

Sources (priority):
  1) vendor/archive_bundle/ synced from I: (navigator + fixtures)
  2) portable fsot_mc/universe_atlas.json (core-only fallback)

free_parameters = 0 — D_eff from navigator scientific metadata;
delta_psi inherited from routed core fold (preregistered), not fitted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.fast import ScalarInputF, compute_scalar_fast
from fsot_mc.paths import PACKAGE_ROOT

BUNDLE = PACKAGE_ROOT / "vendor" / "archive_bundle"
CORE_ATLAS = Path(__file__).resolve().parent / "universe_atlas.json"
OUT_FULL = Path(__file__).resolve().parent / "full_atlas.json"

# Core name aliases when extension routes_to_core uses different labels
_CORE_ALIASES = {
    "Computer_Science": "Quantum_Computing",  # nearest core CS-like fold
    "Finance": "Economics",
    "Finance_Markets": "Economics",
    "Medical": "Biochemistry",
    "Medicine": "Biochemistry",
    "Earth_Science": "Geophysics",
    "Climate": "Meteorology",
    "Climate_Science": "Meteorology",
    "Materials": "Materials_Science",
    "Energy": "Thermodynamics",
    "Space": "Astronomy",
    "Physics": "Physical_Chemistry",
}

# Explicit D_eff fallbacks for navigator rows with null scientific.D_eff
_DEFF_FALLBACK = {
    "Climate_Science": 17,
    "Cosmology_Extended": 25,
    "Particle_Physics": 5,
}


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _navigator_path() -> Path | None:
    p = BUNDLE / "data__fsot_domain_navigator.json"
    return p if p.is_file() else None


def _fixtures_path() -> Path | None:
    p = BUNDLE / "data__fsot_domain_scalar_fixtures.json"
    return p if p.is_file() else None


def load_core_atlas() -> dict[str, Any]:
    raw = _load_json(CORE_ATLAS)
    if not isinstance(raw, dict):
        raise FileNotFoundError(f"Missing core atlas: {CORE_ATLAS}")
    return raw


def _resolve_core_route(routes_to_core: str | None, core_domains: dict[str, Any]) -> str | None:
    if not routes_to_core:
        return None
    if routes_to_core in core_domains:
        return routes_to_core
    alias = _CORE_ALIASES.get(routes_to_core)
    if alias and alias in core_domains:
        return alias
    # fuzzy: case-insensitive
    lower = {k.lower(): k for k in core_domains}
    if routes_to_core.lower() in lower:
        return lower[routes_to_core.lower()]
    return None


def _hits_for_deff(d_eff: int) -> int:
    """Preregistered hit ladder by scale (mirrors core table spirit, not a fit)."""
    if d_eff <= 11:
        return 0
    if d_eff <= 16:
        return 1
    if d_eff <= 20:
        return 2
    return 3


def build_full_atlas(*, write: bool = True) -> dict[str, Any]:
    core_raw = load_core_atlas()
    core_domains: dict[str, Any] = {
        name: dict(meta) for name, meta in (core_raw.get("domains") or {}).items()
    }

    # Overlay fixture scalars if present (authoritative numeric)
    fix_path = _fixtures_path()
    if fix_path:
        fix = _load_json(fix_path) or {}
        for row in fix.get("domains") or []:
            name = row.get("name")
            if name in core_domains and row.get("python_scalar") is not None:
                core_domains[name]["S_canonical"] = float(row["python_scalar"])
                core_domains[name]["regime"] = (
                    "emergence" if float(row["python_scalar"]) > 0 else "dispersal"
                )

    extensions: dict[str, Any] = {}
    nav_path = _navigator_path()
    nav_meta: dict[str, Any] = {}
    if nav_path:
        nav = _load_json(nav_path) or {}
        nav_meta = {
            "generated_at": nav.get("generated_at"),
            "version": nav.get("version"),
            "summary": nav.get("summary"),
            "source": str(nav_path),
        }
        for panel in nav.get("extension_panels") or []:
            pname = panel.get("panel") or panel.get("name")
            if not pname:
                continue
            sci = panel.get("scientific") or {}
            d_eff = sci.get("D_eff")
            if d_eff is None:
                d_eff = _DEFF_FALLBACK.get(pname)
            if d_eff is None:
                # inherit from core route
                route = _resolve_core_route(panel.get("routes_to_core"), core_domains)
                d_eff = core_domains[route]["D_eff"] if route else 18
            d_eff = int(d_eff)

            route_name = _resolve_core_route(panel.get("routes_to_core"), core_domains)
            if route_name:
                base_dp = float(core_domains[route_name]["delta_psi"])
                base_obs = bool(core_domains[route_name]["observed"])
            else:
                # Cosmology-like if high D_eff else mid-scale default from seeds ladder
                base_dp = 1.0 if d_eff >= 22 else (0.7 if d_eff >= 14 else 0.5)
                base_obs = True

            hits = _hits_for_deff(d_eff)
            # Measured panels with records → observed True
            observed = True if (panel.get("record_count") or 0) > 0 else base_obs

            si = ScalarInputF(
                D_eff=float(d_eff),
                recent_hits=float(hits),
                delta_psi=base_dp,
                delta_theta=1.0,
                observed=observed,
            )
            S = float(compute_scalar_fast(si))

            # Avoid overwriting core folds when panel reuses a core name
            key = pname
            if key in core_domains:
                key = f"{pname}__Extension"

            extensions[key] = {
                "kind": "extension_panel",
                "panel": pname,
                "D_eff": d_eff,
                "hits": hits,
                "delta_psi": base_dp,
                "delta_theta": 1.0,
                "observed": observed,
                "S_canonical": S,
                "regime": "emergence" if S > 0 else "dispersal",
                "cluster": _cluster(d_eff),
                "routes_to_core": panel.get("routes_to_core"),
                "resolved_core": route_name,
                "tier": panel.get("tier"),
                "record_count": panel.get("record_count") or sci.get("record_count"),
                "median_error_pct": panel.get("median_error_pct")
                or sci.get("pooled_median_error_pct"),
                "coverage_tier": panel.get("coverage_tier") or sci.get("coverage_tier"),
                "lean_module": panel.get("lean_module"),
                "maps_to_lean": panel.get("maps_to_lean") or sci.get("maps_to_lean"),
                "tags": panel.get("tags") or [],
                "benchmark_path": (panel.get("download_bundle") or {}).get("benchmark_data")
                or sci.get("benchmark_path"),
            }

    # Mark core
    for name, meta in core_domains.items():
        meta["kind"] = "core"
        meta.setdefault("cluster", _cluster(int(meta["D_eff"])))

    all_domains = {**core_domains, **extensions}
    payload = {
        "version": "2.0",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "authority_sha256": core_raw.get("authority_sha256"),
        "free_parameters": 0,
        "purpose": "Full FSOT universe atlas — core folds + extension panels for MC discovery",
        "n_core": len(core_domains),
        "n_extension": len(extensions),
        "n_total": len(all_domains),
        "navigator": nav_meta,
        "S_cosm": core_raw.get("S_cosm"),
        "S_quant": core_raw.get("S_quant"),
        "wave1_anchors": core_raw.get("wave1_anchors"),
        "domains": all_domains,
        "core_names": sorted(core_domains.keys()),
        "extension_names": sorted(extensions.keys()),
    }
    if write:
        OUT_FULL.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _cluster(d_eff: int) -> str:
    if d_eff <= 7:
        return "quantum_particle"
    if d_eff <= 11:
        return "atomic_molecular_optical"
    if d_eff <= 15:
        return "life_matter_energy"
    if d_eff <= 19:
        return "earth_complex_systems"
    if d_eff <= 22:
        return "astro_planetary"
    return "cosmo_unification"


def ensure_full_atlas() -> dict[str, Any]:
    """Load full_atlas.json or build it."""
    if OUT_FULL.is_file():
        return json.loads(OUT_FULL.read_text(encoding="utf-8"))
    return build_full_atlas(write=True)


if __name__ == "__main__":
    a = build_full_atlas(write=True)
    print(
        f"full atlas: core={a['n_core']} ext={a['n_extension']} total={a['n_total']} → {OUT_FULL}"
    )
