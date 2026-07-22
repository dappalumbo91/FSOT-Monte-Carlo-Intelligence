"""
Realities OS client — observe live universe ticks under FSOT law.

MC is a *client* of Realities runtime state. It never writes physics_field.
Default root: I:\\FSOT-Physical-Archive\\10_Realities-OS
Override: REALITIES_OS_ROOT or FSOT_REALITIES_ROOT
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.pi_ring import PiRing
from fsot_mc.pathway_memory import PathwayMemory, pathway_quality

DEFAULT_ROOTS = [
    Path(r"I:\FSOT-Physical-Archive\10_Realities-OS"),
    Path(os.environ.get("REALITIES_OS_ROOT", "")),
    Path(os.environ.get("FSOT_REALITIES_ROOT", "")),
]


def realities_root() -> Path | None:
    for p in DEFAULT_ROOTS:
        if p and p.is_dir() and (p / "data" / "runtime").is_dir():
            return p
    return None


def runtime_dir(root: Path | None = None) -> Path | None:
    root = root or realities_root()
    if root is None:
        return None
    return root / "data" / "runtime"


def _read_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _tail_jsonl(path: Path, n: int = 20) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def poll_runtime(root: Path | None = None) -> dict[str, Any]:
    """Snapshot Realities OS runtime artifacts (read-only)."""
    rt = runtime_dir(root)
    if rt is None:
        return {
            "ok": False,
            "error": "realities_runtime_not_found",
            "free_parameters": 0,
        }

    heartbeat = _read_text(rt / "heartbeat")
    reality = _read_json(rt / "reality.state.json")
    visual = _read_json(rt / "visual_state.live.json")
    emergence = _tail_jsonl(rt / "emergence.jsonl", 15)
    ops = _read_json(rt / "ops_snapshot.json")
    pathway = _read_json(rt / "pathway_reason_last.json")

    pid_path = rt / "kernel.pid"
    kernel_alive = False
    if pid_path.is_file():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            # Windows: check process exists lightly
            import ctypes

            kernel_alive = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid) != 0  # type: ignore
        except Exception:
            kernel_alive = heartbeat is not None

    return {
        "ok": True,
        "method": "fsot_realities_client_poll",
        "free_parameters": 0,
        "root": str(rt.parent.parent),
        "runtime": str(rt),
        "kernel_alive": kernel_alive,
        "heartbeat": heartbeat.strip() if heartbeat else None,
        "reality_state_keys": list(reality.keys()) if isinstance(reality, dict) else None,
        "visual_state_present": visual is not None,
        "n_emergence_tail": len(emergence),
        "emergence_tail": emergence,
        "ops_snapshot": ops,
        "pathway_reason_last": pathway,
        "polled_at": datetime.now(timezone.utc).isoformat(),
        "note": "Read-only client. MC does not write physics_field.",
    }


def emergence_to_path_proxy(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Map emergence events into a pathway-like dict for memory/MC coupling."""
    if not events:
        return {
            "emergence_fraction": 0.5,
            "collapse_true_fraction": 0.5,
            "ladder_agree_fraction": 0.5,
            "n_regime_flips": 0,
            "regime_flips": [],
            "mean_S": 0.0,
            "mean_bridge_strength": 0.0,
            "contested": {},
            "long_range_bridges": [],
            "global_phase": 0.0,
        }
    # Heuristic vitality from event types
    types = [str(e.get("type") or e.get("kind") or e.get("event") or "") for e in events]
    expand = sum(1 for t in types if "expand" in t.lower() or "emerge" in t.lower())
    total = max(len(types), 1)
    ef = expand / total
    mean_S = float(np_mean([float(e.get("S") or e.get("score") or 0.0) for e in events]))
    return {
        "emergence_fraction": ef,
        "collapse_true_fraction": 0.5 + 0.2 * ef,
        "ladder_agree_fraction": min(1.0, 0.4 + ef),
        "n_regime_flips": sum(1 for t in types if "flip" in t.lower() or "shift" in t.lower()),
        "regime_flips": [t for t in types if t][:6],
        "mean_S": mean_S,
        "mean_bridge_strength": abs(mean_S) * 0.1,
        "contested": {},
        "long_range_bridges": [],
        "global_phase": mean_S,
        "source": "realities_emergence",
    }


def np_mean(xs: list[float]) -> float:
    return sum(xs) / max(len(xs), 1)


def couple_to_intelligence(
    *,
    memory: PathwayMemory | None = None,
    project_ring: bool = True,
) -> dict[str, Any]:
    """
    Poll Realities → pathway memory observe → optional π-ring projection.
    """
    poll = poll_runtime()
    if not poll.get("ok"):
        return poll

    mem = memory or PathwayMemory()
    path_proxy = emergence_to_path_proxy(poll.get("emergence_tail") or [])
    rec = mem.observe_path(path_proxy, path_index=int(datetime.now().timestamp()) % 10_000)

    ring_out = None
    if project_ring:
        ring = PiRing()
        # Project pathway quality into interior
        ring.write_mc_state(
            d_eff=20.0,
            phase=float(path_proxy.get("global_phase") or 0.0),
            S=float(path_proxy.get("mean_S") or 0.0),
            mass=1.0 + pathway_quality(path_proxy),
        )
        # Sensory: heartbeat string
        if poll.get("heartbeat"):
            ring.write_text_as_ring(str(poll["heartbeat"])[:64])
        ring.normalize_mc()
        ring_out = ring.readout()

    return {
        "ok": True,
        "method": "fsot_realities_couple",
        "free_parameters": 0,
        "poll": {
            "kernel_alive": poll.get("kernel_alive"),
            "heartbeat": poll.get("heartbeat"),
            "n_emergence_tail": poll.get("n_emergence_tail"),
            "root": poll.get("root"),
        },
        "path_proxy": path_proxy,
        "pathway_record": {
            "key": rec.key,
            "solidified": rec.solidified,
            "acc_phi": rec.acc_phi,
            "trials": rec.trials,
            "strength": rec.strength,
        },
        "pathway_memory": mem.summary(),
        "pi_ring": ring_out,
        "note": "Realities → MC observer coupling. Law remains on archive/kernel.",
    }
