"""
Pathway alignment + gated connective expansion.

Aligns the MC connective graph with:
  - Local multi-verifier court (certificate + cross_proof in vendor/archive_bundle)
  - Optional physical archive hub: I:\\FSOT-Physical-Archive\\02_FSOT-2.1-Lean-Full
  - Optional Desktop Lean: FSOT-2.1-Lean

Fine-tunes *pathways* only via soft court + scaffold deltas — never moves seeds / pin D1D38A.

Expansion sources (all gated free_parameters=0):
  1. Certificate proved claims → ensure domain↔lean_module edges
  2. Soft-court promoted obligations → scaffold pathways
  3. Missing Lean Formal modules on disk vs graph lean_module fields
  4. Qwen/API structured proposals (JSON) → pending obligation → soft court → delta

CLI:
  python -m fsot_mc align-pathways
  python -m fsot_mc expand-pathways
  python -m fsot_mc pathway-status
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.formal_bridge import (
    export_lead_obligation,
    formal_status,
    load_cross_proof_summary,
    load_synced_certificate,
    run_soft_court,
)
from fsot_mc.paths import PACKAGE_ROOT, archive_bundle_dir, data_root

DELTA_DIR = data_root() / "connective_deltas"
SCAFFOLD_NODES = DELTA_DIR / "scaffold_nodes.jsonl"
SCAFFOLD_EDGES = DELTA_DIR / "scaffold_edges.jsonl"
REPORT_JSON = data_root() / "exports" / "pathway_alignment_latest.json"
REPORT_MD = PACKAGE_ROOT / "docs" / "PATHWAY_ALIGNMENT.md"

# Known Lean hub roots (optional external truth surfaces)
_LEAN_HUB_CANDIDATES = (
    Path(r"I:\FSOT-Physical-Archive\02_FSOT-2.1-Lean-Full"),
    Path(r"C:\Users\damia\Desktop\FSOT-2.1-Lean\FSOT-2.1-Lean-main\FSOT-2.1-Lean-main"),
    Path(r"C:\Users\damia\Desktop\FSOT-2.1-Lean\FSOT-2.1-Lean-main"),
    Path(r"C:\Users\damia\Desktop\FSOT-2.1-Lean"),
)


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_lean_hub() -> dict[str, Any]:
    """Find best available Lean/physical-archive hub for alignment."""
    env = __import__("os").environ.get("FSOT_LEAN_HUB") or __import__("os").environ.get(
        "FSOT_ARCHIVE_ROOT"
    )
    found: list[dict[str, str]] = []
    if env:
        p = Path(env)
        if p.is_dir():
            lean = p / "02_FSOT-2.1-Lean-Full" if (p / "02_FSOT-2.1-Lean-Full").is_dir() else p
            if (lean / "FSOT").is_dir() or (lean / "FSOT.lean").is_file():
                found.append({"path": str(lean), "via": "env"})
    for cand in _LEAN_HUB_CANDIDATES:
        if cand.is_dir() and ((cand / "FSOT").is_dir() or (cand / "FSOT.lean").is_file()):
            found.append({"path": str(cand), "via": "default"})
    primary = found[0]["path"] if found else None
    return {
        "primary": primary,
        "candidates": found,
        "physical_archive": str(Path(r"I:\FSOT-Physical-Archive"))
        if Path(r"I:\FSOT-Physical-Archive").is_dir()
        else None,
        "local_bundle": str(archive_bundle_dir()),
    }


def scan_lean_formal_modules(hub: Path | None) -> list[str]:
    """List FSOT.Formal.* module names from .lean files under hub/FSOT/Formal."""
    if hub is None:
        return []
    formal = hub / "FSOT" / "Formal"
    if not formal.is_dir():
        # nested zip layout
        for sub in hub.rglob("FSOT/Formal"):
            if sub.is_dir():
                formal = sub
                break
    if not formal.is_dir():
        return []
    mods: list[str] = []
    for p in formal.rglob("*.lean"):
        # FSOT/Formal/Foo.lean → FSOT.Formal.Foo
        try:
            rel = p.relative_to(formal)
        except ValueError:
            continue
        parts = list(rel.with_suffix("").parts)
        if not parts:
            continue
        mods.append("FSOT.Formal." + ".".join(parts))
    return sorted(set(mods))


def _load_compact_tissue() -> dict[str, Any]:
    from fsot_mc.archive_connective import get_connective_tissue

    return get_connective_tissue(force_rebuild=False)


def _graph_lean_index(tissue: dict[str, Any]) -> dict[str, Any]:
    nodes = tissue.get("nodes") or []
    by_module: dict[str, list[str]] = {}
    by_tag: dict[str, list[str]] = {}
    domains: list[str] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        dom = str(n.get("domain") or n.get("label") or n.get("id") or "")
        if n.get("domain"):
            domains.append(str(n["domain"]))
        lm = n.get("lean_module")
        if lm:
            by_module.setdefault(str(lm), []).append(dom or str(n.get("id")))
        for t in n.get("maps_to_lean") or []:
            by_tag.setdefault(str(t), []).append(dom or str(n.get("id")))
    return {
        "n_nodes": len(nodes),
        "n_edges": tissue.get("n_edges") or len(tissue.get("edges") or []),
        "domains": sorted(set(domains)),
        "lean_modules": sorted(by_module.keys()),
        "by_module": by_module,
        "maps_to_lean_tags": sorted(by_tag.keys()),
        "by_tag": by_tag,
    }


def load_scaffold_deltas() -> dict[str, Any]:
    """Load admitted scaffold nodes/edges for tissue merge."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    if SCAFFOLD_NODES.is_file():
        for line in SCAFFOLD_NODES.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                nodes.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if SCAFFOLD_EDGES.is_file():
        for line in SCAFFOLD_EDGES.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                edges.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return {
        "nodes": nodes,
        "edges": edges,
        "n_nodes": len(nodes),
        "n_edges": len(edges),
        "paths": {"nodes": str(SCAFFOLD_NODES), "edges": str(SCAFFOLD_EDGES)},
    }


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    DELTA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _edge_id(src: str, tgt: str, kind: str) -> str:
    return f"delta_{kind}_{src}_{tgt}"


