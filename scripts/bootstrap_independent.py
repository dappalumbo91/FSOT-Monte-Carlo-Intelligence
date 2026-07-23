#!/usr/bin/env python3
"""
Bootstrap / verify independent workspace (no I:/D:/Desktop required at runtime).

Optional: if external archive/PFLT exist, refresh vendor copies.
Always validates local independence_status().
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from fsot_mc.paths import independence_status, ensure_data_dirs, archive_bundle_dir, pflt_vendor_dir

    ensure_data_dirs()
    st = independence_status()
    print(json.dumps(st, indent=2))

    # Optional literature pack (Git LFS vendor/literature → data/literature if missing)
    try:
        from fsot_mc.literature_corpus import ensure_shipped_literature

        lit = ensure_shipped_literature()
        print("literature_pack:", {k: lit.get(k) for k in ("ok", "copied", "shipped_dir")})
        st_lit = lit.get("status") or {}
        print(
            "  arxiv_indexed=",
            st_lit.get("arxiv_indexed"),
            "wiki_indexed=",
            st_lit.get("wiki_indexed"),
            "shipped=",
            st_lit.get("using_shipped_arxiv"),
        )
    except Exception as exc:
        print("literature_pack: skip", exc)

    # Rebuild atlas from local bundle if needed
    if (archive_bundle_dir() / "data__fsot_domain_navigator.json").is_file():
        from fsot_mc.atlas_build import build_full_atlas
        from fsot_mc.universe_atlas import reload_atlas

        a = build_full_atlas(write=True)
        reload_atlas()
        print(f"atlas core={a['n_core']} ext={a['n_extension']} total={a['n_total']}")

    # Optional refresh from external if present (not required)
    ext_pflt = Path(r"C:\Users\damia\Desktop\pflt\fsot_multilayer_vision.py")
    if ext_pflt.is_file() and not (pflt_vendor_dir() / "fsot_multilayer_vision.py").is_file():
        pflt_vendor_dir().mkdir(parents=True, exist_ok=True)
        shutil.copy2(ext_pflt, pflt_vendor_dir() / "fsot_multilayer_vision.py")
        print("refreshed pflt vision from Desktop")

    st2 = independence_status()
    print("independent=", st2["independent"])
    if not st2["independent"]:
        missing = [k for k, v in st2["checks"].items() if not v]
        print("MISSING:", missing)
        return 1
    print("OK — workspace is self-contained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
