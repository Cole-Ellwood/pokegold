from __future__ import annotations

from tools.pokemon_mastery import retrieve_cases as rc


def make_case(case_id: str, user: str, opp: str, tb: str = "mid", user_sides=(), opp_sides=(), tier="study", lesson="x"):
    return {
        "case_id": case_id,
        "replay_id": "r",
        "turn": 5,
        "side": "p1",
        "tier": tier,
        "fingerprint": {
            "active_user": {"species": user},
            "active_opp": {"species": opp},
            "turn_bucket": tb,
            "side_conditions_user": list(user_sides),
            "side_conditions_opp": list(opp_sides),
        },
        "pro_action": {"type": "move", "move": "Body Slam"},
        "pro_reasoning_class": "converter",
        "failure_mode": "hit_top",
        "lesson": lesson,
        "created_at": "x",
    }


def test_level0_exact_match():
    cases = [
        make_case("a", "Snorlax", "Cloyster", "mid", (), ()),
        make_case("b", "Snorlax", "Cloyster", "early", (), ()),
    ]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    assert [r.case["case_id"] for r in out][:1] == ["a"]
    assert out[0].match_level == 0


def test_level1_relax_turn():
    cases = [
        make_case("a", "Snorlax", "Cloyster", "early", (), ()),
    ]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    assert [r.case["case_id"] for r in out] == ["a"]
    assert out[0].match_level == 1


def test_level2_relax_sides():
    cases = [
        make_case("a", "Snorlax", "Cloyster", "early", ("Spikes",), ()),
    ]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    assert out[0].match_level == 2


def test_level3_single_side_species():
    cases = [
        make_case("a", "Snorlax", "Forretress", "early", (), ()),  # opp differs
    ]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    assert out[0].match_level == 3


def test_no_matches_returns_empty():
    cases = [make_case("a", "Tauros", "Vaporeon", "early")]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    assert out == []


def test_k_limit_respected():
    cases = [make_case(f"c{i}", "Snorlax", "Cloyster", "mid") for i in range(10)]
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=3)
    assert len(out) == 3
    assert all(r.match_level == 0 for r in out)


def test_dedup_across_levels():
    cases = [make_case("a", "Snorlax", "Cloyster", "mid")]  # matches L0
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    out = rc.retrieve(fp, cases, k=5)
    # Even though "a" matches L0, L1, L2, L3, it should appear only once.
    assert len(out) == 1
    assert out[0].match_level == 0


def test_filters_non_study_tier():
    cases = [
        make_case("v1", "Snorlax", "Cloyster", "mid", tier="validation"),
        make_case("e1", "Snorlax", "Cloyster", "mid", tier="sealed_exam"),
        make_case("s1", "Snorlax", "Cloyster", "mid", tier="study"),
    ]
    # load_cases filters; retrieve operates on filtered.
    fp = {"active_user": {"species": "Snorlax"}, "active_opp": {"species": "Cloyster"}, "turn_bucket": "mid", "side_conditions_user": [], "side_conditions_opp": []}
    import json
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "c.jsonl"
        with p.open("w", encoding="utf-8") as f:
            for c in cases:
                f.write(json.dumps(c) + "\n")
        loaded = rc.load_cases(p)
    assert [c["case_id"] for c in loaded] == ["s1"]
    out = rc.retrieve(fp, loaded, k=5)
    assert [r.case["case_id"] for r in out] == ["s1"]


def test_load_cases_empty_file(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert rc.load_cases(p) == []


def test_load_cases_missing_file(tmp_path):
    assert rc.load_cases(tmp_path / "nope.jsonl") == []


def test_format_retrieval_for_predictor_empty():
    assert rc.format_retrieval_for_predictor([]) == "(no cases fired)"


def test_format_retrieval_for_predictor_renders_lesson():
    case = make_case("a", "Snorlax", "Cloyster", "mid", lesson="active damage before script")
    out = rc.format_retrieval_for_predictor([rc.RetrievedCase(case=case, match_level=0)])
    assert "active damage before script" in out
    assert "L0" in out
    assert "a" in out


def test_cli_rejects_when_neither_fingerprint_nor_log_supplied(capsys):
    import pytest
    with pytest.raises(SystemExit):
        rc.main(["--k", "3"])
    err = capsys.readouterr().err
    assert "--fingerprint" in err or "--log" in err


def test_cli_rejects_when_both_fingerprint_and_log_supplied(tmp_path, capsys):
    import pytest
    fp_path = tmp_path / "fp.json"
    fp_path.write_text('{"active_user":{"species":"X"},"active_opp":{"species":"Y"},"turn_bucket":"mid","side_conditions_user":[],"side_conditions_opp":[]}', encoding="utf-8")
    log_path = tmp_path / "r.log"
    log_path.write_text("|gametype|singles\n|player|p1|a||\n|player|p2|b||\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        rc.main(["--fingerprint", str(fp_path), "--log", str(log_path), "--turn", "1", "--side", "p1"])
    err = capsys.readouterr().err
    assert "mutually exclusive" in err


def test_cli_rejects_log_without_turn_or_side(tmp_path, capsys):
    import pytest
    log_path = tmp_path / "r.log"
    log_path.write_text("|gametype|singles\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        rc.main(["--log", str(log_path), "--turn", "1"])
    err = capsys.readouterr().err
    assert "--turn" in err and "--side" in err


def test_cli_log_mode_round_trip(tmp_path, capsys):
    """End-to-end: --log/--turn/--side computes fingerprint, retrieves matching case, prints lesson."""
    # Minimal replay with one turn switched-in.
    log = tmp_path / "r.log"
    log.write_text(
        "|gametype|singles\n"
        "|player|p1|alice||\n"
        "|player|p2|bob||\n"
        "|teamsize|p1|6\n"
        "|teamsize|p2|6\n"
        "|gen|2\n"
        "|tier|[Gen 2] OU\n"
        "|switch|p1a: Snorlax|Snorlax, M|100/100\n"
        "|switch|p2a: Cloyster|Cloyster, M|100/100\n"
        "|turn|1\n",
        encoding="utf-8",
    )
    # Cases file with a single Snorlax-vs-Cloyster entry.
    cases_path = tmp_path / "cases.jsonl"
    import json as _json
    case = make_case("snorlax_vs_cloyster_lesson", "Snorlax", "Cloyster", "t1", lesson="curse over body slam")
    cases_path.write_text(_json.dumps(case) + "\n", encoding="utf-8")
    rc.main([
        "--log", str(log),
        "--turn", "1",
        "--side", "p1",
        "--cases", str(cases_path),
        "--k", "5",
    ])
    out = capsys.readouterr().out
    assert "curse over body slam" in out
    assert "L0" in out
