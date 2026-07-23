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

# Cluster → hue for frontend (CSS-friendly)
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


# ── S–D_eff polar layout (FSOT law geometry) ──────────────────────────
# Radius driven by D_eff (complexity shells). Angle driven by signed S
# from the same SD / free_parameters=0 fold engine (not multipath path-mean).
S_LAYOUT_SPAN = 1.15  # |S| clamp for angular map (~atlas range)


def deff_to_radius(D: float | int | None, *, base: float = 55.0, step: float = 16.0) -> float:
    """Continuous radius from D_eff — low-D near law K, high-D outer."""
    d = float(D if D is not None else 12.0)
    d = max(0.0, min(32.0, d))
    return base + d * step


def s_to_angle(S: float | None, *, span: float = S_LAYOUT_SPAN) -> float:
    """
    Map signed canonical S → polar angle.

    S > 0 (emergence) → right / east half (about −π/2 … +π/2 around 0)
    S < 0 (dispersal) → left / west half
    S = 0 → north (π/2) gap edge

    Uses continuous map: θ = (S/span) * π   so +S → +π side, −S → −π side
    then rotate so emergence is to the RIGHT (0 = +x): θ' = −θ + 0.
    Final: θ = −(S/span)*π  with S=+span → θ=−π (left? wait)

    Desired: emergence RIGHT (+x), dispersal LEFT (−x).
      S = +span → θ = 0      (east)
      S = 0     → θ = π/2    (north) — mid
      S = −span → θ = π      (west)

    Linear: θ = π/2 * (1 − S/span) clamped, but that only covers 0..π.
    Full: θ = (π/2) − (S/span)*(π/2)  → S=+1 → 0, S=−1 → π.
    Extensions/outliers get small φ-jitter later.
    """
    if S is None:
        return math.pi / 2  # unknown → north
    s = max(-span, min(span, float(S)))
    # S=+span → 0 (east/emergence), S=−span → π (west/dispersal)
    return (math.pi / 2.0) * (1.0 - s / span)


