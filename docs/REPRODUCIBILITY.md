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

## 6. Conversational mind + Qwen (documentation chat)

**Model weights (not in git):**  
https://huggingface.co/dappalumbo91/FSOT-Qwen2.5-7B-Instruct  

See [QWEN_WEIGHTS.md](./QWEN_WEIGHTS.md).

```powershell
pip install -e ".[narrate]"
python scripts/download_qwen25_instruct.py   # from dappalumbo91/FSOT-Qwen2.5-7B-Instruct
python -m fsot_mc docs-index --rebuild-index
python -m fsot_mc chat -q "What does the Biology tissue thesis say about S?"
python -m fsot_mc chat                       # interactive multi-turn
python -m fsot_mc serve --port 8765          # UI “Talk to the work”
```

Legacy multipath mind (no Qwen):

```powershell
python -m fsot_mc ask --think -q "What does multipath emergence mean for biology?"
python -m fsot_mc ask --online --chew -q "quantum gravity and fluid spacetime"
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

## 9. Formal soft court + audit promote

```powershell
python -m fsot_mc formal
python -m fsot_mc scientific-audit
python -m fsot_mc audit-promote
```

Soft obligations are batch-oriented. **Promoted ≠ Lean-proved.** Full Lean per multipath step is intentionally out of design.

---

## 10. Visual graph UI (clone-reproducible)

```powershell
python -m fsot_mc serve --port 8765
# open http://127.0.0.1:8765/
```

Shipped assets (no rebuild required on first load):

| Path | Role |
|------|------|
| `frontend/` | canvas UI (app.js, index.html, styles) |
| `vendor/archive_bundle/data__connective_tissue_compact.json` | portable multi-scale tissue |
| `fsot_mc/full_atlas.json` | 402 domain folds + S_canonical |
| `fsot_mc/graph_model.py` | D_eff rings + S-order layout |

Layout: classic multi-scale **D_eff shells** around seed→K hub; nodes on each ring ordered by **signed S**. Zoom densifies coupling mesh.

```powershell
python -m fsot_mc graph --scope core   # JSON summary if CLI supports; else serve UI
curl http://127.0.0.1:8765/api/health
curl "http://127.0.0.1:8765/api/graph?scope=core&n_paths=16"
```

---

## 11. PRED bench + flip protocols (v1.5)

```powershell
python -m fsot_mc pred-bench
python -m fsot_mc pred-bench --set PRED-001 --status in_progress --source "note"
python -m fsot_mc flip-protocols --n-paths 64
```

Ledger template ships under `data/pred_bench/closure_ledger.json` and `docs/PRED_BENCH_CLOSURE.md`.  
Lab still closes `pass`/`kill` with measured evidence — preregistered ≠ lab-closed.

---

## 12. Optional literature pack (Git LFS) + full local rebuild

### 12a. Shipped pack (clone-reproducible)

```powershell
git lfs install
git lfs pull
python scripts\bootstrap_independent.py
python -m fsot_mc literature-status
python -m fsot_mc literature-search -q "fluid spacetime cosmology"
```

| File | Contents |
|------|----------|
| `vendor/literature/arxiv_fts.sqlite` | ~100k FSOT-priority papers (FTS5) |
| `vendor/literature/wiki_fts.sqlite` | Simple Wikipedia FTS |
| `vendor/literature/MANIFEST.json` | build metadata |
| `vendor/archive_bundle/data__domain_coupling_simulation_benchmark.json` | full ~39k-edge coupling (LFS) |
| `vendor/optional_exports/` | audit / claims / flip / readings JSON samples |

Runtime resolution: use `data/literature/*` if present (your full rebuild); else fall back to `vendor/literature/*`.

### 12b. Full OAI dump (local only — multi-GB)

```powershell
$env:FSOT_MC_ARXIV_JSON = "C:\path\to\arxiv-metadata-oai-snapshot.json"
python -m fsot_mc literature-index --max-papers 0 --arxiv-only --rebuild-index
```

Rebuilds into `data/literature/` (gitignored). Does not replace the shipped 100k pack.

Repackage ship assets after rebuild:

```powershell
python scripts\package_optional_assets.py --max-papers 100000
```

---

## 13. What is *not* required to reproduce

- Physical Archive drive letter (`I:\…`)  
- Local `D:\training data\…` arXiv / wiki dumps  
- Live Realities OS kernel (snapshot is enough)  
- Live network (unless testing online chew)  
- GPU / Torch (CPU polar student fallback)  
- Pre-built literature FTS database  

---

## 14. Citation / related work

- Theory / formal: https://github.com/dappalumbo91/FSOT-2.1-Lean  
- This product: https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence  
- Author: Damian Arthur Palumbo  

`free_parameters = 0`. Seeds never move. Version **1.5.0**.
