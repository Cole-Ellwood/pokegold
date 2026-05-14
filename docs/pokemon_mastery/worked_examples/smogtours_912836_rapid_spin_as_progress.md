# Worked Example: Rapid Spin As Progress

Source review: `../reviews/2026-05-13_smogtours-gen2ou-912836.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-912836

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Position Pattern

```text
Our side:
We have set Spikes, but the setter is low or gone.
Our current active is low enough that Rapid Spin may KO or force it.

Opponent side:
The spinner is alive and can enter.
The spinner has enough HP to spin and remain useful.

Critical timing:
If the spinner uses Rapid Spin now, the move may remove the layer and also
create immediate board progress.
```

## Candidate Move Classes

Best when available:

- Deny the spinner's entry before it gets the clean spin turn.
- Force the spinner below the range where it can spin and remain useful.
- Convert the hazard immediately with phazing, a KO threshold, or forced
  recovery before the spinner can remove it.

Acceptable:

- Re-set Spikes if the layer creates immediate value before the next spin and
  the setter has no better remaining route job.
- Trade damage into the spinner if that damage makes future removal impossible
  or too expensive.

Wrong:

- Treating Rapid Spin as a passive support turn when it also KOs, forces, or
  preserves the opponent's switch loop.
- Re-setting hazards with no answer to the still-alive spinner and no immediate
  conversion plan.

## Rule

Before calling a spin turn passive, fill this out:

```text
Current layer value:
Spinner entry cost:
Spinner HP after entry:
Can Rapid Spin also KO or force the active:
Does the spinner survive after spinning:
What route does the removed layer stop:
What route does the spin turn improve:
```

If Rapid Spin clears hazards and creates tempo, it is not just removal. It is a
progress move.

## Boundary Flip

Same spinner, different answer:

```text
If the active threatens a KO or crippling status before spin, Rapid Spin may be
too expensive.
If the active is low and cannot punish, Rapid Spin may be both safe removal and
progress.
```

Same hazard layer, different answer:

```text
If the layer creates a KO or forced recovery before the next spin, re-setting it
can be correct.
If the layer only creates one small switch tax before being removed, the
hazard turn may need a stronger justification.
```

## Boss-Battle Transfer

Use this when a boss has Rapid Spin and the player's hazard route depends on
keeping layers up.

Questions:

1. Does the boss spinner threaten the current active while spinning?
2. Does the boss spinner survive the punish?
3. Does the player have a way to block, KO, status, or force the spinner before
   it removes all layers?
4. If the boss clears all layers, what player route remains?

This especially matters in Gym Leader Lab because Rapid Spin clears all local
Spikes layers. A three-layer stack that gets spun without punish may be a lost
route, not just lost chip.
