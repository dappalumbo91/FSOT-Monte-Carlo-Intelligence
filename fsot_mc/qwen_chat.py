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

CHAT_SYSTEM = """You are the conversational guide for the FSOT Monte Carlo Intelligence workspace.

Your job: have a clear, helpful conversation about THIS project's documentation and results.
You MUST ground answers in the DOCUMENTS provided in each turn (tissue theses, methodology, claims, etc.).

Rules:
1. free_parameters = 0. Authority pin D1D38A. Seeds π,e,φ,γ,Catalan never move.
2. Prefer facts from DOCUMENTS and LIVE_SCALARS. Quote paths when you use a thesis (e.g. docs/tissue/domains/Biology.md).
3. If docs do not cover something, say so honestly — do not invent FSOT formulas, free parameters, or proofs.
4. Multipath / discovery metrics are not the ≤0.5% green-gate empirical bar. Soft court ≠ Lean-proved.
5. Do NOT peer-review social recognition or "is this mainstream?" unless the user asks.
6. Write like a knowledgeable colleague: conversational paragraphs, not dump of tables.
7. When the user greets you or asks how you work, explain that you read the project docs (tissue theses, claims, methodology) and can discuss any fold or report in the pack.
8. Never continue a document mid-sentence. Always answer the latest user message as a complete reply.

You are connected to the work. The documents ARE the source of truth for explanation."""

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


def build_chat_context(user_message: str, *, limit_docs: int = 8) -> dict[str, Any]:
    """Retrieve docs + live scalars for one user message."""
    ensure_doc_index()
    domains = _extract_domain_hints(user_message)
    prefer = []
    for d in domains:
        prefer.append(f"domains/{d}")
        prefer.append(d.lower())
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
        "=== DOCUMENTS RETRIEVED FROM PROJECT (read these) ===\n"
        f"{docs_text}\n\n"
        "=== LIVE FSOT SCALARS (engine, free_parameters=0) ===\n"
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
        f"{ctx['context_block']}\n\n"
        f"USER MESSAGE:\n{message}\n\n"
        "Reply as a complete conversational answer. Use the documents above. "
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
    return t
