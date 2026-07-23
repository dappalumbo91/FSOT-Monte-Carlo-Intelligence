"""
Documentation RAG for Qwen conversation.

Indexes all project markdown the user cares about:
  docs/**/*.md (tissue theses, methodology, claims, audit, …)
  README.md, HANDOFF.md

Retrieval is offline FTS5 under data/doc_index.sqlite (gitignored rebuildable).
free_parameters = 0 — docs never rewrite seeds.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Any

from fsot_mc.paths import PACKAGE_ROOT, data_root

DOC_ROOTS = [
    PACKAGE_ROOT / "docs",
    PACKAGE_ROOT / "README.md",
    PACKAGE_ROOT / "HANDOFF.md",
    PACKAGE_ROOT / "vendor" / "models" / "README.md",
    PACKAGE_ROOT / "vendor" / "literature" / "README.md",
]


def index_db_path() -> Path:
    d = data_root() / "doc_index"
    d.mkdir(parents=True, exist_ok=True)
    return d / "docs_fts.sqlite"


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = path or index_db_path()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def _iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root in DOC_ROOTS:
        if root.is_file() and root.suffix.lower() == ".md":
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.md")))
    # unique
    seen = set()
    out = []
    for f in files:
        try:
            key = str(f.resolve())
        except Exception:
            key = str(f)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


def _chunk_markdown(text: str, *, max_chars: int = 900, overlap: int = 80) -> list[str]:
    """Split on headings / blank lines, then window long sections."""
    text = (text or "").replace("\r\n", "\n").strip()
    if not text:
        return []
    # split on markdown headings
    parts = re.split(r"(?m)(?=^#{1,3}\s)", text)
    chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_chars:
            chunks.append(part)
            continue
        # window long part
        i = 0
        while i < len(part):
            chunks.append(part[i : i + max_chars])
            i += max_chars - overlap
    return chunks


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PACKAGE_ROOT.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def build_doc_index(*, rebuild: bool = False) -> dict[str, Any]:
    """Build/rebuild FTS5 index of all project documentation."""
    db = index_db_path()
    if rebuild and db.is_file():
        try:
            db.unlink()
        except OSError:
            pass

    conn = _connect(db)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            path TEXT NOT NULL,
            title TEXT,
            chunk_ix INTEGER,
            body TEXT NOT NULL,
            content_hash TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            path, title, body,
            content='chunks',
            content_rowid='id',
            tokenize='porter unicode61'
        )
        """
    )
    # clear
    conn.execute("DELETE FROM chunks")
    try:
        conn.execute("DELETE FROM chunks_fts")
    except sqlite3.OperationalError:
        pass

    n_files = 0
    n_chunks = 0
    for fp in _iter_markdown_files():
        try:
            raw = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        n_files += 1
        rel = _rel(fp)
        title = fp.stem.replace("_", " ")
        # first heading
        m = re.search(r"(?m)^#\s+(.+)$", raw)
        if m:
            title = m.group(1).strip()[:200]
        for ix, body in enumerate(_chunk_markdown(raw)):
            h = hashlib.sha1(body.encode("utf-8", errors="ignore")).hexdigest()[:16]
            cur = conn.execute(
                "INSERT INTO chunks(path, title, chunk_ix, body, content_hash) VALUES (?,?,?,?,?)",
                (rel, title, ix, body, h),
            )
            rid = cur.lastrowid
            conn.execute(
                "INSERT INTO chunks_fts(rowid, path, title, body) VALUES (?,?,?,?)",
                (rid, rel, title, body),
            )
            n_chunks += 1

    conn.execute(
        "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
        ("n_files", str(n_files)),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
        ("n_chunks", str(n_chunks)),
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
        ("built", __import__("datetime").datetime.utcnow().isoformat() + "Z"),
    )
    conn.commit()
    conn.close()
    return {
        "ok": True,
        "n_files": n_files,
        "n_chunks": n_chunks,
        "db": str(db),
        "free_parameters": 0,
        "note": "Documentation FTS index for Qwen conversation.",
    }


def index_status() -> dict[str, Any]:
    db = index_db_path()
    if not db.is_file():
        return {"ok": False, "indexed": False, "hint": "python -m fsot_mc docs-index", "db": str(db)}
    conn = _connect(db)
    try:
        n = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        meta = {r[0]: r[1] for r in conn.execute("SELECT key,value FROM meta")}
    except Exception as exc:
        conn.close()
        return {"ok": False, "indexed": False, "error": str(exc), "db": str(db)}
    conn.close()
    return {
        "ok": n > 0,
        "indexed": n > 0,
        "n_chunks": n,
        "meta": meta,
        "db": str(db),
        "free_parameters": 0,
    }


def ensure_doc_index() -> dict[str, Any]:
    st = index_status()
    if st.get("ok") and (st.get("n_chunks") or 0) > 50:
        return st
    return build_doc_index(rebuild=True)


