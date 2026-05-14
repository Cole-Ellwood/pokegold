# Boss AI Offline Preference Model Report

Generated: 2026-05-13T11:25:49+00:00

## Summary

- Strict pairwise examples: 43
- Train examples: 37
- Holdout examples: 6
- Train accuracy: 91.9%
- Holdout accuracy: 83.3%

## Top Positive Features

- `text_tempo_or_punish`: 1.027187 (support 21)
- `move_class_status`: 0.914792 (support 12)
- `move_class_sleep`: 0.893403 (support 6)
- `sleep_enables_setup_line`: 0.750871 (support 5)
- `spikes_third_layer_available`: 0.508711 (support 3)
- `spikes_player_layers_2`: 0.508711 (support 3)
- `text_information_probe`: 0.45252 (support 4)
- `ko_possible`: 0.432967 (support 3)
- `damage_bucket_ko`: 0.432967 (support 3)
- `kind_switch`: 0.418646 (support 11)
- `move_class_setup`: 0.416882 (support 7)
- `setup_into_sleep_window`: 0.390354 (support 1)
- `damage_high_percent`: 0.303645 (support 25)
- `damage_average_percent`: 0.282101 (support 25)
- `damage_low_percent`: 0.260557 (support 25)

## Top Negative Features

- `damage_bucket_chip`: -0.824169 (support 6)
- `move_class_recovery`: -0.764527 (support 4)
- `text_preserve_value`: -0.507279 (support 8)
- `text_visible_risk`: -0.421593 (support 13)
- `kind_move`: -0.418646 (support 11)
- `spikes_already_maxed`: -0.41318 (support 2)
- `spikes_player_layers_3`: -0.41318 (support 2)
- `rest_at_full_hp`: -0.378016 (support 2)
- `public_type_immunity_risk`: -0.346845 (support 3)
- `move_class_speed_control`: -0.280022 (support 1)
- `two_hko_or_better`: -0.23852 (support 9)
- `sleep_talk_while_awake`: -0.207768 (support 1)
- `damage_bucket_meaningful`: -0.189818 (support 11)
- `damage_bucket_near_ko`: -0.189491 (support 6)
- `move_class_lock`: -0.12805 (support 1)

## Model Helps Where Current Scorer Misses

- `koga_crobat_vs_alakazam_toxic_or_attack:move_toxic:move_wing_attack`: model b_better, scorer a_better, expected b_better

## Current Scorer Helps Where Model Misses

- `bugsy_scyther_vs_quilava_fire_pressure:move_swords_dance:move_wing_attack`: model tie, scorer a_better, expected a_better
- `external_gsc_rhydon_vs_sleeping_snorlax_curse_window:move_curse:move_earthquake`: model tie, scorer a_better, expected a_better
- `external_gsc_rhydon_vs_sleeping_snorlax_curse_window:move_curse:switch_zapdos`: model tie, scorer a_better, expected a_better
- `red_snorlax_vs_alakazam_curse_or_body_slam:move_body_slam:move_curse`: model b_better, scorer a_better, expected a_better

## Unstable Low-Support Weights

- `move_class_speed_control`: -0.280022 (support 1)
- `sleep_talk_while_awake`: -0.207768 (support 1)
- `move_class_lock`: -0.12805 (support 1)
- `text_personality_style`: 0.142531 (support 1)
- `setup_into_sleep_window`: 0.390354 (support 1)

## Trajectory Preference Model

- Strict trajectory examples: 43
- Train examples: 42
- Holdout examples: 1
- Train accuracy: 85.7%
- Holdout accuracy: 100.0%
- Skipped strict examples: 0

### Top Plan Features

- `plan_attack_now_under_public_lethal_threat`: 0.88149 (support 13)
- `plan_attack_now_under_public_major_or_lethal_threat`: 0.606707 (support 16)
- `plan_setup_under_public_major_threat`: 0.545035 (support 4)
- `plan_action_text_information_probe`: 0.50735 (support 5)
- `stop_boss_hp_below_35`: 0.421431 (support 19)
- `plan_action_move_class_sleep`: 0.400539 (support 9)
- `plan_switch_preserve_under_public_lethal_threat`: 0.349953 (support 14)
- `plan_stays_in_under_public_major_threat`: 0.332681 (support 3)
- `plan_setup_under_public_lethal_threat`: -0.530305 (support 8)
- `plan_action_text_visible_risk`: -0.509091 (support 9)
- `plan_action_text_setup_or_greedy`: -0.488221 (support 12)
- `plan_stays_in_under_public_lethal_threat`: -0.465694 (support 16)
- `plan_action_move_class_sacrifice`: -0.411902 (support 1)
- `plan_switch_preserve_under_public_major_threat`: -0.332681 (support 3)
- `plan_attack_now_under_public_major_threat`: -0.274783 (support 3)
- `plan_stays_in_under_fast_public_lethal_threat`: -0.253421 (support 2)
