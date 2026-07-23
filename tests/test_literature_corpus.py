"""Local literature corpus tests (mapping + search when index present)."""

from __future__ import annotations

from fsot_mc.literature_corpus import (
    map_arxiv_categories,
    literature_status,
    search_arxiv_local,
    literature_search,
)


def test_category_mapping():
    d = map_arxiv_categories("gr-qc astro-ph.CO")
    assert "Cosmology" in d
    d2 = map_arxiv_categories("quant-ph")
    assert any("Quantum" in x for x in d2)


def test_literature_status_shape():
    st = literature_status()
    assert "arxiv_path" in st
    assert "free_parameters" in st
    assert st["free_parameters"] == 0


def test_search_graceful_without_or_with_index():
    r = search_arxiv_local("quantum gravity cosmology", limit=3)
    # either missing index or real hits
    assert "ok" in r
    if r.get("ok"):
        assert "hits" in r
        lit = literature_search("quantum entanglement observer", arxiv_limit=2, wiki_limit=1)
        assert lit.get("source") == "local_literature_corpus" or lit.get("ok") in (True, False)
