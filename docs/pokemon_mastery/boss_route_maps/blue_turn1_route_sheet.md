# Blue Turn-1 Route Sheet

Status: local boss route map. This is not a final player plan until the user's
team, HP, moves, items, and current box options are known.

Local evidence:

- Roster source: `data/trainers/parties.asm`
- Boss Pokemon stats/types: `data/pokemon/base_stats/*.asm`; Blue is a mixed
  roster, not a single-type gym plan.
- Move table: `data/moves/moves.asm` and
  `docs/agent_navigation/hack_mechanics_reference.md`
- Opening policy source:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md`; Blue is in
  `AdaptiveLeadMap`, so the opening can be Pidgeot, Porygon2, or Gyarados
  rather than guaranteed Pidgeot.
- Choice Band source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  it boosts physical damage by 1.5x and locks the user to the first chosen
  move until reset.
- Dragon Dance source: `docs/agent_navigation/gen2_vs_modern_mechanics.md`;
  this hack boosts the user's current higher offensive stat plus Speed.
- Outrage source: `docs/agent_navigation/gen2_vs_modern_mechanics.md` and
  `engine/battle/type_passive_damage_mods.asm`; Dragon users can make Outrage
  use the physical category under the documented stat condition.
- Hyper Beam source: `data/moves/moves.asm` and
  `engine/battle/effect_commands.asm`; local Hyper Beam is physical, 180 BP,
  90 accuracy, and creates a recharge obligation.
- Priority caveat: Quick Attack and ExtremeSpeed share `EFFECT_PRIORITY_HIT`
  in `data/moves/moves.asm`, so use local priority rather than modern
  ExtremeSpeed brackets.
- Life Orb, Muscle Band, Soft Sand, Leftovers, contact flags, and type-boost
  items: `docs/agent_navigation/gen2_vs_modern_mechanics.md`,
  `docs/agent_navigation/hack_mechanics_reference.md`, and
  `data/moves/contact_flags.asm`.
- Expert principle sources: Smogon wallbreaking, Choice-lock, Gyarados,
  Porygon2, Tauros, Rhydon, priority, and win-condition planning material.

Boss roster:

```text
Lv65 Pidgeot @ Choice Band:
  Wing Attack / Double-Edge / Steel Wing / Quick Attack

Lv65 Porygon2 @ Leftovers:
  Recover / Tri Attack / Thunderbolt / Ice Beam

Lv67 Gyarados @ Leftovers:
  Dragon Dance / Outrage / Surf / Hyper Beam

Lv67 Tauros @ Muscle Band:
  Double-Edge / Earthquake / Rock Slide / Iron Tail

Lv69 Rhydon @ Soft Sand:
  Earthquake / Rock Slide / Megahorn / Roar

Lv70 Arcanine @ Life Orb:
  Flamethrower / ExtremeSpeed / Crunch / Outrage
```

Boss likely openings:

- Blue is source-listed as adaptive first-three, not fixed Pidgeot.
- Plan for Pidgeot / Porygon2 / Gyarados, with Pidgeot favored by the current
  weighted opener rule.
- Player-side planning may use this boss roster and opener policy before the
  fight. Blue's ordinary boss AI still must not know the player's unrevealed
  team, hidden moves, hidden item, private stats, or current-turn input.

## Boss Routes

Pidgeot route:

- Goal: use Choice Band to force immediate physical damage, then use the lock
  only if the chosen move is not punishable.
- What it punishes: fragile leads, ignoring Quick Attack range, and switching
  before the Choice Band lock is known.
- Denial idea: after Pidgeot attacks, record the locked move immediately.
  Double-Edge recoil, Quick Attack range, and Steel Wing / Wing Attack contact
  all change what can pivot in safely.

Porygon2 route:

- Goal: use Recover, Leftovers, Tri Attack, Thunderbolt, and Ice Beam to become
  a durable mixed-coverage bridge that keeps Blue from losing tempo after the
  lead exchange.
- What it punishes: shallow chip, single-resist switching, and using a slow
  setup route that cannot break Recover.
- Denial idea: force a damage threshold, status, PP pressure, or setup denial
  before Porygon2 starts erasing progress. Treat it as a route stabilizer, not
  as dead time.

Gyarados route:

- Goal: use Dragon Dance and Leftovers to turn Outrage, Surf, or Hyper Beam
  into a midgame or endgame conversion route.
- What it punishes: spending the anti-setup answer on Pidgeot or Tauros, and
  assuming a Water/Dragon answer survives after one boost.
- Denial idea: preserve a Gyarados answer before turn 1. If Dragon Dance
  happens, re-score Speed, Outrage category, Hyper Beam burst, and whether the
  recharge window is actually punishable.

Tauros route:

- Goal: use high Speed, Muscle Band, Double-Edge, and broad physical coverage
  to break the player's defensive map without needing setup.
- What it punishes: relying on one Normal answer that loses to Earthquake, Rock
  Slide, or Iron Tail, and ignoring Double-Edge recoil as a two-sided clock.
- Denial idea: do not let Tauros remove the piece that still answers Gyarados
  or Arcanine unless the trade opens a forced route. Recoil can make pivoting
  correct if the next hit is survivable.

Rhydon route:

- Goal: use Soft Sand Earthquake, Rock Slide, Megahorn, and Roar to force
  switches, deny setup, and punish Electric or physical lines.
- What it punishes: Electric-only pressure, setup plans that can be Roared, and
  ignoring Blue's slow but powerful physical breaker.
- Denial idea: exploit Rhydon's low Speed and special vulnerability only with
  local type/passive/damage evidence. Do not assume a special attacker is safe
  if Pidgeot, Tauros, or Arcanine still needs that piece weakened.

Arcanine route:

- Goal: finish or break with Life Orb Flamethrower, ExtremeSpeed, Crunch, and
  Outrage while recoil acts as both cost and clock.
- What it punishes: low-HP cleaners, Psychic/Ghost-style pivots that lose to
  Crunch, and assuming Speed control beats priority.
- Denial idea: track ExtremeSpeed range separately from normal Speed order and
  include Life Orb recoil in both directions: it may open the KO, but it also
  may make Arcanine self-chip into range.

## Player Plan Template

Primary route:

- Blue is an answer-map fight. The player should cover the adaptive opening
  set of Pidgeot / Porygon2 / Gyarados while preserving answers to Gyarados
  setup, Tauros/Rhydon physical breaking, Porygon2 recovery, and Arcanine
  priority.

Backup route:

- If Pidgeot locks into a hard-to-punish move, or if Porygon2 stabilizes the
  fight, rebuild around the next Blue route rather than tunnel on the lead. The
  later fight can be won by denying Dragon Dance, exploiting recoil/lock, or
  forcing recovery turns.

Best lead profile:

- A lead that has a real first-turn job into Pidgeot, Porygon2, and Gyarados
  without being the only Gyarados or Arcanine answer. The first move should
  either exploit Pidgeot's lock, force Porygon2 into a non-free recovery map, or
  deny Gyarados a clean Dragon Dance.

Avoid as lead:

- The only Gyarados denial piece if Pidgeot can chip it into +1 range or if
  Blue can simply open Gyarados.
- A fragile fast cleaner that dies to Quick Attack or later ExtremeSpeed.
- A passive wall that lets opening Porygon2 Recover-loop immediately or opening
  Gyarados boost for free.
- A one-type answer map that ignores Tauros, Rhydon, and Arcanine coverage.

First-turn question:

```text
Which adaptive opener appeared?

