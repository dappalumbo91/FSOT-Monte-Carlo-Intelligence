# PRED-034: fsot_designed_fuel_thermochemistry_panel

> **Tissue ID:** `pred_PRED-034` | **Kind:** preregistered prediction  
> **Domain:** `Fuel_Lab_Live_Panel` | **Branch:** `term1.coherence_efficiency`  
> **Authority:** D1D38A | **free_parameters:** 0 | **Generated:** 2026-07-23

## Abstract

Preregistered FSOT prediction with explicit SOTA baseline and **kill discriminant**.
Engineering / observational designs are ToE-derived leads — experiment still closes the loop.

## Ontology

Predictions are not post-hoc curve fits. They state a seed-engine value, a comparison baseline,
and a pre-registered discriminant (falsification criterion).

## Mathematical formulation

| Field | Value |
|-------|------:|
| FSOT predicted | 0.039349 |
| Unit | pooled_median_error_pct |
| Formula branch | `term1.coherence_efficiency` |
| SOTA baseline | 8.0 |
| SOTA label | Desktop engine simulator typical fuel-property error |
| Discriminant | `within_10pct_of_observed_gap` |

Underlying engine remains \(S=K(T_1+T_2+T_3)\) on the stated branch.

## Results

| Item | Value |
|------|------:|
| Predicted | 0.039349 pooled_median_error_pct |
| Baseline | 8.0 (Desktop engine simulator typical fuel-property error) |
| Registered | 2026-07-15 |

### Notes

Seven FSOT-designed alternative fuels (hemp grounded/advanced, algae biodiesel, mushroom ester, green hydrogen, optimax, bio_spark) — thermochemistry + Prius engine simulator outputs vs seed-scalar predictions; novel molecular states not pre-existing in literature; gasoline baseline for comparison only.

## Application

- Lab / desktop experiment protocols (`python -m fsot_mc protocols`)
- Engineering discovery (fuels, devices, cosmology anchors)
- Visual gold nodes on the connective graph

### Pass / kill

- **Pass:** discriminant satisfied; pin D1D38A verified; no free-parameter retune
- **Kill:** discriminant fails; or requires free fit to match data

## Connective tissue

Links are archive routes, domain-coupling validations, multipath bridges, or seed law feeders.

_No compact-graph edges recorded for this node (may still couple via full 39k raw matrix)._


## Epistemics

| Tier | `preregistered_design` |
| Free parameters | 0 |
| Closure | physical experiment / measurement |

## References

- `vendor/archive_bundle/data__preregistered_predictions_manifest.yaml`
- Experiment protocols API / CLI
- [../../ACHIEVEMENTS.md](../../ACHIEVEMENTS.md)

---
*FSOT tissue doc · preregistered prediction.*
