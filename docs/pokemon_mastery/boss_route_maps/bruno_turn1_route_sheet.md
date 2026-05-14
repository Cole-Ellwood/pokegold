# Bruno Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Bruno as adaptive first-three: Onix / Hitmontop / Hitmonlee.
- Priority source: `data/moves/effects_priorities.asm` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Mach Punch is +1
  priority in this hack.
- Critical-hit source: `data/battle/critical_hit_chances.asm`,
  `data/moves/critical_hit_moves.asm`, and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Cross Chop is a
  high-crit move, Focus Energy adds a crit stage, and Scope Lens adds a crit
  stage.
- Focus Band and type-boost item behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Vital Throw is `EFFECT_ALWAYS_HIT` in the local move table. It is not listed
  as a low-priority move in `data/moves/effects_priorities.asm`, so do not
  import modern negative-priority assumptions.
- Expert principle sources: Smogon Fighting move history, GSC Machamp, GSC
  Heracross, GSC Spikes, and GSC threat-list material.

Boss roster:

```text
Lv42 Onix @ Soft Sand:
  Spikes / Earthquake / Rock Slide / Roar

Lv42 Hitmontop @ Black Belt:
  Rapid Spin / Mach Punch / Rock Slide / Hi Jump Kick

Lv43 Hitmonlee @ Focus Band:
  Meditate / Hi Jump Kick / Rock Slide / Earthquake

Lv46 Machamp @ Leftovers:
  Cross Chop / Earthquake / Rock Slide / Vital Throw

Lv44 Hitmonchan @ Expert Belt:
  Ice Punch / Fire Punch / ThunderPunch / Mach Punch

Lv44 Heracross @ Scope Lens:
  Megahorn / Cross Chop / Rock Slide / Focus Energy
```

Boss likely openings:

- Bruno is source-listed as adaptive first-three, not fixed Onix.
- Plan for Onix / Hitmontop / Hitmonlee, with Onix favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Bruno's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Onix route:

- Goal: start Spikes, then use Roar plus Rock/Ground pressure to turn every
  later Bruno switch into chip and bad positioning.
- What it punishes: passive leads, setup leads that can be Roared out, and
  assuming Bruno is pure Fighting pressure with no hazard/phaze opening.
- Denial idea: pressure Onix before it gets both Spikes and phazing value.
  If Onix lays Spikes, immediately re-score grounded player Pokemon and whether
  a Flying pivot is actually safe into Rock Slide.

Hitmontop route:

- Goal: erase the player's hazard route with Rapid Spin, then threaten fast
  cleanup or revenge damage with Mach Punch while still carrying Fighting/Rock
  attacks.
- What it punishes: hazards without a spin punish, and faster attackers left in
  low enough for priority to finish.
- Denial idea: decide whether Hitmontop is currently a spinner, priority
  revenger, or direct attacker. The correct answer changes depending on whether
  the player's route needs hazards or only needs to preserve a cleaner.

Hitmonlee route:

- Goal: use Meditate or immediate high-power physical coverage to force the
  player to answer quickly, with Focus Band creating a small but real 1-HP
  survival branch.
- What it punishes: giving a free setup turn, relying on a single KO roll when
  Focus Band survival would be catastrophic, and pivoting into generic Fighting
  answers that lose to Rock Slide or Earthquake.
- Denial idea: if Hitmonlee boosts, abandon any slow plan and ask whether
  current damage, phazing/Haze, status, or sacrifice prevents the next hit from
  opening Bruno's endgame.

Machamp route:

- Goal: break the player's defensive map with huge physical damage, Cross Chop
  crit pressure, Rock Slide, Earthquake, and always-hit Vital Throw.
- What it punishes: "walling" by type slogan, letting the Fighting answer take
  prior Spikes or Rock Slide chip, and assuming boosted or defensive stats make
  the Cross Chop branch safe.
- Denial idea: preserve a verified Machamp answer until Machamp is removed or
  in guaranteed revenge range. If the answer depends on avoiding a crit, call
  that out as risk rather than a stable route.

Hitmonchan route:

- Goal: punish the expected Fighting answer with special elemental punches,
  then use Mach Punch to pick off weakened targets.
- What it punishes: bringing in a Flying, Psychic, or bulky pivot without local
  type-chart, passive, and damage evidence for Ice Punch, Fire Punch,
  ThunderPunch, and Expert Belt.
- Denial idea: treat Hitmonchan as coverage plus priority, not as a weak
  physical-only Hitmon. The right answer may be a special sponge, a faster KO,
  or a pivot that does not become Mach Punch cleanup later.

