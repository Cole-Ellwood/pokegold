# Worked Example: Blaine Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Blaine as a hazard, sun,
Safeguard, setup-speed, priority, recoil, coverage, and contact-punish fight.
This is a team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `BlaineGroup`.
- Boss route map: `../boss_route_maps/blaine_turn1_route_sheet.md`.
- Spikes source: `../../engine/battle/move_effects/spikes.asm`.
- Sunny Day and Safeguard source:
  `../../engine/battle/move_effects/sunny_day.asm` and
  `../../engine/battle/move_effects/safeguard.asm`.
- Fire Blast, Flamethrower, Psychic, Agility, Quick Attack, ExtremeSpeed,
  Double-Edge, Crunch, Iron Tail, ThunderPunch, Hidden Power, Curse, Rock
  Slide, Rocky Helmet, Life Orb, Muscle Band, Wise Glasses, Charcoal, contact
  flags, weather, and priority references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.
- Fire low-HP passive fixture:
  `../../../tools/damage_debugger/clobber_smoke.py::special_fire_low_hp` verifies
  the full-Fire below-one-third damage boost. Blaine's Ninetales, Rapidash,
  Arcanine, and Magmar are full-Fire; Magcargo is Fire/Rock and should keep
  half-Fire exact damage labeled source-only until the boundary fixture runs.

Expert study anchors:

- Smogon battle-condition material: weather changes damage, move timing,
  recovery, and accuracy, so it must be tracked as a live field condition.
- Smogon Sunny Day material: sun is useful only when it converts before the
  clock expires; the defender can answer by punishing the setup turn, forcing
  wasted turns, or preserving the one piece that survives the payoff.
- Smogon priority material: priority attacks can override normal Speed-based
  revenge plans and must be priced as endgame range, not just move damage.
- Smogon GSC Spikes and long-term thinking material: hazards are strongest
  when they make the later answer fail after one or two extra entries.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Blaine

Known boss roster:
  Magcargo / Ninetales / Rapidash / Arcanine / Magmar

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a plan for Magcargo Spikes/Curse, a sun-weather answer, a
  priority-safe Arcanine/Rapidash endgame answer, and a Magmar coverage pivot;
  exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes with fourth-click failure, Sunny Day lasting five turns,
  sun boosting Fire damage and weakening Water damage, Safeguard lasting five
  turns and blocking status attempts, Quick Attack and ExtremeSpeed sharing the
  local priority-hit tier, Agility changing Speed control, Life Orb boosting
  damage by 1.3x with max HP / 10 recoil, Muscle Band and Wise Glasses boosting
  physical or special damage by 1.1x, full-Fire attackers below one-third HP
  getting a debugger-verified Fire damage boost, Rocky Helmet punishing contact
  for max HP / 6, and contact flags being move-specific

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, contact flags for intended attacks,
  whether the lead can deny Magcargo before Spikes or Curse matter, whether a
  Water-based answer still works under sun, whether the status route is blocked
  by Safeguard, whether Rapidash after Agility outspeeds and KOs, and whether
  Arcanine priority reaches the planned cleaner
```

## Output Shape

Primary route:

- Keep one real Fire-route answer above the thresholds Blaine is trying to
  create. Magcargo can tax contact and start Spikes, Ninetales can create a
  five-turn sun/Safeguard window, Rapidash can flip Speed control with Agility,
  Arcanine can turn low HP into priority cleanup, and Magmar can punish the
  obvious pivot with coverage.

Backup route:

- If Magcargo gets Spikes or Ninetales starts sun/Safeguard, stop using the
  old defensive math. Rebuild around layer count, sun turns, status
  availability, priority ranges, Life Orb recoil, and which attacker is now
  closest to converting.

Boss route priority:

```text
immediate:
  Magcargo Spikes if the team needs repeated grounded switching.
  Magcargo Curse if the lead cannot punish setup.
  Ninetales Sunny Day if the planned answer depends on Water damage or
  surviving clear-weather Fire damage.
  Arcanine ExtremeSpeed if the converter is already in priority range.

accumulating:
  Ninetales Safeguard blocking the player's status route.
  Magcargo Rocky Helmet plus Spikes chipping the real Fire answer.
  Life Orb recoil moving Arcanine into range while it also boosts damage.

endgame:
  Rapidash after Agility plus Quick Attack chip.
  Arcanine priority cleanup after Spikes, recoil, or Fire pressure.
  Magmar coverage after the obvious Fire pivot has been revealed.
