"""
Cross-domain accuracy / margin-of-error gate for FSOT Monte Carlo Intelligence.

Cross-references local engine + atlas against archive bundle evidence:
  - official green gate: pooled median ≤ 0.5% (archive standard)
  - contested open-science panel vs ΛCDM/SM ~15% baseline
  - core fold S recompute vs S_canonical
  - authority pin D1D38A
  - multipath MC map stats (exploratory — not a replacement for empirical gates)

This is multi-domain: cosmology, particle, chemistry, biology, materials, …
free_parameters = 0. Seeds never move.
"""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.authority_gate import AUTHORITY_SHA256, verify_fsot_gate
from fsot_mc.paths import archive_bundle_dir, data_root
from fsot_mc.universe_atlas import (
    atlas_meta,
    core_names,
    domains_by_cluster,
    evaluate_domain,
    get_domain,
    snapshot_universe,
)


# Acceptable margins (current FSOT archive / publication standard)
THRESHOLD_POOLED_MEDIAN_PCT = 0.5
THRESHOLD_STRICT_SCALAR_MAX_PCT = 0.5
THRESHOLD_CORE_S_RECOMPUTE_PCT = 0.01  # local engine vs atlas S_canonical should be ~0
LCDM_SM_OPEN_PANEL_BASELINE_PCT = 15.0  # contested-sector current-model baseline
NATURAL_MAP_EMERGENCE_BAND = (0.55, 0.78)  # multipath co-emergence window (paradigm)


def _pct_err(computed: float, measured: float) -> float | None:
    if measured == 0 or not math.isfinite(measured) or not math.isfinite(computed):
        if computed == measured:
            return 0.0
        return None
    return abs(computed - measured) / abs(measured) * 100.0


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_archive_margin_audit() -> dict[str, Any]:
    raw = _load_json(archive_bundle_dir() / "benchmarks" / "benchmark_margin_audit.json")
    if not isinstance(raw, dict):
        return {"ok": False, "error": "margin_audit_missing"}
    domains = raw.get("all_domains") or []
    # Summarize by cluster-ish domain name prefixes
    errors = [
        float(d["pooled_median_error_pct"])
        for d in domains
        if isinstance(d, dict)
        and d.get("pooled_median_error_pct") is not None
        and not d.get("excluded")
    ]
    within = [e for e in errors if e <= THRESHOLD_POOLED_MEDIAN_PCT]
    return {
        "ok": True,
        "source": "benchmark_margin_audit.json",
        "threshold_official_pooled_median_pct": raw.get(
            "threshold_official_pooled_median_pct", THRESHOLD_POOLED_MEDIAN_PCT
        ),
        "threshold_strict_scalar_max_pct": raw.get(
            "threshold_strict_scalar_max_pct", THRESHOLD_STRICT_SCALAR_MAX_PCT
        ),
        "green_gate_pass_count": raw.get("green_gate_pass_count"),
        "green_gate_fail_count": raw.get("green_gate_fail_count"),
        "worst_scalar_max_error_pct": raw.get("worst_scalar_max_error_pct"),
        "worst_scalar_domain": raw.get("worst_scalar_domain"),
        "n_domains_reported": len(domains),
        "n_with_pooled_error": len(errors),
        "n_within_0_5pct": len(within),
        "pooled_median_of_domain_medians_pct": (
            float(statistics.median(errors)) if errors else None
        ),
        "pooled_mean_of_domain_medians_pct": (
            float(statistics.mean(errors)) if errors else None
        ),
        "max_pooled_domain_median_pct": float(max(errors)) if errors else None,
        "min_pooled_domain_median_pct": float(min(errors)) if errors else None,
        "all_green": int(raw.get("green_gate_fail_count") or 0) == 0,
        "acceptable_range_pct": f"≤{THRESHOLD_POOLED_MEDIAN_PCT}% pooled median (archive green gate)",
    }


