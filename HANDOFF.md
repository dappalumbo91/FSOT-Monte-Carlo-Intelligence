# Handoff — FSOT Monte Carlo Intelligence

**Workspace:** `C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence`  
**Version:** 0.2.0  
**Authority:** D1D38A (exact `compute_authority.py` from I: archive)

## Verified

- `pytest tests/` — authority gate + MC + intelligence API  
- `python -m fsot_mc gate` — float engine + local SHA match  
- Economics scalar matches archive to ~1e-15 rel err  

## API

```python
from fsot_mc import (
    verify_fsot_gate,
    run_intelligence,           # unified multi-horizon intelligence
    run_dynamic_fsot_monte_carlo,
    run_bhs_backtest,
    run_forward_journal_walk,
    multi_horizon_mc,
)
```

## CLI

```text
python -m fsot_mc gate
python -m fsot_mc intel [--symbol BTC --history]
python -m fsot_mc journal --symbol SPY --history
python -m fsot_mc bhs --symbol ETH --history
```

## Data paths (portable)

```text
FSOT_MC_DATA_ROOT   → root (ohlcv/, patterns/, journals/)
FSOT_MC_OHLCV_DIR
FSOT_MC_PATTERN_DIR
FSOT_ARCHIVE_ROOT   → optional I:\FSOT-Physical-Archive
```

Default falls back to `D:\training data\FSOT-Market-History` if present.

## Publish (needs auth)

| Target | Command | Prerequisite |
|--------|---------|--------------|
| GitHub | `scripts/publish_github.ps1` | `gh auth login` |
| Hugging Face | `scripts/publish_huggingface.ps1` | `huggingface-cli login` |
| Kaggle | `scripts/publish_kaggle.ps1` | `~/.kaggle/kaggle.json` |

## FSOT foundation (do not forget)

- One engine `S = K·(T1+T2+T3)` from seeds only  
- I: archive is master; this package is an **application**  
- Never reintroduce per-symbol least-squares folds  
- Epistemic tier: measured_application  

## Parent projects

- Law: `I:\FSOT-Physical-Archive\02_FSOT-2.1-Lean-Full`  
- UI monitor: `C:\Users\damia\Desktop\FSOT-Market-Monitor`  

## Next intelligence goals

1. Drive solid commit accuracy toward 70–80% on BHS gates (real history)  
2. Forward journal continuous scoring on paper/live stream  
3. Multi-asset coupling via domain coupling (As Above So Below)  
4. Optional: ship demo dataset without requiring D: history  
