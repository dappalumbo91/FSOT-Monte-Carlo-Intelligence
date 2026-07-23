# Adaptive articulation learning (mouth LoRA)

**Purpose:** Internalize Fluid Spacetime Omni-Theory identity and project doctrine into a **small LoRA adapter** on Qwen so the model does not re-guess “what FSOT means” every turn.

**Hard boundary:** This trains **only** the conversational mouth (Qwen adapters). It never moves seeds, \(K\), pin **D1D38A**, domain \(S\) formulas, or Lean proofs.

---

## Architecture

```
                    ┌─────────────────────────────┐
                    │  Law court (immutable)      │
                    │  pin D1D38A / FSOT-2.1-Lean  │
                    │  free_parameters = 0         │
                    └──────────────┬──────────────┘
                                   │ gate (must pass)
                                   ▼
  docs / chat / MC scalars  →  admit sample  →  samples.jsonl
                                   │
                                   ▼
                         QLoRA micro-train (PEFT)
                                   │
                                   ▼
              data/models/articulation/lora/   (adapters only)
                                   │
                                   ▼
              load_model() attaches LoRA at serve / chat
```

| Layer | Role | Trains? |
|-------|------|---------|
| Seeds + `compute_authority` | Law | **Never** |
| Monte Carlo + atlas | Secondary brain / thought | No (run-time simulation) |
| Soft court / promote | Obligations → Lean candidates | No weights |
| Adaptive memory (engrams) | Routing / recall | Engrams, not GPU LoRA |
| **Qwen + LoRA** | Mouth / articulation | **Yes — adapters only** |

Lean court live location (your machines): GitHub [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean), Desktop checkout, and optional `I:\FSOT-Physical-Archive` hub. Runtime pin stays independent of I:.

---

## Commands

```powershell
# 1) Authority must be green
python -m fsot_mc gate

# 2) Harvest identity + methodology/claims (+ Lean README if present)
python -m fsot_mc articulate-seed

# 3) Micro-train LoRA (needs peft + GPU recommended)
pip install peft
python -m fsot_mc articulate-train --max-steps 40

# Or one-shot harvest + train when queue large enough
python -m fsot_mc articulate-loop --max-steps 40

# Status
python -m fsot_mc articulate-status
```

Artifacts (gitignored under `data/models/`):

| Path | Content |
|------|---------|
| `data/models/articulation/samples.jsonl` | Gated supervised pairs |
| `data/models/articulation/lora/` | PEFT adapter |
| `data/models/articulation/meta.json` | Last train meta |
| `data/models/articulation/train_ledger.jsonl` | Train history |

---

## Online loop (optional)

After a good chat turn, enqueue for the next train batch:

```powershell
$env:FSOT_MC_ARTICULATE_LEARN = "1"
python -m fsot_mc serve --port 8765
# later:
python -m fsot_mc articulate-train --max-steps 20
```

Admission rules:

1. `verify_fsot_gate()` must pass  
2. Target text must not claim free parameters / fake Lean proofs / wrong FSOT acronyms  
3. Identity questions must name **Fluid Spacetime**  
4. Optional grade score ≥ 0.5 when grading is present  

Disable adapter at load: `FSOT_MC_ARTICULATE_ADAPTER=0`.

---

## What this is not

- Not full-model fine-tune of 7B base weights  
- Not proof in Lean  
- Not permission to invent new physics  
- Not a substitute for docs RAG (RAG still supplies live numbers)

**Success criterion:** After train + reload, asking “What is FSOT?” answers **Fluid Spacetime Omni-Theory** from adapter + prompt, without inventing another acronym.