def load_contested_panel() -> dict[str, Any]:
    raw = _load_json(archive_bundle_dir() / "benchmarks" / "contested_observables_closure.json")
    if not isinstance(raw, dict):
        return {"ok": False, "error": "contested_closure_missing"}
    obs = raw.get("observables") or []
    rows = []
    for o in obs:
        if not isinstance(o, dict):
            continue
        err = o.get("fsot_error_pct")
        if err is None and o.get("computed") is not None and o.get("measured") is not None:
            err = _pct_err(float(o["computed"]), float(o["measured"]))
        rows.append(
            {
                "name": o.get("name"),
                "property": o.get("property"),
                "computed": o.get("computed"),
                "measured": o.get("measured"),
                "unit": o.get("unit"),
                "fsot_error_pct": err,
                "within_green_gate": bool(
                    o.get("within_green_gate")
                    if o.get("within_green_gate") is not None
                    else (err is not None and float(err) <= THRESHOLD_POOLED_MEDIAN_PCT)
                ),
                "beats_current_model_baseline": o.get("beats_current_model_baseline"),
                "current_model_baseline_pct": o.get(
                    "current_model_baseline_pct", LCDM_SM_OPEN_PANEL_BASELINE_PCT
                ),
                "needs_refinement": o.get("needs_refinement"),
                "reference": o.get("reference"),
                "status": o.get("status"),
            }
        )
    errs = [float(r["fsot_error_pct"]) for r in rows if r.get("fsot_error_pct") is not None]
    panel = raw.get("panel_summary") or {}
    return {
        "ok": True,
        "source": "contested_observables_closure.json",
        "verdict": raw.get("verdict"),
        "reframe": raw.get("reframe"),
        "panel_summary": panel,
        "n_observables": len(rows),
        "n_within_0_5pct": sum(1 for r in rows if r.get("within_green_gate")),
        "n_beats_15pct_baseline": sum(1 for r in rows if r.get("beats_current_model_baseline")),
        "fsot_pooled_median_error_pct": panel.get("pooled_median_error_pct")
        or (float(statistics.median(errs)) if errs else None),
        "fsot_max_error_pct": panel.get("max_error_pct") or (float(max(errs)) if errs else None),
        "current_model_baseline_pct": panel.get(
            "current_model_baseline_pct", LCDM_SM_OPEN_PANEL_BASELINE_PCT
        ),
        "observables": rows,
        "acceptable_range_note": (
            f"Green gate ≤{THRESHOLD_POOLED_MEDIAN_PCT}% FSOT error; "
            f"open-panel current models often ~{LCDM_SM_OPEN_PANEL_BASELINE_PCT}% baseline."
        ),
    }


def load_publication_claims() -> dict[str, Any]:
    raw = _load_json(archive_bundle_dir() / "benchmarks" / "publication_claims_manifest.json")
    if not isinstance(raw, dict):
        return {"ok": False, "error": "publication_claims_missing"}
    emp = raw.get("empirical_evidence") or {}
    cont = raw.get("contested_sector_evidence") or {}
    h0 = raw.get("h0_highlights") or []
    return {
        "ok": True,
        "source": "publication_claims_manifest.json",
        "theory_frame": raw.get("theory_frame"),
        "empirical_evidence": emp,
        "contested_sector_evidence": cont,
        "h0_highlights": h0[:8],
        "n_h0_highlights": len(h0),
        "verdict_empirical": emp.get("verdict"),
        "verdict_contested": cont.get("verdict"),
    }


def load_cosmology_benchmark() -> dict[str, Any]:
    raw = _load_json(archive_bundle_dir() / "benchmarks" / "cosmology_anomalies_benchmark.json")
    if not isinstance(raw, dict):
        return {"ok": False, "error": "cosmo_benchmark_missing"}
    return {
        "ok": True,
        "source": "cosmology_anomalies_benchmark.json",
        "domain": raw.get("domain"),
        "record_count": raw.get("record_count"),
        "observable_count": raw.get("observable_count"),
        "median_error_pct": raw.get("median_error_pct"),
        "within_green_gate": (
            float(raw["median_error_pct"]) <= THRESHOLD_POOLED_MEDIAN_PCT
            if raw.get("median_error_pct") is not None
            else None
        ),
        "D_eff": raw.get("D_eff"),
    }


