"""
Pathway memory — solidify domain-signature pathways (not market tickers).

A pathway signature fingerprints a multipath universe state:
  - global vitality regime
  - flip set hash
  - long-range bridge agreement pattern
  - contested cosmology branch

When a signature repeatedly co-occurs with high ladder-agree + stable bridges,
it solidifies and biases later Monte Carlo discovery (prefer similar phases).

Seeds only: solidify bar = 0.5+Poof, φ-EWMA, Fib trial floors.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, PHI, POOF, PSI_CON
from fsot_mc.paths import data_root

SEED_C = float(C_FACTOR)
SEED_PHI = float(PHI)
SEED_POOF = float(POOF)
SEED_PSI = float(PSI_CON)

SOLIDIFY_ACC = 0.5 + SEED_POOF
SOFTEN_ACC = 0.5 + SEED_POOF * SEED_PSI
_MIN_TRIALS = 8  # Fib
_MIN_TRIALS_FULL = 13  # Fib


def _bin(x: float, edges: tuple[float, ...]) -> int:
    for i, e in enumerate(edges):
        if x < e:
            return i
    return len(edges)


def pathway_signature(path: dict[str, Any]) -> str:
    """Discrete FSOT pathway fingerprint from one universe path result."""
    ef = float(path.get("emergence_fraction") or 0.0)
    cf = float(path.get("collapse_true_fraction") or 0.0)
    agree = float(path.get("ladder_agree_fraction") or 0.0)
    flips = int(path.get("n_regime_flips") or 0)
    mean_S = float(path.get("mean_S") or 0.0)
    bridge = float(path.get("mean_bridge_strength") or 0.0)

    # Contested cosmology sign
    cont = path.get("contested") or {}
    s_cosm = float(cont.get("S_cosm") or 0.0)
    cosm_bin = 1 if s_cosm > 0 else (-1 if s_cosm < 0 else 0)

    # Long-range bridge agree pattern (sorted keys)
    lr = path.get("long_range_bridges") or []
    lr_bits = []
    for br in sorted(lr, key=lambda b: (b.get("a", ""), b.get("b", ""))):
        lr_bits.append(str(int(br.get("agree") or 0)))
    lr_code = "".join(lr_bits) if lr_bits else "0"

    # Top flips (stable order)
    flip_names = sorted(path.get("regime_flips") or [])[:6]
    flip_code = ",".join(flip_names) if flip_names else "-"

    parts = [
        f"ef{_bin(ef, (0.4, 0.55, 0.7, 0.85))}",
        f"cf{_bin(cf, (0.3, 0.5, 0.7))}",
        f"ag{_bin(agree, (0.3, 0.5, 0.7, 0.9))}",
        f"fl{_bin(flips / 35.0, (0.05, 0.15, 0.3, 0.5))}",
        f"ms{1 if mean_S > 0 else (-1 if mean_S < 0 else 0)}",
        f"br{_bin(abs(bridge), (0.05, 0.15, 0.3))}",
        f"cs{cosm_bin}",
        f"lr{lr_code}",
        f"fp{flip_code}",
    ]
    return "|".join(parts)


def pathway_quality(path: dict[str, Any]) -> float:
    """
    Instant quality score for a path (0..1-ish) — used as 'hit' target for memory.
    High when ladder agrees, bridges strong, not chaotic flip storm.
    """
    agree = float(path.get("ladder_agree_fraction") or 0.0)
    bridge = abs(float(path.get("mean_bridge_strength") or 0.0))
    flips = int(path.get("n_regime_flips") or 0)
    flip_pen = min(1.0, flips / 20.0)
    # normalize bridge via Poof scale
    b_n = math.tanh(bridge / max(SEED_POOF, 1e-6))
    q = (1.0 - 1.0 / SEED_PHI) * agree + (1.0 / SEED_PHI) * b_n
    q = q * (1.0 - SEED_POOF * flip_pen)
    return float(np.clip(q, 0.0, 1.0))


def pathway_success(path: dict[str, Any], *, threshold: float | None = None) -> bool:
    """Binary success for solidify training: quality clears seed bar."""
    thr = SOLIDIFY_ACC if threshold is None else threshold
    # Map quality in [0,1] — treat success if quality >= 0.5+Poof*0.5 mid bar
    return pathway_quality(path) >= (0.5 + SEED_POOF * 0.5)


@dataclass
class PathwayRecord:
    key: str
    trials: int = 0
    hits: int = 0
    acc_phi: float = 0.5
    quality_mass: float = 0.0
    solidified: bool = False
    strength: float = 0.0
    soft_fails: int = 0
    last_path_i: int = -1
    # Preferred phase bias for future paths (mean global phase when successful)
    phase_mass: float = 0.0
    preferred_phase: float = 0.0


class PathwayMemory:
    """Online solidify/soften ledger for universe pathway signatures."""

    def __init__(self) -> None:
        self.patterns: dict[str, PathwayRecord] = {}
        self.n_updates = 0
        self.n_solidify_events = 0
        self.n_soften_events = 0
        self.free_parameters = 0

    def observe_path(self, path: dict[str, Any], *, path_index: int = -1) -> PathwayRecord:
        key = pathway_signature(path)
        rec = self.patterns.get(key) or PathwayRecord(key=key)
        success = pathway_success(path)
        q = pathway_quality(path)
        hit = 1.0 if success else 0.0

        rec.trials += 1
        if success:
            rec.hits += 1
            rec.soft_fails = 0
            rec.quality_mass += q
            phase = float(path.get("global_phase") or 0.0)
            rec.phase_mass += phase
            rec.preferred_phase = rec.phase_mass / max(rec.hits, 1)
        else:
            rec.soft_fails += 1

        a = 1.0 / SEED_PHI
        rec.acc_phi = a * hit + (1.0 - a) * rec.acc_phi
        margin = rec.acc_phi - 0.5
        denom = max(0.5 - SEED_POOF, 1e-9)
        rec.strength = float(np.clip(SEED_C * margin / denom, 0.0, 1.0))
        rec.last_path_i = path_index

        raw_acc = rec.hits / max(rec.trials, 1)
        exceptional = rec.acc_phi >= (0.5 + SEED_PHI * SEED_POOF) and rec.trials >= _MIN_TRIALS
        full_ready = rec.trials >= _MIN_TRIALS_FULL
        can_solid = (exceptional or full_ready) and rec.acc_phi >= SOLIDIFY_ACC and raw_acc >= (
            0.5 + SEED_POOF * 0.5
        )

        if not rec.solidified and can_solid:
            rec.solidified = True
            self.n_solidify_events += 1
        elif rec.solidified and (
            rec.acc_phi < SOFTEN_ACC and rec.soft_fails >= 3
        ):
            rec.solidified = False
            rec.strength *= SEED_POOF
            self.n_soften_events += 1

        self.patterns[key] = rec
        self.n_updates += 1
        return rec

    def bias_for(self, key: str) -> dict[str, float]:
        rec = self.patterns.get(key)
        if rec is None or not rec.solidified:
            return {
                "solidified": 0.0,
                "strength": 0.0,
                "phase_bias": 0.0,
                "path_weight": 1.0,
                "acc_phi": rec.acc_phi if rec else 0.5,
                "trials": float(rec.trials) if rec else 0.0,
            }
        return {
            "solidified": 1.0,
            "strength": rec.strength,
            "phase_bias": rec.preferred_phase,
            "path_weight": 1.0 + rec.strength / SEED_PHI,
            "acc_phi": rec.acc_phi,
            "trials": float(rec.trials),
        }

    def best_solidified(self, n: int = 8) -> list[dict[str, Any]]:
        solid = [p for p in self.patterns.values() if p.solidified]
        solid.sort(key=lambda p: (p.strength, p.trials), reverse=True)
        return [
            {
                "key": p.key,
                "strength": round(p.strength, 4),
                "acc_phi": round(p.acc_phi, 4),
                "trials": p.trials,
                "preferred_phase": p.preferred_phase,
            }
            for p in solid[:n]
        ]

    def summary(self) -> dict[str, Any]:
        solid = sum(1 for p in self.patterns.values() if p.solidified)
        return {
            "n_patterns": len(self.patterns),
            "n_solidified": solid,
            "n_updates": self.n_updates,
            "n_solidify_events": self.n_solidify_events,
            "n_soften_events": self.n_soften_events,
            "solidify_threshold": SOLIDIFY_ACC,
            "top_solidified": self.best_solidified(),
            "free_parameters": 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "patterns": {k: asdict(v) for k, v in self.patterns.items()},
            "n_updates": self.n_updates,
            "n_solidify_events": self.n_solidify_events,
            "n_soften_events": self.n_soften_events,
            "free_parameters": 0,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PathwayMemory":
        mem = cls()
        mem.n_updates = int(data.get("n_updates", 0))
        mem.n_solidify_events = int(data.get("n_solidify_events", 0))
        mem.n_soften_events = int(data.get("n_soften_events", 0))
        for k, v in (data.get("patterns") or {}).items():
            mem.patterns[k] = PathwayRecord(**v)
        return mem

    def save(self, path: Path | str | None = None) -> Path:
        path = Path(path) if path else data_root() / "pathways" / "pathway_memory.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | str | None = None) -> "PathwayMemory":
        path = Path(path) if path else data_root() / "pathways" / "pathway_memory.json"
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def train_pathway_memory_from_mc(
    mc_result: dict[str, Any],
    *,
    memory: PathwayMemory | None = None,
) -> tuple[PathwayMemory, dict[str, Any]]:
    """
    Observe sample_paths from a universe MC run into pathway memory.
    For deeper training, re-simulate paths externally and call observe_path.
    """
    mem = memory or PathwayMemory()
    samples = mc_result.get("sample_paths") or []
    # sample_paths are compact — rebuild minimal path dicts
    for i, s in enumerate(samples):
        # compact samples lack full domain maps; still fingerprint available fields
        path = {
            "emergence_fraction": s.get("emergence_fraction"),
            "collapse_true_fraction": s.get("collapse_true_fraction"),
            "ladder_agree_fraction": s.get("ladder_agree_fraction"),
            "n_regime_flips": s.get("n_regime_flips"),
            "regime_flips": s.get("regime_flips"),
            "mean_S": s.get("mean_S"),
            "mean_bridge_strength": s.get("mean_bridge_strength"),
            "contested": s.get("contested"),
            "long_range_bridges": s.get("long_range_bridges"),
            "global_phase": 0.0,
        }
        mem.observe_path(path, path_index=i)
    return mem, mem.summary()
