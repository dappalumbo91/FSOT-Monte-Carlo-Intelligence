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
            "publish-check",
        ],
    )
    ap.add_argument("--n-paths", type=int, default=128)
    ap.add_argument("--seed", type=int, default=0)
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
    args = ap.parse_args(argv)

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

    if args.command == "publish-check":
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        checks = {
            "README": (root / "README.md").is_file(),
            "LICENSE": (root / "LICENSE").is_file(),
            "pyproject": (root / "pyproject.toml").is_file(),
            "hf_card": (root / "publishing" / "huggingface" / "README.md").is_file(),
            "kaggle_nb": (root / "publishing" / "kaggle" / "fsot_mc_demo.ipynb").is_file(),
            "architecture": (root / "docs" / "UNIVERSE_INTELLIGENCE_ARCHITECTURE.md").is_file(),
            "full_atlas": (root / "fsot_mc" / "full_atlas.json").is_file(),
            "authority_gate": verify_fsot_gate()["ok"],
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
    )
    if args.json:
        slim = {
            "method": r.get("method"),
            "scope": r.get("scope"),
            "atlas": r.get("atlas"),
            "canonical_universe": r.get("canonical_universe"),
            "top_ledger": (r.get("discovery") or {}).get("top_ledger"),
            "pathway_memory": (r.get("discovery") or {}).get("pathway_memory"),
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
            print(f"  realities kernel={(r['realities'].get('poll') or {}).get('kernel_alive')}")
        if r.get("apis"):
            print(f"  apis ok={r['apis'].get('n_ok')}")
        print("  purpose: pathways + physics under FSOT — not markets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
