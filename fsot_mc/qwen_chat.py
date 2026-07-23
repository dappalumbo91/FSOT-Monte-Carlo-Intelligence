"""
Qwen conversational interface grounded in FSOT documentation.

This is what the user actually wanted:
  - Read tissue theses + methodology + claims + audit + handoff
  - Retrieve relevant docs per message (RAG)
  - Multi-turn conversation with history
  - Optional live MC scalars when domains are mentioned
  - free_parameters=0 doctrine; no recognition peer-review

Uses local Qwen2.5-Instruct 7B safetensors via qwen_narrate.load_model.
"""

from __future__ import annotations

import re
import threading
from typing import Any

from fsot_mc.doc_rag import ensure_doc_index, format_hits_for_prompt, search_docs
from fsot_mc.qwen_narrate import load_model, model_ready

CHAT_SYSTEM = """You are the conversational guide for FSOT Monte Carlo Intelligence — the product and codebase of Fluid Spacetime Omni-Theory.

=== IDENTITY (never redefine) ===
- FSOT ALWAYS means Fluid Spacetime Omni-Theory (author: Damian Arthur Palumbo). Full name, every time it matters: Fluid Spacetime Omni-Theory.
- This repository (FSOT Monte Carlo Intelligence) IS that work: multipath Monte Carlo + connective tissue + docs under FSOT, free_parameters=0, authority pin D1D38A.
- When the user says "FSOT", "my work", "the theory", "this project", or "this repo", they mean Fluid Spacetime Omni-Theory and this codebase — not any other expansion of the letters F-S-O-T, not a generic "framework", not finance, not an unrelated acronym.
- Do NOT invent alternate expansions (e.g. "Finite State…", "Feature Selection…", "Federal…"). If unsure, say Fluid Spacetime Omni-Theory.

Ground every answer in the DOCUMENTS and LIVE_SCALARS for this turn. Conversational colleague tone — complete replies, not table dumps, not mid-document continuations.

=== HARD DOCTRINE (do not redefine) ===
1. free_parameters = 0. Authority pin D1D38A. Seeds π, e, φ, γ, Catalan never move.
2. Law form: S = K·(T1+T2+T3) under that pin. Domains are folds of one fluid spacetime, not separate fitted models.
3. S is VITALITY, not "importance", "relevance", or "criticality":
   - S > 0 → emergence (structure-forming regime)
   - S ≤ 0 → dispersal (damping regime; still lawful, still the same fluid)
   Never rank folds as "more important" because |S| is larger.
4. D_eff is effective dimensionality of the fold (scale/complexity address), not a vague "depth score" you invent.
5. TWO DIFFERENT METRICS — never conflate:
   - Green gate: archive empirical bar — domain median_error_pct ≤ 0.5% (MEASURED panel accuracy).
   - Multipath map co-emergence: mean over observer paths of (count of folds with S>0) / n_folds.
     Often lands ~0.55–0.78 (~60–70%). This is map occupancy / co-emergence window under multipath thought.
     It is NOT P(Earth has life), NOT a culture-plate rate, and NOT the green gate.
6. Claim tiers: MEASURED (pin, zero free params, green-gate numbers) vs PREREGISTERED PREDs (kill discriminants; lab closes) vs multipath STRUCTURE (discovery/observer stats). Soft court promote ≠ Lean-proved.
7. Prefer numbers from LIVE_SCALARS when present; cite document paths you used (e.g. docs/tissue/domains/Biology.md).
8. If docs/scalars lack something, say so — do not invent free parameters, new constants, or proofs.
9. Do NOT peer-review social recognition / mainstream status unless the user asks.
10. Answer the user's actual question. If they ask for the green-gate vs multipath split, you MUST state both and contrast them explicitly.
11. If they ask what FSOT is / stands for / what their work is: answer Fluid Spacetime Omni-Theory first, then this Monte Carlo intelligence product under that law.

You are connected to this workspace's documentation. Documents + live scalars are the source of truth for explanation."""

# Injected every turn so doctrine survives long RAG context
DOCTRINE_CARD = """DOCTRINE CARD (must obey):
- FSOT = Fluid Spacetime Omni-Theory (Damian Arthur Palumbo). This repo IS that work. No other acronym expansion.
- S = vitality: S>0 emergence, S≤0 dispersal; NOT importance.
- Green gate ≤0.5% median error ≠ multipath co-emergence fraction (~60–70% map occupancy).
- free_parameters=0, pin D1D38A; soft court ≠ proved.
"""

