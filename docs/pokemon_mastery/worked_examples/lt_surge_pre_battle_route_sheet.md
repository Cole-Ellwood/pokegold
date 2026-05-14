# Worked Example: Lt. Surge Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Lt. Surge as a support-chain,
speed-control, screen, spin, Explosion, and coverage fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `LtSurgeGroup`.
- Boss route map: `../boss_route_maps/lt_surge_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Air Balloon, Light Screen, Agility, paralysis tuning, Explosion,
  DynamicPunch, Cross Chop, DragonBreath, move categories, type-boost items,
  Expert Belt, and type-chart references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Smogon GSC status material: paralysis is route control, not just annoyance;
  it is strongest when it disables the piece that needed Speed or reliability
  for a later win condition.
- Smogon speed-control material: controlling move order can preserve good
  matchups and turn bad ones, but the value depends on which attacker benefits.
- Smogon Explosion material: Explosion is a one-time route trade; Magneton and
  Electrode should be priced by what their trade opens, not by damage alone.
- GSC Spikes material: hazards become progress only when switch cost changes
  answer durability, phazing, recovery, or endgame ranges.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Lt. Surge

Known boss roster:
  Magneton / Electrode / Raichu / Electabuzz / Ampharos

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a plan for Air Balloon Magneton, an Explosion absorber or
  acceptable trade target, a Raichu answer after Agility, an Electabuzz coverage
  answer, and a way to handle five-turn Light Screen; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Air Balloon making Ground
  attacks no-effect until popped by direct damage, local screens lasting five
  turns, Agility as the local single-stat +Speed move, Fighting-type-tuned
  paralysis penalties, Electric-type paralysis blocking, Explosion halving
  target Defense, Expert Belt requiring matchup evidence, and Raichu /
  Electabuzz being Electric/Fighting while Ampharos is Electric/Dragon

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether the lead can pop Air Balloon
  without losing its later job, whether Magneton or Electrode Explosion removes
  an irreplaceable answer, whether Light Screen changes the needed attacking
  category, and whether Agility Raichu outspeeds and KOs after one turn
```

## Output Shape

Primary route:

- Stop Surge from converting support into a coverage sweep. Magneton can use
  Air Balloon to buy a turn for Spikes, Thunder Wave, or Explosion. Electrode
  can set Light Screen, remove hazards, or trade with Explosion. Raichu,
  Electabuzz, and Ampharos then punish a player whose speed-control piece,
  coverage answer, or Explosion absorber was spent too early.

Backup route:

- If Air Balloon blocks the first plan, Thunder Wave hits the speed-control
  piece, or Light Screen goes up, rebuild immediately. The backup route should
  name which of these clocks matters most: balloon state, screen turns,
  paralysis state, hazard layers, Electrode spin access, or Agility Raichu.

Boss route priority:

```text
immediate:
  Magneton Thunder Wave if it cripples the Raichu / Electabuzz answer.
  Magneton or Electrode Explosion if it removes an irreplaceable piece.
  Raichu Agility if no denial or revenge route remains.

accumulating:
  Magneton Spikes into repeated grounded switching.
  Electrode Light Screen protecting the special route for five turns.
  Electrode Rapid Spin if the player's plan depends on hazards.
  Ampharos DragonBreath or Thunderbolt pressure plus Light Screen support.

endgame:
  Agility Raichu cleaning after the answer is paralyzed or chipped.
  Electabuzz coverage plus DynamicPunch confusion if the pivot map is thin.
  Ampharos forcing progress once special pressure is protected by screen.
```

Boss route to deny first:

- Deny the route that damages or disables the only answer to Surge's coverage
  attackers. Often this is Thunder Wave or Explosion on the piece meant to
  handle Raichu/Electabuzz, not the first Thunderbolt.

Boss route that can be delayed:

- Magneton Spikes can be delayed if the player has few grounded switch needs,
  can punish Electrode's spin, or can shorten the fight. It cannot be delayed
  if the team's answer map requires repeated pivoting.

- Light Screen can be delayed only if the player's route attacks through a
  different category, uses status/control, or can wait out five turns without
  losing to Raichu, Electabuzz, or Ampharos.

Best lead profile:

