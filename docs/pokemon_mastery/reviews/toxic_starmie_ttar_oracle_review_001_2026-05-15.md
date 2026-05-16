# Toxic Starmie / Tyranitar Oracle Review 001 - 2026-05-15

Parent packet:
`workspace/quick_tests/side_known_transfer_035_gen2ou-2585304299_p2_2026-05-15.md`

## Why This Review Exists

The packet was non-perfect and raw top-match was poor. The misses did not show
hidden-info or severe-blunder regression, but they exposed two live boundaries:

- when a self-KO route piece is too slow or too frail to boom through a
  revealed attack;
- when Toxic on a Recover user is real progress versus when it still needs an
  immediate pressure owner because the target can switch or phaze.

## Sources Read

Local:

- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/reset_loop_denial.md`
- `heuristic_core/role_package_ledger.md`
- `reviews/toxic_recover_clock_review_001_2026-05-15.md`
- `reviews/pursuit_trap_and_oracle_review_001_2026-05-15.md`

Web:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon, GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon Forums, Tyranitar OU Revamp:
  `https://www.smogon.com/forums/threads/tyranitar-ou-revamp-done.3658517/`

## Confirmed Lessons

Explosion needs a pre-boom survival check:
The Explosion source supports using self-KO moves as deliberate offensive,
defensive, and trade-down tools. That does not override move order. If the
opponent's revealed faster attack removes the exploder before it moves, boom is
only a high-risk read, not the normal converter. Turn 20's actual Cloyster
Explosion into Raikou was not a policy correction because Raikou's Thunder
missed.

Toxic on Starmie is a start, not the endpoint:
The GSC Spikes source says Toxic can wear Starmie down but is tricky because
Recover buys time. The packet matched that: Toxic from Alakazam was correct,
but after it landed, the live question became who forces Recover or punishes the
switch. Jolteon pressure and Alakazam Recover were both defensible depending on
the Tyranitar branch; neither should be reduced to "status landed, wait."

Tyranitar's package changes the poison route:
The Tyranitar source emphasizes Rock Slide, Pursuit, Roar, residual damage, and
lack of reliable recovery. In this endgame, poisoned Tyranitar was still active
because Roar changed the board and switching downgraded the toxic clock to
regular poison. Alakazam could stall with Recover, but Psychic into Tyranitar
was mechanically invalid and should be treated as weak-oracle noise.

## Policy Compression

Patch tiny cards only:

- `spend_or_save_piece.md`: before raw Explosion/Self-Destruct from a pressured
  piece, confirm the user moves first or survives the revealed/strong-prior hit.
- `reset_loop_denial.md`: Toxic clocks need an active pressure owner; bad poison
  can reset or downgrade after a switch, so do not count it as stored progress
  unless the target is held, forced to Recover, or punished on exit.

No species-specific live card is needed. This is the existing spend/save and
reset-denial rule applied to a noisy replay oracle.
