from redteam_harness import (
    HeuristicJudge,
    MockTarget,
    RedTeamHarness,
    build_suite,
    compare_defense,
    default_pipeline,
    expand_suite,
)


def test_undefended_run_has_nonzero_attack_success():
    cases = expand_suite(build_suite())
    report = RedTeamHarness(MockTarget(), HeuristicJudge()).run(cases)
    assert report.total == len(cases)
    assert report.attack_success_rate > 0.0  # the mock is genuinely vulnerable


def test_defense_reduces_attack_success():
    cases = expand_suite(build_suite())
    undefended, defended = compare_defense(
        MockTarget(), HeuristicJudge(), default_pipeline(), cases)
    assert defended.attack_success_rate < undefended.attack_success_rate
    assert defended.safety_score > undefended.safety_score


def test_defense_drives_safety_high():
    cases = expand_suite(build_suite())
    _, defended = compare_defense(
        MockTarget(), HeuristicJudge(), default_pipeline(), cases)
    # The layered defense should withstand essentially all attacks here.
    assert defended.safety_score >= 0.95


def test_report_aggregations_consistent():
    cases = expand_suite(build_suite())
    report = RedTeamHarness(MockTarget(), HeuristicJudge()).run(cases)
    by_cat_total = sum(c.total for c in report.by_category())
    assert by_cat_total == report.total
    by_cat_succ = sum(c.succeeded for c in report.by_category())
    assert by_cat_succ == report.succeeded


def test_judge_calibration_reported():
    cases = build_suite()
    report = RedTeamHarness(MockTarget(), HeuristicJudge()).run(cases)
    cal = report.judge_calibration()
    assert 0.0 <= cal["brier"] <= 1.0
    assert 0.0 <= cal["mean_confidence"] <= 1.0
