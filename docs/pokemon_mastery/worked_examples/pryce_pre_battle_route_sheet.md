# Worked Example: Pryce Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Pryce as a hazard-control,
Explosion, Encore, phazing, fast-cleaner, and bulky-Rest fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `PryceGroup`.
- Boss route map: `../boss_route_maps/pryce_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Encore, Explosion, Rest, Roar timing, type categories, Blackglasses,
  NeverMeltIce, Soft Sand, Leftovers, Ice-type passive, and local type-chart
  notes:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Cloyster material: Cloyster's Spikes create progress for offensive
  teammates, while Explosion lets it trade after the hazard job or stop a
  dangerous route.
- GSC Explosion material: Explosion is a route trade, not just a damage button;
  the target removed and the route opened must justify losing the user.
- GSC Spikes material: hazards need support, retention, spin pressure, or
  conversion through phazing, status, Rest pressure, or direct thresholds.
- Encore/control material: locking a support or setup move can force a switch
  or create a safe punishment window, so sequence matters before clicking a
  non-attacking move.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Pryce

Known boss roster:
  Cloyster / Dewgong / Sneasel / Piloswine / Slowking

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a plan for Cloyster Explosion, an answer to Sneasel cleanup, a
  Piloswine answer checked against local type evidence, and a way to pressure
  Slowking's Thunder Wave / Rest loop; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Encore lasting 3-6 turns,
  Explosion halving target Defense and fainting the user, Rest creating a sleep
  window, Roar using Gen 2-style timing, Dark and Ice being special, Ghost being
  physical, Blackglasses / NeverMeltIce / Soft Sand boosting their types by
  1.2x, Ice defender passive reductions, Water hitting Ice for 0.5x in this
  hack, and Fire being only 2x into Ice/Ground Piloswine

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether Cloyster's Explosion removes a
  critical answer, whether Dewgong can spin or Encore safely, and whether
  Slowking can Rest without being punished
```

## Output Shape

Primary route:

- Decide who owns the hazard clock before Pryce's midgame pieces arrive. If
  Cloyster gets Spikes and Dewgong controls Rapid Spin, the player must either
  remove the layer, punish spin, or shorten the fight before Piloswine Roar,
  Sneasel priority, and Slowking paralysis/Rest convert the chip.

Backup route:

- If hazards cannot be removed, stop playing for repeated pivots. Preserve the
  Sneasel and Piloswine answers, avoid donating a key piece to Explosion, and
  force Slowking's Rest only when the sleep turns create a real punish.

Boss route priority:

```text
immediate:
  Cloyster Spikes if the user's team is grounded and pivot-heavy.
  Cloyster Explosion if it removes the only Piloswine, Sneasel, or Slowking
  answer.
  Dewgong Encore if the user's last move was setup, recovery, hazards, or a
  low-value support move.

accumulating:
  Dewgong Rapid Spin if the user's own hazard route matters.
  Piloswine Roar with Spikes active.
  Slowking Thunder Wave if it removes speed control or enables Sneasel cleanup.

endgame:
  Sneasel cleaning with special Dark/Ice damage, physical Shadow Ball, and
  Quick Attack after hazard chip.
  Piloswine forcing coverage trades after the real pivot is low.
  Slowking stabilizing with Leftovers and Rest if the player cannot punish the
  sleep turns.
```

Boss route to deny first:

- Deny the route that makes the answer map collapse. Against a grounded team,
  early Spikes may be the first route. Against a team with one key defender,
  Cloyster's Explosion may be more urgent. Against a setup or hazard plan,
  Dewgong's Encore or Rapid Spin may be the route that invalidates the opening.

Boss route that can be delayed:

- Cloyster can be delayed after Spikes only if Explosion no longer removes a
  critical answer and the team can manage the hazard clock.

- Slowking can be delayed if Thunder Wave does not matter and the player can
  force or punish Rest. It cannot be delayed when paralysis changes Sneasel or
  Piloswine endgame math.

Best lead profile:

- A lead that pressures Cloyster without being the only answer to Piloswine or
  Sneasel. It should either prevent a free layer, make Explosion a poor trade,
  or create immediate pressure that forces Pryce away from the hazard plan.

