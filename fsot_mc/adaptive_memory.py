"""
FSOT-derived adaptive memory — short-term (STM) + long-term (LTM) solidification.

Learning without moving seeds:
  - STM: working buffer of recent observations (session fluid excitation)
  - LTM: engrams that solidify when φ-EWMA accuracy clears seed bars

Mirrors pathway_memory solidify doctrine (0.5+Poof, Fib trials) for *knowledge*
as well as pathway signatures. free_parameters = 0.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fsot_mc.fast import PHI, POOF, PSI_CON, C_FACTOR
from fsot_mc.paths import data_root

SEED_PHI = float(PHI)
SEED_POOF = float(POOF)
SEED_PSI = float(PSI_CON)
SEED_C = float(C_FACTOR)

# Fib capacities / trial floors
STM_CAPACITY = 21  # Fib
LTM_MIN_TRIALS_SOFT = 8  # Fib
LTM_MIN_TRIALS_FULL = 13  # Fib
SOLIDIFY_ACC = 0.5 + SEED_POOF
SOFTEN_ACC = 0.5 + SEED_POOF * SEED_PSI
HIT_THRESHOLD = 0.5 + SEED_POOF * 0.5


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_key(text: str, source: str = "") -> str:
    h = hashlib.sha256(f"{source}|{text.strip().lower()}".encode("utf-8")).hexdigest()[:24]
    return h


def memory_dir() -> Path:
    d = data_root() / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ltm_path() -> Path:
    return memory_dir() / "long_term.jsonl"


@dataclass
class Engram:
    key: str
    text: str
    source: str = "observe"
    domains: list[str] = field(default_factory=list)
    trials: int = 0
    hits: int = 0
    acc_phi: float = 0.5
    strength: float = 0.0
    solidified: bool = False
    soft_fails: int = 0
    quality_last: float = 0.0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    free_parameters: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Engram":
        return cls(
            key=str(d.get("key") or ""),
            text=str(d.get("text") or ""),
            source=str(d.get("source") or "observe"),
            domains=list(d.get("domains") or []),
            trials=int(d.get("trials") or 0),
            hits=int(d.get("hits") or 0),
            acc_phi=float(d.get("acc_phi") or 0.5),
            strength=float(d.get("strength") or 0.0),
            solidified=bool(d.get("solidified")),
            soft_fails=int(d.get("soft_fails") or 0),
            quality_last=float(d.get("quality_last") or 0.0),
            created_at=str(d.get("created_at") or _now()),
            updated_at=str(d.get("updated_at") or _now()),
            free_parameters=0,
        )


def score_observation_quality(
    *,
    text: str,
    domains: list[str] | None = None,
    mc: dict[str, Any] | None = None,
    chew_ok: bool = False,
) -> float:
    """
    Seed-partition quality in ~[0,1]. No free parameters.
    """
    w1 = 1.0 - 1.0 / SEED_PHI  # ~0.382
    w2 = 1.0 / SEED_PHI - 1.0 / (SEED_PHI**2)  # ~0.236
    w3 = 1.0 / (SEED_PHI**2)  # ~0.382 remaining split with w4
    w4 = SEED_POOF  # small pathway/chew term floor
    # renormalize lightly
    s = w1 + w2 + w3 + w4
    w1, w2, w3, w4 = w1 / s, w2 / s, w3 / s, w4 / s

    map_ef = 0.5
    fold_pos = 0.0
    if mc:
        ens = mc.get("ensemble") or {}
        ef = ens.get("emergence_fraction") or {}
        if ef.get("mean") is not None:
            map_ef = float(np_clip(float(ef["mean"]), 0.0, 1.0))
        de = mc.get("domain_ensemble") or {}
        if domains:
            pos = 0
            n = 0
            for d in domains:
                if d in de:
                    n += 1
                    sp = float(de[d].get("S_path_mean", de[d].get("S_canonical", 0.0)))
                    if sp > 0:
                        pos += 1
            fold_pos = pos / n if n else 0.0
        else:
            # any biology/chemistry signal
            for d in ("Biology", "Chemistry", "Cosmology", "Quantum_Mechanics"):
                if d in de:
                    sp = float(de[d].get("S_path_mean", 0.0))
                    fold_pos = max(fold_pos, 1.0 if sp > 0 else 0.0)

    # text substance
    words = len(re.findall(r"[a-zA-Z0-9]{3,}", text or ""))
    substance = float(np_clip(words / 40.0, 0.0, 1.0))
    chew_term = 1.0 if chew_ok else substance

    # pathway-like quality if present on mc sample
    path_q = 0.5
    if mc and (mc.get("sample_paths") or mc.get("pathway_memory")):
        pm = mc.get("pathway_memory") or {}
        if pm.get("n_solidified") is not None:
            path_q = float(np_clip(0.4 + 0.1 * int(pm.get("n_solidified") or 0), 0.0, 1.0))
        samples = mc.get("sample_paths") or []
        if samples:
            path_q = max(
                path_q,
                float(np_clip(float(samples[0].get("ladder_agree_fraction") or 0.5), 0.0, 1.0)),
            )

    q = w1 * map_ef + w2 * fold_pos + w3 * chew_term + w4 * path_q
    return float(np_clip(q, 0.0, 1.0))


def np_clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def phi_ewma(prev: float, hit: float) -> float:
    """φ-EWMA: weight new hit by 1/φ, keep prior by 1-1/φ."""
    a = 1.0 / SEED_PHI
    return float((1.0 - a) * prev + a * hit)


class AdaptiveMemory:
    """
    Dual-store adaptive memory for FSOT Monte Carlo mind.
    """

    def __init__(self, *, stm_capacity: int = STM_CAPACITY, persist: bool = True) -> None:
        self.stm: deque[dict[str, Any]] = deque(maxlen=int(stm_capacity))
        self.ltm: dict[str, Engram] = {}
        self.persist = persist
        self.free_parameters = 0
        if persist:
            self.load()

    def load(self) -> None:
        path = ltm_path()
        if not path.is_file():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                e = Engram.from_dict(d)
                if e.key:
                    self.ltm[e.key] = e
            except Exception:
                continue

    def save(self) -> None:
        if not self.persist:
            return
        path = ltm_path()
        lines = [json.dumps(e.to_dict(), ensure_ascii=False) for e in self.ltm.values()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def observe_text(
        self,
        text: str,
        *,
        source: str = "user",
        domains: list[str] | None = None,
        mc: dict[str, Any] | None = None,
        chew_ok: bool = False,
        force_hit: bool | None = None,
    ) -> dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"ok": False, "error": "empty"}
        domains = domains or []
        key = _content_key(text[:2000], source)
        q = score_observation_quality(text=text, domains=domains, mc=mc, chew_ok=chew_ok)
        hit = 1.0 if (force_hit if force_hit is not None else q >= HIT_THRESHOLD) else 0.0

        stm_item = {
            "t": _now(),
            "key": key,
            "text": text[:800],
            "source": source,
            "domains": domains,
            "quality": q,
            "hit": hit,
        }
        self.stm.appendleft(stm_item)

        e = self.ltm.get(key)
        if e is None:
            e = Engram(key=key, text=text[:2000], source=source, domains=list(domains))
            self.ltm[key] = e
        else:
            # merge domains
            e.domains = sorted(set(e.domains) | set(domains))
            if len(text) > len(e.text):
                e.text = text[:2000]

        e.trials += 1
        e.hits += int(hit)
        e.acc_phi = phi_ewma(e.acc_phi, hit)
        e.quality_last = q
        e.updated_at = _now()

        if e.acc_phi >= SOLIDIFY_ACC and e.trials >= LTM_MIN_TRIALS_FULL:
            e.solidified = True
            e.strength = min(1.0, e.strength + SEED_C * (1.0 / SEED_PHI))
        elif e.acc_phi >= SOLIDIFY_ACC and e.trials >= LTM_MIN_TRIALS_SOFT:
            e.strength = min(1.0, max(e.strength, SEED_POOF + e.acc_phi * SEED_C))
        elif e.acc_phi < SOFTEN_ACC and e.trials >= LTM_MIN_TRIALS_SOFT:
            e.soft_fails += 1
            e.strength = max(0.0, e.strength - SEED_POOF * SEED_C)
            if e.soft_fails >= LTM_MIN_TRIALS_SOFT and e.acc_phi < SOFTEN_ACC:
                e.solidified = False

        self.save()
        return {
            "ok": True,
            "key": key,
            "quality": q,
            "hit": hit,
            "solidified": e.solidified,
            "strength": e.strength,
            "acc_phi": e.acc_phi,
            "trials": e.trials,
            "free_parameters": 0,
        }

    def observe_mc_summary(self, mc: dict[str, Any], *, query: str = "") -> dict[str, Any]:
        ens = mc.get("ensemble") or {}
        ef = ens.get("emergence_fraction") or {}
        text = (
            f"MC n_paths={mc.get('n_paths')} n_domains={mc.get('n_domains')} "
            f"map_emergence_mean={ef.get('mean')} "
            f"query={query[:200]}"
        )
        de = mc.get("domain_ensemble") or {}
        domains = list(de.keys())[:12]
        return self.observe_text(text, source="multipath", domains=domains, mc=mc)

    def observe_turn(
        self,
        query: str,
        answer: str,
        *,
        domains: list[str] | None = None,
        mc: dict[str, Any] | None = None,
        chew: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        chew_ok = bool(chew and chew.get("ok"))
        digest = f"Q: {query[:400]}\nA: {answer[:600]}"
        if chew_ok:
            digest += f"\nChew: {chew.get('title') or ''} {(chew.get('excerpt') or '')[:200]}"
        r1 = self.observe_text(
            digest,
            source="mind_turn",
            domains=domains or [],
            mc=mc,
            chew_ok=chew_ok,
        )
        if chew_ok and chew.get("excerpt"):
            r2 = self.observe_text(
                str(chew.get("excerpt")),
                source=str(chew.get("source") or "chew"),
                domains=domains or [],
                mc=mc,
                chew_ok=True,
            )
        else:
            r2 = None
        if mc:
            r3 = self.observe_mc_summary(mc, query=query)
        else:
            r3 = None
        return {"turn": r1, "chew": r2, "mc": r3, "free_parameters": 0}

    def recall(self, query: str, *, limit: int = 5) -> list[dict[str, Any]]:
        q = (query or "").lower()
        tokens = set(re.findall(r"[a-z0-9]{3,}", q))
        scored: list[tuple[float, Engram]] = []
        for e in self.ltm.values():
            blob = (e.text + " " + " ".join(e.domains) + " " + e.source).lower()
            overlap = sum(1 for t in tokens if t in blob)
            score = overlap * 0.4 + e.strength + (0.5 if e.solidified else 0.0) + e.acc_phi * 0.3
            if overlap or e.solidified or e.strength > SEED_POOF:
                scored.append((score, e))
        # also STM recent
        stm_hits = []
        for item in list(self.stm)[:limit]:
            blob = (item.get("text") or "").lower()
            overlap = sum(1 for t in tokens if t in blob)
            if overlap:
                stm_hits.append(
                    {
                        "store": "stm",
                        "key": item.get("key"),
                        "text": item.get("text"),
                        "source": item.get("source"),
                        "domains": item.get("domains"),
                        "quality": item.get("quality"),
                        "score": float(overlap),
                        "solidified": False,
                    }
                )
        scored.sort(key=lambda x: -x[0])
        out = [
            {
                "store": "ltm",
                "key": e.key,
                "text": e.text[:500],
                "source": e.source,
                "domains": e.domains,
                "strength": e.strength,
                "solidified": e.solidified,
                "acc_phi": e.acc_phi,
                "trials": e.trials,
                "score": float(sc),
            }
            for sc, e in scored[:limit]
        ]
        # merge STM not already in LTM keys
        keys = {x["key"] for x in out}
        for s in stm_hits:
            if s["key"] not in keys:
                out.append(s)
        out.sort(key=lambda x: -float(x.get("score") or 0))
        return out[:limit]

    def summary(self) -> dict[str, Any]:
        solid = [e for e in self.ltm.values() if e.solidified]
        return {
            "stm_size": len(self.stm),
            "stm_capacity": self.stm.maxlen,
            "ltm_size": len(self.ltm),
            "n_solidified": len(solid),
            "solidify_acc_bar": SOLIDIFY_ACC,
            "soften_acc_bar": SOFTEN_ACC,
            "hit_threshold": HIT_THRESHOLD,
            "min_trials_full": LTM_MIN_TRIALS_FULL,
            "ltm_path": str(ltm_path()) if self.persist else None,
            "free_parameters": 0,
            "doctrine": (
                "STM=working fluid; LTM=solidified engrams under φ-EWMA + Poof bars. "
                "Seeds never move."
            ),
        }