IDENTITY_BLOCK = (
    "=== PROJECT IDENTITY (fixed) ===\n"
    "FSOT = Fluid Spacetime Omni-Theory (author Damian Arthur Palumbo).\n"
    "Product in this workspace: FSOT Monte Carlo Intelligence — multipath universe "
    "simulation and discovery under that theory (not markets; free_parameters=0; pin D1D38A).\n"
    "User references to FSOT / my work / the theory / this project always mean the above.\n"
)

_SESSIONS: dict[str, list[dict[str, str]]] = {}
_SESSION_LOCK = threading.Lock()


def _extract_domain_hints(text: str) -> list[str]:
    try:
        from fsot_mc.universe_atlas import core_names

        cores = list(core_names())
    except Exception:
        cores = []
    found = []
    low = (text or "").lower()
    for d in cores:
        if d.lower().replace("_", " ") in low or d.lower() in low or d.replace("_", "").lower() in low.replace(" ", ""):
            found.append(d)
    # also Capital_Word patterns
    for m in re.findall(r"\b([A-Z][a-z]+(?:_[A-Z][a-z]+)+)\b", text or ""):
        if m not in found:
            found.append(m)
    return found[:6]


def _live_scalars(domains: list[str]) -> list[dict[str, Any]]:
    out = []
    try:
        from fsot_mc.universe_atlas import evaluate_domain

        for d in domains[:6]:
            try:
                ev = evaluate_domain(d)
                out.append(
                    {
                        "domain": d,
                        "S": float(ev["S"]),
                        "D_eff": ev.get("D_eff"),
                        "regime": ev.get("regime"),
                    }
                )
            except Exception:
                continue
    except Exception:
        pass
    return out


def _looks_like_identity_query(text: str) -> bool:
    low = (text or "").lower()
    keys = (
        "what is fsot",
        "what does fsot",
        "fsot stand",
        "stands for",
        "fluid spacetime",
        "my work",
        "my theory",
        "this project",
        "this repo",
        "this repository",
        "what is this",
        "omni-theory",
        "omni theory",
        "who is damian",
        "author",
    )
    if any(k in low for k in keys):
        return True
    # bare "fsot" with little else still benefits from identity docs
    if re.search(r"\bfsot\b", low) and len(low.split()) <= 12:
        return True
    return False


def build_chat_context(user_message: str, *, limit_docs: int = 8) -> dict[str, Any]:
    """Retrieve docs + live scalars for one user message."""
    ensure_doc_index()
    domains = _extract_domain_hints(user_message)
    prefer = []
    for d in domains:
        prefer.append(f"domains/{d}")
        prefer.append(d.lower())
    if _looks_like_identity_query(user_message):
        prefer.extend(
            [
                "METHODOLOGY",
                "REPRODUCIBILITY",
                "ACHIEVEMENTS",
                "CLAIMS",
                "Fluid Spacetime Omni-Theory",
            ]
        )
    retrieved = search_docs(user_message, limit=limit_docs, prefer_paths=prefer)
    # force-pull full primary domain theses when named
    hits = list(retrieved.get("hits") or [])
    for d in domains[:3]:
        path = f"docs/tissue/domains/{d}.md"
        if not any(h.get("path", "").endswith(f"{d}.md") for h in hits):
            extra = search_docs(d, limit=2, prefer_paths=[f"domains/{d}"])
            for h in extra.get("hits") or []:
                if h not in hits:
                    hits.insert(0, h)
    # identity questions: force methodology / achievements into the pack
    if _looks_like_identity_query(user_message):
        for q, pref in (
            ("Fluid Spacetime Omni-Theory free_parameters", ["METHODOLOGY"]),
            ("FSOT Monte Carlo Intelligence product paradigm", ["ACHIEVEMENTS", "METHODOLOGY"]),
        ):
            extra = search_docs(q, limit=2, prefer_paths=pref)
            for h in extra.get("hits") or []:
                if not any(x.get("path") == h.get("path") for x in hits):
                    hits.insert(0, h)
        # hard-inject first chunks of key product docs if still missing
        from pathlib import Path
        from fsot_mc.paths import PACKAGE_ROOT

        for rel in ("docs/METHODOLOGY.md", "docs/ACHIEVEMENTS.md"):
            if any((h.get("path") or "").replace("\\", "/").endswith(rel.split("/", 1)[-1]) for h in hits):
                continue
            p = PACKAGE_ROOT / rel
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[:2200]
            except OSError:
                continue
            hits.insert(
                0,
                {
                    "path": rel.replace("\\", "/"),
                    "title": p.stem,
                    "body": text,
                    "score": 1e6,
                },
            )
    hits = hits[:limit_docs]
    scalars = _live_scalars(domains)
    docs_text = format_hits_for_prompt(hits, max_total_chars=5500)
    scalar_lines = []
    for s in scalars:
        scalar_lines.append(
            f"- {s['domain']}: S={s['S']:+.4f}, D_eff={s.get('D_eff')}, regime={s.get('regime')}"
        )
    live = "\n".join(scalar_lines) if scalar_lines else "(no domain scalars extracted this turn)"

    block = (
        f"{IDENTITY_BLOCK}\n"
        "=== DOCUMENTS RETRIEVED FROM PROJECT (read these) ===\n"
        f"{docs_text}\n\n"
        "=== LIVE FSOT SCALARS (Fluid Spacetime Omni-Theory engine, free_parameters=0) ===\n"
        f"{live}\n"
        "=== END RETRIEVED MATERIAL ===\n"
    )
    return {
        "domains": domains,
        "hits": hits,
        "n_docs": len(hits),
        "live_scalars": scalars,
        "context_block": block,
        "free_parameters": 0,
    }


