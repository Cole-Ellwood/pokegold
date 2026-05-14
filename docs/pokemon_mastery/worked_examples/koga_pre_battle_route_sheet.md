# Worked Example: Koga Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Koga as a poison, trap, hazard,
Haze, and coverage-clock fight. This is a team-agnostic planning artifact, not
final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `KogaGroup`.
- Boss route map: `../boss_route_maps/koga_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Spider Web / Mean Look, Haze, Pursuit, Moonlight, Toxic, Expert Belt,
  Leftovers, and Mint Berry references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Spikes material: hazards are route multipliers, not a win condition by
  themselves. They matter when they change switch cost, recovery timing,
  phazing value, or KO thresholds.
- GSC status material: poison is strongest with repeated switches and Spikes,
  but Toxic pressure must be aimed at targets whose timer changes the game.
- GSC Tentacruel material: Rapid Spin support is useful because it can erase
  hazard progress, but the spinner itself must still be priced by matchup and
  role.
- GSC Umbreon material: passive walls threaten through Toxic, Pursuit, trapping,
  confusion, recovery, and PP pressure; the answer is not always raw damage,
  but the player must avoid giving them free clocks.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Koga

Known boss roster:
  Ariados / Tentacruel / Muk / Nidoking / Umbreon / Crobat

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Nidoking answer, a Crobat answer, a Muk-break or Muk-reset
  route, and at least one Ariados-safe early plan; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Spider Web preventing
  normal switching, Haze resetting stat stages, Pursuit doubling on switching
  targets, Toxic counters resetting on switch, Moonlight depending on time and
  weather, Expert Belt requiring profile-specific type evidence, and Flying
  typing ignoring Spikes

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether the lead can remove Ariados
  before trap/status converts, whether the trapped Pokemon wins the locked
  exchange, and whether Tentacruel can spin or Haze safely
```

## Output Shape

Primary route:

- Keep switch freedom and answer integrity through the Ariados opening, then
  deny whichever Koga clock becomes live first: Tentacruel hazard control, Muk
  Curse/Rest, Nidoking coverage, Umbreon attrition, or Crobat cleanup.

Backup route:

- If Ariados lands Spikes, Toxic, or Spider Web, stop treating the battle as
  clean one-on-ones. Rebuild around layer count, toxic timer, trap state,
  grounded switch costs, and which Koga route now asks for the preserved answer.

Boss route priority:

```text
immediate:
  Ariados Spider Web if it can trap the only Nidoking, Muk, or Crobat answer.
  Ariados Toxic if it puts an irreplaceable answer on a clock.
  Nidoking coverage if the answer map is already exposed.

accumulating:
  Ariados Spikes into repeated grounded switching.
  Tentacruel Rapid Spin / Haze if the player's route depends on hazards or
  setup.
  Muk Curse / Rest if the player lacks immediate damage, phazing, Haze, or a
  Rest-punish plan.
  Umbreon Toxic / Confuse Ray / Moonlight / Pursuit attrition.

endgame:
  Crobat cleaning after poison, Spikes, and coverage chip.
  Nidoking breaking once the real pivot is trapped, poisoned, or revealed.
  Muk winning if the fight becomes low-damage and the Rest cycle is unpunished.
```

Boss route to deny first:

- Deny the route that removes switch freedom or poisons the only answer to the
  later breaker. Ariados is weak as a raw attacker, but Spikes/Toxic/Spider Web
  can decide whether Nidoking, Muk, Umbreon, or Crobat gets the exact game state
  it wants later.

Boss route that can be delayed:

- Tentacruel can be delayed if the player's route does not depend on hazards or
  boosts and if Surf/Sludge Bomb does not force the wrong pivot.

- Umbreon can be delayed if the current attacker either forces meaningful
  recovery pressure or uses the turn to stop a more urgent Koga clock. It
  cannot be delayed by a passive attacker that only lets Toxic, Confuse Ray,
  Moonlight, or Pursuit shape the next exchange.

Best lead profile:

- A lead that pressures Ariados without being the only Nidoking, Muk, or Crobat
  answer. It should either remove Ariados quickly, make Spider Web a bad trade,
  absorb Toxic without losing a critical role, or force Koga to answer before
  Tentacruel and Muk clocks become easy.

Avoid as lead:

