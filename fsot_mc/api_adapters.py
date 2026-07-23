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


def fetch_arxiv_search(query: str, *, max_results: int = 3) -> dict[str, Any]:
    """arXiv Atom API — scientific abstract chew (no key)."""
    import urllib.parse
    import xml.etree.ElementTree as ET

    q = urllib.parse.quote(query[:200])
    url = (
        f"http://export.arxiv.org/api/query?search_query=all:{q}"
        f"&start=0&max_results={max_results}"
    )
    cache_key = f"arxiv:{query[:80]}:{max_results}"
    # raw fetch may be XML
    if not online_allowed():
        hit = cache_get(cache_key, max_age_s=None)
        if hit is not None:
            return {"ok": True, "source": "stale_cache", "domain_hint": "Cosmology", "data": hit, "query": query}
        # offline demo stub
        demo = {
            "entries": [
                {
                    "title": "Offline demo: fluid spacetime and multipath observation",
                    "summary": (
                        "Demo abstract for FSOT-MC chew without network. "
                        "Unified scalar engines and cross-domain emergence."
                    ),
                    "id": "demo:arxiv:offline",
                }
            ]
        }
        cache_put(cache_key, demo, meta={"demo": True})
        return {
            "ok": True,
            "source": "demo_offline",
            "domain_hint": "Cosmology",
            "data": demo,
            "query": query,
            "title": demo["entries"][0]["title"],
            "excerpt": demo["entries"][0]["summary"],
            "n_chars": len(demo["entries"][0]["summary"]),
            "free_parameters": 0,
        }

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FSOT-Monte-Carlo-Intelligence/0.7 (research)"},
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = []
        for ent in root.findall("a:entry", ns):
            title = (ent.findtext("a:title", default="", namespaces=ns) or "").strip()
            summary = (ent.findtext("a:summary", default="", namespaces=ns) or "").strip()
            eid = (ent.findtext("a:id", default="", namespaces=ns) or "").strip()
            entries.append({"title": title, "summary": summary[:1200], "id": eid})
        payload = {"entries": entries}
        cache_put(cache_key, payload, meta={"url": url})
        excerpt = " ".join(e["summary"] for e in entries)[:1500]
        title = entries[0]["title"] if entries else query
        return {
            "ok": True,
            "source": "network",
            "domain_hint": "Cosmology",
            "data": payload,
            "query": query,
            "title": title,
            "excerpt": excerpt,
            "n_chars": len(excerpt),
            "free_parameters": 0,
        }
    except Exception as exc:
        hit = cache_get(cache_key, max_age_s=None)
        if hit is not None:
            entries = hit.get("entries") or []
            excerpt = " ".join(e.get("summary", "") for e in entries)[:1500]
            return {
                "ok": True,
                "source": "stale_cache_after_error",
                "error": str(exc),
                "domain_hint": "Cosmology",
                "data": hit,
                "query": query,
                "title": (entries[0].get("title") if entries else query),
                "excerpt": excerpt,
                "n_chars": len(excerpt),
                "free_parameters": 0,
            }
        return {"ok": False, "error": str(exc), "query": query, "domain_hint": "Cosmology"}


def fetch_wikipedia_summary(title: str) -> dict[str, Any]:
    """Wikipedia REST summary — natural language structural chew (no key)."""
    import urllib.parse

    t = urllib.parse.quote(title.replace(" ", "_")[:120])
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{t}"
    cache_key = f"wiki:{title[:80]}"
    r = fetch(cache_key, url, max_age_s=86400 * 7)
    if not r.get("ok"):
        # offline demo
        if not online_allowed():
            demo = {
                "title": title,
                "extract": (
                    f"Offline Wikipedia demo extract for '{title}'. "
                    "General relativity describes gravity as spacetime curvature; "
                    "quantum field theory describes particles and forces. "
                    "FSOT proposes a single fluid scalar architecture across domains."
                ),
            }
            cache_put(cache_key, demo, meta={"demo": True})
            return {
                "ok": True,
                "source": "demo_offline",
                "domain_hint": "Cosmology",
                "data": demo,
                "query": title,
                "title": title,
                "excerpt": demo["extract"],
                "n_chars": len(demo["extract"]),
                "free_parameters": 0,
            }
        return {**r, "domain_hint": "Cosmology", "query": title}
    data = r["data"] if isinstance(r["data"], dict) else {}
    extract = data.get("extract") or data.get("description") or ""
    return {
        **r,
        "domain_hint": "Cosmology",
        "query": title,
        "title": data.get("title") or title,
        "excerpt": str(extract)[:2000],
        "n_chars": len(str(extract)),
        "free_parameters": 0,
    }


