# Lance Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; local Steelix is
  Steel/Dragon, Gyarados is Water/Dragon, Ampharos is Electric/Dragon, and
  Yanma is Bug/Dragon.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Lance as adaptive first-three: Steelix / Gyarados / Ampharos.
- Dragon Dance source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  this hack boosts the user's current higher offensive stat plus Speed.
- Outrage source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`,
  `data/moves/moves.asm`, and `engine/battle/type_passive_damage_mods.asm`;
  local Outrage is 100 BP and can use the physical category only for
  Dragon-typed users whose current Attack is greater than current Special
  Attack.
- Rampage source: `engine/battle/effect_commands.asm`; Outrage-style rampage
  lasts 2-3 total turns and then can confuse.
- Quiver Dance source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  it raises Special Attack, Special Defense, and Speed.
- Hyper Beam source: `data/moves/moves.asm` and
  `engine/battle/effect_commands.asm`; local Hyper Beam is physical, 180 BP,
  90 accuracy, and sets the recharge substatus.
- Focus Band, Leftovers, Magnet, and Metal Coat behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert principle sources: Smogon setup-move, Kingdra, Dragon Dance, and
  long-game route-planning material.

Boss roster:

```text
Lv46 Steelix @ Metal Coat:
  Earthquake / Iron Tail / Outrage / Dragon Dance

Lv49 Gyarados @ Leftovers:
  Dragon Dance / Outrage / Hydro Pump / Hyper Beam

Lv47 Ampharos @ Magnet:
  Thunder / Outrage / Fire Punch / Dragon Dance

Lv46 Yanma @ Focus Band:
  Quiver Dance / Outrage / Giga Drain / Sleep Powder

Lv49 Kingdra @ Leftovers:
  Surf / Outrage / Blizzard / Dragon Dance

Lv50 Dragonite @ Leftovers:
  Dragon Dance / Outrage / Earthquake / Hyper Beam
```

Boss likely openings:

- Lance is source-listed as adaptive first-three, not fixed Steelix.
- Plan for Steelix / Gyarados / Ampharos, with Steelix favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Lance's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Steelix route:

- Goal: use huge physical bulk and local Steel/Dragon typing to buy Dragon
  Dance turns, then pressure with Earthquake, Iron Tail, or Outrage.
- What it punishes: vanilla Steelix assumptions, slow setup leads, and spending
  the only Dragon Dance answer before the rest of Lance's team appears.
- Denial idea: pressure Steelix without emptying the anti-setup toolbox. If it
  uses Dragon Dance, count the local stat boost and new Speed relation rather
  than assuming a generic +Attack sweeper.

Gyarados route:

- Goal: use Dragon Dance and Leftovers to turn Outrage, Hydro Pump, or Hyper
  Beam into a breaker route.
- What it punishes: using the Water/Dragon answer too early, ignoring Hyper
  Beam's physical burst, or assuming Outrage remains special when Gyarados has
  higher Attack.
- Denial idea: preserve the piece that stops boosted Gyarados or force it into
  an Outrage/Hyper Beam commitment that can actually be punished.

Ampharos route:

- Goal: use Electric/Dragon typing, Magnet Thunder, Fire Punch, Outrage, and
  Dragon Dance as a special-side setup threat.
- What it punishes: assuming Dragon Dance always means Attack, and pivoting a
  Steel/Grass/Ice-style answer without checking Fire Punch and Thunder damage.
- Denial idea: after Dragon Dance, treat Ampharos as likely gaining Special
  Attack plus Speed from its current stat profile. Re-score special bulk and
  Thunder accuracy before choosing a pivot.

Yanma route:

- Goal: use Sleep Powder or Quiver Dance to create a fast special route, with
  Focus Band adding a small survival branch.
- What it punishes: status or setup plans that ignore sleep, and single-hit KO
  routes where Focus Band survival lets Yanma sleep or boost.
- Denial idea: decide whether sleep or Quiver Dance is the immediate danger. If
  Sleep Powder lands or Focus Band triggers, abandon the old KO script and
  rebuild from the actual state.

Kingdra route:

- Goal: use balanced bulk, Leftovers, Surf, Blizzard, Outrage, and Dragon Dance
  to become a special-leaning setup sweeper in this hack.
- What it punishes: assuming Kingdra is a simple physical Dragon Dance user,
  spending the special wall earlier, or letting it boost until Surf/Blizzard and
  Outrage all cross thresholds.
- Denial idea: preserve the Kingdra answer separately from the Dragonite answer.
  Local Dragon Dance and Outrage category rules make their damage profiles
  different.

Dragonite route:

- Goal: finish the fight with Dragon Dance, physical Outrage, Earthquake, and
  physical Hyper Beam.
- What it punishes: using the main Dragonite answer to handle earlier threats,
  letting Leftovers recover through weak chip, or failing to punish Outrage /
  Hyper Beam commitments.
- Denial idea: keep a final anti-Dragonite route alive: phazing/Haze, status,
  immediate Ice/special damage, priority/revenge, a controlled sacrifice, or
  forcing a locked move into a punishable target.

## Player Plan Template

Primary route:

- Lance is a multi-wave setup fight. The player must map which piece answers
  Steelix, Gyarados, Ampharos, Yanma, Kingdra, and Dragonite before spending any
  answer on the first good-looking exchange.

Backup route:

- If one Dragon Dance or Quiver Dance lands, shorten the plan. Identify whether
  the boosted attacker must be removed now, phazed/Hazed, statused, locked into
  Outrage, forced into Hyper Beam recharge, or traded against.

Best lead profile:

- A lead that pressures Steelix, does not let Gyarados start Dragon Dance for
  free, and does not mis-answer Ampharos's Thunder / Fire Punch / Dragon Dance
  profile. It must not be the only answer to Kingdra or Dragonite.
- It should either deny Dragon Dance immediately or create damage/status that
  still matters after the first opener switches or falls.

Avoid as lead:

- The only anti-Dragon Dance piece if Steelix can chip or force it out early.
- A slow setup lead that gives Steelix Dragon Dance.
- A status-only route if Yanma can take over the tempo with Sleep Powder.
- A plan that assumes all Outrage users hit the same defensive stat.

First-turn question:

```text
Which adaptive opener appeared?

