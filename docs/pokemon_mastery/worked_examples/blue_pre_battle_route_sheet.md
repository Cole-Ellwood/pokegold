# Worked Example: Blue Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to a mixed boss roster. This is a
team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `BlueGroup`.
- Boss route map: `../boss_route_maps/blue_turn1_route_sheet.md`.
- Opening policy:
  `../romhack_deltas/boss_opening_policy.md` and
  `../boss_route_maps/adaptive_lead_audit_2026-05-13.md`; Blue can open with
  Pidgeot, Porygon2, or Gyarados.
- Choice Band, Life Orb, Muscle Band, Dragon Dance, priority, and Gen 2
  physical/special behavior:
  `../../agent_navigation/gen2_vs_modern_mechanics.md`.
- Species stat/types:
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC team-structure material: read a roster as role machinery, not isolated
  species.
- Porygon2 analysis: Recover plus mixed coverage makes it a durable bridge, not
  passive dead time.
- Gyarados analysis: Dragon Dance routes are often late-game routes after
  checks have been weakened.
- Tauros analysis: fast Normal pressure uses coverage to punish the expected
  Normal answer; prediction matters only when the risk is priced.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Blue

Known boss roster:
  Pidgeot / Porygon2 / Gyarados / Tauros / Rhydon / Arcanine

Known boss fixed/adaptive opener source:
  Adaptive first-three: Pidgeot / Porygon2 / Gyarados

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include one Gyarados denial route and one Arcanine priority/fire route
  answer; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  Choice Band physical lock and boost, local Dragon Dance behavior, local
  priority tier, Life Orb recoil, type-chart/passive differences, Gen 2
  type-based physical/special split

Missing evidence:
  exact player team, HP, levels, moves, items, speed relations, damage ranges,
  and whether any answer survives boosted Gyarados or Arcanine ExtremeSpeed
```

## Output Shape

Primary route:

- Cover the adaptive first-three opening while preserving the answer to Blue's
  setup/priority routes. If Pidgeot opens, exploit Choice Band lock or recoil;
  if Porygon2 opens, deny free Recover stabilization; if Gyarados opens, deny
  Dragon Dance immediately.

Backup route:

- If Pidgeot's lock is not exploitable, shorten the fight by forcing Porygon2
  recovery, denying Gyarados Dragon Dance, or using recoil/priority math to
  make Tauros or Arcanine easier to finish.

Boss route priority:

```text
immediate:
  Pidgeot physical lock/recoil pressure if it opens.
  Porygon2 Recover bridge if it opens.
  Gyarados Dragon Dance if it opens.
  Tauros broad physical coverage if it enters after the lead exchange.
  Arcanine ExtremeSpeed cleanup if our team is already chipped.

accumulating:
  Porygon2 Recover + mixed coverage erasing weak progress.
  Rhydon Roar/coverage disrupting setup or Electric-only plans.

endgame:
  Gyarados Dragon Dance conversion if not already denied.
  Arcanine priority cleanup after Life Orb pressure.
```

Boss likely openings:

- Pidgeot is the favored opener, but Blue is source-checked as adaptive first
  three. Treat Porygon2 and Gyarados as real turn-1 states, not rare surprises.

Boss route to deny first:

- Deny the route that either chips the only Gyarados answer or gives Porygon2 a
  free recovery bridge. If the user's team has only one Gyarados answer, that
  preservation dominates early chip on Pidgeot.

Boss route that can be delayed:

- Rhydon can often be delayed if the team has a confirmed fast special damage
  route and does not rely on Electric-only pressure. This needs local
  type/passive/damage evidence before becoming advice.

Best lead profile:

- A lead that has a useful first-turn job into Pidgeot, Porygon2, and Gyarados:
  punish or scout Pidgeot's lock, prevent Porygon2 from erasing the first turn,
  and deny or survive immediate Gyarados setup. It should still leave a
  separate answer to Gyarados and Arcanine when possible.

Avoid as lead:

- The only Gyarados answer.
- The only Arcanine ExtremeSpeed or Fire route answer.
- A passive wall that lets Porygon2 or Rhydon enter without losing a resource.
- A fragile cleaner that gets put into Quick Attack or ExtremeSpeed range.
- A Pidgeot-only answer that lets opening Gyarados boost or opening Porygon2
  Recover-loop without cost.

First move plan:

- Give the first move one job based on the actual opener: reveal or punish
  Pidgeot's lock, force Porygon2 into a real threshold, deny Gyarados Dragon
  Dance, or pivot to a piece whose role is not needed for Gyarados/Arcanine.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Identify which adaptive opener appeared and price that route: Pidgeot lock,
  Porygon2 recovery, or Gyarados setup.

Turn 2:
  If the opener creates a safe punish, take the route-improving punish. If not,
  pivot without exposing the Gyarados or Arcanine answer.

Turn 3:
  Re-score around the first Blue route that enters: Porygon2 recovery,
  Gyarados setup, Tauros/Rhydon breaking, or Arcanine priority.
```

Piece to preserve:

- The Gyarados denial route. Exact species depends on the user's team, but the
  role must survive Pidgeot and Tauros chip unless another denial route is
  confirmed.

Piece that can be spent:

- A Pidgeot answer whose later jobs are redundant after the lock is known, or a
  low-value pivot that creates a clean entry for the actual Gyarados/Porygon2
  answer. Low HP alone is not enough.

Worst plausible branch:

- The lead was selected for a Pidgeot-only script, but Blue opens Porygon2 or
  Gyarados. The first turn then either lets Recover stabilize or gives Dragon
  Dance a free conversion, and Arcanine finishes through ExtremeSpeed once the
  team is already low.

Abandon conditions:

- Blue opens Porygon2 or Gyarados instead of Pidgeot.
- Pidgeot locks into a move the plan cannot punish safely.
- Porygon2 can Recover through the current damage route.
- Gyarados uses Dragon Dance or the Gyarados answer drops below the boosted
  survival threshold.
- Tauros reveals coverage that invalidates the Normal answer.
- Rhydon Roars away the intended setup or forces the wrong piece through damage.
- Arcanine's ExtremeSpeed range covers the intended cleaner.
- Any local type, passive, item, or damage evidence contradicts the assumed
  answer.

What information would flip the lead or first move:

- A lead candidate that can handle all three adaptive openers while preserving
  a valid Gyarados answer.
- A separate, confirmed Gyarados answer that makes spending the lead safer.
- A damage range showing Porygon2 cannot Recover through the chosen pressure.
- A damage range showing Arcanine priority is or is not lethal after the lead
  exchange.

## Extracted Lesson

Blue is not "beat Pidgeot." Blue is an answer-map test. A correct opening must
exploit the Choice Band lead while keeping enough structure for Dragon Dance,
Recover, Roar, broad physical coverage, and priority cleanup.
