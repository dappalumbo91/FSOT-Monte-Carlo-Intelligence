---
license: apache-2.0
base_model: Qwen/Qwen2.5-7B-Instruct
tags:
  - FSOT
  - Fluid-Spacetime-Omni-Theory
  - qwen2.5
  - conversational
  - physics
  - zero-free-parameters
language:
  - en
library_name: transformers
pipeline_tag: text-generation
---

# FSOT-Qwen2.5-7B-Instruct

**Conversational mouth** for [Fluid Spacetime Omni-Theory (FSOT)](https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence) Monte Carlo Intelligence.

| | |
|--|--|
| **Base** | [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) |
| **Role** | Articulate docs/tissue RAG + live fold scalars — **not** a new law engine |
| **Law court** | Pin **D1D38A** · `free_parameters = 0` · [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean) |
| **Code** | [FSOT-Monte-Carlo-Intelligence](https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence) |

## Important

- **FSOT = Fluid Spacetime Omni-Theory** (Damian Arthur Palumbo).
- Seeds / \(K\) / pin are **never** trained by this product.
- Optional **LoRA adapters** for articulation live in the code repo under `data/models/articulation/lora/` (local); this HF repo hosts the **base safetensors**.
- Soft court promote ≠ Lean-proved. Green gate ≤0.5% ≠ multipath map occupancy.

## Use with the product

```powershell
git clone https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence.git
cd FSOT-Monte-Carlo-Intelligence
pip install -e ".[narrate]"
python scripts/download_qwen25_instruct.py
python -m fsot_mc serve --port 8765
# UI: 2D/3D toggle · Talk to the work (this model) · free_parameters=0
```

Product UI includes **2D + 3D** connective graph (As Above So Below shells) and docs RAG chat over this base model (+ optional local LoRA adapters, not in this HF repo).

## Related

- Code: https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence  
- Lean court: https://github.com/dappalumbo91/FSOT-2.1-Lean  
- Dataset snapshot: https://huggingface.co/datasets/dappalumbo91/fsot-monte-carlo-intelligence  

## License

Apache-2.0 (upstream Qwen2.5-Instruct). Product code is MIT.
