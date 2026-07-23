# Local models (not in git)

## Qwen2.5-Instruct 7B (narration mouth)

```powershell
pip install torch transformers accelerate safetensors huggingface_hub
python scripts/download_qwen25_instruct.py
```

Installs safetensors to:

```text
vendor/models/Qwen2.5-7B-Instruct/
```

### Use

```powershell
pip install bitsandbytes   # 4-bit load for ≤12–16 GB GPUs
$env:FSOT_MC_QWEN_LOAD = "4bit"          # auto|4bit|8bit|fp16|cpu
$env:FSOT_MC_QWEN_MAX_INPUT = "2048"     # prompt tokens (VRAM safety)

python -m fsot_mc narrate-status
python -m fsot_mc narrate -q "Explain multipath emergence for biology under FSOT" --node Biology
python -m fsot_mc narrate -q "What is S for Cosmology?" --node Cosmology --max-tokens 300
```

API:

- `GET /api/narrate/status`
- `POST /api/narrate` `{ "query": "...", "node_id": "optional", "n_paths": 32 }`

### Doctrine

- Monte Carlo mind + tissue theses = intelligence / law  
- Qwen = articulation only (`free_parameters=0`, pin D1D38A)  
- Weights **gitignored** (~15 GB safetensors) — each machine runs `download_qwen25_instruct.py` once  

Override path: `FSOT_MC_QWEN_PATH=C:\path\to\Qwen2.5-7B-Instruct`
