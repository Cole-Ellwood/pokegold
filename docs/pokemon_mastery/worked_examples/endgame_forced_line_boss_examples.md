# Worked Example: Endgame Forced-Line Audit

Status: constructed boss-facing study example. This is not exact live turn
advice until the user's team, HP, moves, items, bench, and damage evidence are
known.

Purpose: practice turning a late-game position into a route tree instead of a
generic move choice.

Source basis:

- `../cookbook.md` recipe: Endgame Forced-Line Audit.
- `../reviews/2026-05-13_smogtours-gen2ou-804450.md`
- `../reviews/2026-05-13_smogtours-gen2ou-909431.md`
- `../worked_examples/smogtours_909431_contained_waiting_loop.md`
- `../worked_examples/resttalk_branch_pricing_boss_examples.md`
- Smogon Playing with Spikes in GSC:
  https://www.smogon.com/gs/articles/gsc_spikes

## Pattern 1: Clock Already Wins

Public state pattern:

```text
Boss anchor:
  poisoned / seeded / trapped / weather-limited / hazard-limited

Our remaining material:
  one durable blocker still above required HP
  one cleaner or revenge piece

Boss remaining route:
  needs setup, recovery, or a crit before the clock expires
```

Bad advice:

```text
Attack because doing damage is progress.
```

Better audit:

```text
If the boss cannot set up, heal, phaze, spin, or KO the blocker before the
clock resolves, preserve the loop. A low-value move, recovery, pivot, or sack
can be correct if it keeps the external clock running.
```

Boundary flip:

```text
If the boss can use the waiting turn to Dragon Dance, Curse, Rest, Haze away
the setup, spin hazards, or KO the blocker, waiting is no longer a line. Break
the route immediately.
```

## Pattern 2: Rest Reset Decides The Race

Public state pattern:

```text
Boss anchor:
  low HP
  Rest available
  Sleep Talk may or may not be available

Our converter:
  can force Rest but may not win after a full reset
```

Bad advice:

```text
Force Rest because the boss is low.
```

Better audit:

```text
Forcing Rest is only a win if the next two turns convert: setup, phaze, Haze,
Explosion, hazard damage, safe entry, PP pressure, or a forced KO before the
anchor resumes its role. If Rest resets the damage race and Sleep Talk can
attack or heal, forcing Rest may just delay losing.
```

Boundary flip:

```text
If the anchor is Rest-only and cannot switch, phaze, or threaten the converter
during sleep turns, forcing Rest becomes much stronger.
```

## Pattern 3: Priority Or Recoil Ends The Game

Public state pattern:

```text
Boss cleaner:
  has priority, recoil attack, lock-in move, weather-boosted attack, or
  revenge range

Our cleaner:
  faster or stronger in normal move order, but low enough for priority or
  recoil math to matter
```

Bad advice:

```text
Use the strongest attack because it KOs.
```

Better audit:

```text
First ask who moves last in the real endgame: priority, Quick Claw, lock-in,
recharge, recoil, poison, weather, and hazard entry can all override the simple
"faster Pokemon wins" story. A sack to force a locked or recoil turn may be the
actual route.
```

Boundary flip:

```text
If the opponent priority does not KO and our attack creates a guaranteed final
KO, immediate damage is correct. Do not over-preserve after the forced line is
won.
```

## Pattern 4: Switch Tax Creates The PP Win

Public state pattern:

```text
Boss side:
  one or more grounded pieces still need to switch to preserve PP or avoid bad
  matchups

Our side:
  can remove or avoid the same switch tax
  has enough recovery / phazing / attack PP to force the boss to move first

Shared state:
  neither side can immediately break through by raw damage
```

Bad advice:

```text
Keep attacking because switching is passive.
```

Better audit:

```text
If every boss switch spends hazard HP while our switching is cheap, the forced
line may be to conserve scarce PP, pivot through safe entries, and make the
boss spend recovery or phazing PP first. The route is not "stall forever." The
route is "their switch loop runs out before ours does."
```

Boundary flip:

```text
If hazards are on our side too, the PP plan may fail because we pay the same or
larger switch tax. If the boss has Rapid Spin, phazing, recovery, or a setup
move that turns the waiting turn into progress, stop waiting and convert.
```

Romhack note:

```text
Gym Leader Lab has three-layer Spikes, so exact switch-tax math is fork-specific
and must use local mechanics. The transferable concept is not the vanilla
damage value; it is checking which side can afford repeated entries and which
side is forced to spend scarce PP first.
```

## Boss Transfer

Use this audit for:

- Red: Snorlax RestTalk, Blastoise Mirror Coat, Pikachu ExtremeSpeed, and
  sun-starter weather turns.
- Misty: Starmie Recover, Quagsire Rest, Lapras rain, and Lanturn Thunder Wave.
- Koga: poison/trap clocks, Muk RestTalk, Haze, and Rapid Spin.
- Lance: Outrage lock, Hyper Beam recharge, Dragon Dance, and priority or
  sacrifice sequencing.
- Blue: Choice lock, Gyarados setup, Arcanine priority, and Alakazam recovery.

## Extracted Rule

Endgame advice should sound less like "this move is good" and more like:

```text
Move A wins because after [boss response], [our follow-up] is forced, and the
remaining clock/PP/priority state leaves no better route for the boss.
```

If the advice cannot name that route, the endgame has not been audited yet.
