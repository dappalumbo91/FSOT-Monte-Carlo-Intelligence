"""
Generate per-node scientific markdown theses for the FSOT connective graph.

Each fold / seed / route / prediction becomes a research-style document:
  Abstract · Ontology · Mathematical formulation · Results · Application ·
  Connective tissue · Epistemics · References

Source of truth: atlas + archive connective compact + predictions + seed engine.
free_parameters = 0. Authority D1D38A.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.archive_connective import get_connective_tissue
from fsot_mc.archive_predictions import load_preregistered_predictions
from fsot_mc.fast import (
    A_BLEED,
    A_IN,
    ALPHA,
    C_FACTOR,
    C_EFF,
    CHAOS,
    E,
    ETA_EFF,
    G_CAT,
    GAMMA,
    K,
    PHI,
    PI,
    POOF,
    PSI_CON,
    THETA_S,
)
from fsot_mc.paths import PACKAGE_ROOT
from fsot_mc.universe_atlas import core_names, evaluate_domain, get_domain, load_atlas

TISSUE_ROOT = PACKAGE_ROOT / "docs" / "tissue"
AUTHORITY = "D1D38A185487B452E470AC68ECE2EB45AEB1CA9CE25FC9BF9564C19633FFBE70"
FORMULA = "S = K · (T1 + T2 + T3)"


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-.]+", "_", str(s).strip())
    return s.strip("_") or "node"


def _md_escape(s: Any) -> str:
    return str(s).replace("|", "\\|")


def _pct(x: float | None) -> str:
    if x is None:
        return "n/a"
    return f"{float(x):.6f}%"


def seed_docs() -> list[dict[str, Any]]:
    """Scientific metadata for fixed seeds and law constant."""
    return [
        {
            "id": "seed_pi",
            "kind": "seed",
            "title": "Seed π — Circular Phase Base",
            "symbol": "π",
            "value": float(PI),
            "role": "Transcendental base for phase geometry, circle measure, and α / η constructions.",
            "derivations": [
                r"\(\alpha = \ln\pi / (e\,\varphi^{13})\)",
                r"\(\eta_{\mathrm{eff}} = 1/(\pi - 1)\)",
                r"\(\mathrm{Poof}\) and bleed amplitudes use \(\pi\) in trig and log arguments.",
            ],
            "application": (
                "Locks angular / acoustic structure of the fluid; appears in cosmology bleed "
                "and dimensional logarithms of T1."
            ),
        },
        {
            "id": "seed_e",
            "kind": "seed",
            "title": "Seed e — Natural Growth Base",
            "symbol": "e",
            "value": float(E),
            "role": "Base of continuous growth and exponential map for coherence and Poof.",
            "derivations": [
                r"\(\psi_{\mathrm{con}} = 1 - e^{-1}\)",
                r"Growth factor \(\exp(\alpha\cdot\ldots)\) in T1",
                r"\(\mathrm{Poof} = \exp\bigl((-\ln\pi/e)/(\eta_{\mathrm{eff}}\ln\varphi)\bigr)\)",
            ],
            "application": "Growth vs decoherence balance; observer coupling scale.",
        },
        {
            "id": "seed_phi",
            "kind": "seed",
            "title": "Seed φ — Golden Self-Similarity",
            "symbol": "φ",
            "value": float(PHI),
            "role": "Self-similar scaling across D_eff ladder; partitions weights and K.",
            "derivations": [
                r"\(\varphi = (1+\sqrt{5})/2\)",
                r"\(K \propto \varphi\cdot(\gamma/e)\cdot\sqrt{2}/\ln\pi\)",
                r"Acoustic mix weights \(\propto 1/\varphi\)",
            ],
            "application": "Cross-scale As Above So Below self-similarity; memory φ-EWMA.",
        },
        {
            "id": "seed_gamma",
            "kind": "seed",
            "title": "Seed γ — Euler–Mascheroni Harmonic Offset",
            "symbol": "γ",
            "value": float(GAMMA),
            "role": "Harmonic / logarithmic offset entering base probability and K.",
            "derivations": [
                r"\(P_{\mathrm{base}} = \gamma/e\)",
                r"\(K = \varphi\cdot(\gamma/e)\cdot\sqrt{2}/\ln\pi\cdot 0.99\)",
            ],
            "application": "Sets overall scale of raw_S without free parameters.",
        },
        {
            "id": "seed_catalan",
            "kind": "seed",
            "title": "Seed G — Catalan Acoustic Constant",
            "symbol": "G",
            "value": float(G_CAT),
            "role": "Catalan's constant; acoustic / bleed refinement of C_eff.",
            "derivations": [
                r"\(C_{\mathrm{eff}} = (1 - \mathrm{Poof}\sin\theta_s)\,(1 + 0.01\,G/(\pi\varphi))\)",
            ],
            "application": "Fine structure of fluid efficiency and acoustic channel.",
        },
        {
            "id": "law_K",
            "kind": "law",
            "title": "Law Scalar K — Zero Free-Parameter Pre-factor",
            "symbol": "K",
            "value": float(K),
            "role": f"Global prefactor of the ToE law {FORMULA}. Derived only from seeds.",
            "derivations": [
                r"\(K = \varphi\cdot(\gamma/e)\cdot\sqrt{2}/\ln\pi\cdot 0.99\)",
                r"\(S = K(T_1 + T_2 + T_3)\)",
                f"Authority pin SHA-256 prefix D1D38A…",
            ],
            "application": (
                "Every domain fold uses the same K. Changing K would break free_parameters=0 "
                "and the multi-prover pin."
            ),
        },
    ]


def _engine_constants_block() -> str:
    return f"""### Seed-derived constants (this workspace)

