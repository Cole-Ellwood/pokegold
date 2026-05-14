# Pre-Battle Route Sheet

Purpose: use this before a planned boss fight. It turns "what should I do from
turn 1?" into a route plan plus abandon conditions. It is not a replacement for
live turn advice; it is the opening map that live advice updates.

Source basis:

- Smogon's Team Preview and Getting Started material is analogy-only here.
  Gen 2 and Gym Leader Lab do not have symmetrical team preview. For planned
  boss fights, use source-known boss rosters and opening policy to form a route
  map; do not assume the boss AI sees the unrevealed player team.
- Smogon's lead articles treat the first Pokemon as a team-level choice, not
  just a strong first-turn attack: a lead sets pace and should fit the team's
  later jobs.
- Smogon's long-term thinking article frames skill as knowing whether the
  battle is developing toward the plan.
- Smogon's risk/reward article says to compare teams, identify the pieces that
  can change the game, and adjust risk based on whether the matchup is ahead,
  stable, or bad.
- Smogon's planning article stresses a main plan plus backup plan.
- Smogon's Battle Maison guidance adds the in-game lesson: known trainer sets
  and threatlists should expose glaring weaknesses before battle, and a small
  team needs a reasonable play line against every severe threat it may face.
- Local boss opening policy is source-specific:
  `docs/pokemon_mastery/romhack_deltas/boss_opening_policy.md`.

Information model:

- Player-side advisor before a planned boss fight: may use the known boss
  roster, fixed/adaptive opener source, local mechanics docs, and the user's
  declared team if the user provides it.
- Boss AI: may use only public battle state and revealed player information,
  plus explicitly allowed source/legal priors. It must not route from the full
  player team before that team is revealed.
- Vanilla GSC review: start from the actual lead and revealed information over
  time, not later-generation team preview.

## Inputs Needed

```text
Mechanics profile:
Boss:
Known boss roster:
Known boss fixed/adaptive opener source:
Boss legal opener family:
Our team:
Our lead candidates:
Our irreplaceable pieces:
Our one-time resources:
Known romhack deltas that matter:
Missing evidence:
```

Missing evidence should be explicit. Examples: exact damage, type-chart claim,
passive type ability, gender for Attract, item behavior, speed relation, PP, or
sleep-clause state.

## Output Shape

```text
Primary route:
Backup route:
Boss route priority:
  immediate:
  accumulating:
  endgame:
Known-set threat audit:
  severe threat:
  answer:
  entry path:
  backup if answer is crippled:
  unknown fact that flips the line:
Boss likely openings:
Boss route to deny first:
Boss route that can be delayed:
Best lead:
First move plan:
First 3 turns as intentions, not a script:
Piece to preserve:
Piece that can be spent:
Degraded jobs if plan A fails:
Worst plausible branch:
Abandon conditions:
What information would flip the lead or first move:
```

## Procedure

1. Compare routes before comparing moves. Which side has the clearer endgame if
   both play normally?
2. Sort the boss routes by urgency:
   - immediate: can win or cripple the plan now;
   - accumulating: becomes dangerous after support, clocks, or repeated
     switches;
   - endgame: needs support first but must be preserved against from turn 1.
3. List the boss fixed opener or source-supported adaptive opener family. If
   the lead is fixed by local trainer data, use that. If the opening is
   variable, filter for choices that fit the source policy and boss incentives
   instead of planning for every legal start equally. Do not assume the boss
   knows the player's unrevealed team.
4. Name our fastest real progress route. "Hit it hard" only counts if it
   changes a KO, recovery, switch, status, setup, or endgame threshold.
5. Audit known-set threats before choosing the lead. Every severe boss threat
   should have a reasonable play line, or the sheet should label the matchup as
   forced risk and name the mitigation.
6. Choose a lead that starts progress or denies the boss route while preserving
   the piece needed for the later boss anchor.
7. Give the first move a job: remove, force recovery, status, set hazards,
   scout, pivot, set up, or preserve.
8. Write the first three turns as intentions. Do not script through misses,
   crits, wakes, switches, reveals, or unexpected damage.
9. For each key piece, name the narrower job it still has if the first plan
   fails: one pivot, one revenge hit, one setup chance, one status move, one
   sacrifice entry, or no remaining job.
10. Decide risk posture:
   - Ahead: minimize risk and deny the boss's game changer.
   - Stable: cover the worst plausible branch while improving the route.
   - Behind: take calculated risk if safe play loses slowly.

## Failure Signs

- The chosen lead is also the only answer to the boss's ace and can be crippled
  before doing anything important.
- The first move gains generic chip but does not change a later threshold.
- The plan spends sleep, a setup chance, or a sacrifice without naming what
  route becomes better.
- The plan assumes a romhack type, passive, item, or damage fact without local
  evidence.
- The plan has no backup if the boss opens with status, setup, or a switch.
- The plan treats a miss, sleep, chip, or lost matchup as making a Pokemon
  useless without checking whether it still has a narrower job.
- The plan imports later-generation Team Preview and assumes both sides know
  all six Pokemon before turn 1.
