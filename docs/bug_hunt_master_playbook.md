# Bug Hunt Master Playbook

Audience: future Codex/helper agents asked to search for bugs anywhere in this
ROM hack. This is an execution checklist, not a design essay. Follow it when a
prompt is broad, scary, release-facing, or says some version of "a bug could be
on any line."

Core rule: find bugs by walking invariants through the project. Do not scroll
randomly and hope defects announce themselves. Every pass should identify an
owner, every owner should have readers/writers checked, and every claim should
end in a command, trace, source citation, or explicit manual proof gap.

## Non-Negotiables

- Preserve the First-Playthrough Promise: Pokemon Gold should feel unknown,
  dangerous, and fair for a veteran player. A bug can be a crash, a table
  mismatch, hidden-information AI, cheap difficulty, or QoL that erases pressure.
- Current source and linker outputs are truth. `docs/generated/dev_index.md` is
  the generated mirror. Hand-authored docs explain intent and workflow.
- Never hand-edit `.gbc`, `.o`, `.map`, `.sym`, or files under
  `docs/generated/`.
- Do not clean, reset, or delete dirty worktree changes unless the user
  explicitly asks for that exact action.
- Static audits are evidence. They are not gameplay proof. Emulator/debugger
  traces and playtest notes must say exactly what they prove.

## Zero-Minute Startup

Run this before deciding where the bug hunt starts:

```powershell
Set-Location "C:\Users\lolno\Downloads\pokemon gold hack"
git status --short --branch
```

Read these files in order:

1. `docs/README.md`
2. `docs/codex_context.md`
3. `docs/project_map.md`
4. `docs/project_roadmap.md`
5. `docs/agent_navigation/start_card.md`
6. `docs/agent_navigation/README.md`
7. `docs/agent_navigation/task_router.md`
8. `docs/agent_navigation/artifact_catalog.md`
9. `docs/agent_navigation/verification_matrix.md`
10. `docs/codex_review_playbook.md`
11. `docs/generated/dev_index.md`

Before touching source, write down the investigation frame in the scratch notes
or final report:

- target subsystem or broad-lane route;
- source-truth files;
- generated/output files that must not be edited;
- durable evidence artifacts to inspect before scratch paths;
- relevant audit commands;
- build expectation;
- manual or live-proof gaps that automation cannot cover.

If no route fits, search docs first and report the missing route as a doc bug:

```powershell
rg -n "keyword|related phrase" docs
rg -n "SymbolOrPhrase" engine data maps constants home ram
```

## Read-Only Bug Hunt Mode

Use this mode when the user says read-only, review-only, report-only, or "do not
fix." In strict read-only mode, do not edit files and do not run commands that
write repo-tracked files, build products, generated docs, emulator state, or
scratch/temp output without asking first.

Safe read-only commands:

```powershell
git status --short --branch
git diff --stat
git diff --name-status
git ls-files
rg -n "pattern" docs engine data maps constants home ram tools scripts
Get-Content path\to\file
Get-Item path\to\file
```

Ask first before running:

- builds or `make`;
- audit scripts, because some create `.local/tmp` or inspect generated mirrors;
- generators such as `scripts\generate_balance_audit.py`, because default
  output may update `docs/generated/`;
- trace, emulator, PyBoy, or save-state tools;
- formatters, cleanup helpers, or anything that stages/commits.

In read-only reports, list the checks that would prove or disprove each lead,
but do not run them unless the user loosens the constraint. If a command writes
only ignored temp output, say that explicitly before asking.

## Search Method

Use this loop for every suspected bug:

1. State the invariant in one sentence.
2. Find the owner file and label/table.
3. Search all direct readers and writers.
4. Search pointer tables, constants, generated mirrors, and docs.
5. Find side-specific copies: player/enemy, Gold/Silver, normal/debug/trace,
   data/table, text/description, map/event/special.
6. Construct a falsifier: the smallest state, table row, or command that would
   prove the invariant wrong.
7. Run the relevant audit/build/trace.
8. Report what is proven and what still needs manual play.

Default symbol search:

```powershell
rg -n "SymbolName" engine data maps constants home ram tools scripts docs
```

Default label-neighborhood search:

```powershell
rg -n "LabelName|RelatedLabel|RelatedConstant" engine data maps constants home ram
```

Default doc/source drift search:

```powershell
rg -n "FeatureName|SymbolName|custom term" docs engine data maps constants ram
```

If a broad search returns too much, narrow by source owner rather than changing
the question. For example, a battle bug should narrow to `engine/battle/`,
`data/moves/`, `constants/*battle*`, and `ram/wram.asm` before searching maps.

## Universal Bug Classes

Check these on every serious pass:

- Build break: source does not assemble/link for Gold or Silver.
- Bank overflow: code/data fits one build but not debug, trace, or Silver.
- Memory lifetime bug: temp state reused after a call that clobbers it.
- WRAM/SRAM/HRAM pressure: new state collides with scarce or saved memory.
- Pointer drift: data table changed without pointer/constant/table-length owner.
- Terminator drift: table parser expects `-1`, `0`, count byte, or fixed width
  and the edited data violates that contract.
- Side drift: player path works but enemy path, AI path, or reflected path does
  not.
- Version drift: Gold works but Silver points at stale object/linker data.
- Generated-doc staleness: `.map` or `.sym` changed and
  `docs/generated/dev_index.md` was not regenerated.
- Design drift: a change makes the hack merely harder, cleaner, or faster while
  damaging fair uncertainty.
- Proof drift: a report claims gameplay behavior from static source/audit alone.

## Assembly Routine Audit

For each suspicious routine:

1. Identify inputs: registers, carry flag, zero flag, memory variables, far-call
   bank context, and macros.
2. Identify outputs: registers, flags, memory writes, return convention, and
   caller assumptions.
3. Search every caller and confirm the same convention is used.
4. Search every callee and confirm clobbers are acceptable.
5. Check bank calls: local call, `farcall`, home-bank wrapper, or included file.
6. Check flag sense twice. Gen 2 assembly bugs often hide in `jr c` vs `jr nc`,
   `and a` before return, or a helper that documents carry backward.
7. Check byte/word order. Speed, HP, stats, and damage are often two-byte values.
8. Check sentinel behavior for zero, max value, no move, no item, no species,
   no trainer, end-of-table, and fainted party slot.
9. Check both normal and debug/trace builds if the routine is inside
   conditional assembly.

State-lifetime checklist:

- If a helper writes `wCurSpecies`, `wCurPartySpecies`, `wBaseType1`,
  `wBaseType2`, or any base-data field through `GetBaseData`, prove every return
  path restores the prior state or document that downstream consumers are meant
  to see the candidate species.
- If a helper writes `hBattleTurn`, prove it restores the old turn value before
  returning.
- If a helper writes `wTypeMatchup`, `wEnemyMoveStruct`, `wPlayerMoveStruct`,
  `wCurEnemyMove`, or `wCurPlayerMove`, check whether later scoring, text, or
  battle-resolution code consumes that scratch state.
- If a helper uses `wBossAITemp*`, `wTempByteValue`, `wBuffer*`, or HRAM scratch
  bytes, search all nested calls for the same scratch variables before assuming
  the value survives.
- Candidate-evaluation helpers are especially dangerous: a routine that tests a
  possible switch target may intentionally load candidate base data, but the
  caller must not accidentally leave that state visible to stay/item/attack
  paths unless that is the documented contract.

Use comments sparingly in findings. Quote the exact line/label and explain the
behavior, not the whole routine.

## Data Table Audit

For every data edit or suspected data bug, inspect:

- defining constant in `constants/`;
- pointer table in `data/`;
- table row format and terminator;
- parser routine in `engine/` or `home/`;
- name, description, animation, item pocket, effect, and text owner;
- Gold/Silver-specific copies;
- trainer usage and wild/progression availability;
- generated audit mirrors such as `docs/generated/balance_audit.md`;
- release notes or manifest if the table is part of shipped balance.

Common failure pattern: the visible row looks correct but the parser indexes a
parallel table, or an enum constant changed without every consumer changing.

## Build And Truth Pass

Start here for release-facing or repo-wide bug hunts.

Read:

- `docs/build.md`
- `docs/generated/dev_index.md`
- `docs/agent_navigation/source_output_ownership.md`
- `Makefile`
- `layout.link`
- `roms.sha1`