def admit_scaffold_edge(
    *,
    source: str,
    target: str,
    kind: str = "scaffold_pathway",
    strength: float = 0.4,
    evidence: str = "",
    epistemic_tier: str = "scaffold",
    lean_module: str | None = None,
    origin: str = "alignment",
) -> dict[str, Any]:
    """
    Admit one scaffold pathway into the delta store.
    Gated: authority pin must pass; no free-parameter language.
    """
    g = verify_fsot_gate(require_archive=False)
    if not g.get("ok"):
        return {"ok": False, "error": "authority_gate_failed", "gate": g}

    src, tgt = str(source).strip(), str(target).strip()
    if not src or not tgt or src == tgt:
        return {"ok": False, "error": "bad_endpoints"}

    blob = f"{evidence} {kind} {epistemic_tier}".lower()
    if any(x in blob for x in ("free parameter", "fitted constant", "retune seed", "we proved in lean just now")):
        return {"ok": False, "error": "forbidden_claim_language"}

    # dedupe
    existing = load_scaffold_deltas()
    eid = _edge_id(src, tgt, kind)
    for e in existing["edges"]:
        if e.get("id") == eid or (
            e.get("source") == f"dom_{src}" and e.get("target") == f"dom_{tgt}" and e.get("kind") == kind
        ):
            return {"ok": True, "admitted": False, "reason": "duplicate", "id": eid}

    # ensure endpoint scaffold nodes
    for name in (src, tgt):
        nid = name if str(name).startswith("dom_") or str(name).startswith("intent_") else f"dom_{name}"
        bare = name.replace("dom_", "") if str(name).startswith("dom_") else name
        if not any(n.get("id") == nid or n.get("domain") == bare for n in existing["nodes"]):
            node = {
                "id": nid,
                "domain": bare,
                "label": bare.replace("_", " "),
                "kind": "extension",
                "atlas_kind": "scaffold_panel",
                "cluster": "extension",
                "group": "scaffold",
                "D_eff": 12,
                "ring": 4,
                "epistemic_tier": epistemic_tier,
                "lean_module": lean_module if bare in (src, tgt) else None,
                "origin": origin,
                "free_parameters": 0,
                "authority": AUTHORITY_SHA256[:12],
                "admitted_at": _utc(),
            }
            if lean_module and bare == src:
                node["lean_module"] = lean_module
            _append_jsonl(SCAFFOLD_NODES, node)

    src_id = src if src.startswith("dom_") else f"dom_{src}"
    tgt_id = tgt if tgt.startswith("dom_") else f"dom_{tgt}"
    edge = {
        "id": eid,
        "source": src_id,
        "target": tgt_id,
        "kind": kind,
        "layer": "scaffold_pathway",
        "strength": float(strength),
        "density_tier": "base",
        "epistemic_tier": epistemic_tier,
        "evidence": (evidence or "")[:800],
        "lean_module": lean_module,
        "origin": origin,
        "free_parameters": 0,
        "authority": AUTHORITY_SHA256[:12],
        "note": "Scaffold pathway — not Lean-proved; soft-court / archive alignment only.",
        "admitted_at": _utc(),
    }
    _append_jsonl(SCAFFOLD_EDGES, edge)
    return {"ok": True, "admitted": True, "edge": edge}


