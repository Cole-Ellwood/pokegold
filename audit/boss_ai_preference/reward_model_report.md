# Boss AI Offline Preference Model Report

Generated: 2026-05-12T10:57:09+00:00

## Summary

- Strict pairwise examples: 13
- Train examples: 11
- Holdout examples: 2
- Train accuracy: 100.0%
- Holdout accuracy: 50.0%

## Top Positive Features

- `move_class_setup`: 1.216965 (support 2)
- `move_class_sleep`: 1.157686 (support 4)
- `text_tempo_or_punish`: 0.846987 (support 3)
- `move_class_status`: 0.760778 (support 5)
- `ko_possible`: 0.599215 (support 3)
- `damage_bucket_ko`: 0.599215 (support 3)
- `damage_high_percent`: 0.353528 (support 9)
- `text_personality_style`: 0.351005 (support 1)
- `damage_average_percent`: 0.324135 (support 9)
- `damage_low_percent`: 0.294741 (support 9)
- `damage_bucket_near_ko`: 0.266019 (support 1)
- `kind_move`: 0.251015 (support 1)
- `ko_confirmed`: 0.202307 (support 2)
- `two_hko_or_better`: 0.096851 (support 4)
- `text_visible_risk`: 0.090359 (support 5)

## Top Negative Features

- `damage_bucket_major`: -1.034403 (support 3)
- `damage_bucket_chip`: -0.918991 (support 2)
- `text_setup_or_greedy`: -0.451532 (support 4)
- `move_class_lock`: -0.332972 (support 1)
- `damage_bucket_meaningful`: -0.266029 (support 3)
- `text_information_probe`: -0.266019 (support 1)
- `kind_switch`: -0.251015 (support 1)
- `text_preserve_value`: -0.251015 (support 1)

## Model Helps Where Current Scorer Misses

- `koga_crobat_vs_alakazam_toxic_or_attack:move_toxic:move_wing_attack`: model b_better, scorer a_better, expected b_better
- `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance:move_sleep_powder:move_quiver_dance`: model a_better, scorer b_better, expected a_better

## Current Scorer Helps Where Model Misses

- `misty_starmie_vs_meganium_recover_or_attack:move_recover:move_psychic`: model a_better, scorer b_better, expected b_better

## Unstable Low-Support Weights

- `move_class_lock`: -0.332972 (support 1)
- `text_information_probe`: -0.266019 (support 1)
- `kind_switch`: -0.251015 (support 1)
- `text_preserve_value`: -0.251015 (support 1)
- `kind_move`: 0.251015 (support 1)
- `damage_bucket_near_ko`: 0.266019 (support 1)
- `text_personality_style`: 0.351005 (support 1)

## Trajectory Preference Model

- Strict trajectory examples: 19
- Train examples: 19
- Holdout examples: 0
- Train accuracy: 89.5%
- Holdout accuracy: n/a
- Skipped strict examples: 0

### Top Plan Features

- `plan_action_text_information_probe`: 0.672386 (support 3)
- `plan_action_text_tempo_or_punish`: 0.591009 (support 3)
- `stop_threat_revealed`: 0.333699 (support 2)
- `plan_shape_scout_probe_then_commit`: 0.333699 (support 2)
- `init_hidden_coverage_or_speed_boundary`: 0.333699 (support 2)
- `branch_then_preserve_or_switch`: 0.333699 (support 2)
- `branch_then_commit_to_damage`: 0.333699 (support 2)
- `branch_if_no_punish_revealed`: 0.333699 (support 2)
- `plan_action_text_visible_risk`: -1.363419 (support 2)
- `plan_action_move_class_sacrifice`: -0.807481 (support 1)
- `plan_action_text_setup_or_greedy`: -0.737737 (support 4)
- `branch_if_target_switches`: -0.345437 (support 12)
- `plan_action_damage_bucket_meaningful`: -0.317024 (support 1)
- `plan_action_move_class_lock`: -0.317024 (support 1)
- `plan_shape_commit_lock_only_if_safe`: -0.317024 (support 1)
- `stop_target_can_switch`: -0.317024 (support 1)
