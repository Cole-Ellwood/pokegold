# Sleep Cash-Out Hazard Sack Review 001 - 2026-05-15

Parent transfer:
`docs/pokemon_mastery/workspace/quick_tests/side_known_transfer_024_smogtours-gen2ou-935947_p1_2026-05-15.md`

Reason for study:
Transfer 024 repeated the cash-out miss after the previous Lovely Kiss repair.
I left Zapdos active into Snorlax Self-Destruct after Lovely Kiss +
Double-Edge, then left Snorlax active into Cloyster Explosion after Surf. I
also missed a hazard-death sack that created clean Zapdos entry.

## Sources Read

Local mastery docs:

- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/branch_punish_ranking.md`
- `reviews/lovely_kiss_selfdestruct_package_review_001_2026-05-15.md`
- `policy_cards/cashout_boundary.md`
- `policy_cards/sleep_absorber_and_set_ambiguity.md`
- `mechanics_fixtures/spikes_rapid_spin/README.md`

Current web sources:

- Smogon, Explosion in GSC:
  `https://www.smogon.com/gs/articles/guide_to_explosion`
- Smogon, Playing with Spikes in GSC:
  `https://www.smogon.com/gs/articles/gsc_spikes`
- Smogon Forums, Snorlax update:
  `https://www.smogon.com/forums/threads/snorlax-update-qc-2-2-gp-2-2-finished.3467216/`
- Smogon Forums, GSC OU Sample Teams Breakdown:
  `https://www.smogon.com/forums/threads/gsc-ou-sample-teams-breakdown-updated-july-2023.3688523/`

Subagent support:

- `Plato` reviewed the compact docs and found the cash-out rules were mostly
  present but under-applied. It identified hazard-death clean entry as the
  weakest live-doc coverage.

## Confirmed Lessons

Cash-out was not missing; I failed to run it:
The local cash-out and sleep cards already require naming the absorber or sack
when Explosion/Self-Destruct can remove a route piece. The Snorlax review had
already patched Lovely Kiss plus Self-Destruct. The failure was that I let the
active pressure story override the one-cycle trade story.

Mid-HP Snorlax can still be a cash-out package:
The Snorlax material shows Lovely Kiss as a serious offensive fourth move, and
the sample-team discussion describes Snorlax using sleep, chip, or
Self-Destruct to clear checks. Therefore the live rule cannot wait until
Snorlax is low. Once sleep has been delivered and Double-Edge is public,
Self-Destruct must be priced if it removes Zapdos, Raikou, Snorlax, or the
current route owner.

Cloyster Surf can be the bluff before Explosion:
The Explosion guide explicitly describes Cloyster bluffing Explosion and using
Surf when the opponent overguards. This means the solve cannot stop after one
Surf. After Surf changes HP, re-run the cash-out four-way check because the
next turn may be the Explosion turn.

Hazard-death sack is a real tactic, but romhack timing is unverified:
The replay log showed a 10% Nidoking switched into Spikes, fainted, canceled
the opponent's action, and gave Zapdos clean entry. That is vanilla Showdown
evidence for the training packet. It is not enough for romhack boss advice, so
the Spikes fixture now tracks complete-turn switch-in-faint action skipping as
unverified.

## Policy Correction

- `role_package_ledger.md`: Lovely Kiss + Double-Edge Snorlax now stays a
  sleep-plus-cash-out package before low HP unless Rest or four moves disprove
  Self-Destruct.
- `spend_or_save_piece.md`: added controlled hazard-death sack and immediate
  re-check after chip into support/cash-out users.
- `branch_punish_ranking.md`: damage is not branch punish if the cash-out or
  clean-entry branch still wins the next board.
- `mechanics_fixtures/spikes_rapid_spin/README.md`: added switch-in Spikes KO
  action-skip as a pending complete-turn fixture.

## Measurement Note

This is regression, not improvement. Packets 023-024 have repeated severe
cash-out failures, and packet 024 was a stronger replay oracle. The next work
should not be broad note-writing or more blind replay volume. It should be a
small regression probe and then one fresh packet explicitly scoring:
`revealed package -> cash-out owner -> lower-value guard/sack -> clean-entry
owner`.

