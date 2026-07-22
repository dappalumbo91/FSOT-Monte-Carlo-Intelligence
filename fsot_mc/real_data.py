"""
Real-data anchors for FSOT Universe discovery.

Pulls optional measured proxies from the physical archive when present.
Never required for MC to run (portable atlas is seed-complete).

Environment:
  FSOT_ARCHIVE_ROOT  default I:\\FSOT-Physical-Archive
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fsot_mc.paths import archive_root
from fsot_mc.universe_atlas import domain_names, get_domain


def _hub() -> Path | None:
    root = archive_root()
    if root is None:
        return None
    hub = root / "02_FSOT-2.1-Lean-Full"
    return hub if hub.is_dir() else None


def load_domain_scalar_fixtures() -> dict[str, Any]:
    """Archive fixtures: python_scalar per domain (authority numeric)."""
    hub = _hub()
    if hub is None:
        return {}
    p = hub / "data" / "fsot_domain_scalar_fixtures.json"
    if not p.is_file():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for row in raw.get("domains") or []:
        name = row.get("name")
        if not name:
            continue
        out[name] = {
            "measured_proxy": float(row["python_scalar"]),
            "source": "fsot_domain_scalar_fixtures.json",
            "D_eff": row.get("d_eff"),
            "kind": "authority_scalar",
        }
    return out


def load_wave1_as_real() -> dict[str, Any]:
    """Wave-1 cosmology anchors as cosmology-domain real targets (meta)."""
    hub = _hub()
    # Prefer local atlas wave1 if no hub
    from fsot_mc.universe_atlas import wave1_anchors

    anchors = wave1_anchors()
    if not anchors:
        return {}
    # Attach to Cosmology domain as multi-observable note
    return {
        "Cosmology": {
            "measured_proxy": get_domain("Cosmology")["S_canonical"],
            "source": "wave1+canonical S_cosm",
            "wave1": anchors,
            "kind": "cosmology_bundle",
        }
    }


def build_real_data_bundle(*, use_archive: bool = True) -> dict[str, Any]:
    """
    Combined real-data map for discovery alignment.
    Keys are domain names; values are anchor dicts.
    """
    bundle: dict[str, Any] = {}
    if use_archive:
        fixtures = load_domain_scalar_fixtures()
        bundle.update(fixtures)
    # Always include canonical self-consistency anchors from portable atlas
    for name in domain_names():
        if name not in bundle:
            d = get_domain(name)
            bundle[name] = {
                "measured_proxy": d["S_canonical"],
                "source": "portable_universe_atlas.json",
                "kind": "canonical_scalar",
            }
    meta = {
        "n_domains": len(bundle),
        "archive_hub": str(_hub()) if _hub() else None,
        "free_parameters": 0,
    }
    return {"anchors": bundle, "meta": meta}


def load_extension_panel_names(limit: int = 50) -> list[str]:
    """Optional: list extension panel names from navigator for future expansion."""
    hub = _hub()
    if hub is None:
        return []
    p = hub / "data" / "fsot_domain_navigator.json"
    if not p.is_file():
        return []
    try:
        nav = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []
    # Navigator schema may nest panels — best-effort
    panels = []
    if isinstance(nav, dict):
        for key in ("panels", "domains", "entries"):
            block = nav.get(key)
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        name = item.get("panel") or item.get("name") or item.get("id")
                        if name:
                            panels.append(str(name))
                    elif isinstance(item, str):
                        panels.append(item)
            elif isinstance(block, dict):
                panels.extend(str(k) for k in block.keys())
    return panels[:limit]
