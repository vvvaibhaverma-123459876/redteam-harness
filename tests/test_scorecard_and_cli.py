import json

from redteam_harness import (
    HeuristicJudge,
    MockTarget,
    RedTeamHarness,
    build_suite,
    compare_defense,
    default_pipeline,
)
from redteam_harness.cli import main
from redteam_harness.scorecard import to_html, to_json


def test_scorecard_html_renders_with_mitigation():
    cases = build_suite()
    undefended, defended = compare_defense(
        MockTarget(), HeuristicJudge(), default_pipeline(), cases)
    html = to_html(undefended, defended)
    assert "<html" in html
    assert "Attack success by category" in html
    assert "Defense impact" in html


def test_scorecard_json_roundtrips():
    cases = build_suite()
    report = RedTeamHarness(MockTarget(), HeuristicJudge()).run(cases)
    data = json.loads(to_json(report))
    assert "undefended" in data
    assert data["undefended"]["total"] == report.total


def test_cli_list_runs():
    assert main(["list", "--no-mutate"]) == 0


def test_cli_run_with_defense(tmp_path):
    html = tmp_path / "sc.html"
    rc = main(["run", "--provider", "mock", "--judge", "heuristic", "--defense",
               "--html", str(html)])
    assert rc == 0
    assert html.exists()


def test_cli_gate_passes_when_defended():
    # Defended safety should clear a high bar => exit 0.
    rc = main(["run", "--provider", "mock", "--defense", "--fail-under", "0.95"])
    assert rc == 0


def test_cli_gate_fails_when_undefended():
    # Undefended mock is vulnerable => safety below 0.95 => exit 1.
    rc = main(["run", "--provider", "mock", "--fail-under", "0.95"])
    assert rc == 1
