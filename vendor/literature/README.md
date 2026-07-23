# Shipped literature pack (optional)

Git LFS assets for offline literature search after clone.

```powershell
git lfs pull
python -c "from fsot_mc.literature_corpus import ensure_shipped_literature; print(ensure_shipped_literature())"
python -m fsot_mc literature-status
python -m fsot_mc literature-search -q "quantum gravity fluid spacetime"
```

Full arXiv OAI (~3M papers / multi-GB) is **not** shipped — rebuild:

```powershell
$env:FSOT_MC_ARXIV_JSON = 'C:\path\to\arxiv-metadata-oai-snapshot.json'
python -m fsot_mc literature-index --max-papers 0 --arxiv-only --rebuild-index
```
