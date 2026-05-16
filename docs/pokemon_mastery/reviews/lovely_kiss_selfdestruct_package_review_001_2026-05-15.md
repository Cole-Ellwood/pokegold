# Lovely Kiss Self-Destruct Package Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_020_smogtours-gen2ou-935952_p1_2026-05-15.md`

Reason for study:
Transfer 020 had strong early top-match but failed the severe gate. I treated
revealed Lovely Kiss as a sleep-absorber problem, then failed to join it with
the low-HP Snorlax cash-out branch. The result was Sleep Talk damage into a
Self-Destruct position where Skarmory was the route-preserving owner.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/rescore_after_reveal.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `policy_cards/cashout_boundary.md`
- `workspace/quick_tests/low_support_four_way_probe_001_2026-05-15.md`

Current web sources:

- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Introduction to Status in GSC:
  `https://www.smogon.com/gs/articles/status`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

## Confirmed Lessons

Snorlax set ambiguity is real:
The Smogon threatlist describes Snorlax as highly versatile and explicitly
includes Lovely Kiss and Selfdestruct among the surprises that make no single
counter cover every set. After Lovely Kiss is public, the set has already moved
out of generic CurseLax/RestLax handling.

Self-Destruct is not a small branch:
The GSC Explosion guide explains that Explosion/Selfdestruct commonly removes
non-resists and that Snorlax's STAB Selfdestruct is especially powerful. A low
Snorlax that has delivered sleep pressure must therefore be treated as a live
cash-out package, not as passive bait for Sleep Talk chip.

Sleep Talk absorber is correct but incomplete:
The status guide supports Sleep Talk users as sleep absorbers, and the local
sleep card already says a sleeping RestTalk user can make progress. The missing
boundary is that sleep absorption does not license staying in when the revealed
sleep user can immediately trade for the absorber with Self-Destruct.

Skarmory's job fit:
The threatlist names Skarmory as a premier physical wall and Snorlax check.
In this replay, Skarmory had already shown it could own the Snorlax branch;
using it at turn 26 preserved Snorlax for Zapdos/Raikou instead of trading the
special wall for a low Snorlax.

## Policy Correction

- `role_package_ledger.md`: Lovely Kiss now asks whether the package has become
  sleep pressure plus low-HP cash-out.
- `spend_or_save_piece.md`: defensive mirror now requires naming the lower-value
  resist/Ghost/sack that preserves a valuable RestTalker or special wall.
- `branch_punish_ranking.md`: damage into a low cash-out user is not a branch
  punish when the trade removes the route piece.
- `rescore_after_reveal.md`: Lovely Kiss and Self-Destruct now explicitly
  trigger re-score.

## Measurement Note

Not progress. The simplified docs helped early exact prediction, but the packet
still failed because I did not merge two already-known lessons into one live
package: sleep reveal plus cash-out timing. This is a structural transfer miss,
not a mechanics miss.