Heracross route:

- Goal: convert high Attack, Megahorn, Cross Chop, Rock Slide, Scope Lens, and
  Focus Energy into a crit-heavy breaker or cleaner.
- What it punishes: giving it a Focus Energy turn, relying on one static wall,
  and assuming a Flying answer is safe before Rock Slide and crit branches are
  priced.
- Denial idea: do not let Focus Energy be free if Heracross still has targets
  to break. If Focus Energy lands, re-score crit stages and whether the current
  answer still survives the worst plausible hit.

## Player Plan Template

Primary route:

- Deny Bruno's opening hazard/phaze plan while preserving the specific pieces
  that answer Machamp and Heracross. The fight is lost if Onix turns the battle
  into repeated chipped entries and the real Fighting answers are spent before
  the final breakers arrive.

Backup route:

- If Spikes go up or a key answer gets chipped, shorten the game around
  immediate KOs, status, phazing/Haze, or controlled sacrifices. Do not keep
  playing a clean switch-map game after Onix has made switching expensive.

Best lead profile:

- A lead that pressures Onix, does not donate free Rapid Spin or Mach Punch
  positioning to Hitmontop, and does not let Hitmonlee Meditate or attack
  freely. It must not be the only Machamp or Heracross answer.
- A special attacker that can remove Onix may be attractive, but it must still
  have a plan for Hitmontop spin, Mach Punch revenge, Focus Band Hitmonlee, and
  Hitmonchan's elemental coverage later.

Avoid as lead:

- A slow setup lead that Onix can Roar after setting Spikes.
- The only Fighting answer if Onix can chip it with Rock Slide or phaze it into
  hazard damage.
- A hazard lead if Hitmontop can spin for free.
- A fragile fast cleaner that falls into Mach Punch range before Machamp or
  Heracross are handled.

First-turn question:

```text
Which adaptive opener appeared?

Onix: can we deny Spikes / Roar value without spending the Machamp or Heracross
answer?

Hitmontop: is Rapid Spin, Mach Punch, Rock Slide, or Hi Jump Kick the live
route, and does our lead preserve the cleaner from priority range?

Hitmonlee: can we deny Meditate or Focus Band catastrophe before it breaks the
answer map?
```

If Onix sets Spikes:

- Re-score grounded player Pokemon, whether the player has spin/removal, and
  whether Bruno's Roar route makes preserving the Fighting answers harder.

If Onix uses Roar:

- Treat the forced switch as information plus hazard pressure. The new active
  is not necessarily the intended answer; rebuild the route from the actual
  board.

If Hitmontop opens or enters:

- Check whether the player's hazards matter. If yes, make Rapid Spin expensive;
  if no, prioritize preserving the Pokemon that avoids Mach Punch cleanup.

If Hitmonlee opens or uses Meditate:

- Stop slow development. The next turn is about denying boosted Hi Jump Kick,
  Rock Slide, or Earthquake from breaking the answer map.

If Machamp enters:

- Count Cross Chop, Rock Slide, Earthquake, and Vital Throw branches before
  switching. The safest-looking answer may still fail if it was already chipped
  by Spikes or Onix.

If Hitmonchan enters:

- Treat elemental punches as the main question and Mach Punch as the cleanup
  question. Do not use type words like "resisted" or "super effective" without
  local matchup evidence.

If Heracross uses Focus Energy:

- Re-score crit stages immediately. With Scope Lens already present, a free
  Focus Energy turn can change whether any defensive answer is still stable.

Worst plausible branch:

- The player lets Onix start Spikes and Roar pressure, fails to punish
  Hitmontop's spin or priority role, loses a Fighting answer to Hitmonlee or
  Machamp coverage, and then Heracross or Hitmonchan converts the remaining
  chipped team with crit pressure or Mach Punch.

Abandon conditions:

- The only Machamp or Heracross answer is below the required HP threshold after
  Spikes, Rock Slide, or priority damage.
- Hitmontop can spin away the player's hazard route without giving up decisive
  pressure.
- Hitmonlee gets a Meditate turn and no immediate denial route remains.
- Hitmonchan's coverage invalidates the assumed pivot.
- Heracross has Focus Energy plus Scope Lens online and the current route
  depends on not being crit.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Bruno is a breaker-map lesson. The useful GSC transfer from Snorlax-heavy
  study is not Snorlax itself; it is preserving the few pieces that can still
  stop a high-power breaker after hazards, crit branches, and coverage have
  changed the state.
