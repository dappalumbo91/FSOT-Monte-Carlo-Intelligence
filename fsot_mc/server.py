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
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from fsot_mc import __version__
from fsot_mc.paths import PACKAGE_ROOT

FRONTEND_DIR = PACKAGE_ROOT / "frontend"


def _json_bytes(obj: Any, code: int = 200) -> tuple[int, bytes, str]:
    body = json.dumps(obj, indent=2, default=str).encode("utf-8")
    return code, body, "application/json; charset=utf-8"


def handle_api(method: str, path: str, query: dict[str, list[str]], body: bytes) -> tuple[int, bytes, str]:
    def q1(key: str, default: str = "") -> str:
        return (query.get(key) or [default])[0]

    try:
        if path == "/api/health" and method == "GET":
            from fsot_mc.authority_gate import verify_fsot_gate

            g = verify_fsot_gate(require_archive=False)
            return _json_bytes(
                {
                    "ok": g.get("ok"),
                    "version": __version__,
                    "product": "FSOT Monte Carlo Intelligence",
                    "authority": g.get("authority_sha256"),
                    "free_parameters": 0,
                    "frontend": FRONTEND_DIR.is_dir(),
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
            from fsot_mc.mind import ask

            data = json.loads(body.decode("utf-8") or "{}")
            r = ask(
                str(data.get("query") or "What is the FSOT universe state?"),
                n_paths=int(data.get("n_paths") or 32),
                with_chew=data.get("chew"),
            )
            # slim for UI
            return _json_bytes(
                {
                    "error": r.get("error"),
                    "answer": r.get("answer"),
                    "thinking": {
                        "routed_domains": (r.get("thinking") or {}).get("routed_domains"),
                        "n_paths": (r.get("thinking") or {}).get("n_paths"),
                        "focus_scalars": (r.get("thinking") or {}).get("focus_scalars"),
                        "adaptive_memory": (r.get("thinking") or {}).get("adaptive_memory"),
                        "emergence_fraction_definition": (r.get("thinking") or {}).get(
                            "emergence_fraction_definition"
                        ),
                    },
                    "session": r.get("session"),
                    "free_parameters": 0,
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


def serve(*, host: str = "127.0.0.1", port: int = 8765) -> None:
    if not FRONTEND_DIR.is_dir():
        raise SystemExit(f"Frontend missing: {FRONTEND_DIR}")
    httpd = ThreadingHTTPServer((host, port), FSOTHandler)
    print(f"FSOT Monte Carlo Intelligence  v{__version__}")
    print(f"  visual:  http://{host}:{port}/")
    print(f"  health:  http://{host}:{port}/api/health")
    print(f"  graph:   http://{host}:{port}/api/graph")
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
