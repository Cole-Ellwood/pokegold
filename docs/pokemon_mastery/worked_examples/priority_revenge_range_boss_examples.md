# Worked Example: Priority And Revenge Range In Boss Fights

Status: constructed boss-facing study example. This is not exact turn advice
without the user's team, HP, moves, Speed, item state, and damage evidence.

Purpose: practice the difference between ordinary Speed control and real
endgame move order. A faster Pokemon is not a cleaner if priority, Quick Claw,
Focus Band, recharge, lock-in, paralysis, or hazard entry changes the final
exchange.

Source basis:

- Smogon's BW priority guide treats priority as a way to check fast sweepers
  and as a possible sweep tool, but also notes the tradeoff: many priority
  moves need setup, item lock, chip, or team support to be strong enough:
  <https://www.smogon.com/bw/articles/ou_priority_guide>.
- Smogon's GSC priority table is the mechanics baseline:
  <https://www.smogon.com/gs/articles/move_priority>.
- Local romhack mechanics:
  `docs/agent_navigation/hack_mechanics_reference.md` and
  `docs/agent_navigation/gen2_vs_modern_mechanics.md` say Quick Attack, Mach
  Punch, and ExtremeSpeed share the same `EFFECT_PRIORITY_HIT` tier.

## Pattern

```text
Our cleaner:
  HP, status, Speed relation, and remaining job

Boss priority / turn-order threat:
  move, item, lock, recharge, paralysis, or Quick Claw branch

Threshold:
  does the branch KO, put us into the next KO, or only chip?

Route choice:
  attack now / preserve cleaner / use bulkier answer / controlled sack /
  force lock or recoil first
```

## Case 1: Blaine Arcanine ExtremeSpeed

Boss shape:

```text
Blaine has Arcanine with ExtremeSpeed and Life Orb-style recoil pressure in the
route map.
```

Bad advice:

```text
"Our Water or Rock attacker is faster, so it cleans."
```

Priority-range reading:

```text
Question:
  Is the cleaner above ExtremeSpeed range after Spikes, sun damage, recoil, or
  prior Fire pressure?

If yes:
  immediate attack can be correct if it removes Arcanine or forces the final
  route.

If no:
  the plan should preserve the cleaner, use a bulkier answer, force recoil, or
  create a sack entry before trying to clean.
```

Answer-changing information:

- Exact current HP and whether Spikes are on the player's side.
- Whether sun is active and whether the cleaner has already taken Fire damage.
- Whether ExtremeSpeed actually reaches the current HP by local damage
  evidence.

## Case 2: Bruno Mach Punch

Boss shape:

```text
Bruno has Mach Punch users in the source route map.
The player's faster Psychic/Flying-style cleaner may be low after handling
Onix, Hitmontop, or Hitmonlee.
```

Bad advice:

```text
"Use the fast cleaner because it outspeeds the Fighting type."
```

Priority-range reading:

```text
Question:
  Does Mach Punch bypass the Speed route and remove the cleaner before its job?

If Mach Punch is lethal:
  preserve the cleaner and enter a bulkier answer, force the Mach Punch user to
  spend its priority into a sack, or create a KO threshold with another piece.

If Mach Punch is not lethal:
  attack may be correct, but only if the cleaner remains useful after the chip.
```

Answer-changing information:

- Whether the boss's current active actually has Mach Punch.
- Whether the cleaner is also needed for Machamp, Heracross, or another later
  route.
- Exact Fighting-type damage under the local physical/special and type-passive
  rules.

## Case 3: Blue Or Red Low-HP Cleanup

Boss shape:

```text
Blue can create Arcanine priority cleanup after Pidgeot, Gyarados, Tauros, or
Rhydon chip.
Red can leave Pikachu or another priority route in a low-HP endgame.
```

Bad advice:

```text
"Take the KO; the last boss Pokemon is slower."
```

Priority-range reading:

```text
Question:
  After this KO, does the next boss priority user revenge our converter?

If yes:
  the KO may be a trap. Prefer a move that preserves HP, forces recoil, creates
  a sack entry, or keeps the converter out of priority range.

If no:
  finish the route. Do not over-preserve once the forced line is won.
```

Answer-changing information:

- Remaining boss roster and whether the priority user is still alive.
- Hazard state and recoil state.
- Whether the active move creates a forced KO or leaves a Focus Band / Quick
  Claw / damage-roll branch.

## Transfer Lesson

Before calling a faster Pokemon a cleaner, write:

```text
Normal Speed order:
Priority / Quick Claw / lock / recharge exceptions:
Current HP after entry hazards:
Damage range from priority:
Does the cleaner still perform its next job after taking that branch:
```

Priority is not just an opponent danger. It is also a commitment by the boss.
If the boss locks, reveals, or spends a low-power priority move that fails to
KO, that turn may create entry, setup, recoil, recovery, or counterattack value.
