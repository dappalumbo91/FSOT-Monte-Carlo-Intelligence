"""
Local literature corpus — arXiv OAI snapshot + Simple English Wikipedia.

Hooks offline verified research into FSOT connective tissue:
  query → retrieve abstracts/articles → map categories to FSOT domains
  → cross-ref with domain folds / S / green-gate → chew for mind + memory

Default paths (override with env):
  FSOT_MC_ARXIV_JSON  = D:\\training data\\arXiv Dataset\\arxiv-metadata-oai-snapshot.json
  FSOT_MC_WIKI_ROOT   = D:\\training data\\nlp\\simple-wiki

Indexes live under data/literature/ (SQLite FTS5). free_parameters = 0.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fsot_mc.paths import data_root

DEFAULT_ARXIV = Path(
    os.environ.get(
        "FSOT_MC_ARXIV_JSON",
        r"D:\training data\arXiv Dataset\arxiv-metadata-oai-snapshot.json",
    )
)
DEFAULT_WIKI = Path(
    os.environ.get(
        "FSOT_MC_WIKI_ROOT",
        r"D:\training data\nlp\simple-wiki",
    )
)

# Full NeuroLab-core coverage: every arXiv primary maps into the 35-core atlas.
ARXIV_CAT_TO_FSOT: dict[str, list[str]] = {
    # High energy / particle / nuclear
    "hep-th": ["Particle_Physics", "Quantum_Gravity", "Quantum_Mechanics", "High_Energy_Physics"],
    "hep-ph": ["Particle_Physics", "High_Energy_Physics"],
    "hep-ex": ["Particle_Physics", "High_Energy_Physics"],
    "hep-lat": ["Particle_Physics", "Quantum_Mechanics", "Nuclear_Physics"],
    "nucl-th": ["Nuclear_Physics", "Particle_Physics"],
    "nucl-ex": ["Nuclear_Physics"],
    # Gravity / cosmo / astro
    "gr-qc": ["Cosmology", "Quantum_Gravity", "Astrophysics"],
    "astro-ph": ["Astrophysics", "Astronomy", "Cosmology", "Particle_Astrophysics"],
    "astro-ph.CO": ["Cosmology", "Astrophysics", "Particle_Astrophysics"],
    "astro-ph.GA": ["Astrophysics", "Astronomy"],
    "astro-ph.HE": ["Astrophysics", "High_Energy_Physics", "Particle_Astrophysics"],
    "astro-ph.EP": ["Planetary_Science", "Astronomy"],
    "astro-ph.SR": ["Astronomy", "Astrophysics"],
    "astro-ph.IM": ["Astronomy", "Optics"],
    # Quantum
    "quant-ph": ["Quantum_Mechanics", "Quantum_Optics", "Quantum_Computing"],
    # Condensed / materials
    "cond-mat": ["Condensed_Matter", "Materials_Science"],
    "cond-mat.str-el": ["Condensed_Matter"],
    "cond-mat.supr-con": ["Condensed_Matter", "Materials_Science"],
    "cond-mat.mtrl-sci": ["Materials_Science", "Condensed_Matter"],
    "cond-mat.soft": ["Condensed_Matter", "Physical_Chemistry"],
    "cond-mat.mes-hall": ["Condensed_Matter", "Quantum_Mechanics"],
    # Physics subfields → remaining cores
    "physics.atom-ph": ["Atomic_Physics"],
    "physics.optics": ["Optics", "Quantum_Optics"],
    "physics.flu-dyn": ["Fluid_Dynamics"],
    "physics.geo-ph": ["Geophysics", "Seismology"],
    "physics.ao-ph": ["Atmospheric_Physics", "Meteorology", "Oceanography"],
    "physics.atm-clus": ["Atomic_Physics", "Physical_Chemistry"],
    "physics.bio-ph": ["Biology", "Biochemistry", "Molecular_Chemistry"],
    "physics.chem-ph": ["Chemistry", "Physical_Chemistry", "Molecular_Chemistry"],
    "physics.class-ph": ["Electromagnetism", "Thermodynamics", "Fluid_Dynamics"],
    "physics.comp-ph": ["Quantum_Computing", "Condensed_Matter"],
    "physics.data-an": ["Economics", "Sociology"],
    "physics.gen-ph": ["Cosmology", "Quantum_Mechanics", "Thermodynamics"],
    "physics.hist-ph": ["Sociology", "Psychology"],
    "physics.ins-det": ["Particle_Physics", "Optics"],
    "physics.med-ph": ["Biology", "Neuroscience", "Acoustics"],
    "physics.soc-ph": ["Sociology", "Economics", "Psychology"],
    "physics.space-ph": ["Planetary_Science", "Astrophysics", "Atmospheric_Physics"],
    "physics.plasm-ph": ["High_Energy_Physics", "Nuclear_Physics", "Fluid_Dynamics"],
    "physics.acc-ph": ["Particle_Physics", "High_Energy_Physics"],
    "physics.app-ph": ["Materials_Science", "Electromagnetism", "Optics"],
    "physics.ed-ph": ["Psychology", "Sociology"],
    "physics.pop-ph": ["Cosmology", "Astronomy"],
    # Life / earth / social
    "q-bio": ["Biology", "Biochemistry"],
    "q-bio.NC": ["Neuroscience", "Biology", "Psychology"],
    "q-bio.BM": ["Biochemistry", "Biology", "Molecular_Chemistry"],
    "q-bio.GN": ["Biology", "Biochemistry"],
    "q-bio.PE": ["Ecology", "Biology"],
    "q-bio.TO": ["Biology", "Ecology"],
    "q-bio.CB": ["Biology", "Molecular_Chemistry"],
    "q-bio.MN": ["Neuroscience", "Biology"],
    "q-bio.QM": ["Biology", "Biochemistry"],
    "q-fin": ["Economics"],
    "q-fin.EC": ["Economics"],
    "q-fin.GN": ["Economics", "Sociology"],
    "econ": ["Economics"],
    "econ.GN": ["Economics", "Sociology"],
    "econ.TH": ["Economics"],
    # CS / stats / math
    "stat.ML": ["Neuroscience", "Quantum_Computing"],
    "stat.AP": ["Economics", "Sociology", "Ecology"],
    "cs.AI": ["Neuroscience", "Psychology", "Quantum_Computing"],
    "cs.LG": ["Neuroscience", "Quantum_Computing"],
    "cs.CV": ["Optics", "Neuroscience"],
    "cs.CL": ["Neuroscience", "Psychology", "Sociology"],
    "cs.QC": ["Quantum_Computing", "Quantum_Mechanics"],
    "cs.SD": ["Acoustics", "Neuroscience"],
    "cs.NE": ["Neuroscience", "Biology"],
    "eess.AS": ["Acoustics", "Neuroscience"],
    "eess.SP": ["Electromagnetism", "Acoustics", "Optics"],
    "eess.IV": ["Optics", "Neuroscience"],
    "math-ph": ["Quantum_Mechanics", "Particle_Physics", "Thermodynamics"],
    "math.MP": ["Quantum_Mechanics", "Thermodynamics"],
    "math.DS": ["Fluid_Dynamics", "Ecology"],
    "math.PR": ["Thermodynamics", "Economics"],
    "nlin": ["Fluid_Dynamics", "Ecology"],
    "nlin.CD": ["Fluid_Dynamics", "Thermodynamics"],
    "nlin.AO": ["Ecology", "Sociology", "Biology"],
    "nlin.PS": ["Fluid_Dynamics", "Optics"],
    "nlin.SI": ["Fluid_Dynamics", "Quantum_Mechanics"],
    # Chemistry
    "chem": ["Chemistry", "Physical_Chemistry", "Molecular_Chemistry"],
}

FSOT_PRIORITY_PREFIXES = [
    "hep-th",
    "hep-ph",
    "hep-ex",
    "hep-lat",
    "gr-qc",
    "astro-ph",
    "quant-ph",
    "nucl-",
    "cond-mat",
    "physics.",
    "q-bio",
    "q-fin",
    "econ",
    "math-ph",
    "math.",
    "cs.AI",
    "cs.LG",
    "cs.QC",
    "cs.CV",
    "cs.CL",
    "cs.NE",
    "cs.SD",
    "eess.",
    "stat.",
    "nlin",
    "chem",
]


def literature_dir() -> Path:
    d = data_root() / "literature"
    d.mkdir(parents=True, exist_ok=True)
    return d


def arxiv_db_path() -> Path:
    return literature_dir() / "arxiv_fts.sqlite"


def wiki_db_path() -> Path:
    return literature_dir() / "wiki_fts.sqlite"


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def map_arxiv_categories(categories: str) -> list[str]:
    cats = (categories or "").replace(",", " ").split()
    out: list[str] = []
    seen: set[str] = set()
    for c in cats:
        c = c.strip()
        mapped = ARXIV_CAT_TO_FSOT.get(c)
        if not mapped and "." in c:
            mapped = ARXIV_CAT_TO_FSOT.get(c.split(".")[0])
        if not mapped:
            head = c.split(".")[0] if c else ""
            mapped = ARXIV_CAT_TO_FSOT.get(head)
        if mapped:
            for d in mapped:
                if d not in seen:
                    seen.add(d)
                    out.append(d)
    return out or ["Cosmology", "Quantum_Mechanics"]


def _fts_query(q: str, *, mode: str = "or") -> str:
    """
    Build FTS5 query. Default OR of significant tokens (AND is too strict for abstracts).
    """
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]{1,40}", q or "")
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "into", "are", "was",
        "what", "how", "does", "about", "under", "over", "than", "then", "also",
    }
    toks = [t for t in toks if t.lower() not in stop and len(t) > 2]
    if not toks:
        return "quantum OR gravity OR spacetime"
    toks = toks[:10]
    if mode == "and":
        return " AND ".join(f'"{t}"' for t in toks)
    # OR ranking works better with bm25; prefix longest tokens
    return " OR ".join(f'"{t}"' for t in toks)


def _matches_prefixes(categories: str, prefixes: list[str] | None) -> bool:
    if not prefixes:
        return True
    cats = (categories or "").split()
    for c in cats:
        for p in prefixes:
            p2 = p.rstrip("-").rstrip(".")
            if c == p or c.startswith(p) or c.startswith(p2):
                return True
    return False


def init_arxiv_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT
        );
        CREATE TABLE IF NOT EXISTS papers (
          arxiv_id TEXT PRIMARY KEY,
          title TEXT,
          abstract TEXT,
          categories TEXT,
          authors TEXT,
          journal_ref TEXT,
          doi TEXT,
          update_date TEXT,
          fsot_domains TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
          arxiv_id,
          title,
          abstract,
          categories
        );
        """
    )
    conn.commit()


