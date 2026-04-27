# Farfetch'd Balance Evidence - 2026-04-27

Lane: weak-Pokemon usefulness.

## What Changed

Farfetch'd was the selected follow-up from
`audit/forward_improvement_lane_2026-04-27.md`. The source question was narrow:
was it supposed to be a Stick-backed crit attacker, a plain early/midgame
Normal/Flying attacker, or an intentional joke? Current source had the outline
of the first answer but not the delivery. Farfetch'd had buffed Attack and the
unique Stick item, but wild held Stick was only in the rare 2 percent item slot,
and its level-up Flying STAB was still just Peck until the player reached Fly.

This pass makes the existing identity reachable without touching stats, typing,
encounters, TM/HM compatibility, or trainer parties:

| Surface | Before | After |
| --- | --- | --- |
| Wild held items | `NO_ITEM, STICK` | `STICK, STICK` |
| Level-up Flying STAB | `PECK` only | `WING_ATTACK` at level 23 |
| Stick item text | "An ordinary stick. Sell low." | Names Farfetch'd critical-ratio boost |

Design intent: Route 38 Farfetch'd is now a strange-but-real midgame crit bird.
It is still slow and fragile next to Fearow and Dodrio, but if the player notices
Stick and invests a few levels, Wing Attack, Swords Dance, and Slash give it a
real reason to exist.

## Source Facts Checked

- `data/pokemon/base_stats/farfetch_d.asm`: raw stats remain
  `60/130/55/60/58/62`, type remains `NORMAL, FLYING`, and TM/HM access still
  includes `CUT`, `FLY`, `STEEL_WING`, `HEADBUTT`, `RETURN`, and `IRON_TAIL`.
- `engine/battle/core.asm`: wild held-item chance is 75 percent no item, 23
  percent item1, 2 percent item2. Changing both Farfetch'd item slots to `STICK`
  makes Stick available on the normal 25 percent held-item roll instead of only
  the rare 2 percent slot.
- `engine/battle/effect_commands.asm`: `STICK` gives Farfetch'd +2 critical
  level. `data/battle/critical_hit_chances.asm` caps Stick plus high-crit Slash
  at a 1-in-2 critical chance, not a guaranteed crit.
- `data/pokemon/evos_attacks.asm`: Farfetch'd now learns Peck, Sand Attack,
  Leer, Fury Attack, Wing Attack, Swords Dance, Slash, and False Swipe.
- `data/wild/johto_grass.asm`: Farfetch'd appears at level 16 on Routes 38 and
  39 in morning/day slots.
- `data/trainers/parties.asm`: Bird Keeper Jose and Bird Keeper Perry use
  level 34-41 Farfetch'd through normal trainer move generation, so they inherit
  the new Wing Attack/Slash kit without party edits.

## Verification

Commands run from `C:\Users\lolno\Downloads\pokemon gold hack`:

```powershell
python scripts\generate_balance_audit.py
```

Result: completed and refreshed `docs/generated/balance_audit.md`. Farfetch'd
still appears as a low-BST final, which is true, but the generated row now shows
8 level-up moves and `WING_ATTACK` as best reliable STAB.

```powershell
python tools\audit\check_release_smoke.py
python tools\audit\check_docs_navigation.py
python tools\audit\check_cheap_difficulty.py
```

Results:

- Release smoke passed.
- Docs navigation passed with the generated balance audit matching source.
- Cheap difficulty audit passed: 43 target entries, 206 target mons, Johto Gym
  peak levels `11, 17, 21, 26, 32, 34, 33, 39`.

Build command:

```powershell
bash -lc 'cd "/mnt/c/Users/lolno/Downloads/pokemon gold hack" && make -j4 RGBASM=rgbds-1.0.1/rgbasm.exe RGBLINK=rgbds-1.0.1/rgblink.exe RGBFIX=rgbds-1.0.1/rgbfix.exe RGBGFX=rgbds-1.0.1/rgbgfx.exe pokegold.gbc pokesilver.gbc'
```

Result: passed. Both `pokegold.gbc` and `pokesilver.gbc` relinked. After the
build, this pass ran:

```powershell
python scripts\generate_dev_index.py --rom pokegold
python tools\audit\check_docs_navigation.py
git diff --check
```

Results: `docs/generated/dev_index.md` refreshed, docs navigation passed again,
and `git diff --check` exited successfully. It printed the existing CRLF
normalization warning for `docs/generated/balance_audit.md`, not a whitespace
error.

## Remaining Uncertainty

- No emulator playtest was run for catching Route 38/39 Farfetch'd and checking
  how often Stick is noticed naturally.
- No manual fight was run against Bird Keeper Jose or Bird Keeper Perry after
  the learnset change.
- The exact feel of Stick plus Slash is still a playtest question. The source
  now makes the role real; it does not prove the role is perfectly tuned.
