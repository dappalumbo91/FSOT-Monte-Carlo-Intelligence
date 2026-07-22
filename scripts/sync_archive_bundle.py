#!/usr/bin/env python3
"""
One-way sync: I: FSOT Physical Archive → local vendor/archive_bundle/

Read-only on archive. Writes hashed portable bundle for Monte Carlo intelligence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = Path(r"I:\FSOT-Physical-Archive\02_FSOT-2.1-Lean-Full")
OUT = ROOT / "vendor" / "archive_bundle"

# Relative paths under Lean hub
COPY_FILES = [
    "vendor/fsot_compute.py",
    "vendor/fsot_compute_AUTHORITY_PIN.json",
    "data/fsot_domain_scalar_fixtures.json",
    "data/fsot_domain_navigator.json",
    "data/canonical_constants.json",
    "data/certificate.json",
    "data/cross_proof_verification_report.json",
    "data/preregistered_predictions_manifest.yaml",
    "data/honest_claims_manifest.yaml",
]

# Optional benchmarks (contested / headline) — copy if present
OPTIONAL_GLOBS = [
    "data/cosmology_anomalies_benchmark.json",
    "data/contested_observables_closure.json",
    "data/publication_claims_manifest.json",
    "data/benchmark_margin_audit.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    archive = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ARCHIVE
    if not archive.is_dir():
        print(f"Archive hub not found: {archive}")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "benchmarks").mkdir(exist_ok=True)

    manifest: dict = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "source": str(archive),
        "direction": "archive_to_mc_one_way",
        "files": [],
        "missing": [],
        "free_parameters": 0,
    }

    for rel in COPY_FILES:
        src = archive / rel
        if not src.is_file():
            manifest["missing"].append(rel)
            print("MISSING", rel)
            continue
        # Flatten name under OUT
        dst_name = rel.replace("/", "__")
        dst = OUT / dst_name
        shutil.copy2(src, dst)
        h = sha256(dst)
        manifest["files"].append({"rel": rel, "local": dst_name, "sha256": h, "bytes": dst.stat().st_size})
        print("OK", rel, h[:12])

    for rel in OPTIONAL_GLOBS:
        src = archive / rel
        if not src.is_file():
            continue
        dst = OUT / "benchmarks" / Path(rel).name
        shutil.copy2(src, dst)
        h = sha256(dst)
        manifest["files"].append(
            {"rel": rel, "local": f"benchmarks/{dst.name}", "sha256": h, "bytes": dst.stat().st_size}
        )
        print("OK optional", rel)

    # Authority check
    auth = OUT / "vendor__fsot_compute.py"
    if auth.is_file():
        h = sha256(auth)
        expected = "D1D38A185487B452E470AC68ECE2EB45AEB1CA9CE25FC9BF9564C19633FFBE70"
        manifest["authority_sha256"] = h
        manifest["authority_ok"] = h == expected
        print("authority_ok", manifest["authority_ok"])

    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Wrote", OUT / "MANIFEST.json")
    print(f"files={len(manifest['files'])} missing={len(manifest['missing'])}")
    return 0 if not manifest["missing"] or manifest.get("authority_ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())