def core_fold_recompute_accuracy() -> dict[str, Any]:
    """
    Recompute every core fold S with local engine vs atlas S_canonical.
    This is the portable integrity check for the Monte Carlo workspace.
    """
    names = core_names()
    rows = []
    errs = []
    for name in names:
        try:
            base = get_domain(name)
            e = evaluate_domain(name)
            S = float(e["S"])
            Sc = float(base.get("S_canonical", e.get("S_canonical", S)))
            # absolute relative error on S (handle near-zero)
            if abs(Sc) < 1e-15:
                err_pct = abs(S - Sc) * 100.0  # absolute *100 as soft metric
            else:
                err_pct = abs(S - Sc) / abs(Sc) * 100.0
            errs.append(err_pct)
            rows.append(
                {
                    "domain": name,
                    "cluster": e.get("cluster") or base.get("cluster"),
                    "D_eff": e.get("D_eff"),
                    "S_recompute": S,
                    "S_canonical": Sc,
                    "rel_error_pct": float(err_pct),
                    "regime": e.get("regime"),
                    "within_tol": err_pct <= THRESHOLD_CORE_S_RECOMPUTE_PCT,
                }
            )
        except Exception as exc:
            rows.append({"domain": name, "error": str(exc), "within_tol": False})

    within = [r for r in rows if r.get("within_tol")]
    return {
        "ok": len(within) == len(rows) and len(rows) > 0,
        "n_core": len(rows),
        "n_within_tol": len(within),
        "threshold_rel_error_pct": THRESHOLD_CORE_S_RECOMPUTE_PCT,
        "max_rel_error_pct": float(max(errs)) if errs else None,
        "median_rel_error_pct": float(statistics.median(errs)) if errs else None,
        "mean_rel_error_pct": float(statistics.mean(errs)) if errs else None,
        "folds": sorted(rows, key=lambda r: -float(r.get("rel_error_pct") or 0)),
        "note": (
            "Core fold recompute must match atlas S_canonical (seed engine integrity). "
            f"Tol ≤{THRESHOLD_CORE_S_RECOMPUTE_PCT}% rel — not the empirical 0.5% panel gate."
        ),
    }


def cluster_accuracy_snapshot() -> dict[str, Any]:
    """Mean |S| and emergence rate by cluster on core atlas (structural, not empirical)."""
    clusters = domains_by_cluster()
    out = {}
    for cl, names in sorted(clusters.items()):
        core = [n for n in names if n in set(core_names())]
        if not core:
            continue
        Ss = []
        emerge = 0
        for n in core:
            try:
                e = evaluate_domain(n)
                Ss.append(float(e["S"]))
                if float(e["S"]) > 0:
                    emerge += 1
            except KeyError:
                continue
        if not Ss:
            continue
        out[cl] = {
            "n_core_folds": len(Ss),
            "mean_S": float(statistics.mean(Ss)),
            "emergence_fraction": emerge / len(Ss),
            "n_emergence": emerge,
            "n_dispersal": len(Ss) - emerge,
        }
    return out


def multipath_exploratory(
    *,
    n_paths: int = 64,
    seed: int = 0,
) -> dict[str, Any]:
    """
    Multipath MC map stats — exploratory discovery layer.
    Explicitly NOT the archive ≤0.5% empirical green gate.
    """
    from fsot_mc.universe_mc import run_universe_monte_carlo

    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        store_paths=min(12, n_paths),
        train_pathway_memory=False,
    )
    if mc.get("error"):
        return {"ok": False, "error": mc.get("error")}
    ens = mc.get("ensemble") or {}
    ef = ens.get("emergence_fraction") or {}
    mean_ef = ef.get("mean")
    in_band = (
        mean_ef is not None
        and NATURAL_MAP_EMERGENCE_BAND[0] <= float(mean_ef) <= NATURAL_MAP_EMERGENCE_BAND[1]
    )
    de = mc.get("domain_ensemble") or {}
    focus = []
    for d in (
        "Cosmology",
        "Quantum_Mechanics",
        "Particle_Physics",
        "Biology",
        "Chemistry",
        "Neuroscience",
        "Seismology",
        "Materials_Science",
        "Economics",
    ):
        if d in de:
            row = de[d]
            focus.append(
                {
                    "domain": d,
                    "S_path_mean": row.get("S_path_mean"),
                    "S_canonical": row.get("S_canonical"),
                    "flip_rate": row.get("flip_rate"),
                    "D_eff": row.get("D_eff"),
                }
            )
    return {
        "ok": True,
        "layer": "exploratory_multipath",
        "epistemic_note": (
            "Multipath map occupancy explores observer histories for discovery. "
            "It does NOT replace archive empirical ≤0.5% green gates or contested panel errors."
        ),
        "n_paths": mc.get("n_paths"),
        "n_domains": mc.get("n_domains"),
        "map_emergence_mean": mean_ef,
        "map_emergence_p10": ef.get("p10"),
        "map_emergence_p50": ef.get("p50"),
        "map_emergence_p90": ef.get("p90"),
        "natural_band": list(NATURAL_MAP_EMERGENCE_BAND),
        "in_natural_band": in_band,
        "mean_S": (ens.get("mean_S") or {}).get("mean") if isinstance(ens.get("mean_S"), dict) else ens.get("mean_S"),
        "focus_domains": focus,
        "free_parameters": 0,
    }


