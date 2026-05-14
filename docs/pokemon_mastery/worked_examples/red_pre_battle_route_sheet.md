# Worked Example: Red Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Red as a full-route exam. This is
a team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `RedGroup`.
- Boss route map: `../boss_route_maps/red_turn1_route_sheet.md`.
- Light Ball, Rest/Sleep Talk, weather, priority, item boosts, and Gen 2
  physical/special behavior:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.
- Razor Leaf critical-hit behavior:
  `data/moves/critical_hit_moves.asm` and
  `data/battle/critical_hit_chances.asm`.
- Species stats/types and move categories:
  `../../agent_navigation/hack_mechanics_reference.md`.
- Fire passive caveat:
  `../../../tools/damage_debugger/clobber_smoke.py::special_fire_low_hp` verifies
  full-Fire below-one-third damage, but Red's Charizard is Fire/Flying locally.
  Treat Charizard's low-HP Fire boost as source-grounded but not yet
  runtime-fixture-verified until the half-Fire fixture runs.

Expert study anchors:

- GSC status material: RestTalk means sleep or Rest does not remove a bulky
  anchor from the game; the plan must price Sleep Talk branches.
- Screen material: Reflect is a timed route enabler. Count turns instead of
  treating the screen as vague bulk.
- Weather material: sun is a temporary clock that changes Fire, Water,
  SolarBeam, and recovery math.
- GSC threat mapping: a single theoretical answer to a bulky setup anchor is
  fragile; the plan should preserve the real answer and name the backup.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Red

Known boss roster:
  Pikachu / Espeon / Snorlax / Venusaur / Charizard / Blastoise

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Snorlax denial route, an Espeon setup denial route, a sun
  weather plan, and a Blastoise Mirror Coat plan; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  Light Ball boosts Pikachu's Special Attack only, ExtremeSpeed shares the
  local priority-hit tier, Razor Leaf has +2 crit stages, Reflect lasts five
  turns, Sunny Day lasts five turns, Rest/Sleep Talk remains live, Mirror Coat
  punishes special attacks, Charizard's half-Fire low-HP passive branch is not
  yet runtime-fixture-verified, and type-chart/passive differences can alter
  every damage claim

Missing evidence:
  exact player team, HP, levels, moves, items, speed relations, damage ranges,
  passive type states, and whether any answer survives Pikachu coverage while
  still answering Snorlax, Espeon, sun, or Blastoise later
```

## Output Shape

Primary route:

- Beat or force Pikachu without spending the piece that must later deny
  Snorlax, Espeon, sun, or Blastoise.

Backup route:

- If Pikachu damages the intended lead-answer map, shorten the fight around
  the next route that can still be denied. Red has several independent routes,
  so the backup plan should name the route being abandoned and the route still
  being preserved.

Boss route priority:

```text
immediate:
  Pikachu Light Ball special coverage, Razor Leaf crit volatility, plus
  ExtremeSpeed revenge range.
  Blastoise Mirror Coat if the current plan depends on special damage.

accumulating:
  Espeon Reflect -> Calm Mind -> Morning Sun pressure.
  Snorlax Curse / Rest / Sleep Talk / Body Slam anchor route.
  Venusaur or Charizard Sunny Day clock.

endgame:
  Snorlax if the answer was spent or paralyzed.
  Charizard or Venusaur after sun changes damage and recovery math.
  Pikachu ExtremeSpeed if it survives into a low-HP cleanup position.
