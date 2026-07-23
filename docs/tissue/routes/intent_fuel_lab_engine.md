# Problem Route: fuel lab engine

> **Tissue ID:** `intent_fuel_lab_engine` | **Kind:** problem_route intent hub  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** 2026-07-23

## Abstract

Navigator **problem route** linking a scientific intent to a core domain and specialized
depth panels. This is connective tissue for *how questions map into FSOT folds*.

## Ontology

Problem routes are not free-parameter models. They are **routing metadata** from the
Physical Archive domain navigator: keywords → core fold → extension panels with benchmarks.

| Field | Value |
|-------|-------|
| Intent | `fuel lab engine` |
| Core domain | `Thermodynamics` |
| Keywords | `fuel`, `engine`, `lhv`, `thermodynamics`, `hemp`, `biodiesel` |
| Panels | `Fuel_Lab_Live_Panel`, `Fuel_Thermochemistry_Public_Anchors`, `Published_Fuel_Property_Panel` |

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
| [Thermodynamics](domains/Thermodynamics.md) | `problem_route` | `problem_intent` | 0.850 | n/a |
| [Fuel Lab Live Panel](domains/Fuel_Lab_Live_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Fuel Thermochemistry Public Anchors](domains/Fuel_Thermochemistry_Public_Anchors.md) | `problem_route` | `problem_intent` | 0.650 | n/a |
| [Published Fuel Property Panel](domains/Published_Fuel_Property_Panel.md) | `problem_route` | `problem_intent` | 0.650 | n/a |


## Epistemics

| Tier | `scaffold` routing metadata over measured panels |
| Free parameters | 0 |

## References

- `vendor/archive_bundle/data__fsot_domain_navigator.json` → `problem_routes`
- [../../METHODOLOGY.md](../../METHODOLOGY.md)

---
*FSOT tissue doc · problem route.*
