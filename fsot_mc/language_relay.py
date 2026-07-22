"""
PFLT language relay — turn discovery leads into Protofluid / plain FSOT language.

Independent: uses vendored vendor/pflt when available; otherwise built-in FSOT prose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fsot_mc.paths import linguistics_dir, pflt_vendor_dir
from fsot_mc.pflt_bridge import _try_import_pflt_core


def _load_linguistics_snippets(limit: int = 12) -> list[dict[str, Any]]:
    p = linguistics_dir() / "linguistics_derivations.json"
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    # flexible shapes
    items = []
    if isinstance(raw, list):
        items = raw[:limit]
    elif isinstance(raw, dict):
        for k, v in list(raw.items())[:limit]:
            if isinstance(v, dict):
                items.append({"id": k, **v})
            else:
                items.append({"id": k, "value": v})
    return items


def _builtin_relay_lead(lead: dict[str, Any]) -> str:
    """Seed-vocabulary English relay without external PFLT."""
    cls = lead.get("class") or "lead"
    lid = lead.get("id") or "UNKNOWN"
    title = lead.get("title") or lead.get("domain") or lid
    score = lead.get("score")
    hyp = lead.get("hypothesis") or lead.get("note") or ""
    tier = lead.get("epistemic_tier") or "scaffold"
    score_s = f"{float(score):.3f}" if score is not None else "?"
    lines = [
        f"[FSOT relay · {cls} · tier={tier} · score={score_s}]",
        f"Lead {lid}: {title}.",
    ]
    if hyp:
        lines.append(str(hyp)[:400])
    if lead.get("domain"):
        lines.append(f"Domain fold: {lead['domain']}.")
    if "S_path_mean" in lead or "S_canonical" in lead:
        lines.append(
            f"Scalar context: path_mean={lead.get('S_path_mean')} "
            f"canonical={lead.get('S_canonical')}."
        )
    lines.append(
        "Law: S = K·(T1+T2+T3) from seeds (π, e, φ, γ, Catalan); free_parameters=0."
    )
    return " ".join(lines)


def _pflt_surface_phrase(text: str) -> dict[str, Any] | None:
    """Optional classical/protofluid surface via vendored PFLT core."""
    mod = _try_import_pflt_core()
    if mod is None:
        return None
    try:
        pflt = mod.PFLT()
        # historical / scientific context
        out = pflt.translate(text[:200], context="scientific")
        if isinstance(out, dict):
            return {
                "ok": True,
                "meanings": out.get("meanings"),
                "S": out.get("fsot_coherence_S") or out.get("S"),
                "domain": out.get("domain"),
                "pipeline": out.get("pipeline"),
            }
        return {"ok": True, "raw": str(out)[:500]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def relay_lead(lead: dict[str, Any], *, use_pflt_surface: bool = True) -> dict[str, Any]:
    prose = _builtin_relay_lead(lead)
    surface = None
    if use_pflt_surface:
        # feed a short English phrase for surface demo
        seed = str(lead.get("title") or lead.get("domain") or lead.get("id") or "fluid cosmos")
        surface = _pflt_surface_phrase(seed)
    return {
        "id": lead.get("id"),
        "class": lead.get("class"),
        "score": lead.get("score"),
        "epistemic_tier": lead.get("epistemic_tier"),
        "relay_text": prose,
        "pflt_surface": surface,
        "free_parameters": 0,
    }


def relay_discovery(
    discovery_or_intel: dict[str, Any],
    *,
    top_n: int = 10,
    use_pflt_surface: bool = True,
) -> dict[str, Any]:
    """Relay top discovery ledger into language."""
    disc = discovery_or_intel.get("discovery") or discovery_or_intel
    leads = disc.get("top_ledger") or []
    relays = [relay_lead(L, use_pflt_surface=use_pflt_surface) for L in leads[:top_n]]
    ling = _load_linguistics_snippets(8)
    return {
        "method": "fsot_pflt_language_relay",
        "free_parameters": 0,
        "n_relayed": len(relays),
        "relays": relays,
        "linguistics_snippets": ling,
        "pflt_vendor": str(pflt_vendor_dir()),
        "pflt_core_available": _try_import_pflt_core() is not None,
        "note": (
            "Builtin FSOT prose always; optional PFLT surface from vendor/pflt. "
            "Independent of Desktop/I: paths."
        ),
    }


def relay_universe_state(canonical: dict[str, Any], ensemble: dict[str, Any] | None = None) -> str:
    """One-paragraph state of the universe snapshot."""
    ef = canonical.get("emergence_fraction")
    ms = canonical.get("mean_S")
    n = canonical.get("n_domains")
    parts = [
        f"FSOT universe map: {n} domain folds evaluated.",
        f"Emergence fraction {ef:.3f}; mean vitality S={ms:+.4f}." if ef is not None and ms is not None else "",
    ]
    if ensemble and isinstance(ensemble.get("emergence_fraction"), dict):
        em = ensemble["emergence_fraction"]
        parts.append(
            f"Multipath ensemble emergence mean={em.get('mean'):.3f} "
            f"(p10={em.get('p10'):.3f}, p90={em.get('p90'):.3f})."
        )
    parts.append("As Above So Below: one fluid, many folds; observation couples via quirk_mod.")
    return " ".join(p for p in parts if p)
