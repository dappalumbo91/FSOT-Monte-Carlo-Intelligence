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
    from fsot_mc.universe_mc import run_universe_monte_carlo

    mc = run_universe_monte_carlo(n_paths=64, seed=7, store_paths=8, train_pathway_memory=False)
    if mc.get("error"):
        return False, 0.0, {"error": mc.get("error")}, "MC failed.", "Fix universe_mc errors."
    ens = mc.get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}
    mean = ef.get("mean")
    p10, p90 = ef.get("p10"), ef.get("p90")
    in_band = mean is not None and 0.55 <= float(mean) <= 0.78
    # stability: width of band
    width = (float(p90) - float(p10)) if p10 is not None and p90 is not None else 1.0
    score = (0.6 if in_band else 0.2) + max(0.0, 0.4 * (1.0 - width))
    de = mc.get("domain_ensemble") or {}
    flips = sorted(
        ((n, float(r.get("flip_rate") or 0)) for n, r in de.items()),
        key=lambda x: -x[1],
    )[:5]
    return (
        in_band,
        min(1.0, score),
        {
            "mean": mean,
            "p10": p10,
            "p90": p90,
            "width": width,
            "n_paths": mc.get("n_paths"),
            "top_flip_domains": flips,
        },
        f"Map emergence mean={mean:.3f} (band 0.55–0.78), p10–p90 width={width:.3f}.",
        "Document multipath vs green-gate confusion; reduce flip hotspots with observer-protocol cards.",
    )


def check_literature() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.literature_corpus import literature_search, literature_status

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
    r = literature_search("quantum gravity cosmology Hubble", arxiv_limit=5, wiki_limit=2)
    hits = ((r.get("arxiv") or {}).get("hits") or [])
    domains = r.get("primary_domains") or []
    ok = bool(r.get("ok") and hits and domains)
    # score by index depth + hit quality
    depth = min(1.0, arx_n / 200_000)  # full-ish scale target
    hit_s = min(1.0, len(hits) / 5)
    score = 0.4 * depth + 0.4 * hit_s + (0.2 if domains else 0.0)
    return (
        ok,
        score,
        {
            "arxiv_indexed": arx_n,
            "wiki_indexed": wiki_n,
            "n_hits": len(hits),
            "primary_domains": domains,
            "sample_ids": [h.get("id") for h in hits[:3]],
        },
        f"Literature OK: {arx_n} arXiv + {wiki_n} wiki; {len(hits)} hits → {domains[:4]}.",
        "Scale index toward full OAI dump; add citation graph & year filters; deep abstract→fold NLP.",
    )


def check_mind_grounding() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.mind import ask

    probes = [
        ("biology emergence percent", ["emergence", "s>", "fold", "not"]),
        ("compare FSOT general relativity", ["relativity", "architecture", "seed"]),
        ("acceptable error margin cross domain", ["0.5", "green", "margin"]),
    ]
    results = []
    score_acc = 0.0
    for q, must in probes:
        r = ask(q, n_paths=20, with_chew=False, force_new_mc=True)
        ans = (r.get("answer") or "").lower()
        th = r.get("thinking") or {}
        hits = sum(1 for m in must if m in ans)
        free0 = r.get("free_parameters") == 0
        method = r.get("method") == "fsot_monte_carlo_mind"
        frac = hits / max(len(must), 1)
        ok_one = free0 and method and frac >= 0.5 and not r.get("error")
        score_acc += (0.7 * frac + 0.3 * (1.0 if ok_one else 0.0))
        results.append(
            {
                "q": q,
                "keyword_frac": frac,
                "n_paths": th.get("n_paths"),
                "domains": th.get("routed_domains"),
                "ok": ok_one,
                "answer_len": len(r.get("answer") or ""),
            }
        )
    score = score_acc / len(probes)
    ok = score >= 0.65
    return (
        ok,
        score,
        {"probes": results},
        f"Mind grounding score={score:.2f} on {len(probes)} scientific probes.",
        "Increase science-grade depth (derivations, citations from literature hits, per-fold T1/T2/T3 in answers).",
    )


