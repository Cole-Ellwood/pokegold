# RestTalk Absorber Staging Probe 001 - 2026-05-15

Parent miss:
`workspace/quick_tests/side_known_transfer_002_smogtours-gen2ou-924543_p1_2026-05-15.md`

Mode: constructed nonblind regression. This does not count as fresh replay
proof.

Purpose: verify the new rule that a sleeping RestTalk user can act, but Sleep
Talk is not automatic when another owner can absorb the revealed hit and
preserve the sleeping piece.

Context used:
- `live_core.md`
- `heuristic_core/role_package_ledger.md`
- `heuristic_core/name_next_board_owner.md`
- `heuristic_core/branch_punish_ranking.md`
- `heuristic_core/spend_or_save_piece.md`
- `heuristic_core/reset_loop_denial.md`

## Score Summary

Scenarios: 4.

Correct top action: 4/4.

Acceptable ranked alternative: 4/4.

Severe blunders: 0.

State errors: 0.

Hidden-info errors: 0.

Mechanics errors: 0.

Verdict: regression pass only. Transfer to a fresh side-known replay before
treating this as improvement.

## Scenario 1 - Sleeping Lax, Revealed Double-Edge Only

Board: our Snorlax is asleep at high HP with RestTalk known. Opposing Snorlax
has revealed Double-Edge and Lovely Kiss, not Earthquake. Our healthy Golem is
available.

Answer: switch Golem. Sleep Talk is acceptable but second because the revealed
hit is Double-Edge, Golem preserves the sleeping Snorlax's HP and sleep turns,
and Earthquake is still only a branch that must be monitored.

Grade: correct.

## Scenario 2 - Golem Active, Earthquake Revealed

Board: our Golem is active at mid HP versus Snorlax. Opposing Snorlax has
revealed Double-Edge and Earthquake. Our sleeping RestTalk Snorlax is healthy.

Answer: Roar if Golem survives the Earthquake; switch Snorlax if Golem is too
low. Explosion is third unless Snorlax must be removed immediately and no
Ghost/absorber branch is credible.

Grade: correct.

## Scenario 3 - No Absorber Can Take The Revealed Hit

Board: our sleeping RestTalk Snorlax faces Zapdos. Golem is too low and Zapdos
has revealed Hidden Power into it. Zapdos has not shown phaze.

Answer: Sleep Talk or switch to a special owner if one is known. Do not switch
Golem just because it is an Electric immunity; the revealed coverage branch
invalidates that absorber.

Grade: correct.

## Scenario 4 - Support Job Before Cash-Out

Board: our Cloyster is healthy and has not set Spikes. Opposing Snorlax is
asleep and likely to switch to Starmie if Spikes go up. Cloyster has Explosion,
Surf, Toxic, and Spikes.

Answer: Spikes first, then Toxic or Explosion only after the spinner/absorber
is named and the support job is delivered or impossible. Explosion into the
sleeping Snorlax is premature.

Grade: correct.

## Lesson

The live ranking order for these boards is:

1. What revealed hit or reset loop is coming?
2. Which owner absorbs it while preserving the sleeping or support piece?
3. Does the coverage branch punish that owner?
4. Only then compare Sleep Talk, Roar, Explosion, or staying active.

Next evidence must be fresh side-known replay transfer, not another constructed
probe.