def stream_arxiv_records(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def build_arxiv_index(
    *,
    source: Path | None = None,
    max_papers: int | None = 100_000,
    category_prefixes: list[str] | None = None,
    rebuild: bool = False,
    fsot_priority: bool = True,
) -> dict[str, Any]:
    """
    Stream arXiv JSONL into SQLite FTS5.

    max_papers=None indexes the full dump (slow). Default 100k.
    fsot_priority=True biases toward physics/astro/quant/q-bio categories first.
    """
    source = Path(source or DEFAULT_ARXIV)
    if not source.is_file():
        return {"ok": False, "error": "arxiv_file_missing", "path": str(source)}

    db = arxiv_db_path()
    if rebuild and db.is_file():
        db.unlink()

    conn = _connect(db)
    init_arxiv_db(conn)

    n_exist = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    if n_exist > 1000 and not rebuild:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
        conn.close()
        return {
            "ok": True,
            "source": str(source),
            "db": str(db),
            "n_papers": n_exist,
            "skipped_rebuild": True,
            "meta": meta,
            "free_parameters": 0,
        }

    prefixes = category_prefixes
    if fsot_priority and prefixes is None:
        prefixes = FSOT_PRIORITY_PREFIXES

    n_in = 0
    n_kept = 0
    batch: list[tuple[Any, ...]] = []
    t0 = datetime.now(timezone.utc)

    def flush() -> None:
        nonlocal batch
        if not batch:
            return
        conn.executemany(
            """
            INSERT OR REPLACE INTO papers
            (arxiv_id, title, abstract, categories, authors, journal_ref, doi, update_date, fsot_domains)
            VALUES (?,?,?,?,?,?,?,?,?)
            """,
            batch,
        )
        conn.executemany(
            """
            INSERT INTO papers_fts(arxiv_id, title, abstract, categories)
            VALUES (?,?,?,?)
            """,
            [(b[0], b[1], b[2], b[3]) for b in batch],
        )
        conn.commit()
        batch = []

    for rec in stream_arxiv_records(source):
        n_in += 1
        cats = rec.get("categories") or ""
        if not _matches_prefixes(cats, prefixes):
            continue
        aid = str(rec.get("id") or "").strip()
        if not aid:
            continue
        title = (rec.get("title") or "").replace("\n", " ").strip()
        abstract = (rec.get("abstract") or "").replace("\n", " ").strip()
        domains = map_arxiv_categories(cats)
        update_date = rec.get("update_date")
        if not update_date and isinstance(rec.get("versions"), list) and rec["versions"]:
            update_date = rec["versions"][-1].get("created")
        batch.append(
            (
                aid,
                title[:500],
                abstract[:4000],
                cats,
                (rec.get("authors") or "")[:500],
                rec.get("journal-ref") or rec.get("journal_ref"),
                rec.get("doi"),
                update_date,
                ",".join(domains),
            )
        )
        n_kept += 1
        if len(batch) >= 400:
            flush()
        if max_papers is not None and n_kept >= max_papers:
            break
        if n_in % 200_000 == 0:
            conn.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
                ("progress", f"scanned={n_in} kept={n_kept}"),
            )
            conn.commit()

    flush()
    meta_rows = {
        "source": str(source),
        "n_scanned": str(n_in),
        "n_papers": str(n_kept),
        "max_papers": str(max_papers),
        "built_at": datetime.now(timezone.utc).isoformat(),
        "category_filter": ",".join(prefixes or []),
        "fsot_priority": str(bool(fsot_priority)),
    }
    for k, v in meta_rows.items():
        conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", (k, v))
    conn.commit()
    n_final = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()
    dt = (datetime.now(timezone.utc) - t0).total_seconds()
    return {
        "ok": True,
        "source": str(source),
        "db": str(db),
        "n_scanned": n_in,
        "n_papers": n_final,
        "seconds": round(dt, 2),
        "free_parameters": 0,
        "note": "Local arXiv FTS index for offline FSOT literature cross-reference.",
    }


