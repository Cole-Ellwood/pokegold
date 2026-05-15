# Phaze Loop Rest Timing Probe 001 - 2026-05-14

Source parent:
`quick_tests/replay_turn_pause_059_rest_phaze_status_smogtours-gen2ou-888483_2026-05-14.md`.

Mode: constructed nonblind policy regression. This is a regression check for
the replay 059 failure classes, not fresh replay-transfer evidence.

## Score Summary

Scenarios: 4.

Action policy hits: 4 / 4.

Classification hits: 4 / 4.

Severe blunders: 0.

Mechanics errors: 0.

Hidden-information errors: 0.

## Scenario 1 - Keep The Phaze Loop

Prompt:

Vanilla GSC. Your Skarmory is active at 100%. Spikes are on the opponent's
side. The opponent's Steelix has just been dragged in at 94% by Whirlwind.
Their revealed team includes a sleeping Snorlax, Zapdos, Cloyster, Porygon2,
and Steelix. Skarmory has revealed Whirlwind. Steelix has not revealed a move.

Question: should Skarmory switch to a Steelix answer, or keep using Whirlwind?

Frozen answer:

Keep using Whirlwind by default. The route is already converting: every switch
or drag taxes the opponent through Spikes, and Steelix has not yet shown an
immediate branch that beats the loop. Switch only if Steelix reveals a move or
the position shows a concrete punish that makes staying lose more than the
Spikes loop gains.

Answer key:

Hit. The replay miss was abandoning Whirlwind before the opponent showed an
actual breaker. A possible Steelix threat is not enough by itself.

## Scenario 2 - Immediate Spinner Exception

Prompt:

Vanilla GSC. Your Skarmory is active at 82%. Spikes are on the opponent's side.
The opponent has Cloyster active at 88%. Cloyster has revealed Rapid Spin and
Surf in earlier turns. Your Gengar is healthy and known; it can enter without
Spikes damage. Skarmory's Whirlwind is slower priority than Rapid Spin.

Question: keep Whirlwind, switch, or attack?

Frozen answer:

Do not keep Whirlwind as the default. The spinner is active and can remove
Spikes before Whirlwind moves. Switch to Gengar if its entry is safe enough to
block Rapid Spin, or use the direct punish that makes Spin costly if the Ghost
entry is not safe. The important point is that the hazard route is not real if
Cloyster spins for free.

Answer key:

Hit. This is the opposite boundary to Scenario 1. The phaze loop stops being
the route when the immediate Spin path is active and unpunished.

## Scenario 3 - Sleeping Status Absorber

Prompt:

Vanilla GSC. Opponent Skarmory has revealed Toxic and Whirlwind. Your Snorlax
is asleep from Rest and still useful later, but cannot be poisoned while
asleep. Your Porygon2 and Cloyster are awake and dislike Toxic. Spikes are on
your side, so every switch costs HP.

Question: can the sleeping Snorlax be switched in, or should it be saved off
the field until it wakes?

Frozen answer:

Switching the sleeping Snorlax into the Toxic turn is live if the cost is worth
protecting the awake pieces. Do not frame this as "wake Snorlax" versus
"preserve Snorlax forever." A sleeping Pokemon can be preserved and still used
as a status absorber. Re-solve next turn around sleep counter, Spikes damage,
and whether Skarmory can Whirlwind again.

Answer key:

Hit. Replay 059 showed sleeping Snorlax repeatedly re-entering to blank Toxic.
The route job was status absorption, not burning wake turns.

## Scenario 4 - Rest Wake Timing Before The Move

Prompt:

Vanilla GSC. Opposing Snorlax used Rest, then spent two active turns asleep
while repeatedly being dragged or switched back in. It is now active again at
88% in front of your Skarmory. Skarmory has Whirlwind and Toxic. Snorlax has
revealed Double-Edge and Rest.

Question: what must be checked before calling this a free Whirlwind or Toxic
turn?

Frozen answer:

Track the active Rest sleep turns exactly. If Snorlax has already spent two
active sleep turns, it can wake and act now. Whirlwind may still be correct,
but the branch is no longer "free sleep"; price Double-Edge damage, Rest,
switch, or another active move before choosing Toxic, Whirlwind, or a handoff.

Answer key:

Hit. The replay 059 state error was assuming another passive sleep turn when
Snorlax could wake and attack.

## Reusable Boundary

Spikes plus phazing is a route engine only while the opponent's answers are
still paying a meaningful cost. Keep it when the switch cycle is losing. Break
it when the opponent has an immediate unpunished Spin path, damaging punish,
status punish, or counter-pivot that changes the next board.

## Next Transfer Check

Use the fixed replay helper on a fresh nicknamed replay if possible. The target
is a no-keyword-screen packet where public species names are visible in the
prompt and the tested boundary is phaze-loop commitment versus the first real
branch that breaks the loop.
