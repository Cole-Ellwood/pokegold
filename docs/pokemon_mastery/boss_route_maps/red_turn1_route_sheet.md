# Red Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; Red combines an
  immediate coverage lead, a screen/setup Psychic, a true Snorlax anchor, two
  sun users, and a mixed Water coverage piece.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Light Ball source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; local Light Ball
  doubles Pikachu's Special Attack only, not Attack.
- Critical-hit source: `data/moves/critical_hit_moves.asm`,
  `data/battle/critical_hit_chances.asm`, and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Razor Leaf is a
  high-crit move with +2 crit stages.
- Priority caveat: ExtremeSpeed uses `EFFECT_PRIORITY_HIT` locally, sharing the
  same priority tier as Quick Attack and Mach Punch.
- Reflect source: `engine/battle/effect_commands.asm`; local Reflect lasts
  five turns.
- Calm Mind source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`; local
  Calm Mind raises Special Attack and Special Defense.
- Rest / Sleep Talk source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; Rest creates the local
  Rest sleep cycle, and Sleep Talk can act while asleep.
- Sunny Day source: `engine/battle/move_effects/sunny_day.asm`; local weather
  lasts five turns.
- Fire passive caveat: `tools/damage_debugger/clobber_smoke.py::special_fire_low_hp`
  verifies full-Fire below-one-third damage, but Red's Charizard is Fire/Flying
  in `data/pokemon/base_stats/charizard.asm`. Treat Charizard's half-Fire
  low-HP modifier as source-grounded but not yet runtime-fixture-verified.
- Synthesis / Morning Sun source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`; recovery depends on
  weather and time of day.
- Mirror Coat source: `engine/battle/move_effects/mirror_coat.asm` and
  `data/moves/moves.asm`; treat special attacks into Blastoise as a possible
  fixed-damage punish branch.
- Expert principle sources: Smogon GSC Snorlax, GSC status, screens, weather,
  priority, wallbreaking, and long-game route-planning material.

Boss roster:

```text
Lv81 Pikachu @ Light Ball:
  ExtremeSpeed / Thunderbolt / Razor Leaf / Surf

Lv73 Espeon @ TwistedSpoon:
  Reflect / Morning Sun / Calm Mind / Psychic

Lv75 Snorlax @ Leftovers:
  Curse / Sleep Talk / Rest / Body Slam

Lv77 Venusaur @ Miracle Seed:
  Sunny Day / Sludge Bomb / Synthesis / SolarBeam

Lv77 Charizard @ Charcoal:
  Flamethrower / Wing Attack / Sunny Day / SolarBeam

Lv77 Blastoise @ Mystic Water:
  Earthquake / Surf / Blizzard / Mirror Coat
```

## Boss Routes

Pikachu route:

- Goal: use Light Ball-boosted special coverage with Thunderbolt, Razor Leaf,
  and Surf while keeping ExtremeSpeed as a priority finisher. Razor Leaf also
  carries a high-crit branch locally, so Grass coverage is not just ordinary
  chip into the expected lead answer.
- What it punishes: assuming Ground or Rock answers are safe without checking
  Surf / Razor Leaf, ignoring Razor Leaf crit volatility, and leaving the
  planned cleaner in ExtremeSpeed range.
- Denial idea: separate Pikachu's physical priority from its special coverage.
  ExtremeSpeed is not Light Ball-boosted, but it still changes revenge math.
  Razor Leaf is Light Ball-relevant special pressure plus a high-crit branch,
  so the lead answer needs survival evidence rather than type-chart comfort.

Espeon route:

- Goal: use Reflect, Morning Sun, Calm Mind, and TwistedSpoon Psychic to turn
  a support turn into a special setup route.
- What it punishes: weak chip into recovery, physical pressure through Reflect,
  and letting Calm Mind make the special answer collapse.
- Denial idea: count Reflect turns, Morning Sun recovery context, and Calm Mind
  boosts. If Espeon boosts, ask whether direct damage, status, phazing/Haze, or
  a sacrifice denies the route before Psychic becomes too strong.

Snorlax route:

- Goal: use Curse, Rest, Sleep Talk, Leftovers, and Body Slam to become the
  long-game anchor that punishes teams without a real Normal-resist, phazer,
  Haze user, pressure route, or strong Fighting/Explosion equivalent.
- What it punishes: spending the Snorlax answer on Pikachu or Espeon, letting
  Body Slam paralysis remove the emergency answer, and treating Rest as the
  end of Red's pressure when Sleep Talk remains live.
- Denial idea: preserve the Snorlax plan from turn 1. Know whether the answer
  is phazing/Haze, strong immediate damage, PP pressure, status before Rest,
  forcing low-HP Rest, or a concrete sacrifice route.

Venusaur route:

- Goal: use Sunny Day to improve SolarBeam and Synthesis, then pressure with
  Miracle Seed Grass damage and Sludge Bomb.
- What it punishes: Water/Rock/Ground pivots that become unstable under sun,
  and status or chip lines that Synthesis erases.
- Denial idea: if sun starts, count five turns and check whether Venusaur owns
  the recovery and damage clock. Do not assume the same pivot map from clear
  weather.