def search_arxiv_local(query: str, *, limit: int = 8) -> dict[str, Any]:
    db = arxiv_db_path()
    if not db.is_file():
        return {"ok": False, "error": "index_missing", "hint": "python -m fsot_mc literature-index"}
    conn = _connect(db)
    fts_q = _fts_query(query)
    err = None
    try:
        rows = conn.execute(
            """
            SELECT p.arxiv_id, p.title, p.abstract, p.categories, p.authors,
                   p.journal_ref, p.doi, p.fsot_domains,
                   bm25(papers_fts) AS score
            FROM papers_fts
            JOIN papers p ON p.arxiv_id = papers_fts.arxiv_id
            WHERE papers_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (fts_q, int(limit)),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        err = str(exc)
        like = f"%{(query or '')[:40]}%"
        rows = conn.execute(
            """
            SELECT arxiv_id, title, abstract, categories, authors,
                   journal_ref, doi, fsot_domains, 0 AS score
            FROM papers
            WHERE title LIKE ? OR abstract LIKE ?
            LIMIT ?
            """,
            (like, like, int(limit)),
        ).fetchall()

    hits: list[dict[str, Any]] = []
    for r in rows:
        domains = (
            [d for d in (r["fsot_domains"] or "").split(",") if d]
            if r["fsot_domains"]
            else map_arxiv_categories(r["categories"] or "")
        )
        hits.append(
            {
                "id": r["arxiv_id"],
                "title": r["title"],
                "abstract": (r["abstract"] or "")[:1200],
                "categories": r["categories"],
                "authors": r["authors"],
                "journal_ref": r["journal_ref"],
                "doi": r["doi"],
                "url": f"https://arxiv.org/abs/{r['arxiv_id']}",
                "fsot_domains": domains,
                "score": float(r["score"] or 0),
                "source": "local_arxiv_fts",
            }
        )
    n_total = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    conn.close()
    return {
        "ok": True,
        "query": query,
        "fts_query": fts_q,
        "n_index": n_total,
        "n_hits": len(hits),
        "hits": hits,
        "error": err,
        "free_parameters": 0,
    }


def init_wiki_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS articles (
          id INTEGER PRIMARY KEY,
          title TEXT,
          body TEXT,
          fsot_domains TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
          title, body, content='articles', content_rowid='id'
        );
        """
    )
    conn.commit()


