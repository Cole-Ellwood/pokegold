# Worked Example: Misty Starmie vs Meganium Follow-Up Chain

Purpose: continue `misty_starmie_meganium_player_turn_drill.md` one turn
farther. The first move is already solved as `Razor Leaf`; this file practices
re-scoring after that correct move instead of treating the battle as finished.

Mechanics profile: `romhack_gym_leader_lab`

Local evidence:

- Root drill: `misty_starmie_meganium_player_turn_drill.md`.
- Recovery tempo note: `misty_starmie_meganium_recover_tempo.md`.
- Misty route map: `../boss_route_maps/misty_turn1_route_sheet.md`.
- Roster source: `data/trainers/parties.asm`, `MistyGroup`.
- Type chart and species table:
  `../../agent_navigation/hack_mechanics_reference.md`.
- Weather and recovery behavior:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.

Expert anchors:

- Smogon Rain Offense guide:
  <https://www.smogon.com/dp/articles/rain_offense>.
- Smogon GSC Spikes guide, especially recovery pressure and Starmie as a
  long-game support piece:
  <https://www.smogon.com/gs/articles/gsc_spikes>.

## Root State

```text
Misty active:
  Starmie Lv63 at 46%, Wise Glasses
  Known moves: Hydro Pump / Recover / Psychic / Thunder

Misty bench:
  Politoed / Quagsire / Lapras / Lanturn

Player active:
  Meganium Lv62 at 68%
  Revealed moves: Razor Leaf / Reflect
  Public priors: Synthesis plausible, Body Slam plausible

Field:
  Rain active
  Player Reflect active
```

Root recommendation:

```text
Use Razor Leaf.
```

Reason:

```text
Razor Leaf removes Starmie from the shown HP before Recover can reset the
exchange. The move wins the current route because it denies the recovery bridge,
not because it is a type-chart slogan.
```

## Branch A: Starmie Uses Psychic, Then Faints

New state:

```text
Starmie fainted.
Meganium took Psychic chip and is roughly in the low-to-mid 40% range by the
source damage anchors.
Rain is still active unless the turn counter says otherwise.
Misty chooses the replacement.
```

Next recommendation:

```text
Do not autopilot Meganium. Preserve it by default unless the replacement can be
removed immediately or Meganium is no longer needed for Quagsire/Lanturn.
```

If Lapras enters:

- Check rain turns first. Lapras in rain has Surf / Ice Beam / Thunder pressure
  and Leftovers.
- Switch or pivot rises if Meganium is still the Quagsire answer or if Ice Beam
  puts Meganium into a losing route.
- Staying in rises only if Razor Leaf, Body Slam, or another move crosses a
  real threshold before Lapras converts.

If Quagsire enters:

- Grass damage is route-relevant by local chart evidence: Quagsire is
  Water/Ground, and the generated chart lists Grass as 2x into Water and 2x
  into Ground before passive or damage modifiers.
- Attack rises if Razor Leaf denies Curse or Rest from becoming the new route.
- Switching rises only if Meganium is too low, out of PP, or needed for Lapras /
  Lanturn more than Quagsire.

If Lanturn enters:

- Price Thunder Wave before protecting Meganium as a generic Water answer. A
  paralyzed Meganium may lose its ability to answer Quagsire or pressure the
  remaining route.
- Pivoting to a status absorber rises if the team has one and Meganium's later
  job matters.

If Politoed enters:

- Rebuild around Hypnosis and Rain Dance. If Sleep Clause is open and Meganium
  remains important, sleep absorption or pivoting can outrank another attack.

Failure sign:

```text
"Starmie is gone, keep clicking Razor Leaf" without checking replacement,
weather, status, and Meganium's remaining job.
```

## Branch B: Starmie Uses Recover, Then Takes Razor Leaf

New state:

```text
Starmie survives but is badly damaged.
Meganium remains near the original HP because Recover spent Starmie's turn.
Rain remains active.
```

Next recommendation:

```text
Use Razor Leaf again unless Meganium cannot act, Starmie has moved out of KO
range by exact evidence, or a switch creates a stronger route.
```

Reason:

- Recover failed to exit the damage cycle. The recovered HP did not create a
  new route if Meganium can keep attacking.
- The follow-up must still respect Starmie's Speed and coverage. If Starmie can
  attack first and put Meganium into a decisive Lapras/Lanturn range, record
  that as the cost of finishing the bridge.

Failure sign:

```text
The advisor sees Recover and switches to a slow plan even though the recovery
window is still closed.
```

## Branch C: Misty Switches Instead Of Spending Starmie

If Lapras switches in:

```text
Re-score around bulky rain extension. Preserve Meganium by default unless the
incoming damage roll proves Meganium can safely pressure Lapras and still cover
Quagsire or Lanturn.
```

If Quagsire switches in:

```text
Razor Leaf pressure likely becomes the immediate route, but exact advice still
needs damage, PP, and whether Meganium can survive the next Ice / Earthquake /
Rest sequence. Do not give Quagsire a free Curse by making a decorative pivot.
```

If Lanturn switches in:

```text
Thunder Wave and Ice Beam pressure are the branch to price. If Meganium is the
only Quagsire answer, preserving its status can outrank staying for damage.
```

If Politoed switches in:

```text
Sleep/rain arbitration returns. The next move depends on Sleep Clause, rain
turns, and whether Meganium is allowed to be the sleep target.
```

## Follow-Up Scorecard

```text
root move: Razor Leaf
root route gained: remove Starmie / deny Recover bridge
branch to price next: Misty's replacement
piece to preserve: Meganium if it remains the Quagsire, Lapras, or status-plan
  answer
main bad habit: correct first move -> stale script
```

## Extracted Lesson

Correct first moves create new states; they do not end the thinking. After
Starmie is removed or forced into a bad recovery turn, the next recommendation
must be chosen from the replacement's route: Lapras rain extension, Quagsire
Curse/Rest, Lanturn paralysis, or Politoed sleep/rain.
