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
    "unknown": "#8892a4",
    "seed": "#ffffff",
    "law": "#c4b5fd",
    "memory": "#94a3b8",
    "prediction": "#fbbf24",
    "bridge": "#67e8f9",
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
    # group by D_eff for ring layout
    by_d: dict[int, list[str]] = {}
    for n in names:
        try:
            d = int(get_domain(n)["D_eff"])
        except KeyError:
            continue
        by_d.setdefault(d, []).append(n)

    for D, group in sorted(by_d.items()):
        for i, name in enumerate(sorted(group)):
            try:
                base = get_domain(name)
                if name in de:
                    S = float(de[name].get("S_path_mean", de[name].get("S_canonical", 0)))
                    flip = float(de[name].get("flip_rate") or 0)
                else:
                    e = evaluate_domain(name)
                    S = float(e["S"])
                    flip = 0.0
                cluster = base.get("cluster") or "unknown"
                color = CLUSTER_COLORS.get(cluster, CLUSTER_COLORS["unknown"])
                size = 6 + min(16, abs(S) * 14)
                angle = (2 * math.pi * i) / max(len(group), 1)
                # slight φ spiral offset by D
                angle += (D * SEED_PHI) % (2 * math.pi) * 0.05
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
                        "S": S,
                        "regime": "emergence" if S > 0 else "dispersal",
                        "flip_rate": flip,
                        "ring": max(1, min(6, int(1 + D / 5))),
                        "angle": angle,
                        "cluster": cluster,
                    }
                )
            except Exception:
                continue
    return nodes


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


def build_universe_graph(
    *,
    n_paths: int = 48,
    seed: int = 0,
    scope: str = "core",
    with_memory: bool = True,
    with_predictions: bool = True,
    with_mc: bool = True,
) -> dict[str, Any]:
    """Full multi-scale connective graph for the visual frontend."""
    mc = None
    if with_mc:
        mc = run_universe_monte_carlo(
            n_paths=n_paths,
            seed=seed,
            store_paths=min(8, n_paths),
            train_pathway_memory=False,
        )
        if mc.get("error"):
            mc = None

    seeds = _seed_nodes()
    seed_edges = _seed_edges()
    domains = build_domain_nodes(scope=scope, mc=mc)
    dom_edges = build_domain_edges(domains, mc)

    mem_nodes, mem_edges = ([], [])
    if with_memory:
        mem_nodes, mem_edges = build_memory_nodes()

    pred_nodes, pred_edges = ([], [])
    if with_predictions:
        pred_nodes, pred_edges = build_prediction_nodes()

    nodes = seeds + domains + mem_nodes + pred_nodes
    edges = seed_edges + dom_edges + mem_edges + pred_edges

    # Filter edges whose endpoints exist
    ids = {n["id"] for n in nodes}
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]

    ens = (mc or {}).get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}

    return {
        "error": None,
        "method": "fsot_universe_connective_graph",
        "free_parameters": 0,
        "authority": "D1D38A",
        "aesthetic": "obsidian_second_brain_x_neural_growth",
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "n_paths": (mc or {}).get("n_paths"),
            "map_emergence_mean": ef.get("mean"),
            "n_domains": len(domains),
            "n_memory": len(mem_nodes),
            "n_predictions": len(pred_nodes),
            "clusters": domains_by_cluster(),
            "cluster_colors": CLUSTER_COLORS,
            "rings": {
                "0": "seeds + law K",
                "1-6": "domain folds by D_eff bands",
                "7": "memory engrams (LTM)",
                "8": "preregistered predictions",
            },
            "legend": [
                "White nodes = seeds (π,e,φ,γ,G)",
                "Violet hub = law scalar K",
                "Colored nodes = domain folds (cluster hue, size ∝ |S|)",
                "Cyan edges = ladder / long-range As Above bridges",
                "Gold nodes = preregistered predictions",
                "Grey nodes = adaptive memory engrams",
            ],
        },
        "note": (
            "Connective multi-scale map of FSOT: seeds propagate through K into domain folds; "
            "bridges and memory form neural tissue across scales. Seeds never move."
        ),
    }
