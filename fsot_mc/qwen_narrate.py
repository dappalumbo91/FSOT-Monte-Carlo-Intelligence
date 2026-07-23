"""
Qwen2.5-Instruct 7B narration layer — articulate mouth over FSOT MC cortex.

Doctrine:
  - free_parameters = 0; pin D1D38A
  - Model only rewrites PROVIDED context (mind answer + tissue theses + MC scalars)
  - Does not invent law, free parameters, or claim Lean-proved status
  - Recognition/consensus peer-review is out of scope unless user asks

Weights: Hugging Face safetensors under vendor/models/Qwen2.5-7B-Instruct
  python scripts/download_qwen25_instruct.py
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fsot_mc.paths import PACKAGE_ROOT

DEFAULT_HF_ID = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_LOCAL = PACKAGE_ROOT / "vendor" / "models" / "Qwen2.5-7B-Instruct"

SYSTEM_PROMPT = """You are the articulation layer for FSOT Monte Carlo Intelligence.
You explain PROVIDED scientific context only. You are not a peer reviewer of social recognition.

HARD RULES:
1. free_parameters = 0. Authority pin D1D38A. Seeds (π,e,φ,γ,Catalan) never move.
2. Use ONLY facts, numbers, and claims present in CONTEXT. Do not invent constants, free parameters, or proofs.
3. Respect claim tiers in context (MEASURED / PREREG / STRUCTURE / multipath discovery). Never promote multipath-only or soft-court items to Lean-proved.
4. Green gate ≤0.5% is the empirical bar where stated; multipath emergence % is co-emergence/map occupancy, not that gate.
5. Do not discuss whether FSOT is "recognized" or mainstream unless the user explicitly asks.
6. Write clear technical English: structured, explanatory, suitable for scientists/engineers.
7. If CONTEXT is silent on a point, say the pack does not contain that information.

