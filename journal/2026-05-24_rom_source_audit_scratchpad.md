# ROM Source Bug Audit Scratchpad - 2026-05-24

## Goal

Read-only audit of the actual ROM source/data behavior, excluding debugger and
support tooling except for repo routing docs and optional read-only verification
commands. Write only this scratchpad and the final audit file.

## Boundaries

- Allowed writes: this file and `audit/rom_source_bug_audit_2026-05-24.md`.
- Do not edit ROM behavior, generated docs, build outputs, debugger tools, or
  unrelated dirty files.
- Prioritize `engine/`, `data/`, `maps/`, `constants/`, `home/`, `ram/`,
  `audio/`, `gfx/`, `macros/`, top-level assembly, and linker/build truth.
- Use web search only for assembly/RGBDS/Game Boy reference gaps.

## Startup Evidence

- Existing dirty worktree observed before this scratchpad was created. Treat all
  pre-existing modifications and untracked files as user/partner work.
- Routing docs read: `docs/README.md`, `docs/project_context.md`,
  `docs/project_map.md`, `docs/bug_hunt_master_playbook.md`,
  `docs/review_playbook.md`.

## Investigation Frame

- Source truth files: current ROM source plus linker outputs when needed.
- Generated/output files not to edit: `docs/generated/*`, `*.gbc`, `*.o`,
  `*.map`, `*.sym`.
- Relevant read-only commands: `git status --short --branch`, `git diff --stat`,
  `git ls-files`, `rg`, `Get-Content`.
- Verification commands may write temp/output, so only run them after checking
  their write behavior or when useful enough to explicitly justify.

## Coverage Log

- [x] Startup docs and source map.
- [x] Top-level include/build/link layout.
- [ ] RAM/SRAM/HRAM layout.
- [ ] Constants and table-width contracts.
- [x] Battle core and move effects changed-source pass.
- [x] Boss/trainer AI changed-source pass.
- [x] Pokemon/move/item/trainer data table consistency pass.
- [x] Map coordinate and warp static pass.
- [x] Home engine and low-level graphics/input/save changed-source pass.
- [ ] Audio/graphics ROM data references.

## Leads

- Confirmed bug: `engine/battle/ai/boss_policy_move.asm`
  `.DamagingMoveBlockedByTypeImmunity` uses
  `BossAI_CheckEnemyMoveTypeMatchupVsPlayerNoItem` on
  `wEnemyMoveStruct + MOVE_TYPE` before Hidden Power's effect command rewrites
  `BATTLE_VARS_MOVE_TYPE`. `data/moves/moves.asm` stores Hidden Power as
  `NORMAL`, so enemy Hidden Power into a Ghost target is hard-scored to 80 and
  exits early even when the trainer's DVs make Hidden Power a non-Normal type.
  Concrete source scenario: Rival1 parties 13-15 have Magneton with
  Hidden Power; `data/trainers/dvs.asm` gives Rival1 DVs 13/13/13/13, which
  the ROM formula maps to HP Bug. Bug vs Ghost/Psychic is neutral, while
  Normal vs Ghost/Psychic is no effect.
- Rejected: Rival1 Gastly SPITE->CONFUSION leaves
  `data/boss_ai/matchup_tables.asm` stale. The generated ROM table includes
  Rival1, but `python tools\audit\check_ko_band_oracle_self_test.py` passes:
  dry-run generator output matches the committed ROM table, with 39 leader rows
  and 179 slots.
- Rejected: `BossAI_EvaluateMoveForPolicy` early stat-drop branch loses the
  score pointer by using `hl` for stat levels. The score helpers reload `hl`
  from `wBossAIScorePtr`.
- Rejected: sleep duration change stores an off-by-one duration. The sleep
  check decrements before testing wake, so storing 3..5 yields 2..4 denied
  actions as intended.

## Verification Notes

- `python tools\audit\check_ko_band_oracle_self_test.py` passed.
- `python tools\audit\check_farcall_hl_clobber.py` passed; scanned 1877 ASM
  files.
- `python tools\audit\check_battle_math_safety.py` passed; scanned 196 ASM
  files.
- `python tools\audit\check_vram_request_contract.py` passed.
- `git diff --check -- engine constants data maps home ram audio gfx macros
  main.asm layout.link Makefile` produced no output.
- Active ROM `INCLUDE`/`INCBIN` target scan: 2214 INCLUDE, 3253 INCBIN,
  0 issues after excluding nested worktrees and non-ROM support areas.
- ROM data consistency pass: moves 254/254, item tables 256-wide, 251 base
  stats, 251 evo sections, 3225 wild encounter rows, 465 map trainer refs,
  0 issues.
