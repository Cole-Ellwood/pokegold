# Worked Example: Lance Sequential Setup Wave Stress Test

Purpose: stress-test the sequential-converter lesson against Lance's serial
Dragon Dance / Quiver Dance route. This is a narrow live-advice drill for
handoffs between setup waves, not another full 30-turn ledger.

Local evidence:

- Lance route map: `../boss_route_maps/lance_turn1_route_sheet.md`.
- Lance pre-battle route sheet: `lance_pre_battle_route_sheet.md`.
- Lance 30-turn drill: `lance_30_turn_serial_setup_ledger_drill.md`.
- Roster source: `data/trainers/parties.asm`.
- Dragon Dance, Quiver Dance, Outrage category, Hyper Beam, Focus Band, and
  local typing notes:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.
- Generated mechanics reference:
  `../../agent_navigation/hack_mechanics_reference.md`.
- Outrage effective-category source:
  `engine/battle/type_passive_damage_mods.asm`.

Expert transfer source:

- Sequential converter recipe:
  `smogtours_gen4ou_670049_sequential_converter_pressure.md`.
- Smogon setup material:
  <https://www.smogon.com/smog/issue26/setting_up>.
- Smogon setup-sweeper material:
  <https://www.smogon.com/articles/ou-setup-sweepers>.
- Smogon risk/reward material:
  <https://www.smogon.com/resources/beginner/bw_risk_reward>.

## Pattern Being Tested

Bad shortcut:

```text
We stopped the first Dragon Dance user, so the setup problem is handled.
```

Better policy:

```text
Every denied setup wave has a cost. After paying it, check which Lance Pokemon
inherits the board and whether the answer is still live.
```

Lance's team punishes answer reuse. Steelix, Gyarados, Ampharos, Kingdra, and
Dragonite all present Dragon Dance routes, but local mechanics can make the
boosted attacking category different. Yanma presents a separate Quiver Dance
and Sleep Powder route, with Focus Band as a small but severe survival branch.

## Stress-Test State

Use this public-state prompt, then substitute the user's real team:

```text
Lance route just stopped:
  Steelix denied / Gyarados checked / Ampharos forced / Yanma removed /
  Kingdra contained

Cost paid:
  HP, sleep, paralysis, PP, item, status move, phaze/Haze use, sacrifice,
  revealed coverage, or answer chip

Lance routes still alive:
  Gyarados Dragon Dance / Hyper Beam
  Ampharos Dragon Dance as special-plus-Speed pressure
  Yanma Sleep Powder / Quiver Dance / Focus Band if not removed
  Kingdra Dragon Dance / Surf / Blizzard / Outrage
  Dragonite Dragon Dance / Outrage / Earthquake / Hyper Beam

Question:
  Which setup wave inherits the board next, and is our current answer still
  valid after the cost paid?
```

## Required Handoff Questions

After every successful setup denial turn, fill this:

```text
Setup wave stopped:
Answer used:
Cost paid by that answer:
Boost, lock, sleep, or recharge state left behind:
Next Lance setup wave:
Our remaining answer:
Can the previous answer still perform that job:
Move that prevents a free handoff:
What information would flip the answer:
```

If the answer is "keep attacking," prove that the next Lance setup wave does
not use that turn to become unanswerable.

## Handoff Cases

### Steelix Into Gyarados Or Ampharos

Steelix may be the opener, but it is not the format. If the player spends the
only anti-Dragon Dance control tool to beat Steelix, Gyarados or Ampharos may
inherit the board with a better matchup.

Failure sign:

- The advice says "Steelix is gone" without tracking whether phazing, Haze,
  status, or the speed-control piece is still available.

Correct pressure:

- Beat Steelix with the least exclusive answer possible, or convert the Steelix
  exchange into a clean entry for the Gyarados/Ampharos plan.

### Gyarados Into Kingdra

Gyarados and Kingdra should not share one vague Water/Dragon answer. Gyarados
can threaten physical Outrage and Hyper Beam; Kingdra can lean into Surf,
Blizzard, and different Outrage category evidence. One answer may cover both
only after HP, category, and coverage evidence say so.

