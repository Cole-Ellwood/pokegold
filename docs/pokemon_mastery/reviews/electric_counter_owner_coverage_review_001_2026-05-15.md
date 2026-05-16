# Electric Counter-Owner Coverage Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_022_smogtours-gen2ou-935949_p1_2026-05-15.md`

Reason for study:
Transfer 022 was a countable 30-decision packet and mostly clean, but it failed
the hidden/strong-prior branch gate. On turn 4 I chose Raikou Thunderbolt into
Cloyster instead of Hidden Power into the strong-prior Ground/Steel
counter-owner, which was revealed as Steelix.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/spend_or_save_piece.md`
- `reviews/electric_coverage_absorber_review_001_2026-05-15.md`
- `reviews/growth_pass_sequence_review_001_2026-05-15.md`

Current web sources:

- Smogon Forums, Raikou Analysis:
  `https://www.smogon.com/forums/threads/raikou-analysis.68429/`
- Smogon Forums, GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`
- Smogon GSC OU Threatlist:
  `https://www.smogon.com/gs/articles/gsc_threats`
- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`

## Confirmed Lessons

Raikou coverage is a counter-owner tool:
The Raikou material explains that Hidden Power choices decide which Pokemon
counter Raikou, and that Water/Ground-style coverage exists specifically to hit
Steelix and other Ground-type answers. Therefore the live ranking cannot stop
at "Thunderbolt beats Cloyster"; it must ask whether Hidden Power beats the
incoming Electric counter-owner.

Steelix is a live Electric answer:
The Steelix analysis explicitly frames Steelix as a phazer for teams weak to
Raikou/Zapdos, with Earthquake, Roar, Curse, and Explosion. Once Raikou appears,
Steelix is a strong-prior class even before the exact slot is revealed.

Spikes change the coverage threshold:
In the replay, Spikes were already on p2's side. Hidden Power into Steelix
turned a full counter-owner into a low, forced piece. That is positive route
conversion even though Thunderbolt would have hit the visible Cloyster harder.

Cash-out repair boundary:
Steelix can explode, but the Explosion guide and local cash-out rule still
require turn-order and exact-removal pricing. On turn 19 I overlearned the
cash-out repair by switching away from Snorlax instead of using Earthquake to
remove a low Steelix. Exact removal beats fear when it lands before reset,
phaze, or trade.

## Policy Correction

- `public_info_tiers.md`: Ground/Steel counter-owner is now explicit
  strong-prior class when our Electric enters.
- `branch_punish_ranking.md`: Electric STAB must be compared to Hidden Power
  into the Ground/Steel counter-owner; exact removal beats overguarding
  possible cash-out.
- `name_next_board_owner.md`: Electric entries now require naming the likely
  Ground/Steel/Snorlax/Electric counter-owner.
- `spend_or_save_piece.md`: added a compact anti-overcorrection clause for
  exact removal before self-KO/reset/phaze.

## Measurement Note

Limited transfer only. This packet met the nominal top and acceptable gates and
had no severe/state/mechanics errors, but the hidden/strong-prior miss means it
cannot count as proof. The next fresh packet should test whether Electric
counter-owner coverage and cash-out overguard boundaries hold without dropping
positive selection.

