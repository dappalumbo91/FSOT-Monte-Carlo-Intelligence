# Qwen2.5-7B chat model — where the weights live

FSOT Monte Carlo Intelligence **code and documentation** are on GitHub.  
The **chat model safetensors** are too large for GitHub LFS, so they are hosted on **Hugging Face** and linked from this repo.

---

## Canonical weight location (use this)

| | |
|--|--|
| **Hugging Face model** | [**dappalumbo91/FSOT-Qwen2.5-7B-Instruct**](https://huggingface.co/dappalumbo91/FSOT-Qwen2.5-7B-Instruct) |
| **Direct URL** | https://huggingface.co/dappalumbo91/FSOT-Qwen2.5-7B-Instruct |
| **Repo id (for scripts)** | `dappalumbo91/FSOT-Qwen2.5-7B-Instruct` |
| **Format** | Safetensors (4 shards + tokenizer + config) · ~14 GB |
| **Role** | Conversational “mouth” over tissue theses + docs (RAG) · `free_parameters=0` |
| **Base model** | [Qwen/Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) |

GitHub project: [dappalumbo91/FSOT-Monte-Carlo-Intelligence](https://github.com/dappalumbo91/FSOT-Monte-Carlo-Intelligence)

---

## Download into a clone

```powershell
cd FSOT-Monte-Carlo-Intelligence
pip install -e ".[narrate]"
python scripts/download_qwen25_instruct.py
# equivalent:
# python scripts/download_qwen25_instruct.py --repo dappalumbo91/FSOT-Qwen2.5-7B-Instruct
```

Installs to:

```text
vendor/models/Qwen2.5-7B-Instruct/
```

Then:

```powershell
python -m fsot_mc docs-index --rebuild-index
python -m fsot_mc chat -q "What does the Biology tissue thesis say about S?"
python -m fsot_mc serve --port 8765
# UI: http://127.0.0.1:8765/  → “Talk to the work”
```

Optional: set `HF_TOKEN` for higher rate limits (public model does not require a token for download).

---

## Why weights are not committed to GitHub

| Constraint | Value |
|------------|--------|
| Shard size on disk | ~3.3–3.7 GB each |
| GitHub LFS max file size | **2 GB** |
| Total model size | ~14 GB |

So the **link** lives on GitHub; the **bytes** live on Hugging Face.

---

## Fallback

If the project mirror is unavailable, the download script can fall back to:

https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

```powershell
python scripts/download_qwen25_instruct.py --repo Qwen/Qwen2.5-7B-Instruct
```

---

## License

- Model weights: Apache-2.0 (upstream Qwen2.5-Instruct)  
- This repository’s code / docs: MIT (see [LICENSE](../LICENSE))