- A lead that pressures Magneton without being stopped by Air Balloon and
  without being the only answer to Raichu or Electabuzz. The lead should either
  pop Balloon safely, deny Thunder Wave on an irreplaceable piece, punish
  Spikes, or make Explosion a poor trade for Surge.

Avoid as lead:

- A Ground-only opener whose first plan fails while Air Balloon is intact.
- The only Raichu or Electabuzz answer if Magneton can paralyze or Explode on
  it.
- A hazard lead if Electrode can spin for free.
- A special-only pressure lead if Light Screen goes up without a punish.
- A route that relies on generic Electric matchup memory instead of local
  type/passive/damage evidence for Electric/Fighting and Electric/Dragon
  attackers.

First move plan:

- Give turn 1 one job: prevent Magneton from buying the support turn that makes
  the rest of Surge's team better. Attacking is good if it pops Air Balloon,
  blocks a status/Explosion trade, or changes the hazard clock. Switching is
  good only if it preserves the later route while still answering Magneton's
  best branch.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Magneton's Spikes, Thunder Wave, Thunderbolt, and Explosion branches
  against the lead's later role.

Turn 2:
  If Air Balloon is still intact, stop using a Ground-only plan. If paralysis
  or Spikes landed, rebuild around the specific piece or switch loop that was
  damaged.

Turn 3:
  Start the ledger: Air Balloon state, Spikes layers, Light Screen turns,
  Electrode spin/Explosion availability, Raichu Speed boosts, and whether
  Electabuzz or Ampharos coverage now invalidates the expected pivot.
```

Piece to preserve:

- The Raichu answer by default. Once Agility happens, revenge-by-Speed may stop
  being a plan, so the answer must survive by bulk, priority, phazing/Haze,
  status, or a forced trade.

- The Electabuzz coverage answer if it is separate. ThunderPunch, Ice Punch,
  Fire Punch, and DynamicPunch punish different pivots; the plan needs damage
  evidence, not a one-word matchup label.

- Any status absorber or status-indifferent piece assigned to take Thunder Wave
  without killing the user's own win route.

Piece that can be spent:

- A lead that has already popped Air Balloon or denied Magneton's support turn
  and has no unique job against Raichu, Electabuzz, Ampharos, or Electrode.

- A hazard setter only if the team no longer needs hazards or can punish
  Electrode's Rapid Spin without that setter.

Worst plausible branch:

- The player opens with a Ground-only plan into Air Balloon, Magneton sets
  Spikes or paralyzes the key answer, Electrode sets Light Screen or removes
  the player's hazards, Magneton/Electrode trades Explosion into the wrong
  target, and Raichu or Electabuzz cleans through the damaged answer map.

Abandon conditions:

- Air Balloon is intact and the current line depends on Ground damage.
- The assigned speed-control or Raichu answer is paralyzed.
- Light Screen is active and the current route depends on special damage.
- Electrode can remove the player's hazards without giving up a decisive
  punish.
- Magneton or Electrode can Explode into an irreplaceable piece.
- Raichu has used Agility and no immediate denial, phaze/Haze, status, priority,
  sacrifice, or survival route remains.
- Type-chart, passive, item, screen, or damage evidence contradicts the assumed
  answer.

What information would flip the lead or first move:

- Whether the lead can pop Air Balloon with low cost before using Ground
  damage.
- Whether the team has a separate Raichu answer, making the Magneton answer
  more spendable.
- Whether the intended Electabuzz pivot survives its coverage and
  DynamicPunch/confusion branch.
- Whether hazards are the player's real route or a distraction that Electrode
  can erase.
- Whether Light Screen changes the attacking category or only wastes
  Electrode's turn.
- Whether Explosion removes a route blocker for Surge or merely trades into an
  expendable piece.

## Extracted Lesson

Surge is not solved by "bring Ground." The first question is which support
effect lets the coverage attackers win: Air Balloon blocking the obvious line,
Thunder Wave removing Speed, Spikes taxing pivots, Light Screen buying five
turns, Rapid Spin erasing the user's hazard route, or Explosion deleting the
wrong answer. The correct opening denies the support link that makes Raichu,
Electabuzz, or Ampharos a real route.
