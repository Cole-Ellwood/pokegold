# Bugsy Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, and items are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Move table: `docs/agent_navigation/hack_mechanics_reference.md`
- Quiver Dance: +1 SpA / +1 SpD / +1 Spe in
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`
- Reflect: sets a 5-turn Reflect counter in
  `engine/battle/effect_commands.asm`
- Baton Pass source: `engine/battle/move_effects/baton_pass.asm`; the routine
  switches and resets non-passed temporary statuses such as attraction and
  disable, so do not assume those disrupt the next Pokemon after a pass.
- Player-availability checkpoint: `tools/boss_ai_preference/threat_availability.py`
  and `audit/boss_ai_preference/threat_availability_report.md` treat Bugsy as
  level cap 17, one badge, Old Rod available from
  `maps/Route32Pokecenter1F.asm`, and Surf not usable.
- Cyndaquil/Quilava source: `data/pokemon/evos_attacks.asm`; Ember is available
  by this checkpoint, but Fire Blast is not a natural Quilava move at cap 17
  and the TM source is later in `maps/GoldenrodGameCorner.asm`.
- Worked damage threshold note:
  `docs/pokemon_mastery/worked_examples/bugsy_scyther_answer_thresholds.md`

Boss roster:

```text
Lv15 Ariados @ BERRY:
  Poison Sting / Giga Drain / Toxic / Leech Life

Lv15 Ledian @ BERRY:
  Reflect / Quiver Dance / Leech Life / Baton Pass

Lv17 Scyther @ SILVERPOWDER:
  Swords Dance / Leech Life / Quick Attack / Wing Attack
```

## Boss Routes

Ariados route:

- Goal: start an early poison or drain clock, then soften the player team for
  Scyther.
- What it punishes: slow setup, low-damage chip, and teams that let Toxic land
  on the later Scyther answer.
- Denial idea: remove it or force it to spend turns healing before poison clock
  plus Scyther pressure combines. Do not spend the Scyther answer for minor
  Ariados chip unless the answer remains healthy enough afterward.

Ledian route:

- Goal: create screen turns, boost Speed and special bulk with Quiver Dance,
  then Baton Pass into the Pokemon that can convert the support.
- What it punishes: treating Ledian as harmless because its direct damage is low.
  A low-damage supporter can still be the most urgent target if it gives Scyther
  the safe turn it needs.
- Denial idea: direct KO, Haze/phazing if available and mechanically valid, or
  pressure that forces Ledian to pass before it has useful support. If Ledian
  already has Reflect and Speed, re-score before assuming the same answer still
  works.

Scyther route:

- Goal: convert with Swords Dance or take passed support, then use strong Bug
  or Flying pressure plus Quick Attack to finish weakened targets.
- What it punishes: using the early fight to trade away the one Pokemon that can
  survive or immediately remove Scyther.
- Denial idea: preserve the Scyther answer until its route is known. If Scyther
  enters without support and cannot KO before taking decisive damage, direct
  pressure can beat over-preservation. If it enters behind Reflect or with Speed
  support, ordinary chip may no longer be enough.

## Player Plan Template

Primary route:

- Stop Bugsy from converting support into Scyther. The fight is not only
  Ariados -> Ledian -> Scyther as separate one-on-ones; Ledian and Ariados can
  change what Scyther is allowed to do later.

Backup route:

- If a support turn lands, stop chasing the original one-on-one and rebuild the
  plan around the supported Scyther state: current HP, boosts, Reflect turns,
  priority ranges, and which answer still survives.

Best lead profile:

- A lead that pressures Ariados or Ledian without being the only Scyther answer.
  Early status or setup is good only if it prevents the support chain or creates
  a clear Scyther answer.
- Under the source-derived Bugsy checkpoint, do not plan around post-Bugsy
  access such as Goldenrod TMs or Surf. If the player has a Fire starter route,
  price the real available moves and levels, not a later Fire Blast plan.

Avoid as lead:

- The only Scyther answer if Ariados can poison it or Ledian can force it to
  absorb support turns.
- A passive setup lead that lets Reflect plus Quiver Dance happen before it
  changes a KO or denial threshold.
- A plan that saves all resources for Scyther while donating free turns to
  Ledian.

First-turn question:

```text
Does our first move stop Bugsy's support chain or preserve the piece that stops
the supported Scyther?
```

If yes:

- Take the action that changes the route fastest: KO, force recovery, status
  the correct target, deny Baton Pass, or pivot into the real Scyther answer.

If no:

- Reconsider the lead or accept a calculated risk only if safe play lets Ledian
  or Scyther set up anyway.

Worst plausible branch:

- The player spends their Scyther answer on Ariados or Ledian, Bugsy gets
  Reflect or Quiver Dance support, and Scyther enters against a team that can no
  longer remove it before it converts.

Abandon conditions:

- Ledian gets Quiver Dance or Reflect and can Baton Pass before being removed.
- Ariados poisons the planned Scyther answer.
- Scyther enters at high HP with support already active.
- Public damage shows the planned Scyther answer no longer survives boosted
  pressure or Quick Attack cleanup.
- Type-chart, passive, or item evidence contradicts the assumed matchup.

Snorlax study transfer:

- This is the opposite shape from many Snorlax anchor lessons. Bugsy is not a
  bulky Rest-cycle boss; the lesson is compound support. Still, the same route
  discipline applies: name the future converter, preserve the answer to it, and
  do not let a low-damage support turn become a hidden win condition.
