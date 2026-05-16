# Strong Prior Coverage Setup Risk Review 001 - 2026-05-15

Trigger:
`workspace/quick_tests/side_known_transfer_010_gen2ou-2604264562_p1_2026-05-15.md`

## Verdict

This is a risk-pricing failure. It is not solved by top-match, because the
replay move itself walked into the punished branch.

## Evidence

The transaction line was present. The early owner routing was mostly coherent.
The severe error came from treating unrevealed Tyranitar Fire coverage as
background noise while recommending Scizor Agility. Smogon Tyranitar material
supports Fire coverage as a normal way Tyranitar punishes Steel-types; that is
at least a strong prior when Scizor is the proposed route piece.

## Compact Repair

Keep the lesson in existing tiny cards:

- `public_info_tiers.md`: strong-prior coverage that deletes the proposed route
  piece must be priced before setup or preservation becomes top.
- `spend_or_save_piece.md`: a setup turn spends HP/tempo; it is legal only if
  the route piece survives the priced branch or the line is marked as a read.

## Next Test

Regression drill on strong-prior coverage into setup pieces, then another
fresh side-known packet. Any severe blunder keeps the goal incomplete.