| Symbol | Value | Role |
|--------|------:|------|
| π | {PI:.15g} | phase / circle |
| e | {E:.15g} | growth |
| φ | {PHI:.15g} | self-similarity |
| γ | {GAMMA:.15g} | harmonic offset |
| G (Catalan) | {G_CAT:.15g} | acoustic refinement |
| K | {K:.15g} | law prefactor |
| Poof | {POOF:.15g} | decoherence floor |
| α | {ALPHA:.15g} | growth rate |
| η_eff | {ETA_EFF:.15g} | effective viscosity-like scale |
| C_eff | {C_EFF:.15g} | efficiency |
| A_bleed | {A_BLEED:.15g} | acoustic bleed |
| A_in | {A_IN:.15g} | acoustic inflow |
| C_factor | {C_FACTOR:.15g} | observer coupling scale |
| ψ_con | {PSI_CON:.15g} | consciousness factor base |
| θ_s | {THETA_S:.15g} | structural angle |
| chaos | {CHAOS:.15g} | chaos channel |

**Law:** `{FORMULA}` with `free_parameters = 0`, authority **D1D38A**.
"""


def _math_formulation_domain(ev: dict[str, Any]) -> str:
    D = ev.get("D_eff")
    dp = ev.get("delta_psi")
    return f"""### Domain inputs (fractal coordinates, not free fits)

| Input | Value | Meaning |
|-------|------:|---------|
| D_eff | {D} | effective depth on the 25D fluid ladder |
| δψ | {dp} | phase offset of this fold |
| δθ | {ev.get("delta_theta")} | acoustic / valve angle |
| recent_hits | {ev.get("recent_hits")} | local hit memory |
| observed | {ev.get("observed")} | observer branch active |

### Term decomposition (this fold)

\\[
S = K(T_1 + T_2 + T_3)
\\]

| Term | Value | Interpretation |
|------|------:|----------------|
| T1 | {float(ev.get("T1") or 0):+.8f} | coherence / growth / quirk_mod channel |
| T2 | {float(ev.get("T2") or 0):+.8f} | scale / amplitude structure |
| T3 | {float(ev.get("T3") or 0):+.8e} | valve + acoustic + chaos channel |
| K | {float(ev.get("K") or K):+.8f} | seed-derived prefactor |
| **S** | **{float(ev.get("S") or 0):+.8f}** | vitality scalar |

