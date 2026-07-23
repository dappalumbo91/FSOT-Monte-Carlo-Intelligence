"""
Multi-scale FSOT connective graph model.

Builds a living graph for the visual frontend:
  - seed hub (π, e, φ, γ, Catalan) → law K
  - domain folds as neurons (D_eff rings, cluster colors, S vitality)
  - adjacent + long-range bridges as axons
  - memory engrams + preregistered predictions as satellite nodes

Aesthetic intent: Obsidian second-brain graph × neural growth / connective tissue.
free_parameters = 0. Seeds never move.
"""

from __future__ import annotations

import math
from typing import Any

from fsot_mc.fast import PHI, POOF, K, PI, E, GAMMA, G_CAT
from fsot_mc.universe_atlas import (
    core_names,
    domains_by_cluster,
    evaluate_domain,
    get_domain,
)
from fsot_mc.universe_mc import run_universe_monte_carlo

SEED_PHI = float(PHI)
SEED_POOF = float(POOF)

# Cluster → hue for frontend (CSS-friendly) — kept for legend / backward compat
CLUSTER_COLORS: dict[str, str] = {
    "quantum_particle": "#7c5cff",
    "atomic_molecular_optical": "#3ecf8e",
    "life_matter_energy": "#ff6b9d",
    "earth_complex_systems": "#f0b429",
    "astro_planetary": "#4cc9f0",
    "cosmo_unification": "#ff8c42",
    "extension": "#5b6b8a",
    "problem_route": "#f472b6",
    "unknown": "#8892a4",
    "seed": "#ffffff",
    "law": "#c4b5fd",
    "memory": "#94a3b8",
    "prediction": "#fbbf24",
    "bridge": "#67e8f9",
    "routes_to_core": "#a3e635",
    "coupling": "#22d3ee",
    "validation": "#34d399",
}

# Scientific cluster keys used for NeuroLab + panel coloring
SCIENCE_CLUSTERS: tuple[str, ...] = (
    "quantum_particle",
    "atomic_molecular_optical",
    "life_matter_energy",
    "earth_complex_systems",
    "astro_planetary",
    "cosmo_unification",
)

# ── As Above, So Below color doctrine ─────────────────────────────────────
# Same *physics spine* → same hue family (shared law across scales).
# D_eff dimensional interface → ring (layout) + lightness (depth in that spine).
# Low D_eff = micro/bright; high D_eff = macro/deep. Seeds never move.

PHYSICS_SPINE_HUE: dict[str, float] = {
    # degrees on the color wheel
    "particle_quantum": 265.0,  # violet — particle / QM / nuclear
    "atomic_optical": 155.0,  # teal-green — AMO / spectroscopy
    "matter_energy": 340.0,  # rose — materials / chem / fluid / energy
    "life_mind": 320.0,  # magenta — bio / neural / consciousness
    "earth_complex": 42.0,  # gold — earth systems / ecology / socio
    "astro_structure": 195.0,  # cyan — stars / planets / galaxies
    "cosmo_unification": 24.0,  # orange — cosmology / BH / CMB / QG
    "formal_math": 210.0,  # steel-blue — formal priors / pure math
    "problem_route": 330.0,
    "seed": 0.0,
    "law": 270.0,
    "prediction": 45.0,
    "memory": 210.0,
    "unknown": 220.0,
}

# maps_to_lean / routes / name cues → physics spine (As Above So Below kinship)
_SPINE_TAG_MAP: list[tuple[str, tuple[str, ...]]] = [
    ("particle_quantum", ("particle", "quantum", "nuclear", "higgs", "muon", "lepton", "hadron", "electron", "plasma", "fusion")),
    ("atomic_optical", ("atomic", "optical", "photon", "laser", "spectro", "acoustical", "acoustics")),
    ("matter_energy", ("material", "chemical", "energy", "fluid", "fuel", "thermo", "condensed")),
    ("life_mind", ("biological", "neural", "consciousness", "medical", "genetics", "codon", "bio", "neuro", "psychology")),
    ("earth_complex", ("ecological", "economic", "earth", "climate", "ocean", "seismo", "meteo", "socio", "ionosph")),
    ("astro_structure", ("astronomical", "galactic", "stellar", "planet", "solar", "astro")),
    ("cosmo_unification", ("cosmological", "blackhole", "cmb", "hubble", "dark", "inflation", "string", "quantum_gravity")),
    ("formal_math", ("mathematical", "ai", "formal", "lean", "linguistic", "computer")),
]

_CLUSTER_TO_SPINE: dict[str, str] = {
    "quantum_particle": "particle_quantum",
    "atomic_molecular_optical": "atomic_optical",
    "life_matter_energy": "matter_energy",  # refined further by lean tags when bio
    "earth_complex_systems": "earth_complex",
    "astro_planetary": "astro_structure",
    "cosmo_unification": "cosmo_unification",
}


