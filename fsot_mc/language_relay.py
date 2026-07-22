"""
PFLT language relay — simulation-grounded language for leads and mind answers.

Independent: vendor/pflt when present; builtin FSOT prose always.
"""

from __future__ import annotations

import json
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
    items: list[dict[str, Any]] = []
    if isinstance(raw, list):
        items = raw[:limit]
    elif isinstance(raw, dict):
        for k, v in list(raw.items())[:limit]:
            if isinstance(v, dict):
                items.append({"id": k, **v})
            else:
                items.append({"id": k, "value": v})
    return items


def densify_prose(text: str, *, max_extra: int = 2) -> str:
    """
    Light densify: attach short FSOT-law clauses + optional linguistics anchor.
    Does not invent free parameters.
    """
    extra = [
        "Vitality sign(S)>0 tends to emergence; sign(S)<0 to dispersal.",
        "Observation couples through quirk_mod and consciousness factor C.",
    ]
    bits = [text]
    for i, e in enumerate(extra[:max_extra]):
        if e.lower() not in text.lower():
            bits.append(e)
    return " ".join(bits)


def _builtin_relay_lead(lead: dict[str, Any]) -> str:
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
    return densify_prose(" ".join(lines))


def _pflt_surface_phrase(text: str) -> dict[str, Any] | None:
    mod = _try_import_pflt_core()
    if mod is None:
        return None
    try:
        pflt = mod.PFLT()
        out = pflt.translate(text[:200], context="scientific")
        if isinstance(out, dict):
            meanings = out.get("meanings")
            # densify: drop pure unresolved spam
            if isinstance(meanings, list):
                clean = [m for m in meanings if m and str(m).lower() != "unresolved"]
                meanings = clean if clean else meanings[:3]
            return {
                "ok": True,
                "meanings": meanings,
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
            "Builtin densified FSOT prose + optional PFLT surface from vendor/pflt."
        ),
    }


def relay_universe_state(canonical: dict[str, Any], ensemble: dict[str, Any] | None = None) -> str:
    ef = canonical.get("emergence_fraction")
    ms = canonical.get("mean_S")
    n = canonical.get("n_domains")
    parts = [
        f"FSOT universe map: {n} domain folds evaluated." if n else "FSOT universe map active.",
    ]
    if ef is not None and ms is not None:
        parts.append(f"Emergence fraction {ef:.3f}; mean vitality S={ms:+.4f}.")
    if ensemble and isinstance(ensemble.get("emergence_fraction"), dict):
        em = ensemble["emergence_fraction"]
        parts.append(
            f"Multipath ensemble emergence mean={em.get('mean'):.3f} "
            f"(p10={em.get('p10'):.3f}, p90={em.get('p90'):.3f})."
        )
    parts.append("As Above So Below: one fluid, many folds; observation couples via quirk_mod.")
    return densify_prose(" ".join(p for p in parts if p))


def relay_mind_answer(answer: str, thinking: dict[str, Any] | None = None) -> str:
    """Densify a mind answer with optional thinking summary line."""
    if not thinking:
        return densify_prose(answer)
    n = thinking.get("n_paths")
    domains = thinking.get("routed_domains") or []
    prefix = ""
    if n:
        prefix = f"(Thought through {n} Monte Carlo paths"
        if domains:
            prefix += f" on {', '.join(domains[:5])}"
        prefix += ".) "
    return densify_prose(prefix + answer)
