# Worked Example: Karen Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Karen as a sleep/hazard/Pursuit
and weather-clock fight. This is a team-agnostic planning artifact, not final
turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `KarenGroup`.
- Boss route map: `../boss_route_maps/karen_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Pursuit, Dragon Dance, Sunny Day, SolarBeam, Safeguard, Hypnosis, Dream
  Eater, Dark category, and weather/recovery references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Gengar material: Gengar's threat comes from fast sleep, surprise support,
  and forcing uncomfortable reactions, not one fixed attack plan.
- GSC Tyranitar material: Pursuit/Roar-style role compression teaches that
  trapping, phazing, and coverage must be priced by current route, not by type
  slogan.
- GSC Houndoom material: Houndoom can trap with Pursuit or convert with Sunny
  Day; sometimes Pursuit damage is more valuable than setting sun.
- GSC status material: sleep and poison create clocks only if the follow-up
  converts before the target or team resets.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Karen

Known boss roster:
  Gengar / Donphan / Murkrow / Tyranitar / Crobat / Houndoom

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Tyranitar answer, a Houndoom sun answer, and a plan for sleep
  or Safeguard disrupting the main status route; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Pursuit doubling on
  switching targets, Dark being special, Dragon Dance raising the current
  higher offensive stat plus Speed, Sunny Day lasting five turns, sun boosting
  Fire and weakening Water, SolarBeam skipping charge in sun, and Safeguard
  blocking status while active

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether the sleep target is expendable,
  whether Donphan can spin or Roar safely, and whether the Houndoom answer
  still works under sun
```

## Output Shape

Primary route:

- Deny Karen ownership of the first clock: Gengar sleep/hazards, Crobat
  status/Safeguard, Tyranitar Dragon Dance, Houndoom sun, or Murkrow Pursuit.

Backup route:

- If Gengar lands Hypnosis or Spikes, rebuild around the sleeping Pokemon's
  role and grounded switch costs. If Houndoom sets sun or Tyranitar boosts,
  shorten the fight around immediate denial rather than continuing a slow
  status or hazard plan.

Boss route priority:

```text
immediate:
  Gengar Hypnosis if it can disable the only Tyranitar or Houndoom answer.
  Gengar Spikes if the user's team needs repeated grounded switching.
  Murkrow Pursuit if the current active wants to flee and cannot stay safely.

accumulating:
  Donphan Rapid Spin / Roar control.
  Crobat Toxic / Confuse Ray / Safeguard clock control.
  Tyranitar Dragon Dance.

endgame:
  Houndoom Sunny Day into boosted Flamethrower or one-turn SolarBeam.
  Tyranitar after a boost if Fighting/Ground/Water answers were slept or
  poisoned.
```

Boss route to deny first:

- Deny the route that removes the only answer to Karen's converter. If the
  Tyranitar answer can be slept by Gengar, that is the first problem. If the
  Houndoom answer relies on Water damage, Sunny Day becomes urgent before the
  Water answer is committed.

Boss route that can be delayed:

- Donphan can be delayed if the player's route does not depend on hazards or
  setup and if Roar does not expose an irreplaceable answer. If hazards/setup
  are central, Donphan is urgent.

- Crobat can be delayed if its status/confusion/Safeguard turns do not block
  the player's actual route. If the route depends on status, Safeguard makes
  Crobat urgent.

Best lead profile:

- A lead that pressures Gengar without being the only Tyranitar or Houndoom
  answer. It should either punish Hypnosis/Spikes attempts, absorb sleep
  without losing the fight, or force Gengar out while keeping Donphan, Crobat,
  Tyranitar, and Houndoom routes covered.

Avoid as lead:

- The only Tyranitar answer if Gengar can sleep it.
- The only Houndoom answer if it loses to Sunny Day plus SolarBeam.
- A hazard lead if Donphan spins for free.
- A status-only lead if Crobat can Safeguard and force the plan to stall.
- A vulnerable Psychic/Ghost/special attacker that Murkrow can trap with
  Pursuit after it is forced out.

First move plan:

- Give turn 1 one job: stop Gengar's sleep/hazard route from disabling the
  answer map. If accepting sleep is the least bad branch, name which Pokemon is
  being spent and which route remains live.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Gengar's Hypnosis, Spikes, Shadow Ball, and Dream Eater branches.

Turn 2:
  If sleep or Spikes landed, rebuild the route around the disabled role and
  grounded switch cost. If Gengar was denied, prepare for Donphan, Murkrow,
  Tyranitar, Crobat, or Houndoom.

Turn 3:
  Start the relevant ledger: sleep turns, Spikes layers, Pursuit stay/switch
  branch, Safeguard turns, Dragon Dance boost, or Sunny Day turns.
```

Piece to preserve:

- The Tyranitar denial route by default. Dragon Dance plus Rock/Dark/Ground
  coverage can punish a team that spends its Fighting/Ground/Water answer too
  early.

- The Houndoom answer if it is separate. A Water answer is not automatically a
  Houndoom answer once sun and SolarBeam are live.

Piece that can be spent:

- A sleep absorber or Gengar pressure piece whose later jobs are redundant, as
  long as the remaining team still covers Tyranitar and Houndoom.

- A poisoned or confused pivot only if it creates clean entry before Crobat's
  clock or Murkrow's Pursuit pressure makes the route worse.

Worst plausible branch:

- The player leads the only Tyranitar answer, Gengar sleeps it or sets Spikes,
  Donphan erases the player's hazard/setup route, Crobat blocks status with
  Safeguard, Murkrow punishes the forced switch with Pursuit, and Houndoom or
  Tyranitar converts once the correct answer is disabled.

Abandon conditions:

- The only Tyranitar or Houndoom answer is asleep, poisoned, confused, trapped,
  or below its required threshold.
- Donphan can Rapid Spin or Roar without giving up decisive pressure.
- Crobat's Safeguard is active and the plan depends on status.
- Murkrow's Pursuit makes switching worse than staying, attacking, or
  sacrificing a different piece.
- Tyranitar has boosted and the Speed/damage map no longer holds.
- Houndoom has sun active and the intended answer loses to boosted Flamethrower
  or one-turn SolarBeam.
- Type-chart, passive, item, weather, or damage evidence contradicts the
  assumed route.

What information would flip the lead or first move:

- A lead that can punish Gengar while remaining expendable after sleep.
- A separate confirmed Tyranitar answer, making the lead less fragile to
  Hypnosis.
- Damage evidence showing Houndoom is or is not forced before Sunny Day.
- Whether the user's Houndoom answer survives SolarBeam under sun.
- Whether the player's hazards matter enough that Donphan must be denied early.
- Whether Safeguard blocks the user's intended status route at the relevant
  turn.
- Whether Pursuit damage on a switch is worse than staying in and taking the
  visible attack.

## Extracted Lesson

Karen is not "beat Dark types." Karen is clock ownership under disruption. The
player has to decide which clock matters first: sleep, Spikes, Pursuit,
Safeguard, Dragon Dance, or sun. The right move is the one that keeps the
Tyranitar and Houndoom answers live while denying Karen's current clock from
becoming the next route.
