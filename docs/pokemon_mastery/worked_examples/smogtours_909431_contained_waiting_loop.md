# Worked Example: Contained Waiting Loop

Source review: `../reviews/2026-05-13_smogtours-gen2ou-909431.md`

Source replay: https://replay.pokemonshowdown.com/smogtours-gen2ou-909431

Format: vanilla GSC OU. This is a strategic example, not romhack mechanics
proof.

## Public State Pattern

```text
Our side:
Raikou is alive and can Rest/Sleep Talk through Zapdos and low Jolteon.
Forretress is alive, can Rest, and walls the remaining Snorlax well enough.
Our side has removed Spikes.

Opponent side:
Spikes are up.
Zapdos is poisoned.
Jolteon is very low and takes Spikes on entry.
Snorlax lacks a revealed setup route that breaks Forretress quickly.

Current active pattern:
Forretress often faces Snorlax.
Raikou pivots into Zapdos or Jolteon.
```

## Candidate Move Classes

Best / acceptable:

- Stay in with Forretress, Rest when needed, and use low-value moves such as
  Defense Curl or harmless Spikes attempts only when the opponent cannot convert
  the free-looking turn into a new route.
- Pivot Raikou into Zapdos/Jolteon when needed, preserving enough HP for Rest.

Wrong:

- Switch aggressively just because Forretress's current move does not look
  productive, if the switch reopens Jolteon or Zapdos pressure.
- Sacrifice Forretress for chip while Snorlax remains the only realistic
  opponent route.

Catastrophic in a different state:

- Clicking a no-effect hazard move while the opponent can Dragon Dance, Curse
  past the wall, spin, recover for free, or KO an irreplaceable answer.

## Why The Waiting Loop Works

The progress is not coming from Forretress's move text. The progress is coming
from the already established state:

```text
Zapdos poison clock
+ Jolteon Spikes clock
+ Snorlax failing to break Forretress
+ Raikou preserving the Electric answer role
= opponent routes slowly expire
```

The "So what?" of a no-effect or low-effect move is:

```text
It preserves the contained loop for one more turn while the external clock
continues.
```

That answer is valid only if the opponent's best response still cannot change
the route.

## Boundary Flip

Same visible idea, different answer:

```text
If the opposing Snorlax has Curse and Forretress cannot stop it, failed Spikes
is no longer a waiting move. It gives Snorlax a setup turn and becomes a severe
state error.
```

Another flip:

```text
If our side still has Spikes and every Raikou/Forretress pivot takes hazard
damage, staying passive may lose the loop. Spinning, attacking, sacrificing, or
changing the route can become necessary.
```

## Boss-Battle Transfer

In Gym Leader Lab, this matters most when a boss has finite weather, Safeguard,
poison, recoil, Perish Song, Rest sleep, or hazard damage already working
against it.

Waiting is allowed only if all three are true:

1. The boss cannot use the turn to create a worse route.
2. The user's irreplaceable answer stays healthy enough.
3. The external clock continues to favor the user.

If any one is false, "waiting" becomes passivity.