### Regime

\\[
\\mathrm{{regime}} =
\\begin{{cases}}
\\text{{emergence}} & S > 0 \\\\
\\text{{dispersal}} & S \\le 0
\\end{{cases}}
\\]

**This fold:** `{ev.get("regime")}` at \(D_{{\\mathrm{{eff}}}}={D}\).
"""


def _neighbors(
    node_id: str,
    edges: list[dict[str, Any]],
    *,
    limit: int = 24,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    out_e, in_e = [], []
    for e in edges:
        if e.get("source") == node_id:
            out_e.append(e)
        if e.get("target") == node_id:
            in_e.append(e)
    # prioritize structural
    def rank(e: dict[str, Any]) -> float:
        k = str(e.get("kind") or "")
        score = float(e.get("strength") or 0)
        if "route" in k:
            score += 2
        if "long_range" in k or "problem" in k:
            score += 1.5
        if "coupling_lean" in k or "membership" in k:
            score -= 0.5
        return -score

    out_e.sort(key=rank)
    in_e.sort(key=rank)
    return out_e[:limit], in_e[:limit]


def _connective_md(
    node_id: str,
    edges: list[dict[str, Any]],
    id_to_label: dict[str, str],
) -> str:
    outs, ins = _neighbors(node_id, edges)
    lines = ["## Connective tissue", ""]
    lines.append("Links are archive routes, domain-coupling validations, multipath bridges, or seed law feeders.")
    lines.append("")
    if outs:
        lines.append("### Outbound axons")
        lines.append("")
        lines.append("| Target | Kind | Layer | Strength | Error % |")
        lines.append("|--------|------|-------|----------|---------|")
        for e in outs:
            tid = e.get("target")
            lab = id_to_label.get(tid, tid)
            err = e.get("error_pct")
            lines.append(
                f"| [{_md_escape(lab)}]({_rel_link(tid)}) | `{e.get('kind')}` | `{e.get('layer')}` | "
                f"{float(e.get('strength') or 0):.3f} | {_pct(err if err is not None else None)} |"
            )
        lines.append("")
    if ins:
        lines.append("### Inbound axons")
        lines.append("")
        lines.append("| Source | Kind | Layer | Strength | Error % |")
        lines.append("|--------|------|-------|----------|---------|")
        for e in ins:
            sid = e.get("source")
            lab = id_to_label.get(sid, sid)
            err = e.get("error_pct")
            lines.append(
                f"| [{_md_escape(lab)}]({_rel_link(sid)}) | `{e.get('kind')}` | `{e.get('layer')}` | "
                f"{float(e.get('strength') or 0):.3f} | {_pct(err if err is not None else None)} |"
            )
        lines.append("")
    if not outs and not ins:
        lines.append("_No compact-graph edges recorded for this node (may still couple via full 39k raw matrix)._")
        lines.append("")
    return "\n".join(lines)


def _rel_link(node_id: str) -> str:
    """Relative link path within docs/tissue."""
    if not node_id:
        return "INDEX.md"
    if node_id.startswith("seed_") or node_id == "law_K":
        return f"seeds/{_slug(node_id)}.md"
    if node_id.startswith("intent_"):
        return f"routes/{_slug(node_id)}.md"
    if node_id.startswith("pred_"):
        return f"predictions/{_slug(node_id)}.md"
    if node_id.startswith("mem_"):
        return f"memory/{_slug(node_id)}.md"
    if node_id.startswith("dom_"):
        return f"domains/{_slug(node_id[4:])}.md"
    return f"domains/{_slug(node_id)}.md"


def render_seed_md(meta: dict[str, Any], edges: list[dict[str, Any]], id_to_label: dict[str, str]) -> str:
    nid = meta["id"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    deriv = "\n".join(f"- {d}" for d in meta.get("derivations") or [])
    body = f"""# {meta["title"]}

