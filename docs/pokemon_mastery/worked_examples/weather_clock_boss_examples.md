# Worked Example: Weather Clock Ownership

Status: constructed boss-facing study example. This is not exact turn advice
until the user's active Pokemon, HP, moves, items, bench, and damage evidence
are known.

Purpose: apply the weather recipe to Misty and Blaine without importing later
generation mechanics blindly.

## Source Basis

Expert sources:

- Smogon's Rain Offense Guide treats manual rain as a finite offensive window:
  the rain user must keep pressure because the team is on a timer, and boosted
  STAB does not remove the need to identify the opposing answers.
- Smogon's battle-conditions guide frames weather as a field condition that
  changes damage, accuracy, charge turns, and recovery.
- Smogon's Sunny Day material is useful for the abstract idea that sun combines
  multiple attacking types and can turn Grass/Fire pieces into a shared route,
  but exact ability mechanics must not be imported into Gym Leader Lab unless
  local source confirms them.

Local evidence:

- Misty route sheet: `../boss_route_maps/misty_turn1_route_sheet.md`
- Blaine route sheet: `../boss_route_maps/blaine_turn1_route_sheet.md`
- Weather docs/source are listed in those sheets; local weather lasts five
  turns.

## Case 1: Misty Politoed Opens

Public boss state:

```text
Misty lead:
Politoed @ Leftovers
Rain Dance / Hypnosis / Surf / Ice Beam

Back line:
Starmie with Recover / Hydro Pump / Psychic / Thunder
Quagsire with Curse / Earthquake / Surf / Rest
Lapras with Rain Dance / Surf / Ice Beam / Thunder
Lanturn with Thunder Wave / Surf / Thunder / Ice Beam
```

Policy answer:

- Primary question: if Politoed uses Rain Dance or Hypnosis on turn 1, which
  later Misty route becomes harder to stop?
- Best move class when our lead pressures Politoed and is not irreplaceable:
  attack or otherwise force immediate progress. Do not donate a setup turn
  merely because Politoed itself looks manageable.
- Acceptable move class when our lead is the only Starmie/Lapras answer:
  pivot to a sleep/rain buffer or choose a lower-value move that preserves the
  answer, if direct pressure risks losing the whole Water route later.
- Catastrophic class: passive setup that lets Politoed start rain or sleep the
  main Water answer, then allows Starmie or Lapras to enter while rain turns
  make Hydro Pump / Surf / Thunder more punishing.

Weather ledger after Rain Dance:

```text
Turn weather starts:
Rain turns remaining:
Who uses boosted Water damage better:
Who uses Thunder reliability better:
Which answer lost value because Fire damage or neutral-weather math changed:
Can we force Misty to spend rain turns switching, recovering, or using weak
coverage:
```

Re-score triggers:

- Hypnosis hits the planned Starmie/Lapras answer.
- Rain is active and Starmie enters.
- Lanturn paralyzes the speed-control piece.
- Quagsire gets a Curse while the team is overfocused on special Water damage.
- Damage shows the assumed answer does not survive boosted Water plus coverage.

Answer-changing information:

- Whether the user's lead can 2HKO or OHKO Politoed before rain payoff.
- Whether the user's bench has a separate sleep absorber.
- Whether the Starmie/Lapras answer is also the lead.
- Exact damage under local rain and type/passive mechanics.

## Case 2: Blaine Ninetales Enters

Public boss state:

```text
Blaine route piece:
Ninetales @ Charcoal
Sunny Day / Fire Blast / Psychic / Safeguard

Other route pieces:
Magcargo with Spikes / Curse / Flamethrower / Rock Slide
Rapidash with Agility / Fire Blast / Quick Attack / Double-Edge
Arcanine with Flamethrower / ExtremeSpeed / Crunch / Iron Tail
Magmar with Fire Blast / ThunderPunch / Psychic / Hidden Power
```

Policy answer:

- Primary question: does Sunny Day or Safeguard make the next Fire attacker
  easier to convert than Ninetales is to punish now?
- Best move class when Ninetales can be forced or heavily damaged: attack or
  pivot into a route that denies the weather payoff immediately.
- Acceptable move class when direct damage is not enough: stall or pivot through
  the five-turn sun/Safeguard window while keeping the real Fire answer out of
  Rapidash Quick Attack or Arcanine ExtremeSpeed range.
- Catastrophic class: status-first or Water-only play that lets Sunny Day and
  Safeguard invalidate the planned answer, then leaves the Fire answer chipped
  by Spikes into priority or coverage range.

Weather ledger after Sunny Day:

```text
Sun turns remaining:
Does our plan rely on Water damage:
Does Blaine now force a Fire KO or 2HKO:
Is status blocked by Safeguard:
Can we burn sun turns without giving Rapidash Agility or Arcanine priority
cleanup:
Which piece must stay above priority range after Spikes/recoil:
```

Re-score triggers:

- Magcargo already set one or more Spikes layers.
- Ninetales used Safeguard, making status routes unavailable.
- Rapidash used Agility.
- Arcanine entered and the cleaner is in ExtremeSpeed range.
- Magmar revealed coverage or Hidden Power damage that changes the pivot map.

Answer-changing information:

- Exact HP threshold for the Fire answer after Spikes and priority.
- Whether the user has weather replacement, Protect, recovery, phazing, Haze,
  or a safe sacrifice.
- Whether local damage evidence supports surviving sun-boosted Fire damage.
- Whether the planned Water attack still changes a route under sun.

## Extracted Recipe

Weather is a deadline for both sides. The weather owner must convert before the
clock expires; the defender must decide whether to punish the setup turn, force
the owner to waste turns switching or recovering, or preserve the one piece that
still answers the weather payoff.

Bad explanation:

```text
Rain/sun is up, so their attacks are stronger.
```

Useful explanation:

```text
Rain is up for five turns. Misty gets value only if those turns become Starmie
or Lapras pressure; if we force Recover, a switch, or a resisted coverage move,
the weather turn is partially spent. If our only Water answer is asleep, the
weather clock belongs to Misty instead.
```
