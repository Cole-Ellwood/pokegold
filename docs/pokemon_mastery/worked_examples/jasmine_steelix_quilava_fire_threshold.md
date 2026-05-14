# Worked Example: Jasmine Fire-Pressure Threshold

Source fixture:
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`jasmine_steelix_vs_quilava_fire_threat`

Source boss roster: `data/trainers/parties.asm`, `JasmineGroup`.

Format: Gym Leader Lab romhack. This example uses local damage-debugger
evidence and local move data. It is a turn-choice drill, not a full boss
simulator result.

## Public State Pattern

```text
Boss active:
Jasmine Steelix, level 34, 69% HP, Metal Coat
Revealed moves: Iron Tail / Rock Slide
Bench: Magneton 76%, Forretress 100%, Scizor 92%, Skarmory 100%

Player active:
Quilava, level 34, 73% HP
Revealed moves: Flame Wheel / Quick Attack
Public priors: Dig plausible; stronger Fire coverage possible if obtained

Field:
No weather or screens
```

The hard part is not remembering a chart label. The hard part is deciding
whether the revealed Fire move actually forces Steelix to leave, whether
Skarmory is a safer pivot, and whether stronger hidden coverage should change
the answer.

## Local Damage Evidence

Damage-debugger ranges for this exact level/state profile:

```text
Steelix Rock Slide -> Quilava at 73%:
45-54 damage, 54-64% current HP

Steelix Earthquake -> Quilava at 73%:
29-35 damage, 35-42% current HP

Quilava Flame Wheel -> Steelix at 69%:
38-45 damage, 48-56% current HP

Quilava Fire Blast -> Steelix at 69%:
89-105 damage, 111-131% current HP

Quilava Dig -> Steelix at 69%:
18-22 damage, 23-28% current HP

Quilava Quick Attack -> Steelix at 69%:
1-2 damage

Quilava Flame Wheel -> Skarmory at full HP:
78-92 damage, 80-95% max HP

Quilava Fire Blast -> Skarmory at full HP:
180-212 damage
```

Local move data:

```text
Rock Slide: 75 BP, 90 accuracy, flinch effect
Earthquake: 100 BP, 100 accuracy
Flame Wheel: 60 BP, 100 accuracy
Fire Blast: 140 BP, 85 accuracy
Dig: 60 BP, 100 accuracy
```

## Candidate Move Classes

Best / acceptable in the fixture:

- Rock Slide. It deals the most relevant immediate damage and keeps pressure on
  Quilava without donating Skarmory to the same Fire branch.
- Earthquake if the plan values accuracy over the higher Rock Slide range, or
  if a miss branch is unacceptable for the larger route.

Wrong:

- Panic-switching to Skarmory only because Quilava has a Fire move. Skarmory
  does not solve the public damage problem here; it is badly punished by the
  same revealed move and removed by the stronger hidden branch.

Needs re-score:

- If Fire Blast is revealed, strongly implied by prior play, or known from the
  user's inventory path, Steelix preservation rises sharply.
- If Quilava falls to the 18% counterfactual range, Rock Slide or Earthquake
  become immediate conversion moves.
- If Steelix is lower or needed for a later boss route, preservation may
  dominate chip.

## Rule

Fire pressure is a threshold question, not a binary switch trigger:

```text
revealed damage is survivable:
obvious pivot is not safer into the same branch:
our attack creates meaningful pressure:
hidden stronger coverage is plausible but unconfirmed:
=> attack and track the hidden branch as answer-changing information
```

If the stronger branch becomes confirmed or highly likely, stop treating the
same turn as a patience drill. Re-score preservation, alternate pivots, and
whether Steelix still needs to stay healthy for Jasmine's later route.

## Boundary Flips

The paired mutations change one fact at a time:

```text
Quilava at 73% -> Quilava at 18%
Expected flip: pressure move becomes conversion; KO threshold dominates.

Fire Blast only possible -> Fire Blast confirmed
Expected flip: Steelix staying in becomes much harder to justify unless the
route is forced.

Skarmory healthy -> Skarmory already damaged or needed for another route
Expected flip: switch value falls even further; do not spend the backup answer
without a concrete payoff.
```

## Boss-Battle Transfer

Use this pattern when advising either side of a boss fight:

1. Do not switch just because a scary coverage family exists.
2. Compare the revealed range, the plausible stronger range, and the pivot's
   range separately.
3. If the pivot is not safer, preservation language is suspect.
4. If direct damage changes the next turn more than switching does, attack can
   be the disciplined line.
5. If the hidden branch becomes confirmed, abandon the old answer immediately.

## Failure Signs

- Calling the switch safe without checking the pivot's damage range.
- Treating revealed Flame Wheel and possible Fire Blast as the same branch.
- Staying in forever after the stronger branch becomes confirmed.
- Saying the attack is correct only from chart memory instead of damage,
  speed, route pressure, and next-turn consequences.
