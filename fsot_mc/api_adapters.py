"""
Live API adapters — offline-first real-data feeds for universe discovery.

Policy:
  - Always cache under data/api_cache/
  - Portable mode never requires network
  - Adapters normalize → domain fold hints → discovery anchors
  - Never rewrite seed constants

Env:
  FSOT_MC_ONLINE=1  allow network
  FSOT_MC_API_CACHE  override cache root
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fsot_mc.paths import PACKAGE_ROOT

CACHE = Path(os.environ.get("FSOT_MC_API_CACHE") or (PACKAGE_ROOT / "data" / "api_cache"))


def online_allowed() -> bool:
    return os.environ.get("FSOT_MC_ONLINE", "").strip() in ("1", "true", "yes")


def _cache_path(key: str) -> Path:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return CACHE / f"{h}.json"


def cache_get(key: str, *, max_age_s: float | None = 86400.0) -> Any | None:
    p = _cache_path(key)
    if not p.is_file():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if max_age_s is not None:
            ts = raw.get("_cached_at_unix")
            if ts and (time.time() - float(ts)) > max_age_s:
                return None
        return raw.get("payload")
    except Exception:
        return None


def cache_put(key: str, payload: Any, meta: dict | None = None) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = _cache_path(key)
    body = {
        "_cached_at": datetime.now(timezone.utc).isoformat(),
        "_cached_at_unix": time.time(),
        "_key": key,
        "meta": meta or {},
        "payload": payload,
    }
    p.write_text(json.dumps(body, indent=2, default=str), encoding="utf-8")
    return p


def http_get_json(url: str, *, timeout: float = 20.0) -> Any:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FSOT-Monte-Carlo-Intelligence/0.5 (research; offline-first)"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def fetch(
    key: str,
    url: str,
    *,
    force: bool = False,
    max_age_s: float = 86400.0,
) -> dict[str, Any]:
    """Offline-first fetch."""
    if not force:
        hit = cache_get(key, max_age_s=max_age_s)
        if hit is not None:
            return {"ok": True, "source": "cache", "key": key, "data": hit, "url": url}

    if not online_allowed():
        # stale cache ok
        hit = cache_get(key, max_age_s=None)
        if hit is not None:
            return {"ok": True, "source": "stale_cache", "key": key, "data": hit, "url": url}
        return {
            "ok": False,
            "error": "offline_no_cache",
            "key": key,
            "url": url,
            "hint": "Set FSOT_MC_ONLINE=1 or pre-seed cache",
        }

    try:
        data = http_get_json(url)
        cache_put(key, data, meta={"url": url})
        return {"ok": True, "source": "network", "key": key, "data": data, "url": url}
    except Exception as exc:
        hit = cache_get(key, max_age_s=None)
        if hit is not None:
            return {
                "ok": True,
                "source": "stale_cache_after_error",
                "key": key,
                "data": hit,
                "url": url,
                "error": str(exc),
            }
        return {"ok": False, "error": str(exc), "key": key, "url": url}


# ── Concrete adapters ────────────────────────────────────────────────────


def fetch_nasa_apod() -> dict[str, Any]:
    """NASA Astronomy Picture of the Day (demo public API; needs DEMO_KEY or NASA_API_KEY)."""
    key = os.environ.get("NASA_API_KEY", "DEMO_KEY")
    url = f"https://api.nasa.gov/planetary/apod?api_key={key}"
    r = fetch(f"nasa_apod:{key}", url, max_age_s=43200)
    if not r.get("ok"):
        return {**r, "domain_hint": "Astronomy"}
    data = r["data"]
    return {
        **r,
        "domain_hint": "Astronomy",
        "anchor": {
            "title": data.get("title") if isinstance(data, dict) else None,
            "date": data.get("date") if isinstance(data, dict) else None,
            "media_type": data.get("media_type") if isinstance(data, dict) else None,
            "measured_proxy": None,  # qualitative sensory for π-ring text
            "text": (data.get("explanation") or "")[:280] if isinstance(data, dict) else None,
        },
        "free_parameters": 0,
    }


def fetch_open_meteo_sample() -> dict[str, Any]:
    """Open-Meteo free weather (no key) — Meteorology fold."""
    # NYC sample coords
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        "latitude=40.71&longitude=-74.01&current=temperature_2m,wind_speed_10m"
    )
    r = fetch("open_meteo_nyc", url, max_age_s=3600)
    if not r.get("ok"):
        return {**r, "domain_hint": "Meteorology"}
    data = r["data"] if isinstance(r["data"], dict) else {}
    cur = data.get("current") or {}
    temp = cur.get("temperature_2m")
    return {
        **r,
        "domain_hint": "Meteorology",
        "anchor": {
            "temperature_2m": temp,
            "wind_speed_10m": cur.get("wind_speed_10m"),
            "measured_proxy": float(temp) if temp is not None else None,
            "source": "open-meteo",
        },
        "free_parameters": 0,
    }


def fetch_usgs_earthquake_count() -> dict[str, Any]:
    """USGS all-day significant feed summary — Seismology fold."""
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
    r = fetch("usgs_eq_2.5_day", url, max_age_s=1800)
    if not r.get("ok"):
        return {**r, "domain_hint": "Seismology"}
    data = r["data"] if isinstance(r["data"], dict) else {}
    feats = data.get("features") or []
    mags = []
    for f in feats:
        try:
            mags.append(float((f.get("properties") or {}).get("mag")))
        except Exception:
            pass
    mean_mag = sum(mags) / len(mags) if mags else None
    return {
        **r,
        "domain_hint": "Seismology",
        "anchor": {
            "n_events": len(feats),
            "mean_mag": mean_mag,
            "measured_proxy": mean_mag,
            "source": "usgs_geojson",
        },
        "free_parameters": 0,
    }


ADAPTERS: dict[str, Callable[[], dict[str, Any]]] = {
    "nasa_apod": fetch_nasa_apod,
    "open_meteo": fetch_open_meteo_sample,
    "usgs_quakes": fetch_usgs_earthquake_count,
}


def run_api_bundle(*, names: list[str] | None = None, force: bool = False) -> dict[str, Any]:
    """Run selected adapters; return domain-hint anchors for discovery alignment."""
    if force:
        os.environ["FSOT_MC_ONLINE"] = "1"
    selected = names or list(ADAPTERS.keys())
    results = {}
    anchors: dict[str, Any] = {}
    for name in selected:
        fn = ADAPTERS.get(name)
        if not fn:
            results[name] = {"ok": False, "error": "unknown_adapter"}
            continue
        r = fn()
        results[name] = r
        hint = r.get("domain_hint")
        anc = r.get("anchor") or {}
        if hint and r.get("ok") and anc.get("measured_proxy") is not None:
            anchors[hint] = {
                "measured_proxy": anc["measured_proxy"],
                "source": f"api:{name}",
                "kind": "live_or_cached_api",
                "meta": anc,
            }
    return {
        "method": "fsot_api_bundle",
        "free_parameters": 0,
        "online": online_allowed(),
        "cache_dir": str(CACHE),
        "results": results,
        "anchors": anchors,
        "n_ok": sum(1 for v in results.values() if v.get("ok")),
        "note": "Offline-first. FSOT_MC_ONLINE=1 enables network.",
    }


def seed_demo_cache() -> dict[str, Any]:
    """Write demo payloads so offline CI works without network."""
    demo = {
        "nasa_apod:DEMO_KEY": {
            "title": "Demo Nebula",
            "date": "2026-01-01",
            "media_type": "image",
            "explanation": "Offline demo APOD for FSOT π-ring sensory marks.",
        },
        "open_meteo_nyc": {
            "current": {"temperature_2m": 12.5, "wind_speed_10m": 3.2},
        },
        "usgs_eq_2.5_day": {
            "features": [
                {"properties": {"mag": 3.1}},
                {"properties": {"mag": 4.0}},
                {"properties": {"mag": 2.7}},
            ]
        },
    }
    written = []
    for key, payload in demo.items():
        written.append(str(cache_put(key, payload, meta={"demo": True})))
    return {"written": written, "free_parameters": 0}
