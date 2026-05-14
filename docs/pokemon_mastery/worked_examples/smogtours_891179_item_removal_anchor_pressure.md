# Worked Example: Item Removal As Anchor Pressure

Source:

- Replay log: https://replay.pokemonshowdown.com/smogtours-gen2ou-891179.log
- Review: `../reviews/2026-05-13_smogtours-gen2ou-891179.md`
- GSC Jynx analysis:
  https://www.smogon.com/forums/threads/jynx-gsc-ou-qc-2-2-gp-2-2.3667481/
- GSC Thief discussion:
  https://www.smogon.com/forums/threads/thief.3543261/
- Romhack Thief source:
  `data/moves/moves.asm`,
  `engine/battle/move_effects/thief.asm`
- Romhack item source:
  `docs/agent_navigation/gen2_vs_modern_mechanics.md`,
  `docs/agent_navigation/hack_mechanics_reference.md`

## Pattern

Public state:

```text
Item target:
Item:
Route that item supports:
Item-removal user:
Follow-up after removal:
Worst plausible branch:
Boss or opponent route if removal fails:
```

Decision:

```text
Item removal is good only if:
  the item supports a live route;
  losing the item changes future HP, status, setup, lock, or endgame math;
  the item-removal user is allowed to spend the turn;
  and the next move converts the item loss into route pressure.
```

## Replay Shape

Position:

```text
Jynx faces Snorlax.
Snorlax is the opposing anchor and has Leftovers.
Spikes are active on Snorlax's side.
Jynx has Thief and Lovely Kiss.
```

Bad advice:

```text
Use Thief because stealing an item is always good.
```

Better posture:

```text
Use Thief only because this item is part of Snorlax's anchor route. Removing
Leftovers makes future Spikes entries, Ice Beam damage, sleep turns, and forced
Rest branches harder for Snorlax to erase.
```

Follow-up:

```text
Thief -> Lovely Kiss -> damage / re-score on wake or Sleep Talk branch.
```

Why the follow-up matters:

- If Jynx steals Leftovers and then leaves without pressure, the item removal is
  only a delayed discount.
- If Jynx steals Leftovers and immediately forces sleep or damage, the anchor's
  recovery loop is under pressure right now.
- If Sleep Talk calls Rest or attack, re-score. The item is gone, but the anchor
  still has agency.

## Boss Transfer

Use this pattern when a boss item is part of the route:

```text
Leftovers:
  recovery anchor, repeated pivot, Rest loop, or hazard-tax survival.

Mint Berry:
  one-time sleep/status route protection.

Focus Band:
  one-hit removal branch that can flip a forced KO plan.

Choice Band:
  damage boost plus lock route.

Type-boost item:
  damage threshold or revenge range.
```

Local transfer limits:

```text
Thief exists locally and steals a non-mail held item if the user has no item
and the target has one.

Knock Off and Trick are not local move-table options.

Standard AI scoring strongly discourages Thief unless it is the only move
available, so boss-side Thief needs trace or current-state AI evidence before
being treated as likely.
```

Do not import the move choice blindly. In Gym Leader Lab, the question is:

```text
Can we remove, exploit, or route around this item, and what turn converts that?
```

## Failure Signs

- The answer says "remove the item" but cannot name the route that changes.
- The removed item belonged to a spent target while the real anchor's item
  remains active.
- The item-removal user is still the only answer to a later boss route.
- The plan assumes the boss will keep switching the same way after the item is
  gone.
- The plan assumes a modern item-control move exists without checking local
  moves.

## Extracted Rule

```text
Treat item removal as a route discount. It becomes progress only when the next
state uses that discount before the opponent can stabilize elsewhere.
```
