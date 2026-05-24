# Ditto Imposter Entry Scratchpad - 2026-05-24

Prompt: user fought a wild Ditto and expected the romhack's Imposter-style
mechanic to auto-Transform it. Check whether it can be safely implemented so
whenever Ditto enters battle it auto-transforms.

## Source Facts

- `engine/battle/ditto_imposter.asm::TryActivateDittoImposter` is already
  side-aware through `hBattleTurn`.
- The routine checks:
  - active HP is nonzero;
  - active species is `DITTO`;
  - the opponent-side transformed bit is not already set;
  - `CheckHiddenOpponent` is false.
- The routine then prints `DittoImposterActivatedText` and calls
  `BattleCommand_Transform`.
- `SpikesDamage` calls `TryActivateDittoImposter` after hazard processing.
- Player lead, player switches, enemy switches, Roar/Whirlwind-style enemy
  replacement, and Baton Pass player entry already reach `SpikesDamage`.
- Wild enemy lead setup skips enemy-side `SpikesDamage`; trainer enemy lead
  setup calls `EnemySwitch` before the player mon is sent out and does not call
  `SpikesDamage` afterward in the non-link path.

## Gap

Current source gives "auto-Transform on switch-in" but not reliably "auto-
Transform whenever Ditto enters battle."

The user-visible miss is wild Ditto as the initial enemy lead. The same lead-gap
appears possible for trainer enemy Ditto leads because the startup path loads
and sends the enemy lead before the player lead, without the usual enemy-turn
`SpikesDamage` call.

## Candidate Patch

Smallest coherent fix:

1. Add a local helper near battle-start setup in `engine/battle/core.asm`:
   `TryInitialEnemyDittoImposter`.
2. It should set enemy turn and call `TryActivateDittoImposter`.
3. Call it after the player's initial `SpikesDamage` at battle start, before
   `BattleTurn`.

Why after the player's initial entry:

- `BattleCommand_Transform` needs both active sides loaded.
- Wild enemy is already loaded before player entry, but Transform should wait
  until the player mon exists.
- Trainer enemy lead is also already loaded by then.
- Player lead Ditto still auto-transforms first because the existing player
  `SpikesDamage` hook runs before this new enemy-lead hook.

## Safety Notes

- Reuse existing Transform legality instead of duplicating Transform state.
- No RAM layout change.
- No new data table.
- ROM0 byte cost should be tiny: one `call`, one local label with
  `SetEnemyTurn`, `callfar TryActivateDittoImposter`, `ret`.
- Existing switches continue to use `SpikesDamage`; the new hook only fills
  initial enemy lead coverage.
- Link battle startup already has a separate enemy initial `SpikesDamage` path
  for player 2; avoid changing link behavior unless a test proves a gap.

## Verification Target

- Build `pokegold.gbc` and `pokesilver.gbc` through WSL command from
  `docs/build.md`.
- Regenerate `docs/generated/dev_index.md` if linker outputs move.
- Run `python tools\audit\check_docs_navigation.py` after generated index
  refresh.
- Run `git diff --check`.
- Runtime smoke would still be ideal: wild Ditto opening should print the
  Imposter text and then Transform text after the player mon appears.

## Implemented Shape

- Added `TryInitialEnemyDittoImposter` in `engine/battle/core.asm`.
- Normal non-link battle start now calls it after the player lead's
  `SpikesDamage`, so both active sides are loaded before Transform runs.
- The helper preserves `hBattleTurn` around the enemy-side Imposter call.
- Link startup paths are left on their existing `SpikesDamage` behavior.
