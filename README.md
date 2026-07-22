# FSOT Monte Carlo Intelligence

**Standalone Fluid Spacetime Omni-Theory (FSOT 2.1) Monte Carlo intelligence**  
Author: **Damian Arthur Palumbo** · Authority pin **D1D38A** · `free_parameters = 0`

> Many futures exist until observation couples. FSOT seeds drive the scalar field;  
> pattern memory solidifies accurate signatures; only solid patterns may commit.

**Parent theory (law court):** [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean)  
**Physical archive:** `I:\FSOT-Physical-Archive` (definitive master)

Research only — **not financial advice**.

---

## What this is

An **application** of FSOT 2.1 to multipath intelligence:

| Layer | Role |
|-------|------|
| `fsot_mc/fast.py` | Seed constants (π, e, φ, γ, Catalan) + float scalar `S = K·(T1+T2+T3)` |
| `fsot_mc/compute_authority.py` | Exact mpmath authority engine (SHA-256 **D1D38A**) |
| `fsot_mc/routes.py` | Preregistered Finance/Economics domain folds |
| `fsot_mc/intrinsic.py` | Market observer → μ, σ, quirk_mod, dual-scale helpers |
| `fsot_mc/pattern_memory.py` | Discrete FSOT signatures · φ-EWMA accuracy · solidify/soften |
| `fsot_mc/monte_carlo.py` | Observer-collapse multipath MC · dynamic training |
| `fsot_mc/bhs_engine.py` | Buy/Hold/Sell multi-gate layer (HOLD default) |
| `fsot_mc/intelligence.py` | Unified multi-horizon + crypto-aware intelligence API |
| `fsot_mc/forward_journal.py` | True-future scoring (no look-ahead) |
| `fsot_mc/authority_gate.py` | Fail-closed constant + hash verification |

**Epistemic tier:** *measured application* of FSOT folds to time-series intelligence — not a replacement for the multi-prover Lean hub.

---

## Ontology (FSOT-faithful)

1. Reality is one seed-derived scalar field; markets are Finance/Economics **folds**.
2. Observation couples via `quirk_mod` and consciousness factor `C`.
3. Each Monte Carlo step: rebuild δψ from fluctuation + sentiment;  
   `p_collapse` from consciousness × phase departure.
4. **Collapse TRUE** → FSOT μ + γ-vol path.  
   **Collapse FALSE** → Poof chaotic branch.
5. History trains **pattern signatures**; accurate ones **solidify** and bias later paths.
6. Unsolidified signatures stay **fluid → FLAT** (cannot commit).
7. Optional BHS: HOLD default; BUY/SELL only when dual-scale + solid + edge gates pass.

Forbidden (founding debt): per-ticker `D_eff` fits, RSI invented coeffs, `S×multiplier+base`.

---

## Quick start

```powershell
cd C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/ -q
python -m fsot_mc gate
python -m fsot_mc intel
```

With market history (set data root or use `D:\training data\FSOT-Market-History`):

```powershell
$env:FSOT_MC_DATA_ROOT = "D:\training data\FSOT-Market-History"
python -m fsot_mc intel --symbol BTC --history
python -m fsot_mc journal --symbol SPY --history
python -m fsot_mc bhs --symbol ETH --history
```

### Package API

```python
import pandas as pd
from fsot_mc import (
    verify_fsot_gate,
    run_intelligence,
    run_dynamic_fsot_monte_carlo,
    run_bhs_backtest,
    run_forward_journal_walk,
)

assert verify_fsot_gate()["ok"]

# df columns: time, open, high, low, close, volume
intel = run_intelligence(df, symbol="BTC", horizon=13, n_paths=256)
print(intel["primary_signal"], intel["primary_confidence"])

mc = run_dynamic_fsot_monte_carlo(df, horizon=21, n_paths=256, symbol="SPY", persist=False)
bhs = run_bhs_backtest(df, capital=10_000, symbol="BTC")
```

---

## FSOT fidelity checklist

| Check | Status |
|-------|--------|
| Seeds π, e, φ, γ, G only | Yes |
| `S = K·(T1+T2+T3)` matches archive | Yes (float rel err ~1e-15) |
| Authority SHA-256 D1D38A | Gated in `verify_fsot_gate()` |
| Economics D_eff=20, hits=3, δψ=1.5 | From core 35-domain table |
| Finance D_eff=19 extension fold | Preregistered, not fitted |
| quirk_mod / consciousness_factor | Lean-aligned |
| free_parameters | Always 0 in outputs |

```bash
python -m fsot_mc gate
```

---

## Publishing

| Platform | Status / how |
|----------|----------------|
| **GitHub** | `scripts/publish_github.ps1` after `gh auth login` |
| **Hugging Face** | Dataset + Space card under `publishing/huggingface/` |
| **Kaggle** | Notebook + dataset under `publishing/kaggle/` |

Export bundles:

```powershell
python scripts/export_publication_bundle.py --symbol BTC --history
```

---

## Relation to other FSOT projects

| Project | Role |
|---------|------|
| FSOT-2.1-Lean / I: archive | Law, proofs, 400+ domains |
| FSOT-Market-Monitor | Full UI + paper trading stack |
| **This repo** | Pure MC intelligence (portable) |

---

## License

Apache-2.0 · Copyright 2026 Damian Arthur Palumbo
