# Benchmark Label Queue

Generated: 2026-05-13T11:25:56+00:00

## Summary

- Fixtures: 57
- Fixtures with feedback: 27
- Complete benchmark candidates: 4
- Partial candidates: 23
- One-label completions available: 11
- Missing label pieces: `{'acceptable': 20, 'best': 3, 'catastrophic': 3, 'single_best': 5}`
- Returned requests: 20 / 23

## Requests

### 1. `bugsy_scyther_vs_quilava_fire_pressure`

- Leader / turn: Bugsy / 2
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Swords Dance (`move_swords_dance`)
- Current acceptable: -
- Current catastrophic: Wing Attack (`move_wing_attack`)
- Question: Can Switch to Ledian (`switch_ledian`) be an acceptable alternative to Swords Dance (`move_swords_dance`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id bugsy_scyther_vs_quilava_fire_pressure --action-a-id move_swords_dance --action-b-id switch_ledian --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 2. `clair_dragonair_vs_suicune_hidden_ice_beam`

- Leader / turn: Clair / 4
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Switch to Kingdra (`switch_kingdra`)
- Current acceptable: -
- Current catastrophic: Thunder (`move_thunder`), Outrage (`move_outrage`)
- Question: Can Switch to Mantine (`switch_mantine`) be an acceptable alternative to Switch to Kingdra (`switch_kingdra`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id clair_dragonair_vs_suicune_hidden_ice_beam --action-a-id switch_kingdra --action-b-id switch_mantine --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 3. `clair_kingdra_vs_lapras_dragon_dance_or_attack`

- Leader / turn: Clair / 6
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Dragon Dance (`move_dragon_dance`)
- Current acceptable: -
- Current catastrophic: Surf (`move_surf`)
- Question: Can Ice Beam (`move_ice_beam`) be an acceptable alternative to Dragon Dance (`move_dragon_dance`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id clair_kingdra_vs_lapras_dragon_dance_or_attack --action-a-id move_dragon_dance --action-b-id move_ice_beam --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 4. `falkner_pidgeotto_vs_geodude_rock_risk`

- Leader / turn: Falkner / 3
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Sand Attack (`move_sand_attack`)
- Current acceptable: -
- Current catastrophic: Gust (`move_gust`)
- Question: Can Switch to Noctowl (`switch_noctowl`) be an acceptable alternative to Sand Attack (`move_sand_attack`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id falkner_pidgeotto_vs_geodude_rock_risk --action-a-id move_sand_attack --action-b-id switch_noctowl --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 5. `jasmine_steelix_vs_quilava_fire_threat`

- Leader / turn: Jasmine / 5
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Rock Slide (`move_rock_slide`)
- Current acceptable: -
- Current catastrophic: Earthquake (`move_earthquake`)
- Question: Can Switch to Skarmory (`switch_skarmory`) be an acceptable alternative to Rock Slide (`move_rock_slide`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id jasmine_steelix_vs_quilava_fire_threat --action-a-id move_rock_slide --action-b-id switch_skarmory --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 6. `koga_crobat_vs_alakazam_toxic_or_attack`

- Leader / turn: Koga / 5
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Wing Attack (`move_wing_attack`)
- Current acceptable: -
- Current catastrophic: Toxic (`move_toxic`)
- Question: Can Switch to Umbreon (`switch_umbreon`) be an acceptable alternative to Wing Attack (`move_wing_attack`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id koga_crobat_vs_alakazam_toxic_or_attack --action-a-id move_wing_attack --action-b-id switch_umbreon --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 7. `misty_starmie_vs_meganium_recover_or_attack`

- Leader / turn: Misty / 8
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Psychic (`move_psychic`)
- Current acceptable: -
- Current catastrophic: Recover (`move_recover`)
- Question: Can Switch to Lapras (`switch_lapras`) be an acceptable alternative to Psychic (`move_psychic`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id misty_starmie_vs_meganium_recover_or_attack --action-a-id move_psychic --action-b-id switch_lapras --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 8. `morty_gengar_vs_kadabra_destiny_bond`

- Leader / turn: Morty / 4
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Shadow Ball (`move_shadow_ball`)
- Current acceptable: -
- Current catastrophic: Destiny Bond (`move_destiny_bond`)
- Question: Can Switch to Misdreavus (`switch_misdreavus`) be an acceptable alternative to Shadow Ball (`move_shadow_ball`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id morty_gengar_vs_kadabra_destiny_bond --action-a-id move_shadow_ball --action-b-id switch_misdreavus --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 9. `morty_haunter_vs_noctowl_sleep_line`

- Leader / turn: Morty / 2
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Hypnosis (`move_hypnosis`)
- Current acceptable: -
- Current catastrophic: Night Shade (`move_night_shade`)
- Question: Can Switch to Gengar (`switch_gengar`) be an acceptable alternative to Hypnosis (`move_hypnosis`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id morty_haunter_vs_noctowl_sleep_line --action-a-id move_hypnosis --action-b-id switch_gengar --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 10. `pryce_cloyster_vs_quilava_explosion_line`

- Leader / turn: Pryce / 3
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Switch to Slowking (`switch_slowking`)
- Current acceptable: -
- Current catastrophic: Surf (`move_surf`), Explosion (`move_explosion`)
- Question: Can Protect (`move_protect`) be an acceptable alternative to Switch to Slowking (`switch_slowking`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id pryce_cloyster_vs_quilava_explosion_line --action-a-id switch_slowking --action-b-id move_protect --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 11. `whitney_miltank_vs_geodude_rollout_temptation`

- Leader / turn: Whitney / 5
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: one acceptable label would complete this candidate
- Current best: Body Slam (`move_body_slam`)
- Current acceptable: -
- Current catastrophic: Rollout (`move_rollout`)
- Question: Can Switch to Girafarig (`switch_girafarig`) be an acceptable alternative to Body Slam (`move_body_slam`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id whitney_miltank_vs_geodude_rollout_temptation --action-a-id move_body_slam --action-b-id switch_girafarig --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 12. `bugsy_ariados_vs_pidgey_toxic_or_attack`

- Leader / turn: Bugsy / 1
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Toxic (`move_toxic`)
- Current acceptable: -
- Current catastrophic: Poison Sting (`move_poison_sting`), Giga Drain (`move_giga_drain`), Leech Life (`move_leech_life`), Switch to Scyther (`switch_scyther`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id bugsy_ariados_vs_pidgey_toxic_or_attack --action-a-id move_toxic --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 13. `pryce_slowking_vs_ampharos_ground_pivot`

- Leader / turn: Pryce / 8
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Switch to Piloswine (`switch_piloswine`)
- Current acceptable: -
- Current catastrophic: Surf (`move_surf`), Thunder Wave (`move_thunder_wave`), Rest (`move_rest`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id pryce_slowking_vs_ampharos_ground_pivot --action-a-id switch_piloswine --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 14. `erika_victreebel_vs_snorlax_sleep_or_boost`

- Leader / turn: Erika / 5
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Sleep Powder (`move_sleep_powder`)
- Current acceptable: -
- Current catastrophic: Swords Dance (`move_swords_dance`), Sludge Bomb (`move_sludge_bomb`), Switch to Exeggutor (`switch_exeggutor`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id erika_victreebel_vs_snorlax_sleep_or_boost --action-a-id move_sleep_powder --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 15. `external_gsc_rhydon_vs_sleeping_snorlax_curse_window`

- Leader / turn: External GSC / 49
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Curse (`move_curse`)
- Current acceptable: -
- Current catastrophic: Earthquake (`move_earthquake`), Rock Slide (`move_rock_slide`), Switch to Zapdos (`switch_zapdos`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id external_gsc_rhydon_vs_sleeping_snorlax_curse_window --action-a-id move_curse --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 16. `lance_yanma_vs_lapras_sleep_powder_or_quiver_dance`

- Leader / turn: Champion Lance / 6
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Sleep Powder (`move_sleep_powder`)
- Current acceptable: -
- Current catastrophic: Quiver Dance (`move_quiver_dance`), Giga Drain (`move_giga_drain`), Switch to Kingdra (`switch_kingdra`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id lance_yanma_vs_lapras_sleep_powder_or_quiver_dance --action-a-id move_sleep_powder --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 17. `red_snorlax_vs_alakazam_curse_or_body_slam`

- Leader / turn: Red / 2
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Body Slam (`move_body_slam`)
- Current acceptable: -
- Current catastrophic: Curse (`move_curse`), Rest (`move_rest`), Sleep Talk (`move_sleep_talk`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id red_snorlax_vs_alakazam_curse_or_body_slam --action-a-id move_body_slam --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 18. `will_slowbro_vs_houndoom_amnesia_or_surf`

- Leader / turn: Will / 3
- Missing: `['acceptable']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Switch to Houndoom (`switch_houndoom`)
- Current acceptable: -
- Current catastrophic: Amnesia (`move_amnesia`), Surf (`move_surf`), Psychic (`move_psychic`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id will_slowbro_vs_houndoom_amnesia_or_surf --action-a-id switch_houndoom --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 19. `sabrina_alakazam_choice_lock_vs_houndoom`

- Leader / turn: Sabrina / 6
- Missing: `['acceptable', 'single_best']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: ThunderPunch (`move_thunderpunch`), Ice Punch (`move_ice_punch`), Switch to Hypno (`switch_hypno`)
- Current acceptable: -
- Current catastrophic: Psychic (`move_psychic`)
- Question: No unclassified action remains. Decide whether an existing catastrophic label is overbroad, add a contextual exception, or create a separate benchmark variant with a real acceptable alternative.
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id sabrina_alakazam_choice_lock_vs_houndoom --action-a-id move_thunderpunch --action-b-id <action-b> --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`

### 20. `janine_qwilfish_spikes_already_maxed`

- Leader / turn: Janine / 22
- Missing: `['acceptable', 'single_best']`
- Review type: `acceptable`
- Completion effect: requires a new contextual exception or benchmark variant
- Current best: Sludge Bomb (`move_sludge_bomb`), Surf (`move_surf`)
- Current acceptable: -
- Current catastrophic: Spikes (`move_spikes`)
- Question: Can Switch to Tentacruel (`switch_tentacruel`) be an acceptable alternative to Sludge Bomb (`move_sludge_bomb`), or should it stay outside the benchmark's acceptable set?
- Command template: `python -m tools.boss_ai_preference prefer --fixture-id janine_qwilfish_spikes_already_maxed --action-a-id move_sludge_bomb --action-b-id switch_tentacruel --choice <a_better|b_better|both_good|needs_context|other_better> --note "<why this label is right>"`
