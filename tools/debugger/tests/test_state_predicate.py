"""Tests for the deity-mode target-state predicate language (Phase 1, Task 1)."""

from __future__ import annotations

import pytest

from tools.debugger.state_predicate import (
    Call,
    Comparison,
    Flag,
    PredicateError,
    evaluate,
    parse,
)


# --- parsing: the happy paths -----------------------------------------------


def test_parse_single_comparison():
    pred = parse("turn==3")
    assert len(pred.clauses) == 1
    clause = pred.clauses[0]
    assert isinstance(clause, Comparison)
    assert clause.field == "turn"
    assert clause.op == "=="
    assert clause.value == 3


def test_equals_alias_normalizes_to_double_equals():
    (clause,) = parse("map=ROUTE_29").clauses
    assert isinstance(clause, Comparison)
    assert clause.op == "=="
    assert clause.value == "ROUTE_29"


def test_parse_conjunction_mixed_clause_kinds():
    pred = parse("battle(boss=MORTY) and turn==3 and wild_battle")
    assert [type(c) for c in pred.clauses] == [Call, Comparison, Flag]
    call = pred.clauses[0]
    assert call.name == "battle"
    assert call.args == (("boss", "==", "MORTY"),)


def test_parse_function_with_ordered_arg():
    (call,) = parse("party_has(species=TYPHLOSION, level>=30)").clauses
    assert isinstance(call, Call)
    assert ("species", "==", "TYPHLOSION") in call.args
    assert ("level", ">=", 30) in call.args


def test_and_is_case_insensitive():
    assert len(parse("turn==1 AND wild_battle").clauses) == 2


def test_int_field_accepts_hex_literal():
    (clause,) = parse("badges==0x03").clauses
    assert clause.value == 3


def test_describe_roundtrips_readably():
    assert parse("turn>=2 and battle(boss=FALKNER)").describe() == (
        "turn>=2 and battle(boss==FALKNER)"
    )


# --- parsing: failures must surface at parse time, not frame 100000 ----------


def test_unknown_field_fails_at_parse():
    with pytest.raises(PredicateError, match="unknown field 'trun'"):
        parse("trun==3")


def test_unknown_function_fails_at_parse():
    with pytest.raises(PredicateError, match="unknown predicate function 'fight'"):
        parse("fight(boss=MORTY)")


def test_unknown_flag_fails_at_parse():
    with pytest.raises(PredicateError, match="unknown flag 'in_menu'"):
        parse("in_menu")


def test_unknown_function_arg_fails_at_parse():
    with pytest.raises(PredicateError, match="no argument 'leader'"):
        parse("battle(leader=MORTY)")


def test_int_field_rejects_identifier_value():
    with pytest.raises(PredicateError, match="expects an integer"):
        parse("turn==soon")


def test_str_field_rejects_ordered_operator():
    with pytest.raises(PredicateError, match="not valid for str field 'map'"):
        parse("map>=ROUTE_29")


def test_str_field_rejects_non_identifier_value():
    with pytest.raises(PredicateError, match="expects an identifier"):
        parse("map==12-34")


def test_empty_predicate_fails():
    with pytest.raises(PredicateError, match="empty predicate"):
        parse("   ")


def test_stray_and_makes_empty_clause():
    with pytest.raises(PredicateError, match="empty clause"):
        parse("turn==3 and ")


def test_repeated_function_arg_fails():
    with pytest.raises(PredicateError, match="repeats argument 'species'"):
        parse("party_has(species=A, species=B)")


# --- evaluation --------------------------------------------------------------


def test_evaluate_all_clauses_satisfied():
    pred = parse("battle(boss=MORTY) and turn==3")
    result = evaluate(pred, {"battle": True, "boss": "MORTY", "turn": 3})
    assert result.satisfied
    assert result.unmet == ()


def test_evaluate_reports_unmet_clauses():
    pred = parse("battle(boss=MORTY) and turn==3")
    result = evaluate(pred, {"battle": True, "boss": "MORTY", "turn": 1})
    assert not result.satisfied
    assert result.unmet == ("turn==3",)


def test_unobserved_field_is_not_satisfied():
    # The navigator must never claim a state it could not see.
    pred = parse("turn==3")
    result = evaluate(pred, {})
    assert not result.satisfied
    assert result.unmet == ("turn==3",)


def test_flag_must_be_truthy():
    pred = parse("wild_battle")
    assert not evaluate(pred, {"wild_battle": False}).satisfied
    assert evaluate(pred, {"wild_battle": True}).satisfied


def test_ordered_comparison_on_level():
    pred = parse("party_has(species=TYPHLOSION, level>=30)")
    assert evaluate(pred, {"party_has": True, "species": "TYPHLOSION", "level": 31}).satisfied
    assert not evaluate(pred, {"party_has": True, "species": "TYPHLOSION", "level": 29}).satisfied


def test_call_requires_function_flag_truthy():
    pred = parse("battle(boss=MORTY)")
    # boss matches but we are not actually in a battle -> unmet.
    assert not evaluate(pred, {"battle": False, "boss": "MORTY"}).satisfied