def apply_sd_layout(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Assign layout_r / layout_angle / ring / angle from D_eff × signed S.

    Geometry is the ToE phase portrait:
      radial = D_eff shells
      angular = S fold sign (emergence ↔ dispersal)
    Multipath path-mean never drives geometry (stored separately as S_path_mean).
    """
    # Index cores by domain for extension inheritance
    core_by_domain: dict[str, dict[str, Any]] = {}
    for n in nodes:
        if n.get("is_core") or (
            n.get("kind") == "domain" and n.get("atlas_kind") not in ("extension_panel",)
            and n.get("domain")
            and n.get("S") is not None
        ):
            if n.get("domain"):
                core_by_domain[str(n["domain"])] = n

    # Collect S range from nodes that have real signed S
    signed = [
        float(n["S"])
        for n in nodes
        if n.get("S") is not None
        and n.get("kind") not in ("seed", "law", "memory", "prediction", "problem_route")
    ]
    span = S_LAYOUT_SPAN
    if signed:
        span = max(S_LAYOUT_SPAN, max(abs(min(signed)), abs(max(signed))) * 1.05)

    # cluster order for micro-jitter (stable, not random)
    cluster_order = {c: i for i, c in enumerate(sorted(CLUSTER_COLORS.keys()))}

    # pre-pass: resolve S_layout for every domain-like node
    for n in nodes:
        kind = n.get("kind") or ""
        if kind in ("seed", "law"):
            n["layout_r"] = 0.0 if kind == "law" else 28.0
            n["layout_angle"] = float(n.get("angle") or 0.0)
            n["ring"] = 0
            continue

        if kind == "memory":
            n["layout_r"] = deff_to_radius(26)
            n["layout_angle"] = float(n.get("angle") or 0.0)
            n["ring"] = 7
            continue

        if kind == "prediction":
            n["layout_r"] = deff_to_radius(28)
            n["layout_angle"] = float(n.get("angle") or 0.0)
            n["ring"] = 8
            continue

        if kind == "problem_route":
            n["layout_r"] = deff_to_radius(n.get("D_eff") or 14)
            # pin intents near their core's S angle if known
            cdom = n.get("core_domain")
            parent = core_by_domain.get(str(cdom)) if cdom else None
            if parent and parent.get("S") is not None:
                base_ang = s_to_angle(float(parent["S"]), span=span)
            else:
                base_ang = float(n.get("angle") or 0.0)
            n["layout_angle"] = base_ang + 0.12
            n["ring"] = 5
            n["angle"] = n["layout_angle"]
            continue

        # domains / extensions — treat is_core as core even if kind mislabeled
        is_core = bool(n.get("is_core") or n.get("atlas_kind") == "core")
        D = n.get("D_eff")
        S = n.get("S")
        # extensions: inherit S angle from routes_to_core parent when own S missing
        if S is None and n.get("routes_to_core"):
            parent = core_by_domain.get(str(n["routes_to_core"]))
            if parent and parent.get("S") is not None:
                S = float(parent["S"])
                n["S_inherited"] = True
                n["S_layout"] = S
        if S is not None:
            n["S_layout"] = float(S)
        else:
            n["S_layout"] = None

        r = deff_to_radius(D)
        # true extension panels sit slightly outward; cores stay on D shell
        if (not is_core) and (kind == "extension" or n.get("atlas_kind") == "extension_panel"):
            r += 22.0

        ang = s_to_angle(n.get("S_layout"), span=span)
        # micro-jitter by cluster + label so same-S nodes don't stack
        cl = str(n.get("cluster") or n.get("group") or "")
        ci = cluster_order.get(cl, 0)
        name = str(n.get("domain") or n.get("label") or n.get("id") or "")
        jitter = (ci * 0.035) + ((hash(name) % 1000) / 1000.0 - 0.5) * 0.06
        # mild golden spiral by D so shells aren't perfect circles of collisions
        ang = ang + jitter + (float(D or 12) * SEED_PHI % 1.0) * 0.04

        n["layout_r"] = r
        n["layout_angle"] = ang
        n["angle"] = ang
        # discrete ring for legend/HUD only (true geometry uses layout_r)
        n["ring"] = max(1, min(8, int(round((float(D or 12)) / 4.0))))
        n["layout_mode"] = "s_deff_polar"

    # second pass: tiny de-overlap only (must NOT destroy S→angle ordering)
    bins: dict[int, list[dict[str, Any]]] = {}
    for n in nodes:
        if n.get("kind") in ("seed", "law", "memory", "prediction"):
            continue
        if n.get("layout_r") is None:
            continue
        b = int(round(float(n["layout_r"]) / 30.0))
        bins.setdefault(b, []).append(n)
    for group in bins.values():
        if len(group) < 3:
            continue
        group.sort(
            key=lambda x: (
                float(x.get("S_layout") if x.get("S_layout") is not None else 0.0),
                str(x.get("domain") or x.get("label") or ""),
            )
        )
        n_g = len(group)
        # Cap total fan to ±0.12 rad so S hemispheres stay intact
        step = min(0.012, 0.24 / max(n_g, 1))
        mid = (n_g - 1) / 2.0
        for i, n in enumerate(group):
            primary = s_to_angle(
                float(n.get("S_layout") if n.get("S_layout") is not None else 0.0),
                span=span,
            )
            n["layout_angle"] = primary + (i - mid) * step
            n["angle"] = n["layout_angle"]

    return nodes


def layout_diagnostics(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Quick test report: how the graph organizes under D_eff and S."""
    domains = [
        n for n in nodes
        if n.get("kind") in ("domain", "extension") or n.get("is_core")
    ]
    cores = [n for n in domains if n.get("is_core") or (n.get("kind") == "domain" and n.get("atlas_kind") != "extension_panel" and n.get("S") is not None)]
    with_s = [n for n in domains if n.get("S") is not None]
    signed_neg = [n for n in with_s if float(n["S"]) < 0]
    signed_pos = [n for n in with_s if float(n["S"]) > 0]

    def polar(n: dict[str, Any]) -> tuple[float, float]:
        r = float(n.get("layout_r") or 0)
        a = float(n.get("layout_angle") or n.get("angle") or 0)
        return r * math.cos(a), r * math.sin(a)

    # correlation proxies: mean x should rise with S; mean r should rise with D
    if with_s:
        xs_s = [(float(n["S"]), polar(n)[0]) for n in with_s]
        # Spearman-ish via ranks
        by_s = sorted(xs_s, key=lambda t: t[0])
        # count pairs where higher S has higher x (east)
        pairs = 0
        agree = 0
        for i in range(len(by_s)):
            for j in range(i + 1, len(by_s)):
                pairs += 1
                if by_s[j][1] >= by_s[i][1]:
                    agree += 1
        s_x_order = agree / pairs if pairs else 0.0
    else:
        s_x_order = None

    with_d = [n for n in domains if n.get("D_eff") is not None and n.get("layout_r") is not None]
    if with_d:
        by_d = sorted(with_d, key=lambda n: float(n["D_eff"]))
        pairs = agree = 0
        for i in range(len(by_d)):
            for j in range(i + 1, min(i + 40, len(by_d))):  # local pairs for speed
                pairs += 1
                if float(by_d[j]["layout_r"]) >= float(by_d[i]["layout_r"]):
                    agree += 1
        d_r_order = agree / pairs if pairs else 0.0
    else:
        d_r_order = None

    core_table = []
    for n in sorted(cores, key=lambda x: float(x.get("S") if x.get("S") is not None else 0)):
        if not n.get("domain"):
            continue
        core_table.append(
            {
                "domain": n.get("domain"),
                "S": n.get("S"),
                "D_eff": n.get("D_eff"),
                "regime": n.get("regime"),
                "layout_r": round(float(n.get("layout_r") or 0), 1),
                "layout_angle_deg": round(math.degrees(float(n.get("layout_angle") or 0)), 1),
                "x_east": round(polar(n)[0], 1),
            }
        )

    return {
        "method": "fsot_sd_layout_diagnostics",
        "layout_mode": "s_deff_polar",
        "free_parameters": 0,
        "n_domains": len(domains),
        "n_with_S": len(with_s),
        "n_emergence_S_gt_0": len(signed_pos),
        "n_dispersal_S_lt_0": len(signed_neg),
        "order_score_S_vs_east_x": s_x_order,
        "order_score_D_vs_radius": d_r_order,
        "note": (
            "S→east/west (emergence right, dispersal left); "
            "D_eff→radius (low-D near K, high-D outer). "
            "Scores ~1.0 = perfect monotonic organization."
        ),
        "core_table": core_table,
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
    for name in names:
        try:
            base = get_domain(name)
            D = int(base["D_eff"])
            # ALWAYS use signed canonical S for geometry/regime (SD law).
            # Multipath path-mean is observer discovery — attach separately.
            e = evaluate_domain(name)
            S_can = float(e["S"])
            flip = 0.0
            S_path = None
            if name in de:
                S_path = float(de[name].get("S_path_mean", S_can))
                flip = float(de[name].get("flip_rate") or 0)
            cluster = base.get("cluster") or "unknown"
            color = CLUSTER_COLORS.get(cluster, CLUSTER_COLORS["unknown"])
            size = 6 + min(16, abs(S_can) * 14)
            nodes.append(
                {
                    "id": f"dom_{name}",
                    "label": name.replace("_", " "),
                    "domain": name,
                    "kind": "domain",
                    "group": cluster,
                    "color": color,
                    "size": float(size),
                    "D_eff": D,
                    "S": S_can,
                    "S_canonical": S_can,
                    "S_path_mean": S_path,
                    "regime": "emergence" if S_can > 0 else "dispersal",
                    "flip_rate": flip,
                    "is_core": name in set(core_names()),
                    "cluster": cluster,
                }
            )
        except Exception:
            continue
    return apply_sd_layout(nodes)


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


def _style_archive_nodes(archive_nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply colors/sizes; S–D_eff polar angles applied later via apply_sd_layout."""
    out = []
    for raw in archive_nodes:
        n = dict(raw)
        kind = n.get("kind") or "domain"
        group_name = n.get("group") or n.get("cluster") or "unknown"
        # Prefer signed canonical S for regime (do not invent path-mean here)
        if n.get("S") is not None:
            try:
                n["S"] = float(n["S"])
                n["S_canonical"] = n.get("S_canonical", n["S"])
                n["regime"] = "emergence" if n["S"] > 0 else "dispersal"
            except (TypeError, ValueError):
                pass
        if kind == "problem_route":
            color = CLUSTER_COLORS["problem_route"]
            size = 10
        elif kind == "extension" or n.get("atlas_kind") == "extension_panel":
            color = CLUSTER_COLORS["extension"]
            err = n.get("median_error_pct")
            if err is not None and float(err) <= 0.5:
                color = "#64748b"
            size = 4 + min(8, (abs(float(n["S"])) * 8) if n.get("S") is not None else 3)
        else:
            color = CLUSTER_COLORS.get(group_name, CLUSTER_COLORS["unknown"])
            size = 6 + min(14, abs(float(n["S"])) * 12) if n.get("S") is not None else 8
        n["color"] = color
        n["size"] = float(size)
        out.append(n)
    return apply_sd_layout(out)


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
        # Overlay multipath as observer stats ONLY — never replace signed S for layout
        de = (mc or {}).get("domain_ensemble") or {}
        for n in domains:
            dom = n.get("domain")
            if not dom:
                continue
            # Re-pin canonical S from atlas when available (truth for SD geometry)
            try:
                if n.get("is_core") or n.get("kind") == "domain":
                    ev = evaluate_domain(str(dom))
                    n["S"] = float(ev["S"])
                    n["S_canonical"] = float(ev["S"])
                    n["D_eff"] = int(ev.get("D_eff") or n.get("D_eff") or 12)
                    n["regime"] = "emergence" if n["S"] > 0 else "dispersal"
            except Exception:
                pass
            if dom in de:
                n["S_path_mean"] = float(de[dom].get("S_path_mean", n.get("S") or 0))
                n["flip_rate"] = de[dom].get("flip_rate")
                # path-mean may flip sign under observer coupling — keep as diagnostic
            if n.get("is_core") and n.get("S") is not None:
                n["size"] = 6 + min(14, abs(float(n["S"])) * 12)
                n["color"] = CLUSTER_COLORS.get(n.get("cluster") or "", CLUSTER_COLORS["unknown"])
        # Re-apply S–D_eff layout after canonical S restore
        domains = apply_sd_layout(domains)
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
    # Final S–D_eff polar layout over full node set (memory/pred get outer shells)
    nodes = apply_sd_layout(nodes)
    layout_diag = layout_diagnostics(nodes)

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
        "layout_mode": "s_deff_polar",
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
            "layer_edge_colors": LAYER_EDGE_COLORS,
            "archive_connective": archive_meta,
            "layout_mode": "s_deff_polar",
            "layout_diagnostics": {
                k: layout_diag.get(k)
                for k in (
                    "n_with_S",
                    "n_emergence_S_gt_0",
                    "n_dispersal_S_lt_0",
                    "order_score_S_vs_east_x",
                    "order_score_D_vs_radius",
                    "note",
                )
            },
            "rings": {
                "geometry": "radius ∝ D_eff · angle ∝ signed S (canonical)",
                "east S>0": "emergence folds (Particle Physics, QM, Biology…)",
                "west S<0": "dispersal folds (Cosmology, QG, Fluid Dynamics…)",
                "inner D~5–10": "low-D near law K",
                "outer D~20–25": "high-D complex systems / cosmo",
                "7": "memory engrams (LTM)",
                "8": "preregistered predictions",
            },
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
                "White = seeds (π,e,φ,γ,G) → violet K law hub",
                "Bright cluster hues = 35 core NeuroLab folds (size ∝ |S|)",
                "Slate nodes = extension panels (367) with archive median_error",
                "Lime axons = routes_to_core (panel → core validation spine)",
                "Pink hubs = problem routes (navigator intents)",
                "Cyan axons = archive domain-coupling validations (crosswalk / lean tags)",
                "Gold = preregistered predictions · Grey = adaptive memory",
                "Green gate: median_error_pct ≤ 0.5% from Physical Archive panels",
            ],
        },
        "note": (
            "Full FSOT connective tissue from Physical Archive: domain coupling simulation, "
            "navigator routes, expansion map accuracy, multipath core overlay. Seeds never move."
        ),
    }