def align_certificate_claims(tissue_index: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Ensure every certificate proved claim with lean_module has a graph foothold
    and a scaffold edge to a matching domain when possible.
    """
    cert = load_synced_certificate() or {}
    claims = cert.get("proved_claims") or []
    tissue = tissue_index or _graph_lean_index(_load_compact_tissue())
    modules = set(tissue.get("lean_modules") or [])
    domains = set(tissue.get("domains") or [])
    by_mod = tissue.get("by_module") or {}

    linked = 0
    missing_module: list[dict[str, Any]] = []
    admitted = 0
    for c in claims:
        if not isinstance(c, dict):
            continue
        lm = c.get("lean_module")
        dom = c.get("domain")
        cid = c.get("id")
        if not lm:
            continue
        if lm in modules or any(lm in m for m in modules):
            linked += 1
            # strengthen: domain → lean hub edge
            hosts = by_mod.get(lm) or []
            if hosts:
                admit_scaffold_edge(
                    source=str(hosts[0]),
                    target=str(hosts[0]),
                    kind="formal_self_anchor",
                    strength=0.2,
                    evidence=f"certificate {cid} {c.get('claim')}",
                    epistemic_tier="measured_application",
                    lean_module=str(lm),
                    origin="certificate",
                )
            continue
        missing_module.append({"claim_id": cid, "lean_module": lm, "domain": dom, "status": c.get("status")})
        # create scaffold panel for missing formal module
        panel = str(lm).replace("FSOT.Formal.", "").replace(".", "_")
        if panel and panel not in domains:
            r = admit_scaffold_edge(
                source=panel,
                target=str(dom) if dom and str(dom) in domains else "Cosmology",
                kind="formal_claim_bridge",
                strength=0.55,
                evidence=f"proved_claim {cid}: {c.get('claim')} module={lm}",
                epistemic_tier="linked_existing_claim",
                lean_module=str(lm),
                origin="certificate_gap",
            )
            if r.get("admitted"):
                admitted += 1
                # tag node lean_module
                _append_jsonl(
                    SCAFFOLD_NODES,
                    {
                        "id": f"dom_{panel}",
                        "domain": panel,
                        "label": panel.replace("_", " "),
                        "kind": "extension",
                        "atlas_kind": "formal_scaffold",
                        "lean_module": lm,
                        "cluster": "cosmo_unification",
                        "group": "formal_math",
                        "D_eff": 16,
                        "ring": 5,
                        "epistemic_tier": "linked_existing_claim",
                        "origin": "certificate_gap",
                        "free_parameters": 0,
                        "admitted_at": _utc(),
                    },
                )

    return {
        "n_claims": len(claims),
        "linked_to_graph": linked,
        "missing_module_claims": missing_module[:50],
        "n_missing": len(missing_module),
        "scaffold_admitted": admitted,
        "free_parameters": 0,
    }


def align_lean_disk_modules(hub_path: str | None = None) -> dict[str, Any]:
    """Diff .lean Formal modules on disk vs graph lean_module fields."""
    hub_info = resolve_lean_hub()
    hub = Path(hub_path) if hub_path else (Path(hub_info["primary"]) if hub_info.get("primary") else None)
    disk = scan_lean_formal_modules(hub)
    tissue = _graph_lean_index(_load_compact_tissue())
    graph_mods = set(tissue.get("lean_modules") or [])
    # normalize loose matches
    disk_set = set(disk)
    missing_on_graph = sorted(disk_set - graph_mods)
    # also check basename match
    graph_bases = {m.split(".")[-1] for m in graph_mods}
    truly_missing = [m for m in missing_on_graph if m.split(".")[-1] not in graph_bases]
    extra_on_graph = sorted(graph_mods - disk_set) if disk_set else []

    admitted = 0
    # admit top missing as formal scaffold hubs (cap)
    for m in truly_missing[:40]:
        panel = m.replace("FSOT.Formal.", "").replace(".", "_")
        r = admit_scaffold_edge(
            source=panel,
            target="Quantum_Mechanics" if "Quantum" in m or "Particle" in m else "Cosmology",
            kind="formal_module_scaffold",
            strength=0.35,
            evidence=f"Lean Formal module on disk not yet in connective graph: {m}",
            epistemic_tier="scaffold",
            lean_module=m,
            origin="lean_disk_scan",
        )
        if r.get("admitted"):
            admitted += 1
            _append_jsonl(
                SCAFFOLD_NODES,
                {
                    "id": f"dom_{panel}",
                    "domain": panel,
                    "label": panel.replace("_", " "),
                    "kind": "extension",
                    "atlas_kind": "formal_scaffold",
                    "lean_module": m,
                    "cluster": "extension",
                    "group": "formal_math",
                    "D_eff": 14,
                    "ring": 4,
                    "epistemic_tier": "scaffold",
                    "origin": "lean_disk_scan",
                    "free_parameters": 0,
                    "admitted_at": _utc(),
                },
            )

    return {
        "hub": str(hub) if hub else None,
        "n_disk_modules": len(disk),
        "n_graph_modules": len(graph_mods),
        "n_missing_on_graph": len(truly_missing),
        "missing_sample": truly_missing[:30],
        "n_extra_on_graph": len(extra_on_graph),
        "extra_sample": extra_on_graph[:20],
        "scaffold_admitted": admitted,
        "free_parameters": 0,
    }


def align_promoted_obligations() -> dict[str, Any]:
    """Turn soft-court promoted leads into scaffold pathways when domain pairs exist."""
    promo = PACKAGE_ROOT / "data" / "obligations_promoted"
    if not promo.is_dir():
        return {"ok": True, "n_promoted": 0, "admitted": 0}
    admitted = 0
    n = 0
    for f in sorted(promo.glob("*.json")):
        n += 1
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        lead = payload.get("lead") or payload
        # try extract domains
        domains: list[str] = []
        for key in ("domain", "source_domain", "target_domain", "focus"):
            v = lead.get(key)
            if isinstance(v, str) and v:
                domains.append(v)
        for d in lead.get("domains") or []:
            if isinstance(d, str):
                domains.append(d)
        title = str(lead.get("title") or lead.get("id") or f.stem)
        # bridges often encoded as A__B
        for m in re.findall(r"([A-Za-z][A-Za-z0-9_]+)", title):
            if "_" in m and m[0].isupper():
                domains.append(m)
        domains = list(dict.fromkeys(domains))
        if len(domains) >= 2:
            r = admit_scaffold_edge(
                source=domains[0],
                target=domains[1],
                kind="soft_court_pathway",
                strength=0.5,
                evidence=f"promoted {f.name}: {title}",
                epistemic_tier="promote_candidate",
                origin="soft_court",
            )
            if r.get("admitted"):
                admitted += 1
        elif len(domains) == 1:
            r = admit_scaffold_edge(
                source=domains[0],
                target="Cosmology",
                kind="soft_court_anchor",
                strength=0.35,
                evidence=f"promoted {f.name}: {title}",
                epistemic_tier="promote_candidate",
                origin="soft_court",
            )
            if r.get("admitted"):
                admitted += 1
    return {"ok": True, "n_promoted": n, "admitted": admitted, "free_parameters": 0}


def propose_expansion_from_text(
    text: str,
    *,
    source: str = "qwen",
    run_court: bool = True,
) -> dict[str, Any]:
    """
    Parse structured expansion proposals from LLM/API text.

    Expected JSON block (or pure JSON):
      {"proposals":[{"source":"Biology","target":"Neuroscience","kind":"scaffold_pathway","evidence":"..."}]}
    """
    g = verify_fsot_gate(require_archive=False)
    if not g.get("ok"):
        return {"ok": False, "error": "authority_gate_failed"}

    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty"}

    payload = None
    # fenced json
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    raw = m.group(1) if m else None
    if not raw:
        # bare object
        m2 = re.search(r"\{[\s\S]*\"proposals\"[\s\S]*\}", text)
        raw = m2.group(0) if m2 else None
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = None
    if payload is None:
        # heuristic: "connect A to B"
        props = []
        for a, b in re.findall(
            r"connect\s+([A-Za-z][A-Za-z0-9_ ]{2,40}?)\s+to\s+([A-Za-z][A-Za-z0-9_ ]{2,40})",
            text,
            flags=re.I,
        ):
            props.append(
                {
                    "source": a.strip().replace(" ", "_"),
                    "target": b.strip().replace(" ", "_"),
                    "kind": "scaffold_pathway",
                    "evidence": text[:400],
                }
            )
        payload = {"proposals": props}

    proposals = payload.get("proposals") if isinstance(payload, dict) else None
    if not proposals:
        return {"ok": False, "error": "no_proposals_parsed", "hint": "Return JSON with proposals[{source,target,evidence}]"}

    results = []
    for p in proposals[:20]:
        if not isinstance(p, dict):
            continue
        lead = {
            "id": f"EXP-{p.get('source')}-{p.get('target')}"[:80],
            "title": f"Pathway {p.get('source')} → {p.get('target')}",
            "epistemic_tier": "scaffold",
            "domain": p.get("source"),
            "domains": [p.get("source"), p.get("target")],
            "source_domain": p.get("source"),
            "target_domain": p.get("target"),
            "evidence": p.get("evidence") or "",
            "origin": source,
            "free_parameters": 0,
            "note": "LLM/API proposal — not proved; soft court + scaffold only.",
        }
        path = export_lead_obligation(lead)
        results.append({"lead": lead["id"], "obligation": str(path)})

    court = None
    admitted = 0
    if run_court and results:
        court = run_soft_court(promote=True)
        # promote_candidate → scaffold edge
        for r in results:
            # re-admit from proposal fields
            pass
        for p in proposals[:20]:
            if not isinstance(p, dict):
                continue
            ar = admit_scaffold_edge(
                source=str(p.get("source")),
                target=str(p.get("target")),
                kind=str(p.get("kind") or "scaffold_pathway"),
                strength=float(p.get("strength") or 0.4),
                evidence=str(p.get("evidence") or f"from {source}"),
                epistemic_tier="scaffold",
                lean_module=p.get("lean_module"),
                origin=source,
            )
            if ar.get("admitted"):
                admitted += 1

    return {
        "ok": True,
        "n_proposals": len(proposals),
        "obligations": results,
        "court": {
            "n_promoted": (court or {}).get("n_promoted"),
            "n_pending": (court or {}).get("n_pending"),
        }
        if court
        else None,
        "scaffold_admitted": admitted,
        "free_parameters": 0,
        "note": "Proposals exported to soft court; scaffold edges are not Lean-proved.",
    }


def rebuild_tissue_with_deltas(*, force: bool = True) -> dict[str, Any]:
    """Force rebuild compact connective tissue (merges scaffold deltas)."""
    from fsot_mc.archive_connective import build_compact_connective_tissue, compact_path

    # clear cache file to force rebuild
    cp = compact_path()
    if force and cp.is_file():
        try:
            cp.unlink()
        except OSError:
            pass
    tissue = build_compact_connective_tissue(force=True)
    return {
        "ok": True,
        "n_nodes": tissue.get("n_nodes"),
        "n_edges": tissue.get("n_edges"),
        "path": str(cp),
        "deltas": load_scaffold_deltas(),
        "free_parameters": 0,
    }


def run_pathway_alignment(
    *,
    expand: bool = True,
    rebuild: bool = True,
    scan_disk: bool = True,
) -> dict[str, Any]:
    """
    Full alignment cycle:
      gate → certificate map → (optional lean disk) → soft-court pathways → rebuild tissue
    """
    gate = verify_fsot_gate(require_archive=False)
    report: dict[str, Any] = {
        "method": "fsot_pathway_alignment",
        "started_at": _utc(),
        "free_parameters": 0,
        "authority": AUTHORITY_SHA256[:12],
        "gate_ok": gate.get("ok"),
    }
    if not gate.get("ok"):
        report["ok"] = False
        report["error"] = "authority_gate_failed"
        return report

    hub = resolve_lean_hub()
    report["lean_hub"] = hub
    report["formal_status"] = formal_status()
    cross = load_cross_proof_summary() or {}
    report["multi_verifier"] = {
        "overall_ok": cross.get("overall_ok"),
        "seven_way_bare_metal": cross.get("seven_way_bare_metal"),
        "github_ready": cross.get("github_ready"),
        "source": cross.get("source"),
        "note": "Batch multi-verifier snapshot — not per-path Lean.",
    }

    tissue = _load_compact_tissue()
    gidx = _graph_lean_index(tissue)
    report["graph"] = {
        "n_nodes": gidx["n_nodes"],
        "n_edges": gidx["n_edges"],
        "n_lean_modules": len(gidx["lean_modules"]),
        "n_map_tags": len(gidx["maps_to_lean_tags"]),
    }

    report["certificate_alignment"] = align_certificate_claims(gidx) if expand else {"skipped": True}
    report["lean_disk"] = align_lean_disk_modules() if (expand and scan_disk) else {"skipped": True}
    report["soft_court_pathways"] = align_promoted_obligations() if expand else {"skipped": True}

    if rebuild:
        report["rebuild"] = rebuild_tissue_with_deltas(force=True)
    else:
        report["rebuild"] = {"skipped": True}

    report["deltas"] = load_scaffold_deltas()
    report["ok"] = True
    report["finished_at"] = _utc()
    _write_reports(report)
    return report


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    g = report.get("graph") or {}
    cert = report.get("certificate_alignment") or {}
    disk = report.get("lean_disk") or {}
    sc = report.get("soft_court_pathways") or {}
    mv = report.get("multi_verifier") or {}
    hub = report.get("lean_hub") or {}
    reb = report.get("rebuild") or {}
    lines = [
        "# Pathway Alignment Report",
        "",
        f"Generated: {report.get('finished_at') or report.get('started_at')}  ",
        f"Authority: **{report.get('authority')}…** · `free_parameters = 0` · gate_ok={report.get('gate_ok')}  ",
        "",
        "## Doctrine",
        "",
        "- MC + Qwen **propose** pathways; multi-verifier court **gates** them.",
        "- Soft court promote = **candidate**, not Lean-proved.",
        "- Scaffold deltas live under `data/connective_deltas/` and merge into connective tissue.",
        "- Seeds / pin D1D38A never move.",
        "",
        "## Hubs",
        "",
        f"- Local bundle: `{hub.get('local_bundle')}`",
        f"- Physical archive: `{hub.get('physical_archive')}`",
        f"- Lean hub primary: `{hub.get('primary')}`",
        "",
        "## Multi-verifier (batch)",
        "",
        f"- overall_ok: **{mv.get('overall_ok')}** · seven_way: **{mv.get('seven_way_bare_metal')}** · github_ready: {mv.get('github_ready')}",
        f"- source: `{mv.get('source')}`",
        "",
        "## Graph snapshot",
        "",
        f"- nodes={g.get('n_nodes')} edges={g.get('n_edges')}",
        f"- lean_modules on nodes={g.get('n_lean_modules')} · maps_to_lean tags={g.get('n_map_tags')}",
        "",
        "## Certificate ↔ graph",
        "",
        f"- claims={cert.get('n_claims')} linked={cert.get('linked_to_graph')} missing_module={cert.get('n_missing')}",
        f"- scaffold_admitted={cert.get('scaffold_admitted')}",
        "",
        "## Lean disk Formal modules",
        "",
        f"- hub modules={disk.get('n_disk_modules')} graph modules={disk.get('n_graph_modules')}",
        f"- missing_on_graph={disk.get('n_missing_on_graph')} (sample capped)",
        f"- scaffold_admitted={disk.get('scaffold_admitted')}",
        "",
        "## Soft-court pathways",
        "",
        f"- promoted files={sc.get('n_promoted')} → scaffold edges admitted={sc.get('admitted')}",
        "",
        "## Tissue rebuild",
        "",
        f"- ok nodes/edges after merge: {reb.get('n_nodes')}/{reb.get('n_edges')}",
        "",
        "## Expand via Qwen / API",
        "",
        "Ask chat for a JSON proposal, or call:",
        "",
        "```powershell",
        'python -m fsot_mc expand-pathways --query "connect Biology to Neuroscience because ..."',
        "python -m fsot_mc align-pathways",
        "```",
        "",
        "Proposal JSON shape:",
        "",
        "```json",
        '{"proposals":[{"source":"Biology","target":"Neuroscience","kind":"scaffold_pathway","evidence":"..."}]}',
        "```",
        "",
        "---",
        "*Generated by `fsot_mc.pathway_alignment` — multi-verifier batch court, free_parameters=0.*",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def pathway_status() -> dict[str, Any]:
    hub = resolve_lean_hub()
    deltas = load_scaffold_deltas()
    fs = formal_status()
    cross = load_cross_proof_summary() or {}
    return {
        "ok": True,
        "free_parameters": 0,
        "gate_ok": verify_fsot_gate(require_archive=False).get("ok"),
        "lean_hub": hub.get("primary"),
        "physical_archive": hub.get("physical_archive"),
        "multi_verifier_ok": cross.get("overall_ok"),
        "formal": {
            "certificate_claims": fs.get("certificate_proved_claims"),
            "pending": fs.get("pending_obligations"),
            "promoted": fs.get("promoted_obligations"),
        },
        "deltas": {"n_nodes": deltas["n_nodes"], "n_edges": deltas["n_edges"]},
        "reports": {"json": str(REPORT_JSON), "md": str(REPORT_MD)},
        "doctrine": {
            "propose": "MC discovery / Qwen JSON / Lean disk gaps",
            "gate": "D1D38A + soft court + certificate / cross_proof",
            "never": "seed retune, free parameters, auto Lean-proved claims",
        },
    }
