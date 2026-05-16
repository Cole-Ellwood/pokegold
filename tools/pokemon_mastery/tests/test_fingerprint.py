from __future__ import annotations

from tools.pokemon_mastery import fingerprint as fp
from tools.pokemon_mastery import replay_turn_pause as rtp


def test_hp_bucket_unknown_inputs():
    assert fp.hp_bucket(None) == "unknown"
    assert fp.hp_bucket("") == "unknown"
    assert fp.hp_bucket("?") == "unknown"
    assert fp.hp_bucket("unknown") == "unknown"


def test_hp_bucket_fnt():
    assert fp.hp_bucket("0 fnt") == "0"
    assert fp.hp_bucket("0") == "0"
    assert fp.hp_bucket("fnt") == "0"


def test_hp_bucket_fractions():
    assert fp.hp_bucket("1/100") == "<=25%"
    assert fp.hp_bucket("25/100") == "<=25%"
    assert fp.hp_bucket("26/100") == "26-50%"
    assert fp.hp_bucket("50/100") == "26-50%"
    assert fp.hp_bucket("51/100") == "51-75%"
    assert fp.hp_bucket("75/100") == "51-75%"
    assert fp.hp_bucket("76/100") == "76-99%"
    assert fp.hp_bucket("99/100") == "76-99%"
    assert fp.hp_bucket("100/100") == "100%"


def test_hp_bucket_percent_strings():
    assert fp.hp_bucket("84%") == "76-99%"
    assert fp.hp_bucket("100%") == "100%"
    assert fp.hp_bucket("12%") == "<=25%"


def test_hp_bucket_handles_status_suffix():
    assert fp.hp_bucket("60/100 par") == "51-75%"
    assert fp.hp_bucket("0 fnt") == "0"


def test_turn_bucket_boundaries():
    assert fp.turn_bucket(1) == "t1"
    assert fp.turn_bucket(2) == "early"
    assert fp.turn_bucket(6) == "early"
    assert fp.turn_bucket(7) == "mid"
    assert fp.turn_bucket(15) == "mid"
    assert fp.turn_bucket(16) == "late"
    assert fp.turn_bucket(25) == "late"
    assert fp.turn_bucket(26) == "endgame"
    assert fp.turn_bucket(99) == "endgame"


def build_state() -> rtp.ReplayState:
    state = rtp.ReplayState(gen="2", tier="[Gen 2] OU")
    p1 = state.sides["p1"]
    p2 = state.sides["p2"]
    p1.active = "Snorlax"
    p1.seen["Snorlax"] = rtp.MonState(
        species="Snorlax",
        hp="84/100",
        status="par",
        moves={"Body Slam", "Curse"},
        boosts={"atk": 2, "def": 1},
    )
    p1.seen["Skarmory"] = rtp.MonState(
        species="Skarmory",
        hp="100/100",
        moves={"Whirlwind"},
    )
    p1.side_conditions.add("Spikes")
    p2.active = "Cloyster"
    p2.seen["Cloyster"] = rtp.MonState(
        species="Cloyster",
        hp="60/100",
        status="slp",
        moves={"Spikes", "Surf"},
    )
    return state


def test_fingerprint_shape_p1():
    state = build_state()
    out = fp.fingerprint_from_state(state, turn=7, side="p1")
    assert out["active_user"]["species"] == "Snorlax"
    assert out["active_user"]["hp_bucket"] == "76-99%"
    assert out["active_user"]["status"] == "par"
    assert out["active_user"]["boosts"] == {"atk": 2, "def": 1}
    assert out["active_user"]["revealed_moves"] == ["Body Slam", "Curse"]
    assert out["active_opp"]["species"] == "Cloyster"
    assert out["active_opp"]["status"] == "slp"
    assert out["turn_bucket"] == "mid"
    assert out["side_conditions_user"] == ["Spikes"]
    assert out["side_conditions_opp"] == []
    assert {f for f in out["decision_relevant_features"]} >= {
        "user_active_statused",
        "opp_active_statused",
        "user_active_positively_boosted",
        "opp_has_spikes_on_user",
    }
    # active is excluded from seen summary
    seen_species = [m["species"] for m in out["seen_user"]]
    assert "Snorlax" not in seen_species
    assert "Skarmory" in seen_species


def test_fingerprint_perspective_flips_for_p2():
    state = build_state()
    p1_fp = fp.fingerprint_from_state(state, turn=7, side="p1")
    p2_fp = fp.fingerprint_from_state(state, turn=7, side="p2")
    assert p1_fp["active_user"]["species"] == p2_fp["active_opp"]["species"]
    assert p1_fp["active_opp"]["species"] == p2_fp["active_user"]["species"]
    # spikes were on p1's side; from p2's view that's "opp_has_spikes_on_user"
    # NO — p2 perspective: p1 is opp; spikes on p1's side = opp_user side. Let me re-derive:
    # user_sides = state.sides[side='p2'].side_conditions = []
    # opp_sides  = state.sides[other='p1'].side_conditions = ['Spikes']
    # so derive_features sees opp_has_spikes_on_user only when 'Spikes' in user_sides;
    # here 'Spikes' is in opp_sides, so feature = user_has_spikes_on_opp.
    assert "user_has_spikes_on_opp" in p2_fp["decision_relevant_features"]


def test_fingerprint_rejects_bad_side():
    state = build_state()
    import pytest
    with pytest.raises(ValueError):
        fp.fingerprint_from_state(state, turn=1, side="p3")


def test_fingerprint_hash_stable_and_matches_definition():
    state = build_state()
    out = fp.fingerprint_from_state(state, turn=7, side="p1")
    h1 = fp.fingerprint_hash(out)
    h2 = fp.fingerprint_hash(out)
    assert h1 == h2
    assert len(h1) == 16
    # Same active species pair + same turn_bucket + same side conditions => same hash
    out2 = fp.fingerprint_from_state(state, turn=8, side="p1")  # also "mid"
    assert fp.fingerprint_hash(out2) == h1
    # Different active opp species => different hash
    state2 = build_state()
    state2.sides["p2"].active = "Zapdos"
    state2.sides["p2"].seen["Zapdos"] = rtp.MonState(species="Zapdos", hp="100/100")
    out3 = fp.fingerprint_from_state(state2, turn=7, side="p1")
    assert fp.fingerprint_hash(out3) != h1


def test_fingerprint_hash_matches_verify_case_breadth_expectation():
    # The verify_case_breadth.py module imports fingerprint_hash from here.
    # Verify the import is the same function (not a stale copy).
    from tools.pokemon_mastery import verify_case_breadth
    assert verify_case_breadth.fingerprint_hash is fp.fingerprint_hash
