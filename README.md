# FSOT Monte Carlo Intelligence

**Simulate the universe under Fluid Spacetime Omni-Theory — discover pathways, physics, and engineering leads.**

| | |
|--|--|
| **Author** | Damian Arthur Palumbo |
| **Version** | 1.5.0 |
| **License** | [MIT](LICENSE) |
| **Authority pin** | **D1D38A** · `free_parameters = 0` |
| **Theory law court** | [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean) |
| **Product** | Universe multipath intelligence (**not** markets) |

> Paradigm: one seed-derived fluid engine; domains are folds; multipath observation histories **are** thought.  
> Seeds never move. Discovery proposes; formal/empirical spine accepts or rejects.

---

## Docs

| Document | Purpose |
|----------|---------|
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | **Clone → install → gate → tests → UI** (start here) |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | How the system works scientifically |
| [docs/CLAIMS.md](docs/CLAIMS.md) | Data-first claims ledger (MEASURED / PREREG / STRUCTURE) |
| [docs/SCIENTIFIC_AUDIT_REPORT.md](docs/SCIENTIFIC_AUDIT_REPORT.md) | Full-domain scientific audit |
| [docs/PRED_BENCH_CLOSURE.md](docs/PRED_BENCH_CLOSURE.md) | PRED lab-closure ledger + kill criteria |
| [docs/FLIP_HOTSPOT_PROTOCOLS.md](docs/FLIP_HOTSPOT_PROTOCOLS.md) | Observer flip-hotspot experiment cards |
| [docs/LITERATURE_CORPUS.md](docs/LITERATURE_CORPUS.md) | Optional local arXiv / wiki index |
| [docs/MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md) | STM/LTM adaptive memory |
| [HANDOFF.md](HANDOFF.md) | Maintainer handoff |

---

## Quick start (fully offline-reproducible)

Requires **Python ≥ 3.11**. No I:/D: drives, no API keys for core path.

```powershell
git clone https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence.git
cd FSOT-Monte-Carlo-Intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e ".[dev]"   # optional: editable + pytest

# authority + independence (must pass)
python -m fsot_mc gate
python -m fsot_mc independent

# tests
python -m pytest tests/ -q

# accuracy readings + multipath mind
python -m fsot_mc readings --n-paths 64
python -m fsot_mc ask --think -q "What does multipath emergence mean?"

# visual UI
python -m fsot_mc serve --port 8765
# open http://127.0.0.1:8765/
```

Linux/macOS: use `source .venv/bin/activate` instead of the PowerShell activate line.

### Requirements

See [`requirements.txt`](requirements.txt) / [`pyproject.toml`](pyproject.toml):

- numpy ≥ 1.26  
- pandas ≥ 2.2  
- mpmath ≥ 1.3  
- pytest ≥ 8.3 (dev)

**Shipped for offline use:** `fsot_mc/` law+atlas, `vendor/archive_bundle/` (navigator, certificates, compact connective tissue, **raw coupling via Git LFS**), `vendor/pflt/`, `frontend/`, `docs/tissue/`.

**Optional assets (Git LFS — pull after clone):**

```powershell
git lfs install
git lfs pull
python scripts\bootstrap_independent.py   # copies vendor/literature → data/ if needed
python -m fsot_mc literature-status
python -m fsot_mc literature-search -q "quantum gravity fluid spacetime"
```

| Asset | Path | Size (approx) |
|-------|------|----------------|
| arXiv FTS (100k FSOT-priority) | `vendor/literature/arxiv_fts.sqlite` | ~275 MB (LFS) |
| Simple Wiki FTS | `vendor/literature/wiki_fts.sqlite` | ~14 MB (LFS) |
| Raw domain coupling benchmark | `vendor/archive_bundle/data__domain_coupling_simulation_benchmark.json` | ~32 MB (LFS) |
| Export snapshots | `vendor/optional_exports/` | small JSON |

**Still local-only (too large for GitHub):** full multi-million arXiv OAI dump / full multi-GB FTS rebuild — use your dump + `literature-index --max-papers 0`.

**Other optional:**

- Live web chew: `FSOT_MC_ONLINE=1`
- Torch polar student: `FSOT_MC_USE_TORCH=1`
- **Qwen2.5-Instruct 7B narration** (local safetensors):

```powershell
pip install -e ".[narrate]"   # torch transformers accelerate safetensors huggingface_hub
python scripts/download_qwen25_instruct.py   # ~15 GB → vendor/models/Qwen2.5-7B-Instruct/
python -m fsot_mc narrate-status
python -m fsot_mc narrate -q "Explain multipath emergence for biology under FSOT"
```

Weights are **gitignored** (download per machine). MC mind + tissue theses = intelligence; Qwen = articulate mouth only.

---

## Core commands

