# Headless Battle Simulator

`tools.headless_battle` is the first no-GUI, text/JSON battle simulator path for
the debugger. It is not a full Python rewrite of the ROM yet. It is a scoped
turn-state engine with explicit proof labels.

Run a template:

```powershell
python -m tools.headless_battle --template
```

Run a scenario:

```powershell
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json
python -m tools.headless_battle --scenario .local\tmp\headless_turn.json --json
```

Current supported slice:

- selected move actions for player and enemy
- source-table shorthand for Pokemon and moves: `species`, `level`, move names,
  repo base stats/types, move IDs, move rows, and trainer/default stat profiles
  are expanded unless explicit stats, HP, types, move fields, IV, or
  `statexp_term` overrides are present
- optional `stages` input for accuracy/evasion modifiers, using normal battle
  stage numbers from `-6` to `+6`:
  `{"stages": {"accuracy": -1, "evasion": 2}}`
- optional `volatile` input for current hit-check flags:
  `protect`, `x_accuracy`, `lock_on`, `flying`, `underground`, and
  `focus_energy`; `flinched` models the current one-turn flinch substatus
- optional `status` input for current persistent status:
  `poison`, `burn`, `toxic`, `paralysis`, `sleep`, or `freeze`; toxic also
  accepts `toxic_count` as the current pre-residual counter and sleep accepts
  `sleep_turns` as the current pre-turn counter
- selected switch actions with explicit active-plus-bench state:
  `{"type": "switch", "bench": 0}`
- explicit forced switch phases after a KO:
  `{"player": {"type": "wait"}, "enemy": {"type": "switch", "bench": 0}}`
- post-score Boss AI move selector actions:
  `{"type": "boss_ai_selector", "tier": "late", "move_ids": [33, 52, 0, 0], "scores": [20, 20, 80, 80]}`
- final-confidence Boss AI switch-policy actions:
  `{"type": "boss_ai_switch_policy", "candidate_bench": 0, "confidence": 80, "tier": "late", "fallback_move": 0}`.
  This mirrors the final `BossAI_SwitchOrTryItem` threshold and switch roll
  once a candidate and confidence are already known; it does not generate the
  candidate or confidence from battle state.
- `actions` for one turn or a `turns[]` sequence for multiple selected turns
- move order from priority, raw speed, Quick Claw, Choice Scarf, and ROM-shaped
  speed-tie RNG for the default role; paralysis speed reduction and Electric
  passive speed boosts are applied before Choice Scarf for turn-order checks
- move accuracy for supported normal, always-hit, Thunder, Gust, and Earthquake
  damaging moves, including accuracy/evasion stage modifiers, BrightPowder, X Accuracy,
  Lock-On, semi-invulnerable flying/underground targets, Thunder-in-rain, and
  ROM-shaped miss RNG
- HP mutation for normal, always-hit, Thunder, Gust, and Earthquake damaging
  moves
- post-variation double damage for Gust against flying targets and Earthquake
  against underground targets
- supported damage scripts follow the ROM command order for the implemented
  surfaces: critical-hit chance, damage variation, and supported
  post-variation damage effects run before hit checking, and HP is applied only
  if the hit check passes
- after-hit HP effects for contact Rocky Helmet recoil, Shell Bell healing, and
  Life Orb recoil
- post-action residual HP damage for poison, burn, and toxic, including toxic
  counter advancement and HP clamping to zero
- between-turn Leftovers healing, including minimum heal and max-HP clamping
- paralysis fully-paralyzed move blocking before move execution, including
  Fighting-type passive thresholds, and paralysis speed recalculation including
  Electric/Fighting passive fractions
- sleep counter decrement, fast-asleep blocking, and wake-up status clearing
  before move execution
- frozen-solid move blocking before move execution, plus the CheckTurn bypass
  for Flame Wheel and Sacred Fire
- one-turn flinch move blocking before move execution, including clearing the
  flinch flag
- damage core through `tools.damage_debugger.oracle.predict_damage`
- ROM-shaped damage variation with `fixed`, `sample`, and `exhaustive` RNG modes;
  exhaustive reports distinct outcome classes with `raw_count` weights, not every
  rejected-byte history, plus per-outcome `rng_weight` probabilities for rate
  calculations and aggregate event/selector rates under `summary`
- continuous fixed/sample RNG streams across selected turns
- report labels for byte-proven, source-mirrored, and out-of-scope mechanics
- outcomes that KO an active Pokemon while its bench is still alive set
  `requires_forced_switch=true`; the next turn can be an explicit forced switch
  phase with the forced side switching and the other side waiting
