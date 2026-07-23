"""
Adaptive articulation learning — LoRA adapters on Qwen only.

Doctrine
--------
- free_parameters = 0 for FSOT *law* (seeds, K, pin D1D38A). Never trained here.
- Monte Carlo + docs + soft court remain the cortex; Qwen is the mouth.
- Lean / pin gate is the law court: training samples are admitted only if the
  authority gate passes and the sample is doctrine-safe.
- Soft court promote ≠ Lean-proved. Adapters never claim new physics.

What trains
-----------
Small PEFT LoRA weights under data/models/articulation/lora/
Base safetensors under vendor/models/ stay read-only.

Loop
----
  harvest (docs / gated chat) → sample queue → micro QLoRA train → load adapter on serve

CLI
---
  python -m fsot_mc articulate-seed
  python -m fsot_mc articulate-train --max-steps 40
  python -m fsot_mc articulate-status
  python -m fsot_mc articulate-loop
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.paths import PACKAGE_ROOT, data_root

ARTICULATION_DIR = data_root() / "models" / "articulation"
SAMPLES_PATH = ARTICULATION_DIR / "samples.jsonl"
LEDGER_PATH = ARTICULATION_DIR / "train_ledger.jsonl"
ADAPTER_DIR = ARTICULATION_DIR / "lora"
META_PATH = ARTICULATION_DIR / "meta.json"

# Claim-tier / identity fixed pairs — always safe after gate (not invented law)
IDENTITY_SFT: list[dict[str, str]] = [
    {
        "id": "id-fsot-name",
        "user": "What is FSOT?",
        "assistant": (
            "FSOT is Fluid Spacetime Omni-Theory — Damian Arthur Palumbo's theory of everything "
            "architecture. In this workspace, FSOT Monte Carlo Intelligence is the multipath "
            "discovery product under that law. free_parameters = 0; authority pin D1D38A. "
            "It is not an unrelated acronym."
        ),
        "tier": "MEASURED_STRUCTURE",
        "source": "identity_seed",
    },
    {
        "id": "id-my-work",
        "user": "What is my work / this project?",
        "assistant": (
            "Your work here is Fluid Spacetime Omni-Theory (FSOT) realized as FSOT Monte Carlo "
            "Intelligence: multipath observer-coupled simulation over one fluid spacetime, "
            "connective tissue docs, and a soft formal court that feeds Lean obligations. "
            "The law court is pin D1D38A / FSOT-2.1-Lean; this product does not refit seeds."
        ),
        "tier": "MEASURED_STRUCTURE",
        "source": "identity_seed",
    },
    {
        "id": "id-free-params",
        "user": "Does FSOT have free parameters?",
        "assistant": (
            "No. Under Fluid Spacetime Omni-Theory (FSOT), free_parameters = 0. Seeds π, e, φ, γ, "
            "Catalan and derived K never move under authority pin D1D38A. Domains are folds of one "
            "fluid spacetime, not separately fitted models."
        ),
        "tier": "MEASURED",
        "source": "identity_seed",
    },
    {
        "id": "id-s-vitality",
        "user": "What does S mean in FSOT?",
        "assistant": (
            "In Fluid Spacetime Omni-Theory, S is vitality under S = K·(T1+T2+T3), not importance. "
            "S > 0 is emergence (structure-forming); S ≤ 0 is dispersal (damping) but still lawful "
            "in the same fluid. Never rank folds as more important because |S| is larger."
        ),
        "tier": "MEASURED_STRUCTURE",
        "source": "identity_seed",
    },
    {
        "id": "id-green-vs-multi",
        "user": "What is the green gate vs multipath co-emergence?",
        "assistant": (
            "In Fluid Spacetime Omni-Theory there are two different metrics. Green gate: archive "
            "empirical bar — domain median_error_pct ≤ 0.5% (MEASURED panel accuracy). Multipath "
            "map co-emergence: mean over observer paths of (count of folds with S>0)/n_folds, "
            "often ~60–70% map occupancy. Multipath is not the green gate and not P(Earth has life)."
        ),
        "tier": "MEASURED_STRUCTURE",
        "source": "identity_seed",
    },
    {
        "id": "id-lean-court",
        "user": "How does this relate to Lean verification?",
        "assistant": (
            "Under Fluid Spacetime Omni-Theory, FSOT-2.1-Lean (and the physical archive copy) is the "
            "formal multi-prover law court. This Monte Carlo product keeps accuracy to pin D1D38A and "
            "may soft-promote obligations as candidates; soft court promote is not Lean-proved. Seeds stay fixed."
        ),
        "tier": "STRUCTURE",
        "source": "identity_seed",
    },
    {
        "id": "id-mouth-cortex",
        "user": "What is the Qwen model for in this project?",
        "assistant": (
            "Qwen2.5-Instruct is the conversational mouth over the Fluid Spacetime Omni-Theory cortex: "
            "multipath MC, tissue theses, docs RAG, and live fold scalars. It must not invent free "
            "parameters or new law. Adaptive articulation training may LoRA only this mouth — never the seeds."
        ),
        "tier": "STRUCTURE",
        "source": "identity_seed",
    },
]

_FORBIDDEN_IN_TARGET = (
    "lean-proved by this chat",
    "we proved in lean just now",
    "free parameter",
    "fitted constant",
    "fsot means feature",
    "fsot stands for finite",
    "fsot is finance",
)


def ensure_dirs() -> None:
    ARTICULATION_DIR.mkdir(parents=True, exist_ok=True)


def adapter_dir() -> Path:
    return ADAPTER_DIR


def adapter_ready() -> bool:
    d = ADAPTER_DIR
    return d.is_dir() and (d / "adapter_config.json").is_file()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sample_hash(user: str, assistant: str) -> str:
    h = hashlib.sha256(f"{user.strip()}\n---\n{assistant.strip()}".encode("utf-8")).hexdigest()
    return h[:16]


def gate_for_training() -> dict[str, Any]:
    """Fail-closed: no articulation train without pin integrity."""
    g = verify_fsot_gate(require_archive=False)
    ok = bool(g.get("ok"))
    return {
        "ok": ok,
        "authority": g.get("authority_sha256") or AUTHORITY_SHA256[:6],
        "free_parameters": 0,
        "gate": g,
        "note": "Law seeds never train; only Qwen LoRA adapters after gate.",
    }


def admit_sample(
    user: str,
    assistant: str,
    *,
    source: str = "manual",
    tier: str = "STRUCTURE",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Admit one supervised pair into the queue only if pin gate passes
    and the target text is doctrine-safe.
    """
    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed", "gate": g}

    user = (user or "").strip()
    assistant = (assistant or "").strip()
    if len(user) < 3 or len(assistant) < 40:
        return {"ok": False, "error": "too_short"}

    low = assistant.lower()
    for bad in _FORBIDDEN_IN_TARGET:
        if bad in low:
            return {"ok": False, "error": "forbidden_claim", "detail": bad}

    # Identity samples must name Fluid Spacetime when teaching FSOT
    if re.search(r"\bfsot\b", user.lower()) and source in ("identity_seed", "chat", "docs"):
        if "fluid" not in low and "spacetime" not in low and "space-time" not in low:
            # allow non-definition questions; only enforce for definition-ish
            if any(k in user.lower() for k in ("what is", "stands for", "mean", "my work", "this project")):
                return {"ok": False, "error": "missing_fluid_spacetime_identity"}

    ensure_dirs()
    row = {
        "id": _sample_hash(user, assistant),
        "ts": _utc_now(),
        "user": user[:2000],
        "assistant": assistant[:4000],
        "source": source,
        "tier": tier,
        "authority": AUTHORITY_SHA256[:12],
        "free_parameters": 0,
        "meta": meta or {},
        "trained": False,
    }
    # dedupe by id
    existing = {r["id"] for r in load_samples()}
    if row["id"] in existing:
        return {"ok": True, "admitted": False, "reason": "duplicate", "id": row["id"]}

    with SAMPLES_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, "admitted": True, "id": row["id"], "source": source}