def _wiki_domains_from_text(title: str, body: str) -> list[str]:
    blob = f"{title} {body}".lower()
    cues = [
        ("quantum", ["Quantum_Mechanics"]),
        ("relativity", ["Cosmology", "Quantum_Gravity"]),
        ("black hole", ["Astrophysics", "Cosmology"]),
        ("cosmology", ["Cosmology"]),
        ("galaxy", ["Astrophysics", "Astronomy"]),
        ("planet", ["Planetary_Science", "Astronomy"]),
        ("neuron", ["Neuroscience"]),
        ("brain", ["Neuroscience"]),
        ("psychology", ["Psychology", "Neuroscience"]),
        ("sociology", ["Sociology"]),
        ("economy", ["Economics"]),
        ("economics", ["Economics"]),
        ("dna", ["Biology", "Biochemistry"]),
        ("cell ", ["Biology"]),
        ("ecology", ["Ecology", "Biology"]),
        ("chemistry", ["Chemistry"]),
        ("atom", ["Atomic_Physics", "Chemistry"]),
        ("earthquake", ["Seismology", "Geophysics"]),
        ("seismic", ["Seismology", "Geophysics"]),
        ("climate", ["Atmospheric_Physics", "Meteorology"]),
        ("meteorology", ["Meteorology", "Atmospheric_Physics"]),
        ("ocean", ["Oceanography"]),
        ("acoustics", ["Acoustics"]),
        ("sound", ["Acoustics"]),
        ("fluid", ["Fluid_Dynamics"]),
        ("thermodynamic", ["Thermodynamics"]),
        ("electromagnet", ["Electromagnetism"]),
        ("optics", ["Optics"]),
        ("gravity", ["Cosmology", "Quantum_Gravity"]),
        ("particle", ["Particle_Physics"]),
        ("nuclear", ["Nuclear_Physics"]),
    ]
    out: list[str] = []
    for cue, doms in cues:
        if cue in blob:
            for d in doms:
                if d not in out:
                    out.append(d)
    return out[:6] or ["Cosmology"]


