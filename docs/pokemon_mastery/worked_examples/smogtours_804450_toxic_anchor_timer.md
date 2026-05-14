# Worked Example: Toxic As Anchor Timer

Source: https://replay.pokemonshowdown.com/smogtours-gen2ou-804450

Format: vanilla GSC OU. Use this for general decision training, not romhack
mechanics proof.

## Position

Turn 33:

```text
OmBrArch active: Alakazam at 65%
Alice active: Snorlax at 57%
Alice side: Spikes active
OmBrArch side: Spikes active
Alice Snorlax known: Lovely Kiss / Curse / Double-Edge / Earthquake
OmBrArch remaining important route: keep Spikes pressure and win through
SleepTalk Snorlax after opposing Snorlax is put on a timer
```

Alakazam used Toxic. Alice's Snorlax used Double-Edge and KOed Alakazam.

## Why This Is Not Just A Bad Trade

The move spent Alakazam, but it changed the most important opposing piece.
Alice's Snorlax had been a stabilizer: it could sleep, threaten damage, Curse,
and absorb pressure. After Toxic, every switch, attack, and recoil turn pushed
it toward an endgame where it could no longer outlast OmBrArch's RestTalk
Snorlax.

The proof appears later:

```text
Turn 49: poisoned Snorlax re-enters through Spikes at 41%, heals to 47%.
Turn 50: Lovely Kiss lands, but poison pulls Snorlax to 34%, then 40%.
Turn 51: Double-Edge plus poison drops it to 24%, then 30%; OmBrArch Sleep Talk
         calls Rest and resets to full.
Turn 54: Snorlax dies to recoil plus poison.
```

## Rule

Trading a frail attacker to land status can be correct when all of these are
true:

1. The target is an opposing anchor or route blocker.
2. The status changes the future endgame, not just the current HP total.
3. The status cannot be cheaply cleared before it matters.
4. The sacrificed piece has less remaining role value than the timer it creates.
5. The opponent's immediate KO does not open a stronger route than the status
   closes.

## Failure Signs

- The target can Rest, Heal Bell, switch away from Toxic pressure, or ignore the
  timer before it matters.
- The sacrificed attacker was still the only answer to a later route.
- The status target is replaceable and not a real blocker.
- The move is justified as "getting chip" rather than naming the future route.

## Romhack Transfer

Do not transfer the exact Toxic behavior without checking local source. The
transferable principle is route trade: a status move can be worth a sacrifice
only when it turns the correct opposing piece into an expiring resource.