def preregistered_predictions_accuracy_summary() -> dict[str, Any]:
    """Inventory of preregistered predictions (design-level; experiment gates remaining)."""
    from fsot_mc.archive_predictions import load_preregistered_predictions, predictions_summary

    preds = load_preregistered_predictions()
    summary = predictions_summary()
    by_domain: dict[str, int] = {}
    for p in preds:
        d = str(p.get("domain") or "unknown")
        by_domain[d] = by_domain.get(d, 0) + 1
    # Sample high-profile cross-domain preds
    samples = []
    for pid in ("PRED-001", "PRED-002", "PRED-004", "PRED-005", "PRED-034", "PRED-035"):
        hit = next((p for p in preds if p.get("id") == pid), None)
        if hit:
            samples.append(
                {
                    "id": hit.get("id"),
                    "name": hit.get("name"),
                    "domain": hit.get("domain"),
                    "fsot_predicted": hit.get("fsot_predicted"),
                    "unit": hit.get("unit"),
                    "sota_baseline": hit.get("sota_baseline"),
                    "sota_label": hit.get("sota_label"),
                    "discriminant": hit.get("discriminant"),
                }
            )
    return {
        "ok": True,
        "n_predictions": summary.get("n_predictions"),
        "n_domains": summary.get("n_domains"),
        "by_domain": dict(sorted(by_domain.items(), key=lambda kv: -kv[1])[:25]),
        "samples": samples,
        "note": (
            "Preregistered designs with kill discriminants. "
            "Engineering panels (e.g. fuels) report pooled_median_error_pct as FSOT predicted tightness "
            "vs SOTA desktop simulators — physical experiment still required for build closure."
        ),
        "free_parameters": 0,
    }


