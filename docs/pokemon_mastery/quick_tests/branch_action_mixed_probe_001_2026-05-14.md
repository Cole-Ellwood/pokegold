# Branch Action Mixed Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_063_branch_action_transfer_smogtours-gen2ou-907828_2026-05-14.md`.

Mode: constructed nonblind policy regression. This checks the replay 063
branch-action misses. It is not fresh replay-transfer evidence.

## Score Summary

Scenarios: 4.

Action policy hits: 4 / 4.

Classification hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Immediate Thunder Branch

Prompt:

Vanilla GSC spectator-public state. Your Raikou is active at 94% against an
opposing Zapdos at 100%. Spikes are on both sides. Zapdos has revealed Thunder.
You have Golem available, and it can enter on Thunder but will take Spikes.
Zapdos could also switch to Snorlax or another absorber, but that branch is not
forced yet.

Question: should Raikou attack or switch Golem?

Frozen answer:

Switch Golem if the immediate Thunder branch is still the best branch. The
absorber switch is possible, but after Zapdos just regained the active matchup,
do not let the previous counter-switch success make you ignore the simplest
active punish.

Answer key:

Hit. Replay 063 punished attacking with Raikou into the immediate Thunder
branch. The correct action was Golem.

## Scenario 2 - Expected Absorber Switch

Prompt:

Vanilla GSC spectator-public state. Your Golem is active at 100% against an
opposing Zapdos at 100%. Zapdos has just had Thunder blocked once. You expect
Zapdos to leave for Cloyster or another physical absorber. You have Raikou
available to meet a Water-type support pivot.

Question: take Rock Slide/Earthquake, or counter-switch?

Frozen answer:

Counter-switch if the Zapdos exit is the best branch. Golem's active attack is
fine only if Zapdos staying is likely enough or if the expected absorber takes
route-changing damage. If the branch is "Zapdos leaves to Cloyster," Raikou is
the move that acts on the read.

Answer key:

Hit. Replay 063 showed p1 switching Raikou into the expected Cloyster branch.
The prior miss was naming the exit and still choosing Golem pressure.

## Scenario 3 - Support Status Timing

Prompt:

Vanilla GSC spectator-public state. Your Skarmory is active at 59% against an
opposing Cloyster at 94%. Spikes are on the opponent's side. Cloyster is likely
to set Spikes or begin hazard control. You can switch Raikou to pressure it, or
use Toxic now. Switching takes no immediate damage but gives up the current
turn.

Question: switch Raikou or use Toxic?

Frozen answer:

Use Toxic if poisoning Cloyster changes its future support job more than the
Raikou switch does. This is not a generic status script: it directly prices the
support piece's future Spikes, Spin, and Explosion map.

Answer key:

Hit. Replay 063 used Toxic, then Cloyster set Spikes. The support-status timing
was correct because it changed Cloyster's future route value.

## Scenario 4 - Hard Answer Over Explosion

Prompt:

Vanilla GSC spectator-public state. Your Cloyster is at 58% against an opposing
Snorlax at 99% with +1 Attack and +1 Defense. Spikes are on the opponent's
side. Snorlax is likely to keep using Double-Edge. You have Skarmory available
as a hard answer. Cloyster can plausibly explode, but the route after the trade
is not named.

Question: Explosion or switch Skarmory?

Frozen answer:

Switch Skarmory by default. Explosion is correct only if it opens a named
converter and the hard-answer route is worse. Here Skarmory preserves Cloyster's
Explosion threat, checks the boosted Snorlax, and keeps the Spikes route alive.

Answer key:

Hit. Replay 063 used Skarmory and punished the auto-cash-out instinct.

## Reusable Boundary

Branch action is a comparison, not a slogan. Immediate active punish,
counter-switch, support status, hard answer, and Explosion are all correct in
different branches. The move must win the named branch and preserve the live
route better than the alternatives.

## Next Transfer Check

Run a fresh no-keyword-screen replay packet. For each turn, write:

- named branch;
- action chosen to beat that branch;
- why that action beats active move, counter-switch, utility, status, phaze, or
  cash-out alternatives.
