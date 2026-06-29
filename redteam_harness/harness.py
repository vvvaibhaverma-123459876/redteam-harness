"""The red-team orchestrator.

Runs an attack suite against a target (optionally behind a defense pipeline),
judges each response, and aggregates a RunReport. Also provides a convenience for
the headline before/after comparison.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .defenses.base import Defense
from .judges.base import Judge
from .targets.base import Target
from .types import AttackCase, AttackResult, RunReport


class RedTeamHarness:
    """Drive attacks through target + judge (+ optional defense)."""

    def __init__(self, target: Target, judge: Judge, defense: Optional[Defense] = None):
        self.target = target
        self.judge = judge
        self.defense = defense

    def run_case(self, case: AttackCase) -> AttackResult:
        messages = case.messages
        if self.defense is not None:
            messages = self.defense.transform_input(messages)

        response = self.target.generate(messages)

        blocked = False
        if self.defense is not None:
            response, blocked = self.defense.filter_output(response)

        judgment = self.judge.evaluate(case, response)
        return AttackResult(
            case=case,
            response=response,
            judgment=judgment,
            defended=self.defense is not None,
            blocked_by_defense=blocked,
        )

    def run(self, cases: List[AttackCase], label: Optional[str] = None) -> RunReport:
        label = label or ("defended" if self.defense else "undefended")
        report = RunReport(label=label)
        for case in cases:
            report.results.append(self.run_case(case))
        return report


def compare_defense(
    target: Target,
    judge: Judge,
    defense: Defense,
    cases: List[AttackCase],
) -> Tuple[RunReport, RunReport]:
    """Return (undefended_report, defended_report) over the same suite."""
    undefended = RedTeamHarness(target, judge).run(cases, label="undefended")
    defended = RedTeamHarness(target, judge, defense).run(cases, label="defended")
    return undefended, defended
