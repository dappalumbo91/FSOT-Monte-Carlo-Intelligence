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
"""

from __future__ import annotations

import json
import mimetypes
import os
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from fsot_mc import __version__
from fsot_mc.paths import PACKAGE_ROOT

FRONTEND_DIR = PACKAGE_ROOT / "frontend"
TISSUE_DIR = PACKAGE_ROOT / "docs" / "tissue"


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
                            "source",
                            "note",
                            "free_parameters",
                        )
                    }
                )
            return _json_bytes(t)

        if path == "/api/ask" and method == "POST":
            from fsot_mc.qwen_narrate import full_mind_answer

            data = json.loads(body.decode("utf-8") or "{}")
            # Default: Qwen articulates the full FSOT pack (mind+tissue+lit+…).
            # Pass narrate=false only to force raw mind text.
            use_qwen = data.get("narrate", data.get("use_qwen", True))
            if isinstance(use_qwen, str):
                use_qwen = use_qwen.lower() not in ("0", "false", "no")
            r = full_mind_answer(
                str(data.get("query") or "What is the FSOT universe state?"),
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
    import threading

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


def serve(*, host: str = "127.0.0.1", port: int = 8765, warm_qwen: bool = True) -> None:
    if not FRONTEND_DIR.is_dir():
        raise SystemExit(f"Frontend missing: {FRONTEND_DIR}")
    if warm_qwen and os.environ.get("FSOT_MC_QWEN_WARM", "1") not in ("0", "false", "no"):
        _warm_qwen_background()
    httpd = ThreadingHTTPServer((host, port), FSOTHandler)
    print(f"FSOT Monte Carlo Intelligence  v{__version__}")
    print(f"  visual:  http://{host}:{port}/")
    print(f"  health:  http://{host}:{port}/api/health")
    print(f"  graph:   http://{host}:{port}/api/graph")
    print(f"  ask:     POST /api/ask  (mind + Qwen default)")
    print(f"  narrate: POST /api/narrate · GET /api/narrate/status")
    print("  Ctrl+C to stop. free_parameters=0 · pin D1D38A")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
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
