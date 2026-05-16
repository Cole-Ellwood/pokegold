# Plateau Diagnosis 001 - 2026-05-15

Purpose: diagnose why fresh unseen GSC replay top-match is not improving
reliably after the mastery-doc compression.

## Working Hypothesis

The main plateau is not missing notes or raw GSC facts. It is a live synthesis
failure: I recognize many individual lessons, but I do not consistently update
the public role/package ledger before ranking moves. When a move or entry
reveals that a Pokemon is a screener, Charm/Pursuit wall, Curse phazer,
spinner, trapper, cleric, RestTalker, lure, or pass receiver, the answer must
first reclassify that Pokemon's job and then solve the next owner. Recent bad
turns happened when I treated those reveals as side facts and kept ranking from
the visible matchup.

## Evidence

Recent measured replay evidence:

| Bucket | Top | Acceptable | Severe | Hidden | State | Mechanics |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Last 10 pre-simplified rows | 72/179 = 40.2% | 136/179 = 76.0% | 0 | 1 | 0 | 0 |
| Post-simplification 3 rows | 41/100 = 41.0% | 78/100 = 78.0% | 0 | 0 | 0 | 0 |

The simplified docs are not clearly making aggregate scores worse. They also
are not producing stable gains: `compressed_core_transfer_001` was strong
(17/30 top), `optimal_cards_transfer_001` returned to average (16/40 top), and
`counter_handoff_transfer_001` collapsed (8/30 top).

Repeated local miss classes:

- `optimal_cards_transfer_001`: missed second-order owner changes after the
  first handoff was obvious, especially Steelix/Zapdos/Cloyster ownership.
- `counter_handoff_transfer_001`: missed support-package identities after
  public reveals: Dragonite Reflect, Umbreon Charm/Pursuit, Skarmory Curse,
  Forretress/Starmie counter-handoffs.
- Older reviews already contain the same idea. `2026-05-13_smogtours-gen2ou-604744`
  says support is route delivery, receiver identity decides whether support is
  good, and support Pokemon should not be frozen into one role.
- `support_handoff_after_job.md` already says screens and drops are first-half
  route actions. The issue is retrieval/application during fresh move choice,
  not absence from the archive.

Current GSC sources support the same diagnosis:

- Smogon's GSC Spikes article treats Spikes as a route subgame with status,
  phazing, spin control, and repeated forced entries, not a standalone support
  move: https://www.smogon.com/gs/articles/gsc_spikes
- The GSC teambuilding compendium lists roles separately, including physical
  walls, special walls, mixed walls, Charm/Growl users, screeners, trappers,
  paralyzers, Toxic users, and Snorlax answers. The live decision must infer
  which role is public now, not just species: https://www.smogon.com/forums/threads/gsc-teambuilding-compendium.3547538/
- The GSC sample-team breakdown explicitly says defensive matchups change with
  HP, status, movesets, Explosion, and game state, and describes Skarmory
  Curse/Whirlwind and Cloyster Spin/Spikes compression as package roles:
  https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/
- Smogon's GSC intro identifies Umbreon Charm and Pursuit, Blissey screens and
  cleric support, and Skarmory Curse/Whirlwind as common role-defining tools:
  https://www.smogon.com/smog/issue28/gsc

## Hypotheses Checked

`Docs are too large`: partly fixed, not root. The compressed live docs reduced
context and kept safety clean. However, the live procedure still split one
decision concept across several cards.

`Docs are too small or missing knowledge`: partly false. The archive and old
reviews already contain the support-package lesson. The missing piece is a live
retrieval step that forces role reclassification before move ranking.

`Card structure is flawed`: likely true. Separate cards for re-score, owner,
branch punish, and reset loops let me satisfy each locally while missing the
integrated role update. The live core needs one explicit role/package ledger
step.

`Missing GSC game theory`: partially true, but not in an abstract way. The gap
is GSC-specific imperfect-information role inference: after a public reveal,
infer which team job is now public, what owner it enables, and how the opponent
will counter-handoff. General "predict switches" advice is too vague.

`No-Team-Preview discipline is the bottleneck`: not currently. Recent severe
and hidden-info errors stayed at zero. The problem is underusing public reveals,
not anchoring on hidden facts.

`Prompt or scoring artifact`: partial. Spectator-public exact top-match is a
hard oracle when hidden teammates matter, so acceptable-match remains important.
But many misses were after public moves revealed role information, so scoring
artifact is not the main explanation.

`Romhack mechanics uncertainty`: not this plateau. The recent failures are
vanilla GSC replay choices with zero mechanics errors.

`Model attention limit`: likely a contributor. Even small cards can fail when
the live procedure lacks a single mandatory ledger update. The fix should be a
smaller algorithm, not more archive context.

## Repair Made

Added `heuristic_core/role_package_ledger.md` and wired it into
`live_core.md`, `heuristic_core/README.md`, and `heuristic_core/migration_map.md`.

New live rule:

```text
Update the public role/package ledger before ranking moves.
```

This compresses the scattered lesson into one step:

1. What package is public now?
2. Which owner does it enable, deny, or invite?
3. Does the move beat that package route, or only the active target?

## Next Discriminating Test

Fresh unseen replay segment with an early support reveal. Stop after 20-30 side
decisions or after the same support-package miss repeats twice.

Required freeze sentence:

```text
Public package reveal: ___ means this Pokemon's job is now ___, so the next
owner is ___.
```

Success for this narrow repair requires:

- 0 severe/hidden/state/mechanics errors;
- acceptable-match at least 70%;
- top-match above the last support-reveal packet's 8/30 and preferably above
  the recent 40% baseline;
- branch-punish and route-conversion not falling;
- at least two public support reveals correctly changing the top-three ranking.

Do not claim broad progress from one pass. If the support-reveal test improves,
repeat on a different fresh replay before treating it as a stable fix.
