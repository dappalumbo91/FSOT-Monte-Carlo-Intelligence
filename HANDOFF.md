# Handoff — FSOT Universe Monte Carlo Intelligence

**Workspace:** `C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence`  
**Version:** 0.3.0  
**Product:** Universe simulation + discovery under FSOT — **NOT markets**

## Vision (locked)

Use FSOT to Monte-Carlo the universe: multipath observation histories across the
35-domain map, discover new pathways, bridges, and physics candidates, align with
real FSOT data, hand leads to Lean/lab verification.

## Primary API

```python
from fsot_mc import run_intelligence, run_universe_monte_carlo, run_discovery, snapshot_universe
intel = run_intelligence(n_paths=256)
```

## CLI

```text
python -m fsot_mc gate
python -m fsot_mc atlas
python -m fsot_mc scan --n-paths 128
python -m fsot_mc intel --n-paths 256
```

## Core modules

| Module | Role |
|--------|------|
| universe_atlas | 35-domain FSOT map |
| universe_mc | multipath universe simulation |
| discovery | candidate ledger |
| real_data | archive anchors |
| intelligence | primary entry |
| authority_gate | D1D38A |

## Legacy (ignore for product)

`monte_carlo.py`, `intrinsic.py`, `bhs_engine.py`, `pattern_memory.py` — market extract.

## Foundation

`I:\FSOT-Physical-Archive` — law court, public data, Realities OS.

## Next

1. Expand atlas beyond 35 core → extension panel folds from navigator  
2. Deeper contested-physics probes (H0, σ8, hierarchy) with archive benchmarks  
3. Pathway solidification memory for *domain signatures* (not tickers)  
4. Couple to Realities OS kernel ticks as live universe substrate  
5. Publish GitHub/HF/Kaggle as **universe discovery** product  
