# Worked Example: Status Absorber Assignment In Boss Fights

Source basis:

- Smogon's GSC status article treats sleep, paralysis, and poison as different
  strategic resources: sleep is temporary control, paralysis often rewrites
  Speed-dependent routes, and poison combines with switching pressure.
- Smogon's GSC Spikes article says status support should target Pokemon that
  care about the status. The defensive mirror is to route predicted status into
  a piece that cares least in the current battle state.
- Smogon's DP status article states the broader status-absorber concept
  directly. For Gym Leader Lab, that concept must still be checked against the
  romhack type chart, passives, items, Sleep Clause, RestTalk behavior, and
  boss roster.

## Recipe Used

Do not ask "who can take status?" in isolation. Ask "which Pokemon can take
this exact status without losing a unique future job?"

Good status absorption requires all three:

1. The absorber's future job is redundant, spent, or still functional while
   statused.
2. The status turn does not give the boss a larger route than the absorbed
   status costs.
3. The plan after absorption is named before the status lands.

## Misty: Hypnosis And Thunder Wave Assignment

Public boss pressure:

- Politoed can use Hypnosis and Rain Dance.
- Starmie and Lapras can convert rain, speed, and recovery pressure.
- Quagsire asks for a distinct anti-Curse or special-pressure route.
- Lanturn can use Thunder Wave to break Speed-dependent revenge plans.

Bad default:

- "Let the Water answer absorb sleep because it switches in well."

Why that fails:

- If that Water answer is also the only Starmie, Lapras, or Quagsire answer,
  sleeping it may solve Politoed while losing the later boss route. If the fast
  cleaner is the only way to finish Starmie or Lapras, letting Lanturn paralyze
  it may remove the endgame rather than merely slow the plan.

Better policy:

- Assign a sleep absorber only if it has no unique later job, if Sleep Clause
  occupation itself creates useful safety, or if it can still perform its job
  asleep through RestTalk, item cure, or a short forced route.
- Assign a Thunder Wave absorber only if its job does not depend on Speed, or
  if paralysis is less costly than allowing rain, Recover, or Curse pressure.
- If no such absorber exists, the status move becomes the route to deny: attack
  Politoed before Hypnosis matters, force Lanturn out, pivot through a piece
  whose paralysis is harmless, or choose a shorter route that avoids the status
  loop.

Answer-changing information:

- A separate Starmie answer makes a Politoed sleep trade easier.
- A slow bulky route makes Lanturn paralysis less severe.
- Rain already active makes spending a turn on absorption more expensive.
- Quagsire still healthy makes sleeping or paralyzing the anti-Curse piece much
  more dangerous.

## Falkner: Noctowl Hypnosis After Accuracy Pressure

Public boss pressure:

- Pidgeotto can create accuracy and priority damage before Noctowl arrives.
- Noctowl can use Hypnosis, and Mint Berry can make sleep plans unreliable.

Bad default:

- "Use the damaged lead as sleep fodder."

Why that fails:

- A damaged lead is expendable only if its Pidgeotto job is finished and it has
  no unique Noctowl or Spearow job left. If it is the only accurate attacker
  after Sand Attack, the priority-safe cleaner, or the special pressure piece,
  sleep absorption may remove the route.

Better policy:

- If a lead has already denied Pidgeotto and no longer handles Spearow or
  Noctowl, it can absorb Hypnosis to create a clean entry for the real closer.
- If the intended absorber is also the only Noctowl answer, deny Hypnosis by
  attacking, switching before the sleep turn, or using a route that does not
  ask the same Pokemon to both sleep and finish.

Answer-changing information:

- Mint Berry still intact lowers the value of the user's own sleep plan.
- A current accuracy drop makes repeated attack routes worse.
- Quick Attack range can turn a "free" sleep absorber into the lost cleaner.

## Sabrina: Lovely Kiss And Thunder Wave Assignment

Public boss pressure:

- Jynx can use Lovely Kiss.
- Hypno can use Thunder Wave, Rest, Seismic Toss, and Psychic.
- Alakazam and Espeon can punish a player who spends the wrong special answer.

Bad default:

- "Let the special wall take status."

Why that fails:

- If the special wall is also the Alakazam answer, Hypno breaker, or Jynx
  answer, sleep or paralysis may remove the only route that survives Sabrina's
  later pieces. Paralysis is not just a speed number: it can add full-paralysis
  risk to Rest, recovery, setup, and revenge turns.

Better policy:

- Route Lovely Kiss into a Pokemon whose awake turns are not required later, or
  one whose sleep creates a useful clause state without uncovering Alakazam or
  Espeon.
- Route Thunder Wave into a slow wall only if that wall still wins its required
  exchange while paralyzed.
- If paralysis removes the only revenge or tempo route, treat Hypno as a
  support-function threat and pressure it before it spreads status.

Answer-changing information:

- Alakazam's lock or fourth move can make a different piece expendable.
- A confirmed separate Hypno answer makes Thunder Wave absorption easier.
- Jynx still unrevealed makes spending the sleep absorber early risky.

## Koga-Style Toxic And Trap Clocks

Public boss pressure:

- Poison, Spider Web / Mean Look, Haze, recovery, Pursuit, and confusion can
  turn a neutral matchup into a clock the player does not own.

Bad default:

- "This low-HP Pokemon can absorb Toxic."

Why that fails:

- Low HP does not imply expendable. A low-HP phazer, spinner, priority check,
  poison answer, or final revenge piece may still have one scheduled job. Toxic
  can remove that last entry before the job arrives.

Better policy:

- Absorb Toxic with a piece whose remaining entries are already scheduled and
  whose route completes before the poison clock matters.
- Do not absorb Toxic with the only answer to the boss's next converter unless
  the status turn creates an immediate stronger route.
- If trap plus poison can lock the supposed absorber, price switch freedom as
  part of the status cost.

Answer-changing information:

- Whether the player has Heal Bell, Rest, item cure, poison immunity, or a
  statused piece changes who can absorb.
- Whether the boss can trap the absorber changes poison from a timer into a
  possible forced loss.
- Whether hazards are active changes how many entries the poisoned piece
  actually has left.

## Extracted Lesson

Status absorption is a route-assignment problem. A statused Pokemon can still
be valuable, and an unstatused Pokemon can be the wrong target to preserve. The
right question is whether this exact status prevents this exact piece from
performing the job the battle still needs.
