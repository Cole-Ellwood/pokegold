# Generated Balance Audit

Generated: 2026-05-09T09:42:27
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

| Score | Pokemon | Flags | BST | Base BST | BST Delta | Stats | Stat Delta | Types | Current Evos | Base Evos | Lv | TM | Best STAB | Best Move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | `DUNSPARCE` | `current-final`, `low-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 420 | 595 | -175 | 120/120/120/20/20/20 | HP-60, Atk-20, Def-10, Spe+5, SpA-45, SpD-45 | NORMAL/NORMAL | - | - | 6 | 29 | DOUBLE_EDGE (NORMAL 130bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 5 | `TOGETIC` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 465 | 575 | -110 | 55/40/85/40/140/105 | Atk-70, Spe-100, SpA+60 | NORMAL/FLYING | - | - | 8 | 31 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 5 | `QUAGSIRE` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 475 | 560 | -85 | 120/100/85/35/70/65 | HP-25, Atk-25, SpA-35 | WATER/GROUND | - | - | 6 | 31 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |

## Removed Evolutions

_No rows._

## Documented Gimmicks

| Score | Pokemon | Flags | BST | Base BST | BST Delta | Stats | Stat Delta | Types | Current Evos | Base Evos | Lv | TM | Best STAB | Best Move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | `DITTO` | `current-final`, `documented-gimmick` | 340 | 288 | 52 | 100/48/48/48/48/48 | HP+52 | NORMAL/NORMAL | - | - | 1 | 0 | - | - |
| 0 | `SMEARGLE` | `current-final`, `documented-gimmick` | 440 | 250 | 190 | 90/45/75/110/45/75 | HP+35, Atk+25, Def+40, Spe+35, SpA+25, SpD+30 | NORMAL/NORMAL | - | - | 10 | 0 | - | - |
| 0 | `UNOWN` | `current-final`, `documented-gimmick` | 496 | 496 | 0 | 148/102/48/48/102/48 | +0 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 1 | 0 | - | - |
| 0 | `WOBBUFFET` | `current-final`, `documented-gimmick` | 449 | 405 | 44 | 220/33/65/33/33/65 | HP+30, Def+7, SpD+7 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 4 | 0 | - | - |

## Current Standalone Or Final Species

| Score | Pokemon | Flags | BST | Base BST | BST Delta | Stats | Stat Delta | Types | Current Evos | Base Evos | Lv | TM | Best STAB | Best Move |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | `DUNSPARCE` | `current-final`, `low-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 420 | 595 | -175 | 120/120/120/20/20/20 | HP-60, Atk-20, Def-10, Spe+5, SpA-45, SpD-45 | NORMAL/NORMAL | - | - | 6 | 29 | DOUBLE_EDGE (NORMAL 130bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 5 | `TOGETIC` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 465 | 575 | -110 | 55/40/85/40/140/105 | Atk-70, Spe-100, SpA+60 | NORMAL/FLYING | - | - | 8 | 31 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 5 | `QUAGSIRE` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 475 | 560 | -85 | 120/100/85/35/70/65 | HP-25, Atk-25, SpA-35 | WATER/GROUND | - | - | 6 | 31 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 4 | `GLIGAR` | `current-final`, `low-and-unbuffed-vs-baseline`, `large-bst-regression-vs-baseline` | 490 | 590 | -100 | 85/95/125/85/35/65 | HP-40, Def-10, SpD-50 | GROUND/FLYING | - | - | 8 | 23 | WING_ATTACK (FLYING 80bp 100%) | IRON_TAIL (STEEL 130bp 75%) |
| 3 | `FARFETCH_D` | `current-final`, `low-bst-final` | 425 | 352 | 73 | 60/130/55/60/58/62 | HP+8, Atk+65 | NORMAL/FLYING | - | - | 8 | 22 | DOUBLE_EDGE (NORMAL 130bp 100%) | DOUBLE_EDGE (NORMAL 130bp 100%) |
| 3 | `DUGTRIO` | `current-final`, `low-bst-final` | 445 | 405 | 40 | 35/110/50/130/50/70 | Atk+30, Spe+10 | GROUND/GROUND | - | - | 10 | 21 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 3 | `ARIADOS` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline` | 460 | 485 | -25 | 110/90/100/40/60/60 | Atk-25 | BUG/POISON | - | - | 9 | 22 | SLUDGE_BOMB (POISON 90bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 3 | `HITMONLEE` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline` | 470 | 535 | -65 | 50/120/53/102/35/110 | Atk-30, Spe-35 | FIGHTING/FIGHTING | - | - | 11 | 20 | FOCUS_PUNCH (FIGHTING 150bp 100%) | FOCUS_PUNCH (FIGHTING 150bp 100%) |
| 3 | `YANMA` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline` | 480 | 495 | -15 | 85/110/60/95/50/80 | HP+20, Atk-15, Def+15, Spe-45, SpA-25, SpD+35 | BUG/FLYING | - | - | 8 | 20 | WING_ATTACK (FLYING 80bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 3 | `GIRAFARIG` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline` | 482 | 505 | -23 | 70/80/65/112/90/65 | HP+30, Atk-40, Spe+27, SpA-40 | NORMAL/PSYCHIC_TYPE | - | - | 10 | 25 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | EARTHQUAKE (GROUND 100bp 100%) |
| 3 | `STANTLER` | `current-final`, `watch-bst-final`, `low-and-unbuffed-vs-baseline` | 485 | 550 | -65 | 73/115/62/85/85/65 | HP-35, Atk-20, Def-20, Spe+25, SpD-15 | NORMAL/NORMAL | - | - | 6 | 23 | DOUBLE_EDGE (NORMAL 130bp 100%) | DOUBLE_EDGE (NORMAL 130bp 100%) |
| 2 | `HITMONTOP` | `current-final`, `large-bst-regression-vs-baseline` | 505 | 615 | -110 | 110/85/95/70/35/110 | HP+60, Atk-80, SpA-30, SpD-60 | FIGHTING/FIGHTING | - | - | 8 | 20 | FOCUS_PUNCH (FIGHTING 150bp 100%) | FOCUS_PUNCH (FIGHTING 150bp 100%) |
| 2 | `JUMPLUFF` | `current-final`, `large-bst-regression-vs-baseline` | 510 | 620 | -110 | 110/55/70/135/55/85 | HP+25, Atk-50, Spe-15, SpA-70 | GRASS/FLYING | - | - | 13 | 20 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 2 | `SLOWBRO` | `current-final`, `large-bst-regression-vs-baseline` | 510 | 690 | -180 | 115/75/110/30/100/80 | HP-20, Def-80, SpD-80 | WATER/PSYCHIC_TYPE | - | - | 12 | 34 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `HITMONCHAN` | `current-final`, `large-bst-regression-vs-baseline` | 514 | 595 | -81 | 50/80/79/75/120/110 | HP-20, Atk-45, Spe-1, SpA-15 | FIGHTING/FIGHTING | - | - | 10 | 23 | FOCUS_PUNCH (FIGHTING 150bp 100%) | FOCUS_PUNCH (FIGHTING 150bp 100%) |
| 2 | `AMPHAROS` | `current-final`, `large-bst-regression-vs-baseline` | 522 | 620 | -98 | 112/75/75/55/115/90 | HP-8, Def-30, SpA-30, SpD-30 | ELECTRIC/DRAGON | - | - | 12 | 26 | OUTRAGE (DRAGON 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `JYNX` | `current-final`, `large-bst-regression-vs-baseline` | 525 | 615 | -90 | 75/50/55/115/135/95 | HP+10, Atk-70, Def+20, Spe+20, SpA-10, SpD-60 | ICE/PSYCHIC_TYPE | - | - | 13 | 25 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `VILEPLUME` | `current-final`, `large-bst-regression-vs-baseline` | 525 | 775 | -250 | 120/80/85/50/100/90 | HP-30, Atk-50, Def-30, Spe-50, SpA-50, SpD-40 | GRASS/POISON | - | - | 8 | 20 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 2 | `MAGNETON` | `current-final`, `large-bst-regression-vs-baseline` | 540 | 655 | -115 | 80/100/110/80/120/50 | HP-10, Atk-60, Def-25, Spe+30, SpA-30, SpD-20 | ELECTRIC/STEEL | - | - | 12 | 17 | THUNDERBOLT (ELECTRIC 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `EXEGGUTOR` | `current-final`, `large-bst-regression-vs-baseline` | 545 | 670 | -125 | 105/95/85/55/125/80 | HP-20, Def-50, SpA-50, SpD-5 | GRASS/PSYCHIC_TYPE | - | - | 8 | 24 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 2 | `GENGAR` | `current-final`, `large-bst-regression-vs-baseline` | 555 | 650 | -95 | 60/130/60/100/130/75 | HP-50, Atk-5, Def-30, Spe-10 | GHOST/PSYCHIC_TYPE | - | - | 11 | 30 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `MEGANIUM` | `current-final`, `large-bst-regression-vs-baseline` | 555 | 645 | -90 | 110/82/100/80/83/100 | HP-5, Atk-6, Def-35, Spe-2, SpA-7, SpD-35 | GRASS/GRASS | - | - | 11 | 26 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 2 | `KINGDRA` | `current-final`, `large-bst-regression-vs-baseline` | 560 | 745 | -185 | 95/95/95/85/95/95 | HP-55, Atk-40, Def-40, Spe+20, SpA-30, SpD-40 | WATER/DRAGON | - | - | 11 | 22 | OUTRAGE (DRAGON 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `PILOSWINE` | `current-final`, `large-bst-regression-vs-baseline` | 560 | 690 | -130 | 140/100/120/50/60/90 | HP-40, Def-40, SpD-50 | ICE/GROUND | - | - | 8 | 23 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 2 | `MURKROW` | `current-final`, `large-bst-regression-vs-baseline` | 561 | 685 | -124 | 110/100/80/91/100/80 | HP-30, Atk-35, Def+38, Spe-100, SpA-35, SpD+38 | DARK/FLYING | - | - | 6 | 21 | WING_ATTACK (FLYING 80bp 100%) | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) |
| 2 | `DRAGONITE` | `current-final`, `large-bst-regression-vs-baseline` | 600 | 740 | -140 | 121/134/95/20/130/100 | HP-40, Atk-20, Def-30, SpA-10, SpD-40 | DRAGON/FLYING | - | - | 14 | 39 | OUTRAGE (DRAGON 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `AIPOM` | `current-final`, `watch-bst-final` | 450 | 360 | 90 | 90/100/55/110/40/55 | HP+35, Atk+30, Spe+25 | NORMAL/NORMAL | - | - | 8 | 31 | DOUBLE_EDGE (NORMAL 130bp 100%) | DOUBLE_EDGE (NORMAL 130bp 100%) |
| 1 | `RATICATE` | `current-final`, `watch-bst-final` | 452 | 447 | 5 | 55/120/60/97/50/70 | HP+30, Atk-25 | NORMAL/NORMAL | - | - | 8 | 29 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `LICKITUNG` | `current-final`, `watch-bst-final` | 455 | 385 | 70 | 125/55/80/30/60/105 | HP+35, Def+5, SpD+30 | NORMAL/NORMAL | - | - | 8 | 39 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `SEAKING` | `current-final`, `watch-bst-final` | 465 | 450 | 15 | 80/92/65/68/80/80 | SpA+15 | WATER/WATER | - | - | 10 | 18 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `SUNFLORA` | `current-final`, `watch-bst-final` | 470 | 425 | 45 | 75/75/55/30/150/85 | SpA+45 | GRASS/GRASS | - | - | 7 | 20 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 1 | `SKARMORY` | `current-final`, `watch-bst-final` | 475 | 465 | 10 | 75/80/140/70/40/70 | HP+10 | STEEL/FLYING | - | - | 7 | 20 | WING_ATTACK (FLYING 80bp 100%) | WING_ATTACK (FLYING 80bp 100%) |
| 1 | `BEEDRILL` | `current-final`, `watch-bst-final` | 480 | 385 | 95 | 75/120/40/120/45/80 | HP+10, Atk+40, Spe+45 | BUG/POISON | - | - | 7 | 21 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `PERSIAN` | `current-final`, `watch-bst-final` | 485 | 440 | 45 | 65/110/60/115/70/65 | Atk+40, SpA+5 | NORMAL/NORMAL | - | - | 8 | 25 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 1 | `SUDOWOODO` | `current-final`, `weak-reliable-stab` | 510 | 550 | -40 | 90/125/145/45/30/75 | HP-40, Atk-25, Spe+15, SpD+10 | ROCK/ROCK | - | - | 9 | 28 | ROCK_SLIDE (ROCK 75bp 90%) | FOCUS_PUNCH (FIGHTING 150bp 100%) |
| 1 | `UMBREON` | `current-final`, `weak-reliable-stab` | 550 | 615 | -65 | 120/65/110/65/60/130 | HP+5, Def-30, SpD-40 | DARK/DARK | - | - | 10 | 24 | FAINT_ATTACK (DARK 60bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `DITTO` | `current-final`, `documented-gimmick` | 340 | 288 | 52 | 100/48/48/48/48/48 | HP+52 | NORMAL/NORMAL | - | - | 1 | 0 | - | - |
| 0 | `SMEARGLE` | `current-final`, `documented-gimmick` | 440 | 250 | 190 | 90/45/75/110/45/75 | HP+35, Atk+25, Def+40, Spe+35, SpA+25, SpD+30 | NORMAL/NORMAL | - | - | 10 | 0 | - | - |
| 0 | `WOBBUFFET` | `current-final`, `documented-gimmick` | 449 | 405 | 44 | 220/33/65/33/33/65 | HP+30, Def+7, SpD+7 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 4 | 0 | - | - |
| 0 | `CLEFABLE` | `current-final` | 490 | 473 | 17 | 120/50/90/45/85/100 | HP+25, Atk-20, Def+17, Spe-15, SpD+10 | NORMAL/NORMAL | - | - | 9 | 34 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DELIBIRD` | `current-final` | 490 | 330 | 160 | 100/55/45/75/65/150 | HP+55, SpD+105 | ICE/FLYING | - | - | 8 | 20 | BLIZZARD (ICE 120bp 85%) | BLIZZARD (ICE 120bp 85%) |
| 0 | `MAGCARGO` | `current-final` | 490 | 410 | 80 | 80/80/120/30/100/80 | HP+30, Atk+30, SpA+20 | FIRE/ROCK | - | - | 10 | 21 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PARASECT` | `current-final` | 490 | 405 | 85 | 90/130/80/30/80/80 | HP+30, Atk+35, SpA+20 | BUG/GRASS | - | - | 10 | 25 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `FURRET` | `current-final` | 494 | 501 | -7 | 85/100/64/90/100/55 | HP-45, Atk-26, Def-16, Spe+50, SpA+55, SpD-25 | NORMAL/NORMAL | - | - | 9 | 31 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GRANBULL` | `current-final` | 495 | 450 | 45 | 90/120/120/45/60/60 | Def+45 | NORMAL/NORMAL | - | - | 10 | 32 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `UNOWN` | `current-final`, `documented-gimmick` | 496 | 496 | 0 | 148/102/48/48/102/48 | +0 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 1 | 0 | - | - |
| 0 | `BUTTERFREE` | `current-final` | 500 | 385 | 115 | 90/45/50/110/95/110 | HP+30, Spe+40, SpA+15, SpD+30 | BUG/FLYING | - | - | 9 | 21 | WING_ATTACK (FLYING 80bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DODRIO` | `current-final` | 500 | 460 | 40 | 80/110/70/120/60/60 | HP+20, Spe+20 | NORMAL/FLYING | - | - | 10 | 20 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `FORRETRESS` | `current-final` | 500 | 545 | -45 | 90/90/140/40/60/80 | HP-15, Atk-70, SpD+40 | BUG/STEEL | - | - | 9 | 24 | LEECH_LIFE (BUG 80bp 100%) | SELFDESTRUCT (NORMAL 200bp 100%) |
| 0 | `MILTANK` | `current-final` | 500 | 480 | 20 | 105/80/105/100/40/70 | HP-20, Atk-30, Def-30, Spe+60, SpD+40 | NORMAL/NORMAL | - | - | 9 | 37 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NOCTOWL` | `current-final` | 500 | 517 | -17 | 100/50/50/70/110/120 | HP+20, Spe-55, SpA-6, SpD+24 | NORMAL/FLYING | - | - | 11 | 21 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `FEAROW` | `current-final` | 505 | 442 | 63 | 110/130/65/100/50/50 | HP+45, Atk+40, SpA-11, SpD-11 | NORMAL/FLYING | - | - | 8 | 20 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `KINGLER` | `current-final` | 505 | 475 | 30 | 55/130/115/75/80/50 | SpA+30 | WATER/WATER | - | - | 10 | 25 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MAROWAK` | `current-final` | 505 | 425 | 80 | 100/120/110/45/50/80 | HP+40, Atk+40 | GROUND/GROUND | - | - | 14 | 30 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `AZUMARILL` | `current-final` | 510 | 410 | 100 | 100/150/80/50/50/80 | Atk+100 | WATER/WATER | - | - | 11 | 29 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `RHYDON` | `current-final` | 510 | 485 | 25 | 130/130/120/40/45/45 | HP+25 | GROUND/ROCK | - | - | 9 | 36 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SANDSLASH` | `current-final` | 510 | 450 | 60 | 105/110/130/65/45/55 | HP+30, Atk+10, Def+20 | GROUND/GROUND | - | - | 8 | 28 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SLOWKING` | `current-final` | 510 | 490 | 20 | 95/75/80/30/120/110 | SpA+20 | WATER/PSYCHIC_TYPE | - | - | 9 | 35 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TAUROS` | `current-final` | 510 | 490 | 20 | 75/120/95/110/40/70 | Atk+20 | NORMAL/NORMAL | - | - | 9 | 27 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ELECTABUZZ` | `current-final` | 512 | 490 | 22 | 65/105/57/105/95/85 | Atk+22 | ELECTRIC/FIGHTING | - | - | 9 | 29 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `OCTILLERY` | `current-final` | 515 | 480 | 35 | 75/105/75/80/105/75 | Spe+35 | WATER/WATER | - | - | 9 | 19 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `WIGGLYTUFF` | `current-final` | 515 | 425 | 90 | 160/100/55/45/75/80 | HP+20, Atk+30, Def+10, SpD+30 | NORMAL/NORMAL | - | - | 8 | 34 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `DONPHAN` | `current-final` | 520 | 500 | 20 | 110/120/120/50/60/60 | HP+20 | GROUND/GROUND | - | - | 8 | 25 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HERACROSS` | `current-final` | 520 | 500 | 20 | 80/125/75/105/40/95 | Spe+20 | BUG/FIGHTING | - | - | 9 | 23 | FOCUS_PUNCH (FIGHTING 150bp 100%) | FOCUS_PUNCH (FIGHTING 150bp 100%) |
| 0 | `KANGASKHAN` | `current-final` | 520 | 490 | 30 | 105/125/80/90/40/80 | Atk+30 | NORMAL/NORMAL | - | - | 9 | 37 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MISDREAVUS` | `current-final` | 520 | 435 | 85 | 80/120/80/85/70/85 | HP+20, Atk+60, Def+20, SpA-15 | GHOST/GHOST | - | - | 8 | 23 | SHADOW_BALL (GHOST 80bp 100%) | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) |
| 0 | `MR__MIME` | `current-final` | 520 | 460 | 60 | 40/45/65/90/100/180 | SpD+60 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 11 | 28 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `SCIZOR` | `current-final` | 520 | 500 | 20 | 70/130/120/65/55/80 | Def+20 | BUG/STEEL | - | - | 10 | 24 | LEECH_LIFE (BUG 80bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TANGELA` | `current-final` | 520 | 435 | 85 | 130/55/115/60/100/60 | HP+65, SpD+20 | GRASS/GRASS | - | - | 10 | 22 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `ARBOK` | `current-final` | 523 | 538 | -15 | 100/85/99/80/80/79 | HP-20, Def-10, SpA+15 | POISON/DARK | - | - | 10 | 21 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `BELLOSSOM` | `current-final` | 525 | 480 | 45 | 85/60/85/80/115/100 | HP+10, Atk-20, Spe+30, SpA+25 | GRASS/GRASS | - | - | 8 | 19 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `GOLDUCK` | `current-final` | 525 | 500 | 25 | 80/82/78/85/120/80 | SpA+25 | WATER/WATER | - | - | 11 | 29 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `KABUTOPS` | `current-final` | 525 | 495 | 30 | 60/125/115/90/65/70 | Atk+10, Def+10, Spe+10 | ROCK/WATER | - | - | 8 | 26 | SURF (WATER 95bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `OMASTAR` | `current-final` | 525 | 495 | 30 | 80/80/125/55/115/70 | HP+10, Atk+20 | ROCK/WATER | - | - | 10 | 23 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `STEELIX` | `current-final` | 525 | 600 | -75 | 100/100/200/30/55/40 | HP-35, Atk-35, SpD-5 | STEEL/DRAGON | - | - | 10 | 30 | OUTRAGE (DRAGON 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ELECTRODE` | `current-final` | 530 | 480 | 50 | 60/50/70/170/100/80 | Spe+30, SpA+20 | ELECTRIC/ELECTRIC | - | - | 13 | 18 | THUNDER (ELECTRIC 120bp 70%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `PINSIR` | `current-final` | 530 | 500 | 30 | 80/140/100/85/55/70 | HP+15, Atk+15 | BUG/BUG | - | - | 8 | 22 | LEECH_LIFE (BUG 80bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NINETALES` | `current-final` | 531 | 505 | 26 | 80/76/75/100/100/100 | HP+7, SpA+19 | FIRE/FIRE | - | - | 8 | 19 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PRIMEAPE` | `current-final` | 535 | 565 | -30 | 100/120/120/95/60/40 | HP-5, Atk-5, Def+60, Spe-50, SpD-30 | FIGHTING/FIGHTING | - | - | 9 | 28 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SNEASEL` | `current-final` | 535 | 605 | -70 | 95/115/55/120/75/75 | HP+70, Atk-40, Spe-40, SpA-60 | DARK/ICE | - | - | 9 | 30 | BLIZZARD (ICE 120bp 85%) | BLIZZARD (ICE 120bp 85%) |
| 0 | `WEEZING` | `current-final` | 535 | 600 | -65 | 110/90/120/60/85/70 | HP+5, Atk-30, SpA-40 | POISON/DARK | - | - | 11 | 20 | SLUDGE_BOMB (POISON 90bp 100%) | SELFDESTRUCT (NORMAL 200bp 100%) |
| 0 | `FLAREON` | `current-final` | 540 | 525 | 15 | 65/145/60/65/95/110 | Atk+15 | FIRE/FIRE | - | - | 10 | 22 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `JOLTEON` | `current-final` | 540 | 525 | 15 | 65/65/60/145/110/95 | Spe+15 | ELECTRIC/ELECTRIC | - | - | 10 | 23 | THUNDER (ELECTRIC 120bp 70%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `LEDIAN` | `current-final` | 540 | 530 | 10 | 90/115/65/105/45/120 | HP+20, Atk+15, Def+15, Spe-40, SpA-10, SpD+10 | BUG/FLYING | - | - | 12 | 28 | WING_ATTACK (FLYING 80bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `RAPIDASH` | `current-final` | 540 | 500 | 40 | 65/100/70/105/120/80 | SpA+40 | FIRE/FIRE | - | - | 13 | 17 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SNORLAX` | `current-final` | 540 | 540 | 0 | 160/110/65/30/65/110 | +0 | NORMAL/NORMAL | - | - | 10 | 38 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `VAPOREON` | `current-final` | 540 | 525 | 15 | 130/65/60/65/110/110 | SpD+15 | WATER/WATER | - | - | 10 | 25 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `LANTURN` | `current-final` | 544 | 600 | -56 | 125/58/76/75/105/105 | HP-20, Def-32, Spe+8, SpA-21, SpD+9 | WATER/ELECTRIC | - | - | 11 | 20 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `POLIWRATH` | `current-final` | 545 | 550 | -5 | 120/85/110/70/70/90 | HP-30, Def-35, Spe+20, SpD+40 | WATER/FIGHTING | - | - | 9 | 30 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `QWILFISH` | `current-final` | 545 | 545 | 0 | 85/105/130/95/65/65 | HP+20, Atk+10, Def-20, Spe+10, SpA-30, SpD+10 | WATER/POISON | - | - | 9 | 22 | HYDRO_PUMP (WATER 120bp 80%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `SHUCKLE` | `current-final` | 545 | 585 | -40 | 60/10/230/5/10/230 | HP-40 | BUG/ROCK | - | - | 7 | 25 | LEECH_LIFE (BUG 80bp 100%) | EARTHQUAKE (GROUND 100bp 100%) |
| 0 | `TENTACRUEL` | `current-final` | 545 | 515 | 30 | 80/80/65/100/100/120 | Atk+10, SpA+20 | WATER/POISON | - | - | 10 | 21 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `URSARING` | `current-final` | 545 | 570 | -25 | 120/145/75/55/75/75 | HP-10, Atk-15 | NORMAL/NORMAL | - | - | 11 | 33 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `AERODACTYL` | `current-final` | 550 | 555 | -5 | 100/105/80/130/60/75 | HP+20, Atk-40, Def+15 | ROCK/FLYING | - | - | 7 | 26 | WING_ATTACK (FLYING 80bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ESPEON` | `current-final` | 550 | 525 | 25 | 65/65/60/125/140/95 | Spe+15, SpA+10 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 10 | 24 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `VICTREEBEL` | `current-final` | 552 | 580 | -28 | 95/120/65/92/120/60 | HP+5, Atk-25, Def+15, Spe-18, SpA-20, SpD+15 | GRASS/POISON | - | - | 7 | 20 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `ALAKAZAM` | `current-final` | 555 | 490 | 65 | 60/50/45/120/150/130 | HP+5, SpA+15, SpD+45 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 9 | 27 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CLOYSTER` | `current-final` | 555 | 525 | 30 | 80/95/180/70/85/45 | HP+30 | WATER/ICE | - | - | 7 | 18 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CORSOLA` | `current-final` | 555 | 520 | 35 | 95/80/130/45/75/130 | HP+40, Atk-45, Def+45, Spe+10, SpA-60, SpD+45 | WATER/ROCK | - | - | 8 | 25 | SURF (WATER 95bp 100%) | EARTHQUAKE (GROUND 100bp 100%) |
| 0 | `FERALIGATR` | `current-final` | 555 | 613 | -58 | 85/105/100/87/95/83 | HP-3, Atk-22, Def-3, Spe+5, SpA-30, SpD-5 | WATER/FIGHTING | - | - | 10 | 32 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MANTINE` | `current-final` | 555 | 575 | -20 | 95/40/85/90/105/140 | HP-10, Atk-40, Def+15, Spe-10, SpA+25 | WATER/FLYING | - | - | 11 | 21 | HYDRO_PUMP (WATER 120bp 80%) | TAKE_DOWN (NORMAL 120bp 85%) |
| 0 | `POLITOED` | `current-final` | 555 | 500 | 55 | 100/70/80/85/115/105 | HP+10, Atk-5, Def+5, Spe+15, SpA+25, SpD+5 | WATER/WATER | - | - | 8 | 29 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TYPHLOSION` | `current-final` | 555 | 608 | -53 | 78/84/78/100/130/85 | Atk-8, Def-2, Spe-23, SpA-15, SpD-5 | FIRE/NORMAL | - | - | 10 | 31 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PIDGEOT` | `current-final` | 559 | 529 | 30 | 113/80/95/91/70/110 | Atk-30, Def+20, SpD+40 | NORMAL/FLYING | - | - | 12 | 19 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GOLEM` | `current-final` | 560 | 485 | 75 | 100/110/150/45/55/100 | HP+20, Def+20, SpD+35 | ROCK/GROUND | - | - | 12 | 29 | EARTHQUAKE (GROUND 100bp 100%) | EXPLOSION (NORMAL 250bp 100%) |
| 0 | `MUK` | `current-final` | 560 | 560 | 0 | 120/105/120/50/65/100 | HP-15, Atk-30, Def+45 | POISON/POISON | - | - | 10 | 25 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `DEWGONG` | `current-final` | 565 | 605 | -40 | 120/70/95/80/95/105 | HP-20, Atk-40, Def+15, Spe+10, SpA-15, SpD+10 | WATER/ICE | - | - | 11 | 20 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `HOUNDOOM` | `current-final` | 565 | 615 | -50 | 100/90/50/115/130/80 | HP-15, Spe+20, SpA-10, SpD-45 | DARK/FIRE | - | - | 8 | 26 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `HYPNO` | `current-final` | 565 | 483 | 82 | 115/85/120/57/73/115 | HP+30, Atk+12, Def+50, Spe-10 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 10 | 25 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NIDOKING` | `current-final` | 565 | 495 | 70 | 95/115/77/100/100/78 | HP+14, Atk+23, Spe+15, SpA+15, SpD+3 | POISON/GROUND | - | - | 9 | 38 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `NIDOQUEEN` | `current-final` | 565 | 495 | 70 | 130/85/100/75/75/100 | HP+40, Atk+3, Def+13, Spe-1, SpD+15 | POISON/GROUND | - | - | 8 | 38 | EARTHQUAKE (GROUND 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `PORYGON2` | `current-final` | 565 | 515 | 50 | 115/80/100/60/105/105 | HP+30, Def+10, SpD+10 | NORMAL/NORMAL | - | - | 10 | 24 | HYPER_BEAM (NORMAL 180bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `STARMIE` | `current-final` | 565 | 520 | 45 | 80/75/85/115/125/85 | HP+20, SpA+25 | WATER/PSYCHIC_TYPE | - | - | 9 | 24 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MAGMAR` | `current-final` | 567 | 495 | 72 | 120/95/60/82/125/85 | HP+55, Def+3, Spe-11, SpA+25 | FIRE/FIRE | - | - | 11 | 25 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `GYARADOS` | `current-final` | 575 | 630 | -55 | 100/125/79/81/90/100 | HP-25, Atk-20, SpA-10 | WATER/DRAGON | - | - | 9 | 31 | OUTRAGE (DRAGON 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `LAPRAS` | `current-final` | 580 | 535 | 45 | 130/85/110/60/85/110 | Def+30, SpD+15 | WATER/ICE | - | - | 11 | 28 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `RAICHU` | `current-final` | 590 | 475 | 115 | 80/110/55/110/125/110 | HP+20, Atk+20, Spe+10, SpA+35, SpD+30 | ELECTRIC/FIGHTING | - | - | 9 | 27 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MACHAMP` | `current-final` | 595 | 635 | -40 | 110/150/130/55/65/85 | HP-40, Atk+20, Def+20, SpD-40 | FIGHTING/FIGHTING | - | - | 10 | 27 | FOCUS_PUNCH (FIGHTING 150bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `BLISSEY` | `current-final` | 600 | 540 | 60 | 255/10/10/55/135/135 | SpA+60 | NORMAL/NORMAL | - | - | 11 | 34 | HYPER_BEAM (NORMAL 180bp 90%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `CELEBI` | `current-final` | 600 | 600 | 0 | 100/100/100/100/100/100 | +0 | PSYCHIC_TYPE/GRASS | - | - | 9 | 24 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `ENTEI` | `current-final` | 600 | 580 | 20 | 115/135/85/100/90/75 | Atk+20 | FIRE/FIRE | - | - | 9 | 26 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `MEW` | `current-final` | 600 | 600 | 0 | 100/100/100/100/100/100 | +0 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 6 | 52 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `RAIKOU` | `current-final` | 600 | 580 | 20 | 90/85/75/115/135/100 | SpA+20 | ELECTRIC/ELECTRIC | - | - | 9 | 26 | THUNDER (ELECTRIC 120bp 70%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `SUICUNE` | `current-final` | 600 | 580 | 20 | 120/75/115/85/90/115 | HP+20 | WATER/WATER | - | - | 9 | 27 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `VENOMOTH` | `current-final` | 600 | 550 | 50 | 110/80/60/100/100/150 | Atk+15, Spe-50, SpA+10, SpD+75 | BUG/POISON | - | - | 11 | 22 | SLUDGE_BOMB (POISON 90bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `CROBAT` | `current-final` | 605 | 605 | 0 | 100/120/105/130/70/80 | HP-45, Atk+60, Def+25, Spe-40 | POISON/FLYING | - | - | 9 | 20 | SLUDGE_BOMB (POISON 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ARTICUNO` | `current-final` | 610 | 580 | 30 | 100/95/100/85/105/125 | HP+10, Atk+10, SpA+10 | ICE/FLYING | - | - | 8 | 23 | BLIZZARD (ICE 120bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MOLTRES` | `current-final` | 610 | 580 | 30 | 100/110/90/90/135/85 | HP+10, Atk+10, SpA+10 | FIRE/FLYING | - | - | 8 | 22 | SKY_ATTACK (FLYING 140bp 90%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `XATU` | `current-final` | 610 | 545 | 65 | 110/75/70/150/115/90 | HP+45, Spe+55, SpA-25, SpD-10 | PSYCHIC_TYPE/FLYING | - | - | 8 | 22 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `ZAPDOS` | `current-final` | 610 | 580 | 30 | 100/100/85/100/135/90 | HP+10, Atk+10, SpA+10 | ELECTRIC/FLYING | - | - | 8 | 24 | DRILL_PECK (FLYING 110bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `ARCANINE` | `current-final` | 615 | 555 | 60 | 120/115/80/90/130/80 | HP+30, Atk+5, Spe-5, SpA+30 | FIRE/DRAGON | - | - | 10 | 23 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `VENUSAUR` | `current-final` | 615 | 525 | 90 | 95/97/98/95/115/115 | HP+15, Atk+15, Def+15, Spe+15, SpA+15, SpD+15 | GRASS/POISON | - | - | 14 | 24 | SOLARBEAM (GRASS 180bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `BLASTOISE` | `current-final` | 620 | 530 | 90 | 94/98/115/93/100/120 | HP+15, Atk+15, Def+15, Spe+15, SpA+15, SpD+15 | WATER/WATER | - | - | 14 | 33 | HYDRO_PUMP (WATER 120bp 80%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `CHARIZARD` | `current-final` | 624 | 614 | 10 | 93/99/93/115/124/100 | HP+15, Atk-25, Def+15, Spe+15, SpA-25, SpD+15 | FIRE/FLYING | - | - | 13 | 35 | FIRE_BLAST (FIRE 140bp 85%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `TYRANITAR` | `current-final` | 640 | 600 | 40 | 100/134/110/61/95/140 | SpD+40 | ROCK/DARK | - | - | 12 | 33 | CRUNCH (DARK 90bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
| 0 | `MEWTWO` | `current-final` | 680 | 680 | 0 | 106/110/90/130/154/90 | +0 | PSYCHIC_TYPE/PSYCHIC_TYPE | - | - | 11 | 33 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `HO_OH` | `current-final` | 740 | 680 | 60 | 116/140/100/100/120/164 | HP+10, Atk+10, Def+10, Spe+10, SpA+10, SpD+10 | FIRE/FLYING | - | - | 10 | 33 | FIRE_BLAST (FIRE 140bp 85%) | SOLARBEAM (GRASS 180bp 100%) |
| 0 | `LUGIA` | `current-final` | 740 | 680 | 60 | 116/100/140/120/100/164 | HP+10, Atk+10, Def+10, Spe+10, SpA+10, SpD+10 | PSYCHIC_TYPE/FLYING | - | - | 10 | 37 | DREAM_EATER (PSYCHIC_TYPE 100bp 100%) | HYPER_BEAM (NORMAL 180bp 90%) |
