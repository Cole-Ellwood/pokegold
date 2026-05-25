# Headless Battle Simulator

`tools.headless_battle` is the first text/JSON no-GUI battle-state path. It is intentionally narrow: selected move-vs-move turns, explicit stats or species shorthand, basic critical-hit checks, basic move accuracy hit/miss checks, damage variation with fixed/sample/exhaustive RNG, selected-action `turns[]` progression with HP/RNG carryover, pre-variation HP damage through the existing damage oracle, and post-score Boss AI selector replay.

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
- `selected_turn_order_priority_speed` is source-mirrored for priority and unequal raw speed only.
- `multi_turn_selected_action_progression` carries active HP/RNG state across a caller-supplied `turns[]` list and stops early on KO.
- `boss_ai_selector_from_post_score_bytes` reuses `select_from_score_bytes` for already-known final score bytes.

Out of scope until separate implementation and proof: automatic action choice, replacement flow after a KO, RNG-consuming mechanics outside critical hits/accuracy/damage variation, accuracy/evasion stat modifiers, BrightPowder, Protect, Fly/Dig, Lock-On, X Accuracy, speed ties, Quick Claw/Choice Scarf turn-order effects, critical-hit messaging, status, switch flow, forced-switch prompts, after-hit/between-turn effects, live Boss AI scoring, Boss AI switch candidate/confidence generation, scripts, text, animations, EXP, and party writes.
