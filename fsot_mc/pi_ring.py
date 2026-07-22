"""
π-Ring field — FSOT-native visual / symbolic apparatus (not a U-Net).

Geometry
  - Unit disk in polar coordinates (r, θ)
  - Interior disk area A = π · r_in²  ← Monte Carlo *writes* pathway tensors here
  - Outer annulus  ← sensory marks (text glyphs, spectra, imagery features)
  - Radial coordinate encodes scale (D_eff / 25)  — As Above, So Below
  - Angular coordinate encodes modality / phase (language, band, domain phase)

This is the visual/symbolic read surface for universe intelligence.
Deep nets may later operate *on* these polar tensors; the product geometry is the ring.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from fsot_mc.fast import C_FACTOR, PHI, PI, POOF, PSI_CON

SEED_C = float(C_FACTOR)
SEED_PHI = float(PHI)
SEED_PI = float(PI)
SEED_POOF = float(POOF)
SEED_PSI = float(PSI_CON)


@dataclass
class PiRingConfig:
    n_radial: int = 32          # r bins (incl. interior + shell)
    n_angular: int = 64         # θ bins around 2π
    r_interior: float = float(1.0 / PHI)  # interior MC disk radius (φ-derived, not free)
    # channels: field S, coherence proxy, mc_mass, sensory_mark, phase
    n_channels: int = 5


@dataclass
class PiRing:
    """Polar tensor field: shape (C, n_radial, n_angular)."""

    cfg: PiRingConfig = field(default_factory=PiRingConfig)
    data: np.ndarray = field(init=False)
    free_parameters: int = 0

    # channel indices
    CH_S = 0
    CH_COH = 1
    CH_MC = 2
    CH_SENSE = 3
    CH_PHASE = 4

    def __post_init__(self) -> None:
        c = self.cfg
        self.data = np.zeros((c.n_channels, c.n_radial, c.n_angular), dtype=np.float64)

    @property
    def interior_area(self) -> float:
        """Literal π r² of the MC fill disk (normalized units)."""
        return SEED_PI * (self.cfg.r_interior**2)

    @property
    def ring_area(self) -> float:
        return SEED_PI * (1.0 - self.cfg.r_interior**2)

    def _r_edges(self) -> np.ndarray:
        return np.linspace(0.0, 1.0, self.cfg.n_radial + 1)

    def _theta_edges(self) -> np.ndarray:
        return np.linspace(0.0, 2.0 * SEED_PI, self.cfg.n_angular + 1)

    def bin_polar(self, r: float, theta: float) -> tuple[int, int]:
        r = float(np.clip(r, 0.0, 1.0 - 1e-12))
        theta = float(theta % (2.0 * SEED_PI))
        ir = min(int(r * self.cfg.n_radial), self.cfg.n_radial - 1)
        it = min(int(theta / (2.0 * SEED_PI) * self.cfg.n_angular), self.cfg.n_angular - 1)
        return ir, it

    def d_eff_to_r(self, d_eff: float) -> float:
        """Map domain scale to radius (0=quantum-ish, 1=cosmo)."""
        return float(np.clip(float(d_eff) / 25.0, 0.0, 1.0))

    def write_mc_state(
        self,
        *,
        d_eff: float,
        phase: float,
        S: float,
        mass: float = 1.0,
    ) -> None:
        """Monte Carlo shoves a domain state into the interior disk (r ≤ r_interior)."""
        r = self.d_eff_to_r(d_eff) * self.cfg.r_interior  # fold into interior
        theta = float(phase) % (2.0 * SEED_PI)
        ir, it = self.bin_polar(r, theta)
        self.data[self.CH_S, ir, it] += float(S) * mass
        self.data[self.CH_MC, ir, it] += mass
        self.data[self.CH_PHASE, ir, it] += phase * mass
        self.data[self.CH_COH, ir, it] += abs(math.cos(phase)) * SEED_C * mass

    def write_sensory_mark(
        self,
        *,
        theta: float,
        amplitude: float = 1.0,
        r: float | None = None,
    ) -> None:
        """
        Sensory / symbolic mark on the outer ring (glyphs, spectral lines, API tokens as dots).
        Default r is mid-annulus.
        """
        r_in = self.cfg.r_interior
        r = 0.5 * (r_in + 1.0) if r is None else float(np.clip(r, r_in, 1.0))
        ir, it = self.bin_polar(r, theta)
        self.data[self.CH_SENSE, ir, it] += float(amplitude)

    def write_text_as_ring(self, text: str, *, amplitude: float = 1.0) -> None:
        """Map characters to angles on the circle (symbolic, not LLM tokenization)."""
        if not text:
            return
        for i, ch in enumerate(text):
            # codepoint → angle; φ scramble avoids trivial clustering
            u = ((ord(ch) * SEED_PHI) + i * SEED_PSI) % 1.0
            theta = 2.0 * SEED_PI * u
            self.write_sensory_mark(theta=theta, amplitude=amplitude * (0.5 + 0.5 * (ord(ch) % 13) / 13.0))

    def fill_from_universe_path(self, path: dict[str, Any]) -> None:
        """Dump one universe MC path's domain states into the interior disk."""
        domains = path.get("domains") or {}
        for name, st in domains.items():
            self.write_mc_state(
                d_eff=float(st.get("D_eff", 25)),
                phase=float(st.get("delta_psi", 0.0)) + float(st.get("phase_departure", 0.0)),
                S=float(st.get("S", 0.0)),
                mass=1.0 + SEED_POOF * float(st.get("collapse_true", False)),
            )

    def normalize_mc(self) -> None:
        """Average S/phase by mc mass where mass > 0."""
        mass = self.data[self.CH_MC]
        mask = mass > 1e-12
        self.data[self.CH_S][mask] /= mass[mask]
        self.data[self.CH_PHASE][mask] /= mass[mask]
        self.data[self.CH_COH][mask] /= mass[mask]

    def readout(self) -> dict[str, Any]:
        """Compact symbolic summary for discovery / PFLT relay."""
        mc = self.data[self.CH_MC]
        sense = self.data[self.CH_SENSE]
        S = self.data[self.CH_S]
        return {
            "method": "fsot_pi_ring",
            "free_parameters": 0,
            "n_radial": self.cfg.n_radial,
            "n_angular": self.cfg.n_angular,
            "r_interior": self.cfg.r_interior,
            "interior_area_pi_r2": self.interior_area,
            "ring_area": self.ring_area,
            "mc_mass_total": float(mc.sum()),
            "sense_mass_total": float(sense.sum()),
            "mean_S_weighted": float((S * mc).sum() / max(mc.sum(), 1e-12)),
            "peak_S": float(S.max()) if S.size else 0.0,
            "peak_sense": float(sense.max()) if sense.size else 0.0,
            "note": (
                "π-ring field: interior disk receives Monte Carlo pathways; "
                "outer ring receives sensory/symbolic marks. Not a U-Net."
            ),
        }

    def as_display_rgb(self, size: int = 128) -> np.ndarray:
        """
        Rasterize polar field to RGB for human/GPU preview.
        R ← |S|, G ← mc mass, B ← sensory marks (false-color).
        """
        img = np.zeros((size, size, 3), dtype=np.float64)
        cy = cx = (size - 1) / 2.0
        rad = (size - 1) / 2.0
        s_max = max(float(np.abs(self.data[self.CH_S]).max()), 1e-9)
        m_max = max(float(self.data[self.CH_MC].max()), 1e-9)
        e_max = max(float(self.data[self.CH_SENSE].max()), 1e-9)

        for y in range(size):
            for x in range(size):
                dx = (x - cx) / rad
                dy = (y - cy) / rad
                r = math.hypot(dx, dy)
                if r > 1.0:
                    continue
                theta = math.atan2(dy, dx) % (2.0 * SEED_PI)
                ir, it = self.bin_polar(r, theta)
                img[y, x, 0] = abs(self.data[self.CH_S, ir, it]) / s_max
                img[y, x, 1] = self.data[self.CH_MC, ir, it] / m_max
                img[y, x, 2] = self.data[self.CH_SENSE, ir, it] / e_max
                # dim exterior of interior disk slightly for visual boundary
                if r > self.cfg.r_interior:
                    img[y, x] *= 0.85
                else:
                    img[y, x, 1] = min(1.0, img[y, x, 1] + 0.05)
        return np.clip(img, 0.0, 1.0)


def demo_ring_from_mc(n_paths: int = 8, seed: int = 0) -> dict[str, Any]:
    """Smoke: run a few universe paths into a π-ring and return readout."""
    from fsot_mc.universe_mc import run_universe_monte_carlo

    mc = run_universe_monte_carlo(n_paths=n_paths, seed=seed, store_paths=n_paths)
    ring = PiRing()
    # Use domain_ensemble means as a compact dump if sample_paths thin
    for name, row in (mc.get("domain_ensemble") or {}).items():
        ring.write_mc_state(
            d_eff=float(row["D_eff"]),
            phase=float(row.get("dS_mean", 0.0)),
            S=float(row["S_path_mean"]),
            mass=1.0,
        )
    ring.write_text_as_ring("FSOT universe discovery")
    ring.normalize_mc()
    out = ring.readout()
    out["authority"] = "pi_ring_demo"
    out["mc_paths"] = n_paths
    return out