```

Boss route to deny first:

- Deny the first route that damages or disables the only answer to a later
  accumulating route. If the user's team has only one Snorlax answer, that
  preservation dominates early chip on Pikachu. If the user's team has only one
  Espeon setup answer, do not use it as the Pikachu damage sponge unless the
  trade creates a forced route before Espeon can set Reflect or Calm Mind.

Boss route that can be delayed:

- Blastoise can often be delayed if the team has a physical or mixed answer
  that does not hand Mirror Coat a decisive punish. This cannot be assumed for
  special-only teams.

- Sun can sometimes be delayed if both Venusaur and Charizard lack a clean
  entry and the team has a pivot that still works under sun. If the plan relies
  on clear-weather Water damage, sun is no longer delayable.

Best lead profile:

- A lead that handles Pikachu's coverage without being the only Snorlax,
  Espeon, sun, or Blastoise answer. The lead should either force Pikachu out,
  KO it, or create a safe pivot while staying out of decisive ExtremeSpeed
  range.

Avoid as lead:

- The only Snorlax answer.
- The only Espeon setup denial route.
- A pure Ground or Rock idea that ignores Surf and Razor Leaf.
- A lead that survives average Razor Leaf damage but collapses if the high-crit
  branch hits the piece needed for Red's later routes.
- A Water answer that becomes unstable if Sunny Day starts.
- A special attacker whose main job is to beat Blastoise unless Mirror Coat is
  already priced.

First move plan:

- Give turn 1 one job: reveal or punish Pikachu's coverage while preserving the
  answer map for Red's independent routes. Do not let a correct Pikachu exchange
  become a losing exchange because it spent the only Snorlax or Espeon answer.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Pikachu's selected move, including Razor Leaf crit volatility, and
  record whether the lead remains needed.

Turn 2:
  If Pikachu is forced or weakened, pivot toward the route that Red can most
  profitably bring in next: Espeon setup, Snorlax anchor, sun, or Blastoise.

Turn 3:
  Start the correct ledger for the route that appeared: Reflect turns, Calm
  Mind boosts, Curse/Rest/Sleep Talk, Sunny Day turns, Mirror Coat risk, or
  ExtremeSpeed range.
```

Piece to preserve:

- The Snorlax denial route is the default preservation priority unless the
  user's team has multiple confirmed answers. Red's Snorlax is not generic GSC
  Snorlax, but the general anchor lesson still applies: if the answer is gone,
  Curse plus RestTalk can become the fight's main clock.

- The Espeon denial route is co-equal if the team is physically biased or lacks
  Haze/phazing/status pressure. Reflect can make the physical plan worse before
  Snorlax even appears.

Piece that can be spent:

- A Pikachu answer whose later jobs are redundant after the lead exchange, or a
  pivot that creates clean entry into the actual Snorlax/Espeon/sun answer.
  Low HP alone is not enough; the piece is spendable only when its remaining
  route jobs are covered.

Worst plausible branch:

- The player overcommits to beating Pikachu, taking paralysis or chip on the
  only bulky-route answer. Espeon then gets Reflect or Calm Mind, or Snorlax
  enters with the answer already weakened. The team scrambles into special
  damage, Blastoise punishes with Mirror Coat, and a later Sunny Day turn flips
  the expected Water or recovery math.

Abandon conditions:

- The Snorlax answer is paralyzed, asleep, below threshold, or out of critical
  PP.
- Espeon gets Calm Mind boosts or Reflect turns that invalidate physical
  pressure.
- Sunny Day starts and the current plan depends on Water damage, clear-weather
  recovery, or a two-turn SolarBeam assumption.
- Blastoise can Mirror Coat the intended special attack for a decisive KO.
- Pikachu coverage proves the lead answer is not stable.
- Razor Leaf crit risk makes the lead answer too unstable to preserve the later
  Snorlax, Espeon, sun, or Blastoise plan.
- A type-chart, passive, item, weather, recovery, or damage fact contradicts
  the assumed route.

What information would flip the lead or first move:

- A lead candidate that beats Pikachu while remaining a valid answer to one of
  Red's later routes.
- A separate confirmed Snorlax answer, making the Pikachu answer more
  expendable.
- A damage range showing Espeon cannot set Reflect or Calm Mind safely.
- A damage range showing Blastoise is forced by physical pressure and Mirror
  Coat is not relevant.
- A weather or type-passive fact showing the planned Venusaur/Charizard pivot
  does or does not survive sun.

## Extracted Lesson

Red is not "beat Pikachu." Red is answer reservation under pressure. The opening
must handle a dangerous coverage lead while preserving the pieces that stop
screen setup, RestTalk anchoring, weather conversion, and Mirror Coat traps.
