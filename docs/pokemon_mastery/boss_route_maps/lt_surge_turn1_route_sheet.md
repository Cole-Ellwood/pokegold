# Lt. Surge Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; local Raichu and
  Electabuzz are Electric/Fighting, and local Ampharos is Electric/Dragon.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Lt. Surge as adaptive first-three: Magneton / Electrode / Raichu.
- Air Balloon source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  Ground attacks have no effect against the holder until the balloon pops on a
  direct damage hit.
- Light Screen source: `engine/battle/effect_commands.asm`; local screens last
  five turns.
- Agility source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; it is
  the only single-stat +Speed move in this hack.
- DynamicPunch, Cross Chop, Razor Leaf, DragonBreath, Thunderbolt, elemental
  punches, Explosion, and Rapid Spin are listed in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert principle sources: Smogon GSC Electrode, GSC Explosion, GSC Spikes,
  screen-support, and speed-control material.

Boss roster:

```text
Lv58 Magneton @ Air Balloon:
  Spikes / Thunderbolt / Thunder Wave / Explosion

Lv58 Electrode @ Magnet:
  Rapid Spin / Thunderbolt / Light Screen / Explosion

Lv65 Raichu @ Expert Belt:
  Agility / Thunderbolt / Cross Chop / Razor Leaf

Lv60 Electabuzz @ Wise Glasses:
  ThunderPunch / Ice Punch / Fire Punch / DynamicPunch

Lv61 Ampharos @ Dragon Fang:
  Thunderbolt / DragonBreath / Fire Punch / Light Screen
```

Boss likely openings:

- Lt. Surge is source-listed as adaptive first-three, not fixed Magneton.
- Plan for Magneton / Electrode / Raichu, with Magneton favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Lt. Surge's ordinary boss AI still must not know the player's
  unrevealed team, hidden moves, hidden item, private stats, or current-turn
  input.

## Boss Routes

Magneton route:

- Goal: use Air Balloon to block the obvious Ground answer long enough to set
  Spikes, spread Thunder Wave, attack, or trade with Explosion.
- What it punishes: leading a Ground attack without first popping Air Balloon,
  and assuming Magneton is only an Electric attacker rather than a hazard/status
  plus Explosion opener.
- Denial idea: decide whether turn 1 must pop Air Balloon, prevent Spikes, deny
  Thunder Wave on an irreplaceable piece, or avoid Explosion trade. The answer
  depends on the player's actual lead and route.

Electrode route:

- Goal: use extreme Speed to set Light Screen, remove hazards with Rapid Spin,
  attack with Magnet-boosted Thunderbolt, or trade with Explosion.
- What it punishes: hazard plans with no spin punish, slow attackers that let
  Light Screen go up, and weakened key pieces that can be removed by Explosion.
- Denial idea: identify whether Electrode is currently a screen setter, spinner,
  attacker, or route-trade button. Do not let Explosion remove the only answer
  to Raichu or Electabuzz unless that trade wins immediately.

Raichu route:

- Goal: use Agility to turn a mixed Electric/Fighting/Grass coverage set into a
  cleaner.
- What it punishes: relying on Speed control alone, assuming one Ground-like
  pivot handles all Electric attackers, and ignoring Razor Leaf / Cross Chop
  coverage until after Agility.
- Denial idea: if Raichu can use Agility, ask whether immediate damage, status,
  phazing/Haze, priority, or sacrifice stops the next two turns. A slow
  defensive answer may fail once Speed changes.

Electabuzz route:

- Goal: use special elemental punches plus DynamicPunch confusion pressure to
  punish predictable pivots.
- What it punishes: type-slogan switching and assuming Electric/Fighting means
  only physical Fighting coverage.
- Denial idea: every intended pivot needs local type-chart, passive, and damage
  evidence for ThunderPunch, Ice Punch, Fire Punch, and DynamicPunch. If the
  plan loses to confusion, call that risk explicitly.

Ampharos route:

- Goal: combine bulk, DragonBreath paralysis chance, Fire Punch coverage,
  Thunderbolt pressure, and Light Screen support.
