# Boss AI Preference Final Readiness Report

Generated: 2026-05-12T10:57:14+00:00

## Summary

- Fixtures: 53
- Pairwise preferences: 20
- Trajectory preferences: 34
- Plan demonstrations: 3
- Ready for ROM scoring review: `False`

## Readiness Gates

- `no_trajectory_conflicts`: True
- `no_stale_trajectory_rows`: True
- `has_holdout_pairwise_examples`: True
- `has_holdout_trajectory_examples`: False
- `all_fixtures_have_exact_party_anchor`: True
- `top_plan_pairs_are_fully_labeled`: False
- `proposals_are_not_conflict_blocked`: True

## Coverage

- Fixture phases: `{'early': 20, 'late': 2, 'mid': 31}`
- Trajectory phases: `{'early': 1, 'late': 1, 'mid': 10}`
- Exact party anchors: 53 / 53
- Incomplete top plan-card questions: 47
- Trajectory conflicts: 0
- Stale trajectory rows: 0
- Pairwise holdout accuracy: 50.0%
- Trajectory holdout accuracy: n/a

## Leader Trajectory Coverage

- `Brock`: 3
- `Bugsy`: 2
- `Champion Lance`: 5
- `Chuck`: 2
- `Clair`: 3
- `Erika`: 6
- `Falkner`: 2
- `Morty`: 2
- `Pryce`: 3
- `Whitney`: 6

## Incomplete Plan Questions

- `lance_dragonite_vs_suicune_champion_ace`: 2 / 3 shown plan pairs covered
- `bugsy_scyther_vs_quilava_fire_pressure`: 2 / 3 shown plan pairs covered
- `pryce_slowking_vs_ampharos_ground_pivot`: 3 / 6 shown plan pairs covered
- `clair_dragonair_vs_suicune_hidden_ice_beam`: 2 / 3 shown plan pairs covered
- `falkner_pidgeotto_vs_geodude_rock_risk`: 2 / 3 shown plan pairs covered
- `chuck_poliwrath_vs_pidgeotto_ice_punch`: 2 / 3 shown plan pairs covered
- `bugsy_ariados_vs_pidgey_toxic_or_attack`: 0 / 3 shown plan pairs covered
- `morty_gengar_vs_kadabra_destiny_bond`: 2 / 3 shown plan pairs covered
- `bugsy_scyther_vs_geodude_safe_swords_dance`: 0 / 3 shown plan pairs covered
- `karen_crobat_vs_dragonite_toxic_or_attack`: 0 / 3 shown plan pairs covered
- `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch`: 0 / 3 shown plan pairs covered
- `koga_ariados_vs_typhlosion_spikes_or_toxic`: 0 / 3 shown plan pairs covered
- `morty_haunter_vs_noctowl_sleep_line`: 0 / 6 shown plan pairs covered
- `will_slowbro_vs_houndoom_amnesia_or_surf`: 0 / 1 shown plan pairs covered
- `brock_golem_vs_vaporeon_explosion_question`: 3 / 6 shown plan pairs covered
- `morty_misdreavus_vs_typhlosion_perish_song`: 0 / 3 shown plan pairs covered
- `pryce_cloyster_vs_quilava_explosion_line`: 0 / 3 shown plan pairs covered
- `red_snorlax_vs_alakazam_curse_or_body_slam`: 0 / 3 shown plan pairs covered
- `whitney_clefairy_vs_bayleef_encore_window`: 0 / 3 shown plan pairs covered
- `jasmine_skarmory_vs_machoke_whirlwind`: 0 / 3 shown plan pairs covered

## Proposal Types

- `hard_rule`: 2
- `needs_more_labels`: 21
- `schema_only`: 1
- `scoring_weight`: 1
- `scout_policy`: 2
- `sequence_policy`: 1
- `switch_policy`: 17