def chew_science_text(query: str) -> dict[str, Any]:
    """
    Chew natural + structural science language for the mind.

    Order:
      1) Local arXiv + Simple Wikipedia corpus (offline, FSOT cross-ref)
      2) Live arXiv Atom API (if FSOT_MC_ONLINE=1)
      3) Live Wikipedia REST
      4) Offline demo stubs
    """
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "empty_query"}

    # 1) Local literature corpus (D: dump / simple-wiki indexes)
    try:
        from fsot_mc.literature_corpus import literature_search, literature_status

        st = literature_status()
        if (st.get("arxiv_indexed") or 0) > 0 or (st.get("wiki_indexed") or 0) > 0:
            lit = literature_search(q, arxiv_limit=5, wiki_limit=3, with_fsot=True)
            if lit.get("ok") and lit.get("excerpt"):
                return {
                    "ok": True,
                    "source": "local_literature_corpus",
                    "title": lit.get("title"),
                    "excerpt": lit.get("excerpt"),
                    "n_chars": lit.get("n_chars"),
                    "query": q,
                    "domain_hint": lit.get("domain_hint"),
                    "primary_domains": lit.get("primary_domains"),
                    "literature": lit,
                    "fsot_crossref": True,
                    "free_parameters": 0,
                }
    except Exception as exc:
        lit_err = str(exc)
    else:
        lit_err = None

    # 2) Prefer live arXiv when online
    arx = fetch_arxiv_search(q, max_results=2)
    if arx.get("ok") and arx.get("excerpt") and arx.get("source") != "demo_offline":
        return {
            "ok": True,
            "source": f"arxiv:{arx.get('source')}",
            "title": arx.get("title"),
            "excerpt": arx.get("excerpt"),
            "n_chars": arx.get("n_chars"),
            "query": q,
            "domain_hint": arx.get("domain_hint"),
            "free_parameters": 0,
        }

    # 3) Wikipedia online / offline
    topic = q
    for key in (
        "general relativity",
        "quantum mechanics",
        "cosmology",
        "biology",
        "fluid",
        "spacetime",
    ):
        if key in q.lower():
            topic = key.title() if key != "spacetime" else "Spacetime"
            break
    else:
        words = [w for w in q.replace("?", "").split() if len(w) > 3][:3]
        topic = " ".join(words) if words else "Spacetime"

    wiki = fetch_wikipedia_summary(topic)
    if wiki.get("ok") and wiki.get("source") != "demo_offline":
        return {
            "ok": True,
            "source": f"wikipedia:{wiki.get('source')}",
            "title": wiki.get("title"),
            "excerpt": wiki.get("excerpt"),
            "n_chars": wiki.get("n_chars"),
            "query": q,
            "domain_hint": wiki.get("domain_hint"),
            "free_parameters": 0,
        }

    # 4) Fall back to whatever we got (including demos)
    if arx.get("ok") and arx.get("excerpt"):
        return {
            "ok": True,
            "source": f"arxiv:{arx.get('source')}",
            "title": arx.get("title"),
            "excerpt": arx.get("excerpt"),
            "n_chars": arx.get("n_chars"),
            "query": q,
            "domain_hint": arx.get("domain_hint"),
            "local_literature_error": lit_err,
            "free_parameters": 0,
        }
    if wiki.get("ok"):
        return {
            "ok": True,
            "source": f"wikipedia:{wiki.get('source')}",
            "title": wiki.get("title"),
            "excerpt": wiki.get("excerpt"),
            "n_chars": wiki.get("n_chars"),
            "query": q,
            "domain_hint": wiki.get("domain_hint"),
            "local_literature_error": lit_err,
            "free_parameters": 0,
        }
    return {
        "ok": False,
        "error": "chew_failed",
        "arxiv": arx,
        "wikipedia": wiki,
        "local_literature_error": lit_err,
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
