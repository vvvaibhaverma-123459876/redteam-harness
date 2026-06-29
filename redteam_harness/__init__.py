"""redteam-harness: automated LLM adversarial robustness & jailbreak evaluation.

Defensive-security tooling to red-team your *own* models: a versioned attack
library + mutation engine, provider-agnostic targets, pluggable judges (heuristic
and LLM-as-judge with calibration), composable defenses, a before/after safety
scorecard, and a CI gate.
"""
from .attacks import build_suite, expand_suite
from .defenses import default_pipeline
from .harness import RedTeamHarness, compare_defense
from .judges import HeuristicJudge
from .targets import MockTarget
from .types import AttackCase, AttackResult, Judgment, RunReport

__version__ = "0.1.0"

__all__ = [
    "build_suite",
    "expand_suite",
    "default_pipeline",
    "RedTeamHarness",
    "compare_defense",
    "HeuristicJudge",
    "MockTarget",
    "AttackCase",
    "AttackResult",
    "Judgment",
    "RunReport",
]
