# Local Literature Corpus — arXiv + Simple Wikipedia → FSOT

Hook offline research dumps into the multipath mind so reasoning can **cross-reference verified literature** with FSOT connective tissue (domain folds, S, green-gate).

## Data sources

| Corpus | Default path | Env override |
|--------|--------------|--------------|
| arXiv OAI snapshot (JSONL) | `D:\training data\arXiv Dataset\arxiv-metadata-oai-snapshot.json` (~4.8 GB) | `FSOT_MC_ARXIV_JSON` |
| Simple English Wikipedia | `D:\training data\nlp\simple-wiki\` | `FSOT_MC_WIKI_ROOT` |

Live network APIs remain optional (`FSOT_MC_ONLINE=1`); **local index is preferred**.

## What it does

1. **Index** papers/articles into SQLite FTS5 under `data/literature/`
2. **Map** arXiv categories → FSOT domains (`gr-qc` → Cosmology/Quantum_Gravity, `quant-ph` → Quantum_Mechanics, …)
3. **Cross-ref** each hit with fold scalars S, D_eff, regime from the seed engine
4. **Chew** into the mind as observation stream (seeds never move)
5. **Solidify** optional LTM via existing adaptive memory / `solidify`

## CLI

```powershell
# Status (paths + indexed counts)
python -m fsot_mc literature-status

# Build indexes (FSOT-priority arXiv categories, default 100k papers + 50k wiki)
python -m fsot_mc literature-index --max-papers 100000 --max-articles 50000

# Full arXiv dump (slow — set max-papers 0)
python -m fsot_mc literature-index --max-papers 0 --rebuild-index

# Search + FSOT cross-ref
python -m fsot_mc literature-search -q "Hubble tension dual anchor dark energy"

# Mind auto-uses local corpus when index exists
python -m fsot_mc ask --chew -q "quantum entanglement and fluid spacetime"
```

## API

- `GET /api/literature/status`
- `GET /api/literature?q=quantum+gravity`

## Epistemics

- Literature is **observation**, not authority over D1D38A.
- Cross-ref answers: “this paper’s category co-signs these FSOT folds with S=…”
- Panel green-gate (≤0.5%) remains the empirical bar for FSOT claims.

## Category → domain (sample)

| arXiv | FSOT folds |
|-------|------------|
| gr-qc | Cosmology, Quantum_Gravity, Astrophysics |
| astro-ph.CO | Cosmology, Astrophysics |
| quant-ph | Quantum_Mechanics, Quantum_Optics, Quantum_Computing |
| hep-th / hep-ph | Particle_Physics, High_Energy_Physics, Quantum_Gravity |
| q-bio.NC | Neuroscience, Biology |
| cond-mat.supr-con | Condensed_Matter |
| physics.flu-dyn | Fluid_Dynamics |

See `fsot_mc/literature_corpus.py` for the full map.
