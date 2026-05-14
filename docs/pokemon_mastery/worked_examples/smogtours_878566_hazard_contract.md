# Worked Example: Hazard Contract From smogtours-gen4ou-878566

Source review: `../reviews/2026-05-13_smogtours-gen4ou-878566.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen4ou-878566

Format: DPP OU on Pokemon Showdown. Use this for transferable planning, not
GSC or Gym Leader Lab mechanics proof.

## Public State Pattern

```text
One side has hazard pressure started.
The natural spinblocker is already very low.
The opposing spinner is healthy enough to enter.
The hazard layer has not yet created an immediate KO, forced recovery turn, or
clean converter entry.
```

The tempting line is to keep setting or preserving hazards because the team was
built around them. The actual question is whether the hazard route still has
all three jobs:

```text
set:
  who creates the layer and what turn it costs

retain:
  who blocks, punishes, or outpaces Rapid Spin / removal

convert:
  what KO, recovery, phaze, switch, or cleaner route improves before removal
```

## Candidate Move Classes

Best / acceptable:

- Convert the existing hazard immediately if it changes the next route.
- Pressure the spinner or its entry if retaining the layer matters.
- Abandon the hazard plan when the retention piece has collapsed and a better
  direct route exists.
- Re-set a temporary layer only if the next forced sequence cashes it out
  before the spinner removes it.

Wrong:

- Re-set hazards while the spinner removes them at lower cost and no threshold
  changes.
- Preserve a weakened spinblocker as if it still performs its original durable
  job.
- Keep playing for a long hazard war after the board has become a direct
  cleaner or anchor endgame.

## Why The Contract Matters

The reviewed game shows hazard pressure failing at the retention layer. Once
the spinblocker is too damaged, Rapid Spin can clear the work at the exact
moment the hazard player needs conversion. That does not make the original
hazard plan bad. It means the plan's job changed:

```text
If retain is gone:
  convert now, pressure removal, or change routes.
```

Continuing to click hazard moves without that change is layer autopilot.

## Boss-Battle Transfer

Gym Leader Lab hazard bosses often compress all three jobs into one fight:

- Koga: Ariados sets clock pressure, Tentacruel removes boosts / hazards, and
  Crobat or Nidoking converts chip.
- Will: Forretress and Starmie can split setter / spinner jobs while Slowbro
  and Alakazam ask whether the player is losing tempo.
- Pryce: Cloyster can set pressure while Dewgong's Rapid Spin asks whether the
  player's layer is temporary or durable.
- Brock and Bruno: Rock / Fighting pressure plus Spikes and phazing can make
  the spin turn more important than the first layer.

The move advice should never stop at "set Spikes." It should say:

```text
This layer is worth the turn because [retention plan] and [conversion route].
```

or:

```text
This layer is not worth the turn because [removal branch] resets it before
[conversion route] happens.
```

## Boundary Flip

Original: the spinner enters freely and clears the layer before conversion.
Correct policy: pressure spinner or change routes.

Mutation: the layer puts the spinner or next switch-in into guaranteed KO range
before it can remove hazards.
Correct policy: set the temporary layer and cash it out immediately.

Mutation: the spinblocker is healthy and punishes Rapid Spin hard enough that
the spinner cannot safely remove hazards.
Correct policy: hazard route becomes durable again.