Avoid as lead:

- The only Sneasel or Piloswine answer if Cloyster can trade Explosion into it.
- A hazard lead if Dewgong can spin all layers without cost.
- A setup or recovery lead that lets Dewgong enter and Encore the support move.
- A Water or Fire plan that relies on vanilla type memory against Ice/Ground or
  Water/Ice instead of local type evidence.
- A passive special attacker that lets Slowking paralyze, Rest, or pivot into
  the endgame without losing a concrete resource.

First move plan:

- Give turn 1 one job: stop Cloyster from converting its lead position into
  both hazards and a later Explosion trade. If attacking, the damage should
  change Cloyster's layer or boom freedom. If pivoting, the pivot must not be
  the only later answer. If setting hazards, the plan must say how Dewgong's
  Rapid Spin is punished.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Cloyster's Spikes, Surf, Ice Beam, and Explosion branches against the
  lead's later role.

Turn 2:
  If Spikes landed, rebuild around grounded switch cost, Dewgong spin access,
  and Cloyster's remaining Explosion value. If Cloyster was denied, prepare for
  Dewgong Encore/spin, Sneasel cleanup, Piloswine Roar, or Slowking paralysis.

Turn 3:
  Start the relevant ledger: Spikes layers on both sides, Rapid Spin access,
  Encore target and turns, Explosion availability, Piloswine Roar routes,
  Slowking Rest timing, Thunder Wave state, and type-evidence assumptions.
```

Piece to preserve:

- The Piloswine answer after local type checking. Fire into Piloswine is 2x,
  not 4x, and Water is not automatically the clean answer because Water into
  Ice is reduced in this hack.

- The Sneasel answer if hazards or paralysis are accumulating. Sneasel's Quick
  Attack means low HP matters even if the player is faster.

- The Slowking breaker or Rest-punish route if the team otherwise stalls out
  into Thunder Wave plus recovery.

Piece that can be spent:

- A lead that already forced Cloyster's hazard or Explosion trade and is not
  needed for Sneasel, Piloswine, or Slowking.

- A paralyzed or Encored utility piece only if spending it gives clean entry to
  a route that wins before the hazard and Rest clocks matter.

Worst plausible branch:

- Cloyster sets Spikes and keeps Explosion available, Dewgong spins away the
  player's own layers or Encores a setup/recovery turn, Piloswine Roars through
  hazard damage, Slowking spreads Thunder Wave and Rests off chip, and Sneasel
  cleans once the real answer has been weakened.

Abandon conditions:

- Cloyster's Explosion can remove an irreplaceable piece.
- Dewgong can Rapid Spin for free and the player's hazard route has no punish.
- Dewgong can Encore the last move into a losing sequence.
- The grounded core can no longer switch enough times through current Spikes.
- Piloswine has a live Roar plus hazard route.
- Slowking can Rest without the player gaining a concrete punish.
- The plan uses type words without checking the romhack chart, type passives,
  and item modifiers.

What information would flip the lead or first move:

- Damage evidence showing the lead can prevent Cloyster's first layer or force
  an early Explosion trade.
- Whether the player has a separate, expendable Explosion absorber.
- Whether Dewgong can spin all layers safely or must fear the immediate punish.
- Whether Encore can lock the player into a low-value move this turn.
- Whether Sneasel's priority range matters after Spikes or paralysis.
- Whether Piloswine's Fire/Water/Ground/Ice matchups are confirmed by local
  type evidence and damage.
- Whether Slowking's Rest turn is punishable or just resets damage while Pryce's
  hazard clock stays active.

## Extracted Lesson

Pryce is not "hit Ice with Fire." Pryce is a hazard-clock and sequence-control
fight. Cloyster asks whether the player can stop Spikes without losing a key
piece to Explosion, Dewgong punishes unsupported hazards and sloppy setup with
Rapid Spin or Encore, Piloswine turns hazards into Roar progress, Slowking tests
whether damage actually converts through Rest, and Sneasel cashes out the chip.
The right opening is the one that prices the first layer, the boom trade, and
the Encore branch before committing to a long plan.