def load_samples(*, untrained_only: bool = False) -> list[dict[str, Any]]:
    if not SAMPLES_PATH.is_file():
        return []
    out = []
    for line in SAMPLES_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if untrained_only and row.get("trained"):
            continue
        out.append(row)
    return out


def mark_samples_trained(ids: list[str]) -> None:
    if not ids or not SAMPLES_PATH.is_file():
        return
    idset = set(ids)
    rows = load_samples()
    for r in rows:
        if r.get("id") in idset:
            r["trained"] = True
            r["trained_at"] = _utc_now()
    with SAMPLES_PATH.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def harvest_identity_seeds() -> dict[str, Any]:
    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed", "gate": g}
    admitted = 0
    skipped = 0
    for s in IDENTITY_SFT:
        r = admit_sample(
            s["user"],
            s["assistant"],
            source=s.get("source", "identity_seed"),
            tier=s.get("tier", "STRUCTURE"),
            meta={"seed_id": s.get("id")},
        )
        if r.get("admitted"):
            admitted += 1
        else:
            skipped += 1
    return {
        "ok": True,
        "admitted": admitted,
        "skipped": skipped,
        "n_queue": len(load_samples()),
        "free_parameters": 0,
    }


def harvest_from_docs(*, limit: int = 24) -> dict[str, Any]:
    """
    Build supervised pairs from key project docs (read → solidify as articulation targets).
    Uses methodology / claims / achievements — not free invention.
    """
    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed", "gate": g}

    paths = [
        PACKAGE_ROOT / "docs" / "METHODOLOGY.md",
        PACKAGE_ROOT / "docs" / "CLAIMS.md",
        PACKAGE_ROOT / "docs" / "ACHIEVEMENTS.md",
        PACKAGE_ROOT / "docs" / "QWEN_WEIGHTS.md",
        PACKAGE_ROOT / "README.md",
    ]
    admitted = 0
    for p in paths:
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # take first substantive section (~1200 chars)
        body = text.strip()
        if len(body) < 80:
            continue
        chunk = body[:1400]
        # strip huge tables somewhat
        chunk = re.sub(r"\|[^\n]+\|\n", "", chunk)
        user = (
            f"Using project document {p.as_posix().split('FSOT-Monte-Carlo-Intelligence/')[-1]}, "
            f"explain what this says about Fluid Spacetime Omni-Theory (FSOT) and this product. "
            f"Keep free_parameters=0 and pin D1D38A."
        )
        assistant = (
            f"From {p.name} under Fluid Spacetime Omni-Theory (FSOT), free_parameters=0, pin D1D38A:\n\n"
            f"{chunk.strip()}\n\n"
            "This is documentation of the pinned law product — not a new fit of constants."
        )
        r = admit_sample(
            user,
            assistant,
            source="docs",
            tier="STRUCTURE",
            meta={"path": str(p.relative_to(PACKAGE_ROOT))},
        )
        if r.get("admitted"):
            admitted += 1
        if admitted >= limit:
            break

    # optional Lean court README if present on Desktop
    lean_readme = Path(r"C:\Users\damia\Desktop\FSOT-2.1-Lean\FSOT-2.1-Lean-main\FSOT-2.1-Lean-main\README.md")
    if not lean_readme.is_file():
        lean_readme = Path(r"C:\Users\damia\Desktop\FSOT-2.1-Lean\FSOT-2.1-Lean-main\README.md")
    if lean_readme.is_file():
        try:
            lt = lean_readme.read_text(encoding="utf-8", errors="replace")[:1200]
            admit_sample(
                "How does FSOT-2.1-Lean relate to this Monte Carlo intelligence product?",
                (
                    "FSOT-2.1-Lean is the formal multi-prover law court for Fluid Spacetime Omni-Theory. "
                    "This product (FSOT Monte Carlo Intelligence) holds accuracy to pin D1D38A and may "
                    "export soft-court obligations; soft promote ≠ Lean-proved.\n\n"
                    f"Lean court README excerpt:\n{lt}"
                ),
                source="lean_court",
                tier="STRUCTURE",
                meta={"path": str(lean_readme)},
            )
            admitted += 1
        except OSError:
            pass

    return {
        "ok": True,
        "admitted": admitted,
        "n_queue": len(load_samples()),
        "free_parameters": 0,
    }


