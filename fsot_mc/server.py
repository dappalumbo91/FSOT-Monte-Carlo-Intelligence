"""
FSOT Monte Carlo Intelligence — full-stack HTTP API + static frontend.

  python -m fsot_mc serve --port 8765

Serves:
  /                 → frontend (neural / Obsidian graph UI)
  /api/health       → pin + version
  /api/graph        → multi-scale connective graph JSON
  /api/ask          → mind Q&A (POST JSON {query, n_paths, chew})
  /api/readings     → accuracy readings
  /api/memory       → adaptive memory summary + recall
  /api/protocols    → experiment protocol cards
  /api/solidify     → batch chew → LTM
  /api/mc           → multipath ensemble snapshot
  /api/pathways     → live pathway queue / alignment status / scaffold deltas
  /api/pathways/expand → POST gated expansion proposals (JSON)
  /api/queue        → alias of pathways status + recent chat/expand activity
  /api/server/restart → POST restart serve process (UI Ctrl+Shift+R)
"""

from __future__ import annotations

import json
import mimetypes
import os
import subprocess
import sys
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from fsot_mc import __version__
from fsot_mc.paths import PACKAGE_ROOT

FRONTEND_DIR = PACKAGE_ROOT / "frontend"
TISSUE_DIR = PACKAGE_ROOT / "docs" / "tissue"

# Filled by serve(); used for in-process restart
_SERVE_HOST = "127.0.0.1"
_SERVE_PORT = 8765
_HTTP_SERVER: ThreadingHTTPServer | None = None
_RESTART_LOCK = threading.Lock()
_RESTART_SCHEDULED = False