> **Tissue ID:** `{nid}` | **Kind:** {meta["kind"]} | **Symbol:** {meta.get("symbol")}  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** {now}

## Abstract

This document is a miniature scientific thesis for the FSOT seed/law node **{meta.get("symbol")}**.
It is not a free parameter: its value is fixed by mathematics / seed derivation and participates
in every domain fold of the fluid spacetime engine.

**Role:** {meta.get("role")}

## Ontology

Under Fluid Spacetime Omni-Theory, physical constants of the law layer are **seeds**, not fitted
couplings. Domains are folds of one 25D fluid; seeds propagate through **K** into \(T_1,T_2,T_3\).

## Mathematical formulation

**Numeric value:** `{meta.get("value"):.15g}`

### Derivations / appearances

{deriv}

{_engine_constants_block()}

## Results

| Quantity | Value |
|----------|------:|
| Symbol | {meta.get("symbol")} |
| Value | {meta.get("value"):.15g} |
| Pin | D1D38A |
| Free parameters introduced | **0** |

## Application

{meta.get("application")}

In the Monte Carlo mind and visual graph, this node sits at **ring 0** (seed hub) and feeds the
law scalar / domain folds. Changing it would invalidate the multi-prover authority pin.

{_connective_md(nid, edges, id_to_label)}

## Epistemics

| Field | Value |
|-------|-------|
| Epistemic tier | `law` / seed (immutable relative to discovery runtime) |
| Falsification | Drift of float engine vs pin D1D38A fails authority gate |
| Relation to ≤0.5% green gate | Seeds are not empirical observables; they *generate* panel predictions |

## References

- FSOT-2.1-Lean formal spine (multi-prover)
- `fsot_mc/fast.py` / `compute_authority.py` (this repo)
- Physical Archive pin & certificates under `vendor/archive_bundle/`
- Parent methodology: [../../METHODOLOGY.md](../../METHODOLOGY.md)

---
*FSOT Monte Carlo Intelligence · tissue documentation system · seeds never move.*
"""
    return body


def render_domain_md(
    node: dict[str, Any],
    edges: list[dict[str, Any]],
    id_to_label: dict[str, str],
    *,
    eval_row: dict[str, Any] | None = None,
) -> str:
    name = node.get("domain") or node.get("label") or "Unknown"
    nid = node.get("id") or f"dom_{name}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_core = bool(node.get("is_core") or node.get("kind") == "domain")
    kind_label = "Core NeuroLab fold" if is_core else "Extension / validation panel"
    err = node.get("median_error_pct")
    cov = node.get("coverage_tier") or "—"
    records = node.get("record_count")
    rtc = node.get("routes_to_core")
    lean = node.get("lean_module")
    tags = node.get("tags") or []
    maps = node.get("maps_to_lean") or []

    # evaluate if core-like and in atlas
    ev = eval_row
    if ev is None:
        try:
            ev = evaluate_domain(str(name))
        except Exception:
            ev = None

    S = node.get("S") if node.get("S") is not None else (ev.get("S") if ev else None)
    regime = node.get("regime") or (ev.get("regime") if ev else None)
    D = node.get("D_eff") or (ev.get("D_eff") if ev else None)

    math_block = _math_formulation_domain(ev) if ev else f"""### Domain coordinates

| Field | Value |
|-------|------:|
| D_eff | {D} |
| S (atlas/path) | {S} |
| regime | {regime} |
| routes_to_core | {rtc or "—"} |

