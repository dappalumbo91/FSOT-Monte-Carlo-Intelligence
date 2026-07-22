# Handoff — FSOT Universe Monte Carlo Intelligence

**Workspace:** `C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence`  
**Version:** 0.5.0  
**Product:** Universe simulation + discovery under FSOT — **NOT markets**

## Vision (locked)

Use FSOT to Monte-Carlo the universe: multipath observation histories across the
domain map, discover pathways/physics, see via π-ring, verify via soft formal court.

## Stack status (all layers)

| Layer | Status | Entry |
|-------|--------|-------|
| 1 Archive sync | Done | `scripts/sync_archive_bundle.py` |
| 2 Full atlas 402 | Done | `python -m fsot_mc build-atlas` |
| 3 Pathway memory | Done | automatic in MC |
| 4 Contested physics | Done | in discovery |
| 5 π-ring + PFLT eyes | Done | `python -m fsot_mc eyes` |
| 6 Formal soft court | Done | `python -m fsot_mc formal` |
| 7 Realities client | Done | `python -m fsot_mc realities` |
| 8 Live APIs offline-first | Done | `python -m fsot_mc apis` |
| 9 Publish check | Done | `python -m fsot_mc publish-check` |

## Primary API

```python
from fsot_mc import run_intelligence
intel = run_intelligence(
    n_paths=128,
    scope="core",          # or "full"
    with_eyes=True,
    with_formal_promote=True,
    with_realities=True,
    with_apis=True,
)
```

## CLI

```text
python -m fsot_mc gate
python -m fsot_mc build-atlas
python -m fsot_mc intel --scope core --n-paths 128 --with-formal --with-apis --with-realities
python -m fsot_mc eyes
python -m fsot_mc formal
python -m fsot_mc realities
python -m fsot_mc apis          # offline demo cache; --online for network
python -m fsot_mc publish-check
```

## Publish (needs your auth)

```powershell
gh auth login
.\scripts\publish_github.ps1
huggingface-cli login
.\scripts\publish_huggingface.ps1
# kaggle.json then:
.\scripts\publish_kaggle.ps1
```

## Foundation

- Law: `I:\FSOT-Physical-Archive\02_FSOT-2.1-Lean-Full`
- PFLT eyes: `C:\Users\damia\Desktop\pflt`
- Realities: `I:\FSOT-Physical-Archive\10_Realities-OS`

## Doctrine

Python discovers · π-ring sees · PFLT senses · Lean judges (batch) · archive remembers · APIs only feed · seeds never move.
