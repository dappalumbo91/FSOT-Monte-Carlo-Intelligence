"""
Forward journal — true-future scoring of FSOT intelligence commits.

Records predictions at decision time; scores only after horizon elapses.
No look-ahead. free_parameters = 0.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fsot_mc.intrinsic import SEED_POOF
from fsot_mc.monte_carlo import run_dynamic_fsot_monte_carlo
from fsot_mc.paths import journal_dir


@dataclass
class JournalEntry:
    symbol: str
    decided_at: str
    bar_index: int
    price0: float
    horizon: int
    signal: str
    confidence: float
    p_up_obs: float
    solidified: bool
    pattern_key: str
    method: str
    # Filled after horizon
    scored: bool = False
    future_return: float | None = None
    hit: float | None = None  # 1.0 / 0.0 / None if FLAT
    scored_at: str | None = None


@dataclass
class ForwardJournal:
    symbol: str = ""
    entries: list[JournalEntry] = field(default_factory=list)
    free_parameters: int = 0

    def append(self, entry: JournalEntry) -> None:
        self.entries.append(entry)

    def pending(self) -> list[JournalEntry]:
        return [e for e in self.entries if not e.scored]

    def score_with_prices(
        self,
        close: np.ndarray,
        times: np.ndarray | None = None,
    ) -> dict[str, Any]:
        """Score any entry where bar_index + horizon is available in close series."""
        n = len(close)
        newly = 0
        for e in self.entries:
            if e.scored:
                continue
            j = e.bar_index + e.horizon
            if j >= n:
                continue
            r = float(close[j] / close[e.bar_index] - 1.0) if close[e.bar_index] else 0.0
            e.future_return = r
            if e.signal == "LONG":
                e.hit = 1.0 if r > 0 else 0.0
            elif e.signal == "SHORT":
                e.hit = 1.0 if r < 0 else 0.0
            else:
                e.hit = None  # FLAT not scored as direction
            e.scored = True
            e.scored_at = datetime.now(timezone.utc).isoformat()
            newly += 1
        return {"newly_scored": newly, **self.summary()}

    def summary(self) -> dict[str, Any]:
        scored = [e for e in self.entries if e.scored and e.hit is not None]
        solid = [e for e in scored if e.solidified]
        hits = [e.hit for e in scored if e.hit is not None]
        solid_hits = [e.hit for e in solid if e.hit is not None]
        return {
            "symbol": self.symbol,
            "n_entries": len(self.entries),
            "n_scored_directional": len(hits),
            "n_pending": len(self.pending()),
            "directional_accuracy": float(np.mean(hits)) if hits else None,
            "n_solid_commits": len(solid_hits),
            "solid_directional_accuracy": float(np.mean(solid_hits)) if solid_hits else None,
            "n_flat": sum(1 for e in self.entries if e.signal == "FLAT"),
            "free_parameters": 0,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "entries": [asdict(e) for e in self.entries],
            "free_parameters": 0,
            "summary": self.summary(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ForwardJournal":
        j = cls(symbol=str(data.get("symbol", "")))
        for raw in data.get("entries") or []:
            j.entries.append(JournalEntry(**raw))
        return j

    def save(self, path: Path | str | None = None) -> Path:
        path = Path(path) if path else journal_dir() / f"{self.symbol or 'UNK'}_forward_journal.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | str) -> "ForwardJournal":
        path = Path(path)
        if not path.exists():
            return cls()
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))


def run_forward_journal_walk(
    df: pd.DataFrame,
    *,
    symbol: str = "",
    horizon: int = 5,
    step: int = 5,
    n_paths: int = 64,
    window: int = 21,
    max_steps: int | None = 40,
    seed: int = 0,
) -> dict[str, Any]:
    """
    Causal walk: at each i run dynamic MC on past-only data, journal signal,
    then score after horizon using true future prices.
    """
    if df is None or len(df) < window + horizon + 80:
        return {"error": "insufficient_data"}

    close = df["close"].astype(float).values
    journal = ForwardJournal(symbol=symbol)
    i = window + 40
    end = len(df) - horizon - 1
    steps = 0

    while i < end:
        sub = df.iloc[: i + 1].copy()
        mc = run_dynamic_fsot_monte_carlo(
            sub,
            horizon=horizon,
            n_paths=n_paths,
            symbol=symbol,
            seed=seed + i,
            persist=False,
            max_train_bars=min(600, i),
        )
        if mc.get("error"):
            i += step
            continue
        bias = (mc.get("pattern") or {}).get("bias") or {}
        journal.append(
            JournalEntry(
                symbol=symbol,
                decided_at=str(df["time"].iloc[i]) if "time" in df.columns else str(i),
                bar_index=i,
                price0=float(close[i]),
                horizon=horizon,
                signal=str(mc.get("signal", "FLAT")),
                confidence=float(mc.get("confidence", 0.0)),
                p_up_obs=float(mc["ensemble"]["p_up_observed_branch"]),
                solidified=bool(bias.get("solidified", 0) > 0),
                pattern_key=str((mc.get("pattern") or {}).get("key", "")),
                method=str(mc.get("method", "")),
            )
        )
        steps += 1
        if max_steps is not None and steps >= max_steps:
            break
        i += step

    scored = journal.score_with_prices(close)
    # Confidence-gated solid accuracy ( |p-0.5| > Poof )
    conf_hits = [
        e.hit
        for e in journal.entries
        if e.scored
        and e.hit is not None
        and e.solidified
        and abs(e.p_up_obs - 0.5) > SEED_POOF
    ]
    scored["solid_confident_accuracy"] = float(np.mean(conf_hits)) if conf_hits else None
    scored["n_solid_confident"] = len(conf_hits)
    scored["method"] = "fsot_forward_journal_walk"
    scored["horizon"] = horizon
    scored["n_decisions"] = len(journal.entries)
    scored["journal"] = journal.summary()
    scored["free_parameters"] = 0
    try:
        path = journal.save()
        scored["journal_path"] = str(path)
    except Exception as exc:  # noqa: BLE001
        scored["journal_path"] = None
        scored["journal_save_error"] = str(exc)
    return scored
