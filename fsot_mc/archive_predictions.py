"""
Load FSOT preregistered predictions / engineering panels from the local archive bundle.

These are *not* free invention: they are seed-scalar designs with stated discriminants
and kill criteria from the Physical Archive. Multipath MC uses them as discovery
targets and science-grade answer context — experiment still required to close the loop.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from fsot_mc.paths import archive_bundle_dir


def _manifest_path() -> Path:
    return archive_bundle_dir() / "data__preregistered_predictions_manifest.yaml"


def _parse_simple_yaml_list(text: str) -> list[dict[str, Any]]:
    """
    Minimal parser for the preregistered predictions YAML (list of maps).
    Avoids a PyYAML dependency; handles the archive's indentation style.
    """
    items: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    multiline_key: str | None = None
    multiline_buf: list[str] = []

    def _flush_ml() -> None:
        nonlocal multiline_key, multiline_buf, cur
        if cur is not None and multiline_key is not None:
            cur[multiline_key] = " ".join(multiline_buf).strip().strip("'\"")
        multiline_key = None
        multiline_buf = []

    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # New list item
        m_item = re.match(r"^- id:\s*(.+)\s*$", line.strip())
        if m_item or re.match(r"^- id:", line):
            _flush_ml()
            if cur:
                items.append(cur)
            # handle both "- id: PRED-001" forms
            id_m = re.search(r"id:\s*(\S+)", line)
            cur = {"id": id_m.group(1) if id_m else "UNKNOWN"}
            continue
        if line.startswith("predictions:") or line.startswith("version:") or line.startswith("notes:") or line.startswith("registered_at:"):
            # top-level keys before list — skip unless mid multi-line notes (we only care about predictions)
            continue
        if cur is None:
            continue
        if multiline_key is not None:
            # continuation of folded note
            if re.match(r"^\s{2}\w", line) and ":" in line and not line.strip().startswith("'"):
                _flush_ml()
            else:
                multiline_buf.append(line.strip().strip("'"))
                continue
        # key: value under item (2-space indent typical)
        m = re.match(r"^\s{2}([a-zA-Z0-9_]+):\s*(.*)$", line)
        if not m:
            # more indented continuation of previous string
            if cur and line.strip():
                last_k = list(cur.keys())[-1] if cur else None
                if last_k and last_k != "id" and isinstance(cur.get(last_k), str):
                    cur[last_k] = (cur[last_k] + " " + line.strip().strip("'\"")).strip()
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", ">", ">-", "|-") or (val.startswith("'") and not val.endswith("'") and len(val) > 1):
            multiline_key = key
            multiline_buf = [val.lstrip("|'>\"").strip()]
            continue
        if val.startswith("'") and val.endswith("'") and len(val) >= 2:
            val = val[1:-1]
        elif val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1]
        # numeric?
        if re.fullmatch(r"-?\d+\.\d+e[+-]?\d+", val, re.I) or re.fullmatch(r"-?\d+\.\d+", val) or re.fullmatch(r"-?\d+", val):
            try:
                num: Any = float(val) if ("." in val or "e" in val.lower()) else int(val)
                cur[key] = num
                continue
            except ValueError:
                pass
        cur[key] = val

    _flush_ml()
    if cur:
        items.append(cur)
    return items


@lru_cache(maxsize=1)
def load_preregistered_predictions() -> list[dict[str, Any]]:
    path = _manifest_path()
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    # Strip document header until predictions list
    if "predictions:" in text:
        text = text[text.index("predictions:") :]
    return _parse_simple_yaml_list(text)


def predictions_summary() -> dict[str, Any]:
    preds = load_preregistered_predictions()
    domains = sorted({str(p.get("domain") or "") for p in preds if p.get("domain")})
    fuelish = [
        p
        for p in preds
        if any(
            k in (str(p.get("name") or "") + " " + str(p.get("domain") or "") + " " + str(p.get("note") or "")).lower()
            for k in ("fuel", "thermo", "hydrogen", "biodiesel", "engine")
        )
    ]
    return {
        "n_predictions": len(preds),
        "n_domains": len(domains),
        "domains": domains[:40],
        "n_engineering_fuel_related": len(fuelish),
        "source": str(_manifest_path().name),
        "free_parameters": 0,
    }


def match_predictions(
    query: str,
    *,
    limit: int = 8,
    domain_hints: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Rank preregistered predictions against a natural-language query + optional domain list.
    """
    q = (query or "").lower()
    preds = load_preregistered_predictions()
    if not preds:
        return []

    # Cue bags
    fuel_cues = ("fuel", "thermo", "hydrogen", "biodiesel", "hemp", "algae", "mushroom", "engine", "energy source")
    cosmo_cues = ("hubble", "h0", "cosmology", "s8", "dark", "lithium", "planck")
    particle_cues = ("muon", "particle", "g-2", "g2", "ckm", "pmns")
    transport_cues = ("transport", "portal", "warp", "beam", "pattern buffer")
    quantum_cues = ("quantum", "entangle", "observer")
    bio_cues = ("bio", "life", "genome", "codon", "cell")

    scored: list[tuple[float, dict[str, Any]]] = []
    for p in preds:
        blob = " ".join(
            str(p.get(k) or "")
            for k in ("id", "name", "domain", "note", "unit", "sota_label", "fsot_formula_branch")
        ).lower()
        score = 0.0
        # domain overlap
        dom = str(p.get("domain") or "")
        if domain_hints:
            for h in domain_hints:
                if h.lower() in dom.lower() or h.lower().replace("_", " ") in blob:
                    score += 1.5
        # query token hits
        for tok in re.findall(r"[a-z0-9+]{3,}", q):
            if tok in blob:
                score += 0.8
        if any(c in q for c in fuel_cues) and any(c in blob for c in fuel_cues):
            score += 3.0
        if any(c in q for c in cosmo_cues) and any(c in blob for c in cosmo_cues):
            score += 2.5
        if any(c in q for c in particle_cues) and any(c in blob for c in particle_cues):
            score += 2.0
        if any(c in q for c in transport_cues) and any(c in blob for c in transport_cues):
            score += 2.5
        if any(c in q for c in quantum_cues) and any(c in blob for c in quantum_cues):
            score += 1.2
        if any(c in q for c in bio_cues) and any(c in blob for c in bio_cues):
            score += 1.5
        # always give engineering panels a floor when query is engineering-ish
        if "engineering" in q or "prediction" in q or "experiment" in q:
            score += 0.4
        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    out = []
    for score, p in scored[:limit]:
        out.append(
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "domain": p.get("domain"),
                "fsot_predicted": p.get("fsot_predicted"),
                "unit": p.get("unit"),
                "sota_baseline": p.get("sota_baseline"),
                "sota_label": p.get("sota_label"),
                "discriminant": p.get("discriminant"),
                "formula_branch": p.get("fsot_formula_branch"),
                "note": (str(p.get("note") or ""))[:400],
                "match_score": float(score),
                "class": "preregistered_prediction",
                "epistemic_tier": "preregistered_design",
                "hypothesis": (
                    f"Archive prediction {p.get('id')} ({p.get('name')}): "
                    f"FSOT value {p.get('fsot_predicted')} {p.get('unit') or ''} "
                    f"vs SOTA {p.get('sota_baseline')} ({p.get('sota_label')}); "
                    f"discriminant={p.get('discriminant')}."
                ),
                "score": float(min(1.0, score / 6.0)),
            }
        )
    return out


def engineering_leads_for_mc(
    mc: dict[str, Any] | None = None,
    *,
    query: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Surface engineering / fuel / technology predictions as discovery ledger entries.
    Optionally bias by domains present in an MC run.
    """
    domain_hints: list[str] = []
    if mc:
        de = mc.get("domain_ensemble") or {}
        domain_hints = list(de.keys())[:20]
    q = query or "fuel energy engineering prediction thermochemistry hydrogen"
    leads = match_predictions(q, limit=limit, domain_hints=domain_hints)
    # Always include the flagship fuel panel if not already present
    fuel = match_predictions("fsot designed fuel thermochemistry hemp algae hydrogen", limit=3)
    seen = {x.get("id") for x in leads}
    for f in fuel:
        if f.get("id") not in seen:
            leads.append(f)
            seen.add(f.get("id"))
    leads.sort(key=lambda x: -float(x.get("match_score") or x.get("score") or 0))
    return leads[:limit]
