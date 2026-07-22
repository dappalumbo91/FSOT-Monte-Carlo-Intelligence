"""
FSOT Monte Carlo Mind — conversational intelligence.

Thinking *is* multipath simulation under Fluid Spacetime Omni-Theory:
  query → route domain folds → run MC paths → read ensemble/bridges/leads
       → language relay answer grounded in that simulation

Not an LLM. free_parameters = 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from fsot_mc.contested_physics import run_contested_physics_pack
from fsot_mc.language_relay import relay_lead, relay_universe_state, _pflt_surface_phrase
from fsot_mc.pathway_memory import PathwayMemory, pathway_quality, pathway_signature
from fsot_mc.pi_ring import PiRing
from fsot_mc.pflt_bridge import eyes_with_mc
from fsot_mc.universe_atlas import (
    core_names,
    domain_names,
    evaluate_domain,
    get_domain,
    snapshot_universe,
)
from fsot_mc.universe_mc import run_universe_monte_carlo


# Keyword → domain folds (FSOT map, not free fits)
_DOMAIN_CUES: dict[str, list[str]] = {
    "cosmology": ["Cosmology", "Astrophysics", "Particle_Astrophysics"],
    "hubble": ["Cosmology", "Astronomy"],
    "h0": ["Cosmology"],
    "dark": ["Cosmology", "Particle_Astrophysics"],
    "quantum": ["Quantum_Mechanics", "Quantum_Optics", "Quantum_Computing", "Quantum_Gravity"],
    "particle": ["Particle_Physics", "High_Energy_Physics", "Nuclear_Physics"],
    "atom": ["Atomic_Physics", "Chemistry"],
    "chemistry": ["Chemistry", "Physical_Chemistry", "Molecular_Chemistry"],
    "biology": ["Biology", "Biochemistry", "Ecology"],
    "life": ["Biology", "Ecology", "Neuroscience"],
    "brain": ["Neuroscience", "Psychology"],
    "mind": ["Neuroscience", "Psychology", "Consciousness"],
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
    "sound": ["Acoustics"],
    "light": ["Optics", "Quantum_Optics"],
    "electric": ["Electromagnetism"],
    "economy": ["Economics", "Sociology"],
    "society": ["Sociology", "Psychology"],
    "math": ["Quantum_Computing", "Quantum_Mechanics"],
    "universe": ["Cosmology", "Astrophysics", "Quantum_Mechanics", "Biology"],
    "emergence": ["Biology", "Cosmology", "Neuroscience", "Complex"],
    "dispersal": ["Cosmology", "Quantum_Gravity"],
    "bridge": ["Quantum_Mechanics", "Cosmology", "Biology"],
    "as above": ["Cosmology", "Biology", "Quantum_Mechanics"],
    "observer": ["Quantum_Mechanics", "Neuroscience", "Cosmology"],
    "simulation": ["Cosmology", "Quantum_Mechanics", "Biology"],
}


def route_query_to_domains(query: str, *, max_domains: int = 12) -> list[str]:
    """Map natural language to FSOT domain folds via cues + name match."""
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
    # direct domain name hits
    for name in core_names():
        token = name.lower().replace("_", " ")
        if token in q or name.lower() in q.replace(" ", "_"):
            scored[name] = scored.get(name, 0.0) + 2.0
        # partial last token
        last = name.split("_")[-1].lower()
        if len(last) > 4 and last in q:
            scored[name] = scored.get(name, 0.0) + 0.5

    if not scored:
        # default universe spine
        for d in ("Cosmology", "Quantum_Mechanics", "Biology", "Neuroscience", "Chemistry"):
            try:
                get_domain(d)
                scored[d] = 1.0
            except KeyError:
                pass

    ranked = sorted(scored.items(), key=lambda x: -x[1])
    return [n for n, _ in ranked[:max_domains]]


def _thinking_trace_steps(
    query: str,
    domains: list[str],
    mc: dict[str, Any],
    focus_eval: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Human-readable thinking steps that *are* the MC process."""
    ens = mc.get("ensemble") or {}
    steps = [
        {
            "step": "1_seed_law",
            "text": (
                "I bind to FSOT law: S = K·(T1+T2+T3) from seeds π, e, φ, γ, Catalan only. "
                "free_parameters=0. Authority pin D1D38A."
            ),
        },
        {
            "step": "2_route_folds",
            "text": (
                f"Query routes to domain folds: {', '.join(domains)}. "
                "These are fractal coordinates of one fluid, not separate theories."
            ),
        },
        {
            "step": "3_multipath",
            "text": (
                f"I run multipath Monte Carlo ({mc.get('n_paths')} paths) with observer collapse: "
                "TRUE locks observed branch; FALSE is Poof decoherence. "
                "Thinking = exploring possible observation histories of the fluid."
            ),
        },
    ]
    ef = (ens.get("emergence_fraction") or {})
    if ef:
        steps.append(
            {
                "step": "4_vitality",
                "text": (
                    f"Across paths, emergence fraction mean={ef.get('mean'):.3f} "
                    f"(p10={ef.get('p10'):.3f}, p90={ef.get('p90'):.3f}). "
                    f"mean_S mean={(ens.get('mean_S') or {}).get('mean', 0):+.4f}."
                ),
            }
        )
    # focus domains
    focus_bits = []
    for ev in focus_eval[:6]:
        focus_bits.append(
            f"{ev['domain']}: S={ev['S']:+.4f} ({ev['regime']}, D_eff={ev['D_eff']})"
        )
    if focus_bits:
        steps.append(
            {
                "step": "5_focus_scalars",
                "text": "Focus fold scalars at path-mean regime: " + "; ".join(focus_bits) + ".",
            }
        )
    agree = (ens.get("ladder_agree_fraction") or {}).get("mean")
    if agree is not None:
        steps.append(
            {
                "step": "6_as_above_so_below",
                "text": (
                    f"Ladder agree fraction mean={agree:.3f} — As Above So Below bridge coherence "
                    f"across the D_eff ladder under observation."
                ),
            }
        )
    flips = (mc.get("discovery_hints") or {}).get("top_flip_domains") or []
    if flips:
        topf = ", ".join(f"{f['domain']}({f['flip_rate']:.2f})" for f in flips[:5])
        steps.append(
            {
                "step": "7_observation_sensitivity",
                "text": f"Most observation-sensitive folds (flip rates): {topf}.",
            }
        )
    steps.append(
        {
            "step": "8_answer_from_sim",
            "text": (
                "I answer only from this simulation outcome + FSOT map — "
                "not from ungrounded free-form invention."
            ),
        }
    )
    return steps


