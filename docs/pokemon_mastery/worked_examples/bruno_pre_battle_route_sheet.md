# Worked Example: Bruno Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Bruno as a hazard/phaze plus
physical-breaker fight. This is a team-agnostic planning artifact, not final
turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `BrunoGroup`.
- Boss route map: `../boss_route_maps/bruno_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Mach Punch priority, critical-hit items/stages, Focus Band, Expert Belt,
  Vital Throw, and type/category references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Machamp material: strong Fighting attackers are dangerous because STAB
  plus coverage can invalidate simple wall labels, and Cross Chop carries crit
  risk.
- Fighting-type material: priority and high-power Fighting moves convert chip
  into cleanup. The exact moves differ by generation, so abstract the lesson
  instead of importing modern mechanics.
- GSC Spikes material: hazards matter when they change switching cost, phazing
  value, and answer durability.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Bruno

Known boss roster:
  Onix / Hitmontop / Hitmonlee / Machamp / Hitmonchan / Heracross

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Machamp answer, a Heracross answer, and a plan for Mach Punch
  cleanup; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Mach Punch sharing the
  local priority-hit tier, Cross Chop high-crit behavior, Scope Lens and Focus
  Energy crit-stage pressure, Focus Band survival, Expert Belt requiring
  matchup evidence, and Vital Throw being always-hit rather than imported
  modern negative-priority behavior

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, crit-risk tolerance, and whether any
  Fighting answer survives Rock Slide / Earthquake / elemental punch coverage
  after Onix Spikes or Roar pressure
```

## Output Shape

Primary route:

- Deny Onix from turning the fight into Spikes plus Roar chip while preserving
  the answers needed for Machamp and Heracross.

Backup route:

- If Onix gets Spikes or a forced Roar sequence, shorten the fight around
  concrete KOs, status, phazing/Haze, or controlled sacrifices. Do not keep
  switching as though the field is clean.

Boss route priority:

```text
immediate:
  Onix Spikes / Roar if the lead is passive.
  Machamp if the current answer map is already chipped.
  Hitmonlee Meditate if it gets a free turn.

accumulating:
  Hitmontop Rapid Spin plus Mach Punch cleanup.
  Hitmonchan elemental punches into expected Fighting answers.
  Heracross Focus Energy plus Scope Lens crit pressure.

endgame:
  Mach Punch cleanup after Spikes, Rock Slide, Cross Chop, or Megahorn chip.
  Heracross or Machamp if the dedicated answer was spent early.
```

Boss route to deny first:

- Deny the route that damages the only Machamp or Heracross answer. Often that
  means stopping Onix's Spikes/Roar value before trying to build a slow hazard
  route of your own.

Boss route that can be delayed:

- Hitmontop can be delayed if the player's plan does not depend on keeping
  hazards and if Mach Punch does not threaten the current cleaner. If hazards
  are the player's route, Hitmontop becomes urgent.

- Hitmonchan can be delayed only when its elemental coverage does not invalidate
  the planned Fighting answer. This needs type/passive/damage evidence.

Best lead profile:

- A lead that pressures Onix immediately without being the only Machamp or
  Heracross answer. It should either deny Spikes, punish Roar, force Onix into
  damage, or create a safe handoff into a piece that does not mind Bruno's next
  route.

Avoid as lead:

- The only Machamp or Heracross answer if Onix can chip it with Rock Slide,
  Earthquake, Spikes, or Roar.
- A slow setup lead that gets Roared after Onix sets Spikes.
- A hazard lead if Hitmontop can spin for free.
- A fragile cleaner that enters Mach Punch range before Bruno's priority user
  is solved.
- A type-slogan Flying/Psychic pivot that has not priced Rock Slide,
  elemental punches, Expert Belt, or crit branches.

First move plan:

- Give turn 1 one job: prevent Onix from making every later Fighting answer
  enter through chip and bad positioning.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Onix's Spikes, Roar, Earthquake, and Rock Slide branches.

Turn 2:
  If Spikes or Roar happened, rebuild the answer map around groundedness and
  the current forced active. If not, decide which Bruno breaker enters next.

Turn 3:
  Re-score around Hitmontop spin/priority, Hitmonlee Meditate, Machamp
  coverage, Hitmonchan coverage, or Heracross crit pressure.
```

Piece to preserve:

- The Machamp answer by default. It must survive Cross Chop crit risk, Rock
  Slide, Earthquake, and Vital Throw assumptions from the actual local moveset.

- The Heracross answer if it is separate. Once Focus Energy plus Scope Lens is
  online, a static wall plan may no longer be stable.

Piece that can be spent:

- A lead that has already denied Onix and has no unique job against Machamp,
  Heracross, Hitmonchan, or Mach Punch cleanup.

- A poisoned, chipped, or low-HP piece only if it creates clean entry to the
  actual Bruno answer before it dies.

Worst plausible branch:

- The player beats Onix slowly, but lets it set Spikes and Roar the team into
  awkward entries. The Machamp answer takes chip, Hitmontop later threatens
  Mach Punch cleanup or spins away the player's route, and Heracross or
  Hitmonchan breaks the remaining answer with crit pressure or coverage.

Abandon conditions:

- The only Machamp or Heracross answer drops below its survival threshold.
- Spikes plus Roar make the planned switch cycle impossible.
- Hitmontop can spin away the player's route or put the cleaner into Mach Punch
  range.
- Hitmonlee gets Meditate and no immediate denial route remains.
- Hitmonchan coverage invalidates the expected pivot.
- Heracross Focus Energy plus Scope Lens makes the plan depend on no crit.
- Type-chart, passive, item, crit, or damage evidence contradicts the assumed
  answer.

What information would flip the lead or first move:

- A lead candidate that can deny Onix while staying expendable afterward.
- A separate confirmed Machamp answer, making the Onix answer more spendable.
- Damage evidence showing the Heracross answer still survives after one Spikes
  entry and Rock Slide.
- A calc showing Hitmonchan's elemental coverage does or does not break the
  planned Fighting pivot.
- Whether the player's route actually needs hazards or can ignore Hitmontop's
  Rapid Spin role.
- Whether Mach Punch range covers the intended cleaner after the opening.

## Extracted Lesson

Bruno is not "bring a Psychic or Flying type." Bruno is answer durability under
hazard and coverage pressure. The player must deny Onix from taxing the real
Fighting answers, then preserve enough HP and positioning to survive Machamp,
Heracross, Hitmonchan coverage, and Mach Punch cleanup.