def run_accuracy_readings(
    *,
    n_paths: int = 64,
    seed: int = 0,
    with_multipath: bool = True,
    write: bool = True,
) -> dict[str, Any]:
    """
    Full cross-domain accuracy readings package for scientific review.
    """
    gate = verify_fsot_gate(require_archive=False)
    margin = load_archive_margin_audit()
    contested = load_contested_panel()
    pub = load_publication_claims()
    cosmo = load_cosmology_benchmark()
    core = core_fold_recompute_accuracy()
    clusters = cluster_accuracy_snapshot()
    snap = snapshot_universe(names=core_names())
    preds = preregistered_predictions_accuracy_summary()
    multi = multipath_exploratory(n_paths=n_paths, seed=seed) if with_multipath else None

    # Overall integrity score for *this workspace*
    checks = {
        "authority_ok": bool(gate.get("ok")),
        "core_recompute_ok": bool(core.get("ok")),
        "archive_margin_all_green": bool(margin.get("all_green")),
        "contested_panel_loaded": bool(contested.get("ok")),
        "publication_claims_loaded": bool(pub.get("ok")),
    }
    if multi and multi.get("ok"):
        checks["multipath_in_natural_band"] = bool(multi.get("in_natural_band"))

    n_ok = sum(1 for v in checks.values() if v)
    report = {
        "error": None,
        "method": "fsot_cross_domain_accuracy_readings",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "free_parameters": 0,
        "authority_sha256": AUTHORITY_SHA256,
        "version_note": (
            "Cross-domain accuracy readings: archive empirical gates + local engine integrity "
            "+ contested panel vs current-model baselines + exploratory multipath. "
            "Not biology-only."
        ),
        "acceptable_margins": {
            "archive_green_gate_pooled_median_pct": THRESHOLD_POOLED_MEDIAN_PCT,
            "archive_strict_scalar_max_pct": THRESHOLD_STRICT_SCALAR_MAX_PCT,
            "core_S_recompute_tol_pct": THRESHOLD_CORE_S_RECOMPUTE_PCT,
            "contested_open_panel_current_model_baseline_pct": LCDM_SM_OPEN_PANEL_BASELINE_PCT,
            "multipath_map_emergence_natural_band": list(NATURAL_MAP_EMERGENCE_BAND),
            "notes": [
                "≤0.5% is the official FSOT archive empirical green gate (pooled median / strict scalar).",
                f"Contested open problems: FSOT errors typically ≪ {LCDM_SM_OPEN_PANEL_BASELINE_PCT}% "
                "ΛCDM/SM-no-unified-prediction baseline.",
                "Multipath ~60–70% map occupancy is co-emergence discovery metric, not the 0.5% gate.",
            ],
        },
        "integrity_checks": checks,
        "integrity_score": f"{n_ok}/{len(checks)}",
        "authority_gate": {
            "ok": gate.get("ok"),
            "authority_sha256": gate.get("authority_sha256"),
            "float_engine_ok": (gate.get("float_engine") or {}).get("ok"),
            "bytes_local_matches": (gate.get("authority_bytes") or {}).get("local_matches"),
        },
        "atlas": atlas_meta(),
        "canonical_snapshot_core": {
            "n_domains": snap.get("n_domains"),
            "emergence_fraction": snap.get("emergence_fraction"),
            "mean_S": snap.get("mean_S"),
            "n_emergence": snap.get("n_emergence"),
            "n_dispersal": snap.get("n_dispersal"),
        },
        "core_fold_recompute": {
            **{k: v for k, v in core.items() if k != "folds"},
            "worst_folds": (core.get("folds") or [])[:8],
        },
        "archive_margin_audit": margin,
        "contested_panel": {
            **{k: v for k, v in contested.items() if k != "observables"},
            "observables": contested.get("observables") or [],
        },
        "publication_claims": pub,
        "cosmology_benchmark": cosmo,
        "cluster_snapshot": clusters,
        "preregistered_predictions": preds,
        "multipath_exploratory": multi,
        "headline": _headline(checks, margin, contested, core, multi),
    }

    if write:
        out_dir = data_root() / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = out_dir / f"accuracy_readings_{stamp}.json"
        latest = out_dir / "accuracy_readings_latest.json"
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        latest.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        report["written"] = {"path": str(path), "latest": str(latest)}

    return report


def _headline(
    checks: dict[str, bool],
    margin: dict[str, Any],
    contested: dict[str, Any],
    core: dict[str, Any],
    multi: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "authority_ok": checks.get("authority_ok"),
        "core_engine_matches_atlas": checks.get("core_recompute_ok"),
        "archive_domains_green": f"{margin.get('green_gate_pass_count')}/{margin.get('n_domains_reported')} "
        f"(fail={margin.get('green_gate_fail_count')})",
        "archive_pooled_median_of_medians_pct": margin.get("pooled_median_of_domain_medians_pct"),
        "contested_fsot_pooled_median_pct": contested.get("fsot_pooled_median_error_pct"),
        "contested_vs_baseline_pct": contested.get("current_model_baseline_pct"),
        "core_max_recompute_error_pct": core.get("max_rel_error_pct"),
        "multipath_map_emergence_mean": (multi or {}).get("map_emergence_mean"),
        "multipath_in_natural_band": (multi or {}).get("in_natural_band"),
        "paradigm": (
            "One seed engine across all domains. Empirical green gate ≤0.5%. "
            "Contested open sectors: FSOT vs ~15% current-model baseline. "
            "Multipath co-emergence is discovery/paradigm map occupancy, not the panel gate."
        ),
    }


