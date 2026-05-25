# Headless Battle Simulator

`tools.headless_battle` is the first text/JSON no-GUI battle-state path. It is intentionally narrow: selected move-vs-move turns, explicit stats or species shorthand, damage variation with fixed/sample/exhaustive RNG, selected-action `turns[]` progression with HP/RNG carryover, pre-variation HP damage through the existing damage oracle, and post-score Boss AI selector replay.

Run:

```powershell
python -m tools.headless_battle --template
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json --json
python tools\audit\check_headless_battle_simulator.py
```

Proof boundary:

- `damage_core_pre_variation` is byte-proven through the existing `tools.damage_debugger.oracle.predict_damage` and `tools.damage_debugger.clobber_smoke` gate.
- `damage_variation_rng_branching` mirrors `BattleCommand_DamageVariation`: 0/1 damage skips variation; otherwise accepted multipliers are 217..255 after the ROM's rotate-right rejection loop.
- `selected_turn_order_priority_speed` is source-mirrored for priority and unequal raw speed only.
- `multi_turn_selected_action_progression` carries active HP/RNG state across a caller-supplied `turns[]` list and stops early on KO.
- `boss_ai_selector_from_post_score_bytes` reuses `select_from_score_bytes` for already-known final score bytes.

Out of scope until separate implementation and proof: automatic action choice, replacement flow after a KO, RNG-consuming mechanics outside damage variation, speed ties, Quick Claw/Choice Scarf turn-order effects, critical hits, accuracy, status, switch flow, forced-switch prompts, after-hit/between-turn effects, live Boss AI scoring, Boss AI switch candidate/confidence generation, scripts, text, animations, EXP, and party writes.