def get_history(session_id: str) -> list[dict[str, str]]:
    with _SESSION_LOCK:
        return list(_SESSIONS.get(session_id or "default", []))


def clear_history(session_id: str = "default") -> None:
    with _SESSION_LOCK:
        _SESSIONS.pop(session_id or "default", None)


def chat(
    message: str,
    *,
    session_id: str = "default",
    history: list[dict[str, str]] | None = None,
    max_new_tokens: int = 450,
    temperature: float = 0.45,
    max_history_turns: int = 8,
) -> dict[str, Any]:
    """
    One conversational turn grounded in documentation RAG + optional scalars.
    """
    message = (message or "").strip()
    if not message:
        return {"ok": False, "error": "empty_message", "free_parameters": 0}

    sid = session_id or "default"
    if history is None:
        history = get_history(sid)
    else:
        history = list(history)

    # Ensure model
    st = model_ready()
    if not st.get("ok"):
        return {
            "ok": False,
            "error": "model_not_downloaded",
            "hint": st.get("hint"),
            "free_parameters": 0,
        }
    lr = load_model()
    if not lr.get("ok"):
        return {
            "ok": False,
            "error": lr.get("error"),
            "detail": lr.get("detail"),
            "free_parameters": 0,
        }

    ctx = build_chat_context(message)
    # Build chat messages: system + prior turns + user with docs this turn
    messages: list[dict[str, str]] = [{"role": "system", "content": CHAT_SYSTEM}]
    # keep last N turns (user/assistant pairs)
    trimmed = history[-(max_history_turns * 2) :]
    for turn in trimmed:
        role = turn.get("role")
        content = (turn.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content[:2000]})

    user_payload = (
        f"{DOCTRINE_CARD}\n"
        f"{ctx['context_block']}\n\n"
        f"USER MESSAGE:\n{message}\n\n"
        "Reply as a complete conversational answer. Use DOCUMENTS + LIVE_SCALARS. "
        "FSOT always expands to Fluid Spacetime Omni-Theory; this project is that work. "
        "Define S only as vitality (emergence/dispersal). "
        "If the question touches multipath or green gate, keep those two metrics distinct. "
        "Do not continue a document mid-stream. Do not invent free parameters."
    )
    messages.append({"role": "user", "content": user_payload})

    from fsot_mc import qwen_narrate as qn

    import torch

    tok = qn._tokenizer
    model = qn._model
    try:
        prompt = tok.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        prompt = CHAT_SYSTEM + "\n\n" + user_payload + "\n\nAssistant:"

    max_input = int(__import__("os").environ.get("FSOT_MC_QWEN_MAX_INPUT", "2800"))
    inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=max_input)
    try:
        dev = next(model.parameters()).device
    except Exception:
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = {k: v.to(dev) for k, v in inputs.items()}

    gen_kwargs: dict[str, Any] = {
        "max_new_tokens": min(int(max_new_tokens), 512),
        "do_sample": temperature > 0.05,
        "pad_token_id": tok.eos_token_id,
        "use_cache": True,
    }
    if gen_kwargs["do_sample"]:
        gen_kwargs["temperature"] = float(temperature)
        gen_kwargs["top_p"] = 0.9

    try:
        with torch.inference_mode():
            out = model.generate(**inputs, **gen_kwargs)
    except torch.cuda.OutOfMemoryError:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {
            "ok": False,
            "error": "cuda_oom",
            "detail": "Lower FSOT_MC_QWEN_MAX_INPUT or free VRAM",
            "docs_used": [h.get("path") for h in ctx["hits"]],
            "free_parameters": 0,
        }

    in_len = inputs["input_ids"].shape[-1]
    text = tok.decode(out[0][in_len:], skip_special_tokens=True).strip()
    text = _clean_reply(text)

    # update session
    with _SESSION_LOCK:
        hist = _SESSIONS.setdefault(sid, [])
        hist.append({"role": "user", "content": message})
        hist.append({"role": "assistant", "content": text})
        # cap session
        if len(hist) > 40:
            _SESSIONS[sid] = hist[-40:]

    # Optional online articulation learning (gated LoRA queue; never trains seeds)
    learn_info: dict[str, Any] | None = None
    try:
        from fsot_mc.articulation_learn import harvest_from_chat_turn

        g = grade_reply(text, expect={})
        learn_info = harvest_from_chat_turn(
            message,
            text,
            docs_used=[{"path": h.get("path")} for h in ctx["hits"]],
            live_scalars=ctx["live_scalars"],
            grade=g,
        )
    except Exception as exc_learn:
        learn_info = {"ok": False, "error": "learn_hook_failed", "detail": str(exc_learn)}

    return {
        "ok": True,
        "method": "fsot_qwen_doc_chat",
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "free_parameters": 0,
        "authority": "D1D38A",
        "session_id": sid,
        "message": message,
        "reply": text,
        "answer": text,  # UI compatibility
        "docs_used": [{"path": h.get("path"), "title": h.get("title")} for h in ctx["hits"]],
        "n_docs": ctx["n_docs"],
        "domains": ctx["domains"],
        "live_scalars": ctx["live_scalars"],
        "qwen": {"used": True, "ready": True, "ok": True},
        "articulation_learn": learn_info,
        "note": "Conversation grounded in project documentation RAG + live fold scalars.",
    }


