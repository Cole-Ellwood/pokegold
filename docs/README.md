# Helper Docs Entrypoint

## Boss AI Cognition Mode

If this session is about Boss AI, read every linked doc with permission to think
wildly on paper: terrifying legal reads, sacrifice lines, bluffs, counterbluffs,
and ugly battle trees are welcome in the journal. Source changes stay narrow,
public-information-only outside explicitly authored Haki branches,
memory-budgeted, and verified.

READ THIS FIRST in new Codex/helper sessions before broad source search.

Audience: future Codex/helper agents, not human readers. Optimize for source
navigation, implementation safety, and drift detection.

## Core Promise

First-Playthrough Promise: this hack exists to make Pokemon Gold feel unknown
and dangerous again for a player who already knows Pokemon. Do not treat it as
generic hard mode, competitive Gen 2, or modernization for its own sake. Every
boss, balance, mechanics, QoL, and review decision should preserve the feeling
that Johto is bigger than the player, gym leaders can be scary because the
player can lose, and old knowledge is useful but incomplete.

## Required Read Order

1. `docs/agent_navigation/hack_mechanics_reference.md`: source-derived
   mechanics lookup for type matchups, move categories/data, item attributes,
   and Pokemon stats. Read before any mechanics, balance, AI, moveset, item,
   or stat claim.
2. `docs/agent_navigation/gen2_vs_modern_mechanics.md`: Gen 2 vs modern
   mechanics drift guide. Use it with the source-derived reference above.
3. `docs/README.md`: helper-doc routing and precedence.
4. `docs/project_context.md`: First-Playthrough Promise, design constraints,
   done criteria.
5. `docs/project_map.md`: task-to-source routing.
6. `docs/project_roadmap.md`: current project workstreams and future-session
   status board.
7. `docs/agent_navigation/start_card.md`: one-screen lane picker for broad or
   ambiguous prompts.
8. `docs/agent_navigation/README.md`: constant-time task routing, source-zone
   classification, verification matrix, and durable artifact catalog.
9. `docs/generated/dev_index.md`: current banks, labels, source anchors, memory.
10. Task-specific docs:
   - Boss AI / trainer difficulty: `docs/boss_ai_spec.md`,
     `docs/boss_ai_bug_testing_plan.md`
   - Review / bug hunt: `docs/review_playbook.md`,
     `docs/bug_hunt_master_playbook.md`
   - Pokemon balance intent: `docs/balance_intent.md`,
     `docs/evolution_policy.md`, `docs/buff_backlog.md`,
     `docs/generated/balance_audit.md`
   - Existing mechanics: `docs/mechanics_changes_from_base.md`
   - QoL follow-up work: `docs/qol_handoff.md`,
     `docs/qol_research_report.md`
   - Graphics / emulator visual bugs:
     `docs/graphics_emulator_debugging.md`
   - Data rebalance history: `docs/manifest.md`
   - Build/release status: `docs/build.md`, `docs/validation_report.md`

## Fast Jump Modes

Use the full read order when the task is ambiguous or gameplay-facing. When the
prompt is about project organization, future AI usability, workspace hygiene, or
making the repo easier to jump through, stay in the navigation track:

1. `docs/agent_navigation/start_card.md`
2. `docs/agent_navigation/README.md`
3. `docs/agent_navigation/subsystems/checkpoint_handoff.md`
4. `docs/agent_navigation/navigation_health_check.md`
5. `docs/project_roadmap.md`

That mode may edit hand-authored docs, audit notes, `decisions/` entries, or
`journal/` entries. It must not touch ROM behavior, generated docs,
linker/build outputs, or unrelated dirty files.

## Debugger First

For bug reports, runtime questions, Boss AI behavior, route confusion, or broad
"what should I inspect next?" prompts, use the completed unified debugger before
old branch notes or stale worktrees:

```powershell
python -m tools.debugger next --symptom "<question>"
python -m tools.debugger triage --symptom "<question>"
python -m tools.debugger investigate --symptom "<question>"
```

Current completion source of truth:
`audit/debugger_godmode_completion_2026-05-24.md`. On `master` at or after
`fda6bbcb`, the verifier-gated debugger-godmode pgoal is complete: benchmark
29/29, pass_rate 1.000, audit `ready=True`, and `gap_actions=0`. Do not treat
`.claude/worktrees/*`, `.local/worktrees/debugger-masterpiece-roadmap`, or old
branch handoff notes as current debugger truth unless the task explicitly asks
to inspect those copies.

## Headless Battle Simulation

For no-GUI text/JSON battle simulation, start with:

```powershell
python -m tools.headless_battle --template
python -m tools.headless_battle --scenario <scenario.json> --json
python tools\audit\check_headless_battle_simulator.py
```