def harvest_from_chat_turn(
    user_message: str,
    reply: str,
    *,
    docs_used: list[Any] | None = None,
    live_scalars: list[Any] | None = None,
    grade: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Online loop hook: enqueue a chat turn only if env enables learning and
    the reply clears light quality bars.
    """
    if os.environ.get("FSOT_MC_ARTICULATE_LEARN", "").strip() not in ("1", "true", "yes"):
        return {"ok": False, "error": "learn_disabled", "hint": "Set FSOT_MC_ARTICULATE_LEARN=1"}

    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed"}

    reply = (reply or "").strip()
    if len(reply) < 80:
        return {"ok": False, "error": "reply_too_short"}

    # if graded, require decent score
    if grade is not None and float(grade.get("score") or 0) < 0.5:
        return {"ok": False, "error": "grade_too_low", "grade": grade}

    # identity hygiene
    um = (user_message or "").lower()
    if any(k in um for k in ("what is fsot", "stands for", "my work", "this project")):
        if "fluid" not in reply.lower() or "spacetime" not in reply.lower().replace("-", ""):
            return {"ok": False, "error": "identity_fail"}

    return admit_sample(
        user_message,
        reply,
        source="chat",
        tier="STRUCTURE",
        meta={
            "docs_used": docs_used or [],
            "live_scalars": live_scalars or [],
            "grade": grade,
        },
    )


def status() -> dict[str, Any]:
    samples = load_samples()
    untrained = [s for s in samples if not s.get("trained")]
    g = gate_for_training()
    return {
        "ok": True,
        "free_parameters": 0,
        "authority_gate_ok": g["ok"],
        "authority": AUTHORITY_SHA256[:12],
        "n_samples": len(samples),
        "n_untrained": len(untrained),
        "adapter_ready": adapter_ready(),
        "adapter_dir": str(ADAPTER_DIR),
        "samples_path": str(SAMPLES_PATH),
        "meta": _load_meta(),
        "doctrine": {
            "trains": "Qwen LoRA adapters only (articulation mouth)",
            "never_trains": "seeds, K, compute_authority, pin, domain S formulas",
            "law_court": "D1D38A + FSOT-2.1-Lean soft/hard court",
            "online_loop": "FSOT_MC_ARTICULATE_LEARN=1 enqueues gated chat turns",
        },
    }


def _load_meta() -> dict[str, Any]:
    if META_PATH.is_file():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_meta(meta: dict[str, Any]) -> None:
    ensure_dirs()
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _format_sft_text(tok: Any, user: str, assistant: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are the FSOT Monte Carlo Intelligence guide. "
                "FSOT = Fluid Spacetime Omni-Theory. free_parameters=0, pin D1D38A."
            ),
        },
        {"role": "user", "content": user},
        {"role": "assistant", "content": assistant},
    ]
    try:
        return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    except Exception:
        return f"System: FSOT=Fluid Spacetime Omni-Theory\nUser: {user}\nAssistant: {assistant}"


def micro_train(
    *,
    max_steps: int = 40,
    batch_size: int = 1,
    lr: float = 2e-4,
    lora_r: int = 8,
    max_seq_len: int = 768,
    force: bool = False,
) -> dict[str, Any]:
    """
    QLoRA micro-train on admitted samples. Unloads inference model first.
    Saves adapter under data/models/articulation/lora/ only.
    """
    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed", "gate": g}

    samples = load_samples(untrained_only=True)
    if not samples and not force:
        # allow retrain on all if force
        samples = load_samples()
    if not samples:
        return {
            "ok": False,
            "error": "empty_queue",
            "hint": "python -m fsot_mc articulate-seed",
        }

    # limit steps to available samples * small epochs
    n_use = min(len(samples), max(max_steps, 1))
    batch = samples[:n_use]

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as exc:
        return {
            "ok": False,
            "error": "missing_deps",
            "detail": str(exc),
            "hint": "pip install torch transformers peft bitsandbytes accelerate",
        }

    try:
        from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    except ImportError:
        return {
            "ok": False,
            "error": "missing_peft",
            "hint": "pip install peft",
        }

    from fsot_mc.qwen_narrate import model_dir, model_ready, unload_model

    st = model_ready()
    if not st.get("ok"):
        return {"ok": False, "error": "model_not_downloaded", **st}

    # free inference VRAM
    unload_model()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    path = str(model_dir())
    t0 = time.time()
    try:
        tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token

        use_cuda = torch.cuda.is_available()
        if use_cuda:
            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            model = AutoModelForCausalLM.from_pretrained(
                path,
                quantization_config=bnb,
                device_map={"": 0},
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                path,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )

        # continue from existing adapter if present
        if adapter_ready():
            model = PeftModel.from_pretrained(model, str(ADAPTER_DIR), is_trainable=True)
        else:
            lora_cfg = LoraConfig(
                r=int(lora_r),
                lora_alpha=int(lora_r * 2),
                lora_dropout=0.05,
                bias="none",
                task_type="CAUSAL_LM",
                target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            )
            model = get_peft_model(model, lora_cfg)

        model.train()
        opt = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=lr)

        steps_done = 0
        losses: list[float] = []
        device = next(model.parameters()).device

        for step in range(min(max_steps, len(batch) * 3)):
            row = batch[step % len(batch)]
            text = _format_sft_text(tok, row["user"], row["assistant"])
            enc = tok(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=max_seq_len,
                padding=False,
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            labels = enc["input_ids"].clone()
            opt.zero_grad(set_to_none=True)
            out = model(**enc, labels=labels)
            loss = out.loss
            if loss is None:
                continue
            loss.backward()
            opt.step()
            losses.append(float(loss.detach().float().cpu()))
            steps_done += 1

        ensure_dirs()
        ADAPTER_DIR.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(str(ADAPTER_DIR))
        tok.save_pretrained(str(ADAPTER_DIR))

        trained_ids = [r["id"] for r in batch]
        mark_samples_trained(trained_ids)

        meta = {
            "updated_at": _utc_now(),
            "steps": steps_done,
            "n_samples_batch": len(batch),
            "mean_loss": (sum(losses) / len(losses)) if losses else None,
            "lora_r": lora_r,
            "lr": lr,
            "base_model": path,
            "authority": AUTHORITY_SHA256[:12],
            "free_parameters": 0,
            "trains": "articulation_lora_only",
            "duration_s": round(time.time() - t0, 2),
        }
        _save_meta(meta)
        with LEDGER_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")

        # release train model so serve can reload with adapter
        del model
        del opt
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return {
            "ok": True,
            "adapter_dir": str(ADAPTER_DIR),
            "adapter_ready": True,
            "steps": steps_done,
            "mean_loss": meta["mean_loss"],
            "n_samples": len(batch),
            "duration_s": meta["duration_s"],
            "free_parameters": 0,
            "note": "Adapter saved. Restart serve / reload model to use it.",
        }
    except Exception as exc:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return {
            "ok": False,
            "error": "train_failed",
            "detail": str(exc),
            "free_parameters": 0,
        }


def articulate_loop(
    *,
    max_steps: int = 40,
    min_queue: int = 4,
    train: bool = True,
) -> dict[str, Any]:
    """Seed harvest → docs harvest → optional micro-train if queue large enough."""
    g = gate_for_training()
    if not g["ok"]:
        return {"ok": False, "error": "authority_gate_failed", "gate": g}

    id_r = harvest_identity_seeds()
    doc_r = harvest_from_docs()
    n_untrained = len(load_samples(untrained_only=True))
    train_r: dict[str, Any] | None = None
    if train and n_untrained >= min_queue:
        train_r = micro_train(max_steps=max_steps)
    elif train:
        train_r = {
            "ok": False,
            "error": "queue_below_min",
            "n_untrained": n_untrained,
            "min_queue": min_queue,
        }

    return {
        "ok": True,
        "identity": id_r,
        "docs": doc_r,
        "train": train_r,
        "status": status(),
        "free_parameters": 0,
    }


def try_attach_adapter(model: Any) -> dict[str, Any]:
    """
    Attach saved LoRA to a loaded base/4bit model for inference.
    Called from qwen_narrate.load_model after base load.
    """
    if not adapter_ready():
        return {"attached": False, "reason": "no_adapter"}
    if os.environ.get("FSOT_MC_ARTICULATE_ADAPTER", "1").strip() in ("0", "false", "no"):
        return {"attached": False, "reason": "disabled_by_env"}
    try:
        from peft import PeftModel
    except ImportError:
        return {"attached": False, "reason": "peft_not_installed"}
    try:
        # already peft?
        if hasattr(model, "peft_config"):
            return {"attached": True, "reason": "already_peft", "path": str(ADAPTER_DIR)}
        wrapped = PeftModel.from_pretrained(model, str(ADAPTER_DIR))
        wrapped.eval()
        return {
            "attached": True,
            "model": wrapped,
            "path": str(ADAPTER_DIR),
            "free_parameters": 0,
        }
    except Exception as exc:
        return {"attached": False, "reason": "attach_failed", "detail": str(exc)}
