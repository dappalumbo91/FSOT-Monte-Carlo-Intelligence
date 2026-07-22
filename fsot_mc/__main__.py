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
        choices=["gate", "atlas", "build-atlas", "scan", "discover", "intel"],
    )
    ap.add_argument("--n-paths", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument(
        "--scope",
        default="core",
        choices=["core", "full", "extensions"],
        help="Domain scope: core(35) | full(core+extensions) | extensions",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-archive", action="store_true", help="Skip archive real-data hooks")
    args = ap.parse_args(argv)

    from fsot_mc import __version__, verify_fsot_gate

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
                            "n_emergence": snap["n_emergence"],
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
            print(f"  clusters={clusters}")
            print(f"  authority={str(meta.get('authority_sha256'))[:12]}…")
        return 0

    if args.command == "scan":
        from fsot_mc import run_universe_scan

        r = run_universe_scan(n_paths=args.n_paths, seed=args.seed, scope=args.scope)
        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            ens = r.get("ensemble") or {}
            print(
                f"fsot_mc {__version__}  universe scan  paths={args.n_paths} "
                f"scope={r.get('scope')} domains={r.get('n_domains')}"
            )
            ef = ens.get("emergence_fraction") or {}
            print(f"  emergence_frac mean={ef.get('mean'):.3f} p50={ef.get('p50'):.3f}")
            pm = r.get("pathway_memory") or {}
            print(
                f"  pathway_memory patterns={pm.get('n_patterns')} "
                f"solid={pm.get('n_solidified')}"
            )
            hints = r.get("discovery_hints") or {}
            flips = hints.get("top_flip_domains") or []
            if flips:
                print("  top flip domains:")
                for row in flips[:5]:
                    print(f"    {row['domain']}: flip_rate={row['flip_rate']:.3f}")
        return 0 if not r.get("error") else 1

    from fsot_mc import run_intelligence

    r = run_intelligence(
        n_paths=args.n_paths,
        seed=args.seed,
        use_real_data=not args.no_archive,
        scope=args.scope,
    )
    if args.json:
        slim = {
            "method": r.get("method"),
            "purpose": r.get("purpose"),
            "scope": r.get("scope"),
            "authority_ok": (r.get("authority_gate") or {}).get("ok"),
            "atlas": r.get("atlas"),
            "canonical_universe": r.get("canonical_universe"),
            "top_ledger": (r.get("discovery") or {}).get("top_ledger"),
            "pathway_memory": (r.get("discovery") or {}).get("pathway_memory"),
            "contested_top": ((r.get("discovery") or {}).get("contested_physics") or {}).get(
                "top"
            ),
            "candidates_summary": {
                k: len(v)
                for k, v in ((r.get("discovery") or {}).get("candidates") or {}).items()
            },
            "ensemble": (r.get("discovery") or {}).get("ensemble"),
            "free_parameters": 0,
        }
        print(json.dumps(slim, indent=2, default=str))
    else:
        print(f"fsot_mc {__version__}  UNIVERSE INTELLIGENCE  scope={args.scope}")
        if r.get("error"):
            print("ERROR", r["error"])
            return 1
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
        print(f"  authority_ok={(r.get('authority_gate') or {}).get('ok')}")
        disc = r.get("discovery") or {}
        pm = disc.get("pathway_memory") or {}
        print(
            f"  pathway_memory patterns={pm.get('n_patterns')} solid={pm.get('n_solidified')}"
        )
        top = disc.get("top_ledger") or []
        print(f"  discovery leads: {len(top)}")
        for lead in top[:8]:
            title = str(lead.get("title") or lead.get("domain") or "")[:70]
            print(
                f"    [{lead.get('class')}] {lead.get('id')}: "
                f"score={float(lead.get('score') or 0):.3f}  — {title}"
            )
        csum = {k: len(v) for k, v in (disc.get("candidates") or {}).items()}
        print(f"  candidate counts: {csum}")
        print("  purpose: pathways + physics under FSOT — not markets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
