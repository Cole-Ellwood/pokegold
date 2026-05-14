# Long Battle Review Report

Generated: 2026-05-13T11:25:48+00:00

## Summary

- Reviews valid: `True`
- Turns reviewed: 32
- Critical turns: 4
- Benchmark extractions: 3
- Earliest meaningful error: turn 9 (OVERFITTED_SCRIPT_ERROR)

## Critical Turns

### Turn 9 - `earliest_irreversible_error`

- Mistake: Swords Dance after Sleep Powder miss without re-scoring
- Expected: retry sleep only if the miss branch is survivable, otherwise preserve Victreebel or pivot to Skarmory

### Turn 17 - `good_route_trade`

- Mistake: none
- Expected: Explosion is justified because Machamp blocks Snorlax endgame and Cloyster already set the only vanilla Spikes layer

### Turn 21 - `rest_tempo_error`

- Mistake: Rest at 72% gave Tyranitar sleep turns without preserving a required role
- Expected: attack or pivot until Rest is forced by range

### Turn 29 - `damage_range_gap`

- Mistake: Gengar spinblock line needs exact Psychic survival evidence before staying in
- Expected: classify as needs_context unless profile-specific damage range is known; a romhack threshold card now covers the verified local damage case

## Benchmark Extractions

- `sleep_disruption_after_miss_long_game_001` from turn 9: best `['move_sleep_powder', 'switch_skarmory']`, catastrophic `['move_swords_dance']`, flip field `sleep_move_result: hit -> miss`
- `rest_tempo_unforced_long_game_001` from turn 21: best `['move_body_slam']`, catastrophic `['move_rest']`, flip field `snorlax_hp: forced_rest_range -> 72%`
- `spinblock_damage_context_long_game_001` from turn 29: best `['needs_context']`, catastrophic `['move_thunderbolt_without_survival_range']`, flip field `starmie_psychic_vs_gengar_damage_range`

## Heuristics Learned

- A sleep miss in a long game invalidates setup scripts more severely when the sleeper is also an irreplaceable route piece.
- Explosion is a good route trade only when the lost role is already discharged or replaceable.
- Rest timing is a route-preservation claim; high-HP Rest without a forced range can donate conversion turns.
- Spinblock decisions in endgames require profile-specific damage evidence; the romhack Starmie/Gengar threshold is not vanilla GSC proof.

## Damage Context Evidence

- `romhack_spinblock_damage_context_001` (romhack_gym_leader_lab): Starmie Psychic deals 53-63 HP to trainer Gengar.; Gengar Thunderbolt deals 85-101 HP to player Starmie.
  - Threshold: Gengar at 67 HP survives Psychic and removes 83 HP Starmie; Gengar at 52 HP is KOed before moving.
  - Transfer warning: This evidence uses romhack source stats and typing, including Ghost/Psychic Gengar, so it must not be used as vanilla GSC truth.

## Unverified

- Exact vanilla GSC Starmie Psychic versus Gengar damage for the constructed review.
- Exact original turn-29 Gengar HP/level if this constructed scenario is replaced with a real battle log.
- Exact remaining PP for Snorlax Body Slam, Rest, and opposing Raikou Roar in the final four turns.
- Whether an expert reviewer would prefer preserving Victreebel or retrying Sleep Powder on turn 9.