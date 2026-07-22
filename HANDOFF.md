# Handoff — FSOT Universe Monte Carlo Intelligence

**Workspace:** `C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence`  
**Version:** 0.4.0  
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

## Done (v0.4)

1. Archive sync → `vendor/archive_bundle/`  
2. Full atlas **35 core + 367 ext = 402** (`python -m fsot_mc build-atlas`)  
3. Pathway memory (domain-signature solidify)  
4. Contested physics pack (H0 dual-anchor + archive closure + flip hotspots)  

## CLI

```text
python -m fsot_mc build-atlas
python -m fsot_mc atlas --scope core|full
python -m fsot_mc scan --scope full --n-paths 32
python -m fsot_mc intel --scope core --n-paths 128
```

## Next layers

5. π-ring + PFLT multilayer eyes  
6. Formal promote/batch court loop  
7. Realities OS client ticks  
8. Live APIs (offline-first caches)  
9. Publish as universe discovery  