def build_wiki_index(
    *,
    root: Path | None = None,
    max_articles: int | None = 50_000,
    rebuild: bool = False,
) -> dict[str, Any]:
    root = Path(root or DEFAULT_WIKI)
    if not root.is_dir():
        return {"ok": False, "error": "wiki_root_missing", "path": str(root)}

    db = wiki_db_path()
    if rebuild and db.is_file():
        db.unlink()
    conn = _connect(db)
    init_wiki_db(conn)
    n_exist = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    if n_exist > 500 and not rebuild:
        conn.close()
        return {
            "ok": True,
            "n_articles": n_exist,
            "db": str(db),
            "skipped_rebuild": True,
            "free_parameters": 0,
        }

    n = 0
    files = sorted(root.rglob("wiki_*"))
    t0 = datetime.now(timezone.utc)
    for fp in files:
        if not fp.is_file():
            continue
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        parts = text.split("\n\n")
        i = 0
        while i < len(parts) - 1:
            title = parts[i].strip()
            body = parts[i + 1].strip()
            i += 2
            if not title or not body or len(title) > 120 or len(title.split()) > 12:
                continue
            domains = _wiki_domains_from_text(title, body[:2000])
            cur = conn.execute(
                "INSERT INTO articles(title, body, fsot_domains) VALUES (?,?,?)",
                (title[:200], body[:5000], ",".join(domains)),
            )
            rid = cur.lastrowid
            conn.execute(
                "INSERT INTO articles_fts(rowid, title, body) VALUES (?,?,?)",
                (rid, title[:200], body[:5000]),
            )
            n += 1
            if n % 2000 == 0:
                conn.commit()
            if max_articles is not None and n >= max_articles:
                break
        if max_articles is not None and n >= max_articles:
            break
    try:
        conn.execute("INSERT INTO articles_fts(articles_fts) VALUES('rebuild')")
    except sqlite3.OperationalError:
        pass
    conn.execute("INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)", ("n_articles", str(n)))
    conn.execute(
        "INSERT OR REPLACE INTO meta(key,value) VALUES (?,?)",
        ("built_at", datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()
    return {
        "ok": True,
        "root": str(root),
        "db": str(db),
        "n_articles": n,
        "seconds": round((datetime.now(timezone.utc) - t0).total_seconds(), 2),
        "free_parameters": 0,
    }


def search_wiki_local(query: str, *, limit: int = 5) -> dict[str, Any]:
    db = wiki_db_path()
    if not db.is_file():
        return {
            "ok": False,
            "error": "wiki_index_missing",
            "hint": "python -m fsot_mc literature-index --wiki",
        }
    conn = _connect(db)
    fts_q = _fts_query(query)
    try:
        rows = conn.execute(
            """
            SELECT a.title, a.body, a.fsot_domains, bm25(articles_fts) AS score
            FROM articles_fts
            JOIN articles a ON a.id = articles_fts.rowid
            WHERE articles_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (fts_q, int(limit)),
        ).fetchall()
    except sqlite3.OperationalError:
        like = f"%{(query or '')[:40]}%"
        rows = conn.execute(
            """
            SELECT title, body, fsot_domains, 0 AS score FROM articles
            WHERE title LIKE ? OR body LIKE ?
            LIMIT ?
            """,
            (like, like, int(limit)),
        ).fetchall()
    hits = []
    for r in rows:
        domains = [d for d in (r["fsot_domains"] or "").split(",") if d]
        hits.append(
            {
                "title": r["title"],
                "extract": (r["body"] or "")[:1500],
                "fsot_domains": domains,
                "score": float(r["score"] or 0),
                "source": "local_simple_wiki_fts",
                "url": f"https://simple.wikipedia.org/wiki/{(r['title'] or '').replace(' ', '_')}",
            }
        )
    n_total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    conn.close()
    return {
        "ok": True,
        "query": query,
        "n_index": n_total,
        "n_hits": len(hits),
        "hits": hits,
        "free_parameters": 0,
    }


def crossref_fsot(hits: list[dict[str, Any]], *, source: str = "arxiv") -> dict[str, Any]:
    """Attach FSOT domain fold S/regime to literature hits."""
    from fsot_mc.universe_atlas import evaluate_domain, get_domain

    domain_cache: dict[str, dict[str, Any]] = {}
    enriched = []
    domain_votes: dict[str, int] = {}

    for h in hits:
        domains = h.get("fsot_domains") or []
        fold_panel = []
        for d in domains[:4]:
            domain_votes[d] = domain_votes.get(d, 0) + 1
            if d not in domain_cache:
                try:
                    base = get_domain(d)
                    try:
                        ev = evaluate_domain(d)
                        domain_cache[d] = {
                            "domain": d,
                            "D_eff": base.get("D_eff"),
                            "S": float(ev["S"]),
                            "regime": ev.get("regime"),
                            "T1": ev.get("T1"),
                            "T2": ev.get("T2"),
                            "T3": ev.get("T3"),
                            "cluster": base.get("cluster"),
                            "median_error_pct": base.get("median_error_pct"),
                        }
                    except Exception:
                        domain_cache[d] = {
                            "domain": d,
                            "D_eff": base.get("D_eff"),
                            "S": float(base.get("S_canonical") or 0),
                            "regime": base.get("regime"),
                            "cluster": base.get("cluster"),
                        }
                except KeyError:
                    domain_cache[d] = {"domain": d, "missing_in_atlas": True}
            fold_panel.append(domain_cache[d])
        enriched.append({**h, "fsot_fold_panel": fold_panel})

    ranked = sorted(domain_votes.items(), key=lambda x: -x[1])
    return {
        "ok": True,
        "source": source,
        "n_hits": len(enriched),
        "hits": enriched,
        "domain_vote": ranked,
        "primary_domains": [d for d, _ in ranked[:6]],
        "crossref_note": (
            "Literature mapped to FSOT folds; S/regime from seed engine. "
            "Does not rewrite seeds — observation stream for multipath reasoning."
        ),
        "free_parameters": 0,
    }


def literature_search(
    query: str,
    *,
    arxiv_limit: int = 6,
    wiki_limit: int = 4,
    with_fsot: bool = True,
) -> dict[str, Any]:
    arx = search_arxiv_local(query, limit=arxiv_limit)
    wiki = search_wiki_local(query, limit=wiki_limit)

    arxiv_x = crossref_fsot(arx.get("hits") or [], source="arxiv") if arx.get("ok") and with_fsot else arx
    wiki_x = crossref_fsot(wiki.get("hits") or [], source="wikipedia") if wiki.get("ok") and with_fsot else wiki

    votes: dict[str, int] = {}
    for d, c in arxiv_x.get("domain_vote") or []:
        votes[d] = votes.get(d, 0) + int(c) * 2
    for d, c in wiki_x.get("domain_vote") or []:
        votes[d] = votes.get(d, 0) + int(c)

    parts: list[str] = []
    for h in (arxiv_x.get("hits") or [])[:3]:
        parts.append(f"[arXiv:{h.get('id')}] {h.get('title')}. {(h.get('abstract') or '')[:400]}")
    for h in (wiki_x.get("hits") or [])[:2]:
        parts.append(f"[Wiki:{h.get('title')}] {(h.get('extract') or '')[:350]}")
    excerpt = " ".join(parts)[:2500]
    title = None
    if arxiv_x.get("hits"):
        title = arxiv_x["hits"][0].get("title")
    elif wiki_x.get("hits"):
        title = wiki_x["hits"][0].get("title")

    primary = [d for d, _ in sorted(votes.items(), key=lambda x: -x[1])[:8]]
    return {
        "ok": bool(arx.get("ok") or wiki.get("ok")),
        "query": query,
        "arxiv": arxiv_x if with_fsot else arx,
        "wikipedia": wiki_x if with_fsot else wiki,
        "primary_domains": primary,
        "title": title or query,
        "excerpt": excerpt,
        "n_chars": len(excerpt),
        "source": "local_literature_corpus",
        "domain_hint": (primary[0] if primary else "Cosmology"),
        "free_parameters": 0,
        "index_status": {
            "arxiv_n": arx.get("n_index"),
            "wiki_n": wiki.get("n_index"),
            "arxiv_ok": arx.get("ok"),
            "wiki_ok": wiki.get("ok"),
        },
    }


def literature_status() -> dict[str, Any]:
    arx_db, wiki_db = arxiv_db_path(), wiki_db_path()
    out: dict[str, Any] = {
        "arxiv_path": str(DEFAULT_ARXIV),
        "arxiv_exists": DEFAULT_ARXIV.is_file(),
        "arxiv_size_gb": round(DEFAULT_ARXIV.stat().st_size / 1e9, 2) if DEFAULT_ARXIV.is_file() else None,
        "wiki_root": str(DEFAULT_WIKI),
        "wiki_exists": DEFAULT_WIKI.is_dir(),
        "arxiv_db": str(arx_db),
        "wiki_db": str(wiki_db),
        "free_parameters": 0,
    }
    if arx_db.is_file():
        conn = _connect(arx_db)
        out["arxiv_indexed"] = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        out["arxiv_meta"] = {r[0]: r[1] for r in conn.execute("SELECT key,value FROM meta")}
        conn.close()
    else:
        out["arxiv_indexed"] = 0
    if wiki_db.is_file():
        conn = _connect(wiki_db)
        out["wiki_indexed"] = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        conn.close()
    else:
        out["wiki_indexed"] = 0
    return out
