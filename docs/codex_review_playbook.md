# Codex Review Playbook

Use this file when a future Codex session is asked to inspect, review, or bug
hunt the ROM hack. It assumes the reviewer has no prior conversation context.

## Fast Start

1. Read `docs/codex_context.md` for the objective and fairness rules.
2. Read `docs/project_map.md` to route the task to the right source area.
3. Read `docs/generated/dev_index.md` for current labels, anchors, and memory
   pressure.
4. For Boss AI or battle work, read `docs/boss_ai_spec.md`.
5. For existing mechanics, read `docs/mechanics_changes_from_base.md`.
6. For release/data scope, read `docs/manifest.md` and
   `docs/RELEASE_NOTES.md`.

Do not start with broad source searches unless these docs fail to identify the
right subsystem.

## Review Stance

Lead with concrete findings. A useful finding has:

- exact file and line;
- why the behavior is wrong or risky;
- why it matters to the fair-but-hard hack goal;
- a concrete fix direction;
- confidence and severity.

If no issues are found, say so directly and name the remaining test gaps.

## High-Risk Bug Classes

- Objective drift: changes that make the hack easier through grinding, hidden
  knowledge, or QoL that removes strategic decisions.
- Hidden-information AI: boss decisions reading unrevealed party slots, hidden
  HP, unrevealed moves/items, private stats, future input, or manipulated RNG.
- Turn-order leaks: same-turn player switch or move input affecting boss
  switch/item decisions.
- Legacy AI re-entry: boss tiers falling back into unsafe legacy scoring helpers.
- Table drift: data tables changed without matching pointer tables, constants,
  descriptions, names, flags, or learnset/evolution entries.
- Memory pressure: new code/data added to ROM0, WRAM0, WRAMX, HRAM, or tight
  ROMX banks without checking the generated index.
- Generated-doc staleness: `.map` or `.sym` changed without regenerating
  `docs/generated/dev_index.md`.

## Boss AI Fairness Checklist

- Current-turn player input is not consumed by same-turn boss decisions.
- `BossAI_RecordPlayerSwitch` writes only pending state.
- Pending switch state is committed at the next `BossAI_IncrementTurnsElapsed`.
- Enemy move choice runs before player action selection.
- Enemy switch/item logic may run after player action parsing, so it must not
  read current-turn player switch intent.
- Revealed move tracking happens only after a move is visibly used.
- Boss AI does not read hidden player party slots, hidden party HP, unrevealed
  moves, unrevealed held items, private stat data, or future input.
- Boss trainers should bypass legacy move scoring or gate every unsafe legacy
  helper before it can run under `wBossAITier != 0`.
- Any exact-stat use is either battle resolution, ordinary AI, or explicitly
  documented as a known remaining boss-estimator risk.

Important files: `engine/battle/ai/boss.asm`, `engine/battle/ai/move.asm`,
`engine/battle/ai/scoring.asm`, `engine/battle/ai/items.asm`,
`engine/battle/ai/switch.asm`, `engine/battle/core.asm`,
`engine/battle/used_move_text.asm`, `engine/battle/read_trainer_attributes.asm`,
`ram/wram.asm`, `constants/battle_constants.asm`.

## Memory And Docs Safety

- Treat ROM0, WRAM0, WRAMX, and HRAM as scarce.
- For exact implementation facts, trust current source and linker outputs first,
  `docs/generated/dev_index.md` second, and hand-authored helper docs only after
  checking they still agree.
- Check `docs/generated/dev_index.md` before adding code/data to tight banks.
- Boss AI state must stay inside the reserved `140` byte block beginning at
  `wBossAITier`.
- `wBossAIStateEnd` must stay before `wEventFlags`.
- If linker outputs change, rebuild first and then regenerate
  `docs/generated/dev_index.md`.
- Never hand-edit `.gbc`, `.o`, `.map`, `.sym`, or generated index output.
- Report missing routes, stale helper docs, or broken doc references as doc gaps.

## Useful Verification Commands

Run what is relevant and available in the local environment:

```powershell
python tools\audit\check_docs_navigation.py
python tools\audit\check_release_smoke.py
python tools\audit\check_ai_tiers.py
python tools\audit\check_boss_ai_gating.py
python tools\audit\check_boss_ai_no_cheat.py
python tools\audit\check_boss_items_present.py
python tools\audit\check_boss_moves_complete.py
python tools\audit\check_battle_math_safety.py
python scripts\generate_dev_index.py --rom pokegold --out .local\out\dev_index_check.md
```

If `make` is unavailable but RGBDS tools are present, a narrow Gold rebuild may
still be possible by rebuilding touched objects and relinking with
`rgbds-1.0.1\rgbasm.exe`, `rgbds-1.0.1\rgblink.exe`,
`rgbds-1.0.1\rgbfix.exe`, and `tools\stadium.exe`. Prefer the repo `Makefile`
when available.

## Report Template

Use this structure for review output:

1. Findings, ordered by severity.
2. Open questions or assumptions.
3. Verification performed.
4. Residual risks or test gaps.
5. Documentation gaps discovered during the review.