Check:

- `pokegold.map` and `pokegold.sym` exist and match the source generation time
  implied by the current build state.
- `docs/generated/dev_index.md` agrees with current linker outputs.
- Root `.gbc`, `.map`, `.sym`, and object files are treated as build outputs,
  not source to hand-edit.
- If the build changes linker outputs, regenerate the generated index after the
  build:

```powershell
python scripts\generate_dev_index.py --rom pokegold
```

Preferred build command from this Windows checkout:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

If WSL or `make` is blocked, use direct RGBDS only as a fallback and say that
the normal build route was unavailable.

## Boss AI Pass

Start here for "boss AI", "trainer AI", "cheating", "switch logic", "major
trainer difficulty", and broad fairness bugs.

Read:

- `docs/boss_ai_spec.md`
- `docs/boss_ai_bug_testing_plan.md`
- `docs/boss_ai_post_patch_notes.md`
- `docs/boss_ai_trace_capture.md`
- `docs/agent_navigation/subsystems/boss_ai_trace.md`

Inspect:

- `engine/battle/ai/boss.asm`
- `engine/battle/ai/move.asm`
- `engine/battle/ai/items.asm`
- `engine/battle/ai/switch.asm`
- `engine/battle/ai/scoring.asm`
- `engine/battle/core.asm`
- `engine/battle/used_move_text.asm`
- `engine/battle/read_trainer_attributes.asm`
- `ram/wram.asm`
- `data/trainers/ai_tiers.asm`
- `data/trainers/parties.asm`

High-risk invariants:

- Boss move choice happens before player action selection.
- Enemy switch/item logic may run after player action parsing, so it must not
  read current-turn player switch intent.
- `BossAI_RecordPlayerSwitch` may record pending state only.
- Pending observations become legal on the next turn, keyed by
  `BossAI_IncrementTurnsElapsed`.
- Revealed moves come from real visible use, especially `wPlayerUsedMoves`.
- Boss AI must not read hidden player party slots, hidden HP, unrevealed moves,
  unrevealed held items, private stat data, future input, or manipulated RNG.
- Boss tiers should not fall into unsafe legacy scoring helpers.
- `wBossAIStateEnd` must remain before `wEventFlags`.
- Boss AI state must stay inside the reserved WRAMX block beginning at
  `wBossAITier`.

Required audits for Boss AI logic:

```powershell
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_live_capture_ledger.py
```

For live proof, use the trace system. A proof needs a current trace ROM,
boss-position state or debugger position, public battle context, nonzero trace
fields at a decision point, and an explanation of why the decision follows
public information.

```powershell
python tools\trace\boss_ai_trace_capture.py --symbols-only
python tools\trace\boss_ai_state_factory.py --all --update-manifest
python tools\trace\boss_ai_trace_batch.py
python tools\trace\boss_ai_trace_batch.py --execute --only <capture_id>
python tools\audit\check_boss_ai_live_capture_ledger.py
```

For Morty candidates only, run the Morty-specific strict preflight before
trusting the state:

```powershell
python tools\trace\boss_ai_trace_state_probe.py --save-state path\to\before_morty_decision.state --expect-morty --strict
```

For other bosses or scenarios, add the candidate to
`audit/boss_ai_trace/live_capture_manifest.json` and let the batch runner enforce
whatever `preflight.expect` guard exists for that capture. Old `.local/` RAM, a
dry-run that reports `MISSING_STATE`, or a symbol dump is not live proof. Do not
mark Morty/Jasmine/Clair/Koga/Lance/Red proven from static audits alone. As of
2026-04-27, the factory covers all real trainer rows in the manifest, and the
synthetic shared switch-loop scenario has a separate fixture script and live
trace artifact.

## Battle Mechanics Pass

Start here for moves, type passives, held items, damage, category, status,
immunity, contact, reflection, and battle text bugs.

Read:

- `docs/mechanics_changes_from_base.md`
- `docs/agent_navigation/custom_terms.md`
- `docs/codex_review_playbook.md`

Inspect:

- `engine/battle/core.asm`
- `engine/battle/effect_commands.asm`
- `engine/battle/type_passive_damage_mods.asm`
- `engine/battle/late_gen_held_items.asm`
- `engine/battle/move_effects/`
- `engine/battle/used_move_text.asm`
- `data/moves/`
- `constants/move_constants.asm`
- `constants/move_effect_constants.asm`
- `constants/battle_constants.asm`
- `data/items/`

Check:

- player and enemy side use the same battle rule unless a documented exception
  exists;
- AI estimation and battle resolution do not diverge silently;
- Counter, Mirror Coat, Destiny Bond, Encore, Substitute, Protect, disable,
  recharge, and reflected damage still consume the correct category/effect;
- status immunity and visible fail states match public battle rules;
- held-item effects update text, item data, and battle behavior together;
- contact effects use `data/moves/contact_flags.asm` consistently.

Minimum audit:

```powershell
python tools\audit\check_battle_math_safety.py
python tools\audit\check_release_smoke.py
```

## Pokemon And Trainer Data Pass

Start here for stats, types, evolutions, learnsets, boss parties, rival parties,
items, TMs, and weak-Pokemon balance bugs.

Read:

- `docs/balance_intent.md`
- `docs/evolution_policy.md`
- `docs/buff_backlog.md`
- `docs/generated/balance_audit.md`
- `docs/manifest.md`

Inspect:

- `data/pokemon/base_stats/`
- `data/pokemon/base_stats.asm`
- `data/pokemon/evos_attacks.asm`
- `data/pokemon/evos_attacks_pointers.asm`
- `data/pokemon/egg_moves.asm`
- `data/moves/tmhm_moves.asm`
- `data/trainers/parties.asm`
- `data/trainers/attributes.asm`
- `data/trainers/ai_tiers.asm`
- `constants/pokemon_constants.asm`
- `constants/trainer_constants.asm`
- `constants/trainer_data_constants.asm`

Check:

- trainer-party move edits are separate from species learnset legality;
- evolution changes match policy and do not strand species without role support;
- type changes match moves, weaknesses, boss usage, and intended discovery;
- TM/HM and egg move access do not accidentally make boss prep trivial;
- data rows and pointer rows stay synchronized;
- generated balance audit reflects current source.

Minimum commands:

```powershell
python scripts\generate_balance_audit.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_release_smoke.py
```

## Progression, Map, And QoL Pass

Start here for NPCs, maps, flags, scenes, event scripts, tutors, move reminder,
repel, Pokemon Center flow, bike registration, and other friction changes.

Read:

- `docs/qol_handoff.md`
- `docs/qol_research_report.md`
- `docs/agent_navigation/subsystems/qol_map_scripts.md`
- `docs/codex_context.md`

Inspect:

- `maps/`
- `data/maps/`
- `engine/events/`
- `data/events/special_pointers.asm`
- `engine/overworld/`
- `constants/event_flags.asm`
- `constants/map_constants.asm`
- `constants/script_constants.asm`
- `data/text/`

Check:

- event flags are set, cleared, and reused safely;
- scene scripts cannot softlock if approached in an unexpected order;
- specials have pointer entries and bank-safe call paths;
- text changes fit and reference valid strings;
- QoL removes tedium without removing preparation or resource pressure;
- map-bank pressure is checked after script growth;
- manual playtest gaps are named when no emulator path was exercised.

Minimum commands:

```powershell
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
```

## Graphics, Audio, And Assets Pass

Start here only when the task names graphics, sprites, palettes, tilesets,
music, cries, or SFX.

Inspect:

- `gfx/`
- `audio/`
- `audio.asm`
- `data/sprites/`
- `data/tilesets.asm`
- `constants/music_constants.asm`
- `constants/sfx_constants.asm`

Check:

- generated `.2bpp`, `.1bpp`, `.gbcpal`, `.lz`, and `.dimensions` outputs are
  build products;
- pointer tables and constants match asset additions;
- both Gold and Silver asset variants build;
- final report names visual/audio gaps if not inspected in-game.

## Documentation Pass

Documentation bugs matter here because future sessions are expected to use the
docs as their navigation layer.

Check:

- `docs/README.md` still names the fastest entrypoints.
- `docs/project_map.md` routes broad work correctly.
- `docs/agent_navigation/task_router.md` has a row for the prompt shape.
- `docs/agent_navigation/verification_matrix.md` has an audit floor.
- `docs/agent_navigation/doc_roles.md` owns where new routing facts belong.
- `docs/agent_navigation/navigation_health_check.md` still describes the
  acceptance criteria for navigation changes.
- `docs/agent_navigation/artifact_catalog.md` names durable evidence before
  scratch or `.local/` paths.
- `docs/generated/dev_index.md` was regenerated only through its script.
- Any stale helper-doc claim is corrected or reported.

Minimum commands:

```powershell
python tools\audit\check_navigation_floor.py
```

Use `python tools\audit\check_navigation_floor.py --workspace-hygiene` only when
the task includes raw-folder clutter, output ownership, or cleanup planning.

## Historical Findings And Evidence Artifacts

Before relabeling an old issue, read durable evidence through
`docs/agent_navigation/artifact_catalog.md`.

- `docs/bug_hunt_labeled_findings_2026-04-26.md` is a bug-hunt evidence ledger
  from a specific dirty checkout. Treat each entry as a lead until current
  source recheck proves it open, resolved, or stale.
- `docs/bugs_and_glitches.md` records original Gold/Silver bugs and Crystal-era
  fixes. It is historical fix documentation, not the current romhack bug queue.
- `audit/boss_ai_trace/live_capture_ledger.md` owns live Boss AI proof status.
  Do not promote a boss/scenario from `UNTOUCHED` without a current capture file
  and a passing ledger audit.
- If a finding changes status, cite the current file/line evidence and command
  output that changed your mind. Do not edit ledgers to make counts look tidy.

## Broad Bug Hunt Command Floor

For a broad review where no narrower matrix row is enough, run:

```powershell
python tools\audit\check_navigation_floor.py
python tools\audit\bug_hunt_triage.py
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_trace_invariants.py
python tools\audit\check_boss_ai_memory_budget.py
python tools\audit\check_boss_ai_live_capture_ledger.py
python tools\audit\check_battle_math_safety.py
python scripts\generate_balance_audit.py --out .local\tmp\balance_audit_check.md
git diff --check
```

Treat `bug_hunt_triage.py` as a lead printer, not a proof gate. If it reports
nothing, keep hunting by invariant; if it reports a lead, prove or reject the
specific source path before broadening.

Then build both ROMs:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

If source did not change, a build may report "up to date." Record that exact
fact. Do not turn it into gameplay validation.

If the build changes `.map` or `.sym` outputs, refresh the generated navigation
mirror and rerun the navigation floor:

```powershell
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_navigation_floor.py
```

## Finding Standard

Every finding should include:

- severity: `P0`, `P1`, `P2`, or `P3`;
- exact file and line;
- current source basis: branch, dirty-state summary, and whether the finding is
  new, historical, reopened, or resolved in current source;
- observed invariant break;
- user-visible or design-visible consequence;
- concrete fix direction;
- commands, traces, or source checks used;
- residual proof gap.

Severity defaults:

- `P0`: build break, crash, save corruption, hidden-information boss cheating,
  or progression softlock.
- `P1`: wrong battle behavior, wrong trainer/boss behavior, serious data drift,
  or unfair difficulty spike.
- `P2`: edge-case gameplay bug, stale table consumer, missing audit coverage, or
  nonfatal release inconsistency.
- `P3`: stale docs, weak routing, tooling polish, or low-risk cleanup.

Use this report shape:

1. Findings, ordered by severity.
2. Open questions or assumptions.
3. Verification performed.
4. Residual risks or test gaps.
5. Documentation gaps discovered.

If no bugs are found, say that directly and name what was not proven.

## Stop Conditions

A bug hunt is not done until the final report names:

- files changed by this session, or that no files were changed;
- checks run and pass/fail status;
- build status if source changed;
- generated files refreshed or deliberately untouched;
- manual emulator/playtest/trace gaps;
- dirty worktree changes that pre-existed the session and were preserved.

If context is running low, write a self-contained handoff under `outbox/` with
the exact read order, commands already run, findings, unresolved leads, and
which files are safe or unsafe to touch next.
