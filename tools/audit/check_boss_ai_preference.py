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
    PreferenceDataError,
    append_label,
    build_report,
    load_fixtures,
    load_labels,
    load_preferences,
    render_markdown_report,
    save_preference,
)
from tools.boss_ai_preference.active_queue import build_active_queue
from tools.boss_ai_preference.benchmark_positions import (
    build_benchmark_mutation_report,
    build_benchmark_policy_answers,
    build_benchmark_report,
    load_benchmark_oracles,
    load_benchmarks,
)
from tools.boss_ai_preference.benchmark_harvest import (
    build_benchmark_harvest_report,
    build_benchmark_label_queue,
)
from tools.boss_ai_preference.boss_team import (
    attach_boss_teams,
    boss_team_for_fixture,
    boss_team_source_for_fixture,
    party_for_fixture,
    species_key,
)
from tools.boss_ai_preference.counterfactuals import build_counterfactual_report
from tools.boss_ai_preference.damage_estimates import (
    attach_damage_estimates,
    estimate_move_damage,
    oracle_item_id,
    pokemon_data,
)
from tools.boss_ai_preference.features import build_feature_report
from tools.boss_ai_preference.final_report import build_final_report
from tools.boss_ai_preference.lessons import build_lesson_report
from tools.boss_ai_preference.long_battle_review import build_long_battle_review_report
from tools.boss_ai_preference.plan_queue import build_coach_report, build_plan_queue
from tools.boss_ai_preference.plans import generate_plan_cards, generated_plan_ids_by_fixture
from tools.boss_ai_preference.proposals import build_proposal_report
from tools.boss_ai_preference.reward_model import build_reward_model_report
from tools.boss_ai_preference.rollouts import project_plan
from tools.boss_ai_preference.trajectory_data import (
    build_trajectory_report,
    demonstration_action_ids_for_fixture,
    load_plan_demonstrations,
    load_trajectory_preferences,
    save_plan_demonstration,
    save_trajectory_preference,
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
from tools.boss_ai_preference.type_evidence import build_type_evidence_report


EXPECTED_FIXTURE_COUNT = 59


def main() -> int:
    fixtures = load_fixtures()
    if len(fixtures) != EXPECTED_FIXTURE_COUNT:
        raise SystemExit(
            f"expected current {EXPECTED_FIXTURE_COUNT}-fixture Boss AI preference corpus"
        )
    missing_bench_state = [
        fixture["id"]
        for fixture in fixtures
        if "bench_state" not in fixture.get("state", {}).get("boss", {})
    ]
    if missing_bench_state:
        raise SystemExit(f"expected every fixture to include bench_state: {missing_bench_state[:3]}")
    for fixture in fixtures:
        boss = fixture["state"]["boss"]
        bench_species = list(boss.get("bench", []))
        state_species = [row.get("species") for row in boss.get("bench_state", [])]
        if state_species != bench_species:
            raise SystemExit(f"expected bench_state to match bench order for {fixture['id']}")
    stale_party_members = []
    for fixture in fixtures:
        party = party_for_fixture(fixture)
        if party is None:
            source = boss_team_source_for_fixture(fixture)
            if not source.get("exact"):
                stale_party_members.append(f"{fixture['id']}: no exact source party")
            continue
        source_species = {species_key(mon.species) for mon in party.mons}
        boss = fixture["state"]["boss"]
        active = boss.get("active", {})
        fixture_species = [active.get("species"), *boss.get("bench", [])]
        missing_species = [
            species
            for species in fixture_species
            if species and species_key(str(species)) not in source_species
        ]
        if missing_species:
            missing_list = ", ".join(str(species) for species in missing_species)
            stale_party_members.append(f"{fixture['id']}: {missing_list}")
    if stale_party_members:
        sample = "; ".join(stale_party_members[:5])
        raise SystemExit(f"expected fixture boss species to come from source parties: {sample}")
    real_preferences = load_preferences(fixtures=fixtures)
    if len(real_preferences) < 17:
        raise SystemExit("expected current pairwise preference corpus to be present")
    first = fixtures[0]
    first_action = first["actions"][0]
    second_action = first["actions"][1]
    first_team = boss_team_for_fixture(first)
    if not first_team or not all("moves" in member for member in first_team):
        raise SystemExit("expected source-backed boss team rows with move lists")
    if first_team[1]["species"] != "Spearow" or first_team[1]["hp"] != "100%":
        raise SystemExit("expected boss team enrichment to consume bench_state rows")
    first_team_source = boss_team_source_for_fixture(first)
    if not first_team_source["exact"] or not first_team_source["hash"]:
        raise SystemExit("expected source-derived boss team rows to have an exact hash anchor")
    enriched_first = attach_boss_teams([first])[0]
    if "boss_team" not in enriched_first or "boss_team_source" not in enriched_first:
        raise SystemExit("expected fixture API enrichment to attach boss_team")
    slowking = next(
        fixture for fixture in fixtures if fixture["id"] == "pryce_slowking_vs_ampharos_ground_pivot"
    )
    if "move_psychic" not in demonstration_action_ids_for_fixture(slowking):
        raise SystemExit("expected missing-plan builder actions to include Slowking source Psychic")

    feature_report = build_feature_report(fixtures)
    if feature_report["action_count"] != sum(len(fixture["actions"]) for fixture in fixtures):
        raise SystemExit("expected feature report to cover every fixture action")
    if "kind_switch" not in feature_report["feature_support"]:
        raise SystemExit("expected feature report to include switch action features")

    benchmarks = load_benchmarks()
    benchmark_oracles = load_benchmark_oracles()
    if {row["id"] for row in benchmarks} != {row["id"] for row in benchmark_oracles}:
        raise SystemExit("expected public benchmark cards and hidden oracles to match by id")
    benchmark_policy = build_benchmark_policy_answers(benchmarks)
    benchmark_answers = {
        row["benchmark_id"]: row["chosen_move_id"]
        for row in benchmark_policy["answers"]
    }
    benchmark_report = build_benchmark_report(
        benchmarks,
        oracles=benchmark_oracles,
        answers=benchmark_answers,
    )
    if not benchmark_report["benchmark_contract_ready"]:
        raise SystemExit("expected state-transition benchmark contract to be ready")
    if not benchmark_report["policy_passes"]:
        raise SystemExit("expected state-transition baseline policy to pass benchmarks")
    mutation_report = build_benchmark_mutation_report(benchmarks)
    if mutation_report["mutation_count"] < 7:
        raise SystemExit("expected answer-flip benchmark mutation coverage")
    if not mutation_report["all_mutations_pass"]:
        raise SystemExit("expected state-transition mutations to pass")
    if not mutation_report["all_mutations_flip"]:
        raise SystemExit("expected every benchmark mutation to flip the baseline answer")
    type_evidence_report = build_type_evidence_report(
        benchmarks,
        benchmark_oracles,
        benchmark_policy["answers"],
    )
    if type_evidence_report["chart_tweak_count"] != 15:
        raise SystemExit("expected all 15 romhack type-chart tweaks in type evidence")
    if not type_evidence_report["all_pass"]:
        raise SystemExit("expected benchmark type-effectiveness evidence to pass")
    long_battle_report = build_long_battle_review_report()
    if not long_battle_report["reviews_valid"]:
        raise SystemExit("expected structured long-battle review to validate")
    if long_battle_report["turn_count"] < 30:
        raise SystemExit("expected long-battle review to cover at least 30 turns")
    if long_battle_report["benchmark_extraction_count"] < 3:
        raise SystemExit("expected long-battle review to extract benchmark candidates")
    harvest_report = build_benchmark_harvest_report(fixtures, real_preferences)
    if harvest_report["complete_candidate_count"] < 3:
        raise SystemExit("expected fixture-derived benchmark harvest candidates")
    label_queue = build_benchmark_label_queue(fixtures, real_preferences, limit=5)
    if label_queue["returned_count"] != 5:
        raise SystemExit("expected benchmark label queue to return requested candidates")
    if label_queue["one_label_completion_count"] == 0:
        raise SystemExit("expected benchmark label queue to find promotable partials")
    if not label_queue["requests"][0]["question"]:
        raise SystemExit("expected benchmark label queue requests to ask concrete questions")

    active_queue = build_active_queue(fixtures, [], real_preferences, trace_dir=Path("missing"), limit=5)
    if active_queue["returned_count"] != 5:
        raise SystemExit("expected active queue smoke report to return requested candidates")
    if not active_queue["candidates"][0]["reasons"]:
        raise SystemExit("expected active queue candidates to explain their priority")

    first_plans = generate_plan_cards(first)
    if len(first_plans) < 2:
        raise SystemExit("expected plan generator to create at least two plan cards")
    if any(not plan.get("stop_conditions") for plan in first_plans):
        raise SystemExit("expected every generated plan card to include stop conditions")
    if any(len(plan.get("projection", [])) != plan.get("horizon") for plan in first_plans):
        raise SystemExit("expected every generated plan card to project its full horizon")
    if not any(row.get("projected") for plan in first_plans for row in plan.get("projection", [])):
        raise SystemExit("expected plan projections to include inferred follow-up turns")
    rollout = project_plan(first, first_plans[0])
    if "player_hidden_moves_not_facts" not in first_plans[0].get("public_info_constraints", []):
        raise SystemExit("expected generated plans to mark hidden player moves as non-facts")
    if set(rollout["player_move_buckets"]) != {"revealed", "plausible", "impossible", "unknown_slots"}:
        raise SystemExit("expected rollout player moves to be bucketed by public-info status")

    plan_queue = build_plan_queue(
        fixtures,
        [],
        real_preferences,
        [],
        [],
        trace_dir=Path("missing"),
        limit=5,
    )
    if plan_queue["returned_count"] != 5:
        raise SystemExit("expected plan queue smoke report to return requested candidates")
    if not plan_queue["candidates"][0]["plans"]:
        raise SystemExit("expected plan queue candidates to include plan cards")

    coach_report = build_coach_report(
        fixtures,
        [],
        real_preferences,
        [],
        [],
        trace_dir=Path("missing"),
        limit=5,
    )
    if coach_report["plan_queue"]["returned_count"] != 5:
        raise SystemExit("expected coach report to include plan queue candidates")

    counterfactual_report = build_counterfactual_report(
        fixtures,
        [],
        real_preferences,
        limit=6,
    )
    if counterfactual_report["generated_count"] != 6:
        raise SystemExit("expected counterfactual smoke report to generate variants")

    lesson_report = build_lesson_report(fixtures, [], real_preferences, [])
    lesson_ids = {lesson["lesson_id"] for lesson in lesson_report["lessons"]}
    if "sleep_pressure_clause_gated" not in lesson_ids:
        raise SystemExit("expected lesson report to derive Sleep Clause lesson")

    reward_report = build_reward_model_report(fixtures, real_preferences, epochs=20)
    if reward_report["strict_example_count"] == 0:
        raise SystemExit("expected reward model to fit strict pairwise examples")

    proposal_report = build_proposal_report(fixtures, [], real_preferences, [])
    if not proposal_report["proposals"]:
        raise SystemExit("expected proposal report to generate review candidates")

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
    if "GoldenrodDeptStore5F.asm" not in direct_sources.get("THUNDERPUNCH", []):
        raise SystemExit("direct TM parser should include Goldenrod mart TM_THUNDERPUNCH")
    if "GoldenrodDeptStore5F.asm" not in direct_sources.get("FIRE_PUNCH", []):
        raise SystemExit("direct TM parser should include Goldenrod mart TM_FIRE_PUNCH")
    if "GoldenrodDeptStore5F.asm" not in direct_sources.get("ICE_PUNCH", []):
        raise SystemExit("direct TM parser should include Goldenrod mart TM_ICE_PUNCH")
    if "CeladonDeptStore3F.asm" not in direct_sources.get("HIDDEN_POWER", []):
        raise SystemExit("direct TM parser should include Celadon mart TM_HIDDEN_POWER")
    whitney_tms = direct_tm_moves_for_checkpoint(checkpoint_for_leader("Whitney"))
    if not {"THUNDERPUNCH", "FIRE_PUNCH", "ICE_PUNCH"} <= whitney_tms:
        raise SystemExit("Whitney checkpoint should include Goldenrod purchasable TM punches")
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
        trajectories_path = Path(tmp) / "trajectories.jsonl"
        demonstrations_path = Path(tmp) / "demonstrations.jsonl"
        append_label(
            fixture_id=first["id"],
            action_id=first_action["id"],
            label="best",
            rank=1,
            confidence="medium",
            public_info_scope="public_only",
            lesson_type="weight_hint",
            condition_tags=["survives_one_hit", "target_can_punish"],
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
            confidence="high",
            public_info_scope="public_only",
            lesson_type="sequence_policy",
            condition_tags=["if_user_faster", "survives_one_hit"],
            counterfactual_group="audit_boundary_group",
            holdout=False,
            source_team_hash="audit-team-hash",
            note="audit swapped-order replacement preference",
            preferences_path=preferences_path,
        )
        try:
            save_preference(
                fixture_id=first["id"],
                action_a_id=first_action["id"],
                action_b_id=second_action["id"],
                choice="both_good",
                confidence="certain",
                preferences_path=Path(tmp) / "invalid_preferences.jsonl",
            )
        except PreferenceDataError:
            pass
        else:
            raise SystemExit("expected invalid V2 confidence to fail validation")
        labels = load_labels(labels_path, fixtures=fixtures)
        preferences = load_preferences(preferences_path, fixtures=fixtures)
        report = build_report(fixtures, labels, preferences)
        markdown = render_markdown_report(report)
        if len(labels) != 2:
            raise SystemExit("expected audit smoke labels to round-trip")
        if labels[0]["condition_tags"] != ["survives_one_hit", "target_can_punish"]:
            raise SystemExit("expected V2 label condition tags to round-trip")
        if len(preferences) != 1:
            raise SystemExit("expected audit smoke preference to round-trip")
        if preferences[0]["choice"] != "a_better":
            raise SystemExit("expected repeated pairwise preference save to replace old row")
        if preferences[0]["action_tags"][second_action["id"]] != ["reduces_risk"]:
            raise SystemExit("expected audit replacement action tags to round-trip")
        if preferences[0]["lesson_type"] != "sequence_policy":
            raise SystemExit("expected V2 preference lesson type to round-trip")
        if preferences[0]["condition_tags"] != ["if_user_faster", "survives_one_hit"]:
            raise SystemExit("expected V2 preference condition tags to round-trip")
        if preferences[0]["source_team_hash"] != "audit-team-hash":
            raise SystemExit("expected V2 source team hash to round-trip")
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

        temp_plan_ids = generated_plan_ids_by_fixture([first])
        temp_plans = generate_plan_cards(first)
        save_trajectory_preference(
            fixture_id=first["id"],
            trajectory_a_id=temp_plans[0]["id"],
            trajectory_b_id=temp_plans[1]["id"],
            choice="a_better",
            horizon=3,
            confidence="medium",
            public_info_scope="public_only",
            lesson_type="sequence_policy",
            condition_tags=["survives_one_hit"],
            branch_tags=["if_player_switches_rescore"],
            comparison_scope="selected_plan_over_all_shown",
            compared_plan_ids=[plan["id"] for plan in temp_plans[:2]],
            note="audit trajectory smoke preference",
            trajectories_path=trajectories_path,
            known_plan_ids_by_fixture=temp_plan_ids,
        )
        save_plan_demonstration(
            fixture_id=first["id"],
            demonstration_id="audit_demo_plan",
            horizon=3,
            steps=[
                {"turn": 1, "action_id": first_action["id"]},
                {"turn": 2, "action_id": second_action["id"]},
            ],
            condition_tags=["do_once_only"],
            human_summary="audit missing-plan smoke demo",
            demonstrations_path=demonstrations_path,
        )
        try:
            save_trajectory_preference(
                fixture_id=first["id"],
                trajectory_a_id=temp_plans[0]["id"],
                trajectory_b_id=temp_plans[1]["id"],
                choice="a_better",
                horizon=6,
                trajectories_path=Path(tmp) / "invalid_trajectories.jsonl",
                known_plan_ids_by_fixture=temp_plan_ids,
            )
        except PreferenceDataError:
            pass
        else:
            raise SystemExit("expected invalid trajectory horizon to fail validation")
        trajectories = load_trajectory_preferences(
            trajectories_path,
            fixtures=fixtures,
            known_plan_ids_by_fixture=temp_plan_ids,
        )
        demonstrations = load_plan_demonstrations(demonstrations_path, fixtures=fixtures)
        trajectory_report = build_trajectory_report(fixtures, trajectories, demonstrations)
        if len(trajectories) != 1:
            raise SystemExit("expected trajectory preference to round-trip")
        if trajectories[0]["branch_tags"] != ["if_player_switches_rescore"]:
            raise SystemExit("expected trajectory branch tags to round-trip")
        if trajectories[0]["comparison_scope"] != "selected_plan_over_all_shown":
            raise SystemExit("expected trajectory comparison scope to round-trip")
        if not trajectories[0].get("source_team_hash") or not trajectories[0].get("fixture_state_hash"):
            raise SystemExit("expected trajectory rows to store source freshness hashes")
        if len(demonstrations) != 1:
            raise SystemExit("expected plan demonstration to round-trip")
        if not demonstrations[0].get("source_team_hash") or not demonstrations[0].get("fixture_state_hash"):
            raise SystemExit("expected demonstrations to store source freshness hashes")
        if trajectory_report["trajectory_count"] != 1 or trajectory_report["demonstration_count"] != 1:
            raise SystemExit("expected trajectory report to count saved rows")
        final_report = build_final_report(
            fixtures,
            labels,
            preferences,
            [],
            trajectories,
            demonstrations,
        )
        if "top_plan_pairs_are_fully_labeled" not in final_report["gates"]:
            raise SystemExit("expected final readiness report to include plan-pair gate")
        missing_exact_ids = {
            row["fixture_id"]
            for row in final_report["party_anchor_report"]["missing_exact"]
        }
        if missing_exact_ids:
            raise SystemExit(
                "expected all fixtures, including fixture-state drills, to have exact "
                f"trainer-party anchors: {sorted(missing_exact_ids)}"
            )

    print(
        "Boss AI preference audit passed: "
        f"{len(fixtures)} fixtures, label persistence/report smoke ok."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
