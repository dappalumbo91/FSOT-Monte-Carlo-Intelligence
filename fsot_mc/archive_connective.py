"""
Archive connective tissue — full FSOT cross-domain validation graph.

Sources (Physical Archive → vendor/archive_bundle):
  - domain_coupling_simulation_benchmark.json  (403 nodes, 39k edges)
  - fsot_domain_navigator.json                 (problem routes, by_core, panels)
  - scientific_domain_expansion_map.json       (403-domain empirical map)
  - full_atlas.json                            (402 local folds + S_canonical)

Builds a portable compact graph for the visual UI without loading 39k
maps_to_lean edges raw into the browser.
"""

from __future__ import annotations

import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from fsot_mc.paths import archive_bundle_dir, data_root
from fsot_mc.universe_atlas import core_names, get_domain, load_atlas


def _bundle(*parts: str) -> Path:
    return archive_bundle_dir().joinpath(*parts)


@lru_cache(maxsize=1)
def load_navigator() -> dict[str, Any]:
    for name in (
        "data__fsot_domain_navigator.json",
        "data__data__fsot_domain_navigator.json",
    ):
        p = _bundle(name)
        if p.is_file():
            return json.loads(p.read_text(encoding="utf-8"))
    # copied as data__fsot_domain_navigator.json from archive
    p = _bundle("data__fsot_domain_navigator.json")
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


@lru_cache(maxsize=1)
def load_expansion_map() -> dict[str, Any]:
    p = _bundle("data__scientific_domain_expansion_map.json")
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


@lru_cache(maxsize=1)
def load_coupling_benchmark() -> dict[str, Any]:
    p = _bundle("data__domain_coupling_simulation_benchmark.json")
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def compact_path() -> Path:
    return data_root() / "connective_tissue_compact.json"


def _node_id(domain: str) -> str:
    return f"dom_{domain}"


def _infer_cluster_from_name(name: str, routes: Any = None) -> str:
    """
    Map panel / formal module names to a science-family cluster for coloring.
    Avoids dumping hundreds of archive nodes into the generic 'extension' gray.
    """
    n = (name or "").lower()
    r = str(routes or "").lower()
    blob = f"{n} {r}"

    def hit(*keys: str) -> bool:
        return any(k in blob for k in keys)

    if hit("cosmo", "hubble", "dark_energy", "dark energy", "s8", "cmb", "inflation", "unification", "quantum_gravity", "string"):
        return "cosmo_unification"
    if hit("astro", "planet", "stellar", "galaxy", "solar", "exoplanet"):
        return "astro_planetary"
    if hit(
        "earth",
        "seismo",
        "ocean",
        "atmos",
        "meteo",
        "climate",
        "geo",
        "ionosph",
        "magnetosph",
        "ecology",
        "economic",
        "finance",
        "socio",
    ):
        return "earth_complex_systems"
    if hit(
        "bio",
        "neuro",
        "life",
        "gene",
        "protein",
        "cell",
        "codon",
        "ecology",
        "chem",
        "fuel",
        "thermo",
        "material",
        "fluid",
        "energy",
    ):
        return "life_matter_energy"
    if hit("atomic", "optical", "photon", "laser", "spectro", "molecular", "amo"):
        return "atomic_molecular_optical"
    if hit(
        "quantum",
        "particle",
        "nuclear",
        "higgs",
        "muon",
        "lepton",
        "hadron",
        "codata",
        "nist",
        "formal.particle",
        "formal.quantum",
    ):
        return "quantum_particle"
    if hit("formal.", "lean", "prior"):
        # formal modules default to cosmo/law spine rather than mute gray
        return "cosmo_unification"
    return "extension"


