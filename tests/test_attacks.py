from redteam_harness.attacks import build_suite, expand_suite, mutate_case
from redteam_harness.attacks.mutations import MUTATORS
from redteam_harness.types import AttackFamily


def test_seed_suite_covers_all_families():
    cases = build_suite()
    families = {c.family for c in cases}
    assert AttackFamily.PROMPT_INJECTION in families
    assert AttackFamily.INDIRECT_INJECTION in families
    assert AttackFamily.JAILBREAK in families
    assert AttackFamily.MULTI_TURN in families
    assert len(cases) >= 8


def test_every_case_has_system_prompt_and_user_turn():
    for c in build_suite():
        roles = [m.role for m in c.messages]
        assert "system" in roles and "user" in roles


def test_mutation_expands_and_tags_provenance():
    seed = build_suite()
    expanded = expand_suite(seed)
    assert len(expanded) > len(seed)  # fuzzing adds variants
    variants = [c for c in expanded if c.mutated_from is not None]
    assert variants
    for v in variants:
        assert v.id.startswith(v.mutated_from)


def test_obfuscation_mutators_change_family():
    case = build_suite()[0]
    variants = mutate_case(case, ["base64", "rot13", "leetspeak", "spaced"])
    assert all(v.family is AttackFamily.OBFUSCATION for v in variants)


def test_ids_are_unique_after_expansion():
    expanded = expand_suite(build_suite())
    ids = [c.id for c in expanded]
    assert len(ids) == len(set(ids))


def test_all_mutators_produce_distinct_text():
    case = build_suite()[0]
    variants = mutate_case(case, list(MUTATORS))
    texts = {v.prompt_text for v in variants}
    assert len(texts) == len(MUTATORS)