def _fts_query(q: str) -> str:
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-]{1,40}", q or "")
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "what", "how", "does",
        "about", "under", "over", "than", "then", "also", "into", "are", "was",
        "please", "explain", "tell", "me", "you", "your",
    }
    keep = [t for t in toks if t.lower() not in stop][:12]
    if not keep:
        return "FSOT OR spacetime OR multipath"
    # OR query for recall
    return " OR ".join(keep)


def search_docs(
    query: str,
    *,
    limit: int = 8,
    prefer_paths: list[str] | None = None,
) -> dict[str, Any]:
    """
    Retrieve documentation chunks for a user query.
    Auto-builds index if missing.
    """
    st = ensure_doc_index()
    if not st.get("ok") and not st.get("n_chunks"):
        return {"ok": False, "hits": [], "error": "index_empty", "status": st}

    conn = _connect()
    fts_q = _fts_query(query)
    hits: list[dict[str, Any]] = []
    try:
        rows = conn.execute(
            """
            SELECT c.id, c.path, c.title, c.chunk_ix, c.body,
                   bm25(chunks_fts) AS score
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (fts_q, max(limit * 3, 12)),
        ).fetchall()
    except sqlite3.OperationalError:
        # fallback: LIKE on path/title
        like = f"%{(query or 'FSOT').split()[0]}%"
        rows = conn.execute(
            """
            SELECT id, path, title, chunk_ix, body, 0.0 AS score
            FROM chunks
            WHERE path LIKE ? OR title LIKE ? OR body LIKE ?
            LIMIT ?
            """,
            (like, like, like, limit * 2),
        ).fetchall()

    prefer = [p.lower() for p in (prefer_paths or [])]
    scored = []
    for r in rows:
        path = r["path"] if isinstance(r, sqlite3.Row) else r[1]
        title = r["title"] if isinstance(r, sqlite3.Row) else r[2]
        body = r["body"] if isinstance(r, sqlite3.Row) else r[4]
        score = float(r["score"] if isinstance(r, sqlite3.Row) else r[5] or 0)
        bonus = 0.0
        pl = path.lower()
        for pref in prefer:
            if pref and pref in pl:
                bonus -= 2.0  # bm25 lower is better typically - wait bm25 in sqlite fts5 lower is better
        # also boost exact domain slug
        ql = (query or "").lower().replace(" ", "_")
        if ql and ql in pl:
            bonus -= 3.0
        scored.append((score + bonus, path, title, body))

    scored.sort(key=lambda x: x[0])
    seen_paths: dict[str, int] = {}
    for score, path, title, body in scored:
        # diversify: max 2 chunks per file first pass
        n = seen_paths.get(path, 0)
        if n >= 2 and len(hits) >= limit // 2:
            continue
        seen_paths[path] = n + 1
        hits.append(
            {
                "path": path,
                "title": title,
                "score": score,
                "body": body[:1200],
            }
        )
        if len(hits) >= limit:
            break

    # If still thin, force-include domain tissue when domain name appears
    if len(hits) < max(3, limit // 2):
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{3,40}", query or ""):
            slug = token if "_" in token else token
            # try domain file
            cand = PACKAGE_ROOT / "docs" / "tissue" / "domains" / f"{slug}.md"
            if not cand.is_file():
                # Title Case to underscore
                alt = re.sub(r"([a-z])([A-Z])", r"\1_\2", token)
                cand = PACKAGE_ROOT / "docs" / "tissue" / "domains" / f"{alt}.md"
            # case-insensitive scan
            if not cand.is_file():
                ddir = PACKAGE_ROOT / "docs" / "tissue" / "domains"
                if ddir.is_dir():
                    for f in ddir.glob("*.md"):
                        if f.stem.lower() == token.lower() or token.lower() in f.stem.lower():
                            cand = f
                            break
            if cand.is_file():
                rel = _rel(cand)
                if any(h["path"] == rel for h in hits):
                    continue
                body = cand.read_text(encoding="utf-8", errors="replace")[:1200]
                hits.insert(
                    0,
                    {
                        "path": rel,
                        "title": cand.stem,
                        "score": -100.0,
                        "body": body,
                    },
                )
            if len(hits) >= limit:
                break

    conn.close()
    return {
        "ok": True,
        "query": query,
        "fts_query": fts_q,
        "n_hits": len(hits),
        "hits": hits[:limit],
        "index": st,
        "free_parameters": 0,
    }


def format_hits_for_prompt(hits: list[dict[str, Any]], *, max_total_chars: int = 6000) -> str:
    lines = []
    used = 0
    for i, h in enumerate(hits, 1):
        block = (
            f"[DOC {i}] path={h.get('path')}\n"
            f"title={h.get('title')}\n"
            f"{h.get('body')}\n"
        )
        if used + len(block) > max_total_chars:
            break
        lines.append(block)
        used += len(block)
    return "\n".join(lines) if lines else "(no documentation retrieved)"
