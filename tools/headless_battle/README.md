# Headless Battle Simulator

`tools.headless_battle` is the first text/JSON no-GUI battle-state path. It is intentionally narrow: selected move-vs-move turns, selected switch actions, caller-supplied replacement after KO, explicit stats or species shorthand, equal-speed tie RNG, basic critical-hit checks, basic move accuracy hit/miss checks, damage variation with fixed/sample/exhaustive RNG, initial poison/burn/toxic residual damage after selected moves, selected-action `turns[]` progression with HP/RNG carryover, pre-variation HP damage through the existing damage oracle, post-score Boss AI selector replay, and executable post-score Boss AI selector turns when the scenario supplies final score bytes.

Run:

```powershell
python -m tools.headless_battle --template
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json --json
python tools\audit\check_headless_battle_simulator.py
```

Proof boundary:

- `damage_core_pre_variation` is byte-proven through the existing `tools.damage_debugger.oracle.predict_damage` and `tools.damage_debugger.clobber_smoke` gate.
- `basic_critical_hit_rng` mirrors `BattleCommand_Critical` for the NormalHit command order: critical check first, damage variation second, accuracy third.
- `damage_variation_rng_branching` mirrors `BattleCommand_DamageVariation`: 0/1 damage skips variation; otherwise accepted multipliers are 217..255 after the ROM's rotate-right rejection loop.
- `basic_move_accuracy_rng` mirrors the basic `BattleCommand_CheckHit` raw-byte threshold for move accuracy, always-hit moves, and Thunder in rain.
- `basic_status_residual` mirrors `ResidualDamage` for initial poison, burn, and toxic residual after a selected move when both active Pokemon remain alive.
- `selected_turn_order_priority_speed` is source-mirrored for priority, unequal raw speed, and non-link equal-speed ties.
- `multi_turn_selected_action_progression` carries active HP/RNG state across a caller-supplied `turns[]` list and stops early on KO.
- `selected_switch_and_replacement` supports caller-selected `switch` actions from `bench[]` and caller-supplied `replace` actions after a KO.
- `boss_ai_selector_from_post_score_bytes` reuses `select_from_score_bytes` for already-known final score bytes.
- `boss_ai_selector_move_execution` branches fixed/sample/exhaustive selector RNG over already-known final score bytes, records the chosen slot, validates the selected move id when available, and then executes the selected move through the same turn-order and damage path.

Out of scope until separate implementation and proof: automatic action choice without caller-supplied final Boss AI score bytes, automatic replacement selection, forced switch prompts, Pursuit-on-switch, Spikes/switch-in effects, RNG-consuming mechanics outside speed ties/Boss AI selector choice/critical hits/accuracy/damage variation, accuracy/evasion stat modifiers, BrightPowder, Protect, Fly/Dig, Lock-On, X Accuracy, link-battle turn-order inversion, Quick Claw/Choice Scarf turn-order effects, status application, sleep, freeze, paralysis, volatile effects, weather, item recovery/cures, after-hit effects, live Boss AI scoring, Boss AI switch candidate/confidence generation, scripts, text, animations, EXP, and party writes.
