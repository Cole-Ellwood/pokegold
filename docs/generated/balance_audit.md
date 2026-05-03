# Generated Balance Audit

Generated: 2026-05-03T00:36:01
Baseline ref: `060d4accd7c0d01b1697ac97e7d7e2da72e3646b`

Do not hand-edit this file. Regenerate it with:

```powershell
python scripts\generate_balance_audit.py --baseline-ref 060d4accd7c0d01b1697ac97e7d7e2da72e3646b
```

## Scope

- Parses current `data/pokemon/base_stats/`, `data/pokemon/evos_attacks.asm`, `data/moves/moves.asm`, and Pokemon constants.
- Parses locked gimmick intent from `docs/balance_intent.md` for `documented-gimmick` demotion.
- Compares stats/evolutions against the baseline ref when that ref is available.
- Best move columns are power/accuracy heuristics only; they are not stat-weighted damage calculations.
- Best move columns ignore fixed-damage, OHKO, Hidden Power, Present, Counter, and Mirror Coat style effects.
- Scores are audit hints, not final balance judgments. Use `docs/balance_intent.md` and `docs/evolution_policy.md` for human intent.

## Flag Legend

- `removed-evolution`: baseline had an evolution rule and current source does not.
- `severe-low-bst-final`: current standalone/final, non-legendary, BST below 400.
- `low-bst-final`: current standalone/final, non-legendary, BST below 450.
- `watch-bst-final`: current standalone/final, non-legendary, BST below 490.
- `no-reliable-stab`: no standard damaging same-type move in direct level-up plus TM/HM learnset.
- `weak-reliable-stab`: best standard damaging same-type move has effective power below 70.
- `low-and-unbuffed-vs-baseline`: low current standalone/final and BST did not rise from baseline.
- `large-bst-regression-vs-baseline`: current BST is at least 80 lower than baseline ref.
- `documented-gimmick`: species has locked gimmick intent and is excluded from generic low-stat, TM, and STAB scoring.

## High-Signal Review Queue

_No rows._

## Removed Evolutions

_No rows._

## Documented Gimmicks

| Score | Pokemon | Flags | BST | Base BST | BST Delta | Stats | Stat Delta | Types | Current Evos | Base Evos | Lv | TM | Best STAB | Best Move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `DITTO` | `current-final`, `documented-gimmick` | 340 | n/a | n/a | 100/48/48/48/48/48 | n/a | NORMAL/NORMAL | - | - | 1 | 0 | - | - |
| 0 | `SMEARGLE` | `current-final`, `documented-gimmick` | 440 | n/a | n/a | 90/45/75/110/45/75 | n/a | NORMAL/NORMAL | - | - | 10 | 0 | - | - |
| 0 | `UNOWN` | `current-final`, `documented-gimmick` | 496 | n/a | n/a | 148/102/48/48/102/48 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 1 | 0 | - | - |
| 0 | `WOBBUFFET` | `current-final`, `documented-gimmick` | 449 | n/a | n/a | 220/33/65/33/33/65 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 4 | 0 | - | - |

## Current Standalone Or Final Species