def _hsl_to_hex(h: float, s: float, light: float) -> str:
    """h in [0,360), s,l in [0,1] → #rrggbb"""
    h = h % 360.0
    s = max(0.0, min(1.0, s))
    light = max(0.0, min(1.0, light))
    c = (1 - abs(2 * light - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = light - c / 2
    if h < 60:
        rp, gp, bp = c, x, 0.0
    elif h < 120:
        rp, gp, bp = x, c, 0.0
    elif h < 180:
        rp, gp, bp = 0.0, c, x
    elif h < 240:
        rp, gp, bp = 0.0, x, c
    elif h < 300:
        rp, gp, bp = x, 0.0, c
    else:
        rp, gp, bp = c, 0.0, x
    r, g, b = int((rp + m) * 255), int((gp + m) * 255), int((bp + m) * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def _blend_hex(hex_color: str, toward: str = "#1a2230", t: float = 0.35) -> str:
    """Blend hex toward a dark slate (mute extensions without losing family hue)."""

    def _rgb(h: str) -> tuple[int, int, int]:
        h = (h or "#8892a4").lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        try:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        except ValueError:
            return 136, 146, 164

    r1, g1, b1 = _rgb(hex_color)
    r2, g2, b2 = _rgb(toward)
    t = max(0.0, min(1.0, float(t)))
    r = int(r1 * (1 - t) + r2 * t)
    g = int(g1 * (1 - t) + g2 * t)
    b = int(b1 * (1 - t) + b2 * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _resolve_cluster(n: dict[str, Any]) -> str:
    """Prefer scientific cluster over the generic 'extension' group label."""
    for key in ("cluster", "group"):
        c = str(n.get(key) or "").strip()
        if c and c not in ("extension", "unknown", ""):
            return c
    return "extension"


def resolve_physics_spine(n: dict[str, Any]) -> str:
    """
    Physics kinship for As Above, So Below coloring.
    Same spine ⇒ same hue; D_eff places the node on the dimensional interface.
    """
    kind = n.get("kind") or ""
    if kind == "problem_route":
        return "problem_route"
    if kind == "seed":
        return "seed"
    if kind == "law":
        return "law"
    if kind == "prediction":
        return "prediction"
    if kind == "memory":
        return "memory"

    blob_parts: list[str] = []
    for t in n.get("maps_to_lean") or []:
        blob_parts.append(str(t).lower())
    for t in n.get("tags") or []:
        blob_parts.append(str(t).lower())
    blob_parts.append(str(n.get("routes_to_core") or "").lower())
    blob_parts.append(str(n.get("domain") or n.get("label") or "").lower().replace("_", " "))
    blob_parts.append(str(n.get("lean_module") or "").lower())
    blob = " ".join(blob_parts)

    # life_matter cluster is dual: bio vs materials
    cluster = _resolve_cluster(n)
    if cluster == "life_matter_energy":
        if any(k in blob for k in ("bio", "neuro", "conscious", "medical", "gene", "codon", "psych", "life")):
            return "life_mind"
        if any(k in blob for k in ("material", "chem", "fluid", "energy", "fuel", "thermo")):
            return "matter_energy"

    for spine, keys in _SPINE_TAG_MAP:
        if any(k in blob for k in keys):
            return spine

    if cluster in _CLUSTER_TO_SPINE:
        return _CLUSTER_TO_SPINE[cluster]
    return "unknown"


def scale_band(d_eff: float | int | None) -> str:
    """Dimensional interface band (As Above So Below ladder)."""
    try:
        d = float(d_eff if d_eff is not None else 12)
    except (TypeError, ValueError):
        d = 12.0
    if d <= 8:
        return "micro"  # particle / atomic interface
    if d <= 16:
        return "meso"  # life / earth / lab scale
    return "macro"  # astro / cosmo interface


def color_as_above_so_below(
    *,
    spine: str,
    d_eff: float | int | None,
    is_core: bool = False,
    is_extension: bool = False,
) -> dict[str, Any]:
    """
    Hue  = physics spine (shared law / kinship)
    Light = D_eff (micro bright → macro deep)
    Sat   = slightly lower for extensions
    """
    hue = PHYSICS_SPINE_HUE.get(spine, PHYSICS_SPINE_HUE["unknown"])
    try:
        d = float(d_eff if d_eff is not None else 12.0)
    except (TypeError, ValueError):
        d = 12.0
    # normalize D_eff ~1..25 → t in 0..1
    t = max(0.0, min(1.0, (d - 1.0) / 24.0))
    # micro: light ~0.62; macro: light ~0.38 (still visible on dark UI)
    light = 0.62 - 0.24 * t
    sat = 0.72 if is_core else (0.55 if is_extension else 0.65)
    if spine in ("seed", "law"):
        sat, light = 0.15, 0.92
    if spine == "prediction":
        sat, light = 0.78, 0.55
    hex_c = _hsl_to_hex(hue, sat, light)
    return {
        "color": hex_c,
        "physics_spine": spine,
        "scale_band": scale_band(d),
        "hue": hue,
        "lightness": light,
        "saturation": sat,
        "D_eff": d,
    }


LAYER_EDGE_COLORS: dict[str, str] = {
    "routes_to_core": "rgba(163,230,53,0.55)",
    "navigator_route": "rgba(163,230,53,0.4)",
    "navigator_membership": "rgba(163,230,53,0.25)",
    "problem_intent": "rgba(244,114,182,0.65)",
    "archive_coupling": "rgba(34,211,238,0.75)",
    "archive_lean_overlap": "rgba(34,211,238,0.22)",
    "ladder": "rgba(103,232,249,0.45)",
    "long_range": "rgba(103,232,249,0.7)",
    "cluster": "rgba(167,139,250,0.35)",
    "law_to_domain": "rgba(196,181,253,0.12)",
    "seed_to_law": "rgba(255,255,255,0.7)",
    "memory_link": "rgba(148,163,184,0.45)",
    "prediction_link": "rgba(251,191,36,0.45)",
}


def _seed_nodes() -> list[dict[str, Any]]:
    seeds = [
        ("seed_pi", "π", float(PI), "transcendental circle / phase"),
        ("seed_e", "e", float(E), "growth / natural base"),
        ("seed_phi", "φ", float(PHI), "golden self-similarity"),
        ("seed_gamma", "γ", float(GAMMA), "Euler–Mascheroni / harmonic"),
        ("seed_catalan", "G", float(G_CAT), "Catalan / acoustic bleed"),
    ]
    nodes = []
    for i, (nid, label, val, role) in enumerate(seeds):
        nodes.append(
            {
                "id": nid,
                "label": label,
                "kind": "seed",
                "value": val,
                "role": role,
                "group": "seed",
                "color": CLUSTER_COLORS["seed"],
                "size": 18,
                "D_eff": 0,
                "S": None,
                "ring": 0,
                "angle": (2 * math.pi * i) / len(seeds),
            }
        )
    nodes.append(
        {
            "id": "law_K",
            "label": "K",
            "kind": "law",
            "value": float(K),
            "role": "S = K·(T1+T2+T3)",
            "group": "law",
            "color": CLUSTER_COLORS["law"],
            "size": 22,
            "D_eff": 0,
            "S": None,
            "ring": 0,
            "angle": 0.0,
            "formula": "S=K*(T1+T2+T3)",
        }
    )
    return nodes


def _seed_edges() -> list[dict[str, Any]]:
    edges = []
    for sid in ("seed_pi", "seed_e", "seed_phi", "seed_gamma", "seed_catalan"):
        edges.append(
            {
                "id": f"{sid}->law_K",
                "source": sid,
                "target": "law_K",
                "kind": "seed_to_law",
                "strength": 1.0,
                "color": CLUSTER_COLORS["law"],
                "animated": True,
            }
        )
    return edges


def build_domain_nodes(*, scope: str = "core", mc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    names = core_names() if scope != "full" else list(
        __import__("fsot_mc.universe_atlas", fromlist=["domain_names"]).domain_names()
    )
    # Cap full atlas for viz performance
    if scope == "full" and len(names) > 120:
        names = core_names() + [n for n in names if n not in set(core_names())][:85]

    de = (mc or {}).get("domain_ensemble") or {}
    nodes = []
    # group by D_eff for classic multi-scale ring shells
    by_d: dict[int, list[str]] = {}
    for n in names:
        try:
            d = int(get_domain(n)["D_eff"])
        except KeyError:
            continue
        by_d.setdefault(d, []).append(n)

    for D, group in sorted(by_d.items()):
        # Build rows first so we can order each shell by physics spine then S
        rows: list[dict[str, Any]] = []
        for name in group:
            try:
                base = get_domain(name)
                e = evaluate_domain(name)
                S_can = float(e["S"])
                flip = 0.0
                S_path = None
                if name in de:
                    S_path = float(de[name].get("S_path_mean", S_can))
                    flip = float(de[name].get("flip_rate") or 0)
                cluster = base.get("cluster") or "unknown"
                draft = {
                    "domain": name,
                    "label": name.replace("_", " "),
                    "kind": "domain",
                    "cluster": cluster,
                    "maps_to_lean": base.get("maps_to_lean") or [],
                    "tags": base.get("tags") or [],
                    "routes_to_core": base.get("routes_to_core"),
                    "is_core": True,
                    "D_eff": D,
                }
                spine = resolve_physics_spine(draft)
                paint = color_as_above_so_below(spine=spine, d_eff=D, is_core=True)
                size = 6 + min(16, abs(S_can) * 14)
                rows.append(
                    {
                        "id": f"dom_{name}",
                        "label": name.replace("_", " "),
                        "domain": name,
                        "kind": "domain",
                        "group": spine,
                        "color": paint["color"],
                        "size": float(size),
                        "D_eff": D,
                        "S": S_can,
                        "S_canonical": S_can,
                        "S_path_mean": S_path,
                        "regime": "emergence" if S_can > 0 else "dispersal",
                        "flip_rate": flip,
                        "ring": max(1, min(6, int(1 + D / 5))),
                        "cluster": cluster,
                        "physics_spine": spine,
                        "scale_band": paint["scale_band"],
                        "color_family": spine,
                        "is_core": True,
                        "layout_mode": "deff_ring_physics_sectors",
                    }
                )
            except Exception:
                continue
        for row in rows:
            nodes.append(row)
    # Sector-pack each D_eff shell (physics pie wedges)
    return reassign_ring_angles_by_s(nodes)


def build_domain_edges(
    domain_nodes: list[dict[str, Any]],
    mc: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Ladder neighbors + long-range bridges + law→domain axons."""
    edges: list[dict[str, Any]] = []
    # Law feeds every domain (propagation from seeds)
    for n in domain_nodes:
        edges.append(
            {
                "id": f"law_K->{n['id']}",
                "source": "law_K",
                "target": n["id"],
                "kind": "law_to_domain",
                "strength": 0.15 + min(0.5, abs(float(n.get("S") or 0)) * 0.3),
                "color": "rgba(196,181,253,0.25)",
                "animated": False,
            }
        )

    # D_eff ladder: connect consecutive domains on sorted ladder
    ladder = sorted(domain_nodes, key=lambda x: (x.get("D_eff") or 0, x.get("label") or ""))
    for a, b in zip(ladder, ladder[1:]):
        da, db = int(a["D_eff"]), int(b["D_eff"])
        if abs(da - db) <= 3:
            edges.append(
                {
                    "id": f"{a['id']}-{b['id']}-ladder",
                    "source": a["id"],
                    "target": b["id"],
                    "kind": "ladder",
                    "strength": 0.45 / (1 + abs(da - db)),
                    "color": "rgba(103,232,249,0.45)",
                    "animated": True,
                }
            )

    # Same-cluster connectivity (neural local neighborhood)
    by_cl: dict[str, list[dict[str, Any]]] = {}
    for n in domain_nodes:
        by_cl.setdefault(n.get("cluster") or "unknown", []).append(n)
    for cl, group in by_cl.items():
        g = sorted(group, key=lambda x: x.get("D_eff") or 0)
        for a, b in zip(g, g[1:]):
            edges.append(
                {
                    "id": f"{a['id']}-{b['id']}-cluster",
                    "source": a["id"],
                    "target": b["id"],
                    "kind": "cluster",
                    "strength": 0.55,
                    "color": CLUSTER_COLORS.get(cl, CLUSTER_COLORS["unknown"]),
                    "animated": True,
                }
            )

    # Long-range bridges from MC
    lr = (mc or {}).get("long_range_bridges") or {}
    if isinstance(lr, dict):
        items = lr.items()
    else:
        items = []
    for key, payload in items:
        if not isinstance(payload, dict):
            continue
        a = payload.get("a")
        b = payload.get("b")
        st = payload.get("strength") or {}
        strength = abs(float(st.get("mean") if isinstance(st, dict) else st or 0.3))
        if not a or not b:
            continue
        edges.append(
            {
                "id": f"bridge_{a}_{b}",
                "source": f"dom_{a}",
                "target": f"dom_{b}",
                "kind": "long_range",
                "strength": min(1.0, strength + SEED_POOF),
                "color": CLUSTER_COLORS["bridge"],
                "animated": True,
                "label": f"{a}↔{b}",
            }
        )

    # Canonical As Above bridges if MC empty
    if not any(e["kind"] == "long_range" for e in edges):
        for a, b in (
            ("Biology", "Cosmology"),
            ("Quantum_Mechanics", "Cosmology"),
            ("Quantum_Mechanics", "Biology"),
            ("Neuroscience", "Cosmology"),
            ("Chemistry", "Biology"),
        ):
            if any(n.get("domain") == a for n in domain_nodes) and any(
                n.get("domain") == b for n in domain_nodes
            ):
                edges.append(
                    {
                        "id": f"bridge_{a}_{b}",
                        "source": f"dom_{a}",
                        "target": f"dom_{b}",
                        "kind": "long_range",
                        "strength": 0.7,
                        "color": CLUSTER_COLORS["bridge"],
                        "animated": True,
                        "label": f"{a}↔{b}",
                    }
                )
    return edges


def build_memory_nodes() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from fsot_mc.adaptive_memory import AdaptiveMemory

    mem = AdaptiveMemory()
    nodes, edges = [], []
    solid = [e for e in mem.ltm.values() if e.solidified or e.strength > SEED_POOF]
    solid = sorted(solid, key=lambda e: -e.strength)[:40]
    for i, e in enumerate(solid):
        nid = f"mem_{e.key[:12]}"
        nodes.append(
            {
                "id": nid,
                "label": (e.text[:28] + "…") if len(e.text) > 28 else e.text,
                "kind": "memory",
                "group": "memory",
                "color": CLUSTER_COLORS["memory"],
                "size": 5 + e.strength * 10,
                "D_eff": 12,
                "S": e.acc_phi,
                "ring": 7,
                "angle": (2 * math.pi * i) / max(len(solid), 1),
                "solidified": e.solidified,
                "source": e.source,
                "full_text": e.text[:300],
            }
        )
        # attach to first domain tag or law
        if e.domains:
            edges.append(
                {
                    "id": f"{nid}->{e.domains[0]}",
                    "source": nid,
                    "target": f"dom_{e.domains[0]}",
                    "kind": "memory_link",
                    "strength": 0.35 + e.strength * 0.4,
                    "color": "rgba(148,163,184,0.5)",
                    "animated": True,
                }
            )
        else:
            edges.append(
                {
                    "id": f"{nid}->law",
                    "source": nid,
                    "target": "law_K",
                    "kind": "memory_link",
                    "strength": 0.25,
                    "color": "rgba(148,163,184,0.4)",
                    "animated": False,
                }
            )
    return nodes, edges


def build_prediction_nodes() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from fsot_mc.archive_predictions import load_preregistered_predictions

    preds = load_preregistered_predictions()[:30]
    nodes, edges = [], []
    for i, p in enumerate(preds):
        pid = str(p.get("id") or f"P{i}")
        nid = f"pred_{pid}"
        dom = str(p.get("domain") or "")
        nodes.append(
            {
                "id": nid,
                "label": pid,
                "kind": "prediction",
                "group": "prediction",
                "color": CLUSTER_COLORS["prediction"],
                "size": 7,
                "D_eff": 10,
                "S": None,
                "ring": 8,
                "angle": (2 * math.pi * i) / max(len(preds), 1),
                "name": p.get("name"),
                "domain": dom,
                "fsot_predicted": p.get("fsot_predicted"),
                "unit": p.get("unit"),
            }
        )
        # link to matching domain if present in core names
        core = set(core_names())
        # fuzzy: if domain name contains a core token
        target = None
        for c in core:
            if c.lower() in dom.lower() or dom.lower() in c.lower():
                target = f"dom_{c}"
                break
        if target is None and "Fuel" in dom:
            target = "dom_Chemistry" if "Chemistry" in core else "law_K"
        if target is None:
            target = "law_K"
        edges.append(
            {
                "id": f"{nid}->{target}",
                "source": nid,
                "target": target,
                "kind": "prediction_link",
                "strength": 0.4,
                "color": "rgba(251,191,36,0.45)",
                "animated": False,
            }
        )
    return nodes, edges


# Fixed pie sectors around each D_eff shell — cosmology-style "lanes"
# (micro→macro expansion keeps the same azimuthal family).
SPINE_SECTOR_ORDER: tuple[str, ...] = (
    "particle_quantum",
    "atomic_optical",
    "matter_energy",
    "life_mind",
    "earth_complex",
    "astro_structure",
    "cosmo_unification",
    "formal_math",
    "problem_route",
    "unknown",
)


def _s_sort_key(n: dict[str, Any]) -> tuple:
    """
    Order within a D_eff ring (dimensional shell):
      1) physics spine (As Above So Below kinship clump)
      2) cores before extensions
      3) signed S (vitality)
      4) name
    """
    spine = str(n.get("physics_spine") or resolve_physics_spine(n))
    try:
        spine_i = SPINE_SECTOR_ORDER.index(spine)
    except ValueError:
        spine_i = len(SPINE_SECTOR_ORDER) - 1
    is_core = 0 if (n.get("is_core") or n.get("atlas_kind") == "core") else 1
    s = float(n["S"]) if n.get("S") is not None else 0.0
    name = str(n.get("domain") or n.get("label") or n.get("id") or "")
    return (spine_i, is_core, s, name)


def _assign_sector_angles(group: list[dict[str, Any]], *, ring: int = 0) -> None:
    """
    Pack nodes into physics-spine pie wedges with small gaps (less visual soup).

    Cosmology metaphor: same physics keeps a constant sky longitude while
    D_eff / ring is the expansion radius (Hubble-flow shells).
    """
    if not group:
        return
    # preserve sort
    ordered = sorted(group, key=_s_sort_key)
    # count per spine
    buckets: dict[str, list[dict[str, Any]]] = {}
    for n in ordered:
        sp = str(n.get("physics_spine") or resolve_physics_spine(n))
        n["physics_spine"] = sp
        buckets.setdefault(sp, []).append(n)

    active = [sp for sp in SPINE_SECTOR_ORDER if buckets.get(sp)]
    # also any unknown spines
    for sp in buckets:
        if sp not in active:
            active.append(sp)
    if not active:
        return

    n_sec = len(active)
    gap = 0.07  # radians gap between sectors (~4°)
    usable = 2 * math.pi - gap * n_sec
    # weight sector width by sqrt(count) so big families don't dominate entirely
    weights = [max(1.0, math.sqrt(len(buckets[sp]))) for sp in active]
    wsum = sum(weights) or 1.0
    cursor = -math.pi / 2 + ring * 0.03  # slight ring twist for depth reading
    for sp, w in zip(active, weights):
        width = usable * (w / wsum)
        members = buckets[sp]
        m = len(members)
        for i, n in enumerate(members):
            # pack inside sector with small inner padding
            pad = width * 0.08
            inner = max(width - 2 * pad, 1e-6)
            frac = (i + 0.5) / max(m, 1)
            n["angle"] = cursor + pad + frac * inner
            n["sector"] = sp
            n["sector_index"] = active.index(sp)
        cursor += width + gap


def _style_archive_nodes(archive_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Classic multi-scale layout + As Above So Below color doctrine:

      ring  = f(D_eff) shells — dimensional interface around law K
      angle = physics spine clumps, then signed S on each shell
      color = physics spine hue; lightness tracks D_eff (micro→macro)

    Green-gate is a status badge, not a gray color wipe.
    """
    by_ring: dict[int, list[dict[str, Any]]] = {}
    out = []
    for n in archive_nodes:
        ring = int(n.get("ring") or max(1, min(8, int(1 + int(n.get("D_eff") or 12) / 4))))
        n = dict(n)
        n["ring"] = ring
        # pin signed canonical S for regime when present
        if n.get("S") is not None:
            try:
                n["S"] = float(n["S"])
                n["S_canonical"] = n.get("S_canonical", n["S"])
                n["regime"] = "emergence" if n["S"] > 0 else "dispersal"
            except (TypeError, ValueError):
                pass
        # physics kinship before sort/color
        spine = resolve_physics_spine(n)
        n["physics_spine"] = spine
        n["scale_band"] = scale_band(n.get("D_eff"))
        by_ring.setdefault(ring, []).append(n)
    for ring, group in by_ring.items():
        _assign_sector_angles(group, ring=int(ring))
        for n in group:
            kind = n.get("kind") or "domain"
            is_core = bool(n.get("is_core") or n.get("atlas_kind") == "core")
            is_ext = (not is_core) and (
                kind == "extension" or n.get("atlas_kind") == "extension_panel"
            )
            cluster = _resolve_cluster(n)
            n["cluster"] = cluster
            spine = n.get("physics_spine") or resolve_physics_spine(n)
            n["physics_spine"] = spine
            # group for UI = physics spine (As Above So Below)
            if kind == "problem_route":
                n["group"] = "problem_route"
            else:
                n["group"] = spine

            paint = color_as_above_so_below(
                spine=spine,
                d_eff=n.get("D_eff"),
                is_core=is_core or kind == "domain",
                is_extension=is_ext,
            )
            if kind == "problem_route":
                color = CLUSTER_COLORS["problem_route"]
                size = 10
            else:
                color = paint["color"]
                if is_core or kind == "domain":
                    size = 6 + min(14, abs(float(n["S"])) * 12) if n.get("S") is not None else 10
                elif is_ext:
                    size = 4 + min(8, (abs(float(n["S"])) * 8) if n.get("S") is not None else 3)
                else:
                    size = 6 + min(14, abs(float(n["S"])) * 12) if n.get("S") is not None else 8

            # Green gate is a *status badge*, not a color wipe to gray
            err = n.get("median_error_pct")
            green = err is not None and float(err) <= 0.5
            n["green_gate"] = bool(green)
            n["color"] = color
            n["size"] = float(size)
            n["color_family"] = spine
            n["scale_band"] = paint.get("scale_band")
            n["layout_mode"] = "deff_ring_physics_sectors"
            out.append(n)
    return out


def reassign_ring_angles_by_s(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """After S updates, re-pack each D_eff ring into physics pie sectors."""
    by_ring: dict[int, list[dict[str, Any]]] = {}
    for n in nodes:
        if n.get("kind") in ("seed", "law", "memory", "prediction"):
            continue
        if not n.get("physics_spine"):
            n["physics_spine"] = resolve_physics_spine(n)
        ring = int(n.get("ring") or max(1, min(8, int(1 + int(n.get("D_eff") or 12) / 4))))
        n["ring"] = ring
        by_ring.setdefault(ring, []).append(n)
    for ring, group in by_ring.items():
        _assign_sector_angles(group, ring=int(ring))
        for n in group:
            n["layout_mode"] = "deff_ring_physics_sectors"
    return nodes


def _style_archive_edges(archive_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for e in archive_edges:
        e = dict(e)
        layer = e.get("layer") or e.get("kind") or ""
        e["color"] = LAYER_EDGE_COLORS.get(layer) or LAYER_EDGE_COLORS.get(e.get("kind") or "") or CLUSTER_COLORS["coupling"]
        e["animated"] = e.get("kind") not in ("by_core_membership",) and "lean_overlap" not in str(e.get("kind"))
        # soften membership edges
        if e.get("kind") == "by_core_membership":
            e["strength"] = min(float(e.get("strength") or 0.4), 0.35)
        out.append(e)
    return out


def build_universe_graph(
    *,
    n_paths: int = 48,
    seed: int = 0,
    scope: str = "full",
    with_memory: bool = True,
    with_predictions: bool = True,
    with_mc: bool = True,
    with_archive_connective: bool = True,
    force_rebuild_connective: bool = False,
) -> dict[str, Any]:
    """
    Multi-scale connective graph for the visual frontend.

    scope:
      - core: 35 NeuroLab folds only (light)
      - full: full archive connective tissue (402+ domains, routes, couplings)
    """
    mc = None
    if with_mc and scope == "core":
        mc = run_universe_monte_carlo(
            n_paths=n_paths,
            seed=seed,
            store_paths=min(8, n_paths),
            train_pathway_memory=False,
        )
        if mc.get("error"):
            mc = None
    elif with_mc and scope == "full":
        # multipath on core only (performance); S overlay for core nodes
        mc = run_universe_monte_carlo(
            n_paths=min(n_paths, 32),
            seed=seed,
            store_paths=min(6, n_paths),
            train_pathway_memory=False,
        )
        if mc.get("error"):
            mc = None

    seeds = _seed_nodes()
    seed_edges = _seed_edges()

    archive_meta: dict[str, Any] = {}
    if with_archive_connective and scope == "full":
        from fsot_mc.archive_connective import get_connective_tissue

        tissue = get_connective_tissue(force_rebuild=force_rebuild_connective)
        archive_meta = {
            "n_archive_nodes": tissue.get("n_nodes"),
            "n_archive_edges": tissue.get("n_edges"),
            "n_core": tissue.get("n_core"),
            "n_extension": tissue.get("n_extension"),
            "n_problem_routes": tissue.get("n_problem_routes"),
            "n_with_error": tissue.get("n_with_error"),
            "n_green_gate": tissue.get("n_green_gate"),
            "edge_type_counts": tissue.get("edge_type_counts"),
            "coupling_raw_edge_count": tissue.get("coupling_raw_edge_count"),
            "coupling_raw_node_count": tissue.get("coupling_raw_node_count"),
            "expansion_summary": tissue.get("expansion_summary"),
            "source": tissue.get("source"),
        }
        domains = _style_archive_nodes(tissue.get("nodes") or [])
        # Multipath path-mean is observer diagnostic only — do not drive geometry.
        # Keep signed canonical S for ring ordering + regime colors.
        de = (mc or {}).get("domain_ensemble") or {}
        for n in domains:
            dom = n.get("domain")
            if not dom:
                continue
            try:
                if n.get("is_core") or n.get("atlas_kind") == "core" or n.get("kind") == "domain":
                    ev = evaluate_domain(str(dom))
                    n["S"] = float(ev["S"])
                    n["S_canonical"] = float(ev["S"])
                    n["D_eff"] = int(ev.get("D_eff") or n.get("D_eff") or 12)
                    n["regime"] = "emergence" if n["S"] > 0 else "dispersal"
                    n["ring"] = max(1, min(8, int(1 + int(n["D_eff"]) / 4)))
            except Exception:
                pass
            if dom in de:
                n["S_path_mean"] = float(de[dom].get("S_path_mean", n.get("S") or 0))
                n["flip_rate"] = de[dom].get("flip_rate")
            if n.get("is_core") and n.get("S") is not None:
                n["size"] = 6 + min(14, abs(float(n["S"])) * 12)
                # keep As Above So Below paint (physics spine + D_eff lightness)
                spine = n.get("physics_spine") or resolve_physics_spine(n)
                paint = color_as_above_so_below(
                    spine=spine,
                    d_eff=n.get("D_eff"),
                    is_core=True,
                )
                n["physics_spine"] = spine
                n["color"] = paint["color"]
                n["scale_band"] = paint["scale_band"]
                n["color_family"] = spine
                n["group"] = spine
        # Re-space shells by physics spine + S after canonical restore
        reassign_ring_angles_by_s(domains)
        # law → core only (not every extension — avoids visual washout)
        law_edges = []
        for n in domains:
            if n.get("is_core") or n.get("kind") == "domain":
                law_edges.append(
                    {
                        "id": f"law_K->{n['id']}",
                        "source": "law_K",
                        "target": n["id"],
                        "kind": "law_to_domain",
                        "layer": "law_to_domain",
                        "strength": 0.2,
                        "color": LAYER_EDGE_COLORS["law_to_domain"],
                        "animated": False,
                    }
                )
        dom_edges = law_edges + _style_archive_edges(tissue.get("edges") or [])
        # also add MC long-range bridges among core
        core_nodes = [n for n in domains if n.get("is_core")]
        dom_edges.extend(build_domain_edges(core_nodes, mc))
        # strip duplicate law edges from build_domain_edges for non-core-only list
        dom_edges = [e for e in dom_edges if not (e.get("kind") == "law_to_domain" and e.get("id", "").count("law_K") and False)]
    else:
        domains = build_domain_nodes(scope="core", mc=mc)
        dom_edges = build_domain_edges(domains, mc)

    mem_nodes, mem_edges = ([], [])
    if with_memory:
        mem_nodes, mem_edges = build_memory_nodes()

    pred_nodes, pred_edges = ([], [])
    if with_predictions:
        pred_nodes, pred_edges = build_prediction_nodes()

    nodes = seeds + domains + mem_nodes + pred_nodes
    edges = seed_edges + dom_edges + mem_edges + pred_edges

    # Filter edges whose endpoints exist; dedupe
    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]
    seen_e = set()
    deduped = []
    for e in edges:
        eid = e.get("id") or f"{e['source']}->{e['target']}:{e.get('kind')}"
        if eid in seen_e:
            continue
        seen_e.add(eid)
        e["id"] = eid
        if "color" not in e:
            e["color"] = LAYER_EDGE_COLORS.get(e.get("layer") or "", LAYER_EDGE_COLORS.get(e.get("kind") or "", "#67e8f9"))
        deduped.append(e)
    edges = deduped

    ens = (mc or {}).get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}

    n_core = sum(1 for n in nodes if n.get("is_core") or (n.get("kind") == "domain" and n.get("atlas_kind") != "extension_panel"))
    n_ext = sum(1 for n in nodes if n.get("kind") == "extension")
    n_pr = sum(1 for n in nodes if n.get("kind") == "problem_route")

    return {
        "error": None,
        "method": "fsot_universe_connective_graph",
        "free_parameters": 0,
        "authority": "D1D38A",
        "scope": scope,
        "aesthetic": "obsidian_second_brain_x_neural_growth_x_archive_connective",
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "n_paths": (mc or {}).get("n_paths"),
            "map_emergence_mean": ef.get("mean"),
            "n_domains": n_core + n_ext,
            "n_core_folds": n_core,
            "n_extension_panels": n_ext,
            "n_problem_routes": n_pr,
            "n_memory": len(mem_nodes),
            "n_predictions": len(pred_nodes),
            "clusters": domains_by_cluster(),
            "cluster_colors": CLUSTER_COLORS,
            "physics_spine_hues": PHYSICS_SPINE_HUE,
            "layer_edge_colors": LAYER_EDGE_COLORS,
            "archive_connective": archive_meta,
            "rings": {
                "0": "seeds (π e φ γ G) + law K — origin of expansion",
                "1-6": "D_eff shells — expansion radius (Hubble-flow style layers)",
                "layout": "ring=D_eff · pie sector=physics spine · within sector=S · color=spine+scale",
                "5": "problem-route intents (navigator)",
                "7": "memory engrams (LTM)",
                "8": "preregistered predictions",
            },
            "layout_mode": "deff_ring_physics_sectors",
            "color_doctrine": "as_above_so_below",
            "layers": [
                "seed_to_law",
                "law_to_domain",
                "routes_to_core",
                "problem_route",
                "coupling_crosswalk",
                "coupling_lean_overlap",
                "ladder / long_range MC bridges",
                "memory / prediction",
            ],
            "legend": [
                "Expansion metaphor: center = seeds/K · outer rings = higher D_eff",
                "Pie sectors = physics spines (same sky longitude across scales)",
                "As Above So Below: same hue family = same physics at every shell",
                "Bright axons = domain communication (law, routes_to_core, long-range)",
                "Violet particle · teal AMO · rose matter · magenta life · gold earth",
                "Cyan astro · orange cosmo · steel formal · lime routes · gold PREDs",
                "Dense lean-overlap mesh only when zoomed (keeps structure readable)",
            ],
        },
        "note": (
            "Full FSOT connective tissue from Physical Archive: domain coupling simulation, "
            "navigator routes, expansion map accuracy, multipath core overlay. Seeds never move."
        ),
    }