Steelix: can we deny Dragon Dance without spending the Gyarados, Kingdra, or
Dragonite answer?

Gyarados: can we stop Dragon Dance, Outrage, Hydro Pump, or Hyper Beam from
turning the lead into a breaker route?

Ampharos: can our lead handle Thunder / Fire Punch / Outrage / Dragon Dance
without using the wrong defensive stat map?
```

If Steelix uses Dragon Dance:

- Re-score under local mechanics: current higher offensive stat plus Speed.
  Decide whether to attack, phaze/Haze, status, pivot, or sacrifice before the
  next hit opens the rest of Lance's route.

If Gyarados opens or enters, or Kingdra enters:

- Do not reuse one generic Water/Dragon answer without checking the exact move
  profile. Gyarados and Kingdra have different offensive stats, different
  damage categories for Outrage, and different likely boosted routes.

If Ampharos opens or uses Dragon Dance:

- Treat the boost as a special/speed threat unless current stat evidence says
  otherwise. A physical-wall pivot may not answer the boosted route.

If Yanma enters:

- Price both Sleep Powder and Quiver Dance. If the plan relies on one attack to
  KO, include the Focus Band branch before calling it stable.

If Outrage starts:

- Use the locked-move recipe. A locked target can sometimes be pivoted around,
  phazed, sacrificed into, or revenge killed, but only if the first hit does not
  remove an irreplaceable answer.

If Hyper Beam is used:

- Check whether the burst damage removes the answer or only creates a recharge
  window. Do not rely on the recharge window unless the user stays active and
  the player's next action actually converts.

Worst plausible branch:

- The player spends the anti-setup answer on Steelix, lets Gyarados or Kingdra
  get a Dragon Dance, uses status into Yanma's sleep tempo or Focus Band branch,
  and reaches Dragonite with no healthy phazer/Haze/status/revenge route left.

Abandon conditions:

- The intended answer to Dragonite, Kingdra, or Gyarados is asleep, chipped, or
  already spent.
- A Dragon Dance changes Speed order or damage thresholds enough that the old
  plan no longer works.
- Yanma has Quiver Dance or has put the wrong Pokemon to sleep.
- Outrage category evidence contradicts the assumed defensive answer.
- Hyper Beam creates a KO instead of a punishable recharge window.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Lance is the clearest anti-overfocus example. Snorlax itself is absent, but
  the GSC habit of preserving irreplaceable answers is everything here: every
  early trade must be judged by whether it leaves a route against the final
  boosted Dragonite and the midgame Dragon Dance users.
