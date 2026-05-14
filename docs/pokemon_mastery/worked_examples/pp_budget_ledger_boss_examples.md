# Worked Example: PP Budget Ledger In Boss Fights

Purpose: practice recognizing when PP, not HP, is the route resource.

Source basis:

- Smogon's GSC Spikes guide says Spikes can decide stall endgames by making
  endless switching costly and turning the game into a PP war, but only if the
  user's own side can avoid the same switch tax.
- `../reviews/2026-05-13_smogtours-gen2ou-933547.md` shows a 239-turn game
  where long Spikes / Rapid Spin / Rest loops changed the route map through PP,
  HP, status, and preserved converters.
- `../reviews/2026-05-13_smogtours-gen2ou-909431.md` shows a contained loop
  where passive-looking turns were correct because poison, Spikes, and answer
  preservation were already doing the work.
- Local PP evidence comes from `data/moves/moves.asm`.

## Recipe Used

Fill this before calling a PP line:

```text
scarce move:
owner:
remaining PP:
route it protects:
route it attacks:
what forces it:
what lets us conserve it:
what happens at zero PP:
```

If "what happens at zero PP" does not improve the route, this is probably not a
PP plan.

## Misty: Recover Is A Reset Budget

Local evidence:

- Starmie has Recover in `data/trainers/parties.asm`.
- Recover has 20 PP in `data/moves/moves.asm`.

Bad default:

- "Keep attacking because Starmie is taking damage."

Why that fails:

- If the damage never crosses a threshold and Starmie can Recover without
  giving up a worse route, the user may be spending attacking PP into a 20-PP
  reset budget. The visible HP bar moves, but the route does not.

Better policy:

- Force Recover only when the recovery turn gives safe entry, setup, status,
  hazards, item pressure, or a stronger attack.
- If the player's attack PP is scarcer than Recover PP, repeating chip may lose
  the PP race.
- If Starmie must choose between Recover and attacking into a setup or pivot,
  the Recover PP is being pressured correctly.

Answer-changing information:

- Recover PP already low makes chip stronger.
- Rain active makes the cost of spending a turn to force Recover higher.
- A player breaker that enters safely on Recover changes the whole route.

## Sabrina And Red: Morning Sun Is Finite

Local evidence:

- Sabrina Espeon and Red Espeon use Morning Sun in local route sheets or
  `data/trainers/parties.asm`.
- Morning Sun has 5 PP in `data/moves/moves.asm`.

Bad default:

- "Recovery means the damage plan is impossible."

Why that fails:

- A five-PP recovery move is not the same as an endless wall. If the player can
  force Morning Sun without losing the Espeon answer, the recovery itself can
  become the resource being exhausted.

Better policy:

- Count Morning Sun uses. If each use costs Espeon screen turns, weather turns,
  Baton Pass timing, or setup access, forcing it can be progress.
- Do not force Morning Sun by spending the only move or PP pool that later
  beats Alakazam, Hypno, Snorlax, or another route.
- If sun or weather changes local recovery amount, use the romhack mechanics
  reference before trusting the line.

Answer-changing information:

- Weather and time-of-day effects on recovery.
- Remaining screen turns.
- Whether Espeon can Baton Pass instead of healing.

## Clair, Lance, And Red: Phazing / Haze PP Is Emergency Material

Local evidence:

- Roar and Whirlwind have 20 PP locally; Haze has 30 PP.
- Boss route maps include setup and phazing/Haze questions across Dragon Dance,
  Curse, Calm Mind, and similar routes.

Bad default:

- "Phaze now because they might set up later."

Why that fails:

- If the opponent has not created a live setup route, spending phazing PP can be
  worse than attacking, pivoting, or preserving the phazer. The last phaze PP is
  often the actual answer to the final setup attempt.

Better policy:

- Spend phazing or Haze PP when a boost route is live or when the phaze creates
  hazard damage, reveal value, or forced recovery.
- Conserve it when the current boost is contained by another answer or when
  attacking forces the same denial without spending emergency PP.
- Track whether the phazer can still enter after hazards, status, and damage.

Answer-changing information:

- Remaining phaze/Haze PP.
- Whether hazards make each phaze progress.
- Whether another answer covers the same setup route.

## Hazard War: Rapid Spin PP Is Usually Not The First Bottleneck

Local evidence:

- Rapid Spin has 40 PP locally.
- Brock, Koga, Will, and other route maps include Spikes and spin questions.

Bad default:

- "Win by exhausting Rapid Spin."

Why that often fails:

- Forty PP is a large budget. In many boss fights, HP, safe entry, spinblocker
  status, hazard layer count, or the setter's survival will fail before Rapid
  Spin PP does.

Better policy:

- Treat spin PP as the bottleneck only when the fight is already a true
  endgame loop and the spinner can no longer convert with damage, recovery, or
  switch pressure.
- More often, pressure the spinner's entry, HP, status, or opportunity cost
  instead of trying to drain 40 PP.

Answer-changing information:

- Three-layer Spikes makes each reset more valuable, but the exact layer math is
  romhack-specific.
- A healthy spinblocker can make spin access, not spin PP, the real bottleneck.
- A low-HP spinner may be denied by thresholds long before PP matters.

## Extracted Lesson

PP is a route resource, not a stall slogan. Count the move that keeps the route
alive, then decide whether this turn forces that move, conserves our answer, or
spends scarce PP into a reset loop the boss is already happy to play.