```

Boss route to deny first:

- Deny the route that changes the answer map for the next two turns. If the
  player has one Fire answer, Magcargo Spikes or Ninetales sun may be more
  urgent than the active damage. If the player relies on status, Safeguard is
  the turn that invalidates the plan.

Boss route that can be delayed:

- Magmar can be delayed while the pivot map is healthy and coverage is still
  only plausible. Once Hidden Power or a coverage damage band reveals the
  intended answer is unstable, Magmar becomes urgent.

- Ninetales can be delayed only when the team can burn sun/Safeguard turns
  without giving Rapidash Agility, Arcanine priority range, or Magmar free
  coverage.

Best lead profile:

- A lead that pressures Magcargo without unsafe contact and without being the
  only sun or priority answer. It should either deny Spikes/Curse, force
  immediate damage, make Ninetales's weather turn expensive, or preserve the
  piece needed for Arcanine and Rapidash ranges.

Avoid as lead:

- A contact-first attacker if Rocky Helmet recoil breaks its later job.
- A status-first lead if Ninetales can make Safeguard free.
- A Water-only plan that becomes unstable once Sunny Day starts.
- The only priority-safe cleaner if Magcargo chip or Arcanine ExtremeSpeed
  changes the endgame.
- A Fire-answer label that has not priced Magmar's ThunderPunch, Psychic, and
  Hidden Power branches with local evidence.

First move plan:

- Give turn 1 one job: stop Magcargo from making Blaine's later clocks cheaper.
  Attacking is good when it denies Spikes/Curse or forces Magcargo into a bad
  trade. Switching is good only if it preserves the real answer while still
  handling Magcargo's best branch. Setting hazards or status is good only if it
  does not donate the weather/Safeguard window.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Magcargo's Spikes, Curse, Flamethrower, and Rock Slide branches against
  the lead's later role and contact risk.

Turn 2:
  If Spikes landed, rebuild around grounded switch cost and priority ranges. If
  Magcargo was denied, prepare for Ninetales weather/Safeguard, Rapidash
  Agility, Arcanine priority, or Magmar coverage.

Turn 3:
  Start the ledger: Spikes layers, sun turns, Safeguard turns, Rapidash Speed
  boosts, Arcanine Life Orb recoil and priority range, Magmar revealed Hidden
  Power/damage, and whether contact recoil changed a required threshold.
```

Piece to preserve:

- The priority-safe endgame answer by default. If Arcanine or Rapidash can use
  priority to bypass Speed, this piece must stay above the relevant threshold.

- The weather answer if it is separate. A pivot that works before sun may stop
  working once Fire and Water damage change.

- The Magmar coverage pivot until Hidden Power or damage evidence proves which
  branch is real.

Piece that can be spent:

- A lead that has already denied Magcargo and has no unique job against
  Ninetales, Rapidash, Arcanine, or Magmar.

- A status user after Safeguard is gone or after status no longer carries the
  route.

Worst plausible branch:

- The player lets Magcargo stack Spikes or Curse, then lets Ninetales set sun
  or Safeguard, causing the Water/status plan to fail. Rapidash uses Agility or
  Arcanine enters while the cleaner is in priority range, and Magmar coverage
  punishes the only remaining pivot.

Abandon conditions:

- Spikes layers change the HP threshold required for the Fire answer.
- Sunny Day is active and the plan depends on Water damage or clear-weather
  Fire survival.
- Safeguard is active and the plan depends on status.
- Rapidash has used Agility and no immediate denial, phaze/Haze, status,
  priority, sacrifice, or survival route remains.
- Arcanine priority reaches the planned cleaner.
- Ninetales, Rapidash, Arcanine, or Magmar is below one-third HP and still has
  a Fire attack available.
- Magmar reveals Hidden Power or coverage damage that contradicts the assumed
  pivot.
- Type-chart, passive, item, contact, weather, priority, or damage evidence
  contradicts the assumed answer.

What information would flip the lead or first move:

- Whether the lead can deny Magcargo before Spikes or Curse changes the fight.
- Whether the lead's attack triggers Rocky Helmet and loses a later role.
- Whether the player has weather replacement, Protect, recovery, phazing/Haze,
  or a safe sacrifice to burn sun turns.
- Whether the main Fire answer still survives sun-boosted Fire damage after one
  Spikes entry.
- Whether Arcanine's Life Orb recoil creates a safe wait-out line or whether
  boosted damage plus ExtremeSpeed makes waiting impossible.
- Whether Magmar's Hidden Power type or damage invalidates the planned pivot.

## Extracted Lesson

Blaine is not solved by "bring Water." Blaine is a clock-stacking fight:
Magcargo starts hazard/contact pressure, Ninetales changes the next five turns,
Rapidash flips Speed, Arcanine tests priority range, and Magmar punishes the
obvious answer with coverage. The correct opening is the one that denies the
clock Blaine can actually convert while preserving the piece that still answers
the weather and priority payoff.