| Score | Pokemon | Flags | BST | Base BST | BST Delta | Stats | Stat Delta | Types | Current Evos | Base Evos | Lv | TM | Best STAB | Best Move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `DUNSPARCE` | `current-final`, `low-bst-final` | 420 | n/a | n/a | 120/120/120/20/20/20 | n/a | NORMAL/NORMAL | - | - | 6 | 30 | DOUBLE_EDGE (NORMAL 130bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 3 | `FARFETCH_D` | `current-final`, `low-bst-final` | 425 | n/a | n/a | 60/130/55/60/58/62 | n/a | NORMAL/FLYING | - | - | 8 | 24 | WING_ATTACK (FLYING 80bp 100%) | IRON_TAIL (STEEL 130bp 75%) |
| 3 | `DUGTRIO` | `current-final`, `low-bst-final` | 445 | n/a | n/a | 35/110/50/130/50/70 | n/a | GROUND/GROUND | - | - | 10 | 22 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 3 | `BUTTERFREE` | `current-final`, `no-reliable-stab` | 500 | n/a | n/a | 90/45/50/110/95/110 | n/a | BUG/FLYING | - | - | 9 | 22 | - | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `AIPOM` | `current-final`, `watch-bst-final` | 450 | n/a | n/a | 90/100/55/110/40/55 | n/a | NORMAL/NORMAL | - | - | 8 | 34 | STRENGTH (NORMAL 80bp 100%) | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) |
| 1 | `GRANBULL` | `current-final`, `watch-bst-final` | 450 | n/a | n/a | 90/120/75/45/60/60 | n/a | NORMAL/NORMAL | - | - | 10 | 32 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `RATICATE` | `current-final`, `watch-bst-final` | 452 | n/a | n/a | 55/120/60/97/50/70 | n/a | NORMAL/NORMAL | - | - | 8 | 30 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `LICKITUNG` | `current-final`, `watch-bst-final` | 455 | n/a | n/a | 125/55/80/30/60/105 | n/a | NORMAL/NORMAL | - | - | 8 | 40 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `ARIADOS` | `current-final`, `watch-bst-final` | 460 | n/a | n/a | 110/90/100/40/60/60 | n/a | BUG/POISON | - | - | 9 | 22 | SLUDGE_BOMB (POISON 90bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `SEAKING` | `current-final`, `watch-bst-final` | 465 | n/a | n/a | 80/92/65/68/80/80 | n/a | WATER/WATER | - | - | 10 | 20 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `TOGETIC` | `current-final`, `watch-bst-final` | 465 | n/a | n/a | 55/40/85/40/140/105 | n/a | NORMAL/FLYING | - | - | 8 | 33 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `HITMONLEE` | `current-final`, `watch-bst-final` | 470 | n/a | n/a | 50/120/53/102/35/110 | n/a | FIGHTING/FIGHTING | - | - | 11 | 22 | HI_JUMP_KICK (FIGHTING 130bp 90%) | HI_JUMP_KICK (FIGHTING 130bp 90%) |
| 1 | `SUNFLORA` | `current-final`, `watch-bst-final` | 470 | n/a | n/a | 75/75/55/30/150/85 | n/a | GRASS/GRASS | - | - | 7 | 21 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `VENOMOTH` | `current-final`, `watch-bst-final` | 470 | n/a | n/a | 70/65/60/100/100/75 | n/a | BUG/POISON | - | - | 11 | 23 | SLUDGE_BOMB (POISON 90bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `QUAGSIRE` | `current-final`, `watch-bst-final` | 475 | n/a | n/a | 120/100/85/35/70/65 | n/a | WATER/GROUND | - | - | 6 | 31 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `SKARMORY` | `current-final`, `watch-bst-final` | 475 | n/a | n/a | 75/80/140/70/40/70 | n/a | STEEL/FLYING | - | - | 7 | 22 | FLY (FLYING 70bp 100%) | FLY (FLYING 70bp 100%) |
| 1 | `BEEDRILL` | `current-final`, `watch-bst-final` | 480 | n/a | n/a | 75/120/40/120/45/80 | n/a | BUG/POISON | - | - | 7 | 21 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `YANMA` | `current-final`, `watch-bst-final` | 480 | n/a | n/a | 85/110/60/95/50/80 | n/a | BUG/FLYING | - | - | 8 | 21 | WING_ATTACK (FLYING 80bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `GIRAFARIG` | `current-final`, `watch-bst-final` | 482 | n/a | n/a | 70/80/65/112/90/65 | n/a | NORMAL/PSYCHIC_TYPE | - | - | 10 | 29 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | EARTHQUAKE (GROUND 100bp 100%) |
| 1 | `PERSIAN` | `current-final`, `watch-bst-final` | 485 | n/a | n/a | 65/110/60/115/70/65 | n/a | NORMAL/NORMAL | - | - | 8 | 30 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `STANTLER` | `current-final`, `watch-bst-final` | 485 | n/a | n/a | 73/115/62/85/85/65 | n/a | NORMAL/NORMAL | - | - | 6 | 27 | DOUBLE_EDGE (NORMAL 130bp 100%) | DOUBLE_EDGE (NORMAL 130bp 100%) |
| 1 | `HITMONTOP` | `current-final`, `weak-reliable-stab` | 505 | n/a | n/a | 110/85/95/70/35/110 | n/a | FIGHTING/FIGHTING | - | - | 8 | 22 | ROLLING_KICK (FIGHTING 60bp 85%) | STRENGTH (NORMAL 80bp 100%) |
| 1 | `SUDOWOODO` | `current-final`, `weak-reliable-stab` | 510 | n/a | n/a | 90/125/145/45/30/75 | n/a | ROCK/ROCK | - | - | 9 | 29 | ROCK_SLIDE (ROCK 75bp 90%) | EARTHQUAKE (GROUND 100bp 100%) |
| 1 | `HITMONCHAN` | `current-final`, `weak-reliable-stab` | 514 | n/a | n/a | 50/80/79/75/120/110 | n/a | FIGHTING/FIGHTING | - | - | 10 | 25 | DYNAMICPUNCH (FIGHTING 100bp 50%) | MEGA_PUNCH (NORMAL 100bp 85%) |
| 1 | `SCIZOR` | `current-final`, `weak-reliable-stab` | 520 | n/a | n/a | 70/130/120/65/55/80 | n/a | BUG/STEEL | - | - | 10 | 25 | STEEL_WING (STEEL 70bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `SHUCKLE` | `current-final`, `weak-reliable-stab` | 545 | n/a | n/a | 60/10/230/5/10/230 | n/a | BUG/ROCK | - | - | 7 | 25 | ROLLOUT (ROCK 30bp 90%) | EARTHQUAKE (GROUND 100bp 100%) |
| 1 | `UMBREON` | `current-final`, `weak-reliable-stab` | 550 | n/a | n/a | 120/65/110/65/60/130 | n/a | DARK/DARK | - | - | 10 | 29 | FAINT_ATTACK (DARK 60bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `DITTO` | `current-final`, `documented-gimmick` | 340 | n/a | n/a | 100/48/48/48/48/48 | n/a | NORMAL/NORMAL | - | - | 1 | 0 | - | - |
| 0 | `SMEARGLE` | `current-final`, `documented-gimmick` | 440 | n/a | n/a | 90/45/75/110/45/75 | n/a | NORMAL/NORMAL | - | - | 10 | 0 | - | - |
| 0 | `WOBBUFFET` | `current-final`, `documented-gimmick` | 449 | n/a | n/a | 220/33/65/33/33/65 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 4 | 0 | - | - |
| 0 | `CLEFABLE` | `current-final` | 490 | n/a | n/a | 120/50/90/45/85/100 | n/a | NORMAL/NORMAL | - | - | 9 | 38 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DELIBIRD` | `current-final` | 490 | n/a | n/a | 100/55/45/75/65/150 | n/a | ICE/FLYING | - | - | 8 | 22 | BLIZZARD (ICE 120bp 85%) | BLIZZARD (ICE 120bp 85%) |
| 0 | `GLIGAR` | `current-final` | 490 | n/a | n/a | 85/95/125/85/35/65 | n/a | GROUND/FLYING | - | - | 8 | 25 | WING_ATTACK (FLYING 80bp 100%) | IRON_TAIL (STEEL 130bp 75%) |
| 0 | `MAGCARGO` | `current-final` | 490 | n/a | n/a | 80/80/120/30/100/80 | n/a | FIRE/ROCK | - | - | 10 | 22 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PARASECT` | `current-final` | 490 | n/a | n/a | 90/130/80/30/80/80 | n/a | BUG/GRASS | - | - | 10 | 25 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `FURRET` | `current-final` | 494 | n/a | n/a | 85/100/64/90/100/55 | n/a | NORMAL/NORMAL | - | - | 9 | 33 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `UNOWN` | `current-final`, `documented-gimmick` | 496 | n/a | n/a | 148/102/48/48/102/48 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 1 | 0 | - | - |
| 0 | `BELLOSSOM` | `current-final` | 500 | n/a | n/a | 85/80/85/60/90/100 | n/a | GRASS/GRASS | - | - | 8 | 20 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DODRIO` | `current-final` | 500 | n/a | n/a | 80/110/70/120/60/60 | n/a | NORMAL/FLYING | - | - | 10 | 20 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `FORRETRESS` | `current-final` | 500 | n/a | n/a | 90/90/140/40/60/80 | n/a | BUG/STEEL | - | - | 9 | 24 | IRON_HEAD (STEEL 80bp 100%) | SELFDESTRUCT (NORMAL 200bp 100%) |
| 0 | `MILTANK` | `current-final` | 500 | n/a | n/a | 105/80/105/100/40/70 | n/a | NORMAL/NORMAL | - | - | 9 | 37 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NOCTOWL` | `current-final` | 500 | n/a | n/a | 100/50/50/70/110/120 | n/a | NORMAL/FLYING | - | - | 11 | 24 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `RAPIDASH` | `current-final` | 500 | n/a | n/a | 65/100/70/105/80/80 | n/a | FIRE/FIRE | - | - | 13 | 19 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `FEAROW` | `current-final` | 505 | n/a | n/a | 110/130/65/100/50/50 | n/a | NORMAL/FLYING | - | - | 8 | 21 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `KINGLER` | `current-final` | 505 | n/a | n/a | 55/130/115/75/80/50 | n/a | WATER/WATER | - | - | 10 | 25 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MAROWAK` | `current-final` | 505 | n/a | n/a | 100/120/110/45/50/80 | n/a | GROUND/GROUND | - | - | 14 | 31 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MAGMAR` | `current-final` | 509 | n/a | n/a | 65/95/57/82/125/85 | n/a | FIRE/FIRE | - | - | 11 | 27 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ALAKAZAM` | `current-final` | 510 | n/a | n/a | 60/50/45/120/135/100 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 9 | 30 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `AZUMARILL` | `current-final` | 510 | n/a | n/a | 100/150/80/50/50/80 | n/a | WATER/WATER | - | - | 11 | 30 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `JUMPLUFF` | `current-final` | 510 | n/a | n/a | 110/55/70/135/55/85 | n/a | GRASS/FLYING | - | - | 13 | 21 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `RHYDON` | `current-final` | 510 | n/a | n/a | 130/130/120/40/45/45 | n/a | GROUND/ROCK | - | - | 9 | 35 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SANDSLASH` | `current-final` | 510 | n/a | n/a | 105/110/130/65/45/55 | n/a | GROUND/GROUND | - | - | 8 | 31 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SLOWBRO` | `current-final` | 510 | n/a | n/a | 115/75/110/30/100/80 | n/a | WATER/PSYCHIC_TYPE | - | - | 12 | 38 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SLOWKING` | `current-final` | 510 | n/a | n/a | 95/75/80/30/120/110 | n/a | WATER/PSYCHIC_TYPE | - | - | 9 | 39 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TAUROS` | `current-final` | 510 | n/a | n/a | 75/120/95/110/40/70 | n/a | NORMAL/NORMAL | - | - | 9 | 26 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ELECTABUZZ` | `current-final` | 512 | n/a | n/a | 65/105/57/105/95/85 | n/a | ELECTRIC/FIGHTING | - | - | 9 | 31 | SUBMISSION (FIGHTING 110bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `AERODACTYL` | `current-final` | 515 | n/a | n/a | 80/105/65/130/60/75 | n/a | ROCK/FLYING | - | - | 7 | 27 | WING_ATTACK (FLYING 80bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `OCTILLERY` | `current-final` | 515 | n/a | n/a | 75/105/75/80/105/75 | n/a | WATER/WATER | - | - | 9 | 21 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `WIGGLYTUFF` | `current-final` | 515 | n/a | n/a | 160/100/55/45/75/80 | n/a | NORMAL/NORMAL | - | - | 8 | 37 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DONPHAN` | `current-final` | 520 | n/a | n/a | 110/120/120/50/60/60 | n/a | GROUND/GROUND | - | - | 8 | 24 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HERACROSS` | `current-final` | 520 | n/a | n/a | 80/125/75/105/40/95 | n/a | BUG/FIGHTING | - | - | 9 | 22 | MEGAHORN (BUG 120bp 85%) | TAKE_DOWN (NORMAL 120bp 85%) |
| 0 | `KANGASKHAN` | `current-final` | 520 | n/a | n/a | 105/125/80/90/40/80 | n/a | NORMAL/NORMAL | - | - | 9 | 36 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MISDREAVUS` | `current-final` | 520 | n/a | n/a | 80/120/80/85/70/85 | n/a | GHOST/GHOST | - | - | 8 | 27 | SHADOW_BALL (GHOST 80bp 100%) | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) |
| 0 | `MR__MIME` | `current-final` | 520 | n/a | n/a | 40/45/65/90/100/180 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 11 | 31 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `TANGELA` | `current-final` | 520 | n/a | n/a | 130/55/115/60/100/60 | n/a | GRASS/GRASS | - | - | 10 | 24 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `AMPHAROS` | `current-final` | 522 | n/a | n/a | 112/75/75/55/115/90 | n/a | ELECTRIC/DRAGON | - | - | 12 | 27 | OUTRAGE (DRAGON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ARBOK` | `current-final` | 523 | n/a | n/a | 100/85/99/80/80/79 | n/a | POISON/DARK | - | - | 10 | 22 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GOLDUCK` | `current-final` | 525 | n/a | n/a | 80/82/78/85/120/80 | n/a | WATER/WATER | - | - | 11 | 32 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GOLEM` | `current-final` | 525 | n/a | n/a | 100/110/150/45/55/65 | n/a | ROCK/GROUND | - | - | 12 | 29 | EARTHQUAKE (GROUND 100bp 100%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `JYNX` | `current-final` | 525 | n/a | n/a | 75/50/55/115/135/95 | n/a | ICE/PSYCHIC_TYPE | - | - | 13 | 28 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `KABUTOPS` | `current-final` | 525 | n/a | n/a | 60/125/115/90/65/70 | n/a | ROCK/WATER | - | - | 8 | 27 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MACHAMP` | `current-final` | 525 | n/a | n/a | 110/130/80/55/65/85 | n/a | FIGHTING/FIGHTING | - | - | 10 | 28 | CROSS_CHOP (FIGHTING 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `OMASTAR` | `current-final` | 525 | n/a | n/a | 80/80/125/55/115/70 | n/a | ROCK/WATER | - | - | 10 | 24 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `STEELIX` | `current-final` | 525 | n/a | n/a | 100/100/200/30/55/40 | n/a | STEEL/GROUND | - | - | 9 | 28 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `VENUSAUR` | `current-final` | 525 | n/a | n/a | 80/82/83/80/100/100 | n/a | GRASS/POISON | - | - | 14 | 25 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `VILEPLUME` | `current-final` | 525 | n/a | n/a | 120/80/85/50/100/90 | n/a | GRASS/POISON | - | - | 8 | 21 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `BLASTOISE` | `current-final` | 530 | n/a | n/a | 79/83/100/78/85/105 | n/a | WATER/WATER | - | - | 14 | 32 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ELECTRODE` | `current-final` | 530 | n/a | n/a | 60/50/70/170/100/80 | n/a | ELECTRIC/ELECTRIC | - | - | 13 | 20 | THUNDER (ELECTRIC 120bp 70%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `PINSIR` | `current-final` | 530 | n/a | n/a | 80/140/100/85/55/70 | n/a | BUG/BUG | - | - | 8 | 21 | LEECH_LIFE (BUG 80bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `STARMIE` | `current-final` | 530 | n/a | n/a | 60/75/85/115/110/85 | n/a | WATER/PSYCHIC_TYPE | - | - | 9 | 28 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `VICTREEBEL` | `current-final` | 530 | n/a | n/a | 95/120/65/70/120/60 | n/a | GRASS/POISON | - | - | 7 | 21 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `NINETALES` | `current-final` | 531 | n/a | n/a | 80/76/75/100/100/100 | n/a | FIRE/FIRE | - | - | 8 | 21 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HYPNO` | `current-final` | 533 | n/a | n/a | 85/73/120/67/73/115 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 10 | 28 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CHARIZARD` | `current-final` | 534 | n/a | n/a | 78/84/78/100/109/85 | n/a | FIRE/FLYING | - | - | 13 | 34 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PRIMEAPE` | `current-final` | 535 | n/a | n/a | 100/120/120/95/60/40 | n/a | FIGHTING/FIGHTING | - | - | 9 | 31 | CROSS_CHOP (FIGHTING 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SNEASEL` | `current-final` | 535 | n/a | n/a | 95/115/55/120/75/75 | n/a | DARK/ICE | - | - | 9 | 35 | BLIZZARD (ICE 120bp 85%) | BLIZZARD (ICE 120bp 85%) |
| 0 | `WEEZING` | `current-final` | 535 | n/a | n/a | 110/90/120/60/85/70 | n/a | POISON/DARK | - | - | 11 | 21 | SLUDGE_BOMB (POISON 90bp 100%) | SELFDESTRUCT (NORMAL 200bp 100%) |
| 0 | `FLAREON` | `current-final` | 540 | n/a | n/a | 65/145/60/65/95/110 | n/a | FIRE/FIRE | - | - | 10 | 25 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HOUNDOOM` | `current-final` | 540 | n/a | n/a | 75/90/50/115/130/80 | n/a | DARK/FIRE | - | - | 8 | 30 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `JOLTEON` | `current-final` | 540 | n/a | n/a | 65/65/60/145/110/95 | n/a | ELECTRIC/ELECTRIC | - | - | 10 | 26 | THUNDER (ELECTRIC 120bp 70%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `LEDIAN` | `current-final` | 540 | n/a | n/a | 90/115/65/105/45/120 | n/a | BUG/FLYING | - | - | 12 | 27 | WING_ATTACK (FLYING 80bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `MAGNETON` | `current-final` | 540 | n/a | n/a | 80/100/110/80/120/50 | n/a | ELECTRIC/STEEL | - | - | 12 | 19 | THUNDERBOLT (ELECTRIC 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SNORLAX` | `current-final` | 540 | n/a | n/a | 160/110/65/30/65/110 | n/a | NORMAL/NORMAL | - | - | 10 | 38 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `VAPOREON` | `current-final` | 540 | n/a | n/a | 130/65/60/65/110/110 | n/a | WATER/WATER | - | - | 10 | 28 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `LANTURN` | `current-final` | 544 | n/a | n/a | 125/58/76/75/105/105 | n/a | WATER/ELECTRIC | - | - | 11 | 21 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `EXEGGUTOR` | `current-final` | 545 | n/a | n/a | 105/95/85/55/125/80 | n/a | GRASS/PSYCHIC_TYPE | - | - | 8 | 27 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `POLIWRATH` | `current-final` | 545 | n/a | n/a | 120/85/110/70/70/90 | n/a | WATER/FIGHTING | - | - | 9 | 31 | SUBMISSION (FIGHTING 110bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `QWILFISH` | `current-final` | 545 | n/a | n/a | 85/105/130/95/65/65 | n/a | WATER/POISON | - | - | 9 | 24 | HYDRO_PUMP (WATER 120bp 80%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `TENTACRUEL` | `current-final` | 545 | n/a | n/a | 80/80/65/100/100/120 | n/a | WATER/POISON | - | - | 10 | 22 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `URSARING` | `current-final` | 545 | n/a | n/a | 120/145/75/55/75/75 | n/a | NORMAL/NORMAL | - | - | 11 | 33 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CROBAT` | `current-final` | 550 | n/a | n/a | 100/90/80/130/70/80 | n/a | POISON/FLYING | - | - | 9 | 21 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ESPEON` | `current-final` | 550 | n/a | n/a | 65/65/60/125/140/95 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 10 | 29 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `XATU` | `current-final` | 550 | n/a | n/a | 90/75/70/150/95/70 | n/a | PSYCHIC_TYPE/FLYING | - | - | 8 | 26 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `CLOYSTER` | `current-final` | 555 | n/a | n/a | 80/95/180/70/85/45 | n/a | WATER/ICE | - | - | 7 | 20 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CORSOLA` | `current-final` | 555 | n/a | n/a | 95/80/130/45/75/130 | n/a | WATER/ROCK | - | - | 8 | 26 | SURF (WATER 95bp 100%) | EARTHQUAKE (GROUND 100bp 100%) |
| 0 | `FERALIGATR` | `current-final` | 555 | n/a | n/a | 85/105/100/87/95/83 | n/a | WATER/FIGHTING | - | - | 10 | 32 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GENGAR` | `current-final` | 555 | n/a | n/a | 60/130/60/100/130/75 | n/a | GHOST/PSYCHIC_TYPE | - | - | 11 | 32 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MANTINE` | `current-final` | 555 | n/a | n/a | 95/40/85/90/105/140 | n/a | WATER/FLYING | - | - | 11 | 22 | HYDRO_PUMP (WATER 120bp 80%) | TAKE_DOWN (NORMAL 120bp 85%) |
| 0 | `MEGANIUM` | `current-final` | 555 | n/a | n/a | 110/82/100/80/83/100 | n/a | GRASS/GRASS | - | - | 11 | 28 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `POLITOED` | `current-final` | 555 | n/a | n/a | 100/70/80/85/115/105 | n/a | WATER/WATER | - | - | 8 | 31 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TYPHLOSION` | `current-final` | 555 | n/a | n/a | 78/84/78/100/130/85 | n/a | FIRE/NORMAL | - | - | 10 | 33 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PIDGEOT` | `current-final` | 559 | n/a | n/a | 113/80/95/91/70/110 | n/a | NORMAL/FLYING | - | - | 12 | 21 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `KINGDRA` | `current-final` | 560 | n/a | n/a | 95/95/95/85/95/95 | n/a | WATER/DRAGON | - | - | 11 | 23 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MUK` | `current-final` | 560 | n/a | n/a | 120/105/120/50/65/100 | n/a | POISON/POISON | - | - | 10 | 26 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PILOSWINE` | `current-final` | 560 | n/a | n/a | 140/100/120/50/60/90 | n/a | ICE/GROUND | - | - | 8 | 25 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `RAICHU` | `current-final` | 560 | n/a | n/a | 80/110/55/110/125/80 | n/a | ELECTRIC/FIGHTING | - | - | 9 | 29 | SUBMISSION (FIGHTING 110bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MURKROW` | `current-final` | 561 | n/a | n/a | 110/100/80/91/100/80 | n/a | DARK/FLYING | - | - | 6 | 25 | WING_ATTACK (FLYING 80bp 100%) | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) |
| 0 | `DEWGONG` | `current-final` | 565 | n/a | n/a | 120/70/95/80/95/105 | n/a | WATER/ICE | - | - | 11 | 21 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NIDOKING` | `current-final` | 565 | n/a | n/a | 95/115/77/100/100/78 | n/a | POISON/GROUND | - | - | 9 | 38 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NIDOQUEEN` | `current-final` | 565 | n/a | n/a | 130/85/100/75/75/100 | n/a | POISON/GROUND | - | - | 8 | 38 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PORYGON2` | `current-final` | 565 | n/a | n/a | 115/80/100/60/105/105 | n/a | NORMAL/NORMAL | - | - | 10 | 28 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GYARADOS` | `current-final` | 575 | n/a | n/a | 100/125/79/81/90/100 | n/a | WATER/DRAGON | - | - | 9 | 29 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ARTICUNO` | `current-final` | 580 | n/a | n/a | 90/85/100/85/95/125 | n/a | ICE/FLYING | - | - | 8 | 25 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ENTEI` | `current-final` | 580 | n/a | n/a | 115/115/85/100/90/75 | n/a | FIRE/FIRE | - | - | 9 | 30 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `LAPRAS` | `current-final` | 580 | n/a | n/a | 130/85/110/60/85/110 | n/a | WATER/ICE | - | - | 11 | 29 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MOLTRES` | `current-final` | 580 | n/a | n/a | 90/100/90/90/125/85 | n/a | FIRE/FLYING | - | - | 8 | 24 | SKY_ATTACK (FLYING 140bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `RAIKOU` | `current-final` | 580 | n/a | n/a | 90/85/75/115/115/100 | n/a | ELECTRIC/ELECTRIC | - | - | 9 | 30 | THUNDER (ELECTRIC 120bp 70%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SUICUNE` | `current-final` | 580 | n/a | n/a | 100/75/115/85/90/115 | n/a | WATER/WATER | - | - | 9 | 31 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ZAPDOS` | `current-final` | 580 | n/a | n/a | 90/90/85/100/125/90 | n/a | ELECTRIC/FLYING | - | - | 8 | 26 | DRILL_PECK (FLYING 110bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `BLISSEY` | `current-final` | 600 | n/a | n/a | 255/10/10/55/135/135 | n/a | NORMAL/NORMAL | - | - | 11 | 34 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `CELEBI` | `current-final` | 600 | n/a | n/a | 100/100/100/100/100/100 | n/a | PSYCHIC_TYPE/GRASS | - | - | 9 | 29 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DRAGONITE` | `current-final` | 600 | n/a | n/a | 121/134/95/20/130/100 | n/a | DRAGON/FLYING | - | - | 14 | 39 | OUTRAGE (DRAGON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MEW` | `current-final` | 600 | n/a | n/a | 100/100/100/100/100/100 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 6 | 57 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `TYRANITAR` | `current-final` | 600 | n/a | n/a | 100/134/110/61/95/100 | n/a | ROCK/DARK | - | - | 12 | 34 | CRUNCH (DARK 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ARCANINE` | `current-final` | 615 | n/a | n/a | 120/115/80/90/130/80 | n/a | FIRE/DRAGON | - | - | 10 | 23 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HO_OH` | `current-final` | 680 | n/a | n/a | 106/130/90/90/110/154 | n/a | FIRE/FLYING | - | - | 10 | 37 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `LUGIA` | `current-final` | 680 | n/a | n/a | 106/90/130/110/90/154 | n/a | PSYCHIC_TYPE/FLYING | - | - | 10 | 41 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MEWTWO` | `current-final` | 680 | n/a | n/a | 106/110/90/130/154/90 | n/a | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 11 | 38 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
