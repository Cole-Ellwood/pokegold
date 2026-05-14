# Worked Example: Clair Hidden-Coverage Stay-In Test

Source fixture:
`tools/boss_ai_preference/fixtures/boss_ai_preference_fixtures.json`,
`clair_dragonair_vs_suicune_hidden_ice_beam`

Source boss roster: `data/trainers/parties.asm`, `ClairGroup`.

Format: Gym Leader Lab romhack. This example uses local damage-debugger
evidence, but it is still a planning drill, not a full boss simulator result.

## Public State Pattern

```text
Boss active:
Clair Dragonair, level 38, 74% HP, Expert Belt
Revealed moves: Thunder / Outrage
Bench includes Kingdra, Mantine, Steelix, Gligar, and another Dragonair

Player active:
Suicune, level 40, 88% HP
Revealed move: Surf
Public priors: Ice coverage and Rest are plausible

Field:
No weather or screens
```

The key public clue is not the type label. It is behavior plus damage: Surf is
small into Dragonair, so if Suicune stays in, the boss should ask what hidden
move would justify that stay-in.

## Local Damage Evidence

Damage-debugger ranges for this exact level/state profile:

```text
Suicune Surf -> Dragonair at 74%:
18-22 damage, 20-24% current HP

Suicune Ice Beam -> Dragonair at 74%:
100-118 damage, 111-131% current HP, guaranteed KO from current HP

Suicune Blizzard -> Dragonair at 74%:
125-148 damage, 139-164% current HP, guaranteed KO

Dragonair Thunder -> Suicune at 88%:
61-72 damage, 40-47% current HP

Dragonair Outrage -> Suicune at 88%:
32-38 damage, 21-25% current HP

Suicune Ice Beam -> Kingdra at full HP:
23-28 damage, 18-22% max HP

Suicune Blizzard -> Kingdra at full HP:
30-36 damage, 23-28% max HP

Suicune Surf -> Kingdra at full HP:
7-9 damage, 5-7% max HP
```

The numbers explain the route. Dragonair's Thunder is meaningful but does not
remove Suicune. Staying in risks losing Dragonair immediately if the hidden Ice
coverage branch is real. Kingdra does not win the game by switching in, but it
keeps Clair's route alive and forces a re-score from a safer board.

## Candidate Move Classes

Best / acceptable in the fixture:

- Switch to Kingdra, then re-score.
- Switch to Mantine if Kingdra is unavailable or a different route must be
  preserved.

Wrong:

- Thunder as a default damage move when Suicune staying in is already public
  evidence for a dangerous hidden branch.

Catastrophic:

- Outrage when the lock lets Suicune reveal the hidden punish or pivot around
  the commitment.

## Rule

When the opponent stays in despite a low-impact revealed move, treat the stay
as information:

```text
revealed move does not justify staying:
hidden punish is plausible:
punish removes or cripples the active:
bench pivot preserves the route:
direct damage does not force a KO:
=> preserve and re-score
```

If the hidden punish is no longer plausible, or if the opponent is forced to
stay for a different reason, direct pressure can rise again.

## Boundary Flip

The paired mutation changes one fact:

```text
Hidden Ice punish plausible -> hidden Ice punish no longer plausible
```

With the hidden punish removed from the public branch model, Thunder can become
the better move because it pressures Suicune immediately and Dragonair is no
longer risking the whole route to a severe unrevealed branch.

## Boss-Battle Transfer

Use this pattern when advising either side of a boss fight:

1. If the opponent's revealed move is weak but they stay in, ask what hidden
   move or item branch makes staying rational.
2. Do not assume the hidden move exists as a fact.
3. Do price the branch if it is legal, plausible, severe, and the opponent is
   incentivized to use it.
4. Preserve the exposed route piece when the direct attack does not force a
   decisive result.
5. Re-score immediately after the hidden move is revealed, disproven, or made
   irrelevant by HP, status, lock-in, or switching.

## Failure Signs

- Calling Thunder correct only because it is Dragonair's biggest visible
  damage.
- Calling the switch cowardly without comparing the hidden-punish branch to the
  reward from immediate damage.
- Treating the hidden move as guaranteed instead of plausible.
- Ignoring that Kingdra's value is preservation and re-score, not immediate
  victory.
