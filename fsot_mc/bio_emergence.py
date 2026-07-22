"""
Biological emergence under FSOT — paradigm-shift science layer.

Paradigm: life is not an extra ontology bolted onto physics. Under FSOT ToE,
biology is a *fold* of the same 25D fluid at intermediate D_eff. The multipath
emergence fraction (~60–70%, often quoted ~69%) is:

  OPERATIONAL
    mean over paths of (count of folds with S>0) / (n folds)
    = map co-emergence occupancy under observer-coupled sampling.

  PARADIGM INTERPRETATION (ToE hypothesis, experiment-gated)
    That occupancy is the *natural co-emergence window* of the multi-scale map —
    how much of the universe’s domain ladder sits in structure-forming regime
    when intermediate-depth folds (chemistry → biology → ecology → mind) are
    allowed to be lawful rather than accidental. In that reading it is an
    *emergence probability / complexity–energy occupancy* of the fluid map
    necessary for biological systems to arise as natural folds — not a Bayesian
    “P(Earth has life)” and not a lab culture success rate.

free_parameters = 0. Seeds never move.
"""

from __future__ import annotations

from typing import Any

from fsot_mc.fast import K, PHI, POOF, C_FACTOR
from fsot_mc.universe_atlas import evaluate_domain, get_domain


# Life corridor on the D_eff ladder (shallow quantum → intermediate bio → deep cosmos)
LIFE_CORRIDOR = (
    "Quantum_Mechanics",
    "Chemistry",
    "Physical_Chemistry",
    "Molecular_Chemistry",
    "Biology",
    "Biochemistry",
    "Neuroscience",
    "Ecology",
    "Cosmology",
)

BIO_CORE = ("Biology", "Biochemistry", "Ecology", "Neuroscience")
CHEM_PRECURSORS = ("Chemistry", "Physical_Chemistry", "Molecular_Chemistry")


def _safe_eval(name: str) -> dict[str, Any] | None:
    try:
        return evaluate_domain(name)
    except KeyError:
        return None


def life_corridor_panel() -> list[dict[str, Any]]:
    """Canonical (zero-noise) life-corridor fold panel with term structure."""
    rows: list[dict[str, Any]] = []
    for name in LIFE_CORRIDOR:
        e = _safe_eval(name)
        if not e:
            continue
        # Complexity proxy: structure-forming magnitude at this depth
        # |S| = vitality intensity; T1 = coherence/growth channel; intermediate D_eff preferred
        S = float(e["S"])
        T1 = float(e.get("T1") or 0.0)
        T2 = float(e.get("T2") or 0.0)
        T3 = float(e.get("T3") or 0.0)
        D = float(e.get("D_eff") or 1.0)
        # Intermediate-depth preference (bio corridor ~8–15): peak near D_eff=12 (φ-scaled)
        depth_weight = float(PHI / (1.0 + abs(D - 12.0) / PHI))
        complexity = abs(S) * depth_weight * (1.0 + abs(T1) * C_FACTOR)
        # Energy-like occupancy: K-scaled positive vitality (emergence energy density proxy)
        energy_proxy = max(0.0, S) * float(K) * (1.0 + max(0.0, T2) * POOF)
        rows.append(
            {
                "domain": name,
                "D_eff": int(D),
                "S": S,
                "T1": T1,
                "T2": T2,
                "T3": T3,
                "regime": e.get("regime"),
                "complexity_proxy": float(complexity),
                "energy_proxy": float(energy_proxy),
                "depth_weight": float(depth_weight),
                "role": (
                    "life_fold"
                    if name in BIO_CORE
                    else "chemical_precursor"
                    if name in CHEM_PRECURSORS
                    else "boundary_scale"
                ),
            }
        )
    rows.sort(key=lambda r: r["D_eff"])
    return rows


def map_emergence_from_mc(mc: dict[str, Any] | None) -> dict[str, Any]:
    """Extract multipath map emergence stats from an MC result."""
    if not mc:
        return {}
    ens = mc.get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}
    de = mc.get("domain_ensemble") or {}
    bio_path = de.get("Biology") or {}
    return {
        "map_emergence_mean": ef.get("mean"),
        "map_emergence_p10": ef.get("p10"),
        "map_emergence_p50": ef.get("p50"),
        "map_emergence_p90": ef.get("p90"),
        "n_paths": mc.get("n_paths"),
        "n_domains": mc.get("n_domains"),
        "biology_S_path_mean": bio_path.get("S_path_mean"),
        "biology_S_canonical": bio_path.get("S_canonical"),
        "biology_flip_rate": bio_path.get("flip_rate"),
        "biology_D_eff": bio_path.get("D_eff")
        if bio_path.get("D_eff") is not None
        else get_domain("Biology").get("D_eff"),
    }


