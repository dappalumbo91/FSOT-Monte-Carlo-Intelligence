"""Documentation RAG for Qwen conversation."""

from __future__ import annotations

from fsot_mc.doc_rag import build_doc_index, search_docs, index_status


def test_build_and_search_docs():
    r = build_doc_index(rebuild=False)
    assert r.get("ok")
    assert r.get("n_chunks", 0) > 50
    st = index_status()
    assert st.get("ok")
    hits = search_docs("Biology fold vitality scalar multipath", limit=5)
    assert hits.get("ok")
    assert hits.get("n_hits", 0) >= 1
    paths = " ".join(h.get("path", "") for h in hits.get("hits") or [])
    assert "tissue" in paths or "Biology" in paths or "biology" in paths.lower()
