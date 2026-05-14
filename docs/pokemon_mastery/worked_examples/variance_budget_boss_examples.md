# Worked Example: Variance Budget In Boss Fights

Status: constructed boss-facing study example. This is not final turn advice
without the user's team, HP, moves, items, speed relations, and damage evidence.

Purpose: practice deciding when to reduce luck exposure and when to accept it
because every non-variance line has already failed.

Source basis:

- Smogon's "Playing with Loaded Dice" article frames luck as something to
  manage by posture: avoid unnecessary miss/crit/status branches when solid
  play is winning, but choose the best real chance when the position is lost
  without variance.
- Smogon's situational analysis and prediction articles reinforce that a move
  is judged by the current board, risk/reward, and information, not by whether
  it feels brave or safe.
- Local route maps:
  `../boss_route_maps/red_turn1_route_sheet.md`,
  `../boss_route_maps/bruno_turn1_route_sheet.md`, and
  `../boss_route_maps/clair_turn1_route_sheet.md`.

## Pattern

```text
Current posture:
  ahead / stable / losing slowly / forced risk

Our route:
  converter:
  irreplaceable piece:
  resource that must survive:

Variance branch:
  miss / crit / full paralysis / sleep turn / Focus Band / Quick Claw /
  damage roll / secondary effect / prediction coinflip

Can variance be removed without losing the route:
  yes / no

If variance happens:
  route impact:
  recovery plan:
```

## Case 1: Red Pikachu Razor Leaf, Preserve The Later Answer

Boss shape:

```text
Red lead:
  Pikachu @ Light Ball
  ExtremeSpeed / Thunderbolt / Razor Leaf / Surf

Local route-map fact:
  Razor Leaf is a high-crit special branch and Light Ball boosts Special
  Attack only.

Our temptation:
  keep a Ground/Rock-style lead in because average damage looks survivable.
```

Bad advice:

```text
"Stay in because the type matchup is good unless Pikachu crits."
```

Variance-budget reading:

```text
If this lead is also the Snorlax, Espeon, sun, or Blastoise answer, average
survival is not enough. A high-crit Razor Leaf branch that removes the later
answer changes the whole Red route map.
```

Better policy:

- If ahead or stable, choose the line that keeps the later answer outside the
  crit-loss branch: pivot, force Pikachu with a redundant piece, or attack only
  when the KO/threshold is decisive.
- If no piece can avoid the branch and the fight is already forced, label the
  line as accepted variance and name the backup route after a crit.

Answer-changing information:

- Exact damage range for Razor Leaf normal hit and crit.
- Whether the lead is the only later answer.
- Whether the lead's attack KOs Pikachu before a second chance branch.
- Whether a pivot remains stable against Surf, Thunderbolt, and ExtremeSpeed.

## Case 2: Bruno Hitmonlee Focus Band, Do Not Call A KO Guaranteed

Boss shape:

```text
Bruno route:
  Hitmonlee @ Focus Band
  Meditate / Hi Jump Kick / Rock Slide / Earthquake

Local route-map fact:
  Focus Band creates a small 1-HP survival branch.
```

Bad advice:

```text
"We OHKO Hitmonlee, so this turn is solved."
```

Variance-budget reading:

```text
The KO line is only clean if the Focus Band survival branch has a follow-up.
If surviving at 1 HP lets Hitmonlee KO an irreplaceable piece, boost, or put the
cleaner into Mach Punch range for a later teammate, the route was never
guaranteed.
```

Better policy:

- If the fight is stable, prefer a line with a Focus Band follow-up: priority,
  residual damage, hazard chip before the attack, a controlled sack after
  survival, or a pivot that survives the 1-HP retaliation.
- If every line loses unless the KO happens now, take the KO attempt but mark
  it as forced risk rather than a guaranteed conversion.

Answer-changing information:

- Whether Focus Band is still held and active.
- Whether entry hazards, poison, burn, Leech Seed, recoil, or priority covers
  the 1-HP branch.
- Whether the attacker is irreplaceable after this turn.

## Case 3: Bruno Heracross Crit Pressure, Shorten Before The Wall Fails

Boss shape:

```text
Bruno route:
  Heracross @ Scope Lens
  Megahorn / Cross Chop / Rock Slide / Focus Energy

Local route-map fact:
  Cross Chop is high-crit, Scope Lens adds crit pressure, and Focus Energy can
  make the defensive answer map unstable.
```

Bad advice:

```text
"Switch to the wall again; it survives average damage."
```

Variance-budget reading:

```text
Once Focus Energy plus Scope Lens is online, repeated wall entries may just buy
Heracross more crit chances. The question is no longer whether the wall handles
the average hit. The question is whether the route survives the number of hits
we are about to permit.
```

Better policy:

- If ahead and Focus Energy is not active, deny the free setup turn before the
  crit branch compounds.
- If Focus Energy is active and the wall route now depends on no crit across
  repeated turns, shorten the game with Haze/phazing, immediate damage,
  sacrifice into revenge range, sleep/status if legal, or another route that
  reduces the number of Heracross attacks.
- If the only possible win requires a miss, crit, or secondary effect back,
  choose the highest real chance and record it as a comeback line.

Answer-changing information:

- Current crit stage and whether Focus Energy has landed.
- Wall HP after hazards and Rock Slide.
- Whether Haze, phazing, Encore, priority, or a controlled sack is available.

## Case 4: Clair Gligar Quick Claw, Separate Speed Plan From Item Variance

Boss shape:

```text
Clair route:
  Gligar @ Quick Claw
  Spikes / Toxic / Earthquake / Rock Slide

Local route-map fact:
  Quick Claw can change a speed assumption that mattered.
```

Bad advice:

```text
"We outspeed, so we can always stop Gligar before it acts."
```

Variance-budget reading:

```text
If the whole plan loses to one Quick Claw activation, it is not a stable speed
plan. If Quick Claw only creates chip but does not remove the route, do not
overreact and abandon a winning line.
```

Better policy:

- Stable route: pick the move that still works if Gligar steals one turn, or
  preserves the piece that can clean up after Toxic, Spikes, or chip.
- Forced route: if stopping Spikes or Toxic now is the only way to prevent
  collapse, attack anyway but record the Quick Claw branch as variance, not as
  a planning error if it triggers.

Answer-changing information:

- Which Gligar move is catastrophic if Quick Claw triggers.
- Whether the current active remains useful after Toxic or chip.
- Whether the team can play through one Spikes layer or must deny it now.

## Transfer Lesson

Do not ask "can this bad-luck branch happen?" in isolation. Ask:

```text
Can we remove the branch while keeping our route?
If not, is the branch the price of our best route or a needless exposure?
If the branch happens, what route remains?
```

Variance control is not cowardice, and variance acceptance is not tilt. The
correct posture depends on whether solid play is still winning.