- What it punishes: trying to outlast Surge with special attacks through Light
  Screen, or ignoring Dragon/Fighting/Electric type changes in the local roster.
- Denial idea: if Light Screen goes up, count five turns and decide whether to
  attack through the other category, use status, phaze/Haze, recover, or pivot
  until the screen no longer protects Surge's route.

## Player Plan Template

Primary route:

- Do not let Surge turn "Electric boss" into a support-chain fight. Magneton
  wants Air Balloon plus Spikes/status/Explosion, Electrode wants screen/spin or
  Explosion, and Raichu/Electabuzz/Ampharos want the player to have spent the
  real answer too early.

Backup route:

- If Air Balloon blocks the first plan, or Light Screen goes up, stop trying to
  force the old line. Rebuild around balloon state, screen turns, paralysis,
  and which Surge attacker is now most dangerous.

Best lead profile:

- A lead that can pressure Magneton without being completely stopped by Air
  Balloon, does not donate free Rapid Spin/Light Screen/Explosion value to
  Electrode, and can deny or immediately answer an Agility Raichu opener. It
  must not be the only Electabuzz answer.
- The first move should either pop Balloon, deny Spikes/Thunder Wave, punish
  Electrode's support turn, or create pressure that makes Explosion less
  valuable for Surge.

Avoid as lead:

- A pure Ground-plan lead if Air Balloon prevents the intended first action.
- The only Raichu or Electabuzz answer if Magneton can paralyze or explode on
  it.
- A hazard lead if Electrode can spin for free.
- A special-only pressure plan if Light Screen can go up without punishment.

First-turn question:

```text
Which adaptive opener appeared?

Magneton: can we pop Air Balloon, deny Spikes / Thunder Wave, or make Explosion
a bad route trade?

Electrode: is Rapid Spin, Light Screen, Thunderbolt, or Explosion the live
support route, and does our lead punish it?

Raichu: can we stop Agility immediately, or do we have a named status, phaze,
damage, sacrifice, or revenge line after +2 Speed?
```

If Magneton sets Spikes:

- Re-score grounded player Pokemon, Electrode's spin role, and whether Raichu
  or Electabuzz now needs less damage to clean.

If Magneton uses Thunder Wave:

- Check whether the paralyzed Pokemon was the speed control or emergency answer
  to Agility Raichu. If yes, the original plan may already be obsolete.

If Magneton threatens Explosion:

- Treat Explosion as a route trade. The question is not "can we survive?" It is
  whether losing that piece opens Raichu, Electabuzz, or Ampharos.

If Electrode opens or uses Light Screen:

- Start a screen ledger. Count five turns and identify whether physical
  pressure, status, phazing/Haze, or a pivot beats the protected route.

If Electrode opens or uses Rapid Spin:

- Decide whether hazards were the real route. If yes, spin must be punished; if
  no, Surge may have spent a low-impact turn.

If Raichu opens or uses Agility:

- Re-score Speed before every move. If the player cannot deny or survive the
  boosted sequence, a sacrifice or immediate status route may be required.

Worst plausible branch:

- The player opens with a Ground plan into Air Balloon, lets Magneton set
  Spikes or paralyze the key answer, fails to punish Electrode's Light Screen or
  Explosion, and then loses to Agility Raichu or coverage Electabuzz while the
  remaining special pressure bounces off screen turns.

Abandon conditions:

- Air Balloon is still intact and the current plan depends on Ground damage.
- The speed-control piece is paralyzed.
- Light Screen is active and the current route depends on special damage.
- Electrode can spin away the player's hazard route without giving up pressure.
- Magneton or Electrode can Explode on an irreplaceable answer.
- Raichu has used Agility and no immediate denial route remains.
- Type-chart, passive, item, screen, or damage evidence contradicts the assumed
  answer.

Snorlax study transfer:

- Surge teaches support-chain denial. The GSC transfer is to ask what the
  support turn enables: Spikes, paralysis, screens, spin, or Explosion. If the
  answer is "Agility Raichu or coverage Electabuzz now wins," the support turn
  was the real threat, not just the visible Electric attack.
