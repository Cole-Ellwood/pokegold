# Brock Turn-1 Route Sheet

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
  list Brock as adaptive first-three: Omastar / Corsola / Golem.
- Worked example:
  `../worked_examples/brock_golem_explosion_turn_order_quarantine.md`
- Exact turn drill:
  `../worked_examples/brock_golem_vaporeon_execution_gate_turn_drill.md`
- Recover source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Recover
  restores 50% max HP.
- Curse, Swords Dance, Explosion, Protect, Rock Slide, Slash, and Surf are
  listed in `docs/agent_navigation/hack_mechanics_reference.md`.
- Rocky Helmet, Muscle Band, type-boost items, and Leftovers behavior:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Contact evidence for Rocky Helmet depends on `data/moves/contact_flags.asm`;
  do not assume a move triggers contact recoil without checking the flag.
- Expert principle sources: Smogon GSC Spikes, Explosion, setup-move, and
  long-term resource-conversion material.

Boss roster:

```text
Lv57 Omastar @ Leftovers:
  Spikes / Surf / Ice Beam / Protect

Lv57 Corsola @ Leftovers:
  Rapid Spin / Recover / Rock Slide / Toxic

Lv60 Golem @ Rocky Helmet:
  Curse / Earthquake / Rock Slide / Explosion

Lv59 Kabutops @ Muscle Band:
  Swords Dance / Rock Slide / Surf / Slash

Lv59 Onix @ Hard Stone:
  Spikes / Rock Slide / Earthquake / Roar

Lv58 Aerodactyl @ Hard Stone:
  Earthquake / Rock Slide / Wing Attack / Protect
```

Boss likely openings:

- Brock is source-listed as adaptive first-three, not fixed Omastar.
- Plan for Omastar / Corsola / Golem, with Omastar favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Brock's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Omastar route:

- Goal: open with Spikes, then use bulk, Leftovers, Protect, Surf, and Ice Beam
  to make the player spend turns while entry damage accumulates.
- What it punishes: passive leads, slow setup, and plans that treat Protect as
  a wasted turn instead of a scouting and recovery turn.
- Denial idea: pressure Omastar before it gets both Spikes and Protect value.
  If Spikes land, immediately re-score grounded player Pokemon and whether
  Brock can force more entries with Onix or Aerodactyl.

Corsola route:

- Goal: remove the player's hazards with Rapid Spin, stretch exchanges with
  Recover, and put a key answer on a Toxic clock.
- What it punishes: hazard plans with no spin punish and low-damage attacks
  that let Corsola Recover indefinitely.
- Denial idea: decide whether Corsola is currently the spinner, the recovery
  wall, or the status clock. If the player's route does not depend on hazards,
  Corsola may be less urgent than Golem or Kabutops.

Golem route:

- Goal: use Curse, heavy physical attacks, Rocky Helmet contact punishment, and
  Explosion to turn one opening into a route trade.
- What it punishes: contact-heavy attackers, weak chip after Curse, and using
  the only Golem/Kabutops answer before Explosion is priced.
- Denial idea: treat Golem as both setup and one-time conversion. If it can
  Explode on an irreplaceable piece, that future route matters more than the
  visible HP total.

Kabutops route:

- Goal: use Swords Dance plus Muscle Band to become a physical breaker while
  still carrying Surf for mixed pressure.
- What it punishes: giving it a free setup turn, using only physical bulk as
  the answer, and assuming all Rock/Water Pokemon have the same damage profile.
- Denial idea: if Swords Dance is possible, ask whether current damage, status,
  phazing/Haze, priority, or sacrifice stops the next attack from opening
  Brock's endgame.

Onix route:

- Goal: add another Spikes source, then use Roar and Rock/Ground pressure to
  make the player repeatedly enter through hazards.
- What it punishes: letting early Spikes remain, and setup plans that are
  undone by Roar before they convert.
- Denial idea: if Onix enters with Spikes already up, Roar is no longer just a
  defensive move. It can become the route that converts Brock's earlier hazard
  turn.

Aerodactyl route:

- Goal: use Speed, Rock/Ground/Flying coverage, and Protect to finish chipped
  targets while scouting the player's response.
- What it punishes: spending the fast or bulky Aerodactyl answer earlier, and
  letting Spikes or Toxic put that answer into range.
- Denial idea: preserve a route that handles Aerodactyl after the slower
  hazard/setup pieces have done their job. Do not call the endgame safe without
  checking Speed, HP, and damage evidence.

## Player Plan Template

Primary route:

- Prevent Brock from combining hazards, recovery, setup, and Explosion into a
  long-game rock slide. The player should decide early whether the fight is
  about denying Spikes, punishing Corsola's spin/recovery, or keeping the
  Golem/Kabutops answer intact.

Backup route:

- If Spikes go up, shorten the game around concrete KOs or preserve only the
  pivots that still matter. Do not keep making empty switches while Onix,
  Corsola, and Aerodactyl turn every entry into progress.

Best lead profile:

- A lead that pressures Omastar, does not donate free Recover/Rapid Spin value
  to Corsola, and does not lose the route map if Golem opens and threatens
  Curse or Explosion. It must not be the only answer to Kabutops or Aerodactyl.
- A hazard lead is useful only if Corsola cannot spin without giving up a
  larger resource.

Avoid as lead:

- A passive setup lead that lets Omastar set Spikes or Golem/Kabutops boost.
- A contact-heavy attacker into Golem unless Rocky Helmet and contact flags are
  already priced.
- The only Aerodactyl answer if it can be poisoned, chipped, or traded by
  Explosion earlier.
- A hazard plan with no answer to Corsola's Rapid Spin.

First-turn question:

```text
Which adaptive opener appeared?

Omastar: does our first move deny Spikes/Protect value or make the layer
convert poorly?

Corsola: is Rapid Spin, Recover, Toxic, or Rock Slide the live reset route, and
does our lead actually punish it?

Golem: can we deny Curse / Explosion value without spending the Kabutops or
Aerodactyl answer?
```

If Omastar sets Spikes:

- Re-score grounded player Pokemon, Corsola's spin role, and whether Onix Roar
  or Aerodactyl cleanup now becomes the main danger.

If Corsola opens or enters:

- Decide whether to punish Rapid Spin, deny Recover, avoid Toxic on an
  irreplaceable answer, or ignore Corsola because another Brock route is more
  urgent.

If Golem opens or enters:

- Price Curse and Explosion before attacking. A move that chips Golem but lets
  it Explode on the only Kabutops/Aerodactyl answer may be a bad trade.

If Kabutops uses Swords Dance:

- Stop slow progress. The next turn is about denial, phazing/Haze, status,
  immediate KO, or controlled sacrifice.

Worst plausible branch:

- The player lets Omastar set Spikes, fails to punish Corsola's spin/recovery,
  gives Golem or Kabutops a setup or Explosion trade, and reaches Aerodactyl
  with the fast/bulky answer already chipped by hazards, Toxic, or Rock Slide.

Abandon conditions:

- Spikes are up and the current route needs repeated grounded switching.
- Corsola can Recover or spin without giving up decisive pressure.
- Golem can Explode on an irreplaceable piece.
- Kabutops has boosted and no immediate denial route remains.
- Aerodactyl can clean after prior chip.
- Type-chart, passive, contact, item, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Brock teaches resource conversion without Snorlax. Omastar and Corsola are
  the slow-resource pieces, Golem is the Curse/Explosion route trade, Kabutops
  is the setup breaker, and Aerodactyl is the cleaner. The transferable lesson
  is to identify which resource clock Brock is actually winning.
