"""
FSOT Monte Carlo Mind — conversational Theory-of-Everything intelligence.

FSOT is treated as a serious ToE: one seed engine verified across formal + empirical
domains. Monte Carlo multipath *is* the thinking process — exploring observation
histories of the fluid, not inventing free physics.

Conversation can chew external science text (arXiv / Wikipedia) as sensory input,
then re-simulate and answer with quantitative fold structure.

free_parameters = 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fsot_mc.adaptive_memory import AdaptiveMemory
from fsot_mc.contested_physics import run_contested_physics_pack
from fsot_mc.language_relay import densify_prose, relay_lead, relay_universe_state, _pflt_surface_phrase
from fsot_mc.pathway_memory import PathwayMemory
from fsot_mc.pflt_bridge import eyes_with_mc
from fsot_mc.universe_atlas import core_names, evaluate_domain, get_domain
from fsot_mc.universe_mc import run_universe_monte_carlo


_DOMAIN_CUES: dict[str, list[str]] = {
    "cosmology": ["Cosmology", "Astrophysics", "Particle_Astrophysics"],
    "hubble": ["Cosmology", "Astronomy"],
    "h0": ["Cosmology"],
    "relativity": ["Cosmology", "Quantum_Gravity", "Astrophysics", "Particle_Physics"],
    "general relativity": ["Cosmology", "Quantum_Gravity", "Astrophysics"],
    "einstein": ["Cosmology", "Quantum_Gravity", "Astrophysics"],
    "gr ": ["Cosmology", "Quantum_Gravity"],
    "dark": ["Cosmology", "Particle_Astrophysics"],
    "quantum": ["Quantum_Mechanics", "Quantum_Optics", "Quantum_Computing", "Quantum_Gravity"],
    "particle": ["Particle_Physics", "High_Energy_Physics", "Nuclear_Physics"],
    "atom": ["Atomic_Physics", "Chemistry"],
    "chemistry": ["Chemistry", "Physical_Chemistry", "Molecular_Chemistry"],
    "biology": ["Biology", "Biochemistry", "Ecology"],
    "life": ["Biology", "Ecology", "Neuroscience"],
    "brain": ["Neuroscience", "Psychology"],
    "mind": ["Neuroscience", "Psychology"],
    "consciousness": ["Neuroscience", "Psychology"],
    "neural": ["Neuroscience"],
    "earth": ["Geophysics", "Seismology", "Oceanography", "Meteorology"],
    "quake": ["Seismology", "Geophysics"],
    "weather": ["Meteorology", "Atmospheric_Physics"],
    "climate": ["Meteorology", "Atmospheric_Physics", "Oceanography"],
    "ocean": ["Oceanography"],
    "fluid": ["Fluid_Dynamics", "Oceanography"],
    "star": ["Astronomy", "Astrophysics"],
    "planet": ["Planetary_Science", "Astronomy"],
    "space": ["Astronomy", "Astrophysics", "Cosmology"],
    "material": ["Materials_Science", "Condensed_Matter"],
    "fuel": ["Chemistry", "Thermodynamics", "Molecular_Chemistry", "Nuclear_Physics"],
    "energy": ["Thermodynamics", "Nuclear_Physics", "Electromagnetism"],
    "fusion": ["Nuclear_Physics", "High_Energy_Physics", "Thermodynamics"],
    "sound": ["Acoustics"],
    "light": ["Optics", "Quantum_Optics"],
    "electric": ["Electromagnetism"],
    "economy": ["Economics", "Sociology"],
    "society": ["Sociology", "Psychology"],
    "math": ["Quantum_Computing", "Quantum_Mechanics"],
    "universe": ["Cosmology", "Astrophysics", "Quantum_Mechanics", "Biology"],
    "emergence": ["Biology", "Cosmology", "Neuroscience"],
    "dispersal": ["Cosmology", "Quantum_Gravity"],
    "bridge": ["Quantum_Mechanics", "Cosmology", "Biology"],
    "as above": ["Cosmology", "Biology", "Quantum_Mechanics"],
    "observer": ["Quantum_Mechanics", "Neuroscience", "Cosmology"],
    "simulation": ["Cosmology", "Quantum_Mechanics", "Biology"],
    "69": ["Biology", "Ecology", "Biochemistry"],
    "percent": ["Biology", "Cosmology", "Quantum_Mechanics"],
    "compare": ["Cosmology", "Quantum_Gravity", "Quantum_Mechanics", "Particle_Physics"],
    "versus": ["Cosmology", "Quantum_Gravity", "Quantum_Mechanics"],
    "vs ": ["Cosmology", "Quantum_Gravity", "Quantum_Mechanics"],
}


def route_query_to_domains(query: str, *, max_domains: int = 14) -> list[str]:
    q = query.lower()
    scored: dict[str, float] = {}
    for cue, domains in _DOMAIN_CUES.items():
        if cue in q:
            for d in domains:
                try:
                    get_domain(d)
                    scored[d] = scored.get(d, 0.0) + 1.0 + 0.1 * len(cue)
                except KeyError:
                    continue
    for name in core_names():
        token = name.lower().replace("_", " ")
        if token in q or name.lower() in q.replace(" ", "_"):
            scored[name] = scored.get(name, 0.0) + 2.0
        last = name.split("_")[-1].lower()
        if len(last) > 4 and last in q:
            scored[name] = scored.get(name, 0.0) + 0.5
    if not scored:
        for d in ("Cosmology", "Quantum_Mechanics", "Biology", "Neuroscience", "Chemistry"):
            try:
                get_domain(d)
                scored[d] = 1.0
            except KeyError:
                pass
    ranked = sorted(scored.items(), key=lambda x: -x[1])
    return [n for n, _ in ranked[:max_domains]]


def _pct(x: float | None) -> str:
    if x is None:
        return "?"
    return f"{100.0 * float(x):.1f}%"


def _law_primer() -> str:
    """Science-grade ToE framing used in every serious answer — paradigm shift."""
    return (
        "FSOT LAW (ToE paradigm shift, free_parameters=0, authority D1D38A): "
        "raw_S = K·(T1+T2+T3) from fixed seeds (π, e, φ, γ, Catalan). "
        "T1 carries coherence / perceived_adjust / quirk_mod (observer coupling); "
        "T2 carries dimensional / fluid-structure terms; "
        "T3 carries acoustic_bleed, poof, chaos, and long-range bleed. "
        "Each scientific domain is a *fold* of one 25D fluid condensate, indexed by "
        "effective depth D_eff and phase δψ — not a separate fitted model. "
        "Sign(S)>0 = emergence (structure-forming vitality); sign(S)≤0 = dispersal. "
        "This is a paradigm shift in how the universe is seen: one fluid, many folds, "
        "life and cosmos on the same seed engine — not bolted-on ontologies. "
        "Formal multi-prover obligations + large empirical panels already close many "
        "domains on this same engine; multipath Monte Carlo explores *observer histories* "
        "of that law for explanation and new combination discovery."
    )


def _explain_emergence_fraction(
    ens: dict[str, Any],
    focus_eval: list[dict[str, Any]],
    n_sim_domains: int,
    n_paths: int,
    bio_analysis: dict[str, Any] | None = None,
) -> str:
    """
    Dual-frame explanation of multipath emergence %:

    OPERATIONAL — mean over paths of (folds with S>0)/n_folds (map co-emergence).
    PARADIGM — natural co-emergence window / complexity–energy occupancy for
    biological systems as lawful intermediate folds (not Bayesian P(Earth life)).
    """
    ef = ens.get("emergence_fraction") or {}
    mean = ef.get("mean")
    p10, p50, p90 = ef.get("p10"), ef.get("p50"), ef.get("p90")
    bio = next((e for e in focus_eval if e.get("domain") == "Biology"), None)
    lines = [
        "DUAL FRAME — multipath emergence fraction (~60–70% band, often ~69%):",
        f"OPERATIONAL: for each of {n_paths} Monte Carlo paths, count how many of the "
        f"{n_sim_domains} simulated domain folds have vitality S>0 (emergence) versus "
        "S≤0 (dispersal); path fraction = count/n_folds; reported "
        f"~{_pct(mean)} is the mean of those path fractions "
        f"(median {_pct(p50)}, p10–p90 {_pct(p10)}–{_pct(p90)}).",
        "PARADIGM (ToE hypothesis): that map occupancy is the *natural co-emergence window* — "
        "the energy/complexity occupancy the multi-scale fluid must sustain for "
        "chemistry→biology→ecology→mind to emerge as lawful intermediate folds, not contingency. "
        "In that reading it *is* an emergence probability of the *map* (share of scales "
        "structure-forming under observer coupling) — the complexity budget visible as ~2/3 "
        "co-emergence — not a Bayesian P(this planet has life) and not a culture-plate rate.",
    ]
    if bio:
        lines.append(
            f"BIOLOGY FOLD: path-mean S={float(bio['S']):+.4f} "
            f"({bio.get('regime')}) at D_eff={bio.get('D_eff')}, "
            f"flip_rate={bio.get('flip_rate')}. "
            "Strong positive S = biology is an emergence regime of the same engine; "
            f"the ~{_pct(mean)} is map co-emergence occupancy, while Biology’s own "
            f"vitality intensity is S={float(bio['S']):+.4f}."
        )
    if bio_analysis and bio_analysis.get("hypothesis"):
        from fsot_mc.bio_emergence import format_bio_emergence_science

        lines.append(format_bio_emergence_science(bio_analysis))
    return " ".join(lines)


def _stream_path_thinking(mc: dict[str, Any], *, max_paths: int = 3) -> str:
    """Surface a few multipath histories so answers show *how* the mind thought."""
    samples = mc.get("sample_paths") or []
    if not samples:
        return ""
    bits = []
    for i, p in enumerate(samples[:max_paths]):
        flips = p.get("regime_flips") or []
        flip_txt = ", ".join(
            f"{f.get('domain')}:{f.get('from')}→{f.get('to')}"
            if isinstance(f, dict)
            else str(f)
            for f in (flips[:4] if isinstance(flips, list) else [])
        ) or "none"
        bits.append(
            f"path[{i}] emergence={_pct(p.get('emergence_fraction'))} "
            f"mean_S={float(p.get('mean_S') or 0):+.3f} "
            f"n_flips={p.get('n_regime_flips')} flips=[{flip_txt}]"
        )
    return (
        "PATH STREAM (how multipath thought moved): " + "; ".join(bits) + ". "
        "Each path is one observer-coupled history through the fluid folds."
    )


def _compose_scientific_answer(
    query: str,
    domains: list[str],
    mc: dict[str, Any],
    focus_eval: list[dict[str, Any]],
    contested: dict[str, Any] | None,
    chew: dict[str, Any] | None,
    prior: dict[str, Any] | None,
    engineering: list[dict[str, Any]] | None = None,
    bio_analysis: dict[str, Any] | None = None,
    memory_recall: list[dict[str, Any]] | None = None,
) -> str:
    ens = mc.get("ensemble") or {}
    can = mc.get("canonical_snapshot") or {}
    n_paths = int(mc.get("n_paths") or 0)
    n_dom = int(mc.get("n_domains") or len(focus_eval) or 0)
    ql = query.lower()
    parts: list[str] = []

    parts.append(_law_primer())
    parts.append(
        f"This reply is the outcome of {n_paths} observer-coupled multipath simulations "
        f"on {n_dom} domain folds (free_parameters=0). Thinking *is* the multipath run — "
        "not a language model free-associating physics. Paradigm: one fluid, many folds."
    )

    if prior:
        parts.append(
            f"Session continuity: refining prior thought (turn {prior.get('n_turns', '?')}) "
            f"with phase bias / pathway memory from previous multipath run."
        )

    bio_cues = (
        "69",
        "percent",
        "emergence",
        "vitality",
        "what does",
        "mean",
        "biology",
        "life",
        "complexity",
        "energy",
        "natural",
        "organism",
        "evolve",
        "abiogen",
    )
    # Emergence % + paradigm biology science when relevant
    if any(k in ql for k in bio_cues):
        parts.append(
            _explain_emergence_fraction(
                ens, focus_eval, n_dom, n_paths, bio_analysis=bio_analysis
            )
        )
    else:
        ef = ens.get("emergence_fraction") or {}
        if ef.get("mean") is not None:
            parts.append(
                f"Multipath map co-emergence occupancy: mean {_pct(ef.get('mean'))} "
                f"(p10–p90 {_pct(ef.get('p10'))}–{_pct(ef.get('p90'))}) = average share of "
                f"folds with S>0 across {n_paths} paths — the natural ~2/3 window under "
                "observer coupling; paradigm-readable as map-level emergence probability / "
                "complexity–energy occupancy (not Bayesian P(Earth life)). "
                "Operational: count(S>0)/n_folds per path, then mean over paths."
            )

    # Per-domain scientific depth
    if focus_eval:
        rows = []
        for e in focus_eval[:10]:
            s = float(e["S"])
            sc = float(e.get("S_canonical") or e["S"])
            dS = s - sc
            rows.append(
                f"{e['domain']}: path-mean S={s:+.4f} "
                f"(canonical {sc:+.4f}, ΔS_obs={dS:+.4f}, "
                f"D_eff={e.get('D_eff')}, {e.get('regime')}, "
                f"flip_rate={e.get('flip_rate')})"
            )
        parts.append(
            "Focus fold panel (path-mean scalars under observer coupling): "
            + "; ".join(rows)
            + ". "
            "ΔS_obs = path-mean S − canonical zero-noise S: large |ΔS| or high flip_rate "
            "marks observer-sensitive folds (priority for experiment / formal panels)."
        )

    # Explicit biology callout with scale context
    bio = next((e for e in focus_eval if e.get("domain") == "Biology"), None)
    if bio and ("bio" in ql or "life" in ql or "69" in ql or "emerg" in ql or "complexity" in ql):
        parts.append(
            f"On the Biology fold alone, path-mean S={float(bio['S']):+.4f} is "
            f"{'strongly positive' if float(bio['S']) > 0.3 else 'positive'}, "
            "so biology is an *emergence regime* of the same engine — structure-forming "
            "vitality — consistent with the paradigm shift that life is not a "
            "separate ontology but a fold of fluid spacetime at intermediate D_eff "
            f"({bio.get('D_eff')}). Intermediate D_eff between quantum (low D_eff) and "
            "cosmology (high D_eff) is where self-organizing chemical/biological structure "
            "is expected under one-fluid ToE architecture — the complexity niche the "
            "~2/3 map co-emergence window makes room for."
        )

    # Scale ladder for science depth
    if any(k in ql for k in ("scale", "ladder", "d_eff", "depth", "as above", "bridge", "universe")):
        ladder = sorted(
            [e for e in focus_eval if e.get("D_eff") is not None],
            key=lambda e: float(e.get("D_eff") or 0),
        )
        if ladder:
            bits = [f"{e['domain']}@D_eff={e.get('D_eff')} S={float(e['S']):+.3f}" for e in ladder[:8]]
            parts.append(
                "D_eff scale ladder (shallow→deep folds on this run): "
                + " → ".join(bits)
                + ". Same seeds at every rung."
            )

    # Bridges
    lr = mc.get("long_range_bridges") or {}
    if lr:
        best = sorted(
            lr.items(),
            key=lambda kv: -abs(float((kv[1].get("strength") or {}).get("mean") or 0)),
        )[:5]
        bits = []
        for _k, payload in best:
            st = payload.get("strength") or {}
            bits.append(
                f"{payload.get('a')}↔{payload.get('b')} "
                f"(mean strength {float(st.get('mean') or 0):+.3f}, "
                f"std {float(st.get('std') or 0):.3f})"
            )
        parts.append(
            "As Above So Below bridges from this run: " + "; ".join(bits) + ". "
            "Stable co-signed strength is a cross-scale coupling signature of one medium — "
            "a discovery target when strength is high and std is controlled."
        )

    # Path stream
    stream = _stream_path_thinking(mc)
    if stream and any(k in ql for k in ("path", "how", "think", "emerg", "69", "detail", "explain", "compare", "fuel")):
        parts.append(stream)

    # Compare FSOT vs GR / standard models when asked
    if any(k in ql for k in ("relativity", "einstein", "general rel", "gr ", "compare", "versus", "vs ")):
        parts.append(
            "COMPARE — FSOT vs General Relativity (architectural, not dismissal of GR data): "
            "GR is the geometric theory of gravity in 4D spacetime with curvature from stress-energy; "
            "it is extraordinarily precise in its domain (solar system, binary pulsars, GW). "
            "FSOT does not discard those measurements; it proposes a *different architecture*: "
            "a 25D fluid condensate with one seed scalar raw_S, observer coupling (quirk_mod), "
            "and domain folds (D_eff, δψ) that must close cosmology *and* biology *and* quantum "
            "with the same seeds. Dark sectors in ΛCDM are parameter slots; FSOT routes contested "
            "readouts (e.g. H0 dual-anchor / bubble-bleed class) through term structure without "
            "per-observable least squares. Precision on FSOT’s verified panels lives in the Lean "
            "hub / strict-empirical corpus; multipath here explores *observer histories* of that "
            "engine for discovery and explanation. GR remains the correct effective geometric "
            "description in its proven regime; FSOT’s claim is *unification architecture* across "
            "regimes GR does not address as a single seed engine."
        )
        cosm = next((e for e in focus_eval if e.get("domain") == "Cosmology"), None)
        qg = next((e for e in focus_eval if e.get("domain") == "Quantum_Gravity"), None)
        if cosm:
            parts.append(
                f"This run’s Cosmology fold: S={float(cosm['S']):+.4f} ({cosm.get('regime')}), "
                f"D_eff={cosm.get('D_eff')}, flip_rate={cosm.get('flip_rate')} "
                f"(canonical S={float(cosm.get('S_canonical') or cosm['S']):+.4f})."
            )
        if qg:
            parts.append(
                f"Quantum_Gravity fold: S={float(qg['S']):+.4f} ({qg.get('regime')}), "
                f"flip_rate={qg.get('flip_rate')} — observer-sensitive contact region "
                "between quantum and cosmos folds."
            )

    # Contested / discovery
    if contested:
        for p in (contested.get("top") or [])[:3]:
            parts.append(
                f"Discovery probe {p.get('id')}: {p.get('title')} "
                f"[score={float(p.get('score') or 0):.2f}, tier={p.get('epistemic_tier')}]. "
                f"{(p.get('hypothesis') or '')[:320]}"
            )

    # Engineering / fuel archive predictions (ToE → design)
    eng_cues = (
        "fuel",
        "energy",
        "thermo",
        "hydrogen",
        "engine",
        "engineering",
        "prediction",
        "experiment",
        "device",
        "molecule",
        "hemp",
        "algae",
        "biodiesel",
        "new physics",
        "discover",
        "invention",
        "design",
    )
    if engineering and any(c in ql for c in eng_cues):
        parts.append(
            "ARCHIVE ENGINEERING / PREREGISTERED DESIGNS (FSOT-derived, experiment-gated): "
            "the Physical Archive already holds multi-domain predictions and fuel/device panels "
            "built from the same seed engine — treated here as serious ToE design leads, not free invention."
        )
        for e in engineering[:5]:
            if e.get("id") == "ENG-ARCHIVE-INVENTORY":
                parts.append(
                    f"Inventory: {e.get('n_predictions')} preregistered predictions "
                    f"({e.get('n_engineering_fuel_related')} fuel/thermo-related) "
                    f"from {e.get('source')}."
                )
                continue
            parts.append(
                f"{e.get('id')} {e.get('name')}: FSOT={e.get('fsot_predicted')} "
                f"{e.get('unit') or ''} vs SOTA {e.get('sota_baseline')} "
                f"({e.get('sota_label')}); discriminant={e.get('discriminant')}; "
                f"branch={e.get('formula_branch')}. "
                f"{(e.get('note') or '')[:220]}"
            )

    # Chew from arxiv/wiki
    if chew and chew.get("ok"):
        parts.append(
            f"External chew ({chew.get('source')}): ingested scientific/natural language "
            f"as sensory context ({chew.get('n_chars', 0)} chars). "
            f"Title/subject: {chew.get('title') or chew.get('query')}. "
            "Text is treated as observation stream into the fluid map — it does not rewrite seeds; "
            "it densifies routing and explanation against real literature structure."
        )
        if chew.get("fsot_crossref") and chew.get("primary_domains"):
            parts.append(
                "LITERATURE→FSOT CROSS-REF: mapped paper/wiki categories onto folds "
                f"{chew.get('primary_domains')}. "
                "Use these as co-sign targets with multipath S/regime (not free invention)."
            )
        lit = chew.get("literature") or {}
        arx_hits = ((lit.get("arxiv") or {}).get("hits") or [])[:2]
        for h in arx_hits:
            folds = h.get("fsot_fold_panel") or []
            fold_s = "; ".join(
                f"{f.get('domain')} S={f.get('S')}" for f in folds[:3] if isinstance(f, dict)
            )
            parts.append(
                f"arXiv {h.get('id')}: {h.get('title')} "
                f"[{h.get('categories')}] → FSOT {{{fold_s or h.get('fsot_domains')}}}."
            )
        if chew.get("excerpt"):
            parts.append(f"Chew excerpt: {str(chew['excerpt'])[:480]}")

    # Ensemble mechanics
    col = ens.get("collapse_true_fraction") or {}
    if col.get("mean") is not None:
        parts.append(
            f"Observer mechanics: collapse-true fraction mean {_pct(col.get('mean'))} "
            f"— fraction of domain-steps locking to the observed branch "
            f"(quirk_mod active) versus Poof decoherent branch."
        )

    if can:
        parts.append(
            f"Canonical (zero-noise) map baseline on these folds: "
            f"emergence {_pct(can.get('emergence_fraction'))}, "
            f"mean_S={float(can.get('mean_S') or 0):+.4f}."
        )

    # Adaptive memory recall (STM/LTM engrams)
    if memory_recall:
        bits = []
        for m in memory_recall[:4]:
            bits.append(
                f"[{m.get('store')}|solid={m.get('solidified')}] "
                f"{str(m.get('text') or '')[:160]}"
            )
        parts.append(
            "ADAPTIVE MEMORY RECALL (FSOT STM/LTM — seeds unchanged): "
            + " || ".join(bits)
            + ". Long-term engrams solidify only under φ-EWMA + Poof bars; "
            "they bias explanation/routing, never rewrite D1D38A."
        )

    # Cross-domain accuracy / margin of error when asked
    if any(
        k in ql
        for k in (
            "accuracy",
            "margin",
            "error",
            "precision",
            "0.5",
            "percent error",
            "green gate",
            "benchmark",
            "cross-domain",
            "cross domain",
            "acceptable",
            "memory",
            "retain",
            "learn",
            "adapt",
        )
    ):
        try:
            from fsot_mc.accuracy_gate import (
                THRESHOLD_POOLED_MEDIAN_PCT,
                LCDM_SM_OPEN_PANEL_BASELINE_PCT,
                load_archive_margin_audit,
                load_contested_panel,
                core_fold_recompute_accuracy,
            )

            margin = load_archive_margin_audit()
            cont = load_contested_panel()
            core_acc = core_fold_recompute_accuracy()
            parts.append(
                "CROSS-DOMAIN ACCURACY / ACCEPTABLE MARGINS (not biology-only): "
                f"Archive green gate is pooled median ≤{THRESHOLD_POOLED_MEDIAN_PCT}% "
                f"(strict scalar max ≤{THRESHOLD_POOLED_MEDIAN_PCT}%). "
                f"Loaded audit: green {margin.get('green_gate_pass_count')}/"
                f"{margin.get('n_domains_reported')} fail={margin.get('green_gate_fail_count')}; "
                f"median-of-domain-medians={margin.get('pooled_median_of_domain_medians_pct')}%. "
                f"Contested open panel: FSOT pooled median error "
                f"{cont.get('fsot_pooled_median_error_pct')}% vs current-model baseline "
                f"~{cont.get('current_model_baseline_pct') or LCDM_SM_OPEN_PANEL_BASELINE_PCT}% "
                f"({cont.get('n_within_0_5pct')}/{cont.get('n_observables')} within green gate). "
                f"Local core fold recompute vs atlas: max_rel_error_pct="
                f"{core_acc.get('max_rel_error_pct')} "
                f"({core_acc.get('n_within_tol')}/{core_acc.get('n_core')} within engine tol). "
                "Multipath map occupancy (~60–70%) is a co-emergence discovery metric — "
                "it is not the empirical ≤0.5% panel gate. Run: python -m fsot_mc readings."
            )
        except Exception as exc:
            parts.append(f"Accuracy cross-ref unavailable in this session: {exc}.")

    parts.append(
        "Epistemic honesty (ToE-serious, multi-domain): multipath statistics explain regime "
        "structure and discovery leads; formal proved claims and ≤0.5% panel gates live in the "
        "FSOT Lean hub / archive margin audit. Engineering predictions (fuels, devices, new "
        "combinations) are FSOT-derived designs with preregistered discriminants — cross-domain "
        "precision raises prior confidence and narrows error bars relative to unconstrained "
        "invention, but physical experiment remains the closure step. This mind is intentionally "
        "deepen-able: more paths, live chew (FSOT_MC_ONLINE=1), archive panels, accuracy readings, "
        "and formal soft-court promotion of leads."
    )
    return densify_prose(" ".join(parts), max_extra=2)


def _thinking_steps(
    query: str,
    domains: list[str],
    mc: dict[str, Any],
    focus_eval: list[dict[str, Any]],
    reused: bool,
    engineering: list[dict[str, Any]] | None = None,
    chew: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    ens = mc.get("ensemble") or {}
    steps = [
        {
            "step": "1_toe_law",
            "text": (
                "FSOT ToE law bound: S=K·(T1+T2+T3) from seeds only; "
                "domains are folds of one 25D fluid. Authority D1D38A. free_parameters=0."
            ),
        },
        {
            "step": "2_route",
            "text": f"Routed query to folds: {', '.join(domains)}.",
        },
    ]
    if chew and chew.get("ok"):
        steps.append(
            {
                "step": "2b_chew",
                "text": (
                    f"Chewed external science language ({chew.get('source')}): "
                    f"{chew.get('title') or chew.get('query')} "
                    f"[{chew.get('n_chars')} chars] as sensory stream (seeds unchanged)."
                ),
            }
        )
    if reused:
        steps.append(
            {
                "step": "3_session_memory",
                "text": "Reused prior multipath state (session memory) with incremental re-simulation bias.",
            }
        )
    else:
        steps.append(
            {
                "step": "3_multipath",
                "text": (
                    f"Ran {mc.get('n_paths')} multipath histories with observer collapse "
                    f"on {mc.get('n_domains')} folds. Thinking = exploring fluid observation histories."
                ),
            }
        )
    stream = _stream_path_thinking(mc, max_paths=2)
    if stream:
        steps.append({"step": "3b_path_stream", "text": stream})
    ef = ens.get("emergence_fraction") or {}
    if ef:
        steps.append(
            {
                "step": "4_map_vitality",
                "text": (
                    f"Map vitality: mean emergence fraction {_pct(ef.get('mean'))} "
                    f"(p10 {_pct(ef.get('p10'))}, p90 {_pct(ef.get('p90'))}). "
                    "This is the share of folds with S>0 averaged over paths — not P(biology)."
                ),
            }
        )
    if focus_eval:
        bits = [f"{e['domain']} S={float(e['S']):+.3f}" for e in focus_eval[:6]]
        steps.append({"step": "5_focus", "text": "Focus scalars: " + "; ".join(bits) + "."})
    if engineering:
        eng_ids = [str(e.get("id")) for e in engineering[:4] if e.get("id")]
        steps.append(
            {
                "step": "5b_engineering",
                "text": f"Fused archive engineering/prediction leads: {', '.join(eng_ids)}.",
            }
        )
    steps.append(
        {
            "step": "6_answer",
            "text": "Compose scientific answer from multipath structure + ToE law + archive designs.",
        }
    )
    return steps


@dataclass
class FSOTMind:
    """
    Conversational ToE intelligence.
    Session reuses last MC for multi-turn refinement.
    AdaptiveMemory: STM (working) + LTM (solidified engrams) — seeds never move.
    """

    n_paths: int = 64
    seed: int = 0
    scope: str = "core"
    memory: PathwayMemory = field(default_factory=PathwayMemory)
    adaptive: AdaptiveMemory = field(default_factory=AdaptiveMemory)
    history: list[dict[str, Any]] = field(default_factory=list)
    last_mc: dict[str, Any] | None = None
    last_domains: list[str] = field(default_factory=list)
    free_parameters: int = 0

    def think(
        self,
        query: str,
        *,
        n_paths: int | None = None,
        with_eyes: bool = False,
        with_pflt_surface: bool = True,
        with_chew: bool | None = None,
        reuse_if_related: bool = True,
        force_new_mc: bool = False,
    ) -> dict[str, Any]:
        query = (query or "").strip()
        if not query:
            return {"error": "empty_query", "free_parameters": 0}

        n_paths = int(n_paths or self.n_paths)
        domains = route_query_to_domains(query)
        ql = query.lower()

        # Recall adaptive LTM/STM before multipath (routing densify)
        memory_recall = self.adaptive.recall(query, limit=5)
        for m in memory_recall:
            for d in m.get("domains") or []:
                if d not in domains:
                    try:
                        get_domain(d)
                        domains.append(d)
                    except KeyError:
                        pass

        for d in ("Cosmology", "Quantum_Mechanics", "Biology"):
            if d not in domains:
                try:
                    get_domain(d)
                    domains.append(d)
                except KeyError:
                    pass

        spine = ["Cosmology", "Quantum_Mechanics", "Biology", "Neuroscience", "Chemistry"]
        use_domains = list(dict.fromkeys([*domains, *spine]))
        core_set = set(core_names())
        use_domains = [d for d in use_domains if d in core_set]
        for d in core_names():
            if d not in use_domains:
                use_domains.append(d)
            if len(use_domains) >= 14:
                break

        # External chew (arXiv / Wikipedia) as sensory language
        # Auto-chew on science-ish questions unless explicitly disabled
        science_cues = (
            "relativity",
            "quantum",
            "biology",
            "cosmology",
            "arxiv",
            "wikipedia",
            "compare",
            "science",
            "physics",
            "fuel",
            "energy",
            "einstein",
            "emergence",
            "theory",
        )
        if with_chew is None:
            with_chew = any(c in ql for c in science_cues)
        chew = None
        if with_chew:
            from fsot_mc.api_adapters import chew_science_text

            chew = chew_science_text(query)

        # Multi-turn: reuse last MC if overlapping domains and not forced
        reused = False
        overlap = 0.0
        if (
            reuse_if_related
            and not force_new_mc
            and self.last_mc
            and self.last_domains
        ):
            inter = len(set(domains) & set(self.last_domains))
            union = len(set(domains) | set(self.last_domains)) or 1
            overlap = inter / union
            if overlap >= 0.35:
                reused = True

        if reused and self.last_mc:
            # Light re-sim with fewer paths, same domain set, memory warm
            mc = run_universe_monte_carlo(
                n_paths=max(16, n_paths // 2),
                seed=self.seed + len(self.history) + 17,
                domains=self.last_domains,
                store_paths=min(12, n_paths),
                train_pathway_memory=True,
                pathway_memory=self.memory,
            )
            # blend ensemble narrative with last for continuity note
            mc_public = {k: v for k, v in mc.items() if not k.startswith("_")}
            mc_public["session_reused_prior"] = True
            mc_public["domain_overlap"] = overlap
        else:
            mc = run_universe_monte_carlo(
                n_paths=n_paths,
                seed=self.seed + len(self.history),
                domains=use_domains,
                store_paths=min(16, n_paths),
                train_pathway_memory=True,
                pathway_memory=self.memory,
            )
            mc_public = {k: v for k, v in mc.items() if not k.startswith("_")}
            mc_public["session_reused_prior"] = False
            self.last_domains = list(use_domains)

        self.last_mc = mc_public

        de = mc_public.get("domain_ensemble") or {}
        focus_eval = []
        for d in domains:
            if d in de:
                row = de[d]
                s_path = float(row.get("S_path_mean", row.get("S_canonical", 0.0)))
                focus_eval.append(
                    {
                        "domain": d,
                        "S": s_path,
                        "S_canonical": float(row.get("S_canonical", 0.0)),
                        "regime": "emergence" if s_path > 0 else "dispersal",
                        "D_eff": row.get("D_eff"),
                        "flip_rate": row.get("flip_rate"),
                    }
                )
            else:
                try:
                    focus_eval.append(evaluate_domain(d))
                except KeyError:
                    continue
        focus_eval.sort(key=lambda e: -abs(float(e.get("S") or 0.0)))

        contested = run_contested_physics_pack(mc_public)

        # Fuse archive engineering / fuel / preregistered predictions (ToE designs)
        from fsot_mc.discovery import classify_engineering_leads
        from fsot_mc.bio_emergence import analyze_biological_emergence

        engineering = classify_engineering_leads(mc_public, query=query, limit=8)
        bio_analysis = analyze_biological_emergence(mc_public, query=query)

        thinking = _thinking_steps(
            query, domains, mc_public, focus_eval, reused, engineering, chew
        )
        # Always attach dual-frame emergence definition when biology/% appears
        if any(
            k in query.lower()
            for k in (
                "69",
                "percent",
                "emergence",
                "biology",
                "vitality",
                "life",
                "complexity",
                "energy",
            )
        ):
            thinking.insert(
                4,
                {
                    "step": "4b_percent_definition",
                    "text": _explain_emergence_fraction(
                        mc_public.get("ensemble") or {},
                        focus_eval,
                        int(mc_public.get("n_domains") or 0),
                        int(mc_public.get("n_paths") or 0),
                        bio_analysis=bio_analysis,
                    ),
                },
            )
            hyp = bio_analysis.get("hypothesis") or {}
            thinking.insert(
                5,
                {
                    "step": "4c_bio_paradigm",
                    "text": (
                        f"Bio paradigm: map occupancy {_pct(hyp.get('map_emergence_mean'))} "
                        f"in natural band={hyp.get('in_natural_band')}; "
                        f"Biology S={hyp.get('biology_S')}; "
                        f"complexity_proxy={hyp.get('biology_complexity_proxy')}; "
                        f"energy_proxy={hyp.get('biology_energy_proxy')}."
                    ),
                },
            )

        answer = _compose_scientific_answer(
            query,
            domains,
            mc_public,
            focus_eval,
            contested,
            chew,
            {"n_turns": len(self.history)} if self.history else None,
            engineering=engineering,
            bio_analysis=bio_analysis,
            memory_recall=memory_recall,
        )

        # Train adaptive STM/LTM from this turn (seeds unchanged)
        mem_train = self.adaptive.observe_turn(
            query,
            answer,
            domains=domains,
            mc=mc_public,
            chew=chew,
        )
        # Explicit "remember" / "retain" intensifies hit
        if any(k in ql for k in ("remember", "retain", "solidify", "commit to memory")):
            self.adaptive.observe_text(
                query + " | " + answer[:400],
                source="explicit_remember",
                domains=domains,
                mc=mc_public,
                force_hit=True,
            )

        pflt = _pflt_surface_phrase(query) if with_pflt_surface else None
        lead_relay = None
        if contested.get("top"):
            lead_relay = relay_lead(contested["top"][0], use_pflt_surface=with_pflt_surface)

        eyes = eyes_with_mc(mc_public, text=query[:80]) if with_eyes else None

        self.history.append(
            {
                "t": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "domains": domains,
                "answer_preview": answer[:400],
                "n_paths": mc_public.get("n_paths"),
                "emergence_mean": (mc_public.get("ensemble") or {})
                .get("emergence_fraction", {})
                .get("mean"),
                "reused": reused,
            }
        )

        return {
            "error": None,
            "method": "fsot_monte_carlo_mind",
            "free_parameters": 0,
            "query": query,
            "thinking": {
                "process": "multipath_observer_collapse_monte_carlo",
                "toe_frame": "FSOT as unified fluid spacetime theory of everything",
                "routed_domains": domains,
                "n_paths": mc_public.get("n_paths"),
                "n_domains_simulated": mc_public.get("n_domains"),
                "session_reused_prior_mc": reused,
                "steps": thinking,
                "ensemble": mc_public.get("ensemble"),
                "focus_scalars": focus_eval[:12],
                "emergence_fraction_definition": (
                    "Mean over paths of (count of folds with S>0)/(n folds). "
                    "Not P(domain is true). Paradigm: map co-emergence / complexity occupancy."
                ),
                "discovery_hints": mc_public.get("discovery_hints"),
                "pathway_memory": mc_public.get("pathway_memory"),
                "contested": (contested or {}).get("top"),
                "engineering": engineering[:8],
                "biological_emergence": {
                    "hypothesis": (bio_analysis or {}).get("hypothesis"),
                    "corridor_coemergence": (bio_analysis or {}).get("corridor_coemergence"),
                    "life_corridor": (bio_analysis or {}).get("life_corridor"),
                    "map_stats": (bio_analysis or {}).get("map_stats"),
                },
                "adaptive_memory": {
                    "recall": memory_recall,
                    "train": mem_train,
                    "summary": self.adaptive.summary(),
                },
                "chew": chew,
                "path_stream": _stream_path_thinking(mc_public, max_paths=3) or None,
            },
            "answer": answer,
            "language": {
                "pflt_surface": pflt,
                "lead_relay": lead_relay,
                "universe_state": relay_universe_state(
                    mc_public.get("canonical_snapshot") or {},
                    mc_public.get("ensemble"),
                ),
            },
            "eyes": eyes,
            "session": {
                "n_turns": len(self.history),
                "pathway_memory": self.memory.summary(),
                "adaptive_memory": self.adaptive.summary(),
                "has_last_mc": self.last_mc is not None,
            },
            "epistemic_tier": "measured_application",
            "note": (
                "Conversational ToE intelligence: multipath FSOT simulation is the thought process. "
                "Discoveries and engineering leads require experiment; precision is not a substitute for build."
            ),
        }

    def chat(self, query: str, **kwargs: Any) -> str:
        r = self.think(query, **kwargs)
        if r.get("error"):
            return f"Error: {r['error']}"
        return str(r.get("answer") or "")


_DEFAULT_MIND: FSOTMind | None = None


def get_mind(**kwargs: Any) -> FSOTMind:
    global _DEFAULT_MIND
    if _DEFAULT_MIND is None or kwargs:
        _DEFAULT_MIND = FSOTMind(**kwargs) if kwargs else FSOTMind()
    return _DEFAULT_MIND


def ask(
    query: str,
    *,
    n_paths: int = 64,
    with_eyes: bool = False,
    with_chew: bool | None = None,
    force_new_mc: bool = False,
) -> dict[str, Any]:
    return get_mind().think(
        query,
        n_paths=n_paths,
        with_eyes=with_eyes,
        with_chew=with_chew,
        force_new_mc=force_new_mc,
    )
