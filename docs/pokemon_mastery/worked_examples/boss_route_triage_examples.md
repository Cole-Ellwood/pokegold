# Worked Example: Boss Route Triage

Purpose: practice choosing the first plan when a boss has several routes, not
just one visible lead matchup.

Source basis:

- `../cookbook.md` recipe: Boss Route Triage.
- `../boss_route_maps/blue_turn1_route_sheet.md`
- `../boss_route_maps/red_turn1_route_sheet.md`
- `../boss_route_maps/will_turn1_route_sheet.md`
- Smogon Team Preview sources, used only as an analogy: when roster information
  is legitimately known from boss data, infer the opponent's plan, name the
  roadblocks to our plan, estimate likely openings, and stay flexible when
  exact opening policy or mechanics remain uncertain. Do not import the preview
  mechanic itself into Gen 2 or Gym Leader Lab.

## Pattern

Public roster:

```text
Immediate routes:
Accumulating routes:
Endgame routes:
Shared player answers:
Single-use answers:
Lead risk:
First route to deny:
Route that can be delayed:
Abandon condition:
```

Decision:

```text
Choose the opening that denies the route that becomes hardest to stop after one
free turn, while preserving any piece that is the only answer to a later route.
```

## Blue Shape

Immediate routes:

- Choice Band Pidgeot can force early physical damage and reveal a lock.
- Tauros and Arcanine can punish low-HP or overcommitted answers later.

Accumulating routes:

- Porygon2 can Recover away weak progress.
- Rhydon can Roar or punish Electric-only pressure.

Endgame route:

- Gyarados can convert with Dragon Dance, Outrage, Surf, or Hyper Beam if the
  anti-setup answer is spent during the Pidgeot exchange.

Triage:

- Do not lead the only Gyarados answer just because it beats Pidgeot. The first
  plan should exploit Pidgeot's lock or recoil while keeping Gyarados denial
  intact.

Answer-changing information:

- Pidgeot's locked move.
- Whether Porygon2 can Recover through the current damage plan.
- Whether the Gyarados answer survives one boosted hit under local mechanics.
- Arcanine ExtremeSpeed range and Life Orb recoil math.

## Will Shape

Immediate routes:

- Forretress can set Spikes, poison, scout with Protect, or trade Explosion.
- Alakazam can punish an over-simple special pivot if it enters early.

Accumulating routes:

- Starmie can erase the player's hazard route with Rapid Spin.
- Xatu can create a Future Sight turn that stacks with later pressure.

Endgame route:

- Slowbro can become a Rest/Amnesia anchor if it gets a free boost and the team
  lacks physical pressure, phazing, Haze, status, or Rest-turn punishment.

Triage:

- Pressure Forretress without using the only Alakazam/Houndoom/Slowbro answer
  as the lead. If Forretress gets Spikes, immediately decide whether the next
  route is to remove hazards, punish Starmie, or shorten the game before
  Slowbro stabilizes.

Answer-changing information:

- Whether the lead is poisoned or exploded on.
- Whether Starmie can spin cheaply.
- Whether Slowbro has used Amnesia.
- Whether Houndoom threatens the stay line, switch line, or both with Pursuit.

## Red Shape

Immediate routes:

- Pikachu's Light Ball special coverage plus ExtremeSpeed can damage the wrong
  lead and put a cleaner into priority range.
- Espeon can start Reflect or Calm Mind if the opening is passive.

Accumulating routes:

- Venusaur or Charizard can start Sunny Day, changing damage and recovery
  clocks.
- Blastoise can punish special attacks with Mirror Coat if the player treats it
  as a normal Water exchange.

Endgame route:

- Snorlax can become the RestTalk Curse anchor if its answer is paralyzed,
  chipped, slept, or spent earlier.

Triage:

- Beat or force Pikachu without using the only Snorlax or Espeon answer. If
  Espeon starts boosting, it may become the immediate route even before Snorlax
  appears.

Answer-changing information:

- Pikachu's revealed coverage.
- Reflect turns and Calm Mind boosts.
- The Snorlax answer's HP, status, PP, and phazing/Haze access.
- Sunny Day turns and whether Blastoise can Mirror Coat the intended attack.

## Known Boss Roster Transfer Drill

Later-generation Team Preview teaches one useful boss-fight habit: known
rosters are not trivia. In Gym Leader Lab, this applies only to source-known
boss rosters and local opening policy. It does not mean the boss sees the
player's unrevealed team.

Use this before choosing a Gym Leader Lab lead:

```text
Known boss roster:
Boss route machinery:
Our first winning route:
Boss roadblocks to that route:
Player pieces that must be conserved:
Fixed-first or adaptive opener source:
Likely opening family:
Lead that covers the opening family:
Set, item, or move uncertainty that matters:
First scouting target:
Abandon condition:
```

Do not fill this with species slogans. The useful answer is the one that says
which route the boss is trying to assemble and which player piece must not be
spent before that route appears.

## Misty Adaptive Shape

Known opening family:

- Misty can open from Politoed, Starmie, or Quagsire under the current
  adaptive-lead source rule.

Bad known-roster logic:

```text
Lead only for Politoed and assume the first turn is a rain/sleep exchange.
```

Why this can fail:

```text
If Starmie opens, the fight can become a Recover and speed-pressure exchange.
If Quagsire opens, the fight can become a Curse/Rest route instead. The lead
that only answers Politoed may spend the piece needed for one of those routes.
```

Better known-roster question:

```text
Which lead keeps the rain/sleep, Recover, and Curse/Rest openings all playable
until the actual opener is revealed?
```

First scouting target:

- Which of the three adaptive openers appeared, and which route did that opener
  make urgent?

## Transfer Rule

The boss lead is not always the boss's most important Pokemon. The lead is the
first test of whether the user's team can preserve the right answers for the
route that will matter later.