Failure sign:

- The advice uses the Gyarados answer as a midgame pivot and later assumes it
  still handles Kingdra or Dragonite.

Correct pressure:

- Label whether the answer is for Gyarados, Kingdra, Dragonite, or all three.
  If it is shared, avoid spending it unless the trade removes a future route.

### Ampharos Into Yanma

Ampharos can change the special-side answer map with Dragon Dance, Thunder, and
Fire Punch. Yanma then attacks the tempo map with Sleep Powder, Quiver Dance,
and Focus Band. These are different problems; do not solve Ampharos by spending
the only sleep-safe or speed-safe Yanma route unless the remaining team covers
it.

Failure sign:

- The advice pivots the sleep absorber or anti-Quiver answer into Ampharos chip
  without naming who handles Yanma.

Correct pressure:

- Preserve a Yanma plan until sleep and Focus Band branches are either removed
  or no longer route-changing.

### Kingdra Into Dragonite

Kingdra is the biggest Dragonite-budget trap. The player often wants to use the
final Dragonite answer because Kingdra is threatening now. That is correct only
if the remaining roster still has a concrete Dragonite route afterward.

Failure sign:

- The advice uses the final answer on Kingdra and describes Dragonite later as
  a generic revenge-kill problem.

Correct pressure:

- Either solve Kingdra with a separate line, or spend the final answer only
  when Dragonite will be covered by lock punish, recharge punish, status,
  priority, sacrifice entry, or confirmed damage.

### Any Wave Into Dragonite

Dragonite is the final audit. If it enters after the anti-setup tools are
asleep, chipped, spent, or slower after Dragon Dance, the earlier successful
turns were only temporary.

Failure sign:

- The advice reaches Dragonite with "we still have coverage" instead of a
  named route through +1 Speed, Outrage lock, Earthquake, and Hyper Beam.

Correct pressure:

- Before Dragonite appears, name the exact remaining route: immediate KO,
  phaze/Haze, status, forced Outrage recipient, Hyper Beam recharge punish,
  controlled sacrifice into revenge, or priority threshold.

## Candidate Move Arbitration

Preserve rises when:

- the answer still uniquely covers a later setup wave;
- the current active can be handled by a less exclusive tool;
- the worst plausible handoff creates an irreversible Dragonite, Kingdra, or
  Yanma route.

Spend or trade rises when:

- the current boosted threat otherwise becomes unanswerable;
- the trade removes a setup wave and the remaining routes are covered;
- the spent piece has no remaining unique job or creates a clean entry to the
  next answer.

Attack rises when:

- damage denies the next boost, forces a lock/recharge, or creates a revenge
  threshold;
- the attacker does not expose the answer needed for the next setup wave.

Setup, recovery, or scouting falls when:

- any Lance Pokemon can use the turn for Dragon Dance or Quiver Dance;
- Yanma can use Sleep Powder before the route converts;
- the move does not improve the final Dragonite route.

## Example Verdict Shape

```text
Recommendation:
  attack / switch / preserve / trade / phaze / Haze / status / sacrifice

Why:
  We stopped [setup wave], but it cost [resource]. Lance's next likely handoff
  is [next setup wave], so this move protects or improves [specific answer].

Worst plausible branch:
  if we continue the old plan, Lance gets [Dragon Dance / Quiver Dance / sleep /
  Outrage lock / Hyper Beam burst] and our [answer] no longer performs its
  role.

What changes the answer:
  Speed after boost, Outrage category, Hyper Beam damage and recharge, Focus
  Band state, sleep target, remaining anti-setup PP, and local type/passive/
  damage evidence.
```

## Extracted Lesson

Lance is the champion-version of sequential converter pressure. The setup waves
are similar enough to invite lazy reuse of one answer, but different enough that
reuse can lose the battle. Strong advice must say which setup wave was stopped,
what it cost, which wave inherits next, and whether the final Dragonite route
is still alive.
