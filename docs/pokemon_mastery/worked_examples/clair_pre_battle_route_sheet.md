# Worked Example: Clair Pre-Battle Route Sheet

Purpose: apply the pre-battle route sheet to Clair as a hazard, Haze, Dragon
Dance, mixed-coverage, status-berry, and locked-move conversion fight. This is
a team-agnostic planning artifact, not final turn advice.

Local evidence:

- Roster source: `data/trainers/parties.asm`, `ClairGroup`.
- Boss route map: `../boss_route_maps/clair_turn1_route_sheet.md`.
- Spikes / Rapid Spin delta:
  `../romhack_deltas/spikes_and_rapid_spin.md`.
- Dragon Dance, Outrage category exception, rampage behavior, Quick Claw,
  MiracleBerry, Expert Belt, Haze, Roar timing, Dragon passives, and local
  Steelix typing references:
  `../../agent_navigation/gen2_vs_modern_mechanics.md` and
  `../../agent_navigation/hack_mechanics_reference.md`.

Expert study anchors:

- Setup-sweeper material: setup is dangerous because it changes both the damage
  race and speed/control map; a free boost can be more important than one turn
  of damage.
- Kingdra material from later generations: bulky Dragon Dance users need their
  checks weakened or removed, and mixed coverage can punish the wall expected
  to stop the sweep. Transfer this as a planning concept, not as mechanics.
- GSC Spikes material: hazards combine with status and phazing to turn repeated
  switches into route progress; Spikes alone are not the whole plan.
- Setup-control material: Haze is valuable because it invalidates accumulated
  boosts, so any setup plan must price whether the Haze user can move safely.

## Inputs Needed

```text
Mechanics profile:
  romhack_gym_leader_lab

Boss:
  Clair

Known boss roster:
  Gligar / Mantine / Kingdra / Dragonair / Steelix / Dragonair

Our team:
  unknown

Our lead candidates:
  unknown

Our irreplaceable pieces:
  must include a Kingdra answer, a Dragonair setup answer, a plan for Mantine's
  Haze / Rapid Spin, and a Steelix answer checked against local typing; exact
  species unknown

Our one-time resources:
  unknown

Known romhack deltas that matter:
  three-layer Spikes, Rapid Spin clearing all layers, Dragon Dance raising the
  user's current higher offensive stat plus Speed, Outrage being Dragon-typed
  with a Dragon-user physical category exception, Outrage locking for 2-3 turns
  before possible confusion, Quick Claw's 60/256 speed override chance,
  MiracleBerry's one-time status cure, Expert Belt's super-effective boost
  requiring type evidence, Dragon passives, and Steelix as Steel/Dragon

Missing evidence:
  exact player team, HP, levels, moves, items, groundedness, speed relations,
  damage ranges, passive type states, whether the lead can prevent Gligar's
  first clock, whether Mantine can Haze or spin safely, and whether the
  Kingdra/Dragonair answers still work after one boost
```

## Output Shape

Primary route:

- Preserve the anti-setup plan until Clair's Dragon Dance users are contained.
  Gligar's hazards/status and Mantine's reset tools exist to make Kingdra,
  Dragonair, or Steelix harder to answer later.

Backup route:

- If the primary answer is poisoned, paralyzed, chipped by Spikes, Hazed out of
  setup, or bypassed by mixed coverage, shorten the battle around a second
  denial line: immediate damage, Haze, phazing, revenge range, sacrifice into a
  safe attacker, or exploiting Outrage lock.

Boss route priority:

```text
immediate:
  Gligar Toxic if it puts the only Kingdra or Dragonair answer on a clock.
  Gligar Spikes if the user's team needs repeated grounded switching.
  Kingdra or Dragonair Dragon Dance when the answer map is not ready.
  Expert Belt Dragonair coverage if the current pivot is only type-slogan safe.

accumulating:
  Mantine Rapid Spin / Haze if the user's route depends on hazards or boosts.
  Thunder Wave from Expert Belt Dragonair if it removes speed control.
  Steelix Roar with Spikes active.

endgame:
  Kingdra converting with boosted Surf / Outrage / Ice Beam.
  MiracleBerry Dragonair using a one-time status cure to keep boosting.
  Steelix forcing hazard entries and coverage trades after the true answer is
  spent.
```

Boss route to deny first:

- Deny the route that makes the Dragon Dance answer fail. If Gligar's Toxic or
  Spikes would remove the only Kingdra answer, Gligar is urgent. If Mantine can
  Haze away the user's setup or spin away the user's needed hazards, Mantine is
  urgent. If Kingdra or Dragonair is already in safely, the boost itself is the
  immediate problem.

Boss route that can be delayed:

- Gligar can be delayed if its first clock lands on an expendable piece and the
  user can still cover Kingdra, Dragonair, and Steelix.

- Mantine can be delayed if the user is not relying on hazards or boosts and
  Confuse Ray does not create a worse branch. It cannot be delayed when Haze or
  Rapid Spin erases the plan's main resource.

Best lead profile:

- A lead that pressures Gligar without being the only Kingdra or Dragonair
  answer. It should make Spikes, Toxic, or Quick Claw variance survivable, or
  force Gligar out before the later setup routes become easier.

Avoid as lead:

- The only Kingdra or Dragonair answer if Gligar can poison it.
- A hazard lead if Mantine spins for free and the follow-up cannot punish it.
- A setup lead if Mantine can Haze without cost.
- A status-only answer if MiracleBerry Dragonair can absorb the first status
  and keep the setup route alive.
- A plan that assumes vanilla Steelix typing, vanilla Outrage category, or
  generic "Dragon resists" language without local evidence.

First move plan:

- Give turn 1 one job: prevent Gligar from making the later Dragon Dance route
  easier. If attacking, the hit must change Gligar's hazard/status freedom. If
  pivoting, the pivot must preserve the real setup answer. If setting hazards
  or boosting, the plan must include Mantine's spin/Haze response.

First 3 turns as intentions, not a script:

```text
Turn 1:
  Price Gligar's Spikes, Toxic, Earthquake, Wing Attack, and Quick Claw
  branches against the lead's later role.

Turn 2:
  If Spikes or Toxic landed, rebuild around grounded switch cost and answer
  preservation. If Gligar was denied, prepare for Mantine reset, Kingdra setup,
  Expert Belt coverage, Steelix phazing, or MiracleBerry Dragonair.

Turn 3:
  Start the relevant ledger: Spikes layers, Toxic/paralysis state, Quick Claw
  evidence, Mantine Haze/spin access, Dragon Dance boosts, MiracleBerry status,
  Expert Belt type evidence, and Outrage lock/confusion timing.
```

Piece to preserve:

- The Kingdra answer by default. Kingdra's bulk and Water/Dragon coverage mean
  the answer has to work after a boost, not merely on turn 1.

- The Dragonair answer if it is separate. One Dragonair spreads Thunder Wave and
  mixed coverage; the other can use MiracleBerry to invalidate a single status
  answer.

- The Steelix answer after checking local evidence. This Steelix is
  Steel/Dragon, so vanilla Steel/Ground assumptions are wrong.

Piece that can be spent:

- A lead that has already denied Gligar and has no remaining setup-answer role.

- A poisoned or paralyzed utility piece only if spending it creates clean entry
  to the true anti-setup move before Dragon Dance converts.

Worst plausible branch:

- Gligar gets Spikes or Toxic onto the answer map, Mantine erases the user's
  hazard or setup route with Rapid Spin / Haze, Kingdra or Dragonair gets one
  Dragon Dance, and the user no longer has a healthy, evidence-backed answer to
  boosted Surf, Outrage, Fire Blast, Thunder, Ice Beam, or Steelix Roar cycles.

Abandon conditions:

- The intended Kingdra or Dragonair answer is poisoned, paralyzed, or below the
  required boosted-damage threshold.
- Mantine can Haze or spin without giving up decisive pressure.
- MiracleBerry Dragonair still has its status cure and the plan depends on one
  status move.
- Quick Claw changes a speed assumption that mattered to survival or denial.
- Outrage begins and creates a better lock-punish route than the previous plan.
- Steelix's local Steel/Dragon typing or Outrage category behavior invalidates
  a vanilla matchup assumption.
- Type-chart, passive, item, or damage evidence contradicts the assumed answer.

What information would flip the lead or first move:

- Damage evidence showing the lead can or cannot remove Gligar before a hazard
  or Toxic turn matters.
- Whether the player has redundant Kingdra and Dragonair answers.
- Whether Mantine is pressured enough that Haze or Rapid Spin costs too much.
- Whether the status plan can force MiracleBerry without losing tempo.
- Whether boosted Outrage is physical or special for the specific Dragon user
  after current-stat comparison.
- Whether Spikes change the number of times the answer can enter.
- Whether the correct route is to bait Outrage lock rather than prevent it.

## Extracted Lesson

Clair is not "use Ice on Dragons." Clair is answer preservation against serial
setup routes. Gligar tries to make the later answer worse, Mantine punishes slow
resource plans, Kingdra and Dragonair ask whether the anti-setup tool is still
live, and Outrage can turn from threat into punish window once it locks. The
right opening keeps the real Dragon Dance answer functional while preparing to
re-score immediately after hazards, status, Haze, Quick Claw, MiracleBerry, or
Outrage changes the board.