This is the new Python battle-state path. Current scope is selected turn
sequences with move actions, explicit switch actions against active-plus-bench
state, post-score Boss AI selector actions, final-confidence Boss AI
switch-policy actions for known candidate and confidence inputs, default-role
priority/raw-speed order, Quick Claw and Choice Scarf turn-order effects, HP mutation for normal
damaging moves, Rocky Helmet / Shell Bell / Life Orb after-hit HP effects,
poison / burn / toxic residual HP damage after selected action phases,
Leftovers between-turn healing,
paralysis fully-paralyzed move blocking and speed recalculation,
sleep counter decrement / fast-asleep blocking / wake-up clearing,
freeze frozen-solid blocking with Flame Wheel / Sacred Fire CheckTurn bypass,
flinch one-turn blocking and flag clearing,
move accuracy for supported damaging moves including accuracy/evasion stage
modifiers, BrightPowder, X Accuracy, Lock-On, semi-invulnerable
flying/underground targets, Thunder-in-rain, and source-table sure-hit effects,
ROM-style damage variation,
fixed/sample/exhaustive RNG modes, and damage core delegated to the existing
damage oracle. Its reports label byte-proven,
source-mirrored, and out-of-scope mechanics. Damage variation, default-role
turn order including Quick Claw and Choice Scarf, and supported damaging-move
accuracy and critical-hit chance have direct ROM-differential gates. Selected switch actions are
source-mirrored, not yet ROM-differential. Boss AI selector actions consume
exact final score bytes via
`select_from_score_bytes`; they do not calculate live scores from battle state.
Boss AI switch-policy actions consume an already-known candidate and confidence,
then mirror the final tier/class threshold, anti-loop/sack/wincon deltas, and
90/75/55 percent switch-roll bands from `BossAI_SwitchOrTryItem`; they do not
generate the candidate or confidence from battle state.
User-provided Protect flags are source-mirrored in the hit-check order, not yet
ROM-differential, because the isolated ROM path enters text/delay handling under
the current safe-call harness.
Scenarios can provide fully materialized stats/moves or source-table shorthand
such as `species`, `level`, and move names; shorthand uses repo base stats,
type rows, move rows, move IDs, and trainer/default stat profiles unless
overridden. Scenarios can also pass `stages.accuracy` and `stages.evasion` as
battle-stage modifiers from `-6` to `+6`, plus `volatile.protect`,
`volatile.x_accuracy`, and `volatile.lock_on` for current hit-check flags.
`volatile.flying` and `volatile.underground` model current semi-invulnerable
hit-check state. `volatile.focus_energy` feeds the supported critical-hit
chance surface. `volatile.flinched` models the current one-turn flinch
substatus. Gust and Earthquake additionally mirror the ROM
post-variation double-damage commands for flying and underground targets.
Scenarios can set `status` to `poison`, `burn`, or `toxic`; toxic also accepts
`toxic_count` as the current pre-residual counter. The residual HP mutation is
ROM-differential after the text/animation branch, while its selected-action
timing is source-mirrored from `Battle_PlayerFirst` / `Battle_EnemyFirst`.
Scenarios can also set `status` to `paralysis` for fully-paralyzed move
blocking before supported move execution. That check is ROM-differential
through `BattleCommand_CheckTurn` text-path hooks and covers the
Fighting-type passive thresholds. Paralysis speed recalculation, including
Electric and Fighting passive fractions, is ROM-differential through
`ApplyPrzEffectOnSpeed_Far`; paralysis infliction is not yet modeled.
Scenarios can set `status` to `sleep` with `sleep_turns` from 1 to 7. Sleep
counter decrement, fast-asleep blocking, and wake-up clearing are
ROM-differential through `BattleCommand_CheckTurn` text/animation hooks; Sleep
Clause slot bookkeeping and sleep infliction are not yet modeled.
Scenarios can set `status` to `freeze`. Frozen-solid turn blocking and the
Flame Wheel / Sacred Fire CheckTurn bypass are ROM-differential through
`BattleCommand_CheckTurn`; freeze infliction and the later `defrost`
move-script status clearing are not yet modeled.
Scenarios can set `volatile.flinched=true`. One-turn flinch blocking and flag
clearing are ROM-differential through `BattleCommand_CheckTurn`; automatic
volatile lifetime generation is not yet modeled.
Scenarios can set `item` to `LEFTOVERS`; the HP mutation is ROM-differential
through `HandleLeftovers.do_it`, and the between-turn timing is source-mirrored
from `HandleBetweenTurnEffects`.
Other source move damage-effect commands still need separate implementation and
proof. Supported damage scripts follow the ROM command order for implemented
surfaces: critical-hit chance, damage variation, and supported post-variation
damage effects run before hit checking, and HP is applied only if the hit check
passes.
Exhaustive mode reports distinct outcome classes with `raw_count` weights,
per-outcome `rng_weight` probabilities, and aggregate event/selector rates in
`summary`.
Outcomes that KO an active Pokemon while its bench is still alive set
`requires_forced_switch=true`; continue with an explicit forced switch phase
where the forced side switches and the other side waits. Do not claim full
battle automation, held-item turn-order effects beyond Quick Claw and Choice
Scarf, held-item after-hit effects beyond Rocky Helmet / Shell Bell / Life
Orb, held-item between-turn effects beyond Leftovers, automatic forced-switch selection, Boss AI live score generation, Boss AI
switch candidate/confidence generation, status infliction, freeze infliction,
defrost move-script status clearing, Sleep Clause slot bookkeeping,
automatic volatile-state lifetimes, source move
damage-effect commands beyond normal/always-hit/Thunder/Gust/Earthquake HP mutation, or
battle-script equivalence
until the simulator report and audit say that mechanic is supported.

