#!/usr/bin/env python3
"""
Package optional assets for GitHub (Git LFS):

  vendor/literature/arxiv_fts.sqlite   — FSOT-priority arXiv subset (default 100k)
  vendor/literature/wiki_fts.sqlite    — Simple Wikipedia FTS
  vendor/literature/MANIFEST.json

Does NOT overwrite data/literature full indexes (keeps local full dump intact).

Also prepares notes for the raw coupling benchmark (tracked via LFS separately).

Usage:
  python scripts/package_optional_assets.py
  python scripts/package_optional_assets.py --max-papers 100000
  python scripts/package_optional_assets.py --wiki-only   # copy existing wiki index
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="Package optional literature for GitHub LFS")
    ap.add_argument("--max-papers", type=int, default=100_000)
    ap.add_argument("--max-articles", type=int, default=50_000)
    ap.add_argument("--wiki-only", action="store_true")
    ap.add_argument("--arxiv-only", action="store_true")
    ap.add_argument("--skip-arxiv", action="store_true")
    args = ap.parse_args()

    from fsot_mc.literature_corpus import (
        build_arxiv_index,
        build_wiki_index,
        literature_dir,
        shipped_literature_dir,
        DEFAULT_ARXIV,
        DEFAULT_WIKI,
    )

    ship = shipped_literature_dir()
    ship.mkdir(parents=True, exist_ok=True)
    results: dict = {"shipped_dir": str(ship), "built_at": datetime.now(timezone.utc).isoformat()}

    # Wiki: prefer copy existing local index (fast) else rebuild
    if not args.arxiv_only:
        local_wiki = literature_dir() / "wiki_fts.sqlite"
        dest_wiki = ship / "wiki_fts.sqlite"
        if local_wiki.is_file() and local_wiki.stat().st_size > 10_000:
            shutil.copy2(local_wiki, dest_wiki)
            results["wiki"] = {
                "ok": True,
                "method": "copy_local",
                "db": str(dest_wiki),
                "mb": round(dest_wiki.stat().st_size / 1e6, 2),
            }
            print(f"wiki: copied local → {dest_wiki} ({results['wiki']['mb']} MB)")
        elif DEFAULT_WIKI.is_dir():
            print(f"wiki: indexing from {DEFAULT_WIKI} …")
            r = build_wiki_index(
                max_articles=None if args.max_articles <= 0 else args.max_articles,
                rebuild=True,
                db_path=dest_wiki,
            )
            results["wiki"] = r
            print("wiki:", {k: r.get(k) for k in ("ok", "n_articles", "db", "error")})
        else:
            results["wiki"] = {"ok": False, "error": "no_local_wiki_index_or_source"}
            print("wiki: SKIP (no source)")

    if args.wiki_only:
        _write_manifest(ship, results)
        return 0 if (results.get("wiki") or {}).get("ok") else 1

    if not args.skip_arxiv:
        dest_arx = ship / "arxiv_fts.sqlite"
        if not DEFAULT_ARXIV.is_file():
            # try copy a smaller existing index if present under ship already
            local_arx = literature_dir() / "arxiv_fts.sqlite"
            results["arxiv"] = {
                "ok": False,
                "error": "arxiv_source_missing",
                "hint": f"Set FSOT_MC_ARXIV_JSON or place dump at {DEFAULT_ARXIV}",
                "local_full_index_mb": round(local_arx.stat().st_size / 1e6, 1) if local_arx.is_file() else None,
            }
            print("arxiv: SKIP (source dump missing) — full local index left untouched")
        else:
            n = None if args.max_papers <= 0 else args.max_papers
            print(f"arxiv: building shipped pack max_papers={n or 'FULL'} → {dest_arx}")
            print("  (does not modify data/literature full index)")
            r = build_arxiv_index(
                max_papers=n,
                rebuild=True,
                fsot_priority=True if n is not None else False,
                db_path=dest_arx,
            )
            results["arxiv"] = r
            if dest_arx.is_file():
                results["arxiv"]["mb"] = round(dest_arx.stat().st_size / 1e6, 2)
            print(
                "arxiv:",
                {k: r.get(k) for k in ("ok", "n_papers", "n_scanned", "seconds", "error", "db")},
            )

    _write_manifest(ship, results)
    print("MANIFEST →", ship / "MANIFEST.json")
    print("Done. Next: git lfs track + commit vendor/literature + coupling benchmark")
    return 0 if (results.get("arxiv") or {}).get("ok") or (results.get("wiki") or {}).get("ok") else 1


def _write_manifest(ship: Path, results: dict) -> None:
    man = {
        "method": "fsot_optional_literature_pack",
        "free_parameters": 0,
        "authority": "D1D38A",
        "note": (
            "Portable FTS indexes for clone reproducibility. "
            "Full multi-million arXiv index is too large for GitHub; "
            "rebuild locally with literature-index --max-papers 0 if you have the OAI dump."
        ),
        "files": {},
        "build": results,
    }
    for name in ("arxiv_fts.sqlite", "wiki_fts.sqlite"):
        p = ship / name
        if p.is_file():
            man["files"][name] = {
                "mb": round(p.stat().st_size / 1e6, 2),
                "bytes": p.stat().st_size,
            }
    (ship / "MANIFEST.json").write_text(json.dumps(man, indent=2), encoding="utf-8")
    (ship / "README.md").write_text(
        "\n".join(
            [
                "# Shipped literature pack (optional)",
                "",
                "Git LFS assets for offline literature search after clone.",
                "",
                "```powershell",
                "git lfs pull",
                "python -c \"from fsot_mc.literature_corpus import ensure_shipped_literature; print(ensure_shipped_literature())\"",
                "python -m fsot_mc literature-status",
                "python -m fsot_mc literature-search -q \"quantum gravity fluid spacetime\"",
                "```",
                "",
                "Full arXiv OAI (~3M papers / multi-GB) is **not** shipped — rebuild:",
                "",
                "```powershell",
                "$env:FSOT_MC_ARXIV_JSON = 'C:\\path\\to\\arxiv-metadata-oai-snapshot.json'",
                "python -m fsot_mc literature-index --max-papers 0 --arxiv-only --rebuild-index",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