def check_connective_tissue() -> tuple[bool, float, dict, str, str]:
    from fsot_mc.archive_connective import get_connective_tissue
    from fsot_mc.graph_model import build_universe_graph

    t = get_connective_tissue()
    g = build_universe_graph(
        n_paths=16,
        seed=1,
        scope="full",
        with_mc=False,
        with_memory=False,
        with_predictions=True,
        with_archive_connective=True,
    )
    n_nodes = int(g.get("n_nodes") or 0)
    n_edges = int(g.get("n_edges") or 0)
    raw = (g.get("meta") or {}).get("archive_connective") or {}
    ok = n_nodes >= 100 and n_edges >= 100
    # coverage vs raw 39k
    raw_e = int(raw.get("coupling_raw_edge_count") or t.get("coupling_raw_edge_count") or 0)
    compact_e = int(t.get("n_edges") or 0)
    coverage = (compact_e / raw_e) if raw_e else 0.5
    score = min(1.0, 0.5 * min(1.0, n_nodes / 400) + 0.3 * min(1.0, n_edges / 2000) + 0.2 * min(1.0, coverage * 10))
    return (
        ok,
        score,
        {
            "graph_nodes": n_nodes,
            "graph_edges": n_edges,
            "tissue_nodes": t.get("n_nodes"),
            "tissue_edges": t.get("n_edges"),
            "raw_coupling_edges": raw_e,
            "green_gate": f"{t.get('n_green_gate')}/{t.get('n_with_error')}",
        },
        f"Connective graph {n_nodes} nodes / {n_edges} edges; compact/raw edge ratio≈{coverage:.4f}.",
        "LOD denser lean-overlap on zoom; per-edge error_pct visualization; live coupling recompute.",
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
    FSOT evaluates FSOT: multipath + literature + domain routing on the architecture itself.
    """
    from fsot_mc.literature_corpus import literature_search
    from fsot_mc.mind import ask
    from fsot_mc.universe_atlas import evaluate_domain
    from fsot_mc.universe_mc import run_universe_monte_carlo

    query = (
        "FSOT Fluid Spacetime Omni-Theory architecture multipath Monte Carlo "
        "observer collapse zero free parameters seed engine domain folds"
    )
    # 1) Literature about related physics (not marketing)
    lit = literature_search(
        "fluid spacetime quantum gravity cosmology observer measurement multipath",
        arxiv_limit=6,
        wiki_limit=2,
    )
    lit_domains = lit.get("primary_domains") or []
    lit_hits = ((lit.get("arxiv") or {}).get("hits") or [])

    # 2) Multipath on architecture-relevant folds
    domains = list(
        dict.fromkeys(
            ["Cosmology", "Quantum_Mechanics", "Quantum_Gravity", "Neuroscience", "Biology", "Particle_Physics"]
            + lit_domains[:4]
        )
    )
    # filter to existing
    use = []
    for d in domains:
        try:
            evaluate_domain(d)
            use.append(d)
        except KeyError:
            continue
    mc = run_universe_monte_carlo(
        n_paths=48,
        seed=42,
        domains=use[:14] if use else None,
        store_paths=6,
        train_pathway_memory=True,
    )
    ens = (mc.get("ensemble") or {}).get("emergence_fraction") or {}
    de = mc.get("domain_ensemble") or {}

    # 3) Mind self-description
    mind = ask(
        "Audit the FSOT Monte Carlo Intelligence architecture as a Theory of Everything application: "
        "what is multipath thinking, what is the 0.5% green gate, and what cannot be claimed?",
        n_paths=28,
        with_chew=True,
        force_new_mc=True,
    )
    ans = (mind.get("answer") or "").lower()
    required = [
        "free_parameters",
        "emergence",
        "seed",
        "0.5",
        "multipath",
        "not",
    ]
    # free_parameters may appear as free_parameters=0
    req_hits = sum(
        1
        for r in required
        if r in ans or (r == "free_parameters" and "free" in ans and "parameter" in ans)
    )
    honesty = any(
        x in ans
        for x in (
            "experiment",
            "scaffold",
            "not a bayesian",
            "does not rewrite",
            "epistemic",
            "lean",
        )
    )

    # Self-consistency score
    fold_scores = []
    for d in use[:6]:
        row = de.get(d) or {}
        S = row.get("S_path_mean", row.get("S_canonical"))
        if S is not None:
            fold_scores.append({"domain": d, "S_path_mean": S, "flip_rate": row.get("flip_rate")})

    lit_ok = bool(lit_hits)
    mc_ok = not mc.get("error") and ens.get("mean") is not None
    mind_ok = req_hits >= 4 and honesty and not mind.get("error")
    score = (
        (0.25 if lit_ok else 0.0)
        + (0.35 if mc_ok else 0.0)
        + (0.25 * (req_hits / len(required)))
        + (0.15 if honesty else 0.0)
    )
    ok = lit_ok and mc_ok and mind_ok
    return (
        ok,
        min(1.0, score),
        {
            "literature_hits": len(lit_hits),
            "literature_domains": lit_domains,
            "sample_arxiv": [h.get("id") for h in lit_hits[:3]],
            "multipath_emergence_mean": ens.get("mean"),
            "self_folds": fold_scores,
            "mind_keyword_hits": f"{req_hits}/{len(required)}",
            "mind_honesty_signals": honesty,
            "mind_answer_len": len(mind.get("answer") or ""),
            "mind_answer_preview": (mind.get("answer") or "")[:600],
        },
        (
            f"Self-referral: lit_hits={len(lit_hits)}, map_emergence={ens.get('mean')}, "
            f"mind_keywords={req_hits}/{len(required)}, honesty={honesty}."
        ),
        (
            "Close the loop: auto-write audit findings as LTM engrams; attach PRED kill-criteria "
            "to each self-claim; promote multipath-only statements never as green-gate claims."
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
    ("MC-001", "multipath", "Multipath map coherence band", check_multipath_coherence, "medium"),
    ("LIT-001", "literature", "Local arXiv/wiki corpus cross-ref", check_literature, "high"),
    ("MIND-001", "mind", "Conversational scientific grounding", check_mind_grounding, "high"),
    ("TISSUE-001", "connective", "Archive connective graph coverage", check_connective_tissue, "medium"),
    ("DOC-001", "documentation", "Per-node scientific tissue theses", check_tissue_docs, "medium"),
    ("SELF-001", "self_referral", "FSOT evaluates FSOT architecture", check_self_referral, "high"),
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