def _compose_answer(
    query: str,
    domains: list[str],
    mc: dict[str, Any],
    focus_eval: list[dict[str, Any]],
    contested: dict[str, Any] | None,
    mem_summary: dict[str, Any] | None,
) -> str:
    ens = mc.get("ensemble") or {}
    can = mc.get("canonical_snapshot") or {}
    parts: list[str] = []

    parts.append(
        f"Under FSOT multipath thinking ({mc.get('n_paths')} paths on folds "
        f"{', '.join(domains[:8])}{'…' if len(domains)>8 else ''}):"
    )

    # Domain narrative
    emerge = [e for e in focus_eval if e.get("regime") == "emergence"]
    disperse = [e for e in focus_eval if e.get("regime") == "dispersal"]
    if emerge:
        parts.append(
            "Emergence (structure forming) strongest in: "
            + ", ".join(f"{e['domain']} (S={e['S']:+.3f})" for e in emerge[:5])
            + "."
        )
    if disperse:
        parts.append(
            "Dispersal (structure fading) in: "
            + ", ".join(f"{e['domain']} (S={e['S']:+.3f})" for e in disperse[:5])
            + "."
        )

    ef = (ens.get("emergence_fraction") or {})
    if ef:
        parts.append(
            f"Ensemble vitality: emergence fraction ≈ {ef.get('mean'):.1%} "
            f"(range p10–p90: {ef.get('p10'):.1%}–{ef.get('p90'):.1%}); "
            f"observer collapse active on ~{(ens.get('collapse_true_fraction') or {}).get('mean', 0):.0%} of domain-steps."
        )

    if can:
        parts.append(
            f"Canonical map baseline: emergence {can.get('emergence_fraction', 0):.1%}, "
            f"mean_S={can.get('mean_S', 0):+.3f}."
        )

    # Bridges
    lr = mc.get("long_range_bridges") or {}
    if lr:
        best = sorted(
            lr.items(),
            key=lambda kv: -abs(float((kv[1].get("strength") or {}).get("mean") or 0)),
        )[:3]
        if best:
            bits = []
            for key, payload in best:
                st = payload.get("strength") or {}
                bits.append(f"{payload.get('a')}↔{payload.get('b')} (strength≈{st.get('mean', 0):+.3f})")
            parts.append("Long-range bridges (As Above So Below): " + "; ".join(bits) + ".")

    # Contested if cosmology-related
    ql = query.lower()
    if contested and any(k in ql for k in ("hubble", "h0", "cosmo", "dark", "universe", "tension")):
        for p in (contested.get("top") or [])[:2]:
            parts.append(
                f"Contested probe {p.get('id')}: {p.get('title')} "
                f"(score={float(p.get('score') or 0):.2f}, tier={p.get('epistemic_tier')}). "
                f"{(p.get('hypothesis') or '')[:220]}"
            )

    flips = (mc.get("discovery_hints") or {}).get("top_flip_domains") or []
    if flips and any(k in ql for k in ("flip", "observer", "sensitive", "quantum", "cosmo")):
        parts.append(
            "Observation-sensitive folds: "
            + ", ".join(f"{f['domain']} ({f['flip_rate']:.0%})" for f in flips[:4])
            + "."
        )

    if mem_summary:
        parts.append(
            f"Pathway memory: {mem_summary.get('n_patterns')} signatures seen, "
            f"{mem_summary.get('n_solidified')} solidified."
        )

    parts.append(
        "This answer is the simulation speaking — not market advice, not unconstrained LLM prose."
    )
    return " ".join(parts)