Full T1/T2/T3 decomposition is available for atlas-resolved folds; this panel may be extension-only.
"""

    green = "PASS within 0.5% green gate" if err is not None and float(err) <= 0.5 else (
        "n/a" if err is None else "outside 0.5% gate (refinement / contested)"
    )

    abstract = (
        f"Scientific tissue note for **{name}**, a {kind_label} in the FSOT domain map. "
        f"Vitality scalar S={S if S is not None else 'n/a'} at D_eff={D}; regime **{regime or 'n/a'}**. "
        f"Empirical panel median error { _pct(err) if err is not None else 'not attached in compact tissue' } "
        f"({green}). "
        "This fold shares the single seed engine with cosmology, quantum, life, and engineering panels."
    )

    apps = []
    if is_core:
        apps.append(
            "Core fold participates in multipath Monte Carlo thought (observer collapse histories)."
        )
        apps.append(
            "Used for As Above So Below bridge probes (e.g. Biology↔Cosmology, QM↔Cosmology)."
        )
    else:
        apps.append(
            "Extension panel: specialized empirical / formal obligations routing into a core fold."
        )
        apps.append(
            "Contributes to archive green-gate statistics and domain-coupling validation edges."
        )
    if "fuel" in str(name).lower() or "Fuel" in str(name):
        apps.append("Engineering / fuel designs: see preregistered PRED-* protocols.")
    if any("bridge" in str(t).lower() for t in tags) or "Bridge" in str(name):
        apps.append("Tagged as cross-scale bridge tissue — high priority for connective visualization.")

    tags_s = ", ".join(f"`{t}`" for t in tags) if tags else "_none listed_"
    maps_s = ", ".join(f"`{m}`" for m in maps) if maps else "_none listed_"

    body = f"""# {name.replace("_", " ")}

> **Tissue ID:** `{nid}` | **Kind:** {kind_label}  
> **Cluster / group:** `{node.get("cluster") or node.get("group")}` | **Ring:** {node.get("ring")}  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** {now}

## Abstract

{abstract}

## Ontology

FSOT treats scientific domains as **folds** of one 25D fluid condensate, not independent
fitted models. Coordinates \((D_{{\\mathrm{{eff}}}}, \\delta\\psi, \\ldots)\) are preregistered fractal
addresses of the same engine \(S = K(T_1+T_2+T_3)\).

| Property | Value |
|----------|------|
| Atlas kind | `{node.get("atlas_kind") or node.get("kind")}` |
| Core NeuroLab | {"yes" if is_core else "no"} |
| Coverage tier | `{cov}` |
| Record count | {records if records is not None else "n/a"} |
| Lean module | `{lean or "n/a"}` |
| Tags | {tags_s} |
| maps_to_lean | {maps_s} |
| routes_to_core | `{rtc or "n/a"}` |

## Mathematical formulation

{_engine_constants_block()}

{math_block}

## Results

| Metric | Value | Notes |
|--------|------:|-------|
| S | {f"{float(S):+.8f}" if S is not None else "n/a"} | vitality scalar |
| Regime | {regime or "n/a"} | emergence if S>0 |
| D_eff | {D if D is not None else "n/a"} | ladder depth |
| median_error_pct | {_pct(err) if err is not None else "n/a"} | archive panel (if any) |
| Green gate <=0.5% | {green} | Physical Archive standard |
| Canonical S (atlas) | {node.get("S") if node.get("S") is not None else (ev.get("S_canonical") if ev else "n/a")} | zero-noise baseline when available |

### Interpretation

- **Emergence (S>0):** structure-forming vitality at this scale.
- **Dispersal (S≤0):** dispersal / damping regime (still lawful; not "failure").
- **High flip_rate under multipath** (when present): observer-sensitive fold — priority for experiment.

## Application

{chr(10).join("- " + a for a in apps)}

### Scientific use in this product

1. **Monte Carlo multipath** — domain participates in map co-emergence occupancy statistics.
2. **Discovery ledger** — bridges / flips / engineering leads may cite this fold.
3. **Visual connective mind** — node in neural/Obsidian multi-scale graph.
4. **Formal soft court** — Lean module `{lean or "n/a"}` for batch obligation promotion when applicable.

