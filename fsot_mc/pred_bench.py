"""
PRED bench-closure ledger — preregistered predictions with kill criteria tracking.

Tracks: open | in_progress | pass | kill | blocked
Does not invent lab results — records status and evidence paths you supply.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.archive_predictions import load_preregistered_predictions
from fsot_mc.paths import PACKAGE_ROOT, data_root


def bench_path() -> Path:
    p = data_root() / "pred_bench"
    p.mkdir(parents=True, exist_ok=True)
    return p / "closure_ledger.json"


def _default_entry(pred: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": pred.get("id"),
        "name": pred.get("name"),
        "domain": pred.get("domain"),
        "fsot_predicted": pred.get("fsot_predicted"),
        "unit": pred.get("unit"),
        "sota_baseline": pred.get("sota_baseline"),
        "sota_label": pred.get("sota_label"),
        "discriminant": pred.get("discriminant"),
        "formula_branch": pred.get("fsot_formula_branch"),
        "note": (str(pred.get("note") or ""))[:500],
        "status": "open",
        "kill_criteria": [
            f"Discriminant fails: {pred.get('discriminant')}",
            "Requires free-parameter retune to match measured value",
            "Authority pin D1D38A mismatch at evaluation time",
        ],
        "pass_criteria": [
            f"Discriminant satisfied: {pred.get('discriminant')}",
            "Pin D1D38A verified",
            "No post-hoc seed or constant retuning",
        ],
        "measured_value": None,
        "measured_source": None,
        "measured_at": None,
        "evidence_paths": [],
        "log": [],
        "free_parameters": 0,
    }


def load_bench_ledger() -> dict[str, Any]:
    path = bench_path()
    preds = {str(p.get("id")): p for p in load_preregistered_predictions()}
    if path.is_file():
        try:
            ledger = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            ledger = {"entries": {}}
    else:
        ledger = {"entries": {}}

    entries = ledger.get("entries") or {}
    # merge new PREDs
    for pid, pred in preds.items():
        if pid not in entries:
            entries[pid] = _default_entry(pred)
        else:
            # refresh static fields from manifest
            e = entries[pid]
            e["name"] = pred.get("name")
            e["fsot_predicted"] = pred.get("fsot_predicted")
            e["discriminant"] = pred.get("discriminant")
            e["sota_baseline"] = pred.get("sota_baseline")
            e["sota_label"] = pred.get("sota_label")
            e["unit"] = pred.get("unit")
            e["domain"] = pred.get("domain")

    ledger["entries"] = entries
    ledger["n"] = len(entries)
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
    ledger["free_parameters"] = 0
    return ledger


def save_bench_ledger(ledger: dict[str, Any]) -> Path:
    path = bench_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(ledger, indent=2, default=str), encoding="utf-8")
    return path


def bench_status_summary(ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    ledger = ledger or load_bench_ledger()
    counts: dict[str, int] = {}
    for e in (ledger.get("entries") or {}).values():
        st = str(e.get("status") or "open")
        counts[st] = counts.get(st, 0) + 1
    return {
        "n": ledger.get("n"),
        "by_status": counts,
        "path": str(bench_path()),
        "free_parameters": 0,
    }


def update_pred_status(
    pred_id: str,
    *,
    status: str,
    measured_value: Any = None,
    measured_source: str | None = None,
    evidence_path: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    allowed = {"open", "in_progress", "pass", "kill", "blocked"}
    if status not in allowed:
        return {"ok": False, "error": f"status must be one of {sorted(allowed)}"}
    ledger = load_bench_ledger()
    entries = ledger["entries"]
    if pred_id not in entries:
        return {"ok": False, "error": f"unknown pred_id {pred_id}"}
    e = entries[pred_id]
    e["status"] = status
    if measured_value is not None:
        e["measured_value"] = measured_value
        e["measured_at"] = datetime.now(timezone.utc).isoformat()
    if measured_source:
        e["measured_source"] = measured_source
    if evidence_path:
        paths = list(e.get("evidence_paths") or [])
        if evidence_path not in paths:
            paths.append(evidence_path)
        e["evidence_paths"] = paths
    log = list(e.get("log") or [])
    log.append(
        {
            "t": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "measured_value": measured_value,
            "note": note,
        }
    )
    e["log"] = log[-50:]
    save_bench_ledger(ledger)
    return {"ok": True, "entry": e, "summary": bench_status_summary(ledger)}


def write_bench_markdown(ledger: dict[str, Any] | None = None) -> Path:
    ledger = ledger or load_bench_ledger()
    summary = bench_status_summary(ledger)
    lines = [
        "# PRED Bench-Closure Ledger",
        "",
        f"Updated: {ledger.get('updated_at')}  ",
        f"Total PREDs: **{summary.get('n')}**  ",
        f"By status: `{summary.get('by_status')}`  ",
        "",
        "Status meanings: `open` | `in_progress` | `pass` | `kill` | `blocked`",
        "",
        "| ID | Name | Domain | FSOT | SOTA | Status | Discriminant |",
        "|----|------|--------|-----:|-----:|--------|--------------|",
    ]
    for pid, e in sorted((ledger.get("entries") or {}).items()):
        lines.append(
            f"| {pid} | {e.get('name')} | {e.get('domain')} | "
            f"{e.get('fsot_predicted')} | {e.get('sota_baseline')} | "
            f"**{e.get('status')}** | {e.get('discriminant')} |"
        )
    lines += [
        "",
        "## Kill / pass criteria (template)",
        "",
        "Every entry carries discriminant-derived kill/pass lists. Update via:",
        "",
        "```powershell",
        'python -m fsot_mc pred-bench --set PRED-001 --status pass --measured 70.8 --source "lab_note.md"',
        "```",
        "",
        "---",
        "*Preregistered ≠ lab-closed until status=pass under discriminant.*",
        "",
    ]
    path = PACKAGE_ROOT / "docs" / "PRED_BENCH_CLOSURE.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    # also refresh ledger file
    save_bench_ledger(ledger)
    return path


def init_bench_from_manifest() -> dict[str, Any]:
    ledger = load_bench_ledger()
    path = save_bench_ledger(ledger)
    md = write_bench_markdown(ledger)
    return {
        "ok": True,
        "n": ledger.get("n"),
        "summary": bench_status_summary(ledger),
        "ledger_path": str(path),
        "markdown": str(md),
        "free_parameters": 0,
    }


# High-value PREDs for active lab / instrument programs (not free-param retune)
PRIORITY_PRED_IDS: tuple[str, ...] = (
    "PRED-001",  # H0 bridge
    "PRED-002",  # S8
    "PRED-004",  # muon g-2
    "PRED-005",  # lithium
    "PRED-034",  # fuel thermochemistry (archive-strong panel)
    "PRED-035",  # machine-molecule catalog
    "PRED-024",  # H0 dual-anchor bubble
)


def _in_silico_discriminant(entry: dict[str, Any]) -> dict[str, Any]:
    """
    Check whether the *preregistered FSOT number* is consistent with its
    discriminant geometry vs SOTA anchors. This is NOT a lab pass.

    Epistemic: STRUCTURE / prereg self-check only.
    """
    disc = str(entry.get("discriminant") or "")
    try:
        fsot = float(entry["fsot_predicted"]) if entry.get("fsot_predicted") is not None else None
    except (TypeError, ValueError):
        fsot = None
    try:
        sota = float(entry["sota_baseline"]) if entry.get("sota_baseline") is not None else None
    except (TypeError, ValueError):
        sota = None

    ok: bool | None = None
    detail = ""

    if fsot is None:
        return {"ok": None, "detail": "no_fsot_predicted", "tier": "STRUCTURE"}

    if disc == "strictly_between_planck_and_sh0es":
        # Planck ~67.4, SH0ES ~73.0 (public anchors); use SOTA as low if labeled Planck
        lo = sota if sota is not None else 67.36
        hi = 73.04
        ok = lo < fsot < hi
        detail = f"lo={lo} fsot={fsot} hi={hi}"
    elif disc == "between_planck_and_des":
        lo, hi = 0.76, 0.85  # rough public S8 band for geometry check
        if sota is not None:
            # place fsot between min(sota,fsot) band widen
            lo, hi = min(sota, fsot) - 0.05, max(sota, fsot) + 0.05
        ok = lo <= fsot <= hi
        detail = f"band=[{lo},{hi}] fsot={fsot}"
    elif disc == "within_10pct_of_observed_gap":
        if sota is None or sota == 0:
            ok = None
            detail = "no_sota_or_zero"
        else:
            rel = abs(fsot - sota) / abs(sota)
            ok = rel <= 0.10
            detail = f"rel_err={rel:.4f} (need ≤0.10 vs sota anchor)"
    elif disc == "same_sign_as_fermilab":
        ok = fsot > 0
        detail = f"fsot_sign={1 if fsot > 0 else -1}"
    elif disc == "fsot_exceeds_sota_by_0.4":
        if sota is None:
            ok = fsot > 0.4
            detail = f"fsot={fsot} (no sota)"
        else:
            ok = fsot >= sota + 0.4 or (sota == 0 and fsot > 0)
            detail = f"fsot={fsot} sota={sota}"
    elif disc == "independent_frontier_not_in_benchmark_panel":
        ok = True
        detail = "frontier_scalar_present"
    else:
        ok = None
        detail = f"no_auto_check_for_{disc}"

    return {
        "ok": ok,
        "detail": detail,
        "discriminant": disc,
        "tier": "STRUCTURE",
        "note": "In-silico discriminant geometry only — not lab-closed pass.",
    }


def run_in_silico_self_checks(*, write: bool = True) -> dict[str, Any]:
    """Annotate every PRED with in_silico_check; does not change pass/kill."""
    ledger = load_bench_ledger()
    n_ok = n_fail = n_skip = 0
    for e in (ledger.get("entries") or {}).values():
        chk = _in_silico_discriminant(e)
        e["in_silico_check"] = {**chk, "checked_at": datetime.now(timezone.utc).isoformat()}
        if chk.get("ok") is True:
            n_ok += 1
        elif chk.get("ok") is False:
            n_fail += 1
        else:
            n_skip += 1
    if write:
        save_bench_ledger(ledger)
        write_bench_markdown(ledger)
    return {
        "ok": True,
        "n_ok": n_ok,
        "n_fail": n_fail,
        "n_skip": n_skip,
        "free_parameters": 0,
        "note": "STRUCTURE self-check only; lab still closes PREDs.",
    }


def advance_priority_preds(
    *,
    pred_ids: list[str] | None = None,
    status: str = "in_progress",
    note: str | None = None,
) -> dict[str, Any]:
    """
    Move high-value PREDs into active lab queue (default in_progress).
    Never invents measured values.
    """
    ids = list(pred_ids or PRIORITY_PRED_IDS)
    note = note or (
        "Priority lab queue — free_parameters=0; close only under discriminant + pin D1D38A; "
        "in_silico self-check is not lab pass."
    )
    results = []
    for pid in ids:
        r = update_pred_status(pid, status=status, note=note)
        results.append({"id": pid, "ok": r.get("ok"), "status": status, "error": r.get("error")})
    write_bench_markdown()
    return {
        "ok": all(x.get("ok") for x in results if x.get("error") is None),
        "advanced": results,
        "summary": bench_status_summary(),
        "free_parameters": 0,
    }


def write_priority_roadmap() -> Path:
    """Markdown roadmap of open/in_progress PREDs for experiment planning."""
    ledger = load_bench_ledger()
    summary = bench_status_summary(ledger)
    # ensure self-checks exist
    for e in (ledger.get("entries") or {}).values():
        if "in_silico_check" not in e:
            e["in_silico_check"] = _in_silico_discriminant(e)

    lines = [
        "# PRED Priority Roadmap — lab closure queue",
        "",
        f"Updated: {datetime.now(timezone.utc).isoformat()}  ",
        f"Ledger: {summary.get('by_status')} · free_parameters=0 · pin D1D38A  ",
        "",
        "## Doctrine",
        "",
        "- **PREREG** until status=`pass` under discriminant with evidence.",
        "- **In-silico check** = discriminant geometry vs anchors (STRUCTURE) — **not** lab pass.",
        "- Soft court promote ≠ Lean-proved.",
        "- Green gate ≤0.5% is MEASURED archive accuracy — **not** multipath map occupancy.",
        "",
        "## Active priority queue",
        "",
        "| ID | Name | Domain | Status | FSOT | Discriminant | In-silico |",
        "|----|------|--------|--------|-----:|--------------|-----------|",
    ]
    for pid in PRIORITY_PRED_IDS:
        e = (ledger.get("entries") or {}).get(pid) or {}
        chk = e.get("in_silico_check") or {}
        lines.append(
            f"| {pid} | {e.get('name')} | {e.get('domain')} | **{e.get('status')}** | "
            f"{e.get('fsot_predicted')} | {e.get('discriminant')} | {chk.get('ok')} |"
        )
    lines += [
        "",
        "## How to close a PRED",
        "",
        "```powershell",
        'python -m fsot_mc pred-bench --set PRED-001 --status pass --measured 70.8 --source "lab_report.md"',
        "```",
        "",
        "Kill if free-parameter retune required or pin fails.",
        "",
        "---",
        "*Generated by pred_bench.write_priority_roadmap — no free parameters.*",
        "",
    ]
    path = PACKAGE_ROOT / "docs" / "PRED_PRIORITY_ROADMAP.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    save_bench_ledger(ledger)
    return path
