# Karen Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; local Gengar is
  Ghost/Psychic.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Spikes / Rapid Spin delta:
  `docs/pokemon_mastery/romhack_deltas/spikes_and_rapid_spin.md`
- Opening policy:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md` and
  `docs/pokemon_mastery/boss_route_maps/adaptive_lead_audit_2026-05-13.md`
  list Karen as adaptive first-three: Gengar / Donphan / Murkrow.
- Pursuit source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Pursuit
  doubles damage on a switching target.
- Dragon Dance source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  this hack boosts the user's current higher offensive stat plus Speed.
- Weather source: `engine/battle/move_effects/sunny_day.asm` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; sun lasts five turns,
  boosts Fire damage, weakens Water damage, and lets SolarBeam skip charge.
- Safeguard source: `engine/battle/move_effects/safeguard.asm`; it sets a
  five-turn side condition.
- Hypnosis is 60 accuracy and Dream Eater only works against sleeping targets
  according to `data/moves/moves.asm` and `engine/battle/effect_commands.asm`.
- Dark is special in this hack according to
  `docs/agent_navigation/hack_mechanics_reference.md`.
- Expert principle sources: Smogon GSC Spikes, GSC Gengar, GSC Donphan, GSC
  Tyranitar, Houndoom Pursuit, and status/sleep resources.

Boss roster:

```text
Lv42 Gengar @ Spell Tag:
  Spikes / Shadow Ball / Hypnosis / Dream Eater

Lv42 Donphan @ Soft Sand:
  Rapid Spin / Earthquake / Rock Slide / Roar

Lv44 Murkrow @ Blackglasses:
  Wing Attack / Faint Attack / Pursuit / Steel Wing

Lv46 Tyranitar @ Blackglasses:
  Crunch / Rock Slide / Earthquake / Dragon Dance

Lv45 Crobat @ Leftovers:
  Wing Attack / Confuse Ray / Toxic / Safeguard

Lv47 Houndoom @ Charcoal:
  Flamethrower / Crunch / Sunny Day / SolarBeam
```

Boss likely openings:

- Karen is source-listed as adaptive first-three, not fixed Gengar.
- Plan for Gengar / Donphan / Murkrow, with Gengar favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Karen's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Gengar route:

- Goal: set Spikes, land Hypnosis, then cash out with Dream Eater or Shadow
  Ball pressure while the sleeping target cannot perform its role.
- What it punishes: passive leads, status plans that ignore sleep clause and
  miss branches, and treating sleep as a permanent disable rather than a
  temporary tempo swing.
- Denial idea: if Hypnosis misses, Karen loses tempo; if it hits, immediately
  re-score the sleeping Pokemon's role and whether Dream Eater can convert.
  Verify local Rapid Spin/type interaction before calling Gengar a spinblocker.

Donphan route:

- Goal: remove the player's Spikes, threaten physical damage, and Roar away
  setup while Karen's own hazards or switch pressure accumulate value.
- What it punishes: hazard plans with no spin punish, setup plans that can be
  Roared, and weak special pivots that ignore Earthquake / Rock Slide damage.
- Denial idea: make Rapid Spin or Roar cost something. If the player does not
  need hazards or boosts, Donphan may be less urgent than the later Tyranitar or
  Houndoom route.

Murkrow route:

- Goal: force switch anxiety with Faint Attack and Pursuit while threatening
  physical Flying/Steel coverage.
- What it punishes: switching a weakened Psychic/Ghost/special attacker without
  pricing Pursuit, and assuming Dark/Flying means only one damage category.
- Denial idea: decide whether staying in or switching is the safer route before
  clicking. Pursuit is strongest when the target wants to flee.

Tyranitar route:

- Goal: use bulk, mixed Rock/Dark/Ground pressure, and Dragon Dance to become a
  breaker or cleaner.
- What it punishes: giving a free Dragon Dance turn, leaning on one pivot that
  loses to the coverage trio, and forgetting that local Dragon Dance chooses the
  user's current higher offensive stat plus Speed.
- Denial idea: preserve a verified Tyranitar answer until Dragon Dance is no
  longer live. If Tyranitar boosts, re-score Speed, damage thresholds, and
  whether phazing/Haze, status, priority, or sacrifice still answers it.

Crobat route:

- Goal: use speed, Toxic, Confuse Ray, Leftovers, and Safeguard to disrupt the
  player's answer map before Tyranitar or Houndoom converts.
- What it punishes: status-only plans after Safeguard, leaving an irreplaceable
  answer on a poison clock, and losing turns to confusion while hazards or
  boosted attackers wait.
- Denial idea: identify whether Crobat is currently protecting Karen's team
  from status, starting a poison clock, or buying free turns. Attack or pivot if
  status would be blocked or too slow.

Houndoom route:

- Goal: threaten immediate special damage with Flamethrower and Crunch, then use
  Sunny Day to turn Fire damage and one-turn SolarBeam into a conversion route.
- What it punishes: Water-based answers after sun is active, switching a
  vulnerable target into Crunch, and assuming SolarBeam gives a free charge turn.
- Denial idea: if Houndoom sets sun, rebuild the damage map. The next turn may
  no longer be "switch to the Water answer"; SolarBeam and boosted Flamethrower
  must be priced under local type/passive/damage evidence.

## Player Plan Template

Primary route:

- Do not let Karen own the first clock. Gengar wants sleep plus hazards,
  Donphan wants spin/Roar control, Crobat wants status/confusion/Safeguard, and
  Tyranitar or Houndoom want a setup/weather turn to convert.

Backup route:

- If Hypnosis lands or Spikes go up, stop following the original plan. Rebuild
  around the sleeping Pokemon's role, grounded switch count, Donphan's spin
  access, and which of Tyranitar or Houndoom is now most dangerous.

Best lead profile:

- A lead that can pressure Gengar, make Donphan's Rapid Spin/Roar route costly,
  and avoid handing Murkrow a clean Pursuit trap. It must not be the only
  Tyranitar or Houndoom answer.
- It should either punish Spikes/Hypnosis attempts or survive the miss and hit
  branches while preserving the later anti-setup route.

Avoid as lead:

- The only Tyranitar answer if Gengar can sleep it.
- A hazard lead if Donphan can spin without cost.
- A status-only lead if Crobat can later create Safeguard turns that invalidate
  the plan.
- A Water answer held in reserve for Houndoom if Sunny Day plus SolarBeam would
  invalidate it without prior chip or speed control.

First-turn question:

```text
Which adaptive opener appeared?