```text
python -m fsot_mc gate              # D1D38A authority
python -m fsot_mc independent       # local vendor integrity
python -m fsot_mc atlas | build-atlas
python -m fsot_mc intel --n-paths 128 --with-formal --with-apis
python -m fsot_mc discover
python -m fsot_mc readings          # cross-domain accuracy vs ≤0.5% / 15% baselines
python -m fsot_mc claims            # data-first claims ledger
python -m fsot_mc scientific-audit  # full audit (+ auto formal promote)
python -m fsot_mc audit-promote     # audit → soft-court obligations
python -m fsot_mc flip-protocols    # high-flip domain experiment cards
python -m fsot_mc pred-bench        # PRED closure ledger (open/pass/kill)
python -m fsot_mc ask | chat        # multipath mind
python -m fsot_mc memory-status     # STM/LTM adaptive memory
python -m fsot_mc graph             # multi-scale connective graph JSON
python -m fsot_mc solidify          # chew corpus → LTM
python -m fsot_mc protocols         # experiment protocol cards
python -m fsot_mc serve --port 8765 # full-stack visual UI + API
python -m fsot_mc eyes | relay | formal | realities | apis
python -m fsot_mc literature-status | literature-index | literature-search
```

---

## Visual full stack (v1.5)

Neural connective map × Obsidian second-brain aesthetic (**clone-reproducible**):

- **Seeds** (π, e, φ, γ, G) → **law K** hub (always connected)  
- **Domain folds** on classic **D_eff rings**, ordered by **signed S** on each shell  
- Compact archive tissue from `vendor/archive_bundle/data__connective_tissue_compact.json`  
- Zoom densifies lean-overlap coupling; pattern anneals then solidifies  
- Sidebar: multipath mind, accuracy, solidify, protocols, per-node tissue theses  

```powershell
python -m fsot_mc serve --port 8765
# → http://127.0.0.1:8765/
# scope: Full FSOT (archive) | Core 35
```

API: `/api/graph` `/api/ask` `/api/readings` `/api/memory` `/api/protocols` `/api/solidify` `/api/mc` `/api/tissue?id=…` `/api/health`

### Local literature (optional)

Offline cross-ref of verified research into FSOT folds (does **not** rewrite seeds). Not needed for gate/tests/UI.

```powershell
python -m fsot_mc literature-status
python -m fsot_mc literature-index --max-papers 100000 --max-articles 50000
# full OAI (long): python -m fsot_mc literature-index --max-papers 0 --arxiv-only
python -m fsot_mc literature-search -q "Hubble tension dark energy"
```

Override paths: `FSOT_MC_ARXIV_JSON` / `FSOT_MC_WIKI_ROOT`  
Docs: [docs/LITERATURE_CORPUS.md](docs/LITERATURE_CORPUS.md)

### Scientific tissue theses (per node)

Every seed, domain fold, extension panel, problem route, and preregistered prediction has a
**miniature research markdown** under [`docs/tissue/`](docs/tissue/INDEX.md):

- Abstract · Ontology · Mathematical formulation · Results · Application · Connective tissue · Epistemics  

```powershell
python -m fsot_mc tissue-docs
# open docs/tissue/INDEX.md  or click a node in the UI
```

---

## Ontology (short)

| Idea | Engine |
|------|--------|
| One medium | 25D fluid; \(S = K\cdot(T_1+T_2+T_3)\) from \(\pi,e,\varphi,\gamma,G\) |
| Domains | 35 core + 367 extension folds |
| Observation | quirk_mod → multipath collapse histories |
| Emergence % | mean over paths of (folds with \(S>0\))/n — map co-emergence |
| Empirical gate | archive pooled median **≤ 0.5%** |
| Contested baseline | often ~**15%** current models without unified spine |
| Memory | STM working fluid + LTM solidify (φ-EWMA, Poof bars) |
| Truth | pin D1D38A; Lean hub; experiment closes engineering |

---

## Python API

```python
from fsot_mc import (
    verify_fsot_gate,
    run_intelligence,
    run_universe_monte_carlo,
    run_discovery,
    run_accuracy_readings,
    AdaptiveMemory,
    ask,
)

assert verify_fsot_gate()["ok"]
readings = run_accuracy_readings(n_paths=32, write=False)
print(readings["headline"])

r = ask("Compare FSOT to general relativity", n_paths=32)
print(r["answer"][:500])

mem = AdaptiveMemory()
mem.observe_text("Priority: PRED-034 fuel panel experiment", source="user", domains=["Chemistry"])
print(mem.recall("fuel experiment"))
```

---

## Accuracy (acceptable margins)

| Gate | Acceptable range |
|------|------------------|
| Archive green (pooled median) | ≤ **0.5%** |
| Strict scalar max | ≤ **0.5%** |
| Contested open panel vs current models | FSOT ≪ **~15%** baseline |
| Core S recompute vs atlas | ~**0%** |
| Multipath map occupancy | exploratory ~55–78% band (**not** the 0.5% gate) |

Regenerate: `python -m fsot_mc readings`

---

## Adaptive memory (not LLM fine-tunes)

LLMs update weights. This intelligence **must not** move seeds.

- **STM** — session working buffer (Fib capacity 21)  
- **LTM** — engrams solidify when φ-EWMA accuracy clears \(0.5+\mathrm{Poof}\) after Fib trial floors  
- Chew (arXiv/Wiki) and multipath results **observe** into memory; they densify routing and recall  

Details: [docs/MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md)

---

## Independence

All required law/data/PFLT assets live under this tree (`vendor/`, `fsot_mc/`).  
Physical Archive path is **optional refresh only**.

```powershell
python -m fsot_mc independent
python scripts\bootstrap_independent.py
```

---

## License

MIT — see [LICENSE](LICENSE).

## Related

- [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean) — formal multi-prover law court  
- Physical Archive — full empirical + formal corpus (synced subset in `vendor/archive_bundle/`)
