# Handoff — FSOT Universe Monte Carlo Intelligence

**Workspace:** `C:\Users\damia\Desktop\FSOT-Monte-Carlo-Intelligence`  
**Version:** 1.5.0  
**Mode:** **Independent** — no I:/D:/Desktop required at runtime  
**Chat weights (Hugging Face):** https://huggingface.co/dappalumbo91/FSOT-Qwen2.5-7B-Instruct  
**GitHub code:** https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence

## Independence

```powershell
python -m fsot_mc independent
python scripts\bootstrap_independent.py
```

All checks must be OK under `vendor/` + `fsot_mc/` + `data/realities_snapshot/`.

| Local tree | Contents |
|------------|----------|
| `fsot_mc/compute_authority.py` | Law pin D1D38A |
| `fsot_mc/full_atlas.json` | 402 domains |
| `vendor/archive_bundle/` | Navigator, certificates, cross-proof, benchmarks |
| `vendor/pflt/` | Multilayer vision + PFLT core + relay deps |
| `vendor/linguistics/` | Derivations + targets |
| `data/realities_snapshot/` | Offline Realities runtime |

External paths are **optional refresh only** (`scripts/sync_archive_bundle.py` if I: present).

## CLI

```text
python -m fsot_mc independent
python -m fsot_mc intel --n-paths 128 --with-formal --with-apis --with-realities
python -m fsot_mc eyes
python -m fsot_mc relay
python -m fsot_mc polar-train --n-paths 64
python -m fsot_mc formal
python -m fsot_mc realities
python -m fsot_mc apis
python -m fsot_mc download-qwen   # or: python scripts/download_qwen25_instruct.py
python -m fsot_mc docs-index --rebuild-index
python -m fsot_mc chat -q "What does the Biology thesis say about S?"
python -m fsot_mc ask --think -q "What does the multipath emergence percentage mean for biology?"
python -m fsot_mc ask --chew --online -q "Compare FSOT to general relativity"
python -m fsot_mc ask -q "What FSOT fuels should we experiment on?"
python -m fsot_mc readings --n-paths 64
python -m fsot_mc accuracy --json
python -m fsot_mc serve --port 8765
python -m fsot_mc graph
python -m fsot_mc solidify
python -m fsot_mc protocols
```

## Visual stack (v1.0)

- Frontend: `frontend/` (canvas neural graph + side panels)
- API: `python -m fsot_mc serve` → `http://127.0.0.1:8765/`
- Graph model: seeds → K → domains → bridges → memory → predictions
- Aesthetic: Obsidian second-brain × neural growth connective tissue

## Accuracy / margins (v0.9)

- Archive green gate: **≤0.5%** pooled median (405 domains in local audit)
- Contested open panel: FSOT vs ~**15%** current-model baseline
- Core fold recompute: engine vs atlas S_canonical
- Multipath ~60–70%: co-emergence discovery metric (**not** the 0.5% gate)
- Readings export: `data/exports/accuracy_readings_latest.json`

**GitHub:** create/push repo only after user reviews readings.

## Mind / ToE doctrine (v0.8)

- **Thinking = multipath MC** under FSOT law (not free invention).
- **~69% dual frame:** operational map co-emergence = mean (folds S>0)/n; paradigm = natural complexity/energy occupancy window for life folds (not Bayesian P(Earth life)).
- **Biology** is a lawful intermediate fold (S≈+0.5, D_eff≈12) on the same fluid as cosmos.
- **arXiv / Wikipedia chew** via `--chew` or auto on science queries; live with `FSOT_MC_ONLINE=1` / `--online`.
- **177 preregistered archive predictions** fused into discovery + mind (fuels, H0, devices…).
- Engineering leads are ToE designs with discriminants — experiment still closes the loop.

## Gap refinements (v1.5 — claim-critical)

| Gap | Status | How |
|-----|--------|-----|
| Full OAI dump | **in progress** | `python -m fsot_mc literature-index --max-papers 0` (full dump, no category filter). Live index under `data/literature/arxiv_fts.sqlite`. |
| Formal auto-promote | **done** | `scientific-audit` auto-feeds obligations; also `audit-promote`. Soft court ≠ Lean-proved. |
| Coupling edge LOD | **done** | Compact tissue ~15k edges (base/dense tiers); zoom ≥0.7 densifies mesh. |
| Flip-hotspot protocols | **done** | `flip-protocols` → `docs/FLIP_HOTSPOT_PROTOCOLS.md` |
| PRED bench closure | **done** | `pred-bench` ledger + kill/pass criteria; lab still closes status. |

```powershell
python -m fsot_mc literature-index --max-papers 0 --arxiv-only   # full OAI (long)
python -m fsot_mc scientific-audit                                 # + auto-promote
python -m fsot_mc audit-promote                                    # re-feed from latest
python -m fsot_mc flip-protocols --n-paths 96
python -m fsot_mc pred-bench
python -m fsot_mc pred-bench --set PRED-001 --status pass --measured 70.8 --source "lab.md"
```

## Next deepening (ongoing)

- Finish full OAI index → literature cross-ref on all cores  
- Lab-close PRED ledger entries (status pass/kill with evidence)  
- Torch/GPU polar student (`FSOT_MC_USE_TORCH=1`)  
- Live Realities kernel optional alongside snapshot

## Doctrine

Python discovers · π-ring sees · vendored PFLT senses · Lean judges batch · local vendor remembers · APIs only feed · seeds never move · FSOT is ToE.
