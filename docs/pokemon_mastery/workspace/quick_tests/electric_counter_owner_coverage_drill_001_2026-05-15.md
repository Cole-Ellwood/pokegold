# Electric Counter-Owner Coverage Drill 001 - 2026-05-15

Mode: constructed nonblind regression probe from
`side_known_transfer_022_smogtours-gen2ou-935949`. This is not fresh progress
proof.

Source basis:

- `reviews/electric_counter_owner_coverage_review_001_2026-05-15.md`
- `heuristic_core/public_info_tiers.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/name_next_board_owner.md`
- Smogon Forums, Raikou Analysis:
  `https://www.smogon.com/forums/threads/raikou-analysis.68429/`
- Smogon Forums, GSC OU Steelix:
  `https://www.smogon.com/forums/threads/gsc-ou-steelix.3705042/`

## Score Summary

Scenarios: 4.
Policy hits: 4/4.
Severe blunders: 0.
Hidden-info errors: 0.
Mechanics errors: 0.

## Scenario 1 - Electric Invites Steelix

Prompt:
Raikou faces poisoned Cloyster with Spikes on the opponent's side. Raikou has
Thunderbolt and Hidden Power Water. Steelix/Ground is unrevealed but is a
strong-prior Electric counter-owner. Thunderbolt hits Cloyster harder; Hidden
Power Water destroys Steelix if it enters and still leaves Cloyster pressure
acceptable.

Frozen answer:
Top action: Hidden Power. Name Steelix/Ground as a strong-prior class, not as a
fact. Thunderbolt is second because it only beats the active target.

Answer key: hit.

## Scenario 2 - STAB Still Top

Prompt:
Raikou faces Cloyster at 42%. Steelix is already fainted and no Ground or
Electric immunity has been revealed. Thunderbolt KOs Cloyster; Hidden Power
does not. Snorlax is the only plausible special sponge.

Frozen answer:
Top action: Thunderbolt. The strong-prior Ground/Steel branch has been removed,
so exact active removal beats generic coverage.

Answer key: hit.

## Scenario 3 - Exact Removal Beats Overguarding

Prompt:
Curse Snorlax at full faces Steelix at 23%. Snorlax's Earthquake KOs. Steelix
can legally have Explosion, but if it chooses Roar or any slower/reset action,
Earthquake removes it. Switching Skarmory preserves Snorlax but leaves the
blocker alive.

Frozen answer:
Top action: Earthquake unless Explosion is revealed, forced by damage order, or
the active cannot survive. Exact removal of the blocker beats reflex guard.

Answer key: hit.

## Scenario 4 - Guard The Forced Cash-Out

Prompt:
Curse Snorlax at 46% faces low Steelix. Steelix has revealed Explosion, and
Snorlax cannot KO before Steelix moves. Skarmory is healthy and can enter.

Frozen answer:
Top action: switch Skarmory. The cash-out is revealed and beats the route
piece before Snorlax can convert.

Answer key: hit.

## Next Use

Resume fresh side-known transfer. For every Electric entry, freeze:
`active target -> Ground/Steel/Snorlax counter-owner -> coverage or STAB`.
For every low self-KO user, freeze:
`exact KO before trade? -> guard only if no`.

