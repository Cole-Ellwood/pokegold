# Resisted Explosion Board Delta Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_038_gen2ou-2588401623_p2_2026-05-15.md`

## Trigger

Packet 038 scored well enough to show the compact cards can be used, but it
still produced two clean policy misses in the same family:

- Turn 23: I made Golem Explosion top too early, before the post-boom board was
  better than Zapdos preserving Golem.
- Turn 25: I then under-ranked Explosion when resisted Skarmory chip plus free
  Vaporeon entry was the actual route-converting spend.

This is the precise boundary the previous repair did not solve. "Do not
over-rank irreversible converters" is incomplete unless I also classify the
post-Explosion board.

## Source Check

Current GSC sources support the correction:

- Smogon's GSC Explosion guide frames Explosion as more than direct removal:
  it can create a free switch sequence after the user faints, but it still
  requires deliberate target and timing selection.
- The Smogon Explosion forum analysis says Golem uses Earthquake to punish many
  Normal resists and Explosion to threaten non-resists, while warning that
  resistant absorbers still take meaningful damage and the board after the
  absorb must be checked.
- The current GSC sample-team breakdown treats bait Explosion as a way to
  improve Vaporeon or Snorlax endgames, not as a generic button.
- Vaporeon analysis says it often needs teammates to remove or weaken checks
  before it can sweep.
- Snorlax and Skarmory sources match the replay branch map: Snorlax is broad
  pressure but can invite phaze/setup during Rest cycles, and Skarmory is a
  physical wall that may still be opened by special free-entry pressure.

Sources:

- `https://www.smogon.com/gs/articles/guide_to_explosion`
- `https://www.smogon.com/forums/threads/explosion-in-gsc-qc-2-2-gp-2-2.3484961/`
- `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`
- `https://www.smogon.com/forums/threads/gsc-ou-vaporeon.3702374/`
- `https://www.smogon.com/forums/threads/gsc-ou-snorlax.3694359/`
- `https://www.smogon.com/forums/threads/skarmory-done.3463827/post-4158175`

## Diagnosis

The live docs had both halves of the answer, but in separate places:

- `spend_or_save_piece.md` said to preserve irreversible converters when a
  reversible line covers the same active and branch.
- Older reviews said resisted Explosion can convert through chip plus free
  entry.

The missing comparator was:

```text
What board exists after Explosion, and is it better than the best preserving
line?
```

For Golem-style positions:

- Into a Ghost branch, Explosion is usually wrong unless the read and fallback
  are explicit; Earthquake or handoff is the branch punish.
- Into a resistant Skarmory branch, Explosion can be right only when chip plus
  free entry creates the named Zapdos/Vaporeon/Snorlax owner before Skarmory
  resets, phazes, or walls the route.
- Into Snorlax, Explosion is top only when Snorlax is the actual blocker and
  the post-boom owner is named. It is not top just because Snorlax is bulky.

## Policy Compression

Patch three tiny cards, not a long new policy:

1. `spend_or_save_piece.md`: classify the post-boom board before ranking
   Explosion or Self-Destruct.
2. `branch_punish_ranking.md`: make Explosion branch-specific for Ghost,
   resist, and true-blocker branches.
3. `name_next_board_owner.md`: when several handoffs answer the visible threat,
   rank them by route budget and whether they create the next action.

## Next Gate

Run one small nonblind regression drill for this board-delta rule, then restart
a fresh packet. Packet 038 is encouraging, but one good packet plus a targeted
drill is still not a trend.
