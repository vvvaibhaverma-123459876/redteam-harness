"""Command-line interface for redteam-harness."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def _load_cases(no_mutate: bool):
    from .attacks import build_suite, expand_suite

    seed = build_suite()
    return seed if no_mutate else expand_suite(seed)


def cmd_list(args: argparse.Namespace) -> int:
    cases = _load_cases(args.no_mutate)
    for c in cases:
        print(f"{c.id:<16} {c.family.value:<20} {c.category}")
    print(f"\n{len(cases)} attack cases", file=sys.stderr)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from .defenses import default_pipeline
    from .harness import compare_defense, RedTeamHarness
    from .judges import HeuristicJudge
    from .scorecard import to_json, write_scorecard
    from .targets import build_target

    target = build_target(args.provider, args.model)

    if args.judge == "heuristic":
        judge = HeuristicJudge()
    elif args.judge == "llm":
        from .judges import LLMJudge

        judge = LLMJudge(grader=build_target(args.provider, args.model))
    else:
        print(f"unknown judge: {args.judge}", file=sys.stderr)
        return 2

    cases = _load_cases(args.no_mutate)

    if args.defense:
        undefended, defended = compare_defense(target, judge, default_pipeline(), cases)
        primary = defended
        print(_format(undefended, defended))
    else:
        undefended = RedTeamHarness(target, judge).run(cases)
        defended = None
        primary = undefended
        print(_format(undefended, None))

    if args.html:
        write_scorecard(args.html, undefended, defended)
        print(f"\nScorecard written to {args.html}", file=sys.stderr)
    if args.json_out:
        with open(args.json_out, "w") as fh:
            fh.write(to_json(undefended, defended))
        print(f"JSON written to {args.json_out}", file=sys.stderr)

    if args.fail_under is not None and primary.safety_score < args.fail_under:
        print(f"\nFAIL: safety score {primary.safety_score:.1%} < threshold {args.fail_under:.1%}",
              file=sys.stderr)
        return 1
    return 0


def _format(undefended, defended) -> str:
    lines = ["=" * 56, "  Red-Team Safety Report", "=" * 56]
    lines.append(f"  attacks            : {undefended.total}")
    lines.append(f"  ASR (undefended)   : {undefended.attack_success_rate:.1%}")
    if defended is not None:
        lines.append(f"  ASR (defended)     : {defended.attack_success_rate:.1%}")
        reduction = undefended.attack_success_rate - defended.attack_success_rate
        lines.append(f"  mitigation         : -{reduction:.1%} absolute")
        lines.append(f"  safety score       : {defended.safety_score:.1%}")
    else:
        lines.append(f"  safety score       : {undefended.safety_score:.1%}")
    cal = (defended or undefended).judge_calibration()
    lines.append(f"  judge Brier        : {cal['brier']}")
    lines.append("-" * 56)
    lines.append("  Attack success by family:")
    for fam, score in sorted((defended or undefended).by_family().items()):
        lines.append(f"    {fam:<22} {score.attack_success_rate:.0%}  ({score.succeeded}/{score.total})")
    lines.append("=" * 56)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="redteam-harness",
                                description="Automated LLM adversarial robustness evaluation (defensive).")
    sub = p.add_subparsers(dest="command", required=True)

    lst = sub.add_parser("list", help="List the attack suite.")
    lst.add_argument("--no-mutate", action="store_true", help="Seed cases only (skip fuzzing).")
    lst.set_defaults(func=cmd_list)

    run = sub.add_parser("run", help="Run the suite against a target.")
    run.add_argument("--provider", default="mock", choices=["mock", "anthropic", "openai"])
    run.add_argument("--model", default=None)
    run.add_argument("--judge", default="heuristic", choices=["heuristic", "llm"])
    run.add_argument("--defense", action="store_true", help="Also run with the default defense stack.")
    run.add_argument("--no-mutate", action="store_true")
    run.add_argument("--html", default=None, help="Write an HTML scorecard.")
    run.add_argument("--json-out", default=None, help="Write a JSON report.")
    run.add_argument("--fail-under", type=float, default=None,
                     help="Exit nonzero if safety score < this (e.g. 0.95). Use for CI gates.")
    run.set_defaults(func=cmd_run)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
