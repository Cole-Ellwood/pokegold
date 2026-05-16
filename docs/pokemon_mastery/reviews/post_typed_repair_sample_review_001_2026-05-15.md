# Post-Typed-Repair Sample Review 001 - 2026-05-15

Parent transfers:

- `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_016_gen2ou-2609052168_p1_2026-05-15.md`
- `docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_017_gen2ou-2609050174_p1_2026-05-15.md`

## Combined Sample

Fresh side-known decisions after typed-absorber repair: 31.

- Top-match: 16/31.
- Acceptable-match: 29/31.
- Severe blunders: 0.
- Hidden-info errors: 0.
- State errors: 0.
- Mechanics errors: 0.
- Positive-selection: 23/31.
- Route-converting move chosen: 19/31.

## Verdict

Limited positive, not proof. This is the first post-repair block with stable
clean gates and high acceptable-match, but exact top-match is still below the
55% gate. Do not claim mastery or 1500-proxy validation from it.

## Method Conclusion

The compact docs are no longer the obvious bottleneck. The remaining issue is
move-ranking calibration under noisy replay-oracle conditions:

- Some exact matches are not positive, such as Thunderbolt into a hidden Ground.
- Some misses are probably stronger than the replay move, such as Roar into
  Starmie or Rock Slide over Pursuit.
- The actionable miss that remains is reset denial when Rest and phazing share
  a turn-order window.

Next fresh work should keep exact top-match, but gate progress on the bundle:
top-match, acceptable class match, positive-selection, route conversion,
branch-punish obedience, and zero severe/hidden/state/mechanics errors.

