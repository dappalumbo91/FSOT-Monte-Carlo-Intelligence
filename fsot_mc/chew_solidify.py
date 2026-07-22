"""
Batch chew → adaptive LTM solidification.

Ingest science queries / topics into AdaptiveMemory with multipath co-sign so the
mind retains new information without moving seeds.
"""

from __future__ import annotations

from typing import Any

from fsot_mc.adaptive_memory import AdaptiveMemory
from fsot_mc.api_adapters import chew_science_text
from fsot_mc.mind import route_query_to_domains
from fsot_mc.universe_mc import run_universe_monte_carlo


DEFAULT_TOPICS = [
    "fluid spacetime cosmology Hubble tension",
    "quantum mechanics observer collapse",
    "biological complexity emergence intermediate scales",
    "general relativity versus unified field architecture",
    "nuclear fusion and thermochemistry fuels",
    "neuroscience consciousness neural circuits",
    "dark energy equation of state w_a DESI",
    "As Above So Below cross-scale coupling",
]


def solidify_topic(
    topic: str,
    *,
    mem: AdaptiveMemory | None = None,
    n_paths: int = 24,
    seed: int = 0,
    with_chew: bool = True,
    online_hint: bool = False,
) -> dict[str, Any]:
    mem = mem or AdaptiveMemory()
    domains = route_query_to_domains(topic)
    chew = None
    if with_chew:
        chew = chew_science_text(topic)

    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        domains=domains[:14] if domains else None,
        store_paths=4,
        train_pathway_memory=False,
    )
    mc_public = {k: v for k, v in (mc or {}).items() if not k.startswith("_")}

    results = []
    # Observe topic itself multiple times with force toward solidify
    for i in range(3):
        results.append(
            mem.observe_text(
                topic,
                source=f"chew_batch:{i}",
                domains=domains,
                mc=mc_public if not mc_public.get("error") else None,
                force_hit=True,
            )
        )
    if chew and chew.get("ok"):
        excerpt = f"{chew.get('title') or topic}\n{chew.get('excerpt') or ''}"
        for i in range(5):
            results.append(
                mem.observe_text(
                    excerpt,
                    source=str(chew.get("source") or "chew"),
                    domains=domains,
                    mc=mc_public if not mc_public.get("error") else None,
                    chew_ok=True,
                    force_hit=True,
                )
            )
    if mc_public and not mc_public.get("error"):
        results.append(mem.observe_mc_summary(mc_public, query=topic))

    last = results[-1] if results else {}
    return {
        "ok": True,
        "topic": topic,
        "domains": domains,
        "chew": {
            "ok": bool(chew and chew.get("ok")),
            "source": (chew or {}).get("source"),
            "title": (chew or {}).get("title"),
            "n_chars": (chew or {}).get("n_chars"),
        },
        "n_observe_steps": len(results),
        "last": last,
        "memory_summary": mem.summary(),
        "free_parameters": 0,
    }


def solidify_corpus(
    topics: list[str] | None = None,
    *,
    n_paths: int = 20,
    seed: int = 0,
) -> dict[str, Any]:
    topics = topics or DEFAULT_TOPICS
    mem = AdaptiveMemory()
    runs = []
    for i, t in enumerate(topics):
        runs.append(
            solidify_topic(
                t,
                mem=mem,
                n_paths=n_paths,
                seed=seed + i,
                with_chew=True,
            )
        )
    return {
        "ok": True,
        "n_topics": len(topics),
        "runs": runs,
        "memory_summary": mem.summary(),
        "free_parameters": 0,
        "note": (
            "Batch chew solidification into LTM. Seeds unchanged. "
            "Solidify bars are φ-EWMA + Poof; repeated force_hit accelerates training for demos."
        ),
    }
