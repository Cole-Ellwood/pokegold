# Worked Example: Janine Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Janine as a poison, hazard, spin,
Haze, RestTalk, Explosion, sleep, and setup fight. This is a team-agnostic
planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `JanineGroup`.
- Boss route map: `../boss_route_maps/janine_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Haze, Rest, Sleep Talk, Sleep Powder, Quiver Dance, Explosion, Rocky Helmet,
  Expert Belt, Wise Glasses, Mystic Water, Leftovers, contact flags, and local
  type-chart references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC status material: poison matters when it changes a route clock,
  especially alongside switching pressure and Spikes; random Toxic is not
  automatically progress.
- Smogon GSC Spikes material: hazards need retention, spin punishment, or a
  concrete conversion route.
- Smogon Explosion material: Explosion is a route trade; Qwilfish and Weezing
  must be priced by what their fainting opens.
- Smogon setup material: sleep plus a multi-stat boost can create a sweeping
  route, but only if the sleep/wake, Haze, damage, and revenge branches are
  accounted for.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Janine

Known boss roster:
  Qwilfish / Tentacruel / Muk / Nidoking / Weezing / Venomoth

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Nidoking answer, a Venomoth anti-setup or revenge plan, a way
  to avoid losing a critical route piece to Explosion, and a hazard/spin plan
  if the team needs repeated switching; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Haze resetting both
  sides' stat stages, Rest plus Sleep Talk branches, Sleep Powder accuracy and
  Sleep Clause, Quiver Dance boosting Venomoth's special route and Speed,
  Explosion halving target Defense, Rocky Helmet punishing contact for max HP
  / 6, Expert Belt and Wise Glasses requiring item/damage evidence, and Weezing
  being local Poison/Dark rather than vanilla memory

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, contact flags for intended attacks,
  whether the lead can deny Qwilfish before Spikes or Explosion matters,
  whether Tentacruel can spin or Haze without cost, whether Muk's RestTalk loop
  can be converted, and whether Venomoth survives to boost after Sleep Powder
```

## Output Shape

Primary route:

- Keep the Nidoking and Venomoth answers intact while denying Janine's first
  clock. Qwilfish can start Spikes or trade Explosion, Tentacruel can erase
  hazards or boosts, Muk can reset through RestTalk, Weezing can trade into the
  wrong answer, and Venomoth can turn sleep into Quiver Dance pressure.

Backup route:

- If Qwilfish gets Spikes or Tentacruel resets the player's hazard/setup plan,
  shorten the fight around direct KOs, status/control, phazing/Haze, a planned
  sacrifice, or clean entry to the actual converter. Do not keep investing in
  a route that Tentacruel erases for free.

Boss route priority:

```text
immediate:
  Qwilfish Explosion if it removes the Nidoking or Venomoth answer.
  Venomoth Sleep Powder if the sleep target is the anti-setup piece.
  Venomoth Quiver Dance if no denial, phaze/Haze, status, or revenge route is
  available.

accumulating:
  Qwilfish Spikes into repeated grounded switching.
  Tentacruel Rapid Spin if the player's plan depends on hazards.
  Tentacruel Haze if the player's plan depends on boosts.
  Muk RestTalk if the player cannot punish the Rest cycle.

endgame:
  Nidoking coverage once the real pivot is chipped or removed.
  Weezing Explosion opening the route for Nidoking or Venomoth.
  Venomoth cleaning after sleep, Quiver Dance, and prior chip.
```

Boss route to deny first:

- Deny the route that removes the answer to Janine's actual converter. If the
  team has only one Venomoth answer, Qwilfish or Weezing Explosion into that
  piece may be more urgent than the first layer. If the team relies on hazards
  or setup, Tentacruel is the route piece that invalidates the plan.

Boss route that can be delayed:

- Muk can be delayed if the player can convert Rest turns or pressure it
  without contact recoil becoming relevant. It cannot be delayed if RestTalk
  lets Janine reset while the player's Nidoking/Venomoth answer is slowly
  losing HP or PP.

- Qwilfish's first layer can be delayed only when the team does not need a long
  grounded pivot loop and the Explosion branch has no valuable target.

Best lead profile:

