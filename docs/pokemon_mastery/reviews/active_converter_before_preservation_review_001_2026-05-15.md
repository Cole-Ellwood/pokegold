# Active Converter Before Preservation Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_014_gen2ou-2610279541_p1_2026-05-15.md`

Reason for study:
The fresh packet used the new candidate-comparison prompt, but top-match stayed
low because I over-preserved. I switched or wanted to switch before pricing the
active move that converted the route.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/converter_before_script.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`

Current web sources:

- Smogon Forums, Zapdos QC:
  `https://www.smogon.com/forums/threads/zapdos-qc-2-2-gp-2-2.3673848/`
- Smogon Forums, GSC Zapdos:
  `https://www.smogon.com/forums/threads/gsc-zapdos.3674240/`
- Smogon, Introduction to Competitive GSC:
  `https://www.smogon.com/smog/issue28/gsc`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Rhydon legitimacy thread:
  `https://www.smogon.com/forums/threads/the-legitimacy-of-rhydon-in-gsc-ou.3768245/`

## Confirmed Lessons

Zapdos is not just a piece to preserve. Current Smogon analysis emphasizes that
Thunder can cripple Snorlax and Raikou and that Zapdos forces many switches.
Even though Snorlax checks are essential, the Zapdos turn can still be the
converter when it forces Rest, paralysis, or low-health pressure before the
handoff.

Phazing is a converter, not only a defensive reset. GSC phazing works by moving
last; after a Normal resist like Rhydon absorbs Double-Edge, Roar can convert
if the phazer survives the Water/special counter-owner's hit. Switching away
immediately can waste the route piece's one live job.

Rhydon is fragile into Water and Grass pressure, but that does not mean it must
leave before acting. The live question is whether Roar/Counter/damage changes
the next forced choice before the counter-owner removes it.

## Policy Correction

- `spend_or_save_piece.md`: added a preservation boundary requiring the active
  attack/phaze/setup converter to be priced before switching away.
- `reset_loop_denial.md`: added a Normal-resist phazing check after absorbing
  pressure.
- `converter_before_script.md`: added an explicit question for whether the
  active piece already has the converter.

## Measurement Note

This is a repair after flat transfer, not progress. The next fresh packet must
show that the active converter is promoted without reintroducing severe or
hidden-info errors.

