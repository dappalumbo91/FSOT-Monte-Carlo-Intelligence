"""Narration pack builds offline without Qwen weights."""

from __future__ import annotations

from fsot_mc.qwen_narrate import build_narration_pack, model_ready, SYSTEM_PROMPT


def test_system_prompt_doctrine():
    assert "free_parameters" in SYSTEM_PROMPT
    assert "D1D38A" in SYSTEM_PROMPT
    assert "recognized" in SYSTEM_PROMPT.lower() or "recognition" in SYSTEM_PROMPT.lower()


def test_build_pack_offline():
    pack = build_narration_pack(
        query="Explain Cosmology under FSOT multipath",
        node_id="Cosmology",
        n_paths=16,
        chew=False,
        max_theses=2,
    )
    assert pack["free_parameters"] == 0
    assert pack["authority"] == "D1D38A"
    assert pack.get("mind_answer")
    assert pack.get("context_text")
    assert "D1D38A" in pack["context_text"]
    # thesis or at least mind answer present
    assert pack.get("n_theses", 0) >= 0


def test_model_ready_shape():
    st = model_ready()
    assert "ok" in st
    assert "path" in st
    assert st["free_parameters"] == 0


def test_full_mind_answer_without_forcing_qwen():
    from fsot_mc.qwen_narrate import full_mind_answer

    r = full_mind_answer(
        "What is Biology under FSOT?",
        n_paths=12,
        use_qwen=False,
    )
    assert r.get("answer")
    assert r["free_parameters"] == 0
    assert r.get("qwen", {}).get("skipped") or r.get("qwen", {}).get("used") is False