Output: a coherent explanation answering the user question, grounded in CONTEXT."""


def model_dir() -> Path:
    env = os.environ.get("FSOT_MC_QWEN_PATH") or os.environ.get("FSOT_MC_NARRATE_MODEL_PATH")
    if env:
        return Path(env)
    return DEFAULT_LOCAL


def model_ready(path: Path | None = None) -> dict[str, Any]:
    p = path or model_dir()
    cfg = p / "config.json"
    # any safetensors shard
    st = list(p.glob("*.safetensors")) + list(p.glob("model*.safetensors"))
    tok = p / "tokenizer.json"
    return {
        "ok": cfg.is_file() and len(st) > 0,
        "path": str(p),
        "has_config": cfg.is_file(),
        "has_tokenizer": tok.is_file() or (p / "tokenizer_config.json").is_file(),
        "n_safetensors": len(st),
        "hf_id": DEFAULT_HF_ID,
        "free_parameters": 0,
        "hint": (
            "python scripts/download_qwen25_instruct.py"
            if not (cfg.is_file() and st)
            else "ready"
        ),
    }


def _truncate(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n…[truncated]"


def build_narration_pack(
    *,
    query: str,
    mind: dict[str, Any] | None = None,
    node_id: str | None = None,
    domains: list[str] | None = None,
    max_thesis_chars: int = 2200,
    max_theses: int = 2,
    max_mind_chars: int = 2800,
    n_paths: int = 48,
    chew: bool = False,
) -> dict[str, Any]:
    """
    Assemble grounded CONTEXT for Qwen from mind + tissue theses.
    Always runs offline; no model load required.
    """
    from fsot_mc.mind import ask as mind_ask
    from fsot_mc.tissue_docs import get_tissue_doc
    from fsot_mc.universe_atlas import core_names, evaluate_domain

    query = (query or "").strip()
    mind_out = mind
    if mind_out is None and query:
        mind_out = mind_ask(
            query,
            n_paths=min(n_paths, 64),
            with_chew=chew,
            force_new_mc=False,
        )

    thinking = (mind_out or {}).get("thinking") or {}
    routed = list(domains or thinking.get("routed_domains") or [])
    if node_id:
        # map node id to domain slug
        dom = node_id
        if dom.startswith("dom_"):
            dom = dom[4:]
        if dom not in routed:
            routed = [dom, *routed]

    # Focus scalars
    focus = thinking.get("focus_scalars") or []
    if not focus and routed:
        for d in routed[:8]:
            try:
                ev = evaluate_domain(d)
                focus.append(
                    {
                        "domain": d,
                        "S": ev.get("S"),
                        "D_eff": ev.get("D_eff"),
                        "regime": ev.get("regime"),
                    }
                )
            except Exception:
                pass

    theses: list[dict[str, Any]] = []
    # Prefer explicit node, then routed domains
    ids_try: list[str] = []
    if node_id:
        ids_try.append(node_id)
        if not node_id.startswith("dom_"):
            ids_try.append(f"dom_{node_id}")
    for d in routed[:max_theses]:
        ids_try.append(f"dom_{d}")
        ids_try.append(d)

    seen: set[str] = set()
    for nid in ids_try:
        if nid in seen or len(theses) >= max_theses:
            continue
        seen.add(nid)
        try:
            doc = get_tissue_doc(nid)
        except Exception:
            continue
        if not doc.get("ok") and not doc.get("markdown") and not doc.get("path"):
            # try domain file directly
            md_path = PACKAGE_ROOT / "docs" / "tissue" / "domains" / f"{nid.replace('dom_', '')}.md"
            if not md_path.is_file():
                continue
            md = md_path.read_text(encoding="utf-8", errors="replace")
            theses.append(
                {
                    "id": nid,
                    "path": str(md_path),
                    "markdown": _truncate(md, max_thesis_chars),
                }
            )
            continue
        if not doc.get("ok"):
            continue
        md = doc.get("markdown") or ""
        if not md and doc.get("path"):
            try:
                p = Path(doc["path"])
                if not p.is_file():
                    p = PACKAGE_ROOT / doc["path"]
                md = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                md = ""
        if not md:
            continue
        theses.append(
            {
                "id": doc.get("id") or nid,
                "path": doc.get("path"),
                "markdown": _truncate(md, max_thesis_chars),
            }
        )

    ens = thinking.get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}

    mind_answer = _truncate(str((mind_out or {}).get("answer") or ""), max_mind_chars)
    pack = {
        "method": "fsot_narration_pack",
        "free_parameters": 0,
        "authority": "D1D38A",
        "query": query,
        "node_id": node_id,
        "routed_domains": routed[:12],
        "mind_answer": mind_answer,
        "mind_answer_full_available": bool((mind_out or {}).get("answer")),
        "focus_scalars": focus[:8],
        "emergence_fraction_mean": ef.get("mean"),
        "emergence_definition": thinking.get("emergence_fraction_definition"),
        "claim_hygiene": (
            "Multipath/discovery is not green-gate. Soft court promote ≠ Lean-proved. "
            "Literature is observation."
        ),
        "tissue_theses": theses,
        "n_theses": len(theses),
        "model_target": DEFAULT_HF_ID,
    }
    pack["context_text"] = _format_context_text(pack)
    # hard cap entire pack text for consumer GPUs (~12 GB)
    pack["context_text"] = _truncate(pack["context_text"], 12_000)
    return pack


def _format_context_text(pack: dict[str, Any]) -> str:
    """
    Compact, prose-first pack. Prefer mind answer + scalar table over raw
    full theses (which blow the 2k token window mid-table and confuse generation).
    """
    lines = [
        "=== FSOT NARRATION CONTEXT (authoritative) ===",
        "authority=D1D38A free_parameters=0",
        f"USER_QUERY: {pack.get('query')}",
        f"routed_domains: {', '.join(pack.get('routed_domains') or [])}",
        f"map_emergence_fraction_mean: {pack.get('emergence_fraction_mean')}",
        f"emergence_definition: {_truncate(str(pack.get('emergence_definition') or ''), 400)}",
        f"claim_hygiene: {pack.get('claim_hygiene')}",
        "",
        "--- FOCUS SCALARS (use these numbers; do not invent) ---",
    ]
    for row in pack.get("focus_scalars") or []:
        if isinstance(row, dict):
            try:
                s = float(row.get("S"))
                s_txt = f"{s:+.4f}"
            except Exception:
                s_txt = str(row.get("S"))
            lines.append(
                f"* {row.get('domain')}: S={s_txt} D_eff={row.get('D_eff')} "
                f"regime={row.get('regime')}"
            )
    lines.append("")
    lines.append("--- MONTE CARLO MIND ANSWER (primary source for prose) ---")
    lines.append(_truncate(str(pack.get("mind_answer") or "(none)"), 2400))
    lines.append("")
    # Short thesis abstracts only (first ~40 lines or Abstract section)
    for i, th in enumerate(pack.get("tissue_theses") or [], 1):
        md = str(th.get("markdown") or "")
        excerpt = _thesis_excerpt(md, max_chars=900)
        lines.append(f"--- TISSUE EXCERPT [{i}] {th.get('id')} ---")
        lines.append(excerpt)
        lines.append("")
    lines.append("=== END CONTEXT ===")
    lines.append(
        "INSTRUCTIONS: Answer USER_QUERY in clear scientific paragraphs. "
        "Do not continue markdown tables or dump the context. "
        "Cite S and D_eff from FOCUS SCALARS when relevant."
    )
    return "\n".join(lines)


def _thesis_excerpt(md: str, max_chars: int = 900) -> str:
    """Prefer Abstract / first prose block; avoid mid-table cuts when possible."""
    md = (md or "").strip()
    if not md:
        return "(no thesis)"
    # strip huge tables lightly
    lines = []
    for ln in md.splitlines():
        if ln.strip().startswith("|") and lines and lines[-1].strip().startswith("|"):
            # keep table headers only briefly
            if sum(1 for x in lines if x.strip().startswith("|")) > 6:
                continue
        lines.append(ln)
    text = "\n".join(lines)
    # try abstract section
    low = text.lower()
    for key in ("## abstract", "# abstract", "**abstract**"):
        i = low.find(key)
        if i >= 0:
            chunk = text[i : i + max_chars]
            return _truncate(chunk, max_chars)
    return _truncate(text, max_chars)


_model = None
_tokenizer = None
_load_error: str | None = None


def unload_model() -> None:
    global _model, _tokenizer, _load_error
    _model = None
    _tokenizer = None
    _load_error = None
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def load_model(*, force: bool = False) -> dict[str, Any]:
    """
    Load Qwen2.5-7B-Instruct from local safetensors.

    Prefer 4-bit (bitsandbytes) on ≤12–16 GB GPUs; else fp16 device_map;
    else CPU. Override: FSOT_MC_QWEN_LOAD=4bit|8bit|fp16|cpu
    """
    global _model, _tokenizer, _load_error
    if _model is not None and _tokenizer is not None and not force:
        return {"ok": True, "loaded": True, "path": str(model_dir()), "cached": True}

    st = model_ready()
    if not st["ok"]:
        _load_error = st["hint"]
        return {"ok": False, "error": "model_not_downloaded", **st}

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        return {
            "ok": False,
            "error": "missing_deps",
            "detail": str(exc),
            "hint": "pip install torch transformers accelerate safetensors",
        }

    path = str(model_dir())
    pref = (os.environ.get("FSOT_MC_QWEN_LOAD") or "").strip().lower()
    use_cuda = torch.cuda.is_available() and pref != "cpu"

    def _try_load(**kwargs: Any) -> Any:
        return AutoModelForCausalLM.from_pretrained(path, **kwargs)

    try:
        _tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        mode = "unknown"
        # 1) 4-bit when CUDA (fits ~12 GB cards)
        if use_cuda and pref in ("", "4bit", "auto"):
            try:
                from transformers import BitsAndBytesConfig

                bnb = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                _model = _try_load(
                    quantization_config=bnb,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                mode = "4bit"
            except Exception as exc4:
                if pref == "4bit":
                    raise
                _load_error = f"4bit_failed:{exc4}"
                _model = None

        # 2) 8-bit
        if _model is None and use_cuda and pref in ("", "8bit", "auto"):
            try:
                from transformers import BitsAndBytesConfig

                bnb8 = BitsAndBytesConfig(load_in_8bit=True)
                _model = _try_load(
                    quantization_config=bnb8,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
                mode = "8bit"
            except Exception as exc8:
                if pref == "8bit":
                    raise
                _load_error = f"8bit_failed:{exc8}"
                _model = None

        # 3) fp16 full with device_map (needs ~14+ GB VRAM)
        if _model is None and use_cuda and pref in ("", "fp16", "auto"):
            try:
                dtype = torch.float16
                kw: dict[str, Any] = {
                    "trust_remote_code": True,
                    "device_map": "auto",
                    "low_cpu_mem_usage": True,
                }
                # transformers 5.x prefers dtype= ; older torch_dtype=
                try:
                    _model = _try_load(dtype=dtype, **kw)
                except TypeError:
                    _model = _try_load(torch_dtype=dtype, **kw)
                mode = "fp16"
            except Exception as exc16:
                if pref == "fp16":
                    raise
                _load_error = f"fp16_failed:{exc16}"
                _model = None

        # 4) CPU fp32/fp16 (slow, always works)
        if _model is None:
            dtype = torch.float32
            try:
                _model = _try_load(
                    dtype=dtype,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
            except TypeError:
                _model = _try_load(
                    torch_dtype=dtype,
                    trust_remote_code=True,
                    low_cpu_mem_usage=True,
                )
            mode = "cpu"

        _model.eval()
        _load_error = None
        return {
            "ok": True,
            "loaded": True,
            "path": path,
            "device": "cuda" if use_cuda and mode != "cpu" else "cpu",
            "load_mode": mode,
            "free_parameters": 0,
        }
    except Exception as exc:
        _model = None
        _tokenizer = None
        _load_error = str(exc)
        return {"ok": False, "error": "load_failed", "detail": str(exc), "path": path}


def narrate(
    query: str,
    *,
    pack: dict[str, Any] | None = None,
    node_id: str | None = None,
    n_paths: int = 48,
    chew: bool = False,
    max_new_tokens: int = 700,
    temperature: float = 0.4,
    load_if_needed: bool = True,
) -> dict[str, Any]:
    """
    Build pack (if needed) and generate Qwen narration.
    Returns structured pack + narration text.
    """
    if pack is None:
        pack = build_narration_pack(
            query=query,
            node_id=node_id,
            n_paths=n_paths,
            chew=chew,
        )

    if load_if_needed and _model is None:
        lr = load_model()
        if not lr.get("ok"):
            return {
                "ok": False,
                "error": lr.get("error"),
                "detail": lr.get("detail") or lr.get("hint"),
                "pack": pack,
                "narration": None,
                "fallback_answer": pack.get("mind_answer"),
                "free_parameters": 0,
                "note": "Pack built; model unavailable — use mind_answer / theses directly.",
            }

    if _model is None or _tokenizer is None:
        return {
            "ok": False,
            "error": "model_not_loaded",
            "detail": _load_error,
            "pack": pack,
            "narration": None,
            "fallback_answer": pack.get("mind_answer"),
            "free_parameters": 0,
        }

    import torch

    user_content = (
        f"{pack.get('context_text')}\n\n"
        f"USER QUESTION:\n{query}\n\n"
        "Write the grounded explanation now."
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    try:
        prompt = _tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    except Exception:
        prompt = SYSTEM_PROMPT + "\n\n" + user_content + "\n\nAssistant:"

    # Keep prefill small enough for 12 GB + 4-bit weights
    max_input = int(os.environ.get("FSOT_MC_QWEN_MAX_INPUT", "3072"))
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_input,
    )
    # device_map=auto models: put tensors on first param device
    try:
        dev = next(_model.parameters()).device
    except Exception:
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = {k: v.to(dev) for k, v in inputs.items()}

    gen_kwargs: dict[str, Any] = {
        "max_new_tokens": min(int(max_new_tokens), 512),
        "do_sample": temperature > 0.05,
        "pad_token_id": _tokenizer.eos_token_id,
        "use_cache": True,
    }
    if gen_kwargs["do_sample"]:
        gen_kwargs["temperature"] = float(temperature)
        gen_kwargs["top_p"] = 0.9

    try:
        with torch.inference_mode():
            out = _model.generate(**inputs, **gen_kwargs)
    except torch.cuda.OutOfMemoryError:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {
            "ok": False,
            "error": "cuda_oom_generate",
            "detail": "Prompt too long for VRAM; shrink pack or set FSOT_MC_QWEN_MAX_INPUT=2048",
            "pack_summary": {
                "n_theses": pack.get("n_theses"),
                "routed_domains": pack.get("routed_domains"),
            },
            "fallback_answer": pack.get("mind_answer"),
            "free_parameters": 0,
        }

    in_len = inputs["input_ids"].shape[-1]
    gen_ids = out[0][in_len:]
    text = _tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

    return {
        "ok": True,
        "method": "fsot_qwen25_narrate",
        "model": DEFAULT_HF_ID,
        "model_path": str(model_dir()),
        "free_parameters": 0,
        "authority": "D1D38A",
        "query": query,
        "narration": text,
        "pack_summary": {
            "n_theses": pack.get("n_theses"),
            "routed_domains": pack.get("routed_domains"),
            "emergence_fraction_mean": pack.get("emergence_fraction_mean"),
        },
        "pack": pack if os.environ.get("FSOT_MC_NARRATE_FULL_PACK") == "1" else None,
        "mind_answer": pack.get("mind_answer"),
        "note": "Narration is speech over MC+tissue pack; not a new theory source.",
    }
