# FSOT Monte Carlo Intelligence

**Simulate the universe under Fluid Spacetime Omni-Theory — discover pathways, physics, and engineering leads.**

| | |
|--|--|
| **Author** | Damian Arthur Palumbo |
| **Version** | 1.2.0 |
| **Authority pin** | **D1D38A** · `free_parameters = 0` |
| **Theory law court** | [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean) |
| **Product** | Universe multipath intelligence (**not** markets) |

> Paradigm: one seed-derived fluid engine; domains are folds; multipath observation histories **are** thought.  
> Seeds never move. Discovery proposes; formal/empirical spine accepts or rejects.

---

## Docs

| Document | Purpose |
|----------|---------|
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | How the system works scientifically |
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | Clone → gate → tests → readings |
| [docs/ACHIEVEMENTS.md](docs/ACHIEVEMENTS.md) | What we achieved and why |
| [docs/MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md) | FSOT-derived STM/LTM adaptive memory |
| [docs/UNIVERSE_INTELLIGENCE_ARCHITECTURE.md](docs/UNIVERSE_INTELLIGENCE_ARCHITECTURE.md) | Full stack architecture |
| [HANDOFF.md](HANDOFF.md) | Maintainer handoff |

---

## Quick start

```powershell
git clone https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence.git
cd FSOT-Monte-Carlo-Intelligence
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/ -q
python -m fsot_mc gate
python -m fsot_mc independent
python -m fsot_mc readings --n-paths 64
python -m fsot_mc ask --think -q "What does multipath emergence mean?"
python -m fsot_mc serve --port 8765
# open http://127.0.0.1:8765/  — neural / Obsidian multi-scale graph UI
```

### Requirements

See [`requirements.txt`](requirements.txt):

- numpy ≥ 1.26  
- pandas ≥ 2.2  
- mpmath ≥ 1.3  
- pytest ≥ 8.3  

Optional: network for live arXiv/Wikipedia (`FSOT_MC_ONLINE=1`); Torch for GPU polar student.

---

## Core commands

```text
python -m fsot_mc gate              # D1D38A authority
python -m fsot_mc independent       # local vendor integrity
python -m fsot_mc atlas | build-atlas
python -m fsot_mc intel --n-paths 128 --with-formal --with-apis
python -m fsot_mc discover
python -m fsot_mc readings          # cross-domain accuracy vs ≤0.5% / 15% baselines
python -m fsot_mc ask | chat        # multipath mind
python -m fsot_mc memory-status     # STM/LTM adaptive memory
python -m fsot_mc graph             # multi-scale connective graph JSON summary
python -m fsot_mc solidify          # chew corpus → LTM
python -m fsot_mc protocols         # experiment protocol cards
python -m fsot_mc serve --port 8765 # full-stack visual UI + API
python -m fsot_mc eyes | relay | formal | realities | apis
```

---

## Visual full stack (v1.0)

Neural connective map × Obsidian second-brain aesthetic:

- **Seeds** (π, e, φ, γ, G) feed **law K** at the hub  
- **Domain folds** on D_eff rings (cluster colors, size ∝ |S|)  
- **Ladder + long-range bridges** as pulsing neural axons  
- **Memory engrams** + **preregistered predictions** as satellites  
- Sidebar: multipath mind ask, accuracy readings, solidify, experiment protocols  

```powershell
python -m fsot_mc serve
# → http://127.0.0.1:8765/
```

API: `/api/graph` `/api/ask` `/api/readings` `/api/memory` `/api/protocols` `/api/solidify` `/api/mc` `/api/tissue/{id}`

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

Apache-2.0 — see [LICENSE](LICENSE).

## Related

- [FSOT-2.1-Lean](https://github.com/dappalumbo91/FSOT-2.1-Lean) — formal multi-prover law court  
- Physical Archive — full empirical + formal corpus (synced subset in `vendor/archive_bundle/`)
