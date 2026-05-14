# Worked Example: Check Durability Ledger

Status: constructed boss-facing study example. This is not exact turn advice
until the user's team, HP, moves, items, bench, and damage evidence are known.

Purpose: practice downgrading or upgrading "answers" based on the current
state, not on full-HP species memory.

Source basis:

- `../cookbook.md` recipe: Check Durability Ledger.
- `../boss_route_maps/blue_turn1_route_sheet.md`
- `../boss_route_maps/lance_turn1_route_sheet.md`
- `../boss_route_maps/clair_turn1_route_sheet.md`
- Smogon "What are Checks and Counters?"
- Smogon "Getting Started with Competitive Battling"
- Smogon "Pivots in SM OU"

## Case 1: Blue Gyarados Answer After Pidgeot

Threat:

```text
Blue Gyarados:
  Dragon Dance / Outrage / Surf / Hyper Beam
  Leftovers
```

Bad label:

```text
Our lead beats Pidgeot and also answers Gyarados.
```

Ledger correction:

```text
If the lead has to take Choice Band Double-Edge, Wing Attack, Steel Wing, or
Quick Attack before Gyarados appears, it may stop being a counter. It might
become only a free-entry check, or it may fall below +1 Hyper Beam / Outrage /
Surf range entirely.
```

Policy implication:

- If the Gyarados answer is still a counter after Pidgeot damage, leading it is
  acceptable.
- If it becomes a free-entry check, do not hard-switch it into Pidgeot just to
  win the lead exchange. Preserve it and find a controlled entry after Pidgeot
  locks, takes recoil, or is removed.
- If it becomes no longer an answer after chip, the lead plan is wrong unless
  the Pidgeot exchange creates an immediate forced route before Gyarados can
  boost.

## Case 2: Lance Multi-Wave Anti-Setup Answers

Threats:

```text
Steelix:
  Dragon Dance / Earthquake / Iron Tail / Outrage

Gyarados:
  Dragon Dance / Outrage / Hydro Pump / Hyper Beam

Dragonite:
  Dragon Dance / Outrage / Earthquake / Hyper Beam
```

Bad label:

```text
We have a Dragon Dance answer.
```

Ledger correction:

```text
Lance has several setup waves. A piece that answers Steelix may not answer
Gyarados or Dragonite after taking chip, status, or using PP. The ledger needs
one row per threat, not one generic "Dragon answer" box.
```

Policy implication:

- Spending Haze, phazing, status, or an Ice/special attacker on Steelix is
  correct only if the remaining roster still has a live answer to Gyarados,
  Kingdra, and Dragonite.
- A one-time emergency answer is allowed if it stops the current boosted route
  and leaves a second route for the later Dragon Dance user.
- If the same Pokemon is the only answer to both midgame Gyarados and final
  Dragonite, its HP is not disposable even when Steelix is active.

## Case 3: Clair Status Into MiracleBerry Dragonair

Threat:

```text
Dragonair @ MiracleBerry:
  Dragon Dance / Surf / Fire Blast / Outrage
```

Bad label:

```text
Our status user checks Dragon Dance.
```

Ledger correction:

```text
If MiracleBerry is intact, the first status attempt may only remove the item.
That can still be useful, but it is not the same as stopping the boosted route.
The answer label depends on whether the status user survives the next turn and
whether another answer handles the boosted state.
```

Policy implication:

- Status is a counter only if it can be applied and the user still survives the
  berry/boost branch.
- If status merely consumes MiracleBerry, the real answer may be the follow-up:
  Haze, phazing, immediate damage, sacrifice into revenge, or exploiting
  Outrage lock.
- If the status user cannot survive the second turn, it is a lure or item
  breaker, not a Dragon Dance answer.

## Case 4: Free-Entry Check Versus Manual Switch

Threat:

```text
Any boss converter that KOs or cripples the active if given a free turn.
```

Bad label:

```text
Our backup can beat it, so switch there now.
```

Ledger correction:

```text
Smogon's check/counter distinction treats a free switch and a manual switch as
different states. A free-entry check may win after a teammate faints, after a
slow pivot, after a forced recharge, or after the boss is locked into a weak
move. The same Pokemon may fail as a manual switch because the boss gets one
unanswered action on the entry turn.
```

Policy implication:

- If the answer only works from free entry, do not hard-switch it into the boss
  route unless the incoming hit is harmless or the switch also creates a route.
- A controlled sack, slow pivot, phaze, Encore lock, recovery turn, or forced
  recharge can upgrade the same answer from unusable to correct.
- A pivot is valuable when it both survives its entry job and creates a safer
  next entry for the real converter or answer. If it only absorbs damage and
  then gives the boss another setup turn, it is not progress.

Answer-changing information:

- Whether the proposed answer survives the entry hit plus follow-up.
- Whether hazards, poison, weather, or prior chip remove the second hit.
- Whether the boss is locked, recharging, asleep, encored, low on PP, or forced
  to recover.
- Whether a slow pivot, sack, or phaze can create the free-entry state.

## Extracted Rule

For boss planning, answer labels should be verbs plus entry conditions:

```text
can hard-switch twice
can hard-switch once
can revenge after sack
can enter only from a free switch
can force item/status but not stop setup alone
can answer only before hazards/weather/status
```

Those labels choose moves better than species slogans like "this walls it."