@dataclass
class FSOTMind:
    """
    Conversational Monte Carlo intelligence.
    Session holds pathway memory + last thought state.
    """

    n_paths: int = 64
    seed: int = 0
    scope: str = "core"
    memory: PathwayMemory = field(default_factory=PathwayMemory)
    history: list[dict[str, Any]] = field(default_factory=list)
    free_parameters: int = 0

    def think(
        self,
        query: str,
        *,
        n_paths: int | None = None,
        with_eyes: bool = False,
        with_pflt_surface: bool = True,
    ) -> dict[str, Any]:
        """
        Full think cycle: route → MC → trace → answer.
        """
        query = (query or "").strip()
        if not query:
            return {"error": "empty_query", "free_parameters": 0}

        n_paths = int(n_paths or self.n_paths)
        domains = route_query_to_domains(query)

        # Always include universe spine anchors for coherence
        for d in ("Cosmology", "Quantum_Mechanics"):
            if d not in domains:
                try:
                    get_domain(d)
                    domains.append(d)
                except KeyError:
                    pass

        # Thinking = multipath MC on routed folds + minimal spine for bridges
        spine = ["Cosmology", "Quantum_Mechanics", "Biology", "Neuroscience", "Chemistry"]
        use_domains = list(dict.fromkeys([*domains, *spine]))
        if self.scope == "core":
            core_set = set(core_names())
            use_domains = [d for d in use_domains if d in core_set]
            # pad with nearby core folds for ladder continuity (cap 14 for speed)
            for d in core_names():
                if d not in use_domains:
                    use_domains.append(d)
                if len(use_domains) >= 14:
                    break
            if not use_domains:
                use_domains = core_names()

        mc = run_universe_monte_carlo(
            n_paths=n_paths,
            seed=self.seed + len(self.history),
            domains=use_domains,
            store_paths=min(16, n_paths),
            train_pathway_memory=True,
            pathway_memory=self.memory,
        )
        # strip internal
        mc_public = {k: v for k, v in mc.items() if not k.startswith("_")}

        # Focus evaluate query domains at ensemble path-mean style (canonical + dS)
        de = mc_public.get("domain_ensemble") or {}
        focus_eval = []
        for d in domains:
            if d in de:
                row = de[d]
                focus_eval.append(
                    {
                        "domain": d,
                        "S": float(row.get("S_path_mean", row.get("S_canonical", 0.0))),
                        "S_canonical": float(row.get("S_canonical", 0.0)),
                        "regime": "emergence"
                        if float(row.get("S_path_mean", 0.0)) > 0
                        else "dispersal",
                        "D_eff": row.get("D_eff"),
                        "flip_rate": row.get("flip_rate"),
                    }
                )
            else:
                try:
                    ev = evaluate_domain(d)
                    focus_eval.append(ev)
                except KeyError:
                    continue
        focus_eval.sort(key=lambda e: -abs(float(e.get("S") or 0.0)))

        contested = None
        if any(k in query.lower() for k in ("hubble", "h0", "cosmo", "dark", "tension", "universe")):
            contested = run_contested_physics_pack(mc_public)

        thinking = _thinking_trace_steps(query, domains, mc_public, focus_eval)
        answer = _compose_answer(
            query,
            domains,
            mc_public,
            focus_eval,
            contested,
            mc_public.get("pathway_memory"),
        )

        # Language surfaces
        pflt = _pflt_surface_phrase(query) if with_pflt_surface else None
        # Relay top related lead if contested
        lead_relay = None
        if contested and contested.get("top"):
            lead_relay = relay_lead(contested["top"][0], use_pflt_surface=with_pflt_surface)

        eyes = None
        if with_eyes:
            eyes = eyes_with_mc(mc_public, text=query[:80])

        # Session memory of thought
        thought = {
            "t": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "domains": domains,
            "answer": answer,
            "n_paths": n_paths,
            "emergence_mean": (mc_public.get("ensemble") or {}).get("emergence_fraction", {}).get(
                "mean"
            ),
        }
        self.history.append(thought)

        return {
            "error": None,
            "method": "fsot_monte_carlo_mind",
            "free_parameters": 0,
            "query": query,
            "thinking": {
                "process": "multipath_observer_collapse_monte_carlo",
                "routed_domains": domains,
                "simulated_domains": use_domains if len(use_domains) <= 40 else f"{len(use_domains)} domains",
                "n_paths": n_paths,
                "steps": thinking,
                "ensemble": mc_public.get("ensemble"),
                "focus_scalars": focus_eval[:10],
                "discovery_hints": mc_public.get("discovery_hints"),
                "pathway_memory": mc_public.get("pathway_memory"),
                "contested": (contested or {}).get("top") if contested else None,
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
            },
            "epistemic_tier": "measured_application",
            "note": (
                "Conversational FSOT intelligence: the Monte Carlo multipath run *is* the thinking. "
                "Answers are grounded in simulation outcomes."
            ),
        }

    def chat(self, query: str, **kwargs: Any) -> str:
        """Convenience: return answer string only."""
        r = self.think(query, **kwargs)
        if r.get("error"):
            return f"Error: {r['error']}"
        return str(r.get("answer") or "")


# Module-level mind for REPL
_DEFAULT_MIND: FSOTMind | None = None


def get_mind(**kwargs: Any) -> FSOTMind:
    global _DEFAULT_MIND
    if _DEFAULT_MIND is None or kwargs:
        _DEFAULT_MIND = FSOTMind(**kwargs) if kwargs else FSOTMind()
    return _DEFAULT_MIND


def ask(query: str, *, n_paths: int = 64, with_eyes: bool = False) -> dict[str, Any]:
    """One-shot query to the FSOT Monte Carlo mind."""
    return get_mind().think(query, n_paths=n_paths, with_eyes=with_eyes)
