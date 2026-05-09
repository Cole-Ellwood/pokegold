#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.damage_debugger import oracle as damage_oracle
from tools.boss_ai_preference.data import (
    append_label,
    build_report,
    load_fixtures,
    load_labels,
    load_preferences,
    render_markdown_report,
    save_preference,
)
from tools.boss_ai_preference.damage_estimates import (
    attach_damage_estimates,
    estimate_move_damage,
    oracle_item_id,
    pokemon_data,
)
from tools.boss_ai_preference.threat_availability import (
    available_species_for_checkpoint,
    build_threat_report,
    checkpoint_for_leader,
    direct_tm_moves_for_checkpoint,
    direct_tm_sources,
    legal_moves_for_species,
    threats_for_pokemon,
    write_threat_report,
)


def main() -> int:
    fixtures = load_fixtures()
    if len(fixtures) < 10:
        raise SystemExit("expected at least 10 Boss AI preference fixtures")
    if len(fixtures) > 20:
        raise SystemExit("MVP fixture set should stay small enough to review")

    first = fixtures[0]
    first_action = first["actions"][0]
    second_action = first["actions"][1]
    annotated = attach_damage_estimates([first])
    first_estimate = annotated[0]["actions"][0].get("damage_estimate")
    if not first_estimate or "%" not in first_estimate["label"]:
        raise SystemExit("expected attacking preference actions to include damage estimates")

    bugsy = next(
        fixture for fixture in fixtures if fixture["id"] == "bugsy_scyther_vs_quilava_fire_pressure"
    )
    falkner = next(
        fixture for fixture in fixtures if fixture["id"] == "falkner_pidgeotto_vs_geodude_rock_risk"
    )
    jasmine = next(
        fixture for fixture in fixtures if fixture["id"] == "jasmine_steelix_vs_quilava_fire_threat"
    )
    jasmine_text = " ".join(
        [jasmine["training_focus"], *jasmine["state"].get("public_notes", [])]
    )
    if "Steel/Dragon" not in jasmine_text:
        raise SystemExit("Jasmine Steelix fixture should reflect Steel/Dragon typing")
    if "Imperial Scales" not in jasmine_text:
        raise SystemExit("Jasmine Steelix fixture should call out Imperial Scales as public info")

    bugsy_checkpoint = checkpoint_for_leader("Bugsy")
    bugsy_quilava_moves = legal_moves_for_species("QUILAVA", bugsy_checkpoint)
    if "FIRE_BLAST" in bugsy_quilava_moves:
        raise SystemExit("Bugsy checkpoint must not treat unavailable Fire Blast as available")
    if "EMBER" not in bugsy_quilava_moves:
        raise SystemExit("Bugsy checkpoint should source Quilava Ember from level-up data")

    falkner_species = available_species_for_checkpoint(checkpoint_for_leader("Falkner"))
    bugsy_species = available_species_for_checkpoint(bugsy_checkpoint)
    whitney_species = available_species_for_checkpoint(checkpoint_for_leader("Whitney"))
    morty_species = available_species_for_checkpoint(checkpoint_for_leader("Morty"))
    chuck_species = available_species_for_checkpoint(checkpoint_for_leader("Chuck"))
    if "MAGIKARP" in falkner_species:
        raise SystemExit("Falkner checkpoint must not expose rod/Surf-only Magikarp")
    if "old_rod_fishing" not in bugsy_species.get("MAGIKARP", set()):
        raise SystemExit("Bugsy checkpoint should expose Old Rod fishing after Route 32")
    if "DRATINI" not in whitney_species:
        raise SystemExit("Whitney checkpoint should source Goldenrod Game Corner prize Pokemon")
    if "SUDOWOODO" in whitney_species:
        raise SystemExit("Whitney checkpoint must not expose post-Whitney Sudowoodo static")
    if "static_encounter:Route36.asm" not in morty_species.get("SUDOWOODO", set()):
        raise SystemExit("Morty checkpoint should expose Route 36 Sudowoodo static")
    if "surf_encounter" not in chuck_species.get("TENTACOOL", set()):
        raise SystemExit("mid-Johto checkpoints should expose Surf-gated water encounters")

    whitney_quilava_moves = legal_moves_for_species("QUILAVA", checkpoint_for_leader("Whitney"))
    if "FIRE_BLAST" not in whitney_quilava_moves:
        raise SystemExit("Whitney checkpoint should expose Quilava Fire Blast after Goldenrod TM access")
    if "tm_available" not in set(whitney_quilava_moves["FIRE_BLAST"]):
        raise SystemExit("Whitney Fire Blast should name direct TM access")

    bugsy_threats = build_threat_report([bugsy])["fixture_threats"][bugsy["id"]]
    threat_by_move = {threat["move_id"]: threat for threat in bugsy_threats}
    if threat_by_move.get("EMBER", {}).get("likelihood") != 99:
        raise SystemExit("revealed Bugsy Quilava Ember should be a 99% incoming threat")
    if "FIRE_BLAST" in threat_by_move:
        raise SystemExit("Bugsy UI threat list should not show unavailable Fire Blast")

    if oracle_item_id("Sharp Beak") != damage_oracle.HELD_SHARP_BEAK:
        raise SystemExit("preference damage estimates should map visible type-item boosts")
    if oracle_item_id("Polkadot Bow") != damage_oracle.HELD_POLKADOT_BOW:
        raise SystemExit("preference damage estimates should map Polkadot Bow as a Normal boost")

    normal_boost_kwargs = {
        "attacker_level": 30,
        "move_bp": 50,
        "move_type": damage_oracle.NORMAL,
        "is_physical": True,
        "attacker_atk": 80,
        "defender_def": 70,
        "attacker_types": (damage_oracle.NORMAL, damage_oracle.NORMAL),
        "defender_types": (damage_oracle.FIRE, damage_oracle.FIRE),
    }
    no_item_damage = damage_oracle.predict_damage(
        damage_oracle.BattleInputs(**normal_boost_kwargs)
    )
    pink_bow_damage = damage_oracle.predict_damage(
        damage_oracle.BattleInputs(
            **normal_boost_kwargs,
            user_item=damage_oracle.HELD_PINK_BOW,
        )
    )
    polkadot_bow_damage = damage_oracle.predict_damage(
        damage_oracle.BattleInputs(
            **normal_boost_kwargs,
            user_item=damage_oracle.HELD_POLKADOT_BOW,
        )
    )
    if polkadot_bow_damage != pink_bow_damage or polkadot_bow_damage <= no_item_damage:
        raise SystemExit("damage oracle should treat Polkadot Bow like Pink Bow")

    direct_sources = direct_tm_sources()
    if "VictoryRoad.asm" not in direct_sources.get("EARTHQUAKE", []):
        raise SystemExit("direct TM parser should include Victory Road TM_EARTHQUAKE itemball")
    if "Route27.asm" not in direct_sources.get("SOLARBEAM", []):
        raise SystemExit("direct TM parser should include Route 27 TM_SOLARBEAM itemball")
    champion_tms = direct_tm_moves_for_checkpoint(checkpoint_for_leader("Champion Lance"))
    if not {"EARTHQUAKE", "SOLARBEAM"} <= champion_tms:
        raise SystemExit("Champion checkpoint should include pre-League item-ball TM rewards")
    postgame_tms = direct_tm_moves_for_checkpoint(checkpoint_for_leader("Brock"))
    if not {"EARTHQUAKE", "SOLARBEAM"} <= postgame_tms:
        raise SystemExit("postgame checkpoints should include item-ball TM rewards")

    bayleef = {"species": "Bayleef", "level": 20, "hp": "100%"}
    clefairy = {"species": "Clefairy", "level": 19, "hp": "100%", "item": "Evolite"}
    field = {"weather": "none", "screens": "none"}
    giga_drain = estimate_move_damage("GIGA_DRAIN", bayleef, clefairy, field)
    if not giga_drain or giga_drain["high_percent"] > 35:
        raise SystemExit("Evolite Clefairy should reduce Bayleef Giga Drain below old rough estimate")

    steelix_data = pokemon_data("Steelix")
    if steelix_data is None or steelix_data.type_names != ("STEEL", "DRAGON"):
        raise SystemExit("Steelix should be parsed as Steel/Dragon for preference damage estimates")

    quilava = {"species": "Quilava", "level": 34, "hp": "100%"}
    jasmine_steelix = {"species": "Steelix", "level": 34, "hp": "69%", "item": "Metal Coat"}
    flame_wheel = estimate_move_damage("FLAME_WHEEL", quilava, jasmine_steelix, field)
    if not flame_wheel or flame_wheel["high_percent"] > 35:
        raise SystemExit("Steelix's Dragon defender passive should lower neutral Fire pressure")

    ghost_target = {"species": "Gengar", "level": 34, "hp": "100%"}
    steelix_tackle = estimate_move_damage("TACKLE", jasmine_steelix, ghost_target, field)
    pidgeotto_tackle = estimate_move_damage(
        "TACKLE",
        {"species": "Pidgeotto", "level": 34, "hp": "100%"},
        ghost_target,
        field,
    )
    if not steelix_tackle or steelix_tackle["high_percent"] <= 0:
        raise SystemExit("Dragon's Majesty should let Steelix convert immunities into resistance")
    if not pidgeotto_tackle or pidgeotto_tackle["high_percent"] != 0:
        raise SystemExit("non-Dragon attackers should still show 0% into true immunities")

    falkner_threats = build_threat_report([falkner])["fixture_threats"][falkner["id"]]
    if any(threat["species"] == "Chikorita" for threat in falkner_threats):
        raise SystemExit(
            "Falkner UI threat list should not show Chikorita as pressure into revealed Gust"
        )

    full_slots = threats_for_pokemon(
        {
            "species": "Quilava",
            "level": 21,
            "revealed_moves": ["Ember", "Quick Attack", "Smokescreen", "Tackle"],
        },
        {"species": "Scyther", "level": 17, "hp": "81%", "item": "Silverpowder"},
        {"weather": "none", "screens": "none"},
        checkpoint_for_leader("Whitney"),
        immediacy="active",
    )
    fire_blast = next(threat for threat in full_slots if threat["move_id"] == "FIRE_BLAST")
    if fire_blast["likelihood"] != 0:
        raise SystemExit("unrevealed Fire Blast should be 0% when four moves are already revealed")

    with tempfile.TemporaryDirectory() as tmp:
        labels_path = Path(tmp) / "labels.jsonl"
        preferences_path = Path(tmp) / "preferences.jsonl"
        threat_report_path = Path(tmp) / "threat_report.md"
        threat_json_path = Path(tmp) / "threat_report.json"
        append_label(
            fixture_id=first["id"],
            action_id=first_action["id"],
            label="best",
            rank=1,
            note="audit smoke label",
            labels_path=labels_path,
        )
        append_label(
            fixture_id=first["id"],
            action_id=first_action["id"],
            label="bad",
            rank=3,
            note="audit conflict label",
            labels_path=labels_path,
        )
        save_preference(
            fixture_id=first["id"],
            action_a_id=first_action["id"],
            action_b_id=second_action["id"],
            choice="b_better",
            preferred_action_id=second_action["id"],
            action_tags={
                first_action["id"]: ["misses_public_threat"],
                second_action["id"]: ["reduces_risk", "calculated_risk"],
            },
            note="audit pairwise smoke preference",
            preferences_path=preferences_path,
        )
        save_preference(
            fixture_id=first["id"],
            action_a_id=first_action["id"],
            action_b_id=second_action["id"],
            choice="both_good",
            action_tags={
                first_action["id"]: ["too_passive"],
                second_action["id"]: ["reduces_risk"],
            },
            note="audit replacement preference",
            preferences_path=preferences_path,
        )
        save_preference(
            fixture_id=first["id"],
            action_a_id=second_action["id"],
            action_b_id=first_action["id"],
            choice="a_better",
            action_tags={
                first_action["id"]: ["too_passive"],
                second_action["id"]: ["reduces_risk"],
            },
            note="audit swapped-order replacement preference",
            preferences_path=preferences_path,
        )
        labels = load_labels(labels_path, fixtures=fixtures)
        preferences = load_preferences(preferences_path, fixtures=fixtures)
        report = build_report(fixtures, labels, preferences)
        markdown = render_markdown_report(report)
        if len(labels) != 2:
            raise SystemExit("expected audit smoke labels to round-trip")
        if len(preferences) != 1:
            raise SystemExit("expected audit smoke preference to round-trip")
        if preferences[0]["choice"] != "a_better":
            raise SystemExit("expected repeated pairwise preference save to replace old row")
        if preferences[0]["action_tags"][second_action["id"]] != ["reduces_risk"]:
            raise SystemExit("expected audit replacement action tags to round-trip")
        if not report["conflicts"]:
            raise SystemExit("expected duplicate/conflicting labels to be flagged")
        if report["preference_count"] != 1:
            raise SystemExit("expected report to count pairwise preferences")
        if first["id"] not in markdown:
            raise SystemExit("expected report to include labeled fixture id")
        threat_report = write_threat_report(
            fixtures,
            out_path=threat_report_path,
            json_out_path=threat_json_path,
        )
        if len(threat_report["checkpoints"]) < 16:
            raise SystemExit("expected threat report to cover Johto and Kanto boss checkpoints")
        if "Bugsy" not in threat_report_path.read_text(encoding="utf-8"):
            raise SystemExit("expected threat report markdown to include checkpoint rows")
        if not threat_json_path.exists():
            raise SystemExit("expected threat report JSON to be written")

    print(
        "Boss AI preference audit passed: "
        f"{len(fixtures)} fixtures, label persistence/report smoke ok."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
