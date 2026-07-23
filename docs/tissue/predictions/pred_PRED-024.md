# PRED-024: h0_dual_anchor_bubble_bleed

> **Tissue ID:** `pred_PRED-024` | **Kind:** preregistered prediction  
> **Domain:** `Hubble_Dark_Sector_Crosswalk` | **Branch:** `term3.acoustic_bleed`  
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
| FSOT predicted | 72.1 |
| Unit | km/s/Mpc |
| Formula branch | `term3.acoustic_bleed` |
| SOTA baseline | 67.4 |
| SOTA label | Planck CMB H0 |
| Discriminant | `fsot_exceeds_sota_by_0.4` |

Underlying engine remains \(S=K(T_1+T_2+T_3)\) on the stated branch.

## Results

| Item | Value |
|------|------:|
| Predicted | 72.1 km/s/Mpc |
| Baseline | 67.4 (Planck CMB H0) |
| Registered | 2026-07-10 |

### Notes

_No extended note in manifest._

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