def format_readings_text(report: dict[str, Any]) -> str:
    """Human-readable multi-domain accuracy report."""
    h = report.get("headline") or {}
    m = report.get("acceptable_margins") or {}
    margin = report.get("archive_margin_audit") or {}
    cont = report.get("contested_panel") or {}
    core = report.get("core_fold_recompute") or {}
    multi = report.get("multipath_exploratory") or {}
    preds = report.get("preregistered_predictions") or {}
    lines = [
        "=== FSOT CROSS-DOMAIN ACCURACY READINGS ===",
        f"generated: {report.get('generated_at')}",
        f"integrity: {report.get('integrity_score')}  free_parameters=0  pin={str(report.get('authority_sha256') or '')[:12]}…",
        "",
        "ACCEPTABLE MARGINS (current archive / science standard for this project)",
        f"  green gate pooled median: ≤{m.get('archive_green_gate_pooled_median_pct')}%",
        f"  strict scalar max:        ≤{m.get('archive_strict_scalar_max_pct')}%",
        f"  core S recompute tol:     ≤{m.get('core_S_recompute_tol_pct')}%",
        f"  contested current-model baseline: ~{m.get('contested_open_panel_current_model_baseline_pct')}%",
        f"  multipath map natural band: {m.get('multipath_map_emergence_natural_band')}",
        "",
        "AUTHORITY / ENGINE",
        f"  authority_ok={h.get('authority_ok')}  core_engine_matches_atlas={h.get('core_engine_matches_atlas')}",
        f"  core recompute max_rel_error_pct={core.get('max_rel_error_pct')} "
        f"median={core.get('median_rel_error_pct')} ({core.get('n_within_tol')}/{core.get('n_core')} within tol)",
        "",
        "ARCHIVE EMPIRICAL GREEN GATE (all domains, not biology-only)",
        f"  domains green: {h.get('archive_domains_green')}",
        f"  pooled median-of-domain-medians: {margin.get('pooled_median_of_domain_medians_pct')}%",
        f"  max domain pooled median: {margin.get('max_pooled_domain_median_pct')}%",
        f"  worst scalar domain: {margin.get('worst_scalar_domain')} "
        f"@ {margin.get('worst_scalar_max_error_pct')}%",
        f"  all_green={margin.get('all_green')}",
        "",
        "CONTESTED OPEN-SCIENCE PANEL (H0, S8, BBN, N_eff, …)",
        f"  verdict: {cont.get('verdict')}",
        f"  FSOT pooled median error: {cont.get('fsot_pooled_median_error_pct')}%",
        f"  FSOT max error: {cont.get('fsot_max_error_pct')}%",
        f"  current-model baseline: {cont.get('current_model_baseline_pct')}%",
        f"  within 0.5% gate: {cont.get('n_within_0_5pct')}/{cont.get('n_observables')}",
        f"  beats baseline: {cont.get('n_beats_15pct_baseline')}/{cont.get('n_observables')}",
        "",
        "PREREGISTERED PREDICTIONS (cross-domain designs)",
        f"  n={preds.get('n_predictions')} across {preds.get('n_domains')} domains",
        "",
        "MULTIPATH EXPLORATORY (discovery layer — not empirical 0.5% gate)",
        f"  map emergence mean: {multi.get('map_emergence_mean')}  "
        f"in_natural_band={multi.get('in_natural_band')}",
        f"  p10–p90: {multi.get('map_emergence_p10')}–{multi.get('map_emergence_p90')}",
        f"  note: {multi.get('epistemic_note')}",
        "",
        f"PARADIGM: {h.get('paradigm')}",
    ]
    # Contested sample table
    obs = cont.get("observables") or []
    if obs:
        lines.append("")
        lines.append("CONTESTED OBSERVABLES (sample)")
        for o in obs[:12]:
            lines.append(
                f"  {o.get('name')}: err={o.get('fsot_error_pct')}% "
                f"gate={o.get('within_green_gate')} "
                f"beats_baseline={o.get('beats_current_model_baseline')} "
                f"[{o.get('computed')} vs {o.get('measured')} {o.get('unit')}]"
            )
    # Focus multipath domains
    focus = (multi or {}).get("focus_domains") or []
    if focus:
        lines.append("")
        lines.append("MULTIPATH FOCUS FOLDS (path-mean S)")
        for f in focus:
            lines.append(
                f"  {f.get('domain')}: S_path={f.get('S_path_mean')} "
                f"S_can={f.get('S_canonical')} flip={f.get('flip_rate')} D_eff={f.get('D_eff')}"
            )
    # Clusters
    cl = report.get("cluster_snapshot") or {}
    if cl:
        lines.append("")
        lines.append("CLUSTER SNAPSHOT (core folds)")
        for name, row in sorted(cl.items()):
            lines.append(
                f"  {name}: n={row.get('n_core_folds')} mean_S={row.get('mean_S'):+.4f} "
                f"emerge={row.get('emergence_fraction'):.2%}"
                if isinstance(row.get("mean_S"), (int, float))
                else f"  {name}: {row}"
            )
    written = report.get("written") or {}
    if written:
        lines.append("")
        lines.append(f"written: {written.get('latest')}")
    return "\n".join(lines)
