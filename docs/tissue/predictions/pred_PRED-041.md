# PRED-041: transporter_pad_b_receiver_hardware

> **Tissue ID:** `pred_PRED-041` | **Kind:** preregistered prediction  
> **Domain:** `Star_Trek_Transporter_Live_Panel` | **Branch:** `term3.acoustic_bleed`  
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
| FSOT predicted | 0.031159 |
| Unit | pooled_median_error_pct |
| Formula branch | `term3.acoustic_bleed` |
| SOTA baseline | 8.0 |
| SOTA label | Reassembly receiver phase-capture typical modeling gap |
| Discriminant | `within_10pct_of_observed_gap` |

Underlying engine remains \(S=K(T_1+T_2+T_3)\) on the stated branch.

## Results

| Item | Value |
|------|------:|
| Predicted | 0.031159 pooled_median_error_pct |
| Baseline | 8.0 (Reassembly receiver phase-capture typical modeling gap) |
| Registered | 2026-07-15 |

### Notes

Pad B receiver hardware simulator — capture-coil phase conjugate lock coupled to psi_gate_pair two-gate entanglement channel; matter-stream reassembly fidelity.

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