- Boss AI selector actions reuse
  `tools.boss_ai_debugger.rom_scenarios.select_from_score_bytes`, so they start
  from exact final score bytes. They do not calculate those scores from battle
  state.

Current proof boundary:

- `damage_core_pre_variation` is delegated to the existing ROM-vs-oracle damage
  proof surface. `check_headless_battle_simulator.py` runs the simulator
  self-test and `tools.damage_debugger.clobber_smoke`.
- `damage_variation` is ROM-differential: the headless audit injects
  deterministic link-battle RNG bytes into `wLinkBattleRNs`, calls
  `BattleCommand_DamageVariation`, and compares both `wCurDamage` and consumed
  RNG byte count with the Python simulator.
- `critical_hit_chance` is ROM-differential: the headless audit injects
  deterministic link-battle RNG bytes into `wLinkBattleRNs`, calls
  `BattleCommand_Critical`, and compares `wCriticalHit` plus consumed RNG byte
  count with the Python simulator across base odds, high-critical moves, Focus
  Energy, Scope Lens, Lucky Punch, Stick, capped critical level, and zero-power
  no-RNG behavior.
- `turn_order_priority_speed_default_role` is ROM-differential for base selected
  move turns: the audit calls `DetermineMoveOrder` and compares the ROM carry
  flag and consumed speed-tie RNG byte count with the Python simulator for
  non-link priority/speed cases and default-role speed ties.
- `turn_order_quick_claw_choice_scarf_default_role` is ROM-differential for
  Choice Scarf speed, one-sided Quick Claw activation/fallback, and
  both-Quick-Claw default-role roll order.
- `status_speed_recalculation` is ROM-differential: the audit calls
  `ApplyPrzEffectOnSpeed_Far` and compares ROM active speed mutation against
  the Python simulator for normal, Electric passive, baseline paralysis,
  Fighting-passive paralysis, and combined Electric/Fighting cases.
- `turn_order_status_adjusted_speed_inputs` is source-mirrored: the simulator
  feeds the byte-proven status-adjusted speed into the existing selected-turn
  order mirror before Choice Scarf, matching the ROM split where speed is
  recalculated before `DetermineMoveOrder` reads it.
- `supported_damage_move_accuracy_modifiers_overrides_semivulnerable_weather_and_sure_hit` is
  ROM-differential
  for supported normal, always-hit, and Thunder damaging moves: the audit calls
  `BattleCommand_CheckHit` for both actors and compares `wAttackMissed`,
  `wCurDamage`, and consumed RNG byte count with the Python simulator across
  neutral accuracy, accuracy/evasion stage modifiers, cap-to-perfect cases,
  BrightPowder, X Accuracy, Lock-On flag clearing, semi-invulnerable
  flying/underground targets, Thunder-in-rain, source-table sure-hit effects,
  and move-ID exceptions such as Gust hitting flying targets and Earthquake
  hitting underground targets.
- `post_variation_double_flying_underground_damage` is ROM-differential for the
  double-damage commands used by Gust and Earthquake after damage variation,
  including the ROM's `$ffff` cap.
- `after_hit_rocky_shell_life_orb` is ROM-differential for the supported
  after-hit item effects: the audit calls `HandleLateGenAfterHitEffects_Far`
  and compares player/enemy HP after Rocky Helmet, Shell Bell, and Life Orb
  cases with the Python simulator.
- `residual_status_hp_mutation` is ROM-differential for poison, burn, and toxic
  HP mutation: the audit enters `ResidualDamage.check_toxic` after the
  text/animation branch and compares HP plus toxic counter changes against the
  Python simulator. The full `ResidualDamage` text/animation entry is not part
  of this headless proof.
- `residual_status_turn_timing` is source-mirrored from `Battle_PlayerFirst`
  and `Battle_EnemyFirst`: supported residual statuses apply after each
  selected non-forced action phase when neither active Pokemon has already
  fainted.
- `leftovers_hp_mutation` is ROM-differential: the audit calls
  `HandleLeftovers.do_it` for player/enemy heal, full-HP no-op, no-item no-op,
  and minimum-heal cases and compares HP with the Python simulator. The handler
  reaches text/animation handling after mutation, so this proof claims HP
  mutation only.
- `leftovers_between_turn_timing` is source-mirrored from
  `HandleBetweenTurnEffects`: Leftovers runs after selected actions and
  residual status effects when no forced-switch prompt is pending.
