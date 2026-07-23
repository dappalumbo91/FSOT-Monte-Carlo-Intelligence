"""Tissue scientific documentation tests."""

from __future__ import annotations

from pathlib import Path

from fsot_mc.tissue_docs import TISSUE_ROOT, generate_all_tissue_docs, get_tissue_doc, resolve_doc_path


def test_tissue_library_exists_or_generate():
    # library should already be generated in repo; if not, generate
    if not (TISSUE_ROOT / "INDEX.md").is_file():
        m = generate_all_tissue_docs(write=True)
        assert m["n_docs"] > 100
    assert (TISSUE_ROOT / "INDEX.md").is_file()
    assert (TISSUE_ROOT / "seeds" / "seed_pi.md").is_file()
    assert (TISSUE_ROOT / "seeds" / "law_K.md").is_file()
    # core domain
    bio = TISSUE_ROOT / "domains" / "Biology.md"
    assert bio.is_file()
    text = bio.read_text(encoding="utf-8")
    assert "Mathematical formulation" in text
    assert "Connective tissue" in text
    assert "S =" in text or "S =" in text.replace(" ", "")
    assert "free_parameters" in text


def test_get_tissue_doc_api_shape():
    r = get_tissue_doc("dom_Biology")
    assert r.get("ok") is True
    assert "markdown" in r and "Abstract" in r["markdown"]
    r2 = get_tissue_doc("seed_pi")
    assert r2.get("ok") is True
    assert resolve_doc_path("law_K") is not None
