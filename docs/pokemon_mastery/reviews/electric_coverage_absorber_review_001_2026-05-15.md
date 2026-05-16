# Electric Coverage Absorber Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_019_gen2ou-2608645646_p1_2026-05-15.md`

Reason for study:
Transfer 019 had strong exact top-match, but it failed the hidden-info gate.
I overcorrected from "typed absorber over generic wall" into sending Nidoking
at Jolteon without sufficiently pricing strong-prior Hidden Power coverage.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/role_package_ledger.md`
- `workspace/quick_tests/typed_absorber_over_generic_wall_drill_001_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Jolteon Baton Pass:
  `https://www.smogon.com/forums/threads/jolteon-baton-pass.3455015/`
- Smogon Forums, Jolteon Baton Pass:
  `https://www.smogon.com/forums/threads/jolteon-baton-pass.3457727/`
- Smogon Forums, GSC Good Cores:
  `https://www.smogon.com/forums/threads/gsc-good-cores.3536015/`

## Confirmed Lessons

Smogon threat material describes Jolteon as an Electric attacker with Water-
or Ice-type Hidden Power coverage. Jolteon coverage is therefore not a
possible-only branch when choosing a Ground absorber; it is a strong prior that
must be priced before the Ground handoff becomes top.

The typed-absorber rule is still correct when Electric STAB or status is the
main route and coverage is acceptable. It is wrong when the current Pokemon can
safely convert with Thunder Wave or damage while the Ground handoff is punished
by standard coverage.

## Policy Correction

- `public_info_tiers.md`: Electric Hidden Power coverage is now explicitly
  strong-prior for Zapdos, Raikou, and Jolteon.
- `role_package_ledger.md`: typed-absorber selection now includes the inverse
  boundary, keeping current status/damage above a punished Ground handoff.

## Measurement Note

Not progress. Exact top-match was high, but the hidden-info gate failed; this
is exactly why the goal scores hidden-info errors independently from top-match.

