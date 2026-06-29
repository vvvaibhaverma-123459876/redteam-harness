"""Demo: run the attack suite against a mock model, then measure a defense.

Fully offline and deterministic (mock target + heuristic judge). Writes an HTML
scorecard you can open in a browser.
"""
from redteam_harness import (
    HeuristicJudge,
    MockTarget,
    build_suite,
    compare_defense,
    default_pipeline,
    expand_suite,
)
from redteam_harness.scorecard import write_scorecard

print("=== redteam-harness Demo ===\n")

seed = build_suite()
cases = expand_suite(seed)
print(f"Attack suite: {len(seed)} seed cases -> {len(cases)} after mutation/fuzzing\n")

target = MockTarget()
judge = HeuristicJudge()

undefended, defended = compare_defense(target, judge, default_pipeline(), cases)

print(f"[undefended] attack success rate : {undefended.attack_success_rate:.1%}")
print(f"[defended]   attack success rate : {defended.attack_success_rate:.1%}")
print(f"             absolute mitigation  : "
      f"-{undefended.attack_success_rate - defended.attack_success_rate:.1%}")
print(f"             safety score         : {defended.safety_score:.1%}")

cal = undefended.judge_calibration()
print(f"\nJudge calibration (Brier, lower=better): {cal['brier']}  "
      f"mean confidence {cal['mean_confidence']}")

print("\nAttack success by family (undefended):")
for fam, score in sorted(undefended.by_family().items()):
    print(f"  {fam:<22} {score.attack_success_rate:>5.0%}  ({score.succeeded}/{score.total})")

write_scorecard("scorecard.html", undefended, defended)
print("\nScorecard written to scorecard.html")
print("Demo complete.")
