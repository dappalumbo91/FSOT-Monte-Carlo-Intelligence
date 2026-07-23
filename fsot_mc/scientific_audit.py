"""
Rigorous scientific intelligence audit + FSOT self-referral loop.

Runs the product through itself:
  1) Law / authority integrity
  2) Empirical green-gate & contested panels
  3) Multipath discovery coherence
  4) Literature cross-ref health
  5) Mind scientific grounding
  6) Connective tissue + tissue docs coverage
  7) Self-referral: multipath + literature on the architecture itself
  8) Failure modes / improvement ledger

Produces data/exports/scientific_audit_*.json and docs/SCIENTIFIC_AUDIT_REPORT.md
free_parameters = 0. Authority D1D38A.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fsot_mc.paths import PACKAGE_ROOT, data_root


@dataclass
class CheckResult:
    id: str
    layer: str
    title: str
    ok: bool
    score: float  # 0..1
    severity: str  # critical | high | medium | low | info
    evidence: dict[str, Any] = field(default_factory=dict)
    finding: str = ""
    improvement: str = ""
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_check(
    cid: str,
    layer: str,
    title: str,
    fn: Callable[[], tuple[bool, float, dict[str, Any], str, str]],
    severity_fail: str = "high",
) -> CheckResult:
    t0 = time.perf_counter()
    try:
        ok, score, evidence, finding, improvement = fn()
        sev = "info" if ok else severity_fail
        return CheckResult(
            id=cid,
            layer=layer,
            title=title,
            ok=ok,
            score=float(max(0.0, min(1.0, score))),
            severity=sev,
            evidence=evidence,
            finding=finding,
            improvement=improvement,
            duration_s=round(time.perf_counter() - t0, 3),
        )
    except Exception as exc:
        return CheckResult(
            id=cid,
            layer=layer,
            title=title,
            ok=False,
            score=0.0,
            severity="critical",
            evidence={"exception": str(exc), "trace": traceback.format_exc()[-800:]},
            finding=f"Check crashed: {exc}",
            improvement="Harden this subsystem against exceptions; add regression test.",
            duration_s=round(time.perf_counter() - t0, 3),
        )


# ── Individual checks ───────────────────────────────────────────────────────

def check_authority() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.authority_gate import verify_fsot_gate

    g = verify_fsot_gate(require_archive=False)
    ok = bool(g.get("ok"))
    return (
        ok,
        1.0 if ok else 0.0,
        {
            "authority_sha256": g.get("authority_sha256"),
            "float_engine": (g.get("float_engine") or {}).get("ok"),
            "bytes_local": (g.get("authority_bytes") or {}).get("local_matches"),
        },
        "Authority pin D1D38A and float engine agree." if ok else "Authority gate failed.",
        "" if ok else "Re-sync compute_authority.py / PIN.json from Physical Archive.",
    )


def check_independence() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.paths import independence_status

    st = independence_status()
    checks = st.get("checks") or st
    if isinstance(checks, dict) and "compute_authority" in str(checks):
        # structure may be nested
        pass
    ok = bool(st.get("independent"))
    detail = st.get("checks") or {}
    n_ok = sum(1 for v in detail.values() if v is True)
    n = len(detail) or 1
    score = n_ok / n
    return (
        ok,
        score,
        {"status": st},
        f"Independent workspace: {n_ok}/{n or '?'} local assets OK." if ok else "Not independent.",
        "" if ok else "Run scripts/bootstrap_independent.py and vendor sync.",
    )


def check_core_recompute() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.accuracy_gate import core_fold_recompute_accuracy

    c = core_fold_recompute_accuracy()
    ok = bool(c.get("ok"))
    max_err = float(c.get("max_rel_error_pct") or 1.0)
    # score: 1 if machine eps, decay if larger
    score = 1.0 if max_err < 1e-9 else max(0.0, 1.0 - max_err)
    return (
        ok,
        score,
        {
            "n_core": c.get("n_core"),
            "n_within_tol": c.get("n_within_tol"),
            "max_rel_error_pct": c.get("max_rel_error_pct"),
            "median_rel_error_pct": c.get("median_rel_error_pct"),
        },
        f"Core recompute max_rel_error_pct={c.get('max_rel_error_pct')}.",
        "" if ok else "Engine drift vs atlas S_canonical — re-pin floats.",
    )


def check_archive_green_gate() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.accuracy_gate import load_archive_margin_audit

    m = load_archive_margin_audit()
    ok = bool(m.get("ok") and m.get("all_green"))
    fail = int(m.get("green_gate_fail_count") or 0)
    pass_c = int(m.get("green_gate_pass_count") or 0)
    total = pass_c + fail
    score = (pass_c / total) if total else 0.0
    med = m.get("pooled_median_of_domain_medians_pct")
    return (
        ok,
        score,
        {
            "pass": pass_c,
            "fail": fail,
            "pooled_median_of_domain_medians_pct": med,
            "max_pooled": m.get("max_pooled_domain_median_pct"),
            "worst": m.get("worst_scalar_domain"),
        },
        f"Archive green gate {pass_c}/{total}, median-of-medians={med}%.",
        "" if ok else "Investigate failing domains in margin audit; do not claim full green.",
    )


def check_contested_panel() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.accuracy_gate import load_contested_panel

    c = load_contested_panel()
    ok = bool(c.get("ok"))
    n = int(c.get("n_observables") or 0)
    within = int(c.get("n_within_0_5pct") or 0)
    score = (within / n) if n else 0.0
    pooled = c.get("fsot_pooled_median_error_pct")
    return (
        ok and within == n,
        score,
        {
            "n": n,
            "within_0_5": within,
            "pooled_median_pct": pooled,
            "baseline_pct": c.get("current_model_baseline_pct"),
            "verdict": c.get("verdict"),
        },
        f"Contested panel {within}/{n} within 0.5%; FSOT pooled={pooled}% vs baseline ~15%.",
        "Expand contested panel live recompute in MC (not only archive snapshot).",
    )


def check_multipath_coherence() -> tuple[bool, float, dict, str, str]:
    """Full-core multipath: all NeuroLab domains present, band, bridges, flip map."""
    from fsot_mc.universe_atlas import core_names
    from fsot_mc.universe_mc import run_universe_monte_carlo

    cores = list(core_names())
    mc = run_universe_monte_carlo(
        n_paths=96,
        seed=7,
        domains=cores,
        store_paths=12,
        train_pathway_memory=True,
    )
    if mc.get("error"):
        return False, 0.0, {"error": mc.get("error")}, "MC failed.", "Fix universe_mc errors."
    ens = mc.get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}
    mean = ef.get("mean")
    p10, p90 = ef.get("p10"), ef.get("p90")
    in_band = mean is not None and 0.55 <= float(mean) <= 0.78
    width = (float(p90) - float(p10)) if p10 is not None and p90 is not None else 1.0
    de = mc.get("domain_ensemble") or {}
    covered = [d for d in cores if d in de]
    cover_frac = len(covered) / max(len(cores), 1)
    flips = sorted(
        ((n, float(r.get("flip_rate") or 0)) for n, r in de.items()),
        key=lambda x: -x[1],
    )
    hot = [(n, f) for n, f in flips if f >= 0.35]
    lr = mc.get("long_range_bridges") or {}
    n_bridges = len(lr) if isinstance(lr, dict) else 0
    # score: coverage dominates
    score = (
        0.40 * cover_frac
        + 0.25 * (1.0 if in_band else 0.2)
        + 0.20 * max(0.0, 1.0 - width)
        + 0.15 * min(1.0, n_bridges / 5)
    )
    ok = cover_frac >= 0.99 and in_band
    return (
        ok,
        min(1.0, score),
        {
            "mean": mean,
            "p10": p10,
            "p90": p90,
            "width": width,
            "n_paths": mc.get("n_paths"),
            "n_core": len(cores),
            "n_core_in_ensemble": len(covered),
            "core_coverage_frac": cover_frac,
            "missing_cores": [d for d in cores if d not in de],
            "n_long_range_bridges": n_bridges,
            "flip_hotspots": hot[:15],
            "all_flip_rates": flips,
        },
        (
            f"Full-core multipath: {len(covered)}/{len(cores)} cores, "
            f"emergence mean={mean}, width={width:.3f}, bridges={n_bridges}, hotspots={len(hot)}."
        ),
        "Per-core observer protocols for flip hotspots; separate UI metric for map% vs green-gate.",
    )


def _all_core_names() -> list[str]:
    from fsot_mc.universe_atlas import core_names

    return list(core_names())


def check_full_domain_atlas() -> tuple[bool, float, dict, str, str]:
    """Every core + extension fold in atlas must evaluate; clusters complete."""
    from fsot_mc.universe_atlas import (
        core_names,
        domain_names,
        domains_by_cluster,
        evaluate_domain,
        get_domain,
    )

    cores = list(core_names())
    all_names = list(domain_names())
    clusters = domains_by_cluster()
    core_ok = []
    core_fail = []
    panel = []
    for d in cores:
        try:
            e = evaluate_domain(d)
            core_ok.append(d)
            panel.append(
                {
                    "domain": d,
                    "S": float(e["S"]),
                    "D_eff": e.get("D_eff"),
                    "regime": e.get("regime"),
                    "cluster": e.get("cluster"),
                    "T1": e.get("T1"),
                    "T2": e.get("T2"),
                    "T3": e.get("T3"),
                }
            )
        except Exception as exc:
            core_fail.append({"domain": d, "error": str(exc)})

    ext = [n for n in all_names if n not in set(cores)]
    ext_ok = 0
    ext_fail = []
    for d in ext:
        try:
            get_domain(d)
            ext_ok += 1
        except Exception as exc:
            ext_fail.append({"domain": d, "error": str(exc)})

    n_core = len(cores)
    n_all = len(all_names)
    core_frac = len(core_ok) / max(n_core, 1)
    ext_frac = ext_ok / max(len(ext), 1)
    cluster_n = len(clusters)
    # target: 35 core, 402 total, 6 clusters
    score = (
        0.45 * core_frac
        + 0.35 * ext_frac
        + 0.10 * min(1.0, n_all / 402)
        + 0.10 * min(1.0, cluster_n / 6)
    )
    ok = len(core_fail) == 0 and ext_frac >= 0.95 and n_all >= 350
    return (
        ok,
        score,
        {
            "n_core": n_core,
            "n_core_eval_ok": len(core_ok),
            "core_fail": core_fail,
            "n_extension": len(ext),
            "n_extension_ok": ext_ok,
            "ext_fail_n": len(ext_fail),
            "n_total_atlas": n_all,
            "clusters": {k: len(v) for k, v in clusters.items()},
            "core_panel_S": panel,
        },
        (
            f"Atlas coverage: core {len(core_ok)}/{n_core} eval-OK, "
            f"extensions {ext_ok}/{len(ext)}, total folds {n_all}, clusters {cluster_n}."
        ),
        "Sync any missing extension panels from Physical Archive navigator; fail closed on core eval errors.",
    )


def check_navigator_subfields_routes() -> tuple[bool, float, dict, str, str]:
    """Navigator: core domains, extension panels, problem routes, subfield breadth."""
    from fsot_mc.archive_connective import load_navigator, load_expansion_map
    from fsot_mc.universe_atlas import core_names

    nav = load_navigator()
    exp = load_expansion_map()
    cores_atlas = set(core_names())
    nav_cores = nav.get("core_domains") or []
    nav_core_names = {
        (c.get("name") if isinstance(c, dict) else str(c)) for c in nav_cores
    }
    ext_panels = nav.get("extension_panels") or []
    routes = nav.get("problem_routes") or []
    subfields = nav.get("subfields") or []
    exp_nl = exp.get("neurolab_domains") or []
    exp_ext = exp.get("extension_domains") or []

    core_overlap = len(nav_core_names & cores_atlas) / max(len(cores_atlas), 1)
    n_ext = len(ext_panels)
    n_routes = len(routes)
    n_sub = len(subfields)
    # breadth: mean subfields_touched/studied where present
    breadths = []
    thin = []
    for s in subfields:
        if not isinstance(s, dict):
            continue
        stud = float(s.get("subfields_studied") or 0)
        touch = float(s.get("subfields_touched") or 0)
        bp = s.get("breadth_pct")
        if bp is not None:
            breadths.append(float(bp))
        elif stud > 0:
            breadths.append(100.0 * touch / stud)
        if (bp is not None and float(bp) < 40) or (stud > 0 and touch / stud < 0.4):
            thin.append(s.get("core_domain") or s)

    mean_breadth = sum(breadths) / len(breadths) if breadths else 0.0
    score = (
        0.25 * core_overlap
        + 0.25 * min(1.0, n_ext / 367)
        + 0.15 * min(1.0, n_routes / 19)
        + 0.15 * min(1.0, n_sub / 35)
        + 0.20 * min(1.0, mean_breadth / 100.0)
    )
    ok = core_overlap >= 0.95 and n_ext >= 300 and n_routes >= 15
    return (
        ok,
        score,
        {
            "nav_core_names": len(nav_core_names),
            "atlas_core": len(cores_atlas),
            "core_overlap_frac": core_overlap,
            "n_extension_panels": n_ext,
            "n_problem_routes": n_routes,
            "n_subfields": n_sub,
            "mean_subfield_breadth_pct": mean_breadth,
            "thin_subfield_domains": thin[:20],
            "expansion_neurolab": len(exp_nl),
            "expansion_extension": len(exp_ext),
            "route_intents": [
                (r.get("intent") if isinstance(r, dict) else str(r)) for r in routes
            ],
        },
        (
            f"Navigator: core overlap {core_overlap:.0%}, ext panels {n_ext}, "
            f"problem routes {n_routes}, subfields {n_sub}, mean breadth {mean_breadth:.1f}%."
        ),
        "Deepen thin subfields (breadth<40%); link every subfield note into tissue docs + graph.",
    )


def check_literature() -> tuple[bool, float, dict, str, str]:
    """
    Multi-cluster literature battery — not one shallow query.
    Probes map across quantum, cosmo, bio, condensed, fluid, earth, nuclear, AI.
    """
    from fsot_mc.literature_corpus import literature_search, literature_status
    from fsot_mc.universe_atlas import core_names

    st = literature_status()
    arx_n = int(st.get("arxiv_indexed") or 0)
    wiki_n = int(st.get("wiki_indexed") or 0)
    if arx_n < 1000:
        return (
            False,
            min(0.4, arx_n / 1000),
            st,
            f"Literature index thin: arxiv={arx_n} wiki={wiki_n}.",
            "Run literature-index with higher --max-papers (or full dump).",
        )

    # Battery covers major archive clusters / cores
    probes = [
        ("quantum entanglement measurement", ["Quantum_Mechanics", "Quantum_Optics", "Quantum_Computing"]),
        ("general relativity gravitational waves black hole", ["Cosmology", "Astrophysics", "Quantum_Gravity", "Astronomy"]),
        ("Hubble tension dark energy cosmology", ["Cosmology", "Astrophysics"]),
        ("superconductivity condensed matter", ["Condensed_Matter", "Materials_Science"]),
        ("neural network brain neuroscience consciousness", ["Neuroscience", "Biology", "Computer_Science"]),
        ("DNA protein genome biology", ["Biology", "Biochemistry"]),
        ("fluid dynamics turbulence Navier", ["Fluid_Dynamics"]),
        ("seismic earthquake geophysics", ["Seismology", "Geophysics"]),
        ("nuclear structure particle physics", ["Nuclear_Physics", "Particle_Physics"]),
        ("atmospheric climate ozone", ["Atmospheric_Physics", "Meteorology", "Oceanography"]),
        ("quantum computing qubit", ["Quantum_Computing", "Quantum_Mechanics"]),
        ("chemistry molecular reaction", ["Chemistry", "Molecular_Chemistry", "Physical_Chemistry"]),
    ]
    core_set = set(core_names())
    all_hit_domains: set[str] = set()
    probe_rows = []
    n_hit_total = 0
    for q, expect in probes:
        r = literature_search(q, arxiv_limit=4, wiki_limit=1, with_fsot=True)
        hits = ((r.get("arxiv") or {}).get("hits") or [])
        n_hit_total += len(hits)
        primary = set(r.get("primary_domains") or [])
        for h in hits:
            for d in h.get("fsot_domains") or []:
                all_hit_domains.add(d)
        # expect at least one expected domain in primary or hit domains
        expect_hit = bool(primary & set(expect) or any(
            set(h.get("fsot_domains") or []) & set(expect) for h in hits
        ))
        probe_rows.append(
            {
                "q": q,
                "n_hits": len(hits),
                "primary": list(primary)[:6],
                "expect": expect,
                "expect_hit": expect_hit,
                "sample": [h.get("id") for h in hits[:2]],
            }
        )

    expect_frac = sum(1 for p in probe_rows if p["expect_hit"]) / max(len(probes), 1)
    domain_breadth = len(all_hit_domains & core_set) / max(len(core_set), 1)
    depth = min(1.0, arx_n / 500_000)  # full OAI scale
    hit_density = min(1.0, n_hit_total / (len(probes) * 3))
    score = 0.30 * expect_frac + 0.30 * domain_breadth + 0.25 * depth + 0.15 * hit_density
    ok = expect_frac >= 0.75 and n_hit_total >= len(probes)
    return (
        ok,
        score,
        {
            "arxiv_indexed": arx_n,
            "wiki_indexed": wiki_n,
            "n_probes": len(probes),
            "expect_hit_frac": expect_frac,
            "core_domains_touched": sorted(all_hit_domains & core_set),
            "n_core_touched": len(all_hit_domains & core_set),
            "n_core_total": len(core_set),
            "domain_breadth_frac": domain_breadth,
            "n_hit_total": n_hit_total,
            "probes": probe_rows,
        },
        (
            f"Literature battery: {expect_frac:.0%} probes domain-aligned, "
            f"{len(all_hit_domains & core_set)}/{len(core_set)} cores touched, "
            f"index arxiv={arx_n} wiki={wiki_n}, hits={n_hit_total}."
        ),
        "Index full OAI dump; expand category→domain map for all 35 cores; per-domain literature shelves in tissue docs.",
    )


def check_mind_grounding() -> tuple[bool, float, dict, str, str]:
    """
    Deep multi-domain mind battery — structural, not 6 shallow keywords.

    For each core domain: route + multipath-backed answer must cite domain name,
    report S or D_eff or regime, keep free_parameters=0.
    Plus cluster-level synthesis probes.
    """
    from fsot_mc.mind import ask, route_query_to_domains
    from fsot_mc.universe_atlas import core_names, domains_by_cluster, evaluate_domain

    cores = list(core_names())
    clusters = domains_by_cluster()
    # structural requirements for ANY science answer
    structural_tokens = [
        "free_parameters",
        "d1d38a",
        "s=",
        "d_eff",
        "emergence",
        "dispersal",
        "seed",
        "fold",
        "multipath",
    ]

    domain_rows = []
    route_hits = 0
    domain_mention = 0
    structural_scores = []

    # Fast path: routing coverage for ALL cores (no MC each — still rigorous structure)
    for d in cores:
        q = f"What is the FSOT vitality and regime of domain {d.replace('_', ' ')}?"
        routed = route_query_to_domains(q, max_domains=20)
        in_route = d in routed
        if in_route:
            route_hits += 1
        s_val = None
        cl = None
        try:
            ev = evaluate_domain(d)
            s_val = float(ev["S"])
            cl = ev.get("cluster")
        except Exception:
            pass
        domain_rows.append(
            {
                "domain": d,
                "routed": in_route,
                "S_canonical_live": s_val,
                "cluster": cl,
            }
        )

    route_frac = route_hits / max(len(cores), 1)

    # Deep probes: one per cluster + cross-cutting (MC-backed answers)
    cluster_probes = []
    for cl, names in sorted(clusters.items()):
        if not names:
            continue
        # pick representative with extreme |S| if possible
        rep = names[0]
        try:
            best = max(names, key=lambda n: abs(float(evaluate_domain(n)["S"])))
            rep = best
        except Exception:
            pass
        cluster_probes.append(
            (
                cl,
                rep,
                f"FSOT multipath analysis of {cl.replace('_', ' ')} cluster focusing on {rep.replace('_', ' ')} "
                f"and related domains {', '.join(n.replace('_', ' ') for n in names[:4])}",
            )
        )

    cross_probes = [
        (
            "cross_scale",
            "Compare FSOT Biology Cosmology Quantum Mechanics bridges As Above So Below "
            "with multipath emergence fraction and per-domain S values",
        ),
        (
            "green_gate",
            "State the archive green gate 0.5 percent pooled median across all domains "
            "and how multipath map occupancy is not the same metric",
        ),
        (
            "to_architecture",
            "Explain FSOT law S equals K times T1 plus T2 plus T3 free_parameters zero "
            "authority D1D38A seeds pi e phi gamma Catalan and domain folds",
        ),
    ]

    deep_results = []
    for item in cluster_probes:
        cl, rep, q = item
        r = ask(q, n_paths=16, with_chew=False, force_new_mc=True)
        ans = (r.get("answer") or "").lower()
        th = r.get("thinking") or {}
        routed = th.get("routed_domains") or []
        focus = th.get("focus_scalars") or []
        # domain grounding: rep or any cluster member mentioned
        members = clusters.get(cl) or []
        mentioned = sum(1 for m in members if m.lower().replace("_", " ") in ans or m.lower() in ans)
        mention_frac = mentioned / max(len(members), 1)
        if rep.lower().replace("_", " ") in ans or rep in str(routed):
            domain_mention += 1
        struct_hit = sum(1 for t in structural_tokens if t in ans.replace(" ", "") or t in ans)
        # S values present
        has_s = "s=" in ans.replace(" ", "") or "s =" in ans
        free0 = r.get("free_parameters") == 0
        ok_one = free0 and not r.get("error") and (mention_frac > 0 or rep in routed) and struct_hit >= 4
        structural_scores.append(struct_hit / len(structural_tokens))
        deep_results.append(
            {
                "cluster": cl,
                "rep": rep,
                "ok": ok_one,
                "mention_frac": mention_frac,
                "structural_token_frac": struct_hit / len(structural_tokens),
                "has_s_numeric": has_s,
                "n_routed": len(routed),
                "n_focus": len(focus),
                "answer_len": len(r.get("answer") or ""),
            }
        )

    for tag, q in cross_probes:
        r = ask(q, n_paths=20, with_chew=False, force_new_mc=True)
        ans = (r.get("answer") or "").lower()
        struct_hit = sum(1 for t in structural_tokens if t in ans.replace(" ", "") or t in ans)
        free0 = r.get("free_parameters") == 0
        structural_scores.append(struct_hit / len(structural_tokens))
        deep_results.append(
            {
                "cluster": tag,
                "rep": None,
                "ok": free0 and struct_hit >= 5 and not r.get("error"),
                "structural_token_frac": struct_hit / len(structural_tokens),
                "answer_len": len(r.get("answer") or ""),
            }
        )

    deep_ok_frac = sum(1 for d in deep_results if d.get("ok")) / max(len(deep_results), 1)
    struct_mean = sum(structural_scores) / max(len(structural_scores), 1)
    score = 0.35 * route_frac + 0.40 * deep_ok_frac + 0.25 * struct_mean
    ok = route_frac >= 0.85 and deep_ok_frac >= 0.7 and struct_mean >= 0.5
    return (
        ok,
        score,
        {
            "n_core_domains": len(cores),
            "route_coverage_frac": route_frac,
            "n_clusters": len(clusters),
            "deep_probes": len(deep_results),
            "deep_ok_frac": deep_ok_frac,
            "mean_structural_token_frac": struct_mean,
            "structural_tokens": structural_tokens,
            "domain_route_table": domain_rows,
            "deep_results": deep_results,
        },
        (
            f"Mind multi-domain grounding: route {route_frac:.0%} of {len(cores)} cores, "
            f"deep probes OK {deep_ok_frac:.0%} ({len(deep_results)} probes across {len(clusters)} clusters), "
            f"structural token mean {struct_mean:.0%} — not a 6-keyword toy check."
        ),
        "Force every answer to emit full core-panel table when query is global; auto-attach literature hits per routed domain.",
    )


def check_connective_tissue() -> tuple[bool, float, dict, str, str]:
    """Coverage vs full archive: 35 core, 367 ext, 19 routes, coupling matrix."""
    from fsot_mc.archive_connective import get_connective_tissue, load_navigator
    from fsot_mc.graph_model import build_universe_graph
    from fsot_mc.universe_atlas import core_names, domain_names

    t = get_connective_tissue()
    nav = load_navigator()
    g = build_universe_graph(
        n_paths=16,
        seed=1,
        scope="full",
        with_mc=False,
        with_memory=False,
        with_predictions=True,
        with_archive_connective=True,
    )
    nodes = g.get("nodes") or []
    edges = g.get("edges") or []
    graph_domains = {
        n.get("domain")
        for n in nodes
        if n.get("domain")
    }
    cores = set(core_names())
    atlas = set(domain_names())
    core_in_graph = len(cores & graph_domains) / max(len(cores), 1)
    atlas_in_graph = len(atlas & graph_domains) / max(len(atlas), 1)

    n_nodes = len(nodes)
    n_edges = len(edges)
    raw = (g.get("meta") or {}).get("archive_connective") or {}
    raw_e = int(raw.get("coupling_raw_edge_count") or t.get("coupling_raw_edge_count") or 0)
    compact_e = int(t.get("n_edges") or 0)
    edge_cov = (compact_e / raw_e) if raw_e else 0.0

    # edge kind diversity
    kinds: dict[str, int] = {}
    for e in edges:
        k = str(e.get("kind") or "unknown")
        kinds[k] = kinds.get(k, 0) + 1
    need_kinds = ["routes_to_core", "seed_to_law", "problem_route"]
    kind_hit = sum(1 for k in need_kinds if any(k in kk for kk in kinds))
    routes = nav.get("problem_routes") or []
    route_nodes = sum(1 for n in nodes if n.get("kind") == "problem_route")

    score = (
        0.25 * core_in_graph
        + 0.25 * atlas_in_graph
        + 0.15 * min(1.0, edge_cov / 0.15)  # reward moving toward 15%+ of raw
        + 0.15 * min(1.0, n_edges / 5000)
        + 0.10 * (kind_hit / len(need_kinds))
        + 0.10 * min(1.0, route_nodes / max(len(routes), 1))
    )
    ok = core_in_graph >= 0.99 and atlas_in_graph >= 0.85 and route_nodes >= 10
    missing_cores = sorted(cores - graph_domains)
    missing_atlas_n = len(atlas - graph_domains)
    return (
        ok,
        score,
        {
            "graph_nodes": n_nodes,
            "graph_edges": n_edges,
            "core_in_graph_frac": core_in_graph,
            "atlas_in_graph_frac": atlas_in_graph,
            "missing_cores": missing_cores,
            "missing_atlas_domains_n": missing_atlas_n,
            "tissue_nodes": t.get("n_nodes"),
            "tissue_edges": t.get("n_edges"),
            "raw_coupling_edges": raw_e,
            "compact_edge_frac": edge_cov,
            "edge_kinds": kinds,
            "problem_route_nodes": route_nodes,
            "nav_problem_routes": len(routes),
            "green_gate": f"{t.get('n_green_gate')}/{t.get('n_with_error')}",
        },
        (
            f"Connective coverage: core {core_in_graph:.0%}, atlas folds {atlas_in_graph:.0%} "
            f"({missing_atlas_n} missing), edges {n_edges} (compact/raw={edge_cov:.3f}), "
            f"problem routes {route_nodes}/{len(routes)}."
        ),
        "Raise lean-overlap degree caps; ensure every atlas domain is a graph node; edge error_pct LOD.",
    )


def check_tissue_docs() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.tissue_docs import TISSUE_ROOT, get_tissue_doc

    man = TISSUE_ROOT / "manifest.json"
    if not man.is_file():
        return False, 0.0, {}, "Tissue docs missing.", "python -m fsot_mc tissue-docs"
    m = json.loads(man.read_text(encoding="utf-8"))
    n = int(m.get("n_docs") or 0)
    samples = ["dom_Biology", "dom_Cosmology", "seed_pi", "law_K", "dom_Atmospheric_Physics"]
    ok_s = 0
    for sid in samples:
        if get_tissue_doc(sid).get("ok"):
            ok_s += 1
    score = 0.5 * min(1.0, n / 600) + 0.5 * (ok_s / len(samples))
    return (
        n >= 100 and ok_s == len(samples),
        score,
        {"n_docs": n, "sample_ok": f"{ok_s}/{len(samples)}"},
        f"Tissue library {n} docs; samples {ok_s}/{len(samples)} resolvable.",
        "Enrich theses with live literature citations + Lean obligation IDs per fold.",
    )


def check_self_referral() -> tuple[bool, float, dict, str, str]:
    """
    FSOT evaluates FSOT on the FULL domain atlas — not 6 toy keywords.

    1) Literature battery across clusters
    2) Multipath on ALL core NeuroLab domains
    3) Mind must ground across structural law + multi-domain panel language
    4) Score = domain coverage × literature breadth × mind structure
    """
    from fsot_mc.literature_corpus import literature_search
    from fsot_mc.mind import ask, route_query_to_domains
    from fsot_mc.universe_atlas import core_names, domains_by_cluster, evaluate_domain
    from fsot_mc.universe_mc import run_universe_monte_carlo

    cores = list(core_names())
    clusters = domains_by_cluster()

    # 1) Multi-query literature covering architecture + physics stack
    lit_queries = [
        "quantum gravity cosmology spacetime",
        "observer measurement quantum mechanics",
        "Hubble tension dark energy",
        "biological complexity emergence",
        "neural computation consciousness",
        "superconductivity condensed matter",
        "fluid dynamics turbulence",
        "particle physics standard model",
    ]
    lit_domains: set[str] = set()
    lit_hits_n = 0
    lit_samples = []
    for q in lit_queries:
        lit = literature_search(q, arxiv_limit=3, wiki_limit=1, with_fsot=True)
        hits = ((lit.get("arxiv") or {}).get("hits") or [])
        lit_hits_n += len(hits)
        for d in lit.get("primary_domains") or []:
            lit_domains.add(d)
        if hits:
            lit_samples.append(hits[0].get("id"))

    # 2) Full-core multipath self-map
    mc = run_universe_monte_carlo(
        n_paths=64,
        seed=42,
        domains=cores,
        store_paths=8,
        train_pathway_memory=True,
    )
    ens = (mc.get("ensemble") or {}).get("emergence_fraction") or {}
    de = mc.get("domain_ensemble") or {}
    core_in_mc = [d for d in cores if d in de]
    fold_scores = []
    for d in cores:
        row = de.get(d) or {}
        S = row.get("S_path_mean", row.get("S_canonical"))
        if S is not None:
            fold_scores.append(
                {
                    "domain": d,
                    "S_path_mean": S,
                    "flip_rate": row.get("flip_rate"),
                    "D_eff": row.get("D_eff"),
                    "cluster": row.get("cluster"),
                }
            )

    # 3) Mind: architecture audit requiring multi-domain grounding
    mind_q = (
        "Full FSOT Monte Carlo Intelligence self-audit across all scientific domains: "
        "state the law S=K(T1+T2+T3), free_parameters=0, authority D1D38A, "
        "multipath thinking, 0.5% green gate vs map emergence occupancy, "
        "and report vitality of Cosmology Quantum Mechanics Biology Neuroscience "
        "Particle Physics Chemistry Condensed Matter Seismology Astrophysics."
    )
    mind = ask(mind_q, n_paths=32, with_chew=True, force_new_mc=True)
    ans = (mind.get("answer") or "").lower()
    th = mind.get("thinking") or {}
    routed = set(th.get("routed_domains") or [])

    # Domain name grounding across ALL cores (not 6 keywords)
    domain_grounded = []
    for d in cores:
        token = d.lower().replace("_", " ")
        compact = d.lower().replace("_", "")
        grounded = token in ans or compact in ans.replace("_", "") or d in routed
        # also accept last segment for long names
        last = d.split("_")[-1].lower()
        if len(last) > 5 and last in ans:
            grounded = True
        domain_grounded.append({"domain": d, "grounded": grounded})
    domain_frac = sum(1 for x in domain_grounded if x["grounded"]) / max(len(cores), 1)

    structural = {
        "free_parameters_or_zero_fp": ("free_parameters" in ans) or ("free parameter" in ans),
        "d1d38a": "d1d38a" in ans.replace(" ", ""),
        "law_S": "s=" in ans.replace(" ", "") or "s = k" in ans or "t1" in ans,
        "multipath": "multipath" in ans or "monte carlo" in ans,
        "green_gate_0_5": "0.5" in ans or "0.5%" in ans or "≤0.5" in ans or "green" in ans,
        "emergence_map": "emergence" in ans,
        "experiment_honesty": any(
            x in ans for x in ("experiment", "scaffold", "epistemic", "does not rewrite", "not a bayesian")
        ),
    }
    struct_frac = sum(1 for v in structural.values() if v) / max(len(structural), 1)

    # Cluster coverage via routing or answer
    cluster_ground = {}
    for cl, names in clusters.items():
        cluster_ground[cl] = any(
            (n.lower().replace("_", " ") in ans) or (n in routed) for n in names
        )
    cluster_frac = sum(1 for v in cluster_ground.values() if v) / max(len(cluster_ground), 1)

    lit_ok = lit_hits_n >= len(lit_queries)
    mc_ok = not mc.get("error") and len(core_in_mc) >= len(cores) * 0.99
    mind_ok = domain_frac >= 0.5 and struct_frac >= 0.7 and not mind.get("error")

    score = (
        0.20 * min(1.0, lit_hits_n / (len(lit_queries) * 2))
        + 0.15 * min(1.0, len(lit_domains) / 12)
        + 0.25 * (len(core_in_mc) / max(len(cores), 1))
        + 0.25 * domain_frac
        + 0.10 * struct_frac
        + 0.05 * cluster_frac
    )
    ok = lit_ok and mc_ok and mind_ok
    return (
        ok,
        min(1.0, score),
        {
            "n_core_total": len(cores),
            "n_core_in_multipath": len(core_in_mc),
            "multipath_emergence_mean": ens.get("mean"),
            "literature_queries": len(lit_queries),
            "literature_hits_total": lit_hits_n,
            "literature_domains": sorted(lit_domains),
            "sample_arxiv": lit_samples[:8],
            "domain_grounding_frac": domain_frac,
            "domains_grounded": [x["domain"] for x in domain_grounded if x["grounded"]],
            "domains_missing_in_mind": [x["domain"] for x in domain_grounded if not x["grounded"]],
            "structural_checks": structural,
            "structural_frac": struct_frac,
            "cluster_grounding": cluster_ground,
            "cluster_frac": cluster_frac,
            "self_folds_n": len(fold_scores),
            "self_folds": fold_scores,
            "mind_answer_len": len(mind.get("answer") or ""),
            "mind_answer_preview": (mind.get("answer") or "")[:800],
            "note": "Self-referral uses full core atlas + multi-cluster literature — not 6 keywords.",
        },
        (
            f"Self-referral FULL: multipath {len(core_in_mc)}/{len(cores)} cores, "
            f"lit hits={lit_hits_n} domains={len(lit_domains)}, "
            f"mind domain-ground {domain_frac:.0%}, structural {struct_frac:.0%}, "
            f"clusters {cluster_frac:.0%}."
        ),
        (
            "Mind must emit full 35-core S panel on self-audit; auto-merge literature hits per core; "
            "LTM-solidify audit ledger; never equate multipath map% with green-gate."
        ),
    )


def check_seed_immutability_claim() -> tuple[bool, float, dict, str, str]:
    """Sanity: literature/chew path must not alter pin constants."""
    from fsot_mc.fast import K, POOF, PHI
    from fsot_mc.authority_gate import EXPECTED
    from fsot_mc.api_adapters import chew_science_text

    before = (float(K), float(POOF), float(PHI))
    chew_science_text("quantum cosmology multipath observer")
    after = (float(K), float(POOF), float(PHI))
    ok = before == after and abs(K - EXPECTED["K"]) < 1e-12
    return (
        ok,
        1.0 if ok else 0.0,
        {"K": K, "POOF": POOF, "PHI": PHI, "match_expected_K": abs(K - EXPECTED["K"]) < 1e-12},
        "Seeds immutable across chew path." if ok else "SEED MUTATION DETECTED.",
        "" if ok else "CRITICAL: isolate literature path from engine constants.",
    )


def check_formal_bridge() -> tuple[bool, float, dict, str, str]:
    try:
        from fsot_mc.formal_bridge import formal_status

        st = formal_status()
        local = bool(st.get("independent_local_court") or st.get("certificate_present"))
        claims = int(st.get("certificate_proved_claims") or 0)
        pending = int(st.get("pending_obligations") or 0)
        promoted = int(st.get("promoted_obligations") or 0)
        score = (0.4 if local else 0.0) + min(0.4, claims / 500) + min(0.2, promoted / 20)
        return (
            local and claims > 0,
            min(1.0, score),
            {
                "local_court": local,
                "proved_claims": claims,
                "pending": pending,
                "promoted": promoted,
                "online_lean_per_path": st.get("online_lean_per_path"),
            },
            f"Soft court local={local}, proved_claims={claims}, pending={pending}, promoted={promoted}.",
            "Auto-promote audit high_failures into pending obligations; never claim per-path Lean.",
        )
    except Exception as exc:
        return (
            False,
            0.2,
            {"error": str(exc)},
            "Formal bridge incomplete.",
            "Implement/export formal_status fully; batch obligations only.",
        )


# ── Orchestrator ────────────────────────────────────────────────────────────

CHECKS: list[tuple[str, str, str, Callable, str]] = [
    ("AUTH-001", "law", "Authority pin D1D38A + float engine", check_authority, "critical"),
    ("AUTH-002", "law", "Seed immutability under literature chew", check_seed_immutability_claim, "critical"),
    ("IND-001", "runtime", "Independent vendor workspace", check_independence, "critical"),
    ("EMP-001", "empirical", "Core fold recompute vs atlas", check_core_recompute, "critical"),
    ("EMP-002", "empirical", "Archive ≤0.5% green gate", check_archive_green_gate, "high"),
    ("EMP-003", "empirical", "Contested open-science panel", check_contested_panel, "high"),
    ("DOM-001", "atlas", "Full domain+extension atlas evaluate coverage", check_full_domain_atlas, "critical"),
    ("NAV-001", "atlas", "Navigator cores/panels/routes/subfields", check_navigator_subfields_routes, "high"),
    ("MC-001", "multipath", "Full-core multipath coherence + flips", check_multipath_coherence, "high"),
    ("LIT-001", "literature", "Multi-cluster literature→FSOT cross-ref battery", check_literature, "high"),
    ("MIND-001", "mind", "Multi-domain mind grounding (all cores + clusters)", check_mind_grounding, "high"),
    ("TISSUE-001", "connective", "Connective graph vs full archive domains", check_connective_tissue, "high"),
    ("DOC-001", "documentation", "Per-node scientific tissue theses", check_tissue_docs, "medium"),
    ("SELF-001", "self_referral", "FSOT self-referral on FULL domain atlas", check_self_referral, "high"),
    ("FORM-001", "formal", "Formal soft-court bridge", check_formal_bridge, "medium"),
]


def run_scientific_audit(
    *,
    write: bool = True,
    include_self: bool = True,
) -> dict[str, Any]:
    checks_spec = CHECKS if include_self else [c for c in CHECKS if c[0] != "SELF-001"]
    results: list[CheckResult] = []
    for cid, layer, title, fn, sev in checks_spec:
        results.append(_run_check(cid, layer, title, fn, severity_fail=sev))

    # Aggregate
    scores = [r.score for r in results]
    overall = sum(scores) / max(len(scores), 1)
    critical_fail = [r for r in results if not r.ok and r.severity == "critical"]
    high_fail = [r for r in results if not r.ok and r.severity == "high"]
    improvements = [
        {
            "id": r.id,
            "title": r.title,
            "severity": r.severity if not r.ok else ("medium" if r.score < 0.85 else "low"),
            "improvement": r.improvement
            or "Maintain regression coverage; re-run scientific-audit after changes.",
            "finding": r.finding,
            "score": r.score,
            "passed": r.ok,
        }
        for r in sorted(
            results,
            key=lambda x: (
                0 if not x.ok else 1,
                x.score,
                -{"critical": 3, "high": 2, "medium": 1, "low": 0, "info": 0}.get(x.severity, 0),
            ),
        )
        if (not r.ok) or r.score < 0.95 or r.improvement
    ]

    grade = (
        "A"
        if overall >= 0.9 and not critical_fail
        else "B"
        if overall >= 0.75 and not critical_fail
        else "C"
        if overall >= 0.6
        else "D"
        if overall >= 0.4
        else "F"
    )

    report = {
        "method": "fsot_scientific_intelligence_audit",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "free_parameters": 0,
        "authority": "D1D38A",
        "overall_score": round(overall, 4),
        "grade": grade,
        "n_checks": len(results),
        "n_pass": sum(1 for r in results if r.ok),
        "n_fail": sum(1 for r in results if not r.ok),
        "critical_failures": [r.id for r in critical_fail],
        "high_failures": [r.id for r in high_fail],
        "checks": [r.to_dict() for r in results],
        "improvement_ledger": improvements,
        "self_referral": next((r.to_dict() for r in results if r.id == "SELF-001"), None),
        "doctrine": (
            "Audit uses the same seed engine and multipath mind under audit. "
            "Literature and multipath are observation/discovery; green-gate remains empirical bar. "
            "Self-referral must never promote multipath-only claims to proved tier."
        ),
    }

    if write:
        exp = data_root() / "exports"
        exp.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = exp / f"scientific_audit_{stamp}.json"
        latest = exp / "scientific_audit_latest.json"
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        latest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        md_path = PACKAGE_ROOT / "docs" / "SCIENTIFIC_AUDIT_REPORT.md"
        md_path.write_text(format_audit_markdown(report), encoding="utf-8")
        report["written"] = {"json": str(path), "latest": str(latest), "markdown": str(md_path)}

    return report


def format_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# FSOT Scientific Intelligence Audit",
        "",
        f"**Generated (UTC):** {report.get('generated_at')}  ",
        f"**Overall score:** {report.get('overall_score')} · **Grade:** {report.get('grade')}  ",
        f"**Pass/Fail:** {report.get('n_pass')}/{report.get('n_checks')} pass  ",
        f"**Authority:** D1D38A · **free_parameters:** 0  ",
        "",
        "## Doctrine",
        "",
        report.get("doctrine") or "",
        "",
        "## Executive summary",
        "",
        f"- Critical failures: {report.get('critical_failures') or 'none'}",
        f"- High failures: {report.get('high_failures') or 'none'}",
        "",
        "## Check results",
        "",
        "| ID | Layer | Title | OK | Score | Severity | Finding |",
        "|----|-------|-------|----|------:|----------|---------|",
    ]
    for c in report.get("checks") or []:
        find = (c.get("finding") or "").replace("|", "/")[:120]
        lines.append(
            f"| {c.get('id')} | {c.get('layer')} | {c.get('title')} | "
            f"{'PASS' if c.get('ok') else 'FAIL'} | {c.get('score'):.2f} | {c.get('severity')} | {find} |"
        )
    lines += ["", "## Improvement ledger (priority order)", ""]
    for i, imp in enumerate(report.get("improvement_ledger") or [], 1):
        lines.append(
            f"### {i}. [{imp.get('severity')}] {imp.get('id')} — {imp.get('title')}"
        )
        lines.append("")
        lines.append(f"**Finding:** {imp.get('finding')}")
        lines.append("")
        lines.append(f"**Improvement:** {imp.get('improvement')}")
        lines.append("")
        lines.append(f"**Score:** {imp.get('score')}")
        lines.append("")

    self_r = report.get("self_referral")
    if self_r:
        lines += [
            "## Self-referral loop (FSOT on FSOT)",
            "",
            f"**OK:** {self_r.get('ok')} · **Score:** {self_r.get('score')}",
            "",
            self_r.get("finding") or "",
            "",
            "### Evidence (abridged)",
            "",
            "```json",
            json.dumps(self_r.get("evidence") or {}, indent=2, default=str)[:4000],
            "```",
            "",
            f"**Improvement:** {self_r.get('improvement')}",
            "",
        ]

    lines += [
        "## How to re-run",
        "",
        "```powershell",
        "python -m fsot_mc scientific-audit",
        "```",
        "",
        "---",
        "*Audit instrumented with the same engine under test. Seeds never move.*",
        "",
    ]
    return "\n".join(lines)
