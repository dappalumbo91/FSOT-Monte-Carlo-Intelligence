# Problem Route: climate paleo

> **Tissue ID:** `intent_climate_paleo` | **Kind:** problem_route intent hub  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** 2026-07-23

## Abstract

Navigator **problem route** linking a scientific intent to a core domain and specialized
depth panels. This is connective tissue for *how questions map into FSOT folds*.

## Ontology

Problem routes are not free-parameter models. They are **routing metadata** from the
Physical Archive domain navigator: keywords → core fold → extension panels with benchmarks.

| Field | Value |
|-------|-------|
| Intent | `climate paleo` |
| Core domain | `Atmospheric_Physics` |
| Keywords | `climate`, `ice core`, `temperature anomaly`, `co2`, `paleo` |
| Panels | `Climate_Science` |

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
| [Atmospheric Physics](domains/Atmospheric_Physics.md) | `problem_route` | `problem_intent` | 0.850 | n/a |
| [Climate Science](domains/Climate_Science.md) | `problem_route` | `problem_intent` | 0.650 | n/a |


## Epistemics

| Tier | `scaffold` routing metadata over measured panels |
| Free parameters | 0 |

## References

- `vendor/archive_bundle/data__fsot_domain_navigator.json` → `problem_routes`
- [../../METHODOLOGY.md](../../METHODOLOGY.md)

---
*FSOT tissue doc · problem route.*