{_connective_md(nid, edges, id_to_label)}

## Epistemics

| Field | Value |
|-------|-------|
| Epistemic tier | `measured` if green-gate panel; else `scaffold` / extension metadata |
| free_parameters | 0 |
| Authority | D1D38A |
| Kill / refinement | Panel error >0.5% or sign mismatch queues refinement (archive doctrine) |

## References

- Physical Archive domain navigator & coupling simulation (synced subset)
- `vendor/archive_bundle/data__scientific_domain_expansion_map.json`
- `vendor/archive_bundle/data__connective_tissue_compact.json`
- Methodology: [../../METHODOLOGY.md](../../METHODOLOGY.md)
- Accuracy: run `python -m fsot_mc readings`

---
*FSOT Monte Carlo Intelligence · tissue documentation · one fluid, many folds.*
"""
    return body


def render_route_md(node: dict[str, Any], edges: list[dict[str, Any]], id_to_label: dict[str, str]) -> str:
    nid = node["id"]
    intent = node.get("label") or nid
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    kws = node.get("keywords") or []
    panels = node.get("panels") or []
    core = node.get("core_domain")
    return f"""# Problem Route: {intent}

> **Tissue ID:** `{nid}` | **Kind:** problem_route intent hub  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** {now}

## Abstract

Navigator **problem route** linking a scientific intent to a core domain and specialized
depth panels. This is connective tissue for *how questions map into FSOT folds*.

## Ontology

Problem routes are not free-parameter models. They are **routing metadata** from the
Physical Archive domain navigator: keywords → core fold → extension panels with benchmarks.

| Field | Value |
|-------|-------|
| Intent | `{intent}` |
| Core domain | `{core}` |
| Keywords | {", ".join(f"`{k}`" for k in kws) or "—"} |
| Panels | {", ".join(f"`{p}`" for p in panels) or "—"} |

## Mathematical formulation

Routing is discrete; underlying panels still obey:

\\[
S = K(T_1+T_2+T_3)
\\]

with domain-specific \((D_{{\\mathrm{{eff}}}},\\delta\\psi)\). Intent hubs do not introduce new constants.

## Results

Intent hubs enable discovery queries and visual clustering of related validation panels.
Associated panels carry their own median_error_pct under the ≤0.5% green gate.

## Application

- Mind / CLI query routing densification
- Download / repro bundles in full archive (`download_bundles` on navigator)
- Visual pink hubs in the connective graph

{_connective_md(nid, edges, id_to_label)}

## Epistemics

| Tier | `scaffold` routing metadata over measured panels |
| Free parameters | 0 |

## References

- `vendor/archive_bundle/data__fsot_domain_navigator.json` → `problem_routes`
- [../../METHODOLOGY.md](../../METHODOLOGY.md)

