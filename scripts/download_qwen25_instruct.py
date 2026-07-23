#!/usr/bin/env python3
"""
Download Qwen/Qwen2.5-7B-Instruct safetensors into the project tree.

  python scripts/download_qwen25_instruct.py

Destination (default):
  vendor/models/Qwen2.5-7B-Instruct/

Requires: huggingface_hub (pip install huggingface_hub)
Optional: HF_TOKEN for higher rate limits (model is public).

Why not GitHub?
  Shards are ~3.5 GB each (~14 GB total). GitHub LFS max file size is 2 GB,
  so the weights cannot live in this git repo. Hugging Face is the host;
  this script is how every clone attaches the same model to the code.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Project mirror (uploaded under dappalumbo91) then official base as fallback
FSOT_HF_ID = "dappalumbo91/FSOT-Qwen2.5-7B-Instruct"
UPSTREAM_HF_ID = "Qwen/Qwen2.5-7B-Instruct"
HF_ID = FSOT_HF_ID
DEFAULT_DIR = ROOT / "vendor" / "models" / "Qwen2.5-7B-Instruct"


def _load_token() -> str | None:
    for key in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        if os.environ.get(key):
            return os.environ[key].strip()
    # local secret file (never commit) — first hf_… line
    for cand in (ROOT / ".hf_token", Path.home() / ".cache" / "huggingface" / "token"):
        if cand.is_file():
            text = cand.read_text(encoding="utf-8", errors="replace")
            for ln in text.splitlines():
                ln = ln.strip()
                if ln.startswith("hf_"):
                    return ln
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Download Qwen2.5-7B-Instruct safetensors")
    ap.add_argument(
        "--repo",
        default=FSOT_HF_ID,
        help=f"HF model id (default project mirror {FSOT_HF_ID})",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_DIR)
    ap.add_argument(
        "--revision",
        default="main",
        help="HF revision/branch/tag",
    )
    ap.add_argument(
        "--upstream-fallback",
        action="store_true",
        default=True,
        help="If project mirror incomplete, fall back to Qwen/Qwen2.5-7B-Instruct",
    )
    args = ap.parse_args()

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("Install: pip install huggingface_hub")
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    token = _load_token()

    repos = [args.repo]
    if args.upstream_fallback and args.repo != UPSTREAM_HF_ID:
        repos.append(UPSTREAM_HF_ID)

    path = None
    last_err = None
    for repo in repos:
        print(f"Downloading {repo} → {out}")
        print("  (safetensors only; ~14–16 GB). free_parameters=0 · FSOT chat layer")
        try:
            path = snapshot_download(
                repo_id=repo,
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
            # require at least one weight shard
            shards = list(out.glob("*.safetensors"))
            if not shards:
                raise RuntimeError(f"no safetensors in {repo}")
            print("OK:", path, "shards=", len(shards))
            args.repo = repo
            break
        except Exception as exc:
            last_err = exc
            print(f"  failed {repo}: {exc}")
            path = None
    if path is None:
        print("DOWNLOAD_FAILED", last_err)
        return 1
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
