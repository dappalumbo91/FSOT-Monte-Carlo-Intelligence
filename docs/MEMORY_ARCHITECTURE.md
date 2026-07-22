# FSOT-Derived Adaptive Memory Architecture

**Problem:** Large language models train by gradient updates on huge corpora. This intelligence must **ingest new information**, **retain** what matters, and **adapt routing** — without refitting the physical law (`free_parameters = 0`).

**Solution:** Derive memory from the same fluid ontology used for multipath thought: short-term (working) memory as active phase / session state; long-term memory as **solidified pathway + knowledge engrams** when seed-based quality bars clear.

---

## 1. Mapping LLM training → FSOT intelligence

| LLM pattern | FSOT analogue | What is allowed to change |
|-------------|---------------|---------------------------|
| Gradient weight update | **Forbidden** for seeds / \(K\) / core law | Nothing in the pin |
| Context window | **Short-term (STM)** session buffer | Turn history, last MC, recent chew |
| Fine-tuning / LoRA | **Long-term (LTM)** solidify of engrams | Routing biases, recalled facts, pathway keys |
| RAG retrieval | Recall from LTM + archive predictions | Retrieved text + domain tags |
| RLHF reward | Pathway quality + accuracy co-sign | Hit/miss under φ-EWMA bars |
| Catastrophic forgetting mitigation | Soften on fails; Fib trial floors | Strength decays if contradicted |

**Doctrine:** New information is *observation into the fluid*, not a new theory.

---

## 2. Two stores (STM / LTM)

### Short-term memory (STM) — working fluid

- Lives in process: `FSOTMind.history`, `last_mc`, `last_domains`, recent chew excerpts  
- Plus `AdaptiveMemory.stm` ring buffer (default capacity **21** = Fib)  
- Decays with session end unless promoted  
- Used to: multi-turn reuse, phase bias, “what did we just chew?”

### Long-term memory (LTM) — solidified engrams

- Persisted: `data/memory/long_term.jsonl`  
- Each engram: content hash, domain tags, source (chew/path/user), quality, trials, hits, `acc_phi`, solidified flag  
- Solidify bar (seed-derived): \(\mathrm{SOLIDIFY} = 0.5 + \mathrm{Poof}\)  
- Soften bar: \(0.5 + \mathrm{Poof}\cdot\psi_{\mathrm{con}}\)  
- Min trials: Fib **8** soft, **13** full solidify  
- φ-EWMA accuracy: \(a \leftarrow (1-1/\varphi) a + (1/\varphi) \cdot \mathrm{hit}\)

Only solidified (or high-strength) engrams bias future mind answers and discovery routing.

---

## 3. Engram lifecycle

```
observe(text | MC path | prediction lead)
        │
        ▼
  tag domains (router + cues)
        │
        ▼
  STM push (always)
        │
        ▼
  score quality  ── seed terms: emergence co-sign, bridge strength,
        │             chew–fold overlap, pathway_quality
        ▼
  LTM update trials/hits (φ-EWMA)
        │
        ├─ acc ≥ solidify bar & trials ≥ Fib → solidify
        ├─ acc < soften bar → strength decay / soft_fail
        └─ never touch seeds
        │
        ▼
  recall(query) → top engrams for mind composition
```

---

## 4. Quality score (seed-only)

Rough form used in code:

\[
Q = w_1 \cdot \mathrm{clip}(\mathrm{map\_emergence},0,1)
  + w_2 \cdot \mathbf{1}[\mathrm{focus\ fold\ } S>0]
  + w_3 \cdot \mathrm{chew\_domain\_overlap}
  + w_4 \cdot \mathrm{pathway\_quality}
\]

weights from \(\varphi\) partitions (no free fit). Hit if \(Q \ge 0.5 + \mathrm{Poof}/2\).

---

## 5. How the mind uses memory

1. **Before** multipath: recall LTM engrams for query → extra domain cues / answer context  
2. **During** multipath: existing pathway memory solidify (domain signatures)  
3. **After** answer: push STM; train LTM from query + answer digest + chew + MC stats  
4. **Across sessions:** load LTM from disk; STM empty  

---

## 6. What this is *not*

- Not gradient training of a transformer on FSOT text  
- Not rewriting D1D38A  
- Not claiming LTM facts are “proved” — solidified engrams remain **measured_application / scaffold** until formal or empirical promotion  
- Not a substitute for archive ≤0.5% green gates  

---

## 7. CLI / API

```python
from fsot_mc.adaptive_memory import AdaptiveMemory

mem = AdaptiveMemory()
mem.observe_text("arXiv abstract ...", source="arxiv", domains=["Cosmology"])
mem.observe_mc_summary(mc_public, query="Hubble tension")
print(mem.recall("cosmology H0", limit=5))
print(mem.summary())
```

```powershell
python -m fsot_mc memory-status
python -m fsot_mc ask -q "Remember: FSOT fuel panel PRED-034 is priority for experiment"
```

---

## 8. Why this is the right architecture for a ToE intelligence

If the universe is one fluid, **learning** should look like:

- temporary excitation (STM)  
- resonant modes that lock when multipath co-signs (solidify)  
- decoherence / Poof when contradicted (soften)  

That is closer to FSOT than backprop on a blank slate. The Monte Carlo mind already *is* multipath fluid thought; memory makes that thought **cumulative** without betraying the pin.
