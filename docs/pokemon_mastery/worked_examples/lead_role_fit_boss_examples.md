# Worked Example: Lead Role Fit

Status: constructed boss-facing study example. This is not exact turn advice
until the user's team, HP, moves, items, bench, and damage evidence are known.

Purpose: practice choosing a lead by whole-fight role, not by the best visible
turn-1 matchup.

Source basis:

- `../cookbook.md` recipe: Lead Role Fit Test.
- `../boss_route_maps/bugsy_turn1_route_sheet.md`
- `../boss_route_maps/misty_turn1_route_sheet.md`
- `../boss_route_maps/red_turn1_route_sheet.md`

Expert principle:

- Smogon lead articles treat the lead as a team-structure choice. A lead sets
  pace, but it must also fit the rest of the battle plan. A Pokemon that wins
  turn 1 and becomes dead weight, or spends the only later answer, can be the
  wrong lead.

## Case 1: Bugsy

Boss route:

```text
Ariados status/drain
-> Ledian Reflect / Quiver Dance / Baton Pass
-> Scyther Swords Dance or supported cleanup
```

Bad lead logic:

```text
Lead the best Fire/Flying pressure because it beats Ariados fastest.
```

Why this can fail:

```text
If that Pokemon is also the only Scyther answer, Ariados Toxic or Ledian support
can spend the exact piece needed later.
```

Better lead question:

```text
Which lead pressures Ariados or Ledian while preserving the piece that stops
supported Scyther?
```

Move class that rises:

- Immediate pressure if it denies support.
- Pivot if the current lead is the only Scyther answer.
- Status only if it changes the Scyther route before Ledian can pass support.

## Case 2: Misty

Boss route:

```text
Politoed Rain Dance / Hypnosis
-> Starmie Recover + rain pressure
-> Lapras rain extension
-> Lanturn paralysis
```

Bad lead logic:

```text
Lead the strongest Water answer into Politoed.
```

Why this can fail:

```text
If that Pokemon is also the only Starmie/Lapras answer, Politoed Hypnosis or
rain damage can remove the whole later route before Misty's main threats appear.
```

Better lead question:

```text
Can this lead pressure Politoed while surviving both Hypnosis branches and still
leaving a separate answer to Starmie or Lapras?
```

Move class that rises:

- Attack if it forces Politoed before rain payoff.
- Sleep-buffer pivot if losing the lead to Hypnosis loses the fight.
- Weather denial or stalling only if the user can spend Misty's rain turns
  without giving Starmie free Recover pressure.

## Case 3: Red

Boss route:

```text
Pikachu coverage / ExtremeSpeed
-> Espeon Reflect or Calm Mind
-> Snorlax RestTalk Curse
-> Venusaur/Charizard sun
-> Blastoise Mirror Coat / coverage
```

Bad lead logic:

```text
Lead the Pokemon that beats Pikachu most cleanly.
```

Why this can fail:

```text
If that Pokemon is also the only Snorlax answer, Espeon answer, sun answer, or
safe Blastoise attacker, winning turn 1 can still lose the fight.
```

Better lead question:

```text
Which lead handles Pikachu without being required for the next two boss routes?
```

Move class that rises:

- Direct KO if it does not expose the later route map.
- Conservative pivot if Pikachu coverage reveals the lead is the wrong answer.
- Scouting only if the revealed Pikachu move changes the later preservation map.

## Extracted Rule

Lead selection should leave the user able to answer the boss's second route.
If the lead wins turn 1 but loses the only later answer to status, chip, item
loss, or bad positioning, it is not a good lead.