- A lead that pressures Qwilfish without being the only Nidoking or Venomoth
  answer. It should either deny Spikes, make Explosion a poor trade, or force
  Janine into Tentacruel/Muk before those pieces can reset the player's main
  route for free.

Avoid as lead:

- A hazard lead if Tentacruel can spin for free.
- A setup lead if Tentacruel can Haze before the boost converts.
- A contact-heavy route into Muk before Rocky Helmet and contact flags are
  checked.
- The only Venomoth answer if Qwilfish or Weezing can trade Explosion into it.
- A generic Poison-answer plan that has not priced Nidoking's four-attack
  coverage and Weezing's local typing.

First move plan:

- Give turn 1 one job: deny Qwilfish from turning a weak-looking opening into
  Spikes plus Explosion pressure. Attacking is good if it changes the hazard or
  trade map. Switching is good only if it preserves the real Nidoking/Venomoth
  answer while still covering Qwilfish's best branch.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Qwilfish's Spikes, Sludge Bomb, Surf, and Explosion branches against
  the lead's later role.

Turn 2:
  If Spikes landed, rebuild around grounded switch cost and Tentacruel spin
  access. If Qwilfish was denied, prepare for Tentacruel Haze/spin, Muk
  RestTalk, Nidoking coverage, Weezing Explosion, or Venomoth sleep/setup.

Turn 3:
  Start the ledger: Spikes layers, Rapid Spin access, Haze access, RestTalk
  turns/branches, Explosion availability, Sleep Clause and sleeping roles,
  Venomoth boosts, and Nidoking coverage thresholds.
```

Piece to preserve:

- The Venomoth answer by default if Sleep Powder plus Quiver Dance can remove
  agency and speed control. This piece must survive both the sleep branch and
  the boosted-damage branch.

- The Nidoking answer if it is separate. Earthquake, Sludge Bomb, Ice Beam, and
  Thunderbolt demand actual type/passive/damage evidence for the current board.

- The Haze, phaze, or revenge piece that stops a boosted Venomoth after sleep
  or chip changes the board.

Piece that can be spent:

- A lead that has already denied Qwilfish and has no unique job against
  Nidoking, Venomoth, Muk, or Weezing.

- A hazard setter only if its layers already forced the needed route and
  Tentacruel cannot erase them without giving up decisive pressure.

Worst plausible branch:

- The player lets Qwilfish set Spikes, invests in hazards or boosts that
  Tentacruel resets, chips the wrong piece into Muk or Weezing, then loses the
  actual answer to Explosion, Sleep Powder, or Nidoking coverage before the
  endgame starts.

Abandon conditions:

- The only Nidoking or Venomoth answer is asleep, exploded on, poisoned, or
  below its required threshold.
- Tentacruel can Rapid Spin or Haze without giving up decisive pressure.
- Muk's RestTalk cycle cannot be punished before Janine's other routes improve.
- Weezing can Explode on an irreplaceable piece.
- Venomoth has boosted and no immediate denial, phaze/Haze, status, priority,
  sacrifice, or survival route remains.
- Type-chart, passive, contact, item, sleep, Haze, or damage evidence
  contradicts the assumed answer.

What information would flip the lead or first move:

- Whether the lead can remove or force Qwilfish before Spikes or Explosion
  matters.
- Whether the player has a second Venomoth answer, making the first one more
  spendable into Qwilfish or Weezing.
- Whether the hazard route still wins if Tentacruel spins once.
- Whether the setup route survives Tentacruel Haze.
- Whether Muk's Rocky Helmet punishes the intended contact attacker enough to
  break a later role.
- Whether Nidoking coverage reaches the planned pivot after Expert Belt and
  local mechanics are applied.

## Extracted Lesson

Janine is not solved by "bring a Psychic or Ground attacker." Janine is a
reset-and-trade fight. Qwilfish starts the clock or trades, Tentacruel erases
slow plans, Muk tests whether RestTalk can be converted, Weezing threatens the
one piece the plan still needs, Nidoking punishes lazy pivots, and Venomoth
turns sleep into a setup route. The right opening is the one that preserves the
actual Nidoking/Venomoth answers while denying the first reset or trade that
makes them fail.
