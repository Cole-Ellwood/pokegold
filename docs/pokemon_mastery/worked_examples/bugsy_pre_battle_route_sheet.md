# Worked Example: Bugsy Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Bugsy as an early support-chain,
poison/drain, screen, Baton Pass, setup, and priority-cleanup fight. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `BugsyGroup`.
- Boss route map: `../boss_route_maps/bugsy_turn1_route_sheet.md`.
- Quiver Dance, Reflect, Baton Pass, Swords Dance, Quick Attack, Wing Attack,
  Leech Life, Toxic, Giga Drain, Berry, SilverPowder, move categories, and
  local type-chart references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Baton Pass source: `../../engine/battle/move_effects/baton_pass.asm`; it
  switches to another party member and resets some non-passed temporary states
  such as Disable and attraction.
- Reflect source: `../../engine/battle/effect_commands.asm`; local screens use
  five-turn counters.

Expert study anchors:

- Smogon Baton Pass material:
  https://www.smogon.com/rs/articles/baton_pass
- Smogon DPP Baton Pass material:
  https://www.smogon.com/dp/articles/baton_pass_chains
- Smogon setup material:
  https://www.smogon.com/smog/issue26/setting_up
- Smogon lead material:
  https://www.smogon.com/smog/issue10/leads

Extracted source lesson: support chains should be judged by what reaches the
receiver, not by the pass user's immediate damage. Setup is correct only when
the punish is survivable and the boost changes a concrete route. The best lead
is the one that fits the whole plan, not necessarily the one that wins the
visible first one-on-one.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Bugsy

Known boss roster:
  Lv15 Ariados @ Berry / Lv15 Ledian @ Berry / Lv17 Scyther @ SilverPowder

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Scyther answer, a way to stop or punish Ledian's support
  chain, and a plan for Ariados Toxic if the lead is the later Scyther answer;
  exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  Reflect lasting five turns, Quiver Dance raising Special Attack / Special
  Defense / Speed, Baton Pass switching while retaining passable battle state,
  Swords Dance boosting Scyther's physical route, Quick Attack using the local
  priority-hit tier, SilverPowder boosting Bug damage, Berry healing HP, and
  local type/passive evidence being required for any matchup claim

Checkpoint constraints:
  level cap 17, one badge, Old Rod available from Route 32, Surf not usable,
  and no Goldenrod TM access. A Fire starter can use checkpoint-real early Fire
  moves such as Ember, but a Fire Blast plan is not valid before Bugsy without
  separate evidence.

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether the lead can remove Ariados
  before Toxic matters, whether Ledian can survive long enough to pass support,
  whether the Scyther answer survives behind Reflect or after Swords Dance, and
  whether Quick Attack reaches the intended cleaner after early chip
```

## Output Shape

Primary route:

- Stop Bugsy from converting low early damage into supported Scyther. Ariados
  can poison or drain the later answer, Ledian can create Reflect and Quiver
  Dance pressure before passing, and Scyther can use Swords Dance or priority
  to turn a small opening into the fight's decisive route.

Backup route:

- If Ariados poisons the Scyther answer or Ledian gets Reflect / Quiver Dance
  before being removed, rebuild immediately. The backup route should name
  whether the player still has direct KO pressure, phazing/Haze, priority,
  status, a controlled sack into the answer, or enough HP to survive boosted
  Scyther.

Boss route priority:

```text
immediate:
  Ariados Toxic if it hits the only Scyther answer.
  Ledian Reflect if it changes Scyther's survival or setup threshold.
  Ledian Baton Pass after Quiver Dance if the receiver converts immediately.

accumulating:
  Ariados Leech Life / Giga Drain if weak chip lets it buy too many turns.
  Reflect turns if the player's Scyther answer relies on physical damage.
  Berry healing if the damage plan only barely crosses a threshold.

endgame:
  Scyther Swords Dance once the answer is poisoned, chipped, or blocked by
  Reflect.
  Scyther Quick Attack cleanup after the player's faster answer falls into
  priority range.
