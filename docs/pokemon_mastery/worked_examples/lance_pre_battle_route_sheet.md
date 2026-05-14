# Worked Example: Lance Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Lance as a multi-wave setup denial
fight. This is a team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `ChampionGroup` / `LANCE`.
- Boss route map: `../boss_route_maps/lance_turn1_route_sheet.md`.
- Dragon Dance, Outrage, Hyper Beam, Quiver Dance, Focus Band, Leftovers,
  Magnet, Metal Coat, and priority references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Outrage effective-category source:
  `engine/battle/type_passive_damage_mods.asm`.

Expert study anchors:

- Setup-sweeper material: Dragon Dance matters because it fixes both power and
  Speed; giving a free turn to the wrong user can decide the game.
- Dragon-type material: Dragon routes are often dangerous because one locked
  attack or boosted attacker can force narrow defensive answers.
- Kingdra/Dragonite strategic notes: bulky Dragon Dance routes can sweep after
  checks are softened, and Dragonite-style endgames often demand preserving a
  late answer rather than spending it early.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Lance

Known boss roster:
  Steelix / Gyarados / Ampharos / Yanma / Kingdra / Dragonite

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include at least one final Dragonite denial route and separate answers
  to boosted Gyarados/Kingdra or proof that one answer covers both

Our one-time resources:
  unknown

Known romhack deltas that matter:
  Dragon Dance raises the user's current higher offensive stat plus Speed,
  Outrage can be physical for Dragon-typed users when current Attack exceeds
  current Special Attack, Hyper Beam is physical 180 BP with recharge,
  Quiver Dance raises Special Attack / Special Defense / Speed, Focus Band can
  preserve Yanma at 1 HP, and several Lance species have changed local typings

Missing evidence:
  exact player team, HP, levels, moves, items, speed relations, damage ranges,
  passive type states, whether status can land, and whether the same answer
  survives both Gyarados/Kingdra midgame and Dragonite endgame
```

## Output Shape

Primary route:

- Deny Lance's first setup wave without spending the final Dragonite answer.

Backup route:

- If a Dragon Dance or Quiver Dance lands, shorten the fight immediately around
  phazing/Haze, status, forced Outrage, Hyper Beam recharge, priority/revenge,
  or a controlled sacrifice. Do not continue a slow damage plan after Speed has
  changed.

Boss route priority:

```text
immediate:
  Steelix Dragon Dance if the lead cannot punish it.
  Yanma Sleep Powder or Quiver Dance if it can enter before sleep/status is
  accounted for.

accumulating:
  Gyarados Dragon Dance plus Hydro Pump / Outrage / Hyper Beam.
  Ampharos Dragon Dance as a likely special-plus-Speed route.
  Kingdra Dragon Dance plus mixed Water/Ice/Outrage pressure.

endgame:
  Dragonite Dragon Dance into Outrage / Earthquake / Hyper Beam.
  Any surviving boosted Dragon user after the player's phazer/status/revenge
  route has been spent.
```

Boss route to deny first:

- Deny the setup route that would consume the same answer needed for
  Dragonite. If the user's only Dragonite answer must also check Gyarados or
  Kingdra, preserve it and find a different way to pressure Steelix.

Boss route that can be delayed:

- Steelix can sometimes be delayed if it has been prevented from boosting or
  if the user's lead forces enough damage/status while preserving the later
  Dragon answers.

- Ampharos can be delayed only if its Dragon Dance boost and Magnet Thunder
  are covered by a special answer. Do not send a physical wall just because the
  move name is Dragon Dance.

Best lead profile:

- A lead that pressures Steelix immediately, denies or punishes Dragon Dance,
  and does not have to be preserved as the final answer to Gyarados, Kingdra, or
  Dragonite.

Avoid as lead:

- The only phazer, Haze user, Ice-route attacker, status route, or revenge
  piece needed for Dragonite.
- A slow setup Pokemon that gives Steelix the first Dragon Dance.
- A status-only plan that loses if Yanma later uses Sleep Powder first.
- A type-slogan answer that ignores local Steel/Dragon, Water/Dragon,
  Electric/Dragon, Bug/Dragon, Outrage category, or type-passive evidence.

First move plan:

- Give turn 1 one job: stop Steelix from making the rest of the fight faster
  and stronger while reserving the final anti-Dragon route.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Steelix's Dragon Dance, Earthquake, Iron Tail, and Outrage branches.

Turn 2:
  If Steelix boosted, choose the denial line now. If Steelix did not boost,
  preserve the Dragonite answer and prepare for Gyarados, Ampharos, Yanma, or
  Kingdra.

Turn 3:
  Re-score based on the first setup wave that appears: Dragon Dance user,
  Quiver Dance Yanma, Sleep Powder branch, Outrage lock, or Hyper Beam burst.
```

Piece to preserve:

- The Dragonite denial route by default. Lance's earlier Pokemon are dangerous,
  but spending the final anti-Dragonite piece early can make a won opening
  collapse later.

- The Gyarados/Kingdra answer if it is not the same as the Dragonite answer.
  These routes can demand different defensive stats because Outrage category
  and local Dragon Dance behavior are state-dependent.

Piece that can be spent:

- A Steelix pressure piece whose later jobs are redundant after Steelix is
  denied, or a controlled sacrifice that forces a boosted attacker into
  revenge range. Low HP alone is not enough.

Worst plausible branch:

- The player wins or trades with Steelix by using the only anti-setup answer,
  then Gyarados or Kingdra gets Dragon Dance. The player improvises with a
  type-slogan pivot, Yanma steals a turn with Sleep Powder or Focus Band, and
  Dragonite arrives after the real phaze/status/revenge route is gone.

Abandon conditions:

- Any Lance Pokemon gains Speed and now outspeeds the intended answer.
- The intended Dragonite, Gyarados, or Kingdra answer is asleep, chipped, or
  already spent.
- Yanma lands Sleep Powder or survives through Focus Band.
- Outrage category evidence contradicts the assumed defensive stat.
- Hyper Beam creates a KO instead of a punishable recharge turn.
- Type-chart, passive, item, or damage evidence contradicts the assumed route.

What information would flip the lead or first move:

- A lead candidate that can deny Steelix and remain a valid Dragonite answer.
- A separate confirmed Dragonite answer, making the Steelix answer more
  spendable.
- Damage evidence showing a boosted Gyarados or Kingdra no longer survives the
  intended revenge line.
- Speed evidence showing one Dragon Dance changes or does not change the
  relevant order.
- Outrage category evidence for each current attacker.
- Whether a phaze/Haze/status route is accurate, legal, and fast enough after a
  boost.

## Extracted Lesson

Lance is not "use Ice against Dragons." Lance is answer budgeting against
serial setup. The player must stop the current Dragon Dance or Quiver Dance
without spending the answer needed for the next one, and every move must be
checked against the local Dragon Dance and Outrage-category fork.