def _json_bytes(obj: Any, code: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(obj, indent=2, default=str).encode("utf-8")
    return code, body, "application/json; charset=utf-8"


def handle_api(method: str, path: str, query: dict[str, list[str]], body: bytes) -> tuple[int, bytes, str]:
    def q1(key: str, default: str = "") -> str:
        return (query.get(key) or [default])[0]

    try:
        if path == "/api/health" and method == "GET":
            from fsot_mc.authority_gate import verify_fsot_gate
            from fsot_mc.qwen_narrate import model_ready

            g = verify_fsot_gate(require_archive=False)
            qst = model_ready()
            return _json_bytes(
                {
                    "ok": g.get("ok"),
                    "version": __version__,
                    "product": "FSOT Monte Carlo Intelligence",
                    "authority": g.get("authority_sha256"),
                    "free_parameters": 0,
                    "frontend": FRONTEND_DIR.is_dir(),
                    "qwen": {
                        "ready": qst.get("ok"),
                        "path": qst.get("path"),
                        "n_safetensors": qst.get("n_safetensors"),
                        "role": "default_articulation_layer",
                    },
                }
            )

        if path == "/api/graph" and method == "GET":
            from fsot_mc.graph_model import build_universe_graph

            n_paths = int(q1("n_paths", "32"))
            seed = int(q1("seed", "0"))
            scope = q1("scope", "full")  # full archive connective tissue by default
            force = q1("rebuild", "0") in ("1", "true", "yes")
            g = build_universe_graph(
                n_paths=min(n_paths, 96),
                seed=seed,
                scope=scope,
                with_memory=True,
                with_predictions=True,
                with_mc=True,
                with_archive_connective=scope == "full",
                force_rebuild_connective=force,
            )
            return _json_bytes(g)

        if path == "/api/connective" and method == "GET":
            from fsot_mc.archive_connective import get_connective_tissue

            force = q1("rebuild", "0") in ("1", "true", "yes")
            t = get_connective_tissue(force_rebuild=force)
            # summary without full node dump unless requested
            if q1("full", "0") not in ("1", "true", "yes"):
                return _json_bytes(
                    {
                        k: t.get(k)
                        for k in (
                            "version",
                            "method",
                            "n_nodes",
                            "n_edges",
                            "n_core",
                            "n_extension",
                            "n_problem_routes",
                            "n_with_error",
                            "n_green_gate",
                            "edge_type_counts",
                            "coupling_raw_edge_count",
                            "coupling_raw_node_count",
                            "expansion_summary",
                            "scaffold_deltas",
                            "source",
                            "note",
                            "free_parameters",
                        )
                    }
                )
            return _json_bytes(t)

        # ── Live pathway / expansion queue (monitor while UI runs) ─────────
        if path in ("/api/pathways", "/api/queue") and method == "GET":
            from fsot_mc.pathway_alignment import load_scaffold_deltas, pathway_status
            from fsot_mc.formal_bridge import formal_status
            from pathlib import Path

            st = pathway_status()
            deltas = load_scaffold_deltas()
            # recent scaffold edges (tail)
            recent_edges = list(deltas.get("edges") or [])[-int(q1("limit", "25")) :]
            recent_nodes = list(deltas.get("nodes") or [])[-int(q1("limit", "25")) :]
            # pending / promoted obligation filenames
            root = Path(__file__).resolve().parents[1] / "data"
            pending = sorted((root / "obligations_pending").glob("*.json")) if (root / "obligations_pending").is_dir() else []
            promoted = sorted((root / "obligations_promoted").glob("*.json")) if (root / "obligations_promoted").is_dir() else []
            return _json_bytes(
                {
                    "ok": True,
                    "free_parameters": 0,
                    "status": st,
                    "formal": formal_status(),
                    "queue": {
                        "scaffold_edges_total": deltas.get("n_edges"),
                        "scaffold_nodes_total": deltas.get("n_nodes"),
                        "pending_obligations": len(pending),
                        "promoted_obligations": len(promoted),
                        "pending_sample": [p.name for p in pending[-15:]],
                        "promoted_sample": [p.name for p in promoted[-15:]],
                        "recent_scaffold_edges": recent_edges,
                        "recent_scaffold_nodes": recent_nodes,
                    },
                    "monitor_hint": (
                        "GET /api/queue while serve runs. "
                        "POST /api/pathways/expand with {proposals:[...]} or connect-text. "
                        "POST /api/ask mode=chat to talk to Qwen; pathway_expand field if expansion triggered."
                    ),
                }
            )

        if path == "/api/pathways/expand" and method == "POST":
            from fsot_mc.pathway_alignment import propose_expansion_from_text, rebuild_tissue_with_deltas

            data = json.loads(body.decode("utf-8") or "{}")
            # accept raw text, or proposals list, or full JSON object as string
            if data.get("proposals"):
                blob = json.dumps({"proposals": data["proposals"]})
            else:
                blob = str(data.get("text") or data.get("query") or data.get("message") or "")
            if not blob.strip():
                return _json_bytes({"ok": False, "error": "text_or_proposals_required"}, 400)
            r = propose_expansion_from_text(
                blob,
                source=str(data.get("source") or "api"),
                run_court=bool(data.get("run_court", True)),
            )
            if r.get("ok") and data.get("rebuild", True):
                r["rebuild"] = rebuild_tissue_with_deltas(force=True)
            return _json_bytes(r)

        if path in ("/api/server/restart", "/api/restart") and method == "POST":
            # Schedule process restart; client should poll /api/health then reload.
            r = schedule_server_restart()
            code = 200 if r.get("ok") else 409
            return _json_bytes(r, code)

        if path in ("/api/server/status", "/api/server") and method == "GET":
            return _json_bytes(
                {
                    "ok": True,
                    "host": _SERVE_HOST,
                    "port": _SERVE_PORT,
                    "version": __version__,
                    "restart_scheduled": _RESTART_SCHEDULED,
                    "pid": os.getpid(),
                    "shortcuts": {
                        "reload_graph": "Ctrl+R (UI)",
                        "restart_server": "Ctrl+Shift+R or ⟳ Restart button",
                    },
                    "free_parameters": 0,
                }
            )

        if path == "/api/ask" and method == "POST":
            """
            Default UI path = DOCUMENTATION CHAT with Qwen (reads tissue + docs).
            mode=mind → legacy multipath-only / full_mind_answer pipeline.
            """
            data = json.loads(body.decode("utf-8") or "{}")
            mode = str(data.get("mode") or "chat").lower()
            query = str(data.get("query") or data.get("message") or "").strip()
            if not query:
                return _json_bytes({"ok": False, "error": "query_required"}, 400)

            # Prefer real documentation conversation
            if mode in ("chat", "docs", "converse", "default", ""):
                from fsot_mc.qwen_chat import chat as qwen_chat

                r = qwen_chat(
                    query,
                    session_id=str(data.get("session_id") or "ui"),
                    history=data.get("history"),
                    max_new_tokens=int(data.get("max_tokens") or 450),
                    temperature=float(data.get("temperature") or 0.45),
                )
                return _json_bytes(
                    {
                        "ok": r.get("ok"),
                        "error": r.get("error"),
                        "detail": r.get("detail"),
                        "answer": r.get("reply") or r.get("answer"),
                        "reply": r.get("reply"),
                        "qwen": r.get("qwen")
                        or {
                            "used": bool(r.get("ok")),
                            "ready": True,
                            "ok": bool(r.get("ok")),
                        },
                        "docs_used": r.get("docs_used"),
                        "n_docs": r.get("n_docs"),
                        "domains": r.get("domains"),
                        "live_scalars": r.get("live_scalars"),
                        "method": r.get("method") or "fsot_qwen_doc_chat",
                        "session_id": r.get("session_id"),
                        "free_parameters": 0,
                        "note": r.get("note"),
                    }
                )

            # Legacy multipath mind (+ optional narrate pack)
            from fsot_mc.qwen_narrate import full_mind_answer

            use_qwen = data.get("narrate", data.get("use_qwen", True))
            if isinstance(use_qwen, str):
                use_qwen = use_qwen.lower() not in ("0", "false", "no")
            r = full_mind_answer(
                query,
                n_paths=int(data.get("n_paths") or 32),
                chew=data.get("chew"),
                node_id=data.get("node_id") or data.get("node"),
                use_qwen=bool(use_qwen),
                max_new_tokens=int(data.get("max_tokens") or 400),
                temperature=float(data.get("temperature") or 0.35),
            )
            th = r.get("thinking") or {}
            return _json_bytes(
                {
                    "error": r.get("error"),
                    "answer": r.get("answer"),
                    "answer_raw": r.get("answer_raw"),
                    "narration": r.get("narration"),
                    "qwen": r.get("qwen"),
                    "pack_summary": r.get("pack_summary"),
                    "thinking": {
                        "routed_domains": th.get("routed_domains"),
                        "n_paths": th.get("n_paths"),
                        "focus_scalars": th.get("focus_scalars"),
                        "adaptive_memory": th.get("adaptive_memory"),
                        "emergence_fraction_definition": th.get(
                            "emergence_fraction_definition"
                        ),
                    },
                    "session": r.get("session"),
                    "method": r.get("method"),
                    "free_parameters": 0,
                }
            )

        if path == "/api/chat" and method == "POST":
            from fsot_mc.qwen_chat import chat as qwen_chat, clear_history

            data = json.loads(body.decode("utf-8") or "{}")
            if data.get("clear"):
                clear_history(str(data.get("session_id") or "ui"))
                return _json_bytes({"ok": True, "cleared": True, "free_parameters": 0})
            msg = str(data.get("message") or data.get("query") or "").strip()
            if not msg:
                return _json_bytes({"ok": False, "error": "message_required"}, 400)
            r = qwen_chat(
                msg,
                session_id=str(data.get("session_id") or "ui"),
                history=data.get("history"),
                max_new_tokens=int(data.get("max_tokens") or 450),
                temperature=float(data.get("temperature") or 0.45),
            )
            return _json_bytes(r)

        if path == "/api/docs/search" and method == "GET":
            from fsot_mc.doc_rag import search_docs, index_status

            q = q1("q", "") or q1("query", "")
            if not q:
                return _json_bytes({"ok": True, "index": index_status(), "hits": []})
            return _json_bytes(search_docs(q, limit=int(q1("limit", "8"))))

        if path == "/api/docs/index" and method in ("POST", "GET"):
            from fsot_mc.doc_rag import build_doc_index

            rebuild = q1("rebuild", "0") in ("1", "true", "yes")
            if method == "POST" and body:
                data = json.loads(body.decode("utf-8") or "{}")
                rebuild = bool(data.get("rebuild", rebuild))
            return _json_bytes(build_doc_index(rebuild=rebuild))

        if path == "/api/narrate/status" and method == "GET":
            from fsot_mc.qwen_narrate import model_ready, DEFAULT_HF_ID, model_dir

            st = model_ready()
            st["hf_id"] = DEFAULT_HF_ID
            st["model_dir"] = str(model_dir())
            return _json_bytes(st)

        if path == "/api/narrate" and method == "POST":
            from fsot_mc.qwen_narrate import narrate, build_narration_pack, model_ready

            data = json.loads(body.decode("utf-8") or "{}")
            query = str(data.get("query") or data.get("q") or "").strip()
            if not query:
                return _json_bytes({"ok": False, "error": "query_required"}, 400)
            node_id = data.get("node_id") or data.get("node")
            pack_only = bool(data.get("pack_only"))
            if pack_only or not model_ready().get("ok"):
                pack = build_narration_pack(
                    query=query,
                    node_id=str(node_id) if node_id else None,
                    n_paths=int(data.get("n_paths") or 32),
                    chew=bool(data.get("chew")),
                )
                return _json_bytes(
                    {
                        "ok": False if pack_only else False,
                        "pack_only": True,
                        "model_ready": model_ready().get("ok"),
                        "query": query,
                        "mind_answer": pack.get("mind_answer"),
                        "pack_summary": {
                            "n_theses": pack.get("n_theses"),
                            "routed_domains": pack.get("routed_domains"),
                        },
                        "context_preview": (pack.get("context_text") or "")[:2000],
                        "free_parameters": 0,
                        "hint": "Download weights: python scripts/download_qwen25_instruct.py",
                    }
                )
            r = narrate(
                query,
                node_id=str(node_id) if node_id else None,
                n_paths=int(data.get("n_paths") or 32),
                chew=bool(data.get("chew")),
                max_new_tokens=int(data.get("max_tokens") or 700),
                temperature=float(data.get("temperature") or 0.4),
            )
            return _json_bytes(
                {
                    "ok": r.get("ok"),
                    "error": r.get("error"),
                    "detail": r.get("detail"),
                    "narration": r.get("narration"),
                    "mind_answer": r.get("mind_answer"),
                    "pack_summary": r.get("pack_summary"),
                    "model": r.get("model"),
                    "free_parameters": 0,
                    "note": r.get("note"),
                }
            )

        if path == "/api/readings" and method == "GET":
            from fsot_mc.accuracy_gate import run_accuracy_readings

            r = run_accuracy_readings(
                n_paths=int(q1("n_paths", "32")),
                seed=int(q1("seed", "0")),
                with_multipath=True,
                write=False,
            )
            return _json_bytes(
                {
                    "headline": r.get("headline"),
                    "integrity_score": r.get("integrity_score"),
                    "acceptable_margins": r.get("acceptable_margins"),
                    "archive_margin_audit": {
                        k: (r.get("archive_margin_audit") or {}).get(k)
                        for k in (
                            "green_gate_pass_count",
                            "green_gate_fail_count",
                            "all_green",
                            "pooled_median_of_domain_medians_pct",
                            "max_pooled_domain_median_pct",
                        )
                    },
                    "contested_panel": {
                        k: (r.get("contested_panel") or {}).get(k)
                        for k in (
                            "verdict",
                            "fsot_pooled_median_error_pct",
                            "current_model_baseline_pct",
                            "n_within_0_5pct",
                            "n_observables",
                        )
                    },
                    "multipath_exploratory": r.get("multipath_exploratory"),
                    "free_parameters": 0,
                }
            )

        if path == "/api/memory" and method == "GET":
            from fsot_mc.adaptive_memory import AdaptiveMemory

            mem = AdaptiveMemory()
            q = q1("q", "")
            out = {"summary": mem.summary(), "recall": mem.recall(q, limit=12) if q else [], "free_parameters": 0}
            return _json_bytes(out)

        if path == "/api/protocols" and method == "GET":
            from fsot_mc.experiment_protocols import get_protocol, list_protocol_cards

            pid = q1("id", "")
            if pid:
                card = get_protocol(pid)
                return _json_bytes({"ok": card is not None, "card": card})
            return _json_bytes(list_protocol_cards(query=q1("q", ""), limit=int(q1("limit", "15"))))

        if path == "/api/solidify" and method in ("POST", "GET"):
            from fsot_mc.chew_solidify import solidify_corpus, solidify_topic

            if method == "POST" and body:
                data = json.loads(body.decode("utf-8") or "{}")
                topics = data.get("topics")
                if data.get("topic"):
                    r = solidify_topic(str(data["topic"]), n_paths=int(data.get("n_paths") or 16))
                    return _json_bytes(r)
                r = solidify_corpus(topics, n_paths=int(data.get("n_paths") or 16))
                return _json_bytes(r)
            # GET: default small corpus
            r = solidify_corpus(n_paths=int(q1("n_paths", "12")), seed=int(q1("seed", "0")))
            return _json_bytes(r)

        if path == "/api/mc" and method == "GET":
            from fsot_mc.universe_mc import run_universe_monte_carlo

            mc = run_universe_monte_carlo(
                n_paths=int(q1("n_paths", "48")),
                seed=int(q1("seed", "0")),
                store_paths=8,
                train_pathway_memory=False,
            )
            pub = {k: v for k, v in mc.items() if not k.startswith("_") and k != "sample_paths"}
            pub["sample_paths"] = (mc.get("sample_paths") or [])[:4]
            return _json_bytes(pub)

        if path == "/api/tissue" and method == "GET":
            from fsot_mc.tissue_docs import TISSUE_ROOT, get_tissue_doc

            node_id = q1("id", "")
            if node_id:
                return _json_bytes(get_tissue_doc(node_id))
            man = TISSUE_ROOT / "manifest.json"
            if man.is_file():
                return _json_bytes(json.loads(man.read_text(encoding="utf-8")))
            return _json_bytes(
                {
                    "ok": False,
                    "error": "tissue_not_generated",
                    "hint": "python -m fsot_mc tissue-docs",
                }
            )

        if path.startswith("/api/tissue/") and method == "GET":
            from fsot_mc.tissue_docs import get_tissue_doc

            node_id = path[len("/api/tissue/") :]
            node_id = urllib.parse.unquote(node_id)
            return _json_bytes(get_tissue_doc(node_id))

        if path == "/api/tissue-generate" and method in ("POST", "GET"):
            from fsot_mc.tissue_docs import generate_all_tissue_docs

            m = generate_all_tissue_docs(write=True)
            return _json_bytes({"ok": True, **m})

        if path == "/api/literature" and method == "GET":
            from fsot_mc.literature_corpus import literature_search, literature_status

            q = q1("q", "") or q1("query", "")
            if not q:
                return _json_bytes(literature_status())
            return _json_bytes(
                literature_search(
                    q,
                    arxiv_limit=int(q1("arxiv_limit", "6")),
                    wiki_limit=int(q1("wiki_limit", "4")),
                    with_fsot=True,
                )
            )

        if path == "/api/literature/status" and method == "GET":
            from fsot_mc.literature_corpus import literature_status

            return _json_bytes(literature_status())

        return _json_bytes({"ok": False, "error": "not_found", "path": path}, 404)
    except Exception as exc:
        return _json_bytes(
            {"ok": False, "error": str(exc), "trace": traceback.format_exc()[-1500:]},
            500,
        )


class FSOTHandler(BaseHTTPRequestHandler):
    server_version = f"FSOT-MC/{__version__}"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[fsot-serve] {self.address_string()} {fmt % args}")

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(204, b"", "text/plain")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            code, body, ct = handle_api("GET", path, query, b"")
            self._send(code, body, ct)
            return

        # static frontend
        rel = "index.html" if path in ("/", "") else path.lstrip("/")
        # prevent path escape
        target = (FRONTEND_DIR / rel).resolve()
        if not str(target).startswith(str(FRONTEND_DIR.resolve())):
            self._send(403, b"forbidden", "text/plain")
            return
        if not target.is_file():
            self._send(404, b"not found", "text/plain")
            return
        data = target.read_bytes()
        ct = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self._send(200, data, ct)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        query = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        if path.startswith("/api/"):
            code, body_out, ct = handle_api("POST", path, query, body)
            self._send(code, body_out, ct)
            return
        self._send(404, b"not found", "text/plain")


def _warm_qwen_background() -> None:
    """Load Qwen in a daemon thread so first UI ask is not cold."""

    def _run() -> None:
        try:
            from fsot_mc.qwen_narrate import model_ready, load_model

            st = model_ready()
            if not st.get("ok"):
                print(f"[fsot-serve] Qwen weights missing — {st.get('hint')}")
                return
            print("[fsot-serve] warming Qwen2.5-7B (4-bit)…")
            r = load_model(force=False)
            if r.get("ok"):
                print(f"[fsot-serve] Qwen ready mode={r.get('load_mode')} device={r.get('device')}")
            else:
                print(f"[fsot-serve] Qwen warm failed: {r.get('error')} {r.get('detail')}")
        except Exception as exc:
            print(f"[fsot-serve] Qwen warm error: {exc}")

    threading.Thread(target=_run, name="qwen-warm", daemon=True).start()


def schedule_server_restart() -> dict[str, Any]:
    """
    Restart the serve process in-place (new console on Windows).

    Flow: respond to client → wait for port free → spawn new serve → exit.
    """
    global _RESTART_SCHEDULED
    with _RESTART_LOCK:
        if _RESTART_SCHEDULED:
            return {
                "ok": True,
                "already_scheduled": True,
                "host": _SERVE_HOST,
                "port": _SERVE_PORT,
                "note": "Restart already in progress — wait for /api/health.",
            }
        _RESTART_SCHEDULED = True

    host, port = _SERVE_HOST, int(_SERVE_PORT)
    root = str(PACKAGE_ROOT)
    py = sys.executable

    def _worker() -> None:
        print(f"[fsot-serve] restart scheduled — spawning new process on {host}:{port}")
        time.sleep(0.45)
        # Child waits until this process releases the port, then starts serve.
        waiter = f"""
import os, sys, time, socket, subprocess
host = {host!r}
port = {port}
root = {root!r}
py = {py!r}
env = os.environ.copy()
env['PYTHONPATH'] = root
# preserve common FSOT env if parent had them
for _ in range(60):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.close()
        break
    except OSError:
        try:
            s.close()
        except Exception:
            pass
        time.sleep(0.25)
else:
    sys.stderr.write('fsot-restart: port still busy\\n')
os.chdir(root)
args = [py, '-m', 'fsot_mc', 'serve', '--host', host, '--port', str(port)]
if sys.platform == 'win32':
    flags = 0x00000010  # CREATE_NEW_CONSOLE
    subprocess.Popen(args, cwd=root, env=env, creationflags=flags, close_fds=True)
else:
    subprocess.Popen(args, cwd=root, env=env, start_new_session=True)
"""
        try:
            if sys.platform == "win32":
                flags = 0x00000010 | 0x00000200  # NEW_CONSOLE | NEW_PROCESS_GROUP
                subprocess.Popen(
                    [py, "-c", waiter],
                    cwd=root,
                    env=os.environ.copy(),
                    creationflags=flags,
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    [py, "-c", waiter],
                    cwd=root,
                    env=os.environ.copy(),
                    start_new_session=True,
                )
        except Exception as exc:
            print(f"[fsot-serve] restart spawn failed: {exc}")
            return

        # Shut down this server
        time.sleep(0.15)
        httpd = _HTTP_SERVER
        try:
            if httpd is not None:
                threading.Thread(target=httpd.shutdown, daemon=True).start()
        except Exception as exc:
            print(f"[fsot-serve] shutdown warn: {exc}")
        time.sleep(0.35)
        print("[fsot-serve] exiting for restart.")
        os._exit(0)

    threading.Thread(target=_worker, name="fsot-restart", daemon=True).start()
    return {
        "ok": True,
        "already_scheduled": False,
        "host": host,
        "port": port,
        "pid": os.getpid(),
        "note": "Server restarting — poll GET /api/health then reload the page.",
        "poll_url": f"http://{host}:{port}/api/health",
        "free_parameters": 0,
    }


def serve(*, host: str = "127.0.0.1", port: int = 8765, warm_qwen: bool = True) -> None:
    global _SERVE_HOST, _SERVE_PORT, _HTTP_SERVER, _RESTART_SCHEDULED
    _SERVE_HOST = host
    _SERVE_PORT = int(port)
    _RESTART_SCHEDULED = False
    if not FRONTEND_DIR.is_dir():
        raise SystemExit(f"Frontend missing: {FRONTEND_DIR}")
    if warm_qwen and os.environ.get("FSOT_MC_QWEN_WARM", "1") not in ("0", "false", "no"):
        _warm_qwen_background()
    httpd = ThreadingHTTPServer((host, port), FSOTHandler)
    _HTTP_SERVER = httpd
    print(f"FSOT Monte Carlo Intelligence  v{__version__}")
    print(f"  visual:  http://{host}:{port}/")
    print(f"  health:  http://{host}:{port}/api/health")
    print(f"  graph:   http://{host}:{port}/api/graph")
    print(f"  ask:     POST /api/ask  (mind + Qwen default)")
    print(f"  queue:   GET  /api/queue  (pathway / soft-court / scaffold live)")
    print(f"  expand:  POST /api/pathways/expand  (gated graph growth)")
    print(f"  restart: POST /api/server/restart  (UI: Ctrl+Shift+R)")
    print(f"  narrate: POST /api/narrate · GET /api/narrate/status")
    print("  Ctrl+C to stop. free_parameters=0 · pin D1D38A")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        _HTTP_SERVER = None
        httpd.server_close()


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="FSOT-MC full-stack server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    serve(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
