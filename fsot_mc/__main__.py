"""python -m fsot_mc — Universe Monte Carlo intelligence CLI."""

from __future__ import annotations

import argparse
import json
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="FSOT Universe Monte Carlo Intelligence — discovery, not markets"
    )
    ap.add_argument(
        "command",
        nargs="?",
        default="gate",
        choices=[
            "gate",
            "atlas",
            "build-atlas",
            "scan",
            "discover",
            "intel",
            "eyes",
            "formal",
            "realities",
            "apis",
            "relay",
            "polar-train",
            "ask",
            "chat",
            "independent",
            "publish-check",
            "readings",
            "accuracy",
            "memory-status",
            "serve",
            "graph",
            "solidify",
            "protocols",
            "tissue-docs",
            "literature-index",
            "literature-search",
            "literature-status",
            "scientific-audit",
            "claims",
            "audit-promote",
            "flip-protocols",
            "pred-bench",
            "narrate",
            "narrate-status",
            "download-qwen",
            "docs-index",
            "docs-search",
            "chat",
        ],
    )
    ap.add_argument("--node", default="", help="narrate: tissue node id or domain name")
    ap.add_argument("--max-tokens", type=int, default=700, help="narrate max_new_tokens")
    ap.add_argument("--temperature", type=float, default=0.4, help="narrate sampling temperature")
    ap.add_argument("--set", default="", help="pred-bench: PRED id to update")
    ap.add_argument("--status", default="", help="pred-bench status: open|in_progress|pass|kill|blocked")
    ap.add_argument("--measured", default="", help="pred-bench measured value")
    ap.add_argument("--source", default="", help="pred-bench measured source note")
    ap.add_argument("--host", default="127.0.0.1", help="serve host")
    ap.add_argument("--port", type=int, default=8765, help="serve port")
    ap.add_argument("-q", "--query", default="", help="Question for ask/chat")
    ap.add_argument("--n-paths", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--think", action="store_true", help="Show full thinking trace")
    ap.add_argument("--chew", action="store_true", help="Chew arXiv/Wikipedia into mind (FSOT_MC_ONLINE=1 for live)")
    ap.add_argument("--max-papers", type=int, default=100_000, help="literature-index max arXiv papers")
    ap.add_argument("--max-articles", type=int, default=50_000, help="literature-index max wiki articles")
    ap.add_argument("--wiki", action="store_true", help="index Simple Wikipedia in literature-index")
    ap.add_argument("--arxiv-only", action="store_true", help="literature-index: arXiv only")
    ap.add_argument("--rebuild-index", action="store_true", help="rebuild literature indexes")
    ap.add_argument(
        "--scope",
        default="core",
        choices=["core", "full", "extensions"],
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-archive", action="store_true")
    ap.add_argument("--with-formal", action="store_true")
    ap.add_argument("--with-realities", action="store_true")
    ap.add_argument("--with-apis", action="store_true")
    ap.add_argument("--online", action="store_true", help="Allow network for APIs")
    # Remainder so: fsot_mc ask --think What about cosmology?
    args, rest = ap.parse_known_args(argv)
    if rest:
        # drop leading '--' if present
        if rest and rest[0] == "--":
            rest = rest[1:]
        q_rest = " ".join(rest).strip()
        if q_rest:
            args.query = (str(args.query) + " " + q_rest).strip()

    from fsot_mc import __version__, verify_fsot_gate

    if args.online:
        import os

        os.environ["FSOT_MC_ONLINE"] = "1"

    if args.command == "gate":
        g = verify_fsot_gate(require_archive=False)
        if args.json:
            print(json.dumps(g, indent=2))
        else:
            print(f"fsot_mc {__version__}  [UNIVERSE DISCOVERY]")
            print(f"authority_ok={g['ok']}  sha={g['authority_sha256'][:12]}…")
            print(
                f"float_engine={g['float_engine']['ok']}  "
                f"bytes={g['authority_bytes']['local_matches']}"
            )
        return 0 if g["ok"] else 2

    if args.command == "build-atlas":
        from fsot_mc.atlas_build import build_full_atlas
        from fsot_mc.universe_atlas import reload_atlas

        a = build_full_atlas(write=True)
        reload_atlas()
        print(
            f"built full atlas: core={a['n_core']} ext={a['n_extension']} total={a['n_total']}"
        )
        return 0

    if args.command == "atlas":
        from fsot_mc import atlas_meta, domains_by_cluster, snapshot_universe
        from fsot_mc.universe_atlas import core_names

        meta = atlas_meta()
        names = core_names() if args.scope == "core" else None
        snap = snapshot_universe(names=names)
        clusters = {k: len(v) for k, v in domains_by_cluster().items()}
        if args.json:
            print(
                json.dumps(
                    {
                        "meta": meta,
                        "snapshot": {
                            "emergence_fraction": snap["emergence_fraction"],
                            "mean_S": snap["mean_S"],
                            "n_domains": snap["n_domains"],
                        },
                        "clusters": clusters,
                    },
                    indent=2,
                )
            )
        else:
            print(
                f"fsot_mc {__version__}  atlas total={meta.get('domain_count')} "
                f"core={meta.get('n_core')} ext={meta.get('n_extension')}"
            )
            print(
                f"  snapshot scope={args.scope} n={snap['n_domains']} "
                f"emergence={snap['emergence_fraction']:.3f} mean_S={snap['mean_S']:+.4f}"
            )
        return 0

    if args.command == "scan":
        from fsot_mc import run_universe_scan

        r = run_universe_scan(n_paths=args.n_paths, seed=args.seed, scope=args.scope)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            ens = r.get("ensemble") or {}
            print(
                f"fsot_mc {__version__}  scan paths={args.n_paths} "
                f"scope={r.get('scope')} domains={r.get('n_domains')}"
            )
            ef = ens.get("emergence_fraction") or {}
            print(f"  emergence mean={ef.get('mean'):.3f}")
            pm = r.get("pathway_memory") or {}
            print(f"  pathway patterns={pm.get('n_patterns')} solid={pm.get('n_solidified')}")
        return 0 if not r.get("error") else 1

    if args.command == "eyes":
        from fsot_mc import demo_ring_from_mc, eyes_with_mc, run_universe_monte_carlo

        mc = run_universe_monte_carlo(
            n_paths=min(args.n_paths, 32), seed=args.seed, scope="core", store_paths=4
        )
        eyes = eyes_with_mc(mc, text="FSOT π-ring eyes")
        if args.json:
            print(json.dumps(eyes, indent=2, default=str))
        else:
            ring = eyes.get("ring") or {}
            print(f"fsot_mc {__version__}  EYES  backend={ring.get('vision_backend')}")
            print(f"  interior_area πr²={ring.get('interior_area_pi_r2'):.4f}")
            print(f"  mc_mass={ring.get('mc_mass_total')} sense={ring.get('sense_mass_total')}")
            print(f"  mean_S_weighted={ring.get('mean_S_weighted')}")
            print(f"  pflt_root={ring.get('pflt_root')}")
        return 0

    if args.command == "formal":
        from fsot_mc import formal_status, run_intelligence, run_soft_court
        from fsot_mc.formal_bridge import promote_from_intelligence

        st = formal_status()
        intel = run_intelligence(
            n_paths=min(args.n_paths, 48),
            seed=args.seed,
            scope="core",
            with_eyes=False,
            with_formal_promote=True,
        )
        if args.json:
            print(json.dumps({"status": st, "promote": intel.get("formal")}, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  FORMAL SOFT COURT")
            print(f"  certificate_claims={st.get('certificate_proved_claims')}")
            print(f"  cross_proof={st.get('cross_proof')}")
            print(f"  pending={st.get('pending_obligations')} promoted={st.get('promoted_obligations')}")
            frm = intel.get("formal") or {}
            court = frm.get("court") or {}
            print(f"  exported={ (frm.get('exported') or {}).get('exported') }")
            print(f"  n_promoted={court.get('n_promoted')} n_pending_scored={court.get('n_pending')}")
        return 0

    if args.command == "realities":
        from fsot_mc import couple_to_intelligence, poll_runtime

        poll = poll_runtime()
        couple = couple_to_intelligence() if poll.get("ok") else poll
        if args.json:
            print(json.dumps({"poll": poll, "couple": couple}, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  REALITIES CLIENT")
            if not poll.get("ok"):
                print(f"  ERROR {poll.get('error')}")
                return 1
            print(f"  kernel_alive={poll.get('kernel_alive')} heartbeat={poll.get('heartbeat')}")
            print(f"  emergence_tail={poll.get('n_emergence_tail')}")
            print(f"  pathway={ (couple.get('pathway_record') or {}) }")
        return 0

    if args.command == "apis":
        from fsot_mc import run_api_bundle, seed_demo_cache

        seed_demo_cache()
        r = run_api_bundle()
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  APIS  online={r.get('online')} ok={r.get('n_ok')}")
            for name, res in (r.get("results") or {}).items():
                print(f"  {name}: ok={res.get('ok')} source={res.get('source')} hint={res.get('domain_hint')}")
        return 0

    if args.command == "independent":
        from fsot_mc.paths import independence_status

        st = independence_status()
        if args.json:
            print(json.dumps(st, indent=2))
        else:
            print(f"fsot_mc {__version__}  INDEPENDENCE")
            print(f"  independent={st['independent']}")
            for k, v in st["checks"].items():
                print(f"  {'OK' if v else 'MISS'}  {k}")
            print(f"  package_root={st['package_root']}")
        return 0 if st["independent"] else 1

    if args.command == "relay":
        from fsot_mc import run_intelligence
        from fsot_mc.language_relay import relay_discovery

        intel = run_intelligence(
            n_paths=min(args.n_paths, 48),
            seed=args.seed,
            scope="core",
            with_eyes=False,
            with_language_relay=True,
        )
        rel = intel.get("language_relay") or relay_discovery(intel.get("discovery") or {})
        if args.json:
            print(json.dumps(rel, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  LANGUAGE RELAY")
            print(f"  pflt_core={rel.get('pflt_core_available')} n={rel.get('n_relayed')}")
            print(f"  state: {(rel.get('universe_state') or '')[:200]}")
            for r in (rel.get("relays") or [])[:5]:
                print(f"  --- {r.get('id')} ---")
                print(f"  {r.get('relay_text')[:220]}")
                surf = r.get("pflt_surface") or {}
                if surf.get("ok"):
                    print(f"  pflt_surface meanings={str(surf.get('meanings'))[:120]}")
        return 0

    if args.command == "polar-train":
        from fsot_mc.polar_student import train_polar_student

        r = train_polar_student(n_paths=min(args.n_paths, 96), seed=args.seed, scope="core")
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  POLAR STUDENT")
            if not r.get("ok"):
                print("  ERROR", r.get("error"))
                return 1
            print(f"  samples={r.get('n_samples')} train_acc={r.get('train_acc'):.3f} test_acc={r.get('test_acc'):.3f}")
            print(f"  backend={r.get('backend')} model={r.get('model_path')}")
            if r.get("torch"):
                print(f"  torch={r['torch']}")
        return 0

    if args.command in ("readings", "accuracy"):
        from fsot_mc.accuracy_gate import format_readings_text, run_accuracy_readings

        r = run_accuracy_readings(
            n_paths=min(args.n_paths, 96),
            seed=args.seed,
            with_multipath=True,
            write=True,
        )
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  CROSS-DOMAIN ACCURACY READINGS")
            print(format_readings_text(r))
        # Exit 0 if integrity authority + core recompute OK (archive green is evidence load)
        ok = bool((r.get("integrity_checks") or {}).get("authority_ok")) and bool(
            (r.get("integrity_checks") or {}).get("core_recompute_ok")
        )
        return 0 if ok and not r.get("error") else 1

    if args.command == "memory-status":
        from fsot_mc.adaptive_memory import AdaptiveMemory

        mem = AdaptiveMemory()
        s = mem.summary()
        if args.json:
            print(json.dumps(s, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  ADAPTIVE MEMORY (STM/LTM)")
            print(f"  STM: {s.get('stm_size')}/{s.get('stm_capacity')}")
            print(f"  LTM: {s.get('ltm_size')}  solidified={s.get('n_solidified')}")
            print(f"  solidify_bar={s.get('solidify_acc_bar'):.4f}  soften={s.get('soften_acc_bar'):.4f}")
            print(f"  path={s.get('ltm_path')}")
            print(f"  doctrine: {s.get('doctrine')}")
        return 0

    if args.command == "serve":
        from fsot_mc.server import serve

        serve(host=args.host, port=args.port)
        return 0

    if args.command == "graph":
        from fsot_mc.graph_model import build_universe_graph

        g = build_universe_graph(
            n_paths=min(args.n_paths, 64),
            seed=args.seed,
            scope=args.scope if args.scope in ("core", "full") else "full",
            with_archive_connective=True,
            force_rebuild_connective=bool(getattr(args, "online", False)),  # reuse flag no
        )
        # allow --scope full|core already on argparse
        if args.json:
            # omit huge node list summary mode unless user wants full - still dump full for API parity
            print(json.dumps(g, indent=2, default=str))
        else:
            m = g.get("meta") or {}
            ac = m.get("archive_connective") or {}
            print(f"fsot_mc {__version__}  CONNECTIVE GRAPH  scope={g.get('scope')}")
            print(f"  nodes={g.get('n_nodes')} edges={g.get('n_edges')}")
            print(f"  core={m.get('n_core_folds')} extension={m.get('n_extension_panels')} intents={m.get('n_problem_routes')}")
            print(f"  map_emergence={m.get('map_emergence_mean')}")
            if ac:
                print(f"  archive tissue: nodes={ac.get('n_archive_nodes')} edges={ac.get('n_archive_edges')}")
                print(f"  green_gate={ac.get('n_green_gate')}/{ac.get('n_with_error')}  raw_couples={ac.get('coupling_raw_edge_count')}")
                print(f"  edge_types={ac.get('edge_type_counts')}")
            print(f"  aesthetic={g.get('aesthetic')}")
            for line in (m.get("legend") or [])[:8]:
                print(f"  · {line}")
        return 0

    if args.command == "solidify":
        from fsot_mc.chew_solidify import solidify_corpus

        r = solidify_corpus(n_paths=min(args.n_paths, 24), seed=args.seed)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            s = r.get("memory_summary") or {}
            print(f"fsot_mc {__version__}  CHEW→LTM SOLIDIFY")
            print(f"  topics={r.get('n_topics')} LTM={s.get('ltm_size')} solid={s.get('n_solidified')}")
            print(f"  {r.get('note')}")
        return 0

    if args.command == "protocols":
        from fsot_mc.experiment_protocols import list_protocol_cards

        r = list_protocol_cards(query=args.query or "", limit=12)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  EXPERIMENT PROTOCOLS")
            for c in r.get("cards") or []:
                print(f"  {c.get('id')}: {c.get('title')}")
                print(f"    FSOT={c.get('fsot_predicted')} {c.get('unit')}  disc={c.get('discriminant')}")
        return 0

    if args.command == "tissue-docs":
        from fsot_mc.tissue_docs import generate_all_tissue_docs

        m = generate_all_tissue_docs(write=True)
        if args.json:
            print(json.dumps(m, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  TISSUE SCIENTIFIC DOCS")
            print(f"  documents={m.get('n_docs')} errors={m.get('n_errors')}")
            print("  root=docs/tissue/  index=docs/tissue/INDEX.md")
            print("  each node = miniature thesis (math · results · application · connective tissue)")
        return 0

    if args.command == "literature-status":
        from fsot_mc.literature_corpus import literature_status

        st = literature_status()
        if args.json:
            print(json.dumps(st, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  LITERATURE CORPUS")
            print(f"  arxiv file: {st.get('arxiv_path')} exists={st.get('arxiv_exists')} size_gb={st.get('arxiv_size_gb')}")
            print(f"  arxiv index: {st.get('arxiv_indexed')} papers → {st.get('arxiv_db')}")
            print(f"  wiki root: {st.get('wiki_root')} exists={st.get('wiki_exists')}")
            print(f"  wiki index: {st.get('wiki_indexed')} articles → {st.get('wiki_db')}")
        return 0

    if args.command == "literature-index":
        from fsot_mc.literature_corpus import build_arxiv_index, build_wiki_index

        results: dict = {}
        do_arxiv = not args.wiki or args.arxiv_only or True
        do_wiki = not args.arxiv_only
        if args.arxiv_only:
            do_arxiv, do_wiki = True, False
        # default both; --arxiv-only skips wiki; --wiki still indexes arxiv too unless arxiv-only
        if not args.arxiv_only:
            do_arxiv, do_wiki = True, True

        if do_arxiv:
            # --max-papers 0 → full OAI dump, no category filter (long run)
            full = args.max_papers <= 0
            print(
                f"fsot_mc {__version__}  indexing arXiv "
                f"(max={'FULL' if full else args.max_papers}, "
                f"filter={'none' if full else 'fsot_priority'})…"
            )
            results["arxiv"] = build_arxiv_index(
                max_papers=None if full else args.max_papers,
                rebuild=args.rebuild_index,
                fsot_priority=False if full else True,
            )
            print(
                "  arxiv:",
                {
                    k: results["arxiv"].get(k)
                    for k in ("ok", "n_papers", "n_scanned", "seconds", "error")
                },
            )
        if do_wiki:
            print(f"fsot_mc {__version__}  indexing Simple Wikipedia (max={args.max_articles})…")
            results["wiki"] = build_wiki_index(
                max_articles=None if args.max_articles <= 0 else args.max_articles,
                rebuild=args.rebuild_index,
            )
            print(
                "  wiki:",
                {k: results["wiki"].get(k) for k in ("ok", "n_articles", "seconds", "error")},
            )
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        return 0 if all((v or {}).get("ok", True) for v in results.values()) else 1

    if args.command == "audit-promote":
        from fsot_mc.formal_bridge import promote_from_audit

        r = promote_from_audit(only_failures=False, also_improvements=True, run_court=True)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  AUDIT → FORMAL OBLIGATIONS")
            print(f"  leads={r.get('n_leads')} grade={r.get('audit_grade')} score={r.get('audit_score')}")
            court = r.get("court") or {}
            print(f"  soft_court pending={court.get('n_pending')} promoted={court.get('n_promoted')}")
            print(f"  pending_dir={r.get('pending_dir')}")
            print(f"  {r.get('note')}")
        return 0

    if args.command == "flip-protocols":
        from fsot_mc.flip_protocols import build_flip_protocol_pack

        r = build_flip_protocol_pack(n_paths=min(args.n_paths, 128), seed=args.seed, write=True)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  FLIP-HOTSPOT PROTOCOLS")
            print(f"  hotspots={r.get('n_hotspots')} n_paths={r.get('n_paths')}")
            for c in (r.get("cards") or [])[:15]:
                print(f"  {c.get('domain')}: flip={c.get('flip_rate'):.3f} pri={c.get('priority')} S_can={c.get('S_canonical')}")
            print(f"  written: {r.get('written')}")
        return 0

    if args.command == "pred-bench":
        from fsot_mc.pred_bench import (
            init_bench_from_manifest,
            load_bench_ledger,
            update_pred_status,
            write_bench_markdown,
            bench_status_summary,
        )

        if args.set and args.status:
            measured = None
            if args.measured != "":
                try:
                    measured = float(args.measured)
                except ValueError:
                    measured = args.measured
            r = update_pred_status(
                args.set,
                status=args.status,
                measured_value=measured,
                measured_source=args.source or None,
                note=args.query or None,
            )
            write_bench_markdown()
            if args.json:
                print(json.dumps(r, indent=2, default=str))
            else:
                print(f"fsot_mc {__version__}  PRED-BENCH UPDATE")
                print(f"  ok={r.get('ok')} id={args.set} status={args.status}")
                if r.get("error"):
                    print(f"  error={r.get('error')}")
                print(f"  summary={r.get('summary')}")
            return 0 if r.get("ok") else 1
        r = init_bench_from_manifest()
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            s = r.get("summary") or bench_status_summary()
            print(f"fsot_mc {__version__}  PRED BENCH-CLOSURE LEDGER")
            print(f"  n={s.get('n')} by_status={s.get('by_status')}")
            print(f"  ledger={r.get('ledger_path')}")
            print(f"  markdown={r.get('markdown')}")
            print("  update: python -m fsot_mc pred-bench --set PRED-001 --status pass --measured 70.8")
        return 0

    if args.command == "claims":
        from fsot_mc.claims_ledger import write_claims_ledger

        r = write_claims_ledger(write_md=True)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  CLAIMS LEDGER (data-first)")
            print(f"  n_claims={r.get('n_claims')} free_parameters=0")
            for c in r.get("claims") or []:
                print(f"  [{c.get('tier')}] {c.get('id')}")
                print(f"    {c.get('statement')[:200]}")
            print(f"  written: {(r.get('written') or {})}")
        return 0

    if args.command == "scientific-audit":
        from fsot_mc.scientific_audit import format_audit_markdown, run_scientific_audit

        r = run_scientific_audit(write=True, include_self=True)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  SCIENTIFIC INTELLIGENCE AUDIT")
            print(f"  grade={r.get('grade')} score={r.get('overall_score')}")
            print(f"  pass={r.get('n_pass')}/{r.get('n_checks')}  critical_fail={r.get('critical_failures')}")
            print(f"  high_fail={r.get('high_failures')}")
            for c in r.get("checks") or []:
                flag = "PASS" if c.get("ok") else "FAIL"
                print(f"  [{flag}] {c.get('id')} {c.get('score'):.2f}  {c.get('title')}")
                print(f"         {c.get('finding')}")
            print(f"  report: {(r.get('written') or {}).get('markdown')}")
            print(f"  json:   {(r.get('written') or {}).get('latest')}")
            promo = r.get("formal_promote") or {}
            if promo:
                court = promo.get("court") or {}
                print(
                    f"  formal_auto_promote: leads={promo.get('n_leads')} "
                    f"pending={court.get('n_pending')} promoted={court.get('n_promoted')} "
                    f"(≠ Lean-proved)"
                )
        return 0 if not r.get("critical_failures") else 2

    if args.command == "literature-search":
        from fsot_mc.literature_corpus import literature_search

        q = (args.query or "").strip() or "quantum gravity fluid spacetime cosmology"
        r = literature_search(q, arxiv_limit=5, wiki_limit=3, with_fsot=True)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  LITERATURE SEARCH + FSOT CROSS-REF")
            print(f"  Q: {q}")
            print(f"  source={r.get('source')} domains={r.get('primary_domains')}")
            print(f"  index={r.get('index_status')}")
            for h in ((r.get("arxiv") or {}).get("hits") or [])[:5]:
                print(f"  arXiv {h.get('id')}: {h.get('title')}")
                print(f"    cats={h.get('categories')} → FSOT {h.get('fsot_domains')}")
                folds = h.get("fsot_fold_panel") or []
                if folds:
                    print(
                        "    folds:",
                        "; ".join(
                            f"{f.get('domain')} S={f.get('S')} {f.get('regime')}" for f in folds[:3]
                        ),
                    )
            for h in ((r.get("wikipedia") or {}).get("hits") or [])[:3]:
                print(f"  Wiki: {h.get('title')} → {h.get('fsot_domains')}")
        return 0 if r.get("ok") else 1

    if args.command == "download-qwen":
        # thin wrapper → scripts/download_qwen25_instruct.py
        import subprocess
        from fsot_mc.paths import PACKAGE_ROOT

        script = PACKAGE_ROOT / "scripts" / "download_qwen25_instruct.py"
        return subprocess.call([sys.executable, str(script)])

    if args.command == "docs-index":
        from fsot_mc.doc_rag import build_doc_index

        r = build_doc_index(rebuild=bool(args.rebuild_index))
        if args.json:
            print(json.dumps(r, indent=2))
        else:
            print(f"fsot_mc {__version__}  DOCS INDEX")
            print(f"  ok={r.get('ok')} files={r.get('n_files')} chunks={r.get('n_chunks')}")
            print(f"  db={r.get('db')}")
        return 0 if r.get("ok") else 1

    if args.command == "docs-search":
        from fsot_mc.doc_rag import search_docs

        q = (args.query or "").strip() or "Biology multipath FSOT"
        r = search_docs(q, limit=8)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  DOCS SEARCH")
            print(f"  Q: {q}  hits={r.get('n_hits')}")
            for h in r.get("hits") or []:
                print(f"  - {h.get('path')} :: {h.get('title')}")
                print(f"    {(h.get('body') or '')[:160].replace(chr(10), ' ')}…")
        return 0 if r.get("ok") else 1

    if args.command == "chat":
        from fsot_mc.qwen_chat import chat as qwen_chat, clear_history

        q = (args.query or "").strip()
        if not q:
            # interactive
            print(f"fsot_mc {__version__}  CHAT  (Qwen · reads docs/tissue)")
            print("Type 'quit' to exit, 'clear' to reset history.\n")
            sid = "cli"
            while True:
                try:
                    line = input("you> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not line:
                    continue
                if line.lower() in ("quit", "exit", "q"):
                    break
                if line.lower() == "clear":
                    clear_history(sid)
                    print("(history cleared)")
                    continue
                r = qwen_chat(line, session_id=sid, max_new_tokens=args.max_tokens, temperature=args.temperature)
                if not r.get("ok"):
                    print("error>", r.get("error"), r.get("detail") or r.get("hint") or "")
                    continue
                docs = ", ".join((d.get("path") or "") for d in (r.get("docs_used") or [])[:4])
                print(f"docs> {docs}")
                print(f"qwen> {r.get('reply')}\n")
            return 0
        r = qwen_chat(q, session_id="cli-once", max_new_tokens=args.max_tokens, temperature=args.temperature)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print(f"fsot_mc {__version__}  CHAT")
            print(f"  docs: {[d.get('path') for d in (r.get('docs_used') or [])]}")
            print(f"  A: {r.get('reply') or r.get('error')}")
        return 0 if r.get("ok") else 1

    if args.command == "narrate-status":
        from fsot_mc.qwen_narrate import model_ready, model_dir, DEFAULT_HF_ID

        st = model_ready()
        if args.json:
            print(json.dumps(st, indent=2))
        else:
            print(f"fsot_mc {__version__}  QWEN NARRATE STATUS")
            print(f"  hf_id={DEFAULT_HF_ID}")
            print(f"  path={model_dir()}")
            print(f"  ready={st.get('ok')} safetensors={st.get('n_safetensors')}")
            print(f"  hint={st.get('hint')}")
        return 0 if st.get("ok") else 1

    if args.command == "narrate":
        from fsot_mc.qwen_narrate import narrate, build_narration_pack, model_ready

        q = (args.query or "").strip() or "Explain multipath emergence under FSOT for biology."
        node = (args.node or "").strip() or None
        if args.json and not model_ready().get("ok"):
            # still emit pack-only for CI without weights
            pack = build_narration_pack(query=q, node_id=node, n_paths=min(args.n_paths, 48), chew=args.chew)
            print(json.dumps({"ok": False, "error": "model_not_downloaded", "pack": pack}, indent=2, default=str))
            return 1
        r = narrate(
            q,
            node_id=node,
            n_paths=min(args.n_paths, 48),
            chew=args.chew,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        if args.json:
            # drop huge full pack unless requested
            out = {k: v for k, v in r.items() if k != "pack"}
            print(json.dumps(out, indent=2, default=str))
            return 0 if r.get("ok") else 1
        print(f"fsot_mc {__version__}  NARRATE  (Qwen2.5-Instruct 7B · FSOT pack)")
        print(f"  Q: {q}")
        if node:
            print(f"  node: {node}")
        print(f"  ok={r.get('ok')} model={r.get('model')}")
        if r.get("error"):
            print(f"  error={r.get('error')} detail={r.get('detail')}")
            if r.get("fallback_answer"):
                print("  --- mind_answer (fallback) ---")
                print(r.get("fallback_answer"))
            return 1
        ps = r.get("pack_summary") or {}
        print(f"  domains: {ps.get('routed_domains')} theses={ps.get('n_theses')}")
        print("  --- narration ---")
        print(r.get("narration") or "")
        return 0

    if args.command == "ask":
        from fsot_mc.qwen_narrate import full_mind_answer

        q = (args.query or "").strip() or "What is the state of the FSOT universe?"
        # Default: mind + Qwen. --think still shows multipath steps if raw mind needed.
        r = full_mind_answer(
            q,
            n_paths=min(args.n_paths, 96),
            chew=args.chew,
            node_id=(args.node or None) or None,
            use_qwen=True,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        if args.json:
            print(json.dumps(r, indent=2, default=str))
            return 0 if not r.get("error") else 1
        print(f"fsot_mc {__version__}  ASK  (mind + Qwen2.5 · ToE)")
        print(f"  Q: {q}")
        th = r.get("thinking") or {}
        qw = r.get("qwen") or {}
        print(f"  domains: {', '.join(th.get('routed_domains') or [])}")
        print(f"  paths: {th.get('n_paths')}  qwen_used={qw.get('used')} ready={qw.get('ready')}")
        if qw.get("error"):
            print(f"  qwen_error={qw.get('error')} {qw.get('detail') or qw.get('hint') or ''}")
        if args.think and r.get("answer_raw"):
            print("  --- mind (raw multipath) ---")
            print(str(r.get("answer_raw"))[:1500])
            print("  --- qwen narration ---")
        print(f"  A: {r.get('answer') or ''}")
        return 0

    if args.command == "chat":
        from fsot_mc.mind import FSOTMind
        from fsot_mc.language_relay import relay_mind_answer

        mind = FSOTMind(n_paths=min(args.n_paths, 64), seed=args.seed)
        print(f"fsot_mc {__version__}  CHAT  (FSOT Monte Carlo mind)")
        print("Thinking = multipath simulation. Type 'quit' to exit. Prefix ?think for traces.\n")
        initial = (args.query or "").strip()

        def _one(line: str) -> None:
            show_think = args.think or line.lower().startswith("?think")
            q = line[6:].strip() if line.lower().startswith("?think") else line
            r = mind.think(
                q,
                n_paths=min(args.n_paths, 64),
                with_chew=args.chew,
            )
            if args.json:
                print(json.dumps(r, indent=2, default=str))
                return
            print(f"you> {q}")
            if show_think:
                for step in ((r.get("thinking") or {}).get("steps") or []):
                    print(f"  [{step.get('step')}] {step.get('text')}")
            print("mind>", relay_mind_answer(str(r.get("answer") or ""), r.get("thinking")))
            print()

        if initial:
            _one(initial)
            return 0
        try:
            while True:
                line = input("you> ").strip()
                if not line or line.lower() in ("quit", "exit", "q"):
                    break
                _one(line)
        except (EOFError, KeyboardInterrupt):
            print()
        return 0

    if args.command == "publish-check":
        from pathlib import Path

        from fsot_mc.paths import independence_status

        root = Path(__file__).resolve().parents[1]
        ind = independence_status()
        checks = {
            "README": (root / "README.md").is_file(),
            "LICENSE": (root / "LICENSE").is_file(),
            "pyproject": (root / "pyproject.toml").is_file(),
            "hf_card": (root / "publishing" / "huggingface" / "README.md").is_file(),
            "kaggle_nb": (root / "publishing" / "kaggle" / "fsot_mc_demo.ipynb").is_file(),
            "architecture": (root / "docs" / "UNIVERSE_INTELLIGENCE_ARCHITECTURE.md").is_file(),
            "full_atlas": (root / "fsot_mc" / "full_atlas.json").is_file(),
            "authority_gate": verify_fsot_gate()["ok"],
            "independent_workspace": ind["independent"],
            "vendor_pflt": (root / "vendor" / "pflt" / "fsot_multilayer_vision.py").is_file(),
            "vendor_bundle": (root / "vendor" / "archive_bundle" / "MANIFEST.json").is_file(),
        }
        if args.json:
            print(json.dumps(checks, indent=2))
        else:
            print(f"fsot_mc {__version__}  PUBLISH CHECK")
            for k, v in checks.items():
                print(f"  {'OK' if v else 'MISSING'}  {k}")
        return 0 if all(checks.values()) else 1

    # discover / intel
    from fsot_mc import run_intelligence

    r = run_intelligence(
        n_paths=args.n_paths,
        seed=args.seed,
        use_real_data=not args.no_archive,
        scope=args.scope,
        with_eyes=True,
        with_formal_promote=args.with_formal,
        with_realities=args.with_realities,
        with_apis=args.with_apis,
        with_language_relay=True,
    )
    if args.json:
        slim = {
            "method": r.get("method"),
            "scope": r.get("scope"),
            "independent": r.get("independent"),
            "atlas": r.get("atlas"),
            "canonical_universe": r.get("canonical_universe"),
            "top_ledger": (r.get("discovery") or {}).get("top_ledger"),
            "pathway_memory": (r.get("discovery") or {}).get("pathway_memory"),
            "language_relay": r.get("language_relay"),
            "eyes": (r.get("eyes") or {}).get("ring"),
            "formal": r.get("formal"),
            "realities": r.get("realities"),
            "apis_n_ok": (r.get("apis") or {}).get("n_ok"),
            "free_parameters": 0,
        }
        print(json.dumps(slim, indent=2, default=str))
    else:
        print(f"fsot_mc {__version__}  UNIVERSE INTELLIGENCE  scope={args.scope}")
        if r.get("error"):
            print("ERROR", r["error"])
            return 1
        ind = r.get("independent") or {}
        print(f"  independent={ind.get('independent')}")
        can = r.get("canonical_universe") or {}
        meta = r.get("atlas") or {}
        print(
            f"  atlas core={meta.get('n_core')} ext={meta.get('n_extension')} "
            f"total={meta.get('domain_count')}"
        )
        print(
            f"  canonical n={can.get('n_domains')} "
            f"emergence={can.get('emergence_fraction'):.3f} mean_S={can.get('mean_S'):+.4f}"
        )
        disc = r.get("discovery") or {}
        pm = disc.get("pathway_memory") or {}
        print(f"  pathway_memory patterns={pm.get('n_patterns')} solid={pm.get('n_solidified')}")
        eyes = (r.get("eyes") or {}).get("ring") or {}
        if eyes:
            print(
                f"  eyes backend={eyes.get('vision_backend')} "
                f"πr²={eyes.get('interior_area_pi_r2'):.3f} "
                f"mc_mass={eyes.get('mc_mass_total')}"
            )
        lang = r.get("language_relay") or {}
        if lang:
            print(f"  language_relay n={lang.get('n_relayed')} pflt={lang.get('pflt_core_available')}")
            if lang.get("universe_state"):
                print(f"  state: {lang['universe_state'][:160]}")
        top = disc.get("top_ledger") or []
        print(f"  discovery leads: {len(top)}")
        for lead in top[:6]:
            print(
                f"    [{lead.get('class')}] {lead.get('id')}: "
                f"score={float(lead.get('score') or 0):.3f}"
            )
        if r.get("formal"):
            print(f"  formal promoted={(r['formal'].get('court') or {}).get('n_promoted')}")
        if r.get("realities"):
            print(
                f"  realities mode={(r['realities'].get('poll') or {}).get('mode')} "
                f"kernel={(r['realities'].get('poll') or {}).get('kernel_alive')}"
            )
        if r.get("apis"):
            print(f"  apis ok={r['apis'].get('n_ok')}")
        print("  purpose: pathways + physics under FSOT — not markets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
