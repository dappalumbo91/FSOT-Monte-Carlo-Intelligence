# Reproducibility — FSOT Monte Carlo Intelligence

Anyone with Python ≥3.11 should be able to clone this repo, install requirements, and reproduce the authority gate, multipath runs, accuracy readings, and tests **without** the local Physical Archive drive.

---

## 1. Environment

```powershell
git clone https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence.git
cd FSOT-Monte-Carlo-Intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Dependencies** (see `requirements.txt` / `pyproject.toml`):

- `numpy>=1.26`
- `pandas>=2.2`
- `mpmath>=1.3`
- `pytest>=8.3` (dev/tests)

Optional: network for live arXiv/Wikipedia (`FSOT_MC_ONLINE=1`). Optional: PyTorch for GPU polar student (`FSOT_MC_USE_TORCH=1`).

---

## 2. Authority pin (must pass)

```powershell
python -m fsot_mc gate
python -m fsot_mc independent
```

Expected:

- `authority_ok=True`
- SHA-256 prefix **D1D38A…**
- float engine matches pinned seeds
- independent mode OK under `vendor/` + `fsot_mc/`

Pin file: `fsot_mc/PIN.json`  
Law mirror: `fsot_mc/compute_authority.py`

---

## 3. Tests

```powershell
python -m pytest tests/ -q
```

All tests should pass offline.

---

## 4. Canonical multipath + intelligence

```powershell
python -m fsot_mc atlas
python -m fsot_mc intel --n-paths 128 --seed 0 --with-formal --with-apis
python -m fsot_mc discover --n-paths 128 --seed 0
```

Determinism: same `--seed` and path count → comparable ensemble statistics (float MC has path noise; seed fixes the RNG stream).

---

## 5. Cross-domain accuracy readings

```powershell
python -m fsot_mc readings --n-paths 80 --seed 0
# or
python -m fsot_mc accuracy --json
```

Produces human text + JSON under `data/exports/accuracy_readings_*.json` (gitignored; regenerate locally).

**Acceptable margins (project standard):**

| Check | Pass criterion |
|-------|----------------|
| Archive green gate | pooled median ≤ **0.5%** |
| Strict scalar max | ≤ **0.5%** |
| Contested panel | FSOT error ≪ **15%** current-model baseline |
| Core S recompute | ~0% vs atlas `S_canonical` |
| Multipath map occupancy | exploratory; natural band ~0.55–0.78 |

Local bundle evidence:

- `vendor/archive_bundle/benchmarks/benchmark_margin_audit.json`
- `vendor/archive_bundle/benchmarks/contested_observables_closure.json`
- `vendor/archive_bundle/benchmarks/publication_claims_manifest.json`

---

## 6. Conversational mind

```powershell
python -m fsot_mc ask --think -q "What does multipath emergence mean for biology?"
python -m fsot_mc ask -q "Compare FSOT to general relativity"
python -m fsot_mc ask -q "What FSOT fuels should we experiment on?"
python -m fsot_mc ask --online --chew -q "quantum gravity and fluid spacetime"
python -m fsot_mc chat
```

Chew is offline-first; live literature requires `--online` or `FSOT_MC_ONLINE=1`.

---

## 7. Adaptive memory (short / long term)

```powershell
python -m fsot_mc memory-status
python -c "from fsot_mc.adaptive_memory import AdaptiveMemory; m=AdaptiveMemory(); print(m.summary())"
```

See [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md). Long-term store path: `data/memory/long_term.jsonl` (created at runtime; gitignored).

---

## 8. Optional archive refresh

If `I:\FSOT-Physical-Archive` is present:

```powershell
python scripts\sync_archive_bundle.py
python scripts\bootstrap_independent.py
```

Never mutate the archive from this repo. Sync is one-way into `vendor/archive_bundle/`.

---

## 9. Formal soft court

```powershell
python -m fsot_mc formal
```

Soft obligations are batch-oriented. Full Lean per multipath step is intentionally **out of design** (see architecture doc).

---

## 10. What is *not* required to reproduce

- Physical Archive drive letter  
- Live Realities OS kernel (snapshot is enough)  
- Live network (unless testing online chew)  
- GPU / Torch (CPU polar student fallback)

---

## 11. Citation / related work

- Theory / formal: https://github.com/dappalumbo91/FSOT-2.1-Lean  
- This product: FSOT Monte Carlo Intelligence (universe discovery)  
- Author: Damian Arthur Palumbo  

`free_parameters = 0`. Seeds never move.