## Truth Precedence

1. Current source files and linker outputs (`pokegold.map`, `pokegold.sym`).
2. Generated navigation mirror: `docs/generated/dev_index.md`.
3. Hand-authored helper docs for intent, workflow, review policy, and task notes.

If a helper doc conflicts with source/linker truth, trust source/linker truth and
update the helper doc. If linker outputs change and are kept, refresh the index:

```powershell
python scripts\generate_dev_index.py --rom pokegold
```

## Task Routing

- Start any mechanics, balance, AI, progression, or QoL task with
  `docs/project_context.md`.
- Use `docs/project_map.md` to choose source areas before broad `rg` searches.
- Use `docs/project_roadmap.md` before inventing new project plans; update it
  when work completes, gets stuck, gains useful ideas, or remains untouched.
- Use `docs/agent_navigation/README.md` when the prompt is broad, when a future
  helper needs an `O(1)` task route, or when classifying source/generated/scratch
  paths before editing.
- Use `docs/agent_navigation/source_output_ownership.md` and
  `python tools\audit\check_workspace_hygiene.py` for repo polish, raw-folder
  clutter, ignored build outputs, or "10/10 workspace" prompts.
- Use `docs/agent_navigation/doc_roles.md` before adding routing facts that
  might duplicate existing docs.
- Use `docs/generated/dev_index.md` before memory-sensitive edits or when
  jumping to labels/banks.
- Use `docs/review_playbook.md` for reviews, bug hunts, and finding
  severity/risk classes.
- Use `docs/bug_hunt_master_playbook.md` when the prompt asks for a broad,
  exhaustive, release-facing, or "bug could be anywhere" investigation.
- Use `docs/boss_ai_spec.md` before changing boss decisions, switch/item logic,
  prediction, timing, or AI memory.
- Use `docs/balance_intent.md`, `docs/evolution_policy.md`, and
  `docs/buff_backlog.md` before changing Pokemon stats, learnsets, types, or
  evolutions.
- Use `docs/qol_handoff.md` before proposing or implementing QoL work; it marks
  already-implemented QoL separately from remaining candidates.

## Build Tip For Codex On Windows

If PowerShell says `make` is unavailable, check WSL before declaring builds
blocked. In this workspace, the WSL `bash` command can run GNU Make even though
`make` is not on the PowerShell `PATH`.

See `docs/build.md` for the exact WSL command pattern, especially the explicit
repo-local RGBDS `.exe` variables needed when building from WSL against this
Windows checkout.

## Always Verify

Run the doc navigation audit after helper-doc or navigation changes:

```powershell
python tools\audit\check_navigation_floor.py
```

For lower-level debugging, the wrapped command is:

```powershell
python tools\audit\check_docs_navigation.py
```

Run task-relevant audits from `tools/audit/` before finalizing source changes.
Do not edit `.gbc`, `.o`, `.map`, `.sym`, or generated index output by hand.

Regenerate the source-derived balance audit after Pokemon stat, learnset, type,
or evolution edits:

```powershell
python scripts\generate_balance_audit.py
```

Regenerate the source-derived mechanics reference after changes to mechanics,
move data, item attributes, type matchups, or base stats:

```powershell
python scripts\generate_hack_mechanics_reference.py
python tools\audit\check_mechanics_docs_and_fixtures.py
```

Regenerate the player-facing trainer dossier PDF (gym leaders + Elite 4 +
Champion teams, Pokemon Showdown style — name, level, item, full moveset, base
stats with bars) after edits to `data/trainers/parties.asm` for any boss
trainer or after relevant base-stat edits. Output is `docs/trainer_dossier.pdf`.

```powershell
python -m pip install reportlab Pillow   # one-time install
python scripts\generate_trainer_dossier_pdf.py
```
