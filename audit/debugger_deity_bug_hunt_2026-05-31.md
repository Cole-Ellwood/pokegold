# Debugger Deity Bug Hunt - 2026-05-31

Scope: adversarial pass against the completed debugger/deity surfaces, looking
for both real ROM bugs and debugger alerts that overclaim ROM evidence.

## Investigation frame

- Worktree at start: `master` ahead of origin with only
  `pokegold_trace.gbc.ram` untracked.
- Source truth: current source plus rebuilt `pokegold.gbc`, `pokesilver.gbc`,
  and explicit refreshed `pokegold_trace.gbc` for Boss AI materialization.
- Main stress route:
  - `python tools\audit\bug_hunt_triage.py --self-test`
  - `python tools\audit\bug_hunt_triage.py --max-leads 50`
  - `python -m tools.debugger fuzz --symptom "find hidden ROM bugs across battle mechanics boss AI maps items and progression" --max-cases 64 --seed 424242 ...`
  - generated Boss AI policy cases, batch simulation, review queue, and
    materialized `explain-decision --run-rom-proof auto` packets.

## Confirmed ROM bug fixed

`engine/battle/move_effects/spikes.asm` fails `BattleCommand_Spikes` when three
layers are already down (`cp 3` then `.failed`). The Boss AI scorer recognized
that state but only added a normal discourage of `+24`, leaving capped Spikes at
score `44`. Because scores under `80` remain selectable, the selector left a
small chance to pick a guaranteed failed fourth Spikes click.

Materialized evidence before fix:

- Scenario: `generated_spikes_spin_424242_00001`
- ROM scores: `[44, 46, 38, 46]`
- Selector probability included `move_spikes=4.3%`
- Policy reason: "A fourth local Spikes click fails after the stack is already
  capped."

Fix:

- `engine/battle/ai/boss_policy_move.asm`: capped Spikes now sets score `80`
  with `BossAI_SetScoreHL`, making it a hard blocked move.

Materialized evidence after fix:

- Scenario: `generated_spikes_spin_1_00000`
- Command:
  `python -m tools.boss_ai_debugger explain-decision --scenario .local\tmp\debugger_seed1_after_expectation_fix.jsonl --scenario-id generated_spikes_spin_1_00000 --run-rom-proof auto --json-out .local\tmp\explain_packets\generated_spikes_spin_1_00000_after_trace_rebuild.json --focus-action-id move_surf`
- ROM scores: `[80, 46, 38, 46]`
- Selector probability: `move_spikes=0.0%`, `move_surf=95.7%`
- Proof status: `BOSS_AI_DEITY_PROOF_COMPLETE`, policy verdict `pass`.

## Debugger false positive fixed

The generated Boss AI review queue kept treating capped-Spikes cases as if
`move_sludge_bomb` must be the expected best damage answer. In cases where the
generated public facts made `move_surf` the ROM-materialized best damage line,
that produced a false `mismatch` after the real bug was fixed.

Fix:

- `tools/boss_ai_debugger/generators.py`: generated capped-Spikes cases now mark
  the Spikes action as blocked and choose the expected damage best from the same
  public prior used by the ROM-score mirror.
- `tools/boss_ai_debugger/tests/test_generators.py`: added coverage that capped
  Spikes is blocked and has zero selector probability, including the
  active-species-prior / identified-Ghost case that exposed the false positive.
- `tools/audit/trace_logic.py`: added an invariant that capped Spikes must use
  `BossAI_SetScoreHL` with score `80`, preventing regressions back to a merely
  discouraged selectable move.
- `audit/boss_ai_debugger/rule_map.json`: refreshed source hashes after the ASM
  change.

Post-fix generated run:

- Command:
  `python -m tools.boss_ai_debugger run-suite --profile changed-ai --count 24 --seed 1 --run-id 20260531_spikes_cap_fix_v4 --refresh-rom-score-materialization --json-out .local\tmp\boss_ai_changed_ai_spikes_cap_fix_v4.json`
- Result: `route_pass` increased to `16`, reviewable dropped to `8`, no capped
  Spikes case remains in top review items, and `rule map errors: []`.

## Broad checks that stayed quiet

- `python tools\audit\bug_hunt_triage.py --self-test`: pass.
- `python tools\audit\bug_hunt_triage.py --max-leads 50`: no ranked leads.
- `python tools\audit\check_release_smoke.py`: pass with the existing two
  stale-claim warnings.
- `python tools\audit\check_boss_ai_no_cheat.py`: pass.
- `python tools\audit\check_boss_ai_gating.py`: pass.
- `python tools\audit\check_boss_ai_trace_invariants.py`: pass after adding the
  capped-Spikes hard-block invariant.
- `python tools\audit\check_boss_ai_live_capture_ledger.py`: pass after
  refreshing trace-ROM hashes.
- `python tools\audit\check_boss_ai_debugger_deity.py --baseline`: pass 8/8
  after refreshing Boss AI deity artifacts.
- `python tools\audit\check_battle_math_safety.py`: pass.
- `python -m tools.damage_debugger.oracle`: 22/22 oracle predictions matched.
- `python -m tools.damage_debugger.fuzz --self-check-workers=2`: pass.
- `python -m tools.damage_debugger.fuzz --max-examples=100 --workers=2`: pass.
- Normal WSL build of `pokegold.gbc` and `pokesilver.gbc`: pass.
- Explicit trace ROM rebuild of `pokegold_trace.gbc`: pass.

## Remaining leads not promoted to bugs

The generated Boss AI review queue still reports several policy-preference
items such as cash-out timing, support handoff, setup cash-out, and prediction
risk. These are useful review leads, but they are not classified here as ROM
bugs because they are generated policy/taste scenarios unless a future pass
materializes a specific case and proves the expected action is a hard rule
rather than a preference.
