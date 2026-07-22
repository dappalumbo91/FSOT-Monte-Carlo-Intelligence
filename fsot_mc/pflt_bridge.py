"""
PFLT / multilayer vision bridge → π-ring eyes.

Loads Protofluid multilayer vision when available on this machine:
  C:\\Users\\damia\\Desktop\\pflt\\fsot_multilayer_vision.py

Falls back to a lightweight FSOT polar sensory sampler (no PFLT install required).
U-Net is not used — π-ring geometry is the product eye.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, E, ETA_EFF, K, PHI, PI, POOF, PSI_CON, THETA_S, P_VAR
from fsot_mc.pi_ring import PiRing, SEED_C, SEED_PHI, SEED_PI, SEED_POOF, SEED_PSI

PFLT_CANDIDATES = [
    Path(r"C:\Users\damia\Desktop\pflt"),
    Path(r"C:\Users\damia\Desktop\PFLT"),
]


def find_pflt_root() -> Path | None:
    for p in PFLT_CANDIDATES:
        if (p / "fsot_multilayer_vision.py").is_file():
            return p
    return None


def _try_import_pflt_vision() -> Any | None:
    root = find_pflt_root()
    if root is None:
        return None
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)
    try:
        import fsot_multilayer_vision as mv  # type: ignore

        return mv
    except Exception:
        return None


def fsot_field_at(x: float, y: float, *, observed: bool = True) -> dict[str, float]:
    """Local FSOT-like field sample on a plane (portable fallback)."""
    from fsot_mc.fast import ALPHA, ETA_EFF, GAMMA

    phase0 = float(THETA_S) + float(PI) * x + float(E) * y
    base = (1.0 / math.sqrt(18.0)) * math.cos(phase0 / float(ETA_EFF))
    growth = math.exp(float(ALPHA) * float(GAMMA / PHI))
    amp = base * (1.0 + 0.1 * growth)
    if observed:
        qm = math.exp(float(C_FACTOR) * float(P_VAR)) * math.cos(phase0 + float(P_VAR))
        amp *= qm
    S = float(K) * (amp + 0.5)
    coh = max(0.0, min(1.0, abs(math.cos(phase0)) * 0.95))
    uv = abs(math.sin(phase0 * float(PHI))) * 0.5
    nir = abs(math.cos(phase0 * float(E))) * 0.5
    gray = abs(amp)
    return {"S": S, "coherence": coh, "uv": uv, "nir": nir, "gray": gray, "phase": phase0}


def sample_scene_to_ring(
    ring: PiRing,
    *,
    mode: str = "auto",
    text: str | None = "FSOT",
    grid: int = 24,
) -> dict[str, Any]:
    """
    Project a sensory scene onto the outer π-ring (and optional PFLT multilayer).

    mode: auto | pflt | fallback
    """
    mv = _try_import_pflt_vision() if mode in ("auto", "pflt") else None
    used = "fallback"
    n_marks = 0

    if mv is not None and mode != "fallback":
        used = "pflt_multilayer"
        probes = mv.full_probe_set()
        # Sample a unit square, map to outer annulus polar
        for iy in range(grid):
            for ix in range(grid):
                x = (ix + 0.5) / grid
                y = (iy + 0.5) / grid
                # map square → polar outer ring
                dx, dy = x - 0.5, y - 0.5
                r_cart = math.hypot(dx, dy) * 2.0  # ~[0,√2]
                if r_cart < 1e-9:
                    continue
                theta = math.atan2(dy, dx) % (2.0 * SEED_PI)
                # place on outer annulus proportional to radial distance
                r_in = ring.cfg.r_interior
                r = r_in + (1.0 - r_in) * min(1.0, r_cart)
                try:
                    pix = mv.fsot_multilayer_at(
                        x=x, y=y, probes=probes, material="ink_on_stone", observed=True
                    )
                    amp = float(pix.gray) + 0.5 * float(pix.uv) + 0.5 * float(pix.nir)
                    ring.write_sensory_mark(theta=theta, amplitude=amp, r=r)
                    # also deposit S into nearby interior for cross-talk (weak)
                    ring.write_mc_state(
                        d_eff=18.0,
                        phase=theta,
                        S=float(pix.S),
                        mass=SEED_POOF * amp,
                    )
                    n_marks += 1
                except Exception:
                    continue
    else:
        used = "fsot_fallback_field"
        for iy in range(grid):
            for ix in range(grid):
                x = (ix + 0.5) / grid
                y = (iy + 0.5) / grid
                dx, dy = x - 0.5, y - 0.5
                r_cart = math.hypot(dx, dy) * 2.0
                if r_cart < 1e-9:
                    continue
                theta = math.atan2(dy, dx) % (2.0 * SEED_PI)
                r_in = ring.cfg.r_interior
                r = r_in + (1.0 - r_in) * min(1.0, r_cart)
                f = fsot_field_at(x, y)
                amp = f["gray"] + 0.5 * f["uv"] + 0.5 * f["nir"]
                ring.write_sensory_mark(theta=theta, amplitude=amp, r=r)
                n_marks += 1

    if text:
        ring.write_text_as_ring(text)

    ring.normalize_mc()
    out = ring.readout()
    out["vision_backend"] = used
    out["pflt_root"] = str(find_pflt_root()) if find_pflt_root() else None
    out["n_sensory_samples"] = n_marks
    out["free_parameters"] = 0
    return out


def eyes_with_mc(
    mc_result: dict[str, Any],
    *,
    text: str | None = None,
    vision_mode: str = "auto",
) -> dict[str, Any]:
    """Fill π-ring from MC domain ensemble + sensory scene."""
    ring = PiRing()
    de = mc_result.get("domain_ensemble") or {}
    for name, row in de.items():
        ring.write_mc_state(
            d_eff=float(row.get("D_eff", 18)),
            phase=float(row.get("dS_mean", 0.0)),
            S=float(row.get("S_path_mean", row.get("S_canonical", 0.0))),
            mass=1.0,
        )
    vision = sample_scene_to_ring(ring, mode=vision_mode, text=text or "FSOT universe")
    return {
        "method": "fsot_pi_ring_eyes",
        "free_parameters": 0,
        "ring": vision,
        "n_domains_projected": len(de),
        "note": "MC interior + PFLT/fallback sensory outer ring — not U-Net.",
    }