Charizard route:

- Goal: use Charcoal Flamethrower, Wing Attack, Sunny Day, and SolarBeam to
  punish the obvious Fire answers and convert weather into direct pressure.
- What it punishes: switching a Water answer after sun is active, ignoring
  Flying physical damage, and assuming SolarBeam costs a charge turn.
- Denial idea: deny or outlast the sun window, force damage before weather
  converts, or pivot to a piece that can take both Fire and SolarBeam routes
  under local type/passive evidence. If Charizard is below one-third HP, do not
  assume it is spent; its half-Fire passive branch still needs exact fixture
  validation before writing exact damage labels.

Blastoise route:

- Goal: use Mystic Water Surf, Earthquake, Blizzard, and Mirror Coat to punish
  both physical and special answers.
- What it punishes: firing a special nuke without pricing Mirror Coat, and
  assuming Water coverage is narrow when Earthquake and Blizzard cover common
  answers.
- Denial idea: identify whether the intended Blastoise answer attacks
  physically, survives Mirror Coat risk, or can force Blastoise into predictable
  damage without losing an irreplaceable piece.

## Player Plan Template

Primary route:

- Red is a full-route exam. The player must beat Pikachu's coverage lead while
  preserving a Snorlax answer, an Espeon setup answer, a sun-weather plan, and
  a Blastoise Mirror Coat plan.

Backup route:

- If Pikachu removes or chips the intended answer, shorten the fight around the
  next route that can actually be denied. Red's team can pivot from immediate
  coverage to screen/setup, RestTalk anchor play, sun conversion, or Mirror Coat
  punishment.

Best lead profile:

- A lead that handles Pikachu's coverage without being the only Snorlax or
  Espeon answer. The lead should either KO or force Pikachu without ending in
  ExtremeSpeed range, and it should not reveal the only special attacker needed
  to beat Blastoise unless Mirror Coat is priced.

Avoid as lead:

- The only Snorlax answer if Pikachu can chip it or force paralysis later.
- A pure Ground plan that ignores Surf and Razor Leaf.
- A physical-only plan that lets Espeon set Reflect and Calm Mind.
- A special-only Blastoise plan with no Mirror Coat branch.
- A Water-only answer to Venusaur or Charizard if Sunny Day can flip the route.

First-turn question:

```text
If Pikachu uses ExtremeSpeed, Thunderbolt, Razor Leaf, or Surf on turn 1, which
Red route becomes easier: Espeon setup, Snorlax RestTalk, Venusaur/Charizard
sun, or Blastoise Mirror Coat?
```

If Pikachu uses ExtremeSpeed:

- Track priority range, but do not overstate the damage boost: Light Ball is
  special-only locally. A low-HP cleaner may still be unusable even if the move
  is not boosted by the item.

If Pikachu uses special coverage:

- Update the pivot map. A Ground/Rock-style answer that loses to Surf or Razor
  Leaf was never a stable plan. If Razor Leaf is the relevant branch, include
  the high-crit chance before deciding the lead is durable enough for later Red
  routes.

If Espeon sets Reflect:

- Start a five-turn Reflect ledger. Physical pressure may need to wait, pivot,
  status, phaze/Haze, or attack through the special side.

If Espeon uses Calm Mind:

- Re-score immediately. The question is whether Red now owns a special setup
  route before Snorlax or the sun users even appear.

If Snorlax enters:

- Do not improvise. Apply the preplanned Snorlax answer and check whether that
  piece was already chipped, paralyzed, or forced to spend PP earlier.

If Venusaur or Charizard uses Sunny Day:

- Start the weather ledger. Count five turns and price SolarBeam, Fire damage,
  Water damage reduction, and recovery changes before choosing the pivot.

If Blastoise enters:

- Ask whether the player is about to give Mirror Coat a decisive punish. If
  special damage is still correct, it needs a route reason beyond "it hits hard."

Worst plausible branch:

- The player overcommits to Pikachu, loses the Snorlax or Espeon answer, lets
  Reflect or Calm Mind make the midgame harder, fails to stop RestTalk CurseLax,
  then has the remaining route checked by sun-boosted starters or Blastoise's
  Mirror Coat.

Abandon conditions:

- The Snorlax answer is paralyzed, asleep, below threshold, or out of critical
  PP.
- Espeon has Calm Mind boosts or Reflect turns that invalidate the current
  damage plan.
- Sunny Day is active and the plan depends on Water damage, clear-weather
  recovery, or a two-turn SolarBeam assumption.
- Blastoise can Mirror Coat the intended special attack for a decisive KO.
- Pikachu's coverage reveals that the lead answer is not stable.
- Razor Leaf crit risk makes the lead answer too unstable to preserve the
  later Snorlax, Espeon, sun, or Blastoise plan.
- Type-chart, passive, item, weather, recovery, or damage evidence contradicts
  the assumed answer.

Snorlax study transfer:

- Red is the one local boss where Snorlax itself matters. The general lesson is
  still broader: preserve the irreplaceable anchor answer from turn 1, because
  a correct lead exchange can still lose if it spends the only piece that keeps
  the long-game route under control.