- `paralysis_checkturn_text_path` is ROM-differential: the audit injects
  deterministic link-battle RNG, hooks `StdBattleTextbox`, and compares the
  ROM `FullyParalyzedText` path plus consumed RNG count against the Python
  simulator across baseline, half-Fighting, full-Fighting, player, and enemy
  cases.
- `paralysis_turn_blocking_timing` is source-mirrored from `DoPlayerTurn` and
  `DoEnemyTurn`: paralysis is checked before supported move execution. Speed
  recalculation is separately byte-proven; paralysis infliction and other
  `CheckTurn` blockers are still out of scope.
- `sleep_checkturn_text_path` is ROM-differential: the audit hooks
  `StdBattleTextbox` / `FarPlayBattleAnimation` and compares ROM fast-asleep /
  wake-up paths plus sleep status-byte decrement against the Python simulator for
  player/enemy fast-asleep and wake-up cases.
- `sleep_turn_counter_timing` is source-mirrored from `BattleCommand_CheckTurn`:
  sleep decrements before supported move execution, blocks while still asleep,
  and clears status when the counter reaches zero. Sleep Talk / Snore bypass
  behavior is source-mirrored only; Sleep Clause slot bookkeeping and sleep
  infliction are still out of scope.
- `freeze_checkturn_text_path` is ROM-differential: the audit hooks
  `StdBattleTextbox` and compares ROM `FrozenSolidText` plus Flame Wheel /
  Sacred Fire CheckTurn bypass return paths against the Python simulator for
  player/enemy cases.
- `freeze_turn_blocking_timing` is source-mirrored from
  `BattleCommand_CheckTurn`: freeze blocks after sleep and before flinch /
  paralysis. Flame Wheel / Sacred Fire CheckTurn bypass is modeled, but their
  later `defrost` move-script command is not yet implemented.
- `flinch_checkturn_text_path` is ROM-differential: the audit hooks
  `StdBattleTextbox` and compares ROM `FlinchedText` plus flinch substatus
  clearing against the Python simulator for player/enemy cases.
- `flinch_turn_blocking_timing` is source-mirrored from
  `BattleCommand_CheckTurn`: flinch blocks after sleep/freeze and before
  paralysis, and clears after the block.
- `selected_turn_sequence` is a source mirror in this slice and is covered by
  the headless simulator audit. It still needs direct differential ROM cases
  before being promoted to byte-proven.
- selected switch actions and explicit forced switch phases are source-mirrored
  for user-provided choices. Automatic forced-switch selection, shift/set
  prompts, trapping/Pursuit/phazing switch effects, and Boss AI switch selection
  still need their own proof gates before being promoted.
- `boss_ai_selector_from_post_score_bytes` is source-mirrored through the
  existing Boss AI selector oracle. It proves the headless scenario can consume
  post-score selector output. The audit directly calls ROM
  `BossAI_SelectMove.first_pass` for deterministic no-roll selector edges; the
  stochastic best-vs-second roll surface is still source-mirrored through the
  selector oracle until seeded selector RNG has its own differential. It does
  not prove Boss AI score-model correctness or switch policy.
- `boss_ai_switch_policy_from_final_confidence` is source-mirrored from
  `BossAI_SwitchOrTryItem`'s final confidence/threshold/roll block. It supports
  fast fixed/sample/exhaustive "how often does this known switch candidate
  commit?" sweeps across tier/class threshold, anti-loop, sack, wincon-risk, and
  90/75/55 percent switch-roll bands. It does not prove candidate selection or
  confidence generation; use `rom-switch-materialize` for the current ROM-backed
  full switch-dispatch path.
- `protect_blocks_before_accuracy` is source-mirrored from
  `BattleCommand_CheckHit.Protect`: the simulator places Protect before Lock-On
  and accuracy. It remains pending direct ROM differential because the isolated
  ROM path enters text/delay handling under the current safe-call harness.
- Boss AI live score generation, Boss AI switch candidate/confidence generation, automatic
  volatile-state lifetimes, status infliction, freeze infliction, defrost
  move-script status clearing, Sleep Clause slot bookkeeping,
  held-item after-hit/between-turn effects beyond Rocky Helmet,
  Shell Bell, Life Orb, and Leftovers, source move damage-effect commands beyond
  normal/always-hit/Thunder/Gust/Earthquake HP mutation, held-item
  turn-order effects beyond Quick Claw and Choice Scarf, multi-hit/forced-move
  effects, battle start/end scripts, text, animation, EXP, and party writes are
  intentionally out of scope until implemented and proven.