def _clean_reply(text: str) -> str:
    t = (text or "").strip()
    # drop accidental continuation markers
    bad_starts = (
        "---",
        "| ",
        "[DOC",
        "END RETRIEVED",
        "=== END",
        "USER MESSAGE",
        "DOCTRINE CARD",
    )
    for b in bad_starts:
        if t.startswith(b):
            # try find first paragraph that looks like prose
            parts = re.split(r"\n\s*\n", t)
            for p in parts:
                p = p.strip()
                if len(p) > 40 and not p.startswith(bad_starts) and not p.startswith("|"):
                    return p
    # strip trailing meta
    if "USER MESSAGE:" in t:
        t = t.split("USER MESSAGE:")[0].strip()
    # strip leading punctuation/number garbage from truncated context
    t = re.sub(r"^[\d\.\,\|\-\s]+", "", t).strip()
    return t


def grade_reply(reply: str, *, expect: dict[str, Any] | None = None) -> dict[str, Any]:
    """Lightweight automatic checks that the reply tracks doctrine / numbers."""
    r = (reply or "").lower()
    expect = expect or {}
    checks = {}
    # Identity: Fluid Spacetime Omni-Theory when asked what FSOT is
    if expect.get("need_fsot_identity"):
        checks["names_fluid_spacetime_omni"] = (
            "fluid spacetime" in r
            or "fluid space-time" in r
            or ("omni-theory" in r or "omni theory" in r)
            or "fluid spacetime omni" in r.replace("-", " ")
        )
        # reject common wrong expansions the base model might invent
        bad = (
            "finite state",
            "feature selection",
            "federal support",
            "forward stock",
            "file system object",
            "full spectrum of training",
        )
        checks["avoids_wrong_fsot_acronym"] = not any(x in r for x in bad)
    # S not importance
    checks["avoids_importance_gloss"] = not any(
        x in r for x in ("importance of the fold", "most critical fold", "relevance of the fold", "not the most critical")
    )
    # vitality / emergence language
    checks["mentions_emergence_or_vitality"] = any(
        x in r for x in ("emergence", "vitality", "dispersal", "s>0", "s > 0", "s≤", "s <")
    )
    if expect.get("need_green_gate_split"):
        checks["mentions_green_gate"] = "0.5" in r or "green gate" in r or "green-gate" in r
        checks["mentions_multipath_or_occupancy"] = any(
            x in r for x in ("multipath", "co-emergence", "coemergence", "occupancy", "map")
        )
        checks["split_both"] = checks["mentions_green_gate"] and checks["mentions_multipath_or_occupancy"]
    if expect.get("s_value") is not None:
        s = float(expect["s_value"])
        # accept a few formats
        frag = f"{abs(s):.3f}"
        checks["has_s_number"] = frag[:5] in r.replace(" ", "") or f"{s:.2f}" in r or f"{s:+.2f}".lower() in r
    if expect.get("domain"):
        checks["mentions_domain"] = expect["domain"].lower().replace("_", " ") in r or expect["domain"].lower() in r
    score = sum(1 for v in checks.values() if v) / max(len(checks), 1)
    return {"checks": checks, "score": round(score, 3), "n_checks": len(checks)}
