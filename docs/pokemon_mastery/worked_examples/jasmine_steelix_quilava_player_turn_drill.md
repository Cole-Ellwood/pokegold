# Worked Example: Jasmine Steelix vs Quilava Player-Turn Drill

Purpose: convert `jasmine_steelix_quilava_fire_threshold.md` into user-facing
advice from Quilava's side. The lesson is coverage-threshold discipline: choose
the move that changes the current route, and keep the miss or hidden-coverage
branch visible.

Mechanics profile: `romhack_gym_leader_lab`

Source position:

- `jasmine_steelix_quilava_fire_threshold.md`
- Fixture:
  `tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
  `jasmine_steelix_vs_quilava_fire_threat`
- Roster source: `data/trainers/parties.asm`, `JasmineGroup`
- Damage-debugger evidence listed in the source note.

## Public State

```text
Boss active:
  Steelix Lv34 at 69%, Metal Coat
  Revealed moves: Iron Tail / Rock Slide
  Bench: Magneton 76%, Forretress 100%, Scizor 92%, Skarmory 100%

Player active:
  Quilava Lv34 at 73%
  Revealed moves: Flame Wheel / Quick Attack
  Public priors: Dig plausible; stronger Fire coverage possible if obtained

Field:
  No weather or screens
```

Damage anchors from the source note:

```text
Quilava Flame Wheel -> Steelix at 69%:
  38-45 damage, 48-56% of Steelix's current HP.

Quilava Fire Blast -> Steelix at 69%:
  89-105 damage, 111-131% of Steelix's current HP.

Quilava Dig -> Steelix at 69%:
  18-22 damage, 23-28% of Steelix's current HP.

Quilava Quick Attack -> Steelix at 69%:
  1-2 damage.

Steelix Rock Slide -> Quilava at 73%:
  45-54 damage, 54-64% of Quilava's current HP.
```

## Live-Turn Advice

Recommendation: if Quilava has Fire Blast, use Fire Blast. If Fire Blast is not
available, use Flame Wheel. Confidence: high for the move class, with accuracy
and actual moveset as the main caps.

Plan: convert Quilava's active pressure before Steelix can use the turn to
attack, pivot, or become a later setup/Steel-core problem.

State read: Fire Blast removes Steelix from the shown range. Flame Wheel does
not remove Steelix immediately, but it is still the best revealed pressure move.
Dig and Quick Attack do not change the route enough from this HP state.

Win condition: either remove Steelix now or put it into a position where the
next Quilava action, pivot, or revenge move finishes the route without giving
Jasmine a free Steel-core reset.

Candidate ranking:

1. Fire Blast, if available: best. It converts the current position immediately
   from the shown damage range.
2. Flame Wheel: best revealed fallback. It creates meaningful pressure while
   Quilava survives the public Rock Slide range.
3. Switch: acceptable only if Quilava is uniquely needed for Forretress,
   Scizor, or Skarmory and another Steelix answer enters safely.
4. Dig or Quick Attack: bad from this state; the damage does not change the
   route enough.

Opponent's best route: hit Quilava with Rock Slide or pivot the Steel-core
position so Quilava is forced to keep taking risks later.

Worst plausible branch: Fire Blast misses or is unavailable, Steelix lands Rock
Slide, and Quilava becomes too low to continue handling Jasmine's later Steel
pieces. This does not make weak moves better; it means the next turn must be
re-scored instead of autopiloted.

Key piece: Quilava may be the current pressure piece for several Jasmine
routes. Do not trade its HP casually if Forretress, Scizor, or Skarmory still
need it.

What changes the answer:

- Quilava does not know Fire Blast.
- Quilava is lower than the public HP or cannot survive Rock Slide.
- Steelix is already in Flame Wheel or Quick Attack cleanup range.
- A safer teammate handles Steelix while Quilava is required later.
- Weather, item, passive, or exact damage evidence differs from the source
  fixture.

Next turn if it works:

- If Fire Blast hits, re-score the incoming Jasmine route; do not assume the
  whole Steel fight is solved.
- If Flame Wheel leaves Steelix alive, check Quilava's remaining HP and whether
  another Flame Wheel, switch, or priority/pivot route is safest.
- If Steelix reveals a new move or switches, update the route map immediately.

## Lesson Extracted

Coverage pressure is not a binary "switch or stay" question. Compare the
confirmed move, stronger possible move, miss branch, pivot safety, and the
piece's later jobs. The right attack is the one that improves the route from
this HP state.