```

Boss route to deny first:

- Deny the support that makes Scyther safe. If the player's lead is the only
  Scyther answer, preserving that piece may be more important than winning the
  Ariados exchange quickly. If Ledian is free to Reflect, boost, and pass, the
  low-damage support Pokemon is the urgent route.

Boss route that can be delayed:

- Ariados can be delayed only when Toxic does not hit a required answer and its
  drain damage does not change Scyther ranges. If it poisons or chips the one
  Scyther answer, Ariados was not harmless.

- Scyther can be delayed while the answer is healthy and Ledian has not passed
  support. It cannot be delayed once Reflect, boosts, poison, or Quick Attack
  range changes the answer map.

Best lead profile:

- A lead that pressures Ariados or Ledian without being the only supported-
  Scyther answer. It should either remove Ariados quickly, make Ledian's pass
  unsafe, absorb Toxic without losing a later role, or pivot cleanly into the
  actual Scyther answer.

Avoid as lead:

- The only Scyther answer if Ariados can poison it or Ledian can force it to
  spend HP before Scyther appears.
- A passive setup lead that lets Reflect plus Quiver Dance plus Baton Pass
  happen before it changes a KO or denial threshold.
- A status-only plan if the status does not stop Ledian from passing or
  Scyther from converting.
- A route that spends the Fire/Flying/Rock-style answer on Ariados chip while
  supported Scyther remains the real converter.

First move plan:

- Give turn 1 one job: preserve or improve the Scyther-answer map. Attacking is
  good if it removes Ariados before Toxic/drain matters or forces Bugsy into a
  bad Ledian entry. Pivoting is good if the current lead is the only later
  answer. Setup is good only if it denies the support chain before Scyther can
  inherit the position.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Ariados's Poison Sting, Giga Drain, Toxic, and Leech Life branches
  against the lead's later Scyther role.

Turn 2:
  If Ariados was denied, prepare for Ledian's Reflect / Quiver Dance / Baton
  Pass route. If Toxic landed, rebuild around whether the poisoned piece is
  still allowed to answer Scyther.

Turn 3:
  Start the ledger: Reflect turns, Ledian boosts, Baton Pass availability,
  Scyther boost state, Berry/SilverPowder item effects, and Quick Attack
  cleanup ranges.
```

Piece to preserve:

- The Scyther answer by default. It may be needed only at the end, but the
  early Ariados/Ledian turns are designed to weaken or bypass it.

- Any Haze, phaze, status, priority, or immediate-KO resource that can stop
  supported Scyther after a pass or Swords Dance.

Piece that can be spent:

- A lead that already denied Ariados and has no unique job against Ledian or
  Scyther.

- A statused or chipped early-game piece only if spending it gives clean entry
  to the actual Scyther answer before Ledian can pass.

Worst plausible branch:

- The player spends the only Scyther answer to beat Ariados, lets Ledian set
  Reflect or Quiver Dance, and then faces Scyther behind support with no piece
  healthy enough to survive Swords Dance pressure or Quick Attack cleanup.

Abandon conditions:

- The only Scyther answer is poisoned, below its required threshold, or forced
  to enter through Reflect-boosted damage math.
- Ledian has Reflect or Quiver Dance and can Baton Pass before being removed.
- Scyther enters high enough to set Swords Dance or attack through the current
  answer.
- Quick Attack reaches the intended cleaner after early chip.
- Type-chart, passive, item, screen, boost, or damage evidence contradicts the
  assumed answer.

What information would flip the lead or first move:

- Whether the lead can remove Ariados before Toxic matters.
- Whether the lead is also the only Scyther answer.
- Whether Ledian survives the proposed hit and gets Reflect or Baton Pass.
- Whether the player has Haze, phazing, priority, or a safe sacrifice after
  Ledian passes support.
- Whether Scyther survives the answer behind Reflect or after Berry/SilverPowder
  effects are applied.
- Whether Quick Attack range changes the value of preserving a faster cleaner.

## Extracted Lesson

Bugsy is not three separate one-on-ones. Bugsy is the early version of a
support-chain fight: Ariados taxes the future answer, Ledian tries to make the
receiver safe, and Scyther converts the support. The correct opening is the
one that either breaks the chain immediately or preserves the piece that still
beats supported Scyther after the chain changes the board.