def corridor_coemergence(panel: list[dict[str, Any]], mc: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Fraction of life-corridor folds in emergence, plus optional multipath path means.
    """
    if not panel:
        return {"canonical_corridor_emergence": None, "n": 0}

    de = (mc or {}).get("domain_ensemble") or {}
    emerge = 0
    total = 0
    path_emerge = 0
    path_total = 0
    for r in panel:
        total += 1
        if float(r["S"]) > 0:
            emerge += 1
        name = r["domain"]
        if name in de:
            path_total += 1
            s_path = float(de[name].get("S_path_mean", de[name].get("S_canonical", 0.0)))
            if s_path > 0:
                path_emerge += 1

    return {
        "canonical_corridor_emergence": emerge / max(total, 1),
        "n_corridor": total,
        "n_corridor_emergent": emerge,
        "path_corridor_emergence": (path_emerge / path_total) if path_total else None,
        "n_path_corridor": path_total or None,
    }


def analyze_biological_emergence(
    mc: dict[str, Any] | None = None,
    *,
    query: str = "",
) -> dict[str, Any]:
    """
    Full dual-frame analysis: operational map vitality + paradigm co-emergence window.
    """
    panel = life_corridor_panel()
    map_stats = map_emergence_from_mc(mc)
    corridor = corridor_coemergence(panel, mc)

    bio = next((r for r in panel if r["domain"] == "Biology"), None)
    chem = [r for r in panel if r["role"] == "chemical_precursor"]
    life = [r for r in panel if r["role"] == "life_fold"]

    # Complexity budget in life corridor (sum of complexity proxies on emergent life folds)
    life_complexity = sum(float(r["complexity_proxy"]) for r in life if float(r["S"]) > 0)
    chem_complexity = sum(float(r["complexity_proxy"]) for r in chem if float(r["S"]) > 0)
    life_energy = sum(float(r["energy_proxy"]) for r in life)
    total_energy = sum(float(r["energy_proxy"]) for r in panel)

    map_mean = map_stats.get("map_emergence_mean")
    if map_mean is None:
        # fallback: corridor-only canonical
        map_mean = corridor.get("canonical_corridor_emergence")

    # Paradigm hypothesis score: how tightly map occupancy sits in the natural ~2/3 band
    # Band centered near 2/3 (φ-related structure: 1 - 1/φ² ≈ 0.618 … soft target ~0.67)
    natural_band_lo, natural_band_hi = 0.55, 0.78
    in_natural_band = (
        map_mean is not None and natural_band_lo <= float(map_mean) <= natural_band_hi
    )

    # Bio fold is lawful if S>0 at intermediate D_eff with positive energy proxy
    bio_lawful = bool(bio and float(bio["S"]) > 0 and float(bio["energy_proxy"]) > 0)

    hypothesis = {
        "id": "BIO-EMERGENCE-MAP-WINDOW",
        "class": "paradigm_hypothesis",
        "title": "Map co-emergence window as natural biological emergence occupancy",
        "operational_definition": (
            "emergence_fraction = mean_over_paths( count(folds with S>0) / n_folds ). "
            "Computed, seed-only, free_parameters=0."
        ),
        "paradigm_reading": (
            "Under FSOT ToE, the multipath ~60–70% (often ~69%) map occupancy is the "
            "natural co-emergence window of the multi-scale fluid: the share of domain "
            "folds that sit in structure-forming regime under observer coupling. "
            "That window is hypothesized as the energy/complexity *occupancy* the map "
            "must sustain for intermediate-D_eff folds (chemistry→biology→ecology→mind) "
            "to emerge as lawful structure rather than contingent fluke. "
            "It is map-level emergence probability in the FSOT sense — not P(a planet has life)."
        ),
        "map_emergence_mean": map_mean,
        "natural_band": [natural_band_lo, natural_band_hi],
        "in_natural_band": in_natural_band,
        "biology_S": bio["S"] if bio else None,
        "biology_D_eff": bio["D_eff"] if bio else None,
        "biology_complexity_proxy": bio["complexity_proxy"] if bio else None,
        "biology_energy_proxy": bio["energy_proxy"] if bio else None,
        "life_corridor_complexity": float(life_complexity),
        "chem_precursor_complexity": float(chem_complexity),
        "life_energy_proxy_sum": float(life_energy),
        "corridor_energy_proxy_sum": float(total_energy),
        "bio_lawful_fold": bio_lawful,
        "corridor": corridor,
        "score": float(
            (0.5 if in_natural_band else 0.2)
            + (0.3 if bio_lawful else 0.0)
            + min(0.2, life_complexity * POOF)
        ),
        "epistemic_tier": "paradigm_hypothesis",
        "experiment_gate": (
            "Close by: (1) lab panels on FSOT-designed bio/chem observables already in archive; "
            "(2) whether intermediate D_eff life-corridor folds remain S>0 under controlled "
            "observer/phase perturbation; (3) whether map occupancy stays in the natural band "
            "when real chem/bio anchors are coupled. Kill if biology fold systematically "
            "disperses while map occupancy is forced high by unrelated domains alone."
        ),
        "free_parameters": 0,
    }

    return {
        "error": None,
        "method": "fsot_biological_emergence",
        "free_parameters": 0,
        "paradigm": "life_as_fluid_fold",
        "map_stats": map_stats,
        "life_corridor": panel,
        "corridor_coemergence": corridor,
        "hypothesis": hypothesis,
        "query": query or None,
        "note": (
            "Dual frame: operational map vitality + ToE co-emergence window for natural "
            "biological complexity. Experiment still closes paradigm claims."
        ),
    }


def format_bio_emergence_science(analysis: dict[str, Any]) -> str:
    """Prose block for mind answers — scientifically dense, paradigm-honest."""
    h = analysis.get("hypothesis") or {}
    panel = analysis.get("life_corridor") or []
    map_stats = analysis.get("map_stats") or {}
    corridor = analysis.get("corridor_coemergence") or {}

    def _pct(x: Any) -> str:
        if x is None:
            return "?"
        return f"{100.0 * float(x):.1f}%"

    parts = [
        "PARADIGM — biological emergence under FSOT ToE:",
        "Life is not an extra ontology. Biology is a fold of the same seed engine "
        f"at intermediate D_eff (Biology D_eff={h.get('biology_D_eff')}, "
        f"S={float(h['biology_S']):+.4f})." if h.get("biology_S") is not None else
        "Life is not an extra ontology; biology is a fluid fold at intermediate D_eff.",
        "OPERATIONAL metric: multipath emergence fraction = mean over paths of "
        f"(folds with S>0)/(n folds) → map occupancy {_pct(h.get('map_emergence_mean'))} "
        f"(p10–p90 {_pct(map_stats.get('map_emergence_p10'))}–{_pct(map_stats.get('map_emergence_p90'))}).",
        "PARADIGM reading of that ~60–70% (~69%) band: the *natural co-emergence window* — "
        "map-level emergence probability / complexity–energy occupancy the multi-scale fluid "
        "must sustain for chemical→biological→ecological→neural structure to arise as lawful "
        "folds rather than contingency. Natural band "
        f"[{_pct(h.get('natural_band', [None, None])[0] if h.get('natural_band') else None)}"
        f"–{_pct(h.get('natural_band', [None, None])[1] if h.get('natural_band') else None)}]; "
        f"in_band={h.get('in_natural_band')}.",
        "Not P(Earth has life) and not a culture-plate success rate — it is the share of the "
        "FSOT domain map in structure-forming regime under observer-coupled multipath thought.",
    ]

    # Corridor ladder
    if panel:
        bits = [
            f"{r['domain']}@D={r['D_eff']} S={float(r['S']):+.3f} "
            f"C={float(r['complexity_proxy']):.3f} E={float(r['energy_proxy']):.4f}"
            for r in panel
        ]
        parts.append(
            "Life corridor (D_eff ladder, complexity C, energy-proxy E): "
            + " → ".join(bits)
            + "."
        )

    if corridor.get("canonical_corridor_emergence") is not None:
        parts.append(
            f"Corridor co-emergence (canonical): {_pct(corridor['canonical_corridor_emergence'])} "
            f"({corridor.get('n_corridor_emergent')}/{corridor.get('n_corridor')} folds). "
            + (
                f"Path-mean corridor occupancy: {_pct(corridor['path_corridor_emergence'])}."
                if corridor.get("path_corridor_emergence") is not None
                else ""
            )
        )

    if h.get("biology_complexity_proxy") is not None:
        parts.append(
            f"Biology complexity_proxy={float(h['biology_complexity_proxy']):.4f}, "
            f"energy_proxy={float(h['biology_energy_proxy']):.4f}; "
            f"life-corridor complexity sum={float(h['life_corridor_complexity']):.4f}; "
            f"chem-precursor complexity sum={float(h['chem_precursor_complexity']):.4f}. "
            "These proxies are seed-derived (|S|·depth-weight·T1 channel; K·max(S,0)) — "
            "not free fit parameters — and stand as quantitative handles for the energy/"
            "complexity necessary for bio-fold emergence."
        )

    parts.append(
        f"Experiment gate: {h.get('experiment_gate')} "
        f"[epistemic_tier={h.get('epistemic_tier')}, score={float(h.get('score') or 0):.2f}]."
    )
    return " ".join(parts)