- The only Nidoking or Crobat answer if Ariados can poison or trap it.
- A slow setup Pokemon whose boosts are erased by Tentacruel's Haze.
- A hazard lead if Tentacruel can spin for free and the team has no spin-punish
  plan.
- A passive special attacker that cannot hurt Umbreon and must switch through
  Pursuit.
- A type-slogan pivot into Nidoking before the romhack type chart, passives,
  Expert Belt, and damage ranges are checked.

First move plan:

- Give turn 1 one job: stop Ariados from converting weak immediate damage into
  long-game control. If the chosen move attacks, it should remove Ariados or
  force a worse Koga line. If it pivots, it should preserve an irreplaceable
  answer. If it sets up or sets hazards, it must survive Spider Web/Toxic and
  Tentacruel Haze/Spin branches.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Ariados's Spikes, Toxic, Spider Web, and Leech Life branches against
  the lead's later role.

Turn 2:
  If trapped or poisoned, decide whether the active wins the locked exchange or
  must be spent for immediate progress. If Ariados was denied, prepare for
  Tentacruel, Muk, Nidoking, Umbreon, or Crobat by route urgency.

Turn 3:
  Start the relevant ledger: Spikes layers, Toxic counter, trap state,
  Tentacruel spin/Haze access, Muk Curse/Rest count, Umbreon attrition, and
  Crobat/Nidoking damage thresholds.
```

Piece to preserve:

- The Nidoking answer by default, because Earthquake / Sludge Bomb / Ice Beam /
  Thunderbolt plus Expert Belt punishes casual type-slogan switching.

- The Crobat answer if the team is likely to be chipped by Spikes or poison.
  Crobat's cleanup route is strongest after earlier clocks have already made
  normal pivoting expensive.

- The Muk breaker or reset button if the team cannot otherwise beat Curse /
  Rest. Forcing Rest is only progress if the sleep turns are punishable.

Piece that can be spent:

- A lead or utility Pokemon that has already denied Ariados and is not needed
  for Nidoking, Muk, Umbreon, or Crobat.

- A poisoned or trapped Pokemon only if it creates a real route before the
  clock expires: removing Ariados, forcing Tentacruel, denying Muk setup, or
  giving clean entry to the actual converter.

Worst plausible branch:

- The player leads a critical answer into Ariados, gets trapped or poisoned,
  then tries a setup or hazard route that Tentacruel erases. Muk uses the
  downtime to enter Curse/Rest range, Umbreon stretches the fight with
  Moonlight/Toxic/confusion/Pursuit, and Crobat or Nidoking converts once the
  true answer is too chipped to function.

Abandon conditions:

- The only Nidoking or Crobat answer is poisoned, trapped, or below its required
  threshold.
- Tentacruel can Rapid Spin or Haze without giving up decisive pressure.
- Muk reaches a Curse/Rest loop that cannot be broken or punished.
- Umbreon turns the exchange into recovery plus status while the player makes
  no concrete progress.
- Crobat can clean with Wing Attack, Sludge Bomb, or Hyper Beam after prior
  chip.
- Type-chart, passive, item, or damage evidence contradicts the assumed pivot.

What information would flip the lead or first move:

- Damage evidence showing the lead can or cannot remove Ariados before
  Spikes/Toxic/Spider Web matters.
- Whether the lead is expendable after absorbing Toxic or trap.
- Whether the intended setup route loses to Tentacruel Haze.
- Whether the hazard route still matters if Tentacruel can spin all layers.
- Whether the Nidoking answer survives the correct coverage move after Expert
  Belt and romhack type/passive evidence.
- Whether Crobat can be held for later or must be denied immediately.
- Whether Muk is breakable before Rest or must be phazed, Hazed, statused, or
  forced into an exploitable sleep cycle.
- Whether Umbreon can actually threaten the current active, or whether it is
  giving the player a safe turn to attack a more urgent route.

## Extracted Lesson

Koga is not "bring Psychic" or "beat Poison types." Koga is clock ownership and
switch-freedom preservation. Ariados tries to make the rest of the fight happen
on Koga's terms; Tentacruel erases slow progress; Muk, Umbreon, Nidoking, and
Crobat each punish a different kind of overcommitment. The right opening is the
one that keeps the real answers live while preventing Koga's first weak-looking
turn from becoming the route that wins the battle.