Pidgeot: can we identify and punish the Choice Band lock without spending the
Gyarados or Arcanine answer?

Porygon2: can we force a real threshold before Recover and Leftovers erase
progress?

Gyarados: can we deny Dragon Dance immediately, or name the Haze, phaze, status,
damage, forced-lock, sacrifice, or revenge line after a boost?
```

If Blue opens Pidgeot:

- Treat the first attack as a Choice Band lock question. Record the locked move
  immediately and decide whether the punish preserves the Gyarados answer.

If Pidgeot locks into Double-Edge:

- Track recoil and ask whether the player can pivot through the lock without
  exposing the Gyarados or Arcanine answer.

If Pidgeot locks into Quick Attack:

- A weak priority lock may be a punish window, but only if the switch-in does
  not invite Gyarados, Rhydon, or Porygon2 into the exact route Blue wants.

If Porygon2 enters:

- Decide whether the live route is Recover stall, BoltBeam coverage, Tri Attack
  secondary pressure, or simply forcing the player to show the breaker too
  early.

If Blue opens Porygon2:

- Do not treat the fight as a failed Pidgeot plan. The live question becomes
  whether the lead can create a real threshold before Recover and Leftovers
  erase progress, without revealing or spending the Gyarados answer too early.

If Blue opens Gyarados:

- The anti-setup plan is immediate, not a later preservation note. Deny Dragon
  Dance or force a damaging line while keeping Arcanine priority and Tauros
  coverage in the remaining answer map.

If Gyarados uses Dragon Dance:

- Re-score under local mechanics. Determine whether phazing/Haze, status,
  immediate damage, forced Outrage, Hyper Beam recharge, priority, or sacrifice
  is the available denial route.

If Rhydon uses Roar:

- Setup and slow recovery plans may be invalid. If Roar is live, direct damage
  or status may outrank boosting.

If Arcanine enters:

- Do not call a faster Pokemon safe until ExtremeSpeed and Life Orb recoil math
  are checked.

Worst plausible branch:

- The player chooses a Pidgeot-only lead plan, Blue opens Porygon2 or Gyarados,
  and the first turn either lets Recover stabilize or gives Dragon Dance a free
  conversion. The backup answer then has to cover Tauros/Rhydon and Arcanine
  while already behind.

Abandon conditions:

- Blue opens Porygon2 or Gyarados instead of Pidgeot, invalidating the
  Choice-lock-first script.
- Pidgeot's lock is not the one the plan expected.
- The Gyarados answer is below the boosted-damage threshold or has been forced
  to take Pidgeot/Tauros chip.
- Porygon2 can Recover through the current damage plan.
- Rhydon can Roar away setup or force the wrong switch.
- Arcanine's ExtremeSpeed range covers the intended cleaner.
- Type-chart, passive, item, contact, lock, or damage evidence contradicts the
  assumed answer.

Snorlax study transfer:

- Blue teaches mixed-roster answer mapping. The useful GSC transfer is to stop
  thinking "I beat the lead"; every lead exchange is judged by whether it
  preserves enough pieces for the later setup, recovery, breaker, phazer, and
  priority routes.