---
*FSOT tissue doc · problem route.*
"""


def render_prediction_md(pred: dict[str, Any], edges: list[dict[str, Any]], id_to_label: dict[str, str]) -> str:
    pid = str(pred.get("id") or "PRED")
    nid = f"pred_{pid}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""# {pid}: {pred.get("name")}

> **Tissue ID:** `{nid}` | **Kind:** preregistered prediction  
> **Domain:** `{pred.get("domain")}` | **Branch:** `{pred.get("fsot_formula_branch")}`  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** {now}

## Abstract

Preregistered FSOT prediction with explicit SOTA baseline and **kill discriminant**.
Engineering / observational designs are ToE-derived leads — experiment still closes the loop.

## Ontology

Predictions are not post-hoc curve fits. They state a seed-engine value, a comparison baseline,
and a pre-registered discriminant (falsification criterion).

## Mathematical formulation

| Field | Value |
|-------|------:|
| FSOT predicted | {pred.get("fsot_predicted")} |
| Unit | {pred.get("unit")} |
| Formula branch | `{pred.get("fsot_formula_branch")}` |
| SOTA baseline | {pred.get("sota_baseline")} |
| SOTA label | {pred.get("sota_label")} |
| Discriminant | `{pred.get("discriminant")}` |

Underlying engine remains \(S=K(T_1+T_2+T_3)\) on the stated branch.

## Results

| Item | Value |
|------|------:|
| Predicted | {pred.get("fsot_predicted")} {pred.get("unit") or ""} |
| Baseline | {pred.get("sota_baseline")} ({pred.get("sota_label")}) |
| Registered | {pred.get("registered_at") or "—"} |

### Notes

{pred.get("note") or "_No extended note in manifest._"}

## Application

- Lab / desktop experiment protocols (`python -m fsot_mc protocols`)
- Engineering discovery (fuels, devices, cosmology anchors)
- Visual gold nodes on the connective graph

### Pass / kill

- **Pass:** discriminant satisfied; pin D1D38A verified; no free-parameter retune
- **Kill:** discriminant fails; or requires free fit to match data

{_connective_md(nid, edges, id_to_label)}

## Epistemics

| Tier | `preregistered_design` |
| Free parameters | 0 |
| Closure | physical experiment / measurement |

## References

- `vendor/archive_bundle/data__preregistered_predictions_manifest.yaml`
- Experiment protocols API / CLI
- [../../ACHIEVEMENTS.md](../../ACHIEVEMENTS.md)

---
*FSOT tissue doc · preregistered prediction.*
"""


