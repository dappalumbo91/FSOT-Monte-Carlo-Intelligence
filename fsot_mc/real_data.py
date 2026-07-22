"""
Real-data anchors — local archive bundle first (independent).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fsot_mc.paths import archive_bundle_dir, linguistics_dir
from fsot_mc.universe_atlas import domain_names, get_domain


def _bundle_file(*names: str) -> Path | None:
    b = archive_bundle_dir()
    for n in names:
        p = b / n
        if p.is_file():
            return p
    return None


def load_domain_scalar_fixtures() -> dict[str, Any]:
    p = _bundle_file("data__fsot_domain_scalar_fixtures.json")
    if p is None:
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for row in raw.get("domains") or []:
        name = row.get("name")
        if not name:
            continue
        out[name] = {
            "measured_proxy": float(row["python_scalar"]),
            "source": "local_archive_bundle/fixtures",
            "D_eff": row.get("d_eff"),
            "kind": "authority_scalar",
        }
    return out


def build_real_data_bundle(*, use_archive: bool = True) -> dict[str, Any]:
    bundle: dict[str, Any] = {}
    if use_archive:
        bundle.update(load_domain_scalar_fixtures())
    for name in domain_names():
        if name not in bundle:
            d = get_domain(name)
            bundle[name] = {
                "measured_proxy": d["S_canonical"],
                "source": "portable_full_atlas",
                "kind": "canonical_scalar",
            }
    ling = linguistics_dir() / "linguistics_derivations.json"
    return {
        "anchors": bundle,
        "meta": {
            "n_domains": len(bundle),
            "archive_bundle": str(archive_bundle_dir()),
            "linguistics_present": ling.is_file(),
            "independent": True,
            "free_parameters": 0,
        },
    }
