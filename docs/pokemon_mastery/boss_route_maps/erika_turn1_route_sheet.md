# Erika Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Rapid Spin source:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Erika as adaptive first-three: Tangela / Jumpluff / Bellossom.
- Encore source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; local
  Encore lasts 3-6 turns.
- Leech Seed, Stun Spore, Sleep Powder, Reflect, Swords Dance, Quiver Dance,
  Synthesis, SolarBeam, Giga Drain, Sludge Bomb, and Explosion are listed in
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Weather/recovery source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  Synthesis recovery changes with weather and time of day, and Sunny Day lasts
  five turns.
- Life Orb, Muscle Band, MiracleBerry, and Leftovers behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Type-chart caveat: `docs/agent_navigation/hack_mechanics_reference.md` says
  Grass is neutral into Flying in this hack, so do not import vanilla Flying
  resistance shortcuts.
- Expert principle sources: Smogon Exeggutor, Jumpluff, status/sleep, setup,
  Explosion, and weather-control material.

Boss roster:

```text
Lv57 Tangela @ Leftovers:
  Rapid Spin / Giga Drain / Stun Spore / Reflect

Lv58 Jumpluff @ MiracleBerry:
  Sleep Powder / Leech Seed / Encore / Sunny Day

Lv59 Bellossom @ Leftovers:
  Quiver Dance / Hidden Power / Synthesis / SolarBeam

Lv64 Victreebel @ Muscle Band:
  Swords Dance / Sludge Bomb / Razor Leaf / Sleep Powder

Lv61 Exeggutor @ Life Orb:
  Psychic / Giga Drain / Sleep Powder / Explosion
```

Boss likely openings:

- Erika is source-listed as adaptive first-three, not fixed Tangela.
- Plan for Tangela / Jumpluff / Bellossom, with Tangela favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Erika's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Tangela route:

- Goal: remove hazards with Rapid Spin, slow the player with Stun Spore, put up
  Reflect, and recover chip through Giga Drain plus Leftovers.
- What it punishes: hazard plans with no spin punish and physical pressure that
  lets Reflect turn the next exchange.
- Denial idea: decide whether Tangela is currently the spinner, status spreader,
  or screen setter. If hazards are not the route, Tangela may be less urgent
  than Jumpluff, Victreebel, or Exeggutor.

Jumpluff route:

- Goal: use Speed, MiracleBerry, Sleep Powder, Leech Seed, Encore, and Sunny
  Day to make the player's intended move sequence collapse.
- What it punishes: slow setup, recovery, status-only plans into MiracleBerry,
  and clicking a passive move that can be Encored for 3-6 turns.
- Denial idea: before using setup, recovery, or a low-impact status move, ask
  whether Jumpluff can enter and Encore it. If Sleep Powder or Encore changes
  the board, discard the prior script and rebuild.

Bellossom route:

- Goal: use Quiver Dance, Synthesis, SolarBeam, and Leftovers to become a
  special setup route, especially if Sunny Day has improved SolarBeam and
  recovery timing.
- What it punishes: letting Erika spend turns on weather or setup while the
  player deals only chip, and assuming Synthesis has one fixed value.
- Denial idea: count weather, recovery, and boosted Speed/Special stats. If
  Bellossom gets Quiver Dance, ask whether the anti-setup tool still works.

Victreebel route:

- Goal: use Sleep Powder or Swords Dance to convert into a physical Sludge Bomb
  / Razor Leaf pressure route.
- What it punishes: one-dimensional special walls, slow pivots, and letting a
  sleeping target make Swords Dance safe.
- Denial idea: identify whether the immediate threat is sleep or setup. If the
  player cannot tolerate either branch, the best move may be direct pressure or
  a pivot that preserves the real Victreebel answer.

Exeggutor route:

- Goal: force progress with Life Orb Psychic/Giga Drain, Sleep Powder, and
  Explosion as a one-time route trade.
- What it punishes: switching the irreplaceable answer into sleep or Explosion,
  and assuming Exeggutor is only a special attacker.
- Denial idea: treat Exeggutor like the GSC proxy it is: sleep and Explosion
  change routes. Ask what it removes if it explodes and whether that opens the
  rest of Erika's team.

## Player Plan Template

Primary route:

- Do not let Erika stack control turns. Her team wants to lock the player into
  a bad sequence with sleep, paralysis, Encore, Leech Seed, Reflect, weather,
  recovery, setup, and Explosion.

Backup route:

- If the first plan is slept, Encored, paralyzed, or seeded, stop following it.
  Rebuild around the affected Pokemon's role, remaining sleep/status tools,
  weather turns, and whether Victreebel or Bellossom can now set up.

Best lead profile:

- A lead that pressures Tangela without being disabled by Stun Spore, does not
  give Jumpluff an obvious Sleep Powder / Leech Seed / Encore target, and can
  stop or immediately punish a Bellossom Quiver Dance opener.
- It should preserve a route against physical/setup Victreebel and Exeggutor's
  Sleep Powder or Explosion trade.

Avoid as lead:

- A passive setup or recovery lead that Jumpluff can Encore.
- A hazard lead if Tangela spins for free.
- The only Exeggutor or Victreebel answer if Sleep Powder can remove it from
  the plan.
- A route that assumes Grass/Flying matchups from vanilla memory.

First-turn question:

```text
Which adaptive opener appeared?

Tangela: is Rapid Spin, Stun Spore, Reflect, or Giga Drain the live control
route, and does our lead punish it?

Jumpluff: can we handle Sleep Powder / Leech Seed / Encore / Sunny Day without
locking the player into a bad sequence?

Bellossom: can we stop Quiver Dance immediately, or do we have a named phaze,
Haze, status, direct damage, or sacrifice line after boosts?
```

If Tangela uses Stun Spore:

- Check whether the paralyzed Pokemon was the speed control for Jumpluff,
  Victreebel, or Bellossom. If yes, the lead plan may already be obsolete.

If Jumpluff opens or enters:

- Price Sleep Powder, Leech Seed, Encore, and Sunny Day before clicking a
  passive move. A harmless-looking recovery or setup turn can become the move
  that loses the fight.

If Bellossom opens or uses Quiver Dance:

- Re-score Speed and special bulk immediately. Weather and Synthesis can turn
  weak chip into a lost recovery race.

If Exeggutor enters:

- Price Sleep Powder and Explosion separately. A correct switch into Psychic
  damage can still be a wrong route if it loses to sleep or boom.

Worst plausible branch:

- The player lets Tangela spin or paralyze the speed-control piece, gets a key
  Pokemon slept or Encored by Jumpluff, allows Bellossom or Victreebel to set
  up, and then loses the remaining answer to Exeggutor's Life Orb pressure or
  Explosion.

Abandon conditions:

- The current route depends on a Pokemon that is asleep, paralyzed, seeded, or
  Encored.
- Reflect or weather is active and the plan assumed baseline damage or recovery.
- Bellossom or Victreebel has boosted and no immediate denial route remains.
- Exeggutor can Explode on an irreplaceable answer.
- Tangela can spin away the player's hazard route without cost.
- Type-chart, passive, item, weather, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Erika is a control-chain fight. The useful GSC transfer is to stop treating
  each status or support move as isolated; sleep, Encore, Leech Seed, Reflect,
  weather, and Explosion all exist to buy a later setup or route-trade turn.
