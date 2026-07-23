#!/usr/bin/env python3
"""
Download Qwen/Qwen2.5-7B-Instruct safetensors into the project tree.

  python scripts/download_qwen25_instruct.py

Destination (default):
  vendor/models/Qwen2.5-7B-Instruct/

Requires: huggingface_hub (pip install huggingface_hub)
Optional: HF_TOKEN for higher rate limits (model is public).

Weights are gitignored — not pushed to GitHub.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HF_ID = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_DIR = ROOT / "vendor" / "models" / "Qwen2.5-7B-Instruct"


def main() -> int:
    ap = argparse.ArgumentParser(description="Download Qwen2.5-7B-Instruct safetensors")
    ap.add_argument("--repo", default=HF_ID)
    ap.add_argument("--out", type=Path, default=DEFAULT_DIR)
    ap.add_argument(
        "--revision",
        default="main",
        help="HF revision/branch/tag",
    )
    args = ap.parse_args()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install: pip install huggingface_hub")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

    print(f"Downloading {args.repo} → {out}")
    print("  (safetensors only; ~14–16 GB). free_parameters=0 · FSOT narrate layer")
    path = snapshot_download(
        repo_id=args.repo,
        local_dir=str(out),
        revision=args.revision,
        token=token,
        allow_patterns=[
            "*.json",
            "*.safetensors",
            "*.txt",
            "*.model",
            "tokenizer*",
            "vocab*",
            "merges.txt",
            "LICENSE*",
            "README*",
            "*.jinja",
        ],
        ignore_patterns=["*.bin", "*.msgpack", "*.h5", "flax_model*", "tf_model*"],
    )
    print("OK:", path)
    # write pointer for tools
    meta = out / "FSOT_MC_MODEL.json"
    meta.write_text(
        "{\n"
        f'  "hf_id": "{args.repo}",\n'
        f'  "local_dir": "{out.as_posix()}",\n'
        '  "role": "fsot_narration_mouth",\n'
        '  "free_parameters": 0,\n'
        '  "doctrine": "Articulate MC+tissue pack only; never invent law."\n'
        "}\n",
        encoding="utf-8",
    )
    from fsot_mc.qwen_narrate import model_ready

    print("ready:", model_ready(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
