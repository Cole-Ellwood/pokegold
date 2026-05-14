# Worked Example: Brock Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Brock as a hazard, recovery,
spin, setup, Explosion, contact-punish, and fast-cleaner fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `BrockGroup`.
- Boss route map: `../boss_route_maps/brock_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Recover, Protect priority, Curse, Swords Dance, Explosion, Roar timing,
  Rocky Helmet, Muscle Band, Leftovers, type-boost items, contact flags, and
  move category references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC Spikes material: hazards are strongest when they change switch
  cost, phazing value, recovery pressure, and endgame ranges.
- Smogon Explosion material: Golem's Explosion should be evaluated by the
  route it opens and the role the target still needed to perform.
- Smogon long-term thinking material: slow teams win by converting small
  resource edges into a later forced position, not by winning every exchange.
- Smogon Rock-type / Rock Slide material: Rock pressure often matters because
  it pairs damage, flinch risk, coverage, and forced switching with teammates
  that punish the answers.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Brock

Known boss roster:
  Omastar / Corsola / Golem / Kabutops / Onix / Aerodactyl

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a plan for Omastar Spikes, Corsola spin/recovery, Golem
  Curse/Explosion, Kabutops Swords Dance, Onix Spikes/Roar, and Aerodactyl
  cleanup; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Recover restoring 50%
  max HP, Protect / Detect using priority 3, Leftovers restoring 1/16 max HP,
  Muscle Band boosting physical damage by 1.1x, Rocky Helmet damaging contact
  attackers for max HP / 6, contact flags being move-specific, Explosion
  halving target Defense, and Roar using Gen 2-style timing

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, contact flags for the intended attacks,
  whether the lead can stop Omastar from getting Spikes plus Protect value,
  whether Corsola can Recover through the damage plan, whether Golem's
  Explosion removes a critical answer, and whether Aerodactyl outspeeds and
  cleans after hazard/status chip
```

## Output Shape

Primary route:

- Prevent Brock from owning the long-game clock. Omastar and Onix can start
  Spikes pressure, Corsola can remove the player's hazards and reset with
  Recover, Golem can turn one opening into Curse or Explosion value, Kabutops
  can punish a free turn with Swords Dance, and Aerodactyl can clean after the
  answers have been chipped.

Backup route:

- If Brock gets Spikes or Corsola stabilizes the hazard/recovery loop, shorten
  the battle. Prefer concrete KO thresholds, status/control, phazing/Haze,
  safe sacrifice, or preserving only the pivots that still matter over slow
  switching.

Boss route priority:

```text
immediate:
  Omastar Spikes if the lead cannot pressure it.
  Golem Explosion if it can remove the current route piece.
  Kabutops Swords Dance if no immediate denial route remains.

accumulating:
  Corsola Rapid Spin plus Recover if the player's hazard route is central.
  Corsola Toxic if it puts an irreplaceable answer on a clock.
  Onix Spikes / Roar with any layer active.
  Omastar Protect plus Leftovers if weak damage is the only plan.

endgame:
  Aerodactyl cleanup after Spikes, Toxic, Rock Slide, or Explosion chip.
  Kabutops cleanup after Swords Dance and Muscle Band damage.
  Golem if Curse makes direct damage stop crossing useful thresholds.
```

Boss route to deny first:

- Deny the route that makes the player's later answers stop entering safely.
  Against Brock, this is often Omastar's first Spikes turn or Golem's
  Explosion target, not the active damage race.

Boss route that can be delayed:

- Corsola can be delayed if the player's route does not depend on hazards and
  Toxic does not hit an irreplaceable answer. If hazards or a clean pivot loop
  are central, Corsola becomes urgent because Recover and Rapid Spin erase weak
  progress.

- Aerodactyl can be delayed while the dedicated answer is healthy and not
  statused. It cannot be delayed once Spikes, Toxic, or Golem Explosion makes
  that answer unreliable.

Best lead profile:

- A lead that pressures Omastar immediately without being the only answer to
  Golem, Kabutops, or Aerodactyl. It should either deny Spikes, punish Protect
  and weak recovery loops, or create a clean handoff into a route that does not
  need repeated grounded switching.

Avoid as lead:

- A passive setup lead that lets Omastar set Spikes or Golem/Kabutops boost.
- A hazard lead if Corsola can spin for free.
- A contact-dependent attacker into Golem before Rocky Helmet and contact flags
  are checked.
- The only Aerodactyl answer if Omastar, Corsola, or Golem can chip, poison, or
  trade it before the endgame.
- A type-slogan Water/Grass/Ground plan that has not been checked against local
  type/passive/item/damage evidence.

First move plan:

- Give turn 1 one job: stop Omastar from making Brock's later turns better.
  Attacking is good if it forces Omastar below a meaningful threshold, denies
  Spikes pressure, or makes Protect/Leftovers insufficient. Setting hazards is
  good only if Corsola cannot remove them without cost.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Omastar's Spikes, Protect, Surf, and Ice Beam branches against the
  lead's later role.

Turn 2:
  If Spikes landed, rebuild around grounded switch cost, Corsola spin access,
  Onix Roar, and Aerodactyl cleanup. If Omastar was denied, prepare for
  Corsola recovery/spin or a setup/trade route from Golem or Kabutops.

Turn 3:
  Start the ledger: Spikes layers, Corsola Recover/Rapid Spin access, Golem
  Explosion availability, Rocky Helmet contact risk, Kabutops boost state,
  Onix Roar routes, and Aerodactyl speed/endgame thresholds.
```

Piece to preserve:

- The Aerodactyl answer by default. It may not be urgent on turn 1, but the
  entire long-game can be lost if this piece is poisoned, chipped by hazards,
  or traded by Golem before Aerodactyl appears.

- The Golem/Kabutops denial piece if it is separate. Curse, Swords Dance, and
  Explosion demand different answers from a generic Rock-check label.

- The hazard-control or hazard-punish piece if the user's route needs repeated
  pivots.

Piece that can be spent:

- A lead that has already denied Omastar and has no unique job against Corsola,
  Golem, Kabutops, Onix, or Aerodactyl.

- A hazard setter after its layers have forced the needed threshold and
  Corsola cannot freely erase the route.

Worst plausible branch:

- The player lets Omastar start Spikes, fails to punish Corsola's
  Rapid Spin/Recover loop, uses contact damage into Rocky Helmet without
  pricing the recoil, then loses an irreplaceable answer to Golem Explosion or
  reaches Aerodactyl with the answer already chipped by hazards, Toxic, or
  Rock Slide.

Abandon conditions:

- Spikes are up and the current plan needs repeated grounded switching.
- Corsola can Recover or spin without giving up decisive pressure.
- Golem can Explode into an irreplaceable piece.
- Kabutops has boosted and no immediate denial, phaze/Haze, status, priority,
  sacrifice, or survival route remains.
- Aerodactyl can clean because the assigned answer is too low, statused, or
  slower than expected.
- Type-chart, passive, contact, item, Protect, recovery, or damage evidence
  contradicts the assumed answer.

What information would flip the lead or first move:

- Whether the lead can stop Omastar before Spikes or Protect value matters.
- Whether the player has a reliable way to punish Corsola's Rapid Spin and
  Recover turns.
- Whether the intended Golem answer uses contact and loses too much to Rocky
  Helmet.
- Whether Golem's Explosion removes the only Kabutops or Aerodactyl answer.
- Whether Kabutops reaches a winning range after one Swords Dance.
- Whether Aerodactyl outspeeds and KOs the planned endgame piece after one
  hazard entry.

## Extracted Lesson

Brock is not solved by "bring Water or Grass." Brock is a resource-conversion
fight: Omastar and Onix start the hazard clock, Corsola resets weak progress,
Golem converts one turn into Curse or Explosion, Kabutops punishes passive
turns with Swords Dance, and Aerodactyl tests whether the endgame answer was
preserved. The correct opening is the one that denies the first clock Brock can
actually convert.