def build_compact_connective_tissue(
    *,
    max_lean_overlap_degree: int = 28,
    force: bool = False,
    dense_lean_cap: int = 22000,
) -> dict[str, Any]:
    """
    Compact multi-layer connective graph from archive validations.

    Edge layers:
      - routes_to_core          extension panel → core fold (base LOD)
      - problem_route           intent hubs → core + panels (base)
      - coupling_crosswalk      archive crosswalk_module edges (base)
      - coupling_cluster        magnetosphere / prediction / fluidlink (base)
      - coupling_lean_overlap   maps_to_lean_overlap with base/dense tiers
      - by_core_membership      navigator membership (dense LOD — zoom reveals)

    denser defaults (v1.5): base degree 28, dense cap 22k so zoom draws a much
    larger fraction of the ~39k raw coupling mesh without melting the browser.
    """
    out_path = compact_path()
    shipped = _bundle("data__connective_tissue_compact.json")
    if not force:
        for p in (out_path, shipped):
            if p.is_file():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue

    atlas = load_atlas()
    domains_meta = atlas.get("domains") or {}
    core = set(core_names())
    nav = load_navigator()
    exp = load_expansion_map()
    coup = load_coupling_benchmark()

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def ensure_domain(name: str, extra: dict[str, Any] | None = None) -> str:
        nid = _node_id(name)
        if nid in nodes:
            if extra:
                # Never demote cores; never wipe a good science cluster with "extension"
                for k, v in extra.items():
                    if v is None:
                        continue
                    if k in ("kind", "atlas_kind") and name in core:
                        continue
                    if k in ("cluster", "group") and str(v) in ("extension", "unknown", ""):
                        continue
                    cur = nodes[nid].get(k)
                    if cur in (None, "", [], False) or k in (
                        "median_error_pct",
                        "coverage_tier",
                        "record_count",
                        "tier",
                        "lean_module",
                        "routes_to_core",
                    ):
                        nodes[nid][k] = v
            if name in core:
                nodes[nid]["is_core"] = True
                nodes[nid]["kind"] = "domain"
                nodes[nid]["atlas_kind"] = "core"
            # repair missing cluster
            if str(nodes[nid].get("cluster") or "") in ("", "extension", "unknown"):
                cl = _infer_cluster_from_name(name, routes=nodes[nid].get("routes_to_core"))
                nodes[nid]["cluster"] = cl
                nodes[nid]["group"] = cl
            return nid
        # try atlas
        base = domains_meta.get(name) or {}
        try:
            if not base and name in core:
                base = get_domain(name)
        except KeyError:
            base = {}
        kind = base.get("kind") or ("core" if name in core else "extension_panel")
        # Never demote a NeuroLab core fold if name is in core set
        if name in core:
            kind = "core"
        cluster = base.get("cluster") or ""
        # Prefer scientific family even for extensions (color graph by domain family)
        if cluster in (None, "", "unknown", "extension"):
            cluster = _infer_cluster_from_name(
                name,
                routes=(base.get("routes_to_core") or (extra or {}).get("routes_to_core")),
            )
        D = base.get("D_eff")
        if D is None:
            D = 12 if kind != "core" else 15
        S = base.get("S_canonical")
        err = base.get("median_error_pct")
        cov = base.get("coverage_tier")
        nodes[nid] = {
            "id": nid,
            "label": name.replace("_", " "),
            "domain": name,
            "kind": "domain" if kind == "core" else "extension",
            "atlas_kind": kind,
            # group = science family for coloring (not the word "extension")
            "group": cluster,
            "cluster": cluster,
            "D_eff": int(D) if D is not None else 12,
            "S": float(S) if S is not None else None,
            "regime": base.get("regime")
            or ("emergence" if (S is not None and float(S) > 0) else "dispersal" if S is not None else None),
            "median_error_pct": float(err) if err is not None else None,
            "coverage_tier": cov or extra.get("coverage_tier") if extra else cov,
            "record_count": base.get("record_count") or (extra or {}).get("record_count"),
            "routes_to_core": base.get("routes_to_core") or (extra or {}).get("routes_to_core"),
            "tier": base.get("tier") or (extra or {}).get("tier"),
            "tags": base.get("tags") or (extra or {}).get("tags") or [],
            "maps_to_lean": base.get("maps_to_lean") or (extra or {}).get("maps_to_lean") or [],
            "lean_module": base.get("lean_module") or (extra or {}).get("lean_module"),
            "ring": max(1, min(8, int(1 + int(D or 12) / 4))),
            "in_atlas": name in domains_meta,
            "is_core": name in core,
        }
        if extra:
            for k, v in extra.items():
                if v is not None and nodes[nid].get(k) in (None, "", [], False):
                    nodes[nid][k] = v
        return nid

    # 1) All atlas domains (402)
    for name, meta in domains_meta.items():
        ensure_domain(name, dict(meta) if isinstance(meta, dict) else None)

    # 2) Expansion map accuracy overlays
    for row in exp.get("neurolab_domains") or []:
        if isinstance(row, dict) and row.get("domain"):
            ensure_domain(
                str(row["domain"]),
                {
                    "median_error_pct": row.get("median_error_pct"),
                    "coverage_tier": row.get("coverage_tier"),
                    "record_count": row.get("empirical_records") or row.get("record_count"),
                    "precision_status": row.get("precision_status"),
                },
            )
    for row in exp.get("extension_domains") or []:
        if isinstance(row, dict) and row.get("domain"):
            dname = str(row["domain"])
            # Do not overwrite true core folds as extension panels
            if dname in core:
                ensure_domain(
                    dname,
                    {
                        "median_error_pct": row.get("median_error_pct"),
                        "coverage_tier": row.get("coverage_tier"),
                        "record_count": row.get("record_count"),
                        "tier": row.get("tier"),
                        "lean_module": row.get("lean_module"),
                    },
                )
            else:
                ensure_domain(
                    dname,
                    {
                        "median_error_pct": row.get("median_error_pct"),
                        "coverage_tier": row.get("coverage_tier"),
                        "record_count": row.get("record_count"),
                        "tier": row.get("tier"),
                        "lean_module": row.get("lean_module"),
                        "atlas_kind": "extension_panel",
                        "kind": "extension",
                    },
                )

    # 3) Coupling benchmark nodes
    for row in coup.get("nodes") or []:
        if isinstance(row, dict) and row.get("domain"):
            ensure_domain(
                str(row["domain"]),
                {
                    "median_error_pct": row.get("median_error_pct"),
                    "record_count": row.get("record_count"),
                    "maps_to_lean": row.get("maps_to_lean"),
                    "lean_module": row.get("lean_module"),
                    "coupling_kind": row.get("kind"),
                },
            )

    # 4) routes_to_core edges from atlas extensions + navigator panels
    for name, meta in domains_meta.items():
        if not isinstance(meta, dict):
            continue
        rtc = meta.get("routes_to_core") or meta.get("resolved_core")
        if rtc and name not in core:
            src = ensure_domain(name)
            tgt = ensure_domain(str(rtc))
            edges.append(
                {
                    "id": f"route_{name}->{rtc}",
                    "source": src,
                    "target": tgt,
                    "kind": "routes_to_core",
                    "layer": "archive_route",
                    "strength": 0.75,
                    "error_pct": meta.get("median_error_pct"),
                    "label": f"{name}→{rtc}",
                    "density_tier": "base",
                }
            )

    for panel in nav.get("extension_panels") or []:
        if not isinstance(panel, dict):
            continue
        pname = panel.get("panel") or panel.get("name")
        rtc = panel.get("routes_to_core")
        if not pname or not rtc:
            continue
        ensure_domain(
            str(pname),
            {
                "routes_to_core": rtc,
                "median_error_pct": panel.get("median_error_pct"),
                "coverage_tier": panel.get("coverage_tier"),
                "record_count": panel.get("record_count"),
                "tier": panel.get("tier"),
                "tags": panel.get("tags"),
                "maps_to_lean": panel.get("maps_to_lean"),
                "lean_module": panel.get("lean_module"),
                "atlas_kind": "extension_panel",
                "kind": "extension",
            },
        )
        edges.append(
            {
                "id": f"navroute_{pname}->{rtc}",
                "source": _node_id(str(pname)),
                "target": ensure_domain(str(rtc)),
                "kind": "routes_to_core",
                "layer": "navigator_route",
                "strength": 0.7,
                "error_pct": panel.get("median_error_pct"),
                "density_tier": "base",
            }
        )

    # by_core_domain membership edges (dense LOD — reveal on zoom)
    for core_d, plist in (nav.get("by_core_domain") or {}).items():
        ensure_domain(str(core_d))
        if not isinstance(plist, list):
            continue
        for p in plist:
            pname = p if isinstance(p, str) else (p.get("panel") if isinstance(p, dict) else None)
            if not pname:
                continue
            ensure_domain(str(pname), {"routes_to_core": core_d, "kind": "extension"})
            edges.append(
                {
                    "id": f"bycore_{pname}->{core_d}",
                    "source": _node_id(str(pname)),
                    "target": _node_id(str(core_d)),
                    "kind": "by_core_membership",
                    "layer": "navigator_membership",
                    "strength": 0.55,
                    "density_tier": "dense",
                }
            )

    # problem routes as intent hubs
    for pr in nav.get("problem_routes") or []:
        if not isinstance(pr, dict):
            continue
        intent = str(pr.get("intent") or "intent")
        hid = f"intent_{intent}"
        nodes[hid] = {
            "id": hid,
            "label": intent.replace("_", " "),
            "kind": "problem_route",
            "group": "problem_route",
            "cluster": "problem_route",
            "D_eff": 14,
            "ring": 5,
            "keywords": pr.get("keywords") or [],
            "core_domain": pr.get("core_domain"),
            "panels": pr.get("panels") or [],
        }
        cdom = pr.get("core_domain")
        if cdom:
            edges.append(
                {
                    "id": f"{hid}->{cdom}",
                    "source": hid,
                    "target": ensure_domain(str(cdom)),
                    "kind": "problem_route",
                    "layer": "problem_intent",
                    "strength": 0.85,
                    "density_tier": "base",
                }
            )
        for p in pr.get("panels") or []:
            edges.append(
                {
                    "id": f"{hid}->{p}",
                    "source": hid,
                    "target": ensure_domain(str(p), {"kind": "extension"}),
                    "kind": "problem_route",
                    "layer": "problem_intent",
                    "strength": 0.65,
                    "density_tier": "base",
                }
            )

    # 5) Coupling edges — always keep sparse high-value types
    PRIORITY_TYPES = {
        "crosswalk_module",
        "magnetosphere_cluster",
        "fsot_prediction_cross_ratio",
        "fluidlink_fpc_timing",
    }
    lean_deg: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    n_lean = 0
    # denser zoom LOD: base degree + 4× dense ring (still cap for browser RAM)
    dense_degree = max(max_lean_overlap_degree * 4, 80)

    for e in coup.get("edges") or []:
        if not isinstance(e, dict):
            continue
        et = str(e.get("edge_type") or "unknown")
        src = e.get("source_domain")
        tgt = e.get("target_domain")
        if not src or not tgt:
            continue
        ensure_domain(str(src))
        ensure_domain(str(tgt))
        err = float(e.get("error_pct") or 0.0)

        if et in PRIORITY_TYPES:
            edges.append(
                {
                    "id": f"coup_{et}_{src}_{tgt}_{e.get('lean_tag') or e.get('name')}",
                    "source": _node_id(str(src)),
                    "target": _node_id(str(tgt)),
                    "kind": f"coupling_{et}",
                    "layer": "archive_coupling",
                    "edge_type": et,
                    "strength": 0.9 if err <= 0.5 else 0.5,
                    "error_pct": err,
                    "lean_tag": e.get("lean_tag"),
                    "label": e.get("name"),
                    "within_green_gate": err <= 0.5,
                    "density_tier": "base",  # always drawn
                }
            )
            type_counts[et] += 1
            continue

        if et == "maps_to_lean_overlap":
            if n_lean >= dense_lean_cap:
                continue
            sid, tid = str(src), str(tgt)
            # base tier: tighter degree for always-visible neural mesh
            # dense tier: higher degree, drawn only when zoomed (frontend LOD)
            if lean_deg[sid] < max_lean_overlap_degree or lean_deg[tid] < max_lean_overlap_degree:
                tier = "base"
            elif lean_deg[sid] < dense_degree or lean_deg[tid] < dense_degree:
                tier = "dense"
            else:
                continue
            prefer = sid in core or tid in core
            if tier == "dense" and not prefer and lean_deg[sid] > dense_degree // 2:
                continue
            edges.append(
                {
                    "id": f"lean_{sid}_{tid}_{e.get('lean_tag')}",
                    "source": _node_id(sid),
                    "target": _node_id(tid),
                    "kind": "coupling_lean_overlap",
                    "layer": "archive_lean_overlap",
                    "edge_type": et,
                    "strength": 0.35 if tier == "base" else 0.2,
                    "error_pct": err,
                    "lean_tag": e.get("lean_tag"),
                    "within_green_gate": err <= 0.5,
                    "density_tier": tier,
                }
            )
            lean_deg[sid] += 1
            lean_deg[tid] += 1
            type_counts[et] += 1
            n_lean += 1

    # 6) Gated scaffold deltas (Lean/court/Qwen expansion — never seeds)
    n_scaffold_nodes = 0
    n_scaffold_edges = 0
    try:
        from fsot_mc.pathway_alignment import load_scaffold_deltas

        deltas = load_scaffold_deltas()
        for sn in deltas.get("nodes") or []:
            if not isinstance(sn, dict):
                continue
            name = str(sn.get("domain") or "").strip()
            if not name:
                continue
            ensure_domain(
                name,
                {
                    "atlas_kind": sn.get("atlas_kind") or "scaffold_panel",
                    "kind": sn.get("kind") or "extension",
                    "lean_module": sn.get("lean_module"),
                    "cluster": sn.get("cluster"),
                    "median_error_pct": sn.get("median_error_pct"),
                    "tier": sn.get("tier"),
                },
            )
            nid = _node_id(name)
            if nid in nodes:
                # stamp epistemic origin without wiping archive fields
                nodes[nid].setdefault("epistemic_tier", sn.get("epistemic_tier") or "scaffold")
                nodes[nid].setdefault("origin", sn.get("origin") or "scaffold_delta")
                if sn.get("lean_module") and not nodes[nid].get("lean_module"):
                    nodes[nid]["lean_module"] = sn.get("lean_module")
                n_scaffold_nodes += 1
        for se in deltas.get("edges") or []:
            if not isinstance(se, dict):
                continue
            s = se.get("source")
            t = se.get("target")
            if not s or not t:
                continue
            # normalize ids
            if not str(s).startswith("dom_") and not str(s).startswith("intent_"):
                s = _node_id(str(s).replace("dom_", ""))
            if not str(t).startswith("dom_") and not str(t).startswith("intent_"):
                t = _node_id(str(t).replace("dom_", ""))
            # ensure endpoints exist
            ensure_domain(str(s).replace("dom_", ""))
            ensure_domain(str(t).replace("dom_", ""))
            edges.append(
                {
                    "id": se.get("id") or f"scaffold_{s}_{t}",
                    "source": s if str(s) in nodes else _node_id(str(s).replace("dom_", "")),
                    "target": t if str(t) in nodes else _node_id(str(t).replace("dom_", "")),
                    "kind": se.get("kind") or "scaffold_pathway",
                    "layer": se.get("layer") or "scaffold_pathway",
                    "strength": float(se.get("strength") or 0.4),
                    "density_tier": se.get("density_tier") or "base",
                    "epistemic_tier": se.get("epistemic_tier") or "scaffold",
                    "lean_module": se.get("lean_module"),
                    "origin": se.get("origin") or "scaffold_delta",
                    "evidence": se.get("evidence"),
                }
            )
            type_counts[str(se.get("kind") or "scaffold_pathway")] += 1
            n_scaffold_edges += 1
    except Exception:
        n_scaffold_nodes = 0
        n_scaffold_edges = 0

    # dedupe edges by id
    seen = set()
    uniq_edges = []
    for e in edges:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        uniq_edges.append(e)

    # only keep edges with both endpoints
    ids = set(nodes)
    uniq_edges = [e for e in uniq_edges if e["source"] in ids and e["target"] in ids]

    # accuracy summary
    with_err = [n for n in nodes.values() if n.get("median_error_pct") is not None]
    green = [n for n in with_err if float(n["median_error_pct"]) <= 0.5]

    payload = {
        "version": "1.0",
        "method": "fsot_archive_connective_tissue",
        "free_parameters": 0,
        "authority": "D1D38A",
        "source": {
            "coupling_benchmark": "data__domain_coupling_simulation_benchmark.json",
            "navigator": "data__fsot_domain_navigator.json",
            "expansion_map": "data__scientific_domain_expansion_map.json",
            "atlas": "full_atlas.json",
            "physical_archive": "I:/FSOT-Physical-Archive (synced subset)",
        },
        "n_nodes": len(nodes),
        "n_edges": len(uniq_edges),
        "n_core": sum(1 for n in nodes.values() if n.get("is_core")),
        "n_extension": sum(1 for n in nodes.values() if n.get("kind") == "extension"),
        "n_problem_routes": sum(1 for n in nodes.values() if n.get("kind") == "problem_route"),
        "n_with_error": len(with_err),
        "n_green_gate": len(green),
        "edge_type_counts": dict(type_counts),
        "density_tier_counts": {
            t: sum(1 for e in uniq_edges if e.get("density_tier") == t)
            for t in ("base", "dense")
        },
        "max_lean_overlap_degree": max_lean_overlap_degree,
        "dense_lean_cap": dense_lean_cap,
        "dense_degree": dense_degree,
        "coupling_raw_edge_count": coup.get("edge_count"),
        "coupling_raw_node_count": coup.get("node_count"),
        "expansion_summary": exp.get("summary"),
        "scaffold_deltas": {
            "n_nodes_touched": n_scaffold_nodes,
            "n_edges_merged": n_scaffold_edges,
            "note": "Gated Lean/court/Qwen scaffolds — not seed retune; not Lean-proved by default",
        },
        "nodes": list(nodes.values()),
        "edges": uniq_edges,
        "note": (
            "Full FSOT connective tissue: atlas folds + navigator routes + problem intents + "
            "archive domain-coupling validations (degree-capped lean-overlap with base/dense LOD). "
            "Zoom densifies mesh; green gate ≤0.5% on median_error_pct where present."
        ),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, default=str)
    out_path.write_text(text, encoding="utf-8")
    # ship portable copy for git clones without the 33MB raw coupling benchmark
    try:
        shipped = _bundle("data__connective_tissue_compact.json")
        shipped.write_text(text, encoding="utf-8")
    except Exception:
        pass
    return payload


def get_connective_tissue(*, force_rebuild: bool = False) -> dict[str, Any]:
    return build_compact_connective_tissue(force=force_rebuild)
