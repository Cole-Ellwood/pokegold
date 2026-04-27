# Delibird Balance Evidence - 2026-04-26

Lane: weak-Pokemon usefulness.

## What Changed

Delibird was the best narrow target in the current medium-priority weak-Pokemon
queue because it already had buffed bulk but still had a one-move level-up kit:
`PRESENT` only. This pass did not touch Delibird's stats, type, encounter data,
TM/HM list, or trainer parties. It only changed the level-up move list and the
documentation that records the design intent.

Current Delibird level-up kit:

| Level | Move |
| --- | --- |
| 1 | `PRESENT` |
| 1 | `QUICK_ATTACK` |
| 12 | `ICY_WIND` |
| 20 | `AURORA_BEAM` |
| 27 | `AGILITY` |
| 31 | `WING_ATTACK` |
| 42 | `HAZE` |
| 52 | `BLIZZARD` |

Design intent: special-delivery Ice/Flying utility wall. It keeps the weird
Present identity, low physical offense, and late-midgame Silver availability,
but it now has real Ice STAB, a modest Flying STAB, speed control, and a late
utility move.

## Source Facts Checked

- `data/pokemon/base_stats/delibird.asm`: unchanged raw stats
  `100/55/45/75/65/150`, type `ICE, FLYING`, TM/HM list still includes
  `BLIZZARD`, `ICY_WIND`, and `FLY`.
- `data/pokemon/evos_attacks.asm`: Delibird no longer has a one-move learnset.
- `data/wild/johto_grass.asm`: Delibird appears in Johto grass tables at
  levels 22, 23, and 24.
- `data/trainers/parties.asm`: PokefanM Colin still has a level 32 Delibird
  holding `BERRY`.

Under standard default move generation, a level 22-24 wild Delibird should
arrive with the early kit online, and Colin's level 32 Delibird should showcase
the midgame kit rather than only `PRESENT`.

## Verification

Commands run from `C:\Users\lolno\Downloads\pokemon gold hack`:

```powershell
python scripts\generate_balance_audit.py
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_cheap_difficulty.py
git diff --check
```

Results:

- `generate_balance_audit.py` completed and refreshed
  `docs/generated/balance_audit.md`.
- Generated audit moved `DELIBIRD` from `thin-levelset` score 1 to score 0 with
  level-up count `8`.
- Release smoke passed.
- Docs navigation passed before and after the ROM build/dev-index refresh.
- Cheap difficulty audit passed: 43 target entries, 206 target mons, Johto Gym
  peak levels `11, 17, 21, 26, 32, 34, 33, 39`.
- `git diff --check` exited successfully; it printed CRLF normalization warnings
  for `audit/boss_ai_trace/morty_live.txt` and
  `docs/generated/balance_audit.md`, not whitespace errors.

Build command:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Result: passed. `pokegold.gbc` relinked and `pokesilver.gbc` was already up to
date. Because Gold relinked, this pass then ran:

```powershell
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
```

Result: `docs/generated/dev_index.md` refreshed, and docs navigation passed with
the generated dev index matching current linker outputs.

Note: the worktree already had unrelated dirty source changes before this pass.
The generated dev-index refresh records the current whole-linker state, so its
anchor/size shifts are not all Delibird-specific.

Final guard after writing notes:

```powershell
python tools\audit\check_navigation_floor.py
```

Result: passed.

## Remaining Uncertainty

- No emulator playtest was run for a Silver Ice Path catch at levels 22-24.
- No manual fight was run against PokefanM Colin's level 32 Delibird.
- Damage/feel still need human judgment: the moves now exist, but the intended
  question is whether Delibird feels like a surprising utility pick rather than
  a stat-inflated novelty.
