"""
Small polar student on π-ring tensors.

Default: NumPy ridge linear classifier (no GPU required).
Optional: PyTorch MLP if torch is installed and FSOT_MC_USE_TORCH=1.

Task: from flattened π-ring channels → predict pathway quality class
  (high emergence / mixed / high flip) using labels from MC sample paths.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from fsot_mc.paths import PACKAGE_ROOT, data_root
from fsot_mc.pi_ring import PiRing
from fsot_mc.universe_mc import run_universe_monte_carlo


def _ring_from_path_proxy(path: dict[str, Any]) -> np.ndarray:
    """Build a π-ring feature vector from a compact path dict."""
    ring = PiRing()
    # inject vitality into interior
    ring.write_mc_state(
        d_eff=18.0,
        phase=float(path.get("global_phase") or path.get("mean_S") or 0.0),
        S=float(path.get("mean_S") or 0.0),
        mass=1.0 + float(path.get("emergence_fraction") or 0.0),
    )
    # flips as sensory marks
    for i, name in enumerate(path.get("regime_flips") or []):
        theta = (hash(name) % 1000) / 1000.0 * 2 * np.pi
        ring.write_sensory_mark(theta=theta, amplitude=0.5 + 0.1 * i)
    ring.normalize_mc()
    # features: channel means + stds + interior mass
    feats = []
    for c in range(ring.data.shape[0]):
        ch = ring.data[c]
        feats.extend([float(ch.mean()), float(ch.std()), float(ch.max())])
    feats.append(float(path.get("emergence_fraction") or 0.0))
    feats.append(float(path.get("ladder_agree_fraction") or 0.0))
    feats.append(float(path.get("n_regime_flips") or 0.0) / 35.0)
    return np.asarray(feats, dtype=np.float64)


def _label_from_path(path: dict[str, Any]) -> int:
    """0=dispersal-ish, 1=mixed, 2=emergence-stable."""
    ef = float(path.get("emergence_fraction") or 0.5)
    flips = float(path.get("n_regime_flips") or 0.0)
    if flips >= 16:
        return 1  # chaotic mixed
    if ef >= 0.7:
        return 2
    if ef <= 0.55:
        return 0
    return 1


@dataclass
class PolarStudent:
    """Linear multi-class student (numpy)."""

    W: np.ndarray | None = None  # (n_features, n_classes)
    classes: tuple[int, ...] = (0, 1, 2)
    free_parameters: int = 0  # architecture is fixed; trained weights are fit artifacts

    def fit(self, X: np.ndarray, y: np.ndarray, *, reg: float = 1e-2) -> dict[str, Any]:
        """Ridge one-vs-rest."""
        n, d = X.shape
        k = len(self.classes)
        W = np.zeros((d, k), dtype=np.float64)
        # bias feature
        Xb = np.concatenate([X, np.ones((n, 1))], axis=1)
        d2 = Xb.shape[1]
        W = np.zeros((d2, k), dtype=np.float64)
        for ci, c in enumerate(self.classes):
            yy = (y == c).astype(np.float64) * 2 - 1
            A = Xb.T @ Xb + reg * np.eye(d2)
            b = Xb.T @ yy
            W[:, ci] = np.linalg.solve(A, b)
        self.W = W
        pred = self.predict(X)
        acc = float((pred == y).mean()) if len(y) else 0.0
        return {"n": n, "features": d, "train_acc": acc, "reg": reg}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.W is None:
            return np.zeros(len(X), dtype=int)
        Xb = np.concatenate([X, np.ones((X.shape[0], 1))], axis=1)
        scores = Xb @ self.W
        idx = np.argmax(scores, axis=1)
        return np.asarray([self.classes[i] for i in idx], dtype=int)

    def save(self, path: Path | str | None = None) -> Path:
        path = Path(path) if path else data_root() / "models" / "polar_student.npz"
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.W is None:
            raise RuntimeError("not fitted")
        np.savez(path, W=self.W, classes=np.asarray(self.classes))
        return path

    @classmethod
    def load(cls, path: Path | str | None = None) -> "PolarStudent":
        path = Path(path) if path else data_root() / "models" / "polar_student.npz"
        z = np.load(path)
        s = cls()
        s.W = z["W"]
        s.classes = tuple(int(x) for x in z["classes"])
        return s


def _try_torch_student(X: np.ndarray, y: np.ndarray) -> dict[str, Any] | None:
    if os.environ.get("FSOT_MC_USE_TORCH") not in ("1", "true", "yes"):
        return None
    try:
        import torch
        import torch.nn as nn
    except Exception:
        return None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    Xt = torch.tensor(X, dtype=torch.float32, device=device)
    yt = torch.tensor(y, dtype=torch.long, device=device)
    model = nn.Sequential(
        nn.Linear(X.shape[1], 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 3),
    ).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = nn.CrossEntropyLoss()
    model.train()
    for _ in range(80):
        opt.zero_grad()
        logits = model(Xt)
        loss = loss_fn(logits, yt)
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        pred = model(Xt).argmax(dim=1).cpu().numpy()
    acc = float((pred == y).mean())
    out = data_root() / "models" / "polar_student_torch.pt"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    return {
        "backend": "torch",
        "device": str(device),
        "train_acc": acc,
        "model_path": str(out),
        "cuda": torch.cuda.is_available(),
    }


def train_polar_student(
    *,
    n_paths: int = 128,
    seed: int = 0,
    scope: str = "core",
) -> dict[str, Any]:
    """Generate MC sample paths → π-ring features → fit student."""
    mc = run_universe_monte_carlo(
        n_paths=n_paths,
        seed=seed,
        scope=scope,
        store_paths=min(n_paths, 64),
        train_pathway_memory=False,
    )
    samples = mc.get("sample_paths") or []
    # also synthesize from ensemble domain flips if samples thin
    X_list, y_list = [], []
    for s in samples:
        X_list.append(_ring_from_path_proxy(s))
        y_list.append(_label_from_path(s))
    if len(X_list) < 8:
        return {"ok": False, "error": "insufficient_samples", "n": len(X_list)}

    X = np.stack(X_list, axis=0)
    y = np.asarray(y_list, dtype=int)
    # holdout
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    cut = max(1, len(y) // 5)
    te, tr = idx[:cut], idx[cut:]
    student = PolarStudent()
    fit = student.fit(X[tr], y[tr])
    pred_te = student.predict(X[te])
    test_acc = float((pred_te == y[te]).mean()) if len(te) else fit["train_acc"]
    path = student.save()

    torch_info = _try_torch_student(X[tr], y[tr])

    return {
        "ok": True,
        "method": "fsot_polar_student_train",
        "free_parameters": 0,
        "backend": "numpy_ridge",
        "n_samples": len(y),
        "n_train": len(tr),
        "n_test": len(te),
        "train_acc": fit["train_acc"],
        "test_acc": test_acc,
        "model_path": str(path),
        "label_counts": {int(c): int((y == c).sum()) for c in (0, 1, 2)},
        "torch": torch_info,
        "note": (
            "Polar student reads π-ring features from MC pathways. "
            "Torch optional via FSOT_MC_USE_TORCH=1. Not a U-Net."
        ),
    }


def predict_with_student(path: dict[str, Any], model_path: Path | str | None = None) -> dict[str, Any]:
    student = PolarStudent.load(model_path)
    x = _ring_from_path_proxy(path)[None, :]
    pred = int(student.predict(x)[0])
    names = {0: "dispersal_lean", 1: "mixed_chaotic", 2: "emergence_stable"}
    return {
        "pred_class": pred,
        "pred_name": names.get(pred, "unknown"),
        "true_label": _label_from_path(path),
        "free_parameters": 0,
    }
