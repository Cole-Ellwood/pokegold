# PerishTrap Sequence Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_018_gen2ou-2609029507_p2_2026-05-15.md`

Reason for study:
Fresh transfer 018 did not regress on severe or hidden-info gates, but it
repeated one new error class. I identified Misdreavus as a trap/perish package
without ranking the sequence correctly.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/rescore_after_reveal.md`
- `workspace/quick_tests/side_known_transfer_018_gen2ou-2609029507_p2_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Misdreavus OU Revamp:
  `https://www.smogon.com/forums/threads/misdreavus-ou-revamp-done.3643258/`
- Smogon Forums, Sleep Trapping:
  `https://www.smogon.com/forums/threads/sleep-trapping.3617871/`
- Smogon Forums, GSC Sleep Trap:
  `https://www.smogon.com/forums/threads/gsc-sleep-trap.3622522/`

## Confirmed Lessons

Smogon threat material describes Misdreavus's route as Mean Look plus Perish
Song, then stalling the count. The important live lesson is order: Perish Song
does not convert if the opponent is not held or can Baton Pass into a receiver
that escapes the count.

The Sleep Trapping discussion describes Mean Look first, then follow-up moves
such as Pain Split to keep Misdreavus healthy. That matched the replay: actual
play trapped Jolteon, then trapped the Baton Pass receiver, then used Perish
Song, then Pain Split, then switched out.

Confuse Ray is not the package by itself. It is a survival/stall tool inside
the trap route. Pain Split is also not generic recovery; it is the move that
keeps Misdreavus alive long enough for the count to resolve.

## Policy Correction

- `role_package_ledger.md`: trap/perish now asks whether the target is actually
  held or can switch, pass, phaze, or KO the trapper before count converts.
- `rescore_after_reveal.md`: Mean Look, Perish Song, and Pain Split now
  trigger re-scoring around hold -> survive -> count.

## Measurement Note

Not progress. The packet went 9/19 top and 16/19 acceptable with clean severe
and hidden gates, but the repeated trap sequence miss means the loop must test
that package again before any broader claim.

