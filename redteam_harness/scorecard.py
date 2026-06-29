"""Render a safety scorecard as HTML and JSON.

The HTML is a self-contained file (no external assets) with a per-category
attack-success heatmap and the before/after defense comparison — the artifact you
attach to a portfolio or a CI run.
"""
from __future__ import annotations

import datetime as _dt
import html
import json
from dataclasses import asdict
from typing import Dict, List, Optional

from .types import RunReport


def _color(asr: float) -> str:
    """Green (safe) -> red (high attack success)."""
    r = int(220 * asr + 30)
    g = int(200 * (1 - asr) + 30)
    return f"rgb({r},{g},60)"


def report_to_dict(report: RunReport) -> Dict:
    return {
        "label": report.label,
        "total": report.total,
        "attack_success_rate": round(report.attack_success_rate, 4),
        "safety_score": round(report.safety_score, 4),
        "judge_calibration": report.judge_calibration(),
        "by_family": {k: round(v.attack_success_rate, 4) for k, v in report.by_family().items()},
        "by_category": [
            {"category": c.category, "total": c.total, "succeeded": c.succeeded,
             "attack_success_rate": round(c.attack_success_rate, 4)}
            for c in report.by_category()
        ],
        "results": [
            {"id": r.case.id, "family": r.case.family.value, "category": r.case.category,
             "succeeded": r.attack_succeeded, "blocked": r.blocked_by_defense,
             "confidence": round(r.judgment.confidence, 3), "rationale": r.judgment.rationale}
            for r in report.results
        ],
    }


def to_json(report: RunReport, defended: Optional[RunReport] = None) -> str:
    payload = {"undefended": report_to_dict(report)}
    if defended is not None:
        payload["defended"] = report_to_dict(defended)
        payload["mitigation"] = {
            "asr_before": round(report.attack_success_rate, 4),
            "asr_after": round(defended.attack_success_rate, 4),
            "absolute_reduction": round(report.attack_success_rate - defended.attack_success_rate, 4),
        }
    return json.dumps(payload, indent=2)


def _heatmap_rows(report: RunReport) -> str:
    rows = []
    for c in report.by_category():
        asr = c.attack_success_rate
        rows.append(
            f"<tr><td>{html.escape(c.category)}</td>"
            f"<td style='background:{_color(asr)};color:#fff;text-align:center'>{asr:.0%}</td>"
            f"<td style='text-align:center'>{c.succeeded}/{c.total}</td></tr>"
        )
    return "\n".join(rows)


def to_html(report: RunReport, defended: Optional[RunReport] = None) -> str:
    cal = report.judge_calibration()
    summary = (
        f"<p><b>Target:</b> {html.escape(report.label)} &nbsp;|&nbsp; "
        f"<b>Attacks:</b> {report.total} &nbsp;|&nbsp; "
        f"<b>Attack success rate:</b> {report.attack_success_rate:.1%} &nbsp;|&nbsp; "
        f"<b>Safety score:</b> {report.safety_score:.1%}</p>"
        f"<p><b>Judge calibration:</b> Brier {cal['brier']} "
        f"(mean confidence {cal['mean_confidence']})</p>"
    )
    mitigation = ""
    if defended is not None:
        before = report.attack_success_rate
        after = defended.attack_success_rate
        mitigation = (
            "<h2>Defense impact</h2>"
            f"<p>Attack success rate: <b style='color:#c0392b'>{before:.1%}</b> "
            f"&rarr; <b style='color:#27ae60'>{after:.1%}</b> "
            f"(absolute reduction <b>{before - after:.1%}</b>)</p>"
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Red-Team Safety Scorecard</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:40px;color:#222;max-width:820px}}
 h1{{margin-bottom:0}} table{{border-collapse:collapse;width:100%;margin:12px 0}}
 td,th{{border:1px solid #ddd;padding:6px 10px}} th{{background:#f4f4f4;text-align:left}}
 .ts{{color:#888;font-size:13px}}
</style></head><body>
<h1>Red-Team Safety Scorecard</h1>
<div class="ts">generated {_dt.datetime.now().isoformat(timespec='seconds')}</div>
{summary}
{mitigation}
<h2>Attack success by category</h2>
<table><tr><th>Category</th><th>Attack success</th><th>Hits</th></tr>
{_heatmap_rows(report)}
</table>
<p class="ts">Defensive security tooling — evaluate your own models. Attack payloads
are benign control-flow probes (a placeholder secret), not weaponized content.</p>
</body></html>
"""


def write_scorecard(path: str, report: RunReport, defended: Optional[RunReport] = None) -> None:
    with open(path, "w") as fh:
        fh.write(to_html(report, defended))
