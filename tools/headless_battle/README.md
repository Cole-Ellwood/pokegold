# Headless Battle Simulator

`tools.headless_battle` is the first text/JSON no-GUI battle-state path. It is intentionally narrow: selected move-vs-move turns, explicit stats or species shorthand, fixed deterministic RNG with no consumed RNG bytes, pre-variation HP damage through the existing damage oracle, and post-score Boss AI selector replay.

Run:

```powershell
python -m tools.headless_battle --template
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json --json
python tools\audit\check_headless_battle_simulator.py
```

Proof boundary:

- `damage_core_pre_variation` is byte-proven through the existing `tools.damage_debugger.oracle.predict_damage` and `tools.damage_debugger.clobber_smoke` gate.
- `selected_turn_order_priority_speed` is source-mirrored for priority and unequal raw speed only.
- `boss_ai_selector_from_post_score_bytes` reuses `select_from_score_bytes` for already-known final score bytes.

Out of scope until separate implementation and proof: sample/exhaustive RNG, consumed fixed RNG bytes, speed ties, Quick Claw/Choice Scarf turn-order effects, damage variation, critical hits, accuracy, status, switch flow, forced-switch prompts, after-hit/between-turn effects, live Boss AI scoring, Boss AI switch candidate/confidence generation, scripts, text, animations, EXP, and party writes.
