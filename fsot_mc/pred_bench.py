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