Gengar: can we deny Spikes / Hypnosis without spending the Tyranitar or
Houndoom answer?

Donphan: is Rapid Spin, Roar, Earthquake, or Rock Slide the live control route,
and does our lead punish it?

Murkrow: can we avoid a bad Pursuit/stay-in fork while preserving the later
anti-setup answers?
```

If Gengar sets Spikes:

- Re-score grounded player Pokemon, Donphan's spin role, and whether the player
  can remove or ignore hazards without opening Tyranitar or Houndoom.

If Gengar uses Hypnosis:

- Separate decision quality from outcome. If the sleep branch was priced and
  survivable, a hit is not automatically a bad decision; if it disables the only
  Tyranitar answer, the lead plan was too fragile.

If Donphan opens or enters:

- Decide whether Rapid Spin, Roar, or direct damage is the live route. Do not
  keep setting hazards or boosting if Donphan erases the state for free.

If Murkrow opens or enters:

- Price the switch and stay branches before moving. If the current Pokemon is a
  vulnerable Psychic, Ghost, special attacker, or weakened answer, Pursuit can
  turn a normal pivot into the resource Karen wanted.

If Tyranitar uses Dragon Dance:

- Re-score immediately under local Dragon Dance mechanics. Count the new Speed
  relation, boosted damage, and whether the planned answer still works.

If Crobat uses Safeguard:

- Status plans are paused for five turns unless the side condition is removed
  or expires. Use damage, pivoting, phazing/Haze, or recovery pressure instead
  of clicking blocked status moves.

If Houndoom uses Sunny Day:

- Start a weather ledger. Count turns and price boosted Flamethrower, weakened
  Water damage, and one-turn SolarBeam before choosing the next pivot.

Worst plausible branch:

- The player lets Gengar start sleep/hazard pressure, Donphan erases the
  player's hazard or boost route, Crobat blocks status with Safeguard, and then
  Tyranitar gets Dragon Dance or Houndoom gets Sunny Day while the correct
  answer is asleep, poisoned, confused, or trapped by Pursuit pressure.

Abandon conditions:

- The only Tyranitar or Houndoom answer is asleep, poisoned, or below its
  required damage threshold.
- Donphan can spin or Roar without giving up decisive pressure.
- Crobat's Safeguard is active and the current route depends on status.
- Tyranitar has boosted and the current Speed/damage map no longer holds.
- Houndoom has sun active and the current answer loses to boosted Fire damage
  or one-turn SolarBeam.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

Snorlax study transfer:

- Karen is a plan-disruption lesson. The useful GSC transfer is not Snorlax
  centrality; it is maintaining route discipline after sleep, hazards, Pursuit,
  phazing, weather, and setup all try to make the original turn-1 plan obsolete.
