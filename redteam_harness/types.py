"""Core data types for the red-team harness.

Defensive-security tooling: these structures describe *attacks you run against
your own model* to measure robustness, and the judgments/defenses used to score
and mitigate them.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class AttackFamily(str, enum.Enum):
    PROMPT_INJECTION = "prompt_injection"     # override the system instruction
    INDIRECT_INJECTION = "indirect_injection"  # payload smuggled via tool/RAG content
    JAILBREAK = "jailbreak"                    # persona / roleplay bypass
    OBFUSCATION = "obfuscation"                # encoded / token-smuggled payload
    MULTI_TURN = "multi_turn"                  # crescendo escalation across turns


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class Message:
    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class AttackCase:
    """A single adversarial test case."""

    id: str
    family: AttackFamily
    category: str                      # human-readable sub-type, drives the heatmap
    messages: List[Message]            # conversation sent to the target
    goal: str                          # the unsafe behaviour the attack tries to elicit
    severity: Severity = Severity.MEDIUM
    mutated_from: Optional[str] = None  # id of the seed case, if this is a fuzz variant
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def prompt_text(self) -> str:
        return "\n".join(m.content for m in self.messages)


@dataclass
class Judgment:
    """A judge's verdict on whether an attack succeeded."""

    success: bool                      # True == the model was successfully attacked
    confidence: float                  # 0..1, used for calibration reporting
    rationale: str = ""

    def __post_init__(self) -> None:
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class AttackResult:
    case: AttackCase
    response: str
    judgment: Judgment
    defended: bool = False
    blocked_by_defense: bool = False   # output suppressed before reaching a user

    @property
    def attack_succeeded(self) -> bool:
        # A blocked output is a defended success-attempt that did not land.
        return self.judgment.success and not self.blocked_by_defense


@dataclass
class CategoryScore:
    category: str
    total: int
    succeeded: int

    @property
    def attack_success_rate(self) -> float:
        return self.succeeded / self.total if self.total else 0.0

    @property
    def block_rate(self) -> float:
        return 1.0 - self.attack_success_rate


@dataclass
class RunReport:
    """Aggregate results of running a suite against one target/defense config."""

    label: str
    results: List[AttackResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def succeeded(self) -> int:
        return sum(1 for r in self.results if r.attack_succeeded)

    @property
    def attack_success_rate(self) -> float:
        return self.succeeded / self.total if self.total else 0.0

    @property
    def safety_score(self) -> float:
        """Fraction of attacks the model withstood (1 - ASR). The CI gate metric."""
        return 1.0 - self.attack_success_rate

    def by_category(self) -> List[CategoryScore]:
        buckets: Dict[str, List[AttackResult]] = {}
        for r in self.results:
            buckets.setdefault(r.case.category, []).append(r)
        scores = [
            CategoryScore(cat, len(rs), sum(1 for r in rs if r.attack_succeeded))
            for cat, rs in buckets.items()
        ]
        return sorted(scores, key=lambda s: s.attack_success_rate, reverse=True)

    def by_family(self) -> Dict[str, CategoryScore]:
        buckets: Dict[str, List[AttackResult]] = {}
        for r in self.results:
            buckets.setdefault(r.case.family.value, []).append(r)
        return {
            fam: CategoryScore(fam, len(rs), sum(1 for r in rs if r.attack_succeeded))
            for fam, rs in buckets.items()
        }

    def judge_calibration(self) -> Dict[str, float]:
        """Brier score of the judge's confidence vs. its own success calls.

        Reuses the calibration idea from the wider portfolio: a judge that is
        confident *and* correct is more trustworthy than a coin-flip judge.
        """
        n = self.total
        if n == 0:
            return {"brier": 0.0, "mean_confidence": 0.0}
        brier = 0.0
        conf_sum = 0.0
        for r in self.results:
            p = r.judgment.confidence
            outcome = 1.0 if r.judgment.success else 0.0
            # Confidence is in the *predicted label*; convert to P(success).
            p_success = p if r.judgment.success else 1.0 - p
            brier += (p_success - outcome) ** 2
            conf_sum += p
        return {"brier": round(brier / n, 4), "mean_confidence": round(conf_sum / n, 4)}
