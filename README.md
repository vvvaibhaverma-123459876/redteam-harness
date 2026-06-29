# redteam-harness

**Automated LLM adversarial-robustness evaluation.** Systematically attacks a
model (or agent) with a versioned, *fuzzed* attack suite, judges each response,
measures how much a defense stack helps, and emits a safety **scorecard** that
can gate CI.

> **Defensive security tooling.** This evaluates *your own* models. Attack
> payloads are well-known, published *control-flow* probes against a placeholder
> secret (does the model follow injected instructions / drop its guardrails) —
> not weaponized content.

This is the capstone of a reliability-focused portfolio: the other projects
*measure* calibration and provenance; this one *attacks* a model's guardrails and
proves a defense works.

## What it does

| Stage | Component | Notes |
|---|---|---|
| **Attack library** | `attacks/library.py` | Versioned cases across prompt-injection, indirect/RAG injection, jailbreak personas, and multi-turn *crescendo* escalation |
| **Mutation / fuzzing** | `attacks/mutations.py` | Expands each seed into variants (base64, ROT13, leetspeak, token-spacing, paraphrase, translation framing) so coverage isn't a static list |
| **Targets** | `targets/` | Provider-agnostic: deterministic `mock`, plus optional Anthropic / OpenAI backends |
| **Judges** | `judges/` | Heuristic refusal/leak detector (deterministic, CI-friendly) **and** LLM-as-judge, with **judge calibration** (Brier score) reported |
| **Defenses** | `defenses/` | Composable: input sanitizer, system-prompt hardener, output filter — measured *before vs. after* |
| **Scorecard + gate** | `scorecard.py`, `cli.py` | Self-contained HTML heatmap + JSON, and a `--fail-under` exit code for CI |

The entire core is **pure-stdlib and fully unit-tested** (32 tests) against the
mock target, so CI is fast and needs no API keys.

## Headline result (mock target, default suite)

```
Attack suite: 9 seed cases -> 63 after mutation/fuzzing

[undefended] attack success rate : 88.9%
[defended]   attack success rate :  0.0%
             absolute mitigation  : -88.9%
             safety score         : 100.0%

Judge calibration (Brier, lower=better): 0.0015   mean confidence 0.971

Attack success by family (undefended):
  prompt_injection    100% (9/9)     indirect_injection  100% (6/6)
  multi_turn          100% (3/3)     obfuscation          89% (32/36)
  jailbreak            67% (6/9)
```

The layered defense (sanitize untrusted input → harden the system prompt → filter
outputs) takes the deliberately-vulnerable mock from 88.9% attack success to 0%.

## Quickstart

```bash
pip install -e ".[dev]"          # core is dependency-free

python demo.py                   # runs the suite + defense, writes scorecard.html

redteam-harness list             # show the (fuzzed) attack suite
redteam-harness run --provider mock --defense --html scorecard.html
redteam-harness run --provider mock --defense --fail-under 0.95   # CI gate (exit code)
```

### Against a real model

```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY=...
redteam-harness run --provider anthropic --model claude-opus-4-8 \
  --judge llm --defense --html scorecard.html --fail-under 0.95
```

`--judge llm` grades with an LLM-as-judge and reports its Brier calibration so you
know how much to trust the verdicts.

## CI gate

`run --fail-under 0.95` exits non-zero when the safety score (1 − attack success
rate) drops below the threshold — drop it into a workflow to block a regression:

```yaml
- run: redteam-harness run --provider mock --defense --fail-under 0.95
```

(This repo's own CI runs exactly that step.)

## Architecture

```
 build_suite() ─► expand_suite() ─►  [AttackCase ...]
                  (mutation/fuzz)          │
                                           ▼
        ┌────────────── RedTeamHarness.run() ──────────────┐
        │  Defense.transform_input ─► Target.generate ─►   │
        │  Defense.filter_output  ─►  Judge.evaluate       │
        └───────────────────────┬──────────────────────────┘
                                ▼
                          RunReport  ─►  scorecard (HTML heatmap + JSON)
                       (ASR, by family/category, judge Brier, before/after)
```

Every seam is an ABC (`Target`, `Judge`, `Defense`), so swapping in a real model,
a stronger judge, or a custom guardrail is a one-class change.

## Testing

```bash
pytest -q     # 32 tests, pure-stdlib, run in CI on 3.10–3.12
```

## License

MIT