def generate_all_tissue_docs(
    *,
    write: bool = True,
    include_predictions: bool = True,
) -> dict[str, Any]:
    """Generate full scientific markdown library for graph nodes."""
    tissue = get_connective_tissue()
    nodes = tissue.get("nodes") or []
    edges = tissue.get("edges") or []
    id_to_label = {n["id"]: n.get("label") or n.get("domain") or n["id"] for n in nodes}
    # seeds
    for s in seed_docs():
        id_to_label[s["id"]] = s.get("symbol") or s["id"]

    written: list[str] = []
    errors: list[str] = []

    def write_doc(rel: str, content: str) -> None:
        path = TISSUE_ROOT / rel
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        written.append(str(rel).replace("\\", "/"))

    # Seeds
    for s in seed_docs():
        write_doc(f"seeds/{_slug(s['id'])}.md", render_seed_md(s, edges, id_to_label))

    # Domains + extensions + problem routes from tissue
    for n in nodes:
        kind = n.get("kind")
        nid = n.get("id") or ""
        try:
            if kind == "problem_route":
                write_doc(f"routes/{_slug(nid)}.md", render_route_md(n, edges, id_to_label))
            elif kind in ("domain", "extension") or n.get("domain"):
                name = n.get("domain") or nid.replace("dom_", "")
                write_doc(f"domains/{_slug(name)}.md", render_domain_md(n, edges, id_to_label))
            elif kind == "seed" or kind == "law":
                continue  # handled
            else:
                # generic domain-like
                if n.get("domain"):
                    write_doc(
                        f"domains/{_slug(n['domain'])}.md",
                        render_domain_md(n, edges, id_to_label),
                    )
        except Exception as exc:
            errors.append(f"{nid}: {exc}")

    # Predictions
    if include_predictions:
        for p in load_preregistered_predictions():
            pid = str(p.get("id") or "")
            if not pid:
                continue
            nid = f"pred_{pid}"
            id_to_label[nid] = pid
            write_doc(f"predictions/{_slug(nid)}.md", render_prediction_md(p, edges, id_to_label))

    # INDEX
    domain_files = sorted([w for w in written if w.startswith("domains/")])
    seed_files = sorted([w for w in written if w.startswith("seeds/")])
    route_files = sorted([w for w in written if w.startswith("routes/")])
    pred_files = sorted([w for w in written if w.startswith("predictions/")])

    index = f"""# FSOT Tissue Documentation Library

**Scientific markdown theses for every rendered connective-graph node.**

| | |
|--|--|
| Generated (UTC) | {datetime.now(timezone.utc).isoformat()} |
| Authority | D1D38A |
| free_parameters | 0 |
| Law | `{FORMULA}` |
| Documents | **{len(written)}** |

## How to read a tissue note

Each file is a **miniature research document**:

1. **Abstract** — what the node is in the ToE  
2. **Ontology** — fold / seed / route / prediction  
3. **Mathematical formulation** — formulas + term tables  
4. **Results** — S, regime, median_error_pct, green gate  
5. **Application** — multipath, discovery, experiment  
6. **Connective tissue** — linked axons to other notes  
7. **Epistemics** — tier + falsification  

## Seeds & law ({len(seed_files)})

{chr(10).join(f"- [{p}]({p})" for p in seed_files)}

## Domain folds & extension panels ({len(domain_files)})

{chr(10).join(f"- [{p}]({p})" for p in domain_files)}

## Problem routes ({len(route_files)})

{chr(10).join(f"- [{p}]({p})" for p in route_files)}

## Preregistered predictions ({len(pred_files)})

{chr(10).join(f"- [{p}]({p})" for p in pred_files)}

## Parent docs

- [Methodology](../METHODOLOGY.md)
- [Reproducibility](../REPRODUCIBILITY.md)
- [Achievements](../ACHIEVEMENTS.md)
- [Memory architecture](../MEMORY_ARCHITECTURE.md)

## Regenerate

```powershell
python -m fsot_mc tissue-docs
```

Or API: `GET /api/tissue` · `GET /api/tissue/{{id}}`

---
*One fluid · many folds · every node a thesis.*
"""
    write_doc("INDEX.md", index)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_docs": len(written),
        "n_errors": len(errors),
        "errors": errors[:50],
        "files": written,
        "free_parameters": 0,
        "authority": AUTHORITY[:12] + "…",
    }
    if write:
        (TISSUE_ROOT / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
    return manifest


def resolve_doc_path(node_id: str) -> Path | None:
    """Map graph node id → markdown path if present."""
    if not node_id:
        return None
    nid = str(node_id).strip()
    # candidates in order
    candidates: list[Path] = []
    rel = _rel_link(nid)
    if not rel.startswith("http"):
        candidates.append(TISSUE_ROOT / rel)
    if nid.startswith("dom_"):
        candidates.append(TISSUE_ROOT / "domains" / f"{_slug(nid[4:])}.md")
    if nid.startswith("pred_"):
        candidates.append(TISSUE_ROOT / "predictions" / f"{_slug(nid)}.md")
    if nid.startswith("intent_"):
        candidates.append(TISSUE_ROOT / "routes" / f"{_slug(nid)}.md")
    if nid.startswith("seed_") or nid == "law_K":
        candidates.append(TISSUE_ROOT / "seeds" / f"{_slug(nid)}.md")
    # bare domain name
    candidates.append(TISSUE_ROOT / "domains" / f"{_slug(nid)}.md")
    # case-insensitive scan of domains if needed
    for p in candidates:
        if p.is_file():
            return p
    # fuzzy: match domain file ignoring case
    domains_dir = TISSUE_ROOT / "domains"
    if domains_dir.is_dir():
        target = _slug(nid[4:] if nid.startswith("dom_") else nid).lower()
        for f in domains_dir.glob("*.md"):
            if f.stem.lower() == target:
                return f
    return None


def get_tissue_doc(node_id: str) -> dict[str, Any]:
    path = resolve_doc_path(node_id)
    if path is None:
        return {
            "ok": False,
            "error": "not_found",
            "id": node_id,
            "hint": "python -m fsot_mc tissue-docs  then restart serve",
            "tissue_root": str(TISSUE_ROOT),
        }
    return {
        "ok": True,
        "id": node_id,
        "path": str(path.relative_to(PACKAGE_ROOT)).replace("\\", "/"),
        "markdown": path.read_text(encoding="utf-8"),
        "free_parameters": 0,
    }
