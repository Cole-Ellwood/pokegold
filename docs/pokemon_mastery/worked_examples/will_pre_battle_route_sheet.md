# Worked Example: Will Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Will as a hazard-control and
special-route arbitration fight. This is a team-agnostic planning artifact, not
final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `WillGroup`.
- Boss route map: `../boss_route_maps/will_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Pursuit, Dark special category, Future Sight, Focus Band, Expert Belt,
  Protect, Explosion, and type/item references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- GSC Spikes material: hazards are strongest when paired with status, forced
  switches, spin pressure, or opportunistic attackers; hazards alone are not a
  plan.
- GSC Starmie material: a spinner with speed and coverage can make hazard
  removal expensive to punish.
- GSC Houndoom material: Pursuit works because the target dislikes both staying
  and switching, not because switching is always wrong.
- GSC anchor lessons: bulky Rest users turn weak damage into lost tempo unless
  the answer creates progress during boost, Rest, or recovery windows.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Will

Known boss roster:
  Forretress / Starmie / Slowbro / Alakazam / Houndoom / Xatu

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include an Alakazam answer, a Houndoom/Pursuit plan, and a Slowbro
  anchor-break plan; exact species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Dark being special,
  Pursuit doubling on switching targets, Focus Band variance, Future Sight's
  local delayed-hit behavior, Expert Belt requiring type-effectiveness
  evidence, and Explosion as a one-time route trade

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, and whether the player can punish
  Starmie's Rapid Spin without losing the Alakazam/Houndoom/Slowbro answer map
```

## Output Shape

Primary route:

- Stop Forretress from converting the opening into Spikes, Toxic, Protect
  scouting, or Explosion while preserving the pieces that answer Will's faster
  special routes.

Backup route:

- If Forretress gets hazard or status value, shorten the game around concrete
  pressure on Starmie, Slowbro, or Alakazam rather than trying to win a slow
  switching game through three-layer Spikes.

Boss route priority:

```text
immediate:
  Forretress Spikes / Toxic / Explosion.
  Alakazam coverage if the special answer has already been poisoned or chipped.
  Houndoom Pursuit if the current active wants to flee.

accumulating:
  Starmie Rapid Spin plus coverage, especially if the player's route depends on
  hazards.
  Slowbro Amnesia / Rest anchoring.
  Xatu Future Sight delayed-damage stacking.

endgame:
  Slowbro if the physical/status/phazing answer is gone.
  Alakazam or Houndoom once Spikes, poison, Pursuit, or Future Sight have
  narrowed switch options.
```

Boss route to deny first:

- Deny the route that removes switch freedom. Usually that is Forretress
  getting Spikes or Toxic onto the later special answer. If the user's team
  relies heavily on its own hazards, Starmie becomes the route to deny before
  stacking extra layers.

Boss route that can be delayed:

- Xatu can often be delayed until Future Sight is active. Once Future Sight is
  active, it becomes a ledger problem: the landing turn can make a previously
  safe pivot unsafe.

- Slowbro can be delayed only if the team has a confirmed plan that makes the
  first Amnesia or Rest turn costly. If weak chip lets it boost and Rest on
  schedule, it is no longer delayable.

Best lead profile:

- A lead that pressures Forretress immediately without being the only answer to
  Alakazam, Houndoom, or Slowbro. The lead should either threaten a meaningful
  KO/status/forced switch, punish Protect or Toxic, or make Explosion a bad
  trade for Will.

Avoid as lead:

- The only special answer if Forretress can poison it or Explode into it.
- A passive hazard setter if Starmie can spin without giving up a larger
  resource.
- A Psychic- or Ghost-leaning piece that must switch out of Houndoom without a
  Pursuit plan.
- A weak special attacker that gives Slowbro a free Amnesia/Rest loop.
- A plan that treats Future Sight as generic Psychic damage instead of a timed
  future hit.

First move plan:

- Give turn 1 one job: deny Forretress a free route or make its route expensive
  enough that Will cannot also keep Starmie/Slowbro/Alakazam/Houndoom intact.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Forretress's Spikes, Toxic, Protect, and Explosion branches.

Turn 2:
  If hazards/status landed, decide whether to remove them, punish Starmie,
  force a KO, or preserve the irreplaceable special answer.

Turn 3:
  Re-score around the route Will actually presents: Spin, Amnesia/Rest,
  Alakazam coverage, Houndoom Pursuit, or Future Sight.
```

Piece to preserve:

- The Alakazam answer if it is the only piece that handles fast Psychic plus
  elemental coverage.
- The Houndoom answer or Pursuit-proof pivot if the planned route requires
  switching a vulnerable special attacker.
- The Slowbro breaker/reset route if the team cannot outlast Amnesia plus Rest.

Piece that can be spent:

- A Forretress pressure piece whose later jobs are redundant after hazards are
  denied, or a poisoned pivot that creates a clean entry before it becomes a
  liability. Low HP alone is not enough.

Worst plausible branch:

- The player lets Forretress set Spikes or poison the main special answer, then
  tries to repair the game by switching repeatedly. Starmie removes the player's
  hazards, Slowbro boosts through weak damage, Houndoom makes the obvious pivot
  expensive with Pursuit, and Xatu's Future Sight forces the last answer into a
  bad landing turn.

Abandon conditions:

- Three-layer Spikes make the planned switch cycle impossible.
- The only Alakazam, Houndoom, or Slowbro answer is poisoned, exploded on, or
  below its required threshold.
- Starmie can Rapid Spin away the player's hazard route without losing a more
  important exchange.
- Slowbro gets Amnesia or Rest tempo that the current team cannot punish.
- Houndoom makes the planned switch worse than staying, attacking, or
  sacrificing a different piece.
- Future Sight is active and would land on the intended irreplaceable answer.
- Type-chart, passive, item, or damage evidence contradicts the assumed route.

What information would flip the lead or first move:

- A lead candidate that can pressure Forretress while remaining expendable
  after Explosion.
- A confirmed separate Alakazam answer, allowing the lead to absorb Toxic or
  Explosion more freely.
- A damage range proving Starmie cannot spin safely into the player's hazard
  setter.
- A damage range or status plan proving Slowbro cannot use Amnesia/Rest as a
  reset.
- A Pursuit calculation showing whether the vulnerable piece can switch out of
  Houndoom safely.
- A Future Sight timing fact showing the intended pivot is safe or unsafe on
  the landing turn.

## Extracted Lesson

Will is not "kill Forretress." Will is route arbitration under hazard pressure:
the player must decide whether the urgent job is denying Spikes/Toxic,
punishing Rapid Spin, preserving the special answer, breaking Slowbro, or
avoiding Pursuit and Future Sight traps. The right first move is the one that
keeps the most future routes alive, not necessarily the one that damages the
lead.
