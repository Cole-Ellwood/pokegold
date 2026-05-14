# Boss AI Preference Final Readiness Report

Generated: 2026-05-13T11:25:57+00:00

## Summary

- Fixtures: 57
- Pairwise preferences: 52
- Trajectory preferences: 69
- Plan demonstrations: 3
- Ready for ROM scoring review: `False`

## Readiness Gates

- `no_trajectory_conflicts`: True
- `no_stale_trajectory_rows`: True
- `has_holdout_pairwise_examples`: True
- `has_holdout_trajectory_examples`: True
- `all_fixtures_have_exact_party_anchor`: True
- `top_plan_pairs_are_fully_labeled`: False
- `proposals_are_not_conflict_blocked`: True

## Coverage

- Fixture phases: `{'early': 20, 'late': 6, 'mid': 31}`
- Trajectory phases: `{'early': 5, 'late': 2, 'mid': 12}`
- Exact party anchors: 57 / 57
- Incomplete top plan-card questions: 42
- Complete benchmark candidates: 4
- Partial benchmark candidates: 23
- One-label benchmark completions: 11 / 23
- Trajectory conflicts: 0
- Stale trajectory rows: 0
- Pairwise holdout accuracy: 83.3%
- Trajectory holdout accuracy: 100.0%

## Leader Trajectory Coverage

- `Brock`: 6
- `Bugsy`: 5
- `Champion Lance`: 11
- `Chuck`: 5
- `Clair`: 3
- `Erika`: 9
- `External GSC`: 2
- `Falkner`: 3
- `Jasmine`: 1
- `Koga`: 2
- `Morty`: 6
- `Pryce`: 6
- `Whitney`: 9
- `Will`: 1

## Incomplete Plan Questions

- `clair_dragonair_vs_suicune_hidden_ice_beam`: 2 / 3 shown plan pairs covered
- `karen_crobat_vs_dragonite_toxic_or_attack`: 0 / 3 shown plan pairs covered
- `external_gsc_rhydon_vs_sleeping_snorlax_curse_window`: 2 / 3 shown plan pairs covered
- `morty_misdreavus_vs_typhlosion_perish_song`: 0 / 3 shown plan pairs covered
- `pryce_cloyster_vs_quilava_explosion_line`: 0 / 3 shown plan pairs covered
- `whitney_clefairy_vs_bayleef_encore_window`: 0 / 3 shown plan pairs covered
- `jasmine_skarmory_vs_machoke_whirlwind`: 0 / 3 shown plan pairs covered
- `bugsy_ariados_vs_pidgey_toxic_or_attack`: 0 / 3 shown plan pairs covered
- `bugsy_scyther_vs_geodude_safe_swords_dance`: 2 / 3 shown plan pairs covered
- `chuck_poliwrath_vs_alakazam_hypnosis_or_ice_punch`: 2 / 3 shown plan pairs covered
- `clair_kingdra_vs_dragonair_dragon_dance_mirror`: 0 / 3 shown plan pairs covered
- `koga_ariados_vs_typhlosion_spikes_or_toxic`: 2 / 3 shown plan pairs covered
- `lance_ampharos_vs_porygon2_thunder_or_dragon_dance`: 0 / 6 shown plan pairs covered
- `lance_kingdra_vs_starmie_dragon_dance_or_attack`: 0 / 3 shown plan pairs covered
- `morty_haunter_vs_noctowl_sleep_line`: 3 / 6 shown plan pairs covered
- `bruno_onix_vs_typhlosion_sandstorm_or_explosion`: 0 / 3 shown plan pairs covered
- `karen_gengar_vs_snorlax_destiny_bond_or_thunderbolt`: 0 / 3 shown plan pairs covered
- `koga_crobat_vs_alakazam_toxic_or_attack`: 0 / 3 shown plan pairs covered
- `jasmine_magneton_vs_quilava_thunder_wave_or_bolt`: 0 / 3 shown plan pairs covered
- `koga_ariados_vs_quilava_spider_web_or_attack`: 0 / 3 shown plan pairs covered

## Proposal Types

- `hard_rule`: 2
- `needs_more_labels`: 15
- `schema_only`: 1
- `scoring_weight`: 1
- `scout_policy`: 2
- `sequence_policy`: 30
- `switch_policy`: 29
