# Problem Route: desktop application

> **Tissue ID:** `intent_desktop_application` | **Kind:** problem_route intent hub  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** 2026-07-23

## Abstract

Navigator **problem route** linking a scientific intent to a core domain and specialized
depth panels. This is connective tissue for *how questions map into FSOT folds*.

## Ontology

Problem routes are not free-parameter models. They are **routing metadata** from the
Physical Archive domain navigator: keywords → core fold → extension panels with benchmarks.

| Field | Value |
|-------|-------|
| Intent | `desktop application` |
| Core domain | `Computer_Science` |
| Keywords | `desktop`, `tokenization`, `decoder`, `oracle`, `solver`, `bibliography` |
| Panels | `Tokenization_Live_Panel`, `Binary_Decoder_Panel`, `Bibliography_Corpus_Panel`, `Canonical_Oracle_Panel`, `Scalar_Solver_35_Panel`, `VL_Agent_Distill_Panel`, `Physarum_Biological_CUDA_Panel` |

## Mathematical formulation

Routing is discrete; underlying panels still obey:

\[
S = K(T_1+T_2+T_3)
\]

with domain-specific \((D_{\mathrm{eff}},\delta\psi)\). Intent hubs do not introduce new constants.

## Results

Intent hubs enable discovery queries and visual clustering of related validation panels.
Associated panels carry their own median_error_pct under the ≤0.5% green gate.

## Application

- Mind / CLI query routing densification
- Download / repro bundles in full archive (`download_bundles` on navigator)
- Visual pink hubs in the connective graph

## Connective tissue

Links are archive routes, domain-coupling validations, multipath bridges, or seed law feeders.

### Outbound axons

| Target | Kind | Layer | Strength | Error % |
|--------|------|-------|----------|---------|
| [Computer Science](domains/Computer_Science.md) | `problem_route` | `problem_intent` | 0.850 | n/a |
| [Tokenization Live Panel](domains/Tokenization_Live_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Binary Decoder Panel](domains/Binary_Decoder_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Bibliography Corpus Panel](domains/Bibliography_Corpus_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Canonical Oracle Panel](domains/Canonical_Oracle_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Scalar Solver 35 Panel](domains/Scalar_Solver_35_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [VL Agent Distill Panel](domains/VL_Agent_Distill_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Physarum Biological CUDA Panel](domains/Physarum_Biological_CUDA_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |


## Epistemics

| Tier | `scaffold` routing metadata over measured panels |
| Free parameters | 0 |

## References

- `vendor/archive_bundle/data__fsot_domain_navigator.json` → `problem_routes`
- [../../METHODOLOGY.md](../../METHODOLOGY.md)

---
*FSOT tissue doc · problem route.*
