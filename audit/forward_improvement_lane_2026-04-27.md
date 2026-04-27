# Forward Improvement Lane - 2026-04-27

Scope: `TODO-004` in `docs/project_completion_todo.md`.

Chosen lane: `FARFETCH_D`.

No Pokemon source was edited for this choice. This file is the pre-source
decision record required before any lane implementation starts.

## Why This Lane

`FARFETCH_D` is the best next move because it is the most contained unresolved
balance problem with the clearest source question.

Current docs say:

- `docs/project_roadmap.md` says the broader weak-Pokemon queue still has
  `FARFETCH_D`, `ARIADOS`, and `YANMA`, and the next queue work should pick
  exactly one.
- `docs/buff_backlog.md` says `FARFETCH_D` has buffed Attack, but reliable STAB
  is still modest for a standalone final, with likely fixes of confirming Stick
  availability or improving Flying/Normal access.
- `docs/generated/balance_audit.md` flags `FARFETCH_D` as `current-final` and
  `low-bst-final` at 425 BST.
- `docs/balance_intent.md` has no current intent row locking `FARFETCH_D` as an
  intentional gimmick or resolved role.

That makes the actual requirement small and honest: decide whether Farfetch'd is
supposed to be a Stick-backed crit attacker, a clean early/midgame physical
Flying/Normal pick, or an intentionally narrow oddball. Then make source and
docs match that answer.

## Why Not The Others

`ARIADOS` is real work, but less sharp. The backlog says it may be bulky status
utility or may need a stronger Bug/Poison identity. That first requires a role
decision.

`YANMA` is suspicious, but its current 480 BST makes it less urgent than a
425-BST standalone final. It may only need move timing or STAB quality review.

Morty-only gym scout dossier is the most interesting systems lane, but choosing
it would immediately open `TODO-005`. That is too much scope for this pass after
closing proof and feel gaps.

## Implementation Boundary For The Next Pass

Start with source truth, not vibes:

- inspect Farfetch'd base stats, level-up moves, TM/HM compatibility, encounters,
  trainer usage, and Stick availability;
- decide whether the smallest good fix is item availability, move access/timing,
  or a documented intentional gimmick;
- update `docs/balance_intent.md` and `docs/buff_backlog.md` with the decision;
- regenerate `docs/generated/balance_audit.md`;
- run the balance/audit/build floor appropriate for Pokemon data changes.

Do not broaden this into a general weak-Pokemon batch.

## Double-Check Status

Double-checked after writing: the choice was reread against
`docs/project_roadmap.md`, `docs/balance_intent.md`, `docs/buff_backlog.md`,
`docs/generated/balance_audit.md`, and the Morty scout row in
`docs/project_roadmap.md`. `FARFETCH_D` is still the single selected lane, and
no source implementation was started.
